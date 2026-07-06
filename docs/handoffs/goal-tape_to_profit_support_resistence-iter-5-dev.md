# goal-tape_to_profit_support_resistence-iter-5 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-5
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## Note on exact field naming (for QA/reviewer alignment)

The pre-dev QA test plan (`reports/qa/goal-tape_to_profit_support_resistence-iter-5-test-plan.md`)
speculatively named fields before the implementation existed. The actual shape, chosen to match
this codebase's EXISTING conventions (the `sr_timeframe_weights` dict-of-values precedent, and
v1/iter-4's own trade-dict field names):

- **Config fields** are THREE dicts keyed by confluence class (`"A"`/`"B"`/`"C"`), not six
  separate per-class scalar fields: `Config.structure_tape_stop_bps_by_class`,
  `Config.structure_tape_reward_r_multiple_by_class`, `Config.structure_tape_size_multiple_by_class`.
  The QA plan's grep pattern `structure_tape_(stop_distance|reward_target|size_multiple)` will only
  partially match — the dict-per-class design was chosen because it makes an unregistered class
  literal a `KeyError` (a defensive floor) rather than a silent fallback, mirroring
  `sr_timeframe_weights`.
- **Trade fields** reuse the EXISTING v1 shape, never a new key style: the stop is still
  `trade["invalidation_price"]` (not `trade["stop"]`); the exit reason is still
  `trade["exit"]["reason"]` (not a top-level `trade["exit_reason"]`) — its VALUE for the new exit
  IS exactly `"reward_target"` as the QA plan names it (`EXIT_REWARD_TARGET`). A NEW
  `trade["target_price"]` key (structure_tape trades only, mirroring `invalidation_price`) carries
  the resolved take-profit price.
- **The per-class breakdown** lives at `result["aggregates_by_class"]` (not
  `response["class_breakdowns"]`), sibling to the existing `result["aggregates"]` — each class an
  `_aggregate()`-shaped dict (`n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`,
  `max_drawdown_r`) plus `insufficient_sample`.
- **No "per train/hold-out split" dimension exists inside one report.** A single backtest already
  runs over ONE dataset, which itself carries ONE `split` value (`"train"` or `"holdout"`, per
  `research/datasets.py`) — there is no second axis to add. `aggregates_by_class` is therefore the
  complete per-class breakdown of THAT one report's own trades; running the same strategy against
  a train dataset and a holdout dataset separately yields two reports, each with its own per-class
  breakdown for that split. This matches the execution plan's own scope ("no new endpoint, no new
  module... computed once by the existing `_aggregate`") and is the natural consequence of J-06
  (out of scope this iteration) being the journey that compares train vs. holdout, not J-05.

## What Was Built

- **Three new `structure_tape_*`-namespaced, per-class `Config` fields** (each a dict keyed by
  `"A"`/`"B"`/`"C"`, documented rationale inline, no literal in `research/backtests.py`):
  - `structure_tape_stop_bps_by_class` = `{"A": 1.0, "B": 5.0, "C": 10.0}` — basis points beyond
    the ARMING LEVEL's own price (goal.md: "an A-class level... justify a stop ~1bp beyond it").
  - `structure_tape_reward_r_multiple_by_class` = `{"A": 3.0, "B": 2.0, "C": 1.0}` — an R-multiple
    of the trade's own R basis, bounded by the next opposing level.
  - `structure_tape_size_multiple_by_class` = `{"A": 2.0, "B": 1.0, "C": 0.5}` — applied over the
    existing fixed `strategy_dollars_per_r` notional.
  - All three added to `config_fingerprint()`'s `excluded` set beside the 3 existing
    `structure_tape_*` exclusions — `config_fingerprint()` stays pinned at `4d665603569b9dbf`
    (verified: presence at any value never moves it).
- **`Config.strategy_definition("structure_tape")` extended** (v1's own branch/dict completely
  untouched): `exits.r_stop` is now `{"rule": "class_scaled_invalidation_beyond_level",
  "stop_bps_by_class": {...}}` (previously identical to v1's spread-based rule); a NEW
  `exits.reward_target` key (`{"rule": "class_r_multiple_bounded_by_next_opposing_level",
  "r_multiple_by_class": {...}}`); a NEW top-level `size_multiple_by_class` key. `horizon_seconds`,
  `state_flip`, `dataset_end`, `fees`, `slippage`, `dollars_per_r` stay byte-identical to v1's.
- **`BacktestRunner` class-scaled math** (`app/research/backtests.py`), gated strictly on the
  arming `level` being present (`structure_tape` trades only — v1/null trades carry no `level` key
  and are provably unaffected):
  - `_class_scaled_invalidation` (NEW helper) — a stop placed the class's own bps beyond the
    ARMING LEVEL's price, on the adverse side. A rejection entry can arm anywhere inside the
    proximity band (either side of the level), so the level-relative price can occasionally sit
    at/through the entry print itself (a structurally invalid stop); the helper falls back to the
    SAME class-bps distance measured from the entry price instead in that case (proven by the
    existing `SIM-ASKABS` rejection-short case, whose entry sits 2bps beyond the level while
    class A's stop is only 1bp — see "Known judgment calls" below).
  - `_next_opposing_zone_price` / `_zone_nearest_price` (NEW helpers) — resolve the nearest OTHER
    confluence zone's nearest member price on the side the trade direction implies (above entry
    for a long, below for a short), excluding the arming zone by identity, from the SAME
    `confluence_zones` list already fetched to arm the trade (no second/future `compute_levels`
    call — lookahead-free by construction).
  - `_class_scaled_target` (NEW helper) — the reward-target price: the class's own R-multiple
    times the trade's R basis, capped at the distance to the next opposing level when one was
    found (never demanding a move past already-detected structure); an honest fallback to the pure
    R-multiple when no opposing zone qualifies on that side.
  - `_arm_trade` now branches on `level is not None` to call the class-scaled invalidation instead
    of the shared spread-based `_synthetic_invalidation`, and (structure_tape only) stores a new
    `target_price` key on the position.
  - `_exit_reason` gains a NEW `EXIT_REWARD_TARGET = "reward_target"` exit reason, checked via
    `trade.get("target_price")` (absent for v1/null — the branch can never fire for them),
    inserted at the documented, now-five-way precedence: **r_stop, then reward_target, then
    state_flip, then horizon**.
  - `_close_trade` now branches on `"level" in trade` to scale `shares` by the class's own size
    multiple over the SAME fixed `strategy_dollars_per_r` notional; carries `target_price` into
    the closed trade dict (structure_tape only, mirroring `invalidation_price`).
- **Per-class PnL breakdown** (`_aggregate_by_class`, NEW function) — partitions the SAME trade
  list by `trade["level"]["class"]` (v1/null trades carry no `level` key and so contribute to NO
  class), calls the EXISTING `_aggregate` once per class, and labels `insufficient_sample` by
  REUSING the existing `Config.pnl_min_sample_size` floor (the `edge_report.py` precedent:
  "reuses that field rather than minting a third minimum" — no fourth new config field). Always
  produces all three classes (even for v1/null reports, which honestly show all-empty A/B/C —
  computed the identical way regardless of strategy, no strategy-id special-casing). Added to
  `BacktestRunner.run()`'s persisted `result` dict as `"aggregates_by_class"`, computed once
  alongside the existing `"aggregates"` and served verbatim by the EXISTING
  `GET /research/backtests/{id}` and MCP `backtests` (no new endpoint, no new module).
- **Extended `tests/test_no_execution_path.py`** with a dedicated test naming the new sizing/exit
  code explicitly and re-asserting no Tier-1/Tier-2 execution-vocabulary pattern appears in it
  (on top of the pre-existing repo-wide sweep, which already covered it).

## Files Changed

- `apps/backend/app/config.py` -- 3 new `structure_tape_*_by_class` dict fields (documented
  rationale, ~45 lines) inserted after the existing `structure_tape_breakthrough_state_by_direction`
  field; `strategy_definition`'s `structure_tape` branch extended (class-scaled `r_stop`, new
  `reward_target` key, new `size_multiple_by_class` key; v1's own branch untouched); all 3 new
  field names added to `config_fingerprint()`'s `excluded` set.
- `apps/backend/app/research/backtests.py` -- new module-level helpers
  `_class_scaled_invalidation`, `_zone_nearest_price`, `_next_opposing_zone_price`,
  `_class_scaled_target`, `_aggregate_by_class`; `_structure_tape_arm` returns a 4th element
  (`next_opposing_zone_price`); `_structure_tape_trades` threads it through; `_arm_trade` branches
  on `level is not None` for the invalidation formula and adds `target_price`; `_exit_reason` adds
  the `reward_target` check at the documented precedence; `_close_trade` branches on `"level" in
  trade` for the class-scaled `shares` and carries `target_price` into the closed dict; `run()`
  adds `"aggregates_by_class"` to the persisted result; new `EXIT_REWARD_TARGET` constant exported
  in `__all__`; import line reordered (`compute_levels` first) to preserve an existing source-scan
  test's exact substring match.
- `apps/backend/tests/test_backtests.py` -- new bar fixtures `_class_b_bar_fixture` (2-timeframe,
  1 zone, class B, isolated — proves the uncapped reward-target fallback) and
  `_class_c_bar_fixture` (1-timeframe, 2 zones, class C — the near/arming zone plus a far zone
  close enough to cap the reward target, proving the CAPPED branch); new
  `_assert_structure_tape_trade_arithmetic` and `_assert_per_class_breakdown_isolates_one_trade`
  helpers (independently re-derive the class-scaled formulas, the `_expected_aggregates`
  precedent); updated `test_structure_tape_definition_is_config_owned_and_additive_beside_v1` for
  the new grammar shape; updated the 4 existing class-A arm tests (breakthrough long/short,
  rejection long/short) to assert the class-scaled arithmetic and per-class breakdown (their own
  entry/exit ts/price assertions are UNCHANGED — verified byte-identical to iter-4); 6 new tests:
  class-B stop/size (uncapped target), class-C widest-stop/smallest-size AND the reward-target CAP
  (a real, closer opposing zone), a dedicated reward-target-fires test (class A, a longer window),
  a config-sourced no-magic-number test, a sub-minimum-n/zero-trade-class honesty test, and a
  v1-report-carries-honest-all-empty-breakdown test; extended the fingerprint-exclusion test with
  the 3 new fields.
- `apps/backend/tests/test_no_execution_path.py` -- one new test naming the class-scaled
  sizing/reward-target code explicitly in the no-execution-vocabulary scan.
- `apps/backend/tests/test_strategies_api.py` -- extended the existing
  `test_backtest_accepts_structure_tape_strategy_id` (a real `POST /research/backtests` ->
  `GET /research/backtests/{id}` round trip) with an assertion that `aggregates_by_class` is
  present and honestly all-empty — closing the loop on "row 42 is served by the EXISTING route"
  at the API-test layer, not only the unit layer.
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-5-dev.md` -- this handoff.

`apps/frontend/` is untouched — confirmed via `git diff --stat -- apps/frontend/` (empty), per the
phase spec (machine surface only, Frontend Present: no).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -q -rA` (project-template's backend test
command)

Result: **full backend suite green — 1135 passed, 1 skipped (the pre-existing gated
live-integration test, unrelated), 0 failed.** Exactly the iter-4 baseline (1128 passed, 1 skipped)
plus the 7 new tests this iteration adds (6 in `test_backtests.py`, 1 in
`test_no_execution_path.py`) — zero regressions. Ran the full suite once, plus the
directly-affected files twice more (`test_backtests.py`, `test_no_execution_path.py`,
`test_strategies_api.py`, `test_backtests_api.py`, `test_levels.py`, `test_bars.py`,
`test_profile_equivalence.py`, `test_mcp_server.py`) with identical pass counts both times (no
flakiness). Also confirmed green individually: `test_pnl_ledger.py`, `test_pnl_scan.py`,
`test_edge_report.py`, `test_pnl_ledger_api.py`, `test_profiles_api.py` (these consume
`BacktestJobManager` too; none do an exact whole-`result`-dict equality that the new
`aggregates_by_class` key could break).

**Live verification** (beyond pytest's `TestClient`): started the real dev stack
(`scripts/dev.sh`) — backend on :8301, frontend on :3301 — both came up clean (`Application
startup complete`, Next.js `Ready in 1192ms`, `GET /health` 200, `GET /` 200). Confirmed live via
curl: `GET /research/strategies` serves the new class-scaled grammar
(`stop_bps_by_class`/`reward_target`/`size_multiple_by_class`); created and ran a real
`structure_tape` backtest via `POST /research/backtests` against the live server's own PG dataset
(no bar series recorded in this fresh server, so an honest zero-arm report — `aggregates_by_class`
correctly shows all three classes `n=0`, `insufficient_sample: true`); confirmed the MCP
`backtests` and `strategies` tools (`app.mcp.call_tool`, pointed at the live server via
`TAPEOLOGY_API_BASE`) serve BYTE-IDENTICAL JSON to REST, including the new field. Both server
processes were stopped afterward (verified via `ps` — no lingering `uvicorn`/`next dev`/
`next-server` processes).

## Known judgment calls (documented per the plan's "Key Design Decisions" list)

1. **Exit precedence**: `r_stop`, then `reward_target`, then `state_flip`, then `horizon` — both
   new price-crossing exits (stop and target) checked before the tape-reading exit (state_flip)
   and the time-based exit (horizon), symmetric with the pre-existing `r_stop`-before-`state_flip`
   ordering.
2. **"Next opposing level" resolution**: the nearest OTHER zone's nearest-member price on the side
   `direction` implies, from the SAME `confluence_zones` list already fetched to arm the trade,
   excluding the arming zone by object identity (never by price coincidence — a rejection entry
   can sit exactly at its own arming level's price).
3. **Class-scaled invalidation is a genuinely NEW helper** (`_class_scaled_invalidation`), not a
   parameterized extension of `_synthetic_invalidation` — v1/null call sites are provably unchanged
   (same function, same arguments, same call site; the equivalence/byte-identity tests confirm no
   behavior shift).
4. **The level-relative-vs-entry-relative stop fallback** (not explicitly asked for by the plan,
   but a correctness necessity discovered while implementing): a rejection entry can arm up to the
   FULL proximity band (5bps) away from the level on either side, while class A's own stop is
   tighter (1bp) — the committed `SIM-ASKABS` rejection-short fixture is exactly this case (entry
   2bps beyond the level, class-A stop only 1bp beyond the level, so the level-relative price would
   sit ON THE WRONG SIDE of the entry print). Resolved by falling back to the SAME class-bps
   distance measured from the entry price instead, whenever the level-relative price would not be
   genuinely adverse to entry. Verified empirically (not hand-derived) via a scratch harness before
   writing the test assertion; proven directly by
   `test_structure_tape_rejection_short_arms_at_the_class_a_resistance_level`'s
   `_assert_structure_tape_trade_arithmetic` call, which independently re-derives this exact
   fallback branch.
5. **The per-class breakdown is ALWAYS present** on every report (v1 and structure_tape alike),
   never omitted for v1 — `_aggregate_by_class` is a pure, strategy-agnostic partition of whatever
   trades exist; a v1 report honestly shows all three classes empty (v1 never touches levels), the
   identical "honest emptiness" discipline `_aggregate([])` already uses for a zero-arm window,
   applied one level deeper. This avoids strategy-id special-casing in `run()` (no new `if
   strategy_id == ...` branch was added there) and keeps every report's top-level schema uniform.
6. **The reward-target's config-bounded floor reuses `pnl_min_sample_size`** for the per-class
   `insufficient_sample` label (not a fourth new config field) — the plan explicitly names 3 new
   fields, and the `edge_report.py` precedent already establishes "reuse the existing floor rather
   than minting a third [here, fourth] minimum."

## Known Issues

- **No dedicated corrupt-bar-series test for the class-scaling path specifically** — unchanged
  from iter-4's own note: `research/levels.py`'s `compute_levels` already aliases a corrupt sole
  bar series to `no_bar_series_for_symbol` (empty levels/zones), so `structure_tape` arms nothing
  regardless of WHY the zones list is empty; no new logic exists in this iteration's code for that
  path specifically.
- **Class B and C are proven end-to-end via two NEW small synthetic bar fixtures** (not the
  committed real PG fixture, which stores only 1h+1d and never produces class A anyway per the
  iter-3 lesson, nor the existing `SYN-CONFLUENCE` fixture, whose class-B/C zones sit at ~200/300 —
  too far from the reachable SIM-BUYER price path within a short, fast test window). Both new
  fixtures are engineered at the SAME ~100.00 price SIM-BUYER already breaks through (verified by
  direct computation via a scratch probe, not hand-derived), so all three classes are measured via
  the IDENTICAL, already-proven tape stream — only the bar series (and therefore the confluence
  class) differs. This mirrors the `_confluence_fixture` precedent exactly, just relocated so the
  existing sim streams can reach it inside a fast test.
- **The reward-target CAP is proven with one dedicated dual-zone fixture** (class C: a near
  arming zone plus a deliberately-placed far zone close enough to bind) — the class-A and class-B
  tests exercise the honest UNCAPPED / no-opposing-zone fallback instead (the opposing zone the
  SYN-CONFLUENCE fixture offers, ~200 away, is always farther than these trades' own tiny
  class-scaled R-multiple distances). Both branches of `_class_scaled_target`'s `min()` are
  therefore covered, on different fixtures.
- No frontend work this iteration (machine surface only, per the phase spec and the J-07
  frozen-frontend guard) — confirmed no `apps/frontend/` changes via `git diff --stat`.
- J-06 (generalize the edge-report/sweep to a named-strategy comparison, hold-out promotion) is
  explicitly out of scope this iteration and was not touched — confirmed via grep
  (`research/pnl_scan.py` and `research/edge_report.py` unmodified, no `set_champion_pointer` call
  added).
- Audit item B1 (carried forward from iter-4, not addressed here): the breakthrough arm is a
  static price-position test (`point.last > price`), not a fresh event-to-event cross — unchanged;
  it affects J-06's honest edge comparison, not J-05's class-scaled risk math.
