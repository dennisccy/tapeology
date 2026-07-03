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
    STRATEGY_V1_ID,
)
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import pnl_scan
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, record_from_source
from app.research.pnl_baseline import seed_founding_row
from app.research.pnl_scan import ScanError, run_sweep
from app.research.profiles import profiles_projection
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
# The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's
# ``test_committed_fixture_pair_backtests_keyless_end_to_end`` uses) — the keyless CI substrate.
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"

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
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
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
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"

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
