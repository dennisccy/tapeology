# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_price_chart_confluence.py b/apps/backend/tests/test_price_chart_confluence.py
index 1f304e0..49011a4 100644
--- a/apps/backend/tests/test_price_chart_confluence.py
+++ b/apps/backend/tests/test_price_chart_confluence.py
@@ -11,9 +11,11 @@ This module extends that precedent to J-06's two hardest-to-verify-by-inspection
   1. the confluence chip's "which tape state confirms this band's side" decision reads the SERVED
      `/research/strategies` `structure_tape_map` mapping — never a client-hardcoded literal of one
      of the four tape-state names (single-source-of-truth / no-client-recomputation);
-  2. the band overlay's fetch is keyed on `ticker` alone and passes the CURRENT wall-clock time as
-     `as_of` (no client-side "which is the prior session" date arithmetic — the no-lookahead
-     resolution is entirely server-side, in `tradability.py`'s own `_resolve_basis`).
+  2. the band overlay's fetch is keyed on `[ticker, history?.epoch_anchor]` (not `ticker` alone) and
+     is DEFERRED — no request is issued — until `history?.epoch_anchor` resolves, with NO
+     wall-clock-"now" fallback anywhere in the `as_of` computation (no client-side "which is the
+     prior session" date arithmetic either — the no-lookahead resolution is entirely server-side, in
+     `tradability.py`'s own `_resolve_basis`).
 
 Copy-discipline coverage (imperative/prediction/claim language in the new chip text) is NOT
 duplicated here: `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` already
@@ -128,29 +130,43 @@ def test_tradability_bands_fetch_is_keyed_on_ticker_and_stable_session_anchor_no
 def test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math():
     """`as_of` must be the WATCHED SESSION's own current moment: `history.epoch_anchor` (Data
     Contract row 13, already fetched by the existing history poll — no new fetch) converted to an
-    ISO string, falling back to the current wall-clock time only before the first `history`
-    response lands. This is what makes a HISTORICAL replay of a PAST session (e.g. 2026-06-22)
-    resolve THAT session's own prior-close basis (2026-06-18) — using the browser's wall-clock
-    "now" instead would resolve TODAY's basis, which is unrelated to whatever price action is being
-    replayed (verified empirically: a live AAPL 2026-06-22 replay showed no band anywhere near the
-    replayed price when as_of was wall-clock "now"). No-lookahead guard: the frontend must contain
-    no local "prior session" date arithmetic — `_resolve_basis` (tradability.py) alone decides the
-    prior session server-side; this only supplies WHICH moment to resolve from."""
+    ISO string. There is NO wall-clock-"now" fallback anywhere in the computation: an early-return
+    guard defers the fetch entirely (issues no request, stays in `phase: "loading"`) until
+    `history?.epoch_anchor` resolves. This is what makes a HISTORICAL replay of a PAST session
+    (e.g. 2026-06-22) resolve THAT session's own prior-close basis (2026-06-18) at every moment,
+    including the sub-second window before the first `history` response lands — the request is
+    simply not issued yet, rather than issued against today's date (the prior iteration's wall-clock
+    fallback was observed to transiently draw today's-basis bands during that window; this iteration
+    removes the fallback entirely instead of narrowing it). No-lookahead guard: the frontend must
+    contain no local "prior session" date arithmetic — `_resolve_basis` (tradability.py) alone
+    decides the prior session server-side; this only supplies WHICH moment to resolve from, and only
+    once that moment is known."""
     source = _source()
     idx = source.index("fetchTradability(")
     call_site = source[idx : idx + 60]
     assert "asOf" in call_site, "expected fetchTradability to be called with a computed `asOf` variable"
-    # The `asOf` computation itself, just above the call site.
-    as_of_computation = source[max(0, idx - 400) : idx]
-    assert "history?.epoch_anchor" in as_of_computation or "history.epoch_anchor" in as_of_computation, (
+    # The `asOf` computation AND its enclosing early-return guard, just above the call site.
+    preceding = source[max(0, idx - 900) : idx]
+    assert "history.epoch_anchor" in preceding, (
         "expected the as_of computation to read history's epoch_anchor field"
     )
-    assert "epoch_anchor * 1000" in as_of_computation, (
+    assert "epoch_anchor * 1000" in preceding, (
         "expected epoch_anchor (seconds) to be converted to ms the SAME way this file already does "
         "for candle timestamps (toClock), not a fresh unit convention"
     )
-    assert "new Date().toISOString()" in as_of_computation, (
-        "expected a current-wall-clock-time fallback for before the first history response lands"
+    assert "new Date().toISOString()" not in source, (
+        "found a wall-clock-'now' fallback still present — the fetch must be deferred (early-return "
+        "guard) until history.epoch_anchor resolves, never fall back to today's date"
+    )
+    # The early-return/deferred-fetch guard itself: the effect must bail out BEFORE computing
+    # `asOf` or calling fetchTradability whenever the anchor has not resolved yet.
+    assert "epoch_anchor == null" in preceding, (
+        "expected an early-return guard checking history?.epoch_anchor == null before the asOf "
+        "computation / fetch call"
+    )
+    assert preceding.count('phase: "loading"') >= 2, (
+        "expected BOTH the deferred-fetch guard and the actual pre-fetch state update to set "
+        'phase: "loading" (never "idle") while epoch_anchor is unresolved or a fetch is in flight'
     )
     banned_session_math = [
         "getPreviousTradingDay",
diff --git a/apps/frontend/components/PriceChart.tsx b/apps/frontend/components/PriceChart.tsx
index d9f2d6a..ca9c9ca 100644
--- a/apps/frontend/components/PriceChart.tsx
+++ b/apps/frontend/components/PriceChart.tsx
@@ -186,24 +186,34 @@ export function PriceChart({
   // Contract row 13, ALREADY fetched by the poll above — no new fetch) is "the real UTC epoch a
   // watched session's logical time 0 maps to" — a real market epoch for a historical replay, so
   // during e.g. the 2026-06-22 replay this correctly resolves THAT session's own prior-close basis
-  // (2026-06-18) rather than today's. Falls back to the current wall-clock time only before the
-  // first `history` response lands (first paint) or for a SIM ticker (whose synthetic anchor is
-  // moot anyway — SIM-* symbols resolve `no_bar_series_for_symbol` regardless of `as_of`). This is
-  // STILL zero client "which session" math (no-lookahead): `_resolve_basis` (tradability.py) alone
-  // decides the prior session server-side; converting an epoch-seconds field to an ISO string is
-  // the SAME pure unit/format conversion this file already does for candle timestamps above
-  // (`toClock`), never a date computation of "which session."
+  // (2026-06-18) rather than today's. The fetch is DEFERRED — no request issued — until this
+  // anchor resolves: there is NO wall-clock fallback anywhere in this computation. Before the
+  // first `history` response lands (first paint), or while a ticker's window has not yet warmed,
+  // the effect below early-returns and stays in `phase: "loading"` (never `"idle"`, so the
+  // ready-only empty-state/`tradabilityEmpty` logic further down never activates prematurely, and
+  // never a fetch against the browser's wall-clock "now", which would resolve TODAY's basis
+  // instead of the replayed session's own). The next 1s `history` poll tick simply re-runs this
+  // effect once the anchor lands (a SIM ticker still resolves `no_bar_series_for_symbol` once it
+  // does fetch, same as before — deferring the fetch is a no-op for SIM since its anchor is always
+  // non-null). This is STILL zero client "which session" math (no-lookahead): `_resolve_basis`
+  // (tradability.py) alone decides the prior session server-side; converting an epoch-seconds
+  // field to an ISO string is the SAME pure unit/format conversion this file already does for
+  // candle timestamps above (`toClock`), never a date computation of "which session."
   useEffect(() => {
     if (!ticker) {
       setTradabilityState({ phase: "idle", data: null });
       return;
     }
+    if (history?.epoch_anchor == null) {
+      // The watched session's own anchor has not resolved yet — defer the fetch entirely (issue
+      // no request) rather than falling back to wall-clock "now". Stay in "loading", not "idle",
+      // so the ready-only tradabilityEmpty/confluence logic never fires on a stale/absent read.
+      setTradabilityState({ phase: "loading", data: null });
+      return;
+    }
     let cancelled = false;
     setTradabilityState({ phase: "loading", data: null });
-    const asOf =
-      history?.epoch_anchor != null
-        ? new Date(history.epoch_anchor * 1000).toISOString()
-        : new Date().toISOString();
+    const asOf = new Date(history.epoch_anchor * 1000).toISOString();
     fetchTradability(ticker, asOf).then((res) => {
       if (cancelled) return;
       if (res.ok && res.data) {
```
