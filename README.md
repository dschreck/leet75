# leet75tui

A terminal workbook for the [LeetCode 75](https://leetcode.com/studyplan/leetcode-75/) study plan. It has
a problem catalog, a code editor, and a test runner for TypeScript and Python.

## Requirements

- Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/)
- Node.js ≥ 23.6 for TypeScript runs. Node runs `.ts` files directly using its built-in type stripping, so there is no build step.

## Install and run

```bash
uv tool install -e .   # puts `leet75tui` on PATH; edits to the repo take effect immediately
leet75tui
```

## Keys

**Catalog**

| Key | Action |
|---|---|
| `↑` `↓` `PgUp` `PgDn` `Home` `End` | Move |
| `/` | Filter by title or category (case-insensitive) |
| `Esc` | Clear the filter |
| `Enter` | Open the problem |
| `q` | Quit |

**Exercise**

| Key | Action |
|---|---|
| `Ctrl+Enter` / `F5` / `Ctrl+R` | Run the tests |
| `F2` / `F3` | Problem tab / Output tab |
| `Ctrl+T` | Switch between TypeScript and Python |
| `Ctrl+Space` | Autocomplete |
| `Ctrl+Shift+O` / `F4` | Open the solution in `$EDITOR` |
| `Esc` | Back to the catalog |

The editor autosaves. The status column shows `✓` solved, `~` attempted, `·` unsolved. A problem
becomes solved the first time every case passes.

## Layout

| Path | Contents |
|---|---|
| `problems/<NNN_slug>/` | `problem.md` (statement), `meta.toml` (metadata and call signature), `cases.json` (tests), `starter.ts`, `starter.py` |
| `workbook/` | Your solutions (`<NNN_slug>.ts` / `.py`) and `progress.json` |
| `src/leet75tui/` | The app: screens, editor widgets, and the subprocess runner with its Python and Node harnesses |

### Adding or editing a problem

`tests/test_content.py` checks every problem against this contract.

- `meta.toml`:
  - Required: `id`, `title`, `difficulty`, `category`, `order` (1–75), `url`, `kind`, `entry`, `cases` (`"ready"` or `"pending"`).
  - Signature: `params = [{ name, type }]` and `returns`, for every kind except `design`.
  - Optional: `compare` (`exact`, `unordered`, `unordered-inner`, `unordered-nested`, `float`) and `output` (`return`, `arg0`, `arg0-prefix`).
- `kind`:
  - `function`: the runner calls `entry(*args)`.
  - `linked-list` / `tree`: values use LeetCode's array form, and the harness builds the nodes.
  - `design`: cases are `{ops, args, expected}`, the same sequence format LeetCode uses.
  - `interactive`: cases carry a `pick` that the harness's `guess()` answers from.
- `cases.json`: a list of `{"name", "args", "expected"}`.
- Starters follow LeetCode's templates. Python uses `class Solution`; TypeScript uses `export function <entry>`.

## Environment

| Variable | Effect |
|---|---|
| `LEET75_HOME` | Repo root. By default the app walks up from the installed package to find `problems/`. |
| `LEET75_NODE` | Node binary. Otherwise the runner tries `node` on PATH, then the newest `~/.nvm/versions/node/*/bin/node`. |

## Development

```bash
uv sync
uv run pytest --cov=src
uv run mypy --strict src/
uv run ruff check .
```

The plan and current status are in [`leet75tui.md`](leet75tui.md).
