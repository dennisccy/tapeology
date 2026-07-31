# Goal Iteration 30 — Close J-18's honest-empty-state screenshot gap + three small honesty/UX fixes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 30
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-18
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between 2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`; `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established. Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Close the second-key confirm's REJECT of iteration 29's GOAL_ACHIEVED proposal — a genuine screenshot of J-18's honest "No screen runs recorded yet." empty state, captured on a rig that has never run a screen — and fix three small, already-identified, non-blocking honesty/UX gaps in the same feature.

## BACKGROUND

`runs/goal-session-desk/iter-29/eval-confirm.md` returned `REJECT`, not because the product behaves wrongly, but because J-18's acceptance names three browser pictures and only two exist: the populated Screen Runs panel and a reused run's own row are photographed and opened, but the honest "nothing recorded yet" starting state was never captured — the ambient store's own Run Screen click destroyed that empty state for good before the earlier attempt's screenshot tool was fixed (iter-29's own disclosed defect). The confirm explicitly disputes none of the on-disk cross-checks and calls the remedy "bounded and cheap."

This iteration's binding depth recommendation, computed by the engine AFTER the reject (`session.json` `next_depth: "lean"`), is `lean`. None of the four depth-binding escape conditions hold this iteration — the reject is recorded as `CONTINUE`, not `ESCALATE`/`REGRESSION`; coherence was `COHERENCE-WARN`, not `FAIL`; hardening cadence is not due (0 consecutive lean); and no brand-new full-stack journey exists this cycle — so `lean` is honored rather than forced to `full` (see `assumptions.md` iter-30 for the full reasoning and the reversible remedy if the owner disagrees).

Applying the accumulated lessons on this exact recurring failure (`lessons.md` iter-21, iter-22(b), iter-24, iter-26, iter-27, iter-28, iter-29): a scoped-rig `[NEW]` demo-narrator walkthrough needs `full` depth (lean dispatches no demo-narrator at all — iter-24), and `evidence` depth cannot provision a rig (no developer dispatched — iter-28). This iteration sidesteps both traps by scoping the deliverable to what LEAN's own browser-qa step can do UNILATERALLY, within its own single dispatch: provision a scoped desk-data rig, screenshot the empty state as the very first action (closing the iter-29 "capture-before-populate" ordering lesson), and tear it down itself — no cross-dispatch rig-teardown race (the exact failure iter-27 hit) because no demo-narrator runs this iteration. The confirm's secondary, "supporting" objection (the walkthrough film's frames are not sufficiently distinct) stays explicitly open and disclosed; it is not fixable at `lean` depth and is not this iteration's target.

Per the binding "Do not redo" instruction in the inlined iteration state ("Do NOT run a capture-only iteration; the J-18 empty-state picture rides the make-up lane") and the priority rubric's rule 7, this iteration is NOT evidence-only: it also lands three small, real, already-identified fixes from iteration 29's own evaluator follow-ups (#3 is the empty-state capture itself; #4 and #5 below are genuine code/test gaps), so the empty-state capture rides along inside a real iteration rather than standing alone.

## IN SCOPE

### Backend
- [ ] `apps/backend/app/research/desk_screen_compute.py`: in `run_screen_and_record`'s failure path, set `failed_member = None` when the run crashed before `_counting_progress` ever fired (`attempted == 0`) instead of guessing `members[0]`; keep `failed_member = members[attempted]` unchanged for `attempted > 0` (a genuine in-progress member).
- [ ] `apps/backend/tests/test_desk_screen_compute.py`: add coverage for the `attempted == 0` vs `attempted > 0` `failed_member` cases, and add a test asserting a CLI-triggered run (`python -m app.research.desk_screen_compute --date <D>`) leaves exactly one record in `ScreenRunStore` matching the persisted snapshot.

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`'s `LatestScreenRunDetail`: suppress the `desk-screen-run-latest-unreached` amber note and the `desk-screen-run-latest-counts` line when the latest run is `state === "done" && reused === true` — a reused run's own `screenRunOutcomeText` ("reused `<id>` — no walk was performed") already discloses this honestly; showing an amber "N members not reached" note plus a row of zero counts beside it reads like a failure. Both elements render unchanged for every other state (a genuine fresh walk, cancelled, or failed run).

### Testing / Evidence infrastructure
- [ ] Update `runs/goal-session-desk/journey-scripts/J-18.json` steps 2–3: assert the stable substrings "no walk was performed" and "101 / 101" against the `desk-screen-runs-table` testid's own rows (not the "latest run" detail block, which changes identity every real run) instead of today's specific run/screen ids, and adjust for the new suppressed amber-note/counts behavior on a reused latest run.
- [ ] Browser-qa: provision a scoped desk-data rig by pointing a fresh backend instance's `TAPEOLOGY_DESK_UNIVERSE_DIR` at an empty, never-populated directory (this env var alone scopes the whole desk data tree as siblings — no other env var needed), serve a scoped frontend build pointed at that backend's port, and — as the FIRST action of the dispatch, before any Run Screen click — screenshot `/desk`'s Screen Runs section showing `data-testid="desk-screen-runs-empty"` / "No screen runs recorded yet." Tear the rig down at the end of the SAME dispatch. No demo-narrator step runs this iteration (lean depth).

### New user-facing capability
None new. A reused screen run's own detail no longer shows a misleading amber "members not reached" warning plus a row of zero counts; a run's failure record no longer misattributes a symbol it never reached.

### New information displayed
None — this iteration corrects the rendering/derivation of already-registered fields (`reused`, `members_attempted`, `failed_member`); no new field or endpoint.

### New user actions
None.

### UI surface changes
`/desk`'s existing Screen Runs section, "Latest run" detail block only — no new page, section, or control.

### Product surface delta
The Screen Runs latest-run detail reads honestly for a reused run (no false-failure signal); a crashed-before-any-attempt run's record is honestly blank on `failed_member` rather than naming a symbol never touched. No navigation or layout change.

### Blueprint conformance
Desk nav section → `/desk` → the already-registered "Screen Runs" section (Feature/journey home row for J-18 in `blueprint.md`, shipped iter-29). No new page, no nav-skeleton change.

### Data-contract additions
None. This iteration only corrects computation/rendering of already-registered fields on the "Screen run records" Data-Contract row (`desk_screen_log.py` → `GET /research/desk/screen/runs`) — no new field, shape, endpoint, module, or `Config` field.

## OUT OF SCOPE

- No `[NEW]`-flagged demo-narrator walkthrough this iteration — `lean` depth dispatches no demo-narrator; the confirm's "distinct frames" objection stays open, tracked for a future iteration (see NOTES).
- No touch to the ranked/skipped table, its `<colgroup>`, or any of the 13 stored golden replay scripts J-01..J-16 depend on — J-16's measured width/layout contract is unchanged.
- No new `Config` field, no fingerprint move, no new MCP tool, no new Data-Contract row, no new page.
- No change to `desk_screen.py`'s snapshot/row/skip shapes, rank order, or five-pin key.
- No re-capture of J-18's already-existing populated/reused-row screenshots or film frames (Do-not-redo, iteration state).
- No fix to the demo_runner.py frame-deduplication tooling bug (lessons iter-21/22(b)) — out of this iteration's blast radius.

## DEFINITION OF DONE

- [ ] J-18 passes via browser-qa, AND the honest empty "No screen runs recorded yet." state is captured as a genuine screenshot on a freshly-provisioned scoped desk-data rig (never the ambient store) — closing `runs/goal-session-desk/iter-29/eval-confirm.md`'s REJECT reason
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16) remain green via deterministic golden replay (including the updated `J-18.json`), with LLM fallback for any journey lacking a golden script
- [ ] No anti-goal violation introduced — single source of truth preserved (`failed_member`/amber-note fixes read/derive only already-recorded fields), persistence stays scoped (the rig used for the empty-state capture is a throwaway copy, never the operator's `.data`), host-guard caps respected
- [ ] Full backend suite passes with zero failures at or above the 1,500-pass / 8-skip baseline; `Config().config_fingerprint()` still prints `08e471b10130e1e2`; `len(app.mcp.TOOL_NAMES) == 17`
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-30-dev.md`

## TESTING REQUIREMENTS

- Browser: J-18 (empty-state capture on a scoped rig, TC-1; regression check of the populated/reused states already captured in prior iterations)
- Unit/integration: `apps/backend/tests/test_desk_screen_compute.py` (TC-4, TC-5, TC-6); golden replay `journey-scripts/J-18.json` (TC-7); full suite (TC-8)
- Error cases: a run crashing before any member is attempted must never fabricate a `failed_member` value (TC-4)

Test-first contract:

- TC-1: given a freshly-provisioned scoped backend+frontend pair whose `TAPEOLOGY_DESK_UNIVERSE_DIR` points at an empty directory with zero prior screen-run records, when the operator loads `/desk` before any Run Screen click, then the Screen Runs section renders `data-testid="desk-screen-runs-empty"` with the exact text "No screen runs recorded yet." and a screenshot of that frame is saved under `reports/qa/goal-desk-iter-30-evidence/`.
- TC-2: given the latest recorded screen run has `state: "done"` and `reused: true`, when `/desk`'s Screen Runs "Latest run" detail block renders, then neither `data-testid="desk-screen-run-latest-unreached"` nor `data-testid="desk-screen-run-latest-counts"` is present in the rendered DOM.
- TC-3: given the latest recorded screen run has `state: "done"`, `reused: false`, and attempted all of its members, when the same detail block renders, then `data-testid="desk-screen-run-latest-counts"` IS present and shows the run's own `ranked_count`/`skipped_by_reason` values, unchanged from current behavior.
- TC-4: given `run_screen_and_record` raises before `_counting_progress` has ever fired (`attempted == 0`), when the terminal `"failed"` run record is written by `record_screen_run`, then its `failed_member` field is `null`.
- TC-5: given `run_screen_and_record` raises after `_counting_progress` has fired at least once (`attempted > 0`), when the terminal `"failed"` run record is written, then `failed_member` equals `members[attempted]`, exactly as before this iteration.
- TC-6: given a screen computed via `python -m app.research.desk_screen_compute --date <D>` against a scoped fixture dir, when the CLI process exits 0, then `ScreenRunStore.list()` returns exactly one record whose `state == "done"`, `screen_id` equals the persisted snapshot's own `id`, and `members_attempted == members_total`.
- TC-7: given `runs/goal-session-desk/journey-scripts/J-18.json`'s updated replay steps, when replayed against the ambient store on any future UTC date (not the date this iteration ran), then the assertions match the `desk-screen-runs-table` testid's stable substrings ("no walk was performed" for a reused row, "101 / 101" for the full-walk row) rather than a specific run/screen id, and pass unchanged.
- TC-8: given the full backend test suite, when it is run after this iteration's changes, then it passes with zero failures at or above the 1,500-pass / 8-skip baseline, `Config().config_fingerprint()` still prints `08e471b10130e1e2`, and `len(app.mcp.TOOL_NAMES) == 17`.

## NOTES

- **This is not the walkthrough fix.** The confirm's secondary objection — the `[NEW]` demo-narrator film's frames are not sufficiently distinct — stays open. Closing it needs `full` depth (a demo-narrator dispatch coordinated with a still-live scoped rig, per iter-27's lesson) and, per the depth-binding rule, a genuine escape condition (owner override, a future ESCALATE, or the hardening-cadence pass). Do not re-attempt it at `lean` or `evidence` depth — both are structurally proven insufficient across four prior iterations (lessons iter-24, iter-28).
- **Scoping mechanism, verified directly this iteration:** `resolve_desk_screen_log_dir` (and its siblings for universe/screen/topup/reconcile stores) derive their directory as `os.path.join(os.path.dirname(desk_universe_dir_resolved), <name>)` — so setting only `TAPEOLOGY_DESK_UNIVERSE_DIR` to a fresh directory scopes the ENTIRE desk data tree with one env var. No code change is needed to provision the rig.
- **Capture ordering is load-bearing.** The empty-state screenshot MUST be the first browser action against the scoped rig — any Run Screen click, even an accidental one from a golden-replay step running out of order, destroys the empty state for that rig instance permanently (iter-29's own lesson).
- Logged to `runs/goal-session-desk/state/assumptions.md` (iter-30 — goal-decomposer): the reasoning for honoring the binding `lean` recommendation over forcing `full`, and the reversible remedy if the owner wants the walkthrough gap closed sooner.
- `blueprint.md` updated with a `NOTED at iter-30` documentation-currency entry (no new Data-Contract row, no nav-skeleton change).
