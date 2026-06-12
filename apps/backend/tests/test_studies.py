"""Replay-study runner + job-manager unit/integration matrix (capability 32, J-60/J-61/J-62).

Covers the determinism + seed-reproducibility + arming + hindsight-exclusion + never-pool/stamp +
cancellation + failure-path + occurrence-R clauses of the iteration spec. The PINNED reference-study
CI test (the J-62 flip) lives in ``test_studies_reference.py``; this file pins the seeded-sim arming
counts and the deterministic behaviours that do not need the real fixture.

All tests are hermetic: a temp-path ``JournalStore`` + a ``StudyJobManager`` run SYNCHRONOUSLY
(``run_sync``) so a study completes in-process with no thread race and no credentials.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from app.config import CONFIG, Config
from app.research.store import JournalStore
from app.research.studies import (
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_FAILED,
    StudyJobManager,
)


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


@pytest.fixture
def jobs(store):
    return StudyJobManager(store, CONFIG)


def _run(jobs, store, params):
    p = jobs.create(params)
    jobs.run_sync(p["id"])
    return store.get_study(p["id"]).payload


def _core(payload: dict) -> dict:
    """The determinism-comparable core (strip the per-creation id + wall ts)."""
    return {k: v for k, v in payload.items() if k not in ("id", "created_wall_ts")}


# --- arming on the seeded sims (deterministic occurrence counts) ---------------------------------

def test_absorption_reversal_arms_one_occurrence_on_sim_reversal(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert pl["status"] == STATUS_DONE
    # SIM-REVERSAL: ONE sustained bid_absorption phase => exactly ONE armed setup occurrence.
    assert pl["aggregates"]["setup"]["n"] == 1
    # The occurrence reaches `confirming` (the reversal to buyer_control the existing verdict engine
    # publishes) — proving the study runs the EXISTING per-setup verdict rule table, no new rule.
    assert pl["occurrences"][0]["verdict_summary"] == "confirming"
    # Its R basis is the deterministic occurrence-R (config spread-multiple on the adverse side).
    assert pl["occurrences"][0]["r_basis"] == 0.2


def test_trend_continuation_arms_on_sim_buyer(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-BUYER", "setup_type": "trend_continuation", "direction": "long"},
    )
    assert pl["status"] == STATUS_DONE
    # SIM-BUYER is one sustained buyer-control phase => exactly ONE armed occurrence.
    assert pl["aggregates"]["setup"]["n"] == 1
    assert pl["occurrences"][0]["verdict_summary"] == "confirming"


def test_setup_distribution_sits_beside_the_seeded_null_baseline(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    setup = pl["aggregates"]["setup"]
    null = pl["aggregates"]["null_baseline"]
    # The null baseline draws the config-owned arm count (100), the side-by-side honest control.
    assert null["n"] == CONFIG.study_null_arm_count == 100
    # The setup's 120s horizon reached +1R (the reversal lifted price) — pinned exactly.
    setup_120 = next(h for h in setup["horizons"] if h["horizon"] == 120.0)
    assert setup_120["+1R_first"] == 1 and setup_120["-1R_first"] == 0
    # The null baseline's 120s distribution differs (random arm times over the same window) — the
    # comparison the page exists to show. Pinned exactly for determinism.
    null_120 = next(h for h in null["horizons"] if h["horizon"] == 120.0)
    assert null_120["+1R_first"] == 77 and null_120["truncated"] == 23


# --- determinism + seed reproducibility ----------------------------------------------------------

def test_double_run_is_byte_identical_for_same_source_fingerprint_seed(jobs, store):
    params = {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"}
    a = _run(jobs, store, params)
    b = _run(jobs, store, params)
    # Identical (source, fingerprint, seed) => identical occurrences + aggregates + null baseline.
    assert _core(a) == _core(b)


def test_same_seed_identical_arms_different_seed_differs(jobs, store):
    base = {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"}
    a = _run(jobs, store, {**base, "null_baseline_seed": 1729})
    a2 = _run(jobs, store, {**base, "null_baseline_seed": 1729})
    different = _run(jobs, store, {**base, "null_baseline_seed": 42})
    # Same seed => identical null arms; the recorded seed is persisted on the record.
    assert a["null_occurrences"] == a2["null_occurrences"]
    assert a["null_baseline_seed"] == 1729 and different["null_baseline_seed"] == 42
    # A different seed => a recorded + different null baseline (the baseline is seed-reproducible).
    assert a["null_occurrences"] != different["null_occurrences"]


# --- the deterministic occurrence-R definition (the named design decision) -----------------------

def test_occurrence_r_is_config_owned_spread_multiple_on_the_adverse_side(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    occ = pl["occurrences"][0]
    # The synthetic invalidation is the arm price minus (spread_mult x spread, floored) for a LONG —
    # i.e. on the ADVERSE (below) side. R = |arm_price - invalidation| via the shared marks.r_basis.
    assert occ["invalidation_price"] < occ["arm_price"]
    assert occ["r_basis"] == round(abs(occ["arm_price"] - occ["invalidation_price"]), 4)


def test_occurrence_r_identical_definition_for_setup_and_null_arms(jobs, store):
    """Setup and null arms use the IDENTICAL R definition (a synthetic invalidation derived the same
    way from each arm's own price + spread) — never a second formula, never fitted. A null arm at the
    same price + spread as a setup arm would yield the same R basis by construction."""
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    # Every null arm's R basis equals |arm_price - invalidation_price| with the invalidation on the
    # adverse side — the same rule the setup arms use.
    for occ in pl["null_occurrences"]:
        assert occ["invalidation_price"] < occ["arm_price"]  # LONG => adverse side is below
        assert occ["r_basis"] == round(abs(occ["arm_price"] - occ["invalidation_price"]), 4)


def test_short_direction_places_synthetic_invalidation_above_arm_price(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-BUYER", "setup_type": "trend_continuation", "direction": "short"},
    )
    # For a SHORT the adverse side is ABOVE — the synthetic invalidation sits above the arm price.
    for occ in pl["null_occurrences"]:
        assert occ["invalidation_price"] > occ["arm_price"]


# --- hindsight level exclusion -------------------------------------------------------------------

def test_level_setup_is_stamped_hindsight_and_excluded_from_cross_study_aggregate(jobs, store):
    pl = _run(
        jobs,
        store,
        {
            "source_kind": "sim",
            "source_id": "SIM-REVERSAL",
            "setup_type": "level_break",
            "direction": "long",
            "level_price": 100.5,
        },
    )
    assert pl["status"] == STATUS_DONE
    assert pl["hindsight_level"] is True
    assert pl["excluded_from_cross_study_aggregate"] is True


def test_state_native_setup_is_not_hindsight(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert pl["hindsight_level"] is False
    assert pl["excluded_from_cross_study_aggregate"] is False


# --- honesty stamps + never-pool -----------------------------------------------------------------

def test_study_is_stamped_with_source_feed_fingerprint_seed(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert pl["data_feed"] == "sim"
    assert pl["config_fingerprint"] == CONFIG.config_fingerprint()
    assert pl["null_baseline_seed"] == CONFIG.study_null_baseline_seed
    assert pl["source"]  # the resolved source descriptor (the sim scenario name)


def test_reference_study_is_stamped_sip(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "reference", "source_id": "PG_SIP_REFERENCE", "setup_type": "trend_continuation", "direction": "long"},
    )
    # The reference window is the SIP consolidated feed — stamped sip, never pooled with a sim study.
    assert pl["data_feed"] == "sip"
    assert pl["status"] == STATUS_DONE


def test_each_study_carries_one_feed_and_one_fingerprint(jobs, store):
    """A study IS one feed + one fingerprint (never pooled across either) — a sim study and a
    reference (sip) study carry distinct feed stamps, so they can never be silently compared."""
    sim = _run(
        jobs, store,
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    ref = _run(
        jobs, store,
        {"source_kind": "reference", "source_id": "PG_SIP_REFERENCE", "setup_type": "trend_continuation", "direction": "long"},
    )
    assert sim["data_feed"] != ref["data_feed"]


# --- cancellation --------------------------------------------------------------------------------

def test_cancel_before_run_yields_cancelled_with_partial_marked_results(jobs, store):
    p = jobs.create(
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"}
    )
    jobs.cancel(p["id"])  # set the flag BEFORE running (deterministic mid-run-equivalent cancel)
    jobs.run_sync(p["id"])
    pl = store.get_study(p["id"]).payload
    assert pl["status"] == STATUS_CANCELLED
    # A cancelled study is explicitly PARTIAL — never presented as a complete measurement.
    assert pl["partial"] is True


def test_cancelled_study_does_not_corrupt_the_writer_queue(jobs, store):
    """After a cancellation the store's single writer queue is intact — a subsequent study runs and
    persists normally (the cancel path never leaves a half-written transaction)."""
    p = jobs.create(
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"}
    )
    jobs.cancel(p["id"])
    jobs.run_sync(p["id"])
    # The writer queue still works for the next study.
    pl = _run(
        jobs, store,
        {"source_kind": "sim", "source_id": "SIM-BUYER", "setup_type": "trend_continuation", "direction": "long"},
    )
    assert pl["status"] == STATUS_DONE


# --- failure path --------------------------------------------------------------------------------

def test_no_data_historical_yields_explicit_failed_never_empty_success(jobs, store):
    from app.providers.adapters.base import NoDataForWindow

    def _no_data():
        raise NoDataForWindow("AAPL")

    p = jobs.create(
        {"source_kind": "historical", "source_id": "AAPL", "setup_type": "trend_continuation", "direction": "long"}
    )
    jobs.run_sync(p["id"], historical_fetch=_no_data)
    pl = store.get_study(p["id"]).payload
    assert pl["status"] == STATUS_FAILED
    assert "error" in pl and pl["error"]  # an explicit reason, never an empty success
    # A failed study carries NO fabricated occurrences.
    assert pl["aggregates"]["setup"]["n"] == 0
    assert pl["aggregates"]["null_baseline"]["n"] == 0


def test_empty_window_yields_failed(jobs, store):
    class _EmptyWindow:
        symbol = "AAPL"
        trades = ()
        quotes = ()

    def _empty():
        return _EmptyWindow()

    p = jobs.create(
        {"source_kind": "historical", "source_id": "AAPL", "setup_type": "trend_continuation", "direction": "long"}
    )
    jobs.run_sync(p["id"], historical_fetch=_empty)
    pl = store.get_study(p["id"]).payload
    assert pl["status"] == STATUS_FAILED


# --- truncation counted separately ---------------------------------------------------------------

def test_truncated_horizons_are_counted_separately_never_folded(jobs, store):
    pl = _run(
        jobs,
        store,
        {"source_kind": "reference", "source_id": "PG_SIP_REFERENCE", "setup_type": "trend_continuation", "direction": "long"},
    )
    # The null baseline's later horizons are truncated near the window end — counted in their OWN
    # bucket, never folded into the resolved ternary outcomes.
    null = pl["aggregates"]["null_baseline"]
    h120 = next(h for h in null["horizons"] if h["horizon"] == 120.0)
    assert h120["truncated"] > 0
    # The truncated count is separate from the three resolved buckets (no double-counting).
    total = h120["+1R_first"] + h120["-1R_first"] + h120["neither_within_horizon"] + h120["truncated"]
    assert total == null["n"]


# --- occurrence rows mirrored to study_occurrences (first writes to that table) ------------------

def test_occurrence_rows_are_mirrored_to_study_occurrences_table(jobs, store):
    p = jobs.create(
        {"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"}
    )
    jobs.run_sync(p["id"])
    pl = store.get_study(p["id"]).payload
    rows = store.study_occurrence_rows(p["id"])
    # First writes to study_occurrences: setup + null occurrences mirrored verbatim from the payload.
    assert len(rows) == len(pl["occurrences"]) + len(pl["null_occurrences"])


# --- config fingerprint discipline (new study keys MOVE the fingerprint) -------------------------

def test_new_study_keys_move_the_fingerprint():
    base = Config().config_fingerprint()
    assert base != Config(study_null_arm_count=50).config_fingerprint()
    assert base != Config(study_arm_sustain_seconds=9.0).config_fingerprint()
    assert base != Config(study_arm_cooldown_seconds=99.0).config_fingerprint()
    assert base != Config(study_occurrence_r_spread_multiple=5.0).config_fingerprint()
    assert base != Config(study_occurrence_r_floor=0.99).config_fingerprint()
    assert base != Config(study_null_baseline_seed=42).config_fingerprint()


def test_study_list_page_size_is_serving_only_excluded_from_fingerprint():
    # The paired counter to the iter-12 page-size precedent: study_list_max is serving-only.
    base = Config().config_fingerprint()
    assert base == Config(study_list_max=999).config_fingerprint()


def test_a_real_threshold_still_changes_fingerprint():
    base = Config().config_fingerprint()
    assert base != Config(min_buy_price_impact=0.99).config_fingerprint()
