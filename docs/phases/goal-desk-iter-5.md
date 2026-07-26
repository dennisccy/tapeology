# Goal Iteration 5 — Close J-04's browser-evidence gap (no product changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** desk
- **Iteration:** 5
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07
- **Anti-goal reminders:**
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk` BESIDE the kept two pages — the one sanctioned kept-surface edit is J-05's additive `/structure` prefill.) *(critical)*
  - 9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - 10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed, append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint, bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or rewritten — a new run is a new snapshot. *(critical)*
  - **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
  - **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test fetches the network; live fetch/top-up/screen runs are operator-run verifications reported honestly (run-or-not-run), never CI gates. *(critical)*
  - **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged by the sentinel every iteration. *(critical)*

## GOAL

Close `/desk`'s (J-04) outstanding browser-evidence gap with a real, fixture-scoped browser-QA pass
that captures the one required screenshot that has never existed (Run Screen running, with a second
click refused) plus fresh empty-state and populated-briefing shots, and records the era's first
`/desk` golden replay script — so J-04 can move from `partial` to `passing` on real evidence.

## BACKGROUND

Iter-4 built `/desk` completely (page, 7 API functions, 10 types, the third nav row, `reused`/
`screen_id`, the no-universe refusal, the `UniverseStore` corrupt-file guard) — the evaluator
verified this itself via live REST calls and two real screenshots. But `browser-qa-agent` never
dispatched at all that iteration (caught only by the phase-closure-auditor's mechanical file-exists
check, per `lessons.md` iter-4 entry 1), so the third required state — Run Screen in progress with a
second click refused — has no picture anywhere, and `reports/qa/goal-desk-iter-4-qa.md` is
discredited (it asserts things the code and the auditor both contradict). Iter-4's own QA pass also
wrote 60 price-less bar records into the REAL `apps/backend/.data` store because it ran unscoped
(`lessons.md` iter-4 entry 2) — fixed at the source, but the root cause (an unscoped QA pass) is a
risk this iteration must not repeat. The `iteration-state.md` "Do not redo" list is explicit: "J-04's
PRODUCT is built — do not rebuild the page... iter-5 owes EVIDENCE only." This iteration is therefore
verification-only: zero product code changes, one careful browser-QA pass against a temp-scoped
backend seeded from committed fixtures, and a saved golden so no future change can silently break
`/desk` the way `bars.py`'s price-less rows almost did.

**Depth: lean — no full trigger holds.** This iteration touches zero product modules (no structural/
cross-cutting change, trigger 1), adds no persisted schema or Data-Contract owner/endpoint change
(trigger 2), the prior verdict was `CONTINUE` not `ESCALATE` (trigger 3 does not apply), and the
hardening cadence is not met (0 consecutive lean iterations dispatched so far this session — iters
0-4 were all full; cadence is 4). Lean's cycle (developer → reviewer → browser-qa-agent) already
includes the exact step this iteration needs (`browser-qa-agent`); iter-4's failure to dispatch that
step was a process gap orthogonal to depth (it happened AT full depth), so choosing full would not by
itself have prevented it.

**Rubric deviation from the prior evaluator's recommendation, logged per the priority rubric:** the
iter-4 `eval.md` "Next-Step Recommendation" bundled closing J-04's evidence gap together with
building J-05 (history click-through + `/structure` drill-in prefill) in one `full` iteration. This
spec deviates: it targets J-04's evidence gap ALONE. Rule 5 of the target-selection rubric ("never
bundle two risky journeys") applies — the evidence lane has already failed once (silently, at full
depth) and had a near-miss real-store write; adding J-05's new frontend build (two pages, a new
guard test) into the same iteration would make any browser-QA failure undiagnosable (evidence-gap
regression vs. new-feature bug). J-05 is deferred to iteration 6, where it can be scored in isolation
against a now-trustworthy `/desk` evidence baseline.

**Lessons applied (from `lessons.md`, read in full):** (a) iter-0's async-render trap — any new golden
step must assert against a stable, non-timing-dependent element (a `data-testid` or a static string),
never a value whose correctness depends on an in-flight compute's timing; (b) iter-4's ambient-store
near-miss — every store this pass touches MUST be env-var-scoped to a fresh temp directory, verified
by a before/after file listing of the real `apps/backend/.data`, not merely assumed; (c) iter-3's
QA-report-fabrication lesson — every claim in this iteration's `ui-test-results.md` must state the
exact fixture-scoped data basis it was measured against, never a number carried over from a different
run; (d) iter-4's post-match-liveness lesson — the new `/desk` golden must, like J-07's hardened
version, re-check the page is still alive after each text match, not only at the match.

## IN SCOPE

### Backend

- [ ] No production code changes to any `desk_*` module or route — verify via `git diff --stat`
      showing zero changed lines on `desk_universe.py`, `desk_coverage.py`, `desk_topup_compute.py`,
      `desk_screen.py`, `desk_screen_compute.py`, `desk_routes.py`, `bars.py`, `meta.py`.
- [ ] Stand up a fixture-scoped backend for the browser-QA pass ONLY (never the ambient dev store):
      point `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_SCREEN_DIR`,
      `TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_BAR_INDEX_DB`, `TAPEOLOGY_DATASET_INDEX_DB` at fresh
      subdirectories of one temp root; seed the universe dir with a verbatim copy of
      `apps/backend/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json`; seed the bar dir
      with verbatim copies of the two committed `apps/backend/tests/fixtures/bars/*.json` files;
      issue one warm-up `GET /research/desk/coverage` call before opening the browser (avoids a cold
      first-call surprise per `lessons.md` iter-0 entry 2's precedent).
- [ ] Record an `apps/backend/.data/` file listing (path + mtime + size) immediately before the pass
      starts and immediately after it ends; diff the two listings and record the result (must be
      identical) in the dev handoff.

### Frontend

- [ ] None — `apps/frontend/app/desk/page.tsx` and every file it imports ship byte-unchanged this
      iteration; verify via `git diff --stat` showing zero changed lines under `apps/frontend/`.

### QA / Evidence (the actual deliverable this iteration)

- [ ] Dispatch `browser-qa-agent` against the fixture-scoped backend above (after
      `rm -rf apps/frontend/.next` + rebuild per T-9) to capture, in order: the empty state, Run
      Screen triggered and running with the button disabled (the missing shot), and the populated
      briefing after the run completes — each as a named screenshot file.
- [ ] Write `reports/phase-goal-desk-iter-5-ui-test-results.md` stating the exact fixture-scoped data
      basis (universe snapshot id, registered bar files, temp root path) behind every claim.
- [ ] Record `runs/goal-session-desk/journey-scripts/J-04.json` (schema mirrors
      `journey-scripts/J-07.json`: `schema_version: 1`, `goto`/`click`/`fill`/`expect`/`wait_for`
      steps against `data-testid` selectors) covering the three states above, with a post-match
      liveness step after each text/state assertion (the J-07 iter-4 hardening pattern).

### New user-facing capability

None — `/desk` already shipped in iter-4. This iteration produces evidence for what already exists;
it does not add or change any capability.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None this iteration — the running product is byte-identical to iter-4's; only its verification
evidence changes.

### Blueprint conformance

No new surfaces. This iteration verifies the already-registered "Desk" home
(`blueprint.md` Information Architecture, nav row 3, `/desk`) — no Information-Architecture or
nav-skeleton change. (Two small documentation-currency edits to `blueprint.md`'s existing rows are
made alongside this spec — see NOTES — neither is a nav-skeleton change and neither needs
reapproval.)

### Data-contract additions

None. No new displayed value, computing module, or serving endpoint this iteration.

## OUT OF SCOPE

- **J-05** (ledger history click-through + `/structure` `?symbol=&asof=` drill-in prefill) — deferred
  to iteration 6 per the priority rubric's rule 5 (do not bundle a second risky/new-build journey into
  the same iteration as a twice-troublesome evidence lane).
- **J-06** (MCP 17-tool contract) — untouched; no MCP code changes this iteration.
- Any change to `desk_universe.py`, `desk_coverage.py`, `desk_topup_compute.py`, `desk_screen.py`,
  `desk_screen_compute.py`, `desk_routes.py`, or `apps/frontend/app/desk/page.tsx`'s production
  logic — the product is already built; this iteration is evidence-only.
- Resolving the queued **"frozen foundations" ratification question** (`bars.py` +
  `StructureChart.tsx` were changed in iter-4 under a developer-written spec amendment; only the
  owner can ratify or require a revert) — this spec re-flags it in NOTES but does not act on it; that
  decision belongs to the owner, not to an agent.
- The three carried-forward one-line hygiene items (guard the screen CLI write path like the POST
  route; apply the price-less-row filter to the per-series bar read too; re-tighten
  `test_structure_chart_viewport.py:194`) — deferred until a nearby file is next touched, per
  `iteration-state.md`'s "Do not redo."
- Any new `Config` field — zero this iteration, per era-wide Path-A discipline.

## DEFINITION OF DONE

- [ ] Target journey J-04 passes via `browser-qa-agent`, fixture-scoped (TC-1..TC-5)
- [ ] `reports/phase-goal-desk-iter-5-ui-test-results.md` exists, is written by `browser-qa-agent`,
      and names the fixture-scoped data basis for every claim (TC-1..TC-5)
- [ ] `runs/goal-session-desk/journey-scripts/J-04.json` golden replay script is recorded with
      post-match liveness steps (TC-6)
- [ ] Zero new or modified files in `apps/backend/.data/` from this iteration's QA pass (TC-7)
- [ ] Required-still-passing journeys J-01, J-02, J-03 (suite + pin + zero-diff on their owning
      modules) and J-07 (deterministic replay) remain green (TC-8, TC-9)
- [ ] No anti-goal violation introduced — persistence stays scoped, snapshots stay append-only, every
      run stays an explicit operator act (TC-7)
- [ ] Unit tests pass; no regressions — suite floor 1328 passing / 8 skipped / 0 failed, pin
      `08e471b10130e1e2` unchanged (TC-8)
- [ ] Dev handoff written at `docs/handoffs/goal-desk-iter-5-dev.md`, including the before/after
      `apps/backend/.data/` file listing and the exact env-var values used to scope the pass

## TESTING REQUIREMENTS

- Browser: J-04 (target — `browser-qa-agent`, fixture-scoped, three named states); J-07 (regression
  smoke — deterministic replay of the existing golden, guarding kept nav/route-count/Structure/
  Cockpit behavior).
- Unit/integration: full backend suite must hold its floor (1328 passing / 8 skipped / 0 failed);
  `git diff --stat` must show zero changed lines on every `desk_*` module, `bars.py`, and `meta.py`
  (J-01/J-02/J-03's zero-diff regression check, per "Do not redo").
- Error cases: a second click on the Run Screen button while a compute is in flight must not produce
  a second `POST /research/desk/screen/compute` request (client-side single-flight refusal via the
  button's `disabled` attribute); the fixture-scoped pass must produce zero writes anywhere under the
  ambient `apps/backend/.data/` store.

Test-first contract:

- TC-1: given a fixture-scoped backend (env vars `TAPEOLOGY_DESK_UNIVERSE_DIR`, `TAPEOLOGY_BAR_DIR`,
  `TAPEOLOGY_DESK_SCREEN_DIR`, `TAPEOLOGY_DATASET_DIR`, `TAPEOLOGY_BAR_INDEX_DB`,
  `TAPEOLOGY_DATASET_INDEX_DB` all pointed at a fresh temp directory, seeded with the committed
  103-member universe fixture `universe-2026-07-25-817cc184bbb3.json` and the two committed
  registered bar-store fixture files, with no screen snapshot recorded yet), when the browser loads
  `/desk`, then the page renders the exact text "Desk screen not computed yet.", an enabled
  `data-testid="desk-run-screen-button"`, and a nav bar listing exactly Cockpit, Structure, Desk —
  captured in a screenshot.
- TC-2: given the empty state from TC-1, when the operator clicks the Run Screen button once, then
  `data-testid="desk-screen-compute-running"` appears with a "members done / members total" progress
  line and the Run Screen button becomes disabled with the label "Computing…" — captured in a
  screenshot.
- TC-3: given Run Screen is disabled and running (TC-2), when a second click is attempted on the same
  button, then no second `POST /research/desk/screen/compute` request is sent (the `disabled`
  attribute blocks the click; the network log shows exactly one trigger call for the whole run) —
  captured in a screenshot showing the still-disabled, still-running button.
- TC-4: given the screen run from TC-2 reaches state "done", when the page re-renders, then
  `data-testid="desk-screen-rows-table"` shows ranked rows each with a band-class chip, a distance
  chip, a score, and coverage/tick-evidence badges, `data-testid="desk-skipped-section"` groups the
  skipped members under an honest heading, and `data-testid="desk-provenance"` shows the universe
  snapshot id/date, as_of, fingerprint `08e471b10130e1e2`, and the "Bar-store signature" label —
  captured in a screenshot.
- TC-5: given the backend from TC-1..TC-4 is still running, when `GET /meta/ui-routes` is called,
  then the response lists exactly three entries: `/`, `/structure`, `/desk`.
- TC-6: given the browser-qa-agent pass (TC-1..TC-5) completes, when the golden script is recorded,
  then `runs/goal-session-desk/journey-scripts/J-04.json` exists with `schema_version: 1` steps
  covering the empty state, the running/disabled state, and the populated state, and at least one
  step after each text-match assertion re-checks the page is still mounted (a post-match liveness
  check, mirroring J-07's iter-4 hardening).
- TC-7: given a file listing of `apps/backend/.data/` (path, mtime, size) taken immediately before the
  browser-QA pass starts and immediately after it ends, when the two listings are diffed, then they
  are byte-for-byte identical — zero new or modified files in the ambient store.
- TC-8: given the current backend test suite and a `git diff --stat` against the last committed tree,
  when the suite is run and the diff is inspected, then the suite reports at least 1328 tests passing
  and 8 skipped with 0 failed, a live call to `Config().config_fingerprint()` returns
  `08e471b10130e1e2`, and `git diff --stat` shows zero changed lines in `desk_universe.py`,
  `desk_coverage.py`, `desk_topup_compute.py`, `desk_screen.py`, `desk_screen_compute.py`, and
  `desk_routes.py`.
- TC-9: given the deterministic replay lane's stored golden for J-07, when it is replayed against the
  current tree, then it reports PASS with no step failures.

## NOTES

- **Human call still queued, not resolved here.** `docs/goal.md` lists `bars.py` and
  `components/StructureChart.tsx` as untouched for the era; both were changed in iter-4 under a
  developer-written spec amendment (the price-less-row fix). Only the owner can ratify that exception
  or require a revert. This iteration does not touch either file and does not decide the question —
  it is re-surfaced here so the evaluator keeps it visible for the owner.
- **Why lean, restated:** lean's cycle already dispatches `browser-qa-agent`; the only reason it
  didn't run in iter-4 was a process gap, not a depth limitation, and this iteration adds zero product
  code, so there is nothing for a full pipeline's extra stages (orchestrator, ui-impact-analyst,
  ui-test-designer, qa validator, ux-regression-reviewer, auditor, phase-closure-auditor) to plan or
  review beyond what the developer→reviewer→browser-qa-agent cycle already covers.
- **`reports/qa/goal-desk-iter-4-qa.md` stays discredited, untouched.** Lean depth does not produce a
  `reports/qa/<phase>-qa.md` (that artifact is written only by the full pipeline's `qa` agent in
  validate mode). This iteration's authoritative evidence is
  `reports/phase-goal-desk-iter-5-ui-test-results.md`; do not cite or "fix" the iter-4 file — it is
  historical record of what iter-4 actually produced.
- **Escalate, don't soft-skip, on a repeat process failure.** If `browser-qa-agent` fails to dispatch
  again, or if the before/after `apps/backend/.data/` listings differ, treat it as a hard stop and
  report it plainly — this is the second attempt at the same evidence, and a second silent skip or a
  second real-store write is a pattern, not a fluke.
- **Blueprint currency edits made alongside this spec** (see `blueprint.md`): (1) the Desk
  nav-skeleton row's "[iter-4, J-04 — being built THIS iteration]" tag is updated to reflect that J-04
  shipped in iter-4 and iter-5 closes its evidence gap; (2) the Structure nav-skeleton row now names
  the iter-4 `StructureChart.tsx` finite-value-guard exception (pending owner ratification) alongside
  the already-documented J-05 prefill exception; (3) the "Bars / candles" Data Contract row's Notes
  column now records the iter-4 priceless-row exclusion (merged read) vs. the still-unfiltered
  per-series read (coherence.md iter-4 advisory finding), so a future iteration does not assume
  `bars.py` stayed fully zero-diff. None of these are nav-skeleton structural changes (no section
  added/renamed/removed, no canonical-home moved), so no reapproval file was written.
