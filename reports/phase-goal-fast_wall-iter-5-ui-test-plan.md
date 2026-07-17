# Phase goal-fast_wall-iter-5 — UI Test Plan

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 (standard instance) — **but see the warning below: every
test that clicks "Compute edge report" must instead target the SCOPED instance at
http://localhost:3391.**

---

## Context

This iteration shipped **zero frontend code changes** (`apps/frontend/` has zero diff, git-confirmed
byte-identical to iter-4). Two things are under test instead:

1. **J-04's still-missing browser evidence** — the already-shipped "Compute edge report" button,
   live progress line, and failed-state render, driven end-to-end in a live Chrome session for the
   first time (TC-1/TC-2/TC-3 in the functional test plan). This is a **re-verification**, not new
   functionality.
2. **J-05's one narrowly observable effect** — the progress line's existing "(N from cache)" clause
   (present in the code since iter-4, permanently dead until now) can genuinely show N > 0 on a
   **resumed** compute. On a first-ever, cold-cache click — the only scenario reliably reproducible
   with the committed test fixtures — this annotation stays absent, exactly as before.

**Known-good baseline:** the developer's own handoff (`docs/handoffs/goal-fast_wall-iter-5-dev.md`,
"Live verification" section) already completed one successful live Chrome pass this iteration using
the exact recipe below, capturing real screenshots for TC-1/TC-2/TC-3. This plan exists to give the
QA/browser-qa-agent lane its own independent, reproducible confirmation — this is a re-run of a
recipe already proven to work, not a first attempt into unknown territory.

---

## ⚠️ Required test environment — read this before running any test below

Any test that clicks "Compute edge report" must run against a SCOPED backend/frontend pair — never
against the standard `http://localhost:3301` / `http://localhost:8301` instance. The standard
instance reads the project's real corpus (`.data/datasets`, 882MB, 18 registered datasets); clicking
the button there starts a genuine sweep over the full corpus — the exact CPU-pin hazard this "Fast
Wall" interlude exists to remove from casual verification passes.

Only **UT-08** (a pure scroll-through that never clicks compute) is safe to run against either
instance.

### One-time setup (before UT-01 through UT-07, UT-09)

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
TAPEOLOGY_EDGE_SWEEP_CACHE_DB="$SCOPED_DIR/edge_report_backtests.db" \
uvicorn main:app --host 0.0.0.0 --port 8391
```

**Terminal 2 — scoped frontend, port 3391:**
```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8391 npx next dev -p 3391
```

**This iteration adds one line to iter-4's recipe:** `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` — the new
per-pair backtest cache's own path. Without it, J-05's new durable sub-cache would fall back to a
default path and risk landing beside real data; setting it explicitly keeps it scoped to
`$SCOPED_DIR`, exactly like the existing `TAPEOLOGY_EDGE_REPORT_CACHE_DB`.

**Verify both are up** before testing: `curl http://localhost:8391/research/edge-report` must
return JSON containing `"status": "not_computed"` and `"dataset_count": 1` — this cold state is the
starting point every test below assumes. Then open `http://localhost:3391/structure`.

Every "Frontend URL" / navigation target below means **`http://localhost:3391`** unless a test says
otherwise. Tear down both processes (Ctrl+C in each terminal) when testing is complete; confirm no
stray `uvicorn`/`next dev` process for this project remains.

**Why `datasets_j03`:** its one dataset (symbol PG) is not a config-owned panel symbol, so a
triggered compute honestly resolves zero eligible backtest pairs and finishes in well under a
second — the "0 / 0 backtests" progress line and the "No edge-report cells yet." terminal state are
the exact, deterministic, reproducible outcomes on this fixture (confirmed by this iteration's own
dev handoff). This is a valid, honest outcome — every test below treats it as a PASS, not a failure.

### Sub-recipe: arranging a "failed" compute (used by UT-06) — CORRECTED this iteration

**This recipe is different from iter-4's own `ui-test-plan.md` and is simpler: no backend restart
is needed at any point.** This iteration's dev handoff (`docs/handoffs/goal-fast_wall-iter-5-dev.md`,
"Known Issues") documents that iter-4's original recipe (corrupt → restart → leave corrupted)
actually produces a *different* render than intended: `GET /research/edge-report` independently
re-verifies dataset integrity on every read, so a *permanently* corrupted dataset makes that GET
itself 500 on every call — the frontend then shows a generic "edge report could not complete: ...
Nothing cached and nothing fabricated is shown in its place." panel, never the not-computed panel's
own embedded failed-compute render. **Order matters — follow these steps exactly:**

1. Start a FRESH scoped backend/frontend pair per the one-time setup above (dataset healthy, cold
   caches, no compute ever triggered).
2. Navigate to `http://localhost:3391/structure` and confirm the not-computed panel with the idle
   "Compute edge report" button is visible (do not click yet).
3. Corrupt the scoped dataset file on disk, backend still running, nothing clicked yet:
   `echo "corrupted" >> "$SCOPED_DIR/datasets/"*.json`
4. Click the "Compute edge report" button in the browser. The backend reads the now-corrupted file,
   fails integrity verification, and records the failure in its in-memory job snapshot.
5. **Immediately afterward** (within a few seconds — before checking the browser panel again),
   restore the original file content, still without restarting the backend:
   `rm -rf "$SCOPED_DIR/datasets" && cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"`
6. Now look at the browser panel (it may already show the error, or wait a moment for the next poll
   tick / reload the page once).

**If you see the generic "edge report could not complete" panel instead of the not-computed panel's
own red error line:** you likely checked the browser before step 5's restore completed, or skipped
it — restore the file (step 5) and reload; the panel will resolve to the correct render described in
UT-06 below. This is not itself a product defect, just a recipe-ordering mistake.

To reset the whole scenario for a re-run, tear down and restart the one-time setup from scratch.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/structure` loads with the not-computed panel, exact J-01 text (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Scoped backend/frontend pair running per the one-time setup above, freshly started (cold
  `TAPEOLOGY_EDGE_REPORT_CACHE_DB` AND cold `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`, no compute ever
  triggered against this backend instance)

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Wait for the page to finish loading
3. Scroll down past the "Tradable Map" and "Case Studies" panels to the "Edge Report" panel
4. Read the panel's headline and detail text before clicking anything

**Expected Result:**
- The panel heading "Edge Report" is visible
- A panel with `data-testid="edge-report-not-computed"` is visible, showing:
  - The amber headline reading exactly: "Edge report not computed yet."
  - The detail line reading exactly: "The 3-way strategy-comparison sweep has not been run for the
    current dataset registry and configuration. It never runs automatically on a GET -- an operator
    must trigger the compute." (this text is byte-unchanged from J-01 per this iteration's own
    diff — confirms the required-still-passing J-01 regression sentinel)
  - A button reading exactly "Compute edge report" (`data-testid="edge-report-compute-button"`),
    enabled (no `disabled` attribute)
- No progress line, no red error line, and no report table are visible yet
- No console errors

---

### UT-02 — Full compute lifecycle: click → running → terminal state (happy path, closes J-04)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold caches).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Capture a screenshot of the pre-click state (the not-computed panel and idle button clearly
   visible)
3. Click the "Compute edge report" button (`data-testid="edge-report-compute-button"`)
4. Immediately (within 1–2 seconds) capture a second screenshot of the button and the area directly
   beneath it
5. Without reloading the page, wait up to 90 seconds, watching the panel
6. Once the panel changes, capture a third screenshot of its final content

**Expected Result:**
- Step 4: the button's label changes to "Computing…" and becomes disabled; a progress line appears
  beneath it (`data-testid="edge-report-compute-progress"`) reading exactly "0 / 0 backtests" — OR
  the panel has already moved past this point by the time you look (expected on this fixture: the
  compute resolves 0 eligible pairs and can finish in well under a second)
- The progress line's text does NOT include a "(N from cache)" clause at any point — this is the
  first-ever compute against a cold sub-cache, so there is nothing yet to resume from; the
  annotation stays absent exactly as it did in iter-4 (confirms J-05's change is invisible on a cold
  first click)
- Within 90 seconds, the not-computed panel is replaced by the honest empty state reading "No
  edge-report cells yet." (`data-testid="edge-report-empty"`) with detail "No recorded dataset has
  resolved an owning, classified scan event — an honest, valid outcome, never hidden." — this is the
  confirmed, deterministic outcome on the `datasets_j03` fixture (PG is not a config-owned panel
  symbol). A populated report view (`edge-report-register` + `edge-report-train-table` /
  `edge-report-holdout-table`) would also be an acceptable pass if a different fixture is used, but
  is not the expected outcome here.
- Throughout, the browser stays at `http://localhost:3391/structure` with no full-page reload (no
  white flash, no from-scratch loading spinner replacing the whole page, URL unchanged)

---

### UT-03 — Button blocks a second trigger while a job is running (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same as UT-01 (fresh scoped pair, cold caches).

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Click "Compute edge report"
3. Immediately attempt to click the SAME button again (as fast as possible), before the panel
   visibly changes

**Expected Result:**
- After the first click, the button carries the `disabled` attribute and reads "Computing…" — the
  attempted second click has no effect (no visible change, no second progress line, no second
  network request fired)
- The button does not toggle back to enabled between the first and second click
- The button only becomes clickable again once the job reaches a terminal state (replaced by the
  report/empty state, or re-enabled reading "Retry compute" on failure)

---

### UT-04 — Reload after completion serves the warm result directly, no button (regression, TC-2)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:** Same scoped session as UT-02, immediately after UT-02's compute has reached a
terminal state (empty state or report view).

**Steps:**
1. With the Edge Report section already showing the terminal result from UT-02, reload
   `http://localhost:3391/structure` (F5 / Cmd+R)
2. Wait for the page to fully load
3. Look at the Edge Report section without clicking anything

**Expected Result:**
- The Edge Report section shows the same warm result from UT-02 immediately (the empty state or
  report view) — it does NOT reset to the idle "Compute edge report" button or the not-computed
  panel
- No button, no progress line, and no "Computing…" state appear anywhere in the section
- Cross-check (optional): `curl http://localhost:8391/research/edge-report` returns the same warm
  report shape with no `status` key (confirms the result is served from the single canonical
  endpoint, not just held in the browser tab)

---

### UT-05 — Other `/structure` sections are unaffected by this iteration (regression, TC-2/J-07)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Tradable Map, Case Studies, Fetch from Yahoo Finance, Registry,
Comparison sections)

**Preconditions:** Same scoped session as UT-02/UT-04, page already reloaded once.

**Steps:**
1. With `http://localhost:3391/structure` loaded, scroll from the very top of the page to the very
   bottom
2. Note each section heading encountered, in order
3. Capture a screenshot (or DOM-text extraction) of each section listed below

**Expected Result:**
- The following panel headings all appear, in this order: "Tradable Map", "Case Studies", "Edge
  Report", "Fetch from Yahoo Finance", "Registry", "Comparison"
- The Tradable Map table (`data-testid="tradable-map-table"`) renders its band rows exactly as
  before this iteration
- The Case Studies table (`data-testid="case-studies-table"`) still lists its touch-event rows with
  the symbol/reaction filter controls present
- The "Fetch from Yahoo Finance" button (`data-testid="fetch-yahoo-button"`) is still present and
  enabled (do NOT click it — fetching from Yahoo is unrelated to this iteration's scope and would
  make an external network call)
- The Registry's champion summary block (`data-testid="champion-summary"`) still shows the current
  champion strategy/profile
- The Comparison section's champion block (`data-testid="comparison-champion"`) still renders
- Zero structural or textual difference from iter-4's own screenshots — no blank sections, no
  crashed components, no error-boundary message anywhere

---

### UT-06 — Failed compute shows the exact backend error and offers retry (error, TC-3)

**Type:** error
**Priority:** P1
**Surface:** `/structure` (Edge Report section)

**Preconditions:**
- Follow the CORRECTED sub-recipe above ("arranging a failed compute") through step 5 (corrupt →
  trigger → restore, all on a FRESH scoped backend instance, no restart)

**Steps:**
1. Complete steps 1–5 of the sub-recipe above
2. If the panel does not already show a red error line, reload `http://localhost:3391/structure`
   once
3. Read the panel's error text and button label

**Expected Result:**
- The not-computed panel shows a red error line (`data-testid="edge-report-compute-error"`) whose
  text matches the pattern "N dataset file(s) failed integrity verification ([filename(s)]) — the
  report stops with nothing written" — the backend's own exact `EdgeReportError` message, not a
  paraphrase. This iteration's own dev verification pass observed exactly: "1 dataset file(s) failed
  integrity verification (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing
  written" — your filename hash will differ (it matches whichever file your scoped copy corrupted),
  but the surrounding structure and wording must match verbatim.
- The button's label changes to "Retry compute" and is enabled again (does NOT stay stuck on
  "Computing…")
- No progress line is visible (the job is no longer running)
- No report table or the generic "edge report could not complete" panel renders anywhere on the page
  (if you see that generic panel instead, see the sub-recipe's troubleshooting note above — restore
  the file and reload)

---

### UT-07 — "(N from cache)" annotation shows N > 0 on a resumed compute (happy path — deferred)

**Type:** happy-path
**Priority:** P3 (informational — not part of this iteration's Definition of Done)
**Surface:** `/structure` (Edge Report section, progress line)

**Status: not independently browser-verifiable this iteration with any committed dataset fixture —
SKIP is an acceptable outcome. Do not fail the phase for not executing this test.**

**Why:** this iteration's own dev handoff (`docs/handoffs/goal-fast_wall-iter-5-dev.md`, "Known
Issues") documents that BOTH committed fixtures usable from a running scoped backend —
`datasets_j03` (symbol PG) and `apps/backend/tests/fixtures/datasets` — resolve **zero** eligible
(dataset, strategy) pairs against the panel-configured strategies. With zero eligible pairs, there is
nothing to durably cache and nothing to resume from, so the "(N from cache)" clause cannot appear
against either fixture no matter how the compute is triggered or interrupted. The developer's own
non-vacuous proof of this behavior (TC-8) required a purpose-built, Python-only synthetic test
fixture reachable only inside the pytest suite, not from a running server.

**The authoritative, non-vacuous proof of this behavior lives entirely at the automated unit-test
level** — TC-6 (kill-and-resume spy), TC-8 (parallel equivalence + multi-process spy), TC-10 (CLI
reusability), TC-11 (manager resumability) in `reports/qa/goal-fast_wall-iter-5-test-plan.md`. Do
not duplicate those here.

**Optional path to observe it live (real corpus, NOT required, NOT part of this test plan's pass
criteria):** after an operator separately runs the CLI warmer at least once against the real
`.data/datasets` corpus — an explicitly bonus, non-blocking, operator-gated action per this
iteration's own scope (see `reports/phase-goal-fast_wall-iter-5-user-visible-changes.md`, "Not
Visible Yet") — a subsequent click of "Compute edge report" / "Retry compute" on the **standard**
`http://localhost:3301/structure` instance, for a dataset whose pairs are already durably cached,
would show a progress line matching `{done} / {total} backtests (N from cache)` with N > 0. This
plan does not include steps to perform that real-corpus warmup.

**Pass criteria:** SKIP (with the reason above recorded) is a PASS for this test case.

---

### UT-08 — Standard instance quick sanity scroll (regression, no compute click)

**Type:** regression
**Priority:** P3
**Surface:** `/structure` (all sections, standard instance)

**Preconditions:** The standard backend/frontend instance is running (the normal `:8301`/`:3301`
pair). **Do NOT click "Compute edge report" on this instance** — it would sweep the real 882MB
corpus.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll from the very top of the page to the very bottom, without clicking any button in the Edge
   Report section
3. Note each section heading encountered, in order

**Expected Result:**
- The page loads without a blank screen or error message
- The same six section headings appear in the same order as UT-05: "Tradable Map", "Case Studies",
  "Edge Report", "Fetch from Yahoo Finance", "Registry", "Comparison"
- No console errors; no visible difference from the page's appearance before this iteration
- (If the Edge Report section here already shows a warm/finished report rather than the
  not-computed panel, that reflects prior real-corpus computes from earlier iterations/operator
  actions — not a defect of this iteration; do not interact with it either way)

---

### UT-09 — The capability is discoverable without developer knowledge (ux)

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
- Nothing about this flow differs from iter-4 — this iteration adds no new navigation and no new
  button

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Not-computed panel loads (cold), exact J-01 text | smoke | P1 | `/structure` Edge Report |
| UT-02 | Full compute lifecycle (closes J-04) | happy-path | P1 | `/structure` Edge Report |
| UT-03 | Button blocks second trigger | validation | P2 | `/structure` Edge Report |
| UT-04 | Reload serves warm result directly | regression | P1 | `/structure` Edge Report |
| UT-05 | Other sections unaffected (J-07) | regression | P1 | `/structure` (all sections) |
| UT-06 | Failed compute shows exact error | error | P1 | `/structure` Edge Report |
| UT-07 | "(N from cache)" > 0 — deferred, SKIP acceptable | happy-path | P3 | `/structure` Edge Report |
| UT-08 | Standard instance sanity scroll | regression | P3 | `/structure` (all sections) |
| UT-09 | Feature discoverability | ux | P2 | nav → `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS. UT-07's documented SKIP does not count
against the verdict.**

**Priority rationale (deviates from the default smoke/happy-path=P1, regression=P3 rubric):** UT-04,
UT-05, and UT-06 are elevated to P1 because the phase spec's own Definition of Done names them
directly as required, evidence-bearing gates for this iteration (TC-2's persistence check, the J-07
regression sentinel, and TC-3's failed-state render respectively) — not low-risk incidental checks.
UT-07 is depressed to P3/SKIP-acceptable because it is explicitly informational: neither committed
fixture can produce a non-vacuous demonstration of it, and it is not named in the Definition of Done.
UT-08 stays P3 as a low-risk supplementary sanity check, distinct from UT-05 which is the required
evidence-gathering pass.

**Traceability to the functional test plan** (`reports/qa/goal-fast_wall-iter-5-test-plan.md`):
UT-01 corresponds to TC-2's not-computed-panel half; UT-02 corresponds to TC-1; UT-04/UT-05
correspond to TC-2's persistence/regression-sentinel halves; UT-06 corresponds to TC-3. UT-03, UT-07,
UT-08, UT-09 are UI-only checks with no functional TC counterpart (client-side double-submit
guarding, the deferred from-cache annotation, a standard-instance sanity pass, and discoverability
are not exercised by the API-level test plan). TC-4 through TC-14 (API/unit-level: cache durability,
key-busting matrix, kill-and-resume, parallel equivalence, cache-loss recompute, CLI wiring, manager
resumability, byte-identity, frozen foundations) are intentionally NOT duplicated here — they have no
browser-observable surface and are already covered in the functional test plan.
