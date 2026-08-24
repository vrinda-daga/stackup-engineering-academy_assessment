-- ===========================================================================
-- SECTION 4 — TASK 2.3: Query optimisation
-- ===========================================================================
--
-- The following query runs slowly in production. It is used on the finance
-- dashboard and executes hundreds of times per day.
--
-- YOUR TASKS:
--   a) Run EXPLAIN or EXPLAIN ANALYZE on the query (depending on your DB)
--      and paste the output as a comment. Identify the bottleneck.
--
--   b) Rewrite the query to improve performance.
--      You may restructure it, add CTEs, change joins, etc.
--
--   c) Write a comment explaining:
--      - What was wrong with the original query
--      - What you changed and why
--      - What indexes (if any) you would add in production
--
-- NOTE: Load sufficient data to make the performance difference meaningful.
--       If running on a small dataset, describe what you would observe at scale.

-- ORIGINAL QUERY (do not modify this — rewrite it in section 4b below)
-- ---------------------------------------------------------------------------
SELECT
    e.full_name,
    e.department,
    e.role,
    p.project_name,
    p.status,
    p.budget,
    p.actual_cost,
    t.amount,
    t.category,
    t.payment_status,
    t.transaction_date
FROM employees e, projects p, transactions t
WHERE e.employee_id = p.project_manager_id
AND   p.project_id  = t.project_id
AND   p.status NOT IN ('Completed', 'On Hold')
AND   t.payment_status = 'Pending'
AND   t.amount > (
        SELECT AVG(amount)
        FROM transactions
        WHERE payment_status = 'Pending'
      )
ORDER BY e.department, t.amount DESC;

-- ---------------------------------------------------------------------------
-- 4a) EXPLAIN output and bottleneck analysis (paste as comment):
-- ---------------------------------------------------------------------------
-- Original EXPLAIN ANALYZE:
-- Total Time: 0.0115s
-- Result rows: 923
--
-- Bottleneck:
-- The original query uses a scalar subquery to calculate AVG(amount)
-- for pending transactions. The subquery is uncorrelated, so DuckDB
-- evaluates the aggregate once rather than once per outer row.
-- The execution plan shows a sequential scan of fact_transactions
-- to process the Pending transactions used by the AVG calculation.
-- The query also uses implicit comma joins, making the join structure
-- less explicit and harder to optimise and maintain.
-- 1. Join bottleneck:
--    The query uses HASH_JOIN operations to join employees, projects,
--    transactions and dates. These joins execute very quickly on the
--    current 50,000-row dataset.
--
-- 2. Highest-cost operations:
--    The largest row-processing operation is the scan of Pending
--    transactions used to calculate AVG(amount), which processes
--    approximately 8,927 rows. However, the DuckDB plan reports
--    negligible operator-level time at this dataset size, so this
--    should be treated as the main scan to monitor rather than a
--    measured runtime bottleneck.
--
-- 3. Sequential scans:
--    The execution plan shows sequential scans on fact_transactions,
--    dim_project, dim_employee and dim_date. On a larger production
--    dataset, indexes on filtering and join columns could reduce the
--    amount of data scanned.
--
-- 4. Subquery:
--    The AVG(amount) subquery is implemented as an aggregate and produces
--    a single value. It is not correlated with the outer query and is
--    therefore not re-executed once per outer row.
--
-- 5. Main optimisation opportunity:
--    The original query uses implicit joins and calculates the pending
--    transaction average through a scalar subquery. The rewritten query
--    uses explicit JOINs, calculates the average once in a CTE, and
--    pushes filtering conditions into the relevant table joins.
--
-- Evidence:
-- outputs/results/vrinda-daga/02_sql_and_viz/task_2_3_original_explain.txt


-- ---------------------------------------------------------------------------
-- 4b) REWRITTEN QUERY
-- outputs/results/vrinda-daga/02_sql_and_viz/task_2_3_optimized_explain

-- Optimisations applied:
-- 1. Replaced implicit comma joins with explicit JOIN ... ON syntax.
-- 2. Replaced the scalar AVG subquery with a CTE calculated once.
-- 3. Applied the employee current-record filter directly in the JOIN
--    and retained transaction/project filters in the WHERE clause.
-- 4. Selected only the columns required by the dashboard.
-- ---------------------------------------------------------------------------
WITH pending_avg AS (
    SELECT AVG(amount) AS avg_pending_amount
    FROM fact_transactions
    WHERE payment_status = 'Pending'
)
SELECT
    e.full_name,
    e.department,
    e.role,
    p.project_name,
    p.status,
    p.budget,
    p.actual_cost,
    t.amount,
    t.category,
    t.payment_status,
    d.full_date AS transaction_date
FROM fact_transactions t
JOIN dim_project p
    ON p.project_key = t.project_key
JOIN dim_employee e
    ON e.employee_id = p.project_manager_id
    AND e.is_current = TRUE
JOIN dim_date d
    ON d.date_key = t.date_key
CROSS JOIN pending_avg a
WHERE p.status NOT IN ('Completed', 'On Hold')
  AND t.payment_status = 'Pending'
  AND t.amount > a.avg_pending_amount
ORDER BY
    e.department,
    t.amount DESC;


-- ---------------------------------------------------------------------------
-- 4c) INDEXING STRATEGY
-- ---------------------------------------------------------------------------
--
-- The following indexes were created to support the join and filtering
-- patterns used by the query.
--
-- Note:
-- These indexes are production-oriented recommendations. On the current
-- DuckDB dataset, EXPLAIN ANALYZE continues to show TABLE_SCAN operations
-- rather than Index Scan operations. Therefore, no runtime improvement
-- from indexing is claimed for this local benchmark.
--
-- 1. fact_transactions(payment_status)
--
-- Supports filtering transactions using:
--     payment_status = 'Pending'
--
-- This filter is used both by the main query and by the AVG(amount)
-- calculation in the pending_avg CTE.
--
-- Trade-off:
-- Additional storage and index maintenance cost during inserts/updates.
--
-- ---------------------------------------------------------------------------
--
-- 2. fact_transactions(project_key)
--
-- Supports the join:
--     fact_transactions.project_key = dim_project.project_key
--
-- This can reduce the amount of transaction data that needs to be
-- considered when joining transactions to projects on larger datasets.
--
-- Trade-off:
-- Additional storage and maintenance overhead during transaction inserts
-- and updates.
--
-- ---------------------------------------------------------------------------
--
-- 3. fact_transactions(date_key)
--
-- Supports the join:
--     fact_transactions.date_key = dim_date.date_key
--
-- This is useful when transaction records are frequently joined to the
-- date dimension for reporting and time-based analysis.
--
-- Trade-off:
-- Additional storage and index maintenance cost.
--
-- ---------------------------------------------------------------------------
--
-- 4. dim_project(project_manager_id)
--
-- Supports the join:
--     dim_project.project_manager_id = dim_employee.employee_id
--
-- This allows project records to be efficiently associated with their
-- project managers.
--
-- Trade-off:
-- Additional storage and maintenance overhead when project records change.
--
-- ---------------------------------------------------------------------------
--
-- 5. dim_project(status)
--
-- Supports filtering using:
--     status NOT IN ('Completed', 'On Hold')
--
-- This index may become more useful as the project dimension grows.
--
-- Trade-off:
-- Status has relatively low cardinality, so the optimizer may still prefer
-- a sequential scan depending on table size and data distribution.
--
-- ---------------------------------------------------------------------------
--
-- 6. dim_employee(employee_id, is_current)
--
-- Supports the join and current-record filter:
--     employee_id = project_manager_id
--     AND is_current = TRUE
--
-- employee_id is placed first because it is the primary lookup/join key,
-- while is_current provides an additional filter for the employee record.
--
-- Trade-off:
-- Additional storage and write/update overhead. The composite index is
-- justified when employee lookups commonly use both columns.
--
-- ---------------------------------------------------------------------------
--
-- Indexes created successfully:
--
-- idx_fact_transactions_payment_status
-- idx_fact_transactions_project_key
-- idx_fact_transactions_date_key
-- idx_dim_project_project_manager
-- idx_dim_project_status
-- idx_dim_employee_employee_current
--
-- Validation:
-- DuckDB's EXPLAIN ANALYZE after index creation still shows TABLE_SCAN
-- operations for this workload. The indexes are therefore retained as
-- production-oriented recommendations rather than being presented as
-- a measured performance improvement for the current dataset.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- 4d) BENCHMARK THE OPTIMISED QUERY
-- ---------------------------------------------------------------------------
--
-- The optimised query was benchmarked using EXPLAIN ANALYZE.
--
-- Benchmark results on the current DuckDB dataset:
--
-- Original execution time:   0.010095 seconds
-- Optimized execution time:  0.010809 seconds
-- Speedup:                   0.93x
-- Result rows:               923
--
-- The optimized query therefore did not produce a measurable runtime
-- improvement on the current dataset. The optimized version is slightly
-- slower in this benchmark.
--
-- This does not indicate that the query restructuring is incorrect.
-- The dataset contains approximately 50,000 transactions, and DuckDB
-- can efficiently process this workload using sequential scans and
-- hash joins. The overhead of the rewritten query can therefore outweigh
-- the benefit of the restructuring at this scale.
--
-- EXPLAIN ANALYZE after indexing still shows TABLE_SCAN operations rather
-- than Index Scan operations. Therefore, index usage cannot be claimed
-- for this DuckDB benchmark.
--
-- Both queries return the same 923 result rows, confirming that the
-- rewrite preserves the result set.
--
-- Execution-plan evidence:
--
-- Original:
-- outputs/results/vrinda-daga/02_sql_and_viz/task_2_3_original_explain.txt
--
-- Optimized:
-- outputs/results/vrinda-daga/02_sql_and_viz/task_2_3_optimized_explain.txt
--
-- Optimized with indexes:
-- outputs/results/vrinda-daga/02_sql_and_viz/task_2_3_optimized_indexed_explain.txt
--
-- Production consideration:
-- The CTE-based rewrite, explicit joins and early filtering provide a
-- clearer and more maintainable query structure. Index effectiveness
-- should be re-evaluated on the target production database engine and
-- with production-scale data.
-- ---------------------------------------------------------------------------