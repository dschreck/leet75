"""Load a problem's meta.toml and cases.json into the job a harness runs."""

import json
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from leet75tui.runner.compare import CompareMode

META_FILE = "meta.toml"
CASES_FILE = "cases.json"
NO_CASES_MESSAGE = "No test cases yet"
PENDING_CASES = "pending"


class Kind(StrEnum):
    """How the harness calls the solution (meta.toml `kind`)."""

    FUNCTION = "function"
    LINKED_LIST = "linked-list"
    TREE = "tree"
    DESIGN = "design"
    INTERACTIVE = "interactive"


class OutputMode(StrEnum):
    """Which value is compared after the call (meta.toml `output`)."""

    RETURN = "return"
    ARG0 = "arg0"  # args[0] after an in-place call
    ARG0_PREFIX = "arg0-prefix"  # args[0][:k], k being the returned length


class ProblemError(Exception):
    """meta.toml or cases.json is missing or malformed; the message is shown to the user."""


@dataclass(frozen=True, slots=True)
class Case:
    """One test case: what the harness receives plus what the runner compares against.

    `shown_args` becomes CaseResult.args (design: {"ops": [...], "args": [...]});
    `harness_input` holds args plus ops or pick, never the expected value.
    """

    name: str
    shown_args: Any
    expected: Any
    compare: CompareMode
    harness_input: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Problem:
    """What run_solution needs from a problem directory."""

    kind: Kind
    entry: str
    param_types: tuple[str, ...]
    returns: str
    output: OutputMode
    cases: tuple[Case, ...]

    def job(self) -> dict[str, Any]:
        """The harness's job.json: the call spec and case inputs, without expected values."""
        return {
            "kind": self.kind.value,
            "entry": self.entry,
            "params": list(self.param_types),
            "returns": self.returns,
            "output": self.output.value,
            "cases": [case.harness_input for case in self.cases],
        }


@dataclass(frozen=True, slots=True)
class _CaseRules:
    """Problem-level facts every case is validated against."""

    kind: Kind
    entry: str
    arity: int
    default_compare: CompareMode


def load_problem(problem_dir: Path) -> Problem:
    """Read and validate `problem_dir`; raise ProblemError with a user-facing message."""
    meta = _read_meta(problem_dir / META_FILE)
    if meta.get("cases") == PENDING_CASES:
        raise ProblemError(NO_CASES_MESSAGE)
    kind = _member(Kind, meta.get("kind"), f"{META_FILE} kind")
    entry = _text(meta.get("entry"), f"{META_FILE} entry")
    default_compare = _member(
        CompareMode, meta.get("compare", "exact"), f"{META_FILE} compare"
    )
    output = _member(OutputMode, meta.get("output", "return"), f"{META_FILE} output")
    is_design = kind is Kind.DESIGN
    param_types = () if is_design else _param_types(meta.get("params"))
    returns = "any" if is_design else _text(meta.get("returns"), f"{META_FILE} returns")
    rules = _CaseRules(kind, entry, len(param_types), default_compare)
    raw_cases = _read_cases(problem_dir / CASES_FILE)
    cases = tuple(_case(raw, index, rules) for index, raw in enumerate(raw_cases))
    return Problem(kind, entry, param_types, returns, output, cases)


def _read_meta(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except FileNotFoundError:
        raise ProblemError(f"{META_FILE} not found in {path.parent}") from None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ProblemError(f"{META_FILE}: {exc}") from None


def _read_cases(path: Path) -> list[Any]:
    try:
        cases = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ProblemError(NO_CASES_MESSAGE) from None
    except (OSError, ValueError) as exc:  # ValueError covers JSON and UTF-8 decoding
        raise ProblemError(f"{CASES_FILE}: {exc}") from None
    if not isinstance(cases, list):
        raise ProblemError(f"{CASES_FILE} must hold a JSON array of cases")
    if not cases:
        raise ProblemError(NO_CASES_MESSAGE)
    return cases


def _member[E: StrEnum](enum: type[E], value: Any, where: str) -> E:
    try:
        return enum(value)
    except ValueError:
        choices = ", ".join(member.value for member in enum)
        raise ProblemError(
            f"{where} must be one of: {choices} (got {value!r})"
        ) from None


def _text(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProblemError(f"{where} must be a non-empty string")
    return value


def _param_types(params: Any) -> tuple[str, ...]:
    if not isinstance(params, list) or not all(
        isinstance(param, dict) for param in params
    ):
        raise ProblemError(
            f"{META_FILE} params must be an array of {{ name, type }} tables"
        )
    return tuple(
        _text(param.get("type"), f"{META_FILE} params type") for param in params
    )


def _case(raw: Any, index: int, rules: _CaseRules) -> Case:
    where = f"{CASES_FILE} case {index + 1}"
    if not isinstance(raw, dict) or "expected" not in raw:
        raise ProblemError(f"{where} must be an object with an 'expected' value")
    name = _text(raw.get("name", f"case {index + 1}"), f"{where} name")
    compare = _member(
        CompareMode, raw.get("compare", rules.default_compare), f"{where} compare"
    )
    if rules.kind is Kind.DESIGN:
        harness_input = _design_input(raw, rules.entry, where)
        shown_args: Any = dict(harness_input)
    else:
        harness_input = _call_input(raw, rules.kind, rules.arity, where)
        shown_args = harness_input["args"]
    return Case(name, shown_args, raw["expected"], compare, harness_input)


def _call_input(
    raw: dict[str, Any], kind: Kind, arity: int, where: str
) -> dict[str, Any]:
    args = raw.get("args")
    if not isinstance(args, list) or len(args) != arity:
        raise ProblemError(f"{where}: 'args' must be an array of {arity} values")
    if kind is not Kind.INTERACTIVE:
        return {"args": args}
    pick = raw.get("pick")
    if not isinstance(pick, int) or isinstance(pick, bool):
        raise ProblemError(f"{where}: an interactive case needs an integer 'pick'")
    return {"args": args, "pick": pick}


def _design_input(raw: dict[str, Any], entry: str, where: str) -> dict[str, Any]:
    ops, args = raw.get("ops"), raw.get("args")
    if (
        not isinstance(ops, list)
        or not ops
        or not all(isinstance(op, str) for op in ops)
    ):
        raise ProblemError(f"{where}: 'ops' must be a non-empty array of method names")
    if ops[0] != entry:
        raise ProblemError(f"{where}: ops[0] must be the constructor {entry!r}")
    if not isinstance(args, list) or len(args) != len(ops):
        raise ProblemError(f"{where}: 'args' must hold one array per op")
    if not all(isinstance(op_args, list) for op_args in args):
        raise ProblemError(f"{where}: each entry of 'args' must be an array")
    return {"ops": ops, "args": args}
