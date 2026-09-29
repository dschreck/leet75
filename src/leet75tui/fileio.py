"""Crash-safe file writes."""

import os
import tempfile
from pathlib import Path

FILE_MODE = 0o644


def write_text_atomic(path: Path, text: str) -> None:
    """Write UTF-8 ``text`` to ``path`` via a temp file and ``os.replace``.

    Readers see either the old or the new content, never a partial write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, FILE_MODE)
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
