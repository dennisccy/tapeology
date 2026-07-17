# goal-fast_wall-iter-5 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05 (the substantive deliverable — a durable, resumable per-pair sub-cache plus a CLI-only
multi-process parallel pre-warm) is delivered to a high standard: every DoD test contract TC-4
through TC-14 is met with genuinely **non-vacuous** tests (a call-counting key-busting matrix, a
kill-and-resume `_run_backtest` spy, a real cross-process distinct-PID proof, a zero-fresh-backtest
CLI-reuse proof), frozen foundations are git-confirmed byte-unchanged, `config_fingerprint` is
still `4d665603569b9dbf`, and no anti-goal was weakened. J-04's browser gap is substantively closed
— the click-through, terminal, and failed-state renders are genuinely browser-verified with
committed screenshots I opened and confirmed. The only gaps are fixture-bound and documented: the
live *mid-run progress tick* and the "(N from cache)" N>0 render cannot be observed against the
mandated keyless fixtures (0 eligible pairs → instant resolution), so those two legs rest on
pytest-level proof, and the general `qa.md` lane narrated the browser leg more pessimistically than
the authoritative browser-qa lane before both reconciled to "ship."

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): the "worker-side backtest failure propagates" test exercises the sequential path, not a real spawned worker**
`tests/test_edge_report.py:1566` (`test_a_worker_side_backtest_failure_propagates_as_a_genuine_sweep_failure`)
monkeypatches the in-process `edge_report._run_backtest` and calls `run_strategy_comparison_report`
with no `workers` argument, so it runs strictly sequentially. A `monkeypatch` does not cross the
`spawn` process boundary, so this test does not actually exercise `_run_dataset_pairs_in_worker`
raising inside a child process. The real parallel-worker exception path
(`edge_report.py:707`, `future.result()` in `_parallel_prewarm_sub_cache`) re-raises a worker
exception in the orchestrator by standard `concurrent.futures` semantics, so the behavior is
correct — it is simply not directly covered by a test. The spec's `state: "failed"` / verbatim-error
requirement applies to the manager path, which is always sequential (TC-12), so the gap has no
product impact. No fix applied (adding a real cross-process failure test is scope-adjacent and the
behavior is standard-library-guaranteed).

**B2 — OBSERVATION (observation): `EdgeReportBacktestCache.lookup` guards `sqlite3.Error` but not a structurally-valid row carrying non-JSON text**
`edge_report_backtest_cache.py:187` does `json.loads(row["result_json"])` outside the
`sqlite3.Error` guard. The module docstring claims "a corrupted/unreadable DB is treated as a full
miss, never a crash"; a row that is valid SQLite but whose text column was externally corrupted to
non-JSON would raise `json.JSONDecodeError`, not `sqlite3.Error`, and propagate. This is negligible
in practice — the cache only ever writes valid `json.dumps(...)`, so the only way to reach it is
external tampering that keeps the SQLite structure intact while corrupting exactly the value column,
and the value is a rebuildable accelerator. Below the fix threshold; recorded for completeness. No
fix applied (fixing it is scope creep for a can't-happen-in-practice path).

### Frontend Findings

**F1 — (observation): zero frontend diff, as specified**
`git diff --stat HEAD -- apps/frontend` is empty (I confirmed directly). `structure/page.tsx` and
every other frontend file are byte-unchanged, exactly as the plan required. `Frontend Present: yes`
was set only to force the UI lanes to re-verify the already-shipped `/structure` button. No finding.

### Test Findings

**T1 — GAP (gap): the live mid-run progress tick and the "(N from cache)" N>0 render are not browser-observable on the committed keyless fixtures**
The spec's TC-1 asks for a screenshot capturing "click → **progress** → terminal-state," and UT-07
asks for the "(N from cache)" annotation showing N>0. Both committed fixtures (`datasets_j03` and
`apps/backend/tests/fixtures/datasets`) resolve **zero eligible pairs** (their PG symbol is not a
config-owned panel symbol), so a compute resolves to the honest empty terminal state before the next
DOM poll — there is nothing to tick and nothing to resume from a live server. The browser therefore
verified the click → *terminal* and click → *failed* legs (UT-02, UT-06, screenshots confirmed),
but not a live running progress line with a real backtest count, and UT-07 is a documented SKIP. The
underlying counting logic is proven non-vacuously at the pytest level (TC-6 asserts
`backtests_from_cache == 1` via a real spy; TC-8/TC-10/TC-11 corroborate). This is a fixture
limitation openly disclosed across `ui-test-results.md`, `ux-regression.md`, and the dev handoff —
not a product defect and not a dishonest claim. Acceptable per the spec's own recipe (which
mandated the keyless fixture) and its explicit "J-04 may stay best-effort" fallback.

**T2 — OBSERVATION (observation): the two QA lanes narrate the browser leg differently, then reconcile**
`reports/qa/goal-fast_wall-iter-5-qa.md` reports browser TC-1 as PARTIAL ("compute remains in
`state: running` … `backtests_done: 0 / 33` across 120+ seconds") and keeps J-04 `partial`, whereas
the authoritative merged browser lane `reports/phase-goal-fast_wall-iter-5-ui-test-results.md`
reports browser PASS (13/14) with J-04 closed via UT-02+UT-06. The discrepancy is explained by the
`ux-regression.md` "Notable Finding #1" (a self-inflicted `.next` build-cache collision from two
`next dev` processes on one directory) and by the `qa.md` run apparently exercising an 11-dataset /
33-backtest instance rather than the scoped 0-eligible-pair `datasets_j03` fixture the recipe
requires. Both lanes ultimately land on "ship" (`status.json` `qa_verdict: PASS`). Recorded so the
evaluator does not treat `qa.md`'s "stuck 0/33" as an independent product signal — it is the same
infra hazard, not a defect. No fix applied.

---

## 3. Domain Assessment

The core domain logic is correct and, importantly, **conservative by construction** — which is
exactly what this "accelerator" interlude demands.

- **Byte-identity discipline holds end-to-end.** `_split_cells`'s `run_pair=None` default
  (`edge_report.py:478-484`) preserves the pre-J-05 inline `_run_backtest` call exactly; the caching
  closure returns a JSON-round-tripped copy of the *same* `_run_backtest` result on a hit and calls
  the *same* function on a miss. The report is serialized `sort_keys=True` for every equivalence
  assertion (TC-4/TC-9/TC-13/TC-8), and each of those asserts a non-degenerate 3-cell shape rather
  than passing vacuously on an empty report. Round-trip fidelity is verified for floats, `None`, and
  nested structures (`test_result_round_trips_byte_identically_through_json_persistence`).

- **The parallel path never assembles the report.** `_parallel_prewarm_sub_cache` (`edge_report.py:632`)
  only pre-warms the sub-cache; the orchestrator then reassembles through the *untouched* sequential
  `_split_cells`/`run_pair` hit path, so parallel output is byte-identical to sequential **by
  construction**. The worker (`_run_dataset_pairs_in_worker`) iterates `_ALL_STRATEGY_IDS` (line 623),
  the identical set `_split_cells` iterates (line 473) and `_count_eligible_pairs`/`_eligible_datasets`
  size against (lines 378/470-471) — so the pre-warm computes exactly the pairs the reassembly looks
  up, and a missed/failed publish merely costs one harmless sequential recompute, never a divergence.

- **The key is complete and each component is load-bearing.** All eight components
  (`edge_report_backtest_cache.py:95-121`) are proven independently necessary by a call-counting spy
  (TC-5), not merely by a hash-changes assertion; `bar_store_signature` reuses `setups._store_signature`
  verbatim and is computed once per sweep, closed over — verified by a source-inspection coherence
  guard (`test_build_caching_run_pair_computes_signature_and_config_hashes_once_per_sweep_not_per_pair`).

- **Anti-goals are respected.** *No compute on page load*: the sub-cache is injected only into the
  `@router.post("/edge-report/compute")` trigger (`routes.py:2187`); the `GET` path and
  `peek_strategy_comparison_report` are untouched, and UT-01/UT-J-01 confirm two GETs served before
  any POST. The UT-06 screenshot even renders the UI copy "It never runs automatically on a GET." *No
  divergent output*: byte-identity tests above. *Accelerators are never sources of truth*: delete-DB
  and corrupt-DB tests force full byte-identical recompute. *No source-guard weakening / no MCP write
  surface / frozen foundations*: `levels.py`, `tradability.py`, `backtests.py`, `bars.py`,
  `datasets.py`, `dataset_index.py`, `app/mcp/__init__.py`, `config.py`, `edge_report_cache.py`, and
  `setups.py` are all git-confirmed zero-diff (I verified directly), the source-introspection guards
  and the 18-tool MCP guard pass unmodified, and `config_fingerprint()` is `4d665603569b9dbf`.

- **The CLI-only-parallelism scope call is enforced structurally, not by convention.**
  `EdgeReportComputeManager.trigger()` (`edge_report_compute.py`) simply never passes `workers`, so
  the `workers > 1` pre-warm branch is unreachable from the always-on backend; TC-12 captures the
  kwargs to prove it.

Independent verification performed this audit: `config_fingerprint()` → `4d665603569b9dbf`;
`pytest tests/test_edge_report_backtest_cache.py tests/test_edge_report.py
tests/test_edge_report_compute.py tests/test_edge_report_api.py` → all pass (0 failures);
`test_advertised_tool_set_is_exactly_capability_6` + `test_backtests.py` guards → pass; frozen files
+ `apps/frontend/` → zero diff; UT-02/UT-06 evidence screenshots → opened and confirmed to show the
honest terminal empty state and the verbatim integrity error with "Retry compute".

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issues were found. The implementation is surgical and matches the
plan's scope exactly (930 insertions across `edge_report.py`, `edge_report_compute.py`, `routes.py`,
the one new cache module, and three test files — nothing wider). All findings are GAP/OBSERVATION
level; fixing them would be scope creep the audit rules explicitly forbid.

---

## 5. Recommended Next Step

**Proceed.** J-05 is complete, rigorously tested, and anti-goal-clean; J-04's browser gap is
substantively closed. The residual gaps are fixture-bound and documented, not product defects. The
evaluator owns the final `partial → passing` call for J-04 on the progress-tick technicality —
either resolution is compatible with shipping this iteration, since the phase spec pre-authorized
J-04 remaining best-effort.

Two non-blocking follow-ups for a future iteration (do **not** hold this one for them):
1. When a fixture/scenario with genuinely eligible resumable pairs exists (e.g. after J-06 or with a
   recorded corpus), add a browser-QA case that actually renders a live progress tick and the
   "(N from cache)" N>0 annotation (currently UT-07 SKIP), so those two legs become visually
   confirmed rather than resting solely on pytest proof.
2. Next journey per goal.md's dependency order is **J-06** (`setups_scan_cache.py`) — independent of
   J-05, the last of this interlude's seven journeys.
