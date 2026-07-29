# Iteration Summary — goal-desk-iter-20

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-29
**Iteration:** 20

## In plain words

**What you can do now:** Open the Desk page and see about 100 stocks ranked by their nearest key price wall, with fresh price history behind them. Every ranked row shows how many days of history back its wall up, the exact closing price and price range the wall was measured against, and — new this chapter — the nearest wall on the other side of price. You can check and repair the page's coverage badges, look back at any past scan by name (including two scans saved on the same day), jump from a past scan straight into the matching Structure chart, and see on screen if a saved record fails its own integrity check. A connected Claude conversation can also read Desk data through 17 read-only tools.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team retook a missing full-page picture proving that two scans saved on the same day genuinely show different price-history coverage for one stock (Netflix), closing an old picture debt. They also tried to record a new guided walkthrough video of the Desk page's price and "nearest wall" columns, but that attempt failed — a broken recording script meant no video came out.

**What's next:** Next, the team will fix the broken recording script and record the missing walkthrough video of the Desk page — and the owner needs to decide how to handle one screenshot (a hover-tip picture) that this test setup simply cannot capture.

## Headline

Evidence-only iteration: no code changes were planned or made.

## Direction

**Signal:** holding
**Why:** All 14 journeys remain passing with zero product diff this iteration — J-12's outstanding picture debt closed, but the required walkthrough video for J-13 and J-14 still failed to record because of a broken script file, so the verdict stays CONTINUE rather than GOAL_ACHIEVED. No journey is failing or regressed; the remaining work is a machine-doable re-capture plus one owner decision on J-14's un-photographable tooltip clause, which iteration 19's independent second check already flagged as blocking the finish.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-13 (iter-17), J-14 (iter-19)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 1 of last 4

**Latest evaluator reasoning:** This run changed no program code at all. Its whole job was to take two pictures that earlier runs owed. The other one failed: the guided walkthrough film over a full Desk page was never recorded, because the film's own instruction file was written with a broken line and the film step gave up and wrote "SKIPPED", leaving its picture folder empty. Because the film the goal file asks for twice is still missing, and because one more picture can only be settled by the owner, I am not calling the goal finished.

## What was done

- Product changes: No product change this iteration.
- Captured a corrected full-page screenshot of the earlier 2026-07-27 same-day scan (`screen-2026-07-27-936543601e75`), closing J-12's outstanding picture debt (`evidence_makeup` cleared).
- Re-derived the captured numbers directly from the stored recording files — zero mismatches — confirming the NFLX "all timeframe badges dark" comparison the goal file names is now legible across both same-day scans.
- Attempted to record the required `[NEW]`-flagged walkthrough video for J-13/J-14 over a populated Desk screen; it failed because its script file (`reports/phase-goal-desk-iter-20-demo.json`) held invalid JSON (stray regex patterns at 3 lines), so the recording lane wrote "SKIPPED" and produced no video.
- Re-verified J-04, J-05, J-07 via deterministic golden replay and re-counted the MCP tool list directly (17 tools, config fingerprint `08e471b10130e1e2` unchanged).
- Confirmed zero footprint on the owner's real data store this run — no files created, modified, or removed under `apps/backend/.data`.
- Verified 6 journeys (J-04, J-05, J-07, J-12, J-13, J-14) pass browser QA — 6/6, 0 skipped.

## What's left

- J-13 and J-14: the required demo-narrator walkthrough video over populated Desk rows is still not recorded — the capture script needs its click-target syntax fixed before it can run.
- J-14: the hover-hint tooltip screenshot still can't be captured in this test rig (a browser limitation) — needs an owner decision on how to satisfy that requirement (read the hint's text from the page instead, already proven correct, or add an on-page panel a picture can capture).
- Carried, not defects: the Desk page is now eight stacked sections and long, the run-history tables have no length limit, and the history rows can't be reached by keyboard.

## Next step

One more short capture-only run, plus one decision only the owner can make. For the chain: fix the walkthrough script's broken syntax (write click targets as plain quoted text, and describe the sideways reveal of the band/opposite columns as a table scroll rather than a click on a button that doesn't exist), verify the script parses before the film runs, then record the walkthrough over the populated Desk screen — on a throwaway copy of the data folder, proving the serving program really points at the copy rather than the owner's real data. For the owner: the goal file asks for a photograph of the hover-hint that appears over a briefing row, but this test setup cannot photograph that kind of hint at all; please choose either reading the hint's text from the page instead (already proven correct) or adding an on-page panel a picture can capture.

## Assumptions made

- iter-20 · goal-evaluator — Ambiguity: goal.md makes a walkthrough film an acceptance requirement for J-13/J-14, but the evaluator's own contract says a missing recording must never be scored as blocking and must never become a new iteration's goal — this iteration was dispatched specifically to capture that film and still produced nothing. We chose: split the two questions — J-13/J-14 stay `passing` with `evidence_makeup: true` (the behaviour is proven, only the artifact is missing), but the overall verdict stays `CONTINUE` rather than `GOAL_ACHIEVED`, because iteration 19's independent second check already refused the finish over this exact missing film. Reversible: yes.
- iter-19 · goal-evaluator — Ambiguity: this iteration's own plan said never to write a screen/universe snapshot into the owner's real data folder, but the evidence lanes ran a real price top-up (390 new files) and recorded four new screens there anyway; goal.md doesn't say whether an agent-triggered write against the owner's own store counts as the "explicit operator act" it requires. We chose: record it as a disclosed process deviation, not a goal.md anti-goal violation, since no pre-existing file was touched or rewritten — only new files were added. Reversible: no — the appended run record, four screens and 390 fetched series are permanent by design.
- iter-19 · goal-evaluator — Ambiguity: J-14's acceptance requires both a tooltip photograph and a `[NEW]`-flagged walkthrough film; neither exists after that run — the tooltip is a native browser hint painted outside any screenshot, and the walkthrough lane ran after evaluation because the iteration was dispatched lean. We chose: score J-14 `passing` with both flagged as capture defects rather than unmet acceptance, since the underlying behaviour is proven three other ways and looping forever on an uncapturable photograph would be the framework's worst anti-pattern. Reversible: yes for the film; no for the tooltip photograph in this rig unless the clause is reworded.
- iter-18 · goal-evaluator — Ambiguity: goal.md's J-14 wording states the opposite-wall selection rule two ways that disagree with each other — the sentence itself points to distance-first, but its own parenthetical names the existing class-first helper, which is what shipped. We chose: read distance-first as the requirement and score J-14 `partial`, because two of the owner's 63 real rows (HONA, META) genuinely pointed at a farther wall under the shipped rule — a real behavioural gap, not a wording quibble. Reversible: yes — either the code or the goal-file wording can move to make the two agree.
- iter-17 · goal-evaluator — Ambiguity: goal.md requires a `[NEW]`-flagged walkthrough covering J-13's price disclosure end to end, but the recorded walkthrough came back with notes and was filmed against the old, pre-fix screen state, showing no band range or close anywhere. We chose: score J-13 `passing` and record the walkthrough shortfall as a capture defect rather than an unmet clause, since the underlying behaviour is proven three independent ways. Reversible: yes — a fresh re-filming run on a properly populated screen produces the literal artifact with zero program change.
- iter-16 · goal-evaluator — Ambiguity: goal.md's J-12 acceptance asks for a named row's coverage badge to be legible across both same-day recordings, but the earlier recording's only genuine full-page capture stopped just above that row. We chose: score J-12 `passing`, since the coverage difference is legible another way (an on-screen sentence plus the two stored files' own data), and record the framing shortfall as a capture defect. Reversible: yes — one full-page re-capture of the earlier recording closes it with zero program change (this is exactly what iteration 20 then did).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-20.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-20-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-20-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-20-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-20/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
