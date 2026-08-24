"""``vault.py`` (Era "The Rapid Microscope" J-06 step 3) -- test-first contract: TC-1 through
TC-9 plus TR-2/4/12/20, per ``docs/phases/goal-rapid-microscope-iter-9.md``. Mirrors
``test_scout_ledger.py``'s own split: most of these tests exercise the ledger's own primitives
directly over a throwaway ``tmp_path`` (no ``DatasetStore``/snapshot machinery needed for those --
a vault shard's ``dataset_id``/``content_checksum`` are opaque strings as far as this module's own
logic is concerned); the route-level tests load the already-committed hermetic PG fixtures (the
``test_scout_ledger._combined_fixture_store`` precedent) to prove the whole stack -- real dataset
metadata through ``seal_shard`` through every registered GET route -- end to end.

**TR-2 is an ADVERSARIAL JOIN-RESISTANCE SWEEP (spec section 7.5/section 9, revision r3), not a
whitelist review** -- see ``test_tr2_...`` at the bottom of this file. The iter-9 audit's finding
B1 showed why: the served field LIST can be perfectly minimal and the guarantee still be defeated,
because a served value that merely IDENTIFIES the shard on another surface leaks everything that
surface serves. So the sweep seals a real fixture shard, calls every registered GET route, and
asserts that nothing anywhere equals, contains, or derives that shard's dataset id, raw
``content_checksum``, symbol, window bounds or exact event counts -- and then executes the join
attack itself, feeding every value the vault DOES serve back into the dataset routes."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_accessor as ma
from app.research import vault
from app.research.datasets import DatasetStore
from app.research.scout_ledger import compute_family_root_id as _scout_compute_family_root_id
from scripts import seed_micro_vault_iter25_sealed_fixture as _iter25_seed_vault

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets"

# The one fixture secret every lifecycle test in this file keys its HMACs on. A literal, never the
# operator's real `TAPEOLOGY_VAULT_SECRET_FILE` -- no test in this repo ever reads that file.
_FIXTURE_SECRET = b"a-fixture-vault-secret"


def _write_secret_file(tmp_path: Path, content: str = "correct-horse-battery-staple") -> str:
    path = tmp_path / "vault_secret.txt"
    path.write_text(content)
    return str(path)


# === no reimplementation: this module reuses scout_ledger's own identity function verbatim ==========


def test_compute_family_root_id_is_the_same_function_object_scout_ledger_exports():
    """TR-20 depends on there being exactly one identity function -- proven directly, not merely
    by matching output, so a future accidental local reimplementation is caught immediately."""
    assert vault.compute_family_root_id is _scout_compute_family_root_id


# === TC-1/TC-2: universe registration + the rule_hash round trip ====================================


def test_tc1_an_unregistered_universe_id_refuses_batch_validation(tmp_path):
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    with pytest.raises(vault.VaultUniverseNotRegisteredError, match="never-registered-universe"):
        vault.verify_universe_recording_batch(
            ledger, "never-registered-universe", recorded=[("PG", "2026-06-09")]
        )


def test_tc2_a_registered_universe_round_trips_its_rule_hash_exactly(tmp_path):
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    symbol_rule = ["PG", "AAPL"]
    date_rule = ["2026-06-08", "2026-06-09"]
    commitment = vault.commit_vault_secret(b"a-fixture-secret")

    row = vault.register_universe(
        ledger, universe_id="starter-tranche-v1", symbol_rule=symbol_rule, date_rule=date_rule,
        vault_secret_commitment=commitment,
    )
    assert row["registered_at"] is not None
    assert row["rule_hash"] == vault.compute_rule_hash(symbol_rule, date_rule)

    reread = vault.find_universe(ledger, "starter-tranche-v1")
    assert reread["rule_hash"] == row["rule_hash"]
    assert reread["registered_at"] == row["registered_at"]
    assert reread["vault_secret_commitment"] == commitment


# === iter-9 audit fix B2: the registered rule is FROZEN (spec section 7.2) ==========================


def test_audit_b2_a_narrowed_re_registration_is_refused_and_cannot_neutralize_the_tr4_refusal(tmp_path):
    """The escape hatch this fix closes, reproduced end to end: register a 2x2 universe, watch a
    cherry-picked batch get refused (TR-4), then attempt exactly what spec section 7.2 forbids
    ("no substitution because a symbol is inconvenient") -- re-register the SAME ``universe_id``
    with the inconvenient symbol dropped. Pre-fix, ``find_universe``'s LATEST-row resolution made
    that second row govern and the identical batch validated ``{"ok": True}``. The registration
    must now refuse, append NO row, and leave the ORIGINAL rule still governing the verifier."""
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    commitment = vault.commit_vault_secret(b"secret")
    vault.register_universe(
        ledger, universe_id="starter-tranche-v1", symbol_rule=["PG", "AAPL"],
        date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
    )
    cherry_picked = [("PG", "2026-06-08"), ("PG", "2026-06-09")]  # AAPL dropped, nothing disclosed
    with pytest.raises(vault.CherryPickedBatchError):
        vault.verify_universe_recording_batch(ledger, "starter-tranche-v1", recorded=cherry_picked)

    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError) as exc_info:
        vault.register_universe(
            ledger, universe_id="starter-tranche-v1", symbol_rule=["PG"],
            date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
        )
    assert "starter-tranche-v1" in str(exc_info.value)

    assert len(ledger.all_rows()) == 1  # the refused registration appended nothing
    assert vault.find_universe(ledger, "starter-tranche-v1")["symbol_rule"] == ["PG", "AAPL"]
    # and the batch the re-registration was trying to legalize is STILL refused.
    with pytest.raises(vault.CherryPickedBatchError):
        vault.verify_universe_recording_batch(ledger, "starter-tranche-v1", recorded=cherry_picked)


def test_audit_b2_a_byte_identical_re_registration_is_an_idempotent_no_op(tmp_path):
    """A crash-retry of the ONE operator registration act must not fork the universe's history:
    an identical re-registration returns the EXISTING row (same ``registered_at``, same
    ``row_hash``) and appends no second row -- the era's own "idempotency everywhere, not
    everywhere except one path" lesson, applied to the freeze this fix introduces."""
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    commitment = vault.commit_vault_secret(b"secret")
    kwargs = dict(
        universe_id="starter-tranche-v1", symbol_rule=["PG", "AAPL"],
        date_rule=["2026-06-08", "2026-06-09"], vault_secret_commitment=commitment,
    )
    first = vault.register_universe(ledger, **kwargs)
    again = vault.register_universe(ledger, **kwargs)

    assert again["row_hash"] == first["row_hash"]
    assert again["registered_at"] == first["registered_at"]
    assert len(ledger.all_rows()) == 1
    assert ledger.verify_chain() == {"ok": True, "failed_at_row": None, "reason": None}


def test_audit_b2_a_re_registration_under_a_different_secret_commitment_is_also_refused(tmp_path):
    """The rule hash is not the only frozen half: swapping the vault secret under an already-
    registered universe would silently re-randomize which shards are sealed (section 7.3), so an
    identical rule with a DIFFERENT commitment is refused too."""
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.register_universe(
        ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(b"first-secret"),
    )
    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError):
        vault.register_universe(
            ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
            vault_secret_commitment=vault.commit_vault_secret(b"a-different-secret"),
        )
    assert len(ledger.all_rows()) == 1


# === TC-3/TC-4: TR-4 cherry-pick refusal + disclosed-failure success ================================


def _registered_universe_ledger(tmp_path) -> tuple[vault.VaultUniverseLedger, str]:
    ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.register_universe(
        ledger, universe_id="u1", symbol_rule=["PG", "AAPL"], date_rule=["2026-06-08", "2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(b"secret"),
    )
    return ledger, "u1"


def test_tc3_a_cherry_picked_batch_is_refused_naming_the_missing_entry(tmp_path):
    ledger, universe_id = _registered_universe_ledger(tmp_path)
    # the rule's full 2x2 = 4 pairs, minus ("AAPL", "2026-06-09") -- no disclosed failure for it.
    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08")]
    with pytest.raises(vault.CherryPickedBatchError) as exc_info:
        vault.verify_universe_recording_batch(ledger, universe_id, recorded=recorded)
    assert "('AAPL', '2026-06-09')" in str(exc_info.value)


def test_tc4_a_batch_matching_the_rule_minus_one_disclosed_failure_is_ok(tmp_path):
    ledger, universe_id = _registered_universe_ledger(tmp_path)
    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08")]
    result = vault.verify_universe_recording_batch(
        ledger, universe_id, recorded=recorded, disclosed_failures=[("AAPL", "2026-06-09")]
    )
    assert result == {"ok": True}


def test_an_unexpected_extra_entry_is_also_refused_never_silently_accepted(tmp_path):
    """The mirror image of TC-3: a batch carrying an entry OUTSIDE the registered rule (not merely
    short one) is refused too -- TR-4 guards both directions, never only under-recording."""
    ledger, universe_id = _registered_universe_ledger(tmp_path)
    recorded = [("PG", "2026-06-08"), ("PG", "2026-06-09"), ("AAPL", "2026-06-08"), ("AAPL", "2026-06-09"), ("MSFT", "2026-06-08")]
    with pytest.raises(vault.CherryPickedBatchError) as exc_info:
        vault.verify_universe_recording_batch(ledger, universe_id, recorded=recorded)
    assert "('MSFT', '2026-06-08')" in str(exc_info.value)


# === TC-5: the HMAC seal decision + the never-logged-raw-secret discipline ==========================


def test_tc5_the_seal_decision_is_deterministic_across_repeated_calls(tmp_path):
    secret = vault.load_vault_secret(_write_secret_file(tmp_path))
    first = vault.compute_seal(secret, "PG", "2026-06-09")
    second = vault.compute_seal(secret, "PG", "2026-06-09")
    assert first == second
    assert isinstance(first, bool)


def test_tc5_the_raw_secret_string_never_appears_in_a_universe_row_or_the_ledger_file_on_disk(tmp_path):
    raw_secret_text = "the-actual-raw-vault-secret-do-not-leak-me"
    secret = vault.load_vault_secret(_write_secret_file(tmp_path, raw_secret_text))
    commitment = vault.commit_vault_secret(secret)
    assert commitment != raw_secret_text  # sanity: the commitment is a sha256 hex digest, not the secret

    vault_dir = str(tmp_path / "vault")
    ledger = vault.VaultUniverseLedger(vault_dir)
    row = vault.register_universe(
        ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=commitment,
    )
    assert raw_secret_text not in json.dumps(row)
    assert row["vault_secret_commitment"] == commitment

    on_disk = (Path(vault_dir) / "vault_universe_ledger.jsonl").read_text()
    assert raw_secret_text not in on_disk


def test_tc5_a_missing_vault_secret_file_env_var_is_a_typed_refusal_never_a_crash(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_VAULT_SECRET_FILE", raising=False)
    with pytest.raises(vault.VaultSecretUnavailable):
        vault.load_vault_secret()


def test_tc5_an_unreadable_vault_secret_path_is_a_typed_refusal(tmp_path):
    with pytest.raises(vault.VaultSecretUnavailable):
        vault.load_vault_secret(str(tmp_path / "does-not-exist.txt"))


def test_tc5_an_empty_vault_secret_file_is_a_typed_refusal(tmp_path):
    path = tmp_path / "empty_secret.txt"
    path.write_text("   \n")
    with pytest.raises(vault.VaultSecretUnavailable):
        vault.load_vault_secret(str(path))


def test_tc5_the_env_var_is_read_when_no_explicit_path_is_given(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_VAULT_SECRET_FILE", _write_secret_file(tmp_path, "env-sourced-secret"))
    secret = vault.load_vault_secret()
    assert secret == b"env-sourced-secret"


# === TC-6: section 7.5 opaque pre-exposure serving ==================================================


_SEALED_DATASET_ID = "dataset-1"
_SEALED_CONTENT_CHECKSUM = "a" * 64


def _sealed_shard_ledger(
    tmp_path, *, dataset_id: str = _SEALED_DATASET_ID, event_count: int = 45_231
) -> vault.VaultShardLedger:
    ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    vault.seal_shard(
        ledger, dataset_id=dataset_id, universe_id="u1",
        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=event_count,
        vault_secret=_FIXTURE_SECRET,
    )
    return ledger


def test_tc6_a_sealed_shards_entry_carries_only_the_section_7_5_opaque_fields(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))

    state = vault.build_vault_state(shard_ledger, universe_ledger)
    assert len(state["shards"]) == 1
    entry = state["shards"][0]

    assert set(entry.keys()) == {"shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state"}
    assert entry["exposure_state"] == "sealed"
    assert "symbol" not in entry
    assert "session_date" not in entry
    assert "45231" not in json.dumps(entry)  # the exact event count never appears anywhere
    assert entry["size_bucket"] != 45_231
    # r3: neither of the two join keys the iter-9 audit found is served -- not the dataset id the
    # public dataset routes are keyed on, and not the raw content checksum they publish.
    assert _SEALED_DATASET_ID not in json.dumps(entry)
    assert _SEALED_CONTENT_CHECKSUM not in json.dumps(entry)


# === Iteration 24: the sealing-time-leak close -- served `sealed_at` is coarsened to date-only,
# while the underlying ledger row keeps its full precision (serve-time-only, never a ledger
# rewrite). TC-1/TC-2/TC-9. ===========================================================================

_DATE_ONLY_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_tc1_a_sealed_rows_served_sealed_at_is_date_only_precision(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))

    entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]

    assert _DATE_ONLY_SHAPE.match(entry["sealed_at"]), entry["sealed_at"]
    # the fixture's own full-precision seal instant (`_sealed_shard_ledger` lets `seal_shard`
    # default it via `_iso_utc_now`) always starts with the served value -- proving this is a
    # genuine coarsening of the SAME instant, not an unrelated string.
    stored_full_precision = shard_ledger.all_rows()[0]["sealed_at"]
    assert stored_full_precision.startswith(entry["sealed_at"])
    assert stored_full_precision != entry["sealed_at"]  # the time-of-day component was dropped


def test_tc2_the_underlying_ledger_rows_sealed_at_stays_full_precision_never_rewritten(tmp_path):
    """Proves the coarsening in `_serialize_shard` is a serve-time-only projection: reading the
    shard ledger DIRECTLY (bypassing `build_vault_state`/`_serialize_shard` entirely) must still
    show the original microsecond-precision ISO timestamp `seal_shard` wrote -- append-only
    discipline holds, nothing on disk was rewritten to accommodate the narrower served shape."""
    explicit_sealed_at = "2026-06-09T14:32:07.481932Z"
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    vault.seal_shard(
        shard_ledger, dataset_id=_SEALED_DATASET_ID, universe_id="u1",
        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=45_231,
        vault_secret=_FIXTURE_SECRET, sealed_at=explicit_sealed_at,
    )

    stored_row = shard_ledger.all_rows()[0]
    assert stored_row["sealed_at"] == explicit_sealed_at  # byte-identical, untouched

    served_entry = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(str(tmp_path / "vault")))["shards"][0]
    assert served_entry["sealed_at"] == "2026-06-09"
    assert stored_row["sealed_at"] != served_entry["sealed_at"]  # the two are genuinely different


def test_tc9_assigned_and_exposed_rows_also_serve_a_date_only_sealed_at(tmp_path):
    """TC-9: the coarsening is uniform across all three exposure states, not sealed-only -- an
    `assigned` or `exposed` shard's served `sealed_at` (inherited unchanged from its original
    sealed row, per `_row_content`) narrows exactly the same way."""
    explicit_sealed_at = "2026-06-09T14:32:07.481932Z"
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    vault.seal_shard(
        shard_ledger, dataset_id=_SEALED_DATASET_ID, universe_id="u1",
        content_checksum=_SEALED_CONTENT_CHECKSUM, event_count=45_231,
        vault_secret=_FIXTURE_SECRET, sealed_at=explicit_sealed_at,
    )
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")

    vault.assign_shard(
        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root,
        symbol="PG", session_date="2026-06-09",
    )
    assigned_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    assert assigned_entry["exposure_state"] == "assigned"
    assert _DATE_ONLY_SHAPE.match(assigned_entry["sealed_at"])
    assert assigned_entry["sealed_at"] == "2026-06-09"

    vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)
    exposed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    assert exposed_entry["exposure_state"] == "exposed"
    assert _DATE_ONLY_SHAPE.match(exposed_entry["sealed_at"])
    assert exposed_entry["sealed_at"] == "2026-06-09"

    # the underlying ledger rows for BOTH transitions still carry the original full-precision
    # value verbatim (`_row_content` carries it forward unchanged) -- never rewritten anywhere.
    for stored_row in shard_ledger.all_rows():
        assert stored_row["sealed_at"] == explicit_sealed_at


def test_r3_the_served_shard_id_is_a_surrogate_with_no_derivable_relation_to_the_dataset_id(tmp_path):
    """Spec section 7.5 point 1: "not the id, not a hash of it, not a prefix". Each of those three
    is checked literally, plus the property that makes the surrogate non-derivable at all -- it is
    keyed on the vault SECRET, so the same dataset id under a different secret mints a different
    token (an attacker holding every public dataset id still cannot compute the mapping)."""
    entry = vault.build_vault_state(
        _sealed_shard_ledger(tmp_path), vault.VaultUniverseLedger(str(tmp_path / "vault"))
    )["shards"][0]
    surrogate = entry["shard_id"]

    assert surrogate.startswith(vault.SURROGATE_SHARD_ID_PREFIX)
    assert surrogate != _SEALED_DATASET_ID
    assert hashlib.sha256(_SEALED_DATASET_ID.encode()).hexdigest() not in surrogate
    assert not surrogate.endswith(_SEALED_DATASET_ID) and _SEALED_DATASET_ID not in surrogate
    assert not _SEALED_DATASET_ID.startswith(surrogate.removeprefix(vault.SURROGATE_SHARD_ID_PREFIX))

    # deterministic under the same secret (the era's no-unseeded-randomness anti-goal) ...
    assert vault.compute_surrogate_shard_id(_FIXTURE_SECRET, _SEALED_DATASET_ID) == surrogate
    # ... and unpredictable without it.
    assert vault.compute_surrogate_shard_id(b"a-different-secret", _SEALED_DATASET_ID) != surrogate


def test_r3_the_sealed_commitment_is_salted_and_re_derivable_once_exposure_reveals_the_checksum(tmp_path):
    """Spec section 7.5 point 2: the pre-exposure commitment is ``HMAC(vault_secret,
    content_checksum)``, NOT the raw checksum (which is served publicly per dataset and would join
    directly) and not a plain hash of it (equally derivable). Auditability survives because
    exposure reveals the raw checksum, against which the salted commitment re-derives exactly."""
    shard_ledger = _sealed_shard_ledger(tmp_path)
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    sealed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    commitment = sealed_entry["checksum_commitment"]

    assert commitment != _SEALED_CONTENT_CHECKSUM
    assert commitment != hashlib.sha256(_SEALED_CONTENT_CHECKSUM.encode()).hexdigest()
    assert vault.commit_content_checksum(b"a-different-secret", _SEALED_CONTENT_CHECKSUM) != commitment

    family_root = vault.compute_family_root_id("f", "c", "o")
    vault.assign_shard(
        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root,
        symbol="PG", session_date="2026-06-09",
    )
    assigned_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    assert "content_checksum" not in assigned_entry  # still withheld at `assigned`
    assert assigned_entry["dataset_id"] == _SEALED_DATASET_ID  # the mapping IS revealed here (r3)

    vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)
    exposed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    assert exposed_entry["content_checksum"] == _SEALED_CONTENT_CHECKSUM
    # the whole point of a commitment: it verifies against what exposure revealed.
    assert vault.commit_content_checksum(_FIXTURE_SECRET, exposed_entry["content_checksum"]) == commitment


def test_size_bucket_is_order_of_magnitude_only_and_monotonic():
    assert vault._coarse_size_bucket(0) == "~0"
    small = vault._coarse_size_bucket(50)
    large = vault._coarse_size_bucket(45_231)
    assert small != large
    assert "45231" not in small and "45231" not in large


# === TC-7: assignment reveals symbol/date; the chain still verifies =================================


def test_tc7_assignment_reveals_symbol_and_date_and_the_chain_still_verifies(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    sealed_entry = vault.build_vault_state(shard_ledger, universe_ledger)["shards"][0]
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")

    vault.assign_shard(
        shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG",
        session_date="2026-06-09",
    )

    state = vault.build_vault_state(shard_ledger, universe_ledger)
    entry = state["shards"][0]
    assert entry["exposure_state"] == "assigned"
    assert entry["symbol"] == "PG"
    assert entry["session_date"] == "2026-06-09"
    assert entry["family_root_id"] == family_root
    # the opaque fields survive alongside the newly-revealed ones -- never REPLACED, only added to.
    assert entry["checksum_commitment"] == sealed_entry["checksum_commitment"]
    assert entry["shard_id"] == sealed_entry["shard_id"]
    assert state["shard_ledger_chain_verification"] == {"ok": True, "failed_at_row": None, "reason": None}


# === TC-8/TR-12: single-shot refusal =================================================================


def test_tc8_a_second_assignment_for_the_same_shard_is_refused_and_appends_no_row(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG", session_date="2026-06-09")
    rows_after_first_assignment = len(shard_ledger.all_rows())

    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG", session_date="2026-06-09")

    assert len(shard_ledger.all_rows()) == rows_after_first_assignment  # no new row for that pair


def test_audit_t1_a_genuinely_different_family_cannot_claim_an_already_assigned_shard(tmp_path):
    """iter-9 audit finding T1: TC-8/TC-9 both re-attempt with the SAME ``family_root_id``, so the
    module's disclosed shard-GLOBAL reading of TR-12 (docstring: "once a shard leaves ``sealed`` it
    belongs to exactly ONE family for the rest of its history") was never actually pinned -- it
    could have regressed silently to the looser (family, shard)-pair scope. This pins it.

    The shard-global rule refuses a strict superset of what TR-12's own row requires ("Second
    evaluation attempt of the same family on the same shard is refused"), so pinning it is safe
    while the owner ruling on scope (audit observation O1) is still open: a refusal can be
    tightened later and cannot safely be loosened once real sealed evidence exists."""
    shard_ledger = _sealed_shard_ledger(tmp_path)
    first_family = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    other_family = vault.compute_family_root_id("cumulative_delta_divergence", "level_test", "clock_60s")
    assert first_family != other_family  # genuinely different triples, genuinely different roots

    vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=first_family, symbol="PG", session_date="2026-06-09")
    rows_after_first_assignment = len(shard_ledger.all_rows())

    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=other_family, symbol="PG", session_date="2026-06-09")
    # ... and it cannot skip ahead to exposure either.
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=other_family)

    assert len(shard_ledger.all_rows()) == rows_after_first_assignment
    assert vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(str(tmp_path / "vault")))["shards"][0]["family_root_id"] == first_family


# === TC-9/TR-20: root-lineage stability -- a rename cannot evade the TC-8 refusal ====================


def test_tc9_a_same_triple_computes_the_same_root_regardless_of_a_renamed_candidate(tmp_path):
    """Two candidate registrations sharing the SAME (feature family, context kind, outcome family)
    triple compute the identical root even though everything ELSE about them (name, threshold
    parameterization -- neither of which is a `compute_family_root_id` input) differs."""
    root_named_a = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    root_named_b = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    assert root_named_a == root_named_b  # same triple in, same root out -- a pure function

    shard_ledger = _sealed_shard_ledger(tmp_path)
    vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=root_named_a, symbol="PG", session_date="2026-06-09")

    # the "rename" attempt: a second registration line computing the identical root (same triple)
    # tries to claim the SAME shard -- refused exactly like TC-8, proving renaming buys nothing.
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=root_named_b, symbol="PG", session_date="2026-06-09")


def test_tc9_a_genuinely_different_triple_computes_a_different_root_and_may_use_a_fresh_shard(tmp_path):
    root_a = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    root_c = vault.compute_family_root_id("cumulative_delta_divergence", "level_test", "clock_60s")
    assert root_a != root_c

    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    vault.seal_shard(shard_ledger, dataset_id="dataset-1", universe_id="u1", content_checksum="a" * 64, event_count=100, vault_secret=_FIXTURE_SECRET)
    vault.seal_shard(shard_ledger, dataset_id="dataset-2", universe_id="u1", content_checksum="b" * 64, event_count=200, vault_secret=_FIXTURE_SECRET)

    vault.assign_shard(shard_ledger, dataset_id="dataset-1", family_root_id=root_a, symbol="PG", session_date="2026-06-09")
    # a genuinely different family root assigning a DIFFERENT (freshly sealed) shard succeeds --
    # the single-shot refusal is about repeats on ONE shard, never a blanket freeze of the ledger.
    result = vault.assign_shard(shard_ledger, dataset_id="dataset-2", family_root_id=root_c, symbol="AAPL", session_date="2026-06-08")
    assert result["exposure_state"] == "assigned"


# === the full one-way lifecycle: sealed -> assigned -> exposed, and its order/repeat refusals =======


def test_expose_after_assign_succeeds_and_a_second_exposure_attempt_is_refused(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.assign_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root, symbol="PG", session_date="2026-06-09")

    exposed = vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)
    assert exposed["exposure_state"] == "exposed"
    assert exposed["exposed_at"] is not None
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset()  # no longer sealed

    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)


def test_expose_before_assignment_is_refused(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.expose_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, family_root_id=family_root)


def test_assign_before_sealing_is_refused(tmp_path):
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.assign_shard(shard_ledger, dataset_id="never-sealed", family_root_id="root", symbol="PG", session_date="2026-06-09")


def test_re_sealing_an_already_sealed_shard_is_refused(tmp_path):
    shard_ledger = _sealed_shard_ledger(tmp_path)
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.seal_shard(shard_ledger, dataset_id=_SEALED_DATASET_ID, universe_id="u1", content_checksum="a" * 64, event_count=1, vault_secret=_FIXTURE_SECRET)


# === the two bridge predicates: `currently_sealed` (walkforward) vs `withheld` (serving) ============


def _three_state_ledger(tmp_path) -> vault.VaultShardLedger:
    """One shard in each lifecycle state, so the two predicates below can be told apart."""
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    family_root = vault.compute_family_root_id("f", "c", "o")
    for dataset_id, checksum in (("still-sealed", "a" * 64), ("will-be-assigned", "b" * 64), ("will-be-exposed", "c" * 64)):
        vault.seal_shard(shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum=checksum, event_count=10, vault_secret=_FIXTURE_SECRET)
    vault.assign_shard(shard_ledger, dataset_id="will-be-assigned", family_root_id=family_root, symbol="PG", session_date="2026-06-09")
    vault.assign_shard(shard_ledger, dataset_id="will-be-exposed", family_root_id=family_root, symbol="PG", session_date="2026-06-10")
    vault.expose_shard(shard_ledger, dataset_id="will-be-exposed", family_root_id=family_root)
    return shard_ledger


def test_currently_sealed_dataset_ids_excludes_assigned_and_exposed_shards(tmp_path):
    assert vault.currently_sealed_dataset_ids(_three_state_ledger(tmp_path)) == frozenset({"still-sealed"})


def test_withheld_dataset_ids_covers_everything_not_yet_exposed(tmp_path):
    """The SERVING refusal's predicate (spec section 7.5 point 3: "until its exposure is
    recorded") is deliberately a superset of the walkforward filter's: the public dataset manifest
    carries the exact event counts section 7.5 withholds until EXPOSURE, so an ``assigned`` shard's
    manifest stays refused even though its symbol and date are by then public."""
    shard_ledger = _three_state_ledger(tmp_path)
    assert vault.withheld_dataset_ids(shard_ledger) == frozenset({"still-sealed", "will-be-assigned"})
    assert vault.withheld_universe_by_dataset_id(shard_ledger) == {
        "still-sealed": "u1", "will-be-assigned": "u1",
    }
    assert vault.currently_sealed_dataset_ids(shard_ledger) < vault.withheld_dataset_ids(shard_ledger)


def test_an_empty_vault_withholds_nothing_so_every_refusal_is_a_provable_no_op_today(tmp_path):
    """The whole r3 closure is fail-closed but inert until the first shard is sealed -- stated as
    a test so "nothing is sealed today" is a checked fact rather than a claim in a handoff."""
    empty = vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets"))
    assert vault.withheld_dataset_ids(empty) == frozenset()
    assert vault.currently_sealed_dataset_ids(empty) == frozenset()


# === TR-2: the adversarial join-resistance sweep (spec section 7.5/section 9, r3) ===================
#
# The rig every route-level test below shares. THREE datasets live in a throwaway store:
#
#   * the two already-committed PG fixtures -- the PUBLIC siblings. They must stay fully served
#     throughout, which is what proves the refusal is a targeted withholding rather than a blanket
#     break of the dataset surface.
#   * one purpose-built shard recorded through the store's OWN public write path, with values
#     chosen to be globally distinctive: a symbol in no panel/universe, a window in no other
#     payload, and event counts that are unusual integers. That is what makes "this value appears
#     in ZERO response bodies of ZERO routes" a meaningful assertion instead of a coincidence hunt
#     -- with a PG shard, "PG" appears legitimately on eight desk surfaces that never heard of the
#     vault, and the assertion would have to be weakened to survive.


_SWEEP_SYMBOL = "ZQXVLT"  # in no panel, no universe, no fixture -- see the rig note above
_SWEEP_WINDOW_START = "2031-03-17T13:31:07Z"
_SWEEP_WINDOW_END = "2031-03-17T19:57:41Z"
_SWEEP_TRADES = 137
_SWEEP_QUOTES = 241


def _combined_fixture_store(tmp_path: Path) -> DatasetStore:
    target = tmp_path / "datasets"
    target.mkdir()
    for path in _FIXTURE_DIR.glob("*.json"):
        shutil.copy(path, target / path.name)
    return DatasetStore(target)


def _record_distinctive_dataset(store: DatasetStore) -> dict:
    """One hermetic dataset through ``DatasetStore.record``'s own public write path (never a
    hand-typed file), carrying `_SWEEP_TRADES` trades and `_SWEEP_QUOTES` quotes."""
    events: list = []
    for i in range(_SWEEP_QUOTES):
        events.append(QuoteEvent(_SWEEP_SYMBOL, float(i), 99.99, 100.02, 100, 100))
    for i in range(_SWEEP_TRADES):
        events.append(TradeEvent(_SWEEP_SYMBOL, float(i) + 0.5, 100.03, 10, Side.BUY))
    return store.record(
        symbol=_SWEEP_SYMBOL, source="historical", source_kind="historical", source_id=_SWEEP_SYMBOL,
        split="train", window_start_utc=_SWEEP_WINDOW_START, window_end_utc=_SWEEP_WINDOW_END,
        data_feed="sip", epoch_anchor=0.0, events=events,
    )


# Every store/cache the swept routes can reach, pointed at throwaway paths. A sweep that reads the
# operator's REAL forward/referee/playbook stores is not a trap, it is a coincidence detector: the
# first run of this test against unscoped stores flagged three routes for "serving" the integers
# 137/241/378, which were real sample sizes in the operator's own data and had nothing to do with
# any sealed shard. Hermetic stores make "this value appears nowhere" mean what it says.
_SCOPED_DIR_ENV_VARS = (
    "TAPEOLOGY_DESK_UNIVERSE_DIR", "TAPEOLOGY_DESK_SCREEN_DIR", "TAPEOLOGY_DESK_SCREEN_LOG_DIR",
    "TAPEOLOGY_DESK_FORWARD_DIR", "TAPEOLOGY_DESK_FORWARD_LOG_DIR", "TAPEOLOGY_DESK_PLAYBOOK_DIR",
    "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
    "TAPEOLOGY_DESK_DEEP_BACKFILL_LOG_DIR", "TAPEOLOGY_DESK_TOPUP_LOG_DIR",
    "TAPEOLOGY_DESK_INDEX_RECONCILE_DIR", "TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR",
    "TAPEOLOGY_DESK_REFEREE_EVAL_DIR", "TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR",
    "TAPEOLOGY_DESK_REFEREE_NULL_DIR", "TAPEOLOGY_DESK_REFEREE_NULL_LOG_DIR",
    "TAPEOLOGY_MICRO_SNAPSHOTS_DIR", "TAPEOLOGY_MICRO_SCOUT_DIR", "TAPEOLOGY_MICRO_WALKFORWARD_DIR",
    "TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR", "TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR",
    "TAPEOLOGY_MICRO_RECORDER_LOG_DIR",
)
_SCOPED_DB_ENV_VARS = (
    "TAPEOLOGY_JOURNAL_DB", "TAPEOLOGY_BAR_INDEX_DB", "TAPEOLOGY_BAR_VERIFY_CACHE_DB",
    "TAPEOLOGY_DATASET_INDEX_DB", "TAPEOLOGY_EDGE_REPORT_CACHE_DB", "TAPEOLOGY_EDGE_SWEEP_CACHE_DB",
    "TAPEOLOGY_FORWARD_META_CACHE_DB", "TAPEOLOGY_MICRO_READINESS_CACHE_DB",
    "TAPEOLOGY_PLAYBOOK_CONTEXT_CACHE_DB", "TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB",
    "TAPEOLOGY_REFEREE_OBS_CACHE_DB", "TAPEOLOGY_SCREEN_META_CACHE_DB", "TAPEOLOGY_SETUPS_CACHE_DB",
    "TAPEOLOGY_TRADABILITY_CACHE_DB",
)


def _scope_everything_to(tmp_path: Path, monkeypatch) -> None:
    """Point every store, log and cache a swept route can reach at a throwaway path -- so the
    operator's real `.data` is neither read nor written by this file, and every payload is either
    honestly empty or built from this test's own three datasets. `TAPEOLOGY_VAULT_SECRET_FILE` is
    deliberately NOT set: no test in this repo ever reads the operator's real vault secret."""
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_VAULT_DIR", str(tmp_path / "micro_vault"))
    for name in _SCOPED_DIR_ENV_VARS:
        monkeypatch.setenv(name, str(tmp_path / name.lower()))
    for name in _SCOPED_DB_ENV_VARS:
        monkeypatch.setenv(name, str(tmp_path / f"{name.lower()}.db"))


def _sweepable_get_paths() -> list[str]:
    """Every registered GET path, read off the app's OWN OpenAPI schema -- never a hand-maintained
    list that a future route could be added without (the sweep has to stay complete by
    construction, which is exactly what the r3 TR-2 row demands)."""
    return sorted(path for path, ops in app.openapi()["paths"].items() if "get" in ops)


def _scalars(value, out: list) -> list:
    if isinstance(value, dict):
        for item in value.values():
            _scalars(item, out)
    elif isinstance(value, list):
        for item in value:
            _scalars(item, out)
    else:
        out.append(value)
    return out


def test_tr2_no_registered_get_route_serves_or_derives_a_sealed_shards_identity(tmp_path, monkeypatch):
    """TR-2 (r3), by construction: seal a shard, call EVERY registered GET route, and assert that
    none of them equals, contains, or derives its dataset id, raw ``content_checksum``, symbol,
    window bounds or exact event counts -- then execute the join attack itself with the values the
    vault DOES serve. The audit's finding B1 was reproducible in exactly this shape."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)
    public_metas = [m for m in store.list()[0] if m["id"] != sealed_meta["id"]]
    assert len(public_metas) == 2  # the two committed PG fixtures, untouched by any of this
    assert sealed_meta["event_counts"] == {"trades": _SWEEP_TRADES, "quotes": _SWEEP_QUOTES, "total": 378}

    vault.seal_shard(
        vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )

    forbidden_substrings = {
        "dataset id": sealed_meta["id"],
        "raw content checksum": sealed_meta["checksum"],
        "symbol": _SWEEP_SYMBOL,
        "window start": _SWEEP_WINDOW_START,
        "window end": _SWEEP_WINDOW_END,
    }
    forbidden_scalars = {_SWEEP_TRADES, _SWEEP_QUOTES, sealed_meta["event_counts"]["total"]}

    swept: dict[str, int] = {}
    leaks: list[str] = []
    with TestClient(app) as client:
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", sealed_meta["id"])
            if "{" in url:
                continue  # a parameterized path with no sealed-shard-reachable value to fill
            response = client.get(url)
            swept[path] = response.status_code
            for name, token in forbidden_substrings.items():
                if token in response.text:
                    leaks.append(f"{path} serves the sealed shard's {name}")
            try:
                payload_scalars = _scalars(response.json(), [])
            except ValueError:
                payload_scalars = []
            hits = sorted({s for s in payload_scalars if s in forbidden_scalars})
            if hits:
                leaks.append(f"{path} serves the sealed shard's exact event counts {hits}")

        assert leaks == [], "join-resistance breached:\n  " + "\n  ".join(leaks)
        # A trap that silently sweeps nothing proves nothing: this floor (against ~66 GET paths
        # registered today) fails loudly if the enumeration above ever stops finding routes.
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        # sanity: the sweep really did run against a live surface, not an empty route table.
        assert swept["/research/datasets"] == 200
        assert swept["/research/desk/micro/vault"] == 200
        assert swept["/research/desk/micro/readiness"] == 200
        # goal-rapid-microscope-iter-31 (J-11): `desk_graduation`'s own REST route -- confirmed
        # covered by this SAME structural sweep (never a second, route-by-route sweep of its own).
        assert swept["/research/desk/micro/graduation"] == 200
        # goal-rapid-microscope-iter-33 (J-12): `desk_micro_snapshots`'s own REST route (already
        # registered since J-02, now carrying two new disclosure fields) -- confirmed covered by
        # this SAME structural sweep too.
        assert swept["/research/desk/micro/snapshots"] == 200
        assert swept["/research/datasets/{dataset_id}"] == 403  # the sealed id, refused

        # --- the join attack, EXECUTED (not merely asserted absent) -------------------------
        entry = client.get("/research/desk/micro/vault").json()["shards"][0]
        assert set(entry) == {"shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state"}
        for field, value in entry.items():
            probe = client.get(f"/research/datasets/{value}")
            assert probe.status_code != 200, f"the served {field} resolves to a dataset -- it is a join key"
            with pytest.raises(Exception):
                store.get(str(value))

        # --- and a backtest (an outcome aggregate over the shard's events) is refused --------
        created = client.post(
            "/research/backtests",
            json={"dataset_id": sealed_meta["id"], "strategy_id": "v1", "profile": "default"},
        )
        assert created.status_code == 403
        assert "sealed" in created.json()["detail"]
        assert client.get("/research/backtests").json()["backtests"] == []


def _poll_compute(client, path: str) -> dict:
    """Poll a compute manager's own progress route until it reaches a terminal state."""
    snap = client.get(path).json()
    for _ in range(900):
        if snap["state"] in ("done", "failed", "cancelled"):
            return snap
        time.sleep(0.05)
        snap = client.get(path).json()
    raise AssertionError(f"{path} never reached a terminal state: {snap}")


def test_tr2_holds_after_the_operator_runs_every_micro_compute_act(tmp_path, monkeypatch):
    """TR-2 (r3), AFTER the two operator compute acts that populate the swept surfaces --
    iter-9 audit finding B1 (second pass).

    The sweep above calls every GET route against a rig where nothing has been COMPUTED, so most
    payloads are honestly empty and cannot leak whatever they would have carried. That made the
    trap pass by accident: pressing ``/desk``'s existing Snapshots-Compute and Scout-Compute
    buttons made ``GET /research/desk/micro/snapshots`` serve the sealed shard's ``dataset_id``,
    its RAW ``dataset_checksum``, its exact ``row_count`` and ``bytes_on_disk``, and made
    ``GET /research/desk/micro/scout`` publish that same id and raw checksum into an APPEND-ONLY
    hash-chained ledger -- while the screening itself read the sealed shard's snapshot rows and
    folded them into an exploratory statistic.

    So this test runs the compute acts FIRST and only then sweeps. Its counter-test half is just
    as important: the two public PG siblings must still be snapshotted and still be screened, so
    the closure is a targeted withholding rather than a blanket break of the micro surface."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)
    public_ids = sorted(m["id"] for m in store.list()[0] if m["id"] != sealed_meta["id"])

    vault.seal_shard(
        vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )

    forbidden_substrings = {
        "dataset id": sealed_meta["id"],
        "raw content checksum": sealed_meta["checksum"],
        "symbol": _SWEEP_SYMBOL,
        "window start": _SWEEP_WINDOW_START,
        "window end": _SWEEP_WINDOW_END,
    }
    forbidden_scalars = {_SWEEP_TRADES, _SWEEP_QUOTES, sealed_meta["event_counts"]["total"]}

    with TestClient(app) as client:
        assert client.post("/research/desk/micro/snapshots/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
        assert client.post("/research/desk/micro/scout/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"

        # the counter-test: both compute acts really did work, on the PUBLIC siblings.
        built = client.get("/research/desk/micro/snapshots").json()["snapshots"]
        assert sorted(m["dataset_id"] for m in built) == public_ids
        families = client.get("/research/desk/micro/scout").json()["families"]
        assert families, "the scout run recorded no family at all -- the counter-test is vacuous"
        screened = {
            entry["dataset_id"]
            for family in families
            for trial in family["trials"]
            for entry in trial["corpus_manifest"]
        }
        assert sorted(screened) == public_ids

        leaks: list[str] = []
        swept: dict[str, int] = {}
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", sealed_meta["id"])
            if "{" in url:
                continue
            response = client.get(url)
            swept[path] = response.status_code
            for name, token in forbidden_substrings.items():
                if token in response.text:
                    leaks.append(f"{path} serves the sealed shard's {name}")
            try:
                payload_scalars = _scalars(response.json(), [])
            except ValueError:
                payload_scalars = []
            hits = sorted({s for s in payload_scalars if s in forbidden_scalars})
            if hits:
                leaks.append(f"{path} serves the sealed shard's exact event counts {hits}")

        assert leaks == [], "join-resistance breached after compute:\n  " + "\n  ".join(leaks)
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        assert swept["/research/desk/micro/snapshots"] == 200
        assert swept["/research/desk/micro/scout"] == 200


def test_tc7_micro_snapshots_withheld_excluded_is_pool_derived_not_snapshot_file_derived(tmp_path, monkeypatch):
    """TC-7 (goal-rapid-microscope-iter-33, J-12; spec section 7.5 point 6, r4): `GET
    /research/desk/micro/snapshots`'s `withheld_excluded` must be POOL-derived (through
    `micro_snapshots`'s shared `_unresolved_pool_ids` choke point -- the SAME one
    `withheld_dataset_ids_for_store`/`exclude_withheld` already share), never a count of which
    withheld ids happen to have a `*.meta.json` file present on disk. A withheld shard's snapshot
    build NEVER RUNS at all (`run_snapshot_build_and_record`'s own filter), so a snapshot-file-
    derived implementation would ALWAYS report `0` for a withheld dataset that has, correctly,
    never had a snapshot built for it -- silently under-disclosing the pool and leaking sealed-
    pool build state by omission.

    This test registers a universe whose RULE matches one real dataset's own (symbol,
    session_date) -- never sealing it, never building any snapshot at all (the rule-membership
    withholding case, spec section 7.5 point 7/r5, exercised without any vault shard-ledger row)
    -- and asserts the served count is `1` while the snapshots directory stays entirely empty
    throughout, non-vacuously proving the count comes from the POOL predicate, not from counting
    meta files on disk."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    withheld_meta = _record_distinctive_dataset(store)

    universe_ledger = vault.universe_ledger_for_dataset_dir(str(tmp_path / "datasets"))
    vault.register_universe(
        universe_ledger,
        universe_id="tc7-pool-only-universe",
        symbol_rule=[_SWEEP_SYMBOL],
        date_rule=["2031-03-17"],  # the ET calendar date of _SWEEP_WINDOW_START (EDT, UTC-4)
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
        registered_at="2020-01-01T00:00:00.000000Z",  # well before the dataset's real created_utc
    )

    with TestClient(app) as client:
        body = client.get("/research/desk/micro/snapshots").json()
        assert body["snapshots"] == [], (
            "no snapshot was ever built for anything -- a file-derived count would report 0 here"
        )
        assert body["withheld_excluded"] == 1, (
            "withheld_excluded did not count the rule-matched pool member -- it is snapshot-file-"
            "derived, not pool-derived (TC-7)"
        )
        assert body["stale_excluded"] == 0
        assert withheld_meta["id"] not in {row.get("dataset_id") for row in body["snapshots"]}


def test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route(tmp_path, monkeypatch):
    """Spec section 7.5's "TR-2 sweeps every registered route, closing the ``get_endpoint`` path
    STRUCTURALLY". The MCP server is a byte-identical GET proxy that imports nothing from ``app``
    (its own module docstring), so it cannot leak anything the REST surface does not: this test
    proves the two surfaces coincide -- every static MCP tool path under ``/research/`` and every
    path its ``get_endpoint`` allowlist can reach is a path the sweep above actually called."""
    from app.mcp import ALLOWED_GET_PREFIXES, _STATIC_PATHS

    swept = set(_sweepable_get_paths())
    research_tool_paths = {p for p in _STATIC_PATHS.values() if p.startswith("/research/")}
    assert "/research/datasets" in research_tool_paths  # the `datasets` tool r3 names explicitly
    # goal-rapid-microscope-iter-31 (J-11): `desk_graduation` is now wired into `_STATIC_PATHS` --
    # a direct, non-vacuous proof the new tool is actually present in this set (not merely implied
    # by the subset assertion below, which would still pass if the entry were silently missing).
    assert "/research/desk/micro/graduation" in research_tool_paths
    # goal-rapid-microscope-iter-33 (J-12): `desk_micro_snapshots` is now wired into
    # `_STATIC_PATHS` too -- the SAME direct, non-vacuous proof, now that the route it proxies
    # carries two new disclosure fields.
    assert "/research/desk/micro/snapshots" in research_tool_paths
    assert research_tool_paths <= swept

    reachable = {p for p in swept if p.startswith(ALLOWED_GET_PREFIXES) and "{" not in p}
    assert reachable, "the get_endpoint allowlist reaches no path at all -- the sweep is vacuous"
    assert reachable <= swept


def test_tr2_the_public_siblings_stay_fully_served_while_one_shard_is_sealed(tmp_path, monkeypatch):
    """The counter-test that keeps the refusal honest: withholding one sealed shard must not break
    (or quietly thin) the dataset surface for everything else, and the withholding itself must be
    DISCLOSED rather than silent -- ``sealed_withheld`` says how many rows are not being shown."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)
    public_metas = [m for m in store.list()[0] if m["id"] != sealed_meta["id"]]

    with TestClient(app) as client:
        before = client.get("/research/datasets").json()
        assert [row["id"] for row in before["datasets"]] == [m["id"] for m in store.list()[0]]
        assert before["sealed_withheld"] == 0  # nothing sealed yet

        vault.seal_shard(
            vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
            dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
            content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
            vault_secret=_FIXTURE_SECRET,
        )

        after = client.get("/research/datasets").json()
        assert [row["id"] for row in after["datasets"]] == [m["id"] for m in public_metas]
        assert after["sealed_withheld"] == 1
        assert after["integrity_errors"] == []
        for meta in public_metas:
            detail = client.get(f"/research/datasets/{meta['id']}")
            assert detail.status_code == 200
            assert detail.json()["dataset"] == meta  # byte-identical to the stored row, as always

        refusal = client.get(f"/research/datasets/{sealed_meta['id']}")
        assert refusal.status_code == 403
        detail_text = refusal.json()["detail"]
        assert "sealed" in detail_text
        # the refusal itself says NOTHING beyond "this id is sealed" (spec section 7.5 point 3).
        for token in (_SWEEP_SYMBOL, _SWEEP_WINDOW_START, _SWEEP_WINDOW_END, "starter-tranche-v1", str(_SWEEP_TRADES)):
            assert token not in detail_text

        # 404 still means 404 -- the refusal did not swallow the unknown-id contract.
        assert client.get("/research/datasets/no-such-dataset-id").status_code == 404


def test_tr2_readiness_serves_sealed_tranche_aggregates_only(tmp_path, monkeypatch):
    """Spec section 7.5 point 4: "Readiness serves sealed-tranche AGGREGATES only (shard count,
    total symbol-days, per-universe totals) -- never a per-shard row, never a per-shard
    ``exposure_state``." The iter-9 audit found this table rendering a sealed shard's symbol,
    session date and exact counts on ``/desk``, mislabelled ``exploratory``."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)
    public_metas = [m for m in store.list()[0] if m["id"] != sealed_meta["id"]]

    with TestClient(app) as client:
        before = client.get("/research/desk/micro/readiness").json()
        assert before["sealed_tranche"] == {"shard_count": 0, "symbol_days": 0, "by_universe": {}}
        assert sorted(row["dataset_id"] for row in before["shards"]) == sorted(m["id"] for m in store.list()[0])

        vault.seal_shard(
            vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
            dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
            content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
            vault_secret=_FIXTURE_SECRET,
        )

        after = client.get("/research/desk/micro/readiness").json()
        assert [row["dataset_id"] for row in after["shards"]] == [m["id"] for m in public_metas]
        assert after["sealed_tranche"] == {
            "shard_count": 1,
            "symbol_days": 1,
            "by_universe": {"starter-tranche-v1": {"shard_count": 1, "symbol_days": 1}},
        }
        assert after["totals"]["distinct_datasets"] == len(public_metas)
        # the exploratory half is untouched by the withholding -- the PG fixtures' own rows are
        # byte-identical to what they were before anything was sealed.
        assert after["shards"] == [row for row in before["shards"] if row["dataset_id"] != sealed_meta["id"]]


# === GET /research/desk/micro/vault: honest empty state, then the three-stage reveal ================


def test_get_vault_route_serves_honest_empty_state_then_tr2_opaque_then_full_provenance(tmp_path, monkeypatch):
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    real_meta = store.list()[0][0]  # the first committed PG fixture's real, checksum-verified meta
    vault_dir = str(tmp_path / "micro_vault")

    with TestClient(app) as client:
        empty = client.get("/research/desk/micro/vault")
        assert empty.status_code == 200
        assert empty.json() == {
            "universes": [], "shards": [],
            "shard_ledger_chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
            "universe_ledger_chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
        }

        shard_ledger = vault.VaultShardLedger(vault_dir)
        vault.seal_shard(
            shard_ledger, dataset_id=real_meta["id"], universe_id="starter-tranche-v1",
            content_checksum=real_meta["checksum"], event_count=real_meta["event_counts"]["total"],
            vault_secret=_FIXTURE_SECRET,
        )

        sealed = client.get("/research/desk/micro/vault")
        body = sealed.json()
        assert len(body["shards"]) == 1
        entry = body["shards"][0]
        assert set(entry.keys()) == {"shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state"}
        assert entry["shard_id"] == vault.compute_surrogate_shard_id(_FIXTURE_SECRET, real_meta["id"])
        assert entry["checksum_commitment"] == vault.commit_content_checksum(_FIXTURE_SECRET, real_meta["checksum"])
        assert "symbol" not in entry
        assert real_meta["id"] not in json.dumps(entry)
        assert real_meta["checksum"] not in json.dumps(entry)
        assert str(real_meta["event_counts"]["total"]) not in json.dumps(entry)

        family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
        vault.assign_shard(
            shard_ledger, dataset_id=real_meta["id"], family_root_id=family_root,
            symbol=real_meta["symbol"], session_date="2026-06-09",
        )
        assigned = client.get("/research/desk/micro/vault").json()
        assert assigned["shards"][0]["symbol"] == real_meta["symbol"]
        assert assigned["shards"][0]["exposure_state"] == "assigned"
        assert assigned["shards"][0]["dataset_id"] == real_meta["id"]


# === spec section 7.5 point 6 (r4, owner ruling): the compute-first sweep, widened to the =========
# === corpus-wide REPORT acts (iter-9 re-audit finding B2) ========================================
#
# The lesson the re-audit paid for twice: a route sweep proves nothing about a surface that has
# computed nothing. `test_tr2_holds_after_the_operator_runs_every_micro_compute_act` above closed
# that for the two `/desk` micro Compute buttons; this closes it for the two acts that enumerate
# the dataset store and drive `BacktestJobManager` DIRECTLY, bypassing the r3 route guard --
# `edge_report` (the `/structure` Edge Report compute) and `pnl_scan` (the sweep CLI). Both
# persist a backtest result carrying the stored `dataset` manifest VERBATIM, which
# `GET /research/backtests` serves and `pnl_ledger` copies into an APPEND-ONLY row.


def test_tr2_holds_after_the_corpus_wide_report_acts(tmp_path, monkeypatch):
    from app.config import CONFIG
    from app.research import edge_report, pnl_scan
    from app.research.referee_registry import CertificateStore
    from app.research.store import JournalStore

    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)
    public_ids = sorted(m["id"] for m in store.list()[0] if m["id"] != sealed_meta["id"])

    vault.seal_shard(
        vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )

    journal = JournalStore(CONFIG.journal_db_path_resolved(), CONFIG)
    try:
        # --- the operator compute acts, RUN (not assumed) --------------------------------------
        report = edge_report.run_edge_report(journal, store, CONFIG)
        sweep = pnl_scan.run_sweep(
            journal, store, CONFIG,
            certificate_store=CertificateStore(tmp_path / "referee_registry"),
        )

        # the counter-test: both acts really did measure the PUBLIC siblings -- an exclusion-only
        # check would also "pass" if the whole report had silently broken.
        measured = sorted(
            r["dataset_id"] for r in report["train"]["datasets"] + report["holdout"]["datasets"]
        )
        assert measured == public_ids
        assert report["withheld_excluded"] == 1
        (candidate,) = sweep["candidates"]
        swept_ids = sorted(
            d["dataset_id"] for d in candidate["train"]["datasets"] + candidate["holdout"]["datasets"]
        )
        assert swept_ids == public_ids
        assert sweep["withheld_excluded"] == 1
        # ... and not one backtest ever opened the sealed shard
        backtested = {b.payload["dataset_id"] for b in journal.list_backtests(limit=500)}
        assert backtested and backtested <= set(public_ids)
    finally:
        journal.close()

    forbidden_substrings = {
        "dataset id": sealed_meta["id"],
        "raw content checksum": sealed_meta["checksum"],
        "symbol": _SWEEP_SYMBOL,
        "window start": _SWEEP_WINDOW_START,
        "window end": _SWEEP_WINDOW_END,
    }
    forbidden_scalars = {_SWEEP_TRADES, _SWEEP_QUOTES, sealed_meta["event_counts"]["total"]}

    with TestClient(app) as client:
        leaks: list[str] = []
        swept: dict[str, int] = {}
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", sealed_meta["id"])
            if "{" in url:
                continue
            response = client.get(url)
            swept[path] = response.status_code
            for name, token in forbidden_substrings.items():
                if token in response.text:
                    leaks.append(f"{path} serves the sealed shard's {name}")
            try:
                payload_scalars = _scalars(response.json(), [])
            except ValueError:
                payload_scalars = []
            hits = sorted({s for s in payload_scalars if s in forbidden_scalars})
            if hits:
                leaks.append(f"{path} serves the sealed shard's exact event counts {hits}")

        assert leaks == [], "join-resistance breached after the report acts:\n  " + "\n  ".join(leaks)
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        # the two surfaces this finding was actually about, proven NON-EMPTY (so the sweep above
        # had something to leak) and clean.
        served_backtests = client.get("/research/backtests").json()["backtests"]
        assert served_backtests, "GET /research/backtests is empty -- the sweep is vacuous here"
        assert {b["dataset_id"] for b in served_backtests} <= set(public_ids)
        assert swept["/research/pnl/ledger"] == 200


def test_r4_the_micro_compute_acts_disclose_what_they_left_out(tmp_path, monkeypatch):
    """Spec section 7.5 point 6 (r4): excluding a withheld shard is only half the rule -- the count
    (never the ids) must travel into the report body and into any append-only row the run writes.
    Proven on the two `/desk` micro compute acts, whose runs are the ones the audit's B1 fix made
    exclusion-only."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)
    sealed_meta = _record_distinctive_dataset(store)

    vault.seal_shard(
        vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
        dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )

    with TestClient(app) as client:
        client.post("/research/desk/micro/snapshots/compute")
        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
        client.post("/research/desk/micro/scout/compute")
        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"

        # the build's own served progress + its APPEND-ONLY run-log row both state the exclusion
        assert client.get("/research/desk/micro/snapshots/compute").json()["withheld_excluded"] == 1
        runs = client.get("/research/desk/micro/snapshots/runs").json()["runs"]
        assert runs[0]["withheld_excluded"] == 1
        assert runs[0]["datasets_total"] == 2  # the two public siblings, and only those

        # every scout row written into the APPEND-ONLY hash-chained ledger states it too
        families = client.get("/research/desk/micro/scout").json()["families"]
        assert families
        trials = [trial for family in families for trial in family["trials"]]
        assert trials and all(trial["withheld_excluded"] == 1 for trial in trials)
        # a COUNT, never an identity
        assert sealed_meta["id"] not in json.dumps(families, sort_keys=True)


def _et_session_date(window_start_utc: str) -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return (
        datetime.fromisoformat(window_start_utc.replace("Z", "+00:00"))
        .astimezone(ZoneInfo("America/New_York")).date().isoformat()
    )


def test_audit_b1_the_universe_rule_cannot_de_anonymise_the_sealed_tranche_by_subtraction(
    tmp_path, monkeypatch
):
    """iter-9 audit, THIRD pass, finding B1 (CRITICAL, fixed here).

    Every TR-2 sweep above seals a shard against a vault whose universe ledger is EMPTY, so the
    one surface that publishes a tranche's COMPLEMENT was never exercised by any of them -- the
    same "the rig computed nothing, so the trap could not bite" shape the second audit paid for.
    Registered here on purpose.

    The attack needs no secret and no vault internals: TR-4 forces the recorded batch to be exactly
    ``symbol_rule x date_rule``, and ``GET /research/datasets`` serves every recorded shard EXCEPT
    the withheld ones -- so ``expected - served`` IS the sealed set. Reproduced against the
    pre-fix code, which named ``('ZQXBBB', ...)`` exactly. Spec section 7.3: "sealed membership
    cannot be inferred from public information before exposure"."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = DatasetStore(str(tmp_path / "datasets"))
    symbols, dates = ["ZQXAAA", "ZQXBBB"], ["2031-03-17", "2031-03-18"]
    metas = {}
    for symbol in symbols:
        for index, date in enumerate(dates):
            events = [
                QuoteEvent(symbol, 1.0, 99.9, 100.1, 100, 100),
                # a per-(symbol, date) nonce: `_content_checksum` covers the ROWS, so two windows
                # with identical events would collide on `DatasetAlreadyRegistered`.
                TradeEvent(symbol, 2.0, 100.0 + index, 10, Side.BUY),
            ]
            metas[(symbol, date)] = store.record(
                symbol=symbol, source="historical", source_kind="historical", source_id=symbol,
                split="train", window_start_utc=f"{date}T14:31:07Z",
                window_end_utc=f"{date}T19:57:41Z", data_feed="sip", epoch_anchor=0.0,
                events=events,
            )

    vault_dir = str(tmp_path / "micro_vault")
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="starter-tranche-v1", symbol_rule=symbols, date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    secret_member = ("ZQXBBB", "2031-03-17")
    sealed_meta = metas[secret_member]
    shard_ledger = vault.VaultShardLedger(vault_dir)
    vault.seal_shard(
        shard_ledger, dataset_id=sealed_meta["id"], universe_id="starter-tranche-v1",
        content_checksum=sealed_meta["checksum"],
        event_count=sealed_meta["event_counts"]["total"], vault_secret=_FIXTURE_SECRET,
    )

    with TestClient(app) as client:
        body = client.get("/research/desk/micro/vault").json()
        datasets = client.get("/research/datasets").json()

        # the counter-test FIRST: the rig is genuinely loaded, so an "absent" assertion means
        # something -- one universe registered, one shard sealed, three siblings still served.
        assert len(body["universes"]) == 1
        assert datasets["sealed_withheld"] == 1
        assert len(datasets["datasets"]) == 3

        universe = body["universes"][0]
        # the commitment stage: the rule's NONCED COMMITMENT and SHAPE, never its membership, and
        # never the plain rule_hash (r7/TR-27 -- a bare deterministic hash of a low-entropy,
        # dictionary-enumerable rule is not a hiding commitment).
        assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
        assert "rule_hash" not in universe
        assert "commitment_nonce" not in universe
        assert universe["rule_commitment"] != vault.compute_rule_hash(symbols, dates)
        assert (universe["symbol_rule_size"], universe["date_rule_size"]) == (2, 2)
        assert "symbol_rule" not in universe and "date_rule" not in universe
        for token in symbols + dates:
            assert token not in json.dumps(universe), f"the served universe row still names {token}"

        # ... and the subtraction attack itself, EXECUTED against the whole payload rather than
        # asserted absent: nothing a reader can reach names the sealed symbol-day.
        served_pairs = {
            (row["symbol"], _et_session_date(row["window_start_utc"]))
            for row in datasets["datasets"]
        }
        assert secret_member not in served_pairs  # withheld, as r3 requires
        public_text = json.dumps(body) + json.dumps(datasets)
        assert sealed_meta["id"] not in public_text
        assert sealed_meta["checksum"] not in public_text
        # the pre-fix payload made this set computable and equal to {secret_member}; with the rule
        # committed there is no published `expected` to subtract from at all.
        assert not any(
            key in universe for key in ("symbol_rule", "date_rule", "expected_pairs")
        )

    # TC-6/TR-27 (r7): assigning, then EXPOSING, this ONE tracked shard does NOT reveal the
    # universe -- three of its four ORIGINAL pool members (both ZQXAAA pairs, and ZQXBBB's other
    # date) were never even ledger-tracked, let alone exposed. The pre-iteration-12 gate
    # (`_fully_exposed_universe_ids`, "every LEDGER-TRACKED shard exposed") would have wrongly
    # revealed the rule here -- the exact two-GET subtraction door the iteration-11 audit proved
    # open (module docstring). The widened `_whole_pool_released_universe_ids` requires every
    # ORIGINAL pool member, not merely every member this ledger happens to know about.
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.assign_shard(
        shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root,
        symbol=secret_member[0], session_date=secret_member[1],
    )
    still_withheld = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert still_withheld["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED  # assigned != exposed

    vault.expose_shard(shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root)
    one_of_four_exposed = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert one_of_four_exposed["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED  # STILL hidden
    assert "symbol_rule" not in one_of_four_exposed

    # the actual reveal half (TC-7): seal, assign and expose the THREE remaining pool members too
    # -- only once literally every one of the universe's four ORIGINAL pairs is exposed does the
    # rule (plus the nonce) serve, and it recomputes EXACTLY to the commitment registration
    # produced up front.
    for pair in metas:  # metas' own keys ARE the universe's full 2x2 expected set (module setup)
        if pair == secret_member:
            continue
        meta = metas[pair]
        vault.seal_shard(
            shard_ledger, dataset_id=meta["id"], universe_id="starter-tranche-v1",
            content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
            vault_secret=_FIXTURE_SECRET,
        )
        vault.assign_shard(
            shard_ledger, dataset_id=meta["id"], family_root_id=family_root,
            symbol=pair[0], session_date=pair[1],
        )
        vault.expose_shard(shard_ledger, dataset_id=meta["id"], family_root_id=family_root)

    revealed = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert revealed["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED
    assert revealed["symbol_rule"] == symbols and revealed["date_rule"] == dates
    assert revealed["rule_commitment"] == universe["rule_commitment"]  # unchanged since registration
    assert (
        vault.compute_rule_commitment(revealed["commitment_nonce"], symbols, dates)
        == revealed["rule_commitment"]
    )


def test_audit_b1_a_universe_with_no_shards_yet_keeps_its_rule_committed(tmp_path):
    """The fail-closed half of the fix. Spec section 7.2's mandated order registers the universe
    (step 5) BEFORE any vendor fetch (step 7), so there is a real window in which the universe owns
    zero shards -- and a reader who harvests the rule during that window keeps it for the whole
    tranche's life. `_whole_pool_released_universe_ids` (iteration 12's widened successor to the
    pre-iteration-12 `_fully_exposed_universe_ids`) therefore reveals only a universe whose full
    EXPECTED pair set (`expected_recording_pairs`) is a subset of its own EXPOSED pairs; "no shards
    at all" trivially fails that subset test (an empty exposed-pairs set can never contain the
    universe's own non-empty expected set), so "no shards" reveals nothing."""
    vault_dir = str(tmp_path / "vault")
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG", "AAPL"],
        date_rule=["2026-06-08", "2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    state = vault.build_vault_state(vault.VaultShardLedger(vault_dir), universe_ledger)
    assert state["shards"] == []
    (universe,) = state["universes"]
    assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
    assert "symbol_rule" not in universe
    assert "PG" not in json.dumps(universe) and "2026-06-08" not in json.dumps(universe)


def test_b7_seal_shard_refuses_an_empty_vault_secret(tmp_path):
    """iter-9 audit finding B7: ``load_vault_secret`` refuses an empty secret file, but
    ``seal_shard`` took raw bytes from its caller and never re-checked -- and an empty HMAC key
    makes BOTH the surrogate shard id and the salted checksum commitment publicly derivable,
    silently voiding r3's whole join-resistance guarantee at the moment sealing happens."""
    ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    for empty in (b"", b"   ", b"\n"):
        with pytest.raises(vault.VaultSecretUnavailable):
            vault.seal_shard(
                ledger, dataset_id="d-1", universe_id="starter-tranche-v1",
                content_checksum="c" * 64, event_count=100, vault_secret=empty,
            )
    assert ledger.all_rows() == []  # refused BEFORE anything was written

    # the counter-test: a real secret still seals exactly as before
    row = vault.seal_shard(
        ledger, dataset_id="d-1", universe_id="starter-tranche-v1",
        content_checksum="c" * 64, event_count=100, vault_secret=_FIXTURE_SECRET,
    )
    assert row["exposure_state"] == "sealed"
    assert len(ledger.all_rows()) == 1


# === Iteration 11 (docs/phases/goal-rapid-microscope-iter-11.md, DEFINITION OF DONE): TR-2
# rewritten into spec section 9's deterministic inference-trap shape -- TC-8/TC-9. The r5
# governing test, verbatim: "given the registered universe (section 7.2) plus EVERY public
# artifact the system serves ... no still-unexposed vault-eligible shard is identifiable with
# certainty." Builds on the SAME rig every TR-2 test above shares
# (`_combined_fixture_store`/`_scope_everything_to`/`_sweepable_get_paths`/`_scalars`/
# `_poll_compute`), widened to a REGISTERED universe with FOUR pool members in THREE distinct
# provenance shapes -- exactly this iteration's own gap: a legitimately EXPOSED member, a
# ledger-tracked SEALED member (the ONLY case the pre-iteration-11 predicate ever recognized), and
# TWO UNTRACKED members (zero vault ledger row at all -- what a real recorder run produces TODAY,
# since nothing wires ``tick_recorder.py`` to ``vault.py`` yet; a repo-wide grep at authoring finds
# zero production call sites of ``seal_shard``/``assign_shard``/``expose_shard``).
# =====================================================================================================


def _record_pool_dataset(store: DatasetStore, *, symbol: str, session_date: str, nonce: int) -> dict:
    """One dataset for (symbol, session_date), in NO real panel/universe and globally distinctive
    via ``nonce`` -- the ``_record_distinctive_dataset`` recipe above, generalized to many
    (symbol, date) pairs instead of one, at a comparable size (135+ trades/quotes) to the sibling
    already proven to survive Snapshot/Scout/edge-report/PnL compute acts
    (``test_tr2_holds_after_the_operator_runs_every_micro_compute_act``/``test_tr2_holds_after_
    the_corpus_wide_report_acts`` above)."""
    trades_n, quotes_n = 137 + nonce, 241 + nonce
    events: list = [QuoteEvent(symbol, float(i), 99.99, 100.02, 100, 100) for i in range(quotes_n)]
    events += [TradeEvent(symbol, float(i) + 0.5, 100.03 + nonce, 10, Side.BUY) for i in range(trades_n)]
    return store.record(
        symbol=symbol, source="historical", source_kind="historical", source_id=symbol,
        split="train", window_start_utc=f"{session_date}T13:31:07Z",
        window_end_utc=f"{session_date}T19:57:41Z", data_feed="sip", epoch_anchor=0.0, events=events,
    )


def test_tc8_tc9_r5_inference_trap_a_registered_pool_with_mixed_provenance_leaves_ge2_candidates(
    tmp_path, monkeypatch
):
    """TC-8 + TC-9 (phase spec; spec section 9's TR-2 row): the deterministic r5 inference trap,
    run against a fixture pool in mixed ledger-tracked/untracked provenance, with the operator
    compute acts run FIRST so the trap "cannot pass merely because the rig computed nothing."

    TC-8's main assertion: for every still-unexposed member, at least 2 candidate (symbol, date)
    identities remain consistent with everything served, and no complete identity-labelled
    exploratory/sealed partition is derivable.

    TC-9's counter-test: the PRE-fix subtraction attack (list ``GET /research/datasets``'s served
    ids, compute the universe's full expected set, subtract) -- run here directly against the OLD,
    still-exported ``vault.withheld_universe_by_dataset_id`` predicate (byte-unchanged; iteration
    11 never edits it, only adds a second, wider predicate alongside it) -- WOULD have isolated
    the sealed-but-untracked dataset's identity uniquely, proving TC-8's fixed-code assertion
    above is not vacuous."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)  # the 2 real PG fixtures -- proven compute-safe

    symbols, dates = ["ZQXPOOL1", "ZQXPOOL2"], ["2031-06-01", "2031-06-02"]
    expected_pairs = frozenset((s, d) for s in symbols for d in dates)

    # the universe is registered BEFORE any of its 4 pairs is recorded (spec section 7.2's own
    # mandated order, and TC-4's own `created_utc >= registered_at` guard: recording BEFORE
    # registration would make every pair a pre-existing dataset the universe-rule check must
    # never withhold -- the exact TC-4 scenario, deliberately NOT this test's scenario).
    vault_dir = str(tmp_path / "micro_vault")
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="pool-tr2", symbol_rule=symbols, date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    shard_ledger = vault.VaultShardLedger(vault_dir)

    metas: dict[tuple[str, str], dict] = {}
    for s_index, symbol in enumerate(symbols):
        for d_index, session_date in enumerate(dates):
            metas[(symbol, session_date)] = _record_pool_dataset(
                store, symbol=symbol, session_date=session_date, nonce=s_index * 10 + d_index,
            )

    exposed_pair = ("ZQXPOOL1", "2031-06-01")
    sealed_only_pair = ("ZQXPOOL1", "2031-06-02")
    untracked_pairs = [("ZQXPOOL2", "2031-06-01"), ("ZQXPOOL2", "2031-06-02")]
    unresolved_pairs = frozenset(expected_pairs - {exposed_pair})
    assert len(unresolved_pairs) >= 2  # the TC-8 threshold this fixture must clear by construction

    exposed_meta = metas[exposed_pair]
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.seal_shard(
        shard_ledger, dataset_id=exposed_meta["id"], universe_id="pool-tr2",
        content_checksum=exposed_meta["checksum"], event_count=exposed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )
    vault.assign_shard(
        shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root,
        symbol=exposed_pair[0], session_date=exposed_pair[1],
    )
    vault.expose_shard(shard_ledger, dataset_id=exposed_meta["id"], family_root_id=family_root)

    sealed_meta = metas[sealed_only_pair]
    vault.seal_shard(
        shard_ledger, dataset_id=sealed_meta["id"], universe_id="pool-tr2",
        content_checksum=sealed_meta["checksum"], event_count=sealed_meta["event_counts"]["total"],
        vault_secret=_FIXTURE_SECRET,
    )
    # the 2 untracked pairs get NO vault call at all -- today's actual recorder gap.

    from app.config import CONFIG
    from app.mcp import _STATIC_PATHS
    from app.research import edge_report, pnl_scan
    from app.research.referee_registry import CertificateStore
    from app.research.store import JournalStore

    with TestClient(app) as client:
        # --- the operator compute acts, RUN FIRST (spec section 9: "cannot pass merely because
        # the rig computed nothing") -----------------------------------------------------------
        assert client.post("/research/desk/micro/snapshots/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
        assert client.post("/research/desk/micro/scout/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"

        built = {m["dataset_id"] for m in client.get("/research/desk/micro/snapshots").json()["snapshots"]}
        assert exposed_meta["id"] in built
        assert sealed_meta["id"] not in built
        assert all(metas[p]["id"] not in built for p in untracked_pairs)

        journal = JournalStore(CONFIG.journal_db_path_resolved(), CONFIG)
        try:
            report = edge_report.run_edge_report(journal, store, CONFIG)
            sweep = pnl_scan.run_sweep(
                journal, store, CONFIG, certificate_store=CertificateStore(tmp_path / "referee_registry"),
            )
        finally:
            journal.close()

        # the counter-test half: the compute acts really did measure something (never vacuous) --
        # the 2 PG siblings and the legitimately exposed pool dataset, never the 3 unresolved ones.
        measured = {r["dataset_id"] for r in report["train"]["datasets"] + report["holdout"]["datasets"]}
        assert exposed_meta["id"] in measured
        assert sealed_meta["id"] not in measured
        assert all(metas[p]["id"] not in measured for p in untracked_pairs)
        assert report["withheld_excluded"] == 3
        assert sweep["withheld_excluded"] == 3

        # --- NOW sweep every registered route + the recorder-progress path + the `datasets` MCP
        # tool (structurally proven to coincide with the REST sweep by
        # test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route above) -------------
        swept: dict[str, object] = {}
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", exposed_meta["id"])
            if "{" in url:
                continue
            response = client.get(url)
            try:
                swept[path] = response.json()
            except ValueError:
                swept[path] = response.text
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        assert "/research/desk/micro/recorder/compute" in swept  # TC-6's own path, in this sweep too
        assert _STATIC_PATHS["datasets"] in swept  # the `datasets` MCP tool's exact proxied path

        served_text = json.dumps(swept, sort_keys=True, default=str)

        # --- TC-8's main assertion: no still-unexposed member's identity is derivable ----------
        # the positive reconstruction: subtract what IS served from what the KNOWN universe rule
        # expects -- this is exactly the attack r5 exists to defeat, EXECUTED, not merely asserted
        # absent.
        datasets_body = swept["/research/datasets"]
        served_identified_pairs = {
            (row["symbol"], _et_session_date(row["window_start_utc"])) for row in datasets_body["datasets"]
        }
        assert served_identified_pairs & expected_pairs == {exposed_pair}
        remaining_candidates = expected_pairs - served_identified_pairs
        assert remaining_candidates == unresolved_pairs
        assert len(remaining_candidates) == 3  # >= 2 -- no unique identity isolated for ANY of them

        # readiness's OWN listing must agree byte-for-byte with the same reconstruction -- two
        # surfaces answering "which pairs are identified" can never diverge.
        readiness = swept["/research/desk/micro/readiness"]
        readiness_identified_pairs = {
            (row["symbol"], row["session_date"])
            for row in readiness["shards"]
            if (row["symbol"], row["session_date"]) in expected_pairs
        }
        assert readiness_identified_pairs == {exposed_pair}
        assert readiness["sealed_tranche"]["shard_count"] == 3
        assert readiness["sealed_tranche"]["by_universe"] == {
            "pool-tr2": {"shard_count": 3, "symbol_days": 3}
        }

        # no unresolved member's dataset id or raw checksum appears ANYWHERE in the swept union --
        # the join-resistance claim, applied to every unresolved member. Both are long, globally
        # unique hex strings (never a plain small integer -- see `_scope_everything_to`'s own
        # comment on why THIS file avoids asserting small scalars are absent: a coincidental
        # collision with an unrelated route's own real count is a false positive, not a leak).
        for pair in unresolved_pairs:
            meta = metas[pair]
            assert meta["id"] not in served_text, f"{pair}'s dataset id leaked"
            assert meta["checksum"] not in served_text, f"{pair}'s raw checksum leaked"

        # --- TC-9's counter-test: the PRE-fix predicate WOULD have isolated a unique identity --
        pre_fix_withheld_ids = set(vault.withheld_universe_by_dataset_id(shard_ledger))
        assert pre_fix_withheld_ids == {sealed_meta["id"]}  # the ONLY case the old predicate saw
        pre_fix_served_pairs = {
            pair for pair, meta in metas.items() if meta["id"] not in pre_fix_withheld_ids
        }
        pre_fix_remaining = expected_pairs - pre_fix_served_pairs
        assert pre_fix_remaining == {sealed_only_pair}, (
            "the pre-fix subtraction attack should isolate exactly the ledger-tracked-but-"
            "unexposed dataset's (symbol, date) uniquely -- proving TC-8's fixed-code assertion "
            "above is not vacuous"
        )


# =====================================================================================================
# Iteration 12 (docs/phases/goal-rapid-microscope-iter-12.md): TR-25 vault-ledger integrity (spec
# section 7.8), TR-27 nonced rule commitment (spec section 7.2/7.5, r7), and the symbol-case
# normalization companion item. TC-1 through TC-14, per the phase spec's own test-first contract.
# =====================================================================================================


def _seal_two_shards(shard_ledger: vault.VaultShardLedger) -> list[dict]:
    """Two sealed shards (``d-1`` then ``d-2``), so a truncated-tail scenario has something real
    to lose -- the shared fixture every TR-25 test below builds on."""
    rows = []
    for i, (dataset_id, checksum) in enumerate((("d-1", "a" * 64), ("d-2", "b" * 64))):
        rows.append(
            vault.seal_shard(
                shard_ledger, dataset_id=dataset_id, universe_id="u1",
                content_checksum=checksum, event_count=100 + i, vault_secret=_FIXTURE_SECRET,
            )
        )
    return rows


def _seal_three_shards(shard_ledger: vault.VaultShardLedger) -> list[dict]:
    """Three sealed shards (``d-1``, ``d-2``, ``d-3``) -- iteration 13's own fixture, the exact
    shape of the iteration-12 evaluator's own reproduction (goal-rapid-microscope-iter-13's
    BACKGROUND): a genuine two-row verified prefix (``d-1``, ``d-2``) in front of a THIRD shard
    whose own row can be destroyed on its own, entirely unnamed by anything before it."""
    rows = []
    for i, (dataset_id, checksum) in enumerate(
        (("d-1", "a" * 64), ("d-2", "b" * 64), ("d-3", "c" * 64))
    ):
        rows.append(
            vault.seal_shard(
                shard_ledger, dataset_id=dataset_id, universe_id="u1",
                content_checksum=checksum, event_count=100 + i, vault_secret=_FIXTURE_SECRET,
            )
        )
    return rows


def _truncate_ledger_tail(ledger) -> None:
    """Drops the LAST line of ``ledger``'s own ``.jsonl`` file, leaving its tail anchor
    (``chain_head.json``, UNTOUCHED) still claiming the ORIGINAL row count -- TC-1/TC-3's own
    scenario: a genuine, self-consistent prefix of true history, short by one row the anchor
    proves should exist. Works for either ``VaultShardLedger`` or ``VaultUniverseLedger``."""
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    ledger.path.write_text("\n".join(lines[:-1]) + ("\n" if lines[:-1] else ""), encoding="utf-8")


def _mutate_interior_row(ledger_path: Path, row_index: int, key: str, value: object) -> None:
    """Rewrites ONE key of an already-appended, interior row -- TC-2's own scenario: the row's own
    content hash no longer matches what it committed to."""
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[row_index])
    row[key] = value
    lines[row_index] = json.dumps(row, sort_keys=True)
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- TC-1/TC-2/TC-3: fail closed on a corrupted ledger, never treat it as empty or complete -------


def test_tc1_a_truncated_shard_ledger_tail_fails_closed_on_every_predicate(tmp_path):
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    _seal_two_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)

    assert shard_ledger.verify_chain()["reason"] == "tail_truncated"
    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
        vault.currently_sealed_dataset_ids(shard_ledger)
    assert exc_info.value.ledger_kind == "shard"
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.withheld_dataset_ids(shard_ledger)  # never silently omits the lost row's shard
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, universe_ledger)


def test_tc1_a_truncated_universe_ledger_tail_fails_closed(tmp_path):
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    vault.register_universe(
        universe_ledger, universe_id="u2", symbol_rule=["AAPL"], date_rule=["2026-06-10"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    _truncate_ledger_tail(universe_ledger)
    assert universe_ledger.verify_chain()["reason"] == "tail_truncated"

    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
        vault.find_universe(universe_ledger, "u2")
    assert exc_info.value.ledger_kind == "universe"
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, universe_ledger)
    # register_universe's own freeze/idempotency check reads the universe ledger too -- refused
    # rather than silently re-registering (or silently refusing) against unverifiable history.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.register_universe(
            universe_ledger, universe_id="u3", symbol_rule=["MSFT"], date_rule=["2026-06-11"],
            vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
        )


def test_tc2_an_interior_row_mutation_fails_closed_and_halts_sealing_and_assignment(tmp_path):
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    _seal_two_shards(shard_ledger)
    _mutate_interior_row(shard_ledger.path, 0, "universe_id", "a-different-universe")

    assert shard_ledger.verify_chain()["reason"] == "content_hash_mismatch"
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, universe_ledger)
    # spec section 7.8's own literal words: "no sealing, no assignment, no exposure check".
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.seal_shard(
            shard_ledger, dataset_id="d-3", universe_id="u1", content_checksum="c" * 64,
            event_count=10, vault_secret=_FIXTURE_SECRET,
        )
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.assign_shard(
            shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
            session_date="2026-06-09",
        )
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.expose_shard(shard_ledger, dataset_id="d-1", family_root_id="root")


def test_tc3_a_last_known_good_prefix_still_fails_closed_when_the_anchor_proves_more_existed(tmp_path):
    """The raw prefix, taken in isolation, IS internally hash-chain-consistent -- proving this
    isn't a trivially-broken file a naive "does row 0 verify" check would already catch. The GATED
    reader refuses anyway, because the durable tail anchor proves a row is missing."""
    shard_ledger = vault.VaultShardLedger(str(tmp_path / "vault"))
    _seal_two_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)

    raw_rows = shard_ledger.all_rows()  # the UNGATED reader -- still works, on purpose
    assert len(raw_rows) == 1 and raw_rows[0]["dataset_id"] == "d-1"

    with pytest.raises(vault.VaultLedgerCorruptionError) as exc_info:
        shard_ledger.verified_rows()
    assert exc_info.value.verify_result["reason"] == "tail_truncated"
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.currently_sealed_dataset_ids(shard_ledger)


# --- TC-4/TC-5 (iteration 12) -- lawful recovery, HALT-ONLY since spec revision r8 (2026-08-19
# owner ruling; vault.py's own module docstring, spec section 7.8, TR-29). Exactly two outcomes: a
# hash-attested proof of completeness resumes the EXACT prior state, and every other input -- empty,
# short, wrong, reordered, padded to the right length, or unanchored -- refuses to resume at all,
# leaving the corrupt file untouched and the whole vault blocked. Iteration 12's graded middle
# branch (resume while marking the named dataset ids `exposure_unknown`) was DELETED by r8 after the
# iteration-13 review proved it launders identity: row-count equality is not evidence of identity.
# The tests below assert the refusals; TR-29's own block further down attacks them. -------------


def test_tc4_a_hash_attested_reconstruction_resumes_service_and_reports_exact_prior_state(tmp_path):
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original_rows = _seal_two_shards(shard_ledger)
    assert shard_ledger.verify_chain()["ok"] is True

    _truncate_ledger_tail(shard_ledger)  # loses d-2's own seal row
    verify_result = shard_ledger.verify_chain()
    assert verify_result["ok"] is False

    lost_row_fields = vault._row_content(original_rows[1])  # the caller's own trusted source
    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[lost_row_fields],
        sources=[{"source": "test-fixture-recall", "sha256": "irrelevant-for-this-test"}],
        operator_identity="test-operator", reason="unit test TC-4",
        recovery_ledger=recovery_ledger, incident_id="incident-tc4",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": True, "resumed": True}

    # service resumes, reporting the EXACT prior state.
    assert shard_ledger.verify_chain()["ok"] is True
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2"})
    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
    assert {s["shard_id"] for s in state["shards"]} == {r["shard_id"] for r in original_rows}

    # the recovery event is on permanent record, in the SEPARATE ledger -- never the shard ledger.
    recovery_rows = recovery_ledger.all_rows()
    assert len(recovery_rows) == 1
    assert recovery_rows[0]["outcome"] == "complete"
    assert recovery_rows[0]["operator_identity"] == "test-operator"
    assert recovery_rows[0]["last_verified_row_index"] == 0
    assert recovery_rows[0]["last_verified_row_hash"] == original_rows[0]["row_hash"]

    # the corrupt original was preserved byte-for-byte, never overwritten in place.
    quarantined = list((tmp_path / "quarantine").glob("incident-tc4.*"))
    assert quarantined, "no forensic copy of the corrupt ledger was preserved"


# --- iteration 13's own TC-1/TC-2/TC-3/TC-4 (docs/phases/goal-rapid-microscope-iter-13.md): the
# hole the iteration-12 evaluator found -- a shard entirely unnamed by any recovery attempt must
# never silently escape marking; it must halt the whole ledger instead. --------------------------


def test_tc1_the_iteration_12_reproduction_an_entirely_unnamed_lost_row_refuses_to_resume(tmp_path):
    """The exact end-to-end reproduction the iteration-12 evaluator ran (goal.md's BACKGROUND):
    seal d-1/d-2/d-3, destroy d-3's own row (only), attempt recovery with NOTHING to reconstruct
    it. Before this iteration's fix, this silently resumed -- marking only d-1/d-2 (the surviving
    verified prefix) exposure_unknown -- letting d-3 escape into looking like an ordinary,
    never-sealed dataset even though verify_chain() reported clean again afterward. The corrected
    behavior (r8): nothing here is PROVEN, so recovery refuses to resume at all."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    assert shard_ledger.read_tail_anchor()["row_count"] == 3

    _truncate_ledger_tail(shard_ledger)  # loses d-3's own seal row; d-1/d-2 remain a genuine prefix
    verify_result = shard_ledger.verify_chain()
    assert verify_result["ok"] is False and verify_result["reason"] == "tail_truncated"

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-1",
        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc1",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # never rewritten -- the corrupted file on disk is exactly as it was before the attempt.
    assert shard_ledger.verify_chain() == verify_result
    raw_dataset_ids = [row["dataset_id"] for row in shard_ledger.all_rows()]
    assert raw_dataset_ids == ["d-1", "d-2"]

    # d-3 appears in NO row anywhere -- not sealed, not "unknown", not anything.
    recovery_rows = recovery_ledger.all_rows()
    assert len(recovery_rows) == 1
    assert recovery_rows[0]["outcome"] == "halted"
    assert recovery_rows[0]["anchor_row_count"] == 3
    assert recovery_rows[0]["attempted_row_count"] == 2
    assert "d-3" not in json.dumps(recovery_rows)


def test_tc2_a_missing_tail_anchor_refuses_to_resume_even_with_a_perfect_reconstruction(tmp_path):
    """iteration-13 TC-2: the ledger's own durable tail-anchor SIDECAR file (not its content rows)
    is the one thing missing here -- all three rows are still fully present and internally
    self-consistent on disk. Even so, `recover_shard_ledger` must never call this "proven
    complete": with no anchor, there is no independent proof of the true history to test the
    reconstruction against AT ALL, so a HALT is the only lawful outcome -- regardless of how
    faithful the caller's own reconstructed_suffix happens to be."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original_rows = _seal_three_shards(shard_ledger)
    assert shard_ledger.verify_chain()["ok"] is True

    shard_ledger.head_anchor_path.unlink()
    verify_result = shard_ledger.verify_chain()
    assert verify_result == {"ok": False, "failed_at_row": None, "reason": "head_anchor_missing"}

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    # a BYTE-PERFECT full reconstruction, offered as the caller's own reconstructed_suffix -- and
    # it still cannot save the attempt, because nothing independent of the missing anchor can
    # prove three rows (not two, not four) is the true count.
    perfect_suffix = [vault._row_content(row) for row in original_rows]
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=perfect_suffix,
        sources=[{"source": "operator-recall", "sha256": "irrelevant-for-this-test"}],
        operator_identity="test-operator", reason="unit test iter-13 TC-2",
        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc2",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # never rewritten -- still failing the identical way immediately after the attempt.
    assert shard_ledger.verify_chain() == verify_result
    recovery_rows = recovery_ledger.all_rows()
    assert len(recovery_rows) == 1
    assert recovery_rows[0]["outcome"] == "halted"
    assert recovery_rows[0]["anchor_row_count"] is None
    assert recovery_rows[0]["anchor_head_hash"] is None


def test_tc3_predicates_keep_raising_after_a_halt_rather_than_omitting_the_unnamed_shard(tmp_path):
    """TC-3: after TC-1's halt, currently_sealed_dataset_ids/withheld_dataset_ids/
    unresolved_pool_universe_by_dataset_id/build_vault_state must each raise
    VaultLedgerCorruptionError -- never silently return a result that simply omits d-3, which is
    exactly the shape of the iteration-12 hole (a corrupted-but-"clean-looking" ledger)."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-3",
        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc3",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome["resumed"] is False

    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.currently_sealed_dataset_ids(shard_ledger)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.withheld_dataset_ids(shard_ledger)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, [])
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, universe_ledger)


def test_tc4_a_later_fuller_reconstruction_still_succeeds_against_the_same_untouched_file(tmp_path):
    """TC-4: a halt never consumes or destroys the corrupted original -- a SECOND
    recover_shard_ledger call, this time with a byte-correct reconstruction of the truly lost row,
    proves complete exactly as the unchanged proven-complete path (TC-6) always has, and the
    recovery_ledger shows BOTH the earlier halted attempt and the later completed one, on
    permanent record."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original_rows = _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    halted = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="unit test iter-13 TC-4 (halt)",
        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc4-halt",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert halted == {"ok": False, "resumed": False}

    # the SAME still-corrupted ledger, re-verified fresh -- untouched by the halted attempt --
    # this time with d-3's true lost row supplied faithfully.
    verify_result_again = shard_ledger.verify_chain()
    assert verify_result_again == verify_result
    lost_row_fields = vault._row_content(original_rows[2])
    completed = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result_again, reconstructed_suffix=[lost_row_fields],
        sources=[{"source": "test-fixture-recall", "sha256": "irrelevant-for-this-test"}],
        operator_identity="test-operator", reason="unit test iter-13 TC-4 (complete)",
        recovery_ledger=recovery_ledger, incident_id="incident-iter13-tc4-complete",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert completed == {"ok": True, "resumed": True}

    assert shard_ledger.verify_chain()["ok"] is True
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3"})
    state = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
    assert {s["shard_id"] for s in state["shards"]} == {r["shard_id"] for r in original_rows}

    recovery_rows = recovery_ledger.all_rows()
    assert len(recovery_rows) == 2
    assert recovery_rows[0]["outcome"] == "halted"
    assert recovery_rows[1]["outcome"] == "complete"


# --- iteration 12's own TC-5, revised twice (iteration 13 + spec revision r8): the smaller-scale,
# two-shard reproductions. An empty suffix halts (below); a wrong suffix that pads the row count to
# the anchor's own count ALSO halts (further below -- iteration 13 first shipped that case as a
# graded resume, which is exactly what r8 deleted). -----------------------------------------------


def test_tc5_an_entirely_unnamed_shortfall_refuses_to_resume_rather_than_marking_a_subset(tmp_path):
    """The smaller-scale (two-shard) companion to iteration 13's own TC-1: before this iteration's
    fix, an entirely-unnamed lost row (nothing in the verified prefix, nothing in an empty
    reconstructed_suffix) still let the recovery "succeed" by marking ONLY the surviving prefix
    (d-1) exposure_unknown -- silently dropping d-2 out of every predicate with no trace, while
    `rewrite_from_recovery` re-healed the tail anchor so `verify_chain()` reported clean again.
    The corrected behavior: nothing about the lost row is PROVEN, so recovery refuses to resume at
    all and d-2 can never silently read as "never sealed" (spec section 7.8's own invariant)."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_two_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    # no trusted source at all -- the honest "we cannot prove what was lost" case.
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="unit test TC-5",
        recovery_ledger=recovery_ledger, incident_id="incident-tc5",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # the ledger is refused, not "recovered incompletely" -- still failing, byte-untouched.
    assert shard_ledger.verify_chain() == verify_result
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1"]  # untouched, 1 raw row

    # every dependent predicate keeps raising -- d-1 is NOT quietly served as "currently sealed"
    # either, since that would itself misstate a shard whose true post-corruption state is unknown.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.currently_sealed_dataset_ids(shard_ledger)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))

    # permanence of the REFUSAL: no lifecycle transition can sneak past it either -- the gated
    # reader every one of them shares raises before any lifecycle-state check even runs.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.assign_shard(
            shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
            session_date="2026-06-09",
        )
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.seal_shard(
            shard_ledger, dataset_id="d-1", universe_id="u1", content_checksum="c" * 64,
            event_count=1, vault_secret=_FIXTURE_SECRET,
        )


def test_tc5_a_wrong_nonempty_reconstruction_is_also_refused_never_treated_as_proven(tmp_path):
    """TC-5's other failure shape: a SUPPLIED but WRONG suffix (not merely an empty one), whose row
    count exactly matches the anchor's own row_count=2.

    **Revised by spec revision r8** (2026-08-19 owner ruling). Iteration 13 first shipped this case
    as a graded RESUME: because both d-1 and d-2 were named, it rewrote the ledger with the named
    ids marked `exposure_unknown` and returned `resumed: True`. The owner deleted that branch after
    the iteration-13 review proved a same-length suffix can name anything at all (TR-29 below), so
    the assertions here now demand a REFUSAL -- a strictly stronger guarantee than the graded
    outcome this test used to assert, not a loosened one: the ledger is not rewritten, the vault
    stays blocked, and no shard is left in a state that says "we are not sure about this one".
    Also proves `recover_shard_ledger` verifies the reconstruction byte-for-byte rather than
    trusting that the caller supplied SOMETHING of the right length."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_two_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)  # loses d-2's own seal row
    verify_result = shard_ledger.verify_chain()
    assert shard_ledger.read_tail_anchor()["row_count"] == 2

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    # a PLAUSIBLE-LOOKING but WRONG guess -- right shape, right dataset_id, right COUNT, wrong
    # content (a different checksum than d-2 actually had): never a byte-for-byte match of what
    # was truly lost.
    wrong_guess = {
        "dataset_id": "d-2", "content_checksum": "f" * 64, "shard_id": "vshard-wrong-guess",
        "universe_id": "u1", "checksum_commitment": "wrong-commitment", "size_bucket": "~10^2",
        "sealed_at": "2026-06-09T00:00:00.000000Z", "exposure_state": vault.STATE_SEALED,
        "family_root_id": None, "symbol": None, "session_date": None,
        "assigned_at": None, "exposed_at": None,
    }
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[wrong_guess],
        sources=[{"source": "a-wrong-guess", "sha256": "irrelevant"}],
        operator_identity="test-operator", reason="unit test TC-5 (wrong guess)",
        recovery_ledger=recovery_ledger, incident_id="incident-tc5-wrong",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    # the count matched the anchor exactly -- and it bought the attempt nothing (r8).
    assert outcome == {"ok": False, "resumed": False}

    # the corrupted file is byte-untouched: still one raw row, still failing identically.
    assert shard_ledger.verify_chain() == verify_result
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1"]
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))

    # the halted attempt is on permanent record, saying WHY the proof failed: the count matched,
    # the hash did not.
    recovery_rows = recovery_ledger.all_rows()
    assert len(recovery_rows) == 1
    assert recovery_rows[0]["outcome"] == "halted"
    assert recovery_rows[0]["anchor_row_count"] == recovery_rows[0]["attempted_row_count"] == 2
    assert recovery_rows[0]["attempted_final_row_hash"] != recovery_rows[0]["anchor_head_hash"]


def test_tc5_a_registered_universe_rule_does_not_bypass_the_post_halt_corruption_refusal(tmp_path):
    """The `unresolved_pool_universe_by_dataset_id` predicate reads BOTH ledgers (module
    docstring) -- this proves its fail-closed check truly runs FIRST, before any universe-rule
    reasoning, even when a real registered universe's rule would otherwise match the very shard a
    halted recovery could not name. Before this iteration's fix, a shard the shard ledger's own
    recovery could not name still fell back on this predicate's universe-rule test as a safety
    net (`recover_shard_ledger` used to resume, marking only d-1); after the fix, no fallback is
    ever reached at all, because the corrupted shard ledger refuses to resume in the first place
    -- a strictly stronger guarantee that makes the old safety net unnecessary."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG", "AAPL"],
        date_rule=["2026-06-08", "2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    _seal_two_shards(shard_ledger)  # d-1, then d-2 -- d-2's own row will be the one lost
    _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="unit test TC-5 (b)",
        recovery_ledger=recovery_ledger, incident_id="incident-tc5b",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # d-2 (recorded AFTER u1's registration, matching its rule) would have matched test (b)'s
    # universe-rule membership check -- but the function never reaches it: the shard ledger's own
    # corruption check fires first and refuses the whole call.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.unresolved_pool_universe_by_dataset_id(
            shard_ledger, universe_ledger,
            [("d-2", "AAPL", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
        )


# =====================================================================================================
# TR-29 (spec revision r8, 2026-08-19 owner ruling -- docs/rapid-validation-spec.md section 9 and
# the rewritten section 7.8): RECOVERY IS HALT-ONLY. The iteration-13 review proved by execution
# that the graded branch iteration 13 itself shipped launders identity, because the tail anchor
# commits to a row COUNT plus the final row's hash and to NO per-row identity. Every trap below
# hands `recover_shard_ledger` a reconstruction that SATISFIES the deleted branch's own row-count
# test exactly, and demands a refusal -- so a future edit that reintroduces any count-based
# resumption fails here, loudly. Each case asserts the count equality explicitly, so none of these
# refusals can be passing for the trivial reason of a short suffix.
# =====================================================================================================


def _fabricated_seal_row_fields(dataset_id: str) -> dict:
    """A structurally valid sealed-shard row for a shard that was never sealed -- the padding
    material every TR-29 case uses to reach the anchor's own row count. Built by hand rather than
    through `seal_shard`, precisely because an attacker (or a well-meaning operator working from a
    faulty recollection) writing a reconstructed_suffix is under no obligation to use this module's
    own write path."""
    return {
        "dataset_id": dataset_id, "content_checksum": "9" * 64,
        "shard_id": f"vshard-fabricated-{dataset_id}", "universe_id": "u1",
        "checksum_commitment": "fabricated-commitment", "size_bucket": "~10^2",
        "sealed_at": "2026-06-09T00:00:00.000000Z", "exposure_state": vault.STATE_SEALED,
        "family_root_id": None, "symbol": None, "session_date": None,
        "assigned_at": None, "exposed_at": None,
    }


def test_tr29_a_same_length_suffix_naming_an_unrelated_dataset_is_refused_and_never_reseals(tmp_path):
    """**The demonstrated attack, verbatim from the owner's ruling.** Seal d-1/d-2/d-3, destroy the
    row containing d-3, then present a SAME-LENGTH reconstructed suffix containing an unrelated
    `d-fake`. Under the deleted graded branch this "recovered": it resumed, marked d-1/d-2/d-fake
    exposure_unknown, re-healed the tail anchor so verify_chain() reported clean, and left d-3 in no
    ledger at all -- after which seal_shard could re-seal d-3 FRESH under a different universe, as
    if its sealed history had never existed (a single-shot-exposure anti-goal breach reached
    through a corruption). r8: refuse, and stay refused."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    assert shard_ledger.read_tail_anchor()["row_count"] == 3

    _truncate_ledger_tail(shard_ledger)  # destroys the row containing d-3
    verify_result = shard_ledger.verify_chain()
    assert verify_result["ok"] is False

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result,
        reconstructed_suffix=[_fabricated_seal_row_fields("d-fake")],
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 demonstrated attack",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-attack",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # NON-VACUITY: this input satisfies the DELETED branch's own test exactly -- three rows named
    # against an anchor attesting three -- so the refusal is the identity proof firing, never an
    # incidental shortfall.
    halted = recovery_ledger.all_rows()[0]
    assert halted["outcome"] == "halted"
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    assert halted["attempted_final_row_hash"] != halted["anchor_head_hash"]

    # the fabricated identity never entered the shard ledger, and the corrupt file is untouched.
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1", "d-2"]
    assert "d-fake" not in shard_ledger.path.read_text(encoding="utf-8")
    assert shard_ledger.verify_chain() == verify_result

    # every predicate stays fail-closed -- nothing reads "clean" the way it did pre-r8.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.currently_sealed_dataset_ids(shard_ledger)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.withheld_dataset_ids(shard_ledger)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))

    # THE HEADLINE the owner named: d-3 never becomes sealable again under another universe.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.seal_shard(
            shard_ledger, dataset_id="d-3", universe_id="u2", content_checksum="c" * 64,
            event_count=102, vault_secret=_FIXTURE_SECRET,
        )


def test_tr29_a_same_count_suffix_with_reordered_identities_is_refused(tmp_path):
    """Same row count, same dataset ids, WRONG ORDER. Every identity the anchor ever covered is
    named -- and history is still not proven, because the order of exposure events is part of the
    history. The second half of the test supplies the identical rows in their true order against
    the identical untouched file and proves complete, so the refusal above is demonstrably about
    the ordering and nothing else."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original_rows = _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)  # loses d-3's row
    _truncate_ledger_tail(shard_ledger)  # loses d-2's row too -- the verified prefix is [d-1]
    verify_result = shard_ledger.verify_chain()
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1"]

    true_suffix = [vault._row_content(original_rows[1]), vault._row_content(original_rows[2])]
    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    reordered = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=list(reversed(true_suffix)),
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 reordered identities",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-reordered",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert reordered == {"ok": False, "resumed": False}
    halted = recovery_ledger.all_rows()[0]
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    assert shard_ledger.verify_chain() == verify_result  # untouched

    # NON-VACUITY: the SAME two rows, in their true order, against the SAME file -> proven.
    completed = vault.recover_shard_ledger(
        shard_ledger, verify_result=shard_ledger.verify_chain(), reconstructed_suffix=true_suffix,
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 reordered identities (true order)",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-reordered-true",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert completed == {"ok": True, "resumed": True}
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3"})


def test_tr29_a_same_count_suffix_with_one_substituted_identity_is_refused(tmp_path):
    """The minimal substitution: the destroyed row reconstructed byte-for-byte EXCEPT its
    `dataset_id`, which names a lookalike shard. Row count matches; one identity is a lie. Refused
    -- and the true row against the same untouched file proves complete, so the single substituted
    field is provably the whole difference."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original_rows = _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)  # loses d-3's row
    verify_result = shard_ledger.verify_chain()

    true_lost_row = vault._row_content(original_rows[2])
    substituted = {**true_lost_row, "dataset_id": "d-3-lookalike"}
    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    refused = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=[substituted],
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 substituted identity",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-substituted",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert refused == {"ok": False, "resumed": False}
    halted = recovery_ledger.all_rows()[0]
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    assert "d-3-lookalike" not in shard_ledger.path.read_text(encoding="utf-8")

    # NON-VACUITY: the same row with its TRUE dataset_id proves complete.
    completed = vault.recover_shard_ledger(
        shard_ledger, verify_result=shard_ledger.verify_chain(),
        reconstructed_suffix=[true_lost_row],
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 substituted identity (true row)",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-substituted-true",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert completed == {"ok": True, "resumed": True}
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3"})


def test_tr29_a_missing_earlier_exposure_padded_to_the_same_final_count_is_refused(tmp_path):
    """The most dangerous shape the owner named: the reconstruction reaches the anchor's final row
    COUNT, but an EXPOSURE that really happened is missing from it -- its slot filled by a
    fabricated seal of an unrelated shard. Accepting this would erase the record of d-1 having
    already been drawn once, which is exactly the "never a second draw" anti-goal. Refused; and
    afterwards no lifecycle call can hand d-1 a second exposure either."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    family_root = "root"
    _seal_two_shards(shard_ledger)  # rows 0,1: seal d-1, seal d-2
    assigned = vault.assign_shard(  # row 2
        shard_ledger, dataset_id="d-1", family_root_id=family_root, symbol="PG",
        session_date="2026-06-09",
    )
    vault.expose_shard(shard_ledger, dataset_id="d-1", family_root_id=family_root)  # row 3
    sealed_d3 = vault.seal_shard(  # row 4
        shard_ledger, dataset_id="d-3", universe_id="u1", content_checksum="c" * 64,
        event_count=102, vault_secret=_FIXTURE_SECRET,
    )
    assert shard_ledger.read_tail_anchor()["row_count"] == 5

    for _ in range(3):  # destroy rows 2,3,4 -- including d-1's own EXPOSURE row
        _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()

    # a reconstruction that keeps the assignment and the later seal, drops the exposure, and pads
    # the count back to five with a fabricated shard.
    reconstruction = [
        vault._row_content(assigned),
        vault._row_content(sealed_d3),
        _fabricated_seal_row_fields("d-4"),
    ]
    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=reconstruction,
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 missing earlier exposure",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-missing-exposure",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}
    halted = recovery_ledger.all_rows()[0]
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 5

    # d-1's exposure is nowhere on disk, and the vault is blocked rather than pretending otherwise.
    surviving = shard_ledger.all_rows()  # the UNGATED reader -- the raw file, exactly as it stands
    assert [row["exposure_state"] for row in surviving] == [vault.STATE_SEALED] * 2
    assert all(row["exposed_at"] is None for row in surviving)
    assert shard_ledger.verify_chain() == verify_result
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
    # no second draw for d-1 -- the gated reader refuses before any lifecycle check runs.
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.expose_shard(shard_ledger, dataset_id="d-1", family_root_id=family_root)
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.assign_shard(
            shard_ledger, dataset_id="d-1", family_root_id="root-2", symbol="PG",
            session_date="2026-06-09",
        )


def test_tr29_a_cleanly_internally_rechained_forged_suffix_is_not_proof_of_completeness(tmp_path):
    """Internal consistency is not historical completeness. `_rehash_suffix` re-chains ANY supplied
    fields into a perfectly valid chain -- that is its job -- so a forged suffix always produces a
    ledger that verifies against ITS OWN regenerated anchor. This test writes exactly that forged
    ledger into a scratch directory and shows it verifying clean there, which is precisely what the
    deleted graded branch would have published over the real ledger. Against the ORIGINAL anchor,
    which the forgery cannot reproduce, recovery refuses."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)  # loses d-3's row
    verify_result = shard_ledger.verify_chain()

    forged_fields = [_fabricated_seal_row_fields("d-3")]  # right identity, invented content
    good_prefix = vault._verified_prefix_rows(shard_ledger, verify_result)
    forged_chain = good_prefix + vault._rehash_suffix(good_prefix, forged_fields)
    for index, row in enumerate(forged_chain):  # the forgery IS internally clean
        assert row["row_index"] == index
        assert row["prev_hash"] == (forged_chain[index - 1]["row_hash"] if index else None)
    scratch = vault.VaultShardLedger(str(tmp_path / "forged"))
    scratch.rewrite_from_recovery(forged_chain)
    assert scratch.verify_chain()["ok"] is True  # clean -- and worthless as proof

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result, reconstructed_suffix=forged_fields,
        sources=[{"source": "operator-reconstruction", "sha256": "0" * 64}],
        operator_identity="test-operator", reason="TR-29 forged but internally clean suffix",
        recovery_ledger=recovery_ledger, incident_id="incident-tr29-forged",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}
    halted = recovery_ledger.all_rows()[0]
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    # the real ledger never received the forgery, and still fails exactly as before.
    assert shard_ledger.verify_chain() == verify_result
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1", "d-2"]


def test_tr29_operator_attestation_alone_never_certifies_missing_identity_evidence(tmp_path):
    """`sources`, `operator_identity` and `reason` are audit metadata -- recorded on every attempt,
    read by no decision. Three escalating attestations against the identical corrupted ledger
    (silence, a named operator swearing completeness, a source row that claims a verifying hash)
    produce the identical refusal, and all three are on permanent record having changed nothing."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    _truncate_ledger_tail(shard_ledger)
    verify_result = shard_ledger.verify_chain()
    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)

    attestations = [
        ([], "unknown-operator", "no sources at all"),
        (
            [{"source": "operator-attestation", "attests": "the suffix above is complete"}],
            "chief-research-operator",
            "operator certifies the reconstruction is complete and correct",
        ),
        (
            [{"source": "backup", "sha256": "a" * 64, "attests": "hash verified by operator"}],
            "chief-research-operator",
            "operator certifies a hash-verified backup",
        ),
    ]
    for index, (sources, identity, reason) in enumerate(attestations):
        outcome = vault.recover_shard_ledger(
            shard_ledger, verify_result=verify_result,
            reconstructed_suffix=[_fabricated_seal_row_fields("d-fake")],
            sources=sources, operator_identity=identity, reason=reason,
            recovery_ledger=recovery_ledger, incident_id=f"incident-tr29-attest-{index}",
            quarantine_dir=str(tmp_path / "quarantine"),
        )
        assert outcome == {"ok": False, "resumed": False}, f"attestation {index} changed the outcome"
        assert shard_ledger.verify_chain() == verify_result

    rows = recovery_ledger.all_rows()
    assert [row["outcome"] for row in rows] == ["halted", "halted", "halted"]
    assert [row["operator_identity"] for row in rows] == [a[1] for a in attestations]
    assert [row["attempted_sources"] for row in rows] == [a[0] for a in attestations]


def test_r8_an_empty_reconstruction_can_never_prove_the_ledger_was_always_empty(tmp_path):
    """Found by attacking `recover_shard_ledger` directly while fixing it, not by any report. A
    tail anchor reading `{"row_count": 0, "head_hash": null}` -- which `append_row` never writes,
    so it means tampering or an earlier bad rewrite -- used to be "matched" by supplying NOTHING at
    all: zero rows equals zero rows, no final hash equals no head hash, so the attempt proved
    complete, `rewrite_from_recovery` wiped every sealed row off the ledger, and the three shards
    became fresh and re-sealable under any universe. That is the r8-forbidden outcome reached
    through the PROVEN side of the door rather than the graded one, so the proof now requires a
    non-empty candidate."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    shard_ledger.head_anchor_path.write_text(
        json.dumps({"row_count": 0, "head_hash": None}, sort_keys=True), encoding="utf-8"
    )

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=shard_ledger.verify_chain(), reconstructed_suffix=[],
        sources=[], operator_identity="test-operator", reason="r8 empty-proof probe",
        recovery_ledger=recovery_ledger, incident_id="incident-r8-empty",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}
    assert recovery_ledger.all_rows()[0]["outcome"] == "halted"

    # nothing was wiped: all three sealed shards are still on the ledger and still sealed...
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1", "d-2", "d-3"]
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3"})
    # ...so a re-seal is refused as the ordinary single-shot violation it is, never granted as if
    # the shard were fresh.
    with pytest.raises(vault.ShardLifecycleOrderError):
        vault.seal_shard(
            shard_ledger, dataset_id="d-1", universe_id="u2", content_checksum="f" * 64,
            event_count=100, vault_secret=_FIXTURE_SECRET,
        )


def test_r8_a_prefix_the_file_no_longer_authenticates_can_never_prove_completeness(tmp_path):
    """The second path found by attacking `recover_shard_ledger` directly. `_verified_prefix_rows`
    trusts the CALLER-SUPPLIED `verify_result` to decide how much of the on-disk file is genuine,
    so a `verify_result` that understates the damage ("tail_truncated" over a file whose interior
    row was edited in place) hands the proof a prefix the file itself no longer authenticates --
    and because an in-place edit leaves the LATER rows' stored hashes untouched, the anchor's count
    and head hash both still matched. The attempt therefore used to return `ok: True` and write a
    permanent `recovery_completed` attestation over rows containing a substituted dataset_id. The
    candidate chain is now re-derived from its own contents and must reproduce itself exactly."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    _seal_three_shards(shard_ledger)
    _mutate_interior_row(shard_ledger.path, 0, "dataset_id", "d-evil")  # no rehash: row 0 now lies

    honest = shard_ledger.verify_chain()
    assert honest["reason"] == "content_hash_mismatch" and honest["failed_at_row"] == 0
    # NON-VACUITY: the count and head-hash conjuncts are both still satisfied by this file, so the
    # refusal below is the internal-consistency conjunct doing the work.
    anchor = shard_ledger.read_tail_anchor()
    raw_rows = shard_ledger.all_rows()
    assert anchor["row_count"] == len(raw_rows) == 3
    assert anchor["head_hash"] == raw_rows[-1]["row_hash"]

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger,
        verify_result={"ok": False, "failed_at_row": None, "reason": "tail_truncated"},
        reconstructed_suffix=[], sources=[], operator_identity="test-operator",
        reason="r8 understated-damage probe", recovery_ledger=recovery_ledger,
        incident_id="incident-r8-understated", quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}
    halted = recovery_ledger.all_rows()[0]
    assert halted["outcome"] == "halted"
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    assert halted["attempted_final_row_hash"] == halted["anchor_head_hash"]  # both matched!
    assert halted["attempted_chain_internally_consistent"] is False  # and it still refused

    # no `recovery_completed` attestation exists over a tampered file, and it stays fail-closed.
    assert [row["kind"] for row in recovery_ledger.all_rows()] == ["recovery_halted"]
    assert shard_ledger.verify_chain() == honest
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))


def test_audit_a_recovery_can_never_delete_rows_the_corrupt_file_itself_still_carries(tmp_path):
    """**Iteration-13 AUDIT finding, reproduced end to end before this guard existed.** The tail
    anchor is written AFTER the row it commits to (`micro_chain_ledger.append_row`'s own comment
    calls the window "benign -- never falsely short"), so a crash between the two leaves the ledger
    LONGER than the anchor -- a state the ledger reads and serves perfectly happily. Let an interior
    row then be corrupted, and a byte-GENUINE reconstruction of the ANCHOR-LENGTH history satisfies
    every other conjunct of the proof: non-empty, count == anchor row_count, final hash == anchor
    head_hash, internally consistent. `rewrite_from_recovery` then truncates the surplus rows away.

    Observed before the fix: d-4's seal row vanished, `verify_chain()` reported clean, d-4 was
    re-sealable FRESH under another universe, and a permanent `recovery_completed` attestation
    certified the loss -- r8 section 7.8's forbidden outcome ("no affected shard becomes fresh,
    sealable, assignable ... merely because the reconstructed ledger now verifies internally")
    reached through the PROVEN side of the door rather than the deleted graded one. A recovery may
    never DELETE rows the preserved corrupt file itself still carries."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    original = _seal_three_shards(shard_ledger)
    anchor_at_three = shard_ledger.head_anchor_path.read_text(encoding="utf-8")
    vault.seal_shard(  # the append whose anchor write never landed
        shard_ledger, dataset_id="d-4", universe_id="u1", content_checksum="d" * 64,
        event_count=103, vault_secret=_FIXTURE_SECRET,
    )
    shard_ledger.head_anchor_path.write_text(anchor_at_three, encoding="utf-8")

    # NON-VACUITY: the lagging anchor is not itself a corruption -- all four shards read as sealed.
    assert shard_ledger.verify_chain()["ok"] is True
    assert vault.currently_sealed_dataset_ids(shard_ledger) == frozenset({"d-1", "d-2", "d-3", "d-4"})

    _mutate_interior_row(shard_ledger.path, 0, "universe_id", "u-evil")
    verify_result = shard_ledger.verify_chain()
    assert verify_result["reason"] == "content_hash_mismatch"

    recovery_ledger = vault.VaultRecoveryLedger(vault_dir)
    outcome = vault.recover_shard_ledger(
        shard_ledger, verify_result=verify_result,
        reconstructed_suffix=[vault._row_content(row) for row in original],  # byte-genuine rows
        sources=[{"source": "trusted-backup", "sha256": "0" * 64}],
        operator_identity="honest-operator", reason="audit: anchor-lag truncation probe",
        recovery_ledger=recovery_ledger, incident_id="incident-audit-anchor-lag",
        quarantine_dir=str(tmp_path / "quarantine"),
    )
    assert outcome == {"ok": False, "resumed": False}

    # NON-VACUITY: every OTHER conjunct of the proof was satisfied -- the refusal is this guard.
    halted = recovery_ledger.all_rows()[0]
    assert halted["outcome"] == "halted"
    assert halted["attempted_row_count"] == halted["anchor_row_count"] == 3
    assert halted["attempted_final_row_hash"] == halted["anchor_head_hash"]
    assert halted["attempted_chain_internally_consistent"] is True
    assert halted["preserved_row_count"] == 4

    # d-4's row was never deleted, the vault stays blocked, and d-4 is not sealable again.
    assert [row["dataset_id"] for row in shard_ledger.all_rows()] == ["d-1", "d-2", "d-3", "d-4"]
    assert shard_ledger.verify_chain() == verify_result
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))
    with pytest.raises(vault.VaultLedgerCorruptionError):
        vault.seal_shard(
            shard_ledger, dataset_id="d-4", universe_id="u2", content_checksum="d" * 64,
            event_count=103, vault_secret=_FIXTURE_SECRET,
        )


def test_r8_a_shard_row_carrying_an_unrecognised_state_serves_only_the_opaque_projection(tmp_path):
    """r8 deleted the fourth lifecycle value (`exposure_unknown`) along with the branch that wrote
    it, so this module's state vocabulary is exactly {sealed, assigned, exposed}. `_serialize_shard`
    therefore reveals identity on a POSITIVE whitelist of the two states that earned it, never by
    excluding a blacklist of the ones that did not: a row carrying any other value discloses
    nothing beyond the sealed-shape opaque projection, even though its own content still holds the
    symbol and session date from an earlier assignment."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    vault.seal_shard(
        shard_ledger, dataset_id="d-1", universe_id="u1", content_checksum="a" * 64,
        event_count=100, vault_secret=_FIXTURE_SECRET,
    )
    assigned = vault.assign_shard(
        shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
        session_date="2026-06-09",
    )
    assert "symbol" in vault._serialize_shard(assigned)  # assigned reveals, as always

    shard_ledger.append_row({**vault._row_content(assigned), "exposure_state": "some_future_state"})
    entry = vault.build_vault_state(shard_ledger, vault.VaultUniverseLedger(vault_dir))["shards"][0]
    assert set(entry) == set(vault._OPAQUE_SHARD_KEYS)
    assert entry["exposure_state"] == "some_future_state"
    for leaked in ("symbol", "session_date", "dataset_id", "content_checksum", "family_root_id"):
        assert leaked not in entry


# --- iteration 13's own TC-7: seal_shard/assign_shard/expose_shard are pinned own-ledger-only ----


def test_tc7_seal_assign_expose_are_scoped_to_their_own_shard_ledger_by_design(tmp_path):
    """spec section 7.8's cross-ledger gating question (the iteration-12 reviewer's open item,
    resolved by the iter-13 decomposer, `state/assumptions.md`'s iter-13 second entry):
    seal_shard/assign_shard/expose_shard deliberately gate on their OWN shard ledger only, never
    the universe ledger -- a documented, intentional scope, not an oversight. Pinned two ways: the
    docstrings say so, and a corrupted UNIVERSE ledger (shard ledger intact) does not stop any of
    the three from succeeding exactly as before this iteration."""
    for fn in (vault.seal_shard, vault.assign_shard, vault.expose_shard):
        doc = fn.__doc__ or ""
        assert "own shard ledger only" in doc, (
            f"{fn.__name__}'s docstring must state its corruption gating is scoped to its own "
            "shard ledger only"
        )

    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    _truncate_ledger_tail(universe_ledger)  # the OTHER ledger corrupted -- shard ledger untouched
    assert universe_ledger.verify_chain()["ok"] is False
    assert shard_ledger.verify_chain()["ok"] is True  # pristine -- nothing sealed here yet

    sealed = vault.seal_shard(
        shard_ledger, dataset_id="d-1", universe_id="u1", content_checksum="a" * 64,
        event_count=100, vault_secret=_FIXTURE_SECRET,
    )
    assert sealed["exposure_state"] == vault.STATE_SEALED
    assigned = vault.assign_shard(
        shard_ledger, dataset_id="d-1", family_root_id="root", symbol="PG",
        session_date="2026-06-09",
    )
    assert assigned["exposure_state"] == vault.STATE_ASSIGNED
    exposed = vault.expose_shard(shard_ledger, dataset_id="d-1", family_root_id="root")
    assert exposed["exposure_state"] == vault.STATE_EXPOSED

    # the corrupted universe ledger is exactly as corrupted as before -- none of these touched it.
    assert universe_ledger.verify_chain()["ok"] is False


# --- TR-27/TC-6/TC-8: the nonced commitment -- dictionary-attack resistance ------------------------


def test_tc8_a_dictionary_attack_cannot_verify_the_commitment_without_the_nonce(tmp_path):
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    real_symbols, real_dates = ["PG", "AAPL", "MSFT"], ["2026-06-08", "2026-06-09"]
    row = vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=real_symbols, date_rule=real_dates,
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    served_commitment = row["rule_commitment"]
    assert served_commitment != row["rule_hash"]  # the served value is NEVER the bare hash

    # a plausible-guess dictionary attack -- every guess hashed WITHOUT the nonce (never served
    # pre-reveal), including guessing the EXACT right rule and a re-ordered permutation of it.
    guesses = [
        (["PG"], ["2026-06-08"]),
        (["PG", "AAPL"], ["2026-06-08", "2026-06-09"]),
        (real_symbols, real_dates),
        (["AAPL", "MSFT", "PG"], real_dates),
    ]
    for symbols_guess, dates_guess in guesses:
        assert vault.compute_rule_hash(symbols_guess, dates_guess) != served_commitment
        assert vault.compute_rule_commitment("0" * 64, symbols_guess, dates_guess) != served_commitment

    # the REAL nonce (never served pre-reveal) is the only input that reproduces it.
    assert (
        vault.compute_rule_commitment(row["commitment_nonce"], real_symbols, real_dates)
        == served_commitment
    )


def test_the_committed_stage_never_serves_a_bare_rule_hash_or_the_nonce(tmp_path):
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    committed = vault.build_vault_state(
        vault.VaultShardLedger(str(tmp_path / "vault")), universe_ledger
    )["universes"][0]
    assert committed["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
    assert "rule_hash" not in committed
    assert "commitment_nonce" not in committed
    assert set(committed) == {
        "universe_id", "registered_at", "rule_commitment", "vault_secret_commitment",
        "symbol_rule_size", "date_rule_size", "rule_disclosure",
    }


def test_an_idempotent_re_registration_keeps_the_same_nonce_and_commitment(tmp_path):
    """TR-27's own idempotency corollary: a crash-retry of the ONE operator registration act must
    not mint a SECOND nonce for what is, by definition, the same registration."""
    universe_ledger = vault.VaultUniverseLedger(str(tmp_path / "vault"))
    kwargs = dict(
        universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    first = vault.register_universe(universe_ledger, **kwargs)
    again = vault.register_universe(universe_ledger, **kwargs)
    assert again["commitment_nonce"] == first["commitment_nonce"]
    assert again["rule_commitment"] == first["rule_commitment"]
    assert len(universe_ledger.all_rows()) == 1


def test_two_shards_sharing_one_pair_keep_the_universe_hidden_even_after_one_is_exposed(tmp_path):
    """Adversarial pre-ship review finding, pinned as a permanent regression test.

    Nothing in this module (or TR-12's single-shot discipline, which scopes to (family, shard),
    never to (symbol, date)) stops a SECOND, DIFFERENT shard from being sealed and assigned under
    the identical (symbol, session_date) pair as a first shard that has already reached
    ``exposed`` -- ``dataset_id`` is a random per-recording identifier, and a re-recorded/retry
    day is exactly the shape spec section 7.7 anticipates. A pair-keyed-only "whole pool released"
    check would be satisfied by the FIRST shard's exposure alone, wrongly revealing the universe's
    rule while the SECOND, genuinely still-withheld shard for that very pair sits unexposed --
    reopening the exact two-GET subtraction class TR-27 exists to close. This is the failure mode
    ``_whole_pool_released_universe_ids``'s own test (a) (ledger-tracked-shard check) closes,
    alongside test (b) (pair-coverage) -- this test exercises the UNION, not either half alone."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["PG"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")

    # shard A: sealed -> assigned -> EXPOSED, for ("PG", "2026-06-09").
    vault.seal_shard(
        shard_ledger, dataset_id="shard-a", universe_id="u1", content_checksum="a" * 64,
        event_count=100, vault_secret=_FIXTURE_SECRET,
    )
    vault.assign_shard(
        shard_ledger, dataset_id="shard-a", family_root_id=family_root, symbol="PG",
        session_date="2026-06-09",
    )
    vault.expose_shard(shard_ledger, dataset_id="shard-a", family_root_id=family_root)

    # a NAIVE pair-only check would already call the pool "released" here -- confirm the pair IS
    # covered by an exposed shard before proving the fuller predicate still refuses.
    exposed_only_state = vault.build_vault_state(shard_ledger, universe_ledger)
    assert exposed_only_state["universes"][0]["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED, (
        "test setup sanity check failed: with only shard A sealed, the SAME pair with no second "
        "shard legitimately releases -- if this fails, the rest of this test proves nothing"
    )

    # shard B: sealed -> assigned for the SAME pair, but never exposed -- a second, independent
    # dataset_id (a re-recorded/retry day), still genuinely withheld.
    vault.seal_shard(
        shard_ledger, dataset_id="shard-b", universe_id="u1", content_checksum="b" * 64,
        event_count=200, vault_secret=_FIXTURE_SECRET,
    )
    vault.assign_shard(
        shard_ledger, dataset_id="shard-b", family_root_id=family_root, symbol="PG",
        session_date="2026-06-09",
    )

    state = vault.build_vault_state(shard_ledger, universe_ledger)
    universe = state["universes"][0]
    assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED, (
        "shard B is sealed+assigned but NOT exposed -- the universe must stay hidden even though "
        "shard A already covers this pair's exact (symbol, date)"
    )
    assert "symbol_rule" not in universe and "date_rule" not in universe

    # exposing shard B too (closing the pool for real) now correctly reveals.
    vault.expose_shard(shard_ledger, dataset_id="shard-b", family_root_id=family_root)
    fully_released = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert fully_released["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED


# --- TC-12/TC-13: symbol-case normalization on the withhold predicate -------------------------------


def test_tc12_a_lowercase_registered_rule_still_withholds_an_uppercase_recorded_dataset(tmp_path):
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["aapl"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    withheld = vault.unresolved_pool_universe_by_dataset_id(
        shard_ledger, universe_ledger,
        [("d-1", "AAPL", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
    )
    assert withheld == {"d-1": "u1"}


def test_tc13_an_uppercase_registered_rule_still_withholds_a_lowercase_recorded_dataset(tmp_path):
    """TC-12's mirror -- normalization must work in BOTH directions, never only one."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["AAPL"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    withheld = vault.unresolved_pool_universe_by_dataset_id(
        shard_ledger, universe_ledger,
        [("d-1", "aapl", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
    )
    assert withheld == {"d-1": "u1"}


def test_case_mismatch_normalization_does_not_widen_a_genuinely_different_symbol(tmp_path):
    """The counter-test: normalization is case-folding ONLY, never a fuzzy match -- a genuinely
    different ticker never withholds."""
    vault_dir = str(tmp_path / "vault")
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="u1", symbol_rule=["AAPL"], date_rule=["2026-06-09"],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    withheld = vault.unresolved_pool_universe_by_dataset_id(
        shard_ledger, universe_ledger,
        [("d-1", "AAPLE", "2026-06-09", "2027-01-01T00:00:00.000000Z")],
    )
    assert withheld == {}


# --- TC-14: the widened TR-2 sweep -- an untracked pool member's symbol/date strings too -----------


def test_tc14_the_widened_tr2_sweep_forbids_an_untracked_pool_members_symbol_and_date_strings(
    tmp_path, monkeypatch
):
    """The gap the phase spec's own BACKGROUND names precisely: the pre-iteration-12 sweeps check
    dataset id/raw checksum (and, for a single globally-unique sealed shard, its symbol/window) --
    but the r5 inference-trap fixture's OWN "mixed provenance" pool deliberately REUSES symbols and
    dates across its exposed/withheld members (to test the (a)+(b) union logic), which makes a
    naive raw-substring check there a false-positive trap. This test uses a CLEAN fixture instead:
    one untracked pool member (test (b) territory -- no vault ledger row at all) whose symbol AND
    date are GLOBALLY UNIQUE, not shared with anything else served -- so "this string appears
    nowhere in the swept union" is a meaningful, unambiguous assertion."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)  # the 2 real PG fixtures -- proven compute-safe

    untracked_symbol, untracked_date = "ZQXTC14", "2031-09-09"
    vault_dir = str(tmp_path / "micro_vault")
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="tc14-universe", symbol_rule=[untracked_symbol],
        date_rule=[untracked_date], vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    untracked_meta = _record_pool_dataset(
        store, symbol=untracked_symbol, session_date=untracked_date, nonce=99
    )
    # deliberately NO vault.seal_shard call -- today's actual recorder gap (test (b) territory).

    with TestClient(app) as client:
        assert client.post("/research/desk/micro/snapshots/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
        assert client.post("/research/desk/micro/scout/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"

        built = {m["dataset_id"] for m in client.get("/research/desk/micro/snapshots").json()["snapshots"]}
        assert untracked_meta["id"] not in built  # the counter-test: withholding really happened

        swept: dict[str, object] = {}
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", untracked_meta["id"])
            if "{" in url:
                continue
            response = client.get(url)
            try:
                swept[path] = response.json()
            except ValueError:
                swept[path] = response.text
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        assert "/research/desk/micro/recorder/compute" in swept  # the recorder progress path too

        from app.mcp import _STATIC_PATHS

        assert _STATIC_PATHS["datasets"] in swept  # the `datasets` MCP tool's exact proxied path

        served_text = json.dumps(swept, sort_keys=True, default=str)
        assert untracked_symbol not in served_text, "the untracked pool member's symbol leaked"
        assert untracked_date not in served_text, "the untracked pool member's session date leaked"
        assert untracked_meta["id"] not in served_text
        assert untracked_meta["checksum"] not in served_text


def test_load_vault_secret_expands_the_home_idiom_in_the_configured_path(tmp_path, monkeypatch):
    """A configured ``TAPEOLOGY_VAULT_SECRET_FILE`` may use ``~``. A shell expands it; ``Path`` does
    not, so an EXISTING secret file was raising ``VaultSecretUnavailable`` and blocking J-06
    universe registration outright. Found live during the J-06 preflight."""
    home = tmp_path / "home"
    (home / ".config" / "tapeology").mkdir(parents=True)
    (home / ".config" / "tapeology" / "vault-secret").write_text("s3cret-under-home\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("TAPEOLOGY_VAULT_SECRET_FILE", "~/.config/tapeology/vault-secret")

    assert vault.load_vault_secret() == b"s3cret-under-home"


def test_an_unexpandable_missing_secret_still_refuses_typed(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TAPEOLOGY_VAULT_SECRET_FILE", "~/nope/vault-secret")
    with pytest.raises(vault.VaultSecretUnavailable):
        vault.load_vault_secret()


# === the Tier-B screen provenance ledger (§7.2 step 2 / §7.2.1 (j)) ===============================


def _screen_kwargs(**over):
    base = dict(
        screen_id="rapid-microscope-tier-b-r11",
        spec_revision="r11",
        screening_cutoff_utc="2026-08-21T12:06:00Z",
        source_snapshot_sha256={"nasdaqlisted": "85fe4372", "otherlisted": "4191463d"},
        candidate_universe_membership_hash="b72805fb",
        screening_artifacts={"tier-b-resolution.json": "fb89c5a2"},
        resolution_artifact_sha256="fb89c5a2",
        resolved_tier_b=["AG", "LYFT", "WULF"],
        resolution_rule_identity="sha256(rapid-microscope-tier-b-r10: + ticker), exactly-3",
    )
    base.update(over)
    return base


def test_screen_provenance_is_a_distinct_ledger_that_cannot_confuse_find_universe(tmp_path):
    """The reason this is a separate file: ``find_universe`` resolves the LATEST row carrying a
    given ``universe_id``, so a screen row sharing that field could masquerade as a registration and
    silently redefine ``expected_recording_pairs``, neutralizing TR-4."""
    root = str(tmp_path)
    sled = vault.VaultScreenProvenanceLedger(root)
    uled = vault.VaultUniverseLedger(root)
    row = vault.record_screen_provenance(sled, **_screen_kwargs())

    assert row["record_kind"] == "tier_b_screen_provenance"
    assert "universe_id" not in row
    assert sled.path != uled.path
    # the universe ledger is untouched, so no screen row can resolve as a registration
    assert uled.all_rows() == []
    assert vault.find_universe(uled, "rapid-microscope-tier-b-r11") is None
    assert vault.find_screen_provenance(sled, "rapid-microscope-tier-b-r11")["resolved_tier_b"] == [
        "AG", "LYFT", "WULF"]


def test_recording_the_same_screen_twice_is_idempotent_not_a_second_row(tmp_path):
    sled = vault.VaultScreenProvenanceLedger(str(tmp_path))
    a = vault.record_screen_provenance(sled, **_screen_kwargs())
    b = vault.record_screen_provenance(sled, **_screen_kwargs())
    assert a["row_index"] == b["row_index"]
    assert len(sled.all_rows()) == 1


def test_a_conflicting_re_record_of_one_screen_id_is_refused(tmp_path):
    """A screen's history can never be quietly rewritten."""
    sled = vault.VaultScreenProvenanceLedger(str(tmp_path))
    vault.record_screen_provenance(sled, **_screen_kwargs())
    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError):
        vault.record_screen_provenance(sled, **_screen_kwargs(resolved_tier_b=["AG", "LYFT", "TDC"]))


def test_the_screen_provenance_chain_verifies(tmp_path):
    sled = vault.VaultScreenProvenanceLedger(str(tmp_path))
    vault.record_screen_provenance(sled, **_screen_kwargs())
    assert sled.verify_chain()["ok"] is True
    assert sled.verified_rows()[0]["resolution_artifact_sha256"] == "fb89c5a2"


# =====================================================================================================
# TR-33 — pool-position disclosure incidents (spec r12 §7.2.2, owner repair ruling 2026-08-22).
#
# The J-06 §14 operator report stated in plain text that one registered pair is NOT HMAC-selected.
# That is a real, already-happened leak of one bit of the hidden partition. It is recorded rather
# than glossed, and it carries a permanent evidence consequence: `assign_shard` -- the transition
# that grants a shard blind/historical-OOS credit -- refuses that pool position forever.
# =====================================================================================================


def _disclose(ledger, pair, *, incident_id="inc-1", universe_id="u1"):
    return vault.record_disclosure_incident(
        ledger,
        incident_id=incident_id,
        disclosure_type=vault.DISCLOSURE_NON_SEALED_POOL_POSITION,
        universe_id=universe_id,
        pairs=[pair],
        source="operator report to the owner",
        occurred_at="2026-08-22T00:55:23Z",
        sealed_member_identity_disclosed=False,
        evidence_consequence="PERMANENT: never sealed/blind/historical_oos credit",
    )


def test_assign_shard_refuses_a_disclosed_pool_position(tmp_path):
    """The permanent consequence, enforced where the credit is actually granted. The incident
    ledger is resolved from the shard ledger's OWN root dir, so no caller can opt out by simply
    not passing it."""
    shard_ledger = vault.VaultShardLedger(str(tmp_path))
    disclosure_ledger = vault.VaultDisclosureIncidentLedger(str(tmp_path))
    root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    for dataset_id in ("d-disclosed", "d-clean"):
        vault.seal_shard(
            shard_ledger, dataset_id=dataset_id, universe_id="u1", content_checksum="a" * 64,
            event_count=1000, vault_secret=_FIXTURE_SECRET,
        )
    _disclose(disclosure_ledger, ("NVDA", "2026-07-08"))

    with pytest.raises(vault.DisclosedPoolPositionError) as excinfo:
        vault.assign_shard(shard_ledger, dataset_id="d-disclosed", family_root_id=root,
                           symbol="NVDA", session_date="2026-07-08")
    assert excinfo.value.incident_id == "inc-1"
    assert vault._latest_shard_row(shard_ledger, "d-disclosed")["exposure_state"] == vault.STATE_SEALED

    # counter-test: an undisclosed pool position still assigns normally, so the refusal above is
    # the disclosure biting and not the lifecycle check firing for an unrelated reason.
    row = vault.assign_shard(shard_ledger, dataset_id="d-clean", family_root_id=root,
                             symbol="NVDA", session_date="2026-07-15")
    assert row["exposure_state"] == vault.STATE_ASSIGNED


def test_record_disclosure_incident_refuses_to_represent_a_sealed_member_leak(tmp_path):
    """A leaked SEALED member's identity is a graver event with no containment in this model.
    Recording one here would silently imply containment exists, so it is refused outright -- the
    owner's own "if there is no lawful way to represent it, STOP and report" instruction, made
    structural."""
    ledger = vault.VaultDisclosureIncidentLedger(str(tmp_path))
    with pytest.raises(ValueError, match="escalated, never recorded as contained"):
        vault.record_disclosure_incident(
            ledger, incident_id="bad", disclosure_type=vault.DISCLOSURE_NON_SEALED_POOL_POSITION,
            universe_id="u1", pairs=[("NVDA", "2026-07-08")], source="x",
            occurred_at="2026-08-22T00:00:00Z", sealed_member_identity_disclosed=True,
            evidence_consequence="y",
        )
    assert ledger.all_rows() == []


def test_an_unknown_disclosure_type_is_refused_rather_than_recorded_as_handled(tmp_path):
    ledger = vault.VaultDisclosureIncidentLedger(str(tmp_path))
    with pytest.raises(ValueError, match="unknown disclosure_type"):
        vault.record_disclosure_incident(
            ledger, incident_id="bad", disclosure_type="sealed_member_identity",
            universe_id="u1", pairs=[("NVDA", "2026-07-08")], source="x",
            occurred_at="2026-08-22T00:00:00Z", sealed_member_identity_disclosed=False,
            evidence_consequence="y",
        )
    assert ledger.all_rows() == []


def test_a_disclosure_incident_is_idempotent_but_can_never_be_quietly_rewritten(tmp_path):
    ledger = vault.VaultDisclosureIncidentLedger(str(tmp_path))
    first = _disclose(ledger, ("NVDA", "2026-07-08"))
    again = _disclose(ledger, ("NVDA", "2026-07-08"))
    assert again["row_index"] == first["row_index"]
    assert len(ledger.all_rows()) == 1
    with pytest.raises(vault.VaultUniverseAlreadyRegisteredError):
        _disclose(ledger, ("AAPL", "2026-07-08"))
    assert len(ledger.all_rows()) == 1
    assert ledger.verify_chain()["ok"] is True


def test_the_disclosure_ledger_is_a_fourth_separate_chain(tmp_path):
    """Same structural reason the screen-provenance ledger is separate: an incident row must never
    be resolvable as a universe registration or a shard-lifecycle transition."""
    root = str(tmp_path)
    ledgers = {
        "universe": vault.VaultUniverseLedger(root).path,
        "shard": vault.VaultShardLedger(root).path,
        "screen": vault.VaultScreenProvenanceLedger(root).path,
        "disclosure": vault.VaultDisclosureIncidentLedger(root).path,
    }
    assert len({str(p) for p in ledgers.values()}) == 4
    disclosure_ledger = vault.VaultDisclosureIncidentLedger(root)
    _disclose(disclosure_ledger, ("NVDA", "2026-07-08"))
    assert vault.VaultUniverseLedger(root).all_rows() == []
    assert vault.VaultShardLedger(root).all_rows() == []
    assert vault.find_universe(vault.VaultUniverseLedger(root), "u1") is None
    assert vault.disclosed_pool_positions(disclosure_ledger, "u1") == {("NVDA", "2026-07-08"): "inc-1"}
    assert vault.disclosed_pool_positions(disclosure_ledger, "other-universe") == {}


def test_tr2_holds_when_one_non_selected_pool_position_is_publicly_disclosed(tmp_path, monkeypatch):
    """TR-2, re-run with the disclosure treated as attacker-known public information.

    The attacker is granted: the registered universe rule, every served/public artifact, the
    published selected COUNT, and the fact that one specific pool position is NOT selected. The
    claim under test is that no still-unexposed selected shard's identity becomes determinable.

    Two independent halves, because a disclosure can bite in two ways. OBSERVATIONALLY: the
    disclosure must not make the system itself start serving pool identities -- the swept union of
    every registered GET route (plus the `datasets` MCP path) still identifies none of the pool's
    pairs, and the incident record itself is never served. COMBINATORIALLY: conditioning on one
    non-selected position leaves strictly more unknown positions than remaining selected shards, so
    the hidden set is not pinned and every sealed row keeps >= 2 candidate identities.

    Non-vacuous by construction: the fixture's HMAC split is asserted to be a real split (both
    sides non-empty), the compute acts run FIRST and are asserted to have measured the two real PG
    fixture datasets, and the counter-case -- disclosing every non-selected position WOULD pin the
    hidden set -- is computed in the same arithmetic."""
    _scope_everything_to(tmp_path, monkeypatch)
    store = _combined_fixture_store(tmp_path)

    symbols, dates = ["ZQXDISC1", "ZQXDISC2", "ZQXDISC3"], ["2031-07-01", "2031-07-02"]
    expected_pairs = frozenset((s, d) for s in symbols for d in dates)
    vault_dir = str(tmp_path / "micro_vault")
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.register_universe(
        universe_ledger, universe_id="pool-disc", symbol_rule=symbols, date_rule=dates,
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
    )
    shard_ledger = vault.VaultShardLedger(vault_dir)
    disclosure_ledger = vault.VaultDisclosureIncidentLedger(vault_dir)

    metas = {}
    for s_index, symbol in enumerate(symbols):
        for d_index, session_date in enumerate(dates):
            metas[(symbol, session_date)] = _record_pool_dataset(
                store, symbol=symbol, session_date=session_date, nonce=s_index * 10 + d_index)

    selected = [p for p in sorted(expected_pairs) if vault.compute_seal(_FIXTURE_SECRET, *p)]
    non_selected = [p for p in sorted(expected_pairs) if p not in set(selected)]
    assert selected and len(non_selected) >= 2, "the fixture's HMAC split must be a real split"
    for pair in selected:
        meta = metas[pair]
        vault.seal_shard(
            shard_ledger, dataset_id=meta["id"], universe_id="pool-disc",
            content_checksum=meta["checksum"], event_count=meta["event_counts"]["total"],
            vault_secret=_FIXTURE_SECRET,
        )

    disclosed_pair = non_selected[0]
    _disclose(disclosure_ledger, disclosed_pair, incident_id="inc-disc", universe_id="pool-disc")

    from app.config import CONFIG
    from app.mcp import _STATIC_PATHS
    from app.research import edge_report
    from app.research.store import JournalStore

    with TestClient(app) as client:
        assert client.post("/research/desk/micro/snapshots/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/snapshots/compute")["state"] == "done"
        assert client.post("/research/desk/micro/scout/compute").json()["state"] == "running"
        assert _poll_compute(client, "/research/desk/micro/scout/compute")["state"] == "done"

        journal = JournalStore(CONFIG.journal_db_path_resolved(), CONFIG)
        try:
            report = edge_report.run_edge_report(journal, store, CONFIG)
        finally:
            journal.close()
        measured = {r["dataset_id"] for r in report["train"]["datasets"] + report["holdout"]["datasets"]}
        assert measured, "the compute acts must have measured SOMETHING -- else the sweep is vacuous"
        assert not (measured & {m["id"] for m in metas.values()})
        assert report["withheld_excluded"] == len(expected_pairs)

        swept = {}
        for path in _sweepable_get_paths():
            if "{" in path:
                continue
            response = client.get(path)
            try:
                swept[path] = response.json()
            except ValueError:
                swept[path] = response.text
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        assert _STATIC_PATHS["datasets"] in swept
        served_text = json.dumps(swept, sort_keys=True, default=str)

        # --- observational half -------------------------------------------------------------
        datasets_body = swept["/research/datasets"]
        assert len(datasets_body["datasets"]) >= 2, "the two real PG fixtures must still be served"
        served_pairs = {
            (row["symbol"], _et_session_date(row["window_start_utc"]))
            for row in datasets_body["datasets"]
        }
        assert served_pairs & expected_pairs == frozenset(), "a pool pair became identifiable"
        for pair, meta in metas.items():
            assert meta["id"] not in served_text, f"{pair}'s dataset id leaked"
            assert meta["checksum"] not in served_text, f"{pair}'s raw checksum leaked"
        # the incident itself is an internal audit record, never a served surface -- publishing it
        # would re-broadcast the very pool position it exists to contain.
        assert "inc-disc" not in served_text
        assert "pool_position_disclosure_incident" not in served_text
        assert disclosed_pair[0] not in served_text

    # --- combinatorial half -----------------------------------------------------------------
    unknown = len(expected_pairs) - 1                      # conditioned on the one disclosure
    still_selected = len(selected)                          # none exposed in this fixture
    assert unknown > still_selected, "the hidden set would be fully determined"
    assert unknown - still_selected >= 1
    assert unknown >= 2, "at least 2 candidate identities must remain for every sealed row"
    # the counter-case, in the same arithmetic: disclose every non-selected position and certainty
    # DOES arrive -- so the assertion above is a measurement, not a tautology.
    assert len(expected_pairs) - len(non_selected) == still_selected


# === Iteration 25 (J-06 close-out): the browser-QA rig's own new permanently-sealed fixture shard
# is proven refused non-vacuously, using the SAME production seeder function the QA launcher's own
# extension calls (``scripts/seed_micro_vault_iter25_sealed_fixture.py`` -- never a second,
# divergent test-only construction of "a sealed shard"). TC-1/TC-8. =================================


def test_tc1_iter25_the_qa_rigs_new_sealed_only_fixture_shard_serves_the_opaque_projection_only(
    tmp_path, monkeypatch
):
    """TC-1: the iteration-25 QA-rig seeder plants a REAL dataset and calls the REAL
    ``vault.seal_shard`` -- never ``assign_shard``/``expose_shard`` -- so
    ``GET /research/desk/micro/vault`` must list it ``sealed`` with no
    ``symbol``/``session_date``/``dataset_id``/``family_root_id`` populated. Runs the actual
    production seeder against the same fixture-rig env-var scoping the browser-QA launcher itself
    uses (``_scope_everything_to``), not a hand-rolled duplicate."""
    _scope_everything_to(tmp_path, monkeypatch)
    planted = _iter25_seed_vault.plant_sealed_shard(tmp_path)

    with TestClient(app) as client:
        state = client.get("/research/desk/micro/vault").json()
    shards = {s["shard_id"]: s for s in state["shards"]}
    assert planted["shard_id"] in shards, "the seeded shard never landed in the served vault state"
    entry = shards[planted["shard_id"]]
    assert entry["exposure_state"] == "sealed"
    assert set(entry.keys()) == {
        "shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state",
    }
    for forbidden_key in ("symbol", "session_date", "dataset_id", "family_root_id"):
        assert forbidden_key not in entry
    assert planted["dataset_id"] not in json.dumps(entry)
    assert planted["symbol"] not in json.dumps(entry)


def test_tc8_iter25_the_qa_rigs_sealed_fixture_shard_is_refused_non_vacuously_on_every_non_vault_surface(
    tmp_path, monkeypatch
):
    """TC-8: sweep every registered GET route (the same ``_sweepable_get_paths``/forbidden-token
    machinery the TR-2 tests above already proved sound) against the LITERAL shard the QA rig's own
    iteration-25 seeder plants, plus a direct ``MicroAccessor`` read -- proving the refusal actually
    fires for THIS shard's id/symbol on every non-Vault surface, never merely that no exception
    happened to occur. (The MCP surface is already covered structurally, not shard-by-shard, by
    ``test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route`` above -- it proves route-
    set equivalence with the REST sweep for ANY shard, this one included, so it is not re-swept
    here.)"""
    _scope_everything_to(tmp_path, monkeypatch)
    planted = _iter25_seed_vault.plant_sealed_shard(tmp_path)
    dataset_store = DatasetStore(tmp_path / "datasets")

    forbidden_substrings = {
        "dataset id": planted["dataset_id"],
        "raw content checksum": planted["content_checksum"],
        "symbol": planted["symbol"],
    }

    with TestClient(app) as client:
        leaks: list[str] = []
        swept: dict[str, int] = {}
        for path in _sweepable_get_paths():
            url = path.replace("{dataset_id}", planted["dataset_id"])
            if "{" in url:
                continue  # a parameterized path with no sealed-shard-reachable value to fill
            response = client.get(url)
            swept[path] = response.status_code
            for name, token in forbidden_substrings.items():
                if token in response.text:
                    leaks.append(f"{path} serves the sealed shard's {name}")
        assert leaks == [], "join-resistance breached:\n  " + "\n  ".join(leaks)
        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
        assert swept["/research/datasets/{dataset_id}"] == 403  # this exact shard's id, refused
        assert swept["/research/desk/micro/vault"] == 200
        assert swept["/research/desk/micro/readiness"] == 200

    # non-vacuity: the seeder's own dataset really did land on disk -- proves the sweep above ran
    # against a live surface with something real to withhold, not an empty route table.
    listed = dataset_store.list()[0]
    assert any(m["id"] == planted["dataset_id"] for m in listed), "the seeder's own dataset never landed on disk"

    # direct accessor read: the SAME typed refusal micro_accessor.py already proves generically
    # (test_micro_accessor.py TC-2), exercised here against THIS shard's literal id.
    accessor = ma.MicroAccessor(
        dataset_store, str(tmp_path / "snapshots"), CONFIG,
        sealed_dataset_ids=frozenset({planted["dataset_id"]}),
    )
    with pytest.raises(ma.MicroAccessorSealedShardError) as excinfo:
        accessor.read_snapshot_rows(planted["dataset_id"])
    assert excinfo.value.opaque_metadata == {"shard_id": planted["dataset_id"], "status": "sealed"}
