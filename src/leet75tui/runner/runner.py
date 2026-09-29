"""Run a solution in a child process and collect its results.

Protocol: the runner writes ``job.json`` (call spec + case inputs, never expected values) and
the solution into a fresh temp dir, starts ``harness.py`` / ``harness.mjs`` on it in a new
session, and reads back ``results.jsonl``, one record per finished case. Comparing happens
here, in :mod:`leet75tui.runner.compare`, so both languages share one implementation.
"""

import asyncio
import contextlib
import json
import math
import os
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from leet75tui.languages import Language
from leet75tui.runner.models import CaseResult, RunOutcome, RunResult
from leet75tui.runner.node import find_node, node_command
from leet75tui.runner.problem import Problem, ProblemError, load_problem
from leet75tui.runner.results import ChildExit, read_records, summarize

__all__ = ["DEFAULT_TIMEOUT_S", "find_node", "run_solution"]

DEFAULT_TIMEOUT_S: float = 5.0
HARNESS_DIR = Path(__file__).resolve().parent
HARNESSES = {
    Language.TYPESCRIPT: HARNESS_DIR / "harness.mjs",
    Language.PYTHON: HARNESS_DIR / "harness.py",
}
SOURCE_FILES = {Language.TYPESCRIPT: "solution.mts", Language.PYTHON: "solution.py"}
SHOWN_TS_SOURCE = "solution.ts"
JOB_FILE = "job.json"
RESULTS_FILE = "results.jsonl"
RUN_DIR_PREFIX = "leet75tui-run-"
OUTPUT_CAP = 64 * 1024  # tail of the raw stdout+stderr kept for crash reports
EXIT_GRACE_S = 2.0  # for a SIGKILLed child to be reaped
PIPE_GRACE_S = 0.5  # for the pipes to reach EOF once the child is gone
# The child runs in its own session, so closing the terminal does not reach it; if the app
# dies mid-run, the kernel stops a spinning child after this much CPU time past the timeout.
CPU_LIMIT_MARGIN_S = 5
# NODE_OPTIONS could preload code or flags into the harness.
CHILD_ENV_DROP = frozenset({"NODE_OPTIONS"})
UNAVAILABLE_MESSAGES = {
    Language.TYPESCRIPT: (
        "TypeScript runs need Node.js >= 23.6: set LEET75_NODE, put node on PATH, "
        "or install one with nvm"
    ),
    Language.PYTHON: "No Python interpreter found to run the solution",
}


class _ChildProtocol(asyncio.SubprocessProtocol):
    """Keeps the last OUTPUT_CAP bytes the child writes and signals exit and pipe EOF."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.output = bytearray()
        self.exited: asyncio.Future[None] = loop.create_future()
        self.closed: asyncio.Future[None] = loop.create_future()

    def pipe_data_received(self, fd: int, data: bytes | bytearray) -> None:
        self.output += data
        del self.output[:-OUTPUT_CAP]

    def process_exited(self) -> None:
        self.exited.set_result(None)

    def connection_lost(self, exc: Exception | None) -> None:
        self.closed.set_result(None)


async def run_solution(
    problem_dir: Path,
    language: Language,
    source: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> RunResult:
    """Run `source` against problem_dir/cases.json; meta.toml supplies the call spec.

    Never raises for user-code problems: returns ERROR, TIMED_OUT or UNAVAILABLE instead.
    Kills the child's whole process group on timeout and when the awaiting task is cancelled.
    """
    started = time.perf_counter()
    try:
        problem = await asyncio.to_thread(load_problem, problem_dir)
    except ProblemError as exc:
        return _result(started, RunOutcome.ERROR, str(exc))
    interpreter = await _interpreter(language)
    if interpreter is None:
        return _result(started, RunOutcome.UNAVAILABLE, UNAVAILABLE_MESSAGES[language])
    try:
        run_dir = Path(tempfile.mkdtemp(prefix=RUN_DIR_PREFIX))
    except OSError as exc:
        return _result(
            started, RunOutcome.ERROR, f"Could not create a run directory: {exc}"
        )
    try:
        _write_inputs(run_dir, problem, language, source)
        command = [*interpreter, str(HARNESSES[language]), str(run_dir)]
        child = await _run_child(command, run_dir, timeout_s)
        results = run_dir / RESULTS_FILE
        records = await asyncio.to_thread(read_records, results, len(problem.cases))
    except OSError as exc:
        return _result(started, RunOutcome.ERROR, f"Could not run the solution: {exc}")
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
    return _result(started, *summarize(problem, records, child))


def _result(
    started: float,
    outcome: RunOutcome,
    message: str,
    cases: tuple[CaseResult, ...] = (),
) -> RunResult:
    return RunResult(outcome, cases, message, (time.perf_counter() - started) * 1000)


async def _interpreter(language: Language) -> list[str] | None:
    if language is Language.PYTHON:
        return [sys.executable, "-I"] if sys.executable else None
    return await asyncio.to_thread(_node_interpreter)


def _node_interpreter() -> list[str] | None:
    node = find_node()
    return None if node is None else node_command(node)


def _write_inputs(
    run_dir: Path, problem: Problem, language: Language, source: str
) -> None:
    (run_dir / JOB_FILE).write_text(json.dumps(problem.job()), encoding="utf-8")
    (run_dir / SOURCE_FILES[language]).write_text(
        source, encoding="utf-8", errors="replace"
    )


async def _run_child(command: list[str], run_dir: Path, timeout_s: float) -> ChildExit:
    """Start the harness in its own session and wait up to `timeout_s` for it to exit."""
    loop = asyncio.get_running_loop()
    protocol = _ChildProtocol(loop)
    env = {key: value for key, value in os.environ.items() if key not in CHILD_ENV_DROP}
    transport, _ = await loop.subprocess_exec(
        lambda: protocol,
        *command,
        cwd=run_dir,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # the child leads a process group we can kill as a whole
    )
    _limit_cpu_time(transport.get_pid(), timeout_s)
    try:
        finished, _ = await asyncio.wait({protocol.exited}, timeout=timeout_s)
    finally:
        await _stop(transport, protocol)
    output = _without_run_dir(protocol.output.decode(errors="replace"), run_dir)
    return ChildExit(
        transport.get_returncode(), None if finished else timeout_s, output
    )


def _limit_cpu_time(pid: int, timeout_s: float) -> None:
    """Backstop for a child orphaned by an app crash; Linux only (prlimit)."""
    prlimit = getattr(resource, "prlimit", None)
    if prlimit is None:
        return
    with contextlib.suppress(OSError, ValueError, OverflowError):
        seconds = math.ceil(timeout_s) + CPU_LIMIT_MARGIN_S
        prlimit(pid, resource.RLIMIT_CPU, (seconds, seconds + 1))


async def _stop(
    transport: asyncio.SubprocessTransport, protocol: _ChildProtocol
) -> None:
    """Kill the child's process group (stragglers too), reap the child, close the pipes."""
    try:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(transport.get_pid(), signal.SIGKILL)
        await asyncio.wait({protocol.exited}, timeout=EXIT_GRACE_S)
        await asyncio.wait({protocol.closed}, timeout=PIPE_GRACE_S)
    finally:
        transport.close()


def _without_run_dir(text: str, run_dir: Path) -> str:
    text = text.replace(f"{run_dir.as_uri()}/", "").replace(f"{run_dir}{os.sep}", "")
    return text.replace(SOURCE_FILES[Language.TYPESCRIPT], SHOWN_TS_SOURCE)
