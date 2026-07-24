# goal-clean_slate-iter-4 Functional Test Plan

**Phase:** goal-clean_slate-iter-4
**Date:** 2026-07-24
**Frontend Present:** no

## Phase Goal

Execute the §0.4 Path B fingerprint epoch bump: delete 23 orphaned journal-era Config fields, update the config fingerprint to a new value at all 13 verified pin sites, re-seed the founding baseline under the new epoch, and verify every kept research value serves byte-identical results under the new fingerprint stamp.

## Test Cases

### TC-01 — Config field deletion correctness

**Type:** artifact
**Preconditions:** `apps/backend/app/config.py` has been edited to delete 23 fields and leave 5 others untouched.

**Steps:**
1. Run `python -c "from app.config import Config; import dataclasses; print(sorted(f.name for f in dataclasses.fields(Config)))"` (cwd: `apps/backend`)
2. Scan output for the 23 deleted fields: `verdict_dwell_seconds`, `invalidation_epsilon_spread_multiple`, `verdict_timeline_cap`, `management_stance_dwell_seconds`, `checklist_stance_dwell_seconds`, `delivery_lag_ok_bound_seconds`, `excursion_horizons_seconds`, `excursion_target_r`, `study_null_arm_count`, `study_null_baseline_seed`, `study_list_max`, `hint_sustain_dwell_seconds`, `hint_cooldown_seconds`, `hint_log_max`, `invalidation_k_consecutive`, `journal_list_default_limit`, `journal_list_max_limit`, `chase_return_threshold`, `invalidation_too_tight_spread_multiple`, `process_outcome_grade_map`, `process_violated_min_failed_checks`, `process_flagged_min_risk_flags`, `sound_cue_cooldown_seconds`
3. Scan output for the 5 fields that must still be present: `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`, `analytics_min_sample_size`

**Expected outcome:** All 23 deleted field names are absent from the output; all 5 protected fields are present.
**Pass criteria:** `grep` of the output contains zero matches for any of the 23 deleted names AND contains all 5 of the protected field names.

---

### TC-02 — Strategy definition still reads study fields

**Type:** api
**Preconditions:** The 4 study_* fields have been left untouched in Config, and `Config.strategy_definition()` is unmodified.

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/test_backtests.py -q`
3. Inspect test output for pass/fail count

**Expected outcome:** Test suite passes with 0 failed, proving that `Config.strategy_definition()` still reads `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, and `study_occurrence_r_floor` correctly, and that `backtests.py:225` still reads the R-stop formula fields.
**Pass criteria:** Exit code 0, output shows 0 failed (exact count of passed tests may vary).

---

### TC-03 — Exclusion set pruned correctly

**Type:** artifact
**Preconditions:** `config_fingerprint()` method in `apps/backend/app/config.py` has been edited to prune the exclusion set.

**Steps:**
1. Open `apps/backend/app/config.py` and locate the `config_fingerprint()` method
2. Count the number of entries in the `excluded = {...}` dictionary literal
3. Verify that exactly these 8 entries were removed: `checklist_stance_dwell_seconds`, `delivery_lag_ok_bound_seconds`, `hint_log_max`, `journal_list_default_limit`, `journal_list_max_limit`, `management_stance_dwell_seconds`, `sound_cue_cooldown_seconds`, `study_list_max`
4. Verify each remaining entry names a field still present on Config

**Expected outcome:** The `excluded` set contains exactly 40 entries (down from 48); all 8 named entries are gone; every remaining entry is a still-live Config field.
**Pass criteria:** Count equals 40 AND all 8 removed names are absent from the set AND every remaining name is a live Config field (verify via `dataclasses.fields(Config)`).

---

### TC-04 — New fingerprint pin computed once

**Type:** api
**Preconditions:** `apps/backend/app/config.py` has the 23 deletions, 8-entry exclusion-set prune, and enhancement-id/title value bump all in place in a single commit state.

**Steps:**
1. cd `apps/backend`
2. Run `python -c "from app.config import Config; print(Config().config_fingerprint())"`
3. Record the printed value

**Expected outcome:** A single new fingerprint string is printed; it must not be `4d665603569b9dbf` (the old epoch pin).
**Pass criteria:** Output is a 32-character hexadecimal string, is not equal to `4d665603569b9dbf`, and is stable across repeated runs.

---

### TC-05 — All 13 pin sites updated to new fingerprint

**Type:** artifact
**Preconditions:** The 13 assertion sites in test files have been updated to the new fingerprint from TC-04.

**Steps:**
1. cd `apps/backend`
2. Run `grep -rn "4d665603569b9dbf" tests/*.py`
3. Record all results

**Expected outcome:** The grep returns zero hits (the old pin value is completely retired from test files).
**Pass criteria:** Exit code 0, no output (empty result set).

---

### TC-06 — Old fingerprint absent from apps/ directory

**Type:** artifact
**Preconditions:** A new test has been added asserting the old literal is absent under `apps/`.

**Steps:**
1. cd `/home/dennis-chan/Git/tapeology`
2. Run the new test (e.g., `pytest tests/test_fingerprint_epoch_retirement.py -v`)
3. Observe test output

**Expected outcome:** Test passes, confirming the old literal `4d665603569b9dbf` appears nowhere under `apps/` (code + tests); `reports/**`, `runs/**`, `docs/goal-archive/**` are exempt as read-only history.
**Pass criteria:** Exit code 0, test marked as PASSED.

---

### TC-07 — New PnL founding row appended via CLI

**Type:** api
**Preconditions:** `Config.pnl_founding_enhancement_id` and `pnl_founding_enhancement_title` have been bumped to new literal values; `python -m app.research.pnl_baseline` is ready to run against the real operator journal DB.

**Steps:**
1. cd `apps/backend`
2. Run `python -m app.research.pnl_baseline`
3. Capture stdout and observe for the "founding baseline row appended" message
4. Run `curl -s http://localhost:8000/research/pnl/ledger | python -m json.tool` to fetch the ledger
5. Count the number of rows in the ledger

**Expected outcome:** stdout prints `founding baseline row appended: '<new-id>' ...` (created=True, NOT "already present"); the `GET /research/pnl/ledger` response contains exactly 2 rows: the original (old id, old fingerprint `4d665603569b9dbf`, byte-unchanged payload) and the new one (new id, the new fingerprint from TC-04).
**Pass criteria:** stdout contains "founding baseline row appended" and does not contain "already present"; ledger endpoint returns JSON with 2 rows array; first row's `enhancement_id` is the old id; second row's `enhancement_id` is the new id; first row's fingerprint is `4d665603569b9dbf`; second row's fingerprint matches TC-04's new pin.

---

### TC-08 — Founding datasets reuse existing registration (rail 9)

**Type:** api
**Preconditions:** The founding reference datasets were already registered by the original pre-demolition seeding run; `python -m app.research.pnl_baseline` is about to be run.

**Steps:**
1. cd `apps/backend`
2. Before running pnl_baseline, capture the current registered-dataset count via `curl -s http://localhost:8000/research/datasets | python -m json.tool | grep -c '"symbol"'` (or similar; count unique dataset entries)
3. Run `python -m app.research.pnl_baseline`
4. After completion, re-capture the registered-dataset count via the same endpoint

**Expected outcome:** The dataset count does not increase; neither founding dataset is re-recorded or re-tagged (the `DatasetAlreadyRegistered` REUSE path was hit for both splits).
**Pass criteria:** Count before == Count after; the operation completes without errors; stdout does not indicate "registered new dataset" for the founding windows.

---

### TC-09 — PnL history markdown regenerated with both epochs

**Type:** artifact
**Preconditions:** `python -m app.research.pnl_history` has been run after TC-07 (the new row was appended).

**Steps:**
1. Open `reports/pnl/pnl-history.md`
2. Locate section 1 (the old founding row)
3. Verify section 1 contains: old id, fingerprint `4d665603569b9dbf`, and the unchanged numerical values from the pre-iteration state
4. Locate a new section (the new-epoch founding row)
5. Verify the new section contains: new id (from TC-07), new fingerprint (from TC-04), and its own numerical values
6. Confirm train/holdout figures from section 1 are not pooled with or compared against the new section

**Expected outcome:** Section 1 is byte-identical to the pre-iteration state; a new section renders the new-epoch row honestly; train/holdout are never aggregated or averaged across the two sections.
**Pass criteria:** File opens without error; section 1 hash is identical to pre-iteration snapshot; new section exists and contains the new id and new fingerprint; no aggregation formulas cross the two sections.

---

### TC-10 — PnL ledger API tests pass with dynamic id reference

**Type:** api
**Preconditions:** `tests/test_pnl_ledger.py` and `tests/test_pnl_ledger_api.py` read `CONFIG.pnl_founding_enhancement_id` dynamically (never hardcoded strings).

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/test_pnl_ledger.py tests/test_pnl_ledger_api.py -q`
3. Observe test output for pass/fail count

**Expected outcome:** Full suite passes with 0 failed, proving the id/title value bump does not break either file.
**Pass criteria:** Exit code 0, output shows 0 failed.

---

### TC-11 — Idempotency: second pnl_baseline run is a no-op

**Type:** api
**Preconditions:** TC-07 has completed and the new founding row was successfully appended; `python -m app.research.pnl_baseline` is about to be run a second time.

**Steps:**
1. cd `apps/backend`
2. Run `python -m app.research.pnl_baseline` a second time
3. Capture stdout
4. Run `curl -s http://localhost:8000/research/pnl/ledger | python -m json.tool` to fetch the ledger again
5. Count the number of rows

**Expected outcome:** stdout prints "already present — the founding baseline row '<new-id>' exists; nothing was appended" or similar (the idempotency guarantee holds for the NEW id); exit code is 0; the ledger still contains exactly 2 rows (no third row was added).
**Pass criteria:** Exit code 0; stdout contains "already present" and does not contain "appended"; ledger row count is still 2.

---

### TC-12 — Kept-route re-capture shows only fingerprint stamp diff

**Type:** artifact
**Preconditions:** The I-9 kept-route re-capture baseline exists at `runs/goal-session-clean_slate/iter-3/kept-route-after.txt`; all edits from previous test cases have landed; the dev implementation is complete.

**Steps:**
1. cd `apps/backend`
2. Re-run the I-9 kept-route byte-comparison capture (every kept `/research`, `/tape`, `/meta` GET endpoint):
   - For each route, run: `curl -s http://localhost:8000<route> | sha256sum`
3. Write results to `runs/goal-session-clean_slate/iter-4/kept-route-after.txt`
4. For each route that embeds `config_fingerprint` (bars, levels, tradability, setups, backtests, pnl-ledger, edge-report, taxonomy):
   - Extract the old JSON response from iter-3 and the new from iter-4
   - Diff them to identify what changed
5. Verify that any diff is ONLY the fingerprint-stamp substring (old pin → new pin), with zero other byte differences
6. For routes that do not embed the fingerprint, verify they are byte-identical across both captures

**Expected outcome:** Every fingerprint-embedding route shows a diff attributable ONLY to the stamp substring; any non-embedding route stays fully byte-identical.
**Pass criteria:** All diffs are substring-only (fingerprint value changed, nothing else); non-embedding routes pass byte-comparison.

---

### TC-13 — Content-hash-cache-busting tests pass unmodified

**Type:** api
**Preconditions:** The existing cache-busting suites (`test_edge_report_cache.py`, `test_edge_report_backtest_cache.py`, `test_tradability_cache.py`, `test_setups.py`) are unmodified.

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/test_edge_report_cache.py tests/test_edge_report_backtest_cache.py tests/test_tradability_cache.py tests/test_setups.py -q`
3. Observe test output for pass/fail count

**Expected outcome:** Full suite passes with 0 failed, proving the general "a fingerprint-affecting config change busts a content-hash cache and recomputes with fresh, correct values" mechanism still holds under the new pin.
**Pass criteria:** Exit code 0, output shows 0 failed.

---

### TC-14 — Chart guard suites pass byte-unmodified

**Type:** api
**Preconditions:** The three chart guard suites (`test_cockpit_chart_upgrade.py`, `test_structure_chart_viewport.py`, `test_price_chart_confluence.py`) are unmodified.

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/test_cockpit_chart_upgrade.py tests/test_structure_chart_viewport.py tests/test_price_chart_confluence.py -q`
3. Observe test output for pass/fail count

**Expected outcome:** All three chart guard suites pass with 0 failed, confirming no regression to chart behavior.
**Pass criteria:** Exit code 0, output shows 0 failed across all three files.

---

### TC-15 — No-execution-path and no-credential guards pass

**Type:** api
**Preconditions:** `test_no_execution_path.py` and `test_no_credential_in_artifacts.py` are unmodified.

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/test_no_execution_path.py tests/test_no_credential_in_artifacts.py -q`
3. Observe test output for pass/fail count

**Expected outcome:** Both suites pass with 0 failed, proving no execution-path code or credentials have been inadvertently introduced.
**Pass criteria:** Exit code 0, output shows 0 failed.

---

### TC-16 — Full backend suite passes with 0 failed, 0 errors

**Type:** api
**Preconditions:** All 23 Config fields have been deleted, all 13 pin sites have been updated, pnl_baseline and pnl_history have been run, and all intermediate tests pass.

**Steps:**
1. cd `apps/backend`
2. Run `pytest tests/ -v`
3. Capture exit code and test summary

**Expected outcome:** All backend tests pass with 0 failed, 0 errors, literally — no pre-authorized failures remain.
**Pass criteria:** Exit code 0; test summary line shows "passed" count and "0 failed"; no "xfailed" or "skipped" entries related to fingerprint or Config fields.

---

### TC-17 — No uncatalogued source-introspection guard broke

**Type:** artifact
**Preconditions:** The full backend suite has been run; the grep for `read_text()`/`.open(` referencing config.py has been re-run.

**Steps:**
1. cd `apps/backend`
2. Run `grep -rn "read_text\|\.open(" tests/*.py | grep -i config`
3. Record results (expected: empty)
4. Review TC-16's full-suite run output for any NEW failure beyond the 13 intentionally-updated pin assertions

**Expected outcome:** grep returns zero hits (no source-introspection guard broke); full suite run shows no unexpected failures.
**Pass criteria:** grep output is empty; TC-16 exit code is 0; no test failures tied to Config introspection.

---

## Summary

Total test cases: 17
API tests: 11 (TC-02, TC-04, TC-07, TC-08, TC-10, TC-11, TC-13, TC-14, TC-15, TC-16, TC-17)
Artifact checks: 6 (TC-01, TC-03, TC-05, TC-06, TC-09, TC-12)

All test cases are backend/keyless (no browser tests). Every test case maps directly to a requirement in the phase spec's DEFINITION OF DONE section (TC-1 through TC-17). Tests verify the correctness of field deletions, fingerprint computation, pin site updates, PnL seeding, kept-route byte-identity, cache behavior, guard tests, and full suite stability.
