# Iteration Summary — goal-fast_wall-iter-4

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 4

## In plain words

**What you can do now:** You can open the cockpit and watch simulated buyer/seller tape scenarios settle, save your trade thinking to a journal and review it later, browse replay studies of past tape readings, check a performance ledger of simulated (not real) results, and view the structure page's price-level map and case studies. The structure page's price-report area is still always safe to open — it never risks starting a giant background calculation, and if a report genuinely hasn't been calculated yet, the page tells you so plainly.

**What changed this time:** The team built a "Compute edge report" button on the structure page, plus a background job and a companion command-line tool, so someone could trigger the full price-report calculation themselves for the first time — watch it progress, and see it finish or fail honestly. Everything behind the button was tested directly and works correctly, but the actual on-screen check of clicking the button and watching it work could not be completed this round because of a browser-testing tool problem — so this new button isn't confirmed to look and behave correctly on screen yet, and this round is being held back from being marked fully done until that check happens.

**What's next:** Next, the team will re-run the visual check of the new "Compute edge report" button in a working browser session, and once that's confirmed, move on to making the calculation resumable and able to use several processor cores at once.

## Headline

Compute edge report button built and backend-verified; Chrome MCP outage blocked browser QA — closure FAIL.

## Direction

**Signal:** holding
**Why:** This iter built J-04 in full — the single-flight/cancel/force/progress/failed-state compute manager, three REST routes, CLI warmer, and the `/structure` button — with strong, independently-verified backend evidence (121 targeted tests, non-vacuous hook proofs TC-14a/TC-14b, zero anti-goal violations) from review, QA, and a hard audit. Closure FAILed anyway because the mandatory browser click-through (TC-15/TC-16) never ran — Chrome MCP would not start for four independent agents this iteration — so J-04 stays `failing` in journey-history pending a real screenshot. No regression occurred (J-01/J-02/J-03/J-07 all intact; the one flagged J-07 golden-replay FAIL traces to a backend-unreachable-at-replay-time false positive) and no anti-goal was violated, so this reads as a one-iteration, environment-driven pause — the fix is a clean-session browser-QA retry, not further code work — rather than a genuine stall or reversal.

**Trend (last 4 iters):**
- Newly passing this iter: none (the evaluator did not run this iteration — closure blocked before evaluation; J-04 is built and backend-verified but its browser leg is unconfirmed)
- Newly passing in last 4 iters total: J-07 (iter-0), J-01 (iter-1), J-02 (iter-2), J-03 (iter-3)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4 (iterations 0-3 each moved exactly one journey to passing; iter-4's own evaluation is pending the browser-QA remediation described above)

**Latest evaluator reasoning:** (most recent available — iter-4's own evaluator never ran because closure blocked first; this is verbatim from the iter-3 log entry) "J-03 verified passing on strong, triangulated, personally-opened evidence. Review PASS, QA PASS (15/15 TCs), and a hard skeptical audit PASS that ran a mutation probe proving the byte-identity tests genuinely bite (a stale-serving memo yields 0 trades where the correct memo yields 1 — TC-7/TC-8 non-vacuous). Not GOAL_ACHIEVED (J-04–J-06 failing by design); not REGRESSION (no prior pass lost, no anti-goal violation); not STALLED (J-04 tractable, keyless-on-fixtures); not ESCALATE (full mode already, review PASS, no fail-open, no cross-cutting ambiguity)."

## What was done

- Built `EdgeReportComputeManager` (`apps/backend/app/research/edge_report_compute.py`, new) — single-flight compute job, cooperative cancel, atomically-published progress snapshot, plus a CLI warmer (`python -m app.research.edge_report_compute`).
- Added 5 additive keyword-only hooks (`force`, `progress`, `should_abort`, `sub_cache`, `workers`) to `run_strategy_comparison_report`; proved byte-identical to the pre-J-04 default path when unused (TC-14a) and genuinely wired — not decorative — when `should_abort` fires (TC-14b).
- Added three REST routes (`POST`/`GET /research/edge-report/compute`, `POST .../cancel`) and rewired `peek_strategy_comparison_report`'s `compute` field to the manager's live snapshot; zero new MCP tool (still 18, `test_advertised_tool_set_is_exactly_capability_6` unmodified).
- Wired `/structure`'s `NotComputedPanel` with a "Compute edge report" button, live progress line, and a verbatim failed-state error render, reusing existing visual language (zero new Tailwind classes/colors).
- Full backend suite: 1482 passed / 7 skipped / 0 failed (42 net-new tests); `config_fingerprint` unchanged at `4d665603569b9dbf`; zero diff on every file the spec pins byte-untouched (`levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `edge_report_cache.py` method bodies, `mcp/__init__.py`, `config.py`).
- Review PASS_WITH_NOTES, QA PASS_WITH_NOTES, audit PASS_WITH_GAPS — all three independently confirm the manager/hooks/routes are correct on direct source inspection, converging on the same single gap.
- Verified 0 target journeys via browser QA this iteration — Chrome MCP failed to start for four independent agents (developer, the QA/browser-qa merge, ux-regression, and the closure auditor's own reproduction attempt), all hitting the identical "Chrome did not become ready on port 9222" error; all 15 browser-tagged rows in `ui-test-results.md` are SKIPPED with zero screenshots.
- Closure verdict: CLOSURE-FAIL — J-04's mandatory browser evidence (Definition of Done #1, TC-15/TC-16) is unmet; every other gate (review, QA, audit, code scope, anti-goals, regression sentinel) passed.

## What's left

- Journey J-04 (The operator-run compute — button, background job, CLI warmer) unresolved — code is built and strongly backend-verified, but journey-history still records it `failing` pending a genuine browser pass (this project's own "no screenshot ⇒ unknown, never passing" discipline).
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing — not started; depends on J-04's manager/hook plumbing.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — not started; unblocked by J-02's `BarStore.root` but deliberately deferred.
- Closure blocker: no browser-executed verification exists anywhere in this iteration's pipeline for TC-15/TC-16 (J-04's compute lifecycle + failed-state render) or the J-01/J-07 regression legs (TC-17/TC-18) — remediation is a clean-session Chrome MCP retry against the scoped fixture backend, not a code change.
- Cancelling a running compute has no UI button yet — `POST /research/edge-report/compute/cancel` and `cancelEdgeReportCompute()` are implemented and tested, but nothing on `/structure` calls them this iteration (deliberately out of scope).
- Forcing a fresh recompute over an already-warm result has no UI control — the backend route and CLI `--force` flag both support it, but the browser button always sends `force: false`.
- The "(N from cache)" progress annotation is wired but will always read `0` until J-05 adds per-pair sub-caching.
- The J-07 golden-replay sentinel flagged a "possible regression" (`buyer_control` text missing) that ux-regression traced to a likely backend-unreachable-at-replay-time false positive, not a genuine product regression — needs one clean re-run to close out rather than being carried forward silently.

## Next step

Retry Chrome MCP in a fresh session — the failure is documented as session/environment-scoped (a manually-launched Chrome worked fine on the same machine across three independent agents' diagnoses) — then bring up the scoped backend/frontend pair exactly per `reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s setup recipe (port 8391 backend pointed at the `datasets_j03` fixture, port 3391 frontend) and re-run browser QA covering at minimum UT-01/UT-02/UT-05 (TC-15/TC-16) plus the J-01/J-07 regression checks (UT-09/UT-10), capturing real screenshots under `reports/qa/goal-fast_wall-iter-4-evidence/`. Update `ui-test-results.md` with the real outcomes, re-run `ux-regression-phase.sh` and phase closure, and once J-04's browser evidence exists, proceed to J-05 ("The sweep becomes resumable and parallel") per goal.md's dependency order.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-fast_wall-iter-4-what-to-click.md`:

1. Open `http://localhost:3391/structure` in your browser
2. Scroll down past "Tradable Map" and "Case Studies" to the "Edge Report" panel
3. Click the "Compute edge report" button
4. Wait up to 90 seconds without clicking anything else
5. Refresh the page (press F5 or Cmd+R)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-4-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-fast_wall-iter-4-review.md |
| Browser QA | SKIPPED | reports/phase-goal-fast_wall-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-4-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-4-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-4-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-fast_wall-iter-4-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-fast_wall-iter-4-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-fast_wall-iter-4-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-fast_wall-iter-4-closure-verdict.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
