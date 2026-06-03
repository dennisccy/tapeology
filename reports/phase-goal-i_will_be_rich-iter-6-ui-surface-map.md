# Phase N — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-6
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No frontend code changed this iteration. The surfaces below are **existing** components on the
single `/` cockpit route whose **displayed data changes** because `SIM-CHOP` now streams a driven
choppy tape (previously it emitted zero events). Every row is a behavior-via-data change verified
against the now-active stream.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Tape-state panel (headline + confidence bar) | Changed behavior (data-driven) | Driven `SIM-CHOP` now warms to `unclear`; previously silent cold-start | Watch `SIM-CHOP`; confirm headline reads **"Unclear"** and confidence shows **0.20** (< `reasonable_confidence`). Confirm amber via **base-selector probe** `.text-amber-400{` / `.bg-amber-500{` (exclude `:hover`/variant forms) + `getComputedStyle` — not eyeballed, not grep-substring |
| `/` | Tape-state panel (no-call assertion) | Changed behavior (data-driven) | Honesty surface now exercised on driven chop | Watch `SIM-CHOP`; confirm the UI does **not** show buyer_control, seller_control, bid_absorption, or ask_absorption — no decisive/absorption headline anywhere |
| `/` | Features panel | Changed behavior (data-driven) | New driven chop readouts | Watch `SIM-CHOP`; confirm `aggressive_buy_ratio` and `aggressive_sell_ratio` both display **< 0.60** (~0.50), `average_spread` **> 0.06**, and `buy_price_impact` / `sell_price_impact` both display **0.0** (genuine, not fabricated decisive numbers) |
| `/` | Quote panel | Changed behavior (data-driven) | Wide jittery quote now streams for `SIM-CHOP` | Watch `SIM-CHOP`; confirm the displayed spread is wide (> 0.06) and the quote's near side jitters; numerics are monospaced |
| `/` | Observations panel | Changed behavior (data-driven) | Unclear rationale now shown for driven chop | Watch `SIM-CHOP`; confirm an observation like "Mixed or weak evidence — no clear side in control" appears |
| `/` | Event-log panel | Changed behavior (data-driven) | Cold-start transition lines verified live (J-07) | On a **fresh backend**, watch `SIM-BUYER` as the **first** watch; confirm a **"Tape state changed to buyer_control"** line appears **live** (no reload). Repeat on a fresh backend with `SIM-SELLER` → **"Tape state changed to seller_control"** (≥2 distinct states) |
| `/` | Event-log panel (negative case) | Changed behavior (data-driven) | Honest absence of spurious transition | Watch `SIM-CHOP`; confirm **no** "Tape state changed to …" line appears (cold→warmed unclear is not a state change) |
| `/` | Top-bar scenario indicator | Changed behavior (data-driven) | `unclear_chop` label now backed by a driven stream | Watch `SIM-CHOP`; confirm the indicator reads **`unclear_chop`** |
| `/` | Recent Trades panel | Changed behavior (data-driven) | Chop trades stream at a constant price | Watch `SIM-CHOP`; confirm trades show a constant price (100.00) with mixed buy/sell/unknown sides |
| `/` | Live WebSocket stream (all panels) | Changed behavior (data-driven) | Chop read streams without reload | Watch `SIM-CHOP`; confirm the `unclear` state and choppy values appear and update **live over the WebSocket without a page reload** |

### Regression surfaces (must stay green — re-verify, no code change)

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Tape-state + all six panels | Changed behavior (none expected) | Classifier/config untouched — guard against regression | Watch `SIM-BUYER`; confirm six panels live and **buyer_control / emerald** (J-01, J-02) |
| `/` | Tape-state panel | Changed behavior (none expected) | Guard | Watch `SIM-SELLER`; confirm **seller_control / rose** (J-03) |
| `/` | Tape-state panel | Changed behavior (none expected) | Guard | Watch `SIM-BIDABS`; confirm **bid_absorption / amber** (J-04) |
| `/` | Tape-state panel | Changed behavior (none expected) | Guard | Watch `SIM-ASKABS`; confirm **ask_absorption / amber** (J-05) |
| `/` | Tape-state panel + Features (single-source) | Changed behavior (none expected) | J-08 extended to fifth state | Watch `SIM-CHOP`; confirm UI `unclear` + confidence **==** `GET /tape/SIM-CHOP/state` and UI feature readouts **==** `/features` |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/providers/simulated.py` — added `_chop_stream()`, the `_CHOP_*` shape
  constants, and the `SIM-CHOP` branch in `stream()`. This is provider/simulator data; it has no
  *direct* UI coupling, but it drives the data the existing `/` cockpit displays (mapped above).
- `apps/backend/tests/test_scenario.py`, `test_classifier.py`, `test_api.py` — new/updated tests
  only; no UI surface.
- **No change** to `app/engine/classifier.py` or `app/config.py` (red-flag guard honored — the
  chop reads `unclear` purely through existing gate/fallback logic).

---

## Summary

- **Frontend surfaces changed:** 0 (no frontend code change; 9 existing surfaces show changed
  data + 5 regression-guard surfaces to re-verify)
- **New pages/routes:** 0
- **Modified components:** 0 (data-driven behavior changes only)
- **Navigation changes:** no
- **Backend-only changes:** 4 files (1 product provider + 3 test files)
