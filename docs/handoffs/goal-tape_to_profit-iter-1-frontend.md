# goal-tape_to_profit-iter-1 Frontend Handoff

**Phase:** goal-tape_to_profit-iter-1
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

- `NavBar.tsx` now renders its links from `GET /meta/ui-routes` (via the existing
  `NEXT_PUBLIC_API_URL` / `API_BASE` convention) — the backend route map is the single source
  of truth for the top bar (Data Contract row 35).
- The hardcoded `NAV_ITEMS` list is **deleted** — no hardcoded route list remains anywhere in
  the frontend, including as a fallback (grep-verified: no `NAV_ITEMS`, no `nav-link-disabled`).
- Explicit degraded state: if the route map is unreachable (or the fetch aborts after the
  `UI_ROUTES_REQUEST_TIMEOUT_MS` backstop), the bar shows the brand plus an honest amber
  placeholder (`data-testid="nav-unavailable"`, "navigation unavailable — backend
  unreachable") — never a fabricated link list.
- Preserved test ids and semantics for archived-era flows: `data-testid="app-nav"`,
  `data-testid="nav-link"`, `data-label`, `aria-current`, identical active/inactive Tailwind
  classes, `/journal/[id]` keeps Journal active (prefix match), Cockpit `/` exact-match only.
- Entries render in endpoint order, filtered to `nav: true` (`/journal/[id]` is `nav: false`
  in the map and is correctly not a top-bar link).

## Visual Delta

None intended: same three links (Cockpit · Journal · Studies), same styling, same active
accent. The rendering SOURCE changed (hardcoded list → canonical route map). New state: the
degraded placeholder, visible only when the backend is unreachable.

## Files Changed

- `apps/frontend/components/NavBar.tsx` — route-map-driven rendering; degraded state; list deleted
- `apps/frontend/lib/config.ts` — `UI_ROUTES_REQUEST_TIMEOUT_MS` (single-source constant)

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: passes (type-check + compile; `/`, `/journal`, `/journal/[id]`, `/studies` all emitted)

Real-browser sanity (Chrome via CDP, services on :8301/:3301):
- Loaded state: exactly 3 `nav-link` elements, labels Cockpit/Journal/Studies, hrefs
  `/`, `/journal`, `/studies`; Cockpit active on `/`; Journal active with emerald class on
  `/journal`; no `nav-unavailable` present.
- Backend killed: `nav-unavailable` placeholder rendered, 0 `nav-link` elements, `app-nav`
  container intact.

## Known Issues

- Links appear only after the client-side route-map fetch resolves (SSR emits the bar with the
  brand only). The fetch is a local sub-100ms call; browser flows that assert nav links should
  (and already do) await elements rather than the first paint.
