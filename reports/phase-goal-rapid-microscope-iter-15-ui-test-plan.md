# Phase goal-rapid-microscope-iter-15 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-15
**Date:** 2026-08-19
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Ground Rules For This Round

- **Do NOT click "Run Screen" (Scout Ledger) or "Run Walk-Forward" (Walk-Forward) in any test
  below.** A live Scout compute has previously run past 25 minutes against the real corpus without
  producing one completed candidate — no test in this plan depends on either finishing.
- **Do NOT seed, mutate, or expose real Vault data.** Sealed exposure is single-shot and permanent.
  Every test below either reads the real store's current honest state or, where explicitly marked
  "fixture-scoped", uses an isolated, throwaway store — never the operator's real `.data` directory.
- The real store's Scout ledger is genuinely empty (zero families) and Microscope Readiness's
  `sealed_tranche`/`withheld_excluded` are genuinely all-zero today. The real Walk-Forward ledger,
  by contrast, already has one real sequence (`seq-d39d20e47af24671`). Tests below are written
  against these actual states, not assumed seed data.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads with the four Rapid-Microscope sections present but collapsed (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend running at http://localhost:8301
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- Section headers "Microscope Readiness", "Scout Ledger", "Walk-Forward", "Validation Vault" are
  all visible, each showing a closed `▸` arrow (collapsed by default)
- No red errors in the browser console

---

### UT-02 — Sealed Tranche aggregate renders the real corpus's honest zero state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness

**Preconditions:**
- Real `.data` store's `sealed_tranche`/`joinable_corpus.withheld_excluded` are all zero (today's
  actual state — no setup required)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Microscope Readiness" section header
3. Scroll to the block titled "Sealed Tranche (Aggregate Only)", directly below "Corpus Totals"

**Expected Result:**
- The row "Sealed shard count" shows `0` (an actual zero, not blank)
- The row "Sealed symbol-days" shows `0`
- The row "Joinable corpus — withheld (excluded)" shows `0`
- Below the 3-row table, the empty state "No sealed shards recorded." appears (no per-universe
  table, since `by_universe` is empty)
- These three values byte-match the numbers in the raw JSON at
  `http://localhost:8301/research/desk/micro/readiness` under `sealed_tranche.shard_count`,
  `sealed_tranche.symbol_days`, and `joinable_corpus.withheld_excluded`

---

### UT-03 — Sealed Tranche's per-universe area renders the correct branch for empty data (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Microscope Readiness → Sealed Tranche block

**Preconditions:**
- Same as UT-02 — real store's `sealed_tranche.by_universe` is an empty object today

**Steps:**
1. Navigate to `http://localhost:3301/desk`, click "Microscope Readiness"
2. Locate the area below the 3-row Sealed Tranche table

**Expected Result:**
- The text "No sealed shards recorded." appears — NOT an empty `<table>` with just a header row,
  NOT blank space, and NOT a JavaScript error
- Right-click that text → Inspect → confirm the element has
  `data-testid="micro-readiness-sealed-by-universe-empty"`
- No `data-testid="micro-readiness-sealed-by-universe-table"` element exists anywhere in the DOM
  while this empty state is showing (confirms the empty/populated branches are mutually exclusive)

---

### UT-04 — Expanding a real Walk-Forward sequence's detail produces zero new console errors (regression — core bugfix)

**Type:** regression
**Priority:** P1 — this is the iteration's headline defect fix (DoD item, TC-7) and the auditor's
own named highest-value check this round
**Surface:** `/desk` → Walk-Forward

**Preconditions:**
- Real Walk-Forward ledger already has one recorded sequence (`seq-d39d20e47af24671`) — no setup
  required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Open the browser DevTools console (F12 → Console tab); note there are zero red errors at this
   point (a harmless React DevTools notice is fine)
3. Click the "Walk-Forward" section header
4. Locate the sequence card and click the small "detail" text immediately after the "Sequence
   verdict:" line (inside the inline `<details>`)
5. Re-check the DevTools console

**Expected Result:**
- After step 3: the section expands showing a "Fold Specs" block and at least one sequence card
  with a "Sequence verdict:" line; zero new console errors from the expansion itself
- After step 4: the `<details>` opens, revealing the verdict JSON in a `<pre>` block
- **No new console errors appear, and no red Next.js dev-overlay "Issues" badge appears anywhere
  on screen** (this exact interaction previously produced a "5 Issues" badge before this
  iteration's fix)

---

### UT-05 — Scout family header change is structurally correct (not live-observable today) (regression)

**Type:** regression
**Priority:** P2 — informational; the real data needed to observe this live does not exist yet
**Surface:** `/desk` → Scout Ledger

**Preconditions:**
- Real Scout ledger has zero registered families today

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Scout Ledger" section header

**Expected Result:**
- The section expands cleanly with zero console errors
- Because the real ledger is empty, only the empty state "No candidates ledgered." is visible — the
  new `family.family_root_id` text cannot be exercised through the browser this round
- This is expected, not a failure: the field addition is confirmed instead by `tsc --noEmit`
  passing against `family.family_root_id: string` on the fetched `ScoutFamily` type, and by the
  backend's own byte-identity contract test proving the field is served whenever a family exists

---

### UT-06 — Walk-Forward empty-sequences copy fix is structurally correct (not live-observable today) (regression)

**Type:** regression
**Priority:** P2 — informational; the real ledger already has data, so the empty-state branch this
fix touches cannot currently render
**Surface:** `/desk` → Walk-Forward

**Preconditions:**
- Real Walk-Forward ledger already has one recorded sequence today (so `sequences.length === 0` is
  false)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Walk-Forward" section header

**Expected Result:**
- The section shows the real sequence card (`seq-d39d20e47af24671`), NOT the empty state — this is
  expected given today's real data
- The copy fix ("No walk-forward sequences run.") is confirmed instead by reading `page.tsx:6520`:
  the `EmptyState` `title` prop for `data-testid="walk-forward-sequences-empty"` is the literal
  string `"No walk-forward sequences run."`, not "No candidates ledgered."

---

### UT-07 — Validation Vault's testid is present in all three states: success, loading, unavailable (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Validation Vault

**Preconditions:**
- Part A needs the backend running normally
- Part C needs the ability to stop the backend process

**Steps:**
1. **Part A (success, baseline):** Navigate to `http://localhost:3301/desk`, click "Validation
   Vault". Confirm "No shards recorded." and "No universes registered." both render, with no
   button anywhere in the section. Right-click anywhere inside the section → Inspect → confirm an
   ancestor element carries `data-testid="validation-vault-section"`.
2. **Part B (loading, new this iteration):** Open DevTools → Network tab → set throttling to "Slow
   3G". Reload `http://localhost:3301/desk`, then immediately click "Validation Vault" before the
   fetch resolves. Right-click the pulsing loading skeleton → Inspect → confirm the nearest
   ancestor `<div>` also carries `data-testid="validation-vault-section"`.
3. **Part C (unavailable, new this iteration):** Reset Network throttling to "No throttling". Stop
   the backend process. Reload `http://localhost:3301/desk`, click "Validation Vault". Confirm an
   amber panel reading "The validation vault could not be loaded." (or similar) appears. Inspect
   Element on it → confirm its wrapping element also carries
   `data-testid="validation-vault-section"`.
4. Restart the backend process before continuing to any other test in this plan.

**Expected Result:**
- All three states — success, loading, unavailable — expose `data-testid="validation-vault-section"`
  on an ancestor element. Before this iteration, only the success state did.

---

### UT-08 — Pre-existing `/desk` sections are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Signals, Referee Registry, Referee Adjudications, Referee Runs

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the "Playbook Signals" panel is visible without clicking anything (it is a plain
   `Panel`, not collapsible)
3. Click "Referee Registry", then "Referee Adjudications", then "Referee Runs" in turn

**Expected Result:**
- "Playbook Signals" renders its content immediately, above the fold, with no expand action needed
- Each of the three Referee sections expands to show its own table/content with no error panel and
  no console error
- The pre-existing "Corpus Totals" table and "Legacy Tick Shards" block inside Microscope Readiness
  (expand it too) render exactly as before, unaffected by the new Sealed Tranche block beside them

---

### UT-09 — Nav bar and sibling routes are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `NavBar` (all pages), `/structure`, `/` (Cockpit)

**Preconditions:**
- None

**Steps:**
1. From `http://localhost:3301/desk`, look at the top navigation bar
2. Navigate to `http://localhost:3301/structure`
3. Navigate to `http://localhost:3301/`
4. In the ticker field (placeholder "Ticker e.g. SIM-BUYER"), type `SIM-BUYER`, then click "Watch"

**Expected Result:**
- Step 1: exactly 3 links are visible, labeled "Cockpit", "Structure", "Desk" — no fourth link
- Step 2: `/structure` loads without an error banner; the Tradable Map table
  (`data-testid="tradable-map-table"`) renders and the comparison dropdown
  (`data-testid="comparison-dataset-select"`) is present and selectable
- Step 3: `/` (Cockpit) loads without an error banner
- Step 4: the chart renders and the live tape begins updating for `SIM-BUYER`. If the chart looks
  static in a headless capture, cross-check against the backend payload before calling it a
  failure — `visibilityState: "hidden"` is known to freeze this specific chart in headless Chrome

---

### UT-10 — J-07 re-verification: direct navigation to the Graduation endpoint (regression re-verification)

**Type:** regression
**Priority:** P1 — explicitly non-deferrable this round (DoD item, TC-11)
**Surface:** Backend endpoint, no frontend page (`http://localhost:8301/research/desk/micro/graduation`)

**Preconditions:**
- Backend running at http://localhost:8301
- This route is on the BACKEND port, not the frontend — there is no `/research/*` proxy on 3301,
  and no link to it from any page (by design)

**Steps:**
1. Navigate directly to `http://localhost:8301/research/desk/micro/graduation` in the browser

**Expected Result:**
- HTTP 200 response
- The JSON body shown contains `"families":[]`, `"message":"No candidates ledgered."`, and
  `"chain_verification":{"ok":true,"failed_at_row":null,"reason":null}` — matching today's real,
  honest-empty graduation state

---

### UT-11 — Sealed Tranche information is discoverable within 2 clicks of the home page (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation → `/desk` → Microscope Readiness

**Steps:**
1. Navigate to `http://localhost:3301/` (Cockpit, the home page)
2. Click "Desk" in the top navigation
3. Click the "Microscope Readiness" section header

**Expected Result:**
- 2 clicks total reach the new information — clicking "Desk" (click 1) then "Microscope Readiness"
  (click 2) reveals the "Sealed Tranche (Aggregate Only)" block
- The block's own heading text is unambiguous ("Sealed Tranche (Aggregate Only)") and its helper
  copy explicitly states the aggregate-only guarantee ("A recorded tranche is one opaque pool
  until its shards are exposed — aggregate counts only, never a per-shard identity for a withheld
  shard.")

---

### UT-12 — [OPTIONAL, backend-assisted] Non-zero Sealed Tranche + differing `family_root_id` render correctly via an isolated fixture backend

**Type:** validation / happy-path (supplementary — NOT required for a PASS verdict this round)
**Priority:** P3 — optional; already independently proven by the code reviewer via a constructed
fixture trace through production code. Include this only if the browser-qa lane has the ability to
stand up a second, isolated backend process.
**Surface:** `/desk` → Microscope Readiness, Scout Ledger (against a scoped rig, NOT the shared dev
instance)

**Preconditions:**
- A SEPARATE backend process, started with its own isolated, empty temp directories via env vars
  (e.g. `TAPEOLOGY_MICRO_SCOUT_DIR`, `TAPEOLOGY_MICRO_VAULT_DIR`, or an equivalent scoped dataset
  dir) — never pointed at the operator's real `.data` store
- Seeded via the SAME production write functions the developer/reviewer used —
  `vault.register_universe(...)` + `vault.seal_shard(...)` for a non-zero `sealed_tranche`, and
  `ScoutLedger(scout_dir).append_row(...)` for a family whose `family_root_id` differs from its
  `family_id` — never via a live Scout/Walk-Forward compute button
- A frontend instance pointed at that scoped backend's port

**Steps:**
1. With the scoped backend seeded as above, navigate to that frontend instance's `/desk`
2. Click "Microscope Readiness", locate the Sealed Tranche block
3. Click "Scout Ledger", locate the seeded family's header

**Expected Result:**
- "Sealed shard count" and "Sealed symbol-days" show non-zero values matching the seeded shard; the
  per-universe table (not the empty state) renders, listing the seeded `universe_id` with correct
  counts
- The Scout family header shows both the seeded `family_id` and a `family_root_id` that differs
  from it, in the format `"<family_id> (root <family_root_id>) — N variants tried"`
- No symbol, session date, dataset id, raw checksum, or per-shard `exposure_state` for the sealed
  shard appears anywhere in the rendered markup (aggregate-only discipline holds under real
  non-zero data, not just in the honest-zero case)
- **Do not run this against the operator's real `.data` store under any circumstance.**

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, 4 sections present & collapsed | smoke | P1 | `/desk` |
| UT-02 | Sealed Tranche renders honest zero state | happy-path | P1 | `/desk` → Microscope Readiness |
| UT-03 | Sealed Tranche empty-by_universe branch is correct | validation | P2 | `/desk` → Microscope Readiness |
| UT-04 | Walk-Forward detail expand → zero new console errors | regression | P1 | `/desk` → Walk-Forward |
| UT-05 | Scout family_root_id — structurally correct, not live-observable | regression | P2 | `/desk` → Scout Ledger |
| UT-06 | WF empty copy fix — structurally correct, not live-observable | regression | P2 | `/desk` → Walk-Forward |
| UT-07 | Vault testid present in success/loading/unavailable | error | P2 | `/desk` → Validation Vault |
| UT-08 | Pre-existing `/desk` sections unaffected | regression | P1 | `/desk` |
| UT-09 | Nav bar + `/structure` + Cockpit unaffected | regression | P1 | nav, `/structure`, `/` |
| UT-10 | J-07 re-verification via direct backend navigation | regression | P1 | backend `:8301` |
| UT-11 | Sealed Tranche discoverable within 2 clicks | ux | P3 | nav → `/desk` |
| UT-12 | [Optional] Non-zero rendering via isolated fixture rig | validation/happy-path | P3 | `/desk` (scoped rig) |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-12 is explicitly optional and does
not gate the verdict — it documents how a deeper, non-live-observable check could be performed if
the browser-qa lane has the tooling for an isolated backend.
