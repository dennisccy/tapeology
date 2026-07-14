# Iteration Summary — goal-tradable_wall-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 1

## In plain words

**What you can do now:** You can watch simulated buy and sell pressure in the trading cockpit, keep a trading journal, replay past trading studies, check an honest profit scorecard, and view a stock's price structure — including fetching real historical prices from Yahoo Finance with one click — on the Structure page.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team built a smarter way to boil down a stock's flood of price levels into the handful that actually matter for trading, and confirmed it works correctly against a real, well-known example — but it isn't reachable through any of the app's screens yet.

**What's next:** Next, the system will scan across a wider range of stocks to build up a library of real historical examples of price reacting at these important levels.

## Headline

The tradable level map: ~1,800 raw levels distilled into ≤10 quality-scored price bands

## Direction

**Signal:** improving
**Why:** This iteration built and verified J-01 (the tradable level map) end-to-end — a new backend module, endpoint, and MCP proxy distilling ~1,800 raw levels into ≤10 ranked bands — and the goal-evaluator independently reproduced the pinned AAPL acceptance (the 300.48–302.07 wall ranked #1, basis correctly resolved to 2026-06-18, zero regressions, `config_fingerprint` unchanged). J-02 through J-06 remain failing but are agent-buildable next (J-03/J-06 additionally credential-gated on operator Alpaca keys), and J-07's regression sentinel stayed green throughout, so direction reads as improving.

**Trend (last 2 iters):**
- Newly passing this iter: J-01
- Newly passing in last 2 iters total: J-01, J-07
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of 2

**Latest evaluator reasoning:** "J-01 (the tradable level map) is genuinely achieved and moves failing -> passing on its first build iteration. I did not rely on the three PASS reports: I independently reproduced the pinned AAPL 2026-06-22 acceptance with a direct `compute_tradability` call on the committed real fixture — 10 bands (5+5), basis 2026-06-18 (holiday 06-19 skipped by the data), the 300.48-302.07 resistance wall (round-number flagged) ranking #1 — and personally re-ran the frozen-foundation guards (equivalence 22/22, config_fingerprint frozen, levels.py byte-identical). Five feature journeys (J-02..J-06) remain failing and untargeted; coherence is PASS and no anti-goal was violated, so the loop continues to J-02."

## What was done

- Built `apps/backend/app/research/tradability.py` — the tradable level map; consumes `compute_levels` verbatim (a lens, never a second engine), with morning-markup as-of resolution, price-scale-aware band clustering, and quality scoring.
- Added `GET /research/tradability?symbol=&as_of=` and the read-only MCP `tradability` proxy; REST and MCP response bodies confirmed byte-identical.
- Added 5 config-owned constants (band cap, band width, quality weights, round-number rule), excluded from `config_fingerprint`, which stays frozen at `4d665603569b9dbf`.
- Fixed a round-1 review CRITICAL: the quality score was summing touches across all timeframes, burying the pinned 300.48–302.07 wall at rank 7 of 9; switched to daily-touch-only (per spec) and the wall now ranks #1, guarded by a new multi-timeframe regression test.
- Live-verified and evaluator-reproduced the pinned AAPL 2026-06-22 map: 10 bands (5 per side), the wall at resistance rank 0 (top-2), `round_number=true`, class inherited, basis = 2026-06-18 close.
- Full backend suite green: 1240 collected / 1234 passed / 6 skipped / 0 failed, +32 new tests this iteration; J-07 regression sentinel re-verified (equivalence 22/22, `config_fingerprint` unchanged).
- Cleared review (PASS), QA (26/26 test cases), audit (PASS_WITH_GAPS, zero blocking issues), and closure (CLOSURE-PASS); the goal-evaluator independently confirmed J-01 passing. Browser QA is correctly SKIPPED (backend-only iteration, `Frontend Present: no`).

## What's left

- Journey J-02 (The wide scan — a case-study registry across the 12-symbol panel) failing — not yet built.
- Journey J-03 (Real tape at the wall — credentialed event-window recording) failing — feature code absent AND credential-blocked (Alpaca keys not set in the operator's environment).
- Journey J-04 (The edge report — what actually profits, under the existing gates) failing — not yet built.
- Journey J-05 (/structure decluttered — the map is the default, the noise is a toggle) failing — `/structure` still shows only the raw ~1,801-level view; this is J-01's on-screen home.
- Journey J-06 (Cockpit confluence — bands + tape markers + a descriptive chip) failing — overlay/chip code absent; its credentialed replay portion is also blocked.
- Advisory, zero-acceptance-impact gap: `_PriorSessionBarView` over-excludes the prior session's own intraday bars (stays on the safe side of the no-lookahead rail); a provably-safe fix is documented and deferred to J-06.

## Next step

Build **J-02** (touch-event scanner + case registry: new `apps/backend/app/research/setups.py`, `GET /research/setups` + `/research/setups/{id}` + MCP `setups`) at depth **full**. Rationale: it is the next dependency-order unblocker (J-03 records tape at its top-ranked events, J-04 arms `structure_tape_map` on its band-touches, J-05 renders the case browser); it establishes a new canonical value + owner across the backend+MCP boundary; and its central risk is the critical no-lookahead rail (each event's morning map must derive only from data before its session) — the exact `_PriorSessionBarView` consecutive-session hazard J-01 surfaced. Carry two watch-items: (1) reaction-classification/forward-return scoring needs a realistic MULTI-TIMEFRAME fixture, not daily-only — the round-1 CRITICAL only appeared under intraday density; (2) J-04 (later) must EXTEND `edge_report.py` additively, never fork. J-03 and J-06 remain operator-Alpaca-credential-gated and honestly deferred.

## Assumptions made

- iter-0 · goal-evaluator — Ambiguity: The iteration spec instructs recording credential-gated J-03 and J-06 as `blocked`, but the journey-history status vocabulary (`passing`/`failing`/`partial`/`already_passing`/`regressed`/`unknown`) has no `blocked` value. We chose: `failing` for both — there is positive evidence their features are entirely absent at baseline, so the credential gate is preserved as a `note` field rather than the primary status. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-tradable_wall-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-tradable_wall-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-tradable_wall-iter-1-review.md |
| Browser QA | SKIPPED | reports/phase-goal-tradable_wall-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-tradable_wall-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-tradable_wall-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-tradable_wall-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-tradable_wall-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-tradable_wall-iter-1-ui-test-plan.md |
| QA | PASS | reports/qa/goal-tradable_wall-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-tradable_wall-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-tradable_wall-iter-1-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-tradable_wall/iter-1/eval.md |
| Journey history | — | runs/goal-session-tradable_wall/state/journey-history.json |
