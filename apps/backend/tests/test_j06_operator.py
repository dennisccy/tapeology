"""The J-06 operator bridge's own refusals — TR-4 (widened, r12) and the §7 preflight STOP.

``scripts/j06_operator.py``.

Two production bugs are pinned here, both found only AFTER the real 80-symbol-day tranche had been
recorded, and both fixed under the owner's repair ruling:

1. **TR-4 could be laundered by arithmetic.** ``stage_verify`` computed
   ``disclosed = expected - recorded`` and passed that straight into
   ``vault.verify_recording_batch``. Any missing pair therefore classified ITSELF as a "disclosed
   vendor failure" purely by being missing, so the check could never fail. The typed J-06 verifier
   below derives the disclosed set from recorder RUN EVIDENCE and accepts no caller-supplied set.

2. **A legacy dataset could short-circuit the recorder.** ``stage_record`` treated any dataset at a
   registered ``(session_date, symbol)`` as ``already_recorded``, so the legacy partial NVDA
   2026-07-08 dataset made the recorder skip a registered pair entirely.

Plus the §7 pre-registration collision check itself, which read ``r.get("session_date") or
r.get("date")`` -- neither is a field on a dataset record, so every record keyed as
``(symbol, None)`` and a real collision passed preflight silently.

Every trap here carries its own counter-test: the pre-fix behaviour is exercised directly, so a
passing assertion proves the fix bites rather than that the scenario never arises.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.research import vault
from scripts import j06_operator as op

REGISTERED = {
    "universe_id": "u-test",
    "symbol_rule": ["AAA", "BBB"],
    "date_rule": ["2026-07-01", "2026-07-08"],
}
ALL_PAIRS = sorted(vault.expected_recording_pairs(REGISTERED))


def _record(symbol, session_date, *, genuine=True, partial=False, checksum="c0ffee"):
    """A dataset manifest record in the REAL served shape -- note there is no ``session_date`` and
    no ``date`` field, which is precisely why the pre-fix collision check could never match."""
    start = f"{session_date}T13:30:00Z"                      # 09:30 ET
    end = f"{session_date}T{'16:10' if partial else '20:00'}:00Z"   # 12:10 ET / 16:00 ET
    return {
        "id": f"ds-{symbol}-{session_date}-{'j06' if genuine else 'legacy'}",
        "symbol": symbol,
        "window_start_utc": start,
        "window_end_utc": end,
        "checksum": checksum,
        "created_utc": "2026-08-20T00:00:00.000000Z",
        "schema_basis": op.J06_SCHEMA_BASIS if genuine else None,
    }


# === §1: the typed verifier -- run evidence, never set subtraction ================================


def test_a_legacy_collision_with_zero_vendor_evidence_cannot_launder_itself_into_tr4():
    """THE trap the owner named: registered expected pair + legacy collision + zero vendor-failure
    evidence + no genuine J-06 dataset must NOT pass TR-4.

    The counter-half runs the PRE-FIX path directly -- the generic
    ``vault.verify_recording_batch`` with the missing pair handed in as a caller-supplied
    ``disclosed_failures`` entry, which is exactly what ``disclosed = expected - recorded``
    produced -- and asserts it returns ``ok``. That is the laundering, still reachable through the
    generic primitive (unchanged, by design) and no longer reachable through the J-06 path."""
    missing = ("BBB", "2026-07-08")
    recorded = {p: f"ds-{p[0]}-{p[1]}" for p in ALL_PAIRS if p != missing}
    collisions = [{"symbol": missing[0], "date": missing[1], "dataset_id": "legacy-1"}]

    result = op.verify_j06_batch(REGISTERED, recorded=recorded, collisions=collisions, runs=[])
    assert result["ok"] is False
    assert result["blocking_missing_pairs"] == {"BBB 2026-07-08": op.MISSING_LEGACY_COLLISION}
    assert result["disclosed_vendor_failures"] == []

    # counter-test: the pre-fix subtraction really did pass, so the assertion above is not vacuous
    laundered = vault.verify_recording_batch(
        REGISTERED, recorded=list(recorded), disclosed_failures=[missing])
    assert laundered == {"ok": True}


def test_the_j06_verifier_takes_no_caller_supplied_disclosed_failures():
    """Structural, not behavioural: the laundering surface is the ``disclosed_failures`` parameter,
    so the J-06 owner must not expose one at all. A future edit re-adding it fails here."""
    import inspect

    assert "disclosed_failures" not in inspect.signature(op.verify_j06_batch).parameters


def test_a_missing_pair_with_no_evidence_at_all_is_unexplained_and_blocks():
    missing = ("AAA", "2026-07-01")
    recorded = {p: "x" for p in ALL_PAIRS if p != missing}
    result = op.verify_j06_batch(REGISTERED, recorded=recorded, collisions=[], runs=[])
    assert result["ok"] is False
    assert result["blocking_missing_pairs"] == {"AAA 2026-07-01": op.MISSING_UNEXPLAINED}


def test_a_provenance_backed_unrecovered_vendor_failure_is_the_one_lawful_disclosure():
    missing = ("AAA", "2026-07-01")
    recorded = {p: "x" for p in ALL_PAIRS if p != missing}
    runs = [{"at": "2026-08-21T00:00:00Z", "outcomes": [
        {"symbol": "AAA", "date": "2026-07-01", "outcome": "failed",
         "detail": "ReadTimeout: vendor did not respond"}]}]
    result = op.verify_j06_batch(REGISTERED, recorded=recorded, collisions=[], runs=runs)
    assert result["ok"] is True
    assert result["disclosed_vendor_failures"] == [["AAA", "2026-07-01"]]
    assert "ReadTimeout" in result["vendor_failure_evidence"]["AAA 2026-07-01"]["detail"]


def test_a_pair_that_failed_then_recorded_is_not_an_unrecovered_failure():
    """Only the LAST outcome across every run counts -- a recovered pair must never be reported as
    a vendor failure, which would understate the tranche's own completeness claim."""
    runs = [
        {"at": "2026-08-21T00:00:00Z", "outcomes": [
            {"symbol": "AAA", "date": "2026-07-01", "outcome": "failed", "detail": "timeout"}]},
        {"at": "2026-08-21T01:00:00Z", "outcomes": [
            {"symbol": "AAA", "date": "2026-07-01", "outcome": "recorded", "dataset_id": "d1"}]},
    ]
    assert op.unrecovered_vendor_failures(runs) == {}
    result = op.verify_j06_batch(
        REGISTERED, recorded={p: "x" for p in ALL_PAIRS}, collisions=[], runs=runs)
    assert result["ok"] is True
    assert result["disclosed_vendor_failures"] == []


def test_a_collision_dominates_vendor_failure_evidence_for_the_same_pair():
    """"A collision may NEVER be converted into a vendor failure merely because the pair is
    missing" -- so when both signals exist for one pair, the collision wins and still blocks.
    Otherwise a single vendor hiccup on a collided pair would restore the laundering route."""
    missing = ("BBB", "2026-07-08")
    recorded = {p: "x" for p in ALL_PAIRS if p != missing}
    runs = [{"at": "2026-08-21T00:00:00Z", "outcomes": [
        {"symbol": "BBB", "date": "2026-07-08", "outcome": "failed", "detail": "timeout"}]}]
    collisions = [{"symbol": "BBB", "date": "2026-07-08", "dataset_id": "legacy-1"}]
    result = op.verify_j06_batch(
        REGISTERED, recorded=recorded, collisions=collisions, runs=runs)
    assert result["ok"] is False
    assert result["blocking_missing_pairs"] == {"BBB 2026-07-08": op.MISSING_LEGACY_COLLISION}


def test_a_complete_batch_verifies_through_the_typed_path(tmp_path):
    """End to end against a REALLY registered universe, so the typed verifier is proven to agree
    with ``vault.verify_recording_batch`` on the success case rather than only on refusals."""
    ledger = vault.VaultUniverseLedger(str(tmp_path))
    universe = vault.register_universe(
        ledger, universe_id="u-real", symbol_rule=["AAA", "BBB"],
        date_rule=["2026-07-01", "2026-07-08"],
        vault_secret_commitment=vault.commit_vault_secret(b"s3cret"),
    )
    recorded = {p: f"ds-{i}" for i, p in enumerate(sorted(vault.expected_recording_pairs(universe)))}
    result = op.verify_j06_batch(universe, recorded=recorded, collisions=[], runs=[])
    assert result["ok"] is True
    assert result["blocking_missing_pairs"] == {}


# === §2: what may count as an already-recorded J-06 shard =========================================


def test_a_legacy_dataset_is_not_a_genuine_j06_shard():
    expected = set(ALL_PAIRS)
    assert op.is_genuine_j06_dataset(_record("AAA", "2026-07-01"), expected) is True
    assert op.is_genuine_j06_dataset(_record("AAA", "2026-07-01", genuine=False), expected) is False


def test_the_full_session_floor_rejects_a_partial_window_carrying_the_recorder_schema_basis():
    """The legacy NVDA dataset was a partial window. Schema basis alone is not sufficient: a
    truncated recording that happened to carry the right basis would otherwise count."""
    expected = set(ALL_PAIRS)
    assert op.is_genuine_j06_dataset(_record("AAA", "2026-07-01", partial=True), expected) is False


def test_a_dataset_outside_the_registered_universe_or_without_a_checksum_is_not_a_j06_shard():
    expected = set(ALL_PAIRS)
    assert op.is_genuine_j06_dataset(_record("ZZZ", "2026-07-01"), expected) is False
    assert op.is_genuine_j06_dataset(_record("AAA", "2026-07-01", checksum=""), expected) is False


def test_a_genuine_shard_and_a_legacy_dataset_can_coexist_at_one_registered_pair():
    """The exact repair shape: the immutable legacy dataset stays on disk and stays reported as a
    collision, while the freshly recorded full-session shard is what the tranche counts."""
    records = [_record("AAA", "2026-07-01", genuine=False, partial=True, checksum="legacy"),
               _record("AAA", "2026-07-01")]
    recorded = op._recorded_pairs(None, REGISTERED, records=records)
    assert recorded == {("AAA", "2026-07-01"): "ds-AAA-2026-07-01-j06"}
    legacy = op._legacy_occupying_registered_pairs(None, REGISTERED, records=records)
    assert [(r["symbol"], r["date"], r["dataset_id"]) for r in legacy] == [
        ("AAA", "2026-07-01", "ds-AAA-2026-07-01-legacy")]


def test_under_repair_a_collision_no_longer_blocks_acceptance_once_the_pair_is_genuinely_recorded():
    records = [_record("BBB", "2026-07-08", genuine=False, partial=True, checksum="legacy")]
    records += [_record(s, d) for s, d in ALL_PAIRS]
    recorded = op._recorded_pairs(None, REGISTERED, records=records)
    collisions = op._legacy_occupying_registered_pairs(None, REGISTERED, records=records)
    assert len(recorded) == len(ALL_PAIRS)
    assert len(collisions) == 1                       # present, and still reported
    result = op.verify_j06_batch(
        REGISTERED, recorded=recorded, collisions=collisions, runs=[])
    assert result["ok"] is True                        # but no longer blocking: nothing is missing
    assert result["blocking_missing_pairs"] == {}


# === §5: the pre-registration collision check (the preflight regression) ==========================


def test_a_collision_is_detected_from_window_start_utc_not_from_a_session_date_field():
    records = [_record("AAA", "2026-07-01", genuine=False)]
    assert op.colliding_registered_pairs(records, ALL_PAIRS) == [("AAA", "2026-07-01")]

    # counter-test: the PRE-FIX expression, verbatim. Every record keys as (symbol, None), so the
    # membership test below can never match a registered pair -- the silent pass that shipped.
    broken = {(r["symbol"], r.get("session_date") or r.get("date")) for r in records}
    assert broken == {("AAA", None)}
    assert sorted(p for p in ALL_PAIRS if p in broken) == []


def test_the_derived_session_date_is_the_et_date_not_the_utc_date():
    """A record whose window opens at 00:30 UTC belongs to the PREVIOUS ET session. Slicing the
    UTC timestamp would name the wrong day, so this pins the ET derivation itself."""
    rec = {"id": "x", "symbol": "AAA", "window_start_utc": "2026-07-02T00:30:00Z",
           "window_end_utc": "2026-07-02T01:00:00Z", "checksum": "c", "schema_basis": None}
    assert op._session_date_of(rec) == "2026-07-01"
    assert rec["window_start_utc"][:10] == "2026-07-02"
    assert op.colliding_registered_pairs([rec], ALL_PAIRS) == [("AAA", "2026-07-01")]


def test_a_legacy_partial_same_day_dataset_is_a_collision_at_pre_registration():
    """A partial window is NOT a genuine shard (above) but IS still a collision: at pre-registration
    the STOP must fire on occupancy, before any market data is requested."""
    records = [_record("BBB", "2026-07-08", genuine=False, partial=True)]
    assert op.colliding_registered_pairs(records, ALL_PAIRS) == [("BBB", "2026-07-08")]
    assert op.is_genuine_j06_dataset(records[0], set(ALL_PAIRS)) is False


def test_the_preflight_stop_is_not_weakened_for_future_registrations():
    """The repair ruling applies to an ALREADY-registered universe. A fresh registration must still
    refuse outright, so the stage's own refusal string is pinned alongside the pure check."""
    import inspect

    source = inspect.getsource(op.stage_preflight)
    assert "colliding_registered_pairs" in source
    assert "raise SystemExit(" in source.split("colliding_registered_pairs", 1)[1]


# === §4: the residual-uncertainty model behind the TR-2 re-analysis ===============================


def test_one_disclosed_non_selected_position_leaves_the_hidden_set_undetermined():
    r = op.residual_pool_uncertainty(80, 21, disclosed_non_selected=1)
    assert r["unknown_positions"] == 79
    assert r["hidden_set_fully_determined"] is False
    assert r["any_identity_certain"] is False
    assert r["candidate_identities_per_unexposed_selected_shard"] >= 2
    assert r["feasible_selection_assignments"] > 10 ** 18


def test_disclosing_every_non_selected_position_WOULD_determine_the_hidden_set():
    """The non-vacuity counter-case: the model really can report certainty, so the passing result
    above is a measurement rather than a constant."""
    r = op.residual_pool_uncertainty(80, 21, disclosed_non_selected=59)
    assert r["unknown_positions"] == 21
    assert r["hidden_set_fully_determined"] is True
    assert r["any_identity_certain"] is True


@pytest.mark.parametrize("disclosed", [0, 1, 2, 30, 58])
def test_uncertainty_holds_for_every_disclosure_count_short_of_the_collapse_point(disclosed):
    r = op.residual_pool_uncertainty(80, 21, disclosed_non_selected=disclosed)
    assert r["any_identity_certain"] is False


# === §4 widened, iteration 24: the run-aware half that closes the sealing-time leak ================
#
# The combinatorial half above never reads `reports/j06-tranche/recording-runs.json` at all -- the
# iter-23 audit's own genuine finding. These tests exercise the widened check against the REAL
# committed run report (`op._load_recording_runs()`, no fixture stand-in -- its 7/13/1/0/0 split
# and four `2026-08-21` + one `2026-08-22` run timestamps are read directly off disk) crossed with
# a served-`sealed_at` list built the SAME way the real route builds it: through the real, production
# `vault._coarsen_sealed_at_to_date` function, never a hand-rolled slice reimplemented in the test.


def test_iter24_run_aware_check_passes_against_the_real_recording_runs_and_coarsened_sealed_at():
    """(a) TC-3's own contract: given the REAL committed run report and sealed_at served at the
    REAL (iteration-24, date-only) precision, every run-time-bucket's residual candidate count is
    `>= 2` and the check reports no violation. Reproduces today's actual shape -- all four
    2026-08-21 runs collapse into ONE date bucket (7+13+1+0=21 candidates), comfortably above the
    floor; the fifth run's 2026-08-22 bucket sealed nothing (`sealed_this_run=0`) so it contributes
    no bucket at all."""
    runs = op._load_recording_runs()
    assert [r["sealed_this_run"] for r in runs] == [7, 13, 1, 0, 0]  # today's real, on-record split

    served_sealed_at_values = []
    for run in runs:
        coarsened = vault._coarsen_sealed_at_to_date(run["at"])
        served_sealed_at_values.extend([coarsened] * run["sealed_this_run"])
    assert len(served_sealed_at_values) == 21

    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_sealed_at_values)

    assert result["any_bucket_below_floor"] is False
    assert result["worst_bucket_candidates"] >= 2
    assert result["buckets"] == {
        "2026-08-21": {
            "sealed_this_run_total": 21,
            "currently_sealed_served_count": 21,
            "candidate_identities_per_unexposed_selected_shard": 21,
        }
    }


def test_iter24_the_same_widened_check_correctly_FAILS_against_the_old_full_precision_join():
    """(b) The non-vacuity counter-test (the Study-3 break-then-restore precedent, applied to a
    check rather than a fix): feed the SAME widened logic a synthetic reproduction of the OLD,
    pre-iteration-24 full-precision `sealed_at` -- each shard's served value literally equal to its
    OWN run's `at` timestamp, joined against the SAME real 7/13/1/0/0 split -- and prove it
    correctly reports a violation. Without this, `any_bucket_below_floor is False` above would be
    unfalsifiable -- it could be `False` because the check never actually looks, not because the
    real data is safe."""
    runs = op._load_recording_runs()

    served_full_precision_sealed_at_values = []
    for run in runs:
        served_full_precision_sealed_at_values.extend([run["at"]] * run["sealed_this_run"])
    assert len(served_full_precision_sealed_at_values) == 21

    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_full_precision_sealed_at_values)

    assert result["any_bucket_below_floor"] is True
    # the third 2026-08-21 run sealed exactly one shard -- under full precision that shard is the
    # UNIQUE candidate in its own bucket, the exact identification the r5 floor exists to prevent.
    assert result["worst_bucket_candidates"] == 1
    third_run_at = runs[2]["at"]
    assert runs[2]["sealed_this_run"] == 1
    assert result["buckets"][third_run_at]["candidate_identities_per_unexposed_selected_shard"] == 1


def test_iter24audit_the_widened_check_also_fails_against_a_REALISTIC_old_full_precision_shape():
    """Iteration-24 audit finding B1 -- the counter-test above is necessary but NOT sufficient: it
    feeds each shard's served value as its own run's ``at`` string, an alignment that cannot occur
    in production. A run's ``at`` is stamped once at the END of the run by
    ``j06_operator._utc()`` (SECOND precision, ``2026-08-21T16:43:09Z``), while each shard's
    ``sealed_at`` is stamped per-seal by ``vault._iso_utc_now()`` (MICROSECOND precision,
    ``2026-08-21T16:42:19.876544Z``) -- so under the genuine pre-iteration-24 served shape no
    served value ever equalled a run key.

    Against the ORIGINAL implementation (which walked the RUN buckets and skipped any bucket a run
    did not claim) that meant zero buckets, ``any_bucket_below_floor: False`` -- the widened check
    reporting "safe" against exactly the leak it was built to catch. Keyed on the SERVED bucket
    instead, each distinct full-precision instant is its own anonymity set of ONE, and the floor
    correctly bites."""
    runs = op._load_recording_runs()

    # a faithful reconstruction of what `seal_shard` actually wrote per shard: distinct
    # microsecond-precision instants shortly BEFORE their own run's `at`, never equal to it.
    served_realistic_old_shape = []
    for run in runs:
        run_end = datetime.strptime(run["at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        n = run["sealed_this_run"]
        for i in range(n):
            instant = run_end - timedelta(seconds=(n - i) * 7, microseconds=123456 + i)
            served_realistic_old_shape.append(
                instant.isoformat(timespec="microseconds").replace("+00:00", "Z")
            )
    assert len(served_realistic_old_shape) == 21
    assert len(set(served_realistic_old_shape)) == 21           # every instant distinct...
    assert not set(served_realistic_old_shape) & {r["at"] for r in runs}   # ...and none is a run key

    result = op.residual_pool_uncertainty_by_run_time_bucket(runs, served_realistic_old_shape)

    assert result["any_bucket_below_floor"] is True
    assert result["worst_bucket_candidates"] == 1
    assert len(result["buckets"]) == 21
    assert all(
        b["candidate_identities_per_unexposed_selected_shard"] == 1 for b in result["buckets"].values()
    )


def test_iter24_stage_tr2_source_wires_the_run_aware_half_into_its_own_ok_gate():
    """Structural companion (the `test_the_preflight_stop_is_not_weakened...` precedent above): pins
    that `stage_tr2`'s own pass/fail gate actually consults the widened check's verdict, rather than
    computing it and discarding the result -- the failure mode a passing test-suite could otherwise
    hide."""
    import inspect

    source = inspect.getsource(op.stage_tr2)
    assert "residual_pool_uncertainty_by_run_time_bucket" in source
    assert 'not run_aware["any_bucket_below_floor"]' in source


def test_the_recorder_walk_derives_already_recorded_from_the_genuine_shard_predicate():
    """Structural companion to the repair: the walk must key off ``_recorded_pairs`` (hence
    ``is_genuine_j06_dataset``), never off a second, drifting "some dataset exists here" map. The
    pre-fix line was ``{(_session_date_of(r), r["symbol"]): r["id"] for r in store.list()[0]}``."""
    import inspect

    source = inspect.getsource(op.stage_record)
    assert "existing = _recorded_pairs(store, universe)" in source
    assert '_session_date_of(r), r["symbol"]' not in source


def test_the_recorder_walk_refuses_to_seal_a_disclosed_pool_position():
    import inspect

    source = inspect.getsource(op.stage_record)
    head, _, tail = source.partition("if key in disclosed_positions:")
    assert tail, "the walk must consult the disclosure ledger before sealing"
    assert "vault.compute_seal" not in head.split("disclosed_positions = ")[-1]
