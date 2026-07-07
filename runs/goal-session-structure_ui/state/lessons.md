# Goal Session structure_ui — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-06T23:28:23Z

**Verdict:** CONTINUE
**Lesson:** The lean baseline advanced to evaluation with **no** browser-qa artifacts —
`reports/qa/goal-structure_ui-iter-0-evidence/` was empty, no `ui-test-results.md` was written, and
`.steps` showed only decomposer/developer/review-1. This was harmless here because the finding is
purely negative/structural (surface provably absent via `GET /structure` → 404 + no `structure/`
dir; foundation provably unchanged via empty `apps/` git diff + live fingerprint `4d665603569b9dbf`),
which the evaluator can re-verify without screenshots. It will **not** be harmless from iteration 1
onward: a rendered Structure tab, the `lightweight-charts` chart, verbatim level/zone values, and
each honest empty state cannot be confirmed by code inspection — they require browser screenshots.
**Applies to:** any structure_ui iteration that builds or changes the `/structure` page (J-01/J-02/J-03)
— treat a journey with no populated `reports/qa/<iter>-evidence/` screenshot as `unknown`, not
`passing`, and do not accept a "surface renders" claim on prose alone.

## iter-1 — 2026-07-07T02:44:28Z

**Verdict:** CONTINUE
**Lesson:** `lightweight-charts` renders its canvases at explicit `z-index:1/2`, so a sibling empty/loading-state overlay left at `z-index:auto` is silently painted *underneath* — a blank chart box with no error, the exact "silent failure" the honest-UI-states anti-goal forbids. It slipped past dev + review + offline-QA and was caught only by the browser-QA pixel-scan / ux-regression lanes, then fixed in-audit (`apps/frontend/components/StructureChart.tsx:99` → add `z-10` to the `!hasBars` overlay). Second, orthogonal lesson: the audit's in-place fix left three records mutually contradictory (`ui-test-results.md` FAIL / `ux-regression.md` FAIL / `status.json` PASS) → phase-closure CLOSURE-FAIL — an auditor's in-place fix of a browser-QA FAIL is not "done" until browser-QA is re-run and the record reconciled; until then the journey is `partial`, not `passing`.
**Applies to:** (a) any structure_ui iter rendering a `lightweight-charts` chart with an empty/loading overlay — J-01/J-02/J-03 and the pre-existing `apps/frontend/components/PriceChart.tsx` on Cockpit (F2, same latent occlusion) — give the overlay an explicit `z-index` above the canvases; and (b) any iteration where the auditor fixes a browser-QA FAIL in place — require an independent browser-QA re-run (not the auditor's self-verification screenshot alone) before marking the journey `passing`.

## iter-2 — 2026-07-07T05:42:49Z

**Verdict:** CONTINUE
**Lesson:** At evaluation time this goal-mode iteration's code changes are UNCOMMITTED in the working tree, and the recorded snapshot SHA (`runs/goal-session-structure_ui/iter-2/snapshot-sha` = fe218a66…) is NOT an ancestor of HEAD — so the methodology's fallback `git diff <snapshot>..HEAD --stat` (two-dot range) returns EMPTY and would fool an evaluator into concluding "nothing was built / backend also untouched" for the wrong reason. The correct scope command here is `git diff <snapshot> -- <path>` (snapshot-tree vs working-tree, no `..`) plus `git status --short`; both then correctly show the 3 additive frontend files (`types.ts`/`api.ts`/`app/structure/page.tsx`, +361/-12) and the genuinely empty `apps/backend/` diff.
**Applies to:** every structure_ui anti-goal/diff-scope check (and any goal-mode session evaluated pre-commit) — never conclude "no diff" from a two-dot `snapshot..HEAD` range; use `git diff <snapshot>` or `git status --short`, and cross-check against the coherence-auditor's own iter-diff which uses the same snapshot-to-working-tree comparison.
