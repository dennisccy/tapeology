"""Era 6 "The Referee" (J-06) -- estimand engines and adjudication: the LAST module in the chain
J-02 (``referee_evidence.py``) -> J-03 (``referee_stats.py``) -> J-04 (``referee_null.py``) -> J-05
(``referee_registry.py``) built for. Implements ``docs/referee-statistical-spec.md`` Sec3/Sec5/Sec8
verbatim: the three estimand engines (A/B/C), evaluation as a recorded operator act, the single
append-only confirmatory checkpoint with its family BH fold, the read-side adjudication fold, and
``authorize_promotion`` (the J-08 interlock's pure decision function, unwired this iteration).

**"Eligible occurrence" for a hypothesis, restated.** A hypothesis registers exactly ONE primary
``(measure_key, horizon)`` (spec Sec3) over ONE ``(setup_id, side)`` cell. The J-02 observation
contract does not carry ``setup_id`` directly (``referee_evidence.py``'s own module docstring) --
this module cross-references each candidate observation's raw ``PlaybookStore`` record (via the
``observation_id``'s own encoded ``record_id``, ``referee_null.py``'s own ``_parse_observation_id``
precedent, imported directly rather than re-derived) for its signal's ``setup_id``/``side``. An
eligible occurrence is one whose ``measure_key`` matches the hypothesis's own primary, whose
``session_date`` is STRICTLY after ``confirmation_start_boundary`` (never on-or-before, including a
deep-backfilled record recorded after registration -- T-1's own pre-boundary counter-test), and
whose symbol/date reaches ``REFEREE_SESSION_COMPLETE_ET`` (spec Sec2's completed-session rule, read
off ``playbook_observations()``'s own ``session_completeness`` list -- never re-derived).

**Estimand A and C share ONE pooling routine.** Spec Sec3.3: "As estimand A, but against the
context-matched null" -- estimand C's occurrence pooling is IDENTICAL to A's; only the null-spec id
(and therefore which already-recorded ``RefereeNullStore`` records are read) differs. C's
occurrence-level context evaluability is answered by ``referee_null.py``'s own already-served
``backing_bucket_eligibility_rate`` disclosure (via each occurrence's OWN context-null record being
present-with-eligible-anchors or not) rather than a second live ``BandMapResolver`` call --
single source of truth (IN SCOPE). Per informative session, occurrence values pool into group1 and
their matched-null anchor values pool into group2 -- exactly ``referee_stats._t_statistic``'s
``(group1, group2)`` session-groups shape, and its generic ``n1*n2/(n1+n2)`` weight IS spec Sec3.4's
named "A/C: ``w_s = n_s*K_s/(n_s+K_s)``" formula (n1=occurrence count, n2=anchor count -- the SAME
harmonic form under different variable names, not a second weighting rule).

**Estimand B needs a live per-occurrence context resolve; A/C do not.** B (spec Sec3.2) compares
occurrences of the SAME setup+side split by whether EACH occurrence's own entry satisfies the
registered ``context_predicate`` -- no null is drawn at all (``null_spec_id`` is always ``None`` on
a B hypothesis, J-05's own validation). This module is banned from importing
``desk_playbook_context`` directly (the import-topology guard narrows the ONE sanctioned exception
to ``referee_null.py``) -- it reaches the live resolver transitively, via
``referee_null.resolve_occurrence_backing_bucket`` (a new iter-7 export of that module, mirroring
how ``referee_registry.py`` already imports ``PLAYBOOK_CONTEXT_BACKING_BUCKETS`` the same way) and
``referee_null.BandMapResolver`` for construction. B's weight (``w_s = n1_s*n2_s/(n1_s+n2_s)``) is
the exact SAME ``_t_statistic`` call as A/C, just fed cell/complement groups instead of
occurrence/anchor groups -- one shared statistics core, never a second implementation.

**The entry-basis sensitivity (spec Sec4.3) applies to A/C only.** It exists to test whether the
detector's OWN entry/entry_kind (vs. the null's uniform close-anchored measurement) drives the
result -- a comparison that only makes sense where a null anchor exists to compare against. B has
no anchor at all, so ``entry_basis_T``/``entry_basis_sign_flip`` are honestly ``None`` on every B
evaluation record (structurally inapplicable, the SAME "``None`` when inapplicable" convention
``context_algorithm_version``/``detector_basis`` already use elsewhere in this era) -- logged to
``state/assumptions.md`` (iter-7, developer).

**Confirmatory fields are withheld below the registered floors (T-4, optional stopping).**
``T``/``permutation_p``/``permutation_enumeration``/``min_attainable_p`` are ``None`` unless
``confirmatory_eligible`` (spec: "earlier runs record pending accrual states with NO confirmatory
p") -- this is the STRUCTURAL guard against peeking. The descriptive companions
(``ci_occurrence``/``ci_cluster``/``sign_flip_p``/``equal_weight_T``/entry-basis) are computed
whenever there IS pooled data, regardless of eligibility -- they are NEVER a decision rule (spec
Sec3.5/Sec3.6, T-3), so showing them early carries none of the p-value peeking risk, and the
verdict-computing fragility/BH machinery only ever runs at the checkpoint moment, never before.

**The "sign_flip" fragility trigger is the equal-weight sensitivity, not ``sign_flip_result``'s own
p.** ``sign_flip_result`` computes the SAME ``T`` (``_t_statistic`` on the identical informative
sessions) as the primary permutation test -- its OWN ``t`` field can never differ in sign from the
primary's, since both read the identical observed data; only its NULL distribution differs. The
ONLY spec Sec3.5 sensitivity whose ``T`` can genuinely flip sign is the equal-session-weight variant
(``equal_weight_t``, Sec3.5 item 2 -- the "fat-session defense reading"). ``fragility_triggers``'
``"sign_flip"`` member is therefore ``sign(equal_weight_T) != sign(T)`` -- logged to
``state/assumptions.md`` (iter-7, developer) since the trigger's own name could otherwise be misread
as referring to the ``sign_flip_result`` FUNCTION.

**``exploratory`` and ``killed`` are documented, unreachable enum members this iteration.**
``adjudications_response()`` folds ONLY hypotheses already in the registry (every entry is, by
construction, already registered) -- spec Sec5's "``exploratory`` (basis not registered)" cannot
describe any entry this fold ever serves; TC-20 pins the zero-accrual baseline as ``"registered"``
instead. ``killed`` names no registered kill-condition mechanism anywhere in the spec or the
Hypothesis record schema (T-1: vagueness is a drop -- logged to ``state/assumptions.md``, iter-7,
goal-decomposer). Both stay in this module's own verdict-vocabulary documentation as FUTURE members
a later spec revision could make reachable, but no code path here computes or returns either.

**Attestation refusal forces the most conservative already-named verdict, never a tenth token.** A
snapshot whose ``attestation`` fails re-verification (``referee_stats.verify_oracle_attestation``,
re-run at FOLD time, never trusted from checkpoint time -- T-8) folds to
``confirmatory_output_refused: True`` with a ``refusal_reason``, and ``verdict`` is forced to
``insufficient_sample`` -- the interpretation call logged to ``state/assumptions.md`` (iter-7,
goal-decomposer)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
from .desk_playbook_features import side_sign
from .referee_evidence import (
    REFEREE_FORMING_BAR_BASIS_CAVEAT,
    _epoch_from_iso,
    current_playbook_detector_basis,
    playbook_observations,
    strategy_observations,
)
from .referee_null import (
    REFEREE_NULL_CONTEXT_SPEC_ID,
    BandMapResolver,
    RefereeNullStore,
    _locate_measurement_series,
    _measure_one_anchor,
    _parse_observation_id,
    null_context_spec_parameters,
    null_context_spec_signature,
    null_tod_spec_parameters,
    null_tod_spec_signature,
    resolve_occurrence_backing_bucket,
    resolve_referee_null_dir,
    test_perm_spec_parameters,
)
from .referee_registry import (
    CertificateAlreadyRecorded,
    CertificateStore,
    FamilyStore,
    HypothesisStore,
    resolve_referee_registry_dir,
)
from .referee_stats import (
    INSUFFICIENT_SAMPLE,
    REFEREE_B,
    REFEREE_SEED,
    STATS_CORE_VERSION,
    _t_statistic,
    benjamini_hochberg,
    bootstrap_ci_cluster,
    bootstrap_ci_occurrence,
    equal_weight_t,
    permutation_test,
    referee_stats_parameters,
    run_oracle_attestation,
    sign_flip_result,
    verify_oracle_attestation,
)
from .routes import get_bar_store
from .store import JournalStore

__all__ = [
    "REFEREE_GATE_VERSION",
    "REFEREE_REGISTER",
    "REFEREE_STRATEGY_NULL_DESIGN_CAVEAT",
    "resolve_referee_eval_dir",
    "resolve_referee_eval_log_dir",
    "referee_parameters",
    "referee_parameters_hash",
    "EvaluationIntegrityError",
    "EvaluationAlreadyRecorded",
    "SnapshotAlreadyRecorded",
    "RefereeEvaluationStore",
    "AdjudicationSnapshotStore",
    "RefereeEvaluationRunStore",
    "record_evaluation_run",
    "run_evaluation_and_record",
    "RefereeEvaluationComputeManager",
    "adjudications_response",
    "authorize_promotion",
]

# === spec Sec1 (the FIRST module that needs it -- the established per-module constant-placement
# precedent) + this iteration's own module constant ===================================================

REFEREE_GATE_VERSION: str = "referee-gate-v1"

# The served disclosure text every adjudications response carries verbatim (spec Sec5: "states what
# verdicts do NOT mean"). This iteration's FIRST authoring -- J-09 (the first UI reader) reads this
# EXACT string back rather than minting a second version (single source of truth, the
# REFEREE_FORMING_BAR_BASIS_CAVEAT precedent in referee_evidence.py).
REFEREE_REGISTER: str = (
    "Referee verdicts are statistical statements about recorded history under stated assumptions -- "
    "never a profit claim, never advice, never a prediction, and never annualized. A "
    "'corroborated' verdict means a pre-registered hypothesis's family passed its Benjamini-"
    "Hochberg gate at the registered q with no fragility trigger and its floors met -- it is not a "
    "guarantee, not an edge claim, and not a forecast of what will happen next. Family-wise q does "
    "not compound across families; only the registry's full history makes cumulative false-"
    "discovery risk auditable."
)

_EVAL_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_EVAL_DIR"
_EVAL_LOG_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR"

_ESTIMANDS_AGAINST_NULL = frozenset({"A", "C"})

# goal-referee-iter-9 (J-08 Step 1, spec Sec3.7/Sec9 item 6): the strategy family's own null-design
# disclosure -- served once per strategy-family evaluation record (``provenance.basis_caveats``,
# alongside the Card-6.4 ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` every strategy_trade observation
# already carries), stated rather than hidden, exactly as the spec's own assumption ledger names
# it. A static, config-independent string -- never wall-clock or per-run-random.
REFEREE_STRATEGY_NULL_DESIGN_CAVEAT: str = (
    "the strategy family's recorded random_null baseline is 100 uniform-random-timed entries per "
    "backtest report (backtests.py's own seeded null baseline), not count- or time-of-day-matched "
    "to the candidate strategy's own entries -- a materially weaker null than the Playbook family's "
    "matched-anchor design (docs/referee-statistical-spec.md Sec3.7, Sec9 item 6). Card 6.6's "
    "strategy-matched nulls remain future work, gated on the tick library."
)


# === spec Sec1's own aggregator: referee_parameters() ================================================
#
# "Every constant [Sec1's table] is read at call time by referee_parameters(), embedded verbatim in
# every referee record, and hashed into that record's identity. A monkeypatched constant must move
# the parameters AND the identity (counter-tested)." This module is the natural home: it already
# defines REFEREE_GATE_VERSION and already imports every OTHER module's own existing `_parameters()`
# stub (referee_stats_parameters, null_tod_spec_parameters, null_context_spec_parameters,
# test_perm_spec_parameters) -- combined here ONCE rather than re-derived per caller, closing the
# goal.md IN SCOPE bullet: "combines every referee module's existing `_parameters()` stub (stats,
# null specs, test spec) plus REFEREE_GATE_VERSION into one dict, hashed once, read at call time."


def referee_parameters() -> dict:
    """Every referee module's own pre-registered constants, in one dict, read fresh at call time
    (never cached) -- Parameters discipline: a test that monkeypatches ANY constant reachable from
    the four stub calls below moves this dict's own return value (and therefore
    ``referee_parameters_hash()``'s), never silently leaving a stale parameters identity behind."""
    return {
        "gate_version": REFEREE_GATE_VERSION,
        "stats": referee_stats_parameters(),
        "null_tod": null_tod_spec_parameters(),
        "null_context": null_context_spec_parameters(),
        "test_perm": test_perm_spec_parameters(),
    }


def referee_parameters_hash() -> str:
    """``referee_parameters()``'s own content hash -- the ``referee_parameters_hash`` pin every
    strategy-family certificate and ``authorize_promotion``'s ``live_scan_context`` carry (spec
    Sec8; goal.md J-08 Step 2/3). Read at call time, exactly like ``referee_parameters()`` itself,
    so a monkeypatched constant moves both together (TC-14)."""
    return _sha256(_canonical(referee_parameters()))[:16]


def resolve_referee_eval_dir(desk_universe_dir_resolved: str) -> str:
    """The evaluation + adjudication-snapshot stores' SHARED directory (two record kinds,
    filename-prefix-distinguished -- the ``referee_registry.py`` four-kinds-one-directory pattern):
    ``TAPEOLOGY_DESK_REFEREE_EVAL_DIR`` if set, else a ``referee_eval`` SIBLING of the caller's own
    already-resolved universe directory. Deliberately NOT a ``Config`` field."""
    override = os.environ.get(_EVAL_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_eval")


def resolve_referee_eval_log_dir(desk_universe_dir_resolved: str) -> str:
    """The evaluation run-ledger's directory -- its own ``_LOG_DIR``-family sibling default."""
    override = os.environ.get(_EVAL_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_eval_runs")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _signs_differ(a: float, b: float) -> bool:
    """``True`` iff ``a``/``b`` are strictly opposite in sign -- a zero on either side is never
    treated as a "flip" (an honest boundary reading, not an over-trigger on a degenerate value)."""
    return _sign(a) * _sign(b) < 0


# === exceptions =======================================================================================


class EvaluationIntegrityError(Exception):
    """An on-disk evaluation or adjudication-snapshot record file failed its checksum verification
    on load -- corrupted or tampered, surfaced explicitly (never silence, never a fabricated
    record)."""


class EvaluationAlreadyRecorded(Exception):
    """An evaluation record with this EXACT ``(hypothesis_id, evaluation_basis)`` key is already
    registered -- evaluation records are immutable and append-only; a re-run over an unchanged
    store reuses the existing record (TC-34), never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"an evaluation record with this exact key is already recorded as '{existing_id}' -- "
            f"evaluation records are immutable and are never re-recorded"
        )


class SnapshotAlreadyRecorded(Exception):
    """An adjudication snapshot for this ``hypothesis_id`` is already on file -- exactly ONE
    snapshot per hypothesis, ever (spec Sec5's single confirmatory checkpoint)."""

    def __init__(self, hypothesis_id: str) -> None:
        self.hypothesis_id = hypothesis_id
        super().__init__(
            f"an adjudication snapshot for hypothesis {hypothesis_id!r} is already recorded -- "
            f"exactly one snapshot per hypothesis is ever written"
        )


# === the eligible-occurrence gather (shared by all three estimands) ==================================


def _eligible_setup_side_occurrences(
    hypothesis: dict, playbook_store: PlaybookStore, config_fingerprint: str,
) -> tuple[list[dict], dict[str, dict | None]]:
    """Every J-02 observation of this hypothesis's own ``(setup_id, side)`` cell, at its registered
    primary ``(measure_key, horizon)`` -- filtered to STRICTLY post-boundary, completed-session
    records only (module docstring). Cross-references each candidate's raw ``PlaybookStore`` record
    (via the observation_id's own encoded ``record_id``) for ``setup_id``/``side`` -- the J-02
    contract does not carry them directly. Returns ``(occurrences, record_cache)``; the cache lets a
    caller re-use already-verified records for the entry-basis sensitivity without a second read."""
    projection = playbook_observations(playbook_store, config_fingerprint)
    boundary = hypothesis["confirmation_start_boundary"]
    primary_measure_key = hypothesis["primary_measure_key"]
    setup_id = hypothesis["setup_id"]
    side = hypothesis["side"]

    complete_by_symbol_date = {
        (row["session_date"], row["symbol"]): row["complete"]
        for row in projection["session_completeness"]
    }

    _missing = object()
    record_cache: dict[str, dict | None] = {}
    occurrences: list[dict] = []
    for observation in projection["observations"]:
        if observation["measure_key"] != primary_measure_key:
            continue
        if observation["session_date"] <= boundary:
            continue  # strictly after the boundary -- the pre-boundary counter-test (T-1)
        if not complete_by_symbol_date.get(
            (observation["session_date"], observation["symbol"]), False
        ):
            continue  # completed-session records only (spec Sec2)
        record_id, signal_index, _measure_key = _parse_observation_id(observation["observation_id"])
        record = record_cache.get(record_id, _missing)
        if record is _missing:
            record = playbook_store.get(record_id)
            record_cache[record_id] = record
        if record is None:
            continue
        signal = record["signals"][signal_index]
        if signal["setup_id"] != setup_id or signal["side"] != side:
            continue
        occurrences.append(
            {
                "observation_id": observation["observation_id"],
                "session_date": observation["session_date"],
                "symbol": observation["symbol"],
                "value": observation["value"],
                "side": observation["side"],
                "anchor_ts": observation["anchor_ts"],
                "measure_key": observation["measure_key"],
                "signal": signal,
            }
        )
    return occurrences, record_cache


# === estimand A/C pooling: occurrences vs their matched-null anchors ==================================


def _pool_against_null(
    occurrences: list[dict], null_store: RefereeNullStore, null_spec_id: str,
) -> dict:
    """Estimand A/C pooling (spec Sec3.1/Sec3.3 -- "as estimand A, but against the context-matched
    null"): per informative session, occurrence values pool into group1 and their ALREADY-RECORDED
    matched-null anchor values pool into group2 (``RefereeNullStore.find_by_key``, never a second
    null build -- GETs/evaluations never compute a null, T-8). An occurrence whose own null record
    is absent, ``excluded``, or carries zero anchors is excluded and counted (T-5) -- never
    substituted. Estimand C reads the context null-spec's OWN already-served eligibility here --
    zero eligible anchors for every occurrence in a cell IS this function's own honest zero-pool
    outcome, never a second live context resolve (IN SCOPE)."""
    signature = (
        null_context_spec_signature()
        if null_spec_id == REFEREE_NULL_CONTEXT_SPEC_ID
        else null_tod_spec_signature()
    )
    by_session_occ: dict[str, list[float]] = {}
    by_session_anchor: dict[str, list[float]] = {}
    by_session_entries: dict[str, list[dict]] = {}
    occurrence_diffs: list[float] = []
    null_record_ids: set[str] = set()
    observation_ids: set[str] = set()
    sessions_touched: set[str] = set()

    for occ in occurrences:
        sessions_touched.add(occ["session_date"])
        null_record = null_store.find_by_key(occ["observation_id"], signature)
        if null_record is None or null_record.get("excluded"):
            continue
        anchor_values = [anchor["value"] for anchor in null_record["anchors"]]
        if not anchor_values:
            continue
        observation_ids.add(occ["observation_id"])
        null_record_ids.add(null_record["null_record_id"])
        by_session_occ.setdefault(occ["session_date"], []).append(occ["value"])
        by_session_anchor.setdefault(occ["session_date"], []).extend(anchor_values)
        by_session_entries.setdefault(occ["session_date"], []).append(
            {
                "symbol": occ["symbol"],
                "trigger_epoch": _epoch_from_iso(occ["anchor_ts"]),
                "side": occ["side"],
                "measure_key": occ["measure_key"],
            }
        )
        occurrence_diffs.append(occ["value"] - (math.fsum(anchor_values) / len(anchor_values)))

    session_groups = {
        date: (values, by_session_anchor[date]) for date, values in by_session_occ.items()
    }
    one_group_sessions_excluded = len(sessions_touched) - len(session_groups)

    return {
        "session_groups": session_groups,
        "occurrence_diffs": occurrence_diffs,
        "occurrences_pooled": len(observation_ids),
        "one_group_sessions_excluded": one_group_sessions_excluded,
        "informative_sessions": len(session_groups),
        "observation_ids": observation_ids,
        "null_record_ids": null_record_ids,
        "by_session": by_session_entries,
    }


# === estimand B pooling: occurrences in the context cell vs its complement ===========================


def _pool_cell_vs_complement(
    occurrences: list[dict], hypothesis: dict, context_resolver: BandMapResolver | None,
) -> dict:
    """Estimand B pooling (spec Sec3.2): per informative session, occurrences whose OWN entry
    satisfies the registered ``context_predicate`` pool into group1 (the cell); same-setup
    occurrences outside it pool into group2 (the complement). An occurrence whose band map cannot
    be resolved at all is excluded and counted (T-5), never assigned to either group."""
    backing_bucket = hypothesis["context_predicate"]["backing_bucket"]
    by_session_cell: dict[str, list[float]] = {}
    by_session_complement: dict[str, list[float]] = {}
    observation_ids: set[str] = set()
    sessions_touched: set[str] = set()

    for occ in occurrences:
        sessions_touched.add(occ["session_date"])
        if context_resolver is None:
            continue
        cell = resolve_occurrence_backing_bucket(
            occ["signal"], occ["symbol"], _epoch_from_iso(occ["anchor_ts"]),
            occ["signal"].get("entry"), occ["side"], context_resolver,
        )
        if cell is None:
            continue
        observation_ids.add(occ["observation_id"])
        if cell == backing_bucket:
            by_session_cell.setdefault(occ["session_date"], []).append(occ["value"])
        else:
            by_session_complement.setdefault(occ["session_date"], []).append(occ["value"])

    all_dates = set(by_session_cell) | set(by_session_complement)
    session_groups: dict[str, tuple[list[float], list[float]]] = {}
    one_group_sessions_excluded = 0
    for date in all_dates:
        cell_values = by_session_cell.get(date, [])
        complement_values = by_session_complement.get(date, [])
        if cell_values and complement_values:
            session_groups[date] = (cell_values, complement_values)
        else:
            one_group_sessions_excluded += 1
    one_group_sessions_excluded += len(sessions_touched - all_dates)

    return {
        "session_groups": session_groups,
        "occurrence_diffs": None,  # not defined at occurrence level for B (spec Sec3.6)
        "occurrences_pooled": len(observation_ids),
        "one_group_sessions_excluded": one_group_sessions_excluded,
        "informative_sessions": len(session_groups),
        "observation_ids": observation_ids,
        "null_record_ids": set(),
        "by_session": {},  # the entry-basis sensitivity does not apply to B (module docstring)
    }


def _pool_for_estimand(
    hypothesis: dict,
    occurrences: list[dict],
    *,
    null_store: RefereeNullStore,
    context_resolver: BandMapResolver | None,
) -> dict:
    if hypothesis["estimand"] in _ESTIMANDS_AGAINST_NULL:
        return _pool_against_null(occurrences, null_store, hypothesis["null_spec_id"])
    return _pool_cell_vs_complement(occurrences, hypothesis, context_resolver)


# === J-08 Step 1: the strategy-family analog pooling (spec Sec3.7) ====================================


def _pool_strategy_trades(journal_store: JournalStore) -> dict:
    """The strategy-family analog of ``_pool_against_null`` (spec Sec3.7: "Cluster = dataset. Per
    dataset d with >=1 candidate trade: Delta_d = mean(candidate net_r in d) - mean(recorded
    random_null net_r in d)") -- reuses ``referee_evidence.strategy_observations()`` verbatim
    (never a second join of trades to dataset identity) and groups by ``cluster_key`` = dataset id
    (never ``session_date``, TC-9). Shaped IDENTICALLY to ``_pool_against_null``'s own return dict
    so ``run_evaluation_and_record`` reuses every downstream step (coverage, permutation test,
    both bootstrap CIs, BH, snapshot) with zero branching beyond the POOLING call itself.

    ``occurrence_diffs`` is honestly ``None`` (``_pool_cell_vs_complement``'s own "not defined at
    occurrence level" precedent, not ``_pool_against_null``'s occurrence-diff list): unlike
    estimand A/C's ToD-matched null (exactly ``K`` anchors per occurrence, a natural per-occurrence
    pairing), a candidate trade has no single designated partner among a dataset's ``random_null``
    trades (``backtest_null_entry_count`` uniform-random draws per report, spec Sec9 item 6) --
    only the DATASET-clustered ``Delta_d`` is spec-defined. Recorded as an explicit design choice
    (T-1), not a silent gap: it structurally disables ``bootstrap_ci_occurrence``/the entry-basis
    sensitivity for strategy-family evaluations (both already gated on non-empty
    ``occurrence_diffs``/``_ESTIMANDS_AGAINST_NULL`` in ``run_evaluation_and_record``), which is
    correct here -- there is no occurrence-level uncertainty quantity to disclose."""
    obs = strategy_observations(journal_store)
    by_cluster_candidate: dict[str, list[float]] = {}
    by_cluster_null: dict[str, list[float]] = {}
    observation_ids_by_cluster: dict[str, set[str]] = {}
    for observation in obs["observations"]:
        cluster_key = observation["cluster_key"]
        by_cluster_candidate.setdefault(cluster_key, []).append(observation["value"])
        observation_ids_by_cluster.setdefault(cluster_key, set()).add(observation["observation_id"])
    for observation in obs["null_observations"]:
        by_cluster_null.setdefault(observation["cluster_key"], []).append(observation["value"])

    all_clusters = set(by_cluster_candidate) | set(by_cluster_null)
    session_groups: dict[str, tuple[list[float], list[float]]] = {}
    one_group_excluded = 0
    for cluster_key in all_clusters:
        candidate_values = by_cluster_candidate.get(cluster_key, [])
        null_values = by_cluster_null.get(cluster_key, [])
        if candidate_values and null_values:
            session_groups[cluster_key] = (candidate_values, null_values)
        else:
            one_group_excluded += 1

    observation_ids: set[str] = set()
    for cluster_key in session_groups:
        observation_ids |= observation_ids_by_cluster.get(cluster_key, set())

    return {
        "session_groups": session_groups,
        "occurrence_diffs": None,
        "occurrences_pooled": len(observation_ids),
        "one_group_sessions_excluded": one_group_excluded,
        "informative_sessions": len(session_groups),
        "observation_ids": observation_ids,
        "null_record_ids": set(),
        "by_session": {},
    }


# === the entry-basis sensitivity (spec Sec4.3; A/C only) ==============================================


def _entry_basis_session_groups(
    pool: dict, bar_store: BarStore,
) -> dict[str, tuple[list[float], list[float]]]:
    """Re-measures each pooled occurrence CLOSE-ANCHORED at its own trigger bar (read-side, at
    evaluation time; detectors untouched) via the SAME ``_measure_one_anchor`` helper
    ``referee_null.py`` already uses for null anchors -- keeps the SAME matched-null anchor values
    (already close-anchored) and only replaces the occurrence side of each session's pair."""
    groups: dict[str, tuple[list[float], list[float]]] = {}
    for session_date, entries in pool["by_session"].items():
        anchor_values = list(pool["session_groups"].get(session_date, ([], []))[1])
        occ_values: list[float] = []
        for entry in entries:
            located = _locate_measurement_series(
                bar_store, entry["symbol"], session_date, entry["trigger_epoch"]
            )
            if located is None:
                continue
            measure_bars, trigger_index, tf_minutes = located
            sign = side_sign(entry["side"])
            value, _forward = _measure_one_anchor(
                measure_bars, trigger_index, tf_minutes, sign, entry["measure_key"]
            )
            if value is None:
                continue
            occ_values.append(value)
        if occ_values and anchor_values:
            groups[session_date] = (occ_values, anchor_values)
    return groups


# === evaluation_basis + attestation ===================================================================


def _evaluation_basis(
    *,
    hypothesis_id: str,
    observation_ids: set[str],
    coverage: dict,
    null_record_ids: set[str],
    null_spec_id: str | None,
    test_spec_id: str,
) -> str:
    """Content hash of the dedup record-id set + coverage counts, null record ids, null/test-spec
    ids, seed, B, stats-core version (spec Sec5 / the Data Contract's own field description) --
    identical inputs (an unchanged store) always hash identically (TC-12)."""
    blob = {
        "hypothesis_id": hypothesis_id,
        "observation_ids": sorted(observation_ids),
        "coverage": coverage,
        "null_record_ids": sorted(null_record_ids),
        "null_spec_id": null_spec_id,
        "test_spec_id": test_spec_id,
        "seed": REFEREE_SEED,
        "b": REFEREE_B,
        "stats_core_version": STATS_CORE_VERSION,
    }
    return _sha256(_canonical(blob))[:16]


# === the append-only evaluation store ==================================================================


class RefereeEvaluationStore:
    """File-based store rooted at the resolved eval directory, ``evaluation-*.json`` files only --
    mirrors ``RefereeNullStore``'s discipline exactly (checksum-verified loads, append-only
    ``record``, no update/delete method anywhere on this class, structural)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, evaluation_id: str) -> Path:
        return self._root / f"evaluation-{evaluation_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise EvaluationIntegrityError(
                f"evaluation record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise EvaluationIntegrityError(
                f"evaluation record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise EvaluationIntegrityError(
                f"evaluation record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise EvaluationIntegrityError(
                f"evaluation record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("evaluation-*.json")):
            try:
                records.append(dict(self._load(path)))
            except EvaluationIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("evaluated_at", ""), meta.get("evaluation_id", "")))
        return records, errors

    def list_for_hypothesis(self, hypothesis_id: str) -> list[dict]:
        records, _errors = self.list()
        return [record for record in records if record.get("hypothesis_id") == hypothesis_id]

    def get(self, evaluation_id: str) -> dict | None:
        path = self._path(evaluation_id)
        if path.parent != self._root:
            return None
        try:
            meta = self._load(path)
        except EvaluationIntegrityError:
            return None
        if meta.get("evaluation_id") != evaluation_id:
            return None
        return dict(meta)

    def find_by_key(self, hypothesis_id: str, evaluation_basis: str) -> dict | None:
        evaluation_id = _sha256(_canonical([hypothesis_id, evaluation_basis]))[:16]
        record = self.get(evaluation_id)
        if record is None:
            return None
        key = (record.get("hypothesis_id"), record.get("evaluation_basis"))
        return record if key == (hypothesis_id, evaluation_basis) else None

    def find_checkpoint_for(self, hypothesis_id: str) -> dict | None:
        """The recorded ``role == "checkpoint"`` evaluation for ``hypothesis_id`` -- at most one
        ever exists (spec Sec5's single confirmatory checkpoint). Used by the family BH fold to
        find a SIBLING hypothesis's own frozen checkpoint p-value."""
        for record in self.list_for_hypothesis(hypothesis_id):
            if record.get("role") == "checkpoint":
                return record
        return None

    def record(self, fields: dict) -> dict:
        evaluation_id = _sha256(
            _canonical([fields["hypothesis_id"], fields["evaluation_basis"]])
        )[:16]
        existing = self.find_by_key(fields["hypothesis_id"], fields["evaluation_basis"])
        if existing is not None:
            raise EvaluationAlreadyRecorded(existing["evaluation_id"])
        fields = {**fields, "evaluation_id": evaluation_id}
        path = self._path(evaluation_id)
        if path.exists():
            raise EvaluationIntegrityError(
                f"evaluation record file '{path.name}' already exists on disk but failed its "
                f"integrity check -- refusing to overwrite it (evaluation records are append-only "
                f"and are never rewritten)."
            )
        record = {"meta": dict(fields)}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return dict(fields)


# === the append-only adjudication snapshot store (exactly ONE per hypothesis, ever) ===================


class AdjudicationSnapshotStore:
    """File-based store rooted at the SAME resolved eval directory as ``RefereeEvaluationStore``
    (the ``referee_registry.py`` shared-directory-distinct-prefix pattern), ``snapshot-*.json``
    files only, keyed by ``hypothesis_id`` -- exactly one snapshot per hypothesis, structurally: a
    second write attempt collides on the SAME deterministic path (``SnapshotAlreadyRecorded``). No
    update/delete method exists anywhere on this class."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, hypothesis_id: str) -> Path:
        return self._root / f"snapshot-{hypothesis_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise EvaluationIntegrityError(
                f"adjudication snapshot file '{path.name}' is not parseable ({exc}) -- corrupted "
                f"or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise EvaluationIntegrityError(
                f"adjudication snapshot file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise EvaluationIntegrityError(
                f"adjudication snapshot file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise EvaluationIntegrityError(
                f"adjudication snapshot file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("snapshot-*.json")):
            try:
                records.append(dict(self._load(path)))
            except EvaluationIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("snapshot_at", ""), meta.get("hypothesis_id", "")))
        return records, errors

    def get_for_hypothesis(self, hypothesis_id: str) -> dict | None:
        path = self._path(hypothesis_id)
        if not path.exists():
            return None
        try:
            meta = self._load(path)
        except EvaluationIntegrityError:
            return None
        if meta.get("hypothesis_id") != hypothesis_id:
            return None
        return dict(meta)

    def record(self, fields: dict) -> dict:
        hypothesis_id = fields["hypothesis_id"]
        path = self._path(hypothesis_id)
        if path.exists():
            try:
                self._load(path)
            except EvaluationIntegrityError:
                raise
            raise SnapshotAlreadyRecorded(hypothesis_id)
        snapshot_id = _sha256(_canonical([hypothesis_id, fields["checkpoint_evaluation_id"]]))[:16]
        fields = {**fields, "snapshot_id": snapshot_id}
        record = {"meta": dict(fields)}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return dict(fields)


# === the durable evaluation run ledger (terminal-state-only writes) ===================================


class RefereeEvaluationRunStore:
    """Mirrors ``RefereeNullRunStore`` exactly, keyed by ``hypothesis_id`` instead of
    ``null_spec_id``: a checksum-verified load on every read, ``record()`` the only mutation, no
    update/delete method anywhere, a real ``"cancelled"`` terminal state."""

    _TERMINAL_STATES = ("completed", "failed", "cancelled")

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise EvaluationIntegrityError(
                f"evaluation run record file '{path.name}' is not parseable ({exc}) -- corrupted "
                f"or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise EvaluationIntegrityError(
                f"evaluation run record file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise EvaluationIntegrityError(
                f"evaluation run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise EvaluationIntegrityError(
                f"evaluation run record file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path)))
            except EvaluationIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
        return records, errors

    def list_for_hypothesis(self, hypothesis_id: str) -> list[dict]:
        records, _errors = self.list()
        return [record for record in records if record.get("hypothesis_id") == hypothesis_id]

    def record(
        self,
        *,
        hypothesis_id: str,
        state: str,
        started_at: str,
        finished_at: str,
        progress: dict,
        error: str | None,
    ) -> dict:
        if state not in self._TERMINAL_STATES:
            raise ValueError(f"invalid terminal state {state!r} -- must be one of {self._TERMINAL_STATES}")
        date_prefix = started_at[:10]
        run_id = f"refereeevalrun-{date_prefix}-{uuid.uuid4().hex[:12]}"
        while self._path(run_id).exists():
            run_id = f"refereeevalrun-{date_prefix}-{uuid.uuid4().hex[:12]}"
        meta = {
            "run_id": run_id,
            "hypothesis_id": hypothesis_id,
            "state": state,
            "started_at": started_at,
            "finished_at": finished_at,
            "progress": dict(progress),
            "error": error,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_evaluation_run(
    store: RefereeEvaluationRunStore,
    *,
    hypothesis_id: str,
    state: str,
    started_at: str,
    finished_at: str,
    progress: dict,
    error: str | None,
) -> dict:
    """THE single shared writer -- called AT MOST once per run, at its own terminal state, from
    inside ``run_evaluation_and_record`` (the ``record_null_run`` precedent)."""
    return store.record(
        hypothesis_id=hypothesis_id, state=state, started_at=started_at, finished_at=finished_at,
        progress=progress, error=error,
    )


# === the family BH fold (directly testable, independent of any real evaluation store) =================


def _family_p_values(
    family: dict, hypothesis_id: str, this_p: float, evaluation_store: RefereeEvaluationStore,
) -> list[float]:
    """p-values in the family's OWN planned order (spec Sec5: m = the frozen planned count,
    forever) -- ``hypothesis_id``'s own just-computed ``this_p``; every OTHER candidate's own
    checkpoint evaluation's ``permutation_p`` if one is on file REGARDLESS of withdrawal status
    (TC-16), else the literal ``1.0`` (never evaluated, or withdrawn without ever checkpointing --
    TC-15; never dropped, never shrinking ``m``)."""
    values: list[float] = []
    for candidate_id in family["candidate_hypothesis_ids"]:
        if candidate_id == hypothesis_id:
            values.append(this_p)
            continue
        sibling = evaluation_store.find_checkpoint_for(candidate_id)
        values.append(sibling["permutation_p"] if sibling is not None else 1.0)
    return values


def _family_bh_fold(hypothesis_id: str, family: dict, p_values: list[float]) -> dict:
    """The family BH fold (spec Sec5) for ONE hypothesis's own rank -- a thin, directly-testable
    wrapper around ``referee_stats.benjamini_hochberg`` (TC-14 exercises this with a synthetic
    p_values list, never needing many real checkpointed hypotheses)."""
    planned = family["candidate_hypothesis_ids"]
    idx = planned.index(hypothesis_id)
    bh = benjamini_hochberg(p_values, family["q"])
    by_adjusted_p = bh["by_adjusted_p"][idx]
    return {
        "q": family["q"],
        "m": bh["m"],
        "k_star": bh["k_star"],
        "bh_pass": bh["bh_pass"][idx],
        "by_adjusted_p": by_adjusted_p,
        "by_pass": by_adjusted_p <= family["q"],
    }


def _build_and_record_snapshot(
    recorded: dict,
    *,
    family_store: FamilyStore,
    evaluation_store: RefereeEvaluationStore,
    snapshot_store: AdjudicationSnapshotStore,
) -> dict:
    """Computes and appends the ONE adjudication snapshot for ``recorded`` (a just-recorded
    ``role == "checkpoint"`` evaluation) -- the family BH fold plus the four named fragility
    triggers (spec Sec5), reused identically by both the fresh-compute path and the dedup
    self-heal path (an evaluation record whose OWN checkpoint snapshot write did not complete for
    some reason -- ``run_evaluation_and_record``'s own retry path)."""
    hypothesis_id = recorded["hypothesis_id"]
    family = family_store.get(recorded["family_id"])
    p_values = _family_p_values(family, hypothesis_id, recorded["permutation_p"], evaluation_store)
    bh = _family_bh_fold(hypothesis_id, family, p_values)

    fragility_triggers: list[str] = []
    if bh["bh_pass"] and not bh["by_pass"]:
        fragility_triggers.append("by_fail")
    if (
        recorded["equal_weight_T"] is not None
        and recorded["T"] is not None
        and _signs_differ(recorded["equal_weight_T"], recorded["T"])
    ):
        fragility_triggers.append("sign_flip")
    if recorded["entry_basis_sign_flip"]:
        fragility_triggers.append("entry_basis_sign_flip")
    ci_cluster = recorded["ci_cluster"]
    if isinstance(ci_cluster, list) and ci_cluster[0] <= 0.0 <= ci_cluster[1]:
        fragility_triggers.append("cluster_ci_includes_zero")

    verdict = (
        "no_evidence" if not bh["bh_pass"]
        else "fragile" if fragility_triggers
        else "corroborated"
    )
    snapshot_fields = {
        "hypothesis_id": hypothesis_id,
        "family_id": recorded["family_id"],
        "checkpoint_evaluation_id": recorded["evaluation_id"],
        "snapshot_at": _iso_utc_now(),
        "bh": bh,
        "fragility_triggers": fragility_triggers,
        "verdict": verdict,
        "evaluation_basis": recorded["evaluation_basis"],
        "attestation": recorded["attestation"],
    }
    try:
        return snapshot_store.record(snapshot_fields)
    except SnapshotAlreadyRecorded:
        existing = snapshot_store.get_for_hypothesis(hypothesis_id)
        assert existing is not None  # the raise above proves a record exists at this exact key
        return existing


# === J-08 Step 2: the certificate's REAL mint call site (spec Sec8) ===================================


def _mint_strategy_certificate(
    *,
    hypothesis: dict,
    recorded: dict,
    snapshot: dict,
    candidate: dict,
    champion_identity_at_scan_time: dict,
    train_dataset: dict,
    holdout_dataset: dict,
    certificate_store: CertificateStore,
) -> dict | None:
    """Mints ONE certificate record (spec Sec8) for a strategy-family hypothesis's own freshly
    recorded, gate-passing confirmatory checkpoint -- called ONLY from
    ``run_evaluation_and_record``'s own fresh-compute path (never a hand-written or fixture path
    in production code), and only when its caller explicitly supplied ``certificate_mint`` (the
    live scan identity this certificate is meant to authorize -- a hypothesis record alone names
    no ``(strategy_id, profile)`` candidate, no champion, and no train/holdout dataset pair, so
    this function cannot derive them; the caller, which DOES know which live ``pnl_scan`` run this
    mint is for, supplies them verbatim).

    Refuses (returns ``None``, mints nothing) unless the attestation RE-verifies (T-8, never
    trusted from the stored ``passed`` flag) -- the exact gate ``_snapshot_fold``/
    ``_build_and_record_snapshot`` already enforce, read here from the just-built
    ``recorded``/``snapshot`` rather than re-derived a second way. ``gate_results.bh_pass`` is the
    family BH pass ``snapshot["bh"]["bh_pass"]`` already computed; ``floors_met`` is
    ``recorded["confirmatory_eligible"]`` (the SAME floor check that gated this evaluation into
    ``role == "checkpoint"`` in the first place -- served explicitly on the certificate so
    ``authorize_promotion`` never has to re-derive it from a foreign evaluation record). A
    re-mint attempt for an identical ``(hypothesis_id, evaluation_basis, candidate)`` key -- e.g. a
    caller retrying after a crash between this write and its own follow-up -- returns the
    ALREADY-recorded certificate rather than raising (append-only idempotence, the
    ``HypothesisStore``/``NullStore`` precedent elsewhere in this era)."""
    if not verify_oracle_attestation(recorded.get("attestation")):
        return None
    ci_cluster = recorded.get("ci_cluster")
    ci = ci_cluster if isinstance(ci_cluster, list) else None
    certificate_id = _sha256(
        _canonical([hypothesis["hypothesis_id"], recorded["evaluation_basis"], candidate])
    )[:16]
    fields = {
        "certificate_id": certificate_id,
        "candidate": dict(candidate),
        "champion_identity_at_scan_time": dict(champion_identity_at_scan_time),
        "train_dataset": dict(train_dataset),
        "holdout_dataset": dict(holdout_dataset),
        "config_fingerprint": recorded["provenance"]["config_fingerprint"],
        "gate_version": REFEREE_GATE_VERSION,
        "referee_parameters_hash": referee_parameters_hash(),
        "family_id": hypothesis["family_id"],
        "hypothesis_id": hypothesis["hypothesis_id"],
        "gate_results": {
            "calibrated_p": recorded["permutation_p"],
            "bh_pass": snapshot["bh"]["bh_pass"],
            "ci": ci,
            "floors_met": recorded["confirmatory_eligible"],
        },
    }
    try:
        return certificate_store.record(fields)
    except CertificateAlreadyRecorded:
        return certificate_store.get(certificate_id)


# === the compute walker: ONE evaluation act, start to finish ==========================================


def run_evaluation_and_record(
    hypothesis_id: str,
    *,
    hypothesis_store: HypothesisStore,
    family_store: FamilyStore,
    playbook_store: PlaybookStore,
    bar_store: BarStore,
    config: Config,
    null_store: RefereeNullStore,
    evaluation_store: RefereeEvaluationStore,
    snapshot_store: AdjudicationSnapshotStore,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    run_store: RefereeEvaluationRunStore | None = None,
    journal_store: JournalStore | None = None,
    certificate_mint: dict | None = None,
) -> dict:
    """Runs ONE evaluation act for ``hypothesis_id`` (spec Sec3/Sec5) and records it -- resumable
    (TC-34: an unchanged store reuses the existing record under the exact ``evaluation_basis`` key,
    computing nothing new) and cancel-safe (``should_abort`` is checked before every named phase, so
    a cancel writes NO partial evaluation record, TC-33). Returns
    ``{"cancelled": bool, "record": dict|None, "snapshot": dict|None, "reused": bool,
    "certificate": dict|None}``. Raises ``ValueError`` for an unknown ``hypothesis_id`` (surfaced
    by the caller -- the CLI lets it propagate; the route validates first and never reaches this
    function for one).

    ``journal_store`` (goal-referee-iter-9, J-08 Step 1) is consulted ONLY for a
    ``hypothesis["evidence_family"] == "strategy"`` hypothesis (the playbook path never touches
    it) -- required for that branch to pool anything; ``None`` (the default -- every EXISTING
    playbook-only caller is unaffected) makes a strategy-family evaluation pool an honest empty
    corpus rather than raise.

    ``certificate_mint`` (J-08 Step 2) is the CALLER's own live scan identity -- this function has
    no way to derive "which pnl_scan run this certificate should authorize" from a hypothesis
    record alone. ``None`` (the default -- every route/CLI caller today) mints nothing, matching
    goal.md's own "no strategy certificate can honestly exist this era" (fixture-only, reachable
    only by a caller that explicitly supplies one). When supplied, shaped
    ``{"candidate": {"strategy_id": str, "profile": str}, "champion_identity_at_scan_time": dict,
    "train_dataset": dict, "holdout_dataset": dict, "certificate_store": CertificateStore}`` -- see
    ``_mint_strategy_certificate``, consulted ONLY at a FRESH strategy-family checkpoint (never on
    the dedup/reused path)."""
    started_at = _iso_utc_now()

    def _log(*, state: str, done: int, total: int, error: str | None) -> None:
        if run_store is None:
            return
        record_evaluation_run(
            run_store, hypothesis_id=hypothesis_id, state=state, started_at=started_at,
            finished_at=_iso_utc_now(), progress={"done": done, "total": total}, error=error,
        )

    total_units = 8
    done_units = 0

    def _tick() -> None:
        nonlocal done_units
        done_units += 1
        if progress is not None:
            progress({"done": done_units, "total": total_units})

    def _aborted() -> bool:
        return should_abort is not None and should_abort()

    hypothesis = hypothesis_store.get(hypothesis_id)
    if hypothesis is None:
        exc = ValueError(f"unknown hypothesis_id {hypothesis_id!r}")
        _log(state="failed", done=0, total=total_units, error=str(exc))
        raise exc

    if _aborted():
        _log(state="cancelled", done=0, total=total_units, error=None)
        return {"cancelled": True, "record": None, "snapshot": None, "reused": False}

    try:
        config_fingerprint = config.config_fingerprint()
        estimand = hypothesis["estimand"]
        evidence_family = hypothesis["evidence_family"]
        if evidence_family == "strategy":
            # J-08 Step 1 (spec Sec3.7): the strategy-family analog -- cluster = dataset, never
            # session_date (``_pool_strategy_trades``, never ``_pool_for_estimand``'s playbook-only
            # occurrence gather). ``journal_store=None`` (no production caller reaches this branch
            # without one this era) pools an honest empty corpus rather than raise.
            pool = (
                _pool_strategy_trades(journal_store)
                if journal_store is not None
                else {
                    "session_groups": {}, "occurrence_diffs": None, "occurrences_pooled": 0,
                    "one_group_sessions_excluded": 0, "informative_sessions": 0,
                    "observation_ids": set(), "null_record_ids": set(), "by_session": {},
                }
            )
        else:
            context_resolver = (
                BandMapResolver(bar_store, config, compute=False) if estimand in ("B", "C") else None
            )
            occurrences, _record_cache = _eligible_setup_side_occurrences(
                hypothesis, playbook_store, config_fingerprint
            )
            pool = _pool_for_estimand(
                hypothesis, occurrences, null_store=null_store, context_resolver=context_resolver
            )
        _tick()

        coverage = {
            "post_boundary_informative_sessions": pool["informative_sessions"],
            "target_sessions": hypothesis["target_sessions"],
            "min_occurrences": hypothesis["min_occurrences"],
            "occurrences_pooled": pool["occurrences_pooled"],
            "one_group_sessions_excluded": pool["one_group_sessions_excluded"],
        }
        evaluation_basis = _evaluation_basis(
            hypothesis_id=hypothesis_id,
            observation_ids=pool["observation_ids"],
            coverage=coverage,
            null_record_ids=pool["null_record_ids"],
            null_spec_id=hypothesis.get("null_spec_id"),
            test_spec_id=hypothesis["test_spec_id"],
        )

        existing = evaluation_store.find_by_key(hypothesis_id, evaluation_basis)
        if existing is not None:
            snapshot = None
            # iter-8 audit (B1): this dedup/self-heal branch is the OTHER of the TWO sites that
            # write a hypothesis's ONE permanent snapshot -- Rider 1 below gated only the
            # fresh-compute site, so an ALREADY-RECORDED checkpoint reached this branch with NO
            # attestation check at all. Gated here with the read side's own re-derivation
            # (`verify_oracle_attestation`, never the stored `passed` flag, T-8), because the
            # realistic case is an attestation that has since gone version-stale: minting the
            # permanent snapshot from it burns the hypothesis's single checkpoint on a verdict the
            # read fold must then refuse forever. When it does not verify, nothing is written and
            # the fold serves its honest live (pre-checkpoint) state instead.
            existing_attested = (
                isinstance(existing.get("attestation"), dict)
                and existing["attestation"].get("passed") is True
                and verify_oracle_attestation(existing["attestation"])
            )
            if (
                existing["role"] == "checkpoint"
                and existing_attested
                and snapshot_store.get_for_hypothesis(hypothesis_id) is None
            ):
                snapshot = _build_and_record_snapshot(
                    existing, family_store=family_store, evaluation_store=evaluation_store,
                    snapshot_store=snapshot_store,
                )
            elif existing["role"] == "checkpoint":
                snapshot = snapshot_store.get_for_hypothesis(hypothesis_id)
            _log(state="completed", done=total_units, total=total_units, error=None)
            # No mint attempt on the dedup/reused path (goal-referee-iter-9): a certificate mints
            # only at the hypothesis's ONE fresh checkpoint compute, below -- a re-run over an
            # unchanged store is by definition not that fresh compute.
            return {
                "cancelled": False, "record": existing, "snapshot": snapshot, "reused": True,
                "certificate": None,
            }

        if _aborted():
            _log(state="cancelled", done=done_units, total=total_units, error=None)
            return {"cancelled": True, "record": None, "snapshot": None, "reused": False}

        checkpoint_exists = snapshot_store.get_for_hypothesis(hypothesis_id) is not None
        confirmatory_eligible = (
            coverage["post_boundary_informative_sessions"] >= coverage["target_sessions"]
            and coverage["occurrences_pooled"] >= coverage["min_occurrences"]
        )
        role = (
            "checkpoint" if (confirmatory_eligible and not checkpoint_exists)
            else "monitoring" if confirmatory_eligible
            else "pending"
        )

        primary_t = None
        if pool["session_groups"]:
            primary_t, _deltas, _weights = _t_statistic(pool["session_groups"])
        _tick()

        fields: dict = {
            "hypothesis_id": hypothesis_id,
            "family_id": hypothesis["family_id"],
            "evaluated_at": _iso_utc_now(),
            "evidence_family": hypothesis["evidence_family"],
            "estimand": estimand,
            "evaluation_basis": evaluation_basis,
            "coverage": coverage,
            "confirmatory_eligible": confirmatory_eligible,
            "role": role,
            "T": None, "permutation_p": None, "permutation_enumeration": None,
            "min_attainable_p": None, "ci_occurrence": None, "ci_cluster": None,
            "sign_flip_p": None, "equal_weight_T": None,
            "entry_basis_T": None, "entry_basis_sign_flip": None,
            "attestation": None,
            "provenance": {"config_fingerprint": config_fingerprint, "computed_at": _iso_utc_now()},
        }
        if evidence_family == "strategy":
            # spec Sec3.7/Sec9 item 6 + goal.md J-08 Step 1: the Card-6.4 forming-bar caveat
            # (already stamped per-observation by `_strategy_observation`) plus the null-design
            # disclosure, served ONCE per evaluation record rather than re-served per observation.
            fields["provenance"]["basis_caveats"] = [
                REFEREE_FORMING_BAR_BASIS_CAVEAT, REFEREE_STRATEGY_NULL_DESIGN_CAVEAT,
            ]

        if _aborted():
            _log(state="cancelled", done=done_units, total=total_units, error=None)
            return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
        fields["attestation"] = run_oracle_attestation()
        _tick()

        if confirmatory_eligible:
            if _aborted():
                _log(state="cancelled", done=done_units, total=total_units, error=None)
                return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
            perm = permutation_test(
                pool["session_groups"], hypothesis_id, sidedness=hypothesis["sidedness"]
            )
            if perm["state"] == "ok":
                fields["T"] = perm["t"]
                fields["permutation_p"] = perm["p"]
                fields["permutation_enumeration"] = perm["enumeration"]
                fields["min_attainable_p"] = perm["min_attainable_p"]
        _tick()

        if pool["session_groups"]:
            if _aborted():
                _log(state="cancelled", done=done_units, total=total_units, error=None)
                return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
            ci_cluster = bootstrap_ci_cluster(pool["session_groups"], hypothesis_id)
            fields["ci_cluster"] = (
                [ci_cluster["ci_low"], ci_cluster["ci_high"]] if ci_cluster["state"] == "ok"
                else INSUFFICIENT_SAMPLE
            )
        _tick()

        if pool["session_groups"]:
            if _aborted():
                _log(state="cancelled", done=done_units, total=total_units, error=None)
                return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
            sign_flip = sign_flip_result(
                pool["session_groups"], hypothesis_id, sidedness=hypothesis["sidedness"]
            )
            if sign_flip["state"] == "ok":
                fields["sign_flip_p"] = sign_flip["p"]
            equal_weight = equal_weight_t(pool["session_groups"])
            if equal_weight["state"] == "ok":
                fields["equal_weight_T"] = equal_weight["t"]
        _tick()

        if pool.get("occurrence_diffs"):
            if _aborted():
                _log(state="cancelled", done=done_units, total=total_units, error=None)
                return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
            ci_occ = bootstrap_ci_occurrence(pool["occurrence_diffs"], hypothesis_id)
            fields["ci_occurrence"] = (
                [ci_occ["ci_low"], ci_occ["ci_high"]] if ci_occ["state"] == "ok"
                else INSUFFICIENT_SAMPLE
            )
        _tick()

        if estimand in _ESTIMANDS_AGAINST_NULL and pool["session_groups"]:
            if _aborted():
                _log(state="cancelled", done=done_units, total=total_units, error=None)
                return {"cancelled": True, "record": None, "snapshot": None, "reused": False}
            entry_basis_groups = _entry_basis_session_groups(pool, bar_store)
            if entry_basis_groups:
                entry_t, _deltas, _weights = _t_statistic(entry_basis_groups)
                fields["entry_basis_T"] = entry_t
                if primary_t is not None:
                    fields["entry_basis_sign_flip"] = _signs_differ(entry_t, primary_t)
        _tick()

        # iter-8 Rider 1 (evaluator-diagnosed, iteration 7): a failed oracle attestation must
        # never mint the hypothesis's ONE permanent checkpoint snapshot -- the WRITE side needs
        # the SAME gate the READ side (`_snapshot_fold`, via `verify_oracle_attestation`) already
        # carries, because the read side can be re-run and an append-only record cannot.
        # Downgrades ONLY the "checkpoint" case: "monitoring"/"pending" never write a snapshot
        # regardless (only `role == "checkpoint"` reaches `_build_and_record_snapshot` below), so
        # nothing else changes. Every other field (T/permutation_p/CIs/etc.) stays exactly as
        # computed above -- they are honest descriptive numbers regardless of attestation state;
        # only the permanent-write eligibility is gated.
        if fields["role"] == "checkpoint" and not fields["attestation"]["passed"]:
            fields["role"] = "pending"

        recorded = evaluation_store.record(fields)
    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised verbatim, never swallowed
        _log(state="failed", done=done_units, total=total_units, error=str(exc))
        raise

    snapshot = None
    certificate = None
    if recorded["role"] == "checkpoint":
        try:
            snapshot = _build_and_record_snapshot(
                recorded, family_store=family_store, evaluation_store=evaluation_store,
                snapshot_store=snapshot_store,
            )
        except Exception as exc:  # noqa: BLE001
            _log(state="failed", done=done_units, total=total_units, error=str(exc))
            raise
        # J-08 Step 2 (spec Sec8): the certificate's REAL mint call site -- reachable ONLY through
        # this fresh-compute path, and only for a strategy-family hypothesis whose caller supplied
        # its own live scan identity (TC-11/TC-12: a Playbook checkpoint or an unsupplied
        # `certificate_mint` mints nothing).
        if evidence_family == "strategy" and certificate_mint is not None:
            try:
                certificate = _mint_strategy_certificate(
                    hypothesis=hypothesis, recorded=recorded, snapshot=snapshot, **certificate_mint,
                )
            except Exception as exc:  # noqa: BLE001
                _log(state="failed", done=done_units, total=total_units, error=str(exc))
                raise

    _log(state="completed", done=total_units, total=total_units, error=None)
    return {
        "cancelled": False, "record": recorded, "snapshot": snapshot, "reused": False,
        "certificate": certificate,
    }


# === the single-flight-per-hypothesis compute manager ==================================================

_IDLE_SNAPSHOT_TEMPLATE: dict = {
    "id": None, "status": "idle", "hypothesis_id": None, "done": 0, "total": 0, "error": None,
}


class RefereeEvaluationComputeManager:
    """Owns one in-flight (or last-terminal) evaluation job PER ``hypothesis_id`` -- mirrors
    ``RefereeNullComputeManager`` exactly (single-flight per key, not process-global; one lock; an
    in-memory process-scoped snapshot per key; cooperative cancel; an atomic snapshot publish under
    the lock)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshots: dict[str, dict] = {}
        self._job_ids: dict[str, str] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}

    def snapshot(self, hypothesis_id: str) -> dict:
        current = self._snapshots.get(hypothesis_id)
        return (
            dict(current) if current is not None
            else {**_IDLE_SNAPSHOT_TEMPLATE, "hypothesis_id": hypothesis_id}
        )

    def trigger(
        self,
        hypothesis_id: str,
        *,
        hypothesis_store: HypothesisStore,
        family_store: FamilyStore,
        playbook_store: PlaybookStore,
        bar_store: BarStore,
        config: Config,
        null_store: RefereeNullStore,
        evaluation_store: RefereeEvaluationStore,
        snapshot_store: AdjudicationSnapshotStore,
        run_store: RefereeEvaluationRunStore | None = None,
    ) -> dict:
        """Start a NEW evaluation job for ``hypothesis_id``, or -- if one is already ``status`` in
        (``"running"``, ``"cancelling"``) -- return it UNCHANGED (``started: False``, single-flight
        per key, TC-32). Never blocks -- the walk runs on a dedicated worker thread."""
        if hypothesis_store.get(hypothesis_id) is None:
            raise ValueError(f"unknown hypothesis_id {hypothesis_id!r}")
        with self._lock:
            current = self._snapshots.get(hypothesis_id)
            if current is not None and current["status"] in ("running", "cancelling"):
                return {"started": False, "compute": dict(current)}

            job_id = uuid.uuid4().hex
            self._job_ids[hypothesis_id] = job_id
            cancel_event = threading.Event()
            self._cancel_events[hypothesis_id] = cancel_event
            snapshot = {
                "id": job_id, "status": "running", "hypothesis_id": hypothesis_id,
                "done": 0, "total": 0, "error": None,
            }
            self._snapshots[hypothesis_id] = snapshot

        def _publish(entry: dict) -> None:
            with self._lock:
                if self._job_ids.get(hypothesis_id) != job_id:
                    return
                current = self._snapshots.get(hypothesis_id)
                if current is None:
                    return
                self._snapshots[hypothesis_id] = {
                    **current, "done": entry["done"], "total": entry["total"],
                }

        def _work() -> None:
            try:
                run_evaluation_and_record(
                    hypothesis_id, hypothesis_store=hypothesis_store, family_store=family_store,
                    playbook_store=playbook_store, bar_store=bar_store, config=config,
                    null_store=null_store, evaluation_store=evaluation_store,
                    snapshot_store=snapshot_store, progress=_publish,
                    should_abort=cancel_event.is_set, run_store=run_store,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_error(hypothesis_id, job_id, str(exc))
                return
            if cancel_event.is_set():
                self._resolve_cancelled(hypothesis_id, job_id)
            else:
                self._resolve_done(hypothesis_id, job_id)

        thread = threading.Thread(
            target=_work, name=f"referee-eval-compute:{hypothesis_id}", daemon=True,
        )
        with self._lock:
            self._threads[hypothesis_id] = thread
        thread.start()
        return {"started": True, "compute": dict(snapshot)}

    def _resolve_done(self, hypothesis_id: str, job_id: str) -> None:
        with self._lock:
            current = self._snapshots.get(hypothesis_id)
            if current is None or self._job_ids.get(hypothesis_id) != job_id:
                return
            self._snapshots[hypothesis_id] = {**current, "status": "done", "error": None}

    def _resolve_error(self, hypothesis_id: str, job_id: str, error: str) -> None:
        with self._lock:
            current = self._snapshots.get(hypothesis_id)
            if current is None or self._job_ids.get(hypothesis_id) != job_id:
                return
            self._snapshots[hypothesis_id] = {**current, "status": "error", "error": error}

    def _resolve_cancelled(self, hypothesis_id: str, job_id: str) -> None:
        with self._lock:
            if self._job_ids.get(hypothesis_id) != job_id:
                return
            self._snapshots[hypothesis_id] = {
                **_IDLE_SNAPSHOT_TEMPLATE, "hypothesis_id": hypothesis_id, "id": job_id,
            }

    def cancel(self, hypothesis_id: str) -> None:
        with self._lock:
            cancel_event = self._cancel_events.get(hypothesis_id)
            current = self._snapshots.get(hypothesis_id)
            if current is not None and current["status"] == "running":
                self._snapshots[hypothesis_id] = {**current, "status": "cancelling"}
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            thread.join(timeout=timeout)


# === the read-side adjudication fold: GET /research/desk/referee/adjudications ========================


def _live_fold(
    hypothesis: dict, *, playbook_store: PlaybookStore, config_fingerprint: str,
) -> dict:
    """A pure fold over recorded facts (no snapshot exists yet) -- a CHEAP recount (file reads,
    never Monte Carlo, T-8) of this hypothesis's own post-boundary accrual. ``registered`` when
    zero post-boundary sessions of any kind exist (TC-20); ``pending_forward_confirmation``
    otherwise (accrual > 0, no checkpoint yet -- whether or not it has already technically crossed
    target, since crossing target is only MEANINGFUL once an operator-run evaluation observes it)."""
    occurrences, _cache = _eligible_setup_side_occurrences(
        hypothesis, playbook_store, config_fingerprint
    )
    sessions = {occ["session_date"] for occ in occurrences}
    accrued = len(sessions)
    verdict = "registered" if accrued == 0 else "pending_forward_confirmation"
    return {
        "verdict": verdict,
        "confirmatory_output_refused": False,
        "refusal_reason": None,
        "snapshot": None,
        "live_coverage": {
            "post_boundary_sessions": accrued, "target_sessions": hypothesis["target_sessions"],
        },
    }


def _snapshot_fold(snapshot: dict) -> dict:
    """A recorded snapshot's own frozen verdict, served verbatim -- UNLESS its attestation fails
    RE-verification at fold time (never trusted from checkpoint time, T-8), in which case
    confirmatory output is refused and ``verdict`` is forced to the most conservative already-named
    non-claim token (``insufficient_sample``), never a tenth vocabulary string (the
    state/assumptions.md iter-7 interpretation)."""
    if not verify_oracle_attestation(snapshot.get("attestation")):
        return {
            "verdict": "insufficient_sample",
            "confirmatory_output_refused": True,
            "refusal_reason": (
                "the checkpoint evaluation's oracle attestation is missing, mismatched, or "
                "version-stale -- confirmatory output is refused"
            ),
            "snapshot": snapshot,
            "live_coverage": None,
        }
    return {
        "verdict": snapshot["verdict"],
        "confirmatory_output_refused": False,
        "refusal_reason": None,
        "snapshot": snapshot,
        "live_coverage": None,
    }


def _hypothesis_id_from_snapshot_filename(filename: str) -> str | None:
    """The inverse of ``AdjudicationSnapshotStore._path``'s ``f"snapshot-{hypothesis_id}.json"``
    naming -- parseable straight off the FILENAME even when the file's own JSON content is
    corrupted (the identity a snapshot integrity error can still be attributed to)."""
    if not (filename.startswith("snapshot-") and filename.endswith(".json")):
        return None
    return filename[len("snapshot-") : -len(".json")]


def _fold_one_hypothesis(
    hypothesis: dict,
    snapshot: dict | None,
    *,
    playbook_store: PlaybookStore,
    config_fingerprint: str,
    live_basis: str,
    snapshot_unverifiable: bool = False,
) -> dict:
    pinned_basis = hypothesis.get("detector_basis")
    if pinned_basis is not None and pinned_basis != live_basis:
        # basis_retired wins REGARDLESS of any other computed state (TC-21) -- checked first,
        # unconditionally, even ahead of an already-recorded (or unverifiable) snapshot.
        return {
            "verdict": "basis_retired",
            "confirmatory_output_refused": False,
            "refusal_reason": None,
            "snapshot": snapshot,
            "live_coverage": None,
        }
    if snapshot_unverifiable:
        # This hypothesis's OWN adjudication snapshot file failed its integrity check -- an honest
        # "corrupted or tampered" refusal, never a silent fall-back to the live (pre-checkpoint)
        # fold, which would otherwise misrepresent an already-checkpointed hypothesis (possibly
        # `corroborated`) as merely "pending" (T-5/T-8: never a silent drop of a permanent
        # record).
        return {
            "verdict": "insufficient_sample",
            "confirmatory_output_refused": True,
            "refusal_reason": (
                "this hypothesis's own adjudication snapshot file failed its integrity check "
                "(corrupted or tampered) -- confirmatory output is refused"
            ),
            "snapshot": None,
            "live_coverage": None,
        }
    if snapshot is not None:
        return _snapshot_fold(snapshot)
    return _live_fold(hypothesis, playbook_store=playbook_store, config_fingerprint=config_fingerprint)


def adjudications_response(
    *,
    hypothesis_store: HypothesisStore,
    snapshot_store: AdjudicationSnapshotStore,
    playbook_store: PlaybookStore,
    config_fingerprint: str,
) -> dict:
    """``GET /research/desk/referee/adjudications``'s whole body: for every registered hypothesis,
    its recorded snapshot verbatim if one exists (attestation re-verified at fold time), else a LIVE
    pure-function fold (TC-23: byte-stable across calls against an unchanged store). A hypothesis
    whose OWN snapshot file exists but fails its integrity check folds to a dedicated refusal
    (never silently treated as "no snapshot", which would misrepresent an already-checkpointed
    hypothesis). Never 404/500 on an empty or partially-corrupted registry (TC-25). Also carries
    ``integrity_errors`` (iter-8 Rider 2, evaluator-diagnosed iteration 7): ``hypothesis_store.
    list()``'s own errors, surfaced the SAME way ``referee_registry.registry_response()`` already
    surfaces its four stores' errors, instead of the ``_errors`` this function used to discard
    silently -- an integrity-error disclosure belongs on EVERY reader of a store, not just the one
    an audit happened to name."""
    hypotheses, hypothesis_errors = hypothesis_store.list()
    live_basis = current_playbook_detector_basis()
    snapshot_records, snapshot_errors = snapshot_store.list()
    snapshot_by_hypothesis_id = {r["hypothesis_id"]: r for r in snapshot_records}
    unverifiable_hypothesis_ids = {
        hid for hid in (
            _hypothesis_id_from_snapshot_filename(e["file"]) for e in snapshot_errors
        ) if hid is not None
    }
    entries = []
    for hypothesis in hypotheses:
        hypothesis_id = hypothesis["hypothesis_id"]
        folded = _fold_one_hypothesis(
            hypothesis, snapshot_by_hypothesis_id.get(hypothesis_id),
            playbook_store=playbook_store, config_fingerprint=config_fingerprint,
            live_basis=live_basis, snapshot_unverifiable=hypothesis_id in unverifiable_hypothesis_ids,
        )
        entries.append({"hypothesis_id": hypothesis_id, **folded})
    return {
        "entries": entries,
        "register": REFEREE_REGISTER,
        "integrity_errors": hypothesis_errors,
    }


# === authorize_promotion: the J-08 interlock's pure decision function (unwired this iteration) ========


def authorize_promotion(
    candidate: dict, certificate_store, live_scan_context: dict,
) -> dict:
    """A pure function (spec Sec8): does a valid, candidate-specific Referee certificate authorize
    promoting ``candidate = {"strategy_id": str, "profile": str}``? Reads the (still-empty this
    iteration) ``CertificateStore`` and ``live_scan_context`` (the live scan's OWN current report
    values: ``{"champion_identity": dict, "train_dataset": dict, "holdout_dataset": dict,
    "config_fingerprint": str, "gate_version": str, "referee_parameters_hash": str}``) -- returns
    ``{"authorized": bool, "refusal_class": str|None, "reason": str|None}``. NOT wired into
    ``pnl_scan._promote`` this iteration (J-08's job) -- a pure, unwired function only.

    **The six refusal classes, partitioned** (spec Sec8 names all six but does not fully
    disambiguate their boundaries -- this partition is an iter-7 interpretation call, logged to
    ``state/assumptions.md``, made to satisfy TC-26/27/28 literally):
    ``malformed_unverifiable`` (the certificate store itself reports an integrity error -- checked
    FIRST, fail closed) -> ``no_certificate`` (zero certificates exist for this ``strategy_id`` at
    all) -> ``wrong_candidate`` (certificates exist for this ``strategy_id`` but none for the exact
    ``profile``) -> ``stale`` (the matching certificate's champion identity, config fingerprint,
    gate version, or referee parameters hash no longer matches the live scan -- TC-27's own
    ``config_fingerprint`` mismatch case) -> ``mismatched_datasets`` (train/holdout dataset pins
    differ) -> ``failed_gates`` (``gate_results.bh_pass``/``floors_met`` is not exactly ``True``) ->
    otherwise authorized (TC-28)."""
    records, errors = certificate_store.list()
    if errors:
        return {
            "authorized": False,
            "refusal_class": "malformed_unverifiable",
            "reason": (
                f"the certificate store reports {len(errors)} unverifiable file(s) -- refusing to "
                f"authorize until they are resolved"
            ),
        }

    same_strategy = [
        record for record in records
        if record.get("candidate", {}).get("strategy_id") == candidate.get("strategy_id")
    ]
    if not same_strategy:
        return {
            "authorized": False,
            "refusal_class": "no_certificate",
            "reason": f"no certificate is recorded for strategy_id {candidate.get('strategy_id')!r}",
        }

    matching = [record for record in same_strategy if record.get("candidate") == candidate]
    if not matching:
        return {
            "authorized": False,
            "refusal_class": "wrong_candidate",
            "reason": (
                f"a certificate exists for strategy_id {candidate.get('strategy_id')!r} but not "
                f"for profile {candidate.get('profile')!r}"
            ),
        }

    certificate = matching[-1]

    if (
        certificate.get("champion_identity_at_scan_time") != live_scan_context.get("champion_identity")
        or certificate.get("config_fingerprint") != live_scan_context.get("config_fingerprint")
        or certificate.get("gate_version") != live_scan_context.get("gate_version")
        or certificate.get("referee_parameters_hash") != live_scan_context.get("referee_parameters_hash")
    ):
        return {
            "authorized": False,
            "refusal_class": "stale",
            "reason": (
                "the certificate's champion identity, config fingerprint, gate version, or "
                "referee parameters hash no longer matches the live scan"
            ),
        }

    if (
        certificate.get("train_dataset") != live_scan_context.get("train_dataset")
        or certificate.get("holdout_dataset") != live_scan_context.get("holdout_dataset")
    ):
        return {
            "authorized": False,
            "refusal_class": "mismatched_datasets",
            "reason": "the certificate's train/holdout dataset pins no longer match the live scan",
        }

    gate_results = certificate.get("gate_results") or {}
    if gate_results.get("bh_pass") is not True or gate_results.get("floors_met") is not True:
        return {
            "authorized": False,
            "refusal_class": "failed_gates",
            "reason": "the certificate's own gate_results do not pass (bh_pass / floors_met)",
        }

    return {"authorized": True, "refusal_class": None, "reason": None}


# --- The CLI warmer --------------------------------------------------------------------------------


def _cli_progress_printer() -> Callable[[dict], None]:
    def _print(entry: dict) -> None:
        print(f"  {entry['done']}/{entry['total']}", flush=True)

    return _print


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m app.research.referee_adjudicate evaluate --hypothesis-id ...``. Runs the
    evaluation act to completion against the operator's real playbook/bar/registry/null/eval store
    dirs, in-process, synchronously -- the CLI warmer precedent every desk/referee compute module
    carries."""
    parser = argparse.ArgumentParser(
        description="Referee evaluation CLI -- runs one evaluation act for a registered hypothesis "
        "and persists the result append-only to the SAME durable stores GET .../evaluations and "
        "GET .../adjudications serve."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    evaluate = subparsers.add_parser("evaluate", help="run one evaluation act for a hypothesis")
    evaluate.add_argument("--hypothesis-id", required=True)
    args = parser.parse_args(argv)

    config = CONFIG
    universe_dir = config.desk_universe_dir_resolved()
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(universe_dir))
    bar_store = get_bar_store()
    null_store = RefereeNullStore(resolve_referee_null_dir(universe_dir))
    registry_dir = resolve_referee_registry_dir(universe_dir)
    hypothesis_store = HypothesisStore(registry_dir)
    family_store = FamilyStore(registry_dir)
    eval_dir = resolve_referee_eval_dir(universe_dir)
    evaluation_store = RefereeEvaluationStore(eval_dir)
    snapshot_store = AdjudicationSnapshotStore(eval_dir)
    run_store = RefereeEvaluationRunStore(resolve_referee_eval_log_dir(universe_dir))

    result = run_evaluation_and_record(
        args.hypothesis_id,
        hypothesis_store=hypothesis_store, family_store=family_store,
        playbook_store=playbook_store, bar_store=bar_store, config=config,
        null_store=null_store, evaluation_store=evaluation_store, snapshot_store=snapshot_store,
        run_store=run_store,
    )
    if result["cancelled"]:
        print("evaluation cancelled -- no record written")
        return 0
    record = result["record"]
    reused = " (reused an existing record)" if result["reused"] else ""
    print(
        f"evaluation recorded for {args.hypothesis_id}: role={record['role']}, "
        f"evaluation_id={record['evaluation_id']}{reused}"
    )
    if result["snapshot"] is not None:
        print(f"adjudication snapshot: verdict={result['snapshot']['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
