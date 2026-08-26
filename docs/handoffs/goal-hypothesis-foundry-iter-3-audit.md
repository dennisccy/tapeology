# goal-hypothesis-foundry-iter-3 Audit Report

**Date:** 2026-08-27
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's substance is real: a new hermetic oracle module (564 lines as delivered) drives the genuine
production interpreter → family → ledger → runner path over one composite epoch containing all
seven outcome types at once, with exact-value assertions (state, kill reason, hash order,
denominator) and kill fixtures traced line-by-line back to already-proven `test_scout.py`
fixtures; both carried repairs (`run_one_candidate`'s already-terminal identity re-verification,
`SourceRecord.source_hash`/`alternatives`) are implemented correctly and are additive-only.
Two IMPORTANT completeness holes in the proof suite were found and fixed during this audit: the
"complete factory" epoch never once fed a **compiler-produced** `CandidateSpec` into the runner
(every fixture in every Foundry test file hand-builds `fc.CandidateSpec`), and TC-3's own
runner clause ("when the runner exhausts it… zero terminal rows") was never exercised. Remaining
items are documented GAPs, none of which compromise the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the "complete factory" oracle never exercised the compiler → runner seam**

The phase's headline claim (spec GOAL, and `state/blueprint.md:129-139`'s pre-authored iter-3
note) is that the composite epoch runs "through the real production compiler → interpreter →
family → freeze/ledger → runner path". It did not for any evaluable variant: TC-1's seven
`FROZEN_READY` variants are hand-built via the local helper `_spec()`
(`apps/backend/tests/test_foundry_hermetic_epoch.py:56`), and `fc.compile_sources` is called only
for the three **non-compiled** sources (`:393` TC-3) whose output is zero specs. A repo-wide check
confirmed the seam was untested anywhere: `compile_sources` appears only in
`test_foundry_compiler.py` and `test_foundry_hermetic_epoch.py`, and neither file passed its
output into `interpret_candidate`/`run_one_candidate`/`run_family` — every interpreter and runner
fixture in `test_foundry_interpreter.py` and `test_foundry_runner.py` hand-builds its spec too.
This is exactly the handoff J-06 depends on (11 real source records → compiled specs → the exhaust
runner), and it was the one cross-module interaction the iteration's own `full`-depth trigger
named that no module's own test covered.

*Fix applied:* new test
`test_compiled_candidate_specs_flow_from_the_real_compiler_into_the_real_runner`
(`apps/backend/tests/test_foundry_hermetic_epoch.py:343-386`): two sibling `SourceRecord`s sharing
one `foundry_family_key` are compiled by the real `fc.compile_sources` (COMPILED disposition, the
compiler derives `foundry_family_id`), the compiled specs are handed to the real `fr.run_family`,
and the terminal rows are asserted to carry the **compiler's own** frozen identities unchanged —
`candidate_spec_hash` (both, in order), `foundry_family_id`, `foundry_family_variant_count == 2`,
the deterministic `rule_id`, the `historical_exposed_diagnostic` evidence class — plus one
survivor / one `killed_null` outcome and a clean hash chain. Evidence:
`.venv/bin/python -m pytest tests/test_foundry_hermetic_epoch.py -v` → **10 passed in 0.80s**.

**B2 — IMPORTANT (fixed): TC-3's runner clause was unexercised**

TC-3 requires "when the runner **exhausts** it, then it reaches a valid terminal completion state
with **zero terminal rows** and an honest zero-candidate read-model summary, not an error". The
delivered test proved only the compiler (zero specs), the empty family registry, and
`fi.read_model` over zero anchors — `foundry_runner` and `foundry_ledger` were never touched, and
"zero terminal rows" was never asserted, so DoD item 1's "run through the real …ledger/runner
path" was not true for the all-blocked epoch.

*Fix applied:* `apps/backend/tests/test_foundry_hermetic_epoch.py:393` (now takes `tmp_path`) and
`:411-432` — the epoch is now actually exhausted through `fr.run_family` (over every family in the
manifest: none; and over a zero-eligible-variant family, asserting
`ff.eligible_variant_ordinals(...) == ()`), asserting an empty result list, `ledger.all_rows() ==
[]` (no intent row and no terminal row), and `ledger.verify_chain()["ok"] is True`. Same test-run
evidence as B1.

**B3 — GAP: `foundry_freeze.py` is not exercised by the "complete factory" suite at all**

The spec's IN SCOPE and the blueprint note both name "…family → **freeze**/ledger → runner", but
`apps/backend/tests/test_foundry_hermetic_epoch.py` never imports `foundry_freeze`. The root cause
is disclosed and pre-existing, not a regression: `foundry_runner.py:1-19`'s own docstring states
that `foundry_freeze.verify_freeze_set_unchanged` "is not yet called from here; that wiring is
real-epoch (J-06/J-07) territory", so the composite epoch **cannot** reach freeze through the
production path without inventing wiring that is explicitly out of scope. Freeze keeps its own
module-level coverage (`test_foundry_freeze.py`). Net effect: the composite oracle proves five of
the six named modules together; the freeze seam remains proven only in isolation. The blueprint's
iter-3 note and the dev handoff should not be read as evidence that freeze was exercised
end-to-end.

**B4 — GAP: the crash-resume path still verifies only `econ_floor_bps`, never `manifest_hash`**

The repair landed on the already-terminal fast path exactly as specified
(`foundry_runner.py:95-110`: terminal `manifest_hash` vs. the caller's, then the pinned intent
row's `econ_floor_bps`), and TC-9's two drift tests are real. Its sibling branch —
intent-row-exists-without-terminal, i.e. the actual mid-candidate crash path
(`foundry_runner.py:112-119`) — still checks `econ_floor_bps` only, even though intent rows carry
`manifest_hash` (`foundry_ledger.py:107-125`), so a resume under a drifted manifest re-executes
that candidate and appends a terminal row stamped with the NEW manifest while its own intent row
holds the OLD one. The exposure is narrow: on a drifted resume the runner halts at the first
already-terminal candidate, so this only bites when the crash happened on the epoch's very first
candidate. I was unsure between IMPORTANT and GAP and settled on GAP because (a) the phase spec
scoped TC-9 to the already-terminal path only, (b) `goal.md` TC-51 speaks only to the economic
floor, and (c) `goal.md` §8.5's full science-hash verification on every run/resume is the
explicitly-deferred J-06/J-07 wiring that will subsume it. Close it when that wiring lands.

**B5 — GAP: the "large-N **performance**" half of the checkpoint fixture was not delivered
(quantified here so it stops being an unknown)**

The spec asks for "a large-N synthetic **performance**/checkpoint fixture" per `goal.md`'s
Constraint "use large hermetic synthetic fixtures to prove performance/checkpoint behavior before
the real freeze". TC-6 (`:544`) is 20 candidates over 4 families and asserts nothing about cost.
The ledger access pattern underneath is quadratic: `HashChainedLedger.all_rows()` re-reads and
re-parses the whole JSONL file on every call (`micro_chain_ledger.py:116-139`) and `append_row`
does too (`:141`), while `run_one_candidate` performs ~5 such full reads per candidate. I
measured it directly (400 candidates, realistic ~930-byte screen payloads):

| candidates | ms per candidate |
|---|---|
| 1–100 | 1.78 |
| 101–200 | 5.14 |
| 201–300 | 8.91 |
| 301–400 | 12.79 |

plus a full resume scan of 400 already-terminal candidates in 1.92 s (710 KB ledger). Growth is
linear per candidate ⇒ O(n²) per epoch. At this era's own scale this is harmless — the hard family
cap is 24 variants (`goal.md` §5.2) over ~11 required source objects — so I graded it GAP rather
than IMPORTANT on the strength of the measurement, not on assumption. It would matter in the
thousands of candidates; if J-06's real manifest ever approaches that, add the missing performance
fixture before the freeze rather than after.

**B6 — OBSERVATION: the fast path's econ-floor check is conditional on the intent row existing**

`foundry_runner.py:104` guards with `pinned_intent is not None`, so a terminal row without a
matching intent row would silently skip the econ-floor half of the identity check.
`run_one_candidate` always records intent before terminal, so this is unreachable through the
production path today; noted only because a future direct `record_terminal` caller would open it.

**B7 — OBSERVATION: `alternatives` is the one §1.4 field with no fail-closed validation**

`foundry_source_registry.py:195`'s `alternatives: tuple[str, ...] = ()` is accepted verbatim: no
check that the named ids exist in the batch, that they are family siblings, or that a record does
not name itself — unlike `threshold_provenance` and `explicit_exclusion`, which raise at
construction (`:202-219`), and unlike `quoted_spans`, which fails closed in `lint_quoted_spans`.
That is consistent with the spec (which asks for a disclosure field, not a constraint), and the
field's own comment is explicit that family-key membership — not this field — is what actually
lets the compiler enumerate. Worth a batch-level lint before J-06 authors the real 11 records, so
a mis-typed sibling id cannot enter the frozen registry silently.

### Frontend Findings

None — no frontend file was touched (`git status` shows zero `apps/frontend` changes), and
`tsc --noEmit` is green (0 errors, QA report Step 3). The Foundry UI stays deferred to Binding
Execution Order step 5 by design.

### Test Findings

**T1 — GAP: TC-6's "crash" discards nothing, and its "never trusts a stale checkpoint" claim is
vacuous**

The crash is simulated by `del ledger_run1` (`test_foundry_hermetic_epoch.py:566`), but
`FoundryLedger` holds no in-memory state — every read goes back to disk
(`micro_chain_ledger.py:116-139`) — so deleting the instance changes nothing that a resume could
have gotten wrong. The resume proof itself is still valid and useful (a fresh ledger over the same
directory verifies/skips the first 12 rows byte-identically, 20 terminal rows total, canonical
order and chain integrity hold). Two honesty notes for the record: the spec allowed "process kill
**or** dropped checkpoint" and the weaker of the two was used; and no checkpoint file exists
anywhere in `foundry_runner.py`, so "never trusting a stale checkpoint" cannot be falsified by any
fixture — the derived checkpoint cache `goal.md` §9.2 describes is simply not built yet. Neither
is a spec violation; both should be stated plainly to J-06/J-07 rather than carried as proven.

**T2 — OBSERVATION: TC-1 asserts canonical order about its own loop, not about `run_family`**

TC-1 calls `fr.run_one_candidate` directly in a `for` loop (necessary — the `killed_fragile`
candidate needs a per-candidate `monkeypatch.context()`), so "visiting order is unaffected by any
kill/survivor" is proven for the caller's sequence, not for the production walker. `run_family`'s
own order invariance is covered by iter-2 (`test_foundry_runner.py:83`), and the seam test added
in B1 now also drives `run_family` inside this file.

**T3 — OBSERVATION: `killed_fragile` is reached with a forced p-value, disclosed and scoped**

`scout._two_sided_p` is monkeypatched to `0.0001` for that one candidate. I verified this is a
verbatim reuse of the production Scout test's own technique (`test_scout.py:424`, with the same
8/12/8-session sign-flip fixture at `:405-417`) and that it is applied inside
`monkeypatch.context()` per candidate, so the other six candidates in the composite epoch screen
under real p-values. Acceptable, and correctly documented in the fixture's docstring.

**T4 — OBSERVATION: two assertions in TC-1 are tautological**

"Every non-compiled source keeps its declared disposition" re-invokes the same pure function on
the same records, and TC-11's `alternatives` assertions read back what the fixture just passed in.
Harmless, but they should not be counted as evidence of interference-freedom or of any derivation.

**T5 — GAP (process, not product): the QA report mis-describes how TC-13 was verified**

`reports/qa/goal-hypothesis-foundry-iter-3-qa.md` Step 3.5/Step 4 assert that the J-01 golden
replay "is a pure backend verification already covered by the full test suite execution". That is
false — `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json` is a two-step browser
script (`goto /desk` → click "Hypothesis Foundry" → expect `08e471b10130e1e2`), and
`status.json` records `browser_checks_run: false` for the QA lane. TC-13 is nevertheless genuinely
satisfied, by a different lane: `reports/phase-goal-hypothesis-foundry-iter-3-regression-replay-results.md`
records a deterministic Playwright replay, 1/1 PASS, with evidence
`reports/qa/goal-hypothesis-foundry-iter-3-evidence/J-01-verify.png`, which I opened and confirmed
shows `/desk` with the Hypothesis Foundry panel rendered. Cite the replay artifact, not the QA
report's reasoning.

---

## 3. Domain Assessment

The scientific machinery holds up to a skeptical read.

- **Mechanical mapping is closed, not defaulted.** `SCOUT_TO_FOUNDRY_STATE`
  (`foundry_runner.py:43-52`) is a fixed dict and `map_scout_decision` raises on an unmapped
  decision rather than falling through to any of the three Foundry states — so J-05 step 3's
  "there is no second Foundry verdict" is structural. The composite epoch asserts the exact
  `reason` string per candidate, not merely the coarse state.
- **TC-2's denominator invariance is structural, not incidental.**
  `foundry_family.n_variants_tried_for` reads `family.variant_count` only and never an execution
  counter (`foundry_family.py:95-99`), and `FoundryFamily` is a frozen dataclass whose only
  "insertion" API refuses unconditionally. The terminal-row assertion (`variant_count == 7` and
  `best_of_n_disclosure.n == 7` on every row regardless of position or verdict) therefore proves
  what it claims.
- **Determinism is genuine.** The kill fixtures use per-fixture `random.Random(<key string>)`
  instances, and `scout`'s permutation null seeds from `scout_stream(family_id, …)` →
  `random.Random(key)` → a numpy engine (`scout.py:281-297, 993-1030`), never the global RNG — so
  the oracle is stable under `pytest-randomly` reseeding and satisfies the "deterministic and
  seeded" anti-goal.
- **Fail-closed is real, by trace not by claim.** `foundry_interpreter.resolve_population`
  iterates the anchor sequence with no `try`/`except` anywhere in the module, and TC-7 passes a
  lazy generator so the accessor error is raised mid-iteration; it propagates through
  `interpret_candidate` → `run_one_candidate` → `run_family` (a plain list comprehension) with no
  handler in any Foundry module. No terminal row can be written on that path. A grep confirms no
  Foundry module assigns `evidence_class` at all (it arrives inside the Scout payload), which is
  the strongest possible form of the TC-8 invariant.
- **Anti-goals verified independently.** No `foundry_*.py` module imports `scout_ledger`;
  `docs/hypothesis-foundry/` does not exist; the diff deletes no test and adds no `xfail`/`skip`
  (`git diff -U0` over `apps/backend` shows the only removed lines are docstring rewraps); the
  new fields are additive with safe defaults; `source_hash` is `init=False` and recomputed in
  `__post_init__` (`foundry_source_registry.py:200, 219`) so it cannot be forged or drift;
  `alternatives` is included in the registry-hash projection while the derived `source_hash` is
  correctly excluded (`:262-302`). Note for J-06: adding `alternatives` to that projection changes
  every `source_registry_hash` and therefore every `candidate_spec_hash` — harmless now because no
  frozen artifact exists, but it means the real freeze must be authored **after** this change,
  never re-verified against pre-iter-3 hashes.

Test quality overall is high: assertions are exact values (states, reasons, counts, hash
sequences), not "in" checks or truthiness, and the fixture provenance is traceable to already-
proven Scout tests rather than hand-tuned to pass.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_foundry_hermetic_epoch.py:301-386` | New `_compilable_variant_record`/`_compilable_blueprint` fixtures plus `test_compiled_candidate_specs_flow_from_the_real_compiler_into_the_real_runner` — closes the untested compiler → runner seam (B1) |
| 2 | Important | `apps/backend/tests/test_foundry_hermetic_epoch.py:393, 411-432` | TC-3 now actually exhausts the zero-candidate epoch through `fr.run_family` and asserts zero ledger rows + clean chain (B2) |

Both changes are test-only and additive; no production file was modified by this audit
(`git status` after the fixes shows the same five modified source files the dev left, and this
one untracked test module).

**Post-fix verification (commands and results):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_foundry_hermetic_epoch.py -v` →
  **10 passed in 0.80s** (was 9 items; +1 new test, TC-3 still green after being rewritten).
- `cd apps/backend && .venv/bin/python -m pytest tests/test_foundry_hermetic_epoch.py
  tests/test_foundry_compiler.py tests/test_foundry_runner.py tests/test_foundry_source_registry.py
  tests/test_foundry_interpreter.py tests/test_foundry_family.py tests/test_foundry_freeze.py
  tests/test_foundry_ledger.py tests/test_scout.py` → **169 passed in 32.15s**.
- Pre-audit full-suite baseline is unchanged and independently cited from QA's own log
  (`reports/qa/goal-hypothesis-foundry-iter-3-test.log`, final line: `3842 passed, 8 skipped,
  2 warnings in 422.49s`); this audit's two additions raise the collected count by one test item
  and touch nothing outside their own module.

---

## 5. Recommended Next Step

**Proceed.** J-05's substance is delivered and now genuinely spans the compiler → runner seam;
J-04's and J-02's carried blockers are closed as specified (TC-9/TC-10/TC-11 traced in code, not
accepted from the handoff). J-05/J-02/J-04 remain `partial` on the established
"no-UI-yet" precedent — nothing here is journey-level browser evidence — and J-01's replay is
verified green with a screenshot.

Carry these into the Binding Execution Order step-5/J-06 planning, in priority order:

1. **Before J-06 authors the real 11 source records**: add a batch-level lint for `alternatives`
   (ids must exist, must be family siblings, must not self-reference) — B7. The real registry is
   the first place a typo becomes frozen.
2. **When the freeze/first-read-lock wiring lands (J-06/J-07)**: verify `manifest_hash` on the
   intent-without-terminal resume branch too (B4), and route the freeze-set verification through
   the runner so the "compiler → … → freeze → … → runner" claim becomes literally true (B3).
3. **Correct the record**: `state/blueprint.md:129-139`'s iter-3 note and the dev handoff both
   describe freeze as exercised by the oracle suite; it is not (B3). Likewise, the evaluator should
   cite the regression-replay artifact for TC-13, not the QA report's account of it (T5).
4. **Only if the real manifest grows past a few hundred candidates**: build the missing performance
   fixture, or replace the per-call full-file ledger scan; the measured cost curve is in B5.
