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

from app.config import (
    CONFIG,
    PROFILE_CANDIDATE_FASTER_WARMUP,
    PROFILE_DEFAULT,
    STRATEGY_TAPE_ID,
    STRATEGY_TAPE_MAP_ID,
    STRATEGY_V1_ID,
)
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import edge_report
from app.research.backtests import BacktestJobManager, REGISTER, STATUS_DONE
from app.research.bars import BarStore
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from app.research.edge_report import (
    EdgeReportError,
    NO_POSITIVE_EDGE_FINDING,
    run_edge_report,
    run_strategy_comparison_report,
)
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's /
# test_pnl_scan.py's own fixture-pair tests use) — the keyless CI substrate.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"
# The committed J-03 event-window fixture (symbol PG -- NOT a config-owned panel symbol, so it
# never resolves an owning compute_setups event under the REAL registered panel; see
# test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report below).
FIXTURE_J03_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"


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

        def _cancel_before_running(backtest_id, *, dataset_store, bar_store=None):
            jobs.cancel(backtest_id)  # sets the cooperative-cancellation flag BEFORE the real run
            real_run_sync(backtest_id, dataset_store=dataset_store, bar_store=bar_store)

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


# ==================================================================================================
# The 3-way strategy-comparison report (era-5B capability 6, J-04) — ``run_strategy_comparison_
# report``. ``run_edge_report``/``main``/every fixture and test above this marker are UNTOUCHED —
# the era-3 champion-only CLI stays byte-identical (proven by the whole suite above still passing).
# ==================================================================================================

from test_backtests import _sim_events  # noqa: E402
from test_setups import SYM_A, _seed_full, _syn_config  # noqa: E402


def _record_windowed(
    dstore: DatasetStore, events: list, *, symbol: str, scenario: str, anchor: float,
    split: str, feed: str, window_start: str, window_end: str,
) -> dict:
    """The IDENTICAL ``DatasetStore.record`` public path ``test_backtests._record`` /
    ``test_edge_report._record`` already use, with EVERY provenance field (split/feed/window)
    caller-controlled — the ONLY thing those two existing helpers hard-code that this section's
    tests genuinely need to vary (a recorded window must CONTAIN a specific known scan event's
    ``touch_ts``; a feed must genuinely differ to prove the no-pooling guard)."""
    return dstore.record(
        symbol=symbol, source=scenario, source_kind="reference", source_id=symbol,
        split=split, window_start_utc=window_start, window_end_utc=window_end,
        data_feed=feed, epoch_anchor=anchor, events=events,
    )


# The SAME synthetic multi-timeframe/multi-session scan fixture ``test_setups.py`` already proves
# exhaustively (touch detection, reaction classification, forward returns) — reused VERBATIM here
# (never a second copy) purely as the KNOWN, pinned SOURCE of classified touch events this report
# joins recorded datasets against. Verified by direct computation (not hand-derived): scanning
# ``_seed_full`` under ``_syn_config()`` emits exactly one clean, SINGLE-event session with a
# classified band -- 2026-01-05 (SYM_A, resistance, class C, band [250.10, 250.20], reaction
# "broke", touch_ts "2026-01-05T00:00:00.000000Z") -- so every dataset window below is sized to
# contain THAT one touch_ts, keeping every scenario a clean, single, known cell.
_SCAN_WINDOW = {"window_start": "2026-01-04T23:00:00Z", "window_end": "2026-01-05T01:00:00Z"}


@pytest.fixture
def scan_bar_store(tmp_path):
    store = BarStore(tmp_path / "scan-bars")
    _seed_full(store)
    return store


@pytest.fixture
def scan_config():
    return _syn_config()


def _record_v1_arming_dataset(
    dstore: DatasetStore, *, max_logical: float, split: str, feed: str, label: str
) -> dict:
    """One dataset recorded from a truncated SIM-BUYER stream (the EXISTING ``_sim_events`` fixture
    reused verbatim): arms exactly one deterministic v1 trend_continuation-long trade (entry
    24.5s@100.24, horizon exit 144.5s@101.28 -- the SAME pinned shape ``test_backtests.py``'s own
    ``test_sim_buyer_arms_one_trend_continuation_long_with_horizon_exit`` proves), so its net_r/
    net_usd are IDENTICAL across every recording (only the truncation length -- hence the file
    checksum -- differs, avoiding ``DatasetAlreadyRegistered`` while keeping pooled sums exact and
    predictable: n datasets pool to net_r == n * 5.050000000001056)."""
    events, provider = _sim_events("SIM-BUYER", max_logical)
    return _record_windowed(
        dstore, events, symbol=SYM_A, scenario=f"edge-report-{label}", anchor=provider.epoch_anchor,
        split=split, feed=feed, **_SCAN_WINDOW,
    )


# --- The keyless committed-fixture run (Key Test Scenario: exact cell shape) ---------------------


def test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report(tmp_path, store):
    """The literal DoD scenario: ``run_strategy_comparison_report`` over the COMMITTED
    ``datasets_j03/`` fixture (symbol PG) under the REAL, shipped ``CONFIG`` (the config-owned
    12-symbol panel, which does NOT include PG). PG can never resolve an owning scan event under
    the real panel, so every cell is honestly absent — the degenerate, valid case of "all cells
    insufficient_sample" (vacuously: there are none to violate the gate). An empty ``BarStore`` is
    sufficient (and proves ``compute_setups`` never needs PG's own bars to reach this honest
    empty state — the panel-symbol filter excludes it before any bar read)."""
    dataset_store = DatasetStore(FIXTURE_J03_DATASET_DIR)
    bar_store = BarStore(tmp_path / "empty-bars")

    report = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)

    assert report["register"] == REGISTER
    assert report["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
    assert report["train"]["cells"] == []
    assert report["holdout"]["cells"] == []
    assert report["surviving_train_cells"] == []
    assert "champion" not in report  # this report is never about a single champion pointer


def test_empty_registry_3way_report_is_honest_and_empty(tmp_path, store):
    dataset_store = DatasetStore(tmp_path / "datasets")  # never populated
    bar_store = BarStore(tmp_path / "empty-bars")

    report = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)

    assert report["train"]["cells"] == []
    assert report["holdout"]["cells"] == []
    assert report["surviving_train_cells"] == []


# --- Real join + real cells over a synthetic scan (Key Test Scenario: exact cell structure) -------


def test_synthetic_scan_join_produces_real_cells_all_insufficient_sample(
    tmp_path, store, scan_bar_store, scan_config
):
    """ONE recorded dataset, windowed around the KNOWN 2026-01-05 class-C/broke/resistance scan
    event, produces exactly THREE cells (v1 / structure_tape / structure_tape_map) — the exact
    strategy x class x side x reaction shape the DoD names. v1 arms its one deterministic
    trend_continuation trade (this fixture's bars are unrelated to structure_tape/
    structure_tape_map's OWN arming source, so both honestly arm zero — never fabricated). Every
    cell is ``insufficient_sample`` at n=1/n=0, below the shipped default minimum of 5 — the
    literal "keyless run is expected all-insufficient_sample" DoD phrasing, realized here with a
    genuinely non-empty, real cell set (not the vacuous empty case above)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")

    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)

    cells = report["train"]["cells"]
    assert {c["strategy_id"] for c in cells} == {STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID}
    for cell in cells:
        assert cell["band_class"] == "C"
        assert cell["band_side"] == "resistance"
        assert cell["reaction"] == "broke"
        assert cell["feed"] == "sim"
        assert cell["dataset_ids"] == [meta["id"]]
        assert cell["insufficient_sample"] is True  # every n below the shipped minimum of 5

    v1_cell = next(c for c in cells if c["strategy_id"] == STRATEGY_V1_ID)
    assert v1_cell["measurement"]["n"] == 1
    assert v1_cell["measurement"]["net_r"] == pytest.approx(5.050000000001056)
    assert v1_cell["measurement"]["win_rate"] == 1.0
    for other_id in (STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID):
        other_cell = next(c for c in cells if c["strategy_id"] == other_id)
        assert other_cell["measurement"] == {
            "n": 0, "gross_r": 0.0, "net_r": 0.0, "gross_usd": 0.0, "net_usd": 0.0,
            "win_rate": None, "max_drawdown_r": None,
        }
    assert report["holdout"]["cells"] == []
    assert report["surviving_train_cells"] == []  # n=1 fails the n>=5 gate on every cell
    assert "champion" not in report


def test_every_cell_carries_the_full_register_and_a_null_baseline(tmp_path, store, scan_bar_store, scan_config):
    _record_v1_arming_dataset(
        DatasetStore(tmp_path / "datasets"), max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a"
    )
    dataset_store = DatasetStore(tmp_path / "datasets")

    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)

    assert report["register"] == REGISTER == "simulated — assumed fees/slippage — not indicative of live results"
    for cell in report["train"]["cells"]:
        for key in ("n", "gross_r", "net_r", "gross_usd", "net_usd", "win_rate", "max_drawdown_r"):
            assert key in cell["measurement"]
            assert key in cell["null_baseline"]
        assert cell["null_baseline"]["n"] == CONFIG.backtest_null_entry_count


# --- No feed pooling (a two-feed input never merges into one cell) -------------------------------


def test_two_same_feed_datasets_pool_and_a_different_feed_never_pools(
    tmp_path, store, scan_bar_store, scan_config
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta_a = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    meta_b = _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
    meta_c = _record_v1_arming_dataset(dataset_store, max_logical=175.0, split=SPLIT_TRAIN, feed="iex", label="c")

    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)

    v1_cells = [c for c in report["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID]
    assert len(v1_cells) == 2  # sim and iex NEVER merge into one cell
    by_feed = {c["feed"]: c for c in v1_cells}
    assert set(by_feed) == {"sim", "iex"}

    sim_cell = by_feed["sim"]
    assert sim_cell["dataset_ids"] == sorted([meta_a["id"], meta_b["id"]])
    assert sim_cell["measurement"]["n"] == 2
    assert sim_cell["measurement"]["net_r"] == pytest.approx(2 * 5.050000000001056)
    assert sim_cell["measurement"]["win_rate"] == 1.0  # both pooled trades are winners

    iex_cell = by_feed["iex"]
    assert iex_cell["dataset_ids"] == [meta_c["id"]]
    assert iex_cell["measurement"]["n"] == 1
    assert iex_cell["measurement"]["net_r"] == pytest.approx(5.050000000001056)

    # No pooled/merged/combined key exists anywhere in the report (the run_edge_report precedent).
    text = json.dumps(report)
    for forbidden_key in ('"combined"', '"pooled"', '"all_feeds"'):
        assert forbidden_key not in text


# --- Train and hold-out stay in separate sections, never pooled (Key Test Scenario) ---------------


def test_train_and_holdout_cells_stay_separate_never_pooled(tmp_path, store, scan_bar_store, scan_config):
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _record_v1_arming_dataset(
        dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="train"
    )
    holdout_meta = _record_v1_arming_dataset(
        dataset_store, max_logical=225.0, split=SPLIT_HOLDOUT, feed="sim", label="holdout"
    )

    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)

    train_v1 = next(c for c in report["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
    holdout_v1 = next(c for c in report["holdout"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
    assert train_v1["dataset_ids"] == [train_meta["id"]]
    assert holdout_v1["dataset_ids"] == [holdout_meta["id"]]
    assert train_v1["measurement"]["n"] == 1
    assert holdout_v1["measurement"]["n"] == 1  # NEVER 2 -- the two splits never pool together
    assert set(report.keys()) >= {"train", "holdout"}
    assert "cells" not in report  # no top-level pooled cell list outside the two sections


# --- The champion pointer is never read, moved, or promoted (no-hand-promotion guard) -------------


def test_champion_pointer_unchanged_after_a_3way_report_run(tmp_path, store, scan_bar_store, scan_config):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    before = store.get_champion_pointer()

    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)

    assert store.get_champion_pointer() == before == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


# --- Hot-path guard: compute_setups runs at most ONCE per report call (audit B2 carry-item) --------


def test_compute_setups_runs_at_most_once_per_report_call(tmp_path, store, scan_bar_store, scan_config, monkeypatch):
    calls = []
    real_compute_setups = edge_report.compute_setups

    def _counting_compute_setups(*args, **kwargs):
        calls.append(1)
        return real_compute_setups(*args, **kwargs)

    monkeypatch.setattr(edge_report, "compute_setups", _counting_compute_setups)

    # Empty registry: never even worth a full panel scan.
    run_strategy_comparison_report(store, DatasetStore(tmp_path / "empty-datasets"), scan_bar_store, scan_config)
    assert len(calls) == 0

    # Non-empty registry: exactly ONE call for the WHOLE report (never once per dataset, never
    # once per split — train + holdout share the SAME scan).
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    _record_v1_arming_dataset(dataset_store, max_logical=225.0, split=SPLIT_HOLDOUT, feed="sim", label="b")
    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
    assert len(calls) == 1


# --- Determinism: two independent runs of the identical scenario are byte-identical ---------------


def test_3way_report_determinism_two_independent_runs_are_byte_identical(
    tmp_path, scan_bar_store, scan_config
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")

    store_a = JournalStore(str(tmp_path / "journal-a.db"), scan_config)
    store_b = JournalStore(str(tmp_path / "journal-b.db"), scan_config)
    try:
        first = run_strategy_comparison_report(store_a, dataset_store, scan_bar_store, scan_config)
        second = run_strategy_comparison_report(store_b, dataset_store, scan_bar_store, scan_config)
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    finally:
        store_a.close()
        store_b.close()


# --- Gate-integrity: the ranking/surviving-cell logic itself (a pure-function proof, the
# ``test_rank_orders_by_net_r_descending_with_dataset_id_tiebreak`` precedent -- representative
# already-computed measurement rows, never a fabricated backtest) --------------------------------


def _cell(strategy_id, band_class, reaction, *, n, net_r, net_usd, null_net_r, null_net_usd, feed="sim"):
    return {
        "strategy_id": strategy_id,
        "band_class": band_class,
        "band_side": "resistance",
        "reaction": reaction,
        "feed": feed,
        "dataset_ids": ["x"],
        "measurement": {
            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
            "win_rate": 1.0 if n else None, "max_drawdown_r": 0.0 if n else None,
        },
        "null_baseline": {
            "n": 100, "gross_r": null_net_r, "net_r": null_net_r, "gross_usd": null_net_usd,
            "net_usd": null_net_usd, "win_rate": 0.4, "max_drawdown_r": 1.0,
        },
        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
    }


def test_surviving_train_cells_clears_every_gate_and_carries_holdout_status():
    clearing = _cell("v1", "A", "broke", n=5, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)
    below_minimum_n = _cell("v1", "B", "broke", n=2, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)
    fails_beat_null = _cell("v1", "C", "broke", n=5, net_r=0.5, net_usd=50.0, null_net_r=1.0, null_net_usd=100.0)
    negative_net_r = _cell("v1", "A", "chopped", n=5, net_r=-1.0, net_usd=-100.0, null_net_r=-2.0, null_net_usd=-200.0)
    train_cells = [clearing, below_minimum_n, fails_beat_null, negative_net_r]

    matching_holdout = _cell("v1", "A", "broke", n=5, net_r=3.0, net_usd=300.0, null_net_r=0.5, null_net_usd=50.0)
    holdout_cells = [matching_holdout]

    survivors = edge_report._surviving_train_cells(train_cells, holdout_cells, CONFIG)

    assert len(survivors) == 1
    assert survivors[0]["train_cell"] == clearing
    assert survivors[0]["holdout_cell"] == matching_holdout
    assert survivors[0]["holdout_positive_edge"] is True


def test_surviving_train_cells_honest_absence_when_no_holdout_data_exists_yet():
    clearing = _cell("v1", "A", "broke", n=5, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)

    survivors = edge_report._surviving_train_cells([clearing], [], CONFIG)

    assert len(survivors) == 1
    assert survivors[0]["holdout_cell"] is None
    assert survivors[0]["holdout_positive_edge"] is False  # never fabricated True on absent data


def test_surviving_train_cells_ranks_by_net_r_descending_with_deterministic_tiebreak():
    lower = _cell("v1", "A", "broke", n=5, net_r=2.0, net_usd=200.0, null_net_r=0.1, null_net_usd=10.0)
    higher = _cell("structure_tape", "A", "broke", n=5, net_r=3.0, net_usd=300.0, null_net_r=0.1, null_net_usd=10.0)

    survivors = edge_report._surviving_train_cells([lower, higher], [], CONFIG)

    assert [s["train_cell"]["strategy_id"] for s in survivors] == ["structure_tape", "v1"]


# --- Coherence: this section reuses the ONE BacktestJobManager path, never a second computation ---


def test_3way_report_source_reuses_the_shared_aggregate_and_never_a_second_edge_formula():
    src = (BACKEND_DIR / "app" / "research" / "edge_report.py").read_text()
    assert "from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate" in src
    assert "def run_strategy_comparison_report(" in src
    # No second R/$/win-rate/drawdown formula anywhere in the new section.
    for forbidden in ("sum(t[", "win_rate =", "max_dd", "cum +="):
        assert forbidden not in src, f"a second aggregate formula leaked into edge_report.py: {forbidden}"


# ==================================================================================================
# The rebuildable result cache (era-5B J-08) — ``run_strategy_comparison_report``'s optional
# ``cache=`` param, wired to ``edge_report_cache.EdgeReportCache``. Every test ABOVE this marker
# calls ``run_strategy_comparison_report`` WITHOUT a cache (``cache=None``, the default) and stays
# green UNMODIFIED — proof by construction that the pre-J-08 uncached path is byte-for-byte
# untouched. ``EdgeReportCache``'s OWN mechanics (keying, durability, concurrency, torn-read
# safety) are unit-tested in isolation in ``tests/test_edge_report_cache.py`` against a cheap
# counting stub; this section proves the WIRING into the real ``_compute_strategy_comparison_
# report`` — byte-identity against a real, non-degenerate report shape (the iter-4 lesson: never
# merely the vacuous ``cells: []`` case) and that a warmed cache genuinely skips recomputation.
# ==================================================================================================

from app.research.edge_report_cache import EdgeReportCache  # noqa: E402
from app.research.edge_report_backtest_cache import EdgeReportBacktestCache  # noqa: E402


def test_cache_none_default_is_byte_identical_to_the_pre_j08_uncached_call(
    tmp_path, store, scan_bar_store, scan_config
):
    """The literal DoD default: omitting ``cache=`` recomputes directly, exactly as every OTHER
    test in this file already proves implicitly by staying green unmodified — this test makes the
    claim explicit and non-degenerate (the real 3-cell synthetic-scan-join shape, not ``[]``)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")

    without_kwarg = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
    with_explicit_none = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=None
    )

    assert json.dumps(without_kwarg, sort_keys=True) == json.dumps(with_explicit_none, sort_keys=True)
    assert len(without_kwarg["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape


def test_warm_cache_report_is_byte_identical_to_a_fresh_cache_cleared_compute(
    tmp_path, store, scan_bar_store, scan_config
):
    """era-5B J-08 determinism (DoD-mandated; the iter-4 lesson: proven on a NON-degenerate report
    shape — the real synthetic scan-join fixture, never merely the vacuous empty case). A warm
    cache's served report is byte-identical to an INDEPENDENT fresh, uncached compute — the cache
    changes nothing about WHAT is returned, only whether it is recomputed."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    warm = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
    fresh = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)  # cache=None

    assert json.dumps(warm, sort_keys=True) == json.dumps(fresh, sort_keys=True)
    assert len(warm["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape, not []


def test_second_call_on_a_warmed_cache_never_recomputes(tmp_path, store, scan_bar_store, scan_config, monkeypatch):
    """The whole point of J-08: a SECOND call against an identical, already-warmed cache must never
    re-enter ``_compute_strategy_comparison_report`` at all (the ``test_compute_setups_runs_at_
    most_once_per_report_call`` counting-wrapper pattern, applied to the NEW cache-aware entry
    point)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    calls = []
    real_compute = edge_report._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)

    first = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
    second = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert len(calls) == 1  # the SECOND call served entirely from the cache
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_a_new_recorded_dataset_busts_the_wired_cache(tmp_path, store, scan_bar_store, scan_config):
    """Adding a NEW registered dataset changes the checksum set the cache is keyed on, so the very
    next call must recompute and reflect the new dataset — never serve the stale pre-addition
    report."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta_a = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    first = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
    first_v1_cell = next(c for c in first["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
    assert first_v1_cell["dataset_ids"] == [meta_a["id"]]

    meta_b = _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
    second = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
    second_v1_cell = next(c for c in second["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)

    assert second_v1_cell["dataset_ids"] == sorted([meta_a["id"], meta_b["id"]])
    assert second_v1_cell["measurement"]["n"] == 2  # both datasets pooled into the recomputed cell


def test_durability_across_a_simulated_backend_restart_via_the_wired_function(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """The DoD's literal restart scenario, exercised through the REAL public entry point (not just
    ``EdgeReportCache`` in isolation): a BRAND NEW ``EdgeReportCache`` at the SAME persisted path
    (simulating a backend restart) serves the prior warm report WITHOUT ever calling
    ``_compute_strategy_comparison_report`` again."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    db_path = str(tmp_path / "cache.db")

    original_cache = EdgeReportCache(db_path)
    warm = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=original_cache
    )

    restarted_cache = EdgeReportCache(db_path)  # no in-process state carried over
    calls = []
    real_compute = edge_report._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)

    served = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=restarted_cache
    )

    assert len(calls) == 0  # never recomputed post-"restart" — served from the durable row alone
    assert json.dumps(served, sort_keys=True) == json.dumps(warm, sort_keys=True)


def test_cached_report_never_moves_the_champion_pointer(tmp_path, store, scan_bar_store, scan_config):
    """The no-hand-promotion guard, re-proven through the cached path specifically: a cache is an
    accelerator over a strictly read-only report, never a new surface that could promote."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    before = store.get_champion_pointer()

    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)
    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)  # warm hit too

    assert store.get_champion_pointer() == before == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


def test_cache_wiring_source_never_duplicates_the_computation():
    """A coherence guard: the cache-aware ``run_strategy_comparison_report`` is a thin dispatcher —
    it calls ``_compute_strategy_comparison_report`` (directly or via ``cache.get_or_compute``) and
    nothing else computes a cell."""
    src = (BACKEND_DIR / "app" / "research" / "edge_report.py").read_text()
    assert "def _compute_strategy_comparison_report(" in src
    assert "cache.get_or_compute(dataset_store, config, compute)" in src
    # Exactly ONE definition of each — never a second copy under a different name.
    assert src.count("def run_strategy_comparison_report(") == 1
    assert src.count("def _compute_strategy_comparison_report(") == 1


# ==================================================================================================
# The honest not-computed peek (era-fast_wall J-01) — ``peek_strategy_comparison_report``, the
# GET-path's EXCLUSIVE entry point from this iteration on (``routes.get_edge_report`` calls ONLY
# this, never ``run_strategy_comparison_report`` — see ``routes.py``). Proves the three branches
# named in the function's own docstring: a cold key on a non-empty registry returns the honest
# not-computed payload and NEVER calls the compute path; a warm key (published via
# ``EdgeReportCache.compute_and_publish`` — the future operator/CLI path, J-04) returns THAT exact
# result verbatim; an empty registry keeps the pre-J-01 O(1) full-report shape untouched.
# ==================================================================================================

from app.research.edge_report import peek_strategy_comparison_report  # noqa: E402


def test_peek_on_a_cold_key_returns_the_not_computed_payload_and_never_computes(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    calls = []
    real_compute = edge_report._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)

    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert calls == []  # a cold GET-path call NEVER computes -- the whole point of J-01
    assert result["status"] == "not_computed"
    assert isinstance(result["detail"], str) and result["detail"] != ""
    assert result["dataset_count"] == 1
    assert result["register"] == REGISTER
    assert result["compute"] is None


def test_peek_on_a_warm_key_returns_the_published_result_verbatim(
    tmp_path, store, scan_bar_store, scan_config
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    published = cache.compute_and_publish(
        dataset_store, scan_config,
        lambda: edge_report._compute_strategy_comparison_report(
            store, dataset_store, scan_bar_store, scan_config
        ),
    )

    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert json.dumps(result, sort_keys=True) == json.dumps(published, sort_keys=True)
    assert "status" not in result
    assert len(result["train"]["cells"]) == 3  # non-degenerate, the real 3-cell shape


def test_peek_on_an_empty_registry_keeps_the_pre_j01_full_report_shape(tmp_path, store):
    dataset_store = DatasetStore(tmp_path / "datasets")  # never populated
    bar_store = BarStore(tmp_path / "empty-bars")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    result = peek_strategy_comparison_report(store, dataset_store, bar_store, CONFIG, cache=cache)

    assert "status" not in result
    assert result["train"]["cells"] == []
    assert result["holdout"]["cells"] == []
    assert result["surviving_train_cells"] == []


def test_peek_raises_on_a_dataset_integrity_error_before_ever_touching_the_cache(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    def _boom(*args, **kwargs):
        raise AssertionError("cache.lookup must never be called on an integrity-error path")

    monkeypatch.setattr(cache, "lookup", _boom)

    with pytest.raises(EdgeReportError, match="integrity"):
        peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)


def test_peek_source_never_calls_a_compute_triggering_cache_method():
    """A coherence guard, mechanically pinning the GET-path's central promise: ``peek_strategy_
    comparison_report``'s OWN source never calls a cache method that could compute and persist a
    fresh report (``cache.get_or_compute``/``cache.compute_and_publish``) — only the read-only
    ``cache.lookup``. The one legitimate direct call to ``_compute_strategy_comparison_report`` is
    the documented empty-registry O(1) branch (see the function's own docstring), not a cache
    method at all."""
    import inspect

    src = inspect.getsource(edge_report.peek_strategy_comparison_report)
    assert "cache.lookup(" in src
    for forbidden in ("cache.get_or_compute(", "cache.compute_and_publish("):
        assert forbidden not in src


# ==================================================================================================
# era-fast_wall J-04 — the operator-run compute's five additive keyword-only hooks on
# ``run_strategy_comparison_report`` (``force``/``progress``/``should_abort``/``sub_cache``/
# ``workers``). Every test ABOVE this marker calls the function with every new kwarg left at its
# default and stays green UNMODIFIED — proof by construction that the unused-default path is
# byte-for-byte untouched (TC-14a's "default path" leg). This section proves the hooks are
# genuinely wired, not decorative (TC-14), and ``peek_strategy_comparison_report``'s new
# ``compute=`` passthrough.
# ==================================================================================================

from app.research.edge_report import EdgeReportComputeCancelled  # noqa: E402


def test_progress_and_should_abort_supplied_but_unused_is_byte_identical_to_the_default_path(
    tmp_path, store, scan_bar_store, scan_config
):
    """TC-14a: the hooked path (every new kwarg actively supplied, ``should_abort`` never firing,
    ``workers`` never resolving above 1 so the parallel branch never triggers) produces a report
    byte-identical to the pre-existing default path — on the REAL, non-degenerate 3-cell
    synthetic-scan-join shape (the iter-4 lesson: never merely the vacuous empty case).

    era-fast_wall J-05: ``sub_cache`` is now threaded through as a REAL ``EdgeReportBacktestCache``
    (no longer the J-04 placeholder sentinel ``object()`` — J-05 gives it genuine caching effect,
    still producing byte-identical output; the dedicated ``sub_cache=None``-vs-warm claim is proven
    in isolation by ``test_sub_cache_supplied_report_is_byte_identical_to_the_default_path``,
    below the J-05 marker)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache_a = EdgeReportCache(str(tmp_path / "cache-a.db"))
    cache_b = EdgeReportCache(str(tmp_path / "cache-b.db"))
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    progress_events: list[dict] = []

    def _progress(patch: dict) -> None:
        progress_events.append(patch)

    default_path = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=cache_a,
    )
    hooked_path = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=cache_b,
        progress=_progress, should_abort=lambda: False, sub_cache=sub_cache, workers=1,
    )

    assert json.dumps(default_path, sort_keys=True) == json.dumps(hooked_path, sort_keys=True)
    assert len(default_path["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape
    assert progress_events  # the hook was genuinely CALLED, not merely accepted and ignored


def test_should_abort_that_fires_mid_run_is_observably_different_and_publishes_nothing(
    tmp_path, store, scan_bar_store, scan_config
):
    """TC-14b — the non-vacuous proof (the iter-3 lesson): a ``should_abort`` that DOES fire
    between pairs changes the observable outcome (raises, publishes nothing) versus one that never
    fires (a normal report, proven above) — never a decorative no-op that would also pass if
    silently ignored."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    calls = {"n": 0}

    def _should_abort() -> bool:
        calls["n"] += 1
        return calls["n"] > 1  # fires at the top of the 2nd pair — never before the 1st

    with pytest.raises(EdgeReportComputeCancelled):
        run_strategy_comparison_report(
            store, dataset_store, scan_bar_store, scan_config, cache=cache, should_abort=_should_abort,
        )

    records, errors = dataset_store.list()
    assert errors == []
    assert cache.lookup(records, scan_config) is None  # nothing was EVER published (TC-3's premise)

    # Cooperative — checked strictly BETWEEN pairs, never mid-backtest: the FIRST pair (v1, the
    # registration order's first strategy) genuinely completed and was persisted as a real backtest
    # record before the second should_abort() check stopped the loop before structure_tape.
    backtests = store.list_backtests(limit=10)
    assert len(backtests) == 1
    assert backtests[0].payload["strategy_id"] == STRATEGY_V1_ID
    assert backtests[0].payload["status"] == STATUS_DONE


def test_force_true_dispatches_through_compute_and_publish(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    calls = []
    real = cache.compute_and_publish

    def _spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(cache, "compute_and_publish", _spy)

    run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=cache, force=True,
    )

    assert len(calls) == 1


def test_force_false_default_still_dispatches_through_get_or_compute(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    calls = []
    real = cache.get_or_compute

    def _spy(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(cache, "get_or_compute", _spy)

    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert len(calls) == 1


def test_force_true_recomputes_over_an_already_warm_key(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-5, at the module level: a call-counting spy on the underlying compute path records a
    FRESH call even though the key is already warm."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    calls = []
    real_compute = edge_report._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)

    run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=cache, force=True,
    )

    assert len(calls) == 1


def test_force_default_over_the_same_warm_key_never_recomputes(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-6, at the module level: the mirror of the test immediately above — zero additional calls
    without ``force``."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    calls = []
    real_compute = edge_report._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_compute_strategy_comparison_report", _counting_compute)

    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert calls == []


def test_a_dataset_integrity_error_still_raises_with_should_abort_and_progress_supplied(
    tmp_path, store, scan_bar_store, scan_config
):
    """No new integrity-bypass path: supplying the new hooks changes nothing about the existing
    store-integrity discipline — a corrupt dataset still aborts the WHOLE report explicitly."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    with pytest.raises(EdgeReportError, match="integrity"):
        run_strategy_comparison_report(
            store, dataset_store, scan_bar_store, scan_config,
            progress=lambda patch: None, should_abort=lambda: False,
        )


# --- ``peek_strategy_comparison_report``'s new ``compute=`` passthrough (era-fast_wall J-04) ------


def test_peek_compute_field_defaults_to_none_exactly_as_before(
    tmp_path, store, scan_bar_store, scan_config
):
    """No caller passes ``compute=`` yet reads a ``null`` — the unchanged J-01 behavior, still true
    with the new keyword-only parameter merely ADDED (default-preserving)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))

    result = peek_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, cache=cache)

    assert result["compute"] is None


def test_peek_compute_field_embeds_whatever_is_passed_verbatim(
    tmp_path, store, scan_bar_store, scan_config
):
    """TC-8's shape: ``peek_strategy_comparison_report`` never re-derives the snapshot — it embeds
    EXACTLY what its caller (the route, reading ``registry.edge_report_compute.snapshot()``) hands
    it, byte-for-byte."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    snapshot = {
        "id": "abc123", "state": "running", "force": False,
        "started_utc": "2026-01-01T00:00:00.000000Z", "finished_utc": None, "error": None,
        "progress": {"phase": "backtests", "backtests_total": 3, "backtests_done": 1,
                     "backtests_from_cache": 0, "current": None},
    }

    result = peek_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, cache=cache, compute=snapshot,
    )

    assert result["compute"] == snapshot


def test_run_strategy_comparison_report_source_documents_the_five_new_hooks():
    """A coherence guard: the five new keyword-only params exist textually on the function's OWN
    signature (never silently absorbed into ``**kwargs`` or dropped). era-fast_wall J-05: ``sub_
    cache``/``workers`` now carry real type hints (``EdgeReportBacktestCache | None`` / ``int |
    None``) since they gained real effect — the literal substrings below are updated to match."""
    import inspect

    src = inspect.getsource(edge_report.run_strategy_comparison_report)
    for hook in (
        "force: bool = False",
        "progress=None",
        "should_abort=None",
        'sub_cache: "EdgeReportBacktestCache | None" = None',
        "workers: int | None = None",
    ):
        assert hook in src


# ==================================================================================================
# The resumable + parallel sweep (era-fast_wall J-05) — ``EdgeReportBacktestCache`` given real
# effect: ``_split_cells``'s ``run_pair`` seam, ``_build_caching_run_pair``, and the CLI-only
# ``_parallel_prewarm_sub_cache``. ``EdgeReportBacktestCache``'s OWN mechanics (keying, durability,
# corrupted-DB tolerance, concurrency) are unit-tested in isolation in
# ``tests/test_edge_report_backtest_cache.py`` against a cheap counting stub — this section proves
# the WIRING into the real ``_split_cells``/``_run_backtest``/``run_strategy_comparison_report``
# path (byte-identity, kill-and-resume, new-dataset-costs-three, cache-loss recompute, the
# non-vacuous multi-process parallel proof).
# ==================================================================================================


def test_build_caching_run_pair_computes_signature_and_config_hashes_once_per_sweep_not_per_pair():
    """Coherence guard (the NOTES' own implementation hint): ``bar_store_signature``/
    ``config_fingerprint``/``config_content_hash``/``strategy_registry`` are computed OUTSIDE the
    ``run_pair`` closure — textually BEFORE ``def run_pair(`` — so they run ONCE per sweep, never
    once per pair (the exact wasteful-recomputation pattern this whole interlude exists to
    remove)."""
    import inspect

    src = inspect.getsource(edge_report._build_caching_run_pair)
    closure_start = src.index("def run_pair(")
    setup, closure_body = src[:closure_start], src[closure_start:]

    assert "_store_signature(bar_store)" in setup
    assert "config.config_fingerprint()" in setup
    assert "_config_content_hash(config)" in setup
    assert "config.strategy_registry()" in setup
    for forbidden in (
        "_store_signature(", "config.config_fingerprint(",
        "_config_content_hash(", "config.strategy_registry(",
    ):
        assert forbidden not in closure_body, f"{forbidden} must not be recomputed per pair"


def test_sub_cache_supplied_report_is_byte_identical_to_the_default_path(
    tmp_path, store, scan_bar_store, scan_config
):
    """TC-13: ``sub_cache=None`` (today's pre-J-05 shape) vs a genuinely warm ``sub_cache``
    produce byte-identical reports for the SAME inputs."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    without_sub_cache = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
    with_sub_cache = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache,
    )

    assert json.dumps(without_sub_cache, sort_keys=True) == json.dumps(with_sub_cache, sort_keys=True)
    assert len(without_sub_cache["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape


def test_a_fully_cached_sweep_publishes_every_eligible_pair_and_is_byte_identical(
    tmp_path, store, scan_bar_store, scan_config
):
    """TC-4: given the fixture dataset registry and a fresh, empty ``EdgeReportBacktestCache`` DB,
    a full sweep publishes a durable row for EVERY eligible (dataset, strategy) pair, and the
    returned report is byte-identical to the SAME inputs computed with ``sub_cache=None``."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache_db_path = tmp_path / "sub-cache.db"
    sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))

    warm = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)
    fresh = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)  # sub_cache=None

    assert json.dumps(warm, sort_keys=True) == json.dumps(fresh, sort_keys=True)

    import sqlite3

    conn = sqlite3.connect(str(sub_cache_db_path))
    try:
        (count,) = conn.execute("SELECT COUNT(*) FROM edge_report_backtest_cache").fetchone()
    finally:
        conn.close()
    assert count == 3  # one row per (dataset, strategy) pair -- 1 dataset x 3 registered strategies


def test_kill_and_resume_recomputes_only_the_missing_pairs(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-6: a sweep aborted (via ``should_abort``) after publishing N pairs, re-triggered with the
    SAME ``sub_cache``, makes fresh ``_run_backtest`` calls for ONLY the remaining pairs, and the
    progress snapshot's ``backtests_from_cache`` equals N."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    should_abort_calls = {"n": 0}

    def _should_abort() -> bool:
        should_abort_calls["n"] += 1
        return should_abort_calls["n"] > 1  # fires at the top of the 2nd pair -- never before the 1st

    with pytest.raises(EdgeReportComputeCancelled):
        run_strategy_comparison_report(
            store, dataset_store, scan_bar_store, scan_config,
            sub_cache=sub_cache, should_abort=_should_abort,
        )

    import sqlite3

    conn = sqlite3.connect(sub_cache.db_path)
    try:
        (published_before_resume,) = conn.execute("SELECT COUNT(*) FROM edge_report_backtest_cache").fetchone()
    finally:
        conn.close()
    assert published_before_resume == 1  # exactly the first (v1) pair persisted before the abort

    calls = []
    real_run_backtest = edge_report._run_backtest

    def _counting_run_backtest(*args, **kwargs):
        calls.append(1)
        return real_run_backtest(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)

    progress_events: list[dict] = []
    result = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config,
        sub_cache=sub_cache, progress=progress_events.append,
    )

    assert len(calls) == 2  # only the 2 REMAINING (of 3 total) pairs recomputed
    pair_done_events = [e for e in progress_events if e.get("event") == "pair_done"]
    assert pair_done_events[-1]["backtests_from_cache"] == 1  # the ONE pair served from cache
    assert len(result["train"]["cells"]) == 3  # the reassembled report is still complete/correct


def test_a_new_dataset_costs_exactly_three_fresh_backtests_on_a_warm_sub_cache(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-7: given a fully-warm sub-cache for the existing fixture registry, registering ONE
    additional dataset and re-triggering the sweep costs EXACTLY three new ``_run_backtest`` calls
    (one per registered strategy), zero for the pre-existing dataset."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))
    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)

    _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")

    calls = []
    real_run_backtest = edge_report._run_backtest

    def _counting_run_backtest(*args, **kwargs):
        calls.append(1)
        return real_run_backtest(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)

    result = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)

    assert len(calls) == 3  # exactly 3 fresh backtests for the ONE new dataset, 0 for the pre-existing one
    v1_cell = next(c for c in result["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
    assert v1_cell["measurement"]["n"] == 2  # both datasets pooled into the recomputed cell


def test_deleting_the_sub_cache_db_triggers_a_full_recompute_byte_identical_to_the_original(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-9: deleting the sub-cache DB file loses nothing — the next sweep fully recomputes every
    pair (a call-counting spy confirms it, never merely inferred from the output alone) and
    republishes, producing a report byte-identical to the original warm-cache report."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache_db_path = tmp_path / "sub-cache.db"
    sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))

    original = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)

    for suffix in ("", "-wal", "-shm"):
        sidecar = Path(str(sub_cache_db_path) + suffix)
        if sidecar.exists():
            sidecar.unlink()

    calls = []
    real_run_backtest = edge_report._run_backtest

    def _counting_run_backtest(*args, **kwargs):
        calls.append(1)
        return real_run_backtest(*args, **kwargs)

    monkeypatch.setattr(edge_report, "_run_backtest", _counting_run_backtest)

    fresh_sub_cache = EdgeReportBacktestCache(str(sub_cache_db_path))
    store2 = JournalStore(str(tmp_path / "journal-2.db"), scan_config)
    try:
        recomputed = run_strategy_comparison_report(
            store2, dataset_store, scan_bar_store, scan_config, sub_cache=fresh_sub_cache,
        )
    finally:
        store2.close()

    assert len(calls) == 3  # every pair genuinely re-run, never silently served from stale state
    assert json.dumps(recomputed, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_a_corrupted_sub_cache_db_is_treated_as_a_full_miss_never_a_crash(
    tmp_path, store, scan_bar_store, scan_config
):
    """Error case: a corrupted/unreadable sub-cache DB is treated as a full miss (recompute), never
    a crash — proven through the REAL sweep end to end, not merely ``EdgeReportBacktestCache`` in
    isolation (see ``test_edge_report_backtest_cache.py`` for that isolated proof)."""
    garbage_path = tmp_path / "garbage.db"
    garbage_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
    sub_cache = EdgeReportBacktestCache(str(garbage_path))

    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")

    result = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)

    assert len(result["train"]["cells"]) == 3  # a full, correct recompute despite the corrupt DB


def test_a_worker_side_backtest_failure_propagates_as_a_genuine_sweep_failure(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """Error case: a pair's ``_run_backtest`` raising propagates as a genuine sweep failure — never
    a silently-dropped pair, and nothing is published for that pair."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic backtest failure")

    monkeypatch.setattr(edge_report, "_run_backtest", _boom)

    with pytest.raises(RuntimeError, match="synthetic backtest failure"):
        run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache)

    assert sub_cache.lookup("anything") is None  # sanity: cache is still genuinely empty (no crash-loop artifact)


# --- The parallel provider (CLI-only) — a non-vacuous, genuinely multi-process proof (TC-8) -------


def test_parallel_prewarm_uses_at_least_two_distinct_worker_processes_and_reassembles_byte_identically(
    tmp_path, store, scan_bar_store, scan_config, monkeypatch
):
    """TC-8 (non-vacuous): two datasets, each resolving the SAME real classified scan event,
    pre-warmed via ``_parallel_prewarm_sub_cache(..., workers=2)`` — the RETURNED per-task
    ``{"dataset_id", "pid"}`` bookkeeping proves at least two DISTINCT worker process ids were
    genuinely used (never a silent sequential fallback: pids can only cross a process boundary via
    a real child process's own ``os.getpid()``, pickled back through the future's result — this
    could not be faked by a same-process shortcut), and the reassembled report (via the SAME
    untouched sequential ``run_strategy_comparison_report`` call, now 100% cache hits) is
    byte-identical to an INDEPENDENT, wholly sequential compute of the SAME inputs.

    ``_parallel_prewarm_sub_cache`` derives its workers' dataset directory from
    ``config.dataset_dir_resolved()`` (the CLI's OWN construction invariant — see that function's
    own docstring), so this test sets ``TAPEOLOGY_DATASET_DIR`` to match ``dataset_store``'s actual
    root, exactly as the real CLI's ``main()`` always does."""
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
    _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")

    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache-parallel.db"))
    task_results = edge_report._parallel_prewarm_sub_cache(
        dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache, workers=2,
    )

    assert len(task_results) == 2  # one task per dataset -- "task = one dataset, all 3 strategies"
    pids = {r["pid"] for r in task_results}
    assert len(pids) >= 2, f"expected >=2 distinct worker pids, got {pids}"

    parallel_report = run_strategy_comparison_report(
        store, dataset_store, scan_bar_store, scan_config, sub_cache=sub_cache,
    )  # 100% cache hits -- pure sequential reassembly, never a fresh backtest

    sequential_store = JournalStore(str(tmp_path / "journal-seq.db"), scan_config)
    try:
        sequential_report = run_strategy_comparison_report(
            sequential_store, dataset_store, scan_bar_store, scan_config,
        )  # sub_cache=None -- a wholly independent fresh compute
    finally:
        sequential_store.close()

    assert json.dumps(parallel_report, sort_keys=True) == json.dumps(sequential_report, sort_keys=True)
    assert len(parallel_report["train"]["cells"]) == 3  # non-degenerate: the real 3-cell shape


def test_parallel_prewarm_with_zero_eligible_datasets_never_spins_up_a_process_pool(
    tmp_path, store, monkeypatch
):
    """A registry with zero eligible pairs (the committed J-03 fixture's own PG symbol, not a
    config-owned panel symbol) returns immediately without ever constructing a
    ``ProcessPoolExecutor`` — no wasted worker-startup cost for nothing to do."""
    dataset_store = DatasetStore(FIXTURE_J03_DATASET_DIR)
    bar_store = BarStore(tmp_path / "empty-bars")
    sub_cache = EdgeReportBacktestCache(str(tmp_path / "sub-cache.db"))

    def _boom(*args, **kwargs):
        raise AssertionError("ProcessPoolExecutor must never be constructed with zero eligible tasks")

    monkeypatch.setattr(edge_report, "ProcessPoolExecutor", _boom)

    results = edge_report._parallel_prewarm_sub_cache(
        dataset_store, bar_store, CONFIG, sub_cache=sub_cache, workers=4,
    )

    assert results == []
