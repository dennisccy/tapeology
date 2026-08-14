# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index cbeb917..eb779be 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -40,6 +40,7 @@ from .providers.adapters.base import (
 from .providers.historical import HistoricalProvider
 from .providers.live import LiveProvider
 from .research.desk_routes import router as desk_router
+from .research.referee_routes import router as referee_router
 from .research.routes import (
     ResearchRegistry,
     get_registry_or_none,
@@ -201,6 +202,12 @@ app.include_router(research_router)
 # its own module (routes.py is already large) — mounted separately, alongside research_router.
 app.include_router(desk_router)
 
+# Era 6 "The Referee" (J-01): the readiness fold, under /research/desk/referee — its own module
+# for the SAME reason desk_routes.py itself is separate from routes.py (already large; see
+# referee_routes.py's own docstring). Reached by the MCP get_endpoint's existing /research/
+# prefix allowlist automatically — no MCP change needed.
+app.include_router(referee_router)
+
 # The meta namespace (Data Contract row 35, J-01): the canonical UI route map. The rendered nav
 # and the MCP ``ui_route_map`` tool read it — never a hand-maintained duplicate list.
 app.include_router(meta_router)
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/telemetry.jsonl   | 7 +++++++
 runs/goal-session-referee/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
