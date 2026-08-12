# Phase goal-playbook-iter-10 — UI Surface Map

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `PlaybookSignalDetail` → `range_trade` geometry line (`data-testid="desk-playbook-signal-range-trade-geometry"`), driven by `DeskPlaybookGeometry.turned_at_midrange` in `apps/frontend/lib/types.ts` | Changed behavior (new conditional chip on an existing element) | R-3.2(b): `_range_trade_side` (`desk_playbook_detect.py`) now also computes and serves whether the approach swing turned at the range's midpoint, alongside the existing "crossed midrange" disclosure | Navigate to `http://localhost:3301/desk`, type `2026-06-22` into the "Session date (yyyy-MM-dd)" field (`data-testid="desk-playbook-date-input"`), click the table row where the symbol cell reads `RTAAA` and the setup chip reads `Range Trade`, and read the geometry line under the signal header — confirm it reads exactly `range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange` with NO `· turned at midrange` text (present-but-`false` on this live record) and no error/blank state. See the UI Test Plan (UT-02/UT-03) for the full procedure, including the currently-blocked `true`-value check. |

Only one production UI surface is affected. No new route, page, section, or navigation entry was
added; the change is a single new conditional text fragment inside an element that already existed
(shipped in goal-playbook-iter-6).

<!-- Change Type key used above: Changed behavior -->

---

## Backend-Only Changes (No UI Impact)

- `docs/playbook-detector-spec.md` — four wording edits (§3.3 body + `PLAYBOOK_JUMP_MIN_MULT` row,
  §3.6 constant rename, §3.7 Trigger clause, §3.8 Caps line) making the written spec match
  already-shipped detector code, verbatim, plus the §3.7 Disclosures clause split that names the
  new field before any code used it. `git diff` shows zero lines changed in any detector function
  these edits describe. Pure documentation — no UI surface affected, ever (this is engineering
  reference material, not user-facing content).
- `apps/backend/tests/test_desk_playbook_detect.py` — adds a `turned_at_midrange` True fixture and
  its near-miss False control, plus one new assertion each on two pre-existing canonical
  long/short `range_trade` fixtures — test-only, no UI surface affected.
- `apps/backend/tests/test_desk_playbook.py` — extends the `playbook_input_signature`/
  `playbook_parameters()` stability counter-test (both directions) and adds a check that a
  pre-iteration-style record serves its geometry with the key absent (never `null`), HTTP 200 —
  test-only, no UI surface affected.
- `apps/backend/tests/test_seed_playbook_iter8_replay_rig.py` (new file) — smoke-checks the seed
  script's index repair (below) in isolation — test-only, no UI surface affected.
- `apps/backend/scripts/seed_playbook_iter8_replay_rig.py` — `_copy_kept_symbol_series` now indexes
  the scoped rig's copied AAPL bar files into its own `bar_index.db` via
  `desk_index_reconcile.run_reconcile`, so `GET /research/bars?symbol=AAPL` (what `/structure`'s
  chart fetches) can find them. This repairs a test/QA-only defect: the SCOPED fixture rig's own
  `/structure` chart previously rendered a blank canvas for AAPL even though the bar files were
  physically present but unindexed. The real, production `/structure` page was never affected —
  its AAPL data was already correctly indexed the whole time. No UI surface affected for real
  users; affects only the fidelity of automated browser-QA evidence captured against the scoped rig.
- `runs/goal-session-playbook/journey-scripts/J-10.json` — step 6 no longer asserts a
  fixture-rebuild-dependent hash; it and two new steps (7, 8) now assert three always-rendered
  `/desk` section headings ("Top-up Runs", "Index Reconciliation", "Screen Runs"). This is an
  internal automated-replay test asset, not shipped product code — the sections it asserts already
  existed and are unchanged by this iteration; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` → Playbook Signals → `range_trade` signal detail)
- **New pages/routes:** 0
- **Modified components:** 1 (`PlaybookSignalDetail`'s `range_trade` branch in
  `apps/frontend/app/desk/page.tsx`), plus 1 type definition updated
  (`DeskPlaybookGeometry` in `apps/frontend/lib/types.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 6 (spec doc, 3 backend test files, 1 seed script, 1 golden-replay
  test asset)
