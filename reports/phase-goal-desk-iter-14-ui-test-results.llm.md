# goal-desk-iter-14 — UI Test Results (LLM browser-qa-agent pass)

**Phase:** goal-desk-iter-14
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/2 tests passed (1 skipped — no browser surface)

**Scope note (lean mode):** per dispatch, only J-06 and J-10 were tested this run. J-01, J-02, J-03,
J-04, J-05, J-07, J-08, J-09 are covered separately by the deterministic golden replay
(`reports/phase-goal-desk-iter-14-regression-replay-results.md`, 8/8 PASS, 2026-07-29) and are not
re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | happy-path | P1 | Honest empty reconciliation state + dark AAPL `1d` badge captured FIRST; then one reconciliation run + one new screen run; then populated reconciliation detail + lit `1d` badge captured, both composite screenshots legible | Empty state captured first (`{"runs": [], "latest": null}` confirmed via API before any UI interaction); "Reconcile Index" clicked → run `reconcile-2026-07-29-74a66e4611a7` resolved `state: done`, `rows_indexed` 345→369, 24 AAPL `1d` unindexed-series drift entries repaired to zero; "Run Screen" clicked → NEW append-only snapshot `screen-2026-07-29-e7e5de9a5815` recorded (not a reuse), AAPL `1d` badge now `data-has-bars="true"`; prior screen `screen-2026-07-27-073795dff864` remained present and distinct in Screen History (unchanged `bar_store_signature`) | PASS | `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC17-empty-before.png`, `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC18-populated-after.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools | happy-path | P1 | N/A — journey's own acceptance text is explicitly "(Keyless; automated.)"; goal.md's "Testing Requirements" line states "J-06 by its 17-tool contract test (no browser surface)" | No UI surface exists for this journey; nothing to drive in a browser | SKIP | none |

---

## Passed Tests

### UT-J-10 — The coverage the briefing shows is the coverage the frozen store can prove
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC17-empty-before.png` (before-state)
- `reports/qa/goal-desk-iter-14-evidence/UT-J-10-TC18-populated-after.png` (after-state)

**Environment correction made before testing:** on arrival, the live processes on `:8301`/`:3301`
(env `CHAIN_CURRENT_AGENT=browser-qa-replay`, presumably left running by the preceding deterministic
regression-replay lane) had **no `TAPEOLOGY_*` scoped env vars set** and were unknowingly serving the
**ambient** `apps/backend/.data` store (confirmed via `/proc/<pid>/environ` showing `PWD=.../apps/backend`
with no `TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/etc., and via the served universe/screen
payloads matching the ambient store's known 101-member universe and pre-existing
`reconcile-2026-07-28-43857811211f` run rather than the dev handoff's scoped AAPL-only rig). Since the
ambient store's reconciliation one-way door was already closed (a run was recorded there on
2026-07-28), testing against it would have made TC-17 uncapturable and risked writing a new screen
into the ambient store. Both processes were stopped cleanly (SIGTERM, verified via `ps`/port checks)
and restarted against the dev-prepared scoped rig
(`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.3302867/desk-iter14-scoped-qa`) with
`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR`/
`TAPEOLOGY_JOURNAL_DB` all pointed at that scoped root, per the dev handoff's exact restart recipe,
including the mandatory T-9 clean rebuild (`rm -rf apps/frontend/.next`) before capturing any evidence.
The ambient store was never targeted by any action in this dispatch (no request was ever issued
against a server pointed at `apps/backend/.data`).

**Evidence sequencing performed, in the binding order:**
1. Confirmed via direct `GET http://localhost:8301/research/desk/coverage/reconcile/runs` on the
   freshly-restarted scoped backend: `{"runs": [], "latest": null}` — the one-way door was still open.
2. Navigated to `/desk`; confirmed via DOM inspection: the AAPL row's coverage badges show
   `data-timeframe="1d" data-has-bars="false"` (dark) alongside `1h`/`4h`/`1w` all `data-has-bars="true"`
   (lit), and the Index Reconciliation section reads exactly "No reconciliation run recorded yet."
3. Captured `UT-J-10-TC17-empty-before.png` (full-page, 1400×2200 viewport) — both the honest empty
   text and the AAPL row with its dark `1d` badge are legible together in one frame.
4. Clicked "Reconcile Index" (`data-testid="desk-reconcile-button"`). Confirmed via API: run
   `reconcile-2026-07-29-74a66e4611a7` resolved `state: "done"`, `series_on_disk: 369`,
   `rows_indexed_before: 345` → `rows_indexed_after: 369`, `drift_before.unindexed_series` names 24
   `AAPL`/`1d` series-on-disk-no-index-row entries, `drift_after` empty on all three buckets.
5. Clicked "Run Screen" (`data-testid="desk-run-screen-button"`). Confirmed via API: a NEW screen
   `screen-2026-07-29-e7e5de9a5815` was recorded (screen list grew from 5 to 6 entries; the prior
   `screen-2026-07-27-073795dff864` entry remained present and unchanged), AAPL's coverage now reads
   `"1d": {"has_bars": true, ...}` alongside all three other timeframes. The page's own outcome line
   read "Recorded a new snapshot — screen-2026-07-29-e7e5de9a5815" (not "Reused…"), confirming the
   post-repair `bar_store_signature` genuinely changed (`460ccfc8aed5f2db` → `643a581230fc110a`).
6. Reloaded `/desk`; confirmed via DOM inspection: `data-timeframe="1d" data-has-bars="true"` now on
   the AAPL badge; the Index Reconciliation section shows the run history table (1 row: date, run id
   `reconcile-2026-07-29-74a66e4611a7`, state `done`, series on disk `369`, rows indexed `345 → 369`)
   and the "Latest run" detail block with "Drift before (24)" (24 `AAPL 1d — series on disk, no index
   row (<series_id>)` entries) and "Drift after (0)" rendering the honest `no drift` text (not a blank
   area) via `data-testid="desk-reconcile-run-latest-drift-after-empty"`.
7. Captured `UT-J-10-TC18-populated-after.png` (full-page, same viewport) — the fully populated
   reconciliation detail (run table row, series-on-disk/rows-indexed counts, drift-before list,
   drift-after "no drift") AND the newly-lit AAPL `1d` badge (alongside `1h`/`4h`/`1w`) are legible
   together in one frame. This is the exact composite framing the phase spec's UT-02/UT-08 test cases
   flagged as missing from the two previously-archived `TC-17-empty-reconciliation.png` /
   `TC-18-populated-reconciliation.png` files (both of those remain on disk, untouched, as historical
   record — this dispatch's two new, clearly-named files are the ones that satisfy the composite
   requirement).
8. Screen History table visibly grew from 5 to 6 dated rows (2026-06-22, 2026-07-25, 2026-07-27 ×2,
   2026-07-27, 2026-07-29), with the pre-repair `2026-07-27` row (provenance
   `universe-2026-07-29-3832dd759a52 · 08e471b10130e1e2 · 460ccfc8aed5f2db`) and the new `2026-07-29`
   row (`...· 643a581230fc110a`) both present and distinguishable — direct visual confirmation that the
   repair appended a new snapshot rather than rewriting the old one.

All copy observed in the Index Reconciliation section during this pass is descriptive measurement
only (run id, date, state word, counts, `AAPL 1d — series on disk, no index row (<id>)`, "no drift") —
no advice, imperative, or prediction language, consistent with `test_copy_discipline.py` staying green.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-J-06 — MCP contract v3 — 17 read-only tools
**Verdict:** SKIPPED
**Reason:** J-06 has no browser-testable surface. Its own acceptance text in `docs/goal.md` is
explicitly parenthesized "(Keyless; automated.)", and the iteration spec's own Testing Requirements
section states verbatim: "J-06 by its 17-tool contract test (no browser surface)." The journey's steps
are entirely backend/MCP-registration changes (`app/mcp/__init__.py`'s `_STATIC_PATHS`,
`tests/test_mcp_server.py`'s `EXPECTED_TOOLS`) with no page, route, or UI element to drive. Per the dev
handoff, this journey's own verification (17-tool count, byte-identity of `desk_universe`/`desk_screen`
against curl equivalents, `get_endpoint` proxy correctness) is covered by the automated backend suite,
not by this agent's remit. No Chrome MCP action was attempted for this journey since none is
applicable; this is a scope-correct skip, not a tooling failure.

---

## Environment

- **Frontend URL:** http://localhost:3301 (this iteration's scoped rig, restarted mid-dispatch — see
  correction note above)
- **Backend URL:** http://localhost:8301 (scoped rig:
  `/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.3302867/desk-iter14-scoped-qa`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-14-evidence/`
- **Golden replay script:** `runs/goal-session-desk/journey-scripts/J-10.json` rewritten this dispatch
  (deliberately read-only — asserts only structural/label text, never clicks "Reconcile Index" or "Run
  Screen"), linted clean via `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
  runs/goal-session-desk/journey-scripts --journeys J-10` → `J-10 ok`.
- **Servers left running** for the downstream demo-narrator lane (TC-19), per the iteration's own
  binding sequencing note: both processes on `:8301`/`:3301` are still live against the same scoped rig
  named above, in the exact post-repair, post-new-screen state this report describes (one reconciliation
  run recorded, latest screen `screen-2026-07-29-e7e5de9a5815`). Do not restart or reseed before that
  lane runs.
