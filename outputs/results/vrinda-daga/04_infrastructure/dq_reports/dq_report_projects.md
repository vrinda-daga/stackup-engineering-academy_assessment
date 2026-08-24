# Data Quality Report - projects

Generated at: 2026-08-24T18:02:53.883712Z

## Summary

- Checks run: 8
- Checks passed: 5
- Checks failed: 3

## Results

| Check | Status | Details |
|---|---|---|
| completeness | FAIL | `{"project_id": 1.0, "project_name": 1.0, "department": 1.0, "status": 1.0, "start_date": 0.87, "end_date": 0.428, "budget": 0.936, "actual_cost": 0.88, "project_manager_id": 1.0, "priority": 1.0, "region": 1.0}` |
| uniqueness | PASS | `"project_id: 500 unique / 500 total; duplicate_rows=0; null_pk_rows=0"` |
| validity_numeric | PASS | `{"budget": {"min": 0, "max": 10000000, "invalid_type_count": 0, "below_min_count": 0, "above_max_count": 0}, "actual_cost": {"min": 0, "max": 10000000, "invalid_type_count": 0, "below_min_count": 0, "above_max_count": 0}}` |
| validity_date | PASS | `{"start_date": {"allow_future": false, "invalid_date_count": 0, "future_count": 0, "min_date": "2022-01-04", "max_date": "2025-02-28"}, "end_date": {"allow_future": true, "invalid_date_count": 0, "future_count": 0, "min_date": "2022-04-29", "max_date": "2026-08-07"}}` |
| consistency | PASS | `[{"rule": "start_date before end_date", "violation_count": 0}, {"rule": "budget >= 0", "violation_count": 0}, {"rule": "actual_cost >= 0", "violation_count": 0}]` |
| referential_integrity | PASS | `{"project_manager_id": {"reference": "employees.employee_id", "checked_values": 500, "invalid_count": 0, "invalid_examples": []}}` |
| distribution | FAIL | `{"department": {"top_value": "HR", "top_count": 49, "top_share": 0.098, "threshold": 0.3, "is_dominated": false}, "status": {"top_value": "Completed", "top_count": 214, "top_share": 0.428, "threshold": 0.3, "is_dominated": true}, "priority": {"top_value": "Medium", "top_count": 213, "top_share": 0.426, "threshold": 0.3, "is_dominated": true}, "region": {"top_value": "Abu Dhabi", "top_count": 220, "top_share": 0.44, "threshold": 0.3, "is_dominated": true}}` |
| outliers | FAIL | `{"budget": {"mean": 564636.75, "std": 604768.16, "z_threshold": 3, "outlier_count": 0, "outlier_examples": []}, "actual_cost": {"mean": 515605.47, "std": 606864.36, "z_threshold": 3, "outlier_count": 2, "outlier_examples": [2381174.0, 2381747.0]}}` |

## Raw Result

```json
{
  "dataset_name": "projects",
  "checks_run": 8,
  "checks_passed": 5,
  "checks_failed": 3,
  "results": {
    "completeness": {
      "status": "FAIL",
      "details": {
        "project_id": 1.0,
        "project_name": 1.0,
        "department": 1.0,
        "status": 1.0,
        "start_date": 0.87,
        "end_date": 0.428,
        "budget": 0.936,
        "actual_cost": 0.88,
        "project_manager_id": 1.0,
        "priority": 1.0,
        "region": 1.0
      },
      "failed_columns": [
        "start_date",
        "end_date",
        "actual_cost"
      ]
    },
    "uniqueness": {
      "status": "PASS",
      "details": "project_id: 500 unique / 500 total; duplicate_rows=0; null_pk_rows=0"
    },
    "validity_numeric": {
      "status": "PASS",
      "details": {
        "budget": {
          "min": 0,
          "max": 10000000,
          "invalid_type_count": 0,
          "below_min_count": 0,
          "above_max_count": 0
        },
        "actual_cost": {
          "min": 0,
          "max": 10000000,
          "invalid_type_count": 0,
          "below_min_count": 0,
          "above_max_count": 0
        }
      }
    },
    "validity_date": {
      "status": "PASS",
      "details": {
        "start_date": {
          "allow_future": false,
          "invalid_date_count": 0,
          "future_count": 0,
          "min_date": "2022-01-04",
          "max_date": "2025-02-28"
        },
        "end_date": {
          "allow_future": true,
          "invalid_date_count": 0,
          "future_count": 0,
          "min_date": "2022-04-29",
          "max_date": "2026-08-07"
        }
      }
    },
    "consistency": {
      "status": "PASS",
      "details": [
        {
          "rule": "start_date before end_date",
          "violation_count": 0
        },
        {
          "rule": "budget >= 0",
          "violation_count": 0
        },
        {
          "rule": "actual_cost >= 0",
          "violation_count": 0
        }
      ]
    },
    "referential_integrity": {
      "status": "PASS",
      "details": {
        "project_manager_id": {
          "reference": "employees.employee_id",
          "checked_values": 500,
          "invalid_count": 0,
          "invalid_examples": []
        }
      }
    },
    "distribution": {
      "status": "FAIL",
      "details": {
        "department": {
          "top_value": "HR",
          "top_count": 49,
          "top_share": 0.098,
          "threshold": 0.3,
          "is_dominated": false
        },
        "status": {
          "top_value": "Completed",
          "top_count": 214,
          "top_share": 0.428,
          "threshold": 0.3,
          "is_dominated": true
        },
        "priority": {
          "top_value": "Medium",
          "top_count": 213,
          "top_share": 0.426,
          "threshold": 0.3,
          "is_dominated": true
        },
        "region": {
          "top_value": "Abu Dhabi",
          "top_count": 220,
          "top_share": 0.44,
          "threshold": 0.3,
          "is_dominated": true
        }
      }
    },
    "outliers": {
      "status": "FAIL",
      "details": {
        "budget": {
          "mean": 564636.75,
          "std": 604768.16,
          "z_threshold": 3,
          "outlier_count": 0,
          "outlier_examples": []
        },
        "actual_cost": {
          "mean": 515605.47,
          "std": 606864.36,
          "z_threshold": 3,
          "outlier_count": 2,
          "outlier_examples": [
            2381174.0,
            2381747.0
          ]
        }
      }
    }
  }
}
```