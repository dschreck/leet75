"""Child-process harness that runs a Python solution against a job's test cases.

The runner starts it as ``python -I harness.py RUN_DIR``. It reads ``RUN_DIR/job.json`` and
``RUN_DIR/solution.py`` and appends one JSON record per line to ``RUN_DIR/results.jsonl``::

    {"type": "case", "index": 0, "actual": ..., "error": null, "stdout": "...", "ms": 0.012}
    {"type": "fatal", "error": "..."}   # the solution could not be loaded; nothing follows
    {"type": "done"}                    # every case ran

Each record is a single ``os.write`` on an O_APPEND file, so a kill loses at most the case in
progress. ``print``, ``sys.stdout`` and ``sys.stderr`` are redirected into a capped buffer per
case (output printed while the solution loads counts toward the first case), and raw writes
to fd 1/2 only reach the runner's capped pipe: neither can touch the results file. Expected
values never enter this process; the runner does the comparing. harness.mjs implements the
same protocol for TypeScript.
"""

from __future__ import annotations

import bisect
import collections
import functools
import heapq
import io
import itertools
import json
import linecache
import math
import os
import re
import string
import sys
import time
import traceback
import typing
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

SOURCE_NAME = "solution.py"
JOB_FILE = "job.json"
RESULTS_FILE = "results.jsonl"
CASE_OUTPUT_CAP = 8 * 1024
TOTAL_OUTPUT_CAP = 64 * 1024
ERROR_TEXT_CAP = 4 * 1024
ACTUAL_JSON_CAP = 256 * 1024
OP_NOTE_CAP = 200
TRACEBACK_FRAMES = 5
TRUNCATED_MARKER = "[truncated]"
PRELOADED_MODULES = (bisect, collections, functools, heapq, itertools, math, re, string)

Job = dict[str, Any]


class ListNode:
    """Singly linked list node, as LeetCode defines it."""

    def __init__(self, val: Any = 0, next: ListNode | None = None) -> None:
        self.val = val
        self.next = next


class TreeNode:
    """Binary tree node, as LeetCode defines it."""

    def __init__(
        self, val: Any = 0, left: TreeNode | None = None, right: TreeNode | None = None
    ) -> None:
        self.val = val
        self.left = left
        self.right = right


class OutputCapture(io.TextIOBase):
    """Text sink keeping CASE_OUTPUT_CAP characters per case and TOTAL_OUTPUT_CAP per run."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._case_size = 0
        self._total_size = 0
        self._truncated = False

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            raise TypeError(f"write() argument must be str, not {type(text).__name__}")
        room = min(
            CASE_OUTPUT_CAP - self._case_size, TOTAL_OUTPUT_CAP - self._total_size
        )
        kept = text[: max(room, 0)]
        self._parts.append(kept)
        self._case_size += len(kept)
        self._total_size += len(kept)
        self._truncated = self._truncated or len(kept) < len(text)
        return len(text)

    def take(self) -> str:
        """Return the output captured since the last call and start a new case."""
        text = "".join(self._parts)
        if self._truncated:
            text += (
                "\n" if text and not text.endswith("\n") else ""
            ) + TRUNCATED_MARKER
        self._parts.clear()
        self._case_size = 0
        self._truncated = False
        return text


class Clock:
    """Accumulates the wall time spent inside user code."""

    def __init__(self) -> None:
        self.ms = 0.0

    def call(self, func: Callable[..., Any], *args: Any) -> Any:
        started = time.perf_counter()
        try:
            return func(*args)
        finally:
            self.ms += (time.perf_counter() - started) * 1000


@contextmanager
def redirected(capture: OutputCapture) -> Iterator[None]:
    """Send sys.stdout and sys.stderr to `capture` for the duration of the block."""
    saved = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = typing.cast(typing.TextIO, capture)
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved


def write_record(fd: int, record: dict[str, Any]) -> None:
    data = memoryview((json.dumps(record) + "\n").encode())
    while data:
        data = data[os.write(fd, data) :]


def cap_text(text: str, limit: int) -> str:
    return text if len(text) <= limit else f"{text[:limit]}\n{TRUNCATED_MARKER}"


def describe_exception(exc: BaseException) -> str:
    """Exception type and message plus the innermost frames that belong to the solution."""
    frames = [
        f for f in traceback.extract_tb(exc.__traceback__) if f.filename == SOURCE_NAME
    ]
    lines = traceback.format_list(frames[-TRACEBACK_FRAMES:])
    if lines:
        lines.insert(0, "Traceback (most recent call last):\n")
    lines.extend(traceback.format_exception_only(type(exc), exc))
    return cap_text("".join(lines).rstrip("\n"), ERROR_TEXT_CAP)


def build_namespace() -> dict[str, Any]:
    """Module globals pre-populated the way LeetCode's Python 3 environment does."""
    namespace: dict[str, Any] = {"__name__": "solution"}
    namespace.update({name: getattr(typing, name) for name in typing.__all__})
    namespace.update({module.__name__: module for module in PRELOADED_MODULES})
    namespace.update(ListNode=ListNode, TreeNode=TreeNode)
    return namespace


def load_solution(run_dir: str, capture: OutputCapture) -> dict[str, Any]:
    with open(os.path.join(run_dir, SOURCE_NAME), encoding="utf-8") as file:
        source = file.read()
    linecache.cache[SOURCE_NAME] = (
        len(source),
        None,
        source.splitlines(True),
        SOURCE_NAME,
    )
    namespace = build_namespace()
    with redirected(capture):  # compile() too: its SyntaxWarnings are worth showing
        code = compile(source, SOURCE_NAME, "exec", dont_inherit=True)
        exec(code, namespace)  # noqa: S102 - running the user's solution is the point
    return namespace


def missing_entry(job: Job, namespace: dict[str, Any]) -> str | None:
    entry = job["entry"]
    if job["kind"] == "design":
        found = isinstance(namespace.get(entry), type)
        return None if found else f"{SOURCE_NAME} must define class {entry}"
    solution = namespace.get("Solution")
    if isinstance(solution, type) and callable(getattr(solution, entry, None)):
        return None
    return f"{SOURCE_NAME} must define class Solution with a method {entry}(self, ...)"


def build_list(values: list[Any]) -> ListNode | None:
    head: ListNode | None = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head


def build_tree(values: list[Any]) -> TreeNode | None:
    """Build a tree from LeetCode's level-order array, where null marks a missing child."""
    nodes = [None if value is None else TreeNode(value) for value in values]
    if not nodes or nodes[0] is None:
        return None
    children = iter(nodes[1:])
    queue = collections.deque([nodes[0]])
    while queue:
        node = queue.popleft()
        node.left, node.right = next(children, None), next(children, None)
        queue.extend(child for child in (node.left, node.right) if child is not None)
    return nodes[0]


def find_tree_node(root: TreeNode | None, val: Any) -> TreeNode:
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if node.val == val:
            return node
        stack.extend((node.left, node.right))
    raise ValueError(f"TreeNodeRef {val!r} is not a value in the tree")


NODE_BUILDERS: dict[str, Callable[[list[Any]], Any]] = {
    "ListNode": build_list,
    "TreeNode": build_tree,
}


def convert_args(values: list[Any], types: list[str]) -> list[Any]:
    """Turn JSON arguments into the objects the solution expects (nodes, node references)."""
    args = [
        NODE_BUILDERS[kind](value) if kind in NODE_BUILDERS else value
        for value, kind in zip(values, types, strict=True)
    ]
    typed_args = list(zip(args, types, strict=True))
    root = next((arg for arg, kind in typed_args if kind == "TreeNode"), None)
    return [
        find_tree_node(root, arg) if kind == "TreeNodeRef" and arg is not None else arg
        for arg, kind in typed_args
    ]


def is_list_node(value: Any) -> bool:
    return hasattr(value, "val") and hasattr(value, "next")


def is_tree_node(value: Any) -> bool:
    return hasattr(value, "val") and hasattr(value, "left") and hasattr(value, "right")


def non_finite_name(value: float) -> str:
    if math.isnan(value):
        return "NaN"
    return "Infinity" if value > 0 else "-Infinity"


def plain_json(value: Any) -> Any:
    """Convert a return value to JSON-safe data; unknown objects become their repr()."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else non_finite_name(value)
    if isinstance(value, dict):
        return {str(key): plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset, collections.deque)):
        return [plain_json(item) for item in value]
    return repr(value)


def list_values(head: Any) -> list[Any]:
    values: list[Any] = []
    seen: set[int] = set()
    while head is not None:
        if id(head) in seen:
            raise ValueError("the linked list contains a cycle")
        seen.add(id(head))
        values.append(plain_json(head.val))
        head = head.next
    return values


def tree_values(root: Any) -> list[Any]:
    """Serialize a tree to LeetCode's level-order array without trailing nulls."""
    values: list[Any] = []
    seen: set[int] = set()
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            values.append(None)
            continue
        if id(node) in seen:
            raise ValueError("the tree contains a cycle or a shared node")
        seen.add(id(node))
        values.append(plain_json(node.val))
        queue.extend((node.left, node.right))
    while values and values[-1] is None:
        values.pop()
    return values


def to_json(value: Any, type_name: str) -> Any:
    """Serialize `value` according to its declared meta.toml type."""
    if type_name == "void":
        return None
    if type_name == "ListNode" and (value is None or is_list_node(value)):
        return list_values(value)
    if type_name == "TreeNode" and (value is None or is_tree_node(value)):
        return tree_values(value)
    if type_name == "TreeNodeRef" and is_tree_node(value):
        return plain_json(value.val)
    return plain_json(value)


def make_guess(pick: int) -> Callable[[int], int]:
    """LeetCode 374's guess API bound to one case's picked number."""

    def guess(num: int) -> int:
        return -1 if num > pick else 1 if num < pick else 0

    return guess


def serialize_output(job: Job, args: list[Any], result: Any) -> Any:
    if job["output"] == "arg0":
        return to_json(args[0], job["params"][0])
    if job["output"] == "arg0-prefix":
        if not isinstance(result, int) or isinstance(result, bool):
            raise TypeError(
                f"expected the new length (an int) as the return value, got {result!r}"
            )
        return to_json(args[0][:result], job["params"][0])
    return to_json(result, job["returns"])


def run_function(
    job: Job, case: dict[str, Any], namespace: dict[str, Any], clock: Clock
) -> Any:
    args = convert_args(case["args"], job["params"])
    if job["kind"] == "interactive":
        namespace["guess"] = make_guess(case["pick"])
    method = getattr(namespace["Solution"](), job["entry"])
    return serialize_output(job, args, clock.call(method, *args))


def run_design(
    job: Job, case: dict[str, Any], namespace: dict[str, Any], clock: Clock
) -> Any:
    """Construct the class with ops[0]'s args, then call each later op on the instance."""
    ops, op_args = case["ops"], case["args"]
    instance = clock.call(namespace[job["entry"]], *op_args[0])
    outputs: list[Any] = [None]
    for position in range(1, len(ops)):
        try:
            method = getattr(instance, ops[position])
            outputs.append(plain_json(clock.call(method, *op_args[position])))
        except Exception as exc:
            call = f"{ops[position]}({json.dumps(op_args[position])[1:-1]})"
            exc.add_note(f"in ops[{position}]: {call[:OP_NOTE_CAP]}")
            raise
    return outputs


def checked_size(actual: Any) -> Any:
    size = len(json.dumps(actual))
    if size > ACTUAL_JSON_CAP:
        raise ValueError(f"result too large to report: {size} characters of JSON")
    return actual


def run_case(
    job: Job, index: int, namespace: dict[str, Any], capture: OutputCapture
) -> dict[str, Any]:
    case = job["cases"][index]
    runner = run_design if job["kind"] == "design" else run_function
    clock = Clock()
    actual, error = None, None
    try:
        with redirected(capture):
            actual = checked_size(runner(job, case, namespace, clock))
    except BaseException as exc:  # noqa: BLE001 - user code may raise even SystemExit
        actual, error = None, describe_exception(exc)
    return {
        "type": "case",
        "index": index,
        "actual": actual,
        "error": error,
        "stdout": capture.take(),
        "ms": round(clock.ms, 3),
    }


def main(run_dir: str) -> None:
    with open(os.path.join(run_dir, JOB_FILE), encoding="utf-8") as file:
        job: Job = json.load(file)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    results = os.open(os.path.join(run_dir, RESULTS_FILE), flags, 0o600)
    capture = OutputCapture()
    try:
        namespace = load_solution(run_dir, capture)
    except BaseException as exc:  # noqa: BLE001 - report any load failure, even SystemExit
        write_record(results, {"type": "fatal", "error": describe_exception(exc)})
        return
    problem = missing_entry(job, namespace)
    if problem is not None:
        write_record(results, {"type": "fatal", "error": problem})
        return
    for index in range(len(job["cases"])):
        write_record(results, run_case(job, index, namespace, capture))
    write_record(results, {"type": "done"})


if __name__ == "__main__":
    main(sys.argv[1])
    os._exit(0)  # do not wait for threads the solution may have left running
