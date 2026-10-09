"""Where the bundled problems live and where each workspace keeps its solutions."""

import os
import re
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

PROBLEMS_DIRNAME = "problems"
APP_DIRNAME = "leet75tui"
WORKSPACES_DIRNAME = "workspaces"
DEFAULT_WORKSPACE = "default"
# Starts alphanumeric and has no separators, so a name never escapes the workspaces directory.
WORKSPACE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


class WorkspaceNameError(ValueError):
    """Raised for a workspace name that is not a plain directory name."""


def content_root() -> Path:
    """The installed package directory; it ships ``problems/`` with the starters."""
    return Path(str(files("leet75tui")))


def data_home(environ: Mapping[str, str] = os.environ) -> Path:
    """``$XDG_DATA_HOME/leet75tui``, or ``~/.local/share/leet75tui`` when unset or relative."""
    base = Path(environ.get("XDG_DATA_HOME", ""))
    if not base.is_absolute():
        base = Path.home() / ".local" / "share"
    return base / APP_DIRNAME


def workspace_dir(name: str, environ: Mapping[str, str] = os.environ) -> Path:
    """``<data home>/workspaces/<name>``; it is created on the first save, not here."""
    if not WORKSPACE_NAME.fullmatch(name):
        raise WorkspaceNameError(
            f"invalid workspace name {name!r}: use up to 64 letters, digits, '.', '_' or '-', "
            "starting with a letter or digit"
        )
    return data_home(environ) / WORKSPACES_DIRNAME / name
