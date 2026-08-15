"""``referee_registry.py`` + the ``/research/desk/referee/registry*`` routes (Era 6 "The Referee",
J-05) -- pre-registration with an immutable boundary. Test-first contract: TC-1 through TC-14 in
``docs/phases/goal-referee-iter-6.md``, full depth (mandatory per the prior ESCALATE verdict).

Fixtures build a complete, valid Estimand-A registration payload (``_estimand_a_payload``) that
each malformed-class test overrides exactly ONE field of -- and plant real ``PlaybookStore``
records (via that store's own public ``record`` write path, the ``test_referee_null.py``
precedent) for the accrual fold tests, since ``register_hypothesis``/``registry_response`` never
re-implement anything ``PlaybookStore`` already owns."""

from __future__ import annotations

import datetime
import sys
import zoneinfo

import pytest
from fastapi.testclient import TestClient

import app.research.referee_registry as referee_registry_module
from app.config import CONFIG
from app.main import app
from app.research.bars import BarStore
from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
from app.research.referee_registry import (
    REFEREE_MIN_OCCURRENCES,
    REFEREE_MIN_SESSIONS,
    REFEREE_STARTER_FAMILY_SHORTLIST,
    CertificateAlreadyRecorded,
    CertificateStore,
    ConfirmationRequired,
    FamilyAlreadyRecorded,
    FamilyStore,
    HypothesisAlreadyRecorded,
    HypothesisMalformed,
    HypothesisStore,
    RetroactiveBoundary,
    UnknownSpecId,
    WithdrawalRefused,
    WithdrawalStore,
    register_hypothesis,
    registry_response,
    shortlist_response,
    withdraw_hypothesis,
)

_ET = zoneinfo.ZoneInfo("America/New_York")


def _et_instant_iso(year: int, month: int, day: int, hour: int, minute: int) -> str:
    """An ISO-8601 UTC string for an ET wall-clock instant -- DST-correct by construction
    (mirrors ``test_referee_null.py`` TC-4's own ``datetime.combine(..., tzinfo=et)`` idiom,
    never a hand-computed UTC offset)."""
    dt = datetime.datetime.combine(
        datetime.date(year, month, day), datetime.time(hour, minute), tzinfo=_ET
    )
    return dt.astimezone(datetime.timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


# A fixed, mid-DST registration instant every test below uses unless it overrides
# ``registered_at`` itself: 2026-06-10 12:00 ET -> boundary "2026-06-10".
_REGISTERED_AT = _et_instant_iso(2026, 6, 10, 8, 0)
_BOUNDARY = "2026-06-10"


def _estimand_a_payload(hypothesis_id: str, family_id: str, **overrides: object) -> dict:
    """A complete, valid Estimand-A (``capitulation``/``long``/``5m``) registration payload --
    spec Sec7's S-1 shape. Each malformed-class test overrides exactly the one field it means to
    break."""
    payload = {
        "hypothesis_id": hypothesis_id,
        "family_id": family_id,
        "family_q": 0.10,
        "family_candidate_hypothesis_ids": [hypothesis_id],
        "evidence_family": "playbook",
        "estimand": "A",
        "setup_id": "capitulation",
        "side": "long",
        "context_predicate": None,
        "primary_measure_key": "5m",
        "primary_horizon": "5m",
        "sidedness": "greater",
        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID,
        "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS,
        "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "registered_at": _REGISTERED_AT,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def stores(tmp_path):
    family_store = FamilyStore(tmp_path / "registry")
    hypothesis_store = HypothesisStore(tmp_path / "registry")
    withdrawal_store = WithdrawalStore(tmp_path / "registry")
    certificate_store = CertificateStore(tmp_path / "registry")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    return family_store, hypothesis_store, withdrawal_store, certificate_store, playbook_store


@pytest.fixture
def bar_store(tmp_path):
    """A SEPARATE fixture (rather than growing ``stores``' own tuple, which every existing test in
    this file already destructures at a fixed length) -- only the iter-8 shortlist tests need a
    ``BarStore`` (``shortlist_response``'s S-4/S-5 band-context lookup requires one to construct a
    ``BandMapResolver``)."""
    return BarStore(tmp_path / "referee_bars")


def _plant_playbook_signals(
    playbook_store: PlaybookStore, session_date: str, signals: list[dict]
) -> None:
    """One playbook record at ``session_date`` carrying ``signals`` verbatim -- minimal dicts are
    sufficient (``PlaybookStore.record`` stores ``signals`` opaquely with zero shape validation,
    and the accrual fold reads only ``setup_id``/``side`` off each one)."""
    playbook_store.record(
        session_date=session_date,
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=f"sig-{session_date}",
        payload_version=3,
        parameters=playbook_parameters(),
        register=PLAYBOOK_REGISTER,
        signals=signals,
        absences=[],
        diagnostics=[],
    )


def _signal(setup_id: str, side: str, symbol: str = "AAA") -> dict:
    return {"setup_id": setup_id, "side": side, "symbol": symbol}


# === TC-1: FamilyStore -- duplicate family_id raises; exactly one record survives ====================


def test_tc1_duplicate_family_id_raises_and_store_keeps_exactly_one_record(stores):
    family_store, _hyp, _wd, _cert, _pb = stores
    fields = {
        "family_id": "fam-tc1",
        "q": 0.10,
        "candidate_hypothesis_ids": ["hyp-a", "hyp-b"],
        "registered_at": _REGISTERED_AT,
    }
    family_store.record(fields)
    with pytest.raises(FamilyAlreadyRecorded):
        family_store.record(fields)
    records, errors = family_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["family_id"] == "fam-tc1"


# === TC-2: a fixture Estimand-A registration returns a hypothesis_id; boundary == ET date =============


def test_tc2_estimand_a_registration_returns_a_hypothesis_id_with_the_correct_boundary(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc2", "fam-tc2")
    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert record["hypothesis_id"] == "hyp-tc2"
    assert record["confirmation_start_boundary"] == _BOUNDARY
    assert record["origin"] == "historical-exploration"
    assert record["detector_basis"] is not None  # playbook family -- server-computed
    assert record["context_predicate"] is None  # estimand A -- never contextual

    public_methods = {name for name in dir(HypothesisStore) if not name.startswith("_")}
    assert public_methods == {"root", "get", "list", "record"}  # no update/delete method


# === TC-3: missing required field (primary_horizon) refused, no record written =======================


def test_tc3_missing_required_field_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc3", "fam-tc3")
    del payload["primary_horizon"]
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    hyp_records, _errors = hypothesis_store.list()
    assert hyp_records == []
    fam_records, _errors = family_store.list()
    assert fam_records == []  # the family is never created behind a malformed hypothesis either


# === TC-4: an explicit boundary at/before registered_at's own ET date is refused =====================


def test_tc4_retroactive_boundary_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-tc4", "fam-tc4", confirmation_start_boundary=_BOUNDARY  # == registered_at's own date
    )
    with pytest.raises(RetroactiveBoundary):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []

    # A date strictly BEFORE registered_at's own ET date is refused too ("at or before").
    payload_earlier = _estimand_a_payload(
        "hyp-tc4b", "fam-tc4b", confirmation_start_boundary="2026-06-01"
    )
    with pytest.raises(RetroactiveBoundary):
        register_hypothesis(family_store, hypothesis_store, payload_earlier, confirm=True)
    assert hypothesis_store.list()[0] == []


# === TC-5: an unknown null_spec_id is refused, no record written =====================================


def test_tc5_unknown_null_spec_id_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc5", "fam-tc5", null_spec_id="referee-null-made-up-v9")
    with pytest.raises(UnknownSpecId):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


def test_tc5_unknown_test_spec_id_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc5b", "fam-tc5b", test_spec_id="referee-test-made-up-v9")
    with pytest.raises(UnknownSpecId):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


# === TC-6: an Estimand-C registration with an unevaluable context_predicate is refused ================


def test_tc6_estimand_c_unevaluable_context_predicate_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-tc6", "fam-tc6",
        estimand="C", setup_id="range_trade", side="long",
        context_predicate={"backing_bucket": "not_a_real_bucket"},
        primary_measure_key="1h", primary_horizon="1h",
    )
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


def test_tc6_estimand_c_missing_context_predicate_entirely_is_also_refused(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-tc6b", "fam-tc6b",
        estimand="C", setup_id="range_trade", side="long",
        context_predicate=None, primary_measure_key="1h", primary_horizon="1h",
    )
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


def test_tc6_estimand_c_valid_at_wall_context_predicate_is_accepted(stores):
    """The can-fail counter-test: a VALID ``backing_bucket`` (``at_wall``, spec Sec7 S-5) is
    accepted -- the refusal above is discriminating, not a blanket ban on Estimand C."""
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-tc6c", "fam-tc6c",
        estimand="C", setup_id="range_trade", side="long",
        context_predicate={"backing_bucket": "at_wall"},
        primary_measure_key="1h", primary_horizon="1h",
    )
    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert record["context_predicate"] == {"backing_bucket": "at_wall"}
    assert record["context_algorithm_version"] is not None


# === TC-7: target_sessions below REFEREE_MIN_SESSIONS is refused, no record written ===================


def test_tc7_target_sessions_below_the_floor_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc7", "fam-tc7", target_sessions=REFEREE_MIN_SESSIONS - 1)
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


def test_tc7_min_occurrences_below_the_floor_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-tc7b", "fam-tc7b", min_occurrences=REFEREE_MIN_OCCURRENCES - 1
    )
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []


# === TC-8: the ET-midnight boundary case (23:30 ET on a DST date) ====================================


def test_tc8_2330_et_registration_lands_on_the_same_et_calendar_date(stores):
    """2026-06-22 is DST (EDT, UTC-4) -- 23:30 ET on that date is 03:30 UTC on 2026-06-23. A naive
    implementation using the UTC calendar date would wrongly store "2026-06-23"; the correct,
    ET-aware boundary is "2026-06-22" -- the SAME ET date the registration instant fell on."""
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    registered_at = _et_instant_iso(2026, 6, 22, 23, 30)
    assert registered_at.startswith("2026-06-23T03:30:00")  # sanity: genuinely crosses midnight UTC

    payload = _estimand_a_payload("hyp-tc8", "fam-tc8", registered_at=registered_at)
    record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert record["confirmation_start_boundary"] == "2026-06-22"  # the ET date, not "2026-06-23"


# === TC-9 / TC-10: withdrawal ==========================================================================


def test_tc9_withdrawal_succeeds_when_no_post_boundary_evaluation_exists(stores):
    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
    payload = _estimand_a_payload("hyp-tc9", "fam-tc9")
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)

    withdrawn = withdraw_hypothesis(
        hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc9", reason="superseded",
        post_boundary_evaluation_exists=False,
    )
    assert withdrawn["hypothesis_id"] == "hyp-tc9"
    assert withdrawn["reason"] == "superseded"
    records, errors = withdrawal_store.list()
    assert errors == []
    assert len(records) == 1

    response = registry_response(
        family_store=family_store, hypothesis_store=hypothesis_store,
        withdrawal_store=withdrawal_store, certificate_store=cert_store,
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc9")
    assert folded["status"] == "withdrawn"

    public_methods = {name for name in dir(WithdrawalStore) if not name.startswith("_")}
    assert public_methods == {"root", "get", "list", "record"}  # no update/delete method


def test_tc10_withdrawal_refused_when_a_post_boundary_evaluation_exists(stores):
    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
    payload = _estimand_a_payload("hyp-tc10", "fam-tc10")
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)

    with pytest.raises(WithdrawalRefused):
        withdraw_hypothesis(
            hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10",
            post_boundary_evaluation_exists=True,
        )
    records, errors = withdrawal_store.list()
    assert errors == []
    assert records == []  # no WITHDRAWAL record written

    response = registry_response(
        family_store=family_store, hypothesis_store=hypothesis_store,
        withdrawal_store=withdrawal_store, certificate_store=cert_store,
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc10")
    assert folded["status"] == "active"


def test_withdrawal_of_an_unknown_hypothesis_id_is_refused(stores):
    _fam, hypothesis_store, withdrawal_store, _cert, _pb = stores
    with pytest.raises(WithdrawalRefused):
        withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="no-such-hypothesis")


def test_a_second_withdrawal_of_an_already_withdrawn_hypothesis_is_refused(stores):
    family_store, hypothesis_store, withdrawal_store, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-tc10b", "fam-tc10b")
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10b")
    with pytest.raises(WithdrawalRefused):
        withdraw_hypothesis(hypothesis_store, withdrawal_store, hypothesis_id="hyp-tc10b")
    records, _errors = withdrawal_store.list()
    assert len(records) == 1  # still exactly one -- the second attempt wrote nothing


# === TC-11: accrual fold matches a hand-counted value from a populated fixture corpus =================


def test_tc11_accrual_matches_a_hand_counted_value_over_two_distinct_setup_side_cells(stores):
    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
    hyp_a = _estimand_a_payload(
        "hyp-tc11-cap", "fam-tc11-cap", setup_id="capitulation", side="long"
    )
    hyp_b = _estimand_a_payload(
        "hyp-tc11-jbe", "fam-tc11-jbe", setup_id="jbe", side="long", primary_horizon="1h",
        primary_measure_key="1h",
    )
    register_hypothesis(family_store, hypothesis_store, hyp_a, confirm=True)
    register_hypothesis(family_store, hypothesis_store, hyp_b, confirm=True)

    # Pre-boundary (2026-06-10): must NEVER count, regardless of cell match.
    _plant_playbook_signals(playbook_store, "2026-06-09", [_signal("capitulation", "long")])
    # Post-boundary, both cells present the same date.
    _plant_playbook_signals(
        playbook_store, "2026-06-11",
        [_signal("capitulation", "long"), _signal("jbe", "long")],
    )
    # Post-boundary, capitulation/long only.
    _plant_playbook_signals(playbook_store, "2026-06-12", [_signal("capitulation", "long")])
    # Post-boundary, capitulation/long only (a third date for this cell).
    _plant_playbook_signals(playbook_store, "2026-06-16", [_signal("capitulation", "long")])
    # Post-boundary, jbe/long only.
    _plant_playbook_signals(playbook_store, "2026-06-15", [_signal("jbe", "long")])
    # A cell neither hypothesis names -- must never leak into either count.
    _plant_playbook_signals(playbook_store, "2026-06-17", [_signal("double_top", "short")])

    response = registry_response(
        family_store=family_store, hypothesis_store=hypothesis_store,
        withdrawal_store=withdrawal_store, certificate_store=cert_store,
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    folded_cap = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc11-cap")
    folded_jbe = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc11-jbe")

    # capitulation/long: 2026-06-11, 06-12, 06-16 -- three post-boundary dates (06-09 excluded).
    assert folded_cap["accrual"]["informative_post_boundary_sessions"] == 3
    # jbe/long: 2026-06-11, 06-15 -- two post-boundary dates.
    assert folded_jbe["accrual"]["informative_post_boundary_sessions"] == 2
    assert folded_cap["accrual"]["is_proxy"] is True
    assert folded_jbe["accrual"]["is_proxy"] is True
    assert folded_cap["accrual"]["target_sessions"] == hyp_a["target_sessions"]
    assert folded_jbe["accrual"]["target_sessions"] == hyp_b["target_sessions"]
    assert folded_cap["accrual"]["basis_current"] is True
    assert folded_jbe["accrual"]["basis_current"] is True

    # iter-8 (J-07): discovery is the exact pre-boundary COMPLEMENT of accrual, over the SAME
    # planted corpus -- 2026-06-09 is the only pre-boundary date, and it carries capitulation:long
    # only (never jbe:long); it must never contribute to either hypothesis's accrual above.
    assert folded_cap["discovery"] == {
        "n": 1, "n_sessions": 1, "label": "discovery (exploratory)",
    }
    assert folded_jbe["discovery"] == {
        "n": 0, "n_sessions": 0, "label": "discovery (exploratory)",
    }

    assert set(response) == {
        "families", "hypotheses", "withdrawals", "certificates", "integrity_errors",
    }
    assert response["integrity_errors"] == []


# === TC-12: CertificateStore -- shape-only, fixture-seeded, duplicate raises ==========================


def _fixture_certificate(certificate_id: str = "cert-tc12") -> dict:
    return {
        "certificate_id": certificate_id,
        "candidate": {"strategy_id": "structure_tape", "profile": "default"},
        "champion_identity_at_scan_time": {"strategy_id": "v1", "profile": "default"},
        "train_dataset": {"id": "ds-train", "checksum": "abc123", "split": "train"},
        "holdout_dataset": {"id": "ds-holdout", "checksum": "def456", "split": "holdout"},
        "config_fingerprint": CONFIG.config_fingerprint(),
        "gate_version": "referee-gate-v1",
        "referee_parameters_hash": "0" * 16,
        "family_id": "fam-tc12",
        "hypothesis_id": "hyp-tc12",
        "gate_results": {
            "calibrated_p": 0.01, "bh_pass": True, "ci": [0.1, 0.9], "floors_met": True,
        },
    }


def test_tc12_duplicate_certificate_id_raises_and_no_update_delete_method_exists(stores):
    _fam, _hyp, _wd, cert_store, _pb = stores
    fields = _fixture_certificate()
    cert_store.record(fields)
    with pytest.raises(CertificateAlreadyRecorded):
        cert_store.record(fields)
    records, errors = cert_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["certificate_id"] == "cert-tc12"

    public_methods = {name for name in dir(CertificateStore) if not name.startswith("_")}
    assert public_methods == {"root", "get", "list", "record"}


# === TC-13: CLI and POST produce byte-identical stored Hypothesis records =============================


def test_tc13_cli_and_post_produce_byte_identical_stored_hypothesis_records(tmp_path, monkeypatch):
    payload_fields = _estimand_a_payload("hyp-tc13", "fam-tc13")

    # Neither operator surface accepts a caller-chosen registration instant any more (iter-6
    # audit, finding B1) -- so byte-identity is established by freezing the SERVER clock both
    # paths stamp from, which is the stronger property: two acts at the same instant produce the
    # same record, with neither able to name that instant itself.
    monkeypatch.setattr(referee_registry_module, "_iso_utc_now", lambda: _REGISTERED_AT)

    cli_dir = tmp_path / "cli_registry"
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(cli_dir))
    monkeypatch.setattr(
        sys, "argv",
        [
            "referee_registry", "register",
            "--hypothesis-id", payload_fields["hypothesis_id"],
            "--family-id", payload_fields["family_id"],
            "--family-q", str(payload_fields["family_q"]),
            "--family-candidate-hypothesis-ids", *payload_fields["family_candidate_hypothesis_ids"],
            "--evidence-family", payload_fields["evidence_family"],
            "--estimand", payload_fields["estimand"],
            "--setup-id", payload_fields["setup_id"],
            "--side", payload_fields["side"],
            "--primary-measure-key", payload_fields["primary_measure_key"],
            "--primary-horizon", payload_fields["primary_horizon"],
            "--sidedness", payload_fields["sidedness"],
            "--null-spec-id", payload_fields["null_spec_id"],
            "--test-spec-id", payload_fields["test_spec_id"],
            "--target-sessions", str(payload_fields["target_sessions"]),
            "--min-occurrences", str(payload_fields["min_occurrences"]),
        ],
    )
    assert referee_registry_module.main() == 0
    cli_record = HypothesisStore(cli_dir).get("hyp-tc13")
    assert cli_record is not None

    post_dir = tmp_path / "post_registry"
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(post_dir))
    with TestClient(app) as client:
        resp = client.post(
            "/research/desk/referee/registry/hypotheses",
            json={**payload_fields, "confirm": True},
        )
    assert resp.status_code == 200
    post_record = HypothesisStore(post_dir).get("hyp-tc13")
    assert post_record is not None

    assert cli_record == post_record  # byte-identical stored records, two isolated stores


# === TC-14: the five starter-family candidates (spec Sec7 S-1..S-5) all register cleanly =============


def _starter_family_payloads() -> list[dict]:
    """spec Sec7's shortlist, verbatim (S-1..S-5) -- one family, the complete planned list."""
    ids = ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"]
    family_kwargs = {
        "family_id": "fam-starter", "family_q": 0.10, "family_candidate_hypothesis_ids": ids,
    }
    return [
        {  # S-1: A, capitulation:long, 5m
            "hypothesis_id": "hyp-s1", **family_kwargs, "evidence_family": "playbook",
            "estimand": "A", "setup_id": "capitulation", "side": "long",
            "context_predicate": None, "primary_measure_key": "5m", "primary_horizon": "5m",
            "sidedness": "greater", "null_spec_id": REFEREE_NULL_TOD_SPEC_ID,
            "test_spec_id": REFEREE_TEST_PERM_SPEC_ID, "target_sessions": REFEREE_MIN_SESSIONS,
            "min_occurrences": REFEREE_MIN_OCCURRENCES, "registered_at": _REGISTERED_AT,
        },
        {  # S-2: A, jbe:long, 1h
            "hypothesis_id": "hyp-s2", **family_kwargs, "evidence_family": "playbook",
            "estimand": "A", "setup_id": "jbe", "side": "long",
            "context_predicate": None, "primary_measure_key": "1h", "primary_horizon": "1h",
            "sidedness": "greater", "null_spec_id": REFEREE_NULL_TOD_SPEC_ID,
            "test_spec_id": REFEREE_TEST_PERM_SPEC_ID, "target_sessions": REFEREE_MIN_SESSIONS,
            "min_occurrences": REFEREE_MIN_OCCURRENCES, "registered_at": _REGISTERED_AT,
        },
        {  # S-3: A, double_top:short, to_close
            "hypothesis_id": "hyp-s3", **family_kwargs, "evidence_family": "playbook",
            "estimand": "A", "setup_id": "double_top", "side": "short",
            "context_predicate": None, "primary_measure_key": "to_close",
            "primary_horizon": "to_close", "sidedness": "greater",
            "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
            "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
            "registered_at": _REGISTERED_AT,
        },
        {  # S-4: B, range_trade:long at_wall vs other same-setup contexts, 1h -- no null
            "hypothesis_id": "hyp-s4", **family_kwargs, "evidence_family": "playbook",
            "estimand": "B", "setup_id": "range_trade", "side": "long",
            "context_predicate": {"backing_bucket": "at_wall"}, "primary_measure_key": "1h",
            "primary_horizon": "1h", "sidedness": "greater", "null_spec_id": None,
            "test_spec_id": REFEREE_TEST_PERM_SPEC_ID, "target_sessions": REFEREE_MIN_SESSIONS,
            "min_occurrences": REFEREE_MIN_OCCURRENCES, "registered_at": _REGISTERED_AT,
        },
        {  # S-5: C, range_trade:long + at_wall vs context/ToD-matched null, 1h
            "hypothesis_id": "hyp-s5", **family_kwargs, "evidence_family": "playbook",
            "estimand": "C", "setup_id": "range_trade", "side": "long",
            "context_predicate": {"backing_bucket": "at_wall"}, "primary_measure_key": "1h",
            "primary_horizon": "1h", "sidedness": "greater",
            "null_spec_id": "referee-null-context-v1", "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
            "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
            "registered_at": _REGISTERED_AT,
        },
    ]


def test_tc14_all_five_starter_candidates_register_cleanly_with_distinct_ids(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    recorded = []
    for payload in _starter_family_payloads():
        recorded.append(register_hypothesis(family_store, hypothesis_store, payload, confirm=True))

    hypothesis_ids = {r["hypothesis_id"] for r in recorded}
    assert len(hypothesis_ids) == 5  # five DISTINCT ids
    assert hypothesis_ids == {"hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"}

    by_id = {r["hypothesis_id"]: r for r in recorded}
    assert by_id["hyp-s1"]["estimand"] == "A" and by_id["hyp-s1"]["primary_horizon"] == "5m"
    assert by_id["hyp-s2"]["estimand"] == "A" and by_id["hyp-s2"]["primary_horizon"] == "1h"
    assert by_id["hyp-s3"]["estimand"] == "A" and by_id["hyp-s3"]["primary_horizon"] == "to_close"
    assert by_id["hyp-s4"]["estimand"] == "B" and by_id["hyp-s4"]["null_spec_id"] is None
    assert by_id["hyp-s5"]["estimand"] == "C" and by_id["hyp-s5"]["null_spec_id"] == "referee-null-context-v1"

    families, _errors = family_store.list()
    assert len(families) == 1  # one shared family -- the starter family
    assert families[0]["candidate_hypothesis_ids"] == ["hyp-s1", "hyp-s2", "hyp-s3", "hyp-s4", "hyp-s5"]


# === J-07 (iter-8): the starter-family shortlist -- GET .../registry/shortlist =========================
#
# spec Sec7's five PINNED module candidates beside LIVE readiness (goal.md J-07 Step 1). n/
# n_sessions for S-1..S-3 (estimand A) reuse playbook_occurrence_readiness()'s existing
# per_setup_side pooling; S-4/S-5 (at_wall context) reuse the referee-era's own band-context
# primitive (referee_null.resolve_occurrence_backing_bucket) -- see
# test_starter_context_readiness_discriminates_at_wall_from_off_wall_and_dedupes_sessions below for
# the non-vacuous proof that the S-4/S-5 wiring genuinely discriminates.


def test_tc1_shortlist_serves_exactly_five_pinned_candidates_with_non_negative_readiness(
    stores, bar_store,
):
    _fam, _hyp, _wd, _cert, playbook_store = stores  # an EMPTY corpus -- the honest baseline
    response = shortlist_response(
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
        bar_store=bar_store, config=CONFIG,
    )
    candidates = response["candidates"]
    assert [c["candidate_id"] for c in candidates] == ["S-1", "S-2", "S-3", "S-4", "S-5"]
    for candidate in candidates:
        assert candidate["n"] >= 0
        assert candidate["n_sessions"] >= 0
        assert candidate["accrual_rate_sessions_per_day"] >= 0
        assert candidate["target_sessions"] == REFEREE_MIN_SESSIONS
        assert candidate["min_occurrences"] == REFEREE_MIN_OCCURRENCES
        assert candidate["test_spec_id"] == REFEREE_TEST_PERM_SPEC_ID
        assert candidate["rationale"]  # a non-empty semantic sentence, per candidate

    by_id = {c["candidate_id"]: c for c in candidates}
    assert (by_id["S-1"]["estimand"], by_id["S-1"]["setup_id"], by_id["S-1"]["side"]) == (
        "A", "capitulation", "long",
    )
    assert (by_id["S-2"]["estimand"], by_id["S-2"]["setup_id"], by_id["S-2"]["side"]) == (
        "A", "jbe", "long",
    )
    assert (by_id["S-3"]["estimand"], by_id["S-3"]["setup_id"], by_id["S-3"]["side"]) == (
        "A", "double_top", "short",
    )
    assert by_id["S-4"]["estimand"] == "B" and by_id["S-4"]["context_predicate"] == {
        "backing_bucket": "at_wall",
    }
    assert by_id["S-4"]["null_spec_id"] is None  # Estimand B: no null population (spec Sec3.2)
    assert by_id["S-5"]["estimand"] == "C" and by_id["S-5"]["null_spec_id"] == "referee-null-context-v1"

    # These five are the exact SAME pinned definitions test_tc14 already registers through the
    # write path -- proof the shortlist's own module constants and the registration fixture stay
    # in lockstep (never two independently-drifting copies).
    assert [c["candidate_id"] for c in REFEREE_STARTER_FAMILY_SHORTLIST] == [
        "S-1", "S-2", "S-3", "S-4", "S-5",
    ]


def test_tc2_zero_jbe_long_signals_amid_a_nonempty_corpus_serves_zero_never_a_divide_by_zero(
    stores, bar_store,
):
    _fam, _hyp, _wd, _cert, playbook_store = stores
    # A nonempty corpus that carries NO jbe:long signal at all -- proves S-2's own zero reading is
    # a genuine per-cell fact, not an artifact of an all-empty store (the iter-5 lesson: a test
    # must exercise the regime where the assertion is actually discriminating).
    _plant_playbook_signals(playbook_store, "2026-06-01", [_signal("capitulation", "long")])

    response = shortlist_response(
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
        bar_store=bar_store, config=CONFIG,
    )
    by_id = {c["candidate_id"]: c for c in response["candidates"]}
    assert by_id["S-1"]["n"] == 1 and by_id["S-1"]["n_sessions"] == 1  # genuinely nonzero elsewhere

    s2 = by_id["S-2"]
    assert s2["setup_id"] == "jbe" and s2["side"] == "long"
    assert s2["n"] == 0
    assert s2["n_sessions"] == 0
    assert s2["accrual_rate_sessions_per_day"] == 0
    assert s2["projected_days_to_target"] is None  # never a divide-by-zero value


def test_shortlist_projected_days_is_measured_from_zero_never_net_of_historical_sessions(
    stores, bar_store,
):
    """iter-8 audit (B2), replacing the earlier "zero once the cell is already at target" pinning:
    ``target_sessions`` is a POST-boundary count everywhere it is used, and registering stamps the
    boundary at that instant -- so a candidate's own HISTORICAL ``n_sessions`` can never count
    toward it, and the projection must be measured from zero (``target_sessions / rate``). The
    old net-of-history reading served ``0.0`` ("ready now") for exactly the richest candidates,
    understating a real 50-120 day wait against the operator's own corpus, and counted historical
    observations as progress toward a confirmatory target."""
    _fam, _hyp, _wd, _cert, playbook_store = stores
    for i in range(REFEREE_MIN_SESSIONS + 3):
        _plant_playbook_signals(
            playbook_store, f"2026-05-{i + 1:02d}", [_signal("capitulation", "long")],
        )
    response = shortlist_response(
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
        bar_store=bar_store, config=CONFIG,
    )
    s1 = next(c for c in response["candidates"] if c["candidate_id"] == "S-1")
    # A cell ALREADY well past its own target -- the regime where the two readings disagree most.
    assert s1["n_sessions"] >= s1["target_sessions"]
    rate = s1["accrual_rate_sessions_per_day"]
    assert rate > 0
    assert s1["projected_days_to_target"] == pytest.approx(s1["target_sessions"] / rate)
    assert s1["projected_days_to_target"] > 0.0  # never "ready now" on historical evidence alone


def test_get_registry_shortlist_route_honest_state_against_a_real_empty_store(route_ctx):
    """TC-6 (the shortlist half): against the real store, with no operator action taken, the
    shortlist still serves 5 candidates and the registry's own hypotheses list stays empty -- the
    honest not-yet-acted state, never fabricated."""
    client, _tmp = route_ctx
    resp = client.get("/research/desk/referee/registry/shortlist")
    assert resp.status_code == 200
    body = resp.json()
    assert [c["candidate_id"] for c in body["candidates"]] == ["S-1", "S-2", "S-3", "S-4", "S-5"]

    registry = client.get("/research/desk/referee/registry")
    assert registry.json()["hypotheses"] == []


class _FakeWallResolver:
    """The wall at [99.9, 100.1] -- prices INSIDE it (or within 70bps of it) resolve ``at_wall``,
    prices far from it resolve ``off_wall`` (the ``test_referee_adjudicate.py``
    ``_FakeContextResolver`` pattern, reused here verbatim -- never a second fake-resolver
    implementation)."""

    def resolve(self, symbol, as_of_epoch):
        return {
            "bands": [
                {
                    "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
                    "quality_score": 1.0, "round_number": False, "member_count": 1,
                }
            ],
            "basis_as_of": "2026-06-21",
        }


def _context_signal(*, entry: float, symbol: str) -> dict:
    return {
        "setup_id": "range_trade", "side": "long", "symbol": symbol,
        "trigger_ts": _et_instant_iso(2026, 6, 21, 10, 0),  # fixed instant -- irrelevant to the fake
        "entry": entry, "invalidation_price": entry - 0.5,
    }


def test_starter_context_readiness_discriminates_at_wall_from_off_wall_and_dedupes_sessions(stores):
    """The non-vacuous proof S-4/S-5's own live readiness genuinely discriminates (not just "zero
    everywhere"): two ``at_wall`` occurrences on the SAME session (deduping to one date), one
    ``at_wall`` occurrence on a second session, and one ``off_wall`` occurrence that must NEVER
    count."""
    _fam, _hyp, _wd, _cert, playbook_store = stores
    _plant_playbook_signals(
        playbook_store, "2026-06-21",
        [
            _context_signal(entry=100.0, symbol="RTA"),   # containing the band -> at_wall
            _context_signal(entry=99.95, symbol="RTB"),    # containing the band -> at_wall
        ],
    )
    _plant_playbook_signals(
        playbook_store, "2026-06-22", [_context_signal(entry=100.05, symbol="RTC")],  # at_wall
    )
    _plant_playbook_signals(
        playbook_store, "2026-06-23", [_context_signal(entry=110.0, symbol="RTD")],  # off_wall
    )
    records, _errors = playbook_store.list()
    newest_by_date = referee_registry_module._newest_per_session_date(records)
    n, n_sessions = referee_registry_module._starter_context_readiness(
        newest_by_date, CONFIG.config_fingerprint(),
        setup_id="range_trade", side="long", backing_bucket="at_wall",
        context_resolver=_FakeWallResolver(),
    )
    assert n == 3  # RTA, RTB, RTC -- RTD (off_wall) never counts
    assert n_sessions == 2  # 2026-06-21 and 2026-06-22 -- the same-session pair dedupes to one date


def test_shortlist_s4_s5_readiness_reflects_the_at_wall_context_resolve(
    stores, bar_store, monkeypatch,
):
    """End-to-end wiring proof (not just the isolated helper above): ``shortlist_response()``
    itself serves nonzero S-4/S-5 readiness when the corpus genuinely carries ``at_wall``
    ``range_trade:long`` occurrences, by constructing a REAL ``BandMapResolver`` whose class this
    test monkeypatches to the fake wall (the class-level substitution ``referee_adjudicate.py``'s
    own estimand-B/C tests never needed, since those call the pooling function directly with an
    injected resolver instead of letting it construct one)."""
    _fam, _hyp, _wd, _cert, playbook_store = stores
    _plant_playbook_signals(
        playbook_store, "2026-06-21", [_context_signal(entry=100.0, symbol="RTA")],
    )
    monkeypatch.setattr(
        referee_registry_module, "BandMapResolver", lambda *args, **kwargs: _FakeWallResolver()
    )
    response = shortlist_response(
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
        bar_store=bar_store, config=CONFIG,
    )
    by_id = {c["candidate_id"]: c for c in response["candidates"]}
    assert by_id["S-4"]["n"] == 1 and by_id["S-4"]["n_sessions"] == 1
    assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1


# === TC-9 / TC-10 (iter-8): the write path stays generic; discovery is boundary-gated on
# session_date, never recorded_at ======================================================================


def test_tc9_a_non_shortlist_setup_side_still_registers_the_write_path_stays_generic(route_ctx):
    """TC-9: a hypothesis payload for a setup/side combination NOT among S-1..S-5 (``dbi:short``,
    estimand A, per the plan's own example) registers successfully -- the write path accepts any
    valid hypothesis, never only the five shortlist candidates."""
    client, _tmp = route_ctx
    payload = _estimand_a_payload("hyp-dbi-short", "fam-dbi-short", setup_id="dbi", side="short")
    resp = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["setup_id"] == "dbi" and body["side"] == "short"


def test_tc10_a_deep_backfilled_pre_boundary_record_lands_in_discovery_never_accrual(stores):
    """TC-10: a deep-backfilled record for a ``session_date`` before the boundary, recorded
    (written to disk) AFTER registration, contributes to ``discovery.n_sessions`` -- never to
    ``accrual.informative_post_boundary_sessions`` -- proving ``session_date``, not
    ``recorded_at``, gates the boundary. Also covers the boundary-INCLUSIVE edge: a record dated
    exactly ON the boundary date itself is discovery too (accrual admits only strictly-after)."""
    family_store, hypothesis_store, withdrawal_store, cert_store, playbook_store = stores
    payload = _estimand_a_payload("hyp-tc10-disc", "fam-tc10-disc")  # boundary == _BOUNDARY
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)

    _plant_playbook_signals(playbook_store, "2026-05-01", [_signal("capitulation", "long")])  # deep-backfilled
    _plant_playbook_signals(playbook_store, _BOUNDARY, [_signal("capitulation", "long")])  # ON the boundary
    _plant_playbook_signals(playbook_store, "2026-06-11", [_signal("capitulation", "long")])  # post-boundary

    response = registry_response(
        family_store=family_store, hypothesis_store=hypothesis_store,
        withdrawal_store=withdrawal_store, certificate_store=cert_store,
        playbook_store=playbook_store, config_fingerprint=CONFIG.config_fingerprint(),
    )
    folded = next(h for h in response["hypotheses"] if h["hypothesis_id"] == "hyp-tc10-disc")
    assert folded["discovery"]["n_sessions"] == 2  # 2026-05-01 and _BOUNDARY itself
    assert folded["discovery"]["n"] == 2
    assert folded["accrual"]["informative_post_boundary_sessions"] == 1  # 2026-06-11 only


# === family/hypothesis coupling: consistency + "no candidate joins retroactively" =====================


def test_a_hypothesis_id_not_among_its_own_familys_candidate_list_is_refused(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload(
        "hyp-outsider", "fam-coupling", family_candidate_hypothesis_ids=["hyp-someone-else"]
    )
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    assert hypothesis_store.list()[0] == []
    assert family_store.list()[0] == []  # the family is not created behind a refused hypothesis


def test_a_second_hypothesis_reusing_the_same_family_id_with_a_different_q_is_refused(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    ids = ["hyp-fam-x1", "hyp-fam-x2"]
    payload_1 = _estimand_a_payload(
        "hyp-fam-x1", "fam-x", family_q=0.10, family_candidate_hypothesis_ids=ids
    )
    register_hypothesis(family_store, hypothesis_store, payload_1, confirm=True)

    payload_2 = _estimand_a_payload(
        "hyp-fam-x2", "fam-x", family_q=0.20, family_candidate_hypothesis_ids=ids,  # q disagrees
        setup_id="jbe",
    )
    with pytest.raises(HypothesisMalformed):
        register_hypothesis(family_store, hypothesis_store, payload_2, confirm=True)
    hyp_records, _errors = hypothesis_store.list()
    assert len(hyp_records) == 1  # only the first hypothesis was ever written


def test_duplicate_hypothesis_id_raises_and_second_call_writes_nothing_new(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-dup", "fam-dup")
    register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    with pytest.raises(HypothesisAlreadyRecorded):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
    records, _errors = hypothesis_store.list()
    assert len(records) == 1


# === confirmation gate: no write without confirm=True =================================================


def test_confirm_false_is_refused_and_writes_nothing(stores):
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    payload = _estimand_a_payload("hyp-noconfirm", "fam-noconfirm")
    with pytest.raises(ConfirmationRequired):
        register_hypothesis(family_store, hypothesis_store, payload, confirm=False)
    assert hypothesis_store.list()[0] == []
    assert family_store.list()[0] == []


# === store discipline: no update/delete method exists anywhere on FamilyStore ========================


def test_family_store_has_no_update_or_delete_method():
    public_methods = {name for name in dir(FamilyStore) if not name.startswith("_")}
    assert public_methods == {"root", "get", "list", "record"}


# === the routes ========================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_DIR", str(tmp_path / "playbook"))
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(tmp_path / "registry"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    with TestClient(app) as client:
        yield client, tmp_path


def test_get_registry_honest_empty_state(route_ctx):
    client, _tmp = route_ctx
    resp = client.get("/research/desk/referee/registry")
    assert resp.status_code == 200
    assert resp.json() == {
        "families": [], "hypotheses": [], "withdrawals": [], "certificates": [],
        "integrity_errors": [],
    }


def test_post_then_get_registry_round_trips_through_the_real_route(route_ctx):
    client, _tmp = route_ctx
    payload = _estimand_a_payload("hyp-route", "fam-route")
    resp = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert resp.status_code == 200
    assert resp.json()["hypothesis_id"] == "hyp-route"

    listed = client.get("/research/desk/referee/registry")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["families"]) == 1
    assert len(body["hypotheses"]) == 1
    hyp = body["hypotheses"][0]
    assert hyp["hypothesis_id"] == "hyp-route"
    assert hyp["status"] == "active"
    assert hyp["accrual"]["is_proxy"] is True


# === iter-7 Rider 2 / TC-30: a corrupted registry file is surfaced, never a silent drop / 500 =========


def test_tc30_a_corrupted_hypothesis_file_is_surfaced_in_integrity_errors_never_500(route_ctx):
    client, tmp_path = route_ctx
    payload = _estimand_a_payload("hyp-tc30-ok", "fam-tc30")
    resp = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert resp.status_code == 200

    registry_dir = tmp_path / "registry"
    corrupt_path = registry_dir / "hypothesis-corrupt.json"
    corrupt_path.write_text("not valid json at all")

    listed = client.get("/research/desk/referee/registry")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["hypotheses"]) == 1  # the healthy record still lists
    assert body["hypotheses"][0]["hypothesis_id"] == "hyp-tc30-ok"
    assert len(body["integrity_errors"]) == 1
    error = body["integrity_errors"][0]
    assert error["store"] == "hypothesis"
    assert error["file"] == "hypothesis-corrupt.json"
    assert "error" in error and error["error"]


def test_post_missing_confirm_is_refused_422_and_writes_nothing(route_ctx):
    client, _tmp = route_ctx
    payload = _estimand_a_payload("hyp-route-noconfirm", "fam-route-noconfirm")
    resp = client.post("/research/desk/referee/registry/hypotheses", json=payload)  # no confirm
    assert resp.status_code == 422
    listed = client.get("/research/desk/referee/registry")
    assert listed.json()["hypotheses"] == []


def test_post_malformed_payload_is_refused_422(route_ctx):
    client, _tmp = route_ctx
    payload = _estimand_a_payload("hyp-route-malformed", "fam-route-malformed")
    del payload["primary_horizon"]
    resp = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert resp.status_code == 422


def test_post_duplicate_hypothesis_id_is_refused_409(route_ctx):
    client, _tmp = route_ctx
    payload = _estimand_a_payload("hyp-route-dup", "fam-route-dup")
    first = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert first.status_code == 200
    second = client.post(
        "/research/desk/referee/registry/hypotheses", json={**payload, "confirm": True}
    )
    assert second.status_code == 409


# === the CLI: withdraw subcommand ======================================================================


def test_cli_withdraw_subcommand(tmp_path, monkeypatch):
    registry_dir = tmp_path / "cli_withdraw_registry"
    monkeypatch.setenv("TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR", str(registry_dir))
    family_store = FamilyStore(registry_dir)
    hypothesis_store = HypothesisStore(registry_dir)
    register_hypothesis(
        family_store, hypothesis_store, _estimand_a_payload("hyp-cliw", "fam-cliw"), confirm=True
    )

    monkeypatch.setattr(
        sys, "argv",
        ["referee_registry", "withdraw", "--hypothesis-id", "hyp-cliw", "--reason", "test"],
    )
    assert referee_registry_module.main() == 0

    withdrawal_store = WithdrawalStore(registry_dir)
    records, errors = withdrawal_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["hypothesis_id"] == "hyp-cliw"


# === iter-6 audit regressions: the boundary can never be backdated through an operator surface ========


def test_post_cannot_backdate_the_boundary_via_a_caller_supplied_registered_at(route_ctx):
    """Audit finding B1. ``RetroactiveBoundary`` bolts the front door (an explicit
    ``confirmation_start_boundary`` at/before the honest date is refused, TC-4) -- this proves the
    back door is bolted too: a caller-supplied ``registered_at`` is NOT a way to choose the
    boundary. Before the fix this POST returned 200 with
    ``confirmation_start_boundary == "2024-12-31"`` and immediately accrued the three
    already-recorded HISTORICAL sessions below as post-boundary confirmation -- the era's
    "the historical atlas is exploratory forever" anti-goal, breached through the shipped route,
    into an append-only record with no delete path."""
    client, tmp_path = route_ctx
    playbook_store = PlaybookStore(tmp_path / "playbook")
    for session_date in ("2025-03-03", "2025-03-04", "2025-03-05"):
        _plant_playbook_signals(playbook_store, session_date, [_signal("capitulation", "long")])

    payload = _estimand_a_payload("hyp-backdate", "fam-backdate")
    resp = client.post(
        "/research/desk/referee/registry/hypotheses",
        json={**payload, "registered_at": "2025-01-01T00:00:00Z", "confirm": True},
    )
    assert resp.status_code == 200
    stored = resp.json()
    today_et = datetime.datetime.now(_ET).date().isoformat()
    assert stored["registered_at"] != "2025-01-01T00:00:00Z"  # server-stamped, never caller-chosen
    assert stored["confirmation_start_boundary"] == today_et  # NOT "2024-12-31"

    folded = client.get("/research/desk/referee/registry").json()["hypotheses"][0]
    # The three historical sessions sit BEFORE the honest boundary -- zero forward accrual.
    assert folded["accrual"]["informative_post_boundary_sessions"] == 0


def test_cli_register_has_no_registered_at_backdating_flag(monkeypatch):
    """Audit finding B1, the operator-CLI half: the flag is gone, so argparse itself refuses it
    (exit code 2) before any store is ever touched."""
    monkeypatch.setattr(
        sys, "argv",
        ["referee_registry", "register", "--hypothesis-id", "hyp-x",
         "--registered-at", "2020-01-01T00:00:00Z"],
    )
    with pytest.raises(SystemExit) as exc_info:
        referee_registry_module.main()
    assert exc_info.value.code == 2


def test_duplicate_hypothesis_id_under_a_new_family_id_writes_no_family_record(stores):
    """Audit finding B2. A duplicate ``hypothesis_id`` is a refusal class ("no record written") --
    including when the call also names a BRAND-NEW ``family_id``, the one ordering where the
    family write used to land BEFORE the hypothesis refusal and leave a permanent, never-deletable
    phantom family behind a registration that was refused."""
    family_store, hypothesis_store, _wd, _cert, _pb = stores
    register_hypothesis(
        family_store, hypothesis_store, _estimand_a_payload("hyp-b2", "fam-b2"), confirm=True
    )

    retry = _estimand_a_payload(
        "hyp-b2", "fam-b2-v2", family_q=0.20, family_candidate_hypothesis_ids=["hyp-b2"]
    )
    with pytest.raises(HypothesisAlreadyRecorded):
        register_hypothesis(family_store, hypothesis_store, retry, confirm=True)

    families, errors = family_store.list()
    assert errors == []
    assert [f["family_id"] for f in families] == ["fam-b2"]  # no phantom "fam-b2-v2"
    assert len(hypothesis_store.list()[0]) == 1


def test_cli_register_rejects_missing_required_argparse_flag(monkeypatch):
    """argparse itself refuses (exit code 2) a missing REQUIRED flag before ``main()``'s own body
    (the ``register_hypothesis`` validation) ever runs -- the ``referee_null.py`` CLI precedent."""
    monkeypatch.setattr(
        sys, "argv",
        ["referee_registry", "register", "--hypothesis-id", "hyp-incomplete"],  # everything else missing
    )
    with pytest.raises(SystemExit) as exc_info:
        referee_registry_module.main()
    assert exc_info.value.code == 2
