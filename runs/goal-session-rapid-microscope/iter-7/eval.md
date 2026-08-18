# Iteration 7 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

Two things were built and both hold up when checked. The walk-forward engine (J-05) is now
finished: there is a real command an operator can run that answers "you only have 11 days of tape,
you need 105" and stops — the exact sentence the goal asks for, which until now only a test could
produce. The recording format also gained the extra trade and quote details that must exist before
any new tape is recorded, and every one of the 18 existing recordings still opens with its
fingerprint matching. One dangerous fault was introduced and fixed inside this same run: the new
details quietly changed how a recording's identity is calculated, which would have let the same
tape be filed twice under two different labels. I broke it again myself and confirmed the repair
holds. Four journeys that were already working were re-checked against the owner's real data and
still work; nothing went backwards.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The corpus truth on the record | passing | passing (re-verified) | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-02-result.png`; evaluator re-derived `build_readiness` against the real store: 12 symbol-days / 18 datasets / 1173.49 RTH min / 3.0089 session-equivalents / gate 150, 18/18 exploratory + hand_assigned, 3 floors `floor_unmet` 11/60, `integrity_errors: []` |
| J-02 The micro observer | passing | passing (re-verified) | Evaluator's live `list_snapshot_meta`: 18 snapshots, 3,815,933 rows, every stored `feature_source_hash` = freshly recomputed `b504251ac6d19f50…`, all `quote_size_unit: unverified`; `micro_features.py`/`micro_observer.py`/`micro_snapshots.py` empty diff |
| J-03 Structure x flow | passing | passing (re-verified) | Evaluator's live read: `joinable_corpus {total: 2, playbook_signal_count: 2, by_setup_id {range_trade: 2}, band_touch_count not_enumerated, playbook_integrity_errors: []}`; `micro_join.py` empty diff |
| J-04 The Scout and the ledger | passing | passing (re-verified) | Evaluator called `ScoutLedger.verify_chain()` on the real `.data/micro_scout` → `{'ok': True, 'failed_at_row': None, 'reason': None}`; `scout.py`/`scout_ledger.py` empty diff |
| J-05 The walk-forward engine | partial | **passing** | Evaluator re-ran `python -m app.research.walkforward --family tick_legacy` against the real store: stdout `11 < 105 -- refused (TR-15): this corpus cannot produce WF_MIN_SUFFICIENT_FOLDS(3) folds under this geometry`, exit 1; real `.data/micro_walkforward` byte-identical before/after (`ea04c19b0a36d6ca`); `apps/backend/app/research/walkforward.py:1005`; `docs/handoffs/goal-rapid-microscope-iter-7-audit.md` §3 |
| J-06 The recorder and the Vault | failing | **partial** | Step 1 of 5, itself partial. Evaluator's own run: `DatasetStore.list()` on the real store → 18 records, `errors: []`, zero new manifest keys; preservation fields round-trip verbatim; absent kwargs ⇒ pre-change manifest shape; bad `quote_size_unit` rejected against `micro_features.QUOTE_SIZE_UNITS`. Absent: `tick_recorder.py`, `vault.py`, TR-2/4/12/20 tests, tranche, sealed shards. `docs/handoffs/goal-rapid-microscope-iter-7-audit.md` B4 |
| J-07 Graduation | failing | failing | `app/research/micro_graduation.py` does not exist (evaluator checked) |
| J-08 The surface and MCP v6 | failing | failing | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-01-result.png` — `/desk` ends at Microscope Readiness, no Scout Ledger / Walk-Forward / Validation Vault section; zero `apps/frontend` files changed; MCP still 22 tools |
| J-09 The pilot studies | failing | failing | All three predeclared study floors read `floor_unmet` at 11/60 in the evaluator's own readiness read; no study family ledgered |
| J-10 The kept product stands | partial | partial | Sentinel green: `reports/phase-goal-rapid-microscope-iter-7-ui-test-results.llm.md` 8/8 PASS (read directly) + replay lane PASS on `journey-scripts/J-10.json`; evaluator opened `UT-03-result.png`, `UT-04-result.png`, `UT-02-result.png`. Frozen half re-run by evaluator: fingerprint `08e471b10130e1e2`, six `referee_*.py` SHA-256 identical to iteration 0, suite 3045 pass / 8 skip / 0 fail. Trap half still short: TR-2/4/12/19/20/22 have no dedicated test |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-7/scan-report.md` CLEAN; the 8-file diff contains no config or env file; no credentialed call was made |
| Paid / external SaaS added | OK | scan-report reports no dependency findings; no manifest (`requirements*.txt`, `pyproject.toml`, `package.json`) is in the diff; the Alpaca change only reads more fields off the existing SDK response object |
| License change | OK | scan-report CLEAN; no LICENSE file or license field in the diff |
| Fabricated / substituted data | OK | Readiness values re-derived by me from disk; floors honestly `floor_unmet`; the tick refusal is an honest refusal; the rig screenshot honestly shows the rig's 1/2 corpus, not a borrowed 12/18 |
| Frozen foundations *(critical)* | OK | `Config().config_fingerprint()` → `08e471b10130e1e2` and all six `referee_*.py` SHA-256 identical to the iteration-0 listing, both re-run by me; `apps/frontend`, `app/engine`, `referee_*`, `micro_features.py`, `micro_observer.py`, `micro_snapshots.py`, `micro_readiness.py`, `micro_join.py`, `routes.py`, `micro_routes.py`, `test_observer_equivalence.py`, `test_dense_replay_gate.py`, `journey-scripts/` — every one an empty diff in my own check |
| Immutable data / splits frozen at registration *(critical)* | **VIOLATED AND FIXED IN-RUN** | Audit B1. `_content_checksum` began hashing the new preservation keys, defeating the only guard on "splits are frozen at registration". Fixed by `_tape_identity_rows` (`apps/backend/app/research/datasets.py:233-254`). I re-broke it myself: the same tape re-recorded with preservation fields under a different split is REFUSED (`DatasetAlreadyRegistered`), one dataset registered, split stays `train`; all 18 real datasets still verify. Resolved |
| Single source of truth *(critical)* | OK | `iter-7/coherence.md` = COHERENCE-PASS; `datasets.py` imports the existing `micro_features.QUOTE_SIZE_UNITS` (its rejection message names that module); `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` undefined, pinned by an AST guard test |
| No cross-unit liquidity arithmetic *(critical)* | OK | No arithmetic added; `quote_size_unit` is storage-only with no caller; all 18 snapshots still read `unverified` in my own listing |
| 12 tick symbol-days permanently exploratory *(critical)* | OK | My readiness read: 18/18 shards `exposure_state: exploratory` |
| The denominator never shrinks *(critical)* | OK | Scout ledger chain verifies `{'ok': True}` on the real store; no ledger row deleted; `scout_ledger.py` unchanged |
| No fold geometry change after fold 1 *(critical)* | **OPEN — minor** | Audit B2. The new CLI registers the tick fold spec BEFORE the floor check, freezing `DIAGNOSTIC_GEOMETRY` for the tick corpus and pinning today's 11-date manifest hash permanently. Scored minor, not critical: no tick fold exists, the tick corpus has zero survivor states, and the operator's real ledger holds no such row (byte-identical before/after my run). Must be fixed before the recorder grows the corpus |
| No lookahead *(critical)* | OK / one carried minor | Nothing this diff computes is time-dependent. The carried iter-2 minor (`micro_observer.py:636/:657` depletion stamp one quote early) is still open and still owner-owned; that file is byte-unchanged and no result this iteration rests on it |
| Deterministic and seeded *(critical)* | OK | No random draw added; I reproduced the developer's exact CLI output byte-for-byte |
| Read-only MCP *(critical)* | OK | No MCP file in the diff; surface still the 22-tool contract |
| Persistence stays scoped *(critical)* | OK | The tick-family CLI is read-only over the dataset store; I confirmed the real `.data/micro_walkforward` unchanged after my run |
| No execution path *(critical)* | OK | No broker/order code; `test_no_execution_path.py` green in my own 3045-pass suite run |
| ~150-symbol-day gate never lowered *(critical)* | OK | Readiness still serves `referee_tick_gate_symbol_days: 150` against 12 actual |

## Next-Step Recommendation

Build the tape recorder next — step 2 of J-06 "The recorder and the Vault" — on its own, under the
full pipeline with the independent checker kept in the loop. That checker has now been the only step
in this session to catch a serious honesty or data-integrity fault four separate times, including
this run's. Do not shorten it for time.

Carry five small items with it, all of which only start to hurt once new tape exists:

1. Make the new tick command check the size floor BEFORE it writes its permanent shape record.
   Today it writes first, which locks in today's 11 days and today's fold shape forever.
2. Make a recording that carries the new extra details safe to use as a lookup key. The extra
   details are stored as a list, and the program will raise an error if anything tries to use such
   a record as a dictionary key — this can only happen on newly recorded tape.
3. Report a damaged recording instead of quietly leaving it out of the list of known days.
4. Word the "request complete" message honestly — today it would say a fold build finished when no
   fold was built. It is unreachable now and becomes reachable the moment the corpus grows.
5. Ask a framework-maintenance session (outside this loop) to look at two harness problems: the
   report merger that reads a bold **FAIL** as no verdict, and whatever deleted the screenshots two
   lanes cited this run.

Two decisions are still waiting on you and neither can be made by a coder: whether the timing stamp
that is one quote too early should be corrected, and whether the corpus-truth photograph must show
your real 12-day corpus when the test rig can only ever show a two-day one. Please answer both
before new tape is recorded, since the recorder is what makes them matter.
