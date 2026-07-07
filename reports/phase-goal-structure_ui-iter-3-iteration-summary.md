# Iteration Summary — goal-structure_ui-iter-3

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-07
**Iteration:** 3

## In plain words

**What you can do now:** On the Structure page, you can look up support-and-resistance price levels and confidence zones on a price chart for a symbol and time you choose, and see the registry of trading strategies together with a badge showing which strategy is the current reigning "champion."

**What changed this time:** The team built a new side-by-side comparison of the two trading strategies, showing trade counts, returns, win rates, and an honest "not enough data yet" label whenever a strategy hasn't traded enough to judge — with a standing reminder that every figure shown is simulated, not live money. It worked correctly in every check the team ran by hand, but one more independent, hands-on check is still pending before it's marked ready for regular use.

**What's next:** Next, the team will re-run an independent check with the app live to confirm the new comparison screen works as expected, then finalize it for everyday use.

## Headline

J-03 comparison built and functionally verified; blocked at closure pending independent browser-QA evidence

## Direction

**Signal:** holding
**Why:** J-03 (the structure_tape-vs-v1 comparison) was built this iteration and independently confirmed correct by both the developer and the auditor via live data-path checks — byte-matched aggregates, the honest keyless non-survivor outcome, and an untouched champion/ledger — but the dispatched browser-qa-agent run recorded SKIPPED (0/26) because both services were down at dispatch time. The Definition of Done's required independent populated-state screenshot evidence for J-03 still doesn't exist, so the closure gate correctly held at CLOSURE-FAIL rather than accepting self-verification in its place. J-01/J-02/J-04 remain solid with no regression, so this is a hold at the finish line on an evidence/process gap, not a functional setback.

**Trend (last 3 iters):**
- Newly passing this iter: none (iteration 3's evaluator has not yet run — blocked at the closure gate before evaluation)
- Newly passing in last 3 iters total: J-01 (iter-2), J-02 (iter-2)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 1 critical (iter-1, resolved same iteration)
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** (from iteration 2 — the evaluator has not yet run for iteration 3, which is blocked at the closure gate) "Backend diff is empty (frozen foundation intact), config_fingerprint recomputes live to 4d665603569b9dbf, /performance is unaffected (UT-12) and the nav stays 5-link (UT-14) → J-04 holds; coherence COHERENCE-PASS, scan CLEAN, no anti-goal violation. Not GOAL_ACHIEVED (J-03 still failing — the comparison surface is out of scope this iter and unbuilt); not REGRESSION/STALLED; not ESCALATE (full pipeline all-green, no fail-open, no surfaced ambiguity) → CONTINUE."

## What was done

- Built the Comparison section (J-03) on `/structure`: dataset picker, dual `v1`-vs-`structure_tape` backtest run + poll loop, side-by-side aggregates, per-class A/B/C breakdown, and the verbatim simulated-PnL register.
- Added a read-only champion badge and a founding-baseline (PnL ledger) panel beside the comparison — the champion pointer never moves and no promotion control exists.
- Implemented 6+ distinct honest states (no datasets, dataset-list unreachable, idle, queued/running, failed, cancelled, poll-unreachable) — no fabricated result anywhere.
- Added 3 new verbatim-read API helpers and matching types; zero backend edits (`apps/backend/` diff empty, `config_fingerprint` unchanged at `4d665603569b9dbf`, backend suite 1146 passed / 1 skipped).
- Fixed a copy-discipline lint flag (bare "win rate" label/testid renamed to `win_rate`).
- Developer and auditor each independently drove the live app end-to-end and confirmed byte-for-byte match against the API, the honest keyless `structure_tape` non-survivor outcome, and an unmoved champion/ledger.
- Verified 0 target journeys pass browser QA this iteration — the dispatched `browser-qa-agent` run recorded SKIPPED (0/26) because both services were unreachable at dispatch time, so J-03 still lacks its Definition-of-Done-required independent populated-state screenshot evidence.

## What's left

- Journey J-03 ("structure_tape is compared to v1 on screen, honestly") remains `failing` until an independent browser-QA re-run confirms the populated render.
- Closure blocker: re-run `browser-qa-agent` (and ideally `demo-narrator`) against the live app to capture populated-state screenshots — a completed comparison, the per-class `insufficient_sample` chips, the verbatim register, the unchanged champion, and the keyless non-survivor outcome — then re-run the closure gate.
- Not yet exercised live (code-complete): the per-side `failed`/`cancelled` states, the poll-time `comparison-poll-error` notice, and the "no datasets registered" empty state.
- `result.null_baseline` (already served by the backend) is not rendered anywhere on the Comparison section.
- No cancel control for a running comparison (explicitly out of scope this iteration).
- No history of past comparisons — reloading `/structure` always resets to the idle state, even if a comparison already ran.
- A `/datasets` library/inventory page still does not exist (out of scope; roadmap item).

## Next step

Per the closure verdict's remediation: start both services live (`bash scripts/dev.sh`, backend `:8301` / frontend `:3301`) and confirm both respond, then re-dispatch `browser-qa-agent` against the full 26-case test plan with the frontend reachable so it actually executes (rather than precondition-skipping) — at minimum the 10 P1 happy-path and 6 P1 regression cases — capturing populated-state screenshots into `reports/qa/goal-structure_ui-iter-3-evidence/` (a completed comparison, the per-class `insufficient_sample` chips, the verbatim register, the champion unchanged at `v1`/`default`, and the keyless non-survivor outcome). Re-dispatch `phase-closure-auditor` once that evidence exists to confirm CLOSURE-PASS before the goal-evaluator is asked to certify GOAL_ACHIEVED. No code change is required or recommended — both the developer and the auditor independently verified the implementation itself is correct, minimal, and honest.

## Quick verify

From `reports/phase-goal-structure_ui-iter-3-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser
2. Scroll to the bottom "Comparison" panel and read its two side-by-side boxes: "Champion (moved never by this view)" and "Founding baseline (PnL ledger)"
3. Click the dropdown that reads "Choose a dataset…" and select any dataset from the list
4. Click the "Run comparison" button
5. Wait for both cards to finish (usually well under 30 seconds — do not refresh or navigate away)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-structure_ui-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-structure_ui-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-structure_ui-iter-3-review.md |
| Browser QA | SKIPPED | reports/phase-goal-structure_ui-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-structure_ui-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-structure_ui-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-structure_ui-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-structure_ui-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-structure_ui-iter-3-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-structure_ui-iter-3-ux-regression.md |
| QA | PASS | reports/qa/goal-structure_ui-iter-3-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-structure_ui-iter-3-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-structure_ui-iter-3-closure-verdict.md |
| Journey history | — | runs/goal-session-structure_ui/state/journey-history.json |
