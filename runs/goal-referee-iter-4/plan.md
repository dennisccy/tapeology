# goal-referee-iter-4 Execution Plan

**Session:** referee (Era 6 "The Referee") · **Target journey:** J-03 · **Required-still-passing:**
J-01, J-02, J-10 · **Depth:** full (mandatory — iter-3 verdict was ESCALATE) · **Prior verdict:**
ESCALATE, not a halt — nothing regressed, no anti-goal violated; a real correctness defect in
already-shipped-but-unconsumed code must be fixed before J-04–J-08 build on top of it.

This plan matches the phase spec's TC-1..TC-15 exactly; treat `docs/phases/goal-referee-iter-4.md`
as the source of truth for full test contracts. This file is the condensed execution guide.

## What to Build

- **Fix the exact-enumeration p-value floor bug in `permutation_test`**
  (`apps/backend/app/research/referee_stats.py`). In the `if use_enumeration:` block (currently
  `:409`), the per-combination `g2_sum = total - g1_sum` (`:424`) disagrees in its last
  representable digit with `_t_statistic`'s own `math.fsum(group2)` accumulation (inline at `:239`
  inside `_t_statistic`, `:219`). This lets the TRUE observed grouping narrowly fail `_is_extreme`
  (`:262`/`:430`) and get dropped from the extreme count, so `p` can fall to HALF its own
  mathematical floor (`2 / (draws_used + 1)`). Fix: compute each enumerated combination's group-2
  sum by direct accumulation over that combination's own complement values (the same method
  `_t_statistic` uses), never by subtracting from a separately-accumulated session total. Verified
  bug still present at these exact lines as of this plan's authoring (re-grepped, not assumed from
  the spec — spec's own NOTES warn line numbers drift).
- **Prove the fix both directions**, in `apps/backend/tests/test_referee_stats.py`:
  - TC-1: the evaluator's exact minimal repro now returns `p == 2/7`, not the previously-served
    `1/7`.
  - TC-2: a freshly seeded-generated property test (thousands of cases, 2-vs-2 and 1-vs-4 shapes,
    all three `sidedness` values) asserting `p >= 2 / (draws_used + 1)` with zero violations.
  - TC-7: direct coverage for `_draw_indices_without_replacement` (`:164`) — KEEP the function
    (documented without-replacement primitive J-04 is expected to reuse), do not delete.
  - TC-8: an `n1 > 1, n2 == 1` fixture inside the seeded branch's fast path, against a from-scratch
    reference (mirrors the existing hand-verified `n1 == 1` case).
- **Close the oracle coverage hole**, in `apps/backend/tests/test_referee_oracles.py`:
  - TC-3: a new calibration case whose permutation space is `<= REFEREE_ENUMERATION_THRESHOLD`
    (8,192, confirmed at `:96`) built from non-round decimals — the suite's first case that
    genuinely enters the enumeration branch — checked for both the floor property and calibration
    within `REFEREE_ORACLE_SIZE_TOLERANCE`.
  - TC-4: a SECOND mutation fixture reproducing the PRE-FIX subtraction bug (anti-conservative
    direction), paired with the existing over-cautious-only mutant, proving the suite catches both
    failure directions.
- **Re-pin the attestation and version-bump**: re-capture `_ATTESTATION_EXPECTED`/
  `_ATTESTATION_TOLERANCE` (`:612`/`:618`) by running `run_oracle_attestation()` against the FIXED
  code; bump `STATS_CORE_VERSION` (`:121`) from `"referee-stats-v1"` to `"referee-stats-v2"`.
  TC-6: `verify_oracle_attestation()` rejects an otherwise-matching attestation whose
  `stats_core_version` reads the old string.
- **Close Lead 1** in `apps/backend/app/research/referee_evidence.py`, additive-only: one shared
  helper — replacing the two independent copies of the same `(detector_basis, config_fingerprint)`
  staleness check — called by both `playbook_occurrence_readiness()` (`:225`, the `continue` at
  `:240-244`) and `playbook_observations()` (`:649`, the `continue` at `:696-700`). Note the two
  call sites hold different record shapes (raw `PlaybookStore` record vs. a pre-built projection
  dict that already carries `record_detector_basis`) — the shared helper's signature should accept
  the basis/fingerprint values already resolved by each caller, not assume a common record shape.
  Adds `stale_basis_dates: [{"session_date": str, "record_detector_basis": str}]` to both response
  dicts; zero change to any currently-served field's value. TC-9 extends the existing D3 fixture in
  `test_playbook_readiness_pools_newest_per_date_at_the_current_basis`; TC-10 adds one sibling test
  for `playbook_observations()`.
- **Dev handoff** at `docs/handoffs/goal-referee-iter-4-dev.md` (DoD requirement).

## Out of Scope / Guardrails — do not touch

- **The seeded (non-enumeration) branch's own `g2_sum = total - g1_sum`** (`:466`, inside the
  `else` branch starting `:438`). Explicitly out of scope per the phase spec: at Monte-Carlo scale
  (`REFEREE_B` = 10,000 draws) the ~1-ULP disagreement is far below sampling error, and the
  `p = (1 + extreme) / (b + 1)` formula's "+1" already accounts for the observed result
  unconditionally — it never needs the observed grouping to bit-match itself. Every existing
  oracle case (1, 2, 3a, 3b, 4, 5, 6 — all S>=10 sessions) runs through THIS branch; touching it
  would risk invalidating their already-pinned goldens (power 0.8950, BH rates 0.0114/0.9375,
  etc.) for zero benefit. Fix the enumeration branch ONLY.
- **Lead 2** (`_strategy_observation()`'s `epoch_anchor = dataset.get("epoch_anchor") or 0.0`) —
  investigated and deliberately DROPPED per T-1 (see phase spec NOTES + the fresh
  `state/assumptions.md` iter-4 entry). Do not touch `_strategy_observation`,
  `strategy_observations`, or `edge_report.py` (frozen this era regardless).
- Do not rewrite `referee_stats.py` or re-derive its already-shipped constants from the spec —
  fix the enumeration branch + its oracle gap, nothing else.
- Zero diff to: `docs/referee-statistical-spec.md` (implementation-fidelity fix, not a spec
  reinterpretation), `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`,
  `setups.py`, `edge_report*.py`, `backtests.py`, `pnl_scan.py`, `app/config.py`, `app/main.py`,
  any route file, any frontend file. Zero new `Config` field, zero new runtime dependency.
- No real registration/evaluation/null-build operator act — that machinery doesn't exist yet
  (J-04+).
- Process cleanup: exact-PID process-tree kill only — never `pkill -f` (iter-2 lesson: took down
  an unrelated project's backend, still not restarted).

## Agents Required

- backend-data: yes -- the `referee_stats.py` enumeration-branch fix, the paired oracle case +
  anti-conservative mutant, the attestation re-pin/version-bump, the two reviewer-flagged same-file
  test gaps, and the `referee_evidence.py` Lead-1 additive disclosure + shared helper, all with
  their test coverage per TC-1..TC-10.
- frontend-ux: no -- zero frontend file changes this iteration (this pipeline has one `developer`
  agent role that handles both backend and frontend; here only the backend-data half applies).

Frontend Present: yes

(No frontend code changes this iteration. Set to `yes` only because this session's binding rule —
`state/iteration-state.md` / the phase spec's own metadata — has J-10's regression sentinel ride
every iteration: browser-qa must still walk the cockpit, `/structure` AAPL Load, and every shipped
`/desk` section per the T-9 clean-rebuild discipline, with screenshots. J-03 and Lead 1 have no
live endpoint to smoke beyond the existing pytest-covered `GET /research/desk/referee/evidence`
route — no new browser interaction is required for the target work itself.)

## Files to Create/Modify

- `apps/backend/app/research/referee_stats.py` -- fix the enumeration-branch `g2_sum` computation
  (`:409-430` region); bump `STATS_CORE_VERSION` `:121`; re-capture `_ATTESTATION_EXPECTED`/
  `_ATTESTATION_TOLERANCE` `:612`/`:618` against the fixed build. Nothing else in this file changes
  (seeded branch `:438-467` byte-unchanged).
- `apps/backend/tests/test_referee_stats.py` -- add TC-1, TC-2, TC-6, TC-7, TC-8.
- `apps/backend/tests/test_referee_oracles.py` -- add TC-3 (enumeration-entering calibration case)
  and TC-4 (paired anti-conservative mutant); whole file must keep completing within
  `REFEREE_ORACLE_BUDGET_SECONDS` (120s).
- `apps/backend/app/research/referee_evidence.py` -- additive-only: one shared stale-basis-dates
  helper called from `playbook_occurrence_readiness()` (`:225`) and `playbook_observations()`
  (`:649`); adds the `stale_basis_dates` field to both.
- `apps/backend/tests/test_referee_evidence.py` -- extend the existing D3 fixture (TC-9); add one
  new sibling test for `playbook_observations()` (TC-10). Every other existing assertion in this
  file stays unchanged.
- `docs/handoffs/goal-referee-iter-4-dev.md` -- new dev handoff.

## UI Evolution

- New user-facing capability: none.
- New information displayed: none — `stale_basis_dates` is served but rendered nowhere (J-09,
  several iterations away, is the first UI consumer); `referee_stats.py` remains unconsumed by any
  route.
- New user actions: none.
- UI surface changes: none.
- Navigation changes: none.

## Key Test Scenarios

- TC-1/TC-2: the exact minimal repro returns the correct floor value; a broad generated property
  set finds zero floor violations across 2-vs-2/1-vs-4 shapes and all three sidedness values.
- TC-3/TC-4: the oracle suite gains a case that genuinely enters the enumeration branch (green,
  within tolerance) and a paired anti-conservative mutant that the suite DETECTS (miscalibrated or
  a floor violation) — proving both directions are guarded, not just the over-cautious one.
- TC-5/TC-6: `run_oracle_attestation()` on the fixed build returns
  `stats_core_version="referee-stats-v2"`, byte-identical across two calls;
  `verify_oracle_attestation()` rejects an attestation carrying the old `"referee-stats-v1"` string
  even when every other field matches.
- TC-7/TC-8: `_draw_indices_without_replacement` determinism + full-population coverage;
  `n1>1,n2==1` seeded fast path matches a from-scratch reference.
- TC-9/TC-10: `GET /research/desk/referee/evidence`'s D3 stale-basis fixture now discloses
  `stale_basis_dates` with every pre-existing field unchanged; `playbook_observations()` discloses
  the same for an equivalent fixture with zero change to `observations`/`coverage_by_date`/
  `coverage_shrink_disclosures`/`session_completeness`.
- TC-11/TC-12: full backend suite >= 2,495 pass / 8 skip, zero errors;
  `Config().config_fingerprint()` == `08e471b10130e1e2`; `EXPECTED_TOOLS` still exactly 20 entries;
  SHA-256 listing of every pre-existing playbook/dataset/journal store file byte-identical
  before/after (this iteration writes to no store at all).
- TC-13/TC-14: every pre-existing `test_referee_evidence.py` assertion passes unmodified except the
  two named additions; the iter-3 `referee_stats.py` import-ban guard + its counter-test still pass
  unmodified.
- TC-15: after `rm -rf apps/frontend/.next` + rebuild + restart, J-10's regression walk (cockpit
  sim tape/chart, `/structure` pinned-AAPL Load, every shipped `/desk` section) renders exactly as
  shipped, each evidenced by a screenshot.
