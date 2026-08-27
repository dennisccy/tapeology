# goal-hypothesis-foundry-iter-8 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

J-08 ("the operator sees the final Foundry truth"): a new top-level "Final Summary" synthesis of
the real Hypothesis Foundry epoch's complete state, plus a per-source canonical-provenance
drill-in, all served through the existing `GET /research/desk/micro/foundry` route and rendered on
`/desk`.

- Extended `read_epoch_manifest_view()` (`micro_routes.py`) to also parse the tracked
  `docs/hypothesis-foundry/source-registry.json` (previously only `.is_file()`-checked, never
  read) and enrich each `epoch_manifest.source_dispositions[]` entry with the matching real
  source-registry record's full §1.4 provenance: `quoted_spans`, `source_hash`,
  `mechanism_statement`, `operative_formula_refs`, `direction_derivation`,
  `comparator_derivation`, `threshold_provenance`, `superseded_fields`, `alternatives`,
  `audit_note`, `lineage_id`. New helper `_enrich_source_dispositions_with_registry_provenance`
  degrades honestly (explicit `None`/`[]`/`{}`) if a manifest entry has no matching registry
  record.
- Added a new pure-projection helper `compute_foundry_final_summary()` in `micro_routes.py` and
  wired it as a new top-level `final_summary` key on `GET /research/desk/micro/foundry`. Every
  field is a projection of an already-canonically-owned value: `family_count`/
  `source_counts_by_disposition` from the epoch manifest view; `variant_count`/
  `frozen_ready_total` copied verbatim from `compute_frozen_ready_total`'s already-computed
  result (never re-summed); `diagnostic_survivor_count`/`freeze_integrity_verdict`/
  `protected_read_count`/`exhaust_complete` copied verbatim from the per-request
  `exhaust_progress` read; `evidence_class` is the one constant `"historical_exposed_diagnostic"`
  label.
- Added `exhaust_progress.diagnostic_survivor_count` — a genuine filter of the real Foundry trial
  ledger's terminal rows whose `foundry_state == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"`.
- Frontend: new `FinalSummarySubsection` component + `data-testid="foundry-final-summary"` block,
  inserted as its own `CollapsibleSection` ("Final Summary") between the existing era-open-baseline
  block and the six existing Foundry subsections on `/desk`. Renders the seven `final_summary`
  fields verbatim, an explicit zero-survivor statement when `diagnostic_survivor_count === 0`, and
  a per-source `<details>` drill-in showing each real source's full §1.4 provenance
  (mechanism/audit note/direction/comparator/threshold/superseded fields/alternatives/quoted
  spans). Reuses the already-fetched `fetchDeskFoundry()` payload — no new fetch, no new
  `useEffect`/`setTimeout`/`setInterval`.
- Extended `test_desk_ui_guards.py`'s numeric-field anti-recomputation regex with the new
  `data.family_count`/`variant_count`/`frozen_ready_total`/`diagnostic_survivor_count`/
  `protected_read_count` field group, plus the required
  `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` counter-test.
- Corrected the docstring on
  `test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper` in
  `test_run_hypothesis_foundry_real_exhaust.py` per the iter-7 finding: it now states plainly that
  the freeze-set hash pinning (not the equivalence assertion itself) is what prevents the sealed
  CLI formula and the canonical helper from silently diverging. No assertion-logic change.
- Fixed a pre-existing test (`test_foundry_real_epoch_artifacts.py::
  test_tc6_outcome_access_census_is_zero_in_the_artifact_and_on_the_served_view`) that asserted
  the served `source_dispositions[]` equals the raw tracked manifest byte-for-byte — that
  equality no longer holds now that the served view is additively enriched. Rewrote it to assert
  every base manifest field still passes through verbatim, field-by-field, plus the presence of
  the new provenance enrichment.

### Critical deviation from the plan, and why

The phase spec's IN SCOPE list and `plan.md` both instructed `diagnostic_survivor_count` to be
added inside `foundry_runner.py`'s `read_exhaust_progress()`. Direct inspection of
`docs/hypothesis-foundry/freeze-set.json` showed this claim was **wrong**: `foundry_runner.py`
(and `foundry_ledger.py`, `foundry_source_registry.py`, `foundry_compiler.py`,
`foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`) are all among the 59
freeze-set-sealed files, sealed since this era's first-read lock. I confirmed this the hard way:
an initial edit to `foundry_runner.py` immediately tripped `verify_freeze_set_unchanged` and
failed five real-epoch tests in `test_run_hypothesis_foundry_real_exhaust.py` with
`FreezeIntegrityHalt`. Per the dispatch's own CRITICAL CONSTRAINT ("do not edit any of [the 59
sealed files]"), I reverted `foundry_runner.py` to byte-identical and instead added
`diagnostic_survivor_count` in `micro_routes.py` (never sealed): a new
`_compute_diagnostic_survivor_count()` helper reads the SAME Foundry trial ledger directly
(`FoundryLedger`/`ROW_KIND_TERMINAL`, filtered on `foundry_runner.SCOUT_TO_FOUNDRY_STATE["survive"]`
— reusing the existing constant, not a new literal) and `get_foundry()` merges this one additive
field onto `read_exhaust_progress()`'s own unchanged, byte-identical return value. The observable
REST/UI contract (`exhaust_progress.diagnostic_survivor_count`) is unaffected — only its ownership
module moved to the one legally-editable location. My source-registry provenance enrichment work
was never at risk: it was always entirely inside `micro_routes.py`, per the spec's own explicit
instruction to read `source-registry.json` directly and never through `resolve_foundry_dir()`.

Verified after the fix: `git status` shows zero freeze-set-sealed files touched (only
`micro_routes.py`, four test files, and the two frontend files changed); the full backend suite is
green; the real, live `/research/desk/micro/foundry` endpoint (unscoped, hitting the actual
`apps/backend/.data/foundry/foundry_trial_ledger.jsonl` this dev environment already had from a
prior iteration's real exhaust CLI run) returns `final_summary.freeze_integrity_verdict == "green"`
and `exhaust_complete == true`, exactly matching TC-1.

## Files Changed

- `apps/backend/app/research/micro_routes.py` — `read_epoch_manifest_view()` now parses
  `source-registry.json` and enriches `source_dispositions[]`; new
  `_enrich_source_dispositions_with_registry_provenance()`,
  `_compute_diagnostic_survivor_count()`, `compute_foundry_final_summary()`; `get_foundry()` now
  serves `final_summary` and merges `diagnostic_survivor_count` onto `exhaust_progress`.
- `apps/backend/tests/test_foundry_route.py` — 7 new tests: real-registry provenance agreement,
  honest-absence degrade, `diagnostic_survivor_count` zero-before-run + genuine-filter proof,
  `final_summary` TC-1 values against an isolated real-manifest+fresh-epoch-open scenario,
  `final_summary`'s no-second-counting-site proof, and `not_yet_generated` honest degrade.
- `apps/backend/tests/test_desk_ui_guards.py` — new `data.*` Foundry final-summary field group in
  the arithmetic-anti-recomputation regex + `test_desk_page_price_arithmetic_guard_catches_
  foundry_field_arithmetic` (TC-6).
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` — docstring-only correction
  (TC-10); no assertion or sealed-file change.
- `apps/backend/tests/test_foundry_real_epoch_artifacts.py` — updated one pre-existing assertion
  that the source-dispositions enrichment made stale (see deviation note above); no weakening —
  it now checks MORE (base-field fidelity plus enrichment presence) than the original bare
  equality.
- `apps/frontend/app/desk/page.tsx` — new `FinalSummarySubsection` component + insertion point;
  new `FoundryFinalSummary`/`FoundrySourceDisposition` imports.
- `apps/frontend/lib/types.ts` — new `FoundryQuotedSpan`, extended `FoundrySourceDisposition`,
  extended `FoundryExhaustProgress` (`diagnostic_survivor_count`), new `FoundryFinalSummary`,
  extended `DeskFoundryResponse`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 3930 passed, 8 skipped, 0 failed.

Command: `cd apps/frontend && npx tsc --noEmit`
Result: 0 errors.

Live verification (backend `:8301`, frontend `:3301`, both started via `scripts/dev.sh` and left
running for the QA lanes per the dispatch's operational note):
- `curl http://localhost:8301/research/desk/micro/foundry` — `final_summary` present with exactly
  TC-1's values (11 sources summing correctly across 7 dispositions, `family_count`/`variant_count`/
  `frozen_ready_total`/`diagnostic_survivor_count` all `0`, `freeze_integrity_verdict: "green"`,
  `evidence_class: "historical_exposed_diagnostic"`, `protected_read_count: 0`,
  `exhaust_complete: true`, `epoch_status: "committed"`).
- Chrome (CDP `:9222`) against `/desk`: expanded the Hypothesis Foundry panel, then the new "Final
  Summary" `CollapsibleSection` (positioned above the six existing subsections, confirmed via DOM
  query order) — every rendered field matched the served JSON byte-for-byte (TC-5). Expanded
  `pilot-study-1-range-wall-failed-aggression`'s detail `<details>` — `mechanism_statement`,
  `audit_note`, `direction_derivation`, `comparator_derivation`, `quoted_spans` all rendered
  verbatim (TC-3). Zero-survivor statement rendered as explicit text, not a bare `0` (TC-4). No
  console errors.

## Known Issues

- No live browser-automation pass was run for the J-01–J-07 regression set or for
  `demo_runner --mode verify`'s screenshot capture — that is QA's job per the pipeline; this dev
  pass verified the new J-08 surface directly (REST + DOM) and confirmed zero backend/TS
  regressions, but did not re-drive the other six journeys' browser flows.
- The optional read-only MCP proxy (`desk_micro_foundry`) remains unbuilt, as explicitly
  out-of-scope/deferrable per the spec and `docs/goal.md`.
- The two HUMAN-owned open anti-goal entries ("No second real generation epoch" ratification;
  "Persistence stays scoped" lock-file write inside the sealed `foundry_runner.py`) remain
  unresolved, as explicitly out of scope for this iteration.
