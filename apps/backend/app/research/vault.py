"""``vault.py`` -- Era "The Rapid Microscope" J-06 step 3 (``docs/rapid-validation-spec.md``
section 7.2-7.5): pre-registered recording universes (rule-hash committed BEFORE any fetch), the
split/seal dual assignment (the opaque HMAC seal axis, NEW and independent of
``tick_recorder.recorder_split_for``'s own published split rule -- this module never reimplements
that rule; it only adds the seal axis), and the one-way ``sealed -> assigned -> exposed``
shard-lifecycle ledger keyed on the COMPUTED ``family_root_id`` (imported from
``scout_ledger.compute_family_root_id``, never reimplemented -- TR-20 depends on there being
exactly one identity function).

**Two distinct ledgers, per the phase spec's own naming (T-2 vocabulary trap).** ``VaultUniverseLedger``
(recording-universe registrations: ``{universe_id, symbol_rule, date_rule, registered_at,
rule_hash, vault_secret_commitment}``) and ``VaultShardLedger`` (the shard-lifecycle
``sealed -> assigned -> exposed`` transitions) are TWO separate ``micro_chain_ledger.
HashChainedLedger`` instances -- the ``walkforward_ledger.WalkForwardLedger`` "thin domain wrapper
over ONE HashChainedLedger" shape, built here TWICE (module docstring precedent: "once per
ledger"), never a fourth hash-chain implementation and never one ledger pretending to be two.
Neither of these is the WALKFORWARD ``ExposureRegistry`` (``micro_accessor.py``, section 6.7) --
that ledger tracks whether a (corpus, session-window) has ever been SERVED; this module's shard
ledger tracks whether a (family, shard) has ever been ASSIGNED/EXPOSED. The two interact (see
``currently_sealed_dataset_ids`` below, the bridge ``walkforward.py`` calls) but are never the same
file, the same identity key, or the same vocabulary.

**A vault "shard" IS a ``DatasetStore`` dataset -- but its SERVED identity is a surrogate (spec
section 7.5, revision r3).** The recorder (``tick_recorder.py``) finalizes exactly one dataset per
recorded symbol-day, and this module keys every ledger row and every lifecycle guard on that
dataset's own ``id`` (``dataset_id`` -- the SAME identity ``micro_readiness.py``'s per-shard
``dataset_id`` field and ``micro_accessor.MicroAccessor``'s ``sealed_dataset_ids: frozenset[str]``
parameter already use; no second shard-identity scheme is invented here). What is SERVED while the
shard is still sealed is NOT that id: it is ``shard_id``, a vault-minted surrogate
(``compute_surrogate_shard_id``) bearing no publicly derivable relation to the dataset id, whose
mapping back to the dataset id lives only in this module's own sealed-side ledger and is revealed
at ASSIGNMENT.

**Why the surrogate exists (iter-9 audit finding B1, closed by the owner's r3 ruling).** Serving the
raw dataset id (and the raw ``content_checksum``) pre-exposure defeated section 7.5's whole purpose
even though the served FIELD LIST was correct: either value joins in one hop to
``GET /research/datasets/{id}`` / ``GET /research/datasets`` / the ``datasets`` MCP tool /
``get_endpoint`` / ``micro_readiness``, each of which serves the shard's symbol, session date and
exact event counts -- precisely what section 7.5 withholds. Field-level minimization is therefore
not enough; JOIN RESISTANCE is the actual requirement (r3), and it is met here in three parts:

1. the surrogate ``shard_id`` above;
2. a SALTED commitment ``HMAC(vault_secret, content_checksum)`` (``commit_content_checksum``)
   instead of the raw checksum, which is itself served publicly per dataset and would join
   directly -- the raw checksum is revealed at EXPOSURE, at which point the salted commitment can
   be re-derived from it and verified, so auditability survives intact; and
3. a seal-aware REFUSAL on the pre-existing public surfaces, keyed on ``withheld_dataset_ids``
   below (``routes.py``'s dataset list/detail + backtest-creation routes, and
   ``micro_readiness.build_readiness``'s per-shard rows -- the MCP ``datasets`` tool and
   ``get_endpoint`` inherit it structurally, being byte-identical GET proxies of those same
   routes); and
4. a COMMITTED (not published) universe rule while any of that universe's shards is still
   withheld (``_serialize_universe``) -- iter-9 audit (third pass) finding B1. Parts 1-3 close
   every per-shard join, but the universe rule is the tranche's own COMPLEMENT: TR-4 requires the
   recorded batch to be exactly ``symbol_rule x date_rule`` net of disclosed failures, so
   publishing those two lists beside a ``GET /research/datasets`` that omits precisely the sealed
   rows lets any reader compute ``sealed = expected - served`` and de-anonymise the whole sealed
   tranche by set subtraction -- defeating section 7.3's stated guarantee that "sealed membership
   cannot be inferred from public information before exposure". So the rule lists follow the SAME
   commit-then-reveal discipline part 2 applies to ``content_checksum``: ``rule_hash`` (already
   computed at registration) is served throughout, the raw lists only once every shard of that
   universe has reached ``exposed``. Section 7.2's requirement is that the rule be RECORDED in the
   vault ledger before any fetch -- unchanged here, and ``find_universe``/the TR-4 verifier still
   read it verbatim from that ledger, so nothing about the batch check or its auditability moves.

TR-2 proves this by construction rather than by whitelist review (``tests/test_vault.py``'s
adversarial join-resistance sweep over every registered GET route).

**The single-shot discipline (TR-12) is shard-GLOBAL, not merely (family, shard)-scoped -- a
disclosed interpretation call (T-1).** Spec section 7.4 says assignment "binds ONE candidate
family LINE to the shard" -- read here as: once a shard leaves ``sealed``, it belongs to exactly
ONE family for the rest of its history; a second ``assign_shard``/``expose_shard`` call for that
shard is refused regardless of which ``family_root_id`` it names (``ShardLifecycleOrderError``).
This is the STRICTER of the two readings the sentence admits (the looser one would scope the
refusal to the exact (family_root_id, dataset_id) pair and allow a different, unrelated family to
claim the same shard while it is still merely ``assigned``) -- chosen because a shard's content is
no longer meaningfully "sealed" for a second family once a first family has been bound to it, and
because every scenario TC-1..TC-9 actually exercises passes identically under either reading (the
stricter rule can only refuse a superset of what the looser one would). Logged here rather than
silently assumed, per this module's own T-1 discipline; nothing about it can widen without a
plan-owner decision, since narrowing a refusal after real sealed evidence exists would not be safe
to reverse. The iter-9 audit reviewed this call (its observation O1) and sided with it; the owner
ruling is still open, so ``test_vault.py``'s ``test_audit_t1_...`` now PINS the stricter behaviour
(the audit's own finding T1) so it cannot regress silently while that ruling is pending.

**Expected recording set = the cartesian product of ``symbol_rule`` x ``date_rule`` (a second
disclosed interpretation call).** Spec section 7.2 calls both "explicit" (the panel list, the date
range/rule) and requires them FULLY RESOLVED before registration (the Tier-B resolution order,
section 7.2: the resolved list is frozen BEFORE ``register_universe`` is ever called) -- so by the
time this module ever sees them, both are already concrete ``list[str]``s, and "the rule's own
computed output" is unambiguously every (symbol, date) pair between them, the exact shape
``tick_recorder.plan_recorder_chunks(symbols, dates)`` already walks for real fetches (no second,
diverging notion of "the universe's expected batch").

**The vault secret never enters a row, a log line, or this module's own return values in raw
form.** ``load_vault_secret`` reads it once from the path named by ``TAPEOLOGY_VAULT_SECRET_FILE``
(a genuinely NEW env var -- no existing "_SECRET_FILE" precedent in this codebase) and returns raw
bytes to the CALLER only; ``register_universe`` accepts only a pre-computed
``vault_secret_commitment`` string (``commit_vault_secret``'s own output), and ``seal_shard`` --
the one other function that must hold the raw secret, since r3's surrogate and salted commitment
are both keyed on it -- consumes it ONLY as an argument to the two HMAC helpers and writes neither
it nor anything reversible to it into the row it appends. A missing or unreadable secret file is
``VaultSecretUnavailable`` -- typed, never a crash, never a fabricated default secret (TC-5).

**Storage -- no new ``Config`` field.** ``resolve_vault_dir`` mirrors ``scout_ledger.
resolve_scout_ledger_dir`` exactly: ``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a ``micro_vault``
SIBLING of the caller's own already-resolved dataset directory (the ``TAPEOLOGY_MICRO_*`` family,
goal.md Constraints).

**Iteration 11 -- the opaque research pool, closed structurally (spec section 7.5 point 7, r5).**
Parts 1-4 above close every JOIN a served field could open; point 7 closes something field-level
minimization cannot reach at all: "no served surface may present a complete identity-labelled
list of EITHER side while any pool member is unexposed", because the registered universe is
public BY CONSTRUCTION (section 7.2), so a complete list of the non-withheld side identifies the
withheld side by subtraction. The gap this closes is concrete, not hypothetical: a repo-wide grep
at authoring finds ZERO production call sites of ``seal_shard``/``assign_shard``/``expose_shard``
-- nothing today wires a real recording to this module's ledger the moment it finalizes. So the
narrower, ledger-row-only ``withheld_universe_by_dataset_id`` above is not wrong, merely
insufficient: the instant a real recording finalizes under a registered universe, it would be
fully identifiable in ``GET /research/datasets`` and in ``micro_readiness``'s per-shard ``shards``
list with zero code path standing in the way. ``unresolved_pool_universe_by_dataset_id`` below
closes this STRUCTURALLY rather than procedurally -- a universe-RULE-driven predicate, safe the
INSTANT ``register_universe`` runs, needing no additional recorder-to-vault wiring (see that
function's own docstring for the full reasoning, including the ``created_utc >= registered_at``
guard that keeps a later-registered universe from retroactively withholding a pre-existing
dataset). It is the ONE new choke point ``micro_snapshots.exclude_withheld``/
``withheld_dataset_ids_for_store`` (hence its 8 existing corpus-wide enumerator consumers) and
``micro_readiness.build_readiness`` both read -- never a second, divergent implementation of "is
this dataset withheld"."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from .micro_chain_ledger import HashChainedLedger
from .scout_ledger import compute_family_root_id

__all__ = [
    "VAULT_SEAL_HEX_BELOW",
    "SURROGATE_SHARD_ID_PREFIX",
    "STATE_SEALED",
    "STATE_ASSIGNED",
    "STATE_EXPOSED",
    "VaultUniverseNotRegisteredError",
    "VaultUniverseAlreadyRegisteredError",
    "CherryPickedBatchError",
    "VaultSecretUnavailable",
    "ShardLifecycleOrderError",
    "SealedShardWithheldError",
    "resolve_vault_dir",
    "shard_ledger_for_dataset_dir",
    "universe_ledger_for_dataset_dir",
    "VaultUniverseLedger",
    "VaultShardLedger",
    "compute_rule_hash",
    "register_universe",
    "find_universe",
    "expected_recording_pairs",
    "verify_recording_batch",
    "verify_universe_recording_batch",
    "load_vault_secret",
    "commit_vault_secret",
    "compute_seal",
    "compute_surrogate_shard_id",
    "commit_content_checksum",
    "seal_shard",
    "assign_shard",
    "expose_shard",
    "currently_sealed_dataset_ids",
    "withheld_dataset_ids",
    "withheld_universe_by_dataset_id",
    "unresolved_pool_universe_by_dataset_id",
    "unresolved_pool_dataset_ids",
    "build_vault_state",
    "compute_family_root_id",
    "RULE_DISCLOSURE_COMMITTED",
    "RULE_DISCLOSURE_REVEALED",
]

# docs/rapid-validation-spec.md section 1, transcribed verbatim -- NEVER a Config field (every
# rapid-microscope constant is a plain module constant embedded in the era's own parameters
# discipline; this module has no persisted "parameters" record of its own to embed it in, since
# nothing here is a research MEASUREMENT -- the seal decision is auditable directly from the
# committed secret hash instead).
VAULT_SEAL_HEX_BELOW = 4

# The served surrogate id's fixed prefix (spec section 7.5 r3). Deliberately NOT the 32-hex shape
# a `DatasetStore` id has, so a surrogate can never be mistaken for -- or accidentally passed as --
# a dataset id by a reader, a log line, or a future UI.
SURROGATE_SHARD_ID_PREFIX = "vshard-"

# Domain-separation labels for the two secret-keyed derivations below, so the surrogate id and the
# checksum commitment can never collide even if some caller ever fed the identical input string to
# both (the standard HMAC domain-separation discipline; each is versioned so a future scheme change
# is a distinguishable v2, never a silent redefinition).
_SURROGATE_LABEL = "vault-shard-surrogate-v1:"
_CHECKSUM_COMMITMENT_LABEL = "vault-checksum-commitment-v1:"

# The one-way lifecycle's three states (module docstring T-2: this module's OWN vocabulary,
# distinct from micro_readiness.py's EXPOSURE_STATE_EXPLORATORY/SPLIT_PROVENANCE_HAND_ASSIGNED).
STATE_SEALED = "sealed"
STATE_ASSIGNED = "assigned"
STATE_EXPOSED = "exposed"

# The universe rule's two serving stages (module docstring's join-resistance part 4). A DIFFERENT
# vocabulary from the shard lifecycle above on purpose: a universe has no lifecycle of its own --
# its rule's disclosure is a pure function of whether every shard it owns has reached `exposed`.
RULE_DISCLOSURE_COMMITTED = "committed"
RULE_DISCLOSURE_REVEALED = "revealed"

_VAULT_DIR_ENV = "TAPEOLOGY_MICRO_VAULT_DIR"
_VAULT_SECRET_FILE_ENV = "TAPEOLOGY_VAULT_SECRET_FILE"

_UNIVERSE_LEDGER_FILENAME = "vault_universe_ledger.jsonl"
_SHARD_LEDGER_FILENAME = "vault_shard_ledger.jsonl"

# Ledger-machinery keys ``HashChainedLedger.append_row`` itself manages -- stripped before a row's
# OWN content is carried forward into a later row (``assign_shard``/``expose_shard`` below), so a
# re-appended row is never confused with the raw ledger internals of the row it was built from.
_LEDGER_INTERNAL_KEYS = ("row_hash", "prev_hash", "row_index")

# The opaque, sealed-safe projection (spec section 7.5) -- the ONLY keys ever served for a shard
# still in `sealed` state (TC-6). Listed once here so `_serialize_shard` cannot silently drift from
# what `seal_shard` actually writes.
_OPAQUE_SHARD_KEYS = ("shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state")


class VaultUniverseNotRegisteredError(Exception):
    """TC-1: a recording batch was asked to validate against a ``universe_id`` with no registered
    rule -- refused, never a silent pass and never an invented default rule."""


class VaultUniverseAlreadyRegisteredError(Exception):
    """iter-9 audit fix B2: spec section 7.2 FREEZES a universe's rule at registration ("After
    universe registration: no Tier-B re-screen, no substitution because a symbol is inconvenient,
    no replacement from vendor availability or observed data"). A second registration of the SAME
    ``universe_id`` under a different rule (or a different secret commitment) is therefore refused
    -- without this, TR-4's cherry-pick refusal is fully evadable: re-register the inconvenient
    symbol out of ``symbol_rule`` and the exact batch that was just refused validates, because
    ``find_universe`` resolves to the LATEST row."""

    def __init__(self, universe_id: str, registered_rule_hash: str, attempted_rule_hash: str) -> None:
        self.universe_id = universe_id
        self.registered_rule_hash = registered_rule_hash
        self.attempted_rule_hash = attempted_rule_hash
        super().__init__(
            f"universe {universe_id!r} is already registered under rule_hash "
            f"{registered_rule_hash!r} -- a registered universe rule is frozen (spec section 7.2) "
            f"and can never be re-registered as {attempted_rule_hash!r}; record the shortfall as a "
            "DISCLOSED per-symbol failure in the batch report instead (TR-4)"
        )


class CherryPickedBatchError(Exception):
    """TR-4/TC-3: a recording batch's (symbol, date) set differs from its universe rule's own
    computed set net of disclosed failures -- refused, naming the specific missing/unexpected
    entries."""


class VaultSecretUnavailable(Exception):
    """TC-5: ``TAPEOLOGY_VAULT_SECRET_FILE`` is unset, or the path it names cannot be read, or is
    empty -- a typed configuration refusal, never a crash and never a fabricated default secret."""


class ShardLifecycleOrderError(Exception):
    """TR-12/TC-8: a shard-lifecycle transition was attempted out of the one-way
    ``sealed -> assigned -> exposed`` order -- either skipping a step or repeating one already
    recorded (single-shot, shard-global -- module docstring).

    Operator-side only: this message names the real ``dataset_id`` (the transitions are keyed on
    it), and no route in this codebase invokes a transition, so it never reaches a public payload.
    A future operator-facing seal/assign/expose route must NOT surface it verbatim to an
    unauthenticated caller -- use ``SealedShardWithheldError`` below for anything served."""

    def __init__(self, dataset_id: str, expected_state: str | None, actual_state: str | None) -> None:
        self.dataset_id = dataset_id
        self.expected_state = expected_state
        self.actual_state = actual_state
        super().__init__(
            f"shard {dataset_id!r} is not eligible for this transition: expected its latest "
            f"recorded state to be {expected_state!r}, found {actual_state!r} -- the one-way "
            "sealed -> assigned -> exposed lifecycle refuses any transition taken out of order "
            "or repeated for a shard already past it (TR-12)"
        )


class SealedShardWithheldError(Exception):
    """spec section 7.5 point 3 (r3): a public surface was asked for a dataset whose vault shard has
    not yet reached ``exposed``. The refusal states ONLY that the id is sealed -- never the symbol,
    the window, the counts, or even the universe (each of which would re-open the join this refusal
    exists to close). ``routes.py`` serves ``str(exc)`` as its HTTP 403 detail, so there is exactly
    ONE wording of this refusal in the codebase.

    The message does not echo the ``dataset_id`` either. Repeating an id the caller just supplied
    discloses nothing NEW -- but TR-2's sweep is written as an absolute ("this id appears in no
    response body of any route"), and a message that quotes it back would force that trap to carry
    a carve-out. An assertion with no exceptions is worth more than a marginally friendlier error,
    so the id stays available programmatically (``exc.dataset_id``) and out of the wire."""

    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(
            "this dataset is sealed in the validation vault -- its metadata is withheld until "
            "its exposure is recorded (spec section 7.5)"
        )


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module hashes -- the identical sorted-keys,
    no-whitespace shape every sibling ledger in this codebase hashes (``scout_ledger.py``,
    ``micro_chain_ledger.py``, ...)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def resolve_vault_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a ``micro_vault`` SIBLING of the caller's
    already-resolved dataset directory -- the ``resolve_scout_ledger_dir`` pattern verbatim."""
    override = os.environ.get(_VAULT_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_vault")


def shard_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultShardLedger":
    """The shard-lifecycle ledger for a caller that knows only its dataset directory -- the ONE
    resolver every non-vault consumer of this module's state shares (``routes.py``'s refusal
    dependency, ``micro_readiness.build_readiness``, ``walkforward.py``'s r2-seed sealed filter),
    so there can never be two vault locations answering "which shards are sealed" differently."""
    return VaultShardLedger(resolve_vault_dir(dataset_dir_resolved))


def universe_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultUniverseLedger":
    """The universe-registration ledger for a caller that knows only its dataset directory -- the
    ``shard_ledger_for_dataset_dir`` pattern verbatim, for the OTHER ledger (module docstring:
    "two separate ``HashChainedLedger`` instances"). Iteration 11's own
    ``unresolved_pool_universe_by_dataset_id`` is the one caller that needs BOTH resolvers
    together, so there can never be two vault locations answering "which universes are
    registered" differently."""
    return VaultUniverseLedger(resolve_vault_dir(dataset_dir_resolved))


# === the two ledgers (module docstring: "once per ledger") =========================================


class VaultUniverseLedger:
    """A thin domain wrapper over ONE ``HashChainedLedger`` -- every registered recording
    universe, in append order. Enforces no business rule of its own (the ``ScoutLedger``/
    ``WalkForwardLedger`` split); ``register_universe``/``find_universe`` below are the validated
    entry points every caller uses."""

    def __init__(self, root_dir: str) -> None:
        self._chain = HashChainedLedger(root_dir, _UNIVERSE_LEDGER_FILENAME)

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        return self._chain.all_rows()

    def append_row(self, fields: dict) -> dict:
        return self._chain.append_row(fields)


class VaultShardLedger:
    """A thin domain wrapper over ONE ``HashChainedLedger`` -- every shard-lifecycle transition
    (``sealed``/``assigned``/``exposed`` rows, one global chain, discriminated by each row's own
    ``exposure_state`` -- the ``WalkForwardLedger`` "one global chain, several row kinds"
    precedent). ``seal_shard``/``assign_shard``/``expose_shard`` below are the validated entry
    points every caller uses."""

    def __init__(self, root_dir: str) -> None:
        self._chain = HashChainedLedger(root_dir, _SHARD_LEDGER_FILENAME)

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        return self._chain.all_rows()

    def append_row(self, fields: dict) -> dict:
        return self._chain.append_row(fields)


# === universe registration (spec section 7.2) =======================================================


def compute_rule_hash(symbol_rule: list[str], date_rule: list[str]) -> str:
    """A pure content hash over the resolved, explicit ``symbol_rule``/``date_rule`` lists --
    excludes any wall-clock-derived value (``registered_at`` is never part of this), so two
    genuinely separate registration acts of the IDENTICAL rule compute the identical hash (the
    ``scout_ledger.compute_spec_hash`` precedent, TC-2)."""
    return _sha256_hex(_canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)}))


def register_universe(
    ledger: VaultUniverseLedger,
    *,
    universe_id: str,
    symbol_rule: list[str],
    date_rule: list[str],
    vault_secret_commitment: str,
    registered_at: str | None = None,
) -> dict:
    """Freezes a recording universe's rule (spec section 7.2): ``{universe_id, symbol_rule,
    date_rule, registered_at, rule_hash, vault_secret_commitment}``. ``vault_secret_commitment`` is
    ``commit_vault_secret``'s own output (``sha256(vault_secret).hexdigest()``) -- this function
    never sees, accepts, or persists the raw secret itself (module docstring; TC-5).

    **The freeze is ENFORCED, not merely documented (iter-9 audit fix B2).** Section 7.2's "no
    substitution because a symbol is inconvenient" is a rule about the universe_id's WHOLE history,
    not just its first row, so a second registration of the same ``universe_id`` is:

    * an idempotent no-op returning the EXISTING row (no second ledger row) when the rule and the
      secret commitment are byte-identical -- a crash-retry of the one operator registration act
      must not fork the universe's history (the era's own "idempotency everywhere, not everywhere
      except one path" lesson); and
    * ``VaultUniverseAlreadyRegisteredError`` otherwise -- because ``find_universe`` resolves to the
      LATEST row, an unrefused re-registration under a narrowed ``symbol_rule`` would silently
      redefine ``expected_recording_pairs`` and neutralize TR-4's cherry-pick refusal entirely."""
    rule_hash = compute_rule_hash(symbol_rule, date_rule)
    existing = find_universe(ledger, universe_id)
    if existing is not None:
        if (
            existing["rule_hash"] == rule_hash
            and existing["vault_secret_commitment"] == vault_secret_commitment
        ):
            return existing
        raise VaultUniverseAlreadyRegisteredError(universe_id, existing["rule_hash"], rule_hash)
    fields = {
        "universe_id": universe_id,
        "symbol_rule": list(symbol_rule),
        "date_rule": list(date_rule),
        "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
        "rule_hash": rule_hash,
        "vault_secret_commitment": vault_secret_commitment,
    }
    return ledger.append_row(fields)


def find_universe(ledger: VaultUniverseLedger, universe_id: str) -> dict | None:
    """The most recently registered universe row for ``universe_id``, or ``None`` -- append order
    IS registration order (the ``walkforward_ledger.latest_fold_spec`` precedent)."""
    matches = [row for row in ledger.all_rows() if row.get("universe_id") == universe_id]
    return matches[-1] if matches else None


def expected_recording_pairs(universe: dict) -> frozenset[tuple[str, str]]:
    """The universe rule's own computed (symbol, date) set -- the cartesian product of its
    resolved ``symbol_rule`` x ``date_rule`` (module docstring's second interpretation call)."""
    return frozenset((symbol, date) for symbol in universe["symbol_rule"] for date in universe["date_rule"])


def verify_recording_batch(
    universe: dict, *, recorded: list[tuple[str, str]], disclosed_failures: list[tuple[str, str]] = ()
) -> dict:
    """TR-4: refuses (``CherryPickedBatchError``, naming the specific gap) unless ``recorded``
    equals the universe rule's own computed set net of ``disclosed_failures`` -- exactly, in both
    directions (a batch missing an expected entry OR carrying an unexpected one is refused; TC-3
    exercises the missing-entry case, TC-4 the disclosed-failure success case)."""
    expected = expected_recording_pairs(universe) - set(disclosed_failures)
    got = set(recorded)
    missing = sorted(expected - got)
    unexpected = sorted(got - expected)
    if missing or unexpected:
        raise CherryPickedBatchError(
            f"recording batch for universe {universe['universe_id']!r} does not match its "
            f"registered rule net of disclosed failures (TR-4): missing={missing!r}, "
            f"unexpected={unexpected!r}"
        )
    return {"ok": True}


def verify_universe_recording_batch(
    ledger: VaultUniverseLedger,
    universe_id: str,
    *,
    recorded: list[tuple[str, str]],
    disclosed_failures: list[tuple[str, str]] = (),
) -> dict:
    """The ledger-aware entry point TC-1 exercises: looks up ``universe_id`` (``find_universe``)
    and raises ``VaultUniverseNotRegisteredError`` when it does not exist -- never validating a
    batch against a rule that was never committed -- else delegates to ``verify_recording_batch``."""
    universe = find_universe(ledger, universe_id)
    if universe is None:
        raise VaultUniverseNotRegisteredError(
            f"no universe registered for universe_id {universe_id!r} -- a recording batch can "
            "never be validated against a rule that does not exist"
        )
    return verify_recording_batch(universe, recorded=recorded, disclosed_failures=disclosed_failures)


# === the seal assignment (spec section 7.3) =========================================================


def load_vault_secret(path: str | None = None) -> bytes:
    """Reads the vault secret ONCE from ``path`` (or, when omitted, the path named by
    ``TAPEOLOGY_VAULT_SECRET_FILE``) -- trailing whitespace stripped, encoded as UTF-8 bytes.
    ``VaultSecretUnavailable`` (typed, never a crash, never a fabricated default) when the env var
    is unset, the path is unreadable, or the file is empty (TC-5, the recorder's own error-cases
    contract: "a missing or unreadable TAPEOLOGY_VAULT_SECRET_FILE ... is a typed configuration
    refusal, never a crash")."""
    resolved = path if path is not None else os.environ.get(_VAULT_SECRET_FILE_ENV)
    if not resolved:
        raise VaultSecretUnavailable(
            f"no vault secret file configured -- set {_VAULT_SECRET_FILE_ENV} to a readable file "
            "path outside the repo; refused rather than fabricating a default secret"
        )
    try:
        raw = Path(resolved).read_text(encoding="utf-8")
    except OSError as exc:
        raise VaultSecretUnavailable(
            f"vault secret file {resolved!r} (from {_VAULT_SECRET_FILE_ENV}) could not be read: {exc}"
        ) from exc
    secret = raw.strip()
    if not secret:
        raise VaultSecretUnavailable(f"vault secret file {resolved!r} is empty -- refused")
    return secret.encode("utf-8")


def commit_vault_secret(vault_secret: bytes) -> str:
    """``sha256(vault_secret)`` -- the ONLY form of the secret this module ever persists
    (``register_universe``'s ``vault_secret_commitment`` kwarg, module docstring)."""
    return hashlib.sha256(vault_secret).hexdigest()


def compute_seal(vault_secret: bytes, symbol: str, session_date: str) -> bool:
    """spec section 7.3: sealed iff the last hex digit of ``HMAC-SHA256(vault_secret,
    f"{symbol}:{session_date}")`` is strictly less than ``VAULT_SEAL_HEX_BELOW`` (=4, ~25% of a
    universe). Deterministic: the identical secret and (symbol, date) always compute the identical
    boolean (TC-5) -- never a wall-clock or unseeded random input."""
    digest = hmac.new(vault_secret, f"{symbol}:{session_date}".encode("utf-8"), hashlib.sha256).hexdigest()
    return int(digest[-1], 16) < VAULT_SEAL_HEX_BELOW


def compute_surrogate_shard_id(vault_secret: bytes, dataset_id: str) -> str:
    """spec section 7.5 point 1 (r3): the vault-minted, publicly opaque token served in place of the
    ``DatasetStore`` dataset id while a shard is sealed. ``SURROGATE_SHARD_ID_PREFIX`` +
    ``HMAC-SHA256(vault_secret, "vault-shard-surrogate-v1:" + dataset_id)``.

    Keyed on the SECRET, not merely hashed: a plain ``sha256(dataset_id)`` would be derivable by
    anyone -- every dataset id is (or was) public, so an attacker could hash each one and match. An
    HMAC under a secret that never leaves ``TAPEOLOGY_VAULT_SECRET_FILE`` is not derivable without
    that secret, while remaining DETERMINISTIC and re-derivable by the operator who holds it (the
    era's own "no unseeded randomness in any research artifact" anti-goal rules out a random token
    here; the seal decision in ``compute_seal`` above is keyed exactly the same way, and the
    universe row's ``vault_secret_commitment`` is what makes both auditable after reveal)."""
    digest = hmac.new(
        vault_secret, f"{_SURROGATE_LABEL}{dataset_id}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{SURROGATE_SHARD_ID_PREFIX}{digest}"


def commit_content_checksum(vault_secret: bytes, content_checksum: str) -> str:
    """spec section 7.5 point 2 (r3): the SALTED pre-exposure commitment,
    ``HMAC-SHA256(vault_secret, "vault-checksum-commitment-v1:" + content_checksum)``.

    The raw ``content_checksum`` is served publicly in every dataset manifest, so committing to it
    unsalted would hand out a perfect join key under the name "commitment". Salting keeps the
    commitment binding (the operator can re-derive it from the raw checksum the moment exposure
    reveals it -- ``expose_shard`` serves that raw checksum, and this function re-computed over it
    must reproduce the sealed row's commitment byte for byte) while making it useless as a lookup
    key beforehand."""
    return hmac.new(
        vault_secret, f"{_CHECKSUM_COMMITMENT_LABEL}{content_checksum}".encode("utf-8"), hashlib.sha256
    ).hexdigest()


# === the shard lifecycle (spec section 7.4-7.5) =====================================================


def _coarse_size_bucket(event_count: int) -> str:
    """Order-of-magnitude ONLY (spec section 7.5: "a coarse size bucket (order of magnitude,
    never an exact count)") -- never reversible to an exact count. ``event_count`` is accepted
    only as an ARGUMENT to this function; no caller in this module ever stores the raw count in a
    ledger row (``seal_shard`` below computes this bucket and discards the input)."""
    if event_count <= 0:
        return "~0"
    return f"~10^{math.floor(math.log10(event_count))}"


def _row_content(row: dict) -> dict:
    """``row`` minus the ``HashChainedLedger``-managed keys -- the projection carried forward when
    one transition's row is built from the PRIOR row for the same shard (module docstring's
    ``_LEDGER_INTERNAL_KEYS``)."""
    return {k: v for k, v in row.items() if k not in _LEDGER_INTERNAL_KEYS}


def _latest_rows_by_dataset_id(ledger: VaultShardLedger) -> dict[str, dict]:
    """Every shard's own single most-recently-appended row, keyed on its ``dataset_id`` -- append
    order is chronological order, so the last row for a dataset is its current state (the
    ``walkforward_ledger.latest_fold_spec`` precedent, applied per-shard). ONE scan, shared by
    every reader below, so "what state is this shard in" is answered in exactly one place.

    Keyed on ``dataset_id``, never on the served surrogate ``shard_id``: the surrogate exists only
    to be handed out (spec section 7.5 r3), while every lifecycle guard, every bridge to another
    module, and every refusal is about the real dataset."""
    latest: dict[str, dict] = {}
    for row in ledger.all_rows():
        latest[row["dataset_id"]] = row
    return latest


def _latest_shard_row(ledger: VaultShardLedger, dataset_id: str) -> dict | None:
    return _latest_rows_by_dataset_id(ledger).get(dataset_id)


def seal_shard(
    ledger: VaultShardLedger,
    *,
    dataset_id: str,
    universe_id: str,
    content_checksum: str,
    event_count: int,
    vault_secret: bytes,
    sealed_at: str | None = None,
) -> dict:
    """The FIRST row a shard may ever carry (refused otherwise -- a shard already in the ledger
    cannot be re-sealed). Opaque by construction, in the r3 sense of "opaque":

    * the SERVED ``shard_id`` is the surrogate (``compute_surrogate_shard_id``), never the
      ``dataset_id`` -- which is recorded in the row's sealed side and withheld until assignment;
    * the SERVED ``checksum_commitment`` is salted (``commit_content_checksum``), never the raw
      ``content_checksum`` -- which is likewise recorded and withheld until exposure;
    * no ``family_root_id``/``symbol``/``session_date`` exists yet at all (nulled explicitly, for a
      uniform row schema across all three states); and
    * ``event_count`` is consumed ONLY to derive the coarse order-of-magnitude bucket -- the exact
      count itself is never stored in the row, so it cannot leak even from the ledger file (TC-6).

    ``vault_secret`` is used exclusively as the key of the two HMACs above and is never written,
    returned, or logged (module docstring, TC-5). An EMPTY (or whitespace-only) secret is refused
    here with the same typed ``VaultSecretUnavailable`` ``load_vault_secret`` raises (iter-9 audit
    finding B7): both HMAC keys would then be publicly derivable by anyone who can guess a dataset
    id, silently voiding r3's entire join-resistance guarantee at the one moment it is supposed to
    take effect. Checked at the door rather than trusted from the caller, because ``seal_shard``
    takes raw bytes and a future operator act could hand it something other than
    ``load_vault_secret``'s already-validated return."""
    if not vault_secret.strip():
        raise VaultSecretUnavailable(
            "seal_shard was handed an empty vault secret -- refused (spec section 7.5 r3): an "
            "empty HMAC key makes both the surrogate shard id and the salted checksum commitment "
            "publicly derivable, so sealing under it would record an opaque-looking row that is "
            "not actually opaque"
        )
    existing = _latest_shard_row(ledger, dataset_id)
    if existing is not None:
        raise ShardLifecycleOrderError(dataset_id, None, existing["exposure_state"])
    fields = {
        # --- sealed-side identity: recorded, never served while sealed -----------------------
        "dataset_id": dataset_id,
        "content_checksum": content_checksum,
        # --- the section 7.5 opaque projection: the ONLY keys served while sealed ------------
        "shard_id": compute_surrogate_shard_id(vault_secret, dataset_id),
        "universe_id": universe_id,
        "checksum_commitment": commit_content_checksum(vault_secret, content_checksum),
        "size_bucket": _coarse_size_bucket(event_count),
        "sealed_at": sealed_at if sealed_at is not None else _iso_utc_now(),
        "exposure_state": STATE_SEALED,
        # --- revealed later, by the transitions below ----------------------------------------
        "family_root_id": None,
        "symbol": None,
        "session_date": None,
        "assigned_at": None,
        "exposed_at": None,
    }
    return ledger.append_row(fields)


def assign_shard(
    ledger: VaultShardLedger,
    *,
    dataset_id: str,
    family_root_id: str,
    symbol: str,
    session_date: str,
    assigned_at: str | None = None,
) -> dict:
    """``sealed -> assigned`` (spec section 7.4): binds ``family_root_id`` to the shard and reveals
    ``symbol``/``session_date`` -- and, per r3, the surrogate -> ``dataset_id`` mapping -- for the
    first time (TC-7). Refused (``ShardLifecycleOrderError``, TR-12) unless the shard's own latest
    row is currently ``sealed`` -- covers BOTH "never sealed" and "already assigned/exposed"
    (module docstring's shard-global single-shot reading, TC-8)."""
    latest = _latest_shard_row(ledger, dataset_id)
    actual_state = latest["exposure_state"] if latest is not None else None
    if actual_state != STATE_SEALED:
        raise ShardLifecycleOrderError(dataset_id, STATE_SEALED, actual_state)
    fields = {
        **_row_content(latest),
        "exposure_state": STATE_ASSIGNED,
        "family_root_id": family_root_id,
        "symbol": symbol,
        "session_date": session_date,
        "assigned_at": assigned_at if assigned_at is not None else _iso_utc_now(),
        "exposed_at": None,
    }
    return ledger.append_row(fields)


def expose_shard(
    ledger: VaultShardLedger, *, dataset_id: str, family_root_id: str, exposed_at: str | None = None
) -> dict:
    """``assigned -> exposed`` (spec section 7.4): the shard's underlying event data/aggregates
    become servable beyond section 7.5's opaque projection from this point on -- including the raw
    ``content_checksum``, which the served entry reveals here so the sealed row's salted
    ``checksum_commitment`` can be re-derived from it and verified (r3 point 2). Refused
    (``ShardLifecycleOrderError``, TR-12) unless the shard's own latest row is currently
    ``assigned`` for THIS ``family_root_id`` -- covers "never assigned", "already exposed", and
    "assigned to a different family" alike."""
    latest = _latest_shard_row(ledger, dataset_id)
    actual_state = latest["exposure_state"] if latest is not None else None
    if actual_state != STATE_ASSIGNED or latest.get("family_root_id") != family_root_id:
        raise ShardLifecycleOrderError(dataset_id, STATE_ASSIGNED, actual_state)
    fields = {
        **_row_content(latest),
        "exposure_state": STATE_EXPOSED,
        "exposed_at": exposed_at if exposed_at is not None else _iso_utc_now(),
    }
    return ledger.append_row(fields)


def currently_sealed_dataset_ids(ledger: VaultShardLedger) -> frozenset[str]:
    """Every dataset id whose latest recorded row is still ``sealed`` -- the WALKFORWARD
    exposure-registry sealed filter's OWN read of this module's state (``walkforward.py``'s r2
    seed call site; module docstring T-2: this is the bridge, never a merge of the two ledgers).

    Strictly ``sealed``: an ASSIGNED shard's window is legitimately seedable by the walkforward
    registry, because assignment is itself the recorded act of binding it to a family. For the
    SERVING refusal (a stricter, later boundary) see ``withheld_dataset_ids`` below."""
    return frozenset(
        dataset_id
        for dataset_id, row in _latest_rows_by_dataset_id(ledger).items()
        if row["exposure_state"] == STATE_SEALED
    )


def withheld_universe_by_dataset_id(ledger: VaultShardLedger) -> dict[str, str]:
    """Every dataset id whose shard has NOT yet reached ``exposed``, mapped to its ``universe_id``
    -- the serving-refusal predicate of spec section 7.5 point 3 ("REFUSE a sealed dataset id ...
    **until its exposure is recorded**") and the grouping key of point 4's sealed-tranche
    aggregates.

    Deliberately a SUPERSET of ``currently_sealed_dataset_ids``: assignment reveals the shard's
    symbol, session date and dataset id (section 7.5), but "exact event counts, bytes, and any
    feature/outcome aggregate are withheld until EXPOSURE" -- and the public dataset manifest
    carries exactly those counts, so the manifest stays refused across ``sealed`` AND ``assigned``
    alike. The two predicates are kept as separate named functions rather than one, because they
    answer two genuinely different questions for two different modules (T-2 vocabulary
    discipline)."""
    return {
        dataset_id: row["universe_id"]
        for dataset_id, row in _latest_rows_by_dataset_id(ledger).items()
        if row["exposure_state"] != STATE_EXPOSED
    }


def withheld_dataset_ids(ledger: VaultShardLedger) -> frozenset[str]:
    """``withheld_universe_by_dataset_id``'s key set -- the membership test ``routes.py`` and
    ``micro_readiness.py`` use (never a second scan of the ledger with its own drifting rule)."""
    return frozenset(withheld_universe_by_dataset_id(ledger))


# === iteration 11: the opaque-pool predicate (spec section 7.5 point 7, r5) =========================
#
# Module docstring's own "Iteration 11" paragraph has the full motivation. Short version: the two
# functions above answer "does this dataset already carry an explicit vault shard-ledger row short
# of exposed" -- correct, but not the whole question, because nothing in this codebase's
# PRODUCTION code path ever calls seal_shard/assign_shard/expose_shard today (verified by grep at
# authoring). The functions below answer the actual question -- "is this dataset part of an
# unresolved registered-universe pool" -- by ALSO reading the registered universe RULE itself,
# which is safe the instant a universe is registered, independent of whether anything ever seals
# its members explicitly.


def _latest_universes(universe_ledger: VaultUniverseLedger) -> list[dict]:
    """Every currently-registered universe's own latest row (``find_universe``'s "most recent row
    per ``universe_id``" semantics, applied across EVERY ``universe_id`` at once rather than one
    named universe) -- the one ledger scan ``_universe_pair_index`` below needs."""
    latest: dict[str, dict] = {}
    for row in universe_ledger.all_rows():
        latest[row["universe_id"]] = row
    return list(latest.values())


def _universe_pair_index(universe_ledger: VaultUniverseLedger) -> dict[tuple[str, str], list[dict]]:
    """Every registered universe's own ``expected_recording_pairs()``, indexed by each
    ``(symbol, date)`` pair it covers -- built ONCE per call so a wide ``symbol_rule x date_rule``
    product is walked once per universe, never once per caller record (``unresolved_pool_
    universe_by_dataset_id`` below does an O(1) dict lookup per record against this index)."""
    index: dict[tuple[str, str], list[dict]] = {}
    for universe in _latest_universes(universe_ledger):
        for pair in expected_recording_pairs(universe):
            index.setdefault(pair, []).append(universe)
    return index


def unresolved_pool_universe_by_dataset_id(
    shard_ledger: VaultShardLedger,
    universe_ledger: VaultUniverseLedger,
    records: list[tuple[str, str, str, str]],
) -> dict[str, str]:
    """The SINGLE shared "is this dataset part of an unresolved registered-universe pool"
    predicate (spec section 7.5 point 7, r5 -- module docstring's "Iteration 11" paragraph has the
    full motivation), mapped to the responsible ``universe_id``. Consumed via
    ``micro_snapshots.exclude_withheld``/``withheld_dataset_ids_for_store`` (hence its 8 existing
    corpus-wide enumerator consumers) and directly by ``micro_readiness.build_readiness`` -- never
    a second, divergent implementation of "is this withheld" anywhere in this codebase.

    A dataset id is caught by the UNION of two independent tests, never a tie-breaker between
    them:

    (a) today's ledger-row check (``withheld_universe_by_dataset_id`` above, byte-UNCHANGED): the
        dataset already carries an explicit vault shard-ledger row whose latest state is short of
        ``exposed``.
    (b) NEW -- a universe-RULE membership check, but ONLY for a dataset that carries NO vault
        shard-ledger row AT ALL (any state -- see the ``ledger_tracked_ids`` guard below): the
        dataset's own ``(symbol, session_date)`` matches some registered universe's
        ``expected_recording_pairs()``, AND the dataset's own ``created_utc`` is at or after THAT
        universe's ``registered_at``.

    **The ``ledger_tracked_ids`` guard is load-bearing, not an optimization.** A universe's rule
    (``symbol_rule``/``date_rule``) never changes after a shard reaches ``exposed`` -- so without
    this guard, test (b) would keep matching a shard's (symbol, session_date) FOREVER, silently
    re-withholding a shard the operator legitimately exposed through the normal
    ``assign_shard``/``expose_shard`` path (caught by this function's own TC-3/TC-10 tests during
    development: an exposed shard has no row in (a)'s result set, since (a) only lists rows SHORT
    of exposed, so a naive "not already withheld by (a)" check alone let (b) re-catch it). The
    fix: test (b) only ever applies to a dataset the shard ledger has NEVER recorded a row for --
    once ANY row exists (sealed, assigned, OR exposed), the ledger's own answer is authoritative
    and test (b) never overrides it in either direction.

    ``created_utc >= registered_at`` is the guard that stops a universe registered LATER from
    retroactively withholding a dataset that already existed when it was registered -- including
    one of the 12 permanently-exploratory legacy symbol-days that happens to share a (symbol,
    date) with a brand-new rule (goal.md's own critical anti-goal: "The 12 pre-existing tick
    symbol-days are permanently exploratory -- never sealed ... never relabeled"). A dataset
    recorded before a universe existed cannot possibly be one of THAT universe's own recording
    outputs, so it is never a candidate for (b) regardless of a coincidental (symbol, date) match.
    Both timestamps are ``datetime.isoformat(timespec="microseconds")`` strings (``datasets.
    _iso_utc``/this module's own ``_iso_utc_now``) -- fixed-width and lexicographically
    comparable, so the plain string comparison is exact, never an approximation.

    Store-agnostic (module docstring: this module never imports ``DatasetStore``): ``records`` is
    the caller's own ``(dataset_id, symbol, session_date, created_utc)`` 4-tuples -- every caller
    already walks its own store and already holds these four already-verified manifest fields per
    record, so no event read is ever implied by calling this function.

    When a dataset id is caught by BOTH tests, or matches (b) against more than one universe, the
    returned ``universe_id`` prefers (a)'s ledger-recorded answer (the authoritative, already-
    assigned truth) and otherwise the first (b) match found -- every caller uses this only for
    AGGREGATE per-universe counting (``micro_readiness.py``'s ``sealed_tranche.by_universe``),
    never as a per-shard identity, so which universe wins a rare double-match is not itself an
    identity leak."""
    result: dict[str, str] = dict(withheld_universe_by_dataset_id(shard_ledger))
    pair_index = _universe_pair_index(universe_ledger)
    if pair_index:
        # Every dataset id the ledger has EVER recorded a row for, in ANY state -- including
        # `exposed`, which `withheld_universe_by_dataset_id` (hence `result` above) deliberately
        # excludes. Needed so test (b) below never re-catches a shard the operator legitimately
        # exposed (see this function's own docstring).
        ledger_tracked_ids = frozenset(_latest_rows_by_dataset_id(shard_ledger))
        for dataset_id, symbol, session_date, created_utc in records:
            if dataset_id in result or dataset_id in ledger_tracked_ids:
                continue
            for universe in pair_index.get((symbol, session_date), ()):
                if created_utc >= universe["registered_at"]:
                    result[dataset_id] = universe["universe_id"]
                    break
    return result


def unresolved_pool_dataset_ids(
    shard_ledger: VaultShardLedger,
    universe_ledger: VaultUniverseLedger,
    records: list[tuple[str, str, str, str]],
) -> frozenset[str]:
    """``unresolved_pool_universe_by_dataset_id``'s key set -- the ``withheld_dataset_ids`` shape,
    widened to the same universe-rule membership test (spec section 7.5 point 7, r5)."""
    return frozenset(unresolved_pool_universe_by_dataset_id(shard_ledger, universe_ledger, records))


# === GET /research/desk/micro/vault (served verbatim, no second computation in the route) ==========


def _serialize_shard(row: dict) -> dict:
    """Section 7.5's three-stage reveal, as an explicit whitelist per stage -- never ``dict(row)``,
    so neither a ledger-internal key (``row_hash``/``prev_hash``/``row_index``) nor a sealed-side
    key (``dataset_id``/``content_checksum``) can leak into a served entry by accident:

    * ``sealed``   -- ONLY the opaque projection (surrogate id, universe, coarse bucket, SALTED
      commitment, ``sealed_at``, state). TC-6/TR-2.
    * ``assigned`` -- the opaque fields PLUS the family binding, the symbol, the session date and
      the surrogate -> ``dataset_id`` mapping (r3 point 1: revealed at assignment). TC-7.
    * ``exposed``  -- the above PLUS the raw ``content_checksum``, against which the salted
      commitment can now be re-derived and verified (r3 point 2)."""
    opaque = {key: row[key] for key in _OPAQUE_SHARD_KEYS}
    state = row["exposure_state"]
    if state == STATE_SEALED:
        return opaque
    revealed = {
        **opaque,
        "dataset_id": row["dataset_id"],
        "family_root_id": row["family_root_id"],
        "symbol": row["symbol"],
        "session_date": row["session_date"],
        "assigned_at": row["assigned_at"],
        "exposed_at": row["exposed_at"],
    }
    if state == STATE_EXPOSED:
        revealed["content_checksum"] = row["content_checksum"]
    return revealed


def _fully_exposed_universe_ids(latest_shard_rows: dict[str, dict]) -> frozenset[str]:
    """Every ``universe_id`` that (a) owns at least one shard and (b) has NO shard left in a state
    short of ``exposed``. Fail-closed by construction: a universe with no shards yet -- registered
    but not recorded, the window between spec section 7.2's step 5 and step 7 -- is absent from
    this set, so its rule stays committed rather than published while the tranche is being built.
    """
    owning: set[str] = set()
    withholding: set[str] = set()
    for row in latest_shard_rows.values():
        owning.add(row["universe_id"])
        if row["exposure_state"] != STATE_EXPOSED:
            withholding.add(row["universe_id"])
    return frozenset(owning - withholding)


def _serialize_universe(row: dict, revealed_universe_ids: frozenset[str]) -> dict:
    """A universe row's served projection -- the module docstring's join-resistance part 4.

    While ANY shard of this universe is still withheld, the ``symbol_rule``/``date_rule`` LISTS are
    replaced by their already-stored ``rule_hash`` commitment plus their two sizes: the sizes state
    the tranche's shape (how much evidence was pre-committed, which is the auditable claim section
    7.2 exists to fix in advance) while revealing nothing about WHICH symbol-days it contains, so
    ``expected - served`` cannot be computed against the public dataset listing. ``rule_disclosure``
    names which of the two stages a reader is looking at, so a committed row can never be mistaken
    for a universe that genuinely has no members."""
    content = _row_content(row)
    if content["universe_id"] in revealed_universe_ids:
        return {**content, "rule_disclosure": RULE_DISCLOSURE_REVEALED}
    return {
        "universe_id": content["universe_id"],
        "registered_at": content["registered_at"],
        "rule_hash": content["rule_hash"],
        "vault_secret_commitment": content["vault_secret_commitment"],
        "symbol_rule_size": len(content["symbol_rule"]),
        "date_rule_size": len(content["date_rule"]),
        "rule_disclosure": RULE_DISCLOSURE_COMMITTED,
    }


def build_vault_state(shard_ledger: VaultShardLedger, universe_ledger: VaultUniverseLedger) -> dict:
    """The whole ``GET /research/desk/micro/vault`` body: every CURRENT shard state (one entry per
    shard, its own latest row, projected by ``_serialize_shard``'s per-stage whitelist), every
    registered universe (never the raw secret -- only its commitment), and both ledgers' own
    ``verify_chain()`` verdicts (the ``GET /scout``/``GET /walkforward`` precedent: surfaced beside
    the data, never silently accepted if tampered).

    The universe rows go through ``_serialize_universe``'s own two-stage reveal. An earlier version
    of this function served them in FULL, reasoning that "knowing a tranche covers S symbols x D
    dates says nothing about WHICH of those symbol-days the secret-keyed HMAC sealed". That
    reasoning was wrong, and the iter-9 audit (third pass, finding B1) reproduced why: it is true of
    the rule in isolation and false the moment the rule is read beside ``GET /research/datasets``,
    which serves every recorded shard EXCEPT the withheld ones. Since TR-4 forces the recorded batch
    to be the rule's complete output, ``expected - served`` is exactly the sealed set -- a full
    de-anonymisation from two public GETs. The rule is therefore committed (``rule_hash``, plus its
    two sizes) until every shard of that universe is exposed. Section 7.2 is unaffected: it requires
    the rule to be RECORDED in the vault ledger before any fetch, which it still is, and the TR-4
    verifier reads it from that ledger, not from this payload."""
    latest_shard_rows = _latest_rows_by_dataset_id(shard_ledger)
    revealed = _fully_exposed_universe_ids(latest_shard_rows)
    return {
        "universes": [_serialize_universe(row, revealed) for row in universe_ledger.all_rows()],
        "shards": [_serialize_shard(row) for row in latest_shard_rows.values()],
        "shard_ledger_chain_verification": shard_ledger.verify_chain(),
        "universe_ledger_chain_verification": universe_ledger.verify_chain(),
    }
