"""Running tests from the exercise screen: run keys, Output rendering, progress."""

import asyncio
import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest
from conftest import FakeRunner
from pilot_helpers import (
    DEPTH,
    NODE,
    RECENT,
    SIZE,
    active_tab,
    editor,
    make_app,
    open_problem,
    output_text,
    output_words,
    press_raw,
    record_notifications,
    run_and_wait,
    solution,
    starter,
)

from leet75tui.app import Leet75App
from leet75tui.languages import Language
from leet75tui.runner import CaseResult, RunOutcome, RunResult
from leet75tui.screens.exercise_screen import CASES_PENDING, NODE_MISSING
from leet75tui.widgets.run_output import RunOutput, format_value


def case(index: int, *, passed: bool = True, **changes: Any) -> CaseResult:
    """A result for case ``index``; failing cases get a wrong ``actual`` unless changed."""
    result = CaseResult(
        index=index,
        name=f"case {index + 1}",
        passed=passed,
        args=["abc", "pqr"],
        expected="apbqcr",
        actual="apbqcr" if passed else "apbq",
        error=None,
        stdout="",
        ms=1.5,
    )
    return dataclasses.replace(result, **changes)


@pytest.mark.parametrize("key", ["ctrl+j", "f5", "ctrl+r", "ctrl+enter"])
async def test_run_keys_run_tests_in_output_tab(
    app_repo: Path, fake_runner: FakeRunner, key: str
) -> None:
    fake_runner.result = RunResult(RunOutcome.PASSED, (case(0), case(1)), "", 3.2)
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        source = editor(app).text

        await run_and_wait(pilot, key)

        assert fake_runner.calls == [(app_repo / "problems" / DEPTH, Language.TYPESCRIPT, source)]
        assert active_tab(app) == "output"
        assert output_text(app).splitlines() == [
            "✔ case 1  1.5 ms",
            "✔ case 2  1.5 ms",
            "✔ 2/2 passed in 3 ms",
        ]


@pytest.mark.parametrize(
    ("data", "label"),
    [("\n", "Ctrl+Enter in Windows Terminal"), ("\x1b[15~", "F5"), ("\x12", "Ctrl+R")],
)
async def test_run_keys_from_terminal_bytes(
    app_repo: Path, fake_runner: FakeRunner, data: str, label: str
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        before = editor(app).text

        await press_raw(pilot, data)
        await app.workers.wait_for_complete()

        assert len(fake_runner.calls) == 1, label
        assert editor(app).text == before  # ctrl+j must not insert a newline


async def test_failure_details_are_rendered(app_repo: Path, fake_runner: FakeRunner) -> None:
    failed = case(1, passed=False, stdout="debug 1\ndebug 2\n")
    crashed = case(2, passed=False, actual=None, error="TypeError: boom")
    fake_runner.result = RunResult(RunOutcome.FAILED, (case(0), failed, crashed), "", 5.0)
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        assert output_text(app).splitlines() == [
            "✔ case 1  1.5 ms",
            "✘ case 2  1.5 ms",
            '    args     ["abc", "pqr"]',
            '    expected "apbqcr"',
            '    actual   "apbq"',
            "    stdout   debug 1",
            "             debug 2",
            "✘ case 3  1.5 ms",
            '    args     ["abc", "pqr"]',
            '    expected "apbqcr"',
            "    error    TypeError: boom",
            "✘ 1/3 passed",
        ]


@pytest.mark.parametrize(
    ("outcome", "message", "expected"),
    [
        (RunOutcome.TIMED_OUT, "timed out after 5.0 s", ["✘ timed out after 5.0 s"]),
        (
            RunOutcome.ERROR,
            "SyntaxError: Unexpected token '}'",
            ["✘ could not run the solution", "SyntaxError: Unexpected token '}'"],
        ),
        (RunOutcome.UNAVAILABLE, "no python3", ["! runner unavailable", "no python3"]),
    ],
)
async def test_unfinished_runs_are_rendered(
    app_repo: Path,
    fake_runner: FakeRunner,
    outcome: RunOutcome,
    message: str,
    expected: list[str],
) -> None:
    fake_runner.result = RunResult(outcome, (), message, 5000.0)
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        assert output_text(app).splitlines() == expected


async def test_result_returns_to_output_tab_and_wraps_to_it(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    failed = case(0, passed=False, actual=None, error="ValueError: " + "x" * 300)
    fake_runner.result = RunResult(RunOutcome.FAILED, (failed,), "", 1.0)
    fake_runner.gate = asyncio.Event()
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.press("f5", "f2")
        assert active_tab(app) == "problem"

        fake_runner.gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert active_tab(app) == "output"
        log = app.screen.query_one(RunOutput)
        assert max(line.cell_length for line in log.lines) <= log.scrollable_content_region.width
        assert "x" * 300 in output_text(app).replace("\n", "").replace(" ", "")


async def test_editor_stays_responsive_and_new_run_cancels_old(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    fake_runner.gate = asyncio.Event()
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.press("ctrl+j")
        await pilot.pause()
        assert output_text(app) == "Running…"

        await pilot.press("x", "y")
        assert editor(app).text.startswith("xy")

        await pilot.press("f5")
        await pilot.pause()
        fake_runner.gate.set()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert len(fake_runner.calls) == 2
        assert fake_runner.cancelled == 1
        assert fake_runner.calls[1][2].startswith("xy")
        assert output_text(app) == "✔ 0/0 passed in 1 ms"


async def test_run_creates_workbook_file(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        path = solution(app_repo, DEPTH, Language.TYPESCRIPT)
        assert path.read_text(encoding="utf-8") == starter(app_repo, DEPTH, Language.TYPESCRIPT)


async def test_progress_is_recorded_and_solved_is_sticky(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    progress_path = app_repo / "workbook" / "progress.json"
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        statuses = []
        for outcome in (RunOutcome.FAILED, RunOutcome.PASSED, RunOutcome.FAILED):
            fake_runner.result = RunResult(outcome, (), "", 1.0)
            await run_and_wait(pilot, "f5")
            entry = json.loads(progress_path.read_text(encoding="utf-8"))["problems"][DEPTH]
            statuses.append(entry["status"])

        assert statuses == ["ATTEMPTED", "SOLVED", "SOLVED"]
        assert entry["lastRunAt"].endswith("+00:00")


async def test_unavailable_runner_is_not_an_attempt(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    fake_runner.result = RunResult(RunOutcome.UNAVAILABLE, (), "no python3", 0.0)
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        assert DEPTH not in (app_repo / "workbook" / "progress.json").read_text(encoding="utf-8")


async def test_failed_progress_write_is_reported(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_to_record(self: object, slug: str, *, all_passed: bool) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("leet75tui.progress.ProgressStore.record_run", fail_to_record)
    app = make_app(app_repo, fake_runner)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        assert notes == ["Cannot save progress: disk full"]


async def test_missing_node_blocks_typescript_but_not_python(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner, node=None)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")
        assert output_words(app) == NODE_MISSING
        assert fake_runner.calls == []

        await run_and_wait(pilot, "ctrl+t", "f5")
        assert [call[1] for call in fake_runner.calls] == [Language.PYTHON]


async def test_pending_cases_do_not_run(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, RECENT)

        await run_and_wait(pilot, "f5")

        assert output_words(app) == CASES_PENDING
        assert fake_runner.calls == []
        assert solution(app_repo, RECENT, Language.TYPESCRIPT).exists()


async def test_runner_crash_is_reported(app_repo: Path) -> None:
    async def broken_runner(problem_dir: Path, language: Language, source: str) -> RunResult:
        raise RuntimeError("harness bug")

    app = Leet75App(app_repo, app_repo / "workbook", runner=broken_runner, node_finder=lambda: NODE)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await run_and_wait(pilot, "f5")

        assert output_words(app) == "Runner crashed: RuntimeError('harness bug')"


def test_format_value_handles_non_json_and_long_values() -> None:
    assert format_value({"a": [1, None]}) == '{"a": [1, null]}'
    assert format_value({1, 2}) == "{1, 2}"
    long_value = format_value("x" * 1000)
    assert len(long_value) == 301
    assert long_value.endswith("…")
