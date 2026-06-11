"""Review save flow + grades + final statuses end-to-end (J-55 / J-56 / J-57).

End-to-end against the real engine (a watched SIM ticker) + a hermetic temp-path journal store:
  * the review endpoint validation matrix (404 / 422 unknown-tag / 422 other-without-note / 409
    unresolved / 409 already-reviewed / success persists verbatim + flips reviewed);
  * grades computed ONCE at resolution and served by GET /research/journal/{id} + on rows;
  * per-statement FINAL statuses persisted at resolution and served by the detail;
  * the J-56 quadrants: an invalidated clean-checks thesis grades thesis_failed × clean; a
    flagged-process played-out thesis grades thesis_held × flagged;
  * the append-only verdict_events surface is UNTOUCHED by a review.

Each test injects a TEMP-PATH store + registry via the existing dependency-override pattern.
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
        yield c, store
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


def _declare(c: TestClient, ticker: str, last: float, **over) -> str:
    body = {
        "ticker": ticker,
        "setup_type": "trend_continuation",
        "direction": "long",
        "invalidation_price": round(last - 0.5, 2),
    }
    body.update(over)
    r = c.post("/research/thesis", json=body)
    assert r.status_code == 200, r.text
    return r.json()["thesis"]["id"]


def _resolve(c: TestClient, tid: str, resolution: str = "played_out") -> None:
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": resolution})
    assert r.status_code == 200, r.text


# --- grades + final statuses computed at resolution, served by the detail ------------------------

def test_resolution_computes_grades_and_final_statuses_served_verbatim(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)

    # Pre-resolution: detail OMITS grades + final statuses; reviewed is the False fact.
    pre = c.get(f"/research/journal/{tid}").json()
    assert "grades" not in pre
    assert "statement_final_statuses" not in pre
    assert pre["reviewed"] is False

    _resolve(c, tid, "played_out")
    detail = c.get(f"/research/journal/{tid}").json()
    # Grades present, enum labels, evidence-backed (no naked grade), 1:1 outcome from resolution.
    assert detail["grades"]["outcome"] == "thesis_held"
    assert detail["grades"]["process"] in {"clean", "flagged", "violated"}
    assert isinstance(detail["grades"]["process_evidence"], str) and detail["grades"]["process_evidence"]
    # Per-statement FINAL statuses: one per frozen statement, each a valid enum.
    fin = detail["statement_final_statuses"]
    assert len(fin) == len(detail["thesis"]["statements"])
    for s in fin:
        assert s["status"] in {"not_yet", "met", "violated", "not_evaluated"}
    # Served VERBATIM (a re-read never recomputes — byte-identical).
    again = c.get(f"/research/journal/{tid}").json()
    assert again["grades"] == detail["grades"]
    assert again["statement_final_statuses"] == fin


def test_grades_and_reviewed_on_journal_rows(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    # Pre-resolution row: grades absent, reviewed False.
    rows = c.get("/research/journal").json()["rows"]
    row = next(r for r in rows if r["id"] == tid)
    assert "grades" not in row
    assert row["reviewed"] is False
    _resolve(c, tid, "played_out")
    rows = c.get("/research/journal").json()["rows"]
    row = next(r for r in rows if r["id"] == tid)
    assert row["grades"]["outcome"] == "thesis_held"
    assert row["reviewed"] is False  # resolved but not reviewed


# --- J-56 quadrant: invalidated clean-process => thesis_failed × clean ----------------------------

def test_invalidated_clean_checks_grades_thesis_failed_times_clean(client):
    # SIM-SHIFT: warm control phase, declare trend_continuation/long with no risk flags, invalidation
    # under the later chop band -> the tape resolves it invalidated. With no marks (no failed
    # execution check) and no fired flag the PROCESS grades CLEAN — being invalidated is never itself
    # a process failure.
    c, store = client
    last = _watch_until_state(c, "SIM-SHIFT", "buyer_control")
    # SIM-SHIFT walks trade prices UP to ~100.4 during the control phase, then the chop phase prints
    # land at exactly 100.00 (the shift-chop center). An invalidation BETWEEN the chop center (100.00)
    # and the warmed late-control last is crossed when the chop dip prints at 100.00 -> the tape
    # resolves it invalidated. 100.05 is comfortably above the chop center and (with last ~100.1+) well
    # outside the too-tight band (2x the ~0.02 spread = 0.04), so NO risk flag fires.
    assert last >= 100.10, f"SIM-SHIFT warmed too early (last={last}); cannot place a clean invalidation"
    tid = _declare(c, "SIM-SHIFT", last, invalidation_price=100.05)
    # The clean-process leg REQUIRES no risk flag fired at declaration (else it is not a clean leg).
    assert (store.get_thesis(tid).risk_flags or []) == [], "expected no risk flags for the clean leg"
    # Wait for the system to auto-resolve invalidated.
    deadline = time.time() + 20.0
    status = None
    while time.time() < deadline:
        status = store.get_thesis(tid).status
        if status in ("invalidated", "expired", "played_out", "abandoned"):
            break
        time.sleep(0.2)
    assert status == "invalidated", f"expected invalidated, got {status}"
    detail = c.get(f"/research/journal/{tid}").json()
    assert detail["grades"]["outcome"] == "thesis_failed"
    assert detail["grades"]["process"] == "clean"
    # Evidence states the invalidation-is-not-a-process-failure invariant explicitly.
    assert "process" in detail["grades"]["process_evidence"].lower()


# --- J-56 quadrant: flagged-process played-out => thesis_held × flagged ---------------------------

def test_flagged_process_played_out_grades_thesis_held_times_flagged(client):
    # A genuinely-firing risk flag at declaration (invalidation_too_tight — deterministic) makes the
    # PROCESS flagged; resolving played_out makes the OUTCOME thesis_held.
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    # An invalidation within ~$0.04 of last fires invalidation_too_tight (2x the ~$0.02 sim spread).
    tid = _declare(c, "SIM-BUYER", last, invalidation_price=round(last - 0.02, 2))
    # Verify the flag actually fired at declaration (else the leg is invalid).
    thesis = store.get_thesis(tid)
    fired = {f["flag"] for f in (thesis.risk_flags or [])}
    assert "invalidation_too_tight" in fired, f"expected invalidation_too_tight to fire, got {fired}"
    _resolve(c, tid, "played_out")
    detail = c.get(f"/research/journal/{tid}").json()
    assert detail["grades"]["outcome"] == "thesis_held"
    assert detail["grades"]["process"] == "flagged"
    assert "invalidation too tight" in detail["grades"]["process_evidence"].lower()


# --- review endpoint validation matrix (J-57) -----------------------------------------------------

def test_review_unknown_id_is_404(client):
    c, _ = client
    r = c.post("/research/thesis/nope/review", json={"mistake_tags": []})
    assert r.status_code == 404


def test_review_unresolved_thesis_is_409(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["overstayed"]})
    assert r.status_code == 409


def test_review_unknown_tag_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    r = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["not_a_real_tag"]})
    assert r.status_code == 422


def test_review_other_without_note_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    r = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["other"]})
    assert r.status_code == 422
    # A blank note also fails.
    r = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["other"], "note": "   "})
    assert r.status_code == 422


def test_review_success_persists_verbatim_and_flips_reviewed(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    r = c.post(
        f"/research/thesis/{tid}/review",
        json={"mistake_tags": ["overstayed", "other"], "note": "held too long"},
    )
    assert r.status_code == 200, r.text
    body = r.json()["review"]
    assert body["reviewed"] is True
    assert body["mistake_tags"] == ["overstayed", "other"]
    assert body["note"] == "held too long"
    # Persisted + served by the detail VERBATIM (re-open the detail).
    detail = c.get(f"/research/journal/{tid}").json()
    assert detail["reviewed"] is True
    assert detail["review"]["mistake_tags"] == ["overstayed", "other"]
    assert detail["review"]["note"] == "held too long"
    # The reviewed flag lands on the journal row.
    row = next(rr for rr in c.get("/research/journal").json()["rows"] if rr["id"] == tid)
    assert row["reviewed"] is True


def test_review_already_reviewed_is_409(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    r1 = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["overstayed"]})
    assert r1.status_code == 200
    r2 = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["chased"]})
    assert r2.status_code == 409


def test_review_does_not_touch_verdict_timeline(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    timeline_before = [(e.verdict, e.evidence) for e in store.verdict_events(tid)]
    r = c.post(f"/research/thesis/{tid}/review", json={"mistake_tags": ["overstayed"]})
    assert r.status_code == 200
    timeline_after = [(e.verdict, e.evidence) for e in store.verdict_events(tid)]
    # The append-only timeline is byte-identical — a review never edits/appends the timeline.
    assert timeline_after == timeline_before


def test_suggested_tags_distinct_from_confirmed_tags(client):
    # The machine-SUGGESTED tags (row 19) are never auto-recorded as the review (row 28). Until the
    # user saves, no confirmed tags exist.
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid, "played_out")
    detail = c.get(f"/research/journal/{tid}").json()
    # Suggested tags are present (row 19 — may be empty); reviewed is False (no confirmed tags yet).
    assert "suggested_mistake_tags" in detail
    assert detail["reviewed"] is False
    assert "review" not in detail
