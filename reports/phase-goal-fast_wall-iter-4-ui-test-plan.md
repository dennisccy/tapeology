# Phase goal-fast_wall-iter-4 — UI Test Plan

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 (standard instance) — **but see the warning below: nearly
every test in this plan must instead target the SCOPED instance at http://localhost:3391.**

---

## ⚠️ Required test environment — read this before running any test below

This phase adds the first real, browser-triggerable compute job on `/structure`. The phase spec
(`docs/phases/goal-fast_wall-iter-4.md`, BACKGROUND + TESTING REQUIREMENTS) is explicit and
critical on this point: **any test that clicks "Compute edge report" must run against a SCOPED
backend/frontend pair — never against the standard `http://localhost:3301` / `http://localhost:8301`
instance.** The standard instance reads the project's real corpus (`.data/datasets`, 882MB, 18
registered datasets); clicking the button there starts a genuine sweep over the full corpus — the
exact CPU-pin hazard this "Fast Wall" interlude exists to remove from casual verification passes.

Only **UT-10** (a pure scroll-through of sections other than Edge Report, never clicks compute) is
safe to run against either instance.

### One-time setup (before UT-01 through UT-09, UT-11, UT-12)

Run in two separate terminals from the repo root (`/home/dennis-chan/Git/tapeology`):

**Terminal 1 — scoped backend, port 8391:**
```bash
SCOPED_DIR=$(mktemp -d)
mkdir -p "$SCOPED_DIR/bars"
cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"
cd apps/backend
source .venv/bin/activate
TAPEOLOGY_DATASET_DIR="$SCOPED_DIR/datasets" \
TAPEOLOGY_BAR_DIR="$SCOPED_DIR/bars" \
TAPEOLOGY_JOURNAL_DB="$SCOPED_DIR/journal.db" \
TAPEOLOGY_EDGE_REPORT_CACHE_DB="$SCOPED_DIR/edge_report_cache.db" \
uvicorn main:app --host 0.0.0.0 --port 8391
```

**Terminal 2 — scoped frontend, port 3391:**
```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8391 npx next dev -p 3391
```

**Verify both are up** before testing: `curl http://localhost:8391/research/edge-report` must
return JSON containing `"status": "not_computed"` and `"dataset_count": 1` — this cold state is the
starting point every test below assumes. Then open `http://localhost:3391/structure`.

Every "Frontend URL" / navigation target below means **`http://localhost:3391`** unless a test says
otherwise. Tear down both processes (Ctrl+C in each terminal) when testing is complete; confirm no
stray `uvicorn`/`next dev` process for this project remains.

**Why `datasets_j03`:** it is the same fixture the developer's own live verification used. Its one
dataset (symbol PG) is not a config-owned panel symbol, so a triggered compute honestly resolves
zero eligible backtest pairs and finishes in well under a second. This is a valid, honest outcome
the phase spec's own TC-15 explicitly accepts ("the honest all-empty-cells state") — every test
below treats a near-instant empty result as a PASS, not a failure. Where a test needs to observe an
actual failure, a short sub-recipe (below) corrupts the fixture on purpose.

### Sub-recipe: arranging a "failed" compute (used by UT-05, UT-08, UT-11)

1. Stop the scoped backend (Ctrl+C in Terminal 1) if it is running.
2. Corrupt the scoped copy's dataset file so its content no longer matches its registered checksum:
   `echo "corrupted" >> "$SCOPED_DIR/datasets/"*.json`
3. Restart the scoped backend with the exact same command and env vars as the one-time setup above.
4. This backend instance will now fail any compute it is asked to run, until restored (step below).

**To restore** (needed before UT-11's "retry succeeds" step): `rm -rf "$SCOPED_DIR/datasets" && cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"`, then restart the backend again.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/structure` loads with the not-computed panel and idle button (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Scoped backend/frontend pair running per the setup above, freshly started (cold edge-report cache,
  no compute ever triggered against this backend instance)

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Wait for the page to finish loading (the `edge-report-loading` placeholder, if briefly visible,
   disappears)
3. Scroll down past the "Tradable Map" and "Case Studies" panels to the "Edge Report" panel

**Expected Result:**
- The panel heading "Edge Report" is visible
- Beneath it, a panel with `data-testid="edge-report-not-computed"` is visible, showing:
  - The amber text "Edge report not computed yet."
  - The detail line: "The 3-way strategy-comparison sweep has not been run for the current dataset
    registry and configuration. It never runs automatically on a GET -- an operator must trigger
    the compute."
  - A button reading exactly "Compute edge report" (`data-testid="edge-report-compute-button"`),
    enabled (not greyed out, no `disabled` attribute)
- No progress line, no red error line, and no report table are visible yet
- No console errors

---

### UT-02 — Full compute lifecycle: click → running → finished report (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold cache).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. In the Edge Report section, click the "Compute edge report" button
   (`data-testid="edge-report-compute-button"`)
3. Immediately look at the button and the area directly beneath it
4. Without reloading the page, wait up to 90 seconds, watching the panel
5. Once the panel changes, inspect its content

**Expected Result:**
- Step 3: the button's label changes to "Computing…" and it becomes disabled; a progress line
  appears beneath it (`data-testid="edge-report-compute-progress"`) reading a pattern like
  "0 / 0 backtests" — OR the panel has already moved past this point by the time you look (expected
  on this fixture, see note below)
- Within 90 seconds, EITHER:
  (a) the not-computed panel disappears and is replaced by a report view: an amber register line
  (`data-testid="edge-report-register"`) followed by Train and Hold-out cell tables
  (`data-testid="edge-report-train-table"` / `edge-report-holdout-table"`), OR
  (b) the panel is replaced by the honest empty state reading "No edge-report cells yet."
  (`data-testid="edge-report-empty"`) with detail "No recorded dataset has resolved an owning,
  classified scan event — an honest, valid outcome, never hidden."
- Throughout, the browser stays at `http://localhost:3391/structure` with no full-page reload (no
  white flash, no from-scratch loading spinner replacing the whole page)
- **Note:** on the recommended `datasets_j03` fixture, outcome (b) typically appears in well under a
  second — this is the expected, correct result, not a failure.

---

### UT-03 — Button blocks a second trigger while a job is running (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold cache).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Click "Compute edge report"
3. Immediately attempt to click the SAME button again (as fast as possible), before the panel
   visibly changes

**Expected Result:**
- After the first click, the button carries the `disabled` attribute and reads "Computing…" — the
  attempted second click has no effect (no visible change, no second progress line, no console
  network request fired from that second click)
- The button does not toggle back to enabled between the first and second click
- The button only becomes clickable again once the job reaches a terminal state: replaced by the
  report/empty state, or re-enabled reading "Retry compute" on failure

---

### UT-04 — Progress line renders the correct live-count format (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold cache).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Click "Compute edge report"
3. While the button still reads "Computing…", read the exact text of the progress line
   (`data-testid="edge-report-compute-progress"`)

**Expected Result:**
- The progress line's text matches the pattern `{integer} / {integer} backtests` (e.g.,
  "0 / 0 backtests") — never negative numbers, never missing numbers
- No "(N from cache)" suffix is present — this is EXPECTED this iteration: the from-cache annotation
  only appears once `backtests_from_cache > 0`, which never happens yet (no per-pair sub-cache
  exists until a future iteration)
- If the line is readable across more than one instant (only likely with a larger dataset registry),
  the counts never decrease

---

### UT-05 — Failed compute shows the exact backend error and offers retry (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Scoped backend/frontend pair running with the "arranging a failed compute" sub-recipe already
  applied (corrupted dataset file, backend restarted) — see the setup section above
- No compute has been triggered against this corrupted backend yet

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Click "Compute edge report"
3. Wait up to 15 seconds without reloading
4. Inspect the panel

**Expected Result:**
- The not-computed panel remains, now showing a red line
  (`data-testid="edge-report-compute-error"`) whose text starts with a number followed by "dataset
  file(s) failed integrity verification" and ends with "the report stops with nothing written" — the
  backend's own exact `EdgeReportError` message, not a paraphrase or generic message
- The button's label changes to "Retry compute" and is enabled again (does NOT stay stuck on
  "Computing…")
- No progress line is visible (the job is no longer running)
- No report table renders anywhere on the page

---

### UT-06 — Unreachable backend at click time shows a distinct trigger-error line (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- The scoped frontend (port 3391) is running and `/structure` has already loaded successfully once
- The scoped backend (port 8391) is then STOPPED (Ctrl+C in Terminal 1) immediately before this
  test's click, without reloading the frontend page

**Steps:**
1. With `/structure` already loaded and the backend now stopped, click "Compute edge report"
2. Wait a few seconds
3. Inspect the panel

**Expected Result:**
- A red line reading exactly "Backend unreachable — is the API running?" appears
  (`data-testid="edge-report-compute-trigger-error"`) — visually distinct from, and shown in addition
  to, the existing headline/detail text
- The button returns to its enabled idle state reading "Compute edge report" — it does NOT stay
  stuck disabled on "Computing…"
- No progress line appears (no job was ever actually started on the server)
- Restart the scoped backend afterward before running any later test.

---

### UT-07 — Reloading mid-job resumes the real state, never resets to idle (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold cache).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Click "Compute edge report"
3. Immediately (within about 1 second) reload the page (F5 / Cmd+R) — do not wait
4. Observe the panel on the reloaded page, without clicking anything

**Expected Result:**
- The reloaded page does NOT show the plain idle "Compute edge report" button as if nothing had
  happened
- Instead it shows one of: the "Computing…" disabled button with an active progress line (job still
  running at reload time), the finished report / honest empty state (job already completed), or
  "Retry compute" with an error line (job already failed) — any of these three confirms the page
  resumed the real server-side state instead of silently resetting to idle
- No extra click was needed to see the correct state

---

### UT-08 — Reloading after a failure resumes the failed state and its exact error (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Complete UT-05 first, so the panel is already showing "Retry compute" and its red error line on a
  corrupted scoped backend

**Steps:**
1. With the panel already showing "Retry compute" and the red error line, reload the page (F5 /
   Cmd+R)
2. Observe the panel immediately after reload, without clicking anything

**Expected Result:**
- Without any click, the panel immediately shows the button reading "Retry compute" (enabled) and
  the SAME red error line text as before the reload
  (`data-testid="edge-report-compute-error"`)
- The plain idle "Compute edge report" label does NOT appear at any point during or after the
  reload

---

### UT-09 — Not-computed headline/detail/register are byte-unchanged from J-01 (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- A FRESH scoped backend/frontend pair — cold compute state AND cold edge-report cache (never
  triggered)

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Read the Edge Report section's panel text before clicking anything

**Expected Result:**
- The headline reads exactly: "Edge report not computed yet."
- The detail line reads exactly: "The 3-way strategy-comparison sweep has not been run for the
  current dataset registry and configuration. It never runs automatically on a GET -- an operator
  must trigger the compute."
- These two lines and their layout are unchanged from the prior iteration (J-01) — only the new
  button sits beneath them; nothing about the existing headline/detail text has changed
- Cross-check: `curl http://localhost:8391/research/edge-report` returns `"dataset_count": 1` and
  `"compute": null` at this point (no compute ever triggered against this fresh instance)

---

### UT-10 — Other `/structure` sections are unaffected by this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Tradable Map, Case Studies, Registry, Comparison sections)

**Preconditions:** Any running frontend instance, page loads successfully. **Safe to run against
either the scoped instance or the standard `http://localhost:3301` instance — this test never
clicks "Compute edge report."**

**Steps:**
1. Navigate to `http://localhost:3391/structure` (or `http://localhost:3301/structure`)
2. Scroll from the very top of the page to the very bottom
3. Note each section heading encountered, in order

**Expected Result:**
- The following Panel headings all appear, in this order: "Tradable Map", "Case Studies", "Edge
  Report", "Fetch from Yahoo Finance", "Registry", "Comparison"
- Each non-Edge-Report section renders its own normal content or its own pre-existing honest
  empty/unavailable state exactly as before this iteration — no blank sections, no crashed
  components, no error-boundary message
- The only visible difference anywhere on the page compared to the prior iteration is inside the
  Edge Report section's not-computed panel (the new button/progress/error elements)

---

### UT-11 — Retry compute succeeds once the underlying issue is fixed (happy path)

**Type:** happy-path
**Priority:** P3
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Continue directly from UT-05/UT-08 (panel showing "Retry compute" + error)
- Apply the "to restore" step from the sub-recipe above (re-copy the clean fixture, restart the
  scoped backend)

**Steps:**
1. Reload `http://localhost:3391/structure` (the panel still shows "Retry compute" and the OLD
   error line, per UT-08's resume behavior — the manager's last-known snapshot is still the failed
   one from before the restart)
2. Click "Retry compute"
3. Wait up to 90 seconds

**Expected Result:**
- The button relabels to "Computing…" and disables, exactly as in UT-02
- Within 90 seconds, the panel is replaced by the finished report or the honest empty state (UT-02's
  outcomes) — NOT by the same error again — confirming the retry genuinely re-ran the compute against
  the now-fixed data rather than replaying a cached failure

---

### UT-12 — The new capability is discoverable without developer knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/structure` → Edge Report section

**Preconditions:** Any running frontend instance, page loads successfully.

**Steps:**
1. Navigate to `http://localhost:3391` (or the standard frontend's home page)
2. Click "Structure" in the top navigation bar (`data-testid="nav-link"`, label "Structure")
3. On the Structure page, scroll down — no more than the length of roughly one page — until the
   "Edge Report" panel is visible
4. Read the button inside the not-computed panel without any prior explanation of this feature

**Expected Result:**
- "Structure" is visible as a top-level nav link with no login or menu-digging required
- The Edge Report section is reachable purely by scrolling — no additional click, no hidden tab, no
  separate URL
- The button's label "Compute edge report" is self-explanatory: a first-time visitor can infer that
  clicking it starts computing the report described by the section's own intro text, without reading
  source code or asking a developer

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Not-computed panel loads (cold) | smoke | P1 | `/structure` Edge Report |
| UT-02 | Full compute lifecycle | happy-path | P1 | `/structure` Edge Report |
| UT-03 | Button blocks second trigger | validation | P2 | `/structure` Edge Report |
| UT-04 | Progress line format | happy-path | P2 | `/structure` Edge Report |
| UT-05 | Failed compute shows exact error | error | P2 | `/structure` Edge Report |
| UT-06 | Unreachable backend at click | error | P2 | `/structure` Edge Report |
| UT-07 | Reload mid-job resumes state | happy-path | P1 | `/structure` Edge Report |
| UT-08 | Reload after failure resumes state | happy-path | P2 | `/structure` Edge Report |
| UT-09 | J-01 not-computed render frozen | regression | P1 | `/structure` Edge Report |
| UT-10 | Other sections unaffected (J-07) | regression | P1 | `/structure` (all sections) |
| UT-11 | Retry succeeds after fix | happy-path | P3 | `/structure` Edge Report |
| UT-12 | Feature discoverability | ux | P2 | nav → `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Priority rationale (deviates slightly from the default smoke/happy-path=P1,
regression=P3 rubric):** UT-09 and UT-10 are elevated to P1 because the phase spec's own Definition
of Done names required-still-passing journeys J-01 and J-07 as blocking gates for this iteration, not
low-risk regressions. UT-04, UT-08, and UT-11 are secondary refinements of the SAME capability UT-02
and UT-07 already gate at P1 (progress-text formatting, a resume variant, and a recovery variant,
respectively), so they carry P2/P3 instead of automatic P1.

**Traceability to the functional test plan** (`reports/qa/goal-fast_wall-iter-4-test-plan.md`):
UT-01/UT-09 correspond to TC-17 (J-01 frozen render); UT-02/UT-04/UT-07 correspond to TC-15 (browser
compute lifecycle); UT-05/UT-08 correspond to TC-16 (browser failed-state render); UT-10 corresponds
to TC-18 (J-07 regression sentinel). UT-03, UT-06, UT-11, UT-12 are UI-only checks with no functional
TC counterpart (client-side button-state guarding, a client-only unreachable-backend path, the retry
recovery loop, and discoverability are not exercised by the API-level test plan).

**Known verification gap carried from the dev handoff:** as of this iteration's dev handoff
(`docs/handoffs/goal-fast_wall-iter-4-dev.md`), Chrome MCP could not be started in the developer's own
session, so none of TC-15/TC-16 (and by extension UT-02 through UT-11) have an actual screenshot yet
— they were verified indirectly via curl against a real running scoped backend and a strict TypeScript
build. Per this project's "no screenshot ⇒ unknown, never passing" discipline, this test plan should
be treated as the FIRST real attempt at a genuine browser pass, not a re-confirmation of one.
