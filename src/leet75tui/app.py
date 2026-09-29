"""The leet75tui Textual application and its console entry point."""

import sys
from pathlib import Path
from typing import Any

from textual.app import App
from textual.screen import Screen

from leet75tui.catalog import CatalogError, load_catalog
from leet75tui.context import AppContext, FindNode, NodeProbe, RunSolution
from leet75tui.paths import RepoNotFoundError, find_repo_root
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
        *,
        runner: RunSolution = run_solution,
        node_finder: FindNode = find_node,
    ) -> None:
        """Load the catalog and progress of the repo at ``root``; raises on bad content."""
        super().__init__()
        workbook = Workbook.in_repo(root)
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


def main() -> None:
    """Console entry point (``leet75tui``)."""
    try:
        app = Leet75App(find_repo_root())
    except (RepoNotFoundError, CatalogError, ProgressError) as error:
        sys.exit(f"leet75tui: {error}")
    app.run()
