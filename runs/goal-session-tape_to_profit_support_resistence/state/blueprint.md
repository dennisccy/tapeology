# App Blueprint — tape_to_profit_support_resistence

> **Tapeology — structure-and-tape era (era 4).** Drafted at baseline (iter-0) from
> `docs/goal.md` (Product Shape, Key Capabilities 1–6, journeys J-01–J-07).
> The archived eras' contract **and** the era-3 measurement-machine contract —
> Data Contract rows **1–37** in `runs/goal-session-tape_to_profit/state/blueprint.md`
> (and its referenced predecessor) — remain **in force, unchanged** (foundation invariant:
> eras 1–3 are frozen foundation and MUST NOT regress). This blueprint registers the era-4
> additions (rows **38–43**) and changes **no nav skeleton** — every new surface this era is a
> machine surface (REST + MCP + report/CLI).
>
> **Governing principles (carried, still law):** every canonical value computed ONCE and read
> verbatim by REST / WS / UI / markdown reports / MCP; the `default` profile is frozen
> (byte-equivalence-tested) and the live cockpit uses it exclusively; the `v1` strategy is
> frozen and byte-identical; structure work is **additive and versioned only**; levels/classes
> carry **no lookahead** (as-of T uses only bars ≤ T); train and hold-out are never pooled;
> promotion only on hold-out survival (net R AND net $, n ≥ configured minimum); no broker /
> order / execution / paper-trading code anywhere (grep-guarded); every $ figure appears beside
> its R, its n, its train/hold-out basis, its fee/slippage assumptions, its null baseline, and
> the "simulated — not indicative of live results" register; "position size" is a simulated
> notional that transmits nothing; the MCP server is a read-only thin HTTP proxy over the
> canonical REST API — byte-identical JSON, never a second computation path.

## Information Architecture

**Layout shell:** unchanged dark instrument-panel with persistent top bar. **The nav skeleton is
UNCHANGED this era** — Cockpit · Journal · Studies · Performance. The rendered nav still reads
`GET /meta/ui-routes` (foundation row 35). Era 4's new capabilities (bars, levels, confluence
classes, the `structure_tape` strategy, its class-scaled PnL, and its honest comparison to `v1`)
are **machine surfaces only** — REST endpoints, MCP proxies, and report/CLI artifacts. A future
levels view is explicitly out of the data-foundation scope.

```
Tapeology (top bar: Cockpit · Journal · Studies · Performance)   [UNCHANGED from era 3]
├── Cockpit  /                        — live tape cockpit (archived eras; UNCHANGED; default profile only)
├── Journal  /journal (+ /journal/[id]) — thesis journal + review detail (archived; UNCHANGED)
├── Studies  /studies                 — replay studies (archived; UNCHANGED)
└── Performance  /performance         — PnL-ledger table + current champion (era 3; UNCHANGED)
```

**Machine surfaces** (no nav home — read-only, spawned on demand):
- `python -m app.mcp` (stdio) — MCP tools proxying the canonical REST API over HTTP; era 4 adds
  the thin proxies `bars`, `levels`, `strategies` (byte-identical to their REST endpoints)
- `python -m app.research.pnl_scan` / `python -m app.research.edge_report` — era-3 sweep + edge
  report, **generalized this era to evaluate a NAMED strategy** (not only the champion)
- `reports/pnl/pnl-history.md` — pure render of the stored PnL-ledger rows (unchanged owner)

**Feature / journey homes** (machine-surface routes; UI-facing rows ≤2 clicks from nav):

| Feature / journey | Canonical home | Nav section |
|---|---|---|
| J-01 multi-timeframe bar store | API `/research/bars*` + MCP `bars` | machine |
| J-02 support/resistance levels | API `GET /research/levels` + MCP `levels` | machine |
| J-03 confluence zones + A/B/C classes | API `GET /research/levels` (same endpoint) + MCP `levels` | machine |
| J-04 `structure_tape` registered strategy | API `GET /research/strategies` + `GET /research/backtests/{id}` + MCP `strategies`/`backtests` | machine |
| J-05 class-scaled stop/reward/simulated size | API `GET /research/backtests/{id}` (per-class breakdown) + MCP `backtests` | machine |
| J-06 `structure_tape` measured vs `v1` champion | CLI `pnl_scan`/`edge_report` `--out` report + `GET /research/pnl/ledger` | machine |
| J-07 regression sentinel (eras 1–3 unchanged) | `/`, `/journal`, `/studies`, `/performance` + full backend suite + engine equivalence | Cockpit/Journal/Studies/Performance |

No watchlist, no multi-symbol view, no charting, no order/execution affordance anywhere — unchanged.

## Data Contract

Rows **1–37** (engine snapshot; tape state/features/history; thesis/journal/analytics/studies;
taxonomy; stamps; datasets; backtests; PnL ledger; indicator profiles + champion pointer;
strategy `v1`; UI route map; scan reports; baseline-edge report) are **in force as approved** in
`runs/goal-session-tape_to_profit/state/blueprint.md` — owners and endpoints unchanged; the live
cockpit keeps reading them under the `default` profile only. Era-4 additions:

| # | Value / entity | Computed by (single owner) | Served by (single endpoint) | Notes |
|---|---|---|---|---|
| 38 | **Bar series** (symbol, timeframe, UTC window, feed, bar count, checksum; immutable OHLC candle list) | NEW bar-store module (single writer; checksum computed at registration, verified on every load) — mirrors dataset store (row 30). Ingested via a NEW neutral `RawBar` on the adapter seam (`providers/adapters/base.py`) + Alpaca `fetch_bars(symbol,start,end,timeframe)` calling `get_stock_bars` with `TimeFrame` (Minute/Hour/Day/Week/Month) | `POST /research/bars` (record/register), `GET /research/bars`, `GET /research/bars/{id}` + MCP `bars` | files under a gitignored bar data dir + a committed miniature multi-timeframe CI fixture; immutable once recorded (re-record → conflict); free-tier Alpaca serves historical bars with ~15-min recency delay + rate limit — backfills throttle and never fetch the most-recent bar; missing credentials surface the EXISTING explicit unavailable state (503), never fabricated bars; capability-probe finding (feed SIP\|IEX, lookback range, rate behaviour) recorded honestly |
| 39 | **Support/resistance levels + A/B/C confluence classes** (per level: price, timeframe, type [swing-pivot \| prior-period-extreme], touch count, strength = timeframe-weight × touch count; per zone: member levels w/ timeframes, score = timeframe-weighted sum of member strengths, class A\|B\|C) | NEW S/R + confluence module — computed ONCE, **no lookahead** (as-of T uses only bars ≤ T), no ML / no fitting; swing pivots (fractal extreme over ±N neighbours) + prior-period extremes (prior day/week/month high/low/close); confluence clusters within a config tolerance band | `GET /research/levels` (symbol + as-of → levels + classes together) + MCP `levels` | every parameter config-sourced (pivot lookback N, touch tolerance, confluence band, class thresholds) — no magic numbers; a zone is class A only when the confluence criteria are met, honestly labelled otherwise; byte-identical re-runs; read verbatim by REST + MCP; keyless-verifiable on the committed bar fixture |
| 40 | **Strategy registry + champion pointer** (registered strategies list: `v1` + `structure_tape`; current champion strategy id) | config-owned strategy registry (additive — extends the row-34 strategy-grammar + row-33 champion-pointer pattern; `v1`/`default` byte-identical). The champion pointer is the SAME single row-33 pointer — NOT a second one | `GET /research/strategies` + MCP `strategies`; champion ALSO summarized via existing `GET /research/profiles` (row 33) — ONE pointer, two read views | additive-only; strategy id folds into backtest provenance (row 31); no strategy id but `v1`/`structure_tape` served until more are registered by a later journey |
| 41 | **`structure_tape` strategy definition** (entries arm where price enters a classified level's proximity band AND the tape confirms direction — rejection [absorption / opposing control holds → fade] or breakthrough [control with price impact through the level → follow]; class-scaled stop [A ≈ 1bp beyond the level, B/C wider], reward target [R:R toward the next opposing level], simulated position notional [better class → larger]) | config-owned strategy grammar `Config.strategy_definition("structure_tape")` (extends row 34; reuses the engine's existing level-cross + state-native arming; every stop/target/size multiple config-owned) | read by the ONE row-31 backtest runner (`app.research.backtests.BacktestJobManager`); echoed verbatim in each report's provenance | no ML / no runtime mutation; all thresholds/fees/minimums from config — no magic numbers; grep-guarded no-execution — "position size" is a simulated notional that places / routes / transmits nothing |
| 42 | **Per-class PnL breakdown** (net R AND net $, n, per train/hold-out split, per class A/B/C) within a `structure_tape` backtest report | the SAME ONE row-31 backtest runner (`BacktestJobManager`) — the class dimension of the same computation, computed ONCE and persisted (NOT a second computation path) | `GET /research/backtests/{id}` (row-31 endpoint; no second endpoint) + MCP `backtests` | each $ beside its R, n, split, null baseline, and the "simulated — assumed fees/slippage — not indicative of live results" register; sub-minimum-n classes labelled "insufficient sample"; deterministic re-runs |
| 43 | **Named-strategy comparison report** (`structure_tape` vs `v1` per split: net R AND net $, n, per-dataset breakdown; `survivor` true iff it beats the champion on **hold-out** net R AND net $ at n ≥ the configured minimum; train-only wins labelled overfit) | the SAME row-36 sweep (`app.research.pnl_scan`) / row-37 edge-report (`app.research.edge_report`) path, **generalized to evaluate a NAMED strategy** (not only the champion) — reuses the ONE `BacktestJobManager`; NEVER a second R/$/edge computation | `--out` report file (machine-readable); a promotion appends ONE row-32 PnL-ledger row + moves the row-40/row-33 champion pointer | train + hold-out never pooled; on the fixtures (n < minimum) it honestly reports **no survivor at exit 0**; a promotion moves the champion pointer WITHOUT modifying `default`, `v1`, or any engine default; deterministic under fixed seeds |

**Persistence (scoped, unchanged discipline).** Backtests + PnL ledger live in the journal-scoped
SQLite (`TAPEOLOGY_JOURNAL_DB`) via the existing single-writer queue + versioned-migration rules.
Datasets live under `TAPEOLOGY_DATASET_DIR`; **bar series live under a new gitignored bar data dir**
(committed multi-timeframe CI fixture excepted), immutable + checksum-verified on load. The live
cockpit's tape is never persisted — recording bars is an explicit credentialed research action.

**MCP tool set** (row-numbered proxies, not owners). Era-3 tools unchanged: `tape_state`,
`tape_features`, `tape_history`, `journal`, `analytics`, `studies`, `datasets`, `backtests`,
`pnl_ledger`, `taxonomy`, `ui_route_map`, `get_endpoint` (GET-only, allowlisted to `/tape/*`,
`/research/*`, `/meta/*`). **Era 4 adds: `bars`, `levels`, `strategies`** — each JSON byte-identical
to its REST endpoint; backend down ⇒ explicit tool error, never cached/fabricated data. No mutating
MCP tool exists.
