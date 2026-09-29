"""The user's solution files: ``workbook/<slug>.ts|.py``, with starter fallback."""

from dataclasses import dataclass
from pathlib import Path

from leet75tui.catalog import Problem
from leet75tui.fileio import write_text_atomic
from leet75tui.languages import Language
from leet75tui.progress import PROGRESS_FILENAME

WORKBOOK_DIRNAME = "workbook"
STARTER_STEM = "starter"
DEFAULT_LANGUAGE = Language.TYPESCRIPT


def starter_path(problem: Problem, language: Language) -> Path:
    """``problems/<slug>/starter.<ext>`` for ``language``."""
    return problem.path / f"{STARTER_STEM}{language.suffix}"


@dataclass(frozen=True, slots=True)
class Workbook:
    """Solution files live in ``directory``; they are created on the first save."""

    directory: Path

    @classmethod
    def in_repo(cls, root: Path) -> "Workbook":
        """The workbook of the repository at ``root``."""
        return cls(root / WORKBOOK_DIRNAME)

    @property
    def progress_path(self) -> Path:
        """Where the solve status of every problem is stored."""
        return self.directory / PROGRESS_FILENAME

    def solution_path(self, slug: str, language: Language) -> Path:
        """``workbook/<slug>.<ext>``; the file may not exist yet."""
        return self.directory / f"{slug}{language.suffix}"

    def load(self, problem: Problem, language: Language) -> str:
        """The saved solution, or the problem's starter code when there is none."""
        path = self.solution_path(problem.slug, language)
        if not path.is_file():
            path = starter_path(problem, language)
        return path.read_text(encoding="utf-8")

    def save(self, slug: str, language: Language, source: str) -> Path:
        """Write the solution (creating ``workbook/`` if needed) and return its path."""
        path = self.solution_path(slug, language)
        write_text_atomic(path, source)
        return path

    def preferred_language(self, slug: str) -> Language:
        """Language of the most recently modified solution file; TypeScript if none."""
        modified = [
            (path.stat().st_mtime_ns, language)
            for language in Language
            if (path := self.solution_path(slug, language)).is_file()
        ]
        if not modified:
            return DEFAULT_LANGUAGE
        return max(modified, key=lambda item: item[0])[1]
