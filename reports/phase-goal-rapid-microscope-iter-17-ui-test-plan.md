# Phase goal-rapid-microscope-iter-17 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Ground Rules For This Round

- **This round ships zero `apps/frontend/**` changes and no new user-facing capability.** Every
  test below is a **regression check of an already-shipped surface**, not new-feature coverage —
  there is deliberately no happy-path or validation category this round, matching the phase spec's
  own "New user-facing capability: none" and the UI surface map's "0 frontend surfaces changed."
- **Do NOT click "Run Screen" (Scout Ledger) or "Run Walk-Forward" (Walk-Forward) in any test
  below.** The plan's own fixture discipline states no acceptance criterion may depend on a live
  Scout/Walk-Forward compute completing — a prior live Scout compute ran past 25 minutes without
  producing one completed candidate, with no reliable fast cancel.
- **Do NOT seed, mutate, or expose real Vault data.** Sealed exposure is family-level and
  single-shot — permanent, and a critical anti-goal this round. Validation Vault is read-only in
  the UI by design (no compute/seal/assign/expose control exists on the page) — just confirm it
  renders.
- **Do not add a browser assertion against the "Screen Comparison" or "Provenance" `/desk`
  sections.** Per the plan's own QA note, both only render after a screen has been computed and do
  not exist in the DOM on the current store — asserting against them would be a false failure, not
  a real one.
- **The one surface whose served payload actually changed this round —
  `GET /research/desk/micro/graduation`** — has no `/desk` section or MCP tool that reads it
  (confirmed by the ui-impact-analyst's own grep: zero hits for "graduation" in `page.tsx` or
  `app/mcp/*.py`). The only way to observe this round's real code change from a browser is direct
  navigation to the endpoint URL itself (UT-09) — this is J-07's own by-design "no golden script,
  LLM-fallback" check, carried unchanged since iteration 15.
- **Walk-Forward may legitimately show either its honest empty state or a real fold spec.** The
  dev handoff records that J-10's replay script was run for the first time this era and genuinely
  FAILED at step 11 in the Walk-Forward section, traced to pre-existing data drift in the real
  store unrelated to this round's code. Either rendering is acceptable for the tests below — do
  not file a new regression for this known, already-documented condition; only file one if the
  section throws a client error or renders something neither state describes.
- **Browser-console checks are high-value.** A hydration-error defect previously survived a full
  iteration because no test lane checked the console. Open DevTools → Console before expanding any
  section and re-check after every expand.
- **Capture notes for whoever executes this with browser automation:** (1) a viewport screenshot
  taken immediately after a large `scrollIntoView` can capture an unpainted/blank frame in headless
  Chrome — use a full-page capture for any below-the-fold section (every `/desk` section in this
  plan is below the fold). (2) `visibilityState: "hidden"` can freeze the Cockpit's live tape chart
  in a headless/background tab — if the chart looks static in a capture, cross-check against the
  backend payload before recording it as a failure.
- If `/desk` was rebuilt recently and looks stale, `rm -rf apps/frontend/.next` and restart the
  frontend before running this plan (a known recurring gotcha in this project).
- No screenshot ⇒ record `unknown`, never `passing`, per this round's own testing requirements
  (T-10). Below-the-fold sections need explicit element captures, not just a full-page scroll.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/desk` loads cleanly with zero console errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend running at http://localhost:8301
- No login required

**Steps:**
1. Open DevTools → Console tab
2. Navigate to `http://localhost:3301/desk`
3. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error banner
- The heading "Desk" (`data-testid="desk-title"`) is visible
- Scrolling down shows every section header collapsed with a closed "▸" arrow, including "Playbook
  Evidence", "Referee Registry", "Referee Adjudications", "Referee Runs", "Microscope Readiness",
  "Scout Ledger", "Walk-Forward", and "Validation Vault"
- Zero red errors in the browser console

---

### UT-02 — Cockpit live tape and chart still work (regression, J-10 sentinel)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the mode selector shows "Simulated" (the default)
3. Type `SIM-BUYER` into the ticker field (placeholder text "Ticker e.g. SIM-BUYER")
4. Click the "Watch" button

**Expected Result:**
- The chart renders and the live tape begins updating for `SIM-BUYER`
- No error banner appears
- If a headless capture shows a static-looking chart, cross-check against the backend payload
  before calling it a failure — `visibilityState: "hidden"` is known to freeze this specific chart
  in headless Chrome

---

### UT-03 — `/structure` load and Tradable Map still work (regression, J-10 sentinel)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type a symbol (e.g. `AAPL`) into the "Symbol" field
3. Type an as-of value into the "As-of (ET)" field (`data-testid="structure-as-of-input"`)
4. Click the "Load" button (`data-testid="structure-load-button"`)

**Expected Result:**
- No error banner appears
- The Tradable Map table (`data-testid="tradable-map-table"`) renders with band rows (or an honest
  "no bands" state if the chosen symbol/as-of pair has none — either is acceptable; a client error
  or blank page is not)
- The comparison dropdown (`data-testid="comparison-dataset-select"`) is present and selectable

---

### UT-04 — Microscope Readiness section renders without error (regression, J-01 relevance)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness

**Preconditions:**
- None (this test accepts whatever the real corpus's current shard count is)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open DevTools console
3. Click the "Microscope Readiness" section header
   (`data-testid="desk-section-expand-microReadiness"`)

**Expected Result:**
- The section expands (arrow "▸" becomes "▾") and shows a "Corpus Totals" table (either populated
  with real shard/session counts, or an honest zero state) without throwing
- Zero new console errors from the expansion
- This journey's own module (`micro_graduation.py`/`micro_sealed_evaluation.py`) is not read by
  this section at all — a pass here confirms the readiness aggregate surface survived this round's
  unrelated `micro_graduation.py` rewrite, per this round's stated regression risk

---

### UT-05 — Scout Ledger section renders without error (regression, J-04 relevance)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Scout Ledger

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Scout Ledger" section header (`data-testid="desk-section-expand-scoutLedger"`)
3. Do NOT click "Run Screen"

**Expected Result:**
- The section expands showing the "Run Screen" button and either the empty state "No candidates
  ledgered." or real registered-family rows — either is acceptable, a client error is not
- "Run History" shows either "No scout runs recorded yet." or real run rows
- Zero new console errors from the expansion

---

### UT-06 — Walk-Forward section renders without error (regression, J-05 relevance)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Walk-Forward

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Walk-Forward" section header (`data-testid="desk-section-expand-walkForward"`)
3. Confirm the "Run Walk-Forward" button is visible but do NOT click it

**Expected Result:**
- The section expands showing either "No fold specs registered." and "No walk-forward sequences
  run." (honest empty state) or a real fold spec/sequence — both are expected-acceptable outcomes
  this round per the dev handoff's documented pre-existing data-drift finding (J-10 replay step 11
  FAILED against the real store's Walk-Forward data, unrelated to this round's code)
- No client error / blank panel / thrown exception
- Zero new console errors from the expansion

---

### UT-07 — Validation Vault section renders without error (regression, read-only surface)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Validation Vault

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Validation Vault" section header
   (`data-testid="desk-section-expand-validationVault"`)

**Expected Result:**
- The section expands showing either "No shards recorded." / "No universes registered." (honest
  empty state) or real shard/universe rows — either is acceptable
- No compute/seal/assign/expose control is present anywhere in the section (it is read-only by
  design — confirms nothing this round accidentally added a live mutation control here)
- Zero new console errors from the expansion

---

### UT-08 — All three Referee sections render without error (regression, J-10 sentinel)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Referee Registry, Referee Adjudications, Referee Runs

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click "Referee Registry" (`data-testid="desk-section-expand-refereeRegistry"`)
3. Click "Referee Adjudications" (`data-testid="desk-section-expand-refereeAdjudications"`)
4. Click "Referee Runs" (`data-testid="desk-section-expand-refereeRuns"`)

**Expected Result:**
- Each of the three sections expands to show its own table/content without a client error
- Zero new console errors after any of the three expansions
- These sections read `referee_*.py`, which is byte-untouched this round (frozen rail,
  SHA-256-verified) — a pass here confirms nothing about this round's `micro_graduation.py` rewrite
  leaked into the Referee surfaces

---

### UT-09 — `GET /research/desk/micro/graduation` serves the honest empty-state body directly (smoke/error — J-07's own no-golden-script check)

**Type:** smoke
**Priority:** P1
**Surface:** `http://localhost:8301/research/desk/micro/graduation` (direct backend navigation, no
`/desk` section reads this endpoint — this is the only way to observe this round's actual served
payload from a browser)

**Preconditions:**
- Backend running at http://localhost:8301
- Real Scout/Graduation ledger has no ledgered candidates today (honest empty-state expected; if a
  real family exists, the same "HTTP 200, valid JSON, no error page" check still applies, and
  `sealed_evaluations` inside the response should be examined for the tri-state verdict / provenance
  fields this round added, per the plan's data-contract note)

**Steps:**
1. Navigate directly to `http://localhost:8301/research/desk/micro/graduation` in the browser
   address bar (this is a direct backend GET, not a frontend route — no `/desk` link points here)

**Expected Result:**
- HTTP 200 — the page shows raw JSON, not a browser error page
- On an empty store: body reads `{"families": [], "message": "No candidates ledgered.", ...}`
  (exact honest-empty-state wording per the ui-impact-analyst's confirmed check)
- The response is valid, parseable JSON with no 500/stack-trace text visible
- This is the ONLY browser-observable evidence this round's `micro_sealed_evaluation.py` +
  `micro_graduation.py` changes are live and serving correctly — no `/desk` page or MCP tool
  fetches this endpoint, so nothing else in the UI can confirm or contradict this check

---

### UT-10 — Nav bar unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** top navigation, all pages

**Preconditions:**
- None

**Steps:**
1. From any page (`/`, `/structure`, or `/desk`), look at the top navigation

**Expected Result:**
- Exactly 3 links are visible, labeled "Cockpit", "Structure", "Desk" — no fourth link, matching
  this round's "no navigation changes, no new `/desk` section" scope

---

### UT-11 — This round's new sealed-verdict data stays correctly invisible in the UI (ux — confirms absence is by design, not a defect)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` (whole page)

**Preconditions:**
- Complete UT-01 through UT-08 first (all sections expanded at least once)

**Steps:**
1. With every `/desk` section expanded from the tests above, use the browser's page search
   (Ctrl+F / Cmd+F) to search the rendered page text for the strings "sealed_evaluation",
   "SEALED_PASS_RULE", and "confirmation_boundary"

**Expected Result:**
- Zero matches anywhere on the rendered `/desk` page — this round's new tri-state verdict and
  lineage-boundary derivation are real, tested, and served at
  `GET /research/desk/micro/graduation` (see UT-09), but by design surface nowhere in the UI yet
  (per the phase spec's "New information displayed: None" and "Not Visible Yet" sections). A match
  here would mean an unplanned UI change slipped in — flag it, do not treat it as a bonus feature

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, zero console errors | smoke | P1 | `/desk` |
| UT-02 | Cockpit live tape + chart | regression | P1 | `/` |
| UT-03 | `/structure` load + Tradable Map | regression | P1 | `/structure` |
| UT-04 | Microscope Readiness renders | regression | P1 | `/desk` → Microscope Readiness |
| UT-05 | Scout Ledger renders | regression | P1 | `/desk` → Scout Ledger |
| UT-06 | Walk-Forward renders (either state acceptable) | regression | P1 | `/desk` → Walk-Forward |
| UT-07 | Validation Vault renders, still read-only | regression | P1 | `/desk` → Validation Vault |
| UT-08 | All three Referee sections render | regression | P1 | `/desk` → Referee ×3 |
| UT-09 | Graduation endpoint serves honest empty state | smoke | P1 | `GET /research/desk/micro/graduation` |
| UT-10 | Nav bar unaffected | regression | P2 | nav |
| UT-11 | New sealed-verdict data stays invisible (by design) | ux | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-06 explicitly accepts either
rendering (honest empty or real fold data) as passing per the documented pre-existing data-drift
finding — only a client error or blank panel there is a real failure.
