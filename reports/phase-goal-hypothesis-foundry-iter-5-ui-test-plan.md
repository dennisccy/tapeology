# Phase goal-hypothesis-foundry-iter-5 — UI Test Plan

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads and the Hypothesis Foundry section is reachable (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301
- No login required (read-only operator surface)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Scroll down (or use browser find) until the section header row reading "Hypothesis Foundry" is visible

**Expected Result:**
- Page renders without a blank screen or error message
- A collapsible section header button with the text "Hypothesis Foundry" is visible (button has `data-testid="desk-section-expand-hypothesisFoundry"`)
- No console errors

---

### UT-02 — Operator can open Epoch / Manifest and see the real committed epoch (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Epoch / Manifest

**Preconditions:**
- Backend is running with the real epoch already committed (commit `dff64eaa` present on `HEAD`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header button
3. Click the nested "Epoch / Manifest" row header button (the last of the five rows inside Hypothesis Foundry, below "Hermetic Oracles")
4. Read the banner text at the top of the expanded panel

**Expected Result:**
- The panel expands and shows a banner reading exactly "Real Epoch — not a fixture", styled with an emerald/green border and text (visually distinct from the amber banners on the other four subsections)
- A "Status:" line reads "Committed — Git-visible pre-outcome barrier crossed" in emerald text
- An identity block shows non-empty values for `epoch_id` (e.g. `epoch:afd19e9c11a6534f`), `source_registry_hash`, `manifest_hash`, `freeze_set_hash`, `freeze_commit`, and `config_fingerprint`
- A line reads `outcome_access_census: 0` in emerald text
- A heading "Source dispositions (11 of 11 required objects)" is followed by exactly 11 list rows
- A heading "Compiled families (0)" is followed by the text "Zero compiled candidates this epoch — every required source disposed non-COMPILED."
- A line near the bottom reads "Source-registry audit report: reports/hypothesis-foundry/source-registry-audit.md (committed)" with "(committed)" in emerald text

---

### UT-03 — Sources / Compiler shows both alias-family siblings and the three additive fields (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Sources / Compiler

**Preconditions:**
- Backend running as above

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header button
3. Click the nested "Sources / Compiler" row header button (the first of the five rows)
4. Scroll through the fixture list

**Expected Result:**
- The subsection shows the amber "Hermetic Fixture — not the real epoch" banner
- A line reads "Real registry audit report: reports/hypothesis-foundry/source-registry-audit.md (committed alongside the real epoch — see Epoch / Manifest below)."
- The fixture list (`data-testid="foundry-source-fixture-rows"`) contains exactly 8 rows
- Both a row labeled `fixture-variant-a` and a separate row labeled `fixture-variant-b` are present, each showing "Alternatives:" naming the other
- Every row shows three additional lines: "Operative formula refs:", "Superseded fields:", and "Aliases/lineage ids:"
- On the `fixture-unsupported-stat` row, "Operative formula refs:" reads "(none)"
- On the `fixture-alias-older` row, "Superseded fields:" reads "event_time_window → docs/rapid-validation-spec.md#feature-windows"

---

### UT-04 — Hermetic Oracles shows the kill-type mapping and best-of-N disclosure (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → Hermetic Oracles

**Preconditions:**
- Backend running as above

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header button
3. Click the nested "Hermetic Oracles" row header button (the fourth of the five rows)
4. Read the list below "Outcome types present:"

**Expected Result:**
- A list (`data-testid="foundry-kill-type-mapping-rows"`) shows exactly 7 rows, each in the form `<label> → <FOUNDRY_STATE>`
- One row reads "fragile → EVALUATED_KILLED"
- One row reads "survive → DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
- Below the list, a line reads "Best-of-N disclosure: n_variants_tried=7 · threshold_bps=<a numeric value>" (the numeric value must be present, not "—" and not blank)
- The five named-oracle rows below (All-blocked epoch completed, All-killed epoch completed, Multi-survivor preserved all, Crash-resume at scale verified, Protected-data trip fails closed / evidence class immutable) all still show "PASS"

---

### UT-05 — Epoch / Manifest empty-families state renders honestly, not as an error (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry → Epoch / Manifest

**Preconditions:**
- Epoch / Manifest subsection expanded (per UT-02)

**Steps:**
1. With Epoch / Manifest already expanded, locate the "Compiled families (0)" heading
2. Inspect the element immediately below it

**Expected Result:**
- The empty state renders as visible body text — "Zero compiled candidates this epoch — every required source disposed non-COMPILED." — not as a blank area, a loading spinner, or an error banner
- The page shows no red/rose-colored error text anywhere in the Epoch / Manifest subsection
- This is the correct behavior for a zero-compiled epoch, not a defect

---

### UT-06 — Foundry panel shows an honest unavailable state if the API call fails (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Hypothesis Foundry panel

**Preconditions:**
- Browser DevTools available (Chrome DevTools Network tab or an MCP browser tool with request-blocking)
- Do NOT stop the shared backend process — other QA lanes may depend on it; use client-side request blocking only

**Steps:**
1. Open DevTools → Network tab, and set up a request-blocking pattern for `*/research/desk/micro/foundry*` (Chrome: right-click a request or use "Block request URL"; MCP browser tools may expose an equivalent network-interception call)
2. Navigate to `http://localhost:3301/desk` (or refresh if already there)
3. Click the "Hypothesis Foundry" section header button to trigger its first expand (this issues the one deferred GET)

**Expected Result:**
- The panel shows an unavailable message (`data-testid="foundry-panel-unavailable"`) instead of a blank panel or an unhandled crash
- The message text is either the generic fallback "The Hypothesis Foundry panel could not be loaded." or a specific error string — either way, readable prose, not a raw stack trace
- Remove the network block afterward and refresh — the panel returns to normal (UT-02 behavior)

---

### UT-07 — Prior-iteration Foundry subsections (J-01, J-03, J-04) still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Hypothesis Foundry → (panel header, Interpreter Fixtures, Freeze / Integrity)

**Preconditions:**
- Backend running as above

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header button (do not expand any nested subsection yet)
3. Read the "Source registry hash:" line inside the panel header (above the five nested subsections)
4. Click the nested "Interpreter Fixtures" row header button (the second row)
5. Click the nested "Freeze / Integrity" row header button (the third row)

**Expected Result:**
- Step 3: the "Source registry hash:" line shows a long hex string (e.g. beginning `ed40dbc25e8f...`) — it must NOT read the literal text `not_yet_generated`
- Step 4: the Interpreter Fixtures subsection expands showing the amber "Hermetic Fixture — not the real epoch" banner and a non-empty list of scenario rows (`data-testid="foundry-interpreter-scenario-rows"`)
- Step 5: the Freeze / Integrity subsection expands showing the amber banner and a "Family Denominator" table with data
- No console errors appear from expanding either subsection

---

### UT-08 — Cockpit and Structure pages still load (sentinel regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit), `/structure`

**Preconditions:**
- Frontend and backend both running

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to load
3. Navigate to `http://localhost:3301/structure`
4. Wait for the page to load

**Expected Result:**
- Both pages render their normal content (chart/panels) with no blank screen and no error banner
- This confirms this iteration's Foundry-only changes did not break the rest of the app

---

### UT-09 — Epoch / Manifest is discoverable one click below Hermetic Oracles (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` → Hypothesis Foundry navigation order

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Hypothesis Foundry" section header button
3. Read the five nested row header labels top to bottom, without expanding any of them

**Expected Result:**
- The five row headers read, in this exact top-to-bottom order: "Sources / Compiler", "Interpreter Fixtures", "Freeze / Integrity", "Hermetic Oracles", "Epoch / Manifest"
- "Epoch / Manifest" is the last row, immediately below "Hermetic Oracles" — reachable in exactly 2 clicks from `/desk` (1: "Hypothesis Foundry", 2: "Epoch / Manifest")

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, Hypothesis Foundry reachable | smoke | P1 | `/desk` |
| UT-02 | Epoch / Manifest shows the real committed epoch | happy-path | P1 | `/desk` → Epoch/Manifest |
| UT-03 | Sources/Compiler shows both siblings + 3 fields | happy-path | P1 | `/desk` → Sources/Compiler |
| UT-04 | Hermetic Oracles shows kill-type mapping + best-of-N | happy-path | P1 | `/desk` → Hermetic Oracles |
| UT-05 | Empty-families state renders honestly | validation | P2 | `/desk` → Epoch/Manifest |
| UT-06 | Foundry panel degrades honestly on API failure | error | P2 | `/desk` → Hypothesis Foundry panel |
| UT-07 | J-01/J-03/J-04 subsections still render | regression | P1 | `/desk` → Hypothesis Foundry |
| UT-08 | Cockpit and Structure pages still load | regression | P1 | `/`, `/structure` |
| UT-09 | Epoch / Manifest discoverable in 2 clicks | ux | P3 | `/desk` navigation order |

**P1 tests must all pass for browser QA verdict to be PASS.**
