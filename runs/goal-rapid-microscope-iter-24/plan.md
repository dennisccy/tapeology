# goal-rapid-microscope-iter-24 Execution Plan

## What to Build

1. **Coarsen the served `sealed_at`** in `vault.py`'s `_serialize_shard` (`vault.py:1486`,
   `_OPAQUE_SHARD_KEYS` at `:380`) from full-precision ISO timestamp to date-only
   (`^\d{4}-\d{2}-\d{2}$`), for every exposure state (`sealed`/`assigned`/`exposed`) so the
   field's shape stays uniform (TC-9 covers `assigned`/`exposed` too). Serve-time-only: the
   underlying shard-ledger row on disk (written at `vault.py:1224`) stays byte-identical —
   never rewritten.
2. **Widen `stage_tr2()`** (`j06_operator.py:748`) with a new run-aware half that consumes
   the committed `reports/j06-tranche/recording-runs.json` (5 runs, `sealed_this_run` =
   7/13/1/0/0, each with an `at` timestamp — verified directly), joins each run's
   `sealed_this_run` count against the now-coarsened served per-shard `sealed_at` date
   buckets, and computes the residual candidate-identity count per run-time-bucket. Assert
   against the SAME existing floor `residual_pool_uncertainty` already enforces
   (`candidate_identities_per_unexposed_selected_shard >= 2`, `j06_operator.py:803`) — do not
   invent a new floor number. Must still `raise SystemExit` on violation, matching the
   existing combinatorial half's behavior (`j06_operator.py:774`, `:816`).
3. **Extend `test_j06_operator.py`** (existing `residual_pool_uncertainty` coverage at
   lines 249-268): (a) a test proving the widened run-aware check passes against the REAL
   `recording-runs.json` + coarsened `sealed_at`; (b) a non-vacuity counter-test reproducing
   the OLD full-precision `sealed_at` join against the same 7/13/1/0/0 split through the SAME
   widened logic, proving it correctly FAILS (break-then-restore proof pattern, matching the
   Study-3 precedent).
4. **Extend `test_vault.py`** (alongside `test_tc6_a_sealed_shards_entry_carries_only_the_
   section_7_5_opaque_fields`, line 272): assert every served `sealed_at` is date-only shape
   for a `sealed`-state row AND (TC-9) for `assigned`/`exposed` rows, while the underlying
   ledger row's own stored `sealed_at` stays full-precision — proving serve-time-only
   coarsening, not a ledger rewrite.
5. **Re-verify J-07 "Graduation"** with a fresh, dated browser-qa pass against the standard
   `qa_playbook_iter7_fixture_scoped_backend.sh` rig. First grep-confirm zero diff to
   `micro_graduation.py`/`micro_sealed_evaluation.py` since the iter-17/18 baseline (evidence
   durability check) — then still capture a genuinely fresh screenshot; a carried-forward
   stamp is not acceptable a third round running.
6. **Re-verify J-09 "The pilot studies"** with a fresh browser-qa pass confirming the three
   ledgered families (range-wall failed aggression, delta divergence, capitulation
   exhaustion) still carry their recorded decision/evidence class/disclosures unchanged since
   iter-22.
7. **Write `journey-scripts/J-09.json`** (a stored deterministic golden replay script) — see
   "J-09 golden — design constraint" below for the concrete mechanism, since the browser-only
   script format cannot literally issue the triggering POST itself.
8. **Re-run the FULL stored replay set** (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09,
   J-10) in one shared QA rig invocation after J-09.json lands, and reconcile any collision
   between J-09's mutating step and J-08's `"No candidates ledgered."` empty-state assertion
   in this same iteration (sequencing or an order-independent assertion — never leave it for
   later).
9. **Independently read `j06_operator.py` (835 lines) and `tick_recorder.py` (1118 lines)
   end to end** (not only this round's diff) against `docs/rapid-validation-spec.md` as
   ground truth — `vault.py` (1952 lines) was already independently read in full in iter-23,
   so together this satisfies the auditor's own "~4,200 never-goal-mode-reviewed lines"
   request. Record findings in the dev handoff; fix a genuine defect as the smallest possible
   change if found (not scope creep).
10. Targeted suite run for touched modules (`test_vault.py`, `test_j06_operator.py`,
    `test_scout.py`, fingerprint pin, referee byte-freeze, `test_mcp_server.py`
    `EXPECTED_TOOLS` — confirmed still the 26-tuple today, unchanged) plus the TR-1…TR-30 trap
    suite — NOT a blanket ~2-hour full-suite gate (explicitly out of scope; this era has
    overrun wall-clock budget three rounds running).

**Out of scope (per spec, do not build):** editing the committed `recording-runs.json`
historical entries; the `desk_micro_readiness` MCP 10s-timeout / ~13.5s-warm latency fix; the
duplicated study-selector list dedupe; any sealed-shard exposure/assignment or real-corpus
J-09 re-run; any Referee/engine/frozen-vocabulary change; a blanket full-suite gate.

## J-09 golden — design constraint (read before implementing)

The deterministic replay harness (`scripts/automation/lib/demo_runner.py`,
`_VALID_ACTIONS = {"goto", "click", "fill", "expect", "wait_for"}`) has **no raw-HTTP/API
action type** — every `journey-scripts/*.json` step is a pure browser action. The `/desk`
frontend's own Scout compute button (`triggerDeskScoutCompute()`, `apps/frontend/lib/api.ts`)
sends a bare `POST /research/desk/micro/scout/compute` with **no body**, i.e. only the
default reference grid — there is no UI control (dropdown or otherwise) to select a
pilot-study grid, and this iteration's Frontend IN SCOPE explicitly expects no code change.

So J-09.json's own `steps[]` **cannot** literally perform the "trigger" — the spec's "(a)
triggers ... via the POST ... grid-selector path" must be realized as a **one-time fixture
seeding act**, run through the REAL production entry point (either
`scout.register_screen_and_walkforward_check` / `run_scout_grid_and_record` called directly,
mirroring `python -m app.research.scout --grid <pilot-selector>`, or the literal route), that
plants a genuine, non-vacuous pilot-study Scout Ledger row into the SAME on-disk store
`qa_playbook_iter7_fixture_scoped_backend.sh` points the scoped backend at — **exactly the
established pattern** `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` already
uses for J-07's "iter18-qa-universe" fixture (calls the real `evaluate_sealed_verdict()`
production function against a throwaway root, never a hand-rolled JSON blob; wired into the
launcher script, which the launcher's own long-standing rule requires extending in place,
never rewriting).

Concretely: write `apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py` (or similarly
named), planting a real dataset + snapshot + band-touch (or playbook-signal) anchor sufficient
for ONE of the three pilot grids (`range_wall_failed_aggression_pilot` /
`delta_divergence_pilot` / `capitulation_exhaustion_pilot`) to produce a real,
non-`no_candidate` decision, then call `register_screen_and_walkforward_check`/the CLI-mirror
entry point for real. Extend `qa_playbook_iter7_fixture_scoped_backend.sh` in place to run
this seeder as part of rig setup (before the backend serves), so the resulting Scout
Ledger/Walk-Forward row is already on disk when `journey-scripts/J-09.json` runs. J-09.json
itself then stays pure `goto` → `click` (`desk-section-expand-scoutLedger` and/or
`desk-section-expand-walkForward`) → `expect` on the seeded candidate/family id, grid name,
or closed-vocabulary decision string — never a pre-existing unrelated Desk heading (the
iter-18/19 "cannot fail" lesson). Prove the assertion discriminates via the break-then-restore
method (temporarily rename the target string in the fixture/source, confirm the step goes
red, restore byte-identical) — TC-6.

Because this seeded row lands in the SAME shared rig store J-08.json's step 3 reads as empty
(`"No candidates ledgered."`), sequence J-09 so it never runs before J-08 within one shared
rig invocation, or make J-08's assertion order-independent (TC-7) — reconcile in this same
iteration, do not carry forward.

## Agents Required

- backend-data: yes — vault.py serve-time coarsening, j06_operator.py TR-2 widening, new
  fixture seeder script, extended vault/j06_operator/scout test coverage, J-09.json golden,
  independent code read of j06_operator.py + tick_recorder.py, targeted suite runs.
- frontend-ux: no — no frontend code change is expected. `ValidationVaultSection` already
  renders whatever `sealed_at` string the route serves, generically. If (and only if) the
  now-coarsened value surfaces a genuine rendering defect not previously exercisable, fix it
  as the smallest possible change and note it in the dev handoff — do not proactively touch
  frontend files otherwise.

## Frontend Present: yes

(No frontend file is expected to change, but the DoD requires browser-qa-agent verification
of J-06/J-07/J-09 on `/desk`, so Chrome MCP checks are required per this iteration's own
NOTES/BACKGROUND — carried forward from iter-18's identical reasoning.)

## Files to Create/Modify

- `apps/backend/app/research/vault.py` — `_serialize_shard` (`:1486`): coarsen `sealed_at` to
  date-only for every served state.
- `apps/backend/scripts/j06_operator.py` — `stage_tr2()` (`:748`): add the run-aware half,
  consuming `reports/j06-tranche/recording-runs.json`; same `>= 2` floor, same `SystemExit`
  contract.
- `apps/backend/tests/test_j06_operator.py` — widened-check pass test (real data) + non-vacuity
  counter-test (old full-precision join fixture).
- `apps/backend/tests/test_vault.py` — date-only `sealed_at` shape assertion (all three
  exposure states) + ledger-row-untouched proof.
- `apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py` — new: plants a real
  pilot-study Scout Ledger row via the real production entry point, for the QA rig.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extend in place to
  invoke the new J-09 seeder during rig setup.
- `runs/goal-session-rapid-microscope/journey-scripts/J-09.json` — new stored golden replay
  script (goto/click/expect only).
- `runs/goal-session-rapid-microscope/journey-scripts/J-08.json` — only if step 3's
  `"No candidates ledgered."` assertion needs to become order-independent to avoid colliding
  with J-09's seeded row (TC-7); otherwise untouched.
- `docs/handoffs/goal-rapid-microscope-iter-24-dev.md` — dev handoff, including the
  independent-read findings for `j06_operator.py`/`tick_recorder.py`.
- `blueprint.md` — an iter-24 note recording the served-precision narrowing (no Data Contract
  table row edit — same name/owner/endpoint/type).
- `runs/goal-session-rapid-microscope/state/assumptions.md` — log any genuine interpretation
  call (the coarsening-vs-editing-the-report choice is already logged by the decomposer; log
  the J-09-golden-trigger-mechanism choice here too, since the spec text does not literally
  resolve the demo_runner action-vocabulary gap).

## UI Evolution

- New user-facing capability: none.
- New information displayed: none new — `sealed_at` keeps its name/owner/endpoint; only its
  served precision narrows (full timestamp → date-only) on the Validation Vault section.
- New user actions: none.
- UI surface changes: none structural — the Validation Vault section's `sealed_at` display
  shows a coarser string; if J-09.json's seeded fixture surfaces through the Scout Ledger /
  Walk-Forward sections, that is new ROW data in already-shipped tables, not a new surface.
- Navigation changes: none.

## Visual Requirements

- Component patterns: unchanged — reuse the existing Validation Vault shard-row rendering,
  the existing Scout Ledger / Walk-Forward table rendering (generic per-family/per-trial
  rows), and the existing section-expand pattern (`desk-section-expand-*` testids).
- Layout: unchanged — no new section, no new column (T-11: new data lives inside existing
  cells/rows, reuses no shipped heading string).
- Key visual effects: none new.
- States to handle: the coarsened `sealed_at` must render correctly in the existing
  loading/empty/error treatments already shipped for the Validation Vault section — no new
  state to design for.

## Key Test Scenarios

- TC-1/TC-9: `GET /research/desk/micro/vault` serves date-only `sealed_at` for `sealed` rows
  AND for any `assigned`/`exposed` rows (uniform coarsening across all three states).
- TC-2: the underlying shard-ledger record on disk, read directly, still carries the original
  full-precision `sealed_at`, byte-identical to before this iteration.
- TC-3: the widened `stage_tr2()` run-aware check, against the REAL `recording-runs.json` +
  coarsened `sealed_at`, reports every run-time-bucket's candidate count `>= 2` and exits 0.
- TC-4: the same widened check, fed a synthetic OLD full-precision `sealed_at` join against
  the same 7/13/1/0/0 split, correctly reports a violation (non-vacuity proof).
- TC-5/TC-6: `journey-scripts/J-09.json`'s seeded pilot-study row is visible on `/desk`
  (Scout Ledger and/or Walk-Forward), the golden's assertion string is discriminating
  (break-then-restore), and the step passes on replay.
- TC-7: the full stored replay set (J-01…J-06, J-08, J-09, J-10) runs in one shared rig
  invocation with zero collision between J-09's mutating step and J-08's empty-state step.
- TC-8: J-07's browser-qa pass reproduces the iter-22-verified graduation states with a
  screenshot timestamped this iteration, given zero diff to `micro_graduation.py`/
  `micro_sealed_evaluation.py`.
- Unit: `test_mcp_server.py` `EXPECTED_TOOLS` stays the 26-tuple (verified unchanged today);
  `test_scout.py` J-09 candidate tests stay green untouched; the TR-1…TR-30 trap suite green;
  fingerprint prints `08e471b10130e1e2`; referee `SHA-256` listing matches iteration-0
  baseline byte-for-byte.
- Error case: `stage_tr2()` still exits non-zero (`SystemExit`) when the widened run-aware
  floor is violated (proven only via the counter-test fixture, never asserted in prose); the
  vault route still refuses (typed error, not degraded 200) any read of a still-sealed shard's
  symbol/date.
