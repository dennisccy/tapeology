# Phase goal-i_will_be_super_rich-iter-3 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

> Wall-clock note: the market-status states ("open" vs "closed + next open") are session-dependent.
> At handoff time the US market was **closed**, so the closed/next-open branch is browser-verifiable
> now. If tested during US market hours, the indicator shows "open" and a Live watch returns the
> honest "streaming not implemented" state instead of the closed panel — in that case the closed
> branch is covered by the deterministic backend test (`FakeAdapter` clock=closed).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `MarketStatusIndicator` (new, in TopBar) | New component | Replaces hardcoded "unavailable" stub with the real row-8 session status | Select **Live** in the data-source selector; confirm the top-bar pill shows the real status — emerald "market open" or amber "market closed — next open <time>" (with creds), matching the actual US session. Confirm it is **not** the old static "unavailable" when creds are present. |
| `/` | `MarketStatusIndicator` — unavailable state | New component | Honest state when no credentials / clock unreachable | With no vendor credentials configured, select **Live**; confirm the pill shows amber "market unavailable" (never a fabricated "open" or "closed"). |
| `/` | `MarketStatusIndicator` — placeholder state | New component | Avoids fabricating a status before first fetch | Select **Live** and watch the pill on first paint; confirm it briefly shows a slate "…" placeholder before resolving to a real status (never flashes "open" first). |
| `/` | `MarketStatusIndicator` — poll cleanup | New component | iter-0 resource-leak lesson | Select **Live**, then switch the data-source selector to **Simulated** or **Historical**; confirm the market pill disappears (component unmounts) and no console errors / stray network polls to `/market/clock` continue. |
| `/` | `TopBar` (modified) | Changed behavior | Conditionally mounts the indicator only in Live mode | Toggle between Simulated / Historical / Live; confirm the market pill appears **only** in Live mode and the Watch form, symbol search, and Stop button are otherwise unchanged. |
| `/` | `ProviderUnavailable` — `market_closed` case | New form/panel variant | Completes J-14: honest closed-market state in place of cockpit | In **Live** mode while the market is closed, type `AAPL` in the symbol box and click **Watch**; confirm a centered amber **"Market is closed"** panel appears showing the phrase "market is closed" and the next-open time, with **no** quote/trades/state cockpit panels rendered. |
| `/` | `ProviderUnavailable` — next-open formatting | Changed display | Renders backend UTC instant in operator's local zone | On the "Market is closed" panel, confirm the next-open time is shown in your local timezone with an explicit zone label (not raw UTC like `...Z`). |
| `/` | `ProviderUnavailable` — existing 3 reasons | Unchanged (regression check) | Must stay byte-for-byte identical | Trigger `provider_unavailable` (Live with no creds), `symbol_not_tradable`, and `no_data_for_window`; confirm each still renders its original panel copy unchanged. |

---

## Backend-Only Changes (No UI Impact)

- `GET /market/clock` endpoint (`app/main.py`) — the canonical row-8 serving endpoint. Consumed by
  the frontend via `getMarketClock()` (so it IS visible through `MarketStatusIndicator`), but the
  endpoint's `next_close` field is not surfaced in any UI element.
- `MarketClock` record + `get_market_clock()` on the adapter Protocol (`providers/adapters/base.py`)
  — vendor-neutral data plumbing, no direct UI surface.
- `AlpacaAdapter.get_market_clock()` (`providers/adapters/alpaca.py`) — vendor translation, read-only
  reference call, no UI surface.
- Market-closed pre-flight gate in `POST /watch/{ticker}` (`app/main.py`) — drives the `market_closed`
  panel above; the gate logic itself is backend.
- `RealDataError.next_open` extension + exception handler (`app/main.py`) — carries `next_open` to the
  frontend; surfaced via the panel above.
- `CONFIG.market_closed_status_code = 409` (`app/config.py`) — tunable, no UI surface (frontend keys
  off the `reason` string, not the HTTP code).
- `FakeAdapter` clock + tests (`tests/fakes.py`, `tests/test_market_clock.py`,
  `tests/test_real_data_gate.py`) — test-only, no UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 (the persistent TopBar gaining the live market-status indicator; the `ProviderUnavailable` honest panel gaining a `market_closed` variant)
- **New pages/routes:** 0 (still exactly one screen, `/`)
- **Modified components:** `TopBar`, `ProviderUnavailable`, `app/page.tsx` (failure-state threading); new components `MarketStatusIndicator`, `lib/datetime.ts` (`formatMarketTime`)
- **Navigation changes:** no
- **Backend-only changes:** 7 (clock endpoint + record + adapter method + pre-flight gate + RealDataError extension + config tunable + tests)
