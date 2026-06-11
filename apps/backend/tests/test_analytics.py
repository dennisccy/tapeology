"""Segregated journal analytics (capability 31, J-59) — the read-only aggregation module tests.

These pin the binding invariants the iter-16 spec / goal.md J-59 mandate over the SINGLE-owner
``app.research.analytics`` module:

  * **Never pool** — records differing ONLY in ``data_feed`` OR only in ``config_fingerprint`` land
    in DISTINCT partitions (no "all"/pooled rollup anywhere).
  * **Abandonment always visible** — abandoned theses stay in every denominator (``n``) AND surface
    as their own ``abandonment`` count (rendered even when 0; no survivorship pruning).
  * **Insufficient-sample gating** — a group below ``analytics_min_sample_size`` serves the explicit
    ``insufficient_sample`` marker WITH its ``n``; at/above it serves full stats.
  * **Truncated horizons counted separately** — never folded into the ternary resolved buckets,
    never extrapolated.
  * **Acted-trade population structurally disjoint** — entry+exit-marked realized-R kept in its own
    block, never merged with the confirmation-anchored excursion stats.
  * **Median time-to-confirm from the persisted timeline** — declaration → first published
    ``confirming`` event (logical time); honest omission (``None``) with zero confirmations.
  * **Median spread/R** — median of persisted ``spread_at_anchor / r_basis`` beside every +1R figure.
  * **Realized-R reuses the ONE registered R path** — the acted-trade distribution consumes
    ``marks.marks_projection`` (no second formula / inline arithmetic).
  * **Deterministic** — two identical calls over a fixed temp-DB are byte-equal.
  * **Honest empty** — an empty journal yields an empty-but-valid payload (no fabricated groups).
"""

from __future__ import annotations

import pytest

from app.config import CONFIG, Config
from app.research.analytics import compute_analytics
from app.research.store import (
    ActionRecord,
    JournalStore,
    ThesisRecord,
    VerdictEventRecord,
)

FP_A = "fingerprintAAAA01"
FP_B = "fingerprintBBBB02"


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def _thesis(
    tid: str,
    *,
    setup_type: str = "absorption_reversal",
    direction: str = "long",
    status: str = "played_out",
    data_feed: str = "sim",
    config_fingerprint: str = FP_A,
    invalidation_price: float = 99.0,
    excursions: dict | None = None,
    grades: dict | None = None,
    review_tags: list[str] | None = None,
    reviewed: bool = False,
    created_logical_ts: float = 0.0,
) -> ThesisRecord:
    return ThesisRecord(
        id=tid,
        ticker="SIM-BIDABS",
        setup_type=setup_type,
        direction=direction,
        invalidation_price=invalidation_price,
        level_price=None,
        status=status,
        bound_source="bid_absorption",
        data_feed=data_feed,
        config_fingerprint=config_fingerprint,
        entry_context={"last": 100.0, "tape_state": "bid_absorption"},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["bid_absorption"]}}],
        created_logical_ts=created_logical_ts,
        created_wall_ts=1700000000.0,
        excursions=excursions,
        grades=grades,
        review_tags=review_tags,
        reviewed=reviewed,
    )


def _confirmation_excursions(
    *,
    reference_price: float = 100.0,
    invalidation_price: float = 99.0,
    spread_at_anchor: float = 0.02,
    outcomes: dict[float, str | None] | None = None,
    truncated: dict[float, bool] | None = None,
) -> dict:
    """A persisted excursion record with ONLY a confirmation population, per-horizon outcomes set."""
    outcomes = outcomes or {}
    truncated = truncated or {}
    r = abs(reference_price - invalidation_price)
    horizons = [
        {
            "horizon": h,
            "mfe_r": 0.0,
            "mae_r": 0.0,
            "outcome": outcomes.get(h),
            "truncated": truncated.get(h, False),
        }
        for h in CONFIG.excursion_horizons_seconds
    ]
    return {
        "tracked": True,
        "populations": {
            "confirmation": {
                "population": "confirmation",
                "anchor_logical_ts": 0.0,
                "anchor_wall_ts": 0.0,
                "reference_price": reference_price,
                "invalidation_price": invalidation_price,
                "r_basis": r,
                "spread_at_anchor": spread_at_anchor,
                "horizons": horizons,
            }
        },
    }


def _seed_confirming_timeline(store: JournalStore, tid: str, *, confirm_logical_ts: float) -> None:
    """Append a pending declaration event then a published ``confirming`` event (logical time)."""
    store.append_verdict_event(
        VerdictEventRecord(
            thesis_id=tid, logical_ts=0.0, wall_ts=1700000000.0, verdict="pending",
            evidence="declared", tape_state="bid_absorption", confidence=0.5, last=100.0,
        )
    )
    store.append_verdict_event(
        VerdictEventRecord(
            thesis_id=tid, logical_ts=confirm_logical_ts, wall_ts=1700000010.0,
            verdict="confirming", evidence="confirmed", tape_state="buyer_control",
            confidence=0.85, last=100.5,
        )
    )


# --- never-pool ----------------------------------------------------------------------------------

def test_records_differing_only_in_data_feed_land_in_distinct_partitions(store):
    store.insert_thesis(_thesis("t1", data_feed="sim", config_fingerprint=FP_A))
    store.insert_thesis(_thesis("t2", data_feed="iex", config_fingerprint=FP_A))
    result = compute_analytics(store, CONFIG)
    feeds = sorted(p["data_feed"] for p in result["partitions"])
    assert feeds == ["iex", "sim"]
    # Each partition holds exactly one thesis (never pooled across feeds).
    for p in result["partitions"]:
        total = sum(g["n"] for g in p["groups"])
        assert total == 1


def test_records_differing_only_in_fingerprint_land_in_distinct_partitions(store):
    store.insert_thesis(_thesis("t1", data_feed="sim", config_fingerprint=FP_A))
    store.insert_thesis(_thesis("t2", data_feed="sim", config_fingerprint=FP_B))
    result = compute_analytics(store, CONFIG)
    fps = sorted(p["config_fingerprint"] for p in result["partitions"])
    assert fps == sorted([FP_A, FP_B])
    assert len(result["partitions"]) == 2


def test_no_pooled_all_rollup_key_anywhere(store):
    store.insert_thesis(_thesis("t1"))
    result = compute_analytics(store, CONFIG)
    # The top level is partitions + the serving min-sample echo only — no "all"/"pooled"/"total" pool.
    assert set(result.keys()) <= {"partitions", "min_sample_size"}
    for p in result["partitions"]:
        for key in ("all", "pooled", "total", "overall"):
            assert key not in p


# --- abandonment always visible ------------------------------------------------------------------

def test_abandonment_counted_in_n_and_as_its_own_bucket(store):
    # 2 played_out + 1 abandoned, all the same group/partition.
    store.insert_thesis(_thesis("t1", status="played_out"))
    store.insert_thesis(_thesis("t2", status="played_out"))
    store.insert_thesis(_thesis("t3", status="abandoned"))
    result = compute_analytics(store, CONFIG)
    grp = result["partitions"][0]["groups"][0]
    assert grp["n"] == 3                 # abandoned stays in the denominator (no survivorship pruning)
    assert grp["abandonment"] == 1       # and surfaces as its own bucket


def test_abandonment_bucket_present_even_when_zero(store):
    store.insert_thesis(_thesis("t1", status="played_out"))
    result = compute_analytics(store, CONFIG)
    grp = result["partitions"][0]["groups"][0]
    assert grp["abandonment"] == 0       # rendered even when 0 (always visible)


# --- insufficient-sample gating ------------------------------------------------------------------

def test_group_below_min_sample_serves_marker_with_n(store):
    cfg = Config(analytics_min_sample_size=3)
    store.insert_thesis(_thesis("t1"))
    store.insert_thesis(_thesis("t2"))
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    assert grp["insufficient_sample"] is True
    assert grp["n"] == 2                 # n still present (never a bare marker)


def test_group_at_min_sample_serves_full_stats(store):
    cfg = Config(analytics_min_sample_size=3)
    for i in range(3):
        store.insert_thesis(_thesis(f"t{i}"))
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    assert grp["insufficient_sample"] is False
    assert grp["n"] == 3


# --- truncated horizons counted separately -------------------------------------------------------

def test_truncated_horizon_counted_separately_never_in_ternary_buckets(store):
    h10, h30 = CONFIG.excursion_horizons_seconds[0], CONFIG.excursion_horizons_seconds[1]
    # t1: 10s resolved +1R; t2: 10s truncated (outcome None, truncated True).
    store.insert_thesis(
        _thesis("t1", excursions=_confirmation_excursions(outcomes={h10: "+1R_first"}))
    )
    store.insert_thesis(
        _thesis("t2", excursions=_confirmation_excursions(outcomes={h10: None}, truncated={h10: True}))
    )
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    horizons = {h["horizon"]: h for h in grp["confirmation_excursions"]["horizons"]}
    h10row = horizons[h10]
    assert h10row["+1R_first"] == 1
    assert h10row["truncated"] == 1
    # The truncated one is NOT pooled into any resolved ternary bucket.
    assert h10row["-1R_first"] == 0
    assert h10row["neither_within_horizon"] == 0


# --- median spread/R beside +1R ------------------------------------------------------------------

def test_median_spread_per_r_from_persisted_anchor_and_basis(store):
    h10 = CONFIG.excursion_horizons_seconds[0]
    # Two confirmation theses: spread 0.02 / R 1.0 => 0.02; spread 0.04 / R 1.0 => 0.04. Median 0.03.
    store.insert_thesis(
        _thesis("t1", excursions=_confirmation_excursions(
            spread_at_anchor=0.02, reference_price=100.0, invalidation_price=99.0,
            outcomes={h10: "+1R_first"}))
    )
    store.insert_thesis(
        _thesis("t2", excursions=_confirmation_excursions(
            spread_at_anchor=0.04, reference_price=100.0, invalidation_price=99.0,
            outcomes={h10: "+1R_first"}))
    )
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    horizons = {h["horizon"]: h for h in grp["confirmation_excursions"]["horizons"]}
    assert horizons[h10]["median_spread_per_r"] == pytest.approx(0.03)


# --- median time-to-confirm ----------------------------------------------------------------------

def test_median_time_to_confirm_from_persisted_timeline(store):
    # Two theses confirming at logical 20s and 40s respectively => median 30s.
    store.insert_thesis(_thesis("t1"))
    store.insert_thesis(_thesis("t2"))
    _seed_confirming_timeline(store, "t1", confirm_logical_ts=20.0)
    _seed_confirming_timeline(store, "t2", confirm_logical_ts=40.0)
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    assert grp["median_time_to_confirm"] == pytest.approx(30.0)


def test_median_time_to_confirm_omitted_with_zero_confirmations(store):
    store.insert_thesis(_thesis("t1"))  # only a pending declaration, never confirms
    store.append_verdict_event(
        VerdictEventRecord(
            thesis_id="t1", logical_ts=0.0, wall_ts=1700000000.0, verdict="pending",
            evidence="declared", tape_state="bid_absorption", confidence=0.5, last=100.0,
        )
    )
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    assert grp["median_time_to_confirm"] is None   # honest omission, never a fabricated zero


# --- tag frequencies (user-confirmed only) -------------------------------------------------------

def test_tag_frequencies_count_only_user_confirmed_reviews(store):
    store.insert_thesis(_thesis("t1", reviewed=True, review_tags=["chased", "overstayed"]))
    store.insert_thesis(_thesis("t2", reviewed=True, review_tags=["chased"]))
    # An unreviewed thesis with NO review_tags contributes nothing (machine suggestions never counted).
    store.insert_thesis(_thesis("t3", reviewed=False, review_tags=None))
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    freq = {t["tag"]: t["count"] for t in grp["tag_frequencies"]}
    assert freq.get("chased") == 2
    assert freq.get("overstayed") == 1


# --- acted-trade population structurally disjoint ------------------------------------------------

def test_acted_trade_population_separate_from_confirmation(store):
    h10 = CONFIG.excursion_horizons_seconds[0]
    # An entry+exit-marked thesis: realized-R via marks.py. Long, entry 100, exit 101, inval 99 => +1R.
    store.insert_thesis(
        _thesis("t1", direction="long", invalidation_price=99.0,
                excursions=_confirmation_excursions(outcomes={h10: "+1R_first"}))
    )
    store.insert_action(ActionRecord(id="a1", thesis_id="t1", kind="entry", price=100.0,
                                     logical_ts=1.0, wall_ts=1700000001.0, spread_at_mark=0.02))
    store.insert_action(ActionRecord(id="a2", thesis_id="t1", kind="exit", price=101.0,
                                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=0.02))
    cfg = Config(analytics_min_sample_size=1)
    result = compute_analytics(store, cfg)
    grp = result["partitions"][0]["groups"][0]
    # The acted-trade block exists and is keyed separately from confirmation_excursions.
    assert "acted_trade" in grp
    assert "confirmation_excursions" in grp
    assert grp["acted_trade"] is not grp["confirmation_excursions"]
    assert grp["acted_trade"]["n"] == 1
    # Realized-R is the marks.py value (+1.0R for this long), never recomputed by a second formula.
    assert grp["acted_trade"]["median_realized_r"] == pytest.approx(1.0)


def test_acted_trade_reuses_marks_projection(monkeypatch, store):
    """The acted-trade distribution MUST consume marks.marks_projection (the ONE registered R path)."""
    import app.research.analytics as analytics_mod

    calls = {"n": 0}
    real = analytics_mod.marks_projection

    def _spy(thesis, actions):
        calls["n"] += 1
        return real(thesis, actions)

    monkeypatch.setattr(analytics_mod, "marks_projection", _spy)
    store.insert_thesis(_thesis("t1", direction="long", invalidation_price=99.0))
    store.insert_action(ActionRecord(id="a1", thesis_id="t1", kind="entry", price=100.0,
                                     logical_ts=1.0, wall_ts=1700000001.0, spread_at_mark=0.02))
    store.insert_action(ActionRecord(id="a2", thesis_id="t1", kind="exit", price=101.0,
                                     logical_ts=5.0, wall_ts=1700000005.0, spread_at_mark=0.02))
    cfg = Config(analytics_min_sample_size=1)
    compute_analytics(store, cfg)
    assert calls["n"] >= 1   # the registered marks projection was used (no second formula)


# --- determinism + honest empty ------------------------------------------------------------------

def test_two_identical_calls_are_byte_equal(store):
    h10 = CONFIG.excursion_horizons_seconds[0]
    store.insert_thesis(_thesis("t1", excursions=_confirmation_excursions(outcomes={h10: "+1R_first"})))
    store.insert_thesis(_thesis("t2", status="abandoned"))
    cfg = Config(analytics_min_sample_size=1)
    import json
    a = json.dumps(compute_analytics(store, cfg), sort_keys=True)
    b = json.dumps(compute_analytics(store, cfg), sort_keys=True)
    assert a == b


def test_empty_journal_yields_honest_empty_payload(store):
    result = compute_analytics(store, CONFIG)
    assert result["partitions"] == []
    assert result["min_sample_size"] == CONFIG.analytics_min_sample_size
