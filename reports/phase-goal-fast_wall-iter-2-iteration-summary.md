# Iteration Summary — goal-fast_wall-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-17
**Iteration:** 2

## In plain words

**What you can do now:** You can open the cockpit and watch simulated buyer/seller tape scenarios settle, save your trade thinking to a journal and review it later, browse replay studies of past tape readings, check a performance ledger of simulated (not real) results, and view the structure page's price-level map and case studies. Opening that structure page's price-report area is still always safe — it never risks starting an hours-long background calculation, and if a report genuinely hasn't been calculated yet, the page tells you so plainly instead of hanging or spinning forever.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The app's internal data lookups (the parts that check recorded price history and past trade recordings) now remember what they've already verified, so a repeat request skips re-reading and re-checking a file that hasn't changed — and that memory survives a server restart too, instead of resetting every time the app is bounced. Nothing you can click or see is different yet, but every page that reads this data, including last round's price-report fix, is quietly faster underneath.

**What's next:** Next, the team plans to speed up how the price-level map itself gets recalculated as new data comes in — another step toward the structure page loading almost instantly.

## Headline

The app stops re-reading unchanged files on every request.

## Direction

**Signal:** improving
**Why:** This iter shipped and independently verified J-02 in full: `bars.py`/`datasets.py` gained stat-keyed verified-content caches and a new durable `dataset_index.db`, with review PASS, QA 15/15 test cases PASS, and a hard audit PASS that independently re-ran the trust-boundary, byte-identity, tamper, and racy-write tests itself (`config_fingerprint` confirmed frozen structurally via git). J-01 and J-07 carry forward passing on a mechanical non-regression basis (zero-frontend diff + TC-8/TC-14 byte-identity), and `eval.md` confirms CONTINUE with zero regressions and zero anti-goal violations. Each of the three iters so far has moved exactly one journey to passing (iter-0 → J-07, iter-1 → J-01, iter-2 → J-02) with no stalls or reversals, so direction reads improving.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-07, J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** J-02 ("the stores stop re-reading") is genuinely passing: `bars.py`/`datasets.py` gained module-level stat-keyed verified-content caches and a new durable `dataset_index.py` sibling, with the critical "verification trust boundary never weakens" and "no divergent accelerator output" anti-goals upheld mechanically (TC-7 plus the auditor's git-diff proof that `load_events`/`replay` bodies are byte-unchanged; TC-8/TC-9 byte-identity, independently re-run by reviewer and auditor). Scope is exact and independently confirmed by git: 11 product files, zero frontend, and every frozen research file (`edge_report.py`, `edge_report_cache.py`, `levels.py`, `tradability.py`, `setups.py`, `backtests.py`, `config.py`, `bar_index.py`) untouched. J-03–J-06 remain failing by design (sequential dependency order, not yet built); J-01 and J-07 carry forward passing.

## What was done

- Added a module-level, stat-keyed verified-content cache to `bars.py` and `datasets.py` — a repeat read of an unchanged file skips re-reading, re-parsing, and re-checksumming entirely; any file whose stat changes (or is corrupted) still forces a full re-verify, and integrity errors are never cached.
- Added a new durable sibling index (`dataset_index.py` / `dataset_index.db`) so the dataset-store speedup survives a backend restart, not just an in-process cache — a restart-simulation test (TC-9) and a real-corpus restart check both confirm zero re-reads after restart.
- Wired `routes.py`'s `get_dataset_store()` to resolve the new `TAPEOLOGY_DATASET_INDEX_DB` env var, mirroring the existing bar-index env-else-sibling pattern — zero change to any route's request/response contract.
- Kept `DatasetStore.load_events()`/`.replay()` fully re-verifying on every call, byte-unchanged — only `get()`/`list()` metadata reads are accelerated; the audit independently confirmed this via git diff.
- Added 20 new/extended tests (TC-1 through TC-15: tamper detection, racy-write guard, row/`event_counts` copy isolation, REST+MCP byte-identity, restart durability) plus `conftest.py`'s first autouse cache-reset fixture.
- Measured on the real 882MB corpus: `GET /research/datasets` dropped from ~29.4s cold to ~0.00s warm, and stayed instant across a genuine backend restart.
- Full backend suite: 1427 passed / 7 skipped / 0 failed; `config_fingerprint()` held at `4d665603569b9dbf` (no new Config field added). Browser QA was skipped — J-02 is backend-only (`Frontend Present: no`); J-01/J-07 were re-verified passing on a mechanical non-regression basis instead of a fresh browser pass.

## What's left

- Journey J-03 (The arm memo — per-tick levels recompute becomes ~100 memo hits per session) failing — not started.
- Journey J-04 (The operator-run compute — button, background job, CLI warmer) failing — `compute_and_publish` exists but is still unwired to any trigger.
- Journey J-05 (The sweep becomes resumable and parallel — durable pair results + process pool) failing — not started.
- Journey J-06 (Restarts stop hurting — the durable setups scan cache) failing — depends on this iteration's new `BarStore.root` but not itself built.
- This iteration's speed win covers only "list/read metadata" requests — `load_events()`/`replay()`'s deeper per-record verification is deliberately untouched and always re-checks in full, by design.
- The first request after a fresh install (or after deleting `dataset_index.db`) still pays the full ~29s cost once, by design — there is no hidden shortcut that could ever serve unverified data.
- `.claude/project-template.md` still resolves to the framework's unfilled generic template rather than this project's real stack/commands — a pre-existing gap, not introduced by this iteration, flagged again by dev, audit, and closure.

## Next step

Build J-03 ("the arm memo — per-tick levels recompute becomes ~100 memo hits per session") next, per `goal.md`'s stated dependency order (J-01 → J-02 → J-03 → J-04 → J-05), now unblocked by J-02. J-03 adds `level_change_points` to `levels.py`, `basis_day_key` to `tradability.py`, and a per-run `_StructureArmMemo` in `backtests.py`, threaded into the arming checks as an optional keyword. Depth full: J-03 modifies three frozen-foundation research-computation files under the critical "frozen foundations" and "no divergent accelerator output" anti-goals — a memo returning a stale level/tradability state would silently corrupt backtest results, a veto-class defect — and is guarded by the goal's enumerated source-introspection tests (`test_backtests.py:1500-1508`, `:932-943`) plus byte-identity determinism tests covering both memo-bust legs; the audit and coherence lanes are the backstop a lean cycle cannot provide. Keyless/automated — no browser leg expected (`Frontend Present: no` again).

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: The stable-journey re-verification model assumes the golden-replay lane runs for the Required-still-passing set (J-01, J-07), but this backend-only iteration (`Frontend Present: no`) skipped the whole browser-qa step, so neither UI journey got a fresh screenshot or replay this iteration. We chose: Score J-01 and J-07 `passing` (bump `last_verified_iter` to iter-2) on a mechanical non-regression argument — a UI end-state can only change if frontend code or the served response bytes change, and both are proven unchanged (zero-frontend diff + TC-8/TC-14 byte-identity + green suite + frozen fingerprint) — rather than downgrading either to `unknown`. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-01 step 2 says the not-computed payload embeds "the current compute snapshot (or `null`)", but the compute manager (`edge_report_compute.py`) is J-04's deliverable and does not exist yet within this iteration's scope. We chose: `peek_strategy_comparison_report`'s not-computed payload always emits `compute: null` this iteration — the key is present now for forward shape-compatibility with J-04's frontend polling logic. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-07's deferred acceptance says its live `/structure` interactive spot-check should be re-run the first iteration that makes the cold GET safe (J-01), but a full `/structure` page load still separately waits on `GET /research/setups`'s cold-scan cost (268.95s measured at iter-0) until J-06 ships. We chose: Scope this iteration's J-07 closure to the specific Edge-Report leg J-01 actually fixes, not the full page load, which still separately waits on the untouched setups cost. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: The iteration spec's "New information displayed" prose says both `detail` AND `dataset_count` "become newly visible" in the not-computed panel, but the shipped `NotComputedPanel` renders only the headline + `detail` (`dataset_count` reaches typed frontend state but is never painted). We chose: Score J-01 `passing` by treating the goal.md journey acceptance + TC-11 (headline + verbatim `detail` only) as authoritative over the stronger iteration-spec prose claim. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-07's acceptance names a live `/structure` era-5/5B interactive spot-check, but loading `/structure` against the default real-corpus backend triggers the never-completing edge-report sweep (hours of CPU pin), so the live leg was withheld. We chose: Score J-07 `passing` on the strength of the green suite, pinned `config_fingerprint`, equivalence 22/22, and four verified screenshots, treating the spec-sanctioned code-citation/SSR substitution as sufficient rather than downgrading to `partial`/`unknown`. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-fast_wall-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-fast_wall-iter-2-dev.md |
| Review | PASS | reports/reviews/goal-fast_wall-iter-2-review.md |
| Browser QA | SKIPPED | reports/phase-goal-fast_wall-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-fast_wall-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-fast_wall-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-fast_wall-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-fast_wall-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-fast_wall-iter-2-ui-test-plan.md |
| QA | PASS | reports/qa/goal-fast_wall-iter-2-qa.md |
| Audit | PASS | docs/handoffs/goal-fast_wall-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-fast_wall-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-fast_wall/iter-2/eval.md |
| Journey history | — | runs/goal-session-fast_wall/state/journey-history.json |
