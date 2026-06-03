# Phase N — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `FeaturesPanel` → three new rows (`Absorption score`, `Bid refresh score`, `Ask refresh score`) | New table rows | J-04/J-05 require the operator to read the absorption/refresh numbers | Watch `SIM-BIDABS`; in the Features panel confirm rows "Absorption score", "Bid refresh score", "Ask refresh score" appear below "Large prints", show 3-decimal numerics in slate (not green/red), and `Bid refresh score` reads elevated (≈1.000) |
| `/` | `TapeStatePanel` → `bid_absorption` state render | Changed behavior (newly reachable state) | SIM-BIDABS now drives the bid_absorption state | Watch `SIM-BIDABS`; confirm the Tape-state headline reads "Bid Absorption" in amber (`text-amber-400`) with the confidence-bar fill amber (`bg-amber-500`) at confidence ≥ reasonable_confidence, and it is NOT "Seller Control" |
| `/` | `TapeStatePanel` → `ask_absorption` state render | Changed behavior (newly reachable state) | SIM-ASKABS now drives the ask_absorption state | Watch `SIM-ASKABS`; confirm the Tape-state headline reads "Ask Absorption" in amber with amber confidence-bar fill, and it is NOT "Buyer Control" |
| `/` | `EventLogPanel` / `ObservationsPanel` → absorption message | Changed behavior | Engine now emits an absorption event-log message on the absorption transition | Watch `SIM-BIDABS`; confirm the Event log shows "Large sell print absorbed" and "Bid refreshing at <price>" (real price, e.g. 100.00) alongside the "Tape state changed to bid_absorption" line |
| `/` | `TopBar` → status dot + label (top-right) | Changed behavior | Dot now reads canonical `snapshot.stream_status` instead of client `connStatus` | Watch a bounded sim stream until it exhausts; confirm the dot turns rose with label "closed" once the engine flips `stream_status` to closed, and matches `GET /tape/{ticker}/summary`'s `stream_status` |
| `/` | `TopBar` → status dot on directional scenarios | Changed behavior (regression guard) | Same dot rewire must not destabilize live scenarios | Watch `SIM-BUYER`; confirm the dot stays emerald "live" while the stream is active (no false "closed"/"stale") |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — added `min_bid_refresh_score`, `min_ask_refresh_score`, `absorption_flat_band`, `refresh_scale` tuning thresholds — no UI surface; only influences computed values already displayed.
- `apps/backend/app/engine/features.py` — `_refresh_fraction` / `_absorption_score` and bid/ask threading into `_Window`/`add_quote` — internal computation; its outputs surface via the new Features rows (mapped above), not a new surface.
- `apps/backend/app/engine/classifier.py` — `STATE_BID_ABSORPTION` / `STATE_ASK_ABSORPTION`, the two gates, `_absorption_confidence` — internal logic; its outputs surface via the Tape-state panel (mapped above).
- `apps/backend/app/engine/observations.py` — absorption emitter — internal; output surfaces in the Event log (mapped above).
- `apps/backend/app/engine/tape_engine.py` — threads bid/ask + evidence to the emitter — internal wiring, no direct UI surface.
- `apps/backend/app/providers/simulated.py` — `_bid_absorption_stream()` / `_ask_absorption_stream()` wired into `stream()` — makes SIM-BIDABS/SIM-ASKABS produce data; effect is visible via the cockpit, not a standalone surface.
- `apps/backend/tests/*` (test_classifier, test_features, test_scenario, test_api) — test-only, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 2 components (`FeaturesPanel`, `TopBar`) on the single `/` cockpit, plus two newly-reachable states surfaced through existing panels (`TapeStatePanel`, `EventLogPanel`/`ObservationsPanel`).
- **New pages/routes:** 0 (all within the existing `/` cockpit)
- **Modified components:** 2 directly edited (`FeaturesPanel.tsx`, `TopBar.tsx`); 2+ panels render new engine outputs without code change
- **Navigation changes:** no
- **Backend-only changes:** 7 files (config, features, classifier, observations, tape_engine, simulated, tests) — all surface through the cockpit, none introduce a standalone backend-only-with-no-UI capability
