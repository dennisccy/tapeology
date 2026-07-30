# Goal Iteration 24 — `/desk`'s ranked table fits its own page, no sideways scroll

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: the reflow touches the ONE shared `/desk` ranked-table render behind 9 already-shipped journeys' testids/tooltip/copy contracts (J-03, J-04, J-05, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15), plus 13 stored golden replay scripts and 3 guard-test suites — no single journey's own test coverage spans that blast radius; the prior evaluator's own depth recommendation for this iteration is also `full`
- **Frontend Present:** yes
- **Target journeys:** J-16
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk` BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure` prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves every recorded series on disk untouched.) *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*

## GOAL

The operator reads every ranked row's full disclosure (rank, symbol, side, class, distance, score,
coverage, tick-evidence, basis, history, band, opposite, levels) on `/desk` in one screenshot at a
1440×900 viewport with zero horizontal scroll, and at least the first eight ranked rows fit on
screen without excessive per-row height.

## BACKGROUND

Iteration 23 (GOAL_ACHIEVED, two-key confirmed) shipped J-15 and left all 15 must-have journeys
passing with no failing/partial/unknown journey and no open blocker — the "zero remaining FAILING
journeys" case this agent's own rules would normally resolve by deferring to the evaluator. But the
goal-proposer has since appended **J-16** inside the `AUTO:journeys` marker block of `docs/goal.md`,
promoting the open design question both the iter-23 evaluator ("the briefing table now has twelve
columns... the right question is how the briefing shows this much detail at all") and the
iteration-state digest ("the next proposer cycle should treat 'how the briefing surfaces disclosure'
as its own journey") explicitly deferred. J-16 is a real, unbuilt, failing-by-default journey (absent
from `journey-history.json`), so per the priority rubric it is this iteration's sole target — the
smallest concrete unblocker available, since it closes the layout debt that has produced a FAIL row
(UT-07) and two `RECORDED_WITH_NOTES` walkthrough verdicts (iter-21, iter-23) without touching any
served value. Depth is `full` per the evaluator's own binding recommendation (`next_depth: full` in
`session.json`), independently justified by trigger 1: this reflow is the ONE shared `/desk`
ranked-row render underneath nine already-shipped journeys' testids, tooltip content, and copy — a
regression here is invisible to any single journey's own narrow test.

**Lessons applied:** (1) iter-19/21/22 — J-16's acceptance is explicit that "no native `title`
tooltip is required by this journey... the T-10a headed rig is NOT needed", so do not invoke
`project-extensions/qa-rig/` for this iteration's evidence; every reveal here is plain DOM content a
normal headless screenshot captures. (2) iter-20/21 — any demo-narrator script touching this page
must be JSON-lint-checked (`demo_runner.py --mode lint`) before recording, and since
`demo_runner.py`'s action vocabulary has no scroll primitive, this iteration's whole point is to make
scrolling unnecessary — do not add one. (3) iter-21/23 — every click locator in the `[NEW]`-flagged
walkthrough script must name exactly ONE row (e.g. by row index or a unique symbol, never a bare
`[data-testid='desk-row-levels']` that matches all 100 cells at once), which is the only reason
iter-21 and iter-23's films were `RECORDED_WITH_NOTES` instead of `RECORDED`. (4) iter-17 (first
lesson) — the `Target journeys:`/`Required-still-passing journeys:` lines above are each kept on ONE
physical line. (5) iter-9/11/14/15/17/19/20/21/23 (the 8-run scoped-rig deviation) — this iteration
needs no new screen/top-up/reconciliation run at all (J-16 is render-only over the ALREADY-recorded
latest screen), so the fix is simply: do not click "Run Screen" or the top-up/reconcile triggers
during evidence capture; read the ambient store's already-populated `/desk` page only.

## IN SCOPE

### Backend

- none — J-16 is explicitly zero-backend-diff (goal.md J-16 step 5: "zero backend diff, zero new
  value... the backend TAKES A ZERO DIFF"). `desk_screen.py`, `tradability.py`, `levels.py`,
  `bars.py`, `bar_index.py`, `desk_coverage.py`, `config.py`, `app/engine/`, `app/mcp/` all take a
  zero change.

### Frontend

- [ ] Reflow `/desk`'s ranked-row table (`apps/frontend/app/desk/page.tsx`) so all disclosures fit
      the page's own `mx-auto max-w-7xl` container (`:1829`) at a 1440×900 viewport with zero
      horizontal scroll: drop the in-cell label prefixes the column headers already state (the
      `basis `/`history `/`band `/`opposite `/`N levels` ≈ 35 characters per row), relax
      `LABEL_CELL`'s `whitespace-nowrap` (`:141`) on the long disclosure cells, and/or lay some
      disclosure fields out as a second line of the same row. Do not drop, hide, collapse behind a
      click, or move into a native `title` tooltip any of the twelve existing disclosures, and do not
      shrink type below the page's existing `text-xs` scale.
- [ ] Render `DeskCoverageBadges` (`:218`, currently `flex flex-wrap`) so its four badges render on
      one line per row instead of wrapping into four, bringing a ranked row's own measured height to
      ≤ 60 px (today ~115 px).
- [ ] Add a `rank` cell rendering each row's own 1-based position in the DISPLAYED snapshot's served
      `rows` array as a plain integer — no label implying action/quality/urgency, no client-side
      sort/reverse/re-slice/paginate of `rows` anywhere in `page.tsx`.
- [ ] Render the class and distance cells as chips, reusing the page's existing bordered
      `text-[11px]` badge style (`desk-coverage-badge`/`round number` precedent) with the exact same
      text those cells render today.
- [ ] Keep every existing `data-testid` and its exact rendered text byte-unchanged
      (`desk-screen-rows-table`, `desk-row-drill-in`, `desk-row-side`, `desk-row-band-class`,
      `desk-row-distance`, `desk-row-score`, `desk-coverage-badges`/`-badge`,
      `desk-row-tick-evidence`, `desk-row-basis`, `desk-row-history`, `desk-row-band`,
      `desk-row-opposite`, `desk-row-levels`, `desk-skip-row*`, `desk-history-row`,
      `desk-provenance`, `desk-title`, the compute controls); if a disclosure's markup moves to a new
      element/line, its `data-testid` moves with it, keeping the same text. Keep the row's stretched
      drill-in anchor's `href`, `absolute inset-0`, `data-testid`, and dynamic consolidated `title`
      attribute byte-unchanged.
- [ ] Extend the source-introspection guard suite (`apps/backend/tests/test_desk_ui_guards.py`, the
      existing pattern) with: (a) `page.tsx` never calls `.sort(`, `.reverse(`, re-slices, or applies
      a comparator over `rows` — proven with its own seeded can-fail counter-test; (b) every testid
      named above is still present in the source.
- [ ] `apps/backend/tests/test_copy_discipline.py` and `apps/backend/tests/test_desk_hover_tooltip_guard.py`
      stay green UNMODIFIED (no assertion edits).

### New user-facing capability

The operator can read a ranked row's entire disclosure set — rank, symbol, side, class, distance,
score, coverage, tick-evidence, basis, history, band, opposite wall, and level composition — in one
screenshot with no sideways scrolling, and see at least 8 ranked rows without scrolling excessively.

### New information displayed

A `rank` cell (the row's own 1-based position in the served order) — rendered for the first time, but
computing nothing new: J-03 already records that order as data.

### New user actions

None — no new buttons/controls; this is a pure layout/render change.

### UI surface changes

`/desk`'s ranked-row table layout only (row width, row height, coverage-badge wrapping, chip styling
for class/distance, new `rank` cell).

### Product surface delta

`/desk` becomes fully legible without horizontal scrolling at a normal viewport; no navigation, IA,
or served-value change.

### Blueprint conformance

`/desk` under the Desk nav section — already registered in `runs/goal-session-desk/state/blueprint.md`'s
Information Architecture; this iteration adds a Feature/journey-homes row for J-16 pointing at the
same canonical home, a Navigation-skeleton note, and a `RESOLVED at iter-24` Data-Contract note — all
already applied to `blueprint.md` by this decomposer pass. No nav-skeleton structural change.

### Data-contract additions

None. J-16 renders only what `GET /research/desk/screen` already serves — `desk_screen.ScreenStore`
stays the only owner and that GET the only serving endpoint. The `rank` cell renders the row's own
position in the SERVED order (already recorded data per J-03); the page never re-orders, sorts,
filters, or paginates it. Zero new field on any recorded shape, zero new endpoint, zero new `Config`
field, zero new MCP tool.

## OUT OF SCOPE

- Any backend/data-model change (see Backend section above — this journey is explicitly zero-diff).
- Running a NEW "Run Screen", top-up, or reconciliation compute — all evidence uses the ALREADY
  -recorded latest screen (`screen-2026-07-30-bad6387963ef` or whatever is currently latest); no new
  append-only write of any kind this iteration.
- Fixing `closure_gate.py`'s bare-substring `backend-only` false-positive or
  `goal_gate.py results`' `| FAIL |` regex miss on bolded cells — both are framework/harness defects
  flagged for the owner's own track (iter-23 next-step follow-ups 1/3), not this product iteration.
- The demo_runner.py `scroll` action / capture-tool enhancement floated at iter-21 — no longer needed
  once this journey ships (the reflow removes the scroll requirement entirely).
- `docs/goal.md`'s stale host-mask paragraph tidy-up (carried non-defect, owner's own track).
- Any new journey beyond J-16.
- The 8-run scoped-rig ambient-write deviation's structural fix (a dispatch-level rail) — this
  iteration avoids the failure mode by not writing anything, not by fixing the rail.

## DEFINITION OF DONE

- [ ] J-16 passes via browser-qa-agent (TC-1 through TC-5)
- [ ] Required-still-passing journeys J-01 through J-15 remain green (deterministic replay + LLM
      fallback where a golden is stale or missing) (TC-6)
- [ ] No anti-goal violation introduced — zero diff to `desk_screen.py`/`tradability.py`/`levels.py`/
      `bars.py`/`bar_index.py`/`StructureChart.tsx`/`config.py`, fingerprint `08e471b10130e1e2`
      unchanged, MCP tool count still exactly 17 (TC-9)
- [ ] Extended/unmodified guard tests pass: `test_desk_ui_guards.py`'s new served-order +
      testid-presence guard (with its own seeded counter-test), `test_desk_hover_tooltip_guard.py`
      unmodified, `test_copy_discipline.py` unmodified (TC-7, TC-8, TC-10)
- [ ] `[NEW]`-flagged demo-narrator walkthrough records `Demo Verdict: RECORDED` (not
      `RECORDED_WITH_NOTES`) with the `opposite` and `levels` columns visible in its own frames and
      every click target naming exactly one row (TC-11)
- [ ] Zero write to any append-only store this iteration — a SHA-256 listing of every universe,
      screen, top-up, and reconciliation file on disk is identical before and after (TC-12)
- [ ] Unit tests pass; no regressions; full backend suite green with a pass count ≥ the iter-23
      baseline (1454 passed / 8 skipped)
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-24-dev.md`

## TESTING REQUIREMENTS

- Browser: J-16 (new); regression sweep over J-01 through J-15 by deterministic golden replay, LLM
  fallback for any journey whose golden is stale or absent (the J-09 iter-23 precedent)
- Unit/integration: `test_desk_ui_guards.py` (extended), `test_desk_hover_tooltip_guard.py`,
  `test_copy_discipline.py`, full backend suite, `Config().config_fingerprint()` pin check, MCP
  17-tool contract test
- Error cases: not applicable — this is a render-only layout change with no new input surface;
  legacy pre-J-15/J-14/J-13/J-11/J-08 snapshots must still render their honest absence strings
  unchanged (TC-5)

Test-first contract:

- TC-1: given a real browser at a 1440×900 viewport after a clean `.next` rebuild (`rm -rf
  apps/frontend/.next`), when `/desk` loads the latest populated screen, then one screenshot shows the
  top-ranked row's rank, symbol, side, class, distance, score, coverage badges, tick-evidence, basis,
  history, band, opposite, and levels values all legible at once with no horizontal scrollbar visible
  on the ranked table's scroll container.
- TC-2: given that same rendered screen, when the ranked table's own `scrollWidth` and its scroll
  container's own `clientWidth` are measured (devtools/JS), then `scrollWidth <= clientWidth`, and
  both numbers are quoted in the UI-test-results row that replaces iter-23's UT-07 FAIL measurement
  (1795 px inside 1214 px).
- TC-3: given a populated ranked row, when `DeskCoverageBadges`' four badges are inspected, then all
  four share one line (same top y-coordinate) and the row's own measured height is ≤ 60 px.
- TC-4: given the populated screen, when a full-page capture (or a crop of one) is taken, then ranked
  rows with served positions 1 through 8 are legible with their `rank` cell values reading 1, 2, 3, 4,
  5, 6, 7, 8 in that order.
- TC-5: given the skipped-members table and a pre-J-15 legacy snapshot opened by id, when the page
  renders them, then the skipped table still groups `no bars`/`no basis` honestly, and the legacy
  snapshot still renders every honest absence string unchanged ("basis not recorded in this
  snapshot", "history not recorded in this snapshot", "close not recorded in this snapshot",
  "opposite wall not recorded in this snapshot", "composition not recorded in this snapshot").
- TC-6: given the 13 stored golden replay scripts (`runs/goal-session-desk/journey-scripts/J-01.json`
  through `J-14.json`, no `J-06`), when each is replayed after this iteration's change, then every one
  passes with zero script edits.
- TC-7: given `test_desk_ui_guards.py`'s extended source-introspection guard, when
  `apps/frontend/app/desk/page.tsx` is scanned, then no `.sort(`, `.reverse(`, re-slice, or comparator
  expression appears over `rows` anywhere in the file, every testid named in the IN SCOPE list is
  still present in source, and a seeded counter-test proves the guard itself can fail.
- TC-8: given `test_desk_hover_tooltip_guard.py` and `test_desk_ui_guards.py`'s existing
  endpoint/price-arithmetic guards, when the full backend suite runs post-change, then both pass with
  zero assertion edits.
- TC-9: given the backend after this iteration's frontend-only change, when the full suite runs and
  `Config().config_fingerprint()` and the running MCP module's tool list are checked, then the suite
  is green with pass count ≥ 1454, the fingerprint prints `08e471b10130e1e2`, the MCP tool list has
  exactly 17 entries, and `git diff` shows zero changes to `desk_screen.py`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, and `config.py`.
- TC-10: given `apps/backend/tests/test_copy_discipline.py`, when it runs post-change, then it passes
  unmodified (no new copy string is added; only layout moved).
- TC-11: given a `[NEW]`-flagged demo-narrator walkthrough recorded over the populated `/desk` page,
  when its saved frames are opened, then the `opposite` and `levels` columns are visible inside the
  film's own frames (not off-screen), every click locator in the script matches exactly one row
  element, and the run's own verdict line reads `Demo Verdict: RECORDED` (not `RECORDED_WITH_NOTES`).
- TC-12: given every recorded universe, screen, top-up, and reconciliation file under
  `apps/backend/.data`, when a SHA-256 listing is taken immediately before and immediately after this
  iteration's dev/QA/demo work, then the two listings are byte-identical (a render-only iteration
  writes no record at all).

## NOTES

- `docs/goal.md`'s J-16 acceptance text and rationale (measured against iter-23's own
  `UT-07-fail.png`: `scrollWidth` 1795 px inside `clientWidth` 1214 px, and the per-column character
  maxima: `opposite` 50, `levels` 62, `history` 38, `band` 36, `basis` 35, ~35 of which per row are
  redundant label prefixes) is the load-bearing spec for exact numeric targets — read it directly
  (`runs/goal-session-desk/iter-24/goal-slice.md`) before implementing; this spec paraphrases its
  structure but the goal text's own numbers govern (per the iter-18 lesson: never let a spec
  paraphrase silently override the canonical goal-text rule).
- `runs/goal-session-desk/state/blueprint.md` has already been updated by this decomposer pass: a new
  Feature/journey-homes row for J-16, a Navigation-skeleton note, and a `RESOLVED at iter-24`
  Data-Contract note (documenting the zero-new-row, zero-nav-change scope) — no further blueprint edit
  should be needed unless the build genuinely diverges from this plan.
- `runs/goal-session-desk/iter-23/eval-confirm.md` and `iter-23/eval.md` both independently verified
  UT-07's FAIL measurement (1795 px / 1214 px) as the one open, non-blocking condition from the prior
  iteration — this iteration turns that exact measurement PASS, quoted the same way.
- Every browser-evidence lane needs the T-9 clean rebuild (`rm -rf apps/frontend/.next`) before
  capturing — a stale build has repeatedly produced false results this session.
