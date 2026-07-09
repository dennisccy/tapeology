# Goal Iteration 3 — Store-first quick reuse via a derived SQLite bar index (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **The SQLite index is a derived cache, never a source of truth.** Canonical bars stay the append-only, checksummed JSON `BarStore`; every served candle is checksum-verified from it; the index holds metadata only, is rebuildable via `reindex()`, and its loss or corruption loses and fabricates nothing. A second authoritative bar store is a defect. *(critical)*
  - **Fetching is explicit and store-first.** Historical data is fetched only on an explicit user action; an already-stored window is served from storage without re-hitting Yahoo; there is no ambient or background polling. *(critical)*
  - **Yahoo data is fetched-and-stored only, never re-tagged or pooled across feeds.** A `feed="yahoo"` series is append-only and checksummed; it is never merged with, re-tagged to, or analytically pooled with `sip` or any other feed. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index.
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*

## GOAL

A repeat fetch of an already-stored `(symbol, timeframe, window)` is served from storage instantly with **no** second Yahoo call, and `GET /research/bars?symbol=&timeframe=` returns just that series via a derived SQLite index — while the canonical JSON `BarStore` stays the one source of truth and the no-param `GET /research/bars` response is byte-identical to before.

## BACKGROUND

J-03 is the next unblocker in the goal's stated dependency chain `J-01 → J-02 → J-03 → J-04 → J-05` (rule 3 of the priority rubric); the iter-2 evaluator recommended it explicitly and there are no regressed journeys (rule 1) and no `COHERENCE-FAIL` to consolidate (last coherence = COHERENCE-PASS, rule 2). It is picked **alone** (rule 5 — one risky change, no bundling). Today `record_bar_series` (`routes.py:1603-1620`) calls `adapter.fetch_bars` — the Yahoo network call — **before** `store.record`, and the content-checksum `BarSeriesAlreadyRegistered` (409) fires only *after* the fetch; so a repeat window-fetch still re-hits Yahoo, which J-03 must end.

**Depth = full** is justified by the "Picking depth" triggers (not by ESCALATE — prior verdict was CONTINUE): J-03 introduces a **new persistence module / data-model** (`bar_index.py`, a new SQLite DB), requires **new tests beyond browser smoke** (index unit tests + a "no-network-on-a-cache-hit" test + a `reindex()` rebuild test), and carries **its own critical anti-goals** ("the SQLite index is a derived cache, never a source of truth" + "fetching is explicit and store-first"), so the audit + coherence lanes must run to confirm the index owns nothing and every served candle stays checksum-verified from the canonical JSON `BarStore`.

**Lessons applied (from `lessons.md`):** (iter-1) any `feed="yahoo"` test fixture must live under `tests/fixtures/yahoo/`, never `tests/fixtures/bars/` (a frozen test blanket-asserts `feed=="sip"` over the latter) — reuse the existing committed `tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json`. (iter-0/iter-2) the browser lane silently no-op'd when services were unreachable — J-03 is **backend-only (`Frontend Present: no`)** so it tolerates that gap, but the orchestrator MUST provision reachable `:3301`/`:8301` + Chrome MCP **before J-05** (the first genuinely-new-UI iteration), where the zero-frontend-diff fallback disappears.

## IN SCOPE

### Backend
- [ ] Add `apps/backend/app/research/bar_index.py` — a derived SQLite index mirroring the stdlib-`sqlite3` pattern of `apps/backend/app/research/store.py` (stdlib `sqlite3` + WAL + `busy_timeout`, hermetic dependency-injected DB path). Schema keyed by `(symbol, timeframe, window_start_utc, window_end_utc)` → `series_id`, `checksum`, `bar_count`. It stores **metadata only** and **owns nothing** — it is a rebuildable cache over the JSON `BarStore`.
- [ ] `reindex()` — rebuild the entire index from the canonical `BarStore.list()` (drop + repopulate); losing/deleting the DB file must reproduce identical lookups.
- [ ] A **store-first coordinator** in `record_bar_series` (`routes.py`): on `POST /research/bars`, look up the `(symbol, timeframe, window)` key in the index **before** calling `adapter.fetch_bars`; on a hit, load the stored series from `BarStore` (checksum-verified) and return it with **no** adapter/network call; on a miss, keep the existing flow (`adapter.fetch_bars` → the frozen `store.record` → then additively update the index). The frozen `BarStore.record` is **called, never modified**.
- [ ] Additive `?symbol=&timeframe=` filter on `GET /research/bars` (`list_bar_series`) served via the index; the **no-param** `GET /research/bars` response stays **byte-identical** to before (still `store.list()` verbatim).
- [ ] A new `get_bar_index` DI provider (mirroring `get_bar_store`) pointing at the config-owned index DB path (see Data-contract note), overridable in tests. DB file is gitignored (`*.db`/`-wal`/`-shm` already covered by `.gitignore`).
- [ ] Index DB path is **config-owned**: anchor it to the existing config-owned `bar_dir_resolved()` (co-located sibling file) with a `TAPEOLOGY_BAR_INDEX_DB` env override for hermetic tests, so **`config.py` stays byte-identical and `config_fingerprint` stays `4d665603569b9dbf`**. If a config field is added instead, it MUST join the fingerprint **exclusion set** with an exclusion test mirroring `test_bar_dir_is_excluded_from_config_fingerprint` — the unchanged fingerprint is the hard rule either way. (See assumptions ledger iter-3.)

### Frontend (if applicable)
- None. `Frontend Present: no` — J-03 is backend-only; the `/structure` fetch control is J-05.

### New user-facing capability
None on-screen this iteration. Backend behavior only: a repeat fetch of an already-stored window is served store-first (no re-download), and bar listings can be filtered by `symbol`/`timeframe`. The user-visible payoff lands in J-05 when the `/structure` fetch control drives this path.

### New information displayed
None (no frontend change).

### New user actions
None (no frontend change).

### UI surface changes
None.

### Product surface delta
The app stops re-downloading data it already holds: an identical fetch returns instantly from storage instead of re-calling Yahoo, and callers/tools can address a single series by `symbol`+`timeframe`. No screen changes.

### Blueprint conformance
Conforms to the existing Information Architecture — all J-03 endpoints live under the **Structure** section's canonical home (`/structure` → `GET /research/bars*`), which the blueprint already assigns to J-03. **No new page, route, or nav element** (nav skeleton unchanged; no re-approval). No `blueprint.reapproval-requested` written.

### Data-contract additions
**None.** J-03 introduces **no new displayed value**. The store-first lookup `(symbol,timeframe,window) → series_id`, its owner `research/bar_index.py` (**owns nothing**; rebuildable via `reindex()`), and its serving endpoint `GET /research/bars?symbol=&timeframe=` are **already registered** in `blueprint.md`'s Data Contract (row "Store-first lookup …") and IA (J-03 row) from the baseline draft — so `blueprint.md` needs no edit this iteration. The `?symbol=&timeframe=` filter serves the **existing** bar-series value (owned by the canonical `BarStore`, served by `GET /research/bars`); no second computation or second endpoint for any existing value is introduced.

## OUT OF SCOPE

- Any `/structure` / frontend change — that is J-05 (`Frontend Present: no` this iteration).
- Real S/R levels and A/B/C zones on Yahoo bars — that is J-04; `research/levels.py` is not touched.
- Overlap / subsumption caching (serving a sub-window from a larger stored window). Store-first is **exact `(symbol, timeframe, window_start, window_end)`-tuple match only** — the key the goal names; a smarter overlapping cache is unrequested scope.
- Any background / ambient re-indexing or polling. The index updates only additively on an explicit store-first fetch.
- Any change to the frozen `BarStore.record`, `bars.py`, the JSON store file format, `config_fingerprint`, `research/levels.py`, `research/strategies.py`, `research/backtests.py`, the tape engine, or the Alpaca adapter and its credentialed path.
- The stale `README.md:72` "only the daily timeframe is available" sentence (a non-blocking coherence advisory carried from iter-2) — a readme-maintainer/showcase concern, not J-03 code; see NOTES.

## DEFINITION OF DONE

- [ ] **J-03 passes** via index unit tests + a store-first "no-network-on-a-cache-hit" test: a first `POST /research/bars` stores + indexes; a second `POST` of the **same** `(symbol, timeframe, window)` invokes the adapter's `fetch_bars` **zero** times (call-counting fake adapter) and returns the stored series.
- [ ] `GET /research/bars?symbol=<S>&timeframe=<T>` returns only the matching series via the index; the **no-param** `GET /research/bars` response is **byte-identical** to before (asserted by test).
- [ ] `reindex()` rebuilds the index after the DB file is deleted and reproduces **identical** lookups (unit test); the index is never the source of truth — every store-first hit is **checksum-verified** from the canonical JSON `BarStore`.
- [ ] Required-still-passing **J-01, J-02, J-06** remain green: `config_fingerprint` stays `4d665603569b9dbf`, engine equivalence 22/22, and the frozen `BarStore.record` + Alpaca `sip` path + no-param `GET /research/bars` stay byte-identical.
- [ ] No anti-goal violation: coherence returns **COHERENCE-PASS** (the index owns nothing; single source of truth intact; no second bar store) and the scan-report is CLEAN.
- [ ] Unit tests pass; full backend suite green with no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-3-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none — `Frontend Present: no`, and J-03's acceptance in `docs/goal.md` is explicitly "index unit tests + a store-first 'no network on a cache hit' test *(Keyless; automated.)*", not browser. (No new live Yahoo test is required: the store-first path is proven keyless with a call-counting `FakeAdapter` via `dependency_overrides` + the committed `tests/fixtures/yahoo/` fixture and a rebuildable in-`tmp` index — no network in the default suite.)
- **Unit/integration:** `bar_index.py` (insert on record; exact-key lookup hit/miss; `reindex()` rebuild from `BarStore.list()`); the store-first coordinator ("cache hit performs no `fetch_bars`" via a call-counting fake adapter, and the returned series is checksum-verified from the JSON store); the additive `?symbol=&timeframe=` filter (returns only the matching series) **and** a byte-identity assertion that the no-param `GET /research/bars` is unchanged; a `config_fingerprint == 4d665603569b9dbf` / DB-path-does-not-move-the-fingerprint assertion.
- **Error cases:** index **miss** falls through to the normal fetch (no fabrication); a **deleted/corrupt** index DB is rebuilt by `reindex()` and never fabricates or loses a candle (rebuilt lookups equal pre-deletion lookups); a store-first hit **never** re-tags or pools the `feed="yahoo"` series with `sip`.

## NOTES

- **Store-first is at the route/coordinator level, above the frozen `BarStore.record`.** The frozen immutability unit test `apps/backend/tests/test_bars.py` (`BarSeriesAlreadyRegistered` on a double `store.record`) stays green because `store.record` is byte-identical. A repo grep found **no** route-level test asserting `409` on a duplicate-window `POST /research/bars` (the bar-level 409 lives only in that unit test), so serving the stored series (200) on a store-first hit is low regression risk — but the full suite must confirm it.
- **`config_fingerprint` is the hard J-06 lever.** Prefer the co-located DB path (no `config.py` edit); if a config field is added it must be fingerprint-excluded with an exclusion test mirroring `test_bar_dir_is_excluded_from_config_fingerprint` (see `test_bars.py:221` and the exclusion set at `config.py:1467-1482`). See assumptions ledger `iter-3 — goal-decomposer`.
- **Browser-env provisioning for J-05 (carry-forward).** iter-0/iter-2 browser lanes no-op'd on unreachable `:3301`/`:8301`. J-03 tolerates this (backend-only), but J-05 introduces the real `/structure` fetch control — the orchestrator must provision reachable services + Chrome MCP before the J-05 run, or J-05 cannot be evidenced.
- **Carried coherence advisory (non-blocking):** `README.md:72` still reads "Only the daily timeframe is available through this free path today" — stale since J-02. Out of J-03's code scope; flag for the next readme-maintainer pass.
- Reference: iter-2 evaluator recommendation (`runs/goal-session-yahoo_fetch/iter-2/eval.md`) and iter-2 coherence (`.../iter-2/coherence.md`, COHERENCE-PASS).
