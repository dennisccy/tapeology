# Phase goal-i_will_be_super_rich-iter-7 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-7
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Pause a live or replaying watch by clicking the **Pause** button (amber, beside the existing **Stop** button in the top bar) — the cockpit, recent-trades list, feature counters, tape state, and prediction chart all freeze at the moment of the click, with the session kept alive (nothing is closed or cleared).
- Resume a paused watch by clicking the **Resume** button (replaces **Pause** in the top bar while paused) — the stream continues from where it left off; for simulated/historical replay, replay picks up at the exact position it stopped; for a live feed, the feed rejoins current real-time data with no fabricated catch-up trades shown.
- Stop a paused watch by clicking **Stop** — works exactly as before; the session is fully closed regardless of whether it was paused first.

---

## What Changed in the Visible UI

- The watch-control cluster in the top bar (the row showing "Watching [TICKER] … Stop") now shows a **Pause** button (amber text, amber border) whenever the feed is active (connecting / live / stale) and not yet paused.
- While paused, the **Pause** button is replaced by a **Resume** button (same amber amber styling).
- The stream-status dot and label in the top-right of the header now has a fourth state: **paused** (amber dot, "paused" label) — displayed while the watch is frozen. The dot reads "paused", never "live", while the session is frozen.
- All existing cockpit panels (quote, recent trades, feature counters, tape state) and the prediction chart below the top bar continue to display the frozen moment's data while paused — they do not clear, reset, or show a spinner.

---

## What Old Behavior Changed

- **Watch controls**: Previously, the only mid-watch action was **Stop** (which fully closed the session). Now there is also **Pause** (freeze without closing) and **Resume** (continue). **Stop** is unchanged — it still fully closes the session, including when called on a paused watch.
- **Stream-status indicator**: Previously showed connecting / live / stale / closed. Now also shows **paused** (amber) as a distinct honest state while a watch is frozen.

---

## Not Visible Yet

- The prediction chart (candlestick OHLC bars with tape-state markers, shipped in the previous iteration) is unchanged in this iteration. Its visual render has not been confirmed by browser screenshots yet — that confirmation is the browser-QA step's responsibility and is still pending for journeys J-17 and J-18.
- The local-time historical-window picker and US-session quick-picks (J-20) are not built yet — deferred to the next iteration.
