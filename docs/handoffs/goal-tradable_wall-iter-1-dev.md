# goal-tradable_wall-iter-1 Dev Handoff

**Phase:** goal-tradable_wall-iter-1
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

- **`apps/backend/app/research/tradability.py`** (new module) — the tradable level map, J-01's
  sole owner. Consumes `compute_levels`'s `levels` + `confluence_zones` output **verbatim** (never
  re-detects pivots/extremes, never touches `levels.py`'s frozen 5 bps / 20 bps parameters).
  - **Morning-markup as-of resolution**: for a requested `as_of` inside a session, finds the last
    completed daily bar strictly before the requested session's own UTC calendar date (holidays
    and weekends handled for free — no hardcoded calendar). Feeds `compute_levels` an as-of epoch
    of that prior bar's own epoch + one calendar day (closes its period, the same convention
    `levels.py`'s own `_prior_period_extremes` uses), through a new read-only, duck-typed
    `_PriorSessionBarView` that additionally bounds every loaded bar (on every timeframe) to
    `epoch <= prior_bar.epoch`.
  - **Band clustering**: raw levels split into support/resistance by the prior session's own close
    price, then each side clustered independently by an anchor-fixed scan (the same technique
    `levels.py`'s `_cluster_levels` uses for confluence zones, reused as a technique only) at a
    new, wider, config-owned bps tolerance. Every level joins exactly one band (including
    singletons); at most `tradability_band_cap_per_side` bands per side survive, ranked by quality
    score.
  - **Quality scoring**: config-owned weighted sum of distinct-timeframe breadth, the **daily**
    (`1d`) touch count (only `1d` members' `touch_count` — see Fix Notes; superseded the initial
    all-timeframe sum), a 0..1 recency score (position of the most recent daily bar whose range
    intersects the band), and a round-number flag (config-owned increment + tolerance).
  - **Class inheritance**: a band's A/B/C class is a projection of its best overlapping confluence
    zone from `compute_levels`'s `confluence_zones` (highest class, tie-broken by score); `null`
    when no zone overlaps — an honest absence, never a fabricated/defaulted grade.
  - **Honest empty states**: `no_bar_series_for_symbol: true` when nothing is recorded for the
    symbol at all (mirrors `levels.py`'s exact flag meaning); `false` with empty `bands` and
    `basis_as_of: null` when a basis can't be resolved (no daily series, or no prior session yet).
- **A real, non-obvious no-lookahead bug found and fixed during implementation** (see Known Issues
  / Notes below for the full mechanism): the naive "as-of = prior bar's epoch + 1 day" approach,
  when handed straight to `compute_levels`, can — for any two CONSECUTIVE trading sessions in a
  fully-fetched series — land exactly on the requested (or a later) session's own bar epoch,
  because real daily bars are stamped at a consistent hour-of-day and `levels.py`'s own
  `_bars_as_of` uses a single inclusive `<=` threshold for both "is this bar visible" and "has its
  period closed". That collision would silently unlock a bar's own swing-pivot check using a
  same-epoch future bar as its right-hand neighbour. Fixed with `_PriorSessionBarView`, a read-only
  view that bounds bar visibility itself (on every timeframe) *in addition to* the as-of epoch, so
  the as-of epoch's only remaining job is closing the prior bar's own period.
- **`apps/backend/app/config.py`** — five new named constants (`tradability_band_cap_per_side`,
  `tradability_band_width_bps`, `tradability_quality_weights`, `tradability_round_number_increment`,
  `tradability_round_number_tolerance_bps`), each documented with its rationale and added to the
  `config_fingerprint` exclusion set (the `sr_*` / `bar_timeframes` precedent). `config_fingerprint`
  confirmed unchanged (`4d665603569b9dbf`) via direct computation against the current source, plus
  a fingerprint-stability test and the paired real-threshold counter-test.
- **`GET /research/tradability?symbol=&as_of=`** (`apps/backend/app/research/routes.py`) — mirrors
  `get_levels` byte-for-byte in structure: parses the ISO `as_of` once at the route boundary, 422s
  on missing `symbol` or malformed `as_of` (never a silent "now" default), serves the module's
  output verbatim as `{"symbol", "as_of", "bands", "no_bar_series_for_symbol", "basis_as_of"}`.
- **Read-only MCP proxy `tradability`** (`apps/backend/app/mcp/__init__.py`) — thin verbatim
  `httpx` GET passthrough, two required params (`symbol`, `as_of`), sharing the same dispatch
  branch as the existing `levels` tool. `TOOL_NAMES` / `TOOLS` updated; the module's own result-
  contract docstring updated to list `tradability` among the shipped endpoints.
- **New committed real-AAPL fixture** — `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json`
  (121 real daily bars, 2026-01-01 through 2026-06-26, frozen from this environment's own live
  `.data/bars` Yahoo fetch — never fabricated). Contains the exact pinned rejection cluster
  goal.md cites: 300.75 (06-09), 300.48 (06-16), 302.07 (06-17), 300.57 (06-18), and confirms the
  2026-06-19 Yahoo gap (the market holiday) directly in the real data.
- **Tests**: `tests/test_tradability.py` (19 tests — pure/module-level, synthetic + real-fixture
  exact values), `tests/test_tradability_api.py` (11 tests — route-level integration), and
  additions to `tests/test_mcp_server.py` (+2 tests: byte-identity on a non-empty live AAPL result
  including the pinned acceptance, and required-args validation; plus `EXPECTED_TOOLS` and the
  `test_backend_down_every_tool_raises_an_explicit_error` args map updated for the new tool).

## Files Changed

- `apps/backend/app/research/tradability.py` -- NEW. Sole owner of the tradable-map computation.
- `apps/backend/app/config.py` -- ADDED 5 named constants + their `config_fingerprint` exclusions.
- `apps/backend/app/research/routes.py` -- ADDED `GET /research/tradability` + import.
- `apps/backend/app/mcp/__init__.py` -- ADDED the `tradability` tool (schema, dispatch branch,
  docstring update).
- `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260101_20260626.json` -- NEW. Committed real AAPL
  daily-bar fixture (frozen live Yahoo data) covering the pinned rejection cluster.
- `apps/backend/tests/test_tradability.py` -- NEW. Unit/fixture test suite.
- `apps/backend/tests/test_tradability_api.py` -- NEW. Route-integration test suite.
- `apps/backend/tests/test_mcp_server.py` -- MODIFIED. Added `tradability` to `EXPECTED_TOOLS`,
  added 2 new tests, added a `tradability` entry to the "every tool errors when backend is down"
  args map.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1239 collected, 1233 passed, 6 skipped, 0 failed.** Baseline (per the iter-0 handoff) was
1207 collected / 1201 passed / 6 skipped — this run adds exactly the 32 new tests this iteration
wrote (19 in `test_tradability.py` + 11 in `test_tradability_api.py` + 2 in `test_mcp_server.py`),
all passing; the skip count is unchanged (no new skips introduced); zero regressions; no test
deleted or weakened. `test_observer_equivalence.py` (7/7) and `test_profile_equivalence.py`
(15/15) are both included in this green run.

New-file-only command: `cd apps/backend && .venv/bin/python -m pytest tests/test_tradability.py tests/test_tradability_api.py tests/test_mcp_server.py -v`
Result: 19 + 11 + 25 = 55 passed, 0 failed (test_mcp_server.py's 25 includes 23 pre-existing + 2 new)

Live-server verification (in addition to the pytest suite, per the pre-handoff checklist): started
a real `uvicorn app.main:app` instance against a fresh temp bar dir, seeded the committed AAPL
fixture, and confirmed live: `GET /research/tradability` returns the pinned resistance band
(rank 0, round_number=true, class="C"); the MCP `tradability` tool's body is byte-identical to the
REST response; two identical REST calls are byte-identical; `GET /research/levels` is
byte-identical before/after a `GET /research/tradability` call on the same store; 422s on missing
`symbol` / missing `as_of` / malformed `as_of`; an unrecorded symbol returns the honest empty
state; other era-1-5 surfaces (`/research/levels`, `/research/taxonomy`, `/meta/ui-routes`) all
respond 200. Server stopped cleanly afterward (verified no uvicorn process remained).

`config_fingerprint` verified == `4d665603569b9dbf` via direct computation against the current
`CONFIG` singleton (the same check the pinned fingerprint test performs) — there is no lightweight
GET endpoint that echoes the raw fingerprint outside of heavier flows (thesis declaration, backtest
reports), so this iteration did not spin up one of those flows solely to re-derive a value already
proven by direct computation and the dedicated unit test.

## Known Issues

- **No frontend work this iteration** (`Frontend Present: no` per the plan/spec) — the map's UI
  home (`/structure` → Tradable Map default view) is J-05, not this iteration. Verified via API +
  MCP + a live server only; no browser check was in scope.
- **`tradability.py` reads bars through a second, deliberate truncation layer
  (`_PriorSessionBarView`)**, not solely through the `compute_levels` as-of parameter. This was a
  necessary fix (see "What Was Built" above and the module's own docstring) for a real lookahead
  hazard the naive single-as-of-epoch approach has on any two CONSECUTIVE trading sessions — it is
  NOT a mutation of `levels.py` (verified byte-identical before/after in both the unit and API test
  suites, plus live), just a second, additive, read-only filtering layer this module owns for its
  own calls into the frozen function. A reviewer should specifically confirm this reads as a
  correctness fix, not scope creep — it directly serves the "no lookahead" critical anti-goal.
  Discovered via a synthetic 8-day, zero-weekend-gap stress test in `test_tradability.py`
  (`test_no_lookahead_bars_after_the_basis_never_affect_the_result`); the pinned AAPL acceptance
  scenario itself (which has a 4-day holiday+weekend gap before the prior session) was NOT exposed
  to this hazard, so the fix changed no previously-asserted AAPL number.
- **Quality-score weights, band-width bps, and the round-number rule are the developer's
  config-owned design freedom** (per the goal/phase spec's explicit statement that this is not an
  ambiguity to raise). Chosen and calibrated against the committed AAPL fixture, verified by direct
  computation (not hand-derived) — documented with rationale in `config.py`. `tradability_band_cap_per_side`
  defaults to 5 (the goal's own ceiling); nothing in code prevents a future config override above 5,
  since no test or spec bullet requires a hard runtime clamp — only the DEFAULT was required to be `<=5`.
- **Band "side" classification** (support vs. resistance) is not an explicit Data-Contract field
  name from the goal doc — implemented as a plain comparison against the prior session's own close
  price (levels priced above it are resistance, at-or-below are support), which is the natural,
  standard reading and requires no new bar detection.

---

## Fix Notes — review round 1 (2026-07-14)

Review verdict was **FAIL** on one CRITICAL (a scoring bug the daily-only fixture could not
surface) plus one MINOR (missing multi-timeframe test) and one NOTE (advisory). This round fixes
the two `fix_tasks`; the NOTE is deferred with evidence (below). No rebuild — three surgical edits
plus four new committed fixtures.

### CRITICAL fixed — the quality score now uses the DAILY touch count, not an all-timeframe sum

- **Root cause (confirmed by live reproduction):** `_quality_score` summed every member's
  `touch_count` across ALL timeframes. On the real multi-timeframe `.data/bars` AAPL store (1,811
  levels / 212 zones — the exact baseline the reviewer and QA probe), a resistance band near the
  current price can hold ~70 5m/1h members; their combined shallow touch volume (2,000+) drowned
  the pinned 300.48–302.07 rejection wall (summed touch ~95). Live, the wall ranked **7th of 9** and
  was excluded from the served top-5 entirely. The committed daily-only fixture could not surface
  this because a daily-only band's summed touch == its daily touch.
- **Fix:** the touch factor now counts only `"1d"` members' `touch_count` — goal.md's factor is
  literally *"daily touch count"* (and `config.py`'s own weight comment already said *"daily touch
  history"*), so this aligns the code to the stated spec, not a tuning hack. The pinned wall's
  daily series rejected it **39 times** — by far the highest daily touch count of any band — so it
  now ranks **#1** (score 153.0 vs the next band's 82.7), a robust margin. Intraday members still
  count toward `timeframe_breadth` (cross-timeframe agreement is its own signal); they just no
  longer inflate the per-band touch total.
- **Files:** `apps/backend/app/research/tradability.py` (new `_DAILY_TIMEFRAME = "1d"` structural
  constant + the `_quality_score` change + module-docstring quality-scoring paragraph);
  `apps/backend/app/config.py` (the `tradability_quality_weights` rationale comment, now describing
  the daily-only semantics and why an all-timeframe sum inverts the signal). **Weights, band-width,
  band-cap, and round-number rule are UNCHANGED** — only *what the touch factor counts* changed.
- **No frozen-output impact:** all existing synthetic + daily-only-AAPL assertions (incl. the pinned
  band's `quality_score == 123.0` on the daily fixture, where daily-touch == summed-touch) pass
  **unchanged**; `config_fingerprint` stays `4d665603569b9dbf`; `levels.py` byte-identity holds.

### MINOR fixed — a committed multi-timeframe regression fixture + test

- Added four real, frozen Yahoo slices under `tests/fixtures/yahoo/` (each truncated to the
  2026-06-18 basis, frozen from this environment's live `.data/bars` — never fabricated):
  `AAPL_1h_20260601_20260618.json` (98 bars), `AAPL_4h_20260601_20260618.json` (28),
  `AAPL_5m_20260601_20260618.json` (1,092 — the dominant intraday-density source), and
  `AAPL_1w_20260601_20260615.json` (3). Seeded ALONGSIDE the existing daily fixture, they reproduce
  the live multi-timeframe density.
- New test `test_aapl_pinned_band_ranks_top2_under_realistic_multitimeframe_density` asserts the
  pinned wall ranks top-2 (in fact #1) under that density, and carries a **regression guard**: it
  asserts at least one served resistance band has >3× the wall's raw all-timeframe touch volume yet
  ranks BELOW it (e.g. the 309–311 5m/1h cluster, ~2,300 summed touches) — the direct proof the
  score is daily-touch-driven, not volume-driven. **This test genuinely bites:** verified that under
  the old all-timeframe sum it ranks the wall 7th-of-9, so the `pinned_index in (0,1)` assertion
  fails — exactly the regression that shipped undetected. File:
  `apps/backend/tests/test_tradability.py`.

### NOTE (advisory) — DEFERRED, with evidence it does not affect acceptance

- The reviewer's NOTE: `_PriorSessionBarView`'s single cutoff (`prior_bar.epoch`, the daily bar's
  04:00Z open stamp) applies to every timeframe, so it excludes the prior session's OWN intraday
  bars (1h/5m open at 13:30Z, after that instant) — "data through the prior session's close" should
  include them. The reviewer hypothesized this is "*likely a secondary contributor to the miss*."
- **Empirically it is NOT a contributor.** I simulated the fix (a provably-safe per-timeframe
  cutoff: daily+ keep `prior_bar.epoch`; intraday use a DATE-based cutoff = the prior session's
  calendar date, which never admits any bar dated on/after the strictly-later requested session).
  It newly admits all 78 of 06-18's own 5m bars, yet the pinned band's rank and score are
  **identical: #0, 153.0**, with and without the change. The score is daily-touch-driven, and daily
  bars are already fully included, so the intraday cutoff cannot move it. The scoring bug was the
  **sole** cause of the miss.
- **Why deferred, not fixed:** (1) it is severity NOTE and NOT in the review's `fix_tasks`; (2) it
  has zero effect on any Definition-of-Done assertion (verified above); (3) the current behavior is
  on the SAFE side of the critical *no-lookahead / morning-markup* rail — it OVER-excludes (some
  completed bars), never admitting forming/future data, so it is anti-goal-**compliant**, not a
  violation; (4) changing the no-lookahead cutoff is the single highest-risk edit in this module, so
  making it for zero acceptance benefit trades real regression risk on a critical rail against an
  advisory completeness nicety. The provably-safe date-based approach is recorded here so a future
  iteration (e.g. J-06, which will care about intraday recency) can adopt it deliberately with its
  own no-lookahead tests. Supersedes nothing shipped; the served map is unchanged either way.

### Verification (this round)

- `apps/backend`: full suite **1240 collected, 1234 passed, 6 skipped, 0 failed** (was
  1239/1233/6 — exactly the +1 regression test; no test deleted, weakened, or newly skipped).
- Tradability subset (`test_tradability.py` + `test_tradability_api.py` + `test_mcp_server.py`):
  **56 passed** (was 55).
- `config_fingerprint` == `4d665603569b9dbf` (live-confirmed via direct computation).
- **Live acceptance probe** against the real `.data/bars` (the same state QA/the evaluator probe),
  default config: `compute_tradability("AAPL", 2026-06-22T15:00:00Z)` → 10 bands (5+5), basis
  `2026-06-18T04:00:00Z`, the pinned band `[300.23–302.25]` at resistance **index 0** (top-2),
  `round_number=True`, `class="A"`, spanning 1d/1h/4h/5m. PASS.
- Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
