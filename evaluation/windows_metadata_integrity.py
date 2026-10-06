"""Detect published Windows expected-test metadata that cannot be graded exactly."""

from __future__ import annotations

import re
from collections.abc import Iterable

# A canonical Go test name does not contain captured JSON syntax, a go-test
# duration suffix, or a parser-spliced package/test separator. Those fragments
# originate from wrapped or permissively parsed Go JSON output.
_GO_JSON_FRAGMENT = re.compile(r'(?:\r?\n|\\n)"\}\s*$')
_GO_DURATION_FRAGMENT = re.compile(r"\s\(\d+(?:\.\d+)?s\)\s*$")
_PACKAGE_TEST_SEPARATOR_FRAGMENT = re.compile(r"/:\s*Test")


def invalid_windows_expected_tests(names: Iterable[object]) -> list[str]:
    """Return expected-test values that cannot be exact parsed test identifiers."""
    invalid: list[str] = []
    for value in names:
        name = str(value)
        if (
            _GO_JSON_FRAGMENT.search(name)
            or _GO_DURATION_FRAGMENT.search(name)
            or _PACKAGE_TEST_SEPARATOR_FRAGMENT.search(name)
        ):
            invalid.append(name)
    return invalid


def windows_metadata_is_gradable(
    instance: dict,
    platform: str = "windows",
) -> tuple[bool, list[str]]:
    """Check whether a Windows row can safely use exact expected-test grading.

    Existing dataset rows are immutable evaluation inputs. A malformed expected
    identifier must produce an unavailable verdict, never a candidate failure
    and never a guessed correction.
    """
    if platform.lower() != "windows":
        return True, []
    expected = list(instance.get("PASS_TO_PASS", []) or []) + list(instance.get("FAIL_TO_PASS", []) or [])
    invalid = invalid_windows_expected_tests(expected)
    return not invalid, invalid