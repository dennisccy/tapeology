# goal-i_will_be_rich-iter-4 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

The `seller_control` tape-state path — the strict negative mirror of `buyer_control` —
so watching `SIM-SELLER` now resolves a real, measured down-tape read (it previously
hung at cold-start `unclear` forever). All net-new **backend** work; **no frontend code
changed** (the UI was already generic and rose-ready — verified by build + live smoke).

- **`config.py`** — two seller-gate thresholds as the negative mirror of the buyer set:
  - `min_aggressive_sell_ratio = 0.60` (mirror of `min_aggressive_buy_ratio`).
  - `max_sell_price_impact = -0.02` (the **negative** keystone mirror of
    `min_buy_price_impact = +0.02`). `seller_control` requires `sell_price_impact <= -0.02`,
    i.e. price actually fell. The side-neutral scales/weights (`ratio_scale`, `impact_scale`,
    `speed_scale`, `max_stable_spread`, `min_trade_speed`, `confidence_weights`,
    `reasonable_confidence`, `max_confidence`, `warmup_min_events`) are **reused unchanged** —
    no per-side duplication, so buyer/seller confidence stay calibrated identically.
- **`classifier.py`** — added `STATE_SELLER_CONTROL` plus a `seller_control` gate that is the
  strict mirror of `buyer_control`: over the primary window ALL of
  `aggressive_sell_ratio >= 0.60` AND `sell_price_impact <= -0.02` (negative — **price impact,
  not aggression**) AND `average_spread <= max_stable_spread` AND `trade_speed >= min_trade_speed`,
  emitting `seller_control` only when confidence `>= reasonable_confidence`, else staying
  `unclear`. Added `_seller_confidence` (impact component scores the *magnitude* of the
  negative impact past the negative cutoff) and `_seller_observations`
  ("Seller aggression increasing" / "Price falling on sell prints" / "Spread stable and
  narrow"). The buyer branch is behaviourally unchanged (only the local `gate` variable was
  renamed `buyer_gate` for clarity alongside the new `seller_gate`).
- **`simulated.py`** — added `_seller_control_stream()` (deterministic, seeded) and wired
  `elif self.ticker == "SIM-SELLER": yield from self._seller_control_stream()`. The dominant
  prints are aggressive **sells that hit the bid**; on a controlling-side tick (same
  probability the buyer stream lifts) the quote **drops one tick** (bid and ask both down) so
  `sell_price_impact` accumulates genuinely **negative**. The four side-neutral shape
  constants were renamed to role-neutral names (`_P_MINORITY`, `_P_QUOTE_MOVE`,
  `_MAJORITY_SIZES`, `_MINORITY_SIZES`) with identical values and are now shared by both
  streams; the buyer stream's emitted output is byte-identical (guarded by the existing
  determinism test). The other three reserved sims (SIM-BIDABS / SIM-ASKABS / SIM-CHOP) still
  emit nothing.

## Files Changed

- `apps/backend/app/config.py` — added `min_aggressive_sell_ratio` + `max_sell_price_impact` (negative); reused all side-neutral scales/weights.
- `apps/backend/app/engine/classifier.py` — added `STATE_SELLER_CONTROL`, the seller gate, `_seller_confidence`, `_seller_observations`; buyer/unclear paths behaviourally unchanged; updated module docstring (two → three states).
- `apps/backend/app/providers/simulated.py` — added `_seller_control_stream()`; wired `SIM-SELLER` into `stream()`; renamed the four side-neutral shape constants to role-neutral names (values unchanged) now shared by both streams.
- `apps/backend/tests/test_classifier.py` — added the seller mirror tests: `test_seller_control_with_reasonable_confidence` (pins 0.8542), `test_price_impact_guard_zero_impact_is_not_seller_control`, `test_price_impact_guard_positive_impact_is_not_seller_control`, `test_wide_spread_blocks_seller_control`, `test_default_buyer_features_do_not_trip_seller_gate`.
- `apps/backend/tests/test_scenario.py` — added `test_sim_seller_settles_on_seller_control` + `test_sim_seller_is_deterministic`; **moved** `test_reserved_ticker_known_but_unresolved` to the still-reserved `SIM-BIDABS` (SIM-SELLER is now driven), keeping the `build_provider("NOPE123") is None` assertion.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **31 passed, 0 failed** (was 24 — +7 new seller tests: 5 classifier + 2 scenario;
the previously-green 24 buyer/unclear/aggressor/features/api tests all still pass unchanged).

Frontend build: `cd apps/frontend && npm run build` → **clean** (compiled, type-check passed,
4 static pages; no frontend code changed).

### Live verification (not just mocked)

A live uvicorn instance was started and driven through the real REST path (then torn down):
- `POST /watch/SIM-SELLER` → **200**; the state resolved `unclear` (conf 0.10) → **seller_control**
  live within ~4–5 s of watching, climbing past `reasonable_confidence` (observed 0.7536 at
  timestamp 22 s, still rising as the 30 s window fills).
- Final summary read: `tape_state=seller_control`, `aggressive_sell_ratio=0.881`,
  `sell_price_impact=-0.350` (negative), bid/ask fell to `99.81/99.83`, spread `~0.02`,
  observations = the three seller messages; the event log contained
  **"Tape state changed to seller_control"**.
- Anti-goal/no-fabrication paths held live: `POST /watch/NOPE123` → **400**;
  `GET /tape/SIM-ASKABS/state` (known but not watched) → **404**.

### Symmetry cross-check (transparent)

Running SIM-BUYER and SIM-SELLER through the engine for the same event count yields a
perfect reflection: **identical confidence 0.8605** both sides; `aggressive_sell_ratio 0.910`
= buyer's `aggressive_buy_ratio 0.910`; `sell_price_impact -0.430` = −(buyer's `+0.430`);
price path mirrored (buyer → 100.56/100.58, seller → 99.44/99.46). SIM-BUYER still settles on
`buyer_control` — the new seller branch does not perturb the buyer read.

## Known Issues

- None. All spec In-Scope items are implemented and all DoD backend items verified.
- The exact confidence differs by construction between the **unit** test (0.8542, a fixed
  synthetic symmetric input) and the **scenario** stream (~0.86 at full warm-up; 0.75 mid-fill).
  This is expected — the scenario stream's live ratio/impact (0.91 / −0.43) is slightly past
  the synthetic test's (0.90 / −0.40). Both are comfortably `>= reasonable_confidence (0.60)`;
  the scenario test asserts the threshold, not a pinned value, exactly as the buyer scenario test does.
- The **browser gate for J-03 is still required** (this handoff covers backend + a REST/live
  smoke only). The on-screen rose render via the dynamic `stateColor("seller_control")` —
  headline `text-rose-400` → `rgb(251,113,133)` and confidence-bar fill `bg-rose-500` →
  `rgb(244,63,94)`, measured by base-selector stylesheet probe + `getComputedStyle`, explicitly
  not slate `rgb(226,232,240)` — must be verified by browser-qa-agent. Precondition per the
  iter-1 lesson: `rm -rf apps/frontend/.next`, restart the managed dev server with
  `NEXT_PUBLIC_API_URL` set, confirm HTTP 200 before driving (an all-SKIPPED run is not verification).

## Suggested Next Phase

**J-04 (bid_absorption)** is the natural and intended next step: high aggressive **sell**
volume **without** the price drop must resolve to `bid_absorption`, *not* `seller_control`.
This iteration's negative-impact guard is exactly the prerequisite that makes that distinction
meaningful — it requires adding the absorption features (`absorption_score`, `bid_refresh_score`)
and the `SIM-BIDABS` stream (sells hit a bid that refreshes at the same price → ~0 sell impact).
The **stream-status-dot consolidation** (drive the top-bar dot from the engine's canonical
`snapshot.stream_status` rather than the client `connStatus`) remains deferred but **must land
before** the J-04/J-05 (no-data) and J-09 (teardown) journeys — not forgotten.
