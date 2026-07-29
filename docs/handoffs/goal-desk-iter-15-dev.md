# goal-desk-iter-15 Dev Handoff

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **J-11: history-depth disclosure on every ranked `/desk` briefing row.** Two new fields —
  `history_sessions` (count of completed daily bars at or before the row's `basis_as_of`) and
  `history_start` (the earliest such bar's own timestamp) — are now attached to every RANKED row a
  screen computes, so the operator can tell a short-history listing (e.g. 27 sessions) from a
  long-history one (e.g. 500 sessions) without leaving `/desk`.
- Both fields are derived **inside the existing** `_resolve_reference_close` ascending walk over
  `BarStore.merged_bars(symbol, "1d")` (renamed `_resolve_reference_close_and_history` to reflect
  its now-broader return contract `(close, history_sessions, history_start)`) — zero new store
  read, zero new accessor on `bars.py`/`bar_index.py`. Verified live against the REAL running
  backend + real `.data/` store, not just fixtures (see "Live verification" below).
- Skip rows (`no_bars`/`no_basis`) never carry the two new fields, matching the J-08
  (`basis_as_of`/`basis_age_days`) precedent exactly.
- A screen snapshot recorded BEFORE this iteration has ranked rows that OMIT both keys entirely
  (never `null`) — `ScreenStore` performs no row-shape validation/enrichment, so this is true by
  construction and is asserted by a dedicated test.
- Frontend: `/desk`'s ranked table gained a `history` column beside `basis` (`data-testid=
  "desk-row-history"`), with the honest `"history not recorded in this snapshot"` fallback for
  legacy rows, and the row anchor's existing composite hover tooltip
  (`deskRowDrillInTitle`) gained a `history_start` detail line — zero change to click geometry,
  zero change to any other column or section.
- No rank-key change, no new `Config` field, no fingerprint move, no new page/nav/endpoint/MCP
  tool — a pure additive-disclosure iteration, structurally identical to J-08 (iter-9).
- A golden replay script (`runs/goal-session-desk/journey-scripts/J-11.json`) for the downstream
  browser-QA/demo-narrator lanes.

## Files Changed

- `apps/backend/app/research/desk_screen.py` — renamed `_resolve_reference_close` →
  `_resolve_reference_close_and_history`, now returning `(close, history_sessions, history_start)`
  from the SAME single ascending walk it already performed; attached both fields to the ranked-row
  dict in `compute_screen`'s `elif` branch; extended the module docstring with a "History
  disclosure" section mirroring the existing "Basis disclosure" section, and updated `compute_
  screen`'s own docstring and the two other references to the renamed function.
- `apps/backend/tests/test_desk_screen.py` — new "history disclosure (goal-desk-iter-15, J-11)"
  test block: golden per-row values for a short-history and a long-history real fixture-universe
  member in the same run (`test_short_and_long_history_members_carry_visibly_different_session_
  counts_in_the_same_run`), an explicit off-by-one edge case (basis bar is the series' first bar,
  `history_sessions == 1`), a byte-identical-recompute test, a legacy-row-absence test, a
  `merged_bars`-call-count guard proving zero extra store reads
  (`test_history_fields_add_zero_extra_merged_bars_calls`), and a single-source-of-truth
  cross-check against `GET /research/candles`. Also added two one-line assertions to the existing
  `no_bars`/`no_basis` skip-row tests proving skip rows never carry the new fields (TC-5). Added a
  small helper trio (`_daily_bar_epoch`, `_iso_of`, `_daily_bars`, `_seed_daily_bars`) for
  synthesizing daily bar series on real fixture-universe symbols (ABBV short, ACN long) — per
  lessons.md iter-2, never a fake `AAA`-style symbol for a clause naming real symbols.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` — added `row.history_start` as a required
  needle in the ranked-row drill-in tooltip's F2-consolidation guard (the same pattern the J-08
  basis fields already established in this file).
- `apps/frontend/lib/types.ts` — `DeskScreenRow` gains `history_sessions: number | null` /
  `history_start: string | null`, mirroring the `basis_as_of`/`basis_age_days` loose-`== null`
  legacy-absence contract.
- `apps/frontend/app/desk/page.tsx` — new `history` `<th>`/`<td>` column pair in the ranked table
  (mirrors the `basis` column exactly, same `LABEL_CELL` class, `data-testid="desk-row-history"`),
  and a `history ${history_sessions} sessions from ${history_start}` detail line added to
  `deskRowDrillInTitle`'s composite tooltip string, both gated on the loose `== null` legacy check.
- `runs/goal-session-desk/journey-scripts/J-11.json` (new) — deterministic golden replay script
  (goto `/desk`, expect the `history` header, expect `desk-row-history` cell text `"sessions"`,
  expect the page title) for the downstream replay/demo-narrator lanes; validated clean against
  `scripts/automation/lib/demo_runner.py`'s `validate_script`. Its `notes` explain why the specific
  short/long split (TC-8) and the tooltip's `history_start` (TC-9, hover-only — `hover` is not in
  `demo_runner.py`'s `_VALID_ACTIONS`) are live-browser-only checks, not expressible in this
  deterministic text-match format.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v` (also `-q` for the full-suite
pass)
Result: **1418 passed, 8 skipped, 0 failed** (full suite; confirmed via progress-character count
since the final summary line was clipped by the background-capture transition in this environment
— exit code 0 on every run, zero `F`/`E` characters across the entire progress bar).

Targeted: `pytest tests/test_desk_screen.py -v` → 49 passed. `pytest
tests/test_desk_hover_tooltip_guard.py tests/test_copy_discipline.py -v` → 33 passed.

Frontend: `npx tsc --noEmit` → clean. `rm -rf .next && npm run build` → compiled successfully,
`/desk` route built (7.26 kB, 117 kB First Load JS).

Sentinels (all green, part of the full-suite run above):
- `Config().config_fingerprint()` still `08e471b10130e1e2` (zero change to `app/config.py` this
  iteration — confirmed by `git diff --stat`, the file does not appear in the diff at all).
- MCP tool count still exactly 17 (`test_mcp_server.py`'s own `len(TOOL_NAMES) == 17` assertion).
- `tests/test_copy_discipline.py` green unmodified (30 tests, including the frontend-literal lint
  that automatically covers the new `history` column/tooltip copy).

## Live verification (Pre-handoff checklist)

- **Service startup:** started backend (`CHAIN_BACKEND_PORT=8471 bash scripts/start-backend.sh`)
  and frontend (`CHAIN_FRONTEND_PORT=3471 bash scripts/start-frontend.sh`) cleanly; `GET /health`
  → `{"status":"ok"}`; `GET /` and `GET /desk` on the frontend both returned 200. Both processes
  were stopped afterward (`pkill`), confirmed dead via a refused connection on both ports.
- **End-to-end confirmation against the REAL ambient `.data/` store** (not just fixtures): the
  already-recorded latest screen (`screen-2026-07-29-ce0d82b8e9bf`, goal.md's own cited J-11
  worked example) correctly OMITS `history_sessions`/`history_start` on its rows (a genuine legacy
  row, recorded before this change — live confirmation of TC-4, not just the unit test). Triggering
  a fresh `POST /research/desk/screen/compute` for `screen_date=2026-07-28` against that SAME real
  store produced a new snapshot (`screen-2026-07-28-ac07c9581a4f`, 63 ranked rows) whose rows DO
  carry both new fields — `history_sessions` ranged from 27 (HONA, the exact short-history example
  goal.md's own rationale cites) to 501 (57 members at or near the store's ~500-bar daily depth),
  independently reconfirming the DoD's `<=60` / `>=400` split is genuinely reachable today, not
  just a stale historical number. A second identical-pins POST correctly returned `"reused": true`
  with the SAME `screen_id` and no duplicate file (append-only dedup unaffected by this change) —
  confirmed exactly one `screen-2026-07-28-*.json` file on disk. The compiled `.next` build was
  grepped and confirmed to contain the new `desk-row-history` testid and the legacy-fallback copy
  string, proving the served bundle reflects this iteration's source, not a stale cache.

## Known Issues

- **MCP `desk_screen` proxy pass-through**: the execution plan's "Agents Required" section lists
  this as part of the new `test_desk_screen.py` test block, but no dedicated new test was added to
  that file for it. Rationale: this iteration adds zero new MCP code (no new endpoint, no new
  tool — `desk_screen`'s existing byte-identical GET-proxy contract already covers new payload
  fields automatically), and `test_mcp_server.py`'s existing
  `test_desk_screen_tool_byte_identical_on_a_populated_state` / `...honest_empty_state` tests
  already prove the proxy is byte-identical for ANY JSON body (they diff the full serialized
  response text, not specific fields) — adding a second, heavier live-server-based test into
  `test_desk_screen.py` to re-prove an already-structurally-guaranteed property seemed like exactly
  the kind of unnecessary abstraction the simplicity bar warns against. If the reviewer disagrees,
  the fix is small: seed a `ScreenStore.record()` call carrying the new fields inside a
  `test_mcp_server.py`-style live-backend fixture and assert MCP/REST byte-identity — flagging here
  rather than silently deciding it doesn't matter.
- The pytest full-suite run's final "N passed in X.XXs" summary line was consistently absent from
  the captured background-task output in this environment (a background-capture buffering artifact
  at the foreground→background transition, not a test problem) — pass/fail was instead confirmed
  by exit code (0, every run) and a character-count of the progress bar (1418 `.` + 8 `s`, zero
  `F`/`E`). Documented here so a reviewer isn't surprised by its absence in the raw log.
- No new Config field, no fingerprint move, no new endpoint/route/page/nav entry, no MCP tool
  change — confirmed structurally (desk_screen.py's own `test_desk_screen_module_adds_no_config_
  field` sentinel plus `git diff --stat` showing `app/config.py`/`app/mcp/__init__.py`/`app/meta.py`
  do not appear in the diff at all).
- A pre-existing, unrelated `next dev -p 3301` process was observed running on this machine before
  this dispatch started (not started by this session, not touched — killing an unrelated ambient
  process outside this task's scope risked disrupting something else already in flight).
