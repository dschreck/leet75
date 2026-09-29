"""Word completion for the code editor: candidate lookup and the popup listing them."""

import keyword
import re
from collections.abc import Sequence

from textual.widgets import OptionList
from textual.widgets.option_list import Option

from leet75tui.languages import Language

MAX_CANDIDATES = 50
IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
WORD_BEFORE_CURSOR = re.compile(r"[\w$]*$")
WORD_AFTER_CURSOR = re.compile(r"[\w$]*")

TYPESCRIPT_KEYWORDS = (
    "abstract", "any", "as", "async", "await", "boolean", "break", "case", "catch", "class",
    "const", "constructor", "continue", "declare", "default", "delete", "do", "else", "enum",
    "export", "extends", "false", "finally", "for", "function", "get", "if", "implements",
    "import", "in", "instanceof", "interface", "keyof", "let", "never", "new", "null", "number",
    "of", "private", "protected", "public", "readonly", "return", "set", "static", "string",
    "super", "switch", "this", "throw", "true", "try", "type", "typeof", "undefined", "unknown",
    "var", "void", "while", "yield",
)  # fmt: skip
KEYWORDS: dict[Language, tuple[str, ...]] = {
    Language.TYPESCRIPT: TYPESCRIPT_KEYWORDS,
    Language.PYTHON: tuple(keyword.kwlist),
}


def word_before(line: str, column: int) -> str:
    """The identifier characters immediately left of ``column`` in ``line``."""
    match = WORD_BEFORE_CURSOR.search(line[:column])
    return match.group() if match else ""


def text_without_word_at(lines: Sequence[str], row: int, column: int) -> str:
    """The buffer minus the word around the cursor, so that word cannot suggest itself."""
    line = lines[row]
    start = column - len(word_before(line, column))
    after = WORD_AFTER_CURSOR.match(line, column)
    end = after.end() if after else column
    return "\n".join([*lines[:row], line[:start] + line[end:], *lines[row + 1 :]])


def completion_candidates(prefix: str, text: str, language: Language, entry: str) -> list[str]:
    """Keywords, identifiers in ``text`` and ``entry`` that extend ``prefix``, sorted."""
    words = {*KEYWORDS[language], *IDENTIFIER.findall(text), entry}
    matches = sorted(word for word in words if word.startswith(prefix) and word != prefix)
    return matches[:MAX_CANDIDATES]


class CompletionPopup(OptionList, can_focus=False):
    """Candidate list drawn over the editor; the editor keeps focus and drives it."""

    DEFAULT_CSS = """
    CompletionPopup {
        overlay: screen;
        position: absolute;
        constrain: inside inflect;
        width: auto;
        min-width: 16;
        max-width: 48;
        height: auto;
        max-height: 12;
        border: round $accent;
        padding: 0;
    }
    """

    def show_candidates(self, candidates: list[str]) -> None:
        """Replace the options with ``candidates`` and highlight the first one."""
        self.set_options(Option(word, id=word) for word in candidates)
        self.highlighted = 0

    @property
    def selected_word(self) -> str | None:
        """The highlighted candidate, if any."""
        option = self.highlighted_option
        return None if option is None else option.id
