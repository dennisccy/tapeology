# Goal Iteration 21 — Record the still-owed J-13/J-14 walkthrough film (fix the malformed script)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 21
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no — no code change; this iteration only re-opens the already-shipped,
  already browser-verified `/desk` page to record the one artifact iteration 20 could not produce.
- **Target journeys:** J-13, J-14
- **Required-still-passing journeys:** J-04, J-05, J-07, J-12
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

Successfully record the still-owed `[NEW]`-flagged demo-narrator walkthrough over populated `/desk`
ranked rows — narrating J-13's price/close disclosure and J-14's opposite-wall disclosure end to
end — with zero program change, closing the `evidence_makeup` flags both journeys carry.

## BACKGROUND

Iteration 20 (verdict `CONTINUE`, `Depth: evidence`) closed J-12's outstanding full-page crop but its
own walkthrough attempt failed silently: `reports/phase-goal-desk-iter-20-demo.json` embedded three
JavaScript regex literals (`/screen.history/i` at line 28, `/scroll.*band/i` at line 64,
`/scroll.*opposite/i` at line 76) where the schema requires plain JSON strings, so the whole script was
unreadable, `demo_runner` wrote `Demo Verdict: SKIPPED`, and `reports/demo/goal-desk-iter-20/` was left
empty. Its own next-step recommendation named exactly this fix: "write the click targets as ordinary
quoted text, and express the sideways reveal of the two right-hand columns as a sideways scroll of the
table rather than a click on a button that does not exist … treating 'SKIPPED' as a failure rather than
a note." I read `scripts/automation/lib/demo_runner.py` directly before writing this spec: its action
vocabulary is exactly `{"goto", "click", "fill", "expect", "wait_for"}` (`:36`) — there is no scroll
primitive, so a literal "sideways scroll" action cannot be authored without a tooling code change, which
`Depth: evidence` explicitly excludes. Worse, every ranked row on `/desk`
(`apps/frontend/app/desk/page.tsx:335-427`, `data-testid="desk-screen-row"`) is covered end-to-end by
one stretched `next/link` anchor (`desk-row-drill-in`, `position: absolute; inset: 0` relative to the
row) that navigates to `/structure` — a `click` on ANY cell in a ranked row, including `desk-row-band`
or `desk-row-opposite`, would silently navigate away rather than reveal anything. This spec resolves
that tension (see `assumptions.md` iter-21): narrate the two disclosures through accurate text
(`narration`/`point_out`) and `expect` assertions on the row's own recorded values, never a click-driven
reveal, since goal.md's own pixel-legibility requirement for both columns is a SEPARATE conjunct already
satisfied by the existing browser-QA screenshots (iter-19/20's independently re-verified evidence), not
by this walkthrough's own frames.

Per the priority rubric's rule 7 exception (the prior evaluator's own next-step asked ONLY for evidence
on already-passing journeys), this iteration is written at `Depth: evidence`, matching the evaluator's
own binding recommendation for iteration 21. No escape condition holds: the last verdict was
`CONTINUE` (not `ESCALATE`/`REGRESSION`), the last coherence verdict was `COHERENCE-PASS`
(`runs/goal-session-desk/iter-20/coherence.md`), the hardening cadence (6) is not due (2 consecutive
lean/evidence iterations dispatched), and there is no brand-new full-stack journey here.

**Scoped-rig lesson applied, again** (`lessons.md` iter-9/11/14/15/17/19; also `assumptions.md`
iter-19): iteration 20's own spec required a scoped, isolated copy of `apps/backend/.data`, but its
execution served from the owner's real store anyway (disclosed as read-only, but still against its own
plan — the fifth run in a row to do so). This iteration repeats the same instruction with the same
concrete proof requirement (serving-process environment check + a direct-`curl` byte match against the
rendered page) so the deviation does not recur a sixth time.

## IN SCOPE

### Backend
- none — no code, config, or test change this iteration (`Depth: evidence`; capture-only).

### Frontend
- none — no `page.tsx` or component change this iteration; `/desk` already renders everything needed
  (J-13's `band` column since iter-17, J-14's `opposite` column since iter-18/corrected iter-19).

### Evidence capture (this iteration's actual deliverable)
- [ ] Author `reports/phase-goal-desk-iter-21-demo.json` as valid JSON only — every `target.name` /
  `target.text` / `target.css` value is a plain quoted string, never a `/regex/` literal — and
  parse-check it with `python3 scripts/automation/lib/demo_runner.py --json <path> --mode lint`
  before any record run. Treat a non-empty lint-error list, or a resulting `Demo Verdict: SKIPPED`, as
  a hard failure of this iteration, not a note to carry forward again.
- [ ] Do not model the sideways reveal of the `band`/`opposite` columns as any click: narrate both
  disclosures through accurate `narration`/`point_out` text and `expect` text assertions on the row's
  own recorded values, and do not target a click on any element inside a `desk-screen-row` (its whole
  row is one stretched `next/link` anchor to `/structure` — see BACKGROUND).
- [ ] Build a fresh, isolated scoped copy of `apps/backend/.data` (the universe file +
  `screen-2026-07-20-ca185294a384.json` + its referenced bar series) under a throwaway directory; boot
  backend + frontend against it (fresh `.next` build, per T-9); confirm via the serving backend
  process's own environment that its data-directory override points away from `apps/backend/.data`,
  and via a direct `curl` to that scoped backend that a rendered `/desk` value matches it byte-for-byte.
- [ ] On that scoped rig, open the fields-complete populated screen `screen-2026-07-20-ca185294a384`
  (100 ranked rows, every row carrying `reference_close`, `price_low`/`price_high`, `opposite_band`)
  on `/desk`, and record a `[NEW]`-flagged demo-narrator walkthrough narrating, end to end: (a) the
  ranked table's `band` column — a row's own `price_low`–`price_high` range beside its
  `reference_close` (J-13); and (b) the `opposite` column — a row's nearest wall on the other side of
  price, with its side/class/price-range/distance (J-14). Every frame stays on `/desk` — never
  `/structure`.

### New user-facing capability
None — every capability being narrated (the `band` column, the `opposite` column) already shipped and
was already browser-verified in prior iterations.

### New information displayed
None new — this iteration narrates already-recorded, already-registered fields
(`reference_close`/`price_low`/`price_high`/`opposite_band`); it introduces nothing.

### New user actions
None.

### UI surface changes
None — no `page.tsx` or component edit.

### Product surface delta
None. The product is unchanged by this iteration; only its evidence trail grows (one new walkthrough
recording).

### Blueprint conformance
`/desk` (Desk section, per `blueprint.md`'s Information Architecture) — no new page, no nav-skeleton
change. `blueprint.md` already registers `band`/`reference_close` (iter-17) and
`opposite_band`/`bands_by_class` (iter-18/19) under their existing single owner (`desk_screen.py`) and
single serving endpoint (`GET /research/desk/screen`). A `NOTED at iter-21` documentation-currency
entry has been appended to `blueprint.md` (no new Data-Contract row, no nav-skeleton change) naming
this capture target, the malformed-script root cause, and the scoped-copy discipline used to reach it.

### Data-contract additions
None — no new value, owner, or endpoint. This iteration reads exclusively from already-registered
Data-Contract rows (the ranked-row fields J-13/J-14 already added to "Screen snapshots, rank rows,
skip rows").

## OUT OF SCOPE

- Re-attempting the hover-hint (`bands_by_class` tooltip) screenshot — this rig cannot photograph a
  native HTML `title` attribute (confirmed three separate runs, `lessons.md` iter-19); its DOM-text-read
  substitute already satisfies the underlying claim and is not re-opened here. This is a HUMAN-owned
  decision (reword the acceptance clause, or add an on-page panel) — not re-planned per rule 6.
- Any change to `_select_best_band`, `_select_opposite_band`, `_row_rank_key`, `desk_screen.py`,
  `page.tsx`, or any test file — this is a capture-only iteration. If a genuinely non-navigating,
  non-scroll way to satisfy the walkthrough turns out not to exist, that is escalated in the results
  report (and, if needed, becomes a small future lean-depth `demo_runner.py` tooling change per
  `assumptions.md` iter-21's reversibility note) — never patched in place during this run.
- Any real ~100-symbol top-up, real universe fetch, or real screen compute against
  `apps/backend/.data` — the scoped rig reads a COPY of an already-recorded file only; nothing new is
  fetched or computed anywhere this iteration.
- `docs/goal.md`'s host-protection paragraph text tidy-up (a carried owner-track item) — not a chain
  deliverable.
- Desk-page length reduction, history-row keyboard access, or run-table pagination — real, carried
  items from prior recommendations, but distinct from this iteration's one named capture; they ride
  whichever future iteration next touches `/desk`.

## DEFINITION OF DONE

- [ ] The `[NEW]`-flagged demo-narrator walkthrough over `screen-2026-07-20-ca185294a384` records
  `Demo Verdict: RECORDED` (never `SKIPPED`; `RECORDED_WITH_NOTES` acceptable only if every note is
  non-blocking selector brittleness, the iter-17 precedent) with a non-empty gallery directory under
  `reports/demo/goal-desk-iter-21/`.
- [ ] The walkthrough's steps narrate both J-13's band/close disclosure and J-14's opposite-wall
  disclosure, end to end, entirely on `/desk` (no step navigates to `/structure`).
- [ ] The recording ran on a fixture-scoped rig proven isolated from the owner's ambient
  `apps/backend/.data` (serving-process environment check + a direct-`curl` byte match), and that
  ambient store shows zero new/modified/removed files after the run.
- [ ] J-13 and J-14 remain `passing`, with their `evidence_makeup` flags able to clear (no behavioral
  clause is reopened).
- [ ] Required-still-passing journeys (J-04, J-05, J-07, J-12) remain green via deterministic replay +
  LLM fallback.
- [ ] No anti-goal violation introduced.
- [ ] No production code, test, or config diff (`git diff` against the pre-iteration tree is empty
  outside `docs/`, `reports/`, and `runs/`).
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-21-dev.md` (records what was captured, on
  which scoped rig, and confirms zero production diff — the developer role this iteration is capture
  coordination, not code).

## TESTING REQUIREMENTS

- Browser: J-13 and J-14 (walkthrough only — their behavioral acceptance is already proven and is NOT
  re-tested here); J-04, J-05, J-07, J-12 (regression replay).
- Unit/integration: none new — the existing suite is expected to show zero diff and zero new failures;
  re-run it once to confirm (`Config().config_fingerprint()` still prints `08e471b10130e1e2`, tool
  count still exactly 17, `test_copy_discipline.py` still green).
- Error cases: none new — no new code path exists to reject invalid input; the one "invalid input" this
  iteration guards against is a malformed demo script, caught by the parse-check (TC-1) rather than
  allowed to silently produce `SKIPPED`.

Test-first contract:

- TC-1: given the authored demo script `reports/phase-goal-desk-iter-21-demo.json`, when it is
  parse-checked via `python3 scripts/automation/lib/demo_runner.py --json
  reports/phase-goal-desk-iter-21-demo.json --mode lint`, then the lint reports zero errors (valid
  JSON, every `target` value a plain string, every `action.type` inside `{goto, click, fill, expect,
  wait_for}`).
- TC-2: given a fresh scoped copy of `apps/backend/.data` (universe file + `screen-2026-07-20-
  ca185294a384.json` + its referenced bar series) serving both a rebuilt frontend and backend, when the
  serving backend process's own environment is inspected, then it shows a data-directory override
  pointing away from `apps/backend/.data`, and a value rendered on `/desk` matches a direct `curl` to
  that same scoped backend byte-for-byte.
- TC-3: given that scoped rig with `screen-2026-07-20-ca185294a384` loaded on `/desk`, when the
  demo-narrator record run executes the parse-checked script, then
  `reports/phase-goal-desk-iter-21-demo-results.md` states `Demo Verdict: RECORDED` and
  `reports/demo/goal-desk-iter-21/` contains at least 2 non-empty PNG files.
- TC-4: given the recorded walkthrough, when its J-13 step's narration/point_out text and captured
  frame are reviewed, then they state a specific ranked row's `price_low`–`price_high` range together
  with its `reference_close`, matching that row's value in the scoped snapshot on disk.
- TC-5: given the recorded walkthrough, when its J-14 step's narration/point_out text and captured
  frame are reviewed, then they state a specific ranked row's opposite-wall side, class, price range,
  and basis-point distance, matching that row's `opposite_band` value in the scoped snapshot on disk.
- TC-6: given every step in the authored script, when its `action.target` is inspected, then no `click`
  action targets any element inside a `desk-screen-row` (no `css`/`role`/`text` resolves to
  `desk-row-band`, `desk-row-opposite`, or any other ranked-row cell), so no step navigates away from
  `/desk`.
- TC-7: given the iteration's file changes, when `git status`/`git diff` is inspected against the
  pre-iteration tree, then it shows changes only under `docs/`, `reports/`, and `runs/` — zero diff to
  `apps/backend/app/`, `apps/frontend/`, or any test file.
- TC-8: given `apps/backend/.data`, when its contents are compared before and after this iteration
  (mtimes, file list, per-file checksums), then zero files are new, modified, or removed.
- TC-9: given the required-still-passing journeys (J-04, J-05, J-07, J-12), when their golden replay
  scripts run against the ambient rig, then all report PASS with no regression.
- TC-10: given the whole backend suite, when run once during this iteration, then it passes with zero
  failures, `Config().config_fingerprint()` prints `08e471b10130e1e2`, exactly 17 MCP tools are
  counted, and `tests/test_copy_discipline.py` passes unmodified.

## NOTES

- Binding "Do not redo" (from iteration-state.md, unless goal.md changed for these items — it has
  not): J-12 is COMPLETE INCLUDING ITS PICTURES — do not re-capture it. J-13/J-14 are COMPLETE IN
  CODE (fields, distance-first selection, render, tooltip line, tests, MCP proxy) — do not re-open the
  tie-break order, `_select_best_band`, or `_row_rank_key`. Only the FILM is owed. Never photograph a
  native `title` tooltip in this rig. Never write a screen/universe snapshot or run a top-up into
  `apps/backend/.data`; never start a second `next dev` from `apps/frontend` while another runs. Zero
  diff stays law for `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `desk_coverage.py`, both charts, `test_copy_discipline.py`; pin `08e471b10130e1e2`; exactly 17 MCP
  tools; no `/desk` "Universe ledger"; no CLI warmer.
- Interpretation call logged in `assumptions.md` iter-21: the walkthrough's own frames are not required
  to visually reveal the `band`/`opposite` columns scrolled into view — that pixel-legibility
  requirement is a separate conjunct already satisfied by existing browser-QA screenshots. Narrate
  accurately over populated data instead of chasing a scroll action that does not exist in
  `demo_runner.py` and would require a click that navigates away from `/desk`.
- The hover-hint photograph (J-14's `bands_by_class` tooltip) stays permanently unresolved AS A
  PHOTOGRAPH in this rig per `assumptions.md` iter-19's own reversibility note; if the owner wants it
  literally satisfied, the remedy is rewording that acceptance clause to "read out of the live DOM" or
  replacing the native `title` with an on-page popover — neither is requested by any open journey
  today, so neither is in scope here.
- `blueprint.md` gained a `NOTED at iter-21` documentation-currency entry (no new Data-Contract row, no
  nav-skeleton change) naming the malformed-script root cause and the scoped-copy discipline.
- If this run's evidence lane again fails to use a genuinely scoped copy (the fifth-in-a-row deviation
  iteration 20's own evaluator log disclosed), that is a process failure to flag explicitly in the
  results report — the spec's own instruction has not changed and does not need to.
