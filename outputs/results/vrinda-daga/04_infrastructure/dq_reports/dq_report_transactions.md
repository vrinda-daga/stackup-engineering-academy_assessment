# Data Quality Report - transactions

Generated at: 2026-08-24T18:02:54.065408Z

## Summary

- Checks run: 9
- Checks passed: 7
- Checks failed: 2

## Results

| Check | Status | Details |
|---|---|---|
| completeness | PASS | `{"transaction_id": 1.0, "project_id": 1.0, "vendor_id": 1.0, "vendor_name": 1.0, "category": 1.0, "amount": 0.9852, "currency": 1.0, "transaction_date": 1.0, "approved_by": 0.9511, "payment_status": 1.0, "invoice_ref": 1.0, "notes": 0.785}` |
| uniqueness | PASS | `"transaction_id: 50000 unique / 50000 total; duplicate_rows=0; null_pk_rows=0"` |
| validity_numeric | PASS | `{"amount": {"min": 0, "max": 1000000, "invalid_type_count": 0, "below_min_count": 0, "above_max_count": 0}}` |
| validity_date | PASS | `{"transaction_date": {"allow_future": false, "invalid_date_count": 0, "future_count": 0, "min_date": "2022-01-06", "max_date": "2026-08-04"}}` |
| consistency | PASS | `[{"rule": "amount >= 0", "violation_count": 0}]` |
| referential_integrity | PASS | `{"project_id": {"reference": "projects.project_id", "checked_values": 50000, "invalid_count": 0, "invalid_examples": []}, "approved_by": {"reference": "employees.employee_id", "checked_values": 47556, "invalid_count": 0, "invalid_examples": []}}` |
| distribution | FAIL | `{"currency": {"top_value": "AED", "top_count": 50000, "top_share": 1.0, "threshold": 0.3, "is_dominated": true}, "payment_status": {"top_value": "Paid", "top_count": 37562, "top_share": 0.7512, "threshold": 0.3, "is_dominated": true}, "category": {"top_value": "Software", "top_count": 10161, "top_share": 0.2032, "threshold": 0.3, "is_dominated": false}}` |
| freshness | PASS | `{"column": "transaction_date", "max_date": "2026-08-04", "as_of_date": "2026-08-24", "age_days": 20, "max_age_days": 30}` |
| outliers | FAIL | `{"amount": {"mean": 62848.38, "std": 118165.66, "z_threshold": 3, "outlier_count": 1593, "outlier_examples": [767323.0, 607104.0, 605824.0, 435715.0, 429668.0, 422839.0, 641933.0, 417954.0, 662396.0, 420012.0]}}` |

## Raw Result

```json
{
  "dataset_name": "transactions",
  "checks_run": 9,
  "checks_passed": 7,
  "checks_failed": 2,
  "results": {
    "completeness": {
      "status": "PASS",
      "details": {
        "transaction_id": 1.0,
        "project_id": 1.0,
        "vendor_id": 1.0,
        "vendor_name": 1.0,
        "category": 1.0,
        "amount": 0.9852,
        "currency": 1.0,
        "transaction_date": 1.0,
        "approved_by": 0.9511,
        "payment_status": 1.0,
        "invoice_ref": 1.0,
        "notes": 0.785
      },
      "failed_columns": []
    },
    "uniqueness": {
      "status": "PASS",
      "details": "transaction_id: 50000 unique / 50000 total; duplicate_rows=0; null_pk_rows=0"
    },
    "validity_numeric": {
      "status": "PASS",
      "details": {
        "amount": {
          "min": 0,
          "max": 1000000,
          "invalid_type_count": 0,
          "below_min_count": 0,
          "above_max_count": 0
        }
      }
    },
    "validity_date": {
      "status": "PASS",
      "details": {
        "transaction_date": {
          "allow_future": false,
          "invalid_date_count": 0,
          "future_count": 0,
          "min_date": "2022-01-06",
          "max_date": "2026-08-04"
        }
      }
    },
    "consistency": {
      "status": "PASS",
      "details": [
        {
          "rule": "amount >= 0",
          "violation_count": 0
        }
      ]
    },
    "referential_integrity": {
      "status": "PASS",
      "details": {
        "project_id": {
          "reference": "projects.project_id",
          "checked_values": 50000,
          "invalid_count": 0,
          "invalid_examples": []
        },
        "approved_by": {
          "reference": "employees.employee_id",
          "checked_values": 47556,
          "invalid_count": 0,
          "invalid_examples": []
        }
      }
    },
    "distribution": {
      "status": "FAIL",
      "details": {
        "currency": {
          "top_value": "AED",
          "top_count": 50000,
          "top_share": 1.0,
          "threshold": 0.3,
          "is_dominated": true
        },
        "payment_status": {
          "top_value": "Paid",
          "top_count": 37562,
          "top_share": 0.7512,
          "threshold": 0.3,
          "is_dominated": true
        },
        "category": {
          "top_value": "Software",
          "top_count": 10161,
          "top_share": 0.2032,
          "threshold": 0.3,
          "is_dominated": false
        }
      }
    },
    "freshness": {
      "status": "PASS",
      "details": {
        "column": "transaction_date",
        "max_date": "2026-08-04",
        "as_of_date": "2026-08-24",
        "age_days": 20,
        "max_age_days": 30
      }
    },
    "outliers": {
      "status": "FAIL",
      "details": {
        "amount": {
          "mean": 62848.38,
          "std": 118165.66,
          "z_threshold": 3,
          "outlier_count": 1593,
          "outlier_examples": [
            767323.0,
            607104.0,
            605824.0,
            435715.0,
            429668.0,
            422839.0,
            641933.0,
            417954.0,
            662396.0,
            420012.0
          ]
        }
      }
    }
  }
}
```