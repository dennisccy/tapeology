# goal-rapid-microscope-iter-19 Audit Report

**Date:** 2026-08-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-10's last acceptance gap is genuinely closed: the three era computations are now proven to
re-run byte-identically, the four "cannot-fail" golden scripts are now measurably discriminating
(their target text is not rendered at all while the section is collapsed, and UT-10 proved the
backend-error branch renders different text), and no production module changed. One IMPORTANT
weakness was found by this audit's own mutation lane and FIXED: as landed, the Scout determinism
comparison was blind to the one thing the era's *critical* "deterministic and seeded" anti-goal
most needs it to see — replacing the seeded permutation stream with an unseeded RNG left the
compared payload byte-identical. Remaining gaps are documented below; the largest is that J-07
was not verified at all this round (deferred for wall-clock budget) and the harness bookkeeping
that would have re-queued it was erased as a side effect.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): the Scout determinism comparison could not observe the seeded
permutation stream.**
`apps/backend/tests/test_micro_deterministic_rerun.py:226` (`test_tc2_screen_candidate_…`) and
`:294` (`test_tc2_register_and_screen_candidate_…`) screen `_planted_effect_anchors()` (`:115`)
with its default `effect=3.0`. That effect saturates the block-permutation null
(`SCOUT_BLOCK_PERMUTATIONS = 2_000`, `apps/backend/app/research/scout.py:141`): not one of the
2,000 draws ever reaches the observed delta, so `p_screen` pins to the floor `1/(draws+1)` in
**every** run. Measured, not inferred — this audit ran an independent mutation lane that replaced
`scout.scout_stream` (`apps/backend/app/research/scout.py:247`, consumed at `:663` and `:668`)
with an UNSEEDED `random.Random()`:

- `p_screen` baseline = `0.0004997501249375312` = `1/2001` (the saturated floor);
- unseeded-vs-unseeded diff over the whole `screen_result` payload = `{}` (empty);
- both landed TC-2 tests (pure and ledger-level) **passed unchanged** with the seed lineage
  destroyed.

So TC-2 proved determinism only of the deterministic half of the screen. TC-4b did not catch this,
because TC-4-class mutation-proofs perturb the *comparison input*, never the *computation* — they
prove the comparator works, not that its inputs carry the nondeterministic part.

**Fix applied** (additive only, in the module this iteration created):
- `test_tc2b_screen_candidate_rerun_is_byte_identical_where_the_seeded_null_stream_actually_moves_it`
  (`apps/backend/tests/test_micro_deterministic_rerun.py:259`) — reruns an `effect=0.0` candidate whose `p_screen` lands strictly inside the null distribution
  (asserted `> 1/(SCOUT_BLOCK_PERMUTATIONS+1)` and `< 1.0`), where the stream genuinely moves the
  result;
- `test_tc4d_scout_rerun_comparison_fails_when_the_seeded_null_stream_is_replaced` (`:275`) — the
  stream-level mutation-proof: the perturbation is the SEED LINEAGE itself (every per-session
  `scout_stream` collapses to one fixed alternate stream, so the test is deterministic, never
  flaky), the comparison must FAIL, and after `monkeypatch.undo()` the real seeded rerun must
  PASS;
- module docstring extended to record the new perturbation, per the spec's own "record which
  fields were perturbed" requirement.

Verification of the fix (all commands run by this audit):
- `.venv/bin/python -m pytest tests/test_micro_deterministic_rerun.py -v` → **10 passed in 0.95s**.
- Scratch mutation harness (created, run, deleted): with `scout.scout_stream` monkeypatched to an
  unseeded `random.Random()`, the NEW TC-2b **raises `AssertionError` as required**, while the
  original TC-2 still passes — the blind spot and its closure both demonstrated in one run
  (`2 passed` for both scratch expectations).
- Full backend suite after the fix: **3,281 passed, 8 skipped, 0 failures, 0 errors (3,289
  collected) in 648.13s**, exit 0 — +2 tests versus the QA run, exactly the two added, and well
  above the iteration-18 baseline of 3,271 collected / 3,263 passed / 8 skipped.

**B2 — GAP (observation-with-evidence): the persisted-snapshot rerun compares byte *length*, not
row content.**
`test_tc1_run_snapshot_build_and_record_persists_byte_identical_identity_across_two_independent_root_dirs`
compares the meta that `write_snapshot` returns (`apps/backend/app/research/micro_snapshots.py:284-301`):
identity fields plus `row_count` and `bytes_on_disk`, minus `built_utc`. There is no digest of the
row payloads in that meta. Measured: with a deliberately jittered observer, two independent runs
produced **identical** meta (`bytes_on_disk` 3168 in both) even though the row content differed
each run, because a random float's JSON repr is the same length. This is a limitation, not a hole
— row *content* determinism is covered by the sibling test
(`test_tc1_build_snapshot_rows_is_byte_identical_across_two_independent_calls`, which compares the
full rows and which my jitter mutation **did** break). Not fixed: the spec's TC-1 asks exactly for
"rows" + "identity fields", and both are covered between the two tests.

**B3 — GAP: TC-3's walk-forward fixture is constant-valued.**
`_wf_observations()` (`apps/backend/tests/test_micro_deterministic_rerun.py:137`) returns 12 observations that all carry `value: 4.0`, so `effect` is 4.0 by
construction. Value-level nondeterminism IS detected (verified: injecting jitter into
`wf.summarize_fold_observations` made TC-3 fail as required), but an order-dependent aggregation
(e.g. float summation order) would be invisible under a constant fixture.
`evaluate_mode_b_fold` (`apps/backend/app/research/walkforward.py:581-615`) draws no randomness at
all, so the practical exposure today is low. Not fixed — varying the fixture is beyond this
iteration's scope and would touch TC-3's spec'd shape.

**B4 — OBSERVATION: `_canonical` stringifies anything non-JSON.**
`_canonical()` (`apps/backend/tests/test_micro_deterministic_rerun.py:170`) uses `json.dumps(obj, sort_keys=True, default=str)`. Every field
compared today is JSON-native, so there is no effect now; a future object-valued field would be
compared by `str()`, which fails *closed* (a repr carrying an address would false-FAIL, never
false-PASS). Recorded, not changed.

### Frontend Findings

**F1 — no product change, verified independently.** `git status --porcelain -- apps/backend/app
apps/frontend` is empty: no production module and no `.tsx` file changed this iteration. The four
newly-asserted strings were traced to their render sites and all sit inside the **success** branch
of their section:
- `"Fallback frac"` — `apps/frontend/app/desk/page.tsx:6071`, inside the table that only renders
  when `readiness.shards.length !== 0` (`:6053`; the empty case renders "No tick shards recorded.");
- `"Joinable corpus — withheld (excluded)"` — `:6006`, driven by `readiness.joinable_corpus.withheld_excluded`;
- `"Ledger chain verification:"` (Scout) — `:6268`, the branch taken only when
  `scoutResult.ok && scoutResult.data !== null`; the failure branch renders `UnavailablePanel`
  (`:6260-6264`);
- `"Ledger chain verification:"` (Walk-Forward) — `:6495`, same structure (`:6487-6491`).
`CollapsibleSection` (`apps/frontend/components/CollapsibleSection.tsx:57-61`) renders the body
**only when open** — it is not CSS-hidden — and the replay's `_check_expect` waits for
`state="visible"` (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:638-648`), so these
assertions cannot pass without the expand genuinely working. The negative case was proven live,
not argued: UT-10 blocked `/research/desk/micro/scout` in the browser and confirmed the
`scout-ledger-unavailable` panel rendered and `"Ledger chain verification"` matched **0** times.
TC-5..TC-8 are genuinely discriminating.

**F2 — OBSERVATION: the ux-regression reviewer did not run.**
`reports/phase-goal-rapid-microscope-iter-19-ux-regression.md` records
`UX-REGRESSION-SKIPPED` — "this iteration exceeded its wall-clock budget, so this non-blocking
reviewer was shed." Non-blocking by design, and zero `.tsx` changed, so the risk is minimal —
but it is the second lane cut for time this round (see T1), which is exactly the question the
phase spec carries forward to the human owner in its NOTES.

### Test / Harness Findings

**T1 — GAP: J-07 was not verified this iteration, and the bookkeeping that would re-queue it was
erased.**
`reports/phase-goal-rapid-microscope-iter-19-ui-test-results.md` ends with a "Deferred (iteration
budget)" table: `UT-J-07 … DEFERRED-BUDGET … not run this iteration`. J-07 is inside the DoD's
"Required-still-passing journeys J-01–J-08". Because J-07 has no golden script by design, its only
lane is the LLM lane, and that lane was shed. Second-order effect, found by diffing the working
tree: `runs/goal-session-rapid-microscope/state/golden-gaps` (whose entire content was `J-07`) is
**deleted** in this iteration's working tree. That is mechanical, not malicious —
`replay_lane_golden_coverage` (`incredible_auto_dev/scripts/automation/lib/replay-lane.sh:520-536`)
rebuilds the file from journeys that PASSED *and* lack a golden, and removes it when that set is
empty; J-07 was not in the PASS set because it was never run. The consequence is that the SPEED-23
nudge (`replay-lane.sh:681-683`, which requires a non-empty gaps file) has nothing to pick next
round, so J-07 will not be nudged toward a golden script. Not fixed — this is goal-engine state
the pipeline owns, and rewriting it from an audit would be worse than reporting it. Recommended
next-iteration action in §5.

**T2 — OBSERVATION: TC-10's "all 8 golden scripts execute" was satisfied 7 + 1, not 8 + 0.**
`reports/phase-goal-rapid-microscope-iter-19-regression-replay-results.md` shows 7 replayed
journeys (J-01..J-06, J-08), all PASS. J-10 — the eighth registered golden — was instead verified
**fresh and live** by the browser-qa agent (UT-06 walks all 11 kept-product confirm steps; UT-07
covers the Validation Vault and all three Referee sections), which is what DoD item 1 asks for and
is strictly stronger evidence than a replay. Substance met; the letter of TC-10 ("all 8 … execute
and report individually") deviated. Worth stating plainly so a future reader does not mistake
"7/7 passed" for the full set.

**T3 — OBSERVATION: J-04 and J-05 assert the same literal string.**
Both now expect `"Ledger chain verification:"`. Each is discriminating for its own section (a
fresh browser context starts with every section collapsed, and only the clicked section mounts),
but a swapped `testid` between those two scripts would not be caught by the assertion text alone.
The strings were dictated by the phase spec (TC-7/TC-8), so this is recorded, not changed.

### Reporting Findings

**R1 — OBSERVATION: the store-provenance DoD item is met by the browser-qa report, not by the QA
report.**
`reports/qa/goal-rapid-microscope-iter-19-qa.md` §Notes 4 states the class of store ("QA launcher
is fixture-scoped … not the real production data store") **without** citing the manifest — the
sourcing the DoD asks for. The requirement is nonetheless satisfied by
`reports/phase-goal-rapid-microscope-iter-19-ui-test-results.llm.md:25-31`, which cites
`reports/qa-scoped-backend-store-manifest.md` by path, quotes its `launched_at_utc
2026-08-20T13:34:48Z`, names the resolved `TAPEOLOGY_DATASET_DIR=.../tapeology-store-scope-qa/rig/datasets`,
and states explicitly that "no statement in this report should be read as 'real data store.'" I
verified the manifest cannot lie about the running process: the launcher exports the scoped vars
before `exec`-ing `scripts/start-backend.sh`, and `app/env.py:23-39` (`load_env`) never overrides
an already-set var, so `.env` cannot silently replace them. Corroborated independently by
`reports/qa/goal-rapid-microscope-iter-19-store-scope-guard.md` (CLEAN — 11,275 protected files
before and after, byte-size and mtime unchanged). No fix applied: the claim is true, sourced, and
cross-checked; only its weakest restatement lacks the citation.

---

## 3. Domain Assessment

The domain question this iteration had to answer is narrow and real: *does re-running the era's
three computations over unchanged stored data reproduce the same numbers?* The module answers it
honestly and, importantly, avoids the trap it names: it does **not** rerun
`run_snapshot_build_and_record` or `append_fold_result` against the same store/ledger (both are
idempotent-on-replay in production, so a same-store rerun would compare a cached object with
itself). Instead it forces genuinely independent second computations — a second `root_dir` for the
snapshot path, a fresh `(WalkForwardLedger, ExposureRegistry)` pair for the fold path — and it
uses the ledger reuse case only where the ledger legitimately grows (`register_and_screen_candidate`
appends a second trial row while `variants_tried_for_family` stays at 1, which is also a correct
reading of the "denominator never shrinks" anti-goal: union-N counts variants, not evaluations).
That is the right shape.

The one place the reasoning was thinner than the prose claimed was the randomized core. The Scout
screen is the only one of the three computations that consumes randomness at all (a seeded
within-session circular block permutation, 2,000 draws), and it was the one computation whose
comparison could not see its own seed lineage. That is now fixed and proven in both directions.
After the fix, the module's claim — and the implementation summary's plain-language version of it
("same effect sizes, same p-values, same disclosures") — is true as written for the first time.

The harness half is a genuine improvement in kind, not degree. Four scripts that would have passed
against a completely broken Rapid-Microscope section now fail if the section does not mount and
serve; the section body is unmounted (not hidden) while collapsed, the replay waits for visibility,
and the error branch was empirically shown to render different text. The store manifest closes
iteration 18's specific process finding with a fixed-path artifact whose truthfulness I traced
through the env-precedence rules rather than accepting.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/tests/test_micro_deterministic_rerun.py` | Added `test_tc2b_screen_candidate_rerun_is_byte_identical_where_the_seeded_null_stream_actually_moves_it` — an `effect=0.0` rerun whose `p_screen` lies strictly inside the permutation null, so the comparison genuinely observes the seeded stream (the strong-effect fixture saturates it at `1/2001` and is stream-blind) |
| 2 | Important | `apps/backend/tests/test_micro_deterministic_rerun.py` | Added `test_tc4d_scout_rerun_comparison_fails_when_the_seeded_null_stream_is_replaced` — stream-level mutation-proof (perturbs the SEED LINEAGE, fixed alternate seed so it can never flake), plus the shared `_screen_planted()` call-shape helper |
| 3 | Important | `apps/backend/tests/test_micro_deterministic_rerun.py` | Module docstring extended to record the new perturbation and the measured blind spot, per the spec's "record which fields were perturbed" rule |
| 4 | Observation | `docs/handoffs/goal-rapid-microscope-iter-19-dev.md` | Appended an auditor addendum correcting the now-stale counts (8 tests → 10; 3,279 passed → 3,281) so the handoff's claims stay accurate |

All four are additive; nothing existing was edited or weakened (the house rule "guard tests are
extended, never edited" is respected). No production module, no `.tsx`, no golden script, and no
frozen/Referee file was touched by this audit — confirmed by re-reading the working tree after the
fix: the only files this audit changed are the two listed above.

Post-fix evidence (per the mandatory self-verification):
1. `pytest tests/test_micro_deterministic_rerun.py -v` → 10 passed in 0.95s.
2. Independent mutation re-run: unseeded `scout_stream` ⇒ new TC-2b raises `AssertionError`
   (required), original TC-2 still passes (the documented blind spot). Scratch harness deleted —
   `ls tests/ | grep -c zz_auditor` → `0`.
3. Full suite: **3,281 passed / 8 skipped / 0 failed / 0 errors, 3,289 collected, 648.13s**, exit 0.
4. No new finding introduced: the added tests use a fixed alternate seed (deterministic, not
   flaky), call `monkeypatch.undo()` before re-asserting the real rerun, and add no escape hatch.

Independently re-verified standing sentinels (not taken from the QA report):
- `Config().config_fingerprint()` → `08e471b10130e1e2` ✓
- the six `referee_*.py` SHA-256s match the iteration-0 baseline
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:76-81`) byte-for-byte ✓

---

## 5. Recommended Next Step

Proceed. J-10's deterministic-rerun acceptance gap is closed and, after this audit's fix, closed
for the right reason — including the seeded-stream path the era's critical anti-goal names. The
three passenger items landed as specified.

Two items to carry into the next iteration's plan, neither blocking:

1. **Re-verify J-07 and restore its golden-gap bookkeeping.** J-07 was shed for wall-clock budget
   (T1) and `state/golden-gaps` — which held exactly `J-07` — was deleted as a side effect, so the
   SPEED-23 nudge has nothing to pick. The next round should run J-07's LLM lane and, per the
   standing nudge intent, author its golden script; that both re-establishes the required-still-
   passing evidence and makes the gaps file self-healing again.
2. **Prefer stream-sensitive fixtures for any future determinism check.** The lesson from B1 is
   reusable and worth adding to `state/lessons.md`: a determinism comparison over a *saturated*
   statistic (a p-value pinned to the null's floor, a decision that cannot flip) is stream-blind by
   construction, and a TC-4-style mutation-proof will not reveal it because it perturbs the
   comparison's input rather than the computation. The mutation that matters is the one applied to
   the *seed lineage*.

The owner ruling on the sealed judge's economic floor / evidence-label ownership
(`docs/rapid-validation-spec.md`, still no revision after r9 — re-confirmed by grep this round)
remains the blocker for iteration 18's item 1 and for J-09; nothing in this iteration changes that.
