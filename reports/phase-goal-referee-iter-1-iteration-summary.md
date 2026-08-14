# Iteration Summary — goal-referee-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-14
**Iteration:** 1

## In plain words

**What you can do now:** Nothing new to click yet — the first piece of the new fact-checking system just started working quietly behind the scenes, with no button or page for it yet. Everything from before still works the same: watch the live tape update on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk.

**What changed this time:** Behind the scenes, the system gained a private way to ask itself "how much evidence do I actually have?" It now honestly counts how many chart-pattern signals it has logged (broken down by setup and by which side of the trade), how many backtested trades exist, and states plainly that it still doesn't have enough tick-by-tick market data to run real statistical tests yet. Nothing about this appears on any page yet.

**What's next:** Next, the team will turn this round's simple counts into a detailed record of every single observation — one entry per logged signal and one per backtested trade — plus a small cache to keep it fast. This still won't be visible on a screen.

## Headline

New backend endpoint reports how much Playbook and strategy evidence already exists, honestly.

## Direction

**Signal:** improving
**Why:** J-01 ("The era transition stands — reconciliation made testable") moved from failing to passing this iteration, verified independently by 15 new hand-computed tests, a live check against the real corpus, and a browser pass against the QA rig. J-10, the regression sentinel, was re-verified via a 9-step deterministic replay with no breaks and zero anti-goal violations. Eight journeys (J-02–J-09) remain unbuilt, but the dependency chain's first link is now in place and the evaluator named J-02 as the unambiguous next target.

**Trend (last 2 iters):**
- Newly passing this iter: J-01
- Newly passing in last 2 iters total: J-01
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** The new page-less backend answer at `/research/desk/referee/evidence` really works. The saved picture of it shows an honest reply: how many Playbook records and trading days exist, the count per setup and side, and the strategy side reporting zero data with a plain sentence saying the tick-data gate is 150 short and one caveat sentence naming the still-forming bar problem. I did not take the builder's word for the rest: I ran the 15 new tests myself (all pass, with counts written out by hand in the test file), re-ran 156 older protection tests (nothing broke, the Claude connector still offers 20 tools), and printed the settings fingerprint myself — still `08e471b10130e1e2`. The old product was replayed step by step in a browser and held: the live tape page reaches "Buyer Control", the Structure page loads Apple as of 22 June, and the Desk page opens its Playbook panel.

## What was done

- Product changes: apps/backend/app/main.py, apps/backend/app/research/referee_evidence.py, apps/backend/app/research/referee_routes.py, GET /research/desk/referee/evidence
- Added `app/research/referee_evidence.py`: aggregates existing Playbook, dataset, and backtest records into per-family readiness counts (records, distinct sessions, per-(setup, side) signal counts, strategy dataset/split/trade counts, an honest "tick-data gate unmet" statement, and the first-ever `basis_caveats` forming-bar disclosure).
- Added `app/research/referee_routes.py`, mounting `GET /research/desk/referee/evidence` behind a new dedicated router wired into `app/main.py`; read-only, zero writes, never 404s on an empty corpus.
- Added `tests/test_referee_evidence.py` (7 hermetic fixture tests) and `tests/test_referee_guards.py` (8 guard tests pinning `docs/playbook-detector-spec.md` §6 and `docs/research-directions.md` against silent drift) — 15 new tests, all passing.
- Verified live against the real corpus (`scripts/dev.sh`, `:8301`): the endpoint reproduces every number `docs/goal.md` records at authoring, byte-for-byte.
- Confirmed zero diff to any frozen file (`desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`, `app/config.py`) and `config_fingerprint()` unchanged at `08e471b10130e1e2`.
- Full backend suite: 2,433 passed / 8 skipped / 0 failed (era-open floor 2,418 plus this iteration's 15 new tests), independently re-run by both the reviewer and the evaluator.
- Verified 2 target journeys pass browser QA: J-01 (the new endpoint, live on the QA-rig backend) and J-10 (the kept-product regression sentinel, deterministic replay).

## What's left

- Journey J-02 (The evidence contract — two families, one observation shape) failing
- Journey J-03 (The statistics core — calibrated, seeded, oracle-proven, fail-closed) failing
- Journey J-04 (Matched nulls — comparable times, identical measurement) failing
- Journey J-05 (The registry — pre-registration with an immutable boundary) failing
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — kept-product half re-verified again this iteration; the three Referee `/desk` sections and the 22-tool MCP contract remain unmet until J-09 lands
- The new endpoint's additive `integrity_errors` key is not yet folded into the documented response-shape contract (flagged by both the developer and reviewer as a non-blocking NOTE)

## Next step

Build J-02 "The evidence contract" next, alone, at lean depth. It is the next step in the goal's own order and everything after it waits on it: turn this iteration's counts into one typed record per single observation, for both families — Playbook occurrences (grouped by trading day, newest record per day) and strategy trades (grouped by dataset) — plus the small rebuildable cache whose deletion may change speed only, never numbers. Two riders for the same file: write the two `integrity_errors` fields into the documented response shape, and have J-02 re-use the existing caveat sentence rather than writing a second one. J-10 keeps riding along as the still-must-pass check. Approve building J-02 next; no human unblock is needed.

## Assumptions made

- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires the strategy family to carry "the `basis_caveats` forming-bar disclosure verbatim", but no verbatim text for it exists in `docs/goal.md` or `docs/referee-statistical-spec.md` — only a description of what it must disclose — so there was nothing to compare the served sentence against. We chose: Accepted this iteration's first authoring as satisfying "verbatim" — the exported constant `REFEREE_FORMING_BAR_BASIS_CAVEAT`, whose served text names `levels._bars_as_of`, the `epoch <= as_of` admission, and the Card 6.4 deferral; it is now the single source of truth J-06 and J-08 must import rather than re-word. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10 "The kept product stands" is written as a continuous regression sentinel, but its own acceptance also names era-end conditions — screenshots of the three Referee `/desk` sections and "MCP = exactly 22 tools" — which are structurally unmeetable at iteration 0, and the goal text does not say whether the sentinel should be scored on its kept-product half alone or on its whole acceptance. We chose: Scored J-10 `partial`, not `passing`/`already_passing` — the whole-acceptance reading — and recorded the verified kept-product evidence in `journey-history.json` so no later iteration re-does that work. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-1-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-1/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
