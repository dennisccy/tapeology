# goal-tape_to_profit-iter-8 Functional Test Plan

**Phase:** goal-tape_to_profit-iter-8  
**Date:** 2026-07-05  
**Frontend Present:** no

## Phase Goal

Deliver a read-only, deterministic baseline-edge report (`python -m app.research.edge_report --out <path>`) that measures the frozen `v1/default` champion's simulated hold-out edge across every registered dataset, ranks each dataset by hold-out edge, flags positive-edge datasets that meet the configured minimum-n threshold and beat their null baseline, and explicitly states "no positive-edge dataset" when none qualify.

## Test Cases

### TC-01 — Pure-Render Equality: Net R/USD/N Match Backend Aggregates

**Type:** api  
**Preconditions:** Backend is running; the champion pointer is set; at least one dataset is registered with a backtest completed.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. For each dataset result in the report, extract `net_r`, `net_usd`, `n`
3. Query `GET /research/backtests/{backtest_id}` for the corresponding backtest
4. Compare the report's displayed values against the `GET` response's `aggregates.net_r`, `aggregates.net_usd`, `aggregates.n`

**Expected outcome:** Every displayed R, USD, and N value matches its corresponding REST endpoint value byte-for-byte (no recomputation, pure read).

**Pass criteria:** 100% of checked values match exactly; zero drift between report and REST source.

---

### TC-02 — Train and Hold-Out Split Separation

**Type:** api  
**Preconditions:** Backend is running; at least two datasets registered (one train, one hold-out) with completed backtests.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. Parse the JSON and verify structure contains two top-level sections (e.g., `"train": [...], "holdout": [...]`)
3. Confirm no dataset appears in both sections
4. Count datasets in each section

**Expected outcome:** Train and hold-out datasets are in separate, never-pooled sections; no dataset appears in both.

**Pass criteria:** Exactly one dataset per section; zero pooled or averaged results; sections are distinct and non-overlapping.

---

### TC-03 — Deterministic Ranking Within Each Split

**Type:** api  
**Preconditions:** Backend is running; at least 3 datasets registered in the same split (train or hold-out) with completed backtests.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report_1.json` and save the ordering of datasets
2. Run again 5 seconds later: `python -m app.research.edge_report --out /tmp/test_report_2.json`
3. Compare dataset ordering in each split between the two runs
4. Verify the sort key (descending edge per dataset, tie-break ascending by `dataset_id`)

**Expected outcome:** Dataset order is identical across runs; the tie-break is deterministic (by `dataset_id` ascending).

**Pass criteria:** Zero differences in ordering; tie-break applied consistently; the sort is reproducible.

---

### TC-04 — Fixture Pair: No Positive-Edge Finding (n < minimum)

**Type:** api  
**Preconditions:** Backend is running with the committed fixture pair (train + hold-out, each n=1 per split, below the configured minimum of 5).

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. Parse the JSON and check for a `"positive_edge_datasets"` field or flag
3. Search for any dataset marked as positive-edge
4. Verify the report emits an explicit `"no positive-edge dataset"` message or summary field

**Expected outcome:** No dataset is flagged as positive-edge; the report explicitly states "no positive-edge dataset"; exit code is 0.

**Pass criteria:** Exit 0; zero positive-edge flags; explicit "no positive-edge dataset" text present; per-dataset values still shown (honest data, not omitted).

---

### TC-05 — Empty Registry: No Datasets Registered

**Type:** api  
**Preconditions:** Backend is running; the dataset registry is empty (zero datasets).

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. Verify the exit code
3. Check the JSON output for empty sections and a "no positive-edge dataset" message

**Expected outcome:** The report renders an honest empty state (empty sections or an explicit count of 0); exit 0; no fabricated data.

**Pass criteria:** Exit 0; JSON is valid; empty registry is explicitly handled; no synthesized edge or trades.

---

### TC-06 — Positive-Edge Flag: Controlled Test (BOTH Ways)

**Type:** api  
**Preconditions:** Backend is running; test infrastructure allows creating a controlled hold-out dataset with known edge (via test fixture or local test setup).

**Steps:**
1. Create or inject a hold-out dataset with champion backtest results: `net_r > 0`, `net_usd > 0`, `n >= 5` (meets minimum), and beats its seeded null baseline
2. Run `python -m app.research.edge_report --out /tmp/test_report.json`
3. Verify exactly one dataset is flagged as positive-edge
4. Then lower the minimum-n threshold in the test (via test-local config override or fixture) to 1
5. Re-run and verify the same dataset is still flagged (positive-edge flag proven BOTH ways)

**Expected outcome:** With minimum-n=5, the qualifying dataset is flagged; with minimum-n=1, the flag remains; the flag is deterministic and honesty-controlled, not arbitrary.

**Pass criteria:** Exactly one positive-edge dataset flagged in both scenarios; flag toggles correctly when minimum-n changes; no false positives or false negatives.

---

### TC-07 — Byte-Identical Re-Runs: Deterministic Output

**Type:** api  
**Preconditions:** Backend is running; the champion pointer and dataset registry are stable.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/run1.json`
2. Record the file's byte-hash (e.g., `sha256sum`)
3. Run again: `python -m app.research.edge_report --out /tmp/run2.json`
4. Record the byte-hash of the second file
5. Compare hashes and run `diff /tmp/run1.json /tmp/run2.json`

**Expected outcome:** Hashes are identical; no diff output; per-run-random fields (backtest report ids, wall-clock) are stripped before writing.

**Pass criteria:** Zero byte differences; identical hashes; deterministic JSON render (sorted keys).

---

### TC-08 — REGISTER String Attached to Every Dollar Figure

**Type:** api  
**Preconditions:** Backend is running with at least one dataset backtest completed.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. Parse the JSON and find all `net_usd` fields
3. For each `net_usd`, verify an adjacent `register` or `REGISTER` field is present with the simulated-results register string
4. Verify the null baseline also carries its `REGISTER` string

**Expected outcome:** Every dollar figure is accompanied by the `REGISTER` string (imported from `backtests.py`, never re-declared); null baseline has the same register.

**Pass criteria:** 100% of dollar figures have an attached register string; zero re-declarations; consistent across all results.

---

### TC-09 — Default-Engine Byte-Equivalence: Config Fingerprint Unchanged

**Type:** artifact  
**Preconditions:** Backend is running; `test_profile_equivalence.py` test suite exists and passes.

**Steps:**
1. Run the existing `test_profile_equivalence.py` test suite (or the specific test `test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field`)
2. Verify the founding PnL row's `config_fingerprint` equals `4d665603569b9dbf`
3. Check that `apps/backend/app/config.py` is unchanged (zero new config fields added)

**Expected outcome:** The fingerprint assertion passes; no config field was added by the edge_report module; byte-equivalence holds.

**Pass criteria:** Test passes green; fingerprint is `4d665603569b9dbf`; `git diff config.py` shows zero changes.

---

### TC-10 — Grep-Style Guard: No Execution Path in Module

**Type:** artifact  
**Preconditions:** Backend code is on disk; `apps/backend/app/research/edge_report.py` exists.

**Steps:**
1. Run `grep -n "set_champion_pointer\|append_validation_row\|broker\|order\|account" apps/backend/app/research/edge_report.py`
2. Verify zero matches (or only in comments/strings that are safe)
3. Run `grep -n "def set_champion_pointer\|def append_validation_row" apps/backend/tests/test_edge_report.py` to check the dedicated guard test exists

**Expected outcome:** `edge_report.py` contains no broker/order/account/execution code; it never calls `set_champion_pointer` or `append_validation_row`; it is strictly read-only.

**Pass criteria:** Zero unsafe matches in `edge_report.py`; guard test exists in `test_edge_report.py` and passes.

---

### TC-11 — Honest Failure: Corrupt Dataset or Non-Done Backtest

**Type:** api  
**Preconditions:** Backend is running; test infrastructure allows injecting a corrupt dataset or a backtest with non-`done` status.

**Steps:**
1. Create or inject a dataset that fails integrity verification
2. Run `python -m app.research.edge_report --out /tmp/test_report.json`
3. Verify the process exits with a non-zero code and an explicit error message
4. Confirm no `--out` file is written (or is empty/truncated)
5. Repeat with a backtest ending in a non-`done` state (e.g., `failed` or `cancelled`)

**Expected outcome:** The process aborts with an explicit error (via `EdgeReportError` or similar); nothing is written to `--out`; the failure is clear and honest, not silent or partial.

**Pass criteria:** Exit code is non-zero; error message names the issue (corrupt data, backtest not done); no partial/invalid output written.

---

### TC-12 — Missing Alpaca Credentials: Real-Feed Record Surfaces 503

**Type:** api  
**Preconditions:** Backend is running; a real-feed (Alpaca) record is attempted without credentials set in environment.

**Steps:**
1. Ensure `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` are not set
2. Run `python -m app.research.edge_report --out /tmp/test_report.json` (this should not attempt recording; reading already-registered datasets is keyless)
3. If a real-feed record is triggered by the test, verify the response is 503 "real-data provider unavailable"
4. Confirm no synthesized data is emitted

**Expected outcome:** Real-feed record attempts surface the existing 503 state; no credentials are required for reading already-stored backtests; no synthesized data.

**Pass criteria:** 503 or "unavailable" message appears; no synthesized trades or dataset; keyless read path works.

---

### TC-13 — Full Backend Suite Regression: Pass Count and Observer-Equivalence

**Type:** api  
**Preconditions:** Backend is running; the full test suite is available (pytest in CI mode).

**Steps:**
1. Run `pytest apps/backend/tests/ -v --tb=short` (or the configured test command from `.claude/project-template.md`)
2. Capture the full output and count passing/skipped/failed/regressed tests
3. Compare against the iter-7 baseline: at least 1025 passed, 1 skipped
4. Run the observer-equivalence test: `pytest apps/backend/tests/test_observer_equivalence.py -v`
5. Verify 7/7 observer checks pass

**Expected outcome:** Backend suite shows ≥1025 passed, no regressions below that floor; observer-equivalence stays green (7/7); no test deletions.

**Pass criteria:** Pass count ≥1025; observer-equivalence 7/7; zero regressions; required-still-passing journeys (J-01–J-08) remain green.

---

### TC-14 — Anti-Goal Zero-Diff: No Frontend/MCP/Goal Changes

**Type:** artifact  
**Preconditions:** Git repository is available; the branch contains the iteration's changes.

**Steps:**
1. Run `git diff --name-only | grep -E "^apps/frontend/|^apps/backend/app/mcp/|^docs/goal.md"`
2. Verify zero files match (no changes under those paths)
3. Run `git diff apps/backend/app/config.py` to verify config.py is untouched
4. Run `git diff docs/goal.md` to verify goal.md is unchanged by the backend work

**Expected outcome:** Zero diffs under frontend, MCP, or goal.md; the iteration is read-only and additive only (new `edge_report.py` and `test_edge_report.py`, no mutations).

**Pass criteria:** `git diff` shows zero changes in forbidden paths; `edge_report.py` and `test_edge_report.py` are new files only.

---

### TC-15 — Null Baseline Seeded Deterministically

**Type:** api  
**Preconditions:** Backend is running; the report contains null baseline results.

**Steps:**
1. Run `python -m app.research.edge_report --out /tmp/test_report.json`
2. Parse the JSON and find each dataset's null baseline entry
3. Extract the null baseline's `net_r`, `net_usd`, `n`, and any seed or rng state if exposed
4. Verify the seed is config-owned (from `Config.pnl_null_baseline_seed` or similar)
5. Run the report again and confirm the null baseline values are identical

**Expected outcome:** The null baseline is seeded by config; re-runs produce identical null results; the seed is deterministic, not random per invocation.

**Pass criteria:** Null baselines are identical across runs; seed is config-owned; zero per-run randomness.

---

## Summary

**Total test cases:** 15  
**API tests:** 12  
**Artifact checks:** 3  
**Backend-only phase:** No frontend/browser tests required.

### Test Case Mapping to DEFINITION OF DONE

- **TC-01**: Pure-render equality acceptance criterion
- **TC-02**: Train/hold-out split separation criterion
- **TC-03**: Deterministic ranking criterion
- **TC-04**: Fixture pair "no positive-edge dataset" acceptance
- **TC-05**: Empty registry honest handling criterion
- **TC-06**: Positive-edge flag proven BOTH ways criterion
- **TC-07**: Byte-identical re-runs criterion
- **TC-08**: REGISTER string attachment criterion
- **TC-09**: Default-engine byte-equivalence criterion
- **TC-10**: Grep-style guard no-execution criterion
- **TC-11**: Honest failure states criterion
- **TC-12**: Missing-credentials regression criterion
- **TC-13**: Backend suite regression + observer-equivalence criterion
- **TC-14**: Anti-goal zero-diff criterion
- **TC-15**: Null baseline determinism criterion

All test cases are derived from the phase spec's DEFINITION OF DONE, IN SCOPE, and TESTING REQUIREMENTS sections. No test cases require user interaction or browser automation (Frontend Present: no).
