import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation import evaluation


class EvaluatorSourceIntegrityTests(unittest.TestCase):
    def test_clean_checkout_provenance(self):
        responses = [
            type("Result", (), {"returncode": 0, "stdout": "C:/repo", "stderr": ""})(),
            type("Result", (), {"returncode": 0, "stdout": "a" * 40, "stderr": ""})(),
            type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
        ]
        with patch.object(evaluation.subprocess, "run", side_effect=responses):
            provenance = evaluation.collect_evaluator_provenance("C:/repo")
        self.assertTrue(provenance["git_available"])
        self.assertTrue(provenance["clean"], provenance)
        self.assertRegex(provenance["head"], r"^[0-9a-f]{40}$")

    def test_dirty_checkout_provenance(self):
        responses = [
            type("Result", (), {"returncode": 0, "stdout": "C:/repo\\n", "stderr": ""})(),
            type("Result", (), {"returncode": 0, "stdout": "b" * 40 + "\\n", "stderr": ""})(),
            type("Result", (), {"returncode": 0, "stdout": " M evaluation/evaluation.py\\n", "stderr": ""})(),
        ]
        with patch.object(evaluation.subprocess, "run", side_effect=responses):
            provenance = evaluation.collect_evaluator_provenance("C:/repo")
        self.assertFalse(provenance["clean"])
        self.assertIn("evaluation/evaluation.py", provenance["status"])

    def test_provenance_artifact_is_written(self):
        provenance = {"root": "C:/repo", "head": "c" * 40, "clean": True}
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(evaluation, "collect_evaluator_provenance", return_value=provenance):
                saved_provenance = evaluation.require_clean_evaluator_checkout(output_dir)
            saved = json.loads(
                (Path(output_dir) / "evaluator_provenance.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved, saved_provenance)


if __name__ == "__main__":
    unittest.main()