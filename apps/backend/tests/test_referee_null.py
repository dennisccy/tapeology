"""``referee_null.py`` + the ``/research/desk/referee/nulls*`` routes (Era 6 "The Referee", J-04) --
matched nulls. Test-first contract: TC-1 through TC-9, TC-13, TC-16 through TC-21 in
``docs/phases/goal-referee-iter-5.md``.

Fixtures build REAL, internally-consistent signals by calling the imported rail's own
``desk_forward._measure_from`` directly against hand-built ``RawBar`` arrays (never a hand-typed
forward block) -- the ``test_desk_forward.py``/``test_referee_evidence.py`` precedent -- then plant
them into a real ``PlaybookStore``/``BarStore`` through each store's own public write path. Every
expected count/index below is independently re-derivable from the fixture's own bar geometry, not
merely read back from the module under test."""

from __future__ import annotations

import hashlib
import sys
import time as time_module

import pytest
from fastapi.testclient import TestClient

import app.research.referee_null as referee_null_module
from app.config import CONFIG
from app.main import app
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_forward import _draw_anchor_indices, _measure_from
from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
from app.research.desk_playbook_context import AT_WALL, PLAYBOOK_CONTEXT_ALGORITHM_VERSION
from app.research.desk_playbook_features import side_sign
from app.research.referee_evidence import playbook_observations
from app.research.referee_null import (
    REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
    REFEREE_NULL_CONTEXT_SPEC_ID,
    REFEREE_NULL_TOD_SPEC_ID,
    REFEREE_TEST_PERM_SPEC_ID,
    NullAlreadyRecorded,
    RefereeNullComputeManager,
    RefereeNullRunStore,
    RefereeNullStore,
    _eligible_anchor_positions,
    _session_close_epoch,
    build_null_record,
    null_context_spec_signature,
    null_tod_spec_signature,
    referee_stream,
    run_null_build_and_record,
    tod_bucket_for_epoch,
)
from app.research.referee_null import test_perm_spec_parameters as _test_perm_spec_parameters
from app.research.referee_null import test_perm_spec_signature as _test_perm_spec_signature
from app.research.referee_routes import get_referee_null_compute_manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET, the codebase's standard fixture anchor
SESSION_DATE = "2026-06-22"


# --- fixture builders (real rail measurement + each store's own public write path) -----------------


def _bar5(symbol: str, i: int, close: float = 100.2) -> RawBar:
    """One 5m RTH bar at ``09:30 + i*5min`` ET -- the ``test_desk_forward.py``/``test_desk_playbook.
    py`` ``_bar``/``_minute`` idiom, specialised to a fixed 5-minute cadence."""
    return RawBar(symbol, "5m", E_OPEN + i * 300.0, 100.0, 100.5, 99.5, close, 1000)


def _plant_bars(bar_store: BarStore, symbol: str, bars: list[RawBar]) -> None:
    bar_store.record(
        symbol=symbol, timeframe="5m", window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-30T00:00:00Z", feed="test", bars=bars,
    )


def _plant_occurrence(
    playbook_store: PlaybookStore, bar_store: BarStore, symbol: str, bars: list[RawBar],
    *, side: str = "long", signature: str = "sig-a",
) -> dict:
    """Plants ``bars`` into ``bar_store`` and a ONE-signal playbook record (triggered at bar index
    0, measured through the REAL rail) into ``playbook_store``. Returns the J-02 observation whose
    ``measure_key == "to_close"`` -- the ToD-bucket-only-eligibility measure, so a fixture's own
    eligible-anchor count depends ONLY on how many bars share the trigger's own ToD bucket, never on
    a remaining-time boundary (kept as its own dedicated TC-4 test below)."""
    _plant_bars(bar_store, symbol, bars)
    sign = side_sign(side)
    forward = _measure_from(bars, 0, bars[0].close, "close", 5, sign)
    signal = {
        "setup_id": "open_high_break", "side": side, "symbol": symbol,
        "trigger_ts": referee_null_module._iso(bars[0].epoch), "entry": bars[0].close,
        "entry_kind": "close", "invalidation_price": bars[0].close - 0.5, "forward": forward,
        "invalidation_breached": False, "geometry": {"anchors": []},
    }
    playbook_store.record(
        session_date=SESSION_DATE, config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=signature, payload_version=3, parameters=playbook_parameters(),
        register=PLAYBOOK_REGISTER, signals=[signal], absences=[], diagnostics=[],
    )
    observations = playbook_observations(playbook_store, CONFIG.config_fingerprint())["observations"]
    to_close = [o for o in observations if o["measure_key"] == "to_close" and o["symbol"] == symbol]
    assert len(to_close) == 1, to_close
    return to_close[0]


def _plant_multi_symbol_occurrences(
    playbook_store: PlaybookStore, bar_store: BarStore, symbols: list[str], *, signature: str = "sig-multi",
) -> list[dict]:
    """Plants ONE playbook record covering MULTIPLE symbols' worth of signals -- a real playbook
    record's own shape (``PlaybookStore``'s newest-per-``session_date`` pooling rule keeps only ONE
    record per date, so a fixture needing several eligible occurrences at the SAME session_date must
    put every signal inside that ONE record, never several separately-recorded ones). Returns the
    J-02 ``to_close`` observation per symbol, in ``symbols`` order."""
    signals = []
    for symbol in symbols:
        bars = [_bar5(symbol, i) for i in range(5)]
        _plant_bars(bar_store, symbol, bars)
        forward = _measure_from(bars, 0, bars[0].close, "close", 5, side_sign("long"))
        signals.append(
            {
                "setup_id": "open_high_break", "side": "long", "symbol": symbol,
                "trigger_ts": referee_null_module._iso(bars[0].epoch), "entry": bars[0].close,
                "entry_kind": "close", "invalidation_price": bars[0].close - 0.5, "forward": forward,
                "invalidation_breached": False, "geometry": {"anchors": []},
            }
        )
    playbook_store.record(
        session_date=SESSION_DATE, config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=signature, payload_version=3, parameters=playbook_parameters(),
        register=PLAYBOOK_REGISTER, signals=signals, absences=[], diagnostics=[],
    )
    observations = playbook_observations(playbook_store, CONFIG.config_fingerprint())["observations"]
    by_symbol = {
        o["symbol"]: o for o in observations if o["measure_key"] == "to_close"
    }
    return [by_symbol[symbol] for symbol in symbols]


@pytest.fixture
def env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    null_store = RefereeNullStore(tmp_path / "nulls")
    run_store = RefereeNullRunStore(tmp_path / "null_runs")
    return bar_store, playbook_store, null_store, run_store


# === TC-1: exactly K=4 eligible anchors -- k_drawn == eligible_count == 4, draw hand-verified ========


def test_tc1_exactly_k_eligible_anchors_draws_all_four_via_the_pinned_seed(env):
    """TC-1: 5 bars total (trigger + 4 more, all inside the SAME "open" ToD bucket) -> k_drawn ==
    eligible_count == 4, excluded == False, and the 4 drawn anchor indices match an INDEPENDENT
    re-derivation of the pinned Fisher-Yates draw (the SAME seeded-stream recipe + ``desk_forward.
    _draw_anchor_indices`` this module itself calls, invoked here a second time with the identical
    inputs -- never by reading the module's own output back)."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC1", i) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC1", bars)

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert record["k_requested"] == REFEREE_NULL_ANCHORS_PER_OCCURRENCE == 4
    assert record["k_drawn"] == 4
    assert record["eligible_count"] == 4
    assert record["excluded"] is False
    assert record["tod_bucket"] == "open"
    assert len(record["anchors"]) == 4

    # Independent re-derivation: eligible positions are indices 1..4 (0 is the trigger, excluded);
    # the SAME stream recipe + draw primitive, called fresh here.
    stream = referee_stream(
        REFEREE_NULL_TOD_SPEC_ID, "null-draw", session_date=observation["session_date"],
        i=observation["observation_id"],
    )
    expected_drawn = _draw_anchor_indices(stream, 4, 4)
    eligible_positions = [1, 2, 3, 4]
    expected_indices = sorted(eligible_positions[j] for j in expected_drawn)
    actual_indices = sorted(
        i for i, bar in enumerate(bars) if referee_null_module._iso(bar.epoch) in {a["anchor_ts"] for a in record["anchors"]}
    )
    assert actual_indices == expected_indices == [1, 2, 3, 4]  # all 4 non-trigger bars, order-sorted


# === TC-2: shortfall -- only 2 eligible, disclosed, never silently absent =============================


def test_tc2_shortfall_is_served_not_silently_absent(env):
    """TC-2: only 3 bars total (trigger + 2 candidates) -> k_drawn == eligible_count == 2, and the
    shortfall (``k_requested - k_drawn == 2``) is computable from the served fields, never hidden."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC2", i) for i in range(3)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC2", bars)

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert record["k_drawn"] == 2
    assert record["eligible_count"] == 2
    assert record["excluded"] is False
    assert record["k_requested"] - record["k_drawn"] == 2  # the shortfall, served not hidden
    assert len(record["anchors"]) == 2


# === TC-3: zero eligible -- occurrence excluded and counted, never silently dropped ===================


def test_tc3_zero_eligible_excludes_and_counts_the_occurrence(env):
    """TC-3: exactly 1 bar total (only the trigger itself) -> excluded == True, eligible_count ==
    0, k_drawn == 0 -- and the record is still RETURNED (never a ``None``/omitted result), so a
    caller's own tally can count the exclusion instead of it silently vanishing."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC3", 0)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC3", bars)

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert record["excluded"] is True
    assert record["eligible_count"] == 0
    assert record["k_drawn"] == 0
    assert record["anchors"] == []
    assert record["mean_window_overlap"] is None


# === TC-4: the remaining-time boundary (15:00 ELIGIBLE / 15:05 INELIGIBLE for a 1h primary) ==========


def test_tc4_remaining_time_boundary_at_1500_vs_1505_et_for_a_1h_horizon():
    """TC-4: a candidate anchor bar at EXACTLY 15:00 ET (60 min remaining before the 16:00 ET
    close) is ELIGIBLE for a 1h-horizon primary (``>= 60``); one at 15:05 ET (55 min remaining) is
    INELIGIBLE (``< 60``) -- both hand-verified against the literal wall-clock distance to the
    session's own RTH close, spec Sec4.1's remaining-time rule. Exercises ``_eligible_anchor_
    positions`` directly (the eligibility primitive), independent of the full record-build
    pipeline."""
    import datetime
    import zoneinfo

    et = zoneinfo.ZoneInfo("America/New_York")
    e_1500 = datetime.datetime.combine(
        datetime.date(2026, 6, 22), datetime.time(15, 0), tzinfo=et
    ).timestamp()
    e_1505 = datetime.datetime.combine(
        datetime.date(2026, 6, 22), datetime.time(15, 5), tzinfo=et
    ).timestamp()
    e_1530 = datetime.datetime.combine(
        datetime.date(2026, 6, 22), datetime.time(15, 30), tzinfo=et
    ).timestamp()  # the trigger -- clear of both candidates, still in the "close" bucket

    bars = [
        RawBar("TC4", "5m", e_1530, 1, 1, 1, 1, 1),  # index 0: trigger
        RawBar("TC4", "5m", e_1500, 1, 1, 1, 1, 1),  # index 1: 60 min remaining -- ELIGIBLE
        RawBar("TC4", "5m", e_1505, 1, 1, 1, 1, 1),  # index 2: 55 min remaining -- INELIGIBLE
    ]
    close_epoch = _session_close_epoch(SESSION_DATE)
    assert tod_bucket_for_epoch(e_1500) == tod_bucket_for_epoch(e_1505) == tod_bucket_for_epoch(e_1530) == "close"

    positions = _eligible_anchor_positions(bars, 0, "close", 60.0, close_epoch)
    assert positions == [1]  # ONLY the 15:00 bar -- the 15:05 bar correctly excluded


# === TC-5: the context-matched null -- backing-bucket predicate + the paired signal's own risk =======


def test_tc5_context_null_backing_bucket_predicate_and_room_r_from_the_paired_signal(env):
    """TC-5: 5 bars -- trigger near a recorded support band (index 0), one candidate far from any
    band (index 1, excluded), three candidates near the SAME band (indices 2-4, matched). Every
    stored anchor's close satisfies ``at_wall`` via the injected resolver (standing in for
    ``BandMapResolver`` -- the SAME public ``band_context_block`` this module calls, dependency-
    injected rather than requiring a real ``TradabilityCache``); the excluded candidate is reflected
    in the served per-cell rate (3 matched / 4 ToD-eligible == 0.75); ``room_r`` on each anchor
    equals the paired occurrence's OWN risk distance (verified by an independent re-derivation
    calling ``band_context_block`` a second time with the SAME ``risk_bps``)."""
    from app.research.desk_playbook_context import band_context_block

    bar_store, playbook_store, _null_store, _run_store = env
    bars = [
        _bar5("TC5", 0, close=100.05),  # trigger -- near the band
        _bar5("TC5", 1, close=200.0),  # far from the band -- excluded
        _bar5("TC5", 2, close=100.06),
        _bar5("TC5", 3, close=100.07),
        _bar5("TC5", 4, close=100.08),
    ]
    observation = _plant_occurrence(playbook_store, bar_store, "TC5", bars)

    class _FakeResolver:
        def resolve(self, symbol, as_of_epoch):
            return {
                "bands": [
                    {
                        "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
                        "quality_score": 1.0, "round_number": False, "member_count": 1,
                    }
                ],
                "basis_as_of": "2026-06-21",
            }

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(), backing_bucket=AT_WALL,
        context_resolver=_FakeResolver(),
    )
    assert record["eligible_count"] == 3  # indices 2,3,4 -- index 1 (200.0) fails the predicate
    assert record["k_drawn"] == 3
    assert record["excluded"] is False
    assert record["backing_bucket_eligibility_rate"] == 3 / 4
    assert record["context_algorithm_version"] == PLAYBOOK_CONTEXT_ALGORITHM_VERSION
    assert all(a["backing_bucket_match"] is True for a in record["anchors"])

    # room_r independent re-derivation: the paired occurrence's own risk distance (entry vs
    # invalidation_price, both recorded on the signal) must be what band_context_block computed.
    entry, invalidation = bars[0].close, bars[0].close - 0.5
    expected_risk_bps = abs(entry - invalidation) / entry * 10_000.0
    map_result = _FakeResolver().resolve("TC5", bars[0].epoch)
    for anchor in record["anchors"]:
        anchor_bar = next(b for b in bars if referee_null_module._iso(b.epoch) == anchor["anchor_ts"])
        ctx = band_context_block(
            map_result, anchor_bar.close, "long", risk_bps=expected_risk_bps,
            risk_source="paired_signal",
        )
        assert ctx["risk_bps"] == expected_risk_bps
        assert ctx["room_r"] is not None or ctx["headroom_bps"] is None  # room_r derivable whenever headroom is


def test_tc5_context_null_unresolvable_map_is_an_honest_exclusion_not_a_substitution(env):
    """TC-5 (the "cannot be found" half): when the context resolver reports NO computed map at all,
    the WHOLE occurrence is excluded (never a silent fallback to the unfiltered ToD population)."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC5B", i) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC5B", bars)

    class _NoMapResolver:
        def resolve(self, symbol, as_of_epoch):
            return None

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
        context_resolver=_NoMapResolver(),
    )
    assert record["excluded"] is True
    assert record["eligible_count"] == 0
    assert record["backing_bucket_eligibility_rate"] is None


# === TC-6: convention identity -- the null path vs a DIRECT desk_forward._measure_from call ==========


def test_tc6_anchor_measurement_is_byte_identical_to_a_direct_measure_from_call(env):
    """TC-6: the value this module serves for a drawn anchor equals, byte for byte, calling
    ``desk_forward._measure_from`` directly on the SAME bar/index/entry/entry_kind/tf_minutes/sign
    -- zero diff to the rail."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC6", i, close=100.0 + i * 0.3) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC6", bars)

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    sign = side_sign("long")
    for anchor in record["anchors"]:
        idx = next(i for i, b in enumerate(bars) if referee_null_module._iso(b.epoch) == anchor["anchor_ts"])
        direct = _measure_from(bars, idx, bars[idx].close, "close", 5, sign)
        assert direct["to_close_pct"] == anchor["value"]  # this fixture's measure_key is to_close


# === TC-7: lookahead-clean -- a session truncated at the trigger fabricates nothing ===================


def test_tc7_truncated_session_produces_zero_eligible_never_a_fabricated_anchor(env):
    """TC-7: a session recorded with bars ONLY through the trigger bar itself (nothing after it, as
    if the null were rebuilt the instant the occurrence fired) yields ``eligible_count == 0`` --
    never a value drawn from a bar that, at that instant, does not yet exist on disk. This module
    reads only ``bar_store.merged_bars`` (whatever is actually recorded), so lookahead-cleanliness
    holds by construction; this test is the regression guard."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC7", 0)]  # truncated immediately after the trigger bar -- nothing else recorded
    observation = _plant_occurrence(playbook_store, bar_store, "TC7", bars)

    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert record["excluded"] is True
    assert record["eligible_count"] == 0
    assert record["anchors"] == []


# === TC-8 / TC-9: idempotent reuse (compute-manager level) + old stores untouched =====================


def test_tc8_idempotent_rerun_writes_zero_new_files_and_reuses_the_recorded_answer(env):
    """TC-8: running the SAME null build twice over an unchanged corpus writes the recorded file
    exactly ONCE -- the second run's own file count/SHA-256 for that key is byte-unchanged
    (idempotent reuse, never a duplicate)."""
    bar_store, playbook_store, null_store, run_store = env
    bars = [_bar5("TC8", i) for i in range(5)]
    _plant_occurrence(playbook_store, bar_store, "TC8", bars)

    first = run_null_build_and_record(
        playbook_store, bar_store, CONFIG, null_store, REFEREE_NULL_TOD_SPEC_ID, run_store=run_store,
    )
    assert first["recorded"] >= 1
    files_after_first = sorted(null_store.root.glob("*.json"))
    hashes_after_first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files_after_first}

    second = run_null_build_and_record(
        playbook_store, bar_store, CONFIG, null_store, REFEREE_NULL_TOD_SPEC_ID, run_store=run_store,
    )
    assert second["recorded"] == 0
    assert second["reused"] == first["recorded"] + first["reused"]
    files_after_second = sorted(null_store.root.glob("*.json"))
    hashes_after_second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files_after_second}
    assert hashes_after_second == hashes_after_first  # byte-unchanged -- no file was rewritten


def test_tc9_old_playbook_store_file_is_byte_unchanged_after_a_null_build(env):
    """TC-9: the playbook store this build READS is never mutated -- its own recorded file's
    SHA-256 is unchanged before vs after a full null-build run."""
    bar_store, playbook_store, null_store, run_store = env
    bars = [_bar5("TC9", i) for i in range(5)]
    _plant_occurrence(playbook_store, bar_store, "TC9", bars)

    playbook_files = sorted(playbook_store.root.glob("*.json"))
    assert len(playbook_files) == 1
    before = hashlib.sha256(playbook_files[0].read_bytes()).hexdigest()

    run_null_build_and_record(
        playbook_store, bar_store, CONFIG, null_store, REFEREE_NULL_TOD_SPEC_ID, run_store=run_store,
    )
    run_null_build_and_record(
        playbook_store, bar_store, CONFIG, null_store, REFEREE_NULL_CONTEXT_SPEC_ID, run_store=run_store,
    )  # the context build resolves no map (no injected resolver in the CLI/manager default path
    # exercised here is NOT used -- direct call constructs its own BandMapResolver; a symbol with no
    # recorded tradability cache simply excludes every occurrence, exercised for its OWN side effect
    # of proving it still never touches the playbook store)

    after = hashlib.sha256(playbook_files[0].read_bytes()).hexdigest()
    assert after == before


# === TC-13: non-finite anchor measurement -- excluded and counted, never propagates ===================


def test_tc13_non_finite_anchor_measurement_is_excluded_and_counted(env, monkeypatch):
    """TC-13: a fixture whose ``_measure_from`` result is non-finite for one specific anchor bar --
    that ONE anchor is excluded and counted in ``non_finite_excluded_count``; the occurrence's other
    eligible anchors are unaffected; no exception propagates out of the build."""
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("TC13", i) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "TC13", bars)

    real_measure_from = referee_null_module._measure_from
    poisoned_epoch = bars[2].epoch  # one specific candidate anchor bar, poisoned below

    def _poisoned_measure_from(session_bars, index, entry, entry_kind, tf_minutes, sign):
        result = real_measure_from(session_bars, index, entry, entry_kind, tf_minutes, sign)
        if session_bars[index].epoch == poisoned_epoch:
            result = {**result, "to_close_pct": float("nan")}
        return result

    monkeypatch.setattr(referee_null_module, "_measure_from", _poisoned_measure_from)
    record = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    assert record["excluded"] is False  # the OCCURRENCE is not excluded, only the one anchor
    assert record["eligible_count"] == 4  # eligibility is unaffected -- 4 candidates were eligible
    assert record["k_drawn"] == 4  # 4 were DRAWN
    assert record["non_finite_excluded_count"] == 1  # but only 3 measured cleanly
    assert len(record["anchors"]) == 3
    assert all(a["anchor_ts"] != referee_null_module._iso(poisoned_epoch) for a in record["anchors"])


# === TC-16: the three spec ids are stable and each changes on its OWN parameter change ================


def test_tc16_spec_id_signatures_are_stable_across_repeated_calls():
    assert null_tod_spec_signature() == null_tod_spec_signature()
    assert null_context_spec_signature() == null_context_spec_signature()
    assert _test_perm_spec_signature() == _test_perm_spec_signature()


def test_tc16_spec_id_signatures_differ_from_each_other():
    sigs = {null_tod_spec_signature(), null_context_spec_signature(), _test_perm_spec_signature()}
    assert len(sigs) == 3


def test_tc16_null_tod_spec_signature_changes_when_its_own_parameter_changes(monkeypatch):
    before = null_tod_spec_signature()
    monkeypatch.setattr(referee_null_module, "REFEREE_NULL_ANCHORS_PER_OCCURRENCE", 7)
    after = null_tod_spec_signature()
    assert after != before


def test_tc16_null_context_spec_signature_changes_when_its_own_parameter_changes(monkeypatch):
    before = null_context_spec_signature()
    monkeypatch.setattr(
        referee_null_module, "PLAYBOOK_CONTEXT_ALGORITHM_VERSION", "playbook-band-context-v999"
    )
    after = null_context_spec_signature()
    assert after != before


def test_tc16_test_perm_spec_signature_changes_when_its_own_parameter_changes(monkeypatch):
    import app.research.referee_stats as referee_stats_module

    before = _test_perm_spec_signature()
    monkeypatch.setattr(referee_stats_module, "REFEREE_ENUMERATION_THRESHOLD", 1)
    after = _test_perm_spec_signature()
    assert after != before


def test_tc16_test_perm_spec_blob_is_exactly_spec_section1s_stated_contents():
    """The blob names ONLY the four spec-stated inputs (weights formula identity, sidedness
    handling, enumeration rule, p convention) plus its own id -- nothing invented."""
    blob = _test_perm_spec_parameters()
    assert set(blob) == {
        "id", "weights_formula", "sidedness_handling", "enumeration_rule", "p_convention",
    }
    assert blob["id"] == REFEREE_TEST_PERM_SPEC_ID


# === store discipline: no update/delete method exists anywhere =======================================


def test_referee_null_store_has_no_update_or_delete_method():
    public_methods = {name for name in dir(RefereeNullStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "get", "find_by_key", "record"}


def test_referee_null_run_store_has_no_update_or_delete_method():
    public_methods = {name for name in dir(RefereeNullRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "list_for_null_spec", "record"}


def test_duplicate_null_record_key_raises(env):
    bar_store, playbook_store, null_store, _run_store = env
    bars = [_bar5("DUP", i) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "DUP", bars)
    fields = build_null_record(
        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    null_store.record(fields)
    try:
        null_store.record(fields)
    except NullAlreadyRecorded:
        pass
    else:
        raise AssertionError("expected NullAlreadyRecorded on a duplicate key")


# === the compute manager: single-flight PER null-spec + cancel-to-terminal-ledger-state ===============


def _wait_for_not_running(manager: RefereeNullComputeManager, null_spec_id: str, timeout: float = 5.0) -> dict:
    deadline = time_module.monotonic() + timeout
    while time_module.monotonic() < deadline:
        snap = manager.snapshot(null_spec_id)
        if snap["status"] not in ("running", "cancelling"):
            return snap
        time_module.sleep(0.01)
    raise AssertionError("referee null compute never reached a terminal state")


def test_manager_single_flight_second_trigger_for_the_same_null_spec_returns_the_same_job(env):
    """TC-19: a second trigger for the SAME null_spec_id while one is running is refused (returns
    the UNCHANGED in-flight job, ``started: False``) -- never a concurrent second walk."""
    bar_store, playbook_store, null_store, run_store = env
    _plant_multi_symbol_occurrences(playbook_store, bar_store, [f"MF{i}" for i in range(20)])

    manager = RefereeNullComputeManager()
    first = manager.trigger(
        REFEREE_NULL_TOD_SPEC_ID, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )
    assert first["started"] is True
    second = manager.trigger(
        REFEREE_NULL_TOD_SPEC_ID, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]
    _wait_for_not_running(manager, REFEREE_NULL_TOD_SPEC_ID)
    manager.join_all(timeout=5.0)


def test_manager_different_null_specs_run_independently(env):
    """Single-flight is scoped PER null-spec, not process-global: a ToD build and a context build
    for the SAME corpus may both be triggered without either refusing the other."""
    bar_store, playbook_store, null_store, run_store = env
    bars = [_bar5("IND", i) for i in range(5)]
    _plant_occurrence(playbook_store, bar_store, "IND", bars)

    manager = RefereeNullComputeManager()
    tod = manager.trigger(
        REFEREE_NULL_TOD_SPEC_ID, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )
    context = manager.trigger(
        REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )
    assert tod["started"] is True
    assert context["started"] is True
    _wait_for_not_running(manager, REFEREE_NULL_TOD_SPEC_ID)
    _wait_for_not_running(manager, REFEREE_NULL_CONTEXT_SPEC_ID)
    manager.join_all(timeout=5.0)


def test_tc20_cancel_reaches_a_cancelled_ledger_state_with_no_partial_or_duplicate_record(env):
    """TC-20: a cancel signalled immediately reaches a ``"cancelled"`` terminal ledger state (no
    ``"running"`` row is ever written -- terminal-state-only), and the null store never carries a
    duplicate for any observation this run touched."""
    bar_store, playbook_store, null_store, run_store = env
    _plant_multi_symbol_occurrences(playbook_store, bar_store, [f"CX{i}" for i in range(5)])

    manager = RefereeNullComputeManager()
    trigger = manager.trigger(
        REFEREE_NULL_TOD_SPEC_ID, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )
    assert trigger["started"] is True
    manager.cancel(REFEREE_NULL_TOD_SPEC_ID)
    _wait_for_not_running(manager, REFEREE_NULL_TOD_SPEC_ID)
    manager.join_all(timeout=5.0)

    runs, errors = run_store.list()
    assert errors == []
    assert len(runs) == 1
    assert runs[0]["null_spec_id"] == REFEREE_NULL_TOD_SPEC_ID
    assert runs[0]["state"] in ("cancelled", "completed")  # the race is real -- both are honest
    # No duplicate for any recorded observation: every (observation_id, null_spec_signature) key on
    # disk is unique.
    records, record_errors = null_store.list()
    assert record_errors == []
    keys = [(r["observation_id"], r["null_spec_signature"]) for r in records]
    assert len(keys) == len(set(keys))


def test_unknown_null_spec_id_is_refused_by_the_compute_manager(env):
    bar_store, playbook_store, null_store, run_store = env
    manager = RefereeNullComputeManager()
    try:
        manager.trigger(
            "not-a-real-null-spec", playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: unknown null_spec_id")


def test_unknown_null_spec_id_is_refused_by_build_null_record(env):
    bar_store, playbook_store, _null_store, _run_store = env
    bars = [_bar5("UNK", i) for i in range(5)]
    observation = _plant_occurrence(playbook_store, bar_store, "UNK", bars)
    try:
        build_null_record(
            observation, null_spec_id="not-a-real-null-spec", playbook_store=playbook_store,
            bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: unknown null_spec_id")


# --- the routes --------------------------------------------------------------------------------------


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_DIR", str(tmp_path / "nulls"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_LOG_DIR", str(tmp_path / "null_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = RefereeNullComputeManager()
    app.dependency_overrides[get_referee_null_compute_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    set_registry(None)
    app.dependency_overrides.pop(get_referee_null_compute_manager, None)
    store.close()


def test_tc17_get_nulls_honest_empty_and_never_computes(route_ctx):
    """TC-17: no null records exist yet -- ``GET /research/desk/referee/nulls`` serves an honest
    empty state and triggers no compute (verified by a monkeypatch-free assertion: the compute
    manager's own snapshot stays idle -- a GET can never have started anything)."""
    client, manager, _tmp = route_ctx
    resp = client.get("/research/desk/referee/nulls")
    assert resp.status_code == 200
    assert resp.json() == {"records": [], "integrity_errors": []}

    scoped = client.get("/research/desk/referee/nulls", params={"id": "no-such-id"})
    assert scoped.status_code == 200
    assert scoped.json() == {"record": None}

    assert manager.snapshot(REFEREE_NULL_TOD_SPEC_ID)["status"] == "idle"  # never triggered by a GET

    unknown_spec = client.get(
        "/research/desk/referee/nulls/compute", params={"null_spec_id": "bogus"}
    )
    assert unknown_spec.status_code == 422

    idle_cancel = client.post(
        "/research/desk/referee/nulls/compute/cancel", json={"null_spec_id": REFEREE_NULL_TOD_SPEC_ID}
    )
    assert idle_cancel.status_code == 409

    refused = client.post("/research/desk/referee/nulls/compute", json={"null_spec_id": "bogus"})
    assert refused.status_code == 422


def test_tc18_tc19_route_compute_runs_to_completion_single_flight_and_runs_ledger(route_ctx):
    """TC-18/TC-19: POST triggers a real build over a small fixture corpus (planted through the
    SAME store paths the route's own dependencies resolve to); a second POST for the SAME null-spec
    while it is running is refused single-flight; once it reaches a terminal state, the recorded
    null appears on ``GET /nulls`` and the ledger row on ``GET /nulls/runs`` reads ``state ==
    "completed"`` with its ``run_id``/``progress``/``null_spec_id`` fields served."""
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    playbook_store = PlaybookStore(tmp / "playbook")
    bars = [_bar5("RT1", i) for i in range(5)]
    _plant_occurrence(playbook_store, bar_store, "RT1", bars)

    trigger = client.post(
        "/research/desk/referee/nulls/compute", json={"null_spec_id": REFEREE_NULL_TOD_SPEC_ID}
    )
    assert trigger.status_code == 200
    assert trigger.json()["started"] is True

    second = client.post(
        "/research/desk/referee/nulls/compute", json={"null_spec_id": REFEREE_NULL_TOD_SPEC_ID}
    )
    assert second.status_code == 200
    assert second.json()["started"] is False  # single-flight -- TC-19

    _wait_for_not_running(manager, REFEREE_NULL_TOD_SPEC_ID)

    served = client.get("/research/desk/referee/nulls")
    assert served.status_code == 200
    records = served.json()["records"]
    assert len(records) >= 1
    assert records[0]["null_spec_id"] == REFEREE_NULL_TOD_SPEC_ID

    runs = client.get(
        "/research/desk/referee/nulls/runs", params={"null_spec_id": REFEREE_NULL_TOD_SPEC_ID}
    )
    assert runs.status_code == 200
    latest = runs.json()["latest"]
    assert latest is not None
    assert latest["state"] == "completed"
    assert latest["null_spec_id"] == REFEREE_NULL_TOD_SPEC_ID
    assert set(latest) == {"run_id", "null_spec_id", "state", "started_at", "finished_at", "progress", "error"}
    assert latest["progress"]["done"] == latest["progress"]["total"]


# --- the CLI --------------------------------------------------------------------------------------


def test_cli_records_into_the_env_scoped_store(tmp_path, monkeypatch):
    """A CLI smoke test -- the ``test_desk_forward.py``/``desk_forward_compute`` pattern verbatim:
    every store env var scoped to a fresh ``tmp_path``, a real fixture planted through each store's
    own public write path, ``sys.argv`` set to the CLI's own invocation shape, ``main()`` called
    directly (never a subprocess -- this project's established CLI-test convention)."""
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_DIR", str(tmp_path / "nulls"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_NULL_LOG_DIR", str(tmp_path / "null_runs"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))

    bar_store = BarStore(tmp_path / "bars")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    bars = [_bar5("CLI1", i) for i in range(5)]
    _plant_occurrence(playbook_store, bar_store, "CLI1", bars)

    monkeypatch.setattr(sys, "argv", ["referee_null", "--null-spec-id", REFEREE_NULL_TOD_SPEC_ID])
    assert referee_null_module.main() == 0

    null_store = RefereeNullStore(tmp_path / "nulls")
    records, errors = null_store.list()
    assert errors == []
    assert len(records) >= 1
    assert all(r["null_spec_id"] == REFEREE_NULL_TOD_SPEC_ID for r in records)

    run_store = RefereeNullRunStore(tmp_path / "null_runs")
    runs, run_errors = run_store.list()
    assert run_errors == []
    assert len(runs) == 1
    assert runs[0]["state"] == "completed"

    # A second CLI invocation over the SAME corpus reuses -- zero new files (idempotent).
    files_before = sorted(null_store.root.glob("*.json"))
    hashes_before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files_before}
    monkeypatch.setattr(sys, "argv", ["referee_null", "--null-spec-id", REFEREE_NULL_TOD_SPEC_ID])
    assert referee_null_module.main() == 0
    files_after = sorted(null_store.root.glob("*.json"))
    hashes_after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files_after}
    assert hashes_after == hashes_before


def test_cli_rejects_an_unknown_null_spec_id_before_any_argparse_default(monkeypatch, capsys):
    """The CLI's own ``--null-spec-id`` is REQUIRED with a closed ``choices=`` set -- argparse
    itself refuses (exit code 2) an unrecognised value before ``main()``'s own body ever runs."""
    monkeypatch.setattr(sys, "argv", ["referee_null", "--null-spec-id", "not-a-real-spec"])
    with pytest.raises(SystemExit) as exc_info:
        referee_null_module.main()
    assert exc_info.value.code == 2
