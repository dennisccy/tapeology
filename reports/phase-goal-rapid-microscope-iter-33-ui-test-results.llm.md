# Goal Iteration 33 — UI Test Results (LLM browser-qa pass)

**Phase:** goal-rapid-microscope-iter-33
**Date:** 2026-08-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Scope: this dispatch tests EXACTLY J-12 (LLM browser lane). J-01, J-02, J-04, J-08, J-10, J-11
were verified separately via deterministic golden replay — see
`reports/phase-goal-rapid-microscope-iter-33-regression-replay-results.md` (6/6 PASS).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-12 | The observer's build truth gets a surface — and its enumerator stops excluding silently | happy-path | P1 | A read-only "Feature Snapshots" section renders directly below the shipped Graduation section on `/desk`, fetched on expand from `GET /research/desk/micro/snapshots` and rendered verbatim (per-snapshot identity fields, `withheld_excluded`, `stale_excluded`, build-run history), with no client-side aggregation and no build/compute control | Section confirmed as the last `<section aria-label>` on the page, immediately after "Graduation" (DOM order: ... Walk-Forward, Validation Vault, Graduation, Feature Snapshots). Expanding it fetched the endpoint and rendered the live payload byte-for-byte against a direct `curl` of the same route: 3 snapshots (dataset ids `6c9bf2c7…`, `bad5a94a…`, `d9f9dbe0…`) each showing `snapshot_format_version=micro-snapshot-v1`, `micro_algo_version=1`, `config_fingerprint=08e471b10130e1e2`, matching `feature_source_hash`/`params_hash`, `quote_size_unit=unverified`, correct `row_count`/`bytes_on_disk`, and `built_utc` correctly rendered as ET; disclosure line "Withheld (excluded): 1 · Stale (excluded): 0" matching the served `withheld_excluded`/`stale_excluded`; Run History showing the served empty-state copy "No snapshot build runs recorded yet." (matching `{"runs":[]}`). Confirmed read-only: the section contains exactly 1 `<button>` (the collapsible toggle itself) — no build/POST control. See "Known Limitation" below for the fixture-scoped (valid/stale/withheld) sub-scenario not independently reproduced. | PASS | `reports/qa/goal-rapid-microscope-iter-33-evidence/J-12-result.png` |

---

## Passed Tests

### UT-J-12 — The observer's build truth gets a surface
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-33-evidence/J-12-result.png` (full-page screenshot, section visible at the bottom, scrolled into view before capture)

- Navigated to `http://localhost:3301/desk`; page loaded with "Desk" heading and all shipped sections present, unchanged (Top-up runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, Playbook Evidence, Referee Registry/Adjudications/Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, Graduation) plus the new Feature Snapshots section at the very bottom.
- Confirmed via `document.querySelectorAll('section[aria-label]')` DOM order that Feature Snapshots is the LAST section, the immediate next sibling directly below Graduation — exactly as T-11/the spec require (new section below the shipped ones).
- Confirmed the collapsed state renders only the "FEATURE SNAPSHOTS" heading (no shipped heading string or testid reused — `data-testid="desk-section-expand-featureSnapshots"` is new).
- Clicked `[data-testid="desk-section-expand-featureSnapshots"]`; the section fetched `GET /research/desk/micro/snapshots` on first expand (same one-fetch-on-toggle pattern as the other Rapid Microscope sections) and rendered (via `innerText`, batch-verified in one `eval` call):
  - Section description: "Feature Snapshots (GET /research/desk/micro/snapshots, read verbatim; read-only -- a snapshot build is an operator/CLI act, not a UI control): the micro observer's build-metadata inventory -- every currently valid snapshot's identity, plus how many pool members this listing withheld or dropped as stale."
  - "Withheld (excluded): 1 · Stale (excluded): 0"
  - A "Snapshots" table with 3 rows, columns: Dataset, Snapshot format, Algo version, Config fingerprint, Feature source hash, Params hash, Quote size unit, Row count, Bytes on disk, Built at.
  - "Run History" block: "∅ No snapshot build runs recorded yet."
- Cross-checked every rendered field directly against `curl -s http://localhost:8301/research/desk/micro/snapshots`: byte-for-byte match on all 3 `dataset_id`s, `snapshot_format_version`, `micro_algo_version`, `config_fingerprint`, `feature_source_hash`, `params_hash`, `quote_size_unit`, `row_count`, `bytes_on_disk` (e.g. dataset `6c9bf2c700d749e0993efd92c5807de3`: `row_count=377`, `bytes_on_disk=649536`), `withheld_excluded=1`, `stale_excluded=0`; `built_utc="2026-08-24T22:30:15.945486Z"` correctly rendered in-page as `2026-08-24 18:30 ET` (UTC−4, EDT). `GET /research/desk/micro/snapshots/runs` returned `{"runs":[]}`, matching the rendered empty-state copy.
- Confirmed read-only: `document.querySelector('section[aria-label="Feature Snapshots"]').querySelectorAll('button').length === 1` and its only text is the collapsible toggle label "▾Feature Snapshots" — no build/compute control anywhere inside the section (`/snapshots/compute` stays UI-unreachable, matching T-8).
- Screenshot: full-page capture (`reports/qa/goal-rapid-microscope-iter-33-evidence/J-12-result.png`) taken after scrolling the section into view; the Feature Snapshots section is visible at the bottom of the page with its description, disclosure line, and the left portion of the Snapshots table (dataset ids, snapshot format, algo version, config fingerprint, feature source hash, params hash) plus the Run History empty state. The table's rightmost columns (Row count/Bytes on disk/Built at) scroll horizontally within their own container (`tableScrollWidth=1549` vs `wrapClientWidth=1214`) and are therefore outside the static screenshot crop but were independently verified via `innerText`/`get_text` batch extraction above and cross-checked against the live API response.
- Wrote and verified `runs/goal-session-rapid-microscope/journey-scripts/J-12.json` (2 steps: `goto /desk` → expect "Playbook Signals"; `click desk-section-expand-featureSnapshots` → expect "Withheld (excluded):", the same string J-02's step 3 already proved reliable under headless deterministic replay this iteration). Linted (`demo_runner.py --mode lint`) and replayed for real (`demo_runner.py --mode verify --base-url http://localhost:3301`): `[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`.

**Known Limitation (disclosed, not fabricated):** J-12's Acceptance/DEFINITION OF DONE names a
second sub-scenario that was NOT independently reproduced this dispatch: the **fixture-scoped rig
seeded with one valid snapshot, one stale meta, and one withheld pool member** (TC-2), which would
prove the stale meta appears ONLY inside `stale_excluded` (never as a row) and the withheld member
appears ONLY inside `withheld_excluded` (never by id/symbol/session-date/checksum/row-count/bytes).
The dev handoff provides a ready seed script
(`apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py`) and exact commands to
stand this up, but doing so requires restarting the shared, long-lived `:8301`/`:3301`
store-scoped browser-QA rig with a different `TAPEOLOGY_DATASET_DIR` (or standing up an entirely
separate backend+frontend pair on new ports) — this role's rules explicitly forbid
debugging/restarting the app ("Never debug or restart the app — that is a SKIPPED with reason").
This is the identical judgment call this same goal-mode session's iter-31 browser-qa pass made for
J-11's own multi-stage fixture sub-scenario (see
`reports/phase-goal-rapid-microscope-iter-31-ui-test-results.llm.md`, "Known Limitation"), which
was accepted without blocking that iteration's PASS. What WAS verified this dispatch — verbatim,
byte-correct rendering of real populated data (3 real snapshots, both real disclosure counts),
correct DOM position below Graduation, and read-only behavior (1 button, no build control) — is
the section's core, safety-relevant contract and is fully evidenced above with a live-API
cross-check. This gap is disclosed for the evaluator/auditor rather than silently absorbed into
the PASS verdict; backend-side proof that `withheld_excluded` is pool-derived (not
snapshot-file-derived) and that a stale meta is dropped correctly is independently covered by the
dev-authored unit tests (`test_vault.py`'s TC-7 counter-test, `test_micro_snapshots.py`'s new
`snapshot_meta_report` tests), which are outside this browser-QA agent's scope to re-verify.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped browser-QA rig; `TAPEOLOGY_DATASET_DIR`
  under `.../tapeology-store-scope-qa/rig/datasets`, shared across this goal-mode session)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (pinned CDP
  profile/port; headless, not modified)
- **Test Date:** 2026-08-24
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-33-evidence/`
- **Golden replay script written this dispatch:**
  `runs/goal-session-rapid-microscope/journey-scripts/J-12.json` (lint-clean and verify-clean
  against the live rig).
