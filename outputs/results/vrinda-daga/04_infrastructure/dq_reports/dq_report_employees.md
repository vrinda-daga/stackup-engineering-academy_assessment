# Data Quality Report - employees

Generated at: 2026-08-24T18:02:53.951562Z

## Summary

- Checks run: 8
- Checks passed: 3
- Checks failed: 5

## Results

| Check | Status | Details |
|---|---|---|
| completeness | PASS | `{"employee_id": 1.0, "full_name": 1.0, "email": 0.99, "department": 1.0, "role": 1.0, "level": 1.0, "hire_date": 1.0, "salary": 1.0, "manager_id": 1.0, "region": 1.0, "status": 1.0, "years_experience": 1.0}` |
| uniqueness | PASS | `"employee_id: 1000 unique / 1000 total; duplicate_rows=0; null_pk_rows=0"` |
| validity_numeric | FAIL | `{"salary": {"min": 10000, "max": 100000, "invalid_type_count": 0, "below_min_count": 0, "above_max_count": 0}, "years_experience": {"min": 0, "max": 50, "invalid_type_count": 0, "below_min_count": 5, "above_max_count": 0}}` |
| validity_date | FAIL | `{"hire_date": {"allow_future": false, "invalid_date_count": 8, "future_count": 0, "min_date": "2000-02-15", "max_date": "2024-09-28"}}` |
| consistency | FAIL | `[{"rule": "salary >= 0", "violation_count": 0}, {"rule": "years_experience >= 0", "violation_count": 5}, {"rule": "role aligns with level", "violation_count": 137, "examples": [{"role": "Senior Data Engineer", "level": "Mid", "allowed_levels": ["Senior", "Lead", "Director"]}, {"role": "Senior Data Engineer", "level": "Junior", "allowed_levels": ["Senior", "Lead", "Director"]}, {"role": "Product Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "Account Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}, {"role": "IT Manager", "level": "Junior", "allowed_levels": ["Mid", "Senior", "Lead", "Director"]}]}]` |
| referential_integrity | PASS | `{"manager_id": {"reference": "employees.employee_id", "checked_values": 995, "invalid_count": 0, "invalid_examples": []}}` |
| distribution | FAIL | `{"department": {"top_value": "Sales", "top_count": 98, "top_share": 0.098, "threshold": 0.3, "is_dominated": false}, "level": {"top_value": "Mid", "top_count": 366, "top_share": 0.366, "threshold": 0.3, "is_dominated": true}, "region": {"top_value": "Abu Dhabi", "top_count": 434, "top_share": 0.434, "threshold": 0.3, "is_dominated": true}, "status": {"top_value": "Active", "top_count": 960, "top_share": 0.96, "threshold": 0.3, "is_dominated": true}}` |
| outliers | FAIL | `{"salary": {"mean": 26461.53, "std": 11291.4, "z_threshold": 3, "outlier_count": 17, "outlier_examples": [64478, 67841, 67180, 63626, 62270, 67168, 69078, 62533, 76507, 62750]}, "years_experience": {"mean": 6.26, "std": 4.67, "z_threshold": 3, "outlier_count": 13, "outlier_examples": [23, 22, 23, 24, 25, 24, 22, 24, 21, 23]}}` |

## Raw Result

```json
{
  "dataset_name": "employees",
  "checks_run": 8,
  "checks_passed": 3,
  "checks_failed": 5,
  "results": {
    "completeness": {
      "status": "PASS",
      "details": {
        "employee_id": 1.0,
        "full_name": 1.0,
        "email": 0.99,
        "department": 1.0,
        "role": 1.0,
        "level": 1.0,
        "hire_date": 1.0,
        "salary": 1.0,
        "manager_id": 1.0,
        "region": 1.0,
        "status": 1.0,
        "years_experience": 1.0
      },
      "failed_columns": []
    },
    "uniqueness": {
      "status": "PASS",
      "details": "employee_id: 1000 unique / 1000 total; duplicate_rows=0; null_pk_rows=0"
    },
    "validity_numeric": {
      "status": "FAIL",
      "details": {
        "salary": {
          "min": 10000,
          "max": 100000,
          "invalid_type_count": 0,
          "below_min_count": 0,
          "above_max_count": 0
        },
        "years_experience": {
          "min": 0,
          "max": 50,
          "invalid_type_count": 0,
          "below_min_count": 5,
          "above_max_count": 0
        }
      }
    },
    "validity_date": {
      "status": "FAIL",
      "details": {
        "hire_date": {
          "allow_future": false,
          "invalid_date_count": 8,
          "future_count": 0,
          "min_date": "2000-02-15",
          "max_date": "2024-09-28"
        }
      }
    },
    "consistency": {
      "status": "FAIL",
      "details": [
        {
          "rule": "salary >= 0",
          "violation_count": 0
        },
        {
          "rule": "years_experience >= 0",
          "violation_count": 5
        },
        {
          "rule": "role aligns with level",
          "violation_count": 137,
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
              "role": "Product Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "Account Manager",
              "level": "Junior",
              "allowed_levels": [
                "Mid",
                "Senior",
                "Lead",
                "Director"
              ]
            },
            {
              "role": "IT Manager",
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
        "manager_id": {
          "reference": "employees.employee_id",
          "checked_values": 995,
          "invalid_count": 0,
          "invalid_examples": []
        }
      }
    },
    "distribution": {
      "status": "FAIL",
      "details": {
        "department": {
          "top_value": "Sales",
          "top_count": 98,
          "top_share": 0.098,
          "threshold": 0.3,
          "is_dominated": false
        },
        "level": {
          "top_value": "Mid",
          "top_count": 366,
          "top_share": 0.366,
          "threshold": 0.3,
          "is_dominated": true
        },
        "region": {
          "top_value": "Abu Dhabi",
          "top_count": 434,
          "top_share": 0.434,
          "threshold": 0.3,
          "is_dominated": true
        },
        "status": {
          "top_value": "Active",
          "top_count": 960,
          "top_share": 0.96,
          "threshold": 0.3,
          "is_dominated": true
        }
      }
    },
    "outliers": {
      "status": "FAIL",
      "details": {
        "salary": {
          "mean": 26461.53,
          "std": 11291.4,
          "z_threshold": 3,
          "outlier_count": 17,
          "outlier_examples": [
            64478,
            67841,
            67180,
            63626,
            62270,
            67168,
            69078,
            62533,
            76507,
            62750
          ]
        },
        "years_experience": {
          "mean": 6.26,
          "std": 4.67,
          "z_threshold": 3,
          "outlier_count": 13,
          "outlier_examples": [
            23,
            22,
            23,
            24,
            25,
            24,
            22,
            24,
            21,
            23
          ]
        }
      }
    }
  }
}
```