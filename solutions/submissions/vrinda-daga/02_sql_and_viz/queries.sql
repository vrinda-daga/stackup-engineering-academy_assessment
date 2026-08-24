-- ===========================================================================
-- SECTION 3 — TASK 2.1: Answer five business questions
-- ===========================================================================
--
-- Write a SQL query to answer each question.
-- For each query, add a comment explaining your approach.
-- Queries must run without errors against your loaded data.

-- ---------------------------------------------------------------------------
-- Q1. BUDGET PERFORMANCE
-- Which departments have spent more than 90% of their total budget across
-- all projects? Show department, total_budget, total_actual_cost,
-- spend_percentage, and whether they are over budget.
-- Order by spend_percentage descending.
-- ---------------------------------------------------------------------------

    SELECT
        department,
        SUM(budget) AS total_budget,
        SUM(actual_cost) AS total_actual_cost,
        ROUND(
            SUM(actual_cost) * 100.0
            / NULLIF(SUM(budget), 0),
            2
        ) AS spend_percentage,
        CASE
            WHEN SUM(actual_cost) > SUM(budget)
            THEN TRUE
            ELSE FALSE
        END AS over_budget

    FROM dim_project

    GROUP BY department

    HAVING
        SUM(actual_cost) * 100.0
        / NULLIF(SUM(budget), 0) > 90

    ORDER BY spend_percentage DESC;


-- ---------------------------------------------------------------------------
-- Q2. PROJECT MANAGER WORKLOAD
-- Which project managers are currently managing more than three active project
-- (status = 'In Progress')? Show their full name, email, number of active
-- projects, and the combined budget they are responsible for.

-- Approach:
-- Join active projects to the current dim_employee SCD2 records,
-- aggregate project count and financial responsibility by manager,
-- and retain managers with more than three active projects.
-- ---------------------------------------------------------------------------

    SELECT
        e.full_name,
        e.email,
        COUNT(*) AS active_project_count,
        SUM(p.budget) AS combined_budget_responsibility,
        SUM(p.actual_cost) AS combined_actual_spend

    FROM dim_project p

    JOIN dim_employee e
        ON p.project_manager_id = e.employee_id
        AND e.is_current = TRUE

    WHERE p.status = 'In Progress'

    GROUP BY
        e.employee_id,
        e.full_name,
        e.email

    HAVING COUNT(*) > 3

    ORDER BY active_project_count DESC;


-- ---------------------------------------------------------------------------
-- Q3. VENDOR CONCENTRATION RISK
-- Identify vendors who account for more than 5% of total transaction spend
-- across all projects. Show vendor_name, total_spend, percentage_of_total.
-- This is a risk indicator — flag these vendors in the output.
-- Approach:
-- Aggregate spend by vendor, calculate each vendor's percentage of total
-- transaction spend, and classify concentration risk as HIGH, MEDIUM, or NORMAL.
-- ---------------------------------------------------------------------------

    WITH vendor_spend AS (
        SELECT
            v.vendor_name,
            SUM(f.amount) AS total_spend,
            COUNT(*) AS transaction_count
        FROM fact_transactions f
        JOIN dim_vendor v
            ON f.vendor_key = v.vendor_key
        GROUP BY v.vendor_name
    ),

    total_spend AS (
        SELECT SUM(amount) AS total_amount
        FROM fact_transactions
    )

    SELECT
        vendor_name,
        total_spend,
        transaction_count,
        ROUND(
            total_spend * 100.0 / NULLIF(total_amount, 0),
            2
        ) AS percentage_of_total_spend,
        CASE
            WHEN total_spend * 100.0 / NULLIF(total_amount, 0) > 10
                THEN 'HIGH'
            WHEN total_spend * 100.0 / NULLIF(total_amount, 0) >= 5
                THEN 'MEDIUM'
            ELSE 'NORMAL'
        END AS risk_flag

    FROM vendor_spend
    CROSS JOIN total_spend

    WHERE total_spend * 100.0 / NULLIF(total_amount, 0) > 5

    ORDER BY percentage_of_total_spend DESC;


-- ---------------------------------------------------------------------------
-- Q4 — Projects with open financial issues
--Find all projects with pending or disputed transactions totalling more than 50,000 AED. 
--These need finance team attention.
--Required columns: project_id, project_name, department, project_status, 
--open_transaction_count, open_transaction_value
--Order by: open_transaction_value descending
-- Approach:
-- Filter pending and disputed transactions, aggregate their count and value
-- by project, then retain projects exceeding the 50,000 AED threshold.
-- ---------------------------------------------------------------------------

    SELECT
        p.project_id,
        p.project_name,
        p.department,
        p.status AS project_status,
        COUNT(*) AS open_transaction_count,
        SUM(f.amount) AS open_transaction_value

    FROM fact_transactions f

    JOIN dim_project p
        ON f.project_key = p.project_key

    WHERE f.payment_status IN ('Pending', 'Disputed')

    GROUP BY
        p.project_id,
        p.project_name,
        p.department,
        p.status

    HAVING SUM(f.amount) > 50000

    ORDER BY open_transaction_value DESC;


-- ---------------------------------------------------------------------------
-- Q5. MONTHLY SPEND TREND
-- Show the total transaction amount per month for the past 12 months,
-- broken down by category (Software, Consulting, Cloud Services, etc.)
-- Format the output as: year_month | category | total_amount | running_total
-- (running_total should accumulate within each category across months)
-- Approach:
-- First aggregate transaction spend by month and category. Then use window
-- functions to calculate the category-level running total and MoM change.
-- ---------------------------------------------------------------------------

    WITH monthly_spend AS (
        SELECT
            STRFTIME(d.full_date, '%Y-%m') AS year_month,
            f.category,
            SUM(f.amount) AS monthly_spend

        FROM fact_transactions f

        JOIN dim_date d
            ON f.date_key = d.date_key

        GROUP BY
            STRFTIME(d.full_date, '%Y-%m'),
            f.category
    ),

    calculated AS (
        SELECT
            year_month,
            category,
            monthly_spend,

            SUM(monthly_spend) OVER (
                PARTITION BY category
                ORDER BY year_month
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) AS running_total,

            LAG(monthly_spend) OVER (
                PARTITION BY category
                ORDER BY year_month
            ) AS previous_month_spend

        FROM monthly_spend
    )

    SELECT
        year_month,
        category,
        monthly_spend,
        running_total,

        ROUND(
            (monthly_spend - previous_month_spend)
            * 100.0
            / NULLIF(previous_month_spend, 0),
            2
        ) AS month_over_month_pct_change

    FROM calculated

    ORDER BY
        category,
        year_month;

-- ---------------------------------------------------------------------------
-- Q6 — Employee compensation history analysis
--Using dim_employee SCD2 data, identify employees who received the largest single salary increase (in absolute AED terms).

--Required columns: employee_id, full_name, change_date (the valid_from of the new record), previous_salary, new_salary, increase_amount, increase_pct
--Order by: increase_amount descending, top 20

--Hint: Self-join dim_employee on employee_id matching the previous version's valid_to to the next version's valid_from.
-- Approach:
-- Self-join consecutive SCD2 versions where the previous version's valid_to
-- equals the new version's valid_from, then calculate the salary increase.
-- ---------------------------------------------------------------------------

    SELECT
        new.employee_id,
        new.full_name,
        new.valid_from AS change_date,
        old.salary AS previous_salary,
        new.salary AS new_salary,
        new.salary - old.salary AS increase_amount,
        ROUND(
            (new.salary - old.salary) * 100.0
            / NULLIF(old.salary, 0),
            2
        ) AS increase_pct

    FROM dim_employee new

    JOIN dim_employee old
        ON new.employee_id = old.employee_id
        AND old.valid_to = new.valid_from

    WHERE new.salary > old.salary

    ORDER BY increase_amount DESC
    LIMIT 20;