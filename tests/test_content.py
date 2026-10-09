"""Validate the problem content (problems/<slug>/) and the workbook (workbook/)."""

from __future__ import annotations

import ast
import functools
import json
import re
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS = ROOT / "problems"
WORKBOOK = ROOT / "workbook"
SLUGS = sorted(path.name for path in PROBLEMS.iterdir() if path.is_dir())
PROBLEM_FILES = ("problem.md", "meta.toml", "cases.json", "starter.ts", "starter.py")

KINDS = {"function", "linked-list", "tree", "design", "interactive"}
COMPARES = {"exact", "unordered", "unordered-inner", "unordered-nested", "float"}
CASE_COMPARES = COMPARES | {"one-of"}
OUTPUTS = {"return", "arg0", "arg0-prefix"}
STATUSES = {"UNSOLVED", "ATTEMPTED", "SOLVED"}
VALUE_TYPE = re.compile(
    r"(?:int|double|bool|string|char)(?:\[\])*|ListNode|TreeNode|TreeNodeRef"
)
REQUIRED_META = {
    "id": int,
    "title": str,
    "difficulty": str,
    "category": str,
    "order": int,
    "url": str,
    "kind": str,
    "entry": str,
    "cases": str,
}

# The hand-reviewed modelling; every other problem is a "function" compared exactly.
SPECIAL_KINDS = {
    "2095_delete-the-middle-node-of-a-linked-list": "linked-list",
    "328_odd-even-linked-list": "linked-list",
    "206_reverse-linked-list": "linked-list",
    "2130_maximum-twin-sum-of-a-linked-list": "linked-list",
    "104_maximum-depth-of-binary-tree": "tree",
    "872_leaf-similar-trees": "tree",
    "1448_count-good-nodes-in-binary-tree": "tree",
    "437_path-sum-iii": "tree",
    "1372_longest-zigzag-path-in-a-binary-tree": "tree",
    "236_lowest-common-ancestor-of-a-binary-tree": "tree",
    "199_binary-tree-right-side-view": "tree",
    "1161_maximum-level-sum-of-a-binary-tree": "tree",
    "700_search-in-a-binary-search-tree": "tree",
    "450_delete-node-in-a-bst": "tree",
    "208_implement-trie-prefix-tree": "design",
    "901_online-stock-span": "design",
    "933_number-of-recent-calls": "design",
    "2336_smallest-number-in-infinite-set": "design",
    "374_guess-number-higher-or-lower": "interactive",
}
SPECIAL_COMPARES = {
    "017_letter-combinations-of-a-phone-number": "unordered",
    "216_combination-sum-iii": "unordered-nested",
    "2215_find-the-difference-of-two-arrays": "unordered-inner",
    "399_evaluate-division": "float",
    "643_maximum-average-subarray-i": "float",
}
SPECIAL_OUTPUTS = {"283_move-zeroes": "arg0", "443_string-compression": "arg0-prefix"}
ONE_OF_PROBLEMS = {"162_find-peak-element", "450_delete-node-in-a-bst"}
SPECIAL_SIGNATURES = {
    "236_lowest-common-ancestor-of-a-binary-tree": (
        ["TreeNode", "TreeNodeRef", "TreeNodeRef"],
        "TreeNodeRef",
    ),
    "283_move-zeroes": (["int[]"], "void"),
    "399_evaluate-division": (["string[][]", "double[]", "string[][]"], "double[]"),
    "443_string-compression": (["char[]"], "int"),
    "643_maximum-average-subarray-i": (["int[]", "int"], "double"),
    "1926_nearest-exit-from-entrance-in-maze": (["char[][]", "int[]"], "int"),
}


@functools.cache
def meta(slug: str) -> dict[str, Any]:
    return tomllib.loads((PROBLEMS / slug / "meta.toml").read_text(encoding="utf-8"))


@functools.cache
def cases(slug: str) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads(
        (PROBLEMS / slug / "cases.json").read_text(encoding="utf-8")
    )
    return data


def slugs_of_kind(kind: str) -> list[str]:
    return [slug for slug in SLUGS if meta(slug)["kind"] == kind]


def conforms(value: Any, vocab: str) -> bool:
    """Whether a cases.json value has the shape of a meta.toml type."""
    if vocab.endswith("[]"):
        return isinstance(value, list) and all(conforms(v, vocab[:-2]) for v in value)
    match vocab:
        case "int" | "TreeNodeRef":
            return type(value) is int
        case "double":
            return type(value) in {int, float}
        case "bool":
            return type(value) is bool
        case "string":
            return type(value) is str
        case "char":
            return type(value) is str and len(value) == 1
        case "void":
            return value is None
        case "ListNode":
            return isinstance(value, list) and all(type(v) is int for v in value)
        case "TreeNode":
            return (
                isinstance(value, list)
                and all(v is None or type(v) is int for v in value)
                and (not value or value[0] is not None)
            )
    return False


def canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def same(actual: Any, expected: Any, mode: str) -> bool:
    """Minimal compare-mode semantics, enough to check the statement examples."""
    if mode == "float":
        if isinstance(actual, list):
            return len(actual) == len(expected) and all(
                same(a, e, mode) for a, e in zip(actual, expected, strict=False)
            )
        return bool(abs(actual - expected) <= 1e-5)
    if mode == "unordered":
        return sorted(map(canon, actual)) == sorted(map(canon, expected))
    if mode == "unordered-inner":
        return len(actual) == len(expected) and all(
            same(a, e, "unordered") for a, e in zip(actual, expected, strict=False)
        )
    if mode == "unordered-nested":
        return sorted(canon(sorted(map(canon, item))) for item in actual) == sorted(
            canon(sorted(map(canon, item))) for item in expected
        )
    return canon(actual) == canon(expected)


def statement_examples(slug: str) -> list[tuple[int, dict[str, Any], Any]]:
    """(number, inputs in cases.json form, statement output) for each example."""
    text = (PROBLEMS / slug / "problem.md").read_text(encoding="utf-8")
    text = text.replace("\u200b", "")
    headings = list(re.finditer(r"^\*\*Example (\d+):\*\*$", text, re.MULTILINE))
    examples = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end() : end].split("**Constraints:**")[0]
        examples.append((int(heading[1]), *parse_example(slug, section)))
    return examples


def parse_example(slug: str, section: str) -> tuple[dict[str, Any], Any]:
    if meta(slug)["kind"] == "design":
        block = re.search(r"^Input\n(.+)\n(.+)\nOutput\n(.+)$", section, re.MULTILINE)
        assert block is not None, section
        return {"ops": json.loads(block[1]), "args": json.loads(block[2])}, json.loads(
            block[3]
        )
    line = re.search(r"^(?:\*\*Input:\*\*|Input:) *(.+)$", section, re.MULTILINE)
    output = re.search(r"^(?:\*\*Output:\*\*|Output:) *(.+)$", section, re.MULTILINE)
    assert line is not None and output is not None, section
    values: dict[str, Any] = {}
    decoder, text, pos = json.JSONDecoder(), line[1].strip(), 0
    while pos < len(text):
        assignment = re.compile(r"[\s,]*(\w+)\s*=\s*").match(text, pos)
        assert assignment is not None, text
        values[assignment[1]], pos = decoder.raw_decode(text, assignment.end())
    inputs: dict[str, Any] = {
        "args": [values.pop(p["name"]) for p in meta(slug)["params"]]
    }
    if "pick" in values:
        inputs["pick"] = values.pop("pick")
    assert not values, f"unexpected inputs {values}"
    return inputs, json.loads(output[1].strip())


def test_there_are_75_problems_with_every_file() -> None:
    assert len(SLUGS) == 75
    for slug in SLUGS:
        missing = [
            name for name in PROBLEM_FILES if not (PROBLEMS / slug / name).is_file()
        ]
        assert not missing, f"{slug} lacks {missing}"


def test_plan_orders_are_1_to_75() -> None:
    assert sorted(meta(slug)["order"] for slug in SLUGS) == list(range(1, 76))


@pytest.mark.parametrize("slug", SLUGS)
def test_meta_toml_follows_the_contract(slug: str) -> None:
    data = meta(slug)
    for key, expected_type in REQUIRED_META.items():
        assert type(data.get(key)) is expected_type, f"{key} = {data.get(key)!r}"
    url_slug = data["url"].rstrip("/").rsplit("/", 1)[-1]
    assert slug == f"{data['id']:03d}_{url_slug}"
    assert data["difficulty"] in {"Easy", "Medium", "Hard"}
    assert data["kind"] in KINDS
    assert data.get("compare", "exact") in COMPARES
    assert data.get("output", "return") in OUTPUTS
    assert data["cases"] in {"ready", "pending"}
    if data["kind"] == "design":
        assert "params" not in data
        assert "returns" not in data
        return
    assert data["params"]
    for param in data["params"]:
        assert set(param) == {"name", "type"}
        assert VALUE_TYPE.fullmatch(param["type"]), param
    assert data["returns"] == "void" or VALUE_TYPE.fullmatch(data["returns"])
    assert data["entry"].isidentifier()


@pytest.mark.parametrize("slug", SLUGS)
def test_problem_md_starts_with_the_title(slug: str) -> None:
    text = (PROBLEMS / slug / "problem.md").read_text(encoding="utf-8")
    assert text.startswith(f"# {meta(slug)['id']}. {meta(slug)['title']}\n\n")
    assert "## Instructions" not in text
    assert "**Plan order**" not in text


@pytest.mark.parametrize("slug", SLUGS)
def test_cases_json_has_the_shape_of_its_kind(slug: str) -> None:
    data, problem = cases(slug), meta(slug)
    if problem["cases"] == "ready":
        assert data
    names = [case["name"] for case in data]
    assert all(isinstance(name, str) and name for name in names)
    assert len(set(names)) == len(names), "case names must be unique"
    for case in data:
        assert case.get("compare", "exact") in CASE_COMPARES
        if problem["kind"] == "design":
            assert set(case) == {"name", "ops", "args", "expected"}
            assert len(case["ops"]) == len(case["args"]) == len(case["expected"])
            assert case["ops"][0] == problem["entry"]
            assert case["expected"][0] is None
            assert all(isinstance(args, list) for args in case["args"])
            continue
        assert len(case["args"]) == len(problem["params"])
        allowed = {"name", "args", "expected", "compare"}
        if problem["kind"] == "interactive":
            assert type(case["pick"]) is int
            allowed.add("pick")
        assert set(case) <= allowed
        assert "expected" in case


@pytest.mark.parametrize("slug", [s for s in SLUGS if meta(s)["kind"] != "design"])
def test_case_values_match_the_declared_types(slug: str) -> None:
    problem = meta(slug)
    params = problem["params"]
    output = problem.get("output", "return")
    expected_type = problem["returns"] if output == "return" else params[0]["type"]
    for case in cases(slug):
        for arg, param in zip(case["args"], params, strict=True):
            assert conforms(arg, param["type"]), (case["name"], param)
            if param["type"] == "TreeNodeRef":  # must name a node of the tree
                assert arg in case["args"][0], case["name"]
        options = (
            case["expected"] if case.get("compare") == "one-of" else [case["expected"]]
        )
        assert options, case["name"]
        assert all(conforms(option, expected_type) for option in options), case["name"]


@pytest.mark.parametrize("slug", SLUGS)
def test_every_statement_example_is_a_case(slug: str) -> None:
    problem = meta(slug)
    examples = statement_examples(slug)
    assert examples, "the statement has no examples"
    for number, inputs, output in examples:
        matches = [
            case
            for case in cases(slug)
            if all(case.get(k) == v for k, v in inputs.items())
        ]
        assert matches, f"example {number} is not a case"
        case = matches[0]
        mode = case.get("compare", problem.get("compare", "exact"))
        if problem.get("output") == "arg0-prefix":  # the statement shows only k
            assert len(case["expected"]) == output, f"example {number}"
        elif mode == "one-of":
            assert any(same(output, option, "exact") for option in case["expected"])
        else:
            assert same(output, case["expected"], mode), f"example {number}"


@pytest.mark.parametrize("slug", SLUGS)
def test_ts_starter_exports_the_entry(slug: str) -> None:
    problem = meta(slug)
    source = (PROBLEMS / slug / "starter.ts").read_text(encoding="utf-8")
    keyword = "class" if problem["kind"] == "design" else "function"
    assert re.search(rf"^export {keyword} {problem['entry']}\b", source, re.MULTILINE)
    assert "README.md" not in source
    if problem["kind"] == "interactive":
        assert "declare function guess(num: number): number;" in source


@pytest.mark.parametrize("slug", SLUGS)
def test_py_starter_defines_the_entry(slug: str) -> None:
    problem = meta(slug)
    tree = ast.parse((PROBLEMS / slug / "starter.py").read_text(encoding="utf-8"))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    if problem["kind"] == "design":
        assert problem["entry"] in classes
        return
    methods = {
        node.name: node
        for node in classes["Solution"].body
        if isinstance(node, ast.FunctionDef)
    }
    arguments = [arg.arg for arg in methods[problem["entry"]].args.args]
    assert arguments == ["self", *(param["name"] for param in problem["params"])]


@pytest.mark.parametrize("slug", slugs_of_kind("design"))
def test_design_ops_are_methods_of_both_starters(slug: str) -> None:
    entry = meta(slug)["entry"]
    ops = {op for case in cases(slug) for op in case["ops"][1:]}
    tree = ast.parse((PROBLEMS / slug / "starter.py").read_text(encoding="utf-8"))
    (cls,) = (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == entry)
    py_methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
    ts_source = (PROBLEMS / slug / "starter.ts").read_text(encoding="utf-8")
    ts_methods = set(re.findall(r"^ {2}(\w+)\(", ts_source, re.MULTILINE))
    assert ops <= py_methods
    assert ops <= ts_methods


def test_special_problems_keep_their_modelling() -> None:
    for slug in SLUGS:
        problem = meta(slug)
        assert problem["kind"] == SPECIAL_KINDS.get(slug, "function"), slug
        assert problem.get("compare", "exact") == SPECIAL_COMPARES.get(slug, "exact"), (
            slug
        )
        assert problem.get("output", "return") == SPECIAL_OUTPUTS.get(slug, "return"), (
            slug
        )
    one_of = {s for s in SLUGS if any(c.get("compare") == "one-of" for c in cases(s))}
    assert one_of == ONE_OF_PROBLEMS
    for slug, (param_types, returns) in SPECIAL_SIGNATURES.items():
        assert [p["type"] for p in meta(slug)["params"]] == param_types, slug
        assert meta(slug)["returns"] == returns, slug


def test_progress_json_follows_the_contract() -> None:
    text = (WORKBOOK / "progress.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert text == json.dumps(data, indent=2, sort_keys=True) + "\n"
    assert set(data) == {"version", "problems"}
    assert data["version"] == 1
    for slug, entry in data["problems"].items():
        assert slug in SLUGS
        assert set(entry) == {"status", "lastRunAt"}
        assert entry["status"] in STATUSES
        assert entry["lastRunAt"] is None or isinstance(entry["lastRunAt"], str)


def test_workbook_files_belong_to_known_problems() -> None:
    for path in WORKBOOK.iterdir():
        if path.name != "progress.json":
            assert path.suffix in {".ts", ".py"}, path.name
            assert path.stem in SLUGS, path.name
