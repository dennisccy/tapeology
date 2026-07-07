# App Blueprint — structure_ui

<!--
Coherence contract for the "Structure, made visible" UI-surfacing interlude (eras 1–4 frozen
foundation). This interlude adds exactly ONE read-only page and ONE additive nav-registry entry;
it OWNS no value and computes nothing. Every value below is already owned by an era-1–4 canonical
source — the Structure view reads each verbatim. The coherence-auditor hard-fails any second
computation, second endpoint, or client-side recomputation of these values.
-->

## Information Architecture

**Layout shell:** top-bar nav + main content, dark-only. The top bar is **data-driven**: it renders
whatever `GET /meta/ui-routes` returns (`nav: true` entries), never a hardcoded client list
(`apps/frontend/components/NavBar.tsx`).

**Navigation skeleton** (persistent top bar — every feature lives under one of these):

```
Tapeology
├── Cockpit       /                         (live tape cockpit — unchanged)
├── Journal       /journal  (+ /journal/[id])  (unchanged)
├── Studies       /studies                  (backtest jobs — unchanged)
├── Performance   /performance              (unchanged)
└── Structure     /structure   [NEW]        (read-only structure surface — this interlude)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 — S/R levels + A/B/C confluence zones on a price chart | `/structure` (Levels & Zones section) | Structure |
| J-02 — strategy registry (`v1` + `structure_tape`) + champion badge | `/structure` (Registry section) | Structure |
| J-03 — `structure_tape`-vs-`v1` comparison + per-class A/B/C breakdown | `/structure` (Comparison section) | Structure |
| J-04 — foundation regression sentinel | existing surfaces `/`, `/journal`, `/studies`, `/performance` (no new home) | all sections |

All three visible journeys (J-01/J-02/J-03) are **sections of the single `/structure` page** — one
new route, not three. The nav entry is owned by `apps/backend/app/meta.py` `UI_ROUTES` (served via
`GET /meta/ui-routes`); adding it is the ONLY backend edit in this interlude.

## Data Contract

Every value the Structure view displays is already owned by an era-1–4 canonical source and is read
**verbatim**. The Structure view registers **no new owned value** and performs **no new computation**
(no client-side grading, PnL math, aggregation, or champion resolution). "Computed by" and "Served by"
below are the *single* existing owners — the Structure page may only re-format what these endpoints return.

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Bar series + checksums (candles for the chart) | bar store (`research/bars` store) | `GET /research/bars` (+ `/{bar_series_id}`) | read verbatim; chart candles only |
| S/R levels (price / timeframe / type) | `research/levels.py` (`_level`, `_swing_pivots`, `_prior_period_extremes`; no lookahead) | `GET /research/levels?symbol=&as_of=` | one price line per level, labelled by timeframe |
| A/B/C confluence-zone class + score | `research/levels.py:_grade_zone` / `_confluence_zone` | `GET /research/levels` (`zone.class`) | badge taken from `zone.class`; **never** recomputed from breadth/score |
| Registered strategies (`v1`, `structure_tape`) + class-scaled params | `Config.strategy_definition` (config-owned) | `GET /research/strategies` | entry rule, exit precedence, `stop_bps_by_class` / `r_multiple_by_class` / `size_multiple_by_class` |
| Champion pointer (founding `v1`/`default`) | `JournalStore.get_champion_pointer` (store-owned) | `GET /research/strategies` + `GET /research/profiles` | one pointer, two read views; UI moves it **never** |
| Backtest aggregates (n, net R, net $, `win_rate`, `max_drawdown_r`) | `research/backtests.py:_aggregate` | `GET /research/backtests/{backtest_id}` | run via `POST /research/backtests` (Studies job/poll pattern) |
| Per-class A/B/C breakdown + `insufficient_sample` | `research/backtests.py:_aggregate_by_class` | `GET /research/backtests/{backtest_id}` (`aggregates_by_class`) | sub-minimum-n shown "insufficient sample" verbatim |
| PnL-ledger rows + founding baseline | `research/pnl_ledger.py:ledger_projection` | `GET /research/pnl/ledger` | baseline row beside the comparison |
| Simulated-honesty register string ("simulated — assumed fees/slippage — not indicative of live results") | `REGISTER` constant (`research/backtests.py:142`; imported — never re-defined — by `research/pnl_ledger.py`) | `GET /research/backtests/{backtest_id}` (`register`) + `GET /research/pnl/ledger` (`register`) | read from the payload verbatim; **never** a hardcoded frontend literal (mirrors `/performance` `pnl-register`, whose page notes "no frontend copy of it exists"). Surfaced on `/structure` for the first time by J-03 (iter-3). |
| Datasets (for choosing the comparison input) | dataset store (`research/datasets`) | `GET /research/datasets` | immutable, checksummed |
| UI route map (the nav itself) | `apps/backend/app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | Structure entry added here; nav renders it verbatim |

**No new owned value. No divergent serialization. The `/structure` page is a pure read/visualize
surface** — any number that diverges from its API/MCP payload is a defect. `config_fingerprint` stays
`4d665603569b9dbf`; `research/levels.py`, `research/backtests.py`, `research/strategies.py`,
`config.py`, and the engine are untouched beyond the additive `meta.py` `UI_ROUTES` entry.
