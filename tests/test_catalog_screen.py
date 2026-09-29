"""Catalog screen via Pilot: rows, filter, open, quit, footer hints; app entry point."""

from pathlib import Path

import pytest
from conftest import FakeRunner
from pilot_helpers import DEPTH, MERGE, RECENT, SIZE, make_app, press_raw
from textual.widgets import Input, Label
from textual.widgets._footer import FooterKey

from leet75tui.app import Leet75App, main
from leet75tui.screens.catalog_screen import CatalogScreen, ProblemTable
from leet75tui.screens.exercise_screen import ExerciseScreen


def row_slugs(app: Leet75App) -> list[str]:
    table = app.screen.query_one(ProblemTable)
    return [str(row_key.value) for row_key in table.rows]


def cell_text(app: Leet75App, slug: str, column: str) -> str:
    return str(app.screen.query_one(ProblemTable).get_cell(slug, column))


def footer_hints(app: Leet75App) -> dict[str, str]:
    return {
        key: active.binding.description
        for key, active in app.screen.active_bindings.items()
        if active.binding.show
    }


async def test_catalog_lists_problems_in_plan_order(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE):
        assert isinstance(app.screen, CatalogScreen)
        assert row_slugs(app) == [MERGE, RECENT, DEPTH]
        assert cell_text(app, MERGE, "order") == "1"
        assert cell_text(app, MERGE, "problem") == "1768. Merge Strings Alternately"
        assert cell_text(app, MERGE, "difficulty") == "Easy"
        assert cell_text(app, MERGE, "category") == "Array / String"
        assert [cell_text(app, slug, "status") for slug in row_slugs(app)] == ["✓", "·", "·"]
        assert "(tests pending)" in cell_text(app, RECENT, "problem")
        assert str(app.screen.query_one("#solved", Label).content) == "1/3 solved"
        assert app.screen.query_one(ProblemTable).has_focus


async def test_slash_filters_and_escape_restores(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("slash", "t", "r", "e", "e")
        filter_input = app.screen.query_one(Input)
        assert filter_input.has_focus
        assert filter_input.value == "tree"
        assert row_slugs(app) == [DEPTH]

        await pilot.press("escape")

        assert filter_input.value == ""
        assert row_slugs(app) == [MERGE, RECENT, DEPTH]
        assert app.screen.query_one(ProblemTable).has_focus


async def test_filter_matches_category_case_insensitively(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("slash", *"QUEUE")
        assert row_slugs(app) == [RECENT]
        await pilot.press("backspace", "backspace", "backspace", "backspace", "backspace", *"zzz")
        assert row_slugs(app) == []
        await pilot.press("enter")
        assert isinstance(app.screen, CatalogScreen)


async def test_enter_opens_highlighted_problem(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("down", "down", "up", "enter")

        assert isinstance(app.screen, ExerciseScreen)
        assert app.screen.problem.slug == RECENT


async def test_enter_in_filter_opens_first_match(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("slash", *"depth", "enter")

        assert isinstance(app.screen, ExerciseScreen)
        assert app.screen.problem.slug == DEPTH


async def test_arrows_move_rows_while_filtering(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("slash", "down", "down")
        assert app.screen.query_one(Input).has_focus
        assert app.screen.query_one(ProblemTable).cursor_row == 2


async def test_q_quits_from_table(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("q")
    assert app.return_code == 0


async def test_q_and_slash_type_into_filter(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("slash", "q")

        assert app.return_code is None
        assert app.screen.query_one(Input).value == "q"
        assert row_slugs(app) == [RECENT]  # "q" matches the Queue category

        await pilot.press("slash")
        assert app.screen.query_one(Input).value == "q/"


async def test_footer_hints(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.pause()
        rendered = [(key.key_display, key.description) for key in app.screen.query(FooterKey)]
        assert rendered == [("↑↓", "move"), ("/", "filter"), ("⏎", "open"), ("q", "quit")]

        await pilot.press("slash")

        assert footer_hints(app) == {"up": "move", "enter": "open"}


async def test_clicking_highlighted_row_opens_problem(
    app_repo: Path, fake_runner: FakeRunner
) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await pilot.click(ProblemTable, offset=(10, 3))  # header is line 0
        assert isinstance(app.screen, CatalogScreen)

        await pilot.click(ProblemTable, offset=(10, 3))

        assert isinstance(app.screen, ExerciseScreen)
        assert app.screen.problem.slug == DEPTH


async def test_keys_from_terminal_bytes(app_repo: Path, fake_runner: FakeRunner) -> None:
    app = make_app(app_repo, fake_runner)
    async with app.run_test(size=SIZE) as pilot:
        await press_raw(pilot, "/tree")  # one read: "/" must focus the filter before "t"
        assert row_slugs(app) == [DEPTH]
        await press_raw(pilot, "\x1b")
        assert row_slugs(app) == [MERGE, RECENT, DEPTH]
        await press_raw(pilot, "\x1b[B\r")
        assert isinstance(app.screen, ExerciseScreen)
        assert app.screen.problem.slug == RECENT
        await press_raw(pilot, "\x1b")
        assert isinstance(app.screen, CatalogScreen)
        await press_raw(pilot, "q")
    assert app.return_code == 0


def test_main_reports_missing_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEET75_HOME", str(tmp_path))

    with pytest.raises(SystemExit, match=r"leet75tui: .*has no problems/ directory"):
        main()


def test_main_reports_bad_content(app_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (app_repo / "workbook" / "progress.json").write_text("{", encoding="utf-8")
    monkeypatch.setenv("LEET75_HOME", str(app_repo))

    with pytest.raises(SystemExit, match=r"leet75tui: .*invalid JSON"):
        main()


def test_main_runs_the_app(app_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launched: list[Leet75App] = []
    monkeypatch.setenv("LEET75_HOME", str(app_repo))
    monkeypatch.setattr(Leet75App, "run", lambda self: launched.append(self))

    main()

    assert len(launched) == 1
    assert launched[0].context.workbook.directory == app_repo.resolve() / "workbook"
