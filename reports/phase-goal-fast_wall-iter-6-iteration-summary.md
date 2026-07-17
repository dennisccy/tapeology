# Iteration Summary — goal-fast_wall-iter-6

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 6

## In plain words

**What you can do now:** You can open the cockpit and watch simulated buyer/seller tape scenarios settle, save your trade thinking to a journal and review it later, browse replay studies, and check a performance ledger of simulated results. On the structure page, the price-level map and case studies list always load quickly and safely — even right after the app restarts — the page is honest if the deeper price-comparison report hasn't been calculated yet instead of hanging, and you can click "Compute edge report" to run that calculation yourself and watch it progress to a finished result or an honest error message.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The case-studies scan on the structure page now remembers its results to disk, so if the app's server ever restarts, that part of the page comes back up to speed almost instantly instead of forcing a slow rescan. This was the last piece of this round of speed-and-reliability work — every planned improvement is now built and double-checked.

**What's next:** This round of work ("The Fast Wall") is done — the team is confirming it's genuinely complete, and after that plans to run the full real-market price-comparison calculation for the first time.

## Headline

Durable setups scan cache (J-06) lands — all 7 Must-have journeys now passing; GOAL_ACHIEVED

## Direction

**Signal:** improving
**Why:** J-06 (the durable setups scan cache) flipped from failing to passing this iteration, closing the interlude's seventh and final Must-have journey — full suite grew to 1544 tests (27 net-new), both frozen source-introspection guards and the config fingerprint held byte-unmodified, and J-01–J-05/J-07 all re-verified regression-clean. With every Must-have journey now passing and zero anti-goal violations across the session, the evaluator declared GOAL_ACHIEVED — the first of the two-key confirm, the strongest possible directional signal this session can produce.

**Trend (last 5 iters):**
- Newly passing this iter: J-06
- Newly passing in last 5 iters total: J-02, J-03, J-04, J-05, J-06
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-06 ("Restarts stop hurting — the durable setups scan cache"), the seventh and final Must-have journey of "The Fast Wall" interlude, landed cleanly: `compute_setups` gained a durable, restart-surviving SQLite tier keyed on config CONTENT (not the fragile `id(config)`), byte-identically. With J-01–J-05 and J-07 already `passing` and re-verified this iteration, all 7 Must-have journeys are now `passing` with positive, personally-opened evidence; scan is CLEAN, coherence is COHERENCE-PASS, no anti-goal is violated, and no goal-edit drift exists. Per the decision tree (rule 3) this is GOAL_ACHIEVED — the first key; the outer loop's deterministic gates + fresh-context confirm are the second.

## What was done

- Built a durable, restart-surviving SQLite cache (`SetupsScanCache`) for `compute_setups`'s multi-minute full-panel touch-event scan (feeds the Case Studies panel and `/studies`) — a backend restart no longer forces a full rescan.
- Replaced the fragile `id(config)` cache key with a config-content hash, so the cache recognizes "the same settings and data," not just "the same object still sitting in memory."
- Refreshed stale module documentation describing the new two-tier (in-memory hot slot + durable) caching reality.
- Added 27 net-new tests, including a non-vacuous mutation-probe proving the durable-hit code path is genuinely read, not dead code; full suite now 1544 passed / 7 skipped / 0 failed.
- Re-verified all 6 previously-passing journeys (J-01–J-05, J-07) regression-clean; both frozen source-introspection guards, the MCP 18-tool count, and `config_fingerprint` (`4d665603569b9dbf`) all held byte-unmodified.
- Verified 1 target journey (J-06) pass browser QA — a full `/structure` regression pass found zero loading panels and zero visual diff vs iter-5.

## What's left

- All Must-have journeys passing, no closure blockers.

## Next step

Halt — GOAL_ACHIEVED. All 7 Must-have journeys of "The Fast Wall" interlude are passing. The interlude's deliverables are complete: `/structure` never computes on load (J-01), the stores stop re-reading with durable caches + dataset index (J-02), the arm memo collapses per-tick recomputes (J-03), the operator-run compute (button + background job + CLI warmer) works (J-04), the sweep is resumable + parallel (J-05), the setups scan cache survives restarts (J-06), and the era-1–5B foundation is byte-identical (J-07, fingerprint frozen).

One cosmetic non-blocker for whenever `test_setups.py` is next edited for a substantive reason (do NOT reopen this iteration for it): the stale `id(config)` docstring aside at `test_setups.py:1027` (flagged MINOR by review, OBSERVATION by audit, already deferred by both). It affects no journey and no anti-goal. The operator-only real-corpus "restart → `/structure` ready within 10s" figure remains tagged *(operator-verified on the real corpus)* in goal.md — gather as bonus evidence if/when a credentialed real-corpus run happens; correctly excluded from this iteration's Definition of Done.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: J-04's acceptance names a browser-verified "button → progress → terminal-state" cycle, but both committed keyless fixtures resolve 0 eligible pairs, so no captured evidence shows a live nonzero progress tick or the "(N from cache)" annotation. We chose: score J-04 `passing` (flip from iter-4's `partial`) since the earlier blocker was strictly "no screenshot," now resolved with real screenshots of the button, click-through, failed state, and warm reload; the one unshown sub-leg is fixture-bound and proven non-vacuously at the pytest level. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: goal.md says parallelism runs "ONLY in the CLI/background job — never inside a request thread," but never states whether the compute manager's own background thread counts as an allowed home for process-pool parallelism. We chose: wire resumability into both the CLI warmer and the button's compute manager, but keep genuine multi-worker parallelism CLI-only — the manager never passes `workers` above 1, keeping multiprocessing out of the always-on backend process. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-01 and J-07 share this iteration's touched page and the browser lane was expected to re-verify their visual legs, but Chrome MCP was down and `structure/page.tsx` was actually modified that time. We chose: keep J-01 and J-07 `passing` on a mechanical + traced-additive-diff argument (backend files byte-unchanged, full suite green, fingerprint frozen, page change strictly additive) rather than downgrading to `unknown`. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-04 requires a browser-verified click-through, but Chrome MCP would not start (reproduced by 4 agents), while every keyless clause was fully proven by 121 targeted tests plus audit-run CLI and curl. We chose: score J-04 `partial` — not `passing` (no screenshot) and not `unknown` (extensively tested and passing on its backend/API/CLI assertions). Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: J-04's acceptance names no concrete wall-clock ceiling for the browser click-to-terminal-render cycle or the CLI's warm-key repeat speedup. We chose: pin two generous ceilings on the tiny fixture (90s browser cycle, 5s warm-key CLI repeat) — clearly satisfiable and diagnostic of a regression, not the real proof itself. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: goal.md names all five keyword-only hooks as J-04's own signature addition, but the work giving `sub_cache=`/`workers=` real parallel effect is explicitly J-05's step. We chose: J-04 adds all five parameters (and the CLI's `--workers N` flag) so the shape is complete from day one, but they stay accepted-and-inert until J-05 makes them real. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: this was the first iteration to modify the canonical owners behind a passing browser journey's UI (`levels.py`/`tradability.py` back J-07) while running `Frontend Present: no`, so J-07's pass had no fresh screenshot. We chose: score J-07 (and J-01/J-02) `passing` on a mechanical byte-identity non-regression argument rather than downgrading to `unknown`. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: J-03's acceptance says the fixture backtests complete "within an interactive test budget" but names no concrete number. We chose: pin a generous 10-second wall-clock ceiling on a fixture crossing 5+ distinct level-change intervals; the real proof is the counting-spy call-count collapse, not the wall-clock number. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the stable-journey re-verification model assumes the golden-replay lane runs for J-01/J-07 each iteration, but this backend-only iteration skipped browser-qa entirely. We chose: score J-01 and J-07 `passing` on a mechanical non-regression argument (served bytes proven unchanged) rather than downgrading to `unknown`. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the iteration spec's prose said both `detail` AND `dataset_count` "become newly visible" in the not-computed panel, but the shipped panel renders only the headline + `detail`. We chose: score J-01 `passing` by treating the goal.md acceptance + TC-11 (headline + verbatim detail only) as authoritative over the stronger spec prose. Reversible: yes

## Quick verify

From `reports/phase-goal-fast_wall-iter-6-what-to-click.md`:

1. Open `http://localhost:3391/structure` in your browser
2. Wait 10 seconds without clicking anything, then look at every panel on the page
3. Scroll down to the **"Case Studies"** panel
4. Scroll down to the **"Edge Report"** panel — do **not** click its button
5. Keep scrolling to the **"Registry"** panel

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-6-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-fast_wall-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-fast_wall-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-6-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-6-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-6-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-fast_wall-iter-6-ux-regression.md |
| QA | PASS | reports/qa/goal-fast_wall-iter-6-qa.md |
| Audit | PASS | docs/handoffs/goal-fast_wall-iter-6-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-fast_wall-iter-6-closure-verdict.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-fast_wall/iter-6/eval.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
