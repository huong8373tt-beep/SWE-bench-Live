import tempfile
import types
import unittest

from . import evaluation


class _Result:
    def __init__(self, output: str = "", exit_code: int = 0):
        self.output = output
        self.metadata = types.SimpleNamespace(exit_code=exit_code)


class _Container:
    def __init__(self, exit_code: int):
        self.exit_code = exit_code
        self.cleaned = False
        self.commands: list[str] = []

    def apply_patch(self, *_args, **_kwargs):
        return True

    def send_command(self, command: str):
        self.commands.append(command)
        if command == "run-tests":
            return _Result(exit_code=self.exit_code)
        if command == "print-results":
            return _Result("partial test output")
        return _Result()

    def cleanup(self):
        self.cleaned = True


class EvaluationCommandStatusTests(unittest.TestCase):
    def setUp(self):
        self.containers: list[_Container] = []
        self.original_runtime = evaluation.SetupRuntime
        self.original_parser = evaluation.run_parser

        containers = self.containers

        class _Runtime:
            @classmethod
            def from_launch_image(cls, *_args, **_kwargs):
                container = _Container(exit_code=1)
                containers.append(container)
                return container

        evaluation.SetupRuntime = _Runtime
        evaluation.run_parser = lambda *_args: {
            "TestPartial": "pass",
            "TestSkipped": "skip",
        }

    def tearDown(self):
        evaluation.SetupRuntime = self.original_runtime
        evaluation.run_parser = self.original_parser

    def test_evaluation_demotes_partial_passes_after_failed_test_command(self):
        with tempfile.TemporaryDirectory() as output_dir:
            result = evaluation.evaluate_instance(
                instance_id="example__partial-command",
                image="example-image",
                rebuild_cmd="rebuild",
                test_cmd="run-tests",
                print_cmd="print-results",
                test_patch="",
                solution_patch="",
                parser="example",
                platform="windows",
                output_dir=output_dir,
            )

        self.assertEqual(
            result,
            {
                "TestPartial": "fail",
                "TestSkipped": "skip",
            },
        )
        self.assertEqual(len(self.containers), 1)
        self.assertTrue(self.containers[0].cleaned)

    def test_evaluation_keeps_statuses_when_test_command_succeeds(self):
        status = {"TestPassing": "pass", "TestSkipped": "skip"}
        self.assertEqual(
            evaluation._demote_passes_after_failed_test_command(status, 0),
            status,
        )


if __name__ == "__main__":
    unittest.main()