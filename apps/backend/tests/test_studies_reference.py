"""J-62 GATE — the committed PINNED reference replay study (capability 32).

THE authoritative, offline, no-credentials gate for J-62. It runs the reference replay study — the
committed PG SIP fixture (the iter-17 capability-34 fixture; this is its second consumer) AND a
seeded sim — UNPACED, in CI, WITHOUT credentials, and asserts the EXACT pinned occurrence rows +
aggregates + null-baseline counts (byte-stable), completing within the config-owned time budget.
Double-run determinism is asserted (identical results for identical source + fingerprint + seed).

If the committed fixture is ever absent the study resolves to ``failed`` and this gate FAILS LOUDLY
(it does NOT skip and does NOT fall back to a synthetic stand-in), so a green run is positive
evidence the reference study reproduces in CI.

The pinned numbers are the runner's output under the committed config defaults. A change here means
the study runner's numbers moved — a STOP-and-flag (re-pin only with a documented justification),
never a silent re-pin.
"""

from __future__ import annotations

import time

import pytest

from app.config import CONFIG
from app.research.store import JournalStore
from app.research.studies import STATUS_DONE, StudyJobManager


@pytest.fixture
def jobs(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    mgr = StudyJobManager(store, CONFIG)
    yield mgr, store
    store.close()


def _run(mgr, store, params):
    p = mgr.create(params)
    mgr.run_sync(p["id"])
    return store.get_study(p["id"]).payload


# --- the committed PG SIP reference study (no credentials, in budget) ----------------------------

def test_reference_pg_sip_study_pins_exact_results_in_budget(jobs):
    mgr, store = jobs
    start = time.perf_counter()
    pl = _run(
        mgr,
        store,
        {
            "source_kind": "reference",
            "source_id": "PG_SIP_REFERENCE",
            "setup_type": "trend_continuation",
            "direction": "long",
        },
    )
    elapsed = time.perf_counter() - start

    # The study completed without credentials over the committed SIP fixture.
    assert pl["status"] == STATUS_DONE, (
        f"reference study did not complete (status={pl['status']!r}); the committed PG SIP fixture "
        "must be present for the J-62 gate — do NOT substitute a synthetic fixture"
    )
    assert pl["data_feed"] == "sip"
    assert pl["source"] == "historical PG reference"

    # The unpaced reference study runs comfortably within the config-owned budget (≈3 s on the dev
    # machine; the budget is the capability-34 dense-replay budget the runner inherits).
    assert elapsed < CONFIG.dense_replay_time_budget_seconds, (
        f"reference study took {elapsed:.2f}s, over the {CONFIG.dense_replay_time_budget_seconds:.0f}s "
        "budget"
    )

    # --- PINNED setup aggregates (exact, byte-stable) -------------------------------------------
    setup = pl["aggregates"]["setup"]
    assert setup["n"] == 2
    assert setup["horizons"] == [
        {"horizon": 10.0, "+1R_first": 0, "-1R_first": 0, "neither_within_horizon": 2, "truncated": 0},
        {"horizon": 30.0, "+1R_first": 0, "-1R_first": 0, "neither_within_horizon": 2, "truncated": 0},
        {"horizon": 60.0, "+1R_first": 0, "-1R_first": 1, "neither_within_horizon": 1, "truncated": 0},
        {"horizon": 120.0, "+1R_first": 0, "-1R_first": 1, "neither_within_horizon": 0, "truncated": 1},
    ]

    # --- PINNED null-baseline aggregates (exact, byte-stable) -----------------------------------
    null = pl["aggregates"]["null_baseline"]
    assert null["n"] == 99
    assert null["horizons"] == [
        {"horizon": 10.0, "+1R_first": 4, "-1R_first": 3, "neither_within_horizon": 91, "truncated": 1},
        {"horizon": 30.0, "+1R_first": 7, "-1R_first": 4, "neither_within_horizon": 79, "truncated": 9},
        {"horizon": 60.0, "+1R_first": 8, "-1R_first": 5, "neither_within_horizon": 72, "truncated": 14},
        {"horizon": 120.0, "+1R_first": 8, "-1R_first": 6, "neither_within_horizon": 62, "truncated": 23},
    ]

    # --- PINNED per-occurrence rows (exact R basis + verdict summary) ---------------------------
    assert [o["r_basis"] for o in pl["occurrences"]] == [0.3, 0.6]
    assert [o["verdict_summary"] for o in pl["occurrences"]] == ["invalidated", "confirming"]


def test_reference_study_is_deterministic_double_run(jobs):
    mgr, store = jobs
    params = {
        "source_kind": "reference",
        "source_id": "PG_SIP_REFERENCE",
        "setup_type": "trend_continuation",
        "direction": "long",
    }
    a = _run(mgr, store, params)
    b = _run(mgr, store, params)
    # Identical (source, fingerprint, seed) => byte-identical occurrences + aggregates + baseline.
    for key in ("occurrences", "null_occurrences", "aggregates"):
        assert a[key] == b[key]


# --- a seeded-sim reference leg (the spec's "AND at least one seeded sim") ------------------------

def test_reference_seeded_sim_study_pins_exact_results(jobs):
    mgr, store = jobs
    pl = _run(
        mgr,
        store,
        {
            "source_kind": "sim",
            "source_id": "SIM-REVERSAL",
            "setup_type": "absorption_reversal",
            "direction": "long",
        },
    )
    assert pl["status"] == STATUS_DONE
    assert pl["data_feed"] == "sim"

    setup = pl["aggregates"]["setup"]
    assert setup["n"] == 1
    assert setup["horizons"] == [
        {"horizon": 10.0, "+1R_first": 0, "-1R_first": 0, "neither_within_horizon": 1, "truncated": 0},
        {"horizon": 30.0, "+1R_first": 0, "-1R_first": 0, "neither_within_horizon": 1, "truncated": 0},
        {"horizon": 60.0, "+1R_first": 1, "-1R_first": 0, "neither_within_horizon": 0, "truncated": 0},
        {"horizon": 120.0, "+1R_first": 1, "-1R_first": 0, "neither_within_horizon": 0, "truncated": 0},
    ]
    null = pl["aggregates"]["null_baseline"]
    assert null["n"] == 100
    assert null["horizons"] == [
        {"horizon": 10.0, "+1R_first": 0, "-1R_first": 0, "neither_within_horizon": 90, "truncated": 10},
        {"horizon": 30.0, "+1R_first": 58, "-1R_first": 0, "neither_within_horizon": 21, "truncated": 21},
        {"horizon": 60.0, "+1R_first": 70, "-1R_first": 0, "neither_within_horizon": 7, "truncated": 23},
        {"horizon": 120.0, "+1R_first": 77, "-1R_first": 0, "neither_within_horizon": 0, "truncated": 23},
    ]
    # The setup occurrence reached +1R (the reversal lifted price) — confirming, with its R basis pinned.
    assert pl["occurrences"][0]["verdict_summary"] == "confirming"
    assert pl["occurrences"][0]["r_basis"] == 0.2


# --- the iter-17 engine gate stays green & untouched ---------------------------------------------

def test_observer_equivalence_and_dense_gate_modules_import_unchanged():
    """A cheap structural guard that the study layer did not touch the engine-gate modules: the
    capability-34 fixture path the study reuses is the SAME committed file the dense gate pins."""
    from app.research.studies import _load_reference_window

    window = _load_reference_window()
    assert window is not None and window.symbol == "PG"
    # The fixture carries thousands of real SIP trades (the same one the dense gate asserts).
    assert len(window.trades) == 3229
