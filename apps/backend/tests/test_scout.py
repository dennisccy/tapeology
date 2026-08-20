"""``scout.py`` (Era "The Rapid Microscope" J-04) -- the Scout screening engine. Test-first

contract: TC-5, TC-6, TC-7, TC-8, TC-10, TC-11, TC-12 in
``docs/phases/goal-rapid-microscope-iter-4.md`` (TC-1/TC-2/TC-3/TC-4/TC-9/TC-13 live in
``test_scout_ledger.py`` -- see that file's own module docstring for the split rationale). Also
covers the pure statistical core (membership, effect, the block-permutation null, every decision
branch) and ``extract_anchors`` directly, over hand-built synthetic anchor lists and the real
committed fixture snapshots respectively -- the "hand-derived oracle fixture" testing style this
codebase uses throughout (``test_micro_features.py``'s own precedent)."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_join as mj
from app.research import scout, scout_ledger
from app.research.datasets import DatasetStore, parse_utc_epoch
from app.research.desk_playbook import PlaybookStore, playbook_parameters
from app.research.desk_playbook_context import BandMapResolver
from app.research.micro_routes import (
    get_scout_compute_manager,
    get_scout_ledger_dir,
)
from app.research.micro_snapshots import (
    resolve_micro_snapshots_dir,
    run_snapshot_build_and_record,
)
from app.research.routes import get_dataset_store
from app.research.micro_routes import get_micro_snapshots_dir
from app.research.tradability_cache import TradabilityCache

_FIXTURE_DIRS = [
    Path(__file__).resolve().parent / "fixtures" / "datasets",
    Path(__file__).resolve().parent / "fixtures" / "datasets_j03",
]

_ECON_FLOOR_TINY = {
    "multiple": 1.0, "family_median_spread_bps": 0.001, "floor_bps": 0.001,
    "proxy_sentence": scout.ECON_PROXY_SENTENCE,
}


def _combined_fixture_store(tmp_path: Path) -> DatasetStore:
    target = tmp_path / "datasets"
    target.mkdir()
    for fixture_dir in _FIXTURE_DIRS:
        for path in fixture_dir.glob("*.json"):
            shutil.copy(path, target / path.name)
    return DatasetStore(target)


# === TC-5 / TC-6: TR-8 calibration + the banned-shuffle counter-test ================================


def _autocorrelated_null_anchors(meta_seed: int, n_sessions: int = 15, n_per_session: int = 60) -> list[dict]:
    """A synthetic, session-clustered, autocorrelated KNOWN-NULL corpus (no true feature-outcome
    relationship): both the feature and the outcome are AR(1)-like within-session random walks,
    so nearby anchors are genuinely correlated -- exactly the structure a plain per-anchor label
    shuffle destroys and a block rotation preserves (module docstring, ``scout.py``'s own)."""
    import random

    rng = random.Random(f"tr8-calibration-fixture:{meta_seed}")
    anchors: list[dict] = []
    for s in range(n_sessions):
        session_date = f"2026-06-{s + 1:02d}"
        outcome = 0.0
        feature = 0.0
        for _ in range(n_per_session):
            outcome = 0.7 * outcome + rng.gauss(0.0, 1.0)
            feature = 0.6 * feature + rng.gauss(0.0, 1.0)
            anchors.append(
                {
                    "session_date": session_date, "symbol": "PG", "feature_value": feature,
                    "outcome_value": outcome, "tod_bucket": "mid", "fallback_frac": rng.random(),
                }
            )
    return anchors


_TR8_SEEDS = 200
_TR8_BLOCK_LENGTH = 20
_TR8_TRANSFORM = "threshold"
_TR8_PARAMS = {"op": "ge", "value": 0.0}


def test_tc5_tr8_block_permutation_pass_rate_holds_the_calibration_ceiling():
    """TR-8: on the autocorrelated known-null fixture across 200 seeds, the block-permutation
    screen's observed pass rate is <= 1.5 x SCOUT_SCREEN_ALPHA (0.075)."""
    n_pass = 0
    for meta_seed in range(_TR8_SEEDS):
        anchors = _autocorrelated_null_anchors(meta_seed)
        _effect, p_screen = scout.compute_p_screen(
            anchors, transform=_TR8_TRANSFORM, params=_TR8_PARAMS,
            seed_scope=f"tr8-calib-{meta_seed}", block_length=_TR8_BLOCK_LENGTH, shuffle="block",
        )
        if p_screen is not None and p_screen < scout.SCOUT_SCREEN_ALPHA:
            n_pass += 1
    pass_rate = n_pass / _TR8_SEEDS
    assert pass_rate <= 1.5 * scout.SCOUT_SCREEN_ALPHA, (
        f"block-permutation pass rate {pass_rate} exceeds the TR-8 calibration ceiling "
        f"{1.5 * scout.SCOUT_SCREEN_ALPHA}"
    )


def test_tc6_the_banned_plain_shuffle_null_demonstrably_exceeds_the_calibration_ceiling():
    """TR-8's own counter-test: substituting the BANNED plain per-anchor shuffle (test-only path,
    ``scout._plain_shuffle_null_deltas`` -- never reachable from production) for the block null,
    over the IDENTICAL fixture and seeds, produces a pass rate that exceeds the ceiling -- proving
    the block design is not a vacuous pass (it fixes a real, demonstrable anti-conservative
    failure), the same evidence TC-5 alone could never provide."""
    n_pass = 0
    for meta_seed in range(_TR8_SEEDS):
        anchors = _autocorrelated_null_anchors(meta_seed)
        _effect, p_screen = scout.compute_p_screen(
            anchors, transform=_TR8_TRANSFORM, params=_TR8_PARAMS,
            seed_scope=f"tr8-calib-{meta_seed}", block_length=_TR8_BLOCK_LENGTH, shuffle="plain",
        )
        if p_screen is not None and p_screen < scout.SCOUT_SCREEN_ALPHA:
            n_pass += 1
    pass_rate = n_pass / _TR8_SEEDS
    assert pass_rate > 1.5 * scout.SCOUT_SCREEN_ALPHA, (
        f"the banned plain-shuffle null's pass rate {pass_rate} should EXCEED the calibration "
        f"ceiling {1.5 * scout.SCOUT_SCREEN_ALPHA} -- demonstrating the anti-conservative failure "
        "the block design exists to fix"
    )


def test_the_banned_plain_shuffle_null_is_never_imported_or_called_by_a_production_path():
    """A source-level guard (the spec's own "never reachable from a production call path"):
    neither ``screen_candidate`` nor ``register_and_screen_candidate`` names the banned function
    anywhere in their own source. A lint that can fail proves something -- the SAME assertion
    against a source string that DOES contain the name is checked first."""
    import inspect

    assert "_plain_shuffle_null_deltas" in inspect.getsource(scout._null_effect_draws)  # the ONE
    # legitimate caller, gated behind shuffle="plain" (test-only)

    production_source = inspect.getsource(scout.screen_candidate) + inspect.getsource(
        scout.register_and_screen_candidate
    )
    assert "_plain_shuffle_null_deltas" not in production_source


# === TC-7 / TR-9: registration-ordering refusal =====================================================


@pytest.fixture
def snapshot_ready_store(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    records, _errors = store.list()
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]
    return store, snapshots_dir, manifest


def test_tc7_econ_floor_computed_after_registered_at_is_refused(tmp_path, snapshot_ready_store):
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")

    with pytest.raises(scout.ScoutRegistrationOrderingError):
        scout.register_and_screen_candidate(
            ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
            structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest,
            grid_version=1, registered_at="2026-01-01T00:00:00Z",
            econ_floor_computed_at="2026-01-02T00:00:00Z", family_median_spread_bps=1.0,
        )
    assert ledger.all_rows() == []  # no ledger row is written for it


def test_tc7_econ_floor_computed_at_or_before_registered_at_is_accepted(tmp_path, snapshot_ready_store):
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")

    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest,
        grid_version=1, registered_at="2026-01-02T00:00:00Z",
        econ_floor_computed_at="2026-01-01T00:00:00Z", family_median_spread_bps=1.0,
    )
    assert row["decision"] in scout_ledger.CLOSED_DECISIONS


def test_tc7_a_normal_registration_never_violates_ordering_by_construction(tmp_path, snapshot_ready_store):
    """The production path (no explicit timestamps -- the default flow every grid entry uses)
    always stamps ``econ_floor_computed_at <= registered_at``, so it can never trip TR-9 itself."""
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest, grid_version=1,
    )
    from app.research.datasets import parse_utc_epoch

    assert parse_utc_epoch(row["econ_floor_computed_at"]) <= parse_utc_epoch(row["registered_at"])


# === TC-8 / TR-10: pool invariance ====================================================================


def test_tc8_screen_candidate_decision_is_unaffected_by_n_variants_tried():
    """The PURE-function proof: ``screen_candidate`` never reads sibling candidates' data at all --
    ``n_variants_tried`` feeds only the best-of-N DISCLOSURE (spec section 5.4: "a disclosure,
    never a decision rule"), never the decision/effect/p_screen themselves."""
    anchors = _autocorrelated_null_anchors(meta_seed=0)
    small_n = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="pool-invariance", n_variants_tried=5,
    )
    large_n = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="pool-invariance", n_variants_tried=105,
    )
    assert small_n["decision"] == large_n["decision"]
    assert small_n["reason"] == large_n["reason"]
    assert small_n["notes"] == large_n["notes"]
    assert small_n["screen_result"]["effect_bps"] == large_n["screen_result"]["effect_bps"]
    assert small_n["screen_result"]["p_screen"] == large_n["screen_result"]["p_screen"]
    # only the best-of-N disclosure differs -- N moved, nothing else did
    assert small_n["screen_result"]["best_of_n_disclosure"]["n"] == 5
    assert large_n["screen_result"]["best_of_n_disclosure"]["n"] == 105


def test_tc8_registering_100_more_candidates_never_rewrites_an_earlier_familys_ledgered_rows(
    tmp_path, snapshot_ready_store
):
    """The LEDGER-level proof: register a few real candidates for family X, capture their rows
    verbatim, then append 100 additional null rows to a DIFFERENT family at "that same origin"
    (the SAME ledger file/store) -- family X's own rows, re-read, are byte-identical (append-only
    immutability, mechanically)."""
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")

    original_rows = []
    for feature_name in ("cumulative_delta", "rolling_imbalance_20t"):
        row = scout.register_and_screen_candidate(
            ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            feature_name=feature_name, transform="threshold", params={"op": "ge", "value": 0.0},
            structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest,
            grid_version=1,
        )
        original_rows.append(row)

    other_family = "a-different-family-100-null-additions"
    for i in range(100):
        ledger.append_row({"family_id": other_family, "grid_version": 1, "decision": "killed_null"})
    assert ledger.variants_tried_for_family(other_family) == 100

    for original in original_rows:
        rows_now = ledger.rows_for_family(original["family_id"])
        reread = next(r for r in rows_now if r["candidate_id"] == original["candidate_id"])
        assert reread == original  # byte-identical -- fitted decision never shifts


# === compute_p_screen / screen_candidate: the closed-vocabulary decision branches ==================


def _planted_effect_anchors(n_sessions=6, n_per_session=20, effect=3.0, seed=1):
    import random

    rng = random.Random(f"planted:{seed}")
    anchors = []
    for s in range(n_sessions):
        session_date = f"2026-07-{s + 1:02d}"
        for _ in range(n_per_session):
            feature_value = rng.gauss(0.0, 1.0)
            is_cand = feature_value >= 0.0
            outcome = rng.gauss(effect if is_cand else 0.0, 1.0)
            anchors.append(
                {
                    "session_date": session_date, "symbol": "PG", "feature_value": feature_value,
                    "outcome_value": outcome, "tod_bucket": "mid", "fallback_frac": rng.random(),
                }
            )
    return anchors


def test_screen_candidate_survives_a_genuine_planted_effect():
    anchors = _planted_effect_anchors()
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="buy", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="survive-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "survive"
    assert result["reason"] == "survive"
    assert result["screen_result"]["p_screen"] < scout.SCOUT_SCREEN_ALPHA
    assert result["screen_result"]["effect_bps"] > 0
    assert result["screen_result"]["econ_interesting"] is True


def test_screen_candidate_kills_null_on_an_unrelated_feature():
    import random

    rng = random.Random("null-feature-fixture")
    anchors = []
    for s in range(6):
        session_date = f"2026-08-{s + 1:02d}"
        for _ in range(20):
            anchors.append(
                {
                    "session_date": session_date, "symbol": "PG", "feature_value": rng.gauss(0, 1),
                    "outcome_value": rng.gauss(0, 1), "tod_bucket": "mid", "fallback_frac": rng.random(),
                }
            )
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="null-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_null"
    assert result["screen_result"]["p_screen"] >= scout.SCOUT_SCREEN_ALPHA


def test_screen_candidate_kills_direction_on_a_wrong_signed_effect():
    anchors = _planted_effect_anchors()
    flipped = [{**a, "outcome_value": -a["outcome_value"]} for a in anchors]
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="buy", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=flipped,
        family_id="direction-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_direction"
    assert result["screen_result"]["effect_bps"] < 0


def test_screen_candidate_kills_economic_below_the_floor():
    anchors = _planted_effect_anchors()
    huge_floor = {
        "multiple": 1.0, "family_median_spread_bps": 1000.0, "floor_bps": 1000.0,
        "proxy_sentence": scout.ECON_PROXY_SENTENCE,
    }
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="buy", horizon_key="trades_20", econ_floor=huge_floor, anchors=anchors,
        family_id="economic-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_economic"
    assert result["screen_result"]["econ_interesting"] is False


def test_screen_candidate_kills_concentration_when_the_effect_is_symbol_skewed():
    import random

    rng = random.Random("concentration-fixture")
    anchors = []
    for s in range(6):
        session_date = f"2026-09-{s + 1:02d}"
        for _ in range(20):
            feature_value = rng.gauss(0.0, 1.0)
            is_cand = feature_value >= 0.0
            outcome = rng.gauss(3.0 if is_cand else 0.0, 1.0)
            symbol = "AAA" if (not is_cand or rng.random() < 0.9) else "BBB"
            anchors.append(
                {
                    "session_date": session_date, "symbol": symbol, "feature_value": feature_value,
                    "outcome_value": outcome, "tod_bucket": "mid", "fallback_frac": rng.random(),
                }
            )
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="buy", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="concentration-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_concentration"
    assert result["screen_result"]["concentration"]["top1_symbol_share"] > scout.SCOUT_MAX_TOP1_CONCENTRATION


def test_screen_candidate_kills_insufficient_n_on_a_single_session():
    anchors = [a for a in _planted_effect_anchors() if a["session_date"] == "2026-07-01"]
    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness=None, horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="insufficient-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_insufficient_n"


def test_screen_candidate_kills_fragile_when_the_sign_depends_on_one_dominant_session(monkeypatch):
    """``_fragile_leave_one_session_out`` only ever gets a chance to fire once statistical
    significance, direction, concentration, and the economic floor have ALL already passed --
    reaching it "naturally" through the block-permutation null needs a fixture with a genuinely
    tiny p-value AND a session-count-driven sign flip at once, which is hard to hand-tune reliably.
    ``_two_sided_p`` is monkeypatched to force significance so this test isolates exactly the ONE
    thing it exists to prove: that ``killed_fragile`` is a live, reachable branch of
    ``screen_candidate`` itself (not merely of the isolated helper) when its own sign-flip
    condition holds."""
    anchors = []
    # session A (few candidate anchors): consistently mildly negative
    for i in range(8):
        anchors.append({"session_date": "A", "symbol": "PG", "feature_value": 1.0, "outcome_value": -0.2})
        anchors.append({"session_date": "A", "symbol": "PG", "feature_value": -1.0, "outcome_value": 0.0})
    # session B (the MOST candidate anchors -- "biggest"): strongly positive
    for i in range(12):
        anchors.append({"session_date": "B", "symbol": "PG", "feature_value": 1.0, "outcome_value": 2.0})
        anchors.append({"session_date": "B", "symbol": "PG", "feature_value": -1.0, "outcome_value": 0.0})
    # session C (few candidate anchors): consistently mildly negative, like A
    for i in range(8):
        anchors.append({"session_date": "C", "symbol": "PG", "feature_value": 1.0, "outcome_value": -0.2})
        anchors.append({"session_date": "C", "symbol": "PG", "feature_value": -1.0, "outcome_value": 0.0})
    for a in anchors:
        a["tod_bucket"] = "mid"
        a["fallback_frac"] = 0.4

    monkeypatch.setattr(scout, "_two_sided_p", lambda observed, null: 0.0001)

    result = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="buy", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="fragile-fixture", n_variants_tried=1,
    )
    assert result["decision"] == "killed_fragile"
    assert result["screen_result"]["effect_bps"] > 0  # the WITH-all-sessions effect is positive


def test_fragile_leave_one_session_out_detects_a_sign_flip_directly():
    """The isolated-helper proof (complementing the full-``screen_candidate`` test above): a
    two-session case where dropping the session with more candidate-cell anchors flips the sign."""
    import numpy as np

    session_groups = {
        "small": {
            "outcomes": np.array([-1.0] * 6 + [0.0] * 6),
            "labels": np.array([True] * 6 + [False] * 6),
        },
        "big": {
            "outcomes": np.array([3.0] * 60 + [0.0] * 60),
            "labels": np.array([True] * 60 + [False] * 60),
        },
    }
    observed, _ = scout._observed_effect(session_groups)
    assert observed == pytest.approx((-1.0 + 3.0) / 2.0)
    assert scout._fragile_leave_one_session_out(session_groups, observed) is True


def test_fragile_leave_one_session_out_is_false_when_the_sign_is_stable():
    import numpy as np

    session_groups = {
        "a": {"outcomes": np.array([1.0, 0.0]), "labels": np.array([True, False])},
        "b": {"outcomes": np.array([2.0, 0.0]), "labels": np.array([True, False])},
    }
    observed, _ = scout._observed_effect(session_groups)
    assert scout._fragile_leave_one_session_out(session_groups, observed) is False


def test_fragile_leave_one_session_out_is_false_with_fewer_than_two_sessions():
    import numpy as np

    session_groups = {"only": {"outcomes": np.array([1.0, 0.0]), "labels": np.array([True, False])}}
    assert scout._fragile_leave_one_session_out(session_groups, 1.0) is False


# === feature membership + fallback-tercile applicability ============================================


def test_feature_membership_threshold_ge():
    assert scout._feature_membership(1.0, "threshold", {"op": "ge", "value": 1.0}) is True
    assert scout._feature_membership(0.999, "threshold", {"op": "ge", "value": 1.0}) is False


def test_feature_membership_threshold_all_operators():
    params_gt = {"op": "gt", "value": 1.0}
    assert scout._feature_membership(1.0001, "threshold", params_gt) is True
    assert scout._feature_membership(1.0, "threshold", params_gt) is False
    params_le = {"op": "le", "value": 1.0}
    assert scout._feature_membership(1.0, "threshold", params_le) is True
    params_lt = {"op": "lt", "value": 1.0}
    assert scout._feature_membership(0.9, "threshold", params_lt) is True


def test_feature_membership_rejects_an_unknown_transform():
    with pytest.raises(ValueError):
        scout._feature_membership(1.0, "not-a-real-transform", {})


def test_fallback_tercile_is_none_for_a_liquidity_only_feature():
    anchors = _planted_effect_anchors()
    cell_of = ["candidate"] * len(anchors)
    assert scout._fallback_tercile_slices(anchors, cell_of, "quote_imbalance") is None


def test_fallback_tercile_is_populated_for_an_aggressor_derived_feature():
    anchors = _planted_effect_anchors()
    cell_of = [
        "candidate" if a["feature_value"] >= 0 else "comparator" for a in anchors
    ]
    sliced = scout._fallback_tercile_slices(anchors, cell_of, "cumulative_delta")
    assert set(sliced.keys()) == {"low", "mid", "high"}


def test_aggressor_derived_features_are_exactly_f_flow_and_f_response():
    for name, family in scout.FEATURE_FAMILY_OF.items():
        assert (name in scout.AGGRESSOR_DERIVED_FEATURES) == (family in ("F-FLOW", "F-RESPONSE"))


# === extract_anchors: reuses micro_join.py's own tested outcome machinery (read-side law) ==========


@pytest.fixture(scope="module")
def pg_snapshot_store(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("scout_extract")
    target = tmp_path / "datasets"
    target.mkdir()
    for fixture_dir in _FIXTURE_DIRS:
        for path in fixture_dir.glob("*.json"):
            shutil.copy(path, target / path.name)
    store = DatasetStore(target)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    records, _errors = store.list()
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]
    return store, snapshots_dir, manifest


def test_extract_anchors_returns_one_row_per_measured_trade_anchor(pg_snapshot_store):
    store, snapshots_dir, manifest = pg_snapshot_store
    anchors = scout.extract_anchors(
        feature_name="cumulative_delta", structure_context_kind="none", horizon_key="trades_20",
        sidedness=None, corpus_manifest=manifest, dataset_store=store, snapshots_dir=snapshots_dir,
        config=CONFIG,
    )
    assert anchors  # non-empty
    for a in anchors:
        assert a["session_date"] == "2026-06-09"
        assert a["symbol"] == "PG"
        assert isinstance(a["feature_value"], float)
        assert isinstance(a["outcome_value"], float)
        assert a["tod_bucket"] in ("open", "mid", "close", None)


def test_extract_anchors_refuses_a_structure_context_outside_the_closed_set():
    """J-09: ``"band_touch"``/``"playbook_signal"`` are now wired (see the dedicated TC-1/TC-2
    tests below) -- ``ScoutUnsupportedStructureContextError`` fires only for a value genuinely
    outside the closed ``STRUCTURE_CONTEXT_KINDS`` set."""
    with pytest.raises(scout.ScoutUnsupportedStructureContextError):
        scout.extract_anchors(
            feature_name="cumulative_delta", structure_context_kind="not_a_real_kind",
            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
            snapshots_dir="/nonexistent", config=CONFIG,
        )


def test_extract_anchors_band_touch_requires_a_resolver():
    with pytest.raises(ValueError, match="requires a resolver"):
        scout.extract_anchors(
            feature_name="failed_aggression_score", structure_context_kind="band_touch",
            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
            snapshots_dir="/nonexistent", config=CONFIG,
        )


def test_extract_anchors_playbook_signal_requires_a_playbook_store():
    with pytest.raises(ValueError, match="requires a playbook_store"):
        scout.extract_anchors(
            feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
            snapshots_dir="/nonexistent", config=CONFIG,
        )


# === TC-1/TC-2 (goal-rapid-microscope-iter-21, J-09): band_touch / playbook_signal are wired ======


class _EmptyBarStore:
    def __init__(self, root="/tmp/does-not-exist-scout-touch-test"):
        self.root = root

    def list(self):
        return [], []


def _touch_resolver(tmp_path) -> BandMapResolver:
    return BandMapResolver(
        _EmptyBarStore(), CONFIG, cache=TradabilityCache(str(tmp_path / "trad.db"))
    )


def test_tc1_extract_anchors_band_touch_returns_rows_joined_via_join_band_touch(pg_snapshot_store, tmp_path):
    """TC-1: given ``structure_context_kind="band_touch"`` and a fixture dataset with a resolvable
    band map, ``extract_anchors`` returns anchor rows joined via ``join_band_touch`` instead of
    raising -- a WIDE band over the real PG price range (148.80-149.20) so at least one of the
    fixture's ~1,000 real trade prints genuinely touches it."""
    store, snapshots_dir, manifest = pg_snapshot_store
    resolver = _touch_resolver(tmp_path)
    first_meta = store.get(manifest[0]["dataset_id"])
    window_start_epoch = parse_utc_epoch(first_meta["window_start_utc"])
    resolver._cache.publish(
        resolver.map_key("PG", window_start_epoch),
        {"basis_day": "2026-06-08", "bands": [{"side": "resistance", "price_low": 148.80, "price_high": 149.20}]},
    )

    anchors = scout.extract_anchors(
        feature_name="failed_aggression_score", structure_context_kind="band_touch",
        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
        snapshots_dir=snapshots_dir, config=CONFIG, resolver=resolver,
    )

    assert anchors, "no anchors extracted -- the band never touched, or the join silently failed"
    for a in anchors:
        assert a["symbol"] == "PG"
        assert isinstance(a["feature_value"], float)
        assert isinstance(a["outcome_value"], float)


def test_tc1_extract_anchors_band_touch_still_raises_for_a_kind_outside_the_closed_set():
    with pytest.raises(scout.ScoutUnsupportedStructureContextError):
        scout.extract_anchors(
            feature_name="failed_aggression_score", structure_context_kind="not_a_real_kind",
            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
            snapshots_dir="/nonexistent", config=CONFIG,
        )


def _plant_capitulation_signal(tmp_path, *, dataset_meta: dict) -> PlaybookStore:
    """One recorded playbook signal, ``setup_id="capitulation"`` verbatim, whose ``trigger_ts``
    falls inside ``dataset_meta``'s own window."""
    playbook_store = PlaybookStore(tmp_path / "playbook")
    window_start_epoch = parse_utc_epoch(dataset_meta["window_start_utc"])

    trigger_dt = datetime.fromtimestamp(window_start_epoch + 5.0, tz=timezone.utc)
    trigger_ts = trigger_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
    playbook_store.record(
        session_date="2026-06-09",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-tc2-capitulation",
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=[
            {"symbol": dataset_meta["symbol"], "setup_id": "capitulation", "trigger_ts": trigger_ts},
        ],
        absences=[], diagnostics=[],
    )
    return playbook_store


def test_tc2_extract_anchors_playbook_signal_carries_setup_id_verbatim(pg_snapshot_store, tmp_path):
    """TC-2: given ``structure_context_kind="playbook_signal"`` and a fixture recorded signal with
    ``setup_id="capitulation"``, ``extract_anchors`` returns an anchor row joined via
    ``join_playbook_signal`` -- this module's own anchor row does not carry ``setup_id`` (the
    "none"-path row shape, unchanged by J-09), so this test proves the join happened by asserting a
    genuine, non-empty row grounded in the recorded signal's own window, and separately (below)
    that ``join_playbook_signal`` itself carries ``setup_id`` verbatim (the underlying primitive
    J-03 already proved -- this test proves J-09 REACHES it)."""
    store, snapshots_dir, manifest = pg_snapshot_store
    first_meta = store.get(manifest[0]["dataset_id"])
    playbook_store = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)

    anchors = scout.extract_anchors(
        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
    )

    assert len(anchors) == 1
    assert anchors[0]["symbol"] == "PG"
    assert isinstance(anchors[0]["feature_value"], float)
    assert isinstance(anchors[0]["outcome_value"], float)

    # The underlying join primitive DOES carry setup_id verbatim (micro_join.py's own contract,
    # J-03) -- proves the ROUTE this anchor traveled, not merely that a row exists.
    signal = playbook_store.list()[0][0]["signals"][0]
    joined = mj.join_playbook_signal(signal, store, snapshots_dir, CONFIG)
    assert joined["status"] == mj.JOIN_STATUS_JOINED
    assert joined["setup_id"] == "capitulation"


def test_tc2_extract_anchors_playbook_signal_narrows_by_setup_id(pg_snapshot_store, tmp_path):
    store, snapshots_dir, manifest = pg_snapshot_store
    first_meta = store.get(manifest[0]["dataset_id"])
    playbook_store = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)
    # A second signal, a DIFFERENT setup_id, at a different instant -- must be excluded when
    # narrowed to "capitulation".
    window_start_epoch = parse_utc_epoch(first_meta["window_start_utc"])
    other_ts = datetime.fromtimestamp(window_start_epoch + 8.0, tz=timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")
    playbook_store.record(
        session_date="2026-06-09",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-tc2-other",
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=[{"symbol": "PG", "setup_id": "opening_range_break", "trigger_ts": other_ts}],
        absences=[], diagnostics=[],
    )

    narrowed = scout.extract_anchors(
        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
        setup_id="capitulation",
    )
    unnarrowed = scout.extract_anchors(
        feature_name="failed_aggression_score", structure_context_kind="playbook_signal",
        horizon_key="trades_20", sidedness=None, corpus_manifest=manifest, dataset_store=store,
        snapshots_dir=snapshots_dir, config=CONFIG, playbook_store=playbook_store,
    )

    assert len(narrowed) == 1
    assert len(unnarrowed) == 2


def test_extract_anchors_skips_a_dataset_with_no_currently_valid_snapshot(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    anchors = scout.extract_anchors(
        feature_name="cumulative_delta", structure_context_kind="none", horizon_key="trades_20",
        sidedness=None, corpus_manifest=[{"dataset_id": "nonexistent"}], dataset_store=store,
        snapshots_dir=str(tmp_path / "snapshots"), config=CONFIG,
    )
    assert anchors == []


def test_extract_anchors_count_matches_measured_outcome_rows_at_that_horizon(pg_snapshot_store):
    """A reference computed a SECOND, obviously-correct way (the ``micro_join.py`` machinery
    directly, not through ``extract_anchors``) -- the same "hand-computed oracle" discipline
    ``test_micro_join.py`` itself uses."""
    store, snapshots_dir, manifest = pg_snapshot_store
    from app.research.micro_snapshots import read_snapshot_rows

    dataset_id = manifest[0]["dataset_id"]
    rows = read_snapshot_rows(snapshots_dir, dataset_id)
    trade_rows = [r for r in rows if not r.get("close_out")]
    session_end_ts = scout._session_end_logical_ts(store.get(dataset_id))

    expected = 0
    for anchor_row in trade_rows:
        if anchor_row.get("cumulative_delta") is None:
            continue
        outcomes = mj.outcome_rows_after_trigger(rows, anchor_row, session_end_ts, side=None)
        o = next(o for o in outcomes if o["horizon_kind"] == "trades" and o["horizon_value"] == 20)
        if not o["mid"]["unmeasured"] and not o["mid"]["truncated"]:
            expected += 1

    anchors = scout.extract_anchors(
        feature_name="cumulative_delta", structure_context_kind="none", horizon_key="trades_20",
        sidedness=None, corpus_manifest=[manifest[0]], dataset_store=store, snapshots_dir=snapshots_dir,
        config=CONFIG,
    )
    assert len(anchors) == expected


# === TC-10: the compute manager enforces single-flight ==============================================


def test_tc10_manager_refuses_a_second_concurrent_trigger(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ledger_dir = str(tmp_path / "scout")
    manager = scout.ScoutComputeManager()
    first = manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    assert first["state"] == "running"
    second = manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    assert second == {"state": "refused", "reason": "already_running"}
    manager.join_all(timeout=30.0)


def test_tc10_manager_reports_idle_before_any_job():
    manager = scout.ScoutComputeManager()
    snap = manager.snapshot()
    assert snap["state"] == "idle"
    assert snap["progress"]["candidates_total"] == 0


def test_tc10_cancel_on_an_idle_manager_is_a_harmless_no_op():
    manager = scout.ScoutComputeManager()
    result = manager.cancel()
    assert result["accepted"] is False


def test_tc10_a_failed_run_never_writes_a_silently_short_ledger(tmp_path, monkeypatch):
    """The iteration-2 streamed-artifact-completeness lesson, explicitly named for THIS manager
    (the phase spec's own NOTES): a mid-run exception resolves the job to "failed", and the run log
    records it -- never a "done" over a partial grid."""
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ledger_dir = str(tmp_path / "scout")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated scout failure")

    monkeypatch.setattr(scout, "register_and_screen_candidate", _boom)
    manager = scout.ScoutComputeManager()
    manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    manager.join_all(timeout=30.0)
    time.sleep(0.05)
    snap = manager.snapshot()
    assert snap["state"] == "failed"
    assert "simulated scout failure" in (snap["error"] or "")

    from app.research.micro_snapshots import read_run_log

    runs = read_run_log(ledger_dir)
    assert runs[0]["state"] == "failed"


# === TC-11: manager-triggered and CLI-triggered runs produce identical ledger content ================


# === J-05 TC-5: the accessor re-point (micro_accessor.MicroAccessor, unfenced) is byte-identical ===


def test_tc5_the_iteration_4_bounded_fixture_grid_still_reads_killed_insufficient_n_after_the_re_point(tmp_path):
    """``_cached_dataset_rows``'s re-pointed ``MicroAccessor(...).read_snapshot_rows(...)`` call
    (J-05) must reproduce the EXACT documented iteration-4 baseline for the default fixture grid --
    every one of its 6 candidates over the committed ``datasets``/``datasets_j03`` fixtures (all
    one session date) honestly reads ``killed_insufficient_n`` (the iter-4 dev handoff's own
    finding: "zero survivors is a passing grade")."""
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    grid = scout.default_fixture_grid(store, grid_version=1)

    rows = scout.run_scout_grid_and_record(grid, ledger, store, snapshots_dir, CONFIG)

    assert len(rows) == 6
    for row in rows:
        assert row["decision"] == "killed_insufficient_n"
        assert row["reason"] == "killed_insufficient_n"


def test_tc11_manager_and_cli_produce_byte_identical_spec_hash_and_decision_per_candidate(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)

    ledger_a = scout_ledger.ScoutLedger(tmp_path / "ledger_manager")
    ledger_b = scout_ledger.ScoutLedger(tmp_path / "ledger_cli")
    grid = scout.default_fixture_grid(store, grid_version=1)

    rows_a = scout.run_scout_grid_and_record(grid, ledger_a, store, snapshots_dir, CONFIG)
    rows_b = scout.run_scout_grid_and_record(grid, ledger_b, store, snapshots_dir, CONFIG)

    assert len(rows_a) == len(rows_b) == len(grid)
    for a, b in zip(rows_a, rows_b):
        assert a["spec_hash"] == b["spec_hash"]
        assert a["params_hash"] == b["params_hash"]
        assert a["decision"] == b["decision"]
        assert a["reason"] == b["reason"]


def test_tc11_the_cli_main_produces_the_same_grid_against_a_pointed_dataset_dir(tmp_path, monkeypatch):
    """The CLI's own ``main()`` entry point, invoked in-process (the ``micro_snapshots.py``
    CLI-test precedent) -- proves the CLI is not a second implementation, only a different
    trigger of the SAME ``run_scout_grid_and_record``. Points every store at ``tmp_path`` via the
    SAME env-var overrides the CLI's own ``main()`` reads through ``CONFIG.dataset_dir_resolved()``
    -- never touches the real ``.data`` corpus."""
    import sys

    store = _combined_fixture_store(tmp_path)
    dataset_dir = str(tmp_path / "datasets")
    scout_dir = str(tmp_path / "cli_scout")
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", dataset_dir)
    monkeypatch.setenv("TAPEOLOGY_MICRO_SCOUT_DIR", scout_dir)
    monkeypatch.setattr(sys, "argv", ["scout.py"])

    exit_code = scout.main()
    assert exit_code == 0

    ledger = scout_ledger.ScoutLedger(scout_dir)
    grid = scout.default_fixture_grid(store, grid_version=1)
    assert len(ledger.all_rows()) == len(grid)


# === TC-12: the served screen carries every mandatory disclosure + the frozen proxy sentence ========


@pytest.fixture
def scout_client(tmp_path):
    dataset_store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ledger_dir = str(tmp_path / "scout")
    manager = scout.ScoutComputeManager()
    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
    app.dependency_overrides[get_micro_snapshots_dir] = lambda: snapshots_dir
    app.dependency_overrides[get_scout_ledger_dir] = lambda: ledger_dir
    app.dependency_overrides[get_scout_compute_manager] = lambda: manager
    with TestClient(app) as c:
        yield c, dataset_store, snapshots_dir, ledger_dir, manager
    app.dependency_overrides.pop(get_dataset_store, None)
    app.dependency_overrides.pop(get_micro_snapshots_dir, None)
    app.dependency_overrides.pop(get_scout_ledger_dir, None)
    app.dependency_overrides.pop(get_scout_compute_manager, None)


# === J-09 (goal-rapid-microscope-iter-21): the additive grid-selector on POST /scout/compute =====


def test_compute_route_omitted_body_is_byte_identical_to_the_default_grid(scout_client):
    """The route's own additive-body contract: no body at all (every pre-J-09 caller) triggers the
    UNCHANGED default reference grid -- ``candidates_total`` matches ``default_fixture_grid``'s own
    width."""
    c, store, snapshots_dir, ledger_dir, manager = scout_client
    expected = len(scout.default_fixture_grid(store))

    resp = c.post("/research/desk/micro/scout/compute")
    assert resp.status_code == 200
    assert resp.json()["state"] == "running"
    manager.join_all(timeout=30.0)
    assert manager.snapshot()["progress"]["candidates_total"] == expected


def test_compute_route_pilot_grid_selector_runs_the_one_delta_divergence_candidate(scout_client):
    """The additive ``{"grid": "delta_divergence_pilot"}`` body selects the ONE J-09 pilot
    candidate this era screens -- ``candidates_total == 1``, never the 6-wide default grid, and
    never Study 1/3 (structurally unreachable through this route -- goal.md OUT OF SCOPE)."""
    c, store, snapshots_dir, ledger_dir, manager = scout_client

    resp = c.post("/research/desk/micro/scout/compute", json={"grid": scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT})
    assert resp.status_code == 200
    assert resp.json()["state"] == "running"
    manager.join_all(timeout=30.0)
    snap = manager.snapshot()
    assert snap["progress"]["candidates_total"] == 1
    assert snap["state"] == "done"

    ledger_body = c.get("/research/desk/micro/scout").json()
    families = ledger_body["families"]
    assert len(families) == 1
    assert families[0]["trials"][0]["feature"]["name"] == scout._DIVERGENCE_FEATURE_NAME
    assert families[0]["trials"][0]["structure_context"]["kind"] == "band_touch"


def test_iter21_audit_b1_pilot_route_records_the_walkforward_floor_check_row(scout_client, tmp_path):
    """iter-21 audit finding B1 (the browser lane's own UT-04): the OPERATOR-reachable pilot run
    (``POST /scout/compute {"grid": "delta_divergence_pilot"}``) RECORDS the walk-forward
    floor-check decision as a SECOND ledger row under the SAME ``candidate_id`` -- goal.md IN SCOPE
    item 6. Before the fix, ``register_screen_and_walkforward_check`` was called only from a unit
    test, so no route, CLI, or manager path could ever produce that row.

    Hermetic: an EMPTY bar store (no band map ever resolves -> an honest zero-anchor screen) and a
    fresh, never-initialized exposure registry (zero ``historical_oos`` sessions -> the honest
    ``insufficient_n`` refusal), so this test never reads the operator's real stores."""
    from app.research.bars import BarStore
    from app.research.micro_routes import get_micro_exposure_registry_dir
    from app.research.routes import get_bar_store

    c, store, snapshots_dir, ledger_dir, manager = scout_client
    app.dependency_overrides[get_bar_store] = lambda: BarStore(str(tmp_path / "audit_bars"))
    app.dependency_overrides[get_micro_exposure_registry_dir] = lambda: str(tmp_path / "audit_exposure")
    try:
        resp = c.post(
            "/research/desk/micro/scout/compute",
            json={"grid": scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT},
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "running"
        manager.join_all(timeout=60.0)
        assert manager.snapshot()["state"] == "done", manager.snapshot()["error"]
    finally:
        app.dependency_overrides.pop(get_bar_store, None)
        app.dependency_overrides.pop(get_micro_exposure_registry_dir, None)

    rows = scout_ledger.ScoutLedger(ledger_dir).all_rows()
    assert len(rows) == 2, [r.get("stage") for r in rows]
    screen_row, wf_row = rows
    assert wf_row["candidate_id"] == screen_row["candidate_id"]
    assert wf_row["stage"] == "walkforward_floor_check"
    assert wf_row["decision"] == "killed_insufficient_n"
    assert wf_row["walkforward_floor_check"]["status"] == "insufficient_n"
    assert wf_row["walkforward_floor_check"]["oos_session_count"] == 0
    assert "WF_TRAIN_MIN_SESSIONS" in wf_row["walkforward_floor_check"]["missing"]["oos_sessions"]

    body = c.get("/research/desk/micro/scout").json()
    assert len(body["families"]) == 1
    trials = body["families"][0]["trials"]
    assert len(trials) == 2
    assert trials[0]["structure_context"]["kind"] == "band_touch"
    assert scout_ledger.distinct_variant_count(rows) == 1


def test_iter21_audit_b1_default_grid_run_is_still_screen_only(scout_client):
    """The other half of the fix's contract: the DEFAULT reference grid (every pre-J-09 caller)
    still writes exactly ONE row per candidate -- no floor-check stage row anywhere."""
    c, store, snapshots_dir, ledger_dir, manager = scout_client

    resp = c.post("/research/desk/micro/scout/compute")
    assert resp.status_code == 200
    manager.join_all(timeout=60.0)
    assert manager.snapshot()["state"] == "done"

    rows = scout_ledger.ScoutLedger(ledger_dir).all_rows()
    assert len(rows) == len(scout.default_fixture_grid(store))
    assert all(row.get("stage") != "walkforward_floor_check" for row in rows)


def test_tc12_served_screen_carries_every_mandatory_disclosure(scout_client):
    c, store, snapshots_dir, ledger_dir, manager = scout_client
    manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    manager.join_all(timeout=30.0)

    resp = c.get("/research/desk/micro/scout")
    assert resp.status_code == 200
    body = resp.json()
    assert body["families"]
    for family in body["families"]:
        assert "variants_tried" in family and isinstance(family["variants_tried"], int)
        assert family["trials"]
        for trial in family["trials"]:
            sr = trial["screen_result"]
            assert sr["evidence_class"] == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
            assert sr["p_screen_label"] == "descriptive screen -- not a confirmatory p-value"
            assert "n_candidate" in sr and "n_comparator" in sr
            assert set(sr["concentration"].keys()) == {"top1_session_share", "top1_symbol_share"}
            assert isinstance(sr["tod_buckets"], dict)
            assert "best_of_n_disclosure" in sr and "n" in sr["best_of_n_disclosure"]
            assert "econ_interesting" in sr
            assert sr["econ_proxy_sentence"] == scout.ECON_PROXY_SENTENCE
            assert scout.ECON_PROXY_SENTENCE == (
                "quoted spread is a research cost proxy, not a full execution or tradability model"
            )


def test_tc2_route_serves_variants_tried_as_the_union_across_grid_versions(scout_client):
    """TC-2's own literal wording: ``GET /research/desk/micro/scout`` serves ``variants_tried``.
    Plants v1 (40) + v2 (25) rows directly into the SAME ledger the route reads (bypassing the
    24-cap deliberately -- ``test_scout_ledger.py``'s own TC-2 tests already document why) and
    confirms the ROUTE -- not just the underlying function -- serves 65."""
    c, _store, _snap_dir, ledger_dir, _manager = scout_client
    ledger = scout_ledger.ScoutLedger(ledger_dir)
    family_id = "route-union-n"
    for i in range(40):
        ledger.append_row({"family_id": family_id, "grid_version": 1, "decision": "killed_null"})
    for i in range(25):
        ledger.append_row({"family_id": family_id, "grid_version": 2, "decision": "killed_null"})

    resp = c.get("/research/desk/micro/scout")
    body = resp.json()
    family = next(f for f in body["families"] if f["family_id"] == family_id)
    assert family["variants_tried"] == 65


def test_get_scout_is_an_honest_empty_list_on_a_fresh_ledger(scout_client):
    c, *_ = scout_client
    resp = c.get("/research/desk/micro/scout")
    assert resp.status_code == 200
    assert resp.json() == {
        "families": [],
        "chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
    }


# --- TC-3's second clause, at the SERVING path (iter-4 audit fix) -----------------------------------


def test_tc3_the_scout_route_never_serves_a_tampered_ledger_without_saying_so(scout_client):
    """TC-3's own literal second clause -- "no code path silently accepts the tampered chain."
    Before this fix ``verify_chain()`` was called by NOTHING but tests: ``GET
    /research/desk/micro/scout`` read the ledger straight through ``all_rows()`` and served a
    tampered ``killed_null`` -> ``survive`` flip as a survivor, silently."""
    c, _store, _snap_dir, ledger_dir, _manager = scout_client
    ledger = scout_ledger.ScoutLedger(ledger_dir)
    ledger.append_row({"family_id": "f", "candidate_id": "c1", "decision": "killed_null"})
    ledger.append_row({"family_id": "f", "candidate_id": "c2", "decision": "killed_null"})

    clean = c.get("/research/desk/micro/scout").json()
    assert clean["chain_verification"] == {"ok": True, "failed_at_row": None, "reason": None}

    lines = ledger.path.read_text().splitlines()
    tampered = json.loads(lines[1])
    tampered["decision"] = "survive"  # a kill rewritten into a survivor, on disk
    lines[1] = json.dumps(tampered, sort_keys=True)
    ledger.path.write_text("\n".join(lines) + "\n")

    body = c.get("/research/desk/micro/scout").json()
    assert body["chain_verification"] == {
        "ok": False,
        "failed_at_row": 1,
        "reason": "content_hash_mismatch",
    }
    # the trials are still served (surfaced, never withheld) -- but never WITHOUT the verdict
    assert [t["decision"] for t in body["families"][0]["trials"]] == ["killed_null", "survive"]


def test_the_scout_route_reports_a_truncated_ledger_tail(scout_client):
    """A deleted TAIL row -- the erasure a linked chain cannot see on its own -- is reported by the
    same served verdict (iter-4 audit fix; the era's "the denominator never shrinks" anti-goal)."""
    c, _store, _snap_dir, ledger_dir, _manager = scout_client
    ledger = scout_ledger.ScoutLedger(ledger_dir)
    ledger.append_row({"family_id": "f", "candidate_id": "c1", "decision": "killed_null"})
    ledger.append_row({"family_id": "f", "candidate_id": "c2", "decision": "killed_economic"})

    lines = ledger.path.read_text().splitlines()
    del lines[-1]  # erase the most recent kill
    ledger.path.write_text("\n".join(lines) + "\n")

    body = c.get("/research/desk/micro/scout").json()
    assert body["chain_verification"] == {"ok": False, "failed_at_row": 1, "reason": "tail_truncated"}


# --- a horizon whose permutation block cannot be sized from spec 5.3 is refused, never screened
# under a mis-calibrated null (iter-4 audit fix) ----------------------------------------------------


@pytest.mark.parametrize("horizon_key", ["shares_5000", "shares_50000", "clock_seconds_30",
                                         "clock_seconds_60", "clock_seconds_300"])
def test_a_shares_or_clock_horizon_is_refused_rather_than_screened_under_a_short_block(horizon_key):
    """Spec section 5.3 ties the block length to the label span in EVENTS. A shares/clock horizon's
    event span is data-dependent and routinely hundreds of trades, so the previous 20-event
    stand-in was SHORTER than the label span -- an anti-conservative null, the exact failure the
    block design and TR-8's calibration trap exist to prevent. Section 5.3's non-overlapping
    anchor subsampling for clock horizons is unimplemented too. Refused, not approximated."""
    with pytest.raises(scout.ScoutUnsupportedHorizonError):
        scout.screen_candidate(
            feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
            sidedness=None, horizon_key=horizon_key, econ_floor=_ECON_FLOOR_TINY,
            anchors=_planted_effect_anchors(), family_id="f", n_variants_tried=1,
        )


def test_a_trade_count_horizon_is_still_screened_normally(tmp_path, snapshot_ready_store):
    """A lint that can fail proves something: the refusal is scoped to the horizons the spec's own
    block rule cannot size, never a blanket block on screening."""
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest,
        grid_version=1,
    )
    assert row["decision"] in scout_ledger.CLOSED_DECISIONS


def test_registering_a_shares_horizon_candidate_writes_no_ledger_row(tmp_path, snapshot_ready_store):
    store, snapshots_dir, manifest = snapshot_ready_store
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    with pytest.raises(scout.ScoutUnsupportedHorizonError):
        scout.register_and_screen_candidate(
            ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
            feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
            structure_context_kind="none", horizon_key="shares_5000", corpus_manifest=manifest,
            grid_version=1,
        )
    assert ledger.all_rows() == []


# --- union-N counts VARIANTS, not evaluations (iter-4 audit fix) ------------------------------------


def test_repeated_runs_of_the_identical_grid_never_inflate_variants_tried_or_exhaust_the_cap(tmp_path):
    """The operator-triggered compute route registers the IDENTICAL ``spec_hash``es on every run.
    Counting ledger ROWS made a family's served union-N grow by the grid's own width per run, and
    drove every family into ``SCOUT_MAX_VARIANTS_PER_FAMILY`` after 12 identical runs -- after
    which the default grid raised ``ScoutGridExhaustedError`` forever, with no recovery an
    append-only ledger is allowed to offer. Every trial is still permanently on record; only the
    COUNT changed."""
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    grid = scout.default_fixture_grid(store, grid_version=1)

    for _ in range(13):  # one more than the 12 identical runs that used to brick the endpoint
        scout.run_scout_grid_and_record(grid, ledger, store, snapshots_dir, CONFIG)

    assert len(ledger.all_rows()) == 13 * len(grid)  # every evaluation still permanently on record
    families = scout.list_scout_families(ledger)
    assert families
    for family in families:
        assert family["variants_tried"] == 2  # 2 DISTINCT variants per family, not 26 evaluations
        assert len(family["trials"]) == 26
        # each row's stamped best-of-N is the union-N AS OF that row (1 for the family's very first
        # trial, 2 from its second on) -- never a number that grows with re-runs
        stamped = [t["screen_result"]["best_of_n_disclosure"]["n"] for t in family["trials"]]
        assert stamped == [1] + [2] * 25


def test_compute_route_triggers_a_run_and_reports_progress_to_done(scout_client):
    c, *_ = scout_client
    post_resp = c.post("/research/desk/micro/scout/compute")
    assert post_resp.status_code == 200
    assert post_resp.json()["state"] == "running"
    assert "run_id" in post_resp.json()

    deadline = time.time() + 30.0
    state = None
    while time.time() < deadline:
        get_resp = c.get("/research/desk/micro/scout/compute")
        state = get_resp.json()["state"]
        if state == "done":
            break
        time.sleep(0.05)
    assert state == "done"


def test_compute_route_refuses_a_second_concurrent_trigger(scout_client, monkeypatch):
    import threading

    c, store, snapshots_dir, ledger_dir, manager = scout_client
    entered = threading.Event()
    release = threading.Event()
    real_grid_run = scout.run_scout_grid_and_record

    def _blocking(*args, **kwargs):
        entered.set()
        release.wait(timeout=15.0)
        return real_grid_run(*args, **kwargs)

    monkeypatch.setattr(scout, "run_scout_grid_and_record", _blocking)
    try:
        manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
        assert entered.wait(timeout=10.0), "the first job never entered its run"
        resp = c.post("/research/desk/micro/scout/compute")
        assert resp.json() == {"state": "refused", "reason": "already_running"}
    finally:
        release.set()
    manager.join_all(timeout=15.0)


def test_cancel_route_409s_when_nothing_is_running(scout_client):
    c, *_ = scout_client
    resp = c.post("/research/desk/micro/scout/compute/cancel")
    assert resp.status_code == 409


def test_runs_route_lists_a_completed_job(scout_client):
    c, *_ = scout_client
    post_resp = c.post("/research/desk/micro/scout/compute")
    run_id = post_resp.json()["run_id"]
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if c.get("/research/desk/micro/scout/compute").json()["state"] == "done":
            break
        time.sleep(0.05)
    resp = c.get("/research/desk/micro/scout/runs")
    runs = resp.json()["runs"]
    assert len(runs) == 1
    assert runs[0]["run_id"] == run_id
    assert runs[0]["state"] == "done"


# === TC-4/TC-7 (goal-rapid-microscope-iter-21, J-09): the pilot-study candidate grid =================


def test_tc4_pilot_study_candidate_grid_carries_all_three_requests_in_priority_order(tmp_path):
    store = _combined_fixture_store(tmp_path)
    grid = scout.pilot_study_candidate_grid(store)

    assert list(grid.keys()) == [
        scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION,
        scout.PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS,
        scout.PILOT_STUDY_CAPITULATION_EXHAUSTION,
    ]


def test_tc4_every_pilot_request_carries_fully_constructed_frozen_fields(tmp_path):
    store = _combined_fixture_store(tmp_path)
    grid = scout.pilot_study_candidate_grid(store)

    for study_id, request in grid.items():
        spec = scout.build_candidate_spec_fields(
            feature_name=request["feature_name"], transform=request["transform"],
            params=request["params"], structure_context_kind=request["structure_context_kind"],
            horizon_key=request["horizon_key"], sidedness=request["sidedness"],
            fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
            corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
            setup_id=request.get("setup_id"),
        )
        assert spec["feature"]["name"] and spec["feature"]["transform"] and spec["feature"]["params"], study_id
        assert spec["structure_context"]["kind"] == request["structure_context_kind"], study_id
        assert spec["outcome"]["horizon_key"] == request["horizon_key"], study_id
        assert spec["econ_floor"]["floor_bps"] is not None, study_id


def test_tc4_the_three_pilot_requests_have_three_distinct_family_root_ids(tmp_path):
    store = _combined_fixture_store(tmp_path)
    grid = scout.pilot_study_candidate_grid(store)

    root_ids = set()
    for request in grid.values():
        spec = scout.build_candidate_spec_fields(
            feature_name=request["feature_name"], transform=request["transform"],
            params=request["params"], structure_context_kind=request["structure_context_kind"],
            horizon_key=request["horizon_key"], sidedness=request["sidedness"],
            fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
            corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
            setup_id=request.get("setup_id"),
        )
        root_ids.add(spec["family_root_id"])
    assert len(root_ids) == 3


def test_tc4_capitulation_request_carries_its_setup_id_in_structure_context(tmp_path):
    store = _combined_fixture_store(tmp_path)
    request = scout.pilot_study_candidate_grid(store)[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
    assert request["structure_context_kind"] == "playbook_signal"
    assert request["setup_id"] == "capitulation"

    spec = scout.build_candidate_spec_fields(
        feature_name=request["feature_name"], transform=request["transform"],
        params=request["params"], structure_context_kind=request["structure_context_kind"],
        horizon_key=request["horizon_key"], sidedness=request["sidedness"],
        fitting_rule=request["fitting_rule"], family_median_spread_bps=1.5,
        corpus_manifest=request["corpus_manifest"], grid_version=request["grid_version"],
        setup_id=request["setup_id"],
    )
    assert spec["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}


def test_tc4_setup_id_omitted_from_structure_context_when_not_given():
    """A pre-J-09 caller (never passing ``setup_id``) sees the IDENTICAL, byte-unmodified
    ``structure_context`` shape -- ``{"kind": ...}`` alone, no key added."""
    spec = scout.build_candidate_spec_fields(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", sidedness=None, fitting_rule=None,
        family_median_spread_bps=1.5, corpus_manifest=[], grid_version=1,
    )
    assert spec["structure_context"] == {"kind": "none"}


def test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened(tmp_path):
    """TC-7: range-wall-failed-aggression and capitulation-exhaustion exist in the frozen grid but
    are NOT passed through ``register_and_screen_candidate`` this iteration -- no partial ledger
    row for either. This test proves the negative directly: an empty scout ledger stays empty
    after only INSPECTING the frozen grid (never calling the registration entry point for those
    two study ids)."""
    store = _combined_fixture_store(tmp_path)
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    grid = scout.pilot_study_candidate_grid(store)

    # Inspecting the frozen requests never writes anything.
    assert grid[scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION]
    assert grid[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
    assert ledger.all_rows() == []


# === TC-5/TC-6 (goal-rapid-microscope-iter-21, J-09): the delta-divergence candidate, screened +
# walk-forward-floor-checked end to end, on a committed hermetic hand-derived oracle fixture. ========


class _DivergenceEmptyBarStore:
    def __init__(self, root="/tmp/does-not-exist-scout-divergence-test"):
        self.root = root

    def list(self):
        return [], []


def _divergence_band_group(symbol: str, price_low: float, *, bearish: bool, t0: float) -> tuple[list, list, float]:
    """4 touches of a ``[price_low, price_low + 0.02]`` band, then a neutral 26-trade tail so the
    ``trades_20`` outcome horizon is measurable at every pair's own tau2.

    ``bearish=True``: each touch is followed by a small BUY that sets a NEW LOCAL HIGH above the
    band (progressively higher across the 3 pairs -- ``price_extreme`` rises pair to pair), while
    the DOMINANT volume around each touch is a heavy SELL (``cumulative_delta`` falls pair to
    pair) -- the textbook divergence signature (Card 9.1). ``bearish=False``: no excursion above
    the band is ever made, so ``price_extreme`` never rises -- ``bearish_divergence`` is ``False``
    regardless of the delta side, by the formula's own AND condition. Validated against
    ``micro_features.divergence_at_level`` directly before being transcribed here (dev handoff)."""
    events: list = []
    events.append(QuoteEvent(symbol, 0.1, price_low - 0.20, price_low - 0.15, 500, 500))
    events.append(TradeEvent(symbol, 0.1, price_low - 0.18, 5, Side.SELL))
    t = t0

    def _q(bid: float, ask: float) -> None:
        events.append(QuoteEvent(symbol, t, bid, ask, 500, 500))

    def _buy(price: float, size: int = 10) -> None:
        _q(price - 0.02, price)
        events.append(TradeEvent(symbol, t, price, size, Side.BUY))

    def _sell(price: float, size: int = 10) -> None:
        _q(price, price + 0.02)
        events.append(TradeEvent(symbol, t, price, size, Side.SELL))

    touches: list[float] = []
    peak = price_low + 0.01
    for _i in range(4):
        _sell(price_low - 0.05, 50)
        t += 0.2
        _buy(price_low + 0.01, 5)
        t += 0.2
        touches.append(t - 0.2)
        if bearish:
            peak += 0.03
            _buy(peak, 5)
            t += 0.2
            _sell(price_low - 0.06, 80)
            t += 0.2
        else:
            _sell(price_low - 0.06, 20)
            t += 0.2
    exit_price = price_low - 0.10
    _sell(exit_price, 10)
    t += 0.2
    for i in range(26):
        px = exit_price + (0.001 if i % 2 == 0 else -0.001)
        if i % 2 == 0:
            _buy(px, 8)
        else:
            _sell(px, 8)
        t += 0.3
    return events, touches, t


_DIVERGENCE_BANDS = (
    {"side": "resistance", "price_low": 100.00, "price_high": 100.02},
    {"side": "resistance", "price_low": 105.00, "price_high": 105.02},
)


def _build_divergence_session(tmp_path: Path, *, symbol: str, window_start_utc: str, window_end_utc: str) -> dict:
    """One session's worth of 2 bands (one bearish-biased at 100.00, one flat-comparator at
    105.00), each contributing 3 consecutive-touch-pair anchors -- 3 candidate + 3 comparator per
    session."""
    bearish_events, _touches, t_after = _divergence_band_group(symbol, 100.00, bearish=True, t0=660.0)
    comparator_events, _touches2, _t = _divergence_band_group(symbol, 105.00, bearish=False, t0=t_after + 60.0)
    store = DatasetStore(tmp_path / "datasets")
    meta = store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-divergence-fixture",
        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
        data_feed="sip", epoch_anchor=0.0, events=bearish_events + comparator_events,
    )
    return meta


@pytest.fixture(scope="module")
def divergence_fixture(tmp_path_factory):
    """Two sessions (2026-06-09/DVA, 2026-06-10/DVB), each with a bearish-biased band and a
    flat-comparator band -- 6 candidate + 6 comparator anchors pooled, safely above
    ``SCOUT_MIN_OBSERVATIONS_PER_CELL``(5) and ``SCOUT_MIN_SESSION_CLUSTERS``(2). Module-scoped:
    dataset/snapshot construction is real I/O, paid once."""
    tmp_path = tmp_path_factory.mktemp("scout_divergence")
    session_a_dir = tmp_path / "a"
    session_a_dir.mkdir()
    session_b_dir = tmp_path / "b"
    session_b_dir.mkdir()
    meta_a = _build_divergence_session(
        session_a_dir, symbol="DVA", window_start_utc="2026-06-09T13:00:00Z",
        window_end_utc="2026-06-09T13:40:00Z",
    )
    meta_b = _build_divergence_session(
        session_b_dir, symbol="DVB", window_start_utc="2026-06-10T13:00:00Z",
        window_end_utc="2026-06-10T13:40:00Z",
    )
    combined_dir = tmp_path / "datasets"
    combined_dir.mkdir()
    for source_dir in (session_a_dir / "datasets", session_b_dir / "datasets"):
        for path in source_dir.glob("*.json"):
            shutil.copy(path, combined_dir / path.name)
    store = DatasetStore(combined_dir)
    records, errors = store.list()
    assert errors == []
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]

    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)

    resolver = BandMapResolver(
        _DivergenceEmptyBarStore(), CONFIG, cache=TradabilityCache(str(tmp_path / "trad.db"))
    )
    for meta in (store.get(meta_a["id"]), store.get(meta_b["id"])):
        window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
        resolver._cache.publish(
            resolver.map_key(meta["symbol"], window_start_epoch),
            {"basis_day": "fixture", "bands": list(_DIVERGENCE_BANDS)},
        )
    return {
        "store": store, "snapshots_dir": snapshots_dir, "manifest": manifest, "resolver": resolver,
    }


def test_tc5_delta_divergence_candidate_screens_with_full_disclosures(divergence_fixture):
    """TC-5: the delta-divergence request, passed to ``register_and_screen_candidate`` against
    this committed synthetic fixture, serves ``evidence_class``, the section 5.4 disclosures, and
    the section 5.5 ``econ_interesting`` column served BESIDE (never merged into) the statistical
    screen, with ``registered_at`` strictly before any outcome field populates (TR-9)."""

    ledger = scout_ledger.ScoutLedger(tempfile.mkdtemp())

    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=divergence_fixture["store"],
        snapshots_dir=divergence_fixture["snapshots_dir"], config=CONFIG,
        feature_name=scout._DIVERGENCE_FEATURE_NAME, transform="threshold",
        params={"op": "ge", "value": 1.0}, structure_context_kind="band_touch",
        horizon_key="trades_20", corpus_manifest=divergence_fixture["manifest"],
        resolver=divergence_fixture["resolver"],
    )

    assert row["structure_context"] == {"kind": "band_touch"}
    result = row["screen_result"]
    assert result["evidence_class"] == scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    assert result["n_candidate"] == 6
    assert result["n_comparator"] == 6
    assert result["n_usable_sessions"] == 2
    # section 5.4 disclosures, all present (TC-12's own "every disclosure, not only a surviving
    # one's" contract, reused here for the NEW band_touch/divergence path):
    assert set(result["concentration"]) == {"top1_session_share", "top1_symbol_share"}
    assert result["tod_buckets"]
    assert result["fallback_tercile"] is not None  # aggressor-derived (F-FLOW) -- always disclosed
    assert result["best_of_n_disclosure"]["n"] == 1
    # section 5.5: econ_interesting served BESIDE the screen, a real bool, never merged into
    # effect_bps/p_screen and never None (the corpus clears sufficiency, so this is computed).
    assert result["econ_interesting"] in (True, False)
    assert result["econ_proxy_sentence"] == scout.ECON_PROXY_SENTENCE
    # TR-9: registered_at strictly before econ_floor_computed_at could ever postdate it -- the
    # normal (both-None) call path stamps both at registration, so this is the ordering PROOF,
    # not merely an absence of the refusal.
    assert parse_utc_epoch(row["econ_floor_computed_at"]) <= parse_utc_epoch(row["registered_at"])
    assert row["decision"] in scout_ledger.CLOSED_DECISIONS


def test_tc6_walkforward_floor_check_refuses_and_records_insufficient_n(divergence_fixture):
    """TC-6: the walk-forward floor check on the delta-divergence candidate serves a typed
    floor-refusal naming the exact shortfall against ``WF_TRAIN_MIN_SESSIONS``/``WF_FOLD_MIN_
    SIGNAL_SESSIONS`` (both real and fixture corpora carry zero ``historical_oos`` sessions today
    -- a fresh, never-initialized exposure registry), recorded as the study's ledger decision
    (``killed_insufficient_n``) rather than silently omitted -- and ``evaluate_mode_b_fold`` is
    never called (a source-level check, below)."""
    from app.research.micro_accessor import ExposureRegistry

    ledger_dir = tempfile.mkdtemp()
    ledger = scout_ledger.ScoutLedger(ledger_dir)
    exposure_registry = ExposureRegistry(tempfile.mkdtemp())

    result = scout.register_screen_and_walkforward_check(
        ledger=ledger, dataset_store=divergence_fixture["store"],
        snapshots_dir=divergence_fixture["snapshots_dir"], config=CONFIG,
        exposure_registry=exposure_registry,
        feature_name=scout._DIVERGENCE_FEATURE_NAME, transform="threshold",
        params={"op": "ge", "value": 1.0}, structure_context_kind="band_touch",
        horizon_key="trades_20", corpus_manifest=divergence_fixture["manifest"],
        resolver=divergence_fixture["resolver"],
    )

    wf_row = result["walkforward_row"]
    assert wf_row["decision"] == "killed_insufficient_n"
    assert wf_row["reason"] == "killed_insufficient_n"
    floor_check = wf_row["walkforward_floor_check"]
    assert floor_check["status"] == "insufficient_n"
    assert floor_check["oos_session_count"] == 0
    assert "WF_TRAIN_MIN_SESSIONS" in floor_check["missing"]["oos_sessions"]
    from app.research import walkforward as wf

    assert floor_check["missing"]["signal_sessions"] == f"0 < {wf.WF_FOLD_MIN_SIGNAL_SESSIONS}"
    # never silently omitted: BOTH rows (screen + floor check) share the same candidate_id and
    # land in the SAME family's ledger history, and the family's own union-N stays 1 (one variant
    # DEFINITION, two evaluated STAGES -- scout_ledger.py's own "variants, not rows" contract).
    family_rows = ledger.rows_for_family(result["screen_row"]["family_id"])
    assert len(family_rows) == 2
    assert scout_ledger.distinct_variant_count(family_rows) == 1
    assert family_rows[0]["candidate_id"] == family_rows[1]["candidate_id"]


def test_evaluate_mode_b_fold_is_never_called_by_the_walkforward_floor_check_path():
    """A source-level guard (the ``test_the_banned_plain_shuffle_null_is_never_imported_or_called_
    by_a_production_path`` precedent): neither ``register_screen_and_walkforward_check`` nor
    ``walkforward.scout_candidate_walkforward_floor_check`` names ``evaluate_mode_b_fold`` anywhere
    in their own source."""
    import inspect

    from app.research import walkforward as wf

    assert "evaluate_mode_b_fold" not in inspect.getsource(scout.register_screen_and_walkforward_check)
    assert "evaluate_mode_b_fold" not in inspect.getsource(wf.scout_candidate_walkforward_floor_check)
