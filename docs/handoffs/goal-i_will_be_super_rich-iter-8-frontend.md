# goal-i_will_be_super_rich-iter-8 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built (UI)

All changes are inline in the existing **Historical** mode reveal on `/` (the tape cockpit home).
No new page, no new route, no nav change — additive only.

- **Local timezone label.** When the data source is **Historical**, a small muted, monospaced label
  shows the operator's IANA zone (e.g. `Asia/Hong_Kong`) next to the date/time inputs, with a
  tooltip "Your date and time entry is interpreted in this timezone". This satisfies "all
  market/session times shown carry an explicit zone label".
- **US-session quick-picks.** A row of three neutral buttons appears beside the date/time/speed
  controls: **Open 9:30 ET**, **Close 16:00 ET**, **Full RTH 9:30–16:00 ET**. Each button is
  annotated with its **local-time equivalent** for the chosen date (e.g. "Open 9:30 ET (21:30
  local)" in Hong Kong). Clicking a button fills the start/end time inputs in one action. The
  buttons are **disabled until a date is chosen** (so a pick can never produce a malformed/empty
  window).
- **Timezone-correct Watch.** Submitting a Historical watch now sends **tz-aware UTC instants**
  (`…Z`) in the `POST /watch` body's `start`/`end`, resolved once from the user's local selection —
  not the old naive string. What the user picks locally is exactly what is fetched; no mental UTC
  conversion, no silent shift.

The **watched-source descriptor** (e.g. `historical F …`) and the **price chart** are unchanged —
they already render the backend's canonical values verbatim. Because the resolved window is what the
backend records in the row-6 descriptor, the displayed source label automatically reflects the
actual fetched window (honest label).

## Files Changed

- `apps/frontend/lib/datetime.ts` — added the pure historical-window resolution module (the row-12
  owner): local→UTC resolver, named ET session anchors, DST-correct ET→UTC via `America/New_York`,
  zone-label + quick-pick annotation helpers. (Display-only `formatMarketTime` unchanged.)
- `apps/frontend/components/TopBar.tsx` — wired the resolver into `handleSubmit`; rendered the zone
  label + quick-pick row inside the `mode === "historical"` reveal; added a `presetWindow` state so a
  quick-pick submits its pre-resolved instants verbatim (correct across a local-midnight span).

## Design System Conformance

- **No component library** (DESIGN SYSTEM = hand-built panels). The quick-pick buttons reuse the
  established small-button pattern and the slate palette; the date/time/speed inputs keep the
  existing `INPUT_CLASS`.
- **Monospaced numerics** (`font-mono`) for the zone label and the local-equivalent annotations.
- **No new colors** — the picker is neutral chrome (no buy/sell semantics). The chart's existing
  emerald/rose/amber marker semantics are untouched.
- **Interactive states** — the quick-pick buttons have hover (border + text lighten), focus
  (emerald ring), active (darker bg), and disabled (40% opacity, not-allowed cursor) states.
- **Responsive** — the quick-pick row is its own flex group with `flex-wrap`, and the whole form
  already wraps; the controls reflow on narrow widths.

## States Handled

- **Zone label** is always shown in Historical mode (display only — never omitted).
- **Quick-picks disabled** when no date is chosen; when enabled, a pick always yields a valid
  `start < end` (a point preset is padded by 1 minute; RTH uses the full span).
- **Half-filled manual entry** resolves to `undefined`, so the backend returns its honest 422 — no
  malformed window is sent.
- **Empty historical window** is unchanged: the backend returns the honest `no_data_for_window`
  state and the chart shows its existing empty treatment (no fabricated candles).

## Verification

- `npx next build` (isolated dist dir): compiled successfully, all TypeScript types valid, 4/4 static
  pages generated. The throwaway dist dir and the build's auto-edits to `tsconfig.json` /
  `next-env.d.ts` were reverted so only the two intended source files are modified.
- DST math validated via a Node check (see the dev handoff): summer EDT (−04:00) and winter EST
  (−05:00) resolve to the correct, different UTC instants; the Hong-Kong round-trip is consistent.

## For Browser QA

- **J-20:** in Historical mode, assert the local zone label renders, the three quick-picks render
  with local-equivalent annotations, clicking one fills a valid RTH start/end, and the submitted
  POST body's `start`/`end` are tz-aware (`offset`/`Z`) equal to the selected local instant — not a
  naive string, not UTC-shifted. (Screenshots + network inspection.)
- **J-18 (requires pixels):** watch the committed Ford fixture window (`F`, 2026-06-02 15:00–15:02)
  in Historical mode against a **clean isolated `.next`** + isolated backend port; screenshot the
  **populated** candlestick chart with real prices + tape-state markers; switch bar size 10→30→60 s
  and screenshot the re-render. (No code change here — render-verification only.)
- Do **not** build against the shared harness `:3650 .next` (running QA servers exist); do **not**
  `git checkout` any file carrying uncommitted iter edits.
