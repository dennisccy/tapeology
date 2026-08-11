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
import random
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
from app.research.desk_forward import (
    DESK_FORWARD_MAX_TOUCHES_PER_ROW,
    _draw_anchor_indices,
    _measure_from,
)
from app.research.desk_playbook import (
    PLAYBOOK_REGISTER,
    PlaybookAlreadyRecorded,
    PlaybookIntegrityError,
    PlaybookSessionRefused,
    PlaybookStore,
    _baseline_seed,
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


# --- goal-playbook-iter-3 (J-03): the sign-duplication consolidation (TC-10) -----------------------

import re as _re  # noqa: E402 -- kept local to this guard section, mirroring the test's own scope


def _strip_python_docstrings_and_comments(source: str) -> str:
    """A source-introspection guard must scan CODE, not the prose that explains it -- this
    module's own `side_sign` docstring necessarily discusses the literal it replaces and the
    rail's `_side_sign` it is deliberately NOT, which would otherwise false-positive the very
    guards below (the ``test_desk_ui_guards.py``/``test_desk_refresh_chain_guard.py``
    comment-stripping precedent, applied to Python: triple-quoted docstrings and ``#`` comments
    are removed; ordinary single/double-quoted string literals in real code are left alone)."""
    without_triple = _re.sub(r'"""(?:.|\n)*?"""', "", source)
    without_triple = _re.sub(r"'''(?:.|\n)*?'''", "", without_triple)
    return _re.sub(r"#[^\n]*", "", without_triple)


def test_no_playbook_module_still_writes_the_inline_sign_literal():
    """The one owner is now `desk_playbook_features.side_sign` -- the literal
    ``1.0 if side == "long" else -1.0`` (in either quote style) must appear nowhere in
    `desk_playbook.py`'s or `desk_playbook_detect.py`'s own CODE any more (every former call site
    -- `desk_playbook.py`'s `_measure_signal` and `compute_playbook`'s baseline-draw branch,
    `desk_playbook_detect.py`'s `_market_block` -- now calls `side_sign` instead), and appears
    EXACTLY ONCE in `desk_playbook_features.py` -- `side_sign`'s own function body, the single
    canonical implementation the other two modules now call instead of repeating."""
    literal_variants = (
        '1.0 if side == "long" else -1.0',
        "1.0 if side == 'long' else -1.0",
        '1.0 if signal["side"] == "long" else -1.0',
    )
    for module in (desk_playbook_module, desk_playbook_detect_module):
        source = _strip_python_docstrings_and_comments(open(module.__file__, encoding="utf-8").read())
        for literal in literal_variants:
            assert literal not in source, (
                f"{module.__file__} still writes the inline sign literal {literal!r} -- it must "
                "call desk_playbook_features.side_sign instead (the single owner)"
            )

    features_source = _strip_python_docstrings_and_comments(
        open(desk_playbook_features_module.__file__, encoding="utf-8").read()
    )
    assert features_source.count('1.0 if side == "long" else -1.0') == 1, (
        "the literal must appear EXACTLY ONCE in desk_playbook_features.py -- side_sign's own "
        "single canonical implementation, never a second copy"
    )


def test_no_playbook_module_imports_desk_forwards_side_sign():
    """`desk_forward._side_sign` is built exclusively for the rail's own support/resistance
    vocabulary -- importing it into a playbook module's CODE would silently flip every short
    signal's sign positive (see `side_sign`'s own docstring, which is exactly why this scan strips
    docstrings before looking). Zero diff to `desk_forward.py` itself."""
    for module in (desk_playbook_module, desk_playbook_detect_module, desk_playbook_features_module):
        source = _strip_python_docstrings_and_comments(open(module.__file__, encoding="utf-8").read())
        assert "_side_sign" not in source, (
            f"{module.__file__} references _side_sign in its own code -- the playbook must use its "
            "OWN desk_playbook_features.side_sign, never desk_forward's"
        )


def test_measure_signal_and_baseline_draw_both_call_the_shared_side_sign():
    """Counter-test: proves the source-scan above actually distinguishes the fixed source from the
    old, un-consolidated one -- a literal reintroduced anywhere in real CODE (not merely prose) is
    still caught after stripping."""
    seeded_source = 'sign = 1.0 if signal["side"] == "long" else -1.0\n'
    stripped = _strip_python_docstrings_and_comments(seeded_source)
    assert '1.0 if signal["side"] == "long" else -1.0' in stripped

    seeded_docstring_only = '"""mentions 1.0 if side == "long" else -1.0 in prose only."""\n'
    assert '1.0 if side == "long" else -1.0' not in _strip_python_docstrings_and_comments(
        seeded_docstring_only
    )

    playbook_source = open(desk_playbook_module.__file__, encoding="utf-8").read()
    assert playbook_source.count("side_sign(signal[\"side\"])") == 2  # _measure_signal + baseline draw
    detect_source = open(desk_playbook_detect_module.__file__, encoding="utf-8").read()
    assert "side_sign(side)" in detect_source


# --- goal-playbook-iter-3 (J-03): desk_routes.py drops the unused import (TC-13) --------------------


def test_desk_routes_no_longer_imports_playbook_session_refused():
    """`PlaybookSessionRefused` is caught internally by `desk_playbook_compute.py`, never by the
    route layer -- the import at `desk_routes.py` was dead. The app still starts and serves
    cleanly with it removed."""
    from app.research import desk_routes as desk_routes_module

    source = open(desk_routes_module.__file__, encoding="utf-8").read()
    assert "PlaybookSessionRefused" not in source
    response = TestClient(app).get("/research/desk/playbook")
    assert response.status_code == 200


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


def test_baseline_seed_at_firing_index_zero_matches_the_original_recipe_literal():
    """TC-12: `firing_index=0`'s seed carries NO discriminator suffix at all -- byte-identical to
    the pre-fix literal recipe (`f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:
    {setup_id}"`)."""
    seed0 = _baseline_seed(SESSION_DATE, "AAA", "open_high_break", 0)
    assert seed0 == f"1729:playbook-{SESSION_DATE}:AAA:open_high_break"
    from app.research.desk_forward import DESK_FORWARD_BASELINE_SEED

    assert seed0 == f"{DESK_FORWARD_BASELINE_SEED}:playbook-{SESSION_DATE}:AAA:open_high_break"


def test_single_firing_baseline_draw_uses_firing_index_zero(monkeypatch, tmp_path, bar_store, universe_store):
    """TC-12: every currently-recordable signal (opening-range-break fires at most once per
    symbol-session) draws its baseline anchor at `firing_index=0` -- the ONE case
    `_baseline_seed` reproduces byte-identically to the pre-fix recipe (the test above). Combined,
    these two prove the seed-collision fix is a genuine no-op for any signal this iteration's
    detectors can actually produce."""
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_firing_session(bar_store, "AAA")
    calls: list[tuple] = []
    original = desk_playbook_module._baseline_seed

    def _spy(session_date, symbol, setup_id, firing_index):
        calls.append((session_date, symbol, setup_id, firing_index))
        return original(session_date, symbol, setup_id, firing_index)

    monkeypatch.setattr(desk_playbook_module, "_baseline_seed", _spy)
    compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert calls == [(SESSION_DATE, "AAA", "open_high_break", 0)]


def test_seed_collision_fix_reproduces_byte_identical_output_for_recordable_data(
    tmp_path, bar_store, universe_store
):
    """TC-12: record the canonical single-fire fixture, then run a FRESH compute over the identical
    inputs post-fix -- every byte of the result (especially `baseline_anchors`/`summary`) matches,
    and re-recording under the identical key is refused (the same file, never a new version); the
    original file on disk is untouched."""
    store, meta = _record_aaa(tmp_path, bar_store, universe_store)
    path = store._path(meta["id"])
    before = _sha256_file(path)

    fresh = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert fresh["baseline_anchors"] == meta["baseline_anchors"]
    assert fresh["summary"] == meta["summary"]
    assert fresh["signals"] == meta["signals"]

    with pytest.raises(PlaybookAlreadyRecorded):
        store.record(**fresh)
    assert _sha256_file(path) == before


def test_two_firings_of_the_same_symbol_setup_pair_draw_independent_non_colliding_anchors():
    """TC-11: a synthetic fixture where the SAME (symbol, setup_id) pair fires TWICE within one
    session -- each firing's own seed differs (`firing_index` 0 vs 1) and the anchor indices they
    draw differ too, so the baseline pool genuinely grows to reflect BOTH independent draws instead
    of the identical index being drawn twice (today's actual walk cannot yet produce two firings of
    one symbol -- opening-range-break fires at most once per symbol-session -- so this fixture
    exercises the seed/draw machinery directly, exactly as the DoD frames it: a no-op today, load-
    bearing the moment a detector CAN fire twice for one (symbol, setup_id))."""
    measure_bars = [
        _bar("AAA", "5m", E_OPEN + i * 300.0, 100.0 + i, 100.5 + i, 99.5 + i, 100.2 + i)
        for i in range(20)
    ]
    pool: list[dict] = []
    seeds: list[str] = []
    for firing_index in range(2):
        seed = _baseline_seed(SESSION_DATE, "AAA", "open_high_break", firing_index)
        seeds.append(seed)
        rng = random.Random(seed)
        (anchor_idx,) = _draw_anchor_indices(rng, len(measure_bars), 1)
        anchor_bar = measure_bars[anchor_idx]
        pool.append(_measure_from(measure_bars, anchor_idx, anchor_bar.close, "close", 5, 1.0))

    assert seeds[0] != seeds[1]  # no seed collision -- the discriminator changed the seed
    assert seeds[1] == f"{seeds[0]}:1"
    assert len(pool) == 2  # the baseline pool grew to reflect both independent draws
    assert pool[0]["at_utc"] != pool[1]["at_utc"]  # the two draws landed on different anchor bars


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


# === goal-playbook-iter-4 (J-04): the continuation family wired into the real compute walk ========


def _plant_ladder_baseline_sessions(bar_store: BarStore, symbol: str) -> None:
    """10 prior RTH 5m sessions, 22 bars each (matching the ladder fixture's OWN session length --
    ``_plant_baseline_sessions``'s shared 6-bar-per-day helper would leave ``slot_volume_medians``
    covering only slots 0-5, starving every base/trigger bar at slot >= 6 of an RVOL -- every
    continuation-family volume gate is fail-closed on a missing median, so this iteration needs its
    own, longer baseline planter rather than widening the shared one every other playbook test
    already depends on)."""
    bars = []
    for day in _BASELINE_DATES:
        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
        for slot in range(22):
            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    _plant(bar_store, symbol, "5m", bars)


def _plant_ladder_jbe_session(bar_store: BarStore, symbol: str) -> None:
    """A real ``BarStore``-backed session where the SAME ``(symbol, "jbe")`` pair fires TWICE --
    the ``test_desk_playbook_detect.py`` ladder fixture, planted as 5m bars only (the opening
    range degrades to its own 5m basis, honestly, per the shared absence gate this iteration's
    continuation detectors ride on -- see ``compute_playbook``'s own docstring)."""
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
        _bar(symbol, "5m", E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
        _bar(symbol, "5m", E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
        _bar(symbol, "5m", E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
        _bar(symbol, "5m", E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
        _bar(symbol, "5m", E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),
        _bar(symbol, "5m", E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),
        _bar(symbol, "5m", E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),
        _bar(symbol, "5m", E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),
        _bar(symbol, "5m", E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),  # step 1 trigger
        _bar(symbol, "5m", E_OPEN + 3000.0, 104.5, 104.6, 104.3, 104.4, 1200),
        _bar(symbol, "5m", E_OPEN + 3300.0, 104.4, 104.5, 104.2, 104.3, 1200),
        _bar(symbol, "5m", E_OPEN + 3600.0, 104.3, 104.4, 104.1, 104.2, 1200),
        _bar(symbol, "5m", E_OPEN + 3900.0, 104.2, 104.3, 104.0, 104.1, 1200),
        _bar(symbol, "5m", E_OPEN + 4200.0, 104.1, 104.2, 103.9, 104.0, 1200),
        _bar(symbol, "5m", E_OPEN + 4500.0, 104.0, 104.3, 103.9, 104.2, 3000),
        _bar(symbol, "5m", E_OPEN + 4800.0, 107.5, 107.8, 107.2, 107.6, 400),
        _bar(symbol, "5m", E_OPEN + 5100.0, 107.6, 108.0, 107.3, 107.7, 500),
        _bar(symbol, "5m", E_OPEN + 5400.0, 107.7, 107.9, 107.4, 107.8, 450),
        _bar(symbol, "5m", E_OPEN + 5700.0, 107.9, 108.8, 107.8, 108.5, 1500),  # step 2 trigger
        _bar(symbol, "5m", E_OPEN + 6000.0, 108.5, 108.7, 108.3, 108.6, 900),
        _bar(symbol, "5m", E_OPEN + 6300.0, 108.6, 108.8, 108.4, 108.7, 900),
    ]
    _plant(bar_store, symbol, "5m", bars_5m)


def test_real_two_firing_jbe_fixture_draws_independent_baseline_anchors_via_compute_playbook(
    tmp_path, bar_store,
):
    """TC-8: the FIRST real exercise of the iter-3 seed-collision fix on an actual multi-fire
    signal (not just the synthetic fixture `test_two_firings_of_the_same_symbol_setup_pair_draw_
    independent_non_colliding_anchors` already proves the machinery with) -- two `jbe` signals
    fire for the SAME symbol in one session, and their baseline draws land on different anchor
    bars because `firing_index` genuinely increments 0 -> 1 across them."""
    universe_store = _register_universe(tmp_path, ["LADDER"])
    _plant_ladder_baseline_sessions(bar_store, "LADDER")
    _plant_ladder_jbe_session(bar_store, "LADDER")

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    jbe_signals = [s for s in result["signals"] if s["setup_id"] == "jbe"]
    assert len(jbe_signals) == 2
    assert jbe_signals[0]["geometry"]["slots_to_break"] < jbe_signals[1]["geometry"]["slots_to_break"]
    assert jbe_signals[0]["geometry"]["ladder_step_ratio"] is None
    assert jbe_signals[1]["geometry"]["ladder_step_ratio"] is not None

    pool = result["baseline_anchors"]["jbe:long"]
    assert len(pool) == 2  # both firings' own draws pooled -- neither one silently dropped
    assert pool[0]["at_utc"] != pool[1]["at_utc"]  # independent, non-colliding anchor bars

    # Determinism: a second, fresh compute over the identical inputs reproduces byte-identically.
    second = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert second["baseline_anchors"]["jbe:long"] == pool


# --- TC-9 / TC-10: the new setups tuple re-keys, it never rewrites -----------------------------


def test_j04_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
    tmp_path, bar_store, universe_store, monkeypatch,
):
    """Simulates 'a file already recorded under the J-01/J-02/J-03-era, 2-setup parameters' by
    monkeypatching `PLAYBOOK_SETUPS` down to its pre-J-04 value for ONE recording (the
    `_record_aaa` fixture's own 6-bar session is too short for `jbe`/`dbi`/`cup_handle` to ever
    fire regardless of which code computed it -- see `_find_one_continuation`'s own
    `jump_lookback_bars` floor -- so this monkeypatch isolates exactly the ONE thing this
    iteration actually changed for an already-recorded file's own inputs: the parameters blob's
    `setups` list, and therefore the signature).

    TC-9: the pre-J-04 file's own bytes on disk are UNCHANGED by a fresh, post-J-04 compute over
    the identical inputs. TC-10: that fresh compute mints a genuinely NEW record (new signature,
    new id) beside the old one -- re-keying, never rewriting -- and the OR-break signal's own
    CONTENT (not its signature) is unaffected."""
    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_SETUPS", ("open_high_break", "open_low_break"))
    pre_j04_store, pre_j04_meta = _record_aaa(tmp_path, bar_store, universe_store)
    pre_j04_path = pre_j04_store._path(pre_j04_meta["id"])
    pre_j04_sha = _sha256_file(pre_j04_path)
    assert pre_j04_meta["parameters"]["setups"] == ["open_high_break", "open_low_break"]

    # goal-playbook-iter-5 (J-05) maintenance note: this restores the CURRENT `PLAYBOOK_SETUPS`,
    # which iter-5 legitimately grew to 6 entries (`capitulation` joined) -- the assertion below is
    # updated to match, exactly as this same test updated it from 2 to 5 entries when it was
    # J-04's own new content. This is a live "what does PLAYBOOK_SETUPS currently say" assertion,
    # not a frozen discipline guard, so it tracks the tuple's real value every iteration that
    # legitimately extends it.
    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS

    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert current_result["parameters"]["setups"] == [
        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
        "range_trade", "double_top", "double_bottom",
    ]
    assert current_result["playbook_input_signature"] != pre_j04_meta["playbook_input_signature"]

    current_meta = pre_j04_store.record(**current_result)
    assert current_meta["id"] != pre_j04_meta["id"]

    # TC-9: the pre-J-04 file is byte-identical, untouched by the second, differently-keyed write.
    assert _sha256_file(pre_j04_path) == pre_j04_sha
    assert pre_j04_store.get(pre_j04_meta["id"]) == pre_j04_meta

    # TC-10: both versions are now recorded for this date; newest is the current-code one.
    newest, versions = pre_j04_store.newest_for_date(SESSION_DATE)
    assert versions == 2
    assert newest["id"] == current_meta["id"]

    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
    # parameters blob -- zero behavior change to the family J-01/J-02/J-03 already shipped.
    pre_j04_or_signals = [
        s for s in pre_j04_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    current_or_signals = [
        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    assert pre_j04_or_signals == current_or_signals


# === goal-playbook-iter-5 (J-05): the climax family wired into the real compute walk ==============


def _plant_capitulation_session(bar_store: BarStore, symbol: str) -> None:
    """The ``test_desk_playbook_detect.py`` canonical capitulation fixture, trimmed to 6 bars
    (matching ``_plant_baseline_sessions``'s own 6-slot coverage) and planted through a real
    ``BarStore``: a vertical decline into a climax bar (slot 3, RVOL surge) followed by a
    first-strength reversal trigger at slot 4."""
    bars_5m = [
        _bar(symbol, "5m", E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
        _bar(symbol, "5m", E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
        _bar(symbol, "5m", E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
        _bar(symbol, "5m", E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),
        _bar(symbol, "5m", E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),
        _bar(symbol, "5m", E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
    ]
    _plant(bar_store, symbol, "5m", bars_5m)


def test_capitulation_wired_into_compute_playbook_is_measured_like_every_other_setup(
    tmp_path, bar_store, universe_store,
):
    """Capitulation joins the SAME per-member walk as every other family: `PLAYBOOK_SETUPS` now
    names it, and the recorded signal carries `forward`/`invalidation_breached` exactly like an
    opening-range-break/jbe/dbi/cup_handle signal does (J-02's measurement pass, unmodified)."""
    _plant_baseline_sessions(bar_store, "AAA")
    _plant_capitulation_session(bar_store, "AAA")
    # THIN stays absent (thin baseline) -- reused from the fixture universe unmodified.

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    # goal-playbook-iter-6 (J-06) maintenance note: `PLAYBOOK_SETUPS` no longer ENDS with
    # "capitulation" (three more setup ids joined after it) -- a live "is it present" check, not a
    # frozen discipline guard, so it tracks the tuple's real membership every iteration that
    # legitimately extends it (the same maintenance the J-04/J-05 setups-tuple tests already do).
    assert "capitulation" in desk_playbook_module.PLAYBOOK_SETUPS
    assert "capitulation" in result["parameters"]["setups"]
    cap_signals = [s for s in result["signals"] if s["symbol"] == "AAA" and s["setup_id"] == "capitulation"]
    assert len(cap_signals) == 1
    signal = cap_signals[0]
    assert "forward" in signal and signal["forward"] is not None
    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
    assert result["summary"]["capitulation:long"]["to_close"]["signals"]["n"] == 1
    assert result["baseline_anchors"]["capitulation:long"]


def test_euphoria_marker_never_appears_in_any_signal_pool_or_summary_key(tmp_path, bar_store):
    """TC-4: the structural guard, proven against a REAL firing (not just a source scan) -- a
    session that fires ONLY the euphoria marker (the exact mirror-UP of the capitulation fixture
    above) records zero signals for that symbol, and `"euphoria"` never appears anywhere in the
    result: not as a `setup_id`, not as a `signal_pool`/`baseline_anchors`/`summary` key
    component."""
    universe_store = _register_universe(tmp_path, ["EUP1"])
    _plant_baseline_sessions(bar_store, "EUP1")
    bars_5m = [
        _bar("EUP1", "5m", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
        _bar("EUP1", "5m", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
        _bar("EUP1", "5m", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
        _bar("EUP1", "5m", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),
        _bar("EUP1", "5m", E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),
        _bar("EUP1", "5m", E_OPEN + 1500.0, 98.9, 99.1, 98.6, 99.0, 900),
    ]
    _plant(bar_store, "EUP1", "5m", bars_5m)

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert [s["symbol"] for s in result["signals"] if s["symbol"] == "EUP1"] == []
    assert not any(s["setup_id"] == "euphoria" for s in result["signals"])
    assert not any("euphoria" in key for key in result["summary"])
    assert not any("euphoria" in key for key in result["baseline_anchors"])
    assert not any(a.get("symbol") == "euphoria" for a in result["absences"])


def _plant_decoration_baseline_sessions(bar_store: BarStore, symbol: str, slots: int = 9) -> None:
    """9 slots (not the shared 6) -- the marker-decoration fixture below needs slots 0-8 for a
    same-session euphoria marker (slot 4) followed by an independent, later capitulation firing
    (slot 8), so it needs its own longer baseline planter (the `_plant_ladder_baseline_sessions`
    precedent)."""
    bars = []
    for day in _BASELINE_DATES:
        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
        for slot in range(slots):
            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, 100.0, 100.5, 99.5, 100.0, 1000))
    _plant(bar_store, symbol, "5m", bars)


def test_a_later_capitulation_signal_is_decorated_euphoria_recent_by_an_earlier_marker(
    tmp_path, bar_store,
):
    """TC-3: ONE session, real end-to-end -- an early euphoria mirror-formation (marker trigger at
    slot 4) followed within `PLAYBOOK_MARKER_DECAY_BARS` (6) bars by an independent, LATER
    capitulation formation (trigger at slot 8) -- the capitulation signal renders with
    `disclosures.euphoria_recent == True`, and the signals table contains no `"euphoria"` row of
    any kind."""
    universe_store = _register_universe(tmp_path, ["DECOR"])
    _plant_decoration_baseline_sessions(bar_store, "DECOR")
    bars_5m = [
        _bar("DECOR", "5m", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
        _bar("DECOR", "5m", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
        _bar("DECOR", "5m", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
        _bar("DECOR", "5m", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # euphoria climax
        _bar("DECOR", "5m", E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),  # euphoria trigger (slot 4)
        _bar("DECOR", "5m", E_OPEN + 1500.0, 98.9, 99.0, 96.5, 97.0, 1000),
        _bar("DECOR", "5m", E_OPEN + 1800.0, 97.0, 97.2, 95.0, 95.5, 1000),
        _bar("DECOR", "5m", E_OPEN + 2100.0, 94.0, 94.2, 92.8, 93.5, 2600),  # capitulation climax
        _bar("DECOR", "5m", E_OPEN + 2400.0, 93.0, 94.5, 93.0, 94.0, 1000),  # capitulation trigger (slot 8)
    ]
    _plant(bar_store, "DECOR", "5m", bars_5m)

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert not any(s["setup_id"] == "euphoria" for s in result["signals"])
    cap_signals = [s for s in result["signals"] if s["setup_id"] == "capitulation"]
    assert len(cap_signals) == 1
    assert cap_signals[0]["geometry"]["slots_to_break"] == 8
    assert cap_signals[0]["disclosures"]["euphoria_recent"] is True
    assert cap_signals[0]["disclosures"]["capitulation_recent"] is False


# --- TC-9 / TC-10: J-05's own setups-tuple re-key, mirroring the J-04 precedent above --------------


def test_j05_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
    tmp_path, bar_store, universe_store, monkeypatch,
):
    """Simulates 'a file already recorded under the pre-J-05, 5-setup parameters' by monkeypatching
    `PLAYBOOK_SETUPS` down to its J-04-era value for ONE recording -- `_record_aaa`'s own 6-bar
    session is too short for `capitulation` to ever fire regardless of which code computed it (its
    own vertical-move window alone needs 4+ bars before any trigger), so this isolates exactly the
    ONE thing this iteration changed for an already-recorded file's own inputs: the parameters
    blob's `setups` list, and therefore the signature.

    TC-9: the pre-J-05 file's own bytes on disk are UNCHANGED by a fresh, post-J-05 compute over
    the identical inputs. TC-10: that fresh compute mints a genuinely NEW record (new signature,
    new id) beside the old one -- re-keying, never rewriting -- and the OR-break signal's own
    CONTENT (not its signature) is unaffected."""
    monkeypatch.setattr(
        desk_playbook_module, "PLAYBOOK_SETUPS",
        ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle"),
    )
    pre_j05_store, pre_j05_meta = _record_aaa(tmp_path, bar_store, universe_store)
    pre_j05_path = pre_j05_store._path(pre_j05_meta["id"])
    pre_j05_sha = _sha256_file(pre_j05_path)
    assert pre_j05_meta["parameters"]["setups"] == [
        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle",
    ]

    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS

    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert current_result["parameters"]["setups"] == [
        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
        "range_trade", "double_top", "double_bottom",
    ]
    assert current_result["playbook_input_signature"] != pre_j05_meta["playbook_input_signature"]

    current_meta = pre_j05_store.record(**current_result)
    assert current_meta["id"] != pre_j05_meta["id"]

    # TC-9: the pre-J-05 file is byte-identical, untouched by the second, differently-keyed write.
    assert _sha256_file(pre_j05_path) == pre_j05_sha
    assert pre_j05_store.get(pre_j05_meta["id"]) == pre_j05_meta

    # TC-10: both versions are now recorded for this date; newest is the current-code one.
    newest, versions = pre_j05_store.newest_for_date(SESSION_DATE)
    assert versions == 2
    assert newest["id"] == current_meta["id"]

    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
    # parameters blob -- zero behavior change to the families J-01 through J-04 already shipped.
    pre_j05_or_signals = [
        s for s in pre_j05_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    current_or_signals = [
        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    assert pre_j05_or_signals == current_or_signals


# === goal-playbook-iter-6 (J-06): the range family wired into the real compute walk ===============


def _plant_range_trade_session(bar_store: BarStore, symbol: str) -> None:
    """The ``test_desk_playbook_detect.py`` canonical range_trade (support-bounce long) fixture,
    planted through a real ``BarStore`` -- a genuinely TWO-SIDED range (both zones tested twice and
    held), the only formation spec §3.7's arming clause admits."""
    bars_5m = [
        _bar(symbol, "5m", E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
        _bar(symbol, "5m", E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
        _bar(symbol, "5m", E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
        _bar(symbol, "5m", E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
        _bar(symbol, "5m", E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
        _bar(symbol, "5m", E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
        _bar(symbol, "5m", E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
        _bar(symbol, "5m", E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
        _bar(symbol, "5m", E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
        _bar(symbol, "5m", E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
    ]
    _plant(bar_store, symbol, "5m", bars_5m)


def test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_setup(
    tmp_path, bar_store,
):
    """Range_trade joins the SAME per-member walk as every other family: `PLAYBOOK_SETUPS` now
    names it, and the recorded signal carries `forward`/`invalidation_breached` exactly like an
    opening-range-break/jbe/dbi/cup_handle/capitulation signal does (J-02's measurement pass,
    unmodified)."""
    universe_store = _register_universe(tmp_path, ["RTAAA"])
    _plant_decoration_baseline_sessions(bar_store, "RTAAA", slots=10)
    _plant_range_trade_session(bar_store, "RTAAA")

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert "range_trade" in result["parameters"]["setups"]
    rt_signals = [s for s in result["signals"] if s["symbol"] == "RTAAA" and s["setup_id"] == "range_trade"]
    assert len(rt_signals) == 1
    signal = rt_signals[0]
    assert "forward" in signal and signal["forward"] is not None
    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
    assert result["summary"]["range_trade:long"]["to_close"]["signals"]["n"] == 1
    assert result["baseline_anchors"]["range_trade:long"]


def _plant_double_top_session(bar_store: BarStore, symbol: str) -> None:
    """The ``test_desk_playbook_detect.py`` canonical double_top fixture, planted through a real
    ``BarStore``."""
    bars_5m = [
        _bar(symbol, "5m", E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
        _bar(symbol, "5m", E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
        _bar(symbol, "5m", E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
        _bar(symbol, "5m", E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),
        _bar(symbol, "5m", E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
        _bar(symbol, "5m", E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
        _bar(symbol, "5m", E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
        _bar(symbol, "5m", E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
        _bar(symbol, "5m", E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),
        _bar(symbol, "5m", E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
        _bar(symbol, "5m", E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
        _bar(symbol, "5m", E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
        _bar(symbol, "5m", E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
        _bar(symbol, "5m", E_OPEN + 13 * 300.0, 106.5, 110.3, 106, 109.5, 1000),
        _bar(symbol, "5m", E_OPEN + 14 * 300.0, 109.5, 108, 107, 107.5, 1000),
        _bar(symbol, "5m", E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
        _bar(symbol, "5m", E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),
        _bar(symbol, "5m", E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
        _bar(symbol, "5m", E_OPEN + 18 * 300.0, 102.5, 103, 96.0, 96.5, 2000),
        _bar(symbol, "5m", E_OPEN + 19 * 300.0, 96.5, 97, 96, 96.8, 1000),
    ]
    _plant(bar_store, symbol, "5m", bars_5m)


def test_double_top_and_double_bottom_wired_into_compute_playbook_is_measured_like_every_other_setup(
    tmp_path, bar_store,
):
    """double_top (and, by the exact-mirror construction, double_bottom) join the SAME per-member
    walk as every other family."""
    universe_store = _register_universe(tmp_path, ["DTAAA"])
    _plant_decoration_baseline_sessions(bar_store, "DTAAA", slots=20)
    _plant_double_top_session(bar_store, "DTAAA")

    result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)

    assert "double_top" in result["parameters"]["setups"]
    assert "double_bottom" in result["parameters"]["setups"]
    dt_signals = [s for s in result["signals"] if s["symbol"] == "DTAAA" and s["setup_id"] == "double_top"]
    assert len(dt_signals) == 1
    signal = dt_signals[0]
    assert "forward" in signal and signal["forward"] is not None
    assert "invalidation_breached" in signal and signal["invalidation_breached"] is not None
    assert result["summary"]["double_top:short"]["to_close"]["signals"]["n"] == 1
    assert result["baseline_anchors"]["double_top:short"]


def test_j06_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file(
    tmp_path, bar_store, universe_store, monkeypatch,
):
    """TC-13/TC-14: the SAME re-key-never-rewrite precedent as the J-04/J-05 tests above, this time
    for J-06's own three new setup ids. `_record_aaa`'s own 6-bar session is too short for
    `range_trade`/`double_top`/`double_bottom` to ever fire (each needs >= 2 zone touches or 2
    confirmed, separated pivots -- neither is reachable in 6 bars), so this isolates exactly the
    ONE thing this iteration changed for an already-recorded file's own inputs: the parameters
    blob's `setups` list, and therefore the signature."""
    monkeypatch.setattr(
        desk_playbook_module, "PLAYBOOK_SETUPS",
        ("open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation"),
    )
    pre_j06_store, pre_j06_meta = _record_aaa(tmp_path, bar_store, universe_store)
    pre_j06_path = pre_j06_store._path(pre_j06_meta["id"])
    pre_j06_sha = _sha256_file(pre_j06_path)
    assert pre_j06_meta["parameters"]["setups"] == [
        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
    ]

    monkeypatch.undo()  # restore this iteration's real 9-setup PLAYBOOK_SETUPS

    current_result = compute_playbook(universe_store, bar_store, CONFIG.config_fingerprint(), SESSION_DATE)
    assert current_result["parameters"]["setups"] == [
        "open_high_break", "open_low_break", "jbe", "dbi", "cup_handle", "capitulation",
        "range_trade", "double_top", "double_bottom",
    ]
    assert current_result["playbook_input_signature"] != pre_j06_meta["playbook_input_signature"]

    current_meta = pre_j06_store.record(**current_result)
    assert current_meta["id"] != pre_j06_meta["id"]

    # TC-13: the pre-J-06 file is byte-identical, untouched by the second, differently-keyed write.
    assert _sha256_file(pre_j06_path) == pre_j06_sha
    assert pre_j06_store.get(pre_j06_meta["id"]) == pre_j06_meta

    # TC-14: both versions are now recorded for this date; newest is the current-code one.
    newest, versions = pre_j06_store.newest_for_date(SESSION_DATE)
    assert versions == 2
    assert newest["id"] == current_meta["id"]

    # The OR-break signal's own CONTENT is unaffected by the new setups tuple joining the
    # parameters blob -- zero behavior change to the families J-01 through J-05 already shipped.
    pre_j06_or_signals = [
        s for s in pre_j06_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    current_or_signals = [
        s for s in current_meta["signals"] if s["setup_id"] in ("open_high_break", "open_low_break")
    ]
    assert pre_j06_or_signals == current_or_signals


# --- TC-8: the widened PLAYBOOK_REGISTER pinned exactly, with a mandatory rationale paragraph ------
#
# goal-playbook-iter-6 (J-06): PLAYBOOK_REGISTER's opening clause widens AGAIN -- this is the THIRD
# occurrence of this pattern (J-04, J-05, now J-06), so it is deliberately not deferred. It now
# names all EIGHT shipped setup families: opening-range-break (one family covering both
# open_high_break/open_low_break, the same grouping the register has used since J-01),
# jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top,
# and double-bottom -- range_trade's own PROVISIONAL tier is a code-comment/spec disclosure, not a
# reason to omit it from the register (it is a genuinely shipped, detected, measured family this
# iteration). This is a PINNED, exact-string assertion so the NEXT widening (whenever it lands)
# fails LOUDLY here rather than silently leaving the served register out of date again -- whoever
# adds a family must deliberately re-derive this constant (and this rationale paragraph), never
# just extend `PLAYBOOK_SETUPS` in isolation.
_EXPECTED_PLAYBOOK_REGISTER = (
    "pre-registered opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, "
    "capitulation, range-trade, double-top, and double-bottom signals detected on the desk's own "
    "recorded 5m/1m bars — every threshold is "
    "fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
    "A signal is a recorded observation, not advice: invalidation_price is the book's own "
    "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
    "Each signal's forward block is measured with the desk forward rail's own conventions — "
    "trading-bar horizons, dual max drawdown, truncation honesty — anchored at the entry already "
    "decided at detection time, never recomputed a second way; invalidation_breached discloses "
    "whether price ever traded through that structural level, never an exit model; baseline_anchors "
    "and summary compare every signal against the SAME math anchored at seeded random minutes of "
    "the same session. A record computed before this measurement pass existed carries an honest "
    "absence instead — no fills, no costs, and no probability, expectancy, edge, or significance "
    "claim are made anywhere on this payload"
)


def test_playbook_register_pinned_text_names_every_shipped_setup_family():
    """TC-8: the widened PLAYBOOK_REGISTER matches EXACTLY (see the rationale paragraph above) --
    zero tolerance for a family being added to PLAYBOOK_SETUPS without this string being
    deliberately re-derived alongside it."""
    assert PLAYBOOK_REGISTER == _EXPECTED_PLAYBOOK_REGISTER
    assert find_violations(PLAYBOOK_REGISTER) == []
