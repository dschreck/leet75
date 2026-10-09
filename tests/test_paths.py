"""Bundled content location, data home and workspace directories."""

from pathlib import Path

import pytest

import leet75tui
from leet75tui.paths import (
    PROBLEMS_DIRNAME,
    WorkspaceNameError,
    content_root,
    data_home,
    workspace_dir,
)


def test_content_root_is_the_package_and_ships_the_problems() -> None:
    root = content_root()

    assert root == Path(leet75tui.__file__).parent
    assert len(list((root / PROBLEMS_DIRNAME).glob("*/meta.toml"))) == 75


def test_data_home_uses_xdg_data_home(tmp_path: Path) -> None:
    assert data_home({"XDG_DATA_HOME": str(tmp_path)}) == tmp_path / "leet75tui"


@pytest.mark.parametrize("value", [None, "", "relative/dir"])
def test_data_home_falls_back_to_local_share(
    value: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    environ = {} if value is None else {"XDG_DATA_HOME": value}

    assert data_home(environ) == tmp_path / ".local" / "share" / "leet75tui"


@pytest.mark.parametrize("name", ["default", "pass-2", "2026.10_retry", "a" * 64])
def test_workspace_dir_is_under_workspaces(name: str, tmp_path: Path) -> None:
    path = workspace_dir(name, {"XDG_DATA_HOME": str(tmp_path)})

    assert path == tmp_path / "leet75tui" / "workspaces" / name


@pytest.mark.parametrize("name", ["", "..", ".hidden", "-flag", "a/b", "../x", "a b", "a" * 65])
def test_workspace_dir_rejects_names_that_are_not_plain_directories(name: str) -> None:
    with pytest.raises(WorkspaceNameError, match="invalid workspace name"):
        workspace_dir(name, {})
