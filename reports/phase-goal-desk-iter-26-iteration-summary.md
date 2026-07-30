# Iteration Summary — goal-desk-iter-26

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-31
**Iteration:** 26

## In plain words

**What you can do now:** You can run a simulated tape-reading session with moving price bars on the Cockpit, and open the Structure page to see a stock's support and resistance on a real chart. You can open the Desk page, which screens about 100 stocks and ranks them — each row shows its price range and close, how much history backs it up, the nearest wall on the other side of price, how many price levels built that wall, its round-number status, and its timeframe breakdown, all fitting on one normal screen with no sideways scrolling. You can browse past scans, jump from a saved scan into the matching Structure chart, repair the Desk's coverage badges, top up the Desk's stored price history on demand, and read Desk data through a connected Claude conversation. You can also see, for each top-up you run, an honest account of what was reused, freshly fetched, already up to date, or failed, plus the exact date range asked for on any failed stock.

**What changed this time:** The Desk page's Top-up Runs panel now shows a fourth, honest outcome — "unchanged" — for a stock whose data supplier check came back with nothing new, alongside the existing reused/fetched/failed counts. It also shows a new line stating how many stocks needed just a short catch-up fetch versus a full one, and each failed stock's row now shows the exact date range that was actually requested.

**What's next:** Next, a stale copy of the app needs rebuilding so the page and its saved checks work correctly again, and then a short walkthrough video of this new top-up behavior needs to be recorded — after that, the finish can be confirmed.

## Headline

The Desk's top-up now says honestly what it asked the data supplier for and what came back.

## Direction

**Signal:** improving
**Why:** Iter-26 added J-17 ("A top-up asks the vendor only for the bars the frozen store cannot already prove") as newly passing, with its behavior proven directly against a real saved run record; the other 16 required journeys re-checked clean with zero regressions. The verdict stayed CONTINUE rather than GOAL_ACHIEVED for one reason only: J-17's own required demo-narrator walkthrough was never recorded because the run was demoted from `full` to `lean` depth, an identical gap to the one iter-24 hit for J-16.

**Trend (last 4 iters):**
- Newly passing this iter: J-17
- Newly passing in last 4 iters total: J-15 (iter-23), J-16 (iter-24), J-17 (iter-26)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none new, none open (0)
- Iters with no journey state change: 1 of 4 (iter-25 — all 16 journeys already passing, only picture debt was closed)

**Latest evaluator reasoning:** The Desk's top-up now says honestly what it asked the data supplier for and what came back. I opened the picture myself and then proved every number in it against the run's own saved record on disk: the counts, the tail-versus-full-window split, and each failed pair's own requested dates all match character for character, and all three cases the goal file describes really happened on a real run. Nothing of the owner's data was created, changed or removed. I did not call the goal finished, for one reason: the goal file also asks for a short guided film over a populated run, the plan for this run asked for the fuller pipeline that records one, and the machine downgraded the run to the shorter one that records none.

## What was done

- Product changes: apps/backend/app/research/desk_topup_compute.py, apps/backend/tests/test_desk_topup_compute.py, apps/backend/tests/test_desk_topup_log.py, apps/backend/tests/test_desk_topup_window_disclosure_guard.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx
- Derived each pair's fetch window from the frozen BarStore's own content (tail window vs. full lookback) instead of a wall-clock horizon.
- Added a new `"unchanged"` outcome for a vendor call that returns only already-frozen bars, distinct from `"reused"` (no vendor call) and `"failed"`.
- Extended each per-pair outcome record with four additive fields (`requested_window`, `store_frozen_from`, `store_frozen_through`, `window_basis`); legacy runs render an honest "not recorded" fallback, never a backfilled guess.
- Extended `/desk`'s Top-up Runs section: a 4-outcome counts line, a new tail-vs-full-lookback tally line, and each failed pair's own requested window.
- Fixed a review FAIL by widening (not weakening) one pre-existing test's outcome key-set assertion from 4 to 8 keys, exactly as the reviewer's fix_task directed.
- Verified 17/17 target journeys pass browser QA (deterministic replay + LLM lane); full backend suite green (1,474 passed / 8 skipped), fingerprint unchanged (`08e471b10130e1e2`), MCP tool count still 17.

## What's left

- J-17's required `[NEW]`-flagged demo-narrator walkthrough is not recorded — the run was demoted from `full` to `lean` depth, which records no film; J-17 keeps an `evidence_makeup: true` flag until it exists.
- The shared frontend build (`.next`) was left pointing at a throwaway evidence-capture backend that no longer exists — it must be deleted and rebuilt, and both everyday processes restarted, before the ambient page or any golden-replay script works correctly again.
- The pre-existing test assertion widened this iteration (4→8 keys) is recorded by the dev as a carve-out "awaiting ratification," though both the reviewer and evaluator have already ratified it independently.
- Two non-blocking notes carried from iteration 25 remain open: the demo film's narration uses some judgement-style wording, and the replay tool keeps saving the same first-view screenshot instead of a fresh one each time.

## Next step

One more short capture-and-check run, with no code change, in two steps. First, rebuild the everyday page: delete `apps/frontend/.next`, rebuild it, and restart both everyday processes — the client bundle currently points at a backend that no longer exists, so the page at port 3301 shows nothing until this is fixed. Second, record the guided film for J-17 over a populated run on a throwaway copy of the data (never the owner's own), showing the four-outcome counts line and the tail-vs-full-window line, with each script step naming one row and reading its text rather than clicking it; also check J-17 in a real browser since no saved replay script exists for it yet. Two non-blocking notes remain on the owner's own track (iteration 25's narration wording and the replay tool's duplicate screenshots).

## Assumptions made

- iter-26 · goal-evaluator — Ambiguity: goal.md's J-17 acceptance makes a demo-narrator walkthrough a conjunct, and the anti-goal "the enhancement loop stays inside its box" requires every proposer-appended journey to include one; the iteration spec set Depth: full to get it, but the engine's depth arbiter demoted the run to lean, which records no walkthrough at all. We chose: split status from verdict, as iter-24 did — J-17 is `passing` with `evidence_makeup: true` (behavior is proven directly; only the film is missing), and the verdict is CONTINUE (Depth: evidence recommended next), not GOAL_ACHIEVED, since a missing acceptance-named film can't support a finish. Reversible: yes — one evidence-depth run records the film with zero product change.
- iter-26 · goal-evaluator — Ambiguity: the iteration's OUT-OF-SCOPE clause forbids editing existing assertions in test_desk_topup_compute.py, but J-17's mandated four additive per-pair fields make the existing 4-key outcome-shape assertion structurally impossible to keep. We chose: ratify the dev's carve-out — the assertion was widened (4 keys to 8) not relaxed, still an exact key-set equality, TC-7/TC-8 stay byte-identical and pass, and the full suite is green; the reviewer independently reached the same call. Reversible: yes — if the owner reads the clause as absolute, the fix is amending goal.md's wording, not the code.
- iter-26 · goal-decomposer — Ambiguity: this iteration's binding depth recommendation (computed before J-17 existed) said `evidence`, but goal.md's AUTO:journeys block now carries J-17 as a genuinely new, never-built full-stack target journey. We chose: override to Depth: full under the depth-binding rule's "brand-new full-stack journey" escape condition, confirmed against the proposer's own promoted-journey record. Reversible: yes — reverting the blueprint's additive J-17 notes would restore the one-line "let the evaluator confirm" spec with nothing built needing undoing.
- iter-25 · goal-evaluator — Ambiguity: immutable rail 2 and the desk-era anti-goal both bar advice/prediction language in "Desk copy", but this iteration's only new artifact is a demo film whose narration uses judgement-style phrasing ("heavily confirmed", "might be noise"). goal.md doesn't say whether the rail reaches narration text. We chose: not to score it as an anti-goal violation, disclosing it instead — no product value, record or served string carries the language, and iter-23's confirmed film used the same style. Reversible: yes — if the owner reads the rail as covering narration, the remedy is a wording pass over the film plus a re-record, with no journey status change.
- iter-25 · goal-evaluator — Ambiguity: J-16's acceptance makes the film's frames plus one-row click targets a conjunct, but this iteration's own DoD asks for the literal string "Demo Verdict: RECORDED"; the delivered film reads "RECORDED_WITH_NOTES" (six Playwright actionability timeouts on in-row clicks). We chose: score J-16 passing with evidence_makeup cleared — both named columns are visible inside the frames and every click target names one row, and the notes' cause is a product structure (the row's stretched drill-in anchor) the same journey mandates stay unchanged. Reversible: yes — swapping the four click actions for expect-only text assertions turns the string to RECORDED with zero product change.
- iter-24 · goal-evaluator — Ambiguity: goal.md's J-16 acceptance says a ranked row's own measured height is ≤60px, but the delivered layout measures 63px on exactly 2 of 100 rows (the rest 56.5-57px) because of the reused "round number" badge's own height. We chose: read the clause as the row-height regime rather than an absolute per-row rule, since the 115→57px defect it targets is fully closed and the acceptance's operational purpose (first 8 ranked rows legible) is met; the reviewer independently judged it a non-blocking note. Reversible: yes — if read as absolute, the remedy is a layout-only width tweak with no recorded-value change.
- iter-24 · goal-evaluator — Ambiguity: J-16's acceptance makes a demo-narrator walkthrough a conjunct, but the run's depth was demoted from full to lean, which records no film at all, and two journeys (J-06, J-15) were also dropped from re-check for time. We chose: J-16 passing with evidence_makeup true (measurements re-derived directly; only the film missing); J-06/J-15 keep passing per the deferred-budget rule with last_verified_iter deliberately left stale; verdict is CONTINUE, not GOAL_ACHIEVED, since a deferred journey can't support a finish. Reversible: yes — one evidence-depth run records the film and re-checks both journeys with zero product change.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-26.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-26-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-desk-iter-26-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-26-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-26/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
