# Maintenance task 2026-08-24 — verification

**Scope:** the owner-ruled maintenance task issued after the iteration-28 `STALLED` halt. Two
classes of work, kept in two commits:

1. **A** — the two remaining project test-hygiene jobs (`test_micro_snapshots.py` durable index;
   test caches off the operator's live DB files).
2. **B** — the one approved framework fix: the confirmed `closure_gate.py` `backend-only`
   false positive.

Everything below was measured on this machine, in this order, and every number is a run I made
rather than a figure carried forward from an earlier report.

---

## A1 + A2 — timings

`cd apps/backend && .venv/bin/python -m pytest <file> -q`, wall clock via `/usr/bin/time`.

| File | Before | After (warm) | Change |
|---|---:|---:|---|
| `test_micro_readiness.py` | 2.80s | **2.83s** | unchanged (iter-28 speed retained) |
| `test_micro_join.py` | 7.00s | **6.94s** | unchanged (iter-28 speed retained) |
| `test_micro_snapshots.py` | **27:31.86** (1651.9s) | **2.55s** | **~648× faster** |
| Full backend suite | 33:43 (2023.75s, iter-28 audit) | **6:34** (394.69s) | **~5.1× faster** |

"Before" for the first two is the iteration-28 state with its live caches fully warm, measured by
temporarily stashing this task's changes — i.e. the most favourable honest baseline, not the
pre-iter-28 14m38s/27m57s figures. `test_micro_snapshots.py`'s before is a full run made at the
start of this task (`--durations=10`): 808.36s fixture setup + 807.92s in the route-listing call +
33.39s identity re-verify.

### Cold behaviour, stated honestly

With `.data/test-cache/` deleted, the three files together:

```
COLD_WALL=14:20.93   COLD_EXIT=0
850.58s setup  tests/test_micro_readiness.py::test_tc1_real_corpus_distinct_symbol_days_and_datasets
  5.51s call   tests/test_micro_join.py::test_tc4_real_corpus_join_playbook_signal_...
  0.46s call   tests/test_micro_join.py::test_tc16_real_corpus_joinable_corpus_arithmetic_...
```

One cold warm-up of **14:20.93** total, essentially all of it a single full corpus verify in the
first module fixture; the other two files then ride the index that verify populated, and
`test_micro_snapshots.py` does not appear in the slowest-8 at all. Compare: before this task,
`test_micro_snapshots.py` **alone** cost 27:31.86 on *every* run, warm or cold.

Every subsequent run is the warm column above. After the change, none of the three files appears
in the full suite's slowest-12; the slowest test in the suite is now
`test_referee_oracles.py::test_oracle_case5_bh_sweep_...` at 30.78s.

### What made it fast

Nothing about the research path changed. `run_snapshot_build_and_record` already reused a valid
snapshot — but *deciding* to reuse calls `DatasetStore.list()` once and `load_snapshot_meta()` →
`DatasetStore.get()` per dataset, and an index-less store re-parses and re-checksums the whole
real corpus for each of those calls. Because `conftest.py`'s `_reset_store_verified_caches`
(correctly) clears the in-process stat cache between tests, that full re-verify was paid once per
test. The fix hands the fixture the production durable `DatasetStore(index_db_path=...)` index, so
already-verified metadata is remembered instead of recomputed.

Trust boundary unchanged: an index hit is metadata `DatasetStore._load` itself checksum-verified,
any stat difference is a miss that re-verifies in full, and `load_events`/`replay` — the calls a
snapshot *build* actually makes — bypass the cache on every call with no bypass path.

---

## A2 — cache paths used by tests, and proof they are not the live ones

Single source: `apps/backend/tests/real_corpus_cache.py`.

| | Live (operator backend) | Test-owned |
|---|---|---|
| dataset index | `apps/backend/.data/dataset_index.db` | `apps/backend/.data/test-cache/dataset_index.db` |
| readiness cache | `apps/backend/.data/micro_readiness_cache.db` | `apps/backend/.data/test-cache/micro_readiness_cache.db` |

Same production classes (`DatasetIndex` via `DatasetStore(index_db_path=)`, `MicroReadinessCache`),
same key semantics, no duplicate cache implementation, persistent across pytest invocations,
`.data/` is already gitignored wholesale, and the whole reset procedure is `rm -rf
apps/backend/.data/test-cache` — both DBs are derived projections that own no research truth. No
raw dataset file is written on any of these paths.

The helper deliberately does **not** read `TAPEOLOGY_DATASET_INDEX_DB` or
`TAPEOLOGY_MICRO_READINESS_CACHE_DB`. Honouring those operator env vars is exactly how iter-28's
fixtures landed on the live files.

### Empirical proof the live DBs were not written

Recorded before the first post-change run and re-checked after **two** full suite runs plus the
cold and warm passes:

```
apps/backend/.data/dataset_index.db          size=147456  mtime=2026-08-23 01:35:46.278317621 +0100
apps/backend/.data/micro_readiness_cache.db  size=12288   mtime=2026-08-17 01:14:23.219254775 +0100
```

Identical size and mtime to the nanosecond, before and after. No `-wal`/`-shm` sidecar was created
beside either file (SQLite would have made them on any open).

### The guard — `test_real_corpus_cache_scope.py` (10 tests) + `conftest.py`

The framework store-scope guard protects the append-only stores from automated *browser* lanes and
deliberately leaves the derived accelerator DBs off its protected list, because a read path
legitimately updates those. That reasoning is right for the browser lane and does not transfer to
pytest. This is the pytest half:

1. **Path identity** — test paths ≠ live paths, for both DBs and both dataset-dir resolutions.
2. **Env independence** — with both operator env vars set to the live paths, the test namespace
   does not move. This is iter-28's exact mechanism, pinned so it cannot return.
3. **Static scan** — no real-corpus test file builds a store or cache from the live env-else-sibling
   policy, and all three import the shared helper.
4. **Construction refusal** (`conftest.py::_forbid_live_cache_db_construction`, session-scoped) —
   for the whole session, constructing `DatasetIndex` or `MicroReadinessCache` against a live path
   raises. Opening either class creates the file, its WAL sidecars and its schema, so refusing the
   constructor is strictly stronger than refusing a write — and unlike an mtime watch it cannot
   false-fail because the operator's own backend touched a file mid-session. Scoped to
   `CONFIG.dataset_dir` (the un-overridden package default = the operator's real store), so a
   session scoped onto a fixture rig is unaffected.

**Mutation-tested.** Collapsing `test_cache_dir()` onto `live_cache_dir()` was caught by four
independent tests (both path-identity params, the deletable-directory test, the env-independence
test, and the conftest guard). Reverted; 10/10 green again.

---

## B — closure gate

**The defect.** `_BACKEND_CLAIM_RE` matched the bare substring `backend-only` anywhere in
`user-visible-changes.md`. Iteration 28's document describes its new visible `/desk` caveat at
length under *What Changed in the Visible UI*, then later says a new test "is a backend-only
regression guard". Frontend files had changed, so the gate emitted `CLOSURE-FAIL` for a
contradiction that did not exist.

**The fix — two signals, both required before blocking.**

- `_NO_VISIBLE_CLAIM_RE` — a claim-*shaped* assertion: a no-visible-changes statement, an explicit
  `Frontend Present: no` / `backend-only: yes` declaration, or `backend-only` bound to the **phase**
  ("backend-only phase", "the iteration is backend-only"), never to a noun inside it. The copular
  form must end its clause, because without that "the new guard test added this iteration is a
  backend-only regression guard" reads as a claim one clause later. `user-facing` is deliberately
  excluded — iter-28 uses "zero user-facing surface" about test infrastructure.
- `documents_a_visible_change()` — the rebuttal: does the document affirmatively describe a visible
  change under its own visible-changes heading? An N/A stub, or a section that says "None.",
  rebuts nothing.

A claim with no rebuttal **blocks** (the defect this gate exists for). A claim *with* a rebuttal is
a wording inconsistency, not a missing description, so it is a **named WARN** rather than silence.

`_NA_STUB_MARKER_RE` keeps the original broad marker set for stub detection only, where the
accompanying `lines <= 5` condition is what makes a bare `backend-only` hit meaningful.

**Both layers now share one definition.** `check_backend_only_claim` (`lib/common.sh`) used the
same substring grep. It now delegates to `closure_gate.py claims-no-visible-surface <file>`, with
the original grep minus the `backend-only` alternative as a python3-less fallback. Verified against
the real iter-28 artifacts: the bash twin returns consistent (exit 0).

**Self-tests, both directions** — added to `closure_gate.py self-test`:

| Test | Asserts |
|---|---|
| `claim_regex_shape` | 7 claim-shaped strings match; 5 incidental-prose strings do not |
| `rebuttal_detection` | iter-28 shape rebuts; N/A stub and a "None." section do not |
| `no_visible_claim_still_blocks` | **direction 1** — "No user-visible changes." + changed `page.tsx` → `CLOSURE-FAIL` |
| `backend_only_phase_declaration_still_blocks` | **direction 1** — "This is a backend-only phase" + changed `page.tsx` → `CLOSURE-FAIL` |
| `iter28_incidental_backend_only_passes` | **direction 2** — iter-28's exact shape + changed `page.tsx` → `CLOSURE-PASS`, guard records *consistent* |
| `claim_with_described_change_is_a_named_warn` | both present → `CLOSURE-PASS` with a named WARN |

```
[closure_gate self-test] 15 passed, 0 failed
bash tests/automation/test-closure-gate.sh   ->  29 passed, 0 failed
```

**Proof on the real artifacts.** Re-running the gate against the actual iteration-28 tree gives
`CLOSURE-PASS` with `no-visible-surface claim guard: consistent`. The historical
`phase-goal-rapid-microscope-iter-28-closure-verdict.md` was restored to its original
`CLOSURE-FAIL` afterwards — that file is the record of what the gate said at the time, and
rewriting it would erase the evidence of the false positive.

The other three framework findings were **not** touched; they remain framework-maintenance backlog.

---

## D — verification runs

| Check | Result |
|---|---|
| Full backend suite | **3491 passed, 8 skipped, 0 failed** in 394.69s (`-o addopts=""`), exit 0 |
| Test count reconciliation | 3489 collected before → 3499 after; delta is exactly the 10 new guard tests |
| Three real-corpus files, cold | exit 0, 14:20.93 |
| Three real-corpus files, warm | exit 0, 2.83s / 6.94s / 2.55s |
| Cache-isolation guard | 10 passed; mutation caught by 4 tests |
| `closure_gate.py self-test` | 15 passed, 0 failed |
| `test-closure-gate.sh` | 29 passed, 0 failed |
| Determinism / referee / fingerprint-epoch / dataset-index guards | 96 passed |
| Config fingerprint | `08e471b10130e1e2` — matches the goal.md-pinned value |
| Referee byte-identity | 6/6 sha256 match the iteration-0 frozen listing; `git status apps/backend/app/` empty |
| Live cache DBs | byte-identical size + mtime before/after; no WAL/SHM sidecars |

### `run-evals.sh` — 29 pre-existing unit failures, unrelated to this task

`./scripts/automation/run-evals.sh` exits 1 with 29 of its 44 `tests/automation/*.sh` units
failing. **This is pre-existing and not caused by this task**, established by A/B:

- `test-goal-checkpoints.sh` gives an identical `2 passed, 9 failed` with the framework changes
  stashed and unstashed.
- The five units whose status was ambiguous (because a comparison baseline run was killed early)
  were run individually both ways: `full-depth-required`, `host-guard`, `host-guard-browser`,
  `maintenance-isolation`, `reset-forensics` → byte-identical exit codes (1, 124, 1, 1, 1) with and
  without the changes.

The failures are path-dependent: the same script passes when invoked as
`incredible_auto_dev/tests/automation/<name>.sh` and fails as `tests/automation/<name>.sh` (the
root symlink path the runner uses), with `rc=127` inside. `test-closure-gate.sh` — the unit that
covers this task's framework change — passes **29/0 through the runner's own symlink path**.

This is a genuine framework-harness problem worth its own ticket. It is not one of the four
findings the owner ruled on and was not in this task's scope, so it is recorded here and left
alone.

---

## C — untouched, as ruled

No change to `docs/goal.md`, rapid-validation statistical methodology, recorder/vault evidence
rules, Scout/walk-forward thresholds, Referee modules, Tier-B resolution, sealed evidence, J-06
data, or J-09 pilot results. `git status --porcelain apps/backend/app/` is **empty** — zero
production backend source changed. No new market-data calls were made.

`goal_gate.py` was not weakened; `DEFERRED-BUDGET` remains blocking. J-07 still owes a real fresh
re-check.
