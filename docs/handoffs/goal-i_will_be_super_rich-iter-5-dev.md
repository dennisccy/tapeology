# goal-i_will_be_super_rich-iter-5 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-5
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

> Overwrites the prior **stale verify-only** handoff. iter-5 is a real engine build per the
> authoritative phase spec (Mode: next, Depth: full): it builds **J-16** — a resolved aggressor
> side via the quote rule + a Lee-Ready **tick-test fallback**.

## What Was Built

- **Two-stage aggressor classification (J-16).** `classify_aggressor` is now:
  - **Stage 1 — the quote rule (unchanged, takes precedence):** with a quote in effect,
    `price >= ask ⇒ BUY`, `price <= bid ⇒ SELL`.
  - **Stage 2 — Lee-Ready tick-test fallback (fires ONLY when stage 1 is undecided: no quote in
    effect, OR the print is strictly between bid and ask):** compare to the **prior trade price** —
    uptick ⇒ BUY, downtick ⇒ SELL, zero-tick ⇒ carry the **last non-zero tick direction**.
  - **Honest-undecidable guard:** no quote **and** no prior trade (or a zero-tick before any
    direction exists) ⇒ `UNKNOWN`. The function never fabricates, invents a quote/trade, or uses
    wall-clock/randomness — it is pure and deterministic.
- **Carried engine state for the tick test.** `TapeEngine` now carries `last_tick_dir` (seeded
  `None` at construction, so a fresh watch / re-watch after Stop starts with no direction). The
  prior-trade price comes from the **existing** `MarketState.last` (read before `update_trade`), so
  no new parallel store was added.
- **Single source of truth preserved.** The one resolved `side` flows through the existing single
  path only — the `recent_trades` row **and** `FeatureEngine.add_trade(...)` (which feeds
  `aggressive_buy_ratio` / `aggressive_sell_ratio` / `net_aggressive_volume`). No second side
  computation exists anywhere (no serializer/API/provider/UI/new-module recompute).

## Result on real data (the J-16 fidelity gain, proven in-loop, offline, no creds)

Replaying the committed **real** Ford fixture (`F_20260602_150000_20260602_150200.json`, 65 trades /
1772 quotes, IEX, self-documented "REAL captured market data — not synthesized") through the engine:

| Rule | `unknown` fraction |
|------|--------------------|
| Quote-only (old) | **13 / 65 = 20.0%** |
| Quote rule + tick test (new) | **0 / 65 = 0.0%** |

The half-cent mid-spread prints (e.g. `16.565` inside a `16.56 / 16.57` quote) that the quote-only
rule left `unknown` are now resolved by the tick test. Recent-trades is no longer dominated by
`unknown` — exactly the J-16 acceptance.

## Files Changed

- `apps/backend/app/engine/aggressor.py` -- two-stage rule (quote-rule precedence + tick-test
  fallback); signature now `classify_aggressor(trade, quote, prior_trade_price=None, last_tick_dir=None)`;
  rewritten docstring. Still operates only on `TradeEvent`/`QuoteEvent`/`Side` (provider-agnostic).
- `apps/backend/app/engine/tape_engine.py` -- carry `self._last_tick_dir` (seeded `None`); at the
  trade call site, read `prior_trade_price = self._market.last` and pass both into
  `classify_aggressor` **before** `update_trade` (ordering preserved); update the carried direction
  from each non-zero price tick.
- `apps/backend/tests/test_aggressor.py` -- kept all 6 quote-rule cases green; added 8 tick-test
  cases (no-quote uptick/downtick/zero-tick-carry, mid-spread uptick/downtick/zero-tick-carry,
  quote-rule-precedence regression, and the two honest-`UNKNOWN` guards).
- `apps/backend/tests/test_historical_provider.py` -- added 5 J-16 tests: real-fixture
  `unknown`-fraction reduction (below 0.05 **and** strictly below quote-only), a concrete
  mid-spread "rescued print" example, per-print determinism (+ identical ratios/net volume),
  single-source (displayed side == feature-counted side via 300s-window net-volume reconstruction),
  and empty-window-no-fabrication.

**Not changed (intentionally):** `app/engine/market_state.py` (its existing `last` already returns
the prior trade price at classify time — no redundant accessor added) and `app/config.py` (the tick
test uses exact `==` for zero-tick — a pure rule with no numeric cutoff, so no magic-number config
was introduced).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **141 passed, 1 skipped (gated live-integration), 0 failed** (exit 0).
Baseline was 128 passed / 1 skipped → **test count strictly increased by 13** (+8 aggressor, +5 historical).

Regression sweep (all green): sim scenarios `test_scenario.py` (15 tests — SIM-BUYER/SELLER/BIDABS/
ASKABS/CHOP each resolve at confidence ≥ threshold), `test_api.py` (J-08 REST==WS single source,
stop/re-watch), `test_features.py`, `test_classifier.py`, `test_live_*`, `test_symbols_search.py`,
`test_market_clock.py`, `test_real_data_gate.py`.

## Service Startup Verification

Started `uvicorn main:app` on an isolated port; `GET /health` → `{"status":"ok"}`;
`POST /watch/SIM-BUYER` → `buyer_control` @ confidence ~0.79 (≥ reasonable threshold);
recent-trades carried resolved sides; `DELETE /watch/SIM-BUYER` → clean stop. Test server was
killed afterward (no stray processes left; the harness frontend was not touched — backend-only change).

## Known Issues

- **No frontend change (by design).** The recent-trades panel already renders `side` from the
  snapshot; the more-resolved side appears automatically. No UI recompute was added.
- **Credentialed live/historical replay is confirmatory only.** Per the iter-2 lesson, the
  authoritative J-16 proof is the committed real-vendor fixture replayed in-loop (deterministic,
  offline). A credentialed browser/historical run, if QA has keys, should agree but is not required
  for the proof.
- The carried tick direction is per-ticker engine state seeded empty at watch start; the very first
  zero-tick-before-any-direction print on a brand-new watch is honestly `UNKNOWN`. This is the
  intended deterministic behavior, not a defect.
