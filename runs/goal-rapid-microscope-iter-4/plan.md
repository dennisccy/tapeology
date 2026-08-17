# goal-rapid-microscope-iter-4 Execution Plan

## Context (for the dispatched agents, not part of the spec)

Session `rapid-microscope`, iteration 4, target journey **J-04** (the Scout + exploratory
candidate ledger), with **J-01/J-02/J-03/J-10 required to stay green** — the regression set widens
to every currently non-failing journey because iteration 3's evaluator verdict was ESCALATE (the
depth arbiter's unconditional Full-trigger-3 rung; confirmed in
`reports/phase-goal-rapid-microscope-iter-3-iteration-summary.md`: "Regressions in last 4 iters:
none," so this widening is precautionary, not a repair task). Two small passenger honesty fixes
ride along in `micro_join.py` (iteration 3's own binding next-step recommendation, items 1-2 of
4 — items 3-4 are explicitly NOT this iteration's job, see below).

`docs/rapid-validation-spec.md` §1 (constants) and §5 (the Scout) are canonical — read directly;
verified this iteration to be verbatim-consistent with the phase spec, no drift. Implement from
the spec, never re-derive; an ambiguity is a drop + owner ruling, not an invention (T-1). The full
acceptance contract (TC-1…TC-20) lives in `docs/phases/goal-rapid-microscope-iter-4.md` — developer
and reviewer should read that file directly; this plan routes and anchors, it does not restate it.

**Confirmed against `docs/goal.md`:** J-04 is a Must-have journey, next in the natural dependency
order (J-01→J-02→J-03→**J-04**→J-05…), and the era's own Vision explicitly accepts "zero survivors
is a passing grade" — an all-`killed_insufficient_n` outcome on the tiny fixture grid this
iteration registers is an HONEST PASS, not a shortfall. **No scope creep found:** the phase spec's
OUT OF SCOPE section already fences off J-05/J-06/J-07, any pilot-study mechanism (J-09), the
`/desk` Scout Ledger rendering + `desk_scout` MCP tool + the 26-tool bump (J-08), and any change to
a frozen spec §1 constant (`KILL_REASONS`, `SCOUT_*`, `ECON_FLOOR_SPREAD_MULTIPLE`). The
`quote_depletion` exclusion is a deliberate, logged scope narrowing pending a human owner ruling on
`micro_observer.py:636/657` — correctly NOT invented here, and correctly NOT blocking the rest of
J-04.

**Do-Not-Redo** (already shipped and verified present on disk this iteration):
`micro_readiness.py` (J-01), the observer/snapshot/feature stack (J-02), `micro_join.py`'s join
primitives + the `joinable_corpus` field (J-03). `app/research/scout.py` and `scout_ledger.py` do
**not** exist yet — this iteration creates them from scratch.

## What to Build

- `scout_ledger.py` (NEW) — hash-chained, append-only JSONL candidate ledger per spec §5.1/§5.2:
  frozen candidate spec (`candidate_id`, `family_id`, `family_root_id` =
  `sha256(canonical(feature_family_name, structure_context_kind, outcome_horizon_family))[:16]`,
  `feature`, `structure_context`, `outcome`, `fitting_rule?`, `econ_floor`, `corpus_manifest`,
  `grid_version`, `registered_at`, `spec_hash`); one permanent row per evaluated variant
  (`decision: survive|<KILL_REASONS>`, `reason`, `notes`, the family's running union-N
  `variants_tried`); `superseded` rows point at their successor, never deleted; chain verification
  fails exactly at a tampered row (TR-11).
  - **Build note:** the cited precedent `desk_playbook_log.py` stores an *independent*
    `sha256(canonical(record))` per record (`_sha256`/`_canonical`, lines 77-85) — a per-row
    checksum, not a literal linked chain. To satisfy "hash-chained" and TR-11's
    chain-verification-failure-at-row-*k* (which should also catch deletion/reordering, not only
    in-place edits), each row should commit to the previous row's hash, not only its own fields —
    a genuinely new pattern in this codebase, not a copy-paste of the playbook-log file.
- `scout.py` (NEW) — spec §5.3 screening (`session_date` cluster unit, frozen & corpus-size-
  invariant; within-session circular block permutation as the null, block length ≥ the longest
  evaluated horizon's label span; the banned plain row-shuffle reachable ONLY from a test-only
  counter-test path, never a production call path; non-overlapping anchor subsampling for
  clock-horizon effects), §5.4 disclosures (session/symbol concentration, ToD-bucket slices,
  fallback-tercile stratification for aggressor-derived features, best-of-N expected-max-under-null,
  `evidence_class`), §5.5 economic relevance (`econ_interesting` served beside — never merged
  into — the statistical screen, frozen proxy sentence verbatim), the `SCOUT_MAX_VARIANTS_PER_FAMILY`
  (24) grid bound.
- `ScoutComputeManager`, mirroring `MicroSnapshotComputeManager`
  (`apps/backend/app/research/micro_snapshots.py:374-513`) verbatim in shape: single-flight
  (`{"state": "refused", "reason": "already_running"}` on a concurrent trigger), dedicated worker
  thread, pollable progress snapshot, cooperative cancel, **terminal-state-only ledger writes** (a
  mid-run exception resolves the job to `"failed"`, never a silently-short ledger write —
  iteration-2's streamed-artifact-completeness lesson, explicitly named for this manager).
- Wire three routes into the EXISTING `micro_routes.py` (no new router file): `GET
  /research/desk/micro/scout`, `POST` + `GET` + `POST .../compute/cancel` on
  `/research/desk/micro/scout/compute`, `GET /research/desk/micro/scout/runs` — mirror the
  snapshot routes' own shape (lines 72-90 for the dir-resolver + singleton pattern, 92-154 for the
  route bodies) closely; reuse `get_dataset_store`/`get_playbook_store` verbatim — no new
  dataset/playbook store provider (a NEW scout-ledger directory resolver + manager singleton,
  analogous to `get_micro_snapshots_dir`/`get_micro_snapshot_compute_manager`, is expected and is
  not what that "no new store provider" line rules out).
- Register a bounded (≤24/family) fixture grid over the already-committed hermetic fixtures
  (`tests/fixtures/datasets/`, `tests/fixtures/datasets_j03/`) plus a purpose-built synthetic
  session-clustered autocorrelated-null fixture for TR-8; run it end to end through both the
  manager and an embedded CLI `main()`/argparse entry point (the `micro_snapshots.py:513+`
  precedent) — an all-`killed_insufficient_n` result on this tiny corpus is honest and acceptable
  (goal.md's own Vision). **Zero registered candidates condition on `quote_depletion`.**
- TR-8 (200-seed calibration on the autocorrelated null, pass-rate ≤ 1.5 × 0.05 = 0.075, plus the
  banned-shuffle counter-test demonstrably exceeding that ceiling), TR-9 (registration-ordering
  refusal), TR-10 (pool invariance across +100 null candidates), TR-11 (union-N + tamper/­deletion
  detection).
- Passenger fix 1 — `micro_join.py:385` (`for playbook_record in playbook_store.list()[0]:`
  discards the tuple's second element): read and surface `playbook_store.list()`'s `_errors`
  return value into `joinable_corpus`'s response, or refuse outright — never silently drop a
  corrupt record from `total`/`playbook_signal_count`/`by_setup_id`.
- Passenger fix 2 — `micro_join.py:401-406` (`band_touch_count = 0`, a bare literal returned
  verbatim in the response dict): change the SHAPE so a reader can tell "not enumerated yet" apart
  from "counted and found zero." Still owned by `micro_join.py`, still served on the existing `GET
  /research/desk/micro/readiness` (no new endpoint, no UI change) — defining a real touch stays
  J-09's job.
- Re-verify unchanged: fingerprint `08e471b10130e1e2`, all 6 `referee_*.py` SHA-256 hashes, the
  18-snapshot row total (3,815,933), and that this iteration's diff never touches
  `micro_features.py`/`micro_observer.py` (so no snapshot rebuild is expected).
- Dev handoff at `docs/handoffs/goal-rapid-microscope-iter-4-dev.md`.

## Agents Required

- backend-data: yes -- implement `scout_ledger.py`, `scout.py`, `ScoutComputeManager`, the 3 new
  `micro_routes.py` routes, the fixture grid + CLI entry point, TR-8/9/10/11, both passenger fixes
  in `micro_join.py`, and the full TC-1…TC-20 test set.
- frontend-ux: no -- zero `.tsx` files change. J-04's Scout Ledger UI rendering is explicitly
  J-08's scope; this iteration serves data through new endpoints only, not yet rendered — the same
  served-ahead-of-UI-wiring pattern already approved for J-02/J-03 by the coherence auditor.

## Frontend Present
Frontend Present: no

(`docs/phases/goal-rapid-microscope-iter-4.md`'s own Goal Mode Metadata states this explicitly.
J-04 names no browser action in `docs/goal.md`, and every shipped `/desk` section — including the
Microscope Readiness panel the two passenger fixes touch — keeps rendering exactly as shipped, DOM
byte-unchanged. The browser-qa-agent still runs for the required-still-passing set: J-01/J-02/J-03
re-verify unchanged and J-10 re-runs its full kept-product sentinel script
(`runs/goal-session-rapid-microscope/journey-scripts/J-10.json`) unmodified — but records an honest
SKIP for J-04 itself, the same precedent already established for J-02/J-03, never an unscored gap.)

## Files to Create/Modify

- `apps/backend/app/research/scout_ledger.py` -- NEW: hash-chained append-only ledger, closed
  kill vocabulary, union-N, `superseded` semantics, chain verification.
- `apps/backend/app/research/scout.py` -- NEW: screening procedure, disclosures, econ-floor
  column, `SCOUT_MAX_VARIANTS_PER_FAMILY` bound, `ScoutComputeManager`, CLI entry point.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: add the 3 scout routes + a scout-ledger
  directory resolver + compute-manager singleton, mirroring the snapshot routes' own wiring.
- `apps/backend/app/research/micro_join.py` -- MODIFY: line 385 surface `playbook_store.list()`'s
  discarded `_errors`; lines 401-406 replace the bare `band_touch_count = 0` literal with a typed
  "not enumerated" representation.
- `apps/backend/app/research/micro_readiness.py` -- MODIFY only as needed to pass through the
  changed `band_touch_count` shape from `micro_join.py` — no independent computation here, same
  single-owner discipline as today.
- `apps/backend/tests/test_scout_ledger.py` -- NEW: TC-1, TC-2, TC-3, TC-4, TC-9, TC-13 (chain
  integrity, `superseded`, union-N, the 24-variant grid bound, no `quote_depletion` candidates).
- `apps/backend/tests/test_scout.py` -- NEW: TC-5, TC-6, TC-7, TC-8, TC-10, TC-11, TC-12
  (calibration + banned-shuffle counter-test, registration ordering, pool invariance, manager
  single-flight, manager/CLI parity, served disclosures + econ column).
- `apps/backend/tests/test_micro_join.py` -- MODIFY: TC-14 (corrupt-record surfacing), TC-15
  (`band_touch_count` typed shape), TC-16 (real-store arithmetic unchanged before/after).
- `apps/backend/tests/test_micro_readiness.py` -- MODIFY: extend for the new `band_touch_count`
  shape (TC-15).
- New synthetic session-clustered autocorrelated-null fixture (location/naming at developer's
  discretion, committed under `apps/backend/tests/fixtures/`) for TR-8's 200-seed calibration.
- `docs/handoffs/goal-rapid-microscope-iter-4-dev.md` -- NEW: dev handoff, including the TC-16
  before/after arithmetic proof and the suite/fingerprint/referee-hash/snapshot-row-total
  re-checks (TC-17/TC-18/TC-19).

No `docs/goal.md`, `blueprint.md`, or `docs/rapid-validation-spec.md` edit expected — all three
were re-read this iteration and confirmed already accurate for this scope (the Scout Ledger row
was pre-registered in `blueprint.md`'s Data Contract at baseline).

## Key Test Scenarios

- TC-1/TC-2: the bounded fixture grid, run end to end via `ScoutComputeManager`, produces exactly
  one closed-vocabulary row per registered variant in `scout_ledger.py`, and `GET
  /research/desk/micro/scout` serves the union-N `variants_tried` across grid versions (v1 N=40 +
  v2 N=25 ⇒ 65).
- TC-3/TC-4: an in-place edit of ledger row *k* fails chain verification AT row *k*; a
  `superseded` row stays on record with a resolvable successor pointer.
- TC-5/TC-6: TR-8's 200-seed autocorrelated-null calibration holds pass-rate ≤ 0.075; the banned
  plain row-shuffle (test-only path) demonstrably exceeds that ceiling.
- TC-7: a candidate whose econ-floor inputs were read after its own `registered_at` is refused,
  no row written (TR-9).
- TC-8: 100 added null candidates at an origin change no prior candidate's ledgered
  threshold/pass-fail, re-read byte-identical (TR-10).
- TC-9/TC-10: a 25th variant for an already-24-variant family is refused; a concurrent
  `trigger()` on a running screen returns `{"state": "refused", "reason": "already_running"}`,
  never a second worker.
- TC-11: manager-triggered and CLI-triggered runs over the same grid produce identical
  `spec_hash`/`params_hash`/`decision`/`reason` per candidate — no second implementation of the
  screen.
- TC-12: a served screen carries `evidence_class`, the best-of-N disclosure, concentration/ToD/
  fallback-tercile slices, and `econ_interesting` beside (never merged into) the statistical
  verdict, with the frozen proxy sentence present verbatim.
- TC-13: no registered candidate this iteration conditions on `quote_depletion`.
- TC-14: a fixture playbook store whose `.list()` returns non-empty `_errors` surfaces that
  corruption in `joinable_corpus` (raise or explicit field) rather than silently shrinking
  `total`/`playbook_signal_count`/`by_setup_id`.
- TC-15: `GET /research/desk/micro/readiness`'s `band_touch_count` is a typed value a reader can
  tell apart from a real zero.
- TC-16: against the REAL `.data/datasets` + playbook stores, `playbook_signal_count` stays `2`
  and `by_setup_id` stays `{"range_trade": 2}` before/after both passenger fixes — only the
  corruption-surfacing and `band_touch_count` shape change, never the enumerated arithmetic.
- TC-17/TC-18: fingerprint `08e471b10130e1e2`, all 6 `referee_*.py` hashes, and the 18-snapshot
  row total (3,815,933) unchanged.
- TC-19: full `pytest tests/` (no extra `-q` — `pyproject.toml` already sets `addopts = "-q"`,
  the iter-0 lesson) reports ≥ 2,866 pass / 8 skip, 0 new failures.
- TC-20: browser-qa re-verifies J-01/J-02/J-03 unchanged and J-10's full sentinel script green
  (screenshots on record); J-04 records an honest SKIP, not an unscored gap.
