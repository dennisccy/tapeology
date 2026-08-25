"""``test_micro_deterministic_rerun.py`` -- Era "The Rapid Microscope" J-10's last acceptance gap

(``docs/phases/goal-rapid-microscope-iter-19.md``, TC-1..TC-4): over an UNCHANGED fixture
dataset/store, each of the three era computations -- snapshot build, Scout screen, walk-forward
fold -- produces byte-identical output when GENUINELY re-run, excluding only fields that are
legitimately new per run (ledger row id/position, ``registered_at``/timestamp, ``run_id``,
``sequence_id`` bookkeeping). This is a test/harness-only module -- no production module changes.

**Non-vacuity is the whole point (iter-15/16's lesson: an equality check between two runs is
exactly the "structurally unable to fail" shape those lessons warn about).** Two of this era's own
production paths are DELIBERATELY idempotent-on-replay, and a naive same-store/same-ledger rerun
against either would compare a cached result against itself -- always "passing", not because the
computation is proven deterministic but because it is LITERALLY the same object:

- ``micro_snapshots.run_snapshot_build_and_record`` reuses an existing valid snapshot
  (``load_snapshot_meta``'s own re-verification, module docstring) rather than rebuild it.
- ``walkforward_ledger.append_fold_result`` returns the CACHED row for an identical
  ``(sequence_id, fold_index, spec_hash)`` rather than append a second one -- that module's own
  docstring, and ``test_walkforward.py``'s own TR-22 section, warn a naive same-ledger rerun test
  falls into exactly this trap.

So every comparison below forces a genuinely independent second computation instead:
``build_snapshot_rows`` (which never caches at all) is called a second time directly;
``run_snapshot_build_and_record`` is pointed at a SECOND, independent ``root_dir`` so it cannot
hit the reuse path; the walk-forward fold is evaluated a second time against a FRESH
``(WalkForwardLedger, ExposureRegistry)`` pair so it cannot hit the idempotent-replay cache. Only
the Scout ledger check (TC-2's second half) reuses the SAME ledger across both calls -- that is
the point of that half: ``register_and_screen_candidate`` carries no idempotency guard of its own
(unlike the walk-forward ledger), so the test proves the ledger genuinely grows by one row per
call while the computed ``screen_result`` stays put.

**TC-4 mutation-proof (this era's own established discipline -- ``test_micro_sealed_
evaluation.py``'s TC-8 precedent, matched here).** Each comparison is proven capable of FAILING,
by deliberately perturbing ONE field of a scratch second-run result before comparing, then
reverting and confirming the real (unperturbed) rerun passes. Perturbed fields, one per
computation: a snapshot row's ``cumulative_delta`` (TC-4a), a scout ``screen_result``'s
``effect_bps`` (TC-4b), a walk-forward fold's ``effect`` (TC-4c).

**TC-2b/TC-4d -- added by the iteration-19 audit (mutation lane).** TC-2 above screens a STRONG
planted effect (``effect=3.0``), which saturates the block-permutation null: not one of the
``SCOUT_BLOCK_PERMUTATIONS`` draws ever reaches the observed delta, so ``p_screen`` pins to
``1/(draws+1)`` in EVERY run. Measured consequence: replacing ``scout.scout_stream`` with an
UNSEEDED ``random.Random()`` leaves that ``screen_result`` byte-identical -- i.e. TC-2 alone
cannot observe the seeded stream at all, and the era's *critical* "deterministic and seeded"
anti-goal is the one thing it would most need to observe. TC-2b therefore reruns a
``effect=0.0`` candidate, whose ``p_screen`` lands strictly INSIDE the null distribution where
the stream genuinely moves it, and TC-4d proves that comparison discriminates by swapping the
per-session seeded streams for one fixed alternate stream (the perturbation here is the SEED
LINEAGE itself, not a result field)."""

from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_snapshots as ms
from app.research import scout, scout_ledger
from app.research import walkforward as wf
from app.research import walkforward_ledger as wl
from app.research.datasets import DatasetStore
from app.research.micro_accessor import ExposureRegistry

TICKER = "TC-DETRUN"

_FIXTURE_DIRS = [
    Path(__file__).resolve().parent / "fixtures" / "datasets",
    Path(__file__).resolve().parent / "fixtures" / "datasets_j03",
]

_ECON_FLOOR_TINY = {
    "multiple": 1.0, "family_median_spread_bps": 0.001, "floor_bps": 0.001, "unit": "bps",
    "proxy_sentence": scout.ECON_PROXY_SENTENCE,
}

_WF_FLOORS = {"wf_fold_min_observations": 1, "wf_fold_min_signal_sessions": 1, "wf_fold_min_symbols": 1}


# === shared fixture builders (local, mirroring -- never importing -- the established patterns in
# test_micro_snapshots.py / test_scout.py / test_walkforward.py, this codebase's own convention:
# see test_micro_sealed_evaluation.py's module docstring for the same "mirror the precedent, do
# not cross-import test internals" discipline) ========================================================


def _events_for_store() -> list:
    return [
        QuoteEvent(TICKER, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(TICKER, 0.1, 100.03, 10, Side.UNKNOWN),  # engine classifies: >= ask -> BUY
        TradeEvent(TICKER, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> SELL
    ]


def _plant(store: DatasetStore) -> dict:
    return store.record(
        symbol=TICKER, source="fixture", source_kind="fixture", source_id="fixture",
        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
    )


def _combined_fixture_store(tmp_path: Path) -> DatasetStore:
    target = tmp_path / "datasets"
    target.mkdir()
    for fixture_dir in _FIXTURE_DIRS:
        for path in fixture_dir.glob("*.json"):
            shutil.copy(path, target / path.name)
    return DatasetStore(target)


def _planted_effect_anchors(n_sessions=6, n_per_session=20, effect=3.0, seed=1):
    """The ``test_scout.py`` precedent, verbatim: a seeded, pure generator -- calling it twice
    with the same ``seed`` returns content-identical (never object-identical) anchor lists."""
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
                    "outcome_bps": outcome, "tod_bucket": "mid", "fallback_frac": rng.random(),
                }
            )
    return anchors


def _wf_observations() -> list[dict]:
    return [
        {"session_date": f"2026-05-{d:02d}", "symbol": "PG", "value": 4.0, "value_unit": wf.WF_OBSERVATION_UNIT}
        for d in range(1, 5)
    ] * 3  # 12 observations across 4 sessions, one symbol -- comfortably above the tiny custom floors


def _wf_fold() -> dict:
    return {
        "fold_index": 0, "origin_index": 0, "train_sessions": [],
        "embargo_sessions": [], "test_sessions": [f"2026-05-{d:02d}" for d in range(1, 5)],
    }


def _evaluate_mode_b_in_a_fresh_ledger(run_dir: Path, *, corpus_id: str) -> dict:
    """ONE genuinely independent evaluation: a brand-new ``WalkForwardLedger``/``ExposureRegistry``
    pair rooted at ``run_dir``, so ``append_fold_result``'s own idempotent-replay guard (keyed on
    ``(sequence_id, fold_index, spec_hash)``) can never fire -- nothing has ever been written to
    THIS ledger before this call."""
    ledger = wl.WalkForwardLedger(str(run_dir / "ledger"))
    registry = ExposureRegistry(str(run_dir / "exposure"))
    spec = wf.register_mode_b_spec(
        corpus_id=corpus_id, rule_id="tc3-rule", sidedness="long", econ_floor=None,
        registered_at="2026-06-01T00:00:00.000000Z",
    )
    return wf.evaluate_mode_b_fold(
        ledger, registry, spec=spec, fold=_wf_fold(), observations=_wf_observations(), floors=_WF_FLOORS,
    )


# === comparison helpers (shared by TC-1..TC-3's real assertions AND TC-4's mutation-proof) ===========


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def _assert_rerun_matches(run_1, run_2, *, label: str) -> None:
    """The ONE comparison every TC below relies on: canonical-JSON equality. Deliberately simple
    (no bespoke per-field logic) so TC-4's mutation-proof exercises the exact function TC-1..TC-3
    trust, not a stand-in for it."""
    c1, c2 = _canonical(run_1), _canonical(run_2)
    assert c1 == c2, f"{label}: rerun diverged\n  run1={c1}\n  run2={c2}"


def _without_keys(d: dict, keys) -> dict:
    return {k: v for k, v in d.items() if k not in keys}


# === TC-1: micro_snapshots.build_snapshot_rows / run_snapshot_build_and_record ========================


def test_tc1_build_snapshot_rows_is_byte_identical_across_two_independent_calls(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)

    rows_1 = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    rows_2 = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    assert len(rows_1) == 3  # sanity: this fixture's own known row count (module docstring)
    _assert_rerun_matches(rows_1, rows_2, label="snapshot rows")

    identity_1 = ms.snapshot_identity(meta, CONFIG)
    identity_2 = ms.snapshot_identity(meta, CONFIG)
    _assert_rerun_matches(identity_1, identity_2, label="snapshot identity")


def test_tc1_run_snapshot_build_and_record_persists_byte_identical_identity_across_two_independent_root_dirs(
    tmp_path,
):
    """Forces a genuine second computation -- never the ``load_snapshot_meta`` reuse path (module
    docstring) -- by pointing run 2 at its OWN ``root_dir``; only ``built_utc`` (a per-run
    wall-clock stamp -- this computation's one legitimately-new-per-run field) is excluded."""
    store = DatasetStore(tmp_path / "datasets")
    _plant(store)

    results_1 = ms.run_snapshot_build_and_record(store, CONFIG, str(tmp_path / "snapshots_run1"))
    results_2 = ms.run_snapshot_build_and_record(store, CONFIG, str(tmp_path / "snapshots_run2"))
    assert len(results_1) == len(results_2) == 1

    _assert_rerun_matches(
        _without_keys(results_1[0], {"built_utc"}),
        _without_keys(results_2[0], {"built_utc"}),
        label="persisted snapshot meta",
    )


# === TC-2: scout.screen_candidate / register_and_screen_candidate =====================================


def test_tc2_screen_candidate_is_byte_identical_across_two_independent_calls():
    """The PURE-function proof: ``screen_candidate`` reads no ledger and keeps no state, so
    identical hand-built anchors screened twice already proves determinism of the whole
    statistical core (effect, p_screen, every disclosure) with zero storage involved."""
    anchors_1 = _planted_effect_anchors()
    anchors_2 = _planted_effect_anchors()  # a SEPARATE, content-identical (never object-identical) list
    assert anchors_1 is not anchors_2
    assert anchors_1 == anchors_2

    result_1 = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors_1,
        family_id="tc2-pure-rerun", n_variants_tried=1,
    )
    result_2 = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors_2,
        family_id="tc2-pure-rerun", n_variants_tried=1,
    )
    assert result_1["decision"] == "survive"  # a genuine, non-trivial numeric result -- not insufficient_n
    _assert_rerun_matches(result_1["screen_result"], result_2["screen_result"], label="screen_result")


def _screen_planted(anchors: list, *, family_id: str) -> dict:
    """TC-2b/TC-4d's ONE screen call shape (identical arguments every time), so the only thing
    that can ever differ between two invocations is the computation itself."""
    return scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id=family_id, n_variants_tried=1,
    )


def test_tc2b_screen_candidate_rerun_is_byte_identical_where_the_seeded_null_stream_actually_moves_it():
    """The RNG-SENSITIVE rerun (audit addition -- module docstring): a zero-effect candidate puts
    ``p_screen`` strictly inside the block-permutation null, so this comparison -- unlike TC-2's
    saturated one -- genuinely proves the seeded stream reproduces byte-identically."""
    result_1 = _screen_planted(_planted_effect_anchors(effect=0.0), family_id="tc2b-seeded-rerun")
    result_2 = _screen_planted(_planted_effect_anchors(effect=0.0), family_id="tc2b-seeded-rerun")

    p_screen = result_1["screen_result"]["p_screen"]
    saturated = 1.0 / (scout.SCOUT_BLOCK_PERMUTATIONS + 1)
    assert p_screen > saturated  # NOT pinned to the null's floor -- the draws genuinely move it
    assert p_screen < 1.0
    _assert_rerun_matches(
        result_1["screen_result"], result_2["screen_result"], label="screen_result (rng-sensitive)"
    )


def test_tc4d_scout_rerun_comparison_fails_when_the_seeded_null_stream_is_replaced(monkeypatch):
    """The STREAM-level mutation-proof (audit addition): perturb the seed lineage itself -- every
    per-session ``scout_stream`` call collapses to one fixed alternate stream -- and the TC-2b
    comparison must FAIL; restore the real streams and it must PASS again."""
    anchors = _planted_effect_anchors(effect=0.0)
    baseline = _screen_planted(anchors, family_id="tc4d-mutation-proof")["screen_result"]

    monkeypatch.setattr(scout, "scout_stream", lambda *a, **k: random.Random("tc4d-alternate-stream"))
    perturbed = _screen_planted(anchors, family_id="tc4d-mutation-proof")["screen_result"]
    with pytest.raises(AssertionError):
        _assert_rerun_matches(baseline, perturbed, label="screen_result (perturbed seed lineage)")

    monkeypatch.undo()
    _assert_rerun_matches(  # the real, seeded rerun still passes
        baseline, _screen_planted(anchors, family_id="tc4d-mutation-proof")["screen_result"],
        label="screen_result (restored seed lineage)",
    )


def test_tc2_register_and_screen_candidate_is_byte_identical_across_two_registrations_on_one_ledger(
    tmp_path,
):
    """The LEDGER-level proof: ``register_and_screen_candidate`` carries no idempotency guard of
    its own (unlike the walk-forward ledger -- module docstring), so re-registering the IDENTICAL
    candidate spec on the SAME ledger genuinely appends a SECOND, independent row -- this is the
    correct way to observe two trials of one variant, not a vacuous cache replay."""
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ms.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    records, _errors = store.list()
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]

    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    kwargs = dict(
        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        structure_context_kind="none", horizon_key="trades_20", corpus_manifest=manifest,
        grid_version=1,
    )
    row_1 = scout.register_and_screen_candidate(**kwargs)
    row_2 = scout.register_and_screen_candidate(**kwargs)

    assert row_1["candidate_id"] == row_2["candidate_id"]  # the SAME variant, evaluated twice
    assert row_1["row_index"] != row_2["row_index"]  # two INDEPENDENT physical ledger rows
    family_id = row_1["family_id"]
    assert len(ledger.rows_for_family(family_id)) == 2  # both trials permanently on record
    assert ledger.variants_tried_for_family(family_id) == 1  # union-N counts variants, not evaluations
    _assert_rerun_matches(row_1["screen_result"], row_2["screen_result"], label="screen_result")


# === TC-3: walkforward.evaluate_mode_b_fold ============================================================


def test_tc3_evaluate_mode_b_fold_result_fields_are_byte_identical_across_two_independent_ledgers(
    tmp_path,
):
    corpus_id = "tc3-detrun-corpus"
    row_1 = _evaluate_mode_b_in_a_fresh_ledger(tmp_path / "run1", corpus_id=corpus_id)
    row_2 = _evaluate_mode_b_in_a_fresh_ledger(tmp_path / "run2", corpus_id=corpus_id)

    # sequence_id is a pure function of (corpus_id, rule_id) (TR-14) -- both runs derive the SAME
    # value independently; this is deterministic behaviour, never a cache leak, because each run's
    # own ledger started genuinely empty (module docstring).
    assert row_1["sequence_id"] == row_2["sequence_id"]
    assert row_1["status"] == wf.FOLD_STATUS_SUFFICIENT  # a genuine, non-trivial computed fold

    carried_fields = ("effect", "n", "n_sessions", "sign", "evidence_class", "process_label")
    _assert_rerun_matches(
        {k: row_1[k] for k in carried_fields}, {k: row_2[k] for k in carried_fields}, label="fold_results"
    )


# === TC-4: the mutation-proof (non-negotiable per iter-15/16's lesson) ================================


def test_tc4a_snapshot_rerun_comparison_fails_on_a_perturbed_cumulative_delta_and_passes_when_reverted(
    tmp_path,
):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    rows_1 = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    rows_2 = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    assert rows_1[0]["cumulative_delta"] == 10.0  # the exact real value this fixture always produces

    mutated = [dict(row) for row in rows_2]
    mutated[0]["cumulative_delta"] = mutated[0]["cumulative_delta"] + 1.0  # deliberately WRONG
    with pytest.raises(AssertionError):
        _assert_rerun_matches(rows_1, mutated, label="snapshot rows (mutated)")

    _assert_rerun_matches(rows_1, rows_2, label="snapshot rows (reverted)")  # the real rerun still passes


def test_tc4b_scout_screen_result_rerun_comparison_fails_on_a_perturbed_effect_bps_and_passes_when_reverted():
    anchors = _planted_effect_anchors()
    result_1 = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="tc4b-mutation-proof", n_variants_tried=1,
    )
    result_2 = scout.screen_candidate(
        feature_name="cumulative_delta", transform="threshold", params={"op": "ge", "value": 0.0},
        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR_TINY, anchors=anchors,
        family_id="tc4b-mutation-proof", n_variants_tried=1,
    )
    assert result_1["screen_result"]["effect_bps"] is not None

    mutated = dict(result_2["screen_result"])
    mutated["effect_bps"] = mutated["effect_bps"] + 1.0  # deliberately WRONG
    with pytest.raises(AssertionError):
        _assert_rerun_matches(result_1["screen_result"], mutated, label="screen_result (mutated)")

    _assert_rerun_matches(  # the real rerun still passes
        result_1["screen_result"], result_2["screen_result"], label="screen_result (reverted)"
    )


def test_tc4c_walkforward_fold_result_rerun_comparison_fails_on_a_perturbed_effect_and_passes_when_reverted(
    tmp_path,
):
    corpus_id = "tc4c-mutation-proof-corpus"
    row_1 = _evaluate_mode_b_in_a_fresh_ledger(tmp_path / "run1", corpus_id=corpus_id)
    row_2 = _evaluate_mode_b_in_a_fresh_ledger(tmp_path / "run2", corpus_id=corpus_id)
    assert row_1["effect"] == 4.0  # the exact real value this fixture always produces

    mutated = dict(row_2)
    mutated["effect"] = mutated["effect"] + 1.0  # deliberately WRONG

    carried_fields = ("effect", "n", "n_sessions", "sign", "evidence_class", "process_label")
    with pytest.raises(AssertionError):
        _assert_rerun_matches(
            {k: row_1[k] for k in carried_fields}, {k: mutated[k] for k in carried_fields},
            label="fold_results (mutated)",
        )

    _assert_rerun_matches(  # the real rerun still passes
        {k: row_1[k] for k in carried_fields}, {k: row_2[k] for k in carried_fields},
        label="fold_results (reverted)",
    )
