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
rule_hash, commitment_nonce, rule_commitment, vault_secret_commitment}`` -- the last three fields'
own two-stage SERVING discipline is the "Iteration 12" paragraph below) and ``VaultShardLedger`` (the
shard-lifecycle
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
   commit-then-reveal discipline part 2 applies to ``content_checksum``: a commitment is served
   throughout, the raw lists only once every shard of that universe has reached ``exposed``.
   [**Iteration 12 update, r7/TR-27:** that served commitment is NOT ``rule_hash`` -- a bare
   deterministic hash of a low-entropy, dictionary-enumerable rule is not a hiding commitment.
   ``rule_hash`` stays purely internal (``register_universe``'s own freeze/idempotency check,
   never served); ``_serialize_universe`` serves the NONCED ``rule_commitment`` instead. See the
   "Iteration 12" paragraph below for the full reasoning.] Section 7.2's requirement is that the
   rule be RECORDED in the vault ledger before any fetch -- unchanged here, and ``find_universe``/
   the TR-4 verifier still read it verbatim from that ledger, so nothing about the batch check or
   its auditability moves.

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
this dataset withheld".

**Iteration 12 -- three closures, per ``docs/rapid-validation-spec.md`` r6/r7 (owner rulings
2026-08-18/19).**

1. **TR-25, vault-ledger integrity (spec section 7.8).** Every normal reader of either ledger now
   goes through a GATED read -- ``VaultShardLedger.verified_rows()``/``VaultUniverseLedger.
   verified_rows()`` -- which calls ``verify_chain()`` FIRST and raises ``VaultLedgerCorruptionError``
   on any failure, never returning a result computed over a tampered or truncated chain. This is
   wired in at the LOWEST shared choke points (``_latest_rows_by_dataset_id``, ``_latest_universes``,
   ``find_universe``), so every one of this module's own public predicates and mutators
   (``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``, ``currently_sealed_dataset_ids``,
   ``withheld_dataset_ids``, ``register_universe``, ``verify_universe_recording_batch``,
   ``seal_shard``/``assign_shard``/``expose_shard`` via their own ``_latest_shard_row`` read)
   inherits the gate automatically -- and so does every OTHER module that calls into this one
   (``walkforward.py``'s direct ``currently_sealed_dataset_ids`` call, ``routes.py``'s
   ``get_withheld_dataset_ids`` dependency) with ZERO changes to those files, exactly the
   "single choke point, never a second divergent implementation" discipline this module already
   follows for the withhold predicate itself. ``main.py`` registers ONE global FastAPI exception
   handler for ``VaultLedgerCorruptionError`` (the ``RealDataError`` precedent), so every route
   this exception can reach -- not merely this module's own ``GET /vault``/``GET /readiness`` --
   gets a non-500 refusal, without needing a route-by-route try/except audit. Lawful recovery
   (``recover_shard_ledger`` below) is the ONLY way back; there is no warn-and-continue path
   anywhere in this module.

   *Disclosed interpretation call (T-1), matching this module's own established convention of
   logging rather than silently assuming a scope boundary.* The phase spec's own text asks the
   shard mutators to check "both ledgers". This module implements that literally for the two
   functions that already take both ledgers as parameters end to end
   (``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``) and transitively for
   ``register_universe``/``find_universe``/``verify_universe_recording_batch`` (all of which read
   the universe ledger through the same gated ``verified_rows()``). ``seal_shard``/``assign_shard``/
   ``expose_shard`` are gated on their OWN (shard) ledger only, NOT additionally threaded with a
   required ``universe_ledger`` parameter. Grounds: a repo-wide grep at authoring (unchanged from
   iteration 11) still finds ZERO production call sites of these three functions -- everything that
   calls them today is a test -- so widening their signature buys no real-world safety today, while
   it would force a mechanical, high-blast-radius migration of roughly 90 call sites across TEN test
   files (``test_vault.py`` alone has 42) that have nothing to do with ledger integrity, for a
   currently-unreachable production risk. TC-2's own literal text ("no sealing, no assignment") is
   satisfied by gating the SHARD ledger, the one these transitions actually read and write; a test
   pins exactly that. When J-06 step 4 eventually wires real ``seal_shard``/``assign_shard``/
   ``expose_shard`` calls into production, that wiring is the natural point to revisit whether the
   universe ledger should also gate these specific transitions -- logged here so the boundary is
   never silently assumed, exactly this module's own T-1 discipline elsewhere (see the single-shot
   discipline paragraph above).

2. **TR-27, nonced rule commitment (spec section 7.2/7.5, r7).** ``register_universe`` now mints a
   high-entropy ``commitment_nonce`` (``secrets.token_hex(32)``) at registration and computes
   ``rule_commitment = sha256(nonce + canonical_rule)`` (``compute_rule_commitment``) -- served in
   place of the plain ``rule_hash`` at every disclosure stage. ``rule_hash``/``compute_rule_hash``
   themselves are UNCHANGED and stay exactly what they were: the ledger's own internal,
   never-served freeze/idempotency identity function for ``register_universe``'s re-registration
   check (spec r7's own text: "rule_hash/compute_rule_hash stays as the ledger's own internal
   identity function"). The reveal gate widens in the SAME diff, per the session's own hard-won
   lesson ("never widen one side of a paired mechanism and leave its twin narrow"):
   ``_fully_exposed_universe_ids`` (ledger-tracked-only, the iteration-11 audit's own two-GET
   subtraction target, ``vault.py:926-938`` pre-iteration-12) is REPLACED by
   ``_whole_pool_released_universe_ids``, which reuses ``expected_recording_pairs`` -- the SAME
   expected-pairs computation ``unresolved_pool_universe_by_dataset_id`` already uses -- as the ONE
   "whole ORIGINAL pool released" predicate. ``symbol_rule``/``date_rule``/``commitment_nonce`` serve
   ONLY once (a) no ledger-tracked shard of that universe is short of ``exposed`` AND (b) every
   expected pair has an ``exposed`` shard -- a universe with any ledger-tracked OR
   untracked-but-rule-matching pair still short of ``exposed`` stays at the committed
   (``rule_commitment``-only) stage. **Part (a) is not redundant with (b):** an adversarial
   pre-ship review found that (b) ALONE is keyed on the ``(symbol, session_date)`` pair, not on
   shard identity, so a SECOND, different ``dataset_id`` sealed+assigned under the SAME pair as an
   already-exposed first shard (a re-recorded/retry day, spec section 7.7) would satisfy (b) while
   genuinely still withheld -- reopening the exact two-GET subtraction class this widening exists
   to close. See that function's own docstring and
   ``test_two_shards_sharing_one_pair_keep_the_universe_hidden_even_after_one_is_exposed``.

3. **The symbol/date withhold-match normalization (the third cheap companion item).** The
   universe-rule membership test inside ``unresolved_pool_universe_by_dataset_id`` (test (b) in that
   function's own docstring) now compares symbols case-insensitively (``_normalize_symbol``) on
   BOTH the registered rule's own ``symbol_rule`` entries and the incoming record's symbol, so a
   universe registered as ``aapl`` still withholds a recording produced as ``AAPL`` and vice versa.
   Deliberately scoped to THIS predicate alone -- ``expected_recording_pairs``/
   ``verify_recording_batch`` (TR-4's cherry-pick check) keep their own byte-exact matching
   unchanged, since the phase spec names only "the universe-rule test" inside this one function, not
   a broader normalization of the recording-batch verifier.

**Iteration 13 -- spec revision r8: recovery is HALT-ONLY this era.** (Owner ruling of
2026-08-19, recorded in ``docs/rapid-validation-spec.md``'s r8 revision header, its rewritten
section 7.8, and trap TR-29; and in ``state/assumptions.md``'s ``2026-08-19 -- OWNER RULING``
entry.) Iteration 12 shipped a GRADED recovery: a reconstruction that could not be PROVEN
complete still resumed service, marking the dataset ids it could name ``exposure_unknown``.
Iteration 13's first pass NARROWED that branch -- resume only when the attempt named at least as
many rows as the anchor attested -- rather than removing it, and the iteration-13 review then
disproved the whole design by execution. The tail anchor commits to a row
COUNT plus the final row's hash and to NO per-row identity, so a SAME-LENGTH suffix naming an
unrelated dataset satisfied every check the graded branch was able to make: the genuinely
destroyed shard then existed in no ledger at all, ``verify_chain()`` reported clean, and
``seal_shard`` would re-seal it FRESH under another universe -- the exact "unknown exposure
history read as never exposed" outcome section 7.8 forbids. **Row-count equality is not evidence
of identity and must NEVER authorize recovery.**

r8 therefore DELETES the graded branch outright. ``recover_shard_ledger`` below resumes ONLY on a
hash-attested proof of completeness; in EVERY other case it refuses -- leaving the corrupt file
byte-untouched and every vault predicate fail-closed -- no matter how much the operator attests.
The ``exposure_unknown`` lifecycle value is deleted with it: its only writer was that branch, and
its only purpose was to make a partially-known ledger servable, which is precisely what r8
forbids. No affected shard becomes fresh, sealable, assignable or ``historical_oos`` merely
because some reconstructed ledger would verify internally; if completeness cannot be proven, the
affected vault/tranche stays BLOCKED. Graded recovery returns only under a FUTURE named revision
built on a real identity commitment -- at minimum ordered row/event identities, preferably a
canonical checkpoint/manifest or Merkle-style commitment tied to the chain -- and that migration
is explicitly NOT designed here. The owner's governing sentence, which every branch below
implements literally: **for this era, safety wins over degraded availability -- unknown or
unprovable exposure history means the vault is unavailable, never "fresh".**

The SAME diff also pins, as a documented and tested decision rather than an open reviewer
question, that ``seal_shard``/``assign_shard``/``expose_shard`` gate on their own shard ledger
only (see each function's own docstring, and ``state/assumptions.md``'s iter-13 second entry)."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import secrets
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
    "VaultLedgerCorruptionError",
    "resolve_vault_dir",
    "shard_ledger_for_dataset_dir",
    "universe_ledger_for_dataset_dir",
    "recovery_ledger_for_dataset_dir",
    "VaultUniverseLedger",
    "VaultShardLedger",
    "VaultRecoveryLedger",
    "compute_rule_hash",
    "compute_rule_commitment",
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
    "preserve_corrupt_ledger",
    "recover_shard_ledger",
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

# The one-way lifecycle's three states -- the WHOLE vocabulary, there is no fourth (module
# docstring T-2: this module's OWN vocabulary, distinct from micro_readiness.py's
# EXPOSURE_STATE_EXPLORATORY/SPLIT_PROVENANCE_HAND_ASSIGNED).
#
# Iteration 12 added a fourth, `exposure_unknown`, as the graded-recovery downgrade target;
# spec revision r8 (2026-08-19, module docstring's own "Iteration 13" paragraph) DELETED both the
# branch that wrote it and the value itself. A vault whose exposure history cannot be PROVEN is
# unavailable -- never partially servable under a "we are not sure about this shard" state, which
# is exactly the degraded availability the owner traded away for safety.
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
# Iteration 12 (spec section 7.8): the THIRD, SEPARATE ledger lawful recovery writes to -- "record
# the corruption event separately and immutably" (never in the corrupted ledger itself, which
# cannot be trusted to record its own corruption).
_RECOVERY_LEDGER_FILENAME = "vault_recovery_ledger.jsonl"

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


class VaultLedgerCorruptionError(Exception):
    """TR-25/spec section 7.8: raised by every GATED vault-ledger read (``VaultShardLedger.
    verified_rows``/``VaultUniverseLedger.verified_rows``) the instant ``verify_chain()`` reports a
    broken chain -- content-hash mismatch, prev-hash mismatch, tail truncation, or a head-hash
    mismatch against the durable tail anchor. Fail-closed: no caller of a gated reader EVER
    receives a result computed over a ledger that failed this check, and there is no
    warn-and-continue path anywhere in this module (module docstring's own iteration-12 paragraph
    lists every choke point this reaches transitively). The ONLY way back is
    ``recover_shard_ledger`` below (lawful recovery, spec section 7.8) -- never a silent retry,
    never treating a truncated chain as merely "empty" (TC-1's own requirement: "no shard is
    reported as 'never exposed'"). ``main.py`` maps this to a single non-500 HTTP refusal for every
    route it can reach (module docstring)."""

    def __init__(self, ledger_kind: str, verify_result: dict) -> None:
        self.ledger_kind = ledger_kind
        self.verify_result = verify_result
        super().__init__(
            f"the {ledger_kind} vault ledger failed chain verification "
            f"(reason={verify_result.get('reason')!r}, failed_at_row={verify_result.get('failed_at_row')!r}) "
            "-- ALL vault/exposure work is refused (no sealing, no assignment, no exposure check, "
            "no sealed evaluation) until a lawful, evidence-backed recovery completes (spec "
            "section 7.8); unknown exposure history may NEVER be read as 'never exposed'"
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


def recovery_ledger_for_dataset_dir(dataset_dir_resolved: str) -> "VaultRecoveryLedger":
    """The SEPARATE, immutable incident ledger lawful recovery writes to (spec section 7.8 step 2:
    "record the corruption event separately and immutably" -- never in the corrupted ledger
    itself, which cannot be trusted to record its own corruption). The SAME sibling-of-the-
    dataset-dir resolution every other vault store shares (``resolve_vault_dir``), so there is
    exactly one vault location, holding all three ledgers side by side."""
    return VaultRecoveryLedger(resolve_vault_dir(dataset_dir_resolved))


# === the two ledgers (module docstring: "once per ledger") =========================================


class VaultUniverseLedger:
    """A thin domain wrapper over ONE ``HashChainedLedger`` -- every registered recording
    universe, in append order. Enforces no business rule of its own (the ``ScoutLedger``/
    ``WalkForwardLedger`` split); ``register_universe``/``find_universe`` below are the validated
    entry points every caller uses."""

    def __init__(self, root_dir: str) -> None:
        self._chain = HashChainedLedger(root_dir, _UNIVERSE_LEDGER_FILENAME)

    @property
    def path(self) -> Path:
        return self._chain.path

    @property
    def head_anchor_path(self) -> Path:
        return self._chain.head_anchor_path

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        """The RAW, UNGATED reader (``HashChainedLedger.all_rows()``'s own documented contract,
        unchanged) -- used only by this module's own recovery tooling, which must be able to
        inspect a corrupted ledger's content directly in order to repair it. Every NORMAL
        predicate uses ``verified_rows()`` below instead."""
        return self._chain.all_rows()

    def verified_rows(self) -> list[dict]:
        """TR-25/spec section 7.8: the GATED reader every normal predicate uses. Calls
        ``verify_chain()`` FIRST and raises ``VaultLedgerCorruptionError`` on any failure --
        never returns a result computed over a tampered or truncated chain (module docstring's
        iteration-12 paragraph)."""
        result = self._chain.verify_chain()
        if not result["ok"]:
            raise VaultLedgerCorruptionError("universe", result)
        return self._chain.all_rows()

    def read_tail_anchor(self) -> dict | None:
        return self._chain.read_tail_anchor()

    def rewrite_from_recovery(self, rows: list[dict]) -> None:
        self._chain.rewrite_from_recovery(rows)

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

    @property
    def path(self) -> Path:
        return self._chain.path

    @property
    def head_anchor_path(self) -> Path:
        return self._chain.head_anchor_path

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        """The RAW, UNGATED reader -- see ``VaultUniverseLedger.all_rows``'s own docstring; the
        identical split, mirrored for the shard ledger."""
        return self._chain.all_rows()

    def verified_rows(self) -> list[dict]:
        """TR-25/spec section 7.8: the GATED reader every normal predicate uses -- see
        ``VaultUniverseLedger.verified_rows``'s own docstring, mirrored for the shard ledger."""
        result = self._chain.verify_chain()
        if not result["ok"]:
            raise VaultLedgerCorruptionError("shard", result)
        return self._chain.all_rows()

    def read_tail_anchor(self) -> dict | None:
        return self._chain.read_tail_anchor()

    def rewrite_from_recovery(self, rows: list[dict]) -> None:
        self._chain.rewrite_from_recovery(rows)

    def append_row(self, fields: dict) -> dict:
        return self._chain.append_row(fields)


class VaultRecoveryLedger:
    """A thin domain wrapper over a THIRD ``HashChainedLedger`` (module docstring: "once per
    ledger") -- every corruption/recovery event lawful recovery records, in append order (spec
    section 7.8: "record the corruption event separately and immutably"). Deliberately NOT
    gated by its own ``verified_rows()`` -- this ledger is a pure audit trail no security
    predicate reads to make a decision, so keeping it simple (raw ``all_rows()``/``verify_chain()``,
    the pre-iteration-12 shape of the other two) avoids an unbounded regress of "who verifies the
    verifier". ``record_recovery_event``'s own append is unaffected either way, since
    ``HashChainedLedger.append_row`` never gates itself."""

    def __init__(self, root_dir: str) -> None:
        self._chain = HashChainedLedger(root_dir, _RECOVERY_LEDGER_FILENAME)

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
    ``scout_ledger.compute_spec_hash`` precedent, TC-2).

    **Never served publicly (spec r7/TR-27).** This stays exactly what it always was: the
    ledger's own INTERNAL freeze/idempotency identity function, read only by
    ``register_universe``'s own re-registration check. A bare deterministic hash of a low-entropy,
    dictionary-enumerable rule is not a hiding commitment -- ``compute_rule_commitment`` below is
    what ``_serialize_universe`` actually serves."""
    return _sha256_hex(_canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)}))


def compute_rule_commitment(nonce: str, symbol_rule: list[str], date_rule: list[str]) -> str:
    """spec section 7.2/7.5 (r7, TR-27): ``rule_commitment = sha256(nonce ++ canonical_rule)``.

    Unlike ``compute_rule_hash`` above, this is the value ``_serialize_universe`` actually SERVES
    pre-reveal. The owner's ruling was explicit about why a bare hash will not do:
    ``symbol_rule``/``date_rule`` are low-entropy and dictionary-enumerable (a real panel of
    tickers and a real date range), so a third party holding only the served digest could simply
    hash every plausible guess and check for a match. Prefixing a high-entropy nonce the ledger
    holds PRIVATELY (never served until whole-pool release) makes this a genuine hiding
    commitment: recomputing it without the nonce is infeasible, while an operator who legitimately
    learns the nonce at reveal can recompute it exactly (TC-7) and prove the rule never changed
    after registration.

    ``nonce`` is encoded as UTF-8 bytes and concatenated directly in front of the SAME canonical
    JSON encoding ``compute_rule_hash`` hashes -- a fixed-length hex string (``secrets.
    token_hex(32)`` == 64 hex chars, always), so the boundary between the two halves is never
    ambiguous."""
    canonical_rule = _canonical({"symbol_rule": list(symbol_rule), "date_rule": list(date_rule)})
    return _sha256_hex(nonce.encode("utf-8") + canonical_rule)


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
      redefine ``expected_recording_pairs`` and neutralize TR-4's cherry-pick refusal entirely.

    **TR-27 (r7): a fresh, high-entropy ``commitment_nonce`` is minted ONLY on a genuinely NEW
    row.** An idempotent replay returns the EXISTING row -- including its ORIGINAL nonce -- never
    generating a second one for what is, by definition, the same registration act."""
    rule_hash = compute_rule_hash(symbol_rule, date_rule)
    existing = find_universe(ledger, universe_id)
    if existing is not None:
        if (
            existing["rule_hash"] == rule_hash
            and existing["vault_secret_commitment"] == vault_secret_commitment
        ):
            return existing
        raise VaultUniverseAlreadyRegisteredError(universe_id, existing["rule_hash"], rule_hash)
    nonce = secrets.token_hex(32)
    fields = {
        "universe_id": universe_id,
        "symbol_rule": list(symbol_rule),
        "date_rule": list(date_rule),
        "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
        "rule_hash": rule_hash,
        "commitment_nonce": nonce,
        "rule_commitment": compute_rule_commitment(nonce, symbol_rule, date_rule),
        "vault_secret_commitment": vault_secret_commitment,
    }
    return ledger.append_row(fields)


def find_universe(ledger: VaultUniverseLedger, universe_id: str) -> dict | None:
    """The most recently registered universe row for ``universe_id``, or ``None`` -- append order
    IS registration order (the ``walkforward_ledger.latest_fold_spec`` precedent). TR-25: reads
    through the GATED ``verified_rows()`` -- a corrupted universe ledger refuses rather than
    silently resolving to a possibly-wrong "latest" row."""
    matches = [row for row in ledger.verified_rows() if row.get("universe_id") == universe_id]
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
    module, and every refusal is about the real dataset.

    TR-25/spec section 7.8: reads through the GATED ``verified_rows()`` -- this is the ONE scan
    every reader in this module shares (module docstring), so gating it here reaches
    ``currently_sealed_dataset_ids``, ``withheld_dataset_ids``, ``withheld_universe_by_dataset_id``,
    ``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``, and (via ``_latest_shard_row``
    below) ``seal_shard``/``assign_shard``/``expose_shard`` -- every one of them, with no second
    call site to remember to gate."""
    latest: dict[str, dict] = {}
    for row in ledger.verified_rows():
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
    ``load_vault_secret``'s already-validated return.

    **Corruption gating covers this function's own shard ledger only (iteration 13) -- a
    deliberate scope, not an oversight (TC-7 pins this).** ``seal_shard``/``assign_shard``/
    ``expose_shard`` read and write ONLY ``VaultShardLedger`` (via ``_latest_shard_row``'s own
    gated ``verified_rows()``); none of the three ever reads the universe ledger, even though a
    ``universe_id`` is stored on every row -- it is recorded verbatim, never looked up, so a
    corrupted UNIVERSE ledger cannot corrupt what these three write. Widening the gate to also
    require a sound universe ledger stays deferred until a matching universe-ledger recovery
    primitive exists to pair with it (module docstring's own "Iteration 12" paragraph, point 1's
    disclosed interpretation call, and ``state/assumptions.md``'s iter-13 second entry have the
    full reasoning): these three functions have zero production call sites today, so widening buys
    no real-world safety yet, while it would force updating roughly 81 unrelated test call sites
    across ten files and introduce a new halt-with-no-recovery-path failure mode the moment the
    universe ledger alone became corrupted."""
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
    (module docstring's shard-global single-shot reading, TC-8).

    **Corruption gating covers this function's own shard ledger only (iteration 13) -- see
    ``seal_shard``'s own docstring for the full reasoning.**"""
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
    "assigned to a different family" alike.

    **Corruption gating covers this function's own shard ledger only (iteration 13) -- see
    ``seal_shard``'s own docstring for the full reasoning.**"""
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
    named universe) -- the one ledger scan ``_universe_pair_index`` below needs. TR-25: reads
    through the GATED ``verified_rows()``."""
    latest: dict[str, dict] = {}
    for row in universe_ledger.verified_rows():
        latest[row["universe_id"]] = row
    return list(latest.values())


def _normalize_symbol(symbol: str) -> str:
    """Case-insensitive symbol matching, scoped SOLELY to the universe-rule withhold test inside
    ``unresolved_pool_universe_by_dataset_id`` (iteration 12's cheap-companion item: "today AAPL
    vs aapl hides nothing"). Deliberately NOT applied to ``expected_recording_pairs``/
    ``verify_recording_batch`` (TR-4's cherry-pick check keeps its own, separately-tested,
    byte-exact matching unchanged) -- the phase spec names only "the universe-rule test" inside
    this one function, not a broader normalization of the recording-batch verifier."""
    return symbol.strip().upper()


def _universe_pair_index(universe_ledger: VaultUniverseLedger) -> dict[tuple[str, str], list[dict]]:
    """Every registered universe's own ``expected_recording_pairs()``, indexed by each
    NORMALIZED ``(symbol, date)`` pair it covers (``_normalize_symbol`` above) -- built ONCE per
    call so a wide ``symbol_rule x date_rule`` product is walked once per universe, never once
    per caller record (``unresolved_pool_universe_by_dataset_id`` below does an O(1) dict lookup
    per record against this index)."""
    index: dict[tuple[str, str], list[dict]] = {}
    for universe in _latest_universes(universe_ledger):
        for symbol, date in expected_recording_pairs(universe):
            index.setdefault((_normalize_symbol(symbol), date), []).append(universe)
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
    identity leak.

    **Symbol matching is case-insensitive (iteration 12).** ``_universe_pair_index`` above
    normalizes every registered rule's symbols; the incoming record's own symbol is normalized
    the identical way at the lookup below -- so a universe registered as ``aapl`` still withholds
    a recording produced as ``AAPL``, and vice versa (TC-12/TC-13)."""
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
            for universe in pair_index.get((_normalize_symbol(symbol), session_date), ()):
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
      commitment can now be re-derived and verified (r3 point 2).

    The reveal test is a POSITIVE whitelist of the two states that provably earned disclosure
    (``assigned``, ``exposed``), not a blacklist of ``sealed`` -- so ``sealed`` and ANY value
    outside this module's three-state vocabulary alike serve only the opaque projection.
    Iteration 12 wrote the test the other way round (reveal unless ``sealed`` or the since-deleted
    ``exposure_unknown``), which would have disclosed symbol/date for any unrecognised state; r8
    (module docstring) removed the fourth state, and the whitelist form makes the serving layer
    fail CLOSED on an unrecognised one rather than depending on the exhaustiveness of a
    blacklist."""
    opaque = {key: row[key] for key in _OPAQUE_SHARD_KEYS}
    state = row["exposure_state"]
    if state not in (STATE_ASSIGNED, STATE_EXPOSED):
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


def _whole_pool_released_universe_ids(
    latest_shard_rows: dict[str, dict], universe_ledger: VaultUniverseLedger
) -> frozenset[str]:
    """TR-27/spec section 7.2 (r7): widened from ``_fully_exposed_universe_ids`` (pre-iteration-12,
    "every LEDGER-TRACKED shard exposed") to "every member of the universe's ORIGINAL registered
    pool released" -- the iteration-11 audit's own two-GET subtraction target
    (``vault._fully_exposed_universe_ids``, pre-iteration-12 ``vault.py:926-938``): a universe with
    every TRACKED shard exposed but an UNTRACKED pool member still unresolved was wrongly
    considered "fully exposed" by the old, narrower gate, which would have revealed the rule while
    a real member of the pool was still hidden.

    Reuses ``expected_recording_pairs`` -- the SAME expected-pairs computation
    ``unresolved_pool_universe_by_dataset_id`` already uses (module docstring: never a second,
    divergent implementation of "is this universe's pool resolved"). A universe_id is released iff
    BOTH:

    (a) no shard THIS LEDGER TRACKS for that universe (any ``dataset_id``, any row) is short of
        ``STATE_EXPOSED``; and
    (b) its OWN ``expected_recording_pairs()`` is a SUBSET of the ``(symbol, session_date)`` pairs
        this ledger has recorded as ``STATE_EXPOSED`` for that universe -- i.e. literally every
        pair the rule promised has reached the final lifecycle state, not merely every pair the
        ledger happens to have a row for.

    **Test (a) is load-bearing, not an optimization -- closes a real gap an adversarial pre-ship
    review found in test (b) alone.** Nothing in this module (or TR-12's single-shot discipline,
    which scopes to (family, shard), never to (symbol, date)) stops a SECOND, DIFFERENT shard
    (``dataset_id`` is a random per-recording identifier -- ``datasets.py``) from being sealed and
    assigned under the identical ``(symbol, session_date)`` pair as a first shard that has already
    reached ``exposed`` -- a re-recorded/retry day is exactly the shape spec section 7.7
    anticipates. Test (b) ALONE is pair-keyed and would have been satisfied by the first shard's
    exposure while the second, genuinely still-withheld shard sat unexposed -- reopening exactly
    the two-GET subtraction class this whole widening exists to close. Test (a) closes it: any
    LEDGER-TRACKED shard of the universe that is not yet exposed keeps the universe hidden,
    regardless of what the pair-coverage arithmetic in test (b) would otherwise say.

    An empty rule (no ``symbol_rule``/``date_rule`` entries at all -- not reachable through the
    Tier-B resolution order's own registration path, but not excluded by this module's own types
    either) owns nothing to reveal and is never considered released, matching the pre-iteration-12
    predicate's own fail-closed-on-no-shards behaviour."""
    exposed_pairs_by_universe: dict[str, set[tuple[str, str]]] = {}
    withholding_universe_ids: set[str] = set()
    for row in latest_shard_rows.values():
        universe_id = row["universe_id"]
        if row["exposure_state"] == STATE_EXPOSED:
            exposed_pairs_by_universe.setdefault(universe_id, set()).add(
                (row["symbol"], row["session_date"])
            )
        else:
            withholding_universe_ids.add(universe_id)  # test (a)
    released: set[str] = set()
    for universe in _latest_universes(universe_ledger):
        universe_id = universe["universe_id"]
        if universe_id in withholding_universe_ids:
            continue
        expected = expected_recording_pairs(universe)
        if expected and expected <= exposed_pairs_by_universe.get(universe_id, set()):  # test (b)
            released.add(universe_id)
    return frozenset(released)


def _serialize_universe(row: dict, released_universe_ids: frozenset[str]) -> dict:
    """A universe row's served projection -- the module docstring's join-resistance part 4,
    widened for TR-27 (r7, iteration 12).

    While the universe's WHOLE ORIGINAL POOL is not yet released (``_whole_pool_released_
    universe_ids`` above -- never merely "every ledger-tracked shard exposed"), only the NONCED
    ``rule_commitment`` (``compute_rule_commitment`` -- never the plain ``rule_hash``, which is
    dictionary-attackable on its own and stays purely internal) is served, plus the rule's two
    SIZES: the sizes state the tranche's shape (how much evidence was pre-committed, the
    auditable claim section 7.2 exists to fix in advance) while revealing nothing about WHICH
    symbol-days it contains, so ``expected - served`` cannot be computed against the public
    dataset listing. ``rule_disclosure`` names which of the two stages a reader is looking at, so
    a committed row can never be mistaken for a universe that genuinely has no members.

    Once released, ``symbol_rule``, ``date_rule`` and ``commitment_nonce`` all serve alongside the
    SAME ``rule_commitment`` -- so a reader can recompute ``compute_rule_commitment(nonce,
    symbol_rule, date_rule)`` and prove it equals the value that was committed at registration,
    long before the rule was ever revealed (TC-7). The plain ``rule_hash`` is never served at
    either stage -- it is not needed for that proof and stays the ledger's own internal identity
    function (module docstring)."""
    content = _row_content(row)
    base = {
        "universe_id": content["universe_id"],
        "registered_at": content["registered_at"],
        "rule_commitment": content["rule_commitment"],
        "vault_secret_commitment": content["vault_secret_commitment"],
    }
    if content["universe_id"] in released_universe_ids:
        return {
            **base,
            "symbol_rule": content["symbol_rule"],
            "date_rule": content["date_rule"],
            "commitment_nonce": content["commitment_nonce"],
            "rule_disclosure": RULE_DISCLOSURE_REVEALED,
        }
    return {
        **base,
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

    TR-25 (spec section 7.8): reads both ledgers through their GATED ``verified_rows()`` (via
    ``_latest_rows_by_dataset_id``/``_whole_pool_released_universe_ids``'s own ``_latest_universes``
    call and the final ``universe_ledger.verified_rows()`` below) -- a corrupted ledger raises
    ``VaultLedgerCorruptionError`` BEFORE this function ever builds a response body, so the two
    ``verify_chain()`` calls in the returned dict only ever report ``{"ok": True, ...}`` when this
    function returns at all (they stay for the happy-path "surfaced beside the data" precedent,
    exercised the instant either underlying gate has already passed).

    The universe rows go through ``_serialize_universe``'s own two-stage reveal
    (``_whole_pool_released_universe_ids``, TR-27/r7). An earlier version of this function served
    them in FULL, reasoning that "knowing a tranche covers S symbols x D dates says nothing about
    WHICH of those symbol-days the secret-keyed HMAC sealed". That reasoning was wrong, and the
    iter-9 audit (third pass, finding B1) reproduced why: it is true of the rule in isolation and
    false the moment the rule is read beside ``GET /research/datasets``, which serves every
    recorded shard EXCEPT the withheld ones. Since TR-4 forces the recorded batch to be the rule's
    complete output, ``expected - served`` is exactly the sealed set -- a full de-anonymisation
    from two public GETs. The rule is therefore committed (``rule_commitment``, plus its two
    sizes) until every member of the ORIGINAL pool is released. Section 7.2 is unaffected: it
    requires the rule to be RECORDED in the vault ledger before any fetch, which it still is, and
    the TR-4 verifier reads it from that ledger, not from this payload."""
    latest_shard_rows = _latest_rows_by_dataset_id(shard_ledger)
    released = _whole_pool_released_universe_ids(latest_shard_rows, universe_ledger)
    return {
        "universes": [_serialize_universe(row, released) for row in universe_ledger.verified_rows()],
        "shards": [_serialize_shard(row) for row in latest_shard_rows.values()],
        "shard_ledger_chain_verification": shard_ledger.verify_chain(),
        "universe_ledger_chain_verification": universe_ledger.verify_chain(),
    }


# === lawful recovery -- fail closed, recover only on PROOF (spec section 7.8, r8) ==================
#
# The ONLY way back from a `VaultLedgerCorruptionError`, and since r8 (module docstring's own
# "Iteration 13" paragraph) it is a single, all-or-nothing door: a hash-attested proof of
# completeness resumes exact prior service, and everything else halts. Scoped to the SHARD ledger
# (a disclosed scope choice, T-1) because that is the ledger whose corruption can make a shard look
# fresh; the shared low-level pieces below (`preserve_corrupt_ledger`, `_verified_prefix_rows`,
# `_rehash_suffix`) are generic over EITHER wrapper class, so an equivalent universe-ledger door
# could reuse them unchanged if a future iteration needs one -- not built here because nothing in
# this iteration's own test-first contract exercises it.


def preserve_corrupt_ledger(ledger, quarantine_dir: str, *, incident_id: str) -> dict:
    """spec section 7.8 step 3: preserves the corrupt ledger file BYTE-FOR-BYTE before any repair
    -- so a corrupted ledger becomes a forensic artifact, never silently discarded or overwritten
    (this codebase's own "corrupt files surfaced, never overwritten" discipline, extended here to
    an explicit, evidenced exception the recovery flow itself creates). Copies both the ledger's
    own ``.jsonl`` file and its tail-anchor sidecar (when one exists) into ``quarantine_dir``,
    named by ``incident_id`` so two incidents against the same ledger can never collide or
    overwrite one another. The ORIGINAL files at ``ledger.path``/``ledger.head_anchor_path`` are
    left exactly where they were -- this function only ever ADDS copies, never moves or deletes
    the source, so an operator's own external forensic tooling still finds them too.

    ``ledger`` is a ``VaultShardLedger``/``VaultUniverseLedger`` (anything exposing ``.path``/
    ``.head_anchor_path``) -- generic over either wrapper class (module section note above)."""
    quarantine_root = Path(quarantine_dir)
    quarantine_root.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger.path
    raw = ledger_path.read_bytes() if ledger_path.exists() else b""
    preserved_ledger_path = quarantine_root / f"{incident_id}.{ledger_path.name}"
    preserved_ledger_path.write_bytes(raw)

    anchor_path = ledger.head_anchor_path
    preserved_anchor_path = None
    if anchor_path.exists():
        preserved_anchor_path = quarantine_root / f"{incident_id}.{anchor_path.name}"
        preserved_anchor_path.write_bytes(anchor_path.read_bytes())

    return {
        "preserved_ledger_path": str(preserved_ledger_path),
        "preserved_anchor_path": str(preserved_anchor_path) if preserved_anchor_path else None,
        "corrupt_ledger_sha256": _sha256_hex(raw),
    }


def _verified_prefix_rows(ledger, verify_result: dict) -> list[dict]:
    """The prefix of ``ledger``'s RAW rows (``ledger.all_rows()``, the UNGATED reader) that lawful
    recovery can still trust, given a FAILED ``verify_chain()`` result -- recovery must reason
    about ledger content directly, since ``verify_chain()`` itself only ever reports pass/fail,
    never "how much of this can still be trusted".

    Conservative on the ONE failure mode where even EARLIER rows are not provably genuine:
    ``head_hash_mismatch`` means the file's own per-row content/prev-hash walk was ALREADY
    internally self-consistent from row 0 onward (``verify_chain()`` only reaches ``_verify_tail``
    -- the check this reason comes from -- after that whole walk passes), yet the row at the
    anchor's own recorded position does not match the hash the anchor committed for it. The tail
    anchor's ``head_hash`` is the ONLY externally-anchored proof point in this whole scheme; if it
    does not match, the current file could be a DIFFERENT, still-self-consistent chain (a
    wholesale replacement, not a mere truncation), so nothing before it is provably the true
    original either -- an empty trusted prefix, never a guess at how far back the replacement
    might start. The same applies to ``head_anchor_missing`` with rows present (an anchor that
    once existed and no longer does is exactly as suspect). ``tail_truncated`` is the opposite,
    genuinely benign case: every row 0..len(rows)-1 already passed the SAME internal walk, and the
    anchor merely claims MORE rows should exist -- the present rows ARE a genuine prefix of the
    true history, so the whole file is trusted."""
    reason = verify_result.get("reason")
    raw_rows = ledger.all_rows()
    if reason in ("content_hash_mismatch", "prev_hash_mismatch"):
        return raw_rows[: verify_result["failed_at_row"]]
    if reason == "tail_truncated":
        return raw_rows
    return []  # head_hash_mismatch / head_anchor_missing / anything unrecognised: trust nothing


def _rehash_suffix(good_prefix: list[dict], suffix_fields: list[dict]) -> list[dict]:
    """Re-derives the ``row_hash``/``prev_hash``/``row_index`` chain for ``suffix_fields`` (plain
    content dicts, no ledger-internal keys) as though ``HashChainedLedger.append_row`` had
    appended them one at a time onto ``good_prefix`` -- the IDENTICAL algorithm (this module's own
    ``_canonical``/``_sha256_hex``, the same canonical encoding every sibling ledger in this
    codebase hashes), so a genuinely faithful reconstruction reproduces byte-identical hashes to
    the rows that were actually lost, and a wrong or incomplete guess provably does not."""
    rows: list[dict] = []
    prev_hash = good_prefix[-1]["row_hash"] if good_prefix else None
    index = len(good_prefix)
    for fields in suffix_fields:
        content = {**fields, "row_index": index, "prev_hash": prev_hash}
        row_hash = _sha256_hex(_canonical(content))
        row = {**content, "row_hash": row_hash}
        rows.append(row)
        prev_hash = row_hash
        index += 1
    return rows


def recover_shard_ledger(
    shard_ledger: VaultShardLedger,
    *,
    verify_result: dict,
    reconstructed_suffix: list[dict],
    sources: list[dict],
    operator_identity: str,
    reason: str,
    recovery_ledger: VaultRecoveryLedger,
    incident_id: str,
    quarantine_dir: str,
    recovered_at: str | None = None,
) -> dict:
    """spec section 7.8's full lawful-recovery sequence for the SHARD ledger. **Halt-only since
    spec revision r8** (2026-08-19 owner ruling; module docstring's own "Iteration 13" paragraph):
    exactly TWO outcomes, divided by a byte-for-byte PROOF -- never a row count, never a shape,
    never the operator's word.

    Steps, in order:

    1. Preserve the corrupt ledger byte-for-byte (``preserve_corrupt_ledger``) -- forensic
       evidence, independent of whatever happens next. Also reads the ledger's OWN currently
       committed tail anchor (``read_tail_anchor``) -- untouched by a content-only corruption --
       as the hash-attested target step 3 below tests against.
    2. Identify the last verified row (``_verified_prefix_rows``).
    3. Re-chain the caller's ``reconstructed_suffix`` onto that prefix EXACTLY the way
       ``HashChainedLedger.append_row`` would (``_rehash_suffix``) and test whether the result is
       HASH-ATTESTED COMPLETE -- FIVE conjuncts, every one required and none sufficient alone:
       the candidate is non-empty, its row count equals the anchor's own ``row_count``, its final
       row's hash equals the anchor's own ``head_hash``, the whole candidate chain is internally
       consistent when re-derived from its own row contents, and it accounts for at least as many
       rows as the preserved corrupt file itself still carries (a recovery may never DELETE
       preserved evidence). The three guards beyond the original count+hash pair each close a
       laundering path found by attacking this function directly; the inline comments at the check
       itself carry all three reproductions. See also the r8 note below on why the count conjunct
       can never be promoted into a dividing line of its own.
    4. Two outcomes, and only two:

       a. **PROVEN COMPLETE -> resume exactly.** The reconstructed prefix+suffix becomes the
          ledger's new content (``VaultShardLedger.rewrite_from_recovery`` -- the ONE lawful
          whole-file rewrite this module ever performs, and only here, only after the corrupt
          original is already preserved); a ``recovery_completed`` row (citing every hash, source,
          operator identity and reason) is appended to ``recovery_ledger``; returns ``{"ok": True,
          "resumed": True}``. Predicates read this ledger normally again from this point on,
          reporting the EXACT prior exposure state -- no shard's history is guessed at, because
          the reconstruction reproduced the committed head hash bit for bit.
       b. **ANYTHING ELSE -> HALT.** A missing, truncated, tampered, wrong, reordered, padded or
          merely unproven suffix -- and equally a missing or unreadable anchor
          (``read_tail_anchor()`` returned ``None``, so no independent proof of the true history
          exists to test against AT ALL) -- all land here. ``rewrite_from_recovery`` is NEVER
          called: the corrupted file on disk stays byte-untouched, ``verify_chain()`` keeps
          reporting exactly the same failure immediately afterward, and every dependent predicate
          (``currently_sealed_dataset_ids``, ``withheld_dataset_ids``,
          ``unresolved_pool_universe_by_dataset_id``, ``build_vault_state``, and the
          ``seal_shard``/``assign_shard``/``expose_shard`` transitions, all gated through
          ``verified_rows()``) keeps raising ``VaultLedgerCorruptionError``. The affected vault
          stays BLOCKED -- no shard of it becomes fresh, sealable, assignable or ``historical_oos``
          on the strength of an unproven story about its own history. An immutable incident row
          (``outcome: "halted"``, citing the anchor's own ``row_count``/``head_hash`` beside what
          the attempt actually produced) is still appended to ``recovery_ledger``, so the attempt
          is on permanent record even though nothing about the shard ledger changed. Returns
          ``{"ok": False, "resumed": False}``. A LATER call against the SAME still-corrupted file,
          given a genuinely provable reconstruction, still succeeds normally -- a halt never
          consumes or alters the original corrupted ledger.

    **Why there is no third, "graded" branch (r8, and TR-29 keeps it deleted).** Iteration 12 had
    one, and iteration 13's first pass narrowed it instead of removing it: if the attempt merely
    NAMED as many rows as the anchor attested, it resumed with the named dataset ids marked
    ``exposure_unknown``. The iteration-13 review broke that by execution --
    seal ``d-1``/``d-2``/``d-3``, destroy ``d-3``'s row, hand this function a SAME-LENGTH suffix
    naming an unrelated ``d-fake``, and ``d-3`` vanished from every ledger while ``verify_chain()``
    reported clean and ``seal_shard`` would re-seal it fresh under another universe. The defect is
    not fixable by tightening that comparison, because the tail anchor commits to a row COUNT plus
    the final row's hash and to NO per-row identity: **counting can never prove identity.** A
    future named revision may reintroduce graded recovery once the ledger carries a real identity
    commitment (at minimum ordered row/event identities, preferably a canonical checkpoint or
    Merkle-style manifest tied to the chain) -- deliberately NOT designed here, and no on-disk
    format changes in this fix.

    ``sources``/``operator_identity``/``reason`` are recorded as audit metadata on every outcome
    and are read by NO decision this function makes: operator attestation can never substitute for
    missing identity evidence (spec section 7.8), so no value of any of them can turn a halt into a
    resume. Only the hashes decide."""
    preserved = preserve_corrupt_ledger(shard_ledger, quarantine_dir, incident_id=incident_id)
    anchor = shard_ledger.read_tail_anchor() or {}
    anchor_row_count = anchor.get("row_count")
    good_prefix = _verified_prefix_rows(shard_ledger, verify_result)
    preserved_row_count = len(shard_ledger.all_rows())
    candidate_suffix = _rehash_suffix(good_prefix, reconstructed_suffix)
    candidate_rows = good_prefix + candidate_suffix
    recovered_at = recovered_at if recovered_at is not None else _iso_utc_now()
    final_hash = candidate_rows[-1]["row_hash"] if candidate_rows else None

    # Spec section 7.8's own "verify the reconstruction is internally consistent" step, applied to
    # the WHOLE candidate ledger rather than the suffix half alone. `_rehash_suffix` already IS the
    # definition of a valid chain (`HashChainedLedger.append_row`'s algorithm), so re-deriving every
    # row from its content and demanding byte-equality re-checks each row's own content hash, its
    # prev_hash link and its row_index in one comparison -- with no second implementation of the
    # chain walk. It matters because `good_prefix` comes from `_verified_prefix_rows`, which trusts
    # the CALLER-SUPPLIED `verify_result` to decide how much of the on-disk file is genuine: hand
    # this function a `verify_result` that understates the damage (say "tail_truncated" over a file
    # whose interior row was edited in place) and the stored final row hash can still match the
    # anchor, so the two hash/count conjuncts alone would attest "proven complete" over rows the
    # file itself no longer authenticates. Verified by execution before this line existed.
    rederived = _rehash_suffix([], [_row_content(row) for row in candidate_rows])
    internally_consistent = rederived == candidate_rows

    # `bool(candidate_rows)`: an EMPTY reconstruction can never be a proof. Without it, an anchor
    # reading `{"row_count": 0, "head_hash": null}` -- which `append_row` never writes, so it means
    # tampering or an earlier bad rewrite -- is "matched" by supplying nothing at all (0 == 0, None
    # == None), and the recovery would WIPE the ledger and report success: every sealed shard gone,
    # re-sealable fresh under any universe. Verified by execution before this guard existed. A
    # genuinely empty ledger has no lost history to recover and never reaches this function.
    #
    # `len(candidate_rows) >= preserved_row_count` (iteration-13 AUDIT): a recovery may never DELETE
    # rows the corrupt file itself still carries. The anchor is written AFTER the row it commits to
    # (`micro_chain_ledger.append_row`'s own comment calls the window "benign -- never falsely
    # short"), so a crash between the two leaves the ledger LONGER than the anchor. In that state a
    # byte-GENUINE reconstruction of the anchor-length history satisfies the four conjuncts above
    # while `rewrite_from_recovery` truncates the surplus rows away -- observed end to end: seal
    # d-1..d-4 with the anchor lagging at 3, corrupt an interior row, recover with the true first
    # three rows, and d-4's seal row is gone, `verify_chain()` reports clean, `seal_shard` re-seals
    # d-4 FRESH, and a `recovery_completed` attestation certifies the loss. That is r8 section 7.8's
    # forbidden outcome ("no affected shard becomes fresh, sealable, assignable ... merely because
    # the reconstructed ledger now verifies internally") reached through the PROVEN side of the
    # door. This conjunct is a pure additional REFUSAL -- it can only turn a proof into a halt,
    # never the reverse -- so it does not resurrect count equality as evidence of anything: it is a
    # floor against destroying preserved evidence, never an authorization. When it fires the vault
    # stays BLOCKED, which is r8's own trade (safety over degraded availability).
    proven_complete = (
        bool(candidate_rows)
        and anchor_row_count == len(candidate_rows)
        and final_hash == anchor.get("head_hash")
        and internally_consistent
        and len(candidate_rows) >= preserved_row_count
    )

    last_verified_row_index = (len(good_prefix) - 1) if good_prefix else None
    last_verified_row_hash = good_prefix[-1]["row_hash"] if good_prefix else None

    if proven_complete:
        shard_ledger.rewrite_from_recovery(candidate_rows)
        recovery_ledger.append_row(
            {
                "kind": "recovery_completed",
                "ledger_kind": "shard",
                "incident_id": incident_id,
                "corrupt_ledger_sha256": preserved["corrupt_ledger_sha256"],
                "last_verified_row_index": last_verified_row_index,
                "last_verified_row_hash": last_verified_row_hash,
                "sources": list(sources),
                "recovered_suffix_hash": _sha256_hex(_canonical(list(reconstructed_suffix))),
                "operator_identity": operator_identity,
                "reason": reason,
                "recovered_at": recovered_at,
                "outcome": "complete",
            }
        )
        return {"ok": True, "resumed": True}

    # NOT PROVEN COMPLETE -> HALT, unconditionally (spec section 7.8 r8; docstring branch 4b). No
    # secondary test runs here and none may ever be added on the CURRENT anchor schema: the anchor
    # commits to a row count and the final row's hash only, so nothing available at this point can
    # distinguish "every truly lost row is accounted for" from "the count was padded with rows that
    # were never there" -- the exact laundering TR-29 pins. The corrupted file is left alone; the
    # vault stays blocked; the attempt goes on permanent record and changes nothing else.
    recovery_ledger.append_row(
        {
            "kind": "recovery_halted",
            "ledger_kind": "shard",
            "incident_id": incident_id,
            "corrupt_ledger_sha256": preserved["corrupt_ledger_sha256"],
            "last_verified_row_index": last_verified_row_index,
            "last_verified_row_hash": last_verified_row_hash,
            # Audit metadata only -- recorded because a halt must say what was attempted, never
            # read back by any decision above (docstring's closing paragraph).
            "attempted_sources": list(sources),
            "operator_identity": operator_identity,
            "reason": reason,
            "recovered_at": recovered_at,
            # Why the proof failed: the two dimensions the anchor actually commits to, plus
            # whether the candidate chain even hangs together on its own terms.
            "anchor_row_count": anchor_row_count,
            "attempted_row_count": len(candidate_rows),
            # How many rows the preserved corrupt file itself still carried -- an attempt that
            # accounts for FEWER than this would have destroyed preserved evidence (see the
            # `preserved_row_count` conjunct above).
            "preserved_row_count": preserved_row_count,
            "anchor_head_hash": anchor.get("head_hash"),
            "attempted_final_row_hash": final_hash,
            "attempted_chain_internally_consistent": internally_consistent,
            "outcome": "halted",
        }
    )
    return {"ok": False, "resumed": False}
