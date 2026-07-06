# goal-tape_to_profit_support_resistence-iter-6 Audit Report

**Date:** 2026-07-06
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-06 — the final Must-have of Era 4 — is genuinely realized. `pnl_scan.py` gains an additive
STRATEGY axis (`--strategy structure_tape`) that reuses the existing per-split comparison and
crash-safe promotion machinery verbatim; the load-bearing "no train-only promotion" gate is
enforced in backend logic, the frozen `default`/`v1`/engine foundation is verifiably untouched
(I confirmed `v1`/`default` aggregates are byte-identical with vs without a `bar_store`, and the
config fingerprint `4d665603569b9dbf` is unmoved), and the committed fixtures honestly yield
"no survivor" at exit 0 with byte-identical determinism. No CRITICAL or IMPORTANT issue found;
no fix required. Three OBSERVATION-level notes are recorded below.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): `overfit=true` on the committed fixtures where `structure_tape` abstained (n=0 on train)**
`apps/backend/app/research/pnl_scan.py:436` (`overfit = train_positive and not survivor`). On the
committed PG fixtures, `structure_tape` trades **zero** times on the train window (`candidate_n=0`,
confirmed live). The train delta reads *positive* only because champion `v1` itself lost money on
that exact window (the era-3 finding) while `structure_tape` did nothing — so `train_positive=True`
and, with `survivor=False`, the derived flag reads `overfit=True`. Semantically this is a loose
label (the strategy abstained; it did not "overfit" a spurious train edge), but it is **not a
defect**: (a) the label uses the era-3, spec-mandated, reused-verbatim formula the plan explicitly
forbids modifying; (b) it is a *derived, non-gating* field — the promotion decision hinges only on
`survivor`, which is correctly `False`; (c) the underlying honest datum (`candidate_n=0` on train)
is fully present in the per-dataset breakdown, so nothing is concealed; and (d) the anti-goal
"train-only wins are labelled overfit and rejected" is literally satisfied. Disclosed by the dev in
the handoff's Known Issues. **Not fixed** — changing the formula would be scope creep explicitly
prohibited by the spec and would risk perturbing the frozen profile axis.

**B2 — OBSERVATION (observation): strategy axis compares against the champion at `profile=default`, not `champion["profile"]`**
`apps/backend/app/research/pnl_scan.py:365` (`champion_strategy_id, champion_profile = champion["strategy_id"], PROFILE_DEFAULT`).
The strategy axis holds the champion's profile fixed at `default` rather than reading
`champion["profile"]`. This is **exactly what the spec prescribes** ("compared against the
champion's CURRENT `strategy_id` … also at `profile=PROFILE_DEFAULT`") and is correct on the
foundation store where the champion is `{v1, default}`. It would only diverge from the "true"
champion after a *prior* profile-axis promotion to a **non-default** profile — a state that cannot
arise on the committed fixtures (no survivor) and is outside the Era-4 hypothesis. Recorded as a
documented design assumption, not a gap.

### Frontend Findings

None. Frontend Present: no. `git status --porcelain apps/frontend/` returns empty — the zero
frontend diff that keeps J-07's cockpit leg green without a new screenshot (iter-0 lesson) is
confirmed.

### Test Findings

**T1 — OBSERVATION (observation): the pre-written QA test plan speculates a CLI/JSON shape that the implementation deliberately does not match**
`reports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md` (authored before the code)
assumes `--splits train`/`--splits hold_out` flags, field names `strategy_tape_R`/`v1_R`/`delta_R`,
and `overfit=false` for a below-min-n hold-out. None of these match the reused-verbatim
implementation (single invocation reports both splits; `champion`/`candidate` field names;
`overfit` per the reused formula). This is a **plan-vs-implementation divergence, not a code
defect** — the implementation correctly follows the spec's "reuse the machinery verbatim"
instruction, and the dev/reviewer/QA all triaged it. The real acceptance is the 9 new code tests,
which use **tight** assertions (exact `champion_after` dicts, exact `promotion`/`enhancement_id`,
exact `candidate_n` 0/1, exact ledger-row counts, `pytest.raises(ScanError, match="already
exists")`). Verified independently.

---

## 3. Domain Assessment

The core domain logic — the promotion gate — is correct and honestly enforced:

- **"No train-only promotion" (the critical anti-goal) holds.** `survivor` is true iff the summed
  hold-out delta is positive on **both** net R and net $ **and** the summed hold-out candidate `n`
  ≥ `promotion_min_sample_size` (`pnl_scan.py:430-433`), and promotion runs only `if survivor`
  (`:449`). A positive-train / failing-hold-out synthetic fixture yields `overfit=true`,
  `survivor=false`, no ledger row, no pointer move
  (`test_strategy_axis_overfit_…`, run green). The gate lives entirely in backend logic; there is
  no frontend to bypass it.
- **Crash-safe promotion order verified.** `_promote` appends the ledger row **then** moves the
  pointer (`pnl_scan.py:307-326`); a mid-promotion crash leaves a durable ledger row + unmoved
  pointer, and a re-run hits the ledger's `DuplicateEnhancementError` → explicit `ScanError`
  (`test_strategy_axis_mid_promotion_crash_…`, green; asserts no second row).
- **Frozen foundation genuinely intact.** I directly re-ran a `v1`/`default` backtest with
  `bar_store=None` and with a real `BarStore` and got **byte-identical aggregates** — so threading
  `bar_store` through the profile axis (the one non-trivial change to the existing path) does not
  perturb `v1`/`default`. `config_fingerprint()` returns `4d665603569b9dbf` (unmoved);
  `test_profile_equivalence.py` is 13/13 green; `config.py`, `store.py`, `pnl_ledger.py`,
  `edge_report.py` are untouched (`git status` clean).
- **Single source of truth preserved.** Every backtest goes through the one
  `BacktestJobManager.create` + `run_sync`; `_measurement`/`_dataset_rows`/`_split_summary` are
  reused verbatim (the removed-lines diff shows no new R/$/edge arithmetic); `set_champion_pointer`
  is called from exactly one file (`test_champion_pointer_setter_is_called_from_exactly_one_source_file`,
  green). The ledger provenance `strategy_id`/`profile` is derived from the winning candidate's own
  report (`pnl_ledger.py:178-179`), so a promoted `structure_tape` row correctly stamps
  `strategy_id=structure_tape`, `profile=default`.
- **Honest fixture outcome + determinism, verified live.** Two independent fresh-state
  `--strategy structure_tape` CLI runs produced **byte-identical** `--out` bytes; exit 0;
  `survivor=false`; `train_n=0`, `holdout_n=1` (below the minimum of 5); `holdout_delta_r ≈ -0.343`
  (a genuine hold-out loss); `champion_before == champion_after == {v1, default}`; `promotion=null`;
  nothing written to the ledger. `get_champion_pointer()` returns only `{strategy_id, profile}`
  (no timestamp), which is why the report is byte-stable across runs.
- **Audit B1 resolved by disclosure, not re-arming.** Every report carries
  `provenance.assumptions` naming the breakthrough arm's loose static-price-position anchor — a
  static, config-independent string that does not perturb byte-identical reruns
  (`pnl_scan.py:143-150, 472`), confirmed present in the live report.
- **No live execution path.** The new grep-guard test is non-vacuous — it positively asserts the
  new axis code (`candidate_strategy_id`, `set_champion_pointer`) is scanned, then asserts none of
  the comprehensive TIER1/TIER2 order/broker/routing/paper-trading patterns appear
  (`test_no_execution_path.py`, 6/6 green). The champion move is a pointer write, not an order.

**Independent test verification (not trusting the handoff):**
- `test_pnl_scan.py` + `test_no_execution_path.py` + `test_profile_equivalence.py`: 42 passed.
- Full backend suite (`.venv/bin/python -m pytest tests/ -q`): **exit code 0** (pytest returns 0
  only when every collected test passes) — reproducing QA's 1146 passed / 1 skipped / 0 failed.
- `grep -c "def test_strategy_axis"` = 9 new tests; 21 total in the file (12 pre-existing
  **unmodified** — the removed-lines diff of `test_pnl_scan.py` is empty, confirming backward
  compatibility).

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT finding was identified. All three findings are OBSERVATION-level and
either spec-conformant by design (B2), a disclosed cosmetic quirk of a spec-mandated reused formula
(B1), or a plan-vs-implementation divergence rather than a code defect (T1). Applying a "fix" to any
of them would be scope creep — B1 in particular would require editing the reused-verbatim `overfit`
formula, which the spec explicitly forbids and which would risk the frozen profile axis.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (no critical/important findings). |

---

## 5. Recommended Next Step

**Proceed.** J-06 is genuinely complete: the named-strategy comparison, the hold-out-only promotion
gate, crash-safe promotion, the frozen-foundation guarantee, B1 disclosure, backward compatibility,
and the honest "no survivor at exit 0" fixture outcome are all implemented and independently
verified. As the final Must-have, this iteration is ready for the **goal-evaluator** to run its
deterministic gates and two-key confirm for a GOAL_ACHIEVED decision (only the evaluator may declare
it). The two OBSERVATIONs (B1's loose `overfit` label when a strategy abstains; B2's `profile=default`
assumption on the strategy axis) are informational and need no action this iteration.
