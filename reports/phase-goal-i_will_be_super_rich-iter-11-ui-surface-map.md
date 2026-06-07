# Phase goal-i_will_be_super_rich-iter-11 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `SymbolSearch` dropdown | Changed behavior | Real `AbortController` cancellation replaces late-drop `active` flag, preventing out-of-order results | Type "TS", immediately type "AAP"; confirm only suggestions matching "AAP" appear in the dropdown — no "TS"-matching results flash or overwrite the final list |
| `/` | `SymbolSearch` dropdown | Changed behavior | Client-side min-query now enforced from `config.ts` constant, mirroring the backend threshold | Type a single character (e.g. "A") into the symbol search box; confirm the dropdown shows nothing and no search request fires before a second character is entered |
| `/` | `SymbolSearch` dropdown | Changed behavior | Symbol universe pre-loaded at backend startup; first search no longer triggers a cold vendor round-trip | After a fresh backend restart, type "AAPL" into the symbol search box; confirm suggestions appear within one second (no multi-second stall on first use) |
| `/` | `SymbolSearch` dropdown — vendor-hiccup state | Changed behavior | Aborted request resolves to `[]`, not an error | Simulate a slow or cancelled search by typing quickly; confirm the dropdown shows no error banner and no stuck "Searching…" indicator when results are empty |
| `/` | Error/failure panel (row-9 `provider_timeout` message) | Changed behavior | Historical Watch timeout now emits the actionable oversize detail string instead of a generic message | Submit a Historical Watch for a very high-volume window (e.g. a liquid ticker over the market-open minute); confirm the failure panel shows the text "try a shorter range" (not a generic "please try again" or blank) |
| `/` | Cockpit panels (tape state, confidence, features) | Changed behavior | Warm-up events are now fast-forwarded in delivery pacing so the cockpit shows a meaningful read sooner | Submit a Historical Watch for a real ticker with a 2-minute window; confirm the tape-state panel shows a non-idle classification within a few seconds of the fetch completing, without waiting the full length of the data's original timeline |
| `/` | Cockpit — re-watch flow | Changed behavior | Same symbol+window is served from the in-process cache, skipping the vendor round-trip | Submit a Historical Watch, wait for the cockpit to populate, then Stop and submit the identical Watch again; confirm the cockpit re-populates in under one second (near-instant cache hit) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/providers/adapters/alpaca.py` — HTTP session-level timeout (`_with_http_timeout`) set on the SDK client's `requests.Session`; `VendorTimeout` exception mapping; concurrent `ThreadPoolExecutor` trades+quotes fetch; LRU+TTL window cache (`_cache_get`/`_cache_put`); `warm_symbol_universe()` + `_fetch_asset_universe()` (single-owner universe). All purely internal to the adapter — no new endpoint, no new displayed value.
- `apps/backend/app/providers/adapters/base.py` — neutral `VendorTimeout` exception class and `warm_symbol_universe()` protocol method added. No API surface change.
- `apps/backend/app/config.py` — new constants: `vendor_http_timeout_seconds`, `frontend_watch_request_timeout_ms`, `historical_cache_max_entries`, `historical_cache_ttl_seconds`, `warmup_fast_forward_pace_seconds`, `symbol_universe_refresh_seconds`. Not displayed; no UI surface.
- `apps/backend/app/watch_manager.py` — `_feed_paced` warm-up fast-forward (delivery pacing only; engine math and event ordering unchanged). The speed improvement is user-observable as a faster cockpit warm-up but involves no new UI element.
- `apps/backend/tests/fakes.py` — test double extensions (`warm_symbol_universe()`, `fetch_timeout` lever, `warm_raises` lever). Test infrastructure only.
- `apps/backend/tests/test_vendor_responsiveness.py` — 32 new unit tests. Test infrastructure only.
- `apps/backend/tests/test_vendor_timeout.py` — updated timeout-message assertion to match the new actionable oversize string. Test infrastructure only.
- `apps/frontend/lib/config.ts` — `SYMBOL_SEARCH_DEBOUNCE_MS` and `SYMBOL_SEARCH_MIN_QUERY` constants extracted (were previously inline literals in the component). No new UI surface; the behavioral effect is captured in the `SymbolSearch` rows above.

---

## Summary

- **Frontend surfaces changed:** 1 (the `SymbolSearch` component and the failure panel message on the single `/` cockpit page)
- **New pages/routes:** 0
- **Modified components:** 2 (`SymbolSearch.tsx`, `api.ts` — the `searchSymbols` function)
- **Navigation changes:** no
- **Backend-only changes:** 8 files (adapter, base protocol, config, watch manager, two test files, one test update, frontend config constants)
