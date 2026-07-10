# Phase goal-yahoo_fetch-iter-5 — User-Visible Changes

**Phase:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On `/structure`, pick a symbol, a timeframe (choices: 1w, 1d, 4h, 1h, 5m, 1m), and a start/end UTC date range, then click **"Fetch from Yahoo Finance"** to pull real historical price bars into the app — no account, API key, or cost required. This is the first place in the app where a person can trigger a real historical-data fetch by clicking a button, rather than it happening only through a background process.
- Immediately after a successful fetch, see the real candlestick chart, the computed support/resistance level lines, and the A/B/C confluence-zone table populate automatically for that data — without a second, separate "Load" click.
- See a **"Yahoo Finance"** badge appear directly above the chart, confirming where the currently displayed price data came from.
- Click "Fetch from Yahoo Finance" again for a symbol/timeframe/window that was already fetched before, and get the result back instantly from local storage instead of waiting on a new Yahoo request — repeating the same fetch never produces a "duplicate" error.
- When a fetch cannot be completed, see a specific, worded reason (e.g. an unsupported timeframe, no data available for the requested window, or the fetch service being unavailable) instead of a generic "something went wrong" message.

---

## What Changed in the Visible UI

- The `/structure` page has a new **"Fetch from Yahoo Finance"** panel above the existing read-only "Load" form. It contains: a Symbol field (the same searchable symbol box used elsewhere on the page), a Timeframe dropdown (six choices: 1w / 1d / 4h / 1h / 5m / 1m), Start and End text fields (UTC, ISO-8601 format), and the "Fetch from Yahoo Finance" button.
- The button is visibly disabled (greyed out) until all four fields have a value. While a fetch is in progress, its label changes to "Fetching…" and it stays disabled.
- A new "Yahoo Finance" badge (a small labeled pill) now appears directly above the price chart whenever a bar series is charted on `/structure`. This is the same badge component already used on the home page to label a live data feed — reused here for a fetched historical series instead.
- When a fetch fails, a distinctly-styled amber/degraded panel appears below the new fetch form, displaying the specific reason for the failure and the note "Nothing cached and nothing fabricated is shown in its place."
- The introductory paragraph at the top of `/structure` and its "framing" caption line just below it were reworded to mention the new fetch action, instead of describing the whole page as read-only.

---

## What Old Behavior Changed

- **`/structure` page description copy**: previously read "Read-only, in three sections: ... Every value below is read verbatim..."; now reads "One explicit write action — fetching bars from Yahoo Finance below — everything else on this page is read-only: ...". This is a wording-only change; the previously-existing Levels & Zones, Registry, and Comparison sections behave exactly as before.
- **The shared feed badge component**: previously shown only on the home/cockpit page (labeling a live watch's feed as "Simulated", "IEX (live)", or "SIP (consolidated)"), it is now also rendered on `/structure`. Its underlying type was widened so any feed name can be shown, not just those three — but its appearance and behavior on the home page are unchanged; this is additive reuse, not a modification of its original use.

---

## Not Visible Yet

- A correctness fix to `GET /research/bars`'s blank-parameter handling (an empty `?symbol=` now returns the exact same result as sending no parameter at all, instead of silently using a narrower lookup that could miss older un-indexed data) was made this iteration — but no control anywhere in the current UI ever sends a blank/empty symbol or timeframe value to that endpoint. The fix has no reachable trigger through the UI today; it guards against a request shape only a future UI change or an external API caller might send.
- Fetching a brand-new window that has never been fetched before — i.e. a real live round-trip to Yahoo's servers on a cache-miss, as opposed to instantly re-serving an already-stored window — was not exercised in this iteration's live/browser walkthrough. That network path was proven in an earlier iteration's automated tests, but is not re-demonstrated by this iteration's UI evidence.
