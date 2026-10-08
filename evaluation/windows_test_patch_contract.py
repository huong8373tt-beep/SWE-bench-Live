"""Preserve the link between Windows Go test patches and expected regressions.

Windows validation publishes exact ``FAIL_TO_PASS`` identities.  When a Go test
patch adds regression functions but none of those roots appears in the published
``FAIL_TO_PASS`` set, the row has no stated target for exact-name evaluation.
That is a dataset-validation problem, not evidence about a candidate patch.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_GO_TEST_FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
_GO_TEST_FUNCTION = re.compile(r"^\+\s*func\s+(Test[A-Za-z0-9_]+)\s*\(")


def added_go_test_functions(test_patch: str) -> list[str]:
    """Return distinct top-level Go test functions added in ``*_test.go`` files.

    Only added diff lines in a test file count.  This avoids treating removed
    tests, context lines, helpers, or non-Go files as regression targets.
    """
    current_path: str | None = None
    result: list[str] = []
    seen: set[str] = set()
    for line in str(test_patch or "").splitlines():
        header = _GO_TEST_FILE_HEADER.match(line)
        if header:
            current_path = header.group(1)
            continue
        if not current_path or not current_path.endswith("_test.go"):
            continue
        if line.startswith("+++"):
            continue
        match = _GO_TEST_FUNCTION.match(line)
        if match:
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                result.append(name)
    return result


def _matches_added_test_root(expected_name: object, roots: Iterable[str]) -> bool:
    """Compare a published package-qualified identity to a Go test root."""
    name = str(expected_name).rsplit("::", 1)[-1]
    return any(name == root or name.startswith(root + "/") for root in roots)


def windows_go_test_patch_contract_is_gradable(
    instance: dict,
    platform: str = "windows",
) -> tuple[bool, list[str]]:
    """Check that a Windows Go test patch has a represented regression target.

    The guard is deliberately narrow:

    * non-Windows rows are unchanged;
    * rows without an added top-level Go test are unchanged;
    * a row is blocked only when *none* of its added test roots is represented
      by a ``FAIL_TO_PASS`` identity or subtest.

    It does not infer a replacement name, alter metadata, or decide whether a
    candidate solved the task.
    """
    if str(platform).lower() != "windows":
        return True, []
    roots = added_go_test_functions(str(instance.get("test_patch", "") or ""))
    if not roots:
        return True, []
    expected = list(instance.get("FAIL_TO_PASS", []) or [])
    if any(_matches_added_test_root(name, roots) for name in expected):
        return True, []
    return False, roots