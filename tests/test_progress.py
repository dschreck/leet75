"""Progress store: parsing, sticky SOLVED, atomic and stable file format."""

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from leet75tui.fileio import write_text_atomic
from leet75tui.progress import ProblemProgress, ProgressError, ProgressStore, Status

SLUG = "104_maximum-depth-of-binary-tree"
RUN_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def write_progress(path: Path, problems: object, version: int = 1) -> None:
    path.write_text(json.dumps({"version": version, "problems": problems}), encoding="utf-8")


def test_missing_file_means_unsolved(tmp_path: Path) -> None:
    store = ProgressStore.load(tmp_path / "progress.json")

    assert store.status(SLUG) is Status.UNSOLVED
    assert store.get(SLUG) == ProblemProgress()
    assert not (tmp_path / "progress.json").exists()


def test_load_reads_entries(app_repo: Path) -> None:
    store = ProgressStore.load(app_repo / "workbook" / "progress.json")
    progress = store.get("1768_merge-strings-alternately")

    assert progress.status is Status.SOLVED
    assert progress.last_run_at == datetime(2026, 9, 1, 10, 0, tzinfo=UTC)
    assert store.solved_count(["1768_merge-strings-alternately", SLUG]) == 1


def test_full_pass_solves_and_writes_stable_format(tmp_path: Path) -> None:
    path = tmp_path / "workbook" / "progress.json"
    store = ProgressStore.load(path)

    progress = store.record_run(SLUG, all_passed=True, at=RUN_AT)

    assert progress == ProblemProgress(Status.SOLVED, RUN_AT)
    assert path.read_text(encoding="utf-8") == (
        "{\n"
        '  "problems": {\n'
        f'    "{SLUG}": {{\n'
        '      "lastRunAt": "2026-09-29T12:00:00+00:00",\n'
        '      "status": "SOLVED"\n'
        "    }\n"
        "  },\n"
        '  "version": 1\n'
        "}\n"
    )


def test_failed_run_marks_attempted(tmp_path: Path) -> None:
    store = ProgressStore.load(tmp_path / "progress.json")

    assert store.record_run(SLUG, all_passed=False, at=RUN_AT).status is Status.ATTEMPTED


def test_solved_is_sticky(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    store = ProgressStore.load(path)
    store.record_run(SLUG, all_passed=True, at=RUN_AT)
    later = RUN_AT + timedelta(hours=1)

    progress = store.record_run(SLUG, all_passed=False, at=later)

    assert progress == ProblemProgress(Status.SOLVED, later)
    assert ProgressStore.load(path).get(SLUG) == progress


def test_record_run_keeps_other_entries_and_normalizes_to_utc(app_repo: Path) -> None:
    path = app_repo / "workbook" / "progress.json"
    store = ProgressStore.load(path)
    local = datetime(2026, 9, 29, 14, 0, tzinfo=timezone(timedelta(hours=2)))

    store.record_run(SLUG, all_passed=False, at=local)

    problems = json.loads(path.read_text(encoding="utf-8"))["problems"]
    assert problems["1768_merge-strings-alternately"]["status"] == "SOLVED"
    assert problems[SLUG] == {"status": "ATTEMPTED", "lastRunAt": "2026-09-29T12:00:00+00:00"}


def test_record_run_defaults_to_now(tmp_path: Path) -> None:
    store = ProgressStore.load(tmp_path / "progress.json")
    before = datetime.now(UTC)

    last_run_at = store.record_run(SLUG, all_passed=True).last_run_at

    assert last_run_at is not None
    assert before <= last_run_at <= datetime.now(UTC)


def test_missing_last_run_at_and_status_default(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    write_progress(path, {SLUG: {}})

    assert ProgressStore.load(path).get(SLUG) == ProblemProgress()


def test_entries_without_run_time_are_written_as_null(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    write_progress(path, {"seeded": {"status": "SOLVED", "lastRunAt": None}})

    ProgressStore.load(path).record_run(SLUG, all_passed=False, at=RUN_AT)

    problems = json.loads(path.read_text(encoding="utf-8"))["problems"]
    assert problems["seeded"] == {"status": "SOLVED", "lastRunAt": None}


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{not json", "invalid JSON"),
        ('{"version": 2, "problems": {}}', 'expected an object with "version": 1'),
        ('{"version": 1, "problems": []}', '"problems" must be an object'),
        ('{"version": 1, "problems": {"a": 1}}', "a: entry must be an object"),
        ('{"version": 1, "problems": {"a": {"status": "DONE"}}}', "a: unknown status 'DONE'"),
        ('{"version": 1, "problems": {"a": {"lastRunAt": "yesterday"}}}', "is not ISO-8601"),
        ('{"version": 1, "problems": {"a": {"lastRunAt": 5}}}', "is not ISO-8601"),
    ],
)
def test_invalid_file_names_the_file(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "progress.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ProgressError) as error:
        ProgressStore.load(path)

    assert str(path) in str(error.value)
    assert message in str(error.value)


def test_failed_write_leaves_status_unchanged(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("", encoding="utf-8")
    store = ProgressStore(blocker / "progress.json", {})

    with pytest.raises(OSError):
        store.record_run(SLUG, all_passed=True, at=RUN_AT)

    assert store.status(SLUG) is Status.UNSOLVED


def test_unreadable_file_raises_progress_error(tmp_path: Path) -> None:
    (tmp_path / "progress.json").mkdir()

    with pytest.raises(ProgressError, match=r"progress\.json"):
        ProgressStore.load(tmp_path / "progress.json")


def test_atomic_write_replaces_without_leftovers(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "file.txt"
    write_text_atomic(path, "one\n")

    write_text_atomic(path, "two\n")

    assert path.read_text(encoding="utf-8") == "two\n"
    assert [entry.name for entry in path.parent.iterdir()] == ["file.txt"]
    assert path.stat().st_mode & 0o777 == 0o644


def test_atomic_write_cleans_up_on_failure(tmp_path: Path) -> None:
    target = tmp_path / "dir-in-the-way"
    target.mkdir()
    (target / "child").write_text("x", encoding="utf-8")

    with pytest.raises(OSError):
        write_text_atomic(target, "text")

    assert sorted(entry.name for entry in tmp_path.iterdir()) == ["dir-in-the-way"]
