# Iteration Summary — goal-desk-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-26
**Iteration:** 6

## In plain words

**What you can do now:** You can run a simulated tape-reading session and watch it settle into a read like "Buyer Control," with live moving price bars. You can open the Structure page, pick a stock and date, and see its key support and resistance levels mapped over a real price chart, including opening a past case study. You can open the Desk page, which scans about 100 well-known stocks: fetch the company list, refresh their price history, and run a fresh ranking that shows which stocks are sitting closest to one of their own key price levels today, with an honest note on every stock that couldn't be ranked. You can now also click any past scan in the Desk's history list to revisit it exactly as it was recorded, and click any stock row to jump straight into the Structure chart for that stock and date, already loaded.

**What changed this time:** Clicking a past Desk scan now shows exactly what was recorded that day — nothing is recalculated. A "Latest" button snaps back to today's scan instantly. And clicking any row in the Desk's results (even one that was skipped) now takes you straight to the Structure chart for that stock and date, already filled in and drawn.

**What's next:** Next we'll add the two remaining ways for Claude to read the Desk directly, fix the hover details that the new clickable rows accidentally hid, and take a few missing photographs of the older pages so this chapter can close.

## Headline

Desk's screen history is now clickable and every briefing row drills into Structure prefilled

## Direction

**Signal:** improving
**Why:** J-05 ("Ledger history + drill-in to /structure") moved from failing to passing this iteration — the Desk's history rows now fetch-and-swap a past screen verbatim, and every briefing row (ranked or skipped) drills into `/structure` with the symbol and as-of already loaded, verified against the real recorded snapshot and 17/17 live browser checks. J-01–J-04 all re-verified passing with zero regressions, and J-06 (the 17-tool MCP contract) remains the only journey still failing, deliberately out of scope this iteration. Every one of the last five iterations (2 through 6) advanced at least one journey, so direction is healthy.

**Trend (last 5 iters):**
- Newly passing this iter: J-05
- Newly passing in last 5 iters total: J-02, J-03, J-04, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 3 minor (2 resolved in-iteration — an append-only overwrite bug at iter-3 and a NaN-row data issue at iter-4; 1 still unresolved — the iter-4 frozen-file exception awaiting the owner's written ratification)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The Desk can now browse its own history and jump into the chart. Clicking a past screen in the history list shows that screen's own recorded rows — I checked all ten rows, the ninety-one "no bars" rows and the five provenance lines against the real recorded file on disk, and they match exactly. Clicking a row opens the Structure page with the symbol and the date already filled in and the wall already drawn. J-05 "Ledger history and drill-in to Structure" therefore moves from failing to passing.

## What was done

- Made Desk's "Screen History" rows clickable — selecting a past date swaps in that exact recorded screen's rows, skipped members, and provenance (a read-only re-render, no recompute).
- Added a "Latest" control that instantly reverts to the newest screen, plus a banner showing which date is currently being viewed.
- Made every Desk briefing row (ranked or skipped) a clickable link into `/structure?symbol=<sym>&asof=<as_of>`, landing with the symbol and date already loaded and the chart already drawn.
- Added Structure's query-param prefill: auto-fills Symbol/As-of and auto-loads when both are present — additive only, byte-unchanged when a link carries no params.
- Added two new guard tests confirming the Desk page never recomputes structure values and the Structure prefill reuses the existing load function.
- Fixed the J-04 replay script so replaying it never writes a real screen record into a live backend.
- Verified 17 target journey checks pass browser QA (17/17 PASS) plus 2/2 on the deterministic replay lane.

## What's left

- Journey J-06 (MCP contract v3 — 17 read-only tools) failing — tool count is still 15; deliberately out of scope this iteration.
- Journey J-07 (The kept product stands) partial — blocked solely on J-06's tool count.
- The new whole-row drill-in link now sits on top of every cell, hiding the hover text that used to show the exact distance value and "window last requested" dates — needs a decision (whole-row link vs. per-cell hover) plus a test that checks which element is really on top.
- The new J-05 replay script has never been run by the deterministic replay lane, and it currently selects its history row by position rather than by date.
- The owner has still not confirmed in writing whether the two files iteration 4 changed (the bar store and the Structure chart) may stay changed.
- Missing kept-product screenshots since iteration 4: the simulated cockpit, the Case Studies drill-in, and the honest Edge Report panel.
- Carried hardening items: a CLI screen-write-path guard, a per-series price-less-row filter, one chart-guard-test re-tightening, the same-date screen ambiguity (two same-day scans can't be told apart by date alone), and keyboard access for the history rows.

## Next step

Run iteration 7 at full depth and treat it as the closing run, in this order: (1) build J-06 — add the two read-only desk tools so the MCP count reaches 17, proving each returns exactly what its web address returns in both the empty and filled state; (2) settle the hover problem — pick one behaviour (whole-row link or per-cell hover text) and add a test that checks which element is really on top, so it cannot break silently again; (3) take the kept-product pictures J-07 still lacks since iteration 4 — the simulated cockpit, the Case Studies drill-in, and the honest Edge Report panel; (4) play the new J-05 replay script once and change its second step to pick the history row by date instead of "the first row"; (5) ask the owner to write in `docs/goal.md` whether the two files iteration 4 changed may stay changed — only he can grant that; (6) carry, do not force, the same-date screen ambiguity, keyboard access for history rows, and the remaining one-line hardening items. One sentence for the owner: the Desk now browses its own history and jumps into the chart, so the next run should add the two Claude-readable desk tools, restore the hover details the new row links hid, and photograph the older pages one final time — after that the era is finished.

## Assumptions made

- iter-6 · goal-evaluator — Ambiguity: the browser-evidence rail doesn't say whether a screenshot captured before a same-iteration fix still counts as valid evidence, and J-05's four screenshots were taken before the auditor's `isViewingLatest` fix landed. We chose: count the screenshots — the fix only touches a path none of the four captures exercises, corroborated by the auditor's live re-run and the evaluator's own field-for-field check against the real recorded file. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: goal.md's J-05 step doesn't say whether both ranked and skipped briefing rows should be drill-in links. We chose: link both row kinds — a skipped symbol still drills into Structure's own honest empty state, matching the era's "describe, never fabricate" discipline. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: goal.md demands a byte-for-byte identical `.data/` listing before and after a browser pass, but two dated SQLite side-files appeared during the pass. We chose: not a violation — the index file itself is untouched, the side-files are empty, and no registered record changed; ambient-store integrity is scored on registered content, not SQLite bookkeeping files. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: whether a screenshot whose layout was altered by a capture aid (repositioned/outlined controls, one held-open reply) still counts as the required evidence. We chose: count it — the rendered elements are the real components in real states, corroborated three independent ways; future reports must disclose such aids up front. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: whether an iteration spec can self-grant an exception to a critical "frozen foundations" rail (this iteration changed the bar store and the Structure chart, both named frozen). We chose: score it a disclosed minor deviation pending the owner's written ratification, not a critical violation — output is identical for good data, the pinned band and fingerprint are unchanged, and the change repairs a surface that would otherwise crash. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: who must capture a required screenshot, since the goal is silent but the spec names a specific lane, and this iteration's captures came from other agents instead. We chose: count a screenshot anyone opened as genuine evidence for the state it shows, but refuse to let it satisfy the lane requirement or substitute for a still-missing state. Reversible: yes
- iter-4 · developer (fix pass) — Ambiguity: how to handle 60 recorded bar records holding a price-less value written by the new Top-up button, when the rules say recorded data is never content-perturbed and say nothing about a non-numeric value. We chose: exclude the bad rows on read only, reported honestly, never deleting or rewriting any file — after measuring that the alternatives would either silently move the results or hide a bug that was deleting bands outright. Reversible: yes — the files are untouched, so any later policy is still available
- iter-4 · goal-decomposer — Ambiguity: the goal never states how the Run Screen button supplies the required date without becoming a disallowed "wall clock" dependency. We chose: Run Screen always submits the browser's own "today" as an explicit, operator-clicked value — the backend itself never reads wall-clock time, and a separate command-line flag remains the path for an arbitrary historical re-screen. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: an audit finding showed the "best band" selection ranks nearest distance ahead of highest score, so a stock's headline row isn't necessarily its strongest band, and the goal is silent on which a "best band" should mean. We chose: keep the underlying ranking unchanged and make the on-screen label read "nearest same-class band" instead of implying it is the stock's strongest. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: whether a recorded creation-time field on each screen snapshot breaches the "no wall-clock" rail. We chose: read it as record-keeping metadata, not a research value — it plays no part in the pinned key or the checksum, and identical inputs still reproduce byte-identical results. Reversible: yes

## Quick verify

From `reports/phase-goal-desk-iter-6-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. In the "Screen History" table, click the row whose "date" column reads `2026-06-22`
3. Click the "Latest" button in that banner
4. Click the row dated `2026-06-22` again, then click anywhere on the `AAPL` row in the Briefing table
5. Look at the Tradable Map table's "range" column for the first row

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-6-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-6-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-6-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-6-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-desk-iter-6-ux-regression.md |
| QA | PASS | reports/qa/goal-desk-iter-6-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-6-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-6-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-6/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
