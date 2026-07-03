# Iteration Summary — goal-tape_to_profit-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-03
**Iteration:** 6

## In plain words

**What you can do now:** Type in a stock ticker (or use a built-in demo ticker) and watch Tapeology read live trade-by-trade activity, showing moment to moment whether buyers or sellers are in control. Write trading ideas into a journal and revisit them later, and run replay studies against past market activity. The product can permanently store slices of historical market data and run a defined trading strategy against it, honestly reporting whether it would have made or lost money compared with a fair random-guessing baseline — and you can see that scorecard for yourself on the Performance page, alongside which strategy version is currently in use. Other software tools, including AI assistants, can connect directly to read all of this information.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The effort went into giving researchers a second, experimental version of the strategy's settings to test alongside the one that's actually live, without changing anything about what a person sees day to day.

**What's next:** Next, the product will learn to test experimental strategy versions automatically and adopt one as the new best choice only if it proves itself on data it's never seen — otherwise it will honestly report that none qualified yet.

## Headline

J-06 ships: candidate indicator profile registered, default profile stays byte-identical

## Direction

**Signal:** improving
**Why:** J-06 (versioned indicator profiles) moved from failing to passing this iteration — a config-owned candidate profile now sits beside a byte-identical frozen default, cross-checked by the full suite (1004 passed / 1 skipped), review (PASS_WITH_NOTES), browser QA (7/7), and coherence (PASS). All six built-so-far journeys plus the J-08 regression sentinel remain green with zero regressions and zero anti-goal violations, continuing an unbroken streak of exactly one journey landing per iteration since iter-1 — only J-07 (the sweep/promotion harness) remains before the goal is achievable.

**Trend (last 5 iters):**
- Newly passing this iter: J-06
- Newly passing in last 5 iters total: J-02 (iter-2), J-03 (iter-3), J-04 (iter-4), J-05 (iter-5), J-06 (iter-6)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-06 (versioned indicator profiles) is newly passing on cross-checked multi-surface evidence: `GET /research/profiles` lists `default` plus the additive candidate `candidate-faster-warmup`, the fixture backtests run to `done` under both profiles with the `default` fingerprint pinned unchanged at `4d665603569b9dbf` and the candidate distinct at `8c2c0fbf978228e3`, and an unknown profile returns an honest `422`. No journey regressed, no anti-goal was violated, and coherence is PASS. Seven of eight Must-have journeys now pass; only J-07 (the candidate sweep / promotion-gate harness) remains, so the goal is not yet achieved.

## What was done

- Verify-and-complete resume: found a complete, uncommitted J-06 implementation already in the working tree from an interrupted prior session and made zero code changes, independently re-verifying every DoD item from scratch (fresh full-suite run, fresh live-server curl checks, a full dev-server restart cycle)
- Registered a config-owned profile registry (`Config.profile_definition` / `profile_registry` / `resolved_for_profile`) — the frozen `default` plus one additive candidate `candidate-faster-warmup` (`warmup_min_events` 40→30)
- Replaced the backtest route's hardcoded profile refusal with registry-backed validation — a registered candidate is now accepted; an unknown profile returns an honest 422 listing the registered ids
- Applied the candidate overlay only inside each fresh per-run backtest engine (`dataclasses.replace`), never mutating the shared config singleton, keeping the default fingerprint pinned at `4d665603569b9dbf`
- Proved the candidate legitimately changes behavior on the fixture — hold-out net R flips from +0.3334 to −0.1728 under a distinct fingerprint (`8c2c0fbf978228e3`) — while the train leg and every default-profile output stay untouched
- Added 16 net-new tests (pinned equivalence, candidate-difference, fingerprint pins, source-scan guards); full backend suite now 1004 passed / 1 skipped, none deleted
- Verified 1 target journey (J-06) passes browser QA; all 6 required-still-passing journeys (J-01–J-05, J-08) also re-verified green — 7/7 in the merged UI test results

## What's left

- Journey J-07 (The candidate sweep survives hold-out or says so honestly) failing — the sweep harness `python -m app.research.pnl_scan` doesn't exist yet; it is the last remaining Must-have journey before the goal is achievable
- Minor test-completeness gap flagged by review: `test_unregistered_profile_is_422` doesn't assert that both registered profile ids are listed in the 422 detail (the behavior itself is correct, verified live) — a future regression there could slip past the test unnoticed
- J-07's promotion-gate tests must control minimum-n both ways: the committed fixture pair arms only n=1 per split (below the configured minimum of 5), so the sweep must honestly report zero survivors on the fixtures while a separate n ≥ minimum scenario is needed to prove the real promotion path

## Next step

Target J-07 (the candidate sweep harness `python -m app.research.pnl_scan --out <path>`) at full depth — the last remaining Must-have journey and the only one performing an anti-goal-gated state mutation (champion-pointer move + PnL-ledger append), gated by the critical "No train-only promotion" anti-goal. The committed fixture pair arms only n=1 per split (below the configured minimum of 5), so the fixture sweep must honestly report zero survivors and exit 0 with the champion unmoved and no ledger row appended; the J-06 candidate itself is a legitimate non-survivor (hold-out net R is negative, −0.1728 vs default's +0.3334). A distinct n ≥ minimum scenario is needed to exercise the actual survivor/promotion path, and promotion mechanics must never mutate the `default` profile or any engine default. Keep J-01–J-06 and J-08 in the required-still-passing set.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tape_to_profit-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-tape_to_profit-iter-6-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-tape_to_profit-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-tape_to_profit-iter-6-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-tape_to_profit/iter-6/eval.md |
| Journey history | — | runs/goal-session-tape_to_profit/state/journey-history.json |
