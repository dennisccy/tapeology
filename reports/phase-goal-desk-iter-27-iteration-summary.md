# Iteration Summary — goal-desk-iter-27

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-31
**Iteration:** 27

## In plain words

**What you can do now:** On the Desk page you can browse a screened list of about 100 stocks ranked by their nearest price wall, with each row showing how much history backs it up, its price range and close, the nearest wall on the other side, how many price levels built the wall, its round-number flag, and its timeframe split — all fitting on one screen with no side-scrolling. You can hover a row for more detail, browse past scans, jump from a scan into the matching chart, repair coverage gaps, top up stored price history on demand (and see honestly what each stock's top-up actually asked for and got back), and read Desk data through a connected Claude conversation.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team rebuilt the Desk page's compiled files so it talks to the right server again (the last round had left it pointed at a server that no longer existed), re-checked all 16 existing screens still work, and re-proved the new top-up disclosure feature with a real test run. They also tried to record a short walkthrough video of that new top-up feature, but the recording captured the wrong screen by mistake and shows nothing useful — it needs to be redone.

**What's next:** One more quick attempt to record that walkthrough video, aimed at the right screen this time — if it works, the whole project can be proposed as finished again; if it doesn't, the team will treat the video as optional polish and propose finishing anyway.

## Headline

Evidence-only iteration: no code changes were planned or made.

## Direction

**Signal:** holding
**Why:** All 17 journeys remain `passing` with no new failures, regressions, or anti-goal violations this iteration — the frontend rebuild and 16/16 golden-script replay succeeded, and J-17's top-up behavior was re-proven on a fresh throwaway rig. The only open item is J-17's demo-narrator walkthrough, which failed to capture real content for the second iteration running (iter-26, iter-27), so the evaluator declined to call the goal achieved even though nothing regressed.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-16, J-17
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 2 of last 4 (iter-25, iter-27)

**Latest evaluator reasoning:** "This run changed no program code at all, and I checked that myself: the difference against the run's own starting point is empty under apps/, scripts/ and config/, with no new files there, and the program tree is byte-identical to the tree that was saved at the end of the last run. The run had three jobs. Two of them landed and I proved both by opening the files rather than reading about them: the page bundle was rebuilt so the everyday page at port 3301 talks to the running program again, after which all sixteen saved test scripts replayed green with no script edits; and the new top-up disclosure was photographed afresh on a throwaway copy of the data, in one picture that shows the four counts, the tail-versus-full-window line and four failed rows each naming the window it asked for. The third job failed."

## What was done

- Product changes: No product change this iteration.
- Rebuilt `apps/frontend/.next` against `NEXT_PUBLIC_API_URL=http://localhost:8301` and restarted the ambient `:3301`/`:8301` pair, closing iteration 26's stale-build risk (rebuilt chunks now carry `localhost:8301`, not `localhost:8000`).
- Replayed all 16 existing golden journey scripts (J-01..J-16) against the rebuilt pair — 16/16 PASS with zero script edits.
- Re-proved J-17 (top-up window disclosure) on a fresh throwaway rig with a real keyless Yahoo top-up run; captured `J-17-topup-window-disclosure.png` showing `0 reused · 6 fetched · 2 unchanged · 4 failed` and the tail-vs-full-lookback line, matching iteration 26's numbers exactly.
- Re-ran the targeted test set (136 passed, exit 0), re-confirmed the config fingerprint (`08e471b10130e1e2`) and the 17-tool MCP count, and proved nothing was written to the operator's own data store (only rebuildable index sidecars touched).
- Attempted the J-17 demo-narrator walkthrough, but it failed: all five recorded frames are one byte-identical top-of-page image of the ambient `/desk` page — the film was aimed at the wrong (already torn-down) rig.
- Verified 17 target journeys pass browser QA (16 via deterministic golden replay, 1 via a fresh real-browser pass on a throwaway rig).

## What's left

- J-17 "A top-up asks the vendor only for the bars the frozen store cannot already prove" — behavior is fully proven, but its required demo-narrator walkthrough has now failed twice in a row (iter-26, iter-27) to show any of the required content; it still carries an `evidence_makeup` flag.
- One more capture-only attempt is planned, aimed at the throwaway rig instead of the ambient page; the evaluator has bounded this as the last such attempt — if it fails again, the film becomes optional showcase polish and the finish will be proposed on existing evidence instead.
- Non-blocking housekeeping carried from earlier iterations: the replay tool keeps saving the same first-view screenshot (16 replay images collapse to 3 distinct ones); the backend suite reads two files from the run-bookkeeping folder, so archiving that folder would break the suite; J-16's film narration wording and verdict string could use an optional polish pass.

## Next step

One more short capture-only run, no code change, with exactly one job: record J-17's guided film so its own frames actually show the top-up disclosure. The fix is small and now precisely known — the film must be pointed at the throwaway copy where the populated run lives, not at the everyday page. The plan must say two things: keep the throwaway rig alive until the film step has finished (this run killed it one minute too early), and set the film's `base_url` to that rig's own address rather than `http://localhost:3301`. The frames must show the four counts line, the tail-versus-full-window line and at least one failed row's own requested window, and each step must name one row rather than all of them; do not script a click inside a briefing row, because an invisible full-row link makes that impossible by design. The evaluator has bounded this deliberately: this is the last capture run it will ask for on this film — if the next attempt still cannot put that content in frame, the right call is to stop retrying, hand the film to the owner as optional showcase polish, and propose the finish on the evidence that already exists, since nothing about the Desk's behaviour itself is unproven. Two further things carried from earlier runs, neither blocking: the replay tool keeps saving the same first view, so sixteen replay pictures are only three distinct images; and the backend test suite reads two files out of the run bookkeeping folder (`runs/goal-session-desk/journey-scripts/`), so archiving that folder would break the suite.

## Assumptions made

- iter-27 · goal-evaluator — Ambiguity: goal.md makes J-17's demo-narrator walkthrough a conjunct of acceptance, but it is genuinely unclear whether the anti-goal rail ("the enhancement loop stays inside its box") is satisfied by the proposer authoring the walkthrough clause (done) or only by the chain actually delivering the film (not done) — a literal top-down read of the verdict tree would otherwise yield GOAL_ACHIEVED. We chose: keep iter-24/iter-26's reading and return CONTINUE — J-17 stays `passing` with `evidence_makeup: true` (behavior is proven; only the film is missing), and no confirmed session precedent covers closing on a film that shows none of the target journey (all five frames are one byte-identical image). Reversible: yes — if the owner reads the walkthrough as optional showcase polish, the finish can be confirmed directly on this iteration's evidence with zero further work.
- iter-26 · goal-evaluator — Ambiguity: the same split as iter-24 — J-17's acceptance makes a demo-narrator walkthrough a conjunct, but no film was recorded because the engine's depth arbiter demoted this run from `full` to `lean`, and the agent contract says a missing-recording gap must never block or become an iteration's goal. We chose: J-17 is `passing` with `evidence_makeup: true` (behavior proven by artifacts opened directly); verdict is CONTINUE at `Depth: evidence`, not GOAL_ACHIEVED, since a finish can't be asserted while an acceptance-named film has never been recorded. Reversible: yes — one evidence-depth run records the film with zero product change; if the owner reads the film as optional, the finish can be confirmed directly on this iteration's evidence instead.
- iter-26 · goal-evaluator — Ambiguity: the iteration spec forbids editing any existing assertion in `test_desk_topup_compute.py`, but J-17's mandated four additive fields make one exact key-set test (pinning the old 4-key shape) impossible to keep green unmodified, and the goal's one named escape doesn't clearly cover it. We chose: ratify the developer's carve-out — the one-line edit widened the key-set from 4 to 8 keys (never relaxed), the two byte-identical tests the spec names by name still pass, and the full backend suite is green with the edit and could not be green without it. Reversible: yes — if the owner reads the out-of-scope clause as absolute, the remedy is amending goal.md's J-17 wording, not the code.
- iter-26 · goal-decomposer — Ambiguity: the binding depth recommendation for this iteration was `evidence` (computed before J-17 was promoted), but the goal-proposer had just added J-17 as a genuinely new, never-built target journey needing both backend and frontend code plus a first walkthrough. We chose: override to `Depth: full`, citing the depth-binding rule's escape for a brand-new full-stack journey — confirmed directly via the goal.md diff, the proposer's own promotion record, and the fact that an `evidence`-depth run can't deliver code or a first walkthrough. Reversible: yes — if the owner prefers to close the session at 16 journeys first, revert this iteration's purely-additive blueprint edits; nothing built yet would need undoing.
- iter-25 · goal-evaluator — Ambiguity: the desk-era anti-goal and copy-discipline rail are worded around DESK COPY, but this iteration's only new artifact is a demo film whose spoken narration uses judgement language ("heavily confirmed", "might be noise") that the product itself is never allowed to use; goal.md doesn't say whether the rail reaches narration text. We chose: not to score it as an anti-goal violation — the enforcement mechanism goal.md names is the frontend-literal copy lint, which is green and unmodified over a zero frontend diff, and an earlier confirmed finish carried the same narration style. Reversible: yes — if the owner reads the rail as covering narration, the remedy is a wording pass over the film's narration strings plus a re-record; no journey status would move.
- iter-25 · goal-evaluator — Ambiguity: this iteration's own spec asks for the literal string "Demo Verdict: RECORDED", but the delivered J-16 film reads "RECORDED_WITH_NOTES" (six soft notes, all Playwright timeouts on in-row cell clicks); goal.md doesn't say whether the verdict string itself is part of the acceptance conjunct. We chose: read the clause by its own words (frames plus one-row click targets) and score J-16 `passing` with `evidence_makeup` cleared — both named columns are visible inside the film's own frames, every click target names exactly one row, and the notes stem from a product structure (the row's own stretched drill-in anchor) the journey itself mandates stay unchanged. Reversible: yes — swapping the four click actions for expect-only text assertions and re-recording would turn the string into "RECORDED" with zero product change.
- iter-24 · goal-evaluator — Ambiguity: J-16's acceptance makes a demo-narrator walkthrough a conjunct, but no film was recorded because the engine's depth arbiter demoted `Depth: full` to `lean` (which records no walkthrough), and separately a wall-clock trim marked two journeys (J-06, J-15) as not re-tested this run; the agent contract says an evidence/recording gap must never block, while goal.md makes the film part of acceptance. We chose: split the two questions — J-16 is `passing` with `evidence_makeup: true` (the asserted behaviour is proven by artifacts and measurements re-derived directly; only the film is missing), J-06/J-15 keep `passing` per a deferred-budget rule with their verified-iter left visibly stale, and the overall verdict is CONTINUE, not GOAL_ACHIEVED, since a deferred journey can never support the achievement gate. Reversible: yes — one evidence-depth run records the film and re-checks the two deferred journeys with zero product change.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-27.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-27-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-27-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-27-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-27/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
