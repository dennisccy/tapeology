# Phase goal-rapid-microscope-iter-25 — UI Test Results

**Phase:** goal-rapid-microscope-iter-25
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. -->

**Overall:** 1/1 tests passed (0 skipped)

Lean goal-mode dispatch: only J-06 was in scope for this browser-qa-agent pass. J-01, J-02,
J-03, J-04, J-05, J-08, J-09, J-10 are verified separately via deterministic golden replay
(`demo_runner.py --mode verify`) per the dispatch instructions and are NOT re-tested here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression/acceptance | P1 | Vault "Sealed at" cell for the pre-existing exposed shard is a bare date (no clock time); the new still-sealed shard's row renders the literal "sealed — opaque" text across Dataset/Family root/Symbol/Session date/Assigned at/Exposed at/Content checksum | Navigated to `/desk`, expanded "Validation Vault". Exposed shard `vshard-b018e9...` "Sealed at" cell reads `2026-05-01` — bare date, no `T`, no colon, no clock time. New sealed shard `vshard-71a307...` "Sealed at" cell reads `2026-06-07` — also bare. The sealed shard's Dataset/Family root/Symbol/Session date/Assigned at/Exposed at/Content checksum cells all render the literal text "sealed — opaque"; the exposed shard's same columns show real values (dataset id, family root, symbol `PGQA`, session date, timestamps, checksum). Confirmed both via page-text extraction and two screenshots (full-width and horizontally-scrolled to reveal the opaque columns). | PASS | `reports/qa/goal-rapid-microscope-iter-25-evidence/UT-J-06-result.png` (+ `J-06-vault-sealed-opaque.png`) |

---

## Passed Tests

### UT-J-06 — The recorder and the Vault — new tape, sealed at birth
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-25-evidence/UT-J-06-result.png`

- Precondition check: frontend rig responded HTTP 200 at `http://localhost:3301`; backend rig
  responded HTTP 200 at `http://localhost:8301`. Confirmed via
  `reports/qa-scoped-backend-store-manifest.md` (launched_at_utc `2026-08-23T06:21:36Z`) that
  the running backend is the fixture-scoped QA rig, not the main dev backend.
- Confirmed via direct `GET /research/desk/micro/vault` on the rig that two shards exist:
  `vshard-b018e9...` (`universe_id: iter18-qa-universe`, `exposure_state: exposed`,
  `sealed_at: "2026-05-01"`, symbol `PGQA`) and `vshard-71a307...` (`universe_id:
  iter25-qa-sealed-only-universe`, `exposure_state: sealed`, `sealed_at: "2026-06-07"`, with
  EXACTLY the six opaque keys — no `symbol`/`session_date`/`dataset_id`/`family_root_id` — at
  the API level).
- Navigated Chrome MCP to `http://localhost:3301/desk`, clicked
  `[data-testid="desk-section-expand-validationVault"]` to expand the section.
- `extract` (page text) over the expanded Validation Vault table confirmed: "Shard ledger chain
  verification: ok", "Universe ledger chain verification: ok", and the shards table row for
  `vshard-71a3070082aa965edd3ac6e97a2e1686d7bdf4504d46a13bce8ff8983765f4a9` shows
  `sealed — opaque` repeated across Dataset, Family root, Symbol, Session date, Assigned at,
  Exposed at, and Content checksum (7 columns, matching TC-2 exactly); the pre-existing exposed
  shard row shows real values in every one of those columns.
- Took a full-width screenshot of the expanded Vault section (`J-06-vault-sealed-opaque.png`),
  confirming the "Sealed at" column: `2026-05-01` for the exposed shard (bare date, TC-3) and
  `2026-06-07` for the sealed shard (also bare).
- Scrolled the table's internal horizontal scroller to the far right and took a second
  screenshot (`UT-J-06-result.png` / `J-06-vault-opaque-columns.png`) that visually shows the
  literal `sealed — opaque` text (wrapped as "sealed / opaque" at this column width) filling
  the Dataset/Family root/Symbol/Session date/Assigned at/Exposed at/Content checksum cells for
  the new sealed shard, beside real dataset id / family root / `PGQA` / session date /
  timestamps / checksum for the pre-existing exposed shard in the same columns — directly
  confirming TC-2.
- No console errors observed that prevented the test from completing.
- Golden replay script check: `runs/goal-session-rapid-microscope/journey-scripts/J-06.json`
  (already updated by the developer this iteration with a genuine step-3 assertion —
  `desk-section-expand-validationVault` → expect `"sealed — opaque"`) matches exactly what was
  observed live in this browser pass; `demo_runner.py --mode lint --scripts-dir
  runs/goal-session-rapid-microscope/journey-scripts --journeys J-06` reports `J-06 ok`. No
  changes needed — left as-is since it is already accurate and independently confirmed.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301 (fixture-scoped QA rig; backend :8301)
- **Browser:** Chrome via MCP (headless, attached to pinned CDP port 9222)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-25-evidence/`
