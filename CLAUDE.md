# leet75tui

Terminal workbook for the LeetCode 75 study plan: a problem catalog, a code editor, and a test runner for
TypeScript and Python. Built with Python 3.12 and Textual 8.2 and run in Windows Terminal on WSL2.
The plan, the decisions behind it, and the current status are in `leet75tui.md`. Read its Status
section before starting work.

## Commands

```bash
uv sync                                    # install deps, including the dev group
uv run leet75tui [-w NAME]                 # launch the app on workspace NAME (default: default)
uv tool install -e .                       # put `leet75tui` on PATH (editable); `uv tool install .` to ship
uv run pytest --cov=src                    # ~800 tests, ~45 s
uv run mypy --strict src/
uv run ruff check .                        # config in pyproject.toml; content dirs are excluded
```

## Layout

| Path | What |
|---|---|
| `src/leet75tui/` | App: `screens/` (catalog, exercise), `widgets/` (editor, completion, run output), `runner/` (subprocess runner, `harness.py`, `harness.mjs`), `languages/` (TS tree-sitter registration) |
| `src/leet75tui/problems/<NNN_slug>/` | `problem.md`, `meta.toml`, `cases.json`, `starter.ts`, `starter.py`. This is package data shipped in the wheel, found via `paths.content_root()`; it is the source of truth and is edited by hand |
| `~/.local/share/leet75tui/workspaces/<name>/` | The user's solutions (`<slug>.ts` / `.py`) and `progress.json` (status `SOLVED` / `ATTEMPTED`), one folder per workspace (`$XDG_DATA_HOME` respected). This is user data outside the repo: never overwrite or reset it. Tests point `XDG_DATA_HOME` at a tmp dir |

Branch `main` still holds the pre-TUI layout (`NNN_slug/` folders with vitest tests). It was removed from `tui` after the content was migrated.

## Content contract

- `meta.toml`: `kind` is one of `function`, `linked-list`, `tree`, `design`, `interactive`. `entry`, `params`, `returns` and `compare` drive both harnesses.
- Starters follow LeetCode's templates on purpose. Python uses `class Solution` with `List[...]`/`Optional[...]`, and the harness injects `ListNode`/`TreeNode`. TS uses `export function <entry>`.
  Do not modernize or lint-fix them; `ruff check --fix .` rewrites all of them.
- Edit `src/leet75tui/problems/` directly. `tests/test_content.py` enforces the contract (summarized in `README.md`), including that every statement example appears as a case.

## Environment and keys

- `--workspace NAME` picks the workspace. Names must match `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`, so a name can never escape the workspaces folder. A new name is a fresh slate.
- `LEET75_NODE` overrides the node binary. Otherwise the runner tries PATH, then the newest `~/.nvm/versions/node/*/bin/node`, and needs Node ≥ 23.6 for type stripping. Node is not on PATH in non-interactive shells here; the nvm fallback covers it.
- Windows Terminal key facts (tested with `textual keys`, details in `leet75tui.md`):
  - Ctrl+Enter arrives as `ctrl+j`.
  - Alt+digit types characters like `¡`, so never bind Alt+digit.
  - WT swallows plain Ctrl+O; Ctrl+Shift+O arrives as `ctrl+o`.
  - New bindings should prefer F-keys, and screen bindings need `priority=True` to beat `TextArea`.

## Conventions

- Conventional commits (`feat:`, `fix:`, …) with no AI co-author trailer.
- Quality gates: ruff 0 errors, `mypy --strict src/` 0 errors, pytest coverage > 70%.
- `pyproject.toml` is protected by a local hook, so edits to it need explicit user approval.
- Known issue: `meta.toml` is parsed twice, in `catalog.py` and in `runner/problem.py`. Merge them before adding fields.
