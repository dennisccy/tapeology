# Goal Iteration 28 — Record J-17's owed walkthrough, this time on a rig that outlives it

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 28
- **Mode:** next
- **Depth:** evidence
- **Target journeys:** J-17
- **Required-still-passing journeys:** J-04, J-07, J-09, J-16
- **Frontend Present:** no
- **Anti-goal reminders:**
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or report as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

With zero code change, record J-17's still-owed `[NEW]`-flagged demo-narrator walkthrough so its
own frames — not a report about them — show the top-up's window-disclosure content, by fixing the
one exact, now-known cause of the last two failed attempts: rig teardown timing and film target
address.

## BACKGROUND

`journey-history.json` shows zero FAILING journeys (17 of 17 `passing`); this is capture-and-check
only (rule 7's exception — the prior evaluator's next-step asks ONLY for evidence capture on an
already-passing journey, J-17, which carries `evidence_makeup: true`). The dispatch prompt's
binding depth recommendation is `evidence`, and no escape condition holds (last verdict
`CONTINUE`, last coherence `COHERENCE-PASS`, hardening cadence at 4/6 consecutive lean — not due,
and this iteration dispatches no lean/full pipeline at all) — `evidence` is correct on the merits,
not merely binding.

This is the THIRD attempt at the same one deliverable, and iteration-state marks it explicitly:
**"BOUNDED: iter-28 is the LAST capture retry the evaluator will request."** Both prior failures
are root-caused, not vague:
- **iter-26:** `Depth: full` was demoted to `lean` by the engine's arbiter — `lean` never
  dispatches a demo-narrator, so no film existed at all.
- **iter-27:** a film WAS recorded, but all 5 frames share one md5 (`dd3486a6bede477c9d9bb5475aa5bd27`,
  also equal to 8 `J-*-verify.png` files) — the demo-narrator's `base_url` was
  `http://localhost:3301` (the ambient page), while the populated run existed only on a
  fixture-scoped rig (`:3391`/`:8391`) that the browser-qa lane tore down at 00:28, one minute
  before the narrator ran at 00:29 (`lessons.md` iter-27).

The fix is now precise and this spec states it as an explicit ordering constraint, not a hope:
**keep the scoped rig alive until the demo-narrator step itself has finished and its frames are
written to disk, and point the film's `base_url` at the scoped frontend's own port — never at
`:3301`.** Separately, per the iter-26 lesson, the scoped-rig FRONTEND for this capture must build
into its OWN `distDir`/copy — the ambient `apps/frontend/.next` (confirmed rebuilt and correct per
iteration-state's "Do not redo": chunks carry `localhost:8301`, no `localhost:8000` in the live
path) must not be touched again this iteration. No rebuild of the ambient pair is needed or
authorized here — that job is already DONE.

## IN SCOPE

### Backend
- (none — zero code change this iteration)

### Frontend
- (none — zero code change this iteration; the ambient `apps/frontend/.next` is NOT touched)

### Evidence capture (developer/reviewer skipped at this depth)
- [ ] Confirm (do not rebuild) that the ambient pair is healthy: a direct `curl` cross-check
  against `:8301` and a grep of the already-rebuilt chunk files for `localhost:8301` /
  absence of `localhost:8000` in the live path — a read-only confirmation, not a rebuild.
- [ ] Stand up a FRESH, fixture-scoped copy of `apps/backend/.data` (never the ambient store) on
  its own backend port (e.g. `:8391`), and a scoped FRONTEND built into its OWN `distDir`/copy
  (e.g. `apps/frontend/.next-scoped-iter28`, or a whole separate `apps/frontend` checkout) on its
  own port (e.g. `:3391`) with `NEXT_PUBLIC_API_URL` pointed at the scoped backend — never a
  second `next build` against the ambient `apps/frontend/.next`.
- [ ] Record a populated top-up run on the scoped backend reproducing the same disclosed shape
  iteration 26/27 already proved (a real mix of `reused`/`fetched`/`unchanged`/`failed` outcomes,
  a real tail-vs-full-lookback split, at least one genuinely failed pair with its own
  `requested_window`) via the existing CLI/POST top-up path — no code change, a pure invocation.
- [ ] Verify by direct `curl` against the scoped backend's own port (never `location.origin` alone
  — the iter-17/23/26 lesson) that the scoped frontend is actually serving that scoped backend's
  data before recording anything.
- [ ] **Keep BOTH the scoped backend and the scoped frontend running, untorn-down, through the
  entire demo-narrator step** — do not stop either process until after the walkthrough has been
  recorded and its frame files exist on disk. This is the one ordering fix this iteration exists
  to apply; iter-27's failure was exactly a premature teardown one minute before the narrator ran.
- [ ] Author or repair a `[NEW]`-flagged demo-narrator script for J-17 whose `base_url` is
  explicitly the scoped frontend's own address (e.g. `http://localhost:3391`) — **never**
  `http://localhost:3301`. Reuse iter-27's script content where it is already correct (every
  click/expect target names exactly one row/element; no `click` on a `/desk` ranked or skipped
  row's cells — the stretched `absolute inset-0` drill-in anchor makes that structurally
  impossible; `expect`-only there per iteration-state's binding "Do not redo" rail) and change
  only the target address.
- [ ] Parse-check the script (`demo_runner.py --mode lint` or equivalent) before the record run.
- [ ] Record the walkthrough. Confirm ON DISK (not from the report's prose) that its own frames —
  opened directly — show the four-outcome counts line, the tail-vs-full-lookback line, and at
  least one failed pair's own `requested_window`, and that at least one frame's md5 is genuinely
  new (does not match any prior `J-*-verify.png` or any prior demo frame on file).
- [ ] After recording, tear down the scoped rig (backend + frontend + its own `.next` copy) and
  confirm the ambient `:3301`/`:8301` pair (and its `.next` build) is untouched — a before/after
  grep of the ambient chunk files should show no change.
- [ ] Prove nothing was written to the operator's own `apps/backend/.data/` store during this run:
  a before/after file listing limited to that path shows no new/changed file outside rebuildable
  index sidecars (`*.db-wal`, `*.db-shm`, `bar_index.db`, `dataset_index.db`).

### New user-facing capability
None — this iteration ships no new product behavior. It records evidence for capability J-17
already shipped (iteration 26) and independently re-proven (iteration 27).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — `/desk` is read exactly as iteration 27 left it (zero diff); only a throwaway rig and its
recording process are stood up and torn down.

### Product surface delta
None. The only deliverable is one demo-narrator walkthrough recording for J-17 whose own frames
show the content its goal.md acceptance names.

### Blueprint conformance
No new page, no new column, no nav-skeleton change — `blueprint.md`'s J-17 "RESOLVED at iter-26"
note already covers the current scope and needs no edit this iteration.

### Data-contract additions
None — zero new displayed value, zero new endpoint, zero new `Config` field.

## OUT OF SCOPE

- Any code change to `desk_topup_compute.py`, `desk_topup_log.py`, `desk_screen.py`,
  `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, either chart, or `/desk`'s own
  layout/testids — all frozen this iteration.
- Re-tuning J-17's window-selection logic, the `unchanged` outcome, or the four disclosed fields —
  built and proven twice already; per iteration-state's "Do not redo," it is done.
- Re-checking J-01 through J-16's underlying behavior beyond the required-still-passing set above
  — nothing in this iteration touches their code or their served values.
- Rebuilding the ambient `apps/frontend/.next` — it is confirmed correct (iteration-state "Do not
  redo") and must not be rebuilt or otherwise disturbed this iteration.
- A real ~100-symbol live Yahoo top-up run against the operator's own universe — the populated run
  needed for capture is recorded on a fresh, fixture-scoped copy of `.data/`, never the ambient
  store.
- Standing up the scoped-rig frontend against the SAME shared `apps/frontend/.next` directory the
  ambient pair uses — it must build into its own `distDir`/copy (the iter-26 lesson's remedy).
- Archiving `runs/goal-session-desk/journey-scripts/` (would break `test_desk_ui_guards.py`'s two
  golden-script reads) — leave it in place.
- Editing `journey-scripts/J-17.json` — it is an honest partial proxy on the ambient store's older
  record (iteration-state "Do not redo": do not delete or "fix" it to chase scoped counts).
- The three optional, non-blocking follow-ups iteration 25 opened (J-16 film wording pass, verdict
  string, replay-tool frame duplication) and the replay-tool duplicate-frame note from iterations
  26/27 — all carried forward again, not this iteration's job.

## DEFINITION OF DONE

- [ ] A fresh, fixture-scoped rig (its own `.data` copy, its own backend port, its own frontend
  `distDir`/copy on its own port) serves a populated top-up run with a real mixed-outcome shape
  and at least one genuinely failed pair
- [ ] The scoped rig (backend + frontend) stays running, untorn-down, until AFTER the
  demo-narrator step has recorded its frames to disk
- [ ] J-17's `[NEW]`-flagged demo-narrator walkthrough is recorded with its `base_url` pointed at
  the scoped frontend's own address (never `:3301`); its own frames — opened directly — show the
  four-outcome counts line, the tail-vs-full-lookback line, and at least one failed pair's
  `requested_window`; every click/expect target names exactly one row/element
- [ ] At least one recorded frame's md5 does not match any prior `J-*-verify.png` or prior demo
  frame on file (proving a genuinely new capture)
- [ ] The ambient `apps/frontend/.next` and the ambient `:3301`/`:8301` pair are confirmed
  unchanged after this iteration (no accidental second-build clobber, the iter-26 recurrence)
- [ ] No anti-goal violation introduced — evidence capture stays read-only against the operator's
  own `.data/` store; the populated run for capture lives only on the fresh, fixture-scoped copy
- [ ] Zero diff under `apps/`, `scripts/`, `config/`; `Config().config_fingerprint()` still reads
  `08e471b10130e1e2`; MCP tool count still exactly 17; backend suite result unchanged from
  iteration 27

## TESTING REQUIREMENTS

- Browser: J-17 (demo-narrator walkthrough over a populated, fixture-scoped Top-up Runs section,
  `base_url` = the scoped frontend); deterministic replay of J-04, J-07, J-09, J-16 against the
  ambient `:3301`/`:8301` pair (unchanged, confirming no accidental disturbance).
- Unit/integration: none new (zero code change) — `test_desk_topup_compute.py` and
  `test_desk_topup_log.py` (including the iteration-26 window-disclosure guard test) are re-run
  only to confirm no drift.
- Error cases: N/A — no new code path this iteration.

Test-first contract:

- TC-1: given a fresh, fixture-scoped copy of `apps/backend/.data` served on its own backend port
  and a scoped frontend built into its OWN `distDir`/copy on its own port, when a populated top-up
  run is recorded through the existing CLI/POST path with a real mixed-outcome shape, then
  `/desk`'s Top-up Runs section on the scoped frontend renders the four-outcome counts line, the
  tail-vs-full-lookback line, and at least one failed pair's own `requested_window`.
- TC-2: given the scoped rig from TC-1 is verified by a direct `curl` against its own backend port
  (not `location.origin` alone) to be genuinely serving the scoped data, when the demo-narrator
  records J-17's `[NEW]`-flagged walkthrough with `base_url` set to the scoped frontend's own
  address, then the walkthrough's own frames — opened directly — show all three items named in
  TC-1, and every click/expect target names exactly one row/element (no bare selector matching
  every row, no `click` on a `/desk` ranked/skipped row's cells).
- TC-3: given the scoped rig is kept running (not torn down) until the demo-narrator step
  completes, when the recording finishes and its frame files are checked, then at least one
  frame's md5 does not match any prior `J-*-verify.png` file or any prior demo frame on file.
- TC-4: given the demo-narrator step has finished and the scoped rig is torn down afterward, when
  the ambient `apps/frontend/.next` chunk files and a direct `curl` against `:8301` are checked,
  then they are byte-identical to their iteration-27 state (no accidental second build clobbered
  the ambient pair).
- TC-5: given evidence capture performs no mutating action against the operator's own
  `apps/backend/.data/` store, when a file listing of that path is diffed before and after this
  iteration's work, then the only files that differ are rebuildable index sidecars (`*.db-wal`,
  `*.db-shm`, `bar_index.db`, `dataset_index.db`) — no new screen, universe, top-up, or
  reconciliation record is written there.
- TC-6: given zero code changes are made this iteration, when the backend suite and
  `Config().config_fingerprint()` are checked, then the suite result is unchanged from iteration
  27, the fingerprint reads `08e471b10130e1e2`, the MCP tool count is exactly 17, and the
  working-tree diff under `apps/`, `scripts/`, `config/` is empty.
- TC-7: given `journey-scripts/J-04.json`, `J-07.json`, `J-09.json`, and `J-16.json` are replayed
  against the UNTOUCHED ambient `:3301`/`:8301` pair, then all four report PASS with zero script
  edits.

## NOTES

- This is a capture-only run (no developer, no reviewer dispatched at `Depth: evidence`) — there is
  no `docs/handoffs/goal-desk-iter-28-dev.md` to write (the iteration-25/27 precedent); the sole
  deliverable is the J-17 walkthrough recording.
- **This is the LAST capture retry the evaluator committed to requesting** (iteration-state,
  iter-27's next-step recommendation). Apply the ordering fix exactly: rig up → verify → record →
  THEN tear down, never the reverse; `base_url` = the scoped frontend's own port, never `:3301`.
  If, despite this, the film still fails to show its subject, that is the evaluator's call to make
  next (drop the film to the owner's optional track and propose the finish on existing evidence,
  per iter-27's own bound) — not a reason to retry a different fix in this same iteration.
- Iteration-state's "Do not redo" list is binding: J-17's `_pair_window` three cases, the
  `unchanged` outcome, the four additive per-pair fields, and the `/desk` disclosure lines are
  BUILT and verified — do not re-implement or re-tune. The single existing-test edit
  (`test_desk_topup_compute.py:1092`, 4-key → 8-key set equality) is ratified — do not touch it.
  J-16's layout (`table-fixed` + 13-col `<colgroup>`, `flex-nowrap` badges) stays as measured — do
  not re-tune widths or add a column. Never script a `click` on a cell inside a `/desk` ranked or
  skipped row.
- Do not delete or mutate anything under the operator's own `apps/backend/.data/` — all capture
  for this iteration happens on a fresh, fixture-scoped copy, on its own ports, with its own
  frontend build artifact.
- No blueprint edit accompanies this iteration — no new displayed value, no nav-skeleton change.
