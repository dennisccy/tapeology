# goal-rapid-microscope-iter-16 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The round's goal is achieved: TR-3, TR-22 and TR-26 land as explicitly-labeled trap-suite entries,
the trap inventory is genuinely 27 of 29 (verified by my own label sweep off disk, not from any
handoff), TR-26's production fix is correct and correctly scoped, and all three passengers landed.
I did not take the dev's or the reviewer's non-vacuity claims on trust: I mutated production source
myself in **twelve** distinct shapes — nine of which neither lane tried — and recorded which tests
caught each. Nine were caught. **Three escaped**, one of them inside TR-26's own specified contract:
the fixture cannot distinguish "the magnitude is measured over the pre-change run" from "the
revealing quote's size was folded in", because that quote happens to carry the same size the run
already held. I fixed that one with a discriminating test and re-ran the mutation to prove the hole
is closed (10 of 12 now caught; the two that still escape are documented GAPs, both in the
fail-safe direction and both outside this round's stated acceptance).

Separately, the target journey's own stored golden replay script was overwritten this round
with a version that was **linted but never executed**, and which silently dropped two data-bearing
Playbook Evidence assertions that iteration 15's version asserted and passed — that one I could not
fix with evidence (both services are down and this sandbox blocks the process control needed to
stand a rig up safely), so it is reported unresolved rather than blind-edited.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): TR-26's own "the magnitude stays unaffected" clause was not provable on
the fixture it is asserted against — a mutation that corrupts the magnitude passed the entire file**

`apps/backend/tests/test_micro_observer.py:268-275` (`_depletion_events()`) ends the ask run at
100.10 with `current_size = 300`, and its revealing (price-changing) quote at `ts=3.0` carries ask
size **300 as well**. The spec's DEFINITION OF DONE for TR-26 requires that "the depletion MAGNITUDE
stays computed from the pre-change run data, unaffected"; TC-9 asserts that as `value == 200.0`
(`test_micro_observer.py:302`). On this fixture that assertion holds under **both** the correct rule
and the corrupt one, because `500 − 300 = 200` either way.

I proved this rather than argued it. Mutating `micro_observer.py:646` to fold the revealing quote's
own size into the run before resolving —

```python
                run["observed_through"] = ts
                run["current_size"] = size          # AUDIT MUTATION
                self._resolve_depletion(side, run)
```

— left the **entire file green**: `tests=35 failures=0 errors=0` (junit XML, mutation `M2`). Nothing
in the suite guards the invariant the round's own DoD names. That is precisely the iteration-15
lesson this round was written to obey ("a trap that only shows green today is not done"), applied to
a clause the round claims to have proven.

**Fix applied** (`tests/test_micro_observer.py`, additive only, no production change): a new fixture
`_depletion_events_with_a_differently_sized_revealing_quote()` whose revealing quote carries ask
size **900**, plus
`test_tr26_the_magnitude_is_measured_over_the_pre_change_run_never_the_revealing_quotes_own_size`.
Under the correct rule the magnitude is `500 − 300 = 200`; folding the revealing quote in would make
it `500 − 900 = −400`, a nonsensical negative depletion. The test also re-asserts the r6 stamp
(`observed_through == available_at == 3.0`) on the same run, so one fixture now proves both halves
of the ruling.

**Post-fix verification (commands and results):**
- `.venv/bin/python -m pytest tests/test_micro_observer.py --junitxml=…` → `tests=36 failures=0
  errors=0`.
- Mutation `M2` re-run with the new test present → `tests=36 failures=1`, failing exactly
  `test_tr26_the_magnitude_is_measured_over_the_pre_change_run_never_the_revealing_quotes_own_size`.
  The hole is closed and the closure is itself non-vacuous.
- Full backend suite re-run: see §2 "Test Findings" T0 and §4.
- `git diff` self-review: +36 lines, one fixture + one test, no production file touched, nothing
  else changed.

**B2 — GAP (documented): TR-3's origin fence has no production caller at all, and
`micro_accessor.py`'s own module docstring describes a walk-forward fenced-read path that does not
exist**

Verified independently, not taken from the handoff: `grep -rn "MicroAccessor" --include=*.py` over
the whole repo outside `tests/` returns exactly two construction sites, `micro_join.py:434` and
`scout.py:353`, and both pass three positional arguments — `origin` defaults to `None`
(`micro_accessor.py:212`). `walkforward.py` imports only `ExposureRegistry`,
`has_any_exposure_entries`, `initialize_r2_exposure_registry`, `resolve_micro_exposure_registry_dir`
(`walkforward.py:65-70`); it never constructs a `MicroAccessor`.

Consequence: the origin fence (`micro_accessor.py:249-256`) and the exposure-logging-on-read branch
(`:257-263`) are both **latent** — correct, fail-closed, well-tested machinery that no production
path currently enters. The unfenced mode is honestly disclosed at both call sites and in the module
docstring, so this is not concealment. But the same docstring states, at `micro_accessor.py:34-37`,
that "Only `walkforward.py`'s OWN origin-fenced reads (an `origin` given, an `ExposureRegistry`
given) participate in exposure logging — the one path where 'was this window ever served before?' is
an actual, load-bearing question this era asks." **No such read exists.** The sentence is true only
vacuously and reads as a description of live behaviour.

My judgement on the question this raises: a fence with no caller is not protection, it is a
*prepared* protection. It has real value — the discipline is built, typed, boundary-exact and
mutation-proven before the vault work that needs it (J-06/J-09) wires it up — and TR-3's third
clause, the import-ban, *does* guard a live invariant today. But the round's own labelling should
not let a later reader infer that production reads are chronologically fenced. They are not.
`micro_accessor.py` is explicitly frozen this round (spec IN SCOPE: "no production edits to either"),
so I did not touch the docstring. Next round should correct that sentence, or wire an actual
`origin=` consumer.

**B3 — GAP (documented): TR-22's `is_exposed_before` strict-`<` boundary is unproven; only the
"always False" shape is guarded**

`micro_accessor.py:164` implements "strictly before" as `row.get("logged_at") < instant`. I mutated
it to `<=` and ran the whole TR-3/TR-22/TC-13/TC-14 selection: `tests=8 failures=0` — **no test
caught it**. The spec's own TC-8 only asks for the always-`False` mutation, which the dev
implemented faithfully and which I confirmed *is* caught (3 tests fail, below), so this is a gap in
the spec's test design rather than a dev deviation. It is also in the **fail-safe** direction: `<=`
classes more evidence as `historical_exposed_diagnostic`, never the reverse, so it cannot promote
genuinely-exposed evidence to fake out-of-sample — which is the leak TR-22 exists to stop. Recorded,
not fixed (out of the round's stated acceptance).

**B4 — GAP (documented): `finalize()`'s session-truncated availability stamp is untested for
discrimination — both depletion fixtures hide it behind a timestamp coincidence**

`micro_observer.py:754` stamps a session-cut-short run at `unavailable_at=ts` where `ts =
self._last_event_ts` (correct: an unavailable construct becomes known at session end). I mutated it
to `unavailable_at=run["observed_through"]` — the same class of "one event early" bug TR-26 just
fixed on the resolved path — and the file stayed green: `tests=35 failures=0`. Both fixtures that
reach this path end on a **quote**, so `_last_event_ts` and `run["observed_through"]` are the same
number (`_depletion_events()` truncated to `< 3.0` → both `2.0`; `_unfinished_depletion_events()` →
both `2.0`). A fixture ending on a trade *after* the last quote would separate them. Pre-existing,
outside TR-26's three specified clauses (the spec's TR-26 row governs the two termination paths and
the truncation boundary, not the unavailable stamp), so documented rather than fixed.

**B5 — OBSERVATION: the shipped TR-3 mutation-proof mutates the fence's date resolver, not the
comparison the spec names — I closed that gap directly**

Spec TC-4 asks for "the origin-fence comparison in `MicroAccessor.read_snapshot_rows` … temporarily
weakened so it never refuses". `test_micro_accessor.py:131-160` instead monkeypatches
`ma._session_date_for_dataset` to return `"2000-01-01"`. That defeats the fence and satisfies the
acceptance text's *effect*, and the test carries a real un-mutated sanity check first, so it is
sound. It simply does not exercise the comparison operator itself. I mutated the comparison in the
real file, three ways, and every one was caught — see the mutation table in §3.

**B6 — OBSERVATION: TC-10's bound assertion is written against the window constant, which coincides
with the bound-hitting quote's timestamp**

`test_micro_observer.py:458` asserts `available_at == observed_through ==
float(mf.DEPLETION_WINDOW_QUOTES)`. The fixture emits quote `i` at `ts = float(i)`, so the 20th
quote's instant is 20.0 and the window bound is also 20 — the assertion cannot distinguish "stamped
at the bound-hitting quote's ts" from "stamped with the update count". The realistic defect shapes
are still caught (my mutation `M3`, stamping `run_start_ts` in that branch, fails exactly this
test), so this is a readability note, not a hole.

### Frontend Findings

**F1 — IMPORTANT (gap — unresolved, could not be fixed with evidence): J-10's golden replay script
was overwritten this round, never executed, and silently lost two data-bearing assertions**

`runs/goal-session-rapid-microscope/journey-scripts/J-10.json` is modified in the working tree. It
is **not** in `runs/goal-rapid-microscope-iter-16/status.json`'s `changed_files`, so the reviewer's
"exactly the 6 files touched" and QA's "Changed files: Exactly 6 files changed — PASS" are both
counting one tracked, behaviour-bearing artifact short. What changed (`git diff HEAD`):

- Steps 9 and 10 — expand `desk-section-expand-playbookEvidence` expecting `"Built from
  signature:"`, and fill `desk-playbook-date-input` with `2026-06-22` expecting `"recorded signals,
  none hidden"` — were **deleted**. Both were data-bearing assertions over real playbook evidence.
  They were replaced by four empty-state assertions (`"No candidates ledgered."`, `"No fold specs
  registered."`, `"No shards recorded."`, `"Distinct symbol-days"`), which assert absence.
- `default_timeout_ms` 10000 → 20000; the `/structure` as-of 17:00:00 → 16:00:00.

Two things make this matter rather than being routine script maintenance:

1. **It was never run.** The browser-QA report states it plainly
   (`…ui-test-results.llm.md:116`): "Linted clean: `demo_runner.py --mode lint …` → `J-10 ok`".
   A lint validates schema, not that a single step passes. This era's own standing rule is "no
   screenshot ⇒ `unknown`, never `passing`" (plan.md:197); by the same standard an unexecuted
   golden script's status is `unknown`.
2. **The previous version had been executed and had passed.**
   `reports/phase-goal-rapid-microscope-iter-15-regression-replay-results.md` records `UT-J-10 … PASS
   … J-10-verify.png` one round ago. This round's replay table
   (`…-regression-replay-results.md`) contains **no J-10 row at all** — J-08 took its slot. So in the
   very round where J-10 is the *target* journey, its deterministic lane went from "executed and
   green" to "replaced and unrun".

Mitigations I verified myself, which are why this is not a FAIL:
- Every `expect` string in the new script exists in the shipped frontend source, and every `testid`
  it targets resolves (`desk-section-expand-{microReadiness,scoutLedger,walkForward,validationVault,
  refereeRegistry,refereeAdjudications,refereeRuns}`, `structure-as-of-input`,
  `structure-load-button`) — the script is not structurally broken.
- Every one of those strings was independently confirmed **live** this round by the LLM browser lane
  (UT-02, UT-03, UT-06, UT-07, UT-08, UT-09) with screenshots on record, including the
  `300.11–302.2` band at the new 16:00:00 as-of (UT-09) and `config fingerprint 08e471b10130e1e2`.
  So J-10's sentinel *is* verified this round; it is the stored asset, not this round's evidence,
  that regressed.
- Both deleted assertions' target strings still exist in `page.tsx`, so they were not obsoleted by a
  UI change — they were dropped.

I did not fix this. Restoring the two steps would mean shipping assertions I cannot execute (both
`:8301` and `:3301` are down — `curl` returns `000` — and this sandbox blocks the process control
needed to stand up and then cleanly retire a rig), and an unverified assertion is exactly what this
finding is about. Recommendation in §5.

**F2 — GAP (closed by trace, not by a live render): TC-14 was never verified against a rendered
DOM**

QA's UT-04 is a **SKIP** with a source-level substitute (`…-ui-test-results.md:27`), and the plan's
own scenario ("seed a sparse/malformed trial row via `ScoutLedger.append_row` into an ISOLATED
fixture store … confirm only that row/cell degrades", plan.md:174-178) was not executed by any lane.
The dev proved the malformed shape *reachable* through the backend contract but did not render it.

I therefore traced every read in the trial row (`page.tsx:6312-6344`) against the dev's own
proven-reachable sparse row (`family_id`, `family_root_id`, `candidate_id`, `decision`, `reason`
only) and confirm the claim holds by construction:

| read | behaviour on a missing field |
|---|---|
| `trial.candidate_id`, `trial.decision`, `trial.withheld_excluded` | bare render of `undefined` — React renders nothing |
| `trial.feature?.name ?? "—"` / `.transform`, `trial.outcome?.horizon_key ?? "—"` | the fix — `"—"` |
| `formatDateTimeET(trial.registered_at, …)` | `lib/datetime.ts:100-101` → `new Date(undefined)` is `Invalid Date` → returns `"—"`; does **not** throw |
| `trial.reason ?? "—"`, `trial.notes ?? "—"` | `"—"` |
| `JSON.stringify(trial.screen_result, null, 2)` | `undefined` — React renders nothing |
| `family.trials.map(…)` | `scout.py:1299` always sets `"trials": family_rows` (a list) — never undefined |

No remaining throw path for a missing-field row. TC-14 is met; only its live-DOM confirmation is
outstanding.

**F3 — GAP (spec-accepted): `/desk` still has zero error boundaries, and ~7 other sections keep the
pattern that caused iteration 15's COHERENCE-WARN**

`grep -c "ErrorBoundary\|componentDidCatch\|getDerivedStateFromError" page.tsx` = 0; a page-wide
boundary is explicitly OUT OF SCOPE this round, so this is accepted, not a defect. Worth recording
for the next round: `MicroReadinessSection` and `ValidationVaultSection` are now the only two of the
thirteen section components that carry their `*-section` testid in **all** render states. Seven
others own a `*-section` testid and still return an unwrapped `<LoadingPanel …/>` early —
`referee-registry-section` (`page.tsx:4759`), `referee-evidence-section` (`:5037`),
`referee-adjudications-section` (`:5318`), `desk-evidence-section` (`:4699`), `desk-forward-section`
(`:3137`), `desk-screen-compare-section` (`:3421`), `desk-playbook-section` (`:9211`). The same
coherence warning can fire against any of them.

### Test Findings

**T0 — verification of the round's own headline numbers (my own independent run)**

I ran the full backend suite myself, after my B1 fix, reading `--junitxml` rather than stdout (the
known miscount trap): `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=… -q` →
**3246 collected / 3238 passed / 8 skipped / 0 failed / 0 errors**, exit 0, 622.1s. That is the
round's verified 3245/3237/8/0/0 plus exactly the one test I added. The dev's open transient
hypothesis (`test_micro_join.py::test_tc4_…`, `test_micro_snapshots.py::test_tc12_…`) did **not**
reproduce — this is now the fifth consecutive clean full run; I agree with the reviewer that it
stays formally open but weakly supported.

Independently re-verified frozen rails (not cited from any handoff): `Config().config_fingerprint()`
→ `08e471b10130e1e2`; the six `referee_*.py` + `micro_chain_ledger.py` SHA-256s match the
iteration-0 baseline byte-for-byte; MCP tool count = **26** (`grep -oP 'name="\K[a-z_]+'
app/mcp/__init__.py | sort -u | wc -l`). `tsc --noEmit` accepted on the reviewer's PASS plus QA's
executed row — my own change is Python-only and cannot affect it.

**T1 — OBSERVATION: two artifacts disagree about J-07; the evidence settles it as verified**

`reports/phase-goal-rapid-microscope-iter-16-ui-test-results.md:56` lists `UT-J-07 … DEFERRED-BUDGET
… not run this iteration`, while `…ui-test-results.llm.md:118-120` records J-07 **PASS** with
evidence. I opened the evidence
(`reports/qa/goal-rapid-microscope-iter-16-evidence/J-07-verify.png`) and it shows the graduation
endpoint's real body: `{"families":[],"message":"No candidates ledgered.","chain_verification":
{"ok":true,"failed_at_row":null,"reason":null}}`. J-07 **is** verified; the merged table's
DEFERRED row is the golden-replay lane reporting on a journey that has no golden script by design.
A downstream evaluator reading only the merged table would wrongly conclude J-07 went unchecked.

**T2 — OBSERVATION: four of the six replay evidence screenshots are byte-identical**

`md5sum` over the evidence directory: `J-02-verify.png`, `J-03-verify.png`, `J-04-verify.png` and
`J-05-verify.png` are all `6f962d465a47ffc233a822e77e36f605`, and `UT-09-result.png` ==
`UT-10-result.png`. I opened one — it is the `/desk` page top, the shared final state those journeys
land on. The PASS gate is the runner's per-step `expect` assertions, not the image, so the verdicts
stand; but the screenshots are not per-journey evidence and should not be read as such.

**T3 — OBSERVATION: one demo caption overstates what was demonstrated**

`reports/phase-goal-rapid-microscope-iter-16-demo-results.md:13` titles step 03 "Expand Scout
Ledger—shows defensive degradation". The Scout Ledger on this store is empty ("No candidates
ledgered." — UT-03), so no row degraded and nothing about the defensive read was demonstrated.
Showcase-only, non-blocking.

---

## 3. Domain Assessment

**TR-26's production fix is correct, minimal, and correctly bounded.** I read
`_advance_depletion_run`/`_resolve_depletion`/`finalize()` in full rather than trusting the handoff:

- The one added line (`micro_observer.py:646`) mutates the **outgoing** run dict immediately before
  `_resolve_depletion`, and that dict is then discarded (`self._depletion_run[side]` is rebuilt at
  `:648`) — no aliasing, no leak into the successor run.
- The magnitude (`:693`) reads `start_size`/`current_size` from the pre-change run; the revealing
  quote's size is never written into it. Correct — and, after B1, now provably so.
- **No new lookahead in either direction.** `ts` is the timestamp of the event currently being
  processed, and event timestamps are non-decreasing, so the stamp can only move later or stay
  equal — it can never land *earlier* than the revealing quote, which the DoD explicitly demanded.
  The opposite direction is guarded too: mutating `"available_at": observed_through` to
  `observed_through + 1.0` fails 9 tests, including `test_tr17a_deferred_completions_available_at_
  equals_observed_through`.
- The bound-termination branch (`:657-662`) is untouched and still stamps the bound-hitting quote,
  because `run["observed_through"] = ts` at `:659` precedes the bound check. `finalize()`'s
  session-truncated path (`:750-755`) is untouched and still stamps session end.
- The second corrected assertion (`test_tc7_tr18_…`) is legitimate, not collateral: it reads the
  same timing fact from the same fixture through the unit-refusal path, and it is one of the four
  tests that fail when the fix is reverted.

**The complete mutation table.** Every mutation was applied to real production source, run, then
restored; `sha256sum` confirmed byte-identical restoration of `micro_observer.py`,
`micro_accessor.py` and `walkforward.py` after every batch.

| # | Mutation (file) | Caught by |
|---|---|---|
| M1 | drop `run["observed_through"] = ts` — revert TR-26 (`micro_observer.py:646`) | **4** — `test_tc10_quote_depletion_resolves_at_a_price_change…`, `test_tc7_tr18_…`, `test_tc11_truncating_at_the_revealing_quote…`, `test_tc12_tr26_…` (reproduces the dev's RED transcript and the reviewer's report exactly) |
| M2 | fold the revealing quote's size into the run before resolving | **0 → 1 after my fix** (finding B1) |
| M3 | bound branch stamps `run_start_ts` (`:660`) | **1** — `test_tc10_bound_terminated_depletion…` |
| M4 | `finalize()` stamps `run["observed_through"]` instead of session end (`:754`) | **0** (finding B4) |
| M5 | `"available_at": observed_through + 1.0` (`:702`) | **9**, incl. `test_tr17a_…` |
| A1 | origin fence never refuses — `if False:` (`micro_accessor.py:251`) | **2** in `test_micro_accessor.py` + **1** in `test_walkforward.py` (the NEW aggregate test) |
| A2 | fence off-by-one — `>` → `>=` | **1** (`test_tc1_origin_equal_…_fence_is_inclusive`) + **1** (the NEW aggregate test) |
| A3 | fence returns `[]` instead of raising the typed error | **2**, incl. `test_tc1_a_read_strictly_after_origin_raises_a_typed_error_never_empty` |
| B1' | `is_exposed_before`: `<` → `<=` (`micro_accessor.py:164`) | **0** (finding B3; fail-safe direction) |
| B2' | `is_exposed_before` always `False` | **3**, incl. `test_tr22_…` |
| B3' | `classify_evidence_class` always returns `historical_oos` (`walkforward.py:439`) | **2**, incl. `test_tr22_…` |
| G1 | delete the three iter-15 `_PRICE_ARITHMETIC_FIELDS` clauses | **1** — exactly the new counter-test |

Reading across it: **TR-3 is boundary-exact in both directions and the new aggregate test earns its
place** — it independently catches both the never-refuse defect and the off-by-one, which is the
iter-11 lesson satisfied rather than recited. **TR-22 guards a live production path** — I confirmed
`classify_evidence_class` is called at `walkforward.py:533` and `:596`, so unlike TR-3's fence it is
not latent. **Passenger 3's counter-test is genuinely bound to the clauses it names.** And TR-26's
non-vacuity claim is real: M1 reproduces the exact four failures both prior lanes reported.

**Trap inventory, counted off disk rather than accepted.** Sweeping every `TR-N` label in
`apps/backend/tests/` (with the `TR-17a/b/c` spelling normalised, the trap that has broken a naive
grep before) yields exactly **27 distinct traps**: TR-1 … TR-22, TR-25, TR-26, TR-27, TR-28, TR-29.
TR-23 and TR-24 are absent, as planned for round 17. J-10 correctly stays `partial`.

**Scope discipline held.** `git status` shows exactly the six product/test files the spec names, plus
the J-10 journey script (F1) and the engine's own append-only telemetry/trace files.
`vault.py`, `tick_recorder.py`, `micro_readiness.py`, `scout.py`, `scout_ledger.py`,
`walkforward_ledger.py`, `micro_routes.py`, `micro_chain_ledger.py`, every `referee_*.py` and
`config.py` are untouched — confirmed by `git status --porcelain` and, for the frozen rails, by
SHA-256. Nothing in the diff invents a rule the spec or an owner ruling does not state; the one
place the dev departed from the spec's literal wording (TR-3's TC-2 naming a walk-forward `origin=`
consumer that does not exist) was resolved in the execution plan **before** implementation and is
disclosed in three places — that is the T-1 discipline working, not an improvisation.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_micro_observer.py` | Added `_depletion_events_with_a_differently_sized_revealing_quote()` (revealing quote carries size 900, not the run's own 300) and `test_tr26_the_magnitude_is_measured_over_the_pre_change_run_never_the_revealing_quotes_own_size`, closing TR-26's untestable "magnitude unaffected" clause (B1). +36 lines, test-only, no production change. Verified: file 36/36 green; the previously-escaping mutation now fails exactly this test; full suite 3246/3238/8/0/0. |

No other file was modified by this audit. All mutation probes were restored and confirmed
byte-identical by `sha256sum` before this report was written. The dev handoff's claims remain
accurate except for its test-count figures, which this fix moves from `3245/3237` to `3246/3238`
(+1 collected, +1 passed, 0 failed).

---

## 5. Recommended Next Step

**Proceed to round 17 (TR-23 + TR-24).** This round's goal is met and the product is materially
stronger: one real trap-coverage hole was found and closed with proof, and nine of the eleven other
mutation shapes were confirmed caught (the two that escape are B3 and B4, both fail-safe and both
documented).

Carry three items into round 17 — none of them large enough to justify a round of their own:

1. **Re-run J-10's golden script and settle it (F1).** With a rig up, run
   `python3 scripts/automation/lib/demo_runner.py --mode verify --scripts-dir
   runs/goal-session-rapid-microscope/journey-scripts --journeys J-10` (the same invocation the
   browser lane used for `--mode lint`, one word changed). If it passes,
   restore the two deleted Playbook Evidence steps (`"Built from signature:"`, `"recorded signals,
   none hidden"`) and re-run — both target strings still exist in `page.tsx`, and iteration 15's
   executed replay proves they held one round ago. If they no longer hold, that is itself a finding
   about the playbook surface and should be recorded, not silently dropped. Until it has been
   executed once, J-10's stored golden is `unknown`, not `passing`. Also add journey scripts to
   `status.json`'s `changed_files` so a script edit cannot again pass under an "exactly N files"
   certification.
2. **Correct `micro_accessor.py:34-37` (B2)** — it describes a `walkforward.py` origin-fenced read
   path that does not exist — or wire the first real `origin=` consumer. Whichever, TR-3's fence
   should stop being described as live protection while it has no caller.
3. **Two cheap coverage additions (B3, B4):** a TR-22 case where an exposure is logged at exactly
   `registered_at` (pins the strict `<`), and a depletion fixture whose last event is a **trade**
   after the last quote (separates `finalize()`'s session-end stamp from the run's own
   `observed_through`). Both are single fixtures in files already in the trap suite.

J-09 and the pilot studies stay blocked as ruled; TR-22 landing this round clears their named
prerequisite but reopens nothing.
