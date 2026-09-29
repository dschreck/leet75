"""Compare modes used by the runner to decide whether a case passed."""

from typing import Any

import pytest

from leet75tui.runner.compare import FLOAT_TOLERANCE, CompareMode, matches

EXACT = CompareMode.EXACT
UNORDERED = CompareMode.UNORDERED
INNER = CompareMode.UNORDERED_INNER
NESTED = CompareMode.UNORDERED_NESTED
FLOAT = CompareMode.FLOAT
ONE_OF = CompareMode.ONE_OF


@pytest.mark.parametrize(
    ("actual", "expected", "mode", "result"),
    [
        # exact: deep JSON equality, 1 == 1.0 but a bool is never a number
        ("apbqcr", "apbqcr", EXACT, True),
        ("apbqcr", "apbqc", EXACT, False),
        (1, 1.0, EXACT, True),
        ([1, [2.0, 3]], [1.0, [2, 3]], EXACT, True),
        (True, 1, EXACT, False),
        (0, False, EXACT, False),
        (True, True, EXACT, True),
        (None, None, EXACT, True),
        (None, [], EXACT, False),
        ("1", 1, EXACT, False),
        ([1, 2], [2, 1], EXACT, False),
        ({"b": [1], "a": None}, {"a": None, "b": [1.0]}, EXACT, True),
        (0.1 + 0.2, 0.3, EXACT, False),
        # unordered: lists as multisets
        ([3, 1, 2], [1, 2, 3], UNORDERED, True),
        ([1, 1, 2], [1, 2, 2], UNORDERED, False),
        ([1, 2], [1, 2, 2], UNORDERED, False),
        (["ad", "ae"], ["ae", "ad"], UNORDERED, True),
        ([True], [1], UNORDERED, False),
        ("abc", "abc", UNORDERED, False),
        (None, [], UNORDERED, False),
        # unordered-inner: each inner list a multiset, outer order significant
        ([[3, 1], [6, 4]], [[1, 3], [4, 6]], INNER, True),
        ([[4, 6], [1, 3]], [[1, 3], [4, 6]], INNER, False),
        ([[1, 3]], [[1, 3], []], INNER, False),
        ([[1, 3], 4], [[1, 3], [4]], INNER, False),
        # unordered-nested: inner lists and the outer list are multisets
        ([[2, 1, 4], [3, 1, 3]], [[1, 3, 3], [1, 2, 4]], NESTED, True),
        ([[1, 2], [1, 2]], [[1, 2], [2, 1]], NESTED, True),
        ([[1, 2], [1, 2]], [[1, 2], [1, 3]], NESTED, False),
        ([[1, 2]], [[1, 2], [1, 2]], NESTED, False),
        ([1, 2], [[1], [2]], NESTED, False),
        ("12", [[1, 2]], NESTED, False),
        # float: numbers or nested lists of numbers within the tolerance
        (12.75, 12.75000001, FLOAT, True),
        (5, 5.0, FLOAT, True),
        (1.0, 1.0 + 2 * FLOAT_TOLERANCE, FLOAT, False),
        ([6.0, 0.5, -1.0], [6.000001, 0.5, -1], FLOAT, True),
        ([[1.0, 2.0]], [[1.0, 2.1]], FLOAT, False),
        ([1.0], [1.0, 2.0], FLOAT, False),
        (True, 1.0, FLOAT, False),
        ("Infinity", 1.0, FLOAT, False),
        (None, None, FLOAT, True),
        # one-of: expected lists the acceptable answers
        (1, [1, 5], ONE_OF, True),
        (5, [1, 5], ONE_OF, True),
        (2, [1, 5], ONE_OF, False),
        (
            [5, 3, 6, 2, 4, None, 7],
            [[5, 4, 6, 2, None, None, 7], [5, 3, 6, 2, 4, None, 7]],
            ONE_OF,
            True,
        ),
        (1, 1, ONE_OF, False),
    ],
)
def test_matches(actual: Any, expected: Any, mode: CompareMode, result: bool) -> None:
    assert matches(actual, expected, mode) is result


def test_every_mode_parses_from_its_meta_toml_spelling() -> None:
    spellings = [
        "exact",
        "unordered",
        "unordered-inner",
        "unordered-nested",
        "float",
        "one-of",
    ]
    assert [CompareMode(spelling) for spelling in spellings] == list(CompareMode)
