"""Thesis lifecycle honesty across interruptions (J-47): a marked position is never orphaned.

End-to-end over the real WatchManager + sim feeder + REST surface (the same dependency-override
pattern as test_research_resolve). Covers:
  * UT-J-47-A — an ENTRY-MARKED thesis SURVIVES Stop as active-but-not-evaluated; the canonical
    REST read serves it from the persisted record (monitor_status: not_evaluated + bound-source
    notice) via the SAME projection path; NO verdict events are appended after the stop.
  * UT-J-47-B — re-watching the MATCHING source resumes live evaluation and the journal timeline
    shows exactly ONE watch_restarted gap event at the re-attach, then post-restart verdicts only.
  * UT-J-47-C — an UNMARKED thesis Stop auto-resolves expired(watch_stopped); the strip returns to
    the declare affordance (active read is null) on re-watch.
  * Non-regression: an entry-marked thesis still refuses abandoned (409) including while
    not-evaluated.

The cross-source mismatch leg is unit-proven in test_research_monitor (the sim browser/REST
environment cannot produce a mismatched source for the same ticker — a sim ticker is bound to its
scenario), exactly as goal.md mandates.
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c, store, registry
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_until_state(c: TestClient, ticker: str, state: str, timeout: float = 12.0) -> float:
    r = c.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = c.get(f"/tape/{ticker}/summary").json()
        last = summary.get("market", {}).get("last")
        if last is not None and summary.get("tape_state") == state:
            return last
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


def _declare_long(c: TestClient, ticker: str, last: float) -> str:
    r = c.post(
        "/research/thesis",
        json={
            "ticker": ticker,
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 1.0, 2),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["thesis"]["id"]


def _mark_entry(c: TestClient, tid: str, price: float) -> None:
    r = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": price})
    assert r.status_code == 200, r.text


# --- UT-J-47-A: entry-marked thesis SURVIVES stop, served not-evaluated via the same path --------

def test_entry_marked_survives_stop_served_not_evaluated(client):
    c, store, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare_long(c, "SIM-BUYER", last)
    _mark_entry(c, tid, last)

    timeline_before = [e.verdict for e in store.verdict_events(tid)]

    # Stop the watch (a USER stop). The entry-marked thesis must survive, NOT expire.
    assert c.delete("/watch/SIM-BUYER").status_code == 200

    # Persisted status is still active (survived — never orphaned).
    assert store.get_thesis(tid).status == "active"
    # NO verdict event appended after the stop (nothing recorded while unwatched).
    assert [e.verdict for e in store.verdict_events(tid)] == timeline_before

    # The canonical REST read serves the surviving thesis from the persisted record — not null.
    body = c.get("/research/thesis/active", params={"ticker": "SIM-BUYER"}).json()
    thesis = body["thesis"]
    assert thesis is not None
    assert thesis["id"] == tid
    assert thesis["monitor_status"] == "not_evaluated"
    # The backend-owned plain-language notice names the bound source (rendered verbatim by the UI).
    assert "not currently evaluated" in thesis["monitor_notice"]
    assert thesis["bound_source"] in thesis["monitor_notice"]
    # The recorded entry mark is still present in the same projection (J-52 marks display).
    assert thesis["marks"]["has_entry"] is True
    assert thesis["marks"]["entry"] is not None
    assert thesis["marks"]["entry"]["price"] == last


# --- UT-J-47-B: re-attach on the matching source resumes + appends ONE watch_restarted gap -------

def test_reattach_matching_source_resumes_with_one_gap_event(client):
    c, store, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare_long(c, "SIM-BUYER", last)
    _mark_entry(c, tid, last)
    assert c.delete("/watch/SIM-BUYER").status_code == 200
    assert store.get_thesis(tid).status == "active"  # survived

    # Re-watch the SAME source (SIM-BUYER => same scenario => matching bound_source).
    _watch_until_state(c, "SIM-BUYER", "buyer_control")
    # Give the fresh monitor a few events to adopt + append the single gap event.
    deadline = time.time() + 8.0
    while time.time() < deadline:
        verdicts = [e.verdict for e in store.verdict_events(tid)]
        if "watch_restarted" in verdicts:
            break
        time.sleep(0.1)

    verdicts = [e.verdict for e in store.verdict_events(tid)]
    # Exactly ONE watch_restarted gap event (append-only — never interpolated/backfilled).
    assert verdicts.count("watch_restarted") == 1
    # The gap event comes AFTER the original declaration rows (post-restart, never inserted earlier).
    assert verdicts.index("watch_restarted") >= 1
    # No expiry was ever recorded for this surviving thesis.
    assert "expired" not in verdicts

    # The strip is live again (the active read no longer carries the not-evaluated flag).
    thesis = c.get("/research/thesis/active", params={"ticker": "SIM-BUYER"}).json()["thesis"]
    assert thesis is not None
    assert thesis["monitor_status"] == "ok"
    assert thesis["id"] == tid

    # The journal timeline (REST) shows the single gap event at the re-attach.
    timeline = c.get(f"/research/journal/{tid}").json()["timeline"]
    assert [r["verdict"] for r in timeline].count("watch_restarted") == 1


# --- UT-J-47-C: an UNMARKED thesis Stop auto-expires watch_stopped --------------------------------

def test_unmarked_stop_expires_watch_stopped_and_strip_returns_to_declare(client):
    c, store, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare_long(c, "SIM-BUYER", last)  # NO entry mark

    assert c.delete("/watch/SIM-BUYER").status_code == 200

    # Auto-resolved expired with the explicit watch_stopped reason (REST journal readback).
    assert store.get_thesis(tid).status == "expired"
    timeline = c.get(f"/research/journal/{tid}").json()["timeline"]
    assert timeline[-1]["verdict"] == "expired"
    assert "stopped the watch" in timeline[-1]["evidence"]

    # On re-watch the active read is null — the strip returns to the declare affordance.
    _watch_until_state(c, "SIM-BUYER", "buyer_control")
    assert c.get("/research/thesis/active", params={"ticker": "SIM-BUYER"}).json()["thesis"] is None


# --- non-regression: entry-marked thesis refuses abandoned (409) even while not-evaluated ---------

def test_entry_marked_refuses_abandoned_while_not_evaluated(client):
    c, store, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare_long(c, "SIM-BUYER", last)
    _mark_entry(c, tid, last)
    assert c.delete("/watch/SIM-BUYER").status_code == 200
    assert store.get_thesis(tid).status == "active"  # surviving, not-evaluated

    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "abandoned"})
    assert r.status_code == 409
    assert "cannot be abandoned" in r.json()["detail"]
    # Still active (the refusal mutated nothing).
    assert store.get_thesis(tid).status == "active"
