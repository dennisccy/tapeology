# goal-hypothesis-foundry-iter-8 Execution Plan

## Context (verified against current code, not assumed)

- Session `hypothesis-foundry`, closing iteration (J-08 of 8). Prior verdict `ESCALATE` forces
  `Depth: full` per binding rule; J-01–J-07 all currently passing.
- `docs/goal.md` J-08 (lines 1168-1188) matches this spec's IN SCOPE/DoD exactly — no drift found.
- `read_epoch_manifest_view()` (`apps/backend/app/research/micro_routes.py:806-880`) already checks
  `source_registry_path.is_file()` as one of three required tracked files but **never parses its
  content** — it only reads `epoch-manifest.json` + `freeze-record.json`. This is the exact gap the
  spec targets.
- The real committed `docs/hypothesis-foundry/source-registry.json` (`{"records": [...]}`, 11
  records) already stores each record as a **fully serialized dict** — `quoted_spans`,
  `source_hash`, `mechanism_statement`, `operative_formula_refs`, `direction_derivation`,
  `comparator_derivation`, `threshold_provenance`, `superseded_fields`, `alternatives`,
  `audit_note`, `lineage_id` are all present per-record, verified directly (pilot-study-1 record
  read in full). This is plain JSON — no `SourceRecord` reconstruction needed, just `json.loads` +
  key lookup by `source_id`.
- The real committed `docs/hypothesis-foundry/epoch-manifest.json`'s `source_dispositions[]`
  entries currently carry only `source_id` / `disposition` / `lineage_refs` / `alias_refs` (verified
  directly — 11 entries, e.g. `pilot-study-1-range-wall-failed-aggression` /
  `ALIASED_PROXY_ONLY`).
- `compute_frozen_ready_total()` (`micro_routes.py:901-920`) is the existing sole-owner helper for
  `frozen_ready_total` — reuse verbatim, do not touch.
- `read_exhaust_progress()` (`apps/backend/app/research/foundry_runner.py:229-283`) has two return
  branches (no epoch-open row → line 258-269; real branch → line 272-283); both need the new field.
  **Field-name correction to the spec text**: ledger terminal rows do NOT have an `outcome` key —
  `foundry_ledger.py`'s `record_terminal()` (line 203-234) writes `foundry_state`, and
  `_SCOUT_OUTCOME_TO_FOUNDRY_STATE` (`foundry_runner.py:52`) maps Scout's `"survive"` outcome to the
  literal string `"DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"`. The new count must filter
  `row["row_kind"] == fl.ROW_KIND_TERMINAL and row["foundry_state"] ==
  "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"`, matching the existing `terminal_count` computation
  pattern at line 271. Today this is `0` for both branches on the real (empty) epoch.
- `/desk` Foundry panel render order in `apps/frontend/app/desk/page.tsx`: `foundry-era-open-baseline`
  div closes at line 8097; the six-subsection block (`Sources/Compiler` → `Interpreter Fixtures` →
  `Freeze/Integrity` → `Hermetic Oracles` → `Epoch/Manifest` → `Runner/Checkpoint`) starts at line
  8099 (`<div className="mt-4 space-y-3">`) and ends at line 8160. **The new Final Summary block
  must be inserted between line 8097 and line 8099** to satisfy "below era-identity header, above
  the six existing subsections."
- `fetchDeskFoundry()` lives in `apps/frontend/lib/api.ts:2799`; response types in
  `apps/frontend/lib/types.ts:3132-3205` (`FoundrySourceDisposition` at 3132,
  `FoundryExhaustProgress` at 3172, `DeskFoundryResponse` at 3187).
- TC-6's exact required test name (`test_desk_page_price_arithmetic_guard_catches_foundry_field_
  arithmetic`) matches the established per-feature naming convention already used by ~15 sibling
  tests in `apps/backend/tests/test_desk_ui_guards.py` (e.g.
  `..._catches_playbook_field_arithmetic` at line 499) — follow that exact pattern.
- TC-10's target docstring already exists at
  `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py:166-201`
  (`test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper`). It already avoids
  the strongest overclaim but does **not** yet state that freeze-set hash pinning (not the
  assertion) is what prevents divergence — that sentence is the actual missing correction (per the
  iter-7 AUDITOR NOTE's measured-divergence table showing the two formulas are NOT equivalent in
  general; only pinning both frozen files makes drift impossible). No assertion logic changes.
- 59 freeze-set-sealed files (verified byte-identical every iteration since iter-6) must stay
  untouched. None of this iteration's files (`micro_routes.py`, `foundry_source_registry.py`,
  `foundry_runner.py`, `apps/frontend/app/desk/page.tsx`, `lib/api.ts`, `lib/types.ts`, the two test
  files) are in that sealed set.
- Backend suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (3930 tests / 8 skipped
  baseline per iter-7). Frontend TS compile: `cd apps/frontend && npx tsc --noEmit` (project
  convention; no separate `test` script exists in `package.json`). Dev services:
  `scripts/dev.sh` (backend `:8301`, frontend `:3301` per iter-6/7 handoffs).
- Two HUMAN-owned open anti-goal entries ("No second real generation epoch"; "Persistence stays
  scoped" lock-file write in the sealed `foundry_runner.py::SingleFlightLock.acquire()`) are
  explicitly OUT OF SCOPE — do not attempt either.

## What to Build

- Backend: extend `read_epoch_manifest_view()` to also read `source-registry.json` content
  (currently only checked for existence) and enrich each `source_dispositions[]` entry with the
  full §1.4 provenance fields, looked up by `source_id` from the registry records — read verbatim,
  zero recompute, zero second compile pass, zero use of `resolve_foundry_dir()`.
- Backend: add `exhaust_progress.diagnostic_survivor_count` to `read_exhaust_progress()` — a real
  filter over ledger terminal rows on `foundry_state == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"`
  (both the no-epoch-open and real branches), not a copy of `terminal_count`.
- Backend: add a new pure-projection helper (e.g. `compute_foundry_final_summary(...)`) in
  `micro_routes.py`, called once at module import time from `_EPOCH_MANIFEST_VIEW` +
  `_FOUNDRY_FROZEN_READY_TOTAL` + the per-request `exhaust_progress` result, producing the new
  `final_summary` top-level key on `GET /research/desk/micro/foundry`. Every value must be a
  projection of an already-canonically-owned field (reuse `compute_frozen_ready_total`'s result
  verbatim; do not re-sum families independently).
- Backend: correct the docstring on
  `test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper` in
  `test_run_hypothesis_foundry_real_exhaust.py` to state plainly that freeze-set hash pinning — not
  the equivalence assertion — prevents silent divergence (no assertion-logic change).
- Frontend: new `FinalSummarySubsection` component + `<div data-testid="foundry-final-summary">`
  block inserted between the era-open-baseline block and the six-subsection block in
  `apps/frontend/app/desk/page.tsx`, rendering `final_summary`'s seven fields verbatim (source
  counts by disposition, family/variant counts, `diagnostic_survivor_count` with explicit
  zero-survivor text when `0`, `freeze_integrity_verdict`, evidence class, `protected_read_count`,
  `exhaust_complete`) plus a per-source `<details>` drill-in (same convention as existing Foundry
  `<details>` uses, e.g. line 7495/7560/7649) showing each real source's `mechanism_statement`,
  `audit_note`, `direction_derivation`, `comparator_derivation`, `threshold_provenance`,
  `superseded_fields`, `alternatives`, and every `quoted_spans[].text`/`.location`. Reuses the
  already-fetched `foundry` payload from `fetchDeskFoundry()` — no new fetch, no new
  `useEffect`/`setTimeout`/`setInterval`.
- Frontend types: extend `FoundrySourceDisposition` (types.ts:3132) with the new provenance fields;
  add `diagnostic_survivor_count: number` to `FoundryExhaustProgress` (types.ts:3172); add a new
  `FoundryFinalSummary` interface and `final_summary: FoundryFinalSummary` on `DeskFoundryResponse`
  (types.ts:3187).
- Tests: unit test(s) proving `read_exhaust_progress()`'s new field and the new `final_summary`
  helper each *read* rather than *recompute* underlying values (assert against
  `compute_frozen_ready_total`'s actual return object identity/value, not a re-derivation); a test
  asserting the extended `source_dispositions[]` provenance fields against the real committed
  `source-registry.json` content; the new
  `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` case in
  `test_desk_ui_guards.py`; error-case tests for `not_yet_generated`/missing-optional-field
  (`threshold_provenance: null`) honest degrade.
- Dev handoff at `docs/handoffs/goal-hypothesis-foundry-iter-8-dev.md`.

## Agents Required

- backend-data: yes — all of the above backend changes (micro_routes.py, foundry_runner.py, the two
  test files) are the majority of the DoD surface.
- frontend-ux: yes — new Final Summary subsection + drill-in in `apps/frontend/app/desk/page.tsx`,
  plus type additions in `lib/types.ts`.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/micro_routes.py` — parse `source-registry.json` inside
  `read_epoch_manifest_view()`, enrich `source_dispositions[]`; add `compute_foundry_final_summary()`
  and the new `final_summary` key on the `GET /foundry` response.
- `apps/backend/app/research/foundry_runner.py` — add `diagnostic_survivor_count` to both branches
  of `read_exhaust_progress()`.
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` — docstring-only correction on
  the existing equivalence-pinning test (TC-10); no assertion change.
- `apps/backend/tests/test_desk_ui_guards.py` — add
  `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` (TC-6).
- New/extended unit tests near `foundry_source_registry.py`/`foundry_runner.py`/`micro_routes.py`
  coverage (existing test file names, e.g. `test_foundry_route.py`,
  `test_run_hypothesis_foundry_real_exhaust.py`, or a project-appropriate existing Foundry test
  module — follow existing file organization, do not invent a new top-level test file unless none
  fits) for the new provenance fields, `diagnostic_survivor_count`, and `final_summary` projection.
- `apps/frontend/app/desk/page.tsx` — new `FinalSummarySubsection` component + insertion point
  (between lines 8097 and 8099 in the current file).
- `apps/frontend/lib/types.ts` — extend `FoundrySourceDisposition`, `FoundryExhaustProgress`; add
  `FoundryFinalSummary`; extend `DeskFoundryResponse`.
- `docs/handoffs/goal-hypothesis-foundry-iter-8-dev.md` — dev handoff (required by DoD).

## UI Evolution

- New user-facing capability: one top-level "final truth" synthesis of the whole real epoch,
  visible without expanding any of the six existing subsections, plus provenance drill-in for any
  individual real source.
- New information displayed: source counts by disposition, family/variant counts,
  `diagnostic_survivor_count` (with explicit honest zero-survivor statement when 0),
  `freeze_integrity_verdict`, evidence class (`historical_exposed_diagnostic`),
  `protected_read_count`, `exhaust_complete`; per-source full §1.4 provenance on expand.
- New user actions: expand/collapse a source's detail `<details>` disclosure inside the new Final
  Summary subsection.
- UI surface changes: one new subsection (`foundry-final-summary`) inside the already-shipped
  `/desk` → Hypothesis Foundry panel. No new page, no new nav entry.
- Navigation changes: none.

## Visual Requirements

- Component patterns: match the existing Foundry subsection conventions exactly — the same
  `data-testid` discipline, the same monospace/slate-muted numeric styling used by
  `EpochManifestSubsection`/`RunnerCheckpointSubsection`, and the same `<details>` per-item
  disclosure pattern already used at page.tsx lines 7495/7560/7649 for source-list drill-ins.
- Layout: inserted as a plain block (or `CollapsibleSection`, matching sibling subsections) directly
  under the `foundry-era-open-baseline` div, above the `mt-4 space-y-3` six-subsection container —
  do not nest it inside that container.
- Key visual effects: none new — reuse existing Foundry-panel styling (slate/emerald palette,
  existing `EmptyState`/`RealEpochBanner`/`HermeticFixtureBanner` helpers as applicable) rather than
  introducing new visual treatments.
- States to handle: honest degrade when `epoch_manifest.status` is `not_yet_generated`/
  `generated_uncommitted` (no fabricated counts); a source record missing an optional field (e.g.
  `threshold_provenance: null`) renders as explicit absence text, never blank.

## Key Test Scenarios

- TC-1: `GET /research/desk/micro/foundry` against the real committed epoch returns `final_summary`
  with disposition counts summing to 11, `family_count == 0`, `variant_count == 0`,
  `frozen_ready_total == 0`, `diagnostic_survivor_count == 0`, `freeze_integrity_verdict == "green"`,
  `protected_read_count == 0`, `exhaust_complete == true`.
- TC-2: `/desk` renders `data-testid="foundry-final-summary"` with those seven values, positioned
  below era-identity header and above the six existing subsections.
- TC-3: expanding the `pilot-study-1-range-wall-failed-aggression` (`ALIASED_PROXY_ONLY`) detail
  `<details>` shows its `mechanism_statement`, `audit_note`, `direction_derivation`,
  `comparator_derivation`, and at least one `quoted_spans[].text`/`.location`, verbatim.
- TC-4: zero-survivor epoch renders an explicit textual zero-survivor statement, not a bare `0`.
- TC-5: served JSON and rendered DOM values match byte-for-byte for every `final_summary`/detail
  field (captured in the same browser-qa pass).
- TC-6: `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` passes normally and
  fails when a seeded client-side-arithmetic violation (e.g. `final_summary.family_count - 1`) is
  injected.
- TC-7: page effect/timer census (`test_table_sort_guards.py` / `test_desk_ui_guards.py`) unchanged.
- TC-8: `test_vault.py` TR-2 sweep still passes with the new fields present on the route.
- TC-9: `test_copy_discipline.py` frontend-literal lint reports zero banned-phrase matches over the
  new JSX.
- TC-10: the equivalence-pinning test's docstring states freeze-set hash pinning (not the assertion)
  prevents divergence; assertion logic and the sealed CLI file are byte-unchanged.
- TC-11: full backend suite + `tsc --noEmit` both pass with zero new failures/errors.
- TC-12: J-01–J-07 all still pass via deterministic replay (LLM fallback if a journey lacks a stored
  golden).
- Browser QA note (per spec NOTES/TESTING REQUIREMENTS): capture every Foundry subsection screenshot
  via `demo_runner --mode verify`, never Chrome-MCP deep-scroll (has returned blank PNGs twice this
  session); ensure the scoped QA rig can see the real committed `docs/hypothesis-foundry/` artifacts
  (`cp`-into-rig-root pattern from iter-1/iter-2) before the pass, or real-epoch checks will
  honestly-but-wrongly degrade to "not recorded yet."

## Out of Scope (do not build)

- Optional read-only MCP proxy (`desk_micro_foundry`) — deferrable per goal.md, non-blocking.
- Either HUMAN-owned open anti-goal entry (second-epoch ratification; page-load-GET lock-file write
  inside sealed `foundry_runner.py`) — both require an owner ruling and/or a sealed-file edit this
  iteration must not make.
- Any edit to any of the 59 freeze-set-sealed files.
- A second real generation epoch or any change to `source-registry.json`/`epoch-manifest.json`/
  `freeze-set.json`/`freeze-record.json` content, or re-running the exhaust CLI.
- Rebuilding/re-verifying the internals of the six already-shipped subsections beyond confirming
  continued regression-passing status.
- Any new top-level page or nav entry.
