# goal-desk-iter-16 Functional Test Plan

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Frontend Present:** yes

## Phase Goal

Every screen snapshot the history list names becomes individually readable by its own id (closing the "two same-date recordings, only the newer one reachable" gap), and the two run ledgers that today silently drop their own store's verification errors start disclosing them the same way the screen and universe ledgers already do.

## Test Cases

### TC-01 — Screen snapshot id-based lookup returns byte-identical record

**Type:** api
**Preconditions:** Two screen snapshots recorded for the same `screen_date` under different `bar_store_signature`s exist on disk (e.g., `screen-2026-07-27-936543601e75` and `screen-2026-07-27-3ad3c57aa6ba`).

**Steps:**
1. Call `GET /research/desk/screen?id=<the earlier id>` (e.g., `?id=screen-2026-07-27-936543601e75`)
2. Compare the response body `screen` field to the actual file content on disk for that id

**Expected outcome:** Response body is byte-identical to the persisted snapshot file for that id.
**Pass criteria:** JSON response matches the on-disk file exactly (same `id`, `screen_date`, `as_of`, `rows`, `skipped`); HTTP 200.

---

### TC-02 — Same-date query without id still resolves to latest recording

**Type:** api
**Preconditions:** Two screen snapshots recorded for the same `screen_date` exist on disk.

**Steps:**
1. Call `GET /research/desk/screen?date=2026-07-27` (no `id` parameter)
2. Verify the response matches the later of the two recordings

**Expected outcome:** Behavior unchanged from before this iteration; the later recording is returned.
**Pass criteria:** Response body matches the later snapshot id (the one with the newer `created_utc`); HTTP 200.

---

### TC-03 — Unknown snapshot id returns honest null at HTTP 200

**Type:** api
**Preconditions:** None (no precondition required).

**Steps:**
1. Call `GET /research/desk/screen?id=does-not-exist`
2. Verify the response status and body

**Expected outcome:** Server returns HTTP 200 with `{"screen": null}`.
**Pass criteria:** HTTP 200 status code; response body is exactly `{"screen": null}`.

---

### TC-04 — Both id and date parameters together return 4xx refusal

**Type:** api
**Preconditions:** None.

**Steps:**
1. Call `GET /research/desk/screen?id=<valid-id>&date=<valid-date>`
2. Verify the response status and error message

**Expected outcome:** Server refuses the request with an HTTP 4xx status (422 expected per FastAPI validation convention) and names that only one of the two parameters may be supplied.
**Pass criteria:** HTTP 4xx status code (422 preferred); response body clearly states that only one of `id` or `date` may be supplied.

---

### TC-05 — Corrupt topup-run record file produces integrity_errors disclosure

**Type:** api
**Preconditions:** A `TopupRunStore` with a planted corrupt record file in a scoped (temporary) store directory is configured. The corrupt file is NOT in `apps/backend/.data`.

**Steps:**
1. Call `GET /research/desk/topup/runs`
2. Check the `integrity_errors` field in the response
3. Verify the corrupt record is excluded from `runs` and `latest` arrays

**Expected outcome:** Response body carries `integrity_errors: [{"file": <filename>, "error": <message>}, ...]` naming the corrupt file; the corrupt record is absent from both `runs` and `latest`.
**Pass criteria:** `integrity_errors` array is non-empty; corrupt file is named with its error message; corrupt record is not present in `runs` or `latest` arrays; HTTP 200.

---

### TC-06 — Corrupt reconcile-run record file produces integrity_errors disclosure

**Type:** api
**Preconditions:** A `ReconcileRunStore` with a planted corrupt record file in a scoped (temporary) store directory is configured. The corrupt file is NOT in `apps/backend/.data`.

**Steps:**
1. Call `GET /research/desk/coverage/reconcile/runs`
2. Check the `integrity_errors` field in the response
3. Verify the corrupt record is excluded from `runs` and `latest` arrays

**Expected outcome:** Response body carries `integrity_errors: [{"file": <filename>, "error": <message>}, ...]` with the same shape as TC-05; the corrupt record is absent from `runs`/`latest`.
**Pass criteria:** `integrity_errors` array is non-empty; corrupt file is named with its error message; corrupt record is not present in `runs` or `latest` arrays; HTTP 200.

---

### TC-07 — MCP desk_screen tool and get_endpoint proxy verbatim

**Type:** api
**Preconditions:** Running backend with MCP server active.

**Steps:**
1. Call MCP `desk_screen` tool with no arguments
2. Compare result to `GET /research/desk/screen` (no params)
3. Call MCP `get_endpoint` with path `/research/desk/screen?id=<id>`
4. Compare result to direct curl `GET /research/desk/screen?id=<id>`

**Expected outcome:** MCP responses are byte-identical to corresponding curl calls.
**Pass criteria:** MCP `desk_screen` no-arg JSON matches `GET /research/desk/screen`; MCP `get_endpoint` on `?id=` path matches direct curl equivalent; no tool behavior change.

---

### TC-08 — MCP tool count remains exactly 17

**Type:** api
**Preconditions:** Backend test suite runs with `test_mcp_server.py::test_expected_tools_count`.

**Steps:**
1. Run `python -m pytest apps/backend/tests/test_mcp_server.py -k test_expected_tools_count`
2. Verify the `EXPECTED_TOOLS` contract is satisfied

**Expected outcome:** Test passes; tool count is exactly 17.
**Pass criteria:** Test passes; no new MCP tools added, no existing tools removed.

---

### TC-09 — Screen history list shows two same-date entries with distinct created_utc and independent selection

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend serving the screen store with two same-date snapshot records (e.g., `screen-2026-07-27-936543601e75` and `screen-2026-07-27-3ad3c57aa6ba`); clean `.next` rebuild completed.

**Steps:**
1. Navigate to `/desk` page
2. Locate the Screen History section
3. Verify both same-date entries are displayed with distinct `created_utc` values beside `screen_date`
4. Verify each row is independently selectable and highlighted (not both highlighted for the same date)

**Expected outcome:** Both entries visible with distinct timestamps; each row can be independently selected and highlighted.
**Pass criteria:** Both same-date rows present in history list; `created_utc` column visible with distinct timestamps for each row; only the clicked row is highlighted (not both); no visual grouping that would suggest they share a date.

---

### TC-10 — Selecting earlier same-date entry shows its own rows and provenance

**Type:** browser
**Preconditions:** Two same-date screen snapshots exist; Screen History list is displayed.

**Steps:**
1. Click the earlier of the two same-date entries in the Screen History list
2. Wait for the page to render the ranked table and Provenance panel
3. Verify the table shows the earlier entry's own rows (e.g., NFLX `1d` coverage badge is dark per the earlier snapshot's state)
4. Verify the Provenance panel displays the earlier entry's own `id` and `created_utc`

**Expected outcome:** The ranked table reflects the earlier snapshot's data; Provenance shows that snapshot's identity.
**Pass criteria:** Table rows match the earlier snapshot's state (e.g., NFLX badge dark); Provenance `id` matches the earlier snapshot's id; Provenance `created_utc` is the earlier timestamp; only that row is highlighted.

---

### TC-11 — Selecting later same-date entry shows its own rows and updated provenance

**Type:** browser
**Preconditions:** TC-10 completed; two same-date snapshots exist.

**Steps:**
1. Click the later of the two same-date entries in the Screen History list
2. Wait for the page to render
3. Verify the table shows the later entry's own rows (e.g., NFLX `1d` badge is lit per the later snapshot's state)
4. Verify the Provenance panel updates to the later entry's own `id` and `created_utc`

**Expected outcome:** The ranked table and Provenance both reflect the later snapshot's state and identity.
**Pass criteria:** Table rows match the later snapshot's state (e.g., NFLX badge lit, different than TC-10); Provenance `id` matches the later snapshot's id; Provenance `created_utc` is the later timestamp; only that row is highlighted.

---

### TC-12 — Default load (no history selection) shows most-recently-recorded snapshot

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend with screen snapshots.

**Steps:**
1. Navigate to `/desk` page without any query string
2. Allow the page to load with the default (latest) snapshot
3. Examine the Provenance panel's default-view description text

**Expected outcome:** Provenance panel describes the displayed snapshot as the most recently recorded screen.
**Pass criteria:** Description text reads as "most recently recorded" (referring to `created_utc`-sorted latest), not "latest screen date"; no advice/imperative/urgency language present.

---

### TC-13 — Corrupt topup-run integrity-error line is visible on screen

**Type:** browser
**Preconditions:** Frontend running; backend configured with a corrupt Top-up Runs record in a scoped store; API endpoint returns `integrity_errors` payload.

**Steps:**
1. Navigate to `/desk` page
2. Locate the Top-up Runs section
3. Verify a count-plus-filename integrity-error line is visible (e.g., "1 file integrity error: topup-run-corrupt-001.json")
4. Take a screenshot of the visible error line

**Expected outcome:** Integrity-error line is rendered and visible on the page.
**Pass criteria:** Error line present in Top-up Runs section; error message includes filename and count; screenshot shows the rendered error text; HTTP 200 from the GET call.

---

### TC-14 — Config fingerprint and protected files unchanged

**Type:** artifact
**Preconditions:** Backend suite built and tests run.

**Steps:**
1. Run `python -c "from app.config import Config; print(Config().config_fingerprint())"`
2. Verify the fingerprint value
3. Run a git diff on `apps/backend/app/research/tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `apps/frontend/components/StructureChart.tsx`, and `desk_coverage.py`
4. Verify diffs are empty

**Expected outcome:** Fingerprint is `08e471b10130e1e2`; the six protected files have zero changes.
**Pass criteria:** Fingerprint output is exactly `08e471b10130e1e2`; git diff on each of the six files returns no changes.

---

### TC-15 — SHA-256 checksums of all desk store files are identical before and after

**Type:** artifact
**Preconditions:** Before and after iteration, compute SHA-256 hashes of every file in the universe, screen, topup-run, and reconcile-run store directories.

**Steps:**
1. Before changes: `find apps/backend/.data/universe apps/backend/.data/screen apps/backend/.data/topup_runs apps/backend/.data/reconcile_runs -type f -exec sha256sum {} \; | tee /tmp/checksums-before.txt`
2. Apply this iteration's changes and run tests
3. After changes: `find apps/backend/.data/universe apps/backend/.data/screen apps/backend/.data/topup_runs apps/backend/.data/reconcile_runs -type f -exec sha256sum {} \; | tee /tmp/checksums-after.txt`
4. Compare: `diff /tmp/checksums-before.txt /tmp/checksums-after.txt`

**Expected outcome:** Every checksum is identical; no files were backfilled, rewritten, or deleted.
**Pass criteria:** diff output is empty; checksum counts before and after are equal; no new files added to the stores; no files deleted.

---

### TC-16 — Demo-narrator J-12 walkthrough recorded with new-flagged gallery

**Type:** browser
**Preconditions:** Full depth iteration (demo-narrator runs after verification); screen store contains the real same-date pair or equivalent; demo-narrator is configured to record.

**Steps:**
1. Demo-narrator records the `[NEW]`-flagged J-12 walkthrough with the following steps:
   - Open the Screen History list on `/desk`
   - Select the earlier same-date entry (highlight + rows + Provenance update)
   - Select the later same-date entry (highlight + rows + Provenance update with different id/created_utc)
   - Show the integrity-error line in the Top-up Runs section
2. Verify the demo artifact shows `Demo Verdict: RECORDED` and contains a non-empty screenshot gallery

**Expected outcome:** Demo-narrator produces `reports/demo/goal-desk-iter-16/` with `Demo Verdict: RECORDED` and screenshots covering all four walkthrough steps.
**Pass criteria:** Demo verdict file exists with `Demo Verdict: RECORDED`; screenshot gallery is non-empty; walkthrough narration covers the four steps listed; `[NEW]` flag is present in the recorded walkthrough.

---

## Summary

**Total test cases:** 16
- **API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08)
- **Browser tests:** 5 (TC-09, TC-10, TC-11, TC-12, TC-13)
- **Artifact checks:** 3 (TC-14, TC-15, TC-16)

These tests cover the full scope of goal-desk-iter-16:
- API surface: id-based screen lookup, integrity_errors disclosure on two run ledgers, MCP contract preservation
- Frontend: id-based history selection/highlighting, provenance display, integrity-error rendering
- Data integrity: store file checksums and configuration fingerprint unchanged
- Demo narrative: end-to-end walkthrough of the same-date snapshot differentiation and integrity-error disclosure
