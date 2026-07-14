# Iteration Summary — goal-tradable_wall-iter-2

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 2

## In plain words

**What you can do now:** You can watch simulated buy and sell pressure in the trading cockpit, keep a trading journal, replay past trading studies, check an honest profit scorecard, and view a stock's price structure — including fetching real historical prices from Yahoo Finance with one click — on the Structure page.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team built a research tool that automatically scans a much wider set of stocks and finds real historical moments where price touched one of those important levels, then labels what happened next — did price bounce away, break through, or just wobble with no clear outcome. It isn't shown on any screen yet, but it now has real evidence to draw on: over 800 real examples across all 12 watched stocks, including the exact example that started this whole effort.

**What's next:** Next, using the operator's trading-data credentials, the system will record the real trade-by-trade activity around the best of these examples so it can show what buying and selling pressure actually looked like at each wall.

## Headline

The wide scan: a case-study registry of 801 real band-touch events across 12 symbols

## Direction

**Signal:** improving
**Why:** J-02 (the touch-event scanner and case-study registry) was built and independently verified this iteration by review, QA, and audit: a live scan against the freshly-populated 12-symbol store found 801 real touch events (309 broke / 306 rejected / 186 chopped), comfortably clearing the ≥15-events/≥8-symbols target, and the pinned AAPL 2026-06-22 event confirmed `rejected` with both forward returns negative, exactly as specified. The audit found zero blocking issues and stated J-02's Definition of Done is fully met and its goal achieved; J-01 and J-07 both stayed green. The goal-evaluator had not yet logged a formal verdict for iteration 2 as of this summary (see "What's left"), so this reads the pipeline's own independent verification chain — dev, review, QA, audit, and closure all converged on PASS-class outcomes with zero contradiction, which is a strong improving signal even ahead of that final confirmation.

**Trend (last 2 iters):**
- Newly passing this iter: not yet logged by the goal-evaluator (see Why) — J-02 independently verified as meeting its Definition of Done by review/QA/audit
- Newly passing in last 2 iters total: J-01, J-07
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of 2

**Latest evaluator reasoning:** (most recently logged — iteration 1; the goal-evaluator has not yet logged iteration 2) "J-01's tradable level map is genuinely achieved — I did not trust the three PASS reports; I independently reproduced the headline via a direct `compute_tradability` call on the committed real AAPL fixture: 10 bands (5+5), basis 2026-06-18T04:00Z (holiday 06-19 skipped by the data, no hardcoded calendar), pinned resistance band [300.23,302.25] (contains 300.48+302.07, round-number 300 flagged) ranks #1. I personally confirmed config_fingerprint==4d665603569b9dbf, ran the REST==MCP byte-identity + levels.py byte-identity + 3 no-lookahead + lens-static guards (33 tradability tests green), and re-ran the J-07 sentinel myself (22 passed)."

## What was done

- Built `apps/backend/app/research/setups.py`, the sole owner of the touch-event/case-registry value; reuses `compute_tradability` (J-01) verbatim per session — never a second map/levels engine.
- Solved the central no-lookahead risk by threading `as_of` per session (never a shared/fixed value); proven by a positive regression test showing a swing-pivot band only appears once its confirming session's bars are visible, and correctly absent one session earlier.
- Classified touch reactions (`rejected`/`broke`/`chopped`) from the reaction-horizon close only, never intrabar wick or volume; a dedicated regression test proves a huge-volume, big-wick touch bar still reads `chopped`, not `rejected`.
- Added `GET /research/setups` + `GET /research/setups/{id}` + a byte-identical read-only MCP `setups` proxy, plus 5 new config-owned constants (12-symbol panel, reaction threshold, forward-return horizons, re-arm rule, retention window) — all excluded from `config_fingerprint`, which stayed frozen at `4d665603569b9dbf`.
- Populated the live bar store for all 12 panel symbols via the existing keyless Yahoo store-first flow (36/36 fetches succeeded), then ran the scanner live: 801 real touch events across 12/12 symbols (309 broke / 306 rejected / 186 chopped) — comfortably clearing the ≥15-events/≥8-symbols target; the pinned AAPL 2026-06-22 event confirmed `rejected` with both forward returns negative (-0.46%, -4.27%).
- Full backend suite green: 1274 collected / 1268 passed / 6 skipped / 0 failed (+34 new tests); frozen foundations (levels/tradability/backtests/tape engine/BarStore) byte-identical; J-01 and J-07 re-confirmed still green.
- Cleared review (PASS_WITH_NOTES), QA (PASS, 13/13 test cases), audit (PASS_WITH_GAPS, zero blocking issues — "J-02 fully meets its Definition of Done and its goal is achieved"), and closure (CLOSURE-PASS). Browser QA correctly SKIPPED — backend + MCP only, no UI surface this iteration.

## What's left

- Journey J-03 (Real tape at the wall — credentialed event-window recording) still failing — feature code not yet built, and separately credential-gated (operator Alpaca keys not yet configured in this environment).
- Journey J-04 (The edge report — what actually profits, under the existing gates) still failing — not yet built; must extend the existing `edge_report.py` additively, never fork.
- Journey J-05 (/structure decluttered — the map is the default, the noise is a toggle) still failing — the new case registry has no UI surface yet; `/structure` still shows only the raw ~1,801-level view.
- Journey J-06 (Cockpit confluence — bands + tape markers + a descriptive chip) still failing — overlay/chip code absent; its credentialed replay portion is also blocked.
- Non-blocking carried gap: 13 of the 801 live-scanned events (the most-recent session per symbol) get a definitive reaction label from a capped sub-horizon bar while both forward-return fields honestly read empty — flagged to be resolved (a regression test that locks the boundary) before J-05 renders these events.
- Non-blocking carried note: a full 12-symbol scan of the live store takes roughly 4.5 minutes (no caching, by design — the anti-goal forbids shortcutting the frozen levels engine) — on the hot path for J-04's edge report and J-05's case browser; a persisted/cached scan result is recommended before those ship.
- Procedural: the goal-evaluator had not yet produced iteration 2's formal verdict or journey-history update as of this summary, even though J-02's acceptance criteria were independently reproduced by review, QA, and audit.

## Next step

No `eval.md` Next-Step Recommendation exists yet for this iteration — the goal-evaluator has not logged iteration 2. The dev handoff's own Suggested Next Phase and the audit's Recommended Next Step converge on the same call: build J-03 next. With operator Alpaca credentials in place, record trade/quote windows around the top-ranked scan events this iteration's registry now provides (≥10 events across ≥5 symbols, including the pinned AAPL 2026-06-22 window), replay them through the frozen tape engine, and join the five-state timeline onto each event's drill-in. Two carried items to address alongside or before it: lock the boundary-condition contract for events whose reaction horizon is unreached (before J-05 renders them), and plan a persisted/cached scan result before J-04 and J-05 put the ~4.5-minute full-panel scan on their hot path.

## Assumptions made

none recorded

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-tradable_wall-iter-2-review.md |
| Browser QA | SKIPPED | reports/phase-goal-tradable_wall-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-2-ui-test-plan.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-2-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-tradable_wall-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-2-closure-verdict.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
