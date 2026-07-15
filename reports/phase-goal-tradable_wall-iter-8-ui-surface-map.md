# Phase goal-tradable_wall-iter-8 — UI Surface Map

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Cockpit) | `PriceChart` — tradable-band fetch effect, feeding the `confluence-chip` and the band overlay lines (Sim/Historical modes only) | Changed behavior | Closes iter-7 audit finding F1: the fetch effect now early-returns and stays in its `loading` phase (issuing no HTTP request) until `history.epoch_anchor` is known, instead of falling back to `new Date().toISOString()` (the browser's wall-clock date) | Open DevTools → Network, filter on `research/tradability`. Watch a historical-replay ticker (e.g. AAPL for the 2026-06-22 session) from a cold page load. Confirm the FIRST `research/tradability` request fired (if any fires before the network tab is ready) already carries an `as_of` resolved to the replayed session's own prior date (e.g. `2026-06-18`), never today's real-world date. Visually confirm the `confluence-chip` element and the band price-lines never flash into view then immediately change within the first second after clicking Watch. Also re-verify a SIM ticker (e.g. `SIM-BUYER`) still shows the `no-tradable-map` element with the text "No tradable map for {ticker}." — confirming this fix did not regress the SIM honest-empty-state. |
| `/structure` | Case Studies → row drill-in panel (`case-drillin` / `case-drillin-tape-timeline` / `case-drillin-tape-timeline-empty` test ids) | Changed behavior — data-only (no code in this component changed this iteration; the underlying `enrich_with_tape_timeline` join was built in an earlier iteration and is untouched) | The operator's 11 newly recorded real tick datasets let the pinned AAPL 2026-06-22 event's tape-timeline join resolve real entries instead of the honest-empty state | In Case Studies, set the Symbol filter input (`case-studies-filter-symbol`) to `AAPL`, locate the row for session `2026-06-22` (band price range ≈ 300.17–302.27), and click it. Wait for the "Case Studies — drill-in" panel's loading skeleton (`case-drillin-loading`) to resolve — this can legitimately take several minutes (a full tick-by-tick replay runs on every click, nothing is cached). Once resolved, confirm the `case-drillin-reaction` field reads `rejected`, both forward-return values are negative, and the "Tape timeline" list (`case-drillin-tape-timeline`) shows multiple dated entries with state names (`buyer_control` / `seller_control` / `bid_absorption` / `ask_absorption`) — NOT the `case-drillin-tape-timeline-empty` "No recorded tape for this event." text. |
| `/structure` | Edge Report panel (`EdgeReportBody`; test ids `edge-report-loading`, `edge-report-cell-row`, `edge-report-insufficient-sample`) | Changed behavior — data-only (no code in this component changed this iteration); **completion was NOT observed in a browser during this iteration** | The operator's 11 newly recorded datasets all independently cross-reference to a classified scan event, so the existing 3-way strategy-comparison report should have real rows to render instead of the previously fully-empty shape | Open `/structure` and observe the Edge Report panel. If it shows its pulsing `edge-report-loading` skeleton, allow substantial time — this endpoint has no caching and a full computation over the current real dataset volume was measured/estimated at "on the order of 10+ hours" on a cold backend process; a long wait alone is not a failure. Once it resolves, confirm at least one row with test id `edge-report-cell-row` shows a real (non-placeholder) `n` count, and any row with `n` below 5 shows the inline `edge-report-insufficient-sample` badge reading "insufficient sample (n < 5)" rather than being hidden or blank. Confirm the train and hold-out splits render as two separate tables (never merged into one). |

<!-- Change Type key used above: Changed behavior. No new page, new component, new form, new table, new modal, removed element, or navigation change was shipped this iteration. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_price_chart_confluence.py` — test-only correction (module docstring bullet 2, and the assertions inside `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`) so the test suite accurately describes the shipped `PriceChart.tsx` behavior (deferred fetch, no wall-clock fallback) instead of a stale pre-iteration description that QA had been observed echoing verbatim in the iter-7 report. This is a test file — it never ships to users — no UI surface affected.
- No backend production or frozen file changed this iteration: `config.py`, `tradability.py`, `setups.py`, `edge_report.py`, `levels.py`, `backtests.py`, the tape engine, and the adapters (including the Alpaca adapter) are all byte-identical to iter-7; `config_fingerprint` is unchanged at `4d665603569b9dbf`. The newly-visible Case Studies/Edge Report content described in the table above comes entirely from the operator's out-of-band recorded datasets (`apps/backend/.data/datasets/`, gitignored, not part of this diff) flowing through these already-existing, unmodified read paths — not from any new backend code shipped this iteration.

---

## Summary

- **Frontend surfaces changed:** 3 (1 code-driven, 2 data-driven)
- **New pages/routes:** 0
- **Modified components (code):** 1 (`PriceChart.tsx`)
- **Data-only surface changes (no code diff):** 2 (Case Studies drill-in, Edge Report — both fed by the operator's newly recorded datasets through pre-existing, unmodified endpoints)
- **Navigation changes:** no
- **Backend-only changes:** 1 (`test_price_chart_confluence.py`, test-only)
