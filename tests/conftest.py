"""Shared fixtures for the app tests: a throwaway fixture repo and a scripted fake runner."""

import asyncio
import shutil
from pathlib import Path

import pytest

from leet75tui.languages import Language
from leet75tui.runner import RunOutcome, RunResult

APP_FIXTURE = Path(__file__).parent / "fixtures" / "app"


class FakeRunner:
    """Stands in for ``run_solution``: records calls, returns ``result``.

    Set ``gate`` to an unset ``asyncio.Event`` to hold runs in flight until it is set;
    ``cancelled`` counts runs cancelled while waiting.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[Path, Language, str]] = []
        self.result = RunResult(RunOutcome.PASSED, (), "", 1.0)
        self.gate: asyncio.Event | None = None
        self.cancelled = 0

    async def __call__(self, problem_dir: Path, language: Language, source: str) -> RunResult:
        self.calls.append((problem_dir, language, source))
        if self.gate is not None:
            try:
                await self.gate.wait()
            except asyncio.CancelledError:
                self.cancelled += 1
                raise
        return self.result


@pytest.fixture
def app_repo(tmp_path: Path) -> Path:
    """Writable copy of tests/fixtures/app: 1768 (SOLVED, TS workbook file), 933 (pending), 104."""
    root = tmp_path / "repo"
    shutil.copytree(APP_FIXTURE, root)
    return root


@pytest.fixture
def fake_runner() -> FakeRunner:
    """A fresh FakeRunner whose default result passes."""
    return FakeRunner()
