-- =============================================================
-- StackUp Engineering Academy — Data Engineering Assessment
-- Starter File: data_model_starter.sql
-- Pillars: Foundations (Task 1.2) | SQL & Viz (Tasks 2.1, 2.3)
-- =============================================================
--
-- SCENARIO
-- --------
-- Presight runs a project management platform. You are designing
-- the data warehouse layer that will power analytics dashboards
-- for Finance, Operations, and Executive leadership.
--
-- The source data comes from three operational tables:
--   projects      → datasets/projects.csv
--   employees     → datasets/employees.csv
--   transactions  → datasets/transactions.json
--
-- HOW TO USE
-- ----------
-- This file is divided into four sections.
-- Work through each section in order.
-- Run against your local database (SQLite, PostgreSQL, or DuckDB all work).
-- =============================================================


-- ===========================================================================
-- SECTION 1 — TASK 1.2: Design the data model (Star Schema)
-- ===========================================================================
--
-- Design a star schema for the Presight project analytics warehouse.
--
-- REQUIREMENTS:
--   - One central fact table: fact_transactions
--   - At minimum four dimension tables:
--       dim_project, dim_employee, dim_vendor, dim_date
--   - fact_transactions must include foreign keys to all four dimensions
--   - dim_date must be a proper date dimension (not just a date column)
--     with columns for year, quarter, month, month_name, week, day, is_weekend
--   - Use surrogate keys (integer PKs) on all dimension tables
--   - Preserve the original source system IDs as natural keys
--   - Add a dim_employee_project bridge table to handle the many-to-many
--     relationship between employees and projects (one employee can manage
--     multiple projects; one project can have multiple team members)
--
-- BONUS:
--   - Add a slowly-changing dimension (SCD Type 2) design to dim_employee
--     to track salary changes over time
--
-- DOCUMENT YOUR DECISIONS:
--   Write a comment before each table explaining why you designed it that way.

-- TODO: Create dim_date
-- YOUR CODE HERE

-- ===========================================================================
-- TASK 1.2 — STAR SCHEMA
-- ===========================================================================

-- ===========================================================================
-- RESET TABLES
-- ===========================================================================
-- Drop dependent tables first so the schema can be rebuilt safely.
-- This allows the SQL file to be rerun during development and validation.

DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS bridge_employee_project;
DROP TABLE IF EXISTS dim_vendor;
DROP TABLE IF EXISTS dim_employee;
DROP TABLE IF EXISTS dim_project;
DROP TABLE IF EXISTS dim_date;

DROP TABLE IF EXISTS stg_salary_history;
DROP TABLE IF EXISTS stg_employees;

-- ---------------------------------------------------------------------------
-- dim_date
-- ---------------------------------------------------------------------------
-- Design decision:
-- Provides reusable calendar attributes for analytical reporting.
-- date_key is the surrogate key and full_date preserves the actual date.

CREATE OR REPLACE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    week INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- ---------------------------------------------------------------------------
-- dim_project
-- ---------------------------------------------------------------------------
-- Design decision:
-- Stores descriptive, financial and analytical attributes for projects.
-- project_key is the warehouse surrogate key, while project_id preserves
-- the source-system natural key.
--
-- The table is populated from the cleaned Task 1.1 project output.

CREATE OR REPLACE TABLE dim_project (
    project_key INTEGER PRIMARY KEY,
    project_id VARCHAR(50) NOT NULL UNIQUE,
    project_name VARCHAR(255),
    department VARCHAR(100),
    status VARCHAR(50),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15,2),
    actual_cost DECIMAL(15,2),
    project_manager_id VARCHAR(50),
    priority VARCHAR(50),
    region VARCHAR(100),
    budget_variance DECIMAL(15,2),
    is_over_budget BOOLEAN,
    duration_days INTEGER,
    budget_utilisation_pct DECIMAL(10,2),
    status_category VARCHAR(50),
    risk_level VARCHAR(50)
);

-- ---------------------------------------------------------------------------
-- dim_employee
-- ---------------------------------------------------------------------------
-- Design decision:
-- SCD Type 2 dimension that preserves historical versions of employee
-- salary, role and level.
--
-- employee_key uniquely identifies each version.
-- employee_id remains the source-system natural key.
-- valid_from and valid_to define the validity period.
-- is_current identifies the current version.

CREATE OR REPLACE TABLE dim_employee (
    employee_key INTEGER PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    department VARCHAR(100),
    role VARCHAR(100),
    level VARCHAR(50),
    hire_date DATE,
    salary DECIMAL(15,2),
    manager_id VARCHAR(50),
    region VARCHAR(100),
    status VARCHAR(50),
    years_experience INTEGER,
    valid_from DATE NOT NULL,
    valid_to DATE NOT NULL,
    is_current BOOLEAN NOT NULL,
    change_reason VARCHAR(255)
);

-- ---------------------------------------------------------------------------
-- dim_vendor
-- ---------------------------------------------------------------------------
-- Design decision:
-- Stores vendor information derived from the transaction source.
-- vendor_key is the warehouse surrogate key and vendor_id preserves
-- the source-system natural key.

CREATE OR REPLACE TABLE dim_vendor (
    vendor_key INTEGER PRIMARY KEY,
    vendor_id VARCHAR(100) NOT NULL UNIQUE,
    vendor_name VARCHAR(255)
);

-- ---------------------------------------------------------------------------
-- bridge_employee_project
-- ---------------------------------------------------------------------------
-- Design decision:
-- Represents the many-to-many relationship between employees and projects.
-- An employee may work on multiple projects and a project may have
-- multiple employees.

CREATE OR REPLACE TABLE bridge_employee_project (
    employee_key INTEGER NOT NULL,
    project_key INTEGER NOT NULL,

    PRIMARY KEY (employee_key, project_key),

    FOREIGN KEY (employee_key)
        REFERENCES dim_employee(employee_key),

    FOREIGN KEY (project_key)
        REFERENCES dim_project(project_key)
);

-- ---------------------------------------------------------------------------
-- fact_transactions
-- ---------------------------------------------------------------------------
-- Design decision:
-- Central transaction fact table.
-- Each transaction links to project, employee, vendor and date dimensions
-- using surrogate foreign keys.

CREATE OR REPLACE TABLE fact_transactions (
    transaction_key INTEGER PRIMARY KEY,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    project_key INTEGER NOT NULL,
    employee_key INTEGER,
    vendor_key INTEGER,
    date_key INTEGER NOT NULL,
    amount DECIMAL(15,2),
    category VARCHAR(100),
    payment_status VARCHAR(50),

    FOREIGN KEY (project_key)
        REFERENCES dim_project(project_key),

    FOREIGN KEY (employee_key)
        REFERENCES dim_employee(employee_key),

    FOREIGN KEY (vendor_key)
        REFERENCES dim_vendor(vendor_key),

    FOREIGN KEY (date_key)
        REFERENCES dim_date(date_key)
);

-- ===========================================================================
-- TASK 1.2 — STAGING TABLES
-- ===========================================================================

-- Staging table for the current employee source.
-- Keeps the source data available in DuckDB for the SCD Type 2 transformation.

CREATE OR REPLACE TABLE stg_employees AS
SELECT *
FROM read_csv_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/datasets/employees.csv',
    header = true
);


-- Staging table for historical salary, role and level changes.
-- This source is used to construct historical versions of dim_employee.

CREATE OR REPLACE TABLE stg_salary_history AS
SELECT *
FROM read_csv_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/datasets/employees_salary_history.csv',
    header = true
);

-- ===========================================================================
-- TASK 1.2 — SCD TYPE 2: POPULATE DIM_EMPLOYEE
-- ===========================================================================
--
-- Design approach:
-- - Employees with salary/role history receive one dimension version per
--   effective date.
-- - valid_from records when each version becomes effective.
-- - valid_to records when the next version becomes effective.
-- - The latest version is marked is_current = TRUE.
-- - Employees without history receive one current record.
-- - employee_key is the surrogate key.
-- - employee_id remains the source-system natural key.
-- - 9999-12-31 is used as the sentinel end date for current records.
--
-- Same-day change handling:
-- The source contains one employee/date combination with multiple changes
-- (EMP0084 on 2025-03-02). Since the source does not contain a timestamp or
-- sequence column, the highest new_salary is used as a deterministic
-- tie-breaker. This retains one effective state per employee per date and
-- prevents zero-length validity periods.


-- ---------------------------------------------------------------------------
-- Step 1: Load employees with salary history
-- ---------------------------------------------------------------------------

INSERT INTO dim_employee (
    employee_key,
    employee_id,
    full_name,
    email,
    department,
    role,
    level,
    hire_date,
    salary,
    manager_id,
    region,
    status,
    years_experience,
    valid_from,
    valid_to,
    is_current,
    change_reason
)

WITH clean_history AS (

    -- Keep one record per employee per effective date.
    -- For same-day changes, retain the record with the highest new salary.

    SELECT *
    FROM (
        SELECT
            h.*,
            ROW_NUMBER() OVER (
                PARTITION BY employee_id, effective_date
                ORDER BY new_salary DESC
            ) AS rn
        FROM stg_salary_history h
    ) ranked_history
    WHERE rn = 1
),

history_with_dates AS (

    -- Find the start date of the next employee version.

    SELECT
        h.*,
        LEAD(effective_date) OVER (
            PARTITION BY employee_id
            ORDER BY effective_date
        ) AS next_effective_date
    FROM clean_history h
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY h.employee_id, h.effective_date
    ) AS employee_key,

    e.employee_id,
    e.full_name,
    e.email,
    e.department,

    h.new_role AS role,
    h.new_level AS level,

    TRY_CAST(e.hire_date AS DATE) AS hire_date,

    h.new_salary AS salary,

    e.manager_id,
    e.region,
    e.status,
    e.years_experience,

    CAST(h.effective_date AS DATE) AS valid_from,

    COALESCE(
        CAST(h.next_effective_date AS DATE),
        DATE '9999-12-31'
    ) AS valid_to,

    CASE
        WHEN h.next_effective_date IS NULL THEN TRUE
        ELSE FALSE
    END AS is_current,

    h.change_reason

FROM history_with_dates h
JOIN stg_employees e
    ON e.employee_id = h.employee_id;


-- ---------------------------------------------------------------------------
-- Step 2: Load employees without salary history
-- ---------------------------------------------------------------------------

INSERT INTO dim_employee (
    employee_key,
    employee_id,
    full_name,
    email,
    department,
    role,
    level,
    hire_date,
    salary,
    manager_id,
    region,
    status,
    years_experience,
    valid_from,
    valid_to,
    is_current,
    change_reason
)

SELECT
    (
        SELECT COALESCE(MAX(employee_key), 0)
        FROM dim_employee
    )
    + ROW_NUMBER() OVER (
        ORDER BY e.employee_id
    ) AS employee_key,

    e.employee_id,
    e.full_name,
    e.email,
    e.department,
    e.role,
    e.level,

    TRY_CAST(e.hire_date AS DATE) AS hire_date,

    e.salary,
    e.manager_id,
    e.region,
    e.status,
    e.years_experience,

    -- Invalid hire dates are replaced with a sentinel date because
    -- valid_from is required for every SCD Type 2 record.
    COALESCE(
    TRY_CAST(e.hire_date AS DATE),
    DATE '1900-01-01'
    ) AS valid_from,

    DATE '9999-12-31' AS valid_to,

    TRUE AS is_current,

    NULL AS change_reason

FROM stg_employees e

WHERE NOT EXISTS (
    SELECT 1
    FROM stg_salary_history h
    WHERE h.employee_id = e.employee_id
);

-- ===========================================================================
-- TASK 1.2 — POPULATE DIM_DATE
-- ===========================================================================
--
-- Design decision:
-- The date dimension provides reusable calendar attributes for reporting.
-- One row represents one calendar date.
-- date_key uses YYYYMMDD format as the surrogate key.
-- The range covers the dates required by the project and transaction data.
--

INSERT INTO dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    week,
    day,
    day_of_week,
    is_weekend
)

SELECT
    CAST(STRFTIME(d, '%Y%m%d') AS INTEGER) AS date_key,
    d AS full_date,
    EXTRACT(YEAR FROM d) AS year,
    EXTRACT(QUARTER FROM d) AS quarter,
    EXTRACT(MONTH FROM d) AS month,
    STRFTIME(d, '%B') AS month_name,
    EXTRACT(WEEK FROM d) AS week,
    EXTRACT(DAY FROM d) AS day,
    EXTRACT(DAYOFWEEK FROM d) AS day_of_week,

    CASE
        WHEN EXTRACT(DAYOFWEEK FROM d) IN (0, 6)
        THEN TRUE
        ELSE FALSE
    END AS is_weekend

FROM generate_series(
    DATE '2020-01-01',
    DATE '2030-12-31',
    INTERVAL '1 day'
) AS dates(d);

-- ===========================================================================
-- TASK 1.2 — POPULATE DIM_PROJECT
-- ===========================================================================
--
-- Design decision:
-- The project dimension is populated from the cleaned Task 1.1 output.
-- project_key is the warehouse surrogate key.
-- project_id remains the source-system natural key.
-- Derived project attributes created during Task 1.1 are retained because
-- they are useful for analytical reporting.
-- ===========================================================================

INSERT INTO dim_project (
    project_key,
    project_id,
    project_name,
    department,
    status,
    start_date,
    end_date,
    budget,
    actual_cost,
    project_manager_id,
    priority,
    region,
    budget_variance,
    is_over_budget,
    duration_days,
    budget_utilisation_pct,
    status_category,
    risk_level
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY project_id
    ) AS project_key,

    project_id,
    project_name,
    department,
    status,

    TRY_CAST(start_date AS DATE) AS start_date,
    TRY_CAST(end_date AS DATE) AS end_date,

    budget,
    actual_cost,
    project_manager_id,
    priority,
    region,
    budget_variance,
    is_over_budget,
    duration_days,
    budget_utilisation_pct,
    status_category,
    risk_level

FROM read_csv_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/outputs/results/vrinda-daga/01_foundations/projects_clean.csv',
    header = true
);


-- ===========================================================================
-- TASK 1.2 — POPULATE DIM_VENDOR
-- ===========================================================================
--
-- Design decision:
-- Vendors are derived from the transaction source because vendor information
-- is not provided as a separate operational export.
-- vendor_key is the warehouse surrogate key.
-- vendor_id is preserved as the source-system natural key.
-- One row is created per unique vendor.
-- ===========================================================================

INSERT INTO dim_vendor (
    vendor_key,
    vendor_id,
    vendor_name
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY vendor_id
    ) AS vendor_key,
    vendor_id,
    MAX(vendor_name) AS vendor_name

FROM read_json_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/datasets/transactions.json'
)
WHERE vendor_id IS NOT NULL
GROUP BY vendor_id;


-- ===========================================================================
-- TASK 1.2 — POPULATE BRIDGE_EMPLOYEE_PROJECT
-- ===========================================================================
--
-- Design decision:
-- The bridge resolves the many-to-many relationship between employees
-- and projects.
--
-- The transaction source provides:
--   approved_by → employee_id
--   project_id  → project_id
--
-- Each employee/project combination is stored only once.
-- The current SCD Type 2 employee version is used for employee_key.
-- ===========================================================================

INSERT INTO bridge_employee_project (
    employee_key,
    project_key
)

SELECT DISTINCT
    e.employee_key,
    p.project_key

FROM read_json_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/datasets/transactions.json'
) t

JOIN dim_employee e
    ON t.approved_by = e.employee_id
    AND e.is_current = TRUE

JOIN dim_project p
    ON t.project_id = p.project_id

WHERE t.approved_by IS NOT NULL
  AND t.project_id IS NOT NULL;

-- ===========================================================================
-- TASK 1.2 — POPULATE FACT_TRANSACTIONS
-- ===========================================================================
--
-- Design decision:
-- fact_transactions is the central transactional fact table.
-- Each transaction is linked to the project, employee, vendor and date
-- dimensions using their warehouse surrogate keys.
--
-- The transaction_id is retained as the source-system natural key.
-- transaction_date is mapped to dim_date using full_date.
-- ===========================================================================

INSERT INTO fact_transactions (
    transaction_key,
    transaction_id,
    project_key,
    employee_key,
    vendor_key,
    date_key,
    amount,
    category,
    payment_status
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY t.transaction_id
    ) AS transaction_key,

    t.transaction_id,

    p.project_key,

    e.employee_key,

    v.vendor_key,

    d.date_key,

    t.amount,
    t.category,
    t.payment_status

FROM read_json_auto(
    'C:/Users/vrinda.daga/projects/stackup-engineering-academy_assessment/datasets/transactions.json'
) t

JOIN dim_project p
    ON t.project_id = p.project_id

LEFT JOIN dim_employee e
    ON t.approved_by = e.employee_id
    AND e.is_current = TRUE

JOIN dim_vendor v
    ON t.vendor_id = v.vendor_id

JOIN dim_date d
    ON TRY_CAST(t.transaction_date AS DATE) = d.full_date;