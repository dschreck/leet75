"""Solve status per problem, persisted in ``workbook/progress.json``."""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from leet75tui.fileio import write_text_atomic

PROGRESS_FILENAME = "progress.json"
PROGRESS_VERSION = 1


class Status(StrEnum):
    """Solve status of a problem; a problem without an entry is UNSOLVED."""

    UNSOLVED = "UNSOLVED"
    ATTEMPTED = "ATTEMPTED"
    SOLVED = "SOLVED"


class ProgressError(Exception):
    """Raised when the progress file cannot be read; the message names the file."""


@dataclass(frozen=True, slots=True)
class ProblemProgress:
    """Status of one problem and when its tests last ran."""

    status: Status = Status.UNSOLVED
    last_run_at: datetime | None = None

    def after_run(self, *, all_passed: bool, at: datetime) -> "ProblemProgress":
        """Progress after a test run: a full pass solves it, and SOLVED is sticky."""
        solved = all_passed or self.status is Status.SOLVED
        return ProblemProgress(Status.SOLVED if solved else Status.ATTEMPTED, at)


class ProgressStore:
    """In-memory progress backed by a JSON file that is rewritten atomically on change."""

    def __init__(self, path: Path, entries: dict[str, ProblemProgress]) -> None:
        self.path = path
        self._entries = entries

    @classmethod
    def load(cls, path: Path) -> "ProgressStore":
        """Load ``path``; a missing file means nothing has been attempted yet."""
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return cls(path, {})
        except (OSError, UnicodeDecodeError) as error:
            raise ProgressError(f"{path}: {error}") from error
        return cls(path, _parse(path, text))

    def get(self, slug: str) -> ProblemProgress:
        """Progress of ``slug`` (UNSOLVED when it has no entry)."""
        return self._entries.get(slug, ProblemProgress())

    def status(self, slug: str) -> Status:
        """Status of ``slug``."""
        return self.get(slug).status

    def solved_count(self, slugs: Iterable[str]) -> int:
        """How many of ``slugs`` are SOLVED."""
        return sum(1 for slug in slugs if self.status(slug) is Status.SOLVED)

    def record_run(
        self, slug: str, *, all_passed: bool, at: datetime | None = None
    ) -> ProblemProgress:
        """Record a test run of ``slug`` and persist the file (memory changes only on success)."""
        progress = self.get(slug).after_run(all_passed=all_passed, at=at or datetime.now(UTC))
        entries = {**self._entries, slug: progress}
        write_text_atomic(self.path, _serialize(entries))
        self._entries = entries
        return progress


def _parse(path: Path, text: str) -> dict[str, ProblemProgress]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ProgressError(f"{path}: invalid JSON: {error}") from error
    if not isinstance(data, dict) or data.get("version") != PROGRESS_VERSION:
        raise ProgressError(f'{path}: expected an object with "version": {PROGRESS_VERSION}')
    problems = data.get("problems", {})
    if not isinstance(problems, dict):
        raise ProgressError(f'{path}: "problems" must be an object')
    return {slug: _parse_entry(path, slug, entry) for slug, entry in problems.items()}


def _parse_entry(path: Path, slug: str, entry: Any) -> ProblemProgress:
    if not isinstance(entry, dict):
        raise ProgressError(f"{path}: {slug}: entry must be an object")
    try:
        status = Status(entry.get("status", Status.UNSOLVED))
    except ValueError:
        raise ProgressError(f"{path}: {slug}: unknown status {entry.get('status')!r}") from None
    return ProblemProgress(status, _parse_time(path, slug, entry.get("lastRunAt")))


def _parse_time(path: Path, slug: str, value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ProgressError(f"{path}: {slug}: lastRunAt {value!r} is not ISO-8601") from None


def _serialize(entries: dict[str, ProblemProgress]) -> str:
    problems = {
        slug: {"status": progress.status.value, "lastRunAt": _format_time(progress.last_run_at)}
        for slug, progress in entries.items()
    }
    data = {"version": PROGRESS_VERSION, "problems": problems}
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _format_time(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(UTC).isoformat(timespec="seconds")
