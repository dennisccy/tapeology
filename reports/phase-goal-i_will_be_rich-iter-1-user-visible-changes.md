# Phase goal-i_will_be_rich-iter-1 — User-Visible Changes

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

This iteration is the first build of the product — the entire `/` tape cockpit is new. From an empty repository, a user can now:

- **Watch a live ticker tape** — open the app at `/`, type `SIM-BUYER` into the ticker input, and click **Watch** to start a live read of that ticker (issues `POST /watch/{ticker}` behind the scenes).
- **See an honest tape-state call** — after a short warm-up the **Tape State** panel shows the classified state (`buyer_control` for `SIM-BUYER`) with a confidence score and confidence bar, color-coded (green = buy-side, red = sell-side, amber = absorption/unclear).
- **Read live quote data** — the **Quote** panel shows bid (green), ask (red), spread, and last price, updating live.
- **Watch recent trades stream in** — the **Recent Trades** panel shows a price / size / side table where each row is colored by aggressor side (green buy, red sell, slate unknown).
- **Inspect the named tape features** — the **Features** panel shows the nine implemented features (trade_speed, volume_speed, aggressive_buy_ratio, aggressive_sell_ratio, net_aggressive_volume, buy_price_impact, sell_price_impact, average_spread, large_print_count) and lets the user switch the lookback window (10s / 30s / 60s / 180s / 300s).
- **Read plain-language evidence** — the **Observations** panel lists the engine's human-readable evidence for the current call, and the **Event Log** panel shows transition messages (e.g. `"Tape state changed to buyer_control"`), newest first.
- **See live updates without reloading** — once watching, every panel updates over a WebSocket connection; no page refresh is needed.
- **See an honest empty/error state** — before watching anything the cockpit shows an idle/empty state with no fabricated numbers; watching an unknown ticker surfaces an explicit error message rather than fake data.

---

## What Changed in the Visible UI

This is a greenfield build, so every surface below is **new** (there was no prior UI):

- The `/` route now renders the **Tapeology tape cockpit** (previously the app had no pages).
- A persistent **app shell / top bar** was added: app name **Tapeology**, a ticker input + **Watch** button, a watched-ticker label, a scenario indicator (e.g. `scenario: buyer_control`), and a stream-status dot (idle / connecting / live / closed).
- Six data **panels** were added in a responsive grid (1 → 2 → 3 columns): Tape State, Quote, Features (with a window selector), Recent Trades, Observations, and Event Log.
- An **idle/empty state** was added for when no ticker is being watched.
- A **footer disclaimer** was added: "Descriptive only — not trading advice."

---

## What Old Behavior Changed

None. This is the first iteration of a greenfield product — there was no prior user-facing behavior to change or regress. No journey was previously green.

---

## Not Visible Yet

These backend capabilities or planned surfaces exist (or are reserved) but are intentionally not exposed in the UI this iteration — all deferred to later journeys per the spec:

- **Other scenarios are reserved but inert.** `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, and `SIM-CHOP` can be typed and watched, but they emit no events yet and stay `unclear` — their target states (seller_control, absorption pair, unclear-chop) are not implemented (deferred to J-03 / J-04 / J-05 / J-06).
- **Five blueprint features are not displayed.** `spread_change`, `absorption_score`, `bid_refresh_score`, `ask_refresh_score`, and `liquidity_imbalance` are not yet computed or shown (added additively with their owning journeys).
- **No Stop / un-watch control.** There is no UI to stop watching a ticker (no `DELETE /watch` this iteration — deferred to J-09).
- **No Level 2 / order-book view.** `BookLevelEvent` and book-depth display are reserved for a later iteration.
