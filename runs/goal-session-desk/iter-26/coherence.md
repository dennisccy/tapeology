# Iteration 26 — Coherence Audit

**Iteration:** goal-desk-iter-26
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The only registered row touched this iteration is "Top-up run records (per-run outcome ledger)"
(owner `desk_topup_log.py`, endpoint `GET /research/desk/topup/runs`), extended per the blueprint's
own pre-registered "iter-26 addition (J-17)" note and the iter spec's "Data-contract additions"
section.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-pair `requested_window`/`store_frozen_from`/`store_frozen_through`/`window_basis` | OK | Computed once by `_pair_window` (`apps/backend/app/research/desk_topup_compute.py:60-106`), reading the canonical `BarStore.merged_bars` accessor — never `bar_index.window_end_utc`. A source-introspection guard (`apps/backend/tests/test_desk_topup_compute.py:265-279`, `test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_end_utc`, with a seeded-violation counter-test at :282) proves this structurally. |
| `"unchanged"` outcome value | OK | Classified inside `_run_one_pair` (`desk_topup_compute.py:145-149`) from `record_bar_series`'s own 409 (`BarSeriesAlreadyRegistered`) — no second fetch-and-record implementation; `record_bar_series` itself is unchanged. |
| Persistence of the new fields | OK | `desk_topup_log.py` (the row's single owner/writer, `record_topup_run`) needed no code change — it is a schema-agnostic passthrough, confirmed by round-trip tests in `apps/backend/tests/test_desk_topup_log.py:462-503` (new-shape and legacy-shape both round-trip verbatim, no backfill). |
| `/desk` Top-up Runs section display (`counts.unchanged`, tail-vs-full-lookback line, per-failed-pair `requested_window`) | OK | `apps/frontend/app/desk/page.tsx:521-600` reads the fields directly off `run.outcomes` (the payload already served by the existing `GET /research/desk/topup/runs` endpoint the section already consumed) — `topupOutcomeCounts`/`topupWindowBasisCounts` are plain tallies of already-served fields, not a re-fetch or independent recomputation. No new endpoint call added anywhere in the diff. |
| Legacy-run fallback text (`"window basis not recorded in this run"`) | OK | Defined once as `WINDOW_BASIS_NOT_RECORDED` (`page.tsx:538`) and referenced (never re-typed) at every other use site; proven by a dedicated single-shared-constant guard, `apps/backend/tests/test_desk_topup_window_disclosure_guard.py:35-49`, with its own seeded-violation counter-test. |
| `_pair_window` called twice per pair (once in `run_topup` for provenance, once inside `_run_one_pair` for the actual fetch body) | OK (not a violation) | Same function, same store state, no write happens between the two calls (documented at `desk_topup_compute.py:17-33`) — this is one computation invoked twice, not two divergent implementations of the same value. Structurally cannot disagree. |

No new function recomputes bars/coverage/tradability/levels/edge-report/PnL/strategies independently
of their registered owners, and the diff shows zero changes to `bars.py`, `bar_index.py`,
`desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `StructureChart.tsx`,
`PriceChart.tsx` (confirmed via the noise-excluded `git diff --stat`, which lists only
`desk_topup_compute.py` + its tests, `apps/frontend/app/desk/page.tsx`, and `apps/frontend/lib/types.ts`
as product files, plus unrelated `incredible_auto_dev/`/host-guard framework-tooling files that are
outside the app's IA/Data Contract entirely). No new `Config` field and no MCP tool count change
appear in the diff, matching the iteration's own "zero diff" constraints.

## Information Architecture check

No new page, route, or nav entry. The change is confined to the content of the already-registered
`/desk` → Top-up Runs section (blueprint IA table, J-17 row: "`/desk` (existing Top-up Runs section;
zero new section/control, zero new ranked-table column)").

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-17 window-disclosure additions on `/desk` Top-up Runs | OK | No `app/meta.py` (`UI_ROUTES`) diff in the noise-excluded stat — nav inventory unchanged at 3 rows. The section itself (`TopupRunsTable`/`LatestTopupRunDetail`, `apps/frontend/app/desk/page.tsx`) is the same component tree the blueprint already registers under Desk; no parallel shell, no second "top-up" surface introduced. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what is already captured above. The one existing-assertion edit
  (`test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manager_triggered_one`,
  `test_desk_topup_compute.py:1083-1097`) is a schema-mirror extension (four-key set → eight-key set),
  not a relaxation, and is out of this gate's remit (it is a test-content concern the reviewer already
  adjudicated per `reports/reviews/goal-desk-iter-26-review.md`, not a Data-Contract or IA issue).
- The large `incredible_auto_dev/` / host-guard / doctor.sh / roadmap changes in this diff are
  goal-mode framework tooling (reset-forensics, hwmon sampler, doctor checks) unrelated to the
  `tapeology` app's information architecture or data contract — noted here only so a future reader
  does not mistake their presence in the diff for an untracked product surface.
