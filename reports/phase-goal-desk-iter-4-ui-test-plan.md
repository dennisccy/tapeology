# Phase goal-desk-iter-4 — UI Test Plan

**Phase:** goal-desk-iter-4
**Date:** 2026-07-25
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL (reference only, for preconditions):** http://localhost:8301

---

## Context

J-04 ships the era's first frontend surface: a new third page `/desk`, reached from a new "Desk"
entry in the top nav (now Cockpit · Structure · Desk). This plan covers only what a human tester can
observe and click in the browser — API/curl/pytest-style checks (reused/screen_id correctness,
no-universe 4xx body, corrupt-file integrity errors, route-count assertions, frozen-module diffs,
suite pass counts) are already covered in `reports/qa/goal-desk-iter-4-test-plan.md` and are not
repeated here.

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301 and can reach its backend.
- No login is required (this product has no auth).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- The page renders — no blank screen, no Next.js error overlay, no 404.
- A heading reading exactly "Desk" (`data-testid="desk-title"`) is visible near the top of the page.
- The top navigation bar (`data-testid="app-nav"`) is visible above the heading.
- No browser console errors appear.

---

### UT-02 — Top nav shows exactly three links everywhere, in order (smoke / regression)

**Type:** smoke
**Priority:** P1
**Surface:** `/`, `/structure`, `/desk` (top nav)

**Preconditions:**
- Frontend is running at http://localhost:3301 and can reach its backend.

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Observe the top navigation bar
3. Click "Structure" in the top navigation bar
4. Observe the top navigation bar again
5. Click "Desk" in the top navigation bar
6. Observe the top navigation bar a third time

**Expected Result:**
- At every step, the top nav shows exactly three links, always in this order: "Cockpit", "Structure", "Desk". No fourth link, no missing link, no reordering.
- After step 3, the page is at `http://localhost:3301/structure` and only the "Structure" link is visually highlighted (emerald background) — "Cockpit" and "Desk" are not highlighted.
- After step 5, the page is at `http://localhost:3301/desk` and only the "Desk" link is highlighted.
- The nav never shows the text "navigation unavailable — backend unreachable" during this sequence.

---

### UT-03 — Empty state and Run Screen starts a live compute (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- At least one universe snapshot is registered.
- No screen has ever been computed for today's date on this backend instance (a fresh/fixture-scoped backend, or one where today's screen genuinely hasn't run yet). If a screen already exists, the page will show the populated view instead of this empty view — use UT-04 onward for that state and re-run this test against a backend with zero prior screens.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish loading
3. Observe the main panel
4. Click the "Run Screen" button
5. Observe the button and the area directly beneath it immediately after clicking

**Expected Result:**
- Step 3: the panel (`data-testid="desk-screen-not-computed"`) shows the exact text **"Desk screen not computed yet."** with the line "No screen has been recorded yet for the registered universe." beneath it. An enabled "Run Screen" button (`data-testid="desk-run-screen-button"`) and an enabled "Top-up" button (`data-testid="desk-topup-button"`) are both visible — neither is greyed out.
- Step 5: the "Run Screen" button becomes disabled and its label changes from "Run Screen" to **"Computing…"**. Within a few seconds, a progress block (`data-testid="desk-screen-compute-running"`) appears containing a small pulsing dot and text reading "**N / M members**" (e.g. "3 / 101 members"), where the first number increases over time. A "Cancel" button is visible beneath the progress line.

---

### UT-04 — Provenance panel shows all five fields correctly (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- A screen has already been computed on this backend (either just completed from UT-03, or pre-existing).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to load the latest screen
3. Locate the panel titled "Provenance" (the first panel on the populated page)
4. Read each labeled row inside it, top to bottom

**Expected Result:**
- A panel titled "Provenance" is visible, containing exactly five labeled rows in this order: "Universe snapshot", "Screen date", "As of", "Config fingerprint", "Window last requested".
- Every row has a non-empty value next to its label — no row shows a blank, "undefined", or "null" value.
- The fifth row's label reads exactly **"Window last requested"** — it must NOT read "Last bar" or any other wording.

---

### UT-05 — Briefing table renders ranked rows with correct columns (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The latest screen has at least one ranked row (`rows` is non-empty).

**Steps:**
1. Navigate to `http://localhost:3301/desk` and wait for the latest screen to load
2. Locate the panel titled "Briefing" and its table
3. Read the column headers left to right
4. Read the first data row left to right

**Expected Result:**
- The table (`data-testid="desk-screen-rows-table"`) header row reads, in order: "symbol", "side", "class", "distance", "score", "coverage", "tick evidence".
- Each data row (`data-testid="desk-screen-row"`) shows: the symbol (e.g. "AAPL"); the side, either "support" or "resistance"; a class cell showing either "Class A" / "Class B" / "Class C" with the smaller caption text **"nearest same-class band"** directly beneath it, OR the word "Unclassified" if the row has no band class; a distance value ending in **" bps"** (e.g. "42 bps"); a plain numeric score; one or more coverage badges (verified in UT-06); and, only on rows where it applies, a small badge reading "tick evidence".
- Rows appear in the same top-to-bottom order every time the page is reloaded (no client-side re-sorting by score or alphabetically).

---

### UT-06 — Coverage badges render honestly per row (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The latest screen contains at least one row for a symbol with partial timeframe coverage (some timeframes have bars, some don't — e.g. MSFT with `1h`/`1d` present but `4h`/`1w` absent, per this project's own documented iter-2 example). If every row happens to have full coverage this run, pick any row and confirm its badge count matches its own data instead.

**Steps:**
1. Navigate to `http://localhost:3301/desk` and wait for the latest screen to load
2. In the Briefing table, find a row whose coverage cell shows badges in two different shades/colors (or, failing that, any row)
3. Count the badges in that row's coverage cell
4. Hover over one emerald-colored badge and one muted slate-colored badge (if both are present)

**Expected Result:**
- The row shows exactly one badge (`data-testid="desk-coverage-badge"`) per timeframe key present in that row's own data — never a fixed set of four badges assumed for every symbol regardless of its actual coverage.
- Badges for timeframes WITH bars are emerald-tinted (`data-has-bars="true"`); badges for timeframes WITHOUT bars are muted slate (`data-has-bars="false"`).
- Hovering an emerald badge shows a tooltip reading "window last requested: `<a timestamp>`"; hovering a slate badge shows "window last requested: never".

---

### UT-07 — Skipped Members section groups honestly by reason (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The latest screen has at least one skipped member. Ideally the fixture/data includes both skip reasons (`no_bars` and `no_basis`) so both branches below can be checked; if only one reason is present, check that branch and treat the other as "correctly absent."

**Steps:**
1. Navigate to `http://localhost:3301/desk` and wait for the latest screen to load
2. Scroll to the panel titled "Skipped Members"
3. Read any heading(s) present and the count in parentheses
4. Check whether a heading is shown for a reason that has zero members that run

**Expected Result:**
- If any members were skipped for lacking bars, a heading reads exactly **"Skipped — no bars (N)"** (N matches the number of rows listed under it), each such row's reason cell reading "no bars".
- If any members were skipped for lacking a basis session, a heading reads exactly **"Skipped — no basis session (N)"** the same way, each row's reason cell reading "no basis".
- A heading for a reason with zero members is completely absent from the page — it is never shown as "(0)".
- If the screen skipped zero members total, the panel instead shows the text "No members were skipped in this screen." and no heading/table appears.

---

### UT-08 — Screen History is a read-only list (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- At least one past screen exists in the backend's history (if none exist, the panel shows "No screens recorded yet." instead — note that as the observed state and skip steps 3-5).

**Steps:**
1. Navigate to `http://localhost:3301/desk` and wait for the page to load
2. Scroll to the panel titled "Screen History"
3. Read one row's date, rows count, skipped count, and provenance text
4. Open the browser DevTools Network tab and clear it
5. Click directly on a history row and wait 2 seconds

**Expected Result:**
- Each row shows a date, a numeric rows count, a numeric skipped count, and a provenance string shaped like "`<universe snapshot id>` · `<config fingerprint>` · `<bar-store signature>`" (an em-dash "—" appears in place of the snapshot id only if none was recorded).
- Clicking a row does not navigate away from `/desk`, does not open a modal or expand any detail, and the page's visible content does not change.
- No new network request appears in the Network tab as a result of the click in step 5.

---

### UT-09 — Top-up starts a live compute with pairs progress (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- `/desk` is reachable in any state (empty or populated — the "Top-up" control is present in both).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Top-up" button
3. Click "Top-up"
4. Observe the area beneath the button over the next several seconds

**Expected Result:**
- Immediately after clicking, the button becomes disabled and its label changes from "Top-up" to **"Topping up…"**.
- A progress block (`data-testid="desk-topup-compute-running"`) appears with a pulsing dot and text reading "**N / M pairs**" (e.g. "0 / 200 pairs"), where the first number increases over time.
- Once at least one symbol/timeframe pair has resolved, a line appears reading "**last: SYMBOL TIMEFRAME — OUTCOME**" (e.g. "last: AAPL 1h — reused").
- A "Cancel" button is visible alongside the progress line.

---

### UT-10 — Run Screen is single-flight: a second click cannot start a second job (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A screen compute is currently running (button reads "Computing…", progress block visible).

**Steps:**
1. With the compute running, click directly on the "Run Screen" button again
2. Observe whether anything changes
3. Open a second browser tab and navigate to `http://localhost:3301/desk` while the first tab's compute is still running
4. Observe the second tab's Run Screen button and progress numbers

**Expected Result:**
- In the first tab, the button remains disabled throughout — the click in step 1 has no visible effect (no progress reset, no second "Computing…" cycle, no error).
- In the second tab, on load the "Run Screen" button also shows disabled with "Computing…" and the SAME progress numbers as the first tab (both converge on one shared job) — it never shows an independent fresh "0 / N" run.

---

### UT-11 — Top-up is single-flight: a second click cannot start a second job (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A top-up compute is currently running (button reads "Topping up…", progress block visible).

**Steps:**
1. With the compute running, click directly on the "Top-up" button again
2. Observe whether anything changes

**Expected Result:**
- The button remains disabled throughout — the second click has no visible effect. The `pairs_done`/`pairs_total` numbers continue counting up from wherever the one running job is; they never reset to "0 / N" as if a new job started.

---

### UT-12 — Cancelling a running Run Screen compute (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A screen compute is running.

**Steps:**
1. While "Run Screen" shows "Computing…" with a visible progress line, click the "Cancel" button beneath it
2. Observe the Cancel button immediately after clicking
3. Wait for the job to resolve (the currently-processing member finishes)
4. Note the row count in the "Screen History" panel

**Expected Result:**
- Immediately after clicking, the Cancel button becomes disabled and relabels to **"Cancelling — finishing the current member…"**.
- Once resolved, the text **"Screen compute cancelled — nothing was recorded this run."** appears, the progress block disappears, and the "Run Screen" button returns to its normal enabled "Run Screen" label (not stuck on "Computing…").
- The Screen History panel's row count is unchanged from before the cancelled run — no new entry was added for the cancelled attempt.

---

### UT-13 — Cancelling a running Top-up compute (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A top-up compute is running.

**Steps:**
1. While "Top-up" shows "Topping up…" with a visible progress line, click the "Cancel" button beneath it
2. Observe the Cancel button immediately after clicking
3. Wait for the job to resolve (the currently-processing pair finishes)

**Expected Result:**
- Immediately after clicking, the Cancel button becomes disabled and relabels to **"Cancelling — finishing the current pair…"**.
- Once resolved, the text **"Top-up cancelled — pairs already recorded before the cancel stay stored."** appears, the progress block disappears, and the "Top-up" button returns to its normal enabled "Top-up" label.

---

### UT-14 — Run Screen with no universe registered shows an inline error (error)

**Type:** error
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The backend has ZERO universe snapshots registered (a genuinely fresh data directory — distinct from UT-03's "no screen yet but a universe exists" state).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the page shows the "Desk screen not computed yet." empty state
3. Click the "Run Screen" button
4. Observe the area directly beneath the button
5. Reload the page

**Expected Result:**
- The button does not enter a lasting "Computing…" state — no progress block with a member counter ever appears.
- An inline error paragraph in a red/warning tone appears beneath the button, containing the words "no universe snapshot is registered" and naming the missing universe as the cause.
- The "Run Screen" button is enabled again immediately (not stuck disabled).
- After reloading in step 5, the page still shows "Desk screen not computed yet." — confirming no snapshot was created or persisted by the failed attempt.

---

### UT-15 — Backend unreachable mid-poll keeps the last known progress (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A screen or top-up compute is running with its progress line visibly updating.
- Tester has a way to stop or block the backend process temporarily.

**Steps:**
1. With a compute running and progress visible (e.g. "12 / 101 members"), stop the backend process (or otherwise make it unreachable)
2. Wait at least 2 seconds (one poll interval)
3. Observe the progress line
4. Restore the backend process

**Expected Result:**
- The progress line does not clear, blank out, crash the page, or jump to a fabricated value — it continues showing the last known numbers it had (still "12 / 101 members" or whatever was last observed).
- No error page or broken layout appears; the rest of the page stays intact.
- After the backend is restored, polling resumes and the numbers begin updating again from where they left off.

---

### UT-16 — Cockpit (`/`) is unaffected by this phase (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- None beyond a running frontend/backend.

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Observe the page

**Expected Result:**
- The Cockpit page loads and renders exactly as before this phase — this phase's diff touched no Cockpit code.
- The top nav shows "Cockpit" highlighted as the active link.
- No Desk-specific content (briefing table, Run Screen button, etc.) appears on this page — Desk is reached only via the nav link.

---

### UT-17 — `/structure` Load workflow still works for the pinned AAPL example (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- The backend has bar/tradability data recorded for symbol AAPL as-of `2026-06-22T21:00:00Z` (the pinned regression fixture this project has used since era 5B; the `tradability_cache` warm-up this phase's backend scope performs before browser QA ensures this).

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type "AAPL" into the "Symbol" field
3. Type "2026-06-22T21:00:00Z" into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button
5. Locate the "Tradable Map" panel and its band table

**Expected Result:**
- The page loads without error and renders the Tradable Map for AAPL.
- At least one band row appears whose range cell reads **"300.11–302.2"** (en dash, no spaces) with side "resistance" and class cell reading "Class A" — the same pinned wall this project has verified every regression pass since era 5B.
- The top nav still shows all three links ("Cockpit", "Structure", "Desk") with "Structure" highlighted active — confirming the new nav entry did not break this existing page.

---

### UT-18 — An all-skipped screen never shows the "not computed" panel (regression / edge case)

**Type:** regression
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- A screen snapshot exists where `rows` is empty but `skipped` is non-empty (every registered member was skipped that run). This is a specific data state; if the current environment has no such snapshot, this test cannot run this pass — note it as not-executable rather than skipping silently.

**Steps:**
1. Load `/desk` so that this all-skipped snapshot is the latest screen
2. Observe the "Briefing" panel
3. Observe the "Skipped Members" panel
4. Confirm which top-level panel is showing

**Expected Result:**
- The "Briefing" panel shows the text "No members ranked in this screen." instead of a table.
- The "Skipped Members" panel below it shows the full grouped skip list (non-empty, per UT-07's grouping rules).
- The "Desk screen not computed yet." panel is NOT shown anywhere on the page — this all-skipped state is visually distinct from "no screen has ever run."

---

### UT-19 — Page load issues GETs only; zero POST fires before a button click (regression / safeguard)

**Type:** regression
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- Tester has basic familiarity with browser DevTools' Network tab.

**Steps:**
1. Open the browser DevTools Network tab and clear its log
2. Navigate to `http://localhost:3301/desk`
3. Wait 2 seconds for the page to settle
4. Filter the Network tab for requests containing "desk"

**Expected Result:**
- Exactly three GET requests are visible, to `/research/desk/screen`, `/research/desk/screen/compute`, and `/research/desk/topup/compute`.
- Zero POST requests appear anywhere in the log at this point.
- Only after explicitly clicking "Run Screen" or "Top-up" does a POST request to the corresponding `/compute` endpoint appear.

---

### UT-20 — "Desk" is discoverable within one click from the home page (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation / `/`

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/` (Cockpit, the app's default landing page)
2. Look at the top navigation bar without scrolling or opening any menu
3. Click the third link in the nav

**Expected Result:**
- A clearly labeled link reading "Desk" is visible in the top nav with no scrolling and no menu expansion required, positioned third, after "Cockpit" and "Structure".
- Clicking it lands on `http://localhost:3301/desk` in exactly one click.
- The destination page's own heading confirms arrival: a heading reading "Desk" is visible at the top of the new page — a first-time user can identify and reach this feature from the home page in a single, unambiguous click.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Top nav shows exactly three links everywhere | smoke | P1 | nav (all pages) |
| UT-03 | Empty state and Run Screen starts a live compute | happy-path | P1 | `/desk` |
| UT-04 | Provenance panel shows all five fields | happy-path | P1 | `/desk` |
| UT-05 | Briefing table renders ranked rows correctly | happy-path | P1 | `/desk` |
| UT-06 | Coverage badges render honestly per row | happy-path | P1 | `/desk` |
| UT-07 | Skipped Members groups honestly by reason | happy-path | P1 | `/desk` |
| UT-08 | Screen History is a read-only list | happy-path | P2 | `/desk` |
| UT-09 | Top-up starts a live compute with pairs progress | happy-path | P1 | `/desk` |
| UT-10 | Run Screen single-flight guard | validation | P2 | `/desk` |
| UT-11 | Top-up single-flight guard | validation | P2 | `/desk` |
| UT-12 | Cancelling a running Run Screen compute | happy-path | P2 | `/desk` |
| UT-13 | Cancelling a running Top-up compute | happy-path | P2 | `/desk` |
| UT-14 | Run Screen with no universe shows inline error | error | P1 | `/desk` |
| UT-15 | Backend unreachable mid-poll keeps last known state | error | P2 | `/desk` |
| UT-16 | Cockpit unaffected by this phase | regression | P2 | `/` |
| UT-17 | `/structure` Load still renders the pinned AAPL wall | regression | P1 | `/structure` |
| UT-18 | All-skipped screen never shows "not computed" | regression | P2 | `/desk` |
| UT-19 | Page load issues GETs only, zero POST before click | regression | P2 | `/desk` |
| UT-20 | "Desk" discoverable within one click from home | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-09, UT-14, UT-17.
