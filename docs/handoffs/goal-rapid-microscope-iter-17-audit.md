# goal-rapid-microscope-iter-17 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

TR-23 and TR-24 genuinely landed, the trap suite genuinely reaches 29/29, and — the round's own
central question — **both traps CAN fail and their acceptance fixtures DO discriminate**. I proved
that independently with ten of my own production-source mutations (all restored byte-identically,
md5-verified) and three live probes that executed paths no committed test reaches, rather than by
re-reading the dev's or reviewer's proofs. The
gaps are real but bounded: one IMPORTANT product finding (condition 1's sufficiency floors are
caller-supplied and were nowhere on the permanent artifact — fixed here, and the underlying spec
tension flagged as owner-owed rather than improvised away), three brand-new code paths that no
committed test can falsify, a lineage frontier narrower than r8 §8.2's own enumeration, and a
browser-evidence lane that ran against a fixture rig while the QA report claims otherwise.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `SEALED_PASS_RULE_V1` condition 1 is decided by caller-supplied floors,
and the permanent artifact recorded a rule identity it had not applied**

`apps/backend/app/research/micro_sealed_evaluation.py:365-366` (pre-fix:
`floors = candidate_spec.get("floors") or {}`) and the artifact block at L381-407.

Spec §8.1 condition 1 pins the floors: "the per-fold sufficiency floors **already pinned in §1** —
`WF_FOLD_MIN_OBSERVATIONS` observations, `WF_FOLD_MIN_SIGNAL_SESSIONS` signal-bearing sessions, and
`WF_FOLD_MIN_SYMBOLS` symbols" (30 / 8 / 2). The shipped evaluator instead passed the candidate
spec's own `floors` dict straight into `walkforward.summarize_fold_observations`, which honours it
key-by-key. I did not infer this — I ran it (probe `probe_c_floors.py`). A candidate spec carrying
`floors={observations:1, sessions:1, symbols:1}`, `econ_floor={"floor_bps": 0.01}` and ONE
observation of 0.02 produced a **permanent, single-shot `verdict: "pass"`**:

```
verdict = 'pass'      n = 1   n_sessions = 1   n_symbols = 1   missing = {}
conditions = {'sufficient_observations': True, 'registered_direction': True,
              'clears_economic_floor': True, 'historical_oos_rule_process': True}
rule_hash = '097358...5c12c'   (== sealed_pass_rule_hash(), which embeds 30 / 8 / 2)
artifact records the floors actually applied? -> False
```

Two things are wrong there. The artifact **affirmatively asserts** `sufficient_observations: True`
with `missing: {}` on n=1; and its `rule_hash` — the very field condition 4 checks for rule identity
— certifies floors of 30/8/2 that the run never applied. Spec §8.1 requires the artifact to be
"sufficient to reproduce the verdict"; condition 1 was **not** reproducible from
`n`/`n_sessions`/`n_symbols` alone. This is the same family as the defect the round set out to kill
("a caller-supplied `passed: bool` is inadmissible"): the caller cannot assert the verdict, but it
could assert the one condition the spec pins as a constant — the anti-goal's own "never lower a
minimum sample size … to manufacture a survivor".

Mutation AM-7 quantifies the dependence: replacing the line with `floors = {}` (i.e. actually
applying the §1 floors) turns **four** of the module's own committed tests from `pass`/`fail` into
`insufficient` (`test_tc2_…`, `test_tc5_…`, `test_tc7_…`, `test_tc8_…`). Every PASS and FAIL verdict
in the TR-23 suite exists only because the fixtures narrow the floors.

**Root cause is a genuine spec tension, not dev carelessness — and the correct fix is an owner
ruling, not an improvisation.** A vault shard is ONE symbol-day (§7.3 seals on
`HMAC(f"{symbol}:{YYYY-MM-DD}")`; `vault.assign_shard` records one `symbol` + one `session_date`).
A single shard therefore can never carry 8 signal-bearing SESSIONS or 2 SYMBOLS. Read literally,
§8.1 condition 1 makes a PASS verdict **structurally unreachable forever** — every sealed evaluation
would return `insufficient`. §8.1 condition 1 and §7.3/§7.4 are in real tension over whether "the
shard's recomputed observations" means one shard or the family's whole exposed tranche. Under rule
T-1 that is an owner ruling; pinning the floors myself would have been exactly the invention T-1
forbids. **What was missing is the T-1 disclosure**: the dev disclosed three interpretation calls
(weekday roll-forward, rule-identity-at-assignment, caller-supplied `observations`) but not this
one, and the module docstring's "it reuses `WF_FOLD_MIN_OBSERVATIONS`/`_SIGNAL_SESSIONS`/`_SYMBOLS`
… via the SAME `summarize_fold_observations` function" reads as if the pinned floors are enforced.

Fix applied (honesty and provenance only — no rule invented, no verdict changed): a `_resolved_floors()`
helper (`micro_sealed_evaluation.py:203`), the resolved triple persisted on every artifact as
`floors_applied` (`:396`), and a docstring paragraph disclosing the tension and marking it
OWNER-OWED. A narrowed floor can now never be silent in a permanent verdict or an export bundle.
**Owner ruling needed:** does §8.1 condition 1 apply per-shard, or across the family's whole exposed
tranche? Until it is answered, `floors_applied` makes the answer used visible on every record.

**B2 — GAP: the shipped lineage frontier is narrower than r8 §8.2's own enumeration, in two named
ways, neither disclosed in the handoff or review**

`apps/backend/app/research/micro_graduation.py:509-535` and `:669`.

(i) §8.2 enumerates "… and **any other outcome-bearing read in the exposure registry (§6.7)**" among
the items the frontier maxes over. `_lineage_data_frontier` scans scout trials + fold results +
sealed evaluations only; `build_export_bundle` takes no `ExposureRegistry` at all. Exposure rows
carry a perfectly usable `logged_at`, so this is not a "no usable timestamp field" drop under T-1 —
it is simply absent. A serving act on a lineage's window that post-dates every ledger row will not
move the frontier, which is precisely the laundering TR-24 exists to block.

(ii) The fold arm reads `wf.fold_results_for_sequence(wf_ledger, sequence_id)` for the ONE
caller-supplied sequence (`:669`). A killed sibling that ran its own walk-forward sequence
contributes only its Scout `registered_at`; its own later fold evidence is invisible.

Both narrowings trace to the phase spec itself (its IN SCOPE transcription of the formula omits (i);
its OUT OF SCOPE forbids the fold↔family join (ii) would need), so this is not developer drift. But
neither is named anywhere in the dev handoff or the review, and both narrow the exact protection the
trap advertises.

**B3 — GAP: the weekday-only embargo roll-forward errs PERMISSIVE, and is described as
"conservative" in both the code and the dev handoff**

`apps/backend/app/research/micro_graduation.py:558-580` (`:573` carries the wording).

The behaviour is correct as specified and I verified it end-to-end rather than by reading (probe
`probe_a_embargo.py`, the first execution this code has ever had — see T1): with a real registered
fold spec carrying `embargo_sessions=5` and a frontier of Friday 2026-05-01, the bundle produced
`embargo_rule_id: "weekday_roll_forward_v1"`, `evidence_safe_boundary: "2026-05-08"`,
`proposed_confirmation_boundary: "2026-05-11"` — hand-checked (Mon 4, Tue 5, Wed 6, Thu 7, Fri 8;
then strictly-after Friday rolls to Monday). Direct unit probes also check out: `roll(Fri, 1) =
Mon`, `roll(Sat, 1) = Mon`, `roll(Fri, 10) = Fri+2wk`.

The defect is in the characterisation, not the arithmetic. A market holiday inside the span is
counted as a session, so **fewer** than N real trading sessions elapse and the boundary lands
**earlier** than a calendar-exact rule would put it — the embargo is under-applied. The docstring's
"a slightly-conservative estimate carries no admission risk this era" and the dev handoff's echo of
it have the direction of error backwards.

On the owner's question (invented rule, or reasonable disclosed approximation?): it is a rule no
spec or ruling states, but it is disclosed in code, stamped on every bundle as `embargo_rule_id`
(never silent), and feeds a value §8.2 itself calls advisory — the real admission gate is the
untouched Referee's own registration-time boundary. I judge it an acceptable disclosed
approximation, **provided the direction-of-error wording is corrected**. Left unfixed here as a
GAP-level documentation issue rather than expanding my footprint.

### Frontend Findings

None. Zero `apps/frontend/**` files changed (`git status` verified), so the round is genuinely
backend-only and the "no new user-facing capability / no UI surface change" claims hold. The
graduation endpoint's payload gains internal fields, and no `/desk` section or MCP tool reads it
(grep-confirmed).

### Test Findings

**T1 — GAP: three brand-new code paths are invisible to the committed suite (mutation-proven)**

Each mutation below was a real on-disk edit of production source, run against
`tests/test_micro_sealed_evaluation.py` + `tests/test_micro_graduation.py` (39 tests), then restored
and md5-verified byte-identical, with the restored run re-confirmed green:

| Mutation | Change | Result |
|---|---|---|
| AM-3 | `micro_sealed_evaluation.py:340` `spec_registered_at < assigned_at` → `<=` | **NO TEST FAILED** |
| AM-6 | `micro_graduation.py:594-602` embargo application removed entirely | **NO TEST FAILED** |
| AM-8 | `micro_graduation.py:526` sealed-evaluation arm of the lineage scan dropped | **NO TEST FAILED** |

AM-3 is the sharpest: §8.1 step 1 requires the candidate spec to be frozen **strictly before**
assignment, and that strictness boundary can silently drift to `<=` with the whole suite green. This
is the identical `<`→`<=` pattern this round's own GAP B3 fixture was added to close for
`is_exposed_before` — and B3 works (mutation AM-10: `micro_accessor.py:176` `<` → `<=` fails exactly
one test, `test_gap_b3_an_exactly_simultaneous_logging_does_not_count_as_before`, out of 86 across
`test_micro_accessor.py` + `test_walkforward.py`). The round applied the discipline to the accessor
and not to its own new module's equivalent boundary. No fixture anywhere sets
`registered_at == assigned_at`.

AM-6 confirms and extends the reviewer's MINOR finding — I removed the whole `frontier + embargo`
half, not just the loop body, and nothing noticed. No test in the repository registers a fold spec
for a graduation fixture, so `embargo_sessions` is 0 everywhere and `_roll_forward_weekday_sessions`
had **never executed** before probe A.

AM-8 kills TR-24's own spec text ("sealed evaluations of any verdict including FAIL/`insufficient`"
feed the frontier) with no test failing. The behaviour itself is correct — probe
`probe_d_lineage.py` confirms a FAILED sealed evaluation dated 2026-07-04 moves the frontier to
2026-07-04 with `lineage_frontier_evidence_ids == ['ds-fail']`, and that an ineligible
(diagnostic + `operator_process` + insufficient) fold also moves it. These are coverage gaps, not
behaviour defects.

For contrast, the clauses the DoD explicitly required proofs for are genuinely non-vacuous under my
own, different mutations: AM-1 (`condition_5_class_process` → `True`) fails naming
`assert 'fail' == 'pass'`; AM-2 (drop the `family_root_id` equality from the vault binding check)
fails `DID NOT RAISE SealedEvaluationRefusedError`; AM-4 (`max` → `min` in the frontier) fails two
tests naming `'2026-02-05…' == '2026-05-01…'`; AM-5 (strictly-after → on-or-after) fails two tests
naming `'2026-05-01' > '2026-05-01'`.

**T2 — GAP: J-08's replay green is rig-dependent and carries the identical stale assertion the dev
correctly diagnosed in J-10**

`runs/goal-session-rapid-microscope/journey-scripts/J-08.json` step 4 expects
`"No walk-forward sequences run."`; `J-10.json` step 11 expects `"No fold specs registered."`. Both
strings render only when the walkforward payload is empty
(`apps/frontend/app/desk/page.tsx:6506` and `:6526`). The real store carries a `fold_spec`
`playbook_setups_diagnostic_v1` (`registered_at 2026-08-17T17:18:38.329992Z`) plus fold results
under `seq-d39d20e47af24671`; the session rig has no `micro_walkforward` directory at all. J-10 was
replayed against the real store → honest FAIL; J-08 was replayed against the rig → PASS. Same stale
assertion, opposite environments — only J-10's was noticed.

The dev's and reviewer's J-10 diagnosis is independently confirmed (the fold spec predates this
round by three days and nothing this round touches `walkforward.py`), and their restraint is
endorsed: `git diff` on `journey-scripts/` is empty, so `J-10.json` really was left byte-unchanged
rather than edited to pass. That was the correct call and I did not touch it either.

**T3 — OBSERVATION: TR-23 / TR-24 appear only in module docstrings and section comments**, never in
a test function name (contrast `test_tc12_tr26_reverting_the_fix_…`). The 29/29 sweep is satisfied
(I re-ran it independently: TR-1…TR-29, exactly 29 distinct ids, TR-17's a/b/c deduplicated), but a
name-level label would make the suite self-describing.

**T4 — OBSERVATION:** `tests/test_micro_sealed_evaluation.py:34` imports
`MicroAccessorOriginFenceError` and never uses it.

### Process / Evidence Findings

**E1 — IMPORTANT (unresolved — evidence integrity, no product impact): the QA report's environment
claim is false; the browser lane is right.**

QA asserts "Backend data store: Using default (real) store, not QA fixture (`TAPEOLOGY_DATASET_DIR`
not set)" and lists "Walk-Forward (exists, can be expanded - **registered fold spec found in
store**)". The browser lane asserts the opposite, with evidence: `/proc/2245354/environ` on the live
`:8301` uvicorn showed `TAPEOLOGY_DATASET_DIR` (and every sibling `*_DIR`/`*_DB`) pointed at
`/home/dennis-chan/.cache/iad/iad.goal-rapid-m-d1ead7e7.3015052/tapeology-store-scope-qa/rig/`.

I settled it from the filesystem, since both services are now stopped:

- that rig directory exists (created 06:09, last modified 06:56) and contains **no
  `micro_walkforward` directory at all** — so `fold_specs: []` was the truthful answer there;
- the real store `apps/backend/.data/micro_walkforward/walkforward_ledger.jsonl` does carry the fold
  spec, dated 2026-08-17;
- QA wrote at 06:33 and the browser lane ran 06:40-06:48, both after the rig existed, against the
  same never-restarted backend PID.

**The browser lane is correct and its SKIP (rather than a false FAIL) was the right call. QA's claim
is wrong** — it reads like a check of QA's own shell environment rather than the server process's.
Consequence: no product defect, but the round's browser-verified J-10 sentinel and the J-01/J-04/
J-05/J-08 replays were all executed against a fixture rig, so their regression signal is weaker than
the QA report represents. I could not fix this (services down; another lane's report is not mine to
rewrite) — it is recorded here as the authoritative correction.

**E2 — GAP: J-07 was not actually re-verified, and could not have been discriminating if it had
been.** The merged UI results mark `UT-J-07` **DEFERRED-BUDGET** ("not run this iteration"), while
DoD/TC-21 names J-07 in Required-still-passing. QA's direct-endpoint substitute (HTTP 200,
`{"families": [], "message": "No candidates ledgered.", "chain_verification": {"ok": true}}`) is the
best check available — but neither the rig nor the real store has a `micro_graduation` directory, so
that response is identical whether the rewritten module works or is broken. J-07 is the journey
whose owner module was rewritten this round; its verification this round is non-discriminating.

**E3 — OBSERVATION:** `ux-regression-reviewer` was shed by the SPEED-15 budget trim
(`reports/phase-goal-rapid-microscope-iter-17-ux-regression.md`, verdict UX-REGRESSION-SKIPPED). By
design non-blocking, recorded for the evaluator's ledger.

**E4 — OBSERVATION: I agree with the pump's demo-script edit.** The Walk-Forward step now reads
"Whether any folds appear depends on which data store this run is pointed at, so we simply confirm
the section opens and reports its state honestly," and the step carries no `expect`. The previous
wording asserted an environment-dependent fact that was false under the rig; the rewrite is accurate
and replay was never at risk.

---

## 3. Domain Assessment

**TR-23 (`micro_sealed_evaluation.py`) — sound, with one owner-owed hole now made visible.** The
seven-step sequence is genuinely implemented, not narrated: the vault-exposure binding is confirmed
against `vault.build_vault_state` for this exact `family_root_id` (AM-2 proves the check is load-
bearing), the rule-identity check runs **before** any shard read so a changed rule fails closed with
nothing persisted (TC-3 asserts the ledger stays empty), the accessor read is real (a fenced
accessor is refused; `observed_through` is stamped from actual snapshot rows, never from the
caller), and `summarize_fold_observations` is consulted rather than reimplemented. The tri-state is
honest — `insufficient` is a distinct persisted value that refuses the transition without collapsing
into `fail`, and the single shot is consumed because the shard was genuinely exposed, matching §8.1
condition 1's own wording. `record_sealed_evaluation`'s `passed: bool` really is structurally gone
(a `TypeError` at argument binding, not a deprecation warning). The one weakness is B1: every
verdict input except the vault binding and the rule hash arrives from the caller's `candidate_spec`,
which the module never cross-checks against a registered Scout row — §8.1 step 2's "load the
candidate's canonical **registered** spec" is satisfied by presence checks, not by a load. With zero
production callers today that is latent rather than live, but it is the shape of hole that becomes
real the moment J-08/J-09 wires a caller.

**TR-24 (lineage boundary) — the right formula, correctly computed, thinly tested.** The rejected
naive "latest timestamp on the survivor's own rows" is genuinely gone: kills, folds of any
verdict/class/process-label, and sealed evaluations of any verdict all feed the max, and I confirmed
each arm by execution rather than by reading. The derivation is fully persisted
(`lineage_data_frontier`, `lineage_frontier_evidence_ids`, `frontier_observed_through`,
`embargo_rule_id`, `embargo_sessions`, `evidence_safe_boundary`, `handoff_created_at`,
`proposed_confirmation_boundary`) and `_REQUIRED_BUNDLE_FIELDS` was extended to match. One detail I
specifically checked for a lurking bug and cleared: `_proposed_confirmation_boundary` takes a `max()`
across a date-only `evidence_safe_boundary` and a full-precision ISO `handoff_created_at`, which
would be a lexicographic trap — but only `basis[:10]` is ever used afterwards, so the mixed
comparison can never change the answer. The `_evidence_item_observed_through` derivation is faithful
to the decomposer's logged ruling (each row type's own recorded instant; Mode-A's later
`validation_revealed_at` preferred over the earlier `registered_at`, which is exactly TC-11's
requirement) — the honest gaps are B2's two narrowings, not the field mapping.

**Frozen rails — all re-verified independently, not accepted from the handoff.** Fingerprint prints
`08e471b10130e1e2`; the six `referee_*.py` SHA-256s are byte-identical to the era's iteration-0
commit `38c83b4` (checked file-by-file); `micro_chain_ledger.py` is unchanged versus `HEAD` (it did
not exist at iteration 0, and the dev handoff words this correctly); `EXPECTED_TOOLS` is exactly 26;
`git diff app/config.py` is empty; zero `apps/frontend/**` files changed; `npx tsc --noEmit` exits 0
with no output; `J-10.json` is byte-unchanged. The dev's reported md5s for the two mutated modules
(`3f64656c7bbc5857ccae9d614cd9794f`, `0eaff0dfb27f3fc098d11ed0036500c2`) match the files on disk
exactly, so the dev's own on-disk mutation-and-restore really was byte-clean.

**Suite count — my own figure, from `--junitxml`.** Pre-fix, on the shipped tree:
`tests="3270" errors="0" failures="0" skipped="8"` → **3262 passed**, 619.7s. That matches the
reviewer (3262, twice) and QA (3270 collected / 3262 / 8) and clears the 3238 baseline. The dev's
3261 came from a collection of 3269, one test earlier — a stale count, not a discrepancy that
matters. Post-audit-fix the same command reports `tests="3271" … skipped="8"` → **3263 passed**,
0 failures, 0 errors.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/micro_sealed_evaluation.py` | `_resolved_floors()` (`:203`) resolves the three per-fold floors condition 1 actually applies; `evaluate_sealed_verdict` uses it (`:365`) and persists it on the artifact as `floors_applied` (`:396`); a module-docstring paragraph discloses that a candidate spec may narrow the §1 floors, records **why** pinning them is not a safe unilateral fix (a one-symbol-day shard can never meet 8 sessions / 2 symbols, so PASS becomes unreachable), and marks the §8.1-vs-§7.3/7.4 tension OWNER-OWED under T-1. No verdict changes; no rule invented. |
| 2 | Important | `apps/backend/tests/test_micro_sealed_evaluation.py` | `test_the_artifact_records_the_floors_condition_1_actually_applied` — asserts the exact resolved triple `{3, 1, 1}` on the persisted row, asserts it differs from the §1-pinned `{30, 8, 2}` (deliberately different numbers, never coincidental), asserts `rule_hash` still pins §1, and asserts `_resolved_floors({})` returns the §1 constants verbatim. |

**Post-fix self-verification.**

1. Targeted run — `pytest tests/test_micro_sealed_evaluation.py tests/test_micro_graduation.py
   tests/test_micro_accessor.py tests/test_micro_observer.py -q -p no:randomly --junitxml=…` →
   `tests="98" errors="0" failures="0" skipped="0"`.
2. Non-vacuity of my own fix (mutation AM-9) — replacing `"floors_applied": floors` with a hardcoded
   `{30, 8, 2}` makes the new test FAIL naming the exact wrong dict
   (`assert {…'n_symbols': 2} == {…'n_symbols': 1}`); restored byte-identically
   (md5 `a57e5301b026e8c8502e70bc579254f2` before and after), green again.
3. Diff minimality — `micro_sealed_evaluation.py` is untracked, so I proved it by reconstruction:
   reverting exactly my four edits reproduces md5 `3f64656c7bbc5857ccae9d614cd9794f`, the
   dev/reviewer-verified original, byte for byte. `micro_graduation.py` is still
   `0eaff0dfb27f3fc098d11ed0036500c2`; `micro_accessor.py`, `test_micro_graduation.py`,
   `test_micro_accessor.py`, `test_micro_observer.py` and `J-10.json` are untouched by me. All ten
   audit mutations were restored and md5-confirmed.
4. Full backend suite re-run after the fix, `--junitxml`, `-p no:randomly`:
   `tests="3271" errors="0" failures="0" skipped="8"` → **3263 passed / 8 skipped / 0 failed /
   0 errors**, 625.5s — exactly the pre-audit 3262 plus my one added test, no skip-count drift.
   `npx tsc --noEmit` in `apps/frontend`: exit 0, no output (clean).
5. No new finding introduced: the change is additive (one deterministic artifact field), so
   `record_sealed_evaluation`'s whole-artifact idempotent-replay comparison stays consistent (TC-4
   green), and no consumer asserts an exact key set on sealed-evaluation rows (grep-verified).

I deliberately did **not** fix the GAP-level items (T1's three unfalsifiable paths, B2's narrowings,
B3's wording, T2's stale J-08 assertion). They are next-round work, not audit-time scope creep — and
in T2's case, editing the assertion is precisely the wrong move, exactly as dev and reviewer judged.

---

## 5. Recommended Next Step

Proceed. The round achieved its goal and the product is materially stronger than before it. The
named carry-forward, in priority order:

1. **Owner ruling (blocking for any real sealed evaluation): does `SEALED_PASS_RULE_V1` condition 1
   apply per-shard or across the family's whole exposed tranche?** As written it cannot be satisfied
   by a one-symbol-day shard. Until it is answered, `floors_applied` keeps the answer actually used
   visible on every permanent record, but no J-08/J-09 caller should be wired to
   `evaluate_sealed_verdict` before the ruling lands.
2. **Close the three unfalsifiable paths (T1)** with fixtures that can fail: a
   `registered_at == assigned_at` boundary fixture for the strictly-before check; a graduation
   fixture that registers a real fold spec with `embargo_sessions > 0` and asserts the exact
   resulting `evidence_safe_boundary`; and a lineage fixture where a sealed evaluation's own
   `evaluated_at` is the latest instant. All three are small, and each closes a "trap clause that
   cannot fail" of exactly the kind that has escaped three rounds running.
3. **Re-run J-10 and J-08 against the real store on a rig whose walkforward ledger reflects it**, and
   decide once for the era whether the golden scripts should assert empty-state copy at all — T2
   shows the current answer is environment-dependent in both directions.
4. Correct B3's direction-of-error wording, and record B2's two frontier narrowings as known
   limitations in the era's assumption ledger rather than leaving them only in this report.
5. J-10 remains `partial` by design (step 2, the byte-identical rerun check, was explicitly out of
   scope) — the planned outcome, not a shortfall.
