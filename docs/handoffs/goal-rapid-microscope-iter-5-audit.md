# Goal-rapid-microscope-iter-5 Audit Report

**Date:** 2026-08-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-05's walk-forward engine is genuinely built, not a shell: the origin fence, the purge assertion,
the five-condition `WF_SURVIVOR_RULE_V1`, the class/process eligibility narrowing, the tail-anchored
hash chain and the real 155-session diagnostic run all hold up under direct inspection, and I
reproduced the real ledger's 5 folds / 100 validation sessions / all-`historical_exposed_diagnostic`
result off disk rather than trusting the handoff. But the audit found and fixed one **critical**
counting fault the whole pipeline missed — a second press of the diagnostic Compute button (or a
second CLI run) appended a duplicate `fold_result` row per fold, and the real sequence's honest
`2 < 3 sufficient folds — refused` then became a **computed verdict over `n_sufficient_folds: 4`
built from the same 2 folds counted twice** — plus two important defects, also fixed (the Mode B
predeclaration ran *after* the run's outcome read and was never ledgered; the TR-3 import-ban guard
scanned one directory and only import statements). Two gaps remain unclosed and are documented: the §6.7
exposure registry is never r2-initialized for the 12 legacy tick symbol-days in production (goal.md
J-05 Step 1 names them explicitly), and **TC-29's browser regression never ran at all** — the exact
`Frontend Present: no` failure iteration 4 made, which this spec forbade in bold.

---

## 2. Findings

### Backend Findings

**B1 — CRITICAL (fixed): a repeat diagnostic run double-counted every fold, converting an honest
sufficiency refusal into a computed verdict over duplicated evidence**

`apps/backend/app/research/walkforward_ledger.py:251` (`append_fold_result`, as shipped) appended a
new physical `fold_result` row on every call, with no notion of "this exact evaluation is already on
record". `run_diagnostic_walkforward` (`walkforward.py:1010`) is invoked by *both*
`POST /research/desk/micro/walkforward/compute` (`micro_routes.py:307`) and the CLI warmer
(`python -m app.research.walkforward --diagnostic`), neither of which forbids a second run — indeed
the module deliberately makes a repeat run safe everywhere else (`register_fold_spec`'s idempotent
replay at `walkforward_ledger.py:176`, the `has_any_exposure_entries` re-seed guard at
`walkforward.py:1072`). The fold-result path was the one place the same discipline was missing.

Failure scenario, reproduced against the **real** corpus through the **real** CLI (I copied
`.data/micro_walkforward` + `.data/micro_exposure_registry` to a scoped temp dir, pointed
`TAPEOLOGY_MICRO_WALKFORWARD_DIR`/`TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR` at the copy, and ran
`python -m app.research.walkforward --diagnostic` a second time):

```
BEFORE : fold_results: 5 | verdict: {"refused": true,
         "reason": "2 < 3 sufficient folds -- ... never a fabricated result", "n_sufficient_folds": 2}
AFTER  : fold_results: 10 | fold_index: [0,1,2,3,4,0,1,2,3,4]
         verdict: {"refused": false, "verdict": "not_survivor", "n_sufficient_folds": 4, ...}
         decay recency: {"older_positive_share": 1.0, "recent_positive_share": 0.0}
```

Every downstream consumer that counts rows was affected: `sequence_verdict`'s
`WF_MIN_SUFFICIENT_FOLDS` floor (`walkforward.py:701`), `_pooled_sign_agreement`
(`walkforward.py:633`), the pooled effect, and `decay_view`'s older-vs-recent split
(`walkforward.py:722`) — which "compared" fold 3 against fold 4 duplicated, producing a
`1.0 vs 0.0` recency line out of two real folds. TC-17's refusal — the single mechanism that stops
this engine fabricating a verdict over an insufficient sample — was defeated by pressing a button
twice. The era's own "the denominator never shrinks" invariant is equally a rule that it must not
spuriously *grow*.

**Fix applied** (`walkforward_ledger.py:216-282`): `existing_fold_result` + an idempotent-replay
branch in `append_fold_result` keyed on `(sequence_id, fold_index, spec_hash)` — the identity of one
evaluation act. A genuinely different fold, or the same fold under a different frozen spec, still
appends. Chosen at that single choke point because all four writers (Mode A refits, Mode B
evaluations, the diagnostic run, the TR-16 oracles) already funnel through it. `run_diagnostic_
walkforward` now also returns `folds_appended`/`folds_replayed`, disclosed in the CLI line and in the
route's run-log entry (`micro_routes.py:332`), so a replay run is never silently reported as
fresh evidence.

**Verification** (post-fix, same real-corpus procedure):
```
diagnostic walk-forward complete: 5 fold(s) (0 newly recorded, 5 replayed from the existing
ledger), 100 validation session(s) over 154 corpus session(s).
fold_results: 5 | fold_index: [0,1,2,3,4]
verdict: {"refused": true, "reason": "2 < 3 sufficient folds -- ...", "n_sufficient_folds": 2}
chain: {'ok': True, 'failed_at_row': None, 'reason': None}
```
Plus three new regression tests (`tests/test_walkforward.py:625, 642, 664`), and the full suite
(§4).

**B2 — IMPORTANT (gap, NOT fixed): the exposure registry is never r2-initialized for the 12 legacy
tick symbol-days in production — a latent breach of the "never `historical_oos`" anti-goal**

`docs/goal.md`'s J-05 Step 1 requires "the §6.7 exposure registry (initialized with every playbook
**and legacy-tick** window pre-marked exposed)"; spec §6.7 says the same. The mechanism exists
(`micro_accessor.py:169`, `initialize_r2_exposure_registry`) but the only production caller is
`walkforward.py:1072`, which seeds `PLAYBOOK_DIAGNOSTIC_CORPUS_ID` alone. Grep of the whole backend
confirms: no other call site in `app/`; the two test call sites both pass a hand-made `"legacy_tick"`
stand-in corpus with fabricated windows (`tests/test_micro_accessor.py:244`,
`tests/test_walkforward.py:307`). So in production the 12 legacy tick symbol-days have **no**
exposure entries.

This compounds with the disclosed unlogged read path: `micro_join.py` and `scout.py` are re-pointed
through the accessor in `origin=None` mode, which by construction never logs an exposure entry
(`micro_accessor.py:257` only logs when an origin *and* a registry are supplied). The module
docstring justifies that as "redundant with r2's own initialization (every window of the
legacy/playbook corpus is ALREADY marked exposed from the moment the registry exists)" — a
justification that is simply not true of the legacy tick corpus as wired. A future Mode B spec
registered against those windows would classify `historical_oos` off an empty registry, which is
precisely the "quietly WRONG" fault the developer caught and fixed for the playbook corpus (his own
Known Issues note), and it would breach the critical anti-goal "the 12 pre-existing tick symbol-days
are permanently exploratory — never sealed, **never `historical_oos`**, never relabeled."

Not reachable today: TR-15 refuses fold construction on an 11-session corpus, so no current code path
queries a tick window's exposure state. Not fixed here because the honest fix requires naming the
legacy tick corpus's `corpus_id` and its window source, and wiring a seeding act that has no
production caller until J-06 — a design decision the spec does not pin, and inventing one would
breach T-1. **This is the top prerequisite for J-06.**

**B3 — IMPORTANT (fixed): the Mode B predeclaration ran AFTER the run's outcome read and was never
ledgered — and both the code and the handoff claimed the opposite**

`run_diagnostic_walkforward` as shipped read the corpus's outcomes at
`observations = playbook_observations(...)` and only then, inside the per-fold loop, called
`register_mode_b_spec`. Its own docstring asserted "predeclares Mode B specs ... (ledgered before any
outcome is read — `register_mode_b_spec` is called before `playbook_observations` is ever invoked
below)", and the dev handoff repeated the claim. Both were false of the code. Worse,
`register_mode_b_spec` (`walkforward.py:556`) is a pure in-memory construction — the predeclaration
was never written to the ledger at all, so nothing on disk could ever evidence the registration
order that spec §6.5 ("registered — ledger row, spec hash, timestamp — FIRST") and the phase spec's
own IN SCOPE bullet ("predeclare (ledgered, before any outcome read)") both demand.

No misclassification resulted *this* run: every playbook window is r2-marked exposed at
`2026-08-16T00:00:00Z`, before any `registered_at`, so the class is `historical_exposed_diagnostic`
either way. The hazard is for the next corpus that is *not* pre-marked — the ordering inversion plus
B2's unlogged reads is exactly how a genuinely-exposed window ends up stamped `historical_oos`.

**Fix applied** (`walkforward.py:1035-1050`): the predeclaration is now the function's first act,
before any store is touched, and is persisted as a permanent hash-chained `mode_b_spec` row
(`walkforward_ledger.py:235`, `record_mode_b_predeclaration`, itself an idempotent replay on
`(sequence_id, spec_hash)`); the evaluation then reuses the **ledgered** row's `registered_at`, so a
repeat run cannot mint a later registration instant. Docstring and dev handoff corrected.
**Verification:** `tests/test_walkforward.py:695` proves the ordering by observing the ledger's
actual contents at the moment the run first touches outcome data (the `mode_b_spec` row is present,
no `fold_result` row is), not by reading source order; the real-corpus re-run above shows the new row
kind on disk with the chain still verifying.

**B4 — GAP: sequence identity ignores every spec field except the rule string**

`sequence_id_for` (`walkforward.py:272`) keys on `(corpus_id, rule_identity)` only, but spec §6.4
says "Only a RULE change **(or any other spec-field change)** starts a new constant-rule sequence".
Two evaluations differing in `sidedness` or `econ_floor` therefore land in one sequence, and
`list_walkforward_sequences` (`walkforward.py:773`) then reads `sidedness`/`econ_floor` off the
sequence's **last** row and judges every earlier fold under it. TC-11 only pins the rule-string
direction, so the DoD checkbox is met verbatim; no production caller can reach the mixed case this
iteration (one spec exists). Left for the spec owner — closing it changes served `sequence_id`s and
the shape of the existing real ledger row, which is not an audit-scope edit.

**B5 — GAP: TR-15's typed floor refusal is never wired into a production entry point**

`require_sufficient_sessions_for_folds` (`walkforward.py:335`) raises the typed `11 < 105` refusal
and is proven by TC-20 — but nothing in `app/` calls it. `run_diagnostic_walkforward` goes straight
to `build_folds`, which returns `[]` for a below-floor corpus; the run then reports
`folds_evaluated: 0` with no reason attached. The delivered test asserts exactly that behaviour for
an empty store ("an empty universe/playbook tree registers the fold spec but evaluates zero folds"),
so it is deliberate, but it is the "empty fold report standing in for the refusal" that TR-15's own
wording forbids. Unfixed: wiring the raise would change the tested empty-store path and needs a call
on what an empty store should return — a design decision, not a surgical fix.

**B6 — GAP: the observation `value` carries no unit contract, while `econ_floor` is denominated in
bps**

`playbook_observations` (`walkforward.py:970`) feeds `forward.horizons[h].return_pct` — **percent**
(the real fold 3 effect reads `0.0192`, i.e. ~1.9 bps) — while the TR-16 oracle fixtures feed **bps**
and `WF_SURVIVOR_RULE_V1` condition 3 compares `abs(pooled_effect) >= econ_floor["floor_bps"]`
(`walkforward.py:676`). Nothing compares mismatched units today only because the diagnostic run's
`econ_floor` is honestly `None` and condition 3 fails closed. A J-09 study that supplies a bps floor
to a percent-valued corpus would be wrong by 100×. Recommend pinning a unit on the observation
contract (or carrying `unit` on each observation) before J-07/J-09 wire real floors.

**B7 — OBSERVATION: conditions 2 and 4 are computed over `eligible` folds where §6.6 says "over the
sufficient folds"**

`_pooled_sign_agreement` (`walkforward.py:633`) and `_opposite_direction_eligible_fold_exists`
(`walkforward.py:641`) both narrow to `historical_oos` + `rule_process` folds. This is conservative
and cannot change a survivor verdict (condition 1 already fails whenever `eligible ⊊ sufficient`),
and it is what makes TR-5's "a diagnostic fold contributes nothing to any pooled number" provable —
but the **served** `sign_agreement` value can differ from the spec's literal denominator in a
mixed-class sequence. Similarly `decay_view`'s recency shares (`walkforward.py:747`) pool folds
without partitioning by `evidence_class`. Worth one line in the J-08 rendering so a reader knows
which denominator they are looking at.

**B8 — OBSERVATION: the corpus is 154 sessions, not 155**

Confirmed live: the current default `playbook_input_signature` covers 155 distinct session dates
including the 2025-06-03 orphan, so 154 are walked after the disclosed exclusion. TC-23's actual
acceptance numbers (5 folds / 100 validation sessions) hold exactly either way — verified off disk
and by re-running the CLI. The developer flagged this rather than silently reconciling it; that was
the right call.

### Frontend Findings

**F1 — none.** `git status` shows zero files touched under `apps/frontend/`, which is correct for
`Frontend Present: no`. The Walk-Forward section's rendering is J-08's registered scope, and the
served-ahead-of-UI pattern matches every prior iteration of this era.

### Test Findings

**T1 — IMPORTANT (fixed): the TR-3 import-ban guard scanned one directory and only import
statements**

TC-3's wording is "given the **full backend source tree** ... no module other than
`micro_accessor.py` contains an import of `read_snapshot_rows`", and the phase spec's IN SCOPE says
"imports **or calls** the raw snapshot-row reader". The delivered guard globbed
`app/research/*.py` only (one of four packages under `app/`) and inspected only `Import`/
`ImportFrom` nodes — so a module in `app/mcp/`, `app/providers/`, `app/engine/` or the package root
could open the raw reader freely, and *any* module could bypass it entirely with
`from . import micro_snapshots` followed by `micro_snapshots.read_snapshot_rows(...)`, which imports
no banned name at all. A guard for a critical anti-goal ("the accessor is the only data door") that
cannot see either case is an escape hatch, not enforcement. (The reviewer's "TR-3 import-ban
confirmed whole-backend-wide" was his own manual grep — the *test* did not do that.)

**Fix applied** (`tests/test_micro_accessor.py:208`): the scan now walks all of `app/` recursively
(101 modules; asserts >50 files and that `app/engine` is covered, so a future tree move cannot
silently narrow it) and additionally flags module-qualified attribute references to the raw opener,
resolved by dotted path so the **legal** `MicroAccessor(...).read_snapshot_rows(...)` call is not
false-flagged. `tests/test_micro_accessor.py:230` proves both directions on seeded sources — the
bypass is caught, the legal call is not. Result: exactly one file references the raw opener across
all 101 modules — `micro_accessor.py`, the allowed importer.

**T2 — GAP: TC-14 is proven only against a stand-in corpus.** Both TC-14 tests
(`test_micro_accessor.py:244`, `test_walkforward.py:307`) seed a hand-made `"legacy_tick"` corpus
with 3-5 invented window strings; neither asserts anything about the actual 155 playbook windows or
the actual 12 legacy tick symbol-days that the spec names. The mechanism is proven; the *named
corpora* are not — which is how B2 stayed invisible through review and QA.

**T3 — OBSERVATION: two acceptance assertions are looser than their TC wording.** TC-5 asks for
`spec_hash`/`decision`/`reason` byte-identical after the re-point; the added test
(`tests/test_scout.py:651`) asserts `decision`/`reason` only (`spec_hash` is a pure function of the
candidate spec, so a read-path re-point cannot move it — acceptable, but the assertion is weaker
than stated). TC-21/TC-22's "byte-identical rerun" is proven by comparing
`(fold_index, effect, sign, n)` tuples and verdicts across two ledgers with different `corpus_id`s,
not literal bytes. Both are defensible; neither is what the words say.

**T4 — positive finding, recorded because it is unusual.** The TR-16 oracles
(`tests/test_walkforward_oracles.py`) run the **real** `scout.compute_p_screen` and the **real**
`build_folds`/`evaluate_mode_b_fold`/`sequence_verdict` over synthetic corpora, not a second
implementation: the known-null corpus reaches `p_screen >= alpha` and never survives; the +20bps
planted corpus is screened significant, recovers `pooled_effect` within ±2bps of the plant with the
right sign, and **does** reach `walkforward_survivor`. That last one matters — it proves the survivor
path is reachable at all, so the diagnostic run's `not_survivor`/refused results are an honest
finding rather than a rule that can never fire.

### Evidence Findings

**E1 — IMPORTANT (gap, NOT fixable in audit scope): TC-29's browser regression never ran — the exact
iteration-4 failure this spec forbade in bold**

`reports/phase-goal-rapid-microscope-iter-5-ui-test-results.md` reads, in full: "**Browser QA
Verdict:** SKIPPED — Backend-only phase (Frontend Present: no). No browser tests executed." The QA
report's Browser Checks section says the same. `runs/goal-rapid-microscope-iter-5/status.json`
records `"browser_checks_run": false`. No screenshots exist; no `ux-regression` report for this
iteration exists.

The spec's TESTING REQUIREMENTS are unambiguous and were written specifically to stop this: "**A
blanket SKIP across J-01/J-02/J-03/J-04/J-10 is not an acceptable outcome of this spec; it is the
exact failure iteration 4 already made once**", and TC-29 requires J-10's 13-step sentinel to run
"regardless of `Frontend Present: no`". It did not run. This is a DoD checkbox that is definitively
unmet, and it is the same unclosed gap that produced iteration 4's ESCALATE.

I did not attempt to close it myself: it needs the store-scoped browser rig, a clean frontend rebuild
and Chrome MCP, which is the browser-qa-agent's own dispatched step, not a source fix. **The honest
consequence for the journey ledger: J-01, J-02, J-03, J-04 and J-10 must be recorded `unknown` for
this iteration, never `passing` — no screenshot, no pass (T-10).** The mitigating fact is real but
does not substitute for evidence: this iteration touched zero frontend files and zero shared UI code
paths, so the *prior* probability of a UI regression is low.

---

## 3. Domain Assessment

The core domain logic is sound, and in several places better than the spec strictly required.

**What is genuinely right.** Purge is asserted rather than assumed on every fold path
(`observations_in_sessions` filters *then* calls `assert_purge_exact`, so a malformed pre-filtered
list raises instead of quietly pooling). The eligibility narrowing in `_eligible_folds` is the
strongest piece of the implementation: every numeric byproduct — sign agreement, pooled effect, the
opposite-direction check — is computed over `historical_oos ∧ rule_process` folds only, so TR-5 and
TR-21 are *provable* (a diagnostic fold carrying `999_999.0` moves the pooled effect by exactly
zero) rather than asserted via a boolean that happens to fail. `sequence_verdict` refuses below
`WF_MIN_SUFFICIENT_FOLDS` **without ever calling** the survivor predicate, which is the right shape
for a refusal. Condition 3 fails closed when no econ floor applies, rather than treating "no floor"
as "floor satisfied" — the single most common way a gate like this gets quietly defeated. The
geometry freeze walks the ledger's own append order instead of a cached "current geometry", and the
tail anchor is written *after* the row it commits to, so a crash leaves the file long (benign), never
falsely short.

**The one real integrity fault** was not in any of that reasoning — it was in the plumbing beneath
it (B1). Every guard above assumes the fold rows it reads are distinct pieces of evidence; nothing
enforced it, and the era's single most load-bearing refusal ("2 < 3 sufficient folds") evaporated on
the second press of a button. That is worth noting as a pattern: this iteration's statistics were
audited carefully and its *bookkeeping* was not.

**Honesty of the real result.** The diagnostic run's actual output is unflattering and correctly
served as such: 3 of 5 real folds are `insufficient` (17, 16 and 15 observations against a floor of
30 — the playbook universe's own coverage grew over the corpus's history), the sequence refuses a
verdict at 2 < 3, and every fold is `historical_exposed_diagnostic`, worth zero graduation credit by
construction. Nothing was tuned to make that look better. That is exactly the behaviour this journey
exists to produce, and I verified all of it off the persisted ledger rather than from the handoff.

**DEFINITION OF DONE.** I ran the full code trace on every risk-class item (accessor fence, purge,
geometry freeze/voiding, Mode A/B registration, survivor rule, floors, class/process discipline,
compute-manager and ledger durability, the diagnostic run) — findings above. The mechanical items I
accepted on the reviewer's PASS plus an executed check: TC-28's suite count (review report
`spec_alignment: definition_of_done: complete` + QA "3028 passed, 8 skipped, 0 failed in 524.66s",
which I then re-ran myself, §4), and TC-27's frozen foundations (review report's own reproduction —
which I *also* re-ran independently rather than accept: fingerprint `08e471b10130e1e2`; all six
`referee_*.py` SHA-256s byte-identical to the iteration-0 listing in
`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:76-81`; empty `git diff` over `app/engine/`,
`desk_playbook.py`, `desk_playbook_context.py`, `config.py`; 18 snapshot files totalling exactly
3,815,933 rows). TC-29 has neither a reviewer PASS nor a QA row — it was never executed (E1).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/backend/app/research/walkforward_ledger.py` | `existing_fold_result` + idempotent-replay branch in `append_fold_result` keyed on `(sequence_id, fold_index, spec_hash)`, so a repeat run replays its folds instead of appending duplicate evidence (B1) |
| 2 | Critical | `apps/backend/app/research/walkforward.py` | `run_diagnostic_walkforward` returns `folds_appended`/`folds_replayed`; CLI line discloses the split (B1) |
| 3 | Critical | `apps/backend/app/research/micro_routes.py:332` | run-log entry carries `folds_replayed` so a repeat trigger is not logged as fresh evidence (B1) |
| 4 | Important | `apps/backend/app/research/walkforward.py` | Mode B predeclaration hoisted to the function's first act, before any store read, and persisted via `record_mode_b_predeclaration`; evaluation reuses the ledgered `registered_at`; false docstring corrected (B3) |
| 5 | Important | `apps/backend/app/research/walkforward_ledger.py` | new `ROW_KIND_MODE_B_SPEC` + `record_mode_b_predeclaration`/`mode_b_predeclarations_for_sequence` (idempotent on `(sequence_id, spec_hash)`) (B3) |
| 6 | Important | `apps/backend/tests/test_micro_accessor.py` | TR-3 guard widened to all 101 modules under `app/` and to module-qualified attribute calls, with a seeded proof that it catches the bypass and does not false-flag the legal accessor call (T1) |
| 7 | — | `apps/backend/tests/test_walkforward.py` | 4 regression tests: duplicate-append replay, below-floor refusal survives 3 repeat runs, repeat diagnostic run leaves the served sequence byte-stable, predeclaration is on disk before the first outcome read |
| 8 | — | `docs/handoffs/goal-rapid-microscope-iter-5-dev.md` | corrected the two claims the fixes invalidated (the predeclaration ordering; the suite count) |

**Evidence for the fixes.**
- Targeted: `.venv/bin/python -m pytest tests/test_walkforward.py tests/test_micro_accessor.py
  tests/test_micro_chain_ledger.py tests/test_walkforward_oracles.py -p no:randomly` →
  **82 passed**.
- Full suite on the final tree: `cd apps/backend && .venv/bin/python -m pytest tests/` → **3033
  passed, 8 skipped, 0 failed in 536.62s**, exit code 0 (dev/QA baseline 3028/8/0; +5 audit
  regression tests, 0 new failures) — TC-28 re-verified post-fix. (An earlier post-fix run, before
  two cosmetic follow-ups, reported the same 3033/8/0.)
- Real-corpus behavioural proof, before and after, via the production CLI against a scoped copy of
  the real ledger — quoted verbatim under B1.
- Frozen foundations re-checked after the fixes: fingerprint `08e471b10130e1e2`, six referee hashes
  unchanged, `app/engine/`+`desk_playbook*`+`config.py` diffs empty, 3,815,933 snapshot rows.
- `.data/micro_walkforward` and `.data/micro_exposure_registry` were **not** modified by this audit —
  all probing ran against copies under `TMPDIR`. The real ledger therefore still carries the
  developer's original 6 rows and will gain its `mode_b_spec` predeclaration row on the operator's
  next genuine run (whose fold rows will replay, not duplicate).
- Diff reviewed for scope: `micro_routes.py` +5 lines inside the block the developer added this
  iteration; no frozen file, no `Config` field, no route, no frontend file touched.

---

## 5. Recommended Next Step

**Do not proceed to J-06 until two things happen, in this order:**

1. **Run the browser regression this spec required (E1).** Dispatch browser-qa-agent for
   J-01/J-02/J-03/J-04's shared-panel re-check and J-10's unmodified 13-step sentinel, with
   screenshots on record, exactly as TC-29 words it. Until then those five journeys are `unknown`
   for this iteration, not `passing` — and this is now the *second* consecutive iteration in which
   `Frontend Present: no` swallowed the whole browser lane despite a spec that forbade it in bold.
   The fix belongs in the pipeline wiring, not in another spec paragraph: a spec that names
   required-still-passing journeys should make the browser step's dispatch unconditional.
2. **Close B2 before J-06 writes a single sealed shard.** J-06 is the iteration that creates
   genuinely unexposed data, which is the first moment `historical_oos` can legitimately be
   awarded — and therefore the first moment an unseeded legacy-tick corpus can award it *wrongly*,
   breaching a critical anti-goal. The owner needs to fix the legacy tick corpus's `corpus_id` and
   its window source, then wire the r2 seeding at the same place the vault initialises. While there,
   decide whether the disclosed unlogged read path (`micro_join`/`scout` unfenced) stays acceptable
   once the registry actually matters — its current justification depends on the seeding that does
   not exist.

Then carry B4 (sequence identity vs. §6.4's "any other spec-field change"), B5 (TR-15's refusal
unwired) and B6 (the bps/percent unit contract) into J-07/J-09 planning — B6 in particular should be
settled before any real economic floor is compared against a real effect. The two open owner rulings
(the `micro_observer.py:636/657` one-quote-early `available_at` stamp; Scout's "variants tried" per
data-set) remain correctly untouched and are still due before J-06.

J-05 itself is delivered and, after this audit, materially more trustworthy than it was when QA
passed it.
