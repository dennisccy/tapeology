# Iteration Summary — goal-rapid-microscope-iter-7

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-18
**Iteration:** 7

## In plain words

**What you can do now:** On the Desk page, you can see a panel that honestly reports how much detailed tick-by-tick market data the product has on file. Behind the scenes, it also reads buying and selling pressure tick by tick, connects chart-pattern signals to that activity, and keeps a permanent, tamper-proof record of every trading idea it tests — successes and failures alike. It can now honestly say "not enough data yet" when checking whether a result is trustworthy, instead of guessing or staying silent.

**What changed this time:** Behind the scenes, the way trading data gets saved was strengthened: it can now safely carry a few extra details about each trade without breaking anything already on file. A routine safety check also caught and fixed a subtle bug the same day, before it touched anything real — it could have let the same recorded data be filed twice under conflicting labels. Nothing new appeared on any screen this round; the Desk page's data panel and every other screen look exactly the same as before.

**What's next:** Next, the team will build the tool that actually records fresh, never-before-seen market data — with the same careful safety check that just caught this round's bug.

## Headline

Trade/quote preservation fields added as storage capability (J-06 step 1, no consumer yet)

## Direction

**Signal:** improving
**Why:** J-05 flipped partial → passing this iteration once the CLI `--family tick_legacy` refusal was proven live against the real store, ending a three-iteration ESCALATE streak with a CONTINUE. J-06 moved failing → partial (step 1 of 5) while the independent auditor caught and fixed a critical anti-goal violation — the new preservation fields had silently defeated the frozen-split guard — before it could ship, the fourth time this session only the auditor caught an integrity fault review/QA missed. J-01–J-04 all re-verified passing against real data with 0 regressions, so the session reads improving despite J-06 and J-10 still being partial.

**Trend (last 5 iters):**
- Newly passing this iter: J-05
- Newly passing in last 5 iters total: J-03, J-04, J-05
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 7 critical (iter-4: 3, iter-5: 3, iter-7: 1 — all introduced and fixed within the same run, 0 left unresolved); several minor items opened and/or closed most iters (see journey notes)
- Iters with no journey state change: 1 of last 5 (iter-6)

**Latest evaluator reasoning:** "Two things were built and both hold up when checked. The walk-forward engine (J-05) is now finished: there is a real command an operator can run that answers 'you only have 11 days of tape, you need 105' and stops — the exact sentence the goal asks for, which until now only a test could produce. One dangerous fault was introduced and fixed inside this same run: the new details quietly changed how a recording's identity is calculated, which would have let the same tape be filed twice under two different labels. I broke it again myself and confirmed the repair holds."

## What was done

- Product changes: apps/backend/app/providers/adapters/base.py, apps/backend/app/providers/base.py, apps/backend/app/providers/historical.py, apps/backend/app/providers/adapters/alpaca.py, apps/backend/app/research/datasets.py, apps/backend/app/research/walkforward.py
- Threaded optional Card-5.1 "preservation" fields (conditions, exchange, tape, trade_id + quote equivalents) additively through the adapter → provider → engine event → stored-row pipeline (J-06 step 1); absent-key default keeps all 18 real datasets and every fixture byte-identical.
- Added optional `schema_basis`/`quote_size_unit` stamp capability to `DatasetStore.record()`/`record_from_source()` — storage-only, no caller supplies it yet.
- Shipped a new CLI `--family tick_legacy` flag on `python -m app.research.walkforward` that checks the real 11-day tick corpus against the 105-session floor and prints the typed refusal "11 < 105" — closes J-05's last acceptance gap through a genuine production entry point.
- Independent audit found and fixed a CRITICAL anti-goal violation introduced in-run: the new preservation fields had entered the dataset content checksum, defeating the "splits frozen at registration" guard — fixed via a tape-only hashing projection plus a new regression test.
- Re-ran the full backend suite (3045 pass / 8 skip / 0 fail, +7 over the iteration-6 baseline) and independently re-verified all 18 real datasets plus 9,145,900 events load byte-identically; fingerprint `08e471b10130e1e2` and all six `referee_*.py` hashes unchanged.
- Verified 2 target journeys pass browser QA (J-01 Microscope Readiness regression, J-10 kept-product sentinel) — 9/9 browser test rows PASS.

## What's left

- Journey J-06 (The recorder and the Vault — new tape, sealed at birth) partial — only step 1 of 5 landed, and even step 1 is missing the §2.6 dated-vendor-rule stamping; `tick_recorder.py`, `vault.py`, universe registration, and any real Alpaca tranche recording remain unbuilt.
- Journey J-10 (The kept product stands — traps armed, sentinel green) partial — sentinel green for a second straight iteration, but the full TR-1…TR-22 trap suite is still short (TR-2/4/12/19/20/22 have no dedicated test).
- Journey J-07 (Graduation — provenance in, nothing laundered out) failing — `micro_graduation.py` does not exist on disk.
- Journey J-08 (The surface and MCP v6 — the funnel is visible) failing — no Scout Ledger/Walk-Forward/Validation Vault UI section exists yet; MCP surface still 22 tools, not the target 26.
- Journey J-09 (The pilot studies — three predeclared questions, honest answers) failing — all three predeclared study floors still read `floor_unmet` at 11/60 sessions.
- New minor item (open): the tick-family CLI writes its permanent fold-spec record before checking the size floor, which will freeze today's 11-day geometry forever once the corpus grows — must fix before J-06 records new tape.
- Two owner rulings are still outstanding: whether the one-quote-early depletion timing stamp should be corrected, and whether the Microscope Readiness photograph must show the real 12-day corpus (the store-scoped test rig can only ever seed 2 fixtures).
- No live credentialed Alpaca fetch was run to prove real `conditions`/`exchange` values populate from a genuine SDK response — hermetic verification only, disclosed as non-blocking.

## Next step

Build the tape recorder next — step 2 of J-06 "The recorder and the Vault" — on its own, under the full pipeline with the independent checker kept in the loop. That checker has now been the only step in this session to catch a serious honesty or data-integrity fault four separate times, including this run's. Do not shorten it for time.

Carry five small items with it, all of which only start to hurt once new tape exists:

1. Make the new tick command check the size floor BEFORE it writes its permanent shape record. Today it writes first, which locks in today's 11 days and today's fold shape forever.
2. Make a recording that carries the new extra details safe to use as a lookup key. The extra details are stored as a list, and the program will raise an error if anything tries to use such a record as a dictionary key — this can only happen on newly recorded tape.
3. Report a damaged recording instead of quietly leaving it out of the list of known days.
4. Word the "request complete" message honestly — today it would say a fold build finished when no fold was built. It is unreachable now and becomes reachable the moment the corpus grows.
5. Ask a framework-maintenance session (outside this loop) to look at two harness problems: the report merger that reads a bold **FAIL** as no verdict, and whatever deleted the screenshots two lanes cited this run.

Two decisions are still waiting on you and neither can be made by a coder: whether the timing stamp that is one quote too early should be corrected, and whether the corpus-truth photograph must show your real 12-day corpus when the test rig can only ever show a two-day one. Please answer both before new tape is recorded, since the recorder is what makes them matter.

## Assumptions made

- iter-7 · goal-decomposer — Ambiguity: goal.md J-06 step 1 requires both the Card-5.1 preservation fields and the §2.6 `schema_basis`/`quote_size_unit` stamping, but the codebase's own docstring reserves the dated-vendor-rule constant for `tick_recorder.py` (not yet built) — unclear if step 1 must implement the date-to-unit rule or just the storage capability. We chose: storage capability only — `DatasetStore.record()` gains optional `schema_basis`/`quote_size_unit` kwargs, persisted only when supplied; the dated-rule decision stays deferred to `tick_recorder.py`. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: goal.md J-05's acceptance doesn't say which caller (the `POST /walkforward/compute` route, the CLI, or both) must carry the tick-family fold request. We chose: CLI only, mirroring the CLI's established "operator's real run" role; the route's family parameter is deferred until a UI/MCP consumer needs it. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: J-05's acceptance names the "11 < 105" typed refusal without saying whether a CLI-only entry point discharges the clause or a route is required. We chose: CLI-only discharges it — scored J-05 `passing` after re-running the command myself against the real store and getting the exact refusal, exit code 1, with the real ledger untouched before and after. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: J-06 has five steps and this iteration delivered only part of step 1 (the `schema_basis`/`quote_size_unit` stamping was explicitly deferred) — unclear whether ~1/5 of a journey qualifies as `partial` or should stay `failing`. We chose: `partial`, since one acceptance clause is genuinely met and proven myself; the journey notes state the fraction explicitly ("1 of 5 steps, and that step only in part") so it doesn't read as "nearly done". Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: unclear whether this iteration must build a new corpus-selectable entry point to make the tick-family fold request reachable, or may wire the guard defensively into the existing single fold-building call site. We chose: wire `require_sufficient_sessions_for_folds` into the existing (and only) fold-building call site in `run_diagnostic_walkforward`, guarding every corpus it ever builds folds for, rather than inventing a new route. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: spec says the exposure registry must pre-mark "the 12 legacy tick symbol-days" as exposed, but not which module resolves that set or whether it's a frozen list versus whatever the tick `DatasetStore` currently holds. We chose: resolve it dynamically at seed time from the same `DatasetStore` listing `micro_readiness.py` already reads, since — before J-06 ships new datasets — "every currently registered dataset" and "the 12 legacy symbol-days" are the same set. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: unclear whether J-05's tick-family fold request acceptance clause is discharged by a guard live on the one production fold path (always the playbook corpus) plus a synthetic unit test, or requires a production path that can actually point the fold engine at the tick corpus. We chose: the stricter reading — scored J-05 `partial`, not `passing`, since `app/` contained exactly one `build_folds` call site and it was hardcoded to the playbook corpus; the "11 < 105" string appeared only in a synthetic-date unit test. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: methodology says the evidence-makeup flag clears once a fresh capture lands "whatever the outcome," but that iteration's fresh Microscope Readiness capture reproduced the same defect (rig-seeded 1/2 corpus, not the real 12/18) rather than fixing it — unclear what to do when a retake can't actually fix the underlying rig limitation. We chose: cleared the flag and kept J-01 `passing`, recording the residual as an owner ruling instead of scheduling an impossible future retake, since the rig structurally cannot show the real corpus. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-05's acceptance sentence names five things at once, two of which were met only at the library level, not at any production entry point (the exposure registry's tick-window initialization and the typed "11 < 105" floor-refusal) — unclear whether a passing test is enough or the protection must be wired into the running product. We chose: the stricter reading — scored J-05 `partial` rather than `passing`, with both gaps named and evidence produced directly (154 registry rows all playbook-keyed; zero call sites for the floor-refusal function in `app/`). Reversible: yes

## Quick verify

From `reports/phase-goal-rapid-microscope-iter-7-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll to the very bottom of the page and click the "Microscope Readiness" section header
3. Open `http://localhost:3301/` (the cockpit page)
4. Type `SIM-BUYER` into the field labeled "Ticker", then click the "Watch" button
5. Open `http://localhost:3301/structure`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-7.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-7-dev.md |
| Review | PASS | reports/reviews/goal-rapid-microscope-iter-7-review.md |
| Browser QA | PASS | reports/phase-goal-rapid-microscope-iter-7-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-7-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-7-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-7-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-7-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-7-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-rapid-microscope-iter-7-ux-regression.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-7-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-7-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-7-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-rapid-microscope/iter-7/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
