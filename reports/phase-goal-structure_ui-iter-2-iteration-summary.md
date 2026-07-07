# Iteration Summary — goal-structure_ui-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-07
**Iteration:** 2

## In plain words

**What you can do now:** You can type in a stock ticker to watch live trade-by-trade tape reading, write trading ideas into a journal, run replay studies, and check an honest profit-and-loss scorecard. On the Structure tab, picking a stock and a point in time draws its key price levels on a chart, grouped into zones graded by strength, and you can now also see the two trading approaches the system knows about side by side, plus which one currently holds the "champion" title.

**What changed this time:** The Structure page gained a new Strategy Registry: two cards showing the original trading approach and a newer, zone-aware one side by side, including how the newer one scales its risk and reward by level strength, plus a "Champion" badge confirming which approach is favored today (still the original) and that this matches what the Performance page already shows. If the backend can't be reached, this new section now says so plainly instead of showing nothing. Also confirmed this round: the price-chart blank-screen issue flagged last time was independently re-tested from scratch, and the fix holds for good.

**What's next:** Next, the plan is to add a side-by-side comparison on the same screen showing how the newer trading approach would have performed against the original one, using real historical data.

## Headline

Strategy registry & champion badge ship on /structure; J-01 closed to passing after re-verify

## Direction

**Signal:** improving
**Why:** J-01 closed from `partial` to `passing` this iteration — browser-QA independently re-verified the `StructureChart.tsx` z-index fix live via `getComputedStyle` (UT-06), and phase-closure returned CLOSURE-PASS, resolving iteration 1's CLOSURE-FAIL. J-02 (strategy registry + champion badge) moved from `failing` to `passing`, verified byte-for-byte against `GET /research/strategies` and `GET /research/profiles`. J-04 held green with zero anti-goal violations or regressions, and only J-03 (the on-screen `structure_tape`-vs-`v1` comparison) remains before all four Must-have journeys are green.

**Trend (last 3 iters):**
- Newly passing this iter: J-01, J-02
- Newly passing in last 3 iters total: J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 critical (iter-1, "Honest UI states only" — resolved and independently re-verified in iter-2)
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** Two journeys advanced with independent browser evidence: J-01 closed from `partial` to `passing` (the levels-but-zero-candles honest hint now renders legibly, getComputedStyle-confirmed above the chart canvases, and phase-closure is CLOSURE-PASS — resolving the exact three-record contradiction that produced iter-1's CLOSURE-FAIL), and J-02 built from `failing` to `passing` (both strategy cards + the v1/default champion badge render verbatim from `GET /research/strategies`, cross-checked byte-for-byte against `/research/profiles`, with an honest registry-unavailable state). The frozen foundation holds (empty `apps/backend/` diff, live `config_fingerprint` = `4d665603569b9dbf`, `/performance` unaffected, 5-link nav intact), coherence is COHERENCE-PASS, and the scan is CLEAN with zero anti-goal violations. Only J-03 (the on-screen `structure_tape`-vs-`v1` comparison) remains — explicitly out of scope this iteration and still unbuilt — so this is not yet GOAL_ACHIEVED.

## What was done

- Built the Registry section (J-02) on `/structure`: two strategy cards (`v1`, `structure_tape`) showing entry/exit rules and `structure_tape`'s three class-scaled tables (stop/reward/size by class), read verbatim from `GET /research/strategies`
- Added a champion badge (`v1`/`default`) with a live cross-check caption confirming it matches `GET /research/profiles`'s champion byte-for-byte — single source of truth made visible in the browser for the first time
- Added an honest "registry unavailable" state for when the backend can't be reached — no fabricated cards, no hardcoded fallback
- Zero backend changes this iteration — diff is frontend-only (`types.ts`, `api.ts`, `page.tsx`); no new endpoint, no champion mutation
- Independently re-verified J-01's prior blank-chart fix live in the browser (UT-06: computed `z-index:10` confirmed above the chart canvases), closing journey J-01 from `partial` to `passing` and resolving iteration 1's CLOSURE-FAIL
- Reconciled `ui-test-results.md` / `ux-regression.md` / `status.json` into a mutually consistent record; phase-closure verdict is CLOSURE-PASS
- Verified 2 target journeys (J-01, J-02) pass browser QA: 14 of 15 tests passed (all seven P1 tests green, including the two elevated-P1 J-01 closure/regression cases); one P3 test skipped for a documented, non-blocking tooling limitation
- Confirmed the J-04 regression sentinel green: backend suite 1146 passed/1 skipped, `config_fingerprint` pinned at `4d665603569b9dbf`, and all four prior surfaces plus the 5-link nav intact

## What's left

- Journey J-03 ("`structure_tape` is compared to `v1` on screen, honestly") failing — not yet built, targeted for iteration 3 per the goal's J-01→J-02→J-03 dependency order
- Not visible yet: the side-by-side `structure_tape`-vs-`v1` backtest comparison — no comparison or backtest-triggering UI exists anywhere in the app yet
- Three of the four champion cross-check messages ("still checking," "cross-check unavailable," "mismatch") are unreachable in normal use today — honest safety nets for a state the system can't currently produce, not a gap
- Non-blocking: `README.md`'s "Structure page" bullet still documents only J-01's levels/zones and is now stale re: the shipped Registry/champion
- Non-blocking: `/structure`'s header subtitle doesn't yet preview the new Registry section, unlike `/performance`'s subtitle precedent
- Carry-forward (non-blocking, pre-existing): `PriceChart.tsx` (Cockpit chart, serving J-04) shares the same latent z-index empty-state occlusion pattern `StructureChart.tsx` had before its iteration-1 fix — out of scope for a Structure-focused iteration

## Next step

Full depth. Build **J-03** — the last remaining journey (`structure_tape`-vs-`v1` on-screen comparison): choose a dataset via `GET /research/datasets`, run both strategies via `POST /research/backtests` at `profile=default` (reuse the Studies job/poll pattern), poll `GET /research/backtests/{id}` to `done`, then render side-by-side aggregates (n, net R, net $, `win_rate`, `max_drawdown_r`) plus the per-class A/B/C `aggregates_by_class` breakdown with `insufficient_sample` verbatim, beside the champion pointer and the founding baseline row from `/research/pnl/ledger`. This is the highest-risk journey (simulated PnL → the "simulated — not indicative of live results" register must appear verbatim; insufficient-sample labeling; champion-moved-never + no-promotion rails), so the full pipeline's audit + coherence + ux-regression + closure lanes are warranted; on the committed keyless reference dataset it must honestly show `structure_tape` as a **non-survivor** with the champion unchanged at `v1`/`default`. J-03 passing makes all four Must-have journeys green → a GOAL_ACHIEVED candidate for iter-3.

Carry two non-blocking polish items (do not gate on them, but ideally fold into the J-03 iteration since it touches `/structure`): (1) `README.md`'s "Structure page" bullet documents only J-01's levels/zones and is now stale re: the shipped Registry/champion; (2) `/structure`'s header subtitle undershoots `/performance`'s precedent by not previewing the Registry section — matters slightly more because on the keyless fixture the Registry is the only default-populated content.

## Quick verify

From `reports/phase-goal-structure_ui-iter-2-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser
2. Without clicking anything, wait about 2 seconds, then scroll down past the "Confluence zones" box
3. In the "Champion" box, read the "strategy" and "profile" values
4. Look at the two cards below the Champion box
5. Near the top of the page, type `ZZTEST` into the "Symbol" field, type `2026-06-09T21:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click "Load"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-structure_ui-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-structure_ui-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-structure_ui-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-structure_ui-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-structure_ui-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-structure_ui-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-structure_ui-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-structure_ui-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-structure_ui-iter-2-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-structure_ui-iter-2-ux-regression.md |
| QA | PASS | reports/qa/goal-structure_ui-iter-2-qa.md |
| Audit | PASS | docs/handoffs/goal-structure_ui-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-structure_ui-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-structure_ui/iter-2/eval.md |
| Journey history | — | runs/goal-session-structure_ui/state/journey-history.json |
