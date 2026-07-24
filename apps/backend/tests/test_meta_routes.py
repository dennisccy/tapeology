"""``GET /meta/ui-routes`` — the canonical UI route map (Data Contract row 35, J-01).

The route-map module is the SINGLE owner of the list of user-facing routes: the rendered
top-bar navigation and the MCP ``ui_route_map`` tool both read this endpoint verbatim — no
hand-maintained duplicate list may exist anywhere else. The map lists exactly the LIVE routes
at all times (a route ships here in the same iteration its page ships).

era-5D J-02 ("The Clean Slate" demolition interlude): the four journal-era rows (``/journal``,
``/journal/[id]``, ``/studies``, ``/performance``) are deleted along with their pages — the map
now lists exactly the two KEPT routes, Cockpit and Structure. The dropped
``test_ui_routes_includes_performance_now_its_page_ships`` and
``test_ui_routes_represents_journal_detail_honestly`` asserted routes that no longer exist.

Uses a lifespan-less ``TestClient`` (the existing ``test_api.py`` precedent): the meta router
has no registry/engine dependencies, so no store injection is needed.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ui_routes_lists_exactly_the_live_routes():
    """The payload is byte-stable and lists exactly the two live routes, in nav order."""
    response = client.get("/meta/ui-routes")
    assert response.status_code == 200
    assert response.json() == {
        "routes": [
            {"path": "/", "label": "Cockpit", "nav": True},
            {"path": "/structure", "label": "Structure", "nav": True},
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


def test_ui_routes_includes_structure_now_its_page_ships():
    """J-01 (this interlude) ships /structure WITH its nav entry (page and entry land in the SAME
    iteration — the no-dead-link rule): exactly one ``/structure`` entry, labeled Structure,
    nav-true."""
    routes = client.get("/meta/ui-routes").json()["routes"]
    structure = [r for r in routes if r["path"] == "/structure"]
    assert len(structure) == 1
    assert structure[0] == {"path": "/structure", "label": "Structure", "nav": True}


def test_ui_routes_top_bar_entries_match_the_rendered_nav_set():
    """The nav filters ``nav: true`` — exactly Cockpit / Structure (two entries in the map, both
    top-bar destinations, per era-5D J-02's demolition of the journal/studies/performance rows)."""
    routes = client.get("/meta/ui-routes").json()["routes"]
    top_bar = [(r["path"], r["label"]) for r in routes if r["nav"]]
    assert len(routes) == 2
    assert top_bar == [
        ("/", "Cockpit"),
        ("/structure", "Structure"),
    ]
