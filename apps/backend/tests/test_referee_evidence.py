"""``referee_evidence.py`` + ``GET /research/desk/referee/evidence`` (Era 6 "The Referee", J-01) —
the readiness fold. Test-first contract: TC-1 through TC-5 in
``docs/phases/goal-referee-iter-1.md``.

Builds its own hand-crafted ``PlaybookStore``/``DatasetStore``/``JournalStore`` records directly
through each store's own public write path (never a real ``compute_playbook`` walk or a real
backtest run — those paths are already covered end to end by ``test_desk_playbook.py``/
``test_backtests.py``), so every pooled count in every assertion below is a number this file's own
hand computation can reproduce, not one a compute happened to produce."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.base import Side, TradeEvent
from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
from app.research.desk_routes import get_playbook_store
from app.research.referee_evidence import (
    REFEREE_FORMING_BAR_BASIS_CAVEAT,
    REFEREE_TICK_GATE_SYMBOL_DAYS,
    _tick_gate_state,
    current_playbook_detector_basis,
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
