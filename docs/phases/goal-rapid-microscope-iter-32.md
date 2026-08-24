# Goal Iteration 32 — Give J-11's Graduation section its two missing evidence renders

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 32
- **Mode:** next
- **Depth:** lean
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-05, J-06, J-07, J-08, J-10
- **Frontend Present:** no (browser evidence only — the frontend Graduation section is already
  shipped; this iteration adds zero frontend lines)
- **Anti-goal reminders:**
  - "No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
    exposure; the refusal is typed, tested, and fail-closed. *(critical)*"
  - "Sealed exposure is family-level and single-shot — never a second draw. No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
    travels in every later export bundle; no perturbed re-submission resets it. *(critical)*"
  - "Single source of truth — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*"
  - "Immutable data — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*"
  - "Persistence stays scoped — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*"
  - "Host-guard caps are law." — every heavy path (backend restarts, full-suite runs) respects
    the declared CPU/memory ceilings; never disable, widen, or bypass them. *(critical)*
  - Era-1–2 constitution phrase carried verbatim in Foundation invariants: "**no fabricated
    data**; single source of truth; no magic numbers" — the fixture rows this iteration seeds
    must be produced by calling the REAL production functions, never hand-rolled JSON.

## GOAL

Give the already-shipped `/desk` Graduation section (J-11) its two still-missing acceptance
renders — the real, unseeded ledger's `"No candidates ledgered."` empty state, and a
fixture-scoped rig showing all four graduation stage tokens plus one permanent FAILED sealed
verdict — so J-11 can move from `partial` to `passing` with genuine element-capture evidence,
and add the `[NEW]`-flagged walkthrough step the journey's own acceptance also requires.

## BACKGROUND

Iteration 31 built the Graduation section, `desk_graduation` MCP tool, and the 27-tuple contract
correctly (verified by the evaluator against the running code and the rig's own ledger row —
see `state/iteration-state.md` "Do not redo") but scored J-11 `partial`: its own acceptance names
two on-screen proofs — the served empty-ledger message, and a fixture rig carrying one family per
stage with a permanent failed verdict — that no browser pass had produced. The iter-31 evaluator's
own next-step recommendation is this iteration's plan verbatim: seed a test store with one family
in each of the four stages plus one permanently failed verdict, photograph it; photograph the same
panel against a store with no records; add the walkthrough step. The iter-31 lesson (second entry)
also flags that this era's ONE persistent :8301 store-scoped rig already carries the iter-18
single-family fixture and cannot show the empty state as-is, and that the frontend's
`NEXT_PUBLIC_API_URL` is baked in at process start — so this spec names, explicitly, which scoped
root serves which capture (see IN SCOPE) rather than leaving that discovery to the browser lane.

The evaluator's binding depth recommendation for this iteration is `lean`; no full trigger holds
(see Depth justification below), so this spec follows it. All ten other journeys are `passing`
and untouched by this iteration's scope — the six previously-open anti-goal findings are all
owner-dispositioned `blocks_current_era: false` per `state/iteration-state.md` and are explicitly
"Do not redo" / "do not re-litigate."

**Depth justification (no full trigger holds):** prior verdict was `CONTINUE` (not
ESCALATE/REGRESSION); the last coherence audit (`iter-31/coherence.md`) was `COHERENCE-PASS`;
consecutive-lean count is 2 of a cadence-6 threshold (not due); and this is not a brand-new
full-stack journey — J-11's production code (backend route reader, MCP proxy, frontend section)
is already fully built and explicitly "Do not redo" (per `state/iteration-state.md`); this
iteration's only deliverable is fixture/test-rig setup plus evidence capture for a journey whose
code already exists, which is squarely inside the lean example the depth rubric itself names
("a new endpoint plus its UI use" — here, zero new endpoint, zero new UI, evidence only).

## IN SCOPE

### Backend

- [ ] New QA-only fixture-seeding script `apps/backend/scripts/seed_micro_graduation_iter32_fourstage_fixture.py`,
  mirroring `seed_micro_graduation_iter18_fixture.py`'s "REAL records through REAL production
  functions, never a hand-rolled JSON blob" discipline (plant dataset + snapshot →
  seal/assign/expose a vault shard → advance state via the real `micro_graduation.py`/
  `micro_sealed_evaluation.py` transition functions), producing, in ONE scoped root (its own
  `TAPEOLOGY_MICRO_GRADUATION_DIR`, distinct from every existing rig directory):
  - Family A: stopped at `exploratory` (no walk-forward survivor transition attempted).
  - Family B: stopped at `walkforward_survivor`, carrying one PERMANENT sealed evaluation with
    `verdict == "fail"` (real observations that miss the family's registered econ floor, via
    `micro_sealed_evaluation.evaluate_sealed_verdict` — never a hand-set `passed` field; mirror
    `test_micro_graduation.py::test_tc6_a_failed_sealed_evaluation_never_advances_and_is_carried_into_the_bundle`).
  - Family C: advanced to `sealed_survivor` (a genuine PASS sealed evaluation, distinct shard
    from Family B).
  - Family D: advanced all the way to `referee_handoff_ready` (mirror
    `test_micro_graduation.py::test_tc3_and_tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_handoff_ready`),
    so its bundle's `referee_registration_note` carries `REFEREE_FUTURE_REVISION_SENTENCE`
    verbatim, the same string the frontend's `GRADUATION_REFEREE_HANDOFF_NOTE` constant already
    quotes byte-for-byte.
  - Script prints each family's `family_root_id` + resulting `state` to stderr, exits 0 only if
    all four land in their target state and Family B's verdict reads `fail`.
- [ ] No change to any production module (`micro_graduation.py`, `micro_sealed_evaluation.py`,
  `micro_routes.py`, `vault.py`, `scout_ledger.py`, `walkforward.py`, `datasets.py`) — the new
  script imports and calls them exactly as shipped.
- [ ] New pytest coverage in `apps/backend/tests/` asserting the new seed script's own fixture
  is well-formed end to end (idempotent replay on a second run appends no duplicate rows; the
  four target states and the one `fail` verdict are exactly as specified) — a regression guard
  for the fixture script itself, not a production-code test.

### Browser evidence (two backend restarts against the SAME :8301/:3301 rig pair — the frontend's
`NEXT_PUBLIC_API_URL` stays fixed; only the backend's `TAPEOLOGY_MICRO_GRADUATION_DIR` changes
between passes; the persistent rig's DEFAULT/unscoped graduation directory — the one J-07's
stored golden replay script reads — is never touched by either pass):

- [ ] Capture 1 ("empty"): restart the :8301 backend with `TAPEOLOGY_MICRO_GRADUATION_DIR`
  pointed at a fresh, never-seeded scoped root (e.g.
  `apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-empty/graduation`); open `/desk`,
  expand the Graduation section, element-capture `[data-testid="graduation-families-block"]`
  showing the `graduation-families-empty` empty state with title `"No candidates ledgered."`
  and the `graduation-chain-verification` line reading `"ok"`.
- [ ] Capture 2 ("four-stage"): restart the same :8301 backend with `TAPEOLOGY_MICRO_GRADUATION_DIR`
  pointed at the new fixture root the seed script wrote; open `/desk`, expand the Graduation
  section, element-capture `[data-testid="graduation-families-block"]` showing all four family
  cards with their stage tokens (`exploratory`, `walkforward_survivor`, `sealed_survivor`,
  `referee_handoff_ready`), Family B's sealed-evaluation row with verdict `fail` visible (expand
  its `graduation-family-<id>-sealed-evaluation-rows` block if collapsed), and Family D's
  `graduation-family-<id>-referee-note` text.
- [ ] Restart the :8301 backend back onto its default (unscoped) configuration before the
  Required-still-passing replay pass runs, so J-07's stored golden (and every other journey's
  golden) replays against the unchanged, iter-18-seeded default state.

### New user-facing capability

None — the Graduation section itself already renders read-only for every operator today; this
iteration only proves, with genuine screenshots, two states of that existing render that had not
yet been photographed.

### New information displayed

None.

### New user actions

None — Graduation stays GET-only (T-8); no button, no compute act.

### UI surface changes

None — zero frontend code changes.

### Product surface delta

None from the operator's point of view; the delta is entirely in recorded QA evidence.

### Blueprint conformance

No new page or nav-skeleton change. Graduation's canonical home stays `/desk` → Graduation
(below Validation Vault), already registered in `blueprint.md`'s Information Architecture table
(iter-31 note). See the new iter-32 note appended to `blueprint.md`.

### Data-contract additions

None. `GET /research/desk/micro/graduation` (owner `micro_graduation.py` /
`micro_sealed_evaluation.py`) stays the sole computing module and sole serving endpoint for every
graduation value; this iteration introduces no second computation, no new endpoint, no new
served field.

## OUT OF SCOPE

- Any change to `micro_graduation.py`, `micro_sealed_evaluation.py`, `micro_routes.py`, the
  `desk_graduation` MCP tool, or the `/desk` Graduation frontend component — all shipped and
  verified at iter-31; "Do not redo."
- Re-seeding, wiping, or otherwise mutating the persistent :8301 rig's DEFAULT graduation
  directory (the one J-07's existing golden reads).
- Recording more real tape, revealing or assigning any sealed recording, or running the three
  pilot studies against the real recorded corpus (per iter-29's standing instruction, still in
  force).
- Re-litigating any of the six owner-dispositioned anti-goal findings — all `blocks_current_era:
  false`, all "Do not redo."
- The optional, non-blocking passenger items named at iter-29/30/31 (J-02/J-03 element
  close-ups, a journey-unique golden string for J-05) — genuinely optional; they may ride along
  ONLY if they do not delay this round, and are not part of this iteration's Definition of Done.
- Any Config field addition, fingerprint movement, or `referee_*` module change.

## DEFINITION OF DONE

- [ ] J-11 passes via browser-qa-agent: Capture 1 (empty ledger) is on record showing
  `"No candidates ledgered."` and chain verification `"ok"`.
- [ ] J-11 passes via browser-qa-agent: Capture 2 (fixture rig) is on record showing all four
  stage tokens.
- [ ] J-11 passes via browser-qa-agent: Capture 2 also shows the permanent FAILED sealed
  verdict row.
- [ ] J-11 passes via browser-qa-agent: Capture 2 also shows the referee-handoff-ready bundle
  copy sentence verbatim.
- [ ] `[NEW]`-flagged demo-narrator walkthrough step added for the Graduation section, its own
  screenshot containing what the narration claims (per T-10).
- [ ] Required-still-passing journeys (J-01, J-04, J-05, J-06, J-07, J-08, J-10) remain green —
  deterministic replay against the persistent rig's default (unscoped) state, LLM fallback for
  any journey without a golden.
- [ ] No anti-goal violation introduced: the new fixture rows are produced only by calling real
  production functions (never a hand-set `passed`/`state` field); no sealed shard is read before
  its recorded exposure; no second draw against any (family, shard) pair.
- [ ] Unit tests pass; no regressions; full backend suite passes at a count ≥ the iter-31 baseline
  (3,495 passed / 8 skipped / 0 failed) with `config_fingerprint()` still printing
  `08e471b10130e1e2`.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-32-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-11 (both captures above); Required-still-passing smoke set J-01, J-04, J-05, J-06,
  J-07, J-08, J-10.
- Unit/integration: new pytest coverage for the seed script's own fixture shape (four target
  states, one `fail` verdict, idempotent-replay safety on a second run).
- Error cases: the seed script must exit non-zero (and print which family/verdict diverged) if
  any of the four families lands in the wrong stage or Family B's verdict is not `fail` — a
  silently-wrong fixture must never be reported as a passing seed.

- TC-1: given a fresh backend restart on :8301 with `TAPEOLOGY_MICRO_GRADUATION_DIR` pointed at
  a never-seeded scoped root, when the browser opens `/desk` and expands the Graduation section,
  then `[data-testid="graduation-families-empty"]` renders with title `"No candidates ledgered."`
  and `[data-testid="graduation-chain-verification"]` renders the text `"ok"`, captured as an
  element screenshot.
- TC-2: given the same backend restarted instead with `TAPEOLOGY_MICRO_GRADUATION_DIR` pointed at
  the new four-family fixture root, when the browser opens `/desk` and expands the Graduation
  section, then four `[data-testid="graduation-family-<id>"]` blocks are visible whose header text
  reads `— exploratory`, `— walkforward_survivor`, `— sealed_survivor`, and
  `— referee_handoff_ready` respectively, captured in the same element screenshot.
- TC-3: given the same fixture rig, when Family B's `[data-testid="graduation-family-<id>-sealed-evaluation-rows"]`
  block is expanded, then it shows exactly one row with `verdict` text `fail`, and Family B's own
  header still reads `— walkforward_survivor` (the failed sealed evaluation never advanced its
  state), captured in the same or a follow-up element screenshot.
- TC-4: given the same fixture rig, when Family D's card is inspected, then
  `[data-testid="graduation-family-<id>-referee-note"]` renders text beginning "This
  referee_handoff_ready state does not imply the current Referee can register or adjudicate this
  candidate", matching the backend's `REFEREE_FUTURE_REVISION_SENTENCE` byte-for-byte, visible in
  the same screenshot.
- TC-5: given the new seed script run against a fresh scoped root, when it completes, then it
  exits 0, and re-reading Family B's row from disk through `GraduationLedger` shows `verdict ==
  "fail"` and `n == 30` derived from real recomputation (never a hand-set field) — confirmed by
  the new pytest coverage, not merely the script's own stdout.
- TC-6: given the seed script is run a second time against the SAME scoped root with identical
  inputs, when it completes, then no family's row count grows (each transition/evaluation call
  returns `"replayed"`, not a new appended row) — confirmed by the new pytest coverage.
- TC-7: given the `[NEW]`-flagged demo-narrator walkthrough step for the Graduation section, when
  the showcase lane runs it, then its own captured screenshot shows the Graduation section with
  the served empty-state copy on screen, matching the step's narration text.
- TC-8: given the full backend suite runs after this iteration's changes, when `pytest` completes,
  then it reports pass count ≥ 3,495, 8 skipped, 0 failed, exit code 0, and
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- TC-9: given the persistent :8301 rig is restarted back onto its default (unscoped) graduation
  directory after both captures, when J-07's stored golden replay script runs against it, then it
  passes unchanged (same assertion target as iter-31, no drift introduced by this iteration's
  scoped-root captures).

## NOTES

- Optional, non-blocking passengers (per iter-29/30/31 lessons): J-02/J-03 element close-up
  captures, and giving J-05's golden its own journey-unique assertion string instead of borrowing
  J-04's `"Ledger chain verification:"`. Include them ONLY if they add no material time to this
  round; they are not part of Definition of Done and must not delay Capture 1/2 or the walkthrough
  step.
- Interpretation call on "the real store" in J-11's acceptance text logged to
  `runs/goal-session-rapid-microscope/state/assumptions.md` (iter-32 entry): read as "an actual,
  unseeded, production-shaped store," not literally today's persistent-rig default directory,
  since the latter already carries the iter-18 single-family fixture and cannot show the empty
  state without disturbing J-07's existing golden.
- If, after this iteration, J-11 is `passing` and the six dispositioned anti-goal findings remain
  the only open items, the next iteration should follow the "zero remaining FAILING journeys"
  path — a one-line spec recommending the evaluator consider `GOAL_ACHIEVED` — per this agent's
  standing rule against manufacturing work.
