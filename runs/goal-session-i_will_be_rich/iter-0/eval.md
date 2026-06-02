# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Verify-only greenfield baseline. No product code was written (git diff HEAD empty,
`status.json` `changed_files: []`, no `apps/`/backend/frontend tree, review PASS confirms
zero product source), and the coherence blueprint exists at the required path ready for the
human approval gate. All nine Must-have journeys are seeded as **failing / not-yet-built** —
the honest, expected baseline that targets iteration 1 at the real gap.

## Journey Results This Iteration

Browser QA recorded every journey as SKIPPED (0/9), because the frontend is not running and
no `apps/` tree exists (HTTP 000). The skip cause is provably "no product exists yet" —
corroborated by the empty git diff, the dev handoff (greenfield), and the review PASS — so
each journey is seeded as `failing` (yet-to-build), not `unknown`. This is an evidenced
not-implemented state, not an evidentiary gap.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Watch a ticker / live tape cockpit | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-02 Buyer-control identified | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-03 Seller-control identified | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-04 Bid absorption (price impact) | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-05 Ask absorption (price impact) | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-06 Unclear / choppy reported as unclear | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-07 Transitions announced in event log/observations | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-08 REST and UI agree (single source of truth) | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |
| J-09 Stop watching a ticker | none (first seen) | failing (not built) | reports/qa/goal-i_will_be_rich-iter-0-evidence/precondition-check.txt |

## Anti-goal Check

No code was written this iteration (git diff HEAD empty; `changed_files: []`), so no
anti-goal could be introduced. Verified against the diff and the review report.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path (no broker/order integration) *(critical)* | OK | No code; nothing to violate |
| Stay in scope (no scanner/news/charting/fundamentals/portfolio) *(critical)* | OK | No code |
| Price impact over raw aggression (absorption ≠ control) *(critical)* | OK | No classifier yet; blueprint codifies the rule for iter 1 |
| Honest uncertainty (weak/mixed ⇒ unclear) *(critical)* | OK | No code; blueprint preserves it |
| No fabricated data (explicit stale/no-data on gap) *(critical)* | OK | No code; blueprint mandates stale/no-data state |
| Single source of truth (compute once, read everywhere) *(critical)* | OK | No code; blueprint's Data Contract maps one producer per value |
| No magic numbers (all thresholds from config) | OK | No code; blueprint requires a single config module |
| Provider-agnostic engine | OK | No code; blueprint depends only on the provider interface |
| Deterministic & reproducible (per-scenario tests) | OK | No code; required for iter 1 |
| No ML in v1 | OK | No code |
| No trade/profit claims | OK | No code/UI |
| No secrets in source | OK | No code; nothing committed |

**Coherence:** No `coherence.md` was produced this iteration — correct, since there is no
diff to audit on a no-code baseline. This is **not** a COHERENCE-FAIL, so there is no
structural veto. The DRAFT blueprint (`runs/goal-session-i_will_be_rich/state/blueprint.md`)
is well-formed: a single `/` cockpit home and a Data Contract assigning each canonical value
exactly one computing module and one serving endpoint — the singularity contract the
coherence-auditor will enforce from iter 1 on.

## Next-Step Recommendation

Continue to iteration 1 (after the human blueprint-approval pause that `run-goal.sh` enforces
post-baseline). Iteration 1 should stand up the foundation, conforming to the approved
blueprint, sequenced so **J-01** becomes verifiable first:

1. Provider interface + deterministic, seedable `SimulatedProvider` with the five reserved
   sim tickers (`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`).
2. `FeatureEngine` (rolling 10/30/60/180/300s windows) + aggressor classifier, with all
   thresholds in one config module (no magic numbers).
3. Rule-based `TapeStateClassifier` keyed on **price impact, not raw aggression** — the
   defining anti-goal; bid/ask absorption must resolve away from control. One automated test
   per scenario asserting the expected state at reasonable confidence (determinism).
4. REST + WS API (`POST`/`DELETE /watch/{ticker}`, `/state`, `/features`, `/events`,
   `/summary`, `WS /stream`) re-exposing a single engine snapshot read-only.
5. The `/` Next.js tape-cockpit UI reading those values — unblocking J-01, then J-02/J-03/J-06
   (control + unclear), J-04/J-05 (absorption), J-07 (event log/observations), J-08 (single
   source of truth), J-09 (stop/idle).

**Depth: full.** Iteration 1 is the highest-stakes foundational build of the session — it
establishes the single-source-of-truth data contract, the price-impact classifier, and
determinism, all of which are critical anti-goals. It warrants the full pipeline (QA, audit,
coherence audit, ux-regression, closure), not lean.

## Halt Justification (if halting)

N/A — not halting. CONTINUE. No journey was previously passing (no regression possible), no
critical anti-goal was violated, and there is a clear, tractable next step (the foundational
build above), so neither REGRESSION nor STALLED applies; GOAL_ACHIEVED is impossible with
0/9 journeys passing.
