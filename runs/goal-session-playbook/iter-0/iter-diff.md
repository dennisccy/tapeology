# Iteration diff (bounded)

Files changed: 3. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `docs/goal-archive/goal-2026-08-10.md` (1658 lines not shown)
- `docs/goal.md` (2242 lines not shown)

```diff
diff --git a/docs/goal-archive/goal-2026-08-10.md b/docs/goal-archive/goal-2026-08-10.md
new file mode 100644
index 0000000..ca8e3c4
--- /dev/null
+++ b/docs/goal-archive/goal-2026-08-10.md
@@ -0,0 +1,2052 @@
+# Tapeology — Project Goal (Era B: The Desk — a daily screening desk over a fetched universe)
+
+> Eras 1–5D are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution,
+> GOAL_ACHIEVED) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md);
+> the structure-UI interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
+> **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
+> the **"Fast Wall" performance interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
+> and the **"Clean Slate" demolition interlude (GOAL_ACHIEVED 2026-07-24, session `clean_slate`)** at
+> [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md). Eras 3, 4, 5B "The Tradable
+> Wall", and 5C "The Fast Wall" are frozen foundation; their records live in git history and in
+> `reports/goal-session-*-delivered.md`.
+>
+> **This chapter is Era B of the operator's three-era pivot (A Demolition → B Desk → C Annotator,
+> decided 2026-07-23).** Era A demolished the journal-era surfaces: the product today is exactly
+> **Cockpit (`/`) + Structure (`/structure`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP
+> surface is 15 read-only tools, and the honesty machinery (stores, gates, registry, PnL promotion
+> ledger) is fully intact. The Desk is the first BUILDING era on that cleared ground: an automated
+> **universe screener + screen ledger + daily briefing**, operated through the UI and through
+> Claude + MCP. It is an operator-directed product era OUTSIDE the research catalog
+> ([`docs/research-directions.md`](research-directions.md) has no Desk card; per its §5.6 this file
+> wins for the running era). The statistics program (era-6 "The Referee") and the AI annotation
+> corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
+>
+> **The Desk adds ZERO new research math.** It orchestrates, persists, and surfaces the frozen
+> 5B/5C computations (tradable-map bands, level classes, bar coverage) across many symbols. Every
+> new number it serves is either read verbatim from an existing canonical owner or is a new
+> desk-owned value (rank rows, coverage rows, snapshot metadata) with exactly one new owner.
+
+## Vision
+
+The instrument can read one symbol deeply — levels, zones, tradable bands, case studies, edge
+report — but the operator starts every day with the OPPOSITE problem: *which of the ~100 liquid
+names deserves the instrument today?* Era B builds that answer as a product:
+
+1. **A fetched, registered universe.** S&P 100 constituent membership is fetched from a documented
+   public source on explicit operator command and registered as a dated, checksummed, append-only
+   **universe snapshot** — never silently refetched, never edited, never a signal input. The suite
+   and the UI run keyless on a committed fixture snapshot; live fetch is an operator act.
+2. **An honest bar library over that universe.** A coverage view says, per member, which
+   timeframes have bars and how fresh they are — read from the durable `bar_index`, never by
+   re-hashing stores. An explicit, resumable **top-up** run fetches missing/stale series through
+   the existing keyless Yahoo seam, store-first (a symbol×timeframe already frozen in the store is
+   reused, never re-fetched).
+3. **An operator-run screen with an append-only ledger.** One button (and one CLI, and one POST)
+   walks the pinned universe snapshot as-of a screen date and summarizes, per symbol, what the
+   FROZEN tradable-map computation says: best band, band class, distance from the last daily close
+   in bps, band score, coverage and tick-evidence badges. The ranked result persists as an
+   append-only **screen snapshot** keyed by its inputs (screen date, as-of, universe snapshot,
+   `config_fingerprint`, bar-store state) — identical inputs reproduce byte-identical rows, and
+   a member with no bars appears as an honest `skipped: no bars` row, never a guess. Because every
+   row is as-of-stamped and lookahead-free, a FUTURE era can measure whether the desk's top-ranked
+   walls produced reactions — the ledger is tomorrow's evidence, not today's advice.
+4. **A briefing the operator (and Claude) actually opens.** A third page — **`/desk`** — renders
+   the latest screen as a dense, descriptive briefing with full provenance, an honest
+   "Desk screen not computed yet." empty state, a Run Screen button with live progress, browsable
+   screen history, and per-row drill-in that preloads `/structure` for that symbol and as-of.
+   Two new read-only MCP tools expose the same payloads byte-identically, so the desk can be
+   operated from a Claude conversation end to end.
+
+The deliverable: the two-page instrument becomes a three-page **desk** — universe in, briefing
+out, every number owned once, every run explicit, every record append-only and evaluable later.
+
+## Target Users
+
+- The project owner (a discretionary intraday trader) who starts the day on `/desk`: run the
+  screen, read the briefing, drill into `/structure` for the names whose walls are close.
+- The same owner operating through **Claude + MCP**: `desk_universe` / `desk_screen` (plus the
+  existing 15 tools) make the whole desk readable from a conversation.
+- AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.
+
+## Foundation invariants (still law — eras 1–5D)
+
+The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
+remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
+fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
+deterministic & reproducible; no secrets in source; research read-only over the engine; record
+integrity; source/feed/`config_fingerprint` honesty. Its surface inventory is the POST-demolition
+one: `/` and `/structure` (this era adds `/desk`).
+
+1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
+   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era — every new
+   `desk_*` Config field takes §0.4 **Path A** (exclusion + stability test + counter-test); a pin
+   movement is a defect, full stop.
+2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
+   cache), `edge_report*.py`, `backtests.py`, the strategy registry (`v1` + `structure_tape` +
+   `structure_tape_map`), `profiles.py` (`default`), the champion pointer — stay behaviorally
+   byte-identical. The desk READS them; it never re-implements, re-tunes, or re-grades.
+3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only
+   immutability, split freezing, the durable accelerator DBs (`bar_index`, `dataset_index`,
+   edge-report caches, setups scan cache, tradability cache) — are untouched in format and
+   discipline. Registered datasets and bar series are never deleted, re-tagged, or
+   content-perturbed. The era ADDS a universe store and a screen store under the same discipline.
+4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, MCP `pnl_ledger`)
+   stays append-only and intact; the champion pointer does not move this era.
+5. The **kept surfaces as shipped**: the cockpit (live/sim/historical tape, `PriceChart.tsx`
+   container behaviors, panels) and `/structure` (Load flow, Tradable Map, Case Studies, Edge
+   Report + Compute button, fetch control + provenance badge) — including **both charts**
+   (`StructureChart.tsx`, `PriceChart.tsx`) — keep working exactly as shipped. The ONLY sanctioned
+   `/structure` edit is J-05's additive query-param prefill of the existing Load form.
+6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this era
+   adds two GET-proxy tools (15 → 17) and never adds writes.
+
+### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1
+
+**Ratified and IN INVENTORY for this era**, in addition to everything named above: the
+price-less-bar repair the chain landed in iteration 4, comprising exactly
+
+- `apps/backend/app/providers/adapters/yahoo.py` — `_is_priced_row` drops a vendor row that
+  carries no price at the fetch seam (an all-priceless window still raises `NoDataForWindow`);
+- `apps/backend/app/research/bars.py` — `BarStore.record` refuses a non-finite price before any
+  write (`NonFiniteBarPriceError`, mapped to 422), and `_merged_rows` excludes already-recorded
+  price-less **rows** on read, reporting them through the existing `integrity_errors` channel;
+- `apps/backend/app/research/routes.py` — one `except NonFiniteBarPriceError` clause on
+  `record_bar_series`, mapping the refusal to the same honest 422 the empty-window refusal already
+  uses (an added `except` + import line; no existing behavior altered);
+- `apps/frontend/components/StructureChart.tsx` — a finite-value guard on the OHLC series
+  (defence in depth);
+- `apps/backend/tests/test_structure_chart_viewport.py` — the one chart-guard assertion relaxed
+  from exact text to a pattern, to match the guarded expression above;
+- `apps/backend/tests/test_bars.py` — six ADDED tests covering the rail (write refusal per field,
+  whole-series refusal, checksum integrity of a planted price-less series, read-time row
+  exclusion + its `integrity_errors` report, append-only file untouched by exclusion, memo
+  preserved). Additions only — no existing test in this file was modified or removed;
+- `apps/backend/tests/test_yahoo_adapter.py` — five ADDED tests for the vendor-seam drop
+  (all-NaN row, real rows undisturbed, all-priceless window raises, NaN volume). Additions only;
+- `apps/backend/tests/test_bars_api.py` — one ADDED test proving the merged read never serves a
+  null-priced candle. Additions only.
+
+**Why:** the vendor genuinely serves a price-less AAPL daily row. Before the repair, one Top-up
+click persisted `NaN`-priced bars into the append-only store, which crashed `/structure`'s chart
+and silently emptied the tradable map (`compute_tradability("AAPL", as_of=2026-07-25)` returned
+`bands: []`). The repair restores honest behavior; it changes nothing for all-finite data, and the
+pinned wall still computes `resistance 300.11–302.2 class A score 171`.
+
+**Scope of the ratification, precisely:** the 60 already-affected bar series stay **on disk,
+untouched** — excluded row-by-row on read, never deleted, re-keyed, or rewritten. The pin
+`08e471b10130e1e2` does not move. `bars.py`'s file format, checksums, append-only immutability and
+split freezing are unchanged; only its write-time refusal and read-time row exclusion are new.
+This ratification does NOT open `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, or any guard
+test to further edits — anything beyond the eight files above still needs a new ratification.
+
+Where the clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
+subject to **R-1**.
+
+## Success Criteria
+
+In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
+
+1. **Nothing kept regresses.** Full backend suite green (1169 pass / 7 skip at era open — grows,
+   never shrinks); engine equivalence proves byte-identical `default` outputs;
+   `Config().config_fingerprint()` prints `08e471b10130e1e2` in every iteration; every kept `/`
+   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified
+   (subject to **R-1**).
+2. **The universe is honest.** Membership comes only from registered, dated, checksummed,
+   append-only snapshots; the parser validates (charset, count bounds, normalization) or fails
+   with an honest error — it NEVER emits a guessed or partial list; the committed fixture keeps
+   every test and default UI state keyless; live fetch happens only on explicit operator command.
+3. **The screen is deterministic and evaluable.** A screen run pins (universe snapshot id, screen
+   date, as-of, `config_fingerprint`, bar-store signature); identical pins reproduce byte-identical
+   rows; members without bars are honest `skipped` rows; snapshots are append-only and never
+   backfilled or recomputed in place; every row's structure numbers match the canonical owners
+   byte-for-byte for the same inputs.
+4. **The briefing is a real product surface.** `/desk` is the third nav row (data-driven from
+   `app/meta.py`); it renders ranked rows with descriptive chips + provenance, honest empty/
+   partial states, a Run Screen button with progress + cancel, browsable history, and drill-in
+   that lands on `/structure` preloaded — all browser-verified with screenshots.
+5. **The desk is Claude-operable.** `desk_universe` and `desk_screen` are byte-identical GET
+   proxies; `ui_route_map` lists the three routes; the MCP suite proves the 17-tool contract.
+
+## Key Capabilities
+
+1. **Universe subsystem (new data kind, honest by construction).** A universe vendor seam (the
+   bars-vendor pattern) fetching S&P 100 membership from ONE documented public source; a parser
+   contract (ticker charset `[A-Z.-]{1,6}`, count sanity 90–110, **Yahoo normalization
+   `BRK.B → BRK-B`**, dedupe, sorted output); registration as
+   `apps/backend/.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json` (frozen JSON = source of
+   truth; any index over it is derived/rebuildable); a committed fixture snapshot under
+   `apps/backend/tests/fixtures/` for hermetic tests + default keyless UI;
+   `GET /research/desk/universe` serving snapshot list + latest membership with honest emptiness.
+2. **Coverage + top-up.** `GET /research/desk/coverage` (or a `universe` payload block): per-member
+   × per-timeframe bar presence + freshness read from `bar_index` (NEVER re-hashing the store);
+   an explicit operator-run top-up (POST + CLI) that walks members store-first through the
+   existing `POST /research/bars` fetch path, resumable, worker-capped, logging per-symbol
+   outcomes; the timeframe set = exactly what `compute_levels`/`compute_tradability` read for a
+   daily-close screen (verify at build time; era-5 contract: `4h` is resampled from `1h`, never
+   fetched; intraday microscope tfs stay per-symbol on `/structure`).
+3. **Screen compute + append-only ledger.** An operator-run screen (POST + CLI + `/desk` button)
+   over the pinned latest universe snapshot: per member, call the CANONICAL owners
+   (`compute_tradability` / levels / `bar_index`) as-of the screen date's session close and
+   summarize best band, class, distance-from-close (bps), band score, coverage + tick-evidence
+   badges; deterministic rank order = (band class A>B>C, then distance asc, then band score desc,
+   then symbol asc); single-flight + progress + cancel via the 5C compute-manager pattern;
+   persistence as append-only screen snapshots (frozen JSON + derived index) with full input pins;
+   `GET /research/desk/screen` (latest / `?date=`) + honest `"Desk screen not computed yet."`.
+4. **The `/desk` briefing page.** Third nav row; latest-screen briefing table (rank, symbol,
+   band class chip, distance chip, score, coverage/evidence badges, skipped rows grouped
+   honestly); provenance line (universe snapshot id + date, as-of, fingerprint, bar-store
+   signature); Run Screen + top-up buttons with live progress + cancel; screen history list;
+   dark/dense/terminal-grade per house style.
+5. **Drill-in + `/structure` prefill.** Clicking a briefing row navigates to
+   `/structure?symbol=<sym>&asof=<iso>`; `/structure` gains query-param PREFILL of its existing
+   Load form (prefill + auto-Load; `apps/frontend/app/structure/page.tsx` inputs at ~:2057/:2070)
+   — no other `/structure` behavior changes; the desk never recomputes structure values.
+6. **MCP contract v3 — 17 read-only tools.** Add `desk_universe` → `/research/desk/universe` and
+   `desk_screen` → `/research/desk/screen` to `_STATIC_PATHS` (`app/mcp/__init__.py:85`);
+   `get_endpoint` allowlist (`/tape/`, `/research/`, `/meta/`) already covers the new paths
+   unchanged; `tests/test_mcp_server.py` proves the 17-tool contract with byte-identity and
+   honest-error clauses.
+
+## Non-Goals
+
+- **No statistics program.** No new gates, CIs, nulls, multiple-testing control, or promotion
+  logic — that is era-6 "The Referee" (future). The screen RANKS by existing descriptive
+  structure metrics; it never claims edge, probability, or expectancy.
+- **No annotation layer.** Human/AI pattern annotation, dispositions, notes, or any manual input
+  path on desk records is Era C "The Annotator" (designed separately). This era's ledger records
+  MACHINE output only.
+- **No strategy/champion work.** No new strategies/profiles, no backtest changes, no champion
+  movement, no PnL-ledger rows beyond what existing machinery already writes.
+- **No scheduling.** No cron, daemon, auto-refresh, or market-hours trigger — every fetch,
+  top-up, and screen run is an explicit operator act (UI button / CLI / POST).
+- **No tick-data expansion.** No new dataset recording, no credential work; tick evidence badges
+  reflect the 11 recorded dataset symbols as they stand.
+- **No engine, chart, or kept-surface work.** `app/engine/` untouched; `StructureChart.tsx`
+  untouched **except R-1's finite-value guard**; `PriceChart.tsx` untouched; `/structure` untouched
+  beyond the J-05 prefill.
+- **No fingerprint epoch bump.** Path A only; the pin `08e471b10130e1e2` does not move.
+- **No second market, no options/sentiment/news data, no paid services.** The one new external
+  read is the documented constituents source; membership is universe METADATA, never a signal
+  input (the roadmap's earnings-calendar exclusion-only precedent).
+
+## Constraints
+
+- **Stack (carried over):** Frontend Next.js 15 + TypeScript + Tailwind v3 (npm),
+  `lightweight-charts`, dark-only. Backend Python 3.12 + FastAPI. Backend `http://localhost:8000`,
+  frontend `http://localhost:3000` (browser-QA rig on `:8301`/`:3301`). No new runtime dependency
+  (the universe fetch uses the stdlib/HTTP client patterns the Yahoo adapter already uses).
+- **Config discipline (§0.4 Path A, every time):** every new SEMANTIC knob is a `Config` field
+  (`desk_universe_source_url`, `desk_universe_min_members`, `desk_universe_max_members`, plus any
+  the build genuinely needs) added to the `config_fingerprint()` exclusion set
+  (`app/config.py:1312`) **in the same commit**, with (i) a stability test proving the pin is
+  unchanged and (ii) a counter-test proving the field alters the NEW path's output, and its value
+  embedded in the desk payloads it shapes (provenance duty — the `structure_tape_*` worked
+  example). Operational knobs (worker counts, timeouts, store dirs) may be env vars per the 5C
+  precedent (`TAPEOLOGY_DATASET_DIR` pattern); a field that changes SERVED VALUES is never an env
+  var.
+- **Snapshot discipline:** universe + screen snapshots are frozen JSON files (source of truth,
+  content-checksummed, append-only) with derived, rebuildable indexes — the `BarStore`/
+  `dataset_index` pattern. No snapshot is ever edited, re-keyed, or silently regenerated;
+  re-running a screen for the same pins either reproduces byte-identical content or refuses with
+  an honest already-recorded response. `journal.db` gets NO new tables (schema stays v8).
+- **No-lookahead as-of rule (morning-markup convention):** a screen for date D builds its map from
+  the last completed session STRICTLY BEFORE D (`tradability._resolve_basis`; every level read is
+  bounded to that prior session's close), so D's own session never enters the map and the forward
+  measurement reads D's own session out-of-sample. D therefore names the TRADE day, not the data
+  day. The recorded `as_of` (`D T23:59:59Z`) is the snapshot key's upper bound and part of the
+  snapshot key; there is no "refresh today's screen in place" — a new run is a new snapshot.
+- **Single source of truth:** the desk owns ONLY its new values (universe membership/metadata,
+  coverage rows, screen rank rows). Band geometry, classes, scores come from
+  `compute_tradability` (`app/research/tradability.py:381`) / `levels.py` verbatim; coverage
+  comes from `bar_index`; the desk NEVER recomputes, re-grades, or caches a divergent copy.
+  The coherence-auditor hard-fails violations.
+- **Copy discipline:** all desk copy is descriptive measurement (distances, classes, counts,
+  dates) — no advice, imperative, or prediction language; `tests/test_copy_discipline.py`'s
+  frontend-literal lint (:220) covers the new page automatically and must stay green unmodified.
+- **Guard tests (kept, never edited):** `tests/test_no_execution_path.py`,
+  `tests/test_no_credential_in_artifacts.py`, the fast_wall source-introspection guards
+  (`test_backtests.py`, `test_setups.py` pins), the chart guard suites, and the 13 fingerprint
+  pin assertions (e.g. `test_profile_equivalence.py:114`) all pass byte-unmodified all era — the
+  single exception is **R-1**'s `test_structure_chart_viewport.py` assertion, relaxed to a pattern
+  to match the guarded expression; no further guard-test edit is authorized.
+- **Hermetic tests:** the suite stays keyless on committed fixtures — the universe fixture
+  snapshot ships in-repo; NO test performs a network fetch; live constituents fetch + 100-symbol
+  top-up + real screens are operator-run verifications, never CI gates.
+- **Browser evidence:** `rm -rf apps/frontend/.next` + rebuild before any browser verification
+  (the stale-build trap); every browser acceptance needs a screenshot — no screenshot ⇒ the
+  journey is `unknown`, never `passing`; route captures in evidence scripts use per-route
+  `curl --max-time`.
+- **Compute-manager reuse:** top-up and screen runs follow `EdgeReportComputeManager`
+  (`app/research/edge_report_compute.py:108`; routes `POST/GET/POST-cancel` at
+  `app/research/routes.py:1268/1293/1302`) — single-flight, snapshot-pollable progress,
+  cancellable, CLI-runnable. Page-load GETs NEVER trigger computes (the 5C lesson).
+
+## Design Direction
+
+Unchanged house style: dark-only, dense, professional, terminal-grade; honest empty/degraded
+states are first-class copy (`"Desk screen not computed yet."`, `"skipped: no bars"`); the
+briefing reads like a trading-floor sheet, not a dashboard toy; no marketing chrome.
+
+## Product Shape
+
+Nav (top bar) after this era: **Cockpit `/` · Structure `/structure` · Desk `/desk`** — data-driven
+from `app/meta.py` `UI_ROUTES` (:27, the single owner); `GET /meta/ui-routes` and MCP
+`ui_route_map` reflect it verbatim.
+
+**Data Contract — new rows (each value computed once, one owner):**
+
+| Value | Owner (module) | Serving endpoint |
+|---|---|---|
+| Universe snapshots + membership | new `app/research/desk_universe.py` (name at build discretion) | `GET /research/desk/universe` |
+| Per-member bar coverage/freshness | same desk module (reads `bar_index` only) | `GET /research/desk/coverage` (or a block of the universe payload — ONE home, decided at build) |
+| Screen snapshots, rank rows, skip rows | new `app/research/desk_screen.py` | `GET /research/desk/screen` |
+| Top-up / screen compute progress | desk compute manager (5C pattern) | `GET /research/desk/*/compute` poll endpoints |
+| Route list (now 3 rows) | `app/meta.py` | `GET /meta/ui-routes` |
+
+**Unchanged owners (the desk reads them verbatim):** bands/scores → `tradability.py`; levels/
+zones/classes → `levels.py`; bars/candles → `bars.py` + `bar_index`; datasets → `datasets.py`;
+edge cells → `edge_report.py`; ledger rows → `pnl_ledger.py`; registry/champion →
+`strategies.py`/store; taxonomy labels → `taxonomy.py`.
+
+## Build anchors & weak-model traps (era B)
+
+Anchors verified against `main @ 05b50ef` (2026-07-25) — **re-locate by symbol name (grep), never
+by line arithmetic**:
+
+- Yahoo fetch seam: `app/providers/adapters/yahoo.py:207` (`YahooAdapter`, `fetch_bars` :233);
+  explicit bar fetch/register: `POST /research/bars` (`app/research/routes.py:519`), store-first.
+- Tradable map: `compute_tradability(store, symbol, as_of_epoch, config)`
+  (`app/research/tradability.py:381`) + durable `tradability_cache.db`.
+- Compute-manager pattern: `EdgeReportComputeManager` (`app/research/edge_report_compute.py:108`),
+  routes at `routes.py:1268/1293/1302`, `/structure` Compute button + progress poll as UI model.
+- Stores: `BarStore` (`app/research/bars.py:210`); `bar_index.db` (coverage truth — 3 symbols have
+  bars at era open: AAPL/AMD/MSFT); `.data/datasets` + `dataset_index.db` (tick evidence — exactly
+  these 11 recorded symbols: AAPL, AMD, AMZN, GOOGL, META, MSFT, NFLX, NVDA, PG, SPY, TSLA).
+- MCP: `_STATIC_PATHS` (`app/mcp/__init__.py:85`), parameterized paths (:107), `get_endpoint`
+  allowlist (:55–65); contract suite `apps/backend/tests/test_mcp_server.py`.
+- Config: `config_fingerprint()` + exclusion set (`app/config.py:1312`); pin literal
+  `08e471b10130e1e2` asserted at 13 sites (e.g. `tests/test_profile_equivalence.py:114`).
+- Frontend: nav auto-follows `meta.py`; `/structure` Load inputs (`app/structure/page.tsx`
+  ~:2057/:2070) are the J-05 prefill target; copy lint `tests/test_copy_discipline.py:220`.
+
+Traps (all learned the hard way in prior eras — read before EVERY iteration):
+
+- **T-1 · Parser honesty.** The constituents source is a live web page: on ANY validation failure
+  (charset, bounds 90–110, table shape) the fetch fails with an honest error — never a guessed,
+  partial, or hard-coded fallback list. The committed fixture is for TESTS and default UI, never
+  a silent runtime fallback for a failed live fetch.
+- **T-2 · Symbol normalization.** Yahoo uses dashes: `BRK.B → BRK-B`, `BF.B → BF-B`. Normalize at
+  ingestion, store the normalized form, keep the raw form in snapshot metadata. Watch dual-class
+  dupes after normalization.
+- **T-3 · Universe store ≠ dataset store.** Both are append-only JSON+index, but they are
+  DIFFERENT owners with different keys — never write universe data through `datasets.py` or
+  register screens as datasets.
+- **T-4 · Coverage reads the index.** Per-member coverage comes from `bar_index` lookups; walking
+  or re-hashing the JSON `BarStore` per page load is the 5C 31.4s mistake. GETs are cache-reads;
+  computes are explicit.
+- **T-5 · Path A or nothing.** Every new Config field: exclusion set + stability test +
+  counter-test + payload provenance, same commit. No field that shapes a SERVED value hides in an
+  env var; the pin never moves (T8 of the roadmap — no third fingerprint move exists).
+- **T-6 · Determinism means no wall-clock.** Screen `as_of` derives from the requested screen
+  date (session close), never `now()`; snapshot ids derive from content checksums; re-runs with
+  identical pins are byte-identical. Progress timestamps live in compute-manager state, never in
+  snapshot content.
+- **T-7 · Tick-evidence honesty.** A "tick evidence" badge means the symbol is among the 11
+  recorded dataset symbols — it never implies bars exist, and vice versa; the two badges are
+  independent reads (datasets vs `bar_index`).
+- **T-8 · `/structure` prefill is additive.** J-05 touches the Load form's initial values +
+  auto-Load from query params ONLY — no chart edits, no Load-flow rewrites, no default changes
+  when params are absent.
+- **T-9 · Clean rebuild before browser evidence.** `rm -rf apps/frontend/.next`, rebuild, restart
+  both processes before any browser pass — a stale build bakes the wrong API base and ghost
+  pages, producing false results in both directions.
+- **T-10 · Evidence honesty.** No screenshot ⇒ `unknown`, never `passing`; backend-only proof
+  never satisfies a browser acceptance line; the real 100-symbol top-up and real screens are
+  operator-run acts reported as such, never simulated by fixtures pretending to be live.
+- **T-10a · Native browser UI is photographed on the approved headed rig** (OWNER RATIFICATION,
+  2026-07-30). Chrome draws native `title` tooltips as a separate X window owned by the browser
+  process, so CDP screenshots — every headless capture, Playwright's included — structurally
+  cannot contain them; iterations 19–21 each failed on exactly this and the session halted
+  `STALLED` for an owner ruling. The owner's ruling is: **the screenshot requirement stands
+  unchanged**, and it is satisfied by `project-extensions/qa-rig/` (own Xvfb display, real headed
+  Chrome, real X pointer, X-level grab — see its README). A DOM read-out of the `title` string is
+  a useful cross-check but is NOT the artifact and never substitutes for it. The rig refuses to
+  write a file unless the tooltip actually rendered as a new X window AND the hovered element's
+  own `title` carries the required substring, so a rig capture cannot be a false positive.
+
+## Must-have user journeys
+
+Journeys **J-01 – J-07** form the era. **Frontend is present** (J-04, J-05, and J-07 are
+browser-verifiable). The default suite stays keyless on committed fixtures. Natural dependency
+order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding continuously.
+
+- **J-01: Universe ingestion — fetched, registered, honest**
+  - Steps:
+    1. Build the universe vendor seam + parser (contract per Key Capability 1: one documented
+       source URL as a Path-A Config field, charset check, 90–110 bounds, `BRK.B → BRK-B`
+       normalization, dedupe, sorted members) and the universe store
+       (`.data/universe/universe-<date>-<checksum12>.json`, frozen JSON + derived index).
+    2. Commit the fixture snapshot under `apps/backend/tests/fixtures/` and wire the hermetic
+       test path (env-scoped universe dir, the `TAPEOLOGY_DATASET_DIR` pattern).
+    3. Expose `POST /research/desk/universe/fetch` (explicit operator act; honest failure body on
+       validation errors) and `GET /research/desk/universe` (snapshot list + latest membership;
+       honest empty state before any registration).
+    4. Unit-test the parser contract (fixture HTML → exact member list; each validation failure →
... [diff_bound] docs/goal-archive/goal-2026-08-10.md: 1658 more diff lines omitted — Read the file for full detail
diff --git a/docs/goal.md b/docs/goal.md
index ca8e3c4..84d4ee4 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1,1964 +1,627 @@
-# Tapeology — Project Goal (Era B: The Desk — a daily screening desk over a fetched universe)
+# Tapeology — Project Goal (Era B2: The Playbook — the book's intraday setups, detected on the desk's own bars and measured forward)
 
-> Eras 1–5D are the **foundation** of this goal. Eras 1–2 (tape reading + the research evolution,
-> GOAL_ACHIEVED) are archived at [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md);
-> the structure-UI interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
+> Eras 1–5D and Era B are the **foundation** of this goal. Eras 1–2 (tape reading + the research
+> evolution, GOAL_ACHIEVED) are archived at
+> [`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md); the structure-UI
+> interlude at [`docs/goal-archive/goal-2026-07-07.md`](goal-archive/goal-2026-07-07.md);
 > **Era 5 "The Library"** at [`docs/goal-archive/goal-2026-07-14.md`](goal-archive/goal-2026-07-14.md);
-> the **"Fast Wall" performance interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
-> and the **"Clean Slate" demolition interlude (GOAL_ACHIEVED 2026-07-24, session `clean_slate`)** at
-> [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md). Eras 3, 4, 5B "The Tradable
-> Wall", and 5C "The Fast Wall" are frozen foundation; their records live in git history and in
-> `reports/goal-session-*-delivered.md`.
+> the **"Fast Wall" interlude** at [`docs/goal-archive/goal-2026-07-17.md`](goal-archive/goal-2026-07-17.md);
+> the **"Clean Slate" demolition** at [`docs/goal-archive/goal-2026-07-25.md`](goal-archive/goal-2026-07-25.md);
+> and **Era B "The Desk" (GOAL_ACHIEVED 2026-07-31, session `desk`, journeys J-01–J-21)** at
+> [`docs/goal-archive/goal-2026-08-10.md`](goal-archive/goal-2026-08-10.md). Eras 3, 4, 5B, and 5C
+> are frozen foundation; their records live in git history and `reports/goal-session-*-delivered.md`.
 >
-> **This chapter is Era B of the operator's three-era pivot (A Demolition → B Desk → C Annotator,
-> decided 2026-07-23).** Era A demolished the journal-era surfaces: the product today is exactly
-> **Cockpit (`/`) + Structure (`/structure`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP
-> surface is 15 read-only tools, and the honesty machinery (stores, gates, registry, PnL promotion
-> ledger) is fully intact. The Desk is the first BUILDING era on that cleared ground: an automated
-> **universe screener + screen ledger + daily briefing**, operated through the UI and through
-> Claude + MCP. It is an operator-directed product era OUTSIDE the research catalog
-> ([`docs/research-directions.md`](research-directions.md) has no Desk card; per its §5.6 this file
-> wins for the running era). The statistics program (era-6 "The Referee") and the AI annotation
+> **This chapter is Era B2 of the operator's pivot (A Demolition → B Desk → B2 Playbook → C
+> Annotator).** The product today is exactly **Cockpit (`/`) + Structure (`/structure`) + Desk
+> (`/desk`)**, the fingerprint epoch is `08e471b10130e1e2`, the MCP surface is **18 read-only
+> tools**, and the honesty machinery (stores, gates, registry, PnL promotion ledger) is fully
+> intact. B2 is a BUILDING era on the desk's ground: it teaches the desk the intraday setups of
+> the book the project is named for — Graifer & Schumacher, *Techniques of Tape Reading* (2004) —
+> detected on the desk's own recorded 5m/1m bars and measured with the desk's own forward-return
+> + max-drawdown conventions. It is an operator-directed product era OUTSIDE the research catalog
+> ([`docs/research-directions.md`](research-directions.md) has no Playbook card; per its §5.6 this
+> file wins for the running era). The statistics program (era-6 "The Referee") and the annotation
 > corpus (Era C) remain SEPARATE future chapters — nothing of them lands here.
 >
-> **The Desk adds ZERO new research math.** It orchestrates, persists, and surfaces the frozen
-> 5B/5C computations (tradable-map bands, level classes, bar coverage) across many symbols. Every
-> new number it serves is either read verbatim from an existing canonical owner or is a new
-> desk-owned value (rank rows, coverage rows, snapshot metadata) with exactly one new owner.
+> **Unlike Era B, this era DOES add new research math** — a family of pre-registered bar-pattern
+> detectors and their trigger-anchored measurements — under two hard disciplines: (1) every
+> detector rule and threshold is fixed in advance in
+> [`docs/playbook-detector-spec.md`](playbook-detector-spec.md) (the canonical spec; developers
+> implement from it, never re-derive or re-tune — a threshold change is a named revision that
+> re-keys future records, never a sweep); (2) every measurement reuses the desk forward rail's
+> own conventions verbatim. It adds **zero statistics gates** and **zero annotation surfaces**.
 
 ## Vision
 
-The instrument can read one symbol deeply — levels, zones, tradable bands, case studies, edge
-report — but the operator starts every day with the OPPOSITE problem: *which of the ~100 liquid
-names deserves the instrument today?* Era B builds that answer as a product:
-
-1. **A fetched, registered universe.** S&P 100 constituent membership is fetched from a documented
-   public source on explicit operator command and registered as a dated, checksummed, append-only
-   **universe snapshot** — never silently refetched, never edited, never a signal input. The suite
-   and the UI run keyless on a committed fixture snapshot; live fetch is an operator act.
-2. **An honest bar library over that universe.** A coverage view says, per member, which
-   timeframes have bars and how fresh they are — read from the durable `bar_index`, never by
-   re-hashing stores. An explicit, resumable **top-up** run fetches missing/stale series through
-   the existing keyless Yahoo seam, store-first (a symbol×timeframe already frozen in the store is
-   reused, never re-fetched).
-3. **An operator-run screen with an append-only ledger.** One button (and one CLI, and one POST)
-   walks the pinned universe snapshot as-of a screen date and summarizes, per symbol, what the
-   FROZEN tradable-map computation says: best band, band class, distance from the last daily close
-   in bps, band score, coverage and tick-evidence badges. The ranked result persists as an
-   append-only **screen snapshot** keyed by its inputs (screen date, as-of, universe snapshot,
-   `config_fingerprint`, bar-store state) — identical inputs reproduce byte-identical rows, and
-   a member with no bars appears as an honest `skipped: no bars` row, never a guess. Because every
-   row is as-of-stamped and lookahead-free, a FUTURE era can measure whether the desk's top-ranked
-   walls produced reactions — the ledger is tomorrow's evidence, not today's advice.
-4. **A briefing the operator (and Claude) actually opens.** A third page — **`/desk`** — renders
-   the latest screen as a dense, descriptive briefing with full provenance, an honest
-   "Desk screen not computed yet." empty state, a Run Screen button with live progress, browsable
-   screen history, and per-row drill-in that preloads `/structure` for that symbol and as-of.
-   Two new read-only MCP tools expose the same payloads byte-identically, so the desk can be
-   operated from a Claude conversation end to end.
-
-The deliverable: the two-page instrument becomes a three-page **desk** — universe in, briefing
-out, every number owned once, every run explicit, every record append-only and evaluable later.
+Era B gave the operator a desk: universe in, wall-screen briefing out, every record append-only
+and evaluable. But the desk still reads only structure — it knows where the walls are, not what
+the tape is DOING. The book this project is named for describes exactly that missing layer: an
+intraday grammar of price/volume behavior (six principles, a handful of named setups) that has
+never been encoded, let alone measured. Era B2 builds it as evidence, not advice:
+
+1. **A pre-registered playbook of the book's intraday setups.** For any recorded session, a
+   detector family — open-high/open-low-break, jump-base-explosion (JBE) / drop-base-implosion
+   (DBI), capitulation (+ euphoria marker), cup-and-handle, range trades, double top/bottom —
+   walks each member's RTH 5m bars (1m bars for the opening range) and emits signals:
+   `{symbol, setup_id, side, trigger price/time, invalidation_price, geometry, volume character,
+   market context, principles}`. Formation logic is lookahead-clean at bar granularity; every
+   threshold is a named constant from the canonical spec, tagged BOOK or ADAPTATION.
+2. **Every signal measured the desk's own way.** Each signal carries a trigger-anchored
+   measurement produced by the SAME conventions as the desk forward rail: horizons +1m/+5m/+1h/
+   +4h/to-close as trading-bar counts on the session's finest series, side-signed returns, dual
+   max drawdown clamped ≤ 0, truncation honesty, and a seeded random-anchor baseline of the same
+   session — plus an `invalidation_breached` disclosure (did price trade through the book's
+   structural level; returns are never stop-adjusted).
+3. **A back-scan that turns the book into a ledger.** One resumable operator act walks EVERY
+   recorded session with 5m coverage (~45 sessions × ~101 members at authoring; the store is
+   append-only so this grows daily), recording one append-only playbook record per
+   (session date, input signature) — reusing recorded work on re-run, chunked by session,
+   host-guard-confined.
+4. **An evidence view that says what happened, with n.** Per setup × side × horizon: the pooled
+   forward-return and MDD distributions of every recorded signal beside the pooled baseline
+   anchors — median/quartiles/mean, `n`, `n_truncated`, `n_baseline`, low-n tags below a named
+   disclosure floor. Descriptive distribution language only; no probability, expectancy, edge,
+   or significance claims — those gates are era-6's.
+
+The deliverable: the desk learns to read the tape the way the book teaches, writes down every
+signal it would have seen, measures what price then did against chance anchors, and shows the
+distributions honestly — every number owned once, every run explicit, every record append-only.
 
 ## Target Users
 
-- The project owner (a discretionary intraday trader) who starts the day on `/desk`: run the
-  screen, read the briefing, drill into `/structure` for the names whose walls are close.
-- The same owner operating through **Claude + MCP**: `desk_universe` / `desk_screen` (plus the
-  existing 15 tools) make the whole desk readable from a conversation.
+- The project owner (a discretionary intraday trader) who opens `/desk`, runs the playbook for a
+  session, reads the signals beside the wall briefing, and reads the evidence table to learn
+  which of the book's setups his own data supports.
+- The same owner operating through **Claude + MCP**: `desk_playbook` / `desk_playbook_evidence`
+  (plus the existing 18 tools) make the playbook readable from a conversation end to end.
 - AI dev-chain agents (the goal-mode chain) building and browser-verifying the era.
 
-## Foundation invariants (still law — eras 1–5D)
+## Foundation invariants (still law — eras 1–5D and B)
 
 The era-1–2 constitution ([`docs/goal-archive/goal-2026-07-03.md`](goal-archive/goal-2026-07-03.md))
 remains binding on all KEPT code — price-impact-over-aggression; honest uncertainty; **no
 fabricated data**; single source of truth; no magic numbers; provider-agnostic engine;
 deterministic & reproducible; no secrets in source; research read-only over the engine; record
-integrity; source/feed/`config_fingerprint` honesty. Its surface inventory is the POST-demolition
-one: `/` and `/structure` (this era adds `/desk`).
+integrity; source/feed/`config_fingerprint` honesty. The surface inventory is the post-Era-B
+one: `/`, `/structure`, and `/desk` (this era adds sections to `/desk`, no new route).
 
 1. The **tape engine** (`app/engine/`) emits byte-identical output under `default` on identical
-   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era — every new
-   `desk_*` Config field takes §0.4 **Path A** (exclusion + stability test + counter-test); a pin
-   movement is a defect, full stop.
+   inputs. `config_fingerprint` stays **`08e471b10130e1e2`** for this WHOLE era. This era needs
+   **zero new `Config` fields** (the `desk_forward` precedent: playbook thresholds are module
+   constants hashed into the record's own input signature); if the build genuinely needs one, it
+   takes §0.4 **Path A** (exclusion + stability test + counter-test) — a pin movement is a
+   defect, full stop.
 2. The **research computations** — `levels.py`, `tradability.py` (+cache), `setups.py` (+scan
-   cache), `edge_report*.py`, `backtests.py`, the strategy registry (`v1` + `structure_tape` +
-   `structure_tape_map`), `profiles.py` (`default`), the champion pointer — stay behaviorally
-   byte-identical. The desk READS them; it never re-implements, re-tunes, or re-grades.
-3. The **stores** — the JSON `BarStore` + `DatasetStore` formats, checksums, append-only
-   immutability, split freezing, the durable accelerator DBs (`bar_index`, `dataset_index`,
-   edge-report caches, setups scan cache, tradability cache) — are untouched in format and
-   discipline. Registered datasets and bar series are never deleted, re-tagged, or
-   content-perturbed. The era ADDS a universe store and a screen store under the same discipline.
-4. The **PnL promotion ledger** (`pnl_ledger.py`, `reports/pnl/pnl-history.md`, MCP `pnl_ledger`)
-   stays append-only and intact; the champion pointer does not move this era.
-5. The **kept surfaces as shipped**: the cockpit (live/sim/historical tape, `PriceChart.tsx`
-   container behaviors, panels) and `/structure` (Load flow, Tradable Map, Case Studies, Edge
-   Report + Compute button, fetch control + provenance badge) — including **both charts**
-   (`StructureChart.tsx`, `PriceChart.tsx`) — keep working exactly as shipped. The ONLY sanctioned
-   `/structure` edit is J-05's additive query-param prefill of the existing Load form.
-6. The **read-only MCP server** (`app/mcp/`) keeps its byte-identical GET-proxy contract; this era
-   adds two GET-proxy tools (15 → 17) and never adds writes.
-
-### OWNER RATIFICATION — 2026-07-27 (price-less-bar repair) — R-1
-
-**Ratified and IN INVENTORY for this era**, in addition to everything named above: the
-price-less-bar repair the chain landed in iteration 4, comprising exactly
-
-- `apps/backend/app/providers/adapters/yahoo.py` — `_is_priced_row` drops a vendor row that
-  carries no price at the fetch seam (an all-priceless window still raises `NoDataForWindow`);
-- `apps/backend/app/research/bars.py` — `BarStore.record` refuses a non-finite price before any
-  write (`NonFiniteBarPriceError`, mapped to 422), and `_merged_rows` excludes already-recorded
-  price-less **rows** on read, reporting them through the existing `integrity_errors` channel;
-- `apps/backend/app/research/routes.py` — one `except NonFiniteBarPriceError` clause on
-  `record_bar_series`, mapping the refusal to the same honest 422 the empty-window refusal already
-  uses (an added `except` + import line; no existing behavior altered);
-- `apps/frontend/components/StructureChart.tsx` — a finite-value guard on the OHLC series
-  (defence in depth);
-- `apps/backend/tests/test_structure_chart_viewport.py` — the one chart-guard assertion relaxed
-  from exact text to a pattern, to match the guarded expression above;
-- `apps/backend/tests/test_bars.py` — six ADDED tests covering the rail (write refusal per field,
-  whole-series refusal, checksum integrity of a planted price-less series, read-time row
-  exclusion + its `integrity_errors` report, append-only file untouched by exclusion, memo
-  preserved). Additions only — no existing test in this file was modified or removed;
-- `apps/backend/tests/test_yahoo_adapter.py` — five ADDED tests for the vendor-seam drop
-  (all-NaN row, real rows undisturbed, all-priceless window raises, NaN volume). Additions only;
-- `apps/backend/tests/test_bars_api.py` — one ADDED test proving the merged read never serves a
-  null-priced candle. Additions only.
-
-**Why:** the vendor genuinely serves a price-less AAPL daily row. Before the repair, one Top-up
-click persisted `NaN`-priced bars into the append-only store, which crashed `/structure`'s chart
-and silently emptied the tradable map (`compute_tradability("AAPL", as_of=2026-07-25)` returned
-`bands: []`). The repair restores honest behavior; it changes nothing for all-finite data, and the
-pinned wall still computes `resistance 300.11–302.2 class A score 171`.
-
-**Scope of the ratification, precisely:** the 60 already-affected bar series stay **on disk,
-untouched** — excluded row-by-row on read, never deleted, re-keyed, or rewritten. The pin
-`08e471b10130e1e2` does not move. `bars.py`'s file format, checksums, append-only immutability and
-split freezing are unchanged; only its write-time refusal and read-time row exclusion are new.
-This ratification does NOT open `bars.py`, `StructureChart.tsx`, `PriceChart.tsx`, or any guard
-test to further edits — anything beyond the eight files above still needs a new ratification.
-
-Where the clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
-subject to **R-1**.
+   cache), `edge_report*.py`, `backtests.py`, the strategy registry, `profiles.py` (`default`),
+   the champion pointer — stay behaviorally byte-identical. The playbook READS bars; it never
+   touches, re-implements, or re-tunes any of them.
+3. The **stores** — `BarStore` + `DatasetStore` formats, checksums, append-only immutability,
+   split freezing, the durable accelerator DBs, the Era-B universe/screen/forward stores and
+   their run ledgers — are untouched in format and discipline. The era ADDS a playbook store
+   (and its run ledgers + a derived evidence projection cache) under the same discipline.
+4. The **PnL promotion ledger** stays append-only and intact; the champion pointer does not move.
+5. The **kept surfaces as shipped**: the cockpit, `/structure`, and every shipped `/desk`
+   section (screen history calendar, forward returns, refresh chain + compute controls, ranked
+   briefing, skipped members, runs/pins/compare/provenance sections) keep working exactly as
+   shipped. The playbook lands as NEW sections below the shipped ones; no shipped `/desk`
+   section, column, or behavior changes.
+6. The **read-only MCP server** keeps its byte-identical GET-proxy contract; this era adds two
+   GET-proxy tools (**18 → 20**) and never adds writes.
+
+### OWNER RATIFICATION — carried and new
+
+**R-1 (2026-07-27, price-less-bar repair)** — ratified in Era B (see the archived goal's R-1
+block for the eight-file inventory); it remains ratified history and its terms carry forward
+unchanged.
+
+**R-2 (2026-08-10, the post-Era-B forward-test interlude) — ratified and IN INVENTORY for this
+era.** Between Era B's GOAL_ACHIEVED (iteration 36, commit `94eb1b0`) and this era's opening,
+the operator's interactive sessions landed a body of desk work no Era-B journey describes. It is
+ratified as foundation, comprising the `goal/desk` commits after `94eb1b0` through the era-open
+tip (including the operator's pre-era commit of the 2026-08-07/09 working tree — 14 modified
+files + `desk_meta_cache.py`/`test_desk_meta_cache.py`; iteration 0 records the era-open SHA):
+
+- `app/research/desk_forward.py` + `desk_forward_compute.py` + `desk_forward_log.py` +
+  `desk_forward_pins.py` — the touch-anchored forward-return v2 rail (horizons/dual-MDD/seeded
+  baseline/2-pin append-only `ForwardStore`) and its manager, ledger, and pins;
+- `app/research/desk_sessions.py` — recorded-session honesty (screen only real sessions);
+- `app/research/desk_screen_decision.py` + `desk_screen_cleanup.py` — one-snapshot-per-date
+  reuse/record/replace semantics and the operator cleanup path;
+- `app/research/desk_deep_backfill.py` — the chunked, resumable fine-bar (1m/5m) deep-backfill
+  quartet and its Alpaca vendor seam;
+- `app/research/desk_meta_cache.py` — the derived, rebuildable screen/forward meta-projection
+  cache (stat-keyed, owns nothing);
+- the desk refresh/screen/forward performance work, the ET time convention on desk surfaces, and
+  the fine-timeframe top-up walk (`DESK_TOPUP_FINE_TIMEFRAMES`).
+
+Where clauses below say "untouched", "byte-unmodified", or "out-of-inventory", they are read
+subject to **R-1** and **R-2**.
 
 ## Success Criteria
 
 In priority order — kept-value integrity outranks new-surface completeness outranks convenience:
 
-1. **Nothing kept regresses.** Full backend suite green (1169 pass / 7 skip at era open — grows,
-   never shrinks); engine equivalence proves byte-identical `default` outputs;
-   `Config().config_fingerprint()` prints `08e471b10130e1e2` in every iteration; every kept `/`
-   and `/structure` behavior browser-verified as shipped; every guard test passes unmodified
-   (subject to **R-1**).
-2. **The universe is honest.** Membership comes only from registered, dated, checksummed,
-   append-only snapshots; the parser validates (charset, count bounds, normalization) or fails
-   with an honest error — it NEVER emits a guessed or partial list; the committed fixture keeps
-   every test and default UI state keyless; live fetch happens only on explicit operator command.
-3. **The screen is deterministic and evaluable.** A screen run pins (universe snapshot id, screen
-   date, as-of, `config_fingerprint`, bar-store signature); identical pins reproduce byte-identical
-   rows; members without bars are honest `skipped` rows; snapshots are append-only and never
-   backfilled or recomputed in place; every row's structure numbers match the canonical owners
-   byte-for-byte for the same inputs.
-4. **The briefing is a real product surface.** `/desk` is the third nav row (data-driven from
-   `app/meta.py`); it renders ranked rows with descriptive chips + provenance, honest empty/
-   partial states, a Run Screen button with progress + cancel, browsable history, and drill-in
-   that lands on `/structure` preloaded — all browser-verified with screenshots.
-5. **The desk is Claude-operable.** `desk_universe` and `desk_screen` are byte-identical GET
-   proxies; `ui_route_map` lists the three routes; the MCP suite proves the 17-tool contract.
+1. **Nothing kept regresses.** Full backend suite green (1926 pass / 8 skip at authoring —
+   iteration 0 records the era-open count; grows, never shrinks); engine equivalence proves
+   byte-identical `default` outputs; `Config().config_fingerprint()` prints `08e471b10130e1e2`
+   every iteration; every kept `/`, `/structure`, and `/desk` behavior browser-verified as
+   shipped; every guard test passes extended-not-edited (subject to R-1/R-2).
+2. **Detection is pre-registered and lookahead-clean.** Every signal is a pure function of bars
+   at or before its trigger bar plus prior-session baselines, under the named constant set of
+   [`docs/playbook-detector-spec.md`](playbook-detector-spec.md); the truncation property test
+   proves it per detector; no code path anywhere iterates thresholds against outcomes.
+3. **Measurement is the desk's own.** Convention identity with the forward rail is proven by
+   test (same horizons, sign discipline, dual-MDD semantics, truncation, seed recipe); the
+   playbook embeds the rail's shape constants in its own parameters so a rail change re-keys
+   playbook records instead of silently reinterpreting them.
+4. **The ledger is append-only and evaluable.** One record per (session date, input signature);
+   identical pins reproduce byte-identical content or reuse honestly; nothing is backfilled,
+   rewritten, or recomputed in place; absences (no bars, thin baseline, no SPY) are disclosed
+   rows, never guesses.
+5. **The playbook is a real `/desk` surface.** Signals, back-scan, and evidence sections render
+   with honest empty states, live progress, and full provenance — all browser-verified with
+   screenshots (DOM-content reveals only; no journey requires native-tooltip photography).
+6. **The playbook is Claude-operable.** `desk_playbook` and `desk_playbook_evidence` are
+   byte-identical GET proxies; the MCP suite proves the 20-tool contract.
 
 ## Key Capabilities
 
-1. **Universe subsystem (new data kind, honest by construction).** A universe vendor seam (the
-   bars-vendor pattern) fetching S&P 100 membership from ONE documented public source; a parser
-   contract (ticker charset `[A-Z.-]{1,6}`, count sanity 90–110, **Yahoo normalization
-   `BRK.B → BRK-B`**, dedupe, sorted output); registration as
-   `apps/backend/.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json` (frozen JSON = source of
-   truth; any index over it is derived/rebuildable); a committed fixture snapshot under
-   `apps/backend/tests/fixtures/` for hermetic tests + default keyless UI;
-   `GET /research/desk/universe` serving snapshot list + latest membership with honest emptiness.
-2. **Coverage + top-up.** `GET /research/desk/coverage` (or a `universe` payload block): per-member
-   × per-timeframe bar presence + freshness read from `bar_index` (NEVER re-hashing the store);
-   an explicit operator-run top-up (POST + CLI) that walks members store-first through the
-   existing `POST /research/bars` fetch path, resumable, worker-capped, logging per-symbol
-   outcomes; the timeframe set = exactly what `compute_levels`/`compute_tradability` read for a
-   daily-close screen (verify at build time; era-5 contract: `4h` is resampled from `1h`, never
-   fetched; intraday microscope tfs stay per-symbol on `/structure`).
-3. **Screen compute + append-only ledger.** An operator-run screen (POST + CLI + `/desk` button)
-   over the pinned latest universe snapshot: per member, call the CANONICAL owners
-   (`compute_tradability` / levels / `bar_index`) as-of the screen date's session close and
-   summarize best band, class, distance-from-close (bps), band score, coverage + tick-evidence
-   badges; deterministic rank order = (band class A>B>C, then distance asc, then band score desc,
-   then symbol asc); single-flight + progress + cancel via the 5C compute-manager pattern;
-   persistence as append-only screen snapshots (frozen JSON + derived index) with full input pins;
-   `GET /research/desk/screen` (latest / `?date=`) + honest `"Desk screen not computed yet."`.
-4. **The `/desk` briefing page.** Third nav row; latest-screen briefing table (rank, symbol,
-   band class chip, distance chip, score, coverage/evidence badges, skipped rows grouped
-   honestly); provenance line (universe snapshot id + date, as-of, fingerprint, bar-store
-   signature); Run Screen + top-up buttons with live progress + cancel; screen history list;
-   dark/dense/terminal-grade per house style.
-5. **Drill-in + `/structure` prefill.** Clicking a briefing row navigates to
-   `/structure?symbol=<sym>&asof=<iso>`; `/structure` gains query-param PREFILL of its existing
-   Load form (prefill + auto-Load; `apps/frontend/app/structure/page.tsx` inputs at ~:2057/:2070)
-   — no other `/structure` behavior changes; the desk never recomputes structure values.
-6. **MCP contract v3 — 17 read-only tools.** Add `desk_universe` → `/research/desk/universe` and
-   `desk_screen` → `/research/desk/screen` to `_STATIC_PATHS` (`app/mcp/__init__.py:85`);
-   `get_endpoint` allowlist (`/tape/`, `/research/`, `/meta/`) already covers the new paths
-   unchanged; `tests/test_mcp_server.py` proves the 17-tool contract with byte-identity and
-   honest-error clauses.
+1. **Detector family + primitives (new research math, pre-registered).** A lean primitives
+   module (RTH session slice, opening range with `1m→5m` honest degradation, prior-20-session
+   MBR + per-slot volume medians, strict swing pivots, consolidation-range finder, vertical-move
+   detector, zone touches, market context) and the nine detectors + euphoria marker of the
+   canonical spec — all thresholds from the spec's single constants table, every vagueness in
+   the book resolved as ONE named, cited adaptation.
+2. **Trigger-anchored measurement on the desk's rail.** Signals measured by the forward rail's
+   own `_measure_from` at the trigger bar on the session's finest series; per-signal
+   `invalidation_breached` computed in the same pass OUTSIDE the rail helper; per (symbol,
+   setup) seeded baseline anchors with the rail's seed discipline; caps + beyond-cap disclosure.
+3. **One compute, one store.** `compute_playbook(session_date)` detects + measures in one walk
+   and records ONE frozen, checksummed, append-only record keyed
+   `(session_date, playbook_input_signature)` — the signature hashes the fine-series tuples of
+   members ∪ {SPY}, the `config_fingerprint`, and the FULL parameters blob (thresholds, setup
+   list, measurement shape), so a logic change mints new versions and can never silently reuse
+   or rewrite old ones. Compute manager trio + CLI + durable run ledger per the desk pattern;
+   `refuse_if_not_a_session` guards every compute path.
+4. **The back-scan.** `GET .../backscan/plan` (pure, metadata-only: recorded session dates ×
+   recorded-at-current-signature) and a resumable compute trio walking planned dates through the
+   ONE shared `run_playbook_and_record` entry point — per-date outcomes
+   `reused/recorded/refused_non_session/failed`, cancel on a date boundary, durable back-scan
+   ledger, host-guard-confined.
+5. **The evidence view.** `GET /research/desk/playbook/evidence` folds the newest record per
+   date AT ONE SIGNATURE into per-(setup, side) × measure distribution cells (median/p25/p75/
+   mean, `n`, `n_truncated`, `n_baseline`, `below_min_n` tags, `invalidation_breached` counts)
+   beside the pooled baseline — computed on read via a stat-keyed derived projection cache
+   (the meta-cache contract), never a snapshot store; other signatures listed, never pooled.
+6. **`/desk` playbook sections + MCP contract v4 (20 tools).** Playbook Signals (per-session
+   signal table + Run Playbook + provenance), Backscan (plan preview + trigger + progress +
+   runs), Playbook Evidence (the distribution table) — rendered BELOW the shipped sections;
+   `desk_playbook` + `desk_playbook_evidence` in `_STATIC_PATHS`; `get_endpoint`'s `/research/`
+   allowlist already reaches the parameterized reads.
 
 ## Non-Goals
 
-- **No statistics program.** No new gates, CIs, nulls, multiple-testing control, or promotion
-  logic — that is era-6 "The Referee" (future). The screen RANKS by existing descriptive
-  structure metrics; it never claims edge, probability, or expectancy.
-- **No annotation layer.** Human/AI pattern annotation, dispositions, notes, or any manual input
-  path on desk records is Era C "The Annotator" (designed separately). This era's ledger records
-  MACHINE output only.
-- **No strategy/champion work.** No new strategies/profiles, no backtest changes, no champion
-  movement, no PnL-ledger rows beyond what existing machinery already writes.
-- **No scheduling.** No cron, daemon, auto-refresh, or market-hours trigger — every fetch,
-  top-up, and screen run is an explicit operator act (UI button / CLI / POST).
-- **No tick-data expansion.** No new dataset recording, no credential work; tick evidence badges
-  reflect the 11 recorded dataset symbols as they stand.
-- **No engine, chart, or kept-surface work.** `app/engine/` untouched; `StructureChart.tsx`
... [diff_bound] docs/goal.md: 2242 more diff lines omitted — Read the file for full detail
diff --git a/docs/playbook-detector-spec.md b/docs/playbook-detector-spec.md
new file mode 100644
index 0000000..0414a6f
--- /dev/null
+++ b/docs/playbook-detector-spec.md
@@ -0,0 +1,361 @@
+# The Playbook — detector specification (Era B2)
+
+Canonical formation/trigger/stop definitions for the intraday setups of Graifer & Schumacher,
+*Techniques of Tape Reading* (McGraw-Hill, 2004), adapted to 5-minute OHLCV bars over the desk
+universe. **This file is the single source of the detector rules and the pre-registered constant
+set.** Goal-mode developers implement from here; they never re-derive, re-name, or re-tune a
+threshold. Every constant is tagged **BOOK** (the book's own number) or **ADAPTATION** (a single
+named choice where the book is vague — the tag records the book basis and the rationale).
+Changing any constant is a **named revision**: the new value lands in code, re-keys every future
+record through the parameters signature, and never touches a recorded file. Threshold sweeps are
+banned outright (`docs/research-directions.md` DO-NOT #5).
+
+Target modules (desk family naming): `app/research/desk_playbook_features.py` (primitives),
+`app/research/desk_playbook_detect.py` (detectors), `app/research/desk_playbook.py`
+(constants + parameters + signature + store + walker). Bars are read through
+`BarStore.merged_bars(symbol, timeframe)` (`app/research/bars.py:883`) only.
+
+---
+
+## 0. Shared conventions (binding on every detector)
+
+**Bars and session.** The detection series is the symbol's 5m bars for the session date,
+extracted with the `_session_slice` semantics (`app/research/desk_forward.py:295`) and then
+filtered to regular trading hours: ET 09:30 ≤ bar open < 16:00. `slot(bar)` = index in the RTH
+5m sequence (0..77 on a full day; fewer on half-days — `session_bar_count` is disclosed on every
+signal). 1m bars are read by the opening-range builder only.
+
+**MBR — the scale unit.** `MBR` = median(high − low) over all RTH 5m bars of the prior
+`PLAYBOOK_BASELINE_SESSIONS` sessions of the same symbol. One number per symbol-session,
+entry-time legal by construction (prior sessions only). Every price-distance threshold below is
+an MBR multiple. This is the deliberate ADAPTATION replacing the book's absolute-cents scale
+(2002–04 Nasdaq: "25 cents" on ~$20 stocks ≈ 1.25%); modern S&P100 5m bars are calmer, so
+relative-to-recent-range beats a fixed percent. `MBR = 0` or fewer than
+`PLAYBOOK_MIN_BASELINE_SESSIONS` prior sessions ⇒ the symbol-session emits **no signals**
+(fail-closed, disclosed as an honest absence row).
+
+**RVOL — the one relative-volume definition.** `RVOL(bar) = bar.volume / median(volume of the
+same RTH slot over the prior PLAYBOOK_BASELINE_SESSIONS sessions)`, requiring at least
+`PLAYBOOK_MIN_BASELINE_SESSIONS` observations of that slot, else RVOL is null and any condition
+needing it fails closed. This is `docs/research-directions.md` Card 5.5's `rvol_m` formula at 5m
+granularity. Every volume condition in every detector is expressed on this RVOL — no second
+volume normalization exists anywhere in the playbook.
+
+**Entry convention — modeled stop-through fill.** Every playbook entry models a stop order
+electing at the trigger price `T`: long `entry = max(trigger_bar.open, T)`, short
+`entry = min(trigger_bar.open, T)`. `entry_kind = "level"` when the bar opened on the near side
+of `T`, `"gap_open"` when it opened beyond. This is a named ADAPTATION of the wall rail's
+resting-limit convention (`desk_forward.py` support `min(open, price_high)`): a limit-at-edge
+model would systematically credit breakout fills better than achievable. The trigger band served
+to the measurement is `(T, T·(1+PLAYBOOK_MAX_CHASE_FRAC))` for longs, mirrored for shorts —
+the band width is BOOK (the 3–5-cent no-chase rule ≈ 0.2% of price). A trigger bar opening
+beyond the band still fires, with `gapped_beyond_chase: true` (the book would skip; we record
+and flag rather than suppress — suppression would hide exactly the fills the rule warns about).
+
+**Measurement.** Each signal is measured with the desk's existing conventions by calling
+`_measure_from(session_bars, anchor_index, entry, entry_kind, tf_minutes, sign)`
+(`desk_forward.py:451`) on the finest series the session holds (1m when present, else 5m; the
+5m→1m anchor mapping takes the first 1m bar of the trigger 5m window whose [low, high] contains
+`T`, falling back to the window's first 1m bar). `sign = +1` long / `−1` short, passed
+explicitly. Horizons, measures, dual MDD, truncation honesty, and the seeded random-anchor
+baseline are the rail's, unchanged.
+
+**Lookahead law (the one argument, holding for all detectors).** Formation conditions read bars
+`[session start .. t−1]` only — including pivot-confirmation delay: a swing pivot is not known
+until `PLAYBOOK_PIVOT_LOOKBACK_BARS` bars after its center (the `levels.py:_swing_pivots` strict
+rule, `app/research/levels.py:325`), and if price crosses the would-be trigger before the
+defining pivot is confirmed, no signal fires (fail-closed). The trigger predicate at bar `t`
+uses ONLY the price-crossing fact (`high > T` / `low < T`) — knowable at the moment it happens
+intrabar. Every other bar-`t` quantity (close, range, volume, RVOL) appears **only in
+disclosures, never in gates** — gating a fill on the trigger bar's own completed volume is
+lookahead-at-fill and is banned. Baselines (MBR, RVOL denominators) are prior-sessions-only.
+Market context reads index bars strictly before the trigger bar's epoch.
+
+**Break strictness.** A break is strict (`high > U`, `low < L`). Equality is a touch, never a
+break (mirrors `_swing_pivots`' tie discipline).
+
+**Invalidation level (the book's stop).** Every signal carries `invalidation_price` — the
+book's structure rule (under/over the structure whose break kills the thesis) padded by
+`PLAYBOOK_STOP_PAD_FRAC` of the nominal distance: long `S − PAD·(T − S)`, short mirrored,
+where `S` is the structural level (base low, handle bottom, leg low, range extreme, pattern
+top). BOOK: the book pads obvious stops by ~20–40% of nominal distance; the midpoint 0.30 is
+pre-registered. `invalidation_price` is a **disclosure level** — the rail never simulates
+stop-outs; the served register states returns are not stop-adjusted. A same-pass
+`invalidation_breached` block (per-horizon boolean + `first_breach_minutes`) is computed
+OUTSIDE `_measure_from` (so the rail's shape never changes) — a boolean fact, never an exit
+model.
+
+**Market context (disclosure, never a gate).** Index = SPY 5m bars (already frozen in the
+store; `market_direction.source: "SPY"`). `market_move` = (idx close[t−1] − idx
+close[t−1−PLAYBOOK_MKT_LOOKBACK_BARS]) in index-MBR units. Alignment: `supportive` when signed
+with the signal beyond `PLAYBOOK_MKT_NEUTRAL_BAND_MBR`; `against` when signed opposite beyond
+the band; else `neutral`. `book_would_skip_market: true` when `against` (Trader's Action step 5
+— the book skips; we disclose). Relative-strength disclosure (Ch 13 narrow-range rule):
+`relative_strength_strong: true` when the stock's last pre-trigger close is within
+`PLAYBOOK_NEAR_EXTREME_MBR` of its session high while SPY's last close is within the same
+tolerance (index-MBR) of its session low — mirrored for shorts. No SPY bars for the session ⇒
+`market_direction: null` + reason (honest absence, never a crash).
+
+**Volume-into-trigger discriminator (Part Three, Example 3 — shared, defined once).** Over the
+`PLAYBOOK_APPROACH_BARS` bars strictly before the trigger bar:
+- `exhausted_spike` — some approach bar has `RVOL ≥ PLAYBOOK_RVOL_SURGE` AND its high is within
+  `PLAYBOOK_NEAR_EXTREME_MBR · MBR` of `T` AND it failed to close beyond `T` (volume spent AT
+  the level without eating it — the book says do NOT buy this break);
+- `constructive` — approach RVOLs non-decreasing and none ≥ SURGE (steady climb/base; the
+  spike, if any, lands on the trigger bar itself, disclosed post-hoc via `rvol_trigger_bar`);
+- `neutral` — otherwise.
+Disclosure only, never a gate.
+
+**Shared disclosure block on every signal:** `rvol_trigger_bar` (post-hoc),
+`approach_rvol_max`, `spike_into_trigger_verdict` (the discriminator), `spiky_approach`
+(single-bar vertical into the level), the market block, `attempt_count` at `T` (pre-trigger
+zone touches of `[T − NEAR_EXTREME·MBR, T]` with the re-arm rule — the book's 2nd/3rd-attempt
+rule as data), `bars_to_close`, `concurrent_signals` (other detector ids sharing the trigger
+bar), `euphoria_recent`/`capitulation_recent` (marker within `PLAYBOOK_MARKER_DECAY_BARS`),
+`gapped_beyond_chase`, `session_bar_count`, `opening_range_basis` where relevant, and
+`principles` — which of the book's six Ch-9 principles the formation exemplifies
+(P1 euphoria/capitulation, P2 trend beginning, P3 trend confirmation, P4 shallow-retracement
+continuation, P5 decreasing-volume reversal, P6 passive accumulation/distribution).
+
+---
+
+## 1. Pre-registered constants (the COMPLETE tunable surface — nothing else exists)
+
+| Constant | Value | Source |
+|---|---|---|
+| `PLAYBOOK_BASELINE_SESSIONS` | 20 | ADAPTATION — Card 5.5's RVOL convention |
+| `PLAYBOOK_MIN_BASELINE_SESSIONS` | 10 | ADAPTATION — minimum honest median |
+| `PLAYBOOK_RVOL_SURGE` | 2.0 | ADAPTATION — book's "volume surge / pace pickup" unquantified |
+| `PLAYBOOK_RVOL_ELEVATED` | 1.5 | ADAPTATION — Card 5.5 high-RVOL bucket boundary |
+| `PLAYBOOK_RVOL_DRYUP` | 0.7 | ADAPTATION — Card 5.5 low-RVOL bucket boundary |
+| `PLAYBOOK_VOL_CONTRAST_RATIO` | 0.6 | ADAPTATION — mechanical "dries on pullback vs advance" |
+| `PLAYBOOK_MAX_CHASE_FRAC` | 0.002 | BOOK — 3–5c chase on ~$20 ≈ 0.2% |
+| `PLAYBOOK_STOP_PAD_FRAC` | 0.30 | BOOK — 20–40% stop padding; midpoint |
+| `PLAYBOOK_OR_MINUTES` | 15 | BOOK — opening range = first 15–20 min; lower endpoint |
+| `PLAYBOOK_NARROW_OR_MAX_MBR` | 3.0 | ADAPTATION — relative form of the ≤25c narrow range |
+| `PLAYBOOK_JUMP_MIN_MULT` | 1.5 | BOOK — jump ≥ 1.5–2× base; stated minimum |
+| `PLAYBOOK_JUMP_MIN_MOVE_MBR` | 3.0 | ADAPTATION — floor so tiny/tiny can't satisfy the ratio |
+| `PLAYBOOK_JUMP_LOOKBACK_BARS` | 6 | ADAPTATION — jump low read from the 30 min before the base |
+| `PLAYBOOK_BASE_MIN_BARS` | 3 | ADAPTATION — book gives no consolidation duration |
+| `PLAYBOOK_BASE_MAX_BARS` | 12 | ADAPTATION — 60-min cap; beyond it the "base" is the day's range |
+| `PLAYBOOK_BASE_MAX_RANGE_MBR` | 2.0 | ADAPTATION — relative form of the ≤25c narrow base |
+| `PLAYBOOK_NEAR_EXTREME_MBR` | 1.0 | ADAPTATION — mechanical "near the high/low" |
+| `PLAYBOOK_PIVOT_LOOKBACK_BARS` | 3 | ADAPTATION — 5m intraday N for the strict-pivot rule |
+| `PLAYBOOK_CUP_MIN_BARS` | 6 | BOOK — cup ≥ 30 min |
+| `PLAYBOOK_CUP_OPTIMAL_BARS` | 12 | BOOK — ≥ 1 h optimal (disclosure only) |
+| `PLAYBOOK_HANDLE_MAX_RETRACE_FRAC` | 0.5 | BOOK — handle ≤ 50% of cup depth |
+| `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` | 0.30 | BOOK — handle ≤ 30% of cup duration (25% desirable → disclosure) |
+| `PLAYBOOK_RIM_MATCH_MBR` | 1.0 | ADAPTATION — "cup edges at the day's high" tolerance |
+| `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR` | 2.0 | ADAPTATION — min cup depth AND min valley depth |
+| `PLAYBOOK_VERTICAL_WINDOW_BARS` | 3 | ADAPTATION — "near-vertical" window (15 min) |
+| `PLAYBOOK_VERTICAL_MOVE_MBR` | 4.0 | ADAPTATION — net move for capitulation/euphoria |
+| `PLAYBOOK_VERTICAL_BAR_MBR` | 2.5 | ADAPTATION — single-bar spike (spiky-approach flag) |
+| `PLAYBOOK_BOUNCE_MAX_BARS` | 3 | ADAPTATION — reversal confirmation must come fast |
+| `PLAYBOOK_RANGE_MIN_WIDTH_MBR` | 4.0 | ADAPTATION — narrower = breakout-only per Ch 13 |
+| `PLAYBOOK_RANGE_HOLD_TOL_MBR` | 0.5 | ADAPTATION — "held" tolerance; also the absorption-bar max range |
+| `PLAYBOOK_TOPS_MATCH_MBR` | 1.0 | ADAPTATION — two tops "at the same level" |
+| `PLAYBOOK_TOPS_MIN_SEPARATION_BARS` | 4 | ADAPTATION — tops ≥ 20 min apart |
+| `PLAYBOOK_LADDER_HEALTHY_LOW` / `_HIGH` | 0.50 / 0.75 | BOOK — ladder step 50–75% of prior step (disclosure only) |
+| `PLAYBOOK_MKT_LOOKBACK_BARS` | 6 | ADAPTATION — 30-min index-direction window |
+| `PLAYBOOK_MKT_NEUTRAL_BAND_MBR` | 1.0 | ADAPTATION — neutral band, index-MBR units |
+| `PLAYBOOK_MARKER_DECAY_BARS` | 6 | ADAPTATION — euphoria/capitulation marker decorates for 30 min |
+| `PLAYBOOK_APPROACH_BARS` | 3 | ADAPTATION — volume-into-trigger window |
+| `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` | 2 | ADAPTATION — ladder steps; every other detector caps at 1 (per side where sided) |
+
+Companion structural constants (shape, not thresholds): `PLAYBOOK_SETUPS` (the setup-id tuple),
+`PLAYBOOK_MARKET_SYMBOL = "SPY"`, `PLAYBOOK_BASELINE_SEED = DESK_FORWARD_BASELINE_SEED`,
+`PLAYBOOK_RETURN_SIGN_CONVENTION = "side_relative"`, `PLAYBOOK_SIGNAL_MEASURES`,
+`PLAYBOOK_MIN_N_DISCLOSURE = 12` (evidence low-n tag — a disclosure floor, never a gate).
+All of the above are embedded in `playbook_parameters()` and hashed into
+`playbook_input_signature` (the `forward_parameters()` pattern, `desk_forward.py:225`).
+
+---
+
+## 2. Shared primitives (`desk_playbook_features.py` — eight functions, nothing more)
+
+1. `rth_session_slice(bars_5m, session_date)` — `_session_slice` semantics + RTH filter,
+   slots attached. (Attribution comment to `desk_forward._session_slice`.)
+2. `opening_range(bars_1m, session_date, minutes)` — `{high, low, width, basis: "1m"|"5m",
+   bars_used}` over ET 09:30–09:45; fewer than 10 of the 15 one-minute bars on file ⇒ fall back
+   to the first 3 five-minute bars with `basis: "5m"`; neither ⇒ null (fail-closed, disclosed).
+3. `baselines(symbol, session_date)` — one pass over the prior 20 sessions' RTH 5m bars
+   returning `MBR` + the per-slot volume-median vector (the RVOL denominators). The only
+   baseline builder.
+4. `swing_pivots(bars, lookback)` — the `levels.py:_swing_pivots` strict-extreme rule (strictly
+   greater/less than all ±N neighbours; ties are not pivots; series ends unconfirmable). The
+   confirmation delay IS the lookahead guard.
+5. `consolidation_range(bars, end_idx, min_bars, max_bars, max_range)` — the maximal window
+   ending at `end_idx` with `max(high) − min(low) ≤ max_range`; returns `(start_idx, U, L)` or
+   null. Shared geometry for JBE/DBI base, handle, flatline.
+6. `vertical_move(bars, end_idx, n, k, direction, require_volume)` — net move over the last `n`
+   bars ≥ `k·MBR` in `direction`, ≥ `n−1` of `n` closes in that direction; with
+   `require_volume`: `RVOL(last) ≥ PLAYBOOK_RVOL_SURGE` and ≥ `RVOL(first)` (rising). Powers
+   capitulation/euphoria and (n=1, k=`PLAYBOOK_VERTICAL_BAR_MBR`, no volume clause) the
+   spiky-approach flag.
+7. `zone_touches(bars, lo, hi)` — overlap + full-exit-re-arm semantics (attribution to
+   `desk_forward._touch_scan`); powers attempt counts, tested-twice-and-held, second-top
+   support.
+8. `market_context(index_bars_5m, session_date, before_epoch)` — §0's market block.
+
+---
+
+## 3. Detectors
+
+Format per detector: formation → trigger → invalidation → caps → extra disclosures → edge
+cases. Side/band/entry/measurement always follow §0.
+
+### 3.1 `open_high_break` / 3.2 `open_low_break`
+- **Formation.** OR per primitive 2 (`PLAYBOOK_OR_MINUTES` BOOK). Narrowness gate:
+  `or_width ≤ PLAYBOOK_NARROW_OR_MAX_MBR · MBR` (ADAPTATION for the book's ≤25c). Eligible
+  trigger bars: 5m slots ≥ 3 (the OR occupies slots 0–2).
+- **Trigger.** First 5m bar with `high > or_high` ⇒ `open_high_break`, `T = or_high`, long;
+  or `low < or_low` ⇒ `open_low_break`, `T = or_low`, short. First break wins; **one
+  opening-range signal per symbol-session total.** A bar strictly breaking BOTH sides with
+  neither previously broken ⇒ no signal; `ambiguous_outside_bar` recorded as a formation
+  diagnostic.
+- **Invalidation.** Long: `S = or_low`, `invalidation = or_low − 0.30·(or_high − or_low)`
+  (BOOK structure + BOOK pad). Short mirrored.
+- **Disclosures.** `or_width_mbr`, `or_bars_used`, `opening_range_basis`,
+  `open_vs_prior_close_pct` (gap context), `slots_to_break`. Principles: P4 when pre-break
+  pullbacks were shallow and dry, else structural-only.
+- **Edge cases.** `gap_open` triggers at slot 3 are common on trend opens —
+  `gapped_beyond_chase` does the honesty work. No 1m and no 5m OR ⇒ silent symbol-session
+  (disclosed absence).
+
+### 3.3 `jbe` / 3.4 `dbi` (exact mirror; JBE described)
+- **Formation** (windows ending at `t−1`): base = `consolidation_range` with
+  `PLAYBOOK_BASE_MIN_BARS ≤ len ≤ PLAYBOOK_BASE_MAX_BARS` and
+  `base_range = U − L ≤ PLAYBOOK_BASE_MAX_RANGE_MBR · MBR` (ADAPTATION). Jump: `jump_low` =
+  min low of the `PLAYBOOK_JUMP_LOOKBACK_BARS` bars before base start; `jump = U − jump_low`;
+  gates `jump ≥ PLAYBOOK_JUMP_MIN_MULT · base_range` (BOOK ≥1.5×) AND
+  `jump ≥ PLAYBOOK_JUMP_MIN_MOVE_MBR · MBR` (ADAPTATION floor). Near the high:
+  `U ≥ session_high_so_far − PLAYBOOK_NEAR_EXTREME_MBR · MBR` at `t−1`. Volume: median
+  RVOL(jump bars) ≥ 1.0 with max ≥ `PLAYBOOK_RVOL_ELEVATED` (P3), and median RVOL(base bars)
+  ≤ `PLAYBOOK_VOL_CONTRAST_RATIO` × median RVOL(jump bars) (P4 dry base; ADAPTATION ratio).
+- **Trigger.** First bar `t` with `high > U`. `T = U`.
+- **Invalidation.** `S = L`; `L − 0.30·(U − L)` (BOOK: under the range's lower limit, padded).
+- **Caps.** ≤ `PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION` (2) per side — ladder steps; a second
+  base must start after the first trigger bar.
+- **Disclosures.** `jump_mbr`, `base_range_mbr`, `base_bars`, `base_flatline` (base range
+  ≤ 1.0·MBR — the flatline-at-the-high variation), `base_lows_ascending` (the
+  ascending-triangle variation), `ladder_step_ratio` vs `PLAYBOOK_LADDER_HEALTHY_LOW/_HIGH`
+  (BOOK: <0.50 trend exhausting, >0.75 break likely fails). Principles: P3 + P4.
+- **Edge cases.** A base still open at session close emits nothing.
+
+### 3.5 `capitulation` (entry) + `euphoria` (marker only)
+- **Formation.** `vertical_move` DOWN ending at climax bar `v`: net decline ≥
+  `PLAYBOOK_VERTICAL_MOVE_MBR · MBR` over `PLAYBOOK_VERTICAL_WINDOW_BARS` bars, ≥ n−1 down
+  closes, `RVOL(v) ≥ PLAYBOOK_RVOL_SURGE` and rising (all ADAPTATION — the book's "fast sharp
+  vertical decline + volume/pace pickup" is unquantified). `leg_low` = min low through `t−1`;
+  a new low after `v` re-anchors `v` (the panic still running).
+- **Trigger.** First bar `t` with `t − v ≤ PLAYBOOK_BOUNCE_MAX_BARS` and `high > high[t−1]`
+  (first-strength reversal bar). `T = high[t−1]` — fully known at `t−1`; the crossing is the
+  only bar-`t` fact. No trigger within the window ⇒ formation expires.
+- **Invalidation.** `S = leg_low`; `leg_low − 0.30·(T − leg_low)` (BOOK: under the bounce low;
+  "any new low should be considered trade failure").
+- **Caps.** 1 per symbol-session (first).
+- **Disclosures.** `decline_mbr`, `decline_bars`, `climax_rvol`,
+  `bars_from_climax_to_trigger`. Principle: P1.
+- **`euphoria`** — exact mirror UP with the same constants, emitted as a **marker, not a
+  signal**: no side, no band, never measured (BOOK: an exit/avoid signal; the authors do not
+  short strong stocks on euphoria). It sets `euphoria_recent: true` on any signal triggering
+  within `PLAYBOOK_MARKER_DECAY_BARS`; capitulation events symmetrically set
+  `capitulation_recent`.
+
+### 3.6 `cup_handle` (long only in v1 — the book presents the long form)
+- **Formation.** Left rim = confirmed swing-high pivot within `PLAYBOOK_RIM_MATCH_MBR · MBR`
+  of session-high-so-far. Cup bottom = min low after it; depth ≥
+  `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR · MBR` (ADAPTATION). Right rim = later confirmed
+  swing-high pivot within `RIM_MATCH` of the left rim, itself near the session high. Cup
+  duration ≥ `PLAYBOOK_CUP_MIN_BARS` (BOOK ≥ 30 min; ≥ `PLAYBOOK_CUP_OPTIMAL_BARS` disclosed
+  as `cup_optimal`). Cup volume (BOOK shape, ADAPTATION ratio): median RVOL of the middle
+  third of cup bars ≤ `PLAYBOOK_VOL_CONTRAST_RATIO` × median RVOL of the outer thirds (dry at
+  the bottom, alive at the edges). Handle: bars after the right rim with min low ≥
+  `rim − PLAYBOOK_HANDLE_MAX_RETRACE_FRAC · cup_depth` (BOOK ≤ 50%), duration ≤
+  `PLAYBOOK_HANDLE_MAX_DURATION_FRAC` × cup duration (BOOK ≤ 30%; ≤ 25% flagged
+  `handle_duration_desirable`), median RVOL(handle) ≤ contrast × outer-third median (BOOK dry
+  handle).
+- **Trigger.** First bar after ≥ 1 handle bar with `high > T`,
+  `T = max(left_rim_high, right_rim_high)` (BOOK: break of the rim). Both rims
+  pivot-confirmed strictly before `t`.
+- **Invalidation.** `S = handle_bottom`; `S − 0.30·(T − S)` (BOOK: below the handle bottom).
+- **Caps.** 1 per symbol-session.
+- **Disclosures.** `cup_bars`, `cup_depth_mbr`, `handle_retrace_frac`,
+  `handle_duration_frac`, `cup_optimal`, the three RVOL medians. Principles: P4 + P5-inverse.
+- **Edge cases.** A handle dipping below 50% of cup depth voids the formation (it is now a
+  range or a double top — detectors are independent hypotheses and both may evaluate). A
+  handle still open at close emits nothing.
+
+### 3.7 `range_trade` (support-bounce long + resistance-fade short) — PROVISIONAL TIER
+- **Arming (BOOK: "test the low and high twice and hold").** At `t−1`: session range
+  `SH − SL ≥ PLAYBOOK_RANGE_MIN_WIDTH_MBR · MBR` (ADAPTATION — narrower is breakout-only per
+  Ch 13); high zone `[SH − NEAR_EXTREME·MBR, SH]` and low zone `[SL, SL + NEAR_EXTREME·MBR]`
+  each with `zone_touches ≥ 2` (re-arm semantics), each later touch extending the extreme by
+  ≤ `PLAYBOOK_RANGE_HOLD_TOL_MBR · MBR` ("held").
+- **Trigger — the mechanical reading of "first sign of strength" (the book's vaguest
+  instruction; this reading is the pre-registered choice):** a bar `b` touches the low zone;
+  the first bar `t` with `b < t ≤ b + PLAYBOOK_BOUNCE_MAX_BARS`, `high > high[t−1]`, and
+  `min(low[b..t−1]) ≥ SL − RANGE_HOLD_TOL·MBR`. `T = high[t−1]` — the same reversal-bar
+  grammar as the capitulation bounce (one shared mechanism, not a second vague one).
+  Resistance-fade mirrored.
+- **Invalidation.** Long `S = SL`, `SL − 0.30·(T − SL)` (BOOK: just outside the range
+  bounds). Short mirrored.
+- **Caps.** 1 per side per symbol-session.
+- **Disclosures.** `range_width_mbr`, per-zone touch counts, `crossed_midrange` on the
+  approach + whether the prior swing turned at midrange (BOOK midrange rule),
+  `absorption_bar_present` — a zone bar with `RVOL ≥ PLAYBOOK_RVOL_ELEVATED` and range ≤
+  `RANGE_HOLD_TOL·MBR` (P6 passive accumulation/distribution, mechanical ADAPTATION).
+  Principles: P6 when absorption present; P5 at the high side.
+- **Edge cases.** A strict break beyond a zone by > `HOLD_TOL` dissolves range-mode (re-arms
+  only on a new twice-tested range).
+- **Provisional status.** First candidate for removal in a named revision if its forward
+  distributions do not separate from the random-anchor baseline.
+
+### 3.8 `double_top` / 3.9 `double_bottom` (mirror; double_top described)
+- **Formation.** Two confirmed swing-high pivots `p1 < p2` with
+  `|high(p1) − high(p2)| ≤ PLAYBOOK_TOPS_MATCH_MBR · MBR`, separation ≥
+  `PLAYBOOK_TOPS_MIN_SEPARATION_BARS`, both within `NEAR_EXTREME·MBR` of the session high at
+  their times (all ADAPTATION). Valley = min low strictly between them; depth ≥
+  `PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR · MBR`.
+- **Trigger.** First bar `t` with `low < valley_low`, `p2` pivot-confirmed strictly before
+  `t` (fail-closed if price collapses through the valley inside `p2`'s confirmation window).
+  `T = valley_low`, short. **Never triggered at the second top itself** — BOOK: short the
+  valley break, never the retest.
+- **Invalidation.** `S = max(high(p1), high(p2))`; `S + 0.30·(S − T)` (BOOK: above the top).
+  Nominal risk is the full pattern height — disclosed as `nominal_risk_mbr`, never shrunk.
+- **Caps.** 1 per detector per symbol-session (the first valid valley break; a triple top
+  cannot re-fire the same valley).
+- **Disclosures.** `tops_gap_mbr`, `tops_separation_bars`, `valley_depth_mbr`,
+  `second_top_rvol_vs_first` (median RVOL of p2±1 / p1±1 — P5's drying retest, disclosed not
+  gated), `attempt_count` (≥ 3 attempts before the valley break is the book's
+  third-attempt-succeeds warning, as data). Principles: P5; the attempt rule.
+- **Edge cases.** `p2` exceeding `p1` by more than `TOPS_MATCH` ⇒ not a double top (possibly
+  a JBE base — independent detectors).
+
+---
+
+## 4. Shared degenerate/edge policy
+
+- **Formation open at session end** ⇒ nothing emitted. Signals only; no "armed" rows in v1.
+- **Halted/missing bars**: a timestamp discontinuity > 5 minutes inside a formation window
+  voids that formation (`halted_formation` diagnostic, ADAPTATION). Missing baseline slots
+  fall out of the medians under the `MIN_BASELINE_SESSIONS` floor.
+- **Late triggers** are never suppressed — the rail's truncation honesty (`truncated`,
+  `effective_minutes`) covers short runways; `bars_to_close` disclosed.
+- **Overlapping setups on the same bars** are allowed — independent hypotheses;
+  `concurrent_signals` cross-lists them so analysis can de-duplicate downstream.
+- **Thin data** (MBR = 0, null RVOL baseline, < 10 baseline sessions, no 5m bars) ⇒ the
+  symbol-session is silent with a disclosed absence, never a guess.
+
+## 5. Expected frequency (~101 members × 78 bars/session; validated on real data by the
+back-scan — validation may DEMOTE a detector in a named revision, never tune constants)
+
+| Detector | Est. signals/day (universe) | Note |
+|---|---|---|
+| `open_high_break` / `open_low_break` | 10–25 | Most frequent; simplest lookahead story — build first |
+| `jbe` / `dbi` | 5–15 | The workhorse |
+| `range_trade` | 5–20 | Provisional tier (vaguest book rule) |
+| `double_top` / `double_bottom` | 5–15 | Pivot-confirmation delay drops fast collapses (fail-closed, honest) |
+| `capitulation` | 0–3 | Rare on calm S&P100 5m; clusters on news days — low n expected, disclosed |
+| `euphoria` (marker) | 0–3 | Marker only, never measured |
+| `cup_handle` | 0–2 | Rarest; exercises every primitive |
```
