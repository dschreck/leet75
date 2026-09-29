"""Locate a Node.js that runs TypeScript by type stripping, and the flags to start it with."""

import os
import re
import shutil
import subprocess
from pathlib import Path

NODE_ENV_VAR = "LEET75_NODE"
MIN_NODE_VERSION = (23, 6, 0)  # first release that strips TypeScript types by default
NVM_VERSIONS_DIR = Path(".nvm") / "versions" / "node"
VERSION_PATTERN = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")
PROBE_TIMEOUT_S = 5.0
BASE_FLAGS = ("--disable-warning=ExperimentalWarning",)
# Also runs TypeScript that needs code generation: enums, namespaces, parameter properties.
TRANSFORM_TYPES_FLAG = "--experimental-transform-types"

Version = tuple[int, ...]


def find_node() -> Path | None:
    """LEET75_NODE env var -> `node` on PATH -> newest ~/.nvm/versions/node/v*/bin/node.

    The first candidate that is Node >= 23.6 wins; returns None when there is none.
    """
    for candidate in _explicit_candidates():
        version = _reported_version(candidate)
        if version is not None and version >= MIN_NODE_VERSION:
            return candidate
    return _newest_nvm_node()


def node_command(node: Path) -> list[str]:
    """`node` plus the flags this build accepts (--experimental-transform-types if known)."""
    flags = [*BASE_FLAGS, TRANSFORM_TYPES_FLAG]
    if not _accepts_flags(node, flags):
        flags = list(BASE_FLAGS)
    return [str(node), *flags]


def _explicit_candidates() -> list[Path]:
    names = [os.environ.get(NODE_ENV_VAR, ""), "node"]
    found = (shutil.which(name) for name in names if name)
    return [Path(path) for path in found if path is not None]


def _newest_nvm_node() -> Path | None:
    candidates: list[tuple[Version, Path]] = []
    for directory in (Path.home() / NVM_VERSIONS_DIR).glob("v*"):
        version = _parse_version(directory.name)
        node = directory / "bin" / "node"
        if (
            version is not None
            and version >= MIN_NODE_VERSION
            and os.access(node, os.X_OK)
        ):
            candidates.append((version, node))
    return (
        max(candidates, key=lambda candidate: candidate[0])[1] if candidates else None
    )


def _parse_version(text: str) -> Version | None:
    match = VERSION_PATTERN.match(text)
    return tuple(int(part) for part in match.groups()) if match else None


def _run_quietly(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _reported_version(node: Path) -> Version | None:
    completed = _run_quietly([str(node), "--version"])
    if completed is None or completed.returncode != 0:
        return None
    return _parse_version(completed.stdout.strip())


def _accepts_flags(node: Path, flags: list[str]) -> bool:
    """Node rejects unknown flags with exit code 9 even alongside --version (~3 ms)."""
    completed = _run_quietly([str(node), *flags, "--version"])
    return completed is not None and completed.returncode == 0
