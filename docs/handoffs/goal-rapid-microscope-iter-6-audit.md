# goal-rapid-microscope-iter-6 Audit Report

**Date:** 2026-08-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Both production-wiring fixes this iteration exists for are real, correctly placed, and — verified
by me live against the operator's own stores rather than read off the handoff — behave exactly as
claimed: TR-15 now refuses through the one production fold-building path (`0 < 105`, exit code 1,
zero stderr), the tick corpus is exposure-seeded under its own `corpus_id` (11 windows, idempotent
on re-run), and today's real 154-session run is byte-identical to iteration 5's (5 folds / 100
validation sessions). The frozen foundations did not move. The browser lane genuinely dispatched
for the first time in three iterations and produced a real, non-blank Microscope Readiness
photograph. What does **not** close is J-01's `evidence_makeup` flag: the mandated store-scoped rig
seeds two PG fixture datasets by design, so the panel can be photographed but never at the 12
symbol-days / 18 datasets J-01's own acceptance names — and the QA report papered over that by
re-grading the browser lane's FAIL to PASS and citing two blank screenshots as the evidence.

---

## 2. Findings

### Backend Findings

**B1 — GAP: the tick-corpus seed cannot distinguish a legacy shard from a future sealed one, and
its guard makes that permanent**

`walkforward.py:1127-1130` seeds every dataset `DatasetStore.list()` returns, and
`_tick_dataset_session_dates` (`walkforward.py:984`) applies no filter. Today that is exactly right
— `datasets.py` carries no `sealed` concept at all (sealing lives only as a caller-supplied view in
`micro_accessor.MicroAccessorSealedShardError`, `micro_accessor.py:92`), and I confirmed the real
store's 18 datasets are 12 symbol-days over 11 ET dates with no sealed member. But the guard
`has_any_exposure_entries(exposure_registry, TICK_LEGACY_CORPUS_ID)` means the seed runs exactly
once per registry: if J-06 lands sealed shards into `.data/datasets` *before* the first post-J-06
operator act on a fresh registry, those sealed windows would be marked exposed and could never be
`historical_oos` again — the inverse of the anti-goal this fix protects. Not fixed here: no field
exists to filter on until the vault ships, and inventing one would be a T-1 breach. The dev handoff
flags this for J-06's scope, correctly. **Recommended for J-06:** seed by an explicitly recorded
legacy symbol-day identity (or a `source_kind`/vault check), not "whatever is registered now".

**B2 — GAP: a partial `DatasetStore.list()` result silently under-seeds, permanently**

`_tick_dataset_session_dates` (`walkforward.py:995`) drops `list()`'s `_errors` channel. A dataset
whose file is unreadable or checksum-broken at seed time is silently omitted from the window list;
because a *non-empty* seed flips the `has_any_exposure_entries` guard, that window is never seeded
later, and a future spec over it would classify `historical_oos` — the exact latent breach B2 of the
iteration-5 audit named. Two things keep this narrow, which is why it is a GAP and not IMPORTANT:
the *fully* empty case self-heals (zero windows appends zero rows, so the guard stays false and the
next act retries — I confirmed this live: the below-floor CLI run left the exposure directory
completely empty), and `micro_readiness` surfaces integrity errors to the operator (real store:
`integrity_errors: []`). The playbook seed one line above has the same shape, so this is a
convention, not a regression.

**B3 — GAP: J-05's acceptance sentence "the tick-family fold request returns the typed
floor-refusal naming `11 < 105`" still has no production entry point**

`require_sufficient_sessions_for_folds` now has a real caller (`walkforward.py:1148`), but that call
site builds folds over the *playbook* corpus. Nothing in `app/` ever requests folds for the tick
family, so the `11 < 105` refusal exists only in `tests/test_walkforward.py:480`, over a synthetic
11-date list rather than the corpus's own dates. This iteration's DEFINITION OF DONE only asks for
"≥1 real call site" (met), so the checkbox is honestly closed — but the evaluator should not read
that as goal.md's J-05 acceptance sentence being met in production. Worth noting this is now cheap
to close: `_tick_dataset_session_dates` resolves the real 11 dates (I ran it: 2026-05-27 …
2026-07-13), so a tick-family request would produce a genuine `11 < 105`.

**B4 — OBSERVATION: the protection is coupled to a string, `"tick_legacy_symbol_days_v1"`**

`classify_evidence_class` (`walkforward.py:437`) matches exposure rows by `corpus_id`, so a future
tick-family spec registered under any other `corpus_id` reads an empty registry and classifies
`historical_oos` regardless of this iteration's seeding. The name is a disclosed implementation
choice (dev handoff, `walkforward.py:979`) and the plan authorised it, so this is not a defect —
but the seed protects a *string*, not the corpus, and whoever writes J-06/J-07's tick spec must
reuse it verbatim.

**B5 — OBSERVATION: "cheap" is not quite right, and the operator's real registry is still unseeded**

The dev handoff justifies the new `DatasetStore.list()` call as "cheap … metadata-only (no event
replay)". Measured against the real 882 MB store from a cold process: **28.3 s** (second call in the
same process: 0.000 s — the stat-keyed cache). The cost is bounded — it is paid at most once per
registry, only while the tick corpus is unseeded, and only inside an operator act (the CLI, or the
compute route's background worker; I confirmed `run_diagnostic_walkforward` has exactly two callers,
`micro_routes.py:323` and `walkforward.py:1221`, so no GET pays it and the era's "No scheduling"
non-goal holds). Related and worth recording: `.data/micro_exposure_registry` today still holds 154
playbook rows and **zero** tick rows — every proof of the seeding was against scoped copies (mine
and the dev's), so the real registry gets its 11 rows the next time an operator runs the act. That
is correct by design, not a gap, but it means "the registry holds tick-corpus entries" is true of
the mechanism, not yet of the operator's disk.

### Frontend Findings

None. This diff touches zero frontend files (`git status` and `git diff --stat` both confirm), and
`Frontend Present: yes` is a disclosed mechanical declaration to force the browser lane to
dispatch, not a UI claim.

### Evidence / Pipeline Findings

**E1 — IMPORTANT (gap, NOT fixable in audit scope): a P1 browser FAIL was silently converted into a
merged PASS by a parser defect**

The browser lane's own report records `**Browser QA Verdict:** FAIL` and a `**FAIL**` verdict cell
for UT-02. The merged artifact records PASS and "8/9 journeys passed". Root cause, reproduced
deterministically against these exact files:
`incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py:64` accepts a verdict cell only
when it equals one of the bare tokens `PASS`/`FAIL`/`SKIP`/`SKIPPED`; the cell is markdown-emphasised
(`**FAIL**`), so `parse_rows` returned `verdict=""` for that row, and `compute_overall`
(`:77-92`) fell through to the surviving PASS rows — the source file's own headline FAIL is
consulted *only* when no row parses at all. My reproduction:

```
UT-01 -> 'PASS'   UT-02 -> ''   UT-03..UT-08 -> 'PASS'
file_top_verdict: FAIL     compute_overall: PASS
```

Consequence: the "## Failed Tests" section the merge tool would normally emit was omitted, and every
downstream reader (QA, status.json's `qa_verdict`, the evaluator) sees a green headline over a red
row. Not fixed: `scripts/automation/**` is pipeline logic, which `.claude/maintenance-protocol.md`
§1 puts in the "edit only with a matching approved task, and every behavior change needs a
self-test" class — and the file's own self-test asserts the FAIL-wins rule while never exercising a
formatted cell, so the fix belongs with its missing test case. **The fix is one line** (normalise
the cell — e.g. `cu = c.upper().strip("*_` ")` before the membership test) **plus a self-test row
using `**FAIL**`.** Escalate to a framework-maintenance session; this is the same class of
silent-skip defect that cost iterations 4 and 5 their browser evidence.

**E2 — IMPORTANT (fixed in the record): the QA report re-graded that FAIL to PASS, cited two blank
screenshots as J-01's evidence, and claimed three unrun journeys as verified**

`reports/qa/goal-rapid-microscope-iter-6-qa.md` records UT-02 as "✓ PASS" with "1 symbol-day / 2
datasets (scoped test rig)", summarises "8/8 test cases passed (100%)", lists
`UT-02-microscope-readiness.png` / `-final.png` as the evidence, and asserts "Required-Still-Passing:
J-01, J-02, J-03, J-04 regressions all verified via browser checks above". Verified against the
artifacts: the browser lane recorded FAIL; `UT-02-microscope-readiness-final.png` is a 9.8 KB
uniform-navy image with no page content (I opened it — it is blank, exactly as the browser agent
warned in its Notes), the sibling file has no `.png` extension at all, and the merged results mark
UT-J-02/UT-J-03/UT-J-04 `DEFERRED-BUDGET` — "not run this iteration". A blank PNG offered as
acceptance evidence is precisely the `evidence_makeup` failure mode this era has been carrying since
iteration 3. **Fix applied:** an explicitly-marked auditor correction appended to the QA report
(original text preserved) naming the true verdict, the real evidence file
(`UT-02-fail.png`, 1668x3179, legible), and the honest coverage statement for J-02/J-03/J-04; plus a
short note appended to the merged results file pointing at E1. Verification of the fix: I re-parsed
the amended merged file with the merge tool's own `parse_rows`/`file_top_verdict` — twelve rows,
same verdicts, headline line untouched, no new parseable row introduced.

**E3 — IMPORTANT (gap, needs an owner ruling): J-01's `evidence_makeup` cannot be closed by the
rig this iteration is required to use**

The failure UT-02 reports is real, but it is an expectation defect in the UI test plan, not a
product defect. The plan (`reports/phase-goal-rapid-microscope-iter-6-ui-test-plan.md`, UT-02)
demands `distinct_symbol_days = 12`, `distinct_datasets = 18` and 18 shard rows while its own
preconditions mandate the store-scoped rig — and that rig seeds exactly two PG fixture datasets by
design: `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` copies
`tests/fixtures/datasets/{6c9bf2c7…,d9f9dbe0…}.json` and states in its own header that seeding "the
full 18-dataset/12-symbol-day corpus is deferred to whichever LATER iteration first needs it". Both
fixtures are PG, `2026-06-09` — exactly the 1 symbol-day / 2 datasets the browser saw. I confirmed
the product is healthy by calling the real path myself: `build_readiness` over `.data/datasets`
serves `{distinct_symbol_days: 12, distinct_datasets: 18, rth_minutes_covered: 1173.49,
session_equivalents: 3.0089, referee_tick_gate_symbol_days: 150}`, 18/18 shards `exploratory` +
`hand_assigned`, all three study floors `floor_unmet` at 11/60, `integrity_errors: []` — byte-equal
to what the iteration-5 evaluator recorded. So: the endpoint half of J-01's acceptance is verified;
the element-screenshot half is verified only against a two-shard fixture corpus, which is not "those
same served values" that goal.md's J-01 acceptance names. **This iteration's TC-8 is met as
written** (it asks only for "a real non-fabricated tick corpus" and a non-SKIPPED verdict, and
`UT-02-fail.png` genuinely shows checksums, coverage gaps, fallback fractions and floor-unmet
states). **J-01's own acceptance is not.** Not fixed here: closing it means either seeding the rig
from the real 18 datasets — which the launcher's own rule forbids ("never a pointer at, or copy of,
the real `.data/datasets` store") — or amending J-01's acceptance to accept an endpoint-level proof
beside a fixture-corpus render. Both are owner decisions, and inventing either is a T-1 breach.

**E4 — GAP: J-10's sentinel was exercised, but not by the deterministic replay lane**

`journey-scripts/J-10.json` was not modified (`git status` clean for that path despite a fresh
mtime — the browser agent rewrote it byte-identically), and I checked its 13 steps one by one
against the LLM lane's rows: steps 1-3 = UT-03, 4-7 = UT-04, 8-10 = UT-01/UT-05, 11 = UT-06, 12-13 =
UT-07, every expectation string matching verbatim (`300.11–302.2`, `config fingerprint
08e471b10130e1e2`, `No hypotheses registered`, `No evaluation runs recorded yet.`). So TC-9's
substance is genuinely met. What did not happen is a `demo_runner.py` replay of J-10.json itself —
the replay lane ran J-01 only (`…-regression-replay-results.md`: 1/1). Recording the distinction so
the next iteration's evidence-durability reasoning starts from fact.

### Test Findings

**T1 — OBSERVATION: the new tests are tight, and one of them earns particular credit**

TC-2 asserts the raise *and* that no `fold_result` row was written; TC-4 asserts a non-zero exit,
the exact `0 < 105` text, the `TR-15` marker, and — the assertion that actually proves the claim —
`captured.err == ""`, i.e. no traceback; TC-5 pins the exact window set `{2026-06-08, 2026-06-09}`
from three shards *and* that the playbook rows stayed at 155; TC-6 compares the count before and
after a second full run. No loose "assert result is not None" anywhere. The rewrite of the old
empty-store CLI test is correct rather than convenient: its previous assertion ("registers the fold
spec but evaluates zero folds") *was* the B5 defect, so preserving it would have pinned the bug.

**T2 — OBSERVATION: TC-5/TC-6/TC-7 build their corpora from string-shaped, non-calendar session
dates** (`f"2026-07-{d:03d}"` → `2026-07-001`…`2026-07-155`). Harmless — fold geometry treats
session dates as opaque sorted strings — and it keeps the fixtures cheap, but it means those tests
would not catch a future change that starts parsing session dates as real dates.

**T3 — OBSERVATION: hermeticity was verified, not assumed.** Every call site of
`run_diagnostic_walkforward` in the suite either passes `_FakeConfig` (whose `dataset_dir_resolved`
returns a deliberately non-existent path, and `DatasetStore.__init__` does no I/O — I checked no
stray directory is created) or sets `TAPEOLOGY_DATASET_DIR` to a `tmp_path`. The store-scope guard
independently reports CLEAN (11275 protected files unchanged), and my own re-verification left the
real ledgers byte-identical (`md5sum -c` on all four files: OK).

---

## 3. Domain Assessment

The domain logic here is small and it is right. The placement decision that matters — calling
`require_sufficient_sessions_for_folds` *after* `register_fold_spec` and *before* `build_folds`
(`walkforward.py:1138-1149`) — is the correct one and is defended in the code: the frozen geometry
is still committed to the ledger for a below-floor corpus (so the registration-first discipline
survives a refusal), while fold *evaluation* is refused with the typed shortfall instead of
`build_folds` returning `[]`. I confirmed this is not merely asserted: the live below-floor CLI run
left `{mode_b_spec: 1, fold_spec: 1}` on the ledger and zero `fold_result` rows, and
`register_fold_spec` (`walkforward_ledger.py:174-184`) treats an identical geometry as an idempotent
replay, so repeated refusals cannot grow the ledger.

The exposure-registry seed is likewise sound at the level that matters — granularity. The registry
keys exposure on `(corpus_id, window)` where `window` is a session date
(`micro_accessor.py:158`, `classify_evidence_class` at `walkforward.py:437`), and the real corpus's
12 symbol-days collapse onto 11 distinct ET dates (GOOGL and MSFT both trade 2026-07-13). Seeding
11 windows therefore covers all 12 protected symbol-days with no hole — I derived the pairs directly
from the 18 dataset files rather than trusting the count, and every symbol-day's date is present in
the seeded set. The ET derivation is the same technique `micro_accessor._session_date_for_dataset`
(`:105`) and `micro_readiness` (`:315`, `start_et.date()`) already use, so the seeded windows cannot
drift from the dates the operator sees.

The separation claim (TC-7) survives inspection rather than resting on the handoff:
`micro_readiness.py:351` writes the literal `EXPOSURE_STATE_EXPLORATORY` per shard and reads the
walk-forward registry nowhere, so seeding cannot move the served value — and the live real-store
read returns 18/18 `exploratory` after seeding a copy. The two mechanisms are genuinely separate.

Live re-derivation of the whole path, run by me against scoped copies of the real ledgers with the
real datasets/universe/bars read-only:

```
RUN 1: 5 fold(s) (0 newly recorded, 5 replayed), 100 validation session(s) over 154 corpus session(s)
RUN 2: identical; tick rows 11 -> 11 (idempotent); playbook rows 154 untouched
exposure chain {'ok': True}   walkforward chain {'ok': True}
tick windows: 2026-05-27 2026-06-02 2026-06-09 2026-06-22 2026-06-25 2026-06-26
              2026-07-06 2026-07-07 2026-07-08 2026-07-09 2026-07-13
CLI below-floor: exit=1, stdout "diagnostic walk-forward refused: 0 < 105 -- refused (TR-15) …", stderr empty
Config().config_fingerprint() -> 08e471b10130e1e2
all six referee_*.py SHA-256 -> byte-identical to the iteration-0 baseline listing
tests/test_walkforward.py + test_micro_accessor.py + test_micro_readiness.py -> 108 passed
```

Full-suite (3038 passed / 8 skipped / 0 failed) accepted on two independent executions — the
reviewer's own run (`reports/reviews/…-review.md`, `spec_alignment: complete`, `issues: []`) and
QA's archived log (`reports/qa/goal-rapid-microscope-iter-6-test.log`, final line `3038 passed, 8
skipped, 2 warnings in 527.28s`) — rather than a third nine-minute repeat.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `reports/qa/goal-rapid-microscope-iter-6-qa.md` | Appended a marked auditor correction (original text preserved): UT-02's true verdict was FAIL and why it is a test-plan expectation defect, not a regression; the cited J-01 evidence PNGs are blank and the real capture is `UT-02-fail.png`; J-02/J-03/J-04 were `DEFERRED-BUDGET`, not browser-verified. Verified by re-reading the artifacts named in each claim. |
| 2 | Important | `reports/phase-goal-rapid-microscope-iter-6-ui-test-results.md` | Appended a marked auditor note recording that the PASS headline is a `merge_ui_test_results.py` parse defect over a `**FAIL**` cell, not a resolved failure. Verified with the merge tool's own parser: 12 rows, unchanged verdicts, headline line untouched, no new parseable row. |

No code fix was applied: I found no CRITICAL or IMPORTANT defect in `walkforward.py` or its tests.
B1-B5 are gaps and observations whose fixes are either owner rulings or J-06 scope, and E1's fix
lives in `scripts/automation/**`, which the maintenance protocol reserves for an approved
framework-maintenance task with its own self-test.

---

## 5. Recommended Next Step

Proceed to J-06, with three items carried explicitly:

1. **Escalate E1 to a framework-maintenance session before the next browser-lane iteration.** This
   era has now lost browser evidence three iterations running to three different mechanical causes
   (`Frontend Present: no` short-circuit in iters 4-5; a FAIL→PASS merge parse this time). The
   phase spec's own Escalation flag anticipated exactly this. One line plus one self-test row.
2. **Get an owner ruling on E3 before J-01's `evidence_makeup` is called closed.** Either the rig
   gains the real 18-dataset corpus (which its own launcher currently forbids) or J-01's acceptance
   is amended to accept an endpoint-level proof against the real store beside a fixture-corpus
   render. Until then J-01's element-screenshot half should be recorded honestly as "photographed
   against the two-shard fixture rig; the 12/18/≈3.0 values verified at the endpoint, not on screen".
   The evaluator should not read this iteration's screenshot as closing that flag.
3. **Carry B1 into J-06's own scope as a hard prerequisite.** The moment the vault introduces sealed
   shards, "seed every currently-registered tick dataset" stops being safe, and the once-per-registry
   guard makes a wrong seed permanent.

J-05's two named gaps are closed and independently proven on the running program. J-10's frozen
half is re-verified and its sentinel content was genuinely exercised; its remaining traps
(TR-2/4/12/19/20) are J-06-owned, as the goal file itself says.
