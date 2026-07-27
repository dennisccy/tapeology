# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
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
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/journey-scripts/J-05.json | 2 +-
 runs/goal-session-desk/telemetry.jsonl           | 6 ++++++
 runs/goal-session-desk/trace/trace.jsonl         | 3 +++
 3 files changed, 10 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
