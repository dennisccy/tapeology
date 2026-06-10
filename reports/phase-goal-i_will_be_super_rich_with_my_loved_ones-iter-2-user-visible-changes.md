# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-2 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Declare a thesis on a watched ticker by clicking the "Declare thesis" button in the new thesis strip on `/`, which sits between the price chart and the panel grid.
- Choose a setup type (absorption reversal, trend continuation, level break-and-go, or failed-move fade) and a direction (long or short) from a form whose options are populated live from the backend catalog — no labels are hardcoded on screen.
- Enter an invalidation price and, for setups that require it (level break-and-go, failed-move fade), an additional level price — the level field appears only when the chosen setup demands it.
- Read explicit inline rejection messages when a declaration is refused: wrong-side invalidation, missing or forbidden level price, second thesis while one is already active (409), and thesis on an unwatched ticker (404) are each surfaced verbatim in rose text beneath the form without creating anything.
- Watch the active thesis's expected-behaviour statements update in real time (met / not yet / violated) as the live tape changes, with each statement carrying a coloured dot: emerald for met, slate for not yet, rose for violated.
- See the "Pending" verdict badge on an active thesis (the verdict-transition engine that moves it through other verdicts arrives next iteration).
- See the data source and feed (SIM / SIP / IEX) that the thesis was declared on, giving the user a clear provenance stamp.
- See an honest "Monitor unavailable" warning if the backend monitor fails — the live tape feed continues unaffected, and the user is told the statement statuses may be stale rather than seeing silently stale data.

---

## What Changed in the Visible UI

- A new thesis strip section now appears on `/` between the price chart and the panel grid whenever a settled (live) snapshot is active. It is not shown while the stream is connecting, waiting, or failed.
- When idle, the strip is a single horizontal bar with the text "Declare a thesis on this ticker to watch the tape judged against it." and a "Declare thesis" button — no other element on the cockpit moves or reflows.
- When the declare form is open and the taxonomy is loading, the strip shows "Loading the setup catalog…" explicitly; if the catalog cannot be fetched it shows a rose error line and a Close button — never a fabricated form with guessed values.
- When an active thesis exists, the strip expands to show: the setup name, direction (emerald for long, rose for short), invalidation price in monospace, an optional level price in monospace, a bulleted list of expected-behaviour statements each with a live status dot and label, a slate "Pending" verdict badge, and a footer line with the bound source and feed stamp plus the disclaimer "Descriptive only — not trading advice."
- The "Declare" submit button shows "Declaring…" while the POST is in flight, and is disabled during submission to prevent double-submission.
- The "Cancel" button in the open form dismisses the form and preserves no pending declaration.

---

## What Old Behavior Changed

- Live stream frames: the WebSocket frame on `/tape/{ticker}/stream` now carries an additional `thesis` key (the active thesis projection or `null`). The existing tape values — state, confidence, features, quote, trades, event log — are byte-for-byte unchanged whether a thesis exists or not. Existing displays of those values are unaffected.

---

## Not Visible Yet

- The verdict badge is always "Pending" this iteration by design. The verdict-transition engine (confirming / weakening / rejecting / invalidated) that moves a thesis through other verdicts is the next iteration.
- Entry risk flags are intentionally omitted from the thesis display — no empty placeholder is shown, because an empty list would falsely read as "no risks found." Arrives in a later iteration.
- The journal database stores additional tables (hints, actions, studies, study_occurrences) that are created on first start but not yet written to or surfaced in the UI. These tables back future iterations' research surfaces.
- The `GET /research/thesis/active?ticker=` REST endpoint exists and returns the verbatim thesis projection, but the UI reads the thesis from the live WebSocket frame rather than polling this endpoint. The endpoint is available for external probes and integration tests but has no dedicated UI entry point.
- The `/journal` and `/studies` pages, and any navigation links to them, are out of scope for this iteration and do not yet exist.
