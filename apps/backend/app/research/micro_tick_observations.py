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
2. *Membership, not exclusion (r14.1).* r14 refused the WHOLE requested window if any dataset on a
   requested date was withheld -- which made the real HMAC architecture unusable, because seal
   assignment is per ``(symbol, session_date)`` and a healthy 8-symbol date is normally MIXED. This
   reader no longer decides what is withheld at all: it is handed a PRECOMMITTED member list, so a
   sealed member is a NON-MEMBER rather than an exclusion. For the legacy corpus that list comes
   from ``legacy_exposed_members`` (through ``exclude_withheld``, the era's one shared exclusion
   primitive); for a bound OOS corpus it comes from ``micro_corpus.eligible_oos_members``, which
   derives it from the universe rule, the HMAC and the frozen release plan. Either way the sealed
   ids never reach this function, so it cannot read one even by accident.
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
    "TickObservationIncompleteError",
    "TickObservationOrderingError",
    "legacy_exposed_members",
    "members_in_window",
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


def legacy_exposed_members(
    dataset_store: DatasetStore,
    *,
    session_dates: list[str] | set[str] | None = None,
    records: list[dict] | None = None,
) -> list[dict]:
    """The member set of the LEGACY exploratory corpus -- every servable dataset, optionally
    narrowed to ``session_dates`` (r14.1).

    The legacy corpus has no registered universe and no release plan: §7.7 makes it permanently
    exploratory, so "what is in it" is simply "what is not withheld". ``exclude_withheld`` is the
    ONE shared exclusion primitive every corpus enumerator uses, consumed here so this module never
    grows a private copy of "is this withheld".

    A BOUND corpus does NOT come through here -- its membership is precommitted by
    ``micro_corpus.eligible_oos_members`` from the universe, the HMAC and the frozen release plan,
    and is handed to the reader already resolved."""
    if records is None:
        records, _errors = dataset_store.list()
    kept, _withheld_count = exclude_withheld(records, dataset_store)
    members = [
        {
            "dataset_id": meta["id"],
            "checksum": meta["checksum"],
            "symbol": meta["symbol"],
            "session_date": _session_date_of(meta),
        }
        for meta in kept
    ]
    if session_dates is not None:
        wanted = set(session_dates)
        members = [m for m in members if m["session_date"] in wanted]
    return sorted(members, key=lambda m: (m["session_date"], m["symbol"], m["dataset_id"]))


def members_in_window(members: list[dict], session_dates: list[str] | set[str]) -> list[dict]:
    """The precommitted members whose own session date is inside the requested window.

    Membership ∩ window, in that order: a dataset must be in the corpus AND in the fold, so the read
    can reach outside neither. A date on which every member happens to be sealed simply contributes
    nothing -- which is the mixed-date case working correctly, not a corpus quietly shrinking,
    because the sealed members were never members of this corpus at all."""
    wanted = set(session_dates)
    return [m for m in members if m["session_date"] in wanted]


def _require_complete_snapshots(
    members: list[dict],
    *,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
) -> None:
    """Every EXPECTED member of this fold's window must carry a CURRENT snapshot -- else refuse.

    This is the one place this module deliberately diverges from ``scout.extract_anchors``, whose
    own contract is that a dataset with no current snapshot is "an honest skip, not a fabricated
    row". An honest skip is right for a discovery screen and wrong for a fold: a fold that silently
    evaluated 17 of 20 expected members reports an effect for a corpus it did not measure.

    "Expected" means the PRECOMMITTED member set, so a sealed sibling on the same date is not a
    missing member -- it was never a member. That distinction is what makes a mixed date usable
    without weakening the completeness guarantee."""
    missing = [
        member["dataset_id"]
        for member in members
        if load_snapshot_meta(snapshots_dir, dataset_store, member["dataset_id"], config) is None
    ]
    if missing:
        raise TickObservationIncompleteError(
            f"{len(missing)} of {len(members)} EXPECTED corpus member(s) in the requested window "
            "have no CURRENT snapshot -- refused (r14 completeness): a fold that silently skipped "
            "them would report an effect for members it never measured. Build the snapshots first."
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
    members: list[dict],
    corpus_id: str,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    session_dates: list[str],
    feature_name: str,
    structure_context_kind: str,
    horizon_key: str,
    sidedness: str,
    exposure_registry: ExposureRegistry,
    purpose: str,
    logged_at: str,
    spec_registered_at: str | None = None,
    rows_cache: dict[str, list[dict]] | None = None,
    resolver=None,
    playbook_store=None,
    setup_id: str | None = None,
) -> dict:
    """The production tick observation read for ONE explicitly named set of session dates, over a
    PRECOMMITTED member set (r14.1).

    ``members`` is the corpus's own eligible-member list -- from
    ``micro_corpus.eligible_oos_members`` for a bound OOS corpus, or ``legacy_exposed_members`` for
    the permanently-exploratory legacy corpus. This function never resolves membership itself and
    never consults the visible store for "what else is on this date": a sealed member's id simply
    never reaches it, which is why a mixed 6-released / 2-sealed date is read as exactly six.

    **Exposure is committed BEFORE the first outcome row is read (r14.1, F).** r14 read the anchors
    and then logged, so a crash in between left a window that had been read while the registry said
    it had not -- and a later spec would then have classified it ``historical_oos``. The order is
    now: validate · resolve the window's members · prove completeness · **append the exposure** ·
    only then read. A read that fails after the precommit leaves the window burned, which is the
    conservative direction: a window wrongly marked exposed costs evidence, a window wrongly marked
    fresh costs the entire scientific claim.

    Returns the observations plus the DISCLOSURE a fold needs to report honestly: which sessions
    were requested, how many members were read, the realized symbol/session breadth of the
    observations themselves, and which exposure windows this read newly burned."""
    mf.validate_candidate_direction(sidedness)
    if sidedness is None:
        raise UnsidedCandidateError(
            "tick observations were requested for an UNSIDED candidate -- refused: Mode B "
            "evaluates a frozen directed hypothesis, and an unsided candidate has no direction "
            "for the canonical outcome signer to sign against"
        )
    if purpose not in _PURPOSES:
        raise ValueError(f"purpose {purpose!r} is outside the closed vocabulary {_PURPOSES!r}")
    # The corpus must be able to speak honestly about its own exposure history before this read
    # contributes to it.
    require_corpus_exposure_baseline(exposure_registry, corpus_id)

    requested = sorted(set(session_dates))
    in_window = members_in_window(members, requested)
    _require_complete_snapshots(
        in_window, dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=config
    )

    # --- F: THE PRECOMMIT. Nothing below this line may run before the registry has recorded that
    # this window is being revealed. ------------------------------------------------------------
    newly_logged = log_window_exposure(
        exposure_registry,
        corpus_id=corpus_id,
        session_dates=requested,
        logged_at=logged_at,
        purpose=purpose,
        spec_registered_at=spec_registered_at,
    )

    corpus_manifest = [
        {"dataset_id": m["dataset_id"], "checksum": m["checksum"]} for m in in_window
    ]
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
    member_ids = {m["dataset_id"] for m in in_window}
    observations: list[dict] = []
    for anchor in anchors:
        session_date = anchor.get("session_date")
        if session_date not in allowed:
            raise TickObservationWindowError(
                f"anchor with session_date={session_date!r} is outside the requested window -- "
                "refused: the manifest was narrowed to this corpus's own members inside this "
                "window before the read, so this can only mean the read reached past it"
            )
        if anchor.get("dataset_id") is not None and anchor["dataset_id"] not in member_ids:
            raise TickObservationWindowError(
                f"anchor from dataset {anchor['dataset_id']!r} is not a member of corpus "
                f"{corpus_id!r} in this window -- refused: purge is asserted at BOTH ends"
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

    return {
        "observations": observations,
        "corpus_id": corpus_id,
        "session_dates": requested,
        "members_expected": len(in_window),
        "datasets_read": len(corpus_manifest),
        "exposure_windows_logged": newly_logged,
        # r14.1 (A): the realized breadth, computed from the observations that actually exist --
        # never assumed from the panel size. On a mixed date the symbol breadth is whatever the
        # HMAC left not-selected, and the fold reports that rather than the panel's 8.
        "realized_breadth": {
            "n_observations": len(observations),
            "n_sessions": len({o["session_date"] for o in observations}),
            "n_symbols": len({o["symbol"] for o in observations}),
            "symbols": sorted({o["symbol"] for o in observations}),
            "sessions_with_observations": sorted({o["session_date"] for o in observations}),
        },
    }
