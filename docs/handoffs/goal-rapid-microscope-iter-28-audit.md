# goal-rapid-microscope-iter-28 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Both halves of the iteration goal were genuinely delivered and independently re-verified by this
audit, not accepted on the handoffs' word: the two real-corpus test files now run in seconds
(I measured `106 passed ... in 9.28s` for both files plus both guards, against the 14m38s/27m57s
"before" the dev recorded), and the owner-ruled r5-point-7 disclosure sentence really is on the
live `/desk` page in the right place — I opened the screenshots and read the text myself. Three
things keep this off a clean PASS: the delivered TC-10 "the cache never masks a checksum failure"
guard is structurally incapable of failing (proven by deleting its premise and re-running) while
the property it names is, measured directly, **false** for the metadata path (fixed here by a new,
mutation-tested TC-10b that pins the real boundary); the QA report cites a 721-byte blank image as
proof of the caveat text (corrected here); and the suite's "finishability" is only two-thirds
solved — a third, unfixed real-corpus file still dominates the run.

---

## 2. Findings

### Backend Findings

**B1 — GAP (gap): the two fixed test files now write into the operator's LIVE production cache
DBs, and no store-scope guard covers those files.**

`apps/backend/tests/test_micro_readiness.py:512-518` and `:524-530`, and
`apps/backend/tests/test_micro_join.py:54-66`, resolve their durable paths to
`apps/backend/.data/dataset_index.db` and `apps/backend/.data/micro_readiness_cache.db` — the
exact files the running backend opens (`app/research/routes.py` `get_dataset_store()`;
`app/research/micro_routes.py:91`). The *result* correctness is sound and I verified it at the
source rather than trusting the handoff:

- `DatasetIndex.lookup` keys on `(path, size, mtime_ns)` and treats any stat difference as a miss
  (`app/research/dataset_index.py:92-99`), so a test can never read another store's row.
- `MicroReadinessCache` keys on the dataset **content checksum**, and its value
  `_compute_fallback_frac(events)` (`app/research/micro_readiness.py:175-193`) is a pure function
  of exactly that content — there is no second mutable input, so a row written by a test is
  byte-identical to the row the backend would have written. The iter-26 "cache with a second
  mutable input" lesson does not bite here.

The residual risk is the *second concurrent writer* this iteration introduces.
`datasets.py:_cached_meta` calls `index.insert(...)` **unguarded** (`app/research/datasets.py:424-426`);
unlike `MicroReadinessCache.publish`, which deliberately swallows `sqlite3.Error`
(`app/research/micro_readiness.py:279-291`), `DatasetIndex.insert` has no `except` — a lock
contention past the 5000 ms busy timeout would surface as an unhandled `sqlite3.OperationalError`
in whichever side lost (a test error, or a 500 from a live route). Writes only happen on a cache
miss (a new or re-stat'ed dataset file), so the window is narrow and nothing irreplaceable is at
risk — both DBs are derived, rebuildable, own-nothing caches. Worth recording alongside this: the
store-scope guard's protected-path list
(`reports/qa/goal-rapid-microscope-iter-28-store-scope-guard.md`) covers `.data/datasets` but not
`.data/*.db`, so its "the automated lanes wrote nothing into the operator's store" statement does
not cover this new write path.

Not fixed. The spec asked for "a PERSISTENT, gitignored on-disk cache path … reusing the SAME
production caching primitives", and sharing the production files is a legitimate reading of that
(`.data/` is gitignored — `git check-ignore` confirms `.gitignore:72`). A dedicated persistent
test-owned path (e.g. `.data/test_dataset_index.db`) would have removed the coupling entirely at
the cost of one cold warm-up; swapping it now is a design change the spec did not ask for and
would invalidate the dev's timing evidence.

**B2 — GAP (gap): the suite is still dominated by a third, unfixed real-corpus file, so the GOAL's
"without starving the live backend" is only partly achieved.**

`apps/backend/tests/test_micro_snapshots.py:483-489` builds `DatasetStore(dataset_dir)` against the
same real `CONFIG.dataset_dir` with **no** `index_db_path=`, then runs
`ms.run_snapshot_build_and_record` over the real corpus. It is the identical defect shape this
iteration fixed in the other two files, and it now carries essentially the whole remaining cost of
the run. Measured on my own end-to-end suite run (`--durations=25`, table below): `799.42s` +
`795.64s` (module-fixture setup) + `31.61s` = **1626.7s of the suite's 2023.75s — about 80% of total
wall clock — inside that one file**, while the two files this iteration fixed contribute 4.86s
(`test_micro_join.py`, rank 19) and nothing at all (`test_micro_readiness.py` does not reach the
top 25). The spec scoped IN SCOPE to exactly two named files, so
this is a documented limitation rather than scope failure — but it is the single highest-value
follow-up, and the phase GOAL sentence ("make the backend test suite finish reliably without
starving the live backend") is only satisfied in the "finishes" half.

**B3 — OBSERVATION (gap): `real_dataset_records`'s `assert errors == []` is now a cache-served
assertion.**

`apps/backend/tests/test_micro_readiness.py:531-534` still carries the comment "a real integrity
error here would be a repo-hygiene regression, not something this iteration's tests should silently
paper over." On a warm index that assertion no longer re-hashes unchanged files. It still catches
any real modification (an edit changes `mtime_ns` ⇒ index miss ⇒ full verify — I measured this, see
T1(c)); only a tamper that preserves both size and mtime slips past. Worth knowing, not worth
changing.

### Frontend Findings

**F1 — OBSERVATION (observation): the static-scan guard's "is actually rendered" check is weaker
than its docstring implies.**

`apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py:69-74` asserts only that
`{REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT}` appears *somewhere* in `page.tsx`. A reference inside a
comment or a dead branch would satisfy it; it does not check the render site is inside
`referee-evidence-strategy-block`. This round the real thing was covered live (UT-02 confirmed the
DOM child order `…-tick-gate → …-seal-unaware-caveat → …-basis-caveats`), so the weakness is latent,
not active. The constant is in fact used exactly once, at `apps/frontend/app/desk/page.tsx:5214`,
defined once at `:5028`.

**F2 — verified, no defect: the caveat is served at every site that serves the metric.** I grepped
for every render/serve path of `strategy_trade`: the only UI consumer of
`strategy_trade.dataset_count` / `per_split_counts` / `trade_count` is
`apps/frontend/app/desk/page.tsx:5177-5198`, and there is no MCP tool or proxy for
`GET /research/desk/referee/evidence`. The owner ruling's "wherever that metric is served" is
therefore fully covered by the one new `<p>`.

### Test Findings

**T1 — IMPORTANT (fixed): the delivered TC-10 cannot fail for the reason it claims, and the
property it names does not actually hold.**

`apps/backend/tests/test_micro_readiness.py:391-419` warms `shared_index_db` against
`tmp_path/other_datasets`, then plants the corrupted file in `tmp_path/scratch_datasets`.
`DatasetIndex.lookup` is keyed on the **absolute path** (`app/research/dataset_index.py:92-99`), so
the scratch store's brand-new paths are a guaranteed miss and the warmed rows can never be
consulted. I proved this rather than arguing it: I copied the test, deleted the entire `other_store`
warming block, and re-ran — `1 passed`, identical result. The premise is inert.

I then measured what the spec's error case actually asks about. With a warm index row for the
**same** path and a tamper that preserves both `st_size` and `st_mtime_ns` (a 64-hex-char checksum
swapped for another 64-hex-char string, `os.utime` restoring the mtime):

```
SIZE_MATCH True MTIME_MATCH True
ERRORS_AFTER_TAMPER []            <- DatasetStore.list() served the record, no integrity error
RECORDS_AFTER_TAMPER 1
CONTROL_ERRORS ['a3aed999….json'] <- the same tamper WITHOUT the durable index: correctly surfaced
```

So the spec's TESTING REQUIREMENTS line — "a corrupted dataset file must still surface as an
explicit `integrity_errors` row … even when the durable index cache is warm — the cache must never
mask a content-checksum failure" — is **false as literally stated** for the metadata path, and the
delivered test passes without touching that question.

Two things bound the severity, both measured in the same probe:

```
LOAD_EVENTS_RAISES: dataset file '608eda54….json' failed its integrity check …
AFTER_MTIME_BUMP_ERRS ['608eda54….json'] records 0
```

i.e. dataset **content** is never served from any cache (`load_events`/`replay` run the full
verifier on every call, `app/research/datasets.py:309-311`), and **any** stat change re-runs the
verifier and surfaces the corruption. This is pre-existing, documented era-fast_wall J-02 behaviour,
not something iteration 28 introduced — but iteration 28 is the round that claimed to have tested
it.

**Fix applied** (test-only, zero production change): added
`test_tc10b_warm_same_path_index_row_never_serves_tampered_content_and_re_verifies_on_any_stat_change`
to `apps/backend/tests/test_micro_readiness.py`, immediately after the existing TC-10, pinning all
three behaviours — (a) metadata may be warm-served when the stat is byte-identical, (b)
`load_events` still raises `DatasetIntegrityError` on the tampered file, (c) any stat change
surfaces `integrity_errors`. Evidence:

- `PYTHONPATH=. .venv/bin/pytest tests/test_micro_readiness.py -k "tc10" -v` →
  `3 passed, 48 deselected … in 0.42s`.
- Non-vacuity by mutation: replacing the tamper line with `path.write_text(original)` →
  `FAILED tests/…::test_tc10b_warm_same_path_index_row_never_serves_tampered_content_and_re_verifies_on_any_stat_change`,
  `1 failed`.
- Regression sweep after the edit:
  `pytest tests/test_micro_readiness.py tests/test_micro_join.py tests/test_datasets_api.py tests/test_dataset_index.py`
  → `125 passed … in 11.84s`; and
  `pytest tests/test_copy_discipline.py tests/test_micro_no_referee_evidence_guard.py tests/test_micro_readiness_seal_unaware_caveat.py tests/test_desk_ui_guards.py`
  → `119 passed … in 1.85s`.
- `git diff --stat apps/backend/tests/test_micro_readiness.py` after my edit: `126 insertions(+), 5
  deletions(-)` — the 5 deletions and 60 of the insertions are the developer's own diff; my
  addition is purely additive, no existing line touched.

I was unsure between IMPORTANT and GAP here and chose the higher one per the rubric: a guard that a
reader would reasonably believe covers the masking risk, but which cannot fail, is a spec'd test
contract that is not actually met.

**T2 — OBSERVATION (observation): the deterministic replay goldens are two-step scripts.**

Each of `J-02`/`J-03`/`J-04`/`J-09` is `goto /desk` + one section expand + one text assertion
(`runs/goal-session-rapid-microscope/journey-scripts/*.json`). That is why `J-02-verify.png` and
`J-03-verify.png` are byte-identical (`md5 b805ad04…`), as are `J-04`/`J-09` — both pairs end on the
same expanded section, so the duplicate images are legitimate, not fabricated. Pre-existing session
structure; nothing for this iteration to fix, but the "J-02..J-09 remain green" signal is thinner
than the row count suggests.

### Evidence / Process Findings

**E1 — IMPORTANT (fixed): the QA report cites a blank image as proof of the caveat text.**

`reports/qa/goal-rapid-microscope-iter-28-qa.md` (pre-correction lines 124 and 169) cited
`TC-05-caveat-text.png` as the evidence that the caveat renders. That file is 721 bytes; opened, it
is a background sliver showing a partial "BACK SCAN RUNS" header band and **none** of the caveat
text — the same headless element-clip blank-capture bug the browser-qa lane hit, diagnosed, and
worked around (its own report documents the workaround). This is a direct recurrence of the defect
class the phase spec made binding for this round ("open and read every screenshot they cite before
writing a claim about its content" — NOTES, lesson (a)); the QA lane narrated the caveat's text over
an image that does not contain it.

The *claim* is nonetheless true. I opened the artifacts that do support it:
`reports/qa/goal-rapid-microscope-iter-28-evidence/UT-02-result.png` is a genuine element-scoped
capture of the Strategy Family block with the sentence legible beneath the tick-gate line, and
`reports/demo/goal-rapid-microscope-iter-28/step-04.png` shows the same line in the running page.

**Fix applied:** both citations in the QA report are struck through and replaced with a labelled
"AUDIT CORRECTION (iter-28 auditor, finding E1)" note pointing at the two artifacts that actually
support the claim. The false statement is removed from the pipeline record; the original text is
left visible (struck through) so the defect itself is not erased.

**E2 — GAP (fixed-as-annotation): QA's J-01 capture is a stitched full-page shot carrying the exact
banned artifact.**

`TC-01-desk-full-page.png` does show the expanded Microscope Readiness section (corpus totals,
sealed tranche, legacy tick shards, pilot-study floors), so the underlying claim holds — but the
`Tapeology / Cockpit / Structure / Desk` nav bar is **duplicated mid-page**, immediately above the
Strategy Family block: the precise iter-27 stitch defect the spec banned as evidence. I annotated the
citation in the QA report rather than deleting the image. J-01's usable evidence for this round is
the browser-qa lane's `UT-05-result.png` — a single atomic capture with no duplicated header, which
I opened and read.

Note the DoD's first bullet asks for element-scoped captures for **both** targets. J-10's sentinel
evidence (`UT-06-result.png`) is genuinely element-scoped; J-01's `UT-05-result.png` is full-page but
atomic, not stitched — it does not carry the failure mode the ban exists to prevent, so I treat the
DoD bullet as substantively met with this note recorded.

**E3 — GAP (gap): two verification lanes were shed for budget and are honestly disclosed as such.**

`UT-J-07` is `DEFERRED-BUDGET` in `reports/phase-goal-rapid-microscope-iter-28-ui-test-results.md`
("not run this iteration", keeps its prior status), although J-07 is on the spec's
Required-still-passing list; the spec itself notes J-07 carries no golden by design, so replay
structurally cannot cover it. `reports/phase-goal-rapid-microscope-iter-28-ux-regression.md` is
`UX-REGRESSION-SKIPPED` (SPEED-15 trim rung 3b). Both are non-blocking and both say plainly what was
not done — the honest-disclosure bar is met; the coverage bar is not.

### Independent verification performed by this audit (not taken from any handoff)

| DoD / TC item | How I verified it | Result |
|---|---|---|
| TC-1/TC-2 warm-run speed, assertions unchanged | `PYTHONPATH=. .venv/bin/pytest tests/test_micro_readiness.py tests/test_micro_join.py tests/test_micro_no_referee_evidence_guard.py tests/test_micro_readiness_seal_unaware_caveat.py` | `106 passed … in 9.28s` (real wall clock `0m9.758s`) — vs the recorded 14m38s + 27m57s before |
| **TC-3** full suite completes with an explicit summary line, and neither fixed file is the largest contributor | Ran it myself end to end: `PYTHONPATH=. .venv/bin/pytest tests/ --durations=25` | `3480 passed, 8 skipped, 2 warnings in 2023.75s (0:33:43)`, `EXIT=0` — an explicit pytest summary, not a truncated process. Matches the dev's 3480/8 exactly. `test_micro_readiness.py` does not appear in the slowest-25 at all; `test_micro_join.py` appears once, at 4.86s (rank 19) |
| TC-3 corollary — where the time actually goes | Same run's `--durations=25` table | `test_micro_snapshots.py` alone: `799.42s` + `795.64s` (setup) + `31.61s` = **1626.7s of 2023.75s ≈ 80% of total suite wall clock** (finding B2) |
| TC-6 guard unmodified and passing | `git status --porcelain apps/backend/tests/` (file absent from the diff) + re-ran it | unmodified; 4/4 pass |
| **TC-7** referee byte-freeze | `sha256sum app/research/referee_*.py` compared line by line against `docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`, plus `git diff` on the path | 6/6 identical, empty diff |
| TC-4 caveat is verbatim and singular | Read `docs/rapid-validation-spec.md:1231-1233` and `apps/frontend/app/desk/page.tsx:5028`; grepped the constant | defined once (`:5028`), used once (`:5214`), character-for-character match including the em dash |
| **TC-5** caveat renders live, element-scoped | Opened `UT-02-result.png` and `step-04.png` myself and read the rendered sentence | confirmed rendered between the tick-gate line and the basis-caveats list (see E1 for the QA lane's broken citation) |
| J-01 / J-10 browser evidence | Opened `UT-05-result.png` (readiness section expanded, all four sub-blocks legible) and `UT-06-result.png` (element-scoped Referee Runs) | present; J-10's is element-scoped, J-01's is atomic-full-page (E2) |
| TC-11 passenger capture | Opened `UT-08-result.png` | element-scoped Scout Ledger family row, "— 1 variants tried" legible |
| TC-9 J-10 golden not weakened | Read `runs/goal-session-rapid-microscope/journey-scripts/J-10.json`; `git status` on the directory | step 12 still asserts `"variants tried"`; both goldens are content-unchanged (the lane rewrote them byte-identically) |
| Scope containment | `git status --porcelain apps/` | 3 test files + 1 frontend file; **zero** production backend code |

Honest caveat on that TC-3 row: the full-suite run was launched **before** I added TC-10b, so
`3480 passed` is the count for the delivered state exactly as handed off, not for the tree as it
stands after my fix. The tree after my fix is `3481` collectible tests; I re-ran the four files that
could be affected (`test_micro_readiness.py`, `test_micro_join.py`, `test_datasets_api.py`,
`test_dataset_index.py` → `125 passed in 11.84s`) plus the four guard/lint files
(`119 passed in 1.85s`) rather than paying another 34 minutes for a one-test delta.

---

## 3. Domain Assessment

**The disclosure (the product half) is correct and complete.** The owner ruling is served exactly
where the ruling requires and nowhere it forbids: `page.tsx:5028` defines the sentence once,
`:5210-5215` renders it inside the already-shipped `referee-evidence-strategy-block`, between
`referee-evidence-strategy-tick-gate` and `referee-evidence-strategy-basis-caveats`, under the new
and unique `data-testid="referee-evidence-strategy-seal-unaware-caveat"`. It is static copy — no
computed value, no request, no state — so the frozen `referee_*` modules keep their behavioural
freeze as well as their byte freeze. I re-hashed all six myself and compared against the
iteration-0 listing at `docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`: 6/6 identical,
`git diff` on `app/research/referee_*.py` empty. The text matches
`docs/rapid-validation-spec.md:1231-1233` character-for-character, em dash included, and I
confirmed the guard's own extraction regex targets that quoted sentence rather than a paraphrase.
`git status apps/` shows the entire iteration is three test files plus one frontend file — zero
production backend code, exactly as claimed.

**The cache reuse (the infra half) is sound in its result and slightly loose in its blast radius.**
The mechanism choice is right: no new cache class, both primitives content- or stat-keyed, both
derived and rebuildable, and the byte-identity of warm-vs-fresh service is already locked by an
existing passing test (`tests/test_datasets_api.py:295` — "a warm-cache response byte-equals a
response served after BOTH the in-process stat cache AND the durable sibling `dataset_index.db` are
forced cold"). The tight numeric assertions the speedup has to preserve — `distinct_datasets == 18`,
`session_equivalents == pytest.approx(3.0089)`, `playbook_signal_count == 2`,
`by_setup_id == {"range_trade": 2}` — all still hold on the warm path, so the acceleration did not
come from doing less work with weaker checks. What is loose is that the accelerator chosen is the
operator's own live DB rather than a test-owned durable file (B1), and that the one safety property
the spec named around it was tested with an inert premise (T1).

**Ambiguous data is surfaced honestly where it matters.** The dev handoff volunteers the `-q`
quiet-level interaction that suppressed a summary line, flags that no live browser render was done
in the dev pass, and lists TC-5/8/9/11 as explicitly *not* covered by it. The browser-qa lane
records the cockpit "Live tab is market-hours-gated" detour as an observation rather than quietly
routing around it, and documents the blank-element-capture bug and its workaround. That is the
standard the QA lane fell below in E1, and the reason E1 is graded IMPORTANT rather than cosmetic.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_micro_readiness.py` | Added `test_tc10b_warm_same_path_index_row_never_serves_tampered_content_and_re_verifies_on_any_stat_change` — the non-vacuous counterpart to TC-10, pinning that a warm same-path index row may serve stale METADATA, that `load_events` still raises `DatasetIntegrityError` on tampered CONTENT, and that any stat change re-surfaces `integrity_errors`. Additive only; no production code and no existing test line touched. Verified: `-k tc10` → 3 passed; mutation (tamper removed) → 1 failed; `125 passed` across the four related files. |
| 2 | Important | `reports/qa/goal-rapid-microscope-iter-28-qa.md` | Struck the two citations of the blank `TC-05-caveat-text.png` and replaced them with a labelled audit correction pointing at `UT-02-result.png` and `step-04.png`, the artifacts that actually show the caveat (both opened and read by the auditor). |
| 3 | Gap | `reports/qa/goal-rapid-microscope-iter-28-qa.md` | Annotated the `TC-01-desk-full-page.png` citation: the claim holds, but the image is a stitched capture with the banned duplicated nav header; J-01's usable evidence is `UT-05-result.png`. |

---

## 5. Recommended Next Step

Proceed. Both halves of the iteration goal are delivered, independently verified, and the two
IMPORTANT findings are fixed in place.

The one thing worth putting at the top of the next round's list is **B2**: apply the identical
`index_db_path=` treatment to `apps/backend/tests/test_micro_snapshots.py:483-489`. This round
removed roughly 42 minutes of real-corpus re-parsing from two files and left the third untouched, so
the suite still spends **about 80% of its 33m43s wall clock (1626.7s of 2023.75s, measured)** inside
that one file, doing exactly the work this iteration proved unnecessary — which is the same "starves
the live backend" condition that produced the blank and skipped screenshots in iterations 26 and 27.
It is a one-line change at a single construction site, with the pattern now proven twice.

Secondary, both cheap: give the two real-corpus test files their own durable cache paths under
`.data/` instead of the live backend's (B1), which removes the only concurrent-writer coupling this
iteration introduced; and extend the store-scope guard's protected-path list to cover
`.data/*.db` so that class of write is visible to the guard at all.
