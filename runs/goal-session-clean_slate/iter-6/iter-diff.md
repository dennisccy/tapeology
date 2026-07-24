# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/README.md b/README.md
index 0bbfc85..72c499d 100644
--- a/README.md
+++ b/README.md
@@ -48,12 +48,12 @@ Current capabilities:
 - **Strategy registry and a tape-confirmed structure strategy (research API)** — a named list of the trading strategies a backtest can be run under: the original `v1` strategy, plus an additive second one, `structure_tape`, that only opens a simulated trade where price sits at (or has just moved through) one of the support/resistance levels above AND the live tape agrees — either the tape shows that level being defended (a fade back the other way) or shows real, sustained price impact carrying straight through it (a follow-through in that direction). Every simulated entry records exactly which level — its price, timeframe, and A/B/C conviction class — triggered it, reported with the same simulated return-in-R-and-dollars figures beside the same random-entry comparison every backtest already shows. Registering `structure_tape` never changes the frozen `v1` strategy or any of its past results, and `structure_tape` only ever becomes the shown "champion" strategy through the same honest hold-out comparison every candidate goes through — never automatically. The current registry and today's champion strategy are reachable through the research API and the matching machine-readable tool.
 - **Class-scaled risk, reward, and size for structure_tape, with a per-class PnL breakdown (research API)** — every `structure_tape` simulated trade sets its stop distance, take-profit target, and simulated position size from the A/B/C conviction class of the level it entered at: an A-class level (the strongest cross-timeframe agreement) gets a tight stop (about 1 basis point beyond the level) and the largest simulated size, while B and C levels get progressively wider stops and smaller size. The take-profit target is a class-scaled multiple of the trade's own risk, capped at the next already-detected opposing level rather than an arbitrary distance. Every stop distance, target multiple, and size factor is a named configuration value, never a number buried in code. Backtest reports for any registered strategy show, alongside the existing blended total, a per-class A/B/C breakdown of trade count and net return in both R-multiples and dollars — a strategy that does not use support/resistance levels (such as `v1`) honestly shows all three classes empty rather than omitting the section.
 - **Fetch real bars from Yahoo Finance, right on the Structure page** — a fetch control lets you pick a symbol and a start/end UTC date range, then click "Fetch from Yahoo Finance" — no account, API key, or cost required. One click fetches all six supported timeframes at once (1w / 1d / 4h / 1h / 5m / 1m; 4h is derived from real 1h bars) — there is no timeframe to pick — and the end date is included in full (a fetch through a given day includes that day's bars). The button stays disabled until the symbol and both dates have a value, and its label changes to "Fetching…" while requests are in flight. Each timeframe reports its own result in a list beneath the form as it completes — how many bars it fetched or served from storage, "already stored" when identical bars were previously saved under a different window, or the exact reason it could not be served (a timeframe Yahoo does not offer for that window, such as 1-minute bars beyond its retention, never masks the timeframes that did succeed). On success, the candlestick chart and the Tradable Map populate automatically — no separate "Load" step — with the raw support/resistance level lines and confluence-zone table available a click away via "Show raw levels"; a "Yahoo Finance" badge appears above the chart confirming the data's provenance, its label read from the same central taxonomy used elsewhere in the product. Asking again for a symbol/timeframe/window you already fetched is served back instantly from local storage instead of contacting Yahoo Finance again. Only if all six timeframes fail does a distinctly-styled panel replace the result — stating plainly that nothing was loaded and nothing cached or fabricated is shown in its place.
-- **Structure page** — the second top-level page (reachable from the top navigation bar on every page). Picking a symbol and an as-of date/time now shows, by default, the **Tradable Map**: bands drawn as solid, color-coded reference lines on the price candlestick chart (rose for resistance, emerald for support) plus a table of each band's side, price range, quality score, member count, round-number flag, and inherited A/B/C class. A "Show raw levels" toggle, off by default, reveals the page's original view unchanged — dashed reference lines for every individual raw level, plus a confluence-zones table beneath the chart listing each zone's A/B/C strength grade, numeric score, and member levels — and can be switched back off. Below the toggle, an **Edge Report** section shows an honest three-strategy profit comparison over recorded event windows; a **Case Studies** section — a filterable registry of historical band-touch events with a per-event drill-in — exists in the app but is currently withheld from view pending an operator decision, with its data still reachable through the research API and the matching machine-readable tool (see below). Further down, the "Fetch from Yahoo Finance" control and its provenance badge (see its own bullet above for its one-click, all-timeframes behavior), the strategy **Registry**/champion panel, and the `structure_tape`-vs-`v1` **Comparison** tool are all still present — the next two bullets describe the Registry and Comparison sections. Every value on the page is read verbatim from its owning endpoint — nothing is recomputed in the browser — and each section has its own explicit empty/error state rather than a blank or guessed screen: no price history ever recorded for the symbol, history recorded but nothing derivable yet at that as-of time, levels with no qualifying zone, or the backend unreachable/date-time invalid. When a symbol has price history recorded at more than one timeframe, a **Chart timeframe** dropdown lets you pick which recorded timeframe's candles both the Tradable Map and the raw-levels chart draw — defaulting to daily when recorded, otherwise the shortest recorded timeframe — while reference lines for levels and zones keep spanning every recorded timeframe regardless of which one is currently drawn; switching the dropdown never changes the as-of levels, zones, or tradable bands themselves.
+- **Structure page** — the second top-level page (reachable from the top navigation bar on every page). Picking a symbol and an as-of date/time now shows, by default, the **Tradable Map**: bands drawn as solid, color-coded reference lines on the price candlestick chart (rose for resistance, emerald for support) plus a table of each band's side, price range, quality score, member count, round-number flag, and inherited A/B/C class. A "Show raw levels" toggle, off by default, reveals the page's original view unchanged — dashed reference lines for every individual raw level, plus a confluence-zones table beneath the chart listing each zone's A/B/C strength grade, numeric score, and member levels — and can be switched back off. Below the toggle, a **Case Studies** section lists every recorded support/resistance band-touch event, filterable by symbol and by rejected/broke/chopped reaction, with each row opening a drill-in that shows that event's band, reaction, forward returns, and — once a dataset was recorded around it — its tape-timeline playback (an honest "No recorded tape for this event." message otherwise); beneath it, an **Edge Report** section shows an honest three-strategy profit comparison over recorded event windows. Further down, the "Fetch from Yahoo Finance" control and its provenance badge (see its own bullet above for its one-click, all-timeframes behavior), the strategy **Registry**/champion panel, and the `structure_tape`-vs-`v1` **Comparison** tool are all still present — the next two bullets describe the Registry and Comparison sections. Every value on the page is read verbatim from its owning endpoint — nothing is recomputed in the browser — and each section has its own explicit empty/error state rather than a blank or guessed screen: no price history ever recorded for the symbol, history recorded but nothing derivable yet at that as-of time, levels with no qualifying zone, or the backend unreachable/date-time invalid. When a symbol has price history recorded at more than one timeframe, a **Chart timeframe** dropdown lets you pick which recorded timeframe's candles both the Tradable Map and the raw-levels chart draw — defaulting to daily when recorded, otherwise the shortest recorded timeframe — while reference lines for levels and zones keep spanning every recorded timeframe regardless of which one is currently drawn; switching the dropdown never changes the as-of levels, zones, or tradable bands themselves.
 - **Strategy registry and champion panel on the Structure page** — further down the page (below the Tradable Map and Edge Report sections), a Registry section shows the three trading strategies the system knows about — `v1`, `structure_tape`, and `structure_tape_map` — each as a card listing its entry rule and its exit rules: stop distance, a reward target where the strategy defines one (`structure_tape` and `structure_tape_map` both do; `v1` does not), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` and `structure_tape_map` cards additionally show three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this is identical to the champion served by the research API's profiles endpoint — one store pointer, two read views. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
 - **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. On the operator's real AAPL price history, for example, the strongest band in the map is the ~300–302 resistance zone — the exact level where price was rejected six times before a sharp drop — ranking first out of all ten bands, ahead of every other zone. This map is now the default view on the Structure page in the browser, and remains reachable through the research API and the matching machine-readable tool.
-- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints; a touch too recent to have built up the usual follow-up window is honestly labeled with exactly how much less time its verdict is based on, rather than being shown as an ordinary result. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results; because scanning the full panel is expensive, the scan result is remembered after the first request — saved durably enough to survive a backend restart — so repeat lookups return in a fraction of a second instead of re-scanning every time. A Case Studies section on the Structure page can browse this registry — filterable by symbol and by reaction outcome, with a per-event drill-in — but it is currently withheld from view pending an operator decision; the registry itself remains fully reachable through the research API and the matching machine-readable tool.
-- **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. Real recordings today span a broad slice of the panel, including the pinned reference example, whose drill-in now shows a real, second-by-second tape reading in place of the earlier empty placeholder. Each drill-in replays its recorded window fresh on every open rather than caching the result, so a large window can take several minutes to load. A committed real-data sample keeps this timeline check running with no credentials required. This timeline is built into each event's Case Studies drill-in, which is currently withheld from the Structure page pending an operator decision (see the Case Studies bullet above); the timeline remains reachable through the research API and the matching machine-readable tool.
+- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints; a touch too recent to have built up the usual follow-up window is honestly labeled with exactly how much less time its verdict is based on, rather than being shown as an ordinary result. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results; because scanning the full panel is expensive, the scan result is remembered after the first request — saved durably enough to survive a backend restart — so repeat lookups return in a fraction of a second instead of re-scanning every time. A Case Studies section on the Structure page browses this registry — filterable by symbol and by reaction outcome, with a per-event drill-in — and the registry itself remains fully reachable through the research API and the matching machine-readable tool.
+- **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. Real recordings today span a broad slice of the panel, including the pinned reference example, whose drill-in now shows a real, second-by-second tape reading in place of the earlier empty placeholder. Each drill-in replays its recorded window fresh on every open rather than caching the result, so a large window can take several minutes to load. A committed real-data sample keeps this timeline check running with no credentials required. This timeline is built into each event's Case Studies drill-in on the Structure page (see the Case Studies bullet above); the timeline remains reachable through the research API and the matching machine-readable tool.
 - **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It appears as its own card in the Structure page's strategy Registry section and is exercised automatically as part of the 3-way edge report below (now also visible on the Structure page); it is runnable through the existing backtest API, but there is no button yet to pick it directly for a standalone ad hoc backtest in the browser.
 - **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. Real recorded trading windows now exist across a broad slice of the panel, giving the report real touches to measure instead of only the small practice dataset; any cell still short of enough trades honestly labels itself "insufficient sample" rather than manufacturing a result, and an entirely empty report remains a valid, honest outcome whenever nothing yet clears the bar. Computing the full report over the currently recorded data is slow and can take a long time to finish on a first run, showing a loading state throughout rather than a fabricated interim result. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. This report is now visible on the Structure page in the browser as the Edge Report, and remains reachable through the research API and the matching machine-readable tool.
 - **Edge report caching and a permanent record of its findings (research API)** — once the 3-way profit edge report's full computation over recorded data has completed a single time, the result is now remembered in a durable, disk-backed cache and served back within an interactive few seconds on every later request — through the REST API, the machine-readable connection, and the Structure page's Edge Report panel alike — including after a full backend restart. Nothing about what the report measures, how it is computed, or the shape of its response changes; any change to the underlying recorded datasets, registered strategies, or configuration automatically invalidates the cached answer, so the next request recomputes it byte-identically rather than serving something stale. A finished report's findings can also now be permanently appended, as a deliberate one-time step, to the same append-only profit-and-loss record described above — its own dedicated entry, with every data feed and the train/hold-out split kept fully separate from every entry recorded before it. As of today the very first full computation over the currently recorded real data, and its permanent recording, have not yet been run — see the next capability for exactly what the Edge Report panel honestly shows in the meantime.
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 250fe4a..f9d140e 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -82,62 +82,6 @@ from .taxonomy import taxonomy_payload
 router = APIRouter(prefix="/research", tags=["research"])
 
 
-class ThesisRequest(BaseModel):
-    """Body for ``POST /research/thesis``. ``level_price`` is optional at the schema level — the
-    per-setup REQUIRED/FORBIDDEN rule is enforced in the route (a 422), never by the schema, so the
-    error message is explicit and taxonomy-owned."""
-
-    ticker: str
-    setup_type: str
-    direction: str
-    invalidation_price: float
-    level_price: float | None = None
-    # The optional declared-from-hint linkage (capability 33, J-65): when the user declares from a
-    # hint's prefill affordance the frontend passes the hint id here. Additive + optional — a normal
-    # (non-prefilled) declaration omits it and is unchanged. An unknown/invalid id is a 422 (validated in
-    # the route, not the schema, so the message is explicit). The link is recorded on the hint record
-    # ONLY when the declaration COMPLETES — one click never creates a thesis.
-    declared_from_hint_id: str | None = None
-
-
-class ResolveRequest(BaseModel):
-    """Body for ``POST /research/thesis/{id}/resolve``. ``resolution`` is validated in the route (not
-    by the schema) so the message is explicit and the user-vs-system ownership rule is enforced in one
-    place: a user may set only ``played_out`` / ``abandoned``; ``invalidated`` / ``expired`` are
-    system-owned (422) and an unknown value is also a 422."""
-
-    resolution: str
-
-
-class ActionRequest(BaseModel):
-    """Body for ``POST /research/thesis/{id}/action`` (J-52). ``kind`` (``entry`` | ``exit``) and the
-    sign/finiteness of ``price`` are validated in the ROUTE (not the schema) so the message is
-    explicit and the verbatim-recording discipline is enforced in one place. ``price`` is typed
-    ``float`` so a non-numeric body is a 422 at the schema layer before the route runs."""
-
-    kind: str
-    price: float
-
-
-class StudyRequest(BaseModel):
-    """Body for ``POST /research/studies`` (capability 32, J-60). ``source_kind`` (``reference`` |
-    ``sim`` | ``historical``) + ``source_id`` (the sim ticker / reference id / the symbol), the setup ×
-    direction, an optional ``level_price`` (REQUIRED for the two level setups, FORBIDDEN otherwise),
-    and the historical ``start`` / ``end`` window for an arbitrary historical study. All validation is
-    enforced in the ROUTE (not the schema) so messages are explicit and taxonomy-owned. An optional
-    ``null_baseline_seed`` lets a caller pin the baseline (the committed reference study uses the config
-    default so it reproduces in CI)."""
-
-    source_kind: str
-    source_id: str = ""
-    setup_type: str
-    direction: str
-    level_price: float | None = None
-    start: str | None = None
-    end: str | None = None
-    null_baseline_seed: int | None = None
-
-
 class BacktestRequest(BaseModel):
     """Body for ``POST /research/backtests`` (era-3 capability 4, J-03) — exactly the Product
     Shape's three fields: the dataset id, the strategy id, and the profile. ``profile`` defaults
@@ -205,17 +149,6 @@ class EdgeReportComputeRequest(BaseModel):
     force: bool = False
 
 
-class ReviewRequest(BaseModel):
-    """Body for ``POST /research/thesis/{id}/review`` (J-57). ``mistake_tags`` is the user-CONFIRMED
-    tag list (distinct from the machine-SUGGESTED tags); ``note`` is the optional free text (REQUIRED
-    only when ``other`` is among the tags). Both rules are enforced in the ROUTE (not the schema) so
-    the message is explicit and taxonomy-owned. ``mistake_tags`` defaults to an empty list so a
-    body with only a note (or an empty review) is well-formed at the schema layer."""
-
-    mistake_tags: list[str] = []
-    note: str | None = None
-
-
 class ResearchRegistry:
     """Owns the journal store and the backtest/edge-compute background job managers.
 
diff --git a/apps/backend/tests/test_routes_no_orphaned_request_models.py b/apps/backend/tests/test_routes_no_orphaned_request_models.py
new file mode 100644
index 0000000..e79ef33
--- /dev/null
+++ b/apps/backend/tests/test_routes_no_orphaned_request_models.py
@@ -0,0 +1,135 @@
+"""Source-introspection guard: every Pydantic request-body model class defined in
+``app/research/routes.py`` must be referenced by at least one live route-handler parameter in the
+same file (era-5D J-05/close-out iteration, "The Clean Slate" demolition interlude).
+
+BACKGROUND: era-5D J-01's route demolition deleted 14 route handlers but left 5 orphaned
+request-body classes behind -- ``ThesisRequest``, ``ResolveRequest``, ``ActionRequest``,
+``StudyRequest``, ``ReviewRequest`` -- each with exactly one occurrence in the file (its own
+``class X(BaseModel):`` def line) and zero live references. That was a grep-provable breach of the
+critical "Deletion is complete, never cosmetic" anti-goal that four earlier passes missed and only
+a hard audit caught. This test is the durable guard against that defect class recurring.
+
+Built STRUCTURALLY (parses ``routes.py``'s own current class/parameter shape via ``ast``) -- it
+NEVER names a specific class as a string, so it keeps failing correctly after any FUTURE route
+deletion instead of going stale itself (the carried lesson: a guard test that hardcodes a deletion
+target is only good until the next deletion).
+"""
+
+from __future__ import annotations
+
+import ast
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+ROUTES_PATH = BACKEND_DIR / "app" / "research" / "routes.py"
+
+
+def _request_body_model_classes(tree: ast.Module) -> set[str]:
+    """Every top-level class in the module whose bases include ``BaseModel`` by name."""
+    names = set()
+    for node in ast.iter_child_nodes(tree):
+        if not isinstance(node, ast.ClassDef):
+            continue
+        for base in node.bases:
+            if isinstance(base, ast.Name) and base.id == "BaseModel":
+                names.add(node.name)
+                break
+    return names
+
+
+def _annotation_names(annotation) -> set[str]:
+    """Every ``Name`` identifier appearing anywhere inside a parameter annotation expression --
+    handles a plain ``X``, a subscripted ``Optional[X]``, or a ``X | None`` union alike. Never
+    matches a class's own ``class X(...):`` def line (that is a different AST node kind, not a
+    function-parameter annotation) and never matches a docstring or comment mention."""
+    if annotation is None:
+        return set()
+    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}
+
+
+def _parameter_referenced_class_names(tree: ast.Module) -> set[str]:
+    """Every class name annotated on some function parameter anywhere in the module -- i.e. used
+    as a live route-handler request body (or any other function parameter)."""
+    referenced: set[str] = set()
+    for node in ast.walk(tree):
+        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
+            continue
+        args = node.args
+        all_params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
+        if args.vararg:
+            all_params.append(args.vararg)
+        if args.kwarg:
+            all_params.append(args.kwarg)
+        for param in all_params:
+            referenced |= _annotation_names(param.annotation)
+    return referenced
+
+
+def _orphaned_model_classes(source: str) -> list[str]:
+    tree = ast.parse(source)
+    model_classes = _request_body_model_classes(tree)
+    referenced = _parameter_referenced_class_names(tree)
+    return sorted(model_classes - referenced)
+
+
+def test_every_request_body_model_is_referenced_by_a_live_route_parameter():
+    """Structural invariant: every ``class X(BaseModel):`` defined in ``routes.py`` must be
+    annotated on at least one function parameter elsewhere in the same file. A class satisfying
+    only its own def line is an orphan -- exactly the residue era-5D's close-out iteration deleted
+    (``ThesisRequest``, ``ResolveRequest``, ``ActionRequest``, ``StudyRequest``,
+    ``ReviewRequest``)."""
+    source = ROUTES_PATH.read_text()
+    model_classes = _request_body_model_classes(ast.parse(source))
+    assert model_classes, "expected at least one BaseModel request-body class in routes.py"
+
+    orphans = _orphaned_model_classes(source)
+    assert not orphans, (
+        "orphaned request-body model class(es) with no live route-handler parameter reference: "
+        f"{orphans} -- delete the class (and its docstring) or wire it to a route parameter"
+    )
+
+
+def test_the_guard_would_have_flagged_the_just_deleted_orphans_pre_cleanup():
+    """Proves the guard's own logic is sound (not merely that it happens to pass today): re-applied
+    to a synthetic module reproducing the PRE-cleanup shape (the 5 now-deleted classes present with
+    zero parameter references, alongside one referenced class standing in for the 4 kept ones), it
+    must name exactly those 5 as orphans."""
+    pre_cleanup_source = '''
+from pydantic import BaseModel
+
+
+class ThesisRequest(BaseModel):
+    ticker: str
+
+
+class ResolveRequest(BaseModel):
+    resolution: str
+
+
+class ActionRequest(BaseModel):
+    kind: str
+
+
+class StudyRequest(BaseModel):
+    source_kind: str
+
+
+class ReviewRequest(BaseModel):
+    note: str | None = None
+
+
+class BacktestRequest(BaseModel):
+    dataset_id: str
+
+
+def create_backtest(body: BacktestRequest) -> dict:
+    return {}
+'''
+    orphans = _orphaned_model_classes(pre_cleanup_source)
+    assert orphans == [
+        "ActionRequest",
+        "ResolveRequest",
+        "ReviewRequest",
+        "StudyRequest",
+        "ThesisRequest",
+    ]
```
