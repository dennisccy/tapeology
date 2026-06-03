# Phase goal-i_will_be_rich-iter-4 — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

> **No frontend code changed this iteration.** Every surface below is affected by *content* (the backend now emits `seller_control` for `SIM-SELLER`), not by a code edit. The existing already-generic, rose-ready components render the new state. "Change Type" reflects the user-visible content/behavior change, not a file edit.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `TapeStatePanel` — headline state label | Changed behavior (new content) | Backend now emits `seller_control`; `stateColor("seller_control")` first on-screen render | Type `SIM-SELLER`, click **Watch**, wait ~5s; assert the headline reads **"Seller Control"** and `getComputedStyle(headline).color` is rose `rgb(251, 113, 133)` (`text-rose-400`), explicitly NOT slate `rgb(226, 232, 240)` |
| `/` | `TapeStatePanel` — confidence bar fill | Changed behavior (new content) | Confidence ≥ `reasonable_confidence` (0.60) now reached for the down-tape; rose fill via `stateBarColor` | After SIM-SELLER resolves, assert confidence value ≥ 0.60 and `getComputedStyle(barFill).backgroundColor` is rose `rgb(244, 63, 94)` (`bg-rose-500`) |
| `/` | `FeaturesPanel` — `aggressive_sell_ratio` row | Changed behavior (new content) | Seller scenario produces a high aggressive sell ratio | After SIM-SELLER resolves, assert the `aggressive_sell_ratio` cell shows a high value (≥ 0.60) |
| `/` | `FeaturesPanel` — `sell_price_impact` row | Changed behavior (new content) | Negative price impact is the keystone seller guard; cell colored via `impactColor` | After SIM-SELLER resolves, assert `sell_price_impact` displays a **negative** number and its cell computes rose `text-rose-400` via `impactColor` |
| `/` | `ObservationsPanel` | Changed behavior (new content) | Seller observations now emitted by the classifier | After SIM-SELLER resolves, assert the list contains "Seller aggression increasing", "Price falling on sell prints", and "Spread stable and narrow" |
| `/` | `EventLogPanel` | Changed behavior (new content) | State-generic transition emitter now fires for the seller state | After SIM-SELLER resolves, assert the event log contains the line **"Tape state changed to seller_control"** |
| `/` | `Cockpit` (live WS updates) | Changed behavior | Same snapshot now carries seller values; pushed over WebSocket | After watching SIM-SELLER, observe values updating WITHOUT a page reload (confidence climbs as window fills) |
| `/` | `TopBar` ticker input + **Watch** button | No change (re-verify regression) | Free-text input already accepts `SIM-SELLER`; drives the seller read | Type `SIM-SELLER` and `SIM-BUYER` (separately), Watch each; confirm input accepts both and triggers a resolve |
| `/` | `TapeStatePanel` + `FeaturesPanel` for `SIM-BUYER` | Regression re-verify (NOT changed) | New seller branch must not perturb the buyer read (J-01/J-02) | Watch `SIM-BUYER`; assert headline reads "Buyer Control" in green `rgb(74, 222, 128)` at confidence ≥ 0.60 — unchanged from before |
| `/` | `TopBar` error surface | Regression re-verify (NOT changed) | No-fabrication error path must still hold (no fabricated snapshot) | Type `NOPE123`, click Watch; assert `POST /watch` returns 400 and the UI surfaces the error message with no cockpit snapshot rendered |

---

## Backend-Only Changes (No UI Impact)

These changes have no *direct* UI surface — they are the engine plumbing that produces the content rendered above:

- `apps/backend/app/config.py` — added `min_aggressive_sell_ratio` (0.60) and `max_sell_price_impact` (−0.02); reused existing side-neutral scales/weights. No UI surface; affects the threshold at which the existing panels flip to seller_control.
- `apps/backend/app/engine/classifier.py` — added `STATE_SELLER_CONTROL`, the seller gate, `_seller_confidence`, `_seller_observations`; buyer/unclear paths behaviourally unchanged. The visible output (state, confidence, observations) flows through the existing single snapshot consumed by REST/WS/UI — no second producer, no parallel path.
- `apps/backend/app/providers/simulated.py` — added `_seller_control_stream()` and wired `SIM-SELLER`; renamed four side-neutral shape constants (values unchanged). Drives the real events behind the seller read.
- `apps/backend/tests/test_classifier.py`, `apps/backend/tests/test_scenario.py` — test-only; no UI impact.

---

## Summary

- **Frontend surfaces changed:** 0 code edits; 7 surfaces show new content + 3 regression re-verify surfaces on the single `/` cockpit
- **New pages/routes:** 0
- **Modified components:** 0 (no code change; existing `TapeStatePanel`, `FeaturesPanel`, `ObservationsPanel`, `EventLogPanel`, `Cockpit`, `TopBar` render the new state)
- **Navigation changes:** no
- **Backend-only changes:** 4 files (config, classifier, simulator, tests)
