# Phase goal-i_will_be_super_rich-iter-2 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- **Replay a real past trading session.** In **Historical** mode, type a real US symbol (e.g. `F`),
  pick a past date, a start/end time, and a replay speed (1×/2×/5×/10×), then press **Watch** — the
  cockpit now fills with that symbol's **real** trades and quotes for that window, replayed through
  the same engine the simulator uses. Previously Historical mode refused every watch.
- **Find a symbol by typing part of it.** In **Live** or **Historical** mode the symbol box now
  shows a live dropdown of real matching tradable symbols (ticker + company name) as you type.
  Click a suggestion to fill the box.
- **Still type any symbol free-hand.** Free-text entry in the symbol box always works — ignore the
  dropdown and press Watch with whatever you typed.
- **See an honest message instead of a fake cockpit when a real symbol can't be replayed.** A symbol
  that isn't tradable shows **"not a tradable symbol"**; a window with no data shows **"no data for
  that window"** — each in place of the cockpit, never alongside an invented tape.

---

## What Changed in the Visible UI

- **The symbol box in Live/Historical mode** is now a search box with a debounced (≈¼ second)
  suggestions dropdown showing matching `SYMBOL` (mono) + company name. In **Simulated** mode the
  box stays the plain ticker input — unchanged.
- **The non-cockpit message area** now renders **three distinct amber panels** keyed off the failure
  reason: *"Real-data provider unavailable"* (no credentials), *"Symbol not tradable"*
  (**new**), and *"No data for that window"* (**new**). Previously only the no-credentials panel
  existed.
- **The cockpit** (bid/ask/spread/last, recent trades, feature readouts, tape state + confidence,
  observations, event log) is reused exactly as in Simulated mode but now displays **real** values
  for a Historical watch.
- **The watched-source label** in the TopBar (`scenario:` chip) reads `historical <SYM> <window>`
  for a Historical watch, sourced from the canonical engine snapshot (no client recompute).
- **The Historical controls** (date / start time / end time / replay-speed select) already rendered
  from the previous iteration; this iteration makes pressing **Watch** actually fetch and replay
  real data.

---

## What Old Behavior Changed

- **Historical mode:** previously every Historical watch returned a generic "not yet available"
  message. Now it fetches and replays real data, or shows one of the three distinct honest panels.
- **Live/Historical symbol input:** previously a plain text field. Now a search box with a live
  suggestions dropdown (free-text entry preserved). Simulated mode is unchanged.
- **Honest non-cockpit area:** previously a single "provider unavailable" panel. Now reason-specific
  — testers should re-verify that the correct panel appears for each failure.
- **Simulated mode and Live mode are unchanged.** Sim scenarios (SIM-BUYER, etc.) behave exactly as
  before; Live mode still reports real-time streaming is not yet wired (deferred to J-12).

---

## Not Visible Yet

- **Live real-time streaming (J-12)** is intentionally out of scope — Live mode still shows the
  "not yet available" / market-status `unavailable` pill; the live socket and `GET /market/clock`
  are deferred.
- **The "market is closed" honest case** (the 4th J-14 case) depends on Live mode and is deferred
  with J-12.
- **Stale-feed recovery (J-15)** is deferred with live streaming.
- **No backend-only capability is hidden** — the symbol search, historical cockpit, and all three
  honest states are reachable from the one screen at `/`.
