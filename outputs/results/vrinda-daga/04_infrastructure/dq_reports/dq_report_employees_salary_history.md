# Data Quality Report - employees_salary_history

Generated at: 2026-08-24T18:02:54.220353Z

## Summary

- Checks run: 8
- Checks passed: 3
- Checks failed: 5

## Results

| Check | Status | Details |
|---|---|---|
| completeness | FAIL | `{"employee_id": 1.0, "previous_salary": 0.6747, "new_salary": 1.0, "previous_role": 0.6747, "new_role": 1.0, "previous_level": 0.6747, "new_level": 1.0, "effective_date": 1.0, "change_type": 1.0, "change_reason": 1.0}` |
| uniqueness | PASS | `"employee_id, effective_date, change_type, new_salary: 1826 unique / 1826 total; duplicate_rows=0; null_pk_rows=0"` |
| validity_numeric | FAIL | `{"previous_salary": {"min": 10000, "max": 100000, "invalid_type_count": 0, "below_min_count": 100, "above_max_count": 0}, "new_salary": {"min": 10000, "max": 100000, "invalid_type_count": 0, "below_min_count": 100, "above_max_count": 0}}` |
| validity_date | PASS | `{"effective_date": {"allow_future": false, "invalid_date_count": 0, "future_count": 0, "min_date": "2000-02-15", "max_date": "2025-06-30"}}` |
| consistency | FAIL | `[{"rule": "previous_salary >= 0", "violation_count": 0}, {"rule": "new_salary >= 0", "violation_count": 0}, {"rule": "previous_role aligns with previous_level", "violation_count": 325, "examples": [{"role": "Senior Data Engineer", "level": "Mid", "allowed_levels": ["Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Finance Director", "level": "Junior", "allowed_levels": ["Director"]}]}, {"rule": "new_role aligns with new_level", "violation_count": 406, "examples": [{"role": "Senior Data Engineer", "level": "Mid", "allowed_levels": ["Senior", "Lead", "Director"]}, {"role": "Senior Data Engineer", "level": "Junior", "allowed_levels": ["Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Finance Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}]}]` |
| referential_integrity | PASS | `{"employee_id": {"reference": "employees.employee_id", "checked_values": 1826, "invalid_count": 0, "invalid_examples": []}}` |
| distribution | FAIL | `{"change_type": {"top_value": "Annual Raise", "top_count": 638, "top_share": 0.3494, "threshold": 0.3, "is_dominated": true}, "new_level": {"top_value": "Junior", "top_count": 946, "top_share": 0.5181, "threshold": 0.3, "is_dominated": true}}` |
| outliers | FAIL | `{"previous_salary": {"mean": 18758.83, "std": 8292.77, "z_threshold": 3, "outlier_count": 17, "outlier_examples": [44568.0, 48860.0, 56773.0, 64294.0, 45854.0, 47557.0, 45186.0, 44623.0, 50829.0, 43986.0]}, "new_salary": {"mean": 21263.38, "std": 9994.85, "z_threshold": 3, "outlier_count": 22, "outlier_examples": [53484, 59891, 56773, 64294, 71212, 69078, 64478, 64777, 59572, 62516]}}` |

## Raw Result

```json
{
  "dataset_name": "employees_salary_history",
  "checks_run": 8,
  "checks_passed": 3,
  "checks_failed": 5,
  "results": {
    "completeness": {
      "status": "FAIL",
      "details": {
        "employee_id": 1.0,
        "previous_salary": 0.6747,
        "new_salary": 1.0,
        "previous_role": 0.6747,
        "new_role": 1.0,
        "previous_level": 0.6747,
        "new_level": 1.0,
        "effective_date": 1.0,
        "change_type": 1.0,
        "change_reason": 1.0
      },
      "failed_columns": [
        "previous_salary",
        "previous_role",
        "previous_level"
      ]
    },
    "uniqueness": {
      "status": "PASS",
      "details": "employee_id, effective_date, change_type, new_salary: 1826 unique / 1826 total; duplicate_rows=0; null_pk_rows=0"
    },
    "validity_numeric": {
      "status": "FAIL",
      "details": {
        "previous_salary": {
          "min": 10000,
          "max": 100000,
          "invalid_type_count": 0,
          "below_min_count": 100,
          "above_max_count": 0
        },
        "new_salary": {
          "min": 10000,
          "max": 100000,
          "invalid_type_count": 0,
          "below_min_count": 100,
          "above_max_count": 0
        }
      }
    },
    "validity_date": {
      "status": "PASS",
      "details": {
        "effective_date": {
          "allow_future": false,
          "invalid_date_count": 0,
          "future_count": 0,
          "min_date": "2000-02-15",
          "max_date": "2025-06-30"
        }
      }
    },
    "consistency": {
      "status": "FAIL",
      "details": [
        {
          "rule": "previous_salary >= 0",
          "violation_count": 0
        },
        {
          "rule": "new_salary >= 0",
          "violation_count": 0
        },
        {
          "rule": "previous_role aligns with previous_level",
          "violation_count": 325,
          "examples": [
            {
              "role": "Senior Data Engineer",
              "level": "Mid",
              "allowed_levels": [
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Director",
              "level": "Junior",
              "allowed_levels": [
                "Director"
              ]
            }
          ]
        },
        {
          "rule": "new_role aligns with new_level",
          "violation_count": 406,
          "examples": [
            {
              "role": "Senior Data Engineer",
              "level": "Mid",
              "allowed_levels": [
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Senior Data Engineer",
              "level": "Junior",
              "allowed_levels": [
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Finance Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            }
          ]
        }
      ]
    },
    "referential_integrity": {
      "status": "PASS",
      "details": {
        "employee_id": {
          "reference": "employees.employee_id",
          "checked_values": 1826,
          "invalid_count": 0,
          "invalid_examples": []
        }
      }
    },
    "distribution": {
      "status": "FAIL",
      "details": {
        "change_type": {
          "top_value": "Annual Raise",
          "top_count": 638,
          "top_share": 0.3494,
          "threshold": 0.3,
          "is_dominated": true
        },
        "new_level": {
          "top_value": "Junior",
          "top_count": 946,
          "top_share": 0.5181,
          "threshold": 0.3,
          "is_dominated": true
        }
      }
    },
    "outliers": {
      "status": "FAIL",
      "details": {
        "previous_salary": {
          "mean": 18758.83,
          "std": 8292.77,
          "z_threshold": 3,
          "outlier_count": 17,
          "outlier_examples": [
            44568.0,
            48860.0,
            56773.0,
            64294.0,
            45854.0,
            47557.0,
            45186.0,
            44623.0,
            50829.0,
            43986.0
          ]
        },
        "new_salary": {
          "mean": 21263.38,
          "std": 9994.85,
          "z_threshold": 3,
          "outlier_count": 22,
          "outlier_examples": [
            53484,
            59891,
            56773,
            64294,
            71212,
            69078,
            64478,
            64777,
            59572,
            62516
          ]
        }
      }
    }
  }
}
```