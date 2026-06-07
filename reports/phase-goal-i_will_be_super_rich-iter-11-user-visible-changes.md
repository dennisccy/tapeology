# Phase goal-i_will_be_super_rich-iter-11 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Re-watch the same Historical symbol and window (same ticker, same date range, same data source) and see the cockpit populate near-instantly — the app remembers the already-fetched data and skips the vendor round-trip entirely.
- When a Historical window is too large or too high-volume to load within budget, read a clear, actionable error message on the existing failure panel: "that window is very high-volume — try a shorter range" — a specific instruction rather than a generic "please try again".
- Type in the symbol search box and see results appear without pile-up or out-of-order flicker, even when typing quickly; each new keystroke cancels any in-flight prior search request so only the latest result is ever shown.
- Start typing a symbol immediately after a backend restart without experiencing a multi-second stall — the symbol list is pre-loaded in the background at startup so the first search is fast.

---

## What Changed in the Visible UI

- The symbol search dropdown (`SymbolSearch` component on `/`) no longer shows stale results from a prior slower query when typing rapidly — a newer keystroke cancels the older request before it can overwrite the current result.
- The symbol search dropdown no longer fires a backend lookup for a single-character query; the minimum query length now matches what the backend enforces, so the dropdown remains empty until a meaningful query is entered.
- When a Historical Watch times out due to a high-volume window, the existing error/failure panel on `/` now shows the specific message "that window is very high-volume — try a shorter range" instead of a generic timeout message.
- A Historical Watch cockpit that is loading real past data now warms up quickly — the cockpit transitions to a meaningful read (tape state, confidence, features) sooner after the fetch completes, rather than waiting through the data's real timeline before showing a result.

---

## What Old Behavior Changed

- **Historical Watch timeout message:** previously showed a generic provider timeout message. Now shows "that window is very high-volume — try a shorter range" — a specific, actionable instruction that tells the user exactly what to change.
- **Re-watching the same Historical window:** previously re-fetched all trades and quotes from the vendor on every Watch submission. Now the app returns the result near-instantly from its in-process cache if the same symbol, date range, and data source were fetched before in the same session.
- **Symbol search while typing fast:** previously could display a slow earlier result on top of a newer one (out-of-order overwrite), because requests were only dropped late by a flag. Now the prior in-flight request is actively cancelled when a new keystroke fires, so only the result that belongs to the most recent query is ever shown.
- **First symbol search after backend restart:** previously triggered a live vendor lookup to build the symbol list, causing a visible stall on the first search. Now the symbol list is loaded in the background during startup, so the first search after a restart is served from the already-warmed list.
- **Historical cockpit warm-up pacing:** previously replayed warm-up events at the real data's logical pacing, which could delay the first meaningful read. Now the warm-up events are fast-forwarded in delivery so the cockpit shows a warm state sooner. The tape values themselves (state, confidence, features, prices) are exactly the same — only how quickly the warm-up events are delivered changed.

---

## Not Visible Yet

- The backend now enforces a real HTTP-level deadline on every vendor call inside the Alpaca adapter, and the backend-effective deadline is always shorter than the browser's client timeout. This ordering invariant is not displayed anywhere in the UI — it is a correctness guarantee for the user that the app's honest error will always appear before the browser gives up.
- The symbol-universe background warm and the window cache are internal backend behaviors with no direct UI representation; their effect is visible only as faster response times, not as new UI elements.
- The optional background symbol-universe refresh interval (`symbol_universe_refresh_seconds`) is configured but defaults to off (`0.0`). If enabled in a future deployment, users would experience fresher search results without any UI change — no control is exposed.
