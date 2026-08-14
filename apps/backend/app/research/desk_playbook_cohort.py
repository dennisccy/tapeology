"""``desk_playbook_cohort`` — the record's own recorded pooled summary, narrowed to a DECLARED
cohort of the locations its signals fired at.

The /desk Playbook section carries two display filters (a wall filter and an inside filter). They
narrow row lists trivially, but the per-setup summary table renders POOLED MEANS, and a browser may
not re-pool served aggregates: the numbers a reader trusts most would become browser-derived, and
the page's own price-arithmetic guard bans it. So the pooling for a narrowed cohort happens HERE,
at serve time, through the measurement rail's own helpers.

**The property this module is built around.** For every recorded record, re-pooling its own in-cap
prefix through ``desk_forward._collect_measures``/``_avg_cell`` reproduces its recorded ``summary``
BYTE-IDENTICALLY -- verified across the whole corpus at authoring time (198 of 198 records that
have a summary, key order included; the other 12 are zero-signal sessions). That is not a
coincidence to be relied on nervously: the unfiltered cohort below never consults the band context
at all, so it is the record's own in-cap prefix pooled by the record's own rule, and it stays equal
to ``record["summary"]`` even when the context is missing, un-warmed, or refused. An operator who
switches a filter back to "all" therefore cannot be shown numbers that differ from the record's.

**Why a module of its own.** The band-context lens (``desk_playbook_context``) is a per-record
LOCATION lens whose output is a durably cached blob keyed on its own algorithm version; putting
pooled means inside it would force a re-warm of every cached row, change what its completeness guard
reasons about, and push a quarter-megabyte into the evidence fold's context reads, which need none
of it. The evidence fold (``desk_playbook_evidence``) owns CROSS-SESSION quartile distributions at
one signature -- a different subject and a different cell vocabulary. This module composes the two
existing owners and adds no third source of truth: every threshold it uses is one the lens already
registered, and every number it emits comes from the rail's own helpers.

**No new threshold exists here.** The cohorts are compositions of buckets the lens already serves
(spec §6). This module registers a VOCABULARY (which compositions the product offers), not a tunable.

Read-side only: ``fold_cohorts`` takes no store, no resolver, no cache and no config, so it is
structurally incapable of computing a map, reading a bar, or writing a record.
"""

from __future__ import annotations

from .desk_forward import _avg_cell, _collect_measures
from .desk_playbook import PLAYBOOK_SIGNAL_MEASURES
from .desk_playbook_context import (
    AT_WALL,
    LOCATED,
    NOT_COMPUTED,
    NO_BAND_CONTEXT,
    PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
    ROOM_1R_2R,
    ROOM_GE_2R,
    ROOM_UNMEASURED,
)

__all__ = [
    "COHORT_REGISTER",
    "PLAYBOOK_COHORT_ALGORITHM_VERSION",
    "PLAYBOOK_COHORT_BACKING_VALUES",
    "PLAYBOOK_COHORT_INSIDE_VALUES",
    "PLAYBOOK_COHORT_KEYS",
    "UNFILTERED_COHORT",
    "cohort_key",
    "cohort_parameters",
    "fold_cohorts",
    "signal_cohorts",
]

# Versioned so a change to the COHORT vocabulary or the pooling rule is nameable. It is a shape
# pointer, not a tunable: no threshold lives here (see the module docstring).
PLAYBOOK_COHORT_ALGORITHM_VERSION = "playbook-cohort-v1"

# --- the two declared axes (docs/playbook-detector-spec.md §7) -----------------------------------
BACKING_ANY = "all"
BACKING_AT_WALL = AT_WALL
BACKING_AT_WALL_ROOM_GE_1R = "at_wall_room_ge_1r"
PLAYBOOK_COHORT_BACKING_VALUES: tuple[str, ...] = (
    BACKING_ANY,
    BACKING_AT_WALL,
    BACKING_AT_WALL_ROOM_GE_1R,
)

INSIDE_ANY = "all"
INSIDE_IN_BAND = "inside"
INSIDE_OUT_OF_BAND = "not_inside"
PLAYBOOK_COHORT_INSIDE_VALUES: tuple[str, ...] = (INSIDE_ANY, INSIDE_IN_BAND, INSIDE_OUT_OF_BAND)

# "Room of at least one multiple" is a statement about a wall AHEAD. The lens's `no_wall_ahead`
# (nothing ahead on the map) and `room_unmeasured` (headroom known, no invalidation distance to
# divide by) are therefore NOT room-of-at-least-1R -- they are counted, never folded in. This is the
# shipped signals-table filter's own rule, reused rather than forked.
PLAYBOOK_COHORT_ROOM_GE_1R_BUCKETS: tuple[str, ...] = (ROOM_1R_2R, ROOM_GE_2R)


def cohort_key(backing: str, inside: str) -> str:
    """The composed cohort identity — the ``"<setup_id>:<side>"`` pool-key idiom applied to the two
    filter axes. Neither axis value contains a colon, so the key splits unambiguously."""
    return f"{backing}:{inside}"


PLAYBOOK_COHORT_KEYS: tuple[str, ...] = tuple(
    cohort_key(backing, inside)
    for backing in PLAYBOOK_COHORT_BACKING_VALUES
    for inside in PLAYBOOK_COHORT_INSIDE_VALUES
)

# The cohort that asks nothing about location -- and therefore IS the record's own summary.
UNFILTERED_COHORT = cohort_key(BACKING_ANY, INSIDE_ANY)

# The named reasons a signal is eligible to be pooled but joins no narrowed cohort. Counted per
# pool, never silently dropped: "no signal was at a wall" and "no map has been computed yet" both
# produce an n: 0 cell, and only these counts separate them.
EXCLUDED_NOT_COMPUTED = "n_excluded_not_computed"
EXCLUDED_NO_BAND_CONTEXT = "n_excluded_no_band_context"
EXCLUDED_ROOM_UNMEASURED = "n_excluded_room_unmeasured"
EXCLUDED_OTHER_LOCATION = "n_excluded_other_location"
EXCLUDED_NO_CONTEXT = "n_excluded_no_context"
_EXCLUSION_KEYS: tuple[str, ...] = (
    EXCLUDED_NOT_COMPUTED,
    EXCLUDED_NO_BAND_CONTEXT,
    EXCLUDED_ROOM_UNMEASURED,
    EXCLUDED_OTHER_LOCATION,
    EXCLUDED_NO_CONTEXT,
)

COHORT_REGISTER = (
    "the record's own recorded pooled means, narrowed to a declared cohort of the locations its "
    "signals fired at. Every number is pooled from the SAME already-recorded forward measurements "
    "the record itself pooled, through the same rail helpers, over the same per-setup-and-side cap "
    "— so the unfiltered cohort is the record's own summary, value for value, and every narrowed "
    "cohort is a subset of it: narrowing can only reduce how many signals a cell covers, never add "
    "one. A signal joins a cohort by the location the band-context lens already served for it — at "
    "a wall behind reads that lens's own backing bucket, room of at least one multiple reads its "
    "room bucket, inside reads whether the entry sat inside a band — never by a threshold applied "
    "here. A signal whose map has not been computed yet, or whose computed map puts no band around "
    "its entry, carries no location and therefore joins no narrowed cohort; it is counted in that "
    "cohort's own basis rather than assumed to be outside one. A signal at a wall with nothing "
    "ahead of it, or with no invalidation distance to measure room against, is counted the same "
    "way rather than placed. Each pooled signal brings the one seeded random-minute anchor drawn "
    "beside it at compute time, so both lines of a narrowed pool describe the same signals — "
    "unlike the cross-session evidence table, where a smaller baseline count discloses the pooling "
    "cap; an anchor whose own signal could not be attributed is counted, never guessed. Signals "
    "recorded beyond the record's own per-setup-and-side cap never fed the recorded summary and "
    "never feed a cohort of it; the cross-session evidence fold is where every recorded signal is "
    "pooled. Nothing here is re-detected, re-measured, or written back, and this payload describes "
    "measurements of what already happened, carrying no probability and no forecast about what "
    "happens next"
)


def cohort_parameters() -> dict:
    """The vocabulary this fold serves, disclosed on the payload rather than re-declared by any
    reader. ``context_algorithm`` names the lens version the cohorts were cut from, so a reader can
    tell which location rules produced a membership."""
    return {
        "algorithm": PLAYBOOK_COHORT_ALGORITHM_VERSION,
        "context_algorithm": PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
        "backing_values": list(PLAYBOOK_COHORT_BACKING_VALUES),
        "inside_values": list(PLAYBOOK_COHORT_INSIDE_VALUES),
        "cohort_keys": list(PLAYBOOK_COHORT_KEYS),
        "unfiltered_cohort": UNFILTERED_COHORT,
        "pooling": "record_in_cap_only",
        "baseline_pairing": "paired_signal",
        "room_ge_1r_buckets": list(PLAYBOOK_COHORT_ROOM_GE_1R_BUCKETS),
    }


# --- membership: the ONE owner of the predicate --------------------------------------------------


def _backing_values_for(band_context: dict) -> tuple[str, ...]:
    values = [BACKING_ANY]
    if band_context.get("status") == LOCATED and band_context.get("backing_bucket") == AT_WALL:
        values.append(BACKING_AT_WALL)
        if band_context.get("room_bucket") in PLAYBOOK_COHORT_ROOM_GE_1R_BUCKETS:
            values.append(BACKING_AT_WALL_ROOM_GE_1R)
    return tuple(values)


def _inside_values_for(band_context: dict) -> tuple[str, ...]:
    values = [INSIDE_ANY]
    if band_context.get("status") == LOCATED:
        # `status == LOCATED` is load-bearing, not defensive. The lens serves
        # `containing_band: null` for EVERY absence too, so a bare "containing_band is None" test
        # would file every un-warmed signal under "not inside a band" -- claiming a location for an
        # event that has none. This module owns the predicate so no reader can restate it that way.
        values.append(INSIDE_IN_BAND if band_context.get("containing_band") else INSIDE_OUT_OF_BAND)
    return tuple(values)


def signal_cohorts(band_context: dict | None) -> tuple[str, ...]:
    """Every declared cohort one signal belongs to, in declared order. A signal with no served
    location belongs to the unfiltered cohort ONLY — which is exactly what "all" means: the
    unfiltered cohort asks nothing about location, and an event with none cannot answer anything
    else."""
    if not band_context:
        return (UNFILTERED_COHORT,)
    backings = _backing_values_for(band_context)
    insides = _inside_values_for(band_context)
    members = {cohort_key(b, i) for b in backings for i in insides}
    return tuple(key for key in PLAYBOOK_COHORT_KEYS if key in members)


def _exclusion_reason(band_context: dict | None) -> str:
    """Why an eligible signal joins no narrowed cohort — first match wins, most specific first."""
    if band_context is None:
        return EXCLUDED_NO_CONTEXT
    status = band_context.get("status")
    if status == NOT_COMPUTED:
        return EXCLUDED_NOT_COMPUTED
    if status == NO_BAND_CONTEXT:
        return EXCLUDED_NO_BAND_CONTEXT
    if band_context.get("room_bucket") == ROOM_UNMEASURED:
        return EXCLUDED_ROOM_UNMEASURED
    return EXCLUDED_OTHER_LOCATION


# --- the record/context join ----------------------------------------------------------------------


def _pool_key(signal: dict) -> str:
    return f"{signal.get('setup_id')}:{signal.get('side')}"


def _in_cap_pools(record: dict, context: dict | None) -> tuple[dict, dict, set]:
    """Per pool: the in-cap forward blocks the record itself pooled, the band context aligned to
    each of them, and the set of pools whose context could not be aligned.

    The in-cap prefix is the record's OWN rule — the first ``rail_max_touches_per_row`` measured
    signals of a pool in record order — cross-checked against the record's own
    ``signals_beyond_cap``. A disagreement refuses that pool's narrowed cohorts rather than risking
    a mispairing; the unfiltered cohort is unaffected because it never consults any of this."""
    cap = (record.get("parameters") or {}).get("rail_max_touches_per_row")
    beyond = record.get("signals_beyond_cap") or {}

    measured: dict[str, list[dict]] = {}
    for signal in record.get("signals") or []:
        if signal.get("forward") is None:
            continue
        measured.setdefault(_pool_key(signal), []).append(signal)

    served: dict[str, list[dict]] = {}
    for entry in (context or {}).get("signals") or []:
        if entry.get("measured"):
            served.setdefault(entry.get("pool_key"), []).append(entry)

    events: dict[str, list[dict]] = {}
    contexts: dict[str, list[dict | None]] = {}
    unaligned: set[str] = set()
    for pool, signals in measured.items():
        prefix = signals if cap is None else signals[:cap]
        events[pool] = [signal["forward"] for signal in prefix]
        pool_served = served.get(pool)
        cap_agrees = len(signals) - len(prefix) == beyond.get(pool, 0)
        if pool_served is None or len(pool_served) != len(signals) or not cap_agrees:
            unaligned.add(pool)
            contexts[pool] = [None] * len(prefix)
        else:
            contexts[pool] = [entry.get("band_context") for entry in pool_served[: len(prefix)]]
    return events, contexts, unaligned


def _anchor_rows(record: dict, context: dict | None) -> tuple[dict, dict]:
    """Per pool: the recorded anchor measurements, and whether each was attributed to its own signal
    (the lens's close-price-verified verdict, never re-derived here)."""
    recorded = record.get("baseline_anchors") or {}
    served = (context or {}).get("baseline_anchors") or {}
    measures: dict[str, list[dict]] = {}
    attributed: dict[str, list[bool]] = {}
    for pool, rows in recorded.items():
        measures[pool] = list(rows)
        pool_served = served.get(pool)
        if pool_served is None or len(pool_served) != len(rows):
            attributed[pool] = [False] * len(rows)
        else:
            attributed[pool] = [
                row.get("attribution") == "positional_verified" for row in pool_served
            ]
    return measures, attributed


# --- the served fold --------------------------------------------------------------------------------


def cohort_signal_rows(record: dict, context: dict | None) -> list[dict]:
    """Per recorded signal: which cohorts it belongs to, and whether it was in-cap.

    Two different facts under two names. ``cohorts`` is DISPLAY membership and ignores the cap — a
    beyond-cap signal at a wall still belongs in a narrowed row list. ``in_cap`` says whether it fed
    the pooled means, which is the fact the "beyond cap" chip needs (deriving that from a row's
    position breaks the moment a filter narrows the list)."""
    cap = (record.get("parameters") or {}).get("rail_max_touches_per_row")
    served: dict[str, list[dict]] = {}
    for entry in (context or {}).get("signals") or []:
        served.setdefault(entry.get("pool_key"), []).append(entry)

    seen: dict[str, int] = {}
    rows: list[dict] = []
    for signal in record.get("signals") or []:
        pool = _pool_key(signal)
        measured = signal.get("forward") is not None
        index = seen.get(pool, 0)
        if measured:
            seen[pool] = index + 1
        pool_served = served.get(pool) or []
        band_context = None
        for entry in pool_served:
            if entry.get("trigger_ts") == signal.get("trigger_ts") and entry.get(
                "symbol"
            ) == signal.get("symbol"):
                band_context = entry.get("band_context")
                break
        rows.append(
            {
                "symbol": signal.get("symbol"),
                "setup_id": signal.get("setup_id"),
                "side": signal.get("side"),
                "pool_key": pool,
                "trigger_ts": signal.get("trigger_ts"),
                "measured": measured,
                "in_cap": measured and (cap is None or index < cap),
                "cohorts": list(signal_cohorts(band_context)),
            }
        )
    return rows


def _empty_pool_basis() -> dict:
    basis = {"n_eligible": 0, "n_signals": 0, "n_anchors": 0, "n_anchors_unattributable": 0}
    basis.update({key: 0 for key in _EXCLUSION_KEYS})
    return basis


def fold_cohorts(record: dict, context: dict | None) -> dict:
    """Every declared cohort's pooled summary for ONE record, in the record's own shape.

    Pool order and measure list are the RECORD's own (``summary`` key order,
    ``parameters.signal_measures``), so the unfiltered cohort round-trips to byte-identical output.
    Pooling is the rail's own ``_collect_measures``/``_avg_cell`` — imported verbatim, one call
    site, never a second implementation."""
    summary = record.get("summary") or {}
    measures = (record.get("parameters") or {}).get("signal_measures") or list(
        PLAYBOOK_SIGNAL_MEASURES
    )
    events, contexts, unaligned = _in_cap_pools(record, context)
    anchor_measures, anchor_attributed = _anchor_rows(record, context)
    pool_keys = list(summary.keys())

    cohorts: dict[str, dict] = {}
    for key in PLAYBOOK_COHORT_KEYS:
        backing, inside = key.split(":", 1)
        unfiltered = key == UNFILTERED_COHORT
        pools: dict[str, dict] = {}
        pool_summaries: dict[str, dict] = {}
        for pool in pool_keys:
            pool_events = events.get(pool, [])
            pool_contexts = contexts.get(pool, [])
            basis = _empty_pool_basis()
            basis["n_eligible"] = len(pool_events)

            if unfiltered:
                # The unfiltered cohort never consults the context. That is what makes it equal to
                # the record's own summary under every context state, including none at all.
                chosen = list(range(len(pool_events)))
                chosen_anchors = list(anchor_measures.get(pool, []))
            else:
                chosen = []
                for index in range(len(pool_events)):
                    band_context = pool_contexts[index] if index < len(pool_contexts) else None
                    if band_context is not None and key in signal_cohorts(band_context):
                        chosen.append(index)
                    else:
                        basis[_exclusion_reason(band_context)] += 1
                rows = anchor_measures.get(pool, [])
                flags = anchor_attributed.get(pool, [])
                chosen_anchors = [
                    rows[i]
                    for i in chosen
                    if i < len(rows) and i < len(flags) and flags[i]
                ]
                basis["n_anchors_unattributable"] = sum(
                    1 for i in chosen if i < len(flags) and not flags[i]
                )

            basis["n_signals"] = len(chosen)
            basis["n_anchors"] = len(chosen_anchors)
            pools[pool] = {**basis, "context_aligned": pool not in unaligned}

            signal_pool = _collect_measures([pool_events[i] for i in chosen])
            baseline_pool = _collect_measures(chosen_anchors)
            pool_summaries[pool] = {
                measure: {
                    "signals": _avg_cell(*signal_pool[measure]),
                    "baseline": _avg_cell(*baseline_pool[measure]),
                }
                for measure in measures
                if measure in signal_pool
            }

        rolled = _empty_pool_basis()
        for pool_basis in pools.values():
            for field in rolled:
                rolled[field] += pool_basis[field]
        cohorts[key] = {
            "backing": backing,
            "inside": inside,
            "summary": pool_summaries,
            "pools": pools,
            "basis": rolled,
        }

    signals = cohort_signal_rows(record, context)
    return {
        "playbook_id": record.get("id"),
        "session_date": record.get("session_date"),
        "parameters": {
            **cohort_parameters(),
            "pool_keys": pool_keys,
            "measures": list(measures),
        },
        "cohorts": cohorts,
        "signals": signals,
        "basis": {
            "n_signals_recorded": len(signals),
            "n_signals_measured": sum(1 for row in signals if row["measured"]),
            "n_signals_in_cap": sum(1 for row in signals if row["in_cap"]),
            "n_pools": len(pool_keys),
            "n_pools_context_unaligned": len(unaligned),
            "n_anchors": sum(len(rows) for rows in anchor_measures.values()),
            "context_status": "served" if context else "absent",
        },
        "register": COHORT_REGISTER,
    }
