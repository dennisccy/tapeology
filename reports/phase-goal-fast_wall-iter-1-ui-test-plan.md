# Phase goal-fast_wall-iter-1 — UI Test Plan

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (the shared pipeline backend — the DEFAULT real-corpus
instance, `.data/datasets`, 882MB, 18 registered datasets, no `TAPEOLOGY_DATASET_DIR` override)

---

## Scope

This iteration (J-01) ships exactly one new frontend state inside the existing `/structure` →
**Edge Report** panel — the `NotComputedPanel` — plus the backend rewire that makes it reachable
without ever running the multi-hour sweep. No new page, no new nav entry, no new button, no form.
Test cases below cover: the new state rendering correctly (UT-01/UT-02), the pre-existing frozen
warm-empty state still rendering byte-identically through the rewired route (UT-03), an honest
degraded-network state (UT-04), discoverability (UT-05), and two regression checks — one scoped to
`/structure`'s untouched neighboring sections (UT-06) and one cross-page spot-check of the
required-still-passing J-07 sentinel (UT-07). This plan does **not** duplicate the API-level
contract checks (`status`/`detail`/`dataset_count`/`register`/`compute` field shapes, the
compute-spy zero-call proof, byte-identity, 405s, cache-layer unit tests) already covered as TC-01
through TC-10 and TC-13–TC-15 in `reports/qa/goal-fast_wall-iter-1-test-plan.md` — those are
backend/API concerns; this plan only covers what an operator observes in a browser.

**Live state confirmed at the time this plan was written** (2026-07-17, via a direct read-only
`GET http://localhost:8301/research/edge-report` — safe to run repeatedly now that J-01 is built,
since a GET never computes): the response was

```json
{"status":"not_computed","detail":"The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute.","dataset_count":18,"register":"simulated — assumed fees/slippage — not indicative of live results","compute":null}
```

returned in **29.08 seconds** (bounded by the still-unaccelerated `dataset_store.list()` cost —
J-02's future scope — never by the sweep; `/health` itself answers instantly). This means the
default backend's cache is **currently cold**, which is exactly the state UT-02 needs. Cache state
is time-varying (anyone running a compute against this backend changes it) — UT-02 includes an
explicit fallback if it has since gone warm.

**Known trap, do not repeat:** the prior QA pass against this same phase
(`reports/qa/goal-fast_wall-iter-1-qa.md`) recorded TC-11/TC-12 as **SKIP** because the browser
session timed out. Root cause is almost certainly scrolling/waiting behavior around the ~30-second
Edge Report resolve time, or accidentally waiting on the separate, unrelated `GET /research/setups`
Case Studies cold-scan (measured 268.95s at iter-0 baseline — **not** fixed by this iteration, see
`docs/phases/goal-fast_wall-iter-1.md` NOTES). Every step below that waits on the Edge Report panel
gives an explicit time budget; no step in this plan requires waiting for the Case Studies section
to finish loading — skip past it while scrolling.

<!-- Test IDs use UT-XX prefix to distinguish from the functional test plan's TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no vague "test the form" steps. -->

---

## Test Cases

### UT-01 — `/structure` loads with the Edge Report panel visible in its initial state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301` (or any
  reachable Tapeology backend).
- No login exists anywhere in this app.
- Fresh navigation (new tab or hard reload) so the page's mount-time fetches fire from a clean
  state.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Wait for the page's initial render to finish (1–2 seconds).
3. Confirm the heading "Structure" is visible near the top of the page.
4. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
5. Observe the Edge Report panel for the first 5 seconds only — do **not** wait for it to fully
   resolve here; that is UT-02's job.

**Expected Result:**
- The `<h1>` heading (`data-testid="structure-title"`) reads exactly "Structure".
- Below it, a byline beginning "Load a symbol and an as-of time to see its tradable level map…" is
  visible.
- The "Edge Report" panel (`<h2>` inside `<section aria-label="Edge report">`) is present, with
  caption text beginning "The v1 / structure_tape / structure_tape_map comparison over recorded
  event windows…".
- Within the first few seconds, a pulsing gray loading placeholder
  (`data-testid="edge-report-loading"`) is visible directly under that caption — confirms the
  `GET /research/edge-report` fetch started automatically on page mount, exactly as it did before
  this iteration (no button click starts it).
- No red/white crash screen and no "Application error" text appears anywhere on the page.
- Opening the browser DevTools Console shows zero red errors at this point.

---

### UT-02 — Cold cache resolves to the honest "not computed" panel within a bounded time (happy-path — THE headline test)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Same as UT-01.
- The default backend's edge-report cache is cold with a non-empty dataset registry — confirmed
  live at plan-authoring time (see Scope above). **If the cache has since become warm** (the panel
  instead shows "No edge-report cells yet." within a few seconds), this specific test cannot be
  observed against this backend right now — do not mark it FAIL; instead run UT-03's environment
  setup against a deliberately cold, freshly-provisioned scoped fixture and repeat these steps
  there.

**Steps:**
1. Navigate to `http://localhost:3301/structure` (a fresh navigation or hard reload, so the fetch
   fires from a clean page mount).
2. Scroll to the "Edge Report" panel.
3. Start a timer the moment step 1's navigation begins.
4. Watching only the Edge Report panel, wait for the pulsing gray loading placeholder to be
   replaced by real content. Expect roughly 30 seconds; allow up to 2 minutes before treating this
   as a failure.
5. Read the panel's contents once resolved.

**Expected Result:**
- The panel resolves to an amber-bordered box (`data-testid="edge-report-not-computed"`) with the
  exact headline text **"Edge report not computed yet."**
- Directly beneath the headline, a non-empty sentence of detail text is visible (server-provided,
  e.g. at plan-authoring time: "The 3-way strategy-comparison sweep has not been run for the
  current dataset registry and configuration. It never runs automatically on a GET -- an operator
  must trigger the compute.") — must be non-empty and must never be a raw error code, stack trace,
  or the literal words "undefined"/"null".
- Resolution happens within roughly 30 seconds and **never exceeds 2 minutes**. If it takes longer
  than 2 minutes, or the browser tab appears to hang/freeze, treat this as a **FAIL** — it would
  indicate the pre-iteration always-compute bug has regressed.
- The text "No edge-report cells yet." is **NOT** visible anywhere in the panel at the same time
  (i.e. `data-testid="edge-report-empty"` is absent).
- No button, input field, or other clickable control appears inside the amber box — this iteration
  ships no trigger control (that is a future iteration's scope).
- *(Optional supplementary evidence, not required for pass/fail):* if you have terminal access to
  the backend host, `top`/`ps` shows backend CPU usage returns to near-idle within a few seconds
  after the response arrives — it does not stay pinned near 100%.

---

### UT-03 — Warm cache renders the frozen "No edge-report cells yet." state byte-identically (regression — the other half of J-01's DoD)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- This test requires a **scoped** backend instance with a pre-warmed edge-report cache — do not
  attempt it against the shared pipeline backend at `http://localhost:8301` while its cache is
  cold (per UT-02, waiting for someone else to warm the shared instance is not a reliable
  precondition).
- Provisioning recipe (the same one the developer used and verified for this exact iteration —
  see `docs/handoffs/goal-fast_wall-iter-1-dev.md`'s "Live verification" section, and the
  identical pattern documented across this codebase's `tradable_wall` iterations, e.g.
  `docs/handoffs/goal-tradable_wall-iter-10-dev.md`):
  a. Start a second backend instance on a free port (e.g. `8391`) with environment variable
     `TAPEOLOGY_DATASET_DIR` pointed at the committed fixture directory
     `apps/backend/tests/fixtures/datasets_j03` (exactly 1 registered dataset, keyless, no
     credentials needed).
  b. Pre-warm its edge-report cache once by calling
     `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn)` for that store/config
     (directly in Python, or via the pattern already exercised in
     `apps/backend/tests/test_edge_report_api.py`'s warm-cache tests). This fixture is known from
     prior iterations (`tradable_wall` iter-9/iter-10) to resolve to an **all-empty** report
     (`train.cells: []` and `holdout.cells: []`).
  c. Start a second frontend instance on a free port (e.g. `3391`) pointed at that backend.
- Frontend running at that scoped instance (e.g. `http://localhost:3391`).

**Steps:**
1. Navigate to the scoped frontend's structure page (e.g. `http://localhost:3391/structure`).
2. Scroll to the "Edge Report" panel.
3. Wait for the panel to resolve — expect well under a minute against this small fixture (likely a
   few seconds).
4. Read the panel's contents.
5. Reload the page once more (F5).

**Expected Result:**
- The panel shows the title **"No edge-report cells yet."**
  (`data-testid="edge-report-empty"`) — the frozen text carried over byte-identically from before
  this iteration.
- Directly below the title, the detail text reads exactly: "No recorded dataset has resolved an
  owning, classified scan event — an honest, valid outcome, never hidden."
- Above it, a separate amber register banner (`data-testid="edge-report-register"`) is visible
  reading exactly: `simulated — assumed fees/slippage — not indicative of live results`.
- The headline "Edge report not computed yet." is **NOT** visible anywhere in the panel at the same
  time (i.e. `data-testid="edge-report-not-computed"` is absent).
- After step 5's reload, the same "No edge-report cells yet." state renders again, just as quickly
  — confirms the durable cache survived the reload rather than a one-off fluke.

---

### UT-04 — Backend unreachable shows the honest degraded panel, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301` pointed at a reachable backend.
- Browser DevTools available. This test uses the browser's own built-in "Offline" network
  simulation — it does **not** require stopping or touching the actual backend process, so it is
  safe to run against the shared pipeline backend without disrupting anything else connected to
  it.

**Steps:**
1. Navigate to `http://localhost:3301/structure` and let the page fully render its initial shell
   (heading + nav visible).
2. Open DevTools → Network panel → set the throttling/connection profile to "Offline".
3. Reload the page (F5) while offline is still active.
4. Wait a few seconds, then scroll to the "Edge Report" panel.
5. Turn the Network throttling profile back to "Online" / "No throttling" (cleanup step).
6. Reload the page one more time while back online.

**Expected Result:**
- The Edge Report panel shows an amber-bordered box
  (`data-testid="edge-report-unavailable"`) with the message **"Backend unreachable — is the API
  running?"** — distinct from UT-02's "Edge report not computed yet." panel; this is the genuine
  network-failure state, not the honest cold-cache state.
- A second, fixed line of reassurance text is visible below it: "Nothing cached and nothing
  fabricated is shown in its place."
- No populated table, no stale cached content, and no raw browser network-error interstitial (e.g.
  "This site can't be reached") appears in the Edge Report panel's place.
- The rest of the page (heading, other panel titles) still renders — the whole page does not go
  blank.
- After step 6, the page resolves normally again (confirms this was a transient simulation, not a
  persisted broken state).

---

### UT-05 — Feature is discoverable and stated in plain language (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`, top navigation

**Preconditions:**
- Frontend running at `http://localhost:3301`.

**Steps:**
1. Navigate to `http://localhost:3301/` (the Cockpit / home page).
2. Look at the top navigation bar.
3. Click "Structure".
4. Once on `/structure`, scroll to the "Edge Report" panel and read its caption and (whichever
   state it currently shows) its headline/detail text as if seeing this feature for the first
   time.

**Expected Result:**
- "Structure" is visible as one of the top navigation items (alongside "Cockpit", "Journal",
  "Studies", "Performance") — reachable in exactly 1 click from the home page.
- Clicking it navigates to `http://localhost:3301/structure`.
- A reader unfamiliar with this update can understand, from the panel text alone, that the report
  simply has not been generated yet and roughly why — no jargon like "cache miss", "sweep
  invocation", or internal function/class names in the user-facing headline; "Edge report not
  computed yet." and its detail sentence read as plain English.
- Nothing about the panel implies the user should click something to fix it — correct for this
  iteration (there genuinely is no control yet); the wording does not send the reader hunting for a
  nonexistent button.

---

### UT-06 — Neighboring `/structure` sections are unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Without filling in any fields, confirm the "Tradable Map" panel (above the Edge Report panel)
   shows its idle message.
3. Confirm the "Case Studies" panel (between Tradable Map and Edge Report) is present with a
   "Symbol" text field and a "Reaction" dropdown, regardless of how long its own data table below
   them takes to resolve.
4. Scroll further down past the Edge Report panel to confirm the "Fetch from Yahoo Finance" panel
   is still present in its usual place.

**Expected Result:**
- The "Tradable Map" panel (`data-testid="tradable-map-idle"`) shows the idle-state message
  "Choose a symbol and an as-of time, then Load, to see its tradable level map." — unchanged from
  before this iteration.
- The "Case Studies" panel's Symbol/Reaction filter controls render immediately — these do not
  depend on this iteration's change, even if the underlying table below them is still loading.
- The "Fetch from Yahoo Finance" panel title is present below the Edge Report section.
- No section is missing, duplicated, or reordered relative to before this iteration; no console
  errors appear.

---

### UT-07 — Cross-page regression sentinel: Cockpit SIM watch still works (regression — J-07 required-still-passing)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- No watch currently active (fresh page load).

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Type `SIM-BUYER` into the field labeled "Ticker" (placeholder "Ticker e.g. SIM-BUYER").
3. Click the "Watch" button.
4. Wait a few seconds for the "Price Chart — Tape-State Markers" panel to render.
5. Click the "Stop" button (`aria-label="Stop watching"`).

**Expected Result:**
- The Tape State panel reads **"Buyer Control"**.
- The event log records an entry noting the transition to `buyer_control` (matching the exact text
  previously observed this same session in `reports/phase-goal-fast_wall-iter-0-ui-test-results.md`:
  "Tape state changed to buyer_control").
- No console errors, no crash — this journey lives entirely outside any file this iteration
  touched (`edge_report*.py`, `routes.py`'s edge-report route, `structure/page.tsx`), confirming
  this iteration's changes did not regress the already-shipped cockpit.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/structure` loads, Edge Report panel visible in initial state | smoke | P1 | `/structure` |
| UT-02 | Cold cache resolves to "not computed" panel within bounded time (headline) | happy-path | P1 | `/structure` |
| UT-03 | Warm cache renders frozen "No edge-report cells yet." byte-identically | regression | P1 | `/structure` |
| UT-04 | Backend unreachable shows honest degraded panel, not a crash | error | P2 | `/structure` |
| UT-05 | Feature discoverable in 1 click, plain-language copy | ux | P3 | `/structure`, nav |
| UT-06 | Neighboring `/structure` sections unaffected | regression | P2 | `/structure` |
| UT-07 | Cockpit SIM watch cross-page sentinel unregressed | regression | P1 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02 carries an explicit fallback
(see its own Preconditions): if the shared backend's cache has gone warm since this plan was
authored, that is not a FAIL — provision UT-03's scoped fixture cold instead and repeat UT-02's
steps there. UT-03 must be run against a scoped fixture, never against the shared pipeline backend
while its cache is cold, per the codebase's own documented lesson (see Scope above).

Save any captured screenshots to
`reports/qa/goal-fast_wall-iter-1-evidence/UT-<ID>-<short-description>.png`, alongside the existing
TC-11/TC-12 evidence already in that directory from the prior QA pass.
