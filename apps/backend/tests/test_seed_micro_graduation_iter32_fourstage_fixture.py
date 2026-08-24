"""Regression coverage for ``scripts/seed_micro_graduation_iter32_fourstage_fixture.py`` (Era "The
Rapid Microscope", goal-rapid-microscope-iter-32, J-11's "four-stage" browser-QA capture) -- a
guard for the FIXTURE SCRIPT itself, not for production code (the script imports and calls
``micro_graduation.py``/``micro_sealed_evaluation.py`` exactly as shipped; see the phase spec's OUT
OF SCOPE list). Asserts the seed script's own fixture is well-formed end to end: the four target
states, Family B's permanent ``fail`` verdict recomputed via the REAL ``evaluate_sealed_verdict``
(never a hand-set field), and idempotent-replay safety (a second run against the SAME scoped root
appends no duplicate row anywhere)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import seed_micro_graduation_iter32_fourstage_fixture as seed  # noqa: E402

from app.research import micro_graduation as g  # noqa: E402
from app.research import micro_sealed_evaluation as sealed_eval  # noqa: E402


def _ledger_for(root: Path) -> g.GraduationLedger:
    return g.GraduationLedger(g.resolve_micro_graduation_dir(str(root / "datasets")))


# === TC-1/TC-2/TC-3/TC-4 (this file's own numbering): the four families land in their target =========
# === states, and Family B's own permanent verdict is a genuine "fail" (never a hand-set field). ======


def test_all_four_families_land_in_their_target_states(tmp_path):
    exit_code = seed.main(tmp_path)
    assert exit_code == 0

    ledger = _ledger_for(tmp_path)
    families = {f["family_root_id"]: f for f in g.list_graduation_families(ledger)}
    assert len(families) == 4

    states = {fam["state"] for fam in families.values()}
    assert states == {
        g.GRADUATION_STATE_EXPLORATORY,
        g.GRADUATION_STATE_WALKFORWARD_SURVIVOR,
        g.GRADUATION_STATE_SEALED_SURVIVOR,
        g.GRADUATION_STATE_REFEREE_HANDOFF_READY,
    }


def test_family_a_is_exploratory_via_one_real_insufficient_sealed_evaluation_no_wf_transition(tmp_path):
    exit_code = seed.main(tmp_path)
    assert exit_code == 0
    ledger = _ledger_for(tmp_path)

    families = g.list_graduation_families(ledger)
    family_a = next(f for f in families if f["state"] == g.GRADUATION_STATE_EXPLORATORY)

    # no walk-forward-survivor transition was ever attempted for this family.
    assert family_a["transitions"] == []
    # its ONE ledger footprint is a real, INSUFFICIENT sealed evaluation.
    assert len(family_a["sealed_evaluations"]) == 1
    assert family_a["sealed_evaluations"][0]["verdict"] == sealed_eval.SEALED_VERDICT_INSUFFICIENT
    assert family_a["sealed_evaluations"][0]["n"] == 29


def test_tc5_family_b_permanent_fail_verdict_is_recomputed_not_hand_set(tmp_path):
    """TC-5 (phase spec): re-reading Family B's row from disk through ``GraduationLedger`` shows
    ``verdict == "fail"`` and ``n == 30`` DERIVED FROM REAL RECOMPUTATION -- confirmed here via the
    ledger, not merely the script's own stdout."""
    exit_code = seed.main(tmp_path)
    assert exit_code == 0
    ledger = _ledger_for(tmp_path)

    families = g.list_graduation_families(ledger)
    family_b = next(f for f in families if f["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR)

    assert len(family_b["sealed_evaluations"]) == 1
    evaluation = family_b["sealed_evaluations"][0]
    assert evaluation["verdict"] == sealed_eval.SEALED_VERDICT_FAIL
    assert evaluation["failure_reason"] == "below_economic_floor"
    assert evaluation["n"] == 30
    assert evaluation["effect"] == pytest.approx(1.0)  # real recomputation, never a hand-set 0/1 flag
    assert evaluation["sign"] == "positive"  # correct direction; fails on magnitude alone

    # the state never advanced past walkforward_survivor -- a failed sealed verdict is permanent
    # and never advances (spec section 7.4/8.1).
    assert family_b["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR
    assert [t["to_state"] for t in family_b["transitions"]] == [g.GRADUATION_STATE_WALKFORWARD_SURVIVOR]


def test_family_c_is_a_genuine_pass_on_a_shard_distinct_from_family_b(tmp_path):
    exit_code = seed.main(tmp_path)
    assert exit_code == 0
    ledger = _ledger_for(tmp_path)

    families = g.list_graduation_families(ledger)
    family_c = next(f for f in families if f["state"] == g.GRADUATION_STATE_SEALED_SURVIVOR)
    family_b = next(f for f in families if f["state"] == g.GRADUATION_STATE_WALKFORWARD_SURVIVOR)

    assert len(family_c["sealed_evaluations"]) == 1
    assert family_c["sealed_evaluations"][0]["verdict"] == sealed_eval.SEALED_VERDICT_PASS
    # distinct shard from Family B's own failed evaluation.
    assert family_c["sealed_evaluations"][0]["shard_checksum"] != family_b["sealed_evaluations"][0]["shard_checksum"]


def test_family_d_bundle_carries_the_referee_future_revision_sentence_verbatim(tmp_path):
    exit_code = seed.main(tmp_path)
    assert exit_code == 0
    ledger = _ledger_for(tmp_path)

    families = g.list_graduation_families(ledger)
    family_d = next(f for f in families if f["state"] == g.GRADUATION_STATE_REFEREE_HANDOFF_READY)
    to_states = [t["to_state"] for t in family_d["transitions"]]
    assert to_states == [
        g.GRADUATION_STATE_WALKFORWARD_SURVIVOR,
        g.GRADUATION_STATE_SEALED_SURVIVOR,
        g.GRADUATION_STATE_REFEREE_HANDOFF_READY,
    ]
    assert "bundle_hash" in family_d["transitions"][-1]


# === TC-6: a second run against the SAME scoped root is an idempotent replay -- no duplicate row =====


def test_tc6_a_second_run_against_the_same_root_appends_no_duplicate_row(tmp_path):
    first_exit = seed.main(tmp_path)
    assert first_exit == 0
    ledger = _ledger_for(tmp_path)
    rows_after_first = ledger.all_rows()

    second_exit = seed.main(tmp_path)
    assert second_exit == 0
    rows_after_second = ledger.all_rows()

    assert len(rows_after_second) == len(rows_after_first)
    # every row is content-identical (chain-position fields aside) -- a genuine replay, not a
    # rebuild that happens to land on the same row count.
    def _content_only(rows: list[dict]) -> list[dict]:
        return [
            {k: v for k, v in row.items() if k not in ("row_index", "prev_hash", "row_hash")}
            for row in rows
        ]

    assert _content_only(rows_after_second) == _content_only(rows_after_first)

    # the chain itself still verifies -- a genuinely re-appended (vs. replayed) row would grow the
    # chain and still verify, so this is a companion check, not a substitute for the count/content
    # assertions above.
    assert ledger.verify_chain()["ok"] is True


def test_tc6_a_second_run_does_not_grow_the_walkforward_fold_ledger_either(tmp_path):
    """The upstream evidence this fixture's graduation transitions are built FROM must also stay
    replay-safe -- otherwise a second run could silently double-count folds even though the
    graduation ledger itself looks unchanged."""
    import app.research.walkforward_ledger as wl

    seed.main(tmp_path)
    wf_ledger = wl.WalkForwardLedger(str(tmp_path / "walkforward"))
    rows_after_first = wf_ledger.all_rows()

    seed.main(tmp_path)
    rows_after_second = wf_ledger.all_rows()

    assert len(rows_after_second) == len(rows_after_first) == 9  # 3 folds x (families B, C, D)


# === error case (TESTING REQUIREMENTS): a wrong target state/verdict is reported, never silently =====
# === swallowed. =========================================================================================


def test_main_exits_nonzero_and_reports_the_diverging_family_when_a_target_is_wrong(monkeypatch, tmp_path, capsys):
    """A silently-wrong fixture must never be reported as a passing seed. Monkeypatches Family A's
    own seed helper to return a WRONG verdict (mirroring a genuine divergence -- e.g. a future
    accidental change to ``_insufficient_observations`` that crept back up to 30 real observations)
    while every other family still seeds for real, and asserts ``main`` catches it."""

    real_seed_family_a = seed._seed_family_a

    def _wrong_seed_family_a(*args, **kwargs):
        family_root_id, _real_verdict = real_seed_family_a(*args, **kwargs)
        return family_root_id, "pass"  # WRONG -- Family A must read "insufficient"

    monkeypatch.setattr(seed, "_seed_family_a", _wrong_seed_family_a)

    exit_code = seed.main(tmp_path)
    assert exit_code == 1

    stderr = capsys.readouterr().err
    assert "MISMATCH" in stderr
    assert "family A" in stderr
    assert "ERROR" in stderr
