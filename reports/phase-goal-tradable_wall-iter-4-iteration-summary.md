# Iteration Summary — goal-tradable_wall-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 4

## In plain words

**What you can do now:** You can watch simulated buy and sell pressure in the trading cockpit, keep a trading journal, replay past trading studies, check an honest profit scorecard, and view a stock's price structure — including fetching real historical prices from Yahoo Finance with one click — on the Structure page.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team taught the product a third way to simulate trades — one that follows the same short list of important price zones the upcoming map will show, instead of the long raw list — and built an honest report comparing how well each of the three trading approaches would actually have done, broken down by zone quality, market side, and how price reacted at the touch. None of this shows up on a page yet; it is ready for a future round to display.

**What's next:** Next we'll bring the price-zone map, the example browser, and this new profit comparison onto the Structure page so people can actually see and use them.

## Headline

J-04's honest 3-way edge report (v1 vs structure_tape vs new structure_tape_map) passes its keyless core

## Direction

**Signal:** improving
**Why:** J-04's keyless core — the honest 3-way edge report comparing v1, structure_tape, and the newly registered structure_tape_map — moved failing to passing this iteration, independently re-verified by the evaluator via fingerprint recomputation, frozen-file diff-absence, and re-run gate-integrity/byte-identity tests. J-01, J-02, and J-07 all re-verified green with zero regressions and no anti-goal violations; only J-03 stays partial (its credentialed enrichment remains operator-gated) and J-05/J-06 are the next agent-buildable, browser-verifiable targets. Three of the last four build iterations (iter-1, iter-2, iter-4) have each landed a newly-passing journey, so direction reads healthy and improving.

**Trend (last 5 iters):**
- Newly passing this iter: J-04
- Newly passing in last 5 iters total: J-07, J-01, J-02, J-04
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of 5

**Latest evaluator reasoning:** "J-04 — the honest 3-way edge report (v1 vs frozen structure_tape vs the new registered structure_tape_map) — moved failing → passing on its keyless core, the passing bar the goal and the iter-4 decomposer assumption scoped. The measurement machinery is genuinely built, gate-abiding, and independently re-verified by the evaluator (fingerprint frozen, frozen files absent from the diff, load-bearing guard tests re-run green, MCP proxy byte-identical). No journey regressed, no anti-goal was violated, coherence is COHERENCE-PASS. J-03 stays partial (credentialed headline still operator-gated); J-05/J-06 remain failing (out of scope)."

## What was done

- Registered `structure_tape_map` as a new third strategy (`config.py`) beside frozen `v1`/`structure_tape`, reusing the same stop/target/position-sizing rules but arming off the tradable-band map instead of raw levels.
- Built the honest 3-way edge report (`v1` vs `structure_tape` vs `structure_tape_map`) aggregating backtests into per strategy × class × side × reaction × feed cells (n≥5 or `insufficient_sample`, train/hold-out and feeds never pooled, full PnL register, null baseline).
- Shipped the canonical `GET /research/edge-report` endpoint plus a byte-identical read-only MCP proxy.
- Verified zero behavior change to existing capabilities — full 1,338-test suite green (1331 passed / 7 skipped / 0 failed), `config_fingerprint` pinned at `4d665603569b9dbf`, champion pointer untouched.
- Cleared review (PASS), QA (PASS, 13/13 functional checks), audit (PASS, zero critical/important findings), and closure (CLOSURE-PASS); browser QA correctly SKIPPED (backend-only iteration, no on-screen change yet).

## What's left

- Journey J-05 (`/structure` decluttered — the map is the default, the noise is a toggle) failing — no on-screen change yet; all three backend values (map, case registry, edge report) are now ready to render.
- Journey J-06 (Cockpit confluence — bands + tape markers + a descriptive chip) failing — credential-gated and no on-screen change yet.
- Journey J-03 (Real tape at the wall — credentialed event-window recording) still partial — the credentialed ≥10-window headline remains operator-gated: an operator must run the recording tool directly or re-run the credentialed integration test to a clean pass with the pinned-AAPL drill-in demonstrated end-to-end.
- Blocking watch-item for J-05: resolve the boundary case where 13 of 801 recorded events carry a definitive reaction label beside a missing forward-return number, with a regression test, before rendering setups events.
- Blocking watch-item for J-05: add a bounded cache/persisted scan for the ~4m43s full-panel scan behind the case registry before the Edge Report section reads it live on every page load.
- Carried, non-blocking: once credentialed/panel-symbol recordings exist, re-verify the edge report produces populated, correctly-labeled cells under the real panel — currently only proven via a synthetic-panel test.

## Next step

Build J-05 (`/structure` decluttered — map default + raw-levels toggle, Case Studies browser, Edge Report section) at depth full. It is the dependency-order next and the first iteration to render three canonical endpoints (`/research/tradability`, `/research/setups` + `/research/setups/{id}`, `/research/edge-report`) verbatim in the browser. Full depth because it is browser-verifiable, coherence-relevant (new UI surfaces), and must resolve two blocking watch-items before it can ship honestly: (1) the boundary case where a definitive reaction label sits beside a missing forward-return number (13/801 events), with a regression test, before rendering setups events; (2) the Edge Report section render hits the ~4m43s full-panel scan on a populated store, so add a bounded cache/persisted-scan read before it loads live. Separate operator-gated carries that do not block J-05: complete J-03's credentialed headline, and once panel-symbol/credentialed recordings exist, re-verify J-04's endpoint produces populated, correctly-labeled cells under the real panel.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: J-04's acceptance ("an all-insufficient report is a valid outcome") tagged "(Keyless via the committed fixture; full run credentialed)" leaves open whether the keyless committed-fixture run must produce a POPULATED all-insufficient_sample report, or whether a vacuously-empty report (`cells: []`) on the literal fixture plus a synthetic-panel proof of the populated cell structure satisfies J-04's passing bar. We chose: the empty-is-valid reading — J-04 = passing on its keyless core, since the goal explicitly names an empty/all-insufficient_sample report a valid outcome and the populated cell structure is proven by a synthetic test. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: whether J-04 can be scored passing on the keyless committed-fixture run alone, or whether the credentialed ≥10-window recorded data (tied to J-03's still-blocked credentialed portion) is required before J-04 can pass. We chose: the keyless reading — a correct, gate-honoring, all-insufficient_sample report is J-04's passing core; the credentialed enrichment is an operator-gated carry parallel to J-03, not a blocker. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: whether J-03's "exist"/"shows" acceptance requires durable persistence in the canonical store plus the specific pinned-AAPL drill-in, or whether a demonstrated-but-ephemeral recording run is enough to score the credentialed headline met. We chose: the stricter reading — the credentialed headline is met only when the datasets persist in the canonical store and the pinned-AAPL drill-in is demonstrated end-to-end; under this bar J-03 = partial. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the iteration spec instructs recording credential-gated J-03 and J-06 as `blocked`, but the journey-history status vocabulary has no `blocked` value. We chose: `failing` for both, since there is positive evidence their features are entirely absent at baseline; the credential gate is preserved as a note field rather than the primary status. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-tradable_wall-iter-4-review.md |
| Browser QA | SKIPPED | reports/phase-goal-tradable_wall-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-4-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-4-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-4-ui-test-plan.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-4-qa.md |
| Audit | PASS | docs/handoffs/goal-tradable_wall-iter-4-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-4-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-tradable_wall/iter-4/eval.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
