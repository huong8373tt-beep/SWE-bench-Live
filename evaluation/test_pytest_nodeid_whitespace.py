import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.evaluation import default_pytest_parser, parse_log_pytest


class PytestNodeIdWhitespaceTests(unittest.TestCase):
    def test_parametrized_node_id_preserves_spaces(self):
        log = "PASSED tests/test_example.py::test_value[bytes data]\n"
        self.assertEqual(
            parse_log_pytest(log, None),
            {"tests/test_example.py::test_value[bytes data]": "PASSED"},
        )
        self.assertEqual(
            default_pytest_parser(log),
            {"tests/test_example.py::test_value[bytes data]": "pass"},
        )

    def test_distinct_space_containing_cases_do_not_collide(self):
        log = "\n".join(
            [
                "FAILED tests/test_example.py::test_value[bytes data]",
                "PASSED tests/test_example.py::test_value[bytes text]",
            ]
        )
        self.assertEqual(
            parse_log_pytest(log, None),
            {
                "tests/test_example.py::test_value[bytes data]": "FAILED",
                "tests/test_example.py::test_value[bytes text]": "PASSED",
            },
        )

    def test_failed_parametrized_node_id_stops_before_failure_message(self):
        log = "FAILED tests/test_example.py::test_value[bytes data] - assertion failed"
        self.assertEqual(
            parse_log_pytest(log, None),
            {"tests/test_example.py::test_value[bytes data]": "FAILED"},
        )

    def test_ordinary_pytest_lines_keep_first_node_token(self):
        log = "PASSED tests/test_example.py::test_value\n"
        self.assertEqual(
            parse_log_pytest(log, None),
            {"tests/test_example.py::test_value": "PASSED"},
        )


if __name__ == "__main__":
    unittest.main()