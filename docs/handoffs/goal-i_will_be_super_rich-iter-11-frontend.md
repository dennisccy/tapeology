# goal-i_will_be_super_rich-iter-11 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built (UI)

J-30 frontend half — **cancellable, debounced, min-query symbol search**. This is the only
user-visible frontend delta this iteration: the symbol-search dropdown now behaves crisply. No new
page, route, nav, component, or displayed value — the action set is unchanged; only the
responsiveness/honesty of the existing search box changed.

- **Real request cancellation.** Each new debounced lookup now creates an `AbortController` and the
  effect cleanup `controller.abort()`s the prior in-flight request. Rapid typing no longer piles up
  requests, and a slow earlier response can never overwrite a newer result (no out-of-order
  flicker). This replaces the old late-drop `active` flag with genuine cancellation (the `active`
  guard is kept as a belt-and-braces check alongside `signal.aborted`).
- **Aborted ⇒ no result, never an error.** `searchSymbols(q, signal?)` resolves an aborted request
  to `[]` (not a throw), so a cancelled query simply shows nothing — no error banner, no stuck
  "Searching…". A vendor hiccup / empty list likewise shows no suggestions.
- **Client min-query mirrors the backend.** The dropdown only fires a lookup once the query reaches
  `SYMBOL_SEARCH_MIN_QUERY` (mirroring the backend `symbol_search_min_query`), avoiding an
  over-broad single-character scan. Free-text watch entry is unaffected — the user can still type
  and Watch a full symbol regardless of the dropdown.
- **Config-driven tuning (no magic numbers).** The debounce (`SYMBOL_SEARCH_DEBOUNCE_MS = 250`) and
  the min-query (`SYMBOL_SEARCH_MIN_QUERY = 1`) now live in `apps/frontend/lib/config.ts`, not as
  inline literals in the component.

## Files Changed

- `apps/frontend/lib/config.ts` — added `SYMBOL_SEARCH_DEBOUNCE_MS` + `SYMBOL_SEARCH_MIN_QUERY`;
  documented the J-28 backend<frontend timeout ordering invariant beside `WATCH_REQUEST_TIMEOUT_MS`.
- `apps/frontend/lib/api.ts` — `searchSymbols(q, signal?)` now accepts an `AbortSignal` and passes
  it to `fetch`; an aborted/failed request resolves to `[]`.
- `apps/frontend/components/SymbolSearch.tsx` — per-lookup `AbortController` (abort on cleanup);
  reads debounce-ms + min-query from config; enforces the client min-query; free-text entry
  unchanged; the existing dropdown idiom, loading/empty treatment, and outside-click close are
  preserved.

## States Handled

- **In-flight cancelled by a newer keystroke** → resolves to no result (no flicker of stale
  matches, no error).
- **Too-short query** (below min-query) → no lookup fires, dropdown shows nothing.
- **Vendor hiccup / empty list** → no suggestions, no error banner, no stuck spinner.
- **Loading** → the existing "Searching…" item shows during a live lookup (unchanged).

## Visual / Design System

No new components, colors, spacing, or effects. Reuses the existing `SymbolSearch` dropdown styling
(slate surface, mono symbol, muted name, hover/focus states) verbatim. The actionable
oversize/timeout error (J-28) surfaces through the **existing** error/failure panel + TopBar error
banner already wired to the row-9 `provider_timeout` reason — no frontend change was needed there
beyond the backend now sending the more actionable `detail` string (rendered verbatim).

## Tests / Verification

- `cd apps/frontend && npx tsc --noEmit` → clean (0 errors). `npm run build` was deliberately NOT
  run (a live harness `next dev` on :3650 shares `.next`; building corrupts it — the
  iter-3/6/8/10 lesson). Type-check writes no `.next`.
- The cancellation/min-query contract is also covered on the backend/API side
  (`test_vendor_responsiveness.py`: min-query drops a too-short query with no vendor call; a vendor
  error degrades to `[]`). The browser-side "crisp/instant, no pile-up, no out-of-order, first
  search after restart not a stall" is for browser-qa to confirm against an isolated stack (capture
  real timed evidence per the standing visual-evidence lesson).

## Known Limitations

- The "no out-of-order overwrite" guarantee relies on both the AbortController cancelling the
  network request AND the `active`/`signal.aborted` guard skipping a late resolution — verified by
  type-check + backend contract; the end-to-end timing is browser-verifiable.
