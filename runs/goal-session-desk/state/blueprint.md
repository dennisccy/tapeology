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
manager ship J-02, iter-2 — see the Data Contract rows below. `desk_screen.py` (append-only screen
snapshots under a NEW `.data/screen/` dir, sibling of `.data/universe/`, resolved via a bare
env-var-or-sibling-default — deliberately NOT a new `Config` field) + a desk-screen compute manager
+ `GET/POST /research/desk/screen*` shipped J-03, iter-3 — see the Data Contract rows below for the
finalized shapes; the `/desk` page ITSELF SHIPPED at iter-4 (J-04) — the briefing table +
provenance line + screen-history list (read-only render) + Run Screen/Top-up buttons wired to the
J-02/J-03 compute managers, over the `UI_ROUTES` nav-skeleton row already planned below. Iter-4's
own browser-QA step never dispatched, so J-04 stayed `partial`; iter-5 is a verification-only pass
(zero product diff) that closes that evidence gap — see the Data Contract rows below for what iter-4
actually shipped. J-05's click-through-to-a-past-screen + `/structure` drill-in prefill SHIPPED at
iter-6 — reusing the ALREADY-REGISTERED `GET /research/desk/screen?date=` read verbatim (zero new
backend route/value); see the Data Contract section's note below for the finalized scope. Iter-7 is
IN BUILD: J-06 (the two `desk_universe`/`desk_screen` MCP tool proxies, zero new value/endpoint) plus
a build-time fix for audit F2 (the whole-row drill-in link had made several per-cell honesty
tooltips unreachable by hover; iter-7 consolidates them onto the row's own drill-in anchor instead) —
see the `RESOLVED at iter-7` note below.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content area, dark-only, dense, terminal-grade
(unchanged shell). Nav is data-driven from `app/meta.py` `UI_ROUTES` (the single owner — currently
3 rows, confirmed live since iter-4) — never hand-edit a nav component.

**Navigation skeleton** (current state — `Desk` shipped at iter-4):

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
│                               era except (a) J-05's additive `?symbol=&asof=` Load-form prefill +
│                               auto-Load (no other behavior change, still deferred past iter-5) and
│                               (b) iter-4's sanctioned finite-value guard on `StructureChart.tsx`
│                               (drops non-finite rows before `setData`; identical output for
│                               all-finite data) — the owner's written ratification of touching this
│                               frozen file is still PENDING (tracked in journey-history.json /
│                               iteration-state.md as an unresolved minor anti-goal item)
└── Desk         /desk         [shipped iter-4, J-04] universe snapshot + coverage summary, screen
                                briefing (ranked rows + honestly-grouped skipped rows), provenance
                                line (universe snapshot id/date, as_of, fingerprint, bar-store
                                signature — labeled "Bar-store signature", AMENDED at iter-4 per
                                audit F1: the snapshot-level value is a CHECKSUM over each member's
                                window-last-requested timestamp, not a timestamp, so the "window
                                last requested" label stays on the per-timeframe coverage badge
                                tooltip, which really is one), Run Screen + Top-up buttons w/ live
                                progress + cancel, a read-only browsable screen-history list (date +
                                counts + provenance summary only — iter-4 scope). Per-row drill-in
                                to `/structure` and click-through to a PAST screen's own rows are
                                J-05, SHIPPED at iter-6 (reusing `GET /research/desk/screen?date=`
                                verbatim — zero new endpoint). iter-5 closed the iter-4
                                browser-evidence gap (the third required screenshot — Run Screen
                                running with a second click refused — plus a saved `/desk` golden
                                replay script; `journey-scripts/J-04.json`, whose step 5 mutating
                                click iter-6 removes before its own replay lane runs it). iter-7
                                fixes audit F2 on these same rows: the whole-row drill-in link had
                                made several per-cell hover tooltips (full-precision distance/score,
                                per-timeframe freshness) unreachable — iter-7 consolidates them onto
                                the row's own drill-in anchor, with zero change to click geometry.
                                iter-11 (J-09) added a read-only "Top-up Runs" section beside
                                Screen History — see the Data Contract row below. iter-14
                                (J-10, IN BUILD) adds a read-only "Index Reconciliation"
                                section beside Top-up Runs, plus a "Reconcile Index" trigger
                                mirroring the Top-up button — see the Data Contract rows
                                below (J-10 and J-11 both shipped and GOAL_ACHIEVED-verified as
                                of iter-15). iter-15 (J-11) added a descriptive `history` column
                                (completed daily-session count + start date) to the ranked table,
                                plus a two-line addition to the row's existing composite hover
                                tooltip — no new section, no new control. iter-16 (J-12, IN BUILD)
                                adds NO new section either: history rows become selectable by their
                                own record `id` (not date) so two same-date recordings are each
                                reachable and each distinctly highlighted; the Provenance panel
                                gains the displayed snapshot's own `id` + `created_utc`; and all
                                four ledger sections (Universe, Screen History, Top-up Runs, Index
                                Reconciliation) gain an honest count-plus-filename
                                `integrity_errors` line where the ledger has any — inline
                                additions to existing sections, no new control, no new page.
                                iter-17 (J-13, GOAL_ACHIEVED) adds one more table column
                                ("band") rendering each ranked row's own already-recorded
                                `price_low`–`price_high` range beside a new `reference_close`
                                value — no new section, no new control. iter-18 (J-14, IN BUILD)
                                adds one more table column ("opposite") rendering each ranked
                                row's own recorded `opposite_band` (nearest wall on the side NOT
                                selected) plus one more line in the row's existing composite
                                hover tooltip (`bands_by_class` counts) — no new section, no new
                                control. iter-23 (J-15, IN BUILD) adds one more table
                                column ("levels") rendering each ranked row's own recorded
                                wall composition (member count + per-timeframe tally +
                                round-number badge) — no new section, no new control. iter-24 (J-16, IN BUILD) adds NO new
                                column and NO new section: it reflows the SAME disclosures
                                (plus a new `rank` cell rendering the row's own already-recorded
                                served position) to fit the page's own `max-w-7xl` width with
                                zero horizontal scroll at a compact row height -- a pure layout
                                change over already-served data, zero backend diff.
```

**Feature / journey homes** (each reachable in ≤2 clicks from the nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Universe ingestion (fetch/register/list, honest parser) | *(backend module + store; surfaced as the provenance line + universe metadata on `/desk` — no standalone page)* | Desk |
| J-02 Coverage + explicit bar top-up | *(backend; surfaced as per-row coverage/tick-evidence badges on `/desk`, plus iter-4's Top-up button — no standalone page)* | Desk |
| J-03 Screen compute + append-only ledger | *(backend POST/CLI compute; served to `/desk`)* | Desk |
| J-04 `/desk` briefing page | `/desk` | Desk |
| J-05 Screen history + `/structure` drill-in — shipped iter-6 | `/desk` (history list) → `/structure?symbol=<sym>&asof=<iso>` (additive prefill) | Desk, Structure |
| J-06 MCP contract v3 (17 read-only tools) — IN BUILD at iter-7 | *(MCP tool surface; no page — `desk_universe`/`desk_screen` proxy the two GETs below)* | — |
| J-07 Kept-product regression sentinel | `/`, `/structure` | Cockpit, Structure |
| J-08 Basis disclosure on ranked rows (measurement age) — implementation shipped iter-9; iter-10 closes the remaining literal-threshold screenshot evidence | `/desk` (ranked table column + row drill-in tooltip) | Desk |
| J-09 Top-up run ledger (append-only record of what a top-up attempted) — implementation shipped iter-11; iter-12 (lean) could not close the remaining narrated-walkthrough evidence — the lane that produces it runs after scoring at lean depth — and also surfaced a capture-order defect; iter-13 (full depth, corrected empty-before-record order) re-attempts it | *(backend; surfaced as a read-only "Top-up Runs" section on `/desk`, beside Screen History — no standalone page)* | Desk |
| J-10 Coverage-index reconciliation (drift classification + repair via the existing `BarIndex.reindex()`, append-only run ledger) — IN BUILD at iter-14 | *(backend; surfaced as a read-only "Index Reconciliation" section on `/desk`, beside Top-up Runs — no standalone page)* | Desk |
| J-11 History-depth disclosure on ranked rows (completed daily-session count + start date) — IN BUILD at iter-15 | `/desk` (ranked table column + row drill-in tooltip) | Desk |
| J-12 Snapshot addressability by id (`?id=` read on the already-registered screen endpoint; history rows select/highlight by id; provenance shows displayed snapshot's own id + created_utc; 4-ledger integrity-error disclosure) — IN BUILD at iter-16 | `/desk` (screen-history list, provenance panel, all four ledger sections) | Desk |
| J-13 Reference-close + band disclosure on ranked rows (price the wall sits at, beside the close it was measured from) — shipped iter-17, GOAL_ACHIEVED-verified | `/desk` (ranked table column + row drill-in tooltip) | Desk |
| J-14 Opposite-wall disclosure on ranked rows (nearest band on the OTHER side of price, plus a `bands_by_class` count) — IN BUILD at iter-18 | `/desk` (ranked table column + row drill-in tooltip) | Desk |
| J-15 Wall-composition disclosure on ranked rows (band member count + round-number flag + per-timeframe member tally) — IN BUILD at iter-23 | `/desk` (ranked table column) | Desk |
| J-16 Table reflow -- every disclosure legible without a sideways scroll, plus a `rank` cell rendering the row's own already-recorded served position -- IN BUILD at iter-24 | `/desk` (ranked table layout only, zero new column beyond `rank`) | Desk |
| J-17 Top-up window honesty (a fetch window derived from the frozen store, not `bar_index`; per-pair `requested_window`/`store_frozen_from`/`store_frozen_through`/`window_basis`; a new `unchanged` outcome) -- IN BUILD at iter-26 | `/desk` (existing Top-up Runs section; zero new section/control, zero new ranked-table column) | Desk |
| J-18 Screen-run ledger (append-only record of every screen run attempted; a pre-check resolves the five pins before the walk so an identical-pin re-trigger reuses instead of paying for a ~101-member recompute) -- IN BUILD at iter-29 | `/desk` (new read-only "Screen Runs" section, beside Screen History / Top-up Runs / Index Reconciliation -- no standalone page) | Desk |
| J-19 Top-up library-reach disclosure (post-fetch newest-frozen-bar date per pair, additive to the already-registered "Top-up run records" row) -- IN BUILD at iter-32 | `/desk` (existing Top-up Runs section; zero new section/control, zero new ranked-table column) | Desk |

## Data Contract

Every value that appears in the UI and should read the same everywhere is registered here with
**one** canonical computing source and **one** serving endpoint. No page may recompute or re-fetch
these from anywhere else; UI may only re-format what the canonical endpoint returns.

**Unchanged owners (carried forward from the Clean Slate era's blueprint — this era reads them
verbatim, never re-implements, re-tunes, or re-grades them):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Bands / tradable-map scores | `tradability.py` (`compute_tradability`, :381) + durable `tradability_cache.db` | `GET /research/tradability` | the screen's per-row "best band/class/score" reads this verbatim for the same symbol/as_of — never recomputed independently; J-03 (iter-3) reads this and NOTHING here changes — zero diff on `tradability.py` is a hard requirement (no new field on its return shape, even additively); iter-4 (J-04) renders these fields on `/desk` — a straight re-format of the screen row, still zero diff on `tradability.py` |
| Levels / zones | `levels.py` | `GET /research/levels` | unchanged; zero diff on its return shape too (see the row above's rationale — J-03 resolves a reference close price via `BarStore` directly, never by extending either frozen module) |
| Bars / candles | `bars.py` (`BarStore`) | `GET /research/bars`, `GET /research/candles` | coverage reads the derived `bar_index`, never re-hashes this store; iter-4 added a sanctioned, same-owner/same-endpoint priceless-row exclusion on the merged read (`_merged_rows`, backing `GET /research/candles`) plus a write-path refusal (`BarStore.record`) — the per-series read (`GET /research/bars/{id}/candles`) does NOT yet apply the same finite-price filter (coherence.md iter-4 advisory finding B2; no UI caller today, so no displayed-value divergence exists yet — close this before any page wires that route) |
| Bar coverage index (existing, internal) | `bar_index.py` (`BarIndex`, derived/rebuildable) | *(no REST route today — used only as a FastAPI dependency, `get_bar_index`, inside existing bars routes)* | J-02 (iter-2) is a NEW desk-owned READ over this same index, not a duplicate index — plus a minimal, additive extension to `BarIndex`'s public read API (exposing the already-existing `window_end_utc` column via `BarIndexHit`/a new accessor) for the coverage freshness field; no DB-schema change, no change to `.lookup()`/`.insert()`'s existing contract (see `assumptions.md` iter-2). J-03 (iter-3) adds NO further method here — it derives its bar-store signature entirely from `desk_coverage.get_desk_coverage`'s own reads. |
| Datasets (tick evidence) | `datasets.py` + `dataset_index.db` | `GET /research/datasets*` | J-03's "tick evidence" badge (screen row summary) reads dataset-registration presence only — 11 recorded symbols at era open (AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG, SPY, TSLA); NOT part of J-02's coverage payload |
| Setups / touch events | `setups.py` (+ scan cache) | `GET /research/setups` | unchanged |
| Edge cells + not-computed payload | `edge_report.py` | `GET /research/edge-report` | unchanged |
| Edge-report compute snapshot | `edge_report_compute.py` (`EdgeReportComputeManager`, :108) | `POST/GET /research/edge-report/compute*` | the compute-manager pattern J-02's top-up (iter-2), J-03's screen compute (iter-3), AND their iter-4 `/desk` UI wiring all copy (single-flight, pollable progress, cancellable) — the `NotComputedPanel`/poll-loop frontend pattern in `structure/page.tsx` is the UX precedent iter-4 mirrors for the Run Screen / Top-up buttons |
| PnL ledger rows | `pnl_ledger.py` | `GET /research/pnl/ledger` | append-only; untouched this era |
| Strategy registry + champion pointer | `strategies.py` / store | `GET /research/strategies` | untouched this era |
| Profiles (`default`) | `profiles.py` | `GET /research/profiles` | untouched this era |
| Research labels (taxonomy) | `taxonomy.py` | `GET /research/taxonomy` | unchanged |
| Route / nav inventory | `app/meta.py` `UI_ROUTES` (single owner) | `GET /meta/ui-routes` | 3 rows since iter-4 (confirmed live) — never hand-edit `NavBar.tsx`; `apps/backend/tests/test_meta_routes.py`'s route-count assertions update in the SAME commit (the file's own documented "route ships WITH its test update" precedent) |
| `config_fingerprint` | `Config.config_fingerprint()` | embedded in research payload stamps | pinned `08e471b10130e1e2` all era (confirmed live through iter-4); §0.4 Path A only for every new desk field — no field that shapes a served value may be an env var. Zero new `Config` fields through iter-4 — the pin, and `edge_report_cache._config_content_hash`, both stay exactly as iter-1 left them. |

**New rows this era (each a new desk-owned value, exactly one owner — per `docs/goal.md`'s Product
Shape table):**

| Value / entity | Computed by (single module/function) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Universe snapshots + membership | `app/research/desk_universe.py` (shipped J-01, iter-1) | `GET /research/desk/universe` (list + latest; fetch via `POST /research/desk/universe/fetch`) | frozen JSON `.data/universe/universe-<date>-<checksum12>.json` is the source of truth; membership is metadata only, NEVER a signal input to any computation or rank formula. iter-4: `UniverseStore.record` gains a corrupt-file `.exists()` guard mirroring `ScreenStore.record`'s (raises rather than silently overwriting a damaged file at the same content-checksum path) — a hygiene fix, zero change to the parse/register/serve contract or the served shape. iter-7 (J-06): `app/mcp/__init__.py` gains a `desk_universe` tool that proxies this row's own `GET /research/desk/universe` verbatim — no new value, no shape change. |
| Per-member bar coverage + freshness | `app/research/desk_coverage.py` (shipped J-02, iter-2), reading `bar_index` only (never re-hashing `BarStore`) | `GET /research/desk/coverage` | payload: `{"universe_snapshot_id": str \| null, "timeframes": ["1h","4h","1d","1w"], "members": [{"symbol": str, "per_timeframe": {"<tf>": {"has_bars": bool, "latest_window_end_utc": str \| null}}}]}`; honest-empty (`universe_snapshot_id: null`, `members: []`) before any universe snapshot exists — HTTP 200, never 404; J-03 (iter-3) reuses this function VERBATIM for every screen row's `coverage` badge — never a second coverage read. iter-4 (J-04): `/desk`'s per-row coverage badge renders each row/skip entry's OWN embedded `coverage` field (copied onto the row at screen-compute time) — NEVER a live re-fetch of this endpoint from the desk page, and the freshness value is labeled "window last requested" in the UI, never "last bar" (it describes whole-store freshness, not what the screen actually consumed — audit B9/iter-2 B2). iter-7: this freshness value's hover-reachability moves from a per-badge `title` onto the row's drill-in anchor (audit F2 fix) — the LABEL and the underlying value are unchanged. J-09 (iter-11) reads NOTHING from this row — a top-up run record describes attempts only; coverage/freshness keeps this single owner, never a second path. |
| Top-up compute progress | `app/research/desk_topup_compute.py` (`DeskTopupComputeManager`, shipped J-02, iter-2) | `POST /research/desk/topup/compute` (trigger), `GET /research/desk/topup/compute` (poll), `POST /research/desk/topup/compute/cancel` (cancel) | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "started_utc": str, "finished_utc": str \| null, "error": str \| null, "progress": {"pairs_total": int, "pairs_done": int, "outcomes": [{"symbol": str, "timeframe": str, "outcome": "reused"\|"fetched"\|"failed", "detail": str \| null}]}}`; single-flight; page-load GETs never trigger a compute; process-scoped bookkeeping, never a research value. iter-4 (J-04) is this row's FIRST UI consumer (a Top-up button on `/desk`, wired with live progress + cancel, mirroring the Edge Report Compute button pattern) — read-only wiring, zero shape change. **This row's own outcomes are still process-scoped and honestly lost on restart/supersession — J-09 (iter-11) does NOT extend or persist this row's shape; it adds a SEPARATE, new, durable row (below) that a shared writer populates from the SAME per-pair outcome values at a run's terminal state, so this row and the new one never disagree because they read the identical `run_topup` output, just at different lifetimes (in-flight/last-only vs. durable history).** |
| Screen snapshots, rank rows, skip rows | `app/research/desk_screen.py` (shipped J-03, iter-3) | `GET /research/desk/screen` — no params: `{"screens": [...lightweight meta only: id/screen_date/as_of/universe_snapshot_id/config_fingerprint/bar_store_signature/created_utc/counts — NEVER full rows/skipped...], "latest": <full snapshot>\|null}`; `?date=YYYY-MM-DD`: `{"screen": <full snapshot for that date>\|null}` — honest-empty, HTTP 200 always | Frozen JSON, append-only, one file per snapshot, keyed on 5 pins (`screen_date`, `as_of`, `universe_snapshot_id`, `config_fingerprint`, `bar_store_signature`) — an identical-pin trigger refuses a duplicate write and returns the existing snapshot (the `UniverseAlreadyRegistered` precedent). Snapshot shape: `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature, created_utc, rows: [...], skipped: [...]}`. Ranked row: `{symbol: str, side: "support"\|"resistance", band_class: "A"\|"B"\|"C"\|null, distance_bps: float>=0, band_score: float, price_low: float, price_high: float, coverage: {<tf>: {has_bars, latest_window_end_utc}}, tick_evidence: bool}` — `band_class`/`distance_bps`/`band_score`/`price_low`/`price_high` all read from ONE `compute_tradability` band per symbol (selected by the SAME `(class, distance, score)` order the screen itself ranks by — see `assumptions.md` iter-3), byte-for-byte; `coverage` reused verbatim from `desk_coverage.get_desk_coverage`; `tick_evidence` = symbol present in `DatasetStore.list()`. Skip row: `{symbol, skipped: true, reason: "no_bars"\|"no_basis", coverage: {...}, tick_evidence: bool}` — `"no_bars"` = `compute_tradability`'s own `no_bar_series_for_symbol`; `"no_basis"` = a daily series exists but no session resolves (`basis_as_of: null`) — two honest, distinct reasons, never conflated. Rank order over `rows`: `(band_class rank A>B>C>null desc, distance_bps asc, band_score desc, symbol asc)`. `bar_store_signature` = a deterministic hash over `desk_coverage`'s own per-member × per-timeframe read — never a `BarStore`/JSON-file re-hash (T-4). Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the `resolve_cache_db_path` pattern) — deliberately NOT a new `Config` field (see `assumptions.md` iter-3); `config_fingerprint` stays `08e471b10130e1e2`. **iter-4 addition (behavior, not shape):** triggering a screen compute with NO universe snapshot registered now REFUSES (an honest 4xx error naming the missing universe, mirroring the top-up CLI's own no-universe message) rather than persisting an honest-empty (`universe_snapshot_id: null, rows: [], skipped: []`) snapshot — closes audit B4; the persisted snapshot SHAPE above is unchanged, this only removes one previously-reachable (and useless) append-only entry. iter-7 (J-06): `app/mcp/__init__.py` gains a `desk_screen` tool that proxies this row's own `GET /research/desk/screen` (no-argument, default shape) verbatim — no new value, no shape change; `get_endpoint` already covers the `?date=` variant unchanged. **iter-9 addition (J-08), additive to the Ranked row shape ONLY:** `basis_as_of: str \| null` (copied verbatim from `compute_tradability`'s own `basis_as_of` — the same value `_resolve_reference_close` already consumes, zero new read) and `basis_age_days: int >= 0 \| null` (a calendar-date difference between the row's own `basis_as_of` and the snapshot's own `as_of` — matches the measured 1/2/4/12-day spread in `docs/goal.md`'s J-08 rationale) are present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks both fields, and `/desk` renders that absence as the honest "basis not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry these fields (a skip row's `reason: "no_basis"` already means no basis resolved at all — structurally exclusive). Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint. **iter-15 addition (J-11), additive to the Ranked row shape ONLY:** `history_sessions: int >= 0` (the count of `BarStore.merged_bars(symbol, "1d")` bars at or before the row's own `basis_as_of`, derived inside the SAME ascending walk `_resolve_reference_close` already performs — zero new store read) and `history_start: str | null` (that same walk's earliest such bar's own timestamp, formatted via `_iso`) are present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks both fields, and `/desk` renders that absence as the honest "history not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry these fields. Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint. **iter-16 addition (J-12), an ADDITIVE READ PARAM ONLY — zero new value, zero new owner, zero new endpoint:** `GET /research/desk/screen?id=<snapshot id>` serves that exact persisted snapshot's own already-recorded content verbatim (identical shape to `latest`/the `?date=` branch); an unknown id returns the existing honest `{"screen": null}` at HTTP 200 (the `?date=` convention, unchanged); `?id=` and `?date=` supplied together is an honest 4xx refusal, never a silent precedence rule; the read recomputes nothing and writes nothing. `desk_screen.ScreenStore` stays the ONLY owner and `GET /research/desk/screen` the ONLY serving endpoint — no stored shape change, no new module, no new route, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/` allowlist already proxies `?id=` verbatim; the `desk_screen` tool stays a byte-identical no-arg proxy; J-06's exactly-17-tool contract is unaffected). **iter-17 addition (J-13), additive to the Ranked row shape ONLY:** `reference_close: float` (copied verbatim from the `close` local `_resolve_reference_close_and_history` already returns and `compute_screen` already binds before calling `_select_best_band`/`_distance_bps` — zero new `BarStore` read, zero new accessor, zero re-derivation of which bar is the basis) is present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks the field entirely (not merely `null`), and `/desk` renders that absence as the honest "close not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry this field. `price_low`/`price_high` are UNCHANGED (already recorded on every ranked row since iter-3; this iteration only RENDERS them, in a new `band` column, beside the new `reference_close`). Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s byte-identical no-arg proxy contract covers the new field automatically; J-06's exactly-17-tool contract is unaffected). This journey discloses only — the rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) is unchanged, and no proximity/quality/threshold flag is computed anywhere. **iter-18 addition (J-14), additive to the Ranked row shape ONLY:** `opposite_band: {side: "support"|"resistance", band_class: "A"|"B"|"C"|null, price_low: float, price_high: float, band_score: float, distance_bps: float>=0} | null` (the nearest band on the side the row's own selected band is NOT on, selected from the SAME `result["bands"]` list `compute_screen` already holds and measured with the SAME `_distance_bps` helper against the row's own `reference_close` — zero second `compute_tradability` call, zero second `BarStore` read; `null` when the canonical return holds no band on the other side, never an invented band) and `bands_by_class: {A: int>=0, B: int>=0, C: int>=0, unclassified: int>=0}` (a plain count of that SAME bands list under its own four class keys, always all four present) are present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks both fields, and `/desk` renders that absence as the honest "opposite wall not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry these fields. Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s byte-identical no-arg proxy contract covers both fields automatically; J-06's exactly-17-tool contract is unaffected). This journey discloses only — neither field enters `_row_rank_key`, the rank key is unchanged, and no corridor-width/room/proximity/quality/threshold number is computed anywhere. **iter-23 addition (J-15), additive to the Ranked row shape ONLY:** `band_member_count: int >= 1` and `band_round_number: bool` (copied verbatim from the SAME band dict `_select_best_band` already returns — that band's own `member_count`/`round_number` keys, `tradability.py:343`) and `band_member_timeframes: {<tf>: int>=0}` (a plain tally of that SAME band's own `members` list by each member's own `timeframe`, in a deterministic key order — the `_bands_by_class` precedent, `desk_screen.py:298` — values summing to `band_member_count`; a timeframe with no member in this band is simply absent, never a fabricated zero) are present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks all three fields, and `/desk` renders that absence as the honest "composition not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry these fields. The band's own `members` list itself is NEVER copied onto the row, and no member price/`touch_count`/`strength` is copied. Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s byte-identical no-arg proxy contract covers all three fields automatically; J-06's exactly-17-tool contract is unaffected). This journey discloses only — neither the count nor the flag enters `_row_rank_key`, the rank key is unchanged, and no confluence-quality/evidence-depth/intraday-share/threshold judgement is computed anywhere. |
| Screen compute progress | `app/research/desk_screen_compute.py` (`DeskScreenComputeManager`, shipped J-03, iter-3) | `POST /research/desk/screen/compute` (trigger, body `{"screen_date": "YYYY-MM-DD"}` REQUIRED — 422 if absent, never defaults to today), `GET /research/desk/screen/compute` (poll), `POST /research/desk/screen/compute/cancel` (cancel) — mirrors `/research/desk/topup/compute*` exactly | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "screen_date": str, "started_utc": str, "finished_utc": str \| null, "error": str \| null, "reused": bool, "screen_id": str \| null, "progress": {"members_total": int, "members_done": int, "current": str \| null}}`; single-flight; page-load GETs never trigger a compute; process-scoped bookkeeping, never a research value; an identical-pin trigger over an already-recorded snapshot returns it without recomputing (T-6/append-only). **`reused`/`screen_id` are an iter-4 (J-04) ADDITIVE amendment to this row's shape** (the fields did not exist before iter-4): `screen_id` is the resulting persisted snapshot's own `id` (populated once the job reaches a terminal state, `null` while running or before any trigger); `reused` is `true` when that snapshot already existed under the SAME 5-pin key before this job ran (a pure re-read, zero new file written) and `false` when this job's own walk is what created it — closes audit B2 (an otherwise-indistinguishable `"done"` for a fresh compute vs. a pure reuse). Computed by the SAME `DeskScreenComputeManager`, served by the SAME two routes — no second owner, no second endpoint. |
| Route list (now 3 rows) | `app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | same owner as the unchanged row above — J-04 (iter-4) appended the `/desk` entry there in the same commit the page shipped |
| **Top-up run records (per-run outcome ledger)** — NEW at iter-11 (J-09) | new `app/research/desk_topup_log.py` (name at build discretion) | `GET /research/desk/topup/runs` | shape: `{"runs": [<lightweight meta only: id, universe_snapshot_id: str\|null, requested_window: {"start": str, "end": str}, config_fingerprint, started_utc, finished_utc, state: "done"\|"cancelled"\|"failed", pairs_total: int>=0, pairs_attempted: int>=0 — NEVER the full `outcomes` array, mirroring the screen list's meta-only convention>, ...], "latest": <same fields PLUS outcomes: [{"symbol": str, "timeframe": str, "outcome": "reused"\|"fetched"\|"failed", "detail": str\|null}, ...] byte-identical to `desk_topup_compute.run_topup`'s own return for that walk> \| null}` — honest-empty `{"runs": [], "latest": null}`, HTTP 200, before any run (never a 404 — the `desk_universe`/`desk_screen` convention). One frozen, checksummed, append-only JSON file per run (the `UniverseStore`/`ScreenStore` discipline: checksum-verified load, `record()` the only mutation, no update/delete) written EXACTLY ONCE, at a run's terminal state, by a SINGLE shared writer both `DeskTopupComputeManager`'s worker resolve path (`desk_topup_compute.py` `_work`/`_resolve`, ~:262/:282) and the CLI's `main` (~:329) call — never two write paths, never a second outcome shape, zero change to what `run_topup`/`_run_one_pair` themselves compute (`:123-188`). A run whose process ends before the writer's terminal call leaves NO record — the ledger never invents an entry for an interrupted run. Records ATTEMPTS only; bar presence/freshness keep their single existing owner (`desk_coverage.py` over `bar_index`, row above) — no second coverage path. Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the `resolve_desk_screen_dir` pattern) — deliberately NOT a new `Config` field. No MCP tool added — `get_endpoint`'s existing `/research/` allowlist (`ALLOWED_GET_PREFIXES`) already reaches this path with zero code change; J-06's exactly-17-tool contract is unaffected. See "RESOLVED at iter-11" below for the full build-time scope note. **iter-16 addition (J-12):** `GET /research/desk/topup/runs` now ALSO serves `integrity_errors` — verbatim from `TopupRunStore.list()`'s own load-time verification errors (the identical `records, errors = store.list()` tuple this route already unpacks and previously dropped) — in the exact same key/shape `GET /research/desk/screen` and `GET /research/desk/universe` already expose. Same owner (`desk_topup_log.py`), same endpoint, no new value computed, no new store field, no new route, no new `Config` field.  **iter-26 addition (J-17), additive to each per-pair outcome entry ONLY:** `requested_window: {start: str, end: str}` (the exact window that pair's fetch call sent this run), `store_frozen_from: str | null` / `store_frozen_through: str | null` (that pair's own earliest/newest frozen bar BEFORE this run's fetch, both `null` when nothing was frozen), and `window_basis: "tail" | "full_lookback"` are present on every per-pair outcome entry of every NEW top-up run from this iteration forward; every run recorded before this iteration lacks all four fields, and `/desk` renders that absence as the honest "window basis not recorded in this run" state — never backfilled, never computed at read time. The `outcome` enum gains exactly one new value, `"unchanged"` (a vendor call ran and returned only bars already frozen in the store), beside the existing `"reused"` (a store-first exact-key hit with ZERO vendor calls — meaning byte-unchanged), `"fetched"` and `"failed"`. All four new fields and the new outcome value are computed inside `_run_one_pair`'s existing walk against the SAME `BarStore.merged_bars` read `_resolve_reference_close_and_history`/`_select_daily_series` already use — never a new store, never a second read of `bar_index`'s own `window_end_utc` (which stays `desk_coverage`'s sole read). Same owner (`desk_topup_log.py`, written by the SAME single shared writer, `record_topup_run`), same endpoint (`GET /research/desk/topup/runs`) — no new Data-Contract row, no new endpoint, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/` allowlist already reaches this path with zero code change; J-06's exactly-17-tool contract is unaffected). No new ranked-table column — the fields surface only inside the ALREADY-REGISTERED Top-up Runs section's own counts line, one new descriptive tail-vs-full-lookback line, and each already-rendered failed pair's own row — so J-16's measured table width stays byte-unchanged. **iter-32 addition (J-19), additive to each per-pair outcome entry ONLY:** `store_frozen_through_after: str \| null` (that pair's own newest frozen bar, read via the SAME pure `_pair_window` accessor J-17 already calls, immediately AFTER `_run_one_pair` returns for that pair) is present on every per-pair outcome entry of every NEW top-up run from this iteration forward; a run recorded before this iteration lacks it, and `/desk` renders that absence as the honest "library reach not recorded in this run" fallback -- never backfilled, never computed at read time. Equal to the pair's own pre-fetch `store_frozen_through` for a `reused`/`unchanged`/`failed` outcome; strictly later for a `fetched` outcome that genuinely appended bars; `null` only when the pair holds nothing at all. Same owner (`desk_topup_log.py`, zero diff -- it persists `outcomes` generically), same endpoint (`GET /research/desk/topup/runs`), same shared writer (`record_topup_run`) -- no new Data-Contract row, no new endpoint, no new `Config` field, no new MCP tool. Surfaces only inside the ALREADY-REGISTERED Top-up Runs latest-run detail as one new descriptive line (newest reach date + pair count) plus a list of pairs recorded earlier -- no new ranked-table column, no new Top-up Runs summary-table column, so J-16's width contract and every stored golden replay script (`J-09.json`/`J-17.json`) stay byte-unchanged. |
| **Coverage-index reconciliation run records (durable ledger)** — NEW at iter-14 (J-10) | new `app/research/desk_index_reconcile.py` (name at build discretion) | `GET /research/desk/coverage/reconcile/runs` (exact path at build discretion) | shape: `{"runs": [<lightweight meta only: id, config_fingerprint, started_utc, finished_utc, state: "done"\|"cancelled"\|"failed", series_on_disk: int>=0, rows_indexed_before: int>=0, rows_indexed_after: int>=0 — NEVER the full drift/store-error detail, mirroring the topup-run-list's meta-only convention>, ...], "latest": <same fields PLUS drift_before: {"unindexed_series": [{"series_id","symbol","timeframe"}], "orphan_index_rows": [{"series_id"}], "stale_checksum_rows": [{"series_id"}]}, drift_after: <same three-bucket shape, expected empty for every pair this run repaired>, store_errors: [{"file","error"}] — verbatim from `BarStore.list()`'s own `errors`> \| null}` — honest-empty `{"runs": [], "latest": null}`, HTTP 200, before any run (never a 404 — the `desk_universe`/`desk_screen`/`desk_topup_log` convention). One frozen, checksummed, append-only JSON file per run (the `TopupRunStore` discipline: checksum-verified load, `record()` the only mutation, no update/delete), written EXACTLY ONCE at a run's terminal state by a SINGLE shared writer. Repairs ONLY through the EXISTING `BarIndex.reindex(store)` (`bar_index.py:198`) — zero diff to `bar_index.py`/`bars.py` (no new accessor, no schema change, no new index) and zero diff to `desk_coverage.py`/`tradability.py`/`levels.py` (coverage/freshness keep their single existing owner, `desk_coverage.get_desk_coverage` over `bar_index` — this row records the REPAIR only, never a second coverage path). Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the `resolve_desk_topup_log_dir` pattern) — deliberately NOT a new `Config` field. No MCP tool added — `get_endpoint`'s existing `/research/` allowlist already reaches this path with zero code change; J-06's exactly-17-tool contract is unaffected. No PnL-ledger append (this row's SSOT proof stands "in place of" one, per goal.md's own J-10 acceptance text). See "RESOLVED at iter-14" below for the full build-time scope note. **iter-16 addition (J-12):** `GET /research/desk/coverage/reconcile/runs` now ALSO serves `integrity_errors` — verbatim from the reconciliation run store's own load-time verification errors, in the exact same key/shape as the three sibling desk GETs above. Same owner, same endpoint, no new value computed, no new store field, no new route, no new `Config` field. |
| **Coverage-index reconciliation compute progress** — NEW at iter-14 (J-10) | same new module (a compute-manager class mirroring `DeskTopupComputeManager`'s shape — single in-flight job slot, atomic snapshot publish, cooperative cancel) | `POST /research/desk/coverage/reconcile/compute` (trigger), `GET /research/desk/coverage/reconcile/compute` (poll), `POST /research/desk/coverage/reconcile/compute/cancel` (cancel) — exact subpaths at build discretion, mirrors `/research/desk/topup/compute*` | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "started_utc": str, "finished_utc": str \| null, "error": str \| null, "progress": {...phase/counters at build discretion, the `DeskScreenComputeManager.progress` precedent}}`; single-flight (a second trigger while running returns the unchanged existing snapshot, `started: false`); page-load GETs never trigger a compute (T-4/5C); process-scoped bookkeeping, honestly lost on restart, never a research value — the SAME contract every compute manager in this app already carries. This row's own terminal resolution is what calls the SINGLE shared writer that populates the durable row above, exactly once — the two rows can never disagree because they share one computation, just different lifetimes (the J-02/"Top-up compute progress" vs. J-09/"Top-up run records" precedent). No CLI warmer this iteration (see "RESOLVED at iter-14" below). |
| **Screen run records (per-run outcome ledger)** — NEW at iter-29 (J-18) | new `app/research/desk_screen_log.py` (name at build discretion) | `GET /research/desk/screen/runs` | shape: `{"runs": [<lightweight meta only: id, screen_date, universe_snapshot_id: str\|null, config_fingerprint, bar_store_signature: str\|null, started_utc, finished_utc, state: "done"\|"cancelled"\|"failed", reused: bool, members_total: int>=0, members_attempted: int>=0, screen_id: str\|null — NEVER the full ranked/skipped breakdown, mirroring the topup/reconcile list's meta-only convention>, ...], "latest": <same fields PLUS ranked_count: int>=0, skipped_by_reason: {"no_bars": int>=0, "no_basis": int>=0}, and — on "failed" only — error: str (the exception detail verbatim) and failed_member: str (the member the walk was on when it raised)> \| null}` — honest-empty `{"runs": [], "latest": null}`, HTTP 200, before any run (never a 404 — the `desk_universe`/`desk_screen`/`desk_topup_log`/reconcile convention); also serves `integrity_errors` in the same key/shape its sibling desk GETs already use (the J-12 rule). One frozen, checksummed, append-only JSON file per run (the `TopupRunStore`/reconcile-run-store discipline: checksum-verified load, `record()` the only mutation, no update/delete) written EXACTLY ONCE, at a run's terminal state, by a SINGLE shared writer both `DeskScreenComputeManager`'s resolve path (`desk_screen_compute.py`, its `_work`/`_resolve`) and the CLI's `main` call — never two write paths. A run whose process ends before the writer's terminal call leaves NO record. **Every pin is resolved through the accessor that already owns it** (`desk_screen.screen_as_of`, `UniverseStore.list()`'s latest record id, `Config.config_fingerprint()`, `desk_screen.compute_bar_store_signature` over `desk_coverage` — zero new derivation, zero new value) — the SAME resolution `run_screen_and_record` (`desk_screen_compute.py:73`) now performs BEFORE the walk, so a `ScreenStore.find_by_key` hit on those five pins short-circuits to `reused=true`/`members_attempted=0` with ZERO `compute_tradability` calls, and a miss walks every member byte-identically to today. This journey changes NO walk behavior and NO recorded-snapshot shape — `desk_screen.ScreenStore` stays the ONLY owner of screen snapshots/rows/skip rows and `GET /research/desk/screen` their ONLY serving endpoint; this row records the RUN only. Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the `resolve_desk_topup_log_dir` pattern) — deliberately NOT a new `Config` field. No MCP tool added — `get_endpoint`'s existing `/research/` allowlist already reaches this path with zero code change; J-06's exactly-17-tool contract is unaffected. No PnL-ledger append (this row's SSOT proof stands "in place of" one, per goal.md's own J-18 acceptance text). See "RESOLVED at iter-29" below for the full build-time scope note. |

<!-- RESOLVED at iter-2: coverage's REST sub-path is the dedicated `GET /research/desk/coverage`
endpoint (row above), per docs/goal.md Key Capability 2's build-time decision — registered here as
the ONE home before any other code reads coverage data.

RESOLVED at iter-3: the screen compute path is `/research/desk/screen/compute*` (row above),
mirroring the topup trio exactly; the screen snapshot/row/skip shapes above are the CONTRACT J-03's
dev must ship byte-for-byte — registered here BEFORE the build, the iter-1/iter-2 precedent. Two
build-time interpretation calls (best-band selection + distance_bps; the reference-close-price
source) and one Config-discipline call (zero new field for the screen store's directory) are logged
in `assumptions.md` iter-3 — read those three entries before implementing `desk_screen.py`.

RESOLVED at iter-4: four build-time decisions for J-04's `/desk` page, registered here BEFORE the
build (the iter-1/iter-2/iter-3 precedent) — the first two are logged as interpretation calls in
`assumptions.md` iter-4, read those before implementing the page:
  1. **B10 chip copy.** `_select_best_band` (`desk_screen.py:206`) ranks distance-to-close ahead of
     quality score and stays BYTE-UNCHANGED this iteration (zero diff on `desk_screen.py`'s
     computation) — `/desk`'s headline-band chip is labeled "nearest same-class band", never
     "strongest band" or similar, so the copy stays honest about what the ranking actually
     selects.
  2. **Run Screen's date source.** The button always submits the CLIENT's own `today` (the SAME
     `todayUtcDate()`-style helper `/structure`'s own "Today" shortcut already uses) as
     `screen_date` — no date-picker/alternate-date UI ships this iteration (the CLI's `--date`
     already covers arbitrary dates for operator use). The operator's click is still the explicit
     act (T-6/anti-goal "every run is an explicit operator act") — the client choosing "today" as
     the parameter value is the same pattern already accepted for the bar top-up's fetch horizon
     (`assumptions.md` iter-2).
  3. **Freshness labelling.** `coverage.latest_window_end_utc` (surfaced via each row's embedded
     `coverage`) is labeled "window last requested" throughout `/desk` — never "last bar" — per
     audit B9/iter-2 B2: it describes whole-store freshness at screen-compute time, not what the
     screen's rows actually consumed. **AMENDED at iter-4 (audit F1):** `bar_store_signature` is NOT
     given that label. It is `sha256(sorted (symbol, timeframe, latest_window_end_utc) tuples)[:16]`
     (`desk_screen.py:172-182`) — a checksum, so "Window last requested  d7bc8f8127904d0a" put a
     false claim on a hex digest. The provenance line labels it **"Bar-store signature"** with a
     caption stating it summarizes every member's window-last-requested timestamp and is a pin,
     never a time. The freshness LABEL now lives only on the value that genuinely is a window end.
  4. **Screen-history interactivity split.** iter-4 renders the screen-history list read-only
     (date + rows/skipped counts + provenance summary, from `GET /research/desk/screen`'s
     meta-only `screens` list) with NO click-through — selecting a past entry to render ITS OWN
     rows verbatim, and the `/structure` drill-in, are J-05's job (deferred past iter-4). This is
     journey-scope allocation matching J-04 vs. J-05's own goal.md acceptance split, not a logged
     assumption.

NOTED at iter-5 (documentation currency only, no new build-time decision): iter-4's browser-QA step
never dispatched, so J-04 stayed `partial` despite the product being fully built and independently
verified via live REST + two of its three required screenshots. iter-5 is a verification-only pass
(zero product diff) that dispatches a real, fixture-scoped browser-QA run to capture the missing
third screenshot (Run Screen running with a second click refused) and records the era's first
`/desk` golden replay script (`journey-scripts/J-04.json`). The Navigation-skeleton and "Bars /
candles" row text above were also refreshed for currency per `coherence.md` iter-4's advisory notes
(the iter-4 audit-B1 `StructureChart.tsx` exception and the iter-4 merged-vs-per-series bar-read
divergence, respectively) — neither is a nav-skeleton structural change.

RESOLVED at iter-6 (build-time scope for J-05, registered here BEFORE the build): both halves of
J-05 reuse ALREADY-REGISTERED contract values verbatim — the history click-through calls
`GET /research/desk/screen?date=` (shipped J-03, iter-3, no shape change) and the `/structure`
drill-in prefill calls that page's own existing Load-form endpoints. Zero new Data-Contract row,
zero new backend route, zero new `Config` field. Row links cover BOTH ranked and skipped members
(goal.md's "each briefing row" does not distinguish the two; logged as an interpretation call in
`assumptions.md` iter-6). No nav-skeleton change — both canonical homes were already registered at
iter-4's build (Feature/journey homes table above).

RESOLVED at iter-7 (build-time scope, registered here BEFORE the build):
  1. **J-06 MCP proxies.** `desk_universe`/`desk_screen` are added to `app/mcp/__init__.py`'s
     `_STATIC_PATHS` as plain no-argument proxies of the two ALREADY-registered rows above (no new
     Data-Contract row, no shape change); `get_endpoint`'s existing `/research/` allowlist already
     covers the `?date=` variant with zero code change.
  2. **F2 hover-tooltip contract.** Audit F2 (iter-6) found the whole-row drill-in link had made
     several per-cell `title` tooltips (full-precision `distance_bps`/`band_score`, per-timeframe
     "window last requested" freshness) unreachable by hover. Rather than either candidate the audit
     named (shrink the row's click target, or let specific cells reclaim pointer priority — both of
     which risk breaking `journey-scripts/J-05.json` step 4's already-passing click on the whole
     `<tr>`), iter-7 consolidates the lost tooltip content onto the row's own drill-in anchor
     (already the topmost element everywhere in the row): hovering anywhere in the row reveals one
     composite tooltip carrying all of it. Zero change to click geometry; logged in `assumptions.md`
     iter-7.

NOTED at iter-8 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iter-8 targets J-07 alone -- the era's regression sentinel, still `partial` after iter-7 for three
reasons the owner's R-1 ratification (docs/goal.md, 2026-07-27) and this iteration's own work close
out: (1) R-1 itself resolves "zero out-of-inventory changes" by naming the iter-4 frozen-file repair
IN INVENTORY; (2) iter-8 captures, for the first time this era, an era-open (`047c38e`) kept-route
response baseline (a scratch worktree against a throw-away data copy) and diffs it against the
current tree, so "kept-route byte-identity" finally has real evidence instead of a skipped clause --
the only expected differences are `/meta/ui-routes` (2->3), the MCP tool count (15->17, already
proven in iter-7), and the bar-backed reads R-1 names; (3) iter-8 restores
`journey-scripts/J-07.json` step 10 to its original `tradable-map-chart-caption` target (the iter-7
edit was based on a disproven premise per the iter-7 audit's T1) and takes the still-missing Cockpit
Historical-mode screenshot on a real symbol. No product surface, page, or served value changes --
this note exists so a future reader does not mistake the baseline-capture script or the golden-script
restore for a new Data-Contract owner.

RESOLVED at iter-9 (build-time scope for J-08, registered here BEFORE the build): the enhancement
loop's first post-GOAL_ACHIEVED journey extends the ALREADY-REGISTERED "Screen snapshots, rank rows,
skip rows" row with two new ranked-row-only fields (`basis_as_of`, `basis_age_days`) — see that row's
own iter-9 addition note above for the exact shape and the legacy-row honest-fallback contract. No
new page, no new endpoint, no new owner, no nav-skeleton change (`/desk`'s Feature/journey homes row
above gains a J-08 entry pointing at the same `/desk` canonical home J-04 already registered). Zero
diff to `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`, zero new `Config` field —
`compute_tradability`'s own `basis_as_of` is read verbatim, never re-derived.

NOTED at iter-10 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 9's own required screenshot proved the basis mechanism end to end (a real 3 d vs 14 d
spread, byte-identical to the canonical `compute_tradability` owner) but missed `docs/goal.md`'s
literal `<= 2 d` / `>= 10 d` thresholds by one day on the fresh side, because it was captured at
`as_of` = the run's own wall-clock "today" rather than the date the goal's own rationale cites.
iter-10 makes no code change and adds no Data-Contract row — it computes one additional screen for
`screen_date=2026-07-25` inside a scoped, throwaway copy of `.data/` (never the ambient store) via
the existing `desk_screen_compute` CLI/POST path, and captures the literal screenshot from that
scoped copy's `/desk`. This note exists so a future reader does not mistake the new scoped-compute
evidence, or the two documentation corrections it lands (a stale iter-9 handoff citation; a
newly-documented `J-08.json` steps-3/6 dependency on its replay target's latest screen already
carrying basis fields), for a new owner, endpoint, or shape.

RESOLVED at iter-11 (build-time scope for J-09, registered here BEFORE the build): the enhancement
loop's second post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at iter-10;
proposer rationale: `state/proposer-result.json` + `state/enhancement-proposals.jsonl`, 2026-07-28 —
measured live against the running backend, `GET /research/desk/topup/compute` already returns `null`
once a job is superseded, so a real ~100-symbol top-up's per-pair outcome is unrecoverable today: the
frozen `BarStore` holds 65 symbols' series while 38 of `universe-2026-07-25-49b33fa31680`'s 101
members hold none, matching the 38 `skipped: no_bars` rows of `screen-2026-07-27-936543601e75`, but
whether each of those pairs was attempted, refused, or never reached is unknowable from any existing
store). Unlike J-08 (an additive field on an EXISTING row), J-09 adds ONE wholly NEW Data-Contract
row — a brand-new append-only store mirroring `UniverseStore`/`ScreenStore`'s discipline — registered
above BEFORE any code lands, per this era's iter-1/2/3/9 precedent. No new page (the new "Top-up
Runs" section lives on the ALREADY-REGISTERED `/desk` canonical home, same as J-04/J-05/J-08), no
nav-skeleton change, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/`
allowlist already reaches `GET /research/desk/topup/runs` with zero code change — J-06's exactly-17
contract is unaffected). The "Top-up compute progress" row (process-scoped, in-memory, honestly lost
on restart/supersession) is UNCHANGED — J-09 reads the SAME per-pair outcome values `run_topup`
already produces but persists them separately and durably; the two rows can never disagree because
they share one computation, just different lifetimes. The backlogged `bar-index-store-reconcile`
proposal is again NOT promoted this cycle (re-measured: 369 store series vs 281 `bar_index` rows,
88 unindexed; same 7 member×timeframe pairs still read `has_bars:false` against a store that holds
them) — deferred a further cycle to keep this iteration's scope to the one promoted journey.

NOTED at iter-12 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 11 built and independently re-verified every behavioral clause of J-09 (byte-identical
per-pair outcomes via a live spy over the real `run_topup`, cancelled-run unreached-pairs honesty,
interrupted-run-leaves-no-record, second-run append-only, MCP/copy/suite/fingerprint all green,
COHERENCE-PASS) but its own `[NEW]`-flagged demo-narrator walkthrough
(`reports/phase-goal-desk-iter-11-demo.json` step 2) narrated only the honest empty state — the
ambient backend it recorded against genuinely had zero top-up runs, so it could not also show a
populated one, leaving docs/goal.md's "covers... end to end" clause unmet (evaluator: `partial`,
`CONTINUE`; audit finding T3, rated PASS_WITH_GAPS/non-blocking). iter-12 makes no code change and
adds no Data-Contract row — it seeds a fresh fixture-scoped copy of `.data/` (never the ambient
store), records three checkpoint top-up runs into it (one ordinary, one cancelled mid-walk, one with
an induced failed pair — the same recipe iter-11's own browser-QA lane already used), and re-records
the demo-narrator walkthrough against that populated rig so it narrates both halves — the honest empty
state, then the populated one — in one artifact. This note exists so a future reader does not mistake
the re-recorded walkthrough, or the scoped rig it was captured against, for a new owner, endpoint, or
shape.

NOTED at iter-13 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 12 (dispatched `lean`) still could not close J-09's outstanding demo-narrator-walkthrough
clause — not for a product reason, but a structural one: at `lean` depth the demo-narrator lane runs
AFTER the goal-evaluator scores the iteration (`trace.jsonl`), so a lean iteration can never film its
own closing artifact in time to be scored (evaluator verdict: `ESCALATE`, this session's first).
Iteration 12 also surfaced a capture-order defect: its dev lane seeded the scoped root, recorded the
three checkpoint runs, and only THEN booted the frontend — closing the honest "no runs recorded yet"
window before any browser existed, since the append-only rail forbids re-creating that window by
deleting real records. The browser-QA lane worked around it by capturing the empty half on a SECOND,
disconnected scoped root (`desk-iter12-scoped-qa-empty`, `:8302`/`:3302`), which the evaluator
accepted for the two separate standalone screenshots (`assumptions.md` iter-12, first entry) but
could not accept as a single coherent walkthrough. iter-13 (`full` depth — mandatory, since the prior
verdict was `ESCALATE`) makes no code change and adds no Data-Contract row — it seeds ONE fresh
scoped root, boots BOTH the backend and the frontend against it BEFORE recording any run, captures
the genuinely live honest-empty state first, THEN records the same three-checkpoint recipe, captures
the populated state second on that same still-live rig, and assembles both captures into one
`[NEW]`-flagged demo-narrator walkthrough. This note exists so a future reader does not mistake the
re-recorded walkthrough, or the corrected-order rig it was captured against, for a new owner,
endpoint, or shape.

RESOLVED at iter-14 (build-time scope for J-10, registered here BEFORE the build): the
goal-proposer's third post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at
iter-13; proposer rationale: `state/proposer-result.json` + `state/enhancement-proposals.jsonl`,
2026-07-28 — measured live against the frozen store and the derived index: `apps/backend/.data/bars`
holds 369 series files while `.data/bar_index.db` holds 281 rows, so 88 recorded series carry no
index row, and 7 of those land on screened member x timeframe pairs that render a dark-or-false
coverage badge on `screen-2026-07-27-936543601e75`, while `BarIndex.reindex()` — the existing
repair — has zero call sites outside its own test). Unlike J-08 (an additive field on an existing
row) or J-09 (one wholly new durable store beside an ALREADY-existing compute-progress row), J-10
adds TWO new Data-Contract rows — a durable run-record ledger (mirrors `TopupRunStore`'s discipline)
AND a transient compute-progress row (mirrors `DeskTopupComputeManager`'s shape), because the
reconcile action has no pre-existing compute manager of its own to extend the way J-09 extended
J-02's — both registered above BEFORE any code lands, per this era's iter-1/2/3/9/11 precedent (see
`assumptions.md` iter-14 for the full reasoning). No new page (the new "Index Reconciliation" section
lives on the ALREADY-REGISTERED `/desk` canonical home, same as J-04/J-05/J-08/J-09), no nav-skeleton
change, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/` allowlist
already reaches the new GET path with zero code change — J-06's exactly-17 contract is unaffected).
No CLI warmer is planned this iteration: unlike J-02/J-03, goal.md's own J-10 text never names one,
and the repair itself is a fast, local, no-network index rebuild rather than a ~100-symbol vendor
walk, so the UI trigger (and a direct `POST`, for the operator's real ambient-store run) is
sufficient — logged in `assumptions.md` iter-14. `bar_index.py`, `bars.py`, `tradability.py`,
`levels.py`, `desk_coverage.py` and `StructureChart.tsx` all take a ZERO diff — reconciliation
changes only the derived index, never any canonical computation or the frozen chart. The reconcile
run's fixture-scoped tests plant a SMALL, controlled drift case (per goal.md J-10 step 6); the real
~88-pair ambient-store reconciliation stays an operator-run act, reported honestly if and when it
happens, never a CI gate (goal.md's own parenthetical). The two other backlogged proposals (top-up-
runs `integrity_errors` disclosure; coverage-freshness date-format consistency) are again NOT
promoted this cycle — deferred to keep this iteration's scope to the one promoted journey.

RESOLVED at iter-15 (build-time scope for J-11, registered here BEFORE the build): the
goal-proposer's fourth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at
iter-13, reopened once for J-10 and closed again at iter-14; proposer rationale measured live
against a real recorded screen, `screen-2026-07-29-ce0d82b8e9bf`: the count of finite-priced merged
daily bars at or before each ranked row's own `basis_as_of` spans 27 to 501 across the same screen,
median 500, and neither `DeskScreenRow` nor any coverage badge can express that spread today — a
27-session listing and a 500-session name sit on one rank scale, indistinguishable). Like J-08 (an
additive field on an EXISTING row) and UNLIKE J-09/J-10 (each a wholly new store), J-11 extends the
ALREADY-REGISTERED "Screen snapshots, rank rows, skip rows" row with two new ranked-row-only fields
(`history_sessions`, `history_start`) — see that row's own iter-15 addition note above for the exact
shape and the legacy-row honest-fallback contract. No new page (the `history` column lives on the
ALREADY-REGISTERED `/desk` canonical home, same as J-04/J-05/J-08/J-09/J-10), no nav-skeleton
change, no new endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s existing
byte-identical GET-proxy contract covers the new fields automatically; J-06's exactly-17-tool
contract is unaffected). Zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
`StructureChart.tsx` — both new values are derived entirely inside the ascending
`BarStore.merged_bars(symbol, "1d")` walk `_resolve_reference_close` already performs for
`basis_as_of`, with no new store read, no new accessor, and no new index. The rank key
(`band_class`, `distance_bps`, `band_score`, `symbol`) is unchanged — this journey discloses, it
never ranks, filters, gates, weights, or scores (goal.md's own explicit Non-Goals text for J-11).

RESOLVED at iter-16 (build-time scope for J-12, registered here BEFORE the build): the
goal-proposer's fifth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at
iter-13, reopened for J-10 at iter-14 and J-11 at iter-15, both closed again; proposer rationale
measured live against the running backend and the frozen `.data/screen` store, 2026-07-29: 6
recorded snapshots, two sharing `screen_date=2026-07-27` under different `bar_store_signature`s —
the pre/post-repair pair J-10's own reconciliation produced — where `GET /research/desk/screen?date=`
resolves only `matching[-1]`, so the earlier, listed snapshot is unreadable by any existing path;
separately `latest` is `records[-1]` under `created_utc`, not the latest `screen_date`, and nothing
on `/desk` names which snapshot is on screen; and both run-ledger GETs drop their own stores'
`errors` while their two sibling GETs already serve them). Unlike J-09/J-10 (each a wholly new
store) and like J-08/J-11 (an additive extension of an ALREADY-REGISTERED row), J-12 adds ZERO new
Data-Contract row: it is a pure additive READ PARAM (`?id=`) on the already-registered "Screen
snapshots, rank rows, skip rows" row, plus an additive `integrity_errors` key on the two run-ledger
rows that already carry an `errors`-producing `store.list()` call — see each row's own iter-16
addition note above for the exact contract. No new page (the affected surfaces — screen-history
list, provenance panel, all four ledger sections — live on the ALREADY-REGISTERED `/desk` canonical
home), no nav-skeleton change, no new endpoint, no new `Config` field, no new MCP tool
(`get_endpoint`'s existing `/research/` allowlist already reaches `?id=` with zero code change;
`desk_screen`'s byte-identical no-arg proxy contract is unaffected; J-06's exactly-17-tool contract
stays green). Zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
`StructureChart.tsx`/`desk_coverage.py` — this journey adds a read path and a disclosure channel,
never a computation. The rank key and every recorded snapshot's stored content are unchanged; the
fixture-scoped tests plant a small planted-corrupt-record case per goal.md J-12 step 6, never
against `apps/backend/.data` (the iter-9/iter-14/iter-15 scoped-rig lesson, restated in this
iteration's own NOTES).

RESOLVED at iter-17 (build-time scope for J-13, registered here BEFORE the build): the
goal-proposer's sixth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at
iter-13, reopened for J-10/J-11/J-12 at iter-14/15/16, each closed again; proposer rationale measured
live against the running product's own artifacts, 2026-07-29: the string `price` occurs zero times in
`apps/frontend/app/desk/page.tsx`, so `price_low`/`price_high` -- already recorded on every ranked row
of every snapshot on disk since iter-3 -- are rendered NOWHERE, and the reference close itself is not
even recorded, though `compute_screen` already binds it locally before feeding the band selection and
the distance; the close is recoverable from a recorded row ONLY by inverting `distance_bps` against a
band edge under the row's own `side`, i.e. only by the client-side recomputation the Data Contract
forbids). Like J-08/J-11 (an additive extension of an ALREADY-REGISTERED row) and UNLIKE J-09/J-10
(each a wholly new store), J-13 adds ZERO new Data-Contract row: one new ranked-row-only field
(`reference_close`) on the ALREADY-REGISTERED "Screen snapshots, rank rows, skip rows" row -- see that
row's own iter-17 addition note above for the exact shape and the legacy-row honest-fallback contract
-- plus a new `band` column on the ranked table RENDERING two fields that have been recorded and typed
since iter-3 but never shown. No new page (the `band` column lives on the ALREADY-REGISTERED `/desk`
canonical home, same as J-04/J-05/J-08/J-09/J-10/J-11/J-12), no nav-skeleton change, no new endpoint,
no new `Config` field, no new MCP tool (`desk_screen`'s existing byte-identical GET-proxy contract
covers the new field automatically; J-06's exactly-17-tool contract is unaffected). Zero diff to
`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/`desk_coverage.py` -- the
new value is copied verbatim out of the SAME ascending `BarStore.merged_bars(symbol, "1d")` walk
`_resolve_reference_close_and_history` already performs for `basis_as_of`/`history_sessions`/
`history_start`, with no new store read, no new accessor, and no new index. The rank key (`band_class`,
`distance_bps`, `band_score`, `symbol`) is unchanged -- this journey discloses, it never ranks,
filters, gates, weights, or scores (goal.md's own explicit Non-Goals text for J-13), and no
proximity/quality/threshold flag (e.g. "price is inside the band") is computed anywhere. Depth is
`full` this iteration (Full trigger 2: the new field is added to a persisted, registered Data-Contract
row) -- also because J-13's acceptance names a first-ever `[NEW]`-flagged demo-narrator walkthrough
for this specific disclosure, and the iter-12 lesson (`lessons.md`) proved a `lean`-dispatched
iteration cannot score a brand-new walkthrough clause within its own run (the demo-narrator lane runs
after the goal-evaluator at `lean` depth).

RESOLVED at iter-18 (build-time scope for J-14, registered here BEFORE the build): the
goal-proposer's seventh post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED at
iter-17, reopened for J-10/J-11/J-12/J-13 at iter-14/15/16/17, each closed again; proposer rationale
measured live 2026-07-29 against the canonical `compute_tradability` owner itself for all 63 ranked
members of a real recorded snapshot: every one of the 63 carries bands on BOTH sides of price, yet
each recorded row keeps exactly one, and the distance from a row's own reference close to the nearest
band on the OTHER side spans 0.0 to 12,178.8 bps -- invisible exactly where the briefing is densest,
since the nine top-ranked rows all read `support . class A . 0.00 bps` while their own nearest
opposite wall sits anywhere from 0.6 bps to 6,067.7 bps away). Like J-08/J-11/J-13 (an additive
extension of an ALREADY-REGISTERED row) and UNLIKE J-09/J-10 (each a wholly new store), J-14 adds
ZERO new Data-Contract row: two new ranked-row-only fields (`opposite_band`, `bands_by_class`) on the
ALREADY-REGISTERED "Screen snapshots, rank rows, skip rows" row -- see that row's own iter-18 addition
note above for the exact shape and the legacy-row honest-fallback contract -- plus a new `opposite`
column on the ranked table and one more line in the row's existing composite hover tooltip. No new
page (the `opposite` column lives on the ALREADY-REGISTERED `/desk` canonical home, same as
J-04/J-05/J-08/J-09/J-10/J-11/J-12/J-13), no nav-skeleton change, no new endpoint, no new `Config`
field, no new MCP tool (`desk_screen`'s existing byte-identical GET-proxy contract covers both new
fields automatically; J-06's exactly-17-tool contract is unaffected). Zero diff to
`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/`desk_coverage.py` -- both
new values are selected from the SAME `result["bands"]` list `compute_screen` already holds and the
SAME `_distance_bps` helper it already calls, with no second `compute_tradability` call and no second
`BarStore` read. The rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) is unchanged --
this journey discloses, it never ranks, filters, gates, weights, or scores (goal.md's own explicit
Non-Goals text for J-14), and no corridor-width/room/proximity/quality/threshold number is computed
anywhere. Depth is `full` this iteration (Full trigger 2: two new fields are added to a persisted,
registered Data-Contract row) -- also because J-14's acceptance names a `[NEW]`-flagged demo-narrator
walkthrough narrated over POPULATED ranked rows, which goal.md's own text ties to closing iter-17's
carried `RECORDED_WITH_NOTES` capture gap (its film showed only the legacy state), and the iter-12
lesson (`lessons.md`) proved a `lean`-dispatched iteration cannot score a brand-new walkthrough clause
within its own run (the demo-narrator lane runs after the goal-evaluator at `lean` depth).

NOTED at iter-19 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 18 shipped `opposite_band`/`bands_by_class` with `_select_opposite_band` delegating to
`_select_best_band`'s own class-rank-first tie-break; the evaluator measured that selection against
the canonical `compute_tradability` owner on the owner's own real 63-row screen and found it diverges
from `docs/goal.md` J-14 step 1's literal "distance ascending, then class rank descending" order on 2
of 63 rows (HONA, META) -- an interpretation call already logged in `assumptions.md` iter-18 (the
evaluator's own "We chose: Read DISTANCE-first as the requirement" entry). iter-19 adds no new
Data-Contract row and makes no nav-skeleton change -- it corrects `_select_opposite_band`'s own
tie-break order to distance-first inside its SAME sole owner (`desk_screen.py`) and SAME serving
endpoint (`GET /research/desk/screen`), updates that module's own docstring description of the order
to match, updates the golden/unit tests that asserted the pre-fix class-first selection, and re-films
the `[NEW]`-flagged demo-narrator walkthrough over POPULATED `/desk` rows -- closing both J-14's own
walkthrough gap and iter-17's carried J-13 `RECORDED_WITH_NOTES` capture gap in the same recording.
`_select_best_band` (the row's own same-side selection) and `_row_rank_key` (the cross-symbol rank
order) are UNCHANGED -- only the opposite-side tie-break order moves. This note exists so a future
reader does not mistake the corrected selection, or its re-verification against real data, for a new
owner, endpoint, or shape.

NOTED at iter-20 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 19 shipped and independently re-verified the distance-first `_select_opposite_band` fix
(GOAL_ACHIEVED) but was dispatched `lean`, so its own `[NEW]`-flagged demo-narrator walkthrough over
POPULATED `/desk` rows never ran in-run (`reports/demo/goal-desk-iter-19/` does not exist), and a
separately carried capture gap from iter-16 (a full-page screenshot of the earlier of J-12's two
same-date recordings, `screen-2026-07-27-936543601e75.json`, showing the NFLX `1d` coverage badge
together with the page's own "every timeframe badge dark" sentence in one frame) stayed open. iter-20
makes no code change and adds no Data-Contract row (`Depth: evidence` -- capture + evaluate only, the
rule-7 exception: the prior evaluator's own next-step asked ONLY for evidence on already-passing
J-12/J-13/J-14) -- it records the walkthrough against the already-recorded, fields-complete screen
`screen-2026-07-20-ca185294a384.json` (100 ranked rows, every row carrying `reference_close`,
`price_low`/`price_high`, and `opposite_band` -- the same recording the iter-19 evaluator re-derived
byte-for-byte) and captures the full-page J-12 screenshot, both from a read-only SCOPED COPY of
`apps/backend/.data` (never a write into the ambient store, per the iter-9/11/14/15/17/19 scoped-rig
lesson). This note exists so a future reader does not mistake either capture, or the scoped copy it
was taken against, for a new owner, endpoint, or shape.

NOTED at iter-21 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
iteration 20 recorded J-12's full-page crop but its own `[NEW]`-flagged demo-narrator walkthrough for
J-13/J-14 still wrote `Demo Verdict: SKIPPED` with an empty gallery, because
`reports/phase-goal-desk-iter-20-demo.json` embedded three JavaScript regex literals
(`/screen.history/i`, `/scroll.*band/i`, `/scroll.*opposite/i`) where the schema requires plain JSON
strings, and two of its steps modelled the sideways reveal of the `band`/`opposite` columns as a click
on a "scroll..." button that has never existed. iter-21 makes no code change and adds no Data-Contract
row (`Depth: evidence` -- capture + evaluate only, the rule-7 exception restated at iter-20: the prior
evaluator's own next-step asked ONLY for evidence on already-passing J-13/J-14) -- it re-authors the
demo script as valid JSON, parse-checks it (`demo_runner.py --mode lint`) before recording, and drops
the nonexistent-button click entirely: `demo_runner.py`'s own action vocabulary
(`goto`/`click`/`fill`/`expect`/`wait_for`, `scripts/automation/lib/demo_runner.py:36`) has no scroll
primitive, and every ranked row (`apps/frontend/app/desk/page.tsx:335-427`, `data-testid=
"desk-screen-row"`) is covered end-to-end by one stretched `next/link` anchor (`desk-row-drill-in`,
`position: absolute; inset: 0` relative to the row) that navigates to `/structure` on a click anywhere
in the row, including the `band`/`opposite` cells -- so the walkthrough narrates both disclosures
through accurate `narration`/`point_out` text and `expect` assertions instead of a click-driven reveal,
over the same already-recorded, fields-complete `screen-2026-07-20-ca185294a384` (100 ranked rows) a
fresh scoped copy of `apps/backend/.data` serves, never the ambient store. This note exists so a future
reader does not mistake the corrected script, or the scoped rig it was captured against, for a new
owner, endpoint, or shape.

NOTED at iter-22 (documentation currency only, no new Data-Contract row, no nav-skeleton change):
the STALLED halt after iteration 21 (J-14's native `title`-attribute tooltip screenshot is
structurally uncapturable by any CDP-based screenshot, three tries) was resolved by the OWNER, not
the chain: `docs/goal.md` gained trap **T-10a** (2026-07-30) ratifying `project-extensions/qa-rig/`
(its own isolated `Xvfb` display, a real headed Chrome, real X-pointer hover, an X-level screen grab)
as the sanctioned way to take that one screenshot — the acceptance bar itself (T-10, "no screenshot
=> unknown, never passing") is UNCHANGED. iter-22 makes no product code change and adds no
Data-Contract row (`Depth: evidence` — capture + evaluate only): it boots the rig, hovers the
already-shipped `/desk` ranked row's own already-shipped drill-in anchor (`deskRowDrillInTitle`,
`page.tsx:278`) on a scoped copy of the already-recorded, fields-complete
`screen-2026-07-20-ca185294a384` screen, and photographs the native tooltip window the rig's own
X-level grab can see (verified against a live negative-guard check in the same run, never assumed
from the README). This note exists so a future reader does not mistake the rig, its state directory,
or this capture for a new owner, endpoint, page, or Data-Contract row — `/desk`'s `opposite` column
and its `bands_by_class` tooltip line were already fully registered at iter-18/19.

RESOLVED at iter-23 (build-time scope for J-15, registered here BEFORE the build): the
goal-proposer's eighth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED
at iter-22; proposer rationale: `state/proposer-result.json`, measured 2026-07-30 against the
canonical `compute_tradability` owner's own cached returns for all 100 ranked rows of
`screen-2026-07-29-2a57de4e7415` — 100/100 matched on `(side, price_low, price_high,
quality_score)`; the selected bands' `member_count` spans 1 to 4,014 (quartiles 19/45.5/87),
`round_number` is true on 16/100, and neither value nor any per-timeframe tally is recorded on
any screen row or rendered anywhere on `/desk`, while `/structure`'s own band table already
renders both for the identical bands). Like J-08/J-11/J-13/J-14 (an additive extension of an
ALREADY-REGISTERED row) and UNLIKE J-09/J-10 (each a wholly new store), J-15 adds ZERO new
Data-Contract row: three new ranked-row-only fields (`band_member_count`, `band_round_number`,
`band_member_timeframes`) on the ALREADY-REGISTERED "Screen snapshots, rank rows, skip rows"
row — see that row's own iter-23 addition note above for the exact shape and the legacy-row
honest-fallback contract — plus one new `levels` column on the ranked table. No new page (the
column lives on the ALREADY-REGISTERED `/desk` canonical home), no nav-skeleton change, no new
endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s existing byte-identical
GET-proxy contract covers all three fields automatically; J-06's exactly-17-tool contract is
unaffected). Zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
`StructureChart.tsx`/`desk_coverage.py` — all three values are read from the SAME band dict
`_select_best_band` already returns and that band's own `members` list, with no second
`compute_tradability` call and no second `BarStore` read. The rank key (`band_class`,
`distance_bps`, `band_score`, `symbol`) is unchanged — this journey discloses, it never ranks,
filters, gates, weights, or scores (goal.md's own explicit Non-Goals text for J-15), and no
confluence-quality/evidence-depth/intraday-share/threshold number is computed anywhere. Depth
is `full` this iteration (Full trigger 4: a brand-new full-stack journey — backend
`desk_screen.py` row-builder work AND frontend `/desk` column work, with three real
Data-Contract additions, for a never-before-implemented journey) — also because J-15's
acceptance names a first-ever `[NEW]`-flagged demo-narrator walkthrough for this specific
disclosure, and the iter-12 lesson (`lessons.md`) proved a `lean`-dispatched iteration cannot
score a brand-new walkthrough clause within its own run (the demo-narrator lane runs after the
goal-evaluator at `lean` depth). The `band_member_timeframes` key order is left to build
discretion (goal.md only requires "a deterministic order") — mirror the `_bands_by_class`
precedent's own key style for consistency, and keep it stable across runs and across the golden
test's own assertions.

RESOLVED at iter-24 (build-time scope for J-16, registered here BEFORE the build): the
goal-proposer's ninth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED + CONFIRM_ACHIEVED
at iter-23; proposer rationale measured live 2026-07-30 against iter-23's own browser-QA
measurement, `UT-07-fail.png`: the ranked table's `scrollWidth` is 1795 px inside a `clientWidth`
of 1214 px at a 1440 px viewport, so the `opposite` (J-14) and `levels` (J-15) columns sit
entirely outside the visible window, and `DeskCoverageBadges`' `flex flex-wrap` stacks each
row's four badges into four lines, ~115 px tall). Unlike every prior post-GOAL_ACHIEVED journey
(J-08 through J-15, each adding a new served field and/or a new column), J-16 adds ZERO new
Data-Contract row and ZERO new column: it is a pure reflow of the ALREADY-REGISTERED "Screen
snapshots, rank rows, skip rows" row's ALREADY-SERVED fields inside the ALREADY-REGISTERED
`/desk` canonical home (dropping in-cell label prefixes the column headers already state,
collapsing the four coverage badges onto one line, and relaxing `LABEL_CELL`'s
`whitespace-nowrap` on the long disclosure cells), plus one new `rank` cell that renders the
row's own 1-based position in the SERVED `rows` array verbatim -- data J-03 already records as
the array's own order, never a new computed value. No new page, no nav-skeleton change, no new
endpoint, no new `Config` field, no new MCP tool (`desk_screen`'s existing byte-identical
GET-proxy contract is untouched; J-06's exactly-17-tool contract is unaffected). Zero diff to
`desk_screen.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
`desk_coverage.py` -- the page renders `GET /research/desk/screen`'s served payload verbatim,
as it already does, and never sorts, reverses, re-slices, filters or paginates `rows` (a new
source-introspection guard in `test_desk_ui_guards.py`, with its own seeded counter-test, proves
it). Every existing `data-testid` and its exact rendered text stay byte-unchanged, so the 13
stored golden replay scripts (`journey-scripts/J-01`...`J-14`) replay green with zero script
edits and `test_desk_hover_tooltip_guard.py`/`test_copy_discipline.py` stay green unmodified.
Depth is `full` this iteration (Full trigger 1: structural/cross-cutting -- the reflow touches
the ONE shared `/desk` ranked-table render behind 9 already-shipped journeys' testids/tooltip/
copy contracts, J-03/J-04/J-05/J-08/J-09/J-10/J-11/J-12/J-13/J-14/J-15, plus 13 golden replay
scripts and 3 guard-test suites -- no single journey's own test coverage spans that blast
radius; the evaluator's own recommendation for this iteration is also `full`).

RESOLVED at iter-26 (build-time scope for J-17, registered here BEFORE the build): the
goal-proposer's tenth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED at iter-25, awaiting
the second-key confirm when the proposer promoted this cycle's top-scored proposal, 0.86;
proposer rationale: `state/enhancement-proposals.jsonl` + `state/proposer-result.json`, measured
2026-07-30 against the desk's own recorded ledger and the frozen store: the ONE recorded real
top-up, `topup-2026-07-29-5de907c83fc4` (404 pairs), reports `0 reused / 390 fetched / 14 failed`
— `reused` has never once fired on a real run, because `_fetch_window_now()` is wall-clock while
`record_bar_series`'s store-first is an exact-key `(symbol, timeframe, window_start, window_end)`
hit, so a window whose end moves every day can structurally never land a store-first reuse; for
the 235 pairs the store already held, that one run downloaded 276,714 bars to gain 13,533
(4.9%), and 174 of those 235 pairs gained ≤5 bars each — Key Capability 2's own "store-first ...
never re-fetched" promise is unreachable on the real path today). Unlike J-09/J-10 (each a
wholly new store) and like J-08/J-11/J-13/J-14/J-15 (an additive extension of an
ALREADY-REGISTERED row), J-17 adds ZERO new Data-Contract row: four new per-pair-outcome-only
fields (`requested_window`, `store_frozen_from`, `store_frozen_through`, `window_basis`) plus one
new `outcome` enum value (`"unchanged"`) on the ALREADY-REGISTERED "Top-up run records" row — see
that row's own iter-26 addition note above for the exact shape and the legacy-run
honest-fallback contract — plus three new disclosure lines inside the ALREADY-REGISTERED Top-up
Runs section (extended counts line, a tail-vs-full-lookback pair-count line, and each
already-rendered failed pair's own `requested_window`). No new page, no nav-skeleton change, no
new endpoint, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/`
allowlist already reaches `GET /research/desk/topup/runs`; J-06's exactly-17-tool contract is
unaffected). Zero diff to `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/
`tradability.py`/`levels.py`/`StructureChart.tsx` — the new window-selection logic reads only the
SAME canonical `BarStore.merged_bars` accessor `desk_screen.py`'s own reference-close/history walk
already uses, never `bar_index`'s request-bound `window_end_utc` (which stays `desk_coverage`'s
sole read), and no ranked-table column is added — J-16's measured `scrollWidth`/row-height
contract stands untouched. Depth is `full` this iteration (Full trigger 1: structural/
cross-cutting — a brand-new, never-before-built full-stack journey whose interaction spans three
modules with no existing single journey's own test coverage: `desk_topup_compute.py`'s per-pair
window-selection branch, `desk_topup_log.py`'s new fields/outcome value written by its one
shared writer, and `/desk`'s Top-up Runs section render — also because J-17's acceptance names a
first-ever `[NEW]`-flagged demo-narrator walkthrough for this specific disclosure, the iter-12/13
lesson (`lessons.md`) that a `lean`-dispatched iteration cannot score a brand-new walkthrough
clause within its own run, and the binding depth recommendation's own "brand-new full-stack
journey" escape condition, since the evaluator's `evidence` recommendation for this iteration
predates the goal-proposer's promotion of J-17 this cycle). The backlogged sibling proposal from
this cycle, `desk-screen-run-ledger-and-member-failure-isolation` (score 0.41), is again NOT
promoted — deferred to keep this iteration's scope to the one promoted journey.

RESOLVED at iter-29 (build-time scope for J-18, registered here BEFORE the build): the goal-proposer's eleventh post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED at iter-28, awaiting the second-key confirm when the proposer promoted this cycle's top-scored proposal, 0.86; proposer rationale: `state/proposer-result.json` + `state/enhancement-proposals.jsonl`, measured 2026-07-31 against the desk's own artifacts: `.data/screen` holds 11 recorded snapshots and every one carries only `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature, created_utc, rows, skipped}` — no start time, duration, members-attempted count, or terminal state — while its two lesser siblings (`.data/topup_runs`, `.data/index_reconcile_runs`) each keep a durable ledger with exactly that kind of detail; `DeskScreenComputeManager`'s state is process-scoped and "honestly lost on restart" by its own docstring, so every screen run that failed, was cancelled, or found its pins already recorded left NOTHING on disk anywhere; and `/desk`'s Run Screen always submits today's UTC date while `trigger` ALWAYS runs the full member walk rather than pre-checking the store first, so a duplicate click recomputes ~101 tradable maps cold before `ScreenStore.record` refuses the duplicate one line later). Unlike J-08/J-11/J-13/J-14/J-15 (each an additive extension of an already-registered row) and like J-09/J-10 (each a wholly new store), J-18 adds ONE wholly NEW Data-Contract row — a brand-new append-only run-record store mirroring `TopupRunStore`'s discipline, PLUS a genuine behavior change to the ALREADY-SHIPPED `run_screen_and_record` (the pre-check itself) — registered above BEFORE any code lands, per this era's iter-1/2/3/9/10 precedent. No new page (the new "Screen Runs" section lives on the ALREADY-REGISTERED `/desk` canonical home, same as J-04/J-05/J-08/J-09/J-10/J-11/J-12/J-13/J-14/J-15/J-16/J-17), no nav-skeleton change, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/` allowlist already reaches the new path with zero code change — J-06's exactly-17-tool contract is unaffected). Zero diff to `desk_screen.py`'s recorded snapshot/row/skip shapes, rank order, or five-pin key, and zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_topup_log.py`/`StructureChart.tsx` — the pre-check resolves the SAME five pins `compute_screen` already resolves, through the SAME accessors, so the two resolutions cannot disagree, and `ScreenStore.record`'s `ScreenAlreadyRecorded` refusal remains the structural backstop for the race where the store changes under a running walk. No new ranked-table column and no change to the ranked table — J-16's measured width contract and every stored golden replay script stand untouched. Depth is `full` this iteration (Full trigger 1: structural/cross-cutting — a brand-new, never-before-built full-stack journey whose interaction spans the shared entry point both callers of `run_screen_and_record` use, a new durable store/module, a new route, and a new `/desk` section, with no existing single journey's own test coverage spanning that blast radius — also because J-18's acceptance names a first-ever `[NEW]`-flagged demo-narrator walkthrough for this specific disclosure, the iter-12/13 lesson (`lessons.md`) that a `lean`-dispatched iteration cannot score a brand-new walkthrough clause within its own run, and the binding depth recommendation's own "brand-new full-stack journey" escape condition, since the evaluator's `evidence` recommendation for this iteration predates the goal-proposer's promotion of J-18 this cycle). The sibling backlog item `desk-live-coverage-view-on-page` (score 0.31) is again NOT promoted — the coverage view already renders one screen-run-stale on every row, so the delta is live-vs-frozen only, deferred to keep this iteration's scope to the one promoted journey.

NOTED at iter-30 (documentation currency only, no new Data-Contract row, no nav-skeleton change; CORRECTED at iter-31 -- see below): the second-key confirm rejected iteration 29's GOAL_ACHIEVED proposal (`runs/goal-session-desk/iter-29/eval-confirm.md`) because J-18's honest "No screen runs recorded yet." empty state was never photographed -- the ambient store's own populating click destroyed it before the earlier attempt's screenshot tool was fixed. iter-30's spec (`docs/phases/goal-desk-iter-30.md`, `Depth: lean`) planned to close that gap AND land three small code/test fixes, but the engine dispatched iter-30 at `Depth: evidence` (a downgrade the spec did not request), so only the browser-qa capture ran. Two things from that dispatch ARE genuine and DONE: the empty-state screenshot (`reports/qa/goal-desk-iter-30-evidence/J-18-empty-state.png`) and the hardening of `journey-scripts/J-18.json` to stable substrings ("no walk was performed", "101 / 101") instead of a specific run/screen id. The three code/test items -- (1) `LatestScreenRunDetail` suppressing the amber `desk-screen-run-latest-unreached` note and `desk-screen-run-latest-counts` line on a reused done run, (2) `run_screen_and_record`'s failure path recording `failed_member: null` for an `attempted == 0` crash instead of `members[0]`, (3) their tests -- were NOT shipped at iter-30 despite this entry previously (wrongly) claiming they were; no developer ran that iteration. See "NOTED at iter-31" below for their actual disposition. Lesson recorded in `lessons.md` iter-30: never write a blueprint entry in the past tense before the code lands.

NOTED at iter-31 (documentation currency + build-time scope, registered here BEFORE the build, per the iter-30 lesson above; no new Data-Contract row, no nav-skeleton change): this iteration lands the two code fixes iter-30's spec planned but its depth-downgrade dropped -- `LatestScreenRunDetail`'s reused-run suppression and `run_screen_and_record`'s `attempted == 0` -> `failed_member: null` fix -- plus their tests, and reverts the two tracked build files (`apps/frontend/next-env.d.ts`, `apps/frontend/tsconfig.json`) iter-30's scoped rig polluted with an absolute scratchpad path (`lessons.md` iter-30(b), the open MINOR anti-goal item in `state/iteration-state.md`). Both fixes correct rendering/derivation of the ALREADY-REGISTERED "Screen run records" row only -- zero new field, shape, endpoint, module, or `Config` field. The `[NEW]` walkthrough film's frames-not-distinct gap rides along as a non-blocking passenger task per the iter-30 evaluator's own bound ("last time I ask" -- `runs/goal-session-desk/iter-30/eval.md`); if it duplicates again this run, it drops to the owner's optional track for good.

IN BUILD at iter-32 (build-time scope for J-19, registered here BEFORE the build, per the iter-30 lesson above; no new Data-Contract row, no nav-skeleton change): the goal-proposer's twelfth post-GOAL_ACHIEVED journey (era closed GOAL_ACHIEVED at iter-31, CONFIRM_ACHIEVED by the second key -- `runs/goal-session-desk/iter-31/eval-confirm.md` -- when the proposer promoted this cycle's top-scored proposal, 0.86; proposer rationale: `state/proposer-result.json` + `state/enhancement-proposals.jsonl`, measured 2026-07-31 read-only over the frozen artifacts: the one recorded real top-up run, `topup-2026-07-29-5de907c83fc4` (404 pairs), records each pair's provenance only as it stood BEFORE its own fetch (`store_frozen_through`, iter-26/J-17) -- no artifact anywhere states what a pair's frozen history reaches once the run ENDS; the pinned pairs' newest bars in fact span 2026-07-21..07-28 across timeframes, and `bar_index`'s only freshness value (the window a run ASKED for) postdates the newest bar actually held on 394 of 395 member x timeframe pairs). Like J-08/J-11/J-13/J-14/J-15/J-17 (each an additive extension of an ALREADY-REGISTERED row), J-19 adds ZERO new Data-Contract row: one new per-pair-outcome-only field, `store_frozen_through_after`, on the ALREADY-REGISTERED "Top-up run records" row -- see that row's own iter-32 addition note above for the exact shape and the legacy-run honest-fallback contract -- plus one new descriptive line and a short pairs-list inside the ALREADY-REGISTERED Top-up Runs section's latest-run detail. No new page, no nav-skeleton change, no new endpoint, no new `Config` field, no new MCP tool (`get_endpoint`'s existing `/research/` allowlist already reaches `GET /research/desk/topup/runs`; J-06's exactly-17-tool contract is unaffected). Zero diff to `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`routes.py`'s `record_bar_series`/`StructureChart.tsx`/`desk_topup_log.py` (a pure generic outcomes persister -- it needs no change to carry one more key per entry) -- the new value reads only the SAME pure `_pair_window` accessor J-17 already calls, a second time, immediately AFTER `_run_one_pair` returns for that pair, and no ranked-table or Top-up-Runs-summary-table column is added -- J-16's measured width contract stands untouched. Depth is `full` this iteration (Full trigger 1: structural/cross-cutting -- a brand-new, never-before-built full-stack journey whose interaction spans `desk_topup_compute.py`'s shared walker, the `/desk` Top-up Runs render, and a new Data-Contract field, with no existing single journey's own test coverage spanning that blast radius -- also because J-19's acceptance names a first-ever `[NEW]`-flagged demo-narrator walkthrough for this specific disclosure, the iter-12/13/26/29 lesson (`lessons.md`) that a `lean`- or `evidence`-dispatched iteration cannot score a brand-new walkthrough clause within its own run, and the binding depth recommendation's own "brand-new full-stack journey" escape condition, since the evaluator's `lean` recommendation for this iteration predates the goal-proposer's promotion of J-19 this cycle -- the same citation pattern iterations 15, 17, 23, 24, 26 and 29 used for their own brand-new journeys). No sibling proposal from this cycle was promoted alongside it (`n_proposals: 3`, one promoted).
-->
