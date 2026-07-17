# Phase goal-fast_wall-iter-6 — UI Test Plan

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 (standard instance) — **but see the warning below: every
test in this plan must instead target the SCOPED instance at http://localhost:3391.**

---

## Context

This iteration shipped **zero frontend code changes** (`apps/frontend/` has zero diff, git-confirmed
byte-identical to iter-5). What changed is entirely inside `compute_setups`'s backend caching: a new
durable, restart-surviving, content-keyed cache now sits in front of the existing multi-minute
full-panel touch-event scan that backs the Case Studies panel (and, indirectly — twice per run — the
Edge Report "Compute edge report" action, via `run_strategy_comparison_report`). This test plan's job
is almost entirely **regression confirmation**, not new-capability testing: prove nothing on
`/structure` visually changed, and confirm the one new failure mode this iteration introduces (a
durable-cache write failure) stays completely invisible to the user.

**Known-good baseline:** the developer's own handoff (`docs/handoffs/goal-fast_wall-iter-6-dev.md`,
"Live verification" section) already completed one successful live Chrome pass this iteration using
the exact scoped recipe below — zero `-loading`-suffixed testids found after a 10s wait, every
section's render confirmed byte-identical to iter-5, and a real `setups_scan_cache.db` file confirmed
written to disk with one row after the page load. This plan exists to give the QA/browser-qa-agent
lane its own independent, reproducible confirmation of that same pass, plus one genuinely new
browser-observable check (UT-05, the publish-failure sub-recipe) the developer's own pass did not
attempt.

**Why there is no dedicated "validation" test case this iteration:** no form or input control was
added or changed this iteration (the Case Studies Symbol/Reaction filters are pre-existing and
untouched by this diff — UT-02 below re-confirms they still render and accept input, but their
validation behavior is unchanged from prior iterations and is not re-litigated here).

---

## ⚠️ Required test environment — read this before running any test below

Never run any test in this plan against the standard `http://localhost:3301` / `http://localhost:8301`
instance. Two independent hazards apply there:
1. `GET /research/setups` (Case Studies' own data source) is an ordinary read endpoint that can
   itself **synchronously run the multi-minute full-panel scan** if no warm cache exists yet for the
   current config/store — simply loading `/structure` for the first time since a restart can trigger
   this, with no button click involved. This is exactly the cost J-06 makes survive a restart, not a
   cost it eliminates on a first-ever load.
2. `POST /research/edge-report/compute` sweeps the real 882MB / 18-dataset corpus if triggered —
   the same CPU-pin hazard iter-4/iter-5's own test plans already warned about (none of this
   iteration's tests trigger it, but do not click "Compute edge report" there regardless).

Use a small, disposable SCOPED instance for every test below.

### One-time setup (before UT-01 through UT-04, UT-06, UT-07)

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
TAPEOLOGY_SETUPS_CACHE_DB="$SCOPED_DIR/setups_scan_cache.db" \
uvicorn main:app --host 0.0.0.0 --port 8391
```
(The last env var, `TAPEOLOGY_SETUPS_CACHE_DB`, is new this iteration — it keeps the new durable
scan cache scoped to this disposable directory too, appended onto iter-4's/iter-5's already-established
recipe, per the "one new env var per new durable cache" precedent.)

**Terminal 2 — scoped frontend, port 3391:**
```bash
cd apps/frontend
NEXT_PUBLIC_API_URL=http://localhost:8391 npx next dev -p 3391
```

**Verify both are up** before testing: `curl http://localhost:8391/research/setups` must return
exactly `{"events":[]}` — this cold, honest-empty state (the scoped bar dir is intentionally empty) is
the starting point every test below assumes. Then open `http://localhost:3391/structure`.

Every "Frontend URL" / navigation target below means **`http://localhost:3391`** unless a test says
otherwise. Tear down both processes (Ctrl+C in each terminal) when testing is complete; confirm no
stray `uvicorn`/`next dev` process for this project remains.

**Why `datasets_j03` + an empty bar dir:** the scoped bar dir is created via bare `mkdir -p` and never
populated, and the committed `tests/fixtures/bars/` fixture itself carries zero `"5m"`-timeframe
series — so `GET /research/setups` honestly resolves zero band-touch events on this fixture, every
time, regardless of J-06's correctness. Case Studies rendering its empty state is the CORRECT expected
outcome on this fixture, not a failure — see UT-06 for what this specifically means you cannot verify
here.

### Sub-recipe: arranging a durable-cache publish failure (used by UT-05 only)

1. Tear down the one-time setup's instance first (Ctrl+C both terminals) if it is still running.
2. Create a fresh scoped dir and pre-create (but do not yet lock) a subdirectory for the cache file —
   order matters:
   ```bash
   SCOPED_DIR=$(mktemp -d)
   mkdir -p "$SCOPED_DIR/bars" "$SCOPED_DIR/ro_cache"
   cp -r apps/backend/tests/fixtures/datasets_j03 "$SCOPED_DIR/datasets"
   chmod 555 "$SCOPED_DIR/ro_cache"
   ```
   (Pre-creating `ro_cache` before locking it matters: the cache constructor calls
   `mkdir(parents=True, exist_ok=True)` on the target directory, which is a safe no-op on an
   already-existing directory — but would raise an uncaught `PermissionError` if it had to actually
   create a new directory inside a read-only parent. Locking an already-existing directory avoids
   that and correctly exercises the intended `sqlite3.Error`-swallowing path instead.)
3. Start the backend exactly as in the one-time setup above, on the same ports 8391, but with
   `TAPEOLOGY_SETUPS_CACHE_DB="$SCOPED_DIR/ro_cache/setups_scan_cache.db"` in place of the normal
   writable path — every other env var (`TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_BAR_DIR`,
   `TAPEOLOGY_JOURNAL_DB`, `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`)
   unchanged.
4. Start the frontend exactly as in the one-time setup above, on port 3391.

To reset afterward: tear down (Ctrl+C both terminals); discarding `$SCOPED_DIR` entirely (its parent
remains writable, so `rm -rf` on it works fine despite the read-only subdirectory inside it) and
restarting the plain one-time setup is the simplest way to return to the other tests.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/structure` reaches full ready state within 10 seconds, no loading panel remains (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (whole page)

**Preconditions:**
- Scoped backend/frontend pair running per the one-time setup above, freshly started (cold
  `TAPEOLOGY_SETUPS_CACHE_DB` — the file does not exist yet)

**Steps:**
1. Navigate to `http://localhost:3391/structure` (a fresh hard reload/new tab, not a client-side link
   click from another page)
2. Wait 10 seconds without clicking anything
3. Open the browser DevTools console and run:
   `document.querySelectorAll('[data-testid$="-loading"]').length`
4. Visually scan every panel on the page, top to bottom

**Expected Result:**
- The `<h1 data-testid="structure-title">` reads exactly "Structure" and is visible near the top of
  the page
- Step 3's query returns `0` — no element anywhere on the page has a `data-testid` ending in
  `-loading` (this covers `case-studies-loading`, `edge-report-loading`, `tradable-map-loading`,
  `tradable-map-chart-loading`, `structure-loading`, `structure-chart-loading`,
  `structure-registry-loading`, `comparison-founding-loading`, `comparison-datasets-loading`)
- No blank white sections, no crashed/error-boundary component, no visible spinner anywhere
- No console errors (the standard "Download the React DevTools..." info line is not an error)

---

### UT-02 — Case Studies renders its honest empty state; filters remain present but inert (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Case Studies panel)

**Preconditions:** Same as UT-01.

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Scroll down past "Tradable Map" to the "Case Studies" panel
3. Read the panel's content before touching either filter field
4. Type `ZZZZ` into the "Symbol" field (`data-testid="case-studies-filter-symbol"`)
5. Select any non-"All" option from the "Reaction" dropdown
   (`data-testid="case-studies-filter-reaction"`)

**Expected Result:**
- Step 3: a panel with `data-testid="case-studies-empty"` is visible, showing the title "No
  band-touch events scanned yet." — NOT a loading spinner, NOT an "unavailable" error panel
  (`case-studies-unavailable`), NOT a populated table
- Steps 4–5: the panel's text stays exactly "No band-touch events scanned yet." — it does NOT change
  to "No events match these filters." (`case-studies-no-match` requires at least one already-scanned
  event to exist before a filter can narrow it down to zero; with zero scanned events on this fixture,
  there is nothing to narrow)
- The "Symbol" and "Reaction" filter inputs themselves remain visible, enabled, and editable
  throughout — confirms this iteration did not disable or remove them
- No console errors

---

### UT-03 — Edge Report's not-computed panel renders byte-identical to before this iteration (regression, no click)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Edge Report panel)

**Preconditions:** Same as UT-01. **Do NOT click "Compute edge report" in this test.**

**Steps:**
1. Navigate to `http://localhost:3391/structure`
2. Scroll down past "Case Studies" to the "Edge Report" panel
3. Read the panel's headline and detail text
4. Locate the button but do not click it

**Expected Result:**
- A panel with `data-testid="edge-report-not-computed"` is visible
- The headline reads exactly: "Edge report not computed yet."
- The detail line reads exactly: "The 3-way strategy-comparison sweep has not been run for the
  current dataset registry and configuration. It never runs automatically on a GET -- an operator
  must trigger the compute."
- A button reading exactly "Compute edge report" (`data-testid="edge-report-compute-button"`) is
  visible and enabled (no `disabled` attribute)
- No progress line, no red error line, and no report table are visible
- This text is unchanged from iter-4's/iter-5's own confirmed baseline — confirms `compute_setups`'s
  caching rewrite did not alter Edge Report's static (pre-click) render, even though
  `run_strategy_comparison_report` calls `compute_setups` internally (twice) when it eventually runs

---

### UT-04 — Tradable Map, Registry, and Comparison sections are unaffected (regression, J-02/J-03/J-07 sentinel)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Tradable Map, Registry, Comparison panels)

**Preconditions:** Same as UT-01.

**Steps:**
1. With `http://localhost:3391/structure` loaded, scroll from the very top of the page to the very
   bottom
2. Note each panel heading encountered, in order
3. Read the "Tradable Map" panel's content
4. Read the "Registry" panel's content, specifically the Champion block and the list of strategy
   cards
5. Read the "Comparison" panel's content, specifically the dataset dropdown

**Expected Result:**
- The following panel headings all appear, in this order: "Tradable Map", "Case Studies", "Edge
  Report", "Fetch from Yahoo Finance", "Registry", "Comparison"
- Step 3: the Tradable Map panel shows its idle state (`data-testid="tradable-map-idle"`) with the
  title "Choose a symbol and an as-of time, then Load, to see its tradable level map." — not a
  loading spinner, not an error
- Step 4: the Registry panel shows a "Champion" block (`data-testid="champion-summary"`) with a
  non-empty strategy id, followed by exactly three strategy cards (`data-testid="strategy-card"`,
  one each carrying `data-strategy-id="v1"`, `"structure_tape"`, and `"structure_tape_map"`)
- Step 5: the Comparison panel's dataset dropdown (`data-testid="comparison-dataset-select"`)
  contains the placeholder "Choose a dataset…" plus at least one dataset option (its label starts
  with "PG ·" on the recommended `datasets_j03` fixture)
- No blank sections, no crashed components, no error-boundary message anywhere on the page
- Zero visual or textual difference from the iter-5 baseline anywhere in these three sections

---

### UT-05 — Case Studies still renders normally even when the durable cache cannot be written (error, TC-8's browser leg)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Case Studies panel); backend startup configuration

**Preconditions:** The "arranging a durable-cache publish failure" sub-recipe above, completed
through step 4 (a fresh scoped backend/frontend pair whose `TAPEOLOGY_SETUPS_CACHE_DB` points inside
a read-only directory).

**Steps:**
1. With the sub-recipe's backend/frontend pair running, navigate to `http://localhost:3391/structure`
2. Wait 10 seconds
3. Read the Case Studies panel's content
4. Reload the page once more (F5)

**Expected Result:**
- The Case Studies panel renders `data-testid="case-studies-empty"` with "No band-touch events
  scanned yet." — exactly the same honest-empty render as UT-02, with NO crash, NO "unavailable"
  error panel, and NO 500-style error page anywhere
- The page does not hang, does not show a blank screen, and does not show any error message
  referencing the cache file, disk, or SQLite
- No console errors
- Step 4's reload produces the identical result again (the read-only cache directory does not cause a
  repeated or worsening failure — every call independently re-attempts and re-swallows)
- This confirms a durable-cache write failure is completely invisible to the user: the
  freshly-scanned result is still served normally, matching TC-8's own pass criteria

---

### UT-06 — Populated table, drill-in, "no match" filter, and restart-survival timing are NOT independently browser-verifiable this iteration (happy path — documented limitation, SKIP acceptable)

**Type:** happy-path
**Priority:** P3 (informational — not part of this iteration's Definition of Done)
**Surface:** `/structure` (Case Studies panel, drill-in panel)

**Status: NOT independently browser-verifiable this iteration with the mandated scoped/keyless
fixture pair — SKIP is an acceptable outcome. Do not fail the phase for not executing this test.**

**Why:** the scoped bar dir this recipe creates is always EMPTY (`mkdir -p`, never populated), and the
committed `tests/fixtures/bars/` fixture itself carries zero `"5m"`-timeframe series either — so
`GET /research/setups` resolves zero events on this fixture regardless of J-06's correctness
(`setupsEvents.length === 0` is always true here). With zero rows:
- `case-studies-table` can never render — there is no row to click, so `case-drillin-loading` /
  `case-drillin-unavailable` / `case-drillin` can never mount.
- `case-studies-no-match` can never render either — that state requires `setupsEvents.length > 0` AND
  a filter matching none of them; an empty registry cannot produce it (confirmed directly in UT-02).
- The restart-survival benefit itself (a warm durable cache serving instantly instead of re-scanning)
  is real but not browser-timing-observable on this fixture: both a cold scan and a warm cache-hit
  against an empty bar dir complete in single-digit milliseconds either way (the dev handoff's own
  `curl` check measured 7ms), so no stopwatch or Network-tab timing comparison in a browser can
  distinguish "served from cache" from "freshly rescanned" here.

The authoritative, non-vacuous proof of all of the above lives entirely at the automated unit-test
level: TC-1 (restart simulation, zero rescans, byte-identical), TC-2 (content-hash equality across a
distinct-identity `Config`), TC-5 (cache-loss recompute), and TC-6 (the deliberately-wrong-payload
mutation probe proving the durable-hit path is genuinely read, not dead code) in
`reports/qa/goal-fast_wall-iter-6-test-plan.md`. Do not duplicate those here.

**Optional path to observe restart-survival live (real corpus, NOT required, NOT part of this test
plan's pass criteria):** on the standard `http://localhost:3301/structure` instance — ONLY if you
already know its backend has been running long enough to have a warm setups scan cache for the
current config — restarting that backend process and reloading `/structure` would show Case Studies
reaching its populated `case-studies-table` state near-instantly instead of after a multi-minute
wait. Do NOT restart or freshly load the standard instance's `/structure` as a casual check: if its
durable setups-scan cache is COLD for the current config (e.g., after a fresh checkout, or its
first-ever load), a `GET /research/setups` call synchronously runs the full multi-minute panel scan
on that request — this is the exact "multi-minute" cost this whole interlude exists to make survive a
restart, not to eliminate on a first load. This plan does not include steps to perform that
real-corpus check.

**Pass criteria:** SKIP (with the reason above recorded) is a PASS for this test case.

---

### UT-07 — `/structure` and its Case Studies panel are discoverable without developer knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** navigation → `/structure`

**Preconditions:** Any running frontend instance (scoped or standard), page loads successfully.

**Steps:**
1. Navigate to `http://localhost:3391` (or the standard frontend's home page)
2. Click "Structure" in the top navigation bar (`data-testid="nav-link"`, label "Structure")
3. On the Structure page, scroll down — no more than the length of roughly one page — until the
   "Case Studies" panel is visible
4. Read the panel's intro text and empty-state message without any prior explanation of this feature

**Expected Result:**
- "Structure" is visible as a top-level nav link with no login or menu-digging required
- The Case Studies panel is reachable purely by scrolling — no additional click, no hidden tab, no
  separate URL
- The panel's intro text ("Every band-touch event this store has scanned, read verbatim from GET
  /research/setups...") and its empty-state message ("No band-touch events scanned yet.") are both
  self-explanatory to a first-time visitor, without reading source code or asking a developer
- Nothing about this flow differs from iter-5 — this iteration adds no new navigation, no new button,
  no new panel

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Full ready state, zero loading panels | smoke | P1 | `/structure` (whole page) |
| UT-02 | Case Studies honest-empty render | regression | P1 | `/structure` Case Studies |
| UT-03 | Edge Report not-computed panel frozen | regression | P1 | `/structure` Edge Report |
| UT-04 | Tradable Map / Registry / Comparison unaffected | regression | P1 | `/structure` (3 sections) |
| UT-05 | Case Studies survives a broken durable cache | error | P2 | `/structure` Case Studies |
| UT-06 | Populated/drill-in/restart-timing — SKIP acceptable | happy-path | P3 | `/structure` Case Studies |
| UT-07 | Feature discoverability | ux | P2 | nav → `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS. UT-06's documented SKIP does not count
against the verdict.**

**Priority rationale (deviates from the default smoke/happy-path=P1, regression=P3 rubric):** UT-02,
UT-03, and UT-04 are elevated to P1 because they are this iteration's actual regression sentinels for
J-01/J-02/J-03/J-07 and directly operationalize TC-9's Definition-of-Done wording ("no
`-loading`-suffixed testid remains... zero visual regression"). UT-06 is depressed to P3/SKIP-acceptable
because it is explicitly named in `docs/goal.md` itself as non-blocking, real-corpus-only, and never
part of this iteration's Definition of Done. UT-05 sits at P2: it is a genuinely new, iteration-specific
check (TC-8's browser leg), but a durable-cache write failure is a narrow edge case, not a routine
regression risk.

**Traceability to the functional test plan** (`reports/qa/goal-fast_wall-iter-6-test-plan.md`):
UT-01/UT-02/UT-03/UT-04 correspond to TC-09 (the browser check) and, by extension, the
"required-still-passing" umbrella of TC-10. UT-05 corresponds to TC-08 (publish-failure swallowed) —
the browser-observable half of a test whose byte-identity proof already lives at the API/unit level.
UT-06 explicitly does NOT re-prove TC-01/TC-02/TC-03/TC-04/TC-05/TC-06 — those are pure
backend/pytest-level determinism proofs with no browser-observable surface on the mandated fixture;
duplicating them here would be either impossible (the fixture cannot produce the scenario) or
redundant (raw API/byte-identity assertions, not UI behavior). UT-07 is a UI-only discoverability
check with no functional TC counterpart, matching the identical role UT-12/UT-09 played in
iter-4's/iter-5's own plans. TC-07 (frozen foundations — guard tests, MCP tool count, config
fingerprint) has no browser-observable surface at all and is intentionally not duplicated here either.
