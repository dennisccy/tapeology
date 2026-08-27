# goal-hypothesis-foundry-iter-6 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

- **`app/research/foundry_ledger.py`**: new `record_epoch_open`/`epoch_open_row` API (row kind
  `epoch_open`) on the existing `FoundryLedger` hash chain — the §8.5 first-read-lock row. Pins
  every freeze hash plus the resolved eligible-corpus manifest hash. Idempotent on replay
  (verify-and-return-existing on an exact-content match); raises `ConflictingReplayRefused` on a
  mismatched replay, mirroring `record_terminal`'s own discipline.
- **`app/research/foundry_freeze.py`**:
  - `generate_freeze_set(..., repo_root=...)` now keys entries **repo-relative** (POSIX path) when
    a `repo_root` is supplied and the scanned file lives under it; omitted (every existing
    hermetic-fixture call site), behavior is byte-identical to before — closes audit finding B1.
  - `verify_freeze_set_unchanged(..., repo_root=...)` resolves a relative key against `repo_root`
    before hashing; an absolute key is used exactly as recorded regardless.
  - `FreezeRecord`/`build_freeze_record` gain the required `era_open_evidence_class_contract`
    field (§8.4) — closes audit finding B7's freeze-record half.
- **`scripts/generate_hypothesis_foundry_real_epoch.py`**:
  - `_load_existing_manifest_store` now raises a typed `ManifestStoreMissingError` when
    `epoch-manifest.json` is missing but its sibling `freeze-record.json` proves a prior generation
    already happened (rather than silently returning an empty store, which would let a re-run
    silently accept drifted inputs as if this were the first-ever generation) — closes TC-7.
  - `source-registry.json`/`epoch-manifest.json` are now written **before** the freeze-set is
    computed (previously after), so both are on disk when `generate_freeze_set` scans/hashes them.
  - New `--advance-freeze-commit` flag: recomputes `freeze_commit` from the current `git rev-parse
    HEAD` instead of reusing the pinned value. Default OFF (an ordinary replay/verify run keeps
    `freeze_commit` pinned once, unchanged behavior); this iteration's own regeneration passed it
    explicitly, as a disclosed operator act, strictly inside spec §7.3's repair window.
  - `generate_freeze_set` is now called with `repo_root=REPO_ROOT` and an expanded
    `FREEZE_SET_EXTRA_PATHS` (the spec, `source-registry.json`, `epoch-manifest.json`, the
    generation CLI itself, and the new real exhaust CLI) — closes B7's freeze-set half.
- **`scripts/run_hypothesis_foundry_real_exhaust.py`** (new): the resumable, single-flight real
  exhaust CLI (spec §9, Binding Execution Order step 8). `run_real_exhaust(...)`:
  1. Verifies freeze integrity (`foundry_freeze.verify_freeze_set_unchanged` +
     `verify_commit_is_ancestor`) before anything else runs.
  2. Acquires `foundry_runner.SingleFlightLock` — a concurrent second invocation raises
     `ConcurrentRunnerRefused`, appends no ledger row.
  3. Computes the resolved eligible diagnostic-corpus `(dataset_id, checksum)` manifest hash
     through the sanctioned data door (`datasets.DatasetStore.list()` +
     `micro_snapshots.exclude_withheld`, the SAME choke point `pnl_scan._verified_corpus` already
     shares) and `micro_corpus.corpus_manifest_hash` (the existing scientific-identity hash
     formula — no second one invented).
  4. Appends the one epoch-opening row (`foundry_ledger.record_epoch_open`), idempotent on replay.
  5. Iterates every `FROZEN_READY` variant in canonical family/variant order via
     `foundry_runner.run_family`/`run_one_candidate` — the real committed manifest carries
     `families: []` (zero compiled candidates), so this reaches an honest, vacuous completion. A
     family entry that DID carry a variant would raise `RealCandidateEvaluationUnsupported` rather
     than being silently mis-evaluated — see that exception's own docstring for why real per-family
     CandidateSpec/anchor reconstruction from the exposed corpus is deliberately unbuilt this era
     (never reachable against the one real, already-frozen, zero-candidate epoch).
  6. Returns/prints the checkpoint (`frozen_ready_total`, `terminal_count`, `checkpoint_ordinal`,
     `protected_read_count`, `exhaust_complete`).
- **`app/research/micro_routes.py`**: `GET /research/desk/micro/foundry` grows the additive
  `exhaust_progress` key, read **per request** (via `foundry_runner.read_exhaust_progress`, unlike
  `epoch_manifest` which is a module-import-time, Git-tracked-path read) — reflects the genuinely
  runtime-scoped Foundry trial ledger.
- **Frontend**: `/desk` → Hypothesis Foundry → new "Runner / Checkpoint" `CollapsibleSection`
  (`foundry-runner-*` testid family) appended after Epoch/Manifest, rendering `exhaust_progress`
  verbatim (first-read-lock timestamp, eligible-corpus hash, checkpoint ordinal, protected-read
  count, single-flight/integrity status, the honest zero-candidate completion message).
- **Ran the real exhaust CLI** against the real committed epoch (see "Real epoch state" below) —
  the era's second and final irreversible act before finalization.

## Files Changed

- `apps/backend/app/research/foundry_ledger.py` -- `record_epoch_open`/`epoch_open_row` (row kind
  `epoch_open`).
- `apps/backend/app/research/foundry_freeze.py` -- repo-relative freeze-set keys;
  `era_open_evidence_class_contract` field.
- `apps/backend/app/research/foundry_runner.py` -- `read_exhaust_progress`, `EXHAUST_LOCK_FILENAME`.
- `apps/backend/app/research/micro_routes.py` -- `exhaust_progress` key on `get_foundry()`.
- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` -- TC-7 typed refusal, write
  ordering, `--advance-freeze-commit`, expanded freeze-set coverage.
- `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` -- new: the real exhaust CLI.
- `apps/backend/tests/test_foundry_freeze.py` -- new `era_open_evidence_class_contract` kwarg;
  repo-relative-keys tests.
- `apps/backend/tests/test_foundry_ledger.py` -- `record_epoch_open` round-trip/idempotent/conflict
  tests.
- `apps/backend/tests/test_foundry_real_epoch_artifacts.py` -- freeze-set/freeze-record B1/B2/B7
  guards; evolved TC-9 into a positive, freeze-gated call-site guard.
- `apps/backend/tests/test_foundry_route.py` -- `exhaust_progress` route tests (honest pre-lock
  degrade, real-row reflection, live single-flight probe).
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` -- new: real-freeze +
  fixture-freeze integration tests for the exhaust CLI.
- `apps/frontend/lib/types.ts` -- `FoundryExhaustProgress`; `DeskFoundryResponse.exhaust_progress`.
- `apps/frontend/app/desk/page.tsx` -- `RunnerCheckpointSubsection`, wired into
  `HypothesisFoundrySection`.
- `docs/hypothesis-foundry/freeze-set.json`, `docs/hypothesis-foundry/freeze-record.json` --
  regenerated (relative paths, expanded coverage, new field, advanced `freeze_commit`). `epoch_id`,
  `source-registry.json`, `epoch-manifest.json` content verified byte-identical (`git diff` empty).

## Real epoch state (irreversible acts this iteration performed)

Four commits on `goal/hypothesis-foundry`, in order:

1. `1573f457` — this iteration's code (backend + tests + frontend).
2. `4f78d1dc` — first freeze-set/freeze-record regeneration (used a stale `freeze_commit` — see
   next commit).
3. `5b41d9ef` — added the `--advance-freeze-commit` flag itself (a necessary follow-up fix: the
   first regeneration ran against the script as it existed BEFORE this flag, so `freeze_commit`
   did not yet contain the flag-adding commit's own bytes — the same B2 trap one level removed,
   caught by this iteration's own new `test_b2_every_freeze_set_path_hash_matches_the_freeze_
   commits_own_committed_bytes` test before the exhaust CLI ever ran).
4. `873b4ed7` — final freeze-record regeneration: `freeze_commit` now equals HEAD exactly, verified
   via `git show freeze_commit:<path>` byte-matching every freeze-set entry.

The real exhaust CLI was then run against commit `873b4ed7`'s tree, appending exactly ONE
epoch-opening row to the runtime Foundry trial ledger (`apps/backend/.data/foundry/
foundry_trial_ledger.jsonl`, gitignored — this is the untracked runtime ledger, never the Git
precommit artifact):

- `epoch_id`: `epoch:afd19e9c11a6534f`
- `first_read_lock_at`: `2026-08-27T06:55:51.071173Z`
- `eligible_corpus_manifest_hash`: `da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260`
  (18 eligible members, 80 withheld — this repository's real corpus carries prior-era Vault-sealed
  shards; `exclude_withheld` genuinely excluded them, not a no-op)
- `frozen_ready_total`: 0, `terminal_count`: 0, `checkpoint_ordinal`: 0
- `protected_read_count`: 0
- `exhaust_complete`: `true` — the real committed manifest's `families: []` (zero compiled
  candidates, established in iter-5) means the exhaust pass reaches an honest, vacuous completion.

Re-running the exhaust CLI a second time verifies and appends nothing further (proven by an
isolated integration test against a small fixture corpus, not re-run against the real 26GB corpus a
second time to avoid an unnecessary ~13-minute re-scan — see Known Issues).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 3916 passed, 8 skipped, 0 failed, 0 errors (exit code 0). This environment's pytest does
not print the standard final summary line (pre-existing, unrelated to this iteration — confirmed
the same behavior on an unmodified `git stash` baseline run at the start of this session); pass/
skip counts above were derived from the dot/`s` status-line characters plus the `0` exit code.

Command: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit`
Result: clean, zero errors.

Browser check (Chrome CDP, :3301 → :8301): navigated to `/desk`, expanded "Hypothesis Foundry" →
"Runner / Checkpoint", confirmed the rendered text matches `exhaust_progress` verbatim (first-read
lock timestamp, eligible-corpus hash, "Checkpoint: 0 of 0", "Protected/withheld/sealed reads: 0",
"Freeze integrity: green", the honest zero-candidate completion sentence) — extracted via DOM text
(`element.innerText`), not a screenshot: the headless Chrome instance produced a blank PNG for this
deep-scrolled element on every attempt (a previously-documented limitation of this environment, not
a rendering defect — the DOM text extraction is the authoritative evidence and matches the served
JSON exactly).

Both dev servers were left running for the QA lanes that follow this handoff: backend on `:8301`,
frontend on `:3301` (per this dispatch's own operational note).

## Known Issues

- **J-01..J-06 golden replay was not re-run by this developer dispatch.** The route/page changes
  this iteration made are purely additive (`exhaust_progress` is a new top-level key; the new
  subsection is appended after the existing Epoch/Manifest one) and the full backend suite
  (including every existing Foundry/Referee/leakage/no-lookahead regression test) is green, so a
  regression is unlikely — but the deterministic replay-script pass itself is QA's explicit task in
  this pipeline's next step, not duplicated here.
- **The real exhaust CLI was not re-invoked a second time against the real, 26GB dataset corpus**
  to prove TC-2 (idempotent replay) against real data specifically — `DatasetStore.list()` over the
  real corpus takes roughly 13 minutes (matches this project's own carried performance note: large
  per-file checksum verification over a many-GB corpus). TC-2 is proven instead by an isolated
  integration test (`test_tc2_second_invocation_verifies_and_appends_no_second_epoch_open_row`)
  against the small, fast `tests/fixtures/datasets` corpus, and independently by
  `foundry_ledger.py`'s own unit-level idempotent-replay tests. A manual second real-corpus
  invocation remains a cheap, safe, ~13-minute operator act any time it is wanted (idempotent by
  construction — it will not mint a second epoch-opening row).
- **`RealCandidateEvaluationUnsupported`** in the real exhaust CLI is a deliberate, disclosed
  scope boundary, not a gap discovered late: real per-family CandidateSpec/anchor reconstruction
  from the exposed diagnostic corpus was never built, because the one real epoch this era will ever
  generate is frozen with zero compiled candidates (established in iter-5) — building that
  extraction machinery now would be new candidate-construction work for a state this era's own one
  epoch structurally cannot reach.
- **The freeze-set deliberately does NOT include `freeze-record.json` itself**, even though this
  iteration's own phase spec's BACKGROUND text names it as one of "the three tracked Foundry
  JSONs" the freeze-set should cover. This is a disclosed, reasoned deviation: `freeze-record.json`'s
  own content embeds `freeze_set_hash`, so pinning its file hash inside the very freeze-set that
  hash is computed over is the identical self-reference `freeze-set.json` is already, explicitly,
  excluded for (one hop removed) — genuinely circular, not merely inconvenient. `docs/goal.md` §8.4
  itself only names "the Foundry methodology/spec and tracked REGISTRY/MANIFEST files"
  (`source-registry.json`/`epoch-manifest.json`) as freeze-set members, never `freeze-record.json`/
  `freeze-set.json` — this implementation follows that authoritative text. `freeze-record.json`'s
  own integrity is instead protected by the existing `verify_commit_is_ancestor` + `freeze_set_hash`
  field-equality check every reader (the route, the exhaust CLI) already performs.
- Two commits in this iteration's own history (`4f78d1dc` then `5b41d9ef`/`873b4ed7`) show a
  freeze-commit-ordering mistake caught and corrected DURING this same dispatch (before the exhaust
  CLI ever ran) — left visible in git history rather than squashed, since `docs/goal.md` explicitly
  forbids amending commits mid-repair and the correction is itself evidence the B2 integrity check
  works.

---

## Fix Notes (review FAIL pass — 2026-08-27)

Fixed only the issues listed in `reports/reviews/goal-hypothesis-foundry-iter-6-review.md`. No
other production code was touched: `git status` shows exactly three source files changed in this
pass (one shell script, two test files). Nothing in the freeze-set was modified, so freeze integrity
is unaffected (verified: the real-freeze exhaust tests, which run the production
`verify_freeze_set_unchanged` + `verify_commit_is_ancestor` against the committed artifacts, still
pass).

### CRITICAL — scoped `:8301` QA rig was never provisioned with the real exhaust state

`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — added a `cp` block mirroring
the existing `era_open_baseline.json` one (immediately below it, same honest-absence guard) that
copies the real, recorded Foundry trial ledger into the rig's own scoped `$ROOT/foundry/`:

- `apps/backend/.data/foundry/foundry_trial_ledger.jsonl`
- `apps/backend/.data/foundry/foundry_trial_ledger.jsonl.chain_head.json` (the hash-chain tail
  anchor — copied together with the ledger and only together, so the rig can never receive a
  mismatched chain)

Deliberately NOT copied: `foundry_exhaust_runner.lock`. That file is live OS-advisory-lock state
belonging to whichever machine last ran the CLI, not recorded evidence; `read_exhaust_progress`'s
own live probe re-creates it in the scoped directory. Honest-absence fallback preserved: if the
operator has never run `run_hypothesis_foundry_real_exhaust.py`, nothing is copied and the rig
correctly falls back to the honest pre-lock `first_read_lock_recorded: false` state — never a
fabricated value.

**Verified end-to-end through the mandated rig, not by inspection.** Launched
`qa_playbook_iter7_fixture_scoped_backend.sh` on `:8301` (fresh root, seeded from scratch) plus the
frontend on `:3301` pointed at it, then:

- `GET :8301/research/desk/micro/foundry` → `exhaust_progress` served the REAL recorded state:
  `first_read_lock_recorded: true`, `first_read_lock_at: 2026-08-27T06:55:51.071173Z`,
  `eligible_corpus_manifest_hash: da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260`,
  `frozen_ready_total: 0`, `terminal_count: 0`, `checkpoint_ordinal: 0`, `protected_read_count: 0`,
  `single_flight_status: "idle"`, `freeze_integrity_verdict: "green"`, `exhaust_complete: true`.
- The copied chain verifies on the rig: `FoundryLedger(<rig>/foundry).verify_chain()` →
  `{"ok": true, "failed_at_row": null, "reason": null}`, 1 row, kind `epoch_open`.
- Browser (`:3301/desk` → Hypothesis Foundry → Runner / Checkpoint) rendered the real state, with a
  screenshot as evidence — this is the "browser-verified against the real state" DEFINITION OF DONE
  item the review correctly found unproven:
  `reports/qa/goal-hypothesis-foundry-iter-6-runner-checkpoint-scoped-rig.png` (full page) and
  `...-crop.png` (the subsection). Screenshot note: a viewport capture taken while deep-scrolled
  comes back blank on this rig (a known, previously-recorded compositing artifact of this setup) —
  the working method is to enlarge the viewport so the subsection sits within an unscrolled page,
  which is what produced the evidence above.

Regression check on the shared rig: no existing golden replay script asserts anything about the
exhaust/runner subsection (grepped `runs/goal-session-*/journey-scripts/` for `exhaust`,
`foundry-runner`, `Runner / Checkpoint` — zero hits), so this provisioning adds state that was
previously absent and cannot flip an existing J-01..J-06 assertion.

### MINOR — TC-7 had zero automated coverage

`apps/backend/tests/test_foundry_real_epoch_artifacts.py` — three new tests (the loader is
exercised through the real shipped script, loaded with the same `importlib` convention the file
already uses for TC-1):

- `test_tc7_deleted_manifest_store_refuses_instead_of_silently_minting_a_new_epoch` — missing
  `epoch-manifest.json` with a standing sibling `freeze-record.json` raises
  `ManifestStoreMissingError`. Fully hermetic (both paths in `tmp_path` via `monkeypatch`); the real
  tracked artifacts are never read, written, or deleted.
- `test_tc7_first_ever_generation_still_gets_a_genuinely_fresh_store` — the refusal is not a blanket
  one: with neither file present (a true fresh install), the loader still returns `{}`, so the very
  first real generation remains possible.
- `test_tc7_the_real_committed_manifest_reconstructs_a_populated_replay_store` — positive control
  over the real committed artifact (read-only): every reconstructed `ManifestRecord` field equals
  the committed one, so the guarded path demonstrably works when the file is present.

### MINOR — TC-4's literal call-counter instrumentation

`apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` — added
`test_tc4_instrumented_micro_accessor_counter_records_zero_protected_reads`. It wraps
`micro_accessor.MicroAccessor.read_snapshot_rows` (the one door to protected snapshot rows) in a
real call counter — patched on the class, so any future call from anywhere in the path is counted —
and asserts zero calls across BOTH flavors of run: the real committed manifest's vacuous
zero-variant pass, and the fixture-backed one-variant pass (the only one that actually crosses
`run_family`/`run_one_candidate` into the interpreter, i.e. the path where such a read could
plausibly appear later). The one-variant run's `terminal_count == 1` is asserted too, so "zero
reads" is not a vacuous claim. This is defense-in-depth beside — not a replacement for — the
existing structural grep-based entrypoint-allowlist guard; `protected_read_count` stays a
structural `0` in production, unchanged.

The reviewer marked this one "Optional" and left it out of `fix_tasks`. It was included anyway
because it is test-only, runs against `tmp_path`, and closes the last named gap; no production code
changed for it.

### Tests re-run

Command: `apps/backend/.venv/bin/python -m pytest` (from `apps/backend`)
Result: **3920 passed, 8 skipped** (exit 0) — up from 3916 passed by exactly the 4 tests added
here; zero previously-passing tests skipped, xfailed, or deleted.

Command: `npx tsc --noEmit` (from `apps/frontend`) — exit 0. No frontend source changed in this fix
pass.

### Still open after this pass

- J-01..J-06 golden replay is still QA's step, not re-run here (unchanged from the original
  handoff). The rig they must use is now correctly provisioned.
- The backend is left running on `:8301` (the scoped QA rig, seeded root under this run's
  `TMPDIR`) and the frontend on `:3301`, for the QA lanes that follow. The store roots this
  launch bound to are recorded in `reports/qa-scoped-backend-store-manifest.md`.
