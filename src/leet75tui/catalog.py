"""The problem catalog: ``problems/<slug>/meta.toml`` loaded into typed records."""

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from leet75tui.paths import PROBLEMS_DIRNAME

META_FILENAME = "meta.toml"


class Difficulty(StrEnum):
    """LeetCode difficulty, spelled as in ``meta.toml``."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class ProblemKind(StrEnum):
    """How the harness calls a solution."""

    FUNCTION = "function"
    LINKED_LIST = "linked-list"
    TREE = "tree"
    DESIGN = "design"
    INTERACTIVE = "interactive"


class CasesStatus(StrEnum):
    """Whether ``cases.json`` holds usable test cases yet."""

    READY = "ready"
    PENDING = "pending"


class CatalogError(Exception):
    """Raised when problem metadata is missing or malformed; the message names the file."""


@dataclass(frozen=True, slots=True)
class Problem:
    """One LeetCode 75 problem as described by its ``meta.toml``."""

    slug: str
    path: Path
    id: int
    title: str
    difficulty: Difficulty
    category: str
    order: int
    url: str
    kind: ProblemKind
    entry: str
    cases: CasesStatus

    @property
    def display_title(self) -> str:
        """Title with the LeetCode number, e.g. ``334. Increasing Triplet Subsequence``."""
        return f"{self.id}. {self.title}"

    @property
    def has_cases(self) -> bool:
        """True when the problem has runnable test cases."""
        return self.cases is CasesStatus.READY


def load_catalog(root: Path) -> tuple[Problem, ...]:
    """Load every ``problems/*/meta.toml`` under ``root``, sorted by study-plan order."""
    problems_dir = root / PROBLEMS_DIRNAME
    if not problems_dir.is_dir():
        raise CatalogError(f"{problems_dir}: directory not found")
    meta_paths = sorted(problems_dir.glob(f"*/{META_FILENAME}"))
    problems = [load_problem(meta_path.parent) for meta_path in meta_paths]
    _check_unique_order(problems)
    return tuple(sorted(problems, key=lambda problem: problem.order))


def load_problem(problem_dir: Path) -> Problem:
    """Load one problem from ``problem_dir/meta.toml``."""
    meta_path = problem_dir / META_FILENAME
    try:
        meta = tomllib.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise CatalogError(f"{meta_path}: {error}") from error
    return Problem(
        slug=problem_dir.name,
        path=problem_dir,
        id=_field(meta, "id", int, meta_path),
        title=_field(meta, "title", str, meta_path),
        difficulty=_choice(meta, "difficulty", Difficulty, meta_path),
        category=_field(meta, "category", str, meta_path),
        order=_field(meta, "order", int, meta_path),
        url=_field(meta, "url", str, meta_path),
        kind=_choice(meta, "kind", ProblemKind, meta_path),
        entry=_field(meta, "entry", str, meta_path),
        cases=_choice(meta, "cases", CasesStatus, meta_path),
    )


def _field[T](meta: dict[str, Any], key: str, kind: type[T], meta_path: Path) -> T:
    value = meta.get(key)
    # Exact type: a TOML boolean must not pass as an integer.
    if isinstance(value, kind) and type(value) is kind:
        return value
    raise CatalogError(f"{meta_path}: '{key}' must be {kind.__name__}, got {value!r}")


def _choice[E: StrEnum](meta: dict[str, Any], key: str, kind: type[E], meta_path: Path) -> E:
    value = _field(meta, key, str, meta_path)
    try:
        return kind(value)
    except ValueError:
        allowed = ", ".join(member.value for member in kind)
        message = f"{meta_path}: '{key}' must be one of {allowed}, got {value!r}"
        raise CatalogError(message) from None


def _check_unique_order(problems: list[Problem]) -> None:
    seen: dict[int, Problem] = {}
    for problem in problems:
        other = seen.setdefault(problem.order, problem)
        if other is not problem:
            meta_path = problem.path / META_FILENAME
            message = f"{meta_path}: order {problem.order} is already used by {other.slug}"
            raise CatalogError(message)
