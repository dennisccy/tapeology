# goal-tape_to_profit_support_resistence-iter-2 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-2
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## What Was Built

J-02 — deterministic, lookahead-free support/resistance levels, the first structural read on top
of iter-1's multi-timeframe bar store, built end to end per the plan's own directive (mirroring
`research/bars.py`'s module discipline, the `/bars` route trio's validation style, and the `bars`
MCP tool's dispatch pattern):

- **`research/levels.py`** — NEW module, the sole computer of S/R levels. Two deterministic,
  config-owned detectors, both filtered to `ts <= as_of` BEFORE any windowing/period analysis runs
  (the lookahead-free invariant):
  - **Swing pivots** — a bar's high (or low) that is the STRICT extreme over its ±`sr_pivot_lookback`
    neighbours (a tie is not a pivot — deterministic, no arbitrary tie-break). Applied to EVERY
    stored series regardless of timeframe.
  - **Prior-period extremes** — a completed period's high/low/close, applied ONLY to series whose
    timeframe is `1d`/`1w`/`1mo` (goal.md's long-term bucket). A period counts as "prior" (closed)
    only once its end (`bar.epoch + period_seconds`) is at or before `as_of` — so a day's H/L/C
    become referenceable starting exactly at the FOLLOWING day's as-of, never earlier.
  - Every level carries `price`, `timeframe`, `type` (`swing-pivot` | `prior-period-extreme`),
    `touch_count` (bars whose high/low come within `sr_touch_tolerance_bps` of the price; the
    originating bar always counts), and `strength = sr_timeframe_weights[timeframe] * touch_count`.
  - `compute_levels(store, symbol, as_of_epoch, config)` groups the symbol's matching series by
    timeframe (most-recently-created wins if more than one series ever shares a pair — `BarStore`
    has no symbol+timeframe accessor, only `list`/`get`/`load_bars`), runs both detectors, sorts by
    `(timeframe, price, type)` for byte-identical output, and returns
    `{"levels": [...], "no_bar_series_for_symbol": bool}`.
- **Config** (`config.py`): `sr_pivot_lookback` (int, default 1), `sr_touch_tolerance_bps` (float,
  default 5.0), `sr_timeframe_weights` (dict, one entry per `bar_timeframes` value, ordinally
  increasing with timeframe length). All three added to `config_fingerprint()`'s `excluded` set
  (rationale: levels are a research computation never stamped with/compared across a
  `config_fingerprint` anywhere, unlike the tape/backtest/PnL/thesis-verdict pipeline that
  fingerprint protects) — the pinned `default` fingerprint stays `"4d665603569b9dbf"`.
- **Route** (`research/routes.py`): `GET /research/levels?symbol=<S>&as_of=<ISO-T>`, reusing the
  existing `get_bar_store()` dependency. Empty `symbol` → 422; malformed/missing `as_of` → 422
  (missing is FastAPI's own required-query-param 422; malformed is a caught `parse_utc_epoch`
  `ValueError`). Serves `compute_levels`' output verbatim, with `symbol` (normalized upper-case)
  and the raw `as_of` string echoed alongside it. `classes` (J-03 confluence) is deliberately
  ABSENT this iteration — additive-only, no breaking change when J-03 adds it.
- **MCP** (`mcp/__init__.py`): a `levels` tool — the first tool needing TWO required query params,
  so it gets its own dedicated branch in `_request_path` (a `_LEVELS_TOOL`/`_LEVELS_PATH` pair)
  rather than reusing the no-arg `_STATIC_PATHS` or the single-ticker `_TAPE_PATHS` shape. Raises
  `ToolArgumentError` before any HTTP call if `symbol` or `as_of` is missing/empty. Byte-identical
  proxy of `GET /research/levels`, added to `TOOLS` right after its `bars` sibling.

## Files Changed

- `apps/backend/app/research/levels.py` -- NEW: the S/R level-detection module (swing pivots,
  prior-period extremes, touch-count/strength, `compute_levels` entry point)
- `apps/backend/app/config.py` -- `sr_pivot_lookback`, `sr_touch_tolerance_bps`,
  `sr_timeframe_weights`; all three excluded from `config_fingerprint`
- `apps/backend/app/research/routes.py` -- `GET /research/levels` (reuses `get_bar_store()`)
- `apps/backend/app/mcp/__init__.py` -- `levels` tool (`_LEVELS_TOOL`/`_LEVELS_PATH` dispatch
  branch + `types.Tool` entry); module docstring updated to mention the new tool
- `apps/backend/tests/test_levels.py` -- NEW: module unit tests. Two synthetic fixtures (a 6-bar
  `4h` series engineered for an exact `touch_count == 2` case; a 3-bar `1d` series isolating the
  period-closing gate) plus the committed PG fixture (exact swing-pivot/prior-period values,
  lookahead-free proof via a physically-truncated store vs the full store, byte-identical
  determinism, honest empty states, no-magic-numbers introspection, fingerprint exclusion)
- `apps/backend/tests/test_levels_api.py` -- NEW: route-level integration tests (happy path via a
  real `POST /research/bars` → `GET /research/levels` round trip, symbol case normalization, the
  three honest states, the 422 matrix)
- `apps/backend/tests/test_mcp_server.py` -- `levels` added to `EXPECTED_TOOLS` (positioned after
  `bars`); the tool-argument allowlist assertion extended to include `symbol`/`as_of`; `levels`
  added to the `args_for` map in the backend-down test; two new tests
  (`test_levels_tool_byte_identical_on_a_non_empty_live_result`,
  `test_levels_tool_requires_both_arguments`)

`git diff -- apps/frontend/` is **empty** — confirmed no frontend file was touched.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=/tmp/junit.xml`
Result (JUnit XML totals): **1095 passed, 1 skipped, 1096 collected, 0 failed, 0 errors**, 364.49s.
The single skip is the same pre-existing gated live-socket test
(`tests/test_live_integration.py`) noted in the iter-0/iter-1 baseline. Up from iter-1's baseline
of 1069 passed / 1070 collected — **+26 new tests** (15 in `test_levels.py`, 9 in
`test_levels_api.py`, 2 in `test_mcp_server.py`), **zero regressions.**

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py tests/test_real_data_gate.py -v`
Result: **57 passed** (7 + 15 + 35 — identical counts to iter-1's handoff; the J-07 byte-identical-
`default` guard, the pinned-fingerprint test, and the vendor-confinement gate are all unaffected).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_levels.py tests/test_levels_api.py -v`
Result: **24 passed** (15 + 9, this iteration's new module + route tests).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; assert CONFIG.config_fingerprint() == '4d665603569b9dbf'"`
Result: passes — the pinned `default` fingerprint is confirmed unchanged despite three new
`Config` fields.

## Pre-Handoff Verification

- **Service startup**: ran `bash scripts/dev.sh` twice in sequence (stop, then start again).
  Both times, backend (uvicorn on :8301) and frontend (Next.js on :3301) started cleanly with no
  errors. While manually stopping the services BETWEEN the two runs (not via the script's own
  Ctrl+C trap), a `next dev` grandchild worker process (`next-server`, not the immediate
  `npm exec`/`next dev` PID `dev.sh` reports) survived a kill of just the reported PIDs — a known
  characteristic of Next.js dev's process tree, unrelated to this iteration's diff (`dev.sh` was
  not touched). `scripts/dev.sh`'s OWN startup cleanup (the `lsof -ti :$PORT` / `fuser -k -9`
  port-based reclaim at the top of the script, before either service starts) already handles this
  correctly by killing whoever currently holds the port rather than relying on a remembered PID —
  confirmed the second `dev.sh` run bound both ports with no conflict.
- **Live smoke test** (this iteration's new capability, run against the real `dev.sh`-started
  backend, not just the test suite): seeded the committed PG fixture pair into
  `apps/backend/.data/bars/`, then hit `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z`
  over real HTTP and called the MCP `levels` tool (`app.mcp.call_tool`) against that same live
  backend via `TAPEOLOGY_API_BASE` — both returned the identical 20-level result verified in the
  test suite. Also checked the three honest-state/422 paths live: an unrecorded symbol
  (`no_bar_series_for_symbol: true`), a missing `as_of` (422), and a malformed `as_of` (422 "as_of
  must be an ISO date-time"). Seeded fixture files were removed after the check; no test data was
  left in the dev data directory.

## Known Issues

- **Touch-tolerance default (5 basis points) is a documented research starting point, not a
  validated edge** — same "RESEARCH DEFAULT, calibrated against the sims/fixtures, never a
  validated edge" discipline the existing `verdict_dwell_seconds` etc. already use. On the
  committed PG fixture it happens to produce a mix of `touch_count == 1` and `touch_count == 2`
  levels (e.g. the 1h swing-low at 148.06 and its neighbour at 148.095, 0.035 apart, are within
  each other's tolerance band; the swing-high at 149.4796 is isolated) — verified by direct
  computation, not hand-derived, and asserted exactly in `test_levels.py`.
- **A corrupted bar-series file for a symbol's ONLY series surfaces as `no_bar_series_for_symbol:
  true`, not a distinct integrity error.** `BarStore.list()` already separates a corrupted file
  into its own `integrity_errors` list (never serving it as data — the existing `bars.py`
  discipline); `compute_levels` only ever sees the healthy `records` half, so a symbol whose sole
  series is corrupted reads identically to a symbol that was never recorded at all. Neither the
  DoD nor the Testing Requirements ask for a distinct state here (only "no bar series at all" vs
  "series exist but nothing derivable" vs the 422s are specified), so this is a deliberate,
  documented scope reading rather than a gap discovered mid-fix — flagging for reviewer/auditor
  triage in case a distinct 500-style state is later wanted.
- **`sr_pivot_lookback` and `sr_touch_tolerance_bps` are single global values, not per-timeframe.**
  The phase spec names each as ONE config-owned parameter (not a per-timeframe map, unlike
  `sr_timeframe_weights`, which the spec's "per-timeframe weights" wording explicitly calls for) —
  matching that reading exactly; flagging only because a future iteration might want the pivot
  window or touch tolerance to differ by timeframe (e.g. a wider N for daily than hourly).
- **`BarStore`'s "no get-by-symbol+timeframe accessor" gap (noted in iter-1 and the plan) is
  worked around, not fixed** — `compute_levels` calls `store.list()` (every series) and filters/
  groups in `levels.py` itself. Functionally correct and tested (including the multi-series-per-pair
  "most recently created wins" case), but scans every registered series on every call; fine at the
  current fixture/committed-data scale, worth reconsidering if the bar store grows large.
- **J-03–J-06 remain unbuilt, as scoped** — no confluence zones, A/B/C classes, `structure_tape`
  strategy, class-scaled risk, or named-strategy comparison exist yet. `GET /research/levels`
  never returns a `classes` key (deliberately absent, not an empty placeholder) and
  `GET /research/strategies` still 404s. This iteration is purely the levels half of Data Contract
  row 39.
- **No frontend/UI surface** — machine-only (REST + MCP), as scoped; no page, panel, or nav change.
  Confirmed via `git diff -- apps/frontend/` (empty).
- **`.claude/project-template.md` is still the generic unfilled template** (carried over from
  iter-0/iter-1, not this iteration's scope) — this developer again used `docs/goal.md`'s
  Constraints section, `scripts/start-backend.sh`, and the venv at `apps/backend/.venv/` as the
  actual stack source of truth. The backend venv runs Python 3.14.4.
