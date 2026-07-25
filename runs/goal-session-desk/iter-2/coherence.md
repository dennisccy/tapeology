# Iteration 2 — Coherence Audit

**Iteration:** goal-desk-iter-2
**Date:** 2026-07-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only (`Frontend Present: no`, target journey J-02). `runs/goal-session-desk/iter-2/iter-diff.md`
does not exist, so the review used the exact noise-excluded `git diff 8448b8821bf7f94965164071e1093dd96c3abb9d`
command from the invocation prompt, plus direct reads of the two new untracked production modules
(git does not diff untracked files):

- Modified (tracked): `apps/backend/app/research/bar_index.py` (+1 additive method, `coverage()`),
  `apps/backend/app/research/desk_routes.py` (+2 new route groups under the existing J-01 router),
  `apps/backend/tests/test_bar_index.py` (+5 tests).
- New (untracked, production): `apps/backend/app/research/desk_coverage.py` (`get_desk_coverage`),
  `apps/backend/app/research/desk_topup_compute.py` (`DeskTopupComputeManager`, `run_topup`, CLI
  `main()`).
- New (untracked, tests): `apps/backend/tests/test_desk_coverage.py` (8 tests),
  `apps/backend/tests/test_desk_topup_compute.py` (17 tests).
- The `README.md` hunk in the raw diff is NOT this iteration's work: it documents J-01 (fetch/
  registry) capability prose and is already committed on `HEAD` (`c04d282 chore(goal): iter 1
  showcase artifacts`), which post-dates the `8448b88` snapshot commit (a dangling `WIP on goal/desk:
  57970a9` point) — a harness snapshot-timing artifact, not iter-2 product surface. No frontend,
  `app/main.py`, `app/meta.py`, or `routes.py` diff exists (confirmed via targeted `git diff` — all
  empty) — matches `Frontend Present: no` and "reuses `routes.py`, never modifies it."
- `runs/goal-session-desk/state/blueprint.md` was edited this iteration (33 lines, excluded from the
  reviewed diff as harness state per the invocation prompt) — read directly in its current form as
  the contract; it registers exactly the two new rows below.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-member bar coverage + freshness (new row, registered this iteration) | OK | Computed by `apps/backend/app/research/desk_coverage.py:39` (`get_desk_coverage`), reading `apps/backend/app/research/bar_index.py:154` (new `BarIndex.coverage()` — a single indexed `COUNT`+`MAX` query, never a `BarStore` re-hash) only. Served by `GET /research/desk/coverage` (`desk_routes.py:137`). Shipped shape matches `blueprint.md`'s registered shape field-for-field: `universe_snapshot_id`, `timeframes`, `members[].symbol`/`.per_timeframe[<tf>].has_bars`/`.latest_window_end_utc`; honest-empty (`null`/`[]`, HTTP 200) confirmed at `desk_coverage.py:50-51`. |
| Top-up compute progress (new row, registered this iteration) | OK | Computed by `apps/backend/app/research/desk_topup_compute.py:191` (`DeskTopupComputeManager`) + `:158` (`run_topup`) + `:123` (`_run_one_pair`), which calls `record_bar_series` (`desk_topup_compute.py:145`) imported from `routes.py` — the SAME fetch-and-record path `POST /research/bars` already uses; never a second implementation. Served by `POST/GET /research/desk/topup/compute` + `POST /research/desk/topup/compute/cancel` (`desk_routes.py:164/180/190`). Shipped snapshot shape matches `blueprint.md`'s registered shape field-for-field (`id`/`state`/`started_utc`/`finished_utc`/`error`/`progress.pairs_total`/`.pairs_done`/`.outcomes[]`). |
| Bar coverage index (existing, internal row) | OK — sanctioned additive extension, not a new index | `bar_index.py:154-176`'s new `coverage()` method is additive-only: `BarIndexHit`'s three fields and every existing `lookup`/`insert`/`list`/`reindex` call site are unchanged, pinned by a new regression test (`test_bar_index.py:241`, `test_bar_index_hit_still_has_exactly_its_original_three_fields`). Matches `blueprint.md`'s explicit sanction ("a NEW desk-owned READ over this same index, not a duplicate index"). |
| Universe snapshots + membership (existing row, owner unchanged) | OK | `desk_coverage.py:53` and `desk_topup_compute.py:231,358` all read membership via `UniverseStore.list()` (`desk_universe.py`, byte-unmodified this iteration) — no independent parse/recompute of membership; each site takes `records[-1]`, a trivial selection over the one canonical, correctly-sorted list. See advisory note below (DRY, not a violation). |
| Bars/candles (`bars.py`/`BarStore`) | OK — unmodified, reused | `bars.py` has zero diff. `desk_topup_compute.py` imports and calls `record_bar_series` rather than re-implementing fetch/record logic (verified at `desk_topup_compute.py:58-64` imports, `:145` call site). |
| All other registered rows (levels/zones, tradability, datasets, setups, edge report + its compute manager, pnl ledger, strategies, profiles, taxonomy, `UI_ROUTES`, `config_fingerprint`) | OK — untouched | Confirmed zero diff on their owning modules (`levels.py`, `tradability.py`, `datasets.py`, `setups.py`, `edge_report.py`, `edge_report_compute.py`, `pnl_ledger.py`, `strategies.py`, `profiles.py`, `taxonomy.py`, `app/meta.py`). `desk_topup_compute.py`'s manager mirrors `EdgeReportComputeManager`'s shape (a sanctioned pattern-copy, per spec) but is a distinct process-scoped job type for a distinct value — not a duplicate of the edge-report value. |

No new displayed value lacks a Data Contract registration: `Frontend Present: no`, so nothing is
"displayed" this iteration; both new servable values were pre-registered into `blueprint.md` in this
same iteration (the sanctioned register-before/at-ship pattern already used in iter-1), and the
shipped payload shapes were checked field-for-field against the registered shapes above — no A4/A5
gap.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature shipped in the UI this iteration)* | OK / N/A | `apps/backend/app/meta.py` diff against the snapshot SHA is empty; `UI_ROUTES` still lists exactly `/` (Cockpit) and `/structure` (Structure). `reports/phase-goal-desk-iter-2-ui-surface-map.md` states "N/A — Backend-only phase... No UI surfaces affected." No frontend file appears anywhere in the diff. |

The three new REST endpoints (`GET /research/desk/coverage`, `POST/GET /research/desk/topup/compute`,
`POST /research/desk/topup/compute/cancel`) plus the CLI warmer are backend/operator/test-callable
only this iteration — exactly what `blueprint.md`'s Feature/journey-homes table already specifies:
*"J-02 Coverage + explicit bar top-up ... — surfaced as per-row coverage/tick-evidence badges on
`/desk` — no standalone page"* (Desk section). There is no UI surface to check reachability for, so
"no navigation path" / "undiscoverable" / "duplicate home" / "parallel shell" cannot fire against a
REST-only change with a pre-planned no-page-yet home. Matches the iteration spec's own "Blueprint
conformance" field ("No new page ships this iteration... `UI_ROUTES` stays 2 rows") and "UI surface
changes: None."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **DRY, not a divergence risk today.** "Latest universe snapshot" selection (`records[-1]`) is
  independently written at four call sites — `desk_routes.py:127` (pre-existing, J-01),
  `desk_coverage.py:53`, `desk_topup_compute.py:231`, `desk_topup_compute.py:358` — instead of one
  shared `UniverseStore.latest()` accessor. All four read the SAME canonical, correctly-sorted
  `UniverseStore.list()` (`desk_universe.py`, unmodified), so no divergent value can be served today;
  this was independently confirmed empirically in `docs/handoffs/goal-desk-iter-2-audit.md` (finding
  B3: `/research/desk/universe` and `/research/desk/coverage` verified to agree on the same
  `universe_snapshot_id` over a real 101-member snapshot). Not a Data Contract violation — flagged
  only so a future iteration that touches just one of these four sites (e.g. adding integrity-error
  filtering) doesn't accidentally create a genuine divergence. A cheap, finite future cleanup:
  collapse the four into one `UniverseStore.latest()` method.
- **Freshness field is spec-conformant today; a J-04 display-wording concern, not a source-of-truth
  violation.** `desk_coverage.py`'s `latest_window_end_utc` serves the *requested* fetch-window end
  (verbatim off `bar_index`'s `window_end_utc` column, a single canonical read), not the actual last
  recorded bar — `docs/handoffs/goal-desk-iter-2-audit.md` (finding B2) shows a real example (AAPL
  `1w`: served `2026-07-25T00:00:00Z` vs. actual last bar `2026-07-20T04:00:00Z`). The shipped payload
  matches `blueprint.md`'s registered shape byte-for-byte and reads from exactly one canonical source,
  so this is not a duplicate-computation or non-canonical-source violation. Already routed by the
  project's own audit to J-04: whichever `/desk` UI badges this field must not word it as "last bar"
  or otherwise imply more freshness than the pinned timeframe actually has recorded.
