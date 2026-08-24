"""
=============================================================
StackUp Engineering Academy - Data Engineering Assessment
Pillar: Big Data Processing - Task 3.3
=============================================================

Airflow DAG: presight_etl_pipeline

This DAG orchestrates the batch ETL workflow with:
  - parallel extraction tasks
  - a data-quality gate
  - transform/enrichment
  - output loading
  - an XCom-driven pipeline report
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pendulum
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


logger = logging.getLogger(__name__)


# ==============================================================================
# Paths
# ==============================================================================

def find_base_dir() -> Path:
    """
    Find the project root locally or inside the Airflow Docker container.
    """
    current = Path(__file__).resolve()

    for parent in [current.parent, *current.parents]:
        if (parent / "datasets").exists():
            return parent

    # Airflow Docker fallback from docker-compose.yml volume mounts.
    airflow_base = Path("/opt/airflow")

    if (airflow_base / "datasets").exists():
        return airflow_base

    raise FileNotFoundError("Could not locate project base directory.")


BASE_DIR = find_base_dir()
DATA_DIR = BASE_DIR / "datasets"
OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "results"
    / "vrinda-daga"
    / "03_big_data"
    / "airflow"
)
STAGING_DIR = OUTPUT_DIR / "_staging"

PROJECTS_INPUT = DATA_DIR / "projects.csv"
EMPLOYEES_INPUT = DATA_DIR / "employees.csv"
TRANSACTIONS_INPUT = DATA_DIR / "transactions.json"

PROJECTS_OUTPUT = OUTPUT_DIR / "projects_clean.csv"
EMPLOYEES_OUTPUT = OUTPUT_DIR / "employees_clean.csv"
TRANSACTIONS_OUTPUT = OUTPUT_DIR / "transactions_clean.csv"


# ==============================================================================
# ETL functions
# ==============================================================================

def load_projects() -> pd.DataFrame:
    logger.info("Loading projects from %s", PROJECTS_INPUT)
    return pd.read_csv(PROJECTS_INPUT)


def load_employees() -> pd.DataFrame:
    logger.info("Loading employees from %s", EMPLOYEES_INPUT)
    return pd.read_csv(EMPLOYEES_INPUT)


def load_transactions() -> pd.DataFrame:
    logger.info("Loading transactions from %s", TRANSACTIONS_INPUT)

    with open(TRANSACTIONS_INPUT, "r", encoding="utf-8") as file:
        records = json.load(file)

    df = pd.json_normalize(records)

    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce",
        )

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    return df


def transform_projects(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming projects")

    df = df.copy()
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0)
    df["actual_cost"] = (
        pd.to_numeric(df["actual_cost"], errors="coerce").fillna(0)
    )
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip().str.title()
    df["priority"] = df["priority"].astype("string").str.strip().str.title()

    df["budget_variance"] = df["actual_cost"] - df["budget"]
    df["is_over_budget"] = df["actual_cost"] > df["budget"]
    df["duration_days"] = (df["end_date"] - df["start_date"]).dt.days
    df["budget_utilisation_pct"] = (
        df["actual_cost"].div(df["budget"].replace(0, np.nan)).mul(100)
    )

    status_map = {
        "In Progress": "Active",
        "Completed": "Closed",
        "Not Started": "Pending",
        "On Hold": "Pending",
    }
    df["status_category"] = df["status"].map(status_map)

    high_risk = (
        df["priority"].eq("Critical") | df["is_over_budget"]
    ).fillna(False).astype(bool).to_numpy()
    medium_risk = (
        df["priority"].eq("High") | df["budget_utilisation_pct"].gt(90)
    ).fillna(False).astype(bool).to_numpy()

    df["risk_level"] = np.select(
        [high_risk, medium_risk],
        ["High", "Medium"],
        default="Low",
    )

    return df


def clean_employees(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Cleaning employees")

    df = df.copy()

    missing_email = df["email"].isna() | df["email"].astype("string").str.strip().eq("")
    df.loc[missing_email, "email"] = (
        df.loc[missing_email, "employee_id"].astype(str)
        + "@unknown.presight.ai"
    )

    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
    df["years_experience"] = pd.to_numeric(
        df["years_experience"],
        errors="coerce",
    )

    negative_experience = df["years_experience"] < 0
    df.loc[negative_experience, "years_experience"] = 0

    self_manager = df["employee_id"] == df["manager_id"]
    df.loc[self_manager, "manager_id"] = pd.NA

    return df


def enrich_transactions(
    transactions: pd.DataFrame,
    projects: pd.DataFrame,
    employees: pd.DataFrame,
) -> pd.DataFrame:
    logger.info("Enriching transactions")

    df = transactions.copy()

    project_lookup = (
        projects[["project_id", "project_name", "department"]]
        .drop_duplicates(subset=["project_id"])
    )
    df = df.merge(
        project_lookup,
        on="project_id",
        how="left",
        validate="many_to_one",
    )

    employee_lookup = (
        employees[["employee_id", "full_name"]]
        .drop_duplicates(subset=["employee_id"])
        .rename(
            columns={
                "employee_id": "approved_by",
                "full_name": "approver_full_name",
            }
        )
    )
    df = df.merge(
        employee_lookup,
        on="approved_by",
        how="left",
        validate="many_to_one",
    )

    df["is_approved"] = df["approved_by"].notna()
    df["amount_aed"] = (
        pd.to_numeric(df["amount"], errors="coerce")
        .fillna(0.0)
        .astype(float)
    )
    df["transaction_year_month"] = df["transaction_date"].dt.strftime("%Y-%m")

    return df


def run_data_quality_checks(df: pd.DataFrame, dataset_name: str) -> dict:
    """
    Run completeness, uniqueness, and basic validity checks.
    """
    key_columns = {
        "projects": ["project_id", "project_name"],
        "employees": ["employee_id", "full_name"],
        "transactions": ["transaction_id", "project_id", "amount"],
    }
    primary_keys = {
        "projects": "project_id",
        "employees": "employee_id",
        "transactions": "transaction_id",
    }

    completeness = (
        df.notna().mean().mul(100).round(2).to_dict()
        if len(df) > 0
        else {column: 0.0 for column in df.columns}
    )
    critical_key_completeness = {
        column: completeness.get(column, 0.0)
        for column in key_columns[dataset_name]
    }

    primary_key = primary_keys[dataset_name]
    duplicate_primary_keys = int(df[primary_key].duplicated().sum())

    validity = {}

    if dataset_name == "projects":
        validity["negative_budget_count"] = int((df["budget"] < 0).sum())
        validity["end_before_start_count"] = int(
            (
                pd.to_datetime(df["end_date"], errors="coerce")
                < pd.to_datetime(df["start_date"], errors="coerce")
            ).sum()
        )
    elif dataset_name == "employees":
        validity["negative_salary_count"] = int((df["salary"] < 0).sum())
        validity["negative_experience_count"] = int(
            (df["years_experience"] < 0).sum()
        )
    elif dataset_name == "transactions":
        validity["negative_amount_count"] = int((df["amount"] < 0).sum())
        validity["missing_transaction_date_count"] = int(
            pd.to_datetime(df["transaction_date"], errors="coerce").isna().sum()
        )

    passed = (
        all(value >= 80 for value in critical_key_completeness.values())
        and duplicate_primary_keys == 0
    )

    return {
        "dataset": dataset_name,
        "row_count": int(len(df)),
        "critical_key_completeness_pct": critical_key_completeness,
        "duplicate_primary_keys": duplicate_primary_keys,
        "validity": validity,
        "passed": passed,
    }


# ==============================================================================
# Airflow task callables
# ==============================================================================

def task_extract_projects(**context):
    df = load_projects()
    context["ti"].xcom_push(key="projects_raw_count", value=int(len(df)))
    return "projects extracted"


def task_extract_employees(**context):
    df = load_employees()
    context["ti"].xcom_push(key="employees_raw_count", value=int(len(df)))
    return "employees extracted"


def task_extract_transactions(**context):
    df = load_transactions()
    context["ti"].xcom_push(key="transactions_raw_count", value=int(len(df)))
    return "transactions extracted"


def task_validate_data_quality(**context):
    """
    DQ gate: fail if completeness is below 80% on any key column.
    """
    ti = context["ti"]

    datasets = {
        "projects": load_projects(),
        "employees": load_employees(),
        "transactions": load_transactions(),
    }
    dq_results = {
        name: run_data_quality_checks(df, name)
        for name, df in datasets.items()
    }

    failures = []

    for dataset_name, result in dq_results.items():
        for column, completeness_pct in result[
            "critical_key_completeness_pct"
        ].items():
            if completeness_pct < 80:
                failures.append(
                    f"{dataset_name}.{column} completeness is "
                    f"{completeness_pct:.2f}% (< 80%)"
                )

        if result["duplicate_primary_keys"] > 0:
            failures.append(
                f"{dataset_name} has "
                f"{result['duplicate_primary_keys']} duplicate primary keys"
            )

    ti.xcom_push(key="dq_results", value=dq_results)

    if failures:
        raise ValueError("Data quality gate failed: " + "; ".join(failures))

    logger.info("Data quality gate passed: %s", dq_results)
    return "data quality passed"


def task_transform_and_enrich(**context):
    ti = context["ti"]
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    raw_projects = load_projects()
    raw_employees = load_employees()
    raw_transactions = load_transactions()

    clean_projects = transform_projects(raw_projects)
    clean_employees_df = clean_employees(raw_employees)
    enriched_transactions = enrich_transactions(
        raw_transactions,
        clean_projects,
        clean_employees_df,
    )

    stage_paths = {
        "projects": str(STAGING_DIR / "projects_clean.csv"),
        "employees": str(STAGING_DIR / "employees_clean.csv"),
        "transactions": str(STAGING_DIR / "transactions_clean.csv"),
    }

    clean_projects.to_csv(stage_paths["projects"], index=False)
    clean_employees_df.to_csv(stage_paths["employees"], index=False)
    enriched_transactions.to_csv(stage_paths["transactions"], index=False)

    ti.xcom_push(key="projects_clean_count", value=int(len(clean_projects)))
    ti.xcom_push(key="employees_clean_count", value=int(len(clean_employees_df)))
    ti.xcom_push(
        key="transactions_clean_count",
        value=int(len(enriched_transactions)),
    )
    ti.xcom_push(key="stage_paths", value=stage_paths)

    return "transform and enrichment complete"


def task_load_to_output(**context):
    ti = context["ti"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stage_paths = ti.xcom_pull(
        task_ids="transform_and_enrich",
        key="stage_paths",
    )

    if not stage_paths:
        raise ValueError("No staged files found from transform_and_enrich.")

    outputs = {
        "projects_clean": str(PROJECTS_OUTPUT),
        "employees_clean": str(EMPLOYEES_OUTPUT),
        "transactions_clean": str(TRANSACTIONS_OUTPUT),
    }

    pd.read_csv(stage_paths["projects"]).to_csv(PROJECTS_OUTPUT, index=False)
    pd.read_csv(stage_paths["employees"]).to_csv(EMPLOYEES_OUTPUT, index=False)
    pd.read_csv(stage_paths["transactions"]).to_csv(
        TRANSACTIONS_OUTPUT,
        index=False,
    )

    ti.xcom_push(key="files_written", value=outputs)

    logger.info("Output files written: %s", outputs)
    return outputs


def task_generate_pipeline_report(**context):
    ti = context["ti"]
    logical_date = context.get("logical_date") or context.get("execution_date")
    ds = context.get("ds") or logical_date.strftime("%Y-%m-%d")

    raw_counts = {
        "projects": ti.xcom_pull(
            task_ids="extract_projects",
            key="projects_raw_count",
        ),
        "employees": ti.xcom_pull(
            task_ids="extract_employees",
            key="employees_raw_count",
        ),
        "transactions": ti.xcom_pull(
            task_ids="extract_transactions",
            key="transactions_raw_count",
        ),
    }
    clean_counts = {
        "projects": ti.xcom_pull(
            task_ids="transform_and_enrich",
            key="projects_clean_count",
        ),
        "employees": ti.xcom_pull(
            task_ids="transform_and_enrich",
            key="employees_clean_count",
        ),
        "transactions": ti.xcom_pull(
            task_ids="transform_and_enrich",
            key="transactions_clean_count",
        ),
    }
    dq_results = ti.xcom_pull(
        task_ids="validate_data_quality",
        key="dq_results",
    )
    files_written = ti.xcom_pull(
        task_ids="load_to_output",
        key="files_written",
    )

    report_path = OUTPUT_DIR / f"pipeline_report_{ds}.txt"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = f"""
Presight ETL Pipeline Report
============================================================

DAG ID:
presight_etl_pipeline

Logical date:
{logical_date}

Run date:
{ds}

RAW VS CLEAN ROW COUNTS
------------------------------------------------------------
Projects:
  Raw:   {raw_counts["projects"]}
  Clean: {clean_counts["projects"]}

Employees:
  Raw:   {raw_counts["employees"]}
  Clean: {clean_counts["employees"]}

Transactions:
  Raw:   {raw_counts["transactions"]}
  Clean: {clean_counts["transactions"]}

DATA QUALITY RESULTS
------------------------------------------------------------
{json.dumps(dq_results, indent=2, default=str)}

FILES WRITTEN
------------------------------------------------------------
{json.dumps(files_written, indent=2, default=str)}
"""

    report_path.write_text(report.strip(), encoding="utf-8")

    logger.info("Pipeline report written to: %s", report_path)
    return str(report_path)


def log_failure(context):
    task_instance = context.get("task_instance")
    exception = context.get("exception")

    logger.error(
        "Task failed. task_id=%s dag_id=%s exception=%s",
        getattr(task_instance, "task_id", "unknown"),
        getattr(task_instance, "dag_id", "unknown"),
        exception,
    )


# ==============================================================================
# 3.3a - DAG configuration
# ==============================================================================

UAE_TZ = pendulum.timezone("Asia/Dubai")

default_args = {
    "owner": "vrinda-daga",
    "depends_on_past": False,
    "start_date": pendulum.datetime(2025, 1, 1, tz=UAE_TZ),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "on_failure_callback": log_failure,
}


with DAG(
    dag_id="presight_etl_pipeline",
    default_args=default_args,
    description="Daily ETL pipeline for Presight project management data",
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["presight", "etl", "assessment"],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    extract_projects = PythonOperator(
        task_id="extract_projects",
        python_callable=task_extract_projects,
    )

    extract_employees = PythonOperator(
        task_id="extract_employees",
        python_callable=task_extract_employees,
    )

    extract_transactions = PythonOperator(
        task_id="extract_transactions",
        python_callable=task_extract_transactions,
    )

    validate_data_quality = PythonOperator(
        task_id="validate_data_quality",
        python_callable=task_validate_data_quality,
    )

    transform_and_enrich = PythonOperator(
        task_id="transform_and_enrich",
        python_callable=task_transform_and_enrich,
    )

    load_to_output = PythonOperator(
        task_id="load_to_output",
        python_callable=task_load_to_output,
    )

    generate_pipeline_report = PythonOperator(
        task_id="generate_pipeline_report",
        python_callable=task_generate_pipeline_report,
    )

    start >> [extract_projects, extract_employees, extract_transactions]
    [extract_projects, extract_employees, extract_transactions] >> validate_data_quality
    validate_data_quality >> transform_and_enrich >> load_to_output
    load_to_output >> generate_pipeline_report >> end
