# Tapeology

- Cockpit
[Cockpit](http://localhost:3301/)
- Structure
[Structure](http://localhost:3301/structure)
# Structure

Load a symbol and an as-of time to see its tradable level map — at most a handful of quality-scored bands, not the full raw level set — and read the 3-way strategy edge report.

Tradable Map is the default view, read verbatim from GET /research/tradability; toggle "Show raw levels" for the underlying S/R levels and confluence zones (off by default). Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline; Edge Report compares v1, structure_tape, and structure_tape_map over recorded windows, register included. Fetching bars below (Yahoo Finance, with Alpaca for history beyond Yahoo's limits) is this page's one explicit write action — everything else, including the strategy registry/champion and the structure_tape-vs-v1 comparison, is read-only. Every value on this page is read verbatim from its canonical endpoint — nothing here is recomputed in the browser.

## Tradable Map

A distilled tradable level map — at most a handful of quality-scored bands per side, clustered and scored from the raw S/R levels under morning-markup as-of discipline. Every band's range, side, class, quality score, member count, and round-number flag below is read verbatim from GET /research/tradability — nothing here is recomputed.

Choose a symbol and an as-of time, then Load, to see its tradable level map.

## Case Studies

Every band-touch event this store has scanned, read verbatim from GET /research/setups — reaction, forward returns, and (once a dataset was recorded around it) the tape timeline. The filters below narrow the already-served rows; nothing here is recomputed.


| Table Content |
|---|
| symbol | session | band |
| AAPL | 2025-01-02 | resistance · 251.6720440162376–251.6720440162376 · Unclassified |
| AAPL | 2025-01-02 | support · 247.84647977817443–248.8302001953125 · Unclassified |
| AAPL | 2025-01-03 | support · 243.85–243.85 · Unclassified |
| AAPL | 2025-01-04 | resistance · 241.82009887695312–243.5 · Class A |
| AAPL | 2025-01-06 | resistance · 241.82009887695312–243.5 · Class A |
| AAPL | 2025-01-06 | resistance · 243.53–245.155 · Class A |
| AAPL | 2025-01-06 | resistance · 247.02–248.25 · Class A |
| AAPL | 2025-01-07 | resistance · 243.45–245.15 · Class A |
| AAPL | 2025-01-07 | resistance · 245.155–246.28 · Class A |


## Edge Report

The v1 / structure_tape / structure_tape_map comparison over recorded event windows, read verbatim from GET /research/edge-report — per-cell n, R, and $ carry the full simulated register; train and hold-out are never pooled. An empty or all-insufficient-sample report is an honest, valid outcome.

Edge report not computed yet.

The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute.

## Fetch bars

Fetch real historical bars for a symbol and UTC date range, on this explicit click. One click fetches all six supported timeframes (1w, 1d, 4h, 1h, 5m, 1m; 4h is derived from real 1h bars). The end date is included in full. Yahoo Finance is the keyless source, and it keeps intraday history for a limited time — 1m for the last 30 days, 5m for 60, 1h for 730; 1d and 1w are unlimited. When the requested range reaches further back than that, the remainder is fetched from Alpaca (credentialed), recorded separately, and stitched into the charts by timestamp. Alpaca's SIP feed includes pre- and post-market bars, so the older part of a range can cover a wider session than the Yahoo part. Each timeframe reports below exactly which vendor covered which dates; an already-fetched window is served from storage. On success, the Tradable Map and Levels & Zones sections above load the fetched symbol automatically.

## Registry

Read-only: every strategy field and the champion below are read verbatim from GET /research/strategies — nothing here is recomputed in the browser.

### Champion

Confirmed identical to the champion served by GET /research/profiles — one store pointer, two read views.

### v1

Exit precedence: r_stop → reward_target → state_flip → horizon (dataset_end forces a close at stream end).

### structure_tape

Exit precedence: r_stop → reward_target → state_flip → horizon (dataset_end forces a close at stream end).

stop (bps by class)


| Table Content |
|---|
| A | 1 |
| B | 5 |
| C | 10 |


reward target (R-multiple by class)


| Table Content |
|---|
| A | 3 |
| B | 2 |
| C | 1 |


size (multiple by class)


| Table Content |
|---|
| A | 2 |
| B | 1 |
| C | 0.5 |


### structure_tape_map

Exit precedence: r_stop → reward_target → state_flip → horizon (dataset_end forces a close at stream end).

stop (bps by class)


| Table Content |
|---|
| A | 1 |
| B | 5 |
| C | 10 |


reward target (R-multiple by class)


| Table Content |
|---|
| A | 3 |
| B | 2 |
| C | 1 |


size (multiple by class)


| Table Content |
|---|
| A | 2 |
| B | 1 |
| C | 0.5 |


## Comparison

Read-only: every aggregate, per-class value, and the register line below are read verbatim from GET /research/backtests — nothing here is recomputed in the browser. Running a comparison starts an offline research job over an already-recorded dataset; it places nothing and never moves the champion.

#### Champion (moved never by this view)

#### Founding baseline (PnL ledger)

Choose a dataset, then Run comparison, to compare structure_tape against v1.
