import csv
import tempfile
import unittest
from pathlib import Path

import plugin


class QueryPaginationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with (Path(self.directory.name) / "items.csv").open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(["id"])
            writer.writerows([[i] for i in range(1, 251)])

    def query(self, **params):
        return plugin.handle("execute_query", {
            "params": {"database": self.directory.name},
            "query": 'SELECT id FROM items ORDER BY CAST(id AS INTEGER)',
            **params,
        })

    def test_host_limit_controls_page_size_and_offset(self):
        first = self.query(limit=25, page=1)
        second = self.query(limit=25, page=2)
        self.assertEqual(first["pagination"]["page_size"], 25)
        self.assertEqual(len(first["rows"]), 25)
        self.assertEqual(first["rows"][0], ["1"])
        self.assertEqual(second["rows"][0], ["26"])
        self.assertTrue(second["pagination"]["has_more"])

    def test_sql_limit_is_respected_before_page_slicing(self):
        result = plugin.handle("execute_query", {
            "params": {"database": self.directory.name},
            "query": "SELECT id FROM items ORDER BY CAST(id AS INTEGER) LIMIT 7",
            "limit": 25,
            "page": 1,
        })
        self.assertEqual(len(result["rows"]), 7)
        self.assertEqual(result["pagination"]["total_rows"], 7)
        self.assertFalse(result["pagination"]["has_more"])

    def test_legacy_page_size_still_works(self):
        self.assertEqual(len(self.query(page_size=12)["rows"]), 12)


if __name__ == "__main__":
    unittest.main()
