"""``scout.py`` -- Era "The Rapid Microscope" J-04: the Scout screening engine.

Implements ``docs/rapid-validation-spec.md`` section 5.3/5.4/5.5: a descriptive (never
confirmatory) screen over a frozen, pre-registered candidate spec, session-clustered
within-session circular block permutation as the null, the mandatory disclosures, and the
economic-relevance column. Registers candidates through ``scout_ledger.py``'s hash chain, enforcing
the two production-boundary rules that module deliberately does NOT (module docstring there):
``SCOUT_MAX_VARIANTS_PER_FAMILY`` (TC-9) and the TR-9 registration-ordering refusal (TC-7).

**``default_fixture_grid`` stays generic, never study-specific.** ``structure_context.kind ==
"none"`` throughout its own registered grid: every trade-anchored snapshot row is an eligible
anchor, with no playbook-signal or band-touch conditioning -- this era's OPERATOR-run production
grid (the CLI, ``ScoutComputeManager``'s default trigger) is unchanged by J-09.

**J-09 wires all three ``structure_context.kind`` combinations, in a SEPARATE, frozen
``pilot_study_candidate_grid``.** ``extract_anchors`` supports ``"band_touch"`` (via
``micro_join.enumerate_band_touches`` + ``micro_join.join_band_touch``) and ``"playbook_signal"``
(via ``micro_join.join_playbook_signal``) -- ``ScoutUnsupportedStructureContextError`` still guards
any FUTURE, genuinely-unsupported value (there is none today: the closed
``STRUCTURE_CONTEXT_KINDS`` set is fully wired). As of iteration 22, all three predeclared
pilot-study candidates (range-wall failed aggression, delta divergence at level tests, capitulation
exhaustion) are taken through ``register_and_screen_candidate``, each via its own additive grid
selector on ``ScoutComputeManager.trigger``/the CLI. Study 1's real screen still examines only its
single ``failed_aggression_score`` feature -- the eventual opposite-side ``refill_consistent``
co-occurrence condition remains T-1 (genuinely unbuilt, disclosed in the request's own frozen
comment, never invented here).

**Read-side law: no second outcome implementation.** Anchor extraction reads snapshot rows through
``micro_accessor.MicroAccessor`` (J-05 re-point, unfenced -- TR-3's import-ban; after
``load_snapshot_meta`` confirms currency, TR-7) and computes each anchor's outcome through
``micro_join.outcome_rows_after_trigger`` -- the SAME closed
outcome set ``micro_join.py`` already proved end to end. This module adds no new outcome math, only
the STATISTICAL SCREEN over outcomes ``micro_join.py`` already knows how to compute.

**The block-permutation null, mechanically (spec section 5.3).** A plain per-anchor label shuffle
is anti-conservative under autocorrelated outcome values (TR-8's own calibration target): it
destroys the LOCAL RUN structure a real candidate/comparator assignment tends to have, so the null
distribution it produces is artificially narrow, and the descriptive screen over-rejects. The fix
here is a circular BLOCK rotation: for each session, the candidate/comparator LABEL sequence (in
its own natural, snapshot-append time order) is rotated by a random multiple of the block length
against the FIXED outcome sequence -- every contiguous run in the label sequence survives intact
(only the seam moves), which is exactly what an autocorrelation-honest null needs to preserve. The
banned plain-shuffle variant is kept ONLY as ``_plain_shuffle_null_deltas`` -- a distinct, clearly
named function, reachable ONLY from ``tests/test_scout.py``'s own TR-8 counter-test, never called
from ``screen_candidate``/``register_and_screen_candidate`` or any production call path.

**Vectorized via numpy, seeded via ``random.Random`` (an explicit interpretation call).** Both null
variants need ``SCOUT_BLOCK_PERMUTATIONS`` (2,000) draws PER SESSION PER SCREENED CANDIDATE, and
TR-8's own calibration trap repeats an entire screen 200 times -- a naive per-draw Python loop is
too slow for the pinned time budgets (goal.md Constraints: "Iteration hygiene ... keep per-iteration
scope lean"). The randomness DECISION still runs through this module's one seeded stream
constructor, ``scout_stream`` (spec section 0's recipe, the ``referee_stats.referee_stream``
precedent mirrored, not imported, since this module owns no import of ``referee_stats`` and the
recipe differs); ``rng.getrandbits(63)`` then derives ONE integer seed per (session, null-draw
batch) that a ``numpy.random.default_rng`` consumes purely as a fast vectorized ENGINE for the
bulk arithmetic (drawing 2,000 shift amounts, or 2,000 full permutations, at once) -- the seed
lineage is still 100% rooted in ``random.Random(key)``, so identical inputs reproduce byte-identical
draws (spec section 0's determinism law), and numpy itself decides nothing about WHICH stream is
used, only how fast the already-decided draws are computed. Logged here, plainly, as this
iteration's own interpretation call (numpy is an existing project dependency, already used by
``levels.py`` -- no new runtime dependency).

**Evidence class is a constant this era, not a computed decision.** Every candidate this module
screens draws on the legacy tick corpus and committed hermetic fixtures -- data whose aggregates
have already been served for months (spec's own evidence-class table: "today: the whole playbook
bar corpus; the 12 legacy tick symbol-days"). ``historical_oos`` requires the exposure registry
(spec section 6.7, J-05's ``walkforward.py``), which does not exist yet -- so every screen this
module ever produces carries ``evidence_class = "historical_exposed_diagnostic"`` unconditionally,
never computed from a rule this module has no machinery to evaluate honestly."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable
from zoneinfo import ZoneInfo

import numpy as np

from ..config import CONFIG, Config
from . import micro_features as mf
from . import micro_join as mj
from . import walkforward as wf
from .datasets import DatasetNotFound, DatasetStore, parse_utc_epoch
from .micro_accessor import MicroAccessor
from .micro_snapshots import (
    append_run_log,
    exclude_withheld,
    load_snapshot_meta,
    resolve_micro_snapshots_dir,
    run_snapshot_build_and_record,
)
from .referee_null import tod_bucket_for_epoch
from .scout_ledger import (
    CLOSED_DECISIONS,
    KILL_REASONS,
    SCOUT_DECISION_SURVIVE,
    ScoutLedger,
    compute_family_root_id,
    compute_spec_hash,
    derive_family_id,
    distinct_variant_count,
    resolve_scout_ledger_dir,
)

if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
    from .desk_playbook import PlaybookStore
    from .desk_playbook_context import BandMapResolver
    from .micro_accessor import ExposureRegistry

__all__ = [
    "SCOUT_BLOCK_PERMUTATIONS",
    "SCOUT_SCREEN_ALPHA",
    "SCOUT_MAX_VARIANTS_PER_FAMILY",
    "ECON_FLOOR_SPREAD_MULTIPLE",
    "ECON_PROXY_SENTENCE",
    "SCOUT_MIN_SESSION_CLUSTERS",
    "SCOUT_MIN_OBSERVATIONS_PER_CELL",
    "SCOUT_MAX_TOP1_CONCENTRATION",
    "STRUCTURE_CONTEXT_KINDS",
    "HORIZON_KEYS",
    "FEATURE_FAMILY_OF",
    "AGGRESSOR_DERIVED_FEATURES",
    "EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC",
    "EVIDENCE_CLASS_HISTORICAL_OOS",
    "EVIDENCE_CLASS_LIVE_CONFIRMATORY",
    "ScoutRegistrationOrderingError",
    "ScoutGridExhaustedError",
    "ScoutUnsupportedHorizonError",
    "ScoutUnsupportedStructureContextError",
    "scout_stream",
    "scout_parameters",
    "scout_parameters_hash",
    "build_candidate_spec_fields",
    "extract_anchors",
    "compute_p_screen",
    "screen_candidate",
    "register_and_screen_candidate",
    "default_fixture_grid",
    "pilot_study_candidate_grid",
    "GRID_SELECTOR_RANGE_WALL_PILOT",
    "GRID_SELECTOR_DELTA_DIVERGENCE_PILOT",
    "GRID_SELECTOR_CAPITULATION_PILOT",
    "run_scout_grid_and_record",
    "register_screen_and_walkforward_check",
    "list_scout_families",
    "ScoutComputeManager",
    "main",
]

# === docs/rapid-validation-spec.md section 1 -- transcribed verbatim, narrowed to what THIS module
# consumes (the micro_readiness.py/micro_features.py precedent for narrowing the shared table). ===

SCOUT_BLOCK_PERMUTATIONS = 2_000
SCOUT_SCREEN_ALPHA = 0.05
SCOUT_MAX_VARIANTS_PER_FAMILY = 24
ECON_FLOOR_SPREAD_MULTIPLE = 1.0
ECON_PROXY_SENTENCE = (
    "quoted spread is a research cost proxy, not a full execution or tradability model"
)

# Structural floors -- the mathematical minimum for a between-cluster comparison to exist at all
# (SCOUT_MIN_SESSION_CLUSTERS: you cannot permute across fewer than 2 clusters) plus two small,
# frozen-before-any-outcome-was-read descriptive-risk ceilings. NEVER tuned from an outcome (anti-
# goal 5, "no threshold ... is chosen or revised from validation, sealed, or holdout outcomes") --
# these are structural/descriptive constants, chosen once, module constants like every other row of
# spec section 1, not a second, hidden config surface.
SCOUT_MIN_SESSION_CLUSTERS = 2
SCOUT_MIN_OBSERVATIONS_PER_CELL = 5
SCOUT_MAX_TOP1_CONCENTRATION = 0.8

STRUCTURE_CONTEXT_KINDS: tuple[str, ...] = ("playbook_signal", "band_touch", "none")

# spec section 4's horizon families (section 1's MICRO_HORIZON_* tuples), named as the candidate-
# spec's own closed `outcome.horizon_key` vocabulary -- the SAME (kind, value) pairs
# `micro_join.outcome_rows_after_trigger` already serves, never a second horizon table.
HORIZON_KEYS: dict[str, tuple[str, int]] = {
    "trades_20": ("trades", 20),
    "trades_100": ("trades", 100),
    "shares_5000": ("shares", 5_000),
    "shares_50000": ("shares", 50_000),
    "clock_seconds_30": ("clock_seconds", 30),
    "clock_seconds_60": ("clock_seconds", 60),
    "clock_seconds_300": ("clock_seconds", 300),
}

# Every `micro_observer.py` row field this module knows how to screen, mapped to its Wave-1 family
# (spec section 3) -- the `family_root_id` r2 formula's own `feature_family_name` input, and the
# single source AGGRESSOR_DERIVED_FEATURES below derives from (never a second, hand-typed list).
FEATURE_FAMILY_OF: dict[str, str] = {
    "cumulative_delta": "F-FLOW",
    "same_side_run_length": "F-FLOW",
    "volume_burst_20t": "F-FLOW",
    "volume_burst_100t": "F-FLOW",
    "rolling_imbalance_20t": "F-FLOW",
    "rolling_imbalance_100t": "F-FLOW",
    "rolling_imbalance_5000sh": "F-FLOW",
    "rolling_imbalance_50000sh": "F-FLOW",
    "absorption_score": "F-RESPONSE",
    "failed_aggression_score": "F-RESPONSE",
    "impact_efficiency_20t": "F-RESPONSE",
    "impact_efficiency_100t": "F-RESPONSE",
    "efficiency_trend_20t": "F-RESPONSE",
    "efficiency_trend_100t": "F-RESPONSE",
    "quote_imbalance": "F-LIQUIDITY",
    "microprice": "F-LIQUIDITY",
    "spread_change_20t": "F-LIQUIDITY",
    "spread_change_100t": "F-LIQUIDITY",
    # J-09 Study 2 (delta divergence at level tests): spec section 3's own F-FLOW bullet names
    # `divergence_at_level` right beside `cumulative_delta` ("Divergence-at-level (Card 9.1,
    # amended r2)") -- the SAME family, never a fourth invented one. `_extract_divergence_anchors`
    # below is this feature's dedicated PAIRED-TOUCH extraction path (module docstring's own
    # dispatch); its `feature_value` is `1.0`/`0.0` (never a fabricated third state) for
    # `divergence_at_level(...)["bearish_divergence"] is True`/`False`, reusing the EXISTING
    # threshold-transform membership check (`op="ge", value=1.0`) rather than inventing a second
    # "boolean" transform kind.
    "divergence_at_level_bearish": "F-FLOW",
}

# spec section 3/5.4: F-FLOW and F-RESPONSE are derived from the engine's aggressor SIDE
# classification; F-LIQUIDITY (quote imbalance, microprice, spread change) is not -- it never reads
# `side` at all. The fallback-tercile disclosure applies only to the former.
AGGRESSOR_DERIVED_FEATURES: frozenset = frozenset(
    name for name, family in FEATURE_FAMILY_OF.items() if family in ("F-FLOW", "F-RESPONSE")
)

EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC = "historical_exposed_diagnostic"
EVIDENCE_CLASS_HISTORICAL_OOS = "historical_oos"
EVIDENCE_CLASS_LIVE_CONFIRMATORY = "live_confirmatory"

_LEDGER_RUN_LOG_NAME = "scout"  # cosmetic only -- append_run_log/read_run_log take a root dir

_ET_ZONE = ZoneInfo("America/New_York")

# The ONE stream constructor's recipe, verbatim (spec section 0/1) -- the referee_stats.py
# `REFEREE_STREAM_RECIPE`/`referee_stream` precedent, mirrored (this module imports no referee_
# stats symbol; the two recipes differ in their bracketed segment's name).
SCOUT_STREAM_RECIPE = "{MICRO_SEED}:{scope_id}:{purpose}[:{fold_or_origin}[:{i}]]"
_SCOUT_STREAM_PURPOSES = frozenset({"block-null", "plain-shuffle-null"})


class ScoutRegistrationOrderingError(Exception):
    """TR-9: this candidate's econ-floor inputs were computed (read) AFTER its own
    ``registered_at`` timestamp. Spec section 5.5: the econ floor's formula AND concrete inputs
    must be frozen INTO the spec at registration -- never back-filled once the spec claims to be
    frozen. Refused; no ledger row is written (TC-7)."""


class ScoutGridExhaustedError(Exception):
    """``SCOUT_MAX_VARIANTS_PER_FAMILY`` (24): a family already carrying that many variants across
    every ``grid_version`` ever registered for it refuses a 25th (TC-9). Refused; no ledger row is
    written."""


class ScoutUnsupportedHorizonError(Exception):
    """``outcome.horizon_key`` names a horizon family whose permutation block length this module
    cannot yet size from the spec's own rule (section 5.3: ">= the label span in EVENTS"), so it
    refuses rather than screen under a mis-calibrated null -- see ``_block_length_for_horizon``'s
    own docstring. Refused; no ledger row is written."""


class ScoutUnsupportedStructureContextError(Exception):
    """``structure_context.kind`` names a value ``extract_anchors`` has no read path for -- as of
    J-09, this can only fire for a value outside the closed ``STRUCTURE_CONTEXT_KINDS`` set itself
    (``"none"``/``"band_touch"``/``"playbook_signal"`` are all wired -- module docstring); kept as
    the guard against any FUTURE addition to that set arriving with no extraction path yet."""


def scout_stream(
    scope_id: str, purpose: str, fold_or_origin: str | None = None, i: int | str | None = None
) -> random.Random:
    """The ONE stream constructor (``SCOUT_STREAM_RECIPE``, implemented verbatim): identical
    arguments always build the identical key string, so ``random.Random(identical_key)`` always
    reproduces the identical draw sequence."""
    if purpose not in _SCOUT_STREAM_PURPOSES:
        raise ValueError(
            f"scout_stream: unknown purpose {purpose!r}, expected one of "
            f"{sorted(_SCOUT_STREAM_PURPOSES)}"
        )
    if i is not None and fold_or_origin is None:
        raise ValueError("scout_stream: `i` requires `fold_or_origin` (the recipe's own nesting)")
    key = f"{mf.MICRO_SEED}:{scope_id}:{purpose}"
    if fold_or_origin is not None:
        key += f":{fold_or_origin}"
        if i is not None:
            key += f":{i}"
    return random.Random(key)


def scout_parameters() -> dict:
    """Every module constant a screened result depends on, embedded verbatim (the
    ``micro_features.micro_parameters`` pattern) -- keyed on its hash by every persisted ledger
    row's ``params_hash``."""
    return {
        "micro_seed": mf.MICRO_SEED,
        "scout_block_permutations": SCOUT_BLOCK_PERMUTATIONS,
        "scout_screen_alpha": SCOUT_SCREEN_ALPHA,
        "scout_max_variants_per_family": SCOUT_MAX_VARIANTS_PER_FAMILY,
        "econ_floor_spread_multiple": ECON_FLOOR_SPREAD_MULTIPLE,
        "scout_min_session_clusters": SCOUT_MIN_SESSION_CLUSTERS,
        "scout_min_observations_per_cell": SCOUT_MIN_OBSERVATIONS_PER_CELL,
        "scout_max_top1_concentration": SCOUT_MAX_TOP1_CONCENTRATION,
    }


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def scout_parameters_hash() -> str:
    return hashlib.sha256(_canonical(scout_parameters())).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


# === anchor extraction (read-side law: reuses micro_join.py's already-tested outcome machinery) ===


def _session_end_logical_ts(dataset_meta: dict) -> float:
    """Mirrors ``micro_join._session_end_logical_ts`` (private there) -- the identical tiny
    computation over PUBLIC fields (``parse_utc_epoch`` + the dataset's own ``epoch_anchor``), an
    interpretation call of the same class ``micro_join.py``'s own docstring already logs for
    mirroring rather than importing a sibling module's small technical helper."""
    end_epoch = parse_utc_epoch(dataset_meta["window_end_utc"])
    anchor = dataset_meta.get("epoch_anchor")
    return end_epoch if anchor is None else end_epoch - anchor


def _session_date_for_dataset(dataset_meta: dict) -> str:
    """The dataset's own ET session date (spec section 0: "a session is an ET RTH trading date"),
    computed ONCE from ``window_start_utc`` -- the ``micro_readiness.build_readiness`` precedent
    (a recorded RTH window never spans an ET midnight, so every anchor drawn from one dataset
    shares its single session date)."""
    parsed = datetime.fromisoformat(dataset_meta["window_start_utc"].replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(_ET_ZONE).date().isoformat()


def _cached_dataset_rows(
    dataset_id: str,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    rows_cache: dict[str, list[dict]] | None,
) -> tuple[dict | None, list[dict] | None]:
    """``(dataset_meta, rows)`` for a currently-valid snapshot -- ``(None, None)`` on any honest
    absence (no dataset, no currently-valid snapshot), never a fabricated pair. Reads through
    ``rows_cache`` when one is supplied: a caller registering MULTIPLE candidates against the SAME
    ``corpus_manifest`` in one grid run (``run_scout_grid_and_record``) would otherwise re-parse
    the identical multi-million-row snapshot JSONL file once per candidate -- measured on the real
    18-dataset corpus (~3.8M rows) to turn a 6-candidate grid run into a multi-minute stall purely
    on repeated I/O. ``rows_cache=None`` (every caller before this fix, and every test not
    explicitly opting in) behaves exactly as before: a fresh read every time, never stale relative
    to a cache another call populated."""
    try:
        dataset_meta = dataset_store.get(dataset_id)
    except DatasetNotFound:
        return None, None
    snapshot_meta = load_snapshot_meta(snapshots_dir, dataset_store, dataset_id, config)
    if snapshot_meta is None:
        return None, None
    if rows_cache is not None and dataset_id in rows_cache:
        return dataset_meta, rows_cache[dataset_id]
    # J-05 re-point (TR-3's import-ban): the ONLY door onto a snapshot's persisted rows is now
    # micro_accessor.py. `origin=None` is the disclosed UNFENCED mode (micro_accessor.py's own
    # module docstring, "Two callers, two disciplines") -- this call site has never been
    # chronologically fenced, the legacy corpus it reads is r2-pre-marked exposed regardless, and
    # fencing/exposure-logging it now would reintroduce exactly the O(n)-per-anchor cost the iter-4
    # audit's perf fixes eliminated for a registry entry that would be redundant with r2's own
    # initialization. Output is byte-identical to the direct `read_snapshot_rows` call it replaces
    # (TC-5).
    rows = MicroAccessor(dataset_store, snapshots_dir, config).read_snapshot_rows(dataset_id)
    if rows_cache is not None:
        rows_cache[dataset_id] = rows
    return dataset_meta, rows


def _outcome_at_horizon(outcomes: list[dict], horizon_kind: str, horizon_value: int) -> dict | None:
    """Picks the ONE entry matching ``(horizon_kind, horizon_value)`` out of an already-computed
    closed outcome set (``micro_join.join_band_touch``/``join_playbook_signal``'s own ``outcomes``
    list, built by ``_outcome_rows_after``) -- a LOOKUP, never a recompute (the read-side law: this
    module adds no new outcome math, module docstring)."""
    for outcome in outcomes:
        if outcome["horizon_kind"] == horizon_kind and outcome["horizon_value"] == horizon_value:
            return outcome
    return None


def _extract_none_anchors(
    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
    snapshots_dir, config, rows_cache,
) -> list[dict]:
    """``structure_context.kind == "none"`` -- every trade-anchored snapshot row is an eligible
    anchor (the ORIGINAL J-04 body, unmodified)."""
    anchors: list[dict] = []
    for entry in corpus_manifest:
        dataset_id = entry["dataset_id"]
        dataset_meta, rows = _cached_dataset_rows(
            dataset_id, dataset_store, snapshots_dir, config, rows_cache
        )
        if dataset_meta is None:
            continue  # an honest absence (no dataset, or no currently-valid snapshot) -- never
            # fabricated, never a compute-on-read
        trade_rows = [r for r in rows if not r.get("close_out")]
        session_end_ts = _session_end_logical_ts(dataset_meta)
        session_date = _session_date_for_dataset(dataset_meta)
        symbol = dataset_meta["symbol"]
        epoch_anchor = dataset_meta.get("epoch_anchor") or 0.0

        for anchor_pos, anchor_row in enumerate(trade_rows):
            feature_value = anchor_row.get(feature_name)
            if feature_value is None:
                continue  # undefined for this row (e.g. a burst ratio with too few baseline
                # windows) -- excluded, never fabricated (the whole codebase's own convention)
            # outcome_row_AT_SINGLE_HORIZON, never the full 7-horizon closed set: this loop needs
            # exactly ONE (horizon_kind, horizon_value) per anchor, and computing the other 6
            # unused horizons' own row-finding scans for every anchor of a large dataset is pure
            # waste -- measured on the real corpus to turn a should-be-fast extraction into a
            # multi-minute stall (see micro_join.outcome_row_at_single_horizon's own docstring).
            outcome = mj.outcome_row_at_single_horizon(
                trade_rows, anchor_pos, horizon_kind, horizon_value, session_end_ts, side=sidedness
            )
            if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
                continue
            anchors.append(
                {
                    "dataset_id": dataset_id,
                    "symbol": symbol,
                    "session_date": session_date,
                    "anchor_at": anchor_row["anchor_at"],
                    "trade_index": anchor_row["trade_index"],
                    "feature_value": feature_value,
                    "outcome_value": outcome["mid"]["value"],
                    "tod_bucket": tod_bucket_for_epoch(epoch_anchor + anchor_row["anchor_at"]),
                    "fallback_frac": anchor_row.get("fallback_frac_20t"),
                }
            )
    return anchors


def _extract_band_touch_anchors(
    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
    snapshots_dir, config, rows_cache, resolver,
) -> list[dict]:
    """``structure_context.kind == "band_touch"``, GENERIC single-touch path (J-09): every
    enumerated wall touch (``micro_join.enumerate_band_touches``) is one candidate anchor, joined
    via ``micro_join.join_band_touch`` (the SAME join primitive J-03 already proved -- no second
    join implementation). ``feature_name == "divergence_at_level_bearish"`` dispatches to
    ``_extract_divergence_anchors`` instead (that feature needs a PAIR of consecutive touches on
    the same band, never a single-touch row -- spec section 3's own formula)."""
    if feature_name == _DIVERGENCE_FEATURE_NAME:
        return _extract_divergence_anchors(
            corpus_manifest=corpus_manifest, dataset_store=dataset_store, snapshots_dir=snapshots_dir,
            config=config, rows_cache=rows_cache, resolver=resolver, horizon_kind=horizon_kind,
            horizon_value=horizon_value, sidedness=sidedness,
        )
    anchors: list[dict] = []
    for entry in corpus_manifest:
        dataset_id = entry["dataset_id"]
        dataset_meta, _rows = _cached_dataset_rows(
            dataset_id, dataset_store, snapshots_dir, config, rows_cache
        )
        if dataset_meta is None:
            continue  # honest absence -- never a compute-on-read (T-8)
        touches = mj.enumerate_band_touches(dataset_meta, dataset_store, resolver)
        for touch in touches:
            joined = mj.join_band_touch(touch, resolver, dataset_store, snapshots_dir, config)
            if joined["status"] != mj.JOIN_STATUS_JOINED:
                continue  # honest miss (no covering snapshot, no row before the touch)
            feature_at_trigger = joined["feature_at_trigger"]
            feature_value = feature_at_trigger.get(feature_name)
            if feature_value is None:
                continue
            outcome = _outcome_at_horizon(joined["outcomes"], horizon_kind, horizon_value)
            if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
                continue
            anchors.append(
                {
                    "dataset_id": dataset_id,
                    "symbol": touch["symbol"],
                    "session_date": _session_date_for_dataset(dataset_meta),
                    "anchor_at": feature_at_trigger["anchor_at"],
                    "trade_index": feature_at_trigger["trade_index"],
                    "feature_value": feature_value,
                    "outcome_value": outcome["mid"]["value"],
                    "tod_bucket": tod_bucket_for_epoch(touch["as_of_epoch"]),
                    "fallback_frac": feature_at_trigger.get("fallback_frac_20t"),
                }
            )
    return anchors


def _windowed_trade_volumes(
    trade_rows: list[dict], end_logical_ts: float, *, window_seconds: float, max_windows: int
) -> list[float]:
    """The trailing, NON-OVERLAPPING, WHOLE ``window_seconds``-long trade-volume windows ending at
    ``end_logical_ts`` (spec section 3's "trailing-120s volume ... over the session-prefix baseline
    windows" -- the SAME window length as the divergence trailing window itself,
    ``BURST_BASELINE_TRAILING_WINDOWS`` of them at most). Only WHOLE windows that fit entirely
    within the dataset's own recorded prefix (before ``end_logical_ts``) are ever counted -- the
    caller (``divergence_delta_threshold``) already treats fewer than 5 as undefined, so this never
    zero-pads a thin prefix into a false floor-clearing count."""
    if not trade_rows:
        return []
    earliest_ts = trade_rows[0]["anchor_at"]
    available_windows = int((end_logical_ts - earliest_ts) // window_seconds)
    n_windows = max(0, min(max_windows, available_windows))
    volumes: list[float] = []
    window_end = end_logical_ts
    for _ in range(n_windows):
        window_start = window_end - window_seconds
        volume = sum(
            row["size"] for row in trade_rows if window_start <= row["anchor_at"] < window_end
        )
        volumes.append(float(volume))
        window_end = window_start
    return volumes


def _extract_divergence_anchors(
    *, corpus_manifest, dataset_store, snapshots_dir, config, rows_cache, resolver, horizon_kind,
    horizon_value, sidedness,
) -> list[dict]:
    """Study 2's own PAIRED-touch anchor path (spec section 3, Card 9.1 amended r2): for every pair
    of CONSECUTIVE touches (tau1 < tau2) of the SAME band within one dataset, reuses
    ``micro_features.divergence_at_level`` VERBATIM over that pair's own cumulative-delta readings
    (read straight off the two touches' own snapshot rows -- never recomputed) plus a trailing
    ``(anchor_at, mid)`` price history and the session-prefix baseline trade-volume windows this
    function builds (``_windowed_trade_volumes``) -- new plumbing this iteration wires (the
    formula itself is 100% pre-coded; only its inputs were unbuilt, per the phase spec's own
    BACKGROUND). ``feature_value`` is ``1.0``/``0.0`` for ``bearish_divergence`` True/False, ``None``
    (excluded, never fabricated) when the formula itself is undefined (too little price/volume
    history). The outcome is measured FROM tau2 (``available_at = tau2`` -- spec section 3's own
    line), the later touch that fixes when the comparison could first be made."""
    anchors: list[dict] = []
    for entry in corpus_manifest:
        dataset_id = entry["dataset_id"]
        dataset_meta, rows = _cached_dataset_rows(
            dataset_id, dataset_store, snapshots_dir, config, rows_cache
        )
        if dataset_meta is None:
            continue
        touches = mj.enumerate_band_touches(dataset_meta, dataset_store, resolver)
        by_band: dict[str, list[dict]] = {}
        for touch in touches:
            by_band.setdefault(touch["band_id"], []).append(touch)

        trade_rows = [r for r in rows if not r.get("close_out")]
        session_end_ts = _session_end_logical_ts(dataset_meta)
        session_date = _session_date_for_dataset(dataset_meta)
        epoch_anchor = dataset_meta.get("epoch_anchor") or 0.0

        for band_touches in by_band.values():
            for tau1_touch, tau2_touch in zip(band_touches, band_touches[1:]):
                tau1_logical = tau1_touch["as_of_epoch"] - epoch_anchor
                tau2_logical = tau2_touch["as_of_epoch"] - epoch_anchor
                tau1_row = mj.feature_row_at_trigger(rows, tau1_logical)
                tau2_row = mj.feature_row_at_trigger(rows, tau2_logical)
                if tau1_row is None or tau2_row is None:
                    continue
                cum_delta_tau1 = tau1_row.get("cumulative_delta")
                cum_delta_tau2 = tau2_row.get("cumulative_delta")
                if cum_delta_tau1 is None or cum_delta_tau2 is None:
                    continue
                price_history = [
                    (row["anchor_at"], row["mid"])
                    for row in trade_rows
                    if tau1_logical - mf.DIVERGENCE_TRAILING_SECONDS <= row["anchor_at"] <= tau2_logical
                    and row.get("mid") is not None
                ]
                baseline_volumes = _windowed_trade_volumes(
                    trade_rows, tau1_logical,
                    window_seconds=mf.DIVERGENCE_TRAILING_SECONDS,
                    max_windows=mf.BURST_BASELINE_TRAILING_WINDOWS,
                )
                divergence = mf.divergence_at_level(
                    price_history=price_history, tau1=tau1_logical, tau2=tau2_logical,
                    cum_delta_at_tau1=cum_delta_tau1, cum_delta_at_tau2=cum_delta_tau2,
                    baseline_volumes=baseline_volumes,
                )
                bearish = divergence["bearish_divergence"]
                if bearish is None:
                    continue  # undefined (thin price/volume history) -- excluded, never fabricated
                feature_value = 1.0 if bearish else 0.0

                tau2_pos = trade_rows.index(tau2_row)
                outcome = mj.outcome_row_at_single_horizon(
                    trade_rows, tau2_pos, horizon_kind, horizon_value, session_end_ts,
                    side=sidedness,
                )
                if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
                    continue
                anchors.append(
                    {
                        "dataset_id": dataset_id,
                        "symbol": tau2_touch["symbol"],
                        "session_date": session_date,
                        "anchor_at": tau2_row["anchor_at"],
                        "trade_index": tau2_row["trade_index"],
                        "feature_value": feature_value,
                        "outcome_value": outcome["mid"]["value"],
                        "tod_bucket": tod_bucket_for_epoch(epoch_anchor + tau2_row["anchor_at"]),
                        "fallback_frac": tau2_row.get("fallback_frac_20t"),
                    }
                )
    return anchors


def _signal_in_dataset_window(signal: dict, dataset_meta: dict) -> bool:
    """A small technical window-containment check, mirroring ``micro_join._covering_dataset``'s OWN
    ``(symbol, window)`` match -- re-implemented locally (rather than imported) because it is
    scoped to ONE already-known dataset, not a store-wide search; the same class of judgment call
    ``micro_join.py``'s own docstring already documents for mirroring rather than importing a
    sibling module's small technical helper."""
    symbol = signal.get("symbol")
    trigger_ts = signal.get("trigger_ts")
    if not symbol or not trigger_ts or symbol != dataset_meta["symbol"]:
        return False
    trigger_epoch = parse_utc_epoch(trigger_ts)
    return (
        parse_utc_epoch(dataset_meta["window_start_utc"])
        <= trigger_epoch
        <= parse_utc_epoch(dataset_meta["window_end_utc"])
    )


def _extract_playbook_signal_anchors(
    *, feature_name, horizon_kind, horizon_value, sidedness, corpus_manifest, dataset_store,
    snapshots_dir, config, rows_cache, playbook_store, setup_id,
) -> list[dict]:
    """``structure_context.kind == "playbook_signal"`` (J-09): every recorded playbook signal whose
    ``(symbol, trigger_ts)`` falls inside a dataset already in ``corpus_manifest`` is one candidate
    anchor, joined via ``micro_join.join_playbook_signal`` (the SAME join primitive J-03 already
    proved). ``setup_id`` (``None`` by default) narrows to signals carrying that exact value verbatim
    (Study 3's own ``setup_id="capitulation"`` -- goal.md's stated frozen field) -- omitted, every
    recorded setup is eligible."""
    playbook_records, _errors = playbook_store.list()
    all_signals = [
        signal
        for record in playbook_records
        for signal in (record.get("signals") or [])
        if setup_id is None or signal.get("setup_id") == setup_id
    ]
    anchors: list[dict] = []
    for entry in corpus_manifest:
        dataset_id = entry["dataset_id"]
        dataset_meta, _rows = _cached_dataset_rows(
            dataset_id, dataset_store, snapshots_dir, config, rows_cache
        )
        if dataset_meta is None:
            continue
        for signal in all_signals:
            if not _signal_in_dataset_window(signal, dataset_meta):
                continue
            joined = mj.join_playbook_signal(signal, dataset_store, snapshots_dir, config)
            if joined["status"] != mj.JOIN_STATUS_JOINED:
                continue
            feature_at_trigger = joined["feature_at_trigger"]
            feature_value = feature_at_trigger.get(feature_name)
            if feature_value is None:
                continue
            outcome = _outcome_at_horizon(joined["outcomes"], horizon_kind, horizon_value)
            if outcome is None or outcome["mid"]["unmeasured"] or outcome["mid"]["truncated"]:
                continue
            trigger_epoch = parse_utc_epoch(signal["trigger_ts"])
            anchors.append(
                {
                    "dataset_id": dataset_id,
                    "symbol": signal.get("symbol"),
                    "session_date": _session_date_for_dataset(dataset_meta),
                    "anchor_at": feature_at_trigger["anchor_at"],
                    "trade_index": feature_at_trigger["trade_index"],
                    "feature_value": feature_value,
                    "outcome_value": outcome["mid"]["value"],
                    "tod_bucket": tod_bucket_for_epoch(trigger_epoch),
                    "fallback_frac": feature_at_trigger.get("fallback_frac_20t"),
                }
            )
    return anchors


_DIVERGENCE_FEATURE_NAME = "divergence_at_level_bearish"


def extract_anchors(
    *,
    feature_name: str,
    structure_context_kind: str,
    horizon_key: str,
    sidedness: str | None,
    corpus_manifest: list[dict],
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    rows_cache: dict[str, list[dict]] | None = None,
    resolver: "BandMapResolver | None" = None,
    playbook_store: "PlaybookStore | None" = None,
    setup_id: str | None = None,
) -> list[dict]:
    """One row per eligible anchor across ``corpus_manifest`` (spec section 5.1's own field -- a
    list of ``{"dataset_id": ...}`` entries): ``{dataset_id, symbol, session_date, anchor_at,
    trade_index, feature_value, outcome_value, tod_bucket, fallback_frac}``. Dispatches on
    ``structure_context_kind`` -- ``"none"`` (every trade-anchored snapshot row), ``"band_touch"``
    (every enumerated wall touch, or a paired-touch divergence row -- see
    ``_extract_band_touch_anchors``), ``"playbook_signal"`` (every recorded signal, optionally
    narrowed by ``setup_id``) -- to the matching private helper above, each of which reuses
    ``micro_join.py``'s own join primitives (no second join implementation, module docstring).
    Never triggers a snapshot build (T-8: reads never compute) -- a dataset with no currently-valid
    snapshot is an honest skip, not a fabricated row. ``rows_cache`` is the ``_cached_dataset_rows``
    opt-in -- ``None`` by default, every pre-J-09 call site's exact prior behavior.

    ``resolver`` is REQUIRED for ``structure_context_kind == "band_touch"`` (a band map cannot be
    resolved without one); ``playbook_store`` is REQUIRED for ``"playbook_signal"`` -- both raise a
    clear ``ValueError`` rather than an opaque ``AttributeError`` when omitted."""
    if structure_context_kind not in STRUCTURE_CONTEXT_KINDS:
        raise ScoutUnsupportedStructureContextError(
            f"structure_context.kind={structure_context_kind!r} is outside the closed "
            f"STRUCTURE_CONTEXT_KINDS set {STRUCTURE_CONTEXT_KINDS!r} -- refused, no read path "
            "could ever exist for an undeclared kind"
        )
    horizon_kind, horizon_value = HORIZON_KEYS[horizon_key]

    if structure_context_kind == "band_touch":
        if resolver is None:
            raise ValueError(
                "extract_anchors: structure_context_kind='band_touch' requires a resolver"
            )
        return _extract_band_touch_anchors(
            feature_name=feature_name, horizon_kind=horizon_kind, horizon_value=horizon_value,
            sidedness=sidedness, corpus_manifest=corpus_manifest, dataset_store=dataset_store,
            snapshots_dir=snapshots_dir, config=config, rows_cache=rows_cache, resolver=resolver,
        )
    if structure_context_kind == "playbook_signal":
        if playbook_store is None:
            raise ValueError(
                "extract_anchors: structure_context_kind='playbook_signal' requires a playbook_store"
            )
        return _extract_playbook_signal_anchors(
            feature_name=feature_name, horizon_kind=horizon_kind, horizon_value=horizon_value,
            sidedness=sidedness, corpus_manifest=corpus_manifest, dataset_store=dataset_store,
            snapshots_dir=snapshots_dir, config=config, rows_cache=rows_cache,
            playbook_store=playbook_store, setup_id=setup_id,
        )
    return _extract_none_anchors(
        feature_name=feature_name, horizon_kind=horizon_kind, horizon_value=horizon_value,
        sidedness=sidedness, corpus_manifest=corpus_manifest, dataset_store=dataset_store,
        snapshots_dir=snapshots_dir, config=config, rows_cache=rows_cache,
    )


def _family_median_spread_bps(
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    corpus_manifest: list[dict],
    rows_cache: dict[str, list[dict]] | None = None,
) -> float:
    """spec section 5.5: the econ floor's own input, "computed from the discovery anchors' quoted
    spreads" -- a real median over every trade row's ``spread_bps`` across the candidate's own
    corpus (never a magic constant). ``0.0`` (an honest floor, never a fabricated number) when no
    currently-valid snapshot exists yet for anything in the manifest. ``rows_cache`` is the SAME
    ``_cached_dataset_rows`` opt-in ``extract_anchors`` uses -- a candidate sharing its
    ``corpus_manifest`` with an earlier one in the SAME grid run reads every dataset's rows from
    memory here too, never a second re-parse."""
    values: list[float] = []
    for entry in corpus_manifest:
        dataset_id = entry["dataset_id"]
        _dataset_meta, rows = _cached_dataset_rows(
            dataset_id, dataset_store, snapshots_dir, config, rows_cache
        )
        if rows is None:
            continue
        for row in rows:
            if row.get("close_out"):
                continue
            bps = mf.spread_bps(row.get("spread"), row.get("mid"))
            if bps is not None:
                values.append(bps)
    return statistics.median(values) if values else 0.0


# === the pure statistical screen (feature membership, effect, block-permutation null, p_screen) ===


def _feature_membership(value: float, transform: str, params: dict) -> bool:
    if transform != "threshold":
        raise ValueError(f"unknown feature.transform {transform!r}")
    op = params["op"]
    threshold = params["value"]
    if op == "ge":
        return value >= threshold
    if op == "gt":
        return value > threshold
    if op == "le":
        return value <= threshold
    if op == "lt":
        return value < threshold
    raise ValueError(f"unknown threshold op {op!r}")


def _session_groups(anchors: list[dict], cell_of: list[str], usable_sessions: list[str]) -> dict:
    """``session_date -> {"outcomes": np.ndarray, "labels": np.ndarray(bool, True=candidate)}``,
    restricted to ``usable_sessions``, preserving each anchor's own snapshot-append (ascending
    ``anchor_at``) time order -- the order the block-rotation null's local-run preservation
    depends on."""
    groups: dict[str, dict[str, list]] = {s: {"outcomes": [], "labels": []} for s in usable_sessions}
    for anchor, cell in zip(anchors, cell_of):
        bucket = groups.get(anchor["session_date"])
        if bucket is None:
            continue
        bucket["outcomes"].append(anchor["outcome_value"])
        bucket["labels"].append(cell == "candidate")
    return {
        s: {
            "outcomes": np.array(g["outcomes"], dtype=float),
            "labels": np.array(g["labels"], dtype=bool),
        }
        for s, g in groups.items()
    }


def _session_delta(outcomes: np.ndarray, labels: np.ndarray) -> float | None:
    cand = outcomes[labels]
    comp = outcomes[~labels]
    if cand.size == 0 or comp.size == 0:
        return None
    return float(cand.mean() - comp.mean())


def _observed_effect(session_groups: dict) -> tuple[float | None, dict]:
    """spec section 5.3: "Effect = mean of session-cluster mean deltas" -- one delta per usable
    session, then the plain mean across sessions with a computable delta."""
    deltas: dict[str, float] = {}
    for session_date, g in session_groups.items():
        delta = _session_delta(g["outcomes"], g["labels"])
        if delta is not None:
            deltas[session_date] = delta
    if not deltas:
        return None, deltas
    return float(statistics.mean(deltas.values())), deltas


def _block_length_for_horizon(horizon_kind: str, horizon_value: int) -> int:
    """spec section 5.3: block length >= the label span in EVENTS of the longest horizon
    evaluated. A trade-count horizon names its span in events directly (``trades_20`` spans exactly
    20 events), so it is the one horizon family this iteration can block-size honestly.

    **A shares/clock horizon is REFUSED, not approximated (iter-4 audit fix).** The original
    implementation returned ``MICRO_HORIZON_TRADES[0]`` (20) for them, described as a "conservative
    floor" -- it is the opposite. A shares/clock horizon's true event span is whatever number of
    trades it takes to accumulate the shares, or to run out the clock: on an actively-traded
    session that is hundreds or thousands of events, so a 20-event block is far SHORTER than the
    label span, which destroys the local run structure the block design exists to preserve,
    narrows the null, and makes ``p_screen`` ANTI-CONSERVATIVE -- precisely the failure TR-8's
    calibration trap and the plain-shuffle ban exist to prevent. Section 5.3 additionally requires
    non-overlapping anchor subsampling for clock-horizon effects, which no code path here
    implements either.

    Sizing the block from the data (per session, ceiling) and wiring the subsampling are real
    work, and choosing a stand-in for them is a methodology decision this iteration's own spec
    fixes but does not authorize inventing (T-1: an unimplementable item is a drop plus an owner
    ruling, never an improvisation). So this raises, following the module's OWN established
    precedent for a path that is not yet honestly wired (``extract_anchors`` refuses a
    ``structure_context.kind`` it has no read path for). Nothing this iteration registers is
    affected: ``default_fixture_grid`` is trade-count-only by construction, and a refused
    candidate writes no ledger row -- far better than permanently ledgering a p-value the module
    knows is mis-calibrated."""
    if horizon_kind == "trades":
        return max(1, int(horizon_value))
    raise ScoutUnsupportedHorizonError(
        f"horizon_kind={horizon_kind!r} cannot be block-sized honestly yet: spec section 5.3 ties "
        "the permutation block length to the label span in EVENTS, and a shares/clock horizon's "
        "event span is data-dependent (unimplemented, together with section 5.3's non-overlapping "
        "anchor subsampling for clock horizons) -- refused rather than screened under a block "
        "shorter than the label span, which would make p_screen anti-conservative"
    )


# A (draws_batch, n) label matrix at this many elements is a few tens of MB at worst (int64
# indices, bool labels) -- bounds PEAK memory regardless of a session's own anchor count `n`. Added
# when a live run against the real corpus's NVDA dataset (~929K trade rows in its one session) tried
# to materialize a (2_000, ~900_000) matrix -- ~14 GB and climbing for JUST the index array -- a
# genuine host-stability risk on this shared, host-guard-governed machine (goal.md Constraints:
# "Host-guard caps are law"), not merely a slow path. A module constant (never a Config field, never
# a spec-governed number -- purely how much work one numpy call does at a time, not what work gets
# done): batching changes NEITHER the seed stream consumed NOR the resulting values, only how many
# numpy calls it takes to compute them (TC-11's manager/CLI byte-identity is unaffected).
_NULL_DRAW_BATCH_MAX_ELEMENTS = 10_000_000


def _batched_null_deltas(n: int, draws: int, draw_batch_fn) -> np.ndarray:
    """Calls ``draw_batch_fn(batch_size) -> np.ndarray[batch_size]`` repeatedly, each batch sized
    so ``batch_size * n <= _NULL_DRAW_BATCH_MAX_ELEMENTS`` (at least 1), concatenating the results
    -- the SAME total ``draws`` values a single unbatched call would produce, computed within
    bounded peak memory regardless of ``n``."""
    if n == 0 or draws == 0:
        return np.full(draws, np.nan)
    batch_size = max(1, _NULL_DRAW_BATCH_MAX_ELEMENTS // n)
    out = np.empty(draws, dtype=float)
    start = 0
    while start < draws:
        end = min(draws, start + batch_size)
        out[start:end] = draw_batch_fn(end - start)
        start = end
    return out


def _rotated_null_deltas(
    outcomes: np.ndarray, labels: np.ndarray, *, rng: random.Random, block_length: int, draws: int
) -> np.ndarray:
    """The production null (spec section 5.3): a random CIRCULAR rotation of the label sequence,
    quantized to multiples of the block length, against the fixed outcome sequence -- every
    contiguous label run survives (module docstring). Vectorized IN BATCHES (``_batched_null_
    deltas``) so peak memory never scales with the full ``draws x n`` product."""
    n = outcomes.size
    if n == 0:
        return np.full(draws, np.nan)
    effective_block_length = max(1, min(block_length, max(1, n - 1)))
    n_blocks = max(1, -(-n // effective_block_length))  # ceil(n / effective_block_length)
    numpy_seed = rng.getrandbits(63)
    generator = np.random.default_rng(numpy_seed)

    def _batch(batch_size: int) -> np.ndarray:
        shifts = generator.integers(0, n_blocks, size=batch_size) * effective_block_length
        idx = (np.arange(n)[None, :] - shifts[:, None]) % n  # shape (batch_size, n)
        shifted_labels = labels[idx]
        return _cell_deltas(outcomes, shifted_labels)

    return _batched_null_deltas(n, draws, _batch)


def _plain_shuffle_null_deltas(
    outcomes: np.ndarray, labels: np.ndarray, *, rng: random.Random, draws: int
) -> np.ndarray:
    """TR-8's own BANNED counter-test null (spec section 5.3: "a plain row shuffle is BANNED").
    Reachable ONLY from ``tests/test_scout.py``'s TR-8 counter-test (module docstring) -- never
    called by ``screen_candidate``/``register_and_screen_candidate`` or any production path.
    Independent per-anchor label permutation, vectorized IN BATCHES like the block variant above."""
    n = outcomes.size
    if n == 0:
        return np.full(draws, np.nan)
    numpy_seed = rng.getrandbits(63)
    generator = np.random.default_rng(numpy_seed)

    def _batch(batch_size: int) -> np.ndarray:
        perm = np.argsort(generator.random((batch_size, n)), axis=1)
        shuffled_labels = labels[perm]
        return _cell_deltas(outcomes, shuffled_labels)

    return _batched_null_deltas(n, draws, _batch)


def _cell_deltas(outcomes: np.ndarray, label_matrix: np.ndarray) -> np.ndarray:
    """``label_matrix`` shape ``(draws, n)`` (boolean, True=candidate) against the fixed
    ``outcomes`` shape ``(n,)`` -- the per-draw candidate-mean-minus-comparator-mean, ``nan`` for
    any draw that happens to put every anchor in one cell (never a division by zero)."""
    cand_sum = np.where(label_matrix, outcomes[None, :], 0.0).sum(axis=1)
    cand_n = label_matrix.sum(axis=1)
    total_sum = outcomes.sum()
    comp_sum = total_sum - cand_sum
    comp_n = outcomes.size - cand_n
    with np.errstate(invalid="ignore", divide="ignore"):
        cand_mean = np.where(cand_n > 0, cand_sum / np.maximum(cand_n, 1), np.nan)
        comp_mean = np.where(comp_n > 0, comp_sum / np.maximum(comp_n, 1), np.nan)
    delta = cand_mean - comp_mean
    delta[(cand_n == 0) | (comp_n == 0)] = np.nan
    return delta


def _null_effect_draws(
    session_groups: dict, *, seed_scope: str, block_length: int, draws: int, shuffle: str
) -> np.ndarray:
    """The aggregate null-effect distribution -- one value per simulated draw, each the mean of
    that draw's own per-session deltas (usable sessions only), mirroring ``_observed_effect``'s own
    aggregation over the real labels EXACTLY (so the observed statistic and its null are computed
    the identical way, the only honest way to compare them)."""
    per_session_draws = []
    for session_date, g in session_groups.items():
        if shuffle == "block":
            rng = scout_stream(seed_scope, "block-null", fold_or_origin=session_date)
            deltas = _rotated_null_deltas(
                g["outcomes"], g["labels"], rng=rng, block_length=block_length, draws=draws
            )
        elif shuffle == "plain":
            rng = scout_stream(seed_scope, "plain-shuffle-null", fold_or_origin=session_date)
            deltas = _plain_shuffle_null_deltas(g["outcomes"], g["labels"], rng=rng, draws=draws)
        else:
            raise ValueError(f"unknown shuffle mode {shuffle!r}")
        per_session_draws.append(deltas)
    if not per_session_draws:
        return np.full(draws, np.nan)
    stacked = np.vstack(per_session_draws)
    with np.errstate(invalid="ignore"):
        return np.nanmean(stacked, axis=0)


def _two_sided_p(observed: float | None, null_effects: np.ndarray) -> float | None:
    """``(count(|null| >= |observed|) + 1) / (n_valid_draws + 1)`` -- the standard +1/+1
    finite-permutation continuity correction (never a fabricated exact-zero p from a finite draw
    set)."""
    if observed is None:
        return None
    valid = null_effects[~np.isnan(null_effects)]
    if valid.size == 0:
        return None
    exceed = int(np.sum(np.abs(valid) >= abs(observed)))
    return float((exceed + 1) / (valid.size + 1))


def compute_p_screen(
    anchors: list[dict],
    *,
    transform: str,
    params: dict,
    seed_scope: str,
    block_length: int,
    shuffle: str = "block",
) -> tuple[float | None, float | None]:
    """PURE: given a pre-built anchor list (``feature_value``/``outcome_value``/``session_date``
    per anchor -- no dataset/snapshot I/O), returns ``(observed_effect_bps, p_screen)``. The ONE
    function ``screen_candidate`` calls for its statistical core, and the function TR-8's
    calibration test (and its banned-shuffle counter-test) calls directly against a hand-built
    synthetic corpus -- the "hand-derived oracle fixture" testing style this codebase uses
    throughout (``micro_features.py``'s own module docstring: "Statelessness is the point")."""
    cell_of = [
        "candidate" if _feature_membership(a["feature_value"], transform, params) else "comparator"
        for a in anchors
    ]
    cand_sessions = {a["session_date"] for a, c in zip(anchors, cell_of) if c == "candidate"}
    comp_sessions = {a["session_date"] for a, c in zip(anchors, cell_of) if c == "comparator"}
    usable_sessions = sorted(cand_sessions & comp_sessions)
    if len(usable_sessions) < SCOUT_MIN_SESSION_CLUSTERS:
        return None, None
    session_groups = _session_groups(anchors, cell_of, usable_sessions)
    effect_bps, _per_session = _observed_effect(session_groups)
    if effect_bps is None:
        return None, None
    null_effects = _null_effect_draws(
        session_groups,
        seed_scope=seed_scope,
        block_length=block_length,
        draws=SCOUT_BLOCK_PERMUTATIONS,
        shuffle=shuffle,
    )
    return effect_bps, _two_sided_p(effect_bps, null_effects)


# === mandatory disclosures (spec section 5.4) ======================================================


def _quantile(sorted_vals: list[float], q: float) -> float | None:
    """Nearest-rank quantile over an already-sorted list -- adequate for a DISCLOSURE (spec
    section 5.4's best-of-N line is explicitly "never a decision rule"), never presented as a
    confirmatory statistic."""
    if not sorted_vals:
        return None
    q = min(max(q, 0.0), 1.0)
    idx = min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


def _top1_share(items: list[str]) -> float:
    if not items:
        return 0.0
    counts = Counter(items)
    return max(counts.values()) / len(items)


def _concentration(cand_anchors: list[dict]) -> dict:
    """Session/symbol concentration OVER THE CANDIDATE CELL -- spec section 5.4's "session/symbol
    concentration (top-1 session share, top-1 symbol share)", the discovery population the effect
    estimate is actually drawn from."""
    return {
        "top1_session_share": _top1_share([a["session_date"] for a in cand_anchors]),
        "top1_symbol_share": _top1_share([a["symbol"] for a in cand_anchors]),
    }


def _bucket_effect(anchors: list[dict], cell_of: list[str], key_fn) -> dict:
    buckets: dict[str, dict] = {}
    for anchor, cell in zip(anchors, cell_of):
        key = key_fn(anchor)
        if key is None:
            continue
        bucket = buckets.setdefault(
            key, {"n_candidate": 0, "n_comparator": 0, "cand_sum": 0.0, "comp_sum": 0.0}
        )
        if cell == "candidate":
            bucket["n_candidate"] += 1
            bucket["cand_sum"] += anchor["outcome_value"]
        else:
            bucket["n_comparator"] += 1
            bucket["comp_sum"] += anchor["outcome_value"]
    out = {}
    for key, b in buckets.items():
        cand_mean = b["cand_sum"] / b["n_candidate"] if b["n_candidate"] else None
        comp_mean = b["comp_sum"] / b["n_comparator"] if b["n_comparator"] else None
        effect = (cand_mean - comp_mean) if (cand_mean is not None and comp_mean is not None) else None
        out[key] = {"n_candidate": b["n_candidate"], "n_comparator": b["n_comparator"], "effect_bps": effect}
    return out


def _tod_slices(anchors: list[dict], cell_of: list[str]) -> dict:
    """spec section 5.4: "ToD-bucket slices (open/mid/close -- the referee's buckets, reused)" --
    the SAME ``tod_bucket_for_epoch`` classification every anchor already carries from
    extraction."""
    return _bucket_effect(anchors, cell_of, lambda a: a["tod_bucket"] or "outside_rth")


def _fallback_tercile_slices(anchors: list[dict], cell_of: list[str], feature_name: str) -> dict | None:
    """spec section 5.4: "fallback-tercile stratification for any aggressor-derived feature" --
    ``None`` (never a fabricated slice) for a liquidity-only feature that never reads the aggressor
    side at all."""
    if feature_name not in AGGRESSOR_DERIVED_FEATURES:
        return None
    values = sorted(a["fallback_frac"] for a in anchors if a["fallback_frac"] is not None)
    if len(values) < 3:
        return {"low": None, "mid": None, "high": None, "note": "insufficient fallback_frac coverage for terciles"}
    t1 = _quantile(values, 1.0 / 3.0)
    t2 = _quantile(values, 2.0 / 3.0)

    def _tercile_key(anchor: dict) -> str | None:
        v = anchor["fallback_frac"]
        if v is None:
            return None
        if v <= t1:
            return "low"
        if v <= t2:
            return "mid"
        return "high"

    sliced = _bucket_effect(anchors, cell_of, _tercile_key)
    return {name: sliced.get(name) for name in ("low", "mid", "high")}


def _best_of_n_disclosure(null_abs_effects: list[float], n_variants_tried: int) -> dict:
    """spec section 5.4: "the family's best-of-N expected-max-under-null line (N = union variants
    tried; a DISCLOSURE, never a decision rule)" -- a Bonferroni-style corrected null threshold at
    ``SCOUT_SCREEN_ALPHA`` over N tests: with N variants tried in this family, the effect size a
    lone false positive could plausibly reach by chance grows with N; this line names that size,
    never gates on it."""
    n = max(1, n_variants_tried)
    threshold = _quantile(sorted(null_abs_effects), 1.0 - min(SCOUT_SCREEN_ALPHA / n, 1.0))
    return {
        "n": n,
        "corrected_threshold_bps": threshold,
        "sentence": (
            f"with n={n} variants tried in this family (union across grid versions), a result "
            "this extreme could arise by chance more easily than a single test's own alpha "
            f"suggests; the Bonferroni-style corrected null threshold at alpha={SCOUT_SCREEN_ALPHA} "
            f"is approximately {threshold} bps -- a disclosure, never a decision rule"
        ),
    }


def _fragile_leave_one_session_out(session_groups: dict, observed_effect: float) -> bool:
    """A minimal, real robustness check (the codebase's own "fragile" usage,
    ``referee_stats.py``'s sign-flip robustness disclosure, mirrored in spirit): drop the session
    contributing the most candidate-cell anchors and recompute; a sign flip on the remainder marks
    the candidate fragile. Only reachable once every other gate has already passed (``screen_
    candidate``'s own decision order), so a candidate never gets BOTH `killed_economic` and
    `killed_fragile` for the identical row."""
    if len(session_groups) < 2:
        return False
    sizes = {s: int(g["labels"].sum()) for s, g in session_groups.items()}
    biggest = max(sizes, key=sizes.get)
    remaining = {s: g for s, g in session_groups.items() if s != biggest}
    without, _ = _observed_effect(remaining)
    if without is None:
        return False
    return (observed_effect > 0) != (without > 0)


# === the decision (closed vocabulary) ===============================================================


def screen_candidate(
    *,
    feature_name: str,
    transform: str,
    params: dict,
    sidedness: str | None,
    horizon_key: str,
    econ_floor: dict,
    anchors: list[dict],
    family_id: str,
    n_variants_tried: int,
) -> dict:
    """The full descriptive screen over one candidate's already-extracted anchors: membership,
    effect, the block-permutation ``p_screen``, every mandatory disclosure (section 5.4), the
    economic-relevance column (section 5.5), and the closed-vocabulary decision. Always returns a
    fully-shaped ``screen_result`` regardless of decision (TC-12: every served screen carries every
    disclosure, not only a surviving one's)."""
    cell_of = [
        "candidate" if _feature_membership(a["feature_value"], transform, params) else "comparator"
        for a in anchors
    ]
    cand_anchors = [a for a, c in zip(anchors, cell_of) if c == "candidate"]
    comp_anchors = [a for a, c in zip(anchors, cell_of) if c == "comparator"]
    sessions = sorted({a["session_date"] for a in anchors})
    cand_sessions = {a["session_date"] for a in cand_anchors}
    comp_sessions = {a["session_date"] for a in comp_anchors}
    usable_sessions = sorted(cand_sessions & comp_sessions)

    n_candidate = len(cand_anchors)
    n_comparator = len(comp_anchors)
    concentration = _concentration(cand_anchors)
    tod_buckets = _tod_slices(anchors, cell_of)
    fallback_tercile = _fallback_tercile_slices(anchors, cell_of, feature_name)

    insufficient = (
        len(usable_sessions) < SCOUT_MIN_SESSION_CLUSTERS
        or n_candidate < SCOUT_MIN_OBSERVATIONS_PER_CELL
        or n_comparator < SCOUT_MIN_OBSERVATIONS_PER_CELL
    )

    effect_bps: float | None = None
    p_screen: float | None = None
    per_session_deltas: dict = {}
    best_of_n = _best_of_n_disclosure([], n_variants_tried)
    econ_interesting: bool | None = None
    session_groups: dict = {}

    if not insufficient:
        session_groups = _session_groups(anchors, cell_of, usable_sessions)
        effect_bps, per_session_deltas = _observed_effect(session_groups)
        horizon_kind, horizon_value = HORIZON_KEYS[horizon_key]
        block_length = _block_length_for_horizon(horizon_kind, horizon_value)
        null_effects = _null_effect_draws(
            session_groups,
            seed_scope=family_id,
            block_length=block_length,
            draws=SCOUT_BLOCK_PERMUTATIONS,
            shuffle="block",
        )
        p_screen = _two_sided_p(effect_bps, null_effects)
        valid_null = null_effects[~np.isnan(null_effects)]
        best_of_n = _best_of_n_disclosure(list(np.abs(valid_null)), n_variants_tried)
        econ_interesting = abs(effect_bps) >= econ_floor["floor_bps"] if effect_bps is not None else None

    screen_result = {
        "evidence_class": EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
        "effect_bps": effect_bps,
        "p_screen": p_screen,
        "p_screen_label": "descriptive screen -- not a confirmatory p-value",
        "n_candidate": n_candidate,
        "n_comparator": n_comparator,
        "n_sessions_total": len(sessions),
        "n_usable_sessions": len(usable_sessions),
        "per_session_deltas_bps": per_session_deltas,
        "concentration": concentration,
        "tod_buckets": tod_buckets,
        "fallback_tercile": fallback_tercile,
        "best_of_n_disclosure": best_of_n,
        "econ_interesting": econ_interesting,
        "econ_proxy_sentence": ECON_PROXY_SENTENCE,
    }

    if insufficient:
        decision = reason = "killed_insufficient_n"
        notes = (
            f"usable_sessions={len(usable_sessions)} (need >= {SCOUT_MIN_SESSION_CLUSTERS}), "
            f"n_candidate={n_candidate}, n_comparator={n_comparator} "
            f"(each need >= {SCOUT_MIN_OBSERVATIONS_PER_CELL})"
        )
    elif p_screen is None or p_screen >= SCOUT_SCREEN_ALPHA:
        decision = reason = "killed_null"
        notes = f"p_screen={p_screen!r} >= alpha={SCOUT_SCREEN_ALPHA} (descriptive screen)"
    elif sidedness is not None and not (effect_bps is not None and effect_bps > 0):
        decision = reason = "killed_direction"
        notes = f"effect_bps={effect_bps!r} opposes the registered sidedness={sidedness!r}"
    elif concentration["top1_session_share"] > SCOUT_MAX_TOP1_CONCENTRATION or (
        len({a["symbol"] for a in cand_anchors}) > 1
        and concentration["top1_symbol_share"] > SCOUT_MAX_TOP1_CONCENTRATION
    ):
        # The symbol-share ceiling only GATES when the candidate's own corpus genuinely spans more
        # than one symbol -- a single-symbol corpus_manifest (this iteration's own fixture grid,
        # and any candidate whose registered corpus is deliberately one symbol) trivially reads
        # top1_symbol_share == 1.0 always; that is a structural fact about the corpus, never a
        # concentration RISK to kill on. Session concentration still gates unconditionally: an
        # effect drawn almost entirely from one session is a genuine idiosyncrasy risk regardless
        # of symbol breadth. Both shares are still served verbatim in `concentration` either way
        # (spec section 5.4's own disclosure, never withheld).
        decision = reason = "killed_concentration"
        notes = f"concentration={concentration!r} exceeds the {SCOUT_MAX_TOP1_CONCENTRATION} ceiling"
    elif not econ_interesting:
        decision = reason = "killed_economic"
        notes = f"|effect_bps|={abs(effect_bps)!r} < floor_bps={econ_floor['floor_bps']!r}"
    elif _fragile_leave_one_session_out(session_groups, effect_bps):
        decision = reason = "killed_fragile"
        notes = "the effect's sign is not stable to leaving out its most-represented session"
    else:
        decision = reason = SCOUT_DECISION_SURVIVE
        notes = "passed the descriptive screen, direction, concentration, and economic checks"

    assert decision in CLOSED_DECISIONS  # a lint that can fail proves something (TC-1's own contract)
    return {"decision": decision, "reason": reason, "notes": notes, "screen_result": screen_result}


# === registration (the ONE production boundary that enforces TR-9 and the 24-variant cap) ==========


def build_candidate_spec_fields(
    *,
    feature_name: str,
    transform: str,
    params: dict,
    structure_context_kind: str,
    horizon_key: str,
    sidedness: str | None,
    fitting_rule: str | None,
    family_median_spread_bps: float,
    corpus_manifest: list[dict],
    grid_version: int,
    setup_id: str | None = None,
) -> dict:
    """Assembles the FROZEN candidate-spec fields (spec section 5.1) -- everything ``compute_spec_
    hash`` hashes, deliberately excluding any wall-clock-derived value (that function's own
    docstring: two separate registration acts of the identical candidate definition, e.g. the
    manager run and the CLI run of the same grid, TC-11, must compute the identical
    ``spec_hash``).

    ``setup_id`` (J-09, default ``None``) is additive: it lands in ``structure_context`` ONLY when
    given (Study 3's own ``structure_context.kind="playbook_signal"``, ``setup_id="capitulation"``
    -- goal.md's stated frozen field) -- every ``structure_context.kind="none"``/``"band_touch"``
    candidate (every pre-J-09 spec) omits the key entirely, so its ``spec_hash``/``candidate_id``
    stay byte-identical to before this parameter existed (TC-4's own distinct-``family_root_id``
    proof does not depend on this key's presence -- ``family_root_id`` is computed from
    ``feature_family_name``/``structure_context_kind``/``outcome_horizon_family`` alone, never from
    ``setup_id``)."""
    if structure_context_kind not in STRUCTURE_CONTEXT_KINDS:
        raise ValueError(f"unknown structure_context.kind {structure_context_kind!r}")
    if horizon_key not in HORIZON_KEYS:
        raise ValueError(f"unknown horizon_key {horizon_key!r}")
    if feature_name not in FEATURE_FAMILY_OF:
        raise ValueError(f"unknown feature.name {feature_name!r}")
    feature_family_name = FEATURE_FAMILY_OF[feature_name]
    outcome_horizon_family = HORIZON_KEYS[horizon_key][0]
    family_id = derive_family_id(feature_name, structure_context_kind, horizon_key)
    family_root_id = compute_family_root_id(
        feature_family_name, structure_context_kind, outcome_horizon_family
    )
    floor_bps = ECON_FLOOR_SPREAD_MULTIPLE * family_median_spread_bps
    econ_floor = {
        "multiple": ECON_FLOOR_SPREAD_MULTIPLE,
        "family_median_spread_bps": family_median_spread_bps,
        "floor_bps": floor_bps,
        "proxy_sentence": ECON_PROXY_SENTENCE,
    }
    structure_context: dict = {"kind": structure_context_kind}
    if setup_id is not None:
        structure_context["setup_id"] = setup_id
    spec_fields = {
        "family_id": family_id,
        "family_root_id": family_root_id,
        "feature": {"name": feature_name, "transform": transform, "params": params},
        "structure_context": structure_context,
        "outcome": {"horizon_key": horizon_key, "sidedness": sidedness},
        "fitting_rule": fitting_rule,
        "econ_floor": econ_floor,
        "corpus_manifest": corpus_manifest,
        "grid_version": grid_version,
    }
    spec_hash = compute_spec_hash(spec_fields)
    return {**spec_fields, "spec_hash": spec_hash, "candidate_id": f"cand-{spec_hash[:16]}"}


def register_and_screen_candidate(
    *,
    ledger: ScoutLedger,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    feature_name: str,
    transform: str,
    params: dict,
    structure_context_kind: str,
    horizon_key: str,
    corpus_manifest: list[dict],
    grid_version: int = 1,
    sidedness: str | None = None,
    fitting_rule: str | None = None,
    registered_at: str | None = None,
    econ_floor_computed_at: str | None = None,
    family_median_spread_bps: float | None = None,
    rows_cache: dict[str, list[dict]] | None = None,
    withheld_excluded: int = 0,
    resolver: "BandMapResolver | None" = None,
    playbook_store: "PlaybookStore | None" = None,
    setup_id: str | None = None,
) -> dict:
    """The ONE production entry point: builds the frozen spec, enforces TR-9 (ordering) and the
    24-variant grid bound BEFORE any outcome is read or any ledger row is written, extracts
    anchors, runs the screen, and appends the combined row. Both ``ScoutComputeManager``'s worker
    and the CLI's ``main()`` call this SAME function for every grid entry -- no second
    implementation of the screen (TC-11).

    ``resolver``/``playbook_store``/``setup_id`` (J-09, all default ``None``) are threaded straight
    through to ``extract_anchors``/``build_candidate_spec_fields`` -- REQUIRED only when
    ``structure_context_kind`` is ``"band_touch"``/``"playbook_signal"`` respectively (that
    function's own ``ValueError`` guards the omission); every pre-J-09 caller
    (``structure_context_kind="none"``) is unaffected.

    ``registered_at``/``econ_floor_computed_at``/``family_median_spread_bps`` default to ``None``,
    meaning "compute honestly right now" -- the econ floor's median spread is read from the
    corpus and BOTH timestamps are stamped at this same call, so a normal registration can never
    violate TR-9 by construction. A caller passing explicit, deliberately-misordered timestamps
    (``tests/test_scout.py``'s TC-7) exercises the refusal directly.

    ``rows_cache`` (default ``None``, i.e. off) is the ``_cached_dataset_rows`` opt-in, threaded
    through to both ``_family_median_spread_bps`` and ``extract_anchors`` -- a grid run registering
    several candidates against the SAME ``corpus_manifest`` (``run_scout_grid_and_record``, every
    call sharing one cache) reads each dataset's snapshot rows from disk exactly once for the WHOLE
    run, never once per candidate."""
    # Refused up front, before any corpus read or ledger write: a horizon this module cannot
    # block-size from spec section 5.3's own rule is never screened at all (iter-4 audit fix --
    # see `_block_length_for_horizon`), rather than refused only later and only when the candidate
    # happened to clear the sufficiency floors.
    # (an UNKNOWN horizon_key stays `build_candidate_spec_fields`'s own ValueError, unchanged)
    _known_horizon = HORIZON_KEYS.get(horizon_key)
    if _known_horizon is not None:
        _block_length_for_horizon(*_known_horizon)

    if family_median_spread_bps is None:
        family_median_spread_bps = _family_median_spread_bps(
            dataset_store, snapshots_dir, config, corpus_manifest, rows_cache
        )
    if econ_floor_computed_at is None:
        econ_floor_computed_at = _iso_utc_now()
    if registered_at is None:
        registered_at = _iso_utc_now()

    if parse_utc_epoch(econ_floor_computed_at) > parse_utc_epoch(registered_at):
        raise ScoutRegistrationOrderingError(
            f"econ_floor inputs were computed at {econ_floor_computed_at!r}, AFTER this "
            f"candidate's own registered_at {registered_at!r} -- refused (TR-9); the econ floor "
            "must already be frozen INTO the spec at registration, never back-filled once the "
            "spec claims to be frozen"
        )

    spec_fields = build_candidate_spec_fields(
        feature_name=feature_name,
        transform=transform,
        params=params,
        structure_context_kind=structure_context_kind,
        horizon_key=horizon_key,
        sidedness=sidedness,
        fitting_rule=fitting_rule,
        family_median_spread_bps=family_median_spread_bps,
        corpus_manifest=corpus_manifest,
        grid_version=grid_version,
        setup_id=setup_id,
    )
    family_id = spec_fields["family_id"]
    family_rows = ledger.rows_for_family(family_id)
    n_prior = distinct_variant_count(family_rows)
    if n_prior >= SCOUT_MAX_VARIANTS_PER_FAMILY:
        raise ScoutGridExhaustedError(
            f"family {family_id!r} already carries {n_prior} variants across every grid_version "
            f"registered for it -- SCOUT_MAX_VARIANTS_PER_FAMILY={SCOUT_MAX_VARIANTS_PER_FAMILY} "
            "is a hard bound (TC-9); refused, no ledger row written"
        )

    anchors = extract_anchors(
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
    result = screen_candidate(
        feature_name=feature_name,
        transform=transform,
        params=params,
        sidedness=sidedness,
        horizon_key=horizon_key,
        econ_floor=spec_fields["econ_floor"],
        anchors=anchors,
        family_id=family_id,
        # The family's union-N INCLUDING this candidate -- `n_prior + 1` would overstate it by one
        # whenever this candidate's own `candidate_id` is already on record (the identical grid
        # re-run through the compute route), which is exactly the inflation
        # `distinct_variant_count` exists to prevent (iter-4 audit fix).
        n_variants_tried=distinct_variant_count([*family_rows, spec_fields]),
    )
    row_fields = {
        **spec_fields,
        "registered_at": registered_at,
        "econ_floor_computed_at": econ_floor_computed_at,
        "params_hash": scout_parameters_hash(),
        "decision": result["decision"],
        "reason": result["reason"],
        "notes": result["notes"],
        "screen_result": result["screen_result"],
        "superseded_by": None,
        # Spec section 7.5 point 6 (r4): how many registered datasets this candidate's corpus
        # manifest left out because their vault shards are withheld -- a count, never an id, and
        # deliberately OUTSIDE ``spec_fields`` (which ``compute_spec_hash`` hashes), so disclosing
        # it re-keys no ``spec_hash`` and no ``candidate_id``, and no already-recorded row moves.
        "withheld_excluded": withheld_excluded,
    }
    return ledger.append_row(row_fields)


# === the bounded reference fixture grid + the shared manager/CLI orchestration (TC-11 parity) =======

# 3 features (one per Wave-1 family: F-FLOW, F-RESPONSE, F-LIQUIDITY) x 2 threshold directions
# each = 6 candidates across 3 distinct family_ids, well under SCOUT_MAX_VARIANTS_PER_FAMILY (24)
# -- this iteration's own "bounded fixture grid" (goal.md IN SCOPE), reused unmodified by the
# manager, the CLI, and TC-11's parity check. `structure_context.kind="none"` throughout (module
# docstring: no pilot-study conditioning yet). Every entry uses a TRADE-COUNT horizon (never
# shares/clock_seconds) deliberately: a trade-count horizon resolves in O(1) per anchor
# (``outcome_row_at_single_horizon``'s own docstring -- direct index arithmetic, no forward scan),
# while a shares/clock horizon's forward scan, run once per anchor across a real, actively-traded
# dataset (hundreds of thousands of trades), is a genuine, disclosed cost this DEFAULT,
# operator-triggered grid deliberately avoids. (Since the iter-4 audit, a shares/clock horizon is
# not merely expensive but REFUSED outright -- `_block_length_for_horizon` cannot size its
# permutation block from spec section 5.3's own rule yet; see that function's docstring.)
DEFAULT_GRID_FEATURES: tuple[tuple[str, str], ...] = (
    ("cumulative_delta", "trades_20"),
    ("failed_aggression_score", "trades_20"),
    ("quote_imbalance", "trades_20"),
)
DEFAULT_GRID_THRESHOLDS: tuple[tuple[str, float], ...] = (
    ("ge", 0.0),
    ("le", 0.0),
)


def default_fixture_grid(dataset_store: DatasetStore, *, grid_version: int = 1) -> list[dict]:
    """Raw candidate-registration requests (kwargs for ``register_and_screen_candidate``, minus
    ``ledger``/``dataset_store``/``snapshots_dir``/``config``) over WHATEVER datasets
    ``dataset_store`` currently holds -- reused unmodified by the manager, the CLI, and the test
    suite's manager/CLI-parity check (TC-11)."""
    records, _errors = dataset_store.list()
    # Spec section 7.4/7.5 (r3) + the era's *(critical)* anti-goal, iter-9 audit finding B1: a
    # shard whose vault lifecycle has not reached ``exposed`` is excluded from the corpus
    # manifest. Two distinct reasons, both fatal without this line: (1) the manifest is written
    # VERBATIM into the append-only, hash-chained scout ledger and served by
    # ``GET /research/desk/micro/scout``, so a sealed shard's ``dataset_id`` and RAW ``checksum``
    # -- precisely the two join keys section 7.5 withholds until exposure -- would be published
    # irreversibly; and (2) screening a sealed shard would READ its snapshot rows and fold its
    # outcomes into an exploratory statistic, destroying the held-out property the whole vault
    # exists to create. Empty (hence byte-identical) until the first shard is ever sealed.
    # Spec section 7.5 point 6 (r4): the exclusion is DISCLOSED as a count on every row this grid
    # writes (``register_and_screen_candidate``'s ``withheld_excluded``, carried OUTSIDE the frozen
    # spec fields so no ``spec_hash``/``candidate_id`` re-keys) -- silent shrinking of a screened
    # corpus is exactly what the era's denominator rail forbids.
    kept, withheld_excluded = exclude_withheld(records, dataset_store)
    corpus_manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in kept]
    requests: list[dict] = []
    for feature_name, horizon_key in DEFAULT_GRID_FEATURES:
        for op, value in DEFAULT_GRID_THRESHOLDS:
            requests.append(
                {
                    "feature_name": feature_name,
                    "transform": "threshold",
                    "params": {"op": op, "value": value},
                    "structure_context_kind": "none",
                    "horizon_key": horizon_key,
                    "sidedness": None,
                    "fitting_rule": None,
                    "corpus_manifest": corpus_manifest,
                    "grid_version": grid_version,
                    "withheld_excluded": withheld_excluded,
                }
            )
    return requests


# === J-09: the three predeclared pilot-study candidate requests, frozen-in-source, in goal.md's
# own stated priority order (Study 1, 2, 3) -- module docstring. As of iteration 22, all three are
# taken through ``register_and_screen_candidate`` (below), each via its own additive grid selector
# -- Study 1's real screen still carries only its single ``failed_aggression_score`` feature (T-1:
# the ``refill_consistent`` co-occurrence condition is genuinely unbuilt, disclosed in its own
# frozen request comment below, not invented here).

PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION = "range_wall_failed_aggression"
PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS = "delta_divergence_level_tests"
PILOT_STUDY_CAPITULATION_EXHAUSTION = "capitulation_exhaustion"

# ``ScoutComputeManager.trigger``/``main``'s own additive grid-selector values (below) -- one per
# predeclared pilot study, each wired the SAME way (one-element grid, required
# resolver/playbook_store, required exposure_registry) so every study's walk-forward floor-check
# decision is recorded on the SAME operator-reachable path (CLI or ``POST /scout/compute``), never
# only a unit test (the iter-21 audit's own B1 lesson, extended to all three this iteration).
GRID_SELECTOR_RANGE_WALL_PILOT = "range_wall_failed_aggression_pilot"
GRID_SELECTOR_DELTA_DIVERGENCE_PILOT = "delta_divergence_pilot"
GRID_SELECTOR_CAPITULATION_PILOT = "capitulation_exhaustion_pilot"


def pilot_study_candidate_grid(
    dataset_store: DatasetStore, *, grid_version: int = 1
) -> dict[str, dict]:
    """The three predeclared pilot-study candidate-registration requests, keyed by
    ``micro_readiness.PILOT_STUDY_IDS``'s own study-id vocabulary (never a second, independently-
    spelled id list -- ``PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION``/``..._DELTA_DIVERGENCE_LEVEL_
    TESTS``/``..._CAPITULATION_EXHAUSTION`` above are the SAME three strings that module's own
    ``PILOT_STUDY_IDS`` tuple already carries -- a value-level coincidence this function does not
    import to avoid, since ``micro_readiness.py`` predates and does not depend on ``scout.py``).
    Each value is a raw kwargs dict for ``register_and_screen_candidate`` -- the SAME shape
    ``default_fixture_grid``'s own entries carry -- with ``feature``/``structure_context``/
    ``outcome``/``econ_floor`` (via ``build_candidate_spec_fields``, called downstream) fully
    constructed regardless of whether this iteration ever screens it (TC-4).

    Every candidate shares the withheld-excluded, currently-registered corpus manifest
    (``exclude_withheld`` -- the SAME r4 discipline ``default_fixture_grid`` already applies) so a
    sealed shard is never silently folded into a pilot study's own evidence pool."""
    records, _errors = dataset_store.list()
    kept, withheld_excluded = exclude_withheld(records, dataset_store)
    corpus_manifest = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in kept]

    range_wall_failed_aggression = {
        "feature_name": "failed_aggression_score",
        "transform": "threshold",
        "params": {"op": "ge", "value": 0.5},
        "structure_context_kind": "band_touch",
        "horizon_key": "trades_20",
        "sidedness": None,
        "fitting_rule": None,
        "corpus_manifest": corpus_manifest,
        "grid_version": grid_version,
        "withheld_excluded": withheld_excluded,
        # goal.md's own framing: this study's eventual real screen additionally examines
        # opposite-side `refill_consistent` (F-LIQUIDITY) co-occurrence at the SAME touch -- a
        # joint two-feature condition `register_and_screen_candidate`'s single-feature threshold
        # membership does not express yet (T-1: genuinely unbuilt, never invented here). This
        # frozen request carries `failed_aggression_score` alone, reviewable today; the
        # co-occurrence disclosure is added when that joint-condition machinery is built, a future
        # iteration's own scope.
    }
    delta_divergence_level_tests = {
        "feature_name": _DIVERGENCE_FEATURE_NAME,
        "transform": "threshold",
        "params": {"op": "ge", "value": 1.0},  # candidate iff bearish_divergence is True (1.0)
        "structure_context_kind": "band_touch",
        "horizon_key": "trades_20",
        "sidedness": None,
        "fitting_rule": None,
        "corpus_manifest": corpus_manifest,
        "grid_version": grid_version,
        "withheld_excluded": withheld_excluded,
    }
    capitulation_exhaustion = {
        "feature_name": "failed_aggression_score",
        "transform": "threshold",
        "params": {"op": "ge", "value": 0.7},
        "structure_context_kind": "playbook_signal",
        "horizon_key": "trades_20",
        "sidedness": None,
        "fitting_rule": None,
        "corpus_manifest": corpus_manifest,
        "grid_version": grid_version,
        "withheld_excluded": withheld_excluded,
        "setup_id": "capitulation",
    }
    return {
        PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION: range_wall_failed_aggression,
        PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS: delta_divergence_level_tests,
        PILOT_STUDY_CAPITULATION_EXHAUSTION: capitulation_exhaustion,
    }


# Grid-selector -> (pilot_study_candidate_grid's own study id, structure_context.kind) -- the ONE
# table ``ScoutComputeManager.trigger`` and the CLI's ``main()`` both read (never a second,
# independently-maintained selector->study mapping); the kind decides which of resolver/
# playbook_store the caller must supply (band_touch needs a resolver, playbook_signal needs a
# playbook_store -- the two structure_context.kind values the three pilot studies actually span).
_PILOT_GRID_SELECTORS: dict[str, tuple[str, str]] = {
    GRID_SELECTOR_RANGE_WALL_PILOT: (PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION, "band_touch"),
    GRID_SELECTOR_DELTA_DIVERGENCE_PILOT: (PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS, "band_touch"),
    GRID_SELECTOR_CAPITULATION_PILOT: (PILOT_STUDY_CAPITULATION_EXHAUSTION, "playbook_signal"),
}


def run_scout_grid_and_record(
    grid: list[dict],
    ledger: ScoutLedger,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    *,
    progress: Callable[[str], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    exposure_registry: "ExposureRegistry | None" = None,
) -> list[dict]:
    """Registers and screens every request in ``grid``, in order, through the ONE production entry
    point (``register_and_screen_candidate``) -- both the manager and the CLI call this SAME
    function (TC-11). A requested abort is honoured at CANDIDATE boundaries only, mirroring
    ``micro_snapshots.run_snapshot_build_and_record``'s own "nothing is ever recorded half-built"
    discipline.

    ONE ``rows_cache`` dict is shared across every request in this run (``_cached_dataset_rows``'s
    own opt-in, ``register_and_screen_candidate``'s own docstring) -- every grid entry in this
    era's own ``default_fixture_grid`` shares an identical ``corpus_manifest``, so this turns what
    would be 2 x len(grid) full re-parses of the snapshot corpus into exactly one per dataset for
    the WHOLE run (measured on the real 18-dataset/~3.8M-row corpus to be the difference between a
    sub-minute run and one that never finishes).

    ``exposure_registry`` (iter-21 audit fix B1, default ``None``): ``None`` is the unchanged
    screen-only path every pre-J-09 caller (and the default reference grid) takes -- exactly ONE
    ledger row per request. Given one, each request runs through
    ``register_screen_and_walkforward_check`` instead, so the walk-forward floor-check decision
    goal.md IN SCOPE item 6 requires is actually RECORDED by the operator-reachable run (the CLI
    ``--grid delta_divergence_pilot`` / ``POST /scout/compute {"grid": ...}`` path) rather than only
    by the hermetic unit test -- the browser lane's own UT-04 finding. The returned list still
    carries ONE row per request (the SCREEN row), so every existing caller's shape is unchanged;
    the floor-check row is read from the ledger, where it belongs."""
    rows_cache: dict[str, list[dict]] = {}
    results: list[dict] = []
    for request in grid:
        if should_abort is not None and should_abort():
            break
        if exposure_registry is None:
            row = register_and_screen_candidate(
                ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir,
                config=config, rows_cache=rows_cache,
                **request,
            )
        else:
            row = register_screen_and_walkforward_check(
                ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir,
                config=config, exposure_registry=exposure_registry, rows_cache=rows_cache,
                **request,
            )["screen_row"]
        results.append(row)
        if progress is not None:
            progress(row["candidate_id"])
    return results


# === J-09: screen ONE candidate through register_and_screen_candidate, THEN run the walk-forward
# floor check for it (goal.md IN SCOPE items 5-6) -- never calls evaluate_mode_b_fold below floor.
# ======================================================================================================


def register_screen_and_walkforward_check(
    *,
    ledger: ScoutLedger,
    dataset_store: DatasetStore,
    snapshots_dir: str,
    config: Config,
    exposure_registry: "ExposureRegistry",
    feature_name: str,
    transform: str,
    params: dict,
    structure_context_kind: str,
    horizon_key: str,
    corpus_manifest: list[dict],
    grid_version: int = 1,
    sidedness: str | None = None,
    fitting_rule: str | None = None,
    resolver: "BandMapResolver | None" = None,
    playbook_store: "PlaybookStore | None" = None,
    setup_id: str | None = None,
    rows_cache: dict[str, list[dict]] | None = None,
    withheld_excluded: int = 0,
) -> dict:
    """Registers+screens ONE candidate (``register_and_screen_candidate``, unmodified -- no second
    screening implementation), THEN runs its walk-forward floor check
    (``walkforward.scout_candidate_walkforward_floor_check``) against its OWN anchor corpus and
    appends the resulting decision as a SECOND ledger row under the SAME ``candidate_id``
    (``scout_ledger.py``'s own "append-only, a later stage's outcome is a NEW row, never an edit"
    precedent -- the module docstring's "superseded" example, applied here to a walk-forward
    stage rather than a supersession). Source-level guard-tested to NEVER call the fold-evaluation
    function walk-forward folds are actually SCORED through -- this function only decides whether
    that call would be legitimate; today's real and fixture corpora both carry zero
    ``historical_oos`` sessions, so the floor check always refuses (goal.md IN SCOPE item 6,
    TC-6).

    Anchors are re-extracted (a second ``extract_anchors`` call, mirroring the screen's own) to
    build the ``{session_date, symbol, value}`` observation list the floor check needs -- cheap on
    the small, committed fixture this candidate runs against (never the real production corpus this
    iteration, goal.md OUT OF SCOPE), so this is NOT the ``rows_cache``-sharing perf path
    ``run_scout_grid_and_record``'s own docstring protects.

    Returns ``{"screen_row": ..., "walkforward_row": ...}`` -- both rows verbatim as ledgered."""
    screen_row = register_and_screen_candidate(
        ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=config,
        feature_name=feature_name, transform=transform, params=params,
        structure_context_kind=structure_context_kind, horizon_key=horizon_key,
        corpus_manifest=corpus_manifest, grid_version=grid_version, sidedness=sidedness,
        fitting_rule=fitting_rule, resolver=resolver, playbook_store=playbook_store,
        setup_id=setup_id, rows_cache=rows_cache, withheld_excluded=withheld_excluded,
    )
    anchors = extract_anchors(
        feature_name=feature_name, structure_context_kind=structure_context_kind,
        horizon_key=horizon_key, sidedness=sidedness, corpus_manifest=corpus_manifest,
        dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=config,
        rows_cache=rows_cache, resolver=resolver, playbook_store=playbook_store, setup_id=setup_id,
    )
    observations = [
        {"session_date": a["session_date"], "symbol": a["symbol"], "value": a["outcome_value"]}
        for a in anchors
    ]
    floor_result = wf.scout_candidate_walkforward_floor_check(
        exposure_registry,
        corpus_id=wf.TICK_LEGACY_CORPUS_ID,
        observations=observations,
        registered_at=screen_row["registered_at"],
    )
    if floor_result["status"] == "sufficient":
        decision = SCOUT_DECISION_SURVIVE
        notes = (
            f"walk-forward floor cleared: {floor_result['oos_session_count']} historical_oos "
            "session(s)"
        )
    else:
        decision = "killed_insufficient_n"
        notes = (
            f"walk-forward floor refused: {floor_result['oos_session_count']} historical_oos "
            f"session(s); missing={floor_result['missing']!r}"
        )
    walkforward_row = ledger.append_row(
        {
            "family_id": screen_row["family_id"],
            "family_root_id": screen_row["family_root_id"],
            "candidate_id": screen_row["candidate_id"],
            "spec_hash": screen_row["spec_hash"],
            "stage": "walkforward_floor_check",
            "registered_at": screen_row["registered_at"],
            "decision": decision,
            "reason": decision,
            "notes": notes,
            "screen_result": None,
            "walkforward_floor_check": floor_result,
            "superseded_by": None,
            "withheld_excluded": 0,
        }
    )
    return {"screen_row": screen_row, "walkforward_row": walkforward_row}


def list_scout_families(ledger: ScoutLedger) -> list[dict]:
    """``GET /research/desk/micro/scout``'s whole body (minus the envelope key): every family with
    at least one registered trial, grouped, each carrying ``variants_tried`` (the union-N across
    every ``grid_version``, TC-2) beside its full ``trials`` list (every row verbatim -- decision,
    reason, notes, screen_result -- TC-1, TC-12)."""
    rows = ledger.all_rows()
    order: list[str] = []
    families: dict[str, list[dict]] = {}
    for row in rows:
        family_id = row.get("family_id")
        if family_id not in families:
            families[family_id] = []
            order.append(family_id)
        families[family_id].append(row)
    out = []
    for family_id in order:
        family_rows = families[family_id]
        out.append(
            {
                "family_id": family_id,
                "family_root_id": family_rows[-1].get("family_root_id"),
                # The ledger's OWN union-N function, never the last row's stamped copy: identical
                # by construction on a clean ledger, but the one place the number is computed
                # (iter-4 audit fix -- reading a stamp would let a tampered row dictate the served
                # denominator).
                "variants_tried": distinct_variant_count(family_rows),
                "trials": family_rows,
            }
        )
    return out


# === the single-flight compute manager (the MicroSnapshotComputeManager pattern, mirrored) ==========

_IDLE_SNAPSHOT: dict = {
    "run_id": None,
    "state": "idle",
    "progress": {"candidates_total": 0, "candidates_done": 0, "current_candidate_id": None},
    "started_utc": None,
    "finished_utc": None,
    "error": None,
}


class ScoutComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) scout-screening job for this process --
    single-flight, pollable progress, cooperative cancel, terminal-state-only ledger writes: a
    mid-run exception resolves the job to ``"failed"``, never a silently-short ledger write (the
    iteration-2 streamed-artifact-completeness lesson, explicitly named for this manager in the
    phase spec). Mirrors ``micro_snapshots.MicroSnapshotComputeManager`` structure-for-structure;
    reuses that module's ``append_run_log``/``read_run_log`` (generic over any root dir -- no
    second implementation of a terminal-run log)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict = dict(_IDLE_SNAPSHOT)
        self._run_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._snapshot)

    def trigger(
        self,
        dataset_store: DatasetStore,
        config: Config,
        snapshots_dir: str,
        ledger_dir: str,
        grid_version: int = 1,
        grid_selector: str | None = None,
        resolver: "BandMapResolver | None" = None,
        playbook_store: "PlaybookStore | None" = None,
        exposure_registry: "ExposureRegistry | None" = None,
    ) -> dict:
        """Start a NEW screening run over ``default_fixture_grid`` (ensuring snapshots exist first,
        reuse-or-build), or -- if one is already ``"running"`` -- refuse (single-flight,
        process-wide).

        ``grid_selector`` (J-09, default ``None``): ``None`` is BYTE-IDENTICAL to every pre-J-09
        call (the unchanged default grid). Each of ``GRID_SELECTOR_RANGE_WALL_PILOT`` /
        ``GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` / ``GRID_SELECTOR_CAPITULATION_PILOT`` (iter-22:
        all three predeclared pilot studies, `_PILOT_GRID_SELECTORS`) selects a ONE-ELEMENT grid --
        the matching frozen request ``pilot_study_candidate_grid`` carries -- so every pilot
        candidate is CLI/manager-runnable beside the default grid, never a second endpoint. The two
        ``band_touch``-kind selectors (range-wall, delta-divergence) require ``resolver`` (a plain
        ``ValueError`` when omitted); the ``playbook_signal``-kind selector (capitulation) requires
        ``playbook_store`` instead -- selector-aware, since the three studies span two different
        ``structure_context.kind`` values.

        ``exposure_registry`` (iter-21 audit fix B1, extended iter-22 to all three selectors) is
        REQUIRED beside ``resolver``/``playbook_store`` for every pilot selector and IGNORED for
        the default grid: it is what lets the pilot run record its walk-forward floor-check
        decision as a second ledger row under the SAME ``candidate_id`` (goal.md IN SCOPE item 6),
        instead of leaving that stage reachable only from a unit test."""
        if grid_selector is not None and grid_selector not in _PILOT_GRID_SELECTORS:
            raise ValueError(f"ScoutComputeManager.trigger: unknown grid_selector {grid_selector!r}")
        if grid_selector is not None:
            _study_id, _structure_kind = _PILOT_GRID_SELECTORS[grid_selector]
            if _structure_kind == "band_touch" and resolver is None:
                raise ValueError(
                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires a "
                    "resolver"
                )
            if _structure_kind == "playbook_signal" and playbook_store is None:
                raise ValueError(
                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires a "
                    "playbook_store"
                )
            # iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): the pilot run
            # RECORDS its walk-forward floor-check decision (goal.md IN SCOPE item 6) -- so the
            # registry that decides `historical_oos` eligibility is as REQUIRED here as
            # resolver/playbook_store, never an optional extra a caller could forget and silently
            # get a screen-only run back.
            if exposure_registry is None:
                raise ValueError(
                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires an "
                    "exposure_registry"
                )
        with self._lock:
            if self._snapshot["state"] == "running":
                return {"state": "refused", "reason": "already_running"}

            if grid_selector is not None:
                study_id, structure_kind = _PILOT_GRID_SELECTORS[grid_selector]
                request = dict(
                    pilot_study_candidate_grid(dataset_store, grid_version=grid_version)[study_id]
                )
                if structure_kind == "band_touch":
                    request["resolver"] = resolver
                else:
                    request["playbook_store"] = playbook_store
                grid = [request]
            else:
                grid = default_fixture_grid(dataset_store, grid_version=grid_version)
            # The DEFAULT grid stays screen-only, byte-identical to every pre-J-09 run (one ledger
            # row per candidate); only a pilot selector carries the floor-check stage.
            floor_check_registry = exposure_registry if grid_selector is not None else None
            run_id = uuid.uuid4().hex
            self._run_id = run_id
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            self._snapshot = {
                "run_id": run_id,
                "state": "running",
                "progress": {
                    "candidates_total": len(grid),
                    "candidates_done": 0,
                    "current_candidate_id": None,
                },
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
            }
            published = dict(self._snapshot)

        def _publish(candidate_id: str) -> None:
            with self._lock:
                if self._run_id != run_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshot
                self._snapshot = {
                    **current,
                    "progress": {
                        **current["progress"],
                        "candidates_done": current["progress"]["candidates_done"] + 1,
                        "current_candidate_id": candidate_id,
                    },
                }

        def _work() -> None:
            try:
                run_snapshot_build_and_record(dataset_store, config, snapshots_dir, None)
                ledger = ScoutLedger(ledger_dir)
                run_scout_grid_and_record(
                    grid, ledger, dataset_store, snapshots_dir, config,
                    progress=_publish, should_abort=cancel_event.is_set,
                    exposure_registry=floor_check_registry,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_terminal(run_id, ledger_dir, "failed", error=str(exc))
                return
            if cancel_event.is_set():
                self._resolve_terminal(run_id, ledger_dir, "cancelled")
            else:
                self._resolve_terminal(run_id, ledger_dir, "done")

        thread = threading.Thread(target=_work, name=f"scout-compute:{run_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return published

    def _resolve_terminal(
        self, run_id: str, ledger_dir: str, state: str, *, error: str | None = None
    ) -> None:
        with self._lock:
            if self._run_id != run_id:
                return  # superseded -- never resolve a job that is no longer the current one
            current = self._snapshot
            finished_utc = _iso_utc_now()
            self._snapshot = {**current, "state": state, "finished_utc": finished_utc, "error": error}
            entry = {
                "run_id": run_id,
                "state": state,
                "started_utc": current["started_utc"],
                "finished_utc": finished_utc,
                "candidates_done": current["progress"]["candidates_done"],
                "candidates_total": current["progress"]["candidates_total"],
                "error": error,
            }
        append_run_log(ledger_dir, entry)

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


# === the CLI ==========================================================================================


def _cli_progress_printer() -> Callable[[str], None]:
    done = {"n": 0}

    def _print(candidate_id: str) -> None:
        done["n"] += 1
        print(f"  [{done['n']}] scout trial recorded: {candidate_id}", flush=True)

    return _print


def main() -> int:
    """``python -m app.research.scout [--grid-version N] [--grid {default,range_wall_failed_
    aggression_pilot,delta_divergence_pilot,capitulation_exhaustion_pilot}]`` -- registers and
    screens this era's bounded reference candidate grid against the operator's REAL
    dataset/snapshot/ledger directories, synchronously, in-process (the ``micro_snapshots``
    CLI-warmer precedent), persisting through the SAME ledger ``GET /research/desk/micro/scout``
    serves. ``--grid`` (J-09, default ``default``) mirrors ``ScoutComputeManager.trigger``'s own
    ``grid_selector`` -- omitted, byte-identical to every pre-J-09 invocation; any of the three
    pilot-study values (iter-22: all three are wired, `_PILOT_GRID_SELECTORS`) runs that ONE
    predeclared candidate through the SAME operator-reachable path the route uses."""
    parser = argparse.ArgumentParser(
        description="Scout screening CLI warmer -- registers and screens the era's bounded "
        "reference candidate grid, ensuring prerequisite snapshots exist first."
    )
    parser.add_argument(
        "--grid-version", type=int, default=1, help="the grid_version to stamp on this run's rows."
    )
    parser.add_argument(
        "--grid", choices=("default", *_PILOT_GRID_SELECTORS), default="default",
        help="'default' (unchanged) or one of the three J-09 pilot-study grid selectors -- "
        "'range_wall_failed_aggression_pilot', 'delta_divergence_pilot', "
        "'capitulation_exhaustion_pilot' -- each screening its ONE predeclared candidate.",
    )
    args = parser.parse_args()

    config = CONFIG
    dataset_store = DatasetStore(config.dataset_dir_resolved())
    snapshots_dir = resolve_micro_snapshots_dir(config.dataset_dir_resolved())
    ledger_dir = resolve_scout_ledger_dir(config.dataset_dir_resolved())

    run_snapshot_build_and_record(dataset_store, config, snapshots_dir, None)
    ledger = ScoutLedger(ledger_dir)
    exposure_registry = None
    if args.grid in _PILOT_GRID_SELECTORS:
        from .bars import BarStore
        from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
        from .desk_playbook_context import BandMapResolver
        from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir

        study_id, structure_kind = _PILOT_GRID_SELECTORS[args.grid]
        # iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): the SAME durable
        # registry `POST /walkforward/compute` already reads (`resolve_micro_exposure_registry_dir`
        # -- never a second, differently-rooted one), so the pilot run's floor check reads the
        # operator's real exposure state.
        exposure_registry = ExposureRegistry(
            resolve_micro_exposure_registry_dir(config.dataset_dir_resolved())
        )
        request = dict(
            pilot_study_candidate_grid(dataset_store, grid_version=args.grid_version)[study_id]
        )
        if structure_kind == "band_touch":
            request["resolver"] = BandMapResolver(BarStore(config.bar_dir_resolved()), config)
        else:
            request["playbook_store"] = PlaybookStore(
                resolve_desk_playbook_dir(config.desk_universe_dir_resolved())
            )
        grid = [request]
    else:
        grid = default_fixture_grid(dataset_store, grid_version=args.grid_version)
    results = run_scout_grid_and_record(
        grid, ledger, dataset_store, snapshots_dir, config, progress=_cli_progress_printer(),
        exposure_registry=exposure_registry,
    )
    print(f"scout screen complete: {len(results)} candidate(s) processed; ledger={ledger_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
