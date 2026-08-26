# Iteration 0 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This was a baseline check with no code changes, and it did what a baseline should: it showed
exactly where we start. One journey is part-done and seven are not started at all. The
paperwork that opens this new era is already in place, but nothing of the Foundry itself has
been built yet. One important problem also appeared: the safety guard that protects the
operator's real data folder correctly refused to run the browser checks, because the test
backend could not be started. That means no screenshots exist for any journey this run, and it
must be repaired before any journey can ever be marked as passing.

## Journey Results This Iteration

No prior status exists for any journey — this is the first evaluation of this session
(`journey-history.pre.json` = `{"journeys":{}}`). No screenshot exists for any row: the browser
lane never ran (see Browser Evidence below). Every status below rests on deterministic
repository evidence the evaluator reproduced itself.

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Foundry era opens / old proposer inactive | (none) | partial | steps 2-4 hold: `docs/goal-archive/goal-2026-08-26.md` (75 KB), dated opening note `docs/research-directions.md:1126`, `runs/goal-session-rapid-microscope/` 527 tracked files clean + nothing touched since 19:00, `project-extensions/proposer-guidance.md` absent (archived at `docs/goal-archive/proposer-guidance-2026-08-26.md`) so the two-file opt-in is broken. Steps 1 + 5 impossible: no "Hypothesis Foundry" string in `apps/frontend/app/desk/page.tsx`, no read model to record the era-open baseline into |
| J-02 Sources compile to CandidateSpec or typed block | (none) | failing | `ls docs/hypothesis-foundry` → No such file or directory |
| J-03 Generic interpretation / exact Scout reuse | (none) | failing | `find apps/backend -name 'foundry*'` → zero hits |
| J-04 Denominator / freeze barrier / integrity lock | (none) | failing | no `freeze-set.json` / `freeze-record.json` (parent dir absent) |
| J-05 Hermetic oracle suite | (none) | failing | `find apps/backend/tests -iname '*foundry*'` → zero hits |
| J-06 Real epoch generated + committed | (none) | failing | no tracked `docs/hypothesis-foundry/` artifacts, no freeze commit; correctly not attempted (Binding Execution Order steps 2-5 first) |
| J-07 Deterministic exhaust of the frozen epoch | (none) | failing | `grep -ril foundry apps/backend/app/` → zero hits; no runner, no trial ledger; real reads illegal before the J-06 freeze commit |
| J-08 Final Foundry truth + foundation rails | (none) | failing | `GET /research/desk/micro/foundry` absent (no foundry route in `apps/backend/app/research/micro_routes.py`), no `/desk` panel. Foundation half healthy: 3747 passed / 8 skipped / 0 failed, `tsc --noEmit` 0 errors, `config_fingerprint 08e471b10130e1e2` |

`spec_hash` recorded for all eight from `goal_gate.py hash-journeys docs/goal.md`.

### Browser evidence — none produced this iteration

`reports/phase-goal-hypothesis-foundry-iter-0-ui-test-results.md` is a SKIPPED stub; its
`**Reason:**` line does NOT name maintenance isolation, and
`reports/qa/goal-hypothesis-foundry-iter-0-evidence/` is empty.
`runs/goal-session-hypothesis-foundry/iter-0/browser-infra.json` lists all 8 journeys
(`reason: store-scope`, `attempts: 1`). Root cause, from `engine.log:186-219`: the backend on
:8301 was the operator's REAL store (universe snapshot `source_url=…wikipedia…S%26P_100`), so
the guard tried to stand up a scoped fixture rig; the rig's seed step crashed —
`apps/backend/scripts/seed_micro_graduation_iter18_fixture.py:175` →
`walkforward.require_canonical_observation_units` → `UnitMismatchError: effect magnitude
declares unit None`, because `_observation()` at line 103-104 builds
`{"session_date", "symbol", "value"}` with no `value_unit`. The rig never became healthy, the
guard refused both lanes, and `store-scope-guard.md` confirms all 11395 protected files were
left untouched — the rail worked exactly as designed.

**Scoring note (deliberate departure from the REL-14 default).** `pending_infra` was NOT set on
any journey. The REL-14 carve-out forbids `failing` on *infra absence alone*; here each status
rests on independent deterministic evidence the evaluator reproduced (the greps above), and a
verify-only make-up ride over surfaces that do not exist would waste an iteration and would push
`attempts` to 2, triggering a STALLED-class treatment for a blocker that is a one-line in-repo
fixture fix. The infra blocker is instead carried as the top active blocker. Recorded in
`assumptions.md`.

## Anti-goal Check

Product diff this iteration is EMPTY (`iter-diff.md`: "(no changes)"); `scan-report.md`: CLEAN.
Disposition counts (`anti_goal_disposition.py summary`): total=0, resolved=0,
unresolved_blocking=0, unresolved_non_blocking=0, unresolved_critical=0.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | `scan-report.md` CLEAN; no new config/env file in the diff (diff is empty). Sole tracked-file modification in the tree is `project-extensions/host-guard/host-guard.env` — read in full, contains a memory limit and a comment, no credential |
| Paid/external SaaS | OK | no manifest touched — `pyproject.toml`/`package.json` unchanged (empty diff) |
| License changes | OK | no LICENSE or license-field change (empty diff); scan CLEAN |
| Fabricated/substituted data | OK | no code changes; store-scope guard verified 11395 files across 12 protected `.data` paths byte-size + mtime unchanged (`reports/qa/goal-hypothesis-foundry-iter-0-store-scope-guard.md`) |
| Rails 1-10 (execution path, profit claims, frozen foundations, gated promotion, lookahead, single source of truth, seeded determinism, read-only MCP, immutable data, scoped persistence) | OK | no product code was added or changed, so none can be violated by construction; `config_fingerprint` re-measured at the pinned `08e471b10130e1e2` |
| Referee / Rapid-Microscope rails | OK | `runs/goal-session-rapid-microscope/` — 527 tracked files, `git status` clean, nothing modified since before the session opened; no evidence-class or Referee file touched |
| Foundry-specific (no candidate/manifest/epoch acts) | OK | zero Foundry code or artifacts exist yet, so no compile, freeze, outcome read, or epoch occurred — the Binding Execution Order barrier is trivially intact |
| No active post-`GOAL_ACHIEVED` science proposer | OK | two-file opt-in broken: `project-extensions/hooks/post-goal.sh` present, `project-extensions/proposer-guidance.md` absent (archived, not rewritten) |
| No workaround that edits/deletes/xfails a scientific guard | OK | the opposite happened — the store-scope guard was obeyed at the cost of the whole browser lane. Flagged forward: the iteration-1 rig repair must fix the *fixture*, never relax `require_canonical_observation_units` |
| No weakening/bypass of `host-guard.env` | OK (noted) | the only tracked modification narrows `HOST_GUARD_MEMORY_HIGH` 10G → 6G — a tightening, dated and owner-authorized in-file, and present in the snapshot commit before this iteration was dispatched (the session correctly paused `AWAITING_HOST_GUARD` first). Reviewer logged the same as a NOTE |

No coherence audit was produced this iteration (`coherence.md` absent — expected for a
zero-diff lean baseline). It is not `COHERENCE-FAIL`, so nothing is vetoed; it is also not a
clean pass, which matters only when GOAL_ACHIEVED is in reach.

## Next-Step Recommendation

Iteration 1 should do two things, in this order.

First, repair the test backend so future work can be checked in a browser. The fixture seeding
script `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` fails because each of its
30 practice measurements does not say what unit it is in. The fix is to make the fixture declare
the unit it already uses (`return_bps`) in its `_observation()` helper at line 103 — after
confirming those values really are in basis points. Do NOT loosen the safety check in
`walkforward.py` that caught this; that check is doing its job. Then confirm the scoped test
backend actually comes up healthy on port 8301 inside its time budget, because until it does, no
journey can ever be marked as passing (a journey needs a screenshot, and no screenshot can be
taken).

Second, start the real work at step 2 of the goal's Binding Execution Order: write the
methodology document `docs/hypothesis-foundry-spec.md` and the CandidateSpec schema, plus the
first source records. This is what J-02 "Sources compile into auditable CandidateSpecs or typed
blocks" needs. Do not touch real epoch generation, freezing, or any candidate result yet —
those are steps 6-8 and are illegal until the machinery exists and is proven on hermetic
fixtures.

One thing for the human operator to decide: the session is currently capped at 60 iterations
(`runs/goal-session-hypothesis-foundry/session.json`), while the goal document recommends
starting this era with 80. Raising it now avoids an early stop that would not mean anything
scientific.

## Halt Justification (if halting)

Not halting. Not STALLED: the one blocker (the broken test backend) is a small code fix inside
this repository that an agent can make — no credentials, network access, paid service, or
irreversible act is needed, and the browser-infra token is only at `attempts: 1`. Not
REGRESSION: no journey had a prior passing status to lose, and no critical anti-goal violation
exists (product diff empty, scan CLEAN). Not ESCALATE: the review lane passed (it did not fail
open), nothing ambiguous surfaced, and running the expensive full pipeline next would hit the
same store-scope refusal without fixing it.
