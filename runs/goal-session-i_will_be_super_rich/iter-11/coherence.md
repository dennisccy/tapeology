**Verdict:** COHERENCE-PASS

---

## Iteration 11 — Coherence Audit

**Session:** i_will_be_super_rich · **Iter:** 11 · **Snapshot SHA:** ef49b6c5dc87e95c09e977b672307c5a92440357
**Blueprint status:** APPROVED (iter-11 extension registered as additive, no new contract row)

---

## Step 1 — Data Contract check

The blueprint's iter-11 header explicitly states: "No new endpoint, no new producer, no new
displayed value, no new contract row." The diff is consistent with that declaration.

**Row 7 (Symbol search results — `GET /symbols/search?q=`).**
`warm_symbol_universe()` was added to `AlpacaAdapter` (`apps/backend/app/providers/adapters/alpaca.py:487`)
and to the neutral `MarketDataAdapter` protocol (`apps/backend/app/providers/adapters/base.py:151`).
It writes to the single existing `_ASSET_UNIVERSE` module-level cell (`alpaca.py:84`), which
`_asset_universe()` (`alpaca.py:457`) already used as the single owner. No second store is
introduced. `main.py` calls the method through the neutral adapter seam (`main.py:114`) — it never
names the SDK or the cache directly. `search_symbols` still reads from `_asset_universe()` (`alpaca.py:358`)
— the same single owner. Canonical source: unchanged. No violation.

`searchSymbols` in `apps/frontend/lib/api.ts` now accepts an `AbortSignal` (`api.ts:142`). An
aborted request resolves to `[]` — presentation property of the same `GET /symbols/search`
endpoint. The canonical serving endpoint is unchanged. No second lookup. No violation.

**Row 9 (Real-data availability / failure state — `POST /watch/{ticker}`).**
`VendorTimeout` is a new neutral exception class added to `base.py` (`base.py:97`). It is raised
by the adapter's `_mapped_vendor_timeout` context manager (`alpaca.py:106`) when the underlying
`requests.Session` HTTP timeout fires, and is caught in `main.py` alongside `asyncio.TimeoutError`
(`main.py:286`), mapping both to `RealDataError("provider_timeout", HISTORICAL_OVERSIZE_DETAIL, 504)`.
This is the same single `POST /watch/{ticker}` failure path registered in row 9 — the error
reason is `provider_timeout` with a more actionable detail string, not a new reason or a new
endpoint. Single owner (Live/Historical provider + adapter): unchanged. No violation.

**Rows 10–12 / historical fetch (engine history buffer, paused state, resolved window).**
The concurrent fetch and window cache live entirely inside `AlpacaAdapter.fetch_historical`
(`alpaca.py:189`). The `_HISTORICAL_WINDOW_CACHE` (`alpaca.py:91`) stores and replays raw
`HistoricalWindow` objects (trades + quotes as neutral records) — not pre-computed engine values.
OHLC/markers are still computed once by the engine history buffer after the provider delivers
events; the cache supplies the raw input records, not computed outputs. No second computation of
rows 1–6 values. No violation.

**Rows 1–6 (engine-owned tape values).**
The `_feed_paced` warm-up fast-forward in `watch_manager.py` (`watch_manager.py:214`) changes the
wall-clock sleep between delivered events (delivery pacing only). The events themselves — their
logical timestamps and ordering — are unchanged. The engine receives the same ordered stream and
computes identical features/state/confidence. `stream_status` is still exclusively written by the
engine/feeder via `set_stream_status` calls; the frontend reads it verbatim from the snapshot
(`Cockpit.tsx:18`, `api.ts:292`). No client-side recomputation. No violation.

**New displayed value check.**
The only new display is the actionable oversize text (`HISTORICAL_OVERSIZE_DETAIL` in `main.py:97`)
shown on the existing failure panel. The blueprint registers this explicitly as a message variant
of the already-registered row-9 `provider_timeout` reason — same failure path, same single owner.
It is not a new engine value and not a new contract row. No violation.

**Conclusion:** No Data Contract violation. PASS.

---

## Step 2 — Information Architecture check

The diff changes these files in the frontend tree:
- `apps/frontend/components/SymbolSearch.tsx` — behavioral change (cancellation, min-query)
- `apps/frontend/lib/api.ts` — `searchSymbols` signature update
- `apps/frontend/lib/config.ts` — new config constants

No new page, no new route. `apps/frontend/app/` still contains only `globals.css`, `layout.tsx`,
and `page.tsx`. The single `/` route is unchanged. No new nav link, no new sidebar section, no
parallel shell.

All journeys J-28/J-29/J-30 are mapped to the single `/` cockpit in the blueprint's IA ("all on
the same `/` cockpit area; no new surface"). The symbol search box, the failure panel, and the
cockpit waiting/progress treatment are existing surfaces on `/`. No reachability or duplicate-home
issue arises.

**Conclusion:** No IA violation. PASS.

---

## Step 3 — Subjective observations (advisory)

**WARN — minor config alignment note (advisory, non-blocking).**
`SYMBOL_SEARCH_MIN_QUERY = 1` in `apps/frontend/lib/config.ts` sets the client-side min-query to
1 character. The backend's `symbol_search_min_query` is a separate constant in
`apps/backend/app/config.py` (not changed in this diff). The blueprint states the client constant
should mirror the backend threshold. If the backend threshold is also 1, these are aligned; if it
differs, a single-character query will pass the client guard but be blocked server-side — a
harmless redundancy, not a correctness defect. No FAIL: these are config values, not displayed
values, and the backend still enforces its own threshold on every request regardless.

---

## Summary

| Check | Result |
|-------|--------|
| Data Contract (Step 1) | PASS — no duplicate computation, no non-canonical source, no new unregistered value |
| Information Architecture (Step 2) | PASS — no new route, no missing nav path, no duplicate home |
| Subjective (Step 3) | WARN — `SYMBOL_SEARCH_MIN_QUERY` / backend `symbol_search_min_query` alignment advisory |

**Verdict:** COHERENCE-PASS
