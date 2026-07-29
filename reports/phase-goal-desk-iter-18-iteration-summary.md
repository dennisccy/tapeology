# Iteration Summary — goal-desk-iter-18

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 18

## In plain words

**What you can do now:** Run a simulated tape-reading session with live moving price bars; open the Structure page to see a stock's support and resistance on a real chart; open the Desk page to screen about 100 stocks, refresh their price history, and see a ranked list where every row shows how old and deep its reading is, the exact price its "wall" was measured against, and how much history that measurement covers. You can check and repair the Desk's coverage badges, look back at any past refresh run or past scan (including two scans saved the same day), jump from a past scan into the matching Structure chart, see when a saved record fails its own integrity check, and read Desk data through a connected Claude conversation.

**What changed this time:** The Desk page's ranked table gained a new "opposite" column showing, for every row, the nearest wall found on the other side of price from the one the row is ranked on — plus a new line in the row's hover tooltip counting how many A/B/C walls were found for that stock. It works and its numbers check out, but on 2 of the owner's 63 real stocks it currently points at a wall that is more than twice as far away as the truly closest one, so the column doesn't yet keep its "nearest wall" promise on every row.

**What's next:** Fix the new "opposite wall" column so it always names the truly closest wall on the other side of price (a small, one-rule code change), and re-film the guided walkthrough for this and two earlier features so the recordings actually show the populated page.

## Headline

Desk table's new "opposite wall" column ships but discloses the best-graded wall, not the nearest, on 2 of 63 rows

## Direction

**Signal:** holding
**Why:** J-14 was built, wired into the UI, and its numbers are independently proven correct — but the evaluator scored it `partial` because the shipped selection rule picks the best-graded wall on the other side of price rather than the truly nearest one, which is what goal.md's own title and wording ask for; the two rules disagree on 2 of the owner's 63 real rows (HONA, META). J-01 through J-13 all re-verified passing with zero regressions and no anti-goal violations, so the existing product surface holds steady while this one addition needs a small follow-up fix.

**Trend (last 5 iters):**
- Newly passing this iter: none (J-14 landed as `partial`)
- Newly passing in last 5 iters total: J-10 (iter-14), J-11 (iter-15), J-12 (iter-16), J-13 (iter-17)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The new `opposite` column is real, it is on screen, and its numbers are correct — the evaluator opened the screenshot directly and re-computed every value from the price files. But the page does not always name the nearest wall on the other side of price, which is exactly what this journey's own title promises: the goal file says "pick the closest one first," the code picks "the best-graded one first" instead, and on the owner's real 63-name screen the two rules disagree on 2 rows, where the page would show a wall more than twice as far away as the closest one. J-01 through J-13 all still work.

## What was done

- Product changes: apps/backend/app/research/desk_screen.py, apps/backend/tests/test_desk_screen.py, apps/backend/tests/test_mcp_server.py, apps/backend/tests/test_desk_ui_guards.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx
- Added an `opposite_band` field to every ranked Desk row — the selected wall on the other side of price, with side/class/price range/distance, honestly `null` when no wall exists there and entirely absent (never backfilled) on screens recorded before this iteration.
- Added a `bands_by_class` field — a plain per-class (A/B/C/unclassified) count of every wall found for a symbol — shown in the row's existing hover tooltip.
- Extended the `/desk` table with a new "opposite" column (11th column) and a new tooltip line, reusing the established legacy-absent/null/populated rendering pattern; zero new endpoint, MCP tool, or Config field.
- Audit strengthened an existing backend test to prove both new fields byte-identical against the real `/research/tradability` endpoint (not just mocked data) — found no product defect, closed a test-coverage gap.
- Browser QA: 23/23 journeys passed (13 regression replays including the MCP contract, plus 10 J-14-specific checks); backend suite grew to 1448 passed / 8 skipped, 0 failed; config fingerprint unchanged (`08e471b10130e1e2`).

## What's left

- Journey J-14 is `partial`: the shipped rule discloses the best-graded wall on the other side of price, not the nearest one, on 2 of the owner's 63 real rows (HONA, META) — goal.md's wording and the code's own docstring/comment both say "nearest."
- J-14's demo-narrator walkthrough doesn't show the new capability at all — 4 of its 6 frames captured the wrong page (`/structure`), and the walkthrough verdict is `RECORDED_WITH_NOTES`, not `RECORDED`.
- J-12's and J-13's earlier capture-quality gaps (`evidence_makeup`) are still carried and unresolved this iteration: J-12's earlier same-day comparison screenshot is still cropped short, and J-13's walkthrough still narrates only the legacy, unpopulated state.
- The opposite wall's own quality score (`band_score`) is computed but not shown anywhere in the UI — a deliberate scope decision, available for a future iteration if wanted.
- Screens recorded before this iteration will forever show "opposite wall not recorded in this snapshot" instead of real values, by design — never backfilled.

## Next step

Run one more iteration at full depth with two pieces of work, both on J-14. First, make the "opposite" column show the closest wall on the other side rather than the best-graded one — a one-rule change in `apps/backend/app/research/desk_screen.py`'s `_select_opposite_band`, its stored test comparisons, and the two comments that already claim "nearest"; if the owner prefers the current grade-first behaviour instead, then goal.md and both comments should stop saying "nearest." Second, re-film the guided walkthrough on a throwaway copy of the data with a freshly computed screen, which also clears the older walkthrough gaps still owed for J-12 and J-13 — and never start a second copy of the web front end from the same source folder while another one is running.

## Assumptions made

- iter-18 · goal-evaluator — Ambiguity: goal.md's J-14 step 1 states the opposite-band selection rule two ways that read against each other — the sentence order says distance-first ("nearest"), while a trailing parenthetical names the existing `_select_best_band` helper, whose key is class-first; goal.md doesn't say which wins. We chose: distance-first is the requirement, so J-14 is scored `partial` (measured a real 2-of-63-row divergence on the owner's own screen, and the shipped docstring/comment already claim "nearest"). Reversible: yes — either a one-key code edit or a wording fix to goal.md and both comments resolves it; nothing recorded blocks either direction.
- iter-17 · goal-evaluator — Ambiguity: J-13's acceptance requires a `[NEW]`-flagged walkthrough covering the price disclosure "end to end," but the produced walkthrough was recorded against the ambient store before an audit fix, so it shows only the unpopulated legacy state — goal.md doesn't say whether that counts as covering the disclosure. We chose: score J-13 `passing` and record the walkthrough shortfall as a capture defect (`evidence_makeup: true`) rather than an unmet acceptance clause, since the underlying behaviour is independently proven three other ways. Reversible: yes — one re-filming run on a fixture-scoped rig produces the literal artifact and clears the flag; read strictly, J-13 would revert to `partial` until then.
- iter-16 · goal-evaluator — Ambiguity: J-12's acceptance asks for a same-day coverage-badge difference "legible across the screenshots," but the earlier view's only genuine full capture is a viewport crop that stops above the named row, so the named comparison isn't literally legible on both sides. We chose: score J-12 `passing` and record the framing shortfall as a capture defect rather than an unmet clause — the difference is independently re-derived from the stored files and confirmed via DOM reads. Reversible: yes — one full-page re-capture closes it, no program change.
- iter-16 · goal-decomposer — Ambiguity: goal.md's J-12 step 1 requires an honest refusal when `id` and `date` are both given, but doesn't name the HTTP status code. We chose: leave the exact code to build discretion (any honest 4xx, never a silent 200 or a 5xx); 422 was the natural pick since it matches the router's existing FastAPI-validation convention. Reversible: yes — a later iteration can pin the exact code with zero effect on any recorded data.
- iter-15 · goal-evaluator — Ambiguity: J-11's acceptance asks for a byte-identical rank-order comparison using the SAME pins before and after the change, but no such before/after pair exists because re-running the same pins correctly returns the already-recorded snapshot instead of recomputing. We chose: treat the clause as satisfied by an equivalent proof — the unchanged rank-key source in `git diff`, identical ranked/skipped symbol sequences across the two nearest snapshots, and golden tests — rather than the literal comparison. Reversible: yes — a future same-date-different-code comparison or a golden fixture would give the literal proof.
- iter-15 · goal-evaluator — Ambiguity: the iteration spec required every lane to use a fixture-scoped rig, but the actual "scoped" rig carried no store override at all, so the browser-QA and demo lanes computed a real screen into the owner's own ambient data folder. We chose: record it as a disclosed process deviation, not a `docs/goal.md` anti-goal violation, since no bar file was modified, only a derived/rebuildable index and one new append-only snapshot were touched, and the trigger was an explicit POST, never a scheduler. Reversible: no — the appended snapshot is permanent by design; the remedy going forward is a rail that forces evidence lanes onto a truly scoped store.
- iter-14 · goal-evaluator — Ambiguity: docs/goal.md's Anti-goals section carries an uncommitted wording edit this iteration, and the file doesn't record who made a given edit, so it's unclear whether the goal-proposer (forbidden from editing that section) or the owner made the change. We chose: treat it as owner-authored maintenance, not a proposer breach — the edit's timestamp aligns with the owner's own unrelated config edit, an hour after the proposer finished, and the proposer's own result file claims only the J-10 journey promotion. Reversible: yes — a one-line revert has no effect on any journey if the owner did not in fact author it.

## Quick verify

From `reports/phase-goal-desk-iter-18-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll down to the ranked table (inside the "Briefing" panel, below "Provenance") and scroll it horizontally all the way to the right
3. Find the row whose leftmost cell reads "BRK-B" (it is the first/topmost ranked row) and read its rightmost cell (the new "opposite" column)
4. Hover your mouse anywhere over that same `BRK-B` row (the whole row is one clickable link, so any spot works) and wait for the tooltip to appear
5. Look at the `BRK-B` row's other cells: "distance", "score", and "band"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-18.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-18-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-18-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-18-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-18-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-18-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-18-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-18-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-18-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-desk-iter-18-ux-regression.md |
| QA | PASS | reports/qa/goal-desk-iter-18-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-18-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-18-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-18/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
