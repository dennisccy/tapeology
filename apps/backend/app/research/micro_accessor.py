"""``micro_accessor.py`` -- Era "The Rapid Microscope" J-05: the origin-fenced accessor

(``docs/rapid-validation-spec.md`` section 6.1) -- the sole legal door onto the micro snapshot
corpus (and, generically, future vault event data, J-06). Two independent disciplines live here:

**1. The origin fence (TR-3).** ``MicroAccessor(dataset_store, snapshots_dir, config, origin=T)``
refuses -- with a typed error, never an empty result -- any read of a dataset whose OWN session
date (spec section 0: "a session is an ET RTH trading date") falls strictly after ``T``. A dataset
is fenced as a WHOLE unit: a recorded RTH window never spans an ET midnight (the
``micro_readiness.py``/``scout.py`` precedent), so "the dataset's session date" is unambiguous.
``origin=None`` (the DEFAULT) is an explicit, disclosed UNFENCED mode -- see "Two callers, two
disciplines" below.

**2. Sealed-shard invisibility (TR-2 in spirit; the vault itself does not exist until J-06).** A
caller MAY pass ``sealed_dataset_ids`` (a frozenset of dataset ids currently sealed) -- a read of
one of those ids raises ``MicroAccessorSealedShardError`` carrying only the section 7.5 OPAQUE
metadata (``shard_id``, a coarse size bucket, never symbol/date/rows), never the underlying rows.
Empty by default (no vault exists yet), so every EXISTING call site behaves exactly as before this
module existed -- this is the "generic hook a J-06 vault can extend without re-deriving the
discipline" the goal.md IN SCOPE names, proven now on a fixture (TC-2) rather than left unbuilt
and unproven until J-06 lands.

**Two callers, two disciplines (a disclosed interpretation call, T-1) -- corrected iter-17: NO
current production caller constructs an origin-fenced read.** ``micro_join.py`` and ``scout.py``
are re-pointed THROUGH this module this iteration (TR-3's import-ban), but their own
served/ledgered values must stay BYTE-IDENTICAL (TC-4, TC-5) -- they have never been
chronologically fenced, and the corpus they read (the legacy tick corpus) is r2-pre-marked
EXPOSED for its entire span regardless. Fencing them now would be a silent, unrequested behavior
change smuggled into a "just move the import" iteration. So: ``origin=None`` is the UNFENCED mode
those two callers construct (every read passes, exactly today's behavior) and it does NOT log to
the exposure registry either -- appending a hash-chained row on every one of ``scout.
extract_anchors``'s thousands-of-anchors-per-dataset calls would reintroduce exactly the O(n)-
per-read cost the iter-4 audit's perf fixes eliminated, for a registry entry that would be
redundant with r2's own initialization (every window of the legacy/playbook corpus is ALREADY
marked exposed from the moment the registry exists -- see ``ExposureRegistry`` below).
``micro_sealed_evaluation.py`` (J-07/TR-23, iteration 17) is re-pointed through this module too --
its shard read is a POST-exposure, whole-shard outcome recomputation, not a rolling-origin
walk-forward fold, so it is a THIRD ``origin=None`` unfenced caller, not a fenced one.

**The FENCED mode is a real, tested capability of this class -- not a claim that a fenced
production caller exists.** An ``origin`` AND an ``ExposureRegistry`` supplied together make a read
participate in exposure logging (the "was this window ever served before?" question) --
proven directly by ``test_origin_fenced_mode_with_a_registry_logs_exactly_one_exposure_entry``. But
as of iteration 17, confirmed by a direct grep of every ``MicroAccessor(`` construction site in
``app/``, NO production module actually constructs one this way: ``walkforward.py`` itself never
constructs a ``MicroAccessor`` at all -- it works over abstract, caller-supplied ``observations``
per its own "one abstract input" design, never raw snapshot rows directly. The fenced mode remains
exactly what it has always been: a capability this class offers, proven on fixtures, available to a
FUTURE rolling-origin caller -- never (today) an actually-exercised production path.

**The exposure registry (section 6.7, r2).** ``ExposureRegistry`` is a corpus-scoped, hash-chained
ledger (``micro_chain_ledger.HashChainedLedger``) of ``{surface, window, corpus_id, logged_at}``
entries. ``initialize_r2_exposure_registry`` seeds it, ONCE, with every window this era already
knows is exposed -- every session-date of the 155-session playbook corpus and of the 12 legacy
tick symbol-days (TC-14) -- stamped at the r2 revision instant
(``R2_REVISION_INSTANT``, 2026-08-16, this spec revision's own date), so a FRESH walk-forward spec
registered any time after that instant reads those windows as already-exposed with no serving act
required in the current run. A registry for a genuinely NEW corpus_id (e.g. this iteration's own
TR-16 synthetic oracle fixtures) starts EMPTY -- nothing pre-marks a corpus this module has never
heard of, so a spec registered against a freshly-built synthetic corpus can legitimately classify
``historical_oos`` (TC-21, TC-22)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ..config import Config
from .datasets import DatasetNotFound, DatasetStore
from .micro_chain_ledger import HashChainedLedger
from .micro_snapshots import read_snapshot_rows as _raw_read_snapshot_rows

__all__ = [
    "R2_REVISION_INSTANT",
    "MicroAccessorOriginFenceError",
    "MicroAccessorSealedShardError",
    "MicroAccessor",
    "ExposureRegistry",
    "resolve_micro_exposure_registry_dir",
    "initialize_r2_exposure_registry",
    "has_any_exposure_entries",
    "log_exposure_once",
    # r14 -- corpus-era freshness provenance (see `register_fresh_corpus_era`)
    "RECORD_KIND_EXPOSURE",
    "RECORD_KIND_CORPUS_ERA",
    "UnregisteredCorpusEraError",
    "CORPUS_ERA_FROZEN_FIELDS",
    "ConflictingCorpusEraError",
    # r14.2 -- the INVERSE binding: one registered universe may found exactly one corpus era
    "UniverseAlreadyBoundToCorpusError",
    "corpus_era_record_for_universe",
    "register_fresh_corpus_era",
    "fresh_corpus_era_record",
    "corpus_exposure_baseline_established",
    "require_corpus_exposure_baseline",
]

# The r2 spec revision's own date (docs/rapid-validation-spec.md's revision header) -- the instant
# every legacy-corpus/playbook-corpus window is honestly treated as "already exposed" from,
# because their aggregates have in fact been served (readiness, evidence, forward reports) for
# months before this era's spec was even written. Never a wall-clock read at call time -- a fixed,
# named instant, exactly like every other frozen constant in this era.
R2_REVISION_INSTANT = "2026-08-16T00:00:00.000000Z"

_ET_ZONE = ZoneInfo("America/New_York")

_EXPOSURE_REGISTRY_DIR_ENV = "TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR"
_EXPOSURE_LEDGER_FILENAME = "exposure_registry.jsonl"


class MicroAccessorOriginFenceError(Exception):
    """A read was requested for a dataset whose own session date falls strictly after this
    accessor's ``origin`` -- refused, never an empty or silently-truncated result (TC-1)."""


class MicroAccessorSealedShardError(Exception):
    """A read was requested for a dataset id this accessor's view marks ``sealed`` -- refused;
    only section 7.5's opaque metadata is ever attached to this error, never the underlying rows
    (TC-2). Carries ``shard_id`` for a caller that wants to report which shard, never a row."""

    def __init__(self, dataset_id: str) -> None:
        self.opaque_metadata = {"shard_id": dataset_id, "status": "sealed"}
        super().__init__(
            f"dataset {dataset_id!r} is sealed -- only opaque metadata is servable pre-exposure "
            "(section 7.5); the underlying rows are refused"
        )


def _session_date_for_dataset(dataset_meta: dict) -> str:
    """The dataset's own ET session date (spec section 0: "a session is an ET RTH trading date"),
    from ``window_start_utc`` -- the identical small technique ``scout.py``'s own private
    ``_session_date_for_dataset`` and ``micro_readiness.py``'s own ``_et_datetime`` already use
    (mirrored, not imported -- the established "small technical helper, not a measurement rail"
    class of interpretation call those modules' own docstrings already log)."""
    parsed = datetime.fromisoformat(dataset_meta["window_start_utc"].replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(_ET_ZONE).date().isoformat()


def resolve_micro_exposure_registry_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR`` if set, else a ``micro_exposure_registry``
    SIBLING of the caller's already-resolved dataset directory -- the ``resolve_micro_snapshots_
    dir``/``resolve_scout_ledger_dir`` pattern verbatim (the ``TAPEOLOGY_MICRO_*`` family, goal.md
    Constraints; deliberately NOT a ``Config`` field)."""
    override = os.environ.get(_EXPOSURE_REGISTRY_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_exposure_registry")


class ExposureRegistry:
    """A corpus-scoped, hash-chained ledger of exposure entries (spec section 6.7). One physical
    ledger file serves every corpus this process ever touches -- ``corpus_id`` is a field on each
    row, not a separate file per corpus (the ``scout_ledger.py`` "one global chain" precedent) --
    so ``verify_chain()`` proves the WHOLE registry's tamper-evidence in one pass."""

    def __init__(self, root_dir: str) -> None:
        self._ledger = HashChainedLedger(root_dir, _EXPOSURE_LEDGER_FILENAME)

    def verify_chain(self) -> dict:
        return self._ledger.verify_chain()

    def all_rows(self) -> list[dict]:
        return self._ledger.all_rows()

    def log_exposure(self, *, corpus_id: str, window: str, surface: str, logged_at: str) -> dict:
        """Append ONE exposure entry: ``corpus_id`` scopes it, ``window`` is a session-date string
        (spec section 6.2's own ``clustering_unit``), ``surface`` names what served it (a route, a
        CLI, a fold evaluation), ``logged_at`` is the instant it was served -- passed explicitly
        (never read from the wall clock inside this method) so a deterministic caller (a test, or
        the r2 initializer below) reproduces byte-identical rows."""
        return self._ledger.append_row(
            {
                "corpus_id": corpus_id,
                "window": window,
                "surface": surface,
                "logged_at": logged_at,
            }
        )

    def is_exposed_before(self, *, corpus_id: str, window: str, instant: str) -> bool:
        """spec section 6.7's mechanical rule: ``True`` iff SOME exposure entry for
        ``(corpus_id, window)`` carries a ``logged_at`` strictly before ``instant``. A spec's own
        ``registered_at`` is exactly the ``instant`` a caller (``walkforward.py``) passes here to
        decide ``historical_oos`` vs ``historical_exposed_diagnostic`` (TC-13)."""
        for row in self._ledger.all_rows():
            # r14: only a genuine window-exposure row can prove exposure. A corpus-era registration
            # names no window and must never be readable as one.
            if not _is_exposure_row(row):
                continue
            if row.get("corpus_id") == corpus_id and row.get("window") == window and row.get("logged_at") < instant:
                return True
        return False


def initialize_r2_exposure_registry(
    registry: ExposureRegistry,
    *,
    corpus_id: str,
    windows: list[str],
    surface: str = "r2_initialization",
    logged_at: str = R2_REVISION_INSTANT,
) -> int:
    """Seeds ``registry`` with one exposure entry per (already-sorted-by-caller) window of
    ``corpus_id``, stamped at ``logged_at`` (default: the r2 revision instant) -- spec section
    6.7's own r2 initialization: "every window of the playbook bar corpus and of the 12 legacy
    tick symbol-days is pre-marked exposed" (TC-14). Idempotent-in-spirit but NOT content-deduped
    (the ``HashChainedLedger`` primitive's own "no dedup, ever" rule) -- a caller runs this exactly
    ONCE per fresh registry (the compute-manager/CLI wiring's own job, not this function's).
    Returns the count of rows appended."""
    for window in windows:
        registry.log_exposure(corpus_id=corpus_id, window=window, surface=surface, logged_at=logged_at)
    return len(windows)


def log_exposure_once(
    registry: ExposureRegistry,
    *,
    corpus_id: str,
    window: str,
    surface: str,
    logged_at: str,
) -> tuple[dict | None, bool]:
    """r14.2: append ONE exposure row for ``(corpus_id, window)`` unless the window's exposure is
    ALREADY an established fact at or before ``logged_at``. Returns ``(row, appended)``.

    **Why deduped.** A release burns a SESSION WINDOW, and a healthy date carries several members;
    releasing six symbols on one date is one exposure fact, not six. The hash-chained primitive
    offers no dedup of its own (deliberately), so the caller that knows the semantic unit does it
    here.

    **Why "at or before ``logged_at``", not merely "exists".** An existing row stamped LATER than
    this act would leave a gap: a spec registered between the two instants would read the window as
    never-exposed even though this release had already made it inspectable. Only a row that is
    already at or before this instant discharges the obligation; anything later and this appends
    its own, earlier, honest row.

    Never a wall-clock read -- ``logged_at`` is supplied, exactly as ``log_exposure`` requires."""
    for row in registry.all_rows():
        if not _is_exposure_row(row):
            continue
        if (
            row.get("corpus_id") == corpus_id
            and row.get("window") == window
            and row.get("logged_at", "") <= logged_at
        ):
            return dict(row), False
    return (
        registry.log_exposure(
            corpus_id=corpus_id, window=window, surface=surface, logged_at=logged_at
        ),
        True,
    )


def has_any_exposure_entries(registry: ExposureRegistry, corpus_id: str) -> bool:
    """``True`` iff ``registry`` already carries at least one exposure entry for ``corpus_id`` --
    the guard a production caller (``walkforward.run_diagnostic_walkforward``) uses to run
    ``initialize_r2_exposure_registry`` exactly ONCE per corpus per registry: without it, every
    repeated compute-manager trigger against the SAME durable registry would append the whole
    playbook corpus's own window list again, growing the exposure ledger unboundedly on an
    append-only store that (correctly) offers no dedup at the primitive level."""
    # r14: counts genuine exposure rows ONLY. A corpus-era registration must not suppress the r2
    # seeding guard this predicate exists to drive -- byte-identical for every pre-r14 row, which
    # carries no `record_kind` and is an exposure row by default.
    return any(
        _is_exposure_row(row) and row.get("corpus_id") == corpus_id for row in registry.all_rows()
    )


# === r14 -- corpus-era freshness provenance ==========================================================
#
# **The problem.** ``ExposureRegistry`` is honest about a corpus it has heard of and silent about one
# it has not, and those two states looked identical: zero rows. ``scout_candidate_walkforward_floor_
# check`` therefore had to treat an empty registry as "nothing is PROVEN unexposed" and count ZERO
# out-of-sample sessions -- correct for a legacy corpus whose aggregates have been served for months,
# but wrong for a genuinely new corpus era, which starts empty precisely BECAUSE nothing has been
# served. The pre-r14 workaround would have been to serve (and thereby burn) a handful of clean
# sessions just to make the registry non-empty. That destroys evidence to satisfy a predicate, and is
# forbidden.
#
# **The mechanism.** ONE new row kind in the SAME hash-chained registry: a corpus-era registration
# that records "this corpus_id is a deliberately fresh era; its empty exposure history is a FACT
# about the world, not an absence of initialization". It is provenance, never an exposure -- it names
# no window, so it can never make any window read as exposed.
#
# **The invariant, stated exactly.** Empty exposure rows ALONE are never proof of freshness. A corpus
# is baseline-established iff EITHER it carries a corpus-era registration (explicitly fresh) OR it
# already carries at least one genuine exposure row (legacy, r2-initialized). Anything else fails
# closed.
RECORD_KIND_EXPOSURE = "exposure"
RECORD_KIND_CORPUS_ERA = "corpus_era_registration"


class UnregisteredCorpusEraError(Exception):
    """A caller asked for out-of-sample eligibility under a ``corpus_id`` whose exposure history has
    neither been r2-initialized nor explicitly registered as a fresh era -- refused (r14). Unknown
    exposure history is NEVER interpretable as "never exposed" (the §7.8 invariant, applied to the
    exposure registry rather than the vault ledger)."""


def _is_exposure_row(row: dict) -> bool:
    """A genuine window-exposure row. Every pre-r14 row carries no ``record_kind`` at all and is
    therefore an exposure row by default -- so this predicate is byte-compatible with every row
    already on disk, and the r14 corpus-era rows are the only thing it ever excludes."""
    return row.get("record_kind", RECORD_KIND_EXPOSURE) == RECORD_KIND_EXPOSURE


#: r14.1: the frozen identity fields of a corpus-era registration. A re-registration is idempotent
#: ONLY when every one of these is byte-identical; anything else is a conflicting claim about what
#: the corpus IS and refuses. `provenance_note` is deliberately absent -- free text may accompany a
#: registration but may never establish, or alter, what makes it fresh.
CORPUS_ERA_FROZEN_FIELDS = (
    "corpus_id",
    "universe_id",
    "universe_registered_at",
    "rule_commitment",
    "vault_secret_commitment",
    "expected_pair_count",
    "freshness_boundary",
)


class ConflictingCorpusEraError(Exception):
    """r14.1: ``corpus_id`` is already registered under a DIFFERENT bound identity -- refused. A
    corpus id names one specific body of evidence; re-registering it against another universe, rule
    commitment or freshness boundary would silently redefine what every ledgered fold result means.
    """


class UniverseAlreadyBoundToCorpusError(Exception):
    """r14.2: this registered universe already founded a corpus era, and a SECOND corpus id was
    asked to draw from it -- refused.

    **The replay this closes.** r14.1 enforced ``corpus_id -> one universe`` and stopped there. The
    inverse was free, and that is the whole exploit: bind ``corpus_A`` to universe ``U``, evaluate
    it, burn its windows; then bind a brand-new ``corpus_B`` to the SAME ``U``. Because exposure is
    scoped by ``corpus_id``, ``corpus_B`` starts with a pristine, empty exposure namespace over
    physically identical bytes -- and every window that ``corpus_A`` already spent reads
    ``historical_oos`` again. The evidence would be re-earned without re-recording a single tick.

    A universe is the physical body of evidence. It can be spent exactly once, so it may found
    exactly one out-of-sample era. Registering the same ``corpus_id`` again with byte-identical
    frozen fields is an idempotent replay and stays legal (nothing new is claimed); anything that
    would give one universe a second exposure namespace refuses here.

    **Derived from the durable registry, never from process state.** The refusal reads the
    hash-chained corpus-era rows themselves, so it survives a restart, a different process, and a
    different operator -- and it holds when the first era has ZERO exposure rows, because the
    exploit is the fresh NAMESPACE, not the rows already in it."""


def register_fresh_corpus_era(
    registry: "ExposureRegistry",
    *,
    corpus_id: str,
    universe_id: str,
    universe_registered_at: str,
    rule_commitment: str,
    vault_secret_commitment: str,
    expected_pair_count: int,
    freshness_boundary: str,
    registered_at: str,
    provenance_note: str = "",
) -> dict:
    """Append ONE permanent, STRUCTURED corpus-era registration for ``corpus_id`` (r14.1).

    **What r14 got wrong.** The first version took a free-text ``provenance`` string and said, in
    its own docstring, that it never parsed it. That made the registration a bare assertion: a
    caller could point a brand-new ``corpus_id`` at already-exposed legacy datasets, declare it
    fresh, and every downstream class check would agree -- because nothing bound the corpus to any
    physical body of data. Freshness has to be a fact about DATA, not a sentence about intent.

    **What this binds.** Every field above is an identity of the registered recording universe the
    corpus is drawn from: which universe, when it was registered, its nonced ``rule_commitment``,
    its ``vault_secret_commitment``, how many pairs its rule promised, and the ``freshness_boundary``
    a genuine member's ``created_utc`` must reach. ``micro_corpus.register_bound_corpus_era`` is the
    caller that proves those against the actual vault ledger before this row is ever written, and
    ``micro_corpus.eligible_oos_members`` is what turns the binding into a member set.

    ``provenance_note`` is recorded verbatim and is inert: notes may say why, never what.

    Still names NO window, so it remains incapable of making any window read as exposed.

    Idempotent when every ``CORPUS_ERA_FROZEN_FIELDS`` value matches; ``ConflictingCorpusEraError``
    otherwise -- the ``register_universe``/``record_screen_provenance`` discipline, mirrored."""
    fields = {
        "record_kind": RECORD_KIND_CORPUS_ERA,
        "corpus_id": corpus_id,
        "universe_id": universe_id,
        "universe_registered_at": universe_registered_at,
        "rule_commitment": rule_commitment,
        "vault_secret_commitment": vault_secret_commitment,
        "expected_pair_count": int(expected_pair_count),
        "freshness_boundary": freshness_boundary,
        "registered_at": registered_at,
        "provenance_note": provenance_note,
    }
    existing = fresh_corpus_era_record(registry, corpus_id)
    if existing is not None:
        frozen = {k: fields[k] for k in CORPUS_ERA_FROZEN_FIELDS}
        recorded = {k: existing.get(k) for k in CORPUS_ERA_FROZEN_FIELDS}
        if recorded == frozen:
            return existing
        differing = sorted(k for k in CORPUS_ERA_FROZEN_FIELDS if recorded[k] != frozen[k])
        raise ConflictingCorpusEraError(
            f"corpus_id {corpus_id!r} is already registered under a different bound identity "
            f"(differs on: {', '.join(differing)}) -- refused (r14.1): a corpus id names one "
            "specific body of evidence and can never be re-pointed at another"
        )

    # r14.2 -- THE INVERSE. Checked only once the corpus_id itself is proven new: an idempotent
    # replay of an existing era returned above and must never be refused for being bound to the
    # universe it is itself the binding of. A DIFFERENT corpus id reaching this point wants a
    # second, empty exposure namespace over the same physical evidence -- the replay route
    # `UniverseAlreadyBoundToCorpusError` exists to close.
    incumbent = corpus_era_record_for_universe(registry, universe_id)
    if incumbent is not None:
        raise UniverseAlreadyBoundToCorpusError(
            f"universe_id {universe_id!r} already founded corpus era "
            f"{incumbent['corpus_id']!r} (registered {incumbent.get('registered_at')!r}) -- "
            f"refused (r14.2): corpus_id {corpus_id!r} would open a SECOND exposure namespace "
            "over the same physical recordings, so every window the first era already spent "
            "would read as never-exposed again. A universe is spent once and founds one era."
        )
    return registry._ledger.append_row(fields)


def fresh_corpus_era_record(registry: "ExposureRegistry", corpus_id: str) -> dict | None:
    """The FIRST corpus-era registration row for ``corpus_id``, or ``None``. First, not last: an era
    is registered once and its instant is the one a freshness claim is anchored to."""
    for row in registry.all_rows():
        if row.get("record_kind") == RECORD_KIND_CORPUS_ERA and row.get("corpus_id") == corpus_id:
            return row
    return None


def corpus_era_record_for_universe(registry: "ExposureRegistry", universe_id: str) -> dict | None:
    """r14.2: the FIRST corpus era founded on ``universe_id``, or ``None`` if it has founded none.

    The inverse index of ``fresh_corpus_era_record``, and the durable basis of
    ``UniverseAlreadyBoundToCorpusError``. First, not last: the era a universe founded is the one
    that spent it, and a later row (which this module refuses to write anyway) could never
    un-spend it.

    Pre-r14.1 unstructured rows carry no ``universe_id`` and are invisible here -- correct, since
    they bound no universe and therefore spent none."""
    for row in registry.all_rows():
        if row.get("record_kind") != RECORD_KIND_CORPUS_ERA:
            continue
        if row.get("universe_id") and row.get("universe_id") == universe_id:
            return row
    return None


def corpus_exposure_baseline_established(registry: "ExposureRegistry", corpus_id: str) -> bool:
    """r14: whether this registry can speak honestly about ``corpus_id`` at all.

    ``True`` iff the corpus is EITHER explicitly registered as a fresh era OR already carries at
    least one genuine exposure row (the legacy, r2-initialized case). ``False`` is the fail-closed
    answer for a corpus this registry has simply never heard of -- for which "no exposure rows"
    means "no initialization", not "no exposure"."""
    if fresh_corpus_era_record(registry, corpus_id) is not None:
        return True
    return has_any_exposure_entries(registry, corpus_id)


def require_corpus_exposure_baseline(registry: "ExposureRegistry", corpus_id: str) -> None:
    """The typed refusal form of ``corpus_exposure_baseline_established`` -- for a caller that must
    stop rather than silently degrade to a conservative zero."""
    if not corpus_exposure_baseline_established(registry, corpus_id):
        raise UnregisteredCorpusEraError(
            f"corpus_id {corpus_id!r} has no exposure baseline -- refused (r14): it carries neither "
            "a fresh-corpus-era registration nor any exposure entry, so its empty exposure history "
            "proves nothing. Unknown exposure history is never 'never exposed'."
        )


class MicroAccessor:
    """Constructed per-call (or per-run) with an explicit ``origin`` (a session date, or ``None``
    for the disclosed unfenced mode -- module docstring) and an optional sealed-dataset view.
    Owns ONE method this iteration: ``read_snapshot_rows`` -- the sole legal path onto
    ``micro_snapshots.read_snapshot_rows`` (TR-3's import-ban; ``tests/test_micro_accessor.py``'s
    AST source-scan proves no other module imports that name)."""

    def __init__(
        self,
        dataset_store: DatasetStore,
        snapshots_dir: str,
        config: Config,
        *,
        origin: str | None = None,
        sealed_dataset_ids: frozenset[str] = frozenset(),
        exposure_registry: ExposureRegistry | None = None,
        corpus_id: str | None = None,
        surface: str = "micro_accessor",
    ) -> None:
        self._dataset_store = dataset_store
        self._snapshots_dir = snapshots_dir
        self._config = config
        self._origin = origin
        self._sealed_dataset_ids = sealed_dataset_ids
        self._exposure_registry = exposure_registry
        self._corpus_id = corpus_id
        self._surface = surface

    @property
    def origin(self) -> str | None:
        return self._origin

    def read_snapshot_rows(self, dataset_id: str, *, logged_at: str | None = None) -> list[dict]:
        """The origin-fenced, sealed-aware read: raises ``MicroAccessorSealedShardError`` for a
        sealed id (never rows); raises ``MicroAccessorOriginFenceError`` when ``self.origin`` is
        set AND the dataset's own session date falls strictly after it (TC-1); else returns the
        SAME rows ``micro_snapshots.read_snapshot_rows`` always has, unmodified.

        Exposure logging fires ONLY when this accessor was constructed with BOTH ``origin`` and
        ``exposure_registry`` set (module docstring's "two callers, two disciplines") -- the
        unfenced ``micro_join.py``/``scout.py`` re-point never logs, by construction, never by a
        runtime branch a caller could get wrong."""
        if dataset_id in self._sealed_dataset_ids:
            raise MicroAccessorSealedShardError(dataset_id)

        try:
            dataset_meta = self._dataset_store.get(dataset_id)
        except DatasetNotFound:
            raise  # an honest absence -- never fabricated, never silently caught here

        if self._origin is not None:
            session_date = _session_date_for_dataset(dataset_meta)
            if session_date > self._origin:
                raise MicroAccessorOriginFenceError(
                    f"dataset {dataset_id!r} has session_date {session_date!r}, strictly after "
                    f"this accessor's origin {self._origin!r} -- refused (TR-3), never an empty "
                    "or truncated result"
                )
            if self._exposure_registry is not None and self._corpus_id is not None:
                self._exposure_registry.log_exposure(
                    corpus_id=self._corpus_id,
                    window=session_date,
                    surface=self._surface,
                    logged_at=logged_at if logged_at is not None else _iso_utc_now(),
                )

        return _raw_read_snapshot_rows(self._snapshots_dir, dataset_id)


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
