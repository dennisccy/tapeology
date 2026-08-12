# Phase goal-playbook-iter-10 — UI Test Plan

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Environment note (read before running any test below)

At the time this plan was written, `http://localhost:3301` was live and talking to a backend at
`http://localhost:8301` whose universe snapshot reports `source_url: "fixture-rig-iter8-replay"` —
i.e. the **scoped QA fixture rig**, the same one `browser-qa-agent` uses for this iteration's own
formal J-06/J-10 check, not necessarily the operator's separate real backend. All exact values
below (symbol `RTAAA`, prices, counts) were read live from that instance via
`GET /research/desk/playbook?date=2026-06-22`. If whoever runs this plan finds a different backend
active (e.g. the operator's real store has been restored — check by looking at the Playbook
Signals table for 2026-06-22 and seeing whether an `RTAAA` row exists), fall back to the general
rule stated in each test case: **any `range_trade` signal recorded before this iteration's code
shipped will show no `· turned at midrange` text, and that is correct, not a bug.**

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- No login required (no auth in this app)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Desk" (`data-testid="desk-title"`) is visible at the top of the page
- Scrolling down, the section heading "Playbook Signals" is visible (this section is
  unconditionally rendered regardless of any data state)
- No blank screen, no red error banner text, no unhandled exception overlay
- No new console errors compared to before this iteration (open DevTools → Console)

---

### UT-02 — Existing `range_trade` signal renders the new field correctly when its value is `false` (happy-path — mechanism proof, deterministic today)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- A `range_trade` signal exists for session date `2026-06-22` (symbol `RTAAA`) — true on the
  scoped fixture rig at time of writing; see the Environment note above if not found

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the field labeled "Session date (yyyy-MM-dd) — blank = the most recent recorded session"
   (`data-testid="desk-playbook-date-input"`), type `2026-06-22`
3. Wait for the Playbook Signals table (`data-testid="desk-playbook-table"`) to refresh
4. In the table, click the row whose `symbol` cell reads `RTAAA` and whose `setup` chip reads
   `Range Trade` (side chip reads `long`)

**Expected Result:**
- A detail panel opens below the table (`data-testid="desk-playbook-signal-detail"`)
- Its header line reads: `RTAAA Range Trade long trigger 102.60 at 10:05:00 ET · entry 102.60
  (level) · invalidation 99.22`
- The geometry line (`data-testid="desk-playbook-signal-range-trade-geometry"`) reads EXACTLY:
  `range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed
  midrange`
- Critically: the text `· turned at midrange` does **NOT** appear anywhere in that line, even
  though the field is present in the underlying data (it evaluates to `false` for this specific
  signal) — this is the field rendering correctly for a "present but false" value, the same way
  `crossed midrange` would be omitted if it were false
- No error, no missing-data placeholder, no layout shift

---

### UT-03 — A `range_trade` signal with `turned_at_midrange: true` shows the new chip (happy-path — TRUE case; currently blocked, documents the procedure)

**Type:** happy-path
**Priority:** P1 (blocked — see Preconditions)
**Surface:** `/desk` → Playbook Signals

**Preconditions:**
- **As of this analysis, no reachable signal on the running app evaluates `turned_at_midrange` to
  `true`.** The one `range_trade` signal available (`RTAAA`, 2026-06-22, see UT-02) is `false`,
  and its bars were not changed by this iteration, so reloading or re-clicking will not change the
  outcome. To exercise this test case for real, a `range_trade` signal that legitimately turned at
  the range's midpoint must first exist — either by running Playbook on a not-yet-recorded session
  date and finding a qualifying signal among whatever fires (not guaranteed — depends on real
  market/fixture data), or by a future fixture update seeding one deliberately. The backend test
  `test_range_trade_turned_at_midrange_true_and_its_near_miss_control`
  (`apps/backend/tests/test_desk_playbook_detect.py`) is the current authoritative proof that the
  underlying computation is correct; this UT case is the browser-level check to run the moment a
  live qualifying example exists.

**Steps (run once a qualifying record exists):**
1. Navigate to `http://localhost:3301/desk`
2. Type the qualifying session's date into the "Session date (yyyy-MM-dd)" field
   (`data-testid="desk-playbook-date-input"`)
3. In the Playbook Signals table, click the row for the `range_trade` signal known to have
   `turned_at_midrange: true`

**Expected Result:**
- The geometry line (`data-testid="desk-playbook-signal-range-trade-geometry"`) includes the text
  `· turned at midrange`, positioned immediately after `· crossed midrange` (if that is also true
  for the same signal) or standing alone if `crossed_midrange` is false for that signal
- Every other field on the line (range width, zone touch counts, break slot) still renders exactly
  as the record's data specifies — the new chip is additive only

---

### UT-04 — A `range_trade` signal recorded before this iteration shows no chip and no error (regression — absence is correct)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Signals

**Preconditions:**
- A `range_trade` signal recorded before this iteration's code shipped (its raw API response has
  no `turned_at_midrange` key at all inside `geometry`, as opposed to UT-02's `false` value). None
  was reachable via plain `/desk` navigation on the app instance available for this analysis (its
  one `range_trade` example was already recomputed with the new code — see UT-02); the backend
  team's own dev handoff confirmed this case directly against a real pre-iteration record
  (signature `16a2734d10c91ea7`) via `GET /research/desk/playbook`. If a genuinely pre-iteration
  `range_trade` record is reachable through the UI when this test runs, use it; otherwise treat
  UT-02 as covering the visual half of this case (both an absent key and a present-but-false value
  render identically: no chip).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate and open (click) a `range_trade` signal known to predate this iteration
3. Read the geometry line

**Expected Result:**
- The geometry line renders with the SAME fields it always has (`range_width_mbr`, both zone touch
  counts, `slots_to_break`, and — if true for that record — `crossed midrange` /
  `absorption_bar_present`)
- No `· turned at midrange` text appears
- No error, no "undefined" or "null" text leaking into the rendered line, no crash

---

### UT-05 — Session date field validation still works (validation / regression)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Playbook Signals

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field (`data-testid="desk-playbook-date-input"`), type an
   invalid value: `not-a-date`

**Expected Result:**
- The input's border turns amber (`aria-invalid="true"`)
- A validation message appears at `data-testid="desk-playbook-date-error"` (exact wording is
  pre-existing behavior, unchanged by this iteration)
- The Playbook Signals table/detail area does not attempt to render data for the invalid input
- This confirms the pre-existing date-input mechanics still function correctly after this
  iteration's edits to the surrounding file

---

### UT-06 — Kept `/desk` sections unaffected (regression — ties to the J-10 fixture fix)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to load, then scroll through the full page from top to bottom

**Expected Result:**
- The following section headings are all present, in this relative order, regardless of whether
  any desk screen has ever been computed: "Top-up Runs", "Index Reconciliation", "Screen Runs",
  "Playbook Signals", "Backscan", "Playbook Evidence"
- None of these sections show an error state or a blank/broken layout
- This directly exercises the same three headings ("Top-up Runs", "Index Reconciliation", "Screen
  Runs") that `runs/goal-session-playbook/journey-scripts/J-10.json` steps 6-8 now assert instead
  of the old, silently-vacuous hash string

---

### UT-07 — New chip text reads as a neutral disclosure, not advice (UX / content sanity)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` → Playbook Signals → `range_trade` geometry line

**Preconditions:**
- Complete UT-02 or UT-03 first so the detail panel with the geometry line is open

**Steps:**
1. With a `range_trade` signal's detail panel open, read the full geometry line text aloud
   (including whichever of `· crossed midrange` / `· turned at midrange` / `· absorption bar
   present` are present)

**Expected Result:**
- The text states an observed fact about the bars only ("turned at midrange") — it contains no
  imperative, advice, prediction, probability, or significance language ("should", "buy", "sell",
  "likely", "expect", "edge")
- This matches `tests/test_copy_discipline.py`'s automated sweep, which the dev handoff reports as
  30/30 passing including this exact new string

---

### UT-08 — Playbook Signals section is where it has always been (ux / discoverability)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` navigation

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301` (Cockpit)
2. Click "Desk" in the top navigation bar (`data-testid="nav-link"`, `data-label="Desk"`)
3. Scroll down past the "Provenance" section

**Expected Result:**
- Clicking "Desk" navigates to `http://localhost:3301/desk` and highlights the "Desk" nav link as
  active
- The "Playbook Signals" section appears directly below "Provenance" and directly above
  "Backscan" — the same position it has held since goal-playbook-iter-3; this iteration added no
  new section and did not move this one

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | `range_trade` signal renders new field when `false` | happy-path | P1 | `/desk` → Playbook Signals |
| UT-03 | `range_trade` signal renders new field when `true` (blocked) | happy-path | P1 | `/desk` → Playbook Signals |
| UT-04 | Pre-iteration `range_trade` signal shows no chip, no error | regression | P1 | `/desk` → Playbook Signals |
| UT-05 | Session date field validation still works | validation | P2 | `/desk` → Playbook Signals |
| UT-06 | Kept `/desk` sections unaffected | regression | P1 | `/desk` |
| UT-07 | New chip text is neutral, non-advisory | ux | P2 | `/desk` → Playbook Signals |
| UT-08 | Playbook Signals section still in its usual place | ux | P3 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-03 is P1 by category (it is the
core new capability) but is documented as currently blocked pending a live qualifying example —
see its Preconditions. Its blocked status should not by itself be read as a FAIL of this iteration;
UT-02 and the backend unit test cited within it are what currently substitute as the correctness
proof for the `true` branch.
