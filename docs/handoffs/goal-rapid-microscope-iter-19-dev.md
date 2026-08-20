# goal-rapid-microscope-iter-19 Dev Handoff

**Phase:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

- **New test module `apps/backend/tests/test_micro_deterministic_rerun.py`** — J-10's last
  remaining acceptance gap: proves each of the three era computations (snapshot build, Scout
  screen, walk-forward fold) produces byte-identical output when GENUINELY re-run over an
  unchanged fixture dataset/store.
  - TC-1: `micro_snapshots.build_snapshot_rows` (called twice, pure recomputation) and
    `run_snapshot_build_and_record` (called against two independent `root_dir`s, so it cannot hit
    the `load_snapshot_meta` reuse path) both produce byte-identical snapshot rows / persisted
    identity (excluding `built_utc`).
  - TC-2: `scout.screen_candidate` (pure function, hand-built anchors) and
    `register_and_screen_candidate` (real ledger, real fixture corpus) both produce
    byte-identical `screen_result` payloads across two independent calls; the ledger-level test
    additionally proves the SAME candidate registered twice appends TWO independent trial rows
    (never overwritten/deduplicated) while `variants_tried_for_family` stays at 1 (union-N counts
    variants, not evaluations).
  - TC-3: `walkforward.evaluate_mode_b_fold` evaluated over two independently-fresh
    `(WalkForwardLedger, ExposureRegistry)` pairs produces byte-identical `fold_results` fields
    (effect, n, n_sessions, sign, evidence_class, process_label); `sequence_id` is confirmed to be
    a deterministic pure function of `(corpus_id, rule_id)`, independently derived in each run.
  - TC-4 (mutation-proof, three tests, one per computation): each comparison is proven capable of
    FAILING by perturbing one field of a scratch second-run result (`cumulative_delta` for
    snapshots, `effect_bps` for scout, `effect` for walk-forward) before comparison, then reverting
    and confirming the real rerun still passes.
  - **Why two of the three computations deliberately avoid a same-store/same-ledger rerun**:
    `run_snapshot_build_and_record` and `walkforward_ledger.append_fold_result` are both
    DELIBERATELY idempotent-on-replay in production (the former reuses an existing valid
    snapshot; the latter returns the cached row for an identical
    `(sequence_id, fold_index, spec_hash)`). A naive rerun test against either using the SAME
    store/ledger would compare a cached result against itself — always "passing" because it is
    literally the same object, not because determinism is proven (exactly the "structurally
    unable to fail" trap iter-15/16 warned about, and `test_walkforward.py`'s own TR-22 section
    calls out explicitly). Every comparison in this module forces a genuinely independent second
    computation instead — see the module's own docstring for the full reasoning.
- **Four golden replay scripts deepened** (`runs/goal-session-rapid-microscope/journey-scripts/
  J-02.json`, `J-03.json`, `J-04.json`, `J-05.json`) — each now expands its own already-registered
  Rapid-Microscope section and asserts a real, already-registered field, instead of an unrelated
  pre-existing Desk heading:
  - J-02: expand Microscope Readiness → `"Fallback frac"` (column header).
  - J-03: expand Microscope Readiness → `"Joinable corpus — withheld (excluded)"` (label).
  - J-04: expand Scout Ledger → `"Ledger chain verification:"`.
  - J-05: expand Walk-Forward → `"Ledger chain verification:"` (step 1 already matched the shared
    pattern; only step 2 is new).
  All four now share step 1 (`goto /desk` → expect `"Playbook Signals"`), the same pattern already
  used by J-01/J-08/J-10.
- **`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` extended in place** — after
  seeding, it now writes a durable manifest to `reports/qa-scoped-backend-store-manifest.md`
  recording the exact resolved `TAPEOLOGY_*` store-root env vars, the root dir, the port, and a
  launch timestamp, alongside the pre-existing stderr echo lines (both now share one var list —
  `_TAPEOLOGY_SCOPED_VARS` — so they can never silently diverge). This closes iteration 18's
  evaluator finding ("the quality report states that the browser lane used your real data store.
  It did not.") by giving any QA/reviewer/auditor report a fixed-path file to cite, independent of
  whether the launch's own stdout/stderr was captured.

## Files Changed

- `apps/backend/tests/test_micro_deterministic_rerun.py` (new) — TC-1..TC-4 (8 tests total: 5 real
  rerun-determinism tests + 3 mutation-proof tests).
- `runs/goal-session-rapid-microscope/journey-scripts/J-02.json` — step 1 fixed to the shared
  pattern; step 2 added (expand Microscope Readiness → `"Fallback frac"`).
- `runs/goal-session-rapid-microscope/journey-scripts/J-03.json` — step 1 fixed to the shared
  pattern; step 2 added (expand Microscope Readiness → `"Joinable corpus — withheld (excluded)"`).
- `runs/goal-session-rapid-microscope/journey-scripts/J-04.json` — step 1 fixed to the shared
  pattern; step 2 added (expand Scout Ledger → `"Ledger chain verification:"`).
- `runs/goal-session-rapid-microscope/journey-scripts/J-05.json` — step 2 added (expand
  Walk-Forward → `"Ledger chain verification:"`); step 1 unchanged (already matched).
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extended in place: writes
  `reports/qa-scoped-backend-store-manifest.md` at launch; factored the var list shared by the
  stderr echo and the new manifest write into one array.
- No `.tsx` file changed — zero product behavior change this iteration (verified: `git diff
  --stat -- apps/frontend` shows no output).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **3279 passed, 8 skipped, 2 warnings in 656.72s (0:10:56)**, exit code 0 — 0 failures, 0
errors. Total collected = 3287, which is >= the iteration-18 baseline (3,271 collected / 3,263
passed / 8 skipped / 0 failures / 0 errors) with 0 regressions and 8 skips matching the baseline
exactly (both warnings are pre-existing library deprecation notices, unrelated to this iteration's
changes). (Note: `addopts = "-q"` is already set in `apps/backend/pyproject.toml`; passing an
extra `-q` on the command line stacks to pytest's quiet level 2, which suppresses the final
summary line entirely in this pytest version — the command above intentionally omits the extra
flag so the summary line prints.)

New module in isolation: `.venv/bin/python -m pytest tests/test_micro_deterministic_rerun.py -v`
→ 8 passed in 0.67s.

Manual verification of the QA launcher script: ran
`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh <scratch-root> 8391` end to
end, confirmed the backend came up, confirmed `reports/qa-scoped-backend-store-manifest.md` was
written with the resolved `TAPEOLOGY_DATASET_DIR` and sibling vars plus a launch timestamp, and
confirmed `GET /research/desk/micro/scout` and `GET /research/desk/micro/walkforward` both return
a `chain_verification` object and `GET /research/desk/micro/readiness` returns non-empty `shards`
against that scoped backend (the data the four deepened golden scripts' assertions read from) —
then killed the scratch backend and removed the scratch root (no artifact left behind except the
manifest file itself, which is regenerated by every future launch of this script).

## Known Issues

- No `.tsx` product change ships this iteration (by design — see the phase spec's "Frontend
  Present: yes despite zero .tsx changes" framing). The four deepened golden scripts click
  ALREADY-shipped `desk-section-expand-*` controls and assert ALREADY-served backend text; I
  confirmed via source inspection (exact grep line matches to the plan's cited line numbers in
  `apps/frontend/app/desk/page.tsx`) and via the scoped-backend GET responses that these strings
  are unconditionally present whenever the section's data loads successfully (not gated behind a
  non-empty-list branch), so they will render on the fixture-scoped rig. I did not run a live
  Chrome/Playwright pass against the frontend myself — that is the browser-qa-agent's job for this
  iteration's DoD (J-10 fresh sentinel + the full 8-journey golden-replay set).
- The QA launcher script extension writes ONE manifest file (`reports/qa-scoped-backend-store-
  manifest.md`) that always reflects the MOST RECENT launch of the script — any downstream
  QA/reviewer/auditor report for this iteration must reference the manifest produced by THAT
  iteration's own actual browser-qa/replay launch, not a stale one from an earlier manual test (I
  ran the script once manually to verify it works, on a scratch root/port; that manifest gets
  overwritten by the real browser-qa-agent's own launch).
- Out of scope, confirmed untouched: `micro_sealed_evaluation.py`'s `econ_floor`/TR-30 logic, J-09
  (pilot studies), J-06 step 4 (real Alpaca tranche recording), `J-08.json`/`J-10.json`'s Vault
  assertions, `vault.py`, `tick_recorder.py`, any Referee module.

---

## Auditor addendum (2026-08-20, iteration-19 audit)

The audit's independent mutation lane found that TC-2's scout comparison, as landed, could NOT
observe the seeded permutation stream: the `effect=3.0` planted candidate saturates the
block-permutation null (`p_screen == 1/(SCOUT_BLOCK_PERMUTATIONS+1)` in every draw), so replacing
`scout.scout_stream` with an UNSEEDED `random.Random()` left the whole `screen_result` payload
byte-identical. Two tests were added to `apps/backend/tests/test_micro_deterministic_rerun.py`
(module docstring updated with the same reasoning):

- `test_tc2b_screen_candidate_rerun_is_byte_identical_where_the_seeded_null_stream_actually_moves_it`
  — an `effect=0.0` candidate whose `p_screen` lands strictly inside the null distribution.
- `test_tc4d_scout_rerun_comparison_fails_when_the_seeded_null_stream_is_replaced` — the
  stream-level mutation-proof (the perturbation is the SEED LINEAGE, not a result field).

Therefore this handoff's "8 tests total: 5 real rerun-determinism tests + 3 mutation-proof tests"
now reads **10 tests total: 6 real rerun-determinism tests + 4 mutation-proof tests**, and the
full backend suite count moves from 3,279 passed / 8 skipped to **3,281 passed / 8 skipped**
(3,289 collected, 0 failures, 0 errors, 648.13s). Everything else in this handoff was verified
correct against source. See `docs/handoffs/goal-rapid-microscope-iter-19-audit.md` finding B1.
