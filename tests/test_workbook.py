"""Workbook files: starter fallback, save, preferred language."""

import os
from pathlib import Path

import pytest

from leet75tui.catalog import Problem, load_catalog
from leet75tui.languages import Language
from leet75tui.workbook import Workbook, starter_path

MERGE = "1768_merge-strings-alternately"
DEPTH = "104_maximum-depth-of-binary-tree"


@pytest.fixture
def workbook(app_repo: Path) -> Workbook:
    return Workbook(app_repo / "workbook")


@pytest.fixture
def depth(app_repo: Path) -> Problem:
    return next(problem for problem in load_catalog(app_repo) if problem.slug == DEPTH)


@pytest.fixture
def merge(app_repo: Path) -> Problem:
    return next(problem for problem in load_catalog(app_repo) if problem.slug == MERGE)


def test_paths(app_repo: Path, workbook: Workbook, depth: Problem) -> None:
    assert workbook.directory == app_repo / "workbook"
    assert workbook.progress_path == app_repo / "workbook" / "progress.json"
    assert workbook.solution_path(DEPTH, Language.PYTHON) == app_repo / "workbook" / f"{DEPTH}.py"
    assert starter_path(depth, Language.TYPESCRIPT) == depth.path / "starter.ts"


def test_load_falls_back_to_starter_without_creating_files(
    workbook: Workbook, depth: Problem
) -> None:
    for language in Language:
        assert workbook.load(depth, language) == starter_path(depth, language).read_text()
        assert not workbook.solution_path(DEPTH, language).exists()


def test_load_prefers_the_workbook_file(workbook: Workbook, merge: Problem) -> None:
    assert "let merged" in workbook.load(merge, Language.TYPESCRIPT)
    assert workbook.load(merge, Language.PYTHON) == starter_path(merge, Language.PYTHON).read_text()


def test_save_creates_directory_and_file(tmp_path: Path, depth: Problem) -> None:
    workbook = Workbook(tmp_path / "new-workbook")

    path = workbook.save(DEPTH, Language.PYTHON, "class Solution: ...\n")

    assert path == tmp_path / "new-workbook" / f"{DEPTH}.py"
    assert workbook.load(depth, Language.PYTHON) == "class Solution: ...\n"


def test_load_raises_when_starter_is_missing(workbook: Workbook, depth: Problem) -> None:
    starter_path(depth, Language.PYTHON).unlink()

    with pytest.raises(FileNotFoundError):
        workbook.load(depth, Language.PYTHON)


def test_preferred_language_defaults_to_typescript(workbook: Workbook) -> None:
    assert workbook.preferred_language(DEPTH) is Language.TYPESCRIPT


def test_preferred_language_is_the_most_recently_modified(workbook: Workbook) -> None:
    python_file = workbook.save(DEPTH, Language.PYTHON, "py")
    assert workbook.preferred_language(DEPTH) is Language.PYTHON

    typescript_file = workbook.save(DEPTH, Language.TYPESCRIPT, "ts")
    os.utime(python_file, ns=(2_000_000_000_000_000_000, 2_000_000_000_000_000_000))
    os.utime(typescript_file, ns=(1_000_000_000_000_000_000, 1_000_000_000_000_000_000))
    assert workbook.preferred_language(DEPTH) is Language.PYTHON

    os.utime(typescript_file, ns=(3_000_000_000_000_000_000, 3_000_000_000_000_000_000))
    assert workbook.preferred_language(DEPTH) is Language.TYPESCRIPT
