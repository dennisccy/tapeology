# Goal Iteration 31 — Land the two dropped J-18 honesty fixes, revert the polluted build files, and correct the blueprint

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 31
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iter-30) was `ESCALATE`, a mandatory full-depth trigger with
  no exceptions; the engine's own binding depth recommendation for this iteration is independently
  `full`.
- **Frontend Present:** yes
- **Target journeys:** J-18
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
    append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
    bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
    rewritten — a new run is a new snapshot. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
    fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
    honestly (run-or-not-run), never CI gates. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY
    inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys,
    this Anti-goals section, or any other part of this file; proposed journeys MUST carry a
    single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
    `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
    journey just to keep the loop alive is a failure. *(critical)*
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

Land the two small honesty/UX fixes iteration 30's own spec ordered but its depth-downgrade
dropped (a reused screen run no longer shows a misleading amber "members not reached" warning
plus a row of zero counts; a run that crashes before attempting any member no longer names a
symbol it never touched), add their tests, revert the two tracked frontend build files iteration
30's scoped rig polluted, and correct this session's blueprint entry that wrongly claimed those
fixes had already shipped.

## BACKGROUND

Iteration 30 was ESCALATEd, not because the product misbehaves, but because the engine dispatched
that iteration's `Depth: lean` spec at `evidence` instead — no developer ran, so none of its three
planned code/test changes landed, while `state/blueprint.md`'s own "NOTED at iter-30" entry
asserted (in the past tense) that they had shipped. The evaluator recorded this as a MINOR
unresolved anti-goal violation (two tracked build files — `apps/frontend/next-env.d.ts`,
`apps/frontend/tsconfig.json` — left pointing at a scratchpad directory the scoped rig's teardown
then deleted) and returned `ESCALATE` under the verdict tree's "a shallow iteration surfaced an
issue warranting the full pipeline" clause, naming exactly five follow-ups. This iteration is a
full-pipeline dispatch (mandatory: `lessons.md` iter-30 records that a `full` recommendation
WITHOUT the engine actually dispatching `full` silently drops IN SCOPE work — the same failure
mode this iteration exists to fix — and the prior verdict was `ESCALATE`, which forces `full` with
no exceptions per the depth-binding rule). Verified directly before writing this spec (not
assumed): `apps/backend/app/research/desk_screen_compute.py:277` still sets
`failed_member = members[0]` when `attempted == 0`, `apps/frontend/app/desk/page.tsx`'s
`LatestScreenRunDetail` still renders `desk-screen-run-latest-unreached`/
`desk-screen-run-latest-counts` unconditionally for a reused done run, and both
`next-env.d.ts`/`tsconfig.json` are still committed (HEAD `48c5fc2`) with the dangling
`/home/.../scratchpad/iter30-rig/...` path/glob — confirming all three items are still genuinely
open, matching `state/iteration-state.md`'s "Active blockers". `blueprint.md`'s mis-stated
iter-30 entry has been corrected as part of writing this spec (see NOTES), consistent with
`lessons.md` iter-30's rule to never claim shipped in the past tense before the code lands.

Per the priority rubric: no journey is regressed or `unknown` (rule 1 N/A); the last coherence
verdict was not `COHERENCE-FAIL` (rule 2 N/A — it was `COHERENCE-WARN`, already reflected in the
blueprint correction); this is squarely an "unblocker" pass (rule 3) — it closes the exact items
the evaluator named as blocking `GOAL_ACHIEVED` re-confirmation, all touching the ALREADY-BUILT
J-18 surface, so no new journey is targeted. The `[NEW]`-flagged walkthrough film (still one
duplicated image across four frames, per `reports/demo/goal-desk-iter-29/`) rides along as a
non-blocking passenger per the iter-30 evaluator's own explicit bound ("last time I ask" —
`runs/goal-session-desk/iter-30/eval.md`); it is NOT this iteration's goal and NOT a
`DEFINITION OF DONE` item (methodology A.7: a missing/duplicated walkthrough capture must never be
scored as blocking or become an iteration's goal).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_screen_compute.py` (~:277): in `run_screen_and_record`'s
  exception handler, set `failed_member = None` when the run crashed before `_counting_progress`
  ever fired (`attempted == 0`) instead of `members[0]`; keep `failed_member = members[attempted]`
  byte-unchanged for `attempted > 0` (a genuine in-progress member).
- [ ] `apps/backend/tests/test_desk_screen_compute.py`: add a test asserting an `attempted == 0`
  crash path (a `fake_compute_screen` that raises before ever calling `progress(...)`) records
  `failed_member: null`; add a test asserting a CLI-triggered run
  (`python -m app.research.desk_screen_compute --date <D>`) leaves exactly one `ScreenRunStore`
  record matching the persisted `ScreenStore` snapshot (`state == "done"`, `screen_id == ` the
  snapshot's own `id`, `members_attempted == members_total`).

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`'s `LatestScreenRunDetail`: suppress the
  `desk-screen-run-latest-unreached` amber note and the `desk-screen-run-latest-counts` line when
  the latest run is `state === "done" && reused === true` — the run's own `screenRunOutcomeText`
  ("reused `<id>` — no walk was performed") already discloses this honestly. Both elements render
  byte-unchanged for every other state (a genuine fresh walk, cancelled, or failed run).

### Repo hygiene / Testing infrastructure
- [ ] Restore `apps/frontend/next-env.d.ts` and `apps/frontend/tsconfig.json` to their
  pre-iteration-30 content (drop the absolute scratchpad path from `next-env.d.ts`'s
  `<reference path>` line — it must read `./.next/types/routes.d.ts` again — and drop the matching
  scratchpad glob from `tsconfig.json`'s `include` list).
- [ ] Any scoped-rig provisioning this iteration's browser-qa or demo-narrator dispatch performs
  (a second `next build`/`next dev` against an alternate `NEXT_DIST_DIR`) MUST, in its own
  teardown, either have built from a full separate copy of `apps/frontend` (never touching the
  tracked working copy) or run `git checkout -- apps/frontend/next-env.d.ts
  apps/frontend/tsconfig.json` as its LAST step — per `lessons.md` iter-30(b). Verify with
  `git status --porcelain -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` (must be
  empty) before the dispatch reports done.
- [ ] Passenger, non-blocking, LAST attempt (per the iter-30 evaluator's own bound): if this
  iteration's `full` depth runs a demo-narrator walkthrough for J-18, point the scoped rig's own
  backend/frontend pair at `$FRONTEND_URL`/`$BACKEND_URL` for the ENTIRE narrator dispatch (a
  script's own `base_url` field is dead — `demo-phase.sh:316` / `demo_runner.py:1292`, lesson
  iter-28) and keep the rig alive until the narrator step finishes (lesson iter-27 — a
  browser-qa-lane teardown killed iter-27's rig one minute before the narrator ran). If the
  resulting frames are duplicated again, do not re-attempt in a future iteration — record it and
  drop the film to the owner's optional track, per `runs/goal-session-desk/iter-30/eval.md`'s own
  bound.

### New user-facing capability
None new. A reused screen run's own detail no longer shows a misleading amber "members not
reached" warning plus a row of zero counts; a run's failure record no longer misattributes a
symbol it never reached.

### New information displayed
None — this iteration corrects the rendering/derivation of already-registered fields (`reused`,
`members_attempted`, `failed_member`); no new field or endpoint.

### New user actions
None.

### UI surface changes
`/desk`'s existing Screen Runs section, "Latest run" detail block only — no new page, section, or
control.

### Product surface delta
The Screen Runs latest-run detail reads honestly for a reused run (no false-failure signal); a
crashed-before-any-attempt run's record is honestly blank on `failed_member` rather than naming a
symbol never touched. No navigation or layout change. Two tracked build files return to their
pre-iteration-30 content (no product behavior change — both are TypeScript build plumbing).

### Blueprint conformance
Desk nav section → `/desk` → the already-registered "Screen Runs" section (Feature/journey home
row for J-18 in `blueprint.md`, shipped iter-29). No new page, no nav-skeleton change.

### Data-contract additions
None. This iteration only corrects computation/rendering of already-registered fields on the
"Screen run records" Data-Contract row (`desk_screen_log.py` → `GET /research/desk/screen/runs`)
— no new field, shape, endpoint, module, or `Config` field.

## OUT OF SCOPE

- No `[NEW]`-flagged demo-narrator walkthrough as a blocking deliverable — it rides as a
  non-blocking passenger only (see IN SCOPE note); it is not a `DEFINITION OF DONE` item.
- No re-capture of J-18's already-existing populated/reused-row/empty-state screenshots
  (Do-not-redo, `state/iteration-state.md` — all three are DONE).
- No re-pin of `journey-scripts/J-18.json` to specific run/screen ids — it is already hardened to
  stable substrings (Do-not-redo).
- No touch to the ranked/skipped table, its `<colgroup>`, or any of the stored golden replay
  scripts J-01..J-16 depend on — J-16's measured width/layout contract is unchanged.
- No new `Config` field, no fingerprint move, no new MCP tool, no new Data-Contract row, no new
  page.
- No change to `desk_screen.py`'s snapshot/row/skip shapes, rank order, or five-pin key.
- No fix to the `demo_runner.py` frame-deduplication tooling bug (lessons iter-21/22(b)) — out of
  this iteration's blast radius.
- No re-verification of J-01..J-17 as an iteration goal beyond the required-still-passing
  regression set below (they were already replayed/spot-checked at iter-29/30).

## DEFINITION OF DONE

- [ ] J-18 passes via browser-qa: golden replay (`journey-scripts/J-18.json`, unchanged) is green,
  AND a live check of `/desk`'s current "Latest run" detail (ambient store's latest run is already
  `state: "done", reused: true` — no click needed) shows neither
  `desk-screen-run-latest-unreached` nor `desk-screen-run-latest-counts`
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16)
  remain green via deterministic golden replay, with LLM fallback for any journey lacking a golden
  script
- [ ] No anti-goal violation introduced or left open — `git status --porcelain -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` is empty (closing iteration 30's MINOR open item);
  single source of truth preserved (both fixes read/derive only already-recorded fields);
  persistence stays scoped (any rig used this iteration is a throwaway copy, never the operator's
  `.data`)
- [ ] Full backend suite passes with zero failures at or above the 1,500-pass / 8-skip baseline;
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`; `len(app.mcp.TOOL_NAMES) == 17`
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-31-dev.md`

## TESTING REQUIREMENTS

- Browser: J-18 (regression replay; live ambient check of the reused-run suppression, TC-4)
- Unit/integration: `apps/backend/tests/test_desk_screen_compute.py` (TC-1, TC-2, TC-3); full
  suite (TC-7)
- Error cases: a run crashing before any member is attempted must never fabricate a
  `failed_member` value (TC-1)

Test-first contract:

- TC-1: given `run_screen_and_record` raises before `_counting_progress` has ever fired
  (`attempted == 0`), when the terminal `"failed"` run record is written by `record_screen_run`,
  then its `failed_member` field is `null`.
- TC-2: given `run_screen_and_record` raises after `_counting_progress` has fired at least once
  (`attempted > 0`), when the terminal `"failed"` run record is written, then `failed_member`
  equals `members[attempted]`, exactly as before this iteration (regression guard on the existing
  `test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member` test).
- TC-3: given a screen computed via `python -m app.research.desk_screen_compute --date <D>`
  against a scoped fixture dir, when the CLI process exits 0, then `ScreenRunStore.list()` returns
  exactly one record whose `state == "done"`, `screen_id` equals the persisted `ScreenStore`
  snapshot's own `id`, and `members_attempted == members_total`.
- TC-4: given the ambient store's current latest recorded screen run
  (`screenrun-2026-07-31-fe0829e64a0d`, `state: "done"`, `reused: true`, `members_attempted: 0`),
  when `/desk`'s Screen Runs "Latest run" detail block renders, then neither
  `data-testid="desk-screen-run-latest-unreached"` nor
  `data-testid="desk-screen-run-latest-counts"` is present in the rendered DOM.
- TC-5: given the latest recorded screen run has `state: "done"`, `reused: false`, and attempted
  all of its members, then the `done && !reused` branch of `LatestScreenRunDetail` (which renders
  `data-testid="desk-screen-run-latest-counts"`) is verified as byte-unchanged from
  pre-iteration source via reviewer diff — this branch is untouched by this iteration's edit
  (logged: `assumptions.md` iter-31, no live ambient data currently exercises this exact state on
  the "latest" run).
- TC-6: given `apps/frontend/next-env.d.ts` and `apps/frontend/tsconfig.json` after this
  iteration's revert, when their contents are read, then neither file contains the substring
  `/scratchpad/` or any path outside the repository, and `next-env.d.ts`'s `<reference path>`
  again reads exactly `./.next/types/routes.d.ts`.
- TC-7: given the full backend test suite, when it is run after this iteration's changes, then it
  passes with zero failures at or above the 1,500-pass / 8-skip baseline,
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`, and
  `len(app.mcp.TOOL_NAMES) == 17`.
- TC-8: given `runs/goal-session-desk/journey-scripts/J-18.json`'s already-hardened replay steps
  (unchanged by this iteration), when replayed against the ambient store, then all four steps pass
  (regression guard — the `desk-screen-runs-table` testid's own rows, which the script targets,
  are unaffected by the "latest run" detail block's suppression fix).
- TC-9: given this iteration's own scoped-rig browser-qa/demo-narrator dispatch(es) finish
  teardown, when `git status --porcelain -- apps/frontend/next-env.d.ts
  apps/frontend/tsconfig.json` is run, then it reports no diff.

## NOTES

- **Blueprint corrected before this build, per the iter-30 lesson.** `state/blueprint.md`'s
  "NOTED at iter-30" entry has been edited (this iteration, before dispatch) to stop claiming the
  three fixes shipped, disclosing that only the empty-state screenshot and the J-18.json hardening
  actually landed at iter-30. A new "NOTED at iter-31" entry registers this iteration's real scope
  BEFORE the build, per the established pattern — see `runs/goal-session-desk/state/blueprint.md`
  (bottom of file). `lessons.md` iter-30's rule — never assert an entry in the past tense before
  the code lands — is the reason for this split.
- **TC-5's verification method is a logged interpretation call**, not an oversight: the ambient
  store's LATEST screen run is currently reused (`members_attempted: 0`), and the one prior
  full-attendance record on disk is not the "latest" one anymore, so live-verifying the unchanged
  branch would require either an unwanted real ambient Run Screen click or a further scoped rig
  with a registered universe purely to re-prove untouched code. See `assumptions.md` iter-31.
- **Do not re-attempt the walkthrough beyond this iteration.** The iter-30 evaluator's own written
  bound ("last time I ask") applies to THIS iteration's attempt; if the film is still duplicated
  after this run, a future iteration must not re-plan it — record it as owner-optional and move on
  (priority rubric rule 6/7 analog: don't keep re-planning a task that structurally cannot
  converge).
- Logged to `runs/goal-session-desk/state/assumptions.md` (iter-31 — goal-decomposer): the TC-5
  verification-method reasoning above.
