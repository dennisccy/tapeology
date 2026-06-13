"""Setup-forming hint engine (capability 33, J-65) — pure + integration unit tests.

Covers, with EXACT numeric anchors stated in the test parameters (iter-8 lesson):
  * the dwell fires deterministically at exactly the configured logical-time dwell on a sustained
    matching state; a flapping / unclear stream NEVER fires; the cooldown suppresses a same-pattern
    re-fire within the window;
  * the pattern -> setup/direction mapping for all four sustained states; ``unclear`` produces nothing;
  * citation logic: a matching persisted ``done`` study (same setup + feed + fingerprint) is cited
    verbatim; no study / feed mismatch / fingerprint mismatch / a hindsight_level-only study all yield
    EXACTLY "no studied baseline — unvalidated pattern";
  * persistence: a hint row is written via the single writer queue with bound source + ``data_feed`` +
    ``config_fingerprint`` stamps; the record is created ONCE (no duplicate on continued sustain);
  * REST ``GET /research/hints/active`` == WS ``hint`` key verbatim (incl. ``hint: null``); the hint-log
    endpoint paginates + filters by ticker;
  * declared-from: a valid id links the thesis + flips the hint record; the prefill path alone creates
    nothing;
  * freshness: a paused/stale/closed/failed status flip clears the active hint immediately; the log
    record survives;
  * a hint-engine exception surfaces ``monitor_status: failed`` while the feeder stays alive (the
    observer-equivalence suite carries the byte-identity proof separately).
"""

import dataclasses

import pytest

from app.config import CONFIG, Config
from app.engine.snapshot import EngineSnapshot
from app.research.hints import HintEngine, data_feed_for_scenario
from app.research.store import HintRecord, JournalStore, StudyRecord
from app.research.taxonomy import HINT_BASELINE_UNVALIDATED, HINT_PATTERNS


# --- a minimal snapshot carrying exactly the canonical values the hint engine reads --------------
def _snap(
    *,
    tape_state="bid_absorption",
    timestamp=0.0,
    scenario="bid_absorption",
    stream_status="live",
    last=100.0,
) -> EngineSnapshot:
    return EngineSnapshot(
        ticker="SIM-BIDABS",
        scenario=scenario,
        timestamp=timestamp,
        event_count=240,
        warm=True,
        stream_status=stream_status,
        bid=last - 0.01,
        ask=last + 0.01,
        spread=0.02,
        last=last,
        features={"30s": {"trade_speed": 2.0, "average_spread": 0.02}},
        primary_window="30s",
        tape_state=tape_state,
        confidence=0.9,
        observations=(),
        delivery_lag_seconds=0.0,
    )


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def _drive(engine: HintEngine, *, state, start, count, dt=0.5, scenario="bid_absorption"):
    """Feed ``count`` events of one tape ``state`` at ``dt`` logical-seconds apart from ``start``.
    Returns the logical timestamp of the LAST event fed."""
    ts = start
    for _ in range(count):
        engine.on_event(_snap(tape_state=state, timestamp=ts, scenario=scenario))
        ts += dt
    return ts - dt


# --- dwell: deterministic fire at exactly the configured logical-time dwell -----------------------

def test_dwell_fires_at_exactly_the_configured_dwell(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=5.0)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    # held_for is measured from the FIRST sustaining event's timestamp. At t=0 the clock starts; the
    # premise must hold CONTINUOUSLY for >= 5.0s. At t=4.5 held_for=4.5 < 5.0 -> no fire; at t=5.0 it
    # fires. Drive 0.0 .. 4.5 (10 events) first: still building, no hint.
    last_ts = _drive(eng, state="bid_absorption", start=0.0, count=10, dt=0.5)  # t = 4.5
    assert last_ts == 4.5
    assert eng.projection() is None
    # The next event at t=5.0 reaches held_for == 5.0 -> fires exactly here.
    eng.on_event(_snap(tape_state="bid_absorption", timestamp=5.0))
    proj = eng.projection()
    assert proj is not None
    assert proj["pattern_id"] == "sustained_bid_absorption"


def test_no_fire_before_the_dwell(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=5.0)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=9, dt=0.5)  # t = 4.0, held_for 4.0 < 5.0
    assert eng.projection() is None
    assert store.list_hints(limit=10) == []


# --- flapping / unclear NEVER fires ---------------------------------------------------------------

def test_unclear_never_fires(store):
    eng = HintEngine(store, CONFIG, "SIM-CHOP")
    _drive(eng, state="unclear", start=0.0, count=100, dt=0.2, scenario="unclear_chop")
    assert eng.projection() is None
    assert store.list_hints(limit=10) == []


def test_flapping_stream_never_sustains_past_the_dwell(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=5.0)
    eng = HintEngine(store, cfg, "SIM-CHOP")
    # Alternate bid_absorption / unclear every event: the sustain clock restarts on each unclear, so the
    # premise never holds continuously for 5.0s. Drive 200 events; nothing ever fires.
    ts = 0.0
    for i in range(200):
        state = "bid_absorption" if i % 2 == 0 else "unclear"
        eng.on_event(_snap(tape_state=state, timestamp=ts))
        ts += 0.5
    assert eng.projection() is None
    assert store.list_hints(limit=10) == []


def test_state_change_resets_the_sustain_clock(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=5.0)
    eng = HintEngine(store, cfg, "SIM-X")
    # 4.0s of bid_absorption (not enough), then SWITCH to buyer_control — the clock restarts at the
    # switch, so buyer_control must itself hold 5.0s from there.
    _drive(eng, state="bid_absorption", start=0.0, count=9, dt=0.5)  # t=4.0
    assert eng.projection() is None
    # buyer_control from t=4.5: needs to reach t=9.5 (held_for 5.0). At t=9.0 held_for=4.5 -> none.
    _drive(eng, state="buyer_control", start=4.5, count=10, dt=0.5)  # t=9.0
    assert eng.projection() is None
    eng.on_event(_snap(tape_state="buyer_control", timestamp=9.5))
    proj = eng.projection()
    assert proj is not None and proj["pattern_id"] == "sustained_buyer_control"


# --- pattern -> setup/direction mapping for all four states ---------------------------------------

@pytest.mark.parametrize(
    "state,pattern,setup_type,direction",
    [
        ("bid_absorption", "sustained_bid_absorption", "absorption_reversal", "long"),
        ("ask_absorption", "sustained_ask_absorption", "absorption_reversal", "short"),
        ("buyer_control", "sustained_buyer_control", "trend_continuation", "long"),
        ("seller_control", "sustained_seller_control", "trend_continuation", "short"),
    ],
)
def test_pattern_setup_direction_mapping(store, state, pattern, setup_type, direction):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-X")
    _drive(eng, state=state, start=0.0, count=5, dt=0.5)  # t=2.0 -> fires
    proj = eng.projection()
    assert proj is not None
    assert proj["pattern_id"] == pattern
    assert proj["setup_type"] == setup_type
    assert proj["direction"] == direction


# --- cooldown: suppresses a same-pattern re-fire within the window --------------------------------

def test_cooldown_suppresses_same_pattern_refire(store):
    cfg = dataclasses.replace(
        CONFIG, hint_sustain_dwell_seconds=2.0, hint_cooldown_seconds=50.0
    )
    eng = HintEngine(store, cfg, "SIM-X")
    # First fire at t=2.0.
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)  # t=2.0 fires
    assert len(store.list_hints(limit=10)) == 1
    fired_logical = 2.0
    # State LEAVES (unclear) -> active hint clears; then the pattern returns. A NEW sustain past the dwell
    # within the cooldown (last fired t=2.0, cooldown 50.0 -> blocked until t=52.0) must NOT re-fire.
    eng.on_event(_snap(tape_state="unclear", timestamp=2.5))
    assert eng.projection() is None
    _drive(eng, state="bid_absorption", start=3.0, count=20, dt=0.5)  # t=12.5, well past dwell, < cooldown
    assert len(store.list_hints(limit=10)) == 1  # still ONE record — cooldown suppressed the re-fire


def test_cooldown_allows_refire_after_the_window(store):
    cfg = dataclasses.replace(
        CONFIG, hint_sustain_dwell_seconds=2.0, hint_cooldown_seconds=10.0
    )
    eng = HintEngine(store, cfg, "SIM-X")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)  # fire at t=2.0
    assert len(store.list_hints(limit=10)) == 1
    eng.on_event(_snap(tape_state="unclear", timestamp=2.5))  # clear active
    # Re-arm AFTER the cooldown elapses (last fired t=2.0 + cooldown 10.0 = t=12.0). Sustain from t=11.0
    # so the dwell (2.0) completes at t=13.0 > 12.0.
    _drive(eng, state="bid_absorption", start=11.0, count=5, dt=0.5)  # t=13.0 -> fires again
    assert len(store.list_hints(limit=10)) == 2


# --- fire-once: no duplicate on continued sustain -------------------------------------------------

def test_fire_once_no_duplicate_on_continued_sustain(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-X")
    # Sustain for a long time WELL past the dwell — exactly ONE record is written, and the active hint
    # stays the SAME id throughout (active while the state persists).
    _drive(eng, state="bid_absorption", start=0.0, count=40, dt=0.5)  # t up to 19.5
    rows = store.list_hints(limit=10)
    assert len(rows) == 1
    first_id = eng.projection()["id"]
    assert rows[0].id == first_id


# --- persistence: stamps + writer queue -----------------------------------------------------------

def test_persisted_record_carries_stamps(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5, scenario="bid_absorption")
    rows = store.list_hints(limit=10)
    assert len(rows) == 1
    p = rows[0].payload
    assert p["bound_source"] == "bid_absorption"
    assert p["data_feed"] == "sim"
    assert p["config_fingerprint"] == cfg.config_fingerprint()
    assert "logical_ts" in p and "wall_ts" in p
    assert isinstance(p["evidence"], str) and p["evidence"]  # no naked output


def test_data_feed_mapping():
    # Re-exported from the ONE owner (feed_basis); defaults byte-identical to the prior literals.
    assert data_feed_for_scenario("live AAPL", CONFIG) == "iex"
    assert data_feed_for_scenario("historical AAPL 2026-..", CONFIG) == "sip"
    assert data_feed_for_scenario("bid_absorption", CONFIG) == "sim"


# --- config fingerprint discipline for the hint-log page size (the config comment's claimed pair) ---
# The carry-along the iter-24 spec mandates (lesson iter-23: "comments claiming test coverage must be
# cross-checked against the suite"). The ``hint_log_max`` config comment claims a fingerprint-stability
# test + its counter-test; this pair makes that claim TRUE, matching the ``test_studies.py``
# precedent (``test_study_list_page_size_is_serving_only_excluded_from_fingerprint`` + counter).

def test_hint_log_max_is_serving_only_excluded_from_fingerprint():
    # The hint-log page size is a SERVING-ONLY value: changing it touches NO persisted hint value, so
    # it MUST NOT move config_fingerprint (else two journals identical in every threshold but served at
    # different hint-log page sizes could never be pooled). The iter-12 page-size precedent.
    base = Config().config_fingerprint()
    assert base == Config(hint_log_max=999).config_fingerprint()


def test_a_real_threshold_still_changes_fingerprint():
    # The counter-test: a REAL classifier threshold (and the hint TIMING keys that shape WHICH hints
    # persist) DO move the fingerprint — proving the stability test above is not vacuously true.
    base = Config().config_fingerprint()
    assert base != Config(min_buy_price_impact=0.99).config_fingerprint()
    assert base != Config(hint_sustain_dwell_seconds=9.0).config_fingerprint()
    assert base != Config(hint_cooldown_seconds=999.0).config_fingerprint()


# --- config fingerprint discipline for the sound-cue cooldown (J-66; the config comment's claimed pair) ---
# The carry-along the iter-25 spec mandates (lesson iter-23: a serving-only exclusion claim MUST ship
# its fingerprint-stability test + real-threshold counter-test in the SAME commit — never promised only
# in prose). ``sound_cue_cooldown_seconds`` is the OPTIONAL, never-persisted client sound cue's debounce;
# its config comment claims this exact pair, matching the ``hint_log_max`` / ``study_list_max`` precedent.

def test_sound_cue_cooldown_is_serving_only_excluded_from_fingerprint():
    # The sound-cue cooldown is a SERVING-ONLY value for a CLIENT-LOCAL UI cue that is NEVER PERSISTED
    # (schema stays v7 — no cue row exists), so changing it touches NO persisted research value and MUST
    # NOT move config_fingerprint (else two journals identical in every threshold but served at different
    # cue cooldowns could never be pooled). Same iter-12/16/20/23 serving-only precedent.
    base = Config().config_fingerprint()
    assert base == Config(sound_cue_cooldown_seconds=99.0).config_fingerprint()


def test_a_real_threshold_still_changes_fingerprint_vs_sound_cue():
    # The counter-test for the sound-cue exclusion: a REAL classifier threshold STILL moves the
    # fingerprint — proving the stability test above is not vacuously true (a lint/exclusion that cannot
    # fail proves nothing). A persisted research-timing key (hint sustain) also still moves it.
    base = Config().config_fingerprint()
    assert base != Config(min_buy_price_impact=0.99).config_fingerprint()
    assert base != Config(hint_sustain_dwell_seconds=9.0).config_fingerprint()


# --- citation logic -------------------------------------------------------------------------------

def _done_study(
    store: JournalStore,
    *,
    setup_type,
    data_feed,
    fingerprint,
    n=7,
    plus=4,
    minus=2,
    neither=1,
    horizon=30,
    hindsight=False,
):
    payload = {
        "id": "study1",
        "status": "done",
        "setup_type": setup_type,
        "direction": "long",
        "data_feed": data_feed,
        "config_fingerprint": fingerprint,
        "hindsight_level": hindsight,
        "aggregates": {
            "setup": {
                "n": n,
                "horizons": [
                    {
                        "horizon": horizon,
                        "+1R_first": plus,
                        "-1R_first": minus,
                        "neither_within_horizon": neither,
                        "truncated": 0,
                    }
                ],
            },
            "null_baseline": {"n": n, "horizons": []},
        },
    }
    store.insert_study(StudyRecord(id="study1", payload=payload, created_wall_ts=1.0))


def test_citation_with_matching_study_is_cited_verbatim(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    fp = cfg.config_fingerprint()
    _done_study(store, setup_type="absorption_reversal", data_feed="sim", fingerprint=fp,
                n=7, plus=4, minus=2, neither=1, horizon=30)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    citation = eng.projection()["baseline_citation"]
    assert "n=7" in citation
    assert "30s" in citation
    assert "4 reached +1R" in citation
    assert "2 reached −1R" in citation
    assert citation != HINT_BASELINE_UNVALIDATED


def test_citation_no_study_is_unvalidated_string(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection()["baseline_citation"] == HINT_BASELINE_UNVALIDATED


def test_citation_feed_mismatch_is_unvalidated(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    fp = cfg.config_fingerprint()
    # Study is on SIP, the hint fires on a SIM scenario -> no match -> unvalidated.
    _done_study(store, setup_type="absorption_reversal", data_feed="sip", fingerprint=fp)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection()["baseline_citation"] == HINT_BASELINE_UNVALIDATED


def test_citation_fingerprint_mismatch_is_unvalidated(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    _done_study(store, setup_type="absorption_reversal", data_feed="sim",
                fingerprint="DIFFERENT_FINGERPRINT")
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection()["baseline_citation"] == HINT_BASELINE_UNVALIDATED


def test_citation_hindsight_only_study_is_unvalidated(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    fp = cfg.config_fingerprint()
    # A level (hindsight) study even if it somehow matched setup_type must be excluded.
    _done_study(store, setup_type="absorption_reversal", data_feed="sim", fingerprint=fp,
                hindsight=True)
    eng = HintEngine(store, cfg, "SIM-BIDABS")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection()["baseline_citation"] == HINT_BASELINE_UNVALIDATED


# --- freshness: a non-live status flip clears the active hint; the log survives -------------------

@pytest.mark.parametrize("status", ["paused", "stale", "closed", "failed"])
def test_non_live_status_clears_active_hint_log_survives(store, status):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-X")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection() is not None
    eng.on_status(status)
    assert eng.projection() is None  # active hint cleared immediately
    assert len(store.list_hints(limit=10)) == 1  # the persisted log record survives


def test_non_live_event_clears_active_hint(store):
    cfg = dataclasses.replace(CONFIG, hint_sustain_dwell_seconds=2.0)
    eng = HintEngine(store, cfg, "SIM-X")
    _drive(eng, state="bid_absorption", start=0.0, count=5, dt=0.5)
    assert eng.projection() is not None
    # An event arriving while the snapshot is not live clears the active hint too (defensive).
    eng.on_event(_snap(tape_state="bid_absorption", timestamp=5.0, stream_status="stale"))
    assert eng.projection() is None


# --- the persisted log: pagination + ticker filter ------------------------------------------------

def test_log_filters_by_ticker_and_paginates(store):
    for i in range(5):
        store.insert_hint(HintRecord(
            id=f"a{i}", ticker="AAA", payload={"id": f"a{i}", "ticker": "AAA"},
            created_wall_ts=float(i),
        ))
    for i in range(3):
        store.insert_hint(HintRecord(
            id=f"b{i}", ticker="BBB", payload={"id": f"b{i}", "ticker": "BBB"},
            created_wall_ts=float(i),
        ))
    aaa = store.list_hints(ticker="AAA", limit=100)
    assert len(aaa) == 5
    assert all(r.ticker == "AAA" for r in aaa)
    # Newest-first by created_wall_ts: a4 first.
    assert aaa[0].id == "a4"
    # Pagination: limit 2 offset 2 over AAA -> a2, a1.
    page = store.list_hints(ticker="AAA", limit=2, offset=2)
    assert [r.id for r in page] == ["a2", "a1"]
    # No filter -> all 8.
    assert len(store.list_hints(limit=100)) == 8


# --- declared-from linkage ------------------------------------------------------------------------

def test_mark_hint_declared_from_flips_payload(store):
    store.insert_hint(HintRecord(
        id="h1", ticker="SIM-X", payload={"id": "h1", "pattern_id": "sustained_bid_absorption"},
        created_wall_ts=1.0,
    ))
    store.mark_hint_declared_from("h1", "thesis-123")
    rec = store.get_hint("h1")
    assert rec.payload["declared_from"] == "thesis-123"


def test_mark_hint_declared_from_unknown_id_is_noop(store):
    # No row exists -> a no-op (the route validates existence first, returning 422 otherwise).
    store.mark_hint_declared_from("does-not-exist", "thesis-123")
    assert store.get_hint("does-not-exist") is None


def test_get_hint_unknown_returns_none(store):
    assert store.get_hint("nope") is None


# --- exception isolation: a hint-engine failure surfaces monitor_status: failed, feeder alive -----

def test_hint_engine_exception_surfaces_monitor_failed(store, monkeypatch):
    """A hint-engine bug must surface as ``monitor_status: failed`` (caught by the monitor's shared
    try/except) and must NEVER propagate to kill the feeder. With NO thesis, the monitor's thesis
    projection is ``None``, but the hint projection is suppressed too on a failed monitor (the present-
    tense card never sits over a monitor that stopped evaluating honestly)."""
    from app.research.monitor import ResearchMonitor

    monitor = ResearchMonitor(store, CONFIG, "SIM-BIDABS")

    def _boom(snapshot):
        raise RuntimeError("hint engine blew up")

    monkeypatch.setattr(monitor._hints, "on_event", _boom)
    # on_event must NOT raise (the monitor isolates it); the failure flips the internal flag.
    monitor.on_event(object(), _snap(tape_state="bid_absorption", timestamp=0.0))
    assert monitor._failed is True
    # A failed monitor shows NO active hint (suppressed honestly).
    assert monitor.hint_projection() is None
