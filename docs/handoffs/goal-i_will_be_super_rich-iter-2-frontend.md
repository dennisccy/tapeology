# goal-i_will_be_super_rich-iter-2 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built (UI)

No new page or route — everything stays on `/` (Watch — HOME). The cockpit body is **unchanged**
and identical across modes; only the symbol input and the honest non-cockpit area evolved.

- **Symbol search dropdown (J-13).** In **Live / Historical** mode the symbol box is now
  `SymbolSearch`: typing a partial symbol/name shows a **debounced** (250ms) dropdown of real
  `GET /symbols/search` suggestions (symbol in mono + company name muted). Clicking a suggestion
  fills the symbol; **free-text entry still works** (ignore the dropdown and press Watch). In
  **Simulated** mode the box stays the plain ticker input (unchanged). No business logic — results
  render verbatim.
- **Historical cockpit (J-11).** A successful `POST /watch` in Historical mode drives the **same**
  `Cockpit` exactly as a sim watch (`page.tsx` `setTicker` → `useTapeStream` → REST/WS). The
  watched-source label reads `historical <SYM> <window>` from the canonical snapshot
  (`snapshot.scenario`) — no client recompute.
- **Distinct honest non-cockpit panels (J-14).** `ProviderUnavailable` is generalized to render a
  distinct amber panel **per failure reason**, in place of the cockpit (never alongside a fabricated
  cockpit, never a fall-back to Simulated):
  - `provider_unavailable` → "real-data provider unavailable" (credentials not configured).
  - `symbol_not_tradable` → "not a tradable symbol".
  - `no_data_for_window` → "no data for that window".
  `lib/api.ts`'s `watchTicker` now returns the distinct `reason`; `page.tsx` keys the panel off it.

## Changed Behavior

- **Symbol input (Live/Historical):** previously a plain text box. Now a search box with a live
  suggestions dropdown (free-text entry preserved). Simulated mode is unchanged.
- **Honest non-cockpit area:** previously only the no-creds "provider unavailable" panel existed.
  Now three distinct reason-specific panels render (the two new ones for untradable symbol / empty
  window). The generic red error banner still handles other failures (e.g. live creds-present "not
  yet available", unreachable backend).

## Files Changed

**Created**
- `apps/frontend/components/SymbolSearch.tsx` — debounced suggestions dropdown (J-13).

**Modified**
- `apps/frontend/lib/types.ts` — `SymbolMatch`, `FailureReason`.
- `apps/frontend/lib/api.ts` — `searchSymbols(q)`; `watchTicker` returns the distinct `reason`.
- `apps/frontend/components/TopBar.tsx` — wires `SymbolSearch` in Live/Historical.
- `apps/frontend/components/ProviderUnavailable.tsx` — distinct honest panel per reason.
- `apps/frontend/app/page.tsx` — tracks the distinct `reason`, renders the matching panel.

## Design System Adherence

- Dropdown + panels use existing tokens only — slate surfaces/borders, `font-mono` for symbols,
  amber for the honest-fail/unavailable states (load-bearing color semantics). The dropdown reuses
  the established input styling; buttons have hover/focus states. No new effects invented.
- States handled: search empty/short (no dropdown), searching (placeholder row), the **three**
  distinct honest non-cockpit states, historical cockpit warm-up (the existing connecting/live dot),
  and idle/empty after Stop.

## Tests Run

- `cd apps/frontend && npm run build` → compiled + type-checked clean (route `/` ~6 kB).
- The user-visible flows (suggestions, historical cockpit, the three honest states, sim regression)
  are for the browser-qa-agent to drive; exact click paths are in the UI test plan.

## Known Issues / Limitations

- Suggestions require operator creds + network (the backend returns `[]` without them); the input
  still accepts free text, so Watch always works.
- The historical date/time the user types is interpreted as **UTC** by the backend (see the dev
  handoff). No tz indicator is shown in the picker this iteration.
- At replay speed 1 the cockpit populates over roughly the real window length; higher speeds
  (2/5/10) populate faster.
