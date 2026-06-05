**Verdict:** COHERENCE-WARN

---

## Coherence Audit — iter-6 (goal-i_will_be_super_rich-iter-6)

**Session:** i_will_be_super_rich · **Iteration index:** 6
**Snapshot SHA:** a01c1cc774c7d95bcefa5dd0505592d38180766e
**Blueprint status:** APPROVED (extended at iter-5, rows 10–12 in force)

---

## Step 1 — Data Contract check

**Result: no objective violations.**

### Row 10 — Price history: OHLC bars + tape-state-transition markers

Canonical computing module: `HistoryBuffer` (`apps/backend/app/engine/history.py`).
Canonical serving endpoint: `GET /tape/{ticker}/history?bar=<10|30|60>`.

The iteration implements row 10 exactly as pre-registered:

- `HistoryBuffer` is the single place candles are binned. It is constructed once inside
  `TapeEngine.__init__` and fed only from `TapeEngine.process_event` — never from
  `set_stream_status` or the constructor, so status flips cannot inject spurious bars or markers.
- Markers are appended via `history.note_state(snapshot.timestamp, snapshot.tape_state,
  snapshot.confidence)` at `tape_engine.py` (in the diff, line `+self._history.note_state(...)`).
  `tape_state` and `confidence` are the classifier's own snapshot values — no second classification.
- `serialize_history` in `apps/backend/app/serializers.py` is a pure projection: it reads
  `history.bars(bar)` and `history.markers()` and recomputes nothing.
- `PriceChart.tsx` calls `fetchHistory(ticker, barSize)` which reads `GET …/history?bar=` and
  passes the response VERBATIM to `series.setData(candles)` / `markersRef.current.setMarkers(...)`.
  The only transformation is `Math.round(b.time)` (coercing a float logical-timestamp to an integer
  for the charting library's time scale) — this is display formatting, not recomputation of price
  or state.

### Rows 1–9 — no new computation paths

No new function, service, or endpoint was introduced for any previously registered value (tape
state, confidence, features, quote/trade data, observations, watch status, symbol search, market
clock, or failure state). The aggressor classifier, `TapeStateClassifier`, `FeatureEngine`, and
`MarketState` are untouched.

---

## Step 2 — Information Architecture check

**Result: no objective violations.**

All new UI lives on the existing **`/` — Watch (the tape cockpit) — HOME** (`page.tsx`). The
`PriceChart` panel is mounted above `<Cockpit>` at `apps/frontend/app/page.tsx:104–106` and is
visible automatically when a sim or historical ticker is watched (0 extra clicks). The blueprint
IA explicitly assigns J-17 / J-18 to "price-chart pane above the cockpit (sim / historical)" —
canonical home matches.

Visibility gate at `page.tsx:104`:

    {ticker && (mode === "sim" || mode === "historical") && (
      <PriceChart ticker={ticker} />
    )}

This correctly hides the chart in Live mode, per the blueprint IA ("Hidden for Live").

No new route, no new page, no new nav entry, no parallel shell.

---

## Step 3 — Advisory observations (WARN)

**WARN — frontend bar-size constant mirrors backend config without a live sync mechanism.**

`apps/frontend/lib/types.ts:90` declares:

    export const HISTORY_BAR_SIZES = [10, 30, 60] as const;

This is a compile-time UI constant used to render the bar-size selector buttons. It mirrors
`history_bar_sizes: tuple[int, ...] = (10, 30, 60)` in `apps/backend/app/config.py:95`. No
data value is recomputed in the frontend — the actual candle data still arrives exclusively from
`GET /tape/{ticker}/history` — so this is not a Data Contract violation. However, the backend
config is the single owner of valid bar sizes; if `history_bar_sizes` is ever changed in config,
the frontend constant must be manually updated or the selector will show stale options (the
backend will reject out-of-set values with a 422, so no silent data divergence occurs, but the
selector UX would be misleading).

Recommended future tidy: expose the configured bar sizes via an API endpoint (e.g. a new
`allowed_bar_sizes` field in the `/tape/{ticker}/history` response or a dedicated `GET
/tape/config` endpoint) so the frontend reads them dynamically — making the backend config the
single source of truth end-to-end. This is advisory only and does not block the goal.

---

## Summary

| Check | Violations | Severity |
|-------|-----------|---------|
| Data Contract — row 10 (OHLC + markers) | none | — |
| Data Contract — rows 1–9 (existing values) | none | — |
| IA — new PriceChart panel on `/` | none | — |
| IA — chart visibility gating (sim/historical only) | none | — |
| Frontend bar-size constant vs backend config | advisory coupling | WARN |

No objective violation from Step 1 or Step 2. One advisory WARN recorded for the next iteration
to optionally tidy.
