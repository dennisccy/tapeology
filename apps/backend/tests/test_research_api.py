"""Research API (capability 23/24): POST /research/thesis validation matrix (404/409/422 both
directions), nothing persisted on rejection, taxonomy endpoint, REST==WS thesis projection verbatim.

Each test injects a TEMP-PATH journal store + registry (the existing dependency-override pattern)
so the suite stays hermetic — no real journal file is written. The app's module-level WatchManager
is wired to the registry's engine-created hook for the duration of the test."""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    # Inject a temp-path store + registry BEFORE the app starts, so the lifespan leaves it in place
    # (skips building the default file store). Wire the WatchManager hook to it.
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c
    # Teardown: stop any leftover watches, clear the registry + hook, close the store.
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_bidabs(client: TestClient) -> None:
    """Watch SIM-BIDABS and wait until it warms to bid_absorption with a last price."""
    r = client.post("/watch/SIM-BIDABS")
    assert r.status_code == 200
    deadline = time.time() + 10
    while time.time() < deadline:
        summary = client.get("/tape/SIM-BIDABS/summary").json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == "bid_absorption":
            return
        time.sleep(0.1)
    raise AssertionError("SIM-BIDABS did not warm to bid_absorption in time")


def _watch_until_state(client: TestClient, ticker: str, state: str, timeout: float = 12.0) -> None:
    r = client.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = client.get(f"/tape/{ticker}/summary").json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == state:
            return
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


# --- taxonomy ------------------------------------------------------------------------------------

def test_taxonomy_endpoint_lists_setups_directions_verdicts(client):
    payload = client.get("/research/taxonomy").json()
    setup_ids = {s["id"] for s in payload["setups"]}
    assert setup_ids == {
        "absorption_reversal",
        "trend_continuation",
        "level_break",
        "failed_move_fade",
    }
    # The per-setup level requirement is taxonomy-owned (the frontend hardcodes none of it).
    by_id = {s["id"]: s for s in payload["setups"]}
    assert by_id["level_break"]["requires_level"] is True
    assert by_id["failed_move_fade"]["requires_level"] is True
    assert by_id["absorption_reversal"]["requires_level"] is False
    assert by_id["trend_continuation"]["requires_level"] is False
    assert {d["id"] for d in payload["directions"]} == {"long", "short"}
    assert "pending" in {v["id"] for v in payload["verdicts"]}
    assert payload["disclaimer"].startswith("Descriptive only")


def test_taxonomy_serves_management_stance_catalog_canary(client):
    # The management-stance catalog (capability 27, J-53; row 25 stance half) is backend-owned —
    # served by GET /research/taxonomy. This is ALSO iter-20's code-identity canary: the presence of
    # `management_stances` here proves the NEW server code is live before any browser capture.
    payload = client.get("/research/taxonomy").json()
    assert "management_stances" in payload
    stances = {s["id"]: s["name"] for s in payload["management_stances"]}
    assert stances == {
        "thesis_intact": "Thesis intact",
        "thesis_weakening": "Thesis weakening",
        "thesis_invalidated": "Thesis invalidated",
    }
    # The two DISTINCT honest-absence copies (iter-15 lesson: one fallback must not cover two causes).
    absence = payload["stance_absence"]
    assert "no_entry_mark" in absence and "not_evaluated" in absence
    assert absence["no_entry_mark"] != absence["not_evaluated"]
    # The journaled-measurement readout caption (consistent with the realized-R register).
    assert "R = |entry" in payload["stance_readout_caption"]
    # Copy discipline (J-66): no imperative trade words in any new stance string.
    blob = " ".join(
        [s["name"] for s in payload["management_stances"]]
        + list(absence.values())
        + [payload["stance_readout_caption"]]
    ).lower()
    for word in (" buy ", " sell ", " enter ", " exit ", "should "):
        assert word not in f" {blob} ", f"imperative word {word!r} in stance copy"


def test_taxonomy_serves_entry_checklist_catalog_canary(client):
    # The entry-checklist catalog (capability 33, J-63; row 25 checklist half) is backend-owned —
    # served by GET /research/taxonomy. ALSO iter-21's code-identity canary: `checklist_checks` here
    # proves the NEW server code is live before any browser capture.
    payload = client.get("/research/taxonomy").json()
    assert "checklist_checks" in payload
    checks = {c["id"]: c for c in payload["checklist_checks"]}
    assert set(checks.keys()) == {
        "verdict_confirming", "warm", "feed_live", "tape_lag_ok",
        "spread_stable", "trade_speed_ok", "invalidation_distance_ok", "not_chasing",
    }
    # Each check carries a display label + a unit caption (the strip hardcodes none).
    for c in checks.values():
        assert c["name"] and c["caption"]
    stances = {s["id"]: s["name"] for s in payload["checklist_stances"]}
    assert stances == {
        "conditions_met": "Conditions met",
        "conditions_not_met": "Conditions not met",
        "tape_against": "Tape against",
        "no_fresh_tape": "No fresh tape",
    }
    assert "no_fresh_tape" in payload["checklist_absence"]
    # Copy discipline (J-66): no imperative / predictive words in any new checklist string.
    blob = " ".join(
        [c["name"] for c in checks.values()]
        + [c["caption"] for c in checks.values()]
        + list(stances.values())
        + list(payload["checklist_absence"].values())
    ).lower()
    for word in (" buy ", " sell ", " enter ", " exit ", "should ", "will ", "predict", "target"):
        assert word not in f" {blob} ", f"forbidden word {word!r} in checklist copy"


def test_checklist_keys_rest_equals_ws_verbatim_on_pre_entry_mark_path(client):
    # The entry-checklist keys served on the PRE-entry-mark path are byte-identical across REST
    # (/research/thesis/active) and the WS `thesis` key (one projection, never a second path — the
    # J-08 single-source discipline). A declared, NOT-yet-entry-marked thesis carries the checklist.
    _watch_bidabs(client)
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert declared.status_code == 200
    rest = client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"]
    assert rest is not None
    assert "entry_checklist" in rest  # pre-entry-mark => checklist present
    assert "management_stance" not in rest  # mutually exclusive
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        ws_thesis = ws.receive_json()["thesis"]
    assert "entry_checklist" in ws_thesis
    rest_cl = rest["entry_checklist"]
    ws_cl = ws_thesis["entry_checklist"]
    # The stance value + label + the eight check ids match verbatim across both reads (the margins
    # themselves are computed once server-side; the per-read snapshot can differ by a live tick, so we
    # assert the stable structural identity — the J-08 single-projection discipline).
    assert rest_cl["stance"]["value"] == ws_cl["stance"]["value"]
    assert rest_cl["stance"]["label"] == ws_cl["stance"]["label"]
    assert [c["check"] for c in rest_cl["checks"]] == [c["check"] for c in ws_cl["checks"]]
    assert rest_cl["total"] == ws_cl["total"] == 8


def test_taxonomy_serves_mistake_tag_catalog_with_display_copy(client):
    # The mistake-tag catalog (capability 29, J-54) is backend-owned — served by GET
    # /research/taxonomy with display copy so the review picker is taxonomy-driven (the frontend
    # hardcodes none of it). The full goal.md catalog must be present.
    payload = client.get("/research/taxonomy").json()
    assert "mistake_tags" in payload
    tags = {t["id"]: t for t in payload["mistake_tags"]}
    assert set(tags.keys()) == {
        "chased",
        "entered_before_confirmation",
        "ignored_rejection",
        "ignored_risk_flags",
        "moved_invalidation",
        "no_clear_setup",
        "wrong_setup_type",
        "overstayed",
        "other",
    }
    # Every tag carries a non-empty display label.
    for t in tags.values():
        assert isinstance(t["name"], str) and t["name"]
    # `other` requires a free-text note (enforced in the J-57 save flow); the others do not.
    assert tags["other"]["requires_note"] is True
    assert tags["chased"]["requires_note"] is False


def test_check_suggested_tag_mapping_targets_exist_in_catalog():
    # The check → suggested-tag mapping must only point at real catalog tags (no fabricated tag).
    from app.research.taxonomy import CHECK_SUGGESTED_TAG, MISTAKE_TAGS

    for check, tag in CHECK_SUGGESTED_TAG.items():
        assert tag in MISTAKE_TAGS, f"{check} suggests unknown tag {tag}"


# --- 404 / 409 -----------------------------------------------------------------------------------

def test_declare_on_unwatched_ticker_is_404_nothing_persisted(client):
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 404
    # Nothing persisted on rejection.
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None


def test_valid_declare_then_second_is_409(client):
    _watch_bidabs(client)
    body = {
        "ticker": "SIM-BIDABS",
        "setup_type": "absorption_reversal",
        "direction": "long",
        "invalidation_price": 99.0,
    }
    r1 = client.post("/research/thesis", json=body)
    assert r1.status_code == 200
    r2 = client.post("/research/thesis", json=body)
    assert r2.status_code == 409
    assert "active thesis" in r2.json()["detail"].lower()


# --- 422 validation matrix -----------------------------------------------------------------------

def test_wrong_side_invalidation_long_is_422_nothing_persisted(client):
    _watch_bidabs(client)
    # last == 100.0; a LONG invalidation at/above last is wrong-side.
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 101.0,
        },
    )
    assert r.status_code == 422
    assert "below" in r.json()["detail"].lower()
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None


def test_wrong_side_invalidation_short_is_422(client):
    _watch_bidabs(client)
    # A SHORT invalidation at/below last is wrong-side.
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "trend_continuation",
            "direction": "short",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "above" in r.json()["detail"].lower()


def test_level_setup_without_level_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "level_break",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "level" in r.json()["detail"].lower()


def test_non_level_setup_with_level_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
            "level_price": 100.5,
        },
    )
    assert r.status_code == 422
    assert "does not take a level" in r.json()["detail"].lower()


def test_unknown_setup_enum_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "moon_shot",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "setup_type" in r.json()["detail"].lower()


def test_unknown_direction_enum_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "sideways",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "direction" in r.json()["detail"].lower()


# --- success projection --------------------------------------------------------------------------

def test_valid_declare_returns_full_projection_and_pending(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 200
    thesis = r.json()["thesis"]
    assert thesis["setup_type"] == "absorption_reversal"
    assert thesis["direction"] == "long"
    assert thesis["invalidation_price"] == 99.0
    assert thesis["verdict"] == "pending"
    assert thesis["bound_source"] == "bid_absorption"  # scenario descriptor, not the ticker
    assert thesis["data_feed"] == "sim"
    assert thesis["config_fingerprint"] == CONFIG.config_fingerprint()
    # Entry risk flags (capability 26, J-49) are now PRESENT — a list (not omitted). This clean,
    # warm, on-premise declare with a normal invalidation fires nothing, so the list is EMPTY
    # (assessed, nothing fired — distinct from the ABSENT key a pre-v4 thesis would carry).
    assert thesis["risk_flags"] == []
    assert len(thesis["statements"]) == 2
    assert all("status" in s and "text" in s for s in thesis["statements"])
    # The initial pending verdict event is recorded (timeline starts at declaration).
    assert thesis["monitor_status"] == "ok"


def test_active_read_null_is_normal_before_any_declare(client):
    _watch_bidabs(client)
    r = client.get("/research/thesis/active?ticker=SIM-BIDABS")
    assert r.status_code == 200
    assert r.json()["thesis"] is None  # a normal state, not an error


def test_rest_active_equals_ws_thesis_key_verbatim(client):
    _watch_bidabs(client)
    client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    rest = client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"]
    assert rest is not None
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        frame = ws.receive_json()
    ws_thesis = frame["thesis"]
    # Data-contract row 15: the WS thesis key MUST equal the REST projection verbatim. Both come
    # from the SAME monitor.projection(); the only fields that can drift are the live statement
    # statuses (recomputed per call from the current snapshot). Assert the stable thesis fields are
    # byte-identical and statuses are from the same enum.
    for key in (
        "id",
        "setup_type",
        "direction",
        "invalidation_price",
        "level_price",
        "verdict",
        "bound_source",
        "data_feed",
        "config_fingerprint",
        "entry_context",
        "monitor_status",
        # Capability 25 / J-48: geometry is part of the row-15 projection, so the WS thesis key MUST
        # carry it verbatim too (one builder, one projection). The price-lines are time-independent
        # and fully stable between the two reads; the markers (verdict-transition rows) come from the
        # same append-only timeline. Assert byte-equality of the whole geometry object.
        "geometry",
        # Capability 26 / J-49: risk_flags is part of the row-15 projection, FROZEN at declaration and
        # re-exposed verbatim by the single build_projection — so REST and WS carry byte-identical
        # flags (here an empty list — a clean on-premise declare — proving the key flows, not just a
        # coincidental match). Extended exactly as iter-10 did for geometry.
        "risk_flags",
    ):
        assert rest[key] == ws_thesis[key], f"REST/WS diverged on {key}"
    # The risk_flags key is really present and a list (not absent), shaped as the frozen flag set.
    assert isinstance(rest["risk_flags"], list)
    assert [s["text"] for s in rest["statements"]] == [s["text"] for s in ws_thesis["statements"]]
    # An absorption_reversal (no level) declares only the invalidation line — sanity that geometry is
    # really present and shaped, not an empty dict that happens to match.
    assert {pl["kind"] for pl in rest["geometry"]["price_lines"]} == {"invalidation"}


def test_rest_active_equals_ws_thesis_key_with_management_stance(client):
    # The J-53 stance keys flow through the SAME single projection — so REST /thesis/active and the WS
    # thesis key carry them verbatim. Declare + mark an entry, then read both: the entry-marked thesis
    # carries the management_stance + distance_to_invalidation + open_r keys identically.
    _watch_bidabs(client)
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    ).json()
    thesis_id = declared["thesis"]["id"]
    # Record an entry mark via the route (price recorded verbatim) — the stance keys then appear.
    mark = client.post(
        f"/research/thesis/{thesis_id}/action",
        json={"kind": "entry", "price": 100.5},
    )
    assert mark.status_code == 200
    rest = client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"]
    assert rest is not None
    # The entry mark is recorded => the stance keys are present.
    assert "management_stance" in rest
    assert rest["management_stance"]["value"] in (
        "thesis_intact",
        "thesis_weakening",
        "thesis_invalidated",
    )
    assert rest["management_stance"]["evidence"]  # no naked stance
    assert "distance_to_invalidation" in rest and "open_r" in rest
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        ws_thesis = ws.receive_json()["thesis"]
    # The stable stance keys are byte-identical across REST and WS (one projection, never a second
    # path). open_r / distance can move with the live last between the two reads, so assert the stance
    # value + label + the key SHAPES match (the J-08 single-projection discipline).
    assert rest["management_stance"]["value"] == ws_thesis["management_stance"]["value"]
    assert rest["management_stance"]["label"] == ws_thesis["management_stance"]["label"]
    assert set(rest["distance_to_invalidation"].keys()) == {"dollars", "r"}
    assert set(ws_thesis["distance_to_invalidation"].keys()) == {"dollars", "r"}
    assert rest["geometry"]["price_lines"][0]["price"] == 99.0


def test_ws_thesis_key_is_null_when_none(client):
    _watch_bidabs(client)
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        frame = ws.receive_json()
    assert "thesis" in frame
    assert frame["thesis"] is None


# --- GET /research/journal/{id} (capability 24 / blueprint row-16 serving slice) -----------------

def test_journal_entry_unknown_id_is_404(client):
    r = client.get("/research/journal/does-not-exist")
    assert r.status_code == 404


def test_journal_entry_serves_thesis_and_persisted_timeline_verbatim(client):
    _watch_bidabs(client)
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    ).json()["thesis"]
    tid = declared["id"]

    entry = client.get(f"/research/journal/{tid}").json()
    # The thesis record is served verbatim (frozen context + statements + stamps).
    assert entry["thesis"]["id"] == tid
    assert entry["thesis"]["setup_type"] == "absorption_reversal"
    assert entry["thesis"]["bound_source"] == "bid_absorption"
    assert entry["thesis"]["data_feed"] == "sim"
    assert len(entry["thesis"]["statements"]) == 2
    # The append-only timeline holds at least the initial pending row (the declaration started it),
    # each with plain-language evidence (no naked verdicts).
    assert len(entry["timeline"]) >= 1
    assert entry["timeline"][0]["verdict"] == "pending"
    assert entry["timeline"][0]["evidence"]  # non-empty
    # Every timeline row carries the timing-record fields (None for the initial pending row).
    for row in entry["timeline"]:
        assert "rule_first_true_ts" in row
        assert "rule_first_true_price" in row


def test_journal_timeline_records_confirming_transition(client):
    # End-to-end through the API + observer: a watched SIM-BUYER trend_continuation/long confirms,
    # and the confirming transition lands on the persisted timeline with its dwell timing record.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": 98.0,
        },
    ).json()["thesis"]
    tid = declared["id"]
    assert declared["verdict"] == "pending"

    # Wait for the verdict to publish confirming (after the logical dwell) via the live observer.
    deadline = time.time() + 12
    confirming = False
    while time.time() < deadline:
        proj = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
        if proj and proj["verdict"] == "confirming":
            confirming = True
            break
        time.sleep(0.1)
    assert confirming, "verdict never published confirming"

    entry = client.get(f"/research/journal/{tid}").json()
    verdicts = [row["verdict"] for row in entry["timeline"]]
    assert "pending" in verdicts and "confirming" in verdicts
    assert verdicts.index("confirming") > verdicts.index("pending")  # append-only order
    confirm_row = next(r for r in entry["timeline"] if r["verdict"] == "confirming")
    # The confirming row carries plain-language evidence and the dwell timing record.
    assert "confirms your thesis" in confirm_row["evidence"].lower()
    assert confirm_row["rule_first_true_ts"] is not None
    assert confirm_row["logical_ts"] >= confirm_row["rule_first_true_ts"]


def test_invalidated_thesis_shows_terminal_projection_not_idle(client):
    # SIM-SELLER drops price; a long thesis invalidates. The active projection then reports the
    # TERMINAL invalidated state (verdict + status invalidated), NOT null/idle, so the strip shows
    # the terminal treatment rather than reverting to the declare affordance.
    _watch_until_state(client, "SIM-SELLER", "seller_control")
    summary = client.get("/tape/SIM-SELLER/summary").json()
    last = summary["market"]["last"]
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-SELLER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 0.05, 2),
        },
    )
    assert declared.status_code == 200
    tid = declared.json()["thesis"]["id"]

    deadline = time.time() + 12
    invalidated = False
    while time.time() < deadline:
        proj = client.get("/research/thesis/active?ticker=SIM-SELLER").json()["thesis"]
        if proj and proj["verdict"] == "invalidated":
            invalidated = True
            assert proj["status"] == "invalidated"
            assert proj["verdict_evidence"]  # the offending evidence, never a naked verdict
            break
        time.sleep(0.1)
    assert invalidated, "thesis never auto-resolved invalidated"

    # The persisted timeline's final row is the invalidation, with the offending print recorded.
    entry = client.get(f"/research/journal/{tid}").json()
    final = entry["timeline"][-1]
    assert final["verdict"] == "invalidated"
    assert final["last"] is not None
    assert final["evidence"]


class _FaultInjectingConn:
    """Proxy around the writer connection that raises on a targeted INSERT (``sqlite3.Connection`` is
    an immutable C type and cannot be monkeypatched directly)."""

    def __init__(self, conn, fail_on: str) -> None:
        import sqlite3 as _sqlite3

        self._conn = conn
        self._fail_on = fail_on
        self._OperationalError = _sqlite3.OperationalError

    def execute(self, sql, *args, **kwargs):
        if isinstance(sql, str) and self._fail_on in sql:
            raise self._OperationalError("injected fault on the initial verdict-event insert")
        return self._conn.execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def test_declare_atomicity_event_insert_failure_surfaces_503_and_persists_nothing(client):
    # A failure DURING the single declaration transaction must surface an explicit API error (503)
    # AND leave NO thesis row — the declaration is one atomic writer transaction now, so a thesis row
    # without its initial verdict event can no longer exist (the iter-4 orphan defect).
    _watch_bidabs(client)

    from app.research.routes import get_registry

    store = get_registry().store
    real_conn = store._write_conn
    store._write_conn = _FaultInjectingConn(real_conn, "INSERT INTO verdict_events")
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    store._write_conn = real_conn  # restore before the clean declare + teardown
    assert r.status_code == 503  # honest, explicit error — never a silent half-save
    # Nothing partially saved: the canonical active read is still null and a clean declare now works.
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None
    ok = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert ok.status_code == 200  # no orphan 409 from the failed attempt


# --- entry risk flags end-to-end through the API (capability 26, J-49) ---------------------------

def test_declare_on_extended_buyer_move_carries_chasing_entry_flag(client):
    # A trend_continuation/long declared on a well-past-warm-up SIM-BUYER (an extended move) carries a
    # frozen ``chasing_entry`` flag with its measured margin — surfaced on the declaration response.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    # Let the move extend a little past warm-up so the favorable return clears the chase threshold.
    # The canonical reference_price lives in the full /features windows; buy_price_impact divided by
    # it is the EXACT relative impact metric compute_risk_flags reads.
    deadline = time.time() + 10
    while time.time() < deadline:
        windows = client.get("/tape/SIM-BUYER/features").json()["windows"]
        pf = windows[client.get("/tape/SIM-BUYER/features").json()["primary_window"]]
        ref = pf.get("reference_price")
        bi = pf.get("buy_price_impact")
        if ref and bi is not None and (bi / ref) > CONFIG.chase_return_threshold:
            break
        time.sleep(0.1)
    last = client.get("/tape/SIM-BUYER/summary").json()["market"]["last"]
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 1.0, 2),  # a normal (not too tight) invalidation
        },
    )
    assert declared.status_code == 200
    thesis = declared.json()["thesis"]
    flags = {f["flag"]: f for f in thesis["risk_flags"]}
    assert "chasing_entry" in flags, f"expected chasing_entry, got {list(flags)}"
    chase = flags["chasing_entry"]
    assert chase["label"]  # taxonomy-owned chip title, present
    assert "chase threshold" in chase["evidence"]  # plain-language measured margin
    assert chase["measured"]["threshold"] == CONFIG.chase_return_threshold
    assert chase["measured"]["impact_return"] > CONFIG.chase_return_threshold


def test_risk_flags_are_frozen_as_the_tape_moves_on(client):
    # The flags are a record of the ENTRY MOMENT — they do NOT change as the tape moves. Two reads of
    # the active projection, separated by live ticks, return byte-identical risk_flags.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": 98.0,
        },
    )
    assert declared.status_code == 200
    first = declared.json()["thesis"]["risk_flags"]
    time.sleep(1.5)  # let the live tape move on (more buyer-control ticks)
    later = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["risk_flags"]
    assert later == first  # frozen — never re-evaluated as the tape moves


def test_journal_detail_carries_frozen_risk_flags(client):
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": 98.0,
        },
    )
    tid = declared.json()["thesis"]["id"]
    flags_at_declare = declared.json()["thesis"]["risk_flags"]
    entry = client.get(f"/research/journal/{tid}").json()
    # Row 17: the journal detail re-exposes the SAME frozen flags verbatim (no second computation).
    assert entry["thesis"]["risk_flags"] == flags_at_declare


def test_wrong_side_invalidation_is_422_with_no_flags_computed(client):
    # Advisory never substitutes for validation: an incoherent (wrong-side) invalidation stays a 422
    # with NOTHING persisted — no thesis row, no flags. (A long's invalidation must be BELOW the last.)
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    last = client.get("/tape/SIM-BUYER/summary").json()["market"]["last"]
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last + 1.0, 2),  # ABOVE the last — wrong side for a long
        },
    )
    assert r.status_code == 422
    # Nothing persisted (no thesis, so no flags) — the canonical active read is still null.
    assert client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"] is None


def test_maximally_flagged_declare_still_succeeds_advisory_never_blocking(client):
    # An early SIM-CHOP declare (before warm-up, slow tape, too-tight invalidation) stacks several
    # flags — creation STILL succeeds (200), flags attached. Advisory, never blocking.
    r = client.post("/watch/SIM-CHOP")
    assert r.status_code == 200
    # Declare promptly (before warm-up) — wait only for a last price to exist so validation can run,
    # while the engine is still NOT warm (the canonical warm flag lives on /state).
    deadline = time.time() + 8
    last = None
    while time.time() < deadline:
        last = client.get("/tape/SIM-CHOP/summary").json().get("market", {}).get("last")
        warm = client.get("/tape/SIM-CHOP/state").json().get("warm", True)
        if last is not None and not warm:
            break
        time.sleep(0.02)
    assert last is not None
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-CHOP",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 0.01, 2),  # extremely tight
        },
    )
    assert declared.status_code == 200  # advisory — creation succeeds despite the stack of flags
    names = {f["flag"] for f in declared.json()["thesis"]["risk_flags"]}
    assert "before_warmup" in names  # declared before warm-up
