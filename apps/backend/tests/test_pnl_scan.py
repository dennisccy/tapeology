"""The candidate-sweep harness (era-3 capability 7, J-07) — ``app/research/pnl_scan.py`` +
``python -m app.research.pnl_scan --out <path>``. Data Contract row 36's ONE computer.

Everything is hermetic and keyless: every dataset is either the committed miniature train +
hold-out fixture pair (recorded once through the real record path, the ``test_backtests.py`` /
``test_profile_equivalence.py`` precedent) or a deterministic seeded synthetic stream recorded
through the REAL ``DatasetStore`` public path (never hand-crafted report JSON), and every sweep
runs SYNCHRONOUSLY (``run_sweep`` calling ``BacktestJobManager.create`` + ``run_sync`` — the
EXISTING J-03 computation path, never a second one).

Locked disciplines (each a J-07 acceptance clause):
  * the fixture sweep is the non-regression baseline: on the committed train/hold-out pair the
    ONE registered candidate is a non-survivor (hold-out net R negative, and — independently — its
    n is below the promotion minimum), the champion stays ``v1``/``default``, and the founding
    ledger row (if present) is untouched;
  * a genuine hold-out survivor (an isolated, controlled synthetic scenario — never the shipped
    fixture pair, and never by weakening the shipped promotion-minimum default) moves the ONE
    persisted champion pointer and appends EXACTLY one provenance-stamped ledger row via the
    EXISTING single writer (``pnl_ledger.append_validation_row``), leaving ``default`` and every
    engine default untouched;
  * the promotion-minimum-n gate is enforced BOTH ways (a test-local lowered/raised threshold via
    ``dataclasses.replace`` — never the shipped default);
  * two independent fresh-state runs of an identical NON-PROMOTING scenario produce byte-identical
    ``--out`` file bytes (no wall-clock or per-run-random field in the report itself);
    ``robustness`` is ``robust`` iff positive on every individual train dataset, else
    ``speculative``; ``overfit`` is positive-train/failing-hold-out, and an overfit candidate is
    never promoted;
  * the champion is single-sourced (``GET``-equivalent projection reflects the persisted pointer)
    and exactly one source file calls the pointer's setter;
  * every failure mode is explicit and distinct: zero candidates or zero survivors is an honest
    exit-0 report; a corrupted dataset aborts with nothing written; a mid-promotion crash (ledger
    row appended, pointer not yet moved) is detected and refused explicitly on retry — never a
    silent orphan or a silent double-append.
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
    Config,
    PROFILE_CANDIDATE_FASTER_WARMUP,
    PROFILE_DEFAULT,
    STRATEGY_TAPE_ID,
    STRATEGY_V1_ID,
)
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
from app.research import pnl_scan
from app.research.bars import BarStore
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, record_from_source
from app.research.pnl_baseline import seed_founding_row
from app.research.pnl_scan import ScanError, run_sweep
from app.research.profiles import profiles_projection
from app.research.store import JournalStore

# The SAME synthetic three-timeframe confluence fixture test_backtests.py reuses (its own directive:
# the committed real PG bar fixture stores only two timeframes and can never produce a class-A
# zone, so any structure_tape test that needs one must use THIS fixture, not a second copy of it).
from test_levels import _BASE as _CONFLUENCE_BASE, _CONFLUENCE_SYMBOL, _DAY, _confluence_fixture

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's
# ``test_committed_fixture_pair_backtests_keyless_end_to_end`` uses) — the keyless CI substrate.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"
# The committed multi-timeframe PG bar fixture (era-4 J-01, 1h + 1d only — test_backtests.py's own
# proof that it can never yield a class-A zone) — the keyless CI level source for the strategy axis.
FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"

# The SAME founding windows the PnL ledger's founding row measures (config-owned; the
# ``test_profile_equivalence.py`` precedent) — used ONLY for the "overfit" scenario below, where a
# REAL, already-pinned candidate-loses-on-hold-out window is the simplest honest substrate.
_HOLDOUT_WINDOW = CONFIG.pnl_founding_holdout_window


# --- deterministic synthetic substrates (recorded through the REAL store path) --------------------
# A two-phase stream: phase A ramps price up under sustained one-sided aggression (the SIM-BUYER
# shape test_backtests.py already proves arms a trend_continuation long); phase B holds the quote
# at its walked-up level under the SAME aggression mix (no further price progress). Because the
# candidate profile's lower warm-up floor (era-3 capability 2, J-06) lets it read the FIRST
# directional call several seconds earlier than ``default`` on the identical stream (the SAME
# mechanism ``test_profile_equivalence.py`` pins on the real fixture), the candidate arms its
# horizon-exited long at a LOWER (better) entry price on ramp_ticks >= ~90 -- empirically robust
# across seeds, asserted below rather than merely assumed.


def _ramp_then_flat_events(
    ticker: str, *, ramp_ticks: int, flat_ticks: int, seed: int
) -> list:
    rng = random.Random(seed)
    events: list = []
    bid, ask, t = 100.00, 100.02, 0.0
    for _ in range(ramp_ticks):  # phase A: sustained buyer aggression, quote walks up
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
    for _ in range(flat_ticks):  # phase B: same aggression mix, quote frozen (no more progress)
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
    """A dataset on which the candidate profile LEGITIMATELY beats the default profile (earlier,
    cheaper entry into a move that is still running at both entrants' horizon exit) — proven
    empirically across seeds, not merely assumed; every caller of this helper asserts the sign."""
    return _record(dstore, ticker, _ramp_then_flat_events(ticker, ramp_ticks=90, flat_ticks=400, seed=seed), split=split)


def _flat_dataset(dstore: DatasetStore, ticker: str, seed: int, *, split: str) -> dict:
    """A dataset with NO sustained price ramp — the candidate's earlier read has nothing extra to
    capture, so it does not reliably beat the champion (used to break "robust" without being a
    dramatic loser)."""
    return _record(dstore, ticker, _ramp_then_flat_events(ticker, ramp_ticks=0, flat_ticks=250, seed=seed), split=split)


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


# --- Fixture sweep: the non-regression baseline (Key Test Scenario 1) ------------------------------


def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store, tmp_path):
    """On the committed fixture pair, ``candidate-faster-warmup`` is a non-survivor: identical
    trades on train (delta exactly zero) and a NEGATIVE hold-out delta with n below the
    promotion minimum — both independently sufficient to refuse promotion. Seeds the founding
    ledger row FIRST (the production sequence) so the DoD's "ledger still has row_count 1" and
    "default fingerprint still pinned" clauses are exercised for real, not merely asserted in the
    abstract."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    created, _ = seed_founding_row(store, DatasetStore(tmp_path / "founding-datasets"), CONFIG)
    assert created is True

    report = run_sweep(store, dataset_store, CONFIG)

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == report["champion_before"]
    assert report["promotion"] is None
    (candidate,) = report["candidates"]
    assert candidate["candidate_id"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert candidate["survivor"] is False
    assert candidate["robustness"] == "speculative"
    assert candidate["overfit"] is False
    # Train: the candidate's earlier call does not move this fixture's sustained-arm instant —
    # identical trades, delta EXACTLY zero (pinned by test_profile_equivalence.py too).
    assert candidate["train"]["aggregate"]["delta_net_r"] == 0.0
    assert candidate["train"]["aggregate"]["delta_net_usd"] == 0.0
    # Hold-out: a real, materially worse entry — negative delta, AND n(=1) below the minimum.
    assert candidate["holdout"]["aggregate"]["delta_net_r"] == pytest.approx(-0.5062000000002079)
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert 1 < CONFIG.promotion_min_sample_size

    # Untouched: the founding row is still the only row; the default fingerprint is still pinned.
    assert len(store.list_pnl_ledger()) == 1
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert profiles_projection(store, CONFIG)["champion"] == report["champion_before"]


def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch):
    """Zero registered candidates -> an explicit, honest empty report (never an error) — the
    ``profile_registry`` filter to non-default entries applied to an all-default registry."""
    monkeypatch.setattr(
        Config,
        "profile_registry",
        lambda self: [{"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}],
    )
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    report = run_sweep(store, dataset_store, CONFIG)
    assert report["candidates"] == []
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0


# --- Controlled survivor: a genuine, isolated hold-out win (Key Test Scenario 2) --------------------


def test_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(store, tmp_path):
    """An ISOLATED synthetic train + hold-out pair (never the shipped fixture) on which the
    candidate legitimately beats the champion on BOTH splits, with a test-LOCAL lowered
    promotion minimum (``dataclasses.replace`` — the shipped default of 5 is never touched):
    promotes for real — champion pointer moves, exactly one provenance-stamped ledger row is
    appended via the existing single writer — while ``default`` and every engine default stay
    byte-identical."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(store, dataset_store, test_config)

    (candidate,) = report["candidates"]
    # The win is asserted, not merely assumed (both R and $ on both splits, empirically robust).
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["survivor"] is True
    assert candidate["robustness"] == "robust"
    assert candidate["overfit"] is False

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == {
        "strategy_id": STRATEGY_V1_ID,
        "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
    }
    assert report["promotion"] == {
        "candidate_id": PROFILE_CANDIDATE_FASTER_WARMUP,
        "promoted": True,
        "enhancement_id": f"{PROFILE_CANDIDATE_FASTER_WARMUP}-over-{STRATEGY_V1_ID}-{PROFILE_DEFAULT}",
    }

    rows = store.list_pnl_ledger()
    assert len(rows) == 1
    row = rows[0].payload
    assert row["founding"] is False
    assert row["baseline"]["train"]["net_r"] == pytest.approx(
        candidate["train"]["datasets"][0]["champion"]["net_r"]
    )
    assert row["candidate"]["train"]["net_r"] == pytest.approx(
        candidate["train"]["datasets"][0]["candidate"]["net_r"]
    )
    assert row["provenance"]["strategy_id"] == STRATEGY_V1_ID
    assert row["provenance"]["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert row["provenance"]["train"]["dataset_id"] == train_meta["id"]
    assert row["provenance"]["holdout"]["dataset_id"] == holdout_meta["id"]

    # The default profile and every engine default are byte-identical to before this ran.
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"

    # Single-source: the projection reflects the SAME moved pointer, verbatim.
    assert profiles_projection(store, test_config)["champion"] == report["champion_after"]


# --- Min-n gate, both ways (Key Test Scenario 3) -----------------------------------------------


def test_min_n_gate_rejects_below_minimum_despite_positive_holdout(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=2)  # candidate n=1 < 2

    report = run_sweep(store, dataset_store, test_config)

    (candidate,) = report["candidates"]
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_min_n_gate_promotes_at_or_above_minimum(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)  # candidate n=1 >= 1

    report = run_sweep(store, dataset_store, test_config)

    (candidate,) = report["candidates"]
    assert candidate["survivor"] is True
    assert report["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1


# --- Determinism (Key Test Scenario 4) ----------------------------------------------------------


def test_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_path, monkeypatch):
    """Two INDEPENDENT fresh-state runs (fresh journal DB each) of the identical NON-PROMOTING
    fixture-sweep scenario, driven through the REAL CLI entry point end to end, produce
    byte-identical ``--out`` file contents — no wall-clock or per-run-random field survives into
    the report (raw backtest-report ids, which ARE per-run-random, are stripped before writing)."""
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))

    def _run_once(label: str) -> bytes:
        monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / f"journal-{label}.db"))
        out_path = tmp_path / f"scan-{label}.json"
        monkeypatch.setattr(sys, "argv", ["pnl_scan", "--out", str(out_path)])
        exit_code = pnl_scan.main()
        assert exit_code == 0
        return out_path.read_bytes()

    first = _run_once("a")
    second = _run_once("b")
    assert first == second
    # A sanity floor: the bytes are non-trivial (not an accidentally-empty report).
    assert len(first) > 200


# --- Robustness / overfit labeling (Key Test Scenario 5) -----------------------------------------


def test_robustness_is_speculative_when_not_every_train_dataset_is_positive(store, tmp_path):
    """TWO train datasets — one where the candidate wins, one flat dataset where it does not
    reliably win — beside a winning hold-out: ``robust`` requires EVERY individual train dataset
    to be positive, so this is ``speculative`` even though the aggregate train delta is positive
    and the candidate still survives on hold-out (the two labels are independent axes)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-WIN", seed=7, split=SPLIT_TRAIN)
    _flat_dataset(dataset_store, "SYN-TRAIN-FLAT", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(store, dataset_store, test_config)

    (candidate,) = report["candidates"]
    assert len(candidate["train"]["datasets"]) == 2
    per_dataset_positive = [
        row["delta_net_r"] > 0 and row["delta_net_usd"] > 0
        for row in candidate["train"]["datasets"]
    ]
    assert not all(per_dataset_positive)  # at least one train dataset is NOT a win
    assert candidate["robustness"] == "speculative"
    assert candidate["survivor"] is True  # hold-out alone still passes the gate
    assert candidate["overfit"] is False


def test_overfit_is_positive_train_failing_holdout_and_is_never_promoted(store, tmp_path):
    """Train = an isolated synthetic win; hold-out = the REAL, already-pinned founding hold-out
    window on which the candidate demonstrably loses (``test_profile_equivalence.py``'s own
    pinned numbers). Positive train + a failed hold-out gate = ``overfit`` by the phase spec's own
    definition — and an overfit candidate is never promoted, whatever the train result looked
    like."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-WIN", seed=7, split=SPLIT_TRAIN)
    record_from_source(
        dataset_store,
        source_kind="reference",
        source_id="PG_SIP_REFERENCE",
        split=SPLIT_HOLDOUT,
        start=_HOLDOUT_WINDOW[0],
        end=_HOLDOUT_WINDOW[1],
        config=CONFIG,
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(store, dataset_store, test_config)

    (candidate,) = report["candidates"]
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_r"] < 0
    assert candidate["overfit"] is True
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0


# --- Single-source champion + the one-setter-call-site guard (Key Test Scenario 6) -----------------


def test_champion_pointer_setter_is_called_from_exactly_one_source_file():
    """J-07 is the iteration's only anti-goal-gated state mutation (BACKGROUND, depth=full) — a
    source-scan guard, the ``test_profile_equivalence.py`` ``resolved_for_profile``-caller-guard
    precedent, asserting only ``app/research/pnl_scan.py`` ever calls the champion-pointer
    setter."""
    app_dir = BACKEND_DIR / "app"
    callers = []
    for path in sorted(app_dir.rglob("*.py")):
        if path.name == "store.py":  # the method's own definition site
            continue
        if ".set_champion_pointer(" in path.read_text():
            callers.append(path.relative_to(app_dir).as_posix())
    assert callers == ["research/pnl_scan.py"], callers


# --- Honest failure states (Key Test Scenario 7) --------------------------------------------------


def test_corrupt_dataset_raises_explicit_error_with_nothing_written(store, tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    with pytest.raises(ScanError):
        run_sweep(store, dataset_store, CONFIG)
    # No ledger row, no champion move -- the whole sweep aborted before anything was decided.
    assert len(store.list_pnl_ledger()) == 0
    assert store.get_champion_pointer() == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


def test_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append(store, tmp_path):
    """Simulates 'the pointer-move write never landed' (a crash between the two promotion writes,
    or a store outage) by running a real promotion once and then manually reverting JUST the
    pointer — exactly the state a mid-promotion crash would leave behind (the ledger append is
    durable; the pointer move is the second write). A re-run must refuse explicitly (the ledger's
    own duplicate-enhancement-id structural guard, surfaced as ``ScanError``) rather than silently
    re-promoting (a second ledger row) or silently doing nothing (the caller would never learn the
    champion is still un-moved)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    first = run_sweep(store, dataset_store, test_config)
    assert first["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1

    # Simulate the crash: only the pointer "didn't move" (the ledger row from the first run
    # stands, exactly as the crash-safe write ORDER guarantees).
    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=0.0)

    with pytest.raises(ScanError, match="already exists"):
        run_sweep(store, dataset_store, test_config)
    assert len(store.list_pnl_ledger()) == 1  # never a second row


# --- The CLI entry point itself ---------------------------------------------------------------


def test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))
    out_path = tmp_path / "scan-report.json"
    monkeypatch.setattr(sys, "argv", ["pnl_scan", "--out", str(out_path)])

    exit_code = pnl_scan.main()

    assert exit_code == 0
    payload = json.loads(out_path.read_text())
    assert payload["candidates"][0]["candidate_id"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert payload["promotion"] is None


# --- era-4 J-06: the STRATEGY axis (``structure_tape`` vs ``v1``, Data Contract row 43) -----------
# The synthetic three-timeframe confluence fixture puts a class-A zone at ~100.00 -- test_backtests.py's
# OWN PROVEN, PINNED SIM-BUYER breakthrough-long arm (entry 19.5s @ 100.18, exit at dataset_end @
# whatever the window's last price is) -- so every delta sign asserted below comes from a LIVE run
# through the real sweep path, never a hand-derived number (mirroring this file's own "asserted, not
# merely assumed" discipline for the profile axis above).

_STRUCTURE_TAPE_ANCHOR = _CONFLUENCE_BASE + 8 * _DAY


@pytest.fixture
def confluence_bar_store(tmp_path):
    bar_store = BarStore(tmp_path / "structure-bars")
    _confluence_fixture(bar_store)
    return bar_store


def _sim_buyer_events(max_logical: float) -> list:
    provider = SimulatedProvider("SIM-BUYER", SIM_SCENARIOS["SIM-BUYER"])
    events: list = []
    for event in provider.stream():
        if event.timestamp > max_logical:
            break
        events.append(event)
    return events


def _record_structure_tape_dataset(
    dataset_store: DatasetStore, *, symbol: str, split: str, max_logical: float
) -> dict:
    """Record the SAME canned SIM-BUYER stream test_backtests.py's own structure_tape tests use,
    stamped with ``symbol`` (so the runner's ``compute_levels`` call finds -- or, for a symbol with
    no recorded bar series, honestly does not find -- a matching level) and the shared
    ``_STRUCTURE_TAPE_ANCHOR``. ``max_logical`` truncates the stream -- a longer window gives both
    strategies more room to run without changing which reading first confirms."""
    return dataset_store.record(
        symbol=symbol,
        source="SIM-BUYER",
        source_kind="reference",
        source_id=symbol,
        split=split,
        window_start_utc="2026-01-02T14:30:00Z",
        window_end_utc="2026-01-02T14:45:00Z",
        data_feed="sim",
        epoch_anchor=_STRUCTURE_TAPE_ANCHOR,
        events=_sim_buyer_events(max_logical),
    )


def test_strategy_axis_fixture_sweep_matches_shape_and_is_honestly_no_survivor(store):
    """``--strategy structure_tape`` (via ``run_sweep``) on the COMMITTED PG train/hold-out fixture
    pair, with the COMMITTED PG bar fixture (only 1h/1d -- test_backtests.py's own proof it can
    never yield a class-A zone) as the level source. Per split the report carries the SAME shape
    the profile axis does (champion + candidate measurements, deltas, dataset breakdown) -- and,
    honestly, ``structure_tape`` trades NOTHING on train (no qualifying level ever reached in that
    window) and exactly one class-C trade on hold-out, whose n sits below the promotion minimum --
    the iter-3 lesson (2-timeframe fixture -> mostly class-C, few trades), proven here, not
    assumed."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    bar_store = BarStore(FIXTURE_BAR_DIR)

    report = run_sweep(
        store, dataset_store, CONFIG, candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store
    )

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == report["champion_before"]
    assert report["promotion"] is None
    (candidate,) = report["candidates"]
    assert candidate["candidate_id"] == STRATEGY_TAPE_ID

    # Shape: per split (never pooled), one dataset row carrying both sides' verbatim measurements
    # plus the deltas -- the SAME shape the profile axis produces.
    assert len(candidate["train"]["datasets"]) == 1
    assert len(candidate["holdout"]["datasets"]) == 1
    for split_summary in (candidate["train"], candidate["holdout"]):
        row = split_summary["datasets"][0]
        assert row.keys() >= {"dataset_id", "dataset_checksum", "champion", "candidate", "delta_net_r", "delta_net_usd"}
        assert row["champion"].keys() == {"net_r", "net_usd", "n"}
        assert row["candidate"].keys() == {"net_r", "net_usd", "n"}

    # Honest fixture outcome (iter-3 lesson): zero structure_tape trades on train, exactly one on
    # hold-out, below the promotion minimum -- champion (v1) genuinely lost money on this same train
    # window (the era-3 finding), so the train delta reads positive even though structure_tape did
    # nothing there; a real, non-fabricated mechanical consequence of the existing formula, not a
    # bug -- but the hold-out gate is what actually decides promotion, and it honestly fails.
    assert candidate["train"]["aggregate"]["candidate_n"] == 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert candidate["holdout"]["aggregate"]["candidate_n"] < CONFIG.promotion_min_sample_size
    assert candidate["survivor"] is False

    # Audit B1: disclosed in provenance/assumptions on every report (this axis included).
    assert any(
        "structure_tape" in note and "breakthrough" in note
        for note in report["provenance"]["assumptions"]
    )

    # Nothing written, nothing moved, foundation untouched.
    assert len(store.list_pnl_ledger()) == 0
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"


def test_strategy_axis_determinism_two_independent_fresh_state_runs_are_byte_identical(tmp_path, monkeypatch):
    """The SAME determinism guarantee as the profile axis (Key Test Scenario 4), proven for
    ``--strategy structure_tape`` end to end through the REAL CLI, against the committed PG
    dataset AND bar fixtures."""
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(FIXTURE_DATASET_DIR))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(FIXTURE_BAR_DIR))

    def _run_once(label: str) -> bytes:
        monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / f"journal-strategy-{label}.db"))
        out_path = tmp_path / f"scan-strategy-{label}.json"
        monkeypatch.setattr(
            sys, "argv", ["pnl_scan", "--out", str(out_path), "--strategy", STRATEGY_TAPE_ID]
        )
        exit_code = pnl_scan.main()
        assert exit_code == 0
        return out_path.read_bytes()

    first = _run_once("a")
    second = _run_once("b")
    assert first == second
    assert len(first) > 200


def test_strategy_axis_controlled_survivor_moves_champion_and_appends_exactly_one_ledger_row(
    store, tmp_path, confluence_bar_store
):
    """An ISOLATED synthetic train + hold-out pair (never the shipped PG fixture) on which
    ``structure_tape`` legitimately beats ``v1`` on BOTH splits (the class-A breakthrough-long arm,
    with a test-LOCAL lowered promotion minimum -- the shipped default of 5 is never touched):
    promotes for real -- the pointer moves to ``{structure_tape, default}``, exactly one
    provenance-stamped ledger row is appended -- while ``default``/``v1``/every engine default stay
    byte-identical."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    holdout_meta = _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["candidate_id"] == STRATEGY_TAPE_ID
    # The win is asserted, not merely assumed (both R and $, on both splits).
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["survivor"] is True
    assert candidate["overfit"] is False

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == {"strategy_id": STRATEGY_TAPE_ID, "profile": PROFILE_DEFAULT}
    assert report["promotion"] == {
        "candidate_id": STRATEGY_TAPE_ID,
        "promoted": True,
        "enhancement_id": f"{STRATEGY_TAPE_ID}-over-{STRATEGY_V1_ID}-{PROFILE_DEFAULT}",
    }

    rows = store.list_pnl_ledger()
    assert len(rows) == 1
    row = rows[0].payload
    assert row["founding"] is False
    assert row["provenance"]["strategy_id"] == STRATEGY_TAPE_ID
    assert row["provenance"]["profile"] == PROFILE_DEFAULT
    assert row["provenance"]["train"]["dataset_id"] == train_meta["id"]
    assert row["provenance"]["holdout"]["dataset_id"] == holdout_meta["id"]

    # Frozen foundation AFTER a STRATEGY-axis promotion too: fingerprint unmoved.
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    # Single-source: the projection reflects the SAME moved pointer, verbatim.
    assert profiles_projection(store, test_config)["champion"] == report["champion_after"]


def test_strategy_axis_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append(
    store, tmp_path, confluence_bar_store
):
    """The SAME crash-safety guarantee as the profile axis (Key Test Scenario 4), reverting JUST
    the pointer after a real strategy-axis promotion and re-running -- must refuse explicitly, never
    silently re-promote (a second ledger row) or silently do nothing."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    first = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )
    assert first["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1

    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=0.0)

    with pytest.raises(ScanError, match="already exists"):
        run_sweep(
            store, dataset_store, test_config,
            candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
        )
    assert len(store.list_pnl_ledger()) == 1  # never a second row


def test_strategy_axis_min_n_gate_rejects_below_minimum_despite_positive_holdout(
    store, tmp_path, confluence_bar_store
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=2)  # candidate n=1 < 2

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_strategy_axis_min_n_gate_promotes_at_or_above_minimum(store, tmp_path, confluence_bar_store):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)  # candidate n=1 >= 1

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["survivor"] is True
    assert report["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1


def test_strategy_axis_overfit_is_positive_train_failing_holdout_and_is_never_promoted(
    store, tmp_path, confluence_bar_store
):
    """Train: ``structure_tape`` genuinely beats ``v1`` (the real class-A breakthrough win, over
    ``_CONFLUENCE_SYMBOL``, which HAS a recorded bar series). Hold-out: a DIFFERENT symbol with NO
    recorded bar series in the SAME bar store -- ``structure_tape`` honestly arms nothing there
    (n=0) while ``v1`` still profits on the identical underlying tape shape, so the hold-out delta
    is NEGATIVE. Positive train + a failed hold-out gate = ``overfit`` by the module's own
    definition -- and an overfit candidate is never promoted, whatever train looked like."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol="SYN-NO-LEVELS", split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 0  # no recorded levels for this symbol
    assert candidate["holdout"]["aggregate"]["delta_net_r"] < 0
    assert candidate["overfit"] is True
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_strategy_axis_more_than_one_dataset_per_split_skips_promotion_with_honest_note(
    store, tmp_path, confluence_bar_store
):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(  # a SECOND registered train dataset
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=30.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
    )

    (candidate,) = report["candidates"]
    assert len(candidate["train"]["datasets"]) == 2
    assert len(candidate["holdout"]["datasets"]) == 1
    assert candidate["survivor"] is True  # the hold-out gate itself still passes...
    assert report["promotion"]["promoted"] is False  # ...but promotion is explicitly skipped
    assert "2 train" in report["promotion"]["note"]
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_strategy_axis_unknown_candidate_strategy_id_is_an_explicit_refusal(store):
    """No new validation code exists for this -- ``BacktestJobManager.create`` stamps
    ``strategy_id`` verbatim, and ``BacktestRunner.run`` persists an unregistered id as an explicit
    ``failed`` record (never raises out), which ``_run_backtest``'s EXISTING status check turns
    into this same ``ScanError``. Never a coerced/fabricated comparison."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)

    with pytest.raises(ScanError):
        run_sweep(store, dataset_store, CONFIG, candidate_strategy_id="not-a-real-strategy")

    assert len(store.list_pnl_ledger()) == 0
    assert store.get_champion_pointer() == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
