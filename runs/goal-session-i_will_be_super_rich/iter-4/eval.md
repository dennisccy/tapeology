# Iteration 4 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

iter-4 closed the **last two failing must-have journeys** — **J-12** (stream a real live ticker)
and **J-15** (a live-feed gap shows `stale`, then recovers) — with **zero regressions** and **no
anti-goal violation**. The full must-have set **J-01–J-15** now has positive passing evidence, the
coherence audit is **COHERENCE-PASS**, and the backend suite is **128 passed / 1 skipped (gated),
exit 0**. The goal is achieved — the loop halts with success.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | reports/qa/…-iter-4-evidence/UT-07-sim-buyer-control.png |
| J-02 | passing | passing | reports/qa/…-iter-4-evidence/UT-07-sim-buyer-control.png |
| J-03 | already_passing | already_passing (0-diff + green scenario suite) | reports/qa/…-iter-0-evidence/UT-J-03-SIM-SELLER.png |
| J-04 | already_passing | already_passing (0-diff + green classifier suite) | reports/qa/…-iter-0-evidence/UT-J-04-SIM-BIDABS.png |
| J-05 | already_passing | already_passing (0-diff + green classifier suite) | reports/qa/…-iter-0-evidence/UT-J-05-SIM-ASKABS.png |
| J-06 | already_passing | already_passing (0-diff + green suite) | reports/qa/…-iter-0-evidence/UT-J-06-SIM-CHOP.png |
| J-07 | already_passing | already_passing (0-diff) | reports/qa/…-iter-4-evidence/UT-07-sim-buyer-control.png |
| J-08 | already_passing | already_passing (SSOT TC-01 REST==WS) | reports/qa/…-iter-2-evidence/UT-06-historical-F-cockpit.png |
| J-09 | passing | passing | reports/qa/…-iter-4-evidence/UT-10-teardown-idle.png |
| J-10 | passing | passing | reports/qa/…-iter-4-evidence/UT-03-11-live-controls-idle.png |
| J-11 | passing | passing | reports/qa/…-iter-4-evidence/UT-08-historical-aapl.png |
| **J-12** | **failing** | **passing** | reports/qa/…-iter-4-evidence/UT-02-live-F-emerald.png |
| J-13 | passing | passing | reports/qa/…-iter-4-evidence/UT-08-historical-aapl.png |
| J-14 | passing | passing | reports/qa/…-iter-4-evidence/TC-14-honest-error-panel.png |
| **J-15** | **failing** | **passing** | reports/qa/…-iter-4-evidence/UT-09-stale-amber.png |

**J-12 (real live read):** Verified directly from UT-02 — a **real Alpaca live socket** through the
UI: emerald "● Live" dot, `scenario: live F`, real Ford penny-spread quote and real trades streaming
(15.38/15.39, SELL/UNKNOWN, sizes 718/600/695/1600/3300…), `stream_status=live`. The cold-start
"Unclear" read is honest on the wide free IEX top-of-book (correct per the iter-2 lesson, not a
defect). Backed by the hermetic pipeline test (TC-01: snapshot populates, classifies, REST==WS) and
— exceeding the goal's operator/gated bar — the **gated `test_live_integration.py` actually RAN and
PASSED** (market open + creds present at impl time; `wss://stream.data.alpaca.markets/v2/iex` →
1 passed).

**J-15 (stale → recover, no fabrication):** Verified directly from UT-09 — a quiet feed (ZZZQQ, which
does not print on the IEX feed) flips the canonical `stream_status` to **`stale`** (amber dot), with
QUOTE all "—", all features 0, RECENT TRADES "No trades yet" sustained ~17s = **zero fabricated
trades**. The stale→live **recovery** leg (not browser-forceable on a non-streaming symbol) is proven
by the hermetic deterministic test TC-02 (`test_live_feeder_flips_live_then_stale_then_recovers_…`)
asserting the exact transitions and an unchanged trade count across the lull — the same evidentiary
standard the evaluator accepted for J-14's hermetic FakeAdapter clock in iter-3.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path (critical) | OK | `git grep` for order/account/position APIs → zero. The 3 `TradingClient` sites are read-only `get_clock`/`get_asset`/`get_all_assets`; the new `stream_live` is market-data subscribe only. |
| Stay in scope (critical) | OK | No scanner/news/charting/portfolio added — only live streaming on the existing `/` cockpit. |
| Price impact over aggression (critical) | OK | Engine 0-diff; J-04/J-05 invariant-preserved. Live F read showed agg_sell 1.000 yet "Unclear" (not seller_control) at cold start — honest. |
| Honest uncertainty (critical) | OK | Live F + ZZZQQ both read "Unclear" with low confidence on weak/wide reads. |
| **No fabricated data (critical — primary for this iter)** | OK | ZZZQQ `stale` shows no trades, QUOTE "—", features 0 (UT-09). Watchdog fabricates nothing; live path never falls back to sim. |
| Single source of truth (critical) | OK | Live flows through the one engine; TC-01 asserts REST==WS; one `stream_status` owner (coherence-verified). |
| No magic numbers | OK | `stale_gap_seconds` added to `config.py`. `LIVE_TEARDOWN_GRACE_SECONDS` is an operational adapter constant (not an engine threshold) — accepted per review NOTE + coherence advisory. |
| Provider-agnostic engine | OK | Engine/API 0-diff; `AsyncProvider` is purely additive; vendor SDK confined to `adapters/alpaca.py`. |
| No secrets in source | OK | Only `.env.example` tracked with empty `ALPACA_API_KEY=`/`ALPACA_API_SECRET=`; no `.env` tracked; no committed key string. |
| Deterministic & reproducible | OK | Engine 0-diff; live maps real epochs → logical timeline; hermetic tests deterministic. |
| No ML in v1 | OK | Rule/threshold classifier unchanged (0-diff). |
| No trade/profit claims | OK | UI footer: "Descriptive only — not trading advice" (visible in UT-09). |

**Coherence:** COHERENCE-PASS (no structural veto) — one app, one source of truth per displayed value; the live half extends rows 1–6 through existing canonical owners with no parallel computation, no second endpoint, no second clock, no new nav surface.

## Next-Step Recommendation

**Halt — goal achieved.** All 15 must-have journeys (J-01–J-15) pass with positive evidence, no
critical anti-goal violation is open, and coherence passes. No required work remains. Any future work
is an explicitly-*later* `docs/goal.md` nice-to-have — Level 2 / `BookLevelEvent` +
`liquidity_pull_score`, the predictive-edge replay harness, or optional auto-reconnect of a dropped
live socket — none of which is needed for the current goal. A human resuming for those should dispatch
**lean** (additive, well-bounded, must not regress the now-complete must-have set).

## Halt Justification

Halting with **GOAL_ACHIEVED** because every Must-have user journey in `docs/goal.md` now has status
`passing` or `already_passing`, each grounded in concrete evidence I inspected directly (live cockpit
and stale-dot screenshots, the green 128-test suite, and independent `git` anti-goal checks); there
are **no** unresolved anti-goal violations (all 12 verified clean, the critical no-fabrication and
no-execution guarantees test-guarded and `git`-confirmed); and this iteration's `coherence.md` is
**COHERENCE-PASS**, so there is no structural veto. The two journeys that close the set — J-12 and
J-15 — were verified to a standard at or above the goal's own bar: J-12 with genuine real-Alpaca-socket
evidence (the gated integration check ran live), and J-15 with a directly-observed real `stale`
flip + zero fabrication plus a deterministic hermetic proof of the recovery transition. The real-data
half now reuses the exact same engine as the simulator, completing the product's defining promise.
