"""The ``/meta/*`` namespace — product metadata. Owner of Data Contract row 35 (J-01).

``GET /meta/ui-routes`` is the SINGLE source of truth for the list of user-facing routes.
The rendered top-bar navigation (``apps/frontend/components/NavBar.tsx``) and the MCP
``ui_route_map`` tool both read this endpoint verbatim — the hand-maintained frontend list is
retired; no duplicate route list (including a frontend "fallback") may exist anywhere.

The map lists exactly the LIVE routes at all times: a route is added here in the same
iteration its page ships (J-05 adds ``/performance`` together with that page), so the nav can
never carry a dead link. ``nav`` says whether an entry is a top-bar destination —
``/journal/[id]`` is a real user-facing page but is reached from the journal list, not the
bar, so it is present with ``nav: false`` (the honest child-route representation).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/meta", tags=["meta"])

# Data Contract row 35: THE canonical route list. Each entry carries at least ``path`` and
# ``label`` (the nav renders them verbatim) plus the ``nav`` top-bar flag. Immutable tuple —
# the endpoint below is this module's only serving path.
UI_ROUTES: tuple[dict[str, object], ...] = (
    {"path": "/", "label": "Cockpit", "nav": True},
    {"path": "/journal", "label": "Journal", "nav": True},
    {"path": "/journal/[id]", "label": "Journal detail", "nav": False},
    {"path": "/studies", "label": "Studies", "nav": True},
)


@router.get("/ui-routes")
def get_ui_routes() -> dict:
    """The canonical UI route map, served verbatim from ``UI_ROUTES`` (computed nowhere else)."""
    return {"routes": [dict(entry) for entry in UI_ROUTES]}
