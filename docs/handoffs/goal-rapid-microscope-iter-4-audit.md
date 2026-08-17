# goal-rapid-microscope-iter-4 Audit Report

**Date:** 2026-08-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-04's Scout and hash-chained candidate ledger are genuinely built, not stubbed: TR-8's 200-seed
calibration is a real calibration with a real counter-test, TR-9's ordering refusal is enforced by
construction, the `quote_depletion` exclusion is structural rather than a policy flag, and both
`micro_join.py` passenger fixes are correct and tightly tested. But four IMPORTANT integrity faults
survived review and QA — all of them in the ledger's own tamper/denominator contract, which is the
one thing this journey exists to guarantee — and I fixed all four with regression tests: the
serving path never verified the hash chain (a `killed_null` edited to `survive` on disk was served
as a survivor), a truncated tail was undetectable (the denominator could silently shrink), a
re-run of the identical grid inflated the served union-N and permanently bricked the compute
endpoint after 12 runs, and the shares/clock-horizon screening path shipped with a null block
shorter than its own label span. One IMPORTANT gap I cannot close remains: TC-20 was never
executed — browser QA recorded a blanket SKIP, so J-01/J-02/J-03 were not re-verified and **J-10's
kept-product sentinel was not run at all**, on the iteration whose regression set was deliberately
widened after an ESCALATE.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): `GET /research/desk/micro/scout` served a tampered ledger silently**

`micro_routes.py:176` (`get_scout`) read the ledger through `scout.list_scout_families` →
`ScoutLedger.all_rows()`, which is the deliberately unverified "plain reader"
(`scout_ledger.py:216`). A repo-wide grep found `verify_chain` referenced by **nothing but
`tests/test_scout_ledger.py`** — no production or serving path ever called it. The phase spec's
TC-3 does not only require the primitive to work; its own second clause is *"and no code path
silently accepts the tampered chain."*

Verified directly, not inferred — I tampered a ledger on disk and read it back through the exact
body of the route:

```
tampered verify: {'ok': False, 'failed_at_row': 1, 'reason': 'content_hash_mismatch'}
SERVED after tamper -> decisions: ['survive', 'survive', 'killed_economic']  variants_tried: 3
```

A kill rewritten into a survivor was served as a survivor, with nothing in the payload hinting
anything was wrong.

The test that claims to cover this clause,
`test_tc3_no_code_path_silently_accepts_a_tampered_chain` (`tests/test_scout_ledger.py:192`), only
re-asserts `verify_chain()`'s own return value; it never exercises any other code path, so the
clause was untested as well as unimplemented.

*Fix applied:* the route now serves `chain_verification` (`ScoutLedger.verify_chain()` verbatim)
beside `families` — surfaced rather than refused, the same discipline this iteration's own
`playbook_integrity_errors` passenger fix chose for a corrupt playbook record. Regression test
`test_tc3_the_scout_route_never_serves_a_tampered_ledger_without_saying_so`
(`tests/test_scout.py`).

**B2 — IMPORTANT (fixed): a truncated ledger tail was undetectable — the denominator could
silently shrink**

`scout_ledger.py`'s module docstring claimed: *"deleting or reordering rows breaks the `prev_hash`
pointer at the first row whose predecessor no longer matches."* That is true for a MID-FILE
deletion and false for the tail. Verified directly:

```
after TAIL truncation -> verify: {'ok': True, 'failed_at_row': None, 'reason': None}
after TAIL truncation -> variants_tried: 2          # was 3 before a kill row was erased
```

Erasing the most recent kill left a chain that verifies perfectly clean and a denominator one
smaller — a direct breach of the era's critical anti-goal *"The denominator never shrinks. …kills
are never deleted"*, and of the plan's own build note (`plan.md:49`) that chain verification
"should also catch deletion/reordering, not only in-place edits."

*Fix applied:* `append_row` now maintains a durable `chain_head.json` tail anchor
(`{"row_count", "head_hash"}`), written **after** the row it commits to so the crash window can
only ever leave the ledger longer than the anchor, never falsely short. `verify_chain` walks the
chain first (every existing exact-equality assertion preserved) and then checks the anchor,
reporting `tail_truncated` at the first missing index, or `head_anchor_missing` on a non-empty
ledger with no anchor — an honest "completeness cannot be certified", never a silent pass. The
false docstring claim is corrected. Four regression tests in `test_scout_ledger.py` plus the
route-level `test_the_scout_route_reports_a_truncated_ledger_tail`.

**B3 — IMPORTANT (fixed): `variants_tried` counted evaluations, not variants — inflating the
served denominator and permanently bricking `POST /scout/compute` after 12 runs**

`ScoutLedger.variants_tried_for_family` was `len(rows_for_family(...))` — a count of ledger ROWS.
`register_and_screen_candidate` reads that same number for the `SCOUT_MAX_VARIANTS_PER_FAMILY`
cap. Because the compute route registers the identical `spec_hash`es (hence identical
`candidate_id`s) on every run, each run added rows without adding variants. I ran the default grid
repeatedly against the committed fixtures:

```
run  1: OK  rows_total=  6  variants_tried={'cumulative_delta__none__trades_20': 2, ...}
run 12: OK  rows_total= 72  variants_tried={'cumulative_delta__none__trades_20': 24, ...}
run 13: RAISED ScoutGridExhaustedError: family 'cumulative_delta__none__trades_20' already
        carries 24 variants … SCOUT_MAX_VARIANTS_PER_FAMILY=24 is a hard bound
```

Two faults, one cause. (a) The 13th operator click of an operator-facing endpoint refuses forever,
and the only "recovery" — pruning the ledger — is exactly what the append-only anti-goal forbids.
(b) The served best-of-N disclosure sentence reads *"with n=24 variants tried in this family (union
across grid versions)"* when 2 variants had ever been tried. `docs/rapid-validation-spec.md:77`
defines the bound as *"per (family, corpus), counted over the UNION of all grid versions ever run
there"* — a union of variants, not a tally of evaluations, which is also the statistically correct
multiple-comparisons denominator for an era about calibration.

*Fix applied:* new `scout_ledger.distinct_variant_count(rows)` counts distinct `candidate_id`
(itself `cand-<spec_hash[:16]>`, a pure content hash of the frozen spec); a row carrying no
`candidate_id` has no variant identity and counts individually, which preserves the spec's own
illustrative TR-11 arithmetic (40 + 25 ⇒ 65) and TC-9's cap scenario exactly. Used by
`variants_tried_for_family`, by `append_row`'s stamp, by `register_and_screen_candidate`'s cap
check and best-of-N input, and by `list_scout_families` (which now computes rather than re-reads
the last row's stamp, so a tampered row can no longer dictate the served denominator). **No row is
ever suppressed** — every evaluation stays permanently on record; only the COUNT changed.
Regression tests in both test files, including a 13-consecutive-run test that used to brick.

**B4 — IMPORTANT (fixed): the shares/clock-horizon screening path shipped with an
anti-conservative null and no subsampling**

`scout.py`'s `_block_length_for_horizon` returned `MICRO_HORIZON_TRADES[0]` (20 events) for every
shares and clock horizon, documented in the dev handoff as "a conservative floor". It is the
opposite of conservative. Spec §5.3 requires *block length ≥ the label span in EVENTS of the
longest horizon evaluated*; a `clock_seconds_300` horizon on an actively-traded session spans
hundreds to thousands of trades (the handoff's own NVDA figure is ~929K trades in one session), so
a 20-event block is far SHORTER than the label span. A too-short block destroys the local run
structure the block design exists to preserve, narrows the null, and makes `p_screen`
**anti-conservative** — precisely the failure TR-8's calibration trap and the plain-shuffle ban
exist to prevent, now reachable through a supported, callable path whose results are permanently
ledgered.

Compounding it: §5.3's *"Clock-horizon effects additionally use non-overlapping anchor subsampling
(every anchor at least one horizon apart within a session, seeded selection)"* — an explicit IN
SCOPE bullet of this phase spec and of `plan.md` — is **absent entirely** (`grep -n
"subsampl\|non-overlap" app/research/scout.py` → nothing), and is not disclosed anywhere in the
dev handoff's own list of interpretation calls. No test exercises any non-trade horizon: every
`horizon_key=` in `tests/test_scout.py` is `trades_20`.

*Fix applied:* sizing the block from the data and wiring the subsampling are methodology decisions
this iteration's spec fixes but does not authorize inventing (T-1). So the module now **refuses**
the horizons it cannot block-size honestly — a typed `ScoutUnsupportedHorizonError` raised both at
the registration boundary (before any corpus read or ledger write) and inside
`_block_length_for_horizon` itself, following this module's OWN precedent (`extract_anchors`
already refuses a `structure_context.kind` it has no read path for). Nothing this iteration
registers is affected: `default_fixture_grid` is trade-count-only by construction, where the block
length equals the label span exactly. Seven regression tests, including that a trade-count horizon
still screens normally and that a refused candidate writes no ledger row.

**B5 — GAP: the cap/denominator bucket omits the corpus the spec's own constant names**

`docs/rapid-validation-spec.md:77` defines `SCOUT_MAX_VARIANTS_PER_FAMILY` as a *"hard grid bound
per (family, **corpus**)"*. `scout_ledger.derive_family_id` (`scout_ledger.py`) is
`f"{feature_name}__{structure_context_kind}__{horizon_key}"` — no corpus term — so variants tried
on one corpus consume the cap for, and pool into the served denominator of, an entirely different
corpus. The deviation is in the conservative direction (the cap is stricter than spec, the
denominator never understated), so nothing served today is dishonest; but it is a divergence from a
frozen §1 constant's own definition and belongs to the spec owner, not to an auditor — redefining
`family_id` would rewrite the grouping key on every row already ledgered. Left as filed.

**B6 — OBSERVATION: the block-permutation null's seed scope is the family, not the candidate**

`_null_effect_draws` builds its stream as `scout_stream(family_id, "block-null",
fold_or_origin=session_date)`, so every candidate in a family shares one rotation sequence, and
`SCOUT_STREAM_RECIPE`'s own trailing `[:{i}]` per-item segment is never used by any caller. This is
deterministic and defensible (common random numbers across siblings aids comparability), but it
does mean sibling candidates' `p_screen` values are positively correlated, and the recipe's final
segment is dead in practice.

**B7 — OBSERVATION: a `killed_insufficient_n` row's best-of-N sentence reads "approximately None
bps"**

When `insufficient` short-circuits the screen, `_best_of_n_disclosure([], n)` is served with
`corrected_threshold_bps: None`, and the composed sentence renders `…is approximately None bps`.
Honest (there is no null distribution to quantile), but it is prose destined for a rendered surface
in J-08.

**B8 — OBSERVATION: the manager's ledger writes are per-candidate, not "terminal-state-only"**

The dev handoff and the spec's IN SCOPE bullet both describe "terminal-state-only ledger writes".
`run_scout_grid_and_record` appends one row per candidate as it goes, so a mid-run exception leaves
a partial grid on disk. I judge the behaviour CORRECT — each row is a complete, permanent record of
one genuine evaluation, and `_resolve_terminal` discloses the shortfall in the run log
(`candidates_done` vs `candidates_total`, `state: "failed"`) — but the claim as written does not
describe the code. `MicroSnapshotComputeManager`'s own discipline is per-DATASET completeness, which
this does mirror at the per-row level.

### Frontend Findings

**F1 — none.** Frontend Present: no, and verified so rather than assumed: `grep` for
`joinable_corpus`, `band_touch_count`, `playbook_integrity_errors` and `variants_tried` across
`apps/frontend` returns nothing, and iteration-3's own browser pass recorded that the
`joinable_corpus` object "does NOT appear anywhere in the rendered section". The passenger fixes'
shape change (`band_touch_count: 0` → `{"status": "not_enumerated", "count": None}`) therefore
cannot alter the Microscope Readiness DOM. Zero `.tsx` files changed.

### Test Findings

**T1 — GAP: TC-4's "resolves to a later row" is not actually tested, and contradicts the module's
own docstring**

`tests/test_scout_ledger.py:227` builds `later_candidate_ids = [row["candidate_id"] for row in
rows[3:]]` and then **never uses it** (dead variable); the assertion instead resolves
`superseded_by` against ANY row in the file, and the test's own comment rationalizes a successor
that appears EARLIER in append order. TC-4's wording is *"its successor pointer resolves to a later
row in the same file"*, and `scout_ledger.py`'s docstring asserts the successor "appears LATER in
the same file, append order." Nothing in the code enforces the ordering, and no production path
writes or reads `superseded_by` this iteration — the module ships the data SHAPE only, which it
says plainly. Impact today is nil; documented rather than fixed, since inventing supersession
ordering semantics is J-05's walk-forward scope.

**T2 — OBSERVATION: `test_tc10_a_failed_run_never_writes_a_silently_short_ledger` does not test its
own name**

It monkeypatches `register_and_screen_candidate` to raise on the FIRST call, so zero rows are ever
written; the mid-run case its name describes (rows 1-3 written, then a raise) is never exercised.
See B8 for what the code actually does.

**T3 — OBSERVATION (reviewer's open MINOR, not re-filed):** no assertion that `fallback_tercile`
survives into the composed `screen_result` / route payload. Already filed by the reviewer at
`tests/test_scout.py:711`; still open, still a coverage note rather than a product defect.

### Evidence Findings

**E1 — IMPORTANT (gap, not auditor-fixable): TC-20 was never executed — the required-still-passing
set is `unknown`, not `passing`**

`reports/phase-goal-rapid-microscope-iter-4-ui-test-results.md` is four lines long:

> **Browser QA Verdict:** SKIPPED
> **Reason:** Backend-only phase (Frontend Present: no). No browser tests executed.

The phase spec asked for the opposite division: *"J-01, J-02, J-03 … re-verify unchanged; J-10's
full kept-product sentinel script (`journey-scripts/J-10.json`) … re-run unmodified"*, with an
honest SKIP recorded for **J-04 only**. Instead the whole pass was skipped, so J-10's 13-step
sentinel — the kept-product guard — was not run at all, and no screenshot exists for any journey.
`runs/goal-rapid-microscope-iter-4/status.json` records `browser_checks_run: false`, and the QA
report deferred the set to browser-qa ("not this QA pass") while browser-qa skipped it — so no
agent ran it. This is the iteration whose regression set was deliberately widened to *every*
non-failing journey precisely because iteration 3's verdict was ESCALATE. Iteration 3 did run the
full sentinel with screenshots, so this is a discipline regression, not a standing limitation.

F1's grep evidence bounds the risk (no frontend surface can see any field this diff changed), but
per this project's own standing rule — no screenshot ⇒ `unknown`, never `passing` — TC-20 is
unmet. I cannot close it: it needs the browser-qa-agent driving the real rig.

---

## 3. Domain Assessment

The statistical core is real work, and better than the pipeline reports credited.

- **TR-8 is a genuine calibration, not a vacuous pass.** `_autocorrelated_null_anchors` builds a
  true AR(1)-within-session known-null corpus; the block screen holds pass-rate ≤ 0.075 across 200
  seeds, and the banned plain shuffle over the *identical fixture and seeds* demonstrably exceeds
  that ceiling. A calibration test whose counter-test also fires is the strongest form of this
  trap, and the banned path is additionally source-guarded out of both production entry points.
- **The block rotation is the right construction** for the trade-count horizons the grid actually
  registers: rotating the label sequence against fixed outcomes by a multiple of the block length
  preserves every contiguous run and moves only the seam. `_two_sided_p`'s `(exceed+1)/(n+1)`
  continuity correction is correct and never fabricates an exact zero. `_null_effect_draws`
  aggregates the null exactly as `_observed_effect` aggregates the real labels — the only honest
  way to compare them. Batching (`_batched_null_deltas`) shares one numpy `Generator` across
  batches, so it changes call count, never values.
- **TR-9 is enforced by construction, not by trust:** the econ floor's median spread is read, and
  both timestamps stamped, before any outcome is touched, so the ordinary path cannot violate the
  rule; the misordered-timestamp refusal is exercised directly. (Note: the phase spec's IN SCOPE
  line 127 says econ inputs read *before* `registered_at` are refused, while TC-7 and §5.5 say
  *after*. The implementation follows TC-7 and the stated rationale, which is correct; the IN SCOPE
  line is a typo, not a spec conflict the code got wrong.)
- **The decision cascade is a genuine closed vocabulary** with all seven branches reachable and
  individually tested, and the concentration gate's single-symbol carve-out is a real structural
  distinction, not a loophole — a one-symbol corpus reads `top1_symbol_share == 1.0` by
  construction, while session concentration still gates unconditionally.
- **`quote_depletion` exclusion (TC-13) is structural**: the name is absent from `FEATURE_FAMILY_OF`
  and refused at spec-build time, so the deferred `available_at` question cannot be leaned on even
  by accident.
- **Both passenger fixes are correct.** `playbook_store.list()`'s discarded error half is now
  surfaced verbatim as `playbook_integrity_errors` while healthy records still count (a corrupted
  file no longer vanishes silently); `band_touch_count` is a typed `{"status": "not_enumerated",
  "count": None}` returned as a fresh dict per call, and `total` is `playbook_signal_count` alone —
  numerically identical to before, verified against the real stores by TC-16
  (`playbook_signal_count == 2`, `by_setup_id == {"range_trade": 2}`).
- **The disclosed O(n²) perf fixes are genuinely behaviour-preserving.** I traced
  `outcome_row_at_single_horizon` against `_outcome_rows_after` line by line: identical
  `horizon_ts` derivation per kind, identical row-finders, identical `_build_outcome` core. The
  index-iteration rewrites of `_shares_horizon_row`/`_clock_horizon_row` preserve iteration order,
  early return and `None` fallthrough exactly.

Where the domain work fell short is the *integrity* half rather than the *statistics* half: the
ledger's tamper contract was verified only where a test looked (B1, B2), and its denominator
conflated evaluations with variants (B3). One statistical gap did exist, on the horizon family
nothing registered yet (B4). All four are now closed.

Frozen foundations re-verified independently, not read off the handoff:
`Config().config_fingerprint()` → `08e471b10130e1e2`; all six `referee_*.py` SHA-256 hashes
byte-match the iteration-0 listing in `docs/handoffs/goal-rapid-microscope-iter-0-dev.md`;
`git diff` over `app/engine/`, `desk_playbook.py`, `desk_playbook_context.py` and the referee
modules is empty; the 18 real-corpus snapshot files total exactly 3,815,933 rows (TC-17, TC-18).
Spec §1 constants transcribed verbatim, `KILL_REASONS` included; `live_confirmatory` is defined but
never emitted anywhere.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/research/micro_routes.py` | `GET /research/desk/micro/scout` now serves `chain_verification` (`ScoutLedger.verify_chain()` verbatim) beside `families`, so no served path can silently accept a tampered chain (B1, TC-3's second clause) |
| 2 | Important | `apps/backend/app/research/scout_ledger.py` | Durable `chain_head.json` tail anchor written after each append; `verify_chain` reports `tail_truncated` / `head_anchor_missing`; the false "deleting … breaks the `prev_hash` pointer" docstring claim corrected (B2) |
| 3 | Important | `apps/backend/app/research/scout_ledger.py` | New `distinct_variant_count`; `variants_tried_for_family` and `append_row`'s stamp count DISTINCT `candidate_id`s instead of rows (B3) |
| 4 | Important | `apps/backend/app/research/scout.py` | `register_and_screen_candidate` derives the cap check and the best-of-N input from `distinct_variant_count`; `list_scout_families` computes `variants_tried` rather than re-reading a row's stamp (B3) |
| 5 | Important | `apps/backend/app/research/scout.py` | New `ScoutUnsupportedHorizonError`; `_block_length_for_horizon` refuses shares/clock horizons instead of returning a 20-event block shorter than their own label span, and the refusal is raised up front at the registration boundary (B4) |
| 6 | Important | `apps/backend/tests/test_scout_ledger.py` | +5 tests: tail truncation caught at the first missing index, missing anchor is an honest refusal to certify, empty ledger still clean, ledger-longer-than-anchor benign, union-N counts distinct variants |
| 7 | Important | `apps/backend/tests/test_scout.py` | +10 tests: the route never serves a tampered chain without saying so, the route reports a truncated tail, 5 parametrized shares/clock refusals, trade-count still screens, a refused horizon writes no row, 13 consecutive identical grid runs neither inflate `variants_tried` nor exhaust the cap |

**Post-fix verification (commands and results, not claims):**

- `cd apps/backend && .venv/bin/python -m pytest tests/test_scout.py tests/test_scout_ledger.py`
  → **71 passed**.
- `cd apps/backend && .venv/bin/python -m pytest tests/test_scout_ledger.py tests/test_scout.py
  tests/test_micro_join.py tests/test_micro_readiness.py tests/test_micro_snapshots.py`
  → **169 passed** (the pre-fix state of the same set, before the B4 tests existed).
- `cd apps/backend && .venv/bin/python -m pytest tests/` → **2949 passed, 8 skipped, 0 failed**
  (492.29s, exit 0), run on the fully settled files with no concurrent edits. Baseline 2,866;
  pre-audit 2,934; +15 audit regression tests = 2,949. TC-19's floor (≥ 2,866 pass / 8 skip / 0 new
  failures) still holds. (An earlier full run reported one failure in
  `test_the_banned_plain_shuffle_null_is_never_imported_or_called_by_a_production_path` — an
  artifact of my editing `scout.py` while that run held stale `inspect.getsource` line numbers, not
  a defect; the test passes on the settled file and in both subsequent clean full runs. Worth
  knowing that this source-text guard is fragile in exactly that way.)
- Every pre-existing assertion in `test_scout_ledger.py`/`test_scout.py` was preserved, including
  the three exact-equality `verify_chain()` comparisons and TC-2's `list(range(1, 66))` stamp
  sequence — the chain walk runs before the anchor check, and anonymous rows count individually,
  precisely so the spec's own illustrations still hold.
- The B1/B2 defects were reproduced against live code before fixing (tamper → `['survive',
  'survive', ...]` served; tail truncation → `ok: True`, `variants_tried` 3→2), and B3 by running
  the default grid 13 times until `ScoutGridExhaustedError`.
- Scope re-read: the diff touches only the four findings. No endpoint added or removed, no
  `Config` field, no frontend file, no `docs/goal.md` / `blueprint.md` /
  `docs/rapid-validation-spec.md` edit. `Config().config_fingerprint()` re-checked after the fixes
  → still `08e471b10130e1e2`.

**Dev handoff claims invalidated by these fixes** (the handoff should be read with this report
beside it): "terminal-state-only ledger writes" describes the run log, not the ledger (B8); "no
gaps against this iteration's own DEFINITION OF DONE" was true only of the numbered DoD items — the
IN SCOPE bullet's non-overlapping anchor subsampling was neither built nor disclosed (B4); and the
`_block_length_for_horizon` interpretation call described as "a conservative floor" was
anti-conservative.

---

## 5. Recommended Next Step

**Do not score this iteration until browser QA actually runs.** The single blocking item is E1:
re-dispatch `browser-qa-agent` to re-verify J-01/J-02/J-03 and to run `journey-scripts/J-10.json`
unmodified, with screenshots on record, recording an honest SKIP for **J-04 only** — exactly what
TESTING REQUIREMENTS asked for and iteration 3 delivered. Nothing in this diff can plausibly have
broken a rendered surface (F1), so the expected outcome is green; the point is that no one has
looked, on the iteration whose regression set was widened after an ESCALATE.

After that, J-04's own work is done and the iteration can proceed. Three items to carry forward,
none of which should block:

1. **B5 (owner ruling):** `family_id` omits the corpus that §1's own constant definition names.
   Decide whether the cap bucket and served denominator should be per-(family, corpus) before more
   corpora land in J-06 — changing it later rewrites the grouping key on rows already ledgered.
2. **B4 follow-up (a real journey, not a patch):** shares and clock horizons are now honestly
   refused rather than mis-screened. Restoring them needs §5.3's per-session block sizing *and* its
   non-overlapping anchor subsampling, both of which are genuine work; they belong in whichever
   iteration first registers a clock-horizon candidate, with their own calibration trap.
3. **The disclosed real-corpus runtime** (dev handoff; reviewer's NOTE): the default grid still
   takes minutes against the full 18-dataset corpus. Weigh a dedicated perf iteration before J-06's
   ~150-symbol-day corpus lands, per this project's own "Edge-report perf fix" precedent. Note that
   B3's fix removes the sharper operational hazard — repeated triggers no longer exhaust the grid
   bound — so this is now a cost question, not a correctness one.
