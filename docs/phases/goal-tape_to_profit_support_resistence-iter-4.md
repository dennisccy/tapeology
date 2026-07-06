# Goal Iteration 4 — J-04: `structure_tape` as a registered, tape-confirmed structure strategy

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — never presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
  - **No lookahead.** Levels and classes computed "as of" time T use only bars at or before T; a backtest may never see a level derived from data after the moment it is used. *(critical)*
  - **No ML, no online tuning.** S/R detection, confluence scoring, class thresholds, and class-based risk are bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops in the engine, no thresholds that move at runtime.
  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **No capital or portfolio management.** Class "position size" is a per-trade simulated notional only — no account, no equity curve, no compounding projection, no real position tracking. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*

## GOAL

The research operator (and AI tools via MCP) can list the registered strategies — the frozen `v1` plus the additive `structure_tape` — and the current champion, then run a backtest under `structure_tape` whose entries fire **only** where a classified support/resistance level and a confirming tape read coincide, measured in R AND $ beside the seeded null baseline and byte-identical on re-run.

## BACKGROUND

J-01–J-03 shipped the era-4 data foundation (bar store → deterministic lookahead-free S/R levels → A/B/C confluence classes) and are stable-passing; J-04 is the next journey in the natural dependency order (J-01→J-02→J-03→**J-04**→J-05→J-06) and the explicit unblocker for J-05 (class-scaled risk) and J-06 (named-strategy comparison), which both consume the `structure_tape` strategy this iteration registers. The iter-3 evaluator explicitly recommended **J-04 at full depth**; the iter-3 coherence verdict was COHERENCE-WARN (not FAIL), so no consolidation pass is owed — the one WARN item (README S/R bullet omits confluence/A-B-C) is folded in as a trivial doc-parity rider. **Depth = full** is justified by the "Picking depth" triggers: a new canonical computation (config-owned strategy registry + tape-confirmed structure arming inside the backtest runner), a new endpoint (`GET /research/strategies`), a critical anti-goal surface (frozen `v1`/`default` byte-identity, the no-broker/no-execution grep-guard, and no-lookahead as levels feed entries), and machine-surface acceptance that needs new correctness tests beyond browser smoke. This is a single **risky** journey and is therefore planned alone (never bundled with another risky change).

Grounding from the live codebase: `Config.strategy_definition()` (config.py:1195) is the sole owner of strategy grammar (currently `v1`-only; any other id → `None`); `POST /research/backtests` already 422s on an unregistered `strategy_id` via that same method (routes.py), so registering `structure_tape` there automatically makes the backtest endpoint accept it — the runner's `_strategy_trades` (backtests.py:236) needs to interpret the new entry rule. The champion pointer already holds a `v1`/`default` pair, read verbatim by `profiles.py` (`store.get_champion_pointer()`), so `GET /research/strategies` surfaces the champion strategy id from that **same single pointer** — not a second one.

## IN SCOPE

### Backend
- [ ] **Register `structure_tape` in the config-owned strategy registry (additive).** Add a `STRATEGY_TAPE_ID = "structure_tape"` constant; extend `Config.strategy_definition()` to return the `structure_tape` grammar for that id (Data Contract row 41). `v1` and `default` are untouched — `strategy_definition("v1")` stays byte-identical and the pinned `config_fingerprint` `4d665603569b9dbf` is unmoved. Add a `_STRATEGY_IDS_IN_ORDER = (STRATEGY_V1_ID, STRATEGY_TAPE_ID)` tuple + a `Config.strategy_registry()` method mirroring the existing `profile_registry()` (built entirely from `strategy_definition`, no second copy of any id).
- [ ] **`structure_tape` entry grammar (row 41), every threshold config-owned (no magic numbers).** Entries arm when price enters a classified level's proximity band AND the tape confirms direction — rejection (`ask_absorption`/`seller_control` at resistance → short; `bid_absorption`/`buyer_control` at support → long) or breakthrough (`buyer_control` with real price impact through resistance → long; mirror for support) — reusing the engine's existing level-cross + state-native arming. The proximity band and the tape-confirmation mapping come from named config values.
- [ ] **Extend the ONE backtest runner** (`app/research/backtests.py` `_strategy_trades`) to interpret the `structure_tape` entry rule, **consuming the symbol's precomputed levels/classes from the row-39 `compute_levels` owner (`research/levels.py`) injected into the run** — single source of truth; NO second S/R computation inside the backtest runner. Each `structure_tape` trade is stamped with the strategy id and the level provenance that armed it. Exits and R/$ math reuse the existing era-3 backtest engine **unchanged** (class-scaled stop/reward/size is J-05, out of scope here).
- [ ] **New endpoint `GET /research/strategies`** serving `Config.strategy_registry()` (`v1` + `structure_tape`, in registration order) plus the current champion strategy id read **verbatim from the same `store.get_champion_pointer()` source `profiles.py` uses** (one pointer, two read views — no second champion read). Mirror the `GET /research/profiles` route shape; GET-only.
- [ ] **MCP `strategies` proxy.** Add `"strategies": "/research/strategies"` to the proxy map and a `strategies` `types.Tool`, JSON byte-identical to the REST endpoint; backend-unreachable → explicit tool error (never cached/fabricated). No mutating tool added.
- [ ] **Fingerprint hygiene (J-07 guard).** Add EVERY new `structure_tape` config field (proximity band, tape-confirmation constants, any strategy-specific field not reusing v1's) to the `config_fingerprint()` `excluded` set so the frozen `default` fingerprint stays `4d665603569b9dbf`. Keep market-data-vendor names out of `config.py` and the engine/canonical modules (vendor specifics stay in `providers/adapters/`).

### Docs (doc-parity rider — closes iter-3 COHERENCE-WARN)
- [ ] Extend the README `AUTO:capabilities` support/resistance bullet to also describe confluence zones + A/B/C conviction classes (it currently describes only the J-02 half). Add one plain-language bullet for the new strategy registry (`v1` + `structure_tape`) and the `strategies` MCP tool, in operator language (no edge/advice framing).

### Frontend (if applicable)
- None. This is a machine surface (REST + MCP + backtest report). **`apps/frontend/` MUST NOT change** — J-07 frozen-frontend guard.

### New user-facing capability
List registered strategies and the champion via `GET /research/strategies` (+ MCP `strategies`), and run a `structure_tape` backtest that arms only at classified levels confirmed by the tape — the tape read is, for the first time, anchored to price structure instead of read in a vacuum, as an additive, honestly-measured strategy beside the frozen `v1`.

### New information displayed
`GET /research/strategies`: the strategy registry (`v1` + `structure_tape`) and the current champion strategy id. A `structure_tape` backtest report (row 31): per-trade entries/exits stamped with strategy id + the level that armed them, R AND $ beside the seeded null baseline.

### New user actions
`GET /research/strategies` (+ MCP `strategies`); `POST /research/backtests` with `strategy_id=structure_tape` (existing endpoint, newly-accepted strategy value).

### UI surface changes
None. Nav skeleton (Cockpit · Journal · Studies · Performance) unchanged — machine surface only.

### Product surface delta
The product gains its first structure-aware strategy: a versioned, additive `structure_tape` strategy in a real registry, judged only by the era-3 measurement machine, never touching `v1`/`default`.

### Blueprint conformance
J-04's canonical home is `GET /research/strategies` + `GET /research/backtests/{id}` + MCP `strategies`/`backtests` — the machine-surface home already listed in the blueprint IA table (J-04 row). No nav skeleton change; no `blueprint.reapproval-requested`.

### Data-contract additions
**None.** Rows **40** (strategy registry + champion pointer) and **41** (`structure_tape` strategy definition) were registered in `blueprint.md` at baseline (iter-0) and are exactly what this iteration builds — no NEW displayed value is introduced, so no blueprint edit is required. The `structure_tape` per-trade "level provenance" is carried **inside the existing row-31 backtest report** produced by the one `BacktestJobManager`, reading row-39 levels — not a new owner or endpoint. The champion strategy id reuses the single row-33/40 pointer.

## OUT OF SCOPE

- **Class-scaled stop / reward / simulated size and per-class PnL breakdown (J-05, row 42).** `structure_tape` entries arm this iteration; class-scaled risk/size math and the per-class report are the next journey. This iteration reuses the existing (non-class-scaled) exit/R/$ machinery unchanged.
- **Named-strategy comparison, the generalized edge-report/`pnl_scan` path, and hold-out promotion (J-06, row 43).** No champion movement, no ledger row this iteration.
- **Any second S/R computation path** in the backtest runner — levels are read from the row-39 `compute_levels` owner only.
- **Any change to `v1`, `default`, the engine defaults, the tape engine, or `apps/frontend/`.**
- **Any brokerage / order / routing / execution / paper-trading code** — none may exist (grep-guarded).

## DEFINITION OF DONE

- [ ] **J-04 passes (machine surface; browser QA SKIPPED, `Frontend Present: no`):** `GET /research/strategies` lists `v1` plus the additive `structure_tape` (a registry, not a hard-coded strategy) and the champion strategy id; a `structure_tape` backtest arms **only** where a classified level and a confirming tape state coincide, stamps strategy id + level provenance, and reports per-trade entries/exits with R AND $ beside the seeded null baseline — verified by the backend acceptance suite.
- [ ] **J-07 stays green:** `default` profile + `v1` strategy byte-identical (engine equivalence suite green), `Config().config_fingerprint() == '4d665603569b9dbf'` unchanged (all new `structure_tape` fields excluded), and `git status apps/frontend/` empty.
- [ ] **Required-still-passing J-01, J-02, J-03 remain green** (full backend suite; the row-39 levels the strategy consumes are unchanged and single-sourced).
- [ ] **MCP `strategies` JSON is byte-identical** to `GET /research/strategies` (asserted by test); backend-down → explicit tool error.
- [ ] **Determinism:** a `structure_tape` backtest re-runs byte-identical.
- [ ] **No-execution grep-guard passes:** no broker/order/routing/execution/paper-trading code anywhere; "position size" (named in the strategy grammar) transmits nothing.
- [ ] **No-lookahead preserved:** the levels feeding entries at as-of T use only bars ≤ T (the strategy reads the row-39 lookahead-free `compute_levels`).
- [ ] Unit/integration tests pass; no regressions (full backend suite green).
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none. `Frontend Present: no` — machine surface, so browser QA is skipped with this documented reason; the J-04 acceptance IS the backend test suite. J-07's frozen-frontend leg is verified by `git status apps/frontend/` empty + the engine equivalence suite, not screenshots (consistent with iters 1–3; the iter-0 lesson requiring screenshots applies only when `apps/frontend/` actually changes — it does not here).
- **Unit/integration:**
  - `Config.strategy_registry()` / `GET /research/strategies` lists exactly `[v1, structure_tape]` in registration order + the champion strategy id from the single pointer; an unregistered strategy id → 422 (never silently coerced to `v1`).
  - `strategy_definition("v1")` byte-identical to its pre-iteration value; `config_fingerprint() == '4d665603569b9dbf'` unchanged; engine/observer/profile equivalence green.
  - `structure_tape` arming: a trade arms **only** where a classified level's proximity band and a confirming tape state coincide — assert both directions of both readings (rejection→fade and breakthrough→follow, long and short); assert **no** arm where the level is absent or the tape is unconfirmed.
  - Each `structure_tape` trade stamps its level provenance; the strategy id folds into backtest provenance; the report shows R AND $ beside the seeded null baseline; the same backtest re-runs byte-identical.
  - MCP `strategies` byte-identical to REST on a non-empty result.
  - No-broker/no-execution source grep-guard is green.
- **Error cases:** unknown `strategy_id` → 422 (not coerced); a backtest requested under an unregistered strategy → explicit `failed` record (never empty success); MCP `strategies` with the backend down → explicit tool error; a symbol/dataset with **no** classified levels → honest empty (zero fabricated arms).

## NOTES

- **Lesson iter-1 (applies — this iteration touches `config.py`):** `config_fingerprint()` hashes every non-excluded `Config` field against the pinned `4d665603569b9dbf`, so ANY new field silently moves the `default` fingerprint and breaks J-07 unless added to the `excluded` set — exclude EVERY new `structure_tape` field. And `config.py` (plus the canonical/engine modules) is vendor-name-forbidden even in comments (`test_real_data_gate.py`); keep vendor specifics in `providers/adapters/`.
- **Lesson iter-3 (applies — this iteration consumes A/B/C classes):** the committed real PG bar fixture stores only two timeframes (1h, 1d) and can NEVER produce a class-A confluence zone (honest real output `[C,C,C,C,C,B]`); any `structure_tape` arming test that needs a class-A level must use the synthetic 3-timeframe `SYN-CONFLUENCE` fixture in `test_levels.py`, not the committed PG fixture.
- **Lesson iter-2 (applies — this iteration consumes `compute_levels`):** the levels endpoint currently aliases a corrupt *sole* bar series to `no_bar_series_for_symbol`; decide `structure_tape`'s behaviour when its symbol's sole bar series is corrupt (surface an honest state; do not silently arm on partial data).
- **Coherence-critical single-source guard:** `structure_tape` MUST read levels/classes from the row-39 `compute_levels` owner (`research/levels.py`) and the champion from the single `store.get_champion_pointer()` — do NOT add a second S/R computation in `backtests.py` or a second champion source. iter-3 coherence PASS hinged on zero second-path hits; the coherence-auditor will FAIL a duplicate.
- **Design shortcut confirmed in code:** `POST /research/backtests` already 422s on an unregistered `strategy_id` via `Config.strategy_definition()`, so registering `structure_tape` there makes the backtest endpoint accept it with no route change — the work is the runner's `_strategy_trades` interpretation of the new entry rule plus the new `GET /research/strategies` read endpoint.
- Depth = full per the iter-3 evaluator recommendation and the "Picking depth" triggers (new endpoint + new canonical computation + critical anti-goal surface + tests beyond browser smoke). Prior verdict was CONTINUE (not ESCALATE).
