# Goal Iteration 11 — Close the era's last three mechanical gate items

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 11
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's
    behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation
    of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*
  - **Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*

## GOAL

Close the three small, machine-fixable items the iteration-10 evaluator named as the only things
standing between CONTINUE and a clean achievement gate: give J-09 a genuine same-run re-test and a
durable golden script, make the Playbook Signals invalid-date input visibly show its already-honest
error state, and close a latent scoping gap that could let a future fixture rig overwrite the
operator's real bar index.

## BACKGROUND

Iteration 10 discharged both owner rulings (R-3.1/R-3.2 in `docs/goal.md`'s dated R-3 block) and
re-verified all ten journeys — `journey-history.json` now carries zero unresolved anti-goal items.
The evaluator still returned CONTINUE, not GOAL_ACHIEVED, for exactly two mechanical reasons it
named explicitly: J-09 "MCP contract v4" was dropped by a wall-clock budget trim before it could be
re-tested this run (it is the only journey with no `journey-scripts/*.json` golden, which is *why*
it is the one that gets trimmed — confirmed on disk: `runs/goal-session-playbook/journey-scripts/`
holds J-01 through J-08 and J-10, never J-09), and one cosmetic `| FAIL |` row (UT-05, an invalid
session-date input whose border should turn amber but stays grey) blocks the deterministic results
gate outright (`rc=1`, confirmed by the evaluator's own run of the gate). A third item is carried as
a **latent hazard, not a violation**: `_assert_scoped` in `desk_playbook_backscan.py` checks four
env vars but not `TAPEOLOGY_BAR_INDEX_DB`, and `apps/backend/.data/bar_index.db` sits outside the
12 directories `STORE_SCOPE_PROTECTED_PATHS` (`project-extensions/store-scope/store-scope.env`)
already protects — nothing was touched this run, but a future rig invoked without exporting that
one var would sail past the guard and could write fixture-only index rows into the operator's real
index. **Depth is lean, matching the evaluator's binding recommendation; no full trigger holds** —
none of the three items touches ≥3 modules' interactions, none changes a persisted schema or an
already-registered Data-Contract value's owner/endpoint, the prior verdict was CONTINUE not
ESCALATE, and consecutive lean iterations is 0 (iteration 10 was full, which reset the hardening-
cadence counter well below its threshold of 6). Iteration 10 itself also wrote a `budget-breached`
marker (`runs/goal-session-playbook/iter-10/budget-breached`), which independently corroborates
lean here — a full spec would be demoted by the engine's own arbiter regardless. **Lesson applied**
(iter-9, `lessons.md`): a golden replay script's `expect` text must target a statically-rendered,
non-rig-dependent shell string, never a value the run itself just produced (iter-9's own J-10 fix
exists because of exactly this trap) — this directly shapes how J-09's new golden must be written
below. **Lessons applied** (iter-6/iter-7/iter-8): store scoping has broken silently three times in
this session already; all browser-qa and replay work this iteration must run through the current
scoped-rig launcher chain (`start_scoped_qa_backend.sh` → `qa_playbook_iter7_fixture_scoped_backend.sh`,
confirmed live — the former `nohup`-launches the latter), never the ambient `:8301` listener.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/research/desk_playbook_backscan.py:111-116` — add `"TAPEOLOGY_BAR_INDEX_DB"`
  as a fifth entry to `_SCOPING_ENV_VARS` (currently four: `TAPEOLOGY_DESK_PLAYBOOK_DIR`,
  `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`,
  `TAPEOLOGY_DESK_UNIVERSE_DIR`), so `_assert_scoped` (`:160-193`) refuses unless it too resolves
  under the scoped root and outside any `.data/` directory. Update the docstring's "four" ->
  "five" language and the raise message's variable-name list (`:190-192`) to match.
- [ ] `apps/backend/tests/test_desk_playbook_backscan.py:654-684` — extend the three existing TC-13
  tests (`test_tc13_assert_scoped_raises_when_all_four_env_vars_are_unset`,
  `..._raises_when_a_var_points_at_a_dot_data_store`, `..._passes_when_all_four_are_properly_scoped`)
  to cover all five vars, and add two new negative-control tests isolating
  `TAPEOLOGY_BAR_INDEX_DB` specifically (unset while the other four are scoped; pointed at a
  `.data/` path while the other four are scoped) — this codebase's standing counter-test
  discipline: a guard must be provably able to fail on the exact case it exists to catch.
- [ ] `runs/goal-session-playbook/journey-scripts/J-09.json` — author a new golden replay script
  (same `schema_version: 1` / `journey` / `name` / `default_timeout_ms` / `steps` shape as
  `J-01.json`/`J-08.json`) so J-09 stops being the one journey the wall-clock trim can silently
  drop. It opens `/desk` and asserts on a STATIC, already-shipped shell string that is NOT
  already claimed by J-01.json's ("Playbook Signals") or J-08.json's (the evidence-cell CSS
  selector) own assertions — e.g. the `desk-evidence-signature` testid's static label text
  "Built from signature:" (`page.tsx:3926-3927`) is a candidate: assert on the LABEL text only,
  never on the dynamic hash value beside it (the exact iter-9 vacuous-assertion trap this session
  already hit once on `J-10.json`). This golden is honest about what it can and cannot prove: it
  gives fast, deterministic regression coverage of the DATA `desk_playbook`/`desk_playbook_evidence`
  proxy byte-identically; it cannot, and does not claim to, exercise MCP tool registration/count —
  no page renders that. The tool-count/proxy-behavior half of J-09's own acceptance stays covered
  by `apps/backend/tests/test_mcp_server.py`'s already-pinned `EXPECTED_TOOLS`/`TOOL_NAMES`
  (`:56,198` — unmodified, already exists, already exercised every suite run) plus a live,
  same-iteration confirmation by the browser-qa lane (mirroring the iteration-9 evaluator's own
  check: count `app.mcp` tools live, confirm both `desk_playbook` and `desk_playbook_evidence` are
  present by name) recorded as a genuine `UT-J-09` row in this iteration's own
  `reports/phase-goal-playbook-iter-11-ui-test-results.md` — not a carried/deferred status.
- [ ] `runs/goal-session-playbook/state/golden-gaps` — this file was auto-deleted as a side effect
  of the framework's own golden-coverage bookkeeping (`replay-lane.sh`'s
  `replay_lane_golden_coverage`, which rebuilds it from PASSing journeys lacking a golden and
  removes it when the gap list is empty). If J-09's golden and live re-test both land this same
  iteration, the mechanism self-heals (the file stays absent because zero gaps remain). If, for any
  reason, this iteration's own re-verification of J-09 does not land a same-run PASS, restore this
  file with the single line `J-09` as a defensive marker so the gap is not silently lost a second
  time (the iter-10 lesson: "a budget-deferred journey silently erases its own follow-up ticket").

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx:5583-5592` — fix the invalid-state border color collision at
  the Playbook Signals session-date input (`data-testid="desk-playbook-date-input"`) ONLY. Root
  cause (confirmed by reading the source): `ASOF_INPUT_CLASS` (`:298-299`) already bakes in
  `border-slate-700`, and line 5591 appends `border-amber-500` when `validated.error !== null` —
  both are single-class Tailwind utilities of equal specificity, so which one wins is decided by
  their order in the COMPILED stylesheet, not by their order in the `className` string, and slate
  wins. The fix must be a LOCAL override at this one call site (e.g. an `!` important modifier, a
  class list that never emits both border-color utilities at once, or an equivalent technique) —
  it must NOT edit the shared `ASOF_INPUT_CLASS` constant itself, because that constant also styles
  two KEPT, frozen Era-B/R-2 surfaces that must stay byte-identical: `desk-refresh-control`
  (`:4396-4434`, the screen/forward refresh chain's own From/To day inputs, which already carry the
  IDENTICAL latent collision but are explicitly out of scope — see below) and
  `desk-deep-backfill-control` (`:3400-3428`).

### New user-facing capability

None. This iteration re-verifies already-shipped J-09 and fixes a pre-existing cosmetic input
affordance; it adds no new capability.

### New information displayed

None. The invalid-date state is already disclosed today via `aria-invalid="true"` and the visible
error message at `desk-playbook-date-error`; the border fix makes that EXISTING disclosed state
also visible on the input's own edge — no new data value is introduced.

### New user actions

None.

### UI surface changes

One small visual-affordance fix on the already-shipped Playbook Signals date input (border color
only, scoped to that one input); no new surface, panel, or control.

### Product surface delta

No product-visible capability changes. Two real defects close (J-09's stale verification gap, the
UT-05 border) and one latent operational hazard closes (bar-index scoping) — the product a user
sees is unchanged.

### Blueprint conformance

No new surfaces. All touched code lives under already-registered homes in
`runs/goal-session-playbook/state/blueprint.md`'s Feature/journey homes table: the Playbook Signals
fix is under Desk → J-03's canonical home (`/desk`, the existing Playbook Signals section); the
J-09 golden and live re-test are under J-09's existing "MCP tool surface only; no page" home. No
nav-skeleton edit; `blueprint.reapproval-requested` is not written.

### Data-contract additions

None. No new displayed value, computing module, or serving endpoint. The MCP tool count/registry is
unchanged (still 20 — `_STATIC_PATHS` and the parameterized six are untouched). The new J-09 golden
reads the ALREADY-registered "Playbook records" and "Evidence aggregates" Data-Contract rows
verbatim through the existing `/desk` page; it adds no second computation or fetch path for either.

## OUT OF SCOPE

- `apps/backend/scripts/seed_playbook_fixture_rig.py:126`'s own, separate, narrower three-directory
  `_assert_scoped` helper — its own docstring says it "predates this one and is left as-is"; it
  never calls `run_reconcile` and has no bar-index exposure to close.
- `project-extensions/store-scope/store-scope.env`'s `STORE_SCOPE_PROTECTED_PATHS` list —
  `bar_index.db`'s exclusion from that (different) 12-directory guard is a separate, deliberate,
  already-reasoned design choice (a rebuildable, stat-keyed projection, not append-only data); this
  iteration only extends `_assert_scoped`'s own positive pre-flight env-var check.
- Adding error-border styling to the Backscan panel's own From/To date inputs
  (`page.tsx:3596-3625`, `desk-backscan-from-input`/`desk-backscan-to-input`) — they have never had
  this affordance, UT-05 never named them, and adding new behavior there is unrequested scope for
  J-07.
- Fixing the identical latent border collision on the KEPT `desk-refresh-control`
  (`page.tsx:4396-4434`) — a frozen Era-B/R-2 surface; touching it is out of bounds for this era
  regardless of whether the same bug happens to live there too.
- Any change to detector logic, thresholds, `playbook_input_signature`, or `config_fingerprint`
  (stays `08e471b10130e1e2`). Re-opening R-3.1/R-3.2 (`docs/goal.md`) or `geometry.turned_at_midrange`
  — both are "Do not redo" per `iteration-state.md`.
- Adding a new `demo_runner.py` action type (e.g. a raw API/MCP-call step) to make J-09's golden
  exercise the MCP transport layer directly — cross-cutting framework risk, not requested, and not
  needed given the pytest-pinned contract already covers that half of J-09's acceptance.
- Any new `Config` field or fingerprint-epoch bump.

## DEFINITION OF DONE

- [ ] J-09 "MCP contract v4" is genuinely re-tested this iteration (a fresh `UT-J-09` row this run,
  not a carried/deferred status) — TC-2
- [ ] J-09 has a golden replay script (`journey-scripts/J-09.json`) a deterministic replay pass can
  execute (`demo_runner.py --mode verify` rc 0) — TC-1
- [ ] `state/golden-gaps` reflects reality: absent if J-09's gap closes this run, else the single
  line `J-09` — TC-3
- [ ] UT-05 flips to PASS: the invalid-date Playbook Signals input visibly shows its error border,
  and the valid/empty state is provably unaffected — TC-4, TC-5
- [ ] The kept `desk-refresh-control`/`desk-deep-backfill-control` regions are provably untouched
  (zero diff lines) — TC-6
- [ ] `_assert_scoped` covers `TAPEOLOGY_BAR_INDEX_DB` as a required fifth var, both as a positive
  refusal and a `.data/`-path refusal — TC-7, TC-8, TC-9
- [ ] The three existing TC-13 tests are extended (not left silently checking only four vars) and
  two new negative-control tests exist for the fifth var — TC-10
- [ ] The current scoped-rig launcher chain still runs clean end to end with the operator's real
  `bar_index.db` mtime provably unchanged after the run — TC-11
- [ ] Full backend suite passes: ≥2168 tests passed (the iteration-10 floor; grows with the new
  TC-13 tests), 8 skipped, exit 0 — TC-12
- [ ] Required-still-passing journeys J-01–J-08, J-10 remain green via deterministic replay, zero
  new FAIL rows — TC-13
- [ ] No anti-goal violation introduced; `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`; zero new `Config` fields
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-11-dev.md`

## TESTING REQUIREMENTS

- Browser: J-09 (live, same-run — MCP tool count/name confirmation plus the new `/desk` golden);
  UT-05 retake (Playbook Signals invalid-date input); deterministic replay of J-01 through J-08 and
  J-10 (regression)
- Unit/integration: the five extended/added TC-13 tests in `test_desk_playbook_backscan.py`; the
  full backend suite
- Error cases: an unset `TAPEOLOGY_BAR_INDEX_DB` (with the other four vars scoped) must still
  refuse; a `TAPEOLOGY_BAR_INDEX_DB` pointed inside `.data/` (with the other four vars scoped) must
  still refuse

Test-first contract — TC-1 through TC-13:

- TC-1: given `runs/goal-session-playbook/journey-scripts/J-09.json` does not exist at the start of
  this iteration, when it is authored in the existing schema shape asserting a static shell string
  distinct from J-01.json's and J-08.json's own assertions, then `demo_runner.py --mode verify`
  against the scoped fixture-rig backend returns rc 0 for J-09.
- TC-2: given the scoped fixture-rig backend is running, when the browser-qa lane inspects the live
  `app.mcp` tool registry, then it counts exactly 20 tools, both `desk_playbook` and
  `desk_playbook_evidence` are present by name, and this is recorded as a fresh `UT-J-09` PASS row
  in `reports/phase-goal-playbook-iter-11-ui-test-results.md`.
- TC-3: given TC-1 and TC-2 both land in this same iteration, when the iteration's browser-qa/replay
  step finishes, then `runs/goal-session-playbook/state/golden-gaps` is absent; given either does
  not land this same run, then the file contains exactly the single line `J-09`.
- TC-4: given the Playbook Signals session-date input has an invalid value typed (e.g.
  `not-a-date`), when it is rendered (focused or blurred), then its border is the amber/error color
  (not the default slate), `aria-invalid="true"` is set, and the verbatim error message renders at
  `desk-playbook-date-error` — captured as fresh screenshot evidence superseding
  `reports/qa/goal-playbook-iter-10-evidence/UT-05-fail.png`.
- TC-5: given the same input has a valid value (e.g. `2026-06-22`) or is empty, when it is rendered,
  then its border stays the default slate color and `aria-invalid` is `false` or absent — proving
  the fix is conditional, not an always-amber regression.
- TC-6: given the fix lands, when `desk-refresh-control`'s and `desk-deep-backfill-control`'s own
  input regions (`page.tsx:3400-3428`, `:4396-4434`) are diffed against the pre-iteration source,
  then zero lines changed in either region.
- TC-7: given `TAPEOLOGY_DESK_PLAYBOOK_DIR`/`_LOG_DIR`/`_BACKSCAN_LOG_DIR`/`_UNIVERSE_DIR` are all
  scoped under a temp root but `TAPEOLOGY_BAR_INDEX_DB` is unset, when `_assert_scoped(root)` is
  called, then it raises `PlaybookNotScopedError` naming `TAPEOLOGY_BAR_INDEX_DB` as unset.
- TC-8: given all five vars are set but `TAPEOLOGY_BAR_INDEX_DB` resolves to a path containing a
  `.data` path segment, when `_assert_scoped(root)` is called, then it raises
  `PlaybookNotScopedError` naming that var.
- TC-9: given all five vars are set and resolve under the scoped root, outside any `.data/`
  directory, when `_assert_scoped(root)` is called, then it returns without raising.
- TC-10: given the three existing TC-13 tests and two new negative-control tests, when the suite
  runs, then all five pass, and at least one of the five can be shown to fail on a seeded wrong
  value (the counter-test discipline this file's own prior guards already follow).
- TC-11: given the current scoped-rig launcher chain (`start_scoped_qa_backend.sh` ->
  `qa_playbook_iter7_fixture_scoped_backend.sh`, which already exports all five vars including
  `TAPEOLOGY_BAR_INDEX_DB`), when this iteration's browser-qa/replay lane runs through it, then no
  `PlaybookNotScopedError` is raised and `find apps/backend/.data -newermt <run-start-timestamp>
  -type f` shows no unexpected write to `bar_index.db` outside sqlite `-wal`/`-shm` sidecars.
- TC-12: given the full backend suite is run to completion, when it finishes, then it exits 0 with 8
  skipped and a passed-test count ≥2168.
- TC-13: given the CSS fix and the `_SCOPING_ENV_VARS` change land, when the deterministic replay
  lane runs `journey-scripts/J-01.json` through `J-08.json` and `J-10.json` against the scoped
  fixture-rig backend, then all nine return PASS with no new FAIL rows.

## NOTES

- **This is intended to be the era's mechanical tail, not a reopening.** Iteration 10 already
  completed R-3.3's substantive scope (the R-3.1/R-3.2 spec catch-up, `J-10.json`'s replay fix, the
  `/structure` chart fix) — those are "Do not redo." This iteration only clears the two items the
  iteration-10 evaluator held CONTINUE on (J-09's stale verification, the UT-05 FAIL row) plus the
  one latent hazard it flagged, so the next evaluation can judge the era on a clean deterministic
  gate. The decomposer does not declare GOAL_ACHIEVED — only the evaluator does.
- **Health-check before trusting any replay result** (iter-2 lesson): confirm `curl /health` against
  the `3301`/`8301` pair (not `3000`/`8000`) before treating a replay FAIL as real.
- **UT-05's exact acceptance text** is recorded at
  `reports/phase-goal-playbook-iter-10-ui-test-results.md:29` — "Input border turns amber
  (`aria-invalid="true"`), error message at `desk-playbook-date-error`, table/detail area does not
  render data for the invalid input." The semantic half (aria-invalid + message + honest empty
  state) already passes; only the border color is being fixed here.
- **`docs/goal.md` never mentions an amber border** — this is a test-designer-invented P2
  expectation, not a written acceptance line or anti-goal. Fixing it (rather than dropping the
  expectation, the evaluator's other sanctioned option) is a decomposer scoping call, logged to the
  assumption ledger.
- If the owner has a preference on the UT-05 border (the iteration-10 evaluator explicitly offered
  "he can say so" and skip it), none has been communicated for this iteration; proceeding with the
  fix as the default, cheaper-than-arguing path.
