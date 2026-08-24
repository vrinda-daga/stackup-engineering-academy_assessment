"""
=============================================================
StackUp Engineering Academy — Data Engineering Assessment
Starter File: spark_starter.py
Pillar: Big Data Processing — Task 3.1
=============================================================

SCENARIO
--------
The events_stream/ folder contains a growing log of platform events emitted
by the project management system (status changes, logins, escalations,
document uploads, meetings, budget updates, task completions).

New event files will be added monthly (events_2025_01.jsonl, events_2025_02.jsonl, ...).
Your pipeline must process ALL files in the folder, not just one.

Your job is to use PySpark to process the events at scale and produce four
aggregated output tables that feed the executive analytics dashboard.

TASKS
-----
  Task 3.1a → Load and parse all JSONL files from events_stream/
  Task 3.1b → Clean and validate the event schema
  Task 3.1c → Produce four aggregated output DataFrames (see below)
  Task 3.1d → Write outputs in Parquet format to outputs/spark/

OUTPUT TABLES REQUIRED
----------------------
  1. project_activity_summary
       project_id | total_events | escalation_count | task_completions |
       last_event_timestamp | unique_users

  2. user_activity_summary
       user_id | login_count | actions_taken | projects_touched | last_active

  3. escalation_log
       event_id | project_id | raised_by | raised_at | severity |
       resolved | resolved_by | resolved_at | resolution_time_hours

  4. daily_event_volume
       event_date | event_type | event_count

HOW TO RUN
----------
  spark-submit starter_files/spark_starter.py

  Or in a notebook / local Spark session:
  exec(open('starter_files/spark_starter.py').read())
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, MapType
)
from pyspark.sql.window import Window
import os
import shutil
import time

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EVENTS_DIR = os.path.join(BASE_DIR, "datasets", "events_stream")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "results", "vrinda-daga", "03_big_data", "spark")


# ==============================================================================
# STEP 1 — Initialise Spark
# ==============================================================================

def get_spark_session() -> SparkSession:
    """
    Create and return a local SparkSession.

    TODO:
      - Set the app name to "PresightEventsProcessing"
      - Configure for local mode with all available cores
      - Set log level to WARN to reduce noise
    """
    """
    Create and return a local SparkSession.
    """
    spark = (
        SparkSession.builder
        .appName("PresightEventsProcessing")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "24")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.cleanup-failures.ignored", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return spark


def _is_windows_hadoop_write_error(exc: Exception) -> bool:
    """
    Detect the local Windows Hadoop/native-file errors that can happen during
    Spark Parquet writes when winutils/hadoop.dll is missing or mismatched.
    """
    message = str(exc)
    markers = (
        "NativeIO$Windows.access0",
        "UnsatisfiedLinkError",
        "winutils.exe",
        "HADOOP_HOME and hadoop.home.dir are unset",
    )
    return os.name == "nt" and any(marker in message for marker in markers)


def _write_parquet_with_pyarrow(df, path: str, partition_cols=None):
    """
    Local Windows fallback for small aggregated Spark outputs.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    partition_cols = partition_cols or []

    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)

    pandas_df = df.toPandas()
    table = pa.Table.from_pandas(pandas_df, preserve_index=False)

    if partition_cols:
        pq.write_to_dataset(
            table,
            root_path=path,
            partition_cols=partition_cols,
        )
    else:
        pq.write_table(table, os.path.join(path, "part-00000.parquet"))


# ==============================================================================
# STEP 2 — Load events
# ==============================================================================

def load_events(spark: SparkSession, events_dir: str):
    """
    Load all JSONL files from the events_stream directory.

    Schema:
      event_id    STRING
      event_type  STRING
      project_id  STRING (nullable)
      user_id     STRING
      timestamp   TIMESTAMP
      payload     MAP<STRING, STRING>  ← the payload is a nested JSON object

    TODO:
      - Define the schema explicitly (do not use inferSchema)
      - Load all .jsonl files in events_dir using a wildcard path
      - Parse the timestamp field correctly
      - Cast the payload field appropriately
      - Return the raw DataFrame
    """
    """
    Load all JSONL files from the events_stream directory
    using an explicit schema.
    """

    schema = StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("project_id", StringType(), True),
        StructField("user_id", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField(
            "payload",
            MapType(StringType(), StringType()),
            True
        )
    ])

     # Resolve all monthly JSONL files explicitly.
    # This avoids Windows/Hadoop wildcard expansion issues.
    event_files = sorted(
        os.path.join(events_dir, filename)
        for filename in os.listdir(events_dir)
        if filename.startswith("events_") and filename.endswith(".jsonl")
    )

    if not event_files:
        raise FileNotFoundError(
            f"No event files found in: {events_dir}"
        )

    print(f"Event files found: {len(event_files)}")

    df = (
        spark.read
        .schema(schema)
        .json(event_files)
    )

    print(f"Loaded events: {df.count()}")

    df.printSchema()

    return df


# ==============================================================================
# STEP 3 — Validate and clean
# ==============================================================================

def validate_events(df):
    """
    Validate and clean the raw events DataFrame.

    TODO:
      - Drop rows where event_id or user_id is null
      - Drop duplicate event_ids (keep first occurrence)
      - Add a column: event_date (date only, derived from timestamp)
      - Add a column: event_hour (hour of day, derived from timestamp)
      - Log the count of rows dropped at each step
      - Return the cleaned DataFrame
    """
    """
    Validate and clean the raw events DataFrame.

    Steps:
      1. Remove rows with null event_id
      2. Remove rows with null user_id
      3. Remove duplicate event_id values, keeping the earliest timestamp
      4. Add event_date
      5. Add event_hour
      6. Add event_month for partitioning
    """

    from pyspark.sql.window import Window

    # ------------------------------------------------------------------
    # Initial count
    # ------------------------------------------------------------------
    initial_count = df.count()
    print(f"Rows before validation: {initial_count}")

    # ------------------------------------------------------------------
    # 1. Remove null event_id
    # ------------------------------------------------------------------
    before = df.count()

    df = df.filter(F.col("event_id").isNotNull())

    after = df.count()

    print(
        f"Null event_id removed: {before - after} rows "
        f"(remaining: {after})"
    )

    # ------------------------------------------------------------------
    # 2. Remove null user_id
    # ------------------------------------------------------------------
    before = df.count()

    df = df.filter(F.col("user_id").isNotNull())

    after = df.count()

    print(
        f"Null user_id removed: {before - after} rows "
        f"(remaining: {after})"
    )

    # ------------------------------------------------------------------
    # 3. Remove duplicate event_id values
    #    Keep the earliest event by timestamp
    # ------------------------------------------------------------------
    before = df.count()

    window_spec = (
        Window
        .partitionBy("event_id")
        .orderBy(F.col("timestamp").asc())
    )

    df = (
        df
        .withColumn("_row_number", F.row_number().over(window_spec))
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )

    after = df.count()

    print(
        f"Duplicate event_id rows removed: {before - after} rows "
        f"(remaining: {after})"
    )

    # ------------------------------------------------------------------
    # 4. Add event_date
    # ------------------------------------------------------------------
    df = df.withColumn(
        "event_date",
        F.to_date(F.col("timestamp"))
    )

    # ------------------------------------------------------------------
    # 5. Add event_hour
    # ------------------------------------------------------------------
    df = df.withColumn(
        "event_hour",
        F.hour(F.col("timestamp"))
    )

    # ------------------------------------------------------------------
    # 6. Add event_month
    #    Format: YYYY-MM
    # ------------------------------------------------------------------
    df = df.withColumn(
        "event_month",
        F.date_format(F.col("timestamp"), "yyyy-MM")
    )

    final_count = df.count()

    print(f"Rows after validation: {final_count}")
    
    return df


# ==============================================================================
# STEP 4 — Aggregations
# ==============================================================================

def project_activity_summary(df):
    """
    Produce a per-project activity summary.

    Required columns:
      project_id, total_events, escalation_count, task_completions,
      last_event_timestamp, unique_users,
      --added document_uploads,unique_event_types

    TODO:
      - Filter out rows where project_id is null (login events)
      - Use groupBy + agg to compute each metric
      - For escalation_count: count rows where event_type = 'escalation_raised'
      - For task_completions: count rows where event_type = 'task_completed'
      - Sort by total_events descending
    """

    # Exclude login events, which have NULL project_id
    project_df = df.filter(F.col("project_id").isNotNull())

    summary = (
        project_df
        .groupBy("project_id")
        .agg(
            F.count("*").alias("total_events"),

            F.sum(
                F.when(
                    F.col("event_type") == "escalation_raised", 1
                ).otherwise(0)
            ).alias("escalation_count"),

            F.sum(
                F.when(
                    F.col("event_type") == "task_completed", 1
                ).otherwise(0)
            ).alias("task_completions"),

            F.sum(
                F.when(
                    F.col("event_type") == "document_uploaded", 1
                ).otherwise(0)
            ).alias("document_uploads"),

            F.max("timestamp").alias("last_event_timestamp"),

            F.countDistinct("user_id").alias("unique_users"),

            F.countDistinct("event_type").alias("unique_event_types")
        )
        .orderBy(F.col("total_events").desc())
    )

    return summary


def user_activity_summary(df):
    """
    Produce a per-user activity summary.

    Required columns:
      user_id, login_count, actions_taken, projects_touched, last_active
      also added logout_count,first_active, active_days

    TODO:
      - actions_taken = all events EXCLUDING logins
      - projects_touched = count of distinct project_ids per user (excluding nulls)
      - last_active = max timestamp per user
    """
    summary = (
        df
        .groupBy("user_id")
        .agg(
            # Number of login events
            F.sum(
                F.when(
                    F.col("event_type") == "login", 1
                ).otherwise(0)
            ).alias("login_count"),

            # Number of logout events
            F.sum(
                F.when(
                    F.col("event_type") == "logout", 1
                ).otherwise(0)
            ).alias("logout_count"),

            # All events except login/logout
            F.sum(
                F.when(
                    ~F.col("event_type").isin("login", "logout"), 1
                ).otherwise(0)
            ).alias("actions_taken"),

            # Distinct projects, excluding NULL project_ids
            F.countDistinct("project_id").alias("projects_touched"),

            # First activity timestamp
            F.min("timestamp").alias("first_active"),

            # Last activity timestamp
            F.max("timestamp").alias("last_active"),

            # Number of distinct days the user was active
            F.countDistinct("event_date").alias("active_days")
        )
        .orderBy(F.col("actions_taken").desc())
    )

    return summary


def escalation_log(df):
    """
    Build a resolved escalation log by joining escalation_raised
    and escalation_resolved events.

    Required columns:
      event_id, project_id, raised_by, raised_at, severity,
      resolved, resolved_by, resolved_at, resolution_time_hours

    TODO:
      - Filter for escalation_raised events → extract severity from payload
      - Filter for escalation_resolved events → extract resolved_by and resolution from payload
      - Join on project_id (a project can only have one open escalation at a time)
      - Compute resolution_time_hours = (resolved_at - raised_at) in hours
      - Set resolved = True/False based on whether a matching resolved event exists
    """

    # ---------------------------------------------------------------
    # 1. Extract escalation_raised events
    # ---------------------------------------------------------------
    raised = (
        df
        .filter(F.col("event_type") == "escalation_raised")
        .select(
            F.col("event_id").alias("raised_event_id"),
            "project_id",
            F.col("user_id").alias("raised_by"),
            F.col("timestamp").alias("raised_at"),
            F.col("payload")["severity"].alias("severity")
        )
    )

    # ---------------------------------------------------------------
    # 2. Extract escalation_resolved events
    # ---------------------------------------------------------------
    resolved = (
        df
        .filter(F.col("event_type") == "escalation_resolved")
        .select(
            F.col("event_id").alias("resolved_event_id"),
            "project_id",
            F.col("user_id").alias("resolved_by"),
            F.col("timestamp").alias("resolved_at")
        )
    )

    # ---------------------------------------------------------------
    # 3. Match resolutions to the same project AND later timestamp
    # ---------------------------------------------------------------
    candidates = (
        raised.alias("r")
        .join(
            resolved.alias("s"),
            (
                (F.col("r.project_id") == F.col("s.project_id")) &
                (F.col("s.resolved_at") >= F.col("r.raised_at"))
            ),
            "left"
        )
    )

    # ---------------------------------------------------------------
    # 4. For each raised event, keep ONLY the first resolution
    #    occurring after it
    # ---------------------------------------------------------------
    window_spec = (
        Window
        .partitionBy("r.raised_event_id")
        .orderBy(F.col("s.resolved_at").asc())
    )

    matched = (
        candidates
        .withColumn("resolution_rank", F.row_number().over(window_spec))
        .filter(F.col("resolution_rank") == 1)
    )

    # ---------------------------------------------------------------
    # 5. Calculate resolution duration
    # ---------------------------------------------------------------
    result = (
        matched
        .select(
            F.col("r.raised_event_id").alias("event_id"),
            F.col("r.project_id").alias("project_id"),
            F.col("r.raised_by").alias("raised_by"),
            F.col("r.raised_at").alias("raised_at"),
            F.col("r.severity").alias("severity"),

            F.col("s.resolved_at").isNotNull().alias("resolved"),

            F.col("s.resolved_by").alias("resolved_by"),
            F.col("s.resolved_at").alias("resolved_at"),

            (
                (
                    F.col("s.resolved_at").cast("long")
                    - F.col("r.raised_at").cast("long")
                ) / 3600.0
            ).alias("resolution_time_hours")
        )
    )

    return result


def daily_event_volume(df):
    """
    Produce a daily event volume breakdown by event type.

    Required columns:
      event_date, event_type, event_count

    TODO:
      - Group by event_date and event_type
      - Sort by event_date asc, event_count desc
    """
    # ---------------------------------------------------------------
    # 1. Count events by date and event type
    # ---------------------------------------------------------------
    daily_counts = (
        df
        .groupBy("event_date", "event_type")
        .agg(
            F.count("*").alias("event_count")
        )
    )

    # ---------------------------------------------------------------
    # 2. Calculate cumulative count per event type
    # ---------------------------------------------------------------
    cumulative_window = (
        Window
        .partitionBy("event_type")
        .orderBy("event_date")
        .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    )

    result = (
        daily_counts
        .withColumn(
            "cumulative_count",
            F.sum("event_count").over(cumulative_window)
        )
        .orderBy(
            F.col("event_date").asc(),
            F.col("event_count").desc()
        )
    )

    return result


def peak_usage_analysis(df):
    """
    Identify the top 20 peak usage windows.

    For each event_date and event_hour combination:
      - total_events: total number of events
      - unique_users: distinct users active
      - event_types_per_hour: distinct event types

    Return the top 20 hours ordered by total_events descending.
    """

    result = (
        df
        .groupBy("event_date", "event_hour")
        .agg(
            F.count("*").alias("total_events"),
            F.countDistinct("user_id").alias("unique_users"),
            F.countDistinct("event_type").alias("event_types_per_hour")
        )
        .orderBy(F.col("total_events").desc())
        .limit(20)
    )

    return result

# ==============================================================================
# STEP 5 — Write outputs
# ==============================================================================


def write_parquet(df, name: str, output_dir: str):
    """
    Write a DataFrame to Parquet.

    TODO:
      - Write to output_dir/name/
      - Use overwrite mode
      - Partition daily_event_volume by event_date
      - Partition escalation_log by severity
      - Print row count after writing
      - Using coalesce(1) for small output tables
    """
    path = os.path.join(output_dir, name)

    print(f"\n=== Writing {name} ===")
    print(f"Output path: {path}")

    partition_cols = []
    write_df = df

    if name == "daily_event_volume":
        partition_cols = ["event_date"]
    elif name == "escalation_log":
        partition_cols = ["severity"]
        write_df = df.coalesce(1)
    else:
        write_df = df.coalesce(1)

    row_count = df.count()

    if os.name == "nt":
        print(
            "Using pyarrow local Parquet writer on Windows to avoid "
            "Hadoop native-file issues."
        )
        _write_parquet_with_pyarrow(df, path, partition_cols)
    else:
        try:
            writer = write_df.write.mode("overwrite")

            if partition_cols:
                writer = writer.partitionBy(*partition_cols)

            writer.parquet(path)

        except Exception as exc:
            if not _is_windows_hadoop_write_error(exc):
                raise

            print(
                "Spark Parquet writer hit a Windows Hadoop native-file issue; "
                "falling back to pyarrow for local output."
            )
            _write_parquet_with_pyarrow(df, path, partition_cols)

    print(f"Rows written: {row_count}")
    print(f"Write complete: {path}")


def materialize_aggregation(name: str, build_dataframe, timings: dict):
    """
    Build and count an aggregation so Spark's lazy execution is included
    in the timing baseline.
    """
    start_time = time.time()
    result = build_dataframe().cache()
    row_count = result.count()
    elapsed = time.time() - start_time

    timings[name] = elapsed
    print(f"{name} aggregation time: {elapsed:.2f}s ({row_count} rows)")

    return result


# ==============================================================================
# PIPELINE ENTRY POINT
# ==============================================================================

def run_pipeline():
    pipeline_start = time.time()
    aggregation_timings = {}

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    spark = get_spark_session()

    raw         = load_events(spark, EVENTS_DIR)
    clean       = validate_events(raw).cache()
    total_rows_processed = clean.count()

    proj_summary = materialize_aggregation(
        "project_activity_summary",
        lambda: project_activity_summary(clean),
        aggregation_timings
    )
    user_summary = materialize_aggregation(
        "user_activity_summary",
        lambda: user_activity_summary(clean),
        aggregation_timings
    )
    esc_log = materialize_aggregation(
        "escalation_log",
        lambda: escalation_log(clean),
        aggregation_timings
    )
    daily_vol = materialize_aggregation(
        "daily_event_volume",
        lambda: daily_event_volume(clean),
        aggregation_timings
    )
    peak_usage = materialize_aggregation(
        "peak_usage_analysis",
        lambda: peak_usage_analysis(clean),
        aggregation_timings
    )

    write_parquet(proj_summary, "project_activity_summary", OUTPUT_DIR)
    write_parquet(user_summary, "user_activity_summary",    OUTPUT_DIR)
    write_parquet(esc_log,      "escalation_log",           OUTPUT_DIR)
    write_parquet(daily_vol,    "daily_event_volume",       OUTPUT_DIR)
    write_parquet(peak_usage,   "peak_usage_analysis",       OUTPUT_DIR)

    total_execution_time = time.time() - pipeline_start
    events_per_second = (
        total_rows_processed / total_execution_time
        if total_execution_time > 0
        else 0
    )

    print("\n" + "=" * 70)
    print("3.1e - Performance Baseline")
    print("=" * 70)
    print(f"Total execution time: {total_execution_time:.2f}s")
    print("Per-aggregation timing:")

    for name, elapsed in aggregation_timings.items():
        print(f"  - {name}: {elapsed:.2f}s")

    print(f"Total rows processed: {total_rows_processed}")
    print(f"Events processed per second: {events_per_second:.2f}")

    spark.stop()
    print("Spark pipeline complete.")



if __name__ == "__main__":
    run_pipeline()
   
