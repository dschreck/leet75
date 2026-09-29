"""Languages a solution can be written in."""

from enum import StrEnum


class Language(StrEnum):
    """A solution language; the value is the file suffix without the dot."""

    TYPESCRIPT = "ts"
    PYTHON = "py"

    @property
    def suffix(self) -> str:
        """File suffix including the dot, e.g. ``.ts``."""
        return f".{self.value}"

    @property
    def label(self) -> str:
        """Short uppercase label for the UI, e.g. ``TS``."""
        return self.value.upper()
