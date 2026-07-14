# goal-tradable_wall-iter-1 Execution Plan

Era 5B "The Tradable Wall", iteration 1: build **J-01 alone** (the natural unblocker per the
iter-0 baseline's recommendation) — the tradable level map. Backend + API + MCP only; no UI this
iteration (J-05 renders it later). Depth: full.

## What to Build

- **`apps/backend/app/research/tradability.py`** (new module, sole owner of the tradable level
  map): consumes `compute_levels(store, symbol, resolved_as_of_epoch, config)` output **verbatim**
  (never re-detects pivots/extremes, never touches `levels.py`'s 5 bps / 20 bps parameters). Reads
  bars only for (a) price-scale context for band-width sizing and (b) morning-markup as-of
  resolution.
- **Morning-markup as-of resolution**: for a requested `as_of` inside a session, derive the basis
  from the stored **daily (`1d`)** bar series — the last completed daily bar strictly before the
  requested session — and pass that resolved epoch into `compute_levels`. No hardcoded calendar
  (this is how the 2026-06-19 holiday gets skipped for free). No session-calendar helper exists
  today (confirmed by grep) — this is genuinely new correctness-bearing code, the reason this
  iteration is depth=full.
- **Band clustering**: group raw levels into price bands per side (support / resistance) using a
  config-owned, price-scale-aware band width; cap at **K ≤ 5 bands per side** (config-owned), so
  ≤10 bands total.
- **Quality scoring**: config-owned factors — distinct-timeframe breadth, daily touch count,
  recency, round-number confluence (config-owned round-number rule; 300 must be flagged).
- **Class inheritance**: each band's A/B/C class is a projection of its best member zone (class
  stays owned by `levels.py` — no re-grading here).
- **Determinism + honesty**: byte-identical output on identical input (stable sort/tie-break, no
  wall-clock/randomness); explicit empty map for a symbol with no bar series or nothing derivable
  at the resolved as-of (never a fabricated band).
- **Config additions** (`apps/backend/app/config.py`): named constants for band cap K,
  band-width scaling, quality-score weights, round-number rule — added to the
  `config_fingerprint` **exclusion set** (the `sr_pivot_lookback` / `sr_confluence_band_bps`
  precedent at config.py:1494-1518), pinned by a fingerprint-stability test **plus** a
  real-threshold counter-test (the established paired-test pattern). Exact weight/rule values are
  the developer's config-owned design freedom — the spec is explicit this is not an ambiguity to
  ask about.
- **`GET /research/tradability?symbol=&as_of=`** (`apps/backend/app/research/routes.py`):
  mirrors `get_levels` exactly (routes.py:1780-1798) — parse the ISO `as_of` to epoch once at the
  route boundary, 422 on missing `symbol` or malformed `as_of` (never a silent "now" default),
  return the module's output verbatim as `{"symbol", "as_of", ...}`.
- **Read-only MCP proxy `tradability`** (`apps/backend/app/mcp/__init__.py`): mirrors the
  existing two-required-param `levels` tool exactly (`_LEVELS_TOOL`/`_LEVELS_PATH` constants at
  lines 107-108, the `_request_path` branch at lines 309-316, the tool schema at lines 190-209) —
  thin verbatim `httpx` GET passthrough, body byte-identical to the REST response.
- **Test data (the central risk — read carefully):** the only committed AAPL fixtures today
  (`tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json`, 3 daily bars, and
  `AAPL_1h_20260601_20260603.json`, 15 hourly bars) cover **2026-06-01 through 06-04 only** — they
  do **not** contain the pinned rejection cluster (300.75 / 300.48 / 302.07 / 300.57 around
  2026-06-18–22) that J-01's acceptance criteria require. A new or extended committed real-AAPL
  fixture (same pattern as the existing pair — real, frozen Yahoo JSON, committed under
  `tests/fixtures/yahoo/`) covering enough daily history through the 2026-06-18 close (and its
  antecedent swing/prior-period structure) is required so `compute_levels` on the fixture produces
  a genuine resistance zone spanning 300.48–302.07 for the unit/integration tests to assert
  against deterministically in CI. This dev environment's live `.data/bars` already holds the real
  fetched AAPL series that reproduces goal.md's cited 1,800-level/212-zone numbers exactly (per
  the iter-0 baseline's live probe) — the developer should use that as the source to freeze a
  fixture slice from, following the `test_levels_api.py` "committed real PG bar-fixture pair"
  precedent, rather than fabricating synthetic prices.
- **Tests**: new `tests/test_tradability.py` (pure-function unit tests, mirrors
  `tests/test_levels.py`'s style) + new `tests/test_tradability_api.py` (route-integration tests
  on the AAPL fixture, mirrors `tests/test_levels_api.py`) + additions to
  `tests/test_mcp_server.py` (REST==MCP byte-identity + required-args validation, mirrors the
  existing `levels` tool tests at lines 296-378). Cover every DEFINITION OF DONE / TESTING
  REQUIREMENTS bullet in the phase spec (see Key Test Scenarios below).
- **Dev handoff** at `docs/handoffs/goal-tradable_wall-iter-1-dev.md`.

No `blueprint.md` edit needed — the Data Contract row and `/structure` → Tradable Map home are
already drafted there; nav is frozen for Era 5B.

## Agents Required

- backend-data: yes -- implement `tradability.py`, the `config.py` additions (+ fingerprint
  exclusion + counter-test), the `/research/tradability` route, the MCP `tradability` proxy, the
  new/extended AAPL fixture, and the full unit/integration/MCP test suite; run the full backend
  suite + equivalence tests + live `config_fingerprint` check before handoff (J-07 sentinel).
- frontend-ux: no -- backend + API + MCP only this iteration.

## Frontend Present

Frontend Present: no

(Matches the phase spec's Goal Mode Metadata exactly. UI pipeline stages — ui-impact-analyst,
ui-test-designer, browser-qa-agent, ux-regression-reviewer — are N/A-stubbed. QA + the
goal-evaluator verify J-01 via live REST + MCP probes instead of a browser.)

## Files to Create/Modify

- `apps/backend/app/research/tradability.py` -- NEW. Sole owner of the tradable-map computation
  (band clustering + quality scoring + morning-markup as-of resolution), consuming `compute_levels`
  verbatim.
- `apps/backend/app/config.py` -- ADD named constants (band cap K, band-width scaling,
  quality-score weights, round-number rule) near the existing `sr_*` fields (~line 1098-1180); ADD
  each to the `config_fingerprint` exclusion set (~line 1494-1518 block).
- `apps/backend/app/research/routes.py` -- ADD `GET /research/tradability` route mirroring
  `get_levels` (line 1780); import `compute_tradability` (or equivalent) from `.tradability`.
- `apps/backend/app/mcp/__init__.py` -- ADD the `tradability` tool definition to `TOOLS` +
  `TOOL_NAMES`, and a two-required-param branch in `_request_path` mirroring `_LEVELS_TOOL`
  (lines 107-108, 309-316).
- `apps/backend/tests/fixtures/yahoo/` -- ADD or EXTEND a committed real-AAPL fixture covering
  through the 2026-06-18 close (see Test data note above).
- `apps/backend/tests/test_tradability.py` -- NEW. Pure-function unit tests mirroring
  `test_levels.py`, including the fingerprint-stability test + real-threshold counter-test (the
  `test_sr_config_fields_are_excluded_from_config_fingerprint` precedent at test_levels.py:644 —
  there is no separate `test_config.py`; this convention lives in the feature's own test file).
- `apps/backend/tests/test_tradability_api.py` -- NEW. Route-integration tests on the AAPL
  fixture (exact band values, 422s, honest-empty states) mirroring `test_levels_api.py`.
- `apps/backend/tests/test_mcp_server.py` -- MODIFY. Add `tradability` tool tests mirroring the
  existing `levels` tool tests (lines 296-378).
- `docs/handoffs/goal-tradable_wall-iter-1-dev.md` -- NEW. Dev handoff.

## Explicitly Out of Scope (per phase spec — do not build)

No touch-event scanner/`setups.py` (J-02); no credentialed recording/`record_from_source`
invocation (J-03); no `structure_tape_map` strategy or `edge_report.py` changes (J-04); no
`/structure` UI changes of any kind — no Tradable Map view, no raw-levels toggle, no Case
Studies/Edge Report sections (J-05); no cockpit `PriceChart`/band overlay/chip changes (J-06); no
edit to `levels.py` or its frozen 5 bps/20 bps parameters; no 12-symbol panel config constant
(belongs to J-02); no champion/promotion/sweep/nav changes; `config_fingerprint` must NOT change.

## Key Test Scenarios

- `GET /research/tradability?symbol=AAPL&as_of=<instant inside 2026-06-22 session>` returns **≤10
  bands total** (≤5 per side); a **resistance band containing both 300.48 and 302.07** (round-number
  300 flagged) ranks in the **top 2** resistance bands by quality score.
- The map derives from **no bar newer than the 2026-06-18 close** — assert no member/basis
  timestamp exceeds it; the 2026-06-19 holiday is skipped (basis resolves to 06-18, not 06-19).
- No-lookahead: shifting the requested `as_of` earlier within the same session never pulls a bar
  past the prior-session close into the map, and never changes an already-emitted band from a
  strictly-later request in a lookahead-revealing way.
- **Repeat-call determinism**: two identical requests return byte-identical JSON.
- **REST == MCP**: the `tradability` MCP proxy body is byte-for-byte equal to the REST response
  body for the same params.
- **Frozen levels**: `GET /research/levels?symbol=AAPL&as_of=...` output is byte-identical to
  before.
- `config_fingerprint` == `4d665603569b9dbf` (live-confirmed); fingerprint-stability test +
  real-threshold counter-test both pass.
- Reviewer/auditor confirm `tradability.py` is a **lens, not a second levels engine**: no
  pivot/extreme detection, no second levels computation — consumes `compute_levels` output only.
- Error cases: missing `symbol` -> 422; malformed `as_of` -> 422 (no silent "now" default); symbol
  with no bar series -> explicit empty map; symbol with series but no derivable bands at the
  resolved as-of -> explicit empty bands (never fabricated).
- **J-07 regression sentinel**: full backend suite green (no test deleted/weakened, baseline was
  1201 passed / 6 skipped / 1207 collected per the iter-0 handoff); `test_observer_equivalence.py`
  (7/7) and `test_profile_equivalence.py` (15/15) stay green; `v1`/`structure_tape`/`default`/the
  champion pointer/the JSON `BarStore`/the Alpaca adapter/the recorder all byte-identical on
  identical inputs; era-1–5 surfaces unaffected.
