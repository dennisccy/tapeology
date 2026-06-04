**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_will_be_super_rich-iter-4

- **Session:** i_will_be_super_rich · **Iteration:** 4 (full) · **Target journeys:** J-12 (live streaming), J-15 (stale-on-gap → recover)
- **Snapshot audited:** `git diff 4808e7f8…` (+ uncommitted working tree)
- **Scope:** backend-only — async provider seam + `LiveProvider` + live feeder/stale-watchdog + `POST /watch` live branch. **0 frontend files changed**, no new route/page/nav (confirmed by the ui-surface-map and the diff).

No objective Data Contract or Information Architecture violation found. This iteration is a clean extension of existing canonical owners — the new live path reuses the one engine, the one `stream_status` writer, and the one market-clock owner, and confines the vendor live SDK to the single adapter module.

---

## Step 1 — Data Contract (rows 1–9): PASS

The spec registers **no new displayed value**; the live read flows through the existing rows 1–6. Verified per row:

- **Row 6 `stream_status` — single owner preserved (the core SSOT risk this iteration).** `set_stream_status` is defined exactly once (`apps/backend/app/engine/tape_engine.py:47`). The new live feeder writes status only through that same engine setter — `apps/backend/app/watch_manager.py:194` (`stale`), `:200` (`live` recovery), `:201`/`:203` (`closed`) — identical to the sync feeder's existing calls (`:122`/`:131`/`:133`). **No second `stream_status` writer and no parallel status store** were introduced. Matches the blueprint's "the live feeder is the single owner that flips row-6 `stream_status`".
- **Rows 1–4 (tape state/confidence, features, quote, recent trades) — no duplicate computation.** The live feeder calls only `engine.process_event(event)` (`watch_manager.py` `_feed_live`). `LiveProvider.stream()` (`apps/backend/app/providers/live.py:45`) merely maps vendor-neutral `RawTrade`/`RawQuote` → `TradeEvent`/`QuoteEvent` (the same neutral→logical mapping `HistoricalProvider` does) and emits trades with `Side.UNKNOWN` so the **engine's** canonical aggressor classifier (row 4) re-derives side. No feature/state/side math is recomputed in the provider, feeder, API, or frontend.
- **Row 6 `scenario` descriptor.** `scenario = f"live {ticker}"` is built in `app/main.py` `_watch_live`, passed into the engine via the provider, and read back from `engine.snapshot().scenario` for the response — not recomputed downstream.
- **Row 8 market clock — no second clock.** The live pre-flight reuses `adapter.get_market_clock()` (`app/main.py` `_watch_live`, off the event loop) — the **same** computing owner the `MarketStatusIndicator` endpoint uses. Explicitly documented in-code; verified there is no new clock implementation.
- **Row 9 availability/failure.** Reuses the existing explicit error path — `provider_unavailable` (503) on no creds, `market_closed` (409 + next open) on an authoritative closed clock; a degraded/indeterminate clock is **not** reported as closed (no fabricated session). No fabricated cockpit, no sim fall-back.
- **Shared engine registry (SSOT).** `watch_with_async_provider` registers the live engine in the same `self._engines[ticker]` store (`watch_manager.py:95`) that `get()` (`:106`) and the REST/WS endpoints read — so `/state`, `/features`, `/summary`, `WS /stream`, and the UI all read the one live engine. No parallel live state/feature path.
- **Provider-seam singularity (architectural).** `git grep` confirms `StockDataStream` / `import alpaca` / `from alpaca` appear **only** in `apps/backend/app/providers/adapters/alpaca.py` (the lone matches elsewhere are a docstring mention in `historical.py:5` and the `AlpacaAdapter` factory export in `adapters/__init__.py` — neither is a vendor-SDK import). The new `AsyncProvider` Protocol (`app/providers/base.py`) is purely additive; the sync `Provider` body is unchanged. The new live socket method makes market-data subscriptions only — no order/account/position call (the pre-existing `TradingClient` references at `alpaca.py:114/198/272` are in the older symbol-search/clock reference reads, not the new `stream_live`).

## Step 2 — Information Architecture: PASS

No new page, route, nav entry, or parallel shell. Both target journeys live on the already-registered canonical home **`/` — Watch (the tape cockpit)**: J-12 → Live controls + status → cockpit; J-15 → the stream-status dot (live ⇄ stale). The behavior surfaces through existing elements (TopBar status dot reading `snapshot.stream_status`, watched-source label reading `snapshot.scenario`, the `Cockpit`) with **0 frontend code change**. Nothing is hidden or duplicated; no reachability or duplicate-home concern arises.

## Step 3 — Advisory (non-blocking)

- **Blueprint update is the promised additive clarification, not drift.** The +6-line edit to `state/blueprint.md` adds the sync/async-seam note and restates the single-`stream_status`-owner / no-parallel-path guarantee under the existing provider-seam section. No Data Contract row and no IA/nav entry changed → consistent with the spec's "additive, non-nav, no re-approval" and with what the code actually does.
- **(FYI only, outside the coherence remit)** `LIVE_TEARDOWN_GRACE_SECONDS = 6.0` is a named module constant in `alpaca.py` rather than `config.py`. It is an operational SDK-socket-close grace, not an engine/classifier threshold, and follows the existing `FEED_PACE_SECONDS` / `WS_PUSH_INTERVAL` precedent — the "no magic numbers" rule (engine thresholds) and the spec's only required config addition (`stale_gap_seconds`, correctly placed in `config.py`) are both satisfied. No action needed.

---

**Result:** COHERENCE-PASS — one app structure, one source of truth for every displayed value. The live half extends rows 1–6 through their existing canonical owners and adds no parallel computation, no second endpoint, no second clock, and no new navigation surface. No remediation required.
