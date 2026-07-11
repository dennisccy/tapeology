# Phase goal-yahoo_fetch-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-yahoo_fetch-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required — this app has no authentication gate
- Nothing to seed yourself: symbol `AAPL` already has a stored `1d` bar series covering
  `2026-06-01T00:00:00Z`–`2026-06-04T00:00:00Z`, and symbol `TSLA` has zero stored bars. Both are
  pre-confirmed in this environment.

---

## Why this check matters

Nothing in the app changed this iteration — every step below exercises a feature that already shipped.
The point of this check is to confirm two things that were previously unproven: that the "Yahoo
Finance" data-source badge is actually readable (not hidden behind a dropdown), and that a symbol with
no data shows a clear, honest message instead of something broken-looking.

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser
   - **Expect:** The page loads with the heading "Structure", a "Fetch from Yahoo Finance" panel, and
     a second form below it with a "Load" button. No error banner, no blank page.

2. In the "Fetch from Yahoo Finance" panel: type `AAPL` in "Symbol", choose `1d` in "Timeframe", type
   `2026-06-01T00:00:00Z` in "Start (UTC, ISO-8601)", type `2026-06-04T00:00:00Z` in "End (UTC,
   ISO-8601)", then click "Fetch from Yahoo Finance"
   - **Expect:** Within about a second, a real candlestick chart appears with at least two dashed
     level lines, and a "Confluence zones" panel below it shows at least one zone with a "Class A/B/C"
     badge and a score number.

3. Click the page heading text "Structure" at the very top of the page (this closes a
   symbol-suggestions dropdown that may have popped open on its own after step 2)
   - **Expect:** A small dark chip directly above the chart reads "feed" then "Yahoo Finance", fully
     legible with nothing overlapping it.

4. In the second form (the one with the "Load" button — not the fetch panel above it), type `TSLA` in
   "Symbol", type `2026-06-05T00:00:00Z` in "As-of (UTC, ISO-8601)", then click "Load"
   - **Expect:** The text "No bar series recorded for TSLA." appears, with "Recording historical bars
     needs provider credentials." below it. No chart appears.

5. In that same form, change "Symbol" back to `AAPL` (leave "As-of" as `2026-06-05T00:00:00Z`), then
   click "Load" again
   - **Expect:** The chart and confluence zones reappear immediately — this is the original Load
     feature, unrelated to the new fetch panel, and it still works exactly as before.

6. Refresh the page (F5 or Cmd+R)
   - **Expect:** The page resets to the prompt "Choose a symbol and an as-of time, then Load, to see
     its S/R levels and confluence zones." This is expected — the page does not remember your last
     view across a refresh.

7. Repeat step 5 (type `AAPL` in "Symbol", keep `2026-06-05T00:00:00Z` in "As-of", click "Load")
   - **Expect:** The exact same chart and zones reappear instantly — proving the AAPL data was really
     saved on the server, not just remembered by your browser tab.

---

## What "Working Correctly" Looks Like

- The "Yahoo Finance" badge is fully readable in step 3, with nothing drawn on top of it
- TSLA shows a plain, clearly-worded "no data" message in step 4 instead of a blank or broken-looking
  chart
- The old "Load" button still pulls up a real chart for AAPL both before and after a refresh (steps 5
  and 7)

## If Something Looks Wrong

- **Badge still covered by a dropdown in step 3**: click a second time, further away from either
  "Symbol" field (e.g., directly on empty page background between the two forms), then look again
- **Blank page or errors everywhere**: the backend at `http://localhost:8301` is probably not running
  — this guide cannot proceed until it is
- **TSLA shows a real chart in step 4**: this would mean TSLA is no longer empty in this environment —
  open `http://localhost:8301/research/bars?symbol=TSLA` in a new tab; if it no longer shows
  `"bar_series":[]`, pick a different symbol confirmed empty by that same check and substitute it in
  step 4
