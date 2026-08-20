# Phase goal-rapid-microscope-iter-16 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness section wrapper (`MicroReadinessSection`'s `data-testid="micro-readiness-section"` on its loading and unavailable early returns, `page.tsx:5889-5904`) | Changed behavior (DOM coherence — closes iteration-15 COHERENCE-WARN) | The testid was present only in the loaded-state return; the loading and unavailable returns skipped it, unlike its 3 sibling Rapid-Microscope sections (Scout Ledger / Walk-Forward / Validation Vault), which already carried it in all 3 states | Navigate to `http://localhost:3301/desk`, click the "Microscope Readiness" header (`data-testid="desk-section-expand-microReadiness"`). Once loaded (today's real data: 2 tick shards, "Distinct symbol-days: 1"), Inspect Element and confirm an ancestor `<div data-testid="micro-readiness-section">` wraps the panel. Then stop the backend process, reload `/desk`, click "Microscope Readiness" again, and confirm the amber panel reading "Backend unreachable — is the API running?" is ALSO wrapped in `data-testid="micro-readiness-section"`. Restart the backend afterward. |
| `/desk` | Scout Ledger table cells (`ScoutLedgerSection`, `trial.feature.name`/`.transform` and `trial.outcome.horizon_key` reads, `page.tsx:6315-6319`) | Changed behavior (defensive read) | The two reads were previously unguarded; a trial row missing either key would throw during render, and since `/desk` has zero React error boundaries (`grep -c "ErrorBoundary\|componentDidCatch\|getDerivedStateFromError"` on the file returns `0`), that would blank the ENTIRE `/desk` page, not just this table. They now use optional chaining with a `"—"` fallback so only that row's own cell degrades | Navigate to `http://localhost:3301/desk`, click "Scout Ledger" (`data-testid="desk-section-expand-scoutLedger"`). Today's real ledger is empty, so confirm the "No candidates ledgered." empty state (`data-testid="scout-ledger-families-empty"`) renders with zero console errors — this is the only state observable against real data this round. [OPTIONAL, non-gating] Against an isolated `tmp_path`-scoped fixture store seeded via `ScoutLedger.append_row()` with one trial row using the sparse field set `test_desk_scout_tool_byte_identical_on_a_populated_state` uses (`family_id`, `family_root_id`, `candidate_id`, `decision`, `reason` — no `feature`/`outcome` key), confirm that row's Feature and Horizon cells render "—" and every other `/desk` section still renders normally on the same page load. Never seed this against the real `.data` store. |
| `/desk` | Walk-Forward, Validation Vault, Playbook Signals, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs sections (all pre-existing, untouched this round) | Regression (unchanged) | None of these sections' code was touched this round — `git diff --stat` shows only `page.tsx`'s two spots above changed; these sit on the same page and use the same `CollapsibleSection`/`toggleSection` machinery | Expand "Walk-Forward" (`desk-section-expand-walkForward`) and confirm "No fold specs registered." / "No walk-forward sequences run." still render (today's real, unchanged state); expand "Validation Vault" (`desk-section-expand-validationVault`) and confirm "No shards recorded." / "No universes registered." still render; confirm "Playbook Signals" renders without any click (it is not collapsible); expand each of "Referee Registry", "Referee Adjudications", "Referee Runs" and confirm each still shows its own content with no error panel and no console error. Do NOT click "Run Screen" or "Run Walk-Forward" anywhere in this check. |
| `/structure` | Tradable Map table (`data-testid="tradable-map-table"`) + Comparison dropdown (`data-testid="comparison-dataset-select"`) | Regression (unchanged, different route) | Confirms this round's `/desk`-only diff did not affect a sibling route | Navigate to `http://localhost:3301/structure`. Type `AAPL` into the "Symbol" field, type `2026-06-22 16:00:00` into the "As-of (ET)" field (`data-testid="structure-as-of-input"`), click "Load" (`data-testid="structure-load-button"`). Confirm the Tradable Map table renders 10 band rows (this exact symbol/as-of pair is confirmed live against the real backend to return 10 bands) and the comparison dropdown is present and selectable. |
| `/` (Cockpit) | Live tape + chart, mode selector (default "Simulated"), ticker field, "Watch" button | Regression (unchanged, different route) | Confirms this round's `/desk`-only diff did not affect the home route | Navigate to `http://localhost:3301/`. Confirm the mode selector shows "Simulated" (the default). Type `SIM-BUYER` into the ticker field and click "Watch". Confirm the chart renders and the tape begins updating. If a headless capture shows a static-looking chart, cross-check against the backend payload before calling it a failure — `visibilityState: "hidden"` is known to freeze this specific chart in headless Chrome. |
| All pages | Top navigation bar | Regression (unchanged) | No navigation change this round (plan.md: "Navigation changes: none") | From any page, confirm the top navigation shows exactly 3 links, labeled "Cockpit", "Structure", "Desk" — no fourth link. |

<!-- Change Type options used above: Changed behavior (DOM coherence) | Changed behavior (defensive read) | Regression (unchanged) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/micro_observer.py` — the one production edit this round (TR-26):
  `_advance_depletion_run`'s price-change-termination branch now stamps `observed_through` at the
  revealing (price-changing) quote's own instant instead of the prior same-price quote's. This
  value is never served through any REST endpoint or MCP tool — it is read only internally by
  `scout.py`/`walkforward.py`/`micro_join.py` during compute. No UI surface affected.
- `apps/backend/tests/test_micro_accessor.py` — 1 new TR-3 non-vacuity mutation-proof test + a
  `# === TR-3 ===` reference header. Test-only. No UI surface affected.
- `apps/backend/tests/test_walkforward.py` — 1 new TR-3 aggregate-boundary test, 1 new TR-22
  non-vacuity mutation-proof test, reference headers for both. Test-only. No UI surface affected.
- `apps/backend/tests/test_micro_observer.py` — 2 existing assertions corrected (documented as the
  TR-26 specified-behaviour fix, not a regression) + 4 new tests (bound-termination,
  2× truncation-boundary, non-vacuity mutation-proof). Test-only. No UI surface affected.
- `apps/backend/tests/test_desk_ui_guards.py` — 1 new seeded-violation counter-test for the two
  iteration-15 `_PRICE_ARITHMETIC_FIELDS` clauses. This file's SUBJECT is UI-safety (it guards
  `page.tsx`'s rendered arithmetic), but the change itself is a new automated test case, not a new
  UI element — no new UI surface.
- `micro_readiness.py`'s served computation, `vault.py`, `tick_recorder.py`, `scout.py`,
  `scout_ledger.py`, `walkforward_ledger.py`, `micro_routes.py`'s route shape, `micro_chain_ledger.py`,
  every `referee_*.py`, and every Playbook detector — **not touched this round** (confirmed via
  `git diff --stat`, the dev handoff's explicit zero-diff check, and the SHA-256 re-check on the
  Referee files + `micro_chain_ledger.py`). Every field this round's tests exercise was already
  computed and served by unchanged code.

---

## Summary

- **Frontend surfaces changed:** 2, both inside the single existing `/desk` route
- **New pages/routes:** 0
- **Modified components:** 2 (`MicroReadinessSection`, `ScoutLedgerSection` — both inline function
  components inside `apps/frontend/app/desk/page.tsx`, the only frontend file touched)
- **Navigation changes:** no
- **Backend-only changes:** 5 (1 production file + 4 test files)
