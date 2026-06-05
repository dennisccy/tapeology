# Phase goal-i_will_be_super_rich-iter-6 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Watch a ticker in **Simulated** or **Historical** mode and see the watched price drawn as a
  live candlestick chart directly **above** the cockpit on the home screen (`/`) — no new page or
  navigation required.
- Read the tape state visually: colored arrow markers appear on the chart at each moment the
  tape state transitions to a meaningful one — **green** (emerald) for buyer control, **red**
  (rose) for seller control, **amber** for bid or ask absorption. "Unclear" is deliberately
  unmarked.
- Switch between **10 s**, **30 s**, and **60 s** candle sizes using the bar-size selector buttons
  on the chart; the chart redraws immediately at the chosen granularity.
- **Pan and zoom** the chart by dragging (pan) and scrolling or pinching (zoom) — library default
  interaction.
- See an honest empty state ("No price history for this window yet") before any price data has
  arrived, rather than placeholder candles. A "Loading price history…" overlay is shown during
  the initial fetch.

---

## What Changed in the Visible UI

- **A new "Price Chart — Tape-State Markers" panel now appears at the top of the main content
  area on `/`** (above the cockpit grid) whenever a ticker is being watched in Simulated or
  Historical mode. This panel was not present in iter-5.
- The panel contains a full-width dark candlestick canvas (slate-950 background, slate-800
  grid lines, monospaced axis labels) styled to match the existing cockpit surfaces — it does
  not appear as a bright third-party widget.
- A small **bar-size selector** (labelled "Bar size", three buttons: "10s", "30s", "60s") sits
  above the chart canvas. The currently selected button is visually distinct (dark fill,
  light text).
- **The chart is hidden when the data source is Live** — switching to Live mode makes the
  chart panel disappear; switching back to Sim or Historical makes it reappear (once a ticker
  is being watched).
- The existing cockpit panels (quote, recent trades, features, tape-state, observations, event
  log) are **unchanged** in position and content — the new chart sits above them without
  displacing anything.

---

## What Old Behavior Changed

- **The Watch screen layout changed for Simulated/Historical**: previously, after starting a
  watch, the page showed the TopBar then immediately the cockpit grid. Now, for Sim and
  Historical modes, the price chart panel is inserted between the TopBar and the cockpit. The
  cockpit itself is visually and functionally unchanged.
- No other existing behavior was modified. Stopping a watch, switching the data source, and
  the cockpit's WebSocket update cadence all work the same as before.

---

## Not Visible Yet

- **`GET /tape/{ticker}/history?bar=<10|30|60>`** is the new backend endpoint that the chart
  reads. It is wired end-to-end (the `PriceChart` component consumes it), so it is not a
  "hidden" capability from the user's perspective. However, the endpoint is also directly
  readable as a raw API for verification purposes (e.g. `curl` against the backend).
- **J-19 (pause/resume)** and **J-20 (local-time window picker)** — deferred to later slices;
  no UI entry point exists for these yet.
- **Chart in Live mode**: the chart is explicitly hidden in Live mode by design for this
  iteration. No UI exposes it there yet.
