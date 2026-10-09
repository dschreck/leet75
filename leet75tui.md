# Implementation Plan: `leet75tui` — LeetCode 75 workbook TUI

## Context

The repo today is 75 `NNN_slug/` folders (`README.md` + `solution.ts` + `solution.test.ts`), a vitest
setup, and `scripts/update-readme.sh`. Progress lives as `[x]` in the root README table (13 solved).

Goal: replace it with a terminal app, `leet75tui`, that acts as workbook + practice tool + study guide,
run locally in Windows Terminal on WSL2. MVP flow:

1. `leet75tui` → **Catalog**: table (name, difficulty, category, status), arrow keys, `/` filter, Enter opens.
2. **Exercise**: split pane. Left: code editor (line numbers, highlighting, simple autocomplete, TS + Python).
   Right: tabs — *Problem* (rendered Markdown) and *Output* (test results). Ctrl+Enter runs tests.

Assets worth keeping: the 75 problem statements (already Markdown, with a metadata table), the 13 solved
TS solutions, and the vitest cases (source material for language-neutral test cases).

## Stack decision

Evaluated against the feature list (table, split panes, tabs, scrolling, Markdown, images, code editor,
process output). The code editor is the deciding component — everything else exists in every stack.

| Option | Table / tabs / split / scroll | Markdown | Images | Code editor | Verdict |
|---|---|---|---|---|---|
| **A. Python + Textual 8.2** | `DataTable`, `TabbedContent`, `Horizontal`, `VerticalScroll` — built in | `Markdown` widget, built in | `textual-image` 0.14 (Sixel/Kitty/half-blocks) | `TextArea.code_editor()` — line numbers, tree-sitter highlighting, undo, selection; `register_language()` for TS | **Recommended** |
| B. Rust + ratatui 0.30 | Primitives only; you build tabs/split/table state | `tui-markdown` 0.3 (basic) | `ratatui-image` 12.0-rc | `tui-textarea` 0.7 (no highlighting) or `edtui` 0.11 (vim-modal, syntect) | Best binary, 2–3× the UI code |
| C. Go + Bubble Tea | `bubbles` table/viewport/textarea, `lipgloss` layout | `glamour` (good) | none first-party | `bubbles/textarea` has no highlighting | Editor is a build-from-scratch |
| D. TS + OpenTUI (Bun) | Yes | Yes | Partial | tree-sitter textarea | Requires Bun (not installed); youngest ecosystem |
| E. No app: Zellij/tmux layout + nvim + `glow` + file watcher | Terminal multiplexer | `glow` | via terminal | Real editor + LSP autocomplete | Zero code; no catalog/status UX, no "workbook" |

Verified in a spike this session (scratch venv): Textual 8.2.8 exposes all widgets above; built-in
highlighting covers `python`, `javascript` (not `typescript`); `tree-sitter-typescript` 0.23.2 registers
via `TextArea.register_language()` and ships `queries/highlights.scm`; Node v24.19 (nvm) reports
`process.features.typescript == "strip"`, so `.ts` files run with no build step.

**Devil's advocate on A**
- *"Python startup is slow."* Textual cold start is well under a second; the per-run cost is a subprocess either way.
- *"`TextArea` is not a real editor."* True: no LSP, no multi-cursor. Mitigation: `ctrl+o` (Ctrl+Shift+O in WT) / `f4` suspends the
  app and opens `$EDITOR` on the same file (`App.suspend()`), so nvim/helix is always one key away.
- *"Rust gives a single static binary."* Irrelevant for a local WSL2 tool; `uv tool install` puts
  `leet75tui` on PATH. Revisit B only if the tool gets distributed.
- *"`textual-autocomplete` solves autocomplete."* It does not: v4.0.6 targets `Input` only. Simple
  autocomplete is custom work (Phase 5).

## Architecture

```
pyproject.toml                    # [project.scripts] leet75tui = "leet75tui.app:main"; textual>=8.2,<9
src/leet75tui/
  app.py                          # App, global bindings, screen stack
  app.tcss
  catalog.py                      # load problems/*/meta.toml -> Problem dataclass
  progress.py                     # status store: unsolved | attempted | solved (+ last run time)
  workbook.py                     # user solution files: load/save/starter fallback
  screens/catalog_screen.py       # DataTable + filter Input
  screens/exercise_screen.py      # Horizontal(CodeEditor, TabbedContent(Markdown, RichLog))
  widgets/code_editor.py          # TextArea.code_editor subclass, completion popup (Phase 5)
  languages/typescript.py         # tree-sitter-typescript registration + highlight query
  runner/runner.py                # async subprocess, timeout, process-group kill -> RunResult
  runner/harness.py               # Python harness (runs in child process)
  runner/harness.mjs              # Node harness (runs in child process)
problems/NNN_slug/
  problem.md                      # statement (migrated from README.md "Instructions")
  meta.toml                       # id, title, difficulty, category, order, url, kind, entry, params, compare
  cases.json                      # [{ "args": [...], "expected": ... }] or design-op sequences
  starter.ts | starter.py
workbook/NNN_slug.ts | .py        # the user's solutions (in git, like today)
workbook/progress.json
tests/                            # pytest: catalog, runner (both langs), Pilot key-flow, snapshots
```

**Test-case model** (language-neutral, one source of truth for TS and Python):

| `kind` | Count | Harness behaviour |
|---|---|---|
| `function` | 56 | call `entry(*args)`, compare to `expected` |
| `linked-list` / `tree` | 14 | args/expected in LeetCode array form; harness converts via injected `ListNode` / `TreeNode` |
| `design` | 4 (208, 901, 933, 2336) | `{"ops": [...], "args": [...], "expected": [...]}` like LeetCode |
| `interactive` | 1 (374) | harness injects `guess()` bound to the case's `pick` |

`compare`: `exact` (default) · `unordered` · `unordered-nested` · `float`. Python starters use LeetCode's
`class Solution` convention; TS starters use `export function <entry>` (matches existing solutions).
Harnesses print one JSON line per case (`pass`, `args`, `expected`, `actual`, `stdout`, `ms`) so the
Output tab renders structured results, not raw text.

**Screens**

```
┌ leet75tui ───────────────────────────────────────────────────┐
│  #  Problem                          Difficulty  Category   ✓│
│ ▶8  334. Increasing Triplet Subseq.  Medium      Array/Str  ·│
│  9  443. String Compression          Medium      Array/Str  ·│
│ /tree_                                           13/75 solved│
└ ↑↓ move  / filter  ⏎ open  q quit ───────────────────────────┘

┌ 334. Increasing Triplet Subsequence ─── [TS] ────────────────┐
│  1 export function increasingTriplet( │ Problem │ Output │    │
│  2   nums: number[]): boolean {       │ ✔ case 1  2ms      │
│  3   let first = Infinity;            │ ✘ case 4           │
│  …                                    │   expected false   │
│                                       │   actual   true    │
└ ^⏎/F5 run  F2/F3 tabs  ^t lang  ^⇧O/F4 $EDITOR  esc back ────┘
```

## Success Criteria

- [ ] `uv tool install -e . && leet75tui` opens the Catalog with 75 rows from any directory.
- [ ] Typing `/tree` filters to the Binary Tree / BST rows; Esc restores all 75; Enter opens the Exercise view.
- [ ] Ctrl+Enter (received as `ctrl+j`; F5 fallback) on a correct solution shows all cases passing in the Output tab within 3 s, for both TS and Python.
- [ ] A `while (true) {}` solution is killed after 5 s with a "timed out" result; the UI stays responsive throughout.
- [ ] Status flips to solved after a full pass and survives restart (`workbook/progress.json`).
- [ ] `pytest` runs every migrated legacy TS solution against its `cases.json` and they pass (except the 2 in-progress ones, 334/443, marked `xfail` if still failing). This validates the cases and the TS harness together.
- [ ] Quality gates: `ruff check .` 0 errors, `mypy --strict src/` 0 errors, `pytest --cov=src` > 70%.

## Pre-Mortem

Ranked by probability × impact.

| # | Risk | Prob | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Windows Terminal sends Ctrl+Enter as plain Enter / `ctrl+j`, so "run" inserts a newline | High | Med | Phase 0 spike with `textual keys`. If indistinguishable: WT `settings.json` action `sendInput` mapping `ctrl+enter` → `\u001b[13;5u`; always bind `f5` and `ctrl+r` as fallbacks. Resolved in Phase 0: Ctrl+Enter arrives as `ctrl+j`; no remap needed. |
| 2 | Migrating 75 problems' tests to `cases.json` stalls on list/tree/design/interactive problems | High | High | `kind` field + harness adapters (above); migration script converts the mechanical `expect(fn(...)).toBe(...)` cases; the ~19 special problems get hand review; Phase 4 may ship with problems flagged `cases: pending` in the table. |
| 3 | `node` not found when launched outside an interactive shell (confirmed: not on PATH in this session's non-interactive shell) | High | Med | Runner resolves `LEET75_NODE` → `PATH` → newest `~/.nvm/versions/node/*/bin/node` ≥ 23.6; footer warns and disables TS runs if none found. |
| 4 | User code hangs or floods output and freezes the TUI | Med | High | Run in a Textual worker; `asyncio.create_subprocess_exec` with `start_new_session=True`; kill process group at 5 s; cap captured stdout at 64 KB. |
| 5 | Result comparison false negatives (order-insensitive answers, floats — e.g. 2215, 643) | Med | Med | `compare` modes in `meta.toml`; legacy-solution test suite (success criterion 6) catches wrong modes. |
| 6 | TS highlight query from `tree-sitter-typescript` does not load standalone (it extends the JS query) | Med | Low | Concatenate JS + TS `highlights.scm`; fallback is the built-in `javascript` grammar (degrades, does not break). |
| 7 | `TextArea` editing feels worse than nvim, tool gets abandoned | Med | Med | `ctrl+o` / `f4` → `$EDITOR` escape hatch in Phase 2, not as polish. |
| 8 | Scope creep into images / study-guide features before the run loop works | Med | Med | Images and notes are explicitly post-MVP; no phase depends on them. |
| 9 | Existing work lost in the rewrite | Low | High | WIP committed on `main` (`9c6aa87`); rewrite on branch `tui`; migration script copies solutions into `workbook/`; git history untouched. |
| 10 | Textual API churn across majors | Low | Med | Pin `textual>=8.2,<9`; snapshot tests surface breaks on upgrade. |

## Tasks

### Phase 0: Fork + key spike (XS, timeboxed 2 h)
- [x] Branch `tui` from `main` (WIP already committed as `9c6aa87`) — git only
- [x] Run `textual keys` in Windows Terminal; record what Ctrl+Enter, Alt+1, Ctrl+O deliver — notes appended to this plan (spike run by the user; see Phase 0 notes below)
- **Exit / scope-cut:** if Ctrl+Enter is unusable even with the WT `sendInput` remap, adopt F5 as the primary run key and continue.

### Phase 1: Catalog tracer bullet (S) — ships a browsable study guide
- [x] `pyproject.toml`, `src/leet75tui/app.py`, `app.tcss` — package + `leet75tui` entry point
- [x] `scripts/migrate_legacy.py` — `NNN_slug/README.md` → `problems/NNN_slug/{problem.md,meta.toml}` (reuses the table parsing that `scripts/update-readme.sh` does in awk); solved flags → `workbook/progress.json`; `solution.ts` → `workbook/NNN_slug.ts`
- [x] `catalog.py`, `progress.py` — typed loaders
- [x] `screens/catalog_screen.py` — `DataTable`, `/` filter `Input` (case-insensitive substring over title + category); Enter opens the Exercise screen (read-only view superseded, see Phase 0 notes)
- [x] `tests/test_catalog.py`, `tests/test_catalog_screen.py` — loader + Pilot test for filter/Enter
- **Rollback:** `main` still holds the legacy repo untouched.

### Phase 2: Exercise view, editing (M) — ships a workbook
- [x] `screens/exercise_screen.py` — `Horizontal` split: editor | `TabbedContent(Problem, Output)`; `f2`/`f3` tabs; Esc back
- [x] `widgets/code_editor.py` — `TextArea.code_editor`, line numbers, soft tabs; autosave on change (debounced) via `workbook.py`
- [x] `languages/typescript.py` — register TS grammar (risk 6); `ctrl+t` toggles TS/Python, loading `starter.*` when no workbook file exists
- [x] `ctrl+o` (Ctrl+Shift+O in Windows Terminal) / `f4` → `App.suspend()` + `$EDITOR`, reload buffer on return
- [x] `tests/test_workbook.py`, `tests/test_exercise_screen.py`, `tests/test_external_editor.py`
- [ ] Snapshot test of the Exercise layout (`pytest-textual-snapshot` is a dev dependency; no snapshot test exists yet)
- **Scope-cut:** Python-only highlighting if TS registration fights back; TS still editable.

### Phase 3: Runner (M) — ships the practice loop
- [x] `runner/harness.py`, `runner/harness.mjs` — all kinds (not only `function`); JSON-lines output
- [x] `runner/runner.py` (+ `node.py`, `compare.py`, `results.py`) — node resolution (risk 3), timeout + process-group kill (risk 4), output cap
- [x] `ctrl+j` (Ctrl+Enter in Windows Terminal) / F5 / Ctrl+R binding at screen level with `priority=True` (so `TextArea` does not consume it); run in worker; switch to Output tab; per-case pass/fail with expected vs actual (`widgets/run_output.py`)
- [x] Update `progress.py` on full pass; status column refreshes on return to Catalog
- [x] ~~Hand-write `cases.json` + starters for 5 `function` problems~~ — superseded by the full Phase 4 migration
- [x] `tests/test_runner.py`, `tests/test_compare.py`, `tests/test_exercise_run.py` — pass, fail, exception, timeout, stdout capture, for both languages
- **Scope-cut:** Python-only runner if node resolution blocks; TS follows in Phase 5.

### Phase 4: Content migration (L) — all 75 problems runnable
- [x] Extend `scripts/migrate_legacy.py` — vitest `expect(fn(args)).toBe/toEqual(x)` → `cases.json`; generate `starter.ts` / `starter.py` from signatures (all 75 migrated, none `pending`; `tests/test_content.py` checks the contract)
- [x] Harness adapters for `linked-list`, `tree`, `design`, `interactive` kinds (both harnesses); `compare` modes
- [ ] Hand-review the 19 non-`function` problems and every `compare` override (`test_special_problems_keep_their_modelling` covers the modelling; no human review yet)
- [ ] `tests/test_legacy_solutions.py` — every migrated TS solution passes its cases (success criterion 6). Checked ad hoc on 2026-09-29: all 10 `workbook/*.ts` pass via `run_solution`, ~75 ms each; not yet a test
- [x] `git rm` legacy `NNN_slug/` dirs, `package.json`, `pnpm-lock.yaml`, `vitest.config.mts`, `tsconfig.json`, `.eslintrc.json`, `.prettierrc`, `scripts/update-readme.sh`, and `scripts/migrate_legacy.py` once migration is committed (no dead code). Done 2026-10-09; `problems/` is now hand-edited and guarded by `tests/test_content.py`
- **Scope-cut:** ship with unmigrated problems flagged `cases: pending` in the Catalog.

### Phase 5: MVP polish (M)
- [x] `widgets/code_editor.py` + `widgets/completion.py` — simple autocomplete: `ctrl+space` popup over language keywords + identifiers in the buffer + `entry` name
- [x] Status column glyphs (`✓` solved, `~` attempted, `·` unsolved) + solved counter in Catalog; footer key hints per screen
- [x] `README.md` rewrite — install (`uv tool install -e .`), key map, content format for adding problems
- [x] Quality gates to green — ruff, mypy and pytest
- **Scope-cut:** autocomplete is the first thing dropped; the `$EDITOR` hatch covers it.

### Post-MVP (not planned here)
Images in problem statements (`textual-image`, Sixel in WT ≥ 1.22), per-problem notes/hints tab,
spaced-repetition review queue, type-checking TS with `tsc --noEmit` as an optional run step.

## Dependencies

```
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 5
          Phase 1 → Phase 4 → Phase 5
          Phase 3 → Phase 4 (harness adapters extend the Phase 3 harness)
```
Phase 4's script work can start in parallel with Phase 2; its adapter work waits on Phase 3.
No cycles.

## Verification

1. `uv tool install -e . --force && cd ~ && leet75tui` — Catalog shows 75 rows.
2. `uv run ruff check . && uv run mypy --strict src/ && uv run pytest --cov=src` — all green, coverage > 70%.
3. Manual, in Windows Terminal: `/linked` → Enter on 206 → Ctrl+Enter (received as `ctrl+j`; F5 is the fallback) → Output tab shows all cases pass →
   Esc → row 206 shows solved. Replace body with `while (true) {}` → Ctrl+Enter → "timed out" after 5 s,
   editor still accepts input during the run.
4. `ctrl+t` to Python on 1768, write a solution, run, quit, relaunch → solution and status persist.

## Agent Assignments

| Task | Role | Agent | Model | Why |
|---|---|---|---|---|
| Phase 0 fork + key spike | shell / git | command-expert | sonnet | Git + terminal config, no app code |
| Phase 1–3, 5 app code (screens, runner, editor) | CLI / TUI developer | backend-specialist | opus | Plan-skill mapping for CLI tools; Python + subprocess work |
| Phase 4 migration script + adapters | data migration | backend-specialist | opus | Same codebase and harness it extends |
| Test suites, snapshot + Pilot tests | tests | test-engineer | sonnet | pytest, coverage gate |
| Runner sandbox review (timeouts, kill, output cap) | review | code-reviewer | opus | Executes arbitrary local code; needs a second pair of eyes |
| README rewrite | docs | documenter | sonnet | User-facing install + key map |

## Open decisions (defaults chosen; change before Phase 1 if you disagree)

| Decision | Default | Alternative |
|---|---|---|
| Where solutions live | In-repo `workbook/` (versioned, like today) | `~/.local/share/leet75tui/` (repo stays content-only) |
| Python solution shape | LeetCode `class Solution` | Bare `def fn(...)` |
| Fork mechanism | Branch `tui` in this repo | New repo, this one archived |

## Phase 0 notes (2026-09-29)

Key spike run by the user in Windows Terminal (WT) with `textual keys`. These results are authoritative for the key map.

| Key pressed | What Textual receives | Binding | Footer label |
|---|---|---|---|
| Ctrl+Enter | `Key(key='ctrl+j', character='\n', aliases=['ctrl+j', 'newline'])`; plain Enter is `enter` (`\r`), so they are distinguishable | Run = `ctrl+j`, screen-level with `priority=True` so `TextArea` does not consume it; `f5` and `ctrl+r` stay as fallbacks; no WT `sendInput` remap needed | `^⏎ run` |
| Alt+1 | `¡` (`inverted_exclamation_mark`, printable): the keyboard layout eats Alt+digit, so `alt+1` / `alt+2` are not usable | Tabs: `f2` = Problem, `f3` = Output (WT does not bind these by default) | `F2/F3 tabs` |
| Ctrl+O | Nothing: WT swallows plain Ctrl+O. Ctrl+Shift+O arrives as `Key(key='ctrl+o', character='\x0f')` | `ctrl+o` stays (it matches Ctrl+Shift+O); `f4` as fallback | `^⇧O / F4 $EDITOR` |

Phase 0 exit / scope-cut not triggered: Ctrl+Enter is usable (as `ctrl+j`) without a remap, so F5 stays a fallback rather than the primary run key.

- **Branch:** `tui` created from `main` at `9c6aa87` (WIP commit "Stashing").
- **Open decisions:** defaults accepted when the user approved orchestration: in-repo `workbook/`, LeetCode `class Solution` for Python, branch `tui` in this repo.
- **Data finding** (verified with grep): the legacy README marks 13 problems `[x]`, but only 8 of them have code in the repo. 1071, 151, 1493, 2095 and 206 are marked solved while their `solution.ts` is still a `throw new Error('Not implemented…')` stub; 334 and 443 contain in-progress code without `[x]`. Migration decision: keep the 13 SOLVED flags (the user's record), copy only real solutions (10 files) into `workbook/`, seed 334/443 as ATTEMPTED. This amends the Context line "the 13 solved TS solutions" and the Phase 1 `solution.ts` copy step.
- **Execution approach:** phases are built by parallel agents against a shared contract (content format + runner API). Phase 3's "hand-write `cases.json` + starters for 5 `function` problems" is superseded by the full Phase 4 migration of all 75 problems; Phase 1's interim read-only Problem view is superseded by the Phase 2 Exercise screen.

## Status (2026-09-29, end of Wave 1)

Wave 1 (four parallel agents: app, runner, content, docs) was stopped at the user's request and its
output committed on `tui` as a checkpoint. Wave 2 (snapshot/legacy tests, runner sandbox review,
README) has not run.

| Gate | Result |
|---|---|
| `uv run pytest --cov=src` | 793 passed, 99% coverage (node found via the nvm fallback; no PATH setup needed) |
| `uv run mypy --strict src/` | 0 issues, 25 files |
| `uv run ruff check .` | 0 errors. `[tool.ruff]` (added 2026-10-09) sets `line-length = 100`, the width the code was written to; it excludes `problems`, `workbook` and `tests/fixtures`, whose stubs deliberately mirror LeetCode's Python template |

**Remaining for MVP**
- [x] `[tool.ruff]` config in `pyproject.toml`
- [ ] `tests/test_legacy_solutions.py` (success criterion 6)
- [ ] Exercise layout snapshot test
- [ ] Code review of the runner: timeout, process-group kill, output cap (risk 4)
- [ ] Hand review of the 19 non-`function` problems and `compare` overrides
- [x] `README.md` rewrite
- [x] `git rm` of the legacy layout (Phase 4 last task)
- [ ] Manual verification in Windows Terminal (Verification steps 1, 3, 4); success criteria 1–5 are covered by Pilot tests only

**Known issue**
- `meta.toml` is parsed twice: `catalog.py` (`Problem`, `load_problem`) for the UI and `runner/problem.py` (`Problem`, `load_problem`) for the runner, because two agents built them in parallel. Merge into one loader before adding more metadata fields.
