# Phase goal-observation-contract-iter-6 — UI Test Plan

**Phase:** goal-observation-contract-iter-6
**Date:** 2026-09-05
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL (required for every `/tape/*/observation` navigation below):** http://localhost:8301

---

## Read this first

This iteration ships **zero new user-facing capability** (see
`reports/phase-goal-observation-contract-iter-6-user-visible-changes.md`). Its two purposes are (1)
a whole-product regression sentinel (J-06) and (2) closing two evidence gaps a prior iteration left
open by independently re-reading an already-shipped JSON endpoint (J-04, J-02). Consequently:

- There is no new form, so there are **no validation test cases** in this plan — a form-validation
  case would have to be invented against an unchanged form, which the `manual-ui-test-plan-generator`
  skill's own rule ("one test per form that was added or changed") does not call for here.
- "Happy path" below means the two evidence-closure journeys (J-04, J-02) — the one substantive,
  clickable thing this iteration actually does — not a create/edit flow, since none exists on this
  surface.
- The observation JSON is served **only** from the backend origin (`:8301`); typing the same path
  on the frontend origin (`:3301`) hits Next.js's own generic 404 page, not the artifact — this
  bit developer/QA passes on iteration 5 and is called out explicitly in every relevant test below.

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit loads with the Data source controls intact (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
  (`scripts/dev.sh` default pair)
- No login (the app has no auth)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or a Next.js error overlay
- The text "Tapeology" is visible in the top-left of the header
- A control group (aria-label "Data source") shows exactly three options: "Live", "Historical", "Simulated"
- With "Simulated" selected (the default), a text field labeled "Ticker" is visible
- No console errors

---

### UT-02 — Structure page loads unchanged (smoke / regression)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- A heading reading exactly "Structure" is visible (`data-testid="structure-title"`)
- No new panel, link, or control is present compared to iteration 5
- No console errors

---

### UT-03 — Desk page loads unchanged (smoke / regression)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at `http://localhost:3301`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- A heading reading exactly "Desk" is visible (`data-testid="desk-title"`)
- No new panel, link, or control is present compared to iteration 5
- No console errors

---

### UT-04 — Observation JSON serves the full artifact for a watched Sim ticker (smoke; J-01/J-05 regression)

**Type:** smoke
**Priority:** P1
**Surface:** backend `GET /tape/{ticker}/observation`

**Preconditions:**
- No ticker currently watched

**Steps:**
1. Navigate to `http://localhost:3301/`
2. In the "Data source" group, click "Simulated" (it is the default; click it anyway to be explicit)
3. Type `SIM-BIDABS` into the "Ticker" field
4. Click the green "Watch" button
5. Wait (up to 15 seconds) until the status dot in the top-right of the header reads "live"
6. Open a new browser tab and navigate to `http://localhost:8301/tape/SIM-BIDABS/observation`

**Expected Result:**
- The response is raw JSON (not an HTML page) beginning with
  `{"schema_version":"tape-observation-v1","provider":"tapeology","ticker":"SIM-BIDABS"`
- The JSON contains the top-level keys `tape_state`, `confidence`, `warm`, `primary_window`,
  `features`, `trade_event_count`, `market`, `observations`, `lifecycle`, `timing`, `source`,
  `engine_identity`, `implementation_provenance`, `observation_hash`, `artifact_hash`
- `engine_identity.config_fingerprint` reads `08e471b10130e1e2`

---

### UT-05 — Happy path: J-04 paused-reload shows identical `observation_hash`, different `generated_at_utc`/`artifact_hash`

**Type:** happy-path
**Priority:** P1
**Surface:** `/` + backend `GET /tape/{ticker}/observation`

**Preconditions:**
- `SIM-BIDABS` is being watched and reads "live" (continue directly from UT-04, or repeat its steps 1-5)

**Steps:**
1. On `http://localhost:3301/`, click the amber "Pause" button (aria-label "Pause watching") next to the "Watching SIM-BIDABS" text
2. Confirm the status dot changes to "paused"
3. On the JSON tab, navigate to `http://localhost:8301/tape/SIM-BIDABS/observation` and record the values of `observation_hash`, `generated_at_utc`, and `artifact_hash`
4. Reload the same URL a second time and record the same three values again

**Expected Result:**
- `observation_hash` is byte-identical between the two reads
- `generated_at_utc` differs between the two reads
- `artifact_hash` differs between the two reads
- Together these demonstrate the contract's equivalence-identity (`observation_hash`) versus
  exact-evidence-identity (`artifact_hash`) distinction, visibly, on the same paused artifact

---

### UT-06 — Happy path: J-02 own steps — three honest time concepts read independently

**Type:** happy-path
**Priority:** P1
**Surface:** backend `GET /tape/{ticker}/observation`

**Preconditions:**
- `SIM-BIDABS` freshly watched and reading "live" (not paused)

**Steps:**
1. On `http://localhost:3301/`, watch `SIM-BIDABS` in Simulated mode and wait for the status dot to read "live"
2. Navigate to `http://localhost:8301/tape/SIM-BIDABS/observation`
3. Independently read and record the values of `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc`, and `generated_at_utc`

**Expected Result:**
- `observed_at_utc` starts with `2024-01-02T14:3` (the synthetic Sim anchor clock)
- `available_at_utc` is `null`
- `availability_basis` reads `simulated_not_applicable`
- `timing.settled_at_utc` and `generated_at_utc` both carry today's real-world date — visibly a
  different day from `observed_at_utc`
- This evidence must be filed under J-02's own test id, never reused from a J-01 screenshot (the
  gap this iteration is explicitly closing, per `state/assumptions.md` iter-5)

---

### UT-07 — Error: observation JSON 404s for an unwatched ticker (J-05 regression)

**Type:** error
**Priority:** P1
**Surface:** backend `GET /tape/{ticker}/observation`

**Preconditions:**
- Ticker `ZZZZ` has never been watched

**Steps:**
1. Navigate to `http://localhost:8301/tape/ZZZZ/observation`

**Expected Result:**
- Response body reads `{"detail":"Ticker 'ZZZZ' is not being watched"}`
- Body shape is byte-identical to `http://localhost:8301/tape/ZZZZ/state`'s existing 404 body
- No crash, no HTML stack trace, no 200 response

---

### UT-08 — Regression: J-03 full lifecycle cycle (Watch → Pause → Resume → Stop → re-Watch)

**Type:** regression
**Priority:** P1
**Surface:** `/` + backend `GET /tape/{ticker}/observation`

**Preconditions:**
- No ticker currently watched

**Steps:**
1. On `http://localhost:3301/`, watch `SIM-BIDABS` (Simulated), wait for the status dot to read "live"; open `http://localhost:8301/tape/SIM-BIDABS/observation` and note `source.session_id` (call it SID-1) and `timing.settled_at_utc`
2. Click "Pause"; reload the observation JSON; confirm `lifecycle.stream_status` is `paused`, `lifecycle.paused` is `true`, `tape_state` is unchanged from step 1, and `timing.settled_at_utc` is unchanged from step 1
3. Click "Resume" (aria-label "Resume watching"); reload the JSON; confirm `lifecycle.stream_status` is `live` again
4. Click "Stop" (aria-label "Stop watching"); reload `http://localhost:8301/tape/SIM-BIDABS/observation`; confirm the response is the same 404 body as UT-07
5. Back on `/`, click "Watch" again for `SIM-BIDABS` (Simulated); wait for "live"; reload the observation JSON; confirm `source.session_id` differs from SID-1 while `source.source_mode` is `sim` and `source.data_feed` is `sim`

**Expected Result:**
- Every sub-step above holds exactly as described — this is the pre-existing J-03 journey,
  re-verified this iteration with zero code change

---

### UT-09 — Regression: J-01 full identity/provenance field set (already-shipped baseline)

**Type:** regression
**Priority:** P1
**Surface:** backend `GET /tape/{ticker}/observation`

**Preconditions:**
- `SIM-BIDABS` watched and live (may reuse UT-04's watch)

**Steps:**
1. Open `http://localhost:8301/tape/SIM-BIDABS/observation`
2. Confirm, in addition to UT-04's key set: `engine_identity.engine_semantics_version` equals `tape-engine-v1`, `engine_identity.profile_id` equals `default`, `source.session_id` is non-empty, `source.session_started_at_utc` ends in `Z`, `implementation_provenance.engine_source_hash` is a 64-hex-character string, and both `observation_hash` and `artifact_hash` are 64-hex-character strings

**Expected Result:**
- All values are present and correctly formatted exactly as listed — no regression from iteration 5

---

### UT-10 — Regression: top nav still shows exactly three links

**Type:** regression
**Priority:** P2
**Surface:** nav (`data-testid="app-nav"`, all pages)

**Steps:**
1. On any of `http://localhost:3301/`, `/structure`, `/desk`, look at the top navigation bar

**Expected Result:**
- Exactly three links are visible, in this order: "Cockpit", "Structure", "Desk"
- No additional link (e.g. no "Observation", "Contract", or "Guards" link) has been added

---

### UT-11 — UX: the observation endpoint stays deliberately undiscoverable from the UI

**Type:** ux
**Priority:** P2
**Surface:** `/`, `/structure`, `/desk`, nav

**Steps:**
1. On each of `/`, `/structure`, `/desk`, and the top nav, look for any link, button, badge, or text that mentions "observation", "TapeObservation", or that points at a `/tape/*/observation` URL

**Expected Result:**
- None exists anywhere in the rendered UI. The artifact is reachable only by typing the URL
  directly or via the MCP `get_endpoint` tool — exactly as this era's Design Direction specifies
  ("no page is introduced anywhere in this era... machine-only surface — no nav entry"). This is
  the correct, intended state, not a bug or an oversight.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads with Data source controls | smoke | P1 | `/` |
| UT-02 | Structure page loads unchanged | smoke | P1 | `/structure` |
| UT-03 | Desk page loads unchanged | smoke | P1 | `/desk` |
| UT-04 | Observation JSON serves for a watched ticker | smoke | P1 | backend `/tape/{ticker}/observation` |
| UT-05 | J-04 paused-reload identity check | happy-path | P1 | backend `/tape/{ticker}/observation` |
| UT-06 | J-02 own-steps time-field readout | happy-path | P1 | backend `/tape/{ticker}/observation` |
| UT-07 | Observation JSON 404s for unwatched ticker | error | P1 | backend `/tape/{ticker}/observation` |
| UT-08 | J-03 full lifecycle cycle | regression | P1 | `/` + backend observation JSON |
| UT-09 | J-01 full identity/provenance field set | regression | P1 | backend `/tape/{ticker}/observation` |
| UT-10 | Top nav unchanged (3 links) | regression | P2 | nav |
| UT-11 | Observation endpoint stays undiscoverable | ux | P2 | `/`, `/structure`, `/desk`, nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
