# Iteration 14 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean (n/a — goal achieved; halt)

## Summary

Iter-14 closes the two real-data defects (J-36, J-37) that the iter-13 synthetic-only "pass"
shipped, this time proven by **committed real-data CI tests that run without live credentials** —
the load-bearing anti-goal #20 gate. The real GME 14-05-2024 SIP drop now resolves to
`seller_control` at confidence 0.925 (vs `unclear` @ 0.200 with the override disabled — the fix is
load-bearing, independently verified by the evaluator), and a long/dense historical window loads
progressively (first chunk before the whole window) with no fabricate/drop/reorder/dedup and
byte-identical engine output vs single-shot. Coherence is PASS, the full J-01–J-35 regression floor
holds (283 passed / 1 credential-gated skip — independently re-run by the evaluator), and no
anti-goal remains violated. Every Must-have journey J-01–J-37 is now `passing`.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-36 (real directional move → control, proven by real fixture) | failing (reopened f3ea17c) | **passing** | `apps/backend/tests/test_real_data_classify.py` (5 green) — committed REAL GME SIP fixture `tests/fixtures/alpaca/GME_20240514_133013_133020_sip.json` (17,342 real trades, µs epochs, ~50bps SIP quote, no secrets) → `seller_control` @ 0.925; evaluator load-bearing check: override-disabled → `unclear` @ 0.200 |
| J-37 (long/dense window loads progressively, proven by real fixture) | failing (reopened f3ea17c) | **passing** | `apps/backend/tests/test_progressive_fetch.py` (9 green) — laziness (counting fake SDK: first chunk before whole window), no fabricate/drop/reorder/dedup, progressive==single-shot determinism over REAL GME records (final `seller_control`) |
| J-01–J-09 (sim scenarios) | passing | passing (no regression) | `test_scenario.py` (15) + `test_classifier.py` (20) + `test_classifier_relative.py` (15) green; sim fixtures byte-identical (override-off keystone) |
| J-11/J-16/J-17/J-18 (historical + chart) | passing | passing (no regression) | `test_historical_provider.py`, `test_history*.py`, `test_window_resolution.py` green; chart `/history` read path untouched |
| J-28/J-29/J-34 (vendor responsiveness) | passing | passing (no regression) | `test_vendor_*`, `test_chunked_fetch.py` green; backend bound < frontend timeout preserved |
| J-31/J-32 (true-clock axis, live speed) | passing | passing (no regression) | `test_epoch_anchor.py`, `test_speed_api.py` green; progressive anchor == single-shot anchor |
| J-33 (relative gates) | passing | passing (no regression) | `test_classifier_relative.py` negative guards: wide *relative* spread on weak tape still `unclear`; absorption gate stays exact complement of control impact |
| J-10/J-13/J-14/J-15/J-19–J-27/J-30/J-35 | passing | passing (carried; backend-only iter, no UI/contract change) | coherence.md PASS; `git diff --stat HEAD -- apps/frontend/` empty (frontend untouched) |

Full backend suite (evaluator re-run): **283 passed, 1 skipped** (the pre-existing
credential-gated live-integration test), zero regressions vs the iter-13 floor (259 + 24 new).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path | OK | No order/broker code; analysis-only |
| Stay in scope | OK | Backend correctness/perf only; no scanner/news/indicator/portfolio surface added |
| Price impact over raw aggression | OK | Override predicate requires real relative price impact AND ratio AND speed; absorption gates keep the spread term and stay the exact complement (keystone re-proven) |
| Honest uncertainty | OK | Override is the control predicate minus the spread term, engaging only within the 4× band; beyond the band a wide *relative* spread still vetoes (`test_spread_beyond_the_band_still_vetoes_control...`); weak/mixed tape still `unclear`/absorption |
| No fabricated data | OK | Progressive stitch preserves the exact real record set in epoch order (no fabricate/drop/reorder/dedup); empty chunks → no events, None anchor |
| Single source of truth | OK | Classifier reads spread/impact/price from the canonical FeatureEngine (no second computation); progressive==single-shot features byte-identical; coherence.md Part A PASS |
| No magic numbers | OK | `historical_feed`/`live_feed`, `directional_override_enabled`, `override_max_spread_multiple`, `override_spread_floor_score`, chunk caps all in `config.py` |
| Provider-agnostic engine | OK | Vendor `DataFeed` enum confined to `alpaca.py:_data_feed`; coherence.md confirms no leak; engine consumes the provider protocol only |
| No secrets in source | OK | Evaluator scanned iter-14 diff + fixture: no key/secret literals; `test_real_gme_sip_fixture_carries_no_credentials` asserts the fixture carries no credential fields |
| Deterministic & reproducible | OK | `test_real_gme_sip_replay_is_deterministic` + progressive==single-shot determinism; incremental feature rewrite byte-identical (audit 1,500-step differential, 0 mismatches) |
| No ML in v1 | OK | Rule/threshold classifier unchanged in kind |
| No trade/profit claims | OK | No claim added |
| Honest side inference | OK | Aggressor/tick-test side inference untouched |
| One focused chart, computed once | OK | Chart reads engine `/history` verbatim; markers carry engine state; no recompute |
| Honest pause | OK | Pause path untouched |
| Timezone-correct windows | OK | `split_window` operates on already-resolved tz-aware instants; `test_window_resolution.py` green (no tz shift) |
| No silent dead-clicks / no mute cockpit | OK | Frontend untouched; J-21–J-27 carried |
| Bounded, honest, performant vendor calls | OK | J-37 decouples time-to-first-data from total load (first chunk under budget, rest background); "very high-volume" is now a true backstop; backend bound < frontend timeout |
| Real-data journeys are proven with real data (#20) | OK | THE load-bearing constraint: J-36/J-37 are gated by committed real-data CI tests that run without live credentials and FAIL LOUDLY if the fixture is absent — never an operator-gated note. Evaluator independently ran them (14 green) and confirmed the override is load-bearing |

No critical anti-goal violation. The one honesty defect found during the iteration (misleading
"Spread stable and narrow" observation on the override path) was found and fixed by the auditor
(B1) — verified on the real GME replay, state/confidence unchanged, default path byte-identical.

## Next-Step Recommendation

Halt — goal achieved. All Must-have user journeys J-01–J-37 are `passing` with positive evidence;
J-36 and J-37 (the last two failing journeys, reopened in f3ea17c) are closed with committed
real-data CI evidence that runs offline. No anti-goal is violated and coherence is PASS.

## Halt Justification

GOAL_ACHIEVED is warranted because:
1. **Every Must-have journey J-01–J-37 has status `passing`** with positive evidence — no `failing`
   or `unknown` remains. The two reopened real-data defects (J-36, J-37) are the only ones that
   were failing at iteration start, and both now pass.
2. **The load-bearing anti-goal #20 is satisfied with positive evidence, not an operator note.**
   The evaluator independently ran `test_real_data_classify.py` + `test_progressive_fetch.py`
   (14 green) and confirmed the fix is load-bearing — replaying the same real GME SIP window with
   the directional override disabled yields `unclear` @ 0.200, while enabled yields `seller_control`
   @ 0.925. The fixture is unambiguously real (17,342 trades at µs epochs, realistic SIP spread,
   no secrets) and the tests fail loudly if it is absent.
3. **No critical anti-goal is violated.** Single-source-of-truth, provider-agnostic engine, no
   fabricated data, no secrets, determinism, and no-magic-numbers all hold (verified against the
   diff, coherence.md Part A, and the audit's differential checks).
4. **Coherence is PASS** — no structural veto.
5. **The full J-01–J-35 regression floor holds** — the evaluator re-ran the full suite: 283 passed
   / 1 credential-gated skip, byte-identical sim/absolute fixtures, zero regressions.
