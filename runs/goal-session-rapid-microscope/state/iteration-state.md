# Iteration State — rapid-microscope

**After iteration:** 4 · **Date:** 2026-08-17 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01..J-04) · 5 failing (J-05..J-09) · 1 partial (J-10) — 10 total

## Active blockers

- **Evidence lane, next iter (BINDING):** iter-4's browser pass was a blanket SKIP — zero
  screenshots, `journey-scripts/J-10.json`'s sentinel never ran though TC-20 required it. A
  `Frontend Present: no` spec must NOT skip a named required-still-passing set. Run it.
- **Owner ruling #1 (human):** a depletion measurement's `available_at` is stamped one quote early
  (`micro_observer.py:636/:657`); iter-4 scoped around it. Due before J-05/J-09 measure a liquidity outcome.
- **Owner ruling #2 (human):** `derive_family_id` omits the CORPUS term `rapid-validation-spec.md:77`
  names for `SCOUT_MAX_VARIANTS_PER_FAMILY`, and `grid_version` is hashed into `spec_hash` (an
  identical candidate re-registered later over-counts union-N). Re-keying rewrites ledgered rows.
- **Dev, before J-08 renders:** one kill line reads "approximately None bps"; scout's served
  numerics are absent from `_PRICE_ARITHMETIC_FIELDS` and copy discipline.

## Last 2 verdicts

- iter 4: ESCALATE — J-04 built and verified end to end by the evaluator, but the browser lane
  produced no evidence at all (no agent owned TC-20) and J-05 is the leakage-critical journey;
  only ESCALATE reliably survives the depth arbiter's budget check.
- iter 3: ESCALATE — J-03 landed, but the engine demoted that full-typed iteration to lean
  (`budget-breach`) so the auditor never ran; iter-4's auditor then caught 4 integrity faults.

## Do not redo

- J-04 is DONE (`scout.py`, `scout_ledger.py`, 3 routes in `micro_routes.py`) — verified on live
  code: closed-vocabulary rows, tamper + tail-truncation detection, union-N stable over 3 re-runs.
- Iter-3's two honesty fixes are DONE (real-store payload): `band_touch_count` is
  `{"status": "not_enumerated", "count": None}`; `playbook_integrity_errors` is surfaced.
- Frozen foundations re-checked PASSING (fingerprint `08e471b10130e1e2`, 6 `referee_*` hashes vs
  iter 0, engine + playbook byte-unchanged, 18 snapshots = 3,815,933 rows, suite 2949/8/0).
- `journey-scripts/J-10.json` is REPAIRED and green (iter-3). Re-run unmodified; do not re-point.
- Shares/clock horizons are DELIBERATELY refused (`ScoutUnsupportedHorizonError`); restoring them
  is real work (block sizing + subsampling + a trap).
