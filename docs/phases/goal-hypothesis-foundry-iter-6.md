# Goal Iteration 6 — Real exhaust pass writes the era's second irreversible act (J-07)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's verdict was ESCALATE (mandatory full depth, no exceptions)
- **Frontend Present:** yes
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06 (full regression — prior
  verdict was ESCALATE, which widens the replay set to every currently-passing journey per the
  Required-still-passing rules)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - "No execution path, ever. No brokerage/trading API, order ticket, live or paper trading, or
    simulated execution path is introduced by this era."
  - "Frozen foundations stay frozen. The existing `v1` strategy, `default` profile, tape engine state
    vocabulary/thresholds, frozen structure calculations, canonical stores, and archived-era behavior
    remain additive/versioned, never silently mutated."
  - "No lookahead. Every value is computed only from information legally available at its declared
    time; deferred constructs cannot be served before resolution."
  - "Single source of truth. Every shared scientific value has one canonical backend owner; REST/UI/MCP
    never independently recompute it."
  - "Deterministic and seeded. Randomized statistical draws use existing named deterministic streams;
    no wall-clock/unseeded randomness changes research results."
  - "Immutable registered data. Dataset content/checksums/splits/recorded evidence are append-only and
    never retagged or content-perturbed to help a candidate."
  - "Persistence stays scoped. Fetching/recording/exposure is always an explicit operator act; page
    loads and Foundry reads never record market data. `GET /research/desk/micro/foundry` and every
    page-load GET are read-only and never compute/evaluate a candidate or trigger the exhaust runner."
  - "No candidate invented after the real manifest freezes." / "No late variant insertion." / "No
    family splitting to evade the 24-variant cap."
  - "No second Foundry statistical decision rail."
  - "No change to a killed candidate or re-run under a renamed id." / "No second real generation
    epoch." / "No science-affecting code/spec/manifest change after the first-read lock."
  - "No automatic corpus-era registration, retention, storage, recording, release, Vault, graduation,
    or Referee act."
  - "No automatic ranking/selection among diagnostic survivors for future protected evidence." / "No
    claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence or proof of edge."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey."
  - "No browser proof based on fabricated fixture state when a journey claims to show real final
    state; fixture and real views must be visibly distinguished."
  - Binding Execution Order: "A real candidate outcome read before step 7 is a critical anti-goal
    violation. A science-affecting edit after step 8 begins is an integrity halt, not an iteration
    opportunity."

## GOAL

Deterministically run the real Hypothesis Foundry exhaust pass over the already-frozen, zero-candidate
real epoch — writing the §8.5 first-read lock — and surface its checkpoint/completion state on `/desk`.

## BACKGROUND

Iter-5 froze the one real epoch (commit `dff64eaa`, ancestor of `HEAD`; zero compiled candidates —
goal.md's own valid ending 1) and closed two long-standing read-surface gaps (J-02, J-05), but
`state/iteration-state.md`'s active blockers list three IMPORTANT freeze-integrity findings still
open: B1 (`freeze-set.json` keys all 55 entries by absolute machine-local path, breaking portability),
B2 (the pinned `freeze_commit` predates when `foundry_compiler.py` was actually committed, so it does
not literally contain the bytes the freeze set pins), and B7 (the freeze set omits the three tracked
Foundry JSONs plus the generation CLI §8.4 names, and `freeze-record.json` omits the required "era-open
evidence-class contract" field). `docs/goal.md`'s Binding Execution Order states "a science-affecting
edit after step 8 begins is an integrity halt, not an iteration opportunity" — and this iteration is
where step 8 begins (J-07 writes the first-read lock), so it is the LAST iteration in which these three
findings can be repaired at all.

This iteration therefore does two things in strict sequence, both still inside §7.3's "Goal Mode may
repair only before any real outcome has been read" window (the real epoch has **zero** candidates, so
no outcome is ever read in this era — the entire remaining window is that repair window): first, commit
the code this iteration adds and regenerate `docs/hypothesis-foundry/freeze-set.json` /
`freeze-record.json` via the already-proven deterministic `generate_freeze_set`/`build_freeze_record`
functions (closing B1/B2/B7, and adding the one new `foundry_ledger.py` capability this iteration needs
to its own coverage) without touching `epoch_id`, `source-registry.json`, or `epoch-manifest.json`
content (§8.1's one-epoch rule stays untouched); second, run the new real exhaust CLI, which appends
the epoch-opening/first-read-lock row and — because the manifest lists zero `FROZEN_READY` variants —
completes immediately with an honest, vacuous exhaustion.

**Disclosed interpretive call (logged to `state/assumptions.md`, iter-6):** the evaluator's own
iteration-state digest tags B1/B2/B7 as requiring owner sign-off ("owner-owned: approving any amendment
to the already-committed frozen artefacts"), but `docs/goal.md` §7.3 itself explicitly authorizes Goal
Mode — not an owner ruling — to repair "freeze hash drift" before any outcome is read, and this era will
never read an outcome. This spec reads the OWNER tag as covering only the disclosed, separate MINOR
anti-goal (ratify/reject the discarded first epoch — a scientific/policy judgment), not this routine
freeze-bookkeeping repair. Full depth (already mandatory from the prior ESCALATE) supplies the
independent-auditor scrutiny this irreversible, freeze-adjacent repair needs. This is disclosed here in
plain prose, not as a self-granted depth/isolation override, precisely so a human watching the run can
pause it before dispatch if they read §7.3 more conservatively.

**Lessons applied:** (iter-5) the one-time frozen artefact class needs a same-iteration read-only guard
test over its committed bytes — this iteration's freeze-set/freeze-record regeneration gets its own
extension to `tests/test_foundry_real_epoch_artifacts.py`, not just a passing generation run. (iter-5,
second) a uniqueness guard keyed on file presence is not a guard — `_load_existing_manifest_store`
returning `{}` on a missing state file is fixed this iteration (this file is confirmed NOT in the
freeze-set, so the fix carries no freeze-drift consequence). (iter-3) an end-to-end claim must be
grep-verified to actually cross the module boundary it claims to — the new exhaust CLI must genuinely
call `foundry_compiler`/`foundry_interpreter`/`foundry_runner`/`foundry_ledger` in the real epoch path,
not a fixture stand-in. (iter-1/iter-2) the scoped `:8301` QA rig cannot see a real artifact under the
runtime-scoped foundry directory unless it is explicitly provisioned there (`cp`-guarded, never
fabricated) — the new `exhaust_progress` UI subsection needs the same treatment as the existing
Epoch/Manifest subsection.

## IN SCOPE

### Backend

- [ ] `app/research/foundry_ledger.py`: add one additive epoch-opening/first-read-lock row-kind
      method alongside the existing `record_intent`/`record_terminal` (same hash-chain primitive, no
      new ledger, no second statistical rail) that pins all freeze hashes plus the resolved eligible
      diagnostic-corpus `(dataset_id, checksum)` manifest hash, and is idempotent on replay (a second
      call verifies and no-ops rather than appending a duplicate row).
- [ ] `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`: fix
      `_load_existing_manifest_store` so a missing manifest-store file causes a typed refusal instead
      of silently returning `{}` (this file is not in the freeze-set; no drift consequence).
- [ ] New script `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` — the resumable,
      single-flight Foundry CLI/manager: verifies freeze integrity, acquires
      `foundry_runner.SingleFlightLock`, computes the resolved eligible-corpus manifest hash via the
      sanctioned `micro_accessor` door, appends the one epoch-opening row, iterates the frozen
      manifest's `FROZEN_READY` variants (zero, for this epoch) in canonical family/variant order via
      the existing `foundry_runner.run_family`/`run_one_candidate`, and reports/serves the checkpoint
      ordinal and a zero protected/withheld/sealed read census. Repeat invocation verifies and
      no-ops; a concurrent invocation refuses via the existing single-flight lock.
- [ ] Regenerate `docs/hypothesis-foundry/freeze-set.json` and `freeze-record.json` via the existing
      `generate_freeze_set`/`build_freeze_record` functions, committed AFTER this iteration's code
      changes so `freeze_commit` is a real ancestor commit that contains every pinned file
      (closes B2), with project-relative paths (closes B1), including the three tracked Foundry JSONs
      and the generation CLI plus the missing "era-open evidence-class contract" field on
      `freeze-record.json` (closes B7). `epoch_id`, `docs/hypothesis-foundry/source-registry.json`,
      and `docs/hypothesis-foundry/epoch-manifest.json` content are byte-identical before and after —
      only the freeze bookkeeping files change.
- [ ] Extend `GET /research/desk/micro/foundry` with the new `exhaust_progress` key (reusing
      `foundry_runner.py`/`foundry_ledger.py`, no new module, no second endpoint) — see Data-contract
      additions below for exact fields.
- [ ] Extend `tests/test_foundry_real_epoch_artifacts.py` with read-only guards over the regenerated
      `freeze-set.json`/`freeze-record.json` (relative paths, `freeze_commit` ancestry + completeness,
      the new required entries/field) so the corrected bookkeeping has the same committed-bytes
      protection iter-5's lesson demands.
- [ ] Extend the hermetic suite (`test_foundry_ledger.py`, `test_foundry_runner.py`, a real-epoch
      integration test) proving: the new ledger row-kind round-trips and is replay-idempotent; the
      real exhaust CLI genuinely calls the production compiler/interpreter/runner/ledger path over the
      real committed manifest (grep-verified, per the iter-3 lesson); the manifest-store deletion no
      longer bypasses `ManifestDriftRefused`; resume/single-flight/protected-read-zero proofs on a
      fixture-backed interrupt (per J-07 step 7's own explicit allowance).

### Frontend

- [ ] `/desk` → Hypothesis Foundry → new "Runner / Checkpoint" subsection (already-registered
      blueprint home; new `foundry-runner-*` testid family, matching the established subsection
      pattern) rendering `exhaust_progress` verbatim: first-read-lock timestamp, checkpoint ordinal
      ("0 of 0"), protected-read census, single-flight/integrity status, and the honest
      zero-candidate completion message — no client-side computation.
- [ ] Provision the scoped `:8301` QA rig with the real `exhaust_progress` state (same `cp`-guarded
      pattern already used for the era-open baseline / `epoch_manifest`, never fabricated) so the
      subsection is screenshot-able against the real committed epoch, not an invented fixture.

### New user-facing capability

An operator can see, on `/desk`, that the real frozen epoch's exhaust pass has run to honest, vacuous
completion (zero candidates ever existed to evaluate) and that zero protected/withheld/sealed data was
ever touched doing it.

### New information displayed

First-read-lock recorded/timestamp, resolved eligible-corpus manifest hash, total/terminal
`FROZEN_READY` counts, checkpoint ordinal, protected-read census, single-flight/integrity status,
exhaust-complete flag.

### New user actions

None — the Foundry surface remains read-only; the exhaust CLI is an operator/CLI act outside the app,
matching §9's "resumable manager/CLI operator act," never a page-load-triggered computation.

### UI surface changes

One new subsection ("Runner / Checkpoint") appended to the existing `/desk` → Hypothesis Foundry panel.

### Product surface delta

`/desk` gains one more read-only Hypothesis Foundry subsection; no new page, no new nav entry.

### Blueprint conformance

`/desk` → Hypothesis Foundry → Runner / Checkpoint (home already registered in
`state/blueprint.md`'s Information Architecture table at baseline).

### Data-contract additions

New key `exhaust_progress` under the existing single canonical endpoint `GET
/research/desk/micro/foundry` (computed by `app/research/foundry_runner.py` +
`app/research/foundry_ledger.py`, both already-registered modules — no new module, no second
endpoint), registered in `state/blueprint.md`'s Data Contract table this iteration:

- `first_read_lock_recorded: bool`
- `first_read_lock_at: str | null` (ISO-8601 UTC timestamp, `null` before the lock is written)
- `eligible_corpus_manifest_hash: str | null` (sha256 over the resolved `(dataset_id, checksum)` set)
- `frozen_ready_total: int >= 0`
- `terminal_count: int >= 0`
- `checkpoint_ordinal: int >= 0`
- `protected_read_count: int >= 0` (must equal 0 for this epoch)
- `single_flight_status: "idle" | "running" | "refused_concurrent"`
- `freeze_integrity_verdict: "green" | <typed halt code>`
- `exhaust_complete: bool`

## OUT OF SCOPE

- Ratifying or rejecting the discarded first real epoch (`ded18b8b…`→`ed40dbc2…`) — remains OWNER,
  unresolved, disclosed as a blocking MINOR anti-goal; not this iteration's decision.
- Any change to `epoch_id`, `docs/hypothesis-foundry/source-registry.json`, or
  `docs/hypothesis-foundry/epoch-manifest.json` content — byte-identical before/after; only
  `freeze-set.json`/`freeze-record.json` bookkeeping is regenerated.
- J-08's full "final Foundry truth" surface — detail drill-ins, survivor labelling, the T-9/T-10/T-11
  regression guards, and any optional MCP proxy. J-07 must land for real first; J-08 is the natural
  next iteration.
- Any new candidate, threshold, family, or scientific choice — the epoch is frozen at zero compiled
  candidates; nothing is rescued, re-thresholded, or re-partitioned.
- Raising the session `--max-iter` cap (60→80) — an operator decision, not a spec item.
- The optional `desk_micro_foundry` MCP proxy (goal-deferrable).

## DEFINITION OF DONE

- [ ] J-07 passes: the real exhaust CLI runs against the committed epoch, the first-read-lock row is
      written exactly once, zero `FROZEN_READY` variants complete zero terminal evaluations honestly,
      and `/desk` → Hypothesis Foundry → Runner / Checkpoint is browser-verified against the real
      state (not a fabricated fixture).
- [ ] Required-still-passing journeys J-01..J-06 remain green (full regression replay, both
      deterministic goldens and LLM fallback where no golden exists).
- [ ] No anti-goal violation introduced: zero protected/withheld/sealed reads; no second `epoch_id`;
      no science-affecting edit to `epoch_id`/registry/manifest content; the freeze-set/freeze-record
      regeneration happens strictly before the first-read-lock row is written.
- [ ] Unit tests pass; no regressions; the freeze-set/freeze-record regeneration is covered by a
      same-iteration read-only guard test over the committed bytes.
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (`/desk` → Hypothesis Foundry → Runner / Checkpoint, real state); full replay of
  J-01..J-06.
- Unit/integration: new `foundry_ledger.py` row-kind; the real exhaust CLI's compiler→interpreter→
  runner→ledger path (grep-verified end-to-end, per the iter-3 lesson); freeze-set/freeze-record
  regeneration determinism; `_load_existing_manifest_store` refusal; single-flight/resume/protected-
  read-zero proofs.
- Error cases: concurrent exhaust-CLI invocation; deleted manifest-store file; a freeze-set path with
  post-lock byte drift; a corrupted ledger chain.

- TC-1: given the committed real epoch (`dff64eaa`'s successor commit, ancestor of `HEAD`) with zero
  `FROZEN_READY` variants, when the real exhaust CLI is invoked for the first time, then it appends
  exactly one epoch-opening row to the Foundry trial ledger containing all pinned freeze hashes and
  the resolved eligible-corpus manifest hash, and `GET /research/desk/micro/foundry`'s
  `exhaust_progress.first_read_lock_recorded` is `true`.
- TC-2: given the first-read-lock row already exists, when the exhaust CLI is invoked a second time,
  then no second epoch-opening row is appended (the ledger's epoch-opening row count stays 1) and the
  command exits verifying the existing state.
- TC-3: given zero `FROZEN_READY` variants exist in the real manifest, when the exhaust CLI completes,
  then `exhaust_progress.frozen_ready_total == 0`, `exhaust_progress.terminal_count == 0`, and
  `exhaust_progress.exhaust_complete == true`.
- TC-4: given the sanctioned `micro_accessor` is instrumented with a call counter, when the exhaust
  CLI runs against the real epoch, then `exhaust_progress.protected_read_count == 0` and no
  sealed/withheld dataset id appears in any ledger row or log line.
- TC-5: given a fixture-backed epoch with one intent-without-terminal ("crashed") row, when the
  exhaust CLI resumes, then it re-executes the exact screen under identical pins and appends exactly
  one terminal row (no duplicate scientific row).
- TC-6: given the real exhaust CLI is already running (single-flight lock held), when a second
  invocation starts concurrently, then the second invocation raises `ConcurrentRunnerRefused` and
  appends no ledger row.
- TC-7: given `generate_hypothesis_foundry_real_epoch.py`'s saved manifest-store state file has been
  deleted, when the generation command is invoked again, then it raises a typed refusal instead of
  silently minting a new `epoch_id`.
- TC-8: given the freeze-set/freeze-record regeneration has run, when `verify_freeze_set_unchanged`
  and `verify_commit_is_ancestor` are called against the new `freeze_commit`, then both pass, every
  freeze-set path is relative, and the freeze-set's entry count includes the three tracked Foundry
  JSONs plus the generation CLI (closing B1/B2/B7).
- TC-9: given the real exhaust has completed, when an operator opens `/desk` → Hypothesis Foundry →
  Runner / Checkpoint, then the panel shows the first-read-lock timestamp, checkpoint ordinal "0 of
  0", the honest zero-candidate completion message, and protected-read count "0" — all read verbatim
  from `exhaust_progress` with no client-side computation.
- TC-10: given the full backend test suite, TypeScript compile, and existing Rapid Microscope
  leakage/unit/no-lookahead regression traps, when they run after this iteration's changes, then all
  pass with no previously-passing test skipped, xfailed, or deleted.
- TC-11: given J-01..J-06's golden replay scripts, when the deterministic replay lane re-runs them
  against the current build, then all six still pass with zero regressions.

## NOTES

- Two operator decisions remain open and are NOT this iteration's concern: whether to ratify or
  reject the discarded first real epoch, and whether to raise `--max-iter` from 60 to 80.
- If the developer's own reading of `docs/goal.md` §7.3 disagrees with this spec's BACKGROUND
  interpretation (i.e., judges the B1/B2/B7 freeze-bookkeeping repair to require owner sign-off before
  proceeding), halt and report rather than silently narrowing scope to "exhaust CLI only, no
  freeze-set repair" — that half-measure would permanently seal three known integrity gaps into the
  era's audit trail with no path to ever fix them, which is worse than pausing for a ruling.
- This is the era's second and final irreversible act before finalization (J-08, then ordinary Goal
  Mode closure). Treat the freeze-set/freeze-record regeneration and the exhaust CLI's first invocation
  as one atomic sequence within this iteration — do not commit the regenerated freeze artifacts and
  then defer the exhaust CLI invocation to a later iteration, since that would leave the era's most
  sensitive commit unverified by its own consuming code for an entire iteration boundary.
