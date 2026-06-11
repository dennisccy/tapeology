"""Segregated journal analytics (capability 31, J-59) — the SINGLE-owner read-only aggregator.

This is the ONE place the J-59 aggregates are computed. The single serving path
``GET /research/analytics`` renders this module's projection VERBATIM (the frontend derives nothing).

What it does — and, just as bindingly, what it MUST NOT do:

  * **Reads persisted rows ONLY.** It aggregates already-persisted values — the ``theses`` rows
    (status / setup / direction / feed / fingerprint / grades / review tags), the persisted excursion
    records (``theses.excursions``), the action marks (``actions``), and the append-only verdict
    timeline (``verdict_events``). It NEVER recomputes any underlying canonical value: no re-derived
    verdict, no second excursion math, no second R formula. Realized-R for the acted-trade block comes
    from the ONE registered R path (``marks.marks_projection`` — the row-27 projection), never a second
    formula or inline arithmetic.

  * **Never pools.** The top-level shape is a list of partitions keyed by (``data_feed``,
    ``config_fingerprint``); within a partition, groups are per ``setup_type`` × ``direction``. There
    is NO "all" / pooled / overall rollup anywhere (the honesty anti-goal — analytics MUST NOT pool
    across feeds or fingerprints).

  * **Abandonment stays visible.** Abandoned theses remain in every denominator (``n``) — no
    survivorship pruning — AND surface as their own ``abandonment`` count (present even when 0).

  * **Insufficient-sample is an explicit gate, never a silent percentage.** A group whose ``n`` is
    below ``Config.analytics_min_sample_size`` carries ``insufficient_sample: True`` with ``n`` still
    present; the distributions are still computed (the frontend chooses to show the marker instead of
    bare numbers), so the data is honest either way.

  * **Truncated horizons counted separately.** A truncated horizon (the stream/gap cut it short
    before +1R / -1R could be answered) is counted in its own ``truncated`` bucket per horizon —
    NEVER folded into the resolved ternary buckets, never extrapolated.

  * **Honest omission.** Median time-to-confirm is ``None`` for a group with no confirmation (never a
    fabricated zero). Median spread/R is ``None`` where no anchored population carries one. The two
    excursion populations (confirmation-anchored / entry-anchored) are kept structurally apart.

  * **Deterministic.** Output depends only on the persisted rows + the config — two identical calls
    over a fixed DB are byte-equal (groups + partitions are emitted in a stable sorted order, R
    figures rounded the same way the persisted records are).
"""

from __future__ import annotations

import statistics

from ..config import Config
from .marks import marks_projection
from .store import JournalStore, ThesisRecord

# The terminal status that is the abandonment bucket (kept in n; surfaced as its own count).
_ABANDONED = "abandoned"

# The published-verdict id the median time-to-confirm anchors on (first such timeline event wins).
_CONFIRMING = "confirming"

# The confirmation-anchored excursion population id (the segregated population analytics aggregates;
# the entry-anchored population's R lives in the acted-trade block via the marks projection instead).
_CONFIRMATION_POP = "confirmation"

# The ternary outcome ids (mirrors excursions.py — LABELS only, never a numeric score). A truncated
# horizon (outcome still ``None`` AND ``truncated``) is counted in its OWN bucket, never these three.
_TERNARY_IDS = ("+1R_first", "-1R_first", "neither_within_horizon")


def _median_or_none(values: list[float]) -> float | None:
    """The median of ``values`` rounded to 4 dp (byte-stable), or ``None`` for an empty list.

    ``None`` is the honest omission (no data → no number, never a fabricated zero). Rounding mirrors
    the persisted excursion records' 4-dp discipline so two runs are byte-equal."""
    if not values:
        return None
    return round(statistics.median(values), 4)


def _confirm_logical_ts(events: list) -> float | None:
    """The logical-time instant of the FIRST published ``confirming`` event (else ``None``).

    Reads the append-only verdict timeline VERBATIM — never recomputed. ``None`` (no confirmation ever
    published) is the honest omission the median treats as "this thesis contributes no time-to-confirm".
    """
    for ev in events:  # the store returns events in insertion (logical) order
        if ev.verdict == _CONFIRMING:
            return ev.logical_ts
    return None


def _empty_horizon_row(horizon: float) -> dict:
    """A zeroed per-horizon ternary row (all buckets + truncated at 0, no spread/R yet)."""
    return {
        "horizon": horizon,
        "+1R_first": 0,
        "-1R_first": 0,
        "neither_within_horizon": 0,
        "truncated": 0,
        "median_spread_per_r": None,
    }


def _aggregate_group(
    theses: list[ThesisRecord],
    *,
    store: JournalStore,
    config: Config,
) -> dict:
    """Aggregate ONE (feed, fingerprint, setup, direction) group from its persisted theses.

    Every figure is a read/aggregation of already-persisted values — no canonical value is recomputed.
    Realized-R reuses ``marks.marks_projection`` (the ONE registered R path); excursion ternaries /
    truncation / spread-at-anchor come from the persisted ``theses.excursions`` record; the
    time-to-confirm comes from the persisted append-only timeline.
    """
    n = len(theses)
    abandonment = sum(1 for t in theses if t.status == _ABANDONED)

    # --- confirmation-anchored excursion distribution (per configured horizon) ------------------
    # Per horizon: ternary bucket counts + a separate truncated count + the spreads/R for the median.
    horizon_rows: dict[float, dict] = {
        h: _empty_horizon_row(h) for h in config.excursion_horizons_seconds
    }
    horizon_spreads: dict[float, list[float]] = {h: [] for h in config.excursion_horizons_seconds}

    for t in theses:
        excursions = t.excursions
        if not excursions or not excursions.get("tracked"):
            continue  # absent / not-tracked record contributes nothing (honest omission, never a zero)
        pop = excursions.get("populations", {}).get(_CONFIRMATION_POP)
        if not pop:
            continue
        r_basis_value = pop.get("r_basis")
        spread_at_anchor = pop.get("spread_at_anchor")
        for hz in pop.get("horizons", []):
            h = hz.get("horizon")
            row = horizon_rows.get(h)
            if row is None:
                continue  # a horizon not in the current config (a pre-config-change record) is skipped
            outcome = hz.get("outcome")
            truncated = bool(hz.get("truncated"))
            if truncated and outcome is None:
                # Truncated BEFORE the ternary could resolve — its OWN bucket, never a resolved bucket.
                row["truncated"] += 1
            elif outcome in _TERNARY_IDS:
                row[outcome] += 1
            # An open-but-not-truncated horizon (outcome None, not truncated) is genuinely undetermined
            # and contributes to NO bucket (neither resolved nor truncated) — never fabricated.
            # Spread/R (the no-cost caveat as a number) — only when both the anchor spread and a
            # positive R basis are present (a degenerate R == 0 yields no honest cost figure).
            if spread_at_anchor is not None and r_basis_value:
                horizon_spreads[h].append(spread_at_anchor / r_basis_value)

    for h, row in horizon_rows.items():
        row["median_spread_per_r"] = _median_or_none(horizon_spreads[h])

    confirmation_excursions = {
        "horizons": [horizon_rows[h] for h in config.excursion_horizons_seconds]
    }

    # --- median time-to-confirm (declaration -> first published confirming, logical time) -------
    times_to_confirm: list[float] = []
    for t in theses:
        confirm_ts = _confirm_logical_ts(store.verdict_events(t.id))
        if confirm_ts is not None:
            times_to_confirm.append(confirm_ts - t.created_logical_ts)
    median_time_to_confirm = _median_or_none(times_to_confirm)

    # --- tag frequencies (USER-confirmed reviews only — machine suggestions never counted) ------
    tag_counts: dict[str, int] = {}
    for t in theses:
        if not t.reviewed or not t.review_tags:
            continue
        for tag in t.review_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    tag_frequencies = [
        {"tag": tag, "count": tag_counts[tag]} for tag in sorted(tag_counts)
    ]

    # --- acted-trade block (entry+exit-marked) — STRUCTURALLY DISJOINT from confirmation stats --
    # Realized-R comes from the ONE registered R path (marks_projection) over the persisted marks —
    # never a second formula, never inline arithmetic here.
    realized_rs: list[float] = []
    acted_spread_per_r: list[float] = []
    for t in theses:
        actions = store.get_actions(t.id)
        proj = marks_projection(t, actions)
        realized_r = proj.get("realized_r")
        if realized_r is None:
            continue  # not an acted (entry+exit) trade — excluded from this population
        realized_rs.append(round(realized_r, 4))
        entry = proj.get("entry")
        r_basis_value = proj.get("r_basis")
        if entry is not None and entry.get("spread_at_mark") is not None and r_basis_value:
            acted_spread_per_r.append(entry["spread_at_mark"] / r_basis_value)
    acted_trade = {
        "n": len(realized_rs),
        "median_realized_r": _median_or_none(realized_rs),
        "median_spread_per_r": _median_or_none(acted_spread_per_r),
    }

    return {
        "setup_type": theses[0].setup_type,
        "direction": theses[0].direction,
        "n": n,
        "abandonment": abandonment,
        "insufficient_sample": n < config.analytics_min_sample_size,
        "confirmation_excursions": confirmation_excursions,
        "median_time_to_confirm": median_time_to_confirm,
        "tag_frequencies": tag_frequencies,
        "acted_trade": acted_trade,
    }


def compute_analytics(store: JournalStore, config: Config) -> dict:
    """The full ``GET /research/analytics`` projection (capability 31, J-59) — read-only over persisted rows.

    Reads every persisted thesis (``store.list_theses()`` with no filter / no limit), buckets them into
    (``data_feed``, ``config_fingerprint``) partitions and, within each, per ``setup_type`` ×
    ``direction`` groups, and aggregates each group via :func:`_aggregate_group`. NEVER pools across
    feeds or fingerprints; emits NO "all"/overall rollup. Partitions and groups are emitted in a stable
    sorted order so two identical calls are byte-equal (the J-59 determinism clause). An empty journal
    yields ``{"partitions": [], "min_sample_size": ...}`` — an honest empty payload, not an error and
    not a fabricated group.
    """
    all_theses = store.list_theses()  # no filter, no limit => every persisted thesis row, verbatim

    # Partition key = (data_feed, config_fingerprint); group key (within) = (setup_type, direction).
    partitions: dict[tuple[str, str], dict[tuple[str, str], list[ThesisRecord]]] = {}
    for t in all_theses:
        pkey = (t.data_feed, t.config_fingerprint)
        gkey = (t.setup_type, t.direction)
        partitions.setdefault(pkey, {}).setdefault(gkey, []).append(t)

    partition_payloads: list[dict] = []
    for (data_feed, fingerprint) in sorted(partitions):
        groups = partitions[(data_feed, fingerprint)]
        group_payloads = [
            _aggregate_group(groups[gkey], store=store, config=config)
            for gkey in sorted(groups)
        ]
        partition_payloads.append(
            {
                "data_feed": data_feed,
                "config_fingerprint": fingerprint,
                # A short form for compact display; the FULL value is always present above so two
                # records are never silently compared across fingerprints.
                "config_fingerprint_short": fingerprint[:8],
                "groups": group_payloads,
            }
        )

    return {
        "partitions": partition_payloads,
        # The serving-only min-sample threshold echoed so the frontend labels the gate honestly (it is
        # excluded from config_fingerprint — a display choice never fragments the pools).
        "min_sample_size": config.analytics_min_sample_size,
    }
