# Iteration 6 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The one-way step the goal calls the era's second irreversible act really happened, and I checked it
myself instead of trusting the reports. The Foundry's record book now holds exactly one opening row,
written after the code it points at was committed, and I re-computed the big data fingerprint inside
it from the real 26 GB store on this machine — it matches to the character. So J-07 "Goal Mode
exhausts the frozen epoch" is done. But the structural check on this iteration failed: the same
number is now worked out in two different places, from two different fields of the same file, and
the file that holds the second copy is one the era has already sealed — so the obvious repair is not
allowed by the era's own rules. That failure blocks any "goal achieved" call, so the next iteration
must settle it before anything new is built.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The Foundry opens as a new finite era | passing | passing (replay) | reports/phase-goal-hypothesis-foundry-iter-6-ui-test-results.md UT-J-01 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-01-verify.png |
| J-02 Sources compile into auditable CandidateSpecs | passing | passing (replay) | UT-J-02 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-02-verify.png |
| J-03 Generic interpretation preserves Scout decisions | passing | passing (replay) | UT-J-03 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-03-verify.png |
| J-04 Foundry owns denominator, ledger, freeze barrier, lock | passing | passing (replay; spot-checked by me) | UT-J-04 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-04-verify.png — I opened it: the fixture subview is badged "HERMETIC FIXTURE — NOT THE REAL EPOCH", so fixture and real stay visibly distinct |
| J-05 Complete factory passes hermetic oracles | passing | passing (replay) | UT-J-05 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-05-verify.png |
| J-06 One complete real epoch generated and committed | passing | passing (replay; spot-checked by me) | UT-J-06 · reports/qa/goal-hypothesis-foundry-iter-6-evidence/J-06-verify.png — I opened it: `epoch:afd19e9c11a6534f` and `ed40dbc2…` on screen equal the committed manifest/registry |
| **J-07 Goal Mode exhausts the frozen real epoch** | **failing** | **passing** | UT-02/UT-03/UT-07 rows · reports/qa/goal-hypothesis-foundry-iter-6-evidence/UT-02-result.png (I opened and enlarged it: "REAL EPOCH — NOT A FIXTURE", first-read lock `2026-08-27T06:55:51.071173Z`, hash `da7488f8…5c3260`, "Checkpoint: 0 of 0", "Protected/withheld/sealed reads: 0", "Runner lock: Idle — lock free", "Freeze integrity: green", vacuous-completion sentence) |
| J-08 Operator sees the final Foundry truth | failing | failing (not targeted; explicitly OUT OF SCOPE in the iteration spec) | no results row, no screenshot — its final-truth surface and the T-9/T-10/T-11 guard battery were deferred by the spec |

### What I verified myself for J-07 (not accepted from any report)

| J-07 step | How I checked it |
|---|---|
| 1 invoke the resumable single-flight runner; checkpoint observable | one `epoch_open` row in `apps/backend/.data/foundry/foundry_trial_ledger.jsonl`; ordinal on screen |
| 2 opening row pins freeze hashes + eligible-corpus hash, before any outcome read | all 12 freeze fields byte-equal to `docs/hypothesis-foundry/freeze-record.json`; row at 06:55:51Z, commits `1573f457`…`873b4ed7` at 06:40–06:42Z |
| 3 every FROZEN_READY variant terminal; blocked/excluded sources unchanged | `families: []`; `source-registry.json` and `epoch-manifest.json` sha256 identical to iter-5's `dff64eaa` |
| 4 only the legal exposed corpus; provenance reported | I re-computed the corpus fingerprint from the real store: 98 datasets, 80 withheld excluded, 18 members → `da7488f8…5c3260` = MATCH. Fixture corpora hash to different values, so this is not fixture-derived |
| 5 family denominator equals the frozen manifest denominator | vacuous — zero families |
| 6 kills/survivors map mechanically; no drift; no second epoch | one `epoch_id`; freeze-set entries all match the working tree (zero drift) |
| 7 interrupt/resume, no duplicate terminal row | I ran `test_j07_step7_fixture_backed_crash_resume_through_the_real_sequence` — passes (fixture-backed path is explicitly permitted by step 7) |
| 8 protected/withheld/Vault/Referee acts stay zero | TC-4's live counter asserts `calls == []` on both the real and a one-variant pass; store-scope guard CLEAN (11395 protected files byte-identical) |
| freeze bookkeeping B1/B2/B7 | 59 freeze-set entries, 0 absolute paths; every entry's bytes at `freeze_commit 5b41d9ef` hash to the pinned digest; `5b41d9ef` is an ancestor of HEAD; `era_open_evidence_class_contract` present |
| tests | I re-ran the three Foundry suites myself: 44 passed, 0 failed |

Gap recorded on J-07 (does not withhold the pass): step 4's "unavailable counts" (`withheld_excluded = 80`) is returned by the command and never shown on `/desk`. It is vacuous here — there were zero evaluations — but J-08's final-truth surface should display it.

## Anti-goal Check

Worked from `runs/goal-session-hypothesis-foundry/iter-6/scan-report.md` (CLEAN) and `iter-diff.md` (16 files).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN on added lines; no new config/env file in the 16-file list |
| Paid / external SaaS | OK | no manifest changed (no package.json / requirements / pyproject in the diff) |
| License changes | OK | scan-report CLEAN; no LICENSE file touched |
| Fabricated / substituted data | OK | the QA rig copies the REAL ledger + its chain sidecar (`qa_playbook_iter7_fixture_scoped_backend.sh:162-171`), with an honest "not recorded yet" fallback; the panel is badged "REAL EPOCH — NOT A FIXTURE" and the fixture freeze view is badged "HERMETIC FIXTURE — NOT THE REAL EPOCH" |
| No execution path, ever | OK | grep of added lines for broker/order/paper-trading terms returns only docstring prose about "execution order" and "canonical order" |
| Frozen foundations stay frozen | OK | iter-4's finding stays resolved; no reassignment of any frozen module attribute in the diff; all 59 freeze-set files byte-identical to their pinned digests |
| No lookahead | OK | no time-dependent value added; the corpus enumeration reads dataset metadata only |
| **Single source of truth** | **VIOLATED (minor, unresolved, blocking)** | `frozen_ready_total` has two owners: `apps/backend/app/research/micro_routes.py:901` (`variant_count`) and `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225` (`len(variants)`). Named by `iter-6/coherence.md` as its blocking Data-Contract violation and independently by audit finding B6 |
| Deterministic and seeded | OK | grep of added lines finds no `random`, `np.random`, `time.time()`, or `datetime.now()` |
| Immutable registered data | OK | store-scope guard CLEAN; the CLI reads dataset id/checksum metadata only, never rewrites a dataset |
| **Persistence stays scoped (page-load GET is read-only)** | **VIOLATED (minor, unresolved, blocking — literal reading)** | `read_exhaust_progress` acquires a real lock, and `SingleFlightLock.acquire` does `mkdir` + `open(path,"w")` (`foundry_runner.py:197-201`, called at `:250-254`), so every page load writes a lock file. The rail's operative intent is intact (no market data recorded, no candidate computed, runner not triggered); the literal "read-only" wording is not. Audit B5 confirms the lock file's timestamp tracks the browser pass |
| No candidate invented / no late variant / no family splitting after freeze | OK | `epoch-manifest.json` and `source-registry.json` sha256 identical to `dff64eaa` |
| No second Foundry statistical decision rail | OK | the CLI drives the existing `foundry_runner.run_family` / `run_one_candidate` |
| No second real generation epoch | **carried over (minor, unresolved, blocking)** | iter-5's finding. The bypass mechanism is now closed — `_load_existing_manifest_store` raises `ManifestStoreMissingError` (`generate_hypothesis_foundry_real_epoch.py:894-909`), which I read and whose TC-7 refusal + positive-control tests I ran. The historical fact that two `epoch_id`s existed is not undone; the auditor asked for owner ratification, and only the owner can give it |
| No science-affecting change after the first-read lock | OK | the lock is 06:55:51Z; the only post-lock edits are uncommitted test/QA-rig files, none of which is a freeze-set member, and zero freeze-set drift exists in the working tree |
| No automatic corpus registration / retention / release / Vault / graduation / Referee act | OK | grep finds only freeze-set hash entries and docstrings; store-scope guard CLEAN |
| No auto ranking among diagnostic survivors | OK | zero candidates exist |
| No guard edited/deleted/xfailed to pass a journey | OK | two test "removals" in the diff are a signature change and a deliberate, disclosed evolution of TC-9 from "satisfied by absence" to a positive check that also asserts freeze-verify precedes lock precedes runner call; nothing is skipped or xfailed |

**Disposition counts (`anti_goal_disposition.py summary`, after my write):** total=4 · resolved=1 · unresolved_blocking=3 · unresolved_non_blocking=0 · unresolved_critical=0. No owner disposition exists on any entry; I may not write one.

**Coherence:** `runs/goal-session-hypothesis-foundry/iter-6/coherence.md` = **COHERENCE-FAIL** (duplicate computation of `exhaust_progress.frozen_ready_total`). Information-architecture check passed. This is a structural veto on GOAL_ACHIEVED.

## Next-Step Recommendation

Two things must happen next, in this order.

First, settle the structural failure, because it blocks the era from ever being declared done. The
same count is worked out in two places from two different fields of the same file. The obvious
repair — delete the second copy and have both callers share one helper — is **not currently legal**:
the file holding the second copy, `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py`, is
one of the 59 sealed files, and its fingerprint is written into the one-way record row that was
created this iteration. Editing it would break the era's own seal checks. I verified this myself, so
please do not let the next iteration quietly edit a sealed file to make the check go green. The next
iteration should try the legal route only — put the one true owner in a file that is not sealed
(`micro_routes.py` is not sealed) and add a test proving the sealed command's own line always
produces the identical number — and if that is judged not to satisfy the check, stop and ask the
owner rather than breaking the seal.

Second, build J-08 "The operator sees the final Foundry truth", the last remaining journey. It needs
the final on-screen summary (including the 80 withheld datasets that were correctly left out, which
today is only printed by the command), the honest "no survivors" statement, and the full battery of
protective checks its own text lists. None of that touches a sealed file.

Three decisions belong to the owner, not to the machine, and the era cannot be declared finished
until they are made: (1) accept or reject the first real epoch that was created and thrown away
before anything was published; (2) accept the duplicated count as a known, harmless, permanently
recorded flaw, or sanction breaking the seal to remove it; (3) accept that a page visit writes a
small lock file, since its fix also lives in a sealed file. Two further gaps found by the auditor
are permanently unfixable for the same reason and should be written into the era's closing record
rather than repaired: the opening row carries no runtime-environment note (B2), and nothing on the
read path re-checks the record book's chain (B3).

Run the next iteration at **full** depth. Twice in this session a plain "continue" was automatically
downgraded to the lighter pipeline because the iteration ran over its time budget, and the next
iteration is the era's closing act with three open findings — a human should force full depth if the
budget rule tries to downgrade it again.
