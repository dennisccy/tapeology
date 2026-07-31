# Goal Iteration 33 — Fix J-19's self-contradicting reach line, cap the earlier-pairs list, repair two stale golden scripts, and record J-19's owed walkthrough

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 33
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: the fix's own correctness requires touching the
  frontend derivation function (`topupLibraryReach`, `apps/frontend/app/desk/page.tsx`), extending
  its structural guard test (`test_desk_topup_library_reach_guard.py`, which iter-32 shipped but
  which did NOT catch this exact bug), repairing TWO other journeys' golden replay scripts
  (`J-17.json`, `J-19.json`, both stale against the same "latest run" panel), and recording a
  first-ever `[NEW]`-flagged demo-narrator walkthrough — a blast radius spanning more agents/tests
  than any single journey's own coverage reaches, which only a full dispatch sends (lean/evidence
  send no demo-narrator, per the iter-24/26/27/28 lessons on file). Separately and consistently: the
  engine's own binding recommendation for this iteration is already `full`
  (`runs/goal-session-desk/session.json` `next_depth: "full"`), set after the second-key confirm
  (`runs/goal-session-desk/iter-32/eval-confirm.md`) REJECTed iter-32's first-key GOAL_ACHIEVED.
- **Frontend Present:** yes
- **Target journeys:** J-19
- **Required-still-passing journeys:** J-04, J-07, J-09, J-16, J-17
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's
    behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation
    of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
    labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
    feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research
    artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects
    WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or report
    as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*
  - **The demolition stays demolished.** No journal-era machinery returns; the desk ledger records
    machine output only — zero manual-input write paths on desk records this era (dispositions/
    annotations are Era C's design space). *(critical)*
  - **The ledger never holds orders.** No sizes, tickets, entries/exits, or account concepts in any
    desk record — rail 1 in desk terms. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged
    by the sentinel every iteration. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside
    the `AUTO:journeys` marker block; it MUST NOT edit human-authored journeys, this Anti-goals
    section, or any other part of the goal file; proposed journeys MUST carry a
    single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1`
    byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just
    to keep the loop alive is a failure. *(critical)*
  - **Host-guard caps are law.** Never disable, widen, or bypass the host's CPU/BLAS/memory caps to
    make a run faster or a pause go away. *(critical)*

## GOAL

Fix the exact bug the second-key confirm rejected on iter-32's Top-up Runs library-reach disclosure
— the "newest recorded reach" line and the "Pairs recorded earlier" list disagree with each other
because they compare at different granularities — cap the earlier-pairs list to a genuinely short
list as J-19's acceptance already required, repair the two golden replay scripts the same display
now invalidates, and record J-19's still-owed `[NEW]`-flagged demo-narrator walkthrough.

## BACKGROUND

`runs/goal-session-desk/iter-32/eval-confirm.md` REJECTed iter-32's first-key GOAL_ACHIEVED on ONE
decisive, reproduced-directly finding: `topupLibraryReach` (`apps/frontend/app/desk/page.tsx:878-904`)
computes `newestDate`/`newestCount`/`earlier` by comparing each pair's `store_frozen_through_after`
as a FULL microsecond-precision ISO timestamp (confirmed at the source: `_iso_bar_epoch` in
`apps/backend/app/research/desk_topup_compute.py:177-185` formats it with
`timespec="microseconds"`, so two pairs whose bars close at different times of day on the SAME
calendar date get different, unequal `store_frozen_through_after` values), while the render
(`:996`, `:1014`) prints only `.slice(0, 10)` — the calendar day. On the ambient store's real latest
run this produced exactly the self-contradiction the confirm opened a screenshot to verify: the page
reads "newest recorded reach 2026-07-30 · 101 pairs reach it" and then lists 303 "earlier" pairs, 202
of which print that SAME 2026-07-30 day under "Pairs recorded earlier." The confirm named this the
rejection reason, plus two riders already on file: J-19's own acceptance step 4 asks for "a short
list" of earlier pairs and the current code renders all of them (up to 303, which is also what
defeated the iter-32 screenshot tool), and the `[NEW]`-flagged demo-narrator walkthrough J-19's
acceptance requires has never been recorded because iter-32 dispatched at `lean` (no demo lane) even
though its own spec asked for `full`. `runs/goal-session-desk/state/iteration-state.md`'s "Active
blockers" additionally flags that this same real ambient run displaced the run TWO golden scripts
were pinned to: `journey-scripts/J-17.json` (asserts a superseded run's exact counts and a "Failed
pairs (14)" block that cannot mount against a run with zero failures) and `journey-scripts/J-19.json`
(pins today's own exact reach date/count/list-size — precisely the mistake `lessons.md` iter-32
flags, itself a repeat of the mistake iter-29 flagged for `J-18.json`). This iteration is scoped to
close all four together, since the display fix, the guard-test extension, and both script repairs
share one root cause and the walkthrough needs a corrected page to narrate. No backend change is
needed or planned: `_pair_window`'s own `store_frozen_through`/`store_frozen_through_after` values are
already correct and byte-identical to the newest bar per J-19's acceptance — the bug is entirely in
the frontend's display-time grouping, so this stays inside the "zero diff to `bars.py`/
`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`desk_topup_log.py`"
law the "Do not redo" list binds. Per the iter-31 lesson, the walkthrough is recorded against the SAME
ambient `:3301`/`:8301` pair the browser-qa lane uses (no scoped rig, no teardown race); per the
iter-32 lesson, both sibling scripts pinned to the same "latest run" panel are refreshed in this SAME
iteration rather than left to break the next replay.

## IN SCOPE

### Backend
- [ ] Extend `apps/backend/tests/test_desk_topup_library_reach_guard.py` (tests only — zero
  production backend diff; zero diff to `desk_topup_compute.py`, `desk_topup_log.py`, `routes.py`,
  `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`)
  with source-introspection assertions that (a) `topupLibraryReach`'s body derives ONE shared
  day-truncation value used for BOTH the newest-extreme computation and the earlier-partition
  filter (no raw full-timestamp `===`/`!==` equality against `store_frozen_through_after` performed
  directly for grouping), and (b) a capping literal bounds the rendered earlier-row array — each
  with a seeded-violation counterpart proving the new assertion can fail, matching this file's own
  existing `test_the_fallback_text_guard_can_fail_on_a_seeded_violation` pattern.

### Frontend
- [ ] Fix `topupLibraryReach` (`apps/frontend/app/desk/page.tsx:878-904`) so the "newest" extreme and
  the "earlier" partition are both computed at CALENDAR-DAY granularity (the same granularity the
  render already prints), not full-timestamp equality — closing the exact self-contradiction the
  confirm reproduced. `store_frozen_through_after`'s own stored value, its null-when-nothing-frozen
  case, and the legacy-run `LIBRARY_REACH_NOT_RECORDED` fallback path stay byte-unchanged.
- [ ] Cap the rendered `desk-topup-run-latest-reach-earlier-row` list to at most 20 rows (a genuinely
  short list, closing J-19 acceptance step 4's own wording, which iter-32 rendered as "every pair"
  despite calling it "a short list" in its own dev handoff). The `desk-topup-run-latest-reach-earlier`
  heading keeps stating the TRUE total earlier count (never the shown count). When the true total
  exceeds 20, add one plain, descriptive sentence disclosing shown-vs-total (no advice/urgency/
  judgement language — `tests/test_copy_discipline.py` stays green unmodified); when the true total
  is ≤20, no such sentence appears (every row already renders, so a "showing N of M" note would be
  redundant/confusing).
- [ ] No new section, control, testid, or ranked-table column: `desk-topup-run-latest-reach`,
  `desk-topup-run-latest-reach-earlier`, `desk-topup-run-latest-reach-earlier-row` keep their
  existing identities; J-16's measured width contract stays untouched.

### Golden replay script maintenance (browser-qa-agent)
- [ ] Refresh `runs/goal-session-desk/journey-scripts/J-19.json` to assert STABLE substrings only
  (e.g. "reach it", "Pairs recorded earlier") rather than today's exact pinned date/count/list-size —
  the `J-18.json` post-iter-30 hardening precedent — so it survives the next real ambient top-up
  without another false break.
- [ ] Refresh `runs/goal-session-desk/journey-scripts/J-17.json`: step 3 no longer asserts the
  now-superseded `WINDOW_BASIS_NOT_RECORDED` fallback text (the CURRENT ambient latest run genuinely
  carries `window_basis`, so it renders the real tail/full-lookback counts line instead) and step 4
  no longer asserts a "Failed pairs (14)" block that cannot mount against a run with zero failures —
  replace step 4 with a liveness re-check (the `J-09.json`/`J-18.json` precedent: a further `/desk`
  navigation after the key match) so the script does not depend on the ambient run's own
  failed-pair count.

### New user-facing capability
None — this is a correctness fix to an already-shipped disclosure (iter-32's Top-up Runs
library-reach line/list) plus its owed evidence, not a new capability.

### New information displayed
None new. The existing reach line and earlier-pairs list now agree with each other at the
granularity both already print, and the list is genuinely short.

### New user actions
None. Read-only disclosure; no new button or control ships this iteration.

### UI surface changes
`/desk`'s existing Top-up Runs section, `LatestTopupRunDetail`'s reach line and earlier-pairs list
only — no new section, no layout change to the ranked table.

### Product surface delta
The operator now reads a reach disclosure that is internally consistent (no pair printed under
"earlier" shares the calendar day named as "newest") and genuinely short, instead of a self-
contradicting sentence beside an ~14-screen-tall list.

### Blueprint conformance
`/desk`, Desk nav section — the SAME already-registered canonical home as J-04/J-09/J-17/J-18/J-19
(`state/blueprint.md` Information Architecture row for J-19, line 140). No new page, no nav-skeleton
change.

### Data-contract additions
None. This iteration fixes the CLIENT-SIDE derivation/rendering of the ALREADY-REGISTERED "Top-up
run records" row's `store_frozen_through_after` field (`state/blueprint.md` line 179, iter-32
addition) — the field's own computing module (`_pair_window` inside `desk_topup_compute.py`) and
serving endpoint (`GET /research/desk/topup/runs`, owned by `desk_topup_log.py`) are UNCHANGED and
byte-identical; only the frontend's display-time grouping of that already-served value is corrected.
No new displayed value, computing module, or serving endpoint is introduced. `state/blueprint.md`
gets one documentation-only "NOTED at iter-33" addendum (registered before the build, per the
iter-30 lesson) recording this fix — no new Data-Contract row, no nav-skeleton change.

## OUT OF SCOPE

- Any change to `_pair_window`, `run_topup`, `desk_topup_log.py`, or the stored shape/precision of
  `store_frozen_through`/`store_frozen_through_after` — the raw value is correct; only its display
  grouping was wrong.
- Any new Config field, endpoint, MCP tool, or ranked-table/Top-up-Runs-summary-table column.
- Re-verifying J-01..J-18 as an iteration goal (per "Do not redo" — J-08/J-11/J-13/J-14/J-15/J-16
  layout, J-12 addressability, and the rest stay carried-forward on already-valid evidence); only
  the five Required-still-passing journeys listed above are re-checked, because only they share this
  iteration's touched surface (`LatestTopupRunDetail`/the Top-up Runs section on `/desk`).
- Standing up any scoped/fixture rig for the walkthrough — record against the ambient `:3301`/`:8301`
  pair per the iter-27/28/31 lessons; the ambient store already carries the populated run J-19 needs
  to narrate.
- Owner-optional items already on file as non-blocking (iter-31's B1/F1/T3/demo scroll-anchor,
  iter-32's two prior wording notes) — none is this iteration's reason to exist.

## DEFINITION OF DONE

- [ ] Target journey J-19 passes via browser-qa-agent: the reach line and the (now-capped) earlier
  list are mutually consistent at calendar-day granularity, and its `[NEW]`-flagged demo-narrator
  walkthrough is recorded with distinct frames.
- [ ] Required-still-passing journeys J-04, J-07, J-09, J-16, J-17 remain green (deterministic
  replay + LLM fallback).
- [ ] No anti-goal violation introduced (copy-discipline lint green; single source of truth
  preserved — no second computation/endpoint for `store_frozen_through_after`; no new fetch/vendor
  call; append-only/immutable-data rails untouched).
- [ ] Unit tests pass; no regressions (full backend suite 0 failures; the extended guard test's
  seeded-violation counterparts prove each new assertion can fail).
- [ ] `journey-scripts/J-17.json` and `journey-scripts/J-19.json` refreshed to stable substrings and
  replay green against the current ambient store.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-33-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-19 (primary target — corrected reach line/earlier list, `[NEW]`-flagged walkthrough);
  J-04, J-07, J-09, J-16, J-17 (regression set, deterministic replay).
- Unit/integration: extend `test_desk_topup_library_reach_guard.py`; full backend suite green;
  fingerprint sentinel unchanged.
- Error cases: a legacy (pre-iter-32) run missing `store_frozen_through_after` still renders the
  honest fallback, never a guessed/backfilled date.

Test-first contract:

- TC-1: given two outcomes with `store_frozen_through_after` `"2026-07-30T00:00:00.000000Z"` and
  `"2026-07-30T16:00:00.000000Z"` (same calendar day, different exact time) and no other outcomes,
  when `topupLibraryReach` computes its result, then `newestCount` is 2 and `earlier` is an empty
  array.
- TC-2: given outcomes dated `"2026-07-30T00:00:00.000000Z"` (newest) and
  `"2026-07-27T00:00:00.000000Z"`, when `topupLibraryReach` computes its result, then `newestCount`
  is 1 and `earlier` contains exactly one entry, for the pair dated 2026-07-27.
- TC-3: given a run whose outcomes include more than 20 pairs whose calendar day is strictly earlier
  than the newest day, when `/desk`'s `LatestTopupRunDetail` renders, then the DOM contains at most
  20 elements with `data-testid="desk-topup-run-latest-reach-earlier-row"`, and the
  `desk-topup-run-latest-reach-earlier` heading states the TRUE total earlier count, not the shown
  count.
- TC-4: given the same over-20 case, when rendered, then one plain descriptive sentence discloses
  both the shown count and the true total (e.g. "showing 20 of 101"), containing no word from
  `tests/test_copy_discipline.py`'s banned lexicon.
- TC-5: given a run whose true earlier-count is ≤20 (e.g. 5), when rendered, then all 5 rows render
  and no "showing N of M" sentence appears.
- TC-6: given a legacy top-up run recorded before iter-32 (an outcome missing
  `store_frozen_through_after`), when `topupLibraryReach` runs, then it returns `null` and `/desk`
  renders the unchanged `LIBRARY_REACH_NOT_RECORDED` fallback text "library reach not recorded in
  this run".
- TC-7: given the ambient store's real latest top-up run (`topup-2026-07-31-8fb5c9a1f737`) after
  this iteration's fix, when captured in a browser screenshot at a 1440×900 viewport, then the reach
  line and the capped earlier-pairs section are both legible with no horizontal scroll, and no row
  in the rendered earlier list shares the same calendar day as the reach line's stated newest date.
- TC-8: given `test_desk_topup_library_reach_guard.py` extended this iteration, when run, then it
  asserts (a) a single shared day-truncation value feeds both the newest-extreme and the
  earlier-partition comparisons inside `topupLibraryReach`'s own source slice, and (b) a capping
  literal bounds the rendered earlier-row array, each with a seeded-violation counterpart that fails
  when the assertion's target pattern is absent.
- TC-9: given `runs/goal-session-desk/journey-scripts/J-19.json` refreshed this iteration, when
  replayed against the current ambient store, then all steps pass using stable substrings only
  ("reach it", "Pairs recorded earlier") with no pinned exact date/count/list-size.
- TC-10: given `runs/goal-session-desk/journey-scripts/J-17.json` refreshed this iteration, when
  replayed against the current ambient store (a run with 0 failed pairs), then all steps pass
  without asserting a "Failed pairs (14)" block or the now-superseded window-basis fallback text.
- TC-11: given `tests/test_copy_discipline.py`, when run after this iteration's wording changes,
  then it passes with zero new banned-lexicon matches.
- TC-12: given the full backend suite, when run after this iteration, then it passes with 0 failures
  and `Config().config_fingerprint()` is still `08e471b10130e1e2`.
- TC-13: given J-19's `[NEW]`-flagged demo-narrator walkthrough (owed since iter-32, `journey-
  history.json`'s `evidence_makeup: true`), when recorded this iteration at `Depth: full` against
  the SAME ambient `:3301`/`:8301` pair (no scoped rig), then the resulting frame files have
  distinct md5 hashes from one another and from any `J-*-verify.png`, and at least one frame
  legibly shows the corrected reach line plus the capped earlier-pairs list.
- TC-14: given every file in the zero-diff law (`bars.py`, `bar_index.py`, `desk_coverage.py`,
  `desk_screen.py`, `tradability.py`, `levels.py`, `routes.py`'s `record_bar_series`,
  `desk_topup_log.py`, `StructureChart.tsx`, the MCP surface), when this iteration's diff is
  reviewed, then none of those files shows a byte change and the MCP tool count stays exactly 17.

## NOTES

- Lesson applied (`lessons.md` iter-32): "any iteration whose evidence route triggers a real run
  against a 'latest run' panel ... must list the sibling scripts pinned to that panel and schedule
  their refresh in the SAME iteration" — this iteration does NOT trigger a new real top-up (no
  Top-up button click planned), but the display fix itself changes what the SAME already-recorded
  latest run renders, which is exactly why both `J-17.json` and `J-19.json` are refreshed here
  together rather than one at a time.
- Lesson applied (`lessons.md` iter-31 "The briefing/demo-narrator lanes"): the walkthrough is
  recorded against the ambient `:3301`/`:8301` pair, not a scoped rig — avoids the iter-27 teardown
  race and the iter-28 dead-`base_url` failure.
- Assumption logged to `runs/goal-session-desk/state/assumptions.md` (iter-33 — goal-decomposer):
  the exact cap (20 rows) and the frontend-only (no stored-precision change) scope of the fix are
  interpretive calls neither `docs/goal.md` nor the confirm dictate numerically.
- If the demo-narrator's walkthrough again produces duplicate frames despite running against the
  ambient pair, treat that as a NEW, separate defect to report — do not silently re-attempt within
  this same iteration's evidence budget.
