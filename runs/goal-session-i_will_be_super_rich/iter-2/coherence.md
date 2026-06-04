# Coherence Audit — goal-i_will_be_super_rich-iter-2

**Verdict:** COHERENCE-PASS

- **Session:** i_will_be_super_rich · **Iteration:** 2 (`goal-i_will_be_super_rich-iter-2`)
- **Audited diff:** `git diff 6e3ca0e8699fe5c4c886c571c232545ad0b12a51` + uncommitted working tree
- **Blueprint:** `runs/goal-session-i_will_be_super_rich/state/blueprint.md`
- **Scope this iter:** J-11 (historical replay), J-13 (symbol search), J-14 (untradable / empty-window honest states). Implements Data Contract rows 7 + 9; **feeds** rows 1–6; no new route, no blueprint edit.

No objective Data-Contract (Part A) or Information-Architecture (Part B) violation found. Two minor advisory notes recorded below; neither blocks.

---

## Part A — Data Contract (single source of truth)

**PASS.** The historical path is a pure new *feeder* of the existing engine snapshot; it adds no parallel computation or serving path for any registered value.

- **Rows 1–6 (engine snapshot — tape state/confidence, 14 features × 5 windows, bid/ask/spread/last, recent trades + side, observations/event-log, watched-source + stream-status).** Fed, not recomputed.
  - `_watch_historical` (`apps/backend/app/main.py:161-191`) validates → fetches → calls `manager.watch_with_provider(ticker, provider, speed)` and returns `engine.snapshot()` (`main.py:192-195`). The canonical reads (`/tape/{ticker}/state|features|events|summary`, `WS /stream` at `main.py:233-253`) are **not in the diff** — unchanged. The historical watch populates the *same* `TapeEngine` those endpoints serve, so `/state`, `/features`, `/summary`, WS, and UI stay identical (J-08).
  - `HistoricalProvider` (`apps/backend/app/providers/historical.py:42-63`) yields only `QuoteEvent`/`TradeEvent` through the `Provider` interface; trades carry `Side.UNKNOWN`, so the engine's aggressor classifier re-derives side — no duplicate side/feature/state computation.
  - `watch_with_provider` (`apps/backend/app/watch_manager.py:57-77`) constructs the same `TapeEngine` and feeds it via `_feed_paced` → `engine.process_event(...)`; stream-status set via `engine.set_stream_status(...)` (the row-6 canonical owner). Pacing is delivery-only; engine math stays logical/deterministic.
  - **Verified untouched:** `serializers.py`, engine module, `providers/base.py`, `providers/simulated.py` all have empty diff stats — the sim path (J-01–J-10) is behavior-identical and no second state/feature path was introduced.
- **Row 7 (symbol-search results).** Canonical computing owner = the vendor adapter (`AlpacaAdapter.search_symbols`, `apps/backend/app/providers/adapters/alpaca.py:155-190`); canonical serving endpoint = `GET /symbols/search` (`main.py:198-217`). Frontend reads only this endpoint (`searchSymbols`, `apps/frontend/lib/api.ts:55-68`) and renders `symbol`+`name` verbatim (`SymbolSearch.tsx:100-111`) — no client-side recomputation/ranking. ✅
- **Row 9 (real-data failure states).** Surfaced as one explicit `RealDataError` from `POST /watch` with distinct reasons — `provider_unavailable` (503), `symbol_not_tradable` (404), `no_data_for_window` (404) (`main.py:141,167,188,190`); **no engine created** on any failure. UI renders the panel purely from the API-supplied `reason` (`page.tsx:47-58`, `ProviderUnavailable.tsx:copyFor`) — it does **not** re-derive availability. ✅
- **Vendor-seam singularity (architectural).** The `alpaca-py` SDK is imported **only** inside `providers/adapters/alpaca.py` (lazy method imports, lines 88-168); no `import alpaca` exists anywhere else. `main.py` names no vendor — it depends on the neutral `MarketDataAdapter` + `get_adapter()` and the neutral `SymbolNotTradable`/`NoDataForWindow`. Neutral types (`RawTrade`/`RawQuote`/`HistoricalWindow`/`SymbolMatch`) live in `adapters/base.py`. ✅
- **No unregistered displayed value.** All new UI values map to existing rows (search → row 7; honest states → row 9; cockpit values → rows 1–6). Config additions (`allowed_replay_speeds`, `default_replay_speed`, `replay_pacing_cap_seconds`, `symbol_search_limit`, `symbol_search_min_query`) are tunables in `app/config.py`, not displayed values. ✅

## Part B — Information Architecture (where do I find it / why is it everywhere)

**PASS.** Still exactly one screen (`/` — Watch — HOME) inside the existing persistent shell.

- **No new route/page** (confirmed in the ui-surface-map and the diff). `SymbolSearch` lives inside the persistent `TopBar` (`TopBar.tsx:94-104`), revealed by the existing data-source selector in Live/Historical — reachable with 0–1 actions, in its blueprint home. No parallel shell.
- **Honest non-cockpit panels** render *in place of* the cockpit via the single mutually-exclusive ternary in `page.tsx:97-104` (`Cockpit` | `ProviderUnavailable` | `IdleState`) — never alongside a fabricated cockpit. No duplicate home, no hidden/undiscoverable feature.
- The cockpit is **reused** (no second "results"/cockpit surface created for real data).

## Part C — Advisory notes (non-blocking)

1. **Vendor name in the seam factory.** `providers/adapters/__init__.py` now imports `AlpacaAdapter` and returns it from `get_adapter()` (and re-exports `real_data_available`). The DoD wording is "the vendor name appears in **exactly one** module (`providers/adapters/alpaca.py`)," so the bare name `Alpaca` technically also appears in the package `__init__.py`. This is **not** a coherence violation: it is the blueprint-sanctioned single wiring point (the package docstring documents "a second vendor … plus a one-line change to `get_adapter` here"), the SDK import stays confined to `alpaca.py`, and `main.py` uses only the neutral accessor — so the singularity is *strengthened*, not scattered. Flagged only so the post-QA auditor can reconcile it against the strict DoD phrasing.
2. **Live creds-present path still returns `provider_not_implemented` → generic error banner**, not a dedicated honest panel (`page.tsx` `HONEST_REASONS` omits it; falls through to `setError`). This is **pre-existing from iter-1**, explicitly **out of scope** here (J-12 live streaming), and `provider_not_implemented` is not a registered row-9 honest state. Forward-note for J-12 only.

## Cross-consistency confirmed

- Failure reasons match end-to-end: backend `main.py` ↔ `lib/types.ts` `FailureReason` ↔ `page.tsx` `HONEST_REASONS` ↔ `ProviderUnavailable.copyFor` (the three honest reasons), and the displayed `phrase` matches each backend `detail` string.
- Replay-speed set is consistent: backend `CONFIG.allowed_replay_speeds = (1,2,5,10)` is documented as a superset of the UI's `TopBar REPLAY_SPEEDS {1,2,5,10}`, so every UI choice validates (out-of-set → 422).
- Source label `historical <SYM> <window>` is produced once (`main.py:189`), carried on the snapshot (row 6), and rendered from the canonical snapshot in the UI — not recomputed client-side.

**Conclusion:** The iteration kept the product coherent — one app shell, one screen, one engine snapshot as the source of truth for every displayed cockpit value, one adapter/endpoint for search, and one `POST /watch` error channel for the honest failure states. Real data added **no** parallel state/feature/serving path. **COHERENCE-PASS.**
