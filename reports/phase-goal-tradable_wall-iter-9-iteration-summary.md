# Iteration Summary — goal-tradable_wall-iter-9

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 9

## In plain words

**What you can do now:** Today you can open the Structure page and see a short, focused list of the handful of price levels that actually matter for a stock, instead of hundreds of noisy lines; browse a searchable library of real historical examples of how price reacted at those levels across a panel of 12 well-known stocks, including the real recorded trade-by-trade activity around a touch once it has been captured; and read an honest report comparing whether any of three trading strategies actually made money on recorded market data. In the cockpit you can also watch live, simulated, or replayed charts that highlight nearby key price levels with a plain-language note about what the tape is doing. Everything you could already do continues to work the same way from update to update.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. We built the plumbing so the Edge Report panel can eventually load in seconds instead of many hours, but that speed-up hasn't been switched on with real data yet, so the page looks and behaves exactly as it did before.

**What's next:** Next, the team will keep running the usual round of building, checking, and testing to move the project forward.

## Headline

Edge Report gains a rebuildable, checksum-keyed cache so warm reads resolve in seconds, not hours

## Direction

**Signal:** holding
**Why:** All seven required Must-have journeys (J-01–J-07) remain passing/already_passing with zero regressions and zero anti-goal violations, so the floor stays fully intact. This iteration's own target — the enhancement journey J-08 (a rebuildable, checksum-keyed Edge Report cache) — passed dev, review, QA, and closure-audit with its keyless core thoroughly verified (44 net-new tests, full suite 1392 passed/7 skipped/0 failed, `config_fingerprint` unchanged at `4d665603569b9dbf`), but journey-history hasn't been updated to reflect it yet pending the evaluator's own run, and the real ~10+h cache warm-up remains an untouched operator-gated carry — so this reads as holding rather than a confirmed improving step.

**Trend (last 5 iters):**
- Newly passing this iter: none recorded (eval.md for iter-9 not yet produced at summary time)
- Newly passing in last 5 iters total: J-04 (iter-4), J-05 (iter-6), J-06 (iter-7), J-03 (iter-8)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iter-5, a backend-only enabler pass)

**Latest evaluator reasoning:** "GOAL_ACHIEVED — all seven Must-have journeys are passing/already_passing, no unresolved anti-goal violation, coherence COHERENCE-PASS, no journeys-changed.md drift (all 7 spec-hashes match current goal text)." "Not REGRESSION (nothing regressed, no critical anti-goal); not STALLED (the blocker is resolved); not CONTINUE/ESCALATE (every journey passes, no fail-open, no cross-cutting ambiguity)."

## What was done

- Added `EdgeReportCache`, a rebuildable two-layer result cache (durable SQLite WAL layer + in-process atomic fast path) around the ~10+h `run_strategy_comparison_report` sweep, keyed on dataset checksums + strategy registry + `config_fingerprint` + a justified, tested 4th whole-config-content hash.
- Wired `GET /research/edge-report` (and its byte-identical MCP proxy) through the new cache via a DI'd `get_edge_report_cache()` dependency; response shape and byte-identity unchanged, `edge_report.py` stays the sole computer.
- Built and unit-tested the keyless PnL-history append machinery (`pnl_ledger.py`/`pnl_history.py`) that records a completed 3-way comparison to `reports/pnl/pnl-history.md`, additive beside the existing two-way row branch, train/hold-out and feeds never pooled.
- Caught and fixed a real byte-identity bug found during implementation (sorted-key JSON serialization broke REST/MCP wire-byte identity on a durable-cache hit); added a dedicated regression test.
- Added 44 net-new backend tests (16 cache-unit incl. a 16-thread torn-read guard, +7 edge-report wiring, +4 API-level, +9 pnl-ledger, +7 pnl-history CLI); full suite 1392 passed / 7 skipped / 0 failed, `config_fingerprint` unchanged at `4d665603569b9dbf`.
- Review PASS, QA PASS, audit PASS_WITH_GAPS (machinery independently re-verified; sole gap is the warm render never observed live), closure-verdict CLOSURE-PASS.
- Browser QA: 7 of 11 tests passed (4 skipped under a documented, independently-verified cold-cache carve-out; 0 failed) — J-03/J-05/J-06/J-07 regression checks all confirmed green with screenshot/DOM evidence.

## What's left

- Operator must run the real ~10+h Edge Report compute over the 11 credentialed `sip` datasets to warm the cache for real — the machinery is built and tested keyless but never exercised against the live corpus.
- Once warmed, the finished 3-way comparison still needs to be appended to `reports/pnl/pnl-history.md` via the new (tested but unused) CLI tool; the committed ledger file remains untouched.
- The warm-cache Edge Report render has never been observed live in a browser — third consecutive iteration (iter-6/8/9) showing only the loading state, because a real compute was genuinely in flight during this iteration's QA session.
- A future iteration must add a `/structure` render path for the new `strategy_comparison` PnL-ledger row type — today's page only looks up a single `founding` row, so a real append would otherwise stay invisible in the app.
- UT-11's band-overlay/confluence-chip did not appear in any of 4 sampled historical AAPL windows despite price sitting inside the pinned band's range twice — plausibly tied to the cold edge-report cache but not independently confirmed.
- The `[NEW]`-flagged demo-narrator walkthrough was SKIPPED this iteration (an unrelated schema-validation bug on an empty-string filter-clear step in the demo script) — no captured demo evidence yet.
- Pre-existing `scripts/dev.sh` process-cleanup gap (uvicorn/next-server grandchildren survive a plain kill) remains unfixed, first flagged at iter-8.

## Next step

Run the full pipeline on the next phase.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-tradable_wall-iter-9-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser.
2. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
3. If step 2 showed the already-resolved outcome, refresh this page (press F5) and watch the "Edge Report" panel again.
4. Scroll back to the top of the page. Type `AAPL` into the "Symbol" field, type `2026-06-22T21:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click the "Load" button.
5. Look at the button just below the Tradable Map panel.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-9-dev.md |
| Review | PASS | reports/reviews/goal-tradable_wall-iter-9-review.md |
| Browser QA | PASS | reports/phase-goal-tradable_wall-iter-9-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-9-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-9-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-9-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-9-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-9-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-tradable_wall-iter-9-ux-regression.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-9-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-tradable_wall-iter-9-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-9-closure-verdict.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
