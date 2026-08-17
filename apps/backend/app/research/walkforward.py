"""``walkforward.py`` -- Era "The Rapid Microscope" J-05: the chronological walk-forward engine

(``docs/rapid-validation-spec.md`` section 6). Fold-spec geometry (frozen, corpus-scoped, voidable
only by a recorded event -- ``walkforward_ledger.py``), purge-by-construction (session-truncated
observations, asserted every fold), Mode A rolling-origin discovery (the frozen fitting RULE is
the sequence identity, never a realized value), Mode B fixed-hypothesis evaluation (registered
first, evaluated after -- the exposure registry mechanically decides ``historical_oos`` vs
``historical_exposed_diagnostic``), the discretion-free ``WF_SURVIVOR_RULE_V1`` predicate, the
per-sequence temporal-stability (decay) view, the single-flight compute manager + CLI, and the
diagnostic acceptance run over the real 155-session playbook corpus.

**Observations are the engine's one abstract input.** Every caller -- the TR-16 synthetic
oracles, the diagnostic run's playbook-setup reader, a future J-09 pilot study -- reduces its own
corpus to a flat list of ``{session_date, symbol, value}`` dicts (``value`` already signed for the
candidate's registered direction, exactly the playbook rail's own ``side_relative`` convention)
BEFORE calling into this module's fold machinery. This mirrors ``scout.py``'s own
``extract_anchors`` -> ``compute_p_screen`` split (a corpus-specific reader feeds a corpus-
agnostic statistical core) and is what lets the TR-16 oracle proofs run entirely on hand-built
fixtures, with no real tick dataset or engine replay required (TR-16 exercises the SAME production
``screen_candidate``/fold functions Scout and this module already ship, over synthetic input --
the identical style ``test_scout.py``'s own TR-8 calibration fixture already established).

**Econ floor for a non-tick corpus (a disclosed interpretation call, T-1).** WF_SURVIVOR_RULE_V1's
condition 3 needs an economic-relevance floor (spec section 5.5), which Scout derives from quoted
SPREAD -- a quantity the PLAYBOOK BAR corpus (the diagnostic run's own source) does not carry at
all. Rather than inventing a spread proxy the spec never authorizes for bar data, a sequence's
``econ_floor`` is EXPLICITLY ``None`` when no spread-based floor applies (the diagnostic run's own
case) and condition 3 evaluates FALSE whenever ``econ_floor`` is ``None`` -- fail-closed, never a
silently-satisfied gate. A caller that DOES have a tick-corpus econ floor (a TR-16 oracle fixture,
a future J-09 study reusing Scout's own registered floor) supplies a concrete ``{floor_bps: ...}``
dict instead.

**Condition 4's own fold-level "opposite-direction screen" (a second disclosed interpretation
call).** Spec section 6.6 condition 4 says "no sufficient fold passes the section 5.3 screen in
the OPPOSITE direction" -- section 5.3 is Scout's own CANDIDATE-level, many-session block-
permutation screen; running a second full copy of that machinery per FOLD, for a rule that (unlike
a Scout candidate) may not even be tick-anchored, is out of this iteration's scope and unspecified
by name. This module reads "passes the screen in the opposite direction" as "a sufficient fold's
own effect is opposite in sign to the registered direction AND clears the SAME economic-relevance
magnitude condition 3 already uses" -- a defensible, internally-consistent reading (a large,
countervailing fold is exactly what this condition exists to catch) that invents no new
statistical apparatus and no new threshold family."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import statistics
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_playbook import PlaybookStore, compute_playbook_input_signature, resolve_desk_playbook_dir
from .desk_universe import UniverseStore
from .micro_accessor import (
    ExposureRegistry,
    has_any_exposure_entries,
    initialize_r2_exposure_registry,
    resolve_micro_exposure_registry_dir,
)
from .micro_readiness import WF_TEST_MIN_SESSIONS, WF_TRAIN_MIN_SESSIONS
from .micro_snapshots import append_run_log
from .walkforward_ledger import (
    ROW_KIND_FOLD_RESULT,
    ROW_KIND_FOLD_SPEC,
    FoldGeometryFrozenError,
    FoldStepTooSmallError,
    WalkForwardLedger,
    append_fold_result,
    compute_geometry_hash,
    fold_results_for_sequence,
    is_corpus_era_voided,
    latest_fold_spec,
    record_mode_b_predeclaration,
    record_voiding_event,
    register_fold_spec,
    sequence_ids_for_corpus,
)

__all__ = [
    "WF_TRAIN_MIN_SESSIONS",
    "WF_TEST_MIN_SESSIONS",
    "WF_MIN_SUFFICIENT_FOLDS",
    "WF_FOLD_MIN_SIGNAL_SESSIONS",
    "WF_FOLD_MIN_OBSERVATIONS",
    "WF_FOLD_MIN_SYMBOLS",
    "WF_SURVIVOR_SIGN_CONSISTENCY",
    "DIAGNOSTIC_GEOMETRY",
    "WF_SURVIVOR_RULE_V1",
    "WF_VERDICT_SURVIVOR",
    "WF_VERDICT_NOT_SURVIVOR",
    "EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC",
    "EVIDENCE_CLASS_HISTORICAL_OOS",
    "EVIDENCE_CLASS_LIVE_CONFIRMATORY",
    "PROCESS_LABEL_RULE",
    "PROCESS_LABEL_OPERATOR",
    "FOLD_STATUS_SUFFICIENT",
    "FOLD_STATUS_INSUFFICIENT",
    "PurgeExactnessError",
    "UnknownFittingRuleError",
    "FoldGeometryFrozenError",
    "FoldStepTooSmallError",
    "WalkForwardLedger",
    "register_fold_spec",
    "record_voiding_event",
    "record_mode_b_predeclaration",
    "latest_fold_spec",
    "is_corpus_era_voided",
    "sequence_ids_for_corpus",
    "fold_results_for_sequence",
    "resolve_walkforward_ledger_dir",
    "wf_stream",
    "walkforward_parameters",
    "walkforward_parameters_hash",
    "build_folds",
    "minimum_sessions_for_sufficient_folds",
    "InsufficientSessionsForFoldsError",
    "require_sufficient_sessions_for_folds",
    "assert_purge_exact",
    "observations_in_sessions",
    "summarize_fold_observations",
    "classify_evidence_class",
    "sequence_id_for",
    "compute_spec_hash",
    "parse_fitting_rule",
    "fit_training_quantile",
    "register_mode_a_origin",
    "register_mode_b_spec",
    "evaluate_mode_b_fold",
    "evaluate_survivor_rule",
    "sequence_verdict",
    "decay_view",
    "list_fold_specs",
    "list_walkforward_sequences",
    "WalkForwardComputeManager",
    "TR16_KNOWN_NULL_CORPUS_ID",
    "TR16_PLANTED_EFFECT_CORPUS_ID",
    "PLAYBOOK_DIAGNOSTIC_CORPUS_ID",
    "PLAYBOOK_DIAGNOSTIC_SETUP_IDS",
    "PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL",
    "PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE",
    "playbook_observations",
    "run_diagnostic_walkforward",
    "main",
]

# === docs/rapid-validation-spec.md section 1 -- transcribed verbatim, narrowed to this module's =====
# === own consumption (the micro_features.py/scout.py precedent for narrowing the shared table). =====

# WF_TRAIN_MIN_SESSIONS/WF_TEST_MIN_SESSIONS are imported verbatim from micro_readiness.py, which
# transcribed them FIRST (that module's own docstring: "a future J-05 dev should import these two
# names from here ... never mint a second, independently-valued copy").
WF_MIN_SUFFICIENT_FOLDS = 3
WF_FOLD_MIN_SIGNAL_SESSIONS = 8
WF_FOLD_MIN_OBSERVATIONS = 30
WF_FOLD_MIN_SYMBOLS = 2
WF_SURVIVOR_SIGN_CONSISTENCY = 0.7

# The diagnostic acceptance run's OWN predeclared geometry (spec section 6.6) -- pinned exactly at
# the WF_TRAIN_MIN_SESSIONS/WF_TEST_MIN_SESSIONS floors; embargo_sessions=5 is THIS run's own
# predeclared choice, never a universal default (spec section 6.3).
DIAGNOSTIC_GEOMETRY: dict = {
    "train_sessions": 40,
    "embargo_sessions": 5,
    "test_sessions": 20,
    "step_sessions": 20,
    "embargo_derivation": (
        "this run's own predeclared choice (spec section 6.6), not derived from an identified "
        "cross-boundary dependency -- never treated as a universal rule for any other corpus"
    ),
}

# T-2's vocabulary minefield, precisely: `WF_SURVIVOR_RULE_V1` NAMES the frozen predicate itself
# (served as `rule_name`, so a reader can tell which frozen rule version produced a verdict -- a
# future WF_SURVIVOR_RULE_V2 would be a named revision, never a silent redefinition); the sequence
# STATE the predicate produces is the SEPARATE, spec-literal token `walkforward_survivor` -- this
# era's full-token vocabulary rule ("'survivor' alone belongs to pnl_scan"), never the rule's own
# name serving double duty as the verdict value.
WF_SURVIVOR_RULE_V1 = "WF_SURVIVOR_RULE_V1"
WF_VERDICT_SURVIVOR = "walkforward_survivor"
WF_VERDICT_NOT_SURVIVOR = "not_survivor"

EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC = "historical_exposed_diagnostic"
EVIDENCE_CLASS_HISTORICAL_OOS = "historical_oos"
EVIDENCE_CLASS_LIVE_CONFIRMATORY = "live_confirmatory"

PROCESS_LABEL_RULE = "rule_process"
PROCESS_LABEL_OPERATOR = "operator_process"

FOLD_STATUS_SUFFICIENT = "sufficient"
FOLD_STATUS_INSUFFICIENT = "insufficient"

# spec section 0's ONE stream-constructor recipe, verbatim -- the scout.py `scout_stream`/
# referee_stats.py `referee_stream` precedent, mirrored (this module imports neither).
WF_STREAM_RECIPE = "{MICRO_SEED}:{scope_id}:{purpose}[:{fold_or_origin}[:{i}]]"
_MICRO_SEED = 314159
_WF_STREAM_PURPOSES = frozenset({"mode-a-fit"})


class PurgeExactnessError(Exception):
    """TR-6: an observation's own ``session_date`` is not a member of the fold-window session set
    it was handed under -- refused, so purge is ASSERTED, not merely assumed from a filter step
    that could silently drift."""


class UnknownFittingRuleError(Exception):
    """A Mode A fitting-rule string does not match any rule family this module knows how to fit
    (the closed vocabulary of ``_FITTING_RULE_PATTERN``) -- refused rather than guessed."""


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def wf_stream(scope_id: str, purpose: str, fold_or_origin: str | None = None, i: int | str | None = None) -> random.Random:
    """The ONE stream constructor (``WF_STREAM_RECIPE``, implemented verbatim -- the
    ``scout.scout_stream`` precedent)."""
    if purpose not in _WF_STREAM_PURPOSES:
        raise ValueError(f"wf_stream: unknown purpose {purpose!r}, expected one of {sorted(_WF_STREAM_PURPOSES)}")
    if i is not None and fold_or_origin is None:
        raise ValueError("wf_stream: `i` requires `fold_or_origin` (the recipe's own nesting)")
    key = f"{_MICRO_SEED}:{scope_id}:{purpose}"
    if fold_or_origin is not None:
        key += f":{fold_or_origin}"
        if i is not None:
            key += f":{i}"
    return random.Random(key)


def walkforward_parameters() -> dict:
    """Every module constant a served walk-forward result depends on, embedded verbatim (the
    ``scout.scout_parameters`` pattern) -- keyed on its hash by every persisted ledger row's
    ``params_hash``."""
    return {
        "micro_seed": _MICRO_SEED,
        "wf_train_min_sessions": WF_TRAIN_MIN_SESSIONS,
        "wf_test_min_sessions": WF_TEST_MIN_SESSIONS,
        "wf_min_sufficient_folds": WF_MIN_SUFFICIENT_FOLDS,
        "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
        "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
        "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
        "wf_survivor_sign_consistency": WF_SURVIVOR_SIGN_CONSISTENCY,
    }


def walkforward_parameters_hash() -> str:
    return _sha256(_canonical(walkforward_parameters()))


def compute_spec_hash(spec_fields: dict) -> str:
    """A pure content hash over a Mode A/B spec's own frozen fields -- excludes any wall-clock-
    derived value (the ``scout_ledger.compute_spec_hash`` precedent)."""
    return _sha256(_canonical(spec_fields))


def sequence_id_for(corpus_id: str, rule_identity: str) -> str:
    """A constant-rule SEQUENCE's own identity key (TR-14): a pure function of ``(corpus_id,
    rule_identity)`` -- ``rule_identity`` is a Mode A fitting-rule STRING (never a realized value)
    or a Mode B ``rule_id`` string. Calling this twice with the SAME two inputs always returns the
    SAME sequence id, so re-running an origin under an unchanged rule stays in one sequence
    (TC-11)."""
    return f"seq-{_sha256(_canonical([corpus_id, rule_identity]))[:16]}"


# === fold geometry + purge (spec section 6.2/6.3) ====================================================


def build_folds(session_dates: list[str], geometry: dict) -> list[dict]:
    """Pure, deterministic rolling-window fold construction over an ALREADY-SORTED-ASCENDING
    ``session_dates`` list -- fold boundaries fall ONLY on session-date boundaries (spec section
    6.2), so purge is exact BY CONSTRUCTION: train/embargo/test never overlap (``step_sessions >=
    test_sessions`` is enforced at REGISTRATION time, ``register_fold_spec``'s own TC-7 refusal,
    never re-checked here). Returns one dict per fold: ``{fold_index, origin_index, train_sessions,
    embargo_sessions, test_sessions}``; stops the instant a fold's own ``test_sessions`` window
    would run past the end of ``session_dates`` -- a below-floor remainder is simply not a fold,
    never a fabricated short one."""
    train_n = geometry["train_sessions"]
    embargo_n = geometry["embargo_sessions"]
    test_n = geometry["test_sessions"]
    step_n = geometry["step_sessions"]
    folds: list[dict] = []
    start = 0
    fold_index = 0
    while True:
        train_end = start + train_n
        embargo_end = train_end + embargo_n
        test_end = embargo_end + test_n
        if test_end > len(session_dates):
            break
        folds.append(
            {
                "fold_index": fold_index,
                "origin_index": start,
                "train_sessions": list(session_dates[start:train_end]),
                "embargo_sessions": list(session_dates[train_end:embargo_end]),
                "test_sessions": list(session_dates[embargo_end:test_end]),
            }
        )
        start += step_n
        fold_index += 1
    return folds


def minimum_sessions_for_sufficient_folds(geometry: dict) -> int:
    """The fewest total sessions a corpus must carry for ``build_folds`` to ever produce
    ``WF_MIN_SUFFICIENT_FOLDS`` folds under ``geometry`` -- fold 1's own span
    (``train+embargo+test``) plus ``WF_MIN_SUFFICIENT_FOLDS - 1`` further steps (TC-20's own "11 <
    105" arithmetic: ``DIAGNOSTIC_GEOMETRY``'s 40+5+20 + 2*20 = 105)."""
    fold_one_span = geometry["train_sessions"] + geometry["embargo_sessions"] + geometry["test_sessions"]
    return fold_one_span + (WF_MIN_SUFFICIENT_FOLDS - 1) * geometry["step_sessions"]


class InsufficientSessionsForFoldsError(Exception):
    """TR-15: a corpus does not carry enough sessions to ever produce ``WF_MIN_SUFFICIENT_FOLDS``
    folds under a given geometry -- a typed refusal (TC-20: "the 18-dataset/11-session tick corpus
    ... a typed floor-refusal naming 11 < 105"), never an empty fold report standing in for one."""


def require_sufficient_sessions_for_folds(session_dates: list[str], geometry: dict) -> None:
    """Raises ``InsufficientSessionsForFoldsError`` (naming the exact shortfall) when
    ``session_dates`` cannot possibly support ``WF_MIN_SUFFICIENT_FOLDS`` folds under ``geometry``
    -- the check a caller makes BEFORE ``build_folds`` when it wants a typed refusal rather than a
    merely-empty fold list (TC-20)."""
    minimum = minimum_sessions_for_sufficient_folds(geometry)
    if len(session_dates) < minimum:
        raise InsufficientSessionsForFoldsError(
            f"{len(session_dates)} < {minimum} -- refused (TR-15): this corpus cannot produce "
            f"WF_MIN_SUFFICIENT_FOLDS({WF_MIN_SUFFICIENT_FOLDS}) folds under this geometry"
        )


def assert_purge_exact(observations: list[dict], allowed_sessions: set[str] | list[str], *, boundary_name: str) -> None:
    """TR-6: every observation's own ``session_date`` must be a member of ``allowed_sessions`` --
    an ACTIVE assertion (not merely an assumed consequence of whatever filter produced the list),
    so a planted observation whose session crosses a fold boundary is caught, never silently
    pooled (TC-8)."""
    allowed = set(allowed_sessions)
    for observation in observations:
        session_date = observation.get("session_date")
        if session_date not in allowed:
            raise PurgeExactnessError(
                f"observation with session_date={session_date!r} is not a member of the "
                f"{boundary_name!r} session set -- refused (TR-6): a label crossing a fold "
                "boundary is never silently included"
            )


def observations_in_sessions(observations: list[dict], sessions: list[str], *, boundary_name: str) -> list[dict]:
    """Filters ``observations`` to those whose ``session_date`` is a member of ``sessions``, THEN
    asserts the result (TR-6, called for EVERY fold this module ever evaluates -- module docstring,
    "session-truncation is asserted... for every fold in the run")."""
    allowed = set(sessions)
    selected = [o for o in observations if o.get("session_date") in allowed]
    assert_purge_exact(selected, allowed, boundary_name=boundary_name)
    return selected


# === per-fold summary statistics (session-cluster mean, spec section 5.3's aggregation mirrored) ===


def summarize_fold_observations(observations: list[dict], floors: dict) -> dict:
    """One fold's own effect/n/sessions/symbols/sign -- spec section 6.6's own per-fold reporting
    fields. Effect = mean of session-cluster means (the SAME "mean of session-cluster mean deltas"
    aggregation spec section 5.3 and ``scout._observed_effect`` already use, adapted to a
    ONE-SAMPLE pool since a walk-forward fold evaluates a single already-hypothesized rule, not a
    two-cell candidate-vs-comparator screen). Below ANY of the three per-fold floors
    (``WF_FOLD_MIN_OBSERVATIONS``/``WF_FOLD_MIN_SIGNAL_SESSIONS``/``WF_FOLD_MIN_SYMBOLS``) reads
    ``insufficient`` with the failed arithmetic attached (TC-16), never a fabricated verdict."""
    n = len(observations)
    sessions: dict[str, list[float]] = {}
    symbols: set[str] = set()
    for o in observations:
        sessions.setdefault(o["session_date"], []).append(o["value"])
        symbols.add(o["symbol"])
    n_sessions = len(sessions)
    n_symbols = len(symbols)

    min_observations = floors.get("wf_fold_min_observations", WF_FOLD_MIN_OBSERVATIONS)
    min_signal_sessions = floors.get("wf_fold_min_signal_sessions", WF_FOLD_MIN_SIGNAL_SESSIONS)
    min_symbols = floors.get("wf_fold_min_symbols", WF_FOLD_MIN_SYMBOLS)

    missing: dict[str, str] = {}
    if n < min_observations:
        missing["observations"] = f"{n} < {min_observations}"
    if n_sessions < min_signal_sessions:
        missing["signal_sessions"] = f"{n_sessions} < {min_signal_sessions}"
    if n_symbols < min_symbols:
        missing["symbols"] = f"{n_symbols} < {min_symbols}"

    if missing:
        return {
            "status": FOLD_STATUS_INSUFFICIENT,
            "n": n,
            "n_sessions": n_sessions,
            "n_symbols": n_symbols,
            "effect": None,
            "sign": None,
            "missing": missing,
        }

    session_means = [statistics.mean(values) for values in sessions.values()]
    effect = statistics.mean(session_means)
    sign = "positive" if effect > 0 else ("negative" if effect < 0 else "zero")
    return {
        "status": FOLD_STATUS_SUFFICIENT,
        "n": n,
        "n_sessions": n_sessions,
        "n_symbols": n_symbols,
        "effect": effect,
        "sign": sign,
        "missing": {},
    }


# === the exposure-registry classification rule (spec section 6.7, TC-13) ============================


def classify_evidence_class(exposure_registry: ExposureRegistry, *, corpus_id: str, window_sessions: list[str], registered_at: str) -> str:
    """spec section 6.7's mechanical rule: ``historical_oos`` iff NO session in ``window_sessions``
    was exposed before ``registered_at``; else ``historical_exposed_diagnostic``. A window with
    zero sessions (an empty test window) is honestly diagnostic -- there is nothing to have been
    unexposed."""
    if not window_sessions:
        return EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    for session_date in window_sessions:
        if exposure_registry.is_exposed_before(corpus_id=corpus_id, window=session_date, instant=registered_at):
            return EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    return EVIDENCE_CLASS_HISTORICAL_OOS


# === Mode A -- rolling-origin discovery (spec section 6.4) ===========================================

# The ONE fitting-rule family this iteration implements (module docstring: Mode A is proven on
# synthetic oracles only this iteration, never against real data -- see the diagnostic run's own
# Mode B framing below). A future rule family extends this tuple/pattern, never replaces it.
_FITTING_RULE_PATTERN = re.compile(r"^training_quantile\(([01](?:\.\d+)?)\)$")


def parse_fitting_rule(rule: str) -> tuple[str, float]:
    """``"training_quantile(0.90)"`` -> ``("training_quantile", 0.90)`` -- refuses (
    ``UnknownFittingRuleError``) any string outside the closed vocabulary this module can fit
    honestly, rather than guessing (T-1)."""
    match = _FITTING_RULE_PATTERN.match(rule)
    if not match:
        raise UnknownFittingRuleError(
            f"fitting_rule {rule!r} does not match any rule family this module can fit -- refused "
            f"(closed vocabulary: {_FITTING_RULE_PATTERN.pattern})"
        )
    return "training_quantile", float(match.group(1))


def fit_training_quantile(train_values: list[float], q: float) -> float | None:
    """Nearest-rank quantile over ``train_values`` -- ``None`` (undefined, never fabricated) on an
    empty training sample."""
    if not train_values:
        return None
    ordered = sorted(train_values)
    q = min(max(q, 0.0), 1.0)
    idx = min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))
    return ordered[idx]


def register_mode_a_origin(
    ledger: WalkForwardLedger,
    exposure_registry: ExposureRegistry,
    *,
    corpus_id: str,
    fitting_rule: str,
    fold: dict,
    train_observations_provider: Callable[[], list[dict]],
    test_observations_provider: Callable[[], list[dict]],
    floors: dict,
    sidedness: str,
    econ_floor: dict | None,
    process_label: str = PROCESS_LABEL_RULE,
    registered_at: str | None = None,
) -> dict:
    """ONE Mode A origin: fits ``fitting_rule`` over the TRAIN window (via
    ``train_observations_provider``, called FIRST), freezes ``spec_hash`` (excludes the realized
    fitted value -- TR-14's own "the frozen spec identity is the fitting RULE, never the realized
    numeric value"), records ``spec_hash_recorded_at``, THEN calls
    ``test_observations_provider`` (the validation-window reveal, TC-12's own freeze-order proof),
    classifies the evidence class via the exposure registry (TC-13's rule, applied identically to
    Mode A), and appends ONE permanent ``fold_result`` row. ``sequence_id`` is a pure function of
    ``(corpus_id, fitting_rule)`` (TR-14/TC-11): re-registering the SAME rule string at a different
    origin lands in the SAME sequence; a changed rule string starts a new one."""
    rule_family, q = parse_fitting_rule(fitting_rule)
    train_observations = observations_in_sessions(
        train_observations_provider(), fold["train_sessions"], boundary_name="train_sessions"
    )
    realized_fitted_value = fit_training_quantile([o["value"] for o in train_observations], q)

    sequence_id = sequence_id_for(corpus_id, fitting_rule)
    spec_fields = {
        "mode": "A",
        "corpus_id": corpus_id,
        "fitting_rule": fitting_rule,
        "sidedness": sidedness,
        "econ_floor": econ_floor,
        "fold_index": fold["fold_index"],
    }
    spec_hash = compute_spec_hash(spec_fields)
    if registered_at is None:
        registered_at = _iso_utc_now()
    spec_hash_recorded_at = registered_at

    test_observations = observations_in_sessions(
        test_observations_provider(), fold["test_sessions"], boundary_name="test_sessions"
    )
    validation_revealed_at = _iso_utc_now()

    evidence_class = classify_evidence_class(
        exposure_registry, corpus_id=corpus_id, window_sessions=fold["test_sessions"], registered_at=registered_at
    )
    summary = summarize_fold_observations(test_observations, floors)

    row_fields = {
        "sequence_id": sequence_id,
        "corpus_id": corpus_id,
        "mode": "A",
        "fitting_rule": fitting_rule,
        "realized_fitted_value": realized_fitted_value,
        "spec_hash": spec_hash,
        "fold_index": fold["fold_index"],
        "sidedness": sidedness,
        "econ_floor": econ_floor,
        "evidence_class": evidence_class,
        "process_label": process_label,
        "registered_at": registered_at,
        "spec_hash_recorded_at": spec_hash_recorded_at,
        "validation_revealed_at": validation_revealed_at,
        **summary,
    }
    return append_fold_result(ledger, row_fields)


# === Mode B -- fixed hypothesis (spec section 6.5) ===================================================


def register_mode_b_spec(*, corpus_id: str, rule_id: str, sidedness: str, econ_floor: dict | None, registered_at: str | None = None) -> dict:
    """A human-authored, fixed-hypothesis spec (spec section 6.5) -- registered ONCE (a pure,
    in-memory construction; the PERMANENT record is the ``fold_result`` row(s) ``evaluate_mode_b_
    fold`` appends, exactly as Mode A's spec is never separately ledgered either -- module
    docstring's "one abstract input" design keeps the spec itself a plain dict a caller threads
    through, not a second store). ``sequence_id`` is a pure function of ``(corpus_id, rule_id)``."""
    sequence_id = sequence_id_for(corpus_id, rule_id)
    spec_fields = {"mode": "B", "corpus_id": corpus_id, "rule_id": rule_id, "sidedness": sidedness, "econ_floor": econ_floor}
    spec_hash = compute_spec_hash(spec_fields)
    return {
        "sequence_id": sequence_id,
        "corpus_id": corpus_id,
        "rule_id": rule_id,
        "sidedness": sidedness,
        "econ_floor": econ_floor,
        "spec_hash": spec_hash,
        "registered_at": registered_at if registered_at is not None else _iso_utc_now(),
    }


def evaluate_mode_b_fold(
    ledger: WalkForwardLedger,
    exposure_registry: ExposureRegistry,
    *,
    spec: dict,
    fold: dict,
    observations: list[dict],
    floors: dict,
    process_label: str = PROCESS_LABEL_RULE,
) -> dict:
    """Evaluates ``spec`` (a ``register_mode_b_spec`` result) against ONE fold's own test window,
    over the FULL ``observations`` corpus (filtered + purge-asserted to the fold's own test
    sessions here). Classifies the evidence class via the exposure registry's mechanical rule
    (TC-13) and appends ONE permanent ``fold_result`` row."""
    test_observations = observations_in_sessions(observations, fold["test_sessions"], boundary_name="test_sessions")
    evidence_class = classify_evidence_class(
        exposure_registry, corpus_id=spec["corpus_id"], window_sessions=fold["test_sessions"],
        registered_at=spec["registered_at"],
    )
    summary = summarize_fold_observations(test_observations, floors)
    row_fields = {
        "sequence_id": spec["sequence_id"],
        "corpus_id": spec["corpus_id"],
        "mode": "B",
        "rule_id": spec["rule_id"],
        "spec_hash": spec["spec_hash"],
        "fold_index": fold["fold_index"],
        "sidedness": spec["sidedness"],
        "econ_floor": spec["econ_floor"],
        "evidence_class": evidence_class,
        "process_label": process_label,
        "registered_at": spec["registered_at"],
        **summary,
    }
    return append_fold_result(ledger, row_fields)


# === WF_SURVIVOR_RULE_V1 (spec section 6.6, r2, frozen) ===============================================


def _eligible_folds(fold_results: list[dict]) -> tuple[list[dict], list[dict]]:
    """``(sufficient, eligible)`` -- ``sufficient`` is every fold whose OWN status cleared its
    per-fold floors (TC-16); ``eligible`` narrows that further to class ``historical_oos`` AND
    process label ``rule_process`` (spec section 6.6 condition 1's own compound test). TR-5/TC-18:
    every numeric byproduct of this rule (sign agreement, pooled effect, the opposite-direction
    check) is computed ONLY over ``eligible`` -- NEVER ``sufficient`` -- so a
    ``historical_exposed_diagnostic`` or ``operator_process`` fold sitting among otherwise-eligible
    folds is independently confirmed to contribute NOTHING to any pooled number, not merely to fail
    condition 1's own boolean."""
    sufficient = [f for f in fold_results if f["status"] == FOLD_STATUS_SUFFICIENT]
    eligible = [
        f for f in sufficient
        if f["evidence_class"] == EVIDENCE_CLASS_HISTORICAL_OOS and f["process_label"] == PROCESS_LABEL_RULE
    ]
    return sufficient, eligible


def _pooled_sign_agreement(eligible_folds: list[dict], sidedness: str) -> float:
    if not eligible_folds:
        return 0.0
    expected = "positive" if sidedness == "long" else "negative"
    agreeing = sum(1 for f in eligible_folds if f["sign"] == expected)
    return agreeing / len(eligible_folds)


def _opposite_direction_eligible_fold_exists(eligible_folds: list[dict], sidedness: str, econ_floor: dict | None) -> bool:
    """This module's own condition-4 reading (module docstring's disclosed interpretation call):
    an eligible fold is treated as "passing the screen in the opposite direction" when its own
    sign opposes the registered direction AND its magnitude clears the SAME economic-relevance
    floor condition 3 uses -- never satisfied (fail-closed) when no econ_floor applies."""
    if econ_floor is None:
        return False
    opposite = "negative" if sidedness == "long" else "positive"
    floor_bps = econ_floor.get("floor_bps")
    if floor_bps is None:
        return False
    return any(f["sign"] == opposite and abs(f["effect"]) >= floor_bps for f in eligible_folds)


def evaluate_survivor_rule(fold_results: list[dict], *, sidedness: str, econ_floor: dict | None, voided: bool) -> dict:
    """The discretion-free ``WF_SURVIVOR_RULE_V1`` predicate (spec section 6.6, all five
    conditions verbatim): returns ``walkforward_survivor`` iff ALL FIVE hold; anything less is
    ``not_survivor`` -- no override branch exists anywhere in this function. Does NOT itself refuse
    below the ``WF_MIN_SUFFICIENT_FOLDS`` floor with a distinct "insufficient" response -- that is
    ``sequence_verdict``'s own job (TC-17); this function always evaluates and reports all five
    conditions, which is exactly what TC-15's own "violate any ONE of the five individually" proof
    needs to observe."""
    sufficient, eligible = _eligible_folds(fold_results)

    condition_1 = len(sufficient) >= WF_MIN_SUFFICIENT_FOLDS and len(eligible) == len(sufficient)
    sign_agreement = _pooled_sign_agreement(eligible, sidedness)
    condition_2 = sign_agreement >= WF_SURVIVOR_SIGN_CONSISTENCY

    pooled_effect = statistics.mean([f["effect"] for f in eligible]) if eligible else None
    expected_sign = "positive" if sidedness == "long" else "negative"
    condition_3 = (
        pooled_effect is not None
        and econ_floor is not None
        and econ_floor.get("floor_bps") is not None
        and ((pooled_effect > 0) == (expected_sign == "positive"))
        and abs(pooled_effect) >= econ_floor["floor_bps"]
    )

    condition_4 = not _opposite_direction_eligible_fold_exists(eligible, sidedness, econ_floor)
    condition_5 = not voided

    conditions = {
        "sufficient_oos_rule_process_folds": condition_1,
        "sign_agreement": condition_2,
        "pooled_effect_clears_econ_floor": condition_3,
        "no_opposite_direction_sufficient_fold": condition_4,
        "zero_voiding_events": condition_5,
    }
    is_survivor = all(conditions.values())
    return {
        "verdict": WF_VERDICT_SURVIVOR if is_survivor else WF_VERDICT_NOT_SURVIVOR,
        "rule_name": WF_SURVIVOR_RULE_V1,
        "conditions": conditions,
        "n_sufficient_folds": len(sufficient),
        "n_eligible_folds": len(eligible),
        "sign_agreement": sign_agreement,
        "pooled_effect": pooled_effect,
    }


def sequence_verdict(fold_results: list[dict], *, sidedness: str, econ_floor: dict | None, voided: bool) -> dict:
    """The ACTUAL "sequence-level verdict" entry point (spec section 6.6: "a sequence with <
    WF_MIN_SUFFICIENT_FOLDS sufficient folds refuses a sequence-level verdict" -- TC-17). Below the
    floor, this returns an explicit REFUSAL (``{"refused": True, "reason": ...}``) WITHOUT ever
    calling ``evaluate_survivor_rule`` -- never a computed verdict over an insufficient sample. At
    or above the floor, delegates to ``evaluate_survivor_rule`` for the full five-condition
    predicate."""
    sufficient = [f for f in fold_results if f["status"] == FOLD_STATUS_SUFFICIENT]
    if len(sufficient) < WF_MIN_SUFFICIENT_FOLDS:
        return {
            "refused": True,
            "reason": f"{len(sufficient)} < {WF_MIN_SUFFICIENT_FOLDS} sufficient folds -- a "
            "sequence-level verdict is refused (spec section 6.6), never a fabricated result",
            "n_sufficient_folds": len(sufficient),
        }
    return {"refused": False, **evaluate_survivor_rule(fold_results, sidedness=sidedness, econ_floor=econ_floor, voided=voided)}


# === the temporal-stability (decay) view (spec section 6.6) ==========================================


def decay_view(fold_results: list[dict]) -> dict:
    """Per constant-rule sequence: per-fold effect/n/sessions/sign/class/process-label rows, plus
    a recent-vs-older consistency line (the newer half's sign-agreement vs the older half's, over
    SUFFICIENT folds only) -- pooling ACROSS folds into one number is explicitly refused here
    (spec section 6.6: "pooling across sequences is refused"; this view reports per-fold, never a
    merged statistic)."""
    ordered = sorted(fold_results, key=lambda f: f["fold_index"])
    rows = [
        {
            "fold_index": f["fold_index"],
            "status": f["status"],
            "effect": f["effect"],
            "n": f["n"],
            "n_sessions": f["n_sessions"],
            "sign": f["sign"],
            "evidence_class": f["evidence_class"],
            "process_label": f["process_label"],
        }
        for f in ordered
    ]
    sufficient = [f for f in ordered if f["status"] == FOLD_STATUS_SUFFICIENT]
    half = len(sufficient) // 2
    older, recent = sufficient[:half], sufficient[half:]

    def _sign_share(folds: list[dict], sign: str) -> float | None:
        return (sum(1 for f in folds if f["sign"] == sign) / len(folds)) if folds else None

    recency = {
        "older_fold_count": len(older),
        "recent_fold_count": len(recent),
        "older_positive_share": _sign_share(older, "positive"),
        "recent_positive_share": _sign_share(recent, "positive"),
    }
    return {"fold_rows": rows, "recency": recency}


# === the serving-side listing (GET /research/desk/micro/walkforward's whole body) ====================


def list_fold_specs(ledger: WalkForwardLedger) -> list[dict]:
    """Every corpus_id's CURRENT (latest-registered, never-superseded-without-a-voiding-event)
    fold spec, in first-seen order -- the ``scout.list_scout_families`` grouping precedent,
    applied to fold specs."""
    seen: list[str] = []
    for row in ledger.rows_of_kind(ROW_KIND_FOLD_SPEC):
        corpus_id = row["corpus_id"]
        if corpus_id not in seen:
            seen.append(corpus_id)
    return [latest_fold_spec(ledger, corpus_id) for corpus_id in seen]


def list_walkforward_sequences(ledger: WalkForwardLedger) -> list[dict]:
    """Every sequence with at least one registered fold_result, grouped -- each carrying its own
    ``fold_results`` (verbatim, every disclosure), ``decay_view``, and ``sequence_verdict`` (spec
    section 6.6). ``sidedness``/``econ_floor`` are read off the sequence's own last fold_result row
    (stamped identically on every row of one sequence); ``voided`` is read live from the ledger's
    own voiding-event rows for that ``corpus_id`` (TC-10: a voided corpus-era's every sequence
    reads void immediately, with no separate write needed anywhere)."""
    rows = ledger.rows_of_kind(ROW_KIND_FOLD_RESULT)
    order: list[str] = []
    by_sequence: dict[str, list[dict]] = {}
    for row in rows:
        sequence_id = row["sequence_id"]
        if sequence_id not in by_sequence:
            by_sequence[sequence_id] = []
            order.append(sequence_id)
        by_sequence[sequence_id].append(row)

    out: list[dict] = []
    for sequence_id in order:
        sequence_rows = by_sequence[sequence_id]
        last = sequence_rows[-1]
        corpus_id = last["corpus_id"]
        voided = is_corpus_era_voided(ledger, corpus_id)
        verdict = sequence_verdict(sequence_rows, sidedness=last["sidedness"], econ_floor=last["econ_floor"], voided=voided)
        out.append(
            {
                "sequence_id": sequence_id,
                "corpus_id": corpus_id,
                "mode": last.get("mode"),
                "fitting_rule": last.get("fitting_rule"),
                "rule_id": last.get("rule_id"),
                "sidedness": last["sidedness"],
                "econ_floor": last["econ_floor"],
                "voided": voided,
                "fold_results": sequence_rows,
                "decay_view": decay_view(sequence_rows),
                "sequence_verdict": verdict,
            }
        )
    return out


# === the single-flight compute manager (the ScoutComputeManager pattern, mirrored) ===================

_IDLE_SNAPSHOT: dict = {
    "run_id": None,
    "state": "idle",
    "progress": {"steps_total": 0, "steps_done": 0, "current_step": None},
    "started_utc": None,
    "finished_utc": None,
    "error": None,
}


class WalkForwardComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) walk-forward job for this process --
    single-flight, pollable progress, cooperative cancel, TERMINAL-STATE-ONLY run-log writes (the
    iteration-2 lesson, explicitly named for this manager: a mid-run exception resolves the run to
    ``"failed"``, never a silently-short run-log write -- note this is the RUN LOG's own
    discipline; every individual ``fold_result``/``fold_spec``/``voiding_event`` row the run
    produces along the way is ALREADY a separate, permanent ledger row the instant it is appended,
    exactly like ``ScoutComputeManager``'s own per-candidate ledger writes -- see that class's own
    docstring for why "terminal-state-only" describes the run-progress log, not the evidentiary
    ledger, which is append-only by design and never "short" in any other sense). The iteration-4
    tail-anchor lesson is already baked into ``WalkForwardLedger`` (via ``HashChainedLedger``) from
    day one, not retrofitted -- see ``micro_chain_ledger.py``'s own module docstring."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict = dict(_IDLE_SNAPSHOT)
        self._run_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._snapshot)

    def trigger(self, work_fn: Callable[[Callable[[str], None], Callable[[], bool]], dict], *, run_log_dir: str, steps_total: int = 1) -> dict:
        """Start a NEW job running ``work_fn(publish, should_abort)`` on a worker thread, or --
        if one is already ``"running"`` -- refuse (single-flight, TC-25). ``work_fn`` returns a
        dict of extra terminal-log fields (e.g. ``{"folds_written": N}``) merged into the run-log
        entry on success."""
        with self._lock:
            if self._snapshot["state"] == "running":
                return {"state": "refused", "reason": "already_running"}
            run_id = uuid.uuid4().hex
            self._run_id = run_id
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            self._snapshot = {
                "run_id": run_id,
                "state": "running",
                "progress": {"steps_total": steps_total, "steps_done": 0, "current_step": None},
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
            }
            published = dict(self._snapshot)

        def _publish(step_name: str) -> None:
            with self._lock:
                if self._run_id != run_id:
                    return
                current = self._snapshot
                self._snapshot = {
                    **current,
                    "progress": {
                        **current["progress"],
                        "steps_done": current["progress"]["steps_done"] + 1,
                        "current_step": step_name,
                    },
                }

        def _work() -> None:
            try:
                extra = work_fn(_publish, cancel_event.is_set) or {}
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_terminal(run_id, run_log_dir, "failed", error=str(exc))
                return
            if cancel_event.is_set():
                self._resolve_terminal(run_id, run_log_dir, "cancelled", extra=extra)
            else:
                self._resolve_terminal(run_id, run_log_dir, "done", extra=extra)

        thread = threading.Thread(target=_work, name=f"walkforward-compute:{run_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return published

    def _resolve_terminal(self, run_id: str, run_log_dir: str, state: str, *, error: str | None = None, extra: dict | None = None) -> None:
        with self._lock:
            if self._run_id != run_id:
                return
            current = self._snapshot
            finished_utc = _iso_utc_now()
            self._snapshot = {**current, "state": state, "finished_utc": finished_utc, "error": error}
            entry = {
                "run_id": run_id,
                "state": state,
                "started_utc": current["started_utc"],
                "finished_utc": finished_utc,
                "steps_done": current["progress"]["steps_done"],
                "steps_total": current["progress"]["steps_total"],
                "error": error,
                **(extra or {}),
            }
        append_run_log(run_log_dir, entry)

    def cancel(self) -> dict:
        with self._lock:
            cancel_event = self._cancel_event
            is_running = self._snapshot["state"] == "running"
        if cancel_event is not None:
            cancel_event.set()
        return {"state": "cancelled", "accepted": is_running}

    def join_all(self, timeout: float = 30.0) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# === TR-16 oracle corpus ids (fixtures live in tests/; these are the corpus_id constants both the ===
# === test module and this module's own doctring/CLI reference) =======================================

TR16_KNOWN_NULL_CORPUS_ID = "tr16_known_null_corpus"
TR16_PLANTED_EFFECT_CORPUS_ID = "tr16_planted_effect_corpus"


# === the diagnostic acceptance run (spec section 6.6, goal.md J-05 IN SCOPE item 8) ==================

PLAYBOOK_DIAGNOSTIC_CORPUS_ID = "playbook_setups_diagnostic_v1"

# The small, predeclared, already-frozen playbook setup definitions this run's candidate rules are
# built from (goal.md: "the specific subset is an implementation choice logged at registration
# time, never invented from outcomes") -- range_trade and capitulation, the two setups this
# project's own prior band-context study (2026-08-13, memory) already found the most descriptively
# interesting ("range_trade gains at a wall, capitulation reverses"), reused here as a disclosed,
# NON-outcome-tuned starting point (this run reads their ALREADY-recorded forward statistics
# unconditionally, never re-selects based on what this run itself finds).
PLAYBOOK_DIAGNOSTIC_SETUP_IDS: tuple[str, ...] = ("range_trade", "capitulation")

# The frozen horizon label (desk_forward.DESK_FORWARD_HORIZONS_MINUTES) this run's effect input is
# read from -- "1h" (60 minutes): always computable on the playbook's own 5m detection series
# (60 % 5 == 0, so no coarser-basis degrade), materially longer than 1m/5m (less noise) and less
# frequently session-truncated than 4h intraday.
PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL = "1h"

# The isolated 2025-06-03 record (goal.md: "the 2025-06 orphan excluded, disclosed") -- the next
# recorded session is 2026-01-02, a ~7-month gap; excluded so the corpus's own session-date
# ordering is a genuine, contiguous trading calendar rather than one artifact date sitting alone.
PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE = "2025-06-03"


def playbook_observations(
    playbook_store, *, setup_ids: tuple[str, ...], horizon_label: str, default_signature: str, exclude_session_dates: tuple[str, ...] = ()
) -> list[dict]:
    """Reads the ALREADY-RECORDED playbook corpus (``desk_playbook.PlaybookStore``, Era B2's own
    frozen store -- this era never re-detects or re-measures a signal) into a flat ``{session_date,
    symbol, value}`` observation list: one row per recorded signal whose ``setup_id`` is in
    ``setup_ids``, pooled ONLY from records matching ``default_signature`` (the
    ``desk_playbook_evidence.fold_evidence`` "the evidence pools exactly ONE signature" precedent,
    mirrored -- multiple recorded versions of the same session_date under DIFFERENT parameter
    signatures are never silently mixed), and ONLY signals whose OWN forward horizon leaf is
    measured and NOT session-truncated (spec section 4: "truncated rows excluded from averages").
    ``value`` is ``forward.horizons[horizon_label].return_pct`` verbatim -- already side-relative
    signed (``desk_playbook.PLAYBOOK_RETURN_SIGN_CONVENTION == "side_relative"``), so a positive
    value already means "worked in the setup's own registered direction", uniformly across every
    setup_id -- never a second, independent sign derivation."""
    records, _errors = playbook_store.list()
    observations: list[dict] = []
    for record in records:
        if record.get("playbook_input_signature") != default_signature:
            continue
        session_date = record["session_date"]
        if session_date in exclude_session_dates:
            continue
        for signal in record.get("signals", []):
            if signal.get("setup_id") not in setup_ids:
                continue
            horizon = signal.get("forward", {}).get("horizons", {}).get(horizon_label)
            if horizon is None or horizon.get("return_pct") is None or horizon.get("truncated"):
                continue
            observations.append(
                {
                    "session_date": session_date,
                    "symbol": signal["symbol"],
                    "value": horizon["return_pct"],
                    "setup_id": signal["setup_id"],
                }
            )
    return observations


def run_diagnostic_walkforward(
    ledger: WalkForwardLedger,
    exposure_registry: ExposureRegistry,
    playbook_store,
    universe_store,
    bar_store,
    config: Config,
    *,
    progress: Callable[[str], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """The ONE diagnostic acceptance run (goal.md J-05 IN SCOPE item 8): predeclares its Mode B
    spec for ``PLAYBOOK_DIAGNOSTIC_SETUP_IDS`` as the FIRST act of this function -- ledgered
    (``record_mode_b_predeclaration``, a permanent hash-chained ``mode_b_spec`` row) before this
    function reads a single byte of any store, let alone an outcome -- then registers
    ``DIAGNOSTIC_GEOMETRY`` for ``PLAYBOOK_DIAGNOSTIC_CORPUS_ID``, builds folds over the real
    155-session playbook corpus (the 2025-06 orphan excluded), and evaluates every fold through
    Mode B -- every row is `historical_exposed_diagnostic` by construction, since the exposure
    registry's r2 initialization ALREADY marks the whole playbook corpus exposed (module docstring;
    ``initialize_r2_exposure_registry`` must already have been run against this same
    ``exposure_registry`` for this to hold, and if it has not, the mechanical exposure rule still
    classifies every window honestly from whatever IS on record -- never a special-cased 'diagnostic
    always' shortcut). Never a blocking pytest recomputation (the Constraints' own iteration-hygiene
    rail) -- this function is the ONE body both ``WalkForwardComputeManager``'s worker and the CLI's
    ``main()`` call."""
    # THE PREDECLARATION, FIRST -- before this function reads anything at all (goal.md J-05 IN
    # SCOPE item 8: "predeclare (ledgered, before any outcome read) ... the run's candidate
    # rule(s)"; spec section 6.5's own "registered (ledger row, spec hash, timestamp) FIRST").
    # Neither the corpus_id nor the rule_id depends on a single byte of corpus data, so nothing
    # forces this below the store reads -- and putting it first makes the registration-first
    # discipline a hash-chained FACT on disk (`record_mode_b_predeclaration`) rather than an
    # ordering a reader has to take on trust. `registered_at` is then read back off the ledgered
    # row, so a repeat run reuses the FIRST predeclaration instant (the instant spec section
    # 6.7's own historical_oos rule compares exposure entries against), never a fresh one.
    predeclared_spec = register_mode_b_spec(
        corpus_id=PLAYBOOK_DIAGNOSTIC_CORPUS_ID,
        rule_id=f"playbook_setups:{'+'.join(PLAYBOOK_DIAGNOSTIC_SETUP_IDS)}:{PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL}:return_pct",
        sidedness="long", econ_floor=None,
    )
    predeclaration_row = record_mode_b_predeclaration(ledger, predeclared_spec)
    spec = {**predeclared_spec, "registered_at": predeclaration_row["registered_at"]}

    records, _errors = universe_store.list()
    members = list(records[-1]["members"]) if records else []
    default_signature = compute_playbook_input_signature(bar_store, members, config.config_fingerprint())

    playbook_records, _pb_errors = playbook_store.list()
    session_dates = sorted(
        {
            r["session_date"]
            for r in playbook_records
            if r.get("playbook_input_signature") == default_signature
            and r["session_date"] != PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE
        }
    )

    # r2 initialization (spec section 6.7): the playbook corpus's own aggregates have been served
    # for months (readiness, evidence, forward reports) -- this run's own corpus_id must read that
    # honestly from its FIRST evaluation, never from a registry that happens to still be empty.
    # Guarded by `has_any_exposure_entries` so a repeated trigger against the SAME durable registry
    # never re-appends the whole window list a second time (module docstring, `micro_accessor.
    # has_any_exposure_entries`'s own docstring).
    if not has_any_exposure_entries(exposure_registry, PLAYBOOK_DIAGNOSTIC_CORPUS_ID):
        initialize_r2_exposure_registry(exposure_registry, corpus_id=PLAYBOOK_DIAGNOSTIC_CORPUS_ID, windows=session_dates)

    corpus_manifest_hash = _sha256(_canonical(session_dates))
    floors = {
        "wf_fold_min_observations": WF_FOLD_MIN_OBSERVATIONS,
        "wf_fold_min_signal_sessions": WF_FOLD_MIN_SIGNAL_SESSIONS,
        "wf_fold_min_symbols": WF_FOLD_MIN_SYMBOLS,
    }
    register_fold_spec(
        ledger, corpus_id=PLAYBOOK_DIAGNOSTIC_CORPUS_ID, corpus_manifest_hash=corpus_manifest_hash,
        geometry=DIAGNOSTIC_GEOMETRY, floors=floors,
    )
    folds = build_folds(session_dates, DIAGNOSTIC_GEOMETRY)

    observations = playbook_observations(
        playbook_store, setup_ids=PLAYBOOK_DIAGNOSTIC_SETUP_IDS, horizon_label=PLAYBOOK_DIAGNOSTIC_HORIZON_LABEL,
        default_signature=default_signature, exclude_session_dates=(PLAYBOOK_DIAGNOSTIC_ORPHAN_SESSION_DATE,),
    )

    fold_rows_before = len(ledger.rows_of_kind(ROW_KIND_FOLD_RESULT))
    rows: list[dict] = []
    for fold in folds:
        if should_abort is not None and should_abort():
            break
        row = evaluate_mode_b_fold(ledger, exposure_registry, spec=spec, fold=fold, observations=observations, floors=floors)
        rows.append(row)
        if progress is not None:
            progress(f"fold-{fold['fold_index']}")

    folds_appended = len(ledger.rows_of_kind(ROW_KIND_FOLD_RESULT)) - fold_rows_before
    validation_sessions = sum(len(f["test_sessions"]) for f in folds)
    return {
        "corpus_id": PLAYBOOK_DIAGNOSTIC_CORPUS_ID,
        "folds_evaluated": len(rows),
        # An honest split of the line above: a repeat of this operator act re-evaluates the same
        # folds under the same frozen spec and REPLAYS their existing ledger rows (never a second
        # copy of the same evidence -- `walkforward_ledger.append_fold_result`'s own docstring).
        "folds_appended": folds_appended,
        "folds_replayed": len(rows) - folds_appended,
        "validation_sessions": validation_sessions,
        "session_count": len(session_dates),
        "default_signature": default_signature,
        "rows": rows,
    }


# === the CLI ===========================================================================================


def resolve_walkforward_ledger_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_WALKFORWARD_DIR`` if set, else a ``micro_walkforward`` SIBLING of the
    caller's already-resolved dataset directory -- the ``resolve_scout_ledger_dir`` pattern
    verbatim (the ``TAPEOLOGY_MICRO_*`` family, goal.md Constraints; deliberately NOT a ``Config``
    field)."""
    override = os.environ.get("TAPEOLOGY_MICRO_WALKFORWARD_DIR")
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_walkforward")


def main() -> int:
    """``python -m app.research.walkforward --diagnostic`` -- runs the diagnostic acceptance run
    against the operator's REAL playbook/universe/bar stores, synchronously, in-process (the
    ``scout``/``micro_snapshots`` CLI-warmer precedent), persisting through the SAME ledger
    ``GET /research/desk/micro/walkforward`` serves."""
    parser = argparse.ArgumentParser(
        description="Walk-forward CLI warmer -- run the diagnostic acceptance run over the real "
        "155-session playbook corpus, persisting through the SAME ledger the walkforward routes serve."
    )
    parser.add_argument("--diagnostic", action="store_true", help="run the diagnostic acceptance run (the only mode this iteration).")
    args = parser.parse_args()

    config = CONFIG
    ledger = WalkForwardLedger(resolve_walkforward_ledger_dir(config.dataset_dir_resolved()))
    exposure_registry = ExposureRegistry(resolve_micro_exposure_registry_dir(config.dataset_dir_resolved()))
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(config.desk_universe_dir_resolved()))
    universe_store = UniverseStore(config.desk_universe_dir_resolved())
    bar_store = BarStore(config.bar_dir_resolved())

    if not args.diagnostic:
        print("nothing to do -- pass --diagnostic to run the acceptance run.")
        return 0

    result = run_diagnostic_walkforward(
        ledger, exposure_registry, playbook_store, universe_store, bar_store, config,
        progress=lambda step: print(f"  [{step}] fold evaluated", flush=True),
    )
    print(
        f"diagnostic walk-forward complete: {result['folds_evaluated']} fold(s) "
        f"({result['folds_appended']} newly recorded, {result['folds_replayed']} replayed from the "
        f"existing ledger), {result['validation_sessions']} validation session(s) over "
        f"{result['session_count']} corpus session(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
