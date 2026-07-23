# App Blueprint — clean_slate

<!--
This is the coherence contract for the whole app. The goal-decomposer drafts it at baseline; you
approve it once (edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

This session ("The Clean Slate") is a DEMOLITION interlude, not additive feature work: the target
Information Architecture below is deliberately smaller than what's live in the repo today. Every row
is taken near-verbatim from docs/goal.md's `## Product Shape` section (which itself names the
canonical owners) plus the I-1..I-9 Demolition inventory. Nothing in this file is a new decision —
it is the existing contract, minus the journal-era surfaces this era removes.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content area, dark-only, dense, terminal-grade
(unchanged shell). Nav is data-driven from `app/meta.py` ROUTES (the single owner) — never hand-edit
a nav component.

**Navigation skeleton** (target state after this interlude closes):

```
Tapeology
├── Cockpit      /             live/sim/historical tape watch, engine panels (recent trades,
│                               observations, event log, quote, features, tape state), the
│                               PriceChart (candles, timeframe switch, viewport paging, S/R band
│                               overlay, live tape moving bars), provenance badge
└── Structure    /structure    bar library + Yahoo fetch + provenance, levels/zones, tradable map,
                                case studies, edge report (compute + warm cells), strategy registry
                                + champion pointer, the StructureChart
```

**Removed this interlude** (grep-provably gone from code/routes/nav/MCP/types/tests by J-02 — these
are NOT relocated, they render the app's honest 404): `/journal` + `/journal/[id]` (manual thesis
journal), `/studies` (replay studies workbench), `/performance` (analytics scoreboard).

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 backend demolition + byte-identical relocations | *(backend-only; no page — verified via kept-route byte-identity + 404s on deleted routes)* | — |
| J-02 kept two-page product (frontend + WS demolition) | `/`, `/structure` | Cockpit, Structure |
| J-03 MCP contract v2 (15 read-only tools) | *(MCP tool surface; no page)* | — |
| J-04 fingerprint epoch bump (§0.4 Path B) | *(backend/config + `reports/pnl/pnl-history.md`; no page)* | — |
| J-05 kept-product regression sentinel | `/`, `/structure` | Cockpit, Structure |

## Data Contract

Every KEPT canonical value keeps its EXISTING single owner **unchanged** this interlude — this era
deletes surfaces around these values, it does not touch how any of them are computed or served
(verbatim intent of `docs/goal.md`'s Product Shape + Foundation invariants §2):

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Bands (tradable map) | `tradability.py` (+ durable cache) | `GET /research/tradability` | unchanged |
| Touch events / setups | `setups.py` (+ scan cache) | `GET /research/setups` | unchanged |
| Edge cells + not-computed payload | `edge_report.py` | `GET /research/edge-report` | unchanged |
| Edge-report compute snapshot | `edge_report_compute.py` | `POST/GET /research/edge-report/compute*` | unchanged |
| PnL ledger rows | `pnl_ledger.py` | `GET /research/pnl/ledger` | append-only; J-04 appends one new-epoch founding row beside old rows (old fingerprint stamps never rewritten) |
| Bars / candles | `bars.py` | `GET /research/bars`, `GET /research/candles` | unchanged |
| Levels / zones | `levels.py` | `GET /research/levels` | unchanged |
| Strategy registry + champion pointer | `strategies.py` / store | `GET /research/strategies` | unchanged |
| Datasets | `datasets.py` | `GET /research/datasets*` | J-01 relocates `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/`REFERENCE_SOURCE_ID`/`_load_reference_window` here from `studies.py` byte-identically — values unchanged, only the home moves |
| Backtests | `backtests.py` | `GET/POST /research/backtests*` | J-01 relocates the `r_basis` helper here from `marks.py` byte-identically — values unchanged, only the home moves |
| Profiles (`default`) | `profiles.py` | `GET /research/profiles` | unchanged |
| Research labels (taxonomy) — SLIMS in J-01/J-02 | `taxonomy.py` (single owner, stays) | `GET /research/taxonomy` | after this interlude serves ONLY the `feed_basis` block (read by `FeedBasisBadge.tsx:46-60`) + source labels (`sim`/`iex`/`sip`/`yahoo`); thesis/verdict/stance/study label families are deleted with their owning surfaces |
| Route / nav inventory | `app/meta.py` ROUTES (single owner) | `GET /meta/ui-routes` | after J-02: exactly Cockpit + Structure |
| `config_fingerprint` | `Config.config_fingerprint()` | embedded in research payload stamps | stays `4d665603569b9dbf` through J-01–J-03; moves to ONE new pin in J-04 only (§0.4 Path B) — never touched by any other commit |

**Removed entirely this interlude, with their owners** (no replacement, no new home — J-01/J-02):
active thesis, thesis journal + detail, verdict timeline, management stance, entry checks, grades,
excursions, hints (active + log), study jobs/results, analytics aggregates. The WS frame becomes the
engine projection only (no additive research keys).
