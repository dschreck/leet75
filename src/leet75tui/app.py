"""The leet75tui Textual application and its console entry point."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from textual.app import App
from textual.screen import Screen

from leet75tui.catalog import CatalogError, load_catalog
from leet75tui.context import AppContext, FindNode, NodeProbe, RunSolution
from leet75tui.paths import (
    DEFAULT_WORKSPACE,
    WORKSPACES_DIRNAME,
    WorkspaceNameError,
    content_root,
    data_home,
    workspace_dir,
)
from leet75tui.progress import ProgressError, ProgressStore
from leet75tui.runner import find_node, run_solution
from leet75tui.screens.catalog_screen import CatalogScreen
from leet75tui.workbook import Workbook


class Leet75App(App[None]):
    """Catalog of the LeetCode 75 problems, each opening into an editor + test runner."""

    TITLE = "leet75tui"
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False

    def __init__(
        self,
        root: Path,
        workspace: Path,
        *,
        runner: RunSolution = run_solution,
        node_finder: FindNode = find_node,
    ) -> None:
        """Load the problems under ``root`` and the progress saved in ``workspace``.

        Raises on bad content or a corrupt progress file.
        """
        super().__init__()
        workbook = Workbook(workspace)
        self.sub_title = f"workspace: {workspace.name}"
        self.context = AppContext(
            catalog=load_catalog(root),
            workbook=workbook,
            progress=ProgressStore.load(workbook.progress_path),
            run_solution=runner,
            node=NodeProbe(node_finder),
        )

    def get_default_screen(self) -> Screen[Any]:
        """The catalog is the bottom of the screen stack."""
        return CatalogScreen(self.context)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Command-line options; ``argv`` defaults to ``sys.argv[1:]``."""
    parser = argparse.ArgumentParser(
        prog="leet75tui", description="LeetCode 75 workbook: catalog, code editor and test runner."
    )
    parser.add_argument(
        "-w",
        "--workspace",
        default=DEFAULT_WORKSPACE,
        metavar="NAME",
        help=(
            f"keep solutions and progress in {data_home() / WORKSPACES_DIRNAME}/NAME; "
            "a new name starts from a fresh slate (default: %(default)s)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Console entry point (``leet75tui``)."""
    args = parse_args(argv)
    try:
        app = Leet75App(content_root(), workspace_dir(args.workspace))
    except (WorkspaceNameError, CatalogError, ProgressError) as error:
        sys.exit(f"leet75tui: {error}")
    app.run()
