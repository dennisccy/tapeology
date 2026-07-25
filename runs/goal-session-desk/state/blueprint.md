# App Blueprint — desk

<!--
This is the coherence contract for the whole app. The goal-decomposer drafts it at baseline; you
approve it once (edit anything, then `--resume`); the coherence-auditor enforces it every iteration.

Era B ("The Desk") builds ADDITIVELY on the two-page product left by the "Clean Slate" demolition
era (Cockpit `/` + Structure `/structure`, `config_fingerprint` `08e471b10130e1e2` confirmed live
against the current tree, 15 read-only MCP tools confirmed via `EXPECTED_TOOLS` in
`apps/backend/tests/test_mcp_server.py`). Every row below is taken near-verbatim from
`docs/goal.md`'s `## Product Shape` section (which itself names the canonical owners) plus the
J-01..J-07 Must-have journeys. The Cockpit/Structure rows are carried forward UNCHANGED (this era
reads them, never mutates them, with the single sanctioned exception of J-05's additive
`/structure` query-param prefill); the new rows below belong to `/desk`, which does not exist as a
PAGE yet (updated at iter-2: `desk_universe.py`/`desk_routes.py` + `GET/POST /research/desk/universe`
shipped J-01, iter-1; a desk-coverage module + `GET /research/desk/coverage` + the top-up compute
manager ship J-02, iter-2 — see the Data Contract rows below. `desk_screen.py`, `.data/universe/`
screen snapshots, and the `/desk` page itself remain unbuilt — J-03/J-04's job).
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content area, dark-only, dense, terminal-grade
(unchanged shell). Nav is data-driven from `app/meta.py` `UI_ROUTES` (the single owner — currently
2 rows, confirmed live) — never hand-edit a nav component; J-04 adds the third row there.

**Navigation skeleton** (target state after this era closes — `Desk` does not exist yet at
baseline):

```
Tapeology
├── Cockpit      /             live/sim/historical tape watch, engine panels (recent trades,
│                               observations, event log, quote, features, tape state), the
│                               PriceChart (candles, timeframe switch, viewport paging, S/R band
│                               overlay, live tape moving bars), provenance badge — UNCHANGED
│                               this era
├── Structure    /structure    bar library + Yahoo fetch + provenance, levels/zones, tradable
│                               map, case studies, edge report (compute + warm cells), strategy
│                               registry + champion pointer, the StructureChart — UNCHANGED this
│                               era except J-05's additive `?symbol=&asof=` Load-form prefill +
│                               auto-Load (no other behavior change)
└── Desk         /desk         [NEW, this era — not yet built] universe snapshot + coverage
                                summary, screen briefing (ranked rows + honestly-grouped skipped
                                rows), provenance line (universe snapshot id/date, as_of,
                                fingerprint, bar-store signature), Run Screen + Top-up buttons
                                w/ live progress + cancel, browsable screen history, per-row
                                drill-in to `/structure`
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Universe ingestion (fetch/register/list, honest parser) | *(backend module + store; surfaced as the provenance line + universe metadata on `/desk` — no standalone page)* | Desk |
| J-02 Coverage + explicit bar top-up | *(backend; surfaced as per-row coverage/tick-evidence badges on `/desk` — no standalone page)* | Desk |
| J-03 Screen compute + append-only ledger | *(backend POST/CLI compute; served to `/desk`)* | Desk |
| J-04 `/desk` briefing page | `/desk` | Desk |
| J-05 Screen history + `/structure` drill-in | `/desk` (history list) → `/structure?symbol=<sym>&asof=<iso>` (additive prefill) | Desk, Structure |
| J-06 MCP contract v3 (17 read-only tools) | *(MCP tool surface; no page — `desk_universe`/`desk_screen` proxy the two GETs below)* | — |
| J-07 Kept-product regression sentinel | `/`, `/structure` | Cockpit, Structure |

## Data Contract

Every value that appears in the UI and should read the same everywhere is registered here with
**one** canonical computing source and **one** serving endpoint. No page may recompute or re-fetch
these from anywhere else; UI may only re-format what the canonical endpoint returns.

**Unchanged owners (carried forward from the Clean Slate era's blueprint — this era reads them
verbatim, never re-implements, re-tunes, or re-grades them):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Bands / tradable-map scores | `tradability.py` (`compute_tradability`, :381) + durable `tradability_cache.db` | `GET /research/tradability` | the screen's per-row "best band/class/score" reads this verbatim for the same symbol/as_of — never recomputed independently |
| Levels / zones | `levels.py` | `GET /research/levels` | unchanged |
| Bars / candles | `bars.py` (`BarStore`) | `GET /research/bars`, `GET /research/candles` | unchanged; coverage reads the derived `bar_index`, never re-hashes this store |
| Bar coverage index (existing, internal) | `bar_index.py` (`BarIndex`, derived/rebuildable) | *(no REST route today — used only as a FastAPI dependency, `get_bar_index`, inside existing bars routes)* | J-02 (iter-2) is a NEW desk-owned READ over this same index, not a duplicate index — plus a minimal, additive extension to `BarIndex`'s public read API (exposing the already-existing `window_end_utc` column via `BarIndexHit`/a new accessor) for the coverage freshness field; no DB-schema change, no change to `.lookup()`/`.insert()`'s existing contract (see `assumptions.md` iter-2) |
| Datasets (tick evidence) | `datasets.py` + `dataset_index.db` | `GET /research/datasets*` | J-03's "tick evidence" badge (screen row summary) reads dataset-registration presence only — 11 recorded symbols at era open; NOT part of J-02's coverage payload |
| Setups / touch events | `setups.py` (+ scan cache) | `GET /research/setups` | unchanged |
| Edge cells + not-computed payload | `edge_report.py` | `GET /research/edge-report` | unchanged |
| Edge-report compute snapshot | `edge_report_compute.py` (`EdgeReportComputeManager`, :108) | `POST/GET /research/edge-report/compute*` | the compute-manager pattern J-02's top-up (iter-2) and J-03's screen compute both copy (single-flight, pollable progress, cancellable) |
| PnL ledger rows | `pnl_ledger.py` | `GET /research/pnl/ledger` | append-only; untouched this era |
| Strategy registry + champion pointer | `strategies.py` / store | `GET /research/strategies` | untouched this era |
| Profiles (`default`) | `profiles.py` | `GET /research/profiles` | untouched this era |
| Research labels (taxonomy) | `taxonomy.py` | `GET /research/taxonomy` | unchanged |
| Route / nav inventory | `app/meta.py` `UI_ROUTES` (single owner) | `GET /meta/ui-routes` | 2 rows today (confirmed live); J-04 appends the `/desk` row here — never hand-edit `NavBar.tsx` |
| `config_fingerprint` | `Config.config_fingerprint()` | embedded in research payload stamps | pinned `08e471b10130e1e2` all era (confirmed live); §0.4 Path A only for every new desk field — no field that shapes a served value may be an env var |

**New rows this era (each a new desk-owned value, exactly one owner — per `docs/goal.md`'s Product
Shape table):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Universe snapshots + membership | `app/research/desk_universe.py` (shipped J-01, iter-1) | `GET /research/desk/universe` (list + latest; fetch via `POST /research/desk/universe/fetch`) | frozen JSON `.data/universe/universe-<date>-<checksum12>.json` is the source of truth; membership is metadata only, NEVER a signal input to any computation or rank formula |
| Per-member bar coverage + freshness | new desk-coverage module (shipped J-02, iter-2; module name at build discretion, e.g. `desk_coverage.py`), reading `bar_index` only (never re-hashing `BarStore`) | `GET /research/desk/coverage` — dedicated endpoint, fixed at iter-2 (resolved; see the note below the table) | payload: `{"universe_snapshot_id": str \| null, "timeframes": ["1h","4h","1d","1w"], "members": [{"symbol": str, "per_timeframe": {"<tf>": {"has_bars": bool, "latest_window_end_utc": str \| null}}}]}`; honest-empty (`universe_snapshot_id: null`, `members: []`) before any universe snapshot exists — HTTP 200, never 404; pinned timeframe set `{1h, 4h, 1d, 1w}` verified against `levels.py`/`config.py`/`yahoo.py` at iter-2 (excludes 5m/1m per the desk anti-goal's explicit "no 5m/1m in the desk top-up"; excludes 8h/15m/1mo — outside Yahoo's `_INTERVAL_MAP`/resample set); must not create a second coverage index; GETs are cache-reads, never computes (T-4) |
| Top-up compute progress | new desk top-up compute manager (shipped J-02, iter-2; copies `EdgeReportComputeManager`'s bookkeeping shape verbatim, `edge_report_compute.py:108`) | `POST /research/desk/topup/compute` (trigger), `GET /research/desk/topup/compute` (poll), `POST /research/desk/topup/compute/cancel` (cancel) — mirrors `/research/edge-report/compute*` (`routes.py:1268/1293/1302`) exactly | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "started_utc": str, "finished_utc": str \| null, "error": str \| null, "progress": {"pairs_total": int, "pairs_done": int, "outcomes": [{"symbol": str, "timeframe": str, "outcome": "reused"\|"fetched"\|"failed", "detail": str \| null}]}}`; single-flight; page-load GETs never trigger a compute (the 5C lesson); process-scoped bookkeeping, never a research value |
| Screen snapshots, rank rows, skip rows | new `app/research/desk_screen.py` (not yet built — J-03) | `GET /research/desk/screen` (latest / `?date=` / snapshot list) — not yet built | frozen JSON screen snapshot, append-only, keyed on (screen_date, as_of, universe snapshot id, `config_fingerprint`, bar-store signature); bands/classes reproduced from the unchanged `tradability.py`/`levels.py` owners above, byte-for-byte, never recomputed independently |
| Screen compute progress | desk screen compute manager (not yet built — J-03; will copy the `EdgeReportComputeManager`/desk-topup-compute-manager pattern above) | `POST/GET /research/desk/screen/compute*` (not yet built — open placeholder, exact subpath to be fixed by the J-03 iteration and reflected here immediately) | single-flight; page-load GETs never trigger a compute (the 5C lesson) |
| Route list (now 3 rows) | `app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | same owner as the unchanged row above — J-04 appends the `/desk` entry there, in the same iteration the page ships |

<!-- RESOLVED at iter-2: coverage's REST sub-path is the dedicated `GET /research/desk/coverage`
endpoint (row above), per docs/goal.md Key Capability 2's build-time decision — registered here as
the ONE home before any other code reads coverage data. The SCREEN compute path (its own row above)
remains an open placeholder for whichever iteration builds J-03. -->
