# goal-tape_to_profit_support_resistence-iter-4 Execution Plan

Frontend Present: no

## Alignment check

J-04 ("Tape-confirmed structure entries as a registered strategy") is docs/goal.md Key Capability
#4 ("The `structure_tape` strategy") and Must-have journey J-04 verbatim, the natural next step
after J-01 (bar store) → J-02 (levels) → J-03 (confluence/A-B-C), all three confirmed **passing**
as of iter-3 in `runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json`
(J-07 `already_passing`, pinned fingerprint `4d665603569b9dbf`). No drift or scope creep detected:
the spec's IN SCOPE section maps 1:1 onto goal.md's J-04 acceptance text (registry, entry grammar,
runner extension, new endpoint, MCP proxy, fingerprint hygiene) and correctly excludes J-05
(class-scaled risk/size) and J-06 (named-strategy comparison/promotion) as OUT OF SCOPE, matching
goal.md's own natural dependency order. This is a single **risky** journey, correctly planned alone.

**One finding worth flagging before work starts**: the spec's "Docs" rider asks to extend the
README's S/R bullet to describe confluence zones + A/B/C (closing iter-3's COHERENCE-WARN). I
checked `README.md`'s `AUTO:capabilities` block directly — the S/R bullet (line 73) **already**
describes confluence zones and A/B/C grading in full detail (git blame: commit `173e387`, iter-3's
own automatic `readme-maintainer` showcase step). That half of the rider is **already done** — no
action needed. Only the second half (a plain-language bullet for the new strategy registry +
`structure_tape` + the `strategies` MCP tool) is genuinely new work this iteration, and the
per-iteration `readme-maintainer` step will likely also pick it up automatically after dev — the
developer should still add it explicitly since the spec lists it as an iteration deliverable.

## What to Build

Register a second, additive strategy (`structure_tape`) beside the frozen `v1`, wire it into the
existing backtest runner so its entries arm only where a classified S/R level and a confirming
tape read coincide, and serve the registry + champion over a new read endpoint and MCP tool.

- **Config-owned strategy registry (additive).** `STRATEGY_TAPE_ID = "structure_tape"` constant in
  `config.py` beside `STRATEGY_V1_ID`; extend `Config.strategy_definition()` to return the
  `structure_tape` grammar for that id (`v1`'s branch is untouched — same `if/return` shape, just
  one more branch). Add `_STRATEGY_IDS_IN_ORDER = (STRATEGY_V1_ID, STRATEGY_TAPE_ID)` (mirroring
  `_PROFILE_IDS_IN_ORDER`) and `Config.strategy_registry()` (mirroring `Config.profile_registry()`
  at `config.py:1171` — built entirely from `strategy_definition`, no second copy of any id).
- **`structure_tape` entry grammar, every threshold config-owned.** Entries arm when price enters a
  classified level's proximity band AND the tape confirms direction:
  - **rejection** (fade): `ask_absorption` at resistance → short; `bid_absorption` at support → long
  - **breakthrough** (follow): `buyer_control` with price impact through resistance → long; mirror
    (`seller_control` through support → short)
  Reuse the EXISTING state vocabulary only — no new tape state. The proximity-band width and the
  rejection/breakthrough state mapping are named config fields (no inline literals).
- **Extend the ONE backtest runner** (`app/research/backtests.py::BacktestRunner._strategy_trades`,
  currently `backtests.py:309`) to interpret the `structure_tape` entry rule as a second branch
  beside v1's state-native sustained-premise loop, consuming the symbol's precomputed
  levels/confluence-zones from the row-39 owner (`research/levels.py::compute_levels`) — **no
  second S/R computation inside the runner**. Each `structure_tape` trade is stamped with strategy
  id + the specific level (price/timeframe/class) that armed it. Exits/R/$ reuse `_exit_reason` /
  `_close_trade` unchanged (class-scaled stop/reward is J-05, out of scope).
- **New endpoint `GET /research/strategies`** (mirror `GET /research/profiles` at `routes.py:1776`
  and its `profiles_projection` module shape in `research/profiles.py`) serving
  `Config.strategy_registry()` (`v1` + `structure_tape`, registration order) plus the champion
  **strategy id read verbatim from `store.get_champion_pointer()`** — the exact same single pointer
  `profiles.py` already reads (`{"strategy_id", "profile"}`), never a second champion source.
- **MCP `strategies` proxy**: add `"strategies": "/research/strategies"` to `_STATIC_PATHS`
  (`mcp/__init__.py:84`) plus a `types.Tool` entry (no-arg, mirroring `datasets`/`bars`/`backtests`)
  — JSON byte-identical to REST; backend-unreachable → the existing `BackendUnreachableError` path
  (no new error handling needed, it's already generic).
- **Fingerprint hygiene.** Every new `structure_tape`-only config field (proximity band, the
  rejection/breakthrough constants, any field not reused from v1) goes into
  `config_fingerprint()`'s `excluded` set (`config.py:1316` block) — same rationale as the existing
  `sr_*` exclusions. `Config().config_fingerprint()` MUST stay `4d665603569b9dbf`.
- **Docs rider**: add the one new README bullet described above (the S/R-bullet half is already done).

**Out of scope this iteration** (per phase spec OUT OF SCOPE — flag and exclude if attempted):
class-scaled stop/reward/simulated size and per-class PnL (J-05); named-strategy comparison,
generalized edge-report/`pnl_scan`, hold-out promotion, any champion movement or ledger row (J-06);
any second S/R computation path in the runner; any change to `v1`, `default`, the tape engine, or
`apps/frontend/`; any brokerage/order/routing/execution/paper-trading code.

## Agents Required

- **developer: yes** — backend-only implementation (strategy registry, entry grammar, runner
  extension, new route, MCP tool, config fields + fingerprint exclusion, README bullet, tests).
  Mapped to the dispatcher's own vocabulary: **backend-data: yes, frontend-ux: no** — there is no
  frontend work; the phase spec explicitly forbids any `apps/frontend/` change this iteration
  (verify via empty `git diff -- apps/frontend/`, per DoD and the J-07 frozen-frontend guard).

## Files to Create/Modify

- `apps/backend/app/config.py` -- `STRATEGY_TAPE_ID` constant (beside `STRATEGY_V1_ID` at line 22);
  `_STRATEGY_IDS_IN_ORDER` tuple + `Config.strategy_registry()` method (mirror
  `_PROFILE_IDS_IN_ORDER` / `profile_registry()` at lines 44/1171); extend `strategy_definition()`
  (line 1195) with the `structure_tape` branch; new `structure_tape`-only fields (proximity band,
  rejection/breakthrough mapping) — name them distinctly from the existing `sr_*` (J-02/J-03) and
  `level_break`/`failed_move_fade` (studies) namespaces; add every new field to
  `config_fingerprint()`'s `excluded` set (line ~1316 block, same comment-rationale style as the
  `sr_confluence_*` entries directly above it).
- `apps/backend/app/research/backtests.py` -- extend `_strategy_trades` (line 309) with the
  `structure_tape` branch; thread a `BarStore` into wherever the runner can call
  `research.levels.compute_levels` for the run's symbol (the dataset's `symbol` is already in
  `dataset_meta` read at `run()` line 226) — mirror how `dataset_store` is passed at call time
  (`start(backtest_id, *, dataset_store=...)` in `BacktestJobManager`, wired from the route via
  `get_dataset_store()`) rather than baking a `BarStore` into the constructor, so `create_backtest`
  can pass a `get_bar_store()`-sourced store the identical way. Stamp each `structure_tape` trade
  with the arming level's provenance (price/timeframe/class) inside the existing trade dict shape.
- `apps/backend/app/research/routes.py` -- new `GET /research/strategies` route (mirror
  `get_profiles` at line 1776); optionally a new `strategies.py` (or reuse `profiles.py`'s pattern
  inline) module analogous to `profiles_projection` — developer's call on file split vs. inline,
  consistent with the existing profiles precedent.
- `apps/backend/app/mcp/__init__.py` -- add `"strategies"` to `_STATIC_PATHS` (line 84) + a
  `types.Tool` entry (mirror the no-arg `backtests`/`datasets` tools).
- `apps/backend/tests/test_backtests.py` -- extend with `structure_tape` arming tests: both
  directions of both readings (rejection→fade, breakthrough→follow; long and short each), no-arm
  when the level is absent or the tape is unconfirmed, level provenance stamped on the trade,
  byte-identical re-run. Per NOTES: use the synthetic `SYN-CONFLUENCE` 3-timeframe fixture from
  `test_levels.py` for any case needing a class-A level (the committed PG fixture can never
  produce class A — only 2 timeframes).
- `apps/backend/tests/test_backtests_api.py` / a new `test_strategies_api.py` (mirror
  `test_profiles_api.py`) -- `POST /research/backtests` accepts `strategy_id=structure_tape`
  (previously 422); `GET /research/strategies` lists `[v1, structure_tape]` in order + champion;
  unregistered strategy id still 422 (never coerced).
- Wherever `strategy_definition("v1")` byte-identity / `config_fingerprint` pinning is currently
  asserted (`test_profile_equivalence.py` and/or `test_backtests.py` — confirm exact location) --
  extend/add the assertion that `v1`'s definition is unchanged and the fingerprint stays
  `4d665603569b9dbf` with the new fields present but excluded, plus a real-threshold counter-test.
- `apps/backend/tests/test_mcp_server.py` -- extend `EXPECTED_TOOLS` with `strategies`; add a
  byte-identity test against a seeded non-empty result (mirror the `backtests`/`levels` pattern).
- `apps/backend/tests/test_no_execution_path.py` -- no code change expected (it's a repo-wide
  grep-guard, not a per-feature test); just confirm it still passes with the new "position size"
  strategy-grammar field naming (the guard already exists — do not weaken or special-case it).
- README.md `AUTO:capabilities` -- add the one new bullet (strategy registry + `structure_tape` +
  `strategies` MCP tool); the S/R-bullet confluence/A-B-C extension is already done (see Alignment
  check).
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-4-dev.md` -- NEW dev handoff.

`apps/frontend/` MUST NOT change this iteration (confirm via `git diff -- apps/frontend/` empty).

## Known Considerations (flagging, not deciding, for the developer)

- **No-lookahead across a tick-level replay is the highest-risk correctness point here.** The
  backtest path (`_PathPoint` list) is tick-level tape events; bars/levels are a separate, coarser
  structure. Computing levels ONCE (e.g. as-of the dataset's end) and reusing that single snapshot
  for entries earlier in the path would leak lookahead and must NOT be done — a level used to arm
  an entry at event timestamp T must be computed `as_of=T` (or otherwise provably restricted to
  bars ≤ T), exactly like `GET /research/levels` already guarantees. Since levels are needed only
  for entry arming (not exits — those reuse existing exit machinery untouched), this only needs
  evaluating while flat, the same shape v1's combo loop already checks every event.
- **Existing "level-cross" precedent to reuse a technique from, not the data**: `studies.py`'s
  `_arm_setup_occurrences` (`studies.py:498-520`) already arms `level_break`/`failed_move_fade`
  against a single **operator-supplied hindsight level**, gated by `_control_state` — that's the
  "breakthrough" half's technique (cross + matching control state), reusable as a pattern. The
  "rejection" half (price enters a level's band AND the tape shows absorption/opposing-control,
  without necessarily crossing) has no existing analog and is genuinely new logic. Neither
  `_arm_setup_occurrences` nor its config is otherwise touched (v1/studies stay untouched).
- **Corrupt-sole-series seam (iter-2/iter-3 precedent)**: `compute_levels` aliases a corrupt sole
  bar series to `no_bar_series_for_symbol: true`. Per NOTES, decide `structure_tape`'s honest
  behaviour for that case (never silently arm on partial data) and document the decision, same as
  iter-3 did — this iteration is not expected to fix the underlying aliasing, only to not
  fabricate an arm on top of it.
- **Naming**: keep `structure_tape`-only config fields distinct from both the `sr_*` (J-02/J-03,
  which stay read-only inputs here) and the studies' `level_break`/`failed_move_fade` namespace —
  same collision discipline as iter-2.

## Key Test Scenarios

- `Config.strategy_registry()` / `GET /research/strategies` lists exactly `[v1, structure_tape]` in
  registration order plus the champion strategy id from the single pointer; an unregistered
  strategy id → 422 (never silently coerced to `v1`).
- `strategy_definition("v1")` byte-identical to its pre-iteration value; `config_fingerprint() ==
  '4d665603569b9dbf'` unchanged (new fields present but excluded, plus a real-threshold
  counter-test); observer/profile/real-data equivalence suites stay green.
- `structure_tape` arming: a trade arms only where a classified level's proximity band AND a
  confirming tape state coincide — both directions of both readings (rejection→fade,
  breakthrough→follow; long and short each); no arm when the level is absent or the tape state is
  unconfirmed; the class-A case exercised via the synthetic `SYN-CONFLUENCE` fixture.
- Each `structure_tape` trade stamps its arming level's provenance; strategy id folds into backtest
  provenance; report shows R AND $ beside the seeded null baseline; byte-identical re-run.
- `POST /research/backtests` with `strategy_id=structure_tape` succeeds (previously 422); a
  backtest under an unregistered strategy still yields an explicit `failed` record, never empty
  success.
- MCP `strategies` byte-identical to REST on a non-empty result; backend-down → explicit tool error.
- No-broker/no-execution grep-guard (`test_no_execution_path.py`) stays green unmodified.
- A symbol/dataset with no classified levels → honest empty (zero fabricated arms) for
  `structure_tape` — never a fallback to v1-like behaviour.
- Full backend suite green, zero regressions (iter-3 baseline: 1107 passed / 1 skipped / 1108
  collected); `git diff -- apps/frontend/` empty; grep confirms no J-05/J-06 code leaked in
  (`class_scaled`, `pnl_scan` generalization, champion movement) and no brokerage/execution
  identifiers introduced.
