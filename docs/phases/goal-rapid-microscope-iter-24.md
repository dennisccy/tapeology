# Goal Iteration 24 — Close the sealing-time leak, re-verify J-07/J-09, give J-09 a golden

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 24
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the iter-23 evaluator verdict was ESCALATE (mandatory, no exceptions). In
  substance this also matches trigger 1: this iteration's own remediation lands directly inside
  `apps/backend/scripts/j06_operator.py`'s `stage_tr2()` and `apps/backend/app/research/vault.py`'s
  shard serializer — the exact never-independently-audited operator surface iter-23 named — but
  trigger 3 alone already makes full mandatory, so no further justification is required.
- **Frontend Present:** yes
- **Target journeys:** J-06, J-07, J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08, J-10 (full remaining set
  — vault.py is shared serving code for readiness/J-08/MCP; see BACKGROUND)
- **Anti-goal reminders:**
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*
  - **Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate; that awaits a future named revision of
    the referee spec. *(critical)*

## GOAL

Close the one open minor anti-goal item the iter-23 auditor found (the sealing-time leak that lets
a served per-shard `sealed_at` timestamp be joined against the committed per-run seal counts to
narrow one shard's candidate identity), and re-verify J-07 and J-09 with fresh browser evidence —
including a stored golden replay script for J-09 so it stops riding the slow LLM lane every round.

## BACKGROUND

Iteration 23 closed J-06 (the era's last non-passing journey — all ten Must-have journeys now read
`passing`) but ended `ESCALATE`, not `CONTINUE`, for a reason written into the engine's own depth
ladder: iter-23 overran its wall-clock budget, which forces the NEXT round to `lean` (no audit
lane) unless this round's own verdict grants full outright. It did, and it named four things in
priority order, explicitly asking that if the clock bites again, item 3 drops first, then item 2,
never item 1: **(1)** re-check J-07 and J-09 first (the budget cut both to `DEFERRED-BUDGET` this
round; they keep their iter-22 stamps and the deterministic achievement gate will not clear until
both get a fresh look) and write J-09 a stored golden while there; **(2)** close the sealing-time
leak (widen the run-aware TR-2 model, don't just re-read the old one); **(3)** let the audit lane
read the ~4,200 lines of never-goal-mode-reviewed recorder/vault/operator code end to end, not just
this round's diff. This spec keeps all three, in that order, and keeps the round deliberately small
per the same recommendation.

Per the priority rubric: no journey regressed (rule 1 moot); the last coherence verdict was
`COHERENCE-PASS` (rule 2 moot, no consolidation mandated); J-06/J-07/J-09 are the only journeys with
open work, and none are human-blocked (rule 6 moot — the blocker the evaluator named, "the checker
must independently read the never-audited operator code," is machine work, not an owner act). I
picked J-06 as a THIRD target (beside the eval's named J-07/J-09) because the sealing-time-leak fix
lands inside `vault.py`'s served shard projection — the exact surface J-06's acceptance governs —
so the fix needs J-06 re-verified alongside it, not left to a bystander regression check.

I verified the leak myself before scoping the fix (never inheriting the finding blind): the
committed `reports/j06-tranche/recording-runs.json` really does carry `sealed_this_run` = 7, 13, 1,
0, 0 across its five runs (read directly, `python3 -c "json.load(...)"`), and `vault.py:380`'s
`_OPAQUE_SHARD_KEYS` really does include a full-precision `sealed_at` in every served shard row
(`_serialize_shard`, `vault.py:1486`) with no coarsening. The existing `stage_tr2()` combinatorial
check (`j06_operator.py:748`) never reads `recording-runs.json` at all — it computes only from the
registered universe size, the published selected count, and disclosed non-selected positions
(`residual_pool_uncertainty`, `j06_operator.py:719`), so this channel is a genuine blind spot in
the automated check, not merely an unread number. I also re-derived the r5 anti-goal's actual
governing test — "no still-unexposed vault-eligible shard is identifiable with certainty," i.e.
never fewer than 2 candidates — and confirmed the EXISTING code already asserts exactly that floor
(`candidate_identities_per_unexposed_selected_shard >= 2`, `j06_operator.py:803`). The iter-23
evaluator's own manually-computed worst case (4 candidates) does not cross that floor today; the
defect is that the automated check cannot see this channel at all, so a future run could cross it
silently. The fix is therefore two things, not one: narrow the actual served channel (so today's
real margin widens, not just gets monitored), AND make `stage_tr2()` compute this channel so a
future violation cannot pass silently. I chose to narrow it by coarsening the SERVED `sealed_at`
(a display-layer change inside `_serialize_shard`, per-shard opaque projection only) rather than
editing the already-committed `reports/j06-tranche/recording-runs.json` in place — rewriting a
committed operator report's historical numbers is itself in tension with this project's record-
integrity discipline, whereas narrowing what a still-live serving endpoint discloses going forward
is not. Logged to `assumptions.md` (this iteration's entry) as a genuine interpretation call, since
iter-23's own recommendation offered both as an "or" without choosing.

**Lessons applied.** (iter-18, first: shared-rig rule) any lane that mutates the QA fixture rig's
ledger state must be inside the "re-run the full replay set before calling it done" rule; the new
J-09 golden script WILL mutate the Scout Ledger the same rig's `J-08.json` reads as empty by
design (`"No candidates ledgered."`), so it is explicitly named below. (iter-18, second: `Frontend
Present`) set to `yes` here even though no frontend file is expected to change, because the DoD
names `browser-qa-agent`. (iter-19, second: J-07 cannot have a golden) not attempted here — J-07
stays on the LLM lane by design; only J-09 gets a new stored script. (iter-21/22, non-self-
verification and vacuous tests) the new TR-2 widening must be proven non-vacuous the same way
Study 3's fix was — show the OLD join would have failed the new floor before trusting that the new
check bites. (iter-23, both: run-aware combinatorial modeling AND the depth-ladder's `full-cap`
rung) this spec asks the auditor to read the named files in full, not just this round's diff hunks
— but per this agent's own instructions I cannot self-grant `Depth enforcement: required` (that is
an operator-only line; a self-written one is exactly the anti-pattern-25 governor bypass). If the
`full-cap` cost rung demotes this spec anyway, the human running the loop is the one who can set
`CHAIN_REQUIRE_FULL_DEPTH` for this iteration — flagged here rather than self-granted.

## IN SCOPE

### Backend

- [ ] Coarsen the SERVED `sealed_at` value in `vault.py`'s `_serialize_shard` (the opaque
  `_OPAQUE_SHARD_KEYS` projection, `vault.py:380`/`:1486`) from full-precision ISO timestamp to
  date-only precision, for every exposure state (`sealed`/`assigned`/`exposed`) so the field's
  shape stays uniform. This is a serve-time-only change: the underlying shard-ledger row's stored
  `sealed_at` stays byte-identical and is never rewritten (append-only discipline holds).
- [ ] Widen `stage_tr2()` (`j06_operator.py:748`) with a new run-aware half: consume the committed
  `reports/j06-tranche/recording-runs.json` per-run `sealed_this_run` counts and `at` timestamps,
  join them against the (now-coarsened) served per-shard `sealed_at` values, and compute the
  residual candidate-identity count for every run-time-bucket. Assert it against the SAME existing
  r5 certainty floor already enforced by the combinatorial half (`>= 2`,
  `candidate_identities_per_unexposed_selected_shard >= 2` at `j06_operator.py:803`) — do not
  invent a new floor number. `stage_tr2()` must still hard-fail (`SystemExit`, matching its
  existing behavior) if the widened check is ever violated.
- [ ] Extend `test_j06_operator.py` (which already covers `residual_pool_uncertainty` at lines
  249-268) with: (a) a test proving the widened run-aware check passes against the REAL committed
  `recording-runs.json` + the now-coarsened `sealed_at` values; (b) a non-vacuity counter-test that
  feeds the OLD full-precision `sealed_at` join (a synthetic fixture reproducing the 7/13/1/0/0
  split against fine-grained timestamps) through the same widened logic and proves it correctly
  FAILS — the same break-then-restore proof pattern this era used for the Study-3 fix.
- [ ] Extend `test_vault.py` (alongside `test_tc6_a_sealed_shards_entry_carries_only_the_section_
  7_5_opaque_fields`, line 272) with an assertion that every served `sealed_at` value matches a
  date-only shape (no time-of-day component) for a `sealed`-state row, and that the underlying
  ledger row's own stored `sealed_at` field is untouched (still full precision) — proving the
  coarsening is a serve-time-only projection, not a ledger rewrite.
- [ ] Re-verify J-07 "Graduation" with a fresh browser-qa pass against the standard scoped QA rig
  (`qa_playbook_iter7_fixture_scoped_backend.sh`). Confirm zero diff to `micro_graduation.py` /
  `micro_sealed_evaluation.py` this iteration (grep-confirm against the iter-17/18 baseline) before
  relying on evidence durability — this round still needs a FRESH, dated screenshot (T-10; a
  carried-forward stamp is not acceptable a third round running).
- [ ] Re-verify J-09 "The pilot studies" the same way: fresh browser-qa pass confirming the three
  ledgered families (range-wall failed aggression, delta divergence, capitulation exhaustion) each
  still carry their recorded decision, evidence class, and disclosures unchanged since iter-22.
- [ ] Write `journey-scripts/J-09.json`: a stored deterministic replay script that (a) triggers at
  least one pilot-study Scout compute via the existing operator-reachable
  `POST /research/desk/micro/scout/compute` grid-selector path (mirroring how
  `delta_divergence_pilot`/`range_wall_failed_aggression_pilot`/`capitulation_exhaustion_pilot`
  are already triggered per the iter-21/22 dev handoffs), then (b) asserts a J-09-specific rendered
  string in the Scout Ledger and/or Walk-Forward sections on `/desk` — a candidate family id, grid
  name, or its closed-vocabulary decision, never a pre-existing unrelated Desk heading (the
  iter-18/iter-19 "cannot fail" replay lesson). Verify the assertion is discriminating with the
  same break-then-restore method used for Study 3: temporarily mutate the target string, confirm
  the step goes red, then restore byte-identical.
- [ ] Because this new script mutates the SAME shared QA rig `J-08.json`'s step 3 reads as empty
  (`"No candidates ledgered."`), re-run the FULL stored replay set (J-01, J-02, J-03, J-04, J-05,
  J-06, J-08, J-09, J-10) after adding J-09.json and reconcile any now-stale assertion in the SAME
  iteration — sequence J-09's mutating step so it never runs before another script's empty-state
  check within one shared rig invocation, or make the affected empty-state assertion order-
  independent. Never leave a collision for a later round to discover (iter-18 lesson).
- [ ] Independently read `apps/backend/scripts/j06_operator.py` and
  `apps/backend/app/research/tick_recorder.py` end to end (not only this round's diff hunks) —
  the auditor's own named ask from iter-23, applying `docs/rapid-validation-spec.md` as ground
  truth. Record findings in the dev handoff; fix a genuine defect as the smallest possible change
  if one is found (do not treat finding-and-fixing as scope creep).

### Frontend

- [ ] No code changes expected — the vault shard serializer change is served, read-side text; the
  existing `ValidationVaultSection` renders whatever `sealed_at` string the route now serves,
  generically. If a real rendering issue surfaces only against the now-coarsened value (not
  previously exercisable), fix it as the smallest possible change and record it in the dev
  handoff.

### New user-facing capability

None. This iteration narrows what a metadata field discloses and re-verifies two already-shipped
journeys; no new control, page, or button.

### New information displayed

None new — `sealed_at` keeps its existing name, owner, and endpoint; only its served precision
narrows (full timestamp → date-only).

### New user actions

None.

### UI surface changes

None structural. The Validation Vault section's `sealed_at` display shows a coarser string.

### Product surface delta

Cosmetic-only: a sealed shard's displayed sealing time loses its time-of-day component. Everything
else on `/desk` is unchanged.

### Blueprint conformance

Validation Vault (J-06), Graduation (J-07, keyless/automated via Scout Ledger/Walk-Forward/Vault),
and Pilot studies (J-09, via Scout Ledger/Walk-Forward) are already registered under
`Desk → Rapid Microscope` in `blueprint.md`'s Information Architecture. No new page, no nav-
skeleton change.

### Data-contract additions

None — this iteration narrows the served PRECISION of the already-registered `sealed_at` sub-field
of the "Vault shards, universes, exposure ledger" Data Contract row (owner `vault.py`, endpoint
`GET /research/desk/micro/vault`), same name, same owner, same endpoint, same string type, only a
coarser value. `blueprint.md` gets an iter-24 note recording this (see below); no table row edit.

## OUT OF SCOPE

- Editing the already-committed `reports/j06-tranche/recording-runs.json` historical entries —
  record-integrity discipline; the fix narrows what is served going forward and widens the
  automated check, it does not retroactively redact a committed operator report.
- The `desk_micro_readiness` MCP 10-second timeout / ~13.5s-warm Desk-readiness-panel latency —
  named "a passenger fix" by iter-23, and squarely UI/MCP polish, the FIRST category the goal's own
  scope-pressure priority order defers. Carried to the next digest, not built here.
- Collapsing the duplicated study-selector list (`micro_routes.py` vs `scout.py`) — cosmetic,
  carried from iter-22, not one of this round's three named priorities.
- Any change to sealed-shard exposure/assignment logic, real-corpus re-run of J-09's studies,
  re-recording tape, or exposing/assigning any real sealed shard — all explicitly forbidden by
  `iteration-state.md`'s "Do not redo" list.
- Any Referee, engine, or frozen-research-vocabulary change.
- A full ~2-hour backend-suite re-run as a blanket gate — this era has overrun its wall-clock
  budget three rounds running (21, 22, 23); run targeted suites for touched modules
  (`test_vault.py`, `test_j06_operator.py`, `test_scout.py`, the fingerprint/referee-freeze/MCP-
  tool-count guards) plus the trap suite (TR-1…TR-30), matching iter-23's own targeted approach.
  The auditor may still choose to run the full suite if time allows.
- The sealed judge's economic-floor ruling and the ~150-symbol-day research-readiness gate —
  owner-owned, block no journey, untouched this iteration.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: the Validation Vault section renders sealed shard rows with
  the new date-only `sealed_at` precision; no per-shard symbol/date visible for any still-sealed
  shard (unchanged from iter-23's proof).
- [ ] J-07 passes via browser-qa-agent with a FRESH screenshot dated this iteration (not a
  carried-forward stamp).
- [ ] J-09 passes via browser-qa-agent AND via the new stored golden replay script
  (`journey-scripts/J-09.json`), which is discriminating (proven by the break-then-restore method).
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-08, J-10) remain green via
  deterministic replay, with the full stored replay set re-run after J-09.json lands and zero
  collisions found (or any found collision reconciled in this same iteration).
- [ ] The widened `stage_tr2()` run-aware check passes against the real committed
  `recording-runs.json` + coarsened `sealed_at` values, and is proven non-vacuous (fails against
  the old full-precision join in a counter-test).
- [ ] No anti-goal violation introduced; the sealing-time-leak minor item is CLOSED, not merely
  reduced — the auditor confirms both halves (narrowed channel + widened check) independently.
- [ ] Unit tests pass for all touched modules; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-24-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-06 (Validation Vault section, coarsened `sealed_at`), J-07 (fresh LLM-lane
  walkthrough against the standard scoped QA rig), J-09 (fresh LLM-lane walkthrough AND the new
  stored golden replay).
- Unit/integration: `test_vault.py` (shard-serializer precision + ledger-row-untouched proof),
  `test_j06_operator.py` (widened `stage_tr2` + non-vacuity counter-test), the full TR-1…TR-30
  trap suite, the fingerprint-pin test, the referee byte-freeze test, `test_mcp_server.py`
  `EXPECTED_TOOLS` (still 26, unchanged), `test_scout.py` J-09 candidate tests (must stay green,
  untouched).
- Error cases: `stage_tr2()` must still exit non-zero (`SystemExit`) if the widened run-aware
  check's candidate-identity floor is ever violated — proven via the counter-test fixture, never
  merely asserted in prose. The vault route must still refuse (typed error, not a degraded 200)
  any attempt to read a still-sealed shard's symbol/date.

Test-first contract:

- TC-1: given the real committed `reports/j06-tranche/recording-runs.json` (`sealed_this_run` =
  7, 13, 1, 0, 0 across five runs) and the vault's 21 sealed shard rows, when `_serialize_shard`
  serves a `sealed`-state row, then its `sealed_at` value matches a date-only shape (e.g.
  `^\d{4}-\d{2}-\d{2}$`) with no time-of-day component.
- TC-2: given the same sealed shard row, when the underlying shard-ledger record on disk is read
  directly (not through `_serialize_shard`), then its stored `sealed_at` field is still the
  original full-precision ISO timestamp, byte-identical to before this iteration — proving the
  coarsening is serve-time-only.
- TC-3: given the real committed `recording-runs.json` and the now-coarsened served `sealed_at`
  values, when the widened `stage_tr2()` run-aware check computes the residual candidate-identity
  count for every run-time-bucket, then every bucket's count is `>= 2` (the same floor
  `stage_tr2()`'s existing combinatorial half already enforces) and `stage_tr2()` exits 0.
- TC-4: given a synthetic fixture reproducing the OLD full-precision `sealed_at` join against the
  same 7/13/1/0/0 per-run counts, when the widened run-aware check runs against that fixture, then
  it correctly reports a violation (a bucket's candidate count `< 2`, or the check otherwise
  fails) — proving the new check is non-vacuous, not merely present.
- TC-5: given the scoped QA backend rig with J-09's pilot-study grid selectors reachable via
  `POST /research/desk/micro/scout/compute`, when `journey-scripts/J-09.json`'s trigger step runs,
  then a new Scout Ledger row appears for at least one pilot-study family with a decision in the
  closed vocabulary, and the script's assertion step reads that row's discriminating string.
- TC-6: given `journey-scripts/J-09.json` with its target assertion string temporarily renamed,
  when the deterministic replay harness runs it, then the step FAILS (goes red); with the string
  restored byte-identical, the step PASSES — proving the golden is discriminating, not vacuous.
- TC-7: given the full stored replay set (J-01…J-06, J-08, J-09, J-10) run in sequence against one
  shared QA rig invocation, when J-09.json's mutating compute step and J-08.json's
  `"No candidates ledgered."` empty-state step both execute, then neither collides with the other
  (either by sequencing or by an updated, order-independent assertion) — zero regression across
  the full set.
- TC-8: given J-07 "Graduation" with zero diff to `micro_graduation.py`/`micro_sealed_evaluation.py`
  this iteration, when browser-qa re-runs its LLM-lane walkthrough, then it reproduces the
  iter-22-verified graduation states with a screenshot timestamped this iteration.
- TC-9: given the real store, when `GET /research/desk/micro/vault` is called for an `assigned` or
  `exposed`-state shard (if any exist), then its `sealed_at` value is ALSO date-only precision
  (uniform coarsening across all three exposure states, not sealed-only).

## NOTES

- Depth-enforcement caution: iter-23's own `full-cap` cost rung demoted a full spec even with a
  written `Full trigger:` line. This spec cannot self-grant `Depth enforcement: required` (an
  operator-only line — writing it here would be the anti-pattern-25 governor bypass). If the human
  running this loop wants to guarantee the audit lane survives the cost rung for this iteration
  (given it independently reads ~4,200 lines of never-goal-mode-reviewed operator code), they can
  set `CHAIN_REQUIRE_FULL_DEPTH` for this run; otherwise the round proceeds at whatever depth the
  arbiter grants.
- If the independent read of `j06_operator.py`/`tick_recorder.py` surfaces a genuine defect beyond
  the sealing-time leak, fix it as the smallest possible change and document it plainly in the dev
  handoff — this is exactly this iteration's purpose for that surface, not scope creep.
- If all of J-06/J-07/J-09 pass cleanly and the sealing-time-leak item closes, all ten Must-have
  journeys are passing with zero open critical anti-goal items; the next evaluator should weigh
  GOAL_ACHIEVED against the two remaining open owner rulings (`iteration-state.md`: the sealed
  judge's money-floor source, and the honestly-unmet ~150-symbol-day gate) — neither blocks any
  journey's acceptance text per the iter-20 lesson on not perpetuating a stale blocker without
  re-testing it.
- Host-guard caps remain law for any backend instance or suite run this iteration (CPU mask
  `4-7,12-15`, per `project-extensions/host-guard/host-guard.env`).
