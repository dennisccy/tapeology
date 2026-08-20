# goal-rapid-microscope-iter-19 Execution Plan

## What to Build
- New backend test module `apps/backend/tests/test_micro_deterministic_rerun.py` proving J-10's
  last acceptance gap: over an UNCHANGED fixture dataset/store, each of the three era
  computations — snapshot build (`micro_snapshots.build_snapshot_rows` /
  `run_snapshot_build_and_record`), Scout screen (`scout.screen_candidate` /
  `register_and_screen_candidate`), walk-forward fold (`walkforward.register_mode_a_origin` +
  `evaluate_mode_b_fold`) — produces byte-identical output when re-run twice, excluding only
  legitimately-new-per-run fields (ledger row id/position, `registered_at`/timestamp, `run_id`,
  `sequence_id`). TC-1..TC-3.
- Mutation-proof (TC-4) for the new determinism assertions themselves: deliberately perturb one
  field of a scratch second-run result, prove the assertion raises, then confirm the real
  unperturbed rerun passes. Document perturbed fields in the module's own docstring, matching
  `test_micro_sealed_evaluation.py`'s existing mutation-proof precedent (see its TC-8 comment
  block, `apps/backend/tests/test_micro_sealed_evaluation.py:24-28`).
- Deepen four "cannot-fail" golden replay scripts under
  `runs/goal-session-rapid-microscope/journey-scripts/` — J-02.json, J-03.json, J-04.json,
  J-05.json — each currently asserting an unrelated pre-existing Desk heading on step 1 alone.
  Add the shared step-1 pattern (`goto /desk` → expect `"Playbook Signals"`, already used by
  J-01/J-08/J-10) plus a NEW step 2 that expands the journey's own already-registered section and
  asserts a real already-registered field (TC-5..TC-8, exact strings below).
- Extend `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` IN PLACE (never a new
  file) to write a durable manifest recording the resolved `TAPEOLOGY_DATASET_DIR` and sibling
  store-root env vars plus a launch timestamp, OR rely on/cite the script's own existing
  `echo … >&2` lines (already present, confirmed) — developer's call per TC-9's own "if judged
  redundant" clause.
- This iteration's own generated QA/quality report must cite that manifest (or the launcher's
  stderr line) for any claim about which data store the browser/replay lane used — never assert
  "real data store" for a fixture-scoped launcher pass. This is a reporting requirement, not a
  code change; flag it explicitly to the qa/reviewer/auditor agents.
- Full 8-journey golden replay set (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-10) must execute
  and report individually this round — mandatory because the diff touches the shared QA launcher
  script and four of the golden scripts themselves (iter-18's standing lesson, TC-10).
- `state/blueprint.md` already carries its iter-19 documentation note (pre-written by the
  decomposer, verified present at the file's tail) — no further edit needed there.

## Out of Scope (do not touch)
- `micro_sealed_evaluation.py`'s `econ_floor` handling / TR-30 condition-1 logic /
  `SEALED_MIN_OBSERVATIONS` / the TR-1…TR-30 trap suite (already 30/30, "Do not redo").
- J-09 "the pilot studies" and the sealed judge's economic-floor/evidence-label ownership fix
  (iter-18 item 1) — both blocked on an owner ruling not yet landed in
  `docs/rapid-validation-spec.md` (confirmed no revision after r9).
- J-06 step 4 (real Alpaca tranche recording) — operator-owned.
- `J-08.json` / `J-10.json`'s already-refreshed Validation Vault assertions (`iter18-qa-universe`)
  — "Do not redo."
- Any `.tsx` file change — zero product behavior change this iteration; the four golden scripts
  click ALREADY-shipped controls and assert ALREADY-served text.
- `vault.py`, `tick_recorder.py`, any frozen/Referee module.

## Agents Required
- backend-data: yes — new determinism test module + mutation-proof; QA launcher script extension.
- frontend-ux: no — zero `.tsx` changes; the "frontend" work this round is entirely golden JSON
  replay-script edits (test/harness artifacts), not product UI.

## Frontend Present: yes

(Set per the phase spec's explicit Goal Mode Metadata: no `.tsx` changes ship, but the
Definition of Done names `browser-qa-agent` for J-10's kept-product sentinel and the 8-journey
golden-replay lane — `Frontend Present: no` would silently skip both lanes, exactly the iter-18
process gap this iteration exists partly to avoid repeating.)

## Files to Create/Modify
- `apps/backend/tests/test_micro_deterministic_rerun.py` (new) — TC-1..TC-4: snapshot/scout/fold
  rerun byte-identity + mutation-proof, reusing existing fixture patterns already present in
  `test_micro_snapshots.py` (e.g. its `build_snapshot_rows`/`run_snapshot_build_and_record`
  fixtures), `test_scout.py` (`snapshot_ready_store` fixture, `screen_candidate` /
  `register_and_screen_candidate` calls), and `test_walkforward.py`
  (`register_mode_a_origin` + `evaluate_mode_b_fold` fixtures, e.g. near
  `test_tc13_a_mode_b_spec_registered_before_any_exposure_of_its_window_classes_historical_oos`).
- `runs/goal-session-rapid-microscope/journey-scripts/J-02.json` — add step 2: click
  `desk-section-expand-microReadiness`, expect literal text `"Fallback frac"` (column header,
  `apps/frontend/app/desk/page.tsx:6071`; served by `micro_readiness.py`,
  `GET /research/desk/micro/readiness`). Fix step 1 to the shared `goto /desk` →
  `"Playbook Signals"` pattern.
- `runs/goal-session-rapid-microscope/journey-scripts/J-03.json` — add step 2: click
  `desk-section-expand-microReadiness`, expect literal text
  `"Joinable corpus — withheld (excluded)"` (`apps/frontend/app/desk/page.tsx:6006`; served by
  `micro_readiness.py`/`micro_join.py`, same endpoint). Fix step 1 to the shared pattern.
- `runs/goal-session-rapid-microscope/journey-scripts/J-04.json` — add step 2: click
  `desk-section-expand-scoutLedger`, expect literal text `"Ledger chain verification:"`
  (`apps/frontend/app/desk/page.tsx:6268`; served by `scout_ledger.py`/`scout.py`,
  `GET /research/desk/micro/scout`). Fix step 1 to the shared pattern.
- `runs/goal-session-rapid-microscope/journey-scripts/J-05.json` — step 1 already matches the
  shared pattern (`goto /desk` → `"Playbook Signals"`) — no change needed there. Add step 2:
  click `desk-section-expand-walkForward`, expect literal text `"Ledger chain verification:"`
  (`apps/frontend/app/desk/page.tsx:6495`; served by `walkforward.py`+its ledger,
  `GET /research/desk/micro/walkforward`).
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extend in place: write a
  durable manifest under `reports/` (e.g. `reports/qa-scoped-backend-store-manifest.md`) with the
  resolved `TAPEOLOGY_DATASET_DIR` + sibling store-root vars + launch timestamp, OR document that
  the script's existing `echo … >&2` lines (already confirmed present, printing every
  `TAPEOLOGY_*` var including `TAPEOLOGY_DATASET_DIR`) satisfy TC-9 and cite those instead.
- `docs/handoffs/goal-rapid-microscope-iter-19-dev.md` (new) — dev handoff.

## UI Evolution
N/A — zero user-visible change. `Frontend Present: yes` exists solely to keep the browser-qa and
replay lanes running per the phase spec's explicit instruction (see above). No new capability,
information, action, surface, or navigation change ships this iteration.

## Visual Requirements
N/A — no UI change. The browser-qa-agent's job this round is verification only: confirm the
kept-product sentinel (`/`, `/structure`, every shipped `/desk` section including the three
Referee sections) still renders as shipped, and confirm the four deepened golden scripts'
newly-asserted strings genuinely render when their sections expand (not merely assumed present).

## Key Test Scenarios
- TC-1: `build_snapshot_rows`/`run_snapshot_build_and_record` invoked twice over an unchanged
  fixture dataset → second run's snapshot rows + identity fields (dataset_checksum,
  MICRO_ALGO_VERSION, SNAPSHOT_FORMAT_VERSION, feature_source_hash, config_fingerprint,
  params_hash) byte-identical (canonical-JSON-equal) to the first.
- TC-2: same registered candidate spec screened twice via `screen_candidate` /
  `register_and_screen_candidate` over an unchanged fixture corpus → `screen_result` payload
  byte-identical between runs, while the ledger records two independent trial rows (never
  overwritten/deduplicated).
- TC-3: same fold spec evaluated twice over an unchanged fixture corpus → every fold index's
  `fold_results` fields (effect, n, n_sessions, sign, evidence_class, process_label)
  byte-identical between runs, while the ledger records a new independent `sequence_id`.
- TC-4: deliberately perturb one field of a scratch second-run result before comparison →
  assertion FAILS; revert the perturbation → the real rerun's assertion PASSES. Non-negotiable
  per iter-15/16's lesson (equality-check-between-two-runs is the classic
  "structurally-unable-to-fail" trap shape).
- TC-5: J-02.json replay, Microscope Readiness expanded → page displays `"Fallback frac"`.
- TC-6: J-03.json replay, same section expanded → page displays
  `"Joinable corpus — withheld (excluded)"`.
- TC-7: J-04.json replay, Scout Ledger expanded → page displays `"Ledger chain verification:"`
  sourced from `GET /research/desk/micro/scout`'s `chain_verification` field.
- TC-8: J-05.json replay, Walk-Forward expanded → page displays `"Ledger chain verification:"`
  sourced from `GET /research/desk/micro/walkforward`'s `chain_verification` field.
- TC-9: fixture-scoped QA launcher startup → a durable record (manifest file or the launcher's
  own stderr line) captures the exact resolved `TAPEOLOGY_DATASET_DIR` + sibling store-root vars
  the running server is bound to.
- TC-10: full 8-journey golden replay set (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-10)
  executes and reports individually — never a subset — because this round's diff touches the
  shared launcher and four golden scripts (J-07 has no golden script by design; its LLM lane
  covers it, per standing precedent).
- TC-11: full backend suite exits 0 with collected/passed count ≥ the iteration-18 baseline
  (3,271 collected / 3,263 passed / 8 skipped / 0 failures / 0 errors), 0 regressions.
- Sentinel checks (already-standing, re-verify not re-build): `Config().config_fingerprint()` →
  `08e471b10130e1e2`; the six `referee_*` module SHA-256 listing unchanged from the iteration-0
  baseline.
- Browser: J-10 fresh (kept-product sentinel — `/`, `/structure`, every shipped `/desk` section
  including the three Referee sections); J-01–J-08 via the full golden-replay set (J-07 via its
  designated LLM lane, no golden script by design).
