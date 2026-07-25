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
`/structure` query-param prefill); the new rows below belong to `/desk`, which does not exist in
the codebase yet (confirmed at baseline: no `apps/frontend/app/desk/`, no `desk_universe.py` /
`desk_screen.py`, no `/research/desk/*` routes, no desk `Config` fields, no `.data/universe/` dir).
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
| Bar coverage index (existing, internal) | `bar_index.py` (`BarIndex`, derived/rebuildable) | *(no REST route today — used only as a FastAPI dependency, `get_bar_index`, inside existing bars routes)* | J-02's new coverage payload is a NEW desk-owned READ over this same index, not a duplicate index |
| Datasets (tick evidence) | `datasets.py` + `dataset_index.db` | `GET /research/datasets*` | J-02/J-03's "tick evidence" badge reads dataset-registration presence only — 11 recorded symbols at era open |
| Setups / touch events | `setups.py` (+ scan cache) | `GET /research/setups` | unchanged |
| Edge cells + not-computed payload | `edge_report.py` | `GET /research/edge-report` | unchanged |
| Edge-report compute snapshot | `edge_report_compute.py` (`EdgeReportComputeManager`, :108) | `POST/GET /research/edge-report/compute*` | the compute-manager pattern J-02's top-up and J-03's screen compute both copy (single-flight, pollable progress, cancellable) |
| PnL ledger rows | `pnl_ledger.py` | `GET /research/pnl/ledger` | append-only; untouched this era |
| Strategy registry + champion pointer | `strategies.py` / store | `GET /research/strategies` | untouched this era |
| Profiles (`default`) | `profiles.py` | `GET /research/profiles` | untouched this era |
| Research labels (taxonomy) | `taxonomy.py` | `GET /research/taxonomy` | unchanged |
| Route / nav inventory | `app/meta.py` `UI_ROUTES` (single owner) | `GET /meta/ui-routes` | 2 rows today (confirmed live); J-04 appends the `/desk` row here — never hand-edit `NavBar.tsx` |
| `config_fingerprint` | `Config.config_fingerprint()` | embedded in research payload stamps | pinned `08e471b10130e1e2` all era (confirmed live); §0.4 Path A only for every new desk field — no field that shapes a served value may be an env var |

**New rows this era (each a new desk-owned value, exactly one owner — per `docs/goal.md`'s Product
Shape table; none exist in the codebase yet):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Universe snapshots + membership | new `app/research/desk_universe.py` (exact module name at build discretion) | `GET /research/desk/universe` (list + latest; fetch via `POST /research/desk/universe/fetch`) | frozen JSON `.data/universe/universe-<date>-<checksum12>.json` is the source of truth; membership is metadata only, NEVER a signal input to any computation or rank formula |
| Per-member bar coverage + freshness | same desk-universe module, reading `bar_index` only (never re-hashing `BarStore`) | `GET /research/desk/coverage` OR a block of the universe payload — ONE home, to be fixed by whichever iteration builds J-02 and reflected here immediately | must not create a second coverage index; GETs are cache-reads, never computes |
| Screen snapshots, rank rows, skip rows | new `app/research/desk_screen.py` | `GET /research/desk/screen` (latest / `?date=` / snapshot list) | frozen JSON screen snapshot, append-only, keyed on (screen_date, as_of, universe snapshot id, `config_fingerprint`, bar-store signature); bands/classes reproduced from the unchanged `tradability.py`/`levels.py` owners above, byte-for-byte, never recomputed independently |
| Top-up / screen compute progress | desk compute manager (copies the `EdgeReportComputeManager` pattern above) | `GET /research/desk/*/compute` poll endpoints (+ `POST .../compute`, `POST .../compute/cancel`) | single-flight; page-load GETs never trigger a compute (the 5C lesson) |
| Route list (now 3 rows) | `app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | same owner as the unchanged row above — J-04 appends the `/desk` entry there, in the same iteration the page ships |

<!-- The exact REST sub-path for coverage (dedicated endpoint vs. a block of the universe payload)
is an explicit build-time decision per docs/goal.md Key Capability 2 — whichever the J-02 iteration
picks, it is registered here as the ONE home before any other code reads coverage data. This is a
goal.md-deferred decision, not a decomposer assumption. -->
