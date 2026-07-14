# App Blueprint — tradable_wall (Era 5B "The Tradable Wall")

<!--
Coherence contract for the whole app. Drafted by goal-decomposer at baseline; auto-approved by
run-goal.sh unless --require-blueprint-approval. The coherence-auditor enforces it every iteration.
Era 5B layers ON TOP of eras 1–5 — the nav is FROZEN (no new entry); all new work lives inside
/structure and the cockpit. Single source of truth is anti-goal #6 (critical): each value below is
computed once by ONE module and served by ONE endpoint; REST/WS/UI/MCP/reports read it verbatim.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content; dark-only, dense, terminal-grade
(`lightweight-charts` for price overlays). Nav is **frozen** for Era 5B — no new top-level entry
(anti-goal "No new nav entry"). New capability lands inside existing homes only.

**Navigation skeleton** (persistent top nav — every feature lives under one of these):

```
Tapeology
├── Cockpit        /                     (PriceChart + tape-state markers; live-mode chart stays hidden)
├── Journal        /journal  · /journal/[id]
├── Studies        /studies
├── Performance    /performance
└── Structure      /structure            (Era 5B sections: Tradable Map · Case Studies · Edge Report)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Tradable level map (≤10 bands) | `/structure` → **Tradable Map** (default view) | Structure |
| J-02 Case-study registry | `/structure` → **Case Studies** table + row drill-in | Structure |
| J-03 Real tape at the wall (recorded timeline) | shown inside the **Case Studies** drill-in (tape timeline) | Structure |
| J-04 Edge report (3-way) | `/structure` → **Edge Report** section | Structure |
| J-05 `/structure` declutter (map default, raw behind toggle) | `/structure` | Structure |
| J-06 Cockpit confluence (band overlay + descriptive chip) | `/` → `PriceChart` (sim/historical only) | Cockpit |
| J-07 Foundation regression sentinel | no UI home — guards all surfaces | (cross-cutting) |

Era-5 fetch control + "Yahoo Finance" provenance badge on `/structure` are **preserved** (foundation).

## Data Contract

Each value is computed once by ONE module and served by ONE endpoint; UI/MCP/reports may only
re-format what the canonical endpoint returns (anti-goals #6 single-source, #8 read-only MCP). MCP
proxies `tradability` / `setups` / `edge_report` are byte-identical read-only mirrors of the same GETs
— they add NO second computation.

**New (Era 5B) — each with exactly one owner:**

| Value / entity | Computed by (single module) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Tradable level map — bands (price range, side, quality score, member refs, round-number flag, inherited class) | `app/research/tradability.py` | `GET /research/tradability?symbol=&as_of=` | Consumes `compute_levels` output **verbatim** (never re-detects); class is a projection of member zones' A/B/C (class stays owned by `levels.py`); morning-markup as-of (prior-session close) |
| Touch events + reaction labels (`rejected`/`broke`/`chopped`) + forward returns + case registry | `app/research/setups.py` | `GET /research/setups`, `GET /research/setups/{id}` | Reaction defs + horizons config-owned, pre-registered; drill-in tape timeline for recorded events = frozen engine replay (tape **states** owned by `TapeEngine`, read via `/tape/{ticker}/history`) |
| Edge-report cells — strategy × class × side × reaction (n, R stats, $ with full register, null baseline) | `app/research/edge_report.py` | `GET /research/edge-report` | 3-way `v1` / `structure_tape` / `structure_tape_map`; train & hold-out never pooled; feeds never pooled. **NOTE:** file currently exists as the era-3 champion-ONLY CLI (`python -m app.research.edge_report`) — Era 5B extends it additively to serve the 3-way endpoint, reusing the one `BacktestJobManager` path |
| `structure_tape_map` definition + chip rejection/breakthrough state mapping + chip labels | config (`app/config.py`) exposed via `app/research/strategies.py` | `GET /research/strategies` | NEW registry entry beside frozen `v1`/`structure_tape`; mapping+labels read here (never client-hardcoded); `config_fingerprint` MUST stay `4d665603569b9dbf` |
| Recorded tick datasets (append-only, checksummed, feed-stamped, split-frozen) | existing `DatasetStore` (`app/research/datasets.py` + store) | `GET /research/datasets`, `GET /research/datasets/{id}` | Event-windowed credentialed recording via existing `record_from_source`; `feed` stamped verbatim from adapter tier (`iex` on free keys, never equated to `sip`); splits frozen at registration |

**Existing owners Era 5B reads verbatim (unchanged — frozen foundation):**

| Value / entity | Computed by | Served by | Notes |
|---|---|---|---|
| Raw levels + A/B/C confluence zones | `app/research/levels.py` | `GET /research/levels` | Frozen: 5 bps touch / 20 bps cluster params; byte-identical output |
| Bar series + checksums + Yahoo provenance | `app/research/bars.py` (+ `bar_index.py` rebuildable cache) | `GET /research/bars`, `GET /research/bars/{id}` | Era-5 store-first flow; `bar_index` is a cache, never a source of truth |
| Backtest aggregates | `app/research/backtests.py` | `GET /research/backtests`, `/backtests/{id}` | Additive `structure_tape_map` arming path only; existing strategy outputs stay byte-identical |
| Tape five-state timeline | frozen `TapeEngine` | `GET /tape/{ticker}/history` | States `buyer_control`/`seller_control`/`bid_absorption`/`ask_absorption`/`unclear`; fingerprint `4d665603569b9dbf` |
| Taxonomy labels | `app/research/taxonomy.py` | `GET /research/taxonomy` | Unchanged |
| UI route map | (meta router) | `GET /meta/ui-routes` | Unchanged |

<!-- The chip's on-screen condition is a display conjunction of TWO canonical reads
(price-in-band from /research/tradability × mapped tape state from /tape history, mapping from
/research/strategies) — zero client recomputation of scores, classes, reactions, PnL, or provenance. -->
