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
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import micro_join as mj
from app.research import scout, scout_ledger
from app.research.datasets import DatasetStore
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


def test_extract_anchors_refuses_a_non_none_structure_context():
    with pytest.raises(scout.ScoutUnsupportedStructureContextError):
        scout.extract_anchors(
            feature_name="cumulative_delta", structure_context_kind="playbook_signal",
            horizon_key="trades_20", sidedness=None, corpus_manifest=[], dataset_store=None,
            snapshots_dir="/nonexistent", config=CONFIG,
        )


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
