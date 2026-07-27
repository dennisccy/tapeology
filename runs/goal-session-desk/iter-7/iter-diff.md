# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/README.md b/README.md
index db14c7a..b354f04 100644
--- a/README.md
+++ b/README.md
@@ -63,7 +63,7 @@ Current capabilities:
 - **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. The top-up job is also reachable from the Desk page's "Top-up" button (below), in addition to the research API and the command line; the coverage check itself has no dedicated page yet, though each screen's briefing row shows a per-timeframe coverage badge — it otherwise remains reachable through the research API.
 - **A daily screening desk over the fetched universe (research API + command-line tool)** — for the latest registered S&P 100 universe snapshot, run a "screen" as of a chosen date: for every member, read its own already-computed tradable level map and summarize the closest support/resistance band into one ranked list — that band's inherited A/B/C conviction class, how far the screen date's closing price sits from it in basis points, and the band's quality score, ranked strongest and closest first. A member with no recorded price bars for that date is reported as an honest "skipped" entry rather than guessed at. Every run is pinned to its exact inputs — the screen date, which universe snapshot was used, the exact configuration in effect, and the bar data on file at the time — so repeating an identical request returns the same saved result instead of writing a duplicate, and a corrupted or tampered saved run is refused rather than silently overwritten. A run reports live progress as it works through the list and can be cancelled mid-flight; only one run proceeds at a time. Past runs can be browsed as lightweight summaries, or fetched in full by date or as the latest recorded result. Triggered explicitly from the command line, the research API, or the Desk page's "Run Screen" button (below) — never automatically.
-- **Desk page** — the third top-level page, reachable from the top navigation bar alongside Cockpit and Structure. Before any screen has ever been run it shows the plain message "Desk screen not computed yet." with enabled "Run Screen" and "Top-up" buttons. Run Screen starts today's screen over the registered universe and shows live progress — how many members have been checked so far and which symbol is currently being processed — with a Cancel control; clicking it again while a run is already in progress does not start a second one, it just shows the same run already under way. Top-up is the first on-screen control for the bar-fetching job described above, with the same live-progress and cancel behavior. Once a screen has run, the page shows four sections in order: a **Provenance** line naming which universe snapshot and date were used, the as-of timestamp, and the app's own internal settings fingerprint and bar-store signature, so two screens can always be told apart or confirmed identical; the **Briefing** — the ranked table itself, with each symbol's side, A/B/C class (captioned "nearest same-class band"), distance from that level in basis points, band score, a badge per timeframe the symbol has bar coverage for, and a tick-evidence badge where a recorded trade-by-trade dataset exists; **Skipped Members**, split into an honest "no bars" group and a "no basis session" group, each shown only when it has entries; and a read-only **Screen History** list of every past run (date, row/skipped counts, and its own provenance summary). Clicking Run Screen before any universe has ever been registered shows an inline error message instead of silently starting a job, and if the backend becomes unreachable while a run's progress is being checked, the page keeps showing the last progress it knew about rather than going blank. Opening a past entry in the Screen History list, and jumping from a ranked symbol straight to its chart on the Structure page, are both planned for a future update — today the history list shows only its summary line.
+- **Desk page** — the third top-level page, reachable from the top navigation bar alongside Cockpit and Structure. Before any screen has ever been run it shows the plain message "Desk screen not computed yet." with enabled "Run Screen" and "Top-up" buttons. Run Screen starts today's screen over the registered universe and shows live progress — how many members have been checked so far and which symbol is currently being processed — with a Cancel control; clicking it again while a run is already in progress does not start a second one, it just shows the same run already under way. Top-up is the first on-screen control for the bar-fetching job described above, with the same live-progress and cancel behavior. Once a screen has run, the page shows four sections in order: a **Provenance** line naming which universe snapshot and date were used, the as-of timestamp, and the app's own internal settings fingerprint and bar-store signature, so two screens can always be told apart or confirmed identical; the **Briefing** — the ranked table itself, with each symbol's side, A/B/C class (captioned "nearest same-class band"), distance from that level in basis points, band score, a badge per timeframe the symbol has bar coverage for, and a tick-evidence badge where a recorded trade-by-trade dataset exists; **Skipped Members**, split into an honest "no bars" group and a "no basis session" group, each shown only when it has entries; and a **Screen History** list of every past run (date, row/skipped counts, and its own provenance summary). Clicking Run Screen before any universe has ever been registered shows an inline error message instead of silently starting a job, and if the backend becomes unreachable while a run's progress is being checked, the page keeps showing the last progress it knew about rather than going blank. Every row in the Screen History list is now clickable: selecting a past date swaps the whole page's Provenance, Briefing, and Skipped Members display to that exact recorded date's own saved screen — a read-back with nothing recomputed — and a banner ("Viewing the recorded screen for `<date>` — not the latest.") appears above the Provenance panel with a one-click "Latest" button that snaps back to the newest screen instantly; a small inline note appears instead if a history click fails or matches no recorded screen, leaving the rest of the page unchanged. Every symbol row in the Briefing and Skipped Members tables — ranked or skipped — is itself a link into the Structure page for that exact symbol and date, arriving there with the symbol and as-of fields already filled in and the tradable-map chart already drawn, no manual re-typing needed; a skipped symbol still lands on Structure's own honest empty/no-data state, which is expected.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /research/desk/screen`, `POST /research/desk/screen/compute`, `GET /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 32b27c1..e4028ec 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -18,8 +18,9 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
     at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
-    era-5B J-04); an allowlisted-but-UNKNOWN path (any unshipped
-    ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
+    era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06); an allowlisted-but-UNKNOWN
+    path (any unshipped ``/research/*``) still surfaces the backend's honest 404 this way — never
+    placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -101,6 +102,14 @@ _STATIC_PATHS: dict[str, str] = {
     # strategy-comparison report takes no query params at all -- it aggregates over the WHOLE
     # registered dataset registry on its own.
     "edge_report": "/research/edge-report",
+    # `desk_universe`/`desk_screen` (Era B "The Desk" J-06) are the IDENTICAL no-required-param
+    # shape as `datasets`/`setups`/`edge_report` above: each proxies an endpoint that already
+    # serves an explicit HTTP 200 honest-empty payload before anything is ever registered/computed
+    # (never a 404 -- the `datasets`/`bars` no-data convention `desk_universe.py`/`desk_screen.py`
+    # themselves follow). Neither tool exposes the `?date=` query variant of
+    # `GET /research/desk/screen` -- that stays reachable only through `get_endpoint`.
+    "desk_universe": "/research/desk/universe",
+    "desk_screen": "/research/desk/screen",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -272,6 +281,29 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_universe",
+        description=(
+            "Read-only proxy of GET /research/desk/universe -- Era B \"The Desk\" J-01's "
+            "registered universe-snapshot list: every dated, checksummed S&P constituents "
+            "snapshot ever registered, its normalized membership, and the most recently "
+            "registered snapshot (`latest`, `null` before any registration -- an explicit "
+            "honest-empty 200, never a 404), JSON verbatim."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_screen",
+        description=(
+            "Read-only proxy of GET /research/desk/screen -- Era B \"The Desk\" J-03's "
+            "append-only screen-snapshot ledger: a meta-only list of every recorded screen plus "
+            "the most recently recorded screen's full ranked/skipped rows and provenance "
+            "(`latest`, `null` before any screen is ever computed -- an explicit honest-empty "
+            "200, never a 404), JSON verbatim. Takes no arguments here; `get_endpoint` reaches "
+            "the `?date=` lookup variant for one specific past screen."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 082d79b..088d51e 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -39,13 +39,16 @@ from app.mcp import (
 )
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarSeriesAlreadyRegistered, BarStore
+from app.research.desk_screen import ScreenStore
+from app.research.desk_universe import UniverseStore
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
 # Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
-# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), and
-# ``setups`` (era-5B J-02) are the newest additions, each positioned right after its
-# dependency-order sibling (the same store/registry+route+MCP shape, mirrored end to end).
+# ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), ``setups``
+# (era-5B J-02), and ``desk_universe``/``desk_screen`` (era-desk J-06, MCP contract v3 -- 15 -> 17
+# tools) are the newest additions, each positioned right after its dependency-order sibling (the
+# same store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -58,6 +61,8 @@ EXPECTED_TOOLS = (
     "backtests",
     "strategies",
     "edge_report",
+    "desk_universe",
+    "desk_screen",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -107,6 +112,8 @@ def backend_paths(tmp_path_factory):
         "TAPEOLOGY_JOURNAL_DB": str(tmp_path_factory.mktemp("mcp-journal") / "journal.db"),
         "TAPEOLOGY_DATASET_DIR": str(tmp_path_factory.mktemp("mcp-datasets")),
         "TAPEOLOGY_BAR_DIR": str(tmp_path_factory.mktemp("mcp-bars")),
+        "TAPEOLOGY_DESK_UNIVERSE_DIR": str(tmp_path_factory.mktemp("mcp-desk-universe")),
+        "TAPEOLOGY_DESK_SCREEN_DIR": str(tmp_path_factory.mktemp("mcp-desk-screen")),
     }
 
 
@@ -247,6 +254,143 @@ async def test_static_live_tools_json_byte_identical_to_rest(mcp_env):
         assert result.content[0].text.encode("utf-8") == rest.content, f"{name} not byte-identical"
 
 
+# --- Era B "The Desk" J-06: desk_universe / desk_screen (empty + populated + ?date= proxy) -------
+#
+# Both stores are rooted at their OWN env-scoped temp dirs (`backend_paths` above) that nothing
+# else in this module ever touches, so the honest-empty state below is genuinely observed BEFORE
+# either populated-state test seeds anything (file order matters here, same as everywhere else in
+# this module -- there is no pytest-randomly plugin in this project).
+
+DESK_SCREEN_DATE = "2026-06-22"
+DESK_SCREEN_NONMATCH_DATE = "2020-01-01"
+
+
+@pytest.mark.anyio
+async def test_desk_universe_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any universe snapshot is ever registered, ``desk_universe`` proxies
+    ``GET /research/desk/universe``'s explicit HTTP 200 honest-empty payload -- never a 404 (the
+    ``datasets``/``bars`` no-data convention ``desk_universe.py`` itself follows)."""
+    result = await call_tool("desk_universe", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/universe", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"snapshots": [], "latest": None, "integrity_errors": []}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_universe not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_universe_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """The ``bars``/``levels``/``tradability``/``setups`` J-01 precedent, applied to the desk
+    universe store: seed ONE real snapshot directly through ``UniverseStore.record()`` -- the
+    exact persistence call ``POST /research/desk/universe/fetch`` itself makes -- into the live
+    backend's env-scoped ``TAPEOLOGY_DESK_UNIVERSE_DIR``, then prove the tool's JSON is
+    byte-identical to its curl equivalent on a NON-EMPTY result."""
+    universe_dir = Path(backend_paths["TAPEOLOGY_DESK_UNIVERSE_DIR"])
+    UniverseStore(universe_dir).record(
+        members=["AAPL", "MSFT"],
+        raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
+        source_url=CONFIG.desk_universe_source_url,
+        min_members=CONFIG.desk_universe_min_members,
+        max_members=CONFIG.desk_universe_max_members,
+    )
+    result = await call_tool("desk_universe", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/universe", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["snapshots"]) >= 1, "the live list must be non-empty for this proof"
+    assert body["latest"] is not None
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_universe not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_screen_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any screen has ever been computed, ``desk_screen`` proxies
+    ``GET /research/desk/screen``'s explicit HTTP 200 honest-empty payload -- never a 404 (the
+    ``GET /research/desk/universe`` convention ``desk_screen.py`` itself follows)."""
+    result = await call_tool("desk_screen", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"screens": [], "latest": None, "integrity_errors": []}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_screen not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_screen_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """The ``desk_universe`` populated-state precedent immediately above, applied to the screen
+    store: seed ONE real snapshot directly through ``ScreenStore.record()`` -- the exact
+    persistence call the screen compute manager itself makes -- into the live backend's
+    env-scoped ``TAPEOLOGY_DESK_SCREEN_DIR``, then prove the tool's JSON is byte-identical to its
+    curl equivalent on a NON-EMPTY result. This screen snapshot is also what the ``get_endpoint``
+    ``?date=`` proxy test right below reads."""
+    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
+    ScreenStore(screen_dir).record(
+        screen_date=DESK_SCREEN_DATE,
+        as_of="2026-06-22T21:00:00Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature="mcp-test-signature",
+        rows=[
+            {
+                "symbol": "AAPL",
+                "side": "resistance",
+                "band_class": "A",
+                "distance_bps": 12.5,
+                "band_score": 3.1,
+                "price_low": 300.0,
+                "price_high": 302.0,
+                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-06-22T00:00:00Z"}},
+                "tick_evidence": True,
+            }
+        ],
+        skipped=[
+            {
+                "symbol": "PG",
+                "skipped": True,
+                "reason": "no_bars",
+                "coverage": {"1d": {"has_bars": False, "latest_window_end_utc": None}},
+                "tick_evidence": False,
+            }
+        ],
+    )
+    result = await call_tool("desk_screen", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["screens"]) >= 1, "the live list must be non-empty for this proof"
+    assert body["latest"] is not None
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_screen not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_get_endpoint_desk_screen_date_query_proxies_verbatim(mcp_env):
+    """TC-6/TC-7: ``get_endpoint`` reaches the ``?date=`` lookup variant ``desk_screen`` itself
+    does not expose -- byte-identical for a matching date (the screen the previous test just
+    recorded), and the honest ``{"screen": null}`` 200 (never a 404, never an error) for a
+    non-matching one."""
+    matching_path = f"/research/desk/screen?date={DESK_SCREEN_DATE}"
+    result = await call_tool("get_endpoint", {"path": matching_path})
+    rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json()["screen"] is not None
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen date-match not byte-identical"
+
+    nonmatch_path = f"/research/desk/screen?date={DESK_SCREEN_NONMATCH_DATE}"
+    result = await call_tool("get_endpoint", {"path": nonmatch_path})
+    rest = httpx.get(f"{mcp_env}{nonmatch_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"screen": None}
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen date-nonmatch not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
     """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 7627da6..0362f78 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -178,6 +178,29 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
   return entries.length > 0 && entries.every((tf) => !tf.has_bars);
 }
 
+// era-desk-iter-7 audit F2 fix: the row's stretched drill-in anchor (`absolute inset-0`) paints
+// above every cell in the row, including the per-cell `title`s at desk-row-distance/desk-row-score
+// and each coverage badge's own `title` -- those became pointer-unreachable the moment the anchor
+// started covering the whole row. Rather than touch the anchor's `href`/class/`data-testid` (any
+// of which risks J-05's already-passing whole-row click), the full-precision detail those per-cell
+// titles carried is composed directly onto the ANCHOR's own `title` instead: hovering ANYWHERE in
+// the row now reveals one composite tooltip. Full precision -- never the rounded 2-decimal DISPLAY
+// audit F3 chose for scanability (this is a hover detail, not a rendered cell).
+function deskRowDrillInTitle(row: DeskScreenRow): string {
+  const coverageLines = Object.entries(row.coverage)
+    .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
+    .join(" · ");
+  return `distance ${row.distance_bps} bps · score ${row.band_score}${coverageLines ? ` · ${coverageLines}` : ""}`;
+}
+
+// A skipped member has no distance_bps/band_score -- its anchor's tooltip carries ONLY the
+// coverage-freshness portion, never a fabricated value for a field that does not exist on that row.
+function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
+  return Object.entries(skip.coverage)
+    .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
+    .join(" · ");
+}
+
 // One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
 // coverage badges, tick-evidence badge — the DoD's exact column list, every value read verbatim
 // from the snapshot. Distance and score are DISPLAYED to two decimals (a `0.33523150389608725 bps`
@@ -205,6 +228,7 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           href={`/structure?symbol=${encodeURIComponent(row.symbol)}&asof=${encodeURIComponent(asOf)}`}
           data-testid="desk-row-drill-in"
           aria-label={`Open ${row.symbol} in Structure as of ${asOf}`}
+          title={deskRowDrillInTitle(row)}
           className="absolute inset-0"
         />
         {row.symbol}
@@ -292,6 +316,7 @@ function DeskSkipRow({ skip, asOf }: { skip: DeskScreenSkip; asOf: string }) {
           href={`/structure?symbol=${encodeURIComponent(skip.symbol)}&asof=${encodeURIComponent(asOf)}`}
           data-testid="desk-skip-row-drill-in"
           aria-label={`Open ${skip.symbol} in Structure as of ${asOf}`}
+          title={deskSkipDrillInTitle(skip)}
           className="absolute inset-0"
         />
         {skip.symbol}
diff --git a/apps/backend/tests/test_desk_hover_tooltip_guard.py b/apps/backend/tests/test_desk_hover_tooltip_guard.py
new file mode 100644
index 0000000..872dacd
--- /dev/null
+++ b/apps/backend/tests/test_desk_hover_tooltip_guard.py
@@ -0,0 +1,145 @@
+"""era-desk-iter-7 (audit finding F2) source-introspection guard test -- the
+``test_desk_ui_guards.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT, assert on
+substrings/structure; no browser, no runtime).
+
+iter-6's audit found F2: the row's stretched drill-in anchor (``desk-row-drill-in`` /
+``desk-skip-row-drill-in``, ``absolute inset-0``) paints above every cell in the row, so the
+per-cell ``title``s at ``desk-row-distance``/``desk-row-score`` and each coverage badge's own
+``title`` -- which carried the row's full-precision ``distance_bps``/``band_score`` and each
+timeframe's "window last requested" freshness -- became pointer-unreachable no matter how deep a
+hover targets. iter-7's fix consolidates that lost detail onto the anchor's OWN ``title`` instead
+of any covered cell (the anchor is already the topmost element everywhere in the row, so this is
+the one placement that stays reachable), with ZERO change to the anchor's ``href``,
+``absolute inset-0`` class, or ``data-testid`` -- the click/navigation geometry J-05's own golden
+script already depends on stays byte-unchanged.
+
+This guard proves the consolidation actually happened and stays that way: each anchor carries a
+dynamic (never static, never empty) ``title`` expression that calls a named function, and that
+function's OWN source references the exact fields the fix is required to carry -- full
+``row.distance_bps``/``row.band_score`` plus coverage ``latest_window_end_utc`` for the ranked-row
+anchor; ONLY the coverage ``latest_window_end_utc`` for the skip-row anchor (a skipped member has
+no distance/score value to show, and fabricating one would violate the "honest absence" rule).
+
+A guard that can never fail proves nothing -- ``test_guard_can_fail_on_a_seeded_violation`` below
+seeds both a static-title regression and a field-dropped regression and proves the same checks
+catch each."""
+
+from __future__ import annotations
+
+import pathlib
+import re
+
+import pytest
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+
+_TITLE_EXPR_RE = re.compile(r"title=\{\s*([A-Za-z_][A-Za-z0-9_]*)\(")
+
+
+def _anchor_block(source: str, testid: str) -> str:
+    """The single self-closing ``<Link ... data-testid="<testid>" ... />`` element's own source
+    text -- located by its testid, sliced from the nearest preceding ``<Link`` to its own closing
+    ``/>`` -- so every check below inspects ONLY that element's own attributes, never the whole
+    file."""
+    marker = f'data-testid="{testid}"'
+    idx = source.index(marker)
+    start = source.rindex("<Link", 0, idx)
+    end = source.index("/>", idx) + len("/>")
+    return source[start:end]
+
+
+def _anchor_title_function_name(source: str, testid: str) -> str:
+    """The name of the function the anchor's ``title={...}`` expression calls. Raises (via a
+    failed ``assert``) if the anchor carries no ``title`` at all, or a static one (e.g.
+    ``title="drill in"``) -- a static/absent title is exactly the F2 regression this guard exists
+    to catch."""
+    block = _anchor_block(source, testid)
+    match = _TITLE_EXPR_RE.search(block)
+    assert match is not None, (
+        f"anchor {testid!r} carries no dynamic title={{fn(...)}} expression -- its hover tooltip "
+        f"is unreachable or static:\n{block}"
+    )
+    return match.group(1)
+
+
+def _extract_function(source: str, name: str) -> str:
+    """The full source text of function ``name``'s block, from its ``function name(`` declaration
+    to its own matching closing brace -- a plain brace-depth walk (TSX has no Python ``ast``
+    module to lean on here), the same "read as TEXT" discipline this whole module uses."""
+    marker = f"function {name}("
+    start = source.index(marker)
+    brace_start = source.index("{", start)
+    depth = 0
+    end = brace_start
+    for i in range(brace_start, len(source)):
+        if source[i] == "{":
+            depth += 1
+        elif source[i] == "}":
+            depth -= 1
+            if depth == 0:
+                end = i
+                break
+    return source[start : end + 1]
+
+
+def test_ranked_row_drill_in_tooltip_is_built_from_distance_score_and_coverage_freshness():
+    """The ranked-row (``desk-row-drill-in``) anchor's tooltip-building function references the
+    row's own full ``distance_bps``, full ``band_score``, and coverage ``latest_window_end_utc``
+    -- the exact three fields audit F2 found unreachable once the anchor started painting above
+    their per-cell ``title``s."""
+    source = _DESK_PAGE.read_text()
+    fn_name = _anchor_title_function_name(source, "desk-row-drill-in")
+    fn_source = _extract_function(source, fn_name)
+    for needle in ("row.distance_bps", "row.band_score", "latest_window_end_utc"):
+        assert needle in fn_source, (
+            f"{fn_name}() never references {needle!r} -- the ranked row's composite hover "
+            "tooltip must carry the row's own full-precision distance/score plus coverage "
+            "freshness, not a static or empty string"
+        )
+
+
+def test_skip_row_drill_in_tooltip_carries_coverage_freshness_only():
+    """The skip-row (``desk-skip-row-drill-in``) anchor's tooltip-building function references
+    coverage ``latest_window_end_utc`` but NEVER ``distance_bps``/``band_score`` -- a skipped
+    member has no distance/score value, and fabricating one would violate the honest-absence
+    rule."""
+    source = _DESK_PAGE.read_text()
+    fn_name = _anchor_title_function_name(source, "desk-skip-row-drill-in")
+    fn_source = _extract_function(source, fn_name)
+    assert "latest_window_end_utc" in fn_source, (
+        f"{fn_name}() never references latest_window_end_utc -- the skip row's tooltip must still "
+        "carry its own coverage-freshness detail"
+    )
+    for forbidden in ("distance_bps", "band_score"):
+        assert forbidden not in fn_source, (
+            f"{fn_name}() references {forbidden!r} -- a skipped member has no distance/score "
+            "value to show; this would fabricate one"
+        )
+
+
+def test_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing. Two seeded regressions, each
+    caught by the checks above: (1) a static ``title`` on the anchor (no dynamic expression to
+    find at all), and (2) a tooltip function that dropped one of the required fields."""
+    seeded_static_title = (
+        '<td>\n  <Link href="/structure" data-testid="desk-row-drill-in" title="drill in" '
+        'className="absolute inset-0" />\n</td>'
+    )
+    with pytest.raises(AssertionError):
+        _anchor_title_function_name(seeded_static_title, "desk-row-drill-in")
+
+    seeded_field_dropped = (
+        "function deskRowDrillInTitle(row: DeskScreenRow): string {\n"
+        "  return `distance ${row.distance_bps} bps`;\n"
+        "}\n\n"
+        "<td>\n"
+        '  <Link data-testid="desk-row-drill-in" title={deskRowDrillInTitle(row)} '
+        'className="absolute inset-0" />\n'
+        "</td>"
+    )
+    fn_name = _anchor_title_function_name(seeded_field_dropped, "desk-row-drill-in")
+    fn_source = _extract_function(seeded_field_dropped, fn_name)
+    assert "row.distance_bps" in fn_source
+    assert "row.band_score" not in fn_source  # the seeded violation: score was dropped
+    assert "latest_window_end_utc" not in fn_source  # the seeded violation: coverage was dropped
```
