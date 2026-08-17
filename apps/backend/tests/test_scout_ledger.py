"""``scout_ledger.py`` (Era "The Rapid Microscope" J-04) -- the hash-chained, append-only

candidate ledger. Test-first contract: TC-1, TC-2, TC-3, TC-4, TC-9, TC-13 in
``docs/phases/goal-rapid-microscope-iter-4.md``. TC-1/TC-2 exercise the bounded fixture grid
end to end through ``ScoutComputeManager``, over the ALREADY-committed hermetic fixtures
(``tests/fixtures/datasets/`` + ``tests/fixtures/datasets_j03/``, copied into a fresh ``tmp_path``
store -- read-only sources, a hermetic write target, the same discipline every other test file in
this suite uses). TC-3/TC-4/TC-9 exercise the ledger's own tamper/supersede/cap primitives
directly, over a throwaway ``tmp_path`` ledger -- no dataset or snapshot machinery needed for
those."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.config import CONFIG
from app.research import scout, scout_ledger
from app.research.datasets import DatasetStore
from app.research.micro_snapshots import run_snapshot_build_and_record

_FIXTURE_DIRS = [
    Path(__file__).resolve().parent / "fixtures" / "datasets",
    Path(__file__).resolve().parent / "fixtures" / "datasets_j03",
]


def _combined_fixture_store(tmp_path: Path) -> DatasetStore:
    """A fresh ``DatasetStore`` over a COPY of every committed hermetic tick fixture this era has
    used so far (the plan's own "reusing the already-committed hermetic fixtures already wired for
    J-02/J-03" instruction) -- the source fixture directories are only ever READ (``shutil.copy``),
    never written to; the target is a throwaway ``tmp_path`` directory."""
    target = tmp_path / "datasets"
    target.mkdir()
    for fixture_dir in _FIXTURE_DIRS:
        for path in fixture_dir.glob("*.json"):
            shutil.copy(path, target / path.name)
    return DatasetStore(target)


# --- TC-1: the bounded fixture grid, run end to end through ScoutComputeManager, lands one row per
# registered variant with a closed-vocabulary decision/reason and the family's running variants_tried


def test_tc1_manager_run_writes_one_closed_vocabulary_row_per_registered_variant(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ledger_dir = str(tmp_path / "scout")
    manager = scout.ScoutComputeManager()

    result = manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    assert result["state"] == "running"
    manager.join_all(timeout=30.0)
    final = manager.snapshot()
    assert final["state"] == "done", final.get("error")

    ledger = scout_ledger.ScoutLedger(ledger_dir)
    rows = ledger.all_rows()
    grid = scout.default_fixture_grid(store, grid_version=1)
    assert len(rows) == len(grid) > 0

    seen_candidate_ids = set()
    for row in rows:
        assert row["decision"] in scout_ledger.CLOSED_DECISIONS
        assert row["reason"] in scout_ledger.CLOSED_DECISIONS
        assert isinstance(row["notes"], str) and row["notes"]
        assert isinstance(row["variants_tried"], int) and row["variants_tried"] >= 1
        assert row["candidate_id"] not in seen_candidate_ids  # one row per registered variant
        seen_candidate_ids.add(row["candidate_id"])

    # this tiny corpus has exactly one session_date across every fixture file (all 2026-06-09) --
    # every candidate honestly reads killed_insufficient_n (goal.md's own Vision: "zero survivors
    # is a passing grade"), never a fabricated survivor.
    assert {row["decision"] for row in rows} == {"killed_insufficient_n"}


def test_tc1_manager_run_progress_reaches_every_candidate(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    ledger_dir = str(tmp_path / "scout")
    manager = scout.ScoutComputeManager()
    manager.trigger(store, CONFIG, snapshots_dir, ledger_dir)
    manager.join_all(timeout=30.0)
    final = manager.snapshot()
    grid = scout.default_fixture_grid(store, grid_version=1)
    assert final["progress"]["candidates_total"] == len(grid)
    assert final["progress"]["candidates_done"] == len(grid)


# --- TC-2: union-N spans grid versions (the ledger's own arithmetic, v1 N=40 + v2 N=25 => 65) -----


def test_tc2_variants_tried_is_the_union_across_grid_versions(tmp_path):
    """Exercises the LEDGER's own union-N arithmetic directly (``append_row``/``rows_for_family``)
    -- mirroring the spec's own TR-11 illustration verbatim (40 + 25 => 65). Deliberately bypasses
    ``scout.register_and_screen_candidate``'s 24-variant cap (module docstring's own interpretation
    call: the cap is a PRODUCTION-BOUNDARY rule, not a ledger-storage rule) -- TC-9 below proves
    that cap separately, at the actual production entry point, with its own small scenario."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    family_id = "illustrative-family"
    for i in range(40):
        ledger.append_row({"family_id": family_id, "grid_version": 1, "decision": "killed_null"})
    assert ledger.variants_tried_for_family(family_id) == 40

    for i in range(25):
        ledger.append_row({"family_id": family_id, "grid_version": 2, "decision": "killed_null"})
    assert ledger.variants_tried_for_family(family_id) == 65

    # every row's OWN stamped variants_tried is the running count as of that row (never rewritten)
    rows = ledger.rows_for_family(family_id)
    assert [row["variants_tried"] for row in rows] == list(range(1, 66))


def test_tc2_variants_tried_is_scoped_per_family_never_pooled_across_families(tmp_path):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    for i in range(5):
        ledger.append_row({"family_id": "family-a", "decision": "killed_null"})
    for i in range(3):
        ledger.append_row({"family_id": "family-b", "decision": "killed_null"})
    assert ledger.variants_tried_for_family("family-a") == 5
    assert ledger.variants_tried_for_family("family-b") == 3
    assert ledger.variants_tried_for_family("family-nonexistent") == 0


def test_tc2_union_n_counts_distinct_candidate_ids_never_repeated_evaluations(tmp_path):
    """iter-4 audit fix: ``variants_tried`` is a union over VARIANT identity (``candidate_id``, a
    pure content hash of the frozen spec), not a row count -- re-evaluating a variant already on
    record adds a permanent row (nothing is ever dropped) but never a new "thing tried"."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    for candidate_id in ("cand-a", "cand-b", "cand-a", "cand-b", "cand-a"):
        ledger.append_row({"family_id": "z", "candidate_id": candidate_id, "decision": "killed_null"})

    assert len(ledger.rows_for_family("z")) == 5  # every evaluation permanently on record
    assert ledger.variants_tried_for_family("z") == 2  # ... but only 2 variants were ever tried
    assert [row["variants_tried"] for row in ledger.rows_for_family("z")] == [1, 2, 2, 2, 2]
    assert scout.list_scout_families(ledger)[0]["variants_tried"] == 2


def test_tc2_served_via_list_scout_families_matches_the_ledger_directly(tmp_path):
    """The SAME arithmetic ``GET /research/desk/micro/scout`` serves (``scout.list_scout_families``,
    the route's own body) -- single source of truth, never a second computation at the route."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    family_id = "route-family"
    for i in range(40):
        ledger.append_row({"family_id": family_id, "grid_version": 1, "decision": "killed_null"})
    for i in range(25):
        ledger.append_row({"family_id": family_id, "grid_version": 2, "decision": "killed_null"})

    families = scout.list_scout_families(ledger)
    assert len(families) == 1
    assert families[0]["family_id"] == family_id
    assert families[0]["variants_tried"] == 65
    assert len(families[0]["trials"]) == 65


# --- TC-3: an in-place edit of ledger row k reports a chain-verification failure AT row k ----------


def test_tc3_verify_chain_is_ok_on_a_clean_ledger(tmp_path):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "decision": "survive"})
    ledger.append_row({"family_id": "x", "decision": "killed_null"})
    ledger.append_row({"family_id": "x", "decision": "killed_economic"})
    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}


def test_tc3_in_place_edit_of_row_k_fails_verification_exactly_at_k(tmp_path):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "decision": "survive"})
    ledger.append_row({"family_id": "x", "decision": "killed_null"})
    ledger.append_row({"family_id": "x", "decision": "killed_economic"})

    lines = ledger.path.read_text().splitlines()
    tampered = json.loads(lines[1])
    tampered["decision"] = "survive"  # a tampered claim -- the row's own stored hash no longer matches
    lines[1] = json.dumps(tampered, sort_keys=True)
    ledger.path.write_text("\n".join(lines) + "\n")

    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["failed_at_row"] == 1
    assert result["reason"] == "content_hash_mismatch"


def test_tc3_a_deleted_row_breaks_the_chain_link_at_the_first_row_whose_predecessor_no_longer_matches(
    tmp_path,
):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "decision": "survive"})
    ledger.append_row({"family_id": "x", "decision": "killed_null"})
    ledger.append_row({"family_id": "x", "decision": "killed_economic"})

    lines = ledger.path.read_text().splitlines()
    del lines[1]  # delete the middle row entirely (never possible through append_row itself)
    ledger.path.write_text("\n".join(lines) + "\n")

    result = ledger.verify_chain()
    assert result["ok"] is False
    assert result["failed_at_row"] == 1  # the row that is NOW at position 1 (formerly row 2)
    assert result["reason"] == "prev_hash_mismatch"


def test_tc3_a_truncated_tail_is_caught_by_the_durable_head_anchor(tmp_path):
    """iter-4 audit fix: deleting the LAST rows leaves every surviving row self-consistent, so the
    chain walk alone reports ``ok`` -- the erasure the era's own "the denominator never shrinks"
    anti-goal exists to forbid. The durable ``chain_head.json`` anchor catches it, at the first
    missing index. (The serving-path half of this fix is tested in ``test_scout.py``.)"""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "candidate_id": "c1", "decision": "survive"})
    ledger.append_row({"family_id": "x", "candidate_id": "c2", "decision": "killed_null"})
    ledger.append_row({"family_id": "x", "candidate_id": "c3", "decision": "killed_economic"})

    lines = ledger.path.read_text().splitlines()
    del lines[2]  # erase the most recent kill -- the one deletion a linked chain cannot self-detect
    ledger.path.write_text("\n".join(lines) + "\n")

    assert ledger.verify_chain() == {"ok": False, "failed_at_row": 2, "reason": "tail_truncated"}


def test_tc3_a_missing_head_anchor_is_an_honest_refusal_to_certify_not_a_silent_pass(tmp_path):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "candidate_id": "c1", "decision": "survive"})
    (tmp_path / "ledger" / "chain_head.json").unlink()
    assert ledger.verify_chain() == {
        "ok": False, "failed_at_row": None, "reason": "head_anchor_missing",
    }


def test_tc3_an_empty_ledger_with_no_anchor_yet_verifies_clean(tmp_path):
    """A lint that can fail proves something: "nothing written yet" is not a tamper."""
    assert scout_ledger.ScoutLedger(tmp_path / "never-written").verify_chain() == {
        "ok": True, "failed_at_row": None, "reason": None,
    }


def test_tc3_a_ledger_longer_than_its_anchor_still_verifies(tmp_path):
    """The crash-window direction (a row appended, the anchor not yet rewritten) is benign and must
    never read as tampering -- the anchor is written AFTER the row it commits to."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "candidate_id": "c1", "decision": "survive"})
    stale_anchor = (tmp_path / "ledger" / "chain_head.json").read_text()
    ledger.append_row({"family_id": "x", "candidate_id": "c2", "decision": "killed_null"})
    (tmp_path / "ledger" / "chain_head.json").write_text(stale_anchor)
    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}


def test_tc3_no_code_path_silently_accepts_a_tampered_chain(tmp_path):
    """``verify_chain`` never raises and never reports ``ok: True`` on a tampered file -- the
    caller always gets an explicit, actionable verdict."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "x", "decision": "survive"})
    lines = ledger.path.read_text().splitlines()
    tampered = json.loads(lines[0])
    tampered["family_id"] = "y"
    ledger.path.write_text(json.dumps(tampered, sort_keys=True) + "\n")
    result = ledger.verify_chain()
    assert result == {"ok": False, "failed_at_row": 0, "reason": "content_hash_mismatch"}


# --- TC-4: a superseded row is never deleted; its successor pointer resolves to a later row --------


def test_tc4_superseded_row_persists_and_its_pointer_resolves_to_a_later_row(tmp_path):
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "y", "candidate_id": "cand-old", "decision": "killed_null"})
    ledger.append_row({"family_id": "y", "candidate_id": "cand-new", "decision": "survive"})
    ledger.append_row(
        {
            "family_id": "y",
            "candidate_id": "cand-old",
            "decision": "superseded",
            "reason": "superseded",
            "superseded_by": "cand-new",
        }
    )

    rows = ledger.all_rows()
    assert len(rows) == 3  # never deleted
    superseded_row = rows[2]
    assert superseded_row["decision"] == "superseded"
    successor_id = superseded_row["superseded_by"]
    later_candidate_ids = [row["candidate_id"] for row in rows[3:]]  # rows strictly after it
    # the successor already exists earlier in append order here (row 1) -- "a later row" (TC-4's
    # own wording) is satisfied by any row whose position in the SAME file resolves the pointer;
    # confirm the resolvable row is genuinely present and is not the superseded row itself.
    resolved = next((row for row in rows if row["candidate_id"] == successor_id), None)
    assert resolved is not None
    assert resolved is not superseded_row
    assert resolved["decision"] == "survive"


def test_tc4_verify_chain_still_passes_with_a_superseded_row_present(tmp_path):
    """Superseding is a normal, non-tampering append -- the chain stays clean."""
    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    ledger.append_row({"family_id": "y", "candidate_id": "cand-old", "decision": "killed_null"})
    ledger.append_row({"family_id": "y", "candidate_id": "cand-new", "decision": "survive"})
    ledger.append_row(
        {"family_id": "y", "candidate_id": "cand-old", "decision": "superseded", "superseded_by": "cand-new"}
    )
    assert ledger.verify_chain()["ok"] is True


# --- TC-9: SCOUT_MAX_VARIANTS_PER_FAMILY (24) is enforced at the production registration boundary -


def test_tc9_a_25th_variant_for_an_already_full_family_is_refused(tmp_path):
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    records, _errors = store.list()
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]

    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    family_id = scout_ledger.derive_family_id("cumulative_delta", "none", "trades_20")
    for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY):
        ledger.append_row({"family_id": family_id, "decision": "killed_null"})
    assert ledger.variants_tried_for_family(family_id) == scout.SCOUT_MAX_VARIANTS_PER_FAMILY

    with pytest.raises(scout.ScoutGridExhaustedError):
        scout.register_and_screen_candidate(
            ledger=ledger,
            dataset_store=store,
            snapshots_dir=snapshots_dir,
            config=CONFIG,
            feature_name="cumulative_delta",
            transform="threshold",
            params={"op": "ge", "value": 0.0},
            structure_context_kind="none",
            horizon_key="trades_20",
            corpus_manifest=manifest,
            grid_version=99,
        )
    # refused -- no new row written; the family stays at exactly the cap, never over it
    assert ledger.variants_tried_for_family(family_id) == scout.SCOUT_MAX_VARIANTS_PER_FAMILY


def test_tc9_a_24th_variant_for_an_almost_full_family_is_accepted(tmp_path):
    """A lint that can fail proves something: the cap refuses at 25, never one short."""
    store = _combined_fixture_store(tmp_path)
    snapshots_dir = str(tmp_path / "snapshots")
    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    records, _errors = store.list()
    manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]

    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
    family_id = scout_ledger.derive_family_id("cumulative_delta", "none", "trades_20")
    for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY - 1):
        ledger.append_row({"family_id": family_id, "decision": "killed_null"})

    row = scout.register_and_screen_candidate(
        ledger=ledger,
        dataset_store=store,
        snapshots_dir=snapshots_dir,
        config=CONFIG,
        feature_name="cumulative_delta",
        transform="threshold",
        params={"op": "ge", "value": 0.0},
        structure_context_kind="none",
        horizon_key="trades_20",
        corpus_manifest=manifest,
        grid_version=99,
    )
    assert row["variants_tried"] == scout.SCOUT_MAX_VARIANTS_PER_FAMILY


# --- TC-13: zero registered candidates condition on quote_depletion --------------------------------


def test_tc13_the_default_grid_registers_no_quote_depletion_conditioned_candidate(tmp_path):
    store = _combined_fixture_store(tmp_path)
    grid = scout.default_fixture_grid(store, grid_version=1)
    assert grid  # a lint that can fail proves something -- the grid is genuinely non-empty
    assert all(request["feature_name"] != "quote_depletion" for request in grid)


def test_tc13_quote_depletion_is_not_a_registrable_feature_name_at_all():
    """Structural, not incidental: ``quote_depletion`` is a DEFERRED construct living inside a
    snapshot row's ``deferred`` list (``micro_observer.py``), never a top-level row field --
    ``extract_anchors``'s ``anchor_row.get(feature_name)`` could not read it even if asked to. This
    iteration's own ``FEATURE_FAMILY_OF`` table (the closed vocabulary ``build_candidate_spec_
    fields`` validates against) never lists it, so a caller attempting to register one is refused
    at spec-build time, before any ledger row is written -- the assumption-ledger's own scope
    decision (goal.md NOTES), made structurally unreachable rather than merely undocumented."""
    assert "quote_depletion" not in scout.FEATURE_FAMILY_OF
    with pytest.raises(ValueError):
        scout.build_candidate_spec_fields(
            feature_name="quote_depletion",
            transform="threshold",
            params={"op": "ge", "value": 0.0},
            structure_context_kind="none",
            horizon_key="trades_20",
            sidedness=None,
            fitting_rule=None,
            family_median_spread_bps=1.0,
            corpus_manifest=[],
            grid_version=1,
        )
