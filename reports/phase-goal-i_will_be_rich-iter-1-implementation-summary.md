# goal-i_will_be_rich-iter-1 — Implementation Summary

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Written by:** developer

---

## Features Implemented

- **Watch a ticker and see a live tape cockpit**: On the home page, type a ticker (e.g. `SIM-BUYER`) and click **Watch**. The page fills with a live read of that ticker — quote, recent trades, the core tape features, the current tape state with a confidence score, plain-language observations, and an event log — and keeps updating on its own (over a live WebSocket connection) without reloading.
- **Honest "buyer control" read on the buyer scenario**: The built-in `SIM-BUYER` scenario streams aggressive buying that genuinely lifts the price. Within a few seconds the system settles on **Buyer Control** with a confidence around 0.88, and the event log records "Tape state changed to buyer_control".
- **Price impact, not just aggression**: The system only calls "buyer control" when aggressive buying is actually moving the price up. Heavy buying with no price progress will not be called buyer control — this rule is locked in now (and protected by an automated test) so it can correctly recognize "absorption" in later iterations.
- **One set of numbers everywhere**: Every value (state, confidence, each feature, the prices) is computed once inside the engine. The web page, the live stream, and the plain web API all show the exact same number for the same ticker — nothing is recalculated in a second place.
- **Honest uncertainty and no made-up data**: Before enough data has arrived, the state is shown as "Unclear" (low confidence) with a "Warming up" note. Asking to watch a ticker the system doesn't know returns a clear error, and reading a ticker nobody is watching returns a clear "not found" — the system never invents trades, prices, or a state.

---

## Changed Behavior

- This is the first feature build (the previous iteration wrote no product code). Before, there was no application at all; now there is a working single-ticker tape cockpit. No prior behavior was changed or removed.

---

## Backend-Only Items

- None. Every capability built this iteration is visible and usable through the web cockpit. (The plain web API endpoints `/tape/{ticker}/state`, `/features`, `/events`, `/summary` exist mainly so the same numbers can be confirmed outside the UI — they back the on-screen panels.)

---

## Incomplete Items

- **Other scenarios** — `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP` are reserved and can be typed in, but they are not yet driven to their target reads; watching them shows an honest "Unclear". Their real behavior (seller control, the two absorption cases, choppy/unclear) is scheduled for later iterations. *(This is by design for this iteration, not a defect.)*
- **Five additional features** — `spread_change`, `absorption_score`, `bid_refresh_score`, `ask_refresh_score`, `liquidity_imbalance` are not shown yet; they are added when the absorption iterations need them. The Features panel currently shows nine features.
- **Stop button** — there is no control to stop watching yet (planned for a later iteration).

---

## Config and Environment Changes

- `NEXT_PUBLIC_API_URL` — tells the web app where the backend is. Default: `http://localhost:8000`. (The automated QA harness sets this automatically; `NEXT_PUBLIC_API_BASE` also works.)
- `TAPEOLOGY_FEED_PACE` — optional; wall-clock seconds between delivered simulated events in live mode. Default: `0.04` (≈ a few seconds for the buyer scenario to resolve in the browser).
- No database and no migrations — this phase runs entirely in memory.

---

## Known Limitations

- Runs on **simulated data only** and entirely **in memory** — nothing is persisted; restarting the backend forgets all watched tickers (this is the intended Phase-1 design).
- The buyer scenario shows "Unclear / Warming up" for roughly the first 3–4 seconds after you click Watch, then resolves to Buyer Control. This warm-up is deliberate so the read is steady rather than flickering at the confidence boundary.
- Only one scenario (`SIM-BUYER`) produces a meaningful read this iteration; the others are placeholders until their dedicated iterations.
- For local development the backend (`http://localhost:8000`) and frontend (`http://localhost:3000`) must both be running; the automated QA harness starts them on per-project offset ports.
