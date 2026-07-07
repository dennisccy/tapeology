# Iteration 1 — Coherence Audit

**Iteration:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| S/R levels (price / timeframe / type) | OK | `apps/frontend/lib/api.ts:861-882` (`fetchLevels` calls `GET /research/levels?symbol=&as_of=`, the sole registered endpoint) → `apps/frontend/app/structure/page.tsx:178-180` (`lvl.price`/`lvl.timeframe`/`lvl.type` rendered via `String()`, no arithmetic) → `apps/frontend/components/StructureChart.tsx:73-82` (level lines drawn from `level.price`/`level.timeframe`/`level.type` verbatim) |
| A/B/C confluence-zone class + score | OK | `apps/frontend/app/structure/page.tsx:143,148,151` (`zone.class` used directly for `data-zone-class` and the "Class {zone.class}" badge) and `:155-156` (`zone.score` via `String(zone.score)`) — no breadth/strength recomputation anywhere in the diff |
| Bar series + checksums (candles for the chart) | OK | `apps/frontend/lib/api.ts:891-902` (`fetchBarSeriesList` calls `GET /research/bars`, the sole registered endpoint) → `page.tsx:228-244` filters/selects among already-served `BarSeriesRecord` rows (by `symbol`, by timeframe-recency for `pickRepresentativeSeries`, by `ts <= as_of` for the chart window) — selection/filtering of served rows, not a new computed value (same discipline the blueprint already sanctions for `NavBar`'s `nav: true` filter) → `StructureChart.tsx:60-67` draws `b.open/high/low/close` verbatim |
| UI route map (the nav itself) | OK | `apps/backend/app/meta.py:30` adds exactly one additive tuple entry (`{"path": "/structure", "label": "Structure", "nav": True}`); the five pre-existing entries are byte-unchanged and in order (confirmed by diff + `test_meta_routes.py`'s updated exact-equality assertions); `apps/frontend/components/NavBar.tsx` is byte-unchanged (not in the diff) and still renders whatever `GET /meta/ui-routes` returns — no hardcoded client route list added |
| New value check | OK — no new owned value | Spec's "Data-contract additions: None" holds. The "representative series" display choice (`page.tsx:61-76`) selects among existing `BarSeriesRecord` rows for chart rendering; it introduces no new metric, price, class, or score — nothing to register |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` (J-01: levels + zones) | OK | Canonical home per blueprint's IA table (`/structure` → Levels & Zones section, Structure nav entry). Reachable in **1 click** from the persistent top bar: `apps/backend/app/meta.py:30` registers the entry, unmodified `apps/frontend/components/NavBar.tsx` renders it data-driven (no new nav file touched, no hardcoded `href="/structure"` — confirmed absent from the diff and independently by browser-qa's grep in `ui-test-results.md` UT-04). No duplicate home: no pre-existing route (`/`, `/journal`, `/studies`, `/performance`) displays S/R levels or confluence zones. No parallel shell: `apps/frontend/app/structure/page.tsx:246-248` uses the identical `<div className="min-h-screen"><main className="mx-auto max-w-7xl px-4 py-6">` wrapper as `apps/frontend/app/performance/page.tsx:216-217` and `apps/frontend/app/journal/page.tsx:120-121`, inside the single unchanged `apps/frontend/app/layout.tsx` root shell that already mounts `<NavBar/>` once for every page |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Out of this gate's scope, noted only for cross-reference:** `reports/phase-goal-structure_ui-iter-1-ui-test-results.md` and `reports/phase-goal-structure_ui-iter-1-ux-regression.md` record a browser-rendering FAIL (UT-10 — a CSS `z-index` stacking bug in `StructureChart.tsx` occluded the empty-chart hint). This is a rendering/visual defect, not a Data Contract or IA violation (no duplicate computation, no non-canonical source, no navigation problem) — it is the browser-qa/ux-regression lanes' finding to make, not this gate's. Per the current working tree, the fix is already applied (`StructureChart.tsx:99` carries `z-10`, per the audit handoff's finding F1) and does not touch any registered value or endpoint — reconfirmed here: the fix is CSS-only, `bars`/`levels` props and their rendering remain verbatim. `reports/phase-goal-structure_ui-iter-1-closure-verdict.md`'s `CLOSURE-FAIL` is about reconciling stale verdict lines across `status.json`/`ui-test-results.md`/`ux-regression.md` after that fix — a record-keeping/artifact-consistency concern, also outside this gate's Data-Contract/IA mandate.
- No unregistered-but-new values, no inconsistent labeling of the same entity, no formatting drift observed across the new surface (all numeric values render via unmodified `String(value)`, matching the `/performance` page's established precedent).
- `blueprint.md` required no edit for this iteration and none was made (no `blueprint.reapproval-requested` file present) — correct, since the nav skeleton was already approved with the `/structure` entry in place.
