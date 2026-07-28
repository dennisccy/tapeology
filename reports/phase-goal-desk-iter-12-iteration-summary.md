# Iteration Summary — goal-desk-iter-12

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-07-28
**Iteration:** 12

## In plain words

**What you can do now:** Run a simulated trading session that settles into a plain-language read like "Buyer Control," with live moving price bars. Open a page that shows a stock's support and resistance levels drawn on a real chart, with examples of past price touches. Open a Desk page that screens about 100 stocks, refreshes their price history, and produces a fresh ranked list — each row shows how old its price reading is, and any unrankable stock is called out honestly. Look back at any past price-refresh run and see exactly what happened — how many stocks were reused, freshly fetched, or failed, and why. Jump from any past scan straight into the chart for that stock and date. If you use Claude, it can read the Desk's saved data directly, but never change anything.

**What changed this time:** Behind-the-scenes work only — nothing new for a user to see or do this round. The team tried again to record a short guided video proving the run-history panel end to end (empty, then with saved runs), but the recording still wasn't made — this time because of a scheduling mix-up in how a short work round is run, not any problem with the feature itself. Everything the panel does was re-checked by hand and still works correctly, and nothing that worked before broke.

**What's next:** Next we'll redo this round in the longer, more careful form, so the video gets recorded before anyone checks it off — filming the panel empty first, then with real saved runs — so this chapter of work can close.

## Headline

Required top-up-run walkthrough still not captured; evaluator escalates to full depth

## Direction

**Signal:** holding
**Why:** Iteration 12 was scoped purely to capture J-09's outstanding demo-narrator walkthrough, but no walkthrough was produced — the evaluator traced this to a structural bug in the lean-depth pipeline (the walkthrough lane runs after scoring, so a lean iteration can never satisfy a clause the evaluator must judge). J-01–J-08 were all re-verified passing with zero product-code diff and no regression, so nothing was lost, but J-09 has now sat at `partial` for two iterations running on the exact same clause, which is why the evaluator escalated to full depth rather than repeat a lean iteration.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-07 "The kept product stands — regression sentinel" (iter-8), J-08 "Every ranked briefing row names the bar its distance was measured from" (iter-10)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (two disclosed non-violation deviations noted along the way: iter-9's write into the real data folder during QA, iter-12's leftover CPU-burning process)
- Iters with no journey state change: 1 of last 5 (this iteration)

**Latest evaluator reasoning:** "This run was asked to do one thing: record a guided walkthrough that shows the new top-up run record both when nothing is saved and when a saved run is on screen. That walkthrough was never made. I found out why, from the session's own activity log: when a run is done in the SHORT form, the walkthrough is recorded AFTER I score the work, so I can never see it; in the LONG form it is recorded BEFORE me."

## What was done

- Confirmed zero product/application code change this iteration (all 16 named product files byte-unmodified) — a pure evidence-capture/showcase dispatch.
- Seeded a fresh scoped throwaway data rig and recorded three checkpoint top-up runs (ordinary `done 404/404`, cancelled `3/404`, one induced failed pair "AAPL 1h — no data for that window") against the real production code path, with zero live vendor calls.
- Captured standalone browser-qa-agent screenshots for J-09's two states — the honest empty "No top-up runs recorded yet." panel (on a separate, genuinely empty scoped rig) and the populated Top-up Runs section with the failed pair's detail legible.
- Replayed the regression set (J-01–J-05, J-07, J-08) against the scoped rig — 7/7 PASS — and re-confirmed J-06's 17-tool MCP contract live (35/35 tests).
- Re-ran the full backend suite (1369 passed / 8 skipped / 0 failed), reconfirmed the settings fingerprint `08e471b10130e1e2` unchanged, and proved zero write landed in the real (ambient) data folder.
- Browser QA: 9/9 test rows passed, but the required `[NEW]`-flagged demo-narrator walkthrough for J-09 was never produced this iteration — so 0 target journeys reached full passing status; the evaluator traced this to a structural depth-ordering issue in the pipeline.

## What's left

- Journey J-09 ("Every top-up run leaves an append-only record of what it attempted") is still `partial` for the second iteration in a row — the required `[NEW]`-flagged demo-narrator walkthrough (showing both the empty and populated Top-up Runs states) has still not been produced.
- Root cause found: at lean depth, the demo-narrator walkthrough lane runs AFTER the evaluator scores the iteration, so a lean iteration structurally can't supply the artifact J-09 still needs — iteration 13 must run at full depth instead.
- A leftover scoped backend process (PID 1180202) is still running, burning roughly 78% CPU with no frontend attached — an orphaned simulated-tick feeder from repeated replay runs; not a product defect, but should be stopped before the next iteration on a host that has already hard-reset five times under load.
- Nothing is currently serving pages — both scoped rigs used for this iteration's screenshots have been shut down; the next iteration must bring a fresh pair up before it can record anything.
- Carried, non-blocking: the run list doesn't yet surface a corrupted record file the way the sibling universe/screen lists do; a just-finished run can stay invisible in the panel until a manual reload, in a narrow timing window; the run history table has no row cap; the Desk page is six stacked sections and growing long; two screens saved on the same calendar day can't be told apart by a date-only lookup; keyboard access for the history rows is still missing.

## Next step

Run iteration 13 in the long (full) form, with no program-code change. First bring the scoped rig back up — stop the leftover backend that is still burning CPU and start a clean pair. Then fix the ordering that broke this iteration: copy the data folder, boot the page, photograph the honest empty "No top-up runs recorded yet." state FIRST, only then record the three checkpoint runs (one ordinary, one cancelled, one with a failed pair — the recipe already works), and photograph the populated panel. Finally, record the `[NEW]`-flagged demo-narrator walkthrough in that same run, showing both states in sequence and naming which data folder was used. Everything else about J-09 is already proven and should not be redone.

## Assumptions made

- iter-12 · goal-evaluator — Ambiguity: nothing in docs/goal.md says whether an acceptance clause may be scored against an artifact a later lane in the same iteration is expected to produce (J-09's outstanding walkthrough runs after the evaluator at lean depth). We chose: score strictly on what exists at evaluation time — no walkthrough on disk means the clause stays unmet — and ESCALATE to force full depth, where the walkthrough lane runs before scoring, instead of continuing and hoping. Reversible: yes — if the owner reads the walkthrough clause as satisfiable by a later showcase lane, whatever that lane records at finalization can close J-09 without another iteration.
- iter-12 · goal-evaluator — Ambiguity: J-09's acceptance implies one scoped rig photographed before-and-after a run, but the delivered frames came from two different scoped roots (one populated, one empty) because the dev's own seed-then-record-then-boot order had already closed the honest-empty window before any browser existed. We chose: accept both frames as satisfying the two browser clauses, since both roots are same-day copies of the identical ambient tree and a single-root capture would have required deleting real append-only records. Reversible: yes — a later iteration that boots the frontend before recording would produce both frames on one root and moot this.
- iter-11 · goal-evaluator — Ambiguity: docs/goal.md requires a demo-narrator walkthrough covering J-09 "end to end," but the recorded walkthrough only narrates the empty panel, never a saved run. We chose: score J-09 `partial`, not `passing` — the rule that showcase artifacts are non-blocking governs the pipeline gate, not a journey's own goal.md acceptance, and the missing evidence is reachable with zero code change. Reversible: yes — a one-line clarification of "end to end" in J-09's acceptance text could settle it either way.
- iter-11 · developer — Ambiguity: whether every historical Top-up Runs row needed a full reused/fetched/failed breakdown, or only the latest run. We chose: show the full breakdown only for the latest run, matching what the backend's own list data carries for older rows. Reversible: yes — a future backend field could add per-run outcome counts without touching the store's append-only discipline.
- iter-11 · developer — Ambiguity: the spec said the new Top-up Runs section should sit "beside" Screen History, but Screen History only renders once a screen has been run, while a top-up is a fully independent operator act. We chose: render Top-up Runs as its own always-visible section, not nested inside the screen's conditional block. Reversible: yes — moving it later is a pure layout change with no backend impact.
- iter-11 · developer — Ambiguity: the goal-decomposer left open exactly where to capture the new run record's "requested fetch window" field. We chose: call the existing window-lookup function once per run, in the caller, before the walk starts — never inside the writer or a second time per pair. Reversible: not stated in the ledger.
- iter-11 · goal-decomposer — Ambiguity: docs/goal.md named a top-up run record field ("the requested fetch window") without specifying its shape. We chose: register it as a simple start/end date pair, a direct packaging of the existing per-pair window-lookup function's own value. Reversible: yes — the shape can be widened later without touching any other field.
- iter-10 · goal-evaluator — Ambiguity: whether every acceptance clause for J-08 needed fresh, same-iteration photographic proof — one clause (a legacy snapshot's honest "not recorded" text) couldn't be re-photographed because the scoped rig now only held newer, basis-carrying recordings for that date. We chose: score J-08 `passing` on this iteration's new evidence plus iteration 9's own evidence for the unreproducible clause, since the product code was proven byte-identical between the two iterations. Reversible: yes — if the owner requires all clauses re-evidenced in the same iteration, J-08 returns to `partial` until one more capture run.
- iter-9 · goal-evaluator — Ambiguity: browser QA clicked "Run Screen" against the operator's real data folder instead of the intended throwaway copy, writing one real screen snapshot there. We chose: log it as a disclosed hygiene deviation, not an anti-goal violation — every individual rail was checked and held. Reversible: yes — if the owner treats the scoped-rig discipline as a hard rail rather than a convention, this becomes a minor violation needing a remediation note.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-12-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-12-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-12-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-desk/iter-12/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
