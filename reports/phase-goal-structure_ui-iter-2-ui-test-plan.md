# Phase goal-structure_ui-iter-2 — UI Test Plan

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Scope & How to Read This Plan

This iteration is purely additive to the existing `/structure` page: a new, read-only **Registry**
section (J-02: two strategy cards + a champion badge) plus an **independent re-verification** of a
prior iteration's chart empty-state fix (J-01 closure). No other route changed. This plan covers
every row of `reports/phase-goal-structure_ui-iter-2-ui-surface-map.md` with 15 test cases across
smoke, happy-path, error, regression, and ux checks.

- **No `validation`-type test case exists in this plan.** The skill's rule is "one test per form
  that was added or changed" — the Registry section has no form/button/input (read-only, per the
  spec's own "New user actions: none"), and the pre-existing Symbol/As-of/Load form was not changed
  this iteration. Its existing validation behavior (a malformed `as_of`) is still exercised, but as
  a **regression** case (UT-11), not a validation case, since it's old behavior being re-confirmed.
- **Two `regression`-type cases (UT-06, UT-07) are elevated to Priority P1**, above the skill's
  default P2/P3 tier for regression tests. Rationale: UT-06 is the exact, named re-verification the
  phase spec requires to close journey J-01 — a prior iteration's browser-QA lane never re-ran after
  an in-tree fix, causing a `CLOSURE-FAIL`. A FAIL on UT-06 this time is blocking, not informational.
- **Out of scope, do not report as missing:** any backtest-comparison UI (J-03, deferred to a later
  iteration), any control to change the champion, and any client-side computation — this section is
  verbatim-read-only by design.
- **Styling note:** section headings inside the page's bordered panels ("Registry", "Confluence
  zones", "Price chart — S/R levels") are rendered in small caps by the shared `Panel` component
  (e.g. the text node is "Registry" but it displays as "REGISTRY"). This document refers to headings
  by their underlying text; either casing is acceptable evidence of the same heading.

---

## Shared Setup — Seeded Bar Fixture (covers UT-06, UT-07, UT-10 only)

Three test cases below need symbol `PG` to have a recorded bar series. **As of this plan being
written, `apps/backend/.data/bars/` is empty**, so `PG` currently has none — this setup step is
required before UT-06/UT-07/UT-10, and it is a one-time file copy, not a UI action:

1. Copy both files from `apps/backend/tests/fixtures/bars/` —
   `009371c9c02f46338bafef47148f92ad.json` and `b08b1a55ef4a45b2a1adad8fa82ccdf1.json` — into
   `apps/backend/.data/bars/` (create the folder if it does not exist).
2. Confirm the backend picked it up: `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z`
   should report `"no_bar_series_for_symbol": false` (restart the backend if it does not).
3. Run UT-06, UT-07, and UT-10 (all three reuse this same seeded data — no re-seeding between them).
4. **Cleanup:** delete the two copied files from `apps/backend/.data/bars/` afterward, restoring the
   default keyless state. Re-run UT-09 to confirm `PG` reverts to "No bar series recorded for PG." —
   leave no test data behind, matching this project's established precedent (see the iter-1 dev and
   audit handoffs, which followed the identical seed → verify → remove cycle).

All other test cases below need **no seeding** — they run against the environment's current default
(empty) bar-series state.

---

## Test Cases

<!-- Test IDs use UT-XX prefix. Ordered P1 first (must-pass), then P2, then P3. -->

### P1 — Must Pass

---

### UT-01 — Structure page loads with the Registry section visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301
- Backend running and reachable
- No login exists in this app — nothing to sign in with

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to finish loading (no click needed)
3. Open the browser DevTools console and check for red error messages

**Expected Result:**
- The heading "Structure" is visible at the top of the page
- The subtitle "Deterministic support/resistance levels and A/B/C confluence zones for a chosen
  symbol and as-of time." is visible
- A bordered form is visible containing a "Symbol" field, an "As-of (UTC, ISO-8601)" field, and a
  "Load" button
- Below the form, the Levels & Zones area shows its idle message: "Choose a symbol and an as-of
  time, then Load, to see its S/R levels and confluence zones."
- Within a few seconds and with no click, a "Registry" section heading appears further down the
  page, containing a "Champion" box and two strategy cards
- No blank white screen, no Next.js error overlay, no red text in the console

---

### UT-02 — Registry section populates independent of the Load button (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- Fresh page load (Symbol and As-of fields are both empty)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Do NOT type into the "Symbol" field, do NOT type into the "As-of (UTC, ISO-8601)" field, do NOT
   click "Load"
3. Wait 3 seconds
4. Look at the Levels & Zones area (above the Registry section)
5. Look at the Registry section (below it)

**Expected Result:**
- The Levels & Zones area still shows its idle message "Choose a symbol and an as-of time, then
  Load, to see its S/R levels and confluence zones." — unchanged, because Load was never clicked
- The Registry section is nonetheless fully populated: a "Champion" box showing "v1" / "default",
  followed by two cards headed "v1" and "structure_tape"
- This confirms the Registry section fetches and renders on page mount, independent of the Levels &
  Zones "Load" button

---

### UT-03 — `v1` strategy card shows correct verbatim entry/exit fields, no `reward_target` row (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:** same as UT-01 (fresh load, backend reachable)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the Registry section to appear
3. Find the card whose heading reads "v1" (the first of the two cards)
4. Read every labeled row inside that card

**Expected Result** — the "v1" card shows exactly these label → value pairs, and no others:
- "entry rule" → `state_native_sustained_premise`
- "r_stop" → `synthetic_invalidation_at_arm`
- "state_flip" → `opposing_control_state`
- "horizon (seconds)" → `120`
- "dataset_end" → `forced_exit_at_last_recorded_price`
- **No "reward_target" row appears anywhere on this card** — `v1` genuinely has no reward target;
  this is a correct, honest omission, not a missing-data bug
- Below the fields, a caption reads: "Exit precedence: r_stop → reward_target → state_flip →
  horizon (dataset_end forces a close at stream end)."
- No class-scaled tables ("stop (bps by class)", "reward target (R-multiple by class)", "size
  (multiple by class)") appear on this card

---

### UT-04 — `structure_tape` strategy card shows correct verbatim fields plus three class-scaled tables (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:** same as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the Registry section to appear
3. Find the card whose heading reads "structure_tape" (the second card, directly below "v1")
4. Read every labeled row and every table inside that card

**Expected Result** — the "structure_tape" card shows:
- "entry rule" → `structure_level_tape_confirmation`
- "r_stop" → `class_scaled_invalidation_beyond_level`
- "reward_target" → `class_r_multiple_bounded_by_next_opposing_level` (present here, unlike the
  `v1` card)
- "state_flip" → `opposing_control_state`
- "horizon (seconds)" → `120`
- "dataset_end" → `forced_exit_at_last_recorded_price`
- The same exit-precedence caption as the `v1` card
- A table titled "stop (bps by class)" with three rows: A → `1`, B → `5`, C → `10`
- A table titled "reward target (R-multiple by class)" with three rows: A → `3`, B → `2`, C → `1`
- A table titled "size (multiple by class)" with three rows: A → `2`, B → `1`, C → `0.5`
- **Note:** "horizon (seconds)" (`120`) and "dataset_end" are legitimately identical between the
  `v1` and `structure_tape` cards — both read one shared config field. This is expected, not a
  copy-paste defect; do not report it as a bug.

---

### UT-05 — Champion badge shows `v1`/`default` with a confirmed cross-check (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:** same as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the Registry section to appear
3. Find the "Champion" box at the top of the Registry section (above the two strategy cards)
4. Read the "strategy" and "profile" values
5. Read the small caption directly below those two values

**Expected Result:**
- "strategy" reads `v1`
- "profile" reads `default`
- The caption reads exactly: "Confirmed identical to the champion served by GET
  /research/profiles — one store pointer, two read views."
- *(Optional deeper check for a technical tester — not required for pass/fail: open a second tab
  to this environment's backend `/research/profiles` endpoint — e.g.
  `http://localhost:8301/research/profiles`, or whatever port `NEXT_PUBLIC_API_URL`/
  `NEXT_PUBLIC_API_BASE` is set to — and confirm its own `champion` field also reads
  `{"strategy_id": "v1", "profile": "default"}`, byte-for-byte matching the badge.)*

---

### UT-06 — J-01 closure: levels-but-zero-candles state shows the honest hint, not a blank chart (regression, elevated P1)

**Type:** regression
**Priority:** P1 — **elevated from the default P2/P3 regression tier.** This is the iteration's
named closure target for journey J-01 (see the "Shared Setup" section above for why the default
P1/P2 table does not apply here). Treat a FAIL as blocking.
**Surface:** `/structure` (`StructureChart` component)

**Preconditions:**
- The shared PG bar fixture (see "Shared Setup" above) is seeded into `apps/backend/.data/bars/`
- Backend and frontend both running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the "Symbol" field
3. Type `2026-06-02T12:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button
5. Wait for the page to finish loading
6. Look at the "Price chart — S/R levels" panel

**Expected Result:**
- The chart panel is **NOT** a blank/empty box
- The text "No candles to draw at this as-of time." is clearly visible, centered over the chart area
- Below the chart, the caption reads: "Candles: 1h series (0 of 9 recorded bars, as of the query
  time). Level lines span every recorded timeframe."
- The "Confluence zones" panel below shows its own distinct message: "No qualifying confluence zone
  among these levels." with detail "Levels exist, but none cluster closely enough across timeframes
  to form a zone." (3 levels exist at this as-of time — 138.86, 140.28, 141.82 — but none cluster
  into a zone)
- **Critically: the "No candles…" text must be legible — not painted underneath/behind the chart's
  dark canvas.** This exact defect (hint text occluded by the chart canvas) was fixed in a prior
  iteration; this test independently re-confirms the fix still holds on the current code, live in
  the browser (not by reading the source).

---

### UT-07 — J-01 regression: populated levels/zones render correctly alongside the new Registry section (regression, elevated P1)

**Type:** regression
**Priority:** P1 — elevated (confirms the new Registry section introduced no regression to the
pre-existing J-01 surface)
**Surface:** `/structure`

**Preconditions:**
- Same seeded fixture as UT-06 (already copied into `apps/backend/.data/bars/`)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the "Symbol" field
3. Type `2026-06-09T21:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button
5. Wait for the page to finish loading
6. Look at the "Price chart — S/R levels" panel, then the "Confluence zones" panel below it, then
   scroll down to the Registry section

**Expected Result:**
- The chart shows visible candles plus multiple dashed horizontal level lines (20 levels total per
  the API — no need to count every line individually)
- The caption below the chart reads: "Candles: 1h series (9 of 9 recorded bars, as of the query
  time). Level lines span every recorded timeframe."
- The "Confluence zones" panel lists exactly **6 zone cards**, with class badges reading, top to
  bottom: "Class C", "Class C", "Class C", "Class C", "Class C", "Class B"
- No "No candles to draw…" hint appears anywhere (that only appears in UT-06's zero-candle case)
- Scrolling further down, the Registry section (Champion + `v1` + `structure_tape` cards) still
  renders exactly as in UT-02 through UT-05 — no visual overlap, no layout break, no missing section
- No JavaScript console errors

**After UT-07, follow the "Cleanup" step in the Shared Setup section above (once UT-10 is also
done) to remove the seeded fixture.**

---

### P2 — Important, Non-Blocking

---

### UT-08 — Registry-unavailable honest state when the backend is stopped (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301
- Backend process is stopped (or otherwise made to return a non-200 response on
  `GET /research/strategies`) — a setup step for a technical tester, not a UI click

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3301/structure` (or refresh if already
   on the page)
2. Wait a few seconds for the fetch to fail
3. Look at the area where the Registry section normally appears

**Expected Result:**
- An amber-bordered panel appears in place of the Registry section, reading: "Backend unreachable —
  is the API running?"
- A second line below it reads: "Nothing cached and nothing fabricated is shown in its place."
- No strategy cards, no Champion box, and no hardcoded `v1`/`default` values appear anywhere on the
  page
- The Levels & Zones section above it separately shows its own degraded message (each section
  reports its own honest failure independently — neither fakes success because the other happened
  to already have data cached)
- Restarting the backend and refreshing the page brings back the normal populated Registry section
  (Champion + two cards)

---

### UT-09 — No-bar-series-for-symbol honest state still renders correctly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running
- **No setup/seeding required** — this is the environment's current default state (no bar series
  recorded for `PG`, or any symbol, unless the Shared Setup fixture is currently seeded — run this
  test either before seeding, or after the UT-06/07/10 cleanup step)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the "Symbol" field
3. Type `2026-06-09T21:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click "Load"

**Expected Result:**
- The Levels & Zones area shows "No bar series recorded for PG." as its heading message
- Below it, the detail text reads: "Recording historical bars needs provider credentials."
- No chart, no level lines, no zones table appear

---

### UT-10 — Series-but-no-levels honest state still renders correctly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Same seeded fixture as UT-06/UT-07

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the "Symbol" field
3. Type `2026-05-01T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click "Load"

**Expected Result:**
- The Levels & Zones area shows "No levels found for PG as of 2026-05-01T00:00:00Z." as its heading
  message
- Below it, the detail text reads: "A bar series is recorded, but nothing is derivable at this
  as-of time."
- No chart, no level lines, no zones table appear (this message is distinct from UT-09's — this one
  confirms bars DO exist, just no levels can be derived yet)
- This is the last of the three seeded-fixture tests — proceed to the Cleanup step in Shared Setup

---

### UT-11 — Malformed `as_of` input still folds into the shared degraded state (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running; no fixture seeding required (this fails validation before any data
  lookup happens)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the "Symbol" field
3. Type `not-a-date` into the "As-of (UTC, ISO-8601)" field
4. Click "Load"

**Expected Result:**
- An amber-bordered degraded panel appears in the Levels & Zones area
- The message reads: "as_of must be an ISO date-time" (the backend's own validation message, shown
  verbatim)
- Below it, "Nothing cached and nothing fabricated is shown in its place." is visible
- No chart, no crash, no blank page

---

### UT-12 — `/performance` champion summary unaffected by `/structure`'s reused testids (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/performance`

**Preconditions:**
- Frontend and backend running
- Complete UT-05 first (so you know what the `/structure` Champion box looks like, for comparison)

**Steps:**
1. Navigate directly to `http://localhost:3301/performance` (type the URL — do not click a link
   from `/structure`, to rule out any leftover client state)
2. Wait for the page to load
3. Look at the "Champion" box in the right-hand column

**Expected Result:**
- The Performance page's own Champion box shows "strategy" → `v1` and "profile" → `default`, exactly
  as before this phase
- A "Profile registry" list appears below it (e.g. a row for the `default` profile marked "frozen"
  and "default")
- The PnL ledger on the left side of the page still renders normally
- Nothing about the new `/structure` Registry section visually leaks onto this page, and nothing
  here changed as a result of `/structure`'s changes — `/structure` and `/performance` deliberately
  reuse the exact same testid strings (`champion-summary`/`champion-strategy`/`champion-profile`)
  on two different components; this test confirms that reuse causes no collision

---

### P3 — Informational

---

### UT-13 — Registry-loading placeholder appears briefly during fetch (smoke, informational)

**Type:** smoke
**Priority:** P3 — **lowered from the skill's default P1 for smoke tests.** This exercises a
sub-second transient loading state that is easy to miss without throttling; a miss here is
informational, not a blocking failure.
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running
- Browser DevTools open, Network tab set to a throttled speed (e.g. Chrome's "Slow 4G" preset)

**Steps:**
1. With network throttling enabled, hard-reload `http://localhost:3301/structure`
   (Ctrl+Shift+R / Cmd+Shift+R)
2. Immediately look at the area below the Levels & Zones section, before the Registry section
   finishes loading

**Expected Result:**
- A pulsing gray skeleton placeholder (three animated bars) appears briefly where the Registry
  section will be
- Within a few seconds, it is replaced by the populated Champion box and the two strategy cards
- A permanently-stuck skeleton, or a crash, is the only failure worth reporting here — simply not
  catching the brief flash (e.g. on a fast connection) is not a defect

---

### UT-14 — Registry section is discoverable within one click from Home (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / `/`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Look at the top navigation bar
3. Click "Structure"
4. Scroll down past the Levels & Zones section

**Expected Result:**
- The top navigation bar shows exactly 5 links: "Cockpit", "Journal", "Studies", "Performance",
  "Structure"
- Clicking "Structure" navigates to `http://localhost:3301/structure` in a single click
- The Registry section is visible after scrolling down — no second click, no hidden menu, no
  separate URL was needed to find it
- The section's heading is a clear, self-explanatory label ("Registry"), not a cryptic internal name

---

### UT-15 — Registry copy honestly confirms read-only, no invented controls (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the Registry section to appear
3. Read the small muted line directly below the "Registry" heading, above the Champion box
4. Look for any buttons, input fields, checkboxes, or links inside the Registry section (Champion
   box + both strategy cards)

**Expected Result:**
- The line reads: "Read-only: every strategy field and the champion below are read verbatim from
  GET /research/strategies — nothing here is recomputed in the browser."
- No button, input, checkbox, dropdown, or link exists anywhere inside the Registry section — it is
  pure display, matching the spec's "New user actions: none"
- Nothing in the Registry section's copy uses trading/advice language (no "buy", "sell",
  "recommended", "should enter") — only descriptive parameter names and values

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Structure page loads with Registry visible | smoke | P1 | `/structure` |
| UT-02 | Registry populates independent of Load button | happy-path | P1 | `/structure` |
| UT-03 | `v1` card verbatim fields, no `reward_target` | happy-path | P1 | `/structure` |
| UT-04 | `structure_tape` card + 3 class-scaled tables | happy-path | P1 | `/structure` |
| UT-05 | Champion badge `v1`/`default` + cross-check | happy-path | P1 | `/structure` |
| UT-06 | J-01 closure: zero-candle honest hint (not blank) | regression | **P1 (elevated)** | `/structure` |
| UT-07 | J-01 regression: populated chart + Registry coexist | regression | **P1 (elevated)** | `/structure` |
| UT-08 | Registry-unavailable when backend stopped | error | P2 | `/structure` |
| UT-09 | No-bar-series honest state still works | regression | P2 | `/structure` |
| UT-10 | Series-but-no-levels honest state still works | regression | P2 | `/structure` |
| UT-11 | Malformed `as_of` still folds into degraded state | regression | P2 | `/structure` |
| UT-12 | `/performance` champion unaffected by testid reuse | regression | P2 | `/performance` |
| UT-13 | Registry-loading skeleton appears briefly | smoke | P3 (lowered) | `/structure` |
| UT-14 | Registry discoverable in 1 click from Home | ux | P3 | nav / `/` |
| UT-15 | Registry copy is honest read-only, no invented controls | ux | P3 | `/structure` |

**All P1 tests (UT-01 through UT-07) must pass for browser QA verdict to be PASS.** UT-06 and UT-07
carry extra weight: they are this iteration's specific mechanism for closing journey J-01, which was
left `partial` (not `passing`) after the prior iteration's browser-QA lane never independently
re-ran a fix that was applied in-tree.
