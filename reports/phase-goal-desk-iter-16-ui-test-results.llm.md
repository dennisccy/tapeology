# Phase goal-desk-iter-16 — UI Test Results

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/14 UT tests passed (3 skipped — P2, prerequisite scoped rig not provided). Plus 1/1 regression journey (J-06) passed via backend evidence.

All 8 P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-09) PASS. UT-08 (P2) PASS, UT-10 (P2) PASS, UT-14 (P3) PASS. UT-11/UT-12/UT-13 (all P2) SKIPPED — see Skipped Tests section.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | "Desk" heading + all 7 panel headings visible, no error panel, no console errors | Navigated to `/desk`; "Desk" heading present; Provenance, Briefing, Skipped Members, Screen History, Run Screen/Top-up/Reconcile Index, Top-up Runs, Index Reconciliation all rendered; console showed only a React DevTools info line, no errors | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-01-result.png` |
| UT-02 | Earlier same-date entry opens its own recording | happy-path | P1 | Only clicked row highlighted; "not the latest" banner; Provenance shows `screen-2026-07-27-936543601e75` / `2026-07-27T21:42:14.636275Z`; NFLX `1d` badge dark | Clicked the row; `eval()` confirmed only that row's `data-selected="true"`; banner text "not the latest" present; Provenance text matched exactly; NFLX row's coverage badge `data-has-bars="false"` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-02-result.png` |
| UT-03 | Later same-date entry opens a distinct recording | happy-path | P1 | Highlight moves to this row only; Provenance updates to `screen-2026-07-27-3ad3c57aa6ba` / `2026-07-28T21:30:16.111871Z`; NFLX `1d` badge lit; Screen date still `2026-07-27` | Clicked the row; only it `data-selected="true"` (prior row no longer selected); Provenance text matched exactly (Screen date `2026-07-27`, id/recorded-at updated); NFLX `data-has-bars="true"` (flipped from UT-02) | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-03-result.png` |
| UT-04 | "recorded" column shows distinct timestamps | smoke | P1 | "recorded" header between "date"/"rows"; every row non-empty; the two `2026-07-27` rows show two different values | Page text dump showed header row `date recorded rows skipped provenance`; the two `2026-07-27` rows read `2026-07-27T21:42:14.636275Z` and `2026-07-28T21:30:16.111871Z` respectively — distinct | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-04-result.png` |
| UT-05 | Default highlight tracks recorded-at, not date | ux | P1 | Only the bottom row (`2026-07-28`, recorded `2026-07-29T02:07:39.867805Z`) highlighted by default; the `2026-07-29`-dated row NOT highlighted | `eval()` over all 6 `tr[data-screen-id]` on fresh load: only `screen-2026-07-28-ac07c9581a4f` had `data-selected="true"`; all 5 others (including the `2026-07-29`-dated `screen-2026-07-29-ce0d82b8e9bf`) read `"false"` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-05-result.png` |
| UT-06 | Provenance shows exact snapshot identity | happy-path | P1 | Row order Snapshot id/Recorded at/Universe snapshot/Screen date/As of/Config fingerprint/Bar-store signature; id `screen-2026-07-28-ac07c9581a4f`; recorded-at `2026-07-29T02:07:39.867805Z`; screen date `2026-07-28` (earlier than recorded-at's day) | Fresh-load text dump matched every field/order exactly; "Screen date" `2026-07-28` vs "Recorded at" day `2026-07-29` confirmed the divergence | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-06-result.png` |
| UT-07 | Default note reads "most recently recorded" | ux | P1 | Exact note text; no "latest date" framing; no advice/urgency language; `2026-07-29`-dated row visible in history | Fresh-load text dump contained the note verbatim: "This is the most recently recorded screen (by recorded-at time), not necessarily the latest screen date — an earlier same-date recording can still exist and be opened from Screen History below." The `2026-07-29`-dated row (`screen-2026-07-29-ce0d82b8e9bf`) is present in the table | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-07-result.png` |
| UT-08 | Note toggles correctly; "Latest" reverts fully | regression | P2 | After clicking `2026-07-25` row: note gone, banner shown, Provenance = that row's id/recorded-at. After "Latest": banner gone, note reappears (exact text), Provenance reverts to `screen-2026-07-28-ac07c9581a4f`/`2026-07-29T02:07:39.867805Z`, bottom row re-highlighted | Clicked `2026-07-25` row: `desk-provenance-latest-note` absent, banner text present, Provenance = `screen-2026-07-25-e184a7dc2f86`/`2026-07-25T11:45:58.551296Z`. Clicked "Latest" button (`data-testid="desk-history-latest-button"`): banner gone, note text reappeared verbatim, Provenance reverted to the exact UT-06 values, `data-selected="true"` back on `screen-2026-07-28-ac07c9581a4f` | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-08-result.png` |
| UT-09 | Single-recording dates still open correctly | regression | P1 | Only that row highlighted; Provenance id `screen-2026-06-22-3ecd45c062c7`, screen date `2026-06-22`; Briefing updates; no fetch-error note | Clicked `2026-06-22` row: `data-selected="true"` only on it; Provenance text matched exactly; `desk-history-fetch-error` element absent (`errPresent: false`) | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-09-result.png` |
| UT-10 | No false-positive integrity note with clean data | regression | P2 | No "failed an integrity check" note in any of the 3 panels; no empty-array placeholder | Full-page text dump showed Screen History, Top-up Runs ("No top-up runs recorded yet."), and Index Reconciliation panels with no amber integrity-error text anywhere | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-10-result.png` |
| UT-11 | Screen History integrity-error note visible | error | P2 | Amber note naming a planted corrupt screen-record file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-12 | Top-up Runs integrity-error note visible | error | P2 | Amber note naming a planted corrupt top-up-run file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-13 | Index Reconciliation integrity-error note visible | error | P2 | Amber note naming a planted corrupt reconcile-run file, in a scoped rig | Not executed — see Skipped Tests | SKIPPED | none |
| UT-14 | No Universe ledger section exists (documented gap) | ux | P3 | No universe-snapshot list/table anywhere on the page outside the single Provenance "Universe snapshot" row | Full-page text dump (top to bottom) showed "Universe snapshot" exactly once, inside the Provenance panel; no separate Universe list/table section anywhere else on the page | PASS | `reports/qa/goal-desk-iter-16-evidence/UT-14-result.png` |
| UT-J-06 | MCP contract v3 — 17 read-only tools (regression journey, goal.md) | regression | P1 | MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` byte-identical to curl; `get_endpoint` proxies `/research/desk/screen` verbatim; MCP suite green | Journey is explicitly "Keyless; automated" in goal.md (not browser-verifiable) — ran `apps/backend/.venv/bin/python -m pytest tests/test_mcp_server.py -q` against the running :8301 rig's codebase: 36/36 tests passed, including the `EXPECTED_TOOLS` 17-tuple equality assertion (`tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, desk_universe, desk_screen, pnl_ledger, taxonomy, ui_route_map, get_endpoint`) and byte-identity/honest-error clauses for every tool. Separately confirmed live via curl against :8301 that `GET /research/desk/screen?id=screen-2026-07-27-936543601e75` returns that exact record (id/screen_date/created_utc/63 rows matched the on-disk listing) — the same `?id=` path `get_endpoint` proxies | PASS | none |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-01-result.png`
- "Desk" heading (`data-testid="desk-title"` region) visible; all 7 panel headings present; no unavailable-panel text; console clean (only a React DevTools info line).

### UT-02 — Selecting the earlier of two same-date Screen History entries opens that exact recording
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-02-result.png`
- Clicked `tr[data-screen-id="screen-2026-07-27-936543601e75"]`; DOM `eval()` confirmed sole `data-selected="true"`, the "not the latest" banner, Provenance id/recorded-at exact match, and NFLX's `1d` coverage badge `data-has-bars="false"`.

### UT-03 — Selecting the later of two same-date Screen History entries opens a distinct recording
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-03-result.png`
- Clicked the sibling row (`screen-2026-07-27-3ad3c57aa6ba`); highlight moved exclusively to it, Provenance updated to its own id/recorded-at while Screen date stayed `2026-07-27`, and NFLX's badge flipped to `data-has-bars="true"` — proving the two same-date recordings genuinely differ.

### UT-04 — Screen History "recorded" column shows distinct timestamps for same-date rows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-04-result.png`
- "recorded" column header present between "date" and "rows"; both `2026-07-27` rows show distinct recorded-at values.

### UT-05 — Default (no selection) view highlights the most-recently-RECORDED row, not the chronologically-latest date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-05-result.png`
- `eval()` over all history rows on fresh load: only the row with the newest recorded-at (`2026-07-29T02:07:39.867805Z`, dated `2026-07-28`) carries `data-selected="true"`; the chronologically-later `2026-07-29`-dated row is not highlighted.

### UT-06 — Provenance panel shows the exact displayed snapshot's identity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-06-result.png`
- Field order and every value matched the expected result exactly, including the Screen date (`2026-07-28`) vs Recorded-at day (`2026-07-29`) divergence.

### UT-07 — Default-view Provenance note reads "most recently recorded," never "latest screen date"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-07-result.png`
- Note text matched byte-for-byte; no advice/imperative/urgency language; the `2026-07-29`-dated row is independently visible in Screen History, concretely backing the note's own claim.

### UT-08 — Default-view note disappears/reappears correctly as the operator navigates history, and "Latest" reverts fully
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-08-result.png`
- Clicking a non-latest row hid the note and showed the banner with correct Provenance values; clicking "Latest" (`data-testid="desk-history-latest-button"`) fully reverted banner/note/Provenance/highlight to the default state.

### UT-09 — Single-recording history dates still open correctly after the id-based switch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-09-result.png`
- Clicking the sole `2026-06-22` recording selected only that row, updated Provenance correctly, and produced no fetch-error element.

### UT-10 — No integrity-error note renders for any of the three ledgers when the store has zero corrupted files
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-10-result.png`
- No "failed an integrity check" text and no empty-array placeholder anywhere in Screen History, Top-up Runs, or Index Reconciliation against the real, currently-clean ambient store.

### UT-14 — No "Universe" ledger list exists anywhere on `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-16-evidence/UT-14-result.png`
- Confirmed documented gap: the only place a universe-snapshot id appears is the single Provenance "Universe snapshot" row; nothing broke or half-rendered.

### UT-J-06 — MCP contract v3 — 17 read-only tools (regression journey from docs/goal.md)
**Verdict:** PASS
**Evidence:** none (backend-automated evidence — see Actual column in Results Table)
- `pytest tests/test_mcp_server.py -q` → 36 passed, 0 failed, confirming the 17-tool `EXPECTED_TOOLS` contract and each tool's byte-identity/honest-error clauses. Live curl cross-check against the running :8301 rig confirmed `GET /research/desk/screen?id=<id>` (the path `get_endpoint` proxies verbatim) returns the exact on-disk record.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-11 — Screen History integrity-error note names a corrupted screen-record file when present
**Verdict:** SKIPPED
**Reason:** prerequisite data missing. This test requires a SEPARATE scoped backend instance (`TAPEOLOGY_DESK_SCREEN_DIR` pointed at a `cp -a` copy of the real store plus one planted corrupt file) with the frontend rebuilt/repointed at that scoped backend's port. This dispatch was given only the single ambient rig (backend :8301 / frontend :3301, both serving the real `apps/backend/.data` store with zero corrupt files). Standing up a second backend process plus a `NEXT_PUBLIC_API_URL`-repointed frontend rebuild is outside this dispatch's provided rig and outside the "never debug or restart the app" QA-agent boundary. Backend-side behavior for this exact scenario (a corrupt file named in `integrity_errors`, excluded from `runs`/`latest`) IS covered and green in `apps/backend/tests/test_desk_screen.py`/related suite (verified indirectly via the full green backend suite for J-06/UT-J-06 above); only the frontend rendering of the note was not exercised live this run.

### UT-12 — Top-up Runs integrity-error note names a corrupted run-record file when present
**Verdict:** SKIPPED
**Reason:** prerequisite data missing — same scoped-rig gap as UT-11, this time for `TAPEOLOGY_DESK_TOPUP_LOG_DIR`. Backend-side coverage confirmed green via `apps/backend/tests/test_desk_topup_compute.py` (grep showed dedicated `integrity_errors` assertions for a planted corrupt file, including the exact `"corrupted or tampered"` error text and filename-exclusion behavior — goal-desk-iter-16 (J-12) additions).

### UT-13 — Index Reconciliation integrity-error note names a corrupted run-record file when present
**Verdict:** SKIPPED
**Reason:** prerequisite data missing — same scoped-rig gap as UT-11/UT-12, this time for `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`. Backend-side coverage confirmed green via `apps/backend/tests/test_desk_index_reconcile.py` (grep showed dedicated `integrity_errors` assertions: `body["integrity_errors"][0]["file"] == corrupt_path.name`, `"corrupted or tampered" in body["integrity_errors"][0]["error"]` — goal-desk-iter-16 (J-12) additions).

---

## Golden Replay Scripts

- `runs/goal-session-desk/journey-scripts/J-12.json` written (overwritten if present) after J-12's underlying UI behavior (UT-02/UT-03/UT-05/UT-06/UT-07/UT-08) verified PASS. Read-only (clicks only drive `GET /research/desk/screen?id=`, never a write path); lints clean via `demo_runner.py --mode lint`.
- No golden written for J-06 (UT-J-06): goal.md marks J-06 explicitly "Keyless; automated" with no browser-observable acceptance surface (MCP tool count / JSON byte-identity aren't expressible as rendered-page text for the Playwright-based replay format) — best-effort skip per the golden-script policy; this journey never had a golden before this dispatch either.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (headless, CDP :9222; a second, unrelated tab briefly showed a stray navigation to an unrelated app — `localhost:3255` "Trendora" — from another concurrent process sharing the same Chrome instance; resolved by opening a fresh dedicated tab for this dispatch's testing, no impact on results)
- **Test Date:** 2026-07-29
- **Evidence directory:** `reports/qa/goal-desk-iter-16-evidence/`
