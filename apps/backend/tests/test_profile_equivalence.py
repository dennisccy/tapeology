"""Versioned indicator profiles (era-3 capability 2, J-06) — the config-owned registry plus the
per-run overlay that lets a backtest select a candidate WITHOUT ever perturbing the frozen
``default`` engine path (Data Contract row 33).

Locked disciplines (each a J-06 acceptance clause or a coherence watchpoint):
  * ONE registry source — ``Config.profile_definition`` / ``Config.profile_registry`` — feeds
    BOTH ``GET /research/profiles`` (``app/research/profiles.py``) and the backtest route's
    validation; there is no second allowlist anywhere.
  * ``default`` resolves to the SAME ``Config`` object, unchanged (the strongest possible
    byte-identical guarantee) — proven here against BOTH a literal pinned fingerprint and a
    pinned replay of the committed PG SIP reference fixture.
  * The ONE registered candidate is a genuinely ADDITIVE alternate threshold
    (``warmup_min_events``, applied ONLY inside a per-run overlay ``Config`` via
    ``dataclasses.replace`` — never a mutation of the shared ``CONFIG`` singleton) and is proven
    to legitimately move classified output (a real ``tape_state`` flip, not merely a confidence
    nudge) on the committed fixture — the iter-4 "make it fire" lesson.
  * ``config_fingerprint`` folds the profile through the ONE existing hasher: the candidate's
    distinct fingerprint comes from the overlaid, always-hashed ``warmup_min_events`` field, not
    a second mechanism. The new registry-metadata field itself
    (``profile_candidate_warmup_min_events``) is excluded so its mere existence never moves
    ``default``'s fingerprint (pinned against the founding PnL-ledger row's committed value).
  * No engine/cockpit path outside the backtest run param may ever resolve a profile (a
    source-scan guard).

era-5D J-02 ("The Clean Slate" demolition interlude): this file's own
``test_performance_page_offers_no_profile_selection_control`` guarded the now-deleted
``/performance`` panel's "no selection control" constraint by reading that page's source file
directly; the page is deleted whole (not merely stripped of its selector), so there is nothing
left to read and the test is removed with it. Nothing else in this file concerns that page — the
registry/config-fingerprint/backtest-overlay coverage below is untouched and stays byte-identical.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from app.config import (
    CONFIG,
    PROFILE_CANDIDATE_FASTER_WARMUP,
    PROFILE_DEFAULT,
    STRATEGY_V1_ID,
)
from app.research.backtests import BacktestJobManager, STATUS_DONE
from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore, record_from_source
from app.research.store import JournalStore

BACKEND_DIR = Path(__file__).resolve().parents[1]
_PRIMARY = CONFIG.primary_window_label

# The SAME founding windows the PnL ledger's founding row measures (config-owned — no literal
# duplication of the dates/times anywhere in this file).
TRAIN_WINDOW = CONFIG.pnl_founding_train_window
HOLDOUT_WINDOW = CONFIG.pnl_founding_holdout_window


def _register(store: DatasetStore, *, split: str, window: tuple[str, str]) -> dict:
    return record_from_source(
        store,
        source_kind="reference",
        source_id="PG_SIP_REFERENCE",
        split=split,
        start=window[0],
        end=window[1],
        config=CONFIG,
    )


# --- the registry itself: ONE source, config-owned, mirrors the strategy_definition pattern -------


def test_profile_registry_lists_default_and_the_registered_candidate():
    registry = CONFIG.profile_registry()
    assert [p["id"] for p in registry] == [PROFILE_DEFAULT, PROFILE_CANDIDATE_FASTER_WARMUP]
    default, candidate = registry
    assert default == {"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}
    assert candidate["frozen"] is False
    assert candidate["is_default"] is False
    assert candidate["based_on"] == PROFILE_DEFAULT
    assert candidate["overrides"] == {"warmup_min_events": CONFIG.profile_candidate_warmup_min_events}


def test_profile_definition_unknown_id_is_none():
    assert CONFIG.profile_definition("nonexistent-profile") is None
    assert CONFIG.profile_definition("") is None


# --- resolution: default is IDENTITY; the candidate is a scoped, non-mutating overlay --------------


def test_resolved_for_profile_default_is_the_same_object_unchanged():
    # The strongest possible "byte-identical" guarantee: default resolves to the IDENTICAL Config
    # object — no new instance, no copy, nothing that could ever drift from the live cockpit's
    # own config (the frozen-default anti-goal).
    assert CONFIG.resolved_for_profile(PROFILE_DEFAULT) is CONFIG


def test_resolved_for_profile_candidate_overlays_only_its_declared_field():
    resolved = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
    assert resolved is not CONFIG
    assert resolved.warmup_min_events == CONFIG.profile_candidate_warmup_min_events
    assert resolved.warmup_min_events != CONFIG.warmup_min_events
    # Every OTHER field is untouched: putting warmup_min_events back reproduces CONFIG exactly
    # (proves the overlay is scoped to ONLY its declared additive override).
    assert dataclasses.replace(resolved, warmup_min_events=CONFIG.warmup_min_events) == CONFIG


def test_resolved_for_profile_unknown_id_is_none():
    assert CONFIG.resolved_for_profile("nonexistent-profile") is None


# --- config_fingerprint: the ONE existing hasher, default untouched, candidate distinct -------------


def test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field():
    # Ground truth: the founding PnL-ledger row (reports/pnl/pnl-history.md, committed) was
    # appended under THIS exact fingerprint. If this pin ever moves, that row (and every
    # archived-era record) has silently drifted — the strongest guard against that.
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"


def test_profile_candidate_field_is_serving_only_excluded_from_fingerprint():
    # Registry metadata only (the value resolved_for_profile OVERLAYS onto the real
    # warmup_min_events field) — never itself read by engine/classifier code, so its mere
    # presence (at ANY value) must not move ANY existing fingerprint.
    base = CONFIG.config_fingerprint()
    bumped = dataclasses.replace(CONFIG, profile_candidate_warmup_min_events=999).config_fingerprint()
    assert bumped == base


def test_candidate_resolved_fingerprint_is_distinct_from_default():
    resolved = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)
    assert resolved.config_fingerprint() != CONFIG.config_fingerprint()
    assert resolved.config_fingerprint() == "16d7c98e4fdca755"


def test_a_real_classifier_threshold_still_changes_the_fingerprint():
    # The counter-test every fingerprint-exclusion claim in this file needs (the established
    # test_backtests.py / test_datasets.py precedent).
    assert dataclasses.replace(CONFIG, min_aggressive_buy_ratio=0.61).config_fingerprint() != (
        CONFIG.config_fingerprint()
    )


# --- the pinned default-equivalence test (J-06 acceptance: byte-identical vs pre-profile) ----------


def test_default_profile_replay_pins_exact_state_confidence_and_features(tmp_path):
    """Replays the committed PG SIP reference fixture (the SAME windows the founding PnL row
    measures) through the SAME production path the backtest runner uses
    (``DatasetStore.replay``) under the profile-resolved ``default`` config, and asserts the
    first AND last snapshot of each split match values pinned BEFORE this iteration's Config
    change — proving the profile machinery is a pure additive overlay that never perturbs the
    frozen default path."""
    store = DatasetStore(tmp_path / "datasets")
    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
    holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)

    run_config = CONFIG.resolved_for_profile(PROFILE_DEFAULT)
    train_snaps = list(store.replay(train["id"], run_config))
    holdout_snaps = list(store.replay(holdout["id"], run_config))

    assert len(train_snaps) == 1321
    assert len(holdout_snaps) == 1158

    first, last = train_snaps[0], train_snaps[-1]
    assert (first.tape_state, first.confidence, first.warm, first.event_count) == ("unclear", 0.1, False, 0)
    assert (last.tape_state, last.confidence, last.warm, last.event_count) == (
        "seller_control",
        0.7562609836229536,
        True,
        376,
    )
    feat = last.features[_PRIMARY]
    assert feat["buy_price_impact"] == pytest.approx(1.8245000000000573)
    assert feat["sell_price_impact"] == pytest.approx(-1.9235000000000468)
    assert feat["aggressive_buy_ratio"] == pytest.approx(0.3408139977177634)

    first, last = holdout_snaps[0], holdout_snaps[-1]
    assert (first.tape_state, first.confidence, first.warm, first.event_count) == ("unclear", 0.1, False, 0)
    assert (last.tape_state, last.confidence, last.warm, last.event_count) == (
        "buyer_control",
        0.741002066460636,
        True,
        228,
    )
    feat = last.features[_PRIMARY]
    assert feat["buy_price_impact"] == pytest.approx(2.452000000000055)
    assert feat["sell_price_impact"] == pytest.approx(-2.1690000000000396)
    assert feat["aggressive_buy_ratio"] == pytest.approx(0.6422896352473817)

    # Double-run determinism (re-runs are byte-identical — the row-30 replay guarantee).
    train_again = list(store.replay(train["id"], run_config))
    assert [(s.tape_state, s.confidence) for s in train_snaps] == [
        (s.tape_state, s.confidence) for s in train_again
    ]


def test_default_profile_replay_matches_plain_config_replay_exactly(tmp_path):
    # A second, independent proof of "byte-identical": profile-resolving `default` and replaying
    # under the bare CONFIG singleton (today's pre-J-06 call shape) yield IDENTICAL snapshot
    # sequences, event for event — including the full features dict, not just state/confidence.
    store = DatasetStore(tmp_path / "datasets")
    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
    plain = list(store.replay(train["id"], CONFIG))
    via_profile = list(store.replay(train["id"], CONFIG.resolved_for_profile(PROFILE_DEFAULT)))
    assert [(s.tape_state, s.confidence, s.features) for s in plain] == [
        (s.tape_state, s.confidence, s.features) for s in via_profile
    ]


# --- the candidate-difference test: a REAL, legitimate, deterministic change -----------------------


def test_candidate_profile_legitimately_differs_from_default_on_the_fixture(tmp_path):
    """The 'make it fire' lesson (iter-4): the candidate must demonstrably and deterministically
    alter at least one classified output on the committed fixture — never a vacuous no-op. Pinned
    on BOTH founding windows: the candidate's lower warm-up floor calls its first directional
    state genuinely EARLIER (a real ``tape_state`` flip, not merely a confidence nudge)."""
    store = DatasetStore(tmp_path / "datasets")
    train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
    holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)
    candidate_config = CONFIG.resolved_for_profile(PROFILE_CANDIDATE_FASTER_WARMUP)

    for dataset, expected_diff_count, expected_first_diff_idx, expected_state in (
        (train, 13, 129, "seller_control"),
        (holdout, 24, 136, "buyer_control"),
    ):
        default_snaps = list(store.replay(dataset["id"], CONFIG))
        candidate_snaps = list(store.replay(dataset["id"], candidate_config))
        diffs = [
            i
            for i, (a, b) in enumerate(zip(default_snaps, candidate_snaps))
            if a.tape_state != b.tape_state
        ]
        assert len(diffs) == expected_diff_count
        assert diffs[0] == expected_first_diff_idx
        assert default_snaps[diffs[0]].tape_state == "unclear"
        assert candidate_snaps[diffs[0]].tape_state == expected_state

        # Determinism: an identical re-run of the CANDIDATE reproduces byte-identically.
        rerun = list(store.replay(dataset["id"], candidate_config))
        assert [(s.tape_state, s.confidence) for s in candidate_snaps] == [
            (s.tape_state, s.confidence) for s in rerun
        ]


def test_candidate_backtest_report_differs_from_default_only_via_legitimate_behavior(tmp_path):
    """The backtest-report-level leg: the SAME dataset backtested under ``default`` vs the
    candidate profile. Train's armed trade happens to be unaffected on this fixture (the earlier
    candidate transition does not move the SUSTAINED arm instant there); hold-out's DOES — a
    materially different entry (timestamp, price, and thus R/$) — proving the difference is
    real, not merely a metadata relabel. Both remain individually deterministic."""
    store = DatasetStore(tmp_path / "datasets")
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    try:
        train = _register(store, split=SPLIT_TRAIN, window=TRAIN_WINDOW)
        holdout = _register(store, split=SPLIT_HOLDOUT, window=HOLDOUT_WINDOW)

        def run(profile: str, dataset_id: str) -> dict:
            jobs = BacktestJobManager(journal, CONFIG)
            payload = jobs.create(
                {"dataset_id": dataset_id, "strategy_id": STRATEGY_V1_ID, "profile": profile}
            )
            jobs.run_sync(payload["id"], dataset_store=store)
            record = journal.get_backtest(payload["id"])
            assert record.payload["status"] == STATUS_DONE, record.payload
            return record.payload["result"]

        default_train = run(PROFILE_DEFAULT, train["id"])
        candidate_train = run(PROFILE_CANDIDATE_FASTER_WARMUP, train["id"])
        default_holdout = run(PROFILE_DEFAULT, holdout["id"])
        candidate_holdout = run(PROFILE_CANDIDATE_FASTER_WARMUP, holdout["id"])

        # Every report is stamped with its own resolved profile + a correctly distinguishing
        # fingerprint (the SAME hasher; the candidate's two reports share a fingerprint with each
        # other and differ from every default report).
        assert default_train["config_fingerprint"] == CONFIG.config_fingerprint()
        assert default_holdout["config_fingerprint"] == CONFIG.config_fingerprint()
        assert candidate_train["config_fingerprint"] == candidate_holdout["config_fingerprint"]
        assert candidate_train["config_fingerprint"] != CONFIG.config_fingerprint()
        assert candidate_train["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP
        assert candidate_holdout["profile"] == PROFILE_CANDIDATE_FASTER_WARMUP

        # TRAIN: this fixture's sustained-arm instant happens not to move — trades stay identical
        # (proving the candidate changes NOTHING it does not legitimately touch).
        assert candidate_train["trades"] == default_train["trades"]

        # HOLDOUT: the earlier directional call DOES move the sustained-arm instant — a
        # materially different entry (never merely a relabel).
        assert len(default_holdout["trades"]) == 1
        assert len(candidate_holdout["trades"]) == 1
        d_entry = default_holdout["trades"][0]["entry"]
        c_entry = candidate_holdout["trades"][0]["entry"]
        assert d_entry["logical_ts"] == pytest.approx(6.549988031387329)
        assert c_entry["logical_ts"] == pytest.approx(6.278010845184326)
        assert d_entry["logical_ts"] != c_entry["logical_ts"]
        assert default_holdout["trades"][0]["net_r"] == pytest.approx(0.3334000000001356)
        assert candidate_holdout["trades"][0]["net_r"] == pytest.approx(-0.1728000000000723)

        # Determinism: an identical re-run of the candidate is byte-identical.
        rerun_holdout = run(PROFILE_CANDIDATE_FASTER_WARMUP, holdout["id"])
        assert rerun_holdout["trades"] == candidate_holdout["trades"]
    finally:
        journal.close()


# --- the "no UI/engine path outside the backtest run param selects a profile" guard ----------------


def test_resolved_for_profile_is_called_only_by_the_backtest_runner():
    # The live cockpit / WatchManager / every archived-era engine path must NEVER resolve a
    # profile — only a backtest run (its explicit ``profile`` request param) may ever apply the
    # candidate overlay.
    app_dir = BACKEND_DIR / "app"
    callers = []
    for path in sorted(app_dir.rglob("*.py")):
        if path.name == "config.py":  # the method's own definition site
            continue
        if "resolved_for_profile" in path.read_text():
            callers.append(path.relative_to(app_dir).as_posix())
    assert callers == ["research/backtests.py"], callers
