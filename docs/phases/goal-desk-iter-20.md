# Goal Iteration 20 — Close the two outstanding evidence gaps (J-12 full-page crop, J-13/J-14 walkthrough)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 20
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no — no code change; this iteration only re-opens already-shipped, already
  browser-verified pages to capture pictures the prior evaluations couldn't take.
- **Target journeys:** J-12, J-13, J-14
- **Required-still-passing journeys:** J-04, J-05, J-07
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
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
    market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
    with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
    bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
    interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
    `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
    engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening
    the mask follows the verification ladder in `trendora/project-extensions/host-guard/README.md`.
    *(critical)*

## GOAL

Close the session's two remaining owed pictures — a corrected full-page crop of J-12's earlier
same-day recording, and a `[NEW]`-flagged demo-narrator walkthrough over populated `/desk` rows that
narrates J-13's price/close disclosure and J-14's opposite-wall disclosure end to end — with zero
program change.

## BACKGROUND

Iteration 19 (verdict `GOAL_ACHIEVED`) fixed `_select_opposite_band` to be distance-first and proved
it against all 100 rows of a real recording, but was dispatched `lean`, so its own required
walkthrough never ran in-run (`reports/demo/goal-desk-iter-19/` does not exist on disk — confirmed).
Its next-step recommendation named exactly two still-owed pictures and asked for nothing else: "(2)
two pictures are still owed and change nothing in the program — the hover-hint photograph, which this
setup cannot take at all (ask for the hint's text to be read out instead; this is the third run that
clause has cost), and the guided walkthrough film over populated Desk rows, which also still owes the
older price/close film and the full-length picture of the earlier same-day recording." The hover-hint
photograph is structurally uncapturable in this rig (native HTML `title`, painted outside CDP's
screenshot surface — confirmed three times now, per `lessons.md` iter-19) and is explicitly OUT OF
SCOPE below; its text-read-from-DOM substitute is already proven and stays as-is. The other two —
the walkthrough and the J-12 full-page crop — are pure evidence-capture tasks over already-shipped,
already-passing surfaces (this session's own iter-19 spec already treated them as two SEPARATE
deliverables — one mandatory, one an optional rider — so this iteration keeps that same split rather
than reinterpreting it). Per the priority rubric's rule 7 exception (the prior evaluator's own
next-step asked ONLY for evidence on already-passing journeys), this iteration is written at
`Depth: evidence`, matching the evaluator's own binding recommendation. No escape condition holds:
the last verdict was `GOAL_ACHIEVED`/`CONTINUE` (not `ESCALATE`/`REGRESSION`), the last coherence
verdict was `COHERENCE-PASS`, the hardening cadence (6) is not due (1 consecutive lean iteration
dispatched), and there is no brand-new full-stack journey here.

**Scoped-rig lesson applied** (`lessons.md` iter-9/11/14/15/17/19; also `assumptions.md` iter-19): the
last several runs' evidence lanes wrote into the owner's real `apps/backend/.data` — most recently a
real 390-file price top-up and 4 new screens during iter-19. This iteration touches NOTHING but
already-recorded, read-only data (`screen-2026-07-27-936543601e75.json`,
`screen-2026-07-27-3ad3c57aa6ba.json`, `screen-2026-07-20-ca185294a384.json` — all confirmed present
on disk today), so there is no reason to read from the ambient store at all: copy the needed files
into a fresh scoped `.data/` tree, serve both processes against that copy, and prove the SERVING
process's own environment is scoped (`/proc/<pid>/environ`), not merely its port (`lessons.md`
iter-15/17) — never start a second `next dev` from `apps/frontend` while another runs (shared
`.next`; `rm -rf apps/frontend/.next` + rebuild before this scoped rig boots, per T-9).

## IN SCOPE

### Backend
- none — no code, config, or test change this iteration (`Depth: evidence`; capture-only).

### Frontend
- none — no `page.tsx` or component change this iteration; both surfaces already render everything
  needed (J-12's screen-history `?id=` selection since iter-16, J-13's `band` column since iter-17,
  J-14's `opposite` column since iter-18/corrected iter-19).

### Evidence capture (this iteration's actual deliverable)
- [ ] Build a fresh, isolated scoped copy of `apps/backend/.data` (universe + the three named screen
  files + their referenced bar series) under a throwaway directory; boot backend + frontend against
  it (fresh `.next` build); confirm via `/proc/<pid>/environ` that the serving backend's data-dir
  override points at the scoped copy, and via a direct `curl` to the scoped backend that a rendered
  value on `/desk` matches it byte-for-byte (the iter-17 lesson).
- [ ] On that scoped rig, open the earlier of J-12's two same-date recordings
  (`screen-2026-07-27-936543601e75`) via its screen-history `?id=` link on `/desk`, and capture a
  FULL-PAGE (not viewport-clipped) screenshot showing the NFLX ranked row's `1d` coverage badge and
  the page's own "... every timeframe badge dark" sentence together in one image.
- [ ] On the same scoped rig, open the fields-complete populated screen
  (`screen-2026-07-20-ca185294a384`, 100 ranked rows) on `/desk` and record a `[NEW]`-flagged
  demo-narrator walkthrough that narrates, end to end: (a) the ranked table's `band` column showing a
  row's recorded price range beside its `reference_close` (J-13), and (b) the `opposite` column
  showing a row's nearest-on-the-other-side wall with its side/class/price-range/distance (J-14) —
  every frame on `/desk`, never `/structure`.

### New user-facing capability
None — every capability being captured (screen-history `?id=` selection, the `band` column, the
`opposite` column) already shipped and was already browser-verified in prior iterations.

### New information displayed
None new — this iteration re-photographs already-recorded, already-registered fields
(`coverage`/`price_low`/`price_high`/`reference_close`/`opposite_band`); it introduces nothing.

### New user actions
None.

### UI surface changes
None — no `page.tsx` or component edit.

### Product surface delta
None. The product is unchanged by this iteration; only its evidence trail grows (one corrected
screenshot, one new walkthrough recording).

### Blueprint conformance
`/desk` (Desk section, per `blueprint.md`'s Information Architecture) — no new page, no nav-skeleton
change. `blueprint.md` already registers `coverage`, `band`/`reference_close` (iter-17), and
`opposite_band`/`bands_by_class` (iter-18/19) under their existing single owners
(`desk_coverage.py`/`desk_screen.py`) and single endpoints (`GET /research/desk/coverage`,
`GET /research/desk/screen`). A `NOTED at iter-20` documentation-currency entry has been appended to
`blueprint.md` (no new Data-Contract row, no nav-skeleton change) naming these two capture targets and
the scoped-copy discipline used to reach them.

### Data-contract additions
None — no new value, owner, or endpoint. This iteration reads exclusively from already-registered
Data-Contract rows (`GET /research/desk/screen?id=<id>` — the additive read param J-12 itself
registered at iter-16 — and the ranked-row fields J-13/J-14 already added).

## OUT OF SCOPE

- Re-attempting the hover-hint (`bands_by_class` tooltip) screenshot — this rig cannot photograph a
  native HTML `title` attribute (confirmed three separate runs); its DOM-text-read substitute already
  satisfies the underlying claim and is not re-opened here.
- Any change to `_select_best_band`, `_select_opposite_band`, `_row_rank_key`, `desk_screen.py`,
  `page.tsx`, or any test file — this is a capture-only iteration.
- Any real ~100-symbol top-up, real universe fetch, or real screen compute against
  `apps/backend/.data` — the scoped rig reads a COPY of already-recorded files only; nothing new is
  fetched or computed anywhere this iteration.
- Docs/goal.md's host-protection paragraph text tidy-up (iter-19 next-step item 3) — that is the
  owner's own documentation track, not a chain deliverable.
- Any new proposer-added journey, Desk-page-length reduction, history-row keyboard access, or run-
  table pagination — real, carried items from prior recommendations, but distinct from this
  iteration's two named captures; they ride whichever future iteration next touches `/desk`.

## DEFINITION OF DONE

- [ ] A fresh full-page screenshot of `screen-2026-07-27-936543601e75` shows the NFLX ranked row's
  `1d` coverage badge and the "... every timeframe badge dark" sentence together in one image, on the
  scoped rig described above.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough over `screen-2026-07-20-ca185294a384` records
  `Demo Verdict: RECORDED` (never `SKIPPED` or `RECORDED_WITH_NOTES`) with a non-empty gallery
  directory, narrating both the price/close disclosure (J-13) and the opposite-wall disclosure
  (J-14) end to end over `/desk`.
- [ ] J-12, J-13, J-14 remain `passing` (this iteration only strengthens their evidence; it does not
  re-open any behavioral clause already closed).
- [ ] Required-still-passing journeys (J-04, J-05, J-07) remain green via deterministic replay + LLM
  fallback.
- [ ] No anti-goal violation introduced — a `find apps/backend/.data -newer <iteration-start-marker>`
  check shows zero new or modified files under the ambient store.
- [ ] No production code, test, or config diff (`git diff` against the pre-iteration tree is empty
  outside `docs/`, `reports/`, and `runs/`).
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-20-dev.md` (records what was captured, on
  which scoped rig, and confirms zero production diff — the developer role this iteration is capture
  coordination, not code).

## TESTING REQUIREMENTS

- Browser: J-12 (re-capture), J-13 and J-14 (re-film, walkthrough only — their behavioral acceptance
  is already proven and is NOT re-tested here).
- Unit/integration: none new — the existing suite is expected to show zero diff and zero new
  failures; re-run it once to confirm (`Config().config_fingerprint()` still prints
  `08e471b10130e1e2`, tool count still exactly 17, `test_copy_discipline.py` still green).
- Error cases: none new — no new code path exists to reject invalid input.

Test-first contract:

- TC-1: given a fresh scoped copy of `apps/backend/.data` (universe file + the three named screen
  files + their referenced bar series) serving both backend and rebuilt frontend, when the serving
  backend process's own environment is inspected (e.g. `/proc/<pid>/environ`), then it shows a
  data-directory override pointing away from `apps/backend/.data`, and a value rendered on `/desk`
  matches a direct `curl` to that same scoped backend byte-for-byte.
- TC-2: given that scoped rig, when the earlier of J-12's two same-date recordings
  (`screen-2026-07-27-936543601e75`) is opened via its screen-history `?id=` link, then the resulting
  page state's NFLX ranked row shows a `1d` coverage badge and the page displays the sentence
  "... every timeframe badge dark" — both present on screen without further navigation.
- TC-3: given that same page state, when a full-page (not viewport-clipped) screenshot is captured,
  then the saved image contains both the NFLX row's `1d` badge and the "every timeframe badge dark"
  sentence in one frame.
- TC-4: given the scoped rig serving `screen-2026-07-20-ca185294a384` (100 ranked rows, every row
  carrying `reference_close`, `price_low`/`price_high`, `opposite_band`), when a demo-narrator step
  captures the ranked table's `band` column, then the recorded frame shows a row reading a price range
  together with its `reference_close` value.
- TC-5: given the same rig and screen, when a demo-narrator step captures the ranked table's
  `opposite` column, then the recorded frame shows a row naming a side, class, price range, and a
  basis-point distance value for the opposite-side wall.
- TC-6: given the demo-narrator run completes, then `reports/phase-goal-desk-iter-20-demo-results.md`
  states `Demo Verdict: RECORDED`, and its gallery directory (`reports/demo/goal-desk-iter-20/`)
  contains at least 2 non-empty PNG files.
- TC-7: given the iteration's file changes, when `git status`/`git diff` is inspected against the
  pre-iteration tree, then it shows changes ONLY under `docs/`, `reports/`, and `runs/` — zero diff to
  `apps/backend/app/`, `apps/frontend/`, or any test file.
- TC-8: given `apps/backend/.data`, when its contents are compared before and after this iteration
  (mtimes, file list, per-file checksums), then zero files are new, modified, or removed.
- TC-9: given the required-still-passing journeys (J-04, J-05, J-07), when their golden replay
  scripts run against the ambient rig, then all report PASS with no regression.
- TC-10: given the whole backend suite, when run once during this iteration, then it passes with
  zero failures, `Config().config_fingerprint()` prints `08e471b10130e1e2`, exactly 17 MCP tools are
  counted, and `tests/test_copy_discipline.py` passes unmodified.

## NOTES

- Binding "Do not redo" (from iteration-state.md, unless goal.md changed for these items — it has
  not): J-14 is COMPLETE (fields, storage, distance-first selection, render, tooltip line, tests, MCP
  proxy) — do not re-open the tie-break order. `_select_best_band` and `_row_rank_key` stay UNCHANGED.
  The `[NEW]` walkthroughs for J-09/J-10/J-11/J-12 are CORRECT — do not re-record them (this
  iteration's own walkthrough is a NEW recording for J-13/J-14 only, not a re-take of those four).
  Never write a screen/universe snapshot or run a top-up into `apps/backend/.data`; never start a
  second `next dev` from `apps/frontend` while another runs. Zero diff stays law for `engine/`,
  `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, both
  charts, `test_copy_discipline.py`; pin `08e471b10130e1e2`; exactly 17 MCP tools; no `/desk`
  "Universe ledger"; no CLI warmer.
- If the scoped copy of `apps/backend/.data` cannot reproduce the exact NFLX legibility issue (e.g.
  if a full-page capture trivially shows both elements without any special handling), that is a
  GOOD outcome, not a failure to report as a gap — simply record the successful full-page capture.
- The hover-hint photograph (J-14's `bands_by_class` tooltip) stays permanently unresolved AS A
  PHOTOGRAPH in this rig per `assumptions.md` iter-19's own reversibility note; if the owner wants it
  literally satisfied, the remedy is rewording that acceptance clause to "read out of the live DOM"
  or replacing the native `title` with an on-page popover — neither is requested by any open journey
  today, so neither is in scope here.
- `blueprint.md` gained a `NOTED at iter-20` documentation-currency entry (no new Data-Contract row,
  no nav-skeleton change) naming the two capture targets and the scoped-copy discipline.
