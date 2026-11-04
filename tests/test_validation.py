import unittest
import pandas as pd
from app.validation import validate_dataframe
from app.analysis import build_monthly_summary, dataframe_from_records

class ValidationTests(unittest.TestCase):
    def test_valid_rows_are_accepted(self):
        raw = pd.DataFrame([{
            "observation_date": "2026-01-01",
            "location": "Hyderabad",
            "temperature": 28.5,
            "humidity": 55,
            "rainfall": 0,
        }])
        valid, report = validate_dataframe(raw)
        self.assertEqual(len(valid), 1)
        self.assertEqual(report["accepted_rows"], 1)

    def test_invalid_humidity_is_rejected(self):
        raw = pd.DataFrame([{
            "observation_date": "2026-01-01",
            "location": "Hyderabad",
            "temperature": 28.5,
            "humidity": 120,
            "rainfall": 0,
        }])
        valid, report = validate_dataframe(raw)
        self.assertEqual(len(valid), 0)
        self.assertEqual(report["invalid_humidity"], 1)

    def test_duplicate_row_is_rejected(self):
        row = {
            "observation_date": "2026-01-01",
            "location": "Hyderabad",
            "temperature": 28.5,
            "humidity": 55,
            "rainfall": 0,
        }
        valid, report = validate_dataframe(pd.DataFrame([row, row]))
        self.assertEqual(len(valid), 1)
        self.assertEqual(report["duplicate_rows"], 1)

    def test_missing_measurement_is_counted_not_zeroed(self):
        raw = pd.DataFrame([{
            "observation_date": "2026-01-01",
            "location": "Hyderabad",
            "temperature": None,
            "humidity": 55,
            "rainfall": None,
        }])
        valid, report = validate_dataframe(raw)
        self.assertEqual(len(valid), 1)
        self.assertEqual(report["missing_temperatures"], 1)
        self.assertEqual(report["missing_rainfall"], 1)
        self.assertTrue(pd.isna(valid.iloc[0]["temperature"]))

    def test_monthly_summary_groups_by_location(self):
        records = [
            {"observation_date": "2026-01-01", "location": "A", "temperature": 10, "humidity": 50, "rainfall": 1},
            {"observation_date": "2026-01-02", "location": "A", "temperature": 20, "humidity": 60, "rainfall": 2},
            {"observation_date": "2026-01-01", "location": "B", "temperature": 30, "humidity": 70, "rainfall": 3},
        ]
        df = dataframe_from_records(records)
        summary = build_monthly_summary(df)
        self.assertEqual(len(summary), 2)
        a = summary[summary["location"] == "A"].iloc[0]
        self.assertAlmostEqual(a["avg_temperature"], 15)

if __name__ == "__main__":
    unittest.main()
