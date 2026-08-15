"""``referee_evidence.py`` + ``GET /research/desk/referee/evidence`` (Era 6 "The Referee", J-01) —
the readiness fold. Test-first contract: TC-1 through TC-5 in
``docs/phases/goal-referee-iter-1.md``.

Builds its own hand-crafted ``PlaybookStore``/``DatasetStore``/``JournalStore`` records directly
through each store's own public write path (never a real ``compute_playbook`` walk or a real
backtest run — those paths are already covered end to end by ``test_desk_playbook.py``/
``test_backtests.py``), so every pooled count in every assertion below is a number this file's own
hand computation can reproduce, not one a compute happened to produce."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.base import Side, TradeEvent
from app.research import desk_playbook as desk_playbook_module
from app.research import referee_evidence as referee_evidence_module
from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
from app.research.desk_playbook import (
    PLAYBOOK_REGISTER,
    PlaybookStore,
    playbook_parameters,
    resolve_desk_playbook_dir,
)
from app.research.desk_routes import get_playbook_store
from app.research.referee_evidence import (
    REFEREE_FORMING_BAR_BASIS_CAVEAT,
    REFEREE_SESSION_COMPLETE_ET,
    REFEREE_TICK_GATE_SYMBOL_DAYS,
    RefereeObservationCache,
    _record_detector_basis,
    _signal_reaches_session_complete,
    _tick_gate_state,
    current_playbook_detector_basis,
    playbook_observations,
    resolve_referee_obs_cache_db_path,
    strategy_observations,
)
from app.research.routes import ResearchRegistry, get_dataset_store, set_registry
from app.research.store import BacktestRecord, JournalStore
from test_copy_discipline import find_violations

E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET, the codebase's standard fixture anchor


# --- fixture builders (the store's own public write path — never a hand-typed file) ----------------


def _signal(setup_id: str, side: str) -> dict:
    """A minimal recorded signal — ``PlaybookStore`` validates nothing about signal shape beyond
    "is dict-able", and this fold only ever reads ``setup_id``/``side`` off one, so a real signal's
    ``forward``/``geometry``/... leaves are irrelevant noise here."""
    return {"setup_id": setup_id, "side": side}


def _plant_playbook_record(
    store: PlaybookStore, *, session_date: str, signature: str, signals: list[dict],
    parameters: dict | None = None,
) -> dict:
    return store.record(
        session_date=session_date,
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=signature,
        payload_version=3,
        parameters=parameters if parameters is not None else playbook_parameters(),
        register=PLAYBOOK_REGISTER,
        signals=signals,
        absences=[],
        diagnostics=[],
    )


def _events(symbol: str, n: int) -> list[TradeEvent]:
    return [TradeEvent(symbol, float(i), 100.0 + i, 10, Side.BUY) for i in range(n)]


def _plant_dataset(store: DatasetStore, *, symbol: str, split: str, source_id: str) -> dict:
    return store.record(
        symbol=symbol,
        source="fixture",
        source_kind="fixture",
        source_id=source_id,
        split=split,
        window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-01T01:00:00Z",
        data_feed="sim",
        epoch_anchor=0.0,
        events=_events(symbol, 3),
    )


def _plant_backtest(
    journal_store: JournalStore, *, backtest_id: str, trades: list[dict] | None = None,
    status: str = "done",
) -> None:
    payload: dict = {"id": backtest_id, "status": status}
    if trades is not None:
        payload["result"] = {"trades": trades}
    journal_store.insert_backtest(
        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
    )


@pytest.fixture
def client(tmp_path):
    journal_store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal_store, CONFIG)
    set_registry(registry)
    playbook_store = PlaybookStore(tmp_path / "playbook")
    dataset_store = DatasetStore(tmp_path / "datasets")
    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
    with TestClient(app) as c:
        yield c, playbook_store, dataset_store, journal_store
    app.dependency_overrides.pop(get_playbook_store, None)
    app.dependency_overrides.pop(get_dataset_store, None)
    set_registry(None)
    journal_store.close()


# --- TC-5: the zero-corpus honest-empty case --------------------------------------------------------


def test_zero_corpus_is_an_honest_200_not_a_404(client):
    c, _playbook_store, _dataset_store, _journal_store = client
    response = c.get("/research/desk/referee/evidence")
    assert response.status_code == 200
    body = response.json()
    assert body["playbook_occurrence"]["records"] == 0
    assert body["playbook_occurrence"]["distinct_sessions"] == 0
    assert body["playbook_occurrence"]["signals_at_current_basis"] == 0
    assert body["playbook_occurrence"]["per_setup_side"] == []
    assert body["strategy_trade"]["dataset_count"] == 0
    assert body["strategy_trade"]["per_split_counts"] == {"train": 0, "holdout": 0}
    assert body["strategy_trade"]["trade_count"] == 0
    assert body["strategy_trade"]["tick_gate_met"] is False


# --- TC-1 / TC-2: the playbook readiness fold --------------------------------------------------------


def test_playbook_readiness_pools_newest_per_date_at_the_current_basis(client):
    c, store, _dataset_store, _journal_store = client

    # Date D1: an OLDER record (1 signal) SUPERSEDED by a NEWER one (2 signals) at the SAME date —
    # only the newer record's own signals may count (T-6's newest-per-date rule).
    _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-d1-older",
        signals=[_signal("capitulation", "long")],
    )
    _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-d1-newer",
        signals=[_signal("capitulation", "long"), _signal("jbe", "short")],
    )
    # Date D2: one more current-basis record, pooling into the SAME two cells.
    _plant_playbook_record(
        store, session_date="2026-06-09", signature="sig-d2",
        signals=[
            _signal("capitulation", "long"), _signal("capitulation", "long"),
            _signal("jbe", "short"),
        ],
    )
    # Date D3: a STALE-basis record (parameters deliberately different from the LIVE
    # playbook_parameters()) — must count toward records/distinct_sessions but NEVER toward
    # signals_at_current_basis or per_setup_side.
    stale_parameters = {**playbook_parameters(), "min_n_disclosure": 999}
    _plant_playbook_record(
        store, session_date="2026-06-10", signature="sig-d3-stale",
        signals=[_signal("capitulation", "long")] * 5,
        parameters=stale_parameters,
    )

    response = c.get("/research/desk/referee/evidence")
    assert response.status_code == 200
    occurrence = response.json()["playbook_occurrence"]

    assert occurrence["detector_basis"] == current_playbook_detector_basis()
    assert occurrence["config_fingerprint"] == CONFIG.config_fingerprint()
    assert occurrence["records"] == 4  # R1a, R1b, R2, R3 — every file on disk, unfiltered
    assert occurrence["distinct_sessions"] == 3  # D1, D2, D3
    # R1b's 2 + R2's 3 — R1a is superseded (same date, older), R3 is stale-basis-excluded.
    assert occurrence["signals_at_current_basis"] == 5

    per_cell = {(row["setup"], row["side"]): row for row in occurrence["per_setup_side"]}
    assert set(per_cell) == {("capitulation", "long"), ("jbe", "short")}
    assert per_cell[("capitulation", "long")]["n"] == 3  # R1b's 1 + R2's 2
    assert per_cell[("capitulation", "long")]["n_sessions"] == 2  # D1, D2
    assert per_cell[("jbe", "short")]["n"] == 2  # R1b's 1 + R2's 1
    assert per_cell[("jbe", "short")]["n_sessions"] == 2  # D1, D2

    # iter-4 TC-9 (Lead 1): the D3 stale-basis record is now DISCLOSED, not silently dropped --
    # exactly one entry, naming D3's own record_detector_basis (the SAME formula
    # `_record_detector_basis` applies to any recorded record, independent of which record's
    # parameters are passed in).
    assert occurrence["stale_basis_dates"] == [
        {
            "session_date": "2026-06-10",
            "record_detector_basis": _record_detector_basis({"parameters": stale_parameters}),
        }
    ]


# --- TC-3: the strategy readiness fold ---------------------------------------------------------------


def test_strategy_readiness_counts_datasets_splits_and_trades(client):
    c, _playbook_store, dataset_store, journal_store = client

    _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
    _plant_dataset(dataset_store, symbol="MSFT", split=SPLIT_TRAIN, source_id="ds-2")
    _plant_dataset(dataset_store, symbol="GOOG", split=SPLIT_HOLDOUT, source_id="ds-3")

    _plant_backtest(
        journal_store, backtest_id="bt-1",
        trades=[{"net_r": 1.0}, {"net_r": -0.5}, {"net_r": 0.8}],
    )
    _plant_backtest(journal_store, backtest_id="bt-2", trades=[{"net_r": 0.3}, {"net_r": -1.0}])
    _plant_backtest(journal_store, backtest_id="bt-3", status="running")  # no result yet -> 0

    response = c.get("/research/desk/referee/evidence")
    assert response.status_code == 200
    strategy = response.json()["strategy_trade"]

    assert strategy["dataset_count"] == 3
    assert strategy["per_split_counts"] == {"train": 2, "holdout": 1}
    assert strategy["trade_count"] == 5  # 3 + 2 + 0 (the running record contributes nothing)


# --- TC-4: the honest unmet tick gate + the Card-6.4 basis caveat ------------------------------------


def test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat(client):
    c, _playbook_store, dataset_store, _journal_store = client
    _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")

    response = c.get("/research/desk/referee/evidence")
    strategy = response.json()["strategy_trade"]

    assert strategy["tick_gate_met"] is False
    assert strategy["tick_gate_statement"] != ""
    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in strategy["tick_gate_statement"]
    assert strategy["basis_caveats"] == [REFEREE_FORMING_BAR_BASIS_CAVEAT]


def test_forming_bar_basis_caveat_passes_copy_discipline():
    """The Card-6.4 caveat is authored for the FIRST time this iteration (docs/goal.md's NOTES) —
    verified against the copy-discipline lexicon directly (the PLAYBOOK_REGISTER/EVIDENCE_REGISTER
    per-module precedent), since it is served on a route the existing taxonomy-payload walk in
    ``test_copy_discipline.py`` does not reach."""
    assert find_violations(REFEREE_FORMING_BAR_BASIS_CAVEAT) == []


# --- the tick-gate arithmetic, unit-level (both branches; TC-4's statement contract) -----------------


def test_tick_gate_state_unmet_branch():
    met, statement = _tick_gate_state(3)
    assert met is False
    assert "3" in statement
    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in statement


def test_tick_gate_state_met_branch():
    met, statement = _tick_gate_state(REFEREE_TICK_GATE_SYMBOL_DAYS)
    assert met is True
    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS) in statement

    comfortably_met, statement2 = _tick_gate_state(REFEREE_TICK_GATE_SYMBOL_DAYS + 50)
    assert comfortably_met is True
    assert str(REFEREE_TICK_GATE_SYMBOL_DAYS + 50) in statement2


# --- TC-11: the iteration-1 documentation rider ------------------------------------------------------


def test_module_docstring_pins_integrity_errors_as_part_of_the_response_shape():
    """The iter-1 eval/coherence rider: the two already-served ``integrity_errors`` fields are now
    named explicitly as part of the pinned ``GET /research/desk/referee/evidence`` response shape
    -- documentation-only, behavior unchanged (J-01's own fixture tests above still pass
    unmodified, proving the shape itself never moved)."""
    doc = referee_evidence_module.__doc__ or ""
    assert "playbook_occurrence.integrity_errors" in doc
    assert "strategy_trade.integrity_errors" in doc


# === J-02: the typed evidence contract -- fixture builders (goal-referee-iter-2 TC-1..TC-9) ==========
#
# Every fixture below plants records through each store's own public write path
# (``PlaybookStore.record`` / ``DatasetStore.record`` / ``JournalStore.insert_backtest`` --
# ``_plant_playbook_record``/``_plant_dataset`` reused verbatim from the J-01 section above), so
# every pooled count and every served value below is a number this file's own hand computation can
# reproduce, never one a real compute happened to produce.


def _horizon(
    *,
    return_pct: float | None = None,
    mdd_long_pct: float | None = None,
    mdd_short_pct: float | None = None,
    truncated: bool = False,
    reason: str | None = None,
) -> dict:
    """One ``forward["horizons"][label]`` leaf, shaped exactly as ``desk_forward._measure_from``
    returns it (every key present, ``exit_price``/``effective_minutes`` are irrelevant filler for
    this fold since the adapter never reads them)."""
    return {
        "return_pct": return_pct,
        "exit_price": 0.0,
        "mdd_long_pct": mdd_long_pct,
        "mdd_short_pct": mdd_short_pct,
        "truncated": truncated,
        "effective_minutes": 0,
        "reason": reason,
    }


# 15 DISTINCT, hand-typed values -- one per ``DESK_FORWARD_MEASURE_KEYS`` entry -- so a test can
# assert each key's own served value by literal comparison, never by re-deriving it through the
# same mapping the adapter itself uses.
_EXPECTED_FULL_FORWARD_VALUES = {
    "1m": 10.0, "5m": 20.0, "1h": 30.0, "4h": 40.0, "to_close": 99.0,
    "mdd_long_1m": -1.0, "mdd_long_5m": -2.0, "mdd_long_1h": -3.0, "mdd_long_4h": -4.0,
    "mdd_long": -9.0,
    "mdd_short_1m": -1.5, "mdd_short_5m": -2.5, "mdd_short_1h": -3.5, "mdd_short_4h": -4.5,
    "mdd_short": -9.5,
}


def _full_forward(at_utc: str, *, minutes_to_close: int = 240) -> dict:
    """A fully-measured ``forward`` block -- every one of the 15 ``DESK_FORWARD_MEASURE_KEYS``
    leaves present and unexcluded, matching ``_EXPECTED_FULL_FORWARD_VALUES`` exactly."""
    return {
        "at_utc": at_utc,
        "entry_price": 100.0,
        "entry_kind": "level",
        "horizons": {
            "1m": _horizon(return_pct=10.0, mdd_long_pct=-1.0, mdd_short_pct=-1.5),
            "5m": _horizon(return_pct=20.0, mdd_long_pct=-2.0, mdd_short_pct=-2.5),
            "1h": _horizon(return_pct=30.0, mdd_long_pct=-3.0, mdd_short_pct=-3.5),
            "4h": _horizon(return_pct=40.0, mdd_long_pct=-4.0, mdd_short_pct=-4.5),
        },
        "to_close_pct": 99.0,
        "close_price": 101.0,
        "minutes_to_close": minutes_to_close,
        "mdd_long_pct": -9.0,
        "mdd_short_pct": -9.5,
    }


def _measured_signal(*, symbol: str, side: str, setup_id: str, trigger_ts: str, forward: dict) -> dict:
    """A minimal already-measured signal -- only the fields ``playbook_observations`` reads."""
    return {"symbol": symbol, "setup_id": setup_id, "side": side, "trigger_ts": trigger_ts, "forward": forward}


def _trade(*, direction: str = "long", logical_ts: float = 100.0, net_r: float = 1.0) -> dict:
    """A minimal ``_close_trade``-shaped trade -- only the fields the strategy adapter reads."""
    return {
        "setup_type": "v1",
        "direction": direction,
        "entry": {"logical_ts": logical_ts, "price": 100.0, "fill_price": 100.0, "spread": 0.0},
        "exit": {
            "logical_ts": logical_ts + 60.0, "price": 101.0, "fill_price": 101.0, "spread": 0.0,
            "reason": "horizon",
        },
        "invalidation_price": 99.0,
        "r_basis": 1.0,
        "shares": 1.0,
        "gross_r": net_r,
        "net_r": net_r,
        "gross_usd": 0.0,
        "net_usd": 0.0,
        "fees_usd": 0.0,
        "slippage_usd": 0.0,
    }


def _plant_backtest_result(
    journal_store: JournalStore,
    *,
    backtest_id: str,
    dataset: dict,
    strategy_id: str = "v1",
    profile: str = "default",
    config_fingerprint: str | None = None,
    trades: list[dict],
    null_trades: list[dict],
) -> None:
    """Plant one ``done`` backtest report whose ``result`` block already carries the dataset
    joined verbatim -- ``backtests.py``'s own result-block shape (§0.4's `"dataset": dataset_meta`
    line), reproduced by hand rather than run through a real replay."""
    payload = {
        "id": backtest_id,
        "status": "done",
        "result": {
            "dataset": dataset,
            "strategy_id": strategy_id,
            "profile": profile,
            "config_fingerprint": config_fingerprint or CONFIG.config_fingerprint(),
            "trades": trades,
            "null_baseline": {"seed": 1729, "entry_count": len(null_trades), "trades": null_trades},
        },
    }
    journal_store.insert_backtest(
        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
    )


def _hash_store_files(*roots: Path) -> dict[str, str]:
    digest: dict[str, str] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


# --- TC-1 / TC-6: the playbook observation contract, cold, including one excluded leaf ---------------


def test_playbook_observations_matches_hand_computed_golden_fixture_and_excludes_unmeasurable_leaves(
    client,
):
    c, store, _dataset_store, _journal_store = client
    fingerprint = CONFIG.config_fingerprint()
    basis = current_playbook_detector_basis()

    forward_a = _full_forward("2026-06-08T13:35:00.000000Z")
    signal_a = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_a,
    )
    # A second signal with ONE structurally-unmeasurable leaf -- the real "1m horizon finer than
    # the 5m touch series" absence text `_measure_from` itself writes -- TC-1's own "at least one
    # truncated/unmeasurable leaf" requirement, and TC-6's dedicated exclusion case.
    forward_b = _full_forward("2026-06-08T14:00:00.000000Z")
    forward_b["horizons"]["1m"] = _horizon(
        reason="the 1m horizon is finer than the 5m touch series",
    )
    signal_b = _measured_signal(
        symbol="MSFT", side="short", setup_id="jbe",
        trigger_ts="2026-06-08T14:00:00.000000Z", forward=forward_b,
    )
    record = _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-tc1", signals=[signal_a, signal_b],
    )

    result = playbook_observations(store, fingerprint)

    assert result["detector_basis"] == basis
    assert result["config_fingerprint"] == fingerprint
    # signal_a: all 15 keys. signal_b: the "1m" horizon's own reason excludes THREE keys that
    # share its window -- "1m", "mdd_long_1m", "mdd_short_1m" (_resolve_leaf's own rule: a
    # horizon's return and both its drawdowns are measured over the identical window, so all
    # three are excluded together) -- leaving 12.
    assert len(result["observations"]) == 15 + 12

    by_key = {(o["symbol"], o["measure_key"]): o for o in result["observations"]}
    for measure_key, expected_value in _EXPECTED_FULL_FORWARD_VALUES.items():
        assert by_key[("AAPL", measure_key)] == {
            "evidence_family": "playbook_occurrence",
            "observation_id": f"playbook:{record['id']}:0:{measure_key}",
            "symbol": "AAPL",
            "session_date": "2026-06-08",
            "anchor_ts": "2026-06-08T13:35:00.000000Z",
            "side": "long",
            "measure_key": measure_key,
            "value": expected_value,
            "cluster_key": "2026-06-08",
            "provenance": {
                "detector_basis": basis,
                "config_fingerprint": fingerprint,
                "context_algorithm_version": None,
                "source_record_id": record["id"],
                "basis_caveats": [],
            },
        }

    excluded_keys = {"1m", "mdd_long_1m", "mdd_short_1m"}
    for key in excluded_keys:
        assert ("MSFT", key) not in by_key  # the excluded leaves -- no fallback, no fabricated value
    for measure_key, expected_value in _EXPECTED_FULL_FORWARD_VALUES.items():
        if measure_key in excluded_keys:
            continue
        obs = by_key[("MSFT", measure_key)]
        assert obs["value"] == expected_value
        assert obs["side"] == "short"
        assert obs["anchor_ts"] == "2026-06-08T14:00:00.000000Z"
        assert obs["observation_id"] == f"playbook:{record['id']}:1:{measure_key}"
        assert obs["cluster_key"] == "2026-06-08"

    assert result["excluded_leaves"] == 3
    assert result["coverage_by_date"] == [{"session_date": "2026-06-08", "symbol_count": 2}]
    assert result["coverage_shrink_disclosures"] == []


# --- TC-2: cold / warm / deleted-cache parity ---------------------------------------------------------


def test_playbook_observations_cache_cold_warm_deleted_parity(client, tmp_path):
    c, store, _dataset_store, _journal_store = client
    forward = _full_forward("2026-06-08T13:35:00.000000Z")
    signal = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
    )
    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-tc2", signals=[signal])
    fingerprint = CONFIG.config_fingerprint()

    db_path = str(tmp_path / "referee_obs_cache.db")
    cache_cold = RefereeObservationCache(db_path)
    result_cold = playbook_observations(store, fingerprint, cache=cache_cold)

    cache_warm = RefereeObservationCache(db_path)  # a FRESH connection to the now-populated file
    result_warm = playbook_observations(store, fingerprint, cache=cache_warm)

    os.remove(db_path)
    cache_deleted = RefereeObservationCache(db_path)  # recreates the file, empty
    result_deleted = playbook_observations(store, fingerprint, cache=cache_deleted)

    assert result_cold["observations"]  # sanity: the fixture actually produced observations
    assert result_cold == result_warm == result_deleted


# --- TC-3: two signatures, identical parameters -> ONE pooled detector_basis --------------------------


def test_playbook_observations_pools_two_signatures_with_identical_parameters_into_one_basis(client):
    c, store, _dataset_store, _journal_store = client
    forward_1 = _full_forward("2026-06-08T13:35:00.000000Z")
    signal_1 = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_1,
    )
    forward_2 = _full_forward("2026-06-09T13:35:00.000000Z")
    signal_2 = _measured_signal(
        symbol="MSFT", side="long", setup_id="capitulation",
        trigger_ts="2026-06-09T13:35:00.000000Z", forward=forward_2,
    )
    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-x", signals=[signal_1])
    _plant_playbook_record(store, session_date="2026-06-09", signature="sig-y", signals=[signal_2])

    result = playbook_observations(store, CONFIG.config_fingerprint())

    assert {o["session_date"] for o in result["observations"]} == {"2026-06-08", "2026-06-09"}
    assert {o["provenance"]["detector_basis"] for o in result["observations"]} == {
        current_playbook_detector_basis()
    }


# --- TC-4: a monkeypatched detector constant splits the pool ------------------------------------------


def test_playbook_detector_basis_splits_on_a_monkeypatched_constant(client, monkeypatch):
    c, store, _dataset_store, _journal_store = client
    fingerprint = CONFIG.config_fingerprint()

    forward_1 = _full_forward("2026-06-08T13:35:00.000000Z")
    signal_1 = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_1,
    )
    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-before", signals=[signal_1])
    basis_before = current_playbook_detector_basis()

    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_MIN_N_DISCLOSURE", 999)
    basis_after = current_playbook_detector_basis()
    assert basis_after != basis_before  # sanity: the monkeypatch genuinely moves the LIVE basis

    forward_2 = _full_forward("2026-06-09T13:35:00.000000Z")
    signal_2 = _measured_signal(
        symbol="MSFT", side="long", setup_id="capitulation",
        trigger_ts="2026-06-09T13:35:00.000000Z", forward=forward_2,
    )
    _plant_playbook_record(store, session_date="2026-06-09", signature="sig-after", signals=[signal_2])

    result_after = playbook_observations(store, fingerprint)
    assert result_after["detector_basis"] == basis_after
    assert {o["session_date"] for o in result_after["observations"]} == {"2026-06-09"}
    assert all(o["provenance"]["detector_basis"] == basis_after for o in result_after["observations"])

    monkeypatch.undo()
    result_before = playbook_observations(store, fingerprint)
    assert result_before["detector_basis"] == basis_before
    assert {o["session_date"] for o in result_before["observations"]} == {"2026-06-08"}
    assert all(
        o["provenance"]["detector_basis"] == basis_before for o in result_before["observations"]
    )


# --- TC-5: same-date dedup, newest wins, coverage-shrink disclosure ------------------------------------


def test_playbook_observations_dedup_selects_newest_and_discloses_coverage_shrink(client):
    c, store, _dataset_store, _journal_store = client
    forward = _full_forward("2026-06-08T13:35:00.000000Z")
    older_signals = [
        _measured_signal(
            symbol=sym, side="long", setup_id="capitulation",
            trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
        )
        for sym in ("AAPL", "MSFT", "GOOG")
    ]
    newer_signals = [
        _measured_signal(
            symbol=sym, side="long", setup_id="capitulation",
            trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
        )
        for sym in ("AAPL", "MSFT")
    ]
    older = _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-older", signals=older_signals,
    )
    newer = _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-newer", signals=newer_signals,
    )

    result = playbook_observations(store, CONFIG.config_fingerprint())

    assert {o["symbol"] for o in result["observations"]} == {"AAPL", "MSFT"}  # newer record only
    assert result["coverage_by_date"] == [{"session_date": "2026-06-08", "symbol_count": 2}]
    assert result["coverage_shrink_disclosures"] == [
        {
            "session_date": "2026-06-08",
            "newest_record_id": newer["id"],
            "newest_symbol_count": 2,
            "superseded_record_id": older["id"],
            "superseded_symbol_count": 3,
        }
    ]


# --- iter-4 TC-10 (Lead 1): the sibling stale-basis disclosure for playbook_observations() -----------


def test_playbook_observations_discloses_stale_basis_dates_with_zero_change_to_other_fields(client):
    """iter-4 TC-10: one live-basis date (contributes its observations normally) and one
    stale-basis date (parameters deliberately different from the LIVE playbook_parameters() --
    the SAME construction TC-9's own D3 fixture in
    test_playbook_readiness_pools_newest_per_date_at_the_current_basis uses) -- the stale date is
    named in result["stale_basis_dates"] and excluded from observations/coverage_by_date/
    session_completeness exactly as it was (silently) before this iteration, with zero change to
    any other field's value."""
    c, store, _dataset_store, _journal_store = client
    fingerprint = CONFIG.config_fingerprint()

    live_forward = _full_forward("2026-06-08T13:35:00.000000Z")
    live_signal = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=live_forward,
    )
    _plant_playbook_record(
        store, session_date="2026-06-08", signature="sig-live", signals=[live_signal],
    )

    stale_parameters = {**playbook_parameters(), "min_n_disclosure": 999}
    stale_forward = _full_forward("2026-06-09T13:35:00.000000Z")
    stale_signal = _measured_signal(
        symbol="MSFT", side="short", setup_id="jbe",
        trigger_ts="2026-06-09T13:35:00.000000Z", forward=stale_forward,
    )
    _plant_playbook_record(
        store, session_date="2026-06-09", signature="sig-stale", signals=[stale_signal],
        parameters=stale_parameters,
    )

    result = playbook_observations(store, fingerprint)

    assert result["detector_basis"] == current_playbook_detector_basis()
    assert result["config_fingerprint"] == fingerprint
    assert {o["symbol"] for o in result["observations"]} == {"AAPL"}  # the stale date excluded
    assert result["excluded_leaves"] == 0
    assert result["coverage_by_date"] == [{"session_date": "2026-06-08", "symbol_count": 1}]
    assert result["coverage_shrink_disclosures"] == []
    assert {s["session_date"] for s in result["session_completeness"]} == {"2026-06-08"}
    assert result["stale_basis_dates"] == [
        {
            "session_date": "2026-06-09",
            "record_detector_basis": _record_detector_basis({"parameters": stale_parameters}),
        }
    ]


# --- TC-7 / TC-8: the strategy observation contract, primary trades and the paired null set -----------


def test_strategy_observations_emits_net_r_with_the_forming_bar_caveat(client):
    c, _playbook_store, dataset_store, journal_store = client
    dataset = _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
    trades = [
        _trade(direction="long", logical_ts=100.0, net_r=1.5),
        _trade(direction="short", logical_ts=200.0, net_r=-0.4),
    ]
    _plant_backtest_result(
        journal_store, backtest_id="bt-tc7", dataset=dataset, trades=trades, null_trades=[],
    )

    result = strategy_observations(journal_store)

    assert len(result["observations"]) == 2
    obs0 = result["observations"][0]
    assert obs0["evidence_family"] == "strategy_trade"
    assert obs0["observation_id"] == "strategy:bt-tc7:trade:0"
    assert obs0["symbol"] == "AAPL"
    assert obs0["side"] == "long"
    assert obs0["measure_key"] == "net_r"
    assert obs0["value"] == 1.5
    assert obs0["cluster_key"] == dataset["id"]
    # dataset["epoch_anchor"] == 0.0 (the shared `_plant_dataset` fixture) + logical_ts 100.0 ->
    # epoch 100.0 == 1970-01-01T00:01:40Z UTC, which is 1969-12-31T19:01:40 ET (UTC-5, no DST in
    # January) -- the ET calendar date crosses to the PRIOR day, hand-verified proof this is a
    # real ET conversion, not a UTC passthrough.
    assert obs0["anchor_ts"] == "1970-01-01T00:01:40.000000Z"
    assert obs0["session_date"] == "1969-12-31"
    assert obs0["provenance"]["detector_basis"] is None
    assert obs0["provenance"]["context_algorithm_version"] is None
    assert obs0["provenance"]["source_record_id"] == "bt-tc7"
    assert obs0["provenance"]["basis_caveats"] == [REFEREE_FORMING_BAR_BASIS_CAVEAT]
    assert obs0["provenance"]["basis_caveats"][0] is REFEREE_FORMING_BAR_BASIS_CAVEAT

    obs1 = result["observations"][1]
    assert obs1["side"] == "short"
    assert obs1["value"] == -0.4
    assert obs1["observation_id"] == "strategy:bt-tc7:trade:1"
    assert result["null_observations"] == []


def test_strategy_observations_keeps_random_null_trades_separately_labeled(client):
    c, _playbook_store, dataset_store, journal_store = client
    dataset = _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
    trades = [_trade(direction="long", logical_ts=100.0, net_r=1.0)]
    null_trades = [
        _trade(direction="short", logical_ts=50.0, net_r=-0.2),
        _trade(direction="long", logical_ts=150.0, net_r=0.3),
    ]
    _plant_backtest_result(
        journal_store, backtest_id="bt-tc8", dataset=dataset, trades=trades, null_trades=null_trades,
    )

    result = strategy_observations(journal_store)

    assert len(result["observations"]) == 1
    assert len(result["null_observations"]) == 2
    assert result["observations"][0]["value"] == 1.0
    assert [o["value"] for o in result["null_observations"]] == [-0.2, 0.3]
    assert result["null_observations"][0]["observation_id"] == "strategy:bt-tc8:null:0"
    assert result["null_observations"][1]["observation_id"] == "strategy:bt-tc8:null:1"
    assert all(o["evidence_family"] == "strategy_trade" for o in result["null_observations"])
    assert all(
        o["provenance"]["basis_caveats"] == [REFEREE_FORMING_BAR_BASIS_CAVEAT]
        for o in result["null_observations"]
    )


def test_strategy_observations_skips_a_report_with_no_dataset_block(client):
    """Defensive completeness (never produced by the shipped runner, read defensively anyway): a
    ``result`` block with no ``dataset`` key contributes zero observations, never a
    fabricated-identity one, and never a crash."""
    c, _playbook_store, _dataset_store, journal_store = client
    payload = {
        "id": "bt-nodataset",
        "status": "done",
        "result": {"trades": [_trade()], "config_fingerprint": CONFIG.config_fingerprint()},
    }
    journal_store.insert_backtest(
        BacktestRecord(id="bt-nodataset", payload=payload, created_wall_ts=time.time())
    )

    result = strategy_observations(journal_store)

    assert result == {"observations": [], "null_observations": []}


# --- TC-9: neither adapter writes to any pre-existing store --------------------------------------------


def test_adapters_write_nothing_to_any_pre_existing_store(client):
    c, store, dataset_store, journal_store = client
    forward = _full_forward("2026-06-08T13:35:00.000000Z")
    signal = _measured_signal(
        symbol="AAPL", side="long", setup_id="capitulation",
        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
    )
    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-tc9", signals=[signal])
    dataset = _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-1")
    _plant_backtest_result(
        journal_store, backtest_id="bt-tc9", dataset=dataset, trades=[_trade()], null_trades=[],
    )

    journal_db_path = Path(journal_store._db_path)
    before = _hash_store_files(store.root, dataset_store._root)
    before_journal = (
        hashlib.sha256(journal_db_path.read_bytes()).hexdigest() if journal_db_path.exists() else None
    )

    playbook_observations(store, CONFIG.config_fingerprint())
    strategy_observations(journal_store)

    after = _hash_store_files(store.root, dataset_store._root)
    after_journal = (
        hashlib.sha256(journal_db_path.read_bytes()).hexdigest() if journal_db_path.exists() else None
    )

    assert after == before
    assert after_journal == before_journal


# === goal-referee-iter-3 carried rider 1 -- TC-20: _signal_reaches_session_complete ==================
#
# Zero assertions existed for this function before this iteration (a gap-blind estimate J-06's
# confirmatory-eligibility fold will lean on). ``REFEREE_SESSION_COMPLETE_ET`` = "15:55" ET.


def _forward_signal(at_utc: str, minutes_to_close: float) -> dict:
    """The minimal shape ``_signal_reaches_session_complete`` reads -- only
    ``forward["at_utc"]``/``forward["minutes_to_close"]``, exactly as it is read off a real
    already-measured signal's own ``forward`` block."""
    return {"forward": {"at_utc": at_utc, "minutes_to_close": minutes_to_close}}


def test_signal_reaches_session_complete_at_and_around_the_boundary():
    """TC-20: a fixture signal engineered so its computed ``last_bar_epoch`` lands exactly at, one
    second before, and one second after ``_session_complete_epoch(session_date)`` -- True at and
    after the boundary, False strictly before it. The anchor (``at_utc``) is held FIXED across all
    three cases; only ``minutes_to_close`` varies, isolating the boundary comparison from any other
    variable."""
    session_date = "2026-06-08"
    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
    anchor_epoch = boundary_epoch - 600.0  # 10 minutes before the boundary
    at_utc = referee_evidence_module._iso(anchor_epoch)

    at_boundary = _forward_signal(at_utc, 10.0)
    one_second_before = _forward_signal(at_utc, 10.0 - 1.0 / 60.0)
    one_second_after = _forward_signal(at_utc, 10.0 + 1.0 / 60.0)

    assert _signal_reaches_session_complete(at_boundary, session_date) is True
    assert _signal_reaches_session_complete(one_second_before, session_date) is False
    assert _signal_reaches_session_complete(one_second_after, session_date) is True


def test_signal_reaches_session_complete_is_false_with_no_forward_block():
    """A signal recorded before the (era-B2) forward-measurement pass existed carries no ``forward``
    block at all -- an honest False, never a crash and never a fabricated True."""
    assert _signal_reaches_session_complete({"symbol": "AAPL"}, "2026-06-08") is False


def test_signal_reaches_session_complete_reads_bar_count_minutes_not_wall_clock_and_says_so():
    """The disclosed bar-gap-blind limitation (module docstring), asserted as a real behavior
    rather than left to pass silently: ``minutes_to_close`` is a BAR-COUNT-equivalent figure, not
    measured wall-clock time, so this function is blind to any intra-session gap in the finest
    measurement series. Two signals whose ``(anchor_epoch, minutes_to_close)`` PRODUCT is identical
    are treated identically regardless of how much real wall-clock time actually elapsed on either
    side of a gap -- exercised here by anchoring EARLIER in the session (23 minutes before the
    boundary) with a bar-count-equivalent ``minutes_to_close`` that under-counts a gapped series and
    still lands exactly one second short of the boundary: the same honest False as a gap-free
    signal in the direct boundary test above, never a "corrected" True."""
    session_date = "2026-06-08"
    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
    anchor_epoch = boundary_epoch - 1380.0  # 23 minutes before the boundary (a gappier series)
    at_utc = referee_evidence_module._iso(anchor_epoch)
    gap_blind_minutes_to_close = (1380.0 - 1.0) / 60.0  # bar-count-equivalent, one second short

    signal = _forward_signal(at_utc, gap_blind_minutes_to_close)

    assert _signal_reaches_session_complete(signal, session_date) is False


def test_referee_session_complete_et_is_the_pinned_1555_boundary():
    """The boundary constant itself, pinned (spec Sec1): 15:55 ET."""
    assert REFEREE_SESSION_COMPLETE_ET == "15:55"


# === goal-referee-iter-3 carried rider 2 -- TC-21: resolve_referee_obs_cache_db_path =================
#
# Exported, never called, before this iteration.


def test_resolve_referee_obs_cache_db_path_env_override_returns_verbatim(monkeypatch):
    """TC-21 (env-var-override half): ``TAPEOLOGY_REFEREE_OBS_CACHE_DB`` set returns that EXACT
    path, verbatim -- never joined, never normalized."""
    monkeypatch.setenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", "/explicit/override/path/obs.db")

    result = resolve_referee_obs_cache_db_path("/anything/universe/dir")

    assert result == "/explicit/override/path/obs.db"


def test_resolve_referee_obs_cache_db_path_defaults_to_a_sibling_of_the_playbook_dir(monkeypatch):
    """TC-21 (sibling-of-playbook-dir default half): with the env var unset, the resolved path is
    ``referee_obs_cache.db`` co-located as a SIBLING of ``resolve_desk_playbook_dir``'s own
    resolved directory -- the ``playbook_evidence_cache_db_path`` resolver pattern verbatim, one
    level up (this module has no dependency on ``desk_routes.py``)."""
    monkeypatch.delenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", raising=False)
    universe_dir = "/some/resolved/desk/universe"
    playbook_dir = resolve_desk_playbook_dir(universe_dir)
    expected = os.path.join(os.path.dirname(playbook_dir), "referee_obs_cache.db")

    result = resolve_referee_obs_cache_db_path(universe_dir)

    assert result == expected
    assert os.path.basename(result) == "referee_obs_cache.db"
    assert os.path.dirname(result) == os.path.dirname(playbook_dir)
