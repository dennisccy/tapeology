# Phase goal-i_will_be_super_rich-iter-13 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Change the replay speed (1× / 2× / 5× / 10×) while a historical replay is actively running by selecting a new value from the speed dropdown in the Historical mode controls — the replay immediately re-paces without restarting or re-loading the window.
- Choose the "Full RTH 9:30–16:00" quick-pick (or any multi-hour historical window) for a busy stock and have it actually load the real tape data, instead of seeing the "very high-volume — try a shorter range" refusal that appeared before.
- Trust that a stock making a clear directional move (strong one-sided price progress relative to its price level) will read as **buyer control** or **seller control** on the tape-state panel, rather than being stuck on "unclear" because a fixed dollar threshold tuned for the simulator was too tight for real sub-$100 names.

---

## What Changed in the Visible UI

- The Historical mode replay-speed dropdown (1× / 2× / 5× / 10×) in the TopBar now has two distinct behaviors: when no watch is running it still just stages the speed for the next Watch (unchanged); when a historical replay is running, selecting a different value immediately re-paces the current replay — no teardown, no spinner, no position loss.
- The tape-state panel (row 1 of the cockpit) may now show **buyer control** (green) or **seller control** (red) where it previously showed **unclear** (amber) for a real stock making a genuine proportionate directional move. The values displayed (state label, confidence bar) are identical in format; only the computed result is recalibrated.
- The speed change is silent on success — the user sees the cadence of new candles and trades arriving change; there is no confirmation toast. A failure (e.g. speed applied to a non-running watch) surfaces in the existing error banner at the top of the page.

---

## What Old Behavior Changed

- **Replay-speed dropdown:** previously selecting a speed while a replay was running had no effect on the running replay — it only set the speed for the *next* Watch. Now selecting a speed during an active historical replay immediately applies it to that replay (cadence changes within approximately one second, watch is not torn down).
- **Historical window loading for long windows:** previously requesting a multi-hour or Full-RTH historical window always resulted in a "very high-volume — try a shorter range" error from the backend. Now such windows load successfully by fetching in parallel bounded pieces and stitching them in order; the "shorter range" error appears only when the window is genuinely too large to load within the time budget.
- **Tape-state classification on real instruments:** previously a real stock at ~$30–50 with a spread that was proportionate relative to its price (but "wide" by the old absolute dollar constant calibrated for the ~$100 simulator) would remain "unclear". Now the classifier judges spread in basis points and price impact as a return, so a clear directional move on a real sub-$100 stock resolves to buyer/seller control. Genuinely uncertain tapes (spread wide relative to its price, or heavy one-sided pressure with no price progress) still read "unclear" or "absorption".

---

## Not Visible Yet

- The `reference_price` value (the in-window mid/last price level used by the classifier) now appears in the raw per-window feature data served by `/features` and the live WebSocket stream. It is not rendered as a new on-screen readout — the frontend only surfaces the existing named headline features.
- The `POST /watch/{ticker}/speed` endpoint exists for Historical replays. It correctly returns 404 when called against a simulator or live watch (those have no replay pacing); the speed control is only shown and only active in Historical mode, so this is not reachable via the normal UI flow.
