"""The $EDITOR escape hatch (ctrl+o / F4): suspend, run the editor, reload the buffer."""

import contextlib
import subprocess
from pathlib import Path

import pytest
from conftest import FakeRunner
from pilot_helpers import (
    DEPTH,
    SIZE,
    editor,
    make_app,
    open_problem,
    press_raw,
    record_notifications,
    solution,
)

from leet75tui.languages import Language
from leet75tui.screens.exercise_screen import ExerciseScreen


class EditorCall:
    """Replaces ``subprocess.run``: records argv and rewrites the file like an editor."""

    def __init__(self, new_text: str) -> None:
        self.new_text = new_text
        self.commands: list[list[str]] = []
        self.existed: list[bool] = []

    def __call__(self, command: list[str], check: bool) -> None:
        path = Path(command[-1])
        self.commands.append(command)
        self.existed.append(path.exists())
        path.write_text(self.new_text, encoding="utf-8")


@pytest.mark.parametrize("key", ["ctrl+o", "f4"])
async def test_open_in_editor_suspends_and_reloads(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    call = EditorCall("// edited outside\n")
    monkeypatch.setenv("VISUAL", "")
    monkeypatch.setenv("EDITOR", "nvim --clean")
    monkeypatch.setattr(subprocess, "run", call)
    app = make_app(app_repo, fake_runner)
    suspended: list[bool] = []
    monkeypatch.setattr(app, "suspend", lambda: contextlib.nullcontext(suspended.append(True)))
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press(key)

        path = solution(app_repo, DEPTH, Language.TYPESCRIPT)
        assert suspended == [True]
        assert call.commands == [["nvim", "--clean", str(path)]]
        assert call.existed == [True]
        assert editor(app).text == "// edited outside\n"
        assert path.read_text(encoding="utf-8") == "// edited outside\n"


@pytest.mark.parametrize(
    ("data", "label"), [("\x0f", "Ctrl+Shift+O in Windows Terminal"), ("\x1bOS", "F4")]
)
async def test_editor_keys_from_terminal_bytes(
    app_repo: Path,
    fake_runner: FakeRunner,
    monkeypatch: pytest.MonkeyPatch,
    data: str,
    label: str,
) -> None:
    call = EditorCall("# py\n")
    monkeypatch.setenv("VISUAL", "code --wait")
    monkeypatch.setattr(subprocess, "run", call)
    app = make_app(app_repo, fake_runner)
    monkeypatch.setattr(app, "suspend", contextlib.nullcontext)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await press_raw(pilot, data)

        assert [command[:2] for command in call.commands] == [["code", "--wait"]], label


async def test_editor_failure_is_reported(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_editor(command: list[str], check: bool) -> None:
        raise FileNotFoundError(2, "No such file or directory", command[0])

    monkeypatch.setenv("VISUAL", "")
    monkeypatch.setenv("EDITOR", "")
    monkeypatch.setattr(subprocess, "run", missing_editor)
    app = make_app(app_repo, fake_runner)
    monkeypatch.setattr(app, "suspend", contextlib.nullcontext)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        before = editor(app).text

        await pilot.press("f4")

        assert notes == ["$EDITOR failed: [Errno 2] No such file or directory: 'vi'"]
        assert editor(app).text == before


async def test_reload_failure_after_editor_is_reported(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(subprocess, "run", lambda command, check: Path(command[-1]).unlink())
    app = make_app(app_repo, fake_runner)
    monkeypatch.setattr(app, "suspend", contextlib.nullcontext)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("f4")

        assert len(notes) == 1
        assert notes[0].startswith("Cannot reload")


async def test_headless_suspend_is_reported(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = make_app(app_repo, fake_runner)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("f4")

        assert notes == ["$EDITOR failed: App.suspend is not supported in this environment."]
        assert isinstance(app.screen, ExerciseScreen)
