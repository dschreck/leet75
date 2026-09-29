"""Solution runner: both harnesses, every kind and output mode, limits, timeouts, cancel."""

import asyncio
import json
import shutil
import signal
import sys
import tempfile
import textwrap
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from leet75tui.languages import Language
from leet75tui.runner import (
    DEFAULT_TIMEOUT_S,
    RunOutcome,
    RunResult,
    find_node,
    run_solution,
)
from leet75tui.runner.node import node_command
from leet75tui.runner.problem import load_problem
from leet75tui.runner.runner import CPU_LIMIT_MARGIN_S

FIXTURES = Path(__file__).parent / "fixtures" / "runner"
PY = Language.PYTHON
TS = Language.TYPESCRIPT
NEEDS_NODE = pytest.mark.skipif(find_node() is None, reason="needs Node.js >= 23.6")
NEEDS_PROC = pytest.mark.skipif(
    not Path("/proc/self/stat").exists(), reason="needs /proc"
)
BOTH = pytest.mark.parametrize(
    "language", [pytest.param(PY, id="py"), pytest.param(TS, id="ts", marks=NEEDS_NODE)]
)
FAST_TIMEOUT_S = 1.0
CASE_OUTPUT_CAP = 8 * 1024
TOTAL_OUTPUT_CAP = 64 * 1024
TRUNCATED = "[truncated]"

KIND_FIXTURES = [
    "add",  # function, output = return
    "reverse_list",  # linked-list
    "search_bst",  # tree -> TreeNode
    "lca",  # tree with TreeNodeRef params and return
    "recent_counter",  # design
    "guess_number",  # interactive
    "move_zeroes",  # output = arg0
    "compress",  # output = arg0-prefix
    "distinct",  # per-case compare override
]

# Case 3 of the "add" fixture has a < 0: these sources hang there after starting a grandchild
# that holds the output pipe, and record both pids so the test can check they are gone.
HANG = {
    PY: """
        import os
        import subprocess

        class Solution:
            def add(self, a, b):
                if a < 0:
                    sleeper = subprocess.Popen(["sleep", "60"])
                    with open(PID_FILE, "w") as file:
                        file.write(f"{os.getpid()} {sleeper.pid}")
                    while True:
                        pass
                return a + b
        """,
    TS: """
        import { spawn } from 'node:child_process';
        import { writeFileSync } from 'node:fs';

        export function add(a: number, b: number): number {
          if (a < 0) {
            const sleeper = spawn('sleep', ['60'], { stdio: 'inherit' });
            writeFileSync(PID_FILE, `${process.pid} ${sleeper.pid}`);
            while (true) {}
          }
          return a + b;
        }
        """,
}


def fixture_source(problem: str, language: Language) -> str:
    return (FIXTURES / problem / f"solution{language.suffix}").read_text(
        encoding="utf-8"
    )


async def run(
    problem: str | Path,
    language: Language,
    source: str | None = None,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> RunResult:
    """Run `source` (dedented) or the fixture's own solution against a fixture problem."""
    problem_dir = problem if isinstance(problem, Path) else FIXTURES / problem
    code = fixture_source(problem_dir.name, language) if source is None else source
    return await run_solution(
        problem_dir, language, textwrap.dedent(code), timeout_s=timeout_s
    )


def copy_fixture(tmp_path: Path, problem: str) -> Path:
    return Path(shutil.copytree(FIXTURES / problem, tmp_path / problem))


def process_state(pid: int) -> str | None:
    """The /proc state letter of `pid`, or None once it no longer exists."""
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        return None


def is_running(pid: int) -> bool:
    return process_state(pid) not in {None, "Z", "X"}


def running_group_members(pgid: int) -> list[int]:
    members = []
    for stat_file in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = stat_file.read_text().rsplit(")", 1)[1].split()
        except (OSError, IndexError):
            continue
        if int(fields[2]) == pgid and fields[0] not in {"Z", "X"}:
            members.append(int(stat_file.parent.name))
    return members


async def eventually(predicate: Callable[[], bool], timeout_s: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while not predicate():
        if time.monotonic() > deadline:
            return False
        await asyncio.sleep(0.02)
    return True


def read_pids(pid_file: Path) -> tuple[int, int] | None:
    try:
        harness, sleeper = pid_file.read_text().split()
    except (OSError, ValueError):
        return None
    return int(harness), int(sleeper)


async def assert_all_gone(pid_file: Path) -> None:
    pids = read_pids(pid_file)
    assert pids is not None
    harness, sleeper = pids
    assert await eventually(lambda: not running_group_members(harness))
    assert not is_running(harness)
    assert not is_running(sleeper)


def cpu_time_limit(pid: int) -> list[str]:
    """Soft and hard RLIMIT_CPU of `pid` as /proc shows them."""
    for line in Path(f"/proc/{pid}/limits").read_text().splitlines():
        if line.startswith("Max cpu time"):
            return line.split()[3:5]
    return []


# --- every kind and output mode -------------------------------------------------------------


@BOTH
@pytest.mark.parametrize("problem", KIND_FIXTURES)
async def test_fixture_solutions_pass(problem: str, language: Language) -> None:
    total = len(json.loads((FIXTURES / problem / "cases.json").read_text()))
    result = await run(problem, language)
    assert result.outcome is RunOutcome.PASSED, result
    assert result.all_passed
    assert result.passed_count == len(result.cases) == total
    assert result.message == f"{total}/{total} cases passed"


@BOTH
async def test_case_results_describe_each_case(language: Language) -> None:
    result = await run("add", language)
    first, _, last = result.cases
    assert (first.index, first.name, first.args, first.expected) == (
        0,
        "small",
        [1, 2],
        3,
    )
    assert (first.actual, first.error, first.stdout) == (3, None, "")
    assert (last.index, last.name) == (2, "case 3")
    assert all(case.ms >= 0 for case in result.cases)
    assert result.duration_ms > 0


@BOTH
async def test_nodes_serialize_to_leetcode_arrays(language: Language) -> None:
    listed = await run("reverse_list", language)
    tree = await run("search_bst", language)
    ancestor = await run("lca", language)
    assert [case.actual for case in listed.cases] == [[5, 4, 3, 2, 1], [2, 1], []]
    assert [case.actual for case in tree.cases] == [[2, 1, 3], [], [8, None, 9]]
    assert [case.actual for case in ancestor.cases] == [3, 5, 1]


@BOTH
async def test_design_case_shows_ops_and_outputs(language: Language) -> None:
    result = await run("recent_counter", language)
    first = result.cases[0]
    assert first.args == {
        "ops": ["RecentCounter", "ping", "ping", "ping", "ping"],
        "args": [[], [1], [100], [3001], [3002]],
    }
    assert first.actual == [None, 1, 2, 3, 3]


@BOTH
async def test_per_case_compare_override_decides_the_case(
    language: Language, tmp_path: Path
) -> None:
    problem = copy_fixture(tmp_path, "distinct")
    cases = json.loads((problem / "cases.json").read_text())
    del cases[1]["compare"]
    (problem / "cases.json").write_text(json.dumps(cases))
    result = await run(problem, language)
    assert result.outcome is RunOutcome.FAILED
    assert [case.passed for case in result.cases] == [True, False]
    assert result.cases[1].actual == [3, 2, 1]


# --- wrong answers, exceptions, load failures -----------------------------------------------

WRONG = {
    PY: """
        class Solution:
            def add(self, a, b):
                return a + b if a > 0 else 99
        """,
    TS: """
        export function add(a: number, b: number): number {
          return a > 0 ? a + b : 99;
        }
        """,
}
RAISES = {
    PY: """
        class Solution:
            def add(self, a, b):
                if a > 10:
                    raise ValueError("boom")
                return a + b
        """,
    TS: """
        export function add(a: number, b: number): number {
          if (a > 10) throw new RangeError('boom');
          return a + b;
        }
        """,
}
RAISE_TEXT = {
    PY: 'File "solution.py", line 5, in add\n    raise ValueError("boom")',
    TS: "RangeError: boom\n    at add (solution.ts:3:",
}
STARTER = {
    PY: """
        class Solution:
            def add(self, a: int, b: int) -> int:
                raise NotImplementedError("add")
        """,
    TS: """
        export function add(a: number, b: number): number {
          throw new Error('Not implemented: add');
        }
        """,
}
STARTER_ERROR = {PY: "NotImplementedError: add", TS: "Error: Not implemented: add"}
SYNTAX = {
    PY: """
        class Solution:
            def add(self, a, b):
                return a +
        """,
    TS: """
        export function add(a: number, b: number): number {
          return a + ;
        }
        """,
}
MISSING = {
    PY: """
        class Solution:
            def plus(self, a, b):
                return a + b
        """,
    TS: """
        function add(a: number, b: number): number {
          return a + b;
        }
        """,
}
MISSING_TEXT = {
    PY: "solution.py must define class Solution with a method add(self, ...)",
    TS: "solution.ts must export function add",
}
BAD_IMPORT = {
    PY: "import no_such_module_for_leet75tui\n",
    TS: "import { add } from './no-such-module.ts';\nexport { add };\n",
}


@BOTH
async def test_wrong_answer_fails_with_actual_value(language: Language) -> None:
    result = await run("add", language, WRONG[language])
    assert result.outcome is RunOutcome.FAILED
    assert result.message == "2/3 cases passed"
    assert not result.all_passed
    assert (result.cases[2].passed, result.cases[2].actual, result.cases[2].error) == (
        False,
        99,
        None,
    )


@BOTH
async def test_exception_is_reported_on_its_case(language: Language) -> None:
    result = await run("add", language, RAISES[language])
    assert result.outcome is RunOutcome.FAILED
    assert [case.passed for case in result.cases] == [True, False, True]
    failed = result.cases[1]
    assert failed.actual is None
    assert failed.error is not None
    assert RAISE_TEXT[language] in failed.error
    assert "harness" not in failed.error


@BOTH
async def test_starter_errors_are_per_case_not_a_crash(language: Language) -> None:
    result = await run("add", language, STARTER[language])
    assert result.outcome is RunOutcome.FAILED
    assert result.message == "0/3 cases passed"
    assert all(STARTER_ERROR[language] in (case.error or "") for case in result.cases)


@BOTH
async def test_syntax_error_is_a_trimmed_error(language: Language) -> None:
    result = await run("add", language, SYNTAX[language])
    assert result.outcome is RunOutcome.ERROR
    assert result.cases == ()
    assert "SyntaxError" in result.message
    assert f"solution{language.suffix}" in result.message
    assert "leet75tui-run-" not in result.message
    assert "harness" not in result.message
    assert "node:internal" not in result.message


@BOTH
async def test_missing_entry_is_an_error(language: Language) -> None:
    result = await run("add", language, MISSING[language])
    assert result.outcome is RunOutcome.ERROR
    assert result.message == MISSING_TEXT[language]


@BOTH
async def test_import_error_is_an_error(language: Language) -> None:
    result = await run("add", language, BAD_IMPORT[language])
    assert result.outcome is RunOutcome.ERROR
    assert "no-such-module" in result.message or "no_such_module" in result.message
    assert "harness" not in result.message
    assert "leet75tui-run-" not in result.message


@BOTH
async def test_design_error_names_the_failing_op(language: Language) -> None:
    source = {
        PY: """
            class RecentCounter:
                def ping(self, t):
                    if t == 100:
                        raise KeyError(t)
                    return 1
            """,
        TS: """
            export class RecentCounter {
              ping(t: number): number {
                if (t === 100) throw new TypeError(`bad ${t}`);
                return 1;
              }
            }
            """,
    }[language]
    result = await run("recent_counter", language, source)
    assert result.outcome is RunOutcome.FAILED
    assert "in ops[2]: ping(100)" in (result.cases[0].error or "")


@BOTH
async def test_arg0_prefix_requires_an_integer_length(language: Language) -> None:
    source = {
        PY: """
            class Solution:
                def compress(self, chars):
                    return None
            """,
        TS: """
            export function compress(chars: string[]): number {
              return undefined as unknown as number;
            }
            """,
    }[language]
    result = await run("compress", language, source)
    assert result.outcome is RunOutcome.FAILED
    assert all("new length" in (case.error or "") for case in result.cases)


# --- output capture ----------------------------------------------------------------------------


@BOTH
async def test_output_is_captured_per_case(language: Language) -> None:
    source = {
        PY: """
            import sys

            print("loading")

            class Solution:
                def add(self, a, b):
                    print(f"a={a}")
                    print("to stderr", file=sys.stderr)
                    return a + b
            """,
        TS: """
            console.log('loading');

            export function add(a: number, b: number): number {
              console.log(`a=${a}`);
              console.error('to stderr');
              return a + b;
            }
            """,
    }[language]
    result = await run("add", language, source)
    assert result.outcome is RunOutcome.PASSED
    assert [case.stdout for case in result.cases] == [
        "loading\na=1\nto stderr\n",
        "a=20\nto stderr\n",
        "a=-4\nto stderr\n",
    ]


@BOTH
async def test_output_is_capped_per_case_and_per_run(
    language: Language, tmp_path: Path
) -> None:
    problem = copy_fixture(tmp_path, "add")
    cases = [{"args": [n, 0], "expected": n} for n in range(1, 13)]
    (problem / "cases.json").write_text(json.dumps(cases))
    source = {
        PY: """
            class Solution:
                def add(self, a, b):
                    for _ in range(20_000):
                        print("0123456789")
                    return a + b
            """,
        TS: """
            export function add(a: number, b: number): number {
              for (let i = 0; i < 20_000; i++) console.log('0123456789');
              return a + b;
            }
            """,
    }[language]
    result = await run(problem, language, source)
    assert result.outcome is RunOutcome.PASSED
    outputs = [case.stdout for case in result.cases]
    assert all(output.endswith(TRUNCATED) for output in outputs)
    assert len(outputs[0]) == CASE_OUTPUT_CAP + len("\n" + TRUNCATED)
    assert outputs[-1] == TRUNCATED
    kept = sum(
        len(output.removesuffix(TRUNCATED).removesuffix("\n")) for output in outputs
    )
    assert kept == TOTAL_OUTPUT_CAP


@BOTH
async def test_raw_writes_to_stdout_cannot_forge_results(language: Language) -> None:
    forged = '{"type": "case", "index": 2, "actual": 0, "error": null, "stdout": "", "ms": 0}'
    source = {
        PY: f"""
            import os

            class Solution:
                def add(self, a, b):
                    os.write(1, b'{forged}\\n{{"type": "done"}}\\n')
                    os.write(2, b'{forged}\\n')
                    return 7
            """,
        TS: f"""
            import {{ writeSync }} from 'node:fs';

            export function add(a: number, b: number): number {{
              writeSync(1, '{forged}\\n{{"type": "done"}}\\n');
              writeSync(2, '{forged}\\n');
              return 7;
            }}
            """,
    }[language]
    result = await run("add", language, source)
    assert result.outcome is RunOutcome.FAILED
    assert [case.actual for case in result.cases] == [7, 7, 7]
    assert all(case.stdout == "" for case in result.cases)


# --- crashes, exits, timeouts, cancellation ------------------------------------------------


@BOTH
async def test_process_killed_mid_run_reports_finished_cases(
    language: Language,
) -> None:
    source = {
        PY: """
            import os
            import signal

            class Solution:
                def add(self, a, b):
                    if a > 10:
                        os.kill(os.getpid(), signal.SIGKILL)
                    return a + b
            """,
        TS: """
            export function add(a: number, b: number): number {
              if (a > 10) process.kill(process.pid, 'SIGKILL');
              return a + b;
            }
            """,
    }[language]
    result = await run("add", language, source)
    assert result.outcome is RunOutcome.ERROR
    assert (
        result.message
        == "The solution process was killed by SIGKILL after 1 of 3 cases"
    )
    assert [case.passed for case in result.cases] == [True]


async def test_python_hard_exit_reports_exit_code_and_output() -> None:
    source = """
        import os

        class Solution:
            def add(self, a, b):
                if a > 10:
                    os.write(2, b"about to exit\\n")
                    os._exit(7)
                return a + b
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.ERROR
    assert result.message == (
        "The solution process exited with code 7 after 1 of 3 cases:\nabout to exit"
    )


async def test_python_system_exit_is_a_case_error() -> None:
    source = """
        import sys

        class Solution:
            def add(self, a, b):
                sys.exit(3)
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.FAILED
    assert all("SystemExit: 3" in (case.error or "") for case in result.cases)


@NEEDS_NODE
async def test_typescript_process_exit_is_a_case_error() -> None:
    source = """
        export function add(a: number, b: number): number {
          process.exit(3);
        }
        """
    result = await run("add", TS, source)
    assert result.outcome is RunOutcome.FAILED
    assert all(
        "process.exit(3) is not allowed" in (case.error or "") for case in result.cases
    )


@pytest.mark.skipif(not hasattr(signal, "SIGRTMIN"), reason="needs real-time signals")
async def test_signal_without_a_name_is_reported_by_number() -> None:
    source = """
        import os
        import signal

        class Solution:
            def add(self, a, b):
                os.kill(os.getpid(), signal.SIGRTMIN + 1)
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.ERROR
    number = signal.SIGRTMIN + 1
    assert (
        result.message
        == f"The solution process was killed by signal {number} after 0 of 3 cases"
    )


async def test_junk_in_the_results_file_is_ignored() -> None:
    source = """
        class Solution:
            def add(self, a, b):
                with open("results.jsonl", "a") as results:
                    results.write('not json\\n[1, 2]\\n{"type": "case", "index": 99}\\n')
                return a + b
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.PASSED, result


async def test_python_is_unavailable_without_an_interpreter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "executable", "")
    result = await run("add", PY)
    assert result.outcome is RunOutcome.UNAVAILABLE
    assert result.message == "No Python interpreter found to run the solution"


async def test_interpreter_that_cannot_start_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(sys, "executable", str(tmp_path / "missing-python"))
    result = await run("add", PY)
    assert result.outcome is RunOutcome.ERROR
    assert result.message.startswith("Could not run the solution: ")


async def test_run_directory_failure_is_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_space(*args: object, **kwargs: object) -> str:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(tempfile, "mkdtemp", no_space)
    result = await run("add", PY)
    assert result.outcome is RunOutcome.ERROR
    assert result.message.startswith("Could not create a run directory: ")


@NEEDS_PROC
@BOTH
async def test_timeout_kills_the_process_group(
    language: Language, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    pid_file = tmp_path / "pids"
    source = HANG[language].replace("PID_FILE", json.dumps(str(pid_file)))
    gaps: list[float] = []

    async def tick() -> None:
        last = time.perf_counter()
        while True:
            await asyncio.sleep(0.01)
            now = time.perf_counter()
            gaps.append(now - last)
            last = now

    ticker = asyncio.create_task(tick())
    started = time.perf_counter()
    result = await run("add", language, source, timeout_s=FAST_TIMEOUT_S)
    elapsed = time.perf_counter() - started
    ticker.cancel()

    assert result.outcome is RunOutcome.TIMED_OUT
    assert result.message == "timed out after 1.0 s"
    assert [case.passed for case in result.cases] == [True, True]
    assert FAST_TIMEOUT_S <= elapsed < FAST_TIMEOUT_S + 1.5
    await assert_all_gone(pid_file)
    assert not list(tmp_path.glob("leet75tui-run-*"))
    assert gaps
    assert max(gaps) < 0.25  # the event loop kept running while the child spun


@NEEDS_PROC
@BOTH
async def test_cancellation_kills_the_process_group(
    language: Language, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    pid_file = tmp_path / "pids"
    source = HANG[language].replace("PID_FILE", json.dumps(str(pid_file)))
    task = asyncio.create_task(run("add", language, source, timeout_s=60))
    assert await eventually(lambda: read_pids(pid_file) is not None)
    pids = read_pids(pid_file)
    assert pids is not None
    cpu_limit = 60 + CPU_LIMIT_MARGIN_S  # backstop should the app itself die mid-run
    assert cpu_time_limit(pids[0]) == [str(cpu_limit), str(cpu_limit + 1)]
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await assert_all_gone(pid_file)
    assert not list(tmp_path.glob("leet75tui-run-*"))


# --- language specifics --------------------------------------------------------------------


async def test_python_namespace_matches_leetcode() -> None:
    source = """
        class Solution:
            def add(self, a: int, b: int) -> int:
                values: List[int] = [a, b]
                best: Optional[int] = heapq.nlargest(1, values)[0]
                queue: Deque[int] = collections.deque(values)
                node = TreeNode(ListNode(0).val)
                return sum(queue) + node.val + best - best + math.floor(0.5)

        if __name__ == "__main__":
            raise SystemExit("the harness must not run this block")
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.PASSED, result


async def test_python_compile_warnings_show_in_the_first_case_output() -> None:
    source = """
        DIGITS = "\\d+"

        class Solution:
            def add(self, a, b):
                return a + b
        """
    result = await run("add", PY, source)
    assert result.outcome is RunOutcome.PASSED
    first_output = result.cases[0].stdout
    assert "solution.py:2: SyntaxWarning: invalid escape sequence '\\d'" in first_output
    assert result.cases[1].stdout == ""


@NEEDS_NODE
async def test_typescript_runs_enums_and_parameter_properties() -> None:
    source = """
        enum Offset {
          None = 0,
        }

        class Adder {
          constructor(private readonly base: number) {}

          plus(value: number): number {
            return this.base + value + Offset.None;
          }
        }

        export function add(a: number, b: number): number {
          return new Adder(a).plus(b);
        }
        """
    result = await run("add", TS, source)
    assert result.outcome is RunOutcome.PASSED, result


# --- problem content errors ----------------------------------------------------------------


async def test_pending_cases_report_no_test_cases() -> None:
    result = await run("pending", PY, "")
    assert (result.outcome, result.message, result.cases) == (
        RunOutcome.ERROR,
        "No test cases yet",
        (),
    )


FUNCTION_META = 'kind = "function"\nentry = "add"\n'
DESIGN_CASE = '[{{"ops": {ops}, "args": {args}, "expected": [null, 1]}}]'
# (fixture, file to replace, its new content or None to delete it, expected message)
CONTENT_ERRORS = [
    ("add", "cases.json", None, "No test cases yet"),
    ("add", "cases.json", "[]", "No test cases yet"),
    ("add", "cases.json", "{", "cases.json: Expecting property name"),
    ("add", "cases.json", '{"args": [1, 2]}', "cases.json must hold a JSON array"),
    (
        "add",
        "cases.json",
        '[{"args": [1, 2]}]',
        "case 1 must be an object with an 'expected'",
    ),
    (
        "add",
        "cases.json",
        '[{"args": [1], "expected": 1}]',
        "'args' must be an array of 2 values",
    ),
    (
        "add",
        "cases.json",
        '[{"name": 7, "args": [1, 2], "expected": 3}]',
        "case 1 name must be",
    ),
    (
        "add",
        "cases.json",
        '[{"args": [1, 2], "expected": 3, "compare": "?"}]',
        "compare must be",
    ),
    ("add", "meta.toml", None, "meta.toml not found"),
    ("add", "meta.toml", FUNCTION_META + "params = [\n", "meta.toml: "),
    (
        "add",
        "meta.toml",
        'kind = "graph"\n',
        "meta.toml kind must be one of: function, ",
    ),
    (
        "add",
        "meta.toml",
        'kind = "function"\n',
        "meta.toml entry must be a non-empty string",
    ),
    ("add", "meta.toml", FUNCTION_META + 'params = ["int"]\n', "{ name, type } tables"),
    (
        "add",
        "meta.toml",
        FUNCTION_META + "params = []\n",
        "meta.toml returns must be a non-empty",
    ),
    (
        "add",
        "meta.toml",
        FUNCTION_META + 'output = "stdout"\n',
        "meta.toml output must be one of",
    ),
    (
        "guess_number",
        "cases.json",
        '[{"args": [10], "expected": 6}]',
        "needs an integer 'pick'",
    ),
    (
        "recent_counter",
        "cases.json",
        DESIGN_CASE.format(ops='"ping"', args="[]"),
        "'ops' must be a non-empty array of method names",
    ),
    (
        "recent_counter",
        "cases.json",
        DESIGN_CASE.format(ops='["Counter", "ping"]', args="[[], [1]]"),
        "ops[0] must be the constructor 'RecentCounter'",
    ),
    (
        "recent_counter",
        "cases.json",
        DESIGN_CASE.format(ops='["RecentCounter", "ping"]', args="[[]]"),
        "'args' must hold one array per op",
    ),
    (
        "recent_counter",
        "cases.json",
        DESIGN_CASE.format(ops='["RecentCounter", "ping"]', args="[[], 1]"),
        "each entry of 'args' must be an array",
    ),
]


@pytest.mark.parametrize(("problem", "file", "content", "message"), CONTENT_ERRORS)
async def test_problem_content_errors(
    problem: str, file: str, content: str | None, message: str, tmp_path: Path
) -> None:
    problem_dir = copy_fixture(tmp_path, problem)
    if content is None:
        (problem_dir / file).unlink()
    else:
        (problem_dir / file).write_text(content)
    result = await run(problem_dir, PY, "")
    assert result.outcome is RunOutcome.ERROR
    assert message in result.message
    assert result.cases == ()


@pytest.mark.parametrize("file", ["meta.toml", "cases.json"])
async def test_unreadable_problem_files_are_errors(file: str, tmp_path: Path) -> None:
    problem_dir = copy_fixture(tmp_path, "add")
    (problem_dir / file).unlink()
    (problem_dir / file).mkdir()
    result = await run(problem_dir, PY, "")
    assert result.outcome is RunOutcome.ERROR
    assert result.message.startswith(f"{file}: [Errno 21] Is a directory")


@pytest.mark.parametrize("problem", KIND_FIXTURES)
def test_harness_job_never_contains_expected_values(problem: str) -> None:
    job = load_problem(FIXTURES / problem).job()
    assert all(set(case) <= {"args", "ops", "pick"} for case in job["cases"])


# --- finding node --------------------------------------------------------------------------


def executable(path: Path, script: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script)
    path.chmod(0o755)
    return path


def fake_node(
    directory: Path, version: str, *, rejects_transform: bool = False
) -> Path:
    """An executable that answers --version like node, optionally rejecting the TS flag."""
    flag = "--experimental-transform-types"
    reject = f'case "$*" in *{flag}*) exit 9 ;; esac\n' if rejects_transform else ""
    return executable(directory / "node", f"#!/bin/sh\n{reject}echo v{version}\n")


@pytest.fixture
def no_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An environment without any node: no LEET75_NODE, empty PATH dir, fresh HOME."""
    monkeypatch.delenv("LEET75_NODE", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "path"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return tmp_path


def nvm_dir(root: Path, version: str) -> Path:
    return root / "home" / ".nvm" / "versions" / "node" / f"v{version}" / "bin"


def test_find_node_prefers_the_env_var(
    no_node: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chosen = fake_node(no_node / "custom", "24.1.0")
    fake_node(no_node / "path", "24.2.0")
    fake_node(nvm_dir(no_node, "25.0.0"), "25.0.0")
    monkeypatch.setenv("LEET75_NODE", str(chosen))
    assert find_node() == chosen


def test_find_node_uses_path_before_nvm(no_node: Path) -> None:
    on_path = fake_node(no_node / "path", "23.6.0")
    fake_node(nvm_dir(no_node, "25.0.0"), "25.0.0")
    assert find_node() == on_path


def test_find_node_skips_old_nodes_and_picks_the_newest_nvm(
    no_node: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LEET75_NODE", str(fake_node(no_node / "custom", "22.12.0")))
    fake_node(no_node / "path", "22.21.0")
    for version in ("22.21.0", "24.18.0", "24.19.0", "24.9.0"):
        fake_node(nvm_dir(no_node, version), version)
    nvm_dir(no_node, "26.0.0").mkdir(parents=True)  # a broken install without a binary
    assert find_node() == nvm_dir(no_node, "24.19.0") / "node"


def test_find_node_skips_candidates_that_cannot_report_a_version(
    no_node: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unstartable = executable(no_node / "custom" / "node", "#!/no/such/interpreter\n")
    monkeypatch.setenv("LEET75_NODE", str(unstartable))
    executable(no_node / "path" / "node", "#!/bin/sh\nexit 1\n")
    fake_node(nvm_dir(no_node, "24.19.0"), "24.19.0")
    assert find_node() == nvm_dir(no_node, "24.19.0") / "node"


def test_find_node_rejects_versions_below_23_6(no_node: Path) -> None:
    fake_node(no_node / "path", "23.5.9")
    fake_node(nvm_dir(no_node, "22.21.0"), "22.21.0")
    fake_node(nvm_dir(no_node, "23.5.0"), "23.5.0")
    assert find_node() is None


async def test_interpreter_dying_before_the_harness_reports_its_output(
    no_node: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = (
        '#!/bin/sh\ncase "$*" in *--version*) echo v24.0.0 ;;\n'
        '*) echo "node: bad option: --frobnicate" >&2; exit 9 ;; esac\n'
    )
    monkeypatch.setenv(
        "LEET75_NODE", str(executable(no_node / "custom" / "node", script))
    )
    result = await run("add", TS)
    assert result.outcome is RunOutcome.ERROR
    assert result.message == (
        "The solution process exited with code 9 after 0 of 3 cases:\n"
        "node: bad option: --frobnicate"
    )


async def test_typescript_is_unavailable_without_node(no_node: Path) -> None:
    result = await run("add", TS)
    assert result.outcome is RunOutcome.UNAVAILABLE
    assert "Node.js >= 23.6" in result.message
    assert result.cases == ()


def test_node_command_adds_transform_types_only_when_accepted(tmp_path: Path) -> None:
    modern = fake_node(tmp_path / "modern", "24.19.0")
    strict = fake_node(tmp_path / "strict", "30.0.0", rejects_transform=True)
    assert node_command(modern) == [
        str(modern),
        "--disable-warning=ExperimentalWarning",
        "--experimental-transform-types",
    ]
    assert node_command(strict) == [
        str(strict),
        "--disable-warning=ExperimentalWarning",
    ]
