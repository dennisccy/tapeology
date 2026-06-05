# goal-i_will_be_super_rich-iter-5 Audit Report

**Date:** 2026-06-05
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-16 is genuinely implemented as a two-stage aggressor classifier (quote-rule precedence + Lee-Ready tick-test fallback), and the headline fidelity claim was independently re-derived from the engine — not merely trusted from the report. On the committed real Ford fixture the engine resolves 65/65 prints (0% `unknown`) versus 13/65 (20%) under the quote-only rule, with zero quote-decided prints overridden by the tick test, so the absorption/control regression surface (J-04/J-05) is provably untouched. The change is surgical (4 files), deterministic, single-source, provider-agnostic, and adds no magic number; the full backend suite is 141 passed / 1 skipped / 0 failed.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified): Two-stage rule and quote-rule precedence are correct in code.**
`apps/backend/app/engine/aggressor.py:42-59`. Stage 1 returns BUY for `price >= ask` and SELL for `price <= bid` whenever a quote is present; only a strictly mid-spread print (or no quote at all) falls through to the tick test. I confirmed the precedence is not just unit-tested but holds on the real stream: replaying the Ford fixture, **0** prints that the quote-only rule decided were flipped by the two-stage rule (recomputed independently, not from the report). This is the load-bearing guarantee that J-04/J-05 absorption (aggressive prints at/through the quote) cannot be silently reclassified.

**B2 — OBSERVATION (verified): Engine state-carry and ordering are correct.**
`apps/backend/app/engine/tape_engine.py:67-79`. `prior_trade_price = self._market.last` is read *before* `self._market.update_trade(event)`, so at classification time `MarketState.last` is the immediately preceding trade — the ordering the tick test depends on. The carried `self._last_tick_dir` (line 42, seeded `None`) is updated purely from the consecutive trade-price move (`event.price > / < prior_trade_price`), independent of how `side` was classified. This is the correct Lee-Ready definition (carry the last non-zero *tick* direction, not the last classified side), and it keeps the zero-tick carry honest.

**B3 — OBSERVATION (verified): Single caller; all feed paths benefit uniformly.**
`classify_aggressor` has exactly one production caller (`tape_engine.py:68`); the sim, paced-historical, and live feeders in `apps/backend/app/watch_manager.py:129/156/198` all route through `engine.process_event`, so the new carried state applies identically across all three with no signature drift. No second side computation exists in serializers, API, providers, or a new module.

**B4 — OBSERVATION (verified): Determinism boundary on re-watch is real.**
`apps/backend/app/watch_manager.py:116-124` (`stop`) deletes the engine from `self._engines`, so a subsequent `watch()` constructs a fresh `TapeEngine` with `_last_tick_dir = None`. Each ticker holds its own engine instance, so the carried direction never leaks across tickers or across a Stop→re-watch cycle — matching the spec's determinism-boundary note exactly.

**B5 — OBSERVATION (verified): No magic number introduced.**
The tick test uses exact `==` for the zero-tick case and has no numeric cutoff, so correctly no constant was added to `app/config.py`. This satisfies the no-magic-numbers anti-goal rather than violating it; adding a tolerance constant would have been the wrong call here.

### Frontend Findings

**F1 — OBSERVATION: No frontend change, correctly.**
`Frontend Present: no` for this iteration and the spec explicitly scopes the frontend to "None" — the recent-trades panel already renders `side` (buy/sell/unknown, color-coded) from the snapshot, so a more-resolved side surfaces automatically with no UI recompute. This is consistent with the single-source architecture principle (frontend renders engine values verbatim). No misleading-UI risk: the UI reads the one value the engine produced.

### Test Findings

**T1 — OBSERVATION (verified): Fidelity test is an honest comparison, not a tautology.**
`apps/backend/tests/test_historical_provider.py:158-179`. The quote-only baseline (`_quote_only_sides`) is an *independent* re-implementation of the OLD rule, deliberately not calling `app.engine.aggressor`, so "strictly lower than quote-only" is a real comparison. The keystone test (`test_tick_test_reduces_unknown_fraction_on_real_fixture`, lines 186-209) asserts tight bounds: `quote_only_unknown > 0.15` (the baseline really leaves a chunk unknown), `two_stage_unknown < quote_only_unknown` (strictly lower), `two_stage_unknown <= 0.05` (absolute bound), and `resolved/total >= 0.90` (J-16 acceptance). I reran the underlying computation directly: 0.0 vs 0.2, 13 rescued, 1.0 resolved — all assertions are satisfied with margin.

**T2 — OBSERVATION (verified): Single-source test is behavioral, not cosmetic.**
`test_displayed_side_equals_feature_counted_side_single_source` (lines 243-259) reconstructs `net_aggressive_volume` from the *displayed* `recent_trades` sides and asserts it equals the `FeatureEngine`'s reported number over the 300s window (no eviction across the 2-min fixture). This genuinely proves the displayed side and the feature-counted side are the same value — it would fail if any second side computation diverged.

**T3 — OBSERVATION (verified): Fabrication and zero-tick-boundary guards are explicit.**
`test_no_quote_and_no_prior_trade_is_unknown`, `test_mid_spread_with_no_prior_trade_is_unknown`, `test_zero_tick_before_any_direction_is_unknown` (test_aggressor.py:108-128) and `test_empty_window_produces_no_fabricated_side` (test_historical_provider.py:262-266) cover every honest-undecidable path the anti-goal demands. Determinism is covered by `test_real_fixture_sides_are_deterministic` (two independent engines → identical per-print sides AND identical ratios/net volume).

**T4 — OBSERVATION (verified): Regression sweep is real.**
`test_scenario.py` (15 tests: SIM-BUYER/SELLER/BIDABS/ASKABS/CHOP) is green, re-proving the sim path now that `aggressor.py` is no longer a 0-line diff. Full suite reran by the auditor: **141 passed, 1 skipped (gated live-integration), 0 failed, exit 0**; baseline was 128 → +13 tests (+8 aggressor, +5 historical), so the count strictly increased as required.

---

## 3. Domain Assessment

The core domain logic is correct and faithful to the documented Lee-Ready algorithm. The two-stage rule preserves the economically meaningful precedence (a print that lifts the offer or hits the bid is classified by the quote, full stop), and only fills the previously-`unknown` gap (mid-spread or pre-quote prints) with the tick test. Crucially, the carried direction is the last non-zero *price tick*, not the last *classified side* — the standard and correct formulation; carrying the classified side instead would have let a quote-rule SELL contaminate a later zero-tick into SELL even after an uptick sequence, which would be subtly wrong. The implementation avoids that trap.

The no-fabrication guarantee is intact at the only place it matters: with no quote and no prior trade (or a zero-tick before any direction exists), the function returns `UNKNOWN` — and the real fixture still leaves such prints honest rather than forced. The fidelity gain (20% → 0% on a liquid penny-quoted name) is exactly the "real recent-trades no longer dominated by `unknown`" outcome J-16 targets, and it was achieved without retuning any classifier threshold or feature formula (out-of-scope items genuinely untouched: no `/history`, no pause/resume, no local-time picker, no second vendor, no quote-rule retune).

The remaining J-17–J-20 are correctly left unbuilt for later slices, matching the spec's stated single-slice scope. No scope drift.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found; every DEFINITION OF DONE item is implemented and independently verified in code and by recomputation. No surgical fix was warranted.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed. This iteration cleanly delivers the J-16 foundation (resolved aggressor side) that the later slices depend on. The natural next slice is J-17+J-18 (the price/candlestick chart with tape-state markers, plus `GET /tape/{ticker}/history` and the engine history buffer), as the spec's OUT OF SCOPE and BACKGROUND already sequence. The evaluator should admit J-16 as passing into `journey-history.json` and carry J-17–J-20 as still-to-build, alongside the J-01–J-15 regression confirmation this iteration re-proved.
