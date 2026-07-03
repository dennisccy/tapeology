# Iteration Summary — goal-tape_to_profit-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-03
**Iteration:** 3

## In plain words

**What you can do now:** Type in a stock ticker (or use a built-in demo ticker) and watch Tapeology read live trade-by-trade activity, showing moment to moment whether buyers or sellers are in control. Write trading ideas into a journal and revisit them later, and run replay studies against past market activity. The product can permanently store slices of historical market data — checked for tampering on every read and locked forever as "practice" or "final exam" data once saved — and it can now run a defined trading strategy against that saved data to get back an honest report on whether the strategy would have made or lost money, always shown next to a fair random-guessing comparison. Other software tools, including AI assistants, can connect directly to read all of this information.

**What changed this time:** This round added the actual profit-testing engine. You can now take historical data saved in earlier rounds, run a trading strategy against it, and get back a detailed, honest report — how many trades it made, how many won, the overall result — with a random-guessing comparison shown alongside every number so results can't be dressed up to look better than they are. Running the exact same test twice was proven to give back the exact same result. This is working behind the scenes for now, reachable by the tools built in earlier rounds — there's no new screen to look at yet.

**What's next:** Next, the product will start keeping a permanent scoreboard — a running record of the honest profit-or-loss result of every new trading idea as it's tried, so results build up over time instead of disappearing after each test.

## Headline

J-03 ships: strategy grammar v1 + deterministic backtest engine (product's first PnL measurement machinery)

## Direction

**Signal:** improving
**Why:** J-03 (strategy grammar v1 + deterministic backtest engine) moved from failing to passing this iteration, independently cross-checked by the evaluator via a full suite re-run, direct inspection of all three J-03 screenshots, and three separate byte-identity proofs. J-01, J-02, and J-08 were all re-verified passing with explicit evidence rows and no regressions or anti-goal violations were found. Three of the last four iterations have each landed exactly one newly-passing journey, and the evaluator's next-step recommendation (J-04, the PnL ledger) is concrete and already unblocked.

**Trend (last 4 iters):**
- Newly passing this iter: J-03
- Newly passing in last 4 iters total: J-01 (iter-1), J-02 (iter-2), J-03 (iter-3)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 1 of last 4 (iteration 0, baseline verification)

**Latest evaluator reasoning:** J-03 passes on independently cross-checked evidence: full suite re-run green by this evaluator (952 collected — 951 passed / 1 skipped, exact match to dev + reviewer; +50 tests over iter-2, none deleted), the 42 new backtest/API/no-broker tests green, and all three J-03 screenshots inspected — the 404→200 flip, a done report carrying per-trade fills/fees/slippage, aggregates (net/gross R AND $, win rate 0.2, max drawdown, n=5), seeded null baseline (seed 1729, entry_count 100), full verbatim provenance, and the exact register string, plus honest 404/422 error legs. Byte-identity verified three ways (QA's two independent POSTs → identical 59,157-char result blocks; dev's live 59,844-byte re-POST; the API-level test). J-01/J-02/J-08 all re-verified with explicit result rows (replay lane crashed, browser-qa ran the fallback legs per the iter-1 lesson).

## What was done

- Added a config-owned strategy grammar v1 (`Config.strategy_definition`) reusing the existing state-native entry-arming rules — no new indicators or inline thresholds
- Built the deterministic, seeded backtest runner (`app/research/backtests.py`) and a cancellable `BacktestJobManager` mirroring the studies job pattern; identical requests reproduce byte-identical results
- Added four REST routes (create/list/detail/cancel) on the existing research router with an honest 404/422/409 validation matrix, serving stored rows verbatim
- Added the `backtests` table via a proven v7→v8 schema migration tested against a committed old-schema fixture; rows survive store reload
- Added a signal-bearing repo-wide no-broker/order/account grep test, proven non-vacuous against a seeded counter-example
- Flipped the MCP `backtests` tool from honest 404 to live data with a surgical two-string description-only diff — zero proxy-logic changes
- Grew the backend suite from 901 to 951 passed / 1 skipped (+50 tests, none deleted); engine-equivalence suite still 7/7
- Verified 1 target journey (J-03) passes browser QA; re-verified J-01, J-02, J-08 all still passing with explicit evidence rows

## What's left

- Journey J-04 (Every enhancement lands one honest row in the PnL ledger) failing — next target
- Journey J-05 (The /performance page reports PnL per enhancement honestly) failing
- Journey J-06 (Indicator profiles are versioned; the default stays byte-identical) failing
- Journey J-07 (The candidate sweep survives hold-out or says so honestly) failing
- Environment: `/tmp` per-user tmpfs quota pinned by ~4.5G of accumulated pytest basetemp dirs — destabilizes Playwright/Chrome browser lanes; evaluator was permission-denied to clear it, carried forward as an operator must-fix
- Known limitation: the null baseline can honestly serve fewer than the configured draw count when a seeded draw lands before the first recorded price (documented behavior, not a defect)

## Next step

Iter-4 targets J-04 (the append-only PnL ledger) at lean depth — the next link in the J-02→J-03→J-04→J-05 chain: the founding baseline row evaluates strategy v1 on profile `default` over the committed fixture train AND hold-out datasets using this iteration's backtest reports, exposed at `GET /research/pnl/ledger` plus the pure-rendered `reports/pnl/pnl-history.md`; the MCP `pnl_ledger` tool flips from its last remaining honest 404. Environment must-fix to carry into iter-4: clear `/tmp/pytest-of-dennis-chan` (~4.5G, pinning the per-user tmpfs quota) or route pytest basetemp off tmpfs — otherwise browser lanes and large suite runs stay flaky.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tape_to_profit-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-tape_to_profit-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-tape_to_profit-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-tape_to_profit-iter-3-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-tape_to_profit/iter-3/eval.md |
| Journey history | — | runs/goal-session-tape_to_profit/state/journey-history.json |
