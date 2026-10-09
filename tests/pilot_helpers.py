"""Helpers shared by the Pilot tests of the app (tests/fixtures/app repo, fake runner)."""

from pathlib import Path

import pytest
from conftest import FakeRunner
from textual._xterm_parser import XTermParser
from textual.pilot import Pilot
from textual.widgets import TabbedContent

from leet75tui.app import Leet75App
from leet75tui.languages import Language
from leet75tui.screens.exercise_screen import ExerciseScreen
from leet75tui.widgets.code_editor import CodeEditor
from leet75tui.widgets.run_output import RunOutput

SIZE = (140, 40)
MERGE = "1768_merge-strings-alternately"
RECENT = "933_number-of-recent-calls"
DEPTH = "104_maximum-depth-of-binary-tree"
NODE = Path("/usr/bin/node")


def make_app(root: Path, runner: FakeRunner, node: Path | None = NODE) -> Leet75App:
    """The app on ``root`` with a fake runner; ``node=None`` simulates a missing Node."""
    return Leet75App(root, root / "workbook", runner=runner, node_finder=lambda: node)


async def open_problem(app: Leet75App, slug: str) -> ExerciseScreen:
    """Push the exercise screen for ``slug`` and wait until it is mounted."""
    problem = next(problem for problem in app.context.catalog if problem.slug == slug)
    screen = ExerciseScreen(app.context, problem)
    await app.push_screen(screen)
    return screen


async def press_raw(pilot: Pilot[None], data: str) -> None:
    """Feed terminal bytes through Textual's own input parser, as the Linux driver does."""
    parser = XTermParser()
    for message in [*parser.feed(data), *parser.feed("")]:
        message.set_sender(pilot.app)
        pilot.app.post_message(message)
    await pilot.pause()


async def run_and_wait(pilot: Pilot[None], *keys: str) -> None:
    """Press ``keys``, wait for the run worker, then for the Output tab's deferred write."""
    await pilot.press(*keys)
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


def editor(app: Leet75App) -> CodeEditor:
    return app.screen.query_one(CodeEditor)


def active_tab(app: Leet75App) -> str:
    return app.screen.query_one(TabbedContent).active


def output_text(app: Leet75App) -> str:
    return "\n".join(line.text for line in app.screen.query_one(RunOutput).lines)


def output_words(app: Leet75App) -> str:
    """Output text with wrapping undone, for messages longer than the pane."""
    return " ".join(output_text(app).split())


def solution(root: Path, slug: str, language: Language) -> Path:
    return root / "workbook" / f"{slug}{language.suffix}"


def starter(root: Path, slug: str, language: Language) -> str:
    return (root / "problems" / slug / f"starter{language.suffix}").read_text(encoding="utf-8")


def record_notifications(app: Leet75App, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture messages sent to ``App.notify`` (screens notify through the app)."""
    messages: list[str] = []
    monkeypatch.setattr(app, "notify", lambda message, **options: messages.append(message))
    return messages
