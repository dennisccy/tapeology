# Goal Iteration 36 — UI Test Results (J-21)

**Phase:** goal-desk-iter-36
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Scope note (lean/goal-mode dispatch): this run tests ONLY J-21, per the dispatch's explicit
instruction. J-01, J-03, J-04, J-06, J-07, J-12, J-16, J-18, J-20 are verified separately by
deterministic replay (`reports/phase-goal-desk-iter-36-regression-replay-results.md`, 9/9 PASS,
2026-07-31) and are not re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-21 | The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now | happy-path | P1 | `/desk` shows, before any click, whether a screen run right now would reuse an already-recorded snapshot or walk fresh — for the displayed screen's own date (Provenance panel) and for today (Run Screen control) — with an honest empty state when no universe is registered; three states (match, differ, empty) each browser-verified with a screenshot at 1440×900, no horizontal scroll, ranked table unchanged from J-16 | All three states rendered exactly as specified. Match (fixture-scoped rig): Provenance panel's resolved-pins block read "A screen is recorded under these exact pins — screen-2026-06-22-09cf660a4125, recorded 2026-07-31T13:22:41.106918Z." Differ (ambient rig, read-only): both the Provenance panel and the Run-Screen-control line read "No screen is recorded under the pins that resolve right now for this date — a run would walk 101 members." / "No screen is recorded under the pins that resolve for today — a run would walk 101 members." Empty (fixture-scoped rig, before any registration): "No universe snapshot is registered — whether a run today would reuse a recorded screen cannot be named." rendered beside the Run Screen button. `scrollWidth == clientWidth` (1425px) confirmed on both rig captures. All 21 stored golden replay scripts (J-01..J-21) replay green against the ambient rig. | PASS | `reports/qa/goal-desk-iter-36-evidence/J-21-match.png`, `reports/qa/goal-desk-iter-36-evidence/J-21-differ.png`, `reports/qa/goal-desk-iter-36-evidence/J-21-empty.png` |

---

## Passed Tests

### UT-J-21 — The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-36-evidence/J-21-match.png`, `-differ.png`, `-empty.png`

**Rig setup (per goal.md's own "fixture-scoped rig" acceptance clause and lessons.md iter-26/29/32
precedent — never an ambient Top-up/Run Screen click):**

- Stood up a scoped backend on port 8391 with `TAPEOLOGY_DESK_UNIVERSE_DIR` /
  `TAPEOLOGY_BAR_DIR` / `TAPEOLOGY_DESK_SCREEN_DIR` / `TAPEOLOGY_DATASET_DIR` /
  `TAPEOLOGY_JOURNAL_DB` all pointed at a fresh scratch directory (never `apps/backend/.data`).
- Stood up a scoped frontend on port 3391 via `NEXT_DIST_DIR=.next-iter36-qa` (the project's own
  `next.config.mjs` env-gated `distDir`), so the ambient `apps/frontend/.next` build was never
  rebuilt or clobbered (the iter-26 lesson) — verified before AND after: `apps/frontend/.next`'s
  built `desk/page.js` still contains `localhost:8301`, and `next-env.d.ts`/`tsconfig.json`
  (which Next.js rewrote with the scoped `distDir` reference at scoped-server startup, the
  iter-30(b) trap) were restored byte-identical to their pre-rig md5sums after teardown.
- **Step order (iter-29 lesson: capture the empty state before any populating action in the same
  rig session):** (1) started the empty scoped rig, opened `/desk`, captured the empty-state
  screenshot; (2) ran the population script (registers the committed universe fixture — 103
  members — seeds the committed `AAPL_1d_20260101_20260626.json` bars fixture into the scoped
  `BarStore`/`BarIndex`, then calls `run_screen_and_record` for `screen_date=2026-06-22`, mirroring
  `test_desk_screen_pins.py`'s own `real_ctx` fixture); (3) restarted the scoped backend to serve
  the now-populated store; (4) reloaded `/desk`, captured the match-state screenshot; (5) tore the
  whole rig down (killed both processes, removed `.next-iter36-qa`, restored the two tracked
  files).
- The differ state used the AMBIENT `:3301`/`:8301` rig, read-only — no click, no write — exactly
  matching the state goal.md's own iter-36 rationale measured independently at authoring time
  (`bar_store_signature 2ce14e8f252966f7`, none of the 12 recorded screens carry it).

**Verification steps:**
1. Empty state (scoped rig, pre-registration): navigated to `http://localhost:3391/desk`. Page
   text confirmed: `"Desk screen not computed yet."` / `"No universe snapshot is registered —
   whether a run today would reuse a recorded screen cannot be named."` rendered beside the Run
   Screen button. Screenshot: `J-21-empty.png`.
2. Populated the scoped store (universe + AAPL bars + a real screen run for 2026-06-22) via a
   script using the app's own modules (`UniverseStore`, `BarStore`, `BarIndex`, `ScreenStore`,
   `run_screen_and_record`, `resolve_desk_screen_pins`) — self-verified in the script's own output
   (`recorded.id == screen-2026-06-22-09cf660a4125`, 1 ranked / 102 skipped, consistent with the
   fixture universe having bars for only AAPL).
3. Match state (scoped rig, after population): reloaded `/desk`. Provenance panel showed the
   recorded pins AND the "Pins resolved right now for this screen date" block with identical
   universe snapshot id / config fingerprint / bar-store signature, and the descriptive line named
   the exact snapshot a run would reuse. `document.documentElement.scrollWidth (1425) ==
   clientWidth (1425)` — no horizontal scroll. Ranked table (1 AAPL row) and Skipped Members table
   (102 rows) rendered per J-16's existing layout. Screenshot: `J-21-match.png`.
4. Differ state (ambient rig, read-only): navigated to `http://localhost:3301/desk`. Both the
   Provenance panel's resolved-pins line and the Run-Screen-control's today-line stated no screen
   is recorded under the pins that resolve now, each naming "a run would walk 101 members."
   `scrollWidth (1425) == clientWidth (1425)`. Screenshot: `J-21-differ.png`.
5. Backend route sanity: `GET /research/desk/screen/pins?screen_date=2026-06-22` on the scoped
   backend returned the exact byte-for-byte match payload before the frontend capture (confirms
   the endpoint itself, independent of rendering).
6. Golden replay sweep: wrote `runs/goal-session-desk/journey-scripts/J-21.json` (stable
   testid/structural assertions only, per the J-18/19/20 hardening precedent — never the
   match/differ narrative text, since a future ambient Run Screen click could flip which state is
   displayed at any time). Ran `demo_runner.py --mode verify` for J-01 through J-21 together
   against the ambient `:3301` rig: **21/21 passed, 0 failed.**
7. Teardown verified: `lsof -ti :3391`/`:8391` empty after kill; `apps/frontend/.next-iter36-qa`
   removed; `git status --porcelain` on `next-env.d.ts`/`tsconfig.json` clean, md5sums identical to
   pre-rig; ambient `:8301`/`:3301` both still healthy (HTTP 200) with real data rendering
   unaffected.

**No console errors** observed on either rig during any of the three captures (only the benign
React DevTools info log, consistent with the dev handoff's own note).

---

## Failed Tests

None.

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301 (ambient, differ state) / http://localhost:3391 (scoped rig, match + empty states)
- **Backend URL:** http://localhost:8301 (ambient) / http://localhost:8391 (scoped rig)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), 1440×900 viewport
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-36-evidence/`
