# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
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
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-clean_slate/telemetry.jsonl   | 6 ++++++
 runs/goal-session-clean_slate/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
