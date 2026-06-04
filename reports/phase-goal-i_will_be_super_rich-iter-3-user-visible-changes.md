# Phase goal-i_will_be_super_rich-iter-3 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the **real market session status** when they select **Live** in the data-source
  selector — a pill in the top bar shows "market open" (green), "market closed — next open <time>"
  (amber), or "market unavailable" (amber, when no credentials are configured). Previously this was
  a permanently hardcoded "market unavailable" stub that never reflected reality.
- Users can now Watch a real symbol in **Live** mode while the market is closed and get an explicit,
  honest **"Market is closed"** screen that tells them when the market next opens — instead of a
  fabricated tape cockpit. To reach it: select **Live**, type a real symbol (e.g. `AAPL`) in the
  symbol search box, and click **Watch** while the US market is closed.
- Users can read the **next-open time** in their own local timezone (with an explicit zone label) in
  both the top-bar indicator and the "Market is closed" panel, so the next-open instant is never
  mis-read as the wrong time zone.

---

## What Changed in the Visible UI

- The **top bar** (persistent header) now shows a live **market-status indicator** while in Live mode,
  replacing the old static "market unavailable" pill. It has four visual states: a slate "…"
  placeholder before the first check resolves, emerald "market open", amber "market closed — next
  open <time>", and amber "market unavailable".
- The market-status indicator **refreshes itself** every 60 seconds while Live mode is active, so the
  open/closed status stays current without the user reloading the page.
- The honest non-cockpit panel (`ProviderUnavailable`) gained a new **"Market is closed"** variant —
  an amber warning panel showing the phrase "market is closed", the next-open time, and guidance that
  no tape is shown and that Historical replay is available as an alternative. It renders centered, in
  place of the cockpit (no quote, trades, or state panels appear alongside it).

---

## What Old Behavior Changed

- **Live mode market pill:** previously the top bar always showed a fixed "market unavailable" pill in
  Live mode regardless of the real session. Now it shows the actual session status (open / closed +
  next open / unavailable) fetched from the backend.
- **Live Watch while market is closed:** previously a Live watch fell through to the generic
  not-implemented / unavailable path. Now, when the market is authoritatively closed, it surfaces the
  distinct **"Market is closed"** honest panel with the next-open time. (A Live watch with credentials
  while the market is **open** is unchanged — it still honestly reports streaming as not-yet-available.)
- The existing three honest-failure panels (provider unavailable, symbol not tradable, no data for
  window) are **unchanged** — their copy and behavior are byte-for-byte the same.

---

## Not Visible Yet

- **Live streaming itself** (real-time trade/quote feed via the Alpaca WebSocket) is still not
  available. A Live watch with valid credentials while the market is **open** continues to report an
  honest "streaming not implemented" state — the real live socket is deferred to a future iteration.
- The backend's **`next_close`** time from `GET /market/clock` is returned by the API but is not
  surfaced anywhere in the UI (only `is_open` and `next_open` are displayed).
