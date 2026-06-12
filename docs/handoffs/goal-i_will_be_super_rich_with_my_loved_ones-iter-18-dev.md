# goal-i_will_be_super_rich_with_my_loved_ones-iter-18 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

The replay-study layer (capability 32, J-60/J-61/J-62) — the last evidence-layer step before the cue layer.

- **Study runner — single-owner module** (`app/research/studies.py`): an unpaced offline replay over a
  chosen source + window through a **fresh `TapeEngine`**, attached ONLY via the existing observer
  seam (the `test_real_data_classify.py` / `test_dense_replay_gate.py` pattern). Read-only over the
  engine — observer-equivalence (J-68) stays green; no engine/provider/classifier/history/snapshot file
  was touched.
- **Three sources through existing seams:** (a) the committed PG SIP reference fixture
  (`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`, loadable without credentials — the
  iter-17 capability-34 fixture, now its second consumer); (b) seeded sim scenarios (SIM-REVERSAL,
  SIM-BUYER, etc.) replayed unpaced; (c) arbitrary symbol + past window via the EXISTING adapter
  `fetch_historical` path (credentialed; existing explicit error states on failure — never fabricated).
- **State-native auto-arming** for `absorption_reversal` (sustained matching absorption) and
  `trend_continuation` (sustained matching control), composed ONLY of existing engine states, gated by
  config-owned sustain + cooldown. Each armed occurrence runs the EXISTING per-setup verdict rule table
  (`verdict.VerdictEvaluator`) — no new rule, no new indicator — recording its verdict summary.
- **Level setups** (`level_break` / `failed_move_fade`) require a user-supplied level: stamped
  `hindsight_level` and `excluded_from_cross_study_aggregate` (enforced in code + tested). A level setup
  with no level is a **422** at the route, never a guessed level.
- **Seeded random-arm-time null baseline:** `study_null_arm_count` arm times drawn from a recorded seed
  over the SAME window / direction / R definition / horizons. The seed is persisted on the study record.
  **ONE replay pass serves both populations** (the observer records the snapshot path in memory once;
  every arm — setup or null — measures its excursions against that recorded path). No tape data is
  persisted (in-job memory only).
- **Excursions per occurrence** via the EXISTING `excursions.ExcursionTracker` (arm-anchored entry
  population, per config horizon, first-touch in logical time); window-end-truncated horizons are
  flagged `truncated` and counted separately — never dropped, never extrapolated.
- **Cancellable background jobs** (`StudyJobManager`): `queued | running | done | cancelled | failed`
  with progress; cancellation honored cooperatively between events; cancelled → explicit `cancelled`
  with `partial: true`; failed → explicit `error`, never an empty success. Jobs run on a worker thread
  OFF the event loop; ALL SQLite writes go through the existing single writer queue.
- **Four endpoints** (blueprint row 23): `POST /research/studies` (create + start, full 422 validation),
  `GET /research/studies` (list), `GET /research/studies/{id}` (status/progress + stored results),
  `POST /research/studies/{id}/cancel` (404 unknown, 409 terminal). Served VERBATIM — never recomputed
  at read.
- **Taxonomy copy** (row 24, additive): study status labels (each its own copy), per-status
  honest-absence sentences (each distinct — iter-15 lesson), hindsight label, truncated label (reused),
  null-baseline caption, journaled-measurements framing — all via `GET /research/taxonomy → studies`.
- **Frontend:** enabled the pre-registered Studies nav entry; new `/studies` page (create form, job
  list with cancel, results view with setup distribution side-by-side with the seeded null baseline,
  occurrence rows, feed + fingerprint + seed stamps, hindsight label, n + caveats, "Descriptive only").

## The documented occurrence-R design decision (the reviewer's flagged ambiguity)

An auto-armed occurrence has no user-typed invalidation, so its R basis is derived **deterministically**
from existing engine values **at the arm instant**:

- A **synthetic invalidation** is placed `study_occurrence_r_spread_multiple × spread_at_arm` (floored
  at `study_occurrence_r_floor`) on the **adverse** side of the arm price (below for a long, above for a
  short). Defaults: spread multiple `10.0`, floor `0.05`.
- `R = |arm_price − synthetic_invalidation|` via the **single shared `marks.r_basis` helper** — the
  study is a **registered consumer of the one R formula**, never a second one. R values and ternary
  outcomes flow through the existing `excursions.ExcursionTracker` + `excursion_horizons_seconds`.
- **Identical for setup and null arms** — each arm derives its own basis from its own arm-instant price
  + spread the same way.
- It is **config-owned and documented as a research default** — NEVER fitted (fitting it to make
  results look good would be auto-tuning). All five shaping keys (`study_null_arm_count`,
  `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`,
  `study_occurrence_r_floor`, `study_null_baseline_seed`) ENTER `config_fingerprint`; `study_list_max`
  is serving-only and EXCLUDED (with a stability + counter test).

## Pinned reference-study numbers (the J-62 flip — see `tests/test_studies_reference.py`)

Reproducible from the committed PG SIP fixture + the seeded sim, unpaced, no credentials, in budget
(~3 s on the dev machine vs the 60 s `dense_replay_time_budget_seconds`). Double-run determinism asserted.

**Reference — PG SIP, `trend_continuation` long** (feed `sip`, source `historical PG reference`):
- setup n = 2; per-horizon `[+1R, −1R, neither, truncated]`:
  10s `[0,0,2,0]`, 30s `[0,0,2,0]`, 60s `[0,1,1,0]`, 120s `[0,1,0,1]`
- null baseline n = 99; per-horizon:
  10s `[4,3,91,1]`, 30s `[7,4,79,9]`, 60s `[8,5,72,14]`, 120s `[8,6,62,23]`
- occurrence R bases `[0.3, 0.6]`; verdict summaries `["invalidated", "confirming"]`

**Seeded sim — SIM-REVERSAL, `absorption_reversal` long** (feed `sim`):
- setup n = 1; per-horizon: 10s `[0,0,1,0]`, 30s `[0,0,1,0]`, 60s `[1,0,0,0]`, 120s `[1,0,0,0]`
- null baseline n = 100; per-horizon:
  10s `[0,0,90,10]`, 30s `[58,0,21,21]`, 60s `[70,0,7,23]`, 120s `[77,0,0,23]`
- the setup occurrence reaches `+1R_first` at 60s/120s (the reversal lifted price), verdict `confirming`,
  R basis `0.2`.

## Files Changed

- `apps/backend/app/research/studies.py` -- NEW single-owner study runner + `StudyJobManager`
- `apps/backend/app/research/routes.py` -- four `/research/studies` endpoints + `StudyJobManager` on the registry
- `apps/backend/app/research/store.py` -- `StudyRecord` + study repository methods (NO schema bump — stays v7)
- `apps/backend/app/research/taxonomy.py` -- additive row-24 studies display copy
- `apps/backend/app/config.py` -- 6 study config keys (5 IN fingerprint, `study_list_max` excluded)
- `apps/backend/app/main.py` -- drain in-flight study jobs on shutdown (lifespan finally)
- `apps/backend/tests/test_studies.py`, `test_studies_reference.py`, `test_studies_api.py` -- NEW
- `apps/frontend/components/NavBar.tsx` -- enabled the Studies nav entry
- `apps/frontend/app/studies/page.tsx` -- NEW route
- `apps/frontend/components/StudyCreateForm.tsx`, `StudyList.tsx`, `StudyResultsView.tsx` -- NEW
- `apps/frontend/lib/api.ts`, `lib/types.ts` -- study API functions + types

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/` (verified by EXIT CODE — the `-q`
double-quiet gotcha avoided)
Result: **671 passed, 1 skipped, 0 failed** (was 629+; +42 new study tests, zero re-pins).
Regression gates green: `test_observer_equivalence.py` (7/7), `test_dense_replay_gate.py`,
`test_real_data_classify.py`. Frontend build: clean (`npm run build` — `/studies` route 7.1 kB).

Live verification: backend started AFTER dev on :8777 with a persistent DB, canary-probed
(`GET /research/taxonomy` carries the new studies copy), a study created → background job → `done` with
the setup distribution + 100-arm null baseline; server stopped cleanly afterward.

## Schema

**No schema bump — stays v7.** The `studies` + `study_occurrences` tables already exist (v1 payload-blob
shape); the entire study state lives in `studies.payload` and the occurrence rows are mirrored verbatim
into `study_occurrences` (first writes to both tables). No `ALTER TABLE`, no migration, no v7→v8 step.
Confirmed: the store diff carries no `CREATE TABLE` / `ALTER TABLE` / `_migrate` / `journal_schema_version`
change.

## Diff confinement

App-code changes are ONLY under `app/research/**`, `app/config.py`, and `app/main.py` (routes wiring +
shutdown drain). NO engine/provider/classifier file changed; the store change is additive (a dataclass +
repository methods), no schema change. Verified via `git diff --stat`.

## Known Issues

- **Background jobs are process-scoped.** A backend restart loses in-flight jobs; a study left `running`
  in the DB by a prior process is NOT auto-resolved (it stays `running` honestly — never silently
  completed). This matches the spec's intent (no fabricated success). A future iteration could add a
  startup sweep that marks orphaned `running` studies `failed` with a restart reason.
- **Arbitrary-window historical studies require live credentials.** With no credentials the create
  endpoint returns an explicit 422 "real-data provider unavailable" — never fixture-substituted. Live
  credentialed verification of the arbitrary-window path was NOT run here (no creds in this environment);
  the reference + sim paths are fully covered in CI without credentials, and the credentialed path reuses
  the exact same `adapter.fetch_historical` seam the watch path already exercises.
- The per-occurrence verdict summary reconstructs directional impact from the recorded tape state (a
  control state implies matching directional impact) rather than re-running the feature engine, so the
  summary reads the canonical state verbatim and stays deterministic without a second feature computation.
  The verdict semantics (the existing rule table) are unchanged.
