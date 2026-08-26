"""``micro_tick_observations.py`` -- the production TICK observation adapter for walk-forward (r14).

**What this closes.** ``walkforward.py`` takes one abstract input: a flat list of
``{session_date, symbol, value, value_unit}`` observations. Exactly one production reader existed
for that shape -- ``walkforward.playbook_observations``, which reads the BAR corpus. There was no
tick reader at all, so the tick family could be floor-refused but never actually evaluated. This
module is that reader, and nothing more: a narrow adapter from the SAME canonical outcome machinery
Scout already uses onto the observation shape walk-forward already consumes.

**It adds no outcome math.** Every value it emits is ``scout.extract_anchors``' own ``outcome_bps``
-- computed by ``micro_join.outcome_rows_after_trigger`` through ``micro_features.mid_outcome``,
the one canonical, direction-signed, ``return_bps`` outcome path. There is no second formula here,
no re-signing, and no unit conversion: the anchor arrives in ``return_bps`` and leaves in
``return_bps``, and ``walkforward.require_canonical_observation_units`` proves it before returning.

**Four refusals, all fail-closed, all BEFORE any outcome is read:**

1. *Window confinement.* The caller names the session dates it is entitled to read. The corpus
   manifest is narrowed to those dates BEFORE ``extract_anchors`` is called, so the read is
   physically incapable of touching a future fold's window -- not merely filtered afterwards. The
   returned anchors are then re-asserted against the same set (``TickObservationWindowError``),
   because a filter that is only applied at one end is a filter that can silently drift.
2. *Withheld/sealed refusal.* Every requested dataset is tested against
   ``micro_snapshots.withheld_dataset_ids_for_store`` -- the ONE shared withheld predicate -- and a
   withheld or sealed id raises rather than being quietly dropped. Dropping it would shrink the
   corpus behind the caller's back, which is exactly the class of defect the era's denominator rail
   forbids.
3. *Completeness.* A dataset inside the requested window whose snapshot is missing or stale REFUSES
   (``TickObservationIncompleteError``). This is the one place this module deliberately diverges
   from ``scout.extract_anchors``, whose own contract is that a dataset with no current snapshot is
   "an honest skip, not a fabricated row". An honest skip is right for a discovery screen and wrong
   for a fold: a fold that silently evaluates 17 of 20 validation sessions reports a number for a
   window it did not actually measure.
4. *Unit proof.* ``walkforward.require_canonical_observation_units`` runs on the way out.

**Exposure logging (spec §6.7).** Reading a window's outcomes IS serving them, so this reader is the
production boundary where the exposure registry is finally written. Both purposes log -- a TRAIN
read exposes its window exactly as a TEST read does -- which is what makes "a training read
masquerading as a clean test read" structurally impossible: once a window has been read for any
purpose, every spec registered afterwards sees it as exposed and classifies it diagnostic. A TEST
read additionally proves its own ordering: ``logged_at`` must be strictly after the spec's
``registered_at``, so the reveal provably followed the freeze.

Logging is DEDUPED per ``(corpus_id, window)``: the registry answers "has this window ever been
served", a boolean, so a second row adds no information and an append-only ledger must not grow
without bound under a Mode A sequence that re-reads the same training window at every origin.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..config import Config
from .datasets import DatasetStore
from .micro_accessor import (
    ExposureRegistry,
    require_corpus_exposure_baseline,
)
from .micro_snapshots import exclude_withheld, load_snapshot_meta
from . import micro_features as mf
from . import scout
from . import walkforward as wf

__all__ = [
    "PURPOSE_TRAIN",
    "PURPOSE_TEST",
    "UnsidedCandidateError",
    "TickObservationWindowError",
    "TickObservationWithheldError",
    "TickObservationIncompleteError",
    "TickObservationOrderingError",
    "manifest_for_sessions",
    "log_window_exposure",
    "tick_observations_for_sessions",
]

PURPOSE_TRAIN = "train"
PURPOSE_TEST = "test"
_PURPOSES = (PURPOSE_TRAIN, PURPOSE_TEST)

_EXPOSURE_SURFACE = "walkforward_tick_observation_read"


class TickObservationWindowError(Exception):
    """An observation was produced for a session date outside the explicitly requested window --
    refused. Purge is asserted at BOTH ends of this reader, never assumed from one filter."""


class TickObservationWithheldError(Exception):
    """A requested dataset is a withheld/sealed member of an unresolved registered-universe pool --
    refused, never silently excluded. Carries the COUNT and the requested session dates, never the
    withheld dataset ids (spec §7.5)."""


class TickObservationIncompleteError(Exception):
    """A dataset inside the requested window has no CURRENT snapshot, so its sessions cannot be
    measured -- refused. A fold must never report an effect for a window it only partly read."""


class UnsidedCandidateError(Exception):
    """r14: this reader was handed an UNSIDED candidate (``sidedness is None``) -- refused.

    ``micro_features.validate_candidate_direction`` deliberately admits ``None``: an unsided
    exploratory Scout candidate is a legal, meaningful thing, and Scout screens plenty of them. It
    is NOT meaningful here. This reader feeds Mode B, which evaluates an already-frozen directed
    hypothesis, and the outcome signer needs a direction to sign against -- so the vocabulary
    validator's own tolerance has to be narrowed at this boundary rather than relied on."""


class TickObservationOrderingError(Exception):
    """A test-window read was asked to log its exposure at an instant that is not strictly after
    the spec's own ``registered_at`` -- refused: the whole point of the reveal-after-freeze order is
    that the ledger can prove it happened."""


def _session_date_of(meta: dict) -> str:
    """The dataset's own ET session date, from its already-verified ``window_start_utc`` -- the
    identical conversion ``micro_readiness._et_datetime``/``scout``'s own private helper use."""
    parsed = datetime.fromisoformat(meta["window_start_utc"].replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(scout._ET_ZONE).date().isoformat()


def manifest_for_sessions(
    dataset_store: DatasetStore,
    *,
    session_dates: list[str] | set[str],
    records: list[dict] | None = None,
) -> list[dict]:
    """The corpus manifest NARROWED to ``session_dates`` -- the confinement in refusal 1, applied
    before any read. Raises ``TickObservationWithheldError`` if any dataset whose session date falls
    inside the window is withheld, rather than dropping it.

    ``records`` lets a caller that already holds a verified ``DatasetStore.list()`` pass it in
    rather than paying a second full inventory (the r14 performance rail); omitted, one is taken."""
    wanted = set(session_dates)
    if records is None:
        records, _errors = dataset_store.list()
    in_window = [meta for meta in records if _session_date_of(meta) in wanted]
    # `exclude_withheld` is the ONE shared exclusion primitive every corpus enumerator uses (spec
    # §7.5 point 6) -- consumed here rather than `withheld_dataset_ids_for_store` so this reader
    # takes NO second inventory of its own, and so it can never drift into a private copy of "is
    # this withheld". What differs is only what we do with the answer: every other enumerator
    # EXCLUDES and discloses a count, and a fold REFUSES.
    kept, withheld_count = exclude_withheld(in_window, dataset_store)
    if withheld_count:
        raise TickObservationWithheldError(
            f"{withheld_count} dataset(s) inside the requested {len(wanted)}-session window are "
            "withheld members of an unresolved registered-universe pool -- refused (spec §7.5 "
            "point 6): a fold never silently evaluates a corpus a withheld shard was quietly "
            "removed from. Release or exclude those session dates explicitly."
        )
    return [{"dataset_id": meta["id"], "checksum": meta["checksum"]} for meta in kept]


def _require_complete_snapshots(
    corpus_manifest: list[dict],
    *,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
) -> None:
    """Refusal 3. Every dataset in the (already window-narrowed) manifest must carry a CURRENT
    snapshot -- ``load_snapshot_meta`` is the same TR-7 re-verification ``scout.extract_anchors``
    consults, read here for a different decision: Scout skips, a fold refuses."""
    missing = [
        entry["dataset_id"]
        for entry in corpus_manifest
        if load_snapshot_meta(snapshots_dir, dataset_store, entry["dataset_id"], config) is None
    ]
    if missing:
        raise TickObservationIncompleteError(
            f"{len(missing)} of {len(corpus_manifest)} dataset(s) in the requested window have no "
            "CURRENT snapshot -- refused (r14 completeness): a fold that silently skipped them "
            "would report an effect for sessions it never measured. Build the snapshots first."
        )


def log_window_exposure(
    exposure_registry: ExposureRegistry,
    *,
    corpus_id: str,
    session_dates: list[str] | set[str],
    logged_at: str,
    purpose: str,
    spec_registered_at: str | None = None,
) -> list[str]:
    """Append ONE exposure entry per session date this read actually revealed, and return the dates
    newly logged (spec §6.7).

    Deduped against the registry's existing rows for the same ``(corpus_id, window)``: exposure is a
    boolean fact, so a second row carries no information while an append-only ledger under a Mode A
    sequence that re-reads one training window at every origin would otherwise grow without bound.

    For ``PURPOSE_TEST`` the ordering is PROVED, not assumed: ``logged_at`` must be strictly after
    ``spec_registered_at``. That is what makes a later reader able to see that the validation window
    was revealed after the spec froze, rather than having to take it on trust."""
    if purpose not in _PURPOSES:
        raise ValueError(f"purpose {purpose!r} is outside the closed vocabulary {_PURPOSES!r}")
    if purpose == PURPOSE_TEST:
        if not spec_registered_at:
            raise TickObservationOrderingError(
                "a test-window read must supply the spec's own registered_at -- refused (r14): "
                "without it the reveal-after-freeze order cannot be proved"
            )
        if not logged_at > spec_registered_at:
            raise TickObservationOrderingError(
                f"exposure logged_at {logged_at!r} is not strictly after the spec's registered_at "
                f"{spec_registered_at!r} -- refused (r14): a validation window's exposure must "
                "provably follow the freeze it was revealed after"
            )
    already = {
        row.get("window")
        for row in exposure_registry.all_rows()
        if row.get("corpus_id") == corpus_id and row.get("window") is not None
    }
    newly: list[str] = []
    for window in sorted(set(session_dates)):
        if window in already:
            continue
        exposure_registry.log_exposure(
            corpus_id=corpus_id,
            window=window,
            surface=f"{_EXPOSURE_SURFACE}:{purpose}",
            logged_at=logged_at,
        )
        newly.append(window)
    return newly


def tick_observations_for_sessions(
    *,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    session_dates: list[str],
    feature_name: str,
    structure_context_kind: str,
    horizon_key: str,
    sidedness: str,
    exposure_registry: ExposureRegistry,
    corpus_id: str,
    purpose: str,
    logged_at: str,
    spec_registered_at: str | None = None,
    records: list[dict] | None = None,
    rows_cache: dict[str, list[dict]] | None = None,
    resolver=None,
    playbook_store=None,
    setup_id: str | None = None,
) -> dict:
    """The production tick observation read for ONE explicitly named set of session dates.

    Returns ``{"observations", "session_dates", "datasets_read", "exposure_windows_logged"}`` --
    ``observations`` in walk-forward's canonical shape, everything else disclosure so a caller can
    report WHAT was read rather than assert it.

    ``sidedness`` is validated first and is a required ``long``/``short``: this reader feeds Mode B,
    which evaluates an already-frozen, already-directed hypothesis. ``validate_candidate_direction``
    admits ``None`` (a legal unsided Scout candidate); this boundary does not."""
    mf.validate_candidate_direction(sidedness)
    if sidedness is None:
        raise UnsidedCandidateError(
            "tick observations were requested for an UNSIDED candidate -- refused: Mode B "
            "evaluates a frozen directed hypothesis, and an unsided candidate has no direction "
            "for the canonical outcome signer to sign against"
        )
    if purpose not in _PURPOSES:
        raise ValueError(f"purpose {purpose!r} is outside the closed vocabulary {_PURPOSES!r}")
    # r14: the corpus must be able to speak honestly about its own exposure history before this
    # read contributes to it. A corpus that is neither r2-initialized nor registered-fresh refuses.
    require_corpus_exposure_baseline(exposure_registry, corpus_id)

    requested = sorted(set(session_dates))
    corpus_manifest = manifest_for_sessions(
        dataset_store, session_dates=requested, records=records
    )
    _require_complete_snapshots(
        corpus_manifest,
        dataset_store=dataset_store,
        snapshots_dir=snapshots_dir,
        config=config,
    )

    anchors = scout.extract_anchors(
        feature_name=feature_name,
        structure_context_kind=structure_context_kind,
        horizon_key=horizon_key,
        sidedness=sidedness,
        corpus_manifest=corpus_manifest,
        dataset_store=dataset_store,
        snapshots_dir=snapshots_dir,
        config=config,
        rows_cache=rows_cache,
        resolver=resolver,
        playbook_store=playbook_store,
        setup_id=setup_id,
    )
    # The anchors' own unit provenance, read off the rows rather than assumed from this module's
    # own constant (the r13 contract-pass rule, reused verbatim -- never a second unit assertion).
    scout.require_canonical_anchor_units(anchors)

    allowed = set(requested)
    observations: list[dict] = []
    for anchor in anchors:
        session_date = anchor.get("session_date")
        if session_date not in allowed:
            raise TickObservationWindowError(
                f"anchor with session_date={session_date!r} is outside the requested window -- "
                "refused (r14): the manifest was narrowed before the read, so this can only mean "
                "the read reached past its own window"
            )
        if anchor.get("outcome_bps") is None:
            continue
        observations.append(
            {
                "session_date": session_date,
                "symbol": anchor["symbol"],
                "value": anchor["outcome_bps"],
                "value_unit": mf.OUTCOME_UNIT,
            }
        )
    wf.require_canonical_observation_units(observations)

    newly_logged = log_window_exposure(
        exposure_registry,
        corpus_id=corpus_id,
        session_dates=requested,
        logged_at=logged_at,
        purpose=purpose,
        spec_registered_at=spec_registered_at,
    )
    return {
        "observations": observations,
        "session_dates": requested,
        "datasets_read": len(corpus_manifest),
        "exposure_windows_logged": newly_logged,
    }
