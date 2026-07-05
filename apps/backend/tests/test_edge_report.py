"""The baseline-edge report (era-3 capability 9 groundwork, J-09) — ``app/research/edge_report.py``
+ ``python -m app.research.edge_report --out <path>``.

Everything is hermetic and keyless: every dataset is either the committed miniature train +
hold-out fixture pair (the SAME fixture ``test_backtests.py`` / ``test_pnl_scan.py`` use) or a
deterministic seeded synthetic stream recorded through the REAL ``DatasetStore`` public path
(never hand-crafted report JSON), and every measurement runs SYNCHRONOUSLY
(``run_edge_report`` calling ``BacktestJobManager.create`` + ``run_sync`` — the EXISTING J-03
computation path, never a second one).

Locked disciplines (each a J-09 acceptance clause), each with its own test below:
  * the champion is read VERBATIM from the persisted pointer, never hardcoded;
  * every displayed net_r/net_usd/n is a byte-for-byte copy of a FRESH, independently-run backtest
    over the identical (dataset, strategy, profile) — pure-render equality, no second computation
    path;
  * train and hold-out are always two separate, never-pooled sections;
  * ranking is deterministic (champion's own net R descending, ``dataset_id`` tie-break);
  * the positive-edge flag is hold-out ONLY, proven both ways (fixture pair -> unflagged +
    honest "no positive-edge dataset"; a controlled synthetic scenario -> exactly one flag);
  * two independent fresh-state runs of an identical scenario are byte-identical;
  * a dataset failing integrity verification, or a backtest ending non-``done``, aborts with an
    explicit ``EdgeReportError`` and NOTHING is written to ``--out``;
  * the module is strictly read-only: no broker/order/account code, and it never calls
    ``set_champion_pointer`` or ``append_validation_row``.
"""

from __future__ import annotations

import dataclasses
import json
import random
import sys
from pathlib import Path

import pytest

from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_V1_ID
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import edge_report
from app.research.backtests import BacktestJobManager, REGISTER, STATUS_DONE
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from app.research.edge_report import EdgeReportError, NO_POSITIVE_EDGE_FINDING, run_edge_report
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's /
# test_pnl_scan.py's own fixture-pair tests use) — the keyless CI substrate.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"


# --- deterministic synthetic substrates (recorded through the REAL store path) -------------------
# The SAME two-phase ramp-then-flat shape test_pnl_scan.py uses: sustained buyer aggression that
# walks the quote up, then a flat continuation at the SAME aggression mix (no further price
# progress). Empirically measured (not merely assumed) via the champion's real backtest below.


def _ramp_then_flat_events(ticker: str, *, ramp_ticks: int, flat_ticks: int, seed: int) -> list:
    rng = random.Random(seed)
    events: list = []
    bid, ask, t = 100.00, 100.02, 0.0
    for _ in range(ramp_ticks):  # sustained buyer aggression, quote walks up
        is_buy = rng.random() >= 0.12
        if is_buy and rng.random() < 0.5:
            bid = round(bid + 0.01, 2)
            ask = round(ask + 0.01, 2)
        events.append(QuoteEvent(ticker, t, bid, ask, 800, 800))
        if is_buy:
            events.append(TradeEvent(ticker, t, ask, rng.choice((100, 200, 300, 600)), Side.UNKNOWN))
        else:
            events.append(TradeEvent(ticker, t, bid, rng.choice((100, 200)), Side.UNKNOWN))
        t += 0.5
    for _ in range(flat_ticks):  # same aggression mix, quote frozen (no more progress)
        is_buy = rng.random() >= 0.12
        events.append(QuoteEvent(ticker, t, bid, ask, 800, 800))
        if is_buy:
            events.append(TradeEvent(ticker, t, ask, rng.choice((100, 200, 300, 600)), Side.UNKNOWN))
        else:
            events.append(TradeEvent(ticker, t, bid, rng.choice((100, 200)), Side.UNKNOWN))
        t += 0.5
    return events


def _record(dstore: DatasetStore, ticker: str, events: list, *, split: str) -> dict:
    return dstore.record(
        symbol=ticker,
        source=f"synthetic {ticker}",
        source_kind="reference",
        source_id=ticker,
        split=split,
        window_start_utc="2026-01-02T14:30:00Z",
        window_end_utc="2026-01-02T15:30:00Z",
        data_feed="sim",
        epoch_anchor=CONFIG.sim_session_anchor_epoch,
        events=events,
    )


def _winning_dataset(dstore: DatasetStore, ticker: str, seed: int, *, split: str) -> dict:
    """A dataset on which the champion's OWN trade is net-positive and beats its null baseline
    decisively — empirically measured: net_r=+0.80, net_usd=+80.00, n=1; null net_r=-13.40,
    null net_usd=-1339.99 (seed=7). Used to prove the positive-edge flag fires (with a test-local
    lowered minimum sample size — the shipped default of 5 is never touched)."""
    return _record(
        dstore, ticker, _ramp_then_flat_events(ticker, ramp_ticks=90, flat_ticks=400, seed=seed), split=split
    )


def _losing_dataset(dstore: DatasetStore, ticker: str, seed: int, *, split: str) -> dict:
    """A dataset with NO sustained price ramp — the champion's trade is net-NEGATIVE: empirically
    measured net_r=-0.15, net_usd=-15.00, n=1 (seed=7). Used as the "does not qualify" control
    beside a winning dataset, in the SAME split, to prove ranking + selective flagging together."""
    return _record(
        dstore, ticker, _ramp_then_flat_events(ticker, ramp_ticks=0, flat_ticks=250, seed=seed), split=split
    )


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


# --- Champion is read verbatim, never hardcoded (IN SCOPE bullet 2) ------------------------------


def test_champion_is_read_verbatim_and_never_hardcoded(store, tmp_path):
    """Move the persisted pointer to the ONE other registered profile (still `v1`, but
    `candidate-faster-warmup`) BEFORE running the report — never via `edge_report.py` (only the
    test calls `set_champion_pointer`, exercising the store's public API directly). The report's
    `champion` field must reflect the MOVED pointer, and every backtest it actually runs must use
    that profile — proof the module reads the pointer, rather than hardcoding `v1`/`default`."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    store.set_champion_pointer(
        strategy_id=STRATEGY_V1_ID, profile=PROFILE_CANDIDATE_FASTER_WARMUP, wall_ts=123.0
    )

    report = run_edge_report(store, dataset_store, CONFIG)

    assert report["champion"] == {
        "strategy_id": STRATEGY_V1_ID,
        "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
    }
    backtests = store.list_backtests(limit=10)
    assert len(backtests) == 2  # one per fixture dataset
    assert all(b.payload["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP for b in backtests)


# --- Empty registry: honest empty report, exit 0 (Key Test Scenario 5) ---------------------------


def test_empty_registry_is_an_honest_empty_report(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")  # never populated

    report = run_edge_report(store, dataset_store, CONFIG)

    assert report["train"]["datasets"] == []
    assert report["holdout"]["datasets"] == []
    assert report["positive_edge_dataset_ids"] == []
    assert report["finding"] == NO_POSITIVE_EDGE_FINDING
    assert report["champion"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


# --- Fixture pair: the non-regression baseline (Key Test Scenario 4) -----------------------------


def test_fixture_pair_yields_no_positive_edge_dataset_with_real_measured_numbers(store):
    """On the committed fixture pair the train dataset's champion trade is net-NEGATIVE (fails
    the sign gate) and the hold-out dataset's champion trade is net-POSITIVE but its n=1 is below
    the configured minimum of 5 AND it fails to beat its own (much larger) null baseline — TWO
    independent reasons it is honestly unflagged despite a positive sign. Numbers are the real,
    empirically-measured champion backtest aggregates (not assumed)."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)

    report = run_edge_report(store, dataset_store, CONFIG)

    assert report["register"] == REGISTER
    assert report["pnl_min_sample_size"] == 5 == CONFIG.pnl_min_sample_size
    (train_row,) = report["train"]["datasets"]
    assert train_row["champion"]["net_r"] == pytest.approx(-0.16000000000001136)
    assert train_row["champion"]["n"] == 1
    assert "positive_edge" not in train_row  # honest omission — never flagged on train

    (holdout_row,) = report["holdout"]["datasets"]
    assert holdout_row["champion"]["net_r"] == pytest.approx(0.3334000000001356)
    assert holdout_row["champion"]["net_usd"] == pytest.approx(33.34000000001356)
    assert holdout_row["champion"]["n"] == 1
    assert holdout_row["null_baseline"]["net_r"] == pytest.approx(5.101632142856395)
    assert 1 < CONFIG.pnl_min_sample_size  # reason 1: n below the configured minimum
    assert holdout_row["champion"]["net_r"] < holdout_row["null_baseline"]["net_r"]  # reason 2: fails beat-null
    assert holdout_row["positive_edge"] is False

    assert report["positive_edge_dataset_ids"] == []
    assert report["finding"] == NO_POSITIVE_EDGE_FINDING
    # Default-frozen cross-check: untouched by this iteration (no new Config field).
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"


# --- Split separation (Key Test Scenario 2) -------------------------------------------------------


def test_split_separation_train_and_holdout_never_pooled(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=7, split=SPLIT_HOLDOUT)

    report = run_edge_report(store, dataset_store, CONFIG)

    assert set(report.keys()) >= {"train", "holdout"}
    assert len(report["train"]["datasets"]) == 1
    assert len(report["holdout"]["datasets"]) == 1
    assert report["train"]["datasets"][0]["dataset_id"] != report["holdout"]["datasets"][0]["dataset_id"]
    # No pooled/merged key exists anywhere in the report.
    assert "combined" not in report and "pooled" not in report and "all" not in report


# --- Ranking + the positive-edge flag, proven both ways (Key Test Scenarios 3 & 6) ---------------


def test_ranking_is_descending_by_net_r_and_exactly_one_holdout_dataset_is_flagged(store, tmp_path):
    """Two hold-out datasets: a winner (net_r=+0.80, beats its very negative null) and a loser
    (net_r=-0.15). With a test-LOCAL lowered minimum sample size (`dataclasses.replace` — the
    shipped default of 5 is never touched), the winner clears every gate and the loser fails the
    sign gate alone — exactly one flag, and the ranking puts the winner first."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-WIN-A", seed=7, split=SPLIT_HOLDOUT)
    _losing_dataset(dataset_store, "SYN-FLAT-B", seed=7, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, pnl_min_sample_size=1)

    report = run_edge_report(store, dataset_store, test_config)

    rows = report["holdout"]["datasets"]
    assert [r["champion"]["net_r"] > 0 for r in rows] == [True, False]  # winner ranked first
    assert rows[0]["champion"]["net_r"] == pytest.approx(0.8000000000001677)
    assert rows[1]["champion"]["net_r"] == pytest.approx(-0.1499999999999389)
    assert rows[0]["positive_edge"] is True
    assert rows[1]["positive_edge"] is False
    assert len(report["positive_edge_dataset_ids"]) == 1
    assert report["positive_edge_dataset_ids"] == [rows[0]["dataset_id"]]
    assert report["finding"] == f"positive-edge dataset(s): {rows[0]['dataset_id']}"
    # The shipped default minimum is untouched by this test-local override.
    assert CONFIG.pnl_min_sample_size == 5


def test_n_gate_alone_keeps_a_qualifying_dataset_unflagged_below_minimum(store, tmp_path):
    """SYN-WIN-A at the SHIPPED DEFAULT minimum (5, untouched): champion net_r=+0.80,
    net_usd=+80.00 (both positive) and decisively beats its very negative null baseline — but
    n=1 is below the configured minimum of 5, which is the ONLY reason it stays unflagged.
    Isolates the sample-size gate from the sign and beats-null gates (both exercised elsewhere:
    a mutation that dropped this check alone would not be caught by any other test)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-WIN-A", seed=7, split=SPLIT_HOLDOUT)

    report = run_edge_report(store, dataset_store, CONFIG)  # shipped default min=5, untouched

    (row,) = report["holdout"]["datasets"]
    assert row["champion"]["net_r"] > 0
    assert row["champion"]["net_r"] > row["null_baseline"]["net_r"]  # beats null
    assert row["champion"]["n"] == 1
    assert row["champion"]["n"] < CONFIG.pnl_min_sample_size  # fails ONLY the n-gate
    assert row["positive_edge"] is False
    assert report["finding"] == NO_POSITIVE_EDGE_FINDING


def test_beats_null_gate_alone_keeps_a_net_positive_dataset_unflagged(store):
    """The committed fixture hold-out dataset, with a test-LOCAL lowered minimum (n=1 clears it —
    the shipped default of 5 is never touched): champion net_r=+0.3334 is net-positive and its
    n now clears the (lowered) minimum, but it fails to beat its own LARGER null baseline
    (null net_r=+5.10 > champion's +0.33) — the ONLY remaining reason it stays unflagged.
    Isolates the beats-null gate from the sign and sample-size gates (both exercised elsewhere:
    a mutation that dropped this check alone would not be caught by any other test)."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    test_config = dataclasses.replace(CONFIG, pnl_min_sample_size=1)

    report = run_edge_report(store, dataset_store, test_config)

    (holdout_row,) = report["holdout"]["datasets"]
    assert holdout_row["champion"]["net_r"] > 0
    assert holdout_row["champion"]["n"] >= 1  # clears the (lowered) minimum
    assert holdout_row["champion"]["net_r"] < holdout_row["null_baseline"]["net_r"]  # fails beat-null
    assert holdout_row["positive_edge"] is False
    assert report["finding"] == NO_POSITIVE_EDGE_FINDING
    # The shipped default minimum is untouched by this test-local override.
    assert CONFIG.pnl_min_sample_size == 5


def test_rank_orders_by_net_r_descending_with_dataset_id_tiebreak():
    """A pure-function proof of the tie-break rule itself (dataset_id ascending on an exact net_r
    tie) — a genuine float tie is impractical to engineer through a real backtest, so this checks
    the deterministic JSON-shaping/sorting logic directly with representative measurement rows
    (no tape/PnL data is fabricated here — only the sort order of already-computed numbers)."""
    rows = [
        {"dataset_id": "b", "champion": {"net_r": 1.0, "net_usd": 100.0, "n": 5}},
        {"dataset_id": "a", "champion": {"net_r": 1.0, "net_usd": 100.0, "n": 5}},
        {"dataset_id": "c", "champion": {"net_r": 2.0, "net_usd": 50.0, "n": 5}},
    ]
    ranked = edge_report._rank(rows)
    assert [r["dataset_id"] for r in ranked] == ["c", "a", "b"]


# --- Pure-render equality: no second computation path (Key Test Scenario 1) ----------------------


def test_every_displayed_value_matches_a_fresh_independent_backtest(store):
    """Every displayed net_r/net_usd/n is byte-for-byte identical to a FRESH, independently-run
    backtest over the SAME (dataset, strategy, profile) — proof there is no second computation
    path (the backtest engine is fully deterministic given the same inputs and the config-owned
    null-baseline seed, so re-running it independently must reproduce the report's numbers
    exactly)."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    report = run_edge_report(store, dataset_store, CONFIG)
    champion = report["champion"]

    verify_jobs = BacktestJobManager(store, CONFIG)
    for row in report["train"]["datasets"] + report["holdout"]["datasets"]:
        payload = verify_jobs.create(
            {
                "dataset_id": row["dataset_id"],
                "strategy_id": champion["strategy_id"],
                "profile": champion["profile"],
            }
        )
        verify_jobs.run_sync(payload["id"], dataset_store=dataset_store)
        fresh = store.get_backtest(payload["id"]).payload
        assert fresh["status"] == STATUS_DONE
        fresh_agg = fresh["result"]["aggregates"]
        assert row["champion"]["net_r"] == fresh_agg["net_r"]
        assert row["champion"]["net_usd"] == fresh_agg["net_usd"]
        assert row["champion"]["n"] == fresh_agg["n"]
        fresh_null = fresh["result"]["null_baseline"]["aggregates"]
        assert row["null_baseline"]["net_r"] == fresh_null["net_r"]
        assert row["null_baseline"]["net_usd"] == fresh_null["net_usd"]
        assert row["null_baseline"]["n"] == fresh_null["n"]


# --- Determinism (Key Test Scenario 7) -------------------------------------------------------------


def test_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_path, monkeypatch):
    """Two INDEPENDENT fresh-state runs (fresh journal DB each) of the identical fixture-pair
    scenario, driven through the REAL CLI entry point end to end, produce byte-identical ``--out``
    file contents — no wall-clock or per-run-random field is ever collected into the report."""
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))

    def _run_once(label: str) -> bytes:
        monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / f"journal-{label}.db"))
        out_path = tmp_path / f"edge-report-{label}.json"
        monkeypatch.setattr(sys, "argv", ["edge_report", "--out", str(out_path)])
        exit_code = edge_report.main()
        assert exit_code == 0
        return out_path.read_bytes()

    first = _run_once("a")
    second = _run_once("b")
    assert first == second
    assert len(first) > 200  # a sanity floor: not an accidentally-empty report


# --- Honest failure states (Key Test Scenario 11) --------------------------------------------------


def test_corrupt_dataset_raises_explicit_error_with_nothing_computed(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    with pytest.raises(EdgeReportError):
        run_edge_report(store, dataset_store, CONFIG)
    # No backtest rows persisted before the abort — the sweep never started (the integrity check
    # is the very first thing run_edge_report does).
    assert store.list_backtests(limit=10) == []


def test_cli_writes_nothing_and_exits_1_on_corrupt_dataset(tmp_path, monkeypatch):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    out_path = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", ["edge_report", "--out", str(out_path)])

    exit_code = edge_report.main()

    assert exit_code == 1
    assert not out_path.exists()


def test_run_backtest_raises_explicit_error_when_status_is_not_done(tmp_path):
    """A backtest ending anything other than `done` aborts explicitly. Forced via the REAL
    cooperative-cancellation mechanism (`BacktestJobManager.cancel` set BEFORE `run_sync` observes
    it) — a genuine non-`done` outcome, never a hand-crafted fake payload."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _winning_dataset(dataset_store, "SYN-CANCEL-ME", seed=7, split=SPLIT_HOLDOUT)
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    try:
        jobs = BacktestJobManager(store, CONFIG)
        real_run_sync = jobs.run_sync

        def _cancel_before_running(backtest_id, *, dataset_store):
            jobs.cancel(backtest_id)  # sets the cooperative-cancellation flag BEFORE the real run
            real_run_sync(backtest_id, dataset_store=dataset_store)

        jobs.run_sync = _cancel_before_running

        with pytest.raises(EdgeReportError, match="ended 'cancelled'"):
            edge_report._run_backtest(
                jobs, store, dataset_store, meta["id"],
                strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT,
            )
    finally:
        store.close()


# --- No-execution / no-promotion guard (Key Test Scenario 10) -------------------------------------


def test_edge_report_source_calls_no_promotion_api():
    """The edge report promotes/appends NOTHING (that is what makes "no train-only promotion"
    satisfied by construction): its source never calls the champion-pointer setter or the
    ledger's single writer. The broader "no broker/order/account/execution pattern anywhere"
    clause is already enforced repo-wide by ``test_no_execution_path.py`` (its
    ``test_scan_is_not_vacuous`` now explicitly asserts ``edge_report.py`` is within its scanned
    file set) — deliberately NOT duplicated here, since restating those literal pattern strings
    as this test's own "forbidden" data would itself trip that same repo-wide scanner (the exact
    reason it already self-allowlists its own file and ``test_real_data_gate.py``)."""
    text = (BACKEND_DIR / "app" / "research" / "edge_report.py").read_text()
    assert ".set_champion_pointer(" not in text
    assert "append_validation_row(" not in text


# --- The CLI entry point itself ---------------------------------------------------------------


def test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))
    out_path = tmp_path / "edge-report.json"
    monkeypatch.setattr(sys, "argv", ["edge_report", "--out", str(out_path)])

    exit_code = edge_report.main()

    assert exit_code == 0
    payload = json.loads(out_path.read_text())
    assert payload["finding"] == NO_POSITIVE_EDGE_FINDING
    assert payload["champion"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert len(payload["train"]["datasets"]) == 1
    assert len(payload["holdout"]["datasets"]) == 1
