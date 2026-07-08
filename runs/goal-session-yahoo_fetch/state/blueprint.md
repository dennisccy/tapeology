# App Blueprint — yahoo_fetch

<!--
Coherence contract for Era 5 "The Library" (bars/structure side, keyless) — eras 1–4 + the
structure-UI interlude are frozen foundation. This era adds EXACTLY ONE new owned value
(bar-series provenance `feed="yahoo"`) and NO new computation of any existing value. The
`/structure` page gains ONE new write action (the explicit Yahoo fetch); it still reads every
displayed value verbatim from its canonical endpoint and recomputes nothing. The SQLite bar
index OWNS NOTHING — it is a derived, rebuildable cache over the JSON BarStore. The
coherence-auditor hard-fails any second computation, second endpoint, second bar store, or
client-side recomputation of these values.
-->

## Information Architecture

**Layout shell:** top-bar nav + main content, dark-only. The top bar is **data-driven** — it
renders whatever `GET /meta/ui-routes` returns (`nav: true` entries), never a hardcoded client list
(`apps/frontend/components/NavBar.tsx`). **Nav skeleton is UNCHANGED this era** (no re-approval).

**Navigation skeleton** (persistent top bar — every feature lives under one of these):

```
Tapeology
├── Cockpit       /                          (live tape cockpit — unchanged)
├── Journal       /journal  (+ /journal/[id])   (unchanged)
├── Studies       /studies                   (backtest jobs — unchanged)
├── Performance   /performance               (unchanged)
└── Structure     /structure                 (structure surface — gains ONE fetch control this era)
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 — fetch real Yahoo bars keyless, stored append-only + checksummed | `/structure` (Fetch control) → `GET /research/bars` (+ `/{id}`), MCP `bars` | Structure |
| J-02 — full timeframe set (`1w 1d 4h 1h 5m 1m`), 4h resampled-from-1h | `/structure` (Fetch control → timeframe selector) → `GET /research/bars` | Structure |
| J-03 — store-first quick reuse via derived SQLite index | `/structure` (re-fetch served instantly) → `GET /research/bars?symbol=&timeframe=` | Structure |
| J-04 — real S/R levels + A/B/C zones on real Yahoo bars | `/structure` (Levels & Zones section — existing) → `GET /research/levels` | Structure |
| J-05 — fetch-from-the-app control + "Yahoo Finance" provenance badge | `/structure` (Fetch control + provenance badge) | Structure |
| J-06 — foundation regression sentinel | existing surfaces `/`, `/journal`, `/studies`, `/performance` (no new home) | all sections |

All visible journeys are **sections of the single `/structure` page** — no new route. The one new
UI element is the **fetch control** (symbol + timeframe + date range + "Fetch from Yahoo Finance"
button) and its provenance badge; it is the ONLY new explicit write action in the app.

## Data Contract

Every value the `/structure` view displays is read **verbatim** from its single canonical endpoint;
the UI recomputes nothing (no client-side grading, PnL math, aggregation, provenance labelling, or
champion resolution). This era adds **exactly ONE** new owned value (`feed="yahoo"`) and **no** new
computation of any existing value.

| Value / entity | Computed / owned by (single module) | Served by (single endpoint) | Notes |
|---|---|---|---|
| **Bar-series provenance `feed="yahoo"`** — **NEW (only new owned value)** | canonical `BarStore` (`research/bars.py`) stamped from the **Yahoo adapter** `providers/adapters/yahoo.py` — the adapter is the sole source of the `feed` stamp (never route/client-hardcoded) | `GET /research/bars*` (the `feed` field) | append-only, checksummed; never re-tagged or pooled with `sip`/`iex`/`sim` |
| "Yahoo Finance" human label for `feed="yahoo"` | `research/taxonomy.py` `FEED_BASIS_LABELS` | `GET /research/taxonomy` | badge reads this verbatim (`FeedBasisBadge` pattern); never a hardcoded frontend literal |
| Bar series + double-sha256 checksums (candles) | canonical JSON `BarStore` (`research/bars.py`) | `GET /research/bars` (+ `/{bar_series_id}`), MCP `bars` | the **one** source of truth for bars; every served candle checksum-verified from it |
| Store-first lookup `(symbol,timeframe,window)` → `series_id` | **derived SQLite index** `research/bar_index.py` — **OWNS NOTHING**; rebuildable via `reindex()`; a cache, never a source of truth | `GET /research/bars?symbol=&timeframe=` (additive filter; no-param call byte-identical to before) | its loss/corruption loses or fabricates nothing; every hit is checksum-verified from the JSON store |
| S/R levels (price / timeframe / type) | `research/levels.py` (no lookahead) | `GET /research/levels?symbol=&as_of=`, MCP `levels` | one price line per level; **no second levels computation** this era |
| A/B/C confluence-zone class + score | `research/levels.py` (`zone.class`) | `GET /research/levels` | badge from `zone.class`; never recomputed client-side |
| Registered strategies (`v1`, `structure_tape`) + champion pointer | config-owned + `JournalStore` champion pointer | `GET /research/strategies` + `GET /research/profiles` | UI moves the champion **never**; `v1`/`default` byte-identical |
| Backtest aggregates + per-class A/B/C breakdown + `insufficient_sample` | `research/backtests.py` (`_aggregate`, `_aggregate_by_class`) | `GET /research/backtests/{id}` | sub-minimum-n shown "insufficient sample" verbatim; train/hold-out never pooled |
| PnL-ledger rows + founding baseline + simulated-honesty register | `research/pnl_ledger.py`; `REGISTER` constant (`research/backtests.py`, imported not re-defined) | `GET /research/pnl/ledger` (+ backtest `register`) | "$ never without R, n, basis"; register string never a hardcoded frontend literal |
| Datasets (immutable, checksummed) | dataset store (`research/datasets`) | `GET /research/datasets` | Yahoo research segregated from Alpaca `sip`; feeds never pooled |
| UI route map (the nav itself) | `apps/backend/app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | nav renders it verbatim; unchanged this era |

**No new second source of truth for any value.** `config_fingerprint` stays `4d665603569b9dbf`;
`config.py`, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, the
JSON `BarStore`, and the Alpaca adapter + its credentialed path stay byte-identical. The only additive
changes permitted are: the Yahoo adapter, the bar-vendor selector, sourcing the `feed` stamp from the
adapter, the SQLite index + store-first coordinator, the additive `symbol`/`timeframe` filter on `GET
/research/bars`, the `"yahoo"` taxonomy label, the `/structure` fetch control + provenance badge, and
the pinned `yfinance` dependency + allowlist entry. Any displayed number that diverges from its
API/MCP payload — or any second bar store / second levels-or-PnL computation — is a defect.
