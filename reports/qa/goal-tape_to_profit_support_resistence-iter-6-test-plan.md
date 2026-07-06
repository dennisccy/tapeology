# Goal Iteration 6 (J-06): Named-Strategy Comparison Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-6
**Date:** 2026-07-06
**Frontend Present:** no

## Phase Goal

Generalize the existing sweep (`pnl_scan.py`) to measure whether `structure_tape` beats the frozen `v1` champion on **held-out** data — and promote it to champion only if it survives hold-out at n ≥ minimum, while keeping the default profile and v1 strategy byte-identical and labelling train-only wins as overfit.

## Test Cases

### TC-01 — Named-strategy comparison report shape (train split)

**Type:** api
**Preconditions:** 
- Backend running with at least one registered training dataset
- `structure_tape` strategy registered
- `v1` champion pointer seeded in store

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --splits train --out /tmp/test-report-train.json`
2. Parse the JSON output file
3. Inspect the train-split report section

**Expected outcome:** 
Report contains per-dataset breakdown with:
- `structure_tape` net R, net $, n
- `v1` net R, net $, n
- Candidate-minus-champion deltas for net R and net $
- Dataset name and window for each row
- No pooling: each dataset is a separate row (never aggregated within train split)

**Pass criteria:** 
- JSON parses without error
- Train split section has ≥1 per-dataset row
- Each row has fields: `dataset`, `strategy_tape_R`, `strategy_tape_usd`, `strategy_tape_n`, `v1_R`, `v1_usd`, `v1_n`, `delta_R`, `delta_usd`
- No null/missing values in any required field

---

### TC-02 — Named-strategy comparison report shape (hold-out split)

**Type:** api
**Preconditions:**
- Backend running with at least one registered hold-out dataset
- `structure_tape` strategy registered
- `v1` champion pointer seeded in store

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --splits hold_out --out /tmp/test-report-holdout.json`
2. Parse the JSON output file
3. Inspect the hold-out-split report section

**Expected outcome:**
Report contains per-dataset breakdown with:
- `structure_tape` net R, net $, n
- `v1` net R, net $, n
- Candidate-minus-champion deltas for net R and net $
- Train and hold-out splits are separate (never pooled)

**Pass criteria:**
- JSON parses without error
- Hold-out split section has ≥1 per-dataset row
- Each row has all required fields (same as TC-01)
- Train and hold-out sections are structurally distinct (not merged)

---

### TC-03 — Survivor gate: below-min-n hold-out win marked NOT survivor

**Type:** api
**Preconditions:**
- Backend running with synthetic fixture that has:
  - Train: positive `structure_tape` edge (cumulative delta > 0)
  - Hold-out: `structure_tape` also positive but n < `Config.promotion_min_sample_size`

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-below-min.json`
2. Parse output
3. Check survivor flag and overfit flag in the report

**Expected outcome:**
- `survivor` = false
- `overfit` = false (positive train AND failing hold-out would be true; positive train AND below-min n IS a non-survivor case, labeled clearly)
- Report still fully rendered with all per-split data

**Pass criteria:**
- `survivor` field in report is exactly `false`
- Comparison metrics are present and valid
- Champion pointer remains unchanged (no write to store)
- Exit code 0

---

### TC-04 — Survivor gate: at/above-min-n positive hold-out win IS survivor

**Type:** api
**Preconditions:**
- Backend running with synthetic fixture that has:
  - Train: positive `structure_tape` edge
  - Hold-out: positive `structure_tape` edge AND n ≥ `Config.promotion_min_sample_size`

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-above-min.json`
2. Parse output
3. Check survivor flag

**Expected outcome:**
- `survivor` = true
- `overfit` = false
- Promotion occurs (ledger row appended, champion pointer moved to `strategy_id=structure_tape`)

**Pass criteria:**
- `survivor` field in report is exactly `true`
- New row in `GET /research/pnl/ledger` with `enhancement_id` naming the strategy promotion
- `GET /research/profiles` and `GET /research/strategies` show champion pointer moved to `strategy_tape`
- Exit code 0

---

### TC-05 — Overfit: positive train + failing hold-out marked overfit, NOT promoted

**Type:** api
**Preconditions:**
- Backend running with synthetic fixture that has:
  - Train: positive `structure_tape` edge
  - Hold-out: negative `structure_tape` edge (worse than `v1`)

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-overfit.json`
2. Parse output
3. Check survivor, overfit flags and store state

**Expected outcome:**
- `survivor` = false
- `overfit` = true
- Report labels this case as overfit
- No promotion (champion unchanged, no ledger row)

**Pass criteria:**
- `survivor` is false, `overfit` is true (both explicit in report)
- Champion pointer still points to `{v1, default}`
- No new row in PnL ledger
- Exit code 0

---

### TC-06 — Promotion correctness: exactly one ledger row, then pointer moves

**Type:** api
**Preconditions:**
- Backend running with synthetic ≥-min-n survivor fixture
- Store has clean state (champion at `{v1, default}`)
- PnL ledger is empty or known state

**Steps:**
1. Record ledger row count: `curl -s http://localhost:8000/research/pnl/ledger | jq '.rows | length'`
2. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-promotion.json`
3. Re-check ledger row count
4. Get champion pointer: `curl -s http://localhost:8000/research/profiles | jq '.champion_pointer'`

**Expected outcome:**
- Ledger row count increased by exactly 1
- New ledger row has `enhancement_id` like `"structure_tape-over-v1"`
- Champion pointer's `strategy_id` is now `"structure_tape"`
- Champion pointer's `profile` is still `"default"` (only strategy axis moved)

**Pass criteria:**
- Ledger rows += 1
- New row has all required fields (strategy, profile, dates, net R, net $, n, train/hold-out, survivor flag)
- Champion pointer: `strategy_id == "structure_tape"` AND `profile == "default"`
- Exit code 0

---

### TC-07 — Promotion crash-safety: mid-promotion re-run hits DuplicateEnhancementError

**Type:** api
**Preconditions:**
- Backend running with synthetic ≥-min-n survivor fixture
- Previous TC-06 promotion completed (champion now at `{structure_tape, default}`)

**Steps:**
1. Run the same sweep again: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-duplicate.json`
2. Check exit code and error output

**Expected outcome:**
- CLI detects that an identical `enhancement_id` was already promoted
- Raises explicit `ScanError` / `DuplicateEnhancementError`
- Nothing is written a second time

**Pass criteria:**
- Exit code non-zero (error exit)
- Error message names `DuplicateEnhancementError` or explicit duplicate-detection logic
- No second row in ledger (still the same count as after TC-06)
- No pointer move (still at `{structure_tape, default}`)

---

### TC-08 — Frozen foundation after promotion: fingerprint, v1, default byte-identical

**Type:** api
**Preconditions:**
- Promotion completed (champion now at `{structure_tape, default}`)

**Steps:**
1. Get config fingerprint: `python -c "from app.config import Config; print(Config.config_fingerprint())"`
2. Run engine equivalence test: `pytest apps/backend/tests/test_profile_equivalence.py -v`
3. Verify `v1` strategy bytes: backtest `v1` on a fixture, record net R and $
4. Verify `default` profile bytes: run two identical backtests, compare outputs byte-for-byte

**Expected outcome:**
- Config fingerprint is still `"4d665603569b9dbf"` (unchanged)
- Engine equivalence test passes (v1 and default produce same results as baseline)
- v1 strategy backtests are deterministic (two runs = identical bytes)
- default profile produces no new fields or altered computations

**Pass criteria:**
- Fingerprint == `"4d665603569b9dbf"`
- `test_profile_equivalence.py` exit code 0
- Two v1 backtests produce identical `--out` JSON (byte-identical hashes)
- No config mutations present

---

### TC-09 — Fixture honesty: committed train/hold-out pair → no survivor, champion unchanged

**Type:** api
**Preconditions:**
- Backend running with committed PG train/hold-out fixture pair
- Champion at `{v1, default}` (baseline state)

**Steps:**
1. Run the sweep on the committed fixtures: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-fixture-honest.json`
2. Parse the report
3. Check champion pointer: `curl -s http://localhost:8000/research/profiles | jq '.champion_pointer.strategy_id'`
4. Check ledger row count (should be unchanged)

**Expected outcome:**
- Report's `survivor` flag = false
- Report notes that hold-out n is below `promotion_min_sample_size`
- Exit code 0
- Champion pointer still at `strategy_id: "v1"`
- No new ledger row

**Pass criteria:**
- `survivor` == false
- Hold-out n < `Config.promotion_min_sample_size` (fixture detail visible in report or via inspection)
- Exit code 0
- Champion unchanged
- Ledger unchanged

---

### TC-10 — Deterministic re-runs: byte-identical `--out` on committed fixtures

**Type:** api
**Preconditions:**
- Backend running with committed fixtures
- Both runs from clean state

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/run1.json`
2. Capture hash: `sha256sum /tmp/run1.json`
3. Run again: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/run2.json`
4. Capture hash: `sha256sum /tmp/run2.json`
5. Compare hashes

**Expected outcome:**
- Both hashes are identical
- JSON content is byte-identical (same sort order, no timestamps, deterministic)

**Pass criteria:**
- sha256 hashes match exactly
- No per-run randomness, no wall-clock fields in report

---

### TC-11 — Backward compatibility: no `--strategy` flag behaves byte-identically

**Type:** api
**Preconditions:**
- Backend running with existing test fixtures
- A pre-recorded baseline of the profile-only sweep output (from before this change)

**Steps:**
1. Run profile-only sweep (no `--strategy` flag): `python apps/backend/app/research/pnl_scan.py --out /tmp/profile-only.json`
2. Compare to baseline output from before the generalization

**Expected outcome:**
- `--out` is byte-identical to the pre-change baseline
- Profile axis behaves the same (loops over all profiles)
- All per-split summaries match

**Pass criteria:**
- sha256 hash matches the baseline (or diff shows only whitespace/order changes that are immaterial)
- All profile candidates in the report
- Exit code 0

---

### TC-12 — Single-source scan: champion pointer setter called from one file only

**Type:** artifact
**Preconditions:**
- Codebase checked out

**Steps:**
1. Grep for calls to `store.set_champion_pointer`: `grep -r "set_champion_pointer" apps/backend --include="*.py" | grep -v test | grep -v "def set_champion_pointer"`
2. Identify all non-test, non-definition call sites

**Expected outcome:**
- Exactly one call site in production code (in `pnl_scan.py`'s promotion logic)
- No second implementation path for moving the champion

**Pass criteria:**
- Only one production file calls `set_champion_pointer` (and it's `pnl_scan.py`)
- No second net R/$/edge computation path introduced

---

### TC-13 — Unknown candidate strategy id → explicit refusal

**Type:** api
**Preconditions:**
- Backend running

**Steps:**
1. Run with invalid strategy id: `python apps/backend/app/research/pnl_scan.py --strategy unknown_strategy --out /tmp/test-unknown.json`
2. Check exit code and output

**Expected outcome:**
- CLI raises explicit error (not a coerced/fabricated comparison)
- Error message names the unknown strategy
- Exit code non-zero

**Pass criteria:**
- Exit code != 0
- Error message contains strategy id or "strategy not found" or similar
- No report file written (or empty report with error note)

---

### TC-14 — Error case: corrupt dataset → explicit ScanError, nothing written

**Type:** api
**Preconditions:**
- Backend running with a dataset marked as corrupt or non-`done` status

**Steps:**
1. Manually mark a dataset as `status != done` in the research store
2. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-corrupt.json`
3. Check exit code and output

**Expected outcome:**
- CLI raises explicit `ScanError`
- No promotion occurs
- No ledger row written

**Pass criteria:**
- Exit code non-zero
- Error message names the dataset or status issue
- Champion unchanged
- No ledger row added

---

### TC-15 — More than one train/hold-out dataset → promotion skipped, comparison reported

**Type:** api
**Preconditions:**
- Backend running with ≥2 train datasets and/or ≥2 hold-out datasets
- All datasets have valid backtests for both strategies

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-multi-dataset.json`
2. Parse report

**Expected outcome:**
- Report includes per-dataset comparison for all datasets
- But promotion is skipped (no ledger row, no pointer move)
- Report explicitly notes "multiple train/hold-out datasets; promotion skipped"
- Exit code 0

**Pass criteria:**
- Report is complete and per-dataset rows present
- `survivor` == false (or explicit note)
- Champion unchanged
- No ledger row written

---

### TC-16 — Audit B1 disclosed: breakthrough arm assumptions in report provenance

**Type:** artifact
**Preconditions:**
- Backend running
- Sweep produces a report

**Steps:**
1. Run: `python apps/backend/app/research/pnl_scan.py --strategy structure_tape --out /tmp/test-b1-disclosure.json`
2. Parse JSON and look for provenance/assumptions section
3. Search report for text naming "breakthrough," "static," "price-position," or "anchor"

**Expected outcome:**
- Report includes a provenance or assumptions section
- That section explicitly names the breakthrough arm as a "static price-position test" or similar
- Caveat is visible to any reader of the report

**Pass criteria:**
- Provenance section exists
- Mentions breakthrough or arm assumptions
- Text is clear enough for a human to understand the loose-anchor caveat

---

### TC-17 — No execution path: no broker/order/routing identifier in new code

**Type:** artifact
**Preconditions:**
- Codebase checked out

**Steps:**
1. Run grep-guard test: `pytest apps/backend/tests/test_no_execution_path.py -v`
2. Specifically check for new assertions that cover the strategy-axis comparison/promotion code

**Expected outcome:**
- Test passes
- New test explicitly names the comparison/promotion code paths (e.g., "pnl_scan named-strategy path")
- No broker/order/execution/paper-trading identifiers found in those paths

**Pass criteria:**
- `test_no_execution_path.py` exit code 0
- Test log shows coverage of the named-strategy branch
- No forbidden keywords in the diff

---

### TC-18 — Full regression: J-01–J-05 and J-07 remain green

**Type:** api
**Preconditions:**
- Backend fully built and tests run

**Steps:**
1. Run full backend test suite: `pytest apps/backend/tests/ -v`
2. Check exit code
3. Run engine equivalence test: `pytest apps/backend/tests/test_profile_equivalence.py -v`
4. Run full journey validation if available

**Expected outcome:**
- All tests pass
- No regressions in pre-existing journeys
- J-07 cockpit surface unchanged (frontend diff is empty)

**Pass criteria:**
- Backend test suite exit code 0
- Profile equivalence test exit code 0
- No new failures compared to baseline
- Frontend diff is empty (zero changes to `apps/frontend/`)

---

## Summary

**Total test cases:** 18
- **API tests:** 14 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-13, TC-14, TC-15)
- **Artifact tests:** 4 (TC-12, TC-16, TC-17, TC-18)

**Key acceptance criteria:**
- Named-strategy comparison report fully structured per split (TC-01, TC-02)
- Survivor gate enforced on hold-out AND minimum n (TC-03, TC-04)
- Overfit detected and rejected (TC-05)
- Promotion is crash-safe and single-source (TC-06, TC-07, TC-12)
- Frozen foundation (fingerprint, v1, default) unchanged (TC-08)
- Fixture honestly yields no survivor (TC-09)
- Determinism (TC-10)
- Backward compatibility (TC-11)
- Error cases handled explicitly (TC-13, TC-14, TC-15)
- Audit B1 disclosed (TC-16)
- No execution path (TC-17)
- Full regression green (TC-18)
