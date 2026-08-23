# goal-rapid-microscope-iter-24 Audit Report

**Date:** 2026-08-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's primary goal — closing the sealing-time leak — was **half delivered as claimed and
half defective**, and both halves are now closed. The served channel genuinely narrows (verified
against the LIVE real vault store: all 21 sealed shards of `rapid-microscope-j06-starter` now serve
a bare `2026-08-21`, one indistinguishable bucket), but the automated check that was supposed to
make a future violation impossible was **vacuous against the real pre-iteration-24 data shape** —
fed a faithful reproduction of what `seal_shard` actually wrote before this round, it found zero
buckets and reported "safe" against exactly the leak it exists to catch. Separately, the shipped
`/desk` page rendered the newly coarsened date **one calendar day early with an invented ET time**
(`2026-05-01` → `2026-04-30 20:00 ET`) — reproduced live by browser-qa (UT-03 FAIL) and predicted
in writing by the ui-impact-analyst, then shipped anyway. Both are fixed in this audit with
executed tests and break-then-restore proofs. J-07 and J-09 re-verification, the J-09 golden, and
the J-08/J-10 collision reconciliation all hold up. What remains is evidence gaps, not code gaps.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the widened run-aware TR-2 check could not see the leak it was built for**

`apps/backend/scripts/j06_operator.py:793-806` (pre-fix) walked the RUN buckets and skipped any
bucket with `run_sealed_count <= 0` or `served_count <= 0`. The bucket key on the run side is
`str(run["at"])[:bucket_len]` and on the served side the served value verbatim. Those two strings
can only meet when the served precision is coarse enough for a shard's seal instant to share a
prefix with its run's `at`:

* a run's `at` is stamped once at the END of the run by `_utc()` — **second** precision
  (`2026-08-21T16:43:09Z`, 20 chars; confirmed by reading all five entries of the committed
  `reports/j06-tranche/recording-runs.json`);
* each shard's `sealed_at` is stamped per-seal by `vault._iso_utc_now()` — **microsecond**
  precision (`2026-08-21T16:42:19.876544Z`, 27 chars), because `stage_record` calls
  `vault.seal_shard(...)` at `j06_operator.py:369` with **no** `sealed_at` argument, so
  `vault.py:1224`'s `_iso_utc_now()` default applies.

So under the genuine pre-iteration-24 served shape, no served value ever prefix-equalled a run key.
Measured directly against the shipped code before the fix:

```
B) realistic OLD full-precision -> {"any_bucket_below_floor": false, "worst_bucket_candidates": null}, n_buckets = 0
```

`stage_tr2()`'s `ok` gate consults `not run_aware["any_bucket_below_floor"]`
(`j06_operator.py:890`), so a reverted or drifted precision would have passed the widened check
silently — precisely the failure the phase spec named ("make `stage_tr2()` compute this channel so
a future violation cannot pass silently", spec BACKGROUND).

**Fix applied.** The bucket walk is now keyed on the **served** buckets, not the run buckets, and
no bucket is skipped (`j06_operator.py`, `residual_pool_uncertainty_by_run_time_bucket`). The
attacker's starting point is a served `sealed_at` value, so every served value must sit in an
anonymity set of ≥ 2 — including one no run's own bucket claims. `sealed_this_run_total` stays in
the record (0 when unclaimed, itself worth reading) but no longer gates. The floor number is
unchanged (`>= 2`); the docstring paragraph that described the old behaviour was corrected in the
same hunk.

**Post-fix evidence** (all commands re-run, results below in §4):
* Real live store, read-only through `vault.build_vault_state`: 21 sealed shards, histogram
  `{'2026-08-21': 21}`, verdict `any_bucket_below_floor: false`, `worst_bucket_candidates: 21` —
  TC-3 satisfied against the real state, not only a reconstruction.
* Realistic old shape: `any_bucket_below_floor: True`, `worst: 1`, 21 buckets — the check now bites.
* The dev's own counter-test fixture still bites (`True`, worst 1, 3 buckets), so no existing test
  was weakened.

**B2 — OBSERVATION: `candidate_identities_per_unexposed_selected_shard` means two different things
in the two halves.** In the combinatorial half (`j06_operator.py:803`) it is the number of
candidate `(symbol, session_date)` identities. In the run-aware half it is the number of served
shards sharing a bucket. The latter is ≤ the former (a bucket's true identity candidates are all
pairs recorded in the runs that claim it), so the shared floor is applied in the conservative
direction — it can over-flag, never under-flag. Honest and safe, but the reused key name invites a
misreading of the operator artifact. Not fixed (naming only).

**B3 — OBSERVATION: `referee_evidence.py:286` reads `signal["side"]` with no defensive default.**
This is what 500'd `GET /research/desk/referee/registry/shortlist` while the dev was wiring the
J-09 seeder. I verified the dev's claim that no production path can reach it: all seven signal
constructions in `app/research/desk_playbook_detect.py` (lines 380, 598, 877, 1082, 1367, 1616 plus
the shape-anchor merge at 143) stamp `side`, and `playbook_occurrence_readiness` `continue`s past
any record not at the live detector basis. The seeder's `"side": "long"` addition is therefore a
fixture-correctness fix, not a mask over a live bug. Referee modules confirmed byte-frozen (below).
Not fixed — `referee_*` is byte-untouched this era by anti-goal.

### Frontend Findings

**F1 — IMPORTANT (fixed): the coarsened `sealed_at` rendered as the previous calendar day plus an
invented time**

`apps/frontend/app/desk/page.tsx:6801` (pre-fix) rendered the Validation Vault "Sealed at" cell as
`formatDateTimeET(shard.sealed_at, { seconds: false })`. That is the **instant** formatter. Since
this iteration the field is a bare day marker, and `new Date("2026-05-01")` parses as UTC midnight,
which in US-Eastern is the **previous** day at 19:00/20:00. `apps/frontend/lib/datetime.ts:132-148`
already documents this exact trap and ships `formatDayMarker` for it ("It names a DAY, not an
instant, so it is read LEXICALLY … a value with no clock at all would acquire a `20:00:00` that was
never in the record").

Reproduced independently with the app's own `etParts`/`formatDateTimeET` logic:

| served value | old rendering | new rendering |
|---|---|---|
| `2026-05-01` | `2026-04-30 20:00 ET` | `2026-05-01` |
| `2026-06-09` | `2026-06-08 20:00 ET` | `2026-06-09` |
| `2026-01-15` | `2026-01-14 19:00 ET` | `2026-01-15` |

The first row is byte-identical to what browser-qa photographed live
(`reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png`, UT-03 **FAIL**).

This defeats **DEFINITION OF DONE item 1** as written ("the Validation Vault section renders sealed
shard rows with the new date-only `sealed_at` precision") and partly undoes the iteration's own
stated intent — the column still showed a time-of-day, just a wrong and fabricated one. The
`ui-impact-analyst` wrote it up in full before browser-qa ran
(`reports/phase-goal-rapid-microscope-iter-24-user-visible-changes.md:39-60`); browser-qa then
reproduced it live; nothing in the dev/review lane acted on it. This is squarely inside the phase
spec's own Frontend IN SCOPE clause ("If a real rendering issue surfaces only against the
now-coarsened value … fix it as the smallest possible change").

**Fix applied.** One call site swapped to `formatDayMarker(shard.sealed_at)` (already imported at
`page.tsx:163`), with a comment recording why. The neighbouring `assigned_at`/`exposed_at` cells
are still genuine full-precision instants and deliberately keep `formatDateTimeET`.

**F2 — GAP: no fresh browser screenshot exists for the fixed rendering.** The scoped QA rig
(:8301/:3301) was already torn down when this audit ran (`curl` to both ports returns no
connection), so the F1 fix is proven at source, formatter, typecheck and regression-test level but
not re-photographed. See §5.

### Test Findings

**T1 — IMPORTANT (fixed): the non-vacuity counter-test proved nothing about the real join**

`test_iter24_the_same_widened_check_correctly_FAILS_against_the_old_full_precision_join`
(`apps/backend/tests/test_j06_operator.py`) builds its "OLD full-precision" fixture as
`served.extend([run["at"]] * run["sealed_this_run"])` — i.e. each shard's served value is literally
its own run's `at` string. That alignment cannot occur in production (see B1: different stamping
function, different precision, different instant), and it is what made the check appear to bite.
The test's own docstring calls this "a synthetic reproduction of the OLD, pre-iteration-24
full-precision `sealed_at`", which it is not. Spec **TC-4** asks for a fixture "reproducing the OLD
full-precision `sealed_at` join"; this did not reproduce it.

**Fix applied.** Added
`test_iter24audit_the_widened_check_also_fails_against_a_REALISTIC_old_full_precision_shape`, which
reconstructs what `seal_shard` actually wrote — distinct microsecond-precision instants shortly
before each run's own `at`, asserted distinct from every run key — and proves the widened check
reports `any_bucket_below_floor: True`, `worst_bucket_candidates == 1`, 21 buckets each of size 1.
The original counter-test is left in place (it still passes and still covers its own case) with the
new one beside it; the function docstring was corrected to describe the real behaviour.

**T2 — GAP: the deterministic replay lane never executed `J-06.json` or the new `J-09.json`.**
`reports/phase-goal-rapid-microscope-iter-24-regression-replay-results.md` records **7/7** — J-01,
J-02, J-03, J-04, J-05, J-08, J-10, i.e. exactly the spec's "Required-still-passing" list. Nine
stored goldens exist in `runs/goal-session-rapid-microscope/journey-scripts/`. So DoD item 3's "AND
via the new stored golden replay script" and item 4's "full stored replay set re-run" rest on the
dev handoff's own claim of a 9/9 local run plus browser-qa's manual re-walk of J-09.json's two
steps (`ui-test-results.llm.md`, UT-06: "its two steps … reproduce exactly what this browser
session just did"). That is corroboration, not an independent harness execution. Not fixable in
this audit without relaunching the rig; recorded as a gap. Mitigating evidence I did verify
directly: the golden's assertion string is real and discriminating —
`scout_ledger.derive_family_id("failed_aggression_score", "playbook_signal", "trades_20")` returns
`failed_aggression_score__playbook_signal__trades_20` exactly, and Study 1's grid
(`scout.pilot_study_candidate_grid`, `structure_context_kind="band_touch"`) derives a *different*
family id, so the string is unique to Study 3.

**T3 — GAP: DoD item 1's "no per-shard symbol/date visible for any still-sealed shard" could not be
observed in the browser this round.** The scoped rig's vault holds exactly ONE shard, already in
`exposed` state (`readiness.sealed_tranche.shard_count: 0`), so UT-05 was correctly SKIPPED and the
date-only rendering was observed on an `exposed` row only. The property itself is enforced
server-side by `_serialize_shard`'s per-state whitelist and is covered by
`test_tc6_a_sealed_shards_entry_carries_only_the_section_7_5_opaque_fields` and
`test_tr2_no_registered_get_route_serves_or_derives_a_sealed_shards_identity` (both green), so this
is an evidence gap, not a behaviour gap.

**T4 — OBSERVATION: J-08 step 3 and J-10 step 12 lost their empty-state assertion.** Both swapped
`"No candidates ledgered."` for `"Ledger chain verification:"`. The swap is spec-sanctioned (TC-7
allows "an updated, order-independent assertion") and reuses J-04's existing convention. It is
strictly weaker: the substitute string occurs **twice** in `page.tsx` (`:6282` Scout Ledger,
`:6518` Walk-Forward). It still discriminates today only because `CollapsibleSection` does not
render a closed body (`apps/frontend/components/CollapsibleSection.tsx:57`) and both scripts expand
Walk-Forward *after* the step in question (J-08 step 4, J-10 step 13). Reorder either script and the
assertion becomes satisfiable without the Scout Ledger opening at all. No journey now asserts the
Scout Ledger empty state anywhere.

**T5 — OBSERVATION: `J-06.json` is a two-step golden that never touches the Validation Vault.** Its
only real assertion is `"No integrity errors."` in the Microscope Readiness section — nothing about
shards, sealing, or opacity, i.e. the surface this iteration changed. Pre-existing; out of scope to
fix here, but worth noting since J-06 is a *target* journey this round.

---

## 3. Domain Assessment

**The r5 opaque-pool property.** The served channel is now genuinely single-doored and narrowed. I
grepped every occurrence of `sealed_at` outside tests across `apps/`: it reaches the outside world
through exactly one projection, `vault._serialize_shard` (`vault.py:1534-1535`), fed by the one
served body builder `build_vault_state` (`vault.py:1687`). Coarsening `opaque["sealed_at"]` once,
before the `revealed = {**opaque, ...}` merge, is what makes the narrowing uniform across
`sealed`/`assigned`/`exposed` without a second call site to forget — a sound structural choice.
`micro_readiness.py`'s `sealed_tranche` is aggregate-only (counts and symbol-day counts, no
timestamps), so there is no second time-shaped door. The stored ledger row is untouched, proven by
`test_tc2_...` reading `shard_ledger.all_rows()[0]["sealed_at"]` directly and asserting the exact
microsecond string. Append-only discipline holds; the committed
`reports/j06-tranche/recording-runs.json` is byte-untouched (`git status` on
`reports/j06-tranche/` is empty), honouring the OUT OF SCOPE line.

Against the live real store the margin is now large: every one of the 21 still-sealed shards serves
the same `2026-08-21`, and four of the five recorded runs fall on that day — so the join the
iter-23 auditor used to narrow one shard to 4 candidates now cannot separate any shard from the
other 20, and the candidate identity set is the union of all pairs those four runs recorded. The
"minor open item" is closed on the channel side, and after B1 it is closed on the monitoring side
too.

**The new tests are tight.** `test_vault.py`'s three additions assert exact values
(`== "2026-06-09"`, `== explicit_sealed_at`), not shapes-only, and TC-9 walks the shard through
`seal → assign → expose` re-reading all rows each time. That is the right level of rigour. The
weakness was concentrated in the one counter-test (T1), which is exactly the kind of test that
passes for the wrong reason — the failure mode this era's own iter-21/22 lessons warn about.

**The J-09 golden's design is sound.** The seeder calls the real production entry point
(`scout.register_screen_and_walkforward_check`) rather than writing a JSON blob, is wired into the
rig launcher in place under `set -euo pipefail` (so a seeding failure aborts the rig loudly rather
than silently serving an empty ledger), reuses the already-staged real PG SIP dataset, and asserts
on `family_id` rather than the store-nondeterministic `candidate_id`. The dev's reasoning for that
choice is verifiable and correct. The one non-vacuity risk — that the family id might collide with
Study 1's — I checked and it does not.

**Scope.** The diff matches the spec exactly. No sealed-shard exposure/assignment, no Referee
change (all six `referee_*.py` SHA-256 hashes diff byte-identical against the iteration-0 baseline
listing in `docs/handoffs/goal-rapid-microscope-iter-0-dev.md:76-81`), fingerprint still
`08e471b10130e1e2`, `EXPECTED_TOOLS` still 26, `micro_graduation.py`/`micro_sealed_evaluation.py`
untouched since `ab075a5`/`765a187` (`git status` empty for both) — so J-07's evidence-durability
premise holds.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/scripts/j06_operator.py` | `residual_pool_uncertainty_by_run_time_bucket` now walks the SERVED buckets instead of the run buckets and skips none, so a full-precision (or otherwise unattributable) served `sealed_at` yields an anonymity set of 1 and trips the `>= 2` floor instead of vanishing. Same floor, same `SystemExit` contract, docstring corrected. |
| 2 | Important | `apps/backend/tests/test_j06_operator.py` | Added `test_iter24audit_the_widened_check_also_fails_against_a_REALISTIC_old_full_precision_shape` — reconstructs what `seal_shard` actually wrote (distinct microsecond instants, asserted disjoint from every run key) and proves the check reports 21 buckets of size 1, below the floor. Added the `datetime` import it needs. |
| 3 | Important | `apps/frontend/app/desk/page.tsx` | Validation Vault "Sealed at" cell: `formatDateTimeET(shard.sealed_at, { seconds: false })` → `formatDayMarker(shard.sealed_at)`, fixing the one-day-early date and the invented 19:00/20:00 ET time. One call site; neighbouring instant columns untouched. |
| 4 | Important | `apps/backend/tests/test_desk_vault_sealed_at_day_marker_guard.py` (new) | Source-introspection guard (the repo's own `test_desk_touch_time_et_guard.py` pattern) pinning the day-marker formatter on `sealed_at`, with a seeded pre-fix counter-test and a scope pin that `assigned_at`/`exposed_at` keep the instant formatter. |

**Verification run for every fix (commands and results):**

* `cd apps/backend && taskset -c 4-7,12-15 .venv/bin/python -m pytest tests/test_j06_operator.py tests/test_vault.py -p no:cacheprovider` → **118 passed** (117 before, +1 from fix 2).
* `... -m pytest tests/test_desk_vault_sealed_at_day_marker_guard.py -q` → **3 passed**.
* **Break-then-restore on the new guard (fix 4 proving fix 3):** re-inserted the literal pre-fix
  line → `FAILED tests/test_desk_vault_sealed_at_day_marker_guard.py::test_the_vault_sealed_at_cell_renders_the_day_marker_lexically`;
  restored from a saved copy → `diff` reports byte-identical, **3 passed** again.
* **Empirical proof of fix 1**, run against the patched function:
  `A) real coarsened -> any_bucket_below_floor: false, worst: 21` ·
  `B) realistic OLD full-precision -> any_bucket_below_floor: True, worst: 1, 21 buckets` (was
  `false` / 0 buckets before the fix) · `C) dev's own counter-test fixture -> True, worst: 1`.
* **Fix 1 against the LIVE real store** (`vault.build_vault_state` on
  `CONFIG.dataset_dir_resolved()`, read-only): 21 sealed shards for
  `rapid-microscope-j06-starter`, served histogram `{'2026-08-21': 21}`, verdict
  `{"any_bucket_below_floor": false, "worst_bucket_candidates": 21}` — TC-3 met against real data.
* **Fix 3 behavioural proof:** the app's own `etParts`/`formatDateTimeET`/`formatDayMarker` logic
  run under node on `2026-05-01` / `2026-06-09` / `2026-01-15` (table in F1); the first row matches
  browser-qa's live capture exactly.
* `cd apps/frontend && ./node_modules/.bin/tsc --noEmit -p tsconfig.json` → **exit 0**.
* **Frontend-source guard regression sweep** (21 suites that read `app/desk/page.tsx` as text —
  `test_desk_ui_guards`, `test_copy_discipline`, `test_desk_run_stamp_guard`,
  `test_desk_touch_time_et_guard`, `test_desk_topup_library_reach_guard`, `test_referee_registry`,
  `test_fingerprint_epoch_retirement`, …) → **379 passed**.
* **Targeted era suite** (the dev's own 17 files plus the new guard, `-k "not test_tc12"`, the same
  real-corpus deselect the dev used) → **620 selected, 620 passed, 0 failed, exit 0** (620 progress
  dots, zero `F`/`E`/`s` characters in the log; the dev's own comparable run was 617 before my
  four added tests).
* `git diff` on all four touched files re-read: the hunks contain only what B1/F1/T1 required — no
  incidental edits, no behaviour change outside the two call sites.

Two claims in the dev handoff are invalidated by these fixes and should be read with this report
beside them: (a) "the non-vacuity counter-test … proves it correctly FAILS" — it proves the logic
fails on an alignment that cannot occur, not on the real old shape (T1); (b) "No code changes
expected" for the frontend — one was needed and is now made (F1).

---

## 5. Recommended Next Step

**Proceed**, with two things carried into the next round rather than re-opened here:

1. **Re-photograph the Validation Vault "Sealed at" cell.** Relaunch
   `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` plus the frontend and re-run
   UT-03 alone; it should now read a bare `2026-05-01`. Cheap, and it is the one piece of evidence
   this audit could not capture (F2). Bundle it with a re-run of the FULL nine-golden replay set so
   `J-06.json` and `J-09.json` stop resting on a dev-local claim (T2) — the pipeline's replay lane
   currently drives only the seven "required-still-passing" scripts, which is worth fixing in the
   lane itself, not per-iteration.
2. **Consider seeding one still-`sealed` shard into the QA rig.** Every browser round for the last
   three iterations has been unable to test the r5 opacity property that J-06 exists to protect,
   because the rig's only shard is already `exposed` (T3). One extra `seal_shard` call in the
   iter-18 seeder would make UT-05 executable and give J-06's own golden something to assert
   (T5).

The three remaining `OBSERVATION`s (B2 naming, B3 defensive read, T4 weakened empty-state
assertions) are documented limitations, not work items — fixing them here would be scope creep.

With B1/F1/T1 closed, the sealing-time leak is closed on **both** halves independently confirmed:
the channel is narrowed at the single serve-time door (real-store verified), and the automated
check now fails loudly on the shape that used to slip past it.
