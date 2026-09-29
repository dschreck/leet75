"""Catalog screen: every problem with difficulty, category and solve status."""

from typing import ClassVar

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Label

from leet75tui.catalog import Difficulty, Problem
from leet75tui.context import AppContext
from leet75tui.progress import Status
from leet75tui.screens.exercise_screen import ExerciseScreen

STATUS_GLYPHS = {Status.SOLVED: "✓", Status.ATTEMPTED: "~", Status.UNSOLVED: "·"}
DIFFICULTY_STYLES = {Difficulty.EASY: "green", Difficulty.MEDIUM: "yellow", Difficulty.HARD: "red"}
PENDING_NOTE = "  (tests pending)"
STATUS_COLUMN = "status"
COLUMNS = (
    ("#", "order"),
    ("Problem", "problem"),
    ("Difficulty", "difficulty"),
    ("Category", "category"),
    (STATUS_GLYPHS[Status.SOLVED], STATUS_COLUMN),
)
# Hidden from the footer while typing in the filter, where these keys insert text.
TYPING_HIDDEN_ACTIONS = frozenset({"focus_filter", "quit"})


def matches(problem: Problem, query: str) -> bool:
    """Case-insensitive substring match over title and category."""
    needle = query.casefold()
    return needle in problem.title.casefold() or needle in problem.category.casefold()


class ProblemTable(DataTable[str | Text], inherit_bindings=False):
    """Row table whose up/down/enter belong to the screen, so they also work from the filter."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("pageup", "page_up", show=False),
        Binding("pagedown", "page_down", show=False),
        Binding("home", "scroll_top", show=False),
        Binding("end", "scroll_bottom", show=False),
    ]


class CatalogScreen(Screen[None]):
    """Browse, filter and open problems."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("up", "cursor_up", "move", key_display="↑↓", priority=True),
        Binding("down", "cursor_down", "move", show=False, priority=True),
        # Priority: the focus must move before keys that follow in the same terminal read are
        # forwarded. check_action lets "/" through to the filter while typing.
        Binding("slash", "focus_filter", "filter", key_display="/", priority=True),
        Binding("enter", "open_problem", "open", key_display="⏎", priority=True),
        Binding("escape", "clear_filter", "clear filter", show=False),
        Binding("q", "quit", "quit"),
    ]

    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self._problems = {problem.slug: problem for problem in context.catalog}
        self._table = ProblemTable(id="problems", cursor_type="row", zebra_stripes=True)
        self._filter = Input(placeholder="/ filter by title or category", id="filter", compact=True)
        self._solved = Label(id="solved")

    def compose(self) -> ComposeResult:
        yield Header()
        yield self._table
        with Horizontal(id="catalog-bar"):
            yield self._filter
            yield self._solved
        yield Footer()

    def on_mount(self) -> None:
        for label, key in COLUMNS:
            self._table.add_column(label, key=key)
        self._show_rows("")
        self._table.focus()

    def on_screen_resume(self) -> None:
        """Statuses may have changed in the exercise screen."""
        for row_key in self._table.rows:
            if row_key.value is not None:
                self._table.update_cell(row_key, STATUS_COLUMN, self._glyph(row_key.value))
        self._update_counter()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Hide keys that would type into the filter while it has focus."""
        return not (action in TYPING_HIDDEN_ACTIONS and self._filter.has_focus)

    def action_cursor_up(self) -> None:
        """Move the row cursor up."""
        self._table.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move the row cursor down."""
        self._table.action_cursor_down()

    def action_focus_filter(self) -> None:
        """Start typing a filter."""
        self.set_focus(self._filter)  # synchronous, unlike Widget.focus()

    def action_clear_filter(self) -> None:
        """Clear the filter (its Changed event restores every row) and return to the table."""
        self._filter.value = ""
        self.set_focus(self._table)

    def action_open_problem(self) -> None:
        """Open the highlighted problem."""
        if self._table.row_count == 0:
            return
        row_key, _ = self._table.coordinate_to_cell_key(self._table.cursor_coordinate)
        if row_key.value is not None:
            self._open(row_key.value)

    def action_quit(self) -> None:
        """Quit the app."""
        self.app.exit()

    @on(Input.Changed, "#filter")
    def _filter_changed(self, event: Input.Changed) -> None:
        self._show_rows(event.value)

    @on(DataTable.RowSelected)
    def _row_clicked(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value is not None:
            self._open(event.row_key.value)

    def _open(self, slug: str) -> None:
        self.app.push_screen(ExerciseScreen(self.context, self._problems[slug]))

    def _show_rows(self, query: str) -> None:
        self._table.clear()
        for problem in self.context.catalog:
            if matches(problem, query):
                self._table.add_row(*self._cells(problem), key=problem.slug)
        self._update_counter()

    def _cells(self, problem: Problem) -> tuple[str | Text, ...]:
        title = Text(problem.display_title)
        if not problem.has_cases:
            title.append(PENDING_NOTE, style="dim italic")
        return (
            Text(str(problem.order), justify="right"),
            title,
            Text(problem.difficulty.value, style=DIFFICULTY_STYLES[problem.difficulty]),
            problem.category,
            self._glyph(problem.slug),
        )

    def _glyph(self, slug: str) -> str:
        return STATUS_GLYPHS[self.context.progress.status(slug)]

    def _update_counter(self) -> None:
        catalog = self.context.catalog
        solved = self.context.progress.solved_count(problem.slug for problem in catalog)
        self._solved.update(f"{solved}/{len(catalog)} solved")
