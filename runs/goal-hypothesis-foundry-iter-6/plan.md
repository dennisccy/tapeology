# goal-hypothesis-foundry-iter-6 Execution Plan

## Alignment check

Directly advances `docs/goal.md`'s Foundry era: this is Binding Execution Order **step 8** (the
real deterministic exhaust pass / §8.5 first-read lock, J-07), the mandatory next target after two
consecutive ESCALATE verdicts (iter-4, iter-5) and after iter-5 crossed step 7 (the real epoch
`dff64eaa` frozen, zero compiled candidates — goal.md's own valid ending 1). No drift from goal.md
detected: the phase spec's freeze-set/freeze-record repair (B1/B2/B7) is explicitly grounded in
§7.3's "Goal Mode may repair only before any real outcome has been read" window, which this epoch's
zero-candidate result keeps open through this entire iteration. The session's own
`state/assumptions.md` iter-6 entry has already made and disclosed this interpretive call — this
plan does not re-litigate it, only implements against it. If the developer's independent reading of
§7.3 disagrees, the phase spec itself requires halting and reporting rather than silently narrowing
scope — carry that instruction forward verbatim, do not resolve it here.

**This iteration is irreversible once step 8 begins.** Per the spec's NOTES: commit this
iteration's code, regenerate+commit `freeze-set.json`/`freeze-record.json`, and run the exhaust
CLI's first invocation as ONE atomic sequence inside this iteration — do not defer the exhaust CLI
invocation to a later iteration after the freeze artifacts are committed.

## What to Build

**Backend — freeze-bookkeeping repair (must land BEFORE the exhaust CLI's first real invocation)**

- `apps/backend/app/research/foundry_freeze.py`:
  - `generate_freeze_set`: emit **repo-relative** path keys (closes B1) instead of `str(research_dir / name)` absolute paths. `verify_freeze_set_unchanged` must resolve relative keys against the repo root; absolute keys (used by the hermetic temp-dir fixtures in `test_foundry_freeze.py`) must still pass through unchanged — do not break those fixtures.
  - `generate_freeze_set`'s `required_names`/`extra_paths` inputs (via the real generation CLI's call site) must grow to cover the three tracked Foundry JSONs (`docs/hypothesis-foundry/source-registry.json`, `epoch-manifest.json`, `freeze-record.json` — **not** `freeze-set.json` itself, which cannot self-reference its own not-yet-computed hash) plus the generation CLI (`apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`) — closes B7's freeze-set half.
  - `FreezeRecord` / `build_freeze_record`: add the missing **"era-open evidence-class contract"** field named in §8.4 (closes B7's freeze-record half). Ground its value in the already-established `historical_exposed_diagnostic` evidence class this era is constitutionally locked to (§10.1/goal.md Success Criteria 16).
- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`:
  - Fix `_load_existing_manifest_store` (currently ~lines 858-875) so a **missing** manifest-store file raises a typed refusal instead of silently returning `{}` — TC-7. This file is confirmed not in the freeze-set, so the fix carries no freeze-drift consequence.
  - Add (or extend) the freeze-set/freeze-record **regeneration** entrypoint: repo-relative paths, expanded `required_names`/`extra_paths`, `freeze_commit` = the commit hash **after** this iteration's code changes are committed (never a working-tree/pre-code-commit hash — that is exactly B2). `epoch_id`, `source-registry.json`, `epoch-manifest.json` content must be byte-identical before/after — verify this explicitly (e.g. hash comparison) as part of the regeneration script's own output, not just by inspection.
- `apps/backend/app/research/foundry_ledger.py`: new additive row-kind method (e.g. `record_epoch_open`, alongside `record_intent`/`record_terminal`, same `HashChainedLedger` primitive — no new ledger). Pins all freeze hashes (from `freeze-record.json`) plus the resolved eligible diagnostic-corpus `(dataset_id, checksum)` manifest hash. Idempotent on replay: a second call with matching content verifies and returns the existing row (mirror `record_terminal`'s `ConflictingReplayRefused`-on-mismatch pattern — do not silently append a duplicate row on mismatch either; refuse).
- New script `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` — the resumable, single-flight real exhaust CLI/manager:
  1. Verify freeze integrity (`foundry_freeze.verify_freeze_set_unchanged` + `verify_commit_is_ancestor` against the regenerated freeze-record).
  2. Acquire `foundry_runner.SingleFlightLock` (concurrent second invocation → `ConcurrentRunnerRefused`, no ledger row).
  3. Compute the resolved eligible-corpus `(dataset_id, checksum)` manifest hash via the sanctioned `micro_accessor` door only (no ad hoc filesystem scan).
  4. Append the one epoch-opening row via the new `foundry_ledger` method (idempotent — second invocation verifies and no-ops).
  5. Iterate the frozen manifest's `FROZEN_READY` variants (zero, for this epoch) in canonical family/variant order via the existing `foundry_runner.run_family`/`run_one_candidate` — this is the real end-to-end compiler→interpreter→runner→ledger call, grep-verifiable exactly like the now-obsolete `test_tc9_no_real_exhaust_runner_entrypoint_exists...` test used to verify absence (see Test note below).
  6. Report/serve checkpoint ordinal and a zero protected/withheld/sealed read census.
- `apps/backend/app/research/micro_routes.py`: extend `get_foundry()` with the new `exhaust_progress` top-level key (reusing `foundry_runner.py`/`foundry_ledger.py`; no new module, no second endpoint). **This key reflects genuinely runtime-scoped state** (the Foundry trial ledger written by the exhaust CLI under `get_foundry_dir()`/`TAPEOLOGY_FOUNDRY_DIR`-scoped storage) — unlike `epoch_manifest`, which reads a Git-tracked literal path. Read it the same way the era-open baseline block already does (via `get_foundry_dir()`), honestly degrading to the pre-first-read-lock zero/null state when no ledger exists yet.

**Backend — tests**

- Extend `apps/backend/tests/test_foundry_real_epoch_artifacts.py` with read-only guards over the regenerated `freeze-set.json`/`freeze-record.json`: relative paths, `freeze_commit` ancestry + literal byte-completeness (every pinned path's hash actually matches a commit that contains it — the direct fix for B2), the three new tracked-JSON + generation-CLI entries, the new era-open-evidence-class-contract field.
- **Critical, load-bearing:** `test_tc9_no_real_exhaust_runner_entrypoint_exists_to_read_a_candidate_outcome` (same file, ~line 221) currently asserts **no** call site for `run_family`/`run_one_candidate` exists outside `foundry_runner.py`/`foundry_hermetic_summary.py`. This iteration's entire purpose is to add exactly one legitimate such call site (`run_hypothesis_foundry_real_exhaust.py`). Do not delete this test or silently loosen its allowlist — **evolve** it into a positive guard: exactly one new allowed call site, and that call site is reached only after `verify_freeze_set_unchanged`/`SingleFlightLock` have run (grep/AST-order check), matching the iter-3 lesson that an end-to-end claim must be grep-verified to cross the real module boundary, not asserted in prose.
- `test_foundry_ledger.py`: new tests for the epoch-opening row-kind — round-trips, idempotent replay (verify-and-no-op), mismatch-refuses.
- `test_foundry_runner.py` / a new real-epoch integration test: prove the exhaust CLI's compiler→interpreter→runner→ledger path is real (not a fixture stand-in) over the real committed manifest; prove the manifest-store deletion fix (TC-7) actually raises instead of bypassing; prove resume/single-flight/protected-read-zero on a fixture-backed interrupt (J-07 step 7's own explicit fixture allowance — do not attempt to simulate an interrupt against the real epoch, which has zero variants to interrupt mid-evaluation anyway).

**Frontend**

- `/desk` → Hypothesis Foundry → new **"Runner / Checkpoint"** subsection (home already registered in `state/blueprint.md`'s Information Architecture table — no re-approval needed), new `foundry-runner-*` testid family, following the exact `CollapsibleSection` + subsection-component pattern already used by `EpochManifestSubsection`/`HermeticOraclesSubsection`. Render `exhaust_progress` verbatim, no client computation: first-read-lock recorded/timestamp, resolved eligible-corpus manifest hash, `frozen_ready_total`/`terminal_count`, checkpoint ordinal ("0 of 0"), `protected_read_count`, `single_flight_status`, `freeze_integrity_verdict`, honest zero-candidate `exhaust_complete` completion message.
- `apps/frontend/lib/types.ts`: new `FoundryExhaustProgress` type (fields exactly per Data-contract below); `DeskFoundryResponse` grows `exhaust_progress`.
- Provision the scoped `:8301` QA rig with the real `exhaust_progress` state: after running the real exhaust CLI once during dev, `cp`-guard the resulting ledger/checkpoint files into wherever the `:8301` backend's own `TAPEOLOGY_FOUNDRY_DIR`/dataset-dir-scoped storage resolves to (same pattern already used for the era-open baseline and confirmed working for `epoch_manifest`'s J-06 predecessor problem) — never fabricate a fixture value for this subsection. This is the exact "iter-1/iter-2 lesson" the spec calls out by name.

## Agents Required

- developer: yes — implements the backend freeze-bookkeeping repair, the new ledger row-kind, the real exhaust CLI, the `exhaust_progress` route extension, the extended test suite, and the frontend Runner/Checkpoint subsection (single developer agent, standard convention).
- backend-data: yes — `foundry_ledger.py`, `foundry_freeze.py`, the real exhaust CLI, `_load_existing_manifest_store` fix, freeze-set/freeze-record regeneration + commit sequencing, `micro_routes.py` `exhaust_progress`.
- frontend-ux: yes — new Runner/Checkpoint subsection, `types.ts` extension, scoped `:8301` QA-rig provisioning for the new runtime-scoped state.

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/foundry_ledger.py` -- new additive epoch-opening/first-read-lock row-kind method (idempotent on replay).
- `apps/backend/app/research/foundry_freeze.py` -- repo-relative `generate_freeze_set` keys; `verify_freeze_set_unchanged` repo-root resolution (absolute keys still pass through for hermetic fixtures); `FreezeRecord`/`build_freeze_record` gain the era-open evidence-class-contract field.
- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` -- `_load_existing_manifest_store` typed refusal (TC-7); freeze-set/freeze-record regeneration call site with expanded coverage and post-code-commit `freeze_commit`.
- `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` -- NEW: the real exhaust CLI/manager.
- `docs/hypothesis-foundry/freeze-set.json` -- regenerated (relative paths, expanded coverage), committed.
- `docs/hypothesis-foundry/freeze-record.json` -- regenerated (new `freeze_commit`, new evidence-class-contract field), committed.
- `docs/hypothesis-foundry/source-registry.json`, `docs/hypothesis-foundry/epoch-manifest.json` -- byte-identical, untouched content; verify explicitly, do not just assume.
- `apps/backend/app/research/micro_routes.py` -- `get_foundry()` grows `exhaust_progress`.
- `apps/backend/tests/test_foundry_real_epoch_artifacts.py` -- new freeze-set/freeze-record regeneration guards; the exhaust-runner-entrypoint test evolved from absence-guard to positive end-to-end guard (see above — do not delete/weaken).
- `apps/backend/tests/test_foundry_ledger.py` -- new epoch-opening row-kind tests.
- `apps/backend/tests/test_foundry_runner.py` (and/or a new real-epoch integration test file) -- real exhaust CLI end-to-end path, manifest-store-deletion refusal, resume/single-flight/protected-read-zero fixture proofs.
- `apps/frontend/lib/types.ts` -- `FoundryExhaustProgress`; `DeskFoundryResponse` grows `exhaust_progress`.
- `apps/frontend/app/desk/page.tsx` -- new `RunnerCheckpointSubsection` + `CollapsibleSection` entry, `foundry-runner-*` testids.
- `docs/handoffs/goal-hypothesis-foundry-iter-6-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: an operator can see, on `/desk`, that the real frozen epoch's exhaust pass has run to honest, vacuous completion (zero candidates ever existed to evaluate) and that zero protected/withheld/sealed data was ever touched doing it.
- New information displayed: first-read-lock recorded/timestamp, resolved eligible-corpus manifest hash, total/terminal `FROZEN_READY` counts, checkpoint ordinal, protected-read census, single-flight/integrity status, exhaust-complete flag.
- New user actions: none — the Foundry surface stays read-only; the exhaust CLI is an operator/CLI act outside the app (§9's "resumable manager/CLI operator act"), never a page-load-triggered computation.
- UI surface changes: one new subsection ("Runner / Checkpoint") appended to the existing `/desk` → Hypothesis Foundry panel, after the Epoch/Manifest subsection.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `CollapsibleSection` pattern and the `RealEpochBanner`/`HermeticFixtureBanner` visual-distinction convention already established for Epoch/Manifest — this subsection reflects real runtime state, not a fixture, so it should read consistently with the "real, not fixture" treatment.
- Layout: nested inside `HypothesisFoundrySection`, appended after Epoch/Manifest, matching the sibling subsections' spacing/heading conventions.
- Key visual effects: none new — laboratory-instrument/audit-first tone per goal.md's Design Direction; no status color implying urgency/confidence beyond evidence class.
- States to handle: pre-first-read-lock (should not occur post-invocation, but must render honestly if `exhaust_progress` reflects an unrun state), the honest zero-candidate `exhaust_complete` completion state, and the (never-expected-here) `single_flight_status: "refused_concurrent"` state as an explicit render path even if not exercised by the real epoch.

## Key Test Scenarios

- TC-1: first exhaust CLI invocation appends exactly one epoch-opening row with all pinned freeze hashes + eligible-corpus manifest hash; `exhaust_progress.first_read_lock_recorded == true`.
- TC-2: second invocation appends no second epoch-opening row (ledger count stays 1); exits verifying existing state.
- TC-3: `exhaust_progress.frozen_ready_total == 0`, `.terminal_count == 0`, `.exhaust_complete == true` (the real manifest has zero `FROZEN_READY` variants).
- TC-4: `micro_accessor` call-counter instrumentation proves `exhaust_progress.protected_read_count == 0` and no sealed/withheld dataset id appears in any ledger row or log line.
- TC-5: fixture-backed epoch with one intent-without-terminal ("crashed") row resumes, re-executes the exact screen under identical pins, appends exactly one terminal row (no duplicate).
- TC-6: concurrent second invocation while the single-flight lock is held raises `ConcurrentRunnerRefused`, appends no ledger row.
- TC-7: deleted manifest-store state file → generation command raises a typed refusal (not a silently-minted new `epoch_id`).
- TC-8: `verify_freeze_set_unchanged` + `verify_commit_is_ancestor` both pass against the new `freeze_commit`; every freeze-set path is relative; entry count includes the three tracked Foundry JSONs + generation CLI (closes B1/B2/B7).
- TC-9: browser check — `/desk` → Hypothesis Foundry → Runner / Checkpoint shows the first-read-lock timestamp, checkpoint ordinal "0 of 0", the honest zero-candidate completion message, and protected-read count "0" — all read verbatim from `exhaust_progress`, no client-side computation.
- TC-10: full backend suite + TypeScript compile + existing Rapid Microscope leakage/unit/no-lookahead regression traps all pass, zero previously-passing test skipped/xfailed/deleted.
- TC-11: J-01..J-06 golden replay scripts all still pass (full regression — required by the prior ESCALATE verdict widening the replay set).
- Error cases: concurrent exhaust-CLI invocation; deleted manifest-store file; a freeze-set path with post-lock byte drift (`FreezeIntegrityHalt`); a corrupted ledger chain.

## Out of Scope (explicitly excluded, matching the phase spec)

- Ratifying/rejecting the discarded first real epoch (`ded18b8b…`→`ed40dbc2…`) — remains an unresolved OWNER decision, not this iteration's concern.
- Any change to `epoch_id`, `docs/hypothesis-foundry/source-registry.json`, or `docs/hypothesis-foundry/epoch-manifest.json` content — byte-identical before/after; only freeze-set/freeze-record bookkeeping is regenerated.
- J-08's full "final Foundry truth" surface (detail drill-ins, survivor labelling, T-9/T-10/T-11 regression guards, optional MCP proxy) — natural next iteration, not this one.
- Any new candidate, threshold, family, or scientific choice — the epoch stays frozen at zero compiled candidates.
- Raising `--max-iter` (60→80) — an operator decision, not a spec item.
- The optional `desk_micro_foundry` MCP proxy (goal-deferrable).
