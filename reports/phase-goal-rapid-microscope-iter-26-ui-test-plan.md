# Phase goal-rapid-microscope-iter-26 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Scope note

This iteration shipped no new UI capability — every changed file is a Python backend module
(`micro_readiness.py`, `micro_join.py`, `micro_routes.py`) that adds an internal SQLite cache for an
already-served field and derives two already-hardcoded selector sets from one canonical source. The
`/desk` page's two touched sections — "Microscope Readiness" (J-01) and "Scout Ledger" (J-08) — must
render **byte-identical** values to before this iteration; that is the entire acceptance bar (TC-7,
TC-8 in the phase spec). Because there is no new workflow or form, the **happy-path** and
**validation** test types from the standard template are not applicable this iteration — they are
recorded below as N/A with the reasoning, per honesty policy, rather than manufactured against a
non-existent new flow.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at `http://localhost:3301`
- Backend is running and reachable (no login required — this app has no auth gate)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The top nav bar (`data-testid="app-nav"`) shows a "Desk" link highlighted as the active page
  (`aria-current="page"`)
- The text "Playbook Signals" is visible somewhere on the page (the first section, rendered above
  Microscope Readiness)
- Both "Microscope Readiness" and "Scout Ledger" section headers are visible further down the page,
  each showing a collapsed `▸` marker (sections start closed)
- No console errors

---

### UT-02 — Microscope Readiness section renders byte-identical corpus figures (regression — J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness section (`data-testid="micro-readiness-section"`)

**Preconditions:**
- On `http://localhost:3301/desk`, page freshly loaded, "Microscope Readiness" section collapsed

**Steps:**
1. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
2. Wait for the section body to mount (its `aria-expanded` attribute should read `"true"`)
3. Read the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`): Distinct symbol-days,
   Distinct datasets, RTH minutes covered, Session-equivalents, Referee tick-gate (symbol-days)
4. Scroll to the "Sealed Tranche (Aggregate Only)" table
   (`data-testid="micro-readiness-sealed-tranche-table"`) and read "Joinable corpus — band touches"
   (`data-testid="micro-readiness-band-touch-count"`)
5. Scroll to the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) and read the
   "Split provenance" column for each row

**Expected Result:**
- The five Corpus Totals figures match the values registered against the QA fixture rig in
  `runs/goal-session-rapid-microscope/state/journey-history.json`'s J-01 note: **2** distinct
  symbol-days, **3** distinct datasets, **1.75** RTH minutes covered, **0.0045** session-equivalents,
  **150** referee tick-gate (symbol-days). (If the running instance is pointed at a different dataset
  fixture than the QA rig, the exact numbers may differ — in that case, compare against a screenshot
  taken immediately before this iteration's code was deployed instead of these literal numbers.)
- "Joinable corpus — band touches" shows either a numeric count or the literal text "not enumerated" —
  never blank, never an error string
- At least one shard row's "Split provenance" cell reads the literal text `hand_assigned`
- No value in this section should differ from a pre-iteration capture of the same page — the cache
  change must not alter any displayed number

---

### UT-03 — Scout Ledger section renders byte-identical pilot-family rows (regression — J-08)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Scout Ledger section (`data-testid="scout-ledger-section"`)

**Preconditions:**
- On `http://localhost:3301/desk`, page freshly loaded, "Scout Ledger" section collapsed

**Steps:**
1. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)
2. Wait for the section body to mount
3. Read the "Ledger chain verification:" line (`data-testid="scout-ledger-chain-verification"`)
4. For each rendered pilot-study family block (`data-testid="scout-family-<family_id>"`), read its
   header line and its trial-row table

**Expected Result:**
- "Ledger chain verification:" reads `ok` (or, if broken, `failed at row N (<reason>)` — this
  iteration's selector dedup must not be the cause of a broken chain; a change from `ok` to `failed`
  here would be a genuine regression to flag)
- Each family header still reads exactly `<family_id> (root <family_root_id>) — N variants tried`,
  with the text `variants tried` present
- Each family's trial-row table still has all nine columns: Candidate, Feature, Horizon, Registered,
  Decision, Reason, Notes, Withheld excluded, Screen detail — no column missing, added, or reordered
- The set of pilot-study families and their trial counts (`variants_tried`) is unchanged from a
  pre-iteration capture of the same page (the selector-table dedup changes only which code path
  computes the classification, never the classification result itself)

---

### UT-04 — Band-touch value is stable across a second expand/collapse cycle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness section, "Joinable corpus — band touches" row

**Preconditions:**
- On `http://localhost:3301/desk`, page freshly loaded

**Steps:**
1. Click the "Microscope Readiness" section header (`data-testid="desk-section-expand-microReadiness"`)
   to expand it; note the "Joinable corpus — band touches" value
   (`data-testid="micro-readiness-band-touch-count"`)
2. Click the same header again to collapse the section
3. Click the same header a third time to re-expand it
4. Read "Joinable corpus — band touches" again
5. Refresh the whole page (F5), then repeat step 1

**Expected Result:**
- The "Joinable corpus — band touches" value read in step 1, step 4, and step 5 is identical every
  time — this is the specific claim the new `MicroBandTouchCache` must not violate (a warm cache
  entry must serve the same count as the original uncached computation)
- No loading spinner or error state should appear on the second/third expand within the same page
  session (step 2–4) — the section body simply remounts from already-fetched client state; only the
  full-page refresh in step 5 triggers a new network request

---

### UT-05 — Corrupted band-touch cache degrades to a full miss, never an error (error / resilience)

**Type:** error
**Priority:** P3 (informational — requires backend file-system access, not a pure-browser check)
**Surface:** `/desk` — Microscope Readiness section

**Preconditions:**
- Backend is running with a known dataset directory
- Operator has shell access to the backend host to locate and corrupt the cache file (this step is
  outside what a browser-only operator can do — included here for completeness of the error-path
  coverage the phase spec's TC-5 describes, and is expected to be exercised by an automated test, not
  manually, in normal QA)

**Steps:**
1. Locate the band-touch cache DB file: by default `micro_band_touch_cache.db`, co-located next to the
   dataset directory (or wherever `TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB` points, if set)
2. With the backend stopped, overwrite the file with random bytes (e.g.
   `head -c 200 /dev/urandom > <path-to-file>`) to simulate corruption
3. Restart the backend
4. Navigate to `http://localhost:3301/desk` and expand "Microscope Readiness"

**Expected Result:**
- The page still returns HTTP 200 and renders the Microscope Readiness section normally — no error
  banner, no blank panel, no crash
- "Joinable corpus — band touches" shows a freshly-computed value (recomputed from the corrupted cache
  being treated as a full miss), matching the value it showed before the corruption was introduced
- This mirrors the existing `MicroReadinessCache` self-heal contract this iteration's cache was built
  to match

---

### UT-06 — Both touched sections are discoverable from a fresh page load (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` navigation and section headers

**Steps:**
1. Navigate to `http://localhost:3301` (home/Cockpit)
2. Click "Desk" in the top nav bar (`data-testid="nav-link"`, `data-label="Desk"`)
3. On the resulting `/desk` page, scroll down without clicking anything

**Expected Result:**
- Clicking "Desk" navigates to `http://localhost:3301/desk`
- Scrolling down, the "Microscope Readiness" section header is visible with a `▸` (collapsed) marker,
  and the "Scout Ledger" section header is visible directly below it, also collapsed
- Both headers are real `<button>` elements (keyboard-focusable, `aria-expanded="false"` initially) —
  not inert text or a row-click-only control

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness renders byte-identical figures (J-01) | regression | P1 | `/desk` Microscope Readiness |
| UT-03 | Scout Ledger renders byte-identical family rows (J-08) | regression | P1 | `/desk` Scout Ledger |
| UT-04 | Band-touch value stable across repeat expand/refresh | regression | P1 | `/desk` Microscope Readiness |
| UT-05 | Corrupted cache degrades to a full miss, never an error | error | P3 | `/desk` Microscope Readiness |
| UT-06 | Both sections discoverable from a fresh page load | ux | P2 | `/desk` navigation |

**Happy-path / validation:** N/A this iteration — no new form, workflow, or capability was added; both
touched surfaces are pre-existing, and the whole point of this iteration is that they behave
identically to before (see UT-02, UT-03, UT-04).

**P1 tests must all pass for browser QA verdict to be PASS.**
