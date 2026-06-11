# goal-i_will_be_super_rich_with_my_loved_ones-iter-11 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-11
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

Entry risk flags at declaration (capability 26, J-49). When a thesis is declared, the system now
computes the full six-flag risk set ONCE from the live engine snapshot + config, freezes it on the
thesis (advisory, never blocking — creation always succeeds), and serves it verbatim as the additive
`risk_flags` projection key. Amber advisory chips render it on the thesis strip, each with its
measured plain-language margin.

- **Single flag-computation function** — `compute_risk_flags(snapshot, …)` in `app/research/monitor.py`,
  invoked exactly once inside `POST /research/thesis` (the same place `entry_context` is frozen), after
  all validation passes. The six flags, each reading canonical engine values verbatim:
  - `before_warmup` — declaration trade count below the classifier's own `warmup_min_events` (reused).
  - `invalidation_too_tight` — |last − invalidation| below `invalidation_too_tight_spread_multiple` ×
    current spread (NEW config research default).
  - `chasing_entry` — the favorable-side price-impact RETURN (the SAME `buy_price_impact` /
    `sell_price_impact` ÷ the canonical `reference_price` the classifier uses; direction-aware: buy for
    a long, |sell| for a short) already past `chase_return_threshold` (NEW config research default).
  - `wide_spread_illiquid` — the classifier's relative-spread gate VERBATIM (bps vs `max_stable_spread_bps`
    when a price basis exists, else absolute vs `max_stable_spread`) — no new threshold.
  - `low_trade_speed` — `trade_speed` below `min_trade_speed` VERBATIM — no new threshold.
  - `against_expected_tape` — setup-aware: a DEFINITE snapshot tape state (not `unclear`) not among the
    setup's expected premise states (derived from the frozen `tape_state_is` statements). A long
    absorption_reversal during `bid_absorption` is NOT flagged; during `seller_control` it IS.
- **Frozen with measured evidence** — each fired flag is stored as `{flag, label, evidence, measured}`:
  the taxonomy-owned label, the plain-language measured-margin sentence, and the raw canonical values
  behind it (so review can later show them with zero recompute). Chip labels + evidence templates live
  in `app/research/taxonomy.py` (row 24); the frontend hardcodes none of them.
- **Advisory, never blocking** — a maximally-flagged declaration still returns 200. The J-39 validation
  contract is untouched: incoherent input (wrong-side invalidation, missing/forbidden level, unknown
  enums) stays a 422 with NO flags computed or persisted.
- **Versioned migration v3 → v4** — `theses` gains a `risk_flags` TEXT (JSON) column;
  `journal_schema_version` bumped to 4 with an in-place idempotent `ALTER` step in `store._migrate`,
  proven against a committed v3-schema fixture. Pre-migration rows keep `NULL` — never backfilled; a
  NULL-flags thesis OMITS the `risk_flags` key from its projection (an absent key = "never assessed";
  an empty list = "assessed, nothing fired" — the two never collapse).
- **Additive `risk_flags` key on the row-15 projection** — re-exposed verbatim inside the single
  `build_projection`, so the live monitor, the surviving/not-evaluated path, REST
  `GET /research/thesis/active`, the WS `thesis` key, and `GET /research/journal/{id}` all carry
  identical frozen flags. Never recomputed at read, never a second computation/serving path.
- **Config research defaults** — `chase_return_threshold` (0.0040) and
  `invalidation_too_tight_spread_multiple` (2.0) in `app/config.py`, documented with their sim
  calibration. NOT added to the fingerprint exclusion set — they enter `config_fingerprint`
  automatically (by design).
- **Frontend** — amber risk-flag chips on the thesis strip (active + surviving/not-evaluated variants),
  rendering the taxonomy label + measured margin verbatim, numerics in mono. No flags fired ⇒ no chips
  and no "all clear" badge.

## Files Changed

- `apps/backend/app/config.py` — bumped `journal_schema_version` to 4 (with v3→v4 doc); added
  `chase_return_threshold` + `invalidation_too_tight_spread_multiple` research defaults (in fingerprint).
- `apps/backend/app/research/taxonomy.py` — `RISK_FLAGS` label catalog + per-flag evidence-template
  functions + `is_valid_risk_flag` / `risk_flag_label`; `risk_flags` added to `taxonomy_payload`.
- `apps/backend/app/research/monitor.py` — `compute_risk_flags` + `_expected_tape_states`; `build_projection`
  re-exposes the frozen `thesis.risk_flags` (omits the key when `None`); module docstring updated.
- `apps/backend/app/research/routes.py` — declaration route computes + freezes flags (after validation);
  `GET /research/journal/{id}` re-exposes the frozen flags (omits when NULL).
- `apps/backend/app/research/store.py` — `theses.risk_flags` column; v3→v4 idempotent migration step;
  `ThesisRecord.risk_flags` field; insert paths + `_row_to_thesis` read (NULL→None); `_encode_risk_flags`.
- `apps/backend/tests/fixtures/journal_v3_schema.sql` — NEW committed v3-schema fixture (actions has
  `spread_at_mark`, theses LACKS `risk_flags`; one pre-existing entry-marked thesis).
- `apps/backend/tests/test_journal_migration.py` — v3→v4 migration tests (column add, no backfill,
  pre-migration projection omits key, round-trip, idempotency, stale-version guard); the three v2→v3
  assertions that pinned `== 3` now assert `== CONFIG.journal_schema_version` (chained migration).
- `apps/backend/tests/test_research_risk_flags.py` — NEW: one positive + one negative case per flag,
  the `against_expected_tape` setup-aware matrix, direction-awareness, frozen-ness, and
  advisory-never-blocking.
- `apps/backend/tests/test_research_api.py` — updated the declare-projection assertion (`risk_flags`
  now present as `[]` on a clean declare); extended the REST==WS parity to `risk_flags`; added
  end-to-end flagged-declare, frozen-across-tape, journal-detail-carries-flags, 422-no-flags, and
  maximally-flagged-still-succeeds tests.
- `apps/frontend/lib/types.ts` — `RiskFlag` interface; `risk_flags?` on `ThesisProjection`;
  `risk_flags?` on `ResearchTaxonomy`.
- `apps/frontend/components/ThesisStrip.tsx` — `RiskFlagChips` component; rendered on both the active
  and the surviving/not-evaluated strips.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: 469 passed, 1 skipped (the skip is the pre-existing credentialed live-integration test,
`test_live_integration.py`, `skipif` no Alpaca keys — unrelated to this iteration).

Frontend: `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build` → Compiled successfully, types
valid (the `.next-qa` dist was removed after; the dev server's shared `.next` was never touched).

New/changed test highlights (all green):
- `test_research_risk_flags.py` — 18 tests; each flag's exact measured-evidence payload pinned.
- `test_journal_migration.py` — v3→v4 add + no-backfill + projection-omits-key + round-trip + idempotency.
- `test_research_api.py::test_rest_active_equals_ws_thesis_key_verbatim` — `risk_flags` byte-identical REST≡WS.
- `test_observer_equivalence.py` — still green (research layer remains read-only over the engine).

## Pre-handoff verification

- **Service startup**: started `scripts/start-backend.sh` (uvicorn on :8650) and
  `scripts/start-frontend.sh` (next dev on :3650) — both started without errors; `GET /` → 200; both
  processes killed afterward (ports 8650/3650 confirmed free).
- **Live content canary**: watched SIM-BUYER on the running backend, let the move extend past warm-up,
  declared trend_continuation/long via REST → response carried
  `risk_flags: [{flag: "chasing_entry", label: "Chasing an extended move", evidence: "recent buy
  impact +0.44% already exceeds the +0.40% chase threshold — the move has run before this entry",
  measured: {impact_return: 0.0044, threshold: 0.004, side: "buy"}}]`. `GET /research/thesis/active`
  returned the same frozen flag; `GET /research/taxonomy` listed all six flag ids.
- **Live migration**: the running backend opened the existing `tapeology_journal.db` and migrated it
  in-place to schema v4 (`theses.risk_flags` present; the 22 pre-existing theses kept NULL flags — never
  backfilled; the one new declaration carried frozen flags).

## Known Issues

- None for this iteration's scope. `chasing_entry` is calibrated tight by design: SIM-BUYER's favorable
  buy-impact return is ~0.0033 right at warm-up (below the 0.0040 threshold → a clean no-chase declare)
  and climbs to ~0.0043–0.0048 a few seconds later (an extended move → fires). For the browser
  `chasing_entry` leg, watch SIM-BUYER a few seconds PAST warm-up before declaring; for the clean
  no-flags frame, declare at/near warm-up with a normal (~$1-away) invalidation.
- `wide_spread_illiquid` honestly does NOT fire on a warm SIM-CHOP declare: SIM-CHOP's spread (~14 bps)
  is under the classifier's 30-bps stable cap (the chop is `unclear` because of mixed 0.50/0.50 ratios,
  not a wide spread). The browser liquidity leg fires `low_trade_speed` instead by declaring promptly on
  a freshly-watched SIM-CHOP (early speed < 0.5/s) — the spec's "and/or" covers this. This is the honest
  reading of the verbatim classifier gates (no new threshold invented).
- The FULL-pipeline harness defect (engine halts at `qa_complete`) remains open upstream — depth is lean
  per the evaluator recommendation; this iteration produced complete evaluator-verifiable evidence.
