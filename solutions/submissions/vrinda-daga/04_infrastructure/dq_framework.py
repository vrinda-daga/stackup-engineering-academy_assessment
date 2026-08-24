"""
Reusable data quality framework for Pillar 4 - Task 4.3.

Rules are declared in DQ_CONFIG. To extend coverage, add or change rules in the
config rather than modifying the check execution code.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parents[4] if len(CURRENT_FILE.parents) > 4 else Path.cwd()

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "datasets"))
OUTPUT_DIR = Path(
    os.getenv(
        "OUTPUT_DIR",
        BASE_DIR
        / "outputs"
        / "results"
        / "vrinda-daga"
        / "04_infrastructure"
        / "dq_reports",
    )
)


ROLE_LEVEL_RULES = {
    "Director": ["Director"],
    "Lead": ["Lead", "Director"],
    "Senior": ["Senior", "Lead", "Director"],
    "Manager": ["Mid", "Senior", "Lead", "Director"],
}


DQ_CONFIG: dict[str, dict[str, Any]] = {
    "projects": {
        "path": "projects.csv",
        "format": "csv",
        "completeness_threshold": 0.90,
        "pk_columns": ["project_id"],
        "numeric_ranges": {
            "budget": {"min": 0, "max": 10_000_000},
            "actual_cost": {"min": 0, "max": 10_000_000},
        },
        "date_columns": {
            "start_date": {"allow_future": False},
            "end_date": {"allow_future": True},
        },
        "consistency_rules": [
            {"type": "before", "columns": ["start_date", "end_date"]},
            {"type": "non_negative", "column": "budget"},
            {"type": "non_negative", "column": "actual_cost"},
        ],
        "foreign_keys": {
            "project_manager_id": {
                "dataset": "employees",
                "column": "employee_id",
                "ignore_nulls": True,
            }
        },
        "distribution_checks": {
            "columns": ["department", "status", "priority", "region"],
            "max_share": 0.30,
        },
        "outlier_checks": {
            "budget": {"z_threshold": 3},
            "actual_cost": {"z_threshold": 3},
        },
    },
    "employees": {
        "path": "employees.csv",
        "format": "csv",
        "completeness_threshold": 0.85,
        "pk_columns": ["employee_id"],
        "numeric_ranges": {
            "salary": {"min": 10_000, "max": 100_000},
            "years_experience": {"min": 0, "max": 50},
        },
        "date_columns": {
            "hire_date": {"allow_future": False},
        },
        "consistency_rules": [
            {"type": "non_negative", "column": "salary"},
            {"type": "non_negative", "column": "years_experience"},
            {
                "type": "role_level_alignment",
                "role_column": "role",
                "level_column": "level",
                "keyword_levels": ROLE_LEVEL_RULES,
            },
        ],
        "foreign_keys": {
            "manager_id": {
                "dataset": "employees",
                "column": "employee_id",
                "ignore_nulls": True,
                "ignore_values": ["EMP0000"],
            }
        },
        "distribution_checks": {
            "columns": ["department", "level", "region", "status"],
            "max_share": 0.30,
        },
        "outlier_checks": {
            "salary": {"z_threshold": 3},
            "years_experience": {"z_threshold": 3},
        },
    },
    "transactions": {
        "path": "transactions.json",
        "format": "json",
        "completeness_threshold": 0.85,
        "completeness_optional_columns": ["approved_by", "notes"],
        "pk_columns": ["transaction_id"],
        "numeric_ranges": {
            "amount": {"min": 0, "max": 1_000_000},
        },
        "date_columns": {
            "transaction_date": {"allow_future": False},
        },
        "consistency_rules": [
            {"type": "non_negative", "column": "amount"},
        ],
        "foreign_keys": {
            "project_id": {
                "dataset": "projects",
                "column": "project_id",
                "ignore_nulls": True,
            },
            "approved_by": {
                "dataset": "employees",
                "column": "employee_id",
                "ignore_nulls": True,
            },
        },
        "distribution_checks": {
            "columns": ["currency", "payment_status", "category"],
            "max_share": 0.30,
        },
        "freshness_check": {
            "column": "transaction_date",
            "max_age_days": 30,
        },
        "outlier_checks": {
            "amount": {"z_threshold": 3},
        },
    },
    "employees_salary_history": {
        "path": "employees_salary_history.csv",
        "format": "csv",
        "completeness_threshold": 0.85,
        "pk_columns": [
            "employee_id",
            "effective_date",
            "change_type",
            "new_salary",
        ],
        "numeric_ranges": {
            "previous_salary": {"min": 10_000, "max": 100_000},
            "new_salary": {"min": 10_000, "max": 100_000},
        },
        "date_columns": {
            "effective_date": {"allow_future": False},
        },
        "consistency_rules": [
            {"type": "non_negative", "column": "previous_salary"},
            {"type": "non_negative", "column": "new_salary"},
            {
                "type": "role_level_alignment",
                "role_column": "previous_role",
                "level_column": "previous_level",
                "keyword_levels": ROLE_LEVEL_RULES,
            },
            {
                "type": "role_level_alignment",
                "role_column": "new_role",
                "level_column": "new_level",
                "keyword_levels": ROLE_LEVEL_RULES,
            },
        ],
        "foreign_keys": {
            "employee_id": {
                "dataset": "employees",
                "column": "employee_id",
                "ignore_nulls": True,
            }
        },
        "distribution_checks": {
            "columns": ["change_type", "new_level"],
            "max_share": 0.30,
        },
        "outlier_checks": {
            "previous_salary": {"z_threshold": 3},
            "new_salary": {"z_threshold": 3},
        },
    },
}


def load_dataset(dataset_name: str, dataset_config: dict[str, Any]) -> pd.DataFrame:
    """Load one configured dataset."""

    path = DATA_DIR / dataset_config["path"]
    file_format = dataset_config.get("format", "csv")

    logger.info("Loading %s from %s", dataset_name, path)

    if file_format == "json":
        with open(path, "r", encoding="utf-8") as file:
            records = json.load(file)
        return pd.json_normalize(records)

    if file_format == "csv":
        return pd.read_csv(path)

    raise ValueError(f"Unsupported format for {dataset_name}: {file_format}")


def load_all_datasets(config: dict[str, dict[str, Any]]) -> dict[str, pd.DataFrame]:
    """Load every dataset declared in the DQ config."""

    return {
        dataset_name: load_dataset(dataset_name, dataset_config)
        for dataset_name, dataset_config in config.items()
    }


def add_result(
    results: dict[str, Any],
    check_name: str,
    status: str,
    details: Any,
    failed_columns: list[str] | None = None,
) -> None:
    """Record one check result and log a warning when it fails."""

    payload = {
        "status": status,
        "details": details,
    }

    if failed_columns is not None:
        payload["failed_columns"] = failed_columns

    results[check_name] = payload

    if status == "FAIL":
        logger.warning("%s check failed: %s", check_name, details)


def string_non_empty(series: pd.Series) -> pd.Series:
    """Treat blank strings as missing values for completeness checks."""

    present = series.notna()

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        present = present & series.astype("string").str.strip().fillna("").ne("")

    return present


def check_completeness(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, dict[str, float], list[str]]:
    threshold = dataset_config["completeness_threshold"]
    optional_columns = set(dataset_config.get("completeness_optional_columns", []))

    details = {}
    failed_columns = []

    for column in df.columns:
        completeness = string_non_empty(df[column]).mean()
        details[column] = round(float(completeness), 4)

        if column not in optional_columns and completeness < threshold:
            failed_columns.append(column)

    status = "PASS" if not failed_columns else "FAIL"
    return status, details, failed_columns


def check_uniqueness(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, str]:
    pk_columns = dataset_config["pk_columns"]
    missing_columns = [column for column in pk_columns if column not in df.columns]

    if missing_columns:
        return "FAIL", f"Missing PK columns: {missing_columns}"

    duplicate_rows = int(df.duplicated(subset=pk_columns, keep=False).sum())
    unique_rows = int(df.drop_duplicates(subset=pk_columns).shape[0])
    total_rows = int(len(df))
    null_pk_rows = int(df[pk_columns].isna().any(axis=1).sum())

    status = "PASS" if duplicate_rows == 0 and null_pk_rows == 0 else "FAIL"
    details = (
        f"{', '.join(pk_columns)}: {unique_rows} unique / {total_rows} total; "
        f"duplicate_rows={duplicate_rows}; null_pk_rows={null_pk_rows}"
    )

    return status, details


def check_validity_numeric(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    numeric_ranges = dataset_config.get("numeric_ranges", {})
    details = {}

    for column, rule in numeric_ranges.items():
        if column not in df.columns:
            details[column] = {"missing_column": True}
            continue

        values = pd.to_numeric(df[column], errors="coerce")
        original_present = df[column].notna()
        invalid_type_count = int((original_present & values.isna()).sum())
        below_min = int((values < rule["min"]).sum())
        above_max = int((values > rule["max"]).sum())

        details[column] = {
            "min": rule["min"],
            "max": rule["max"],
            "invalid_type_count": invalid_type_count,
            "below_min_count": below_min,
            "above_max_count": above_max,
        }

    failed = any(
        detail.get("missing_column")
        or detail.get("invalid_type_count", 0) > 0
        or detail.get("below_min_count", 0) > 0
        or detail.get("above_max_count", 0) > 0
        for detail in details.values()
    )

    return ("FAIL" if failed else "PASS"), details


def check_validity_date(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
    as_of_date: pd.Timestamp | None = None,
) -> tuple[str, dict[str, Any]]:
    date_columns = dataset_config.get("date_columns", {})
    as_of = as_of_date or pd.Timestamp.now().normalize()
    details = {}

    for column, rule in date_columns.items():
        if column not in df.columns:
            details[column] = {"missing_column": True}
            continue

        values = pd.to_datetime(df[column], errors="coerce")
        original_present = df[column].notna()
        invalid_date_count = int((original_present & values.isna()).sum())
        future_count = 0

        if not rule.get("allow_future", False):
            future_count = int((values > as_of).sum())

        details[column] = {
            "allow_future": bool(rule.get("allow_future", False)),
            "invalid_date_count": invalid_date_count,
            "future_count": future_count,
            "min_date": None if values.dropna().empty else str(values.min().date()),
            "max_date": None if values.dropna().empty else str(values.max().date()),
        }

    failed = any(
        detail.get("missing_column")
        or detail.get("invalid_date_count", 0) > 0
        or detail.get("future_count", 0) > 0
        for detail in details.values()
    )

    return ("FAIL" if failed else "PASS"), details


def allowed_levels_for_role(
    role: Any,
    keyword_levels: dict[str, list[str]],
) -> list[str] | None:
    """Return allowed levels when a role name contains a governed keyword."""

    if pd.isna(role):
        return None

    role_text = str(role)

    for keyword, allowed_levels in keyword_levels.items():
        if keyword.lower() in role_text.lower():
            return allowed_levels

    return None


def check_consistency(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    details = []

    for rule in dataset_config.get("consistency_rules", []):
        rule_type = rule["type"]

        if rule_type == "before":
            left_column, right_column = rule["columns"]
            if left_column not in df.columns or right_column not in df.columns:
                details.append({"rule": rule, "missing_column": True})
                continue

            left = pd.to_datetime(df[left_column], errors="coerce")
            right = pd.to_datetime(df[right_column], errors="coerce")
            comparable = left.notna() & right.notna()
            allow_equal = rule.get("allow_equal", False)
            violations = (
                comparable & (left > right)
                if allow_equal
                else comparable & (left >= right)
            )
            details.append(
                {
                    "rule": f"{left_column} before {right_column}",
                    "violation_count": int(violations.sum()),
                }
            )

        elif rule_type == "non_negative":
            column = rule["column"]
            if column not in df.columns:
                details.append({"rule": rule, "missing_column": True})
                continue

            values = pd.to_numeric(df[column], errors="coerce")
            violations = values < 0
            details.append(
                {
                    "rule": f"{column} >= 0",
                    "violation_count": int(violations.sum()),
                }
            )

        elif rule_type == "role_level_alignment":
            role_column = rule["role_column"]
            level_column = rule["level_column"]
            keyword_levels = rule["keyword_levels"]

            if role_column not in df.columns or level_column not in df.columns:
                details.append({"rule": rule, "missing_column": True})
                continue

            violation_count = 0
            examples = []

            for _, row in df[[role_column, level_column]].iterrows():
                allowed_levels = allowed_levels_for_role(
                    row[role_column],
                    keyword_levels,
                )

                if allowed_levels is None or pd.isna(row[level_column]):
                    continue

                if row[level_column] not in allowed_levels:
                    violation_count += 1
                    if len(examples) < 5:
                        examples.append(
                            {
                                "role": row[role_column],
                                "level": row[level_column],
                                "allowed_levels": allowed_levels,
                            }
                        )

            details.append(
                {
                    "rule": f"{role_column} aligns with {level_column}",
                    "violation_count": violation_count,
                    "examples": examples,
                }
            )

        else:
            details.append({"rule": rule, "unsupported_rule_type": rule_type})

    failed = any(
        detail.get("missing_column")
        or detail.get("unsupported_rule_type")
        or detail.get("violation_count", 0) > 0
        for detail in details
    )

    return ("FAIL" if failed else "PASS"), details


def check_referential_integrity(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
    reference_datasets: dict[str, pd.DataFrame],
) -> tuple[str, dict[str, Any]]:
    details = {}

    for local_column, rule in dataset_config.get("foreign_keys", {}).items():
        reference_dataset = rule["dataset"]
        reference_column = rule["column"]

        if local_column not in df.columns:
            details[local_column] = {"missing_local_column": True}
            continue

        if reference_dataset not in reference_datasets:
            details[local_column] = {"missing_reference_dataset": reference_dataset}
            continue

        reference_df = reference_datasets[reference_dataset]

        if reference_column not in reference_df.columns:
            details[local_column] = {"missing_reference_column": reference_column}
            continue

        local_values = df[local_column]

        if rule.get("ignore_nulls", True):
            local_values = local_values.dropna()

        ignore_values = set(rule.get("ignore_values", []))
        if ignore_values:
            local_values = local_values[~local_values.isin(ignore_values)]

        reference_values = set(reference_df[reference_column].dropna())
        invalid_mask = ~local_values.isin(reference_values)
        invalid_values = sorted(local_values[invalid_mask].dropna().unique().tolist())

        details[local_column] = {
            "reference": f"{reference_dataset}.{reference_column}",
            "checked_values": int(len(local_values)),
            "invalid_count": int(invalid_mask.sum()),
            "invalid_examples": invalid_values[:10],
        }

    failed = any(
        detail.get("missing_local_column")
        or detail.get("missing_reference_dataset")
        or detail.get("missing_reference_column")
        or detail.get("invalid_count", 0) > 0
        for detail in details.values()
    )

    return ("FAIL" if failed else "PASS"), details


def check_distribution(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    distribution_config = dataset_config.get("distribution_checks", {})
    columns = distribution_config.get("columns", [])
    max_share = distribution_config.get("max_share", 0.30)
    details = {}

    for column in columns:
        if column not in df.columns:
            details[column] = {"missing_column": True}
            continue

        counts = df[column].value_counts(dropna=False)
        if counts.empty:
            details[column] = {
                "top_value": None,
                "top_share": 0.0,
                "threshold": max_share,
            }
            continue

        top_value = counts.index[0]
        top_count = int(counts.iloc[0])
        top_share = float(top_count / len(df)) if len(df) else 0.0

        details[column] = {
            "top_value": None if pd.isna(top_value) else str(top_value),
            "top_count": top_count,
            "top_share": round(top_share, 4),
            "threshold": max_share,
            "is_dominated": top_share > max_share,
        }

    failed = any(
        detail.get("missing_column") or detail.get("is_dominated", False)
        for detail in details.values()
    )

    return ("FAIL" if failed else "PASS"), details


def check_freshness(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
    as_of_date: pd.Timestamp | None = None,
) -> tuple[str, dict[str, Any]]:
    freshness_config = dataset_config.get("freshness_check")
    if not freshness_config:
        return "PASS", {"not_configured": True}

    column = freshness_config["column"]
    max_age_days = freshness_config["max_age_days"]
    as_of = as_of_date or pd.Timestamp.now().normalize()

    if column not in df.columns:
        return "FAIL", {"missing_column": column}

    dates = pd.to_datetime(df[column], errors="coerce").dropna()

    if dates.empty:
        return "FAIL", {"column": column, "reason": "No valid dates"}

    max_date = dates.max()
    age_days = int((as_of - max_date.normalize()).days)

    details = {
        "column": column,
        "max_date": str(max_date.date()),
        "as_of_date": str(as_of.date()),
        "age_days": age_days,
        "max_age_days": max_age_days,
    }

    status = "PASS" if age_days <= max_age_days else "FAIL"
    return status, details


def check_outliers(
    df: pd.DataFrame,
    dataset_config: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    outlier_config = dataset_config.get("outlier_checks", {})
    details = {}

    for column, rule in outlier_config.items():
        if column not in df.columns:
            details[column] = {"missing_column": True}
            continue

        values = pd.to_numeric(df[column], errors="coerce").dropna()

        if values.empty:
            details[column] = {"reason": "No numeric values"}
            continue

        mean = values.mean()
        std = values.std(ddof=0)
        threshold = rule.get("z_threshold", 3)

        if std == 0:
            outlier_count = 0
            examples = []
        else:
            z_scores = (values - mean).abs() / std
            outliers = values[z_scores > threshold]
            outlier_count = int(len(outliers))
            examples = outliers.head(10).tolist()

        details[column] = {
            "mean": round(float(mean), 2),
            "std": round(float(std), 2),
            "z_threshold": threshold,
            "outlier_count": outlier_count,
            "outlier_examples": examples,
        }

    failed = any(
        detail.get("missing_column") or detail.get("outlier_count", 0) > 0
        for detail in details.values()
    )

    return ("FAIL" if failed else "PASS"), details


def run_data_quality_checks(
    df: pd.DataFrame,
    dataset_name: str,
    config: dict[str, dict[str, Any]] | None = None,
    reference_datasets: dict[str, pd.DataFrame] | None = None,
    as_of_date: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Run all configured data quality checks for a dataset."""

    config = config or DQ_CONFIG
    reference_datasets = reference_datasets or {}

    if dataset_name not in config:
        raise KeyError(f"No DQ configuration found for dataset: {dataset_name}")

    dataset_config = config[dataset_name]
    results: dict[str, Any] = {}

    status, details, failed_columns = check_completeness(df, dataset_config)
    add_result(results, "completeness", status, details, failed_columns)

    status, details = check_uniqueness(df, dataset_config)
    add_result(results, "uniqueness", status, details)

    status, details = check_validity_numeric(df, dataset_config)
    add_result(results, "validity_numeric", status, details)

    status, details = check_validity_date(df, dataset_config, as_of_date)
    add_result(results, "validity_date", status, details)

    status, details = check_consistency(df, dataset_config)
    add_result(results, "consistency", status, details)

    status, details = check_referential_integrity(
        df,
        dataset_config,
        reference_datasets,
    )
    add_result(results, "referential_integrity", status, details)

    status, details = check_distribution(df, dataset_config)
    add_result(results, "distribution", status, details)

    if "freshness_check" in dataset_config:
        status, details = check_freshness(df, dataset_config, as_of_date)
        add_result(results, "freshness", status, details)

    status, details = check_outliers(df, dataset_config)
    add_result(results, "outliers", status, details)

    checks_run = len(results)
    checks_passed = sum(1 for result in results.values() if result["status"] == "PASS")
    checks_failed = sum(1 for result in results.values() if result["status"] == "FAIL")

    return {
        "dataset_name": dataset_name,
        "checks_run": checks_run,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "results": results,
    }


def write_markdown_report(report: dict[str, Any], output_dir: Path) -> Path:
    """Write one human-readable markdown report per dataset."""

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_name = report["dataset_name"]
    output_path = output_dir / f"dq_report_{dataset_name}.md"

    lines = [
        f"# Data Quality Report - {dataset_name}",
        "",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "",
        "## Summary",
        "",
        f"- Checks run: {report['checks_run']}",
        f"- Checks passed: {report['checks_passed']}",
        f"- Checks failed: {report['checks_failed']}",
        "",
        "## Results",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]

    for check_name, result in report["results"].items():
        details = json.dumps(result["details"], ensure_ascii=True, default=str)
        details = details.replace("|", "\\|")
        lines.append(f"| {check_name} | {result['status']} | `{details}` |")

    lines.append("")
    lines.append("## Raw Result")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report, indent=2, ensure_ascii=True, default=str))
    lines.append("```")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_summary_json(reports: list[dict[str, Any]], output_dir: Path) -> Path:
    """Write an optional machine-readable summary across all datasets."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dq_summary.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "datasets": reports,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, default=str),
        encoding="utf-8",
    )
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run configurable data quality checks for assessment datasets.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Directory containing source datasets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory where DQ markdown reports should be written.",
    )
    parser.add_argument(
        "--as-of-date",
        type=str,
        default=None,
        help="Optional YYYY-MM-DD date for non-future and freshness checks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    global DATA_DIR
    DATA_DIR = args.data_dir

    as_of_date = (
        pd.Timestamp(args.as_of_date).normalize()
        if args.as_of_date
        else pd.Timestamp.now().normalize()
    )

    datasets = load_all_datasets(DQ_CONFIG)
    reports = []

    for dataset_name, df in datasets.items():
        logger.info("Running DQ checks for %s", dataset_name)
        report = run_data_quality_checks(
            df=df,
            dataset_name=dataset_name,
            config=DQ_CONFIG,
            reference_datasets=datasets,
            as_of_date=as_of_date,
        )
        reports.append(report)
        report_path = write_markdown_report(report, args.output_dir)
        logger.info("Wrote DQ report: %s", report_path)

    summary_path = write_summary_json(reports, args.output_dir)
    logger.info("Wrote DQ summary: %s", summary_path)


if __name__ == "__main__":
    main()
