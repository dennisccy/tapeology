# goal-tape_to_profit-iter-7 Functional Test Plan

**Phase:** goal-tape_to_profit-iter-7  
**Date:** 2026-07-03  
**Frontend Present:** no

## Phase Goal

Ship the candidate-sweep harness (`python -m app.research.pnl_scan --out <path>`) so researchers can evaluate every registered candidate against the champion over train datasets, validate apparent winners on the frozen hold-out set, and—only for a genuine hold-out survivor—promote it by appending one honest PnL-ledger row and moving the champion pointer, while zero survivors is an explicit, honest, exit-0 outcome.

## Test Cases

### TC-01 — Fixture sweep yields zero survivors with champion unmoved

**Type:** api  
**Preconditions:** Backend running; committed fixture datasets loaded; `candidate-faster-warmup` registered; champion pointer persisted at `v1/default`; default fingerprint `4d665603569b9dbf` in pinned store.

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/scan_report_fixture.json`
2. Check exit code and report file existence
3. Parse report JSON; verify `candidate-faster-warmup` in candidates list
4. Verify train + hold-out net R/$ deltas recorded per candidate; verify n per split
5. Verify `survivor: false` for `candidate-faster-warmup` (hold-out net R negative, n < minimum)
6. Verify `overfit` label present (train-positive/hold-out-negative)
7. Call `GET /research/profiles` and verify champion is still `{strategy_id: v1, profile: default}`
8. Query ledger row count via `GET /research/pnl/ledger` and verify count == 1 (founding row only)
9. Verify default fingerprint in founding ledger row still equals `4d665603569b9dbf`

**Expected outcome:** Sweep completes cleanly with exit code 0; report documents the candidate as non-survivor/overfit; champion pointer and ledger remain unmodified; default fingerprint is unchanged.

**Pass criteria:** Exit code is 0; `survivor: false` and `overfit: true` in report for `candidate-faster-warmup`; `GET /research/profiles` champion remains `v1/default`; ledger row count unchanged; default fingerprint hash equals `4d665603569b9dbf`.

---

### TC-02 — Scan report contains required fields per candidate

**Type:** artifact  
**Preconditions:** Fixture sweep (TC-01) has run; report file exists at known path.

**Steps:**
1. Parse `/tmp/scan_report_fixture.json` as JSON
2. For `candidate-faster-warmup`, verify presence of fields: `candidate_id`, `train_net_r`, `train_net_$`, `holdout_net_r`, `holdout_net_$`, `n_train`, `n_holdout`, `per_dataset_breakdown`, `survivor`, `robustness`, `overfit`
3. Verify `robustness` is either `"robust"` or `"speculative"` (not null/missing)
4. Verify `per_dataset_breakdown` is a non-empty list with `dataset_id`, `split` (train/holdout), `net_r`, `net_$`, `n` per item

**Expected outcome:** Report structure matches the schema: per-candidate arrays with all required fields present and populated.

**Pass criteria:** All required fields present in report JSON; `robustness` has valid enum value; `per_dataset_breakdown` is non-empty array with correct structure.

---

### TC-03 — Determinism: identical scans produce byte-identical reports

**Type:** api  
**Preconditions:** Backend running; same fixture datasets; RNG seeds fixed throughout.

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/scan_1.json`
2. Run `python -m app.research.pnl_scan --out /tmp/scan_2.json` (identical command, fresh state)
3. Compare file bytes: `cmp /tmp/scan_1.json /tmp/scan_2.json` or equivalent
4. Verify no wall-clock/timestamp fields in the report that would differ between runs

**Expected outcome:** Two independent fresh-state runs produce byte-identical output files.

**Pass criteria:** Exit code 0 for both runs; file byte comparison shows no differences; both reports identical when parsed as JSON.

---

### TC-04 — Min-n gate enforced: below-minimum candidate rejected despite positive hold-out net R/$

**Type:** api  
**Preconditions:** Test fixture or modified config with `promotion_min_sample_size = 3` (or via dataclass replace); candidate with positive hold-out R and $ but n < 3 on hold-out.

**Steps:**
1. Create or select a test dataset/candidate scenario where hold-out net R > 0, net $ > 0, but n_holdout < 3
2. Run `python -m app.research.pnl_scan --out /tmp/scan_min_n.json` with this scenario
3. Parse report; find the candidate and verify `survivor: false` even though hold-out metrics are positive
4. Verify `GET /research/profiles` champion unchanged (not promoted)
5. Verify ledger row count unchanged

**Expected outcome:** Candidate is rejected as non-survivor despite positive hold-out performance because n < configured minimum.

**Pass criteria:** `survivor: false` in report; champion pointer unmodified; ledger count unchanged; exit code 0.

---

### TC-05 — Min-n gate enforced: at-or-above-minimum survivor promoted

**Type:** api  
**Preconditions:** Test scenario where candidate has hold-out net R > 0, net $ > 0, and n_holdout >= configured minimum (e.g., n=5); champion pointer and ledger initially unchanged.

**Steps:**
1. Set up test fixture or use modified config with lowered threshold or enlarged dataset windows to arm n >= minimum
2. Run `python -m app.research.pnl_scan --out /tmp/scan_survivor.json`
3. Parse report; verify `survivor: true` for the candidate
4. Verify exactly one new PnL-ledger row was appended via `GET /research/pnl/ledger`; verify row count increased by 1
5. Call `GET /research/profiles` and verify champion pointer moved to the new candidate's strategy/profile
6. Verify appended ledger row is stamped with `dataset_ids`, `checksums`, `strategy_config`, `profile_id`, `config_fingerprint`; verify `config_fingerprint` matches the baseline default (no engine defaults mutated)

**Expected outcome:** Survivor candidate is promoted; champion pointer moves; exactly one ledger row appended with full provenance.

**Pass criteria:** `survivor: true` in report; ledger row count increased by 1; `GET /research/profiles` champion reflects the new candidate; appended row has provenance fields; default fingerprint unchanged; exit code 0.

---

### TC-06 — Robustness classification: robust iff positive on every train dataset

**Type:** api  
**Preconditions:** Test scenarios with candidates showing different train-dataset performance patterns.

**Steps:**
1. Scenario A: candidate with positive net R/$ on every individual train dataset → expect `robustness: "robust"`
2. Scenario B: candidate with positive overall train aggregate but negative on at least one individual dataset → expect `robustness: "speculative"`
3. Run scans for both and parse reports
4. Verify each candidate's `robustness` field matches expected classification

**Expected outcome:** Robustness is correctly labeled based on per-dataset performance, not just aggregates.

**Pass criteria:** Scenario A shows `robustness: "robust"`; Scenario B shows `robustness: "speculative"`; classifications match the spec rule.

---

### TC-07 — Overfit labeling: train-positive/hold-out-negative never promoted

**Type:** api  
**Preconditions:** Fixture scenario where `candidate-faster-warmup` has positive train net R/$ but negative hold-out net R/$.

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/scan_overfit.json`
2. Parse report; find `candidate-faster-warmup` and verify `overfit: true`
3. Verify `survivor: false` (even though train is positive)
4. Verify `GET /research/profiles` champion is still `v1/default`
5. Verify ledger row count unchanged

**Expected outcome:** Overfit candidate is labeled and rejected; no promotion occurs.

**Pass criteria:** `overfit: true` in report; `survivor: false`; champion unmoved; ledger unchanged; exit code 0.

---

### TC-08 — Honest empty outcome: zero registered candidates → exit 0

**Type:** api  
**Preconditions:** Test scenario with no registered candidates (only default profile, no non-default profiles).

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/scan_empty.json`
2. Verify exit code is 0
3. Parse report and verify it contains an explicit message or field indicating zero candidates (e.g., `candidates: []`)
4. Verify champion unchanged, ledger unchanged

**Expected outcome:** Clean exit with explicit "no candidates" report; no state mutations.

**Pass criteria:** Exit code 0; report indicates zero candidates explicitly; champion and ledger unchanged.

---

### TC-09 — Honest failure: corrupt dataset → explicit error, no partial write

**Type:** api  
**Preconditions:** A test dataset file corrupted (truncated JSON, invalid checksum, unreadable).

**Steps:**
1. Configure test to reference a corrupted dataset
2. Run `python -m app.research.pnl_scan --out /tmp/scan_corrupt.json`
3. Verify exit code is non-zero (error)
4. Verify error message is explicit (e.g., mentions checksum mismatch or parse failure)
5. Verify ledger row count unchanged; champion unchanged (no partial write)

**Expected outcome:** Explicit error on corrupt dataset; no silent data loss or partial state updates.

**Pass criteria:** Exit code non-zero; error message is specific and actionable; no ledger rows appended; champion unmoved.

---

### TC-10 — Single-source champion: profiles.py reads from persisted pointer only

**Type:** artifact  
**Preconditions:** Source code review; profiles.py reviewed.

**Steps:**
1. Search `app/research/profiles.py` for the hardcoded constant `STRATEGY_V1_ID` and `PROFILE_DEFAULT`
2. Verify they are NO LONGER used directly at serve time (only as seed/default values on schema/migration)
3. Verify `profiles_projection()` reads champion from the persisted store pointer (via `JournalStore.get_champion()` or equivalent)
4. Verify `GET /research/profiles` route passes `registry.store` into the function
5. Source-scan test: grep for all calls to the champion-pointer setter (e.g., `store.set_champion()` or `pnl_scan.py` only)

**Expected outcome:** Single persisted source of truth for the champion pointer; no divergence between hardcoded constant and stored value.

**Pass criteria:** Constants no longer used at serve time; `profiles_projection()` reads from store; setter called only from `pnl_scan.py`; source-scan test passes.

---

### TC-11 — Promotion is two writes with explicit failure discipline

**Type:** api  
**Preconditions:** Controlled survivor scenario (TC-05); ability to simulate mid-promotion failure (e.g., via transaction mock or deliberate exception).

**Steps:**
1. Mock or simulate the scenario where champion-pointer move completes but ledger append fails
2. Run promotion and allow the failure to occur
3. Verify state afterward: champion either moved or unmoved (consistent), not half-moved; ledger either unchanged or has the new row, not orphaned
4. Repeat with opposite order: ledger append succeeds, then champion-pointer move fails
5. Verify explicit error is raised; state remains consistent (champion+ledger pair is either old or new, never mixed)

**Expected outcome:** No silent half-applied state; failures are caught and explicitly surfaced.

**Pass criteria:** After any failure, champion and ledger are in a consistent state (both old or both new); error message is explicit; no orphaned rows or stale pointers.

---

### TC-12 — Store unavailable during promotion → explicit failure, no orphan

**Type:** api  
**Preconditions:** Store connection failure mid-promotion (simulate database unavailability).

**Steps:**
1. Set up controlled survivor scenario
2. Inject a failure into the store write (e.g., mock the SQLite connection to raise an exception)
3. Run promotion and catch the exception
4. Verify champion pointer unchanged, ledger row count unchanged (no partial write)
5. Verify error is explicit (not a silent retry or cached value)

**Expected outcome:** Store unavailability is surfaced as a clean error; no partial mutations.

**Pass criteria:** Exit code non-zero; champion and ledger both unchanged; error message explicitly mentions store/database unavailability.

---

### TC-13 — Backend suite and equivalence test remain green

**Type:** api  
**Preconditions:** Full backend test suite setup.

**Steps:**
1. Run full backend suite: `pytest apps/backend/tests/ -v`
2. Verify pass count >= iter-6 baseline (1004 passed / 1 skipped)
3. Verify no test deletions (count == previous count or higher)
4. Run equivalence test: `pytest apps/backend/tests/test_observer_equivalence.py -v`
5. Verify all 7 observer-equivalence cases pass

**Expected outcome:** Full test suite passes with no regressions; equivalence test confirms default behavior unchanged.

**Pass criteria:** Backend suite pass count >= 1004; no test deletions; equivalence 7/7 pass; default fingerprint `4d665603569b9dbf` verified in test assertions.

---

### TC-14 — test_no_execution_path.py extended to cover pnl_scan.py

**Type:** artifact  
**Preconditions:** test_no_execution_path.py reviewed.

**Steps:**
1. Open `apps/backend/tests/test_no_execution_path.py`
2. Verify that `test_scan_is_not_vacuous` (or equivalent) includes `"backend/app/research/pnl_scan.py"` in the explicit path assertions list
3. Run the test: `pytest apps/backend/tests/test_no_execution_path.py -v`
4. Verify no execution/broker/order/paper-trading code is found in pnl_scan.py

**Expected outcome:** pnl_scan.py is explicitly scanned and passes the no-execution-path gate.

**Pass criteria:** Test file includes `pnl_scan.py` in assertions; test passes; no broker/order/trading imports or calls found.

---

### TC-15 — CLI entry point `python -m app.research.pnl_scan` with --out argument

**Type:** api  
**Preconditions:** Backend running; test datasets available.

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/test_output.json` from the `apps/backend` directory
2. Verify exit code is 0
3. Verify `/tmp/test_output.json` is created and is valid JSON
4. Verify `--help` displays usage information
5. Test without `--out`: expect explicit error or usage message

**Expected outcome:** CLI is executable and handles arguments correctly.

**Pass criteria:** Command runs without error; report file created; JSON is well-formed; help text present; error on missing argument.

---

### TC-16 — Required-still-passing journeys remain green: J-01/J-05/J-08 via golden replay

**Type:** api  
**Preconditions:** Golden replay infrastructure available; MCP server running.

**Steps:**
1. Run golden replay for J-01 (MCP byte-identity); verify tool outputs match curl
2. Run golden replay for J-05 (/performance page renders profiles verbatim); verify champion reflects persisted pointer
3. Run golden replay for J-08 (regression sentinel); verify archived surfaces unchanged, equivalence test passes
4. Verify each replay captures a result row (not just merge header)

**Expected outcome:** All three golden replays pass; no regressions in existing journeys.

**Pass criteria:** J-01, J-05, J-08 replays all pass; per-journey result rows present; equivalence test 7/7 pass.

---

### TC-17 — Live pnl_scan run via in-page fetch (machine-surface verification for J-07)

**Type:** api  
**Preconditions:** Backend running; a test page with fetch() capability (or CLI invocation).

**Steps:**
1. Run `python -m app.research.pnl_scan --out /tmp/j07_live.json` via CLI from the repo root
2. Parse output and verify all DoD criteria: fixture sweep → zero survivors, exit 0, champion unmoved, ledger count 1, default fingerprint `4d665603569b9dbf`
3. Verify no golden replay script exists for J-07 (per the iter-2 lesson)
4. Verify test suite captures this CLI run as the durable regression test

**Expected outcome:** J-07 is verified via live CLI execution plus backend suite coverage; no golden replay script needed.

**Pass criteria:** Live CLI run exits 0; all fixture-sweep assertions pass; backend suite includes J-07 test cases; exit code and report structure correct.

---

## Summary

**Total test cases:** 17

**API tests:** 12 (TC-01, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-13, TC-15, TC-16, TC-17)

**Artifact checks:** 5 (TC-02, TC-10, TC-11, TC-12, TC-14)

**Backend-only phase:** No browser tests required.

**External integrations:** None; all tests run keyless against committed fixture datasets.

**Critical assertions:**
- Fixture sweep yields zero survivors with champion unmoved and ledger unchanged
- Min-n gate enforced both ways (below-min rejected, at-or-above-min positive candidate promoted)
- Robustness and overfit labeling correct per spec
- Determinism: byte-identical re-runs
- Single-source champion pointer; no partial writes on failure
- Backend suite and equivalence test remain green (no regressions)
- J-07 verified via live CLI run plus backend suite; no golden replay
