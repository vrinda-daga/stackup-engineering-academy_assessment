"""
etl_pipeline.py
StackUp Engineering Academy - Data Engineering Assessment

Pillar 1: Foundations
Task 1.1 - Clean and transform projects.csv
Task 1.3 - Identify and fix data quality issues in employees.csv
"""

import logging
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

BASE_DIR = Path(__file__).resolve().parents[4]

DATA_DIR = BASE_DIR / "datasets"

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "results"
    / "vrinda-daga"
    / "01_foundations"
)

PROJECTS_INPUT = DATA_DIR / "projects.csv"

PROJECTS_OUTPUT = OUTPUT_DIR / "projects_clean.csv"

# ==============================================================================
# TASK 1.3 - EMPLOYEE PATHS
# ==============================================================================

EMPLOYEES_INPUT = DATA_DIR / "employees.csv"

EMPLOYEES_OUTPUT = OUTPUT_DIR / "employees_clean.csv"


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

    # Standardize priority values to ensure consistent risk-level comparisons.
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
    # Missing dates will result in missing duration values
    # --------------------------------------------------------------------------

    df["duration_days"] = (
        df["end_date"] - df["start_date"]
    ).dt.days

    # --------------------------------------------------------------------------
    # 7. Calculate budget utilisation percentage
    # Avoid division by zero by replacing 0 budget with NaN
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
    #
    # High:
    #   - Priority is Critical
    #   OR
    #   - Project is over budget
    #
    # Medium:
    #   - Priority is High
    #   OR
    #   - Budget utilisation is greater than 90%
    #
    # Low:
    #   - All other projects
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
# SAVE OUTPUT
# ==============================================================================

def save_projects(
    df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Save the cleaned projects dataset.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    logger.info(
        "Cleaned projects data saved to: %s",
        output_path
    )

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
    # Values such as -999 and 99999-01-01 are not valid dates.
    # Convert invalid values to null rather than inventing a date.
    # --------------------------------------------------------------------------

    invalid_hire_dates = pd.to_datetime(
    df["hire_date"],
    errors="coerce"
    ).isna().sum()

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
    # Negative experience is not logically valid, so replace it with zero.
    # --------------------------------------------------------------------------

    negative_experience = (
        pd.to_numeric(
            df["years_experience"],
            errors="coerce"
        ) < 0
    )

    df.loc[negative_experience, "years_experience"] = 0

    logger.info(
        "Negative experience values corrected: %d",
        negative_experience.sum()
    )

    # --------------------------------------------------------------------------
    # Issue 4: Self-referencing manager
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
# TASK 1.3 - SAVE EMPLOYEES
# ==============================================================================

def save_employees(
    df: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Save the cleaned employee dataset.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    logger.info(
        "Cleaned employee data saved to: %s",
        output_path
    )

# ==============================================================================
# PIPELINE ENTRY POINT
# ==============================================================================

def main() -> None:
    """
    Run Task 1.1 and Task 1.3 end to end.
    """

    logger.info("=" * 60)
    logger.info("Starting Foundations ETL")
    logger.info("=" * 60)

    # --------------------------------------------------------------------------
    # Task 1.1 - Projects
    # --------------------------------------------------------------------------

    raw_projects = load_projects(PROJECTS_INPUT)

    clean_projects = transform_projects(raw_projects)

    save_projects(
        clean_projects,
        PROJECTS_OUTPUT
    )

    # --------------------------------------------------------------------------
    # Task 1.3 - Employees
    # --------------------------------------------------------------------------

    raw_employees = load_employees(EMPLOYEES_INPUT)

    clean_emp = clean_employees(raw_employees)

    save_employees(
        clean_emp,
        EMPLOYEES_OUTPUT
    )

    logger.info("=" * 60)
    logger.info("Foundations ETL completed successfully")
    logger.info(
        "Projects output shape: %s",
        clean_projects.shape
    )
    logger.info(
        "Employees output shape: %s",
        clean_emp.shape
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    main()