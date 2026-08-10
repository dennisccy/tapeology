# Iteration Summary — goal-playbook-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-10
**Iteration:** 1

## In plain words

**What you can do now:** You can still watch a simulated ticker's live buy-and-sell pressure, load a real stock's chart with support-and-resistance walls drawn on it, and run the desk's daily screen for a ranked briefing with forward-looking return numbers — all of that keeps working exactly as before. Behind the scenes, the desk can now also spot and permanently record a stock's "opening range breakout" for any trading day it has data for, though there's no button for it yet — only someone with direct technical access can ask for it today.

**What changed this time:** Nothing changed on the pages you can already click through — Cockpit, Structure, and Desk all look and behave exactly the same. Behind the scenes, we built the first piece of a new pattern-recognition feature: the desk now watches the opening minutes of a trading session and permanently writes down every time a stock breaks cleanly out of that early range, plus an honest note whenever it doesn't have enough data to tell. This isn't shown on any screen yet — that comes in a later step.

**What's next:** Next, the desk will start measuring what price actually did after each pattern it spots, using its existing measuring rules.

## Headline

J-01 ships: opening-range breakout signals detected, recorded, and readable via a new backend endpoint (no UI yet).

## Direction

**Signal:** improving
**Why:** J-01 "The signal contract" moved from failing to passing this iteration — 43 new tests, a full suite of 1969 pass / 8 skip, and the live route independently re-verified by the evaluator — with zero other journeys newly failing or regressed. The audit caught and fixed a critical-severity honesty bug in the same cycle before anything shipped (a fabricated opening-range value on gapped sessions, now an honest disclosed absence with a permanent regression test); the evaluator's own verdict stayed CONTINUE, treating the catch as the safety net working rather than a setback. The two gaps carried forward — J-10's still-unrun browser replay and one open minor spec-completeness item — are both explicitly assigned to J-02 next.

**Trend (last 2 iters):**
- Newly passing this iter: J-01
- Newly passing in last 2 iters total: J-01
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: iter-1: 1 critical (found and fixed in-iteration, regression test added) + 1 minor (open, needs an owner ruling); iter-0: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** J-01 "The signal contract" is genuinely built and it works. The desk can now find opening-range break signals on its own recorded bars and write them down in a permanent, never-rewritten record, and a reader who asks for a session with nothing recorded gets an honest "nothing here" answer instead of an error. I did not take this from the write-ups: I ran the 43 new tests myself, ran the whole test suite myself (1969 passed, 8 skipped), asked the new address for data four different ways and read the answers, and checked with git that no protected file was touched. One serious honesty bug was found and fixed inside this same iteration by the audit step: a session missing its first few bars was being handed a made-up "opening range" that looked exactly like a real one.

## What was done

- Product changes: apps/backend/app/research/desk_playbook_features.py, apps/backend/app/research/desk_playbook_detect.py, apps/backend/app/research/desk_playbook.py, apps/backend/app/research/desk_routes.py, GET /research/desk/playbook
- Built the 8 shared primitives (opening range, baselines, swing pivots, zone touches, market context, and more) in `desk_playbook_features.py`, each attributed to its existing `desk_forward`/`levels` precedent.
- Built the `open_high_break`/`open_low_break` detector pair in `desk_playbook_detect.py` — constant-free, lookahead-clean (new generic property test), never imports `setups.py`/`backtests.py`.
- Built `desk_playbook.py`: ~40 spec constants, `playbook_parameters()`/`compute_playbook_input_signature()`, and an append-only `PlaybookStore` (no update/delete method) plus `compute_playbook()`'s session walk with honest per-symbol absences.
- Wired `GET /research/desk/playbook` (`?date=`/`?id=`, honest-empty, never 404) into `desk_routes.py` — the only change to that shared file.
- Added 42 new tests (full suite 1968 pass / 8 skip pre-audit, 1969/8 after the audit's own added test); `Config().config_fingerprint()` unchanged (`08e471b10130e1e2`); zero diff to `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`apps/frontend/`.
- Audit found and fixed a critical honesty bug in the same iteration: the 5m opening-range fallback was building a fabricated range from bars outside the opening window on gapped sessions; it now records an honest disclosed absence instead, with a regression test.

## What's left

- Journey J-02 (Every signal measured — the rail's own conventions, anchored at the trigger bar) failing — targeted next.
- Journey J-03 (The Playbook lands on /desk) failing — no UI surface exists yet.
- Journey J-04 (The continuation family — JBE, DBI, cup-and-handle) failing.
- Journey J-05 (The climax family — capitulation entry, euphoria marker) failing.
- Journey J-06 (The range family — range trades, double top/bottom) failing.
- Journey J-07 (The back-scan — every recorded session, resumable and append-only) failing.
- Journey J-08 (The evidence view — distributions beside the null, min-n honest) failing.
- Journey J-09 (MCP contract v4 — 20 read-only tools) failing — MCP is still at 18 tools.
- Journey J-10 (The kept product stands — regression sentinel) still partial — this iteration's required golden-script replay (`journey-scripts/J-10.json`) was not run; must be requested explicitly next time or it will be skipped again.
- Two owner rulings needed in `docs/playbook-detector-spec.md` before J-08 (what "P4" mechanically means for an opening-range break; whether the opening-range 10-bar threshold belongs in the spec's own constants table), plus three test-debt gaps the audit named (end-to-end tests for the 5-minute-fallback case and the both-sides-break case, and one detector fixture with a populated market index).

## Next step

Build J-02 "Every signal measured" next, at full depth — the step that measures what price did after each signal, reusing the desk's existing measuring rules rather than a second copy of them. Three pieces of carried work should ride along inside J-02's own cycle rather than becoming their own iteration: (1) run the J-10 browser replay (`journey-scripts/J-10.json`) as soon as the next iteration brings the app up — it has now been skipped once and must be asked for explicitly or it will be skipped again; (2) close the three test gaps the audit named — one end-to-end test each for the 5-minute-fallback case and the both-sides-break case, plus one test where the market index actually has bars; (3) get two owner rulings written into `docs/playbook-detector-spec.md` before J-08 — what "P4" means for an opening-range break, and whether the 10-bar threshold belongs in the spec's own constants table. Also: commit iteration 1's seven files before the next iteration starts, so the next diff isn't blamed on iteration 2.

## Assumptions made

- iter-1 · goal-evaluator — Ambiguity: `docs/goal.md` marks "No threshold exists outside the spec" as critical, but `desk_playbook_detect.py:276` settles a spec rule (§3.1's "P4" principle) in code without inventing a threshold or a sweep; the auditor was genuinely unsure between GAP and IMPORTANT, and critical severity would force a REGRESSION halt. We chose: minor, not critical — nothing is fabricated, no threshold invented, no sweep exists, and the field is a disclosure label gating no computation; recorded as an open minor violation needing an owner ruling in `docs/playbook-detector-spec.md` before J-08 groups evidence by principle. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-10's required verification (TC-14, the golden-script replay) was executed by nobody this iteration, and the auditor recommended recording J-10 as `unknown-by-replay`; the goal never says whether a sentinel journey keeps its status when the iteration provably touches none of its surfaces. We chose: kept J-10 at `partial` (its prior status) under the evidence-durability rule — the frontend diff is empty and the only shipped-file change is `desk_routes.py` at +75/-0 inside one new block, so iter-0's screenshots still show the current product; the un-run replay is recorded as an explicit gap demanded of the next iteration. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10's acceptance text bundles kept-product behaviour with a clause ("MCP = exactly 20 tools") that only becomes true at the end of the era, and the goal never says how to score J-10 mid-flight. We chose: `partial` — the kept half is fully evidenced (screenshots, suite 1926/8, fingerprint `08e471b10130e1e2`), while the 20-tool clause is recorded as not-yet-satisfiable rather than a failure of the kept product, mirroring how the previous era's baseline scored its own sentinel journey. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-playbook-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-playbook-iter-1-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-playbook-iter-1-review.md |
| Browser QA | SKIPPED | reports/phase-goal-playbook-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-playbook-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-playbook-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-playbook-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-playbook-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-playbook-iter-1-ui-test-plan.md |
| QA | PASS | reports/qa/goal-playbook-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-playbook-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-playbook-iter-1-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-playbook/iter-1/eval.md |
| Journey history | — | runs/goal-session-playbook/state/journey-history.json |
