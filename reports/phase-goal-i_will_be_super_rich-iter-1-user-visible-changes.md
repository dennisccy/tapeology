# Phase goal-i_will_be_super_rich-iter-1 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now **choose a data source** for the tape by using the new **Live / Historical / Simulated** segmented selector in the top bar (Simulated is selected by default).
- Users can now **enter a stock symbol** (free-text, e.g. `AAPL`) into a symbol box that appears when **Live** or **Historical** is selected.
- Users can now **set a historical replay window** — pick a date, a start time, and an end time, and choose a replay speed (1× / 2× / 5× / 10×) — when **Historical** is selected.
- Users can now **attempt a real-data Watch** (Live or Historical) and get an **honest answer**: when no vendor credentials are configured, the main area shows an explicit **"real-data provider unavailable"** panel instead of the cockpit — the app never fabricates tape data and never silently falls back to Simulated.
- Users can still **watch a simulated ticker exactly as before** — selecting Simulated, typing `SIM-BUYER`, and clicking Watch populates the cockpit and resolves to `buyer_control` (no regression).

---

## What Changed in the Visible UI

- The **top bar** now starts with a 3-way **Data source** segmented control (`Live` / `Historical` / `Simulated`) placed between the "Tapeology" title and the symbol/ticker input.
- The single ticker box is now **mode-aware**: in Simulated it is labeled "Ticker" with placeholder `Ticker e.g. SIM-BUYER`; in Live/Historical it is labeled "Symbol search" with placeholder `Symbol e.g. AAPL`.
- In **Historical** mode the top bar reveals extra controls inline: a **date** picker, a **start time** and **end time** input (separated by an "–"), and a **replay-speed** dropdown (1× / 2× / 5× / 10×).
- In **Live** mode the top bar shows a small **market-status indicator** — an amber pill reading `market unavailable` with an amber dot.
- The main cockpit area now has a third possible state: when a Live/Historical Watch is refused, it shows an amber-bordered **"Real-data provider unavailable"** panel (⚠ icon + the exact phrase "real-data provider unavailable" + guidance to set Alpaca credentials or switch to Simulated), shown **in place of** the cockpit.

---

## What Old Behavior Changed

- **Watching a ticker:** previously the top bar had a single ticker box with no data-source choice. Now a data-source selector comes first, and the ticker box is the Simulated mode's control. Simulated behavior itself is unchanged end-to-end (SIM-BUYER → buyer_control).
- **Starting a watch / switching ticker or source:** previously, starting a new watch (or switching symbol) did **not** stop the previous backend watch — leaving orphaned watches alive. Now any new Watch, or any change of data source / symbol, **tears down the prior watch first** (backend `DELETE /watch/{prev}` + closes its WebSocket) before starting the new one. The status dot returns to idle/connecting during the handover.

---

## Not Visible Yet

- **Real Live and Historical tape data (serving)** is not visible yet — even with credentials present, a real-mode Watch returns an explicit "not yet available" error rather than a cockpit. Real serving lands in later iterations (J-11 historical, J-12 live).
- **The Historical date / time / replay-speed values** are accepted and sent to the backend but **drive no real data fetch yet** — the watch is refused (no credentials) before they are used.
- **A live market open/closed status** is not visible yet — the Live market-status indicator is a static honest "unavailable" and does not call a real market-clock endpoint (deferred to J-12).
- **Vendor-backed symbol suggestions** are not visible yet — the symbol box is free-text only (vendor search is J-13).
- **The internal `real_data_available` credential check** is intentionally not surfaced as its own screen value — users only learn availability when a real-mode Watch is refused.
