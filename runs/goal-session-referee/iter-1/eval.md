# Iteration 1 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The first real Referee piece works. A new backend answer at `/research/desk/referee/evidence`
now reports, honestly, how much evidence the system already holds: Playbook records, trading
days, and counts per setup and side, plus the strategy side's dataset, split and trade counts
with a plain sentence saying the tick-data gate is unmet. The old product still stands: the
browser replay of the live tape page, the Structure page and the Desk page all held, the owner's
saved data was not touched, and the settings fingerprint did not move. Eight Referee journeys
remain unbuilt, so the work continues.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | failing | passing | `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png` (UT-J-01 PASS row, `reports/phase-goal-referee-iter-1-ui-test-results.md:19`); evaluator re-ran `tests/test_referee_evidence.py` + `tests/test_referee_guards.py` = 15 passed |
| J-02 The evidence contract | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-02`; iter-diff shows no J-02 code |
| J-03 The statistics core | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-03` |
| J-04 Matched nulls | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-04` |
| J-05 The registry | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-05` |
| J-06 Estimand engines + adjudication | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-06` |
| J-07 The starter family | failing | failing (not targeted; carried) | `reports/qa/goal-referee-iter-0-evidence/J-07-fail.png` |
| J-08 Strategy family + promotion interlock | failing | failing (not targeted; carried) | `reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-08` |
| J-09 Referee on /desk + 22 MCP tools | failing | failing (not targeted; carried) | `reports/qa/goal-referee-iter-0-evidence/J-09-fail.png` |
| J-10 The kept product stands | partial | partial (kept-product half re-verified) | `reports/qa/goal-referee-iter-1-evidence/J-10-verify.png` (UT-J-10 PASS, deterministic replay of the 9-step golden `runs/goal-session-referee/journey-scripts/J-10.json`) |

Verification notes (what I opened, and what I did not):

- J-01's screenshot shows the full served body: `detector_basis 02bebbe17e7b8769`,
  `config_fingerprint 08e471b10130e1e2`, `records 4`, `distinct_sessions 3`,
  `signals_at_current_basis 21`, seven `per_setup_side` cells, and on the strategy side
  `tick_gate_met: false` with "150 short of the gate" plus a `basis_caveats` entry naming
  `levels._bars_as_of` and `epoch <= as_of`. The small numbers are the fixture-scoped QA rig's own
  seeded corpus (iter-0 lesson), not the real store.
- I re-ran the 15 new tests myself (all pass; assertions are hand-computed exact counts, including
  newest-record-per-date supersession, stale-basis exclusion, and the zero-corpus HTTP 200 case),
  and re-ran 156 existing guard tests (`test_mcp_server`, `test_no_execution_path`,
  `test_copy_discipline`, `test_desk_ui_guards`) — all pass, MCP still exactly 20 tools.
- I printed `Config().config_fingerprint()` myself: `08e471b10130e1e2`.
- I did NOT re-run the full 2,441-test suite. The reviewer independently re-ran it
  (`reports/reviews/goal-referee-iter-1-review.md`: 2,433 pass / 8 skip / 0 fail, above the 2,418
  era-open floor); the dev handoff reports the same numbers. Diff scope is tiny (one changed file,
  7 added lines, plus 4 new files), so I accepted that pair of independent runs.
- `git status` confirms the only tracked change is `apps/backend/app/main.py`; no diff to
  `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`,
  `pnl_scan.py`, or `app/config.py`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | `iter-1/scan-report.md`: CLEAN on added lines (4 untracked files scanned); no config/env file in the diff |
| Paid/external SaaS, new dependency | OK | No manifest change at all (`requirements.txt` untouched; `git status` shows only `main.py` + 4 new `.py` files); new code imports stdlib `hashlib`/`json` only |
| License changes | OK | No LICENSE or license-field diff (scan-report CLEAN; file list has none) |
| Fabricated/substituted data | OK | Endpoint aggregates recorded stores through their own public read APIs; test corpora are built inside pytest temp dirs via `PlaybookStore.record`/`DatasetStore.record`/`JournalStore.insert_backtest`, never planted in a production path |
| 1. No execution path | OK | `tests/test_no_execution_path.py` re-run by the evaluator — green |
| 2. No profit claims / no advice | OK | `tests/test_copy_discipline.py` green; the new caveat string is asserted clean via `find_violations` (`tests/test_referee_evidence.py:230`) |
| 3. Frozen foundations | OK | Zero diff to `desk_playbook*.py` / `desk_forward.py` / `levels.py` / `tradability.py` / `setups.py` / `pnl_scan.py` / `app/config.py` (git status); the new source-hash guard pins `desk_playbook_context.py` byte-unchanged; fingerprint `08e471b10130e1e2` printed by the evaluator |
| 4. Hold-out-only promotion | OK | `pnl_scan.py` untouched this iteration (J-08 not started) |
| 5. No lookahead | OK | Nothing is computed or measured here — pure counting of already-recorded records; the known forming-bar admission is disclosed, not hidden, per goal.md's Card-6.4 Non-Goal |
| 6. Single source of truth | OK | `iter-1/coherence.md`: **COHERENCE-PASS**; it checked the two near-misses (`detector_basis` vs `playbook_input_signature`, and `dataset_count` vs `edge_report.py`) and found no second implementation |
| 7. Deterministic and seeded | OK | No randomness introduced; response is a pure function of stored records |
| 8. Read-only MCP | OK | Zero diff to `app/mcp/__init__.py`; `tests/test_mcp_server.py` green at the 20-tool tuple; the new path is reachable only through the existing GET proxy allowlist |
| 9. Immutable data | OK | `reports/qa/goal-referee-iter-1-store-scope-guard.md`: CLEAN, all 11,274 protected files unchanged; grep confirms no write/append/open call in either new module |
| 10. Persistence stays scoped | OK | No recording, fetching, or scheduling added |
| Referee: never feeds back (import ban) | OK | Grep: neither new module imports `desk_playbook_detect` or `desk_playbook_context`; imports are `PlaybookStore`/`playbook_parameters`, `DatasetStore`, `JournalStore` only |
| Referee: no confirmatory claim / atlas exploratory / CI-inversion / BH denominator / no gate loosening / certificate-locked promotion / attestation | OK — not yet reachable | No statistics, registry, verdict, or promotion code exists yet (J-03–J-08 unbuilt); nothing this iteration serves any verdict |
| No annualized metrics | OK | Served payload (screenshot, full body) contains no "annualized"; copy-discipline suite green |
| Proposer stays inside the marker block | OK | `docs/goal.md` unchanged this iteration (not in `git status`) |
| Host-guard caps | OK | `host-guard.env` untouched; no cap widened or bypassed |

Minor, non-blocking: the response serves an additive `integrity_errors` key on both blocks that is
outside the iteration spec's pinned six-key shape. The reviewer logged it as a NOTE and the
coherence auditor as an advisory; it is honest error propagation matching every sibling desk
route, so it is not an anti-goal violation — but the written-down contract should absorb it.

## Next-Step Recommendation

Build **J-02 "The evidence contract"** next, alone, at lean depth. It is the next step in the
goal's own order and everything after it waits on it: turn this iteration's counts into one typed
record per single observation, for both families — Playbook occurrences (grouped by trading day,
newest record per day) and strategy trades (grouped by dataset) — plus the small rebuildable cache
whose deletion may change speed only, never numbers. Two riders for the same file: write the two
`integrity_errors` fields into the documented response shape, and have J-02 re-use the existing
caveat sentence rather than writing a second one. J-10 keeps riding along as the
still-must-pass check. Approve building J-02 next; no human unblock is needed.

## Halt Justification (if halting)

Not halting.
