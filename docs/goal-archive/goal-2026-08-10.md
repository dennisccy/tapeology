# Tapeology — Project Goal (Era B: The Desk — a daily screening desk over a fetched universe)

> Eras 1–5D are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution,
> GOAL_ACHIEVED) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md);
> the structure-UI interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
> the **"Fast Wall" performance interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
> and the **"Clean Slate" demolition interlude (GOAL_ACHIEVED 2026-07-24, session `clean_slate`)** at
> [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md). Eras 3, 4, 5B "The Tradable
> Wall", and 5C "The Fast Wall" are frozen foundation; their records live in git history and in
> `reports/goal-session-*-delivered.md`.
>
> **This chapter is Era B of the operator's three-era pivot (A Demolition → B Desk → C Annotator,
> decided 2026-07-23).** Era A demolished the journal-era surfaces: the product today is exactly
> **Cockpit (`/`) + Structure (`/structure`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP
> surface is 15 read-only tools, and the honesty machinery (stores, gates, registry, PnL promotion
> ledger) is fully intact. The Desk is the first BUILDING era on that cleared ground: an automated
> **universe screener + screen ledger + daily briefing**, operated through the UI and through
> Claude + MCP. It is an operator-directed product era OUTSIDE the research catalog
> ([`docs/research-directions.md`](research-directions.md) has no Desk card; per its §5.6 this file
> wins for the running era). The statistics program (era-6 "The Referee") and the AI annotation
> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
>
> **The Desk adds ZERO new research math.** It orchestrates, persists, and surfaces the frozen
> 5B/5C computations (tradable-map bands, level classes, bar coverage) across many symbols. Every
> new number it serves is either read verbatim from an existing canonical owner or is a new
> desk-owned value (rank rows, coverage rows, snapshot metadata) with exactly one new owner.

## Vision

The instrument can read one symbol deeply — levels, zones, tradable bands, case studies, edge
report — but the operator starts every day with the OPPOSITE problem: *which of the ~100 liquid
names deserves the instrument today?* Era B builds that answer as a product:

1. **A fetched, registered universe.** S&P 100 constituent membership is fetched from a documented
   public source on explicit operator command and registered as a dated, checksummed, append-only
   **universe snapshot** — never silently refetched, never edited, never a signal input. The suite
   and the UI run keyless on a committed fixture snapshot; live fetch is an operator act.
2. **An honest bar library over that universe.** A coverage view says, per member, which
   timeframes have bars and how fresh they are — read from the durable `bar_index`, never by
   re-hashing stores. An explicit, resumable **top-up** run fetches missing/stale series through
   the existing keyless Yahoo seam, store-first (a symbol×timeframe already frozen in the store is
   reused, never re-fetched).
3. **An operator-run screen with an append-only ledger.** One button (and one CLI, and one POST)
   walks the pinned universe snapshot as-of a screen date and summarizes, per symbol, what the
   FROZEN tradable-map computation says: best band, band class, distance from the last daily close
   in bps, band score, coverage and tick-evidence badges. The ranked result persists as an
   append-only **screen snapshot** keyed by its inputs (screen date, as-of, universe snapshot,
   `config_fingerprint`, bar-store state) — identical inputs reproduce byte-identical rows, and
   a member with no bars appears as an honest `skipped: no bars` row, never a guess. Because every
   row is as-of-stamped and lookahead-free, a FUTURE era can measure whether the desk's top-ranked
   walls produced reactions — the ledger is tomorrow's evidence, not today's advice.
4. **A briefing the operator (and Claude) actually opens.** A third page — **`/desk`** — renders
   the latest screen as a dense, descriptive briefing with full provenance, an honest
   "Desk screen not computed yet." empty state, a Run Screen button with live progress, browsable
   screen history, and per-row drill-in that preloads `/structure` for that symbol and as-of.
   Two new read-only MCP tools expose the same payloads byte-identically, so the desk can be
   operated from a Claude conversation end to end.

The deliverable: the two-page instrument becomes a three-page **desk** — universe in, briefing
out, every number owned once, every run explicit, every record append-only and evaluable later.

## Target Users

- The project owner (a discretionary intraday trader) who starts the day on `/desk`: run the
  screen, read the briefing, drill into `/structure` for the names whose walls are close.
- The same owner operating through **Claude + MCP**: `desk_universe` / `desk_screen` (plus the
  existing 15 tools) make the whole desk readable from a conversation.
- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.

## Foundation invariants (still law — eras 1–5D)

The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
deterministic & reproducible; no secrets in source; research read-only over the engine; record
integrity; source/feed/`config_fingerprint` honesty. Its surface inventory is the POST-demolition
one: `/` and `/structure` (this era adds `/desk`).

1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era — every new
   `desk_*` Config field takes §0.4 **Path A** (exclusion + stability test + counter-test); a pin
   movement is a defect, full stop.
2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
   cache), `edge_report*.py`, `backtests.py`, the strategy registry (`v1` + `structure_tape` +
   `structure_tape_map`), `profiles.py` (`default`), the champion pointer — stay behaviorally
   byte-identical. The desk READS them; it never re-implements, re-tunes, or re-grades.
3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only
   immutability, split freezing, the durable accelerator DBs (`bar_index`, `dataset_index`,
   edge-report caches, setups scan cache, tradability cache) — are untouched in format and
   discipline. Registered datasets and bar series are never deleted, re-tagged, or
   content-perturbed. The era ADDS a universe store and a screen store under the same discipline.
4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, MCP `pnl_ledger`)
   stays append-only and intact; the champion pointer does not move this era.
5. The **kept surfaces as shipped**: the cockpit (live/sim/historical tape, `PriceChart.tsx`
   container behaviors, panels) and `/structure` (Load flow, Tradable Map, Case Studies, Edge
   Report + Compute button, fetch control + provenance badge) — including **both charts**
   (`StructureChart.tsx`, `PriceChart.tsx`) — keep working exactly as shipped. The ONLY sanctioned
   `/structure` edit is J-05's additive query-param prefill of the existing Load form.
6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this era
   adds two GET-proxy tools (15 → 17) and never adds writes.

### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1

**Ratified and IN INVENTORY for this era**, in addition to everything named above: the
price-less-bar repair the chain landed in iteration 4, comprising exactly

- `apps/backend/app/providers/adapters/yahoo.py` — `_is_priced_row` drops a vendor row that
  carries no price at the fetch seam (an all-priceless window still raises `NoDataForWindow`);
- `apps/backend/app/research/bars.py` — `BarStore.record` refuses a non-finite price before any
  write (`NonFiniteBarPriceError`, mapped to 422), and `_merged_rows` excludes already-recorded
  price-less **rows** on read, reporting them through the existing `integrity_errors` channel;
- `apps/backend/app/research/routes.py` — one `except NonFiniteBarPriceError` clause on
  `record_bar_series`, mapping the refusal to the same honest 422 the empty-window refusal already
  uses (an added `except` + import line; no existing behavior altered);
- `apps/frontend/components/StructureChart.tsx` — a finite-value guard on the OHLC series
  (defence in depth);
- `apps/backend/tests/test_structure_chart_viewport.py` — the one chart-guard assertion relaxed
  from exact text to a pattern, to match the guarded expression above;
- `apps/backend/tests/test_bars.py` — six ADDED tests covering the rail (write refusal per field,
  whole-series refusal, checksum integrity of a planted price-less series, read-time row
  exclusion + its `integrity_errors` report, append-only file untouched by exclusion, memo
  preserved). Additions only — no existing test in this file was modified or removed;
- `apps/backend/tests/test_yahoo_adapter.py` — five ADDED tests for the vendor-seam drop
  (all-NaN row, real rows undisturbed, all-priceless window raises, NaN volume). Additions only;
- `apps/backend/tests/test_bars_api.py` — one ADDED test proving the merged read never serves a
  null-priced candle. Additions only.

**Why:** the vendor genuinely serves a price-less AAPL daily row. Before the repair, one Top-up
click persisted `NaN`-priced bars into the append-only store, which crashed `/structure`'s chart
and silently emptied the tradable map (`compute_tradability("AAPL", as_of=2026-07-25)` returned
`bands: []`). The repair restores honest behavior; it changes nothing for all-finite data, and the
pinned wall still computes `resistance 300.11–302.2 class A score 171`.

**Scope of the ratification, precisely:** the 60 already-affected bar series stay **on disk,
untouched** — excluded row-by-row on read, never deleted, re-keyed, or rewritten. The pin
`08e471b10130e1e2` does not move. `bars.py`'s file format, checksums, append-only immutability and
split freezing are unchanged; only its write-time refusal and read-time row exclusion are new.
This ratification does NOT open `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, or any guard
test to further edits — anything beyond the eight files above still needs a new ratification.

Where the clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
subject to **R-1**.

## Success Criteria

In priority order — kept-value integrity outranks new-surface completeness outranks convenience:

1. **Nothing kept regresses.** Full backend suite green (1169 pass / 7 skip at era open — grows,
   never shrinks); engine equivalence proves byte-identical `default` outputs;
   `Config().config_fingerprint()` prints `08e471b10130e1e2` in every iteration; every kept `/`
   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified
   (subject to **R-1**).
2. **The universe is honest.** Membership comes only from registered, dated, checksummed,
   append-only snapshots; the parser validates (charset, count bounds, normalization) or fails
   with an honest error — it NEVER emits a guessed or partial list; the committed fixture keeps
   every test and default UI state keyless; live fetch happens only on explicit operator command.
3. **The screen is deterministic and evaluable.** A screen run pins (universe snapshot id, screen
   date, as-of, `config_fingerprint`, bar-store signature); identical pins reproduce byte-identical
   rows; members without bars are honest `skipped` rows; snapshots are append-only and never
   backfilled or recomputed in place; every row's structure numbers match the canonical owners
   byte-for-byte for the same inputs.
4. **The briefing is a real product surface.** `/desk` is the third nav row (data-driven from
   `app/meta.py`); it renders ranked rows with descriptive chips + provenance, honest empty/
   partial states, a Run Screen button with progress + cancel, browsable history, and drill-in
   that lands on `/structure` preloaded — all browser-verified with screenshots.
5. **The desk is Claude-operable.** `desk_universe` and `desk_screen` are byte-identical GET
   proxies; `ui_route_map` lists the three routes; the MCP suite proves the 17-tool contract.

## Key Capabilities

1. **Universe subsystem (new data kind, honest by construction).** A universe vendor seam (the
   bars-vendor pattern) fetching S&P 100 membership from ONE documented public source; a parser
   contract (ticker charset `[A-Z.-]{1,6}`, count sanity 90–110, **Yahoo normalization
   `BRK.B → BRK-B`**, dedupe, sorted output); registration as
   `apps/backend/.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json` (frozen JSON = source of
   truth; any index over it is derived/rebuildable); a committed fixture snapshot under
   `apps/backend/tests/fixtures/` for hermetic tests + default keyless UI;
   `GET /research/desk/universe` serving snapshot list + latest membership with honest emptiness.
2. **Coverage + top-up.** `GET /research/desk/coverage` (or a `universe` payload block): per-member
   × per-timeframe bar presence + freshness read from `bar_index` (NEVER re-hashing the store);
   an explicit operator-run top-up (POST + CLI) that walks members store-first through the
   existing `POST /research/bars` fetch path, resumable, worker-capped, logging per-symbol
   outcomes; the timeframe set = exactly what `compute_levels`/`compute_tradability` read for a
   daily-close screen (verify at build time; era-5 contract: `4h` is resampled from `1h`, never
   fetched; intraday microscope tfs stay per-symbol on `/structure`).
3. **Screen compute + append-only ledger.** An operator-run screen (POST + CLI + `/desk` button)
   over the pinned latest universe snapshot: per member, call the CANONICAL owners
   (`compute_tradability` / levels / `bar_index`) as-of the screen date's session close and
   summarize best band, class, distance-from-close (bps), band score, coverage + tick-evidence
   badges; deterministic rank order = (band class A>B>C, then distance asc, then band score desc,
   then symbol asc); single-flight + progress + cancel via the 5C compute-manager pattern;
   persistence as append-only screen snapshots (frozen JSON + derived index) with full input pins;
   `GET /research/desk/screen` (latest / `?date=`) + honest `"Desk screen not computed yet."`.
4. **The `/desk` briefing page.** Third nav row; latest-screen briefing table (rank, symbol,
   band class chip, distance chip, score, coverage/evidence badges, skipped rows grouped
   honestly); provenance line (universe snapshot id + date, as-of, fingerprint, bar-store
   signature); Run Screen + top-up buttons with live progress + cancel; screen history list;
   dark/dense/terminal-grade per house style.
5. **Drill-in + `/structure` prefill.** Clicking a briefing row navigates to
   `/structure?symbol=<sym>&asof=<iso>`; `/structure` gains query-param PREFILL of its existing
   Load form (prefill + auto-Load; `apps/frontend/app/structure/page.tsx` inputs at ~:2057/:2070)
   — no other `/structure` behavior changes; the desk never recomputes structure values.
6. **MCP contract v3 — 17 read-only tools.** Add `desk_universe` → `/research/desk/universe` and
   `desk_screen` → `/research/desk/screen` to `_STATIC_PATHS` (`app/mcp/__init__.py:85`);
   `get_endpoint` allowlist (`/tape/`, `/research/`, `/meta/`) already covers the new paths
   unchanged; `tests/test_mcp_server.py` proves the 17-tool contract with byte-identity and
   honest-error clauses.

## Non-Goals

- **No statistics program.** No new gates, CIs, nulls, multiple-testing control, or promotion
  logic — that is era-6 "The Referee" (future). The screen RANKS by existing descriptive
  structure metrics; it never claims edge, probability, or expectancy.
- **No annotation layer.** Human/AI pattern annotation, dispositions, notes, or any manual input
  path on desk records is Era C "The Annotator" (designed separately). This era's ledger records
  MACHINE output only.
- **No strategy/champion work.** No new strategies/profiles, no backtest changes, no champion
  movement, no PnL-ledger rows beyond what existing machinery already writes.
- **No scheduling.** No cron, daemon, auto-refresh, or market-hours trigger — every fetch,
  top-up, and screen run is an explicit operator act (UI button / CLI / POST).
- **No tick-data expansion.** No new dataset recording, no credential work; tick evidence badges
  reflect the 11 recorded dataset symbols as they stand.
- **No engine, chart, or kept-surface work.** `app/engine/` untouched; `StructureChart.tsx`
  untouched **except R-1's finite-value guard**; `PriceChart.tsx` untouched; `/structure` untouched
  beyond the J-05 prefill.
- **No fingerprint epoch bump.** Path A only; the pin `08e471b10130e1e2` does not move.
- **No second market, no options/sentiment/news data, no paid services.** The one new external
  read is the documented constituents source; membership is universe METADATA, never a signal
  input (the roadmap's earnings-calendar exclusion-only precedent).

## Constraints

- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm),
  `lightweight-charts`, dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`,
  frontend `http://localhost:3000` (browser-QA rig on `:8301`/`:3301`). No new runtime dependency
  (the universe fetch uses the stdlib/HTTP client patterns the Yahoo adapter already uses).
- **Config discipline (§0.4 Path A, every time):** every new SEMANTIC knob is a `Config` field
  (`desk_universe_source_url`, `desk_universe_min_members`, `desk_universe_max_members`, plus any
  the build genuinely needs) added to the `config_fingerprint()` exclusion set
  (`app/config.py:1312`) **in the same commit**, with (i) a stability test proving the pin is
  unchanged and (ii) a counter-test proving the field alters the NEW path's output, and its value
  embedded in the desk payloads it shapes (provenance duty — the `structure_tape_*` worked
  example). Operational knobs (worker counts, timeouts, store dirs) may be env vars per the 5C
  precedent (`TAPEOLOGY_DATASET_DIR` pattern); a field that changes SERVED VALUES is never an env
  var.
- **Snapshot discipline:** universe + screen snapshots are frozen JSON files (source of truth,
  content-checksummed, append-only) with derived, rebuildable indexes — the `BarStore`/
  `dataset_index` pattern. No snapshot is ever edited, re-keyed, or silently regenerated;
  re-running a screen for the same pins either reproduces byte-identical content or refuses with
  an honest already-recorded response. `journal.db` gets NO new tables (schema stays v8).
- **No-lookahead as-of rule (morning-markup convention):** a screen for date D builds its map from
  the last completed session STRICTLY BEFORE D (`tradability._resolve_basis`; every level read is
  bounded to that prior session's close), so D's own session never enters the map and the forward
  measurement reads D's own session out-of-sample. D therefore names the TRADE day, not the data
  day. The recorded `as_of` (`D T23:59:59Z`) is the snapshot key's upper bound and part of the
  snapshot key; there is no "refresh today's screen in place" — a new run is a new snapshot.
- **Single source of truth:** the desk owns ONLY its new values (universe membership/metadata,
  coverage rows, screen rank rows). Band geometry, classes, scores come from
  `compute_tradability` (`app/research/tradability.py:381`) / `levels.py` verbatim; coverage
  comes from `bar_index`; the desk NEVER recomputes, re-grades, or caches a divergent copy.
  The coherence-auditor hard-fails violations.
- **Copy discipline:** all desk copy is descriptive measurement (distances, classes, counts,
  dates) — no advice, imperative, or prediction language; `tests/test_copy_discipline.py`'s
  frontend-literal lint (:220) covers the new page automatically and must stay green unmodified.
- **Guard tests (kept, never edited):** `tests/test_no_execution_path.py`,
  `tests/test_no_credential_in_artifacts.py`, the fast_wall source-introspection guards
  (`test_backtests.py`, `test_setups.py` pins), the chart guard suites, and the 13 fingerprint
  pin assertions (e.g. `test_profile_equivalence.py:114`) all pass byte-unmodified all era — the
  single exception is **R-1**'s `test_structure_chart_viewport.py` assertion, relaxed to a pattern
  to match the guarded expression; no further guard-test edit is authorized.
- **Hermetic tests:** the suite stays keyless on committed fixtures — the universe fixture
  snapshot ships in-repo; NO test performs a network fetch; live constituents fetch + 100-symbol
  top-up + real screens are operator-run verifications, never CI gates.
- **Browser evidence:** `rm -rf apps/frontend/.next` + rebuild before any browser verification
  (the stale-build trap); every browser acceptance needs a screenshot — no screenshot ⇒ the
  journey is `unknown`, never `passing`; route captures in evidence scripts use per-route
  `curl --max-time`.
- **Compute-manager reuse:** top-up and screen runs follow `EdgeReportComputeManager`
  (`app/research/edge_report_compute.py:108`; routes `POST/GET/POST-cancel` at
  `app/research/routes.py:1268/1293/1302`) — single-flight, snapshot-pollable progress,
  cancellable, CLI-runnable. Page-load GETs NEVER trigger computes (the 5C lesson).

## Design Direction

Unchanged house style: dark-only, dense, professional, terminal-grade; honest empty/degraded
states are first-class copy (`"Desk screen not computed yet."`, `"skipped: no bars"`); the
briefing reads like a trading-floor sheet, not a dashboard toy; no marketing chrome.

## Product Shape

Nav (top bar) after this era: **Cockpit `/` · Structure `/structure` · Desk `/desk`** — data-driven
from `app/meta.py` `UI_ROUTES` (:27, the single owner); `GET /meta/ui-routes` and MCP
`ui_route_map` reflect it verbatim.

**Data Contract — new rows (each value computed once, one owner):**

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Universe snapshots + membership | new `app/research/desk_universe.py` (name at build discretion) | `GET /research/desk/universe` |
| Per-member bar coverage/freshness | same desk module (reads `bar_index` only) | `GET /research/desk/coverage` (or a block of the universe payload — ONE home, decided at build) |
| Screen snapshots, rank rows, skip rows | new `app/research/desk_screen.py` | `GET /research/desk/screen` |
| Top-up / screen compute progress | desk compute manager (5C pattern) | `GET /research/desk/*/compute` poll endpoints |
| Route list (now 3 rows) | `app/meta.py` | `GET /meta/ui-routes` |

**Unchanged owners (the desk reads them verbatim):** bands/scores → `tradability.py`; levels/
zones/classes → `levels.py`; bars/candles → `bars.py` + `bar_index`; datasets → `datasets.py`;
edge cells → `edge_report.py`; ledger rows → `pnl_ledger.py`; registry/champion →
`strategies.py`/store; taxonomy labels → `taxonomy.py`.

## Build anchors & weak-model traps (era B)

Anchors verified against `main @ 05b50ef` (2026-07-25) — **re-locate by symbol name (grep), never
by line arithmetic**:

- Yahoo fetch seam: `app/providers/adapters/yahoo.py:207` (`YahooAdapter`, `fetch_bars` :233);
  explicit bar fetch/register: `POST /research/bars` (`app/research/routes.py:519`), store-first.
- Tradable map: `compute_tradability(store, symbol, as_of_epoch, config)`
  (`app/research/tradability.py:381`) + durable `tradability_cache.db`.
- Compute-manager pattern: `EdgeReportComputeManager` (`app/research/edge_report_compute.py:108`),
  routes at `routes.py:1268/1293/1302`, `/structure` Compute button + progress poll as UI model.
- Stores: `BarStore` (`app/research/bars.py:210`); `bar_index.db` (coverage truth — 3 symbols have
  bars at era open: AAPL/AMD/MSFT); `.data/datasets` + `dataset_index.db` (tick evidence — exactly
  these 11 recorded symbols: AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG, SPY, TSLA).
- MCP: `_STATIC_PATHS` (`app/mcp/__init__.py:85`), parameterized paths (:107), `get_endpoint`
  allowlist (:55–65); contract suite `apps/backend/tests/test_mcp_server.py`.
- Config: `config_fingerprint()` + exclusion set (`app/config.py:1312`); pin literal
  `08e471b10130e1e2` asserted at 13 sites (e.g. `tests/test_profile_equivalence.py:114`).
- Frontend: nav auto-follows `meta.py`; `/structure` Load inputs (`app/structure/page.tsx`
  ~:2057/:2070) are the J-05 prefill target; copy lint `tests/test_copy_discipline.py:220`.

Traps (all learned the hard way in prior eras — read before EVERY iteration):

- **T-1 · Parser honesty.** The constituents source is a live web page: on ANY validation failure
  (charset, bounds 90–110, table shape) the fetch fails with an honest error — never a guessed,
  partial, or hard-coded fallback list. The committed fixture is for TESTS and default UI, never
  a silent runtime fallback for a failed live fetch.
- **T-2 · Symbol normalization.** Yahoo uses dashes: `BRK.B → BRK-B`, `BF.B → BF-B`. Normalize at
  ingestion, store the normalized form, keep the raw form in snapshot metadata. Watch dual-class
  dupes after normalization.
- **T-3 · Universe store ≠ dataset store.** Both are append-only JSON+index, but they are
  DIFFERENT owners with different keys — never write universe data through `datasets.py` or
  register screens as datasets.
- **T-4 · Coverage reads the index.** Per-member coverage comes from `bar_index` lookups; walking
  or re-hashing the JSON `BarStore` per page load is the 5C 31.4s mistake. GETs are cache-reads;
  computes are explicit.
- **T-5 · Path A or nothing.** Every new Config field: exclusion set + stability test +
  counter-test + payload provenance, same commit. No field that shapes a SERVED value hides in an
  env var; the pin never moves (T8 of the roadmap — no third fingerprint move exists).
- **T-6 · Determinism means no wall-clock.** Screen `as_of` derives from the requested screen
  date (session close), never `now()`; snapshot ids derive from content checksums; re-runs with
  identical pins are byte-identical. Progress timestamps live in compute-manager state, never in
  snapshot content.
- **T-7 · Tick-evidence honesty.** A "tick evidence" badge means the symbol is among the 11
  recorded dataset symbols — it never implies bars exist, and vice versa; the two badges are
  independent reads (datasets vs `bar_index`).
- **T-8 · `/structure` prefill is additive.** J-05 touches the Load form's initial values +
  auto-Load from query params ONLY — no chart edits, no Load-flow rewrites, no default changes
  when params are absent.
- **T-9 · Clean rebuild before browser evidence.** `rm -rf apps/frontend/.next`, rebuild, restart
  both processes before any browser pass — a stale build bakes the wrong API base and ghost
  pages, producing false results in both directions.
- **T-10 · Evidence honesty.** No screenshot ⇒ `unknown`, never `passing`; backend-only proof
  never satisfies a browser acceptance line; the real 100-symbol top-up and real screens are
  operator-run acts reported as such, never simulated by fixtures pretending to be live.
- **T-10a · Native browser UI is photographed on the approved headed rig** (OWNER RATIFICATION,
  2026-07-30). Chrome draws native `title` tooltips as a separate X window owned by the browser
  process, so CDP screenshots — every headless capture, Playwright's included — structurally
  cannot contain them; iterations 19–21 each failed on exactly this and the session halted
  `STALLED` for an owner ruling. The owner's ruling is: **the screenshot requirement stands
  unchanged**, and it is satisfied by `project-extensions/qa-rig/` (own Xvfb display, real headed
  Chrome, real X pointer, X-level grab — see its README). A DOM read-out of the `title` string is
  a useful cross-check but is NOT the artifact and never substitutes for it. The rig refuses to
  write a file unless the tooltip actually rendered as a new X window AND the hovered element's
  own `title` carries the required substring, so a rig capture cannot be a false positive.

## Must-have user journeys

Journeys **J-01 – J-07** form the era. **Frontend is present** (J-04, J-05, and J-07 are
browser-verifiable). The default suite stays keyless on committed fixtures. Natural dependency
order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding continuously.

- **J-01: Universe ingestion — fetched, registered, honest**
  - Steps:
    1. Build the universe vendor seam + parser (contract per Key Capability 1: one documented
       source URL as a Path-A Config field, charset check, 90–110 bounds, `BRK.B → BRK-B`
       normalization, dedupe, sorted members) and the universe store
       (`.data/universe/universe-<date>-<checksum12>.json`, frozen JSON + derived index).
    2. Commit the fixture snapshot under `apps/backend/tests/fixtures/` and wire the hermetic
       test path (env-scoped universe dir, the `TAPEOLOGY_DATASET_DIR` pattern).
    3. Expose `POST /research/desk/universe/fetch` (explicit operator act; honest failure body on
       validation errors) and `GET /research/desk/universe` (snapshot list + latest membership;
       honest empty state before any registration).
    4. Unit-test the parser contract (fixture HTML → exact member list; each validation failure →
       honest error, no partial list) and snapshot immutability (re-registration of identical
       content is a no-op/refusal, never a rewrite).
  - Acceptance: with no snapshot, `GET /research/desk/universe` serves the honest empty payload;
    after registering the FIXTURE snapshot the GET lists it with checksum + member count in
    90–110 and normalized symbols; a deliberately corrupted fixture fails with the honest error
    and registers nothing; the full suite is green, keyless, with
    `Config().config_fingerprint()` still `08e471b10130e1e2` and the new field counter-tested.
    *(Keyless; automated. The LIVE Wikipedia fetch is an operator-run verification, reported
    honestly as run-or-not-run.)*

- **J-02: Coverage + explicit bar top-up over the universe**
  - Steps:
    1. Serve per-member coverage (bars present per required timeframe + freshness, read from
       `bar_index` only) for the latest universe snapshot — ONE owner per the Product Shape row.
    2. Pin the top-up timeframe set = exactly what `compute_levels`/`compute_tradability` read
       for a daily-close screen (verify against `levels.py` at build time; `4h` resampled from
       `1h` per the era-5 contract; no 5m/1m in the desk top-up).
    3. Build the operator-run top-up (POST + CLI, compute-manager pattern: single-flight,
       progress with per-symbol outcomes, cancel, resumable) walking members store-first through
       the existing `POST /research/bars` path.
    4. Test with fixtures: coverage truth-table (bars-present vs missing members), top-up
       resumability (a cancelled run resumes without re-fetching frozen series), and the
       GET-never-computes rule.
  - Acceptance: coverage for the fixture universe reports bars-present for exactly the members
    the era-open store holds (AAPL/AMD/MSFT) and bars-missing for every other member (asserted
    per-member in a truth-table test); a fixture-scoped top-up run completes with honest
    per-symbol outcomes and a second run reports all-reused (store-first proven); coverage GET
    latency is index-read fast (no store re-hash); suite green + pin unchanged. *(Keyless core;
    the real ~100-symbol Yahoo top-up is an operator-run act with its outcome — including
    partial coverage — reported honestly.)*

- **J-03: The screen — pinned inputs, append-only snapshot, deterministic rank**
  - Steps:
    1. Build the screen compute (POST + CLI + compute-manager): walk the pinned latest universe
       snapshot as-of the requested screen date's session close; per member call the canonical
       owners (`compute_tradability` :381 / levels / `bar_index`) and summarize best band, class,
       distance-from-close bps, band score, coverage + tick-evidence badges; members without
       bars → `skipped: no bars` rows.
    2. Rank deterministically: band class (A>B>C), then distance asc, then band score desc, then
       symbol asc — the order is data, recorded in the snapshot.
    3. Persist as an append-only screen snapshot (frozen JSON + derived index) keyed
       (screen_date, as_of, universe snapshot id, `config_fingerprint`, bar-store signature);
       identical pins → byte-identical content (tested); same-pins re-run → honest
       already-recorded response, never a rewrite.
    4. Serve `GET /research/desk/screen` (latest, `?date=`, and a snapshot list) with the honest
       `"Desk screen not computed yet."` payload before any run.
  - Acceptance: on the fixture universe + fixture bars, a screen run produces the expected ranked
    rows + skipped rows (golden-tested); a re-run with identical pins is byte-identical; the
    snapshot embeds every pin + the Path-A field values (provenance duty); rows' band values match
    `GET /research/tradability` byte-for-byte for the same symbol/as-of; suite green + pin
    unchanged. *(Keyless; automated. A real screen over real bars is an operator-run act.)*

- **J-04: The `/desk` briefing page**
  - Steps:
    1. Add the `/desk` row to `UI_ROUTES` (`app/meta.py:27`) — nav + `ui_route_map` follow
       automatically; never hand-edit a nav component.
    2. Build the page: latest-screen briefing table (rank, symbol, class chip, distance chip,
       score, coverage/evidence badges; skipped rows grouped under an honest heading), the
       provenance line (universe snapshot id + date, as_of, fingerprint, bar-store signature),
       screen-history list, and the honest empty state when no screen exists.
    3. Wire Run Screen + Top-up buttons to the compute endpoints with live progress + cancel
       (the `/structure` Compute-button UX pattern); page-load GETs never trigger computes.
    4. Keep all copy descriptive (distances, classes, counts, dates); the copy-discipline lint
       stays green unmodified.
  - Acceptance: in a real browser (after the T-9 clean rebuild) — nav shows **Cockpit ·
    Structure · Desk**; `/desk` with no screen shows `"Desk screen not computed yet."` + enabled
    Run Screen (screenshot); after a fixture-scoped screen run the briefing renders ranked rows
    with chips + provenance and groups skipped members honestly (screenshot); Run Screen shows
    live progress and an in-flight second trigger is refused (single-flight, screenshot);
    `GET /meta/ui-routes` lists exactly the three routes. *(Browser-verifiable; keyless via the
    fixture-scoped backend.)*

- **J-05: Ledger history + drill-in to `/structure`**
  - Steps:
    1. Render the screen-history list on `/desk` (date, member/skip counts, provenance summary);
       selecting a past screen renders THAT snapshot's rows verbatim (no recompute).
    2. Add query-param prefill to `/structure` (`?symbol=&asof=`): prefill the existing Load
       form inputs (~:2057/:2070) and auto-Load — additive only (T-8), no behavior change when
       params are absent.
    3. Make each briefing row a drill-in link to `/structure?symbol=<sym>&asof=<as_of>`.
    4. Guard-test that the desk pages contain no structure recomputation (rows read snapshot
       JSON; `/structure` values come from its existing endpoints).
  - Acceptance: in a real browser — opening a PAST screen renders its recorded rows (byte-equal
    to the snapshot payload, spot-checked); clicking a row (e.g. AAPL) lands on `/structure`
    with symbol + as-of prefilled and the wall/bands loaded for that date (screenshot proving
    the pinned AAPL 2026-06-22 flow still renders 300–302.4-region bands when drilled from a
    screen containing it); `/structure` with no params behaves exactly as shipped (screenshot).
    *(Browser-verifiable; keyless.)*

- **J-06: MCP contract v3 — 17 read-only tools**
  - Steps:
    1. Add `desk_universe` → `/research/desk/universe` and `desk_screen` →
       `/research/desk/screen` to `_STATIC_PATHS` (`app/mcp/__init__.py:85`); `get_endpoint`
       allowlist unchanged (the new paths are under `/research/`).
    2. Update `tests/test_mcp_server.py` to the 17-tool contract, keeping byte-identity and
       honest-error clauses for every tool (including the two new ones against the honest
       empty states).
    3. If the neutral asset source changed, re-render per the maintenance protocol — never
       hand-edit generated mirrors.
  - Acceptance: the MCP server advertises exactly 17 tools; `desk_universe`/`desk_screen` outputs
    are proven byte-identical to their curl equivalents (empty AND populated fixture states);
    `get_endpoint` on `/research/desk/screen` proxies verbatim; the MCP suite is green.
    *(Keyless; automated.)*

- **J-07: The kept product stands — regression sentinel**
  - Steps:
    1. Run the full backend suite + engine equivalence; verify every guard test
       (`test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, source-introspection
       guards, chart guard suites, the 13 pin assertions) passes byte-unmodified — the sole
       exception is **R-1**'s `test_structure_chart_viewport.py` assertion;
       `Config().config_fingerprint()` prints `08e471b10130e1e2`.
    2. In a real browser (after T-9): walk the kept product — sim cockpit (`SIM-BUYER` settles
       `buyer_control`, chart candles + timeframe switch + band overlay + live tape bars),
       `/structure` Load for pinned AAPL as-of 2026-06-22 (the 300–302.4 wall band renders),
       Case Studies drill-in, Edge Report honest state — screenshots for each.
    3. Verify the desk additions did not perturb kept values: kept-route responses byte-identical
       on identical inputs vs a baseline captured **from the era-open commit `047c38e`** (check it
       out into a scratch worktree and capture per-route with `curl --max-time`; no baseline was
       recorded at era open, so it is reconstructed from git at verification time). Two routes are
       expected to differ and are exempt, because this era's own inventory changes them:
       `/meta/ui-routes` (2 → 3 rows) and the MCP tool list (15 → 17). Where a route's body differs
       for any OTHER reason, the difference is explained against **R-1** or it is a defect.
       `/research/taxonomy` unchanged; WS frame = engine projection only.
    4. Confirm the era's cumulative diff stays inside this goal.md's inventory (new desk modules/
       routes/page/tools + the named `meta.py`/MCP/test touches + the J-05 prefill + **R-1**'s eight
       files) — anything else is surfaced BEFORE it lands.
  - Acceptance: full suite green under the unchanged pin; every browser step evidenced by
    screenshot (T-10); kept-route byte-identity holds on every route outside step 3's two named
    exemptions; nav = exactly three routes; MCP = exactly 17 tools; zero out-of-inventory changes
    in the cumulative diff, reading "inventory" as including **R-1**. *(Keyless core;
    browser-verifiable.)*

<!-- AUTO:journeys -->

- **J-08: Every ranked briefing row names the bar its distance was measured from**
  - Steps:
    1. Record the basis on every NEW screen row: `basis_as_of`, copied **verbatim** from the value
       `compute_tradability` already returns (`tradability.py:381`'s
       `{"bands", "no_bar_series_for_symbol", "basis_as_of"}` — the same value
       `desk_screen._resolve_reference_close` already consumes), plus `basis_age_days`, a plain
       arithmetic derivation from the row's own `basis_as_of` and the snapshot's own `as_of` (the
       `distance_bps` precedent, `desk_screen.py:197`). Both are desk-owned row fields with exactly
       one owner (`desk_screen.py`) and one serving endpoint (`GET /research/desk/screen`) — zero
       diff to `tradability.py`/`levels.py`/`bars.py` (no new field on any frozen return shape) and
       zero new `Config` field.
    2. Register both fields in the Data Contract's "Screen snapshots, rank rows, skip rows" row; the
       pinned snapshot key (screen date, as_of, universe snapshot id, `config_fingerprint`,
       bar-store signature) is unchanged — only NEW snapshots' row content grows.
    3. Keep the append-only rail absolute: never backfill, rewrite, or recompute an
       already-recorded snapshot; `GET /research/desk/screen` serves legacy rows exactly as
       recorded, and `/desk` renders their absent basis as an honest
       `"basis not recorded in this snapshot"` — never a value computed at read time.
    4. Surface it on `/desk`: a descriptive `basis` column beside `distance` on the ranked table
       (e.g. `basis 2026-07-13 · 12 d before as-of`), full precision in the row anchor's existing
       consolidated honesty tooltip (the iter-7 pattern), copy = descriptive measurement only (no
       advice, imperative, urgency, or prediction language).
    5. Test: a fixture-scoped golden screen asserting the exact `basis_as_of` + `basis_age_days` per
       ranked row and byte-identical row content on a re-run under identical pins; a guard test that
       the desk never re-derives the basis (it comes from `compute_tradability`'s return — no extra
       bar scan in the row builder, none in the frontend); the MCP `desk_screen` tool stays a
       byte-identical GET proxy (17-tool contract unchanged).
  - Acceptance: on the fixture-scoped rig a NEW screen run records `basis_as_of` and
    `basis_age_days` on every ranked row, and each row's `basis_as_of` is byte-identical to
    `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s `basis_as_of`
    (**single source of truth**: the desk reads the canonical owner verbatim, and both new values
    are registered in the Data Contract with `desk_screen.py` as their only owner and
    `GET /research/desk/screen` as their only serving endpoint — this SSOT criterion stands in place
    of a PnL-ledger append, which this era's Non-Goals forbid); a re-run under identical pins
    reproduces byte-identical rows and a same-pins re-run still returns the honest already-recorded
    response; the previously recorded screen snapshots are proven byte-identical on disk (checksums
    unchanged, nothing backfilled) and `/desk` renders their rows with the honest
    `"basis not recorded in this snapshot"` state; in a real browser after the T-9 clean rebuild,
    `/desk` shows the `basis` column with at least one fresh row (age ≤ 2 d) and one stale row
    (age ≥ 10 d) legible in the same screenshot (T-10: no screenshot ⇒ `unknown`, never
    `passing`); a **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's basis
    disclosure end to end; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the
    `default` profile and `v1` byte-identical (engine equivalence green), zero diff to
    `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why:
    measured live on the canonical endpoint at as-of 2026-07-25 — `basis_as_of` spans 2026-07-24
    for AAPL (1 d) to 2026-07-13 for META/NFLX/NVDA (12 d), while the recorded snapshot
    `screen-2026-07-25-e184a7dc2f86` ranks NFLX #2 on `distance_bps 0.0` with no basis field in any
    row, so an 11-day spread of reading ages is invisible on one rank scale.)*

- **J-09: Every top-up run leaves an append-only record of what it attempted**
  - Steps:
    1. Persist the top-up's OWN per-pair outcomes — the list `run_topup` already returns
       (`desk_topup_compute.py:158`; entries `{"symbol", "timeframe", "outcome":
       "reused"|"fetched"|"failed", "detail"}` built at :184, with the vendor/HTTP detail preserved
       verbatim at :147) — as ONE frozen, checksummed, append-only run record per run, written once at
       the run's terminal state by a SINGLE shared writer that BOTH callers use (the manager worker's
       resolve path, :262/:282, and the CLI's `main`, :329): never two write paths, never a second
       outcome shape, zero change to what `run_topup` itself computes. Recorded with it: run id,
       universe snapshot id, the requested fetch window, `config_fingerprint`, started/finished UTC,
       terminal state (`done`/`cancelled`/`failed`), `pairs_total` and `pairs_attempted` — so
       "attempted and failed" and "never attempted" are distinct on the record, never conflated.
    2. Own it exactly once: a new desk module (name at build discretion, e.g.
       `app/research/desk_topup_log.py`) as the ONLY owner and `GET /research/desk/topup/runs` as the
       ONLY serving endpoint (lightweight run-meta list + the latest full record; honest-empty
       `{"runs": [], "latest": null}`, HTTP 200, before any run) — registered as a NEW row in the
       blueprint's Data Contract BEFORE the code lands, storage dir a bare env-var-or-sibling default
       like the screen store's (deliberately NOT a new `Config` field — the iter-3 precedent). The
       record describes ATTEMPTS only: bar presence and freshness keep their single owner
       (`desk_coverage` over `bar_index`) and no second coverage path is created anywhere.
    3. Keep every era rail: page-load GETs never trigger a top-up (the 5C lesson); a record is never
       rewritten, backfilled, or recomputed — a second run appends a new one; a run whose process ends
       before its terminal write records NOTHING and the ledger never invents an entry for it (its
       honest limit, asserted by a test); and NO MCP tool is added — J-06's exactly-17-tool contract
       stays green and `get_endpoint`'s `/research/` allowlist already reaches the new path.
    4. Surface it on `/desk`: a read-only "top-up runs" section beside the existing screen-history
       table (same pattern, no recompute), each run showing date + id, universe snapshot id, terminal
       state, attempted-of-total pairs and counts by outcome, and — for the latest run — every
       `failed` pair with its recorded detail rendered verbatim plus the honest count of pairs the run
       never reached; an honest empty state when no run is recorded; copy = descriptive measurement
       only (no advice, imperative, urgency, or prediction language).
    5. Test fixture-scoped: recorded outcomes byte-identical to `run_topup`'s return for the same
       walk; a cancelled run recorded as `cancelled` with `pairs_attempted < pairs_total`; a failed
       pair's detail stored verbatim; a second run appending without touching the first file; the GET
       honest-empty before any run and triggering nothing.
  - Acceptance: on the fixture-scoped rig `GET /research/desk/topup/runs` serves the honest empty
    payload before any run and, after a fixture-scoped top-up, one record whose per-pair
    `outcome`/`detail` values are byte-identical to what `run_topup` returned for that walk
    (**single source of truth**: the run record is registered in the Data Contract with the new desk
    module as its only owner and `GET /research/desk/topup/runs` as its only serving endpoint, it
    records attempts only, and coverage/freshness still comes solely from `desk_coverage` over
    `bar_index` — this SSOT criterion stands in place of a PnL-ledger append, which this era's
    Non-Goals forbid); a cancelled run records `cancelled` with `pairs_attempted < pairs_total`, and a
    run interrupted before its terminal write leaves the ledger honestly empty rather than a
    fabricated entry; a second run appends a new record while every previously recorded file stays
    byte-identical on disk (checksums unchanged); in a real browser after the T-9 clean rebuild,
    `/desk` shows the honest no-run-recorded state in one screenshot and, after a fixture-scoped run,
    the top-up-runs section with attempted-of-total, per-outcome counts and at least one `failed`
    pair's recorded detail legible in another (T-10: no screenshot ⇒ `unknown`, never `passing`); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the top-up-run disclosure end to end; and the
    full backend suite is green with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero
    new `Config` fields, the `default` profile and `v1` byte-identical (engine equivalence green), the
    MCP surface still exactly 17 tools, zero diff to
    `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`, and `tests/test_copy_discipline.py`
    green unmodified. *(Keyless core; browser-verifiable. Why: measured live 2026-07-28 —
    `GET /research/desk/topup/compute` returns `null`, so the real ~100-symbol run that populated the
    store left no trace anywhere; the frozen `BarStore` holds series for 65 symbols and 38 of the 101
    members of `universe-2026-07-25-49b33fa31680` (the alphabetical tail `MA`…`XOM`) hold none —
    exactly the 38 `skipped: no bars` rows of `screen-2026-07-27-936543601e75` (63 ranked / 38
    skipped) — while 5 further members (AXP, BAC, DIS, HD, LMT) rank with `1h` dark beside a `4h`
    series the era-5 contract resamples from that same `1h` fetch, so whether a pair was attempted,
    refused, or never reached is unknowable today.)*

- **J-10: The coverage the briefing shows is the coverage the frozen store can prove**
  - Steps:
    1. Classify the drift between the derived `bar_index` and the frozen `BarStore` using ONLY reads
       that already exist — `BarStore.list(include_bars=False)`'s healthy records plus its own
       `errors`, and `BarIndex.list()`'s indexed `series_id`s (`bar_index.py:178`) — into three
       honest classes: a series on disk with no index row (attributed to its `symbol` × `timeframe`
       from that record's own meta), an index row whose `series_id` is not on disk (reported by
       `series_id` alone — never an invented meta), and a row indexed under a checksum the store no
       longer reports. **Zero diff to `bar_index.py` and `bars.py`**: the drift is pure composition
       of their existing public reads, no new accessor, no schema change, no new index.
    2. Repair through the EXISTING `BarIndex.reindex(store)` (`bar_index.py:198`) and nothing else —
       never a second index-building path — then re-run the identical comparison and record the
       post-repair result together with `BarStore.list()`'s own `errors` **verbatim**, because
       `reindex()` is DROP-and-repopulate over HEALTHY records only: a corrupt file that the rebuilt
       index therefore cannot carry is disclosed on the record, never silently dropped.
    3. Keep it an explicit operator act and never a page-load compute (T-4 and the 5C lesson):
       trigger via `POST` through the established compute-manager pattern (`DeskTopupComputeManager`,
       `desk_topup_compute.py` — single-flight, pollable progress, cancellable), and persist ONE
       frozen, checksummed, append-only run record per run — run id, started/finished UTC, terminal
       state (`done`/`cancelled`/`failed`), `config_fingerprint`, pre-repair drift counts + the
       affected `symbol × timeframe` pairs, post-repair verification counts, and the store errors —
       written EXACTLY ONCE at the run's terminal state by a SINGLE shared writer every caller uses
       (the `desk_topup_log` J-09 discipline); a run whose process dies before that write records
       NOTHING and the ledger never invents an entry for it.
    4. Own it exactly once: a new desk module (name at build discretion, e.g.
       `app/research/desk_index_reconcile.py`) as the ONLY owner and ONE serving endpoint (exact path
       at build discretion, e.g. `GET /research/desk/coverage/reconcile/runs`) with an honest-empty
       `{"runs": [], "latest": null}` HTTP 200 before any run — registered as a NEW row in the
       blueprint's Data Contract BEFORE the code lands; storage dir a bare env-var-or-sibling default
       (the `desk_screen`/`desk_topup_log` precedent — deliberately NOT a new `Config` field); NO MCP
       tool added (J-06's exactly-17-tool contract stays green and `get_endpoint`'s `/research/`
       allowlist already reaches the path). Coverage and freshness keep their single existing owner —
       `desk_coverage.get_desk_coverage` over `bar_index` — and no second coverage path, cache, or
       copy is created anywhere.
    5. Surface it on `/desk`: a "Reconcile Index" trigger wired exactly like the existing Top-up
       button (live progress + cancel, page-load GETs trigger nothing) and a read-only reconciliation
       section beside Screen History and Top-up Runs showing the latest run's counts (series on disk,
       rows indexed, drift before, drift after, affected pairs, store errors) with an honest
       no-run-recorded empty state; copy = descriptive measurement only (no advice, imperative,
       urgency, or prediction language).
    6. Test fixture-scoped: a scoped store holding a series its scoped index has no row for →
       `GET /research/desk/coverage` reports `has_bars: false` for that pair BEFORE the run and
       `true` AFTER it, with the run record's pre/post counts matching that drift exactly; a planted
       corrupt file is recorded verbatim as a store error and simply absent from the rebuilt index
       (never fabricated); a second run appends a new record while every earlier record file stays
       byte-identical; the GET is honest-empty before any run and triggers nothing.
  - Acceptance: on the fixture-scoped rig, a pair whose series the frozen store holds but the derived
    index has no row for reports `has_bars: false` from `GET /research/desk/coverage` before the run
    and `true` after exactly one reconciliation run, and the recorded run states the same drift it
    repaired (pre-repair count and affected pairs, post-repair verification, store errors verbatim)
    (**single source of truth**: the run record is registered in the Data Contract with the new desk
    module as its only owner and its one GET as its only serving endpoint; the index is rebuilt ONLY
    through the existing `BarIndex.reindex()`; coverage and freshness still come solely from
    `desk_coverage` over `bar_index`; and `bar_index.py`, `bars.py`, `tradability.py` and `levels.py`
    take a ZERO diff — this SSOT criterion stands in place of a PnL-ledger append, which this era's
    Non-Goals forbid); every `.data/bars/*.json` series file in the scoped root is proven
    byte-identical before and after the run (SHA-256 listing) and every previously recorded universe,
    screen and top-up record is proven byte-identical on disk (checksums unchanged, nothing
    backfilled) — a reconciliation changes only the derived index, so the NEXT screen run is a NEW
    append-only snapshot under a NEW `bar_store_signature` (`desk_screen.py`'s checksum over
    `desk_coverage`'s reads), never a rewrite of an existing one; in a real browser after the T-9
    clean rebuild, `/desk` shows the honest no-run-recorded state in one screenshot and, after a
    fixture-scoped run, the reconciliation section with its drift counts plus a ranked row whose
    coverage badge was dark before and is lit on a NEW screen run after — both legible (T-10: no
    screenshot ⇒ `unknown`, never `passing`); a **`[NEW]`-flagged demo-narrator walkthrough** covers
    the reconciliation end to end; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
    tools, zero diff to `StructureChart.tsx`, and `tests/test_copy_discipline.py` green unmodified.
    *(Keyless core; browser-verifiable. Reconciling the AMBIENT index is an operator-run act, reported
    honestly as run-or-not-run — never a CI gate. Why: measured 2026-07-28 directly from the frozen
    store and the derived index — `apps/backend/.data/bars` holds 369 series files while
    `.data/bar_index.db` holds 281 rows, so 88 recorded series carry no index row (and zero index rows
    point at a series that is not on disk); intersected with the pinned universe
    `universe-2026-07-25-49b33fa31680` and `desk_coverage.DESK_TOPUP_TIMEFRAMES` (`1h`,`4h`,`1d`,`1w`),
    exactly 7 member × timeframe pairs are affected: META `1h`+`1d`, MSFT `4h`, NFLX `1h`+`1d`, NVDA
    `1h`+`1d`. On `screen-2026-07-27-936543601e75` (63 ranked / 38 skipped) that renders as NFLX ranked
    #5, META #48 and NVDA #57 with all four badges dark — covered by the page's own divergence note,
    which fires only when EVERY badge in a row is dark (`app/desk/page.tsx:193/308`) — and MSFT #53 with
    `4h` dark beside `1h`/`1d` lit and NO note at all: the store holds MSFT `4h` (that dark badge is
    false) and holds no MSFT `1w` (that one is true), and nothing on the page distinguishes them.
    `BarIndex.reindex()` is referenced only by `tests/test_bar_index.py` — zero call sites in `app/`
    or `scripts/` — so no operator can reach the repair; and because `bar_store_signature` is a
    checksum over `desk_coverage`'s index-backed reads, a series the index cannot see also cannot move
    the pin the append-only screen ledger keys on.)*

- **J-11: Every ranked briefing row states how much completed history its wall was measured over**
  - Steps:
    1. Record two desk-owned fields on every NEW ranked screen row: `history_sessions` — the count of
       completed daily bars at or before that row's own `basis_as_of` — and `history_start`, the
       earliest of those bars' own timestamps, formatted through the SAME `_iso` helper the row's
       `basis_as_of` already uses. Both are derived INSIDE the single ascending walk over
       `BarStore.merged_bars(symbol, "1d")` that `_resolve_reference_close` (`desk_screen.py:239`)
       already performs — the exact accessor `tradability._select_daily_series`
       (`tradability.py:163/180`) reads — so the desk issues no second store read and invents no
       series of its own: zero diff to `bars.py`/`tradability.py`/`levels.py`/`bar_index.py` (no new
       field on any frozen return shape), zero new `Config` field, no new index, no new cache.
    2. Keep no-lookahead absolute: only bars at or before the row's OWN `basis_as_of` are counted (the
       as-of clamp stays `compute_tradability`'s exclusive decision — `tradability.py:157`'s bounded
       view — and the count never sees a bar the wall could not have seen). Both values are per-ROW,
       never per-snapshot, and skip rows carry neither (the J-08 shape).
    3. Register both fields in the blueprint's Data Contract "Screen snapshots, rank rows, skip rows"
       row BEFORE the code lands — one owner (`desk_screen.py`), one serving endpoint
       (`GET /research/desk/screen`). The snapshot key (screen date, as_of, universe snapshot id,
       `config_fingerprint`, bar-store signature) is unchanged, and the rank key — band class A>B>C,
       then distance asc, then band score desc, then symbol asc — is UNCHANGED: this journey
       DISCLOSES, it never ranks, filters, gates, weights, or scores. No threshold, no
       quality/confidence number, no "enough history" judgement anywhere (this era's Non-Goals forbid
       new statistics and gates outright), and the copy never advises, predicts, or implies action.
    4. Keep the append-only rail: never backfill, rewrite, or recompute an already-recorded snapshot;
       `GET /research/desk/screen` serves legacy rows exactly as recorded, and `/desk` renders their
       absent history as an honest `"history not recorded in this snapshot"` — the established J-08
       pattern (`apps/frontend/app/desk/page.tsx:236/318`) — never a value computed at read time.
    5. Surface it on `/desk`: a descriptive `history` column beside the existing `basis` column on the
       ranked table (e.g. `history 500 sessions · from 2024-07-25`), with full precision in the row
       anchor's existing consolidated honesty tooltip (the iter-7 pattern); copy = descriptive
       measurement only, and `tests/test_copy_discipline.py` stays green unmodified.
    6. Test fixture-scoped: a golden screen asserting the exact `history_sessions` + `history_start`
       per ranked row — including one short-history member and one long-history member — and
       byte-identical row content on a re-run under identical pins; a guard test that the row builder
       performs NO additional `BarStore` read beyond the one `merged_bars(symbol, "1d")` walk it
       already makes (assert the call count) and that the frontend derives neither value; the MCP
       `desk_screen` tool stays a byte-identical GET proxy (J-06's exactly-17-tool contract unchanged).
  - Acceptance: on the fixture-scoped rig a NEW screen run records `history_sessions` and
    `history_start` on every ranked row; `history_sessions` equals the number of daily bars
    `GET /research/candles?symbol=<sym>&timeframe=1d` (the same merged, price-less-row-excluded read)
    reports at or before that row's own `basis_as_of`, and `history_start` is that read's earliest such
    bar timestamp (**single source of truth**: the desk counts the canonical owner's own merged daily
    series inside the walk it already makes, and both new values are registered in the Data Contract
    with `desk_screen.py` as their only owner and `GET /research/desk/screen` as their only serving
    endpoint — this SSOT criterion stands in place of a PnL-ledger append, which this era's Non-Goals
    forbid); the recorded rank order is byte-identical to what the same pins produced before this
    change (disclosure only — a golden comparison proves the rank key did not move); a re-run under
    identical pins reproduces byte-identical rows and a same-pins re-run still returns the honest
    already-recorded response; every previously recorded screen snapshot is proven byte-identical on
    disk (checksums unchanged, nothing backfilled) and `/desk` renders their rows with the honest
    `"history not recorded in this snapshot"` state; in a real browser after the T-9 clean rebuild,
    `/desk` shows the `history` column with at least one ranked row of ≤ 60 sessions and one of ≥ 400
    sessions legible in the SAME screenshot (T-10: no screenshot ⇒ `unknown`, never `passing`); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's history disclosure end to end;
    and the full backend suite is green with `Config().config_fingerprint()` still `08e471b10130e1e2`,
    zero new `Config` fields, the `default` profile and `v1` byte-identical (engine equivalence green),
    the MCP surface still exactly 17 tools, zero diff to
    `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why:
    measured 2026-07-29 from the recorded snapshot `screen-2026-07-29-ce0d82b8e9bf` (63 ranked / 38
    skipped) plus the frozen bar files on disk — the count of finite-priced merged daily bars at or
    before each row's own `basis_as_of` spans 27 to 501, median 500: HONA ranks **#8** (support, class
    A, `distance_bps` 0.0, `band_score` 51) on **27** sessions, its series meta recording
    `covered_start_utc 2026-06-15` / `covered_end_utc 2026-07-24` (a ~6-week listing), directly beside
    BRK-B #1, DHR #2, HD #3 and IBM #4 on **500** each, with NFLX #5 / META #48 / NVDA #57 on 382,
    MSFT #53 on 388, TSLA #29 on 390 and AAPL #19 on 501. All four of HONA's coverage badges are lit
    (`has_bars: true` ×4, `latest_window_end_utc 2026-07-25T00:00:00Z` — the requested-window end,
    honestly labelled "window last requested"), so the badges structurally cannot express the
    difference, and `DeskScreenRow` (`lib/types.ts:801`) carries nothing about extent — a 27-session
    wall and a 500-session wall sit on one rank scale, indistinguishable on the page.)*

- **J-12: Every recorded screen the ledger lists can be read back — snapshots are addressable by id**
  - Steps:
    1. Serve any recorded snapshot by its OWN id: add an `?id=<snapshot id>` branch to the
       ALREADY-registered `GET /research/desk/screen` (`desk_routes.py:314`), returning that exact
       persisted snapshot verbatim (`{"screen": <snapshot>|null}` — the `?date=` shape), a plain read
       that recomputes nothing and writes nothing. `?date=` keeps its documented meaning
       byte-identically ("the latest recording on that date", `desk_routes.py:326`); an unknown id is
       an honest `{"screen": null}` at HTTP 200 (the `?date=` convention); `id` and `date` together is
       an honest refusal, never a silent precedence rule. **Zero new value, zero new owner**:
       `desk_screen.ScreenStore` stays the only owner and `GET /research/desk/screen` the only serving
       endpoint — no new module, no new route, no new `Config` field, no new MCP tool (J-06's
       exactly-17-tool contract stays green and `get_endpoint`'s `/research/` allowlist already reaches
       the new query).
    2. Register the additive `?id=` read param on the blueprint's Data Contract "Screen snapshots, rank
       rows, skip rows" row BEFORE the code lands. The 5-pin snapshot key, every recorded row's content
       and the rank key (band class A>B>C, then distance asc, then band score desc, then symbol asc) are
       all UNCHANGED: this journey adds a READ path, never a value, never a ranking input.
    3. Address history by id on `/desk`: history rows select `meta.id` and fetch `?id=` (they select
       `meta.screen_date` today, `page.tsx:493`), the displayed snapshot is highlighted by id (today
       `meta.screen_date === selectedDate` lights BOTH rows of a same-date pair, `page.tsx:537`), and
       each entry shows its recorded-at `created_utc` beside its screen date so two recordings of one
       screen date are distinguishable on the page.
    4. Say which snapshot is on screen: the Provenance panel (`DeskProvenance`, `page.tsx:890`) gains the
       displayed snapshot's own `id` and `created_utc` — both already carried by `DeskScreenSnapshot`
       (`lib/types.ts:838`), a straight re-format of the served payload, nothing derived — and the
       default view describes itself as the most recently RECORDED screen, which is what `latest` is
       (`records[-1]` under `ScreenStore.list`'s `created_utc` sort, `desk_screen.py:478`), never "the
       latest screen date". Copy = descriptive measurement only (no advice, imperative, urgency or
       prediction language).
    5. Disclose what cannot be read at all: `GET /research/desk/topup/runs` (`desk_routes.py:277`) and
       `GET /research/desk/coverage/reconcile/runs` (`desk_routes.py:505`) serve their own store's
       `errors` as `integrity_errors` exactly as `GET /research/desk/screen` (`:330`) and
       `GET /research/desk/universe` (`:171`) already do — same channel, same key, same shape, no second
       path — and `/desk` renders each ledger's integrity errors as an honest count-plus-filename line
       (the page renders none today, for any ledger). No record is ever repaired, rewritten or hidden: a
       file that fails verification stays out of `runs`/`latest` and is NAMED instead.
    6. Test fixture-scoped: two snapshots sharing one `screen_date` under different
       `bar_store_signature`s (the pre/post-reconciliation pair J-10's own repair produces) → `?id=`
       returns EACH byte-identical to its own recorded file while `?date=` still returns the later
       recording; unknown id honest-null; the GET triggers no compute and writes nothing; a corrupt
       record file planted in a SCOPED store dir (never in `apps/backend/.data`) appears in each run
       ledger's `integrity_errors` and stays out of `runs`/`latest`; the MCP `desk_screen` tool stays a
       byte-identical no-arg GET proxy and `get_endpoint` proxies `?id=` verbatim.
  - Acceptance: with two snapshots recorded for ONE screen date under different bar-store signatures,
    `GET /research/desk/screen?id=<the earlier id>` serves that snapshot byte-identically to its own
    recorded file on disk, and `?date=` still serves the later recording unchanged (a golden comparison
    proves the shipped branch unmoved) (**single source of truth**: an additive READ param on the
    already-registered endpoint — `desk_screen.ScreenStore` remains the only owner and
    `GET /research/desk/screen` the only serving endpoint, registered in the Data Contract before the
    code lands, with zero new value computed, zero recompute on the GET, zero new module/route/`Config`
    field, and zero change to what any desk store RECORDS or to any recorded shape — this SSOT criterion
    stands in place of a PnL-ledger append, which this era's Non-Goals forbid); an unknown id returns an
    honest `{"screen": null}` at HTTP 200; every recorded universe, screen, top-up and reconciliation
    file is proven byte-identical on disk before and after the iteration (SHA-256 listing — nothing
    backfilled, repaired or rewritten); both run-ledger GETs carry `integrity_errors`, and a corrupt
    record planted in a scoped store dir is named there while staying out of `runs`/`latest`; in a real
    browser after the T-9 clean rebuild, `/desk`'s screen-history table shows the two same-date entries
    with distinct recorded-at values and selecting each renders ITS OWN rows, with at least one row whose
    coverage badge differs between the two views legible across the screenshots (on the ambient rig this
    is the already-recorded 2026-07-27 pair: NFLX's `1d` badge dark in `screen-2026-07-27-936543601e75`
    and lit in `screen-2026-07-27-3ad3c57aa6ba`), plus one screenshot of the honest integrity-error line
    for the planted corrupt run record (T-10: no screenshot ⇒ `unknown`, never `passing`); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers reaching a same-date recorded snapshot end to
    end; and the full backend suite is green with `Config().config_fingerprint()` still
    `08e471b10130e1e2`, zero new `Config` fields, the `default` profile and `v1` byte-identical (engine
    equivalence green), the MCP surface still exactly 17 tools, zero diff to
    `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
    2026-07-29 from the running backend and the frozen store — `apps/backend/.data/screen` holds 6
    recorded snapshots, two of them for screen date 2026-07-27: `screen-2026-07-27-936543601e75`
    (bar-store signature `7eab5f03cf23e8c7`, recorded 2026-07-27T21:42:14Z) and
    `screen-2026-07-27-3ad3c57aa6ba` (`350c85d18b1ff234`, recorded 2026-07-28T21:30:16Z). Their content
    differs on exactly 4 ranked rows — META, MSFT, NFLX, NVDA `coverage` — i.e. the pre- and post-repair
    state of J-10's own index reconciliation. `GET /research/desk/screen?date=2026-07-27` returns only
    `3ad3c57aa6ba` (`matching[-1]`, `desk_routes.py:326`); the `screens` list advertises the other with
    its id, checksum-pinned provenance and counts, but NO API path serves it, MCP `get_endpoint` has the
    same date-only reach, and on `/desk` both history rows fetch the same date and both highlight — so
    the pre-repair record that J-10's own acceptance rests on is listed and unreadable. Separately,
    `latest` is `records[-1]` under a `created_utc` sort, so the page opens on
    `screen-2026-07-28-ac07c9581a4f` although `screen-2026-07-29-ce0d82b8e9bf` carries the later screen
    date, and nothing on the page names the snapshot being displayed. And both run ledgers drop their
    store's own verification errors (`records, _errors = store.list()`, `desk_routes.py:277` and `:505`)
    while their two sibling desk GETs serve them — today `integrity_errors` is empty everywhere, so this
    closes the channel before it is ever needed, never after.)*

- **J-13: Every ranked briefing row states the price its wall sits at and the close it was measured from**
  - Steps:
    1. Record ONE desk-owned field on every NEW ranked screen row: `reference_close` — the daily close
       `_resolve_reference_close_and_history` (`desk_screen.py:250`) ALREADY returns and `compute_screen`
       already binds as `close` (`desk_screen.py:370`) before handing it to `_select_best_band` (`:373`)
       and `_distance_bps` (`:379`). It is copied verbatim out of that same single walk's own return —
       no second store read, no new accessor, no new arithmetic, no re-derivation of WHICH bar the basis
       is (that stays `compute_tradability`'s exclusive decision): zero diff to
       `bars.py`/`tradability.py`/`levels.py`/`bar_index.py` (no new field on any frozen return shape),
       zero new `Config` field, no new index, no new cache. Skip rows carry nothing (the J-08/J-11 shape).
    2. Register `reference_close` in the blueprint's Data Contract "Screen snapshots, rank rows, skip
       rows" row BEFORE the code lands — one owner (`desk_screen.py`), one serving endpoint
       (`GET /research/desk/screen`). The snapshot key (screen date, as_of, universe snapshot id,
       `config_fingerprint`, bar-store signature) is unchanged, and the rank key — band class A>B>C, then
       distance asc, then band score desc, then symbol asc — is UNCHANGED: this journey DISCLOSES, it
       never ranks, filters, gates, weights, or scores. No threshold, no proximity/quality number, no
       "price is inside the band" flag computed anywhere (this era's Non-Goals forbid new statistics and
       gates outright), and the copy never advises, predicts, or implies action.
    3. Keep the append-only rail: never backfill, rewrite, or recompute an already-recorded snapshot;
       `GET /research/desk/screen` serves legacy rows exactly as recorded, and `/desk` renders their
       absent close as an honest `"close not recorded in this snapshot"` — the established J-08/J-11
       pattern (`apps/frontend/app/desk/page.tsx:236/318`) — never a value computed at read time, and in
       particular NEVER re-derived from `distance_bps` and a band edge, which is precisely the
       client-side recomputation the single-source-of-truth rail forbids.
    4. Surface both prices on `/desk`: a descriptive `band` column rendering the row's OWN
       already-recorded `price_low`–`price_high` (recorded on every ranked row of every snapshot ever
       written and already typed at `lib/types.ts:801` — nothing new to record, only rendered) with the
       row's `reference_close` beside it (e.g. `band 488.50–490.85 · close 490.85`), following the same
       rounded-display split the distance/score/basis/history cells already use, with full precision in
       the row anchor's existing consolidated honesty tooltip (the iter-7 pattern — never a per-cell
       `title` under the stretched drill-in anchor). Copy = descriptive measurement only, and
       `tests/test_copy_discipline.py` stays green unmodified.
    5. Test fixture-scoped: a golden screen asserting the exact `reference_close` per ranked row —
       including one row whose close lies INSIDE its own recorded band (`distance_bps` 0.0) and one whose
       close lies outside it — and byte-identical row content on a re-run under identical pins; a guard
       test that the row builder issues NO additional `BarStore` read beyond the one
       `merged_bars(symbol, "1d")` walk it already makes (assert the call count, the J-11 precedent) and
       that the frontend derives no price of its own (no arithmetic on `distance_bps`/`price_low`/
       `price_high` anywhere in the page); the MCP `desk_screen` tool stays a byte-identical GET proxy
       (J-06's exactly-17-tool contract unchanged).
  - Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded under
    the same five pins, so the store's identical-pin refusal is respected rather than worked around —
    records `reference_close` on every ranked row, and each row's value is byte-identical to the close of
    the `1d` bar dated at that row's own `basis_as_of` in
    `GET /research/candles?symbol=<sym>&timeframe=1d` (the same merged, price-less-row-excluded read)
    (**single source of truth**: the desk copies the canonical owner's own close out of the walk it
    already makes, and the new value is registered in the Data Contract with `desk_screen.py` as its only
    owner and `GET /research/desk/screen` as its only serving endpoint — this SSOT criterion stands in
    place of a PnL-ledger append, which this era's Non-Goals forbid); the recorded rank order is
    byte-identical to what the same pins produced before this change (disclosure only — a golden
    comparison proves the rank key did not move); a re-run under identical pins reproduces byte-identical
    rows and a same-pins re-run still returns the honest already-recorded response; every previously
    recorded screen snapshot is proven byte-identical on disk (checksums unchanged, nothing backfilled)
    and `/desk` renders their rows with their OWN recorded band range plus the honest
    `"close not recorded in this snapshot"` state; in a real browser after the T-9 clean rebuild, `/desk`
    shows the `band` column with at least one ranked row whose close lies inside its recorded band range
    and one whose close lies outside it, both legible in the SAME screenshot (T-10: no screenshot ⇒
    `unknown`, never `passing`); a **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's
    price disclosure end to end; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
    zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
    2026-07-29 from the running product's own artifacts — the string `price` does not occur ONCE in the
    1,779-line `apps/frontend/app/desk/page.tsx`. The ranked table's nine columns are symbol, side,
    class, distance, score, coverage, tick evidence, basis, history, and the row's composite tooltip
    carries distance/score/basis/history/coverage only, so `price_low`/`price_high` — recorded on every
    ranked row of all six snapshots on disk and typed at `lib/types.ts:801` — are rendered NOWHERE, and
    the reference close is not even recorded: `compute_screen` binds it at `desk_screen.py:370`, feeds it
    to the band selection and the distance, and drops it. In `screen-2026-07-29-ce0d82b8e9bf` (63 ranked
    / 38 skipped) those closes span 21.92 to 1,185.87 and the recorded band widths span 18.1 to 100.0
    bps, none of it on the page. The nine top-ranked rows every one read `0.00 bps`: for each, the close
    sits exactly on the band's upper edge, INSIDE the recorded band (BRK-B support, band 488.50–490.85,
    close 490.85; NFLX 73.45–73.83, close 73.83; HONA 195.16–195.87, close 195.87), while #10 LIN reads
    `0.20 bps` with close 506.32 just BELOW a 506.33–509.61 resistance band and #19 AAPL reads `1.50 bps`
    with close 333.02 below a 333.07–334.99 band — "price is in the wall" and "price is short of the
    wall" print as the same small bps number today. The close is recoverable from a recorded row ONLY by
    inverting `distance_bps` against a band edge under the row's own `side` (verified exact to 1.1e-13 on
    all 63 rows), i.e. only by the client-side recomputation the Data Contract forbids — which is why it
    must be recorded at its owner, never derived on the page.)*

- **J-14: Every ranked briefing row states where the nearest wall on the OTHER side of price sits**
  - Steps:
    1. Record ONE desk-owned nested field on every NEW ranked screen row: `opposite_band` — the nearest
       band on the side the row's own selected band is NOT on, taken from the SAME `result["bands"]` list
       `compute_screen` already holds (`desk_screen.py:369` — the identical list `_select_best_band`
       consumes at `:385`) and measured with the SAME `_distance_bps` helper (`desk_screen.py:231`)
       against the SAME `close` the row already records as `reference_close` (`:382`/`:401`). Its values
       are copied VERBATIM out of the canonical owner's own band dict — `{"side", "band_class",
       "price_low", "price_high", "band_score", "distance_bps"}`, where `band_class`/`band_score` are
       `compute_tradability`'s own `class`/`quality_score` passed straight through (never re-graded,
       never re-scored; a band whose class is `null` is reported as recorded, never filtered out of the
       candidate set) and the band's `members` list is never copied. The selection is deterministic and
       stated on the record: distance ascending, then class rank descending (`_CLASS_RANK`,
       `desk_screen.py:121` — an unclassified band ranks lowest, never highest), then `band_score`
       descending, resolved by `min`'s first-of-tie stability over `compute_tradability`'s own served
       order (the `_select_best_band` precedent). No second store read, no second `compute_tradability`
       call, no new arithmetic beyond the existing helper: zero diff to
       `tradability.py`/`levels.py`/`bars.py`/`bar_index.py` (no new field on any frozen return shape),
       zero new `Config` field, no new index, no new cache. When the canonical return holds no band on
       the other side the field is an honest `null`, never an invented band; skip rows carry nothing (the
       J-08/J-11/J-13 shape).
    2. Record, in that SAME single pass over that SAME list, one more desk-owned field: `bands_by_class`
       — how many bands `compute_tradability` returned for this symbol, counted under the four fixed keys
       `"A"`, `"B"`, `"C"`, `"unclassified"`, all four ALWAYS present (never sparse), so a row says how
       many walls its one displayed wall was chosen from. It is a plain count of the canonical owner's own
       output — never a grade, threshold, weight, or quality number.
    3. Register both fields in the blueprint's Data Contract "Screen snapshots, rank rows, skip rows" row
       BEFORE the code lands — one owner (`desk_screen.py`), one serving endpoint
       (`GET /research/desk/screen`). The snapshot key (screen date, as_of, universe snapshot id,
       `config_fingerprint`, bar-store signature) is unchanged, and the rank key — band class A>B>C, then
       distance asc, then band score desc, then symbol asc — is UNCHANGED: this journey DISCLOSES, it
       never ranks, filters, gates, weights, or scores. Neither new value enters `_row_rank_key`
       (`desk_screen.py:252`) or any selection, and no "corridor width", "room", proximity flag,
       threshold, or quality number is computed anywhere (this era's Non-Goals forbid new statistics and
       gates outright); the copy never advises, predicts, or implies action.
    4. Keep the append-only rail: never backfill, rewrite, or recompute an already-recorded snapshot;
       `GET /research/desk/screen` serves legacy rows exactly as recorded, and `/desk` renders their
       absent value as an honest `"opposite wall not recorded in this snapshot"` — the established
       J-08/J-11/J-13 pattern (`apps/frontend/app/desk/page.tsx:266/270/278`) — never a value computed at
       read time, and in particular NEVER derived on the page from the row's own band range, close, or
       `distance_bps`, which is precisely the client-side recomputation the single-source-of-truth rail
       forbids.
    5. Surface it on `/desk`: exactly ONE new descriptive column, `opposite`, beside the existing `band`
       column on the ranked table, rendering the recorded block in the same rounded-display split the
       distance/score/basis/history/band cells already use (e.g. `opposite resistance A 490.88–494.22 ·
       0.6 bps`), with an honest `"no band on the other side"` for a recorded `null` and the
       legacy-absence copy above for a legacy row; full precision plus one `bands_by_class` line (e.g.
       `10 bands · A 10 · B 0 · C 0 · unclassified 0`) in the row anchor's existing consolidated honesty
       tooltip (the iter-7 pattern — never a per-cell `title` under the stretched drill-in anchor). Copy =
       descriptive measurement only, and `tests/test_copy_discipline.py` stays green unmodified.
    6. Test fixture-scoped: a golden screen asserting the exact `opposite_band` + `bands_by_class` per
       ranked row — including one row whose nearest opposite wall is within 25 bps, one whose nearest
       opposite wall is beyond 1,000 bps, and one whose nearest opposite band carries a `null` class — and
       byte-identical row content on a re-run under identical pins; a unit test of the selector proving the
       honest `null` when the canonical return holds no band on the other side and proving the tie-break is
       stable; a guard test that the row builder issues NO additional `BarStore` read and NO second
       `compute_tradability` call beyond the ones it already makes (assert the call counts — the
       J-11/J-13 precedent) and that the frontend derives no distance or price of its own; a golden
       comparison proving the recorded rank order is byte-identical to what the same pins produced before
       this change; the MCP `desk_screen` tool stays a byte-identical GET proxy (J-06's exactly-17-tool
       contract unchanged).
  - Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded under
    the same five pins, so the store's identical-pin refusal is respected rather than worked around —
    records `opposite_band` and `bands_by_class` on every ranked row, and each row's `opposite_band`
    `side`/`band_class`/`price_low`/`price_high`/`band_score` are byte-identical to the corresponding band
    in `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s own `bands` list, its
    `distance_bps` reproduces that band's distance from the row's own recorded `reference_close` under the
    SAME formula the row's own `distance_bps` already uses, and `bands_by_class` sums to that same list's
    length (**single source of truth**: the desk selects from the canonical owner's own returned bands
    inside the call it already makes and copies their values verbatim — no second read, no re-grading, no
    re-scoring — and both new values are registered in the Data Contract with `desk_screen.py` as their
    only owner and `GET /research/desk/screen` as their only serving endpoint; this SSOT criterion stands
    in place of a PnL-ledger append, which this era's Non-Goals forbid); the recorded rank order is
    byte-identical to what the same pins produced before this change (disclosure only — a golden
    comparison proves the rank key did not move); a re-run under identical pins reproduces byte-identical
    rows and a same-pins re-run still returns the honest already-recorded response; every previously
    recorded screen snapshot is proven byte-identical on disk (checksums unchanged, nothing backfilled)
    and `/desk` renders their rows with the honest `"opposite wall not recorded in this snapshot"` state;
    in a real browser after the T-9 clean rebuild, `/desk` shows the `opposite` column with at least one
    ranked row whose nearest opposite wall is within 25 bps and one whose nearest opposite wall is more
    than 1,000 bps away, both legible in the SAME screenshot, plus one screenshot of a row tooltip
    carrying its `bands_by_class` line — captured on the owner-approved headed rig per T-10a
    (`project-extensions/qa-rig/`: `xrig.sh up`, then `capture-native-tooltip.py --hover-selector
    '[data-testid="desk-row-drill-in"]' --require-title 'bands by class'`, quoting the tool's
    reported `title` in the results row and attaching BOTH the full frame and the tooltip crop) —
    (T-10: no screenshot ⇒ `unknown`, never `passing`); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's opposite-wall disclosure end to
    end, narrated over POPULATED ranked rows (which also closes iter-17's RECORDED_WITH_NOTES capture
    gap, whose frames narrate the legacy state only); and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
    zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
    2026-07-29 against the canonical owner itself — `GET /research/tradability?as_of=2026-07-29T23:59:59Z`
    for all 63 ranked members of `screen-2026-07-29-ce0d82b8e9bf` (63 ranked / 38 skipped): all 63 carry
    bands on BOTH sides of price (typically 5 + 5 of the ≤10-band map; 52 of 63 hold the full 10), yet
    each recorded row keeps exactly one. The distance from a row's own reference close to the nearest band
    on the other side spans 0.0 to 12,178.8 bps — median 1,355, within 25 bps on 5 rows, beyond 500 bps on
    48 — and the spread is invisible exactly where the briefing is densest: the nine top-ranked rows every
    one read `support · class A · 0.00 bps`, while their nearest opposite wall sits at 0.6 bps for BRK-B
    #1 (a class-A resistance band 490.88–494.22, score 3001, three cents above its close of 490.85),
    72.7 bps for DHR #2, 1,457.5 bps for IBM #4 and 6,067.7 bps for CRM #6 — a 10,000× spread printed as
    nine identical-looking rows. Two rows invert it: ISRG #63 ranks on a wall 4,311 bps away while an
    unclassified support band sits 0.0 bps from its close, and CMCSA #62 the same with a class-B band —
    the class-first selection (`_select_best_band`, `desk_screen.py:240`) is doing exactly what it is
    specified to do, and nothing on the page says a nearer band on the other side exists. `DeskScreenRow`
    (`lib/types.ts:815`) carries no field for it, and the ranked table's ten columns — symbol, side,
    class, distance, score, coverage, tick evidence, basis, history, band — have no cell for it. The same
    reads also close the backlog's `desk-row-band-class-uniformity` observation: all 63 rows read class A,
    and 42 of them hold ten class-A bands, so `bands_by_class` is what makes the class column's constancy
    legible instead of mysterious.)*

- **J-15: Every ranked briefing row states what its wall is actually made of**
  - Steps:
    1. Record three desk-owned fields on every NEW ranked screen row, all taken from the SAME band dict
       `_select_best_band` (`desk_screen.py:262`) already returns — the band `compute_tradability` itself
       built (`tradability._band`, `tradability.py:343`): `band_member_count` and `band_round_number`,
       copied **VERBATIM** out of that band's own `member_count` / `round_number` keys (never
       recomputed, never re-derived, never compared against a threshold), and `band_member_timeframes`,
       a plain count of that SAME band's own `members` list under those members' own `timeframe` values
       (the `bands_by_class` precedent, `_bands_by_class`, `desk_screen.py:298`) — keys are exactly the
       timeframes present among those members in a deterministic order, values are integer counts whose
       sum EQUALS `band_member_count`, and a timeframe with no member in this band is simply absent,
       never a fabricated zero for a timeframe the symbol's own level computation never read. The band's
       `members` list itself is NEVER copied into the record (the J-14 rule), no member price /
       `touch_count` / `strength` is copied, and no second store read and no second `compute_tradability`
       call is made: zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py` (no new field on
       any frozen return shape), zero new `Config` field, no new index, no new cache. Skip rows carry
       none of the three (the J-08/J-11/J-13/J-14 shape).
    2. Register all three in the blueprint's Data Contract "Screen snapshots, rank rows, skip rows" row
       BEFORE the code lands — one owner (`desk_screen.py`), one serving endpoint
       (`GET /research/desk/screen`). The snapshot key (screen date, as_of, universe snapshot id,
       `config_fingerprint`, bar-store signature) is unchanged, and the rank key — band class A>B>C,
       then distance asc, then band score desc, then symbol asc — is UNCHANGED: this journey DISCLOSES,
       it never ranks, filters, gates, weights, or scores. Neither count nor the flag enters
       `_row_rank_key` (`desk_screen.py:309`) or any band selection, and no "confluence quality",
       "evidence depth", intraday-share ratio, threshold, or judgement about which composition is
       BETTER is computed anywhere (this era's Non-Goals forbid new statistics and gates outright); the
       copy never advises, predicts, or implies action.
    3. Keep the append-only rail: never backfill, rewrite, or recompute an already-recorded snapshot;
       `GET /research/desk/screen` serves legacy rows exactly as recorded, and `/desk` renders their
       absent composition as an honest `"composition not recorded in this snapshot"` — the established
       J-08/J-11/J-13/J-14 pattern (`apps/frontend/app/desk/page.tsx:383/392/407/420`) — never a value
       computed at read time, and in particular never inferred on the page from `band_score`, the band
       range, or `bands_by_class`, which is precisely the client-side recomputation the
       single-source-of-truth rail forbids.
    4. Surface it on `/desk`: exactly ONE new descriptive column, `levels`, beside the existing
       `band`/`opposite` columns, rendering the row's OWN recorded counts and flag (e.g.
       `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11`) together with the same `round number` badge
       `/structure`'s own band table already renders for the identical canonical field
       (`apps/frontend/app/structure/page.tsx:612/619`), so the two pages describe one band in one
       vocabulary. Every new value is an exact integer or boolean, so there is NO rounded display and
       therefore NO new row-tooltip line is required or added by this journey (the iter-7 full-precision
       tooltip pattern covers rounded numerics only; J-14's `bands_by_class` tooltip line stays exactly
       as shipped, and no per-cell `title` is ever added under the stretched drill-in anchor). Copy =
       descriptive measurement only, and `tests/test_copy_discipline.py` stays green unmodified.
    5. Test fixture-scoped: a golden screen asserting the exact `band_member_count`,
       `band_round_number` and `band_member_timeframes` per ranked row — including one row whose band
       holds a SINGLE member (a zero-width `price_low == price_high` band) and one whose band is
       dominated by intraday (`1m`/`5m`) members — plus the
       `sum(band_member_timeframes.values()) == band_member_count` invariant asserted on every ranked
       row, and byte-identical row content on a re-run under identical pins; a guard test that the row
       builder issues NO additional `BarStore` read and NO second `compute_tradability` call beyond the
       ones it already makes (assert the call counts — the J-11/J-13/J-14 precedent) and that the
       frontend derives no count of its own; a golden comparison proving the recorded rank order is
       byte-identical to what the same pins produced before this change; the MCP `desk_screen` tool
       stays a byte-identical GET proxy (J-06's exactly-17-tool contract unchanged).
  - Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded
    under the same five pins, so the store's identical-pin refusal is respected rather than worked
    around — records `band_member_count`, `band_round_number` and `band_member_timeframes` on every
    ranked row, and each row's `band_member_count`/`band_round_number` are byte-identical to the
    `member_count`/`round_number` of the corresponding band in
    `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s own `bands` list, while
    `band_member_timeframes` is a plain tally of that SAME band's own `members` list by `timeframe` and
    sums to that band's own `member_count` (**single source of truth**: the desk copies the canonical
    owner's own band fields verbatim and counts that same band's own members inside the call it already
    makes — no second read, no second compute, no re-grading, no re-scoring — and all three values are
    registered in the Data Contract with `desk_screen.py` as their only owner and
    `GET /research/desk/screen` as their only serving endpoint; this SSOT criterion stands in place of a
    PnL-ledger append, which this era's Non-Goals forbid); the recorded rank order is byte-identical to
    what the same pins produced before this change (disclosure only — a golden comparison proves the
    rank key did not move); a re-run under identical pins reproduces byte-identical rows and a
    same-pins re-run still returns the honest already-recorded response; every previously recorded
    screen snapshot is proven byte-identical on disk (checksums unchanged, nothing backfilled) and
    `/desk` renders their rows with the honest `"composition not recorded in this snapshot"` state; in a
    real browser after the T-9 clean rebuild, `/desk` shows the `levels` column with at least one ranked
    row whose band holds ≤ 5 levels and one whose band holds ≥ 100 levels legible in the SAME
    screenshot, plus one row carrying the `round number` badge legible in that same frame or in one
    further screenshot of the SAME rendered screen (T-10: no screenshot ⇒ `unknown`, never `passing`; no
    native `title` tooltip is required by this journey, so the T-10a headed rig is not needed for it); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's wall-composition disclosure end
    to end, narrated over POPULATED ranked rows; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
    zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
    2026-07-30 against the canonical owner's own recorded output — all 100 ranked rows of
    `screen-2026-07-29-2a57de4e7415` (100 ranked / 1 skipped) matched to their own
    `compute_tradability` returns cached in `.data/tradability_cache.db` on
    (`side`,`price_low`,`price_high`,`quality_score`), 100/100 matched. The selected bands'
    `member_count` spans **1 to 4,014** (quartiles 19 / 45.5 / 87) and `round_number` is **true on 16 of
    the 100 rows** — and NEITHER value is recorded on any screen row or rendered anywhere on `/desk`,
    while `/structure`'s own band table renders BOTH for the identical bands (a `member count` column
    plus a `round number` badge, `app/structure/page.tsx:612/619`), so the briefing says less about a
    wall than the page it drills into. The 15 top-ranked rows every one read `support · Class A ·
    0.00 bps`, yet their walls are built of 2 to 609 levels: #4 MSFT's band holds **609** members of
    which **572 are `1m`/`5m`** and only 28 are `1d`; #1 BRK-B's holds 155 (68 of them `1d`); #15 ORCL's
    holds **2** (one `1h` + one `1d`); and #45 SPG's holds a **single** member, which is why its
    recorded band is zero-width (`price_low == price_high == 231.72999572753906`) and prints today as
    `band 231.73–231.73` with nothing saying why. Across the 100 rows composition spans 1 to 6 distinct
    timeframes (75 rows are 4-timeframe confluences, 1 row a single timeframe) and 8 rows carry
    intraday members, up to AAPL's 4,014-member band (3,895 of them `1m`/`5m`). `DeskScreenRow`
    (`lib/types.ts:826`) carries no field for any of it, and the ranked table's eleven columns — symbol,
    side, class, distance, score, coverage, tick evidence, basis, history, band, opposite — have no cell
    for it.)*

- **J-16: The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll**
  - Steps:
    1. Reflow the ranked table so the ROW's own content fits the width the page actually gives it. The
       scroll container is capped by `/desk`'s own `mx-auto max-w-7xl` (`apps/frontend/app/desk/page.tsx:1829`
       — 1280 px), and the table's intrinsic content width is 1795 px, so simply widening the container
       cannot fix it: at a 1440 px viewport even an uncapped container offers ~1408 px < 1795 px. Sanctioned
       mechanisms, builder's choice, any combination: drop the in-cell label prefixes the column headers
       (`:486`–`:497`) already state (`basis `/`history `/`band `/`opposite `/`N levels` ≈ 35 characters per
       row), render the four coverage badges on ONE line instead of today's wrap-into-four
       (`DeskCoverageBadges`' `flex flex-wrap`, `:218`), relax `LABEL_CELL`'s `whitespace-nowrap` (`:141`)
       on the long disclosure cells, and/or lay the five disclosure fields out as a second line of the SAME
       row. What is NOT sanctioned: dropping, hiding, collapsing behind a click, or moving into a native
       `title` tooltip ANY of the twelve disclosures — each one is a shipped journey's own acceptance
       clause (J-08 `basis`, J-11 `history`, J-13 `band`, J-14 `opposite`, J-15 `levels`) — and NOT shrinking
       the table's base type below the page's existing `text-xs` scale to buy width.
    2. Add the `rank` cell Key Capability 4 and J-04 step 2 both name first: the row's own 1-based position
       in the DISPLAYED snapshot's own served `rows` array, rendered as a plain integer position (never a
       label implying action, quality, or urgency). The rank ORDER is already recorded data (J-03 step 2:
       "the order is data, recorded in the snapshot"), so this RENDERS recorded data and computes no new
       value: zero new recorded field, zero backend diff — `desk_screen.py`'s row shape, the five-pin
       snapshot key and `_row_rank_key` are untouched — and the page never sorts, re-orders or filters
       `rows`, it renders the served order verbatim (in 10-row windows — see the amendment below).
    3. Render the class and distance cells as the chips Key Capability 4 ("band class chip, distance chip")
       and Success Criterion 4 ("descriptive chips") name — and which this page's own source comment
       (`:326`) already calls chips while the DOM carries none — reusing the page's OWN existing badge style
       (the bordered `text-[11px]` style `desk-coverage-badge` / `tick evidence` / `round number` already
       use), with the SAME text those cells render today so every stored golden's text expect stays true.
    4. Keep every browser contract the shipped journeys rest on: each existing `data-testid` on `/desk`
       keeps its element and its exact text (`desk-screen-rows-table`, `desk-row-drill-in`, `desk-row-side`,
       `desk-row-band-class`, `desk-row-distance`, `desk-row-score`, `desk-coverage-badges`/`-badge`,
       `desk-row-tick-evidence`, `desk-row-basis`, `desk-row-history`, `desk-row-band`, `desk-row-opposite`,
       `desk-row-levels`, `desk-skip-row*`, `desk-history-row`, `desk-provenance`, `desk-title`, the compute
       controls), and the row's stretched drill-in anchor keeps its `href`, its `absolute inset-0`, its
       `data-testid` and its dynamic consolidated `title` byte-unchanged — so
       `tests/test_desk_hover_tooltip_guard.py` and `tests/test_desk_ui_guards.py` stay green UNMODIFIED,
       J-14's already-photographed `bands_by_class` tooltip keeps working, and the 13 stored golden replay
       scripts (`runs/goal-session-desk/journey-scripts/J-01`…`J-14`; there is no `J-06` script) replay
       green without a single script edit. If the reflow moves a disclosure out of its own `<td>`, its
       testid moves WITH it and keeps the same text.
    5. Zero backend diff, zero new value: no new field on any recorded shape, no new Data-Contract row
       (nothing new is computed — the page renders `GET /research/desk/screen`'s served payload verbatim, as
       it already does), no new endpoint/route/`Config` field, no new MCP tool. The page still derives no
       price and no distance of its own (`test_desk_ui_guards.py`'s price-arithmetic guard stays green
       unmodified), and legacy rows keep every honest-absence string exactly as shipped ("basis / history /
       close / opposite wall / composition not recorded in this snapshot").
    6. Test: extend the source-introspection guard suite (the `test_desk_ui_guards.py` pattern, with its own
       seeded can-fail counter-test) with (a) the page renders `rows` in served order — no `.sort(`,
       `.reverse(` or comparator over `rows` anywhere in `page.tsx`, and its one page-window slice pinned
       verbatim beside an absolute-rank guard — and (b) every testid named
       in step 4 is still present in the source. Copy stays descriptive measurement only and
       `tests/test_copy_discipline.py` stays green unmodified.
  - Acceptance: in a real browser after the T-9 clean rebuild, at a 1440×900 viewport with NO horizontal
    scrolling and no click, ONE screenshot of `/desk`'s populated briefing shows the top-ranked row's
    `rank`, symbol, side, class, distance, score, coverage badges, tick-evidence, `basis`, `history`,
    `band`, `opposite` AND `levels` values all legible at once, and the ranked table's own measured
    `scrollWidth` is ≤ its scroll container's `clientWidth` with both numbers quoted in the UI-test results
    row (this is iter-23's UT-07 turned PASS, measured exactly the way it was measured FAIL: 1795 px inside
    1214 px); each ranked row's four coverage badges render on ONE line and a ranked row's own measured
    height is ≤ 60 px (today ~115 px — the BRK-B / AMZN / MDLZ row baselines sit 115 px apart in
    `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png`); a further screenshot of that same rendered
    screen shows at least the first EIGHT ranked rows legible with their rank positions 1…8 in the served
    order (a full-page capture or a crop of one is fine — today three ranked rows fill a 1440×900 frame);
    and the skipped-members table still groups `no bars` / `no basis` honestly while a pre-J-15 snapshot
    still renders every honest legacy-absence string (screenshot) (T-10: no screenshot ⇒ `unknown`, never
    `passing`; **no native `title` tooltip is required by this journey** — every reveal is DOM content, so
    the T-10a headed rig is NOT needed and no capture may depend on one) (**single source of truth**: this
    journey renders only what `GET /research/desk/screen` already serves — `desk_screen.ScreenStore` remains
    the only owner and that GET the only serving endpoint; the `rank` cell renders the row's own position in
    the SERVED order (the order J-03 already records as data) and the page never re-orders, sorts or
    filters it; zero new value is computed, zero recorded shape changes, no new Data-Contract row is
    needed, and the BACKEND TAKES A ZERO DIFF — this SSOT criterion stands in place of a PnL-ledger append,
    which this era's Non-Goals forbid); every stored golden replay script replays green (two scripts
    edited — see the amendment below), `tests/test_desk_hover_tooltip_guard.py` passes unmodified, and
    every recorded universe, screen, top-up and reconciliation file is proven byte-identical on disk
    (SHA-256 listing — a render-only iteration writes no record at all); a **`[NEW]`-flagged demo-narrator
    walkthrough** covers the briefing end to end with the `opposite` and `levels` columns visible IN ITS OWN
    FRAMES and its click targets naming ONE row (closing iter-21's and iter-23's RECORDED_WITH_NOTES frame
    gap, where the film narrated columns its own frames could not show); and the full backend suite is green
    with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools, zero
    diff to `desk_screen.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
    2026-07-30. Width — iter-23's own browser-QA measured the ranked table at `scrollWidth` 1795 px inside a
    `clientWidth` 1214 px `overflow-x: auto` container at a 1440 px viewport, with the `levels` header's
    rect at left 1658 / right 1901, entirely outside the visible window (`UT-07` = **FAIL**, P2/non-gating;
    `UT-07-fail.png` shows the table cut off after `band`, so `opposite` (J-14) and `levels` (J-15) — the two
    newest and densest disclosures — are unreachable at any monitor size because the cap is the page's own
    `max-w-7xl`). Cause — for the #1 row of `screen-2026-07-30-bad6387963ef` (100 ranked / 1 skipped, all
    100 rows `band_class A`, `distance_bps` median 3.38, 15 rows tied at 0.00) the five disclosure cells
    carry 194 of the row's 263 rendered characters (74%), all inside `LABEL_CELL`'s `whitespace-nowrap`, and
    the per-column maxima across the 100 rows sum to 309 characters (`opposite` 50, `levels` 62, `history`
    38, `band` 36, `basis` 35) — about 35 of them per row being label prefixes the headers already state.
    Height — `DeskCoverageBadges` is `flex flex-wrap`, so the four badges stack into four lines and each
    ranked row is ~115 px tall: three rows fill a 1440×900 frame and 100 rows span ~11,500 px. Vision gap —
    Key Capability 4 and J-04 step 2 both name `(rank, symbol, …)` first and Success Criterion 4 says
    "descriptive chips", yet `grep rank app/desk/page.tsx` matches only comments and prose (16 hits, zero
    cells) and the class/distance cells carry no chip styling. And iter-23's own iteration summary records
    that "a layout decision … is due before any 13th column is added" and asks the next proposer cycle to
    own it, while the iter-21 and iter-23 walkthrough films were RECORDED_WITH_NOTES for exactly this
    reason.)*

> **AMENDED (desk layout reflow).** The clauses in this journey that forbade PAGINATING `rows` and required "zero script edits" no longer hold, by explicit operator decision. The ranked briefing now renders one contiguous 10-row WINDOW of the served order at a time. What the clauses were protecting is intact and still guarded: the page performs no `.sort(`, no `.reverse(` and no comparator over `rows` (`test_desk_ui_guards.py::test_desk_page_never_reorders_rows_client_side`, narrowed to those two with the narrowing recorded in its own test); the ONE slice on the page is the page window itself, pinned verbatim by `test_desk_page_slices_rows_only_for_the_ranked_page_window`; and every rendered rank is still the row's ABSOLUTE position in the served array — row 11 reads 11 — pinned by `test_desk_ranked_rows_render_an_absolute_rank_across_pages`. Two golden steps were edited rather than zero: J-16 step 3 (its bare `BRK-B` was a page-wide text match that a 10-row window and the moved Forward Returns table would each have turned into a FALSE GREEN — it is now scoped inside `desk-screen-rows-table`) and J-12 step 4 (the coverage-divergence note's own copy said those rows were "below", which a page window makes untrue). Both edits are recorded in the scripts' own `notes`.

- **J-17: A top-up asks the vendor only for the bars the frozen store cannot already prove**
  - Steps:
    1. Choose each pair's fetch window from that pair's OWN frozen content, read verbatim from the
       canonical owner — the single ascending `BarStore.merged_bars(symbol, timeframe)` read
       (`bars.py:557`, the SAME accessor `desk_screen._resolve_reference_close_and_history` and
       `tradability._select_daily_series` already use), never from `bar_index`'s
       `window_end_utc`, which records what an earlier run ASKED for rather than what the store can
       prove (and whose single owner stays `desk_coverage`). Exactly three cases, decided per pair
       inside the shared walker's own `_run_one_pair` (`desk_topup_compute.py:141`): a pair with
       NOTHING frozen keeps the byte-identical full `_TOPUP_LOOKBACK_DAYS` window it asks for today
       (`:98`/`_fetch_window_now`, `:109`); a pair whose frozen bars do NOT reach back to that
       lookback start keeps that SAME full window, so short histories keep deepening exactly as they
       do now; and a pair whose frozen bars already reach the lookback start asks for a tail window
       `[the pair's own newest frozen bar's UTC date, today]`, so the boundary session is always
       re-requested and re-merged, never assumed complete. The end bound stays `_fetch_window_now()`'s
       wall-clock today, unchanged. **Zero diff** to `bars.py`, `record_bar_series`
       (`routes.py:521`), `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py` and
       `levels.py`: the SAME single fetch-and-record seam is called with a different window — no
       second fetch path, no new adapter, no new store, no new `Config` field (`_TOPUP_LOOKBACK_DAYS`
       stays the module constant it is).
    2. Name the vendor's "you already have this" answer honestly. `record_bar_series` refuses content
       already registered with the frozen store's own 409 (`BarSeriesAlreadyRegistered`,
       `routes.py:681`), which `_run_one_pair`'s `except HTTPException` records as `failed` today — a
       tail window makes that the NORMAL weekend/holiday answer. Add exactly ONE new outcome value,
       `unchanged` (a vendor call ran and returned only bars already frozen), beside J-09's shipped
       `reused` (a store-first exact-key hit with ZERO vendor calls — its meaning stays
       byte-unchanged), `fetched` and `failed`; every other refusal keeps its verbatim detail and its
       `failed` label, and nothing is ever recorded as reused that a vendor call actually served.
    3. Record what each pair asked for and why: on each per-pair outcome entry, `requested_window`
       (`{start, end}` — the exact strings that pair sent), `store_frozen_from` and
       `store_frozen_through` (that pair's own earliest/newest frozen bar, both `null` when nothing is
       frozen) and `window_basis` (`"tail"` | `"full_lookback"`; names at build discretion), written
       at the run's terminal state by the SAME single shared writer both callers already use
       (`desk_topup_log.record_topup_run`, from the manager's resolve path and the CLI's `main`) —
       never a second writer, never a second outcome shape. The run-level `requested_window` keeps its
       recorded meaning verbatim (the run's own full-lookback bound). The append-only rail is
       absolute: no recorded run is backfilled, rewritten or recomputed;
       `GET /research/desk/topup/runs` serves legacy runs exactly as recorded and `/desk` renders
       their absent fields as an honest `"window basis not recorded in this run"` (the established
       J-08/J-11/J-13 legacy-absence pattern), never a value derived at read time.
    4. Own it exactly once: register the added per-pair fields and the `unchanged` value on the
       blueprint Data Contract's top-up-run-record row BEFORE the code lands — `desk_topup_log` stays
       the only owner and `GET /research/desk/topup/runs` the only serving endpoint. No new endpoint,
       route, store, `Config` field or MCP tool (J-06's exactly-17-tool contract stays green and
       `get_endpoint`'s `/research/` allowlist already reaches the path). Coverage and freshness keep
       their single existing owner — `desk_coverage.get_desk_coverage` over `bar_index` — and this
       journey creates no second coverage path and serves no coverage value; the top-up stays an
       explicit operator act (POST + CLI + the shipped button), page-load GETs trigger nothing, and no
       scheduler, retry loop or auto-refresh is added anywhere.
    5. Surface it on `/desk` inside the SHIPPED Top-up Runs section — no new section, no new control,
       and NO new column on the ranked table, so J-16's measured width contract stands untouched: the
       latest-run counts line extends to `N reused · N fetched · N unchanged · N failed`
       (`topupOutcomeCounts`, `apps/frontend/app/desk/page.tsx:809` — a plain tally of the served
       payload, nothing derived), one descriptive line states how many pairs asked for a tail window
       and how many for the full lookback, and each already-rendered failed pair additionally shows
       its own recorded `requested_window`. Copy = descriptive measurement only: the page states what
       was asked for and what came back, and never a saving, waste, efficiency, speed or
       recommendation claim; `tests/test_copy_discipline.py` stays green unmodified.
    6. Test fixture-scoped with the suite's own injected fake adapter (the `test_desk_topup_compute.py`
       pattern — no test touches the network): a pair whose planted frozen bars span past the lookback
       start asks for a tail window starting at its own newest frozen bar (asserted BOTH on the
       adapter's received arguments and on the recorded entry); a pair with a short frozen history and
       a pair with nothing frozen each ask for the byte-identical full window they ask for today; a
       fetch whose answer holds only already-frozen bars records `unchanged`, not `failed`, and writes
       no second series file; and every EXISTING test in `test_desk_topup_compute.py` — including
       TC-7's "a second run is all-reused with zero vendor calls" and TC-8's resumability guarantee —
       passes UNMODIFIED (if any existing assertion genuinely pins the shipped window for a pair whose
       frozen history already reaches the lookback start, disclose it in the iteration record rather
       than edit the test).
  - Acceptance: on the fixture-scoped rig, a pair whose frozen series reaches back past the lookback
    start is asked for `[that pair's own newest frozen bar's UTC date, today]` — proven by the fake
    adapter's received window AND by the run record's own `requested_window`/`store_frozen_through` —
    while a pair with nothing frozen, and a pair whose frozen history stops short of the lookback
    start, are each asked for the byte-identical full `_TOPUP_LOOKBACK_DAYS` window they are asked for
    today (a golden comparison proves the shipped window unmoved for both); a vendor answer holding
    only already-frozen bars is recorded `unchanged` with its `requested_window` and adds no second
    series file, never `failed` (**single source of truth**: the window is derived only from the
    canonical `BarStore`'s own merged read — never from `bar_index`'s request-bound `window_end_utc` —
    the run record stays owned by `desk_topup_log` alone and served by `GET /research/desk/topup/runs`
    alone, with the added fields and the new outcome value registered in the Data Contract BEFORE the
    code lands, and coverage/freshness still come solely from `desk_coverage` over `bar_index`; this
    SSOT criterion stands in place of a PnL-ledger append, which this era's Non-Goals forbid); every
    bar series file already on disk is proven byte-identical before and after the iteration (SHA-256
    listing — a top-up only ever APPENDS a new series; nothing is deleted, re-keyed, superseded or
    rewritten), and every previously recorded universe, screen, top-up and reconciliation record is
    proven byte-identical too, with legacy top-up runs rendering the honest `"window basis not
    recorded in this run"` state; in a real browser after the T-9 clean rebuild, `/desk`'s Top-up Runs
    section shows the four-outcome counts including at least one `unchanged`, the tail-versus-full
    window line, and one failed pair with its own recorded `requested_window`, all legible in ONE
    screenshot at a 1440×900 viewport with no horizontal scroll, and the ranked briefing table renders
    exactly as J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title`
    tooltip is required by this journey, so the T-10a headed rig is not needed); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the top-up's window disclosure end to end,
    narrated over a populated run; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
    zero diff to
    `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`StructureChart.tsx`,
    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. The
    real ~100-symbol Yahoo top-up stays an operator-run act, reported honestly as run-or-not-run —
    never a CI gate. Why: measured 2026-07-30 from the desk's own recorded ledger and the frozen store.
    The one recorded real top-up, `topup-2026-07-29-5de907c83fc4` (404 pairs, 12:00:29Z → 12:04:53Z),
    reports **`0 reused · 390 fetched · 14 failed`** — `reused` has never once been recorded on a real
    run. Cause: `_fetch_window_now()` is wall-clock (end = today, start = 730 d earlier) while
    `record_bar_series`'s store-first is an **exact-key** `(symbol, timeframe, window_start,
    window_end)` index hit (its own docstring, `routes.py:558`), so a window whose end moves each day
    can structurally never hit — Key Capability 2's "store-first (a symbol×timeframe already frozen in
    the store is reused, never re-fetched)" is unreachable on the real path, and J-02's "a second run
    reports all-reused" holds only for two runs inside one UTC day. Cost, measured against the store's
    own files: for the **235** pairs the store ALREADY held before that run, the run downloaded
    **276,714** bars and gained **13,533** new ones (**4.9 %**); for **174** of those 235 the entire
    download yielded **≤ 5** new bars (91,226 downloaded, 348 new), median 4. AAPL `1d` is the clean
    case — a 500-bar 730-day series re-downloaded to add exactly **one** bar to the 501 already frozen;
    MSFT `1d` is the counter-case the full window must keep serving, gaining 112. Steady state today:
    **390 of the 404** member × timeframe pairs already hold bars reaching past the lookback start,
    **5** hold shorter histories (HONA ×4, MSFT `1h`) and **9** hold nothing (8 × `1h` + NOW `1d`), so
    the next daily run under today's rule re-downloads on the order of the 462,535 bars / 68.5 MB that
    run recorded across 390 series to gain a day. The whole store is 759 series files / 220 MB /
    1,766,542 recorded rows, of which 301,271 (17.1 %) are timestamps another series for the same pair
    already holds. And the wrinkle a tail window creates is already visible in the code: an
    already-registered answer raises the store's 409 (`routes.py:681`), which `_run_one_pair` records
    as `failed` — so without the `unchanged` outcome a weekend run would print a wall of false
    failures.)*

- **J-18: Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks**
  - Steps:
    1. Resolve the run's five pins BEFORE the walk, using ONLY accessors that already exist and are
       already each pin's single owner: `desk_screen.screen_as_of` (`desk_screen.py:233`), the
       universe store's own latest record id (`UniverseStore.list()`'s `records[-1]["id"]` — the
       identical read `compute_screen` makes at `:441`), `Config.config_fingerprint()`, and
       `desk_screen.compute_bar_store_signature` (`:255`, which exists precisely "so a caller (or a
       test) can resolve the 5-pin key's `bar_store_signature` component WITHOUT running the full
       per-member walk", over `desk_coverage.get_desk_coverage`'s index-only read, T-4). **No new
       derivation of any pin, no new value**: the signature keeps its single owner
       (`_bar_store_signature` over `desk_coverage`), and `compute_screen` keeps resolving its own
       pins exactly as it does today — the same functions over the same immutable store, so the two
       resolutions cannot disagree.
    2. Answer an already-recorded pin set without paying for the walk: inside the ONE shared entry
       point both callers already use (`run_screen_and_record`, `desk_screen_compute.py:73`), a
       `ScreenStore.find_by_key` hit on those five pins (`desk_screen.py:602` — the SAME lookup that
       path already performs at `desk_screen_compute.py:114`, one line AFTER the walk it could have
       avoided) returns the existing snapshot with `reused=True` immediately: zero
       `compute_tradability` calls and no `BarStore` read beyond the index-only coverage read the pin
       resolution already made. Nothing else moves — the manager's
       `GET /research/desk/screen/compute` poll shape stays byte-unchanged (`state`/`reused`/
       `screen_id` keep their exact recorded meanings; `progress.members_done` simply stays 0),
       `ScreenStore.record` remains the ONLY writer and its `ScreenAlreadyRecorded` refusal remains
       the structural backstop for the race where the store changes under a running walk, and a
       trigger whose pins MISS runs the full walk byte-identically to today.
    3. Persist ONE frozen, checksummed, append-only run record per run, written EXACTLY ONCE at the
       run's terminal state by a SINGLE shared writer BOTH callers use — the manager's resolve path
       (`desk_screen_compute.py:197`/`:226`) and the CLI's `main` (`:271`) — the J-09/J-10
       `record_topup_run`/`record_reconcile_run` discipline verbatim. Recorded with it: run id,
       `screen_date`, the five pins as resolved (each honestly `null` when a run failed before
       resolving it), started/finished UTC, terminal state (`done`/`cancelled`/`failed`), `reused`
       (true when step 2 short-circuited), `members_total` and `members_attempted` (so "attempted"
       and "never reached" stay distinct — the J-09 rule), the walk's own outcome counts (ranked,
       `skipped: no_bars`, `skipped: no_basis`), the resulting `screen_id` or an honest `null`, and —
       on `failed` — the exception detail VERBATIM plus the member the walk was on when it raised.
       This journey changes NO walk behavior: `compute_screen`'s member loop (`desk_screen.py:455`)
       keeps its shipped semantics (no per-member guard is added, no error skip row is invented, a
       cancelled partial walk is still never recorded) — the record makes the outcome legible, it
       does not alter it. A run whose process ends before the terminal write records NOTHING and the
       ledger never invents an entry for it (J-09's honest limit, asserted by a test).
    4. Own it exactly once: a new desk module (name at build discretion, e.g.
       `app/research/desk_screen_log.py`) as the ONLY owner and `GET /research/desk/screen/runs` as
       the ONLY serving endpoint (lightweight run-meta list + the latest full record; honest-empty
       `{"runs": [], "latest": null}`, HTTP 200, before any run), serving its own store's
       verification errors as `integrity_errors` in the same key and shape its four sibling desk GETs
       already use (the J-12 rule) — registered as a NEW row in the blueprint's Data Contract BEFORE
       the code lands, storage dir a bare env-var-or-sibling default (the `resolve_desk_screen_dir`/
       `resolve_desk_topup_log_dir` precedent — deliberately NOT a new `Config` field). The record
       describes the RUN only: screen rows, skip rows and the five-pin snapshot key keep their single
       owner (`desk_screen.ScreenStore`) and their single serving endpoint
       (`GET /research/desk/screen`), and nothing about what a snapshot records, how it is keyed, or
       how rows are ranked changes. No new MCP tool (J-06's exactly-17-tool contract stays green and
       `get_endpoint`'s `/research/` allowlist already reaches the new path), no scheduler, no
       auto-refresh, no retry loop — a screen run stays an explicit operator act and page-load GETs
       trigger nothing.
    5. Surface it on `/desk`: a read-only "Screen Runs" section beside the shipped Screen History,
       Top-up Runs and Index Reconciliation sections (the same table-plus-latest-detail pattern, no
       recompute, NO new control), each run showing its date + id, terminal state, members
       attempted-of-total, the ranked/skipped counts, its own recorded start→finish elapsed and the
       snapshot id it produced — or the honest "reused <id> — no walk was performed" and "nothing
       recorded" states — with the latest run's failure detail rendered verbatim when it failed, an
       honest no-run-recorded empty state, and its ledger's `integrity_errors` line. **No new
       ranked-table column and no change to the ranked table**, so J-16's measured width contract and
       every stored golden replay script stand untouched. Copy = descriptive measurement only: the
       page states what a run attempted and what it produced, never advice, imperative, urgency,
       prediction, or any saving/waste/efficiency/speed claim; `tests/test_copy_discipline.py` stays
       green unmodified.
    6. Test fixture-scoped: a completed run's recorded counts are byte-identical to its own
       snapshot's `len(rows)` and its skip counts by reason; an identical-pin re-trigger records
       `reused: true` with `members_attempted: 0`, makes provably ZERO `compute_tradability` calls
       (assert the call count — the J-11/J-13/J-14/J-15 precedent), returns the SAME `screen_id` and
       writes no second snapshot file; a cancelled run records `cancelled` with
       `members_attempted < members_total` and `screen_id: null` while still recording no snapshot; a
       raising member records `failed` with the detail verbatim and that member named, and no
       snapshot; a second run appends a new record while the first record file stays byte-identical;
       the GET is honest-empty before any run and triggers nothing; and every EXISTING test in
       `test_desk_screen_compute.py` and `test_desk_screen.py` passes UNMODIFIED — in particular
       `test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file` (:373),
       `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot` (:718) and
       `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`
       (:287), whose outcomes the pre-check must reproduce exactly (if one genuinely pins a full walk
       on an identical-pin retrigger, disclose it in the iteration record rather than edit it — the
       J-17 precedent).
  - Acceptance: on the fixture-scoped rig `GET /research/desk/screen/runs` serves the honest empty
    payload before any run and, after one fixture-scoped screen run, ONE record whose `members_total`/
    `members_attempted`, ranked and skip-by-reason counts, five pins and `screen_id` are byte-identical
    to the snapshot that run recorded (**single source of truth**: the run record is registered in the
    Data Contract with the new desk module as its only owner and `GET /research/desk/screen/runs` as
    its only serving endpoint; it records the RUN only — rows, skip rows, the five-pin key and the rank
    order keep `desk_screen.ScreenStore` as their sole owner and `GET /research/desk/screen` as their
    sole serving endpoint, with zero change to any recorded snapshot shape — and every pin is resolved
    through the accessor that already owns it (`screen_as_of`, `UniverseStore.list`,
    `Config.config_fingerprint`, `compute_bar_store_signature` over `desk_coverage`), never a second
    derivation; this SSOT criterion stands in place of a PnL-ledger append, which this era's Non-Goals
    forbid); a re-trigger under identical pins returns the SAME `screen_id` with `reused: true`,
    records `members_attempted: 0`, makes zero `compute_tradability` calls and writes no second
    snapshot file, while a trigger whose pins MISS still walks every member and records a snapshot
    byte-identical to what those same pins produce today (a golden comparison proves the recorded rows
    and their order unmoved); a cancelled run records `cancelled` with
    `members_attempted < members_total`, `screen_id: null` and no snapshot; a run interrupted before
    its terminal write leaves the ledger honestly empty rather than a fabricated entry; a second run
    appends a new record while every previously recorded universe, screen, top-up and reconciliation
    file is proven byte-identical on disk (SHA-256 listing — nothing backfilled, repaired or
    rewritten); in a real browser after the T-9 clean rebuild, `/desk` shows the honest
    no-run-recorded state in one screenshot and, after a fixture-scoped run, the Screen Runs section
    with attempted-of-total, the ranked/skipped counts, the elapsed and the produced snapshot id
    legible in another, plus one screenshot in which a `reused` run's own row states that no walk was
    performed — all at a 1440×900 viewport with no horizontal scroll and the ranked briefing table
    rendering exactly as J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native
    `title` tooltip is required by this journey, so the T-10a headed rig is not needed); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the screen-run disclosure end to end,
    narrated over a populated ledger; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
    tools, zero diff to
    `desk_screen.py`'s recorded row/snapshot shapes and to
    `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_topup_log.py`/`StructureChart.tsx`,
    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. A
    real ~101-member screen run stays an operator-run act, reported honestly as run-or-not-run — never
    a CI gate. Why: measured 2026-07-31 from the desk's own artifacts. **The desk's central act is the
    only compute whose runs vanish.** `.data/screen` holds 11 recorded snapshots and every one carries
    exactly `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature,
    created_utc, rows, skipped}` — no start time, no duration, no members-attempted count, no terminal
    state — while its two lesser siblings each keep a durable ledger: `.data/topup_runs` holds
    `topup-2026-07-29-5de907c83fc4` (404 pairs, `12:00:29.889748Z` → `12:04:53.521809Z` = 4m23.6s) and
    `.data/index_reconcile_runs` holds two reconcile records (5.5 s and 10.8 s), each with its own
    state, counts and timings. `DeskScreenComputeManager`'s state is process-scoped and "honestly lost
    on restart" (its own docstring, `desk_screen_compute.py:9-11`), so every screen run that failed,
    was cancelled, or found its pins already recorded left NOTHING on disk anywhere; the only runs with
    any trace are the 11 that happened to write a NEW snapshot, and even they cannot say how long they
    took — the four recorded back-to-back on 2026-07-29 (`created_utc` 12:06:52.688, 12:15:46.801,
    12:22:19.019, 12:24:33.312) sit 8m54s, 6m32s and 2m14s apart, which bounds nothing. **The silence
    is paid for on every duplicate click.** `/desk`'s Run Screen always submits today's UTC date
    (`todayUtcDate`, `apps/frontend/app/desk/page.tsx:204/209`) and `trigger` "ALWAYS runs the full
    member walk … rather than pre-checking the store before paying for it"
    (`desk_screen_compute.py:21`), calling `compute_tradability` DIRECTLY — never through the 128 MB
    durable `tradability_cache.db` that `GET /research/tradability` reads (`:23-27`) — across all 101
    members of `universe-2026-07-25-49b33fa31680`, after which `ScreenStore.record` refuses the
    duplicate; iter-3's own dev handoff live-verified the first symbol alone taking several seconds
    cold. **And the fix needs no new machinery:** the same docstring names it ("a future iteration can
    add a cheap pre-check (the five pins resolve synchronously before the walk, the SAME way
    `members_total` already does)"), `compute_bar_store_signature` (`desk_screen.py:255`) exists for
    exactly that purpose, and `find_by_key` (`:602`) is already called on that path one line after the
    walk. **When a run does die, the record is the only place the reason could live:**
    `compute_screen`'s member loop (`desk_screen.py:455`) has no per-member guard and
    `_resolve_reference_close_and_history` raises on its own invariant (`:378`), so one member's
    exception discards all 100 ranked rows already computed — today into a process-scoped snapshot the
    next restart erases.)*

- **J-19: Every top-up run records the date each pair's frozen history actually reaches**
  - Steps:
    1. Record ONE new desk-owned field on every per-pair outcome entry the shared walker already
       builds (`run_topup`'s `entry` dict, `desk_topup_compute.py:304`): `store_frozen_through_after`
       (name at build discretion) — that pair's own newest frozen bar AFTER the attempt, read
       VERBATIM from the canonical owner through the SAME pure accessor J-17 already uses,
       `_pair_window` over `BarStore.merged_bars(symbol, timeframe)` (`desk_topup_compute.py:162`/
       `:182`, whose own docstring already sanctions repeat calls — "A PURE read (zero vendor calls,
       zero writes) — safe to call more than once"), called once more immediately after
       `_run_one_pair` returns and recorded beside the pre-fetch `store_frozen_through` J-17 already
       records. Never `bar_index`'s `window_end_utc` (whose single owner stays `desk_coverage`),
       never a new accessor, never a second fetch, never arithmetic over bars, and never a change to
       `_run_one_pair`'s two-value return shape — the manager-mechanics tests substitute a FAKE
       `_run_one_pair` returning a two-tuple (`tests/test_desk_topup_compute.py:139`/`:192`/`:339`/
       `:870`) and every one of them must keep passing unmodified. The value is `null` only when the
       pair holds nothing at all, exactly the shape `store_frozen_through` already uses. **Zero
       diff** to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`,
       `levels.py` and `routes.py`'s `record_bar_series`; zero new `Config` field; no new store,
       endpoint, route or MCP tool.
    2. State what it does NOT mean, structurally. The record describes THIS RUN's own observation of
       the frozen store at attempt time — the J-09 rule verbatim: coverage and freshness keep their
       single existing owner (`desk_coverage.get_desk_coverage` over `bar_index`), this journey
       creates no second coverage path, cache or copy, serves no coverage value, adds no coverage
       read anywhere, and leaves the ranked table's own coverage badges and their "window last
       requested" tooltip byte-unchanged (`apps/frontend/app/desk/page.tsx:284`/`:357`). `/desk`
       still fetches no coverage endpoint, and no screen row shape changes.
    3. Own it exactly once: register the added per-pair field on the blueprint Data Contract's
       "Top-up run records" row BEFORE the code lands — `desk_topup_log` stays the only owner and
       `GET /research/desk/topup/runs` the only serving endpoint, written by the SAME single shared
       writer both callers already use (`desk_topup_log.record_topup_run`, from the manager's resolve
       path `desk_topup_compute.py:413` and the CLI's `main` `:547`) — never a second writer, never a
       second outcome shape. The append-only rail is absolute: no recorded run is backfilled,
       rewritten or recomputed; `GET /research/desk/topup/runs` serves legacy runs exactly as
       recorded and `/desk` renders their absent field as an honest `"library reach not recorded in
       this run"` (the established J-08/J-11/J-13/J-17 legacy-absence pattern), never a value derived
       at read time. The top-up stays an explicit operator act (POST + CLI + the shipped button),
       page-load GETs trigger nothing, and no scheduler, retry loop or auto-refresh is added
       anywhere.
    4. Surface it on `/desk` inside the SHIPPED Top-up Runs section — no new section, no new control,
       no new column on the runs table and NO new column on the ranked briefing table, so J-16's
       measured width contract stands untouched: the latest-run detail gains one descriptive line
       naming the newest date this run's own pairs reach and how many pairs reach it, plus a short
       list of the pairs whose recorded date is earlier (or `null`), each rendered with its own
       symbol, timeframe and recorded date verbatim — both a plain tally/extreme over the served
       payload, nothing derived from bars (the `topupOutcomeCounts`/`topupWindowBasisCounts`
       precedent, `apps/frontend/app/desk/page.tsx:834`/`:857`). Copy = descriptive measurement only:
       the page states the dates the run recorded and never a fresh/stale/current/behind/up-to-date
       judgement, an advice, imperative, urgency or prediction, and never a saving, waste,
       efficiency, speed or recommendation claim; `tests/test_copy_discipline.py` stays green
       unmodified.
    5. Test fixture-scoped with the suite's own injected fake adapter (the
       `test_desk_topup_compute.py` pattern — no test touches the network): a pair whose fetch
       genuinely appends bars records an `after` value later than its own recorded
       `store_frozen_through` and byte-identical to the newest bar `BarStore.merged_bars` then
       reports for that pair; a pair recorded `unchanged` and a pair recorded `failed` each record
       their pre-fetch value verbatim; a `reused` pair records its pre-fetch value; a pair that held
       nothing and whose fetch failed records `null`; a second run appends a new record while the
       first record file stays byte-identical; the GET is honest-empty before any run and triggers
       nothing; and every EXISTING test in `test_desk_topup_compute.py` and `test_desk_topup_log.py`
       — including TC-7's "a second run is all-reused with zero vendor calls", TC-8's resumability
       guarantee, the manager-mechanics tests' fake `_run_one_pair`, and
       `test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_end_utc` (`:614`)
       — passes UNMODIFIED (if one genuinely pins the walker's per-pair read count, disclose it in
       the iteration record rather than edit it — the J-17 precedent).
  - Acceptance: on the fixture-scoped rig every per-pair outcome entry of a NEW top-up run carries
    `store_frozen_through_after` byte-identical to the newest bar
    `BarStore.merged_bars(symbol, timeframe)` reports for that pair after the walk — later than its
    own recorded `store_frozen_through` exactly for the pairs whose fetch appended bars, equal to it
    for every `reused`/`unchanged`/`failed` pair, and `null` only for a pair holding nothing
    (**single source of truth**: the value is read verbatim from the canonical `BarStore`'s own
    merged read through the accessor J-17 already calls — never `bar_index`'s request-bound
    `window_end_utc`, never a second fetch, never a new accessor — the run record stays owned by
    `desk_topup_log` alone and served by `GET /research/desk/topup/runs` alone, with the added field
    registered in the Data Contract BEFORE the code lands; it records this run's own ATTEMPT-time
    observation and never current coverage, and coverage/freshness still come solely from
    `desk_coverage` over `bar_index`, with the briefing's coverage badges and their tooltip
    byte-unchanged — this SSOT criterion stands in place of a PnL-ledger append, which this era's
    Non-Goals forbid); every bar series file already on disk is proven byte-identical before and
    after the iteration (SHA-256 listing — a top-up only ever APPENDS a new series; nothing is
    deleted, re-keyed, superseded or rewritten) and every previously recorded universe, screen,
    top-up and reconciliation record is proven byte-identical too, with legacy top-up runs rendering
    the honest `"library reach not recorded in this run"` state; in a real browser after the T-9
    clean rebuild, `/desk`'s Top-up Runs section shows the latest run's reach line AND at least one
    pair whose own recorded date is earlier than that newest date, both legible in ONE screenshot at
    a 1440×900 viewport with no horizontal scroll, and the ranked briefing table renders exactly as
    J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title` tooltip is
    required by this journey, so the T-10a headed rig is not needed); a **`[NEW]`-flagged
    demo-narrator walkthrough** covers the top-up's library-reach disclosure end to end, narrated
    over a populated run; and the full backend suite is green with
    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
    tools, zero diff to
    `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`StructureChart.tsx`,
    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable.
    The real ~101-member top-up stays an operator-run act, reported honestly as run-or-not-run —
    never a CI gate. Why: measured 2026-07-31 read-only over the frozen artifacts (no service
    started, no product code run). **A top-up says what it asked for and what came back, never what
    the library then holds.** The one recorded real run, `topup-2026-07-29-5de907c83fc4` (404 pairs,
    12:00:29.889748Z → 12:04:53.521809Z, `0 reused · 390 fetched · 14 failed`), carries only
    `{symbol, timeframe, outcome, detail}` per pair, and even a post-J-17 run records the store's
    content only as it stood BEFORE each fetch (`store_frozen_through`) — so no artifact anywhere
    states the date a pair's history reaches once a run ends. Reconstructing it took a walk of all
    759 series files: that run advanced 235 pairs (by 3 d ×58, 4 d ×110, 5 d ×1, 6 d ×1, 7 d ×58,
    14 d ×3, 15 d ×3, 22 d ×1), recorded 155 pairs for the first time, and failed 14. **What the
    silence hides today:** the newest bar each pinned pair actually holds now spans 2026-07-21 to
    2026-07-28 — `1h`: 88 members through 07-28, AAPL/AMT/BLK/LOW through 07-24, MSFT through 07-21,
    and 8 members (MDT, MRK, MU, NEE, PEP, TMO, UNH, UPS) hold none; `4h`: 101 through 07-28; `1d`:
    100 through 07-27 (NOW holds none — the screen's one `skipped: no basis` row); `1w`: 101 through
    07-27. The only freshness the desk serves is `bar_index`'s `MAX(window_end_utc)` — the window a
    run ASKED for — which for 394 of the 395 member × timeframe pairs that hold bars postdates the
    newest bar actually held, by 1 day (193 pairs) or 2 days (201 pairs); the single exception is
    MSFT `1h` (both read 2026-07-21). On `screen-2026-07-31-c169546856c7` (100 ranked / 1 skipped)
    that renders as BLK #17 — a band of 134 levels, 53 of them `1h`, over a `1h` series that stops
    2026-07-24 — beside BRK-B #1's 155-level band with 57 `1h` members over a series through
    2026-07-28, both rows showing an identical lit `1h` badge whose only difference is a requested
    window in a hover tooltip (`2026-07-25T00:00:00Z` vs `2026-07-29T00:00:00Z`). And J-17's tail
    window ends at wall-clock today for every pair it applies to, so after the next daily top-up even
    that faint request-bound difference collapses to one identical date for every successful pair.)*

- **J-20: Every recorded screen states how it differs from the screen recorded before it**
  - Steps:
    1. Compare exactly TWO already-recorded snapshots, read verbatim through the accessor that already
       owns them — `ScreenStore.list()` (`desk_screen.py:581`, the SAME `(records, errors)` read all
       three branches of `GET /research/desk/screen` already make, `desk_routes.py:353`/`:377`/`:381`).
       For every symbol ranked in the COMPARE snapshot, in that snapshot's OWN served rank order (the
       order J-03 step 2 already records as data — never re-sorted, never re-ranked, never re-scored),
       copy VERBATIM its own 1-based position plus its recorded `side`, `band_class`, `distance_bps`
       and `basis_as_of`, and the same values from the BASE snapshot's own recorded row for that
       symbol, plus `rank_change` — a plain integer subtraction of two ALREADY-RECORDED positions (the
       `basis_age_days` precedent, `desk_screen.py:388`: arithmetic over recorded values, never a new
       measurement). A symbol ranked in the compare snapshot but not in the base is reported as
       `entered` carrying the base snapshot's own recorded skip `reason` (`no_bars`/`no_basis`) when it
       has one and an honest `null` when that snapshot does not mention the symbol at all; a symbol
       ranked in the base but not in the compare is `left`, the same way. **Zero diff** to
       `desk_screen.py`'s recorded row/snapshot shapes and to
       `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`; zero new `Config`
       field; no `BarStore`, `bar_index` or dataset read of ANY kind; and nothing is recomputed — no
       `compute_tradability` call, no band selection, no rank-key evaluation (assert the call counts,
       the J-11/J-13/J-14/J-15 precedent).
    2. Resolve the base in the OWNER, never on the page: the default base for a compare snapshot is the
       recorded snapshot with the greatest `screen_date` STRICTLY earlier than the compare snapshot's
       own `screen_date`, ties (two recordings of one earlier date) broken by the later `created_utc` —
       i.e. exactly the record `GET /research/desk/screen?date=<that earlier date>` already serves
       (`matching[-1]`, `desk_routes.py:381`), so the two reads can never disagree. An explicit
       `base=<id>` overrides it. The payload ALWAYS names both snapshots it compared — `id`,
       `screen_date`, `as_of`, `created_utc`, `bar_store_signature`, `universe_snapshot_id` and
       ranked/skipped counts, each copied verbatim from that record's own meta — and states how the
       base was chosen. When no earlier `screen_date` exists the payload is an honest "no earlier
       recorded screen" state with `base: null`, never a fabricated comparison; an unknown id is an
       honest `null` at HTTP 200 (the `?id=` convention, `desk_routes.py:377`); a snapshot compared
       with itself is an honest refusal, never a silent no-op.
    3. Own it exactly once: a new desk module (name at build discretion, e.g.
       `app/research/desk_screen_diff.py`) as the ONLY owner and ONE serving endpoint (exact path at
       build discretion, e.g. `GET /research/desk/screen/compare`) — registered as a NEW row in the
       blueprint's Data Contract BEFORE the code lands. It PERSISTS NOTHING: no store, no file, no
       cache, no index, no new `Config` field, no new MCP tool (J-06's exactly-17-tool contract stays
       green and `get_endpoint`'s `/research/` allowlist already reaches the new path). The GET
       recomputes nothing, writes nothing and triggers nothing (the 5C lesson); screen rows, skip rows,
       the five-pin snapshot key and the rank key keep `desk_screen.ScreenStore` as their sole owner
       and `GET /research/desk/screen` as their sole serving endpoint, and nothing about what a
       snapshot records, how it is keyed, or how rows are ranked changes. Determinism is structural:
       the body is a pure function of two IMMUTABLE recorded files, so the same two ids reproduce a
       byte-identical body, and the payload carries no wall-clock field of its own (T-6).
    4. Disclose, never judge. This journey states what two recordings say and stops there: it never
       ranks, filters, gates, weights, scores, or orders by size of change, and it never measures
       whether a wall held, broke, was reached, or produced any reaction — outcome measurement is
       era-6 "The Referee" and stays entirely out (this era's Non-Goals). Concretely: no threshold, no
       significance/confidence number, no churn/stability/volatility metric, no "notable"/"biggest
       mover"/"top movers" framing, no ordering by `|rank_change|` anywhere (the compare snapshot's own
       served order is the only order), no arrow or colour that gives a direction a valence, and no
       advice, imperative, urgency or prediction language; `tests/test_copy_discipline.py` stays green
       unmodified.
    5. Surface it on `/desk` as ONE new read-only "Screen Comparison" section rendered AFTER the ranked
       briefing table, beside the shipped Screen History / Top-up Runs / Index Reconciliation / Screen
       Runs sections (the same table-plus-detail pattern, no new control, no recompute, page-load GETs
       trigger nothing): both snapshots' own ids, screen dates, recorded-at and `bar_store_signature`s;
       one descriptive counts line (rows compared, rank changed, side changed, entered, left); an
       honest "the compared snapshots' ranked rows are identical" line when every compared field
       matches; the honest no-earlier-screen state; and a capped table of the compare snapshot's own
       first N rows (the shipped `EARLIER_PAIRS_DISPLAY_CAP` precedent,
       `apps/frontend/app/desk/page.tsx:882`/`:1032`, with its honest "showing N of M" line) each
       showing the symbol, this snapshot's recorded rank/side/distance and the base's own recorded
       rank/side/distance, with an honest "not recorded in the compared snapshot" for a field the
       base's row does not carry (the J-08/J-13/J-14 legacy-absence pattern) — never a value derived on
       the page. The section describes whichever snapshot the page is DISPLAYING (the shipped `?id=`
       history selection), so opening a past screen compares THAT screen. **No new ranked-table column
       and no change to the ranked table**, so J-16's measured width contract stands untouched.
    6. Keep every browser and test contract the shipped journeys rest on, and test fixture-scoped:
       every existing `data-testid` keeps its element and its exact text; the new section introduces no
       attribute or selector an existing golden's click target can match (it never reuses
       `data-screen-id`, `desk-history-row`, `desk-screen-row` or any `desk-row-*` testid) and —
       because the replay tool's text matcher takes the FIRST visible match
       (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:641`) — it renders after the ranked
       table so no stored expect (J-13/J-14's literal band strings, J-12/J-13/J-14's snapshot ids)
       can resolve into it; all 19 stored golden replay scripts replay green (J-16's own former
       `BRK-B` pin is now scoped inside the briefing table — see the J-16 amendment) and
       `tests/test_desk_ui_guards.py` +
       `tests/test_desk_hover_tooltip_guard.py` pass unmodified. Backend tests over planted scoped
       snapshots: two snapshots whose ranked rows are identical report zero changes; a pair with moved
       ranks, a flipped side, an entered symbol and a left symbol reports each exactly once with both
       recorded values verbatim; the oldest recorded snapshot reports the honest no-earlier-screen
       state; an unknown id is an honest null; the same two ids twice produce a byte-identical body;
       the GET writes nothing and issues no `compute_tradability` call (assert the call count); and a
       legacy base row missing `basis_as_of` is reported absent, never derived.
  - Acceptance: `GET` the new comparison endpoint for a recorded snapshot and it names both snapshots it
    compared and reports, for every symbol ranked in the compare snapshot in that snapshot's OWN served
    order, its recorded rank/side/`band_class`/`distance_bps`/`basis_as_of` beside the base snapshot's
    own recorded values for the same symbol — each byte-identical to what
    `GET /research/desk/screen?id=<that snapshot's id>` serves for that row — plus the entered/left sets
    with the other snapshot's own recorded skip reason where it has one (**single source of truth**: the
    comparison is a NEW value with exactly one owner, the new desk module, and exactly one serving
    endpoint, registered in the Data Contract BEFORE the code lands; it reads two immutable recorded
    snapshots through `ScreenStore.list` and copies their values verbatim — zero recompute, zero second
    read of any store, zero change to what a snapshot records, to its five-pin key, or to the rank key,
    which keep `desk_screen.ScreenStore` and `GET /research/desk/screen` as their sole owner and sole
    serving endpoint, and the page derives no rank, distance or difference of its own — this SSOT
    criterion stands in place of a PnL-ledger append, which this era's Non-Goals forbid); the default
    base is the record `?date=` already serves for the greatest strictly-earlier screen date, the same
    two ids reproduce a byte-identical body, the endpoint writes nothing, and every recorded universe,
    screen, top-up, reconciliation and screen-run file is proven byte-identical on disk before and after
    the iteration (SHA-256 listing — a read-only iteration records nothing); in a real browser after the
    T-9 clean rebuild, at a 1440×900 viewport with no horizontal scroll and the ranked briefing table
    rendering exactly as J-16 shipped it, `/desk` shows the Screen Comparison section in three states
    across screenshots — the identical state (zero rank changes, zero side changes, zero entered, zero
    left, both `bar_store_signature`s equal), a churned state with at least one row whose recorded rank
    moved by ≥ 20 places and one whose side differs between the two recordings, and the honest
    no-earlier-recorded-screen state on the ledger's oldest snapshot (on the ambient ledger as it stands
    these are, respectively, `screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef`,
    `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384` — 95 of 100 rows changed rank,
    12 changed side, PLTR recorded 7 then 84 — and `screen-2026-06-22-3ecd45c062c7`; if the ledger has
    moved by build time, the same three states over whatever snapshots it then holds, reported honestly)
    (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title` tooltip is required by this
    journey, so the T-10a headed rig is not needed and no capture may depend on one); a
    **`[NEW]`-flagged demo-narrator walkthrough** covers the screen-comparison disclosure end to end,
    narrated over a populated ledger and over both the identical and the churned pair; and the full
    backend suite is green with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new
    `Config` fields, the `default` profile and `v1` byte-identical (engine equivalence green), the MCP
    surface still exactly 17 tools, zero diff to
    `desk_screen.py`/`desk_coverage.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`,
    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. Why:
    measured 2026-07-31 read-only over the frozen artifacts (no service started, no product code run).
    **The desk records 12 screens and relates none of them to any other.** No desk module and no line of
    `apps/frontend/app/desk/page.tsx` compares two snapshots: `GET /research/desk/screen` serves a
    meta-only `screens` list, a `latest`, and single snapshots by `?date=`/`?id=`, and every rendered
    view is standalone. Yet the ledger's own pairs sit at both extremes and print identically. Pairing
    each of the 12 with the record for its greatest strictly-earlier screen date: FOUR pairs changed
    nothing at all — `screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef`, that one vs
    `screen-2026-07-29-2a57de4e7415`, that one vs `screen-2026-07-28-817d92d9c924`, and
    `screen-2026-07-28-ac07c9581a4f` vs `screen-2026-07-27-3ad3c57aa6ba` — 0 of 100 (0 of 63) rows
    changed rank, side or `distance_bps`. A field-by-field diff of the four consecutive 100-row screens
    07-28 → 07-29 → 07-30 → 07-31 shows the ONLY field that differs across all 100 ranked rows is
    `basis_age_days` (3 → 4 for every row on the last step): all four share basis
    `2026-07-27T04:00:00.000000Z` and bar-store signature `ae2c740d1a70c9c7`, and each cost a full walk —
    `screenrun-2026-07-31-725c4ec2bfcd` records 101 members attempted, 01:58:48.238Z → 02:00:29.056Z.
    SEVEN pairs churned instead: `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384` —
    95 of 100 common rows changed rank, 89 changed `distance_bps`, 12 changed side, PLTR 7 → 84, JPM
    19 → 96, UBER 2 → 77, and only 5 of the top ten symbols stayed in it — and
    `screen-2026-07-28-817d92d9c924` vs `screen-2026-07-27-3ad3c57aa6ba` — 61 of 63 common rows changed
    rank, 8 changed side, 37 symbols entered the ranked set (AAPL 19 → 100). On `/desk` today, "the same
    100 rows for the fourth day running" and "95 of 100 rows moved and 12 flipped side" render as the
    same screen: one ranked table, with no relation to anything recorded before it.)*

- **J-21: The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now**
  - Steps:
    1. Resolve the five pins for a CALLER-SUPPLIED screen date using ONLY the accessors that already own
       each one, in the SAME order `run_screen_and_record` resolves them (`desk_screen_compute.py:155`–
       `:161`): `desk_screen.screen_as_of` (`desk_screen.py:233`), the universe store's own latest record
       id (`UniverseStore.list()`'s `records[-1]["id"]`), `Config.config_fingerprint()`, and
       `desk_screen.compute_bar_store_signature` (`desk_screen.py:255`) over
       `desk_coverage.get_desk_coverage`'s index-only read (`desk_coverage.py:40` → `BarIndex.coverage`,
       `bar_index.py:154`) — **no `BarStore` read of any kind** (T-4), no new derivation, no new pin, no
       second owner: the same functions over the same immutable store, so this resolution and a run's own
       cannot disagree (the J-18 rule verbatim). The date comes from the caller — the page passes the SAME
       `todayUtcDate()` value it already submits to the trigger (`apps/frontend/app/desk/page.tsx:228`/
       `:2350`) — so nothing on the new path calls `now()`; the body is a pure function of (requested
       date, the pinned universe record, the index's rows as they stand), identical inputs reproduce a
       byte-identical body, and the payload carries no wall-clock field of its own (T-6).
    2. Answer the one question those pins decide, through the owner that already answers it:
       `ScreenStore.find_by_key` on exactly those five pins (`desk_screen.py:602` — the SAME lookup
       J-18's pre-check makes at `desk_screen_compute.py:209`) either NAMES the snapshot already recorded
       under them — its own `id`, `screen_date`, `created_utc`, `bar_store_signature` and ranked/skipped
       counts copied VERBATIM out of that record's own meta — or is an honest `null`. Beside it,
       `members_total`: the pinned universe record's own member count, read the way
       `DeskScreenComputeManager.trigger` already reads it (`len(records[-1]["members"])`,
       `desk_screen_compute.py:336`), so "a run would walk N members" is a recorded count and never an
       estimate. Nothing is recomputed and nothing is ranked: zero `compute_tradability` calls, zero band
       selections, zero rank-key evaluations, zero bar reads.
    3. Own it exactly once: a new desk module (name at build discretion, e.g.
       `app/research/desk_screen_pins.py`) as the ONLY owner and ONE serving endpoint (exact path at
       build discretion, e.g. `GET /research/desk/screen/pins`) — registered as a NEW row in the
       blueprint's Data Contract BEFORE the code lands. It PERSISTS NOTHING: no store, no file, no cache,
       no index, no new `Config` field, no new MCP tool (J-06's exactly-17-tool contract stays green and
       `get_endpoint`'s `/research/` allowlist already reaches the new path). The GET writes nothing,
       computes nothing and triggers nothing (the 5C lesson): screen rows, skip rows, the five-pin
       snapshot key and the rank key keep `desk_screen.ScreenStore` as their sole owner and
       `GET /research/desk/screen` as their sole serving endpoint, with zero change to what any desk store
       RECORDS or to any recorded shape; coverage and freshness keep their single existing owner
       (`desk_coverage.get_desk_coverage` over `bar_index`) and no second coverage path, cache or copy is
       created anywhere; and nothing this journey adds starts, schedules, retries or auto-refreshes any
       screen, top-up or reconciliation run — every run stays an explicit operator act.
    4. Disclose, never judge. The endpoint and the page state what the pins ARE and whether a recording
       exists under them, and stop there. The bar-store signature is a checksum over every member's
       window-LAST-REQUESTED value — the page's own shipped note already says so
       (`apps/frontend/app/desk/page.tsx:1725`) — so a differing signature proves exactly ONE thing: that
       no recorded screen carries these pins, i.e. a run for this date would walk rather than reuse. The
       copy therefore never claims that bars arrived, that the library advanced, or that any ranked row
       would change, never uses a fresh / stale / current / behind / up-to-date / outdated judgement, and
       never advises, predicts, implies urgency or names an action to take; no threshold, score,
       confidence or staleness number is computed anywhere (this era's Non-Goals forbid new statistics and
       gates outright), and `tests/test_copy_discipline.py` stays green unmodified.
    5. Surface it on `/desk` as ONE more mount-time GET beside the shipped ones (no timer, no polling
       loop, no auto-refresh — at most a refetch where the page already refetches its ledgers on a
       terminal compute tick): (a) the Provenance panel (`DeskProvenance`,
       `apps/frontend/app/desk/page.tsx:1702`) renders the resolved pins beside the DISPLAYED snapshot's
       own recorded pins, with the match/differ statement computed at the OWNER and served — the page
       derives nothing, not even an equality (the J-20 rule); (b) one descriptive line beside the Run
       Screen control names the snapshot a run for that date would reuse (its own recorded id and
       recorded-at) or states that no screen is recorded under the resolved pins and that a run would walk
       `members_total` members; and (c) an honest empty state when no universe snapshot is registered.
       **No new ranked-table column and no change to the ranked table**, so J-16's measured width contract
       stands untouched at a 1440×900 viewport; every existing `data-testid` keeps its element and its
       exact text; the row's stretched drill-in anchor keeps its `href`, `absolute inset-0`, `data-testid`
       and dynamic consolidated `title` byte-unchanged.
    6. Test fixture-scoped, over scoped universe/screen/bar-index stores (never `apps/backend/.data`): the
       GET's resolved pins are byte-identical, value by value, to the pins `run_screen_and_record` resolves
       for the SAME date over the SAME stores (the two resolutions cannot disagree); with a snapshot
       recorded under those pins the payload names it and every copied meta field is byte-identical to that
       record's own file, and a trigger for that date still reuses exactly the named snapshot (J-18's
       shipped behaviour, unchanged); after ONE row is planted in the scoped index the same GET for the same
       date resolves a different `bar_store_signature` and reports `recorded: null`, and a trigger then
       walks and records a NEW snapshot while the earlier file stays byte-identical; with no universe
       snapshot the payload is an honest empty at HTTP 200; the GET writes nothing and makes ZERO
       `compute_tradability` calls and ZERO `BarStore` reads (assert the call counts — the
       J-11/J-13/J-14/J-15 precedent); the same inputs twice produce a byte-identical body; every EXISTING
       test in `test_desk_screen.py`, `test_desk_screen_compute.py`, `test_desk_coverage.py`,
       `test_desk_ui_guards.py` and `test_desk_hover_tooltip_guard.py` passes UNMODIFIED; and a static
       sweep of all 20 stored golden replay scripts proves no string this journey adds can resolve ahead of
       any script's intended target (the J-20 rule — the replay matcher takes the FIRST visible match), so
       every golden replays green with ZERO script edits (if a collision is unavoidable, MOVE the added
       copy rather than edit a script).
  - Acceptance: on the fixture-scoped rig the new GET, for a screen date whose five pins a recorded
    snapshot already carries, names THAT snapshot with its `id`/`created_utc`/`bar_store_signature` and
    ranked/skipped counts byte-identical to the record on disk and reports `members_total` equal to the
    pinned universe record's own member count, while a trigger for that date reuses exactly that snapshot;
    after a single row is planted in the scoped bar index, the same GET resolves a different
    `bar_store_signature`, reports `recorded: null`, and a trigger then walks every member and records a
    NEW snapshot with the earlier file byte-identical on disk (**single source of truth**: the resolution
    is a NEW value with exactly one owner — the new desk module — and exactly one serving endpoint,
    registered in the Data Contract BEFORE the code lands; every pin is resolved through the accessor that
    already owns it (`screen_as_of`, `UniverseStore.list`, `Config.config_fingerprint`,
    `compute_bar_store_signature` over `desk_coverage`'s index-only read), never a second derivation, and
    the recorded-or-not answer comes from `ScreenStore.find_by_key` — the same lookup the run path makes —
    with `desk_screen.ScreenStore` remaining the sole owner of rows, skip rows, the five-pin key and the
    rank key and `GET /research/desk/screen` their sole serving endpoint; the endpoint persists nothing,
    computes nothing, reads no bar and serves no coverage value, and the page derives nothing, not even a
    match/differ equality — this SSOT criterion stands in place of a PnL-ledger append, which this era's
    Non-Goals forbid); the honest empty state is served at HTTP 200 when no universe snapshot is
    registered; every recorded universe, screen, top-up, reconciliation and screen-run file is proven
    byte-identical on disk before and after the iteration apart from the snapshots the iteration's own
    fixture-scoped runs deliberately create (SHA-256 listing — this journey's own code records nothing);
    in a real browser after the T-9 clean rebuild, at a 1440×900 viewport with no horizontal scroll and
    the ranked briefing table rendering exactly as J-16 shipped it, `/desk` shows BOTH states across
    screenshots — one in which the displayed screen's own recorded pins match the resolved ones and the
    page names the snapshot a run would reuse, and one in which they differ and the page states that no
    screen is recorded under the resolved pins and that a run would walk `members_total` members — plus
    one screenshot of the honest empty state (T-10: no screenshot ⇒ `unknown`, never `passing`; no native
    `title` tooltip is required by this journey, so the T-10a headed rig is NOT needed and no capture may
    depend on one); a **`[NEW]`-flagged demo-narrator walkthrough** covers the pin disclosure end to end,
    narrated over both states; and the full backend suite is green with `Config().config_fingerprint()`
    still `08e471b10130e1e2`, zero new `Config` fields, the `default` profile and `v1` byte-identical
    (engine equivalence green), the MCP surface still exactly 17 tools, zero diff to
    `desk_screen.py`/`desk_screen_compute.py`/`desk_coverage.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`,
    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. Why:
    measured 2026-07-31 read-only over the frozen artifacts (no service started, no product code run) —
    the bar-store signature was reconstructed with the module's OWN algorithm (`_bar_store_signature`,
    `desk_screen.py:242`: sorted `(symbol, timeframe, MAX(window_end_utc))` tuples over the pinned
    universe's members × `DESK_TOPUP_TIMEFRAMES`, canonical JSON, `sha256[:16]`) directly from
    `.data/bar_index.db`. **No recorded screen can be reused today, and the page cannot say so.** The 12
    snapshots in `.data/screen` carry four distinct signatures (`d7bc8f8127904d0a` ×2,
    `7eab5f03cf23e8c7`, `350c85d18b1ff234` ×3, `ae2c740d1a70c9c7` ×6); the index as it stands resolves
    **`2ce14e8f252966f7`** — a value NO recorded screen carries. The displayed briefing
    `screen-2026-07-31-c169546856c7` (100 ranked / 1 skipped, recorded `2026-07-31T02:00:29.054546Z` under
    `ae2c740d1a70c9c7`) carries today's own screen date and looks current, but the 06:52→06:56Z top-up
    `topup-2026-07-31-8fb5c9a1f737` moved `MAX(window_end_utc)` to `2026-07-31T00:00:00Z` for **404 of 404**
    pinned member × timeframe pairs, so that snapshot's own recorded coverage differs from the live index
    on 404 of 404 pairs and its pin can no longer be hit. **The same click therefore has two behaviours
    and nothing distinguishes them:** the desk's own screen-run ledger records
    `screenrun-2026-07-31-725c4ec2bfcd` walking 101 members in 1m41s (`01:58:48.238Z` → `02:00:29.056Z`)
    beside `screenrun-2026-07-31-0662273df270` and `screenrun-2026-07-31-fe0829e64a0d`, which J-18's
    pre-check resolved as `reused` in 14 ms and 16 ms — all three for screen date 2026-07-31, all three
    invisible in advance. **And the briefing reads as if nothing were pending:** every one of its 100 rows
    prints `basis 2026-07-27 · 4 d before as-of` while the frozen store now holds `1d` bars through
    2026-07-30 for all 101 members (read from the series files' own `covered_end_utc`; the 40 pairs whose
    legacy files predate that meta field were all recorded on or before `2026-07-21T22:35:58Z` and cannot
    hold newer content), which invites the reading "no newer daily close exists" when the truth is that
    this screen predates the top-up. `GET /research/desk/screen/compute` serves only the process-scoped
    manager snapshot (`null` after a restart, its own docstring), and `compute_bar_store_signature` exists
    precisely so a caller can resolve the pin "WITHOUT running the full per-member walk" — no endpoint,
    no page and no MCP tool exposes it today.)*

<!-- /AUTO:journeys -->

## Anti-goals

**Immutable rails — the identity of the project (from
[`docs/research-directions.md`](research-directions.md) §0.3; enforced by existing tests and
audits; only ever grow more specific, never weaker):**

1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
   trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
   tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
   fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
   imperative trading cues. *(critical)*
3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
   states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
   surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
   a mutation of them. (The 5D demolition's removals are final history; this era builds `/desk`
   BESIDE the kept two pages — the sanctioned kept-surface edits are J-05's additive `/structure`
   prefill and **R-1**'s price-less-row repair, which changes no output for finite data and leaves
   every recorded series on disk untouched.) *(critical)*
4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
   through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are
   labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
   feeds/fingerprints to manufacture a survivor. *(critical)*
5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
   *(critical)*
6. **Single source of truth** — each shared value is computed once, owned by one canonical
   endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
   violations. *(critical)*
7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
   requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
   research artifact.
8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
   MCP surface can change state. *(critical)*
9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
   re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
   *(critical)*
10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an
    explicit, logged act. *(critical)*

**Desk-era anti-goals (added, not weakening any rail above):**

- **Membership is never a signal.** Universe membership (and any constituents metadata) selects
  WHAT to screen; it never enters a computation, rank formula beyond selection, feature, or
  report as an input value. *(critical)*
- **Snapshots are append-only and pinned.** Universe and screen snapshots are dated, checksummed,
  append-only; every screen pins (universe snapshot id, screen date, as_of, fingerprint,
  bar-store signature); nothing is silently refetched, backfilled, recomputed in place, or
  rewritten — a new run is a new snapshot. *(critical)*
- **Every run is an explicit operator act.** No scheduler, cron, daemon, auto-refresh, or
  market-hours trigger anywhere; page-load GETs never trigger fetches or computes. *(critical)*
- **The briefing describes, never advises.** Desk copy is descriptive measurement only — no
  advice, imperative, prediction, or ranking language implying action ("buy", "watch this",
  "opportunity"); the copy-discipline lint stays green unmodified. *(critical)*
- **No new statistics, gates, or strategies.** No probability/expectancy/edge claims on any desk
  surface; champion, `v1`, `default`, gates, and minimum-n floors untouched (the Referee is a
  future era). *(critical)*
- **The demolition stays demolished.** No journal-era machinery returns; the desk ledger records
  machine output only — zero manual-input write paths on desk records this era (dispositions/
  annotations are Era C's design space). *(critical)*
- **The ledger never holds orders.** No sizes, tickets, entries/exits, or account concepts in any
  desk record — rail 1 in desk terms. *(critical)*
- **The suite stays keyless and hermetic.** Committed fixtures cover every test path; no test
  fetches the network; live fetch/top-up/screen runs are operator-run verifications reported
  honestly (run-or-not-run), never CI gates. *(critical)*
- **The fingerprint pin does not move.** All new Config fields take Path A (exclusion + stability
  test + counter-test + payload provenance, same commit); `08e471b10130e1e2` is asserted unchanged
  by the sentinel every iteration. *(critical)*
- **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside
  the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this
  Anti-goals section, or any other part of this file; proposed journeys MUST carry a
  single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
  `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
  journey just to keep the loop alive is a failure. *(critical)*

**Host protection (added 2026-07-28 — a physical constraint of the host, not product scope):**

- **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
  2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
  with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
  beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
  (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
  bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
  interactive pump sessions are auto-confined in place by the engine (`host-guard-adopt.sh`;
  `scripts/automation/host-guard-exec.sh claude` is the optional from-birth wrapper) — the
  engine pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
  Never disable,
  widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
  the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*
