"""Code editor: ctrl+space completion popup and TypeScript highlighting fallback."""

from pathlib import Path

import pytest
from conftest import FakeRunner
from pilot_helpers import (
    DEPTH,
    MERGE,
    SIZE,
    editor,
    make_app,
    open_problem,
    press_raw,
    run_and_wait,
)
from textual.pilot import Pilot

from leet75tui.app import Leet75App
from leet75tui.languages import Language, typescript
from leet75tui.screens.catalog_screen import CatalogScreen
from leet75tui.screens.exercise_screen import ExerciseScreen
from leet75tui.widgets.code_editor import CodeEditor
from leet75tui.widgets.completion import (
    CompletionPopup,
    completion_candidates,
    text_without_word_at,
    word_before,
)


async def type_on_new_last_line(pilot: Pilot[None], *keys: str) -> None:
    text_area = pilot.app.screen.query_one(CodeEditor)
    text_area.move_cursor(text_area.document.end)
    await pilot.press("enter", *keys)


def popup(app: Leet75App) -> CompletionPopup:
    return app.screen.query_one(CompletionPopup)


def options(app: Leet75App) -> list[str | None]:
    return [popup(app).get_option_at_index(i).id for i in range(popup(app).option_count)]


def last_line(app: Leet75App) -> str:
    document = editor(app).document
    return document.get_line(document.line_count - 1)


async def test_ctrl_space_completes_from_buffer_and_entry(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, MERGE)
        await type_on_new_last_line(pilot, "m", "e")

        await pilot.press("ctrl+space")

        assert editor(app).completion_open
        assert options(app) == ["mergeAlternately", "merged"]

        await pilot.press("down", "enter")

        assert not editor(app).completion_open
        assert last_line(app) == "merged"
        assert editor(app).cursor_location[1] == len("merged")


async def test_nul_byte_opens_completion_and_tab_accepts(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "r", "e", "t")

        await press_raw(pilot, "\x00")  # what a terminal sends for Ctrl+Space
        assert editor(app).completion_open

        await pilot.press("tab")
        assert last_line(app) == "return"


async def test_escape_closes_popup_without_leaving(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "c", "o")
        await pilot.press("ctrl+space")
        assert editor(app).completion_open

        await pilot.press("escape")
        assert not editor(app).completion_open
        assert isinstance(app.screen, ExerciseScreen)
        assert last_line(app) == "co"

        await pilot.press("escape")
        assert isinstance(app.screen, CatalogScreen)


async def test_other_keys_close_popup_and_type(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "c", "o")
        await pilot.press("ctrl+space", "down", "up")
        assert popup(app).selected_word == "const"

        await pilot.press("n")

        assert not editor(app).completion_open
        assert last_line(app) == "con"


async def test_python_mode_completes_python_keywords(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await pilot.press("ctrl+t")
        await type_on_new_last_line(pilot, "w", "h")

        await pilot.press("ctrl+space")

        assert popup(app).selected_word == "while"


async def test_popup_reopens_below_the_new_word(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "c", "o", "n")
        await pilot.press("ctrl+space", "enter", "space", "r", "e", "t", "ctrl+space")

        assert editor(app).completion_open
        assert popup(app).selected_word == "return"
        x, y = editor(app).cursor_screen_offset
        border = 1
        assert (popup(app).region.x, popup(app).region.y) == (x - len("ret") - border, y + 1)

        await pilot.press("enter")
        assert last_line(app) == "const return"


async def test_no_candidates_keeps_popup_closed(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "z", "q", "x")

        await pilot.press("ctrl+space")

        assert not editor(app).completion_open


async def test_word_under_cursor_is_not_its_own_candidate(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, *"zebra")

        await pilot.press("left", "left", "left", "ctrl+space")

        assert not editor(app).completion_open  # "zebra" exists only under the cursor


async def test_run_closes_popup(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await open_problem(app, DEPTH)
        await type_on_new_last_line(pilot, "c", "o")
        await pilot.press("ctrl+space")

        await run_and_wait(pilot, "ctrl+j")

        assert not editor(app).completion_open
        assert len(fake_runner.calls) == 1


def test_completion_candidates() -> None:
    text = "const total = 0;\nlet totals = [];\n"

    assert word_before("  tot", 5) == "tot"
    assert word_before("a.b$c", 5) == "b$c"
    assert word_before("x + ", 4) == ""
    typescript_words = completion_candidates("tot", text, Language.TYPESCRIPT, "maxDepth")
    assert typescript_words == ["total", "totals"]
    assert completion_candidates("ma", text, Language.TYPESCRIPT, "maxDepth") == ["maxDepth"]
    assert "lambda" in completion_candidates("la", "", Language.PYTHON, "")
    assert "let" not in completion_candidates("le", "", Language.PYTHON, "")


def test_text_without_word_at_cuts_the_word_around_the_cursor() -> None:
    lines = ["let total = 0;", "sereturn x;"]

    assert text_without_word_at(lines, 1, 2) == "let total = 0;\n x;"
    assert text_without_word_at(lines, 0, 14) == "let total = 0;\nsereturn x;"
    assert text_without_word_at(lines, 0, 0) == " total = 0;\nsereturn x;"


def test_typescript_highlighting_falls_back_to_javascript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(typescript, "JAVASCRIPT_QUERY_PATH", Path("/nonexistent/javascript.scm"))
    typescript._typescript_grammar.cache_clear()  # drop the grammar loaded by earlier tests
    try:
        code_editor = CodeEditor()
        code_editor.set_solution_language(Language.TYPESCRIPT)
        assert code_editor.language == "javascript"
    finally:
        typescript._typescript_grammar.cache_clear()


def test_typescript_highlighting_uses_the_typescript_grammar() -> None:
    code_editor = CodeEditor()

    code_editor.set_solution_language(Language.TYPESCRIPT)
    assert code_editor.language == "typescript"
    assert "typescript" in code_editor.available_languages
    code_editor.set_solution_language(Language.PYTHON)
    assert (code_editor.language, code_editor.indent_width) == ("python", 4)
