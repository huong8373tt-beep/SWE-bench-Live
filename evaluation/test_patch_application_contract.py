import tempfile
import types
import unittest

from . import evaluation


class _Result:
    def __init__(self, output="", exit_code=0):
        self.output = output
        self.metadata = types.SimpleNamespace(exit_code=exit_code)


class _Container:
    def __init__(self, patch_results):
        self.patch_results = list(patch_results)
        self.commands = []
        self.cleaned = False

    def apply_patch(self, *_args, **_kwargs):
        return self.patch_results.pop(0)

    def send_command(self, command):
        self.commands.append(command)
        return _Result()

    def cleanup(self):
        self.cleaned = True


class PatchApplicationContractTests(unittest.TestCase):
    def setUp(self):
        self.original_runtime = evaluation.SetupRuntime

    def tearDown(self):
        evaluation.SetupRuntime = self.original_runtime

    def _assert_stops_before_commands(self, patch_results, expected_error):
        container = _Container(patch_results)

        class _Runtime:
            @classmethod
            def from_launch_image(cls, *_args, **_kwargs):
                return container

        evaluation.SetupRuntime = _Runtime
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaisesRegex(RuntimeError, expected_error):
                evaluation.evaluate_instance(
                    instance_id="example__required-patch",
                    image="example-image",
                    rebuild_cmd="rebuild",
                    test_cmd="run-tests",
                    print_cmd="print-results",
                    test_patch="test-patch",
                    solution_patch="solution-patch",
                    parser="pytest",
                    platform="windows",
                    output_dir=output_dir,
                )
        self.assertEqual(container.commands, [])
        self.assertTrue(container.cleaned)

    def test_failed_test_patch_stops_before_candidate_or_commands(self):
        self._assert_stops_before_commands([False], "test patch failed to apply")

    def test_failed_solution_patch_stops_before_commands(self):
        self._assert_stops_before_commands([True, False], "solution patch failed to apply")


if __name__ == "__main__":
    unittest.main()