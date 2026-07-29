# Goal Iteration 19 — Fix the opposite-wall selection to be nearest-by-distance, and re-film J-14/J-13

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 19
- **Mode:** next
- **Depth:** full
- **Full trigger:** 2 — this iteration changes the COMPUTED CONTENT of the already-registered
  `opposite_band` Data-Contract field (its selection tie-break order) inside its sole owner
  `desk_screen.py`; per this session's own iter-13/14/17/18 precedent, any content-computation
  change to a persisted, registered Data-Contract row is dispatched full, and its acceptance also
  names a `[NEW]`-flagged demo-narrator walkthrough (the iter-12 lesson: a `lean`-dispatched
  iteration cannot close a walkthrough clause within its own run because the demo-narrator lane
  runs AFTER the goal-evaluator at `lean` depth).
- **Frontend Present:** no — the frontend already renders whatever `opposite_band` the backend
  records; no `page.tsx` code change is needed, only browser re-verification and re-filming.
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-03, J-04, J-05, J-06, J-07, J-08, J-11, J-12, J-13
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated,
    checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of,
    fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in
    place, or rewritten — a new run is a new snapshot. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
    advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
    "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
    surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
    future era). *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
    test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted
    unchanged by the sentinel every iteration. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable,
    widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
    the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Make the `/desk` ranked table's `opposite` column name the wall genuinely NEAREST to price on the
other side, not the best-graded one, closing iter-18's 2-of-63-real-row divergence and re-filming the
walkthrough over populated rows so both J-14's and iter-17's carried J-13 evidence gaps close in one
recording.

## BACKGROUND

Iter-18 shipped `opposite_band`/`bands_by_class` fully — stored, byte-identical to
`compute_tradability`, rendered, tested — but `_select_opposite_band` (`desk_screen.py:269`)
delegates to `_select_best_band`, whose tie-break tuple is `(class rank DESCENDING, distance_bps
ascending, quality_score descending)`. `docs/goal.md` J-14 step 1 states the opposite-band order
literally: "distance ascending, then class rank descending (`_CLASS_RANK`, `desk_screen.py:121` — an
unclassified band ranks lowest, never highest), then `band_score` descending, resolved by `min`'s
first-of-tie stability over `compute_tradability`'s own served order." The iter-18 evaluator measured
both rules against the owner's real 63-row screen and found 2 rows diverge: HONA (shipped class A at
336.96 bps vs. the nearer class B at 153.67 bps) and META (class A at 232.58 bps vs. the nearer class
C at 92.05 bps) — logged as an interpretation call in `assumptions.md` iter-18, "We chose: Read
DISTANCE-first as the requirement," and scored J-14 `partial`, verdict `CONTINUE`, next-step: "make
the opposite column show the CLOSEST wall on the other side... a one-rule change... its stored
comparisons, and the two comments that already claim 'nearest'." This iteration implements exactly
that. It also carries the walkthrough: iter-18's own `[NEW]`-flagged film shows `/structure`, not
`/desk`, in 3 of 6 frames and the new column in none — goal.md's own J-14 acceptance text says the
re-film "also closes iter-17's `RECORDED_WITH_NOTES` capture gap" (J-13's walkthrough, which narrated
the legacy pre-close-disclosure state only). One re-film over freshly-computed, populated `/desk` rows
closes both.

**Lesson applied (`lessons.md` iter-18, "Applies to: any `desk_screen.py` band-selection change"):**
the prior spec's OWN paraphrase of this exact rule silently overrode the goal text and shipped past
five green lanes. This spec therefore quotes goal.md's rule verbatim below rather than re-paraphrasing
it, and requires re-measuring against real/fixture multi-row data (TC-5/TC-6), not the fixture alone.

**Scoped-rig lessons applied** (`lessons.md` iter-9/11/14/15/17): use a fixture-scoped rig for every
compute and every capture (never the ambient `apps/backend/.data`); prove the SERVING process's own
environment is scoped (`/proc/<pid>/environ`), not just its port; never start a second `next dev`
from `apps/frontend` while another runs (shared `.next` cross-contaminates the API base — cross-check
one rendered value against a direct `curl`); `rm -rf apps/frontend/.next` + rebuild before any browser
pass (T-9).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_screen.py`: give `_select_opposite_band` its OWN tie-break key
  — distinct from `_select_best_band`'s — implementing goal.md J-14 step 1 verbatim: **"distance
  ascending, then class rank descending (`_CLASS_RANK` — an unclassified band ranks lowest, never
  highest), then `band_score` descending, resolved by `min`'s first-of-tie stability over
  `compute_tradability`'s own served order."** `_select_best_band` (the row's own same-side
  selection) and `_row_rank_key` (the cross-symbol rank order) are UNCHANGED — this is a one-key
  edit to `_select_opposite_band` alone.
- [ ] Update `desk_screen.py`'s own module-docstring description of the opposite-band tie-break
  order (the "Opposite-band disclosure (goal-desk-iter-18, J-14)" section, currently describing
  "the IDENTICAL (class rank DESCENDING, distance_bps ascending, quality_score descending) tuple")
  to match the corrected order, tagged as a goal-desk-iter-19 correction per this file's own
  per-iteration docstring convention.
- [ ] `apps/backend/tests/test_desk_screen.py`: flip
  `test_select_opposite_band_prefers_higher_class_over_closer_distance` to assert the corrected
  distance-first behavior (rename to reflect it), and re-verify/update every other assertion whose
  expected `opposite_band` value depends on the old rule — including the golden near/far/null-class
  fixture test (`test_opposite_band_golden_near_far_and_null_class_rows`) and the byte-identical-
  recompute and legacy-row-absence tests, none of which change SHAPE, only the selected band on
  fixture rows where the two rules disagree.
- [ ] `apps/backend/tests/test_mcp_server.py`: re-verify and, where the fixture's opposite-side
  divergence changes it, update the specific `opposite_band` values asserted in
  `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` — the proxy contract
  itself (byte-identity between `GET /research/desk/screen`, the `desk_screen` MCP tool, and
  `get_endpoint`) is unchanged.
- [ ] Verify the fix against real (or fixture-scoped multi-row-equivalent) data reproducing the
  exact HONA/META divergence the evaluator measured, on a fixture-scoped rig (never
  `apps/backend/.data`) — record the comparison in the dev handoff.

### New user-facing capability
None — the `opposite` column and its tooltip already exist (iter-18); this iteration corrects which
band that column names.

### New information displayed
None new — same two fields (`opposite_band`, `bands_by_class`), corrected selection.

### New user actions
None.

### UI surface changes
None — no `page.tsx` edit; the frontend already renders whatever the backend serves.

### Product surface delta
On every NEW screen computed after this fix, the `opposite` column names the wall genuinely closest
to price on the other side rather than the best-graded one on that side — closing the exact
divergence a discretionary trader would otherwise be misled by (a 336.96-bps wall shown as "the
opposite wall" when a 153.67-bps wall exists, and similarly for META). Legacy-recorded rows and rows
where both rules already agree are unaffected.

### Blueprint conformance
`/desk` (Desk section) — no new page, no nav-skeleton change. `blueprint.md`'s Data Contract row
"Screen snapshots, rank rows, skip rows" already registers `opposite_band`/`bands_by_class` under
`desk_screen.py` / `GET /research/desk/screen`; a "NOTED at iter-19" entry has been appended
documenting the selection-rule correction (no new row, no new owner, no new endpoint).

### Data-contract additions
None — `opposite_band`/`bands_by_class`'s shape, owner (`desk_screen.py`), and serving endpoint
(`GET /research/desk/screen`) are all unchanged from iter-18; only the selection RULE that decides
which band populates `opposite_band` on NEW rows is corrected.

## OUT OF SCOPE

- Any change to `_select_best_band` (the row's own same-side selection) or `_row_rank_key`
  (cross-symbol rank order) — both stay byte-unchanged; this journey discloses, it never re-ranks.
- Any change to `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, or
  `desk_coverage.py` — zero diff, verified.
- Any new `Config` field, new store, new endpoint, or new MCP tool — the 17-tool contract and the
  `08e471b10130e1e2` fingerprint pin are unaffected by construction.
- Backfilling `opposite_band`/`bands_by_class` on legacy-recorded rows or pre-fix snapshots — the
  append-only rail means every already-recorded snapshot keeps exactly what it recorded; `/desk`'s
  existing legacy-absence copy is unchanged.
- J-12's separately carried "one full-length picture of the earlier same-day recording" gap and the
  general Desk-page-length / history-row-keyboard-access items from prior `Next-step recommendation`s
  — real, but distinct from this iteration's scope; they may ride the make-up lane on whichever future
  iteration next touches `/desk`, not this one.
- Any new proposer-added journey — this is a corrective pass on the already-open J-14, not a new
  enhancement cycle.

## DEFINITION OF DONE

- [ ] J-14 passes via browser-qa-agent — `/desk`'s `opposite` column shows the corrected,
  distance-first opposite wall, with both a within-25-bps row and a beyond-1,000-bps row legible in
  one screenshot, plus a tooltip screenshot showing `bands_by_class`.
- [ ] Required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-08, J-11, J-12, J-13) remain
  green via deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced — single-source-of-truth, append-only, and fingerprint-pin
  rails all hold; zero diff to every named frozen module.
- [ ] Unit tests pass; `_select_opposite_band`'s corrected rule is proven by an updated, passing
  `test_desk_screen.py` suite, with `_select_best_band`'s own suite passing byte-unmodified.
- [ ] The corrected rule is verified against real (or fixture-scoped multi-row-equivalent) data
  reproducing the HONA/META divergence the iter-18 evaluation measured.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough narrates the opposite-wall disclosure end to end
  over POPULATED `/desk` rows (never `/structure`), closing both J-14's own gap and iter-17's carried
  J-13 `RECORDED_WITH_NOTES` gap.
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-19-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-14 (`/desk` opposite column + tooltip, on a fixture-scoped rig after `rm -rf
  apps/frontend/.next` + rebuild); regression smoke across J-03/J-04/J-05/J-06/J-07/J-08/J-11/J-12/
  J-13 via saved-script replay.
- Unit/integration: `_select_opposite_band`'s corrected tie-break order (near/far/null-class/tie
  cases), `_select_best_band`'s unchanged behavior, the golden screen fixture, the append-only
  identical-pins re-run, the MCP proxy byte-identity, the whole backend suite + fingerprint +
  copy-discipline lint.
- Error cases: opposite-side-empty still returns an honest `None`; a legacy row (recorded before
  iter-18) still serves `opposite_band`/`bands_by_class` entirely absent, never backfilled.

Test-first contract:

- TC-1: given a bands list containing the row's own selected band plus a close-but-lower-class
  opposite-side band and a farther-but-higher-class opposite-side band, when
  `_select_opposite_band` is called, then it returns the closer band, not the higher-class one.
- TC-2: given a bands list with two exactly-tied opposite-side bands, when `_select_opposite_band`
  is called with the list in each of the two possible orders, then each call returns that order's
  own first-served item, and repeated calls on the same order return the identical item every time.
- TC-3: given a bands list where every band shares the row's own selected side, when
  `_select_opposite_band` is called, then it returns `None`.
- TC-4: given `test_desk_screen.py`'s golden near/far/null-class fixture rows, when the screen is
  recomputed under the corrected rule, then each row's `opposite_band` matches the fixture's own
  nearest-by-distance opposite-side band, and no test in the file still asserts the pre-fix
  class-first selection.
- TC-5: given a freshly computed screen on the fixture-scoped rig for a screen date not already
  recorded under the same five pins, when each ranked row's `opposite_band` is compared against
  `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s own `bands` list,
  then `side`/`band_class`/`price_low`/`price_high`/`band_score` are byte-identical to that list's
  smallest-`_distance_bps` band on the opposite side, and `distance_bps` reproduces the same formula
  the row's own `distance_bps` already uses.
- TC-6: given the real (or fixture-scoped multi-row-equivalent) screen the iter-18 evaluation
  measured, when HONA's and META's rows are inspected, then HONA's `opposite_band` reports the
  nearer class-B band (~153.67 bps) rather than the farther class-A band (~336.96 bps), and META's
  reports the nearer class-C band (~92.05 bps) rather than the farther class-A band (~232.58 bps).
- TC-7: given `_select_best_band`'s own existing unit-test suite, when the full suite runs after
  the fix, then every one of those tests passes unmodified.
- TC-8: given a screen recomputed under the SAME five pins as an already-recorded snapshot, when the
  compute is triggered again, then it returns the existing snapshot unchanged rather than writing a
  second file.
- TC-9: given the cross-symbol ranked-row order (`_row_rank_key`) before and after the fix under
  identical pins, when the two are compared, then they are byte-identical.
- TC-10: given the MCP `desk_screen` tool and `get_endpoint`'s `/research/desk/screen` proxy, when
  both are queried against the same fixture screen post-fix, then each returns
  `opposite_band`/`bands_by_class` byte-identical to `GET /research/desk/screen`'s own response, and
  the MCP contract suite still counts exactly 17 tools.
- TC-11: given the whole backend suite, when run after the fix, then it passes with zero failures,
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, and `tests/test_copy_discipline.py`
  passes unmodified.
- TC-12: given `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py`, when diffed against the pre-iteration tree, then each shows zero changes.
- TC-13: given `/desk` after a `rm -rf apps/frontend/.next` rebuild on a fixture-scoped rig with a
  freshly computed screen, when viewed in a real browser, then the ranked table's `opposite` column
  shows at least one row with `distance_bps` within 25 bps and one with `distance_bps` beyond 1,000
  bps, both legible in one screenshot, plus a second screenshot of a row's hover tooltip showing its
  `bands_by_class` line.
- TC-14: given a `[NEW]`-flagged demo-narrator walkthrough recorded against that same populated
  `/desk` rig, when the recording is reviewed, then every step narrates the opposite-wall disclosure
  over the populated ranked rows, never `/structure`, closing both J-14's own walkthrough clause and
  iter-17's carried J-13 `RECORDED_WITH_NOTES` gap.

## NOTES

- Binding "Do not redo" (from iteration-state.md, unless goal.md changed for these items — it has
  not): J-14's fields/storage/render/tests/MCP proxy are DONE and verified
  (`_select_opposite_band`, `_bands_by_class`, `lib/types.ts`, `app/desk/page.tsx` opposite cell +
  tooltip line, `test_desk_screen.py`, `test_desk_ui_guards.py`, `test_mcp_server.py`) — only the
  ORDER inside `_select_opposite_band` is open. Do not re-add fields, do not touch `page.tsx`. The
  `[NEW]` walkthroughs for J-09/J-10/J-11/J-12 are CORRECT — do not re-record them. Never write a
  screen/universe snapshot into `apps/backend/.data`. No `/desk` "Universe ledger" section; no CLI
  warmer for the new fields. No legacy backfill; `_row_rank_key` unmoved; zero diff to every
  protected module, `config.py` and `engine/` included. Never start a second `next dev` from
  `apps/frontend` while the ambient one runs (shared `.next`).
- If the fix genuinely finds zero real-data divergence once implemented (i.e. the two rules turn out
  to agree everywhere on the specific rig used for TC-5/TC-6), that is a surprising result worth
  flagging in the dev handoff and the assumption ledger rather than silently treated as "done" — the
  iter-18 evaluator's own measurement (2 of 63 real rows) is the standard this iteration is held to.
- If evidence capture time allows, a rider (not a DoD requirement) is welcome: one full-page capture
  of the earlier same-day Screen History recording that would close J-12's separately carried gap —
  only if it does not risk or delay this iteration's own DoD.
