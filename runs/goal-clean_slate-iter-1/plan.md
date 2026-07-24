# goal-clean_slate-iter-1 Execution Plan

Session `clean_slate`, iteration 1, depth **full**, Mode **next**. Target journey **J-01** ("Backend
demolition with byte-identical relocations") — the first of the five Must-have journeys in "The Clean
Slate" demolition interlude (`docs/goal.md`). Required-still-passing: J-05 in its backend/keyless
subset only — `journey-history.json` currently has no `passing` journeys, so there is no stable-passing
replay set to protect yet. Full acceptance detail, the I-1..I-9 Demolition inventory, Weak-model traps
T-1..T-14, and the TC-1..TC-11 test-first contract live in `docs/phases/goal-clean_slate-iter-1.md` —
the developer must read it in full. This plan distills it plus flags one real gap I found while
cross-checking the inventory against the live repo (see below) — it is a guide, not a restatement.

**Alignment check:** J-01 is named verbatim in `docs/goal.md`'s Must-have journeys and is the explicit
dependency-order first step (J-02's frontend deletion and J-03's MCP contract both assume the backend
routes/modules are already gone). The interlude is operator-directed (2026-07-23) and deletes zero
research value — every KEPT route must stay byte-identical this iteration; only `/research/taxonomy`'s
payload is allowed to shrink. No scope creep: the phase spec's OUT OF SCOPE section (J-02/J-03/J-04
deferred, no browser verification required) is carried forward unchanged below, and matches the spec's
own `Frontend Present: no` metadata — this iteration is keyless/automated, curl/pytest-verifiable only.
I independently confirmed the repo is still at the commit goal.md was authored against (`fa76460`, one
docs-only commit behind current `HEAD`) — zero code drift since the inventory was written.

## ⚠ Inventory gap found — read before deleting `studies.py` (a real T-14 case, not a restatement)

I grepped `studies.py`'s actual importers against `docs/goal.md`'s I-2 RELOCATE table (which names only
two relocations: `r_basis`, and the four `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID`/
`_load_reference_window` symbols) and found a **third, unnamed family of symbols** that `backtests.py` —
a KEPT, frozen-foundation module — genuinely imports from `studies.py` at runtime:

```
backtests.py:110-122 → from .studies import (
    STATUS_CANCELLED, STATUS_DONE, STATUS_FAILED, STATUS_QUEUED, STATUS_RUNNING, TERMINAL_STATUSES,
    _control_state, _premise_state, _synthetic_invalidation, _PathPoint, _PROGRESS_EVERY,
)
```

These are used throughout `backtests.py`'s core job-lifecycle and path-recording logic (job status
persistence, backtest path-point recording, state-native trade helpers, progress-heartbeat throttling)
— confirmed NOT journal-era code by `backtests.py:106-109`'s own comment: *"The status vocabulary and
the state-native helpers are REUSED from the studies module (one owner per literal / per mapping —
never a second copy)."* goal.md's I-2 DELETE-table row for `studies.py` lists `backtests.py:110` as an
importer tagged "(moves)" — but the RELOCATE table's "Symbol(s)" column never names this family, only
the four `SOURCE_*`/`_load_reference_window` symbols (which really do live at `datasets.py:69-70`, not
`backtests.py`). **If `studies.py` is deleted without relocating this second family too, `backtests.py`
breaks on import — an immediate, guaranteed suite failure**, not a subtle bug, and it would fail this
iteration's own ordering-discipline gate (full suite green after relocation, before any deletion).

Two more confirmed consumers of the same orphaned family:
- `tests/test_backtests.py:64` — a KEPT test file (I-8 "KEEP unmodified... all kept-research tests...
  backtests*") — imports `_PathPoint` directly `from app.research.studies`.
- `tests/test_studies_reference.py` (an I-8 **UPDATE** file, not delete — "re-point at the relocated
  loader/constants... the coverage itself stays") — 3 of its 4 tests (`test_reference_pg_sip_study_...`,
  `test_reference_study_is_deterministic_double_run`, `test_reference_seeded_sim_study_pins_exact_...`)
  don't call `_load_reference_window` directly; they exercise it *indirectly* by running a full study
  job through `StudyJobManager` (`studies.py:741`, itself DELETE-listed — the `/research/studies` engine
  being removed this iteration). Only the 4th test (`test_observer_equivalence_and_dense_gate_modules_
  import_unchanged`) calls `_load_reference_window` directly. Simply "re-pointing an import" per I-8's
  literal wording is insufficient for the other 3 — `StudyJobManager` won't exist to run.

**Recommended handling (document as a T-14 inventory correction in the dev handoff, per goal.md's own
protocol — "STOP and surface it... the fix is a documented inventory correction, never a silent
improvisation"; this is not a stop-the-pipeline event, the fix is bounded and precedented):**
1. Treat the `STATUS_*`/`_control_state`/`_premise_state`/`_synthetic_invalidation`/`_PathPoint`/
   `_PROGRESS_EVERY` family as a **third relocation**, landed in the same relocate-and-prove-green step
   as `r_basis` and the `SOURCE_*` symbols. `backtests.py` is its only surviving non-test runtime
   importer (confirmed by grep — nothing else in `apps/backend/app/` imports these from `studies.py`
   except `routes.py`'s own delete-side import, which dies with the deleted routes), so relocating it
   into `backtests.py` as private helpers/constants — exactly the same pattern as `r_basis` — is the
   consistent default. Verify with your own T-12 grep before committing to this.
2. Update `test_backtests.py:64`'s import to the new home once relocated.
3. For `test_studies_reference.py`'s 3 `StudyJobManager`-dependent tests: rework them to exercise the
   relocated reference-window path without depending on the deleted study-job engine, preserving the
   file's stated purpose (I-8: "guards the founding-baseline data path", the pinned J-62 gate). This is
   a real judgment call — decide the minimal faithful rewrite (e.g., drive the reference/seeded-sim
   computation directly rather than through `StudyJobManager.create`/`run_sync`) and document what
   changed and why in the dev handoff. Do not stub or recreate `StudyJobManager` itself (T-2).
4. Run T-12's grep-before-delete for `studies` for real before deleting the file — don't rely solely on
   this note; it was a spot-check, not an exhaustive substitute for the protocol goal.md already
   mandates.

## What to Build

Backend-only, keyless/automated (curl + pytest). Ordering discipline is load-bearing: relocations must
land and the full suite must be green **before** any deletion below (I-2's own rule; T-3/T-12 apply
throughout).

1. **Baseline capture (I-9 step 1):** with the backend running on committed fixtures, sha256 every KEPT
   `/research`, `/tape`, `/meta` GET route into `runs/goal-session-clean_slate/iter-1/kept-route-
   baseline.txt`, before touching any code.
2. **Relocate, then prove green:** `r_basis` (`marks.py` → `backtests.py`, private helper, same math);
   the four `SOURCE_*`/`_load_reference_window` symbols (`studies.py` → `datasets.py`, updating
   `datasets.py`, `backtests.py` [see gap above — NOT this row], `pnl_baseline.py`, and the
   `edge_report.py:72` comment); **plus the third relocation flagged above.** Run the full suite — green
   — before any deletion.
3. **Delete 14 I-1 routes** from `routes.py` (`analytics`, `thesis/active`, `hints/active`, `hints`,
   `journal`, `journal/{id}`, `thesis` POST/resolve/action/review, `studies` POST/GET/{id}/cancel) plus
   dead helpers `build_journal_detail`, `get_study_market_adapter`.
4. **SLIM `GET /research/taxonomy`** (`taxonomy.py`) to the `feed_basis` block + `sim`/`iex`/`sip`/
   `yahoo` source labels only; delete every verdict/thesis-status/stance/`STUDY_COPY` family (a label
   family survives only if a kept surface provably reads it — grep the frontend + kept routes).
5. **Strip `routes.py`'s delete-side imports** and `ResearchRegistry`'s `study_jobs`,
   `hint_projection_for`, `on_engine_created`, `startup_sweep` (store access + backtest/edge-compute job
   managers stay).
6. **`main.py` lifespan-wiring removal only** — `manager.set_on_engine_created(registry.
   on_engine_created)`, `registry.startup_sweep()`, and the shutdown unset. The WS `thesis`/`hint` frame
   merge is explicitly **J-02's job, not this iteration's** — do not touch it here.
7. **Delete the eleven journal-era modules** (`journal_rows`, `monitor`, `hints`, `stance`, `verdict`,
   `grades`, `marks`, `excursions`, `execution_checks`, `analytics`, `studies`) — T-12 grep-before-delete
   each, individually, no exceptions (studies.py especially — see gap above).
8. **Delete `JournalStore`'s journal-era methods + record dataclasses** (`store.py`, per I-3's DELETE
   list) — migrations, schema version (`v8`), and every I-3 KEEP method (backtest/pnl/champion/
   migration methods) stay byte-untouched. `config.py` is **not** touched this iteration even though
   `execution_checks.py` (the module) is deleted — its config fields and schema-history comments are
   J-04's job (T-3); leave it alone.
9. **Delete ~24 journal-era test files** (full list in the phase spec's IN SCOPE section) and apply the
   I-8 UPDATE edits belonging to this iteration: `test_research_api.py`, `test_research_store.py`,
   `test_studies_reference.py` (see gap above — bigger than a re-point), `conftest.py`, and
   `test_copy_discipline.py`'s served-copy walk (drop verdict/checklist/hint/analytics/studies served
   copy; its frontend-literal walk is J-02's). Leave `test_mcp_server.py` and `test_meta_routes.py`
   untouched (J-03/J-02's contracts).
10. **Leave every `Config` field and all 13 fingerprint pin assertion sites byte-unmodified** (J-04's
    job only — T-3). `python -c "from app.config import Config; print(Config().config_fingerprint())"`
    must still print `4d665603569b9dbf` at the end of this iteration.
11. **Re-capture the byte-comparison hashes** (I-9 step 2) and diff against the baseline — zero deltas
    except `/research/taxonomy`'s expected shrink.
12. **Re-run T-12's grep** for all eleven deleted module names (plus `studies` per the gap note) across
    `apps/` — zero live hits outside `reports/**`, `runs/**`, `docs/goal-archive/**`.
13. Dev handoff at `docs/handoffs/goal-clean_slate-iter-1-dev.md`, including the T-14 write-up for the
    gap above (what was relocated, where, and how `test_studies_reference.py` was reworked).

## Out of Scope (carried from the phase spec — do not relitigate)

- Frontend/WS demolition (J-02): pages, components, `lib/api.ts`, types, cockpit thesis/hint/sound
  integration, `PriceChart.tsx`'s overlay removal, `app/meta.py` ROUTES trim, WS `thesis`/`hint` merge
  removal in `main.py`.
- MCP tool removal (J-03): `_TOOL_PATHS`/`types.Tool` deletions, `test_mcp_server.py`'s 15-tool
  contract. The three soon-dead MCP tools transiently proxy to now-404 routes via `get_endpoint`'s
  existing honest-404 contract this iteration — expected, not a defect.
- `Config` field deletion + the `config_fingerprint` epoch bump (J-04) — strictly deferred; zero diff on
  the 13 pinned assertion lines is a hard requirement of this iteration, not J-04's.
- `test_meta_routes.py` (J-02's job) and `test_copy_discipline.py`'s frontend-literal walk (J-02's job).
- Restoring `/structure`'s suppressed `SHOW_CASE_STUDIES` flag — pre-existing, unrelated, flagged again
  for J-02/J-05 planning, not this iteration.
- Any browser/UI verification — this iteration is keyless/automated; no Chrome MCP dispatch expected.
- Schema migrations, `journal.db` table drops, any edit to `_migrate`/`_create_schema` — dormant tables
  are the correct end state.

## Agents Required

- developer: yes — implements J-01 end to end per "What to Build" above, including resolving the
  flagged relocation gap and documenting it in the dev handoff. This project's agent roster has one
  implementation agent (`developer`) covering all backend/frontend work — there are no separate
  backend-data/frontend-ux agents in `.claude/agents/`. In file terms this iteration is backend-only:
  `git diff apps/frontend/` must be empty.

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/research/routes.py` — delete 14 route handlers + dead helpers; strip delete-side
  imports; slim `ResearchRegistry`.
- `apps/backend/app/research/taxonomy.py` — SLIM to kept label families.
- `apps/backend/app/research/backtests.py` — gains `r_basis` (private) **and** the STATUS_*/control-
  state/`_PathPoint`/`_PROGRESS_EVERY` family (gap above); no behavior change.
- `apps/backend/app/research/datasets.py` — gains `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/
  `REFERENCE_SOURCE_ID`/`_load_reference_window`.
- `apps/backend/app/research/pnl_baseline.py` — import updated to `datasets.py`.
- `apps/backend/app/research/edge_report.py` — one comment updated (line ~72).
- `apps/backend/app/main.py` — lifespan monitor-wiring removal only (not the WS merge).
- `apps/backend/app/research/store.py` — delete journal-era methods + dataclasses (I-3); migrations
  untouched.
- **Delete:** `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`, `grades.py`,
  `marks.py`, `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py`.
- `apps/backend/tests/` — delete ~24 journal-era test files; update `test_research_api.py`,
  `test_research_store.py`, `test_studies_reference.py` (rework, not just re-point — see gap),
  `conftest.py`, `test_copy_discipline.py`; update `test_backtests.py:64`'s `_PathPoint` import.
- `runs/goal-session-clean_slate/iter-1/kept-route-baseline.txt` — new, the I-9 byte-comparison capture.
- `docs/handoffs/goal-clean_slate-iter-1-dev.md` — new, required.
- **Zero diff expected:** `apps/backend/app/config.py`, all 13 fingerprint pin assertion lines,
  `test_mcp_server.py`, `test_meta_routes.py`, every file under `apps/frontend/`, `app/engine/`.

## Key Test Scenarios

(Full TC-1..TC-11 wording in the phase spec; condensed here.)

- Relocations land and `pytest apps/backend/tests/` is green **before** any deletion (ordering gate).
- Each of the 14 deleted routes returns exactly HTTP 404 (correct verb); `GET /research/taxonomy`
  returns 200 with `feed_basis`+source labels and none of the deleted label families.
- Every OTHER kept `/research`/`/tape`/`/meta` GET route is byte-identical (sha256) to the pre-deletion
  baseline capture.
- T-12 grep for each of the eleven deleted modules (studies.py included — verify the gap's relocation
  closed every real importer) returns zero live hits outside `reports/**`/`runs/**`/
  `docs/goal-archive/**`.
- `JournalStore` I-3 KEEP methods (`insert_backtest`, `append_pnl_ledger_row`, `get_champion_pointer`,
  `list_pnl_ledger`) return identical shape/values to the pre-iteration suite run.
- Full backend suite: 0 failed, 0 errors; collected-test count no higher than 1665 minus the deleted
  files' test counts (iter-0's confirmed baseline: 1665 passed / 7 skipped).
- `config_fingerprint()` still prints `4d665603569b9dbf`; none of the 13 pinned assertion lines differ
  from `fa76460`.
- Diff contains zero touches to `docs/goal-archive/`, `runs/goal-session-*` (other than this iteration's
  own new `iter-1/` artifacts), `reports/goal-session-*-delivered.md`, or `journal.db`'s existing rows.
- `test_backtests.py`, all engine tests, all chart guard suites
  (`test_cockpit_chart_upgrade.py`/`test_structure_chart_viewport.py`/`test_price_chart_confluence.py`),
  `test_no_execution_path.py`, `test_no_credential_in_artifacts.py` pass byte-unmodified.
