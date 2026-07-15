# Iteration 6 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-6
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Diff scope confirmed via `git diff 78c4143c..HEAD --stat`: only `apps/backend/app/research/setups.py`
(+ its test file), `apps/frontend/app/structure/page.tsx`, `apps/frontend/components/StructureChart.tsx`,
`apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts`, and `README.md` changed. `routes.py`,
`tradability.py`, `edge_report.py`, `levels.py`, `strategies.py`, `backtests.py`, `config.py`,
`datasets.py` are absent from the diff (verified with a targeted `git diff --stat` against those
paths — empty output) — the DoD's "every frozen backend file is absent from the diff EXCEPT the
scoped `setups.py` cache hardening" holds.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Tradable level map bands (range, side, class, quality_score, member_count, round_number, basis_as_of) | OK | Canonical: `apps/backend/app/research/tradability.py:321` `compute_tradability`, served by `apps/backend/app/research/routes.py:1814` `get_tradability` (both untouched this iteration). New consumer: `apps/frontend/app/structure/page.tsx` `BandRow`/`BandsTable` (added ~L243-300) render `band.side`/`price_low`/`price_high`/`class`/`quality_score`/`member_count`/`round_number` via `String(...)` verbatim off `fetchTradability`'s response; `StructureChart.tsx:94-118` overlay reads the same fields verbatim to draw price lines. No clustering/scoring logic added client-side. |
| Touch events + reaction + forward returns + recency-boundary fields | OK | Canonical: `apps/backend/app/research/setups.py` `compute_setups`, served by `routes.py:1851` (`/setups`) and `:1892` (`/setups/{id}`). New consumer: `page.tsx` `SetupRow`/`SetupDrillIn`/`ForwardReturnsList` (added ~L308-452) render `event.reaction`, `event.forward_returns[].return_fraction`, `event.effective_reaction_horizon_bars`, `event.reaction_boundary_truncated` verbatim; the boundary note text embeds the served number into a sentence, it does not derive a new one. Case Studies symbol/reaction filter (`page.tsx` ~L812-821, `filteredSetupsEvents`) is a client-side equality filter over the one already-fetched, unfiltered list — the same class of operation as the pre-existing `bar_series.filter((s) => s.symbol === ...)` precedent, not a recomputation. |
| Tape-at-the-wall timeline (J-03 join) | OK | Canonical: frozen `TapeEngine`, joined verbatim inside `setups.py`'s detail read, served by `GET /research/setups/{id}`'s `tape_timeline`. New consumer: `page.tsx` `TapeTimelineList` (added ~L368-391) renders `entry.timestamp`/`entry.state`/`entry.confidence` verbatim; empty list renders the distinct honest `case-drillin-tape-timeline-empty` state rather than fabricating an entry. |
| Edge-report cells (n, R, $, win_rate, insufficient_sample, register) | OK | Canonical: `apps/backend/app/research/edge_report.py` `run_strategy_comparison_report`, served by `routes.py:2076` (`/edge-report`, untouched). New consumer: `page.tsx` `EdgeReportCellRow`/`EdgeReportMeasurementCells`/`EdgeReportBody` (added ~L461-668) render `cell.measurement.*`, `cell.insufficient_sample`, `report.register` verbatim; `isEmpty` (`train.cells.length === 0 && holdout.cells.length === 0`) is a UI-state derivation from served array shapes for choosing which honest-empty state to show, the same class as the pre-existing `levels.levels.length === 0` check — not a recomputation of any registered figure. `SurvivingCellRow`'s "clears the gate" text reads the server's own `survivor.holdout_positive_edge` boolean, it does not compute the gate. |
| B3 process-local scan cache (`_SCAN_CACHE`, accelerator behind `compute_setups`) | OK | `apps/backend/app/research/setups.py:351-410` (per the reviewed diff): the two-key mutable-dict publish (`_SCAN_CACHE["key"]=`, then `["result"]=`) is replaced with one atomic `(key, result)` tuple rebind under a single `global _SCAN_CACHE` assignment. `compute_setups` itself, `_run_full_panel_scan`, and every field it returns are byte-for-byte unchanged — confirmed by the new `test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes` (structural guard) and `test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair` (16-thread behavioral proof) in `apps/backend/tests/test_setups.py`. Remains what the blueprint's own Data Contract entry already calls "a rebuildable accelerator ... never a second source of truth" — `setups.py` stays the single computer. |

No new displayed value is missing from the Data Contract — the iteration spec's own "Data-contract
additions: None" claim checks out against the diff: every field rendered by the three new sections
traces to a field already named in one of the three registered Era-5B rows above.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Tradable Map (J-01 default view) | OK | `apps/backend/app/meta.py:30` (`{"path": "/structure", "label": "Structure", "nav": True}`) and `apps/frontend/components/NavBar.tsx` (renders `GET /meta/ui-routes` verbatim) — both absent from this iteration's diff, confirming the nav is unchanged. The section lives inside the already-registered `/structure` home (blueprint IA row "J-01 Tradable level map → `/structure` → Tradable Map (default view)"), reached via the existing single top-nav link — 1 click, unchanged from before this iteration. |
| Case Studies + drill-in (J-02/J-03) | OK | Same `/structure` page, same nav link. Matches blueprint IA rows "J-02 Case-study registry → `/structure` → Case Studies table + row drill-in" and "J-03 ... shown inside the Case Studies drill-in (tape timeline)" exactly — `page.tsx`'s new `<section aria-label="Case studies">` (~L1061) and `SetupDrillIn`'s tape-timeline block. |
| Edge Report (J-04) | OK | Same `/structure` page, same nav link. Matches blueprint IA row "J-04 Edge report → `/structure` → Edge Report section" — `page.tsx`'s new `<section aria-label="Edge report">` (~L1158). |
| Raw-levels toggle / declutter (J-05, this iteration's own target) | OK | Same `/structure` page. `showRawLevels` state defaults to `false` (`page.tsx` ~L684, `useState(false)`), gating the pre-existing "Levels and zones" section (~L976-1056), whose inner JSX is textually identical to the pre-iteration block removed at the diff's old L1236-1313 (verified line-by-line — same testids, same copy, same components, only re-indented one level inside the new conditional). Matches blueprint IA row "J-05 `/structure` declutter (map default, raw behind toggle) → `/structure`." |
| Fetch-from-Yahoo control, provenance badge, Registry, Comparison (era-4/5 foundation) | OK | Repositioned only (moved below the three new sections per the DoD's explicit instruction); confirmed unchanged apart from one copy line referencing the new section names above them. No new route, no removed route. |

No new top-level route was added (confirmed against both `git status --short` and `git diff --stat`:
the only frontend files touched are `page.tsx`, `StructureChart.tsx`, `lib/api.ts`, `lib/types.ts` —
no new file under `apps/frontend/app/`). No parallel shell — every new section reuses the page's
existing `Panel`/`EmptyState`/`LoadingPanel`/`UnavailablePanel` components and layout conventions
(e.g. `EdgeReportCellRow`'s `insufficient_sample` badge explicitly reuses the `BacktestClassTable`
copy/precedent already on this page). No duplicate home — each of J-01/J-02/J-03/J-04/J-05 lands in
exactly the single canonical `/structure` home the blueprint already assigned it; nothing here
invents a second location for an entity that already had one.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. (Checked and ruled out as non-issues rather than omitted: (1) a null `band.class` renders the
label "Unclassified" in `BandRow` — this is a distinct, newly-introduced null state on a field the
type contract itself documents as legitimately nullable, `TradabilityBand.class`, not a relabeling of
any existing non-null convention such as `ZoneRow`'s always-present `Class {zone.class}` badge, so
there is no labelling drift to flag. (2) `fetchSetups()` is invoked with zero arguments — filtering
is done entirely client-side over the one unfiltered fetch — even though `lib/api.ts`'s `fetchSetups`
signature also accepts optional `symbol`/`reaction`/`band_class` query params; the iteration spec
explicitly sanctions either approach ("the endpoint's optional filter params, or a display-filter of
served rows"), so the unused param capability is not a coherence concern.)
