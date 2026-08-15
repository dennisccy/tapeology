"""Era 6 "The Referee" (J-05) -- the registry: pre-registration with an immutable boundary. The
FOURTH ``referee_*.py`` module, following ``referee_evidence.py``/``referee_null.py``'s exact
conventions (append-only file-per-record stores, checksum-verified loads, a resolved
env-var-or-sibling storage directory, a CLI warmer matching ``argparse``/``main()``).

**What this module builds, spec-verbatim (``docs/referee-statistical-spec.md`` Sec5).** Four
append-only record kinds -- FAMILY, HYPOTHESIS, WITHDRAWAL, CERTIFICATE -- plus the registration
act (``register_hypothesis``) that writes the first two, the withdrawal act
(``withdraw_hypothesis``) that writes the third, and the read-side fold (``registry_response``)
``GET /research/desk/referee/registry`` serves. The CERTIFICATE store exists this iteration in
SHAPE only (append-only-ness tested); its mint path is explicitly J-08's job
(``docs/goal.md``: "mintable only through the real evaluation rail").

**Family + hypothesis are registered together, through ONE act.** The Data Contract names
exactly one POST route (``.../registry/hypotheses``) and the goal's own Steps describe
"Registration acts: CLI + POST ... with explicit confirmation" as a single act, never two. A
FAMILY's ``candidate_hypothesis_ids`` must be "the COMPLETE planned list -- the BH denominator m,
forever" (spec Sec5), decided BEFORE any of its hypotheses are individually registered -- so
every hypothesis-registration call carries its OWN family's full definition
(``family_id``/``family_q``/``family_candidate_hypothesis_ids``) alongside the hypothesis's own
fields. The FIRST call naming a given ``family_id`` CREATES that family record (append-only,
from that call's own family fields); every LATER call naming the SAME ``family_id`` must supply
the IDENTICAL ``q``/candidate list (else refused -- a family's definition can never drift after
its first sighting) and its own ``hypothesis_id`` must already be a member of that list (a
hypothesis can never "join a family retroactively" -- the era's own anti-goal, made structural).
``FamilyStore`` is independently a plain append-only store (TC-1 exercises it directly, with no
hypothesis involved at all) -- ``register_hypothesis`` is simply its ONE production caller this
iteration.

**``hypothesis_id``/``family_id``/``certificate_id`` are caller-supplied, not derived.** Unlike
``RefereeNullStore`` (whose identity is a pure function of an observation + null-spec, so a
re-run over an unchanged corpus must DEDUPE, never duplicate), a hypothesis is a genuinely new,
rare, deliberate operator act each time -- there is no "the same content should collapse to the
same record" requirement anywhere in the spec, and mandating one would invent an identity
function the spec never names. A caller-chosen mnemonic string (mirroring how ``family_id``,
setup ids, and dataset ids are already caller-named throughout this codebase) is the simplest
design that satisfies every TC: "duplicate hypothesis_id/family_id" (IN SCOPE) means exactly
"the same id string submitted twice," structurally identical to ``NullAlreadyRecorded``'s own
append-only-with-raise discipline.

**The boundary is computed, not chosen -- and no operator surface can name the instant it is
computed FROM (iter-6 audit, finding B1).** ``confirmation_start_boundary`` is DEFINED as "the ET
calendar date of ``registered_at``" (spec Sec5) -- never independently choosable. The
payload-level ``registered_at`` override below survives as a hermetic TEST seam only (the ONLY way
a keyless test can exercise a specific ET calendar instant -- e.g. TC-8's 23:30 ET fixture --
without waiting on the real clock): the POST route does not expose the field at all and the CLI
carries no ``--registered-at`` flag, so every operator-reachable registration is stamped with real
wall-clock ``_iso_utc_now()``. That containment is load-bearing, not hygiene -- a caller-chosen
instant IS a caller-chosen boundary, and a backdated boundary makes already-recorded HISTORICAL
sessions accrue as post-boundary confirmation, breaching the era's "the historical atlas is
exploratory forever" anti-goal into an append-only record with no delete path. An explicit
``confirmation_start_boundary`` in the payload is likewise never stored as-is: a value AT OR
BEFORE the honest computed one is refused (``RetroactiveBoundary``, TC-4); a value strictly after
it is ignored (the stored value is always exactly the computed one -- spec Sec5 names no "delay
the boundary" feature). This is a defensive validation path, not a feature a real caller is
expected to use.

**The Estimand-C "cannot evaluate" check is structural, never a live resolve (Build Notes,
iteration spec).** A hypothesis registers against a setup+side ABSTRACTLY -- no concrete
symbol/session exists yet to hand ``BandMapResolver.resolve()``. The spec's own text ("not
evaluable at anchor bars from recorded data") is satisfied by checking the named
``backing_bucket`` value against the FIXED vocabulary (``PLAYBOOK_CONTEXT_BACKING_BUCKETS``) --
never a live map lookup. This module does NOT import ``desk_playbook_context`` (the
import-topology guard's existing, unmodified ban already covers it, since it globs every
``referee_*.py`` module) -- it reads the vocabulary constant TRANSITIVELY through
``referee_null.py`` (the one referee module the guard exempts to hold it in the first place),
never touching the live resolver, never duplicating the vocabulary as a second hand-copied
tuple (single source of truth).

**Withdrawal's evaluation-existence signal is injected, not queried.** No evaluation store
exists until J-06 -- ``withdraw_hypothesis`` takes a plain ``post_boundary_evaluation_exists:
bool`` parameter (default ``False``, the honest answer for EVERY real hypothesis today, since no
evaluation of any kind has ever run this era) rather than reaching into a store that does not
exist. J-06 wires the real signal through this identical parameter once it exists -- the
refusal RULE itself (tested both ways via the injected bool, TC-9/TC-10) does not change.

**Accrual is a disclosed readiness PROXY, not spec Sec3.1's exact informative-session count**
(ratified, ``runs/goal-session-referee/state/assumptions.md`` iter-6): the count of distinct
POST-BOUNDARY ``session_date``s carrying >=1 observation in the hypothesis's own
``(setup_id, side)`` cell, computed with the SAME shared pooling primitives
``referee_evidence.playbook_occurrence_readiness()`` is built from
(``_newest_per_session_date``, ``_is_stale_basis``, ``current_playbook_detector_basis``) --
never a second, independently-written date/basis loop, and never a second ``PlaybookStore``
scan per hypothesis: ``registry_response`` scans the store exactly ONCE per call and folds every
hypothesis's own accrual against that single scan.

**iter-8 (J-07) additions -- the starter-family shortlist + the discovery fold, plus two
write-side riders.** ``shortlist_response()`` serves spec Sec7's five PINNED candidates
(``REFEREE_STARTER_FAMILY_SHORTLIST``) beside LIVE readiness (``GET .../registry/shortlist``) --
the FIRST real, browser-usable Referee action of the whole era. ``registry_response()``'s
per-hypothesis fold gains a ``discovery`` block (``_hypothesis_discovery``): the exact
PRE-boundary complement of ``accrual``, over the SAME pooling primitives -- never a confirmatory
count, always labeled ``"discovery (exploratory)"``. Neither addition writes anything; both are
pure reads over the identical already-scanned corpus. This module's own two write-side riders
(a failed-attestation write gate, an integrity-error disclosure) live in ``referee_adjudicate.py``
instead, since that is where the affected writer/reader actually is."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_playbook import PlaybookStore
from .referee_evidence import (
    _epoch_from_iso,
    _et_session_date,
    _is_stale_basis,
    _newest_per_session_date,
    _record_detector_basis,
    current_playbook_detector_basis,
    playbook_occurrence_readiness,
)
from .referee_null import (
    AT_WALL,
    PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
    REFEREE_NULL_CONTEXT_SPEC_ID,
    REFEREE_NULL_TOD_SPEC_ID,
    REFEREE_TEST_PERM_SPEC_ID,
    BandMapResolver,
    resolve_occurrence_backing_bucket,
)

__all__ = [
    "REFEREE_MIN_SESSIONS",
    "REFEREE_MIN_OCCURRENCES",
    "REFEREE_DEFAULT_Q",
    "REFEREE_HYPOTHESIS_ORIGIN",
    "REFEREE_STARTER_FAMILY_ID",
    "REFEREE_STARTER_FAMILY_SHORTLIST",
    "resolve_referee_registry_dir",
    "RegistryIntegrityError",
    "FamilyAlreadyRecorded",
    "HypothesisAlreadyRecorded",
    "CertificateAlreadyRecorded",
    "HypothesisMalformed",
    "RetroactiveBoundary",
    "UnknownSpecId",
    "ConfirmationRequired",
    "WithdrawalRefused",
    "FamilyStore",
    "HypothesisStore",
    "WithdrawalStore",
    "CertificateStore",
    "register_hypothesis",
    "withdraw_hypothesis",
    "registry_response",
    "shortlist_response",
]

# === spec Sec1: the two floors this module is the first consumer of (module constants, never
# Config fields -- the `REFEREE_NULL_ANCHORS_PER_OCCURRENCE`-in-`referee_null.py` precedent: a
# constant lives in the FIRST module that actually needs it, not in a shared catch-all). ===========

REFEREE_MIN_SESSIONS: int = 12
REFEREE_MIN_OCCURRENCES: int = 12

# goal-referee-iter-9 rider (closes the iter-8 coherence-audit F1 WARN): spec Sec1's own pinned
# default BH q -- previously only an UNOWNED apps/frontend/app/desk/page.tsx literal
# (REFEREE_STARTER_FAMILY_Q). Owned here, served by `shortlist_response()` below.
REFEREE_DEFAULT_Q: float = 0.10

# The starter family's own id (spec Sec7's single shared family) -- previously only an unowned
# frontend literal (REFEREE_STARTER_FAMILY_ID in apps/frontend/app/desk/page.tsx), moved
# backend-side this iteration (goal-referee-iter-9 rider) and served by `shortlist_response()`.
REFEREE_STARTER_FAMILY_ID: str = "referee-starter-family"

# Every hypothesis this era carries this exact origin label (goal.md: "the atlas was inspected
# before these questions were written down") -- server-stamped, never caller-supplied.
REFEREE_HYPOTHESIS_ORIGIN: str = "historical-exploration"

_EVIDENCE_FAMILIES = frozenset({"playbook", "strategy"})
_ESTIMANDS = frozenset({"A", "B", "C"})
_SIDES = frozenset({"long", "short"})
_SIDEDNESS_VALUES = frozenset({"greater", "less", "two-sided"})
_NULL_SPEC_IDS = frozenset({REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID})
_TEST_SPEC_IDS = frozenset({REFEREE_TEST_PERM_SPEC_ID})
_CONTEXTUAL_ESTIMANDS = frozenset({"B", "C"})

_REGISTRY_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR"

_REQUIRED_HYPOTHESIS_FIELDS: tuple[str, ...] = (
    "hypothesis_id",
    "family_id",
    "family_q",
    "family_candidate_hypothesis_ids",
    "evidence_family",
    "estimand",
    "setup_id",
    "side",
    "primary_measure_key",
    "primary_horizon",
    "sidedness",
    "test_spec_id",
    "target_sessions",
    "min_occurrences",
)


def resolve_referee_registry_dir(desk_universe_dir_resolved: str) -> str:
    """The registry's ONE storage directory (all four record kinds live here, distinguished by
    filename prefix): ``TAPEOLOGY_DESK_REFEREE_REGISTRY_DIR`` if set, else a ``referee_registry``
    SIBLING of the caller's own already-resolved universe directory
    (``resolve_referee_null_dir``'s exact pattern). Deliberately NOT a ``Config`` field."""
    override = os.environ.get(_REGISTRY_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_registry")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


# === exceptions =======================================================================================


class RegistryIntegrityError(Exception):
    """An on-disk registry record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


class FamilyAlreadyRecorded(Exception):
    def __init__(self, family_id: str) -> None:
        self.family_id = family_id
        super().__init__(
            f"a family record with id {family_id!r} is already recorded -- family records are "
            f"immutable and are never re-recorded"
        )


class HypothesisAlreadyRecorded(Exception):
    def __init__(self, hypothesis_id: str) -> None:
        self.hypothesis_id = hypothesis_id
        super().__init__(
            f"a hypothesis record with id {hypothesis_id!r} is already recorded -- hypothesis "
            f"records are immutable and are never re-recorded"
        )


class CertificateAlreadyRecorded(Exception):
    def __init__(self, certificate_id: str) -> None:
        self.certificate_id = certificate_id
        super().__init__(
            f"a certificate record with id {certificate_id!r} is already recorded -- certificate "
            f"records are immutable and are never re-recorded"
        )


class HypothesisMalformed(Exception):
    """A registration payload is missing a required field, carries an out-of-vocabulary value, a
    below-floor sample target, an unevaluable Estimand-C context predicate, or a family
    definition that disagrees with that family's own already-recorded fields."""


class RetroactiveBoundary(Exception):
    """A payload's own explicit ``confirmation_start_boundary`` disagrees with the honest value
    ``registered_at`` computes to -- refused (the boundary is derived, never chosen)."""


class UnknownSpecId(Exception):
    """A payload names a ``null_spec_id``/``test_spec_id`` outside the pinned set (spec Sec1)."""


class ConfirmationRequired(Exception):
    """``confirm`` was not explicitly ``True`` -- no record is ever written without it."""


class WithdrawalRefused(Exception):
    """A withdrawal was refused: unknown ``hypothesis_id``, a post-boundary evaluation already
    exists, or the hypothesis is already withdrawn."""


# === shared checksum-verified JSON record read/write (4 store classes below share this) ==============


def _write_json_record(root: Path, path: Path, fields: dict, *, kind: str) -> dict:
    record = {"meta": dict(fields)}
    payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
    root.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return dict(fields)


def _load_json_record(path: Path, *, kind: str) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise RegistryIntegrityError(
            f"{kind} file '{path.name}' is not parseable ({exc}) -- corrupted or tampered"
        ) from exc
    if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
        raise RegistryIntegrityError(
            f"{kind} file '{path.name}' does not carry the expected record shape -- corrupted "
            f"or tampered"
        )
    record = data["record"]
    if _sha256(_canonical(record)) != data["file_checksum"]:
        raise RegistryIntegrityError(
            f"{kind} file '{path.name}' failed its integrity check (checksum mismatch) -- the "
            f"file was corrupted or tampered with"
        )
    meta = record.get("meta")
    if not isinstance(meta, dict):
        raise RegistryIntegrityError(
            f"{kind} file '{path.name}' does not carry the expected record shape -- corrupted "
            f"or tampered"
        )
    return meta


# === the four append-only stores (one shared directory, one filename prefix each) ====================


class FamilyStore:
    """File-based store rooted at the resolved registry directory, ``family-*.json`` files only.
    No update/delete method exists anywhere on this class (structural -- source-scan
    guard-tested); ``record`` refuses an already-present ``family_id`` (``FamilyAlreadyRecorded``,
    TC-1) or a corrupted file already occupying that id's own deterministic path
    (``RegistryIntegrityError``, never a silent overwrite)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, family_id: str) -> Path:
        return self._root / f"family-{family_id}.json"

    def get(self, family_id: str) -> dict | None:
        path = self._path(family_id)
        if not path.exists():
            return None
        meta = _load_json_record(path, kind="family")
        if meta.get("family_id") != family_id:
            return None
        return dict(meta)

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("family-*.json")):
            try:
                records.append(dict(_load_json_record(path, kind="family")))
            except RegistryIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("registered_at", ""), meta.get("family_id", "")))
        return records, errors

    def record(self, fields: dict) -> dict:
        family_id = fields["family_id"]
        path = self._path(family_id)
        if path.exists():
            try:
                _load_json_record(path, kind="family")
            except RegistryIntegrityError:
                raise
            raise FamilyAlreadyRecorded(family_id)
        return _write_json_record(self._root, path, fields, kind="family")


class HypothesisStore:
    """File-based store rooted at the resolved registry directory, ``hypothesis-*.json`` files
    only. No update/delete method exists anywhere on this class (structural); ``record`` refuses
    an already-present ``hypothesis_id`` (``HypothesisAlreadyRecorded``, TC-2's own duplicate
    check)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, hypothesis_id: str) -> Path:
        return self._root / f"hypothesis-{hypothesis_id}.json"

    def get(self, hypothesis_id: str) -> dict | None:
        path = self._path(hypothesis_id)
        if not path.exists():
            return None
        meta = _load_json_record(path, kind="hypothesis")
        if meta.get("hypothesis_id") != hypothesis_id:
            return None
        return dict(meta)

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("hypothesis-*.json")):
            try:
                records.append(dict(_load_json_record(path, kind="hypothesis")))
            except RegistryIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(
            key=lambda meta: (meta.get("registered_at", ""), meta.get("hypothesis_id", ""))
        )
        return records, errors

    def record(self, fields: dict) -> dict:
        hypothesis_id = fields["hypothesis_id"]
        path = self._path(hypothesis_id)
        if path.exists():
            try:
                _load_json_record(path, kind="hypothesis")
            except RegistryIntegrityError:
                raise
            raise HypothesisAlreadyRecorded(hypothesis_id)
        return _write_json_record(self._root, path, fields, kind="hypothesis")


class WithdrawalStore:
    """File-based store rooted at the resolved registry directory, ``withdrawal-*.json`` files
    only, keyed by ``hypothesis_id`` -- one withdrawal per hypothesis, structurally (a second
    withdrawal attempt collides on the SAME deterministic path, refused the identical way a
    genuine duplicate would be -- ``withdraw_hypothesis`` below surfaces this as
    ``WithdrawalRefused``). No update/delete method exists anywhere on this class."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, hypothesis_id: str) -> Path:
        return self._root / f"withdrawal-{hypothesis_id}.json"

    def get(self, hypothesis_id: str) -> dict | None:
        path = self._path(hypothesis_id)
        if not path.exists():
            return None
        return dict(_load_json_record(path, kind="withdrawal"))

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("withdrawal-*.json")):
            try:
                records.append(dict(_load_json_record(path, kind="withdrawal")))
            except RegistryIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(
            key=lambda meta: (meta.get("withdrawn_at", ""), meta.get("hypothesis_id", ""))
        )
        return records, errors

    def record(self, fields: dict) -> dict:
        hypothesis_id = fields["hypothesis_id"]
        path = self._path(hypothesis_id)
        if path.exists():
            return None  # caller (withdraw_hypothesis) turns this into WithdrawalRefused
        return _write_json_record(self._root, path, fields, kind="withdrawal")


class CertificateStore:
    """File-based store rooted at the resolved registry directory, ``certificate-*.json`` files
    only. SHAPE-only this iteration (J-08 mints for real) -- no update/delete method exists
    anywhere on this class; ``record`` refuses an already-present ``certificate_id``
    (``CertificateAlreadyRecorded``, TC-12)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, certificate_id: str) -> Path:
        return self._root / f"certificate-{certificate_id}.json"

    def get(self, certificate_id: str) -> dict | None:
        path = self._path(certificate_id)
        if not path.exists():
            return None
        meta = _load_json_record(path, kind="certificate")
        if meta.get("certificate_id") != certificate_id:
            return None
        return dict(meta)

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("certificate-*.json")):
            try:
                records.append(dict(_load_json_record(path, kind="certificate")))
            except RegistryIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: meta.get("certificate_id", ""))
        return records, errors

    def record(self, fields: dict) -> dict:
        certificate_id = fields["certificate_id"]
        path = self._path(certificate_id)
        if path.exists():
            try:
                _load_json_record(path, kind="certificate")
            except RegistryIntegrityError:
                raise
            raise CertificateAlreadyRecorded(certificate_id)
        return _write_json_record(self._root, path, fields, kind="certificate")


# === registration: family (create-if-absent, verified-if-present) + hypothesis, one act ===============


def _require(payload: dict, field: str) -> object:
    value = payload.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise HypothesisMalformed(f"missing required field {field!r}")
    return value


def _validate_hypothesis_payload(payload: dict) -> None:
    for field in _REQUIRED_HYPOTHESIS_FIELDS:
        _require(payload, field)
    evidence_family = payload["evidence_family"]
    if evidence_family not in _EVIDENCE_FAMILIES:
        raise HypothesisMalformed(
            f"unknown evidence_family {evidence_family!r} -- expected one of "
            f"{sorted(_EVIDENCE_FAMILIES)}"
        )
    estimand = payload["estimand"]
    if estimand not in _ESTIMANDS:
        raise HypothesisMalformed(f"unknown estimand {estimand!r} -- expected one of {sorted(_ESTIMANDS)}")
    side = payload["side"]
    if side not in _SIDES:
        raise HypothesisMalformed(f"unknown side {side!r} -- expected one of {sorted(_SIDES)}")
    sidedness = payload["sidedness"]
    if sidedness not in _SIDEDNESS_VALUES:
        raise HypothesisMalformed(
            f"unknown sidedness {sidedness!r} -- expected one of {sorted(_SIDEDNESS_VALUES)}"
        )
    if not isinstance(payload["family_candidate_hypothesis_ids"], list) or not payload[
        "family_candidate_hypothesis_ids"
    ]:
        raise HypothesisMalformed("family_candidate_hypothesis_ids must be a non-empty list")
    target_sessions = payload["target_sessions"]
    if not isinstance(target_sessions, int) or target_sessions < REFEREE_MIN_SESSIONS:
        raise HypothesisMalformed(
            f"target_sessions ({target_sessions!r}) must be an int >= REFEREE_MIN_SESSIONS "
            f"({REFEREE_MIN_SESSIONS})"
        )
    min_occurrences = payload["min_occurrences"]
    if not isinstance(min_occurrences, int) or min_occurrences < REFEREE_MIN_OCCURRENCES:
        raise HypothesisMalformed(
            f"min_occurrences ({min_occurrences!r}) must be an int >= REFEREE_MIN_OCCURRENCES "
            f"({REFEREE_MIN_OCCURRENCES})"
        )


_NULL_MATCHED_ESTIMANDS = frozenset({"A", "C"})


def _validate_spec_ids(payload: dict) -> None:
    """``test_spec_id`` is required for every hypothesis. ``null_spec_id`` is required (and
    validated against the pinned set) only for a PLAYBOOK-family hypothesis whose estimand is A
    or C -- the two estimands spec Sec3.1/Sec3.3 define as "vs a ToD/context-matched null".
    Estimand B is a cell-vs-complement comparison with NO null population at all (spec Sec3.2:
    "Among occurrences of setup S ... do occurrences in context cell C differ from same-setup
    occurrences outside C?" -- spec Sec7's own S-4 table row names no null either, unlike
    S-1/S-2/S-3/S-5) -- any ``null_spec_id`` supplied for a B hypothesis is ignored, mirroring how
    ``context_predicate`` is scoped to B/C only rather than validated for every estimand."""
    test_spec_id = payload["test_spec_id"]
    if test_spec_id not in _TEST_SPEC_IDS:
        raise UnknownSpecId(
            f"unknown test_spec_id {test_spec_id!r} -- expected one of {sorted(_TEST_SPEC_IDS)}"
        )
    if payload["evidence_family"] == "playbook" and payload["estimand"] in _NULL_MATCHED_ESTIMANDS:
        null_spec_id = payload.get("null_spec_id")
        if null_spec_id not in _NULL_SPEC_IDS:
            raise UnknownSpecId(
                f"unknown null_spec_id {null_spec_id!r} -- expected one of {sorted(_NULL_SPEC_IDS)}"
            )


def _validate_context_predicate(payload: dict) -> dict | None:
    """Estimand A: no context predicate (any given value is ignored -- A is unconditional).
    Estimand B/C: a context predicate is REQUIRED and its ``backing_bucket`` must be a member of
    the fixed vocabulary (spec Sec3.3's refusal clause; the Build Notes' own structural-check
    ruling -- never a live ``BandMapResolver`` call at registration time, since no concrete
    symbol/session exists yet to resolve one against)."""
    if payload["estimand"] not in _CONTEXTUAL_ESTIMANDS:
        return None
    predicate = payload.get("context_predicate")
    if not isinstance(predicate, dict):
        raise HypothesisMalformed(
            f"estimand {payload['estimand']!r} requires a context_predicate dict naming a "
            f"backing_bucket"
        )
    backing_bucket = predicate.get("backing_bucket")
    if backing_bucket not in PLAYBOOK_CONTEXT_BACKING_BUCKETS:
        raise HypothesisMalformed(
            f"context_predicate names backing_bucket {backing_bucket!r}, not evaluable at anchor "
            f"bars from recorded data -- expected one of {sorted(PLAYBOOK_CONTEXT_BACKING_BUCKETS)}"
        )
    return dict(predicate)


def _resolve_boundary(payload: dict, registered_at: str) -> str:
    """The boundary is ALWAYS the ET calendar date of ``registered_at`` (spec Sec5's own
    definitional equality) -- an explicit ``confirmation_start_boundary`` in the payload is never
    stored as-is; it exists only so a defensive/adversarial payload trying to set the boundary AT
    OR BEFORE the honest value is caught and refused (TC-4) rather than silently accepted or
    silently ignored. A supplied value strictly AFTER the honest one is not a documented feature
    (spec names no such thing) and is likewise ignored -- the returned value is always exactly
    ``computed``."""
    computed = _et_session_date(_epoch_from_iso(registered_at))
    override = payload.get("confirmation_start_boundary")
    if override is not None and override <= computed:
        raise RetroactiveBoundary(
            f"confirmation_start_boundary {override!r} is at or before the ET calendar date of "
            f"registered_at ({computed!r}) -- the boundary is derived, never chosen"
        )
    return computed


def _validate_family_consistency(family_store: FamilyStore, payload: dict) -> dict | None:
    """Read-only: validates the payload's own family fields (q range, hypothesis membership, and
    -- if the family already exists -- agreement with its already-recorded q/candidate list)
    WITHOUT writing anything. Returns the existing family record, or ``None`` when this would be
    the family's first sighting (the caller creates it, but only after the confirm gate -- see
    ``register_hypothesis``: no write of ANY kind, family or hypothesis, happens before
    ``confirm is True``)."""
    family_id = payload["family_id"]
    candidate_ids = list(payload["family_candidate_hypothesis_ids"])
    q = float(payload["family_q"])
    if not (0.0 < q <= 1.0):
        raise HypothesisMalformed(f"family_q ({q!r}) must satisfy 0 < q <= 1")
    if payload["hypothesis_id"] not in candidate_ids:
        raise HypothesisMalformed(
            f"hypothesis_id {payload['hypothesis_id']!r} is not among its own family's planned "
            f"candidate list -- no candidate joins a family retroactively"
        )
    existing = family_store.get(family_id)
    if existing is None:
        return None
    if existing["q"] != q or existing["candidate_hypothesis_ids"] != candidate_ids:
        raise HypothesisMalformed(
            f"family {family_id!r} is already recorded with a different q/candidate list -- a "
            f"family's definition can never change after its first registration"
        )
    return existing


def register_hypothesis(
    family_store: FamilyStore,
    hypothesis_store: HypothesisStore,
    payload: dict,
    *,
    confirm: bool,
) -> dict:
    """The registration act (spec Sec5; goal.md J-05 Step 2): validates ``payload`` per every
    refusal class named in the iteration spec, create-if-absent/verify-if-present's the
    hypothesis's own family (see module docstring), and -- only when ``confirm is True`` --
    appends exactly one new FAMILY record (if this is the family's first sighting) and exactly
    one new HYPOTHESIS record. Refuses distinctly, with NO record of ANY kind written, on:
    a missing/out-of-vocabulary required field or a below-floor sample target
    (``HypothesisMalformed``), an unrecognised ``null_spec_id``/``test_spec_id``
    (``UnknownSpecId``), an explicit boundary that disagrees with the honest computed one
    (``RetroactiveBoundary``), a missing/unconfirmed act (``ConfirmationRequired``), or a
    duplicate ``family_id``/``hypothesis_id`` (``FamilyAlreadyRecorded``/
    ``HypothesisAlreadyRecorded``, raised by the stores themselves). Returns the stored
    HYPOTHESIS record (raw fields only -- ``status``/``accrual`` are GET-time fold additions,
    never persisted)."""
    _validate_hypothesis_payload(payload)
    _validate_spec_ids(payload)
    context_predicate = _validate_context_predicate(payload)

    registered_at = payload.get("registered_at") or _iso_utc_now()
    boundary = _resolve_boundary(payload, registered_at)

    # Read-only consistency check BEFORE the confirm gate too -- a caller previewing a payload
    # (confirm=False) still learns whether its family definition is even coherent, matching every
    # OTHER validation class above. It writes nothing: the ACTUAL family write (below) is
    # confirm-gated exactly like the hypothesis write -- "no write of any kind before confirm".
    existing_family = _validate_family_consistency(family_store, payload)

    if confirm is not True:
        raise ConfirmationRequired("hypothesis registration requires confirm=True before any write")

    # A duplicate `hypothesis_id` is a REFUSAL class ("no record written", iteration spec) -- so it
    # must be detected BEFORE the family write below, not only by `hypothesis_store.record()` after
    # it (iter-6 audit, finding B2: registering an already-recorded hypothesis_id under a NEW
    # family_id used to append that family record and only THEN refuse, leaving a permanent,
    # never-deletable phantom family behind a refused registration). The store's own raise stays as
    # the final backstop.
    if hypothesis_store.get(payload["hypothesis_id"]) is not None:
        raise HypothesisAlreadyRecorded(payload["hypothesis_id"])

    if existing_family is None:
        family_store.record(
            {
                "family_id": payload["family_id"],
                "q": float(payload["family_q"]),
                "candidate_hypothesis_ids": list(payload["family_candidate_hypothesis_ids"]),
                "registered_at": registered_at,
            }
        )

    evidence_family = payload["evidence_family"]
    estimand = payload["estimand"]
    detector_basis = current_playbook_detector_basis() if evidence_family == "playbook" else None
    context_algorithm_version = (
        PLAYBOOK_CONTEXT_ALGORITHM_VERSION if estimand in _CONTEXTUAL_ESTIMANDS else None
    )
    null_spec_id = (
        payload.get("null_spec_id")
        if evidence_family == "playbook" and estimand in _NULL_MATCHED_ESTIMANDS
        else None
    )

    fields = {
        "hypothesis_id": payload["hypothesis_id"],
        "family_id": payload["family_id"],
        "registered_at": registered_at,
        "evidence_family": evidence_family,
        "estimand": estimand,
        "setup_id": payload["setup_id"],
        "side": payload["side"],
        "context_predicate": context_predicate,
        "primary_measure_key": payload["primary_measure_key"],
        "primary_horizon": payload["primary_horizon"],
        "sidedness": payload["sidedness"],
        "null_spec_id": null_spec_id,
        "test_spec_id": payload["test_spec_id"],
        "detector_basis": detector_basis,
        "context_algorithm_version": context_algorithm_version,
        "confirmation_start_boundary": boundary,
        "target_sessions": payload["target_sessions"],
        "min_occurrences": payload["min_occurrences"],
        "origin": REFEREE_HYPOTHESIS_ORIGIN,
    }
    return hypothesis_store.record(fields)


# === withdrawal =========================================================================================


def withdraw_hypothesis(
    hypothesis_store: HypothesisStore,
    withdrawal_store: WithdrawalStore,
    *,
    hypothesis_id: str,
    reason: str | None = None,
    post_boundary_evaluation_exists: bool = False,
    withdrawn_at: str | None = None,
) -> dict:
    """The withdrawal act (spec Sec5): refused when ``hypothesis_id`` is unknown, when
    ``post_boundary_evaluation_exists`` is ``True`` (the injected signal -- see module docstring;
    no evaluation store exists until J-06), or when a withdrawal is already on file. An accepted
    withdrawal appends exactly one WITHDRAWAL record and changes nothing else about the
    (immutable) hypothesis record itself."""
    hypothesis = hypothesis_store.get(hypothesis_id)
    if hypothesis is None:
        raise WithdrawalRefused(f"unknown hypothesis_id {hypothesis_id!r}")
    if post_boundary_evaluation_exists:
        raise WithdrawalRefused(
            f"hypothesis {hypothesis_id!r} has a post-boundary evaluation on record -- withdrawal "
            f"is refused; it remains active and folds as p=1 in its family's BH pass"
        )
    fields = {
        "hypothesis_id": hypothesis_id,
        "withdrawn_at": withdrawn_at or _iso_utc_now(),
        "reason": reason,
    }
    recorded = withdrawal_store.record(fields)
    if recorded is None:
        raise WithdrawalRefused(f"hypothesis {hypothesis_id!r} is already withdrawn")
    return recorded


# === the read-side fold: GET /research/desk/referee/registry =========================================


def _signal_matches_hypothesis_cell(
    hypothesis: dict, signal: dict, *, context_resolver: BandMapResolver | None,
) -> bool:
    """goal-referee-iter-9 rider: ``True`` iff ``signal`` belongs to ``hypothesis``'s own
    ``(setup_id, side[, context_predicate])`` cell -- the SAME context_predicate/backing-bucket
    check ``_starter_context_readiness`` already applies for the shortlist's own live readiness,
    now shared by BOTH ``_hypothesis_accrual`` and ``_hypothesis_discovery`` below (one helper,
    never two independently-drifting pooling walks) so a B/C hypothesis's registry-row numbers
    agree with its own shortlist row's live readiness for the identical cell. Estimand A
    (``context_predicate`` is ``None``) is a plain ``(setup_id, side)`` match, unchanged from
    before this rider. A B/C hypothesis whose context cannot be resolved at all (no
    ``context_resolver`` supplied, or the signal's own band map cannot be resolved) is honestly
    EXCLUDED, never assumed a match (T-5)."""
    if signal["setup_id"] != hypothesis["setup_id"] or signal["side"] != hypothesis["side"]:
        return False
    context_predicate = hypothesis.get("context_predicate")
    if context_predicate is None:
        return True
    if context_resolver is None:
        return False
    cell = resolve_occurrence_backing_bucket(
        signal, signal["symbol"], _epoch_from_iso(signal["trigger_ts"]),
        signal.get("entry"), hypothesis["side"], context_resolver,
    )
    return cell == context_predicate["backing_bucket"]


def _hypothesis_accrual(
    hypothesis: dict,
    newest_by_date: dict[str, dict],
    *,
    live_basis: str,
    config_fingerprint: str,
    context_resolver: BandMapResolver | None = None,
) -> dict:
    """The disclosed readiness PROXY (module docstring): distinct post-boundary ``session_date``s
    carrying >=1 observation in this hypothesis's own ``(setup_id, side[, context_predicate])``
    cell (goal-referee-iter-9 rider: a B/C hypothesis's own context predicate now applies here
    too, via the shared ``_signal_matches_hypothesis_cell`` helper), walked against an
    ALREADY-scanned ``newest_by_date`` map (never a second ``PlaybookStore.list()`` call --
    ``registry_response`` below scans exactly once and folds every hypothesis against that one
    scan) using the SAME shared pooling primitives ``playbook_occurrence_readiness`` itself uses."""
    boundary = hypothesis["confirmation_start_boundary"]
    informative_dates: set[str] = set()
    for session_date, record in newest_by_date.items():
        if session_date <= boundary:
            continue  # strictly after the boundary (spec Sec5)
        record_basis = _record_detector_basis(record)
        if _is_stale_basis(
            record_basis,
            record["config_fingerprint"],
            live_basis=live_basis,
            live_config_fingerprint=config_fingerprint,
        ):
            continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
        for signal in record["signals"]:
            if _signal_matches_hypothesis_cell(hypothesis, signal, context_resolver=context_resolver):
                informative_dates.add(session_date)
                break

    pinned_basis = hypothesis.get("detector_basis")
    basis_current = (
        True
        if pinned_basis is None
        else not _is_stale_basis(
            pinned_basis, config_fingerprint, live_basis=live_basis, live_config_fingerprint=config_fingerprint
        )
    )
    return {
        "informative_post_boundary_sessions": len(informative_dates),
        "target_sessions": hypothesis["target_sessions"],
        "is_proxy": True,
        "basis_current": basis_current,
    }


def _hypothesis_discovery(
    hypothesis: dict,
    newest_by_date: dict[str, dict],
    *,
    live_basis: str,
    config_fingerprint: str,
    context_resolver: BandMapResolver | None = None,
) -> dict:
    """The ``discovery (exploratory)`` block (goal.md J-07 Step 4): pre-boundary (``session_date
    <= confirmation_start_boundary``) observations in the hypothesis's own
    ``(setup_id, side[, context_predicate])`` cell (goal-referee-iter-9 rider: the SAME
    context-predicate check ``_hypothesis_accrual`` now applies, via the shared
    ``_signal_matches_hypothesis_cell`` helper) -- the exact COMPLEMENT of ``_hypothesis_accrual``'s
    own post-boundary walk, over the SAME already-scanned ``newest_by_date`` map and the SAME
    current-basis filter (never a second pooling implementation). ``state/assumptions.md``
    (iter-8) rules the stale-basis exclusion applies here too, for consistency with ``accrual``.
    Never contributes to the ``accrual`` block; a deep-backfilled pre-boundary record recorded
    AFTER registration still lands here, keyed on ``session_date`` alone -- never ``recorded_at``
    (TC-10)."""
    boundary = hypothesis["confirmation_start_boundary"]
    n = 0
    discovery_dates: set[str] = set()
    for session_date, record in newest_by_date.items():
        if session_date > boundary:
            continue  # discovery is PRE-boundary only -- accrual's own filter, inverted
        if _is_stale_basis(
            _record_detector_basis(record),
            record["config_fingerprint"],
            live_basis=live_basis,
            live_config_fingerprint=config_fingerprint,
        ):
            continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
        for signal in record["signals"]:
            if _signal_matches_hypothesis_cell(hypothesis, signal, context_resolver=context_resolver):
                n += 1
                discovery_dates.add(session_date)
    return {"n": n, "n_sessions": len(discovery_dates), "label": "discovery (exploratory)"}


def registry_response(
    *,
    family_store: FamilyStore,
    hypothesis_store: HypothesisStore,
    withdrawal_store: WithdrawalStore,
    certificate_store: CertificateStore,
    playbook_store: PlaybookStore,
    config_fingerprint: str,
    bar_store: BarStore | None = None,
    config: Config | None = None,
) -> dict:
    """The whole ``GET /research/desk/referee/registry`` body -- the pinned five-key shape
    (``runs/goal-session-referee/state/blueprint.md`` iter-6/iter-7/iter-8 notes): ``families``,
    ``hypotheses`` (each folded with ``status`` + ``accrual`` + ``discovery``, iter-8 J-07),
    ``withdrawals``, ``certificates``, plus ``integrity_errors`` (iter-7 Rider 2, audit gap B4).
    Never 404/500 on an empty or
    partially-corrupted registry (the desk router's established never-404-on-absence convention;
    ``get_referee_nulls``'s own ``{"records": [...], "integrity_errors": [...]}`` disclosure
    pattern, reused here rather than inventing a second shape -- each of the four stores' own
    ``.list()`` errors is tagged with its ``store`` kind and concatenated into ONE flat list, so a
    corrupted file is surfaced explicitly instead of silently vanishing from the response.

    ``bar_store``/``config`` (goal-referee-iter-9 rider) are OPTIONAL: supplied by the real route
    so a B/C hypothesis's ``accrual``/``discovery`` can resolve its own context predicate (the
    SAME ``compute=False`` ``BandMapResolver`` lookup ``shortlist_response`` already builds, over
    the ALREADY-RECORDED band map, never a fresh compute, T-8); omitted, every hypothesis in this
    era's own registered set is Estimand A (``context_predicate is None``), which never touches
    the resolver at all -- so every EXISTING caller of this function is unaffected either way."""
    families, family_errors = family_store.list()
    hypotheses, hypothesis_errors = hypothesis_store.list()
    withdrawals, withdrawal_errors = withdrawal_store.list()
    certificates, certificate_errors = certificate_store.list()
    integrity_errors = [
        {"store": store_kind, **error}
        for store_kind, errors in (
            ("family", family_errors),
            ("hypothesis", hypothesis_errors),
            ("withdrawal", withdrawal_errors),
            ("certificate", certificate_errors),
        )
        for error in errors
    ]
    withdrawn_ids = {w["hypothesis_id"] for w in withdrawals}

    live_basis = current_playbook_detector_basis()
    records, _integrity_errors = playbook_store.list()
    newest_by_date = _newest_per_session_date(records)
    context_resolver = (
        BandMapResolver(bar_store, config, compute=False)
        if bar_store is not None and config is not None
        else None
    )

    folded_hypotheses = []
    for hypothesis in hypotheses:
        accrual = _hypothesis_accrual(
            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint,
            context_resolver=context_resolver,
        )
        discovery = _hypothesis_discovery(
            hypothesis, newest_by_date, live_basis=live_basis, config_fingerprint=config_fingerprint,
            context_resolver=context_resolver,
        )
        status = "withdrawn" if hypothesis["hypothesis_id"] in withdrawn_ids else "active"
        folded_hypotheses.append(
            {**hypothesis, "status": status, "accrual": accrual, "discovery": discovery}
        )

    return {
        "families": families,
        "hypotheses": folded_hypotheses,
        "withdrawals": withdrawals,
        "certificates": certificates,
        "integrity_errors": integrity_errors,
    }


# === J-07: the starter-family shortlist -- GET /research/desk/referee/registry/shortlist ==============
#
# goal.md J-07 Step 1 ("serve the shortlist... beside LIVE readiness"). spec Sec7's five candidates
# as PINNED module constants (T-1: never derived, never tunable) -- the exact same field values
# ``test_referee_registry.py``'s own already-established ``_starter_family_payloads()`` helper
# already uses to test the write path (that helper builds REGISTRATION-payload fixtures; these are
# the shortlist's own read-side PRODUCTION constants -- the two serve different purposes,
# state/assumptions.md iter-8). "No hard-coded hypothesis set" (goal.md J-07 Step 2) governs the
# REGISTRATION WRITE PATH staying generic (``register_hypothesis`` already accepts any valid
# hypothesis, never only these five) -- it does not forbid the shortlist's own spec-pinned list from
# existing as a module constant, exactly like ``REFEREE_MIN_SESSIONS`` or the null-spec ids already
# do (state/assumptions.md iter-8).

REFEREE_STARTER_FAMILY_SHORTLIST: tuple[dict, ...] = (
    {
        "candidate_id": "S-1", "estimand": "A", "evidence_family": "playbook",
        "setup_id": "capitulation", "side": "long", "context_predicate": None,
        "primary_measure_key": "5m", "primary_horizon": "5m", "sidedness": "greater",
        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "the book's capitulation claim is the immediate reflexive snapback off climax "
            "exhaustion -- minutes-scale, not session-scale"
        ),
    },
    {
        "candidate_id": "S-2", "estimand": "A", "evidence_family": "playbook",
        "setup_id": "jbe", "side": "long", "context_predicate": None,
        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "jump-base-explosion claims continuation of an established leg -- the follow-through "
            "hour after the base resolves"
        ),
    },
    {
        "candidate_id": "S-3", "estimand": "A", "evidence_family": "playbook",
        "setup_id": "double_top", "side": "short", "context_predicate": None,
        "primary_measure_key": "to_close", "primary_horizon": "to_close", "sidedness": "greater",
        "null_spec_id": REFEREE_NULL_TOD_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "a completed reversal structure claims the session's trend has turned -- always "
            "measurable by construction"
        ),
    },
    {
        "candidate_id": "S-4", "estimand": "B", "evidence_family": "playbook",
        "setup_id": "range_trade", "side": "long",
        "context_predicate": {"backing_bucket": AT_WALL},
        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "a range bounce plays out over the traverse toward the opposite boundary -- to_close "
            "would contaminate with post-breakout regimes"
        ),
    },
    {
        "candidate_id": "S-5", "estimand": "C", "evidence_family": "playbook",
        "setup_id": "range_trade", "side": "long",
        "context_predicate": {"backing_bucket": AT_WALL},
        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
        "null_spec_id": REFEREE_NULL_CONTEXT_SPEC_ID, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "the combined claim: a wall-backed bounce is priced better than chance at that time "
            "and place"
        ),
    },
    # goal-referee-iter-9 rider: spec Sec7's own S-4 row reads "range_trade (registered PER SIDE)
    # at_wall vs other same-setup contexts" -- only the long side shipped at iter-8, dropped
    # without a recorded reason (state/assumptions.md iter-9 entry rules this a plain instruction,
    # not a human-ruling question). The short-side sibling, otherwise byte-identical to S-4
    # (estimand B, same measure/horizon/sidedness/rationale shape), reusing
    # `_starter_context_readiness` verbatim.
    {
        "candidate_id": "S-6", "estimand": "B", "evidence_family": "playbook",
        "setup_id": "range_trade", "side": "short",
        "context_predicate": {"backing_bucket": AT_WALL},
        "primary_measure_key": "1h", "primary_horizon": "1h", "sidedness": "greater",
        "null_spec_id": None, "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
        "target_sessions": REFEREE_MIN_SESSIONS, "min_occurrences": REFEREE_MIN_OCCURRENCES,
        "rationale": (
            "the short-side sibling of S-4 (spec Sec7's own \"registered per side\" wording): a "
            "range bounce plays out over the traverse toward the opposite boundary; to_close "
            "would contaminate with post-breakout regimes"
        ),
    },
)


def _corpus_session_span_days(newest_by_date: dict[str, dict]) -> int:
    """The recorded corpus's own calendar-day span -- earliest recorded ``session_date`` to the
    latest, inclusive -- the denominator each shortlist candidate's own
    ``accrual_rate_sessions_per_day`` divides by. No spec-pinned accrual-rate methodology exists
    (``docs/referee-statistical-spec.md`` Sec7 lists only static authoring-time corpus counts, not
    a formula); this basis -- a candidate's OWN ``n_sessions`` over the WHOLE corpus's own
    trailing day-span -- is disclosed here, not hidden (state/assumptions.md iter-8). Zero when
    the corpus is empty (no session dates recorded at all) -- the caller reads this as its own
    divide-by-zero guard, never crashing (TC-2)."""
    if not newest_by_date:
        return 0
    dates = sorted(newest_by_date)
    earliest = date.fromisoformat(dates[0])
    latest = date.fromisoformat(dates[-1])
    return (latest - earliest).days + 1


def _starter_context_readiness(
    newest_by_date: dict[str, dict],
    config_fingerprint: str,
    *,
    setup_id: str,
    side: str,
    backing_bucket: str,
    context_resolver: BandMapResolver,
) -> tuple[int, int]:
    """LIVE ``(n, n_sessions)`` among ``(setup_id, side)`` occurrences at the CURRENT detector
    basis (T-6) whose OWN entry resolves into ``backing_bucket`` -- the S-4/S-5 shortlist
    candidates' own readiness. Walks the IDENTICAL newest-per-date, current-basis-only raw-record
    set ``playbook_occurrence_readiness()`` already walks (never a second pooling
    implementation), adding ONE per-signal context resolve via the referee-era's own
    already-imported band-context primitive -- ``referee_null.resolve_occurrence_backing_bucket``
    over a ``compute=False`` ``BandMapResolver`` (a RECORDED-band-map lookup, never a fresh
    compute, T-8) -- the SAME primitive ``referee_adjudicate.py``'s own Estimand B/C pooling
    (``_pool_cell_vs_complement``) already calls."""
    live_basis = current_playbook_detector_basis()
    n = 0
    sessions: set[str] = set()
    for session_date, record in newest_by_date.items():
        if _is_stale_basis(
            _record_detector_basis(record),
            record["config_fingerprint"],
            live_basis=live_basis,
            live_config_fingerprint=config_fingerprint,
        ):
            continue  # T-6: pool only at the current (detector_basis, config_fingerprint)
        for signal in record["signals"]:
            if signal["setup_id"] != setup_id or signal["side"] != side:
                continue
            cell = resolve_occurrence_backing_bucket(
                signal, signal["symbol"], _epoch_from_iso(signal["trigger_ts"]),
                signal.get("entry"), side, context_resolver,
            )
            if cell == backing_bucket:
                n += 1
                sessions.add(session_date)
    return n, len(sessions)


def shortlist_response(
    *,
    playbook_store: PlaybookStore,
    config_fingerprint: str,
    bar_store: BarStore,
    config: Config,
) -> dict:
    """The whole ``GET /research/desk/referee/registry/shortlist`` body (J-07): spec Sec7's five
    PINNED candidates (``REFEREE_STARTER_FAMILY_SHORTLIST``) beside LIVE readiness computed fresh
    on every call -- a plain read (GET never computes, T-8; the band-context lookup below is
    ``compute=False``, a lookup over the ALREADY-RECORDED band map, never a fresh map build). n/
    n_sessions for S-1..S-3 (estimand A, no context) reuse ``playbook_occurrence_readiness()``'s
    existing ``per_setup_side`` pooling verbatim; S-4/S-5 (``at_wall`` context) reuse
    ``_starter_context_readiness`` above. ``accrual_rate_sessions_per_day``/
    ``projected_days_to_target`` never divide by zero (TC-2): both read ``0``/``None`` on an empty
    corpus or a zero-eligible cell.

    ``projected_days_to_target`` is ``target_sessions / accrual_rate`` -- measured from ZERO, never
    net of the candidate's own historical ``n_sessions`` (iter-8 audit, finding B2). ``target_
    sessions`` is a POST-BOUNDARY count everywhere it is used (``_hypothesis_accrual``'s
    ``informative_post_boundary_sessions``, ``run_evaluation_and_record``'s own
    ``confirmatory_eligible``), and registering stamps the boundary at that instant -- so not one
    of the historical sessions counted in ``n``/``n_sessions`` above can ever count toward it. A
    projection net of them read ``0.0`` for every candidate whose cell is already rich (all three
    estimand-A candidates, against the real corpus), i.e. "ready now" for a wait that is really
    ``target_sessions`` post-boundary sessions away -- and counted historical observations as
    progress toward a confirmatory target, which the era's own "the historical atlas is exploratory
    forever" anti-goal forbids."""
    readiness = playbook_occurrence_readiness(playbook_store, config_fingerprint)
    per_setup_side = {(cell["setup"], cell["side"]): cell for cell in readiness["per_setup_side"]}

    records, _errors = playbook_store.list()
    newest_by_date = _newest_per_session_date(records)
    corpus_span_days = _corpus_session_span_days(newest_by_date)
    context_resolver = BandMapResolver(bar_store, config, compute=False)

    candidates = []
    for spec in REFEREE_STARTER_FAMILY_SHORTLIST:
        context_predicate = spec["context_predicate"]
        if context_predicate is None:
            cell = per_setup_side.get((spec["setup_id"], spec["side"]))
            n = cell["n"] if cell is not None else 0
            n_sessions = cell["n_sessions"] if cell is not None else 0
        else:
            n, n_sessions = _starter_context_readiness(
                newest_by_date, config_fingerprint,
                setup_id=spec["setup_id"], side=spec["side"],
                backing_bucket=context_predicate["backing_bucket"],
                context_resolver=context_resolver,
            )
        accrual_rate = (n_sessions / corpus_span_days) if corpus_span_days > 0 else 0.0
        projected_days = (
            # From ZERO, never net of the historical n_sessions above -- see the docstring
            # (iter-8 audit, finding B2): the target is a POST-boundary count, and registering
            # stamps the boundary now.
            spec["target_sessions"] / accrual_rate
            if accrual_rate > 0 else None
        )
        candidates.append(
            {
                "candidate_id": spec["candidate_id"],
                "estimand": spec["estimand"],
                "evidence_family": spec["evidence_family"],
                "setup_id": spec["setup_id"],
                "side": spec["side"],
                "context_predicate": context_predicate,
                "primary_measure_key": spec["primary_measure_key"],
                "primary_horizon": spec["primary_horizon"],
                "sidedness": spec["sidedness"],
                "null_spec_id": spec["null_spec_id"],
                "test_spec_id": spec["test_spec_id"],
                "rationale": spec["rationale"],
                "n": n,
                "n_sessions": n_sessions,
                "target_sessions": spec["target_sessions"],
                "min_occurrences": spec["min_occurrences"],
                "accrual_rate_sessions_per_day": accrual_rate,
                "projected_days_to_target": projected_days,
            }
        )
    # goal-referee-iter-9 rider (closes iter-8 coherence-audit F1 WARN): `family_id`/`family_q`
    # served here for the first time -- the starter family's own registration-mechanics fields,
    # previously only an unowned apps/frontend/app/desk/page.tsx literal. The frontend now reads
    # both from this response instead of a local constant.
    return {
        "candidates": candidates,
        "family_id": REFEREE_STARTER_FAMILY_ID,
        "family_q": REFEREE_DEFAULT_Q,
    }


# --- The CLI (register / withdraw) --------------------------------------------------------------------


def _json_arg(value: str | None) -> dict | None:
    if value is None:
        return None
    return json.loads(value)


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m app.research.referee_registry register ...`` /
    ``python -m app.research.referee_registry withdraw ...``. Runs against the operator's real
    playbook/registry dirs, in-process, synchronously -- the CLI warmer precedent every desk/
    referee compute module carries. Running the command IS the explicit act (``confirm=True``
    always, for ``register``) -- unlike the POST route, a CLI invocation has no automated/
    accidental-call surface to guard against."""
    parser = argparse.ArgumentParser(
        description="Referee registry CLI -- registers a hypothesis (through its family) or "
        "withdraws one, append-only, against the SAME durable store GET .../registry serves."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    register = subparsers.add_parser("register", help="register one hypothesis (and its family)")
    register.add_argument("--hypothesis-id", required=True)
    register.add_argument("--family-id", required=True)
    register.add_argument("--family-q", required=True, type=float)
    register.add_argument("--family-candidate-hypothesis-ids", required=True, nargs="+")
    register.add_argument("--evidence-family", required=True, choices=sorted(_EVIDENCE_FAMILIES))
    register.add_argument("--estimand", required=True, choices=sorted(_ESTIMANDS))
    register.add_argument("--setup-id", required=True)
    register.add_argument("--side", required=True, choices=sorted(_SIDES))
    register.add_argument("--context-predicate", default=None, help="JSON object, B/C only")
    register.add_argument("--primary-measure-key", required=True)
    register.add_argument("--primary-horizon", required=True)
    register.add_argument("--sidedness", required=True, choices=sorted(_SIDEDNESS_VALUES))
    register.add_argument("--null-spec-id", default=None, choices=sorted(_NULL_SPEC_IDS) + [None])
    register.add_argument("--test-spec-id", required=True, choices=sorted(_TEST_SPEC_IDS))
    register.add_argument("--target-sessions", required=True, type=int)
    register.add_argument("--min-occurrences", required=True, type=int)
    # NO `--registered-at` flag (iter-6 audit, finding B1): the registration instant is the act's
    # own wall-clock instant, and the boundary is DERIVED from it -- a backdating flag on the
    # operator CLI would defeat the very commitment device this module exists to be (and would
    # make already-recorded historical sessions count as post-boundary accrual). Hermetic tests
    # that need a specific ET instant call `register_hypothesis` directly (TC-8) or freeze
    # `_iso_utc_now` (TC-13); neither is an operator-reachable surface.
    register.add_argument("--confirmation-start-boundary", default=None)

    withdraw = subparsers.add_parser("withdraw", help="withdraw one already-registered hypothesis")
    withdraw.add_argument("--hypothesis-id", required=True)
    withdraw.add_argument("--reason", default=None)
    withdraw.add_argument("--post-boundary-evaluation-exists", action="store_true")

    args = parser.parse_args(argv)
    config = CONFIG
    registry_dir = resolve_referee_registry_dir(config.desk_universe_dir_resolved())
    family_store = FamilyStore(registry_dir)
    hypothesis_store = HypothesisStore(registry_dir)
    withdrawal_store = WithdrawalStore(registry_dir)

    if args.action == "register":
        payload = {
            "hypothesis_id": args.hypothesis_id,
            "family_id": args.family_id,
            "family_q": args.family_q,
            "family_candidate_hypothesis_ids": list(args.family_candidate_hypothesis_ids),
            "evidence_family": args.evidence_family,
            "estimand": args.estimand,
            "setup_id": args.setup_id,
            "side": args.side,
            "context_predicate": _json_arg(args.context_predicate),
            "primary_measure_key": args.primary_measure_key,
            "primary_horizon": args.primary_horizon,
            "sidedness": args.sidedness,
            "null_spec_id": args.null_spec_id,
            "test_spec_id": args.test_spec_id,
            "target_sessions": args.target_sessions,
            "min_occurrences": args.min_occurrences,
            "confirmation_start_boundary": args.confirmation_start_boundary,
        }
        record = register_hypothesis(family_store, hypothesis_store, payload, confirm=True)
        print(f"registered hypothesis {record['hypothesis_id']} (family {record['family_id']})")
        return 0

    record = withdraw_hypothesis(
        hypothesis_store,
        withdrawal_store,
        hypothesis_id=args.hypothesis_id,
        reason=args.reason,
        post_boundary_evaluation_exists=args.post_boundary_evaluation_exists,
    )
    print(f"withdrew hypothesis {record['hypothesis_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
