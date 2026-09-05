# Iteration Summary — goal-observation-contract-iter-5
**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-09-05
**Iteration:** 5

## In plain words

**What you can do now:** Watch live simulated or historical tape data on the Cockpit page, look at market structure on the Structure page, and check desk screens on the Desk page — all still work exactly as before. New this round: once you are watching a ticker, you can open its own dedicated web address directly in the browser and see a complete, trustworthy report on that ticker — exactly when things happened, where the data came from, and a tamper-evident stamp proving nothing was altered. That report stays honest as you pause, resume, stop and restart watching.

**What changed this time:** The web address for a watched ticker's report — for example `/tape/SIM-BIDABS/observation`, reached after watching "SIM-BIDABS" on the Cockpit page — now actually answers with the full report instead of a "page not found" error, for the first time this chapter. No button, page or screen changed; this is a new, real answer at an already-documented address, not a new page.

**What's next:** Next, the team will add the last honesty check across the whole product and finish confirming, with a real browser, that watching live and replaying the same data give back the exact same reading.

## Headline

The observation web address now works — four journeys move to passing

## Direction

**Signal:** improving
**Why:** Iter-5 landed the observation route in `main.py`, moving J-01, J-02, J-03 and J-05 from partial (or failing) to passing in a single round — the first journeys in this session to reach `passing`. J-04 stays partial (its tests pass 6/6, but no browser evidence yet shows the served address) and J-06 remains partial and untouched this round (deferred for time). Nothing regressed and the anti-goal scan stayed clean, so this is the clearest forward jump of the session so far.

**Trend (last 5 iters):**
- Newly passing this iter: J-01, J-02, J-03, J-05
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The web address `/tape/{ticker}/observation` now works: watching SIM-BIDABS and opening that address shows the whole observation record instead of an error page. Four journeys move to passing this round — J-01, J-02, J-03 and J-05 — while J-04 was never opened in a browser this round and J-06 was skipped for time. A tooling fault, not a product fault, was also found: the automatic replay tool always opens addresses on the page server, which has no such address, so its three reported failures were correctly voided.

## What was done

- Product changes: apps/backend/app/main.py, GET /tape/{ticker}/observation
- Added the `GET /tape/{ticker}/observation` route in `main.py` — reads the watch manager's single atomic snapshot and calls no `TapeEngine` method; returns the existing 404 shape when the ticker isn't watched.
- Added `test_tape_observation_route.py` (8 new tests): an AST/source guard against direct engine calls, 404 parity with `/tape/{ticker}/state`, frozen-`now` field-for-field equality against the builder's direct output, hash recomputation, a 100-request no-side-effect call count, and MCP/REST byte parity via a real uvicorn subprocess.
- Fixed the carried-forward vacuous TC-16 counter-example in `test_tape_observation_path_equivalence.py` so it now perturbs the real `MACHINE_OBSERVATION_SEMANTIC_FIELDS` constant instead of comparing two hand-written lists.
- Rewrote the three stale golden replay scripts (`J-01.json`, `J-03.json`, `J-04.json`) that had asserted the route was still missing.
- Full backend suite green: 4044 passed / 8 skipped / 0 failed (iter-4's 4036 baseline plus 8 net-new); fingerprint unchanged at `08e471b10130e1e2`; frontend `tsc --noEmit` reports 0 errors.
- Verified 1 target journey (J-05) pass fresh browser QA this round; the evaluator additionally confirmed J-01, J-02 and J-03 passing from pre-existing screenshot evidence (see Assumptions made).

## What's left

- Journey J-04 (Ingestion-path equivalence under an identical valid event stream) partial — its test suite passes (6/6) but no browser evidence shows the served address; the only capture on file is the frontend's "page not found" screen (wrong origin).
- Journey J-06 (Guards and the regression sentinel) partial — the guard test module (`test_tape_observation_guards.py`) and the whole-product regression re-check were not run this round (iteration time budget).
- The MCP/REST byte-identity test (TC-13) could not compare full response bodies verbatim because `generated_at_utc`/`artifact_hash` legitimately differ per request; it was adjusted to compare the stable `observation_hash` plus every other field plus independently recomputed hashes instead — flagged in the dev handoff for reviewer judgment (review already passed it as a NOTE).
- The three rewritten golden replay scripts will likely still false-FAIL under the automatic deterministic replay runner, because it resolves every web address against the frontend's own server, which has no page at `/tape/{ticker}/observation` — a tooling gap, not a product defect.

## Next step

Build the last block, J-06 "Guards and the regression sentinel": the missing test file `test_tape_observation_guards.py`, then the whole-product re-check (all backend tests, the frontend compile check, the settings fingerprint, and the three pages — Cockpit, Structure, Desk — loading with nothing new on them). In the same round, close this round's two verification gaps: have the browser tester open the observation address itself for J-04 (watch SIM-BIDABS, press Pause, reload twice, and show the content identity stays the same while the generation time and record identity differ), and have the browser tester run J-02 as its own numbered steps rather than resting on a screenshot filed under J-01's name. Also fix, or document in writing, the replay tool's wrong-address problem so it stops reporting false failures. Next iteration should run at full depth — it is the final block and it carries the whole-product re-check.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: J-03 Step 2 asks that `timing.settled_at_utc` be unchanged "from step 1" across a Pause, but SIM-BIDABS keeps ticking in real time, so a literal browser comparison is inherently racy. We chose: to accept the invariant in its non-racy form — a tighter Resume→read→Pause→read canary sequence returned a byte-identical `settled_at_utc`, backed by the race-free clock-controlled test suite (29/29 passing) — so J-03 scored passing rather than being held back on a browser timing race the product cannot control. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: no browser row ran J-02's own numbered steps this round (the merged results marked it SKIP); the only real evidence is a screenshot filed under J-01's test id. We chose: to score J-02 passing anyway, because that screenshot was captured by the exact browser sequence J-02's own Step 1 prescribes and shows every one of its Acceptance values legibly — recorded so a later iteration can re-run J-02 under its own name and retire this call. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: proving the replay and live ingestion paths match required feeding a seeded sim scenario through entry points labelled `historical`/`sip` and `live`/`iex`, brushing against the era's "no pooling or equating sim, iex, sip" rule. We chose: to score the anti-goal OK — the two legs' feed labels stay distinct and excluded from the compared set, and nothing built this way is ever served or displayed, only exercised inside one test file. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: only one screenshot (the final re-watched-live state) was captured for a five-step browser sequence; the paused and post-Stop states are described in prose only. We chose: not to treat this as fabricated evidence — J-03 was already partial for a substantive reason (the route didn't exist yet) and full browser evidence would need retaking anyway once the route landed. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's literal steps read fields from a served route that doesn't exist until iteration 5, so browser QA scored a narrower "regression-smoke" scope instead of the journey's literal steps. We chose: to credit that row only for the sub-steps it actually ran and treat every JSON-field assertion as unmet, so J-03 stayed partial, never passing, on that evidence. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the era's copy-discipline/actionability guard is reserved for iteration 6, but a required trap-coverage item naming it is also listed under J-03; unclear whether J-03's own test module must duplicate that scan now. We chose: J-03's own module ships a scoped grep over one built artifact for the same fixed token list, leaving the general-purpose, lexicon-driven guard as iteration 6's own module rather than duplicating it. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the goal lists `profile_id` as a manager-owned field recorded at watch creation, but no live/replay watch path in this repo actually supports profile selection. We chose: to store `profile_id` as a constant field of the same per-ticker descriptor recorded at watch creation, keeping every descriptor field readable from one call site. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: unclear whether `get_observation_source` must return the full descriptor-bearing shape this iteration or a narrower shape iteration 3 extends. We chose: to introduce it this iteration returning only what the atomic settled pair itself carries (snapshot, `settled_at_utc`, `end_reason`), with descriptor fields added onto the same method by iteration 3 without a second read. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's Acceptance is a conjunction (served JSON plus a passing test file); the goal text doesn't say how to score a journey when the route half is blocked by the goal's own required build order. We chose: partial — the test-file half verified met, the served-route half verified unmet (404) — matching the "only some assertion steps passed" convention; partial never counts toward the goal being achieved. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the goal's required order doesn't say whether `build_tape_observation` should be a partial function this iteration or must already produce the complete v1 schema. We chose: to have it produce the complete v1 schema now, accepting already-resolved values as parameters, while the machinery that makes those values correct is left to iterations 2/3/5. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06's Acceptance is one long conjunction and the goal text doesn't say how to score a journey whose sub-checks split. We chose: partial (not failing) — the era-open documents and unchanged pages are genuinely done, only the guard-test file is missing; neither status counts toward the goal, so no gate is loosened. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06 also requires the full backend suite recorded green, but browser QA's own re-run didn't finish and honestly recorded unknown. We chose: to treat the developer's and reviewer's independent full runs plus the evaluator's own re-collection as sufficient evidence the foundation is unchanged, while still leaving J-06 partial on the missing guard module. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-observation-contract-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-observation-contract-iter-5-dev.md |
| Review | PASS | reports/reviews/goal-observation-contract-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-observation-contract-iter-5-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-observation-contract/iter-5/eval.md |
| Journey history | — | runs/goal-session-observation-contract/state/journey-history.json |
