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
import shutil
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import vault
from app.research.datasets import DatasetStore
from app.research.scout_ledger import compute_family_root_id as _scout_compute_family_root_id

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
        # the commitment stage: the rule's HASH and SHAPE, never its membership.
        assert universe["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED
        assert universe["rule_hash"] == vault.compute_rule_hash(symbols, dates)
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

    # the reveal half: once EVERY shard of the universe is exposed, section 7.2's audit trail is
    # served in full again -- the commitment is a delay, never a permanent withholding.
    family_root = vault.compute_family_root_id("impact_efficiency_trend", "band_wall_touch", "trades_20")
    vault.assign_shard(
        shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root,
        symbol=secret_member[0], session_date=secret_member[1],
    )
    still_withheld = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert still_withheld["rule_disclosure"] == vault.RULE_DISCLOSURE_COMMITTED  # assigned != exposed

    vault.expose_shard(shard_ledger, dataset_id=sealed_meta["id"], family_root_id=family_root)
    revealed = vault.build_vault_state(shard_ledger, universe_ledger)["universes"][0]
    assert revealed["rule_disclosure"] == vault.RULE_DISCLOSURE_REVEALED
    assert revealed["symbol_rule"] == symbols and revealed["date_rule"] == dates
    assert revealed["rule_hash"] == vault.compute_rule_hash(symbols, dates)


def test_audit_b1_a_universe_with_no_shards_yet_keeps_its_rule_committed(tmp_path):
    """The fail-closed half of the fix. Spec section 7.2's mandated order registers the universe
    (step 5) BEFORE any vendor fetch (step 7), so there is a real window in which the universe owns
    zero shards -- and a reader who harvests the rule during that window keeps it for the whole
    tranche's life. `_fully_exposed_universe_ids` therefore reveals only a universe that owns at
    least one shard AND has none left withheld; "no shards" reveals nothing."""
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
