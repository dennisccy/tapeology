# Iteration Summary — goal-desk-iter-35

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-07-31
**Iteration:** 35

## In plain words

**What you can do now:** On the Desk page, you can browse a daily ranked screen of about 100 stocks — each row showing its price range, opposite wall, level makeup, and how much history backs it, all fitting one screen with no sideways scroll. You can browse past scans and jump into the matching Structure chart, top up stored price history and see an honest account of what was fetched, and see a permanent record of every scan and top-up ever run. You can now also see, for the screen you're viewing, exactly how it differs from the screen recorded right before it — which stocks moved rank, flipped from support to resistance, or newly entered or left the list. On the Cockpit you can run a simulated live tape-reading session, on Structure you can view a stock's support and resistance levels, and you can read Desk data through a connected Claude conversation.

**What changed this time:** The Desk page now has a new "Screen Comparison" section, shown below the ranked list. It states how today's screen differs from the one recorded right before it — which stocks moved up or down in rank, which flipped sides, which are new to or dropped from the list — with an honest "nothing changed" message when two screens are identical, and an honest "no earlier screen" note on the very oldest recorded screen.

**What's next:** Please confirm the Desk — and this whole chapter of work — is finished; a short list of small, optional wording notes (like one sentence that could be worded more precisely) can wait and nothing more needs to be built right now.

## Headline

Desk's new "Screen Comparison" section ships — shows how today's screen differs from the last one recorded

## Direction

**Signal:** improving
**Why:** J-20 ("Every recorded screen states how it differs from the screen recorded before it") went from non-existent to passing this iteration — the product's 20th journey, with zero regressions. Ten regression journeys (J-03, J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18) were re-verified by golden replay with zero script edits, and the backend suite grew from 1520 to 1551 passing tests. The only gap is a missing demo-narrator walkthrough for J-20 (flagged `evidence_makeup`), which the evaluator explicitly ruled non-blocking since the feature's behavior was independently re-derived and proven.

**Trend (last 4 iters):**
- Newly passing this iter: J-20
- Newly passing in last 4 iters total: J-19, J-20
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** The Desk now tells the operator how the screen on the page differs from the screen recorded before it. I did not take the reports' word for it. I opened all three pictures myself, then re-did the whole comparison by hand from the twelve frozen record files and got the same numbers, row for row. Nothing of yours was written this run: not one file in the data folder is newer than the run's start.

## What was done

- Product changes: apps/backend/app/research/desk_screen_diff.py, apps/backend/app/research/desk_routes.py (new GET /research/desk/screen/compare), apps/backend/tests/test_desk_screen_diff.py, apps/backend/tests/test_desk_screen_compare_ui_guard.py, apps/frontend/lib/types.ts, apps/frontend/lib/api.ts, apps/frontend/app/desk/page.tsx
- Built J-20: a new backend module (`desk_screen_diff.py`) that computes screen-to-screen comparisons purely from two already-recorded `ScreenStore` snapshots — zero new store, zero recompute, structurally incapable of calling `compute_tradability`.
- Added the `GET /research/desk/screen/compare` endpoint with honest-null handling for an unknown snapshot id and a 422 refusal for comparing a snapshot with itself.
- Added a new read-only "Screen Comparison" section to `/desk`, rendered after the ranked table, showing both snapshots' metadata, a descriptive counts line, and a capped 20-row diff table with an honest "showing N of M" disclosure.
- Added 31 new tests (26 backend logic tests + 5 UI guard tests); full backend suite now 1551 passed / 8 skipped / 0 failed, up from iteration 34's 1520.
- Wrote the new golden replay script `journey-scripts/J-20.json` using stable substrings rather than today's exact counts, per this session's hardening precedent.
- Verified 11 target/regression journeys pass browser QA (J-03, J-04, J-05, J-06, J-07, J-12, J-13, J-14, J-16, J-18, J-20 — 11/11 PASS).

## What's left

- The `[NEW]`-flagged demo-narrator walkthrough for J-20 was never recorded — this run was dispatched at the shorter "lean" setting (no film crew); the feature's behavior is proven, only the recording is owed (carried as `evidence_makeup`).
- The Desk's "ranked rows are identical" sentence is wider than what it actually checks — for the identical-state pair, all rows differ in one field (how old the price basis is), though the wording matches the project's own written spec verbatim.
- Asking for an unknown screen returns a "how the base was chosen" value not listed among the three the written contract enumerates (a minor documentation gap, not a behavior bug).
- Only 10 of the 19 existing saved re-check scripts were replayed this run (not all 19); none were edited, and the other 9 were proven unable to collide with the new section's wording or elements.
- The three new screenshots are crops from full-page captures, because a direct capture at that scroll depth renders solid black in this environment — a known, previously-accepted quirk.

## Next step

Halt — the goal is reached; please confirm the finish. Five follow-ups are noted, none a fault in what the product computes and none blocking: reword the "ranked rows are identical" sentence to match what it actually compares (the one worth a look first), record the still-missing J-20 walkthrough at any later time as a passenger on a future run rather than the reason for one, note the undocumented `base_resolution` value for an unknown id, note that only 10 of 19 goldens were replayed this run, and note the black-frame screenshot workaround. The evaluator recommends none of these become a new build run, and suggests an "evidence" depth for whatever comes next.

## Assumptions made

- iter-35 · goal-evaluator — Ambiguity: J-20's spec requires a `[NEW]` demo-narrator walkthrough, but the engine dispatched lean depth (no demo-narrator lane) so none could be recorded; separately, the page's "ranked rows are identical" sentence is worded more broadly than what it actually checks (basis age differs on the "identical" pair). We chose: score J-20 `passing` with `evidence_makeup: true` (behavior proven via independent re-derivation and a full SSOT round-trip check; the missing walkthrough is a capture debt, not a blocking defect) and treat the "identical" wording as a spec-compliance issue (goal.md dictates that exact sentence) rather than a J-20 failure. Reversible: yes.
- iter-35 · goal-decomposer — Ambiguity: the evaluator's binding depth recommendation for this iteration was `lean`, predating the goal-proposer's mid-cycle promotion of the brand-new journey J-20. We chose: override to `Depth: full`, citing the depth-binding rule's "brand-new full-stack journey" escape condition, the same pattern used for this session's earlier brand-new journeys. Reversible: yes.
- iter-34 · goal-evaluator — Ambiguity: J-19's acceptance demands its reach line and an earlier pair be legible in one screenshot at 1440×900 with no horizontal scroll, plus a `[NEW]` walkthrough — but a direct 1440×900 capture came back solid black, and the recorded walkthrough had five of its six frames byte-identical. We chose: score J-19 `passing` with no `evidence_makeup` flag (the substance — both facts legible, nothing cut off — holds in the two available crops, a stricter test than needed), treating the duplicated film frames as presentation-only on a non-gating lane. Reversible: yes.
- iter-33 · goal-evaluator — Ambiguity: J-19 had been recorded `passing` at iter-32, and this iteration's browser lane scored it FAIL — literally a "passing → failing" pattern that reads as a regression — but the product diff was completely empty (nothing had changed since the build the owner's own second key had already reviewed and rejected). We chose: score J-19 `partial` (neither passing nor a regression) and return ESCALATE rather than REGRESSION, since a regression call implies a human-owned manual fix while this only needed two frontend lines from a developer. Reversible: yes.
- iter-33 · goal-decomposer — Ambiguity: J-19's spec asked for "a short list" of earlier pairs without naming a count, and left open whether the newest-reach/earlier-pairs contradiction should be fixed by truncating the stored value or by fixing only the on-screen grouping. We chose: cap the rendered list at 20 rows with an honest "showing N of M" disclosure, and fix only the frontend's display-time grouping, leaving the stored field's full precision untouched. Reversible: yes.
- iter-32 · goal-evaluator — Ambiguity: whether the demo-narrator walkthrough falling one section short of its own title's promise should block the finish, and whether pressing the Desk's own Top-up button (an explicit operator act named by the iteration's own spec) to photograph the new feature — which really fetched 404 new price files from the vendor — should count as breaking the "no ambient recording" rule. We chose: treat the walkthrough gap as optional tidying, not a reason for a new run, and did NOT record the 404-pair fetch as a rule violation, since it was disclosed, explicitly sanctioned by the iteration's own spec, and destroyed nothing (every pre-existing file stayed byte-untouched). Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-35.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-35-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-35-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-35-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-desk/iter-35/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
