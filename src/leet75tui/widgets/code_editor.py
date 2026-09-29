"""The solution editor: code-editor ``TextArea`` with TS/Python modes and completion."""

from typing import ClassVar

from textual import events
from textual.binding import Binding, BindingType
from textual.widgets import TextArea

from leet75tui.languages import Language
from leet75tui.languages.typescript import register_typescript
from leet75tui.widgets.completion import (
    CompletionPopup,
    completion_candidates,
    text_without_word_at,
    word_before,
)

THEME = "monokai"
PYTHON = "python"
INDENT_WIDTHS = {Language.TYPESCRIPT: 2, Language.PYTHON: 4}
ACCEPT_KEYS = frozenset({"enter", "tab"})
POPUP_BORDER = 1  # cells of CompletionPopup's left border


class CodeEditor(TextArea):
    """``TextArea.code_editor`` settings plus a language switch and ctrl+space completion.

    While the completion popup is open, up/down pick a candidate, enter/tab accept it and
    any other key closes it (escape is routed here by the screen's priority binding).
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        # Terminals send ctrl+space as NUL, which Textual names ctrl+@.
        Binding("ctrl+space,ctrl+@", "complete", "complete", show=False),
    ]

    def __init__(self, *, entry: str = "", id: str | None = None) -> None:
        super().__init__(
            theme=THEME,
            soft_wrap=False,
            tab_behavior="indent",
            show_line_numbers=True,
            id=id,
        )
        self.entry = entry
        self.solution_language = Language.TYPESCRIPT
        self._typescript = register_typescript(self)
        self._popup = CompletionPopup()
        self._prefix = ""

    def set_solution_language(self, language: Language) -> None:
        """Switch highlighting and indent width (TS: 2 spaces, Python: 4)."""
        self.solution_language = language
        self.indent_width = INDENT_WIDTHS[language]
        self.language = self._typescript if language is Language.TYPESCRIPT else PYTHON

    @property
    def completion_open(self) -> bool:
        """True while the completion popup is shown."""
        return self._popup.is_mounted and self._popup.display

    def close_completion(self) -> None:
        """Hide the completion popup (no-op when it is closed)."""
        self._popup.display = False

    async def action_complete(self) -> None:
        """Open the popup with candidates for the word left of the cursor."""
        row, column = self.cursor_location
        prefix = word_before(self.document.get_line(row), column)
        others = text_without_word_at(self.document.lines, row, column)
        candidates = completion_candidates(prefix, others, self.solution_language, self.entry)
        if not candidates:
            self.close_completion()
            self.app.bell()
            return
        if not self._popup.is_mounted:
            await self.screen.mount(self._popup)
        self._prefix = prefix
        self._popup.show_candidates(candidates)
        x, y = self.cursor_screen_offset
        # Below the cursor line, the candidates' first letter under the word's first letter.
        self._popup.styles.offset = (x - len(prefix) - POPUP_BORDER, y + 1)
        self._popup.display = True

    def on_key(self, event: events.Key) -> None:
        """Drive the popup while it is open; otherwise leave keys to ``TextArea``."""
        if not self.completion_open:
            return
        if event.key in ACCEPT_KEYS:
            self._accept_completion()
        elif event.key == "up":
            self._popup.action_cursor_up()
        elif event.key == "down":
            self._popup.action_cursor_down()
        else:
            self.close_completion()
            return
        event.stop()
        event.prevent_default()

    def on_blur(self, event: events.Blur) -> None:
        """Close the popup when focus leaves the editor."""
        self.close_completion()

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        """Close the popup when the cursor moves (e.g. on a mouse click)."""
        self.close_completion()

    def _accept_completion(self) -> None:
        word = self._popup.selected_word
        self.close_completion()
        if word is None:
            return
        row, column = self.cursor_location
        start = (row, column - len(self._prefix))
        self.replace(word, start, (row, column), maintain_selection_offset=False)
