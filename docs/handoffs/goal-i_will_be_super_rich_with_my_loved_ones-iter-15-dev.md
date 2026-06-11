# goal-i_will_be_super_rich_with_my_loved_ones-iter-15 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-15
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The **evidence layer begins** (J-58): a resolved-or-ended thesis now carries honest, deterministic
**excursion outcomes** — max favorable / max adverse excursion in **R units** per configured horizon,
anchored at the **first published confirmation** AND separately at the **entry mark** (two
populations, never pooled), each with the ternary outcome `+1R_first | −1R_first |
neither_within_horizon` by first touch, spread-at-anchor beside it, and explicit **TRUNCATED** flags
where the stream end / a gap cut a horizon short.

- **Config — excursion research defaults** (`app/config.py`): `excursion_horizons_seconds =
  (10, 30, 60, 120)` (goal.md's predictive-value family) + `excursion_target_r = 1.0`, documented
  research defaults calibrated against the seeded J-58 substrate (J-42's SIM-BUYER, invalidation 98.0,
  R ≈ 2.21). The calibration is proven by a unit test: the 10/30/60s horizons fully elapse at
  `neither_within_horizon` (a partial favorable excursion honestly recorded as MFE, under +1R) — at
  least one **completed** horizon — and the 120s horizon is **truncated** at the stream end (~77s past
  confirmation) — at least one stream-end-truncated horizon. `journal_schema_version` bumped 6 → 7.
  The config-fingerprint shift is the intended honesty mechanism (analytics never pool across
  fingerprints), not a defect.
- **Single-owner excursion calculator** — new module `app/research/excursions.py`: an in-memory
  `ExcursionTracker` fed ONLY by the research-monitor observer (read-only over the engine). Arms the
  confirmation population once at the first published `confirming` (reference = that event's persisted
  `last`; spread-at-anchor stamped once, the row-18 moment-value pattern); arms the entry population
  once at the recorded entry mark (verbatim price; reuses row-18's stamped `spread_at_mark`); R basis
  via the **one shared `marks.r_basis` helper** (never a second formula); running MFE/MAE in R over
  each horizon window; ternary by **first touch** in logical time; truncation at stream end / gaps
  (never bridged, never extrapolated); the two populations fully segregated. `compute_and_persist_
  excursions(...)` is the persist-once seam; `not_tracked_record()` is the explicit honest marker for
  tracker-unavailable paths (restart sweep).
- **Schema v6 → v7** (`app/research/store.py`): one additive `theses.excursions` TEXT column;
  idempotent versioned migration step (one `BEGIN IMMEDIATE`, no backfill — pre-v7 rows keep the key
  ABSENT); `set_excursions(...)` writer (single writer queue); read-back on `ThesisRecord.excursions`;
  a committed **v6 fixture** (`tests/fixtures/journal_v6_schema.sql`) proving the migration; a
  **persistent-DB check** (close → reopen → byte-identical served values, proving no read-time
  recomputation).
- **Wired the persist-once seam at all defining moments** (`app/research/monitor.py`,
  `app/research/routes.py`): the monitor holds the tracker (created at `set_thesis` / re-attach),
  feeds it from `on_event`, arms confirmation in `_evaluate_verdict`, and truncates + persists at the
  invalidation auto-resolve and the stream-end/stop expiry. The **stream-end survival path**
  (`_detach_not_evaluated`, the J-58 script's exact endpoint) truncates + persists for a surviving
  entry-marked thesis with NO resolution. The action route arms the entry population on an entry mark;
  the user-resolve route persists via the monitor's tracker; the restart sweep persists the
  `not_tracked` marker.
- **Serve verbatim, one endpoint**: `GET /research/journal/{id}` (`build_journal_detail`) serves the
  persisted `excursions` record verbatim with honest omission (pre-v7 ⇒ key absent). No new endpoint,
  no second serving path, no client-side arithmetic.
- **Taxonomy (additive)** (`app/research/taxonomy.py`): `taxonomy_payload()["excursions"]` ships the
  ternary-outcome labels, the truncated label, the two population titles, the per-population
  not-applicable copy, the not-tracked copy, and the R-basis caption — the frontend hardcodes none.
- **Frontend** (`apps/frontend`): new "How far the tape went (R)" excursion section on
  `/journal/[id]` (`JournalDetailView.tsx`) — two visually separate blocks ("From first confirmation",
  "From entry mark"), each with its anchor (true-clock time, mono reference price, spread-at-anchor, R
  basis) and per-horizon rows (horizon, MFE/MAE in R, the ternary outcome chip, a TRUNCATED flag).
  Honest absence: a missing population renders explicit not-applicable copy; `tracked:false` renders
  not-tracked copy; a pre-v7 thesis renders honest-omission copy. R-units only, descriptive copy, no
  currency, no prediction. **Carry-along cleanup:** the grade-chip emerald shade is unified
  (`bg-emerald-900/40 border-emerald-700`) between `JournalDetailView.tsx` and `JournalTable.tsx`.
  Types added to `lib/types.ts` (`ExcursionHorizon`, `ExcursionPopulation`, `ThesisExcursions`,
  `ExcursionTaxonomy`).

## Files Changed

- `apps/backend/app/config.py` -- excursion research defaults; `journal_schema_version` 6 → 7
- `apps/backend/app/research/excursions.py` -- NEW single-owner tracker + persist seam
- `apps/backend/app/research/marks.py` -- extracted the shared `r_basis(reference, invalidation)` helper (row 27 / row 20 share one formula)
- `apps/backend/app/research/store.py` -- v7 schema column + migration + `set_excursions` + read-back
- `apps/backend/app/research/monitor.py` -- tracker lifecycle; arm-on-confirming; persist at invalidation / expiry / survival paths; entry-arm + user-resolve persist helpers
- `apps/backend/app/research/routes.py` -- serve `excursions` on journal detail; arm entry on mark; persist on user resolve; not-tracked marker on restart sweep
- `apps/backend/app/research/taxonomy.py` -- excursion display copy in `taxonomy_payload()`
- `apps/backend/tests/test_excursions.py` -- NEW pure calculator + J-58 calibration matrix (17 tests)
- `apps/backend/tests/test_research_excursions_integration.py` -- NEW real-stack monitor+store+detail matrix (6 tests)
- `apps/backend/tests/test_journal_migration.py` -- v6 → v7 migration + persistent-DB check tests; updated chained-version assertions
- `apps/backend/tests/fixtures/journal_v6_schema.sql` -- NEW committed v6 fixture
- `apps/frontend/lib/types.ts` -- excursion + taxonomy types
- `apps/frontend/components/JournalDetailView.tsx` -- the excursion section (two segregated blocks)
- `apps/frontend/components/JournalTable.tsx` -- grade-chip emerald shade unified with the detail view

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **586 passed, 1 skipped** (the skip is the pre-existing credentialed live-integration test
that needs vendor keys — unrelated to this iteration). Includes 17 new excursion-calculator tests, 6
new real-stack integration tests, and the v6 → v7 migration + persistent-DB checks. The
observer-equivalence test still passes (engine outputs byte-identical with the research layer + the
excursion tracker attached). No engine/classifier/provider/chart/feature file is in the diff (J-68
sentinel holds).

Command: `cd apps/frontend && npm run build` (and `npx tsc --noEmit`)
Result: build succeeds, type-check clean (exit 0). Routes `/`, `/journal`, `/journal/[id]` compile.

## Known Issues

- **None blocking.** The J-58 truncation calibration depends on the watch ending before ~120s of
  *logical* time elapses past the first confirmation. SIM-BUYER grinds slowly, so a normal QA run
  (stop / stream-end well before that) reliably leaves the 120s horizon truncated while 10/30/60s
  complete — proven deterministically by `test_j58_sim_buyer_exercises_both_a_completed_and_a_
  truncated_horizon`. If a future QA run watches for an extraordinarily long time, the 120s horizon
  could complete too (still correct — just one fewer truncated horizon); the calibration test pins the
  intended behaviour at the spec's stop point.
- **`anchor_wall_ts` is wall-clock** (true-clock display only, mirroring every timeline `wall_ts`), so
  it is the one excursion field that legitimately differs run-to-run; every MEASURED value (R bases,
  MFE/MAE, ternary outcomes, truncation, logical anchors, reference prices, spreads) is byte-identical
  across seeded re-runs (the determinism integration test strips only the wall-clock display field
  before comparing — the same treatment the codebase gives timeline wall timestamps).
- **Config-fingerprint changed** (intended): every record created after this iteration carries a new
  `config_fingerprint` because `excursion_horizons_seconds`/`excursion_target_r` joined the config
  dataclass. This is the honesty mechanism (analytics never pool across fingerprints), documented in
  the config and the iter spec NOTES — not a regression.
