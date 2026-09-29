"""Locate the leet75 repository (the directory that holds ``problems/``)."""

import os
from collections.abc import Mapping
from pathlib import Path

HOME_ENV_VAR = "LEET75_HOME"
PROBLEMS_DIRNAME = "problems"


class RepoNotFoundError(Exception):
    """Raised when no directory containing ``problems/`` can be found."""


def find_repo_root(environ: Mapping[str, str] = os.environ, start: Path = Path(__file__)) -> Path:
    """Return the repository root.

    ``$LEET75_HOME`` wins when set; otherwise walk up from ``start`` (this package, so an
    editable install works from any working directory) to the first directory that
    contains ``problems/``.
    """
    home = environ.get(HOME_ENV_VAR)
    if home:
        root = Path(home).expanduser().resolve()
        if not (root / PROBLEMS_DIRNAME).is_dir():
            raise RepoNotFoundError(f"{HOME_ENV_VAR}={home} has no {PROBLEMS_DIRNAME}/ directory")
        return root
    for directory in start.resolve().parents:
        if (directory / PROBLEMS_DIRNAME).is_dir():
            return directory
    raise RepoNotFoundError(
        f"no directory containing {PROBLEMS_DIRNAME}/ above {start}; "
        f"set {HOME_ENV_VAR} or install with `uv tool install -e .`"
    )
