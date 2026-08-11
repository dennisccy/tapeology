"""``desk_playbook_evidence.py`` (Era B2, J-08) -- the pooled evidence fold, the projection cache's
cold/warm/deleted byte-identity, min-n tagging, truncation-exclusion, single-signature pooling,
and the wired ``GET /research/desk/playbook/evidence`` route. Test-first contract: TC-1 through
TC-7 (+ TC-15's suite-floor lives in the full-suite run, not here) in
``docs/phases/goal-playbook-iter-8.md``.

Builds its own hand-crafted ``PlaybookStore`` records directly through the store's public
``record`` writer (never through a real ``compute_playbook``/detector walk -- that path is already
covered end to end by ``test_desk_playbook.py``/``test_desk_playbook_detect.py``) so every pooled
value in every assertion below is a number this file's own hand computation can reproduce, not one
a detector happened to produce. Every per-signal ``forward`` leaf is built through the REAL
``desk_forward._measure_from`` over small synthetic bar lists (the ``test_desk_playbook.py``
``test_measure_signal_and_measure_from_produce_byte_identical_leaves`` precedent) -- never a
hand-typed dict shape that could silently drift from what the rail actually produces."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_forward import DESK_FORWARD_MEASURE_KEYS, _measure_from
from app.research.desk_playbook import PLAYBOOK_MIN_N_DISCLOSURE, PLAYBOOK_SETUPS, PlaybookStore
from app.research.desk_playbook_evidence import (
    EVIDENCE_REGISTER,
    PlaybookEvidenceCache,
    fold_evidence,
    inspect_signature,
)
from app.research.desk_routes import get_playbook_evidence_cache, get_playbook_store
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from test_copy_discipline import find_violations

E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET


def _bar(symbol: str, epoch: float, close: float) -> RawBar:
    """A flat 5m bar (open == high == low == close) -- makes every drawdown/exit-price computation
    trivial by construction, so only the ``return_pct`` this file actually asserts on varies."""
    return RawBar(symbol, "5m", epoch, close, close, close, close, 1000)


def _forward(entry: float, at_1h: float, *, side: str = "long", n_bars: int = 15) -> dict:
    """A REAL ``_measure_from`` leaf: ``n_bars`` flat 5m bars, entry at bar 0, the 1h horizon
    (offset 12 bars on a 5m series) closing at ``at_1h`` -- so ``horizons["1h"]["return_pct"]`` is
    EXACTLY ``sign * (at_1h - entry) / entry * 100.0``, a number this file's own assertions
    hand-compute independently rather than trusting."""
    sign = 1.0 if side == "long" else -1.0
    closes = [entry] * n_bars
    if n_bars > 12:
        closes[12] = at_1h
    bars = [_bar("SYN", E_OPEN + i * 300.0, c) for i, c in enumerate(closes)]
    return _measure_from(bars, 0, entry, "level", 5, sign)


def _truncated_forward(entry: float, exit_price: float, *, side: str = "long") -> dict:
    """A short (5-bar) session -- the 1h horizon (needs offset 12) is unreachable, so every
    signal's ``horizons["1h"]`` measures AT the last bar with ``truncated: True``. Used for TC-4."""
    return _forward(entry, exit_price, side=side, n_bars=5)


def _signal(setup_id: str, side: str, forward: dict, *, breached: dict | None = None) -> dict:
    return {
        "symbol": "SYN",
        "setup_id": setup_id,
        "side": side,
        "geometry": {"slots_to_break": 0},
        "trigger_price": forward["entry_price"],
        "invalidation_price": forward["entry_price"] - 1.0 if side == "long" else forward["entry_price"] + 1.0,
        "entry": forward["entry_price"],
        "entry_kind": forward["entry_kind"],
        "disclosures": {},
        "forward": forward,
        "invalidation_breached": breached
        or {"1m": False, "5m": False, "1h": False, "4h": False, "to_close": False, "first_breach_minutes": None},
    }


def _record(
    store: PlaybookStore,
    session_date: str,
    signature: str,
    signals: list[dict],
    baseline_anchors: dict[str, list[dict]] | None = None,
) -> dict:
    return store.record(
        session_date=session_date,
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=signature,
        payload_version=2,
        parameters={"fixture": True},
        register="fixture register",
        signals=signals,
        absences=[],
        diagnostics=[],
        baseline_anchors=baseline_anchors or {},
    )


SIG_DEFAULT = "current-signature-abc123"
SIG_OLDER = "older-signature-def456"


@pytest.fixture
def store(tmp_path) -> PlaybookStore:
    return PlaybookStore(tmp_path / "playbook")


@pytest.fixture
def bar_store(tmp_path) -> BarStore:
    return BarStore(tmp_path / "bars")


def _members(universe_store: UniverseStore) -> list[str]:
    records, _errors = universe_store.list()
    return list(records[-1]["members"]) if records else []


# --- TC-1: pooling math against a hand-computed fixture ---------------------------------------------


def test_tc1_pooled_1h_cell_matches_the_hand_computed_aggregate(store, bar_store, monkeypatch):
    """Three recorded records at the SAME (current) signature, each contributing exactly one
    (jbe, long) signal plus a scatter of OTHER setups (dbi/capitulation/range_trade) that must
    never leak into the jbe cell. jbe/long/1h return_pct values: 2.0, 4.0, 6.0 -- median 4.0, mean
    4.0, p25 3.0, p75 5.0 (``statistics.quantiles(..., n=4, method="inclusive")`` over [2, 4, 6])."""
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [
            _signal("jbe", "long", _forward(100.0, 102.0)),
            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
            _signal("capitulation", "long", _forward(100.0, 101.0)),
        ],
    )
    _record(
        store, "2026-06-23", SIG_DEFAULT,
        [
            _signal("jbe", "long", _forward(100.0, 104.0)),
            _signal("range_trade", "long", _forward(100.0, 100.5)),
        ],
    )
    _record(
        store, "2026-06-24", SIG_DEFAULT,
        [_signal("jbe", "long", _forward(100.0, 106.0))],
    )

    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    assert body["signature"] == SIG_DEFAULT

    cell = next(
        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 3
    assert cell["signal"]["n_truncated"] == 0
    assert cell["signal"]["median_pct"] == pytest.approx(4.0)
    assert cell["signal"]["mean_pct"] == pytest.approx(4.0)
    assert cell["signal"]["p25_pct"] == pytest.approx(3.0)
    assert cell["signal"]["p75_pct"] == pytest.approx(5.0)
    assert cell["baseline"]["n_baseline"] == 0  # no baseline_anchors planted for this pool key
    assert cell["below_min_n"] is True  # 3 < PLAYBOOK_MIN_N_DISCLOSURE (12)

    # The scattered dbi/capitulation/range_trade signals never leak into the jbe cell.
    dbi_cell = next(
        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
    )
    assert dbi_cell["signal"]["n"] == 1


# --- TC-2: cache cold vs warm byte-identity ----------------------------------------------------------


def test_tc2_cache_cold_and_warm_reads_are_byte_identical(store, bar_store, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])

    cache = PlaybookEvidenceCache(str(tmp_path / "evidence_cache.db"))
    cold = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache)
    warm = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache)
    assert json.dumps(cold, sort_keys=False) == json.dumps(warm, sort_keys=False)


# --- TC-3: below_min_n tags while still serving populated numbers -----------------------------------


def test_tc3_below_min_n_cell_still_serves_populated_numbers(store, bar_store, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [
            _signal("dbi", "short", _forward(100.0, 98.0, side="short")),
            _signal("dbi", "short", _forward(100.0, 97.0, side="short")),
            _signal("dbi", "short", _forward(100.0, 99.0, side="short")),
        ],
    )
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    cell = next(
        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 3 < PLAYBOOK_MIN_N_DISCLOSURE
    assert cell["below_min_n"] is True
    assert cell["signal"]["median_pct"] is not None
    assert cell["signal"]["p25_pct"] is not None
    assert cell["signal"]["p75_pct"] is not None
    assert cell["signal"]["mean_pct"] is not None


def test_a_cell_with_zero_recorded_signals_is_served_as_n0_not_omitted(store, bar_store):
    """Error case: every (setup_id, side, measure) combination is present in ``cells`` even with an
    entirely empty store -- the full declared cross product, never a sparse/omitted set."""
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    assert len(body["cells"]) == len(PLAYBOOK_SETUPS) * 2 * len(DESK_FORWARD_MEASURE_KEYS)
    cell = next(
        c for c in body["cells"]
        if c["setup_id"] == "open_high_break" and c["side"] == "long" and c["measure"] == "1h"
    )
    assert cell["signal"] == {
        "n": 0, "n_truncated": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
    }
    assert cell["baseline"] == {
        "n_baseline": 0, "median_pct": None, "p25_pct": None, "p75_pct": None, "mean_pct": None,
    }
    assert cell["below_min_n"] is True


# --- TC-4: truncated values excluded from the pool, the exclusion counted ---------------------------


def test_tc4_a_truncated_value_is_excluded_from_the_pool_but_counted(store, bar_store, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    untruncated = _forward(100.0, 102.0)
    truncated = _truncated_forward(100.0, 999.0)  # exit_price 999 would wreck the mean if pooled
    assert untruncated["horizons"]["1h"]["truncated"] is False
    assert truncated["horizons"]["1h"]["truncated"] is True

    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [_signal("jbe", "long", untruncated), _signal("jbe", "long", truncated)],
    )
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    cell = next(
        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 1  # the truncated value never entered the pool
    assert cell["signal"]["n_truncated"] == 1
    assert cell["signal"]["mean_pct"] == pytest.approx(2.0)  # untruncated's own return only
    assert cell["signal"]["median_pct"] == pytest.approx(2.0)


# --- T1 (goal-playbook-iter-8 audit): the BASELINE half of the fold -----------------------------
# The audit's finding T1: every fixture above records ``baseline_anchors={}``, so the pooled
# baseline -- the "beside the pooled baseline" half of J-08's whole promise -- had no unit coverage
# at all, and the ``f"{setup_id}:{side}"`` key agreement between ``desk_playbook.py``'s writer and
# ``desk_playbook_evidence.py``'s reader was load-bearing yet unasserted. The auditor verified it by
# hand; these two tests make it a guard, so a rename on either side fails here instead of silently
# serving an empty baseline column beside populated signal numbers.


def test_t1_pooled_baseline_anchors_fold_into_the_baseline_half_of_the_matching_cell(
    store, bar_store, monkeypatch
):
    """Baseline anchors keyed EXACTLY as the writer keys them (``setup_id:side``) pool into that
    cell's ``baseline`` block across files, with their own hand-computed quartiles -- and the
    signal half of the same cell keeps its own, unmixed."""
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    # signals: 1h returns 2.0 and 4.0 -> median 3.0. baselines: 1.0, 3.0, 5.0 -> median 3.0,
    # p25 2.0, p75 4.0, mean 3.0 (statistics.quantiles([1,3,5], n=4, method="inclusive")).
    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [_signal("jbe", "long", _forward(100.0, 102.0))],
        baseline_anchors={"jbe:long": [_forward(100.0, 101.0), _forward(100.0, 103.0)]},
    )
    _record(
        store, "2026-06-23", SIG_DEFAULT,
        [_signal("jbe", "long", _forward(100.0, 104.0))],
        baseline_anchors={"jbe:long": [_forward(100.0, 105.0)]},
    )

    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    cell = next(
        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 2
    assert cell["signal"]["median_pct"] == pytest.approx(3.0)
    assert cell["baseline"]["n_baseline"] == 3  # pooled ACROSS both files, like the signal half
    assert cell["baseline"]["median_pct"] == pytest.approx(3.0)
    assert cell["baseline"]["p25_pct"] == pytest.approx(2.0)
    assert cell["baseline"]["p75_pct"] == pytest.approx(4.0)
    assert cell["baseline"]["mean_pct"] == pytest.approx(3.0)


def test_t1_baseline_anchors_never_leak_across_setup_or_side(store, bar_store, monkeypatch):
    """The pool key is (setup, side) on BOTH halves: a ``dbi:short`` anchor set never appears in
    the ``jbe:long`` cell's baseline, and a cell whose key nothing planted serves an honest zero
    rather than borrowing a neighbour's anchors."""
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [_signal("jbe", "long", _forward(100.0, 102.0)), _signal("dbi", "short", _forward(100.0, 98.0, side="short"))],
        baseline_anchors={"dbi:short": [_forward(100.0, 99.0, side="short")]},
    )
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    jbe = next(
        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
    )
    dbi = next(
        c for c in body["cells"] if c["setup_id"] == "dbi" and c["side"] == "short" and c["measure"] == "1h"
    )
    assert jbe["signal"]["n"] == 1 and jbe["baseline"]["n_baseline"] == 0
    assert jbe["baseline"]["median_pct"] is None  # honest absence, never a fabricated 0.0
    assert dbi["baseline"]["n_baseline"] == 1
    assert dbi["baseline"]["median_pct"] == pytest.approx(1.0)  # short side: (100 - 99)/100 * 100


def test_b1_a_cell_whose_baseline_pool_is_capped_serves_both_counts_and_discloses_why(
    store, bar_store, monkeypatch
):
    """goal-playbook-iter-8 audit, finding B1: ``compute_playbook`` draws ONE baseline anchor per
    signal only while that ``(setup_id, side)`` is within the rail's own
    ``DESK_FORWARD_MAX_TOUCHES_PER_ROW`` pooling cap for the session, while EVERY signal (in-cap or
    beyond) carries a ``forward`` block and enters the signal pool. On the operator's own real
    corpus this bites hard -- ``(double_top, short)`` pools 90 signals against 32 baseline anchors
    -- so the served register must not claim the baseline covers every signal. This fixture
    reproduces the shape (5 signals, 2 anchors) and pins BOTH halves: the two counts are served
    side by side, and ``EVIDENCE_REGISTER`` names the cap as the reason they can differ."""
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(
        store, "2026-06-22", SIG_DEFAULT,
        [_signal("double_top", "short", _forward(100.0, 99.0, side="short")) for _ in range(5)],
        baseline_anchors={"double_top:short": [_forward(100.0, 99.5, side="short") for _ in range(2)]},
    )
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    cell = next(
        c for c in body["cells"]
        if c["setup_id"] == "double_top" and c["side"] == "short" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 5
    assert cell["baseline"]["n_baseline"] == 2  # the capped half, served as its own honest count
    low = body["register"].lower()
    assert "cap" in low and "n_baseline" in low, (
        "EVIDENCE_REGISTER must disclose that the baseline column can cover fewer signals than the "
        "signal column because of the per-setup-and-side pooling cap"
    )
    assert find_violations(body["register"]) == []


# --- TC-5: two signatures -- only the default pools, the other is listed, never merged --------------


def test_tc5_only_the_default_signature_pools_the_other_is_listed_not_merged(store, bar_store, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])
    _record(store, "2026-06-10", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
    _record(store, "2026-06-11", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])

    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    cell = next(
        c for c in body["cells"] if c["setup_id"] == "jbe" and c["side"] == "long" and c["measure"] == "1h"
    )
    assert cell["signal"]["n"] == 1  # the older signature's two signals never entered this pool
    assert cell["signal"]["mean_pct"] == pytest.approx(2.0)

    assert len(body["other_signatures"]) == 1
    other = body["other_signatures"][0]
    assert other["signature"] == SIG_OLDER
    assert other["dates"] == ["2026-06-10", "2026-06-11"]
    assert other["created_span"]["from"] <= other["created_span"]["to"]


def test_inspect_signature_reports_dates_and_created_span_without_pooling(store, bar_store, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(store, "2026-06-10", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
    result = inspect_signature(store, SIG_OLDER)
    assert result == {
        "signature": SIG_OLDER,
        "dates": ["2026-06-10"],
        "created_span": {"from": result["created_span"]["from"], "to": result["created_span"]["to"]},
    }
    assert "cells" not in result and "signals" not in result


def test_inspect_unknown_signature_is_an_honest_empty_not_a_crash(store):
    result = inspect_signature(store, "never-recorded")
    assert result == {"signature": "never-recorded", "dates": [], "created_span": None}


# --- TC-6: deleting the cache DB changes nothing but latency -----------------------------------------


def test_tc6_deleting_the_cache_db_produces_a_byte_identical_rebuild(store, bar_store, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.research.desk_playbook_evidence.compute_playbook_input_signature",
        lambda *_a, **_k: SIG_DEFAULT,
    )
    _record(store, "2026-06-22", SIG_DEFAULT, [_signal("jbe", "long", _forward(100.0, 102.0))])

    db_path = tmp_path / "evidence_cache.db"
    cache1 = PlaybookEvidenceCache(str(db_path))
    before = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache1)

    db_path.unlink()  # the cache DB is gone; nothing in this test touches the playbook store itself

    cache2 = PlaybookEvidenceCache(str(db_path))  # a fresh, empty DB -- every file re-verified
    after = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint(), cache=cache2)

    assert json.dumps(before, sort_keys=False) == json.dumps(after, sort_keys=False)


# --- TC-7: copy-discipline lint on EVIDENCE_REGISTER -------------------------------------------------


def test_tc7_evidence_register_carries_no_forbidden_language(store, bar_store):
    """TC-7: the copy-discipline lint (``find_violations`` -- the SAME function
    ``PLAYBOOK_REGISTER``/``FORWARD_REGISTER`` are checked with) finds nothing to flag. Note this
    is NOT a bare substring ban on {probability, expectancy, edge, significance, advice,
    prediction}: ``PLAYBOOK_REGISTER`` itself already carries "no probability, expectancy, edge, or
    significance claim" as a NEGATED disclosure sentence and is the established, already-shipped
    precedent for exactly this wording -- ``find_violations`` clears a claim word when its own
    sentence carries a negation marker (``not``/``never``/``no``/...), which is the honesty
    mechanism itself, not a violation."""
    assert find_violations(EVIDENCE_REGISTER) == []
    low = EVIDENCE_REGISTER.lower()
    assert "seeded random" in low and "no fills" in low and "no costs" in low
    # A stricter reading of TC-7 than PLAYBOOK_REGISTER's own established precedent (which DOES
    # carry these words in a negated disclosure sentence, e.g. "no probability... claim"):
    # EVIDENCE_REGISTER simply never uses any of the six words at all, so the literal "contains no
    # word from {...}" reading holds too, not just the find_violations negation-clearing reading.
    for banned in ("probability", "expectancy", "edge", "significance", "advice", "prediction"):
        assert banned not in low, f"{banned!r} found in EVIDENCE_REGISTER"
    body = fold_evidence(store, bar_store, [], CONFIG.config_fingerprint())
    assert body["register"] == EVIDENCE_REGISTER


# --- structural guard: the evidence cache class exposes no update/delete method ----------------------


def test_playbook_evidence_cache_has_no_update_or_delete_method():
    assert not hasattr(PlaybookEvidenceCache, "update")
    assert not hasattr(PlaybookEvidenceCache, "delete")


# --- the route, end to end --------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    journal_store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal_store, CONFIG)
    set_registry(registry)
    playbook_store = PlaybookStore(tmp_path / "playbook")
    app.dependency_overrides[get_playbook_store] = lambda: playbook_store
    app.dependency_overrides[get_playbook_evidence_cache] = lambda: None
    with TestClient(app) as c:
        yield c, playbook_store
    app.dependency_overrides.pop(get_playbook_store, None)
    app.dependency_overrides.pop(get_playbook_evidence_cache, None)
    set_registry(None)
    journal_store.close()


def test_route_serves_an_honest_empty_body_before_any_record_exists(client):
    c, _store = client
    response = c.get("/research/desk/playbook/evidence")
    assert response.status_code == 200
    body = response.json()
    assert body["other_signatures"] == []
    assert body["register"] == EVIDENCE_REGISTER
    assert len(body["cells"]) == len(PLAYBOOK_SETUPS) * 2 * len(DESK_FORWARD_MEASURE_KEYS)


def test_route_signature_query_param_inspects_without_pooling(client):
    c, store = client
    _record(store, "2026-06-10", SIG_OLDER, [_signal("jbe", "long", _forward(100.0, 999.0))])
    response = c.get("/research/desk/playbook/evidence", params={"signature": SIG_OLDER})
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "signature": SIG_OLDER, "dates": ["2026-06-10"],
        "created_span": {"from": body["created_span"]["from"], "to": body["created_span"]["to"]},
    }
