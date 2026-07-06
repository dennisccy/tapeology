# goal-tape_to_profit_support_resistence-iter-6 Execution Plan

Frontend Present: no

## Context (why this iteration, and why it's safe)

J-06 is the **sole remaining failing Must-have journey** of Era 4 (`docs/goal.md`) — the
goal-completing iteration. iter-4 shipped `structure_tape` as a registered strategy; iter-5
(evaluator PASS, audit PASS) added its class-scaled stop/reward/size math. J-06 asks: is
`structure_tape` honestly better than the frozen `v1` champion on **hold-out** data? This plan
generalizes the ONE existing sweep (`pnl_scan.py`) rather than building anything new. I
independently verified the phase spec's reuse claims against the actual code before writing this:

- `BacktestJobManager.create()` (`app/research/backtests.py:871`) stamps `params["strategy_id"]`
  verbatim with no registry check at create-time — the check lives in `BacktestRunner.run()`
  (line 388: `strategy = self._config.strategy_definition(params["strategy_id"]); if strategy is
  None: raise ValueError(...)`), and `run()` **never raises out** — every failure, including an
  unknown strategy id, is persisted as an explicit `failed` record (docstring, line 356). So
  `pnl_scan._run_backtest`'s existing `if final.get("status") != STATUS_DONE: raise ScanError(...)`
  already turns an unknown `--strategy` value into a clean, explicit refusal with **zero new
  validation code required** — confirms the BACKGROUND section's claim that no new backtest path
  is needed.
- `store.set_champion_pointer(*, strategy_id, profile, wall_ts)` and
  `pnl_ledger.append_validation_row(...)` already accept arbitrary strategy ids / report ids —
  neither needs a signature change. **`store.py` and `pnl_ledger.py` should need NO code changes.**
- `config.py` already has everything the spec says to reuse: `STRATEGY_V1_ID = "v1"`,
  `STRATEGY_TAPE_ID = "structure_tape"`, `PROFILE_DEFAULT = "default"`,
  `promotion_min_sample_size`, `pnl_min_sample_size`. **No new `Config` field should be needed.**

This matches `docs/goal.md`'s Success Criterion 4 (`structure_tape` "judged only by the era-3
machine and promoted only by beating the champion on the frozen hold-out set... train-only wins
are labelled overfit and rejected") with no drift. No scope creep found in the phase spec — its own
OUT OF SCOPE list already excludes a second module/endpoint, a second champion pointer, any
`v1`/`default`/engine mutation, and a required `edge_report.py` generalization.

## What to Build

- **A strategy axis on the ONE existing sweep** (`apps/backend/app/research/pnl_scan.py`): the CLI
  gains a `--strategy <id>` option (e.g. `--strategy structure_tape`). When given, `run_sweep()`
  evaluates exactly ONE named-strategy candidate — backtest at `strategy_id=<named>`,
  `profile=PROFILE_DEFAULT` — compared against the champion's **current** strategy id (read
  verbatim from `store.get_champion_pointer()["strategy_id"]`, never hardcoded `"v1"`) also at
  `profile=PROFILE_DEFAULT`. **With no `--strategy` given, the sweep must behave byte-identically
  to today** (the existing profile-only candidate loop over `config.profile_registry()`) —
  implement the new axis as an additive branch, not a refactor of the existing path, and prove it
  with the pre-existing `test_pnl_scan.py` tests passing unmodified.
- Reuse `_dataset_rows` / `_split_summary` / `_is_positive` / `_promote` verbatim — these are
  already axis-agnostic (they operate on `(report_id, result)` pairs, not on "profile" per se).
- Per-split (train, hold-out — never pooled) report: `structure_tape`'s and `v1`'s net R AND net
  $, n, per-dataset breakdown, and candidate-minus-champion deltas.
- `survivor` reuses the existing gate verbatim (summed hold-out delta positive on BOTH net R and
  net $ AND summed hold-out candidate n ≥ `Config.promotion_min_sample_size` — no new min-n
  field). `overfit` = positive train AND NOT survivor (unchanged definition).
- Promotion of a genuine hold-out survivor reuses the existing crash-safe two-write order
  (`append_validation_row` THEN `store.set_champion_pointer`), generalized to move the strategy
  axis: `strategy_id=<named candidate>`, `profile=PROFILE_DEFAULT`. Pointer write only — never
  touches `default`, `v1`, or any engine default.
- Honest fixture outcome: on the committed train/hold-out fixture pair, `structure_tape`'s
  hold-out n is below `promotion_min_sample_size` (2-timeframe PG fixture → mostly class-C, per
  the iter-3 lesson) → no survivor → no promotion → champion stays `{v1, default}` → CLI exits 0.
- Determinism: the report keeps the existing sorted-key, no-wall-clock render discipline — two
  fresh-state runs on the fixtures produce byte-identical `--out` bytes.
- **Disclose audit item B1** (carried from iter-4/iter-5: the breakthrough arm is a static
  price-position test, not a fresh event-to-event cross) explicitly in the comparison report's
  provenance/assumptions — do NOT re-arm it. Tightening it is permitted only if J-04/J-05 stay
  provably byte-identical, which is a second risky change this plan does not ask for.
- Extend `tests/test_no_execution_path.py`'s grep-guard to explicitly name the new comparison
  code path (mirroring the iter-5 precedent of a dedicated test, on top of the pre-existing
  repo-wide sweep).
- Doc-parity: update `README.md` to describe the named-strategy comparison capability and the
  honest "no survivor on the fixtures" finding (and verify the iter-5 rider was already applied
  before adding a duplicate note — check `git blame`/existing bullets first).

**Explicitly out of scope this iteration** (per the phase spec's own OUT OF SCOPE list — do not
build): a new comparison/promotion module or new REST endpoint; a second champion pointer or a
second min-n `Config` field; any change to `v1`, `default`, the tape engine, the live cockpit, or
any engine default; a required `edge_report.py` generalization (optional, read-only only, not
DoD-gated); any real promotion on the committed fixtures (n is honestly below the minimum — the
promotion *path* is exercised only via synthetic ≥-min-n test fixtures); any new REST endpoint,
nav, page, or UI change.

## Agents Required

- developer: yes -- generalize `pnl_scan.py`'s sweep with the named-strategy axis described above
  (CLI `--strategy` flag, per-split comparison report, survivor/overfit gate, crash-safe
  promotion), extend `test_pnl_scan.py` and `test_no_execution_path.py`, update `README.md`, and
  write the dev handoff. Backend-only; no frontend agent needed.
- backend-data: yes
- frontend-ux: no

## Frontend Present

no

(Frontend Present: no — machine surface only, CLI + existing REST/MCP reads. `apps/frontend/`
MUST NOT be touched this iteration — confirm a zero frontend diff in the dev handoff, per the
iter-0 lesson that this is what keeps J-07's cockpit leg green without a new screenshot. No browser
QA required.)

## Files to Create/Modify

- `apps/backend/app/research/pnl_scan.py` -- add the `--strategy` CLI option and the strategy-axis
  candidate path in `run_sweep()`; keep the no-flag path byte-identical to today.
- `apps/backend/app/config.py` -- expected **no changes**; touch only if a genuinely new
  config-owned parameter proves necessary, and then only by adding it to `config_fingerprint()`'s
  `excluded` set (the pinned `v1`/`default` fingerprint `4d665603569b9dbf` must not move).
- `apps/backend/app/research/store.py`, `apps/backend/app/research/pnl_ledger.py` -- expected
  **no changes** (both already accept arbitrary strategy ids / report ids verbatim).
- `apps/backend/tests/test_pnl_scan.py` -- extend with: named-strategy comparison shape; survivor
  gate on the strategy axis (below-min-n vs at/above-min-n, via synthetic fixtures mirroring the
  existing min-n tests); overfit labelling; promotion correctness + crash safety (exactly one
  ledger row then the pointer moves to `strategy_id=structure_tape`); frozen-foundation check
  after a promotion (fingerprint unmoved, `v1`/`default` byte-identical, engine equivalence green);
  fixture honesty (no survivor on the committed pair); determinism; backward compatibility (the
  existing profile-only sweep tests pass unmodified); single-source scan (pointer setter still
  called from exactly one file); unknown-candidate-strategy-id refusal; >1 train/hold-out dataset
  registered → promotion skipped with an honest note.
- `apps/backend/tests/test_no_execution_path.py` -- one new test naming the strategy-axis
  comparison/promotion code explicitly (iter-5 precedent).
- `README.md` -- doc-parity bullet(s) for the named-strategy comparison + honest fixture finding.
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-6-dev.md` -- dev handoff (required by
  DoD), listing every file changed including doc edits.
- `apps/backend/app/research/edge_report.py` -- optional, NOT required for DoD; touch only if
  trivial and strictly read-only (no `_promote`, no ledger write, no pointer move).

## Key Test Scenarios

1. Named-strategy comparison shape: per split (train, hold-out, never pooled) —
   `structure_tape` vs `v1` net R AND net $, n, per-dataset breakdown + deltas.
2. Survivor gate on the strategy axis: a below-min-n hold-out win is NOT a survivor; an
   at/above-min-n positive hold-out win IS a survivor (synthetic fixtures).
3. Overfit: positive train + failing hold-out → `overfit=true`, `survivor=false`, never promoted.
4. Promotion correctness + crash safety: exactly ONE ledger row appended THEN the pointer moves to
   `strategy_id=structure_tape`, `profile=default`; a mid-promotion re-run hits the existing
   `DuplicateEnhancementError` → explicit `ScanError` (no silent double-append, no orphan).
5. Frozen foundation after a promotion: `config_fingerprint() == "4d665603569b9dbf"` unmoved,
   `v1`/`default` byte-identical (`test_profile_equivalence.py` green), engine equivalence green.
6. Fixture honesty: the committed train/hold-out fixture pair yields no survivor, champion stays
   `{v1, default}`, exit 0, nothing written to the ledger, no pointer move.
7. Determinism: two independent fresh-state runs on the fixtures produce byte-identical `--out`.
8. Backward compatibility: the existing profile-only sweep (no `--strategy`) reproduces
   byte-identically — every pre-existing `test_pnl_scan.py` test passes unmodified.
9. Single-source scan: `store.set_champion_pointer` still called from exactly one source file; no
   second net R/$/edge computation path introduced.
10. Honest error states: corrupt dataset → explicit `ScanError`, nothing written; unknown
    candidate strategy id → explicit refusal, never a coerced/fabricated comparison; more than one
    train or one hold-out dataset registered → promotion explicitly skipped with an honest note,
    comparison still fully reported.
11. Audit B1 disclosed: the comparison report's provenance/assumptions section explicitly names
    the breakthrough arm's loose static-price-position anchor.
12. Grep-guard: no broker/order/routing/execution/paper-trading identifier introduced anywhere in
    the new code (`test_no_execution_path.py` extended and green).
13. Full regression: required-still-passing journeys J-01–J-05 and J-07 stay green — full backend
    suite passes, engine equivalence test passes, `apps/frontend/` diff stays empty.

## Notes for reviewer / QA / auditor

- This is a **full-depth, goal-completing** iteration touching the champion pointer and PnL
  ledger — expect the auditor to specifically re-verify (not just trust) the crash-safety ordering
  and the "no train-only promotion" gate, per the phase spec's own NOTES.
- Only the goal-evaluator (not this plan, not the developer) may declare GOAL_ACHIEVED, and only
  after the deterministic gates and a two-key confirm. This plan marks no journey as passing.
- Lessons carried forward (surface to developer): don't silently break
  `_class_scaled_invalidation`'s level-relative-vs-entry-relative fallback when re-backtesting
  `structure_tape` for the comparison (iter-5); the committed PG fixture only ever yields class-C
  / below-min-n trades, so any ≥-min-n survivor test must use a **synthetic** fixture, never the
  shipped PG fixture (iter-3); any new `Config` field must join the `config_fingerprint` excluded
  set or J-07 breaks (iter-1) — prefer adding none.
