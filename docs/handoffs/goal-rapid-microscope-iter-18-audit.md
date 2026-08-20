# goal-rapid-microscope-iter-18 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

TR-30's own goal is genuinely achieved: I re-proved by execution (not by reading) that the
iteration-17 defect is dead — nine different caller-supplied floor shapes, including the exact
`floors={1,1,1}` + one-observation payload that produced a permanent `"pass"` last round, now all
yield `insufficient` with the evaluator-owned floors recorded on the artifact. But the audit also
found one real regression this iteration introduced and shipped unnoticed: the new QA seed writes a
vault shard into the SHARED browser-QA rig, which broke the golden `"No shards recorded."`
assertion in **J-08** (a Required-still-passing journey) and **J-10** (the kept-product sentinel).
It went undetected because the browser and deterministic-replay lanes never ran this iteration —
the spec's own `Frontend Present: no` metadata contradicts its own DEFINITION OF DONE, and QA
skipped both lanes while reporting PASS. I fixed the two golden assertions, then ran the replay
lane myself: 8/8 journeys now pass. A second, pre-existing gap of the *same defect class* TR-30
just closed (condition 3's economic floor is still caller-supplied and unverified) is documented,
proven, and left for the owner.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the new QA seed silently broke two golden journeys' assertions.**

`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh:121` adds
`seed_micro_graduation_iter18_fixture.py` to the **one mandatory browser-lane rig launcher**
(`scripts/start_scoped_qa_backend.sh:73` execs exactly this script; it is tapeology's
`STORE_SCOPE_PREPARE_CMD`, so every browser/replay pass in this era drives this rig). The seed
must seal → assign → expose a real vault shard before `evaluate_sealed_verdict` can run
(`seed_micro_graduation_iter18_fixture.py:143-152`), so the rig's vault goes from 0 shards to 1.
`apps/frontend/app/desk/page.tsx:6740` renders `"No shards recorded."` only when
`vault.shards.length === 0`, and both
`runs/goal-session-rapid-microscope/journey-scripts/J-08.json:11` (step 5) and
`runs/goal-session-rapid-microscope/journey-scripts/J-10.json:18` (step 12) assert that exact
string.

Proven by execution, not inference. I started the real rig through the real launcher
(`start_scoped_qa_backend.sh <scoped-root> 8302`) plus the frontend on :3302, then replayed J-08
with the same runner the lane uses:

```
$ python3 scripts/automation/lib/demo_runner.py --mode verify \
    --scripts-dir runs/goal-session-rapid-microscope/journey-scripts --journeys J-08 \
    --base-url http://localhost:3302 ...
[demo_runner] verify: 1 journey(s), 1 failed (verdict: FAIL)
| UT-J-08 | ... | step 05 expected "No shards recorded." did not appear | FAIL |
```

`curl http://localhost:8302/research/desk/micro/vault` on that same rig: `shards: 1
universes: 0 ['PGQA'] ['iter18-qa-universe']`.

**Fix applied.** This iteration is precisely the one the phase spec's own NOTES policy anticipated
("the assertion is revisited in whichever future iteration first makes that endpoint's honest state
non-empty"). I replaced the now-dishonest empty-state assertion in both scripts with a string
copied verbatim from the endpoint's actual current rendering — `iter18-qa-universe`, the seeded
shard's `universe_id`, rendered at `apps/frontend/app/desk/page.tsx:6770-6772` and appearing
**only** inside the Validation Vault shards table (the readiness shard rows carry no universe id,
and the universes list is empty). The new assertion is strictly more discriminating than the one it
replaces: it proves the vault section rendered a real row, where the old one only proved it
rendered an empty state.

I deliberately did **not** take the alternative fix of pointing the seed at a private vault
directory to keep the desk section empty — that would have persisted a graduation row referencing a
shard the product's own vault has no record of, i.e. a fixture that could never arise in reality.

Re-verified after the fix (see §4 for the full evidence chain): lint `J-08 ok / J-10 ok`, then
`--journeys J-01,J-02,J-03,J-04,J-05,J-06,J-08,J-10` → `8 journey(s), 0 failed (verdict: PASS)`.

**B2 — IMPORTANT (gap, not fixed): condition 3's economic floor is still caller-supplied — the same
defect class TR-30 just closed for condition 1.**

`micro_sealed_evaluation.py:316` reads `econ_floor = candidate_spec.get("econ_floor")` and
lines 254-258 gate on `abs(summary["effect"]) >= econ_floor["floor_bps"]`. Nothing verifies that
this floor is the family's *pre-registered* floor, nor that it equals the one the walk-forward
applied — which is what spec §8.1 condition 3 requires ("the family's own pre-registered economic
floor (§5.5) — the same floor the walk-forward applied, not a new one"). Condition 5 has the same
shape: `evidence_class`/`process_label` are read straight off the caller's spec
(`micro_sealed_evaluation.py:407-408`) rather than derived from the exposure registry per §6.7/§6.8.

Proven by execution — two runs differing ONLY in the caller-supplied floor, same 30 observations
with a ~0.001 bps effect:

```
econ_floor={'floor_bps': 5.0} -> verdict=fail   effect=0.0010145 failure_reason=below_economic_floor
econ_floor={'floor_bps': 0.0} -> verdict=pass   effect=0.0010145 failure_reason=None
```

That is a permanent `"pass"` certificate manufactured from a caller-chosen gate — structurally the
same exploit the iteration-17 audit found on condition 1, one condition over.

**Not fixed, deliberately.** Spec revision r9 explicitly rules `econ_floor` out of this round
("unaffected by r9 … stays exactly as it was"), and closing it properly requires the
candidate-registration ledger this codebase still does not have (disclosed across several
iterations and in the dev handoff's own Known Issues). Fixing it here would be scope creep and
would pre-empt an owner ruling. It is real, it is live, and it should be the next TR row.

Mitigating context, stated honestly: there are zero production callers — I confirmed the real store
serves `{"families": [], "message": "No candidates ledgered.", …}` and has no
`apps/backend/.data/micro_graduation` directory at all.

**B3 — OBSERVATION: the override refusal is keyed on the literal `"floors"` name.**

`micro_sealed_evaluation.py:332` refuses on `if "floors" in candidate_spec`. Spec §8.1 condition 1
asks for refusal of "floors, altered thresholds, or any equivalent override". Per-field aliases are
not refused — they are simply never read. I probed nine plausible alias shapes
(`wf_fold_min_observations`, `min_observations`, `sealed_min_observations`,
`SEALED_MIN_OBSERVATIONS`, `floors_applied`, `sufficiency_floors`, `thresholds`,
`wf_fold_min_signal_sessions`, `n_min`), each with exactly 1 observation; every one returned
`verdict=insufficient n=1` with `floors_applied={'min_observations': 30, 'min_signal_sessions':
'not_applicable_single_shard', 'min_symbols': 'not_applicable_single_shard'}`. So the *equivalence*
the spec asks for is achieved by the absence of any read path rather than by an explicit refusal.
That is defensible (refusing every unknown key would be over-strict), but it means the guarantee
rests on "nothing reads it" rather than on a check — worth knowing if a future iteration adds a new
spec-driven parameter.

**B4 — OBSERVATION: the seed script's docstring overstates its own scoping.**

`seed_micro_graduation_iter18_fixture.py:39-41` states "this script contains no fallback to an
unscoped default path", but line 192 falls back to `Path.cwd()` when no root argument is given, and
line 118 derives `root / "datasets"` rather than honouring the `TAPEOLOGY_DATASET_DIR` the wrapper
exports. Both are harmless as wired (the rig always passes `$ROOT`, and
`qa_playbook_iter7_fixture_scoped_backend.sh` sets `DATASET_DIR="$ROOT/datasets"`, so the two agree
exactly), and I verified the real store is untouched. But the docstring claim is not accurate as
written, and a future caller that exports a scoped `TAPEOLOGY_DATASET_DIR` while passing a
different root would seed a directory the backend never reads.

### Frontend Findings

None. No `apps/frontend/**` file changed this iteration (`git status` confirms), and the replay
lane exercised `/`, `/structure` and all eight `/desk` sections end to end after the B1 fix.

### Test Findings

**T1 — OBSERVATION: `SEALED_MIN_OBSERVATIONS` numerically coincides with `WF_FOLD_MIN_OBSERVATIONS`.**

Both are `30` (`micro_sealed_evaluation.py:131`, `walkforward.py:168`), so an assertion of the form
`row["n"] == 30` alone cannot distinguish "the sealed constant was applied" from "the walk-forward
default leaked through" — exactly the coincidence iteration-16's lesson warns about. It is not a
live defect: the value is spec-pinned at 30 (§1), `sealed_pass_parameters()` no longer imports the
WF names at all (`micro_sealed_evaluation.py:185-193`), and deleting `_sealed_floors()` would make
`summarize_fold_observations` fall back to `min_signal_sessions=8`/`min_symbols=2`, which the
single-session 30-observation fixture would fail — so TC-3 would catch it. Recording it so the
coincidence is a known, checked one rather than an unnoticed one.

**T2 — the TR-30 test block is tight, not loose.** `tests/test_micro_sealed_evaluation.py:651-881`.
Every assertion is an exact value, not a range or an `in` check: TC-4 asserts the literal string
AND `!= 1` AND `not isinstance(..., int)` on both breadth fields *and* that the informational
`n_sessions`/`n_symbols` stay real integers; TC-5 asserts the ledger is still empty after BOTH
refused attempts, so neither floor value reached a verdict; TC-6 chains
`row["rule_hash"] == sealed_pass_rule_hash()` with `row["n"] == SEALED_MIN_OBSERVATIONS == 30`;
TC-7 asserts `len(persisted) == 1` and that the surviving verdict is still `insufficient`. The
mutation-proof (`:846`) asserts the retired symbol is absent (`not hasattr(..., "_resolved_floors")`),
that the replacement's signature has zero parameters, and that the old call shape raises
`TypeError` — structural, not behavioural. The PASS-path fixtures were genuinely rewritten to 30
real observation dicts with deliberately different values (`:64-89`), not patched; `_TINY_FLOORS`
survives only as a sentence in the module docstring.

---

## 3. Domain Assessment

The scientific core is correct and, more importantly, correct for the right reason.

Condition 1 now reads `summary["status"] == wf.FOLD_STATUS_SUFFICIENT`
(`micro_sealed_evaluation.py:248`) against a floors dict that no caller can reach:
`_sealed_floors()` (`:221-234`) takes no parameters and pins
`wf_fold_min_observations=SEALED_MIN_OBSERVATIONS` with the two breadth floors at `0`, so
`walkforward.summarize_fold_observations` (`walkforward.py:399-409`, `n < min_observations`) gates
on observation count alone — 29 → `insufficient`, 30 → `sufficient`. The breadth floors sit at `0`
rather than being removed, which is the honest encoding of "structurally inapplicable at shard
scope" given that function's shared signature, and the artifact never records that `0`: it records
the literal `"not_applicable_single_shard"` (`:433-437`), while the *informational*
`n_sessions`/`n_symbols` counts stay separately as real integers (`:426-427`). That split is
exactly what §8.1 asks for and it is the one place a lazy implementation would have written a
silent `1`.

The rule hash is now computed from the rule that actually executes: `sealed_pass_parameters()`
(`:185-193`) embeds `SEALED_MIN_OBSERVATIONS` and the breadth policy and has dropped
`wf.WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_SYMBOLS` entirely, so the iteration-17 pathology — a
`rule_hash` certifying 30/8/2 over a run that applied 1/1/1 — cannot recur even in principle. I
confirmed the served artifact, the on-disk ledger row and a freshly-computed
`sealed_pass_rule_hash()` all agree byte-for-byte on
`8aaea80b53c56805a396a3f8456ae79702e6527b8b4c9aeb5f009a54ff58d115`.

Single-shot semantics are intact and, if anything, stricter than needed: `record_sealed_evaluation`
(`micro_graduation.py:381-400`) refuses any second evaluation whose artifact content differs and
replays a byte-identical one; because `evaluated_at` defaults to wall-clock, a genuine second draw
is refused in every realistic case. A refusal correctly does **not** consume the shot (nothing is
persisted — TC-1 and TC-5 both assert the empty ledger afterwards), and an `insufficient` verdict
correctly **does** (TC-7).

The one thing I want on the record: the module is now airtight about *who owns the sufficiency
floor* and still permissive about *who supplies the economic floor and the evidence class*
(finding B2). The owner's ruling was that "the evaluator's authority must be fixed before any
sealed graduation is allowed"; this iteration fixed one third of that authority. That is the right
third to fix first, and it is fixed properly — but the sentence is not yet fully true.

### DEFINITION OF DONE — item by item

| # | Item | Verdict | Basis |
|---|------|---------|-------|
| 1 | TR-30's seven trap assertions implemented and green | ✅ | Full trace. All seven spec §9 clauses map 1:1 to `test_tr30_tc1`…`tc7` (`tests/test_micro_sealed_evaluation.py:651-838`) plus the mutation-proof (`:846`); re-run green in my own full-suite run, and independently re-proved by my nine-alias adversarial probe. |
| 2 | Trap suite reaches 30/30 (TR-1…TR-30) | ✅ | My own sweep of test-id markers across `apps/backend/tests/`. All 30 present; TR-17 appears as TR-17a/b/c (`test_micro_observer.py:6,649`, `test_micro_features.py:225`), which a naive `TR-17\b` grep misses — flagging so the evaluator's own sweep does not false-negative. |
| 3 | B3 and B4 fixtures land and pass | ✅ | Mechanical, verified twice — accepted with citation: reviewer PASS ("B3/B4 coverage-gap fixtures confirmed present and passing", `issues: []`) + QA rows (`test_micro_accessor.py` 20/20, `test_micro_observer.py` 38/38). Both modules were also inside my own clean full-suite run. Correctly identified by dev as already-landed in iter-17's pass rather than duplicated. |
| 4 | QA seeding fixture makes `GET …/graduation` return a non-empty discriminating body; J-07 re-verified via browser-qa-agent | ⚠️ → ✅ | **The browser-qa-agent lane never ran** (finding P1). I executed it: Playwright navigated to `http://localhost:8302/research/desk/micro/graduation` on the real rig, HTTP 200, `families` length 1, `verdict=pass n=30 rule_hash=8aaea80b… floors_applied={min_observations:30, min_signal_sessions:"not_applicable_single_shard", min_symbols:"not_applicable_single_shard"} row_hash=796eff5a…` — **byte-identical to the on-disk ledger row**. Screenshot: `reports/qa/goal-rapid-microscope-iter-18-evidence/J-07-graduation-seeded.png`. |
| 5 | J-10 re-verified via browser-qa-agent (kept-product sentinel) | ⚠️ → ✅ | Lane never ran, and J-10 was **actually broken** (B1). After the fix, full 15-step replay PASS across `/`, `/structure` and all eight `/desk` sections including the three Referee sections. Evidence: `…-evidence/J-10-verify.png`. |
| 6 | Required-still-passing journeys (J-01…J-05, J-08) remain green | ⚠️ → ✅ | Lane never ran, and **J-08 was failing** (B1). After the fix: `8 journey(s), 0 failed` across J-01…J-06, J-08, J-10. Evidence: `…-evidence/auditor-regression-replay-results.md` + per-journey PNGs. |
| 7 | No anti-goal violation; iteration-17's Hold-out-only-promotion open item CLOSED | ⚠️ partial | The **condition-1 half is genuinely closed** — proven, not asserted (nine-alias probe, all `insufficient`). The same exploit shape survives on condition 3 (finding B2), so "the caller-floor override no longer exists to exploit" is true of sufficiency floors and not yet true of the economic floor. |
| 8 | Suite: 0 failures, ≥3,263 passed, exactly 8 skipped, fingerprint `08e471b10130e1e2`, referee files byte-identical | ✅ | My own run, not the handoff's: `.venv/bin/python -m pytest tests/ -q -p no:randomly` → exit 0, progress-marker census **3271 `.` / 8 `s` / 0 `F` / 0 `E` / 0 `x`**. `Config().config_fingerprint()` → `08e471b10130e1e2`. `git diff HEAD -- 'apps/backend/app/research/referee_*.py'` → empty. |
| 9 | `blueprint.md` carries the in-place iter-18 note | ✅ | Present at the tail of `runs/goal-session-rapid-microscope/state/blueprint.md`; I read it against the shipped code — constant name, refusal behaviour, literal breadth string, unchanged endpoint/owner/rule-name/version all match what actually shipped. No row shape or ownership change. |
| 10 | Dev handoff written | ✅ | `docs/handoffs/goal-rapid-microscope-iter-18-dev.md`, complete, and honest about its one plan deviation (no `J-07.json` golden script — a genuine, long-disclosed limitation of the replay runner's `normalize_url`, corroborated by `micro_routes.py`'s own docstring and `state/golden-gaps`). |

### P1 — IMPORTANT (process, remediated by this audit): three DoD items were reported complete with no execution behind them

The phase spec's metadata says `Frontend Present: no`, while the same spec's TESTING REQUIREMENTS
says "Browser: J-07 …, J-10 …" and its DEFINITION OF DONE names `browser-qa-agent` twice. The
pipeline resolved that contradiction by skipping: `status.json` records
`browser_checks_run: false`, the five UI-lane artifacts are one-line "N/A — Backend-only phase"
stubs, and the QA report states "Browser Checks **SKIPPED**" — yet still returns **PASS**, and the
review returns `definition_of_done: complete`. Iteration 17, whose spec said `Frontend Present:
yes`, ran 16 journeys with screenshots; iteration 18 ran none. That gap is what let B1 ship. The
spec's own NOTES asked the review/QA lanes to "explicitly name which store the browser run actually
used" — moot, because no browser run happened.

Remediated by this audit (the lanes were executed and their evidence persisted), but the
decomposer should set `Frontend Present: yes` whenever the DoD names `browser-qa-agent`, and QA
should not return PASS while a DoD item's verification lane is skipped.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `runs/goal-session-rapid-microscope/journey-scripts/J-08.json` | Step 5's Validation Vault assertion `"No shards recorded."` → `"iter18-qa-universe"`, the seeded shard's `universe_id`, copied verbatim from the endpoint's current rendering. The old string became dishonest the moment this iteration's seed put a real shard in the rig's vault. |
| 2 | Important | `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` | Same change at step 12, same reason. |

**Post-fix self-verification (evidence, in order):**

1. **Reproduced the failure first** — J-08 replay against the real rig: `1 journey(s), 1 failed`,
   `step 05 expected "No shards recorded." did not appear`.
2. **Schema lint after the edit** — `demo_runner.py --mode lint --journeys J-08,J-10` → `J-08 ok`,
   `J-10 ok` (a golden that fails lint is quarantined by the lane, so this had to be checked).
3. **Targeted re-run** — J-08 → `0 failed (verdict: PASS)`; J-10 → `0 failed (verdict: PASS)`,
   all 15 steps.
4. **No collateral damage** — full replay set `J-01,J-02,J-03,J-04,J-05,J-06,J-08,J-10` →
   `8 journey(s), 0 failed (verdict: PASS)`. Note J-06's `"No integrity errors."` assertion was a
   live risk (the seed adds a third dataset); I checked the readiness payload directly
   (`integrity_errors: []`, totals now 2 symbol-days / 3 datasets) and then confirmed by replay.
5. **Diff review** — `git diff runs/goal-session-rapid-microscope/journey-scripts/` is exactly two
   changed lines, one per file. Nothing else touched.
6. **Backend suite unaffected** — the fix touches only JSON outside `apps/backend`; suite census
   after the fix remains 3271 passed / 8 skipped / 0 failed.
7. **No new finding introduced** — the replacement assertion is strictly more discriminating than
   the one it replaces (it requires a rendered shard row, not merely a rendered empty state) and is
   stable across runs (`universe_id` is a fixed fixture literal; `dataset_id`/`shard_id` are not,
   which is why neither was used).
8. **Environment left clean** — the rig backend (:8302) and frontend (:3302) I started are stopped;
   both ports confirmed free. The real `apps/backend/.data` store was never written to (it still
   has no `micro_graduation` directory at all).

**Evidence persisted at** `reports/qa/goal-rapid-microscope-iter-18-evidence/`:
`auditor-regression-replay-results.md`, `J-01`…`J-06`/`J-08`/`J-10-verify.png`,
`J-07-graduation-seeded.png`.

I did **not** overwrite `reports/phase-goal-rapid-microscope-iter-18-ui-test-results.md`. It
accurately records that the browser-QA lane was skipped; my results are auditor evidence and are
labelled as such rather than backfilled into another lane's artifact. **The goal-evaluator should
read the evidence directory above, not the "SKIPPED" stub, when judging J-07 and J-10.**

---

## 5. Recommended Next Step

**Proceed.** The iteration's one risky change landed correctly and its four passengers are all
genuinely done. Two things should follow it, in this order:

1. **Fix the lane contradiction before the next iteration is planned.** Set `Frontend Present: yes`
   in any spec whose DEFINITION OF DONE names `browser-qa-agent`, or teach the QA lane to refuse
   PASS when a DoD verification lane is skipped. This iteration's only real regression was caught
   by the auditor rather than by the two lanes built to catch it, and that is the second-order
   lesson worth more than the fix itself: *a change to a shared QA fixture is a change to every
   journey that rig serves* — when a seed writes into the browser rig, re-run the replay set before
   calling the round done.

2. **TR-31 — finish the evaluator's authority (finding B2), before J-09.** The standing instruction
   makes J-09 "the pilot studies" the natural next subject, and TR-30 was named as its one blocking
   safety test. I would not start J-09 yet: the audit found that the *identical* exploit the owner
   ruled must be fixed "before any sealed graduation is allowed" is still live one condition over —
   a caller-supplied `econ_floor.floor_bps = 0.0` turns a 0.001 bps effect into a permanent
   `"pass"`, demonstrated above. Condition 5 (`evidence_class`/`process_label`) is caller-asserted
   in the same way. Closing this needs an owner ruling on where a candidate's pre-registered floor
   and evidence class actually come from — which is the candidate-registration ledger this codebase
   has deferred since iteration 12. That is a genuine decision, not an implementation detail, so it
   belongs to the owner rather than to a decomposer's next round.

Findings B3, B4 and T1 are OBSERVATION-level and should be left alone — they are recorded here so
they are known, not so they are worked on.
