"""``micro_corpus.py`` -- what a ``corpus_id`` actually MEANS, in datasets (r14.1).

**The hole this closes.** r14 gave a fresh corpus era a provenance record, and every consumer then
resolved its membership by SESSION DATE against the globally visible ``DatasetStore``. Three things
followed, and all three are laundering routes:

1. a legacy dataset that happens to share a calendar date with a new-corpus recording was pooled
   into the new corpus, carrying its exposed history in with it;
2. a dataset belonging to a DIFFERENT registered universe was pooled in the same way;
3. a brand-new ``corpus_id`` could be pointed at already-exposed data and declared fresh, because
   nothing bound the id to a physical body of evidence at all.

A corpus id must not mean "every visible dataset whose date happens to match". It means: **the
members of one registered recording universe that the frozen release plan marks releasable, that
the store proves are genuine recorder output created after that universe's own registration, and
that no exposure or incident has barred.** That set is computed here, once, from data that exists
before any outcome is read -- never from what a fold happens to find.

**Mixed released/sealed dates are normal, and are the point (A).** Seal assignment is per
``(symbol, session_date)``, so a healthy 8-symbol date typically holds ~6 not-selected members and
~2 sealed ones. r14's reader refused the WHOLE date if any member was withheld, which made the real
architecture unusable. The fix is not "drop the withheld ones quietly" -- silence is how a corpus
shrinks without saying so. The fix is a PRECOMMITTED member set: the sealed members were never in
this corpus, so they are not exclusions to be filtered, they are non-members. What IS disclosed is
how many of each class the date holds, and the fold's realized symbol breadth, computed from the
observations that actually exist rather than assumed from the panel size.

**No sealed shard is ever read.** Membership is decided from the vault ledgers and the store's
already-verified METADATA -- symbol, session date, checksum, ``schema_basis``, ``created_utc``.
Nothing here loads events or snapshot rows, so a sealed member cannot be read even by accident:
its id never enters the manifest a reader is handed.
"""

from __future__ import annotations

import hashlib
import json

from .datasets import DatasetStore
from .micro_accessor import (
    ExposureRegistry,
    fresh_corpus_era_record,
    register_fresh_corpus_era,
)
from . import vault

__all__ = [
    "CorpusNotBoundError",
    "CorpusMembershipError",
    "register_bound_corpus_era",
    "resolve_corpus_binding",
    "corpus_is_bound",
    "eligible_oos_members",
    "corpus_manifest_hash",
    "members_for_sessions",
    "corpus_session_dates",
]


class CorpusNotBoundError(Exception):
    """A caller asked what a ``corpus_id`` contains, and it carries no bound corpus-era
    registration -- refused. An unbound id has no defined membership, and guessing one from the
    visible store is precisely the laundering route r14.1 exists to close."""


class CorpusMembershipError(Exception):
    """A bound corpus's membership could not be resolved honestly -- the universe named by its
    registration is gone, the committed release plan is missing, or the plan no longer recomputes
    to what was committed."""


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


# === binding: corpus_id -> a registered universe ===================================================


def register_bound_corpus_era(
    registry: ExposureRegistry,
    universe_ledger: "vault.VaultUniverseLedger",
    *,
    corpus_id: str,
    universe_id: str,
    registered_at: str,
    provenance_note: str = "",
) -> dict:
    """Register ``corpus_id`` as a fresh era BOUND to an existing registered universe (r14.1).

    The universe must already exist: its identity fields are read off the vault ledger and frozen
    into the registration, so the binding is a fact this function PROVED rather than a claim the
    caller made. ``freshness_boundary`` is the universe's own ``registered_at`` -- a dataset that
    already existed at that instant cannot be one of this universe's recordings, which is what
    stops a legacy dataset from being adopted into a fresh corpus.

    Conflicting re-registration refuses (``micro_accessor.ConflictingCorpusEraError``)."""
    universe = vault.find_universe(universe_ledger, universe_id)
    if universe is None:
        raise vault.VaultUniverseNotRegisteredError(
            f"universe_id {universe_id!r} is not registered -- refused (r14.1): a corpus era can "
            "only be bound to a universe that actually exists, because the universe is what "
            "defines the corpus's membership"
        )
    return register_fresh_corpus_era(
        registry,
        corpus_id=corpus_id,
        universe_id=universe_id,
        universe_registered_at=universe["registered_at"],
        rule_commitment=universe["rule_commitment"],
        vault_secret_commitment=universe["vault_secret_commitment"],
        expected_pair_count=len(vault.expected_recording_pairs(universe)),
        freshness_boundary=universe["registered_at"],
        registered_at=registered_at,
        provenance_note=provenance_note,
    )


def resolve_corpus_binding(registry: ExposureRegistry, corpus_id: str) -> dict:
    """The frozen corpus-era registration for ``corpus_id`` -- ``CorpusNotBoundError`` if none."""
    row = fresh_corpus_era_record(registry, corpus_id)
    if row is None:
        raise CorpusNotBoundError(
            f"corpus_id {corpus_id!r} carries no corpus-era registration -- refused (r14.1): its "
            "membership is undefined, and inferring one from the visible store is the laundering "
            "route this refusal exists to close"
        )
    if not row.get("universe_id"):
        raise CorpusNotBoundError(
            f"corpus_id {corpus_id!r} carries a PRE-r14.1 unstructured corpus-era row with no "
            "bound universe -- refused: re-register it with a structured binding"
        )
    return row


def corpus_is_bound(registry: ExposureRegistry, corpus_id: str) -> bool:
    """Whether ``corpus_id`` has a structured binding -- the discriminator a caller uses to choose
    between the bound-membership path and the legacy whole-store path."""
    try:
        resolve_corpus_binding(registry, corpus_id)
    except CorpusNotBoundError:
        return False
    return True


# === membership: a bound corpus -> its eligible member datasets ====================================


def eligible_oos_members(
    registry: ExposureRegistry,
    dataset_store: DatasetStore,
    shard_ledger: "vault.VaultShardLedger",
    universe_ledger: "vault.VaultUniverseLedger",
    incident_ledger: "vault.VaultDisclosureIncidentLedger",
    plan_ledger: "vault.VaultReleasePlanLedger",
    *,
    corpus_id: str,
    vault_secret: bytes,
    records: list[dict] | None = None,
) -> dict:
    """**The precommitted eligible-member set of a bound OOS corpus** (r14.1, A + C).

    Derived from, and ONLY from: the bound universe's registered rule · the HMAC's not-selected
    status · the frozen release plan's ``releasable`` class · the permanent incident exclusions ·
    the deterministic reserved decoy · and the store's already-verified per-dataset metadata. Never
    from an observed outcome, never from what a fold happened to find, and never from a session-date
    match against the visible store.

    A dataset is a member iff ALL hold:
      * its own ``(symbol, ET session_date)`` is in the frozen plan's ``releasable`` class -- which
        by construction excludes every HMAC-SELECTED position, every incident-barred position and
        the reserved decoy;
      * its ``schema_basis`` is the recorder's own (a legacy dataset occupying a registered pair is
        a §7.2.2 collision, never a member);
      * its ``created_utc`` reaches the binding's ``freshness_boundary``;
      * it is not currently withheld by the vault (i.e. it has actually been released).

    Returns the members AND the class counts every one of the other positions falls into, because a
    fold that quietly evaluated a subset is exactly the failure this whole structure prevents. No
    events and no snapshot rows are read: the sealed members' ids never enter the returned manifest,
    so a downstream reader is structurally incapable of touching one."""
    binding = resolve_corpus_binding(registry, corpus_id)
    universe_id = binding["universe_id"]
    universe = vault.find_universe(universe_ledger, universe_id)
    if universe is None:
        raise CorpusMembershipError(
            f"corpus {corpus_id!r} is bound to universe {universe_id!r}, which is not registered "
            "-- refused: its membership cannot be resolved"
        )
    for field, recorded in (
        ("rule_commitment", universe["rule_commitment"]),
        ("vault_secret_commitment", universe["vault_secret_commitment"]),
        ("registered_at", universe["registered_at"]),
    ):
        bound_key = "universe_registered_at" if field == "registered_at" else field
        if binding.get(bound_key) != recorded:
            raise CorpusMembershipError(
                f"corpus {corpus_id!r} was bound to universe {universe_id!r} at "
                f"{bound_key}={binding.get(bound_key)!r}, but the universe ledger now records "
                f"{recorded!r} -- refused: the binding no longer describes this universe"
            )

    commitment = vault.find_release_plan_commitment(plan_ledger, universe_id)
    if commitment is None:
        raise CorpusMembershipError(
            f"universe {universe_id!r} has no committed release plan -- refused (r14.1): without a "
            "frozen plan, which members are releasable would depend on operator order"
        )
    plan = vault.build_release_plan(universe, incident_ledger, vault_secret)
    if plan["plan_hash"] != commitment["plan_hash"]:
        raise CorpusMembershipError(
            f"the release plan for universe {universe_id!r} recomputes to {plan['plan_hash']!r} "
            f"but {commitment['plan_hash']!r} was committed -- refused: the partition moved after "
            "it was frozen"
        )

    releasable = {tuple(p) for p in plan["releasable"]}
    if records is None:
        records, _errors = dataset_store.list()
    withheld = vault.unresolved_pool_universe_by_dataset_id(
        shard_ledger,
        universe_ledger,
        [
            (
                meta["id"],
                meta["symbol"],
                vault._et_session_date_of(meta["window_start_utc"]),
                meta.get("created_utc", ""),
            )
            for meta in records
        ],
    )

    boundary = binding["freshness_boundary"]
    members: list[dict] = []
    rejected = {
        "not_in_releasable_class": 0,
        "not_recorder_output": 0,
        "created_before_freshness_boundary": 0,
        "still_withheld": 0,
    }
    for meta in records:
        session_date = vault._et_session_date_of(meta["window_start_utc"])
        position = (vault._normalize_symbol(meta["symbol"]), session_date)
        if position not in releasable:
            continue  # a non-member: sealed, barred, decoy, another universe, or not a pool pair
        if meta.get("schema_basis") != vault.RECORDER_SCHEMA_BASIS:
            rejected["not_recorder_output"] += 1
            continue
        if meta.get("created_utc", "") < boundary:
            rejected["created_before_freshness_boundary"] += 1
            continue
        if meta["id"] in withheld:
            rejected["still_withheld"] += 1
            continue
        members.append(
            {
                "dataset_id": meta["id"],
                "checksum": meta["checksum"],
                "symbol": meta["symbol"],
                "session_date": session_date,
            }
        )
    members.sort(key=lambda m: (m["session_date"], m["symbol"], m["dataset_id"]))
    resolved_positions = {(vault._normalize_symbol(m["symbol"]), m["session_date"]) for m in members}
    rejected["not_in_releasable_class"] = len(releasable) - len(resolved_positions)

    return {
        "corpus_id": corpus_id,
        "universe_id": universe_id,
        "plan_hash": plan["plan_hash"],
        "members": members,
        "member_count": len(members),
        "session_dates": sorted({m["session_date"] for m in members}),
        "symbols": sorted({m["symbol"] for m in members}),
        "manifest_hash": corpus_manifest_hash(members),
        # The §7.5-safe disclosure: COUNTS of what this corpus deliberately does not contain, never
        # the identities. A reader can see that a date is mixed without learning which member is
        # which.
        "excluded": {
            "sealed_path_positions": len(plan["sealed_path"]),
            "incident_barred_positions": len(plan["barred"]),
            "reserved_decoy_positions": len(plan["reserved_decoy"]),
            "releasable_positions_without_a_resolved_dataset": rejected["not_in_releasable_class"],
            "rejected_not_recorder_output": rejected["not_recorder_output"],
            "rejected_created_before_boundary": rejected["created_before_freshness_boundary"],
            "rejected_still_withheld": rejected["still_withheld"],
        },
    }


def corpus_manifest_hash(members: list[dict]) -> str:
    """The corpus's SCIENTIFIC identity: a hash over the actual eligible ``(dataset_id, checksum)``
    membership, not over its list of dates (r14.1, C).

    r14 hashed the session dates alone, so two genuinely different bodies of evidence covering the
    same calendar produced the same ``corpus_manifest_hash`` -- and a member swapped for another at
    the same date left it unchanged. Hashing identity plus content means a changed member, a changed
    dataset, or a changed number of members all move the hash."""
    payload = sorted((m["dataset_id"], m["checksum"]) for m in members)
    return _sha256_hex(_canonical(payload))


def members_for_sessions(membership: dict, session_dates: list[str] | set[str]) -> list[dict]:
    """The bound corpus's members whose own session date is in ``session_dates`` -- the per-fold
    narrowing. A member is selected only if it is in BOTH the precommitted set and the requested
    window, so a fold can never reach outside either."""
    wanted = set(session_dates)
    return [m for m in membership["members"] if m["session_date"] in wanted]


def corpus_session_dates(membership: dict) -> list[str]:
    """The session dates this corpus actually has members on -- the fold-geometry input. A date
    whose every member turned out to be sealed contributes nothing and is honestly absent."""
    return list(membership["session_dates"])
