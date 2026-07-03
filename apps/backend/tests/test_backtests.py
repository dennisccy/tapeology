"""Strategy grammar v1 + the deterministic backtest engine (era-3 capability 3/4, J-03) —
runner/manager-level discipline. Data Contract rows 31 (backtest reports) & 34 (strategy v1).

Everything here is hermetic and keyless: datasets are recorded through the REAL ``DatasetStore``
public path (deterministic seeded sim streams and one synthetic two-phase stream — never
hand-crafted report JSON), backtests run SYNCHRONOUSLY (``run_sync``) against a temp-path
``JournalStore``, and the committed miniature train/holdout fixture pair proves the whole
pipeline end-to-end in CI with no credentials.

Locked disciplines (each an anti-goal or a J-03 acceptance clause):
  * the COMPLETE v1 strategy definition is config-owned (Data Contract row 34) — every knob is
    a named ``Config`` field, the definition is a pure read of them (proven by replacing config
    values), and entry arming reuses the studies' sustained-premise rules and constants;
  * fills are honest — at recorded prices adjusted by the configured slippage model, with the
    fee model applied per fill, and the gross-vs-net R/$ arithmetic asserted EXACTLY;
  * every exit reason is exercised (``r_stop`` / ``horizon`` / ``state_flip``) plus the explicit
    deterministic ``dataset_end`` handling for a trade open at stream end;
  * R comes ONLY from the shared ``marks.r_basis`` helper (row 27 — never a second formula) and
    datasets are read ONLY through ``DatasetStore``'s public API (row 30);
  * identical request re-runs are byte-identical on the deterministic ``result`` payload; the
    null baseline is seeded, its seed recorded in the report, reproducible exactly;
  * a window arming zero trades yields an honest n=0 report (empty trades, no error, never
    fabricated) beside its seeded null baseline;
  * the job lifecycle mirrors studies (queued -> running -> done | cancelled | failed persisted;
    a corrupt dataset surfaces an explicit ``failed`` record carrying the integrity error);
  * the new strategy/fee/slippage knobs ENTER ``config_fingerprint`` (they shape persisted
    research values); the serving-only ``backtest_list_max`` is EXCLUDED (pinned both ways).
"""

from __future__ import annotations

import dataclasses
import json
import random
from pathlib import Path

import pytest

from app.config import CONFIG, STRATEGY_V1_ID
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
from app.research.backtests import (
    BacktestJobManager,
    EXIT_DATASET_END,
    EXIT_HORIZON,
    EXIT_R_STOP,
    EXIT_STATE_FLIP,
    NULL_SETUP_TYPE,
    PROFILE_DEFAULT,
    REGISTER,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_QUEUED,
)
from app.research.datasets import DatasetStore
from app.research.marks import r_basis
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + holdout dataset pair (recorded ONCE through the real record
# path by scripts/generate_dataset_fixtures.py) — the keyless CI substrate.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"


# --- deterministic dataset substrates (recorded through the REAL store path) ----------------------


def _sim_events(ticker: str, max_logical: float | None = None):
    """Materialize a deterministic seeded sim stream (optionally truncated at a logical bound)."""
    provider = SimulatedProvider(ticker, SIM_SCENARIOS[ticker])
    events = []
    for event in provider.stream():
        if max_logical is not None and event.timestamp > max_logical:
            break
        events.append(event)
    return events, provider


def _flip_events(ticker: str = "SYN-FLIP"):
    """A synthetic two-phase stream: a buyer-control phase (mirroring the SIM-BUYER shape) then a
    SLOW seller-control phase (the SIM-SELLER mirror) continuing from the walked-up quote — so the
    armed long's state-flip exit fires while price is still comfortably ABOVE its synthetic
    invalidation (the deterministic ``state_flip``-before-``r_stop`` substrate). Recorded through
    the REAL store path like every other test dataset — never hand-crafted report JSON."""
    rng = random.Random(7)
    events: list = []
    bid, ask, t = 100.00, 100.02, 0.0
    for _ in range(120):  # buyer-control phase: 60s logical (the sim shape)
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
    for _ in range(160):  # seller-control phase: 80s logical, continuing from the walked-up quote
        is_sell = rng.random() >= 0.12
        if is_sell and rng.random() < 0.5:
            bid = round(bid - 0.01, 2)
            ask = round(ask - 0.01, 2)
        events.append(QuoteEvent(ticker, t, bid, ask, 800, 800))
        if is_sell:
            events.append(TradeEvent(ticker, t, bid, rng.choice((100, 200, 300, 600)), Side.UNKNOWN))
        else:
            events.append(TradeEvent(ticker, t, ask, rng.choice((100, 200)), Side.UNKNOWN))
        t += 0.5
    return events


def _record(root: Path, events, *, symbol: str, scenario: str, anchor: float | None) -> tuple[DatasetStore, dict]:
    """Record a deterministic event stream as a dataset through the REAL public store path."""
    store = DatasetStore(root)
    meta = store.record(
        symbol=symbol,
        source=scenario,
        source_kind="reference",
        source_id=symbol,
        split="train",
        window_start_utc="2026-01-02T14:30:00Z",
        window_end_utc="2026-01-02T14:45:00Z",
        data_feed="sim",
        epoch_anchor=anchor,
        events=events,
    )
    return store, meta


def _record_sim(tmp_path: Path, ticker: str, max_logical: float | None = None):
    events, provider = _sim_events(ticker, max_logical)
    return _record(
        tmp_path / "datasets", events, symbol=ticker, scenario=provider.scenario, anchor=provider.epoch_anchor
    )


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


@pytest.fixture
def jobs(store):
    return BacktestJobManager(store, CONFIG)


def _run(jobs, store, dataset_store, dataset_id, *, strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT) -> dict:
    payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
    jobs.run_sync(payload["id"], dataset_store=dataset_store)
    return store.get_backtest(payload["id"]).payload


# --- Strategy grammar v1: config-owned (Data Contract row 34) -------------------------------------


def test_strategy_v1_definition_is_config_owned_and_complete():
    d = CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert d is not None
    assert d["strategy_id"] == STRATEGY_V1_ID
    # Entries: the four state-native setup x direction combos, reusing the studies' constants.
    combos = {(s["setup_type"], s["direction"]) for s in d["entries"]["setups"]}
    assert combos == {
        ("trend_continuation", "long"),
        ("trend_continuation", "short"),
        ("absorption_reversal", "long"),
        ("absorption_reversal", "short"),
    }
    assert d["entries"]["arm_sustain_seconds"] == CONFIG.study_arm_sustain_seconds
    assert d["entries"]["arm_cooldown_seconds"] == CONFIG.study_arm_cooldown_seconds
    # Exits: R-stop (the studies' synthetic-invalidation constants), horizon, state-flip, dataset_end.
    assert d["exits"]["r_stop"]["spread_multiple"] == CONFIG.study_occurrence_r_spread_multiple
    assert d["exits"]["r_stop"]["floor"] == CONFIG.study_occurrence_r_floor
    assert d["exits"]["horizon_seconds"] == CONFIG.strategy_exit_horizon_seconds
    assert "state_flip" in d["exits"] and "dataset_end" in d["exits"]
    # Fee model, slippage model, and the fixed $-per-R notional — every knob a named config value.
    assert d["fees"]["per_share"] == CONFIG.strategy_fee_per_share
    assert d["fees"]["min_per_trade"] == CONFIG.strategy_fee_min_per_trade
    assert d["slippage"]["spread_fraction"] == CONFIG.strategy_slippage_spread_fraction
    assert d["dollars_per_r"] == CONFIG.strategy_dollars_per_r
    # The level setups are NOT in v1 (no state-native arming exists for them).
    assert not any(s["setup_type"] in ("level_break", "failed_move_fade") for s in d["entries"]["setups"])


def test_unknown_strategy_id_has_no_definition():
    assert CONFIG.strategy_definition("nope") is None
    assert CONFIG.strategy_definition("") is None


def test_strategy_definition_reads_config_not_literals():
    # Replacing a config knob must flow into the definition — proof the definition is a pure read
    # of config fields (no inline copy of any threshold anywhere).
    custom = dataclasses.replace(
        CONFIG,
        strategy_fee_per_share=0.123,
        strategy_exit_horizon_seconds=45.0,
        strategy_dollars_per_r=250.0,
        strategy_slippage_spread_fraction=0.25,
        strategy_fee_min_per_trade=2.5,
    )
    d = custom.strategy_definition(STRATEGY_V1_ID)
    assert d["fees"]["per_share"] == 0.123
    assert d["fees"]["min_per_trade"] == 2.5
    assert d["exits"]["horizon_seconds"] == 45.0
    assert d["dollars_per_r"] == 250.0
    assert d["slippage"]["spread_fraction"] == 0.25


def test_runner_reads_horizon_from_config_not_literal(tmp_path, store):
    # A shorter configured horizon moves the exit — the runner reads config, never a literal 120.
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER")
    custom = dataclasses.replace(CONFIG, strategy_exit_horizon_seconds=30.0)
    jobs = BacktestJobManager(store, custom)
    payload = _run(jobs, store, dstore, meta["id"])
    trade = payload["result"]["trades"][0]
    assert trade["exit"]["reason"] == EXIT_HORIZON
    assert trade["exit"]["logical_ts"] - trade["entry"]["logical_ts"] >= 30.0
    assert trade["exit"]["logical_ts"] - trade["entry"]["logical_ts"] < 120.0


# --- Exit coverage: every exit reason exercised deterministically ----------------------------------


def test_sim_buyer_arms_one_trend_continuation_long_with_horizon_exit(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER")
    payload = _run(jobs, store, dstore, meta["id"])
    assert payload["status"] == STATUS_DONE
    trades = payload["result"]["trades"]
    assert len(trades) == 1
    t = trades[0]
    # The calibrated deterministic arm: buyer_control reads from 19.5s; the config sustain (5s)
    # arms at 24.5s at the recorded last of 100.24; the 120s horizon exits at 144.5s @ 101.28.
    assert (t["setup_type"], t["direction"]) == ("trend_continuation", "long")
    assert t["entry"]["logical_ts"] == 24.5
    assert t["entry"]["price"] == 100.24
    assert t["exit"]["reason"] == EXIT_HORIZON
    assert t["exit"]["logical_ts"] == 144.5
    assert t["exit"]["price"] == 101.28


def test_truncated_stream_open_trade_exits_dataset_end(tmp_path, store, jobs):
    # Truncate SIM-BUYER at 100s: the 24.5s arm cannot reach its 120s horizon, so the open trade
    # is force-exited at the LAST recorded price, labeled dataset_end — explicit, never silent.
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER", max_logical=100.0)
    payload = _run(jobs, store, dstore, meta["id"])
    trades = payload["result"]["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert t["entry"]["logical_ts"] == 24.5
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 100.0  # the last recorded point


def test_shift_stream_hits_the_r_stop(tmp_path, store, jobs):
    # SIM-SHIFT: buyer control walks price up (arm at 24.5 @ 100.24, synthetic invalidation
    # 10 x 0.02 spread = 0.20 below), then the chop phase prints at 100.00 — through the stop.
    dstore, meta = _record_sim(tmp_path, "SIM-SHIFT")
    payload = _run(jobs, store, dstore, meta["id"])
    trades = payload["result"]["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert t["exit"]["reason"] == EXIT_R_STOP
    assert t["exit"]["logical_ts"] == 60.0
    assert t["exit"]["price"] == 100.00
    assert t["exit"]["price"] <= t["invalidation_price"]  # the recorded print crossed the stop
    assert t["net_r"] < 0  # an r_stop long is a loser net of costs


def test_flip_stream_exits_on_state_flip_and_then_arms_the_short(tmp_path, store, jobs):
    # The synthetic buyer->slow-seller stream: the long exits on the OPPOSING control state
    # (seller_control) while price is still ABOVE its invalidation (state_flip, not r_stop);
    # the sustained seller_control then arms the SHORT combo, which rides to dataset_end.
    events = _flip_events()
    dstore, meta = _record(tmp_path / "datasets", events, symbol="SYN-FLIP",
                           scenario="synthetic buyer then seller", anchor=CONFIG.sim_session_anchor_epoch)
    payload = _run(jobs, store, dstore, meta["id"])
    trades = payload["result"]["trades"]
    assert len(trades) == 2
    long_t, short_t = trades
    assert (long_t["setup_type"], long_t["direction"]) == ("trend_continuation", "long")
    assert long_t["exit"]["reason"] == EXIT_STATE_FLIP
    assert long_t["exit"]["logical_ts"] == 79.0
    assert long_t["exit"]["price"] > long_t["invalidation_price"]  # flipped, never stopped
    assert (short_t["setup_type"], short_t["direction"]) == ("trend_continuation", "short")
    assert short_t["entry"]["logical_ts"] == 84.0
    assert short_t["invalidation_price"] > short_t["entry"]["price"]  # adverse side for a short
    assert short_t["exit"]["reason"] == EXIT_DATASET_END


def test_reversal_covers_absorption_arming_horizon_and_dataset_end(tmp_path, store, jobs):
    # SIM-REVERSAL: sustained bid_absorption arms the absorption_reversal LONG (horizon exit as
    # the buyer phase lifts price), then the sustained buyer_control arms a trend_continuation
    # long that is still open at stream end (dataset_end). One position at a time throughout.
    dstore, meta = _record_sim(tmp_path, "SIM-REVERSAL")
    payload = _run(jobs, store, dstore, meta["id"])
    trades = payload["result"]["trades"]
    assert len(trades) == 2
    first, second = trades
    assert (first["setup_type"], first["direction"]) == ("absorption_reversal", "long")
    assert first["entry"]["logical_ts"] == 24.5
    assert first["entry"]["price"] == 100.00
    assert first["exit"]["reason"] == EXIT_HORIZON
    assert first["net_r"] > 0  # the reversal lifted price — a winner even net of costs
    assert (second["setup_type"], second["direction"]) == ("trend_continuation", "long")
    assert second["exit"]["reason"] == EXIT_DATASET_END
    # Trades never overlap (one open trade at a time).
    assert second["entry"]["logical_ts"] >= first["exit"]["logical_ts"]


# --- Fill honesty: recorded prices, slippage model, fee model, exact R/$ arithmetic ----------------


def _assert_trade_arithmetic(t: dict, config=CONFIG) -> None:
    """The EXACT fill/fee/R/$ arithmetic every trade row (setup or null) must satisfy."""
    sign = 1.0 if t["direction"] == "long" else -1.0
    entry_spread = t["entry"]["spread"] if (t["entry"]["spread"] or 0) > 0 else 0.0
    exit_spread = t["exit"]["spread"] if (t["exit"]["spread"] or 0) > 0 else 0.0
    # Synthetic invalidation on the ADVERSE side; R via the ONE shared marks.r_basis helper.
    band = max(entry_spread * config.study_occurrence_r_spread_multiple, config.study_occurrence_r_floor)
    assert t["invalidation_price"] == t["entry"]["price"] - sign * band
    assert t["r_basis"] == r_basis(t["entry"]["price"], t["invalidation_price"])
    assert t["shares"] == config.strategy_dollars_per_r / t["r_basis"]
    # Fills at recorded prices adjusted ADVERSELY by the slippage model.
    entry_slip = entry_spread * config.strategy_slippage_spread_fraction
    exit_slip = exit_spread * config.strategy_slippage_spread_fraction
    assert t["entry"]["fill_price"] == t["entry"]["price"] + sign * entry_slip
    assert t["exit"]["fill_price"] == t["exit"]["price"] - sign * exit_slip
    # Gross from recorded prices; net from fills minus fees; $ never without its R.
    gross_move = sign * (t["exit"]["price"] - t["entry"]["price"])
    fill_move = sign * (t["exit"]["fill_price"] - t["entry"]["fill_price"])
    fee = max(config.strategy_fee_per_share * t["shares"], config.strategy_fee_min_per_trade)
    assert t["gross_r"] == gross_move / t["r_basis"]
    assert t["gross_usd"] == gross_move * t["shares"]
    assert t["fees_usd"] == 2.0 * fee
    assert t["slippage_usd"] == (gross_move - fill_move) * t["shares"]
    assert t["net_usd"] == fill_move * t["shares"] - t["fees_usd"]
    assert t["net_r"] == t["net_usd"] / config.strategy_dollars_per_r


def test_fill_honesty_exact_arithmetic_on_the_calibrated_trade(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER")
    payload = _run(jobs, store, dstore, meta["id"])
    t = payload["result"]["trades"][0]
    # The buyer stream holds a constant 0.02 spread, so the slippage legs are exact and non-zero.
    assert t["entry"]["spread"] == pytest.approx(0.02)
    _assert_trade_arithmetic(t)
    assert t["slippage_usd"] > 0
    assert t["fees_usd"] > 0


def test_every_trade_row_setup_and_null_satisfies_the_same_arithmetic(tmp_path, store, jobs):
    # SAME exits, SAME fees, SAME slippage for the null baseline — asserted row by row.
    dstore, meta = _record_sim(tmp_path, "SIM-REVERSAL")
    payload = _run(jobs, store, dstore, meta["id"])
    result = payload["result"]
    assert len(result["null_baseline"]["trades"]) > 0
    for t in result["trades"] + result["null_baseline"]["trades"]:
        _assert_trade_arithmetic(t)
    for t in result["null_baseline"]["trades"]:
        assert t["setup_type"] == NULL_SETUP_TYPE  # never dressed up as a real setup


# --- Aggregates: net AND gross R AND $, win rate, max drawdown (R), n ------------------------------


def _expected_aggregates(trades: list[dict]) -> dict:
    n = len(trades)
    gross_r = sum(t["gross_r"] for t in trades)
    net_r = sum(t["net_r"] for t in trades)
    gross_usd = sum(t["gross_usd"] for t in trades)
    net_usd = sum(t["net_usd"] for t in trades)
    win_rate = (sum(1 for t in trades if t["net_r"] > 0) / n) if n else None
    if n:
        peak = 0.0
        cum = 0.0
        dd = 0.0
        for t in trades:
            cum += t["net_r"]
            peak = max(peak, cum)
            dd = max(dd, peak - cum)
        max_dd = dd
    else:
        max_dd = None
    return {
        "n": n,
        "gross_r": gross_r,
        "net_r": net_r,
        "gross_usd": gross_usd,
        "net_usd": net_usd,
        "win_rate": win_rate,
        "max_drawdown_r": max_dd,
    }


def test_aggregates_recompute_exactly_from_the_trade_rows(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-REVERSAL")
    payload = _run(jobs, store, dstore, meta["id"])
    result = payload["result"]
    assert result["aggregates"] == _expected_aggregates(result["trades"])
    assert result["null_baseline"]["aggregates"] == _expected_aggregates(result["null_baseline"]["trades"])
    assert result["aggregates"]["n"] == 2


def test_zero_arm_window_yields_honest_n0_report_beside_its_null_baseline(tmp_path, store, jobs):
    # SIM-CHOP never leaves unclear: zero strategy trades is a DONE report with an empty trade
    # list and n=0 aggregates (win rate / drawdown honestly absent) — never an error, never a
    # fabricated trade — while the seeded random-entry null baseline still measures.
    dstore, meta = _record_sim(tmp_path, "SIM-CHOP", max_logical=90.0)
    payload = _run(jobs, store, dstore, meta["id"])
    assert payload["status"] == STATUS_DONE
    result = payload["result"]
    assert result["trades"] == []
    agg = result["aggregates"]
    assert agg["n"] == 0
    assert agg["win_rate"] is None and agg["max_drawdown_r"] is None
    assert agg["gross_r"] == 0.0 and agg["net_r"] == 0.0
    assert result["null_baseline"]["aggregates"]["n"] == len(result["null_baseline"]["trades"]) > 0


def test_committed_fixture_pair_backtests_keyless_end_to_end(store, jobs):
    # The committed miniature train + holdout pair runs the WHOLE pipeline keyless in CI,
    # whatever its n — the J-02 -> J-03 chain proven on real recorded SIP tape.
    dstore = DatasetStore(FIXTURE_DATASET_DIR)
    records, errors = dstore.list()
    assert errors == [] and len(records) == 2
    for meta in records:
        payload = _run(jobs, store, dstore, meta["id"])
        assert payload["status"] == STATUS_DONE
        result = payload["result"]
        assert result["register"] == REGISTER
        assert result["aggregates"]["n"] == len(result["trades"])
        assert result["dataset"]["id"] == meta["id"]
        assert result["dataset"]["checksum"] == meta["checksum"]


# --- Determinism: byte-identical re-runs; seeded, recorded, reproducible null baseline -------------


def test_identical_request_rerun_is_byte_identical_on_the_result_payload(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-REVERSAL")
    first = _run(jobs, store, dstore, meta["id"])
    second = _run(jobs, store, dstore, meta["id"])
    assert first["id"] != second["id"]  # distinct run identities...
    assert json.dumps(first["result"], sort_keys=True) == json.dumps(second["result"], sort_keys=True)


def test_null_baseline_seed_is_recorded_and_reproduces_exactly(tmp_path, store):
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER")
    jobs = BacktestJobManager(store, CONFIG)
    payload = _run(jobs, store, dstore, meta["id"])
    nb = payload["result"]["null_baseline"]
    assert nb["seed"] == CONFIG.backtest_null_baseline_seed
    assert payload["null_baseline_seed"] == CONFIG.backtest_null_baseline_seed
    assert nb["entry_count"] == CONFIG.backtest_null_entry_count
    assert len(nb["trades"]) <= CONFIG.backtest_null_entry_count
    # Same seed -> identical baseline; a different seed -> a different baseline (genuinely seeded).
    again = _run(jobs, store, dstore, meta["id"])
    assert json.dumps(nb, sort_keys=True) == json.dumps(again["result"]["null_baseline"], sort_keys=True)
    other = BacktestJobManager(store, dataclasses.replace(CONFIG, backtest_null_baseline_seed=999))
    reseeded = _run(other, store, dstore, meta["id"])
    other_nb = reseeded["result"]["null_baseline"]
    assert other_nb["seed"] == 999
    assert [t["entry"]["logical_ts"] for t in other_nb["trades"]] != [
        t["entry"]["logical_ts"] for t in nb["trades"]
    ]


# --- Provenance + the honesty register -------------------------------------------------------------


def test_report_carries_register_and_full_provenance(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER")
    payload = _run(jobs, store, dstore, meta["id"])
    result = payload["result"]
    assert result["register"] == REGISTER == (
        "simulated — assumed fees/slippage — not indicative of live results"
    )
    # Dataset id + checksum + the stored metadata VERBATIM (read through the public store API).
    assert result["dataset"] == dstore.get(meta["id"])
    # The resolved strategy config echoed verbatim (row 34: read by the runner, never restated).
    assert result["strategy"] == CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert result["strategy_id"] == STRATEGY_V1_ID
    assert result["profile"] == PROFILE_DEFAULT
    assert result["config_fingerprint"] == CONFIG.config_fingerprint()


# --- Job lifecycle mirrors studies (queued -> running -> done | cancelled | failed) ---------------


def test_create_persists_queued_with_identity_stamps(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-CHOP", max_logical=30.0)
    payload = jobs.create({"dataset_id": meta["id"], "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT})
    assert payload["status"] == STATUS_QUEUED
    assert payload["dataset_id"] == meta["id"]
    assert payload["strategy_id"] == STRATEGY_V1_ID
    assert payload["profile"] == PROFILE_DEFAULT
    assert payload["null_baseline_seed"] == CONFIG.backtest_null_baseline_seed
    assert payload["config_fingerprint"] == CONFIG.config_fingerprint()
    assert store.get_backtest(payload["id"]).payload == payload
    assert "result" not in payload


def test_cancel_before_run_yields_cancelled_without_a_result(tmp_path, store, jobs):
    # A cancelled backtest never serves a half-computed PnL: explicit ``cancelled``, NO result
    # block (honest omission — a partial simulated PnL would be a misleading number).
    dstore, meta = _record_sim(tmp_path, "SIM-BUYER", max_logical=50.0)
    payload = jobs.create({"dataset_id": meta["id"], "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT})
    jobs.cancel(payload["id"])
    jobs.run_sync(payload["id"], dataset_store=dstore)
    stored = store.get_backtest(payload["id"]).payload
    assert stored["status"] == STATUS_CANCELLED
    assert "result" not in stored
    assert "error" not in stored


def test_corrupt_dataset_yields_explicit_failed_with_the_integrity_error(tmp_path, store, jobs):
    dstore, meta = _record_sim(tmp_path, "SIM-CHOP", max_logical=30.0)
    payload = jobs.create({"dataset_id": meta["id"], "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT})
    # Corrupt the stored file AFTER creation — the store's verified load surfaces the integrity
    # error mid-job and the record resolves to explicit ``failed`` carrying it (never silence,
    # never fabricated results).
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    tampered = path.read_text().replace('"type": "trade"', '"type": "tRade"', 1)
    assert tampered != path.read_text()
    path.write_text(tampered)
    jobs.run_sync(payload["id"], dataset_store=dstore)
    stored = store.get_backtest(payload["id"]).payload
    assert stored["status"] == STATUS_FAILED
    assert "integrity" in stored["error"].lower() or "corrupted" in stored["error"].lower()
    assert "result" not in stored


def test_unknown_dataset_at_run_yields_explicit_failed(tmp_path, store, jobs):
    dstore = DatasetStore(tmp_path / "datasets")
    payload = jobs.create({"dataset_id": "nope", "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT})
    jobs.run_sync(payload["id"], dataset_store=dstore)
    stored = store.get_backtest(payload["id"]).payload
    assert stored["status"] == STATUS_FAILED
    assert "no dataset" in stored["error"]


def test_done_report_has_no_progress_residue_and_survives_store_reload(tmp_path):
    db = str(tmp_path / "journal.db")
    store = JournalStore(db, CONFIG)
    try:
        jobs = BacktestJobManager(store, CONFIG)
        dstore, meta = _record_sim(tmp_path, "SIM-BUYER", max_logical=100.0)
        payload = _run(jobs, store, dstore, meta["id"])
        assert payload["status"] == STATUS_DONE
        assert "events_processed" not in payload and "progress" not in payload
    finally:
        store.close()
    # A brand-new store over the same file serves the identical persisted row (rows survive reload).
    reopened = JournalStore(db, CONFIG)
    try:
        assert reopened.get_backtest(payload["id"]).payload == payload
        assert len(reopened.list_backtests(limit=10)) == 1
    finally:
        reopened.close()


# --- Fingerprint discipline (the intended shift + the serving-only exclusion) ----------------------


def test_new_strategy_and_backtest_knobs_move_the_fingerprint():
    # These SHAPE persisted research values (which trades arm, the fills, the fees, the null
    # baseline), so each MUST move ``config_fingerprint`` — the never-pool honesty mechanism.
    base = CONFIG.config_fingerprint()
    for field, value in (
        ("strategy_exit_horizon_seconds", 60.0),
        ("strategy_fee_per_share", 0.009),
        ("strategy_fee_min_per_trade", 2.0),
        ("strategy_slippage_spread_fraction", 0.75),
        ("strategy_dollars_per_r", 500.0),
        ("backtest_null_entry_count", 7),
        ("backtest_null_baseline_seed", 4242),
    ):
        assert dataclasses.replace(CONFIG, **{field: value}).config_fingerprint() != base, field


def test_backtest_list_max_is_serving_only_excluded_from_fingerprint():
    # A list page size touches NO persisted backtest value — two journals identical in every
    # threshold but served at different page sizes MUST share a fingerprint (the study_list_max
    # precedent).
    assert dataclasses.replace(CONFIG, backtest_list_max=7).config_fingerprint() == CONFIG.config_fingerprint()


def test_a_real_threshold_still_changes_the_fingerprint():
    assert dataclasses.replace(CONFIG, min_aggressive_buy_ratio=0.61).config_fingerprint() != CONFIG.config_fingerprint()


# --- Single-source discipline: one R formula, one dataset reader ------------------------------------


def test_runner_consumes_the_shared_r_helper_and_the_public_dataset_api():
    src = (BACKEND_DIR / "app" / "research" / "backtests.py").read_text()
    # R comes ONLY from the shared marks.r_basis helper (row 27 — never a second formula).
    assert "from .marks import r_basis" in src
    # Datasets are read ONLY through DatasetStore's public API (row 30 — never a second file
    # reader): the runner replays via the store and never opens/parses dataset files itself.
    assert ".replay(" in src
    for forbidden in ("json.load", "read_text", "open(", "_load("):
        assert forbidden not in src, f"backtests.py must not read dataset files itself: {forbidden}"
