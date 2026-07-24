# Phase goal-clean_slate-iter-2 — User-Visible Changes

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

**None.** This is a subtractive-only demolition iteration. Goal.md's own acceptance text states
it explicitly: "New user-facing capability: None." The dev handoff confirms nothing new was
added — no new page, button, form, data view, or affordance exists after this iteration that
didn't already exist before it. Every change below is a removal or a behind-the-scenes edit that
preserves existing behavior.

---

## What Changed in the Visible UI

- **The top navigation bar** (present on every page) now shows exactly two links — "Cockpit" and
  "Structure" — instead of the previous five ("Cockpit", "Journal", "Studies", "Performance",
  "Structure"). The bar itself was not edited; it reads the link list from the backend at runtime,
  and the backend's list shrank.
- **`/journal` no longer exists.** Visiting it now shows the app's standard dark, styled "page not
  found" screen instead of the trade-journal list (previously a filterable table of journaled
  positions plus a running hint-activity log).
- **`/journal/<id>` no longer exists.** Visiting any journal-entry detail URL now shows the same
  "not found" screen instead of that entry's detail view (thesis timeline, entry/exit marks,
  saved review notes).
- **`/studies` no longer exists.** Visiting it now shows the "not found" screen instead of the
  replay-studies workbench (a create-study form plus a list of study results).
- **`/performance` no longer exists.** Visiting it now shows the "not found" screen instead of the
  analytics/performance dashboard.
- **The Cockpit page (`/`) no longer shows a thesis strip.** Previously this appeared between the
  price chart and the panel grid, letting a user manually declare a trade thesis, watch its live
  verdict, and log entry/exit/review marks. That entire strip — in both its "live" and its
  post-Stop "surviving thesis" states — is gone; nothing replaces it.
- **The Cockpit page no longer shows a hint panel** under the Tape State panel. Previously this
  surfaced a setup-forming "hint" a user could click to prefill a thesis declaration.
- **The Cockpit page no longer shows a sound-cue toggle anywhere.** It only ever appeared nested
  inside the now-removed thesis strip, so it disappeared along with it.
- **Stopping a watch on the Cockpit** now always returns directly to the plain "No ticker watched"
  idle screen. The previous "surviving thesis" idle variant (shown when an entry-marked thesis
  outlived the stopped watch) no longer exists.

---

## What Old Behavior Changed

- **Cockpit price chart**: previously drew two layers of markers — tape-state markers above each
  bar, plus thesis-verdict/entry-exit markers below each bar — and could draw dashed
  invalidation/level reference price lines when a thesis was active. It now draws only the
  tape-state markers; no thesis markers, no thesis price lines. Everything else about the chart is
  unchanged and was re-verified working: candles render, the timeframe selector switches views,
  the support/resistance band overlay renders, and live bars keep moving as new trades arrive.
- **Live tape data stream**: the WebSocket feed a watched ticker's page reads from previously
  carried two extra fields (`thesis`, `hint`) alongside the core tape data on every frame. Those
  two fields are gone now; every other field (price/quote data, tape state, recent trades,
  features, event log, etc.) is unchanged. This is only directly visible to someone inspecting raw
  network traffic (e.g., browser devtools' WS inspector) — its on-screen effect is the removed
  thesis strip / hint panel / chart overlay described above.
- **`/structure` page**: not edited this iteration, and re-verified unchanged — loading the pinned
  AAPL as-of date still renders the same 300–302.4-class resistance wall band as before.
- **Feed-basis/provenance badge**: not edited this iteration, and re-verified unchanged — still
  shows the correct feed label ("Simulated" on a sim watch, "SIP (consolidated)" on a real
  historical replay).

---

## Not Visible Yet

- **The AI-assistant (MCP) tool list still offers three tools named `journal`, `analytics`, and
  `studies`** — these are used by external AI-assistant integrations, not the browser UI. They
  already honestly respond "not found" when called (their backing routes were deleted in the prior
  iteration), but removing them from the offered tool list itself is explicitly deferred to the
  next iteration (J-03) and was not touched here.

**Pre-existing, unrelated to this iteration** (noted so it is not mistaken for a regression
introduced here): `/structure`'s "Case Studies" section remains hidden behind a switch that was
already off before this cleanup project started. This iteration did not touch it.
