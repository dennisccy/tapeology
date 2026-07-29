# Iteration Summary — goal-desk-iter-16

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-full
**Date:** 2026-07-29
**Iteration:** 16

## In plain words

**What you can do now:** Run a simulated tape-reading session with live moving price bars; open the Structure page to see a stock's support and resistance levels on a real chart; and open the Desk page to screen about 100 stocks, refresh their price history, and rank them, with each row showing how old and how deep its reading is. You can check and repair the Desk's own coverage badges, look back at any past price-refresh run to see exactly what it did, and read the Desk's data through a connected Claude conversation. New this round: you can now open any past scan by its own name — including an older scan saved on the same day as a newer one that used to hide it — and the run-history panels now tell you out loud if one of their own saved files is damaged.

**What changed this time:** The Desk page's "Screen History" list now has a "recorded" column showing exactly when each scan was saved, and clicking a row opens that exact scan (not just "whichever scan matches this date"), so two scans from the same day now open separately. The "Provenance" panel names the exact scan on screen and its recorded time. The "Top-up Runs" and "Index Reconciliation" panels now show a plain warning naming any of their own saved files that fail an integrity check, instead of staying silent about it.

**What's next:** Nothing is planned to build next — the team is asking you to look over "The Desk" chapter and confirm it's finished. A handful of small, optional polish items (like telling two same-day scans apart at a glance without opening them, and keyboard navigation of the history rows) are noted for later, none of them blocking.

## Headline

Open any recorded screen snapshot by its own identity, not just by date

## Direction

**Signal:** improving
**Why:** This iteration built and verified J-12 (snapshots individually addressable by id, plus honest damaged-file disclosure on the two run ledgers), bringing all twelve Must-have journeys to passing. The audit caught and fixed three evidence-lane defects (a wrong-page demo walkthrough, two skipped integrity-note browser tests, one wrong-app screenshot) before the evaluator scored the run, and the evaluator independently re-derived every load-bearing claim from disk rather than trusting reports. This iteration also wrote nothing at all into the owner's real data folder — the cleanest run of the era on that front.

**Trend (last 5 iters):**
- Newly passing this iter: J-12
- Newly passing in last 5 iters total: J-09 (iter-13), J-10 (iter-14), J-11 (iter-15), J-12 (iter-16)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (iter-14 and iter-15 each carried one disclosed process deviation — an agent-triggered write against the real ambient store — that the evaluator classified as a plan breach, not a goal.md anti-goal violation)
- Iters with no journey state change: 1 of last 5 (iter-12, which ESCALATEd solely on a missing walkthrough film, not a journey regression)

**Latest evaluator reasoning:** This run had one job: make every screen recording the history list already names openable on its own, and make the two run lists say out loud when one of their own files is damaged. Both are built, and I checked them myself rather than reading the reports. I opened the pictures: the same day, 2026-07-27, now opens as two separate recordings, each naming its own recording time on screen, and a damaged file is named in plain words on the page instead of being dropped in silence. All twelve journeys now pass.

## What was done

- Product changes: apps/backend/app/research/desk_routes.py, apps/backend/tests/test_desk_screen.py, apps/backend/tests/test_desk_topup_compute.py, apps/backend/tests/test_desk_index_reconcile.py, apps/backend/tests/test_mcp_server.py, apps/frontend/lib/types.ts, apps/frontend/lib/api.ts, apps/frontend/app/desk/page.tsx
- Added `GET /research/desk/screen?id=` for byte-identical lookup of any individually-recorded snapshot, with an honest 4xx (422) refusal when `id` and `date` are both supplied.
- Added `integrity_errors` disclosure to `GET /research/desk/topup/runs` and `GET /research/desk/coverage/reconcile/runs` (previously silently discarded by both routes).
- Frontend: Screen History rows now select and highlight by snapshot id (not date) and show a new "recorded" column, so two same-date recordings are each independently reachable.
- Provenance panel now names the exact displayed snapshot's id and recorded-at time; default-view copy reworded to "most recently recorded" instead of implying "latest date".
- Three of four ledger sections (Screen History, Top-up Runs, Index Reconciliation) now render a plain-text integrity-error note when a stored record file fails its own checksum.
- Verified J-12 passes browser QA and demo-narrator evidence (audit-repaired walkthrough: Demo Verdict RECORDED, 7/7 `[NEW]`-flagged steps); all 12 journeys re-verified passing.

## What's left

- A "Universe" ledger section named in the original plan does not exist in the frontend and was not built — there is no Universe snapshot list on `/desk` to extend, only a single id string in Provenance; a deliberate future journey would be needed if it's wanted.
- If every recorded screen snapshot were simultaneously corrupted, the Screen History integrity-error note would be hidden behind the pre-existing "not computed yet" empty state — a pre-existing property, not exercised by any test this iteration.
- One evidence screenshot (`UT-02-result.png`) briefly captured an unrelated application sharing the same browser; the audit added verified replacement captures and left the bad file in place with a written warning rather than deleting it silently.
- The earlier same-date screenshot crops just above the NFLX row goal.md names as its worked example; the coverage difference is still legible via on-screen text, and the underlying files were independently re-checked.
- Backlog, open by choice: keyboard access for the history rows, no length limit on the run tables, and the Desk page is now eight stacked sections long.

## Next step

Halt — the goal is achieved. Six follow-ups for the owner, none a defect and none blocking: (1) one picture in this run's evidence folder, `reports/qa/goal-desk-iter-16-evidence/UT-02-result.png`, is a screenshot of a completely different program — not this product at all. I opened it and confirmed it. The independent audit caught it, took its own correct pictures beside it, and left the bad one in place with a written warning rather than quietly deleting it. Nothing about the product is affected, but the picture-taking step and an unrelated program were sharing one browser, and the picture-taking step's own report said that had "no impact". That claim was wrong, and the check that would catch it should become automatic. (2) The two same-day recordings are proven different on screen, but the specific row the goal text names (Netflix's one-day badge) is only visible in one of the two pictures — the other picture stops just above that row. The difference itself is still plainly visible in that picture as the sentence "3 ranked row(s) below show every timeframe badge dark", which the other picture does not have, and I re-checked the underlying files myself: the two recordings differ on exactly four rows and Netflix's one-day badge really does flip. A single full-length re-take of the earlier view would close this; it needs no program change. (3) The checking step marked five browser test cases as passed while only reading source code. The real browser step did run the equivalents properly, and the audit ran the one that had not been run at all, so no conclusion is wrong — but "passed by reading the code" should never be accepted for a test that says "in a browser". (4) This run's own written plan asked for a damaged-file line on a fourth list ("Universe") that has never existed anywhere on the page. The development step correctly refused to invent a new section for it and said so. The goal file never asked for it either. Please have the plan text corrected rather than the section built — or decide separately that you want such a section. (5) Two small things stay open by choice, neither forced: if EVERY saved screen were damaged at once, the page would show the "nothing computed yet" panel and the screen list's own damaged-file line would be hidden exactly when it matters most; and eight regression pictures in this run are the same single image reused, so they prove the checks ran, not what each check saw. (6) Still open by choice from earlier runs: keyboard access for the history rows, the run tables have no length limit, and the Desk page is now eight stacked sections and long.

One sentence for the owner: every saved screen can now be opened by name, damaged files are named on screen instead of being dropped in silence, and this run touched none of your own data — please confirm the finish.

## Assumptions made

- iter-16 · goal-evaluator — Ambiguity: J-12's acceptance asks for a same-date pair with a differing coverage badge "legible across the screenshots," but the earlier view's only genuine capture stops above the named NFLX row, so the exact example isn't legible on both sides. We chose: read "at least one row" as the requirement (the NFLX line is an illustration, not a pinned literal), score J-12 passing, and record the framing shortfall as a capture defect (`evidence_makeup: true`) rather than an unmet clause, since the coverage difference is independently legible via on-screen text and re-derived from the stored files. Reversible: yes — one full-page re-capture closes it, no program change needed.
- iter-16 · goal-decomposer — Ambiguity: goal.md requires an honest refusal when `id` and `date` are both supplied but doesn't name the HTTP status code. We chose: leave the exact code to build discretion, requiring only an honest 4xx (422 chosen to match this router's existing FastAPI-validation convention). Reversible: yes — a later iteration can pin the exact code with zero effect on any recorded data.
- iter-15 · goal-evaluator — Ambiguity: J-11's acceptance asks for a byte-identical same-pins rank-order comparison, but no screen with identical pins exists on both sides of the change (re-running the same pins returns the already-recorded snapshot instead of recomputing). We chose: treat the clause as satisfied by an equivalent proof — unchanged rank-key code in the diff, identical ranked/skipped sequences across the two screens, and differences confined to the one field that must differ by exactly one day. Reversible: yes — a genuinely new date computed under both code paths would give the literal comparison.
- iter-15 · goal-evaluator — Ambiguity: the iteration's own plan required every lane to use a fixture-scoped rig, but the running "scoped" rig carried no environment override at all, so browser-QA and demo-narrator lanes served the real ambient store instead. We chose: record it as a disclosed process deviation (breach of this iteration's plan), not a goal.md anti-goal violation, since zero bar-series files were modified, only one derived/rebuildable snapshot and cache were written, and the trigger was an explicit POST, never a scheduler. Reversible: no — the appended snapshot is permanent by design; the real fix is a rail forcing evidence lanes onto a scoped store.
- iter-14 · goal-evaluator — Ambiguity: an earlier QA pass triggered a real coverage-index reconciliation and screen compute against the owner's ambient data store, which the phase spec put explicitly out of scope; goal.md doesn't say whether an agent-triggered run counts as an "explicit operator act." We chose: record it as a disclosed process deviation, not an anti-goal violation — no bar-series file was modified, the rebuilt index is goal.md's own "derived" accelerator, the trigger was an explicit POST, and reverting would mean deleting an append-only record. Reversible: no — the run record and new screen snapshot are permanent by design.
- iter-14 · goal-evaluator — Ambiguity: docs/goal.md's Anti-goals section carried an uncommitted reword of the host-guard paragraph this iteration, and the file doesn't record who made any given edit. We chose: treat it as owner-authored maintenance rather than a goal-proposer breach, based on file mtimes, the proposer's own result-file scope, and the reviewer's independent confirmation the wording matches an already-committed mechanism. Reversible: yes — a one-line revert with no effect on any journey if the owner did not author it.
- iter-14 · goal-decomposer — Ambiguity: goal.md's J-10 doesn't say whether the transient in-flight compute progress needs its own registered Data-Contract row, or whether a CLI warmer is required (unlike J-02/J-03). We chose: register a second, transient "compute progress" row alongside the durable run-record row, and skip a CLI warmer since the repair is a fast local no-network index rebuild that goal.md's own text never names a CLI for. Reversible: yes — a CLI warmer can be added later with zero shape change; the transient row can be folded back if judged unnecessary.
- iter-13 · goal-evaluator — Ambiguity: goal.md's J-09 acceptance requires a `[NEW]`-flagged demo-narrator walkthrough covering the top-up-run disclosure end to end, but a live demo pass can only ever render the store's current (populated) state — never both an empty and a filled state in one live pass on an append-only rig. We chose: score J-09 passing on a repaired artifact where the audit substituted a genuine same-rig, same-order empty-state frame from the dev lane's own pre-write capture, disclosed in three places. Reversible: yes — but the strict "every frame live-captured" reading would make J-09 permanently unclosable until the demo runner gains a static-frame step kind.

## Quick verify

From `reports/phase-goal-desk-iter-16-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll down to the "Screen History" panel and find the table's header row
3. In that table, find the two rows whose "date" column both read `2026-07-27` (they sit next to each other, a few rows up from the bottom)
4. Click the `2026-07-27` row with the EARLIER "recorded" time (`2026-07-27T21:42:...`)
5. Click the OTHER `2026-07-27` row (the LATER one, `2026-07-28T21:30:...`)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-16.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-16-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-desk-iter-16-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-16-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-desk-iter-16-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-desk-iter-16-user-visible-changes.md |
| What to click | — | reports/phase-goal-desk-iter-16-what-to-click.md |
| UI surface map | — | reports/phase-goal-desk-iter-16-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-desk-iter-16-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-desk-iter-16-ux-regression.md |
| QA | PASS | reports/qa/goal-desk-iter-16-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-desk-iter-16-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-desk-iter-16-closure-verdict.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-desk/iter-16/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
