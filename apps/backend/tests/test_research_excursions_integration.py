"""Excursion wiring through the REAL research stack (capability 30, J-58) — the monitor + store +
journal-detail integration matrix.

Drives the J-58 script's exact shape through the real ``ResearchMonitor`` + ``JournalStore`` (no
FastAPI): declare a trend_continuation / long thesis on SIM-BUYER, run the seeded stream through the
monitor's ``on_event`` until the published ``confirming`` arms the confirmation population, record an
ENTRY mark (arming the entry population), run to the stream end, fire ``on_status('closed')`` so the
ENTRY-marked thesis SURVIVES active-but-not-evaluated — and assert the excursion record is persisted
ONCE at that survival path and served verbatim by ``build_journal_detail`` with the two segregated
populations. Also covers: the unmarked-expiry path, the not-tracked restart-sweep marker, the
no-confirmation honest absence, and the byte-identical determinism re-run.
"""

import itertools
import json

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.monitor import ResearchMonitor, data_feed_for_scenario
from app.research.routes import build_journal_detail
from app.research.store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
from app.research.taxonomy import frozen_statements


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def _declare(store: JournalStore, *, invalidation: float = 98.0) -> ThesisRecord:
    """Insert a trend_continuation / long SIM-BUYER thesis (the J-42/J-58 substrate) + its initial
    pending timeline event, exactly as the declare route does."""
    thesis = ThesisRecord(
        id="t-exc", ticker="SIM-BUYER", setup_type="trend_continuation", direction="long",
        invalidation_price=invalidation, level_price=None, status="active",
        bound_source="buyer_control", data_feed="sim",
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={"last": 100.0, "tape_state": "buyer_control"},
        statements=frozen_statements("trend_continuation", "long"),
        created_logical_ts=0.0, created_wall_ts=1700000000.0,
    )
    store.insert_thesis_with_event(
        thesis,
        VerdictEventRecord(
            thesis_id=thesis.id, logical_ts=0.0, wall_ts=1700000000.0, verdict="pending",
            evidence="Thesis declared.", tape_state="buyer_control", confidence=0.8, last=100.0,
        ),
    )
    return thesis


def _run_to_survival(
    store: JournalStore, thesis: ThesisRecord, *, stop_after: int = 400, mark_entry: bool = True
) -> ResearchMonitor:
    """Attach a monitor, run SIM-BUYER through ``on_event`` (arming confirmation at the first
    published confirming), optionally record + arm an ENTRY mark just after confirmation, run to the
    cut, then fire ``on_status('closed')`` — the ENTRY-marked thesis SURVIVES (the survival path
    persists excursions); an unmarked thesis EXPIRES (the expiry path persists them)."""
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    entered = False
    for event in itertools.islice(SimulatedProvider("SIM-BUYER", "buyer_control").stream(), stop_after):
        snap = engine.process_event(event)
        monitor.on_event(None, snap)
        # Record the entry mark a few seconds after the first confirmation publishes.
        if mark_entry and not entered and monitor._verdict == "confirming" and snap.timestamp > 26.0:
            action = ActionRecord(
                id="a-entry", thesis_id=thesis.id, kind="entry", price=snap.last,
                logical_ts=snap.timestamp, wall_ts=1700000030.0, spread_at_mark=snap.spread,
            )
            store.insert_action(action)
            monitor.arm_entry_excursions(
                logical_ts=snap.timestamp, wall_ts=1700000030.0, price=snap.last,
                spread_at_mark=snap.spread,
            )
            entered = True
    # The engine's end_reason would be stream_closed on real exhaustion; fire the terminal status.
    monitor.on_status("closed")
    return monitor


# --- the J-58 survival path: an entry-marked thesis survives, excursions persisted there ---------

def test_entry_marked_thesis_survives_and_excursions_persist_with_two_populations(store):
    thesis = _declare(store)
    _run_to_survival(store, thesis, mark_entry=True)
    # The thesis SURVIVES (still active — an entry-marked position is never orphaned).
    back = store.get_thesis(thesis.id)
    assert back.status == "active"
    # Excursions were persisted at the survival path with BOTH populations, fully segregated.
    detail = build_journal_detail(store, thesis.id, CONFIG)
    exc = detail["excursions"]
    assert exc["tracked"] is True
    pops = exc["populations"]
    assert "confirmation" in pops and "entry" in pops
    conf, entry = pops["confirmation"], pops["entry"]
    # Independent anchors + independent R bases (never pooled).
    assert conf["reference_price"] != entry["reference_price"]
    assert conf["anchor_logical_ts"] != entry["anchor_logical_ts"]
    assert conf["r_basis"] > 0 and entry["r_basis"] > 0
    # Each population reports every configured horizon with a ternary outcome OR a truncated flag, in
    # R units (no currency anywhere in the served record).
    for pop in (conf, entry):
        horizons = {h["horizon"] for h in pop["horizons"]}
        assert horizons == set(CONFIG.excursion_horizons_seconds)
        for h in pop["horizons"]:
            assert (h["outcome"] is not None) or (h["truncated"] is True)
    # At least one COMPLETED and at least one TRUNCATED horizon on the confirmation population (the
    # spec's calibration requirement, proven through the real stack).
    assert any(h["truncated"] for h in conf["horizons"])
    assert any((not h["truncated"]) and h["outcome"] is not None for h in conf["horizons"])
    # Spread-at-anchor present on both (a moment value).
    assert conf["spread_at_anchor"] is not None
    assert entry["spread_at_anchor"] is not None


def test_excursions_persisted_once_not_recomputed_at_read(store):
    # Persist-once: a second build_journal_detail read returns byte-identical excursions (never
    # recomputed at read) and the persisted thesis row already carries them.
    thesis = _declare(store)
    _run_to_survival(store, thesis, mark_entry=True)
    a = build_journal_detail(store, thesis.id, CONFIG)["excursions"]
    b = build_journal_detail(store, thesis.id, CONFIG)["excursions"]
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert store.get_thesis(thesis.id).excursions == a


def _strip_wall(record: dict) -> dict:
    """Drop the ``anchor_wall_ts`` true-clock display fields (inherently wall-clock — like every
    timeline ``wall_ts`` the codebase never determinism-checks). The MEASURED excursion values — the
    R bases, MFE/MAE, ternary outcomes, truncation flags, logical anchors, reference prices, and
    spreads — are what J-58's determinism clause pins."""
    import copy
    out = copy.deepcopy(record)
    for pop in out.get("populations", {}).values():
        pop.pop("anchor_wall_ts", None)
    return out


def test_determinism_identical_run_yields_byte_identical_excursions(store, tmp_path):
    # J-58's determinism clause through the real stack: the identical seeded scenario + arming sequence
    # yields byte-identical MEASURED excursion values (R bases, MFE/MAE, ternary outcomes, truncation,
    # logical anchors, reference prices, spreads). The only run-to-run difference is the wall-clock
    # display anchor (never a measured value, never determinism-checked anywhere in the codebase).
    thesis1 = _declare(store)
    _run_to_survival(store, thesis1, mark_entry=True)
    rec1 = store.get_thesis(thesis1.id).excursions

    store2 = JournalStore(str(tmp_path / "journal2.db"), CONFIG)
    try:
        thesis2 = _declare(store2)
        _run_to_survival(store2, thesis2, mark_entry=True)
        rec2 = store2.get_thesis(thesis2.id).excursions
    finally:
        store2.close()
    assert json.dumps(_strip_wall(rec1), sort_keys=True) == json.dumps(_strip_wall(rec2), sort_keys=True)


# --- the unmarked expiry path: excursions persisted at stream-end expiry --------------------------

def test_unmarked_thesis_expires_and_excursions_persist_confirmation_only(store):
    thesis = _declare(store)
    _run_to_survival(store, thesis, mark_entry=False)
    back = store.get_thesis(thesis.id)
    assert back.status == "expired"  # unmarked => expired at stream end
    exc = build_journal_detail(store, thesis.id, CONFIG)["excursions"]
    assert exc["tracked"] is True
    # Confirmation armed (the thesis confirmed), but NO entry population (no mark) — honest absence.
    assert "confirmation" in exc["populations"]
    assert "entry" not in exc["populations"]


# --- the not-tracked restart-sweep marker ---------------------------------------------------------

def test_restart_sweep_persists_not_tracked_marker(store):
    # A thesis left active from a prior process with NO entry mark: the startup sweep expires it and
    # persists the explicit not-tracked marker (no in-memory tracker to measure from) — never numbers.
    from app.research.excursions import compute_and_persist_excursions

    thesis = _declare(store)
    expired = store.expire_stale_actives(1700000100.0)
    assert thesis.id in expired
    # The sweep path passes tracker=None (no live tracker on a restart).
    compute_and_persist_excursions(store, thesis.id, None)
    exc = build_journal_detail(store, thesis.id, CONFIG)["excursions"]
    assert exc == {"tracked": False, "populations": {}}


# --- honest absence: a thesis that never confirms has no confirmation population ------------------

def test_no_confirmation_means_no_confirmation_population(store):
    # SIM-BIDABS never confirms a long trend_continuation; an UNMARKED such thesis expires at stream
    # end with NO confirmation population (never armed) and NO entry population (no mark).
    thesis = ThesisRecord(
        id="t-bidabs", ticker="SIM-BIDABS", setup_type="trend_continuation", direction="long",
        invalidation_price=98.0, level_price=None, status="active", bound_source="bid_absorption",
        data_feed="sim", config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={"last": 100.0}, statements=frozen_statements("trend_continuation", "long"),
        created_logical_ts=0.0, created_wall_ts=1700000000.0,
    )
    store.insert_thesis_with_event(
        thesis,
        VerdictEventRecord(
            thesis_id=thesis.id, logical_ts=0.0, wall_ts=1700000000.0, verdict="pending",
            evidence="Thesis declared.", tape_state="bid_absorption", confidence=0.7, last=100.0,
        ),
    )
    monitor = ResearchMonitor(store, CONFIG)
    monitor.set_thesis(thesis)
    engine = TapeEngine("SIM-BIDABS", "bid_absorption", CONFIG)
    for event in itertools.islice(SimulatedProvider("SIM-BIDABS", "bid_absorption").stream(), 400):
        monitor.on_event(None, engine.process_event(event))
    monitor.on_status("closed")
    exc = build_journal_detail(store, thesis.id, CONFIG)["excursions"]
    assert exc["tracked"] is True
    assert exc["populations"] == {}  # never confirmed, never marked => both populations absent
