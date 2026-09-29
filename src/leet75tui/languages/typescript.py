"""TypeScript highlighting for ``TextArea`` via tree-sitter-typescript."""

from functools import cache
from pathlib import Path

import textual
from textual import log
from textual.widgets import TextArea
from tree_sitter import Language as Grammar
from tree_sitter import Query

TYPESCRIPT = "typescript"
FALLBACK = "javascript"
# The TypeScript query only adds TS-specific captures on top of the JavaScript one.
JAVASCRIPT_QUERY_PATH = Path(textual.__file__).parent / "tree-sitter/highlights/javascript.scm"


@cache
def _typescript_grammar() -> tuple[Grammar, str] | None:
    """Grammar and validated highlight query, or None when either cannot be loaded."""
    try:
        import tree_sitter_typescript

        grammar = Grammar(tree_sitter_typescript.language_typescript())
        query = JAVASCRIPT_QUERY_PATH.read_text(encoding="utf-8")
        query += "\n" + tree_sitter_typescript.HIGHLIGHTS_QUERY
        Query(grammar, query)
    except (ImportError, OSError, ValueError) as error:
        log.warning(f"TypeScript highlighting unavailable, using {FALLBACK}: {error}")
        return None
    return grammar, query


def register_typescript(text_area: TextArea) -> str:
    """Register TypeScript on ``text_area``; return the language name to use for TS code.

    Falls back to the built-in JavaScript highlighting instead of failing.
    """
    grammar = _typescript_grammar()
    if grammar is None:
        return FALLBACK
    text_area.register_language(TYPESCRIPT, *grammar)
    return TYPESCRIPT
