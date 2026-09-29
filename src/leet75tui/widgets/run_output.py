"""The Output tab: per-case test results and a summary line."""

import json
from typing import Any

from rich.text import Text
from textual.widgets import RichLog

from leet75tui.runner import CaseResult, RunOutcome, RunResult

MAX_VALUE_CHARS = 300
PASS_STYLE = "bold green"
FAIL_STYLE = "bold red"
WARN_STYLE = "bold yellow"
DETAIL_INDENT = "    "
# Outcomes whose runner message (compile error, missing interpreter) adds to the summary.
MESSAGE_OUTCOMES = frozenset({RunOutcome.ERROR, RunOutcome.UNAVAILABLE})


def format_value(value: Any) -> str:
    """Compact JSON for a case value, truncated for display."""
    try:
        text = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) > MAX_VALUE_CHARS:
        return text[:MAX_VALUE_CHARS] + "…"
    return text


def case_lines(case: CaseResult) -> list[Text]:
    """Status line for ``case`` plus args/expected/actual/error/stdout on failure."""
    glyph, style = ("✔", PASS_STYLE) if case.passed else ("✘", FAIL_STYLE)
    lines = [Text.assemble((f"{glyph} {case.name}", style), (f"  {case.ms:.1f} ms", "dim"))]
    if not case.passed:
        lines += _detail("args", format_value(case.args))
        lines += _detail("expected", format_value(case.expected))
        if case.error is None:
            lines += _detail("actual", format_value(case.actual))
    if case.error:
        lines += _detail("error", case.error)
    if case.stdout:
        lines += _detail("stdout", case.stdout.rstrip("\n"))
    return lines


def summary_line(result: RunResult, timeout_s: float) -> Text:
    """One line describing how the run ended."""
    total = len(result.cases)
    passed = result.passed_count
    match result.outcome:
        case RunOutcome.PASSED:
            return Text(f"✔ {passed}/{total} passed in {result.duration_ms:.0f} ms", PASS_STYLE)
        case RunOutcome.FAILED:
            return Text(f"✘ {passed}/{total} passed", FAIL_STYLE)
        case RunOutcome.TIMED_OUT:
            return Text(f"✘ timed out after {timeout_s:.1f} s", FAIL_STYLE)
        case RunOutcome.ERROR:
            return Text("✘ could not run the solution", FAIL_STYLE)
        case RunOutcome.UNAVAILABLE:
            return Text("! runner unavailable", WARN_STYLE)


def _detail(label: str, value: str) -> list[Text]:
    first, *rest = value.splitlines() or [""]
    lines = [Text.assemble((f"{DETAIL_INDENT}{label:<9}", "dim"), first)]
    padding = DETAIL_INDENT + " " * 9
    lines += [Text(padding + line) for line in rest]
    return lines


class RunOutput(RichLog):
    """Scrolling log of test results; every update replaces the whole log."""

    def show_running(self) -> None:
        """Replace the log with a progress note."""
        self._replace([Text("Running…", "dim")])

    def show_message(self, message: str, style: str = WARN_STYLE) -> None:
        """Replace the log with a single message."""
        self._replace([Text(message, style)])

    def show_result(self, result: RunResult, timeout_s: float) -> None:
        """Replace the log with the per-case lines, the summary and the runner message."""
        lines = [line for case in result.cases for line in case_lines(case)]
        lines.append(summary_line(result, timeout_s))
        if result.message and result.outcome in MESSAGE_OUTCOMES:
            lines.append(Text(result.message))
        self._replace(lines)

    def _replace(self, lines: list[Text]) -> None:
        # RichLog wraps at write time, and a tab activated in this tick has no width yet.
        self.call_after_refresh(self._write_lines, lines)

    def _write_lines(self, lines: list[Text]) -> None:
        self.clear()
        for line in lines:
            self.write(line)
