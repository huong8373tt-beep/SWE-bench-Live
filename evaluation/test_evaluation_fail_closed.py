import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation import evaluation


class FakeRuntime:
    def __init__(self, patch_results):
        self.patch_results = iter(patch_results)
        self.patches = []
        self.commands = []
        self.cleaned_up = False
        self.mnt_host = tempfile.gettempdir()
        self.mnt_container = "/mnt_tmp"

    def apply_patch(self, patch, verbose=False):
        self.patches.append((patch, verbose))
        return next(self.patch_results)

    def send_command(self, command):
        self.commands.append(command)
        return SimpleNamespace(output="")

    def cleanup(self):
        self.cleaned_up = True


class FailClosedEvaluationTests(unittest.TestCase):
    def test_test_patch_failure_stops_before_candidate_or_commands(self):
        runtime = FakeRuntime([False])
        with patch.object(evaluation.SetupRuntime, "from_launch_image", return_value=runtime):
            with self.assertRaisesRegex(RuntimeError, "Benchmark test patch did not apply cleanly"):
                evaluation.evaluate_instance(
                    "example__project-1",
                    "example-image",
                    "rebuild-command",
                    "run-tests",
                    "collect-log",
                    "test-patch",
                    "candidate-patch",
                    "custom",
                    "linux",
                    tempfile.gettempdir(),
                )
        self.assertEqual(runtime.patches, [("test-patch", True)])
        self.assertEqual(runtime.commands, [])
        self.assertTrue(runtime.cleaned_up)

    def test_candidate_patch_failure_stops_before_rebuild_or_tests(self):
        runtime = FakeRuntime([True, False])
        with patch.object(evaluation.SetupRuntime, "from_launch_image", return_value=runtime):
            with self.assertRaisesRegex(RuntimeError, "Candidate patch did not apply cleanly"):
                evaluation.evaluate_instance(
                    "example__project-1",
                    "example-image",
                    "rebuild-command",
                    "run-tests",
                    "collect-log",
                    "test-patch",
                    "candidate-patch",
                    "custom",
                    "linux",
                    tempfile.gettempdir(),
                )
        self.assertEqual(
            runtime.patches,
            [("test-patch", True), ("candidate-patch", True)],
        )
        self.assertEqual(runtime.commands, [])
        self.assertTrue(runtime.cleaned_up)

    def test_unmatched_parser_output_is_an_evaluator_contract_error(self):
        instance = {
            "instance_id": "example__project-1",
            "docker_image": "example-image",
            "rebuild_cmds": [],
            "test_cmds": [],
            "print_cmds": [],
            "test_patch": "test-patch",
            "pred_patch": "candidate-patch",
            "log_parser": "custom",
            "PASS_TO_PASS": ["expected::stable"],
            "FAIL_TO_PASS": ["expected::fixed"],
        }
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(evaluation, "evaluate_instance", return_value={"unrelated::test": "pass"}):
                with self.assertRaisesRegex(evaluation.EvaluationContractError, "matched none"):
                    evaluation.run_instance(instance, "linux", output_dir, True)

            report = __import__("json").loads(
                (Path(output_dir) / instance["instance_id"] / "report.json").read_text(encoding="utf-8")
            )
        self.assertFalse(report["resolved"])
        self.assertFalse(report["evaluation_contract"]["valid"])
        self.assertEqual(report["evaluation_contract"]["matched_expected_tests"], 0)

    def test_matching_parser_output_can_be_scored(self):
        instance = {
            "instance_id": "example__project-1",
            "docker_image": "example-image",
            "rebuild_cmds": [],
            "test_cmds": [],
            "print_cmds": [],
            "test_patch": "test-patch",
            "pred_patch": "candidate-patch",
            "log_parser": "custom",
            "PASS_TO_PASS": ["expected::stable"],
            "FAIL_TO_PASS": ["expected::fixed"],
        }
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(
                evaluation,
                "evaluate_instance",
                return_value={"expected::stable": "pass", "expected::fixed": "pass"},
            ):
                report = evaluation.run_instance(instance, "linux", output_dir, True)
        self.assertTrue(report["resolved"])
        self.assertTrue(report["evaluation_contract"]["valid"])
        self.assertEqual(report["evaluation_contract"]["matched_expected_tests"], 2)


if __name__ == "__main__":
    unittest.main()