# Iteration 3 — Coherence Audit

**Iteration:** goal-desk-iter-3
**Date:** 2026-07-25
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend/CLI-only (`Frontend Present: no`, target journey J-03). `runs/goal-session-desk/iter-3/iter-diff.md`
does not exist, so the review used the exact noise-excluded `git diff 68e3adee4918943f9ffda2744c4f7f7c775a75bb`
command from the invocation prompt, plus direct reads of the untracked new production/test files
(git does not diff untracked files):

- Modified (tracked): `apps/backend/app/research/desk_routes.py` (+112 lines: four new routes —
  `GET /research/desk/screen`, `POST/GET /research/desk/screen/compute`,
  `POST /research/desk/screen/compute/cancel` — plus docstring/import updates; every pre-existing
  J-01/J-02 handler body is byte-unchanged, confirmed by both my own read and
  `docs/handoffs/goal-desk-iter-3-audit.md`'s independent diff check), `README.md` (a showcase-prose
  catch-up bullet for J-02's coverage/top-up capability — outside the blueprint's IA/Data-Contract
  scope this gate audits; no bullet for J-03 itself was added, since this iteration's own spec states
  "No new user-facing capability... Product surface delta: None visible to an end user").
- New (untracked, production): `apps/backend/app/research/desk_screen.py` (`ScreenStore`,
  `compute_screen`, `resolve_desk_screen_dir`), `apps/backend/app/research/desk_screen_compute.py`
  (`DeskScreenComputeManager`, `run_screen_and_record`, CLI `main()`).
- New (untracked, tests/fixtures): `apps/backend/tests/test_desk_screen.py`,
  `apps/backend/tests/test_desk_screen_compute.py`, two real-vendor MSFT bar fixtures (partial
  1h/1d-only coverage, for TC-2's honest-partial-coverage case).
- `runs/goal-session-desk/state/blueprint.md` already carries the two new Data-Contract rows below
  (registered at spec-write time, the iter-1/iter-2 precedent) — read directly as the contract; the
  shipped payload shapes were checked field-for-field against it.
- Confirmed zero diff (via the stat of the noise-excluded diff, which lists only `README.md` and
  `desk_routes.py`) on every file the spec names as frozen: `config.py`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `desk_universe.py`, `desk_coverage.py`,
  `desk_topup_compute.py`, `routes.py`, `main.py`, `meta.py`, `mcp/__init__.py`. Independently
  reconfirmed post-audit-fix in `docs/handoffs/goal-desk-iter-3-audit.md` ("git diff HEAD numstat = 0
  lines on" the same 12 files) and `Config().config_fingerprint()` unchanged at
  `08e471b10130e1e2`.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows, skip rows (new row, registered this iteration) | OK | Computed by `apps/backend/app/research/desk_screen.py:251` (`compute_screen`, the sole walker — both the compute manager `desk_screen_compute.py:91` and the CLI `desk_screen_compute.py:266` call this same function, never a second implementation). Served by `GET /research/desk/screen` (`desk_routes.py:141`). Shipped shape matches `blueprint.md`'s registered shape field-for-field: snapshot `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature, created_utc, rows, skipped}`, ranked row `{symbol, side, band_class, distance_bps, band_score, price_low, price_high, coverage, tick_evidence}`, skip row `{symbol, skipped, reason, coverage, tick_evidence}`; list response meta-only (`desk_routes.py:123-137`, `_screen_meta_only`) vs. `?date=` full-snapshot read (`desk_routes.py:150-153`, a plain lookup, never recomputed on GET) — both exactly as specified. Honest-empty `{"screens": [], "latest": null, "integrity_errors": []}` at `desk_routes.py:154-158` (HTTP 200, never 404, matching the `GET /research/desk/universe` convention already in use at `desk_routes.py:144`). |
| Screen compute progress (new row, registered this iteration) | OK | Computed by `apps/backend/app/research/desk_screen_compute.py:116` (`DeskScreenComputeManager`). Served by `POST/GET /research/desk/screen/compute` + `POST /research/desk/screen/compute/cancel` (`desk_routes.py:178/196/206`). Snapshot shape (`id/state/screen_date/started_utc/finished_utc/error/progress.members_total/.members_done/.current`) matches the registered shape verbatim. `screen_date` is REQUIRED in the trigger body (`ScreenComputeRequest` at `desk_routes.py:161-166`, Pydantic — a missing field 422s before the handler runs, TC-9); never defaults to a wall-clock date. |
| Bands / tradable-map scores (`tradability.py`) | OK — reused verbatim, zero diff | `compute_screen` calls `compute_tradability` directly (`desk_screen.py:298`), not through the REST-serving `TradabilityCache`. This is a deliberate, logged choice (`desk_screen_compute.py:21-36` docstring), not a divergent second computation: it is the identical canonical function (`tradability.py:381`), same inputs, so its output is byte-identical to what `GET /research/tradability` serves for the same `(symbol, as_of)` — proven directly by TC-1's cross-check against the real endpoint through `TestClient` (confirmed executed and passing per `docs/handoffs/goal-desk-iter-3-audit.md`'s "Domain Assessment" section, which also verified the `TradabilityCache` key can never disagree with a direct call). `git diff` on `tradability.py` is empty (TC-19's own requirement). |
| Per-member bar coverage + freshness (`desk_coverage.py`) | OK — reused verbatim | `compute_screen` calls `get_desk_coverage(universe_store, bar_index)` once per screen (`desk_screen.py:282`) and reuses its per-member `per_timeframe` block for every row's `coverage` field (`desk_screen.py:296,303,308,322`) — never a second coverage derivation. TC-12's byte-identity requirement is met by construction (same dict, not re-derived). |
| Bar coverage index / `bar_store_signature` (T-4) | OK — index-only, never a `BarStore` re-hash | `_bar_store_signature` (`desk_screen.py:172-182`) takes only an already-fetched `coverage: dict` — no store handle is passed in, so it is structurally incapable of issuing a `BarStore` call. Enforced by an instrumented regression test (`apps/backend/tests/test_desk_screen.py:125`, `test_bar_store_signature_issues_zero_bar_store_calls`, monkeypatching `BarStore.list`/`.get`). |
| Datasets (tick evidence) | OK — reused verbatim | `compute_screen` reads tick-evidence presence via `dataset_store.list()` (`desk_screen.py:286-287`, `DatasetStore.list`, unmodified) — a plain membership check, not a re-derivation of dataset content. |
| Bars/candles (`bars.py`/`BarStore`) | OK — unchanged; reference-close read is not a new bar computation | `_resolve_reference_close` (`desk_screen.py:227-245`) reads the one daily bar at `basis_as_of` via `BarStore.merged_bars(symbol, "1d")` — the same accessor `tradability.py` already calls internally — and never touches `tradability.py`'s or `levels.py`'s return shape (TC-19, zero diff confirmed). This resolves a genuinely new desk-owned value (`distance_bps`'s reference close), not a duplicate of an existing registered value; it is registered as part of the new "Screen snapshots..." row above, not a separate unregistered value. |
| `config_fingerprint` | OK — unchanged, zero new `Config` field | `resolve_desk_screen_dir` (`desk_screen.py:113-124`) takes a plain string and resolves via a bare `TAPEOLOGY_DESK_SCREEN_DIR` env var or a sibling-of-the-universe-dir default — never touches the `Config` class. `git diff` on `config.py` is empty; `Config().config_fingerprint()` is unchanged at `08e471b10130e1e2` (re-verified post-fix in the audit handoff). |
| All other registered rows (levels/zones, edge report + its compute manager, pnl ledger, strategy registry, profiles, taxonomy, `UI_ROUTES`, universe snapshots) | OK — untouched | Zero diff on every owning module, confirmed by the stat above and independently by the audit handoff. |

No new displayed value lacks a Data Contract registration: `Frontend Present: no`, so nothing is
"displayed" in the UI this iteration; both new servable values were pre-registered into
`blueprint.md` at spec-write time (the sanctioned register-before-build pattern already used in
iter-1/iter-2), and the shipped payload shapes were checked field-for-field against the registered
shapes above — no A4/A5 gap. One additive field beyond the registered shape,
`integrity_errors` on the no-`?date=` `GET /research/desk/screen` response (`desk_routes.py:157`),
is not a new "value" in the coherence sense (it is store-integrity diagnostic metadata, not a
business value that could diverge across pages) and exactly mirrors the existing, unmodified
`GET /research/desk/universe`'s own `integrity_errors` field (`desk_routes.py:144`) — a consistent
reuse of an established pattern, not an invented one.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature shipped in the UI this iteration)* | OK / N/A | `apps/backend/app/meta.py` diff against the snapshot SHA is empty; `UI_ROUTES` still lists exactly `/` (Cockpit) and `/structure` (Structure) — confirmed live in the audit handoff's Frontend Findings ("zero frontend files touched... `UI_ROUTES`/`meta.py` carry zero diff"). `reports/phase-goal-desk-iter-3-ui-surface-map.md` states "N/A — Backend-only phase... No UI surfaces affected." No `apps/frontend/` file appears anywhere in `git status` or the diff. |

The four new REST endpoints (`GET /research/desk/screen`, `POST/GET /research/desk/screen/compute`,
`POST /research/desk/screen/compute/cancel`) plus the CLI warmer are backend/operator/test-callable
only this iteration — exactly what `blueprint.md`'s Feature/journey-homes table already specifies:
*"J-03 Screen compute + append-only ledger | (backend POST/CLI compute; served to `/desk`) | Desk"*.
There is no UI surface to check reachability for, so "no navigation path" / "undiscoverable" /
"duplicate home" / "parallel shell" cannot fire against a REST-only change with a pre-planned
no-page-yet home. Matches the iteration spec's own "Blueprint conformance" field ("No new page ships
this iteration... no nav-skeleton change") and "UI surface changes: None."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Growing DRY pattern, still not a divergence risk.** "Latest universe snapshot" selection
  (`records[-1]`) now has independent call sites in `desk_screen.py:279-280` (`compute_screen`) and
  `desk_screen_compute.py:157` (`DeskScreenComputeManager.trigger`, for `members_total`), on top of
  the four already flagged in iter-2's coherence audit (`desk_routes.py`, `desk_coverage.py`,
  `desk_topup_compute.py` ×2). All six read the SAME canonical, correctly-sorted
  `UniverseStore.list()` (`desk_universe.py`, unmodified), so no divergent value can be served today.
  This iteration's own spec explicitly pre-acknowledged this ("a 5th `records[-1]` call site here is
  acceptable (advisory-only finding)" — OUT OF SCOPE section), carrying forward iter-2's deferred
  cleanup. Repeating the note here only so the count (now six) stays visible for whichever future
  iteration collapses them into one `UniverseStore.latest()` accessor.
- **Best-band selection is a logged product-judgment call, not a coherence violation.**
  `docs/handoffs/goal-desk-iter-3-audit.md` (finding B10) documents that `_select_best_band`
  (`desk_screen.py:206-215`) ranks distance-to-close ahead of quality score, so a symbol's headline
  row can be a lower-score, nearer band rather than the map's strongest same-class band. This is
  spec-conformant (the exact tuple `assumptions.md` iter-3 entry 1 logged) and reads its inputs from
  the single canonical `compute_tradability` output — not a duplicate computation or a non-canonical
  source — so it is out of this gate's scope. Flagged only so the next decomposer sees it before
  J-04 renders these rows on `/desk`.
