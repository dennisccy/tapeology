# Phase goal-desk-iter-11 — UI Test Plan

**Phase:** goal-desk-iter-11 (Era B, Journey J-09 — durable top-up run log)
**Date:** 2026-07-28
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Scope

One surface changed: `/desk`. Every test case below targets the new **"Top-up Runs"** section
(`<section aria-label="Top-up runs">`, rendered as the LAST section on the page, wrapping
`<Panel title="Top-up Runs">`) fed by the new `GET /research/desk/topup/runs` endpoint. No new
page, no new form, no new button — this iteration adds one read-only panel next to the page's
existing Provenance / Briefing / Skipped Members / Screen History / Run Screen-Top-up sections,
all of which stay unchanged and are covered here only as regression checks (UT-08).

Verified against source before writing this plan (`apps/frontend/app/desk/page.tsx`): the section
renders unconditionally, as a sibling AFTER the screen-state ternary closes (lines 1245–1280) — it
is never nested inside the "screen not computed" branch, so its own honest state is independent of
whether a screen has ever been run. The dev handoff (`docs/handoffs/goal-desk-iter-11-dev.md`)
confirms the AMBIENT backend (the one this project normally runs at :8301/:3301) has never run a
J-09-aware top-up, so `GET /research/desk/topup/runs` on it today genuinely returns
`{"runs": [], "latest": null}` — UT-02's empty-state check is exercisable live, right now, with no
setup. The populated-state checks (UT-03 through UT-06, UT-08 through UT-10) require at least one
completed top-up run with a deliberately induced failure and a deliberately cancelled run — per the
phase spec's own NOTES ("never a live vendor call" for the induced failure), these are built on a
**fixture-scoped rig**, not the live vendor, using this project's own established technique (see
Test Data Setup below).

---

## Test Data Setup (shared fixture — build once, use across UT-03 through UT-10)

Stand up a scoped backend the same way `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`
does (copy `apps/backend/.data/` into a fresh root — e.g. `${TMPDIR:-/tmp}/desk-iter11-scoped-qa`
— and serve it on port 8301; pair with
`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh` so the frontend
at `http://localhost:3301` points at it). That copied `.data/` already carries a registered
universe snapshot (e.g. `universe-2026-07-25-49b33fa31680`) and already-cached bars for most
members, so "reused" outcomes resolve instantly with no network call.

Before starting the server, record three runs into that scoped root's own top-up run log, in this
exact order (each is a full backend-level trigger — either `DeskTopupComputeManager.trigger()` or
the CLI — against the SAME scoped `.data/` root; check the target store for a pre-existing run
record first per the iter-10 lesson before assuming a clean start):

- **Checkpoint 1** — one ordinary run, no induced failure (mostly/all `"reused"` outcomes since
  bars are already cached). Result: `state: "done"`, `pairs_attempted == pairs_total`.
- **Checkpoint 2** — one run with a cancel signaled mid-walk (the same technique
  `test_desk_topup_compute.py`'s existing cancelled-run test already uses). Result:
  `state: "cancelled"`, `pairs_attempted < pairs_total`.
- **Checkpoint 3** — one run with exactly one pair's fetch made to fail via a monkeypatched
  adapter double that fails on exactly one call (the existing
  `_NthCallFailsAdapter`/`NoDataForWindow("no data for that window")` technique
  `test_desk_topup_compute.py`'s
  `test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_continues` already
  uses). Result: `state: "done"`, `pairs_attempted == pairs_total`, exactly one `outcomes` entry
  with `outcome: "failed"` and `detail` containing the verbatim substring `no data for that
  window`.

After Checkpoint 3, `GET /research/desk/topup/runs` should report a `runs` list with 3 entries and
a `latest` whose `outcomes` carry the one failed pair. Perform Checkpoint 3 by actually clicking
the "Top-up" button in the browser at `http://localhost:3301/desk` (with the scoped backend's
adapter dependency monkeypatched to the failing double) rather than by a script, so the same setup
step also serves as UT-07's auto-refresh proof.

Run IDs follow the pattern `topup-<YYYY-MM-DD>-<12 hex chars>` (e.g.
`topup-2026-07-28-a1b2c3d4e5f6`) — illustrative; the exact hex suffix and exact
symbol/timeframe pair chosen to fail will differ by run. Read the actual values rendered on screen
rather than expecting an exact literal match to the examples in this document.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` shows the Top-up Runs section as the last element, independent of screen state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend reachable at `http://localhost:3301`; backend reachable.
- No specific top-up-run state required — this test checks structural presence, not content.

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Wait for the gray pulsing loading skeletons to disappear.
3. Scroll to the very bottom of the page.
4. Read the section heading of the LAST panel on the page.
5. Open browser DevTools (F12) → Console tab; check for red error entries logged during load.
6. Stop the backend process, then reload `http://localhost:3301/desk` (or use DevTools' "Offline"
   network throttling instead of actually stopping the process).
7. Restart the backend and reload the page once more to confirm it returns to normal.

**Expected Result:**
- Step 4: the last panel's heading reads exactly "Top-up Runs" (`data-testid="desk-topup-runs-*"`
  present in the surrounding DOM) — it appears below every other section on the page (Provenance /
  Briefing / Skipped Members / Screen History / Run Screen-Top-up controls, or the amber "Desk
  screen not computed yet." panel if no screen exists yet) in all cases.
- Step 5: no red console errors during the normal load.
- Step 6: with the backend unreachable, BOTH the screen area and the "Top-up Runs" panel
  independently show their own amber panel reading "Backend unreachable — is the API running?"
  (`data-testid="desk-screen-unavailable"` and `data-testid="desk-topup-runs-unavailable"`) — the
  page does not blank out, crash, or show only one of the two failures while silently omitting the
  other.
- Step 7: after the backend returns, both sections recover to their normal content on reload with
  no leftover error banners.

---

### UT-02 — Honest empty state before any run; the GET never triggers a compute (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- A backend with zero top-up runs ever recorded (true on the live/ambient instance today, per the
  dev handoff — or Checkpoint 0 of the scoped rig, before Checkpoint 1 is recorded).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Scroll to the "Top-up Runs" section at the bottom of the page.
3. Read the panel's contents.
4. Open DevTools → Network tab, filter for `topup`, then reload the page 3 times in a row.
5. Inspect the captured requests.

**Expected Result:**
- The panel shows exactly the text "No top-up runs recorded yet." and zero table rows — no blank
  space, no spinner stuck forever, no raw JSON, no "undefined".
- Step 5: every captured request to `/research/desk/topup/runs` is a `GET` (never a `POST`); no
  request to `/research/desk/topup/compute` with method `POST` appears as a result of merely
  loading or reloading the page. `curl -s http://localhost:8301/research/desk/topup/compute`
  (or the equivalent Network-tab entry for that path) still reads `null` after all 3 reloads.

---

### UT-03 — Populated Top-up Runs table lists every recorded run with correct columns (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The scoped rig at Checkpoint 3 (3 runs recorded: ordinary, cancelled, then one-failed-pair) — see
  Test Data Setup above.

**Steps:**
1. Navigate to `http://localhost:3301/desk` (or reload if already open from the setup step).
2. Scroll to the "Top-up Runs" section.
3. Count the number of rows in the table.
4. Read the header row left to right.
5. Read each row's 5 cells left to right.

**Expected Result:**
- Step 3: exactly 3 rows — one per recorded run (Checkpoints 1, 2, and 3), in reverse-chronological
  or chronological order (whichever the backend returns; note which it is, but either order is a
  PASS as long as all 3 are present).
- Step 4: the header row reads exactly, left to right: `date`, `run`, `state`,
  `attempted / total`, `universe snapshot`.
- Step 5: every row shows a `YYYY-MM-DD` date, a non-empty run id string starting with `topup-`, a
  state of exactly `done` or `cancelled` (never blank, never `running`, never a raw enum like
  `DONE`), an "`N` / `M`" pair count, and a universe snapshot id string (not a blank dash, since
  this rig has a registered universe).
- Checkpoint 2's row (the cancelled one) shows a strictly smaller left number than right number in
  its "attempted / total" cell (e.g. "6 / 101") even though it is NOT the latest row — proving the
  table's own per-row summary discloses incompleteness on every row, not only the latest one.
- No row is missing, duplicated, or silently merged with another.

---

### UT-04 — Latest run detail block shows correct attempted/total and per-outcome counts (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Same as UT-03 (scoped rig at Checkpoint 3; latest run = the one-failed-pair run).

**Steps:**
1. On `/desk`, scroll just below the Top-up Runs table.
2. Read the "Latest run — `<date>` · `<id>`" heading.
3. Read the line of stats beneath it.
4. Add the three per-outcome counts together by hand.

**Expected Result:**
- The heading's date and id match the table's own last-recorded (Checkpoint 3) row exactly.
- The stats line contains three pieces of text: `state: done`, "`N` of `M` pairs attempted" (where
  `N` equals `M`, since Checkpoint 3 completed every pair), and a counts string reading
  "`R` reused · `F` fetched · `X` failed" (e.g. "78 reused · 22 fetched · 1 failed").
- Step 4: `R + F + X` equals the `N` from the "pairs attempted" text exactly (no pair double-counted
  or missing from the sum).
- `X` (the failed count) is exactly 1, matching the single induced failure from Checkpoint 3.

---

### UT-05 — A failed pair's real error text is shown verbatim and fully legible (error)

**Type:** error
**Priority:** P1 *(elevated above this category's default P2 — this is a named Definition-of-Done
line item and the specific screenshot requirement TC-13 in the functional test plan gates on: "the
failed pair's detail all legible in one image." A truncated or hidden error string here is exactly
the defect this iteration exists to prevent — silently losing a real vendor failure's detail the
way the in-flight compute snapshot used to.)*
**Surface:** `/desk`

**Preconditions:**
- Same as UT-03/UT-04 (scoped rig at Checkpoint 3, whose one failed pair was produced via the
  `NoDataForWindow("no data for that window")` monkeypatch technique).

**Steps:**
1. Below the "Latest run" stats line, locate the "Failed pairs (`N`)" heading.
2. Read `N`.
3. Read the one (or more) list item(s) beneath it.
4. Zoom in / inspect the text to confirm it is not cut off, wrapped behind another element, or
   truncated with an ellipsis.
5. Take a full-page or section screenshot capturing the table, the stats line, and this failed-pair
   list together in one image.

**Expected Result:**
- `N` equals 1 (matching UT-04's failed count).
- The one list item reads "`<SYMBOL>` `<timeframe>` — `<verbatim detail text>`" (e.g.
  "AAPL 1h — no data for that window") — the detail segment contains the exact substring
  `no data for that window` (the literal message the induced `NoDataForWindow` exception carried),
  never a generic "An error occurred" placeholder, never truncated with "…", never blank.
- The symbol and timeframe named match the actual pair the setup step monkeypatched to fail.
- Step 5's screenshot shows the full detail text legibly in one frame with no horizontal clipping —
  save it as evidence (matches the functional test plan's
  `reports/qa/goal-desk-iter-11-evidence/TC-13-populated-topup-runs.png`, or a distinctly-named
  file if captured separately for this UI test plan).

---

### UT-06 — Unreached-pairs note appears only when honestly true, with the correct count (error)

**Type:** error
**Priority:** P1 *(elevated for the same reason as UT-05 — this and UT-05 are named together in
the same Definition-of-Done bullet and the same anti-fabrication concern: a cancelled run's
disclosure must never overstate OR understate what was actually reached.)*
**Surface:** `/desk`

**Preconditions:**
- **Part A (positive case):** the scoped rig paused right after Checkpoint 2 (cancelled run is the
  latest recorded run at that point — before Checkpoint 3 is added).
- **Part B (negative case):** the scoped rig at Checkpoint 3 (from UT-03 — latest run completed
  every pair, so nothing was left unreached).

**Steps (Part A):**
1. With the scoped rig stopped right after Checkpoint 2, navigate to `/desk` and scroll to the
   "Latest run" detail block.
2. Read the stats line for an amber note.
3. Compare its stated count against `pairs_total - pairs_attempted` read from the table row above
   it.

**Steps (Part B):**
4. Continue the rig to Checkpoint 3 (or reuse UT-03's already-built Checkpoint-3 state).
5. Reload `/desk` and read the "Latest run" detail block again.

**Expected Result:**
- Part A: an amber note (`data-testid="desk-topup-run-latest-unreached"`) reads
  "`X` pairs not reached" (or "`1` pair not reached" if X is exactly 1 — singular/plural grammar
  must match), where `X` equals `pairs_total - pairs_attempted` exactly, computed from the SAME
  numbers shown in the "`N` of `M` pairs attempted" text just before it.
- Part B: no amber "pairs not reached" note appears anywhere in the block — not even a "0 pairs not
  reached" line. The element is entirely absent from the DOM, not merely hidden/blank, since
  Checkpoint 3's run reached every pair.

---

### UT-07 — Top-up Runs panel updates itself when a run finishes, with no manual page reload (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` open and idle in the browser, showing Checkpoints 1–2 already recorded (2 rows in the
  table) — i.e., performed as part of building Checkpoint 3 in the Test Data Setup above.

**Steps:**
1. With `/desk` already open (do NOT reload), scroll so both the "Top-up" button and the "Top-up
   Runs" table are visible at once (or use two browser windows/a tall viewport).
2. Click the "Top-up" button.
3. Watch the button's label change to "Topping up…" with a progress line beneath it.
4. Let the run reach its terminal state (button label returns to "Top-up" or "Retry Top-up").
5. Without pressing F5 or clicking anything else, watch the Top-up Runs table for up to 2 seconds
   after step 4.

**Expected Result:**
- Step 5: within roughly one poll tick (~700ms, so allow up to ~2 seconds of margin) after the run
  reaches its terminal state, the table's row count increases by exactly one, and the "Latest run"
  detail block's heading now references the JUST-FINISHED run's own id (not the previous latest) —
  all without any manual reload or extra click by the tester.
- No flash of the empty state or a loading skeleton replacing already-visible content during this
  update — the previously-shown rows stay on screen the whole time; only the new row and the detail
  block's content change.

---

### UT-08 — Every pre-existing `/desk` section still renders and behaves unchanged (regression)

**Type:** regression
**Priority:** P1 *(elevated — `/desk` is the shared home of three already-shipped journeys,
J-04/J-05/J-08; this iteration adds a 4th mount-time GET and extends an existing poll's `useEffect`,
both realistic places to accidentally break the page's other data loads. "Required-still-passing
journeys J-01–J-08 remain green" is an explicit Definition-of-Done line.)*
**Surface:** `/desk`

**Preconditions:**
- Scoped rig at Checkpoint 3 (a fully populated page: a screen result, screen history, and now 3
  top-up runs).

**Steps:**
1. Navigate to `/desk`.
2. Read the page heading.
3. Confirm the "Provenance" panel shows Universe snapshot / Screen date / As of / Config
   fingerprint / Bar-store signature values (not blank/dash where data exists).
4. Confirm the "Briefing" panel's ranked-rows table renders with its usual columns
   (`symbol, side, class, distance, score, coverage, tick evidence`, plus `basis` if the rig
   includes iter-9's data).
5. Confirm the "Skipped Members" panel renders (or its own honest empty state if nothing was
   skipped).
6. Click a row in "Screen History" other than the currently-viewed one; confirm the
   "Viewing the recorded screen for … — not the latest." banner appears; click "Latest" to return.
7. Confirm the "Run Screen" button is present, reads "Run Screen" (not stuck on "Computing…"), and
   is clickable.

**Expected Result:**
- All five pre-existing sections (Provenance, Briefing, Skipped Members, Screen History, Run
  Screen/Top-up controls) render with the same content, layout, and behavior they had before this
  iteration — no visual overlap with the new Top-up Runs section, no missing data, no JavaScript
  console errors.
- The history drill-through (step 6) still works exactly as it did in the prior iteration: banner
  appears, "Latest" button reverts cleanly.
- Nothing about the new Top-up Runs section interferes with any of the above.

---

### UT-09 — Top-up Runs is discoverable without scrolling tricks or extra clicks (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- None beyond a running frontend; any screen/top-up-run state.

**Steps:**
1. Open a fresh browser tab and navigate directly to `http://localhost:3301/desk` (as a first-time
   visitor would, no prior clicks).
2. Scroll down the page at a normal pace, reading each section heading as it comes into view.
3. Note whether "Top-up Runs" is distinguishable from "Screen History" at a glance.

**Expected Result:**
- The "Top-up Runs" section is reached by ordinary vertical scrolling alone — no toggle, "show
  more," tab, or settings menu is required to reveal it.
- Its heading text ("Top-up Runs") is visually styled identically to every other section heading on
  the page (same uppercase small-caps treatment, same panel border) — it does not look like an
  afterthought or a debug panel bolted on.
- It is clearly a DIFFERENT section from "Screen History" (distinct heading, distinct table columns:
  date/run/state/attempted-total/universe-snapshot vs. Screen History's own date/rows/skipped/
  provenance columns) — a first-time viewer would not confuse the two.

---

### UT-10 — Top-up Runs copy is plain descriptive measurement, never advice or urgency styling (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- Scoped rig at Checkpoint 3 (both a cancelled run's "not reached" note and a failed pair's detail
  visible somewhere in the run history, per UT-05/UT-06).

**Steps:**
1. Read every piece of text in the "Top-up Runs" section, including the empty-state sentence (if
   revisiting Checkpoint 0), the table headers, the "Latest run" stats line, the "pairs not
   reached" note, and the "Failed pairs" list.
2. Note the text color/styling used for the failed-pair detail versus the cancelled run's
   "pairs not reached" note versus an ordinary "done" row.

**Expected Result:**
- No word anywhere in the section reads like advice, a recommendation, or an urgency cue — e.g. no
  "warning", "act now", "danger", "you should", "consider", "opportunity", or similar. Every string
  is a plain factual measurement ("state: cancelled", "3 pairs not reached", "AAPL 1h — no data for
  that window").
- The failed pair's detail text and the "pairs not reached" note both use a restrained styling
  (slate/amber text) consistent with the rest of the page's existing error/cancelled-state styling
  elsewhere on `/desk` (e.g. the Top-up control's own existing "Top-up cancelled — pairs already
  recorded before the cancel stay stored." line) — no flashing, no red "ALERT" banner, no icon
  implying the operator must act.
- `pytest tests/test_copy_discipline.py` is confirmed green in the functional test plan (TC-11) —
  this UX check is the human-eyeball confirmation of the same guarantee, not a duplicate of that
  automated lint.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Section present, last on page, independent failure states | smoke | P1 | `/desk` |
| UT-02 | Honest empty state; GET never triggers a compute | happy-path | P1 | `/desk` |
| UT-03 | Populated table lists every run with correct columns | happy-path | P1 | `/desk` |
| UT-04 | Latest-run detail counts are correct and sum right | happy-path | P1 | `/desk` |
| UT-05 | Failed pair's verbatim detail is legible, untruncated | error | P1 (elevated) | `/desk` |
| UT-06 | Unreached-pairs note correct and honestly absent when 0 | error | P1 (elevated) | `/desk` |
| UT-07 | Panel auto-refreshes on run completion, no reload | happy-path | P2 | `/desk` |
| UT-08 | Every pre-existing `/desk` section unaffected | regression | P1 (elevated) | `/desk` |
| UT-09 | Discoverable with plain scrolling, distinct from history | ux | P3 | `/desk` |
| UT-10 | Copy stays descriptive, no advice/urgency styling | ux | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**

### Coverage notes

- **No validation-type test case.** `/desk` gains no new form or input field this iteration — the
  Top-up Runs section is pure read-only disclosure of outcomes the existing Top-up button already
  produces ("No new interactive control" is explicit OUT OF SCOPE text in both the phase spec and
  the execution plan). The "validation" category applies to form input handling, which does not
  exist on this surface, matching the same coverage note the prior iteration's UI test plan
  (iter-9) recorded for the same reason.
- **UT-05/UT-06 elevated to P1** together because they are named in the SAME Definition-of-Done
  bullet ("every failed pair's detail verbatim plus the honest unreached-pairs count") and share the
  same failure mode this whole journey exists to prevent: a run's real outcome silently
  disappearing or being misrepresented. **UT-08 elevated to P1** because `/desk` is a
  three-journeys-deep shared surface and "J-01–J-08 remain green" is its own Definition-of-Done
  line, independent of J-09's own success.
- **Dynamic/illustrative data notice:** run ids, exact pair counts, and the exact symbol/timeframe
  chosen to fail are illustrative throughout this document. Testers should read the actual values
  rendered on screen rather than expecting a literal match to the examples given — only the
  *shape* (id prefix, count relationships, verbatim-substring presence) is a hard requirement.
- Backend-only assertions already in `reports/qa/goal-desk-iter-11-test-plan.md` (TC-01 through
  TC-11, TC-14, TC-15, TC-16 — byte-identity, checksum/append-only discipline, shared-writer schema
  parity, MCP proxying, suite/fingerprint, golden replay, copy-discipline lint) are intentionally
  not duplicated here; this plan covers only what a human or browser agent observes on screen.
  TC-17 (J-01–J-08 smoke replay) is likewise not re-authored here as manual click-paths — UT-08
  above is this document's own lighter-weight, directly-observable regression check on the same
  risk.
