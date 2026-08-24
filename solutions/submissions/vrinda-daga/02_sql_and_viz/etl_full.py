"""
etl_full.py
StackUp Engineering Academy - Data Engineering Assessment

Pillar 1: Foundations
Task 1.1 - Clean and transform projects.csv
Task 1.3 - Identify and fix data quality issues in employees.csv

Pillar 2: SQL & Data Visualization
Task 2.2 - Full ETL pipeline for transactions

This script runs the complete ETL pipeline end to end.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==============================================================================
# PATHS
# ==============================================================================

CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = (
    CURRENT_FILE.parents[4]
    if len(CURRENT_FILE.parents) > 4
    else Path("/app")
)

DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        BASE_DIR / "datasets"
    )
)

OUTPUT_DIR = Path(
    os.getenv(
        "OUTPUT_DIR",
        BASE_DIR
        / "outputs"
        / "results"
        / "vrinda-daga"
        / "04_infrastructure"
        / "docker_etl"
    )
)

PROJECTS_INPUT = DATA_DIR / "projects.csv"
EMPLOYEES_INPUT = DATA_DIR / "employees.csv"
TRANSACTIONS_INPUT = DATA_DIR / "transactions.json"

PROJECTS_OUTPUT = OUTPUT_DIR / "projects_clean.csv"
EMPLOYEES_OUTPUT = OUTPUT_DIR / "employees_clean.csv"
TRANSACTIONS_OUTPUT = OUTPUT_DIR / "transactions_clean.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "pipeline_summary.txt"


# ==============================================================================
# TASK 1.1 - LOAD PROJECTS
# ==============================================================================

def load_projects(filepath: Path) -> pd.DataFrame:
    """
    Load the raw projects.csv dataset.
    """

    logger.info("Loading projects data from: %s", filepath)

    df = pd.read_csv(filepath)

    logger.info(
        "Projects loaded successfully: %d rows, %d columns",
        df.shape[0],
        df.shape[1]
    )

    return df


# ==============================================================================
# TASK 1.1 - TRANSFORM PROJECTS
# ==============================================================================

def transform_projects(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the projects dataset.

    Transformations:
    - Convert budget and actual_cost to numeric values
    - Replace missing budget and actual_cost with 0
    - Parse start_date and end_date
    - Standardize status values
    - Calculate budget_variance
    - Calculate is_over_budget
    - Calculate duration_days
    - Calculate budget_utilisation_pct
    - Create status_category
    - Create risk_level
    """

    logger.info("Transforming projects data...")

    df = df.copy()

    # --------------------------------------------------------------------------
    # 1. Convert financial columns to numeric and replace missing values with 0
    # --------------------------------------------------------------------------

    df["budget"] = (
        pd.to_numeric(
            df["budget"],
            errors="coerce"
        )
        .fillna(0)
    )

    df["actual_cost"] = (
        pd.to_numeric(
            df["actual_cost"],
            errors="coerce"
        )
        .fillna(0)
    )

    # --------------------------------------------------------------------------
    # 2. Parse project dates
    # --------------------------------------------------------------------------

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        errors="coerce"
    )

    df["end_date"] = pd.to_datetime(
        df["end_date"],
        errors="coerce"
    )

    # --------------------------------------------------------------------------
    # 3. Standardize status values
    # --------------------------------------------------------------------------

    df["status"] = (
        df["status"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Standardize priority values
    df["priority"] = (
        df["priority"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # --------------------------------------------------------------------------
    # 4. Create budget variance
    # Formula: actual_cost - budget
    # --------------------------------------------------------------------------

    df["budget_variance"] = (
        df["actual_cost"] - df["budget"]
    )

    # --------------------------------------------------------------------------
    # 5. Flag projects that are over budget
    # --------------------------------------------------------------------------

    df["is_over_budget"] = (
        df["actual_cost"] > df["budget"]
    )

    # --------------------------------------------------------------------------
    # 6. Calculate project duration in days
    # --------------------------------------------------------------------------

    df["duration_days"] = (
        df["end_date"] - df["start_date"]
    ).dt.days

    # --------------------------------------------------------------------------
    # 7. Calculate budget utilisation percentage
    # Avoid division by zero
    # --------------------------------------------------------------------------

    df["budget_utilisation_pct"] = (
        df["actual_cost"]
        .div(
            df["budget"].replace(0, np.nan)
        )
        .mul(100)
    )

    # --------------------------------------------------------------------------
    # 8. Categorize project status
    # --------------------------------------------------------------------------

    status_map = {
        "In Progress": "Active",
        "Completed": "Closed",
        "Not Started": "Pending",
        "On Hold": "Pending"
    }

    df["status_category"] = (
        df["status"]
        .map(status_map)
    )

    # --------------------------------------------------------------------------
    # 9. Assign risk level
    # --------------------------------------------------------------------------

    high_risk = (
        df["priority"].eq("Critical")
        | df["is_over_budget"]
    )

    medium_risk = (
        df["priority"].eq("High")
        | df["budget_utilisation_pct"].gt(90)
    )

    df["risk_level"] = np.select(
        [
            high_risk,
            medium_risk
        ],
        [
            "High",
            "Medium"
        ],
        default="Low"
    )

    logger.info(
        "Projects transformation completed: %d rows, %d columns",
        df.shape[0],
        df.shape[1]
    )

    return df


# ==============================================================================
# TASK 1.3 - LOAD EMPLOYEES
# ==============================================================================

def load_employees(filepath: Path) -> pd.DataFrame:
    """
    Load the raw employees.csv dataset.
    """

    logger.info("Loading employee data from: %s", filepath)

    df = pd.read_csv(filepath)

    logger.info(
        "Employees loaded successfully: %d rows, %d columns",
        df.shape[0],
        df.shape[1]
    )

    return df


# ==============================================================================
# TASK 1.3 - CLEAN EMPLOYEES
# ==============================================================================

def clean_employees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the identified data-quality issues in employees.csv.
    """

    logger.info("Cleaning employee data...")

    df = df.copy()

    # --------------------------------------------------------------------------
    # Issue 1: Missing email values
    #
    # Replace missing emails with a deterministic placeholder based on
    # employee_id.
    # --------------------------------------------------------------------------

    missing_email = df["email"].isna()

    df.loc[missing_email, "email"] = (
        df.loc[missing_email, "employee_id"].astype(str)
        + "@unknown.presight.ai"
    )

    logger.info(
        "Missing email values fixed: %d",
        missing_email.sum()
    )

    # --------------------------------------------------------------------------
    # Issue 2: Invalid hire dates
    #
    # Invalid dates are converted to null rather than inventing a date.
    # --------------------------------------------------------------------------

    df["hire_date"] = pd.to_datetime(
        df["hire_date"],
        errors="coerce"
    )

    logger.info(
        "Invalid hire dates converted to null: %d",
        df["hire_date"].isna().sum()
    )

    # --------------------------------------------------------------------------
    # Issue 3: Negative years of experience
    #
    # Negative experience is logically invalid, so replace it with zero.
    # --------------------------------------------------------------------------

    df["years_experience"] = pd.to_numeric(
        df["years_experience"],
        errors="coerce"
    )

    negative_experience = (
        df["years_experience"] < 0
    )

    df.loc[negative_experience, "years_experience"] = 0

    logger.info(
        "Negative experience values corrected: %d",
        negative_experience.sum()
    )

    # --------------------------------------------------------------------------
    # Issue 4: Self-referencing manager
    #
    # An employee should not be their own manager.
    # --------------------------------------------------------------------------

    self_manager = (
        df["employee_id"] == df["manager_id"]
    )

    df.loc[self_manager, "manager_id"] = pd.NA

    logger.info(
        "Self-referencing manager records corrected: %d",
        self_manager.sum()
    )

    # EMP0000 manager references are intentionally retained because
    # they represent the root/system manager.

    return df


# ==============================================================================
# TASK 2.2 - LOAD TRANSACTIONS
# ==============================================================================

def load_transactions(filepath: Path) -> pd.DataFrame:
    """
    Load transactions.json into a flat DataFrame.

    Decisions:
    - transaction_date is parsed to datetime.
    - Null amount values are retained during ingestion and converted to 0.0
      in amount_aed during enrichment.
    - Null approved_by values are retained because they indicate transactions
      without an approver.
    """

    logger.info("Loading transaction data from: %s", filepath)

    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Flatten JSON records into a tabular DataFrame
    df = pd.json_normalize(data)

    logger.info(
        "Transactions loaded successfully: %d rows, %d columns",
        df.shape[0],
        df.shape[1]
    )

    # --------------------------------------------------------------------------
    # Parse transaction date
    # --------------------------------------------------------------------------

    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

    # --------------------------------------------------------------------------
    # Convert amount to numeric.
    #
    # Null values are intentionally retained here.
    # They will be converted to 0.0 in amount_aed during enrichment.
    # --------------------------------------------------------------------------

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce"
        )

    return df


# ==============================================================================
# TASK 2.2 - ENRICH TRANSACTIONS
# ==============================================================================

def enrich_transactions(
    transactions: pd.DataFrame,
    projects: pd.DataFrame,
    employees: pd.DataFrame
) -> pd.DataFrame:
    """
    Enrich transactions with project and current employee information.

    Adds:
    - project_name
    - department
    - full_name
    - is_approved
    - amount_aed
    - transaction_year_month

    Employee enrichment uses CURRENT employee records only.
    """

    logger.info("Enriching transactions...")

    df = transactions.copy()

    # ==========================================================================
    # 1. Add project_name and department
    # ==========================================================================

    project_lookup = (
        projects[
            [
                "project_id",
                "project_name",
                "department"
            ]
        ]
        .drop_duplicates(
            subset=["project_id"]
        )
    )

    df = df.merge(
        project_lookup,
        on="project_id",
        how="left",
        validate="many_to_one"
    )

    logger.info(
        "Project enrichment completed. Rows after merge: %d",
        len(df)
    )

    # ==========================================================================
    # 2. Add approver full_name
    #
    # Use current employee records only.
    # ==========================================================================

    employee_lookup = (
        employees[
            [
                "employee_id",
                "full_name"
            ]
        ]
        .drop_duplicates(
            subset=["employee_id"]
        )
    )

    employee_lookup = employee_lookup.rename(
        columns={
            "employee_id": "approved_by",
            "full_name": "approver_full_name"
        }
    )

    df = df.merge(
        employee_lookup,
        on="approved_by",
        how="left",
        validate="many_to_one"
    )

    # ==========================================================================
    # 3. Add is_approved
    #
    # True when approved_by contains a value.
    # ==========================================================================

    df["is_approved"] = (
        df["approved_by"].notna()
    )

    # ==========================================================================
    # 4. Add amount_aed
    #
    # Null amount values are converted to 0.0 for downstream aggregation.
    # Original amount column is retained for traceability.
    # ==========================================================================

    df["amount_aed"] = (
        pd.to_numeric(
            df["amount"],
            errors="coerce"
        )
        .fillna(0.0)
        .astype(float)
    )

    # ==========================================================================
    # 5. Add transaction_year_month
    # Format: YYYY-MM
    # ==========================================================================

    df["transaction_year_month"] = (
        df["transaction_date"]
        .dt.strftime("%Y-%m")
    )

    logger.info(
        "Transaction enrichment completed: %d rows, %d columns",
        df.shape[0],
        df.shape[1]
    )

    return df


# ==============================================================================
# TASK 2.2 - WRITE OUTPUTS
# ==============================================================================

def write_outputs(
    projects: pd.DataFrame,
    employees: pd.DataFrame,
    transactions: pd.DataFrame,
    raw_project_rows: int,
    raw_employee_rows: int,
    raw_transaction_rows: int,
    start_time: float
) -> None:
    """
    Write all cleaned/enriched datasets and pipeline summary.

    Outputs:
    - projects_clean.csv
    - employees_clean.csv
    - transactions_clean.csv
    - pipeline_summary.txt
    """

    logger.info("Writing outputs...")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------------------------
    # Write CSV outputs
    # --------------------------------------------------------------------------

    projects.to_csv(
        PROJECTS_OUTPUT,
        index=False
    )

    employees.to_csv(
        EMPLOYEES_OUTPUT,
        index=False
    )

    transactions.to_csv(
        TRANSACTIONS_OUTPUT,
        index=False
    )

    logger.info(
        "Projects output written to: %s",
        PROJECTS_OUTPUT
    )

    logger.info(
        "Employees output written to: %s",
        EMPLOYEES_OUTPUT
    )

    logger.info(
        "Transactions output written to: %s",
        TRANSACTIONS_OUTPUT
    )

    # --------------------------------------------------------------------------
    # Pipeline execution time
    # --------------------------------------------------------------------------

    execution_time = time.perf_counter() - start_time

    # --------------------------------------------------------------------------
    # Pipeline summary
    # --------------------------------------------------------------------------

    summary = f"""
StackUp Engineering Academy
Pillar 2 - Task 2.2 ETL Pipeline
============================================================

Run timestamp:
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ROW COUNTS
------------------------------------------------------------
Projects:
  Before: {raw_project_rows}
  After:  {len(projects)}

Employees:
  Before: {raw_employee_rows}
  After:  {len(employees)}

Transactions:
  Before: {raw_transaction_rows}
  After:  {len(transactions)}

DATA QUALITY DECISIONS
------------------------------------------------------------
1. Missing project budget and actual_cost values:
   Replaced with 0.

2. Invalid project dates:
   Converted to null using pandas date parsing.

3. Missing employee email values:
   Replaced with deterministic placeholder:
   <employee_id>@unknown.presight.ai

4. Invalid employee hire dates:
   Converted to null rather than inventing dates.

5. Negative years of experience:
   Replaced with 0.

6. Self-referencing manager records:
   manager_id replaced with null.

7. Null transaction amount:
   Original amount retained as null.
   amount_aed converted to 0.0 for downstream aggregation.

8. Null approved_by:
   Retained as null because it represents a transaction
   without an approver.
   is_approved is set to False.

9. Employee enrichment:
   Current employee records are used for approver information.

PERFORMANCE
------------------------------------------------------------
Pipeline execution time: {execution_time:.4f} seconds

Target:
Less than 30 seconds

Target achieved:
{"YES" if execution_time < 30 else "NO"}

OUTPUT FILES
------------------------------------------------------------
{PROJECTS_OUTPUT}
{EMPLOYEES_OUTPUT}
{TRANSACTIONS_OUTPUT}
"""

    with open(
        SUMMARY_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(summary.strip())

    logger.info(
        "Pipeline summary written to: %s",
        SUMMARY_OUTPUT
    )

    logger.info(
        "Total pipeline execution time: %.4f seconds",
        execution_time
    )


# ==============================================================================
# PIPELINE ENTRY POINT
# ==============================================================================

def run_pipeline() -> None:
    """
    Run the complete ETL pipeline end to end.
    """

    start_time = time.perf_counter()

    logger.info("=" * 60)
    logger.info("Starting Full ETL Pipeline - Task 2.2")
    logger.info("=" * 60)

    # ==========================================================================
    # STEP 1 - LOAD RAW DATA
    # ==========================================================================

    raw_projects = load_projects(
        PROJECTS_INPUT
    )

    raw_employees = load_employees(
        EMPLOYEES_INPUT
    )

    raw_transactions = load_transactions(
        TRANSACTIONS_INPUT
    )

    # Store original row counts for pipeline summary

    raw_project_rows = len(raw_projects)
    raw_employee_rows = len(raw_employees)
    raw_transaction_rows = len(raw_transactions)

    # ==========================================================================
    # STEP 2 - CLEAN / TRANSFORM PROJECTS
    # ==========================================================================

    clean_projects = transform_projects(
        raw_projects
    )

    # ==========================================================================
    # STEP 3 - CLEAN EMPLOYEES
    # ==========================================================================

    clean_emp = clean_employees(
        raw_employees
    )

    # ==========================================================================
    # STEP 4 - ENRICH TRANSACTIONS
    # ==========================================================================

    enriched_transactions = enrich_transactions(
        raw_transactions,
        clean_projects,
        clean_emp
    )

    # ==========================================================================
    # STEP 5 - WRITE OUTPUTS
    # ==========================================================================

    write_outputs(
        clean_projects,
        clean_emp,
        enriched_transactions,
        raw_project_rows,
        raw_employee_rows,
        raw_transaction_rows,
        start_time
    )

    # ==========================================================================
    # FINAL LOGGING
    # ==========================================================================

    execution_time = time.perf_counter() - start_time

    logger.info("=" * 60)
    logger.info("Full ETL Pipeline completed successfully")
    logger.info(
        "Projects output shape: %s",
        clean_projects.shape
    )
    logger.info(
        "Employees output shape: %s",
        clean_emp.shape
    )
    logger.info(
        "Transactions output shape: %s",
        enriched_transactions.shape
    )
    logger.info(
        "Execution time: %.4f seconds",
        execution_time
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
