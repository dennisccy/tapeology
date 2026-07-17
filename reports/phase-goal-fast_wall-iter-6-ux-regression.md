# Phase goal-fast_wall-iter-6 — UX Regression Review

**Date:** 2026-07-17

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

There is no new capability to assess this iteration. Independently verified via direct `git status
--short -- apps/frontend/` and `git diff --stat HEAD -- apps/frontend/` against the working tree
(both empty) — not merely taken on the artifacts' word. The actual uncommitted diff touches exactly
six files, all backend: `apps/backend/app/research/setups.py` (modified), `apps/backend/tests/
conftest.py` (modified), `apps/backend/tests/test_setups.py` (modified), `apps/backend/tests/
test_setups_api.py` (modified), `apps/backend/app/research/setups_scan_cache.py` (new),
`apps/backend/tests/test_setups_scan_cache.py` (new). Every one of `plan.md`, the phase spec's UI
Evolution section, `user-visible-changes.md`, and `ui-surface-map.md` independently states "none
new" / "zero frontend files changed" — all four agree with the git evidence.

`Frontend Present: yes` is set for a documented reason unrelated to new UI: it forces the UI Impact
/ UI Test Design / Browser QA / UX Regression lanes to re-verify the EXISTING `/structure` page
against this iteration's backend caching change, not because a new capability was built. This
mirrors iter-5's identical framing for the sibling `EdgeReportBacktestCache` work. There is
therefore nothing to score against the "1-click / 2-click / hidden" discoverability rubric — the
skill's Discoverability Assessment step is correctly a no-op this iteration, not a gap.

## Regression Risk

Frontend code carries **zero** regression surface (byte-identical file tree, confirmed above). The
risk instead runs through the one shared **backend** function this iteration rewired —
`compute_setups` in `setups.py` — which is read by two prior-shipped UI features on the same
`/structure` page:

| Shared component | Prior feature it serves | This iteration's change | Risk level | Verified how |
|---|---|---|---|---|
| `compute_setups` (`setups.py`) via `routes.py:1945` (`list_setups`) / `:1967` (`get_setup`) | Case Studies panel + drill-in — built `goal-tradable_wall-iter-6` (era 5B): the registry table, symbol/reaction filters, and row-click drill-in with tape timeline (testids `case-studies-*`, `case-drillin*`) | Cache key changed from `(id(config), _store_signature(store))` to `(config_content_hash, _store_signature(store))`; three-tier lookup (hot slot → durable `SetupsScanCache` → full scan) replaces the old two-tier one | High exposure (this function is the panel's entire data source) — mitigated to Low residual risk: `compute_setups`'s served shape (`{"events": [...]}`) is unchanged by construction (only the caching layer underneath it changed), backed by byte-identity tests TC-1/TC-2/TC-5 (`json.dumps(sort_keys=True)` equality across restart-simulation, content-equal-object, and cache-deletion scenarios) and the non-vacuous mutation probe TC-6 (a durable row pre-seeded with a deliberately WRONG payload is returned verbatim — proving the durable-hit path is genuinely read, not silently bypassed) | Pytest byte-identity (TC-1/2/5/6, `test_setups.py`); browser `UT-02` (honest-empty render intact) and `UT-05` (survives a broken/read-only durable cache, no crash, no error surfaced, reload reproduces identically) |
| `compute_setups` via `edge_report.py:582`/`:932` (`run_strategy_comparison_report`) | Edge Report panel — not-computed state built `goal-fast_wall-iter-1`, "Compute edge report" button/progress/failed-state built `goal-fast_wall-iter-4` (testids `edge-report-*`) | Same keying/tiering change as above, reached indirectly (Edge Report resolves each dataset's touch events by calling `compute_setups` internally, twice) | Medium-High exposure (central to J-04's compute workflow) — mitigated: `edge_report.py`/`edge_report_compute.py`/`edge_report_cache.py` method bodies and `edge_report_backtest_cache.py` are git-confirmed byte-unchanged this iteration (only `_config_content_hash` reused via import, never re-derived) | Browser `UT-J-04`: full click-through (`edge-report-compute-button` → `POST /research/edge-report/compute` 200 → poll 200 → re-fetch 200 → frozen `edge-report-empty` text byte-matched) with zero console errors; keyless `UT-J-05` plus the required-still-passing regression pass (J-01/J-04/J-05 all reported PASS); full suite 1544 passed / 0 failed |
| `apps/backend/tests/conftest.py`'s autouse fixture (now also resets `setups.py`'s hot slot) | Test isolation infrastructure only | No production code path — test-only | None | N/A (no user-facing surface) |

**Confirmed zero risk (git-verified untouched) to:** `levels.py` / `tradability.py` / `backtests.py`
— feeding the Tradable Map, Registry (champion + `v1`/`structure_tape`/`structure_tape_map` cards),
and Comparison sections (era-4/5B features) — and `bars.py` / `datasets.py` / `dataset_index.py` —
feeding the store-read path underneath Tradable Map. All were re-loaded during this iteration's
browser pass (`UT-01`, `UT-04`) purely as regression sentinels and rendered identically to the
iter-5 baseline (exact same 6 section headings in order, exact same champion/3-strategy-card
Registry, exact same Comparison dropdown options). Navigation itself (top nav bar, `Sidebar`/
`Nav`/`App.tsx`-equivalent, router config) is untouched by construction (zero frontend diff) — no
navigation-integrity check is needed beyond that confirmation. The separate `/studies` route is
unrelated to this iteration entirely: direct grep (recorded in `user-visible-changes.md`) confirms
it never calls `GET /research/setups`/`GET /research/setups/{id}`, so it carries no shared-component
exposure from this iteration's diff at all — correctly excluded from this iteration's own browser
verification.

**One honest, carried-forward verification gap, not a new regression:** the scoped/keyless browser
fixture used for `UT-02`/`UT-05`/`UT-J-04` has an intentionally empty bar directory, so none of this
iteration's browser evidence could exercise the *populated* Case Studies table, the drill-in panel,
or populated Edge Report cells — only the honest-empty states. This has been true of every iteration
in this interlude since iter-0 (documented at iter-0, iter-4, and iter-5 alike) and is not specific
to or worsened by iter-6. It is well-mitigated for the specific risk that matters to a UX reviewer
(does the durable-hit path serve stale/wrong/divergent data to a real user) by TC-6's non-vacuous
mutation probe, which is purpose-built to catch exactly that failure mode at the unit level since the
browser leg structurally cannot on this fixture.

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure | Assessment |
|---|---|---|
| `SetupsScanCache` — durable, restart-surviving SQLite cache for `compute_setups`, content-hash keyed | None — no badge, timestamp, or "served from cache" indicator anywhere; the only externally observable signal is load latency, which the product does not display as a number | Appropriate, not a gap. This is a robustness/performance change to an existing computation, not a new capability requiring a new element — explicitly out of scope per the phase spec ("Any new `/structure`/`/studies` UI element, nav entry, or page... None planned"). Matches the interlude's own established precedent: J-02's stat-keyed store cache, J-03's arm memo, and J-05's `EdgeReportBacktestCache` are all equally UI-invisible durable accelerators, and iter-5's own UX-regression review explicitly validated that exact "intentionally backend-only — correctly documented" carve-out for J-05's sibling cache |
| `TAPEOLOGY_SETUPS_CACHE_DB` env var (new, optional path override) | None — deployment/operator-level configuration only | Consistent with every other cache-path env var in this codebase (`TAPEOLOGY_EDGE_REPORT_CACHE_DB`, `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`, `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DATASET_DIR`) — none are surfaced in the UI. Not a parity gap |
| Content-hash keying replacing `id(config)` (TC-2/TC-3) | None directly, but removes a class of "occasional unneeded re-scan even without a restart" a user could previously have experienced as unexplained slowness | Correctly framed in `user-visible-changes.md` as an invisible reliability improvement, not withheld or mis-described as a user-facing feature |

`implementation-summary.md`'s "Backend-Only Items: None" and `user-visible-changes.md`'s "Not
Visible Yet" section are mutually consistent — neither describes this work as a "complete" *product*
capability that the UI then fails to expose; both correctly frame it as internal caching with no
product-shape change. No contradiction to flag.

## Flags

### Hidden Capabilities
None. No new capability shipped this iteration to hide.

### Undiscoverable Capabilities
None. The two pre-existing UI surfaces that read through the changed function (Case Studies panel,
Edge Report panel) were both already discoverable before this iteration (confirmed again this
iteration via `UT-07`: "Structure" nav link visible with no login, Case Studies reachable by one
scroll at 827px into a 1252px viewport) and this iteration changes neither their location nor their
labels.

### Potential Regressions
None confirmed. The one function this iteration rewired (`compute_setups`) is read by two
prior-shipped UI features (Case Studies/drill-in from `tradable_wall`-iter-6; Edge Report from
`fast_wall`-iter-1/iter-4); both were exercised this iteration (browser + keyless-pytest) and both
returned byte-identical served shapes with zero visual or functional change. Full backend suite
green (1544 passed / 7 skipped / 0 failed, up from iter-5's 1517 by exactly the 27 net-new tests
this iteration added). The two source-introspection guard tests protecting `setups.py`'s frozen
discipline (`test_compute_setups_itself_never_touches_the_dataset_store`,
`test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`) both pass
byte-unmodified.

### Visual Consistency
Zero frontend diff this iteration — there is no new page or element to check against DESIGN SYSTEM
tokens. `UT-01`'s full-page screenshot and `UT-04`'s section-order/content check both confirm every
`/structure` section (Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry,
Comparison) renders in the same dark slate/amber terminal-dense visual language established across
prior eras, with no new color, spacing, or effect introduced — consistent with the phase spec's
explicit "no new visual language" Design Direction.

## Recommendation

No action required. This iteration correctly matched its own stated scope: zero new frontend
surface for zero new user-facing capability, and the one shared backend function it rewired
(`compute_setups`) was regression-tested against both of its downstream UI consumers (Case Studies
and Edge Report) at three independent levels — byte-identity/mutation-probe unit tests, an HTTP-level
publish-failure test, and a live browser pass — with zero divergence found.

One non-blocking note, carried forward from iter-5's own report and now more durable since this is
the interlude's closing iteration: no iteration in "The Fast Wall" (iter-0 through iter-6) has ever
browser-verified the *populated* Case Studies table, its drill-in panel, or populated Edge Report
cells, because the mandated keyless fixture's bar directory is always empty. This is a structural
fixture limitation, not a product gap, and the byte-identity/mutation-probe test discipline
(TC-1/TC-2/TC-5/TC-6) directly covers the specific risk a UX reviewer would otherwise worry about
(served data quietly diverging). If a future iteration or the goal-proposer ever stands up a
populated-corpus scoped fixture for browser QA, adding one populated-state screenshot for Case
Studies/drill-in would close this long-standing verification gap — but it does not block this
iteration or this interlude's closure.
