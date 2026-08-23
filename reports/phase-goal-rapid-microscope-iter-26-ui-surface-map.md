# Phase goal-rapid-microscope-iter-26 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/micro_readiness.py` | backend-internal → backend-api (indirect) | indirect | Adds `MicroBandTouchCache` + `resolve_micro_band_touch_cache_db_path`; `build_readiness` gains an optional `band_touch_cache` param. Frontend already consumes `build_readiness`'s output via `GET /research/desk/micro/readiness`, so this is reachable from the UI, but the served field (`joinable_corpus.band_touch_count`) is unchanged — only warm-path latency. |
| `apps/backend/app/research/micro_join.py` | backend-internal → backend-api (indirect) | indirect | `joinable_corpus_counts` gains an optional `band_touch_cache=None` keyword param, used by the same readiness route above. Same field, same value, cache is purely an internal lookup-or-compute layer. |
| `apps/backend/app/research/micro_routes.py` | backend-api | indirect (regression-relevant only) | (a) New `get_micro_band_touch_cache` FastAPI dependency wired into `GET /research/desk/micro/readiness` — response schema unchanged. (b) `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` replaced by a single `_pilot_selectors_by_kind(kind, source=None)` derivation, used inside `trigger_scout_compute` (the `POST` handler behind the Scout Ledger's "Run Screen" button). Classification decisions are unchanged (same selector sets), so the Scout Ledger section's rendered rows are unaffected. |
| `apps/backend/tests/test_micro_readiness.py` | backend-internal (test) | none | Unit tests only, not reachable from any UI surface. |
| `apps/backend/tests/test_micro_join.py` | backend-internal (test) | none | Unit tests only, not reachable from any UI surface. |
| `apps/backend/tests/test_scout.py` | backend-internal (test) | none | Unit tests only, not reachable from any UI surface. |
| `docs/handoffs/goal-rapid-microscope-iter-26-dev.md` | docs | none | Handoff document, not shipped UI. |

No `.tsx`, `.jsx`, `.css`, or other frontend file changed this iteration (`git diff --stat` against
`apps/frontend/` is empty for this iteration's diff).

---

## Affected UI Surfaces

<!-- Both rows below are REGRESSION-ONLY: the backend change is purely a caching/dedup layer behind
an existing endpoint. Neither surface gained, lost, or altered any rendered field, label, or control
this iteration. "What to Test" proves the served values stayed byte-identical, not that anything new
appeared. -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | "Microscope Readiness" section (`MicroReadinessSection`, `data-testid="micro-readiness-section"`), specifically the "Joinable corpus — band touches" row (`data-testid="micro-readiness-band-touch-count"`) inside the "Sealed Tranche (Aggregate Only)" block | Changed behavior (performance only, no display change) | `GET /research/desk/micro/readiness`'s band-touch count is now served from the new `MicroBandTouchCache` SQLite cache instead of re-scanning raw tick data on every request | Navigate to `http://localhost:3301/desk`, click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`) to expand it, read the "Joinable corpus — band touches" value, then collapse and re-expand the same section a second time — verify the value is identical both times and the "Corpus Totals" table (distinct symbol-days, distinct datasets, RTH minutes covered, session-equivalents, referee tick-gate symbol-days) is unchanged from the pre-iteration baseline recorded in `runs/goal-session-rapid-microscope/state/journey-history.json`'s J-01 note (2 distinct symbol-days, 3 datasets, 1.75 RTH minutes covered, 0.0045 session-equivalents, referee tick-gate 150 — QA fixture rig values) |
| `/desk` | "Scout Ledger" section (`ScoutLedgerSection`, `data-testid="scout-ledger-section"`), specifically each pilot-study family's header line ("`{family_id}` (root `{family_root_id}`) — `{variants_tried}` variants tried") | Changed behavior (internal dedup, no display change) | `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` are now derived from the single canonical `scout._PILOT_GRID_SELECTORS` table instead of a duplicated hand-written literal, inside the code path behind the "Run Screen" button | Navigate to `http://localhost:3301/desk`, click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`) to expand it, and verify each pilot-study family row still shows the "— N variants tried" text and the same trial-row columns (Candidate / Feature / Horizon / Registered / Decision / Reason / Notes / Withheld excluded / Screen detail) as the pre-iteration render — no family, row, or column should be missing or reordered |
| `/desk` | "Microscope Readiness" and "Scout Ledger" section toggle controls (`data-testid="desk-section-expand-microReadiness"` / `desk-section-expand-scoutLedger"`) | Unchanged (regression check only) | Confirms the collapse/expand mechanism and deferred-fetch-on-first-expand behavior still work identically after the cache/dedup change | With both sections collapsed (page freshly loaded), click "Microscope Readiness" — verify the section body mounts and its `aria-expanded` attribute flips to `"true"`; click it again — verify the body unmounts and `aria-expanded` flips back to `"false"` without re-fetching (no visible flash of a loading state on re-expand) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/micro_readiness.py` — new `MicroBandTouchCache` class (composite-key
  SQLite cache table keyed on `(checksum, map_key)` → `touch_count`) and its
  `resolve_micro_band_touch_cache_db_path` env-driven path helper — purely an internal storage layer;
  no new or changed field in any response the frontend reads.
- `apps/backend/app/research/micro_join.py` — `joinable_corpus_counts`'s optional
  `band_touch_cache` parameter and its lookup-or-compute-and-publish logic — internal to the
  count computation, the returned count is unchanged.
- `apps/backend/app/research/micro_routes.py` — `get_micro_band_touch_cache` FastAPI dependency
  construction — internal wiring, not a new endpoint or new response field.
- `apps/backend/app/research/micro_routes.py` — `_pilot_selectors_by_kind(kind, source=None)`
  derivation function replacing two hand-written frozensets — internal decision logic behind
  `trigger_scout_compute`; the selector sets it produces are unchanged from before, so classification
  outcomes are identical.
- `apps/backend/tests/test_micro_readiness.py`, `apps/backend/tests/test_micro_join.py`,
  `apps/backend/tests/test_scout.py` — new unit tests for the above; test-only, no UI surface.

---

## Summary

- **Frontend surfaces changed:** 0 (2 existing surfaces regression-verified: Microscope Readiness,
  Scout Ledger)
- **New pages/routes:** 0
- **Modified components:** 0 (`.tsx` files: none changed)
- **Navigation changes:** no
- **Backend-only changes:** 5 files (`micro_readiness.py`, `micro_join.py`, `micro_routes.py`, plus
  `test_micro_readiness.py` and `test_micro_join.py`; `test_scout.py` also touched but shares the
  same no-UI-impact classification)
