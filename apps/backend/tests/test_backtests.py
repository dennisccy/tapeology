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

from app.config import CONFIG, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID, STRATEGY_V1_ID
from app.providers.adapters.base import RawBar
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
from app.research.backtests import (
    BacktestJobManager,
    BacktestRunner,
    EXIT_DATASET_END,
    EXIT_HORIZON,
    EXIT_REWARD_TARGET,
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
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.marks import r_basis
from app.research.store import JournalStore
from app.research.studies import _PathPoint

# The synthetic three-timeframe confluence fixture (class A/B/C zones at exact, known prices) --
# REUSED verbatim from test_levels.py (the plan's own directive: the committed real PG bar fixture
# stores only two timeframes and can NEVER produce a class-A zone, so any structure_tape arming
# test that needs one must use THIS fixture, not a second copy of it).
from test_levels import _BASE as _CONFLUENCE_BASE, _CONFLUENCE_SYMBOL, _DAY, _confluence_fixture

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


def _run(
    jobs,
    store,
    dataset_store,
    dataset_id,
    *,
    strategy_id=STRATEGY_V1_ID,
    profile=PROFILE_DEFAULT,
    bar_store=None,
) -> dict:
    payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
    jobs.run_sync(payload["id"], dataset_store=dataset_store, bar_store=bar_store)
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


# --- Strategy grammar structure_tape: additive, config-owned (era-4 J-04; Data Contract row 41) ---
# The SYN-CONFLUENCE synthetic bar fixture's own committed as-of instant (test_levels.py's own
# proof point — "comfortably past every period's closure, 1w's 604800s is longest") is REUSED here
# as the epoch_anchor for every structure_tape tape dataset below. ``epoch_anchor`` is PURELY
# additive display metadata (app/engine/tape_engine.py — never read by classification), so a canned
# SIM_SCENARIOS stream (whose own prices/timing are deterministic and already proven throughout
# this file) can be recorded under ANY epoch_anchor without changing a single classified
# tape_state or price — decoupling the tape's calendar reference from the bar series' calendar
# reference lets BOTH fixtures be reused verbatim, unmodified.
_STRUCTURE_TAPE_ANCHOR = _CONFLUENCE_BASE + 8 * _DAY


@pytest.fixture
def confluence_bar_store(tmp_path):
    bar_store = BarStore(tmp_path / "confluence-bars")
    _confluence_fixture(bar_store)
    return bar_store


def _record_structure_tape_dataset(
    tmp_path, ticker, *, anchor=_STRUCTURE_TAPE_ANCHOR, max_logical=25.0, symbol=_CONFLUENCE_SYMBOL
):
    """Record ONE canned SIM_SCENARIOS stream (its price/state path already proven elsewhere in
    this file) as a dataset stamped with the given symbol (so the runner's ``compute_levels`` call
    finds the matching bar fixture) and the given epoch anchor."""
    events, provider = _sim_events(ticker, max_logical)
    return _record(
        tmp_path / "datasets", events, symbol=symbol, scenario=provider.scenario, anchor=anchor
    )


# --- Class-scaled stop/reward/size fixtures (era-4 capability 5, J-05; Data Contract row 41
# extension) — the SAME SYN-CONFLUENCE class-A zone above already sits at ~100.00; these TWO
# additional synthetic bar fixtures put a class-B and a class-C zone at the SAME ~100.00 price
# SIM-BUYER's proven breakthrough-long path already crosses, so all three classes are measured via
# the IDENTICAL tape stream — only the bar series (and therefore the confluence class) differs.
_CLASS_B_SYMBOL = "SYN-CLASS-B"


def _class_b_bar_fixture(store: BarStore) -> None:
    """A TWO-timeframe (1h + 1d) fixture producing exactly ONE confluence zone at ~100.00 — class
    B (2 distinct timeframes, below the class-A floor of 3 — the SAME mechanism the real committed
    PG fixture already proves in ``tests/test_levels.py``). No other zone exists in this store, so
    the reward-target's "next opposing level" search honestly finds none (the uncapped fallback)."""
    hourly_specs = [(50, 40, 45), (100.00, 41, 98), (55, 42, 50)]
    hourly_bars = [
        RawBar(_CLASS_B_SYMBOL, "1h", _CONFLUENCE_BASE + i * 3600.0, close, high, low, close, 1_000)
        for i, (high, low, close) in enumerate(hourly_specs)
    ]
    daily_bars = [
        RawBar(_CLASS_B_SYMBOL, "1d", _CONFLUENCE_BASE + 0 * _DAY, 100.02, 900, 10, 100.02, 1_000),
    ]
    store.record(
        symbol=_CLASS_B_SYMBOL, timeframe="1h",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T03:00:00Z",
        feed="sip", bars=hourly_bars,
    )
    store.record(
        symbol=_CLASS_B_SYMBOL, timeframe="1d",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-02T00:00:00Z",
        feed="sip", bars=daily_bars,
    )


@pytest.fixture
def class_b_bar_store(tmp_path):
    bar_store = BarStore(tmp_path / "class-b-bars")
    _class_b_bar_fixture(bar_store)
    return bar_store


_CLASS_C_SYMBOL = "SYN-CLASS-C"


def _class_c_bar_fixture(store: BarStore) -> None:
    """A ONE-timeframe (1h) fixture producing TWO confluence zones, both class C (a single
    timeframe — below the class-B floor of 2 distinct timeframes): the NEAR zone at ~100.00/100.05
    (the SAME price SIM-BUYER already breaks through — the arming zone) and a FAR zone at
    ~100.30/100.32 — close enough to entry to become the reward-target's "next opposing level"
    bound (proving the CAPPED branch of the class-scaled reward target), yet far enough from the
    near zone's own anchor (100.00) to stay a SEPARATE cluster rather than merging into one (per
    ``_cluster_levels``'s anchor-fixed confluence band — verified by direct computation, not
    hand-derived)."""
    hourly_specs = [
        (50, 40, 45), (100.00, 41, 98), (52, 42, 50), (100.05, 43, 99), (54, 44, 53),
        (100.30, 45, 101), (56, 46, 55), (100.32, 47, 102), (58, 48, 57),
    ]
    hourly_bars = [
        RawBar(_CLASS_C_SYMBOL, "1h", _CONFLUENCE_BASE + i * 3600.0, close, high, low, close, 1_000)
        for i, (high, low, close) in enumerate(hourly_specs)
    ]
    store.record(
        symbol=_CLASS_C_SYMBOL, timeframe="1h",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T09:00:00Z",
        feed="sip", bars=hourly_bars,
    )


@pytest.fixture
def class_c_bar_store(tmp_path):
    bar_store = BarStore(tmp_path / "class-c-bars")
    _class_c_bar_fixture(bar_store)
    return bar_store


def test_structure_tape_definition_is_config_owned_and_additive_beside_v1():
    d = CONFIG.strategy_definition(STRATEGY_TAPE_ID)
    assert d is not None
    assert d["strategy_id"] == STRATEGY_TAPE_ID
    assert d["entries"]["proximity_band_bps"] == CONFIG.structure_tape_proximity_band_bps
    assert d["entries"]["rejection_states"] == CONFIG.structure_tape_rejection_state_by_direction
    assert (
        d["entries"]["breakthrough_states"] == CONFIG.structure_tape_breakthrough_state_by_direction
    )
    assert d["entries"]["arm_cooldown_seconds"] == CONFIG.study_arm_cooldown_seconds
    # Era-4 J-05: the r_stop and reward_target exits are CLASS-SCALED (a NEW grammar shape,
    # distinct from v1's own r_stop) — read by name from the three new config dicts.
    assert d["exits"]["r_stop"]["stop_bps_by_class"] == CONFIG.structure_tape_stop_bps_by_class
    assert (
        d["exits"]["reward_target"]["r_multiple_by_class"]
        == CONFIG.structure_tape_reward_r_multiple_by_class
    )
    assert d["size_multiple_by_class"] == CONFIG.structure_tape_size_multiple_by_class
    # Horizon/state-flip/dataset_end/fees/slippage/dollars-per-r stay IDENTICAL to v1's — the SAME
    # config fields, never a second copy of any value.
    v1 = CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert d["exits"]["horizon_seconds"] == v1["exits"]["horizon_seconds"]
    assert d["exits"]["state_flip"] == v1["exits"]["state_flip"]
    assert d["exits"]["dataset_end"] == v1["exits"]["dataset_end"]
    assert d["fees"] == v1["fees"]
    assert d["slippage"] == v1["slippage"]
    assert d["dollars_per_r"] == v1["dollars_per_r"]
    # v1 itself stays completely untouched — no structure_tape vocabulary leaked into its setups,
    # its r_stop grammar, or a class-scaling key it never had.
    assert not any(
        s["setup_type"] in ("rejection", "breakthrough") for s in v1["entries"]["setups"]
    )
    assert "stop_bps_by_class" not in v1["exits"]["r_stop"]
    assert "reward_target" not in v1["exits"]
    assert "size_multiple_by_class" not in v1


def test_strategy_registry_lists_v1_structure_tape_then_structure_tape_map_in_registration_order():
    registry = CONFIG.strategy_registry()
    assert [s["strategy_id"] for s in registry] == [
        STRATEGY_V1_ID,
        STRATEGY_TAPE_ID,
        STRATEGY_TAPE_MAP_ID,
    ]
    assert registry[0] == CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert registry[1] == CONFIG.strategy_definition(STRATEGY_TAPE_ID)
    assert registry[2] == CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)


def test_structure_tape_map_definition_is_config_owned_and_identical_to_structure_tape_except_id():
    """era-5B J-04: ``structure_tape_map`` reuses the EXACT SAME grammar as ``structure_tape`` —
    same entries/exits/fees/slippage/size fields, verbatim, no new magic number — differing ONLY
    in its own ``strategy_id``. What genuinely differs (arming candidate source: tradable-map
    bands instead of raw levels/zones) lives in the backtest runner, not in this definition."""
    tape = CONFIG.strategy_definition(STRATEGY_TAPE_ID)
    tape_map = CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
    assert tape_map is not None
    assert tape_map["strategy_id"] == STRATEGY_TAPE_MAP_ID
    assert {**tape_map, "strategy_id": "x"} == {**tape, "strategy_id": "x"}


def test_default_fingerprint_still_pinned_after_registering_structure_tape_map():
    # structure_tape_map introduces NO new Config field (it reuses the six structure_tape_* fields
    # verbatim — see strategy_definition), so no new exclusion-set entry is needed at all; the
    # fingerprint stays pinned trivially. Verified by direct computation, not assumed.
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"


def test_structure_tape_breakthrough_long_arms_at_the_class_a_resistance_level(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-BUYER: buyer_control reads from 19.5s at 100.18 — already beyond the class-A zone's
    # 1h member at 100.00, so breakthrough arms immediately (the studies' level-cross technique:
    # price beyond the level + the matching control state).
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    assert payload["status"] == STATUS_DONE
    result = payload["result"]
    assert result["strategy_id"] == STRATEGY_TAPE_ID
    assert result["strategy"] == CONFIG.strategy_definition(STRATEGY_TAPE_ID)
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.18
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 100.26
    # Class-scaled stop/size/target (era-4 J-05): the next opposing level on the long side is
    # zone_b's nearest member (200.00, far beyond this trade's own class-A R-multiple distance) —
    # the honest UNCAPPED case.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="A")


def test_structure_tape_breakthrough_short_arms_at_the_class_a_support_level(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-SELLER: seller_control reads from 19.5s at 99.84 — already beyond (below) the class-A
    # zone's 1h member at 100.00.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "short")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 99.84
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 99.76
    # No zone exists BELOW entry in this fixture — the honest no-opposing-zone fallback.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=None)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="A")


def test_structure_tape_rejection_long_arms_at_the_class_a_support_level(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-BIDABS: bid_absorption reads from 19.5s, price HELD FLAT at 100.00 — exactly at the
    # class-A zone's 1h member (within the proximity band; never crossing, genuinely new logic).
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BIDABS")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("rejection", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.00
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 100.00
    # The next opposing level on the long side is zone_b's nearest member (200.00) — far beyond
    # this trade's own tiny class-A R-multiple distance, so uncapped.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="A")


def test_structure_tape_rejection_short_arms_at_the_class_a_resistance_level(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-ASKABS: ask_absorption reads from 19.5s, price HELD FLAT at 100.02 — within the class-A
    # zone's 1h member (100.00) proximity band (0.02 <= 5bps of 100.00 == 0.05).
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-ASKABS")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("rejection", "short")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.02
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 100.02
    # No zone exists BELOW entry in this fixture — the honest no-opposing-zone fallback. Also
    # proves the stop's ENTRY-relative fallback branch: the level-relative price (100.01) sits
    # THROUGH this entry (100.02), so the invalidation re-anchors to the entry instead (still the
    # SAME class-A bps distance) — see ``_assert_structure_tape_trade_arithmetic``.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=None)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="A")


def test_structure_tape_no_arm_when_symbol_has_no_classified_levels(tmp_path, store, jobs):
    # An empty bar store (nothing recorded for this symbol at all) -> compute_levels' own honest
    # no_bar_series_for_symbol state -> zero fabricated arms, never a fallback to v1-like behaviour.
    empty_bar_store = BarStore(tmp_path / "empty-bars")
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=empty_bar_store
    )
    assert payload["status"] == STATUS_DONE
    assert payload["result"]["trades"] == []


def test_structure_tape_no_arm_when_tape_state_is_unconfirmed(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-CHOP never leaves unclear (the existing v1 zero-arm-window precedent) -- a classified
    # level exists, but the tape never confirms either reading, so structure_tape arms nothing.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-CHOP", max_logical=90.0)
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    assert payload["status"] == STATUS_DONE
    assert payload["result"]["trades"] == []


def test_structure_tape_no_arm_before_the_defining_bars_are_visible_no_lookahead(
    tmp_path, store, jobs, confluence_bar_store
):
    # The SAME confluence bar store and the SAME SIM-BUYER tape as the breakthrough-long test
    # above, but anchored so the arm instant (19.5s) maps to an as_of of EXACTLY the fixture's own
    # epoch base -- before even the earliest 1h swing pivot's defining neighbour bar (at base +
    # 7200s) is visible, so compute_levels honestly derives NO levels yet and structure_tape arms
    # NOTHING. Proves the runner computes levels AS OF EACH event's OWN timestamp (epoch_anchor +
    # point.timestamp), never a single fixed whole-history snapshot -- the highest-risk
    # correctness point flagged in the execution plan.
    too_early_anchor = _CONFLUENCE_BASE - 19.5
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER", anchor=too_early_anchor)
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    assert payload["status"] == STATUS_DONE
    assert payload["result"]["trades"] == []


def test_structure_tape_identical_request_rerun_is_byte_identical(
    tmp_path, store, jobs, confluence_bar_store
):
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER")
    first = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    second = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    assert first["id"] != second["id"]
    assert json.dumps(first["result"], sort_keys=True) == json.dumps(second["result"], sort_keys=True)


# --- Class-scaled stop, reward-target, and size (era-4 capability 5, J-05) --------------------------


def test_structure_tape_class_b_stop_is_wider_and_size_smaller_than_class_a(
    tmp_path, store, jobs, class_b_bar_store
):
    # The IDENTICAL SIM-BUYER breakthrough at the IDENTICAL ~100.00 price as the class-A test
    # above — only the bar fixture (and therefore the confluence class) differs.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER", symbol=_CLASS_B_SYMBOL)
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=class_b_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.18
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "B"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 100.26
    # No other zone exists in this fixture — the honest no-opposing-zone fallback.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=None)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="B")
    # Class B is visibly wider/smaller than class A's own breakthrough-long trade (SAME entry
    # price, SAME level price, SAME tape stream — only the class differs): a strictly wider stop
    # (farther invalidation), a strictly smaller notional (fewer shares), traceable to the two
    # named config dicts (never a magic number).
    assert CONFIG.structure_tape_stop_bps_by_class["B"] > CONFIG.structure_tape_stop_bps_by_class["A"]
    assert t["invalidation_price"] < 99.99  # class A's own invalidation on the identical level
    assert (
        CONFIG.structure_tape_size_multiple_by_class["B"]
        < CONFIG.structure_tape_size_multiple_by_class["A"]
    )
    assert t["shares"] < 1052.6315789473024  # class A's own shares on the identical trade shape


def test_structure_tape_class_c_widest_stop_smallest_size_and_reward_target_capped_by_next_opposing_level(
    tmp_path, store, jobs, class_c_bar_store
):
    # The IDENTICAL SIM-BUYER breakthrough at the IDENTICAL ~100.00 price, arming against the NEAR
    # class-C zone; a FAR class-C zone at ~100.30/100.32 sits closer to entry than this trade's own
    # class-C R-multiple distance would reach, so the reward target is CAPPED by it (the "toward
    # the next opposing level" clause, proven — not merely the uncapped R-multiple fallback the
    # class-A/B tests above exercise).
    dstore, meta = _record_structure_tape_dataset(
        tmp_path, "SIM-BUYER", symbol=_CLASS_C_SYMBOL, max_logical=40.0
    )
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=class_c_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.18
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "C"}
    # The reward-target exit fires at the CAPPED price (100.30, the far zone's nearest member) —
    # well before dataset_end, and before the uncapped class-C R-multiple target (100.46) would
    # ever be reached.
    assert t["exit"]["reason"] == EXIT_REWARD_TARGET
    assert t["exit"]["logical_ts"] == 29.0
    assert t["exit"]["price"] == 100.30
    assert t["target_price"] == 100.30
    _assert_structure_tape_trade_arithmetic(t, opposing_price=100.30)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="C")
    # Class C is the widest stop / smallest size of all three classes (SAME entry/level price).
    assert (
        CONFIG.structure_tape_stop_bps_by_class["C"]
        > CONFIG.structure_tape_stop_bps_by_class["B"]
        > CONFIG.structure_tape_stop_bps_by_class["A"]
    )
    assert t["invalidation_price"] < 99.95  # class B's own invalidation on the identical level
    assert (
        CONFIG.structure_tape_size_multiple_by_class["C"]
        < CONFIG.structure_tape_size_multiple_by_class["B"]
        < CONFIG.structure_tape_size_multiple_by_class["A"]
    )
    assert t["shares"] < 434.7826086956446  # class B's own shares on the identical trade shape


def test_structure_tape_reward_target_exit_fires_lookahead_free(
    tmp_path, store, jobs, confluence_bar_store
):
    # The SAME SIM-BUYER breakthrough-long arm as the class-A test above, given enough room
    # (max_logical=100.0, well short of the NEXT arm opportunity at 199.5s) to reach its own
    # class-A reward target (100.75) before ``dataset_end`` or the 120s horizon — proving the
    # take-profit exit genuinely FIRES, at the documented precedence (r_stop, then reward_target,
    # then state_flip, then horizon), never merely computed and ignored.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER", max_logical=100.0)
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.18
    assert t["exit"]["reason"] == EXIT_REWARD_TARGET
    assert t["exit"]["logical_ts"] == 78.0
    assert t["exit"]["price"] == 100.76
    assert t["target_price"] == pytest.approx(100.75)
    # Lookahead-free: the target was fixed AT ARM TIME (19.5s) from the levels visible then — the
    # SAME 100.00 class-A level and the SAME zone_b-derived bound this file's other class-A tests
    # already prove come from that one as-of read, never a later/future levels computation.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="A")


def test_structure_tape_class_scaling_parameters_are_config_sourced_no_magic_numbers():
    # Every class-scaling dict is keyed by exactly the three confluence-zone grades and read BY
    # NAME in research/backtests.py — no inline literal duplicates them.
    for field_name in (
        "structure_tape_stop_bps_by_class",
        "structure_tape_reward_r_multiple_by_class",
        "structure_tape_size_multiple_by_class",
    ):
        value = getattr(CONFIG, field_name)
        assert isinstance(value, dict)
        assert set(value) == {"A", "B", "C"}

    # Better class -> tighter stop, larger size, a more generous reward multiple (goal.md's own
    # class-conviction ordering) -- never inverted.
    stop = CONFIG.structure_tape_stop_bps_by_class
    assert stop["A"] < stop["B"] < stop["C"]
    size = CONFIG.structure_tape_size_multiple_by_class
    assert size["A"] > size["B"] > size["C"]
    reward = CONFIG.structure_tape_reward_r_multiple_by_class
    assert reward["A"] >= reward["B"] >= reward["C"]

    src = (BACKEND_DIR / "app" / "research" / "backtests.py").read_text()
    assert "config.structure_tape_stop_bps_by_class" in src
    assert "config.structure_tape_reward_r_multiple_by_class" in src
    assert "config.structure_tape_size_multiple_by_class" in src


def test_structure_tape_sub_minimum_n_and_zero_trade_class_are_never_fabricated(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-CHOP never leaves unclear (the existing v1/structure_tape zero-arm precedent): zero
    # structure_tape trades yields an honest all-empty per-class breakdown (n=0, rates None) for
    # EVERY class, each still labeled insufficient_sample — never a dishonest 0% and never an
    # omitted class.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-CHOP", max_logical=90.0)
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    assert result["trades"] == []
    by_class = result["aggregates_by_class"]
    assert set(by_class) == {"A", "B", "C"}
    for cls in ("A", "B", "C"):
        assert by_class[cls] == {
            "n": 0,
            "gross_r": 0.0,
            "net_r": 0.0,
            "gross_usd": 0.0,
            "net_usd": 0.0,
            "win_rate": None,
            "max_drawdown_r": None,
            "insufficient_sample": True,
        }


def test_v1_backtest_carries_an_honest_all_empty_per_class_breakdown(tmp_path, store, jobs):
    # v1 trades carry no ``level`` key at all -- the per-class breakdown is computed the SAME way
    # for every strategy (no strategy_id special-casing), so a v1 report honestly shows all THREE
    # classes empty (v1 never touches levels/classes), never an omitted or fabricated field.
    dstore, meta = _record_sim(tmp_path, "SIM-REVERSAL")
    payload = _run(jobs, store, dstore, meta["id"])
    result = payload["result"]
    assert result["aggregates"]["n"] == 2  # the existing v1 precedent (two trades)
    by_class = result["aggregates_by_class"]
    assert set(by_class) == {"A", "B", "C"}
    for cls in ("A", "B", "C"):
        assert by_class[cls]["n"] == 0
        assert by_class[cls]["insufficient_sample"] is True


# --- Strategy grammar structure_tape_map: additive over compute_tradability BANDS (era-5B
# capability 5, J-04) -- REUSES the confluence_bar_store fixture directly above (genuinely
# multi-timeframe: 1h + 1d + 1w -- the iter-1 lesson: a daily-only fixture previously hid a real
# ranking bug, so every arming test below runs against a fixture that mixes timeframes). Every
# value below is VERIFIED BY DIRECT COMPUTATION against this exact fixture (never hand-derived --
# the test_tradability.py/test_setups.py precedent). Through ``compute_tradability`` (as of
# ``_STRUCTURE_TAPE_ANCHOR``, whose basis is the "1d" bar at BASE+1*DAY, close=200.08), the ~100.00
# confluence zone becomes a SUPPORT band [100.00, 100.05] class B (the weekly member has not yet
# closed at this basis, so B -- not the class-A zone test_synthetic_three_timeframe_fixture...
# proves through the DIRECT, far-future compute_levels call above); ~300.00/300.05 becomes a
# RESISTANCE band class C; 500/900/910/20/10 are each unclassified (``class: null``) singleton
# bands with no overlapping confluence zone. --------------------------------------------------------


def test_structure_tape_map_breakthrough_short_arms_at_the_class_b_support_band(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-SELLER: seller_control reads from 19.5s at 99.84 -- beyond (below) the support band's
    # 1h member at 100.00. seller_control -> breakthrough short -> a FLOOR break (goal.md's own
    # floor/ceiling language) -> the SUPPORT side, which is exactly this band's own side.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
    )
    assert payload["status"] == STATUS_DONE
    result = payload["result"]
    assert result["strategy_id"] == STRATEGY_TAPE_MAP_ID
    assert result["strategy"] == CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "short")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 99.84
    # The inherited class is B here (a genuinely DIFFERENT class from structure_tape's own class-A
    # test above) -- the tradable map's own morning-markup basis, not compute_levels' far-future
    # as-of, so the arming level's class is READ from the band, never assumed identical.
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "B"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 99.76
    # Next opposing band price on the short side: the support band at [200.00, 200.08]'s nearest
    # member (200.00) -- EVERY level joins some band (unlike zone membership), so this search finds
    # more candidates than structure_tape's own zone-based one did on the identical trade shape.
    _assert_structure_tape_trade_arithmetic(t, opposing_price=20.0)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="B")


def test_structure_tape_map_rejection_long_arms_at_the_class_b_support_band(
    tmp_path, store, jobs, confluence_bar_store
):
    # SIM-BIDABS: bid_absorption reads from 19.5s, price HELD FLAT at 100.00 -- inside the support
    # band's own [100.00, 100.05] range. bid_absorption -> rejection long -> defends a FLOOR -> the
    # SUPPORT side, matching this band's own side.
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BIDABS")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
    )
    result = payload["result"]
    trades = result["trades"]
    assert len(trades) == 1
    t = trades[0]
    assert (t["setup_type"], t["direction"]) == ("rejection", "long")
    assert t["entry"]["logical_ts"] == 19.5
    assert t["entry"]["price"] == 100.00
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "B"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    assert t["exit"]["logical_ts"] == 25.0
    assert t["exit"]["price"] == 100.00
    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
    _assert_per_class_breakdown_isolates_one_trade(result, cls="B")


def test_structure_tape_map_side_aware_reading_never_arms_on_the_wrong_side_band(
    tmp_path, store, jobs, confluence_bar_store
):
    """A deliberate, flagged design decision (see the dev handoff and
    ``_structure_tape_map_side_for_reading``'s own docstring): unlike ``structure_tape`` (which has
    no side concept and tests every zone regardless of position), ``structure_tape_map`` only tests
    bands on the semantically correct side of a reading. SIM-BUYER's breakthrough-long premise
    (buyer_control -> break a CEILING -> RESISTANCE) and SIM-ASKABS's rejection-short premise
    (ask_absorption -> defend a CEILING -> RESISTANCE) both confirm at price ~100 -- but the ONLY
    classified band there is the SUPPORT band [100.00, 100.05] (class B), so BOTH arm nothing, even
    though structure_tape's OWN zone-based arm (no side filter) DOES arm on the identical zone at
    the identical price (proven directly below as the contrasting positive control)."""
    buyer_dstore, buyer_meta = None, None
    for ticker in ("SIM-BUYER", "SIM-ASKABS"):
        dstore, meta = _record_structure_tape_dataset(tmp_path, ticker)
        if ticker == "SIM-BUYER":
            buyer_dstore, buyer_meta = dstore, meta
        payload = _run(
            jobs, store, dstore, meta["id"],
            strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store,
        )
        assert payload["status"] == STATUS_DONE
        assert payload["result"]["trades"] == [], f"{ticker} must not arm on the wrong-side band"

    # Positive control: the IDENTICAL recorded SIM-BUYER dataset, but run under structure_tape's
    # OWN raw-levels arm (no side filter at all) -- DOES arm at this exact zone, proving the empty
    # result above is this iteration's deliberate side-awareness, not an accidental "nothing there".
    tape_payload = _run(
        jobs, store, buyer_dstore, buyer_meta["id"],
        strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )
    assert len(tape_payload["result"]["trades"]) == 1


def test_structure_tape_map_skips_an_unclassified_band_even_when_price_and_state_qualify(
    confluence_bar_store,
):
    """An UNCLASSIFIED band (``class: null`` -- no overlapping confluence zone, an honest absence
    ``tradability.py`` documents) never arms, even when price sits within its own proximity band
    and the tape state confirms the matching reading -- there is no A/B/C to scale a stop/reward/
    size against. Exercised directly against ``_structure_tape_map_arm`` (never through a full
    backtest run) so the SAME reading/price/side can be tested against BOTH an unclassified band
    (900.0, resistance, singleton, no zone) and a classified one (300.0/300.05, resistance, class
    C) as a clean positive/negative contrast."""
    entries = CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)["entries"]
    # ask_absorption -> rejection short -> defends a CEILING -> RESISTANCE side (matches both
    # bands' own side, isolating the class check alone).
    null_point = _PathPoint(timestamp=0.0, last=900.2, spread=0.02, tape_state="ask_absorption")
    arm = BacktestRunner._structure_tape_map_arm(
        null_point, confluence_bar_store, _CONFLUENCE_SYMBOL, _STRUCTURE_TAPE_ANCHOR, entries, CONFIG
    )
    assert arm is None, "an unclassified band must never arm"

    classified_point = _PathPoint(timestamp=0.0, last=300.02, spread=0.02, tape_state="ask_absorption")
    arm2 = BacktestRunner._structure_tape_map_arm(
        classified_point, confluence_bar_store, _CONFLUENCE_SYMBOL, _STRUCTURE_TAPE_ANCHOR, entries, CONFIG
    )
    assert arm2 is not None, "the SAME reading against a classified band at a nearby price must arm"
    direction, setup_type, level, _opposing = arm2
    assert (direction, setup_type) == ("short", "rejection")
    assert level == {"price": 300.0, "timeframe": "1h", "class": "C"}


def test_structure_tape_map_no_arm_when_symbol_has_no_recorded_bands(tmp_path, store, jobs):
    # An empty bar store -> compute_tradability's own honest no_bar_series_for_symbol state ->
    # zero fabricated arms (the identical structure_tape precedent, era-5B J-04 twinned).
    empty_bar_store = BarStore(tmp_path / "empty-bars")
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
    payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=empty_bar_store
    )
    assert payload["status"] == STATUS_DONE
    assert payload["result"]["trades"] == []


def test_structure_tape_map_identical_request_rerun_is_byte_identical(
    tmp_path, store, jobs, confluence_bar_store
):
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
    first = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
    )
    second = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
    )
    assert first["id"] != second["id"]
    assert json.dumps(first["result"], sort_keys=True) == json.dumps(second["result"], sort_keys=True)


def test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones():
    """Coherence-critical guard (the ``test_structure_tape_reads_levels_from_the_one_canonical_
    compute_levels_owner`` precedent, applied to the NEW arming path): ``_structure_tape_map_arm``
    itself must read the row-"Tradable level map" canonical ``compute_tradability`` owner and must
    NEVER call ``compute_levels`` or re-derive pivots/zones directly -- the tradable map is the
    ONLY lens this strategy reads."""
    import inspect

    src = inspect.getsource(BacktestRunner._structure_tape_map_arm)
    assert "compute_tradability(" in src
    for forbidden in ("compute_levels(", "_swing_pivots", "_prior_period_extremes", "_cluster_levels", "_grade_zone"):
        assert forbidden not in src, f"_structure_tape_map_arm must not recompute levels itself: {forbidden}"


def test_v1_and_structure_tape_byte_identical_after_structure_tape_map_added(
    tmp_path, store, jobs, confluence_bar_store
):
    """Frozen-foundation regression guard (era-5B J-04 DoD): v1's and structure_tape's OWN pinned
    outputs, re-asserted on the EXACT SAME fixtures/inputs their own tests above already prove,
    now that structure_tape_map's additive dispatch branch exists beside them -- the ONE explicit,
    named before/after checkpoint the DoD requires (not a second source of truth; every value here
    is already independently pinned by a dedicated test earlier in this file)."""
    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER")
    tape_payload = _run(
        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
    )
    t = tape_payload["result"]["trades"][0]
    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
    assert t["entry"]["logical_ts"] == 19.5 and t["entry"]["price"] == 100.18
    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
    assert t["exit"]["reason"] == EXIT_DATASET_END
    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)

    dstore2, meta2 = _record_sim(tmp_path, "SIM-BUYER")
    v1_payload = _run(jobs, store, dstore2, meta2["id"])
    v1t = v1_payload["result"]["trades"][0]
    assert (v1t["setup_type"], v1t["direction"]) == ("trend_continuation", "long")
    assert v1t["entry"]["logical_ts"] == 24.5 and v1t["entry"]["price"] == 100.24
    assert v1t["exit"]["reason"] == EXIT_HORIZON
    assert "level" not in v1t


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


def _assert_structure_tape_trade_arithmetic(
    t: dict, *, opposing_price: float | None, config=CONFIG
) -> None:
    """The EXACT class-scaled fill/fee/R/$ arithmetic a ``structure_tape`` trade must satisfy
    (era-4 J-05) — independently re-derived here (the ``_assert_trade_arithmetic`` /
    ``_expected_aggregates`` precedent: never a re-import of the production formula), so a bug
    shared between the implementation and this helper cannot silently agree with itself.

    ``opposing_price`` is the price the caller independently knows ``_next_opposing_zone_price``
    ought to have resolved for this specific trade's fixture (or ``None`` when no zone qualifies
    on that side) — the SAME class R-multiple-vs-opposing-level ``min()`` the production
    ``_class_scaled_target`` applies is re-derived here from it, proving the reward target is
    genuinely bounded both ways, not merely copied from the observed value."""
    level = t["level"]
    direction = t["direction"]
    sign = 1.0 if direction == "long" else -1.0
    entry_price = t["entry"]["price"]

    # Class-scaled, LEVEL-relative invalidation, with the entry-relative fallback when the
    # level-relative price would sit at/through the entry print itself.
    stop_bps = config.structure_tape_stop_bps_by_class[level["class"]]
    band = level["price"] * (stop_bps / 10_000.0)
    if direction == "long":
        level_relative = level["price"] - band
        expected_invalidation = level_relative if level_relative < entry_price else entry_price - band
    else:
        level_relative = level["price"] + band
        expected_invalidation = level_relative if level_relative > entry_price else entry_price + band
    assert t["invalidation_price"] == expected_invalidation
    assert t["r_basis"] == r_basis(entry_price, expected_invalidation)

    # Class-scaled size multiple over the SAME fixed strategy_dollars_per_r notional.
    size_multiple = config.structure_tape_size_multiple_by_class[level["class"]]
    assert t["shares"] == size_multiple * config.strategy_dollars_per_r / t["r_basis"]

    # Reward target: the class R-multiple times R basis, bounded by the distance to
    # ``opposing_price`` when one exists.
    reward_multiple = config.structure_tape_reward_r_multiple_by_class[level["class"]]
    distance = reward_multiple * t["r_basis"]
    if opposing_price is not None:
        distance = min(distance, abs(opposing_price - entry_price))
    assert t["target_price"] == entry_price + sign * distance

    # Fills/fees/slippage/gross-vs-net: the IDENTICAL shape v1/null satisfy (only the
    # invalidation/shares/target formulas above differ for structure_tape).
    entry_spread = t["entry"]["spread"] if (t["entry"]["spread"] or 0) > 0 else 0.0
    exit_spread = t["exit"]["spread"] if (t["exit"]["spread"] or 0) > 0 else 0.0
    entry_slip = entry_spread * config.strategy_slippage_spread_fraction
    exit_slip = exit_spread * config.strategy_slippage_spread_fraction
    assert t["entry"]["fill_price"] == t["entry"]["price"] + sign * entry_slip
    assert t["exit"]["fill_price"] == t["exit"]["price"] - sign * exit_slip
    gross_move = sign * (t["exit"]["price"] - t["entry"]["price"])
    fill_move = sign * (t["exit"]["fill_price"] - t["entry"]["fill_price"])
    fee = max(config.strategy_fee_per_share * t["shares"], config.strategy_fee_min_per_trade)
    assert t["gross_r"] == gross_move / t["r_basis"]
    assert t["gross_usd"] == gross_move * t["shares"]
    assert t["fees_usd"] == 2.0 * fee
    assert t["slippage_usd"] == (gross_move - fill_move) * t["shares"]
    assert t["net_usd"] == fill_move * t["shares"] - t["fees_usd"]
    assert t["net_r"] == t["net_usd"] / config.strategy_dollars_per_r


def _assert_per_class_breakdown_isolates_one_trade(result: dict, *, cls: str) -> None:
    """era-4 J-05 (Data Contract row 42): given a report with EXACTLY one structure_tape trade in
    class ``cls`` and none in the other two, the per-class breakdown must (a) mirror the
    strategy-level aggregate exactly in ``cls``'s own bucket, (b) report the other two classes as
    an honest empty (n=0, rates ``None``), (c) label EVERY bucket ``insufficient_sample`` (n=1 or
    n=0 are both under the reused ``pnl_min_sample_size`` floor of 5), and (d) sum back to the
    strategy-level aggregate's own n/net_r/net_usd — one aggregation, no second scan."""
    by_class = result["aggregates_by_class"]
    assert set(by_class) == {"A", "B", "C"}
    assert by_class[cls] == {**result["aggregates"], "insufficient_sample": True}
    for other in {"A", "B", "C"} - {cls}:
        assert by_class[other] == {
            "n": 0,
            "gross_r": 0.0,
            "net_r": 0.0,
            "gross_usd": 0.0,
            "net_usd": 0.0,
            "win_rate": None,
            "max_drawdown_r": None,
            "insufficient_sample": True,
        }
    assert sum(v["n"] for v in by_class.values()) == result["aggregates"]["n"]
    assert sum(v["net_r"] for v in by_class.values()) == result["aggregates"]["net_r"]
    assert sum(v["net_usd"] for v in by_class.values()) == result["aggregates"]["net_usd"]


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


def test_structure_tape_fields_are_serving_only_excluded_from_fingerprint():
    # structure_tape is read ONLY when structure_tape itself is selected — never by a v1 backtest,
    # the tape engine, or any study/PnL computation this fingerprint stamps — so its own fields'
    # mere presence (at ANY value) must not move the frozen default/v1 fingerprint (the sr_*
    # precedent, applied to a different, brand-new, unrelated strategy).
    base = CONFIG.config_fingerprint()
    assert (
        dataclasses.replace(CONFIG, structure_tape_proximity_band_bps=999.0).config_fingerprint()
        == base
    )
    assert (
        dataclasses.replace(
            CONFIG, structure_tape_rejection_state_by_direction={"long": "x", "short": "y"}
        ).config_fingerprint()
        == base
    )
    assert (
        dataclasses.replace(
            CONFIG, structure_tape_breakthrough_state_by_direction={"long": "x", "short": "y"}
        ).config_fingerprint()
        == base
    )
    # era-4 J-05: the class-scaled stop/reward/size fields join the SAME exclusion — a structure_tape
    # report's own class-scaled config is instead provenanced by its embedded ``strategy`` dict,
    # never by ``config_fingerprint``.
    assert (
        dataclasses.replace(
            CONFIG, structure_tape_stop_bps_by_class={"A": 999.0, "B": 999.0, "C": 999.0}
        ).config_fingerprint()
        == base
    )
    assert (
        dataclasses.replace(
            CONFIG,
            structure_tape_reward_r_multiple_by_class={"A": 999.0, "B": 999.0, "C": 999.0},
        ).config_fingerprint()
        == base
    )
    assert (
        dataclasses.replace(
            CONFIG, structure_tape_size_multiple_by_class={"A": 999.0, "B": 999.0, "C": 999.0}
        ).config_fingerprint()
        == base
    )


def test_default_fingerprint_still_pinned_with_the_new_structure_tape_fields_present():
    # Ground truth (the test_profile_equivalence.py precedent): the founding PnL-ledger row was
    # appended under THIS exact fingerprint. Every new structure_tape field above is present on
    # CONFIG but excluded, so adding them must not move it.
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"


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


def test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner():
    # era-4 J-04's coherence-critical guard: structure_tape MUST read levels/classes from the
    # row-39 compute_levels owner (research/levels.py) — NEVER a second S/R computation inside the
    # backtest runner (the highest coherence risk flagged in the execution plan).
    src = (BACKEND_DIR / "app" / "research" / "backtests.py").read_text()
    assert "from .levels import compute_levels" in src
    assert "compute_levels(" in src
    for forbidden in ("_swing_pivots", "_prior_period_extremes", "_cluster_levels", "_grade_zone"):
        assert forbidden not in src, f"backtests.py must not recompute levels itself: {forbidden}"
