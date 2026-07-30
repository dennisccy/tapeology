# Goal Iteration 27 — Rebuild the shared frontend and record J-17's owed walkthrough

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 27
- **Mode:** next
- **Depth:** evidence
- **Target journeys:** J-17
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16
- **Frontend Present:** no
- **Anti-goal reminders:**
  - **Membership is never a signal.** Universe membership (and any constituents metadata) selects WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or report as an input value. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The briefing describes, never advises.** Desk copy is descriptive measurement only — no advice, imperative, prediction, or ranking language implying action ("buy", "watch this", "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

With zero code change, repair the shared frontend build that iteration 26 left pointing at a
torn-down backend, then record the `[NEW]`-flagged demo-narrator walkthrough J-17's own acceptance
text requires — the one conjunct iteration 26 built and proved by every other means but never
filmed.

## BACKGROUND

`journey-history.json` shows zero FAILING journeys (17 of 17 `passing`) — per the target rubric
this is capture-and-check only. J-17 alone carries `evidence_makeup: true`: iteration 26 built and
verified its behavior number-for-number (run record on disk matches the on-screen counts
character for character; suite 1,474 passed / 8 skipped; fingerprint `08e471b10130e1e2`; 17 MCP
tools; the one existing-test edit ratified) but its acceptance-named walkthrough was never
recorded — `Depth: full` was demoted to `lean` by the engine's arbiter (telemetry
`depth_demoted`), and `lean` never dispatches the demo-narrator. This is exactly iteration 24's
J-16 gap replayed on J-17. Iteration 26's own next-step recommendation names precisely two jobs —
record the film, and rebuild the frontend first — and this iteration does both, nothing else.

The dispatch prompt's binding depth recommendation for this iteration is `evidence`, matching
rule 7's exception (the prior evaluator's next-step asks only for evidence capture on an
already-passing journey). No escape condition holds: the last verdict was `CONTINUE` (not
`ESCALATE`/`REGRESSION`), the last coherence verdict was `COHERENCE-PASS`, the hardening-cadence
counter (3 consecutive lean, cadence 6) is not due, and no brand-new full-stack journey exists
this cycle — so `evidence` is not merely binding, it is correct on the merits, and the engine's
arbiter would demote any `full`/`lean` deviation regardless.

**A verified, blocking precondition (not merely a report claim):** direct inspection of the tree
confirms `apps/frontend/.next/static/chunks/app/{layout,desk/page}.js` still contain the literal
substring `localhost:8000` and NOT `localhost:8301` — iteration 26's scoped rig built the ONE
shared `.next` directory against its own scoped backend, since torn down, exactly as the iter-26
lesson (`lessons.md`) describes. No ambient process is currently listening on `:3301`, `:8301`,
`:3000`, or `:8000`. Every one of the 16 stored golden replay scripts targets `:3301`, so all 16
would false-FAIL against the current build for a reason that has nothing to do with the product —
this iteration's very first act, before any capture, is the rebuild + restart (T-9 in `docs/goal.md`
Constraints, and the iter-26 lesson's own remedy: build the scoped rig into its OWN `distDir`/copy
next time so the ambient pair is never overwritten again).

Two lessons apply directly: the iter-24/iter-12/13 lesson — a `[NEW]`-flagged walkthrough clause
needs `full` or `evidence` depth, never `lean` — is exactly why this run exists; and the iter-26
lesson — a second frontend instance must build into its own `distDir`/copy, never the shared
`apps/frontend/.next` — governs how THIS run's own scoped-rig capture (for the walkthrough itself)
must be set up so it does not repeat the same mistake on top of the very rebuild it is fixing.

## IN SCOPE

### Backend
- (none — zero code change this iteration)

### Frontend
- (none — zero code change this iteration; only a build artifact rebuild, not a source edit)

### Evidence capture (developer/reviewer skipped at this depth)
- [ ] **First, before any capture:** `rm -rf apps/frontend/.next`, rebuild with
  `NEXT_PUBLIC_API_URL=http://localhost:8301` (the QA-rig convention `lib/config.ts` already
  reads), and restart both ambient processes — backend on `:8301`, frontend on `:3301`
  (`incredible_auto_dev/scripts/start-backend.sh` / `start-frontend.sh`). Confirm via direct
  inspection (grep the rebuilt chunk files, and a direct `curl` cross-check against the running
  backend — never `location.origin` alone, per the iter-17 lesson) that the compiled output now
  carries `localhost:8301` and no longer carries `localhost:8000`.
- [ ] Replay all 16 stored golden scripts (`journey-scripts/J-01.json`..`J-16.json`) against the
  rebuilt ambient pair — confirm they pass with zero script edits, proving the prior false-FAIL
  risk is closed and no product regression exists.
- [ ] Set up a FRESH, fixture-scoped copy of `apps/backend/.data` (the iter-9/11/14/15/17/19-23/26
  precedent — never the ambient store) and record a populated top-up run using the SAME shape
  iteration 26 already proved (`0 reused · 6 fetched · 2 unchanged · 4 failed`, `2 tail · 10
  full_lookback`, at least one failed pair's own `requested_window`) via the existing CLI/POST
  top-up path — no code change, a pure invocation of what iteration 26 shipped.
- [ ] Verify the serving process for the scoped-rig capture actually points at the scoped copy (a
  direct `curl` cross-check against the scoped backend's own port, not `location.origin` alone —
  the iter-17/23/26 lesson) before recording.
- [ ] Author (or reuse/repair) a `[NEW]`-flagged demo-narrator script for J-17 that narrates the
  Top-up Runs section over that populated run: the four-outcome counts line and the
  tail-vs-full-lookback line must be legible inside the film's OWN frames, and at least one
  failed pair's `requested_window` line must appear in frame. Every click/expect target must name
  exactly ONE row or element (e.g. a specific failed pair's own row, scoped by its symbol) —
  never a bare selector matching every row (iter-20/23/25 lesson) — and never a `click` on a
  `/desk` ranked or skipped row's cells (the stretched `absolute inset-0` drill-in anchor makes it
  structurally impossible; use `expect`-only text assertions there per iteration-state's binding
  "Do not redo" rail).
- [ ] Parse-check the script (`demo_runner.py --mode lint` or equivalent) before the record run
  (iter-20 lesson: a malformed script fails open to `SKIPPED` with no visible error elsewhere).
- [ ] Record the walkthrough. Confirm on disk (not from the report's prose) that its frames show
  the required content and that at least one frame is a genuinely new capture, not a
  byte-identical duplicate of a prior journey's frame (iter-22b lesson — check md5s).
- [ ] Prove nothing was written to the operator's own `apps/backend/.data/` store during this
  run: a before/after file listing limited to that path shows no new/changed file outside
  rebuildable index sidecars (`*.db-wal`, `*.db-shm`, `bar_index.db`, `dataset_index.db`).

### New user-facing capability
None — this iteration ships no new product behavior. It repairs a build artifact and records
evidence for capability J-17 already shipped (iteration 26).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — `/desk` is read exactly as iteration 26 left it; only the compiled build artifact and the
running processes change.

### Product surface delta
None. The only deliverables are: a working ambient `:3301`/`:8301` pair, 16 clean golden replays,
and one demo-narrator walkthrough recording for J-17.

### Blueprint conformance
No new page, no new column, no nav-skeleton change — `blueprint.md`'s J-17 "RESOLVED at iter-26"
note already covers the current scope and needs no edit this iteration.

### Data-contract additions
None — zero new displayed value, zero new endpoint, zero new `Config` field.

## OUT OF SCOPE

- Any code change to `desk_topup_compute.py`, `desk_topup_log.py`, `desk_screen.py`,
  `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, either chart, or `/desk`'s own
  layout/testids — all frozen this iteration.
- Re-tuning the J-17 window-selection logic, the `unchanged` outcome, or the four disclosed
  fields — iteration 26 built and the evaluator proved all of it; per iteration-state's "Do not
  redo," it is done.
- Re-checking J-01 through J-16's underlying behavior beyond golden-script replay — they are
  `passing` and unaffected by a build-artifact rebuild; replay is the mechanical proof, not a
  re-audit.
- A real ~100-symbol live Yahoo top-up run against the operator's own universe — the populated run
  needed for capture is recorded on a fresh, fixture-scoped copy of `.data/`, never the ambient
  store.
- Standing up a second frontend instance against the SAME shared `apps/frontend/.next` directory
  — if the scoped-rig capture needs its own frontend build, it must use its own `distDir`/copy (the
  iter-26 lesson's own remedy), never rebuild the one the ambient `:3301` pair also uses.
- Archiving `runs/goal-session-desk/journey-scripts/` (would break `test_desk_ui_guards.py`'s two
  golden-script reads) — leave it in place.
- The three optional, non-blocking follow-ups iteration 25 opened (J-16 film wording pass, verdict
  string, replay-tool frame duplication) — carried forward again, not this iteration's job.

## DEFINITION OF DONE

- [ ] `apps/frontend/.next` rebuilt and both ambient processes (`:3301`, `:8301`) restarted;
  compiled chunks contain `localhost:8301` and do not contain `localhost:8000`
- [ ] All 16 existing golden replay scripts (J-01..J-16) pass with zero script edits post-rebuild
- [ ] J-17's `[NEW]`-flagged demo-narrator walkthrough is recorded, its own frames show the
  four-outcome counts line, the tail-vs-full-lookback line, and at least one failed pair's
  `requested_window`, and every click/expect target names exactly one row/element
- [ ] The recorded walkthrough contains at least one genuinely new frame (not a byte-identical
  duplicate of a prior journey's capture)
- [ ] No anti-goal violation introduced — evidence capture stays read-only against the operator's
  own `.data/` store; the populated run for capture lives only on a fresh, fixture-scoped copy
- [ ] Zero diff under `apps/`, `scripts/`, `config/`; `Config().config_fingerprint()` still reads
  `08e471b10130e1e2`; MCP tool count still exactly 17; backend suite result unchanged from
  iteration 26 (1,474 passed / 8 skipped)

## TESTING REQUIREMENTS

- Browser: J-17 (demo-narrator walkthrough over a populated, fixture-scoped Top-up Runs section);
  deterministic replay of J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12,
  J-13, J-14, J-15, J-16 against the rebuilt ambient `:3301`/`:8301` pair.
- Unit/integration: none new (zero code change) — the existing `test_desk_topup_compute.py` and
  `test_desk_topup_log.py` suites (including the iteration-26 window-disclosure guard test) are
  re-run only to confirm no drift.
- Error cases: N/A — no new code path this iteration.

Test-first contract:

- TC-1: given `apps/frontend/.next/static/chunks/app/{layout,desk/page}.js` currently contain the
  substring `localhost:8000` (verified stale build), when `apps/frontend/.next` is deleted,
  rebuilt with `NEXT_PUBLIC_API_URL=http://localhost:8301`, and both ambient processes are
  restarted, then the rebuilt chunk files contain `localhost:8301` and no longer contain
  `localhost:8000`.
- TC-2: given the rebuilt ambient pair serving `:3301`/`:8301`, when all 16 stored golden scripts
  (`journey-scripts/J-01.json`..`J-16.json`) are replayed, then all 16 report PASS with zero
  script edits.
- TC-3: given a fresh, fixture-scoped copy of `apps/backend/.data` (verified via a direct `curl`
  cross-check against the scoped backend, not `location.origin` alone), when a populated top-up
  run is recorded through the existing CLI/POST path with the same shape iteration 26 proved
  (`0 reused · 6 fetched · 2 unchanged · 4 failed`, `2 tail · 10 full_lookback`), then `/desk`'s
  Top-up Runs section renders that exact counts line and tail-vs-full-lookback line, and at least
  one failed pair's row shows its own recorded `requested_window`.
- TC-4: given the script for J-17's `[NEW]`-flagged walkthrough is parse-checked before the record
  run, when `demo_runner.py --mode lint` (or equivalent validation) runs against it, then it
  reports zero parse errors.
- TC-5: given the TC-3 populated scoped rig, when the demo-narrator records the `[NEW]`-flagged
  J-17 walkthrough with every click/expect target scoped to one row or element (never a bare
  selector matching every row, and never a `click` on a `/desk` ranked/skipped row's cells), then
  its own frames — opened directly, not read about — show the four-outcome counts line, the
  tail-vs-full-lookback line, and at least one failed pair's `requested_window`, and the verdict
  reads `Demo Verdict: RECORDED` or `RECORDED_WITH_NOTES` with every soft note disclosed.
- TC-6: given the recorded walkthrough's frame files, when their md5 hashes are compared against
  every pre-existing `J-*-verify.png` and prior demo frame on file, then at least one frame's md5
  does not match any prior file (proving a genuine new capture, not a stale duplicate).
- TC-7: given evidence capture performs no mutating action against the operator's own
  `apps/backend/.data/` store, when a file listing of that path is diffed before and after this
  iteration's work, then the only files that differ are rebuildable index sidecars (`*.db-wal`,
  `*.db-shm`, `bar_index.db`, `dataset_index.db`) — no new screen, universe, top-up, or
  reconciliation record is written there.
- TC-8: given zero code changes are made this iteration, when the backend suite and
  `Config().config_fingerprint()` are checked, then the suite result (1,474 passed / 8 skipped)
  and the fingerprint (`08e471b10130e1e2`) are unchanged from iteration 26, the MCP tool count is
  exactly 17, and the working-tree diff under `apps/`, `scripts/`, `config/` is empty.

## NOTES

- This is a capture-only run (no developer, no reviewer dispatched at `Depth: evidence`) — there is
  no `docs/handoffs/goal-desk-iter-27-dev.md` to write (the iteration-25 precedent); the
  deliverables are the rebuild + restart, the 16 clean golden replays, and the J-17 walkthrough.
- **Do the rebuild FIRST, before any golden-script replay or capture** — replaying against the
  stale build would produce false-FAILs indistinguishable from a real regression (the exact trap
  iteration 26's evaluator flagged and iteration 26's own replays only escaped by running before
  the scoped build).
- **Build the scoped-rig frontend (if one is needed for the populated-run capture) into its OWN
  `distDir`/copy** — never re-run `next build` against the SAME shared `apps/frontend/.next` the
  ambient `:3301` pair now correctly points at. This is the iter-26 lesson's own stated remedy;
  repeating iter-26's mistake inside the very iteration that fixes it would be a self-inflicted
  regression.
- Iteration-state's "Do not redo" list is binding: J-17's `_pair_window` three cases, the
  `unchanged` outcome, the four additive per-pair fields, and the `/desk` disclosure lines are
  BUILT and verified — do not re-implement or re-tune; the ONLY gap this iteration closes is the
  build artifact and the film. The single existing-test edit
  (`test_desk_topup_compute.py:1092`, 4-key → 8-key set equality) is ratified — do not touch it.
  J-16's layout (`table-fixed` + 13-col `<colgroup>`, `flex-nowrap` badges) stays as measured — do
  not re-tune widths or add a column. Never script a `click` on a cell inside a `/desk` ranked or
  skipped row.
- Do not delete or mutate anything under the operator's own `apps/backend/.data/` — all capture
  for this iteration happens on a fresh, fixture-scoped copy.
- No blueprint edit accompanies this iteration — no new displayed value, no nav-skeleton change.
