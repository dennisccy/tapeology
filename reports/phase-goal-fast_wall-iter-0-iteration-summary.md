# Iteration Summary — goal-fast_wall-iter-0

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-17
**Iteration:** 0

## In plain words

**What you can do now:** You can already open the tape-reading cockpit and watch simulated buyer/seller scenarios play out, save your trade reasoning to a journal and review it later, browse replay studies of past tape readings, check a performance ledger of simulated (not real) results, and view the structure page's price-level map and case studies. All of that still works exactly as it did before this round.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team spent this round carefully measuring exactly how slow the newer Structure page's price-report area is today, and double-checking that everything else still works, as groundwork for next round's speed fixes.

**What's next:** Next, the team will stop the Structure page's price-report area from silently starting an hours-long calculation on every visit, replacing the hang with either an instant saved result or a clear "not computed yet" message.

## Headline

Fast Wall baseline established — J-01–J-06 absent as expected, J-07 regression sentinel passes

## Direction

**Signal:** improving
**Why:** This iter established the session's first honest, zero-diff baseline — J-07 (the foundation regression sentinel) is newly passing on strong evidence (suite 1392/1399, fingerprint 4d665603569b9dbf, equivalence 22/22), while J-01–J-06 fail exactly as predicted since none of the interlude's code exists yet. No regression, no anti-goal violation, and the real corpus is already present locally, so the concrete, unblocked next step (build J-01 at depth full) keeps direction reading as improving rather than merely holding.

**Trend (last 1 iter):**
- Newly passing this iter: J-07
- Newly passing in last 1 iter total: J-07
- Regressions in last 1 iter: none
- Anti-goal violations in last 1 iter: none
- Iters with no journey state change: 0 of last 1

**Latest evaluator reasoning:** Honest verify-only baseline with zero source diff (`git diff --stat -- apps/` empty, `iter-diff.md` "no changes", scan CLEAN). J-01–J-06 confirmed absent by independent grep + the zero-diff scan (the interlude's six new modules/functions do not exist); J-01's target defect (compute-inside-GET via `routes.py:2110-2115` → `get_or_compute` synchronous `compute_fn()`) is live and re-verified. J-07 passes on strong evidence: suite 1392 passed / 7 skipped / 0 failed, `config_fingerprint` 4d665603569b9dbf (live + on-page), equivalence 22/22, and four personally-opened screenshots (both cockpit settlements, frozen performance register banner, on-page fingerprint).

## What was done

- Ran the full backend test suite as the Fast Wall opening baseline: 1392 passed / 7 skipped / 0 failed (435.16s), cross-validated two independent ways; `config_fingerprint` confirmed `4d665603569b9dbf`.
- Confirmed via direct code citation that J-01's target defect is live today: `GET /research/edge-report` (`routes.py:2110-2115`) calls the sweep synchronously inside the request through the only existing cache method, `get_or_compute`.
- Confirmed J-02–J-06's target modules/caches/memos are all absent (grep-verified: no `dataset_index.py`, no `_StructureArmMemo`, no `edge_report_compute.py`, no `EdgeReportBacktestCache`, no `setups_scan_cache.py`).
- Measured live baseline latencies on the real 882MB corpus: `GET /research/datasets` = 30.13s, `GET /research/setups` = 268.95s (4m29s) — both matching `docs/goal.md`'s documented figures closely.
- Verified 1 target journey (J-07) pass browser QA — sim cockpit (SIM-BUYER/SIM-SELLER), `/journal`, `/journal/[id]`, `/studies`, `/performance` all render correctly with frozen texts intact.
- Deliberately withheld a live `/structure` page load against the real corpus (would trigger the hours-long CPU-pinning sweep); substituted a code citation + SSR probe per the spec's own explicit allowance.
- Confirmed zero source files under `apps/` were created, modified, or deleted this iteration (`git diff --stat -- apps/` empty) — a genuine verify-only baseline.

## What's left

- Journey J-01 (Stop the bleeding — `GET /research/edge-report` never computes) failing — the route still computes the sweep synchronously inside the GET request.
- Journey J-02 (The stores stop re-reading — verified-content caches + durable dataset index) failing — no stat-keyed caches or `dataset_index.py` exist yet.
- Journey J-03 (The arm memo — per-tick levels recompute becomes ~100 memo hits per session) failing — no `level_change_points`/`basis_day_key`/`_StructureArmMemo` exist yet.
- Journey J-04 (The operator-run compute — button, background job, CLI warmer) failing — no `edge_report_compute.py`, no compute routes, no "Compute edge report" button.
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing — no `EdgeReportBacktestCache` or `run_pair` seam exist yet.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — `setups.py` still uses only the restart-wiped in-process `_SCAN_CACHE`.
- Known operational risk carried forward: loading `/structure` against the real corpus still triggers the hours-long CPU-pinning sweep until J-01 ships, so live browser checks of `/structure` remain withheld until then.

## Next step

Build J-01 alone ("Stop the bleeding") next, per `goal.md`'s dependency order and the priority rubric (smallest, self-contained, an unblocker): add `EdgeReportCache.lookup`/`compute_and_publish` beside the untouched `get_or_compute`, the shared cache-DB-path resolver, `edge_report.peek_strategy_comparison_report`, rewire `GET /research/edge-report`, and add the `/structure` "Edge report not computed yet." panel — leaving the frozen warm-cache texts byte-identical. J-01 also removes the browser-QA CPU hazard, unblocking live `/structure` checks for every later iteration. Recommended depth: full — this is the session's first code-delivery iteration and it carries the interlude's headline critical anti-goals (no-compute-on-page-load, warm-cache byte-identity, REST↔MCP proxy byte-identity) plus a browser-verifiable frontend panel with a frozen-text-preservation requirement, so the audit + ux-regression + closure lanes are warranted for this opener.

## Assumptions made

- iter-1 · goal-decomposer — Ambiguity: J-07's deferred acceptance (iter-0 assumptions.md) says its live `/structure` interactive spot-check should be re-run the first iteration that makes the cold GET safe (J-01), but a full `/structure` page load on the default real-corpus backend still separately waits on `GET /research/setups`'s cold-scan cost (268.95s measured at iter-0) until J-06 ships — a hazard J-01 does not touch. We chose: scope this iteration's J-07 closure to the specific leg J-01 actually fixes (the Edge-Report mount-time GET), rather than requiring a full live page load that would still cost several minutes for an unrelated, already-diagnosed reason. Reversible: yes.
- iter-1 · goal-decomposer — Ambiguity: J-01 step 2 says the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager (`edge_report_compute.py`) is J-04's deliverable and does not exist yet within this iteration's scope. We chose: `peek_strategy_comparison_report`'s not-computed payload always emits `compute: null` this iteration (key present now for forward shape-compatibility with J-04's frontend polling logic; value is honestly `null` because no compute manager exists yet). Reversible: yes.
- iter-0 · goal-evaluator — Ambiguity: J-07's acceptance names a live `/structure` era-5/5B interactive spot-check, but loading `/structure` against the default real-corpus backend triggers the never-completing edge-report sweep (hours of CPU pin), so the live leg was withheld and only the backend suite + SSR-probe + the other four surfaces' live screenshots cover it. We chose: score J-07 `passing` on the strength of the green suite + pinned `config_fingerprint` + equivalence 22/22 + four verified screenshots + zero-code diff, treating the spec-sanctioned code-citation/SSR substitution as sufficient rather than downgrading to `partial`/`unknown`. Reversible: yes — the deferred live spot-check re-runs the first iteration that makes the cold GET safe (J-01); if it ever fails, J-07 flips to `regressed` there.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-0.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-0-dev.md |
| Review | PASS | reports/reviews/goal-fast_wall-iter-0-review.md |
| Browser QA | PASS | reports/phase-goal-fast_wall-iter-0-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-fast_wall/iter-0/eval.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
