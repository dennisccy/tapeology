# goal-i_will_be_super_rich_with_my_loved_ones-iter-10 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-10
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

Thesis chart geometry (capability 25, J-48) — the declared thesis is now drawn ON the price chart:
labeled invalidation/level price-lines at the declared prices, plus verdict-transition,
entry/exit, and first-confirmation markers at their times. Closes J-45's deferred level-line clause
and J-52's deferred chart-marks clause. Pure visualization of already-declared/recorded facts; no
new endpoint, no new user action, no schema change, no engine/history-buffer change.

- **Additive `geometry` key on the ONE row-15 thesis projection** (`build_projection`), computed
  once server-side from canonical owners only:
  - `price_lines` — invalidation (always; declared price verbatim) + level (ONLY when
    `level_price` is set), each with a backend-owned plain-language label (taxonomy module).
  - `markers` — (a) one per published **verdict transition** from the append-only timeline (pure
    projection of the appended rows — never recomputed/edited), each carrying verdict, `logical_ts`,
    `wall_ts`, the appended `last`, and the backend verdict label; (b) **entry/exit** marks (row-18
    `marks_projection`) at their recorded `logical_ts` with verbatim prices — present ONLY when the
    mark exists; (c) the **first-confirmation** marker — the first timeline event whose verdict is
    `confirming`, identified once.
  - **Honest segment rule** — only events on the CURRENT watch's logical timeline are drawn: rows
    after the latest `watch_restarted` gap (positional) and marks at/after that gap's wall time
    (`logical_ts` resets per watch, so `wall_ts` — monotonic across re-watches — discriminates
    pre/post-gap marks). Pre-gap events are omitted from the chart (still visible in the journal
    timeline). Price-lines are time-independent and always served. `watch_restarted` itself is a
    gap delimiter, never drawn as a verdict marker.
- **WS == REST parity for free** — geometry rides the same single projection, so the WS `thesis`
  key carries it verbatim; the existing parity test was extended to assert `geometry` byte-equal.
- **Backend-owned geometry labels** added to the taxonomy module (the single research-copy owner):
  `Invalidation`, `Level`, `Entry`, `Exit`, `First confirmation`, and a `verdict_marker_label()`
  reusing the `VERDICTS` enum. Frontend hardcodes none of them.
- **Timeline access stays canonical** — `build_projection` takes `verdict_events` (the thesis's
  append-only rows from the store) the same way it already took `actions`; all three callers (the
  live monitor, the mismatched-source survivor, the unwatched-survivor route) pass
  `store.verdict_events(thesis.id)`. The existing config-owned `verdict_timeline_cap` already bounds
  the rows; no new magic numbers.

## Files Changed
- `apps/backend/app/research/monitor.py` -- new pure `_build_geometry(thesis, verdict_events, marks)`; `build_projection` gains a `verdict_events` param and emits the `geometry` key; both monitor callers pass the store's timeline rows.
- `apps/backend/app/research/routes.py` -- the unwatched-survivor `build_projection` call passes `verdict_events`.
- `apps/backend/app/research/taxonomy.py` -- backend-owned geometry labels + `verdict_marker_label()`.
- `apps/backend/tests/test_research_geometry.py` -- NEW: 12 tests (price-lines, verdict-transition markers = appended rows exactly, first-confirmation = first confirming, no-marks honesty, segment rule, watch_restarted not a marker, survivor serves geometry, live monitor carries geometry).
- `apps/backend/tests/test_research_api.py` -- extended the REST==WS parity test to assert `geometry` byte-equal.
- `apps/frontend/lib/types.ts` -- `GeometryPriceLine`, `GeometryMarker`, `ThesisGeometry`; optional `geometry` on `ThesisProjection`.
- `apps/frontend/components/PriceChart.tsx` -- new `thesis` prop; draws price-lines (`series.createPriceLine`, dashed) and thesis markers via the existing series-marker mechanism, visually distinct from tape-state markers (BELOW the bar; circle for verdict/first-confirmation, arrow-up for entry/exit; verdict palette), placed on the SAME `epoch_anchor + logical_ts` the candles use; clears all overlay when `thesis`/`geometry` is null.
- `apps/frontend/app/page.tsx` -- passes `snapshot?.thesis ?? null` into `PriceChart`.

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **439 passed, 1 skipped** (the 1 skip is the credentialed live-feed integration test). Includes the new geometry suite, the extended WS/REST parity test, and the observer-equivalence suite (still green — nothing in this diff touches the engine).

Frontend: `npx tsc --noEmit` clean (lightweight-charts 5.2.0 API verified: `createPriceLine`/`removePriceLine`, `LineStyle.Dashed=2`, marker shapes `circle`/`arrowUp`/`arrowDown`, positions `belowBar`/`aboveBar`). `next dev` compiles and serves `/` => HTTP 200.

## Live verification (not mocked)
Ran a real declare -> mark-entry -> confirm flow against a freshly started backend (temp journal DB):
- Watched `SIM-BUYER`, declared `level_break / long` with level just above last and invalidation below.
- `GET /research/thesis/active?ticker=SIM-BUYER` returned `geometry.price_lines` = `[{invalidation, 100.91, "Invalidation"}, {level, 101.81, "Level"}]`.
- After the price crossed the level and confirmation published, `geometry.markers` carried the `pending` and `confirming` verdict-transition markers (with the appended `last`) and a `first_confirmation` marker at the first confirming `logical_ts`.
- After `POST /research/thesis/{id}/action {kind:entry}`, the action-route projection carried an `entry` marker with the verbatim price `103.80` and its `logical_ts` (so the action route, WS frame, and REST `/active` all serve geometry via the one builder).
- A never-declared ticker (`SIM-SELLER`) returned `thesis: null` — no geometry anywhere.
- Backend + temp DB cleaned up; no uvicorn/next processes left running.

## Known Issues
- The sim browser leg is one continuous watch, so the **segment rule** (pre-gap markers omitted on a re-attached thesis) is exercised by unit test, not by browser pixels — this matches the spec's documented assumption (re-attach pixels were iter-9's scope).
- The **live-mode chart render** is credentials/market-hours operator-gated per goal.md J-48; the same single `PriceChart` component renders all modes (sim/historical/live) with no mode-specific geometry code path, so the sim leg + the shared component is the browser evidence this iteration owes. Note it explicitly in QA results rather than skipping silently.
- The FULL-pipeline harness defect (engine halts at `qa_complete`) remains open upstream — depth stays lean per the evaluator; not introduced or affected by this iteration.
