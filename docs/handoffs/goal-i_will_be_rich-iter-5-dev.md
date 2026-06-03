# goal-i_will_be_rich-iter-5 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

The absorption pair — **bid_absorption (J-04)** and **ask_absorption (J-05)** — the product's
defining "price impact, not raw aggression" case. Identical high one-sided aggression now
resolves to *control* when price actually moved and to *absorption* when the quote held.

**Backend (net-new):**
- **Three features** added to `FeatureEngine` (additively; the existing nine are byte-identical):
  - `bid_refresh_score` — among aggressive-**sell** prints, the fraction at which the bid HELD
    (did not fall below its in-window high-water mark). 1.0 when the bid refreshes under
    selling (SIM-BIDABS); ~0 when it walks down (SIM-SELLER).
  - `ask_refresh_score` — the strict mirror over aggressive-**buy** prints (ask did not rise
    above its in-window low-water mark).
  - `absorption_score` — summary of "high dominant aggression × flat matching impact"; high
    only when both hold. Collapses to 0 on real directional progress.
- **Bid/ask price series threaded** into `_Window` / `FeatureEngine.add_quote(...)` and the
  `TapeEngine.process_event` quote branch (additively) so the refresh scores can correlate
  each print with the quote in effect. `average_spread` computation is untouched.
- **Two classifier states** `bid_absorption` / `ask_absorption` with gates inserted **after**
  the buyer/seller-control gates and **before** the `unclear` fallback (control precedence).
  Each absorption gate uses the **exact complement** of the control impact condition
  (bid_absorption needs `sell_price_impact > max_sell_price_impact` where seller_control needs
  `<=`), so control and absorption are **mutually exclusive on impact** — the keystone guard.
- **Absorption confidence** (side-neutral): rewards aggression past floor, FLATNESS of impact
  (near-zero — the opposite of the directional impact component), a narrow spread, and refresh
  past floor. Reuses the shared `confidence_weights`, so absorption stays calibrated with the
  directional states (a symmetric absorption read scores the same 0.8542 the symmetric
  buyer/seller cases pin; SIM-BIDABS/ASKABS resolve at 0.9167).
- **Absorption event-log message** emitted once, in the engine emitter, from REAL in-window
  evidence on the transition into an absorption state: "Large sell/buy print absorbed" (when a
  large print is present) and "Bid/Ask refreshing at <price>". The existing "Tape state changed
  to …" transition line still fires.
- **Two simulated streams** wired into `SimulatedProvider.stream()` (`SIM-BIDABS`, `SIM-ASKABS`
  previously emitted nothing): heavy one-sided aggression into a quote that **holds at one
  price**, so the matching price impact is exactly flat (no off-price print, which would
  reintroduce tick-to-tick impact and corrupt the "no price progress" signal).
- **Config-only thresholds** (no magic numbers): `min_bid_refresh_score`,
  `min_ask_refresh_score`, `absorption_flat_band`, `refresh_scale`. Side-neutral existing
  values (`max_stable_spread`, ratio floors, the control cutoffs, `reasonable_confidence`,
  `confidence_weights`) are reused.

**Frontend:**
- `FeaturesPanel.tsx` — three new rows (`absorption_score`, `bid_refresh_score`,
  `ask_refresh_score`; 3 decimals, neutral text, not color-by-sign).
- `TopBar.tsx` — the **stream-status dot** now reads the canonical `snapshot.stream_status`
  (connecting/live/stale/closed) when a snapshot is present, falling back to the client
  `connStatus` only for the pre-snapshot idle/connecting affordance. This removes the parallel
  client-side "is the stream live" source and fixes the real divergence: when a bounded sim
  stream exhausts and the engine flips `stream_status → "closed"`, the dot now tells the truth
  instead of a stale client "live". (No backend change was needed — `stream_status` was already
  computed, serialized, and threaded to `TopBar`.)

## Files Changed

**Backend**
- `apps/backend/app/config.py` — added `min_bid_refresh_score`, `min_ask_refresh_score`,
  `absorption_flat_band`, `refresh_scale`.
- `apps/backend/app/engine/features.py` — `bid`/`ask` threaded into `_Window`/`add_quote`;
  `_refresh_fraction` (high/low-water correlation) and `_absorption_score`; three features
  added to `FEATURE_NAMES` and the `compute()` output.
- `apps/backend/app/engine/classifier.py` — `STATE_BID_ABSORPTION` / `STATE_ASK_ABSORPTION`;
  two gates; `_absorption_confidence`; bid/ask absorption observations.
- `apps/backend/app/engine/observations.py` — emitter now takes bid/ask/large-print evidence
  and emits the absorption message on the transition into an absorption state.
- `apps/backend/app/engine/tape_engine.py` — threads `bid`/`ask` into `add_quote`; passes the
  absorption evidence to the emitter.
- `apps/backend/app/providers/simulated.py` — `_bid_absorption_stream()`,
  `_ask_absorption_stream()`, wired into `stream()`; SIM-CHOP remains the only reserved-unresolved.
- `apps/backend/tests/test_classifier.py` — fixture gains the 3 absorption keys (default 0.0 =
  no refresh evidence); 8 new tests incl. the keystone precedence guards.
- `apps/backend/tests/test_features.py` — `_known_engine` updated to the new `add_quote`
  signature; 6 new refresh/absorption tests + a no-fabrication test.
- `apps/backend/tests/test_scenario.py` — SIM-BIDABS/SIM-ASKABS resolution + determinism +
  no-misroute regression guards; the reserved-unresolved assertion moved to SIM-CHOP.
- `apps/backend/tests/test_api.py` — absorption single-source agreement test; the live
  SIM-BUYER test now **freezes the feeder** before the cross-view comparison (see Known Issues).

**Frontend**
- `apps/frontend/components/FeaturesPanel.tsx` — three absorption rows.
- `apps/frontend/components/TopBar.tsx` — dot reads canonical `snapshot.stream_status`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **53 passed** (31 baseline + 22 new), stable across repeated runs and 10× on the
previously-flaky live test.

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully**, type-check clean.

Live HTTP smoke (uvicorn on an isolated port, `TAPEOLOGY_FEED_PACE=0.01`):
- `SIM-BIDABS` → `bid_absorption`, conf 0.9167; `sell_ratio=1.000`, `sell_price_impact=+0.0000`
  (flat), `bid_refresh_score=1.000`, `absorption_score=1.000`; event log: "Large sell print
  absorbed", "Bid refreshing at 100.00"; `/state` and `/summary` agree.
- `SIM-ASKABS` → `ask_absorption`, conf 0.9167; `buy_ratio=1.000`, `buy_price_impact=+0.0000`
  (flat), `ask_refresh_score=1.000`; event log: "Large buy print absorbed", "Ask refreshing at
  100.02".
- `SIM-BUYER` → `buyer_control` (NOT ask_absorption), `absorption_score=0.000`;
  `SIM-SELLER` → `seller_control` (NOT bid_absorption) — the keystone, end-to-end.

Server processes started for the smoke test were killed; none left running.

## Known Issues

- **Live SIM-BUYER test was stabilized (not a product bug).** The pre-existing
  `test_watch_sim_buyer_resolves_and_views_agree` compared a still-*climbing* `confidence`
  across two *separate* live HTTP reads; the background feeder advances the snapshot between
  reads, so the two values can differ by one tick. My per-tick compute cost (refresh
  correlation + absorption_score across 5 windows) shifted the feeder's wall-clock timing and
  exposed this latent race (it was 8/8 green at baseline, ~4/5 after). Fix: the test now
  **freezes the feeder** (`manager.shutdown()` + settle) before the cross-view comparison, so
  every view reads one identical engine snapshot — making the exact single-source assertion
  deterministic (10/10 green). The engine itself is single-source; the serializer-level tests
  prove that race-free on one snapshot.
- **SIM-BIDABS/SIM-ASKABS are 100% one-sided by design.** Flat price impact requires every
  consecutive print at one price; any off-price minority print reintroduces tick-to-tick impact
  via the cumulative-delta computation and would corrupt the keystone "no price progress"
  signal. "Majority aggressive sells/buys" is therefore realized as the degenerate (cleanest)
  100% case. Documented inline in `simulated.py`.
- **`absorption_score` is a display/summary feature**, not a gate input — the gate keys on the
  refresh score + flat-impact condition + ratio + spread (per the spec's gate definition). It
  is shown in the Features panel and read by J-04/J-05.
- **`stream_status = "stale"`** is enumerated and handled defensively by the dot map, but no
  code path sets it yet (no provider-gap detector this iteration).
- The on-screen **computed-style amber probe** for the resolved absorption render is the
  browser-QA gate; at the build level the base selectors `.text-amber-400{…}` and
  `.bg-amber-500{…}` are confirmed present in the served CSS bundle, and `format.ts` already
  maps both absorption states to amber.

## Suggested Next Phase

**J-06 (unclear / choppy tape).** Author an *actively choppy* `SIM-CHOP` stream (mixed two-sided
aggression, wide/jittery spread, no clean price impact) that the engine resolves to `unclear`
at low confidence — proving honest uncertainty against a *driven* stream rather than mere
silence. After that, **J-09** (the Stop / `DELETE /watch` UI control + return-to-idle), which
the stream-status-dot consolidation landed here as groundwork for.
