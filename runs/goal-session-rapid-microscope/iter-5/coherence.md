# Iteration 5 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-5
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Corpus readiness truth + joinable-corpus counts (owner: `micro_readiness.py`/`micro_join.py`, endpoint: `GET /research/desk/micro/readiness`) | OK — only the internal snapshot-row read path changed (re-pointed through the new accessor); served arithmetic proven byte-identical by `test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point` (`apps/backend/tests/test_micro_join.py:631-663`) | `apps/backend/app/research/micro_join.py:417-426` |
| Scout trials, kills, denominators, screens (owner: `scout.py`/`scout_ledger.py`, endpoint: `GET /research/desk/micro/scout*`) | OK — same internal-read-path re-point only; every candidate's `decision`/`reason` proven byte-identical by `test_tc5_the_iteration_4_bounded_fixture_grid_still_reads_killed_insufficient_n_after_the_re_point` (`apps/backend/tests/test_scout.py:648-672`) | `apps/backend/app/research/scout.py:341-350` |
| Fold specs, folds, sequences, decay view (owner: new `walkforward.py` + `walkforward_ledger.py`, endpoint: `GET /research/desk/micro/walkforward*`) | OK — this is the row `blueprint.md:57` pre-registered at baseline; built exactly as named, single ledger, single endpoint family, no second implementation anywhere else in the diff | `apps/backend/app/research/walkforward.py` (whole module, new); `apps/backend/app/research/micro_routes.py:270-371` (routes) |
| §6.7 exposure registry / §6.8 process labels / `chain_verification` (new sub-fields on the walk-forward row above) | OK — sub-components of the one already-registered row, not a second value or a second endpoint. Same reasoning this session's coherence audit already applied, independently re-verified here, to Scout's analogous `chain_verification` field in `runs/goal-session-rapid-microscope/iter-4/coherence.md:21` | `apps/backend/app/research/micro_accessor.py:128-196`, `apps/backend/app/research/walkforward.py` `list_walkforward_sequences`/`decay_view` |
| Playbook forward/MDD outcome statistics (unchanged owner: `desk_playbook.py`, Era B2) | OK — read verbatim, `signal["forward"]["horizons"][h]["return_pct"]`, no recomputation of the detector or forward-measurement logic; only pooled into a flat observation list for the fold machinery | `apps/backend/app/research/walkforward.py:970-1007` (`playbook_observations`) |
| Raw snapshot-row reader (`micro_snapshots.read_snapshot_rows`) | OK — now imported/called from exactly ONE module (`micro_accessor.py`), confirmed by a repo-wide grep (zero other call sites in `apps/backend/app/`) and by a real AST-based source-scan test, not merely asserted in a docstring | `apps/backend/app/research/micro_accessor.py:61,265`; guard test `apps/backend/tests/test_micro_accessor.py:208-263` |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /walkforward`, `POST/GET/POST-cancel /walkforward/compute`, `GET /walkforward/runs` (new backend endpoints) | OK — no UI surface this iteration (`Frontend Present: no`; UI surface map confirms "N/A — Backend-only phase"; `git status`/diff confirm zero files under `apps/frontend/` touched). Added to the existing `micro_routes.py` file, no new router; mounted through the pre-existing, unchanged `app.include_router(micro_router)` call in `main.py`. Canonical UI home already reserved by `blueprint.md`'s IA table (`/desk` → Walk-Forward) and wiring is explicitly, disclosedly deferred to J-08 — the same "served ahead of UI wiring" pattern this session's coherence audit has approved every iteration since J-02 (`blueprint.md:77-80`) | `apps/backend/app/main.py:43,217` (router mount, unchanged this iteration); `runs/goal-session-rapid-microscope/state/blueprint.md:39` (canonical home already registered) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- This iteration's own auditor (`docs/handoffs/goal-rapid-microscope-iter-5-audit.md`, verdict `PASS_WITH_GAPS`) found and fixed a real bug in the walk-forward ledger (B1: a repeat diagnostic run double-appended fold-result rows) and left several open gaps (B2: the exposure registry is never r2-initialized for the 12 legacy tick symbol-days in production; B4: sequence identity ignores spec fields other than the rule string; B5: the TR-15 floor refusal isn't wired into `run_diagnostic_walkforward`'s production path; B6: `playbook_observations`' percent-valued `value` field has no unit contract against a bps-denominated `econ_floor`; E1: the browser regression set (TC-29) never ran). None of these create a second source of truth, a duplicate endpoint, or a navigation/nav-home problem — they are spec-completeness, correctness, and evidence-execution gaps within the one canonical mechanism, squarely the auditor's/evaluator's domain rather than this gate's. Recorded here only so it's visible that they were considered and ruled out of this gate's scope, not overlooked.
- No new Data Contract row was needed and none was added — `blueprint.md` was re-read and confirmed accurate for this iteration's scope (`docs/phases/goal-rapid-microscope-iter-5.md`'s own "Blueprint conformance"/"Data-contract additions" fields, independently verified against the diff above, not just taken on trust).
