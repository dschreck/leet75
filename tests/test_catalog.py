"""Catalog loading and repository-root resolution."""

from pathlib import Path

import pytest

from leet75tui.catalog import (
    CasesStatus,
    CatalogError,
    Difficulty,
    ProblemKind,
    load_catalog,
    load_problem,
)
from leet75tui.paths import RepoNotFoundError, find_repo_root

TWO_SUM_META = """\
id = 1
title = "Two Sum"
difficulty = "Easy"
category = "Array / String"
order = 99
url = "https://leetcode.com/problems/two-sum/"
kind = "function"
entry = "twoSum"
cases = "ready"
"""


def write_meta(root: Path, slug: str, text: str) -> Path:
    problem_dir = root / "problems" / slug
    problem_dir.mkdir(parents=True)
    (problem_dir / "meta.toml").write_text(text, encoding="utf-8")
    return problem_dir


def test_load_catalog_sorts_by_order(app_repo: Path) -> None:
    catalog = load_catalog(app_repo)

    assert [problem.order for problem in catalog] == [1, 27, 38]
    assert [problem.id for problem in catalog] == [1768, 933, 104]


def test_load_catalog_parses_fields(app_repo: Path) -> None:
    first, pending, tree = load_catalog(app_repo)

    assert first.slug == "1768_merge-strings-alternately"
    assert first.path == app_repo / "problems" / first.slug
    assert first.title == "Merge Strings Alternately"
    assert first.display_title == "1768. Merge Strings Alternately"
    assert first.difficulty is Difficulty.EASY
    assert first.category == "Array / String"
    assert first.url == "https://leetcode.com/problems/merge-strings-alternately/"
    assert first.kind is ProblemKind.FUNCTION
    assert first.entry == "mergeAlternately"
    assert first.has_cases
    assert pending.cases is CasesStatus.PENDING
    assert not pending.has_cases
    assert pending.kind is ProblemKind.DESIGN
    assert tree.kind is ProblemKind.TREE


def test_load_catalog_ignores_directories_without_meta(app_repo: Path) -> None:
    (app_repo / "problems" / "scratch").mkdir()

    assert len(load_catalog(app_repo)) == 3


def test_load_catalog_requires_problems_directory(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="directory not found"):
        load_catalog(tmp_path)


def test_load_problem_reports_invalid_toml(tmp_path: Path) -> None:
    problem_dir = write_meta(tmp_path, "1_two-sum", "id = = 1")

    with pytest.raises(CatalogError, match=r"1_two-sum/meta\.toml"):
        load_problem(problem_dir)


@pytest.mark.parametrize(
    ("replace", "by", "message"),
    [
        ('title = "Two Sum"\n', "", "'title' must be str, got None"),
        ("id = 1\n", "id = true\n", "'id' must be int, got True"),
        ("order = 99\n", 'order = "99"\n', "'order' must be int"),
        ('difficulty = "Easy"', 'difficulty = "easy"', "'difficulty' must be one of Easy, Medium"),
        ('kind = "function"', 'kind = "graph"', "'kind' must be one of function, linked-list"),
        ('cases = "ready"', 'cases = "todo"', "'cases' must be one of ready, pending"),
    ],
)
def test_load_problem_names_file_and_key(
    tmp_path: Path, replace: str, by: str, message: str
) -> None:
    problem_dir = write_meta(tmp_path, "1_two-sum", TWO_SUM_META.replace(replace, by))

    with pytest.raises(CatalogError) as error:
        load_problem(problem_dir)

    assert str(problem_dir / "meta.toml") in str(error.value)
    assert message in str(error.value)


def test_load_catalog_rejects_duplicate_order(app_repo: Path) -> None:
    write_meta(app_repo, "1_two-sum", TWO_SUM_META.replace("order = 99", "order = 27"))

    with pytest.raises(CatalogError, match="order 27 is already used by"):
        load_catalog(app_repo)


def test_find_repo_root_prefers_env_var(app_repo: Path, tmp_path: Path) -> None:
    root = find_repo_root({"LEET75_HOME": str(app_repo)}, start=tmp_path / "elsewhere.py")

    assert root == app_repo.resolve()


def test_find_repo_root_rejects_env_var_without_problems(tmp_path: Path) -> None:
    with pytest.raises(RepoNotFoundError, match="has no problems/ directory"):
        find_repo_root({"LEET75_HOME": str(tmp_path)})


def test_find_repo_root_walks_up_from_package(app_repo: Path) -> None:
    module = app_repo / "src" / "leet75tui" / "paths.py"

    assert find_repo_root({}, start=module) == app_repo.resolve()


def test_find_repo_root_explains_failure(tmp_path: Path) -> None:
    with pytest.raises(RepoNotFoundError, match="LEET75_HOME"):
        find_repo_root({}, start=tmp_path / "a" / "b.py")


def test_find_repo_root_defaults_to_this_checkout() -> None:
    assert (find_repo_root({}) / "src" / "leet75tui").is_dir()
