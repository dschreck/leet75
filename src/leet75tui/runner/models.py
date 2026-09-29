"""Result types produced by the solution runner."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RunOutcome(StrEnum):
    """How a run ended."""

    PASSED = "PASSED"  # every case passed
    FAILED = "FAILED"  # ran to completion; at least one case failed or raised
    TIMED_OUT = "TIMED_OUT"  # killed at the timeout; `cases` holds the cases finished before the kill
    ERROR = "ERROR"  # could not run: syntax/import error, missing entry, no cases, harness crash
    UNAVAILABLE = "UNAVAILABLE"  # interpreter missing (e.g. no Node >= 23.6); `message` says why


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Outcome of a single test case."""

    index: int  # 0-based position in cases.json
    name: str  # cases.json "name", else f"case {index + 1}"
    passed: bool
    args: Any  # JSON value as given in cases.json (design: {"ops": [...], "args": [...]})
    expected: Any
    actual: Any  # serialized return/output; None when the call raised
    error: str | None  # exception type + message (+ short user-code traceback) when the call raised
    stdout: str  # what the solution printed during this case (capped)
    ms: float  # wall time of the call


@dataclass(frozen=True, slots=True)
class RunResult:
    """Outcome of running one solution against a problem's cases."""

    outcome: RunOutcome
    cases: tuple[CaseResult, ...]
    message: str  # human-readable summary or error text
    duration_ms: float

    @property
    def passed_count(self) -> int:
        """Number of passing cases."""
        return sum(1 for case in self.cases if case.passed)

    @property
    def all_passed(self) -> bool:
        """True when the run passed every case."""
        return self.outcome is RunOutcome.PASSED
