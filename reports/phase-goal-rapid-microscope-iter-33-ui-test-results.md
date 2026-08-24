# UI Test Results (merged)

**Date:** 2026-08-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-02-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-04-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-10-verify.png |
| UT-J-11 | Graduation gets a surface — the funnel's last state stops being invisible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-33-evidence/J-11-verify.png |
| UT-J-12 | The observer's build truth gets a surface — and its enumerator stops excluding silently | happy-path | P1 | A read-only "Feature Snapshots" section renders directly below the shipped Graduation section on `/desk`, fetched on expand from `GET /research/desk/micro/snapshots` and rendered verbatim (per-snapshot identity fields, `withheld_excluded`, `stale_excluded`, build-run history), with no client-side aggregation and no build/compute control | Section confirmed as the last `<section aria-label>` on the page, immediately after "Graduation" (DOM order: ... Walk-Forward, Validation Vault, Graduation, Feature Snapshots). Expanding it fetched the endpoint and rendered the live payload byte-for-byte against a direct `curl` of the same route: 3 snapshots (dataset ids `6c9bf2c7…`, `bad5a94a…`, `d9f9dbe0…`) each showing `snapshot_format_version=micro-snapshot-v1`, `micro_algo_version=1`, `config_fingerprint=08e471b10130e1e2`, matching `feature_source_hash`/`params_hash`, `quote_size_unit=unverified`, correct `row_count`/`bytes_on_disk`, and `built_utc` correctly rendered as ET; disclosure line "Withheld (excluded): 1 · Stale (excluded): 0" matching the served `withheld_excluded`/`stale_excluded`; Run History showing the served empty-state copy "No snapshot build runs recorded yet." (matching `{"runs":[]}`). Confirmed read-only: the section contains exactly 1 `<button>` (the collapsible toggle itself) — no build/POST control. See "Known Limitation" below for the fixture-scoped (valid/stale/withheld) sub-scenario not independently reproduced. | PASS | `reports/qa/goal-rapid-microscope-iter-33-evidence/J-12-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-24

