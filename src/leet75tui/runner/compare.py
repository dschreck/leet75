"""Compare a solution's serialized output with a case's expected value."""

import json
from collections import Counter
from enum import StrEnum
from typing import Any

FLOAT_TOLERANCE = 1e-5


class CompareMode(StrEnum):
    """How `actual` must relate to `expected` for a case to pass.

    - exact: deep JSON equality; 1 == 1.0, but true != 1
    - unordered: lists equal as multisets
    - unordered-inner: list of lists, each inner list a multiset; outer order matters
    - unordered-nested: inner lists and the outer list are all multisets
    - float: numbers, or nested lists of numbers, within FLOAT_TOLERANCE
    - one-of: `expected` lists the acceptable answers; `actual` exactly equals one
    """

    EXACT = "exact"
    UNORDERED = "unordered"
    UNORDERED_INNER = "unordered-inner"
    UNORDERED_NESTED = "unordered-nested"
    FLOAT = "float"
    ONE_OF = "one-of"


def matches(actual: Any, expected: Any, mode: CompareMode) -> bool:
    """True when `actual` satisfies `expected` under `mode`; never raises on odd shapes."""
    match mode:
        case CompareMode.EXACT:
            return _canonical(actual) == _canonical(expected)
        case CompareMode.UNORDERED:
            return _both_lists(actual, expected) and _same_multiset(actual, expected)
        case CompareMode.UNORDERED_INNER:
            return _unordered_inner(actual, expected)
        case CompareMode.UNORDERED_NESTED:
            return _unordered_nested(actual, expected)
        case CompareMode.FLOAT:
            return _close(actual, expected)
        case CompareMode.ONE_OF:
            return isinstance(expected, list) and any(
                _canonical(actual) == _canonical(option) for option in expected
            )


def _normalize(value: Any) -> Any:
    """Make equal JSON values identical: integral floats become ints; bools stay bools."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _canonical(value: Any) -> str:
    return json.dumps(_normalize(value), sort_keys=True)


def _both_lists(actual: Any, expected: Any) -> bool:
    return isinstance(actual, list) and isinstance(expected, list)


def _same_multiset(actual: list[Any], expected: list[Any]) -> bool:
    return Counter(map(_canonical, actual)) == Counter(map(_canonical, expected))


def _unordered_inner(actual: Any, expected: Any) -> bool:
    if not _both_lists(actual, expected) or len(actual) != len(expected):
        return False
    return all(
        _both_lists(got, want) and _same_multiset(got, want)
        for got, want in zip(actual, expected, strict=True)
    )


def _unordered_nested(actual: Any, expected: Any) -> bool:
    if not _both_lists(actual, expected):
        return False
    if not all(isinstance(inner, list) for inner in (*actual, *expected)):
        return False
    return _inner_multisets(actual) == _inner_multisets(expected)


def _inner_multisets(lists: list[list[Any]]) -> Counter[str]:
    return Counter(json.dumps(sorted(map(_canonical, inner))) for inner in lists)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _close(actual: Any, expected: Any) -> bool:
    if _is_number(actual) and _is_number(expected):
        return bool(abs(actual - expected) <= FLOAT_TOLERANCE)
    if _both_lists(actual, expected):
        return len(actual) == len(expected) and all(
            _close(got, want) for got, want in zip(actual, expected, strict=True)
        )
    return _canonical(actual) == _canonical(expected)
