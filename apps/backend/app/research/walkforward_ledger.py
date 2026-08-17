"""``walkforward_ledger.py`` -- Era "The Rapid Microscope" J-05: the fold-spec registry plus the

hash-chained, append-only fold-result/sequence/voiding-event ledger (``docs/rapid-validation-
spec.md`` section 6.2-6.8). Built on ``micro_chain_ledger.HashChainedLedger`` (the SAME shared
primitive ``micro_accessor.ExposureRegistry`` uses -- see that module's own docstring for why a
shared primitive is the right call this iteration, not a duplication of
``scout_ledger.py``'s own, untouched, Scout-specific mechanic).

**One global chain, three row kinds (the ``scout_ledger.py`` "one global chain, not one per
family" precedent, mirrored).** ``fold_spec`` rows (frozen geometry registrations), ``fold_result``
rows (one per constant-rule sequence's per-fold evaluation -- Mode A per-origin refits and Mode B
per-window evaluations alike), and ``voiding_event`` rows (TR-13) all land in ONE physical ledger
file, discriminated by their own ``row_kind`` field -- so ``verify_chain()`` proves the WHOLE
ledger's tamper-evidence (every fold, every kill, every voiding) in a single pass, exactly the
"the denominator never shrinks" guarantee spec section 6 exists to make mechanical.

**Fold-spec freeze (TR-13, TC-6, TC-7, TC-10).** ``register_fold_spec`` computes ``geometry_hash``
(a pure content hash, wall-clock-excluded -- the ``scout_ledger.compute_spec_hash`` precedent) and
refuses ``step_sessions < test_sessions`` (TC-7: pooled statistics over overlapping validation
windows are never constructed) BEFORE writing anything. A corpus_id's fold spec is FROZEN at its
first registration: a second registration with a DIFFERENT geometry is refused
(``FoldGeometryFrozenError``) unless a voiding event for that ``corpus_id`` was recorded first
(TC-10) -- checked by walking the ledger's own append order, never a second, independently-kept
"current geometry" cache."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from .micro_chain_ledger import HashChainedLedger

__all__ = [
    "ROW_KIND_FOLD_SPEC",
    "ROW_KIND_FOLD_RESULT",
    "ROW_KIND_VOIDING_EVENT",
    "ROW_KIND_MODE_B_SPEC",
    "FoldStepTooSmallError",
    "FoldGeometryFrozenError",
    "WalkForwardLedger",
    "compute_geometry_hash",
    "register_fold_spec",
    "record_voiding_event",
    "record_mode_b_predeclaration",
    "mode_b_predeclarations_for_sequence",
    "latest_fold_spec",
    "voiding_events_for_corpus",
    "is_corpus_era_voided",
    "existing_fold_result",
    "append_fold_result",
    "fold_results_for_sequence",
    "sequence_ids_for_corpus",
]

_LEDGER_FILENAME = "walkforward_ledger.jsonl"

ROW_KIND_FOLD_SPEC = "fold_spec"
ROW_KIND_FOLD_RESULT = "fold_result"
ROW_KIND_VOIDING_EVENT = "voiding_event"
ROW_KIND_MODE_B_SPEC = "mode_b_spec"

_GEOMETRY_KEYS = ("train_sessions", "test_sessions", "step_sessions", "embargo_sessions")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class FoldStepTooSmallError(Exception):
    """TC-7: ``step_sessions < test_sessions`` -- refused before any ledger row is written, so
    pooled statistics over overlapping validation windows are never constructed (spec section
    6.2)."""


class FoldGeometryFrozenError(Exception):
    """TC-10 (first half): a corpus_id already carries a registered fold spec with a DIFFERENT
    geometry, and no voiding event has been recorded for it since -- refused (TR-13)."""


class WalkForwardLedger:
    """A thin domain wrapper over ONE ``HashChainedLedger`` -- the module docstring's "one global
    chain, three row kinds" ledger."""

    def __init__(self, root_dir: str) -> None:
        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)

    def verify_chain(self) -> dict:
        return self._chain.verify_chain()

    def all_rows(self) -> list[dict]:
        return self._chain.all_rows()

    def rows_of_kind(self, row_kind: str) -> list[dict]:
        return [row for row in self._chain.all_rows() if row.get("row_kind") == row_kind]

    def append_row(self, fields: dict) -> dict:
        """The pure storage primitive (the ``scout_ledger.ScoutLedger.append_row`` precedent --
        enforces no business rule of its own; ``register_fold_spec``/``record_voiding_event``/
        ``append_fold_result`` below are the validated entry points every production caller uses)."""
        return self._chain.append_row(fields)


def compute_geometry_hash(geometry: dict) -> str:
    """A pure content hash over the geometry's own frozen fields (``_GEOMETRY_KEYS`` -- NOT
    ``embargo_derivation``, a free-text disclosure rather than a numeric geometry component) --
    excludes any wall-clock-derived value, so two genuinely separate registration acts of the
    IDENTICAL geometry (a re-run of the same CLI invocation, TC-6-style) compute the identical
    hash (the ``scout_ledger.compute_spec_hash`` precedent)."""
    return _sha256(_canonical({key: geometry[key] for key in _GEOMETRY_KEYS}))


def latest_fold_spec(ledger: WalkForwardLedger, corpus_id: str) -> dict | None:
    """The most recently registered ``fold_spec`` row for ``corpus_id``, or ``None`` -- append
    order IS registration order (the ledger's own invariant), so the last matching row is the
    latest."""
    matches = [row for row in ledger.rows_of_kind(ROW_KIND_FOLD_SPEC) if row.get("corpus_id") == corpus_id]
    return matches[-1] if matches else None


def voiding_events_for_corpus(ledger: WalkForwardLedger, corpus_id: str) -> list[dict]:
    return [row for row in ledger.rows_of_kind(ROW_KIND_VOIDING_EVENT) if row.get("corpus_id") == corpus_id]


def is_corpus_era_voided(ledger: WalkForwardLedger, corpus_id: str, *, since_registered_at: str | None = None) -> bool:
    """``True`` iff ANY voiding event exists for ``corpus_id`` -- optionally restricted to those
    recorded AT OR AFTER ``since_registered_at`` (a sequence's own ``registered_at``, so a sequence
    frozen and evaluated entirely BEFORE a later voiding event can still be judged on its own
    un-voided history if a caller ever needs that finer question; the coarse "any voiding event on
    this corpus-era at all" -- WF_SURVIVOR_RULE_V1's own condition 5 -- is the ``since_registered_
    at=None`` default)."""
    events = voiding_events_for_corpus(ledger, corpus_id)
    if since_registered_at is None:
        return bool(events)
    return any(event["voided_at"] >= since_registered_at for event in events)


def register_fold_spec(
    ledger: WalkForwardLedger,
    *,
    corpus_id: str,
    corpus_manifest_hash: str,
    geometry: dict,
    clustering_unit: str = "session_date",
    floors: dict,
    registered_at: str | None = None,
) -> dict:
    """Freezes a fold spec for ``corpus_id`` (spec section 6.2): ``{corpus_id,
    corpus_manifest_hash, geometry, clustering_unit, floors, registered_at, geometry_hash}``.
    Refuses ``step_sessions < test_sessions`` (TC-7) and a SECOND, DIFFERENT geometry registered
    for a corpus_id that already carries one without an intervening voiding event (TC-10) --
    BEFORE writing anything either way. Re-registering the IDENTICAL geometry (byte-equal
    ``geometry_hash``) is treated as an idempotent replay: the EXISTING fold spec is returned
    unchanged rather than appending a redundant row (the ``PlaybookStore``/``ForwardStore``
    "an identical key is refused as a NEW registration, but reading back what already exists is
    always fine" spirit, adapted here since a fold spec has no separate `.get()` accessor of its
    own)."""
    if geometry["step_sessions"] < geometry["test_sessions"]:
        raise FoldStepTooSmallError(
            f"step_sessions={geometry['step_sessions']!r} < test_sessions="
            f"{geometry['test_sessions']!r} -- refused (spec section 6.2): pooled statistics over "
            "overlapping validation windows are never constructed"
        )
    geometry_hash = compute_geometry_hash(geometry)

    existing = latest_fold_spec(ledger, corpus_id)
    if existing is not None:
        if existing["geometry_hash"] == geometry_hash:
            return dict(existing)
        if not is_corpus_era_voided(ledger, corpus_id, since_registered_at=existing["registered_at"]):
            raise FoldGeometryFrozenError(
                f"corpus_id {corpus_id!r} already carries a registered fold spec with geometry_hash "
                f"{existing['geometry_hash']!r} (registered {existing['registered_at']!r}); a "
                f"DIFFERENT geometry (hash {geometry_hash!r}) is refused without a recorded voiding "
                "event for this corpus-era (TR-13)"
            )

    fields = {
        "row_kind": ROW_KIND_FOLD_SPEC,
        "corpus_id": corpus_id,
        "corpus_manifest_hash": corpus_manifest_hash,
        "geometry": dict(geometry),
        "clustering_unit": clustering_unit,
        "floors": dict(floors),
        "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
        "geometry_hash": geometry_hash,
    }
    return ledger.append_row(fields)


def record_voiding_event(
    ledger: WalkForwardLedger, *, corpus_id: str, reason: str, voided_at: str | None = None
) -> dict:
    """TC-10 (second half): a permanent, append-only voiding event for ``corpus_id`` -- after this,
    ``is_corpus_era_voided`` reads ``True`` for the corpus-era, which
    WF_SURVIVOR_RULE_V1's own condition 5 makes fatal to EVERY existing survivor state of that
    corpus-era (never a deletion or edit of any prior row -- the voiding is itself permanent
    history, spec section 6.2's own closing sentence)."""
    fields = {
        "row_kind": ROW_KIND_VOIDING_EVENT,
        "corpus_id": corpus_id,
        "reason": reason,
        "voided_at": voided_at if voided_at is not None else _iso_utc_now(),
    }
    return ledger.append_row(fields)


def existing_fold_result(ledger: WalkForwardLedger, *, sequence_id: str, fold_index: int, spec_hash: str) -> dict | None:
    """The already-recorded ``fold_result`` row for this exact ``(sequence_id, fold_index,
    spec_hash)``, or ``None`` -- the identity of ONE evaluation act (a sequence's own fold, under
    one frozen spec). Two rows sharing all three are the SAME evaluation re-executed, never two
    independent pieces of evidence."""
    for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT):
        if (
            row.get("sequence_id") == sequence_id
            and row.get("fold_index") == fold_index
            and row.get("spec_hash") == spec_hash
        ):
            return row
    return None


def mode_b_predeclarations_for_sequence(ledger: WalkForwardLedger, sequence_id: str) -> list[dict]:
    return [row for row in ledger.rows_of_kind(ROW_KIND_MODE_B_SPEC) if row.get("sequence_id") == sequence_id]


def record_mode_b_predeclaration(ledger: WalkForwardLedger, spec: dict) -> dict:
    """spec section 6.5's own "a human-authored spec is registered (LEDGER ROW, spec hash,
    timestamp) FIRST; evaluation then runs on later windows": persists ONE permanent
    ``mode_b_spec`` row for a ``register_mode_b_spec`` result, so the predeclaration is a
    hash-chained, timestamped fact on disk written BEFORE any outcome is read -- not merely an
    ordering the caller asserts in a docstring. A re-registration of the byte-identical spec
    (same ``sequence_id`` AND ``spec_hash``) is an idempotent replay returning the FIRST
    predeclaration row (the ``register_fold_spec`` precedent), so a repeat operator run neither
    grows the ledger nor back-dates -- or forward-dates -- the original registration instant that
    spec section 6.7's ``historical_oos`` rule reads."""
    for row in mode_b_predeclarations_for_sequence(ledger, spec["sequence_id"]):
        if row.get("spec_hash") == spec["spec_hash"]:
            return dict(row)
    return ledger.append_row({"row_kind": ROW_KIND_MODE_B_SPEC, **spec})


def append_fold_result(ledger: WalkForwardLedger, fields: dict) -> dict:
    """Persist ONE permanent ``fold_result`` row -- a thin, explicit entry point (the
    ``scout.register_and_screen_candidate`` -> ``ScoutLedger.append_row`` precedent) so every
    caller (Mode A's per-origin refit, Mode B's per-window evaluation, the diagnostic run, the
    TR-16 oracle proofs) writes through the SAME one function, never a second implementation of
    "what a fold-result row looks like on disk". ``fields`` must already carry ``row_kind`` unset
    -- this function stamps it, refusing to silently overwrite a caller-supplied one that might
    diverge.

    **Re-evaluating the SAME (sequence_id, fold_index, spec_hash) is an idempotent replay** (the
    ``register_fold_spec`` precedent directly above): the EXISTING row is returned unchanged rather
    than appended a second time. Without this, a benign repeat of an operator act -- pressing
    ``POST /research/desk/micro/walkforward/compute`` twice, or re-running the CLI warmer -- would
    append a second physical row per fold, and every downstream consumer that counts rows
    (``sequence_verdict``'s own ``WF_MIN_SUFFICIENT_FOLDS`` floor, ``_pooled_sign_agreement``,
    ``decay_view``'s older-vs-recent split) would silently pool the SAME fold twice: two real
    sufficient folds would read as four, turning an honest "2 < 3 sufficient folds -- refused" into
    a COMPUTED verdict over duplicated evidence. The denominator never shrinks (spec section 6) --
    it must not spuriously GROW either."""
    if "row_kind" in fields:
        raise ValueError("append_fold_result stamps row_kind itself -- do not pass one")
    sequence_id, fold_index, spec_hash = fields.get("sequence_id"), fields.get("fold_index"), fields.get("spec_hash")
    if sequence_id is not None and fold_index is not None and spec_hash is not None:
        already = existing_fold_result(ledger, sequence_id=sequence_id, fold_index=fold_index, spec_hash=spec_hash)
        if already is not None:
            return dict(already)
    return ledger.append_row({"row_kind": ROW_KIND_FOLD_RESULT, **fields})


def fold_results_for_sequence(ledger: WalkForwardLedger, sequence_id: str) -> list[dict]:
    return [row for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT) if row.get("sequence_id") == sequence_id]


def sequence_ids_for_corpus(ledger: WalkForwardLedger, corpus_id: str) -> list[str]:
    """Every DISTINCT ``sequence_id`` ever recorded for ``corpus_id``, in first-seen (append)
    order."""
    seen: list[str] = []
    seen_set: set[str] = set()
    for row in ledger.rows_of_kind(ROW_KIND_FOLD_RESULT):
        if row.get("corpus_id") != corpus_id:
            continue
        sequence_id = row["sequence_id"]
        if sequence_id not in seen_set:
            seen_set.add(sequence_id)
            seen.append(sequence_id)
    return seen
