# Iteration Summary — goal-referee-iter-0

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-14
**Iteration:** 0

## In plain words

**What you can do now:** Just getting started — nothing for users to try yet.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team spent this round checking the whole existing app end to end — the live price chart, the Structure page's price walls, and every section of the Desk page — and confirmed with screenshots that all of it still works exactly as before.

**What's next:** Next, the team will build the first hidden piece of the new evidence-checking system: a private count of how much trading evidence already exists, before any of it becomes visible to you.

## Headline

This was the opening check of Era 6 "The Referee".

## Direction

**Signal:** holding
**Why:** This iteration recorded a real, evidence-backed baseline for a brand-new era instead of moving any journey forward — J-01 through J-09 (the new Referee machinery) are confirmed failing because none of it exists yet, and J-10 (the kept-product sentinel) is partial because its own acceptance also names the still-unbuilt Referee `/desk` sections and 22-tool MCP contract. Zero regressions and zero anti-goal violations were found, and the existing app (Cockpit, Structure, Desk) was verified intact in a live browser pass, so direction is neutral at the starting line, with J-01 next in an unambiguous 9-journey dependency chain.

**Trend (last 1 iter):**
- Newly passing this iter: none
- Newly passing in last 1 iter total: none
- Regressions in last 1 iter: none
- Anti-goal violations in last 1 iter: none
- Iters with no journey state change: 0 of last 1

**Latest evaluator reasoning:** This was a verify-only baseline with zero code written, and the checks were really run instead of assumed. The four Referee web addresses all answer "not found", every `referee_*.py` file is missing, `authorize_promotion` does not exist, and the Claude connector still offers 20 tools, not 22 — so nine journeys are honestly recorded as failing. The old product was walked in a real browser and works: the live tape page shows a converged tape state with a populated quote and feature panel, the Structure page loads Apple's real price walls including the 300.11–302.2 band, and the Desk page renders every shipped section with honest "not computed yet" copy.

## What was done

- No product change this iteration.
- Attempted all 10 Must-have journeys (J-01–J-10) against the current codebase and recorded each verdict with concrete evidence in `journey-history.json`.
- Confirmed by direct source and route inspection that every piece of J-01–J-09's Referee machinery (the evidence, statistics, matched-null, registry, and adjudication modules; the `authorize_promotion` gate; the three new Desk sections; the 22-tool MCP contract) is entirely absent — all nine journeys correctly recorded `failing`.
- Ran the full backend test suite once: 2,418 passed / 8 skipped / 0 failed, matching `docs/goal.md`'s stated era-open floor exactly; confirmed `config_fingerprint() == 08e471b10130e1e2` and the MCP tool list has exactly 20 entries.
- Verified 1 target journey (J-10, the kept-product sentinel) passes browser QA — the live Cockpit tape, Structure's AAPL price walls, and every shipped Desk section all render correctly; recorded `partial` in journey-history because J-10's own acceptance also names the still-unbuilt Referee sections and 22-tool contract.
- Ran the store-scope guard over the owner's saved data: all 11,274 protected files unchanged.
- Drafted `runs/goal-session-referee/state/blueprint.md` with the Era 6 Information Architecture and 7-row Data Contract for iteration 1+ to build into.

## What's left

- Journey J-01 (The era transition stands — reconciliation made testable) failing
- Journey J-02 (The evidence contract — two families, one observation shape) failing
- Journey J-03 (The statistics core — calibrated, seeded, oracle-proven, fail-closed) failing
- Journey J-04 (Matched nulls — comparable times, identical measurement) failing
- Journey J-05 (The registry — pre-registration with an immutable boundary) failing
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — kept-product half verified; the remaining acceptance (three Referee `/desk` sections + a 22-tool MCP contract) is blocked until J-09 lands

## Next step

Build J-01 "Era transition made testable" next, on its own, at lean depth: add the first slice of backend work that answers `GET /research/desk/referee/evidence` with an honest count of what evidence the system already holds — how many Playbook records and sessions exist per setup and side, and how many strategy datasets and trades exist — plus the written statement that the old tick-data gate is still unmet, and the two guard tests that pin the documentation to the code. Nothing else in this era can be built before that count exists, and it needs no browser work, no credentials, and no new dependency. Do not re-do the baseline checks — the kept product, the test count, and the fingerprint are already verified for this iteration.

## Assumptions made

- iter-0 · goal-evaluator — Ambiguity: Journey J-10 "The kept product stands" reads as a continuous regression sentinel, but its own acceptance also names era-end conditions (the three Referee `/desk` sections plus a 22-tool MCP contract) that are structurally unmeetable at iteration 0; the goal text does not say whether to score it on the kept-product half alone or the whole acceptance. We chose: scored it `partial` (the whole-acceptance reading), recording the verified kept-product evidence so no later iteration repeats that work — J-10 closes only once J-09 lands, and a future break of the kept product is still caught as a frozen-foundations violation. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-0.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-0-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-0-review.md |
| Browser QA | FAIL | reports/phase-goal-referee-iter-0-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-0/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
