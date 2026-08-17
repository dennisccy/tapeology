# Iteration 1 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The corpus-truth surface was built and the backend half of it is real: I called the new
readiness code myself against the real tick files on disk and read the exact numbers the goal
asks for — 12 symbol-days, 18 shards, about 3.0 session-equivalents, every shard marked
"exploratory" and "hand assigned", and all three pilot studies short of their floor. But the
browser check could not see any of that. The test rig the project forces browser checks to use
points at an empty data folder, so the new panel on the Desk page truthfully showed an empty
corpus. So J-01 "The era transition stands" is half-proven, not done. Nothing regressed: the
Cockpit, Structure and Desk pages all still work, the frozen fingerprint and the six referee
files are byte-for-byte unchanged, and the guard tests are green.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | partial | partial | `reports/phase-goal-rapid-microscope-iter-1-ui-test-results.md` (UT-J-01, FAIL) + `reports/qa/goal-rapid-microscope-iter-1-evidence/UT-J-01-fail.png`; backend half re-computed by the evaluator against `apps/backend/.data/datasets` (12 / 18 / 3.0089 / all floors unmet) and `tests/test_micro_readiness.py` 31/31 green |
| J-02 | failing | failing | Evaluator re-check: `apps/backend/app/research/datasets.py:376` still `def replay(self, dataset_id, config)` — no `observer=`; `micro_observer.py`/`micro_snapshots.py`/`micro_features.py` absent |
| J-03 | failing | failing | Evaluator re-check: `micro_join.py` absent; readiness payload carries no joinable-corpus count |
| J-04 | failing | failing | Evaluator re-check: `scout.py`/`scout_ledger.py` absent |
| J-05 | failing | failing | Evaluator re-check: `micro_accessor.py`/`walkforward.py` absent |
| J-06 | failing | failing | Evaluator re-check: `tick_recorder.py`/`vault.py` absent |
| J-07 | failing | failing | Evaluator re-check: `micro_graduation.py` absent |
| J-08 | failing | failing | `UT-J-01-fail.png` shows no Scout/Walk-Forward/Vault section; `tests/test_mcp_server.py` EXPECTED_TOOLS still a 22-tuple |
| J-09 | failing | failing | Evaluator re-check: no ledgered study specs; the scout ledger does not exist |
| J-10 | partial | partial | `reports/phase-goal-rapid-microscope-iter-1-ui-test-results.md` (UT-J-10, PASS) + `UT-J-10-cockpit.png`, `UT-J-10-structure.png`, `UT-J-10-desk-sections.png`; evaluator re-ran fingerprint `08e471b10130e1e2`, 6/6 referee SHA-256 match iter-0, 239 guard/golden tests green. Trap suite TR-1..TR-22 still absent |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-1/scan-report.md` CLEAN; no new env/config file in the 8-file diff |
| Paid / external SaaS, new runtime dependency | OK | scan-report CLEAN; no manifest touched; `micro_readiness.py` uses only stdlib `sqlite3`/`zoneinfo` |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff list |
| Fabricated / substituted data | OK | Readiness reads `DatasetStore.list()`/`load_events()` verbatim; evaluator reproduced 12/18/3.0089 from the real store. The rig's `0` reading is an honest empty state, correctly labelled "No tick shards recorded." |
| Rail 1 — no execution path | OK | `tests/test_no_execution_path.py` green (evaluator re-ran) |
| Rail 2 — no profit claims / advice | OK | `tests/test_copy_discipline.py` green (evaluator re-ran) |
| Rail 3 — frozen foundations | OK | Fingerprint `08e471b10130e1e2` re-printed by the evaluator; 6/6 `referee_*.py` SHA-256 byte-identical to the iter-0 listing; `test_observer_equivalence.py` + the `test_dense_replay_gate.py` golden trace green byte-unmodified; engine/, `datasets.py`, `config.py` absent from the diff |
| Rail 4 — hold-out-only promotion | OK | No promotion/champion path touched; `pnl_scan` interlock absent from the diff |
| Rail 5 — no lookahead | OK | Readiness is a static on-disk inventory; no as-of computation exists in `micro_readiness.py` |
| Rail 6 — single source of truth | OK | `coherence.md` = COHERENCE-PASS; evaluator grep confirms `REFEREE_TICK_GATE_SYMBOL_DAYS` is defined once (`referee_evidence.py:149`) and imported once (`micro_readiness.py:71`), with no duplicated `150` literal |
| Rail 7 — deterministic and seeded | OK | No randomness introduced; cache is checksum-keyed and rebuildable |
| Rail 8 — read-only MCP | OK | `EXPECTED_TOOLS` still a 22-tuple; `test_mcp_server.py` green unmodified; no MCP file in the diff |
| Rail 9 — immutable data | OK | `reports/qa/goal-rapid-microscope-iter-1-store-scope-guard.md` CLEAN — 11,275 protected files unchanged in size and mtime, `.data/datasets` included. The new `micro_readiness_cache.db` is a derived, rebuildable projection outside the protected list, matching the `dataset_index.db`/`tradability_cache.db` precedent |
| Rail 10 — persistence stays scoped | OK | No recording path added; readiness is a plain GET |
| 12 legacy symbol-days permanently exploratory | OK | All 18 shards served `exposure_state: "exploratory"`, `split_provenance: "hand_assigned"` (evaluator-computed) |
| ~150-symbol-day gate never lowered | OK | `referee_tick_gate_symbol_days: 150` served verbatim; all 3 studies read `floor_unmet` at required 60 / available 11 |
| No claim beyond what L1 supports | OK, with a watch item | No "iceberg"/intent language (copy-discipline green). `unknown_frac` is not served — the dev flagged this; this endpoint serves no aggressor-derived measurement, only the `fallback_frac` disclosure itself, so the rail is not breached here. It becomes live in J-02, where every per-window feature must carry both fractions |
| Referee modules byte-untouched | OK | 6/6 SHA-256 match; `test_referee_guards.py` green |
| Vault secret never in repo | OK | No vault code exists yet; nothing secret in the diff |
| Accessor is the only data door | OK (not yet in force) | `micro_accessor.py` lands in J-05; readiness reads dataset events through `store.load_events()`, never a raw `open()` |
| Enhancement loop stays in its box | OK | `docs/goal.md` untouched (`git status`) |
| Host-guard caps | OK | Evaluator ran every test under the declared CPU mask `4-7,12-15` |

## Next-Step Recommendation

Build J-02 "The micro observer" next, and run it through the full pipeline. It is the next thing
everything else waits on: it adds the reading hook to the replay path, writes the per-event
feature snapshots, and lands the first no-peeking-at-the-future checks. It also touches the two
files this era promises to keep byte-for-byte identical (the tape engine's observer hook and the
dataset replay function), which is exactly the kind of change that deserves the auditor and
closure steps rather than a light pass.

Carry two small clean-up jobs alongside it, not as the goal:

1. Make the browser test rig able to show tick data. Today the rig's data folder is empty, so no
   browser check in this whole era can ever see a real corpus — that will block J-08's four new
   panels the same way it blocked J-01 today. Either seed the rig with the tick fixture files the
   repo already keeps at `apps/backend/tests/fixtures/datasets/`, or let the readiness check run
   against the real read-only corpus while the store-scope guard keeps proving nothing was
   written. Then take one element screenshot of the Microscope Readiness panel with a non-empty
   shard table so J-01 can finally be scored as passing.
2. Tidy the test file the reviewer flagged: `apps/backend/tests/test_desk_ui_guards.py:510-559`
   has five checks sitting in the wrong test function, so both function names now describe
   something they do not test. Nothing is lost, but it should be moved back.

In one sentence: approve building the observer next with the fuller review pipeline, and let it
also fix the empty test rig so the corpus panel can finally be photographed with real numbers.
