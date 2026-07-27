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
| Per-member bar coverage + freshness | `app/research/desk_coverage.py` (shipped J-02, iter-2), reading `bar_index` only (never re-hashing `BarStore`) | `GET /research/desk/coverage` | payload: `{"universe_snapshot_id": str \| null, "timeframes": ["1h","4h","1d","1w"], "members": [{"symbol": str, "per_timeframe": {"<tf>": {"has_bars": bool, "latest_window_end_utc": str \| null}}}]}`; honest-empty (`universe_snapshot_id: null`, `members: []`) before any universe snapshot exists — HTTP 200, never 404; J-03 (iter-3) reuses this function VERBATIM for every screen row's `coverage` badge — never a second coverage read. iter-4 (J-04): `/desk`'s per-row coverage badge renders each row/skip entry's OWN embedded `coverage` field (copied onto the row at screen-compute time) — NEVER a live re-fetch of this endpoint from the desk page, and the freshness value is labeled "window last requested" in the UI, never "last bar" (it describes whole-store freshness, not what the screen actually consumed — audit B9/iter-2 B2). iter-7: this freshness value's hover-reachability moves from a per-badge `title` onto the row's drill-in anchor (audit F2 fix) — the LABEL and the underlying value are unchanged. |
| Top-up compute progress | `app/research/desk_topup_compute.py` (`DeskTopupComputeManager`, shipped J-02, iter-2) | `POST /research/desk/topup/compute` (trigger), `GET /research/desk/topup/compute` (poll), `POST /research/desk/topup/compute/cancel` (cancel) | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "started_utc": str, "finished_utc": str \| null, "error": str \| null, "progress": {"pairs_total": int, "pairs_done": int, "outcomes": [{"symbol": str, "timeframe": str, "outcome": "reused"\|"fetched"\|"failed", "detail": str \| null}]}}`; single-flight; page-load GETs never trigger a compute; process-scoped bookkeeping, never a research value. iter-4 (J-04) is this row's FIRST UI consumer (a Top-up button on `/desk`, wired with live progress + cancel, mirroring the Edge Report Compute button pattern) — read-only wiring, zero shape change. |
| Screen snapshots, rank rows, skip rows | `app/research/desk_screen.py` (shipped J-03, iter-3) | `GET /research/desk/screen` — no params: `{"screens": [...lightweight meta only: id/screen_date/as_of/universe_snapshot_id/config_fingerprint/bar_store_signature/created_utc/counts — NEVER full rows/skipped...], "latest": <full snapshot>\|null}`; `?date=YYYY-MM-DD`: `{"screen": <full snapshot for that date>\|null}` — honest-empty, HTTP 200 always | Frozen JSON, append-only, one file per snapshot, keyed on 5 pins (`screen_date`, `as_of`, `universe_snapshot_id`, `config_fingerprint`, `bar_store_signature`) — an identical-pin trigger refuses a duplicate write and returns the existing snapshot (the `UniverseAlreadyRegistered` precedent). Snapshot shape: `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature, created_utc, rows: [...], skipped: [...]}`. Ranked row: `{symbol: str, side: "support"\|"resistance", band_class: "A"\|"B"\|"C"\|null, distance_bps: float>=0, band_score: float, price_low: float, price_high: float, coverage: {<tf>: {has_bars, latest_window_end_utc}}, tick_evidence: bool}` — `band_class`/`distance_bps`/`band_score`/`price_low`/`price_high` all read from ONE `compute_tradability` band per symbol (selected by the SAME `(class, distance, score)` order the screen itself ranks by — see `assumptions.md` iter-3), byte-for-byte; `coverage` reused verbatim from `desk_coverage.get_desk_coverage`; `tick_evidence` = symbol present in `DatasetStore.list()`. Skip row: `{symbol, skipped: true, reason: "no_bars"\|"no_basis", coverage: {...}, tick_evidence: bool}` — `"no_bars"` = `compute_tradability`'s own `no_bar_series_for_symbol`; `"no_basis"` = a daily series exists but no session resolves (`basis_as_of: null`) — two honest, distinct reasons, never conflated. Rank order over `rows`: `(band_class rank A>B>C>null desc, distance_bps asc, band_score desc, symbol asc)`. `bar_store_signature` = a deterministic hash over `desk_coverage`'s own per-member × per-timeframe read — never a `BarStore`/JSON-file re-hash (T-4). Storage dir: a bare env-var-or-sibling-of-`desk_universe_dir_resolved()` default (the `resolve_cache_db_path` pattern) — deliberately NOT a new `Config` field (see `assumptions.md` iter-3); `config_fingerprint` stays `08e471b10130e1e2`. **iter-4 addition (behavior, not shape):** triggering a screen compute with NO universe snapshot registered now REFUSES (an honest 4xx error naming the missing universe, mirroring the top-up CLI's own no-universe message) rather than persisting an honest-empty (`universe_snapshot_id: null, rows: [], skipped: []`) snapshot — closes audit B4; the persisted snapshot SHAPE above is unchanged, this only removes one previously-reachable (and useless) append-only entry. iter-7 (J-06): `app/mcp/__init__.py` gains a `desk_screen` tool that proxies this row's own `GET /research/desk/screen` (no-argument, default shape) verbatim — no new value, no shape change; `get_endpoint` already covers the `?date=` variant unchanged. **iter-9 addition (J-08), additive to the Ranked row shape ONLY:** `basis_as_of: str \| null` (copied verbatim from `compute_tradability`'s own `basis_as_of` — the same value `_resolve_reference_close` already consumes, zero new read) and `basis_age_days: int >= 0 \| null` (a calendar-date difference between the row's own `basis_as_of` and the snapshot's own `as_of` — matches the measured 1/2/4/12-day spread in `docs/goal.md`'s J-08 rationale) are present on every ranked row of every NEW screen snapshot from this iteration forward; every snapshot recorded before this iteration lacks both fields, and `/desk` renders that absence as the honest "basis not recorded in this snapshot" state — never backfilled, never computed at read time. Skip rows never carry these fields (a skip row's `reason: "no_basis"` already means no basis resolved at all — structurally exclusive). Same owner (`desk_screen.py`), same endpoint (`GET /research/desk/screen`) — no new Data-Contract row, no new endpoint. |
| Screen compute progress | `app/research/desk_screen_compute.py` (`DeskScreenComputeManager`, shipped J-03, iter-3) | `POST /research/desk/screen/compute` (trigger, body `{"screen_date": "YYYY-MM-DD"}` REQUIRED — 422 if absent, never defaults to today), `GET /research/desk/screen/compute` (poll), `POST /research/desk/screen/compute/cancel` (cancel) — mirrors `/research/desk/topup/compute*` exactly | shape: `{"id": str, "state": "running"\|"done"\|"cancelled"\|"failed", "screen_date": str, "started_utc": str, "finished_utc": str \| null, "error": str \| null, "reused": bool, "screen_id": str \| null, "progress": {"members_total": int, "members_done": int, "current": str \| null}}`; single-flight; page-load GETs never trigger a compute; process-scoped bookkeeping, never a research value; an identical-pin trigger over an already-recorded snapshot returns it without recomputing (T-6/append-only). **`reused`/`screen_id` are an iter-4 (J-04) ADDITIVE amendment to this row's shape** (the fields did not exist before iter-4): `screen_id` is the resulting persisted snapshot's own `id` (populated once the job reaches a terminal state, `null` while running or before any trigger); `reused` is `true` when that snapshot already existed under the SAME 5-pin key before this job ran (a pure re-read, zero new file written) and `false` when this job's own walk is what created it — closes audit B2 (an otherwise-indistinguishable `"done"` for a fresh compute vs. a pure reuse). Computed by the SAME `DeskScreenComputeManager`, served by the SAME two routes — no second owner, no second endpoint. |
| Route list (now 3 rows) | `app/meta.py` `UI_ROUTES` | `GET /meta/ui-routes` | same owner as the unchanged row above — J-04 (iter-4) appended the `/desk` entry there in the same commit the page shipped |

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
carrying basis fields), for a new owner, endpoint, or shape. -->
