"""``desk_playbook.py`` -- constants/parameters/signature liveness, ``PlaybookStore`` append-only
discipline, ``compute_playbook``'s session-refusal and per-symbol absence wiring, and
``GET /research/desk/playbook`` (Era B2, J-01). Also the whole-package structural guards (TC-15:
no ``setups``/``backtests`` import, no ``stop_loss`` field anywhere in a served signal) and the
copy-discipline lint (TC-16) that close out this iteration's test-first contract.

``test_desk_playbook_features.py`` covers the eight primitives in isolation and
``test_desk_playbook_detect.py`` covers the detector as a pure function of hand-built bars/dicts;
this file is the only one that plants real bars through a real ``BarStore`` and drives the full
``compute_playbook`` walk end to end."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.adapters.base import RawBar
from app.research import desk_playbook as desk_playbook_module
from app.research import desk_playbook_detect as desk_playbook_detect_module
from app.research import desk_playbook_features as desk_playbook_features_module
from app.research.bars import BarStore
from app.research.desk_forward import DESK_FORWARD_MAX_TOUCHES_PER_ROW, _measure_from
from app.research.desk_playbook import (
    PLAYBOOK_REGISTER,
    PlaybookAlreadyRecorded,
    PlaybookIntegrityError,
    PlaybookSessionRefused,
    PlaybookStore,
    _invalidation_breached,
    _measure_signal,
    _measurement_anchor,
    compute_playbook,
    compute_playbook_input_signature,
    playbook_parameters,
)
from app.research.desk_sessions import non_session_refusal, session_evidence
from app.research.desk_universe import UniverseStore
from test_copy_discipline import find_violations

SESSION_DATE = "2026-06-22"
E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET
_BASELINE_DATES = [f"2026-06-{d:02d}" for d in range(8, 18)]  # 10 prior dates < SESSION_DATE


def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
    return RawBar(symbol, timeframe, epoch, o, h, low, c, v)


def _plant(bar_store: BarStore, symbol: str, timeframe: str, bars: list[RawBar]) -> None:
    bar_store.record(
        symbol=symbol, timeframe=timeframe,
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
        feed="test", bars=bars,
    )


def _plant_baseline_sessions(bar_store: BarStore, symbol: str, dates: list[str] = _BASELINE_DATES) -> None:
    """10 prior RTH 5m sessions, 6 bars each, all identical (range 1.0, volume 1000) -> MBR=1.0,
    a full slot-volume-median vector. All dates are in June (EDT, no DST transition), so plain
    day arithmetic against E_OPEN resolves the SAME epoch a fresh ET conversion would."""
    bars = []
    for day in dates:
        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
        for slot in range(6):
            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    _plant(bar_store, symbol, "5m", bars)


def _plant_firing_session(bar_store: BarStore, symbol: str) -> None:
    """The canonical open_high_break session (test_desk_playbook_detect.py's hand-computed
    fixture, planted through a real BarStore this time): a narrow, 1m-basis opening range and a
    slot-3 trigger that breaks only the high side."""
    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),
        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _plant_gap_open_firing_session(bar_store: BarStore, symbol: str) -> None:
    """Same opening range as ``_plant_firing_session`` (or_high=101.0, 1m basis), but the trigger
    bar OPENS at/beyond ``or_high`` -- ``entry_kind == "gap_open"`` (TC-3)."""
    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 900.0, 101.2, 101.6, 101.1, 101.4, 1000),  # opens BEYOND 101.0
        _bar(symbol, "5m", E_OPEN + 1200.0, 101.4, 101.6, 101.2, 101.3, 800),
        _bar(symbol, "5m", E_OPEN + 1500.0, 101.3, 101.5, 101.0, 101.2, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _plant_full_1m_coverage_firing_session(bar_store: BarStore, symbol: str) -> None:
    """Like ``_plant_firing_session``, but the 1m series extends THROUGH the trigger's own 5m
    window (09:45-09:50), not just the opening range (09:30-09:45) -- exercises the "found a real
    1m bar inside the trigger window" branch of ``_measurement_anchor`` (the non-degraded path)."""
    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
    # The trigger 5m bar's own window: 09:45:00 .. 09:50:00 (5 one-minute bars), one of which
    # (100.9-101.3) actually contains T=101.0 in its [low, high].
    bars_1m += [
        _bar(symbol, "1m", E_OPEN + 900.0, 100.8, 100.95, 100.7, 100.9, 200),
        _bar(symbol, "1m", E_OPEN + 960.0, 100.9, 101.3, 100.85, 101.2, 400),  # contains T=101.0
        _bar(symbol, "1m", E_OPEN + 1020.0, 101.2, 101.4, 101.1, 101.3, 300),
        _bar(symbol, "1m", E_OPEN + 1080.0, 101.3, 101.4, 101.2, 101.3, 300),
        _bar(symbol, "1m", E_OPEN + 1140.0, 101.3, 101.4, 101.1, 101.1, 300),
    ]
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.4, 100.7, 101.1, 1200),  # trigger: breaks 101.0
        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _plant_5m_basis_firing_session(bar_store: BarStore, symbol: str) -> None:
    """Fewer than ``PLAYBOOK_OR_MIN_1M_BARS`` (10) one-minute bars on file -> the opening range
    degrades to the 5m basis -- closes audit T1's first gap as a ``compute_playbook``-LEVEL
    fixture (real ``BarStore`` walk), not just a features/detector-level hand-built dict."""
    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5, 500) for i in range(5)]
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),  # trigger
        _bar(symbol, "5m", E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, "5m", E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _plant_ambiguous_session(bar_store: BarStore, symbol: str) -> None:
    """A single 5m bar strictly breaking BOTH opening-range sides, neither previously broken --
    closes audit T1's second gap as a ``compute_playbook``-LEVEL fixture (real ``BarStore`` walk)."""
    bars_1m = [_bar(symbol, "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5, 500) for i in range(15)]
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, "5m", E_OPEN + 900.0, 100.5, 102.0, 99.0, 100.5, 1000),  # breaks BOTH sides
        _bar(symbol, "5m", E_OPEN + 1200.0, 100.5, 100.8, 100.2, 100.6, 800),
    ]
    _plant(bar_store, symbol, "1m", bars_1m)
    _plant(bar_store, symbol, "5m", bars_5m)


def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
    store = UniverseStore(tmp_path / "universe")
    store.record(
        members=members, raw_members={m: m for m in members},
        source_url="test", min_members=1, max_members=10,
    )
    return store


@pytest.fixture
def bar_store(tmp_path) -> BarStore:
    return BarStore(tmp_path / "bars")


@pytest.fixture
def universe_store(tmp_path) -> UniverseStore:
    return _register_universe(tmp_path, ["AAA", "THIN"])


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- compute_playbook: session refusal (TC-7) -----------------------------------------------------


def test_compute_playbook_refuses_a_known_non_session_date(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["AAA"])
    # Daily bars bracket 06-21 without recording it -- a provable non-session gap.
    for day in ("2026-06-19", "2026-06-20", "2026-06-22"):
        epoch = datetime.fromisoformat(f"{day}T00:00:00+00:00").timestamp()
        _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", epoch, 100.0, 101.0, 99.0, 100.0)])

    with pytest.raises(PlaybookSessionRefused) as exc_info:
        compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), "2026-06-21")

    evidence = session_evidence(bar_store, ["AAA"])
    assert str(exc_info.value) == non_session_refusal("2026-06-21", evidence)

    store = PlaybookStore(tmp_path / "playbook")
    assert store.list() == ([], [])  # nothing was ever written


# --- compute_playbook: per-symbol absences (TC-8) and a real firing signal ------------------------


def test_compute_playbook_records_a_thin_baseline_absence_beside_a_firing_signal(tmp_path, bar_store, universe_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    _plant_baseline_sessions(bar_store, "THIN", _BASELINE_DATES[:3])  # only 3 -- below the floor
    _plant_firing_session(bar_store, "THIN")  # has session bars, but the baseline gate fires first

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert [s["symbol"] for s in result["signals"]] == ["AAA"]
    assert result["signals"][0]["setup_id"] == "open_high_break"
    absence_symbols = {a["symbol"] for a in result["absences"]}
    assert absence_symbols == {"THIN"}
    assert "baseline too thin" in result["absences"][0]["reason"]
    assert result["diagnostics"] == []
    assert result["session_date"] == SESSION_DATE
    assert result["parameters"] == playbook_parameters()
    assert result["register"] == PLAYBOOK_REGISTER


def test_compute_playbook_records_a_no_bars_absence(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["NOBARS"])
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert result["signals"] == []
    assert result["absences"] == [
        {"symbol": "NOBARS", "reason": f"no 5m bars recorded for the {SESSION_DATE} session"}
    ]


# --- PlaybookStore: append-only discipline (TC-9, TC-11) --------------------------------------------


def _record_aaa(tmp_path, bar_store, universe_store) -> tuple[PlaybookStore, dict]:
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    store = PlaybookStore(tmp_path / "playbook")
    meta = store.record(**result)
    return store, meta


def test_duplicate_key_raises_and_leaves_the_recorded_file_byte_identical(tmp_path, bar_store, universe_store):
    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
    path = store._path(meta["id"])
    before = _sha256_file(path)

    duplicate_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    with pytest.raises(PlaybookAlreadyRecorded) as exc_info:
        store.record(**duplicate_result)
    assert meta["id"] in str(exc_info.value)
    assert _sha256_file(path) == before


def test_playbook_store_has_no_update_or_delete_method():
    assert not hasattr(PlaybookStore, "update")
    assert not hasattr(PlaybookStore, "delete")


def test_corrupt_file_checksum_is_surfaced_and_disk_is_untouched(tmp_path, bar_store, universe_store):
    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
    path = store._path(meta["id"])
    original_bytes = path.read_bytes()

    tampered = json.loads(original_bytes)
    tampered["record"]["meta"]["signals"] = []  # payload changed; file_checksum now stale
    path.write_text(json.dumps(tampered))

    with pytest.raises(PlaybookIntegrityError) as exc_info:
        store._load(path)
    assert path.name in str(exc_info.value)

    # `list()` withholds the corrupted file into `errors` rather than raising through the walk.
    records, errors = store.list()
    assert records == []
    assert len(errors) == 1 and errors[0]["file"] == path.name

    # The tamper itself is the only mutation; the store never rewrote it on either read attempt.
    assert path.read_bytes() == json.dumps(tampered).encode()


# --- parameters / signature liveness (TC-10) ---------------------------------------------------------


def test_monkeypatched_constant_moves_parameters_and_signature_and_mints_a_new_version(
    tmp_path, bar_store, universe_store, monkeypatch
):
    store, first_meta = _record_aaa(tmp_path, bar_store, universe_store)
    original_params = playbook_parameters()
    original_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())

    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_NARROW_OR_MAX_MBR", 999.0)

    moved_params = playbook_parameters()
    moved_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
    assert moved_params != original_params
    assert moved_params["narrow_or_max_mbr"] == 999.0
    assert moved_signature != original_signature

    second_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert second_result["playbook_input_signature"] == moved_signature
    second_meta = store.record(**second_result)  # does NOT raise -- a genuinely new key
    assert second_meta["id"] != first_meta["id"]

    newest, versions = store.newest_for_date(SESSION_DATE)
    assert versions == 2
    assert newest["id"] == second_meta["id"]
    # The original file is untouched by the second, differently-keyed write.
    assert store.get(first_meta["id"]) == first_meta


def test_compute_playbook_input_signature_is_deterministic(bar_store):
    _plant_baseline_sessions(bar_store, "AAA")
    fp = CONFIG.config_fingerprint()
    first = compute_playbook_input_signature(bar_store, ["AAA"], fp)
    second = compute_playbook_input_signature(bar_store, ["AAA"], fp)
    assert first == second
    different_members = compute_playbook_input_signature(bar_store, ["AAA", "ZZZ"], fp)
    assert different_members == first  # ZZZ has no recorded series -- contributes no tuples


# --- GET /research/desk/playbook (TC-1, TC-12) -------------------------------------------------------


@pytest.fixture
def playbook_client(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    return TestClient(app), tmp_path


def test_get_playbook_honest_empty(playbook_client):
    client, _tmp_path = playbook_client
    response = client.get("/research/desk/playbook")
    assert response.status_code == 200
    assert response.json() == {"playbooks": [], "latest": None, "integrity_errors": []}


def test_get_playbook_date_and_id_are_verbatim_reads(tmp_path, bar_store, monkeypatch):
    # A single-member universe (unlike the shared `universe_store` fixture's ["AAA", "THIN"]) so
    # this route-focused test's `counts` assertion isn't coupled to another test's absence fixture.
    solo_universe = _register_universe(tmp_path, ["AAA"])
    _, meta = _record_aaa(tmp_path, bar_store, solo_universe)
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    client = TestClient(app)

    by_date = client.get("/research/desk/playbook", params={"date": SESSION_DATE})
    assert by_date.status_code == 200
    body = by_date.json()
    assert body["versions"] == 1
    assert body["playbook"]["signals"] == meta["signals"]
    assert body["playbook"]["id"] == meta["id"]

    by_id = client.get("/research/desk/playbook", params={"id": meta["id"]})
    assert by_id.status_code == 200
    assert by_id.json() == {"playbook": meta}

    unknown_date = client.get("/research/desk/playbook", params={"date": "2099-01-01"})
    assert unknown_date.json() == {"playbook": None, "versions": 0}

    unknown_id = client.get("/research/desk/playbook", params={"id": "playbook-nope"})
    assert unknown_id.json() == {"playbook": None}

    both = client.get("/research/desk/playbook", params={"date": SESSION_DATE, "id": meta["id"]})
    assert both.status_code == 422

    bulk = client.get("/research/desk/playbook")
    assert bulk.status_code == 200
    bulk_body = bulk.json()
    assert bulk_body["latest"] == meta
    assert len(bulk_body["playbooks"]) == 1
    assert bulk_body["playbooks"][0]["id"] == meta["id"]
    assert bulk_body["playbooks"][0]["counts"] == {"signals": 1, "absences": 0, "diagnostics": 0}
    assert "signals" not in bulk_body["playbooks"][0]  # meta-only -- the bulk field is never served


# --- structural guards (TC-15) and copy discipline (TC-16) -------------------------------------------


def test_neither_playbook_module_imports_setups_or_backtests():
    for module in (
        desk_playbook_module, desk_playbook_detect_module, desk_playbook_features_module,
    ):
        source = open(module.__file__, encoding="utf-8").read()
        assert "import setups" not in source and "from .setups" not in source
        assert "import backtests" not in source and "from .backtests" not in source


def test_no_served_signal_field_is_ever_named_stop_loss(bar_store, universe_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    def _flatten_keys(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield key
                yield from _flatten_keys(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from _flatten_keys(item)

    keys = set(_flatten_keys(result))
    assert "stop_loss" not in keys
    assert "invalidation_price" in keys


def test_playbook_register_passes_copy_discipline():
    assert find_violations(PLAYBOOK_REGISTER) == []


# --- J-02: measurement -- convention identity (TC-1) --------------------------------------------


def test_measure_signal_and_measure_from_produce_byte_identical_leaves():
    """A synthetic anchor measured through ``_measure_signal`` (the playbook's own call site) and
    directly through ``desk_forward._measure_from`` with the identical resolved arguments produce
    byte-identical horizons/to_close_pct/mdd leaves."""
    session_5m = [
        _bar("SYN", "5m", E_OPEN + i * 300.0, 100.0 + i * 0.1, 100.5 + i * 0.1, 99.5 + i * 0.1, 100.2 + i * 0.1)
        for i in range(6)
    ]
    signal = {
        "geometry": {"slots_to_break": 2},
        "trigger_price": 100.7,
        "side": "long",
        "entry": 100.75,
        "entry_kind": "level",
        "invalidation_price": 99.0,
    }
    forward, breached, measure_bars, tf_minutes = _measure_signal(signal, session_5m, [])
    assert measure_bars is session_5m and tf_minutes == 5

    direct = _measure_from(session_5m, 2, 100.75, "level", 5, 1.0)
    assert forward == direct
    assert set(breached.keys()) == {"1m", "5m", "1h", "4h", "to_close", "first_breach_minutes"}


# --- J-02: truncation + gap_open entry reuse (TC-2, TC-3) ----------------------------------------


def test_truncated_horizon_reports_effective_minutes_and_last_bar_close(tmp_path, bar_store, universe_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    forward = result["signals"][0]["forward"]
    horizon_4h = forward["horizons"]["4h"]
    assert horizon_4h["truncated"] is True
    assert horizon_4h["effective_minutes"] < 240
    assert horizon_4h["exit_price"] == forward["close_price"]


def test_gap_open_entry_is_reused_verbatim_from_detection(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["GAP"])
    _plant_baseline_sessions(bar_store, "GAP")
    _plant_gap_open_firing_session(bar_store, "GAP")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    signal = result["signals"][0]
    assert signal["entry_kind"] == "gap_open"
    assert signal["forward"]["entry_price"] == signal["entry"]
    assert signal["forward"]["entry_kind"] == signal["entry_kind"]


# --- J-02: invalidation_breached (TC-4, TC-5, TC-6) -----------------------------------------------


def test_invalidation_breach_at_a_horizon_boundary_bar():
    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(7)]
    bars[5] = _bar("INV", "1m", E_OPEN + 5 * 60.0, 100.0, 100.2, 98.0, 99.0)  # breach at offset 5
    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
    breached = _invalidation_breached(bars, 0, 99.0, "long", 1, forward)
    assert breached["1m"] is False  # its own boundary (offset 1) is BEFORE the breach
    assert breached["5m"] is True  # breach lands exactly on the 5m horizon's own boundary
    assert breached["1h"] is True  # truncated (effective_minutes=6), but 5 <= 6
    assert breached["4h"] is True
    assert breached["to_close"] is True
    assert breached["first_breach_minutes"] == 5


def test_invalidation_breach_on_the_anchor_bar_itself():
    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(5)]
    bars[0] = _bar("INV", "1m", E_OPEN, 100.0, 100.2, 98.0, 99.5)  # breach at offset 0
    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
    breached = _invalidation_breached(bars, 0, 99.0, "long", 1, forward)
    assert all(breached[label] for label in ("1m", "5m", "1h", "4h", "to_close"))
    assert breached["first_breach_minutes"] == 0


def test_invalidation_never_breached_reports_null_first_breach_minutes():
    bars = [_bar("INV", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(5)]
    forward = _measure_from(bars, 0, 100.0, "level", 1, 1.0)
    breached = _invalidation_breached(bars, 0, 90.0, "long", 1, forward)  # never trades that low
    assert not any(breached[label] for label in ("1m", "5m", "1h", "4h", "to_close"))
    assert breached["first_breach_minutes"] is None


def test_invalidation_breach_mirrors_for_a_short_signal():
    bars = [_bar("INVS", "1m", E_OPEN + i * 60.0, 100.0, 100.2, 99.9, 100.0) for i in range(3)]
    bars[1] = _bar("INVS", "1m", E_OPEN + 60.0, 100.0, 101.5, 99.9, 101.0)  # breach at offset 1
    forward = _measure_from(bars, 0, 100.0, "level", 1, -1.0)
    breached = _invalidation_breached(bars, 0, 101.0, "short", 1, forward)
    assert breached["1m"] is True and breached["first_breach_minutes"] == 1


# --- J-02: baseline anchors -- determinism + cross-symbol independence (TC-7, TC-8) --------------


def test_baseline_anchors_are_seeded_and_reproducible(tmp_path, bar_store, universe_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    first = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    second = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert first["baseline_anchors"] == second["baseline_anchors"]
    pool = first["baseline_anchors"]["open_high_break:long"]
    assert len(pool) == 1  # k = min(this symbol's 1 signal, session bar count)
    assert pool[0]["entry_kind"] == "close"


def test_baseline_anchors_unchanged_by_an_unrelated_zero_signal_symbol(tmp_path, bar_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    solo_universe = _register_universe(tmp_path, ["AAA"])
    solo = compute_playbook(solo_universe, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    wider_universe = _register_universe(tmp_path, ["AAA", "ZZZ"])  # ZZZ: zero bars, zero signals
    wider = compute_playbook(wider_universe, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert wider["baseline_anchors"]["open_high_break:long"] == solo["baseline_anchors"]["open_high_break:long"]


# --- J-02: the pooling cap + beyond-cap disclosure (TC-9) -----------------------------------------


def test_signals_beyond_the_pooling_cap_are_disclosed_and_excluded_from_the_pool(tmp_path, bar_store):
    symbols = [f"SYM{i}" for i in range(DESK_FORWARD_MAX_TOUCHES_PER_ROW + 1)]  # 9 symbols, 1 over
    universe_store = _register_universe(tmp_path, symbols)
    for symbol in symbols:
        _plant_baseline_sessions(bar_store, symbol)
        _plant_firing_session(bar_store, symbol)

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert len(result["signals"]) == len(symbols)  # every symbol still gets a measured signal
    pool_key = "open_high_break:long"
    assert len(result["baseline_anchors"][pool_key]) == DESK_FORWARD_MAX_TOUCHES_PER_ROW
    assert result["summary"][pool_key]["to_close"]["signals"]["n"] == DESK_FORWARD_MAX_TOUCHES_PER_ROW
    assert result["signals_beyond_cap"] == {pool_key: len(symbols) - DESK_FORWARD_MAX_TOUCHES_PER_ROW}


# --- J-02: embedded rail-constant liveness (TC-10) ------------------------------------------------


def test_embedded_rail_baseline_seed_monkeypatch_moves_the_signature_and_mints_a_new_version(
    tmp_path, bar_store, universe_store, monkeypatch
):
    store, first_meta = _record_aaa(tmp_path, bar_store, universe_store)
    first_path = store._path(first_meta["id"])
    before = _sha256_file(first_path)
    original_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())

    monkeypatch.setattr(desk_playbook_module, "DESK_FORWARD_BASELINE_SEED", 42)

    moved_params = playbook_parameters()
    assert moved_params["rail_baseline_seed"] == 42
    moved_signature = compute_playbook_input_signature(bar_store, ["AAA"], CONFIG.config_fingerprint())
    assert moved_signature != original_signature

    second_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert second_result["playbook_input_signature"] == moved_signature
    second_meta = store.record(**second_result)  # does NOT raise -- a genuinely new key
    assert second_meta["id"] != first_meta["id"]
    assert _sha256_file(first_path) == before  # the original file is untouched


# --- J-02: a J-01-era (pre-measurement) record serves verbatim (TC-11) ----------------------------


def test_j01_era_record_serves_verbatim_with_honest_absence_and_unchanged_sha(tmp_path):
    """A record written BEFORE this iteration's measurement pass existed (no ``forward`` key on its
    signal, no ``baseline_anchors``/``summary``) reads back byte-unchanged through the route -- the
    honest absence is that the signal simply carries no ``forward`` block, never a backfilled one."""
    old_signal = {"symbol": "AAA", "setup_id": "open_high_break", "side": "long"}  # no `forward` key
    store = PlaybookStore(tmp_path / "playbook")
    meta = store.record(
        session_date=SESSION_DATE,
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="pretend-j01-era-signature",
        payload_version=1,
        parameters=playbook_parameters(),
        register="a pre-measurement J-01-era register string",
        signals=[old_signal],
        absences=[],
        diagnostics=[],
        # baseline_anchors / summary / signals_beyond_cap deliberately omitted -- the J-01 shape.
    )
    path = store._path(meta["id"])
    before = _sha256_file(path)

    reread = store.get(meta["id"])
    assert reread["signals"] == [old_signal]
    assert "forward" not in reread["signals"][0]
    assert "invalidation_breached" not in reread["signals"][0]
    assert reread["baseline_anchors"] == {}
    assert reread["summary"] == {}
    assert reread["signals_beyond_cap"] == {}
    assert _sha256_file(path) == before  # reading never rewrites the file


# --- J-02: audit T1 -- compute_playbook-LEVEL fixtures (TC-16, TC-17) -----------------------------


def test_5m_basis_degrade_fires_a_signal_through_a_real_barstore_walk(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["DEG"])
    _plant_baseline_sessions(bar_store, "DEG")
    _plant_5m_basis_firing_session(bar_store, "DEG")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert len(result["signals"]) == 1
    signal = result["signals"][0]
    assert signal["geometry"]["opening_range_basis"] == "5m"
    assert signal["forward"] is not None
    assert signal["forward"]["horizons"]["5m"]["return_pct"] is not None


def test_ambiguous_outside_bar_fires_no_signal_through_a_real_barstore_walk(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["AMB"])
    _plant_baseline_sessions(bar_store, "AMB")
    _plant_ambiguous_session(bar_store, "AMB")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert result["signals"] == []
    assert [d["diagnostic"] for d in result["diagnostics"]] == ["ambiguous_outside_bar"]


# --- J-02: the gapped-anchor-window degrade (TC-19) -----------------------------------------------


def test_gapped_1m_window_at_the_trigger_bar_degrades_honestly_to_5m_basis(tmp_path, bar_store, universe_store):
    """``_plant_firing_session``'s 1m series covers ONLY the opening range (09:30-09:45) -- the
    trigger's own 5m window (09:45-09:50) has ZERO 1m bars. The measurement must degrade to the 5m
    basis for THIS signal rather than borrow a bar from a neighboring window."""
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    forward = result["signals"][0]["forward"]
    assert forward["horizons"]["1m"]["reason"] == "the 1m horizon is finer than the 5m touch series"
    assert forward["horizons"]["5m"]["return_pct"] is not None  # measured on the 5m basis instead


def test_a_real_1m_bar_inside_the_trigger_window_is_used_when_available(tmp_path, bar_store):
    universe_store = _register_universe(tmp_path, ["FULL1M"])
    _plant_baseline_sessions(bar_store, "FULL1M")
    _plant_full_1m_coverage_firing_session(bar_store, "FULL1M")
    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    forward = result["signals"][0]["forward"]
    # measured on the genuine 1m basis this time -- the "1m" horizon IS resolvable.
    assert forward["horizons"]["1m"]["reason"] is None
    assert forward["horizons"]["1m"]["return_pct"] is not None


def test_measurement_anchor_falls_back_to_the_windows_first_1m_bar_when_none_contains_t():
    session_5m = [_bar("FB", "5m", E_OPEN + i * 300.0, 100.0, 100.5, 99.5, 100.2) for i in range(2)]
    # Neither 1m bar's [low, high] contains T=105.0 -- falls back to the window's FIRST 1m bar.
    session_1m = [
        _bar("FB", "1m", E_OPEN + 300.0, 100.0, 100.3, 99.8, 100.1),
        _bar("FB", "1m", E_OPEN + 360.0, 100.1, 100.4, 99.9, 100.2),
    ]
    measure_bars, anchor_index, tf_minutes = _measurement_anchor(session_5m, session_1m, 1, 105.0)
    assert measure_bars is session_1m and tf_minutes == 1
    assert measure_bars[anchor_index].epoch == E_OPEN + 300.0  # the window's first bar


# --- J-02: audit B3/B4 doc-only spec catch-ups leave source constants byte-unchanged (TC-20) ------


def test_b3_b4_spec_doc_catchups_leave_source_constants_byte_unchanged():
    """audit B3/B4: two documentation-only edits to ``docs/playbook-detector-spec.md`` -- zero
    code/value/behavior change. Asserts the spec doc now states both, AND that the exact source
    lines they describe are byte-unchanged from before this iteration."""
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    spec_text = (repo_root / "docs" / "playbook-detector-spec.md").read_text()
    assert "PLAYBOOK_OR_MIN_1M_BARS" in spec_text
    assert '`spike_into_trigger_verdict == "constructive"`' in spec_text

    playbook_source = pathlib.Path(desk_playbook_module.__file__).read_text()
    assert "PLAYBOOK_OR_MIN_1M_BARS: int = 10" in playbook_source

    detect_source = pathlib.Path(desk_playbook_detect_module.__file__).read_text()
    assert 'principles = ["P4"] if spike_verdict == "constructive" else []' in detect_source


# --- J-02: progress + should_abort wiring ----------------------------------------------------------


def test_compute_playbook_progress_and_should_abort_wiring(tmp_path, bar_store, universe_store):
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    seen: list[str] = []
    result = compute_playbook(
        universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE,
        progress=lambda entry: seen.append(entry["symbol"]),
    )
    assert seen == ["AAA", "THIN"]  # every member, in walk order, regardless of outcome
    assert len(result["signals"]) == 1

    aborted = compute_playbook(
        universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE,
        should_abort=lambda: True,
    )
    assert aborted["signals"] == [] and aborted["absences"] == []
