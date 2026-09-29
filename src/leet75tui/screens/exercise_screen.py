"""Exercise screen: solution editor beside the problem statement and the test output."""

import os
import shlex
import subprocess
from pathlib import Path
from typing import ClassVar

from textual import on, work
from textual.app import ComposeResult, SuspendNotSupported
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Footer, Header, Markdown, TabbedContent, TabPane, TextArea
from textual.worker import Worker, WorkerState

from leet75tui.catalog import Problem
from leet75tui.context import AppContext
from leet75tui.languages import Language
from leet75tui.runner import DEFAULT_TIMEOUT_S, RunOutcome, RunResult
from leet75tui.widgets.code_editor import CodeEditor
from leet75tui.widgets.run_output import FAIL_STYLE, WARN_STYLE, RunOutput

AUTOSAVE_DELAY_S = 0.5
OUTPUT_MIN_WIDTH = 20  # RichLog's default of 78 overflows a half-width pane
PROBLEM_TAB = "problem"
OUTPUT_TAB = "output"
RUN_GROUP = "run"
STATEMENT_FILENAME = "problem.md"
FALLBACK_EDITOR = "vi"
NODE_MISSING = "Node >= 23.6 not found — set LEET75_NODE"
CASES_PENDING = 'No test cases for this problem yet (cases = "pending").'


def editor_command(path: Path) -> list[str]:
    """``$VISUAL`` / ``$EDITOR`` (fallback ``vi``) split into argv, followed by ``path``."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or FALLBACK_EDITOR
    return [*shlex.split(editor), str(path)]


def run_editor(path: Path) -> str | None:
    """Run the user's editor on ``path`` (no shell); return an error message on failure."""
    try:
        subprocess.run(editor_command(path), check=False)
    except (OSError, ValueError) as error:
        return str(error)
    return None


class ExerciseScreen(Screen[None]):
    """Edit, run and read one problem; edits autosave to ``workbook/``."""

    BINDINGS: ClassVar[list[BindingType]] = [
        # Windows Terminal delivers Ctrl+Enter as ctrl+j; ctrl+enter covers CSI-u terminals.
        Binding("ctrl+j,f5,ctrl+r,ctrl+enter", "run", "run", key_display="^⏎/F5", priority=True),
        Binding("f2", f"show_tab('{PROBLEM_TAB}')", "tabs", key_display="F2/F3", priority=True),
        Binding("f3", f"show_tab('{OUTPUT_TAB}')", "output", show=False, priority=True),
        Binding("ctrl+t", "toggle_language", "lang", key_display="^t", priority=True),
        # Windows Terminal delivers Ctrl+Shift+O as ctrl+o.
        Binding("ctrl+o,f4", "open_editor", "$EDITOR", key_display="^⇧O/F4", priority=True),
        # TextArea would consume escape (focus next), so this must be a priority binding.
        Binding("escape", "back", "back", key_display="esc", priority=True),
    ]

    def __init__(self, context: AppContext, problem: Problem) -> None:
        super().__init__()
        self.context = context
        self.problem = problem
        self.solution_language = context.workbook.preferred_language(problem.slug)
        # Held directly: on_unmount still saves after the children have left the DOM.
        self._editor = CodeEditor(entry=problem.entry, id="editor")
        self._output = RunOutput(
            id="output-log", wrap=True, markup=False, min_width=OUTPUT_MIN_WIDTH
        )
        self._saved_text = ""
        self._autosave_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="split"):
            yield self._editor
            with TabbedContent(initial=PROBLEM_TAB, id="side"):
                with TabPane("Problem", id=PROBLEM_TAB), VerticalScroll(id="statement-scroll"):
                    yield Markdown(self._statement(), id="statement")
                with TabPane("Output", id=OUTPUT_TAB):
                    yield self._output
        yield Footer()

    def on_mount(self) -> None:
        self._load(self.solution_language)
        self._editor.focus()

    def on_unmount(self) -> None:
        self._save_if_dirty()

    def action_run(self) -> None:
        """Save, switch to the Output tab and run the tests in a worker."""
        self._editor.close_completion()
        source = self._editor.text
        self._save_ensuring_file()
        if not self.problem.has_cases:
            self._show_message(CASES_PENDING)
            return
        self.action_show_tab(OUTPUT_TAB)
        self._output.show_running()
        self._run_tests(self.solution_language, source)

    def action_show_tab(self, tab: str) -> None:
        """Activate the Problem or Output tab."""
        self.query_one(TabbedContent).active = tab

    def action_toggle_language(self) -> None:
        """Save, then load the other language's solution or starter."""
        self._editor.close_completion()
        if not self._save_if_dirty():
            return
        is_typescript = self.solution_language is Language.TYPESCRIPT
        self._load(Language.PYTHON if is_typescript else Language.TYPESCRIPT)

    def action_open_editor(self) -> None:
        """Suspend the app, edit the solution in ``$EDITOR`` and reload it."""
        self._editor.close_completion()
        path = self._save_ensuring_file()
        if path is None:
            return
        try:
            # run_editor never raises: an exception here would skip the app's resume.
            with self.app.suspend():
                error = run_editor(path)
        except SuspendNotSupported as unsupported:
            error = str(unsupported)
        if error:
            self.notify(f"$EDITOR failed: {error}", severity="error")
        self._reload(path)

    def action_back(self) -> None:
        """Close the completion popup if open; otherwise save and return to the catalog."""
        if self._editor.completion_open:
            self._editor.close_completion()
        elif self._save_if_dirty():
            self.app.pop_screen()

    @on(TextArea.Changed, "#editor")
    def _schedule_autosave(self) -> None:
        if self._autosave_timer is not None:
            self._autosave_timer.stop()
        if self._is_dirty():
            self._autosave_timer = self.set_timer(AUTOSAVE_DELAY_S, self._save_if_dirty)

    @work(exclusive=True, group=RUN_GROUP, exit_on_error=False)
    async def _run_tests(self, language: Language, source: str) -> None:
        if language is Language.TYPESCRIPT and not await self.context.node.available():
            self._show_message(NODE_MISSING)
            return
        result = await self.context.run_solution(self.problem.path, language, source)
        self.action_show_tab(OUTPUT_TAB)  # the user may have switched tabs during the run
        self._output.show_result(result, DEFAULT_TIMEOUT_S)
        self._record(result)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Report a crashed run in the Output tab instead of exiting the app."""
        if event.worker.group == RUN_GROUP and event.state is WorkerState.ERROR:
            self._show_message(f"Runner crashed: {event.worker.error!r}", FAIL_STYLE)

    def _show_message(self, message: str, style: str = WARN_STYLE) -> None:
        self.action_show_tab(OUTPUT_TAB)
        self._output.show_message(message, style)

    def _record(self, result: RunResult) -> None:
        if result.outcome is RunOutcome.UNAVAILABLE:
            return  # nothing ran, so it is not an attempt
        try:
            self.context.progress.record_run(self.problem.slug, all_passed=result.all_passed)
        except OSError as error:
            self.notify(f"Cannot save progress: {error}", severity="error")

    def _statement(self) -> str:
        path = self.problem.path / STATEMENT_FILENAME
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            return f"*Cannot read {path}: {error}*"

    def _load(self, language: Language) -> None:
        try:
            text = self.context.workbook.load(self.problem, language)
        except (OSError, UnicodeDecodeError) as error:
            self.notify(f"Cannot load {language.label} code: {error}", severity="error")
            text = ""
        self.solution_language = language
        editor = self._editor
        editor.set_solution_language(language)
        editor.load_text(text)
        self._saved_text = editor.text
        self.title = f"{self.problem.display_title} — [{language.label}]"

    def _reload(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            self.notify(f"Cannot reload {path}: {error}", severity="error")
            return
        editor = self._editor
        location = editor.cursor_location
        editor.load_text(text)
        self._saved_text = editor.text
        editor.move_cursor(location)

    def _is_dirty(self) -> bool:
        return self._editor.text != self._saved_text

    def _save_if_dirty(self) -> bool:
        """Persist unsaved edits; False when they could not be written."""
        return not self._is_dirty() or self._write() is not None

    def _save_ensuring_file(self) -> Path | None:
        """Persist edits and create the workbook file even when unchanged (run, $EDITOR)."""
        path = self.context.workbook.solution_path(self.problem.slug, self.solution_language)
        if self._is_dirty() or not path.is_file():
            return self._write()
        return path

    def _write(self) -> Path | None:
        if self._autosave_timer is not None:
            self._autosave_timer.stop()
        text = self._editor.text
        try:
            path = self.context.workbook.save(self.problem.slug, self.solution_language, text)
        except OSError as error:
            self.notify(f"Save failed: {error}", severity="error")
            return None
        self._saved_text = text
        return path
