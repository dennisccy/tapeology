"""TR-16 -- the end-to-end known-null / planted-effect oracles (``docs/rapid-validation-spec.md``

section 9's own TR-16 row: "A synthetic known-null corpus survives nothing end-to-end (Scout +
folds); a synthetic planted-effect corpus is recovered with the planted sign and magnitude within
tolerance (mid-basis primary); byte-identical rerun"). Test-first contract: TC-21, TC-22 in
``docs/phases/goal-rapid-microscope-iter-5.md``.

**Synthetic, keyless, hand-built -- no real tick dataset or engine replay (a disclosed design
choice, ``walkforward.py``'s own module docstring).** Both fixtures are flat, session-clustered
``{session_date, symbol, feature_value, outcome_bps}`` corpora built directly in Python (the
``test_scout.py`` TR-8 calibration-fixture style), run through the SAME two production entry
points this era ships: ``scout.compute_p_screen`` (Scout's own descriptive screen -- proving the
corpus's OWN ground truth is honestly detectable/undetectable at that stage) and
``walkforward.build_folds`` / ``walkforward.evaluate_mode_b_fold`` / ``walkforward.sequence_verdict``
(the walk-forward engine's own fold machinery, evaluating a Mode B spec over the SAME candidate
cell's own outcome values as its observations). Nothing here re-implements either statistical
core a second way.

**Corpus shape (both fixtures, identical structure, different outcome-generating rule).** 70
sessions x 2 symbols x 4 anchors/symbol/session = 560 anchors; ``feature_value`` is a seeded
standard-normal draw deciding Scout's candidate/comparator split (``>= 0.0``); ``outcome_bps``
(bps) is ``planted_effect_bps + Uniform(-2, 2)`` for a candidate-cell anchor, ``Uniform(-2, 2)``
alone (mean 0) for a comparator-cell one -- ``planted_effect_bps = 0.0`` for the known-null corpus
(candidate and comparator are drawn from the IDENTICAL distribution: no true relationship exists
between ``feature_value`` and ``outcome_bps`` at all) and ``20.0`` for the planted-effect corpus
(a clearly recoverable, deterministic-by-construction mean shift). Walk-forward's own
``observations`` are the candidate cell's ``outcome_bps``s alone (``feature_value >= 0.0``) --
the "already selected rule, does it hold out of sample" question Mode B asks, mirrored from the
diagnostic run's own ``playbook_observations`` design.

Geometry: ``train=20, test=10, step=10, embargo=0`` (embargo=0 legitimate here -- each anchor is an
independent per-print draw with no cross-session memory, so no cross-boundary dependency exists to
name) over the 70 sessions produces exactly 5 folds, comfortably clearing every WF_FOLD_MIN_*
floor per fold (~37-43 observations, ~10 signal-carrying sessions, 2 symbols)."""

from __future__ import annotations

import random

import pytest

from app.research import scout
from app.research import walkforward as wf
from app.research.micro_accessor import ExposureRegistry
from app.research.walkforward_ledger import WalkForwardLedger

N_SESSIONS = 70
SYMBOLS = ("AAA", "BBB")
ANCHORS_PER_SYMBOL_PER_SESSION = 4
GEOMETRY = {"train_sessions": 20, "test_sessions": 10, "step_sessions": 10, "embargo_sessions": 0, "embargo_derivation": "each anchor is an independent per-print draw with no cross-session memory -- no cross-boundary dependency identified"}
ECON_FLOOR = {"floor_bps": 5.0, "unit": "bps"}  # r13: an economic floor must declare its unit

PLANTED_EFFECT_BPS = 20.0
PLANTED_TOLERANCE_BPS = 2.0


def _build_synthetic_corpus(*, planted_effect_bps: float, seed_key: str) -> list[dict]:
    rng = random.Random(seed_key)
    anchors: list[dict] = []
    for s in range(N_SESSIONS):
        session_date = f"2026-01-{s + 1:03d}"
        for symbol in SYMBOLS:
            for _ in range(ANCHORS_PER_SYMBOL_PER_SESSION):
                feature_value = rng.gauss(0.0, 1.0)
                if feature_value >= 0.0:
                    outcome_bps = planted_effect_bps + rng.uniform(-2.0, 2.0)
                else:
                    outcome_bps = rng.uniform(-2.0, 2.0)
                anchors.append(
                    {
                        "session_date": session_date, "symbol": symbol,
                        "feature_value": feature_value, "outcome_bps": outcome_bps,
                        "tod_bucket": "mid", "fallback_frac": 0.3,
                    }
                )
    return anchors


def _run_scout_screen(anchors: list[dict], *, seed_scope: str) -> tuple[float | None, float | None]:
    """The REAL production statistical core (``scout.compute_p_screen``), over the synthetic
    corpus directly -- no second implementation, the ``test_scout.py`` TR-8 precedent."""
    return scout.compute_p_screen(
        anchors, transform="threshold", params={"op": "ge", "value": 0.0}, seed_scope=seed_scope, block_length=1
    )


def _run_walkforward(anchors: list[dict], *, corpus_id: str, tmp_path) -> tuple[list[dict], dict]:
    """The REAL production fold machinery, over the SAME corpus's candidate-cell outcomes. A
    genuinely fresh ``ExposureRegistry`` (never r2-initialized for this made-up corpus_id) means
    every fold's window classifies ``historical_oos`` from the mechanical exposure rule alone --
    proving TR-16's oracles can legitimately reach a survivor verdict, unlike the real
    legacy/playbook corpora this era otherwise reads."""
    sessions = sorted({a["session_date"] for a in anchors})
    folds = wf.build_folds(sessions, GEOMETRY)
    observations = [
        {"session_date": a["session_date"], "symbol": a["symbol"], "value": a["outcome_bps"],
         "value_unit": wf.WF_OBSERVATION_UNIT}
        for a in anchors if a["feature_value"] >= 0.0
    ]
    ledger = WalkForwardLedger(str(tmp_path / f"{corpus_id}_ledger"))
    registry = ExposureRegistry(str(tmp_path / f"{corpus_id}_exposure"))
    spec = wf.register_mode_b_spec(
        corpus_id=corpus_id, rule_id="tr16_oracle_rule", sidedness="long", econ_floor=ECON_FLOOR,
        registered_at="2026-08-17T00:00:00.000000Z",
    )
    rows = [wf.evaluate_mode_b_fold(ledger, registry, spec=spec, fold=fold, observations=observations, floors={}) for fold in folds]
    verdict = wf.sequence_verdict(rows, sidedness="long", econ_floor=ECON_FLOOR, voided=False)
    return rows, verdict


# === TC-21: the known-null corpus survives nothing end to end =========================================


def test_tc21_the_known_null_corpus_survives_nothing_through_scout_screening():
    anchors = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
    effect_bps, p_screen = _run_scout_screen(anchors, seed_scope="tr16-known-null-scope")
    assert p_screen is not None and p_screen >= scout.SCOUT_SCREEN_ALPHA  # never falsely significant


def test_tc21_the_known_null_corpus_survives_nothing_through_walkforward_folds(tmp_path):
    anchors = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
    rows, verdict = _run_walkforward(anchors, corpus_id=wf.TR16_KNOWN_NULL_CORPUS_ID, tmp_path=tmp_path)
    assert len(rows) == 5
    assert all(row["status"] == wf.FOLD_STATUS_SUFFICIENT for row in rows)
    assert all(row["evidence_class"] == wf.EVIDENCE_CLASS_HISTORICAL_OOS for row in rows)
    assert verdict["refused"] is False
    assert verdict["verdict"] == "not_survivor"  # NEVER walkforward_survivor


def test_tc21_the_known_null_corpus_reproduces_byte_identically_on_rerun(tmp_path):
    anchors_first = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
    anchors_second = _build_synthetic_corpus(planted_effect_bps=0.0, seed_key="tr16-known-null")
    assert anchors_first == anchors_second  # the fixture itself is deterministic

    effect1, p1 = _run_scout_screen(anchors_first, seed_scope="tr16-known-null-scope")
    effect2, p2 = _run_scout_screen(anchors_second, seed_scope="tr16-known-null-scope")
    assert (effect1, p1) == (effect2, p2)

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    rows1, verdict1 = _run_walkforward(anchors_first, corpus_id="rerun-null-a", tmp_path=tmp_path / "a")
    rows2, verdict2 = _run_walkforward(anchors_second, corpus_id="rerun-null-b", tmp_path=tmp_path / "b")
    effects1 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows1]
    effects2 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows2]
    assert effects1 == effects2
    assert verdict1["verdict"] == verdict2["verdict"] == "not_survivor"


# === TC-22: the planted-effect corpus is recovered with the planted sign and magnitude ===============


def test_tc22_the_planted_effect_corpus_is_significant_through_scout_screening():
    anchors = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
    effect_bps, p_screen = _run_scout_screen(anchors, seed_scope="tr16-planted-effect-scope")
    assert effect_bps == pytest.approx(PLANTED_EFFECT_BPS, abs=PLANTED_TOLERANCE_BPS)
    assert p_screen is not None and p_screen < scout.SCOUT_SCREEN_ALPHA


def test_tc22_the_planted_effect_corpus_recovers_the_planted_sign_and_magnitude_through_walkforward(tmp_path):
    anchors = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
    rows, verdict = _run_walkforward(anchors, corpus_id=wf.TR16_PLANTED_EFFECT_CORPUS_ID, tmp_path=tmp_path)
    assert len(rows) == 5
    assert all(row["sign"] == "positive" for row in rows)  # the planted sign, every fold
    assert verdict["refused"] is False
    assert verdict["verdict"] == wf.WF_VERDICT_SURVIVOR
    assert verdict["rule_name"] == wf.WF_SURVIVOR_RULE_V1
    # mid-basis primary: the RECOVERED pooled effect matches the planted magnitude within tolerance
    assert verdict["pooled_effect"] == pytest.approx(PLANTED_EFFECT_BPS, abs=PLANTED_TOLERANCE_BPS)


def test_tc22_the_planted_effect_corpus_reproduces_byte_identically_on_rerun(tmp_path):
    anchors_first = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
    anchors_second = _build_synthetic_corpus(planted_effect_bps=PLANTED_EFFECT_BPS, seed_key="tr16-planted-effect")
    assert anchors_first == anchors_second

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    rows1, verdict1 = _run_walkforward(anchors_first, corpus_id="rerun-planted-a", tmp_path=tmp_path / "a")
    rows2, verdict2 = _run_walkforward(anchors_second, corpus_id="rerun-planted-b", tmp_path=tmp_path / "b")
    effects1 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows1]
    effects2 = [(r["fold_index"], r["effect"], r["sign"], r["n"]) for r in rows2]
    assert effects1 == effects2
    assert verdict1["pooled_effect"] == verdict2["pooled_effect"]
    assert verdict1["verdict"] == verdict2["verdict"] == wf.WF_VERDICT_SURVIVOR
