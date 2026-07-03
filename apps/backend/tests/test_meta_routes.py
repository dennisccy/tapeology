"""``GET /meta/ui-routes`` — the canonical UI route map (Data Contract row 35, J-01).

The route-map module is the SINGLE owner of the list of user-facing routes: the rendered
top-bar navigation and the MCP ``ui_route_map`` tool both read this endpoint verbatim — no
hand-maintained duplicate list may exist anywhere else. The map lists exactly the LIVE routes
at all times (a route ships here in the same iteration its page ships), so it MUST NOT carry
``/performance`` until J-05 lands that page — the nav never renders a dead link.

Uses a lifespan-less ``TestClient`` (the existing ``test_api.py`` precedent): the meta router
has no registry/engine dependencies, so no store injection is needed.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ui_routes_lists_exactly_the_live_routes():
    """The payload is byte-stable and lists exactly the four live routes, in nav order."""
    response = client.get("/meta/ui-routes")
    assert response.status_code == 200
    assert response.json() == {
        "routes": [
            {"path": "/", "label": "Cockpit", "nav": True},
            {"path": "/journal", "label": "Journal", "nav": True},
            {"path": "/journal/[id]", "label": "Journal detail", "nav": False},
            {"path": "/studies", "label": "Studies", "nav": True},
        ]
    }


def test_ui_routes_every_entry_carries_path_and_label():
    """The nav renders entries verbatim, so ``path`` and ``label`` are mandatory per entry."""
    routes = client.get("/meta/ui-routes").json()["routes"]
    assert len(routes) > 0
    for entry in routes:
        assert isinstance(entry["path"], str) and entry["path"].startswith("/")
        assert isinstance(entry["label"], str) and entry["label"]
        assert isinstance(entry["nav"], bool)


def test_ui_routes_excludes_performance_until_it_exists():
    """J-05 ships /performance WITH its nav entry; until then the map must not mention it."""
    body = client.get("/meta/ui-routes").text
    assert "performance" not in body.lower()


def test_ui_routes_top_bar_entries_match_the_rendered_nav_set():
    """The nav filters ``nav: true`` — exactly Cockpit / Journal / Studies today."""
    routes = client.get("/meta/ui-routes").json()["routes"]
    top_bar = [(r["path"], r["label"]) for r in routes if r["nav"]]
    assert top_bar == [("/", "Cockpit"), ("/journal", "Journal"), ("/studies", "Studies")]


def test_ui_routes_represents_journal_detail_honestly():
    """``/journal/[id]`` exists as a real page but is not a top-bar destination: present in the
    map (the map lists ALL live user-facing routes), excluded from the nav via ``nav: false``."""
    routes = client.get("/meta/ui-routes").json()["routes"]
    detail = [r for r in routes if r["path"] == "/journal/[id]"]
    assert len(detail) == 1
    assert detail[0]["nav"] is False
