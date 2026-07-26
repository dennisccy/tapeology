# Iteration 4 — Coherence Audit

**Iteration:** goal-desk-iter-4
**Date:** 2026-07-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->
<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->
<!-- COHERENCE-FAIL: ≥1 objective violation; blocks GOAL_ACHIEVED, forces a consolidation iteration -->

No objective Data Contract or Information Architecture violation was found. `/desk` realizes the
pre-planned "Desk" nav home exactly as registered, reads all four canonical endpoints (screen,
screen/compute, topup/compute — no fifth), and introduces zero unregistered values (`reused`/
`screen_id` were pre-registered in blueprint.md's "RESOLVED at iter-4" note before the build).
Advisory items below are documentation-currency drift and one internal (never user-visible)
inconsistency inside the single `bars.py` owner — none of them meet the FAIL bar.

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows, skip rows | OK | `apps/frontend/app/desk/page.tsx:653` (`fetchDeskScreen` → `GET /research/desk/screen`, the ONLY fetch of this value); rows rendered in served order, `DeskRowsTable` at `page.tsx:212-245` never re-sorts or recomputes `band_class`/`distance_bps`/`band_score` |
| Screen compute progress (incl. new `reused`/`screen_id`) | OK | `apps/backend/app/research/desk_screen_compute.py:81-120,360-418` — same `DeskScreenComputeManager`, same two routes (`desk_routes.py:285-340`); `reused`/`screen_id` pre-registered in `runs/goal-session-desk/state/blueprint.md` lines 110/1794 as this iteration's additive amendment before the build, matching the iter spec's "Data-contract additions" field |
| Top-up compute progress | OK | `apps/frontend/lib/api.ts` new `triggerDeskTopupCompute`/`fetchDeskTopupCompute`/`cancelDeskTopupCompute` hit `/research/desk/topup/compute*` only — zero shape change, first-ever UI consumer per blueprint row |
| Bands / tradable-map scores, Levels/zones | OK | `/desk` never calls `/research/tradability` or `/research/levels` directly — `band_class`/`distance_bps`/`band_score`/`price_low`/`price_high` are read verbatim off the screen row (already resolved server-side by `desk_screen.py`'s registered `_select_best_band`); no client fetch, no client recompute |
| Bar coverage index / per-timeframe freshness | OK (advisory below) | `DeskCoverageBadges` (`page.tsx:115-140`) renders each row's own embedded `coverage` object verbatim — no live re-fetch of `GET /research/desk/coverage` from the desk page, matching the registered Note |
| Route / nav inventory (`UI_ROUTES`, now 3 rows) | OK | `apps/backend/app/meta.py:31-35` appends `{"path": "/desk", "label": "Desk", "nav": True}` as the third tuple entry — single owner, `test_meta_routes.py` widened in the same commit |
| Bars / candles (`BarStore`, unchanged-owners row) | OK, contract intact; documentation stale (advisory) | `apps/backend/app/research/bars.py:88-100,614-628` — the priceless-bar rail is a change WITHIN the same single canonical module/endpoint pair (`GET /research/bars`, `GET /research/candles`), explicitly sanctioned by the iter-4 spec's OUT-OF-SCOPE "zero-diff constraint is LIFTED for the priceless-bar rail only" clause; no second computation, no non-canonical endpoint |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` (new page, J-04) | OK | `apps/frontend/components/NavBar.tsx` (byte-unchanged this iteration) renders links purely from `GET /meta/ui-routes`; confirmed the array now yields `[{"/","Cockpit"},{"/structure","Structure"},{"/desk","Desk"}]` via `apps/backend/app/meta.py:31-35` and `test_meta_routes.py`'s widened assertions — 1 click from any page, no hardcoded nav edit |
| `/desk` shell | OK | `apps/frontend/app/layout.tsx` mounts `<NavBar/>` once at the root; `apps/frontend/app/desk/page.tsx` has no sibling `layout.tsx` and renders no competing nav/shell — inherits the established shell, not a parallel one |
| `/desk` home assignment | OK | Realizes the pre-planned "Desk" row already in blueprint.md's Navigation skeleton / Feature-journey-homes table (iter-1's baseline registration) — this iteration does not invent a new IA slot, matching the spec's own "Blueprint conformance" field |
| `StructureChart.tsx` finite-value guard (kept-surface edit) | OK (advisory below) | `apps/frontend/components/StructureChart.tsx:92-109,181-183` — a defensive filter (drop non-finite rows before `setData`) explicitly sanctioned by the iter-4 spec's OUT-OF-SCOPE clause ("Requires sanctioning a kept-surface edit... identical output for all-finite data"); not a new page, not a duplicate home, not a parallel shell — a scoped bugfix to an existing surface |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **blueprint.md's "Bars / candles" Data Contract row is now stale.** `runs/goal-session-desk/state/blueprint.md`'s unchanged-owners table still reads "unchanged; coverage reads the derived `bar_index`, never re-hashes this store" for the `bars.py`/`BarStore` row, but this iteration did change `bars.py` (the `NonFiniteBarPriceError` write-path refusal + the `_merged_rows` read-side exclusion, `apps/backend/app/research/bars.py:88-100,205-241,614-628`), under a scope-lift the iter spec itself logged in OUT OF SCOPE. The single-owner/single-endpoint contract was not broken, but the blueprint's Notes column should be amended next iteration to record the lift (mirroring how the "Bands/tradable-map scores" row above it already got an "iter-4 renders these fields" note in this same edit) — otherwise a future iteration or auditor may wrongly assume `bars.py` is still fully zero-diff.
- **blueprint.md's `/structure` IA description is now slightly inaccurate.** The Navigation-skeleton entry for Structure still reads "UNCHANGED this era except J-05's additive `?symbol=&asof=` Load-form prefill + auto-Load (no other behavior change)" (`blueprint.md` line ~46), but this iteration's audit-B1 fix pass also added a finite-value guard + a new visible message (`data-testid="structure-chart-undrawable-rows"`, `StructureChart.tsx:1273-1280`) to the SAME kept surface — a second, distinct sanctioned exception the line no longer names. Recommend appending a clause noting the audit-B1 exception the next time this row is touched.
- **Internal (not user-visible) inconsistency inside the single `bars.py` owner, flagged by this iteration's own audit as B2.** The merged-candles read (`BarStore._merged_rows`, backing `GET /research/candles` — what both chart pages use) now excludes non-finite-priced rows and reports them in `integrity_errors`; the per-series read (`BarStore.candles`, backing `GET /research/bars/{bar_series_id}/candles`) does not, and still serves a `null` price for the 60 already-recorded series holding one priceless row each. This is not a Data Contract violation today because `fetchBarCandles` has no UI caller (`apps/frontend/lib/api.ts`), so no two displayed values currently disagree — but if a future iteration wires that per-series route into a page, it would re-introduce the exact `null`-price crash this iteration just fixed on the merged path. Worth closing (one line, applying `_has_finite_prices` to the per-series read too) before any UI consumer is added.
- **`reports/phase-goal-desk-iter-4-ui-surface-map.md` is stale relative to the shipped code.** Its Provenance-panel row still lists "Window last requested" as the fifth labeled value; the actual shipped `/desk` (`apps/frontend/app/desk/page.tsx:386`, per the iter-4 fix-pass audit finding F1) labels that same field "Bar-store signature" with a checksum caption, moving the "window last requested" label to the per-timeframe coverage-badge tooltip only. This is a report-hygiene note, not a coherence violation in the running app — the audit handoff (`docs/handoffs/goal-desk-iter-4-audit.md` §4 item 2) already caught and fixed the equivalent staleness in the iteration spec's own TC-4; this report was left un-amended.
- **Bar-index vs. merged-candle count divergence for the 60 priceless-row-affected series (audit finding B3) is disclosed on-screen, not hidden.** `/desk`'s `desk-coverage-divergence-note` (`page.tsx:216-224`) already explains that a ranked row's coverage badges (from `bar_index`) and its rank (from the merged bar-store read) are two independent reads that can honestly disagree for an affected pair — this is the correct "no fabricated data" posture given the two values are intentionally separate Data Contract rows, not a coherence defect.
