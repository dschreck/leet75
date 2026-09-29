"""Turn the harness's results.jsonl records and the child's exit into a run outcome."""

import json
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from leet75tui.runner.compare import matches
from leet75tui.runner.models import CaseResult, RunOutcome
from leet75tui.runner.problem import Case, Problem

RESULTS_READ_CAP = 32 * 1024 * 1024
CRASH_EXCERPT_CHARS = 2000


@dataclass(frozen=True, slots=True)
class ChildExit:
    """How the child ended; `timeout_s` is the timeout that fired, None if it exited."""

    returncode: int | None
    timeout_s: float | None
    output: str  # tail of the raw stdout+stderr, run-dir paths removed


@dataclass(slots=True)
class Records:
    """The well-formed records of one run: first record per case, fatal error, done flag."""

    cases: dict[int, dict[str, Any]] = field(default_factory=dict)
    fatal: str | None = None
    done: bool = False


def read_records(path: Path, case_count: int) -> Records:
    """Parse results.jsonl, skipping anything malformed or out of range."""
    records = Records()
    try:
        with path.open("rb") as file:
            data = file.read(RESULTS_READ_CAP)
    except FileNotFoundError:
        return records
    # The last piece is empty, or a record whose write a kill cut short.
    for line in data.split(b"\n")[:-1]:
        _add_record(records, line, case_count)
    return records


def summarize(
    problem: Problem, records: Records, child: ChildExit
) -> tuple[RunOutcome, str, tuple[CaseResult, ...]]:
    """Outcome, message and finished cases; PASSED needs every case to have passed."""
    if records.fatal is not None:
        return RunOutcome.ERROR, records.fatal, ()
    cases = tuple(
        _case_result(index, problem.cases[index], records.cases[index])
        for index in sorted(records.cases)
    )
    total = len(problem.cases)
    if records.done and len(cases) == total:
        passed = sum(case.passed for case in cases)
        outcome = RunOutcome.PASSED if total and passed == total else RunOutcome.FAILED
        return outcome, f"{passed}/{total} cases passed", cases
    if child.timeout_s is not None:
        return RunOutcome.TIMED_OUT, f"timed out after {child.timeout_s:.1f} s", cases
    return RunOutcome.ERROR, _crash_message(child, len(cases), total), cases


def _add_record(records: Records, line: bytes, case_count: int) -> None:
    try:
        record = json.loads(line)
    except ValueError:
        return
    if not isinstance(record, dict):
        return
    kind, index = record.get("type"), record.get("index")
    if kind == "case" and isinstance(index, int) and 0 <= index < case_count:
        records.cases.setdefault(index, record)
    elif kind == "fatal":
        records.fatal = str(record.get("error"))
    elif kind == "done":
        records.done = True


def _case_result(index: int, case: Case, record: dict[str, Any]) -> CaseResult:
    error = record.get("error")
    error = error if isinstance(error, str) else None
    actual = record.get("actual") if error is None else None
    stdout = record.get("stdout")
    ms = record.get("ms")
    return CaseResult(
        index=index,
        name=case.name,
        passed=error is None and matches(actual, case.expected, case.compare),
        args=case.shown_args,
        expected=case.expected,
        actual=actual,
        error=error,
        stdout=stdout if isinstance(stdout, str) else "",
        ms=float(ms) if isinstance(ms, (int, float)) else 0.0,
    )


def _crash_message(child: ChildExit, finished: int, total: int) -> str:
    code = child.returncode  # set: this path is only reached after the child exited
    if code is not None and code < 0:
        how = f"was killed by {_signal_name(-code)}"
    else:
        how = f"exited with code {code}"
    message = f"The solution process {how} after {finished} of {total} cases"
    excerpt = child.output.strip()[-CRASH_EXCERPT_CHARS:]
    return f"{message}:\n{excerpt}" if excerpt else message


def _signal_name(number: int) -> str:
    try:
        return signal.Signals(number).name
    except ValueError:
        return f"signal {number}"
