# goal-tape_to_profit-iter-7 Audit Report

**Date:** 2026-07-03
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-07 — the candidate-sweep harness with its hold-out promotion gate — is genuinely and fully
delivered. I verified the headline behavior **live** (not from the handoff): `python -m
app.research.pnl_scan --out <path>` on the committed fixtures exits 0, reports one candidate
(`candidate-faster-warmup`) as a non-survivor, leaves the champion at `v1/default`, keeps the
default fingerprint pinned at `4d665603569b9dbf`, and produces byte-identical output across two
independent fresh-state runs. Every Definition-of-Done clause and all ten anti-goals hold up under
direct code reading and independent test execution. The verdict carries `_WITH_GAPS` only because
of a small number of **minor, acceptable, non-blocking** limitations (documented below): a
cosmetic failure-message polish on the one un-wrapped promotion write, one unused import, and the
one-train/one-hold-out constraint on *automatic* promotion (which matches the shipped state and is
an out-of-scope consequence of reusing the existing ledger writer verbatim). None compromises the
phase goal; no audit fix was required.

---

## 2. Findings

### Backend Findings

**B1 — CORRECTNESS (verified correct, no change): overfit labeling is precise, not sloppy.**
`app/research/pnl_scan.py:337` defines `overfit = train_positive and not survivor`, and
`train_positive` requires the summed train delta to be strictly `> 0` on BOTH R and $
(`_is_positive`, line 200-201). On the committed fixture the candidate's train delta is **exactly
`0.0`** (identical trades — the earlier warm-up read does not move this fixture's arm instant), so
the live report correctly shows `overfit: false` and `survivor: false` — a *plain non-survivor*,
not a mislabeled overfit. This is more honest than the QA test plan's prose implied (see T2) and
is exactly what the module docstring promises ("a candidate that never looked good on train is
honestly just a non-survivor, never mislabeled overfit"). DoD bullet 2's "non-survivor/overfit"
label is satisfied via `survivor: false` for the stated reasons (hold-out net R negative **and**
n=1 < min 5 — both independently sufficient, both present in the live report).

**B2 — GAP (documented, safe, not fixed): the champion-pointer write in `_promote` is not wrapped
in an explicit `ScanError`, and no test injects a live failure at that exact write.**
`app/research/pnl_scan.py:256` calls `store.set_champion_pointer(...)` un-wrapped, whereas the
preceding ledger append (line 238) is wrapped. I traced the failure path rather than assume it is
unsafe: `JournalStore._do_write` (`store.py:703-705`) **re-raises** any worker exception
synchronously, so a pointer-write failure propagates loudly (uncaught → traceback → non-zero exit),
`--out` is never written, and the resulting state (ledger row committed, pointer unmoved) is the
*recoverable, detectable* orphan the module's ledger-first ordering is designed around — a re-run
re-hits the ledger's `DuplicateEnhancementError` and surfaces it as an explicit `ScanError`
("already exists … a PRIOR promotion attempt likely crashed"). That recovery path **is** tested
(`test_pnl_scan.py:416` `test_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append`).
The plan (Design Note 2) explicitly sanctioned ledger-first ordering "as long as the failure mode
is one explicit, honestly-surfaced error with no silently-inconsistent state" — which holds. So
this is a cosmetic polish (raw traceback vs. clean `ScanError` message) plus a missing
direct-injection test, not a correctness or anti-goal defect. **Not fixed** (GAP-level, behavior is
safe and plan-sanctioned; wrapping it and adding a monkeypatched-failure test is the reviewer's
suggested future touch). Matches reviewer issue #2.

**B3 — GAP (documented, honestly surfaced): automatic promotion is limited to exactly one train +
one hold-out dataset.** `_promote` (`pnl_scan.py:221`) returns
`{"promoted": False, "note": "… automatic promotion requires exactly one of each …"}` when more
than one dataset per split is registered — a structural consequence of reusing
`pnl_ledger.append_validation_row` **verbatim** (`pnl_ledger.py` is unmodified — confirmed
zero-diff — per the spec's "no second append path"). This matches today's shipped state exactly
(one train, one hold-out) and the SCAN still fully evaluates and reports every dataset per split
regardless of count. The limitation is **explicit and honest** (a `note` in the report, never a
silent skip or an arbitrary guess), so it does not violate the honest-failure anti-goal. Documented
as a forward-looking limitation, not a defect in current behavior. Matches the handoff's own Known
Issue.

### Frontend Findings

**None.** Backend-only iteration (`Frontend Present: no`). Zero frontend files changed. The J-05
`/performance` champion summary reads `GET /research/profiles`, whose serving now sources the
champion from the persisted pointer — proven end-to-end through the real HTTP route by
`test_profiles_api.py:111` (`test_served_champion_reflects_a_moved_pointer`). On the shipped
fixtures the sweep yields zero survivors, so the page is visually unchanged. Confirmed correct.

### Test Findings

**T1 — OBSERVATION (not fixed): unused `import time` in `store.py:36`.** Confirmed genuinely unused
— the store never calls the wall clock itself (every write takes `wall_ts` from the caller, e.g.
`set_champion_pointer`), and the only `time.` token in the file is prose inside a docstring
(line 787). Dead code, zero functional impact. Left in place per audit scope discipline (fixing it
is the reviewer's/a cleanup pass's job). Matches reviewer issue #1.

**T2 — OBSERVATION (no code change): QA test-plan prose mis-describes the fixture candidate as
"overfit / train-positive."** The QA functional test plan (`…-test-plan.md` TC-01 step 6, TC-07)
states the fixture candidate is `overfit: true` with "positive train net R/$". The actual fixture
has train delta exactly `0.0` (see B1), so the correct label is `overfit: false` (plain
non-survivor). The **implementation and its unit test are correct** (`test_pnl_scan.py:170` asserts
`overfit is False`), and the QA *results* table (TC-07) did record the real value
("Test data shows overfit=false"). Only the test-plan narrative is imprecise. No implementation
impact.

---

## 3. Domain Assessment

The core domain logic — the promotion gate — is correct, honest, and well-guarded:

- **Single computation path.** Every backtest goes through the existing
  `BacktestJobManager.create` + `run_sync` (the J-03/J-04 path); the module reads persisted row-31
  aggregates verbatim and computes only candidate-minus-champion deltas — never a second PnL
  computation. `pnl_ledger.py` and `app/mcp/` are both confirmed zero-diff.
- **Single champion source.** The hardcoded `{STRATEGY_V1_ID, PROFILE_DEFAULT}` constant is retired
  from the serving path; `profiles_projection` reads `store.get_champion_pointer()` verbatim and
  carries **no** id literals (enforced by `test_profiles_module_carries_no_second_copy_of_the_id_strings`).
  The one setter is source-scan-guarded to `pnl_scan.py` only (`test_pnl_scan.py:383`). No surface
  infers the champion from the ledger (grep-confirmed).
- **Promotion gate, both ways.** `survivor` requires hold-out net R AND net $ positive AND
  `candidate_n ≥ promotion_min_sample_size`; tests exercise below-min rejection despite positive
  hold-out (`:264`) and at-or-above-min promotion (`:282`). `robustness` is per-dataset (`robust`
  iff every individual train dataset positive) — proven distinct from the aggregate by the
  two-train-dataset `speculative` test (`:324`). Overfit is never promoted (`:349`).
- **Config discipline.** `promotion_min_sample_size` is a dedicated config field (not a magic
  number) and is correctly **excluded** from `config_fingerprint` (`config.py:1278`), matching the
  `pnl_min_sample_size` precedent — a decision-only threshold that never shapes persisted trade
  content. I confirmed the pinned fingerprint is still `4d665603569b9dbf` live, so the exclusion is
  not merely argued but verified.
- **Migration honesty.** The v9→v10 `champion_pointer` migration is covered by 8 mirror tests,
  including the critical "never re-seed over a moved pointer" property
  (`test_journal_migration.py:1568`) and verbatim preservation of a pre-existing ledger row
  (`:1506`). Seeding the singleton pointer (vs. leaving it empty) is the one deliberate,
  documented exception to "a migration never fabricates a row" — justified because the pointer is a
  required setting, not a record of an event.
- **Anti-goals (all ten hold).** No execution path (test_no_execution_path scans `pnl_scan.py`
  explicitly, `:116`); no profit claims (the `REGISTER` "simulated — … not indicative of live
  results" caveat stamps the report); default frozen (fingerprint pinned, observer-equivalence
  7/7); no train-only promotion; no ML (config-enumerated, fixed seeds, deterministic); honest
  failure states (corrupt dataset → `ScanError`, nothing written, `:401`; zero candidates → exit 0,
  `:186`); single source of truth; MCP zero-diff; persistence scoped to the one new table;
  `docs/goal.md` untouched.

Test quality is high: assertions are tight and exact (e.g. `delta_net_r == -0.5062000000002079`,
`candidate_n == 1`, `config_fingerprint() == "4d665603569b9dbf"`), datasets are recorded through
the **real** `DatasetStore` public path (never hand-crafted report JSON), and the champion-serving
and CLI paths are exercised through the real HTTP route and the real `main()` entry point
respectively. No test passes by accident or on a loose "accepts multiple outcomes" assertion.

**Independent verification performed by this audit:**
- Live CLI sweep on fixtures → exit 0, `survivor: false`, champion `v1/default`, `promotion: null`,
  register caveat present, full per-dataset breakdown. ✓
- Two independent fresh-state runs → `cmp` byte-identical. ✓
- `config_fingerprint()` == `4d665603569b9dbf` and `get_champion_pointer()` == `v1/default` after a
  live scan, ledger rows == 0 (no fabricated row). ✓
- Ran `test_pnl_scan.py` (12) + `test_profiles_api.py` (5) + `test_no_execution_path.py` (4) +
  `test_observer_equivalence.py` (7) + `test_journal_migration.py` (incl. the 8 v9→v10 tests) →
  **97 passed, 0 failed**. ✓
- `_do_write` re-raise behavior read directly to confirm B2 is safe (not a silent inconsistency). ✓
- `app/mcp/` and `app/research/pnl_ledger.py` confirmed zero-diff via `git diff`. ✓
- **Full backend suite ran to completion under this audit → exit 0, `[100%]`, no failures**
  (independent of the handoff). Consistent with the reviewer's independent run (1026 collected,
  exit 0, 1 skipped, +21 net new tests over the iter-6 baseline of 1004/1 with no deletions).

---

## 4. Fixes Applied During This Audit

**None.** No CRITICAL or IMPORTANT issue was found. The three GAP/OBSERVATION items (B2, B3, T1,
T2) are minor, safe, and — for B2 and B3 — explicitly sanctioned by the execution plan and the
spec's out-of-scope boundary; fixing them would be scope creep. They are documented above as
known, acceptable limitations.

---

## 5. Recommended Next Step

**Proceed.** J-07 genuinely passes and closes the profit-research era's measurement story: the
enhancement loop can now honestly convert a hold-out survivor into a champion move plus a
provenance-stamped ledger row, or honestly report "no survivor" (exit 0, nothing moved) — verified
live on the committed fixtures. All required-still-passing journeys remain green (observer-
equivalence 7/7; J-05 serving path re-proven through the real route). This iteration is a valid
GOAL_ACHIEVED candidate for the next evaluation, subject to the deterministic gates and the two-key
confirm.

Optional future polish (non-blocking, do NOT gate the goal on these): (1) wrap
`set_champion_pointer` in `_promote` in an explicit `ScanError` and add a monkeypatched
failure-injection test (B2); (2) remove the unused `import time` from `store.py` (T1); (3) if a
second train/hold-out dataset is ever registered, extend the promotion path beyond the current
single-pair ledger-writer shape (B3).
