# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index ab472fe..32b27c1 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -83,9 +83,6 @@ def api_base() -> str:
 # substitute the (URL-quoted) ticker; ``get_endpoint`` proxies any allowlisted GET path verbatim.
 
 _STATIC_PATHS: dict[str, str] = {
-    "journal": "/research/journal",
-    "analytics": "/research/analytics",
-    "studies": "/research/studies",
     "datasets": "/research/datasets",
     "bars": "/research/bars",
     "backtests": "/research/backtests",
@@ -172,21 +169,6 @@ TOOLS: tuple[types.Tool, ...] = (
             ("ticker",),
         ),
     ),
-    types.Tool(
-        name="journal",
-        description="Read-only proxy of GET /research/journal — the research journal rows JSON, verbatim.",
-        inputSchema=_object_schema({}),
-    ),
-    types.Tool(
-        name="analytics",
-        description="Read-only proxy of GET /research/analytics — the journal analytics JSON, verbatim.",
-        inputSchema=_object_schema({}),
-    ),
-    types.Tool(
-        name="studies",
-        description="Read-only proxy of GET /research/studies — the replay-study list JSON, verbatim.",
-        inputSchema=_object_schema({}),
-    ),
     types.Tool(
         name="datasets",
         description=(
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 4391010..082d79b 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -50,9 +50,6 @@ EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
     "tape_history",
-    "journal",
-    "analytics",
-    "studies",
     "datasets",
     "bars",
     "levels",
@@ -77,11 +74,14 @@ YAHOO_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "yahoo"
 # covered on a PERMANENTLY-unknown ``/research/*`` path, which no journey will ever ship.
 UNKNOWN_RESEARCH_PATH = "/research/nonexistent-path-canary"
 
+# clean_slate J-03: a path that WAS a real, shipped route (the journal-era `journal` MCP tool
+# proxied it) until clean_slate J-01 deleted its route handler — distinct from
+# UNKNOWN_RESEARCH_PATH above, which was NEVER real. Proves the honest-404 contract holds for an
+# actually-deleted surface, not only a synthetic canary.
+DELETED_RESEARCH_ROUTE = "/research/journal"
+
 # Live 2xx no-argument tools and their canonical endpoints.
 LIVE_STATIC = {
-    "journal": "/research/journal",
-    "analytics": "/research/analytics",
-    "studies": "/research/studies",
     "taxonomy": "/research/taxonomy",
     "ui_route_map": "/meta/ui-routes",
 }
@@ -700,6 +700,21 @@ async def test_get_endpoint_proxies_allowlisted_but_unknown_path_404_verbatim(mc
     assert result.content[1].text == f"HTTP 404 from GET {UNKNOWN_RESEARCH_PATH}"
 
 
+@pytest.mark.anyio
+async def test_get_endpoint_proxies_a_deleted_route_404_verbatim(mcp_env):
+    """clean_slate J-03: unlike ``UNKNOWN_RESEARCH_PATH`` (a path that was NEVER real),
+    ``/research/journal`` WAS a real, shipped route — proxied by the now-removed ``journal`` MCP
+    tool — until clean_slate J-01 deleted its route handler. The honest-404 contract must hold
+    identically for an ACTUALLY-deleted route: the backend's real 404 payload verbatim, plus the
+    explicit status message, never a synthesized or cached response."""
+    result = await call_tool("get_endpoint", {"path": DELETED_RESEARCH_ROUTE})
+    rest = httpx.get(f"{mcp_env}{DELETED_RESEARCH_ROUTE}", timeout=5.0)
+    assert rest.status_code == 404
+    assert result.isError is True
+    assert result.content[0].text.encode("utf-8") == rest.content
+    assert result.content[1].text == f"HTTP 404 from GET {DELETED_RESEARCH_ROUTE}"
+
+
 @pytest.mark.anyio
 async def test_get_endpoint_profiles_byte_identical_on_the_live_200(mcp_env):
     """J-05 flips ``/research/profiles`` from honest 404 to live data with ZERO MCP code changes
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-clean_slate/telemetry.jsonl   | 6 ++++++
 runs/goal-session-clean_slate/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
