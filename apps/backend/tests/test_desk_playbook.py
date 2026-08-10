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
from app.research.desk_playbook import (
    PLAYBOOK_REGISTER,
    PlaybookAlreadyRecorded,
    PlaybookIntegrityError,
    PlaybookSessionRefused,
    PlaybookStore,
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
