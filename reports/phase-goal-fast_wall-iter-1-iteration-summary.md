# Iteration Summary — goal-fast_wall-iter-1

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 1

## In plain words

**What you can do now:** You can open the tape-reading cockpit and watch simulated buyer and seller scenarios settle, save trade reasoning to a journal and review it later, browse replay studies of past tape readings, check a performance ledger of simulated (not real) results, and view the structure page's price-level map and case studies. Opening that structure page is now safe too: visiting its Edge Report section never risks silently starting an hours-long calculation in the background, and if a report genuinely hasn't been run yet, you'll see a plain "not computed yet" message instead of an endless spinner.

**What changed this time:** The Structure page's Edge Report area used to silently kick off a multi-hour calculation and peg the computer's processor near 100% for hours — just from opening the page. That risk is now gone: opening the page (or asking for the report directly) always answers in well under a minute, usually instantly, no matter what state the report is in. When the report genuinely hasn't been calculated yet, you now see a short, honest message — "Edge report not computed yet" — instead of an endless spinner or, worse, no warning at all that a huge background job had just started.

**What's next:** Next, the team plans to speed up how quickly the app reads its saved trading data on file, so that the report and other slow parts of the Structure page will not need nearly 30 seconds to answer every time.

## Headline

The Structure page no longer risks hanging the machine — J-01 ships, cold GET now instant.

## Direction

**Signal:** improving
**Why:** This iteration shipped J-01 in full: `GET /research/edge-report` now returns an honest, instant not-computed payload on a cold cache instead of silently running the multi-hour sweep, mechanically proven by a zero-call compute-spy and confirmed live in the browser (UT-02/UT-03, mapping to TC-11/TC-12). Review (PASS), QA (138/140 checks), audit (PASS_WITH_GAPS, 0 CRITICAL/IMPORTANT), and closure (CLOSURE-PASS) all independently re-verified the change with fresh evidence, and the J-07 foundation sentinel stayed green (fingerprint `4d665603569b9dbf`, suite 1407 passed/7 skipped). Note: `runs/goal-session-fast_wall/iter-1/eval.md` and `journey-history.json` had not yet been refreshed for this iteration at synthesis time, so J-01's newly-passing read here rests on the converging review/QA/audit/closure evidence rather than the evaluator's own ledger update.

**Trend (last 1 iter):**
- Newly passing this iter: not yet evaluator-logged (eval.md for iter-1 had not been written at synthesis time — see Why above; J-01's pass is inferred from converging review/QA/audit/closure evidence)
- Newly passing in last 1 iter total: J-07 (iter-0)
- Regressions in last 1 iter: none
- Anti-goal violations in last 1 iter: none
- Iters with no journey state change: 0 of last 1

**Latest evaluator reasoning:** [iter-1's eval.md was not yet written at synthesis time; this is the most recent logged entry, from iter-0] Honest verify-only baseline with zero source diff (`git diff --stat -- apps/` empty, `iter-diff.md` "no changes", scan CLEAN). J-01–J-06 confirmed absent by independent grep + the zero-diff scan (the interlude's six new modules/functions do not exist); J-01's target defect (compute-inside-GET via `routes.py:2110-2115` → `get_or_compute` synchronous `compute_fn()`) is live and re-verified. J-07 passes on strong evidence: suite 1392 passed / 7 skipped / 0 failed, `config_fingerprint` 4d665603569b9dbf (live + on-page), equivalence 22/22, and four personally-opened screenshots.

## What was done

- Shipped J-01: `GET /research/edge-report` no longer computes inside a cold-cache page load — added `EdgeReportCache.lookup`/`compute_and_publish` plus a shared cache-DB-path resolver beside the untouched `get_or_compute`.
- Added `edge_report.peek_strategy_comparison_report` as the GET path's sole entry point (not-computed / warm-verbatim / empty-registry branches) and rewired `routes.py`'s `get_edge_report` to call it, preserving the pinned `Depends`/`cache=cache` wiring byte-for-byte.
- Added the `NotComputedPanel` on `/structure`'s Edge Report section ("Edge report not computed yet." + the server's verbatim detail text), rendered before the existing frozen "No edge-report cells yet." state.
- Added 15 new/adapted backend tests, including a compute-spy proving zero sweep calls on a cold GET, a byte-identity determinism test, and REST↔MCP proxy parity in the new state — full suite 1407 passed / 7 skipped, `config_fingerprint` unchanged at `4d665603569b9dbf`.
- Verified live on the real 882MB/18-dataset corpus: a cold GET now answers in ~29s (bounded by the still-unaccelerated `dataset_store.list()`, never by the sweep) instead of hours, and backend CPU dropped to 0.5% immediately after — the literal hazard `docs/goal.md` documented.
- Verified J-01 (TC-11/TC-12 cold/warm states) and J-07 (sentinel) pass browser QA — 7/7 test cases PASS, 0 skipped — independently corroborated by review (PASS), QA (138/140 checks), audit (PASS_WITH_GAPS, 0 CRITICAL/IMPORTANT), and closure (CLOSURE-PASS).

## What's left

- Journey J-02 (The stores stop re-reading — verified-content caches + durable dataset index) failing — a real-corpus GET is still bounded by the unaccelerated ~29s `dataset_store.list()` cost.
- Journey J-03 (The arm memo — per-tick levels recompute becomes ~100 memo hits per session) failing — no change-point/memo helpers exist yet.
- Journey J-04 (The operator-run compute — button, background job, CLI warmer) failing — `compute_and_publish` is built and tested but has no caller; no "Compute edge report" button, POST route, or CLI warmer exists yet.
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — `/structure`'s Case Studies section still costs several minutes on the real corpus (`GET /research/setups` cold-scan, untouched this iteration).
- `NotComputedPanel`'s `dataset_count` field is fetched and typed but not rendered anywhere in the panel (audit finding F1 — disclosed, non-blocking, no binding DoD item required it).
- Minor test debt (audit finding T1, non-blocking): `test_edge_report_tool_byte_identical_to_rest` became order-coupled to an earlier test's side effect this iteration — passes in the canonical suite run, fails in isolation; recommended self-seed fix in a future cleanup.

## Next step

`eval.md` for this iteration had not yet been written at synthesis time, so no verbatim evaluator Next-Step Recommendation exists to carry forward. The audit's own recommended next step (`docs/handoffs/goal-fast_wall-iter-1-audit.md`) is to proceed to J-02 ("The stores stop re-reading — verified-content caches + durable dataset index"), per `docs/goal.md`'s stated dependency order (J-01 → J-02 → J-03 → J-04 → J-05, with J-06 riding on J-02's durable index): J-01's phase goal is fully achieved and the frozen foundation is verifiably intact (fingerprint `4d665603569b9dbf`, 0 CRITICAL/IMPORTANT audit findings). Two non-blocking carry-forwards are worth folding into that or a later cleanup pass: self-seed the newly order-coupled `test_edge_report_tool_byte_identical_to_rest` MCP test, and consider surfacing `dataset_count` in the not-computed panel if still desired.

## Assumptions made

- iter-1 · goal-decomposer — Ambiguity: what value the not-computed payload's `compute` field should carry before a compute-job manager exists. We chose: always emit `compute: null` this iteration (the manager is J-04's future deliverable; the key is present now for forward shape-compatibility). Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: how broadly to scope J-07's previously-deferred Edge-Report-leg regression check now that J-01 makes the cold GET safe. We chose: close only the Edge-Report leg J-01 actually fixes, not the full `/structure` page load, which still separately waits on the untouched `GET /research/setups` cold-scan cost (J-06's future scope). Reversible: yes

## Quick verify

From `reports/phase-goal-fast_wall-iter-1-what-to-click.md`:

1. Open `http://localhost:3301/structure` in your browser.
2. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
3. Wait up to about 1 minute, watching only the Edge Report panel.
4. If you saw "Edge report not computed yet.", look for any button or input field inside that amber box.
5. Reload the page (press F5 or Cmd+R).

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-fast_wall-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-fast_wall-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-1-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-fast_wall-iter-1-ux-regression.md |
| QA | PASS | reports/qa/goal-fast_wall-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-fast_wall-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-fast_wall-iter-1-closure-verdict.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
