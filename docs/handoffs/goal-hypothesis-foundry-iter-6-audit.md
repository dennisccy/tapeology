# goal-hypothesis-foundry-iter-6 Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration genuinely performed the era's second irreversible act: exactly one §8.5 epoch-opening
row exists in the real Foundry trial ledger, its hash chain verifies, every one of its twelve freeze
fields is byte-equal to the committed `freeze-record.json`, and it was written **after** the
freeze-bookkeeping commits (lock `2026-08-27T06:55:51Z`; commits `1573f457`…`873b4ed7` at
06:40–06:42Z). B1/B2/B7 are genuinely closed — 59 repo-relative freeze-set entries, all present, all
hashing to `freeze_commit` `5b41d9ef`'s own committed bytes, which is a real ancestor of `HEAD` —
and `epoch_id`/`source-registry.json`/`epoch-manifest.json` are byte-identical to iter-5's `dff64eaa`.

Two IMPORTANT findings surfaced that no prior artifact caught. One I fixed (freeze-record.json had
**no** integrity tie to the freeze-set, despite the dev handoff asserting one exists). The other is
permanent and unfixable: goal.md §8.5 requires the epoch-opening row to disclose environment
metadata, and it carries none — a change that could only be made inside the now-frozen
`foundry_ledger.py`, which the era's own Binding Execution Order forbids after the lock. It is inert
for a zero-candidate epoch, so it degrades the verdict rather than defeating the phase.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `freeze-record.json` had no integrity tie to the freeze-set, and the
handoff's justification for that cited a check that does not exist**

`docs/handoffs/goal-hypothesis-foundry-iter-6-dev.md` (Known Issues) justifies excluding
`freeze-record.json` from the freeze-set by asserting its integrity "is instead protected by the
existing `verify_commit_is_ancestor` + `freeze_set_hash` field-equality check every reader (the
route, the exhaust CLI) already performs."

Traced: no such check exists anywhere in the repository.
`foundry_freeze.verify_freeze_set_unchanged` (`apps/backend/app/research/foundry_freeze.py:299-325` (body at :315-325))
only re-hashes the paths `entries` enumerates — it never recomputes `freeze_set_hash` and never looks
at `freeze-record.json`. `run_hypothesis_foundry_real_exhaust.run_real_exhaust`
(`apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:217, 233-249`) reads
`freeze_record["freeze_set_hash"]` and copies it straight into the irreversible ledger row without
comparing it to anything. `micro_routes.read_epoch_manifest_view`
(`apps/backend/app/research/micro_routes.py:873`) surfaces it verbatim. A repo-wide grep for any
equality comparison over `freeze_set_hash` returns only unrelated assignment sites plus one
*self*-consistency assertion inside the freeze-set
(`apps/backend/tests/test_foundry_real_epoch_artifacts.py:473`).

Consequence: a hand-edit of `freeze-record.json` swapping in a different `freeze_set_hash` — the
value copied verbatim into the era's one unrepeatable §8.5 row — would pass every existing check.
The exclusion itself is correct (the circularity argument is genuine and matches goal.md §8.4's own
wording, which names only the registry and manifest as members); what was missing was the
compensating guard.

**Fix applied.** `apps/backend/tests/test_foundry_real_epoch_artifacts.py:145` — new read-only guard
over the committed bytes, `test_freeze_record_freeze_set_hash_matches_the_committed_freeze_set`,
asserting `freeze_record["freeze_set_hash"] == freeze_set["freeze_set_hash"]` and that the freeze-set's
enumerated `entries` recompute to that same digest. Test-only; no production code, no freeze-set
member, and no science value touched. Evidence in §4.

**B2 — IMPORTANT (gap, permanently unfixable): the §8.5 epoch-opening row carries no environment
metadata**

`docs/goal.md` §8.5: *"Runtime library/compiler versions that can affect floating-point behavior but
are outside the repository hash set are disclosed in the **epoch-opening environment metadata**."*

The row written by `foundry_ledger.record_epoch_open`
(`apps/backend/app/research/foundry_ledger.py:153-199`) carries the twelve freeze hashes,
`epoch_id`, `eligible_corpus_manifest_hash` and `recorded_at` — and nothing else. Confirmed against
the real artifact (`apps/backend/.data/foundry/foundry_trial_ledger.jsonl`, one row, read in full).
A grep for `platform.`/`sys.version`/`python_version`/`environment_metadata`/`numpy.__version__`
across every `foundry_*.py` and both Foundry CLIs returns zero hits; `era_open_baseline.json` records
only suite counts, `config_fingerprint`, `tsc_error_count` and the Referee module hashes; the
manifest's `_generation_inputs` carries only `compiler_hash`, `config_fingerprint`, `dispositions`,
`foundry_spec_version`, `source_registry_hash`.

Not fixed, deliberately. The only correct fix site is inside `foundry_ledger.py`, which is
one of the 59 freeze-set entries (`apps/backend/app/research/foundry_ledger.py`) — editing it would break
`verify_freeze_set_unchanged` for every future run and is exactly the "science-affecting code change
after the first-read lock" that goal.md §7.3 and this phase's own anti-goal list call an integrity
halt. The row is also append-only and `record_epoch_open` refuses on any content mismatch, so it
cannot be amended. Impact is bounded to nil for this epoch: zero candidates were evaluated, so no
floating-point-dependent scientific value exists whose reproducibility this metadata would qualify.
It is a permanent hole in the era's audit trail that the next methodology era must close before its
first real evaluation.

**B3 — GAP: a corrupted ledger chain is neither detected nor tested on either the CLI or the read
path**

The phase spec's TESTING REQUIREMENTS name "a corrupted ledger chain" as a required error case.
`HashChainedLedger.all_rows()` (`apps/backend/app/research/micro_chain_ledger.py:132-134`) is an
explicit non-verifying reader — its own docstring says so. Neither
`run_real_exhaust` (`run_hypothesis_foundry_real_exhaust.py:216-262`) nor
`foundry_runner.read_exhaust_progress` (`apps/backend/app/research/foundry_runner.py:229-283`) ever
calls `verify_chain()`. A tampered or forged `epoch_open` row would therefore be served by
`GET /research/desk/micro/foundry` as `first_read_lock_recorded: true` with
`freeze_integrity_verdict: "green"`, and the `/desk` panel would present it as the real first-read
lock. No test in this iteration covers the case.

Not fixed: the correct call site is `read_exhaust_progress`, inside the frozen `foundry_runner.py`
(same bar as B2). Verified separately, by hand, that the real ledger is currently clean:
`FoundryLedger('.data/foundry').verify_chain()` → `{'ok': True, 'failed_at_row': None, 'reason': None}`,
one row, kind `epoch_open`.

**B4 — GAP: `freeze_integrity_verdict` is a historical fact, not a live verdict**

`foundry_runner.read_exhaust_progress` (`apps/backend/app/research/foundry_runner.py:267, 281`)
returns `"green"` whenever an `epoch_open` row exists and `"not_yet_verified"` otherwise. The
docstring discloses the reasoning (the row could only have been appended after the CLI's own
verification passed) and the "a GET must never recompute" constraint is a legitimate anti-goal
driver. The consequence is still real: post-lock byte drift in a freeze-set path would leave the
`/desk` panel reading "Freeze integrity: green" indefinitely, since nothing on the read path
re-verifies. The enforceable primitive fires only on the next CLI invocation.

**B5 — GAP: the Foundry read surface now performs a filesystem write and an exclusive lock
acquisition on every page load**

`read_exhaust_progress` runs a live single-flight probe (`foundry_runner.py:250-254`), and
`SingleFlightLock.acquire` (`foundry_runner.py:197-201`) does
`self._path.parent.mkdir(parents=True, exist_ok=True)` then `open(self._path, "w")`. Confirmed on the
real machine: `apps/backend/.data/foundry/foundry_exhaust_runner.lock` has mtime `10:10`, i.e. the
QA browser pass, not the 07:55 CLI run. Three consequences:

- A GET holds `LOCK_EX` for a few microseconds; an exhaust-CLI invocation landing inside that window
  refuses with `ConcurrentRunnerRefused`. Loud and re-runnable, so low harm, but real.
- `mkdir`/`open` sit *outside* the `try` in `acquire`, so an unwritable Foundry directory raises
  through `get_foundry()` and 500s the whole Foundry panel — a surface that was previously
  write-free and always-succeeding. It degrades visibly (`foundry-panel-unavailable`) rather than
  lying, which bounds the harm.
- `errno.EACCES` is mapped to `ConcurrentRunnerRefused` → the UI would report "Running — lock held by
  another invocation" for what is actually a permissions failure.

Not fixed — same frozen-module bar as B2/B3.

**B6 — OBSERVATION: `frozen_ready_total` has two independent derivations, keyed on two different
manifest fields**

`micro_routes.py:901` computes `sum(f["variant_count"] for f in _EPOCH_MANIFEST_VIEW["families"])`;
`run_hypothesis_foundry_real_exhaust.py:225` computes
`sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))`. The committed manifest has
`families: []` and the era will never generate another, so both are permanently `0` and the values
can never disagree in practice. Two notes for J-08: this is a second owner for a shared value (the
"single source of truth" anti-goal), and `f["variant_count"]` is an unguarded subscript evaluated at
module import time — a family entry lacking that key would fail the backend's import, not just the
route.

**B7 — OBSERVATION: the outcome-access census tracer no longer covers the freeze-generation calls
its own docstring claims**

`generate_hypothesis_foundry_real_epoch.py` moved `generate_freeze_set`/`build_freeze_record` out of
the traced `with` block (they now run after `census = len(hits)` and after the census check) so the
tracked JSONs could be written first and hashed. The module docstring still says the census is
"a dynamic call-trace over the actual compile/**freeze-generation** calls". Materially inert:
`foundry_freeze` is not in `_FORBIDDEN_OUTCOME_MODULES` and neither function calls into any module
that is, the recorded census in the manifest is unchanged (`0`, byte-identical file), and the script
is itself now a freeze-set member so a future edit could not silently widen it.

**B8 — OBSERVATION: the dev handoff mis-states the final `freeze_commit`**

The handoff says commit `873b4ed7` made "`freeze_commit` now equal HEAD exactly". It is
`5b41d9ef` = `HEAD~1` — which is correct and unavoidable (a commit cannot pin its own hash) and
satisfies B2's actual requirement, verified independently: `git show 5b41d9ef:<path>` hashes to the
pinned digest for all 59 entries, and `verify_commit_is_ancestor(5b41d9ef, HEAD)` → `True`.

### Frontend Findings

**F1 — OBSERVATION: two rendered states are outside the spec's declared data contract**

The spec declares `single_flight_status: "idle" | "running" | "refused_concurrent"` and
`freeze_integrity_verdict: "green" | <typed halt code>`. The backend never emits
`"refused_concurrent"` (a held lock maps to `"running"`, `foundry_runner.py:254`) and does emit
`"not_yet_verified"`, which the declared enum does not name. `apps/frontend/lib/types.ts:3172-3186` (the widened field at :3183)
discloses the second in a comment and widens the type to `string`;
`apps/frontend/app/desk/page.tsx:7830-7845` handles all four values. Honest and defensive — noted
only so the contract table and the code agree in J-08.

The subsection itself renders `exhaust_progress` verbatim with no client-side computation
(`page.tsx:7830-7901`, honest paths at :7852 and :7894), including honest pre-lock (`foundry-runner-checkpoint-empty`) and
incomplete (`foundry-runner-exhaust-incomplete`) paths.

### Test Findings

**T1 — GAP: the QA report's browser evidence is one blank image cited four times**

`reports/qa/goal-hypothesis-foundry-iter-6-qa.md` cites
`goal-hypothesis-foundry-iter-6-runner-checkpoint.png` as proof of its Visibility PASS. That file and
its three siblings (`-desk-scroll.png`, `-foundry-section.png`, `-foundry-expanded.png`) are all
9,344 bytes with the identical md5 `a435648ab35a24a350f336d2527ffb46`; opened, it is a uniform dark
rectangle with no content. Four different views cannot be one byte-identical file.

The underlying claim nevertheless holds on other evidence, which I verified myself:
`reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png` (361,986 B) and
`UT-07-result.png` (362,809 B) from the browser-QA lane, and
`reports/qa/goal-hypothesis-foundry-iter-6-runner-checkpoint-scoped-rig-crop.png` (1400×400) from the
dev fix pass, are genuine captures. I opened the crop and cross-checked every rendered value against
the real ledger row: `2026-08-27T06:55:51.071173Z`, `da7488f8…5c3260`, `Checkpoint: 0 of 0`,
`Protected/withheld/sealed reads: 0`, `Runner lock: Idle — lock free`, `Freeze integrity: green`,
and the vacuous-completion sentence — all exact. Downstream consumers should read J-07's browser
proof off the `-evidence/UT-*` and `-scoped-rig-crop` files, **not** off the QA report's own citation.

**T2 — OBSERVATION: TC-2 is proven on the fixture corpus, not by a second real-corpus invocation**

Disclosed by the developer and flagged as a NOTE by the reviewer.
`test_tc2_second_invocation_verifies_and_appends_no_second_epoch_open_row`
(`apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py:147`) runs the **real** committed
freeze-set/freeze-record/manifest against an isolated `tmp_path` ledger and the small fixture dataset
dir, so only the corpus enumeration is fixture-backed; idempotency itself is exercised through the
production `record_epoch_open`. Acceptable.

**T3 — OBSERVATION: the QA-rig sidecar copy is not as atomic as its comment claims**

`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh:162-171` states the ledger and its
`.chain_head.json` are "copied together and only together", but the sidecar copy is guarded by its
own nested `if`, so a missing sidecar would yield a ledger without its anchor. Harmless today (the
sidecar exists) and nothing on the read path calls `verify_chain`, but the comment overstates the
guarantee.

**Test quality overall: good.** The evolved TC-9 guard
(`test_foundry_real_epoch_artifacts.py:327-352`) is a genuine strengthening, not a loosening: a
three-entry allowlist plus a textual ordering assertion that `verify_freeze_set_unchanged` precedes
`SingleFlightLock` precedes the `run_family` call site. I checked the regex cannot be satisfied by
the docstring mentions. The B2 guard (`test_foundry_real_epoch_artifacts.py:182-202`) verifies every pinned path against
`git show {freeze_commit}:{path}` rather than settling for ancestry. The TC-4 counter
(`test_run_hypothesis_foundry_real_exhaust.py:346-388`) patches
`MicroAccessor.read_snapshot_rows` on the class and asserts `calls == []` across both the vacuous
real pass and a one-variant fixture pass whose `terminal_count == 1` is asserted, so "zero reads" is
not vacuous. The crash-resume test (`test_run_hypothesis_foundry_real_exhaust.py:309-343`) writes a real intent row, resumes through the full
production sequence, and asserts exactly one intent and one terminal row survive.

---

## 3. Domain Assessment

The scientific core is sound and, where it is deliberately unbuilt, it fails closed rather than
guessing.

**The lock row is real and correctly ordered.** I read the artifact rather than the handoff: one row,
`row_index 0`, `prev_hash null`, `verify_chain()` clean; a field-by-field diff against the committed
`freeze-record.json` returned an empty set. The lock timestamp (06:55:51Z) is 13 minutes after the
last freeze commit (06:42:01Z), so the spec's "one atomic sequence — code, then freeze regeneration,
then first invocation" was genuinely honoured rather than asserted.

**B1/B2/B7 are genuinely closed, not cosmetically.** 59 entries, zero absolute keys, every path
present on disk, every digest matching both the working tree and `freeze_commit`'s own committed
tree. The freeze-set now covers `source-registry.json`, `epoch-manifest.json`, the methodology spec
and both CLIs; `era_open_evidence_class_contract` is `historical_exposed_diagnostic`, sourced from
`scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC` rather than a hand-typed literal. §8.4's named
minimum members check out — `MICRO_ALGO_VERSION` (`micro_features.py:102`) and
`SNAPSHOT_FORMAT_VERSION` (`micro_snapshots.py:71`) both live in files that are in the set.

**Nothing scientific moved.** `source-registry.json` and `epoch-manifest.json` are byte-identical
across `dff64eaa` → `873b4ed7` → working tree (sha256 `d3bea09c…` / `49d8de3f…` at all three points).
One `epoch_id`, one epoch-opening row.

**Protected-read-zero is structural, not asserted.** `compute_eligible_corpus`
(`run_hypothesis_foundry_real_exhaust.py:172-195`) goes through `DatasetStore.list()` +
`micro_snapshots.exclude_withheld` — the shared choke point — and hashes with the existing
`micro_corpus.corpus_manifest_hash`, which sorts its members (`micro_corpus.py:349`) so the digest is
order-independent and portable. The withheld exclusion is demonstrably not a no-op: 18 members kept,
80 excluded on the real corpus.

**The unbuilt path fails closed.** `_default_frozen_ready_families` raises
`RealCandidateEvaluationUnsupported` on any family carrying a variant rather than skipping it — the
right call for machinery that this epoch structurally cannot reach, and it is tested in both
directions.

**Idempotency is refuse-not-overwrite.** `record_epoch_open` returns the existing row only on exact
identity-field equality across all fourteen fields and raises `ConflictingReplayRefused` otherwise,
mirroring `record_terminal`. `recorded_at` is correctly excluded from the identity set.

The weaknesses that remain (B2–B5) all share one shape: the read path and the ledger reader trust
what is on disk without re-verifying it, and the one place to change that is now frozen. That is a
consequence of the era's own design — the freeze barrier is doing exactly what it is supposed to do,
including preventing late improvements — not a defect introduced by carelessness this iteration.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_foundry_real_epoch_artifacts.py` | New read-only guard `test_freeze_record_freeze_set_hash_matches_the_committed_freeze_set` (line 139): asserts the committed `freeze-record.json`'s `freeze_set_hash` equals the committed `freeze-set.json`'s, and that the freeze-set's enumerated `entries` recompute to that digest. Closes B1 — the compensating protection the handoff claimed already existed. |

**Verification of the fix (evidence, not assertion):**

- Targeted run:
  `cd apps/backend && .venv/bin/python -m pytest tests/test_foundry_real_epoch_artifacts.py -q -p no:cacheprovider -k freeze_record_freeze_set_hash`
  → `1 passed, 22 deselected`. Whole file: `23 passed`, exit 0.
- Non-vacuity proved directly: the same assertion evaluated against a copy of the record with
  `freeze_set_hash` replaced by `"0"*64` raises — "OK: tampered freeze-record is rejected by the new
  guard" — while the committed entries recompute to the committed digest.
- Full suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -p no:cacheprovider`
  → **3921 passed, 8 skipped, 2 warnings in 422.20s**, exit 0. Exactly QA's 3920 plus this one test;
  zero previously-passing tests skipped, xfailed, or deleted.
- Freeze integrity re-verified through production code after the edit:
  `foundry_freeze.verify_freeze_set_unchanged(freeze_set, repo_root=REPO_ROOT)` raises nothing and
  `verify_commit_is_ancestor('5b41d9ef…', HEAD)` → `True`. The edited file is a test and is not a
  freeze-set member (checked: zero overlap between `git status` paths and `freeze-set.json` entries),
  so no frozen byte, no science value, and no ledger row was touched.
- Diff re-read: the change is the 30-line test block and nothing else.

No other issue was fixed. B2–B5 are all inside freeze-set members, where a fix would itself be the
anti-goal violation this audit exists to catch; B6–B8, F1 and T1–T3 are GAP/OBSERVATION class and
fixing them would be scope creep.

---

## 5. Recommended Next Step

Proceed to J-08. The phase goal is met and the era's step-8 act is complete, correctly ordered, and
independently verified against the real artifacts.

Carry these forward, in priority order:

1. **B2 is now a permanent property of this era.** The next methodology era must capture
   epoch-opening environment metadata *before* its first-read lock. Record it as an era-close
   limitation, not as a J-08 task — it cannot be repaired here.
2. **J-08 must not touch a freeze-set member.** `foundry_runner.py` and `foundry_ledger.py` are both
   pinned, so any detail drill-in or survivor-labelling work belongs in `micro_routes.py` (not in the
   set) or in a new module. B3/B4/B5 are the fixes that would otherwise be tempting and are now
   barred; the honest move is to document them, not to route around the freeze.
3. **Downstream evidence pointer.** The goal-evaluator should read J-07's browser proof from
   `reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png` / `UT-07-result.png` and
   `…-runner-checkpoint-scoped-rig-crop.png`. The QA report's own screenshot citation (T1) is a blank
   image and supports nothing.
4. **Cheap, safe operator act:** re-run `scripts/run_hypothesis_foundry_real_exhaust.py` once against
   the real corpus (~13 min, idempotent by construction) to close T2's last real-data gap. Optional.
5. The iter-6 coherence audit had not run at audit time; B6 (the dual `frozen_ready_total`
   derivation) is the item that lane should look at.
