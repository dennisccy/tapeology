"""The Hypothesis Foundry -- the hash-chained, append-only Foundry trial ledger (spec §4.2.1/§9.2).
Built on ``micro_chain_ledger.HashChainedLedger`` (the SAME shared tamper-evident primitive
``micro_accessor.ExposureRegistry``/``walkforward_ledger.WalkForwardLedger`` already use -- see
that module's own docstring for why one shared primitive is right here rather than a fourth
hand-rolled hash chain).

**Why this ledger is its own file, never a row kind inside ``scout_ledger.py``.** Spec §4.2.1 is
explicit: "the Foundry does not call the Scout registration/ledger path for these trials, and the
Scout ledger receives no synthetic/non-§3 feature rows from this era." This module never imports
``scout_ledger``; every Foundry trial (intent or terminal) is recorded here and ONLY here."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .foundry_compiler import CandidateSpec
from .micro_chain_ledger import HashChainedLedger

__all__ = [
    "ROW_KIND_INTENT",
    "ROW_KIND_TERMINAL",
    "ROOT_DEFERRED_COMPOSITE",
    "ConflictingReplayRefused",
    "FoundryLedger",
    "deterministic_rule_id",
    "prospective_root_status",
]

_LEDGER_FILENAME = "foundry_trial_ledger.jsonl"

ROW_KIND_INTENT = "evaluation_intent"
ROW_KIND_TERMINAL = "terminal"

# §5.5: "otherwise record the literal `root_deferred_composite`... no composite root is invented
# in this era."
ROOT_DEFERRED_COMPOSITE = "root_deferred_composite"


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def deterministic_rule_id(epoch_id: str, candidate_spec_hash: str) -> str:
    """§8.2/§11: the deterministic, pre-outcome future Mode-B ``rule_id``. A pure string function
    of two already-frozen identities -- computable (and, per TC-19, IMMUTABLE) before any outcome
    is read."""
    return f"foundry:{epoch_id}:{candidate_spec_hash}"


def prospective_root_status(spec: CandidateSpec) -> str:
    """§5.5: "the current prospective root for scalar mechanisms where mechanically defined, else
    the literal `root_deferred_composite`". This era registers no real Scout `family_root_id`
    mapping (that is real-corpus/J-06+ territory), so the one MECHANICAL fact available pre-outcome
    is the CandidateSpec's own relation shape: a ``direct_scalar_membership`` candidate with
    exactly one coordinate has a one-to-one correspondence between its Foundry family and a single
    conditioning feature -- its own frozen ``foundry_family_id`` IS the mechanically-defined
    current prospective root candidate. Anything else (``conjunction``, or a future relation kind)
    has no such one-to-one mapping and always records the literal sentinel -- "no composite root is
    invented in this era" (§5.5), never a synthetic root id manufactured here."""
    if spec.relation.kind == "direct_scalar_membership" and len(spec.coordinates) == 1:
        return spec.foundry_family_id
    return ROOT_DEFERRED_COMPOSITE


class ConflictingReplayRefused(Exception):
    """§9.2: "conflicting candidate/hash/corpus/floor/screen attempt -> refuse" -- a terminal
    replay whose content differs from the already-recorded terminal row for the SAME
    ``candidate_spec_hash`` (TC-14)."""


# The terminal fields that decide "exact duplicate" (idempotent replay, TC-14) vs "conflicting"
# (refused) -- every field that pins a frozen identity or the screen's own verdict/payload.
_TERMINAL_IDENTITY_FIELDS = (
    "manifest_hash", "foundry_family_id", "foundry_family_variant_count", "screen_result",
    "rule_id", "prospective_root_status", "foundry_state",
)


class FoundryLedger:
    """One Foundry epoch's complete trial record -- intent rows (§6 step 4 / §9.2's
    ``EVALUATION_INTENT_RECORDED``) and terminal rows (§7.2's three terminal states) share ONE
    physical hash chain (the ``scout_ledger.py``/``walkforward_ledger.py`` "one global chain, not
    one per family/kind" precedent), discriminated by ``row_kind``."""

    def __init__(self, root_dir: str | Path) -> None:
        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)

    def all_rows(self) -> list[dict]:
        return self._chain.all_rows()

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def intent_row_for(self, candidate_spec_hash: str) -> dict | None:
        for row in reversed(self._chain.all_rows()):
            if row["row_kind"] == ROW_KIND_INTENT and row["candidate_spec_hash"] == candidate_spec_hash:
                return row
        return None

    def terminal_row_for(self, candidate_spec_hash: str) -> dict | None:
        for row in reversed(self._chain.all_rows()):
            if row["row_kind"] == ROW_KIND_TERMINAL and row["candidate_spec_hash"] == candidate_spec_hash:
                return row
        return None

    def record_intent(
        self, *, candidate_spec_hash: str, manifest_hash: str, econ_floor_bps: float | None,
        econ_floor_provenance: str, recorded_at: str | None = None,
    ) -> dict:
        """§6 step 4: the pre-outcome evaluation-intent row -- CandidateSpec hash, manifest hash,
        the materialized numeric economic floor + provenance, and a timestamp. Appended BEFORE any
        outcome is measured (the caller's own obligation; this method just persists whatever it is
        given)."""
        return self._chain.append_row(
            {
                "row_kind": ROW_KIND_INTENT,
                "candidate_spec_hash": candidate_spec_hash,
                "manifest_hash": manifest_hash,
                "econ_floor_bps": econ_floor_bps,
                "econ_floor_provenance": econ_floor_provenance,
                "recorded_at": recorded_at or _iso_utc_now(),
            }
        )

    def record_terminal(
        self, *, candidate_spec_hash: str, manifest_hash: str, foundry_family_id: str,
        foundry_family_variant_count: int, screen_result: dict, rule_id: str,
        prospective_root_status: str, foundry_state: str, recorded_at: str | None = None,
    ) -> dict:
        """§4.2.1/§7.2: the canonical Foundry trial record -- embeds the COMPLETE
        ``scout.screen_candidate`` result plus every frozen identity a future auditor needs, and
        is the ONLY row this trial is ever recorded on (never the Scout ledger). Exact-duplicate
        replay (every identity field byte-identical to the existing terminal row for this
        ``candidate_spec_hash``) is idempotent and returns the EXISTING row (TC-14); any
        difference -- a different screen payload, a different rule_id/root status/family identity
        -- raises ``ConflictingReplayRefused`` rather than silently overwriting."""
        candidate = {
            "row_kind": ROW_KIND_TERMINAL,
            "candidate_spec_hash": candidate_spec_hash,
            "manifest_hash": manifest_hash,
            "foundry_family_id": foundry_family_id,
            "foundry_family_variant_count": foundry_family_variant_count,
            "screen_result": screen_result,
            "rule_id": rule_id,
            "prospective_root_status": prospective_root_status,
            "foundry_state": foundry_state,
            "recorded_at": recorded_at or _iso_utc_now(),
        }
        existing = self.terminal_row_for(candidate_spec_hash)
        if existing is not None:
            if all(existing[f] == candidate[f] for f in _TERMINAL_IDENTITY_FIELDS):
                return existing
            raise ConflictingReplayRefused(
                f"terminal row for candidate_spec_hash={candidate_spec_hash!r} already exists with "
                "different content -- refused rather than overwritten (spec §9.2)"
            )
        return self._chain.append_row(candidate)
