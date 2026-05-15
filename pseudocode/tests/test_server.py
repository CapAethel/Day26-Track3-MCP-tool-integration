import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import SQLiteAdapter, ValidationError
from init_db import create_database


class SQLiteAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = create_database(reset=True)
        cls.adapter = SQLiteAdapter(cls.db_path)

    def test_search_with_filters_and_order(self):
        rows = self.adapter.search(
            table="students",
            filters=[{"column": "cohort", "op": "eq", "value": "A1"}],
            order_by="name",
            descending=False,
            limit=5,
        )
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("name", rows[0])

    def test_insert_returns_payload(self):
        result = self.adapter.insert(
            table="students",
            values={"name": "Fiona Le", "cohort": "B2", "email": "fiona@example.com", "age": 21},
        )
        self.assertIn("id", result)
        self.assertEqual(result["table"], "students")

    def test_aggregate_avg_score(self):
        rows = self.adapter.aggregate(table="enrollments", metric="avg", column="score")
        self.assertEqual(len(rows), 1)
        self.assertIsNotNone(rows[0]["value"])

    def test_invalid_table_rejected(self):
        with self.assertRaises(ValidationError):
            self.adapter.search(table="not_a_table")

    def test_invalid_operator_rejected(self):
        with self.assertRaises(ValidationError):
            self.adapter.search(
                table="students",
                filters=[{"column": "cohort", "op": "bad_op", "value": "A1"}],
            )


if __name__ == "__main__":
    unittest.main()
