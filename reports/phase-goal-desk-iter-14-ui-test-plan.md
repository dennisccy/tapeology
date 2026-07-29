# Phase goal-desk-iter-14 — UI Test Plan

**Phase:** goal-desk-iter-14 (Era B, Journey J-10 — coverage-index reconciliation)
**Date:** 2026-07-28
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 — this iteration's own scoped rig, NOT the ambient app (`:3000`/`:8000`)

---

## Scope

One surface changed: `/desk`. J-10 adds a third operator-triggered control, **"Reconcile Index"**
(mirrors the existing "Top-up" button), and a third durable, read-only history section, **"Index
Reconciliation"**, placed immediately after the existing "Top-up runs" section. No new page, no nav
change. Test cases below derive from `reports/phase-goal-desk-iter-14-ui-surface-map.md`'s "Affected
UI Surfaces" table (11 rows, all under `/desk` or its four new backend endpoints), cross-checked
against the actual shipped component code in `runs/goal-desk-iter-14/review-packet.md`'s diff (exact
copy strings, data-testids, and column headers below are taken from that diff, not paraphrased).

---

## Current state of the evidence trail — read before executing anything below

Per `runs/goal-desk-iter-14/status.json` (`current_step: qa_complete`, `qa_passed: true`) and
`reports/qa/goal-desk-iter-14-qa.md` (verdict `PASS`), QA and browser-qa-agent have **already
executed** against this iteration's scoped rig before this plan was written —
`reports/qa/goal-desk-iter-14-evidence/TC-17-empty-reconciliation.png` and
`TC-18-populated-reconciliation.png` both already exist on disk. This plan is written to the same
rigor bar a fresh execution should meet regardless of that prior pass: it is this agent's job
independent of what already ran, a future iteration seeding a fresh rig needs a reusable procedure
not a one-off record, and — most importantly — a direct check of the two already-archived images
surfaced something worth disclosing before anyone treats them as settled:

**Factual observation on the two already-captured PNGs** (checked directly: `file` reports both as
`1400 x 1000, 8-bit/color RGB` — an ordinary viewport screenshot, not a full-page capture). Both
images, as saved, show only the top of the "Briefing" ranked-rows table — rows for BRK-B, DHR, HD,
IBM, NFLX, CRM, AMT, HONA, LOW, LIN, CAT, COST, and more below the fold — a wide, ~100-member
universe, not the single-row AAPL-only universe `docs/handoffs/goal-desk-iter-14-dev.md` describes
deliberately registering for this evidence (`UniverseStore.record(members=["AAPL"], ...)`). Neither
image shows the "Index Reconciliation" section itself (documented as the LAST section on the page)
or a coverage badge in the same frame as that section — the specific "both legible in one
screenshot" shape TC-17/TC-18 and the phase spec's own Visual Requirements both bind to. Separately,
the QA report's own TC-18 row states the served JSON showed `drift_before=88, drift_after=0` — not
the ~7-entry, AAPL/`1d`-only shape the dev handoff's plant action describes, but a size matching the
phase spec's own BACKGROUND section (369 files / 281 rows / 88 unindexed, measured directly from the
ambient store before this iteration's work began). This plan does not attempt to resolve exactly
which mechanism produced that broader universe/count on the rig QA actually captured — that is an
auditor-class question, outside this agent's remit — but every test case below is written to be
correct and checkable regardless of which shape the rig is actually in when next opened (see each
case's own hedge on exact counts and the specific symbol involved).

**Current process state at the time this plan was written** (checked via `ss -ltnp` and a direct
`curl`): the frontend is still listening on `:3301`, but the backend on `:8301` is **not currently
reachable**. `/desk` will show its amber "Backend unreachable" panels until the backend is
restarted — see the restart recipe below.

---

## Critical constraints — read before executing ANY test case below

- **Rig location** (the same one the dev prepared and QA already used):
  ```
  /home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.154299/desk-iter14-scoped-qa
  ```
  Backend on `:8301`, frontend on `:3301`. Restart recipe (from
  `docs/handoffs/goal-desk-iter-14-dev.md`, reused verbatim — restarts against the SAME on-disk
  data; nothing is reseeded or lost):
  ```bash
  SCOPED_ROOT="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.154299/desk-iter14-scoped-qa"
  nohup bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301 > /tmp/backend.log 2>&1 &
  disown
  rm -rf apps/frontend/.next   # T-9 -- only needed before capturing NEW official evidence
  nohup env CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh > /tmp/frontend.log 2>&1 &
  disown
  ```
  For a routine re-verification pass where the already-running frontend is sufficient, only the
  backend line needs to run.
- **The empty-state window (UT-02 / TC-17) is very likely ALREADY CLOSED on this specific rig.**
  Given `qa_passed: true` and the existing TC-17/TC-18 PNGs, a reconciliation run has almost
  certainly already been recorded here. **Do not assume the honest-empty "No reconciliation run
  recorded yet." state can be reproduced live on this rig** — confirm first with
  `GET http://localhost:8301/research/desk/coverage/reconcile/runs` once the backend is back up; if
  `latest` is non-null, treat UT-02 below as an evidence-review case, not a live capture. Only a
  brand-new scoped copy (a fresh run of `goal-desk-iter9-scoped-backend.sh` against a NEW,
  distinctly-named root, replaying the dev handoff's own plant steps 1–5) can reproduce the empty
  state live again — out of scope for a routine re-verification pass.
- **Do not click "Top-up" anywhere on this rig.** It is irrelevant to J-10, starts a real network
  fetch against the live keyless Yahoo adapter, and only adds risk/noise to this plan's evidence.
- **Do not click "Cancel" during any "Reconcile Index" trigger you perform.** Reconciliation is a
  local, no-network, classify→reindex→verify walk fast enough that the backend's own unit suite uses
  a deterministic test seam (not real timing) to exercise its "running"/cancel states — a human
  click is unlikely to land inside the window reliably, and no Definition-of-Done line in this
  iteration requires a live-cancelled capture (only TC-17/TC-18/TC-19 do: empty state, populated
  state, demo walkthrough). If a triggered run completes before you can observe "Reconciling…", that
  is expected, not a failure — see UT-04.
- Functional/API-level assertions (raw JSON shape, checksum/append-only discipline, the 44-test
  `test_desk_index_reconcile.py` suite, the MCP 17-tool contract, `git diff --stat`, the config
  fingerprint) are already covered in `reports/qa/goal-desk-iter-14-test-plan.md` (TC-01 through
  TC-16, TC-20) and are **not duplicated here** — this plan covers only what is observable through
  the browser.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. Execute in the
order given below — this is NOT a set of independent cases; UT-04 onward depends on state UT-02/
UT-03 observe first, and UT-07/UT-08/UT-09 depend on UT-04's trigger having already happened. -->

---

### UT-01 — `/desk` loads cleanly and issues zero POSTs on load (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The scoped rig is running (restart per Critical Constraints if needed).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Wait for the gray pulsing loading skeletons to disappear.
3. Open DevTools (F12) → Network tab, filter for `reconcile`, then reload the page once more.
4. Scroll to the very bottom of the page.

**Expected Result:**
- The page renders with the heading "Desk"; the top nav shows "Cockpit", "Structure", "Desk" with
  "Desk" marked active — no blank screen, no red/amber "Backend unreachable" panel (if one appears,
  the backend needs restarting first).
- No red console errors.
- Step 3: every captured request matching `reconcile` is a `GET` — to
  `/research/desk/coverage/reconcile/compute` and `/research/desk/coverage/reconcile/runs`. Zero
  `POST` requests to either `/compute` path fire merely from loading or reloading the page (the
  "every run is an explicit operator act" anti-goal).
- Step 4: the LAST section on the page reads "Index Reconciliation", immediately preceded by a
  section titled "Top-up Runs" (or "Top-up runs").

---

### UT-02 — Honest empty reconciliation state (TC-17 equivalent — evidence review primary, live capture only if the window is still open)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Index Reconciliation section, empty variant (`data-testid="desk-reconcile-runs-empty"`)

**Preconditions:**
- Per Critical Constraints, first call `GET http://localhost:8301/research/desk/coverage/reconcile/runs`
  (once the backend is up) and read `latest`. If `latest` is non-null, this window is already closed
  on this rig — do only the evidence-review steps (1–2) below and skip the live-capture steps (3–6).

**Steps (evidence review — always do this):**
1. Open `reports/qa/goal-desk-iter-14-evidence/TC-17-empty-reconciliation.png` in an image viewer.
2. Confirm it shows a live, fully-hydrated `/desk` page (a real ranked table with real symbols), not
   a loading skeleton or a blank tab.

**Steps (live capture — ONLY if `latest: null` was confirmed above, e.g. on a freshly-seeded rig):**
3. Navigate to `http://localhost:3301/desk`, scroll to the very bottom.
4. Read the Index Reconciliation section's text.
5. Scroll up to the ranked "Briefing" table; locate a row whose "coverage" cell shows at least one
   dark/gray timeframe badge alongside lit ones (the dev handoff's own documented plant case: AAPL,
   with `1d` dark and `1h`/`4h`/`1w` lit — `data-testid="desk-coverage-badge"
   data-timeframe="1d" data-has-bars="false"` on that specific badge).
6. Capture one screenshot showing BOTH the Index Reconciliation section's empty-state text AND that
   dark badge's row, legible together in one frame.

**Expected Result:**
- Steps 1–2: the archived screenshot exists and shows a live page. **Caveat, disclosed from this
  plan's own review**: as saved, this PNG (1400×1000, a viewport capture) shows only the Briefing
  table's top rows for a wide, multi-symbol universe — it does not, by itself, show the Index
  Reconciliation section or a coverage badge in the same frame. Note this rather than assume it
  already satisfies the "both legible in one screenshot" requirement below.
- Steps 3–6 (if performed): the section reads exactly "No reconciliation run recorded yet."; the
  identified row's dark badge and the empty-state text are both legible in one frame — this IS the
  "both legible in one screenshot" bar TC-17 and the phase spec's Visual Requirements set.

---

### UT-03 — Every pre-existing `/desk` section still renders, unaffected, and the controls panel was correctly renamed (regression)

**Type:** regression
**Priority:** P1 *(elevated — `/desk` is the shared home of nine required-still-passing journeys;
"J-01–J-09 remain green" is an explicit Definition-of-Done line, independent of J-10's own success.)*
**Surface:** `/desk`

**Preconditions:**
- Backend reachable; state-independent (works whether Index Reconciliation is empty or populated).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Scroll from top to bottom, reading each section heading in order.
3. On the "Run Screen / Top-up / Reconcile Index" controls panel, read its title and count its
   buttons.

**Expected Result:** sections appear in this exact order, all populated (none showing an
"unavailable" or crashed state):
1. "Provenance" — shows Universe snapshot / Screen date / As of / Config fingerprint / Bar-store
   signature values.
2. "Briefing" — a ranked rows table with columns `symbol, side, class, distance, score, coverage,
   tick evidence, basis`.
3. "Skipped Members" — either a populated list or the honest "No members were skipped in this
   screen." empty state.
4. "Screen History" — a dated table.
5. The controls panel titled exactly **"Run Screen / Top-up / Reconcile Index"** (its `aria-label`
   is "Run Screen, Top-up and Reconcile Index controls"), holding exactly 3 buttons side by side:
   "Run Screen", "Top-up", and "Reconcile Index" (or "Retry Reconcile Index" only if a prior run
   genuinely failed).
6. "Top-up Runs" (or "Top-up runs").
7. "Index Reconciliation" — correctly the LAST section on the page.

---

### UT-04 — Trigger "Reconcile Index" and confirm it reaches a terminal state (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `data-testid="desk-reconcile-button"`

**Preconditions:**
- UT-01/UT-03 completed. The "Reconcile Index" button is present and NOT disabled.

**Steps:**
1. Scroll to the "Run Screen / Top-up / Reconcile Index" panel.
2. Click "Reconcile Index".
3. Watch the button and the area immediately below it for up to 5 seconds.

**Expected Result:**
- The button becomes disabled momentarily. It MAY show "Reconciling…" with a small pulsing dot and
  a one-word phase label (one of "classifying", "reindexing", "verifying") plus a "Cancel" button —
  OR it may transition straight to its terminal state before this is observable. **Either outcome is
  a PASS** — reconciliation is a fast, local, no-network operation; a stuck "Reconciling…" that never
  resolves after 5+ seconds would be the actual failure to watch for.
- Within a few seconds, the button returns to enabled, reading exactly "Reconcile Index" — not
  "Retry Reconcile Index" (which would indicate a genuine failure — flag this if seen; nothing in
  this rig's design should cause one) and not left permanently disabled.
- No red trigger-error text (`data-testid="desk-reconcile-compute-trigger-error"`) appears.

---

### UT-05 — Populated Index Reconciliation panel shows correct before/after data (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `data-testid="desk-reconcile-run-latest-detail"`

**Preconditions:**
- UT-04 completed (or the rig already had a recorded run per UT-02's precondition check).

**Steps:**
1. Without reloading, wait up to 2 seconds, then scroll to the "Index Reconciliation" section (or
   reload once if you triggered UT-04 in a separate session).
2. Read the run history table's rows.
3. Read the "Latest run — `<date>` · `<id>`" detail block beneath it.

**Expected Result:**
- The table (`data-testid="desk-reconcile-runs-table"`) shows at least 1 row — exactly 1 if this was
  genuinely the first-ever trigger on this rig (unlikely per the Critical Constraints note; treat 1
  or more as correct either way).
- The latest-run heading reads "Latest run — `<date>` · `<id>`" matching the table's own
  newest-recorded row.
- `data-testid="desk-reconcile-run-latest-state"` reads exactly `state: done`.
- `data-testid="desk-reconcile-run-latest-series-on-disk"` reads "`N` series on disk" for some
  positive integer `N`.
- `data-testid="desk-reconcile-run-latest-rows-indexed"` reads "rows indexed: `X` before, `Y` after"
  where **`Y` is strictly larger than `X`** — rows were genuinely added back, not just relabeled. Do
  not fail this check over the exact numbers: the already-recorded run on this rig (per the QA
  report) shows a broad repair (drift in the dozens), while the dev handoff's own documented plant
  describes a narrower ~7-row AAPL/`1d` case — either shape is consistent with a genuine repair as
  long as `Y > X`.
- "Drift before (`N`)" lists at least one entry. If AAPL is among the rows visible in the Briefing
  table, look for an entry reading exactly "**AAPL 1d** — series on disk, no index row (`<series_id>`)".
- "Drift after (`M`)" — that SAME AAPL/`1d` entry (if it was present in drift-before) must NOT
  reappear here; `M` may still be non-zero for other pairs this run did not fully resolve — only
  fail this check if the identical pair reappears in both lists. If drift-after is genuinely zero,
  it renders as the text "no drift" (`data-testid="desk-reconcile-run-latest-drift-after-empty"`),
  never a blank area.
- This content appeared without a manual page reload if you stayed on the page from UT-04 (confirms
  the ~700ms poll-refresh-on-terminal behavior).

---

### UT-06 — Store errors are honestly absent when no corrupted file exists (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — `data-testid="desk-reconcile-run-latest-store-errors"`

**Preconditions:**
- UT-05 completed (latest-run detail visible).

**Steps:**
1. In the latest-run detail block, look for a "Store errors (`N`)" heading.

**Expected Result:**
- Per the dev handoff, TC-3's corrupt-file case was deliberately NOT planted on this shared rig — so
  the default, expected outcome is: **no "Store errors" heading appears anywhere in the block.** The
  element must be entirely absent from the page, not rendered as "Store errors (0)" — an honestly
  absent element, not a fabricated zero-count line. (If a corrupted file genuinely exists on this
  rig for some other reason, a "Store errors (`N`)" list with `N ≥ 1` naming that file and its
  verbatim error text would instead be the correct outcome — either state is fine as long as it
  reflects reality, never a placeholder.)

---

### UT-07 — "Run Screen" produces a NEW snapshot and the previously-dark badge relights (happy-path — the iteration's core claim)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `data-testid="desk-screen-rows-table"`, `data-testid="desk-coverage-badge"`

**Preconditions:**
- UT-04/UT-05 completed (a reconciliation run has resolved `state: done`).
- Before proceeding, note which symbol/timeframe badge (if any) currently reads dark
  (`data-has-bars="false"`) in the Briefing table — you will re-check the SAME one in step 5.

**Steps:**
1. Scroll to the "Run Screen / Top-up / Reconcile Index" panel.
2. Click "Run Screen".
3. Wait for completion (well under a minute — this reads only already-stored bars, no network
   fetch).
4. Read the outcome line just above the controls.
5. Scroll to the Briefing table; find the same row/badge noted in Preconditions.
6. Scroll to "Screen History"; count the dated rows.

**Expected Result:**
- Step 4: the outcome line reads "Recorded a new snapshot — screen-…" — **NOT** "Reused the
  snapshot already recorded for this key…". A "Reused" result here would mean the post-repair
  `bar_store_signature` check failed to produce a genuinely new snapshot key — flag this as a
  defect, since it would mean TC-12's SSOT guarantee is not holding in the live UI.
- Step 5: the badge noted in Preconditions (if any was dark) now renders `data-has-bars="true"`,
  lit with emerald styling — matching its sibling timeframes. If every badge was already lit before
  this step (nothing left to repair), confirm they all remain lit.
- Step 6: the row count increased by exactly 1 versus before step 2.

---

### UT-08 — Composite screenshot: populated reconciliation detail + lit badge together (TC-18 equivalent)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- UT-05 and UT-07 both completed on the SAME page session (or the same rig, reloaded).

**Steps:**
1. Arrange the viewport (or take two adjoining screenshots and crop/stitch) so that both the Index
   Reconciliation section's populated detail AND the newly-lit badge's row are visible.
2. Capture the screenshot.

**Expected Result:**
- Both the run's drift counts/affected pairs (from UT-05) and the lit badge (from UT-07) are legible
  together in one frame — this is the exact "both legible in one screenshot" bar the phase spec's
  Visual Requirements and TC-18 set, and the specific thing the two already-archived PNGs (per the
  disclosure at the top of this document) do not currently demonstrate.

---

### UT-09 — The pre-repair screen snapshot stays immutable (regression — SSOT/immutability proof)

**Type:** regression
**Priority:** P1 *(elevated — this is a direct, visual proof of the critical "Immutable data" and
"Snapshots are append-only and pinned" anti-goals, not a cosmetic regression check.)*
**Surface:** `/desk` → Screen History drill-in

**Preconditions:**
- UT-07 completed (a new screen snapshot now exists in addition to at least one older one).

**Steps:**
1. Scroll to "Screen History"; click the row for the OLDER screen date — the one that existed
   BEFORE UT-07's new run (i.e., any date other than the one UT-07 just added).
2. Confirm the "Viewing the recorded screen for `<date>` — not the latest." banner appears.
3. Find the same symbol/badge checked in UT-07; read its state.
4. Click "Latest" to return.
5. Re-check the same badge.

**Expected Result:**
- Step 3: the OLDER screen's own recorded badge for that pair still reads exactly as it did BEFORE
  any reconciliation ran (dark / `has_bars: false`, if that was its pre-repair state) — proving the
  repair never rewrote an existing snapshot in place, only appended a new one under a new
  `bar_store_signature`.
- Step 5: after clicking "Latest", the badge reads lit again (the newest screen, from UT-07).

---

### UT-10 — Index Reconciliation is discoverable without scrolling tricks or extra clicks (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- None beyond a running frontend/backend.

**Steps:**
1. Open a fresh browser tab, navigate directly to `http://localhost:3301/desk`.
2. Scroll down at a normal pace, reading each section heading as it comes into view.

**Expected Result:**
- The "Index Reconciliation" section is reached by ordinary scrolling alone — no toggle, tab, or
  "show more" interaction required.
- Its heading is styled identically to every other section heading on the page (same uppercase
  small-caps treatment, same panel border) — not an afterthought or debug panel.
- It is clearly distinguishable from "Top-up Runs" immediately above it (different column headers:
  `date, run, state, series on disk, rows indexed (before → after)` vs. Top-up's own
  `date, run, state, attempted / total, universe snapshot`).

---

### UT-11 — Reconciliation copy stays descriptive measurement only, never advice or urgency language (ux / anti-goal)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` — Index Reconciliation section + Reconcile Index button

**Preconditions:**
- Populated state visible (per UT-05).

**Steps:**
1. Read every visible string in the Index Reconciliation section: table cells, the "Latest run"
   line, both drift lists' entries, any store-errors text, and the button's own label/progress/
   cancelled-note text.

**Expected Result:**
- All copy is measurement/description only: run id, date, state word, counts, pair names, verbatim
  error text, the phase words "classifying"/"reindexing"/"verifying".
- No advice, imperative, prediction, or ranking language appears anywhere — specifically absent:
  "should", "buy", "sell", "watch this", "opportunity", "recommended", "warning", "act now", or any
  similar cue implying action. The cancelled-state note ("Index reconciliation cancelled — the index
  was not repaired this run.") is itself a plain factual statement, not a warning.
- Matches `tests/test_copy_discipline.py` staying green unmodified — already independently confirmed
  in the functional QA report; this is the human-eyeball confirmation of the same guarantee, not a
  duplicate of that automated lint.

---

### UT-12 — Running-state progress line and Cancel button presence (informational, best-effort only)

**Type:** happy-path
**Priority:** P3 *(informational — no Definition-of-Done line requires a live-observed running/cancel
state; this case exists only to note what to look for IF the timing happens to allow it.)*
**Surface:** `/desk` — `data-testid="desk-reconcile-compute-running"`, `desk-reconcile-compute-cancel`

**Preconditions:**
- None specific. Re-triggering "Reconcile Index" again after UT-04/UT-07 is safe and idempotent —
  with nothing left to repair, it should simply classify, find zero drift, and resolve `done` fast.

**Steps:**
1. Click "Reconcile Index" again and watch closely (do not click "Cancel" — see Critical
   Constraints).

**Expected Result:**
- If observable at all: the pulsing-dot progress line shows exactly one word — one of
  "classifying", "reindexing", "verifying" — and a "Cancel" button is present and enabled beside it.
- If the run completes too fast to observe this (likely, given zero network calls involved), that is
  **not a failure**. This exact contract (single-flight while running, cancel returns 409 when idle)
  is already proven by the backend's own unit tests (functional test plan TC-09/TC-10/TC-11) and is
  structurally the same mirrored component Top-up's own cancel behavior already uses, previously
  verified live against a real running operation in this session's own iteration-11 UI test plan
  (UT-06/UT-07 there).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads clean, zero POSTs on load | smoke | P1 | `/desk` |
| UT-02 | Honest empty state (TC-17) — evidence review + conditional live capture | happy-path | P1 | `/desk` |
| UT-03 | Every pre-existing section unaffected + controls rename | regression | P1 (elevated) | `/desk` |
| UT-04 | Trigger Reconcile Index, reaches terminal state | happy-path | P1 | `/desk` |
| UT-05 | Populated panel: correct before/after data | happy-path | P1 | `/desk` |
| UT-06 | Store errors honestly absent when none exist | error | P2 | `/desk` |
| UT-07 | Run Screen: new snapshot, badge relights | happy-path | P1 | `/desk` |
| UT-08 | Composite screenshot (TC-18) | happy-path | P1 | `/desk` |
| UT-09 | Pre-repair screen stays immutable | regression | P1 (elevated) | `/desk` |
| UT-10 | Discoverable without scrolling tricks | ux | P3 | `/desk` |
| UT-11 | Copy stays descriptive, no advice language | ux | P3 | `/desk` |
| UT-12 | Running-state/Cancel presence (best-effort) | happy-path | P3 (informational) | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**

### Coverage notes

- **No validation-type test case.** J-10 adds no new form or text-input field — "Reconcile Index" is
  a parameterless trigger button, matching this session's own established coverage note from
  iterations 9 and 11 for the same reason.
- **TC-19 (the `[NEW]`-flagged demo-narrator walkthrough) is a separate downstream lane**, not
  reproduced here as manual click-steps. This plan's own strict ordering (UT-02's empty-state check
  before UT-04's trigger, on the same rig) is exactly what makes that walkthrough recordable
  correctly — the demo-narrator lane depends on this plan's sequencing discipline, not the reverse.
- **J-01–J-09 regression is not re-derived as 9 separate UT cases.** All 8 browser-verifiable ones
  (J-06 has no browser surface) are already 8/8 PASS per
  `reports/phase-goal-desk-iter-14-smoke-replay-results.md`. UT-03 above is this plan's own
  lighter-weight, directly-observable check on the same shared-surface risk (mirrors the equivalent
  choice made in this session's own iteration-9 and iteration-11 UI test plans, both new-capability
  iterations like this one).
- **Functional/API-level assertions** (drift-classification bucket correctness, append-only/checksum
  discipline, single-flight/idle-poll/409-cancel contract, byte-identity proofs, sentinel checks) are
  already covered in `reports/qa/goal-desk-iter-14-test-plan.md` (TC-01–TC-16, TC-20) and
  intentionally not duplicated here.
- **The evidence-discrepancy note at the top of this document is the single most important thing to
  carry forward** to whoever next touches TC-17/TC-18: the already-archived screenshots do not, as
  saved, demonstrate the composite framing this plan's UT-02/UT-08 require. This plan does not
  render a verdict on that gap — only auditor-class review can — but it defines the exact bar a
  corrective re-capture needs to hit.
