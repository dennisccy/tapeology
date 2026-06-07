# Goal Iteration 11 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Written by:** developer

---

## Features Implemented

This iteration makes the app's real-market-data features **fast and honest under vendor latency** —
it is the last set of "must-have" behaviours (J-28, J-29, J-30). Nothing new appears on screen; the
existing actions just behave better.

- **A real, honest time limit on every market-data call (J-28)**: when the data vendor is slow or a
  request asks for too much data, the request is now genuinely cut off by a real deadline at the
  network call itself (not just abandoned by an outer timer). The user always sees the app's own
  honest error rather than a browser giving up, because the app's deadline is deliberately set
  shorter than the browser's.

- **An actionable "window too big" message (J-28)**: if a Historical window is so high-volume that
  it exceeds the budget, the error now says *"that window is very high-volume — try a shorter
  range"* — a useful instruction — instead of a misleading "please try again" that would just fail
  the same way.

- **Fast Historical loading (J-29)**: loading a real past window is now fast by design. The app
  fetches the trades and the quotes **at the same time** (instead of one after the other), skips a
  needless extra lookup it used to do before every fetch, **remembers** windows it has already
  fetched (so re-watching the same symbol + window is near-instant), and **warms up the read
  quickly** so the cockpit shows a meaningful read sooner instead of waiting out the real timeline.

- **Instant-feeling symbol search (J-30)**: the tradable-symbol list is now loaded once in the
  background when the app starts, so the **first** search after a restart is no longer a multi-second
  stall. While typing quickly, each new keystroke **cancels** the previous search request, so
  results never pile up or arrive out of order. A search that finds nothing (or hits a vendor
  hiccup) quietly shows no suggestions — never an error or a stuck "Searching…". You can still type
  and watch any symbol by hand.

---

## Changed Behavior

- **Historical Watch that times out**: Previously showed a generic timeout message. Now shows the
  actionable "that window is very high-volume — try a shorter range" message (same place on screen —
  the existing error panel). The underlying failure category is unchanged (a "provider timeout").

- **Re-watching the same Historical window**: Previously re-fetched everything from the vendor. Now
  reuses the already-fetched real data and loads near-instantly.

- **Symbol search while typing fast**: Previously could let a slow earlier result overwrite a newer
  one and re-fetched the whole symbol list as needed. Now older requests are cancelled and the
  symbol list is pre-loaded, so results stay correct and fast.

- **A Historical read warming up**: Previously paced the warm-up at the data's real timeline. Now
  the warm-up is fast-forwarded so the cockpit becomes meaningful quickly. Important: this only
  changes *how quickly events are shown*, not *what they are* — the tape state, confidence, and all
  the numbers are exactly the same as before (verified by an automated test).

---

## Backend-Only Items

- None. Every change is either user-visible behaviour (faster/clearer Historical loading and search)
  or an internal performance/honesty property of an existing on-screen feature. No new endpoint,
  page, or displayed value was added.

---

## Incomplete Items

- None of the planned scope was deferred. All three target journeys (J-28, J-29, J-30) are
  implemented with automated tests.
- Two legs remain operator/browser-confirmed (as planned for credentialed real-vendor checks): the
  oversize-window timeout against the live vendor, and the market-open-minute busy-window load timing
  in a real browser. The deterministic in-loop proofs (slow/timeout/timed test doubles) cover the
  logic; live spot-checks against the real vendor succeeded during development (search, a 2-minute
  Historical fetch, and a near-instant cache re-watch).

---

## Config and Environment Changes

No new environment variables. New internal tuning values (all in `apps/backend/app/config.py`, no
hard-coded numbers in the logic):

- `vendor_http_timeout_seconds` — the real network deadline for a single vendor call — default: `6.0` s
- `frontend_watch_request_timeout_ms` — a mirror of the browser's timeout, used only to verify the
  app's deadline stays shorter than the browser's — default: `12000` ms
- `historical_cache_max_entries` — how many fetched Historical windows to remember — default: `32`
- `historical_cache_ttl_seconds` — how long a remembered window stays fresh — default: `300.0` s
- `warmup_fast_forward_pace_seconds` — pacing for the fast warm-up of a Historical read — default: `0.0` s
- `symbol_universe_refresh_seconds` — optional background refresh of the symbol list; `0.0` = off — default: `0.0`

Frontend tuning (in `apps/frontend/lib/config.ts`):

- `SYMBOL_SEARCH_DEBOUNCE_MS` — quiet period before a search fires — default: `250` ms
- `SYMBOL_SEARCH_MIN_QUERY` — minimum characters before searching — default: `1`

---

## Known Limitations

- The market-data vendor used is unchanged (Alpaca's free IEX feed); with no credentials configured,
  the real modes still show an explicit "unavailable" and search is empty — exactly as before. No
  fabricated data is ever shown.
- The "fast first search" relies on a one-time background load at app startup; if that startup load
  fails (vendor hiccup), it is ignored and the first search falls back to loading the list on demand
  — slightly slower that once, never broken.
- The browser-side feel of search (crisp, no pile-up, fast first search) is best confirmed in a real
  browser; the automated tests cover the logic and the backend behaviour.
