# goal-desk-iter-11 Execution Plan

Era B "The Desk", iteration 11 — builds the single promoted post-GOAL_ACHIEVED journey **J-09**:
a durable, append-only record of what every top-up run attempted. Required-still-passing:
J-01–J-08 (smoke-replay only, per `iteration-state.md`'s "Do not redo").

## What to Build

- New append-only store `desk_topup_log.py` mirroring `UniverseStore`/`ScreenStore`'s discipline
  exactly (checksum-verified load, `record()` the only mutation, no update/delete) — one frozen
  JSON file per completed top-up run.
- A SINGLE shared writer function, called exactly once at a run's terminal state, from BOTH
  `DeskTopupComputeManager`'s worker resolve path (`desk_topup_compute.py` `_work`/`_resolve`,
  currently lines 262/282) and the CLI's `main()` (currently line 329) — never a second write path,
  never a second outcome shape. `run_topup`/`_run_one_pair` (lines 123-188) stay byte-unchanged.
- New route `GET /research/desk/topup/runs` on the ALREADY-mounted `desk_routes.py` router
  (`prefix="/research/desk"`, imported into `app/main.py:42` — no new router/mount needed): honest
  `{"runs": [], "latest": null}` HTTP 200 before any run; `runs` = lightweight meta (everything
  except `outcomes`, mirroring the screen list's meta-only convention); `latest` = full record with
  `outcomes` byte-identical to `run_topup`'s own return for that walk.
- Interrupted-run honesty: a run whose process ends before the writer's terminal call leaves ZERO
  record — never a fabricated entry.
- `/desk` frontend: new read-only "Top-up Runs" section beside the existing "Screen History"
  section — per-run date+id, universe snapshot id, terminal state, attempted-of-total pairs,
  per-outcome counts, and (latest run only) every failed pair's detail verbatim + honest
  unreached-pairs count. No new interactive control.
- New golden replay script `journey-scripts/J-09.json`, scoped to a throwaway backend, with a
  post-match liveness assertion (iter-4/iter-5 lesson).
- `[NEW]`-flagged demo-narrator walkthrough for the top-up-run disclosure.
- Zero diff to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`; zero new `Config`
  field; zero new MCP `_STATIC_PATHS` entry (`ALLOWED_GET_PREFIXES` already includes `/research/`,
  confirmed at `app/mcp/__init__.py:58` — `get_endpoint` reaches the new path with no code change).

## Agents Required

- developer: yes -- implements the full stack below (backend store/writer/route + frontend panel)
  in one TDD pass; both halves are small and tightly coupled to the same data shape.
- backend-data: yes -- new `desk_topup_log.py` store, shared writer wired into two call sites, new
  `GET /research/desk/topup/runs` route, new/extended pytest coverage.
- frontend-ux: yes -- new read-only "Top-up Runs" section on `apps/frontend/app/desk/page.tsx`.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

Backend — new:
- `apps/backend/app/research/desk_topup_log.py` -- `TopupRunStore` (mirrors `ScreenStore`),
  `resolve_desk_topup_log_dir(desk_universe_dir_resolved)` (mirrors `desk_screen.resolve_desk_screen_dir`
  — bare env-var-or-sibling default, NOT a `Config` field), and the shared writer function (e.g.
  `record_topup_run(...)`) that both call sites invoke.
- `apps/backend/tests/test_desk_topup_log.py` -- store discipline (checksum/append-only/no-update),
  the shared-writer contract exercised from both a manager-style call and a CLI-style call,
  interrupted-run-leaves-no-record, cancelled-run, second-run-appends-without-touching-first.

Backend — modify:
- `apps/backend/app/research/desk_topup_compute.py` -- thread `universe_snapshot_id` (currently
  discarded after `trigger()`'s `records, _errors = universe_store.list()` at line ~230; only
  `members` is kept) and a single `requested_window` capture through to `_resolve`/the writer; call
  the shared writer at both `_resolve` exit paths (~272 failed, ~274 cancelled/done) and once more
  in the CLI's `main()` after `outcomes = run_topup(...)` succeeds (~364).
- `apps/backend/app/research/desk_routes.py` -- add `get_topup_run_store` dependency (mirrors
  `get_screen_store` at ~223) + `GET /topup/runs` route (mirrors `GET /screen`'s meta-only-list +
  full-latest shape at ~248-266).
- `apps/backend/tests/test_desk_topup_compute.py` -- extend if the writer call is asserted inline
  here; otherwise unaffected — re-run to confirm no regression.
- `apps/backend/tests/test_mcp_server.py` -- re-run only, no code change expected (17-tool count +
  `get_endpoint("/research/desk/topup/runs")` byte-identity).
- `apps/backend/tests/test_copy_discipline.py` -- re-run only, no code change expected.

Frontend — modify:
- `apps/frontend/app/desk/page.tsx` -- new `TopupRunsSection`/`TopupRunsTable` component(s) reusing
  the existing `Panel`/`EmptyState`/`HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL` primitives already
  used by `DeskHistoryTable` (~418-484); a new read-only fetch added to the page's mount-time GET
  batch (~882-896, currently 3 GETs — this becomes a 4th, still zero POSTs on load); render the
  section adjacent to `section aria-label="Screen history"` (~827-835).

Golden / regression:
- `runs/goal-session-desk/journey-scripts/J-09.json` -- new, scoped backend, post-match liveness
  assertion.

Docs:
- `docs/handoffs/goal-desk-iter-11-dev.md` -- new dev handoff.

## Implementation traps (verified against the current tree — read before coding)

1. **Do not extend the existing "Top-up compute progress" job-snapshot shape.** `blueprint.md`
   registers that row as UNCHANGED this iteration. `universe_snapshot_id` and `requested_window`
   must reach the writer as plain local/closure values threaded from `trigger()`/`main()` down to
   the write call — never added as a new key on `self._snapshot` (the manager's in-memory dict). A
   coherence-auditor hard-fail is the likely consequence of getting this wrong.
2. **Run-level `state: "failed"` is not the same thing as a per-pair `outcome: "failed"`.** A
   single failing pair is already caught inside `_run_one_pair` and recorded as an `outcomes` entry
   — it does not fail the run. The run's own `state` is `"failed"` only when something escapes
   `run_topup` itself (mirrors `_resolve`'s existing exception branch at ~268-272). The CLI path
   normally only ever terminates `"done"` (no cancel signal exists there); an uncaught crash before
   the writer's call is the CORRECT interrupted-run case (zero record), not a bug to guard against.
3. **`requested_window` — capture once per run, not once per pair.** `_run_one_pair` calls
   `_fetch_window_now()` itself (line 141) for every pair; re-deriving it a second time inside the
   writer risks a mismatched window on a run that crosses a UTC day boundary. Capture ONE
   `_fetch_window_now()` value in the caller (`trigger()`/`main()`) before the walk starts and pass
   it through — this is the phase spec's own flagged build-time ambiguity (NOTES section); log the
   final choice in `assumptions.md` per that section's instruction.
4. **`pairs_attempted` is `len(outcomes)` at terminal time, not a separately tracked counter** — the
   manager's `self._snapshot["progress"]["pairs_done"]` already equals this; the CLI path can just
   use `len(outcomes)` directly.

## UI Evolution

- New user-facing capability: the operator can see, on `/desk`, a durable record of every top-up
  run's outcome — which pairs were reused/fetched/failed (with vendor detail) and how many a
  cancelled/interrupted run never reached — instead of that information vanishing once the next run
  supersedes the in-flight compute snapshot.
- New information displayed: run date + id, universe snapshot id, terminal state, attempted-of-total
  pair counts, counts by outcome, and (latest run) every failed pair's detail + unreached-pairs count.
- New user actions: none. No new button/control — pure read-only disclosure of outcomes the
  existing Top-up button already produces.
- UI surface changes: one new read-only panel/section on `/desk`, beside Screen History.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse `Panel` (section wrapper), `EmptyState` (honest empty state), and the
  same `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL` table-cell class constants the Screen History and
  Briefing tables already use — visual consistency with the rest of `/desk`, zero new design tokens.
- Layout: same stacked `<section aria-label="...">` single-column layout `/desk` already uses;
  recommended placement is immediately after `section aria-label="Screen history"` and before the
  "Run Screen and Top-up controls" section (groups the two read-only history/log panels together
  ahead of the action controls) — not a hard requirement, log the final placement choice if changed.
- Key visual effects: none new — no glow, gradient, or animation beyond what the existing desk
  tables already use; this is a dense data table, not a hero element.
- States to handle: honest empty state before any run (descriptive copy only, no advice/prediction
  language — `test_copy_discipline.py` must stay green unmodified); populated state with one row per
  run; the latest run's failed-pair detail block must render the full verbatim detail string legibly
  (not truncated) since TC-13's screenshot requires it readable in one image.

## Key Test Scenarios

Full test-first contract is TC-1..TC-17 in `docs/phases/goal-desk-iter-11.md` — highlights:

- Honest-empty `GET /research/desk/topup/runs` before any run; GET never triggers a compute (TC-1, TC-8).
- Manager-triggered run's `latest.outcomes` byte-identical to `run_topup`'s own return (TC-2).
- CLI-triggered run produces the identical record shape (field names/types) as a manager-triggered
  one — proving the ONE shared writer (TC-3).
- Cancelled run: `state: "cancelled"`, `pairs_attempted < pairs_total` (TC-4).
- A failing pair's `outcome: "failed"` with verbatim `detail`; the walk continues past it (TC-5).
- Second run appends a new file; the first file's sha256 is unchanged on disk; `runs` has 2 entries,
  `latest` is the newer one (TC-6).
- A run whose terminal writer call is simulated as never invoked leaves zero record for it (TC-7).
- MCP stays exactly 17 tools; `get_endpoint("/research/desk/topup/runs")` byte-identical to a direct
  GET (TC-9).
- Full suite green at/above 1346 passing / 8 skipped; `Config().config_fingerprint()` still
  `08e471b10130e1e2`; `git diff --stat` empty for `tradability.py`/`levels.py`/`bars.py`/
  `StructureChart.tsx` (TC-10).
- `test_copy_discipline.py` green unmodified against the new panel (TC-11).
- Browser (fixture-scoped rig): honest empty Top-up Runs state screenshot (TC-12); after one
  fixture-scoped top-up run containing an INDUCED failure (use the existing monkeypatch/known
  Yahoo-adapter failure-taxonomy technique `test_desk_topup_compute.py`'s
  `test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_continues` already
  uses — never a live vendor call), a screenshot with attempted-of-total, per-outcome counts, and
  the failed pair's detail all legible in one image (TC-13).
- Store dir resolves as a sibling of `desk_universe_dir_resolved()` with no env override; zero new
  `Config` field (TC-14).
- `J-09.json` verify-mode replay reports 0 failed (TC-15).
- `[NEW]`-flagged demo-narrator walkthrough exists (TC-16).
- J-01–J-08 smoke replay passes against the SAME scoped rig named explicitly in the browser-QA
  dispatch, zero write-path side effect on the ambient `.data/` store (TC-17) — reuse
  `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (the most recent worked scoped-rig
  example) rather than inventing a new recipe, per the phase spec's own NOTES.

## Guardrails (carried from goal.md / iteration-state.md — do not redo or drift)

- Out of scope: any edit to `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`,
  `PriceChart.tsx`, the engine, or any R-1 file; any change to what `run_topup`/`_run_one_pair`
  compute; any change to `desk_coverage.py`; any new `Config` field, MCP tool, page, or nav change;
  a PnL-ledger append; backfilling/rewriting any existing universe/screen/top-up-run record; the
  backlogged `bar-index-store-reconcile` proposal; a real ~100-symbol operator top-up run (this
  iteration proves the mechanism on the fixture-scoped rig only); any new interactive control on the
  Top-up Runs section.
- J-01–J-08 are DONE and clause-verified (`iteration-state.md`) — smoke-replay only, do not
  re-derive or re-implement any of their internals.
- If `journey-scripts/J-09.json`'s replay triggers a NEW top-up run, scope that replay's backend
  explicitly and check the target store for a pre-existing run record first (iter-5/iter-10 lessons
  on golden-script write paths and snapshot collisions).
- If any lane edits `journey-scripts/J-09.json` after recording it, disclose it explicitly in that
  lane's results report (iter-8 lesson on undisclosed golden edits).
