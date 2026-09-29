"""Services shared by the screens: catalog, workbook, progress and the solution runner."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from leet75tui.catalog import Problem
from leet75tui.languages import Language
from leet75tui.progress import ProgressStore
from leet75tui.runner import RunResult
from leet75tui.workbook import Workbook

RunSolution = Callable[[Path, Language, str], Awaitable[RunResult]]
FindNode = Callable[[], Path | None]


class NodeProbe:
    """Remembers whether a usable Node exists; the lookup spawns ``node`` so it runs once."""

    def __init__(self, find_node: FindNode) -> None:
        self._find_node = find_node
        self._available: bool | None = None

    async def available(self) -> bool:
        """True when a Node able to run TypeScript was found (probed off the event loop)."""
        if self._available is None:
            self._available = await asyncio.to_thread(self._find_node) is not None
        return self._available


@dataclass(frozen=True, slots=True)
class AppContext:
    """Everything a screen needs, injected so tests can swap the runner."""

    catalog: tuple[Problem, ...]
    workbook: Workbook
    progress: ProgressStore
    run_solution: RunSolution
    node: NodeProbe
