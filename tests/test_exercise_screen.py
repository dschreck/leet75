"""Exercise screen via Pilot: opening, footer, autosave, tabs, language toggle, leaving."""

from pathlib import Path

import pytest
from conftest import FakeRunner
from pilot_helpers import (
    DEPTH,
    MERGE,
    SIZE,
    active_tab,
    editor,
    make_app,
    open_problem,
    press_raw,
    record_notifications,
    run_and_wait,
    solution,
    starter,
)
from textual.widgets import Markdown
from textual.widgets._footer import FooterKey

from leet75tui.app import Leet75App
from leet75tui.languages import Language
from leet75tui.screens.catalog_screen import CatalogScreen, ProblemTable
from leet75tui.screens.exercise_screen import ExerciseScreen

AUTOSAVE_WAIT_S = 0.8  # AUTOSAVE_DELAY_S plus margin


def statement(app: Leet75App) -> str:
    return app.screen.query_one("#statement", Markdown).source


async def test_opening_loads_starter_without_creating_files(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        screen = await open_problem(app, DEPTH)
        await pilot.pause(AUTOSAVE_WAIT_S)

        assert editor(app).text == starter(app_repo, DEPTH, Language.TYPESCRIPT)
        assert screen.title == "104. Maximum Depth of Binary Tree — [TS]"
        assert (editor(app).language, editor(app).indent_width) == ("typescript", 2)
        assert editor(app).has_focus
        assert active_tab(app) == "problem"
        assert statement(app).startswith("# 104. Maximum Depth of Binary Tree")
        assert not solution(app_repo, DEPTH, Language.TYPESCRIPT).exists()


async def test_opening_prefers_workbook_file(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE):
        await open_problem(app, MERGE)

        assert "let merged" in editor(app).text


async def test_opening_uses_most_recent_language(app_repo: Path, fake_runner: FakeRunner) -> None:
    solution(app_repo, DEPTH, Language.PYTHON).write_text("# mine\n", encoding="utf-8")
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE):
        screen = await open_problem(app, DEPTH)

        assert editor(app).text == "# mine\n"
        assert screen.title.endswith("— [PY]")
        assert (editor(app).language, editor(app).indent_width) == ("python", 4)


async def test_missing_statement_is_reported(app_repo: Path, fake_runner: FakeRunner) -> None:
    (app_repo / "problems" / DEPTH / "problem.md").unlink()
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.pause()

        assert statement(app).startswith("*Cannot read")


async def test_footer_hints(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.pause()

        hints = [(key.key_display, key.description) for key in app.screen.query(FooterKey)]
        assert hints == [
            ("^⏎/F5", "run"),
            ("F2/F3", "tabs"),
            ("^t", "lang"),
            ("^⇧O/F4", "$EDITOR"),
            ("esc", "back"),
        ]


async def test_edits_autosave_after_debounce(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    path = solution(app_repo, DEPTH, Language.TYPESCRIPT)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("x")
        assert not path.exists()

        await pilot.pause(AUTOSAVE_WAIT_S)
        assert path.read_text(encoding="utf-8") == editor(app).text
        assert editor(app).text.startswith("x")


async def test_f2_f3_switch_tabs(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("f3")
        assert active_tab(app) == "output"
        await pilot.press("f2")
        assert active_tab(app) == "problem"

        await press_raw(pilot, "\x1bOR")  # F3 as the terminal sends it
        assert active_tab(app) == "output"
        await press_raw(pilot, "\x1bOQ")  # F2
        assert active_tab(app) == "problem"
        assert editor(app).has_focus


async def test_ctrl_t_toggles_language(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        screen = await open_problem(app, DEPTH)

        await pilot.press("ctrl+t")
        assert editor(app).text == starter(app_repo, DEPTH, Language.PYTHON)
        assert screen.title == "104. Maximum Depth of Binary Tree — [PY]"
        assert (editor(app).language, editor(app).indent_width) == ("python", 4)

        await press_raw(pilot, "\x14")  # ctrl+t as the terminal sends it
        assert editor(app).text == starter(app_repo, DEPTH, Language.TYPESCRIPT)
        assert screen.title.endswith("— [TS]")
        assert not solution(app_repo, DEPTH, Language.PYTHON).exists()
        assert not solution(app_repo, DEPTH, Language.TYPESCRIPT).exists()


async def test_toggle_saves_unsaved_edits_first(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("x", "ctrl+t")
        assert solution(app_repo, DEPTH, Language.TYPESCRIPT).read_text().startswith("x")

        await pilot.press("ctrl+t")
        assert editor(app).text.startswith("x")


async def test_escape_saves_and_refreshes_catalog(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("down", "down", "enter")
        assert isinstance(app.screen, ExerciseScreen)
        await run_and_wait(pilot, "x", "f5")
        await pilot.press("y", "escape")
        await pilot.pause()

        assert isinstance(app.screen, CatalogScreen)
        table = app.screen.query_one(ProblemTable)
        assert str(table.get_cell(DEPTH, "status")) == "✓"
        assert "2/3 solved" in str(app.screen.query_one("#solved").render())
        saved = solution(app_repo, DEPTH, Language.TYPESCRIPT).read_text(encoding="utf-8")
        assert saved.startswith("xy")  # "y" was typed after the run and saved by escape


async def test_quitting_saves_pending_edits(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.press("z", "ctrl+q")

    assert solution(app_repo, DEPTH, Language.TYPESCRIPT).read_text().startswith("z")


def fail_to_save(self: object, slug: str, language: Language, source: str) -> Path:
    raise PermissionError(13, "Permission denied", slug)


async def test_failed_save_keeps_edits_on_screen(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("leet75tui.workbook.Workbook.save", fail_to_save)
    app = make_app(app_repo, fake_runner)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        screen = await open_problem(app, DEPTH)
        await pilot.press("x")

        await pilot.press("ctrl+t", "f4", "escape")

        assert app.screen is screen
        assert screen.title.endswith("— [TS]")
        assert editor(app).text.startswith("x")
        assert notes == [f"Save failed: [Errno 13] Permission denied: {DEPTH!r}"] * 3
        monkeypatch.undo()  # let the unmount-time save succeed


async def test_missing_starter_opens_empty_editor(
    app_repo: Path, fake_runner: FakeRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    (app_repo / "problems" / DEPTH / "starter.py").unlink()
    app = make_app(app_repo, fake_runner)
    notes = record_notifications(app, monkeypatch)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)

        await pilot.press("ctrl+t")

        assert editor(app).text == ""
        assert len(notes) == 1
        assert notes[0].startswith("Cannot load PY code: [Errno 2] No such file or directory")
