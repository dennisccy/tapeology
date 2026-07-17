# Iteration Summary — goal-fast_wall-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 3

## In plain words

**What you can do now:** You can open the cockpit and watch simulated buyer/seller tape scenarios settle, save your trade thinking to a journal and review it later, browse replay studies of past tape readings, check a performance ledger of simulated (not real) results, and view the structure page's price-level map and case studies. Opening that structure page's price-report area is still always safe — it never risks starting an hours-long background calculation, and if a report genuinely hasn't been calculated yet, the page tells you so plainly instead of hanging or spinning forever.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. Two of the app's internal analysis engines (the ones that check whether a price sits at a known support or resistance level) stopped redoing the exact same calculation on every single recorded price tick — they now reuse the answer until it's genuinely due for a refresh. What these engines report hasn't changed at all; they're proven to produce identical results, just computed far less often, which will make a still-to-come "run the full report" feature dramatically faster once it exists.

**What's next:** Next, the team plans to add the actual button and background job that let someone trigger this now-much-faster calculation directly from the app.

## Headline

The two structure-aware simulated strategies stop redoing the same work over and over.

## Direction

**Signal:** improving
**Why:** J-03 (the arm memo) is newly passing this iteration on strong, independently-verified evidence — the per-run `_StructureArmMemo` collapses per-tick `compute_levels`/`compute_tradability` recomputation to once per real change-point interval / UTC session date, byte-identical to the unmemoized path, confirmed by review PASS, QA 15/15, and a hard audit whose mutation probe proved the byte-identity guards genuinely catch a stale-memo bug. J-01, J-02, and J-07 carry forward passing on the mechanical byte-identity gate this backend-only iteration requires (`Frontend Present: no`), with zero regressions and zero anti-goal violations. Each of the four iterations so far (0 through 3) has moved exactly one journey to passing with no stalls or reversals, so direction reads improving.

**Trend (last 4 iters):**
- Newly passing this iter: J-03
- Newly passing in last 4 iters total: J-07 (iter-0), J-01 (iter-1), J-02 (iter-2), J-03 (iter-3)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** "J-03 ('the arm memo') is newly passing on strong, personally-verified evidence: the per-run `_StructureArmMemo` in `backtests.py` ... collapses the per-tick `compute_levels`/`compute_tradability` recompute into one call per real change-point interval / UTC session date, byte-identically to the `memo=None` direct-call path. All four lanes agree (review PASS, QA 15/15, a hard audit PASS with a mutation probe, coherence COHERENCE-PASS); I independently re-ran the targeted suite (114/114), the two guard tests, the two counting-spy tests, and the frozen fingerprint. No journey regressed and no anti-goal was violated, but J-04–J-06 remain unbuilt by design — so this is CONTINUE, not GOAL_ACHIEVED."

## What was done

- Added `level_change_points` (levels.py) and `basis_day_key` (tradability.py) — pure, additive helpers marking exactly when `compute_levels`/`compute_tradability` can change, mirroring the owner functions' own logic verbatim.
- Added a per-run `_StructureArmMemo` in `backtests.py`, threaded into `_structure_tape_arm`/`_structure_tape_map_arm` via a `memo=None` keyword-only param — every pre-existing caller keeps today's exact direct-call behavior byte-for-byte.
- Collapsed `compute_levels`/`compute_tradability` calls from once per confirming tick to once per real change-point interval / UTC session date — mechanically proven by call-counting spy tests (TC-9, TC-10), not just asserted.
- Proved byte-identical output memoized vs. unmemoized for both structure strategies, including both goal-named edge cases (a daily period closing mid-tick-stream; a run crossing a UTC date boundary) — TC-5 through TC-8.
- Full backend suite: 1440 passed / 7 skipped / 0 failed (13 new tests added, 0 newly skipped or deleted); `config_fingerprint()` unchanged at `4d665603569b9dbf`; zero diff to every out-of-scope file (edge_report.py, bars.py, datasets.py, routes.py, config.py, all frontend files).
- Review PASS, QA PASS (15/15 test cases), and a hard audit PASS that independently mutation-tested the byte-identity guards and confirmed they genuinely catch a stale-memo bug; goal-evaluator confirmed CONTINUE with J-03 newly passing in journey-history.json.
- Browser QA skipped (backend-only iteration, `Frontend Present: no`); required-still-passing journeys J-01/J-02/J-07 re-verified passing via the mechanical byte-identity gate (TC-14/TC-15) rather than a fresh browser pass.

## What's left

- Journey J-04 (The operator-run compute — button, background job, CLI warmer) failing — not yet built; now unblocked by J-03's memo, next per the dependency order.
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing — depends on J-04's manager plumbing.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — technically unblocked by J-02's `BarStore.root`, but deliberately deferred to avoid bundling two risky frozen-foundation-file changes in one diff.
- The memo's throughput win is not yet observable from `/structure` — no operator-run trigger exists until J-04 ships, so there's no user-facing artifact to screenshot yet.
- `.claude/project-template.md` still resolves to the framework's generic, unfilled template rather than this project's real stack/commands — a pre-existing gap flagged again this iteration, not introduced by it.

## Next step

Build J-04 ("The operator-run compute — button, background job, CLI warmer") next, per goal.md's dependency order (J-01 → J-02 → J-03 → J-04 → J-05), now unblocked by J-03's memo. J-04 is `Frontend Present: yes`: a browser-verifiable "Compute edge report" button on `/structure` with progress polling, plus a new `edge_report_compute.py` module, three new REST routes (`POST/GET /research/edge-report/compute`, `POST .../cancel`), and a CLI warmer. Depth **full** — J-04 carries the critical "No compute on page load — operator-run only" anti-goal (the trigger must be POST-only; GET stays 405; no ambient/scheduled compute), the "No MCP write surface" anti-goal (no new MCP tool; the compute trigger is REST-only), the frozen warm-cache render must survive, and it has a real browser leg (button → progress counts → cells or the honest empty state). The audit + ux-regression + closure + browser-qa lanes are the warranted backstop for a new operator-facing compute surface over frozen foundations.

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: This iteration modified the canonical owners (`levels.py`/`tradability.py`) behind J-07's `/structure` UI while running `Frontend Present: no`, so J-07's pass has no fresh screenshot or replay this iteration. We chose: Score J-07 (and J-01/J-02) `passing` on a mechanical byte-identity argument — the served bytes of the modified owners are proven unchanged (TC-15 + an independently re-run pinned-value suite + frozen fingerprint `4d665603569b9dbf`) — rather than downgrading to `unknown`, extending iter-2's mechanical-carry precedent to the harder case where the journey's own backing computation changed. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: J-03's acceptance requires the tick-fixture structure backtests to complete "within an interactive test budget" but names no concrete number. We chose: Pin TC-11 at a generous 10-second wall-clock ceiling on a fixture crossing at least 5 distinct `level_change_points` intervals — satisfiable once the memo works, diagnostic of a regression to per-tick recomputation, and not flaky on a loaded CI box; the real proof of the throughput fix is the counting-spy call-count collapse (TC-9/TC-10), not this wall-clock number. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: The stable-journey re-verification model assumes the golden-replay lane runs for J-01/J-07, but this backend-only iteration (`Frontend Present: no`) skipped browser-qa entirely, so neither got a fresh screenshot. We chose: Score J-01 and J-07 `passing` on a mechanical non-regression argument — a UI end-state can change only if frontend code or served bytes change, and both are proven unchanged (zero-frontend diff + TC-8/TC-14 byte-identity + green suite + frozen fingerprint) — rather than downgrading to `unknown`. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: The iteration spec's prose says both `detail` AND `dataset_count` "become newly visible" in the not-computed panel, but the shipped panel renders only the headline + `detail` (`dataset_count` reaches typed state but is never painted). We chose: Score J-01 `passing` by treating the goal.md acceptance + TC-11 (headline + verbatim `detail` only) as authoritative over the stronger iteration-spec prose claim; the unrendered `dataset_count` is a spec-completeness gap, not an acceptance miss. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-07's deferred acceptance says its live `/structure` spot-check should re-run "the first iteration that makes the cold GET safe (J-01)", but a full page load still separately waits on `GET /research/setups`'s cold-scan cost (268.95s at iter-0) until J-06 ships. We chose: Scope J-07's closure to the specific Edge-Report leg J-01 actually fixes, not the full page load, which still separately waits on the untouched setups cost — a full live spot-check is bonus evidence, not required. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-01 step 2 says the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager (`edge_report_compute.py`) is J-04's deliverable and doesn't exist yet. We chose: `peek_strategy_comparison_report`'s not-computed payload always emits `compute: null` this iteration — the key exists now for forward shape-compatibility with J-04's polling logic; J-04 wires the real snapshot into the same key without a shape change. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-07's acceptance names a live `/structure` interactive spot-check, but loading `/structure` against the default real-corpus backend triggers the never-completing edge-report sweep (hours of CPU pin), so the live leg was withheld. We chose: Score J-07 `passing` on the strength of the green suite, pinned fingerprint, equivalence 22/22, and four verified screenshots, treating the spec-sanctioned code-citation/SSR substitution as sufficient rather than downgrading to `partial`/`unknown`. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-fast_wall-iter-3-review.md |
| Browser QA | SKIPPED | reports/phase-goal-fast_wall-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-3-ui-test-plan.md |
| QA | PASS | reports/qa/goal-fast_wall-iter-3-qa.md |
| Audit | PASS | docs/handoffs/goal-fast_wall-iter-3-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-fast_wall-iter-3-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-fast_wall/iter-3/eval.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
