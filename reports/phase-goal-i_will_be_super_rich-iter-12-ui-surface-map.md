# Phase goal-i_will_be_super_rich-iter-12 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `PriceChart` — horizontal time axis | Changed behavior | Axis now maps logical bin time to true clock time via the backend `epoch_anchor` | Watch `SIM-BUYER` (sim mode), wait for bars to appear, confirm the axis tick labels read `dd-MM-yyyy HH:mm:ss` (e.g. `02-01-2024 09:30:00`) and NOT a bare elapsed-seconds counter like `60` or `120` |
| `/` | `PriceChart` — crosshair tooltip | Changed behavior | Crosshair timestamp is now the true clock time, not elapsed seconds | Hover over a candle in the populated `SIM-BUYER` chart and confirm the crosshair label shows `dd-MM-yyyy HH:mm:ss` in 24-hour local time |
| `/` | `PriceChart` — tape-state marker labels | Changed behavior | Marker timestamps now show true clock time so the user can tell when a classified state occurred in real market time | After `SIM-BUYER` classifies `buyer_control`, confirm the marker stamp on the chart reads a real clock time (e.g. `02-01-2024 09:30:19`) not an elapsed value like `19` or `19.5` |
| `/` | `PriceChart` — bar-size switcher (10 / 30 / 60 s) | Changed behavior | Axis must remain in true clock time at every bar-size setting | Switch bar size from 10 s to 60 s while `SIM-BUYER` is populated; confirm the axis tick labels still show `dd-MM-yyyy HH:mm:ss` after the switch |
| `/` | `PriceChart` — empty-window state | Changed behavior | An absent or zero-bar window must not fabricate axis timestamps | Open a Historical session with a ticker that returns no bars; confirm the chart shows the "No price history for this window yet" hint and the axis contains no timestamp labels |
| `/` | `TopBar` — Historical date input | Changed behavior | Native `<input type="date">` replaced by a custom validated `dd-MM-yyyy` text field | Switch to Historical mode; confirm the date field shows a text box with placeholder `dd-MM-yyyy` (not the browser's native date picker); type `08-06-2024` and confirm the Watch button becomes enabled |
| `/` | `TopBar` — Historical date input inline validation | New component behavior | Invalid dates must show an inline error instead of silently no-opping | In Historical mode type `31-02-2026` in the date field; confirm the field border turns amber and an error message appears; confirm the Watch button remains disabled |
| `/` | `TopBar` — watched-source descriptor | Changed behavior | ISO-8601 timestamps embedded in the descriptor string are now reformatted to `dd-MM-yyyy HH:mm` (local zone) | After a successful historical watch (any real symbol), inspect the descriptor text at the top of the cockpit and confirm it reads `dd-MM-yyyy HH:mm` dates (e.g. `14-05-2024 09:30`) — no `YYYY-MM-DD` or `T13:30:00.000Z` remains |
| `/` | `MarketStatusIndicator` — "next open" time (Live mode, closed-market state) | Changed behavior | Market close/open times previously showed "Jun 8"-style locale dates; now routed through the shared `dd-MM-yyyy` formatter | With the market closed (or in a timezone where the market reads as closed), confirm the "next open" time in the market-status panel reads `dd-MM-yyyy HH:mm UTC±HH:MM` rather than a locale or ISO date |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — added `sim_session_anchor_epoch = 1704205800.0` constant — the chart reads this value through the history endpoint, so it is fully surfaced via the UI; listed here only for completeness of the backend-change record.
- `apps/backend/app/engine/snapshot.py` — additive `epoch_anchor: float | None = None` field on the engine snapshot — no UI impact on its own; surfaced through the history serializer.
- `apps/backend/app/engine/tape_engine.py` — accepts and exposes the `epoch_anchor` from the provider — backend plumbing only.
- `apps/backend/app/providers/simulated.py` / `historical.py` / `live.py` — each provider now declares its `epoch_anchor` — backend plumbing only.
- `apps/backend/app/watch_manager.py` — `_provider_anchor` helper threads the anchor into the engine — backend plumbing only.
- `apps/backend/app/serializers.py` — `serialize_history` now includes `epoch_anchor` in the response — the frontend reads this field; no UI surface change beyond what is already covered in the PriceChart row above.
- `apps/backend/app/main.py` — `/history` route passes `engine.epoch_anchor` to the projection — no independent UI surface change.
- `apps/backend/tests/test_epoch_anchor.py` (new) — backend test only; no UI impact.
- `apps/backend/tests/test_history_api.py` — updated assertion; no UI impact.
- `apps/frontend/lib/types.ts` — added `epoch_anchor: number | null` to `TapeHistory` type — TypeScript type only; no UI surface change.
- `apps/frontend/lib/api.ts` — `fetchHistory` reads `epoch_anchor` verbatim from the response — data layer; UI impact is through `PriceChart` (already covered above).

---

## Summary

- **Frontend surfaces changed:** 9
- **New pages/routes:** 0
- **Modified components:** 3 (`PriceChart`, `TopBar`, `MarketStatusIndicator`)
- **Navigation changes:** no
- **Backend-only changes:** 10 (plumbing and tests; all contract-new data fully wired to the chart)
