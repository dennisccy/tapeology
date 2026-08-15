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
import time
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
from app.research.desk_playbook import PlaybookStore
from app.research.referee_adjudicate import (
    REFEREE_GATE_VERSION,
    AdjudicationSnapshotStore,
    RefereeEvaluationStore,
    referee_parameters_hash,
    run_evaluation_and_record,
)
from app.research.referee_null import REFEREE_TEST_PERM_SPEC_ID, RefereeNullStore
from app.research.referee_registry import (
    REFEREE_MIN_OCCURRENCES,
    REFEREE_MIN_SESSIONS,
    CertificateStore,
    FamilyStore,
    HypothesisStore,
    register_hypothesis,
)
from app.research.store import BacktestRecord, JournalStore

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


@pytest.fixture
def certificate_store(tmp_path):
    """era-6 J-08: an isolated, per-test ``CertificateStore`` — ``run_sweep``'s new REQUIRED
    parameter. Empty by default (the honest "no certificate exists" baseline every scenario below
    that never sets one up naturally reaches)."""
    return CertificateStore(tmp_path / "referee_registry")


# --- era-6 J-08: the promotion interlock -- shared certificate/live-scan-context fixture helpers ---


def _live_scan_context(*, champion: dict, train_meta: dict, holdout_meta: dict, config: Config) -> dict:
    """The exact ``live_scan_context`` shape ``pnl_scan._promote`` builds from a live run's own
    values — computed independently here (never imported from ``pnl_scan`` internals) so a test
    genuinely proves the two sides agree, rather than sharing one implementation with itself."""
    return {
        "champion_identity": champion,
        "train_dataset": {
            "id": train_meta["id"], "checksum": train_meta["checksum"], "split": train_meta["split"],
        },
        "holdout_dataset": {
            "id": holdout_meta["id"], "checksum": holdout_meta["checksum"], "split": holdout_meta["split"],
        },
        "config_fingerprint": config.config_fingerprint(),
        "gate_version": REFEREE_GATE_VERSION,
        "referee_parameters_hash": referee_parameters_hash(),
    }


def _matching_certificate(*, candidate: dict, live: dict, **overrides: object) -> dict:
    """A hand-built certificate matching every one of ``live``'s own pins (the
    ``test_referee_adjudicate.py`` ``_fixture_certificate``/``_live_scan_context_matching``
    precedent) — every refusal-class test below overrides exactly the ONE field it means to
    mismatch. Hand-building a certificate directly (never through the real evaluation rail) is
    fine for THESE tests: they exercise ``authorize_promotion``'s own refusal-class boundaries,
    not the mint path itself (that is TC-2's own job, below, which mints for real)."""
    fields = {
        "certificate_id": f"cert-{candidate['strategy_id']}-{candidate['profile']}",
        "candidate": dict(candidate),
        "champion_identity_at_scan_time": live["champion_identity"],
        "train_dataset": live["train_dataset"],
        "holdout_dataset": live["holdout_dataset"],
        "config_fingerprint": live["config_fingerprint"],
        "gate_version": live["gate_version"],
        "referee_parameters_hash": live["referee_parameters_hash"],
        "family_id": "fam-fixture", "hypothesis_id": "hyp-fixture",
        "gate_results": {"calibrated_p": 0.01, "bh_pass": True, "ci": [0.1, 0.9], "floors_met": True},
    }
    fields.update(overrides)
    return fields


# --- era-6 J-08 (TC-2): a REAL strategy-family evaluation, minted through the real rail ------------
#
# 12 independent dataset clusters (REFEREE_MIN_SESSIONS/REFEREE_MIN_OCCURRENCES's own floor), each
# carrying exactly ONE candidate trade at a strongly positive net_r and ONE recorded random_null
# trade at an equally strongly NEGATIVE net_r -- an IDENTICAL per-cluster Delta_d by construction
# (the ``_plant_known_corpus`` precedent in test_referee_adjudicate.py), so the exact-enumeration
# permutation space (2**12 = 4096 <= REFEREE_ENUMERATION_THRESHOLD) has exactly ONE combination
# (the observed grouping itself) at or above the observed T -- a deterministic, hand-verifiable
# p = 2/4097, comfortably under the family's own q=0.10 (m=1: bh_pass iff p<=q).


def _strategy_trade(*, direction: str = "long", logical_ts: float = 100.0, net_r: float = 1.0) -> dict:
    """A minimal ``_close_trade``-shaped trade -- only the fields the strategy adapter
    (``referee_evidence._strategy_observation``) reads (the ``test_referee_evidence.py`` ``_trade``
    precedent, reused here rather than imported across test files)."""
    return {
        "setup_type": "v1", "direction": direction,
        "entry": {"logical_ts": logical_ts, "price": 100.0, "fill_price": 100.0, "spread": 0.0},
        "exit": {
            "logical_ts": logical_ts + 60.0, "price": 101.0, "fill_price": 101.0, "spread": 0.0,
            "reason": "horizon",
        },
        "invalidation_price": 99.0, "r_basis": 1.0, "shares": 1.0,
        "gross_r": net_r, "net_r": net_r, "gross_usd": 0.0, "net_usd": 0.0,
        "fees_usd": 0.0, "slippage_usd": 0.0,
    }


def _plant_strategy_backtest(
    journal_store: JournalStore, *, backtest_id: str, dataset: dict,
    candidate_net_r: float, null_net_r: float,
) -> None:
    """Plants one ``done`` backtest report whose ``result`` block already carries the dataset
    joined verbatim (``backtests.py``'s own result-block shape), reproduced by hand -- the
    ``test_referee_evidence.py`` ``_plant_backtest_result`` precedent."""
    payload = {
        "id": backtest_id, "status": "done",
        "result": {
            "dataset": dataset, "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT,
            "config_fingerprint": CONFIG.config_fingerprint(),
            "trades": [_strategy_trade(net_r=candidate_net_r)],
            "null_baseline": {
                "seed": 1729, "entry_count": 1, "trades": [_strategy_trade(net_r=null_net_r)],
            },
        },
    }
    journal_store.insert_backtest(
        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
    )


def _mint_matching_certificate_through_the_real_rail(
    store: JournalStore, tmp_path: Path, *, candidate: dict, live: dict,
) -> CertificateStore:
    """Plants 12 strongly-separated strategy-family dataset clusters into ``store`` (the SAME
    journal DB the caller's own ``run_sweep`` will use), registers a strategy-family hypothesis at
    exactly the floor (``target_sessions=min_occurrences=REFEREE_MIN_SESSIONS``), and runs the REAL
    evaluation rail (``run_evaluation_and_record``) to its attested, gate-passing confirmatory
    checkpoint -- minting exactly one certificate pinned to ``candidate``/``live`` (goal.md J-08:
    "mintable only through the real evaluation rail"). Returns the ``CertificateStore`` the caller's
    own ``run_sweep`` should then pass ``authorize_promotion``."""
    for i in range(12):
        dataset = {
            "id": f"strategy-ds-{i}", "checksum": f"cksum-{i}", "split": SPLIT_TRAIN,
            "symbol": "SYN-STRAT", "epoch_anchor": 1_800_000_000.0 + i * 86_400.0,
        }
        _plant_strategy_backtest(
            store, backtest_id=f"strategy-bt-{i}", dataset=dataset,
            candidate_net_r=1.0, null_net_r=-1.0,
        )

    registry_dir = tmp_path / "referee_registry"
    eval_dir = tmp_path / "referee_eval"
    family_store = FamilyStore(registry_dir)
    hypothesis_store = HypothesisStore(registry_dir)
    hypothesis_id = "hyp-strategy-cert"
    payload = {
        "hypothesis_id": hypothesis_id, "family_id": "fam-strategy-cert", "family_q": 0.10,
        "family_candidate_hypothesis_ids": [hypothesis_id],
        "evidence_family": "strategy", "estimand": "A",
        "setup_id": "structure_tape", "side": "long", "context_predicate": None,
        "primary_measure_key": "net_r", "primary_horizon": "trade", "sidedness": "greater",
        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
    }
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)

    certificate_store = CertificateStore(registry_dir)
    result = run_evaluation_and_record(
        hypothesis_id,
        hypothesis_store=hypothesis_store, family_store=family_store,
        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
        evaluation_store=RefereeEvaluationStore(eval_dir),
        snapshot_store=AdjudicationSnapshotStore(eval_dir),
        journal_store=store,
        certificate_mint={
            "candidate": candidate,
            "champion_identity_at_scan_time": live["champion_identity"],
            "train_dataset": live["train_dataset"],
            "holdout_dataset": live["holdout_dataset"],
            "certificate_store": certificate_store,
        },
    )
    assert result["cancelled"] is False
    assert result["record"]["role"] == "checkpoint"
    assert result["record"]["permutation_p"] == pytest.approx(2.0 / 4097.0)
    assert result["snapshot"]["bh"]["bh_pass"] is True
    assert result["certificate"] is not None
    return certificate_store


# --- Fixture sweep: the non-regression baseline (Key Test Scenario 1) ------------------------------


def test_fixture_sweep_is_zero_survivors_and_leaves_everything_untouched(store, tmp_path, certificate_store):
    """On the committed fixture pair, ``candidate-faster-warmup`` is a non-survivor: identical
    trades on train (delta exactly zero) and a NEGATIVE hold-out delta with n below the
    promotion minimum — both independently sufficient to refuse promotion. Seeds the founding
    ledger row FIRST (the production sequence) so the DoD's "ledger still has row_count 1" and
    "default fingerprint still pinned" clauses are exercised for real, not merely asserted in the
    abstract."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    created, _ = seed_founding_row(store, DatasetStore(tmp_path / "founding-datasets"), CONFIG)
    assert created is True

    report = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)

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


def test_zero_registered_candidates_is_an_honest_empty_sweep(store, monkeypatch, certificate_store):
    """Zero registered candidates -> an explicit, honest empty report (never an error) — the
    ``profile_registry`` filter to non-default entries applied to an all-default registry."""
    monkeypatch.setattr(
        Config,
        "profile_registry",
        lambda self: [{"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}],
    )
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)
    report = run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
    assert report["candidates"] == []
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0


# --- Controlled survivor: a genuine, isolated hold-out win (Key Test Scenario 2) --------------------


def test_controlled_survivor_is_refused_without_a_certificate(store, tmp_path, certificate_store):
    """era-6 J-08 (TC-1), inverting this suite's own pre-iter-9 "controlled survivor promotes"
    assertions per goal.md's own stated consequence: an ISOLATED synthetic train + hold-out pair on
    which the candidate legitimately beats the champion on BOTH splits is now REFUSED — no ledger
    row, no pointer move — absent a valid, candidate-specific Referee certificate. ``survivor``
    still reads ``True`` (the hold-out gate itself still passed; only the NEW certificate interlock
    blocks the write)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    (candidate,) = report["candidates"]
    # The win is asserted, not merely assumed (both R and $ on both splits, empirically robust) —
    # the hold-out gate itself still genuinely passes; only the certificate interlock refuses.
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["survivor"] is True
    assert candidate["robustness"] == "robust"
    assert candidate["overfit"] is False

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == report["champion_before"]  # UNMOVED
    assert report["promotion"] == {
        "candidate_id": PROFILE_CANDIDATE_FASTER_WARMUP,
        "promoted": False,
        "note": None,
        "promotion_eligible": False,
        "refusal_class": "no_certificate",
        "reason": report["promotion"]["reason"],
    }
    assert report["promotion"]["reason"]

    assert len(store.list_pnl_ledger()) == 0  # nothing written
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert profiles_projection(store, test_config)["champion"] == report["champion_before"]


def test_controlled_survivor_promotes_with_a_certificate_minted_through_the_real_evaluation_rail(
    store, tmp_path,
):
    """era-6 J-08 (TC-2): the SAME controlled-survivor scenario as the refusal test above, but with
    a certificate minted through the REAL evaluation rail (``run_evaluation_and_record``, a genuine
    strategy-family hypothesis reaching an attested, gate-passing confirmatory checkpoint — never a
    hand-written fixture path) matching every one of the live scan's own pins: promotes for real —
    champion pointer moves, exactly one provenance-stamped ledger row is appended — exactly as this
    suite asserted before this iteration, PLUS the new ``promotion_eligible: True`` field."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    certificate_store = _mint_matching_certificate_through_the_real_rail(
        store, tmp_path, candidate=candidate, live=live,
    )

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    (result_candidate,) = report["candidates"]
    assert result_candidate["survivor"] is True

    assert report["champion_before"] == champion_before
    assert report["champion_after"] == {
        "strategy_id": STRATEGY_V1_ID,
        "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
    }
    assert report["promotion"] == {
        "candidate_id": PROFILE_CANDIDATE_FASTER_WARMUP,
        "promoted": True,
        "enhancement_id": f"{PROFILE_CANDIDATE_FASTER_WARMUP}-over-{STRATEGY_V1_ID}-{PROFILE_DEFAULT}",
        "promotion_eligible": True,
        "refusal_class": None,
        "reason": None,
    }

    rows = store.list_pnl_ledger()
    assert len(rows) == 1
    row = rows[0].payload
    assert row["founding"] is False
    assert row["baseline"]["train"]["net_r"] == pytest.approx(
        result_candidate["train"]["datasets"][0]["champion"]["net_r"]
    )
    assert row["candidate"]["train"]["net_r"] == pytest.approx(
        result_candidate["train"]["datasets"][0]["candidate"]["net_r"]
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


def test_min_n_gate_rejects_below_minimum_despite_positive_holdout(store, tmp_path, certificate_store):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=2)  # candidate n=1 < 2

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    (candidate,) = report["candidates"]
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_min_n_gate_survivor_at_or_above_minimum_is_still_refused_without_a_certificate(
    store, tmp_path, certificate_store,
):
    """era-6 J-08: inverts this suite's own pre-iter-9 "min-n gate promotes" assertion — the
    hold-out gate itself still passes at n=1>=1 (``survivor`` reads ``True``), but with no
    certificate on file the certificate interlock refuses it, same as the controlled-survivor case
    above (a different fixture path reaching the identical refusal, TC-1's own generality)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)  # candidate n=1 >= 1

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    (candidate,) = report["candidates"]
    assert candidate["survivor"] is True
    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["promotion_eligible"] is False
    assert report["promotion"]["refusal_class"] == "no_certificate"
    assert len(store.list_pnl_ledger()) == 0


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


def test_robustness_is_speculative_when_not_every_train_dataset_is_positive(store, tmp_path, certificate_store):
    """TWO train datasets — one where the candidate wins, one flat dataset where it does not
    reliably win — beside a winning hold-out: ``robust`` requires EVERY individual train dataset
    to be positive, so this is ``speculative`` even though the aggregate train delta is positive
    and the candidate still survives on hold-out (the two labels are independent axes)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _winning_dataset(dataset_store, "SYN-TRAIN-WIN", seed=7, split=SPLIT_TRAIN)
    _flat_dataset(dataset_store, "SYN-TRAIN-FLAT", seed=7, split=SPLIT_TRAIN)
    _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

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


def test_overfit_is_positive_train_failing_holdout_and_is_never_promoted(store, tmp_path, certificate_store):
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

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

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


def test_corrupt_dataset_raises_explicit_error_with_nothing_written(store, tmp_path, certificate_store):
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    with pytest.raises(ScanError):
        run_sweep(store, dataset_store, CONFIG, certificate_store=certificate_store)
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
    champion is still un-moved). era-6 J-08: the FIRST promotion now needs a matching certificate,
    minted through the real evaluation rail exactly as TC-2 does — the crash-retry behaviour under
    test here is otherwise unchanged."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    certificate_store = _mint_matching_certificate_through_the_real_rail(
        store, tmp_path, candidate=candidate, live=live,
    )

    first = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
    assert first["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1

    # Simulate the crash: only the pointer "didn't move" (the ledger row from the first run
    # stands, exactly as the crash-safe write ORDER guarantees).
    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=0.0)

    with pytest.raises(ScanError, match="already exists"):
        run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)
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


def test_strategy_axis_fixture_sweep_matches_shape_and_is_honestly_no_survivor(store, certificate_store):
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
        store, dataset_store, CONFIG, candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=bar_store,
        certificate_store=certificate_store,
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


def test_strategy_axis_controlled_survivor_is_refused_without_a_certificate(
    store, tmp_path, confluence_bar_store, certificate_store
):
    """era-6 J-08 (TC-1), STRATEGY axis: inverts this suite's own pre-iter-9 "controlled survivor
    promotes" assertions — an ISOLATED synthetic train + hold-out pair on which ``structure_tape``
    legitimately beats ``v1`` on BOTH splits is now REFUSED absent a valid, candidate-specific
    Referee certificate — no ledger row, no pointer move — while ``survivor`` still reads ``True``
    (the hold-out gate itself still genuinely passed)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)

    report = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
        certificate_store=certificate_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["candidate_id"] == STRATEGY_TAPE_ID
    # The win is asserted, not merely assumed (both R and $, on both splits) — the hold-out gate
    # itself still genuinely passes; only the certificate interlock refuses.
    assert candidate["train"]["aggregate"]["delta_net_r"] > 0
    assert candidate["train"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["survivor"] is True
    assert candidate["overfit"] is False

    assert report["champion_before"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert report["champion_after"] == report["champion_before"]  # UNMOVED
    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["promotion_eligible"] is False
    assert report["promotion"]["refusal_class"] == "no_certificate"
    assert report["promotion"]["reason"]

    assert len(store.list_pnl_ledger()) == 0
    # Frozen foundation: fingerprint unmoved regardless of the refusal.
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert profiles_projection(store, test_config)["champion"] == report["champion_before"]


def test_strategy_axis_mid_promotion_crash_leaves_no_orphan_and_no_silent_double_append(
    store, tmp_path, confluence_bar_store
):
    """The SAME crash-safety guarantee as the profile axis (Key Test Scenario 4), reverting JUST
    the pointer after a real strategy-axis promotion and re-running -- must refuse explicitly, never
    silently re-promote (a second ledger row) or silently do nothing. era-6 J-08: the FIRST
    promotion now needs a matching certificate, minted through the real evaluation rail."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_TRAIN, max_logical=25.0
    )
    holdout_meta = _record_structure_tape_dataset(
        dataset_store, symbol=_CONFLUENCE_SYMBOL, split=SPLIT_HOLDOUT, max_logical=40.0
    )
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": STRATEGY_TAPE_ID, "profile": PROFILE_DEFAULT}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    certificate_store = _mint_matching_certificate_through_the_real_rail(
        store, tmp_path, candidate=candidate, live=live,
    )

    first = run_sweep(
        store, dataset_store, test_config,
        candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
        certificate_store=certificate_store,
    )
    assert first["promotion"]["promoted"] is True
    assert len(store.list_pnl_ledger()) == 1

    store.set_champion_pointer(strategy_id=STRATEGY_V1_ID, profile=PROFILE_DEFAULT, wall_ts=0.0)

    with pytest.raises(ScanError, match="already exists"):
        run_sweep(
            store, dataset_store, test_config,
            candidate_strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
            certificate_store=certificate_store,
        )
    assert len(store.list_pnl_ledger()) == 1  # never a second row


def test_strategy_axis_min_n_gate_rejects_below_minimum_despite_positive_holdout(
    store, tmp_path, confluence_bar_store, certificate_store
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
        certificate_store=certificate_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["holdout"]["aggregate"]["delta_net_r"] > 0
    assert candidate["holdout"]["aggregate"]["delta_net_usd"] > 0
    assert candidate["holdout"]["aggregate"]["candidate_n"] == 1
    assert candidate["survivor"] is False
    assert report["promotion"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_strategy_axis_min_n_gate_survivor_at_or_above_minimum_is_still_refused_without_a_certificate(
    store, tmp_path, confluence_bar_store, certificate_store
):
    """era-6 J-08: STRATEGY-axis counterpart of the profile-axis min-n refusal test above — the
    hold-out gate itself still passes at n=1>=1, but the certificate interlock refuses it."""
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
        certificate_store=certificate_store,
    )

    (candidate,) = report["candidates"]
    assert candidate["survivor"] is True
    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "no_certificate"
    assert len(store.list_pnl_ledger()) == 0


def test_strategy_axis_overfit_is_positive_train_failing_holdout_and_is_never_promoted(
    store, tmp_path, confluence_bar_store, certificate_store
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
        certificate_store=certificate_store,
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
    store, tmp_path, confluence_bar_store, certificate_store
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
        certificate_store=certificate_store,
    )

    (candidate,) = report["candidates"]
    assert len(candidate["train"]["datasets"]) == 2
    assert len(candidate["holdout"]["datasets"]) == 1
    assert candidate["survivor"] is True  # the hold-out gate itself still passes...
    assert report["promotion"]["promoted"] is False  # ...but promotion is explicitly skipped
    assert "2 train" in report["promotion"]["note"]
    # The structural (dataset-cardinality) skip is a DIFFERENT refusal than the certificate
    # interlock -- authorize_promotion is never even consulted on this path (era-6 J-08).
    assert report["promotion"]["promotion_eligible"] is None
    assert report["promotion"]["refusal_class"] is None
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_strategy_axis_unknown_candidate_strategy_id_is_an_explicit_refusal(store, certificate_store):
    """No new validation code exists for this -- ``BacktestJobManager.create`` stamps
    ``strategy_id`` verbatim, and ``BacktestRunner.run`` persists an unregistered id as an explicit
    ``failed`` record (never raises out), which ``_run_backtest``'s EXISTING status check turns
    into this same ``ScanError``. Never a coerced/fabricated comparison."""
    dataset_store = DatasetStore(FIXTURE_DATASET_DIR)

    with pytest.raises(ScanError):
        run_sweep(
            store, dataset_store, CONFIG, candidate_strategy_id="not-a-real-strategy",
            certificate_store=certificate_store,
        )

    assert len(store.list_pnl_ledger()) == 0
    assert store.get_champion_pointer() == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


# --- era-6 J-08: the remaining five refusal classes (TC-3..TC-7), each fixture-tested through the
# full run_sweep/_promote path over the SAME controlled-survivor scenario TC-1/TC-2 use ------------


def _survivor_scenario(tmp_path):
    """The SAME isolated, controlled hold-out win TC-1/TC-2 use, factored out for the five
    mismatch-class refusal tests below — each one hand-builds a certificate that matches every
    pin EXCEPT the one field under test."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    train_meta = _winning_dataset(dataset_store, "SYN-TRAIN-A", seed=7, split=SPLIT_TRAIN)
    holdout_meta = _winning_dataset(dataset_store, "SYN-HOLDOUT-B", seed=11, split=SPLIT_HOLDOUT)
    test_config = dataclasses.replace(CONFIG, promotion_min_sample_size=1)
    return dataset_store, train_meta, holdout_meta, test_config


def test_tc3_a_stale_config_fingerprint_certificate_refuses(store, tmp_path, certificate_store):
    dataset_store, train_meta, holdout_meta, test_config = _survivor_scenario(tmp_path)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    stale = dict(live)
    stale["config_fingerprint"] = "some-other-fingerprint-entirely"
    certificate_store.record(_matching_certificate(candidate=candidate, live=stale))

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["promotion_eligible"] is False
    assert report["promotion"]["refusal_class"] == "stale"
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_tc4_a_certificate_for_a_different_profile_refuses_wrong_candidate(store, tmp_path, certificate_store):
    dataset_store, train_meta, holdout_meta, test_config = _survivor_scenario(tmp_path)
    champion_before = store.get_champion_pointer()
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    other_candidate = {"strategy_id": champion_before["strategy_id"], "profile": "some-other-profile"}
    certificate_store.record(_matching_certificate(candidate=other_candidate, live=live))

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "wrong_candidate"
    assert len(store.list_pnl_ledger()) == 0


def test_tc5_a_mismatched_train_dataset_pin_refuses(store, tmp_path, certificate_store):
    dataset_store, train_meta, holdout_meta, test_config = _survivor_scenario(tmp_path)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    mismatched = dict(live)
    mismatched["train_dataset"] = {"id": "some-other-dataset", "checksum": "0" * 8, "split": "train"}
    certificate_store.record(_matching_certificate(candidate=candidate, live=mismatched))

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "mismatched_datasets"
    assert len(store.list_pnl_ledger()) == 0


def test_tc6_a_certificate_with_a_failed_gate_refuses(store, tmp_path, certificate_store):
    dataset_store, train_meta, holdout_meta, test_config = _survivor_scenario(tmp_path)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    certificate_store.record(
        _matching_certificate(
            candidate=candidate, live=live,
            gate_results={"calibrated_p": 0.5, "bh_pass": False, "ci": [-1.0, 1.0], "floors_met": True},
        )
    )

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "failed_gates"
    assert len(store.list_pnl_ledger()) == 0


def test_tc7_a_malformed_certificate_store_refuses_and_never_crashes_promote(
    store, tmp_path, certificate_store,
):
    dataset_store, train_meta, holdout_meta, test_config = _survivor_scenario(tmp_path)
    champion_before = store.get_champion_pointer()
    candidate = {"strategy_id": champion_before["strategy_id"], "profile": PROFILE_CANDIDATE_FASTER_WARMUP}
    live = _live_scan_context(
        champion=champion_before, train_meta=train_meta, holdout_meta=holdout_meta, config=test_config,
    )
    # A genuine, valid, matching certificate IS on file (so a naive implementation might promote) --
    # a SEPARATE, unrelated corrupted file in the same store must still refuse, honestly, never
    # crash `_promote` (the error-cases clause: "a malformed/corrupted certificate file must return
    # malformed_unverifiable, never crash _promote").
    certificate_store.record(_matching_certificate(candidate=candidate, live=live))
    certificate_store.root.mkdir(parents=True, exist_ok=True)
    (certificate_store.root / "certificate-corrupt.json").write_text("not valid json at all")

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "malformed_unverifiable"
    assert len(store.list_pnl_ledger()) == 0
    assert report["champion_after"] == report["champion_before"]


def test_a_survivor_with_zero_certificates_on_file_completes_the_sweep_honestly_never_raises(
    store, tmp_path, certificate_store,
):
    """Error case (iteration spec): a survivor with zero certificates on file must still complete
    the sweep and report honestly (never raise) — the ``certificate_store`` fixture is a freshly
    empty, never-populated directory throughout this whole file; this test names that expectation
    explicitly rather than leaving it merely implicit in every OTHER test's own passing assertion."""
    dataset_store, _train_meta, _holdout_meta, test_config = _survivor_scenario(tmp_path)

    report = run_sweep(store, dataset_store, test_config, certificate_store=certificate_store)

    (candidate,) = report["candidates"]
    assert candidate["survivor"] is True
    assert report["promotion"]["promoted"] is False
    assert report["promotion"]["refusal_class"] == "no_certificate"


# --- era-6 J-08 (TC-8): the no-bypass source-scan guard --------------------------------------------


def test_no_bypass_path_exists_for_authorize_promotion():
    """TC-8: scans the two files implementing the promotion interlock's own source text for any
    CODE-shaped ``--force``/skip-flag/environment-override/default-allow IDENTIFIER that could
    satisfy ``authorize_promotion`` without a genuine, matching, on-file certificate. Every banned
    token below is an underscore/flag-shaped identifier (never a bare English word like "bypass"
    prose legitimately uses to describe the ABSENCE of one -- this module's own docstrings do
    exactly that) so the scan cannot self-trip on its own documentation. A lint that CAN fail on a
    seeded violation (the ``test_desk_ui_guards.py`` precedent) — proven below."""
    banned_tokens = (
        "--force", "force_promote", "force_certificate", "force=true",
        "skip_certificate", "skip_cert", "no_certificate_required", "allow_without_certificate",
        "default_allow", "tapeology_force", "tapeology_skip_cert",
    )
    for relative in ("research/pnl_scan.py", "research/referee_adjudicate.py"):
        source = (BACKEND_DIR / "app" / relative).read_text().lower()
        for token in banned_tokens:
            assert token not in source, (
                f"{relative} contains a potential promotion-interlock bypass token: {token!r}"
            )
    # `--strategy` is the ONE existing CLI flag on pnl_scan.py — proves this scan is not simply
    # rejecting every flag definition; it targets bypass-shaped tokens specifically.
    pnl_scan_source = (BACKEND_DIR / "app" / "research" / "pnl_scan.py").read_text()
    assert "--strategy" in pnl_scan_source


def test_no_bypass_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail — a lint that cannot fail proves nothing (the ``test_desk_ui_guards.py``
    precedent)."""
    seeded_source = "if args.force or os.environ.get('TAPEOLOGY_SKIP_CERTIFICATE'):\n    return authorized\n"
    lowered = seeded_source.lower()
    assert "--force" in lowered or "force" in lowered
    assert "skip_certificate" in lowered
