# Phase goal-rapid-microscope-iter-21 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness section — Sealed Tranche table, new row `data-testid="micro-readiness-band-touch-count"` | Changed behavior (new row, real data) | `joinable_corpus.band_touch_count` is now materialized to a real int via the new band-touch enumerator instead of the `not_enumerated` sentinel | Navigate to `/desk`, click the "Microscope Readiness" header (`data-testid="desk-section-expand-microReadiness"`), locate the row labeled "Joinable corpus — band touches", and confirm the value cell (`data-testid="micro-readiness-band-touch-count"`) shows either an integer or the literal text "not enumerated" — never blank and never an unlabeled `0`. |
| `/desk` | Scout Ledger section — trial row Feature cell, inside `data-testid="scout-family-{family_id}-trial-rows"` | Changed behavior (conditional new content) | `structure_context.kind` now renders inline after the feature name/transform for any non-`"none"`-kind candidate | With the pilot grid triggered (see the row below), expand Scout Ledger (`data-testid="desk-section-expand-scoutLedger"`) and confirm a trial's Feature cell reads `divergence_at_level_bearish / threshold (band_touch)` — the `(band_touch)` suffix must be present. Then confirm every pre-existing `kind="none"` row (any row from the default grid) renders with NO parenthetical suffix at all. |
| `/desk` | Scout Ledger table — second ledger row under the same `candidate_id` (walk-forward floor-check decision) | New data in an existing table | `register_screen_and_walkforward_check` appends the floor-check result as a second row, never editing the first | In the same expanded Scout Ledger family block, locate the row immediately after the delta-divergence screen row sharing its `candidate_id`, and confirm its Feature and Horizon cells show `—` (em-dash) and its Decision column shows `insufficient_n`; expand that row's `<details>` and confirm the collapsed `screen_result` JSON shows `null`. |
| `/desk` | Scout Ledger section — `data-testid="scout-ledger-unavailable"` panel | Evidence re-capture only (no code change to this panel) | UT-10 passenger: re-capture the backend-unavailable evidence via element-capture instead of a full-page screenshot | Override `window.fetch` in the browser console to reject/error the Scout Ledger's GET call, expand Scout Ledger, then screenshot ONLY the element with `data-testid="scout-ledger-unavailable"` (not the full page) and confirm it shows real message text (e.g. "Backend unreachable — is the API running?"), never a blank or loading frame. |
| `/desk` | Playbook Evidence section — `data-testid="desk-section-expand-playbookEvidence"` and `data-testid="desk-playbook-date-input"` | Regression check (test-script-only change, no product code changed) | `J-10.json` steps 9–10 restored to their pre-iter-16 assertions | Click "Playbook Evidence" (`desk-section-expand-playbookEvidence`) and confirm the text "Built from signature:" appears; then fill `desk-playbook-date-input` with `2026-06-22` and confirm the text "recorded signals, none hidden" appears. |
| `POST /research/desk/micro/scout/compute` (backend endpoint) | none — no UI control exists for this parameter | New API param, deliberately not wired to any control | Additive, default-omitted `grid` body param added; goal.md explicitly keeps this CLI/API-only this iteration | `curl -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"delta_divergence_pilot"}'` and confirm HTTP 200 with `{"state":"running","run_id":"..."}` (or `{"state":"refused","reason":"already_running"}` if a run is in flight). Separately, click the shipped "Run Scout" button on `/desk` and confirm the request it issues (inspect the Network tab) carries no `grid` field — the UI control still only ever triggers the unchanged default grid. |
| `GET /research/desk/micro/readiness` (backend endpoint, feeds Microscope Readiness) | none — same row as above | Changed response value (same shape) | `band_touch_count` sentinel replaced by the real materialized value on every call | `curl http://localhost:8301/research/desk/micro/readiness \| python3 -m json.tool` and confirm `joinable_corpus.band_touch_count` reads `{"status": "enumerated", "count": <int>}`, never `{"status": "not_enumerated", "count": null}`. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/micro_join.py` — `enumerate_band_touches`/`_band_id` (the new
  band-touch enumeration primitive) — no direct UI surface; its only observable trace is the
  materialized count row already listed above.
- `apps/backend/app/research/scout.py` — `extract_anchors` dispatch
  (`_extract_none_anchors`/`_extract_band_touch_anchors`/`_extract_divergence_anchors`/
  `_extract_playbook_signal_anchors`), `_windowed_trade_volumes`, `_signal_in_dataset_window`,
  `_outcome_at_horizon`, `pilot_study_candidate_grid`, `register_screen_and_walkforward_check`,
  CLI `--grid` flag — pure backend research logic; feeds the Scout Ledger row already listed above,
  otherwise no UI surface.
- `apps/backend/app/research/walkforward.py` — `scout_candidate_walkforward_floor_check` — pure
  backend logic; its only visible trace is the walk-forward ledger row already listed above (it
  does NOT appear in the separate Walk-Forward section's own UI).
- `apps/backend/tests/test_micro_join.py`, `test_micro_readiness.py`, `test_scout.py`,
  `test_walkforward.py`, `test_micro_no_referee_evidence_guard.py` (new) — test-only, zero UI
  surface.
- Source-scan guard proving no `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py` module calls
  `strategy_trade_readiness`/`referee_evidence` — a code-hygiene guard with no rendered surface.

---

## Summary

- **Frontend surfaces changed:** 2 (Microscope Readiness section, Scout Ledger section — both
  already-shipped, no new section/page/heading)
- **New pages/routes:** 0
- **Modified components:** 2 (`MicroReadinessSection`, `ScoutLedgerSection` in
  `apps/frontend/app/desk/page.tsx`), plus 1 additive type widening (`lib/types.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 5 (band-touch enumerator, Scout anchor-extraction dispatch, pilot
  candidate grid + screen/floor-check chain, walk-forward floor check, guard/source-scan test)
