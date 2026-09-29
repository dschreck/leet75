#!/usr/bin/env python3
"""Migrate the legacy NNN_slug/ folders into problems/ and workbook/ (one-shot).

Usage: python3 scripts/migrate_legacy.py

Reads the legacy folders and the root README.md (never modifies them) and regenerates
problems/<slug>/{problem.md,meta.toml,cases.json,starter.ts,starter.py}, a
workbook/<slug>.ts copy of every real legacy solution, and workbook/progress.json.

cases.json comes from solution.test.ts: every expect() on the entry point becomes a
case. Each "Example N" of the statement is then cross-checked against those cases:
a missing example is added and a conflicting expectation is replaced by the
statement's output; both are reported. Re-running regenerates the same files.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
type Case = dict[str, Json]
type Expr = Lit | Name | Attr | Call | New

ROOT = Path(__file__).resolve().parent.parent
PROBLEMS = ROOT / "problems"
WORKBOOK = ROOT / "workbook"
LEGACY_DIR = re.compile(r"\d+_[a-z0-9-]+")
STALE_HEADER = " * See README.md in this folder for the full problem statement.\n"

# Modelling the legacy TypeScript cannot express, keyed by problem id.
COMPARE = {
    17: "unordered",  # "Return the answer in any order."
    216: "unordered-nested",  # "the combinations may be returned in any order"
    2215: "unordered-inner",  # "the integers in the lists may be returned in any order"
    399: "float",
    643: "float",  # "Any answer with a calculation error less than 10^-5"
}
OUTPUT = {283: "arg0", 443: "arg0-prefix"}  # in-place problems
DOUBLE = {399: {"values", "return"}, 643: {"return"}}  # TS number that is fractional
CHAR = {443: {"chars"}, 1926: {"maze"}}  # TS string that LeetCode types as char
TREE_REF = {236: {"p", "q", "return"}}  # nodes passed and returned by their value
TEST_HELPERS = {"ListNode", "TreeNode", "setPick", "guess"}

TS_TYPES = {
    "number": "int",
    "string": "string",
    "boolean": "bool",
    "void": "void",
    "ListNode | null": "ListNode",
    "TreeNode | null": "TreeNode",
}
PY_TYPES = {
    "int": "int",
    "double": "float",
    "bool": "bool",
    "string": "str",
    "char": "str",
    "void": "None",
    "ListNode": "Optional[ListNode]",
    "TreeNode": "Optional[TreeNode]",
    "TreeNodeRef": '"TreeNode"',
}

TS_LIST_NODE = """/**
 * Definition for singly-linked list.
 */
export class ListNode {
  val: number;
  next: ListNode | null;
  constructor(val?: number, next?: ListNode | null) {
    this.val = val === undefined ? 0 : val;
    this.next = next === undefined ? null : next;
  }
}
"""
TS_TREE_NODE = """/**
 * Definition for a binary tree node.
 */
export class TreeNode {
  val: number;
  left: TreeNode | null;
  right: TreeNode | null;
  constructor(val?: number, left?: TreeNode | null, right?: TreeNode | null) {
    this.val = val === undefined ? 0 : val;
    this.left = left === undefined ? null : left;
    this.right = right === undefined ? null : right;
  }
}
"""
TS_GUESS_API = """/**
 * Forward declaration of guess API.
 * @param {number} num   your guess
 * @return               -1 if num is higher than the picked number
 *                        1 if num is lower than the picked number
 *                        otherwise return 0
 */
declare function guess(num: number): number;
"""
PY_COMMENTS = {
    "linked-list": """# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
""",
    "tree": """# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
""",
    "interactive": """# The guess API is already defined for you.
# @param num, your guess
# @return -1 if num is higher than the picked number
#          1 if num is lower than the picked number
#          otherwise return 0
# def guess(num: int) -> int:
""",
}


class MigrationError(Exception):
    pass


# --------------------------------------------------------------------------- legacy


@dataclass
class Readme:
    id: int
    title: str
    difficulty: str
    category: str
    order: int
    url: str
    statement: str


@dataclass
class Signature:
    """The entry point of a legacy solution.ts, with TypeScript types."""

    entry: str
    params: list[tuple[str, str]]
    returns: str  # "" for a class
    methods: list[tuple[str, list[tuple[str, str]], str]]  # classes only
    is_interactive: bool


def parse_readme(text: str) -> Readme:
    heading = re.match(r"# (\d+)\. (.+)\n", text)
    cells = dict(re.findall(r"^\| \*\*(.+?)\*\* \| (.*?) \|$", text, re.MULTILINE))
    order = re.fullmatch(r"(\d+) / 75", cells.get("Plan order", ""))
    parts = text.split("\n## Instructions\n")
    if heading is None or order is None or len(parts) != 2:
        raise MigrationError("README.md lacks the heading, plan order or Instructions")
    return Readme(
        id=int(heading[1]),
        title=heading[2].strip(),
        difficulty=cells["Difficulty"],
        category=cells["Category"],
        order=int(order[1]),
        url=cells["LeetCode"],
        statement=parts[1].strip("\n") + "\n",
    )


def split_params(text: str) -> list[tuple[str, str]]:
    params = []
    for part in text.split(","):
        if part.strip():
            name, ts_type = part.split(":", 1)
            params.append((name.strip(), ts_type.strip()))
    return params


def parse_signature(source: str) -> Signature:
    functions = {
        m[1]: m
        for m in re.finditer(
            r"^export function (\w+)\(([^)]*)\):\s*([^{]+?)\s*\{", source, re.MULTILINE
        )
    }
    classes = {
        m[1]: m for m in re.finditer(r"^export class (\w+) \{$", source, re.MULTILINE)
    }
    entries = [name for name in [*functions, *classes] if name not in TEST_HELPERS]
    if len(entries) != 1:
        raise MigrationError(f"expected one exported entry point, found {entries}")
    entry = entries[0]
    is_interactive = "setPick" in functions
    if entry in functions:
        match = functions[entry]
        return Signature(entry, split_params(match[2]), match[3], [], is_interactive)
    start = classes[entry].end()
    body = source[start : source.index("\n}", start)]
    methods = [
        (m[1], split_params(m[2]), m[3])
        for m in re.finditer(
            r"^  (\w+)\(([^)]*)\):\s*([^{]+?)\s*\{$", body, re.MULTILINE
        )
    ]
    return Signature(entry, [], "", methods, is_interactive)


def drop_stale_header(source: str) -> str:
    """Remove the header line pointing at the legacy README (and its blank line)."""
    return source.replace(" *\n" + STALE_HEADER, "").replace(STALE_HEADER, "")


def done_flags(readme_text: str) -> dict[str, bool]:
    rows = re.findall(
        r"^\| \d+ \| \[[^\]]*\]\(([^)]+)/README\.md\) \|.*\| \[([ x])\] \|$",
        readme_text,
        re.MULTILINE,
    )
    return {slug: flag == "x" for slug, flag in rows}


# ---------------------------------------------------------------------- the model


@dataclass
class Param:
    name: str
    type: str


@dataclass
class Method:
    name: str
    params: list[Param]
    returns: str


@dataclass
class Problem:
    slug: str
    id: int
    kind: str
    entry: str
    params: list[Param]
    returns: str  # "" for design
    methods: list[Method]  # design only
    compare: str
    output: str


def to_vocab(ts_type: str, problem_id: int, name: str) -> str:
    """Map a TypeScript type to the meta.toml vocabulary; name is a param or "return"."""
    base, dims = ts_type.strip(), 0
    while base.endswith("[]"):
        base, dims = base[:-2], dims + 1
    vocab = TS_TYPES[base]
    if vocab == "int" and name in DOUBLE.get(problem_id, set()):
        vocab = "double"
    elif vocab == "string" and name in CHAR.get(problem_id, set()):
        vocab = "char"
    elif vocab == "TreeNode" and name in TREE_REF.get(problem_id, set()):
        vocab = "TreeNodeRef"
    return vocab + "[]" * dims


def build_problem(slug: str, readme: Readme, signature: Signature) -> Problem:
    pid = readme.id
    params = [Param(n, to_vocab(t, pid, n)) for n, t in signature.params]
    returns = to_vocab(signature.returns, pid, "return") if signature.returns else ""
    methods = [
        Method(
            name,
            [Param(n, to_vocab(t, pid, n)) for n, t in method_params],
            to_vocab(ret, pid, "return"),
        )
        for name, method_params, ret in signature.methods
    ]
    types = " ".join([p.type for p in params] + [returns])
    if not signature.returns:
        kind = "design"
    elif signature.is_interactive:
        kind = "interactive"
    elif "ListNode" in types:
        kind = "linked-list"
    elif "TreeNode" in types:
        kind = "tree"
    else:
        kind = "function"
    return Problem(
        slug=slug,
        id=pid,
        kind=kind,
        entry=signature.entry,
        params=params,
        returns=returns,
        methods=methods,
        compare=COMPARE.get(pid, "exact"),
        output=OUTPUT.get(pid, "return"),
    )


# ------------------------------------------------- reading the legacy vitest files


@dataclass(frozen=True)
class Lit:
    value: Json


@dataclass(frozen=True)
class Name:
    id: str


@dataclass(frozen=True)
class Attr:
    obj: Expr
    attr: str


@dataclass(frozen=True)
class Call:
    func: Expr
    args: tuple[Expr, ...]


@dataclass(frozen=True)
class New:
    cls: str
    args: tuple[Expr, ...]


TOKEN = re.compile(
    r"""\s*(?:
        (?P<number>\d+(?:\.\d+)?)
      | (?P<string>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
      | (?P<name>[A-Za-z_$][\w$]*)
      | (?P<punct>\?\.|[-()\[\],.])
    )""",
    re.VERBOSE,
)
TEST_BLOCK = re.compile(r"\b(?:it|test)\(\s*(['\"])(.*?)\1\s*,\s*\(\)\s*=>\s*\{")
CONST = re.compile(r"const (\w+) = (.+)", re.DOTALL)
FOR_EACH_CLOSE_TO = re.compile(  # 399: [...].forEach((expected, i) => toBeCloseTo)
    r"(\[.*\])\.forEach\(\(expected, i\) => \{\s*"
    r"expect\((\w+)\[i\]\)\.toBeCloseTo\(expected, \d+\);?\s*\}\)",
    re.DOTALL,
)


class ExprParser:
    """Parser for the JavaScript expression subset used by the legacy tests."""

    def __init__(self, source: str) -> None:
        self.tokens: list[tuple[str, str]] = []
        pos, source = 0, source.rstrip()
        while pos < len(source):
            match = TOKEN.match(source, pos)
            if match is None or match.lastgroup is None:
                raise MigrationError(f"cannot tokenize {source[pos : pos + 40]!r}")
            self.tokens.append((match.lastgroup, match[match.lastgroup]))
            pos = match.end()
        self.pos = 0

    def parse(self) -> Expr:
        expr = self.expr()
        if self.pos != len(self.tokens):
            raise MigrationError(f"unexpected {self.tokens[self.pos][1]!r}")
        return expr

    def take(self) -> tuple[str, str]:
        if self.pos >= len(self.tokens):
            raise MigrationError("unexpected end of expression")
        self.pos += 1
        return self.tokens[self.pos - 1]

    def at(self, text: str) -> bool:
        return self.pos < len(self.tokens) and self.tokens[self.pos][1] == text

    def expect(self, text: str) -> None:
        if self.take()[1] != text:
            raise MigrationError(f"expected {text!r}")

    def expr(self) -> Expr:
        kind, text = self.take()
        node: Expr
        if text == "-":
            operand = self.expr()
            if not isinstance(operand, Lit) or not isinstance(
                operand.value, int | float
            ):
                raise MigrationError("unary minus on a non-number")
            return Lit(-operand.value)
        if kind == "number":
            node = Lit(float(text) if "." in text else int(text))
        elif kind == "string":
            node = Lit(re.sub(r"\\(.)", r"\1", text[1:-1]))
        elif text in ("null", "undefined", "true", "false"):
            node = Lit({"true": True, "false": False}.get(text))
        elif text == "new":
            node = New(self.take()[1], self.arguments())
        elif text == "[":
            node = Lit([literal(item) for item in self.sequence("]")])
        elif kind == "name":
            node = Name(text)
        else:
            raise MigrationError(f"unexpected {text!r}")
        while True:
            if self.at("("):
                node = Call(node, self.arguments())
            elif self.at(".") or self.at("?."):
                self.pos += 1
                node = Attr(node, self.take()[1])
            else:
                return node

    def sequence(self, close: str) -> list[Expr]:
        items = []
        while not self.at(close):
            items.append(self.expr())
            if not self.at(close):
                self.expect(",")
        self.expect(close)
        return items

    def arguments(self) -> tuple[Expr, ...]:
        self.expect("(")
        return tuple(self.sequence(")"))


def parse_expr(source: str) -> Expr:
    return ExprParser(source).parse()


def literal(node: Expr) -> Json:
    if not isinstance(node, Lit):
        raise MigrationError(f"expected a literal, got {node!r}")
    return node.value


def skip_string(text: str, start: int) -> int:
    """Return the index just past the string literal opening at text[start]."""
    pos = start + 1
    while text[pos] != text[start]:
        pos += 2 if text[pos] == "\\" else 1
    return pos + 1


def split_statements(body: str) -> list[str]:
    """Split a block body on top-level semicolons."""
    parts, depth, start, pos = [], 0, 0, 0
    while pos < len(body):
        char = body[pos]
        if char in "'\"`":
            pos = skip_string(body, pos)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == ";" and depth == 0:
            parts.append(body[start:pos])
            start = pos + 1
        pos += 1
    parts.append(body[start:])
    return [part.strip() for part in parts if part.strip()]


def test_blocks(source: str) -> list[tuple[str, str]]:
    """Return (title, body) of every it()/test() block."""
    blocks = []
    for match in TEST_BLOCK.finditer(source):
        depth, pos = 1, match.end()
        while depth:
            char = source[pos]
            if char in "'\"`":
                pos = skip_string(source, pos)
                continue
            depth += {"{": 1, "}": -1}.get(char, 0)
            pos += 1
        blocks.append((match[2], source[match.end() : pos - 1]))
    return blocks


def split_expect(node: Expr) -> tuple[Expr, str, tuple[Expr, ...]] | None:
    """Split expect(subject).matcher(arguments) into its parts."""
    if (
        isinstance(node, Call)
        and isinstance(node.func, Attr)
        and isinstance(node.func.obj, Call)
        and node.func.obj.func == Name("expect")
        and len(node.func.obj.args) == 1
    ):
        return node.func.obj.args[0], node.func.attr, node.args
    return None


def as_double(value: Json) -> Json:
    if isinstance(value, list):
        return [as_double(item) for item in value]
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    return value


def tree_array(node: Expr) -> list[Json]:
    """Serialize a `new TreeNode(...)` expression to LeetCode level order."""
    out: list[Json] = []
    queue: list[Expr] = [node]
    while queue:
        current = queue.pop(0)
        if isinstance(current, Lit) and current.value is None:
            out.append(None)
            continue
        if not isinstance(current, New) or current.cls != "TreeNode":
            raise MigrationError(f"expected new TreeNode(...), got {current!r}")
        children = list(current.args[1:]) + [Lit(None)] * (3 - len(current.args))
        out.append(literal(current.args[0]))
        queue += children
    while out and out[-1] is None:
        out.pop()
    return out


class BlockReader:
    """Turns the statements of one legacy it()/test() block into cases."""

    def __init__(self, problem: Problem, title: str) -> None:
        self.problem = problem
        self.title = title
        self.env: dict[str, Expr] = {}
        self.cases: list[Case] = []
        self.pick: Json = None  # interactive: the number given to setPick()
        self.instance = ""  # design: the variable holding the object under test
        self.ops: list[Json] = []
        self.op_args: list[Json] = []
        self.op_results: list[Json] = []
        self.in_place: tuple[str, Case] | None = None  # (argument variable, case)

    def read(self, body: str) -> list[Case]:
        for statement in split_statements(body):
            self.statement(statement)
        if self.ops:
            self.cases.append(
                {
                    "name": "",
                    "ops": self.ops,
                    "args": self.op_args,
                    "expected": self.op_results,
                }
            )
        for number, case in enumerate(self.cases, 1):
            case["name"] = (
                self.title if len(self.cases) == 1 else f"{self.title} ({number})"
            )
        return self.cases

    def statement(self, text: str) -> None:
        if match := FOR_EACH_CLOSE_TO.fullmatch(text):
            case = self.call_case(Name(match[2]))
            case["expected"] = self.value(parse_expr(match[1]), self.problem.returns)
        elif match := CONST.fullmatch(text):
            value = parse_expr(match[2])
            if isinstance(value, New) and value.cls == self.problem.entry:
                self.instance = match[1]
                self.ops, self.op_args, self.op_results = [value.cls], [[]], [None]
            else:
                self.env[match[1]] = value
        elif expectation := split_expect(node := parse_expr(text)):
            self.expect(*expectation)
        elif isinstance(node, Call) and node.func == Name("setPick"):
            self.pick = literal(node.args[0])
        elif self.is_method_call(node):
            self.design_op(node, None)
        elif isinstance(node, Call) and node.func == Name(self.problem.entry):
            self.call_case(node)  # in place: the next expect() inspects the argument
        else:
            raise MigrationError(f"unsupported statement {text!r}")

    def expect(self, subject: Expr, matcher: str, arguments: tuple[Expr, ...]) -> None:
        if matcher in ("toBeInstanceOf", "toHaveLength"):
            return  # the "exports X" smoke test; 399 checks every index anyway
        if matcher in ("toContain", "toContainEqual"):
            case = self.call_case(arguments[0])
            options = literal(subject)
            if not isinstance(options, list):
                raise MigrationError(f"{matcher} needs a list of accepted answers")
            returns = self.problem.returns
            case["expected"] = [self.value(Lit(option), returns) for option in options]
            case["compare"] = "one-of"
            return
        if matcher not in ("toBe", "toEqual", "toStrictEqual", "toBeNull"):
            raise MigrationError(f"unsupported matcher {matcher}")
        expected = Lit(None) if matcher == "toBeNull" else arguments[0]
        if self.is_method_call(subject):
            self.design_op(subject, expected)
        elif self.in_place and self.problem.output != "return":
            self.expect_in_place(subject, expected)
        else:
            case = self.call_case(subject)
            case["expected"] = self.value(expected, self.problem.returns)

    def expect_in_place(self, subject: Expr, expected: Expr) -> None:
        """283 checks `nums` after the call; 443 checks `chars.slice(0, k)`."""
        assert self.in_place is not None
        variable, case = self.in_place
        arg_type = self.problem.params[0].type
        if subject == Name(variable) and self.problem.output == "arg0":
            case["expected"] = self.value(expected, arg_type)
        elif (
            isinstance(subject, Call)
            and subject.func == Attr(Name(variable), "slice")
            and self.problem.output == "arg0-prefix"
        ):
            prefix = self.value(expected, arg_type)
            if subject.args != (Lit(0), Lit(case.get("expected"))) or not isinstance(
                prefix, list
            ):
                raise MigrationError("slice(0, k) must follow expect(call).toBe(k)")
            case["expected"] = prefix
        else:
            case = self.call_case(subject)
            case["expected"] = self.value(expected, self.problem.returns)

    def resolve(self, node: Expr) -> Expr:
        while isinstance(node, Name) and node.id in self.env:
            node = self.env[node.id]
        return node

    def entry_call(self, node: Expr) -> Call:
        """Find the entry-point call inside toArray(...), x?.val and variables."""
        node = self.resolve(node)
        if isinstance(node, Call) and node.func == Name(self.problem.entry):
            return node
        if isinstance(node, Call) and node.func == Name("toArray"):
            return self.entry_call(node.args[0])
        if isinstance(node, Attr) and node.attr == "val":
            return self.entry_call(node.obj)
        raise MigrationError(f"no call to {self.problem.entry} in {node!r}")

    def call_case(self, node: Expr) -> Case:
        call = self.entry_call(node)
        params = self.problem.params
        if len(call.args) != len(params):
            raise MigrationError(
                f"{self.problem.entry} called with {len(call.args)} args"
            )
        case: Case = {
            "name": "",
            "args": [self.value(arg, p.type) for arg, p in zip(call.args, params)],
        }
        if self.problem.kind == "interactive":
            if self.pick is None:
                raise MigrationError("guessNumber called before setPick")
            case["pick"] = self.pick
        self.cases.append(case)
        if isinstance(call.args[0], Name):
            self.in_place = (call.args[0].id, case)
        return case

    def value(self, node: Expr, vocab: str) -> Json:
        """Convert an argument or expected expression to its cases.json form."""
        node = self.resolve(node)
        if isinstance(node, Call) and node.func in (
            Name("buildList"),
            Name("buildTree"),
        ):
            return literal(node.args[0])
        if isinstance(node, Call) and node.func == Name("find"):  # 236: node by value
            return literal(node.args[1])
        if isinstance(node, New):
            return tree_array(node)
        value = literal(node)
        if value is None and vocab in ("ListNode", "TreeNode"):
            return []
        return as_double(value) if vocab.startswith("double") else value

    def is_method_call(self, node: Expr) -> bool:
        return (
            isinstance(node, Call)
            and isinstance(node.func, Attr)
            and node.func.obj == Name(self.instance)
        )

    def design_op(self, node: Expr, expected: Expr | None) -> None:
        assert isinstance(node, Call) and isinstance(node.func, Attr)
        self.ops.append(node.func.attr)
        self.op_args.append([literal(arg) for arg in node.args])
        self.op_results.append(None if expected is None else literal(expected))


def legacy_cases(problem: Problem, test_source: str) -> list[Case]:
    cases: list[Case] = []
    for title, body in test_blocks(test_source):
        cases += BlockReader(problem, title).read(body)
    return cases


# --------------------------------------------------- statement examples cross-check


INPUT_KEYS = ("ops", "args", "pick")


@dataclass
class Example:
    number: int
    case: Case  # cases.json form without a name


def canon(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def json_value(text: str) -> Json:
    value: Json
    value, end = json.JSONDecoder().raw_decode(text.strip())
    if end != len(text.strip()):
        raise MigrationError(f"trailing text after JSON value in {text!r}")
    return value


def parse_assignments(text: str) -> dict[str, Json]:
    """Parse `a = [1,2], b = "x"` from a statement's Input line."""
    values: dict[str, Json] = {}
    decoder, text, pos = json.JSONDecoder(), text.strip(), 0
    while pos < len(text):
        match = re.compile(r"[\s,]*(\w+)\s*=\s*").match(text, pos)
        if match is None:
            raise MigrationError(f"cannot parse example input {text!r}")
        values[match[1]], pos = decoder.raw_decode(text, match.end())
    return values


def statement_examples(problem: Problem, statement: str) -> list[Example]:
    text = statement.replace("\u200b", "")
    headings = list(re.finditer(r"^\*\*Example (\d+):\*\*$", text, re.MULTILINE))
    examples = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end() : end].split("**Constraints:**")[0]
        examples.append(parse_example(problem, int(heading[1]), section))
    if not examples:
        raise MigrationError("the statement has no examples")
    return examples


def parse_example(problem: Problem, number: int, section: str) -> Example:
    if problem.kind == "design":
        block = re.search(r"^Input\n(.+)\n(.+)\nOutput\n(.+)$", section, re.MULTILINE)
        if block is None:
            raise MigrationError(f"example {number}: no Input/Output block")
        ops, args, expected = (json_value(group) for group in block.groups())
        return Example(number, {"ops": ops, "args": args, "expected": expected})
    inputs = re.search(r"^(?:\*\*Input:\*\*|Input:)[ \t]*(.+)$", section, re.MULTILINE)
    output = re.search(
        r"^(?:\*\*Output:\*\*|Output:)[ \t]*(.+)$", section, re.MULTILINE
    )
    if inputs is None or output is None:
        raise MigrationError(f"example {number}: no Input/Output lines")
    values = parse_assignments(inputs[1])
    case: Case = {}
    try:
        case["args"] = [values.pop(p.name) for p in problem.params]
        if problem.kind == "interactive":
            case["pick"] = values.pop("pick")
    except KeyError as missing:
        raise MigrationError(f"example {number}: no input named {missing}") from None
    if values:
        raise MigrationError(f"example {number}: unexpected inputs {sorted(values)}")
    expected = json_value(output[1])
    case["expected"] = (
        as_double(expected) if problem.returns.startswith("double") else expected
    )
    return Example(number, case)


def equivalent(actual: Json, expected: Json, mode: str) -> bool:
    if mode == "float":
        if isinstance(actual, list) and isinstance(expected, list):
            return len(actual) == len(expected) and all(
                equivalent(a, e, mode) for a, e in zip(actual, expected)
            )
        return (
            isinstance(actual, int | float)
            and isinstance(expected, int | float)
            and abs(actual - expected) <= 1e-5
        )
    if mode == "exact":
        return canon(actual) == canon(expected)
    if not isinstance(actual, list) or not isinstance(expected, list):
        return False
    if mode == "unordered":
        return sorted(map(canon, actual)) == sorted(map(canon, expected))
    if mode == "unordered-inner":
        return len(actual) == len(expected) and all(
            equivalent(a, e, "unordered") for a, e in zip(actual, expected)
        )
    if mode == "unordered-nested":
        inner = [
            [canon(sorted(map(canon, item))) for item in side if isinstance(item, list)]
            for side in (actual, expected)
        ]
        lengths_match = len(inner[0]) == len(actual) and len(inner[1]) == len(expected)
        return lengths_match and sorted(inner[0]) == sorted(inner[1])
    raise MigrationError(f"unknown compare mode {mode}")


def satisfies(problem: Problem, case: Case, statement_output: Json) -> bool:
    """Whether the case accepts the statement's output (as a solution would print it)."""
    expected = case["expected"]
    if problem.output == "arg0-prefix":  # the statement shows only the length k
        return isinstance(expected, list) and len(expected) == statement_output
    mode = case.get("compare", problem.compare)
    if mode == "one-of":
        options = expected if isinstance(expected, list) else []
        return any(equivalent(statement_output, option, "exact") for option in options)
    assert isinstance(mode, str)
    return equivalent(statement_output, expected, mode)


def reconcile(
    problem: Problem, cases: list[Case], notes: list[str], statement: str
) -> None:
    """Make every statement example a case whose expectation agrees with it."""
    for example in statement_examples(problem, statement):
        wanted = example.case
        match = next(
            (
                case
                for case in cases
                if all(canon(case.get(k)) == canon(wanted.get(k)) for k in INPUT_KEYS)
            ),
            None,
        )
        if match is None:
            if problem.output == "arg0-prefix":
                raise MigrationError(f"example {example.number} has no legacy case")
            cases.append({"name": f"example {example.number}", **wanted})
            notes.append(f"{problem.slug}: added statement example {example.number}")
        elif not satisfies(problem, match, wanted["expected"]):
            if problem.output == "arg0-prefix" or "compare" in match:
                raise MigrationError(f"example {example.number} contradicts the tests")
            notes.append(
                f"{problem.slug}: case {match['name']!r} expected "
                f"{canon(match['expected'])}, statement example {example.number} "
                f"says {canon(wanted['expected'])}; kept the statement"
            )
            match["expected"] = wanted["expected"]


def drop_duplicates(
    problem: Problem, cases: list[Case], notes: list[str]
) -> list[Case]:
    unique: dict[str, Case] = {}
    for case in cases:
        key = canon({k: v for k, v in case.items() if k != "name"})
        if key in unique:
            notes.append(f"{problem.slug}: dropped duplicate case {case['name']!r}")
        else:
            unique[key] = case
    return list(unique.values())


def validate(problem: Problem, cases: list[Case]) -> None:
    names = [case["name"] for case in cases]
    if not cases or len(set(map(str, names))) != len(names):
        raise MigrationError("cases are missing or their names are not unique")
    for case in cases:
        if "expected" not in case:
            raise MigrationError(f"case {case['name']!r} has no expectation")
        if problem.output == "arg0-prefix" and not isinstance(case["expected"], list):
            raise MigrationError(f"case {case['name']!r} lacks the compressed prefix")


# ------------------------------------------------------------------------ writers


def toml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # a valid TOML basic string


def meta_toml(readme: Readme, problem: Problem) -> str:
    lines = [
        f"id = {readme.id}",
        f"title = {toml_str(readme.title)}",
        f"difficulty = {toml_str(readme.difficulty)}",
        f"category = {toml_str(readme.category)}",
        f"order = {readme.order}",
        f"url = {toml_str(readme.url)}",
        f"kind = {toml_str(problem.kind)}",
        f"entry = {toml_str(problem.entry)}",
    ]
    if problem.kind != "design":
        params = ", ".join(
            f"{{ name = {toml_str(p.name)}, type = {toml_str(p.type)} }}"
            for p in problem.params
        )
        lines += [f"params = [{params}]", f"returns = {toml_str(problem.returns)}"]
    if problem.compare != "exact":
        lines.append(f"compare = {toml_str(problem.compare)}")
    if problem.output != "return":
        lines.append(f"output = {toml_str(problem.output)}")
    lines.append('cases = "ready"')
    text = "\n".join(lines) + "\n"
    tomllib.loads(text)  # fail fast on a malformed file
    return text


def cases_json(cases: list[Case]) -> str:
    rows = ",\n".join("  " + json.dumps(case, ensure_ascii=False) for case in cases)
    return f"[\n{rows}\n]\n"


def ts_starter(
    readme: Readme, problem: Problem, legacy: str, signature: Signature
) -> str:
    if "Not implemented" in legacy:  # a legacy stub: keep it, minus the stale header
        source = drop_stale_header(legacy)
        if problem.kind == "interactive":  # the harness provides guess()
            start = source.index("/**\n * The guess API")
            end = source.index("export function guessNumber")
            source = source[:start] + TS_GUESS_API + "\n" + source[end:]
        return source
    if problem.kind == "design":
        raise MigrationError("no stub generator for a solved design problem")
    header = (
        f"/**\n * {readme.id}. {readme.title}\n * {readme.url}\n"
        f" * Difficulty: {readme.difficulty}\n * Category: {readme.category}\n */\n"
    )
    params = [f"{name}: {ts_type}" for name, ts_type in signature.params]
    head, tail = f"export function {signature.entry}(", f"): {signature.returns} {{"
    line = head + ", ".join(params) + tail
    if len(line) > 80:  # prettier: one parameter per line
        line = head + "\n" + "".join(f"  {param},\n" for param in params) + tail
    function = f"{line}\n  throw new Error('Not implemented: {signature.entry}');\n}}\n"
    nodes = [
        node
        for name, node in (("ListNode", TS_LIST_NODE), ("TreeNode", TS_TREE_NODE))
        if name in line
    ]
    return "\n".join([header, *nodes, function])


def py_type(vocab: str) -> str:
    dims = vocab.count("[]")
    result = PY_TYPES[vocab[: len(vocab) - 2 * dims]]
    for _ in range(dims):
        result = f"List[{result}]"
    return result


def py_def(name: str, params: list[Param], returns: str) -> str:
    """A method header formatted the way ruff format / black would."""
    args = ["self", *(f"{p.name}: {py_type(p.type)}" for p in params)]
    head, tail = f"    def {name}(", f") -> {py_type(returns)}:"
    line = head + ", ".join(args) + tail
    if len(line) <= 88:
        return line
    if len("        " + ", ".join(args)) <= 88:
        return f"{head}\n        {', '.join(args)}\n    {tail}"
    return head + "\n" + "".join(f"        {arg},\n" for arg in args) + "    " + tail


def py_starter(problem: Problem) -> str:
    if problem.kind == "design":
        lines = [
            f"class {problem.entry}:",
            "    def __init__(self) -> None:",
            "        # TODO: initialise state",
            "        pass",
        ]
        for method in problem.methods:
            error = f"{problem.entry}.{method.name}"
            lines += [
                "",
                py_def(method.name, method.params, method.returns),
                f'        raise NotImplementedError("{error}")',
            ]
    else:
        lines = [
            "class Solution:",
            py_def(problem.entry, problem.params, problem.returns),
        ]
        if problem.output == "arg0":
            arg = problem.params[0].name
            lines += [
                '        """',
                f"        Do not return anything, modify {arg} in-place instead.",
                '        """',
            ]
        lines.append(f'        raise NotImplementedError("{problem.entry}")')
    body = PY_COMMENTS.get(problem.kind, "") + "\n".join(lines) + "\n"
    names = [name for name in ("List", "Optional") if f"{name}[" in body]
    return (f"from typing import {', '.join(names)}\n\n\n" if names else "") + body


def progress_json(statuses: dict[str, str]) -> str:
    problems = {slug: {"status": s, "lastRunAt": None} for slug, s in statuses.items()}
    data = {"version": 1, "problems": problems}
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- main


def migrate_problem(folder: Path, notes: list[str]) -> tuple[Problem, int, bool]:
    """Write problems/<slug>/ (and workbook/<slug>.ts); return (problem, cases, real)."""
    readme = parse_readme((folder / "README.md").read_text(encoding="utf-8"))
    legacy = (folder / "solution.ts").read_text(encoding="utf-8")
    signature = parse_signature(legacy)
    problem = build_problem(folder.name, readme, signature)
    tests = (folder / "solution.test.ts").read_text(encoding="utf-8")
    cases = drop_duplicates(problem, legacy_cases(problem, tests), notes)
    reconcile(problem, cases, notes, readme.statement)
    validate(problem, cases)
    target = PROBLEMS / folder.name
    write(target / "problem.md", f"# {readme.id}. {readme.title}\n\n{readme.statement}")
    write(target / "meta.toml", meta_toml(readme, problem))
    write(target / "cases.json", cases_json(cases))
    write(target / "starter.ts", ts_starter(readme, problem, legacy, signature))
    write(target / "starter.py", py_starter(problem))
    is_real = "Not implemented" not in legacy
    if is_real:
        write(WORKBOOK / f"{folder.name}.ts", drop_stale_header(legacy))
    return problem, len(cases), is_real


def main() -> int:
    folders = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir() and LEGACY_DIR.fullmatch(path.name)
    )
    done = done_flags((ROOT / "README.md").read_text(encoding="utf-8"))
    if sorted(done) != [folder.name for folder in folders]:
        print(
            "error: the README table and the legacy folders disagree", file=sys.stderr
        )
        return 1
    notes: list[str] = []
    statuses: dict[str, str] = {}
    kinds: Counter[str] = Counter()
    total = 0
    for folder in folders:
        try:
            problem, count, is_real = migrate_problem(folder, notes)
        except MigrationError as error:
            print(f"error: {folder.name}: {error}", file=sys.stderr)
            return 1
        kinds[problem.kind] += 1
        total += count
        if done[folder.name]:
            statuses[folder.name] = "SOLVED"
        elif is_real:
            statuses[folder.name] = "ATTEMPTED"
    write(WORKBOOK / "progress.json", progress_json(statuses))
    print("\n".join(notes))
    print(
        f"{len(folders)} problems, {total} cases, kinds: {dict(sorted(kinds.items()))}"
    )
    print(f"progress: {dict(sorted(Counter(statuses.values()).items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
