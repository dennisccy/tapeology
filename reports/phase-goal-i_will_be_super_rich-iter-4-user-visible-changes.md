# Phase goal-i_will_be_super_rich-iter-4 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

<!-- The capability is delivered entirely through EXISTING UI surfaces. No frontend
     code changed; the backend made the already-rendered Live "Watch" action functional. -->

- **Watch a real live ticker.** Select **Live** mode, search/enter a real US symbol (e.g. `F`,
  `AAPL`), and press **Watch** — during market hours with credentials configured, the single-ticker
  cockpit now streams the vendor's real-time trades and quotes through the same engine, and the
  status dot reads **live** (emerald). Previously this exact action was refused by the backend
  (the watch never started and no cockpit appeared).
- **See an honest `stale` status when the live feed goes quiet.** If no live event arrives within
  the configured stale-gap window, the TopBar status dot flips to **stale** (amber) — without
  inventing any trades — and flips back to **live** (emerald) when real events resume.
- **See the live source label.** The watched-source label in the TopBar now reads **`live <SYM>`**
  (e.g. `scenario: live F`) for a live watch, distinguishing it from a sim or historical source.
- **Switch/stop a live watch cleanly.** Pressing **Stop** or switching symbol/mode tears down the
  live watch (the dot goes `closed` / the cockpit clears), and the underlying real vendor socket is
  closed — no leftover/leaked connection.

---

## What Changed in the Visible UI

<!-- No component was added or restyled. These are behavior changes on existing elements. -->

- The **Live "Watch" button** now produces a streaming cockpit instead of an error/no-op. Before
  this iteration, watching in Live mode hit a backend refusal (`provider_not_implemented`, HTTP 503)
  and the cockpit never mounted.
- The **TopBar status dot** now displays **live** (emerald) and **stale** (amber) driven by a *real
  live feed*. Previously these two values only ever came from the simulated/historical paths
  (which produced `connecting`/`closed`); the dot itself is unchanged code.
- The **watched-source label** in the TopBar now renders the `live <SYM>` descriptor for live
  watches.
- No new pages, routes, components, navigation links, columns, fields, or displayed values were
  added. Still exactly one screen (`/`); the cockpit body is identical across sim/historical/live.

---

## What Old Behavior Changed

<!-- Important for regression testing. -->

- **Live mode Watch:** previously refused at the backend with `provider_not_implemented` (503) so
  no cockpit rendered. Now it starts a real live stream and renders the cockpit (or returns an
  honest non-cockpit state — see below). Testers re-verifying Live mode must expect a working watch,
  not a refusal.
- **Live mode error states (unchanged contract, now reached via the real path):** Live + missing
  credentials still surfaces **`provider unavailable`** (503, no cockpit); Live + market closed still
  surfaces **`market is closed`** with the next open time (409, no cockpit). These honest non-cockpit
  states are preserved — the iteration did not weaken them.
- **No change** to sim mode (J-01/J-02), historical mode (J-11), the mode selector (J-10), symbol
  search (J-13), or the market-status indicator (J-14) — the engine, classifier, serializers, and
  synchronous providers are a verified 0-line diff, so those journeys must behave identically.

---

## Not Visible Yet

<!-- Backend capability whose only confirmation is operator/gated, not a browser-visible path. -->

- **The real Alpaca live socket itself is operator/gated.** The live feed (J-12/J-15) can only be
  exercised against the real market during market hours with credentials; it is confirmed by a
  backend gated integration test against the real Alpaca WebSocket (run and passed per the dev
  handoff — F streamed `live` with a real penny spread), not by a browser-against-live-market test.
  The browser-visible verification is limited to: the Live controls render, and a successful watch
  mounts the cockpit with the dot reading `live`.
- **Auto-reconnect of a dropped socket is not implemented** (out of scope). A dropped live socket
  honestly surfaces as **stale** until events resume or the user stops the watch — there is no
  "reconnecting" affordance in the UI.
