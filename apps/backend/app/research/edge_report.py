"""The baseline-edge report (era-3 capability 9 groundwork, J-09) —
``python -m app.research.edge_report --out <path>`` — PLUS the era-5B J-04 additive 3-way
strategy-comparison report served by ``GET /research/edge-report`` (see
``run_strategy_comparison_report`` near the bottom of this module for that section's own detailed
docstring; every helper/CLI above it is UNTOUCHED, byte-identical to before).

Answers the era's founding question for the FROZEN champion ALONE — no candidate, no comparison,
no promotion: does the currently persisted champion (read verbatim via
``store.get_champion_pointer()``, NEVER hardcoded) carry a measurable, positive, simulated
hold-out edge across every registered dataset? Modeled structurally on
``app/research/pnl_scan.py`` (the champion-pointer read, the ONE ``BacktestJobManager``
computation path, the verbatim ``aggregates`` read, the sorted-key deterministic render) but
STRICTLY READ-ONLY: it has no ``_promote``, appends no PnL-ledger row, and moves no champion
pointer — there is nothing here to promote, which is what makes the "no train-only promotion"
anti-goal satisfied BY CONSTRUCTION.

Disciplines, clause by clause:

  * **No second computation path.** Every backtest this module runs goes through the SAME
    ``BacktestJobManager.create`` + ``run_sync`` every other era-3 CLI uses (``pnl_baseline``,
    ``pnl_scan``). This module never touches a dataset file, an engine, or a trade/fill/R
    computation directly — it reads the persisted row-31 ``aggregates`` (and the seeded null
    baseline's own ``aggregates``) VERBATIM.

  * **Never pooled across splits.** Train and hold-out are two separate, independently-ranked
    report sections; nothing is summed or averaged between them.

  * **Ranking.** Within each section, datasets are ordered by the champion's OWN net R on that
    dataset (descending), tie-broken by ``dataset_id`` ascending — deterministic and reproducible
    across re-runs (a flagged judgment call — see the dev handoff for the exact reasoning).

  * **The positive-edge flag, precisely (hold-out ONLY).** A hold-out dataset is flagged iff its
    champion measurement clears ``net_r > 0`` AND ``net_usd > 0`` AND
    ``n >= Config.pnl_min_sample_size`` (the existing "insufficient sample" floor — a
    display/measurement gate, not a promotion gate, so it reuses that field rather than minting a
    third minimum) AND it beats its OWN null baseline on BOTH net R and net $ (the codebase's
    established "gate on both R and $ jointly" convention — see ``pnl_scan._is_positive``). Train
    datasets are ranked and shown the same way but are NEVER flagged — the key is simply absent
    from a train row (the honest-omission pattern used throughout this codebase, e.g.
    ``ThesisRecord.risk_flags``). Zero qualifying datasets — including the true-empty registry —
    is the explicit ``"no positive-edge dataset"`` finding, never a fabricated edge.

  * **Deterministic, byte-identical re-runs.** The report never carries a backtest-report id or a
    wall-clock field — neither is ever even collected, so there is nothing to strip — so two
    independent fresh-state runs of an identical scenario produce byte-identical ``--out`` bytes.

  * **Honest failure states.** A dataset failing integrity verification anywhere in the store, or
    a backtest ending anything other than ``done``, aborts with an explicit ``EdgeReportError``
    before anything is written — a partial report is a misleading report.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ..config import (
    CONFIG,
    Config,
    PROFILE_DEFAULT,
    STRATEGY_TAPE_ID,
    STRATEGY_TAPE_MAP_ID,
    STRATEGY_V1_ID,
)
from .bars import BarStore
# ``_aggregate`` is imported PRIVATE (the ``backtests.py``-owned-private-helper precedent —
# ``r_basis``/the state-native arming family relocated there whole, era-5D J-01): the ONE
# trade-population aggregator every other report in this codebase already computes with
# (n/gross/net R and $/win_rate/max_drawdown_r) -- reused VERBATIM for a strategy-comparison
# cell's pooled trade list, never a second R/$/edge formula.
from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate
from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
# era-fast_wall J-05: ``pair_cache_key``/``EdgeReportBacktestCache`` for the per-pair sub-cache;
# ``_config_content_hash`` reused VERBATIM from ``edge_report_cache.py`` (never re-derived a
# second time -- see ``edge_report_backtest_cache.py``'s own module docstring for the full "why").
from .edge_report_backtest_cache import EdgeReportBacktestCache, pair_cache_key
from .edge_report_cache import EdgeReportCache, _config_content_hash
# ``_store_signature`` imported PRIVATE (the identical ``_aggregate`` precedent above, and the
# phase plan's own explicit suggestion): the ONE bar-store-signature tuple shape ``setups.py``
# already computes for its OWN scan cache, reused verbatim here rather than duplicated.
from .setups import _store_signature, compute_setups
from .store import JournalStore

__all__ = [
    "EdgeReportError",
    "EdgeReportComputeCancelled",
    "run_edge_report",
    "run_strategy_comparison_report",
    "peek_strategy_comparison_report",
    "main",
]

# era-5B J-04: the three registered strategies a comparison cell may ever carry, in the SAME
# registration order ``Config.strategy_registry()`` serves -- read here so a cell's own
# ``strategy_id`` is never a restated literal.
_ALL_STRATEGY_IDS: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID)

# The exact, honest empty finding (DoD-mandated literal string) — emitted whenever zero hold-out
# datasets clear the positive-edge gate, including the true-empty-registry case.
NO_POSITIVE_EDGE_FINDING = "no positive-edge dataset"

# era-fast_wall J-01: the not-computed payload's own explanatory ``detail`` string (DoD: "a detail
# naming the trigger") — ONE canonical literal, never restated inline at ``peek_strategy_
# comparison_report``'s own call site.
EDGE_REPORT_NOT_COMPUTED_DETAIL = (
    "The 3-way strategy-comparison sweep has not been run for the current dataset registry and "
    "configuration. It never runs automatically on a GET -- an operator must trigger the compute."
)


class EdgeReportError(Exception):
    """The report could not complete honestly — a dataset failed integrity verification or a
    backtest ended non-``done``. Explicit; nothing is written to ``--out``."""


class EdgeReportComputeCancelled(Exception):
    """era-fast_wall J-04 — raised by ``_split_cells`` when an actively-supplied ``should_abort()``
    hook returns ``True`` between dataset x strategy pairs (the cooperative-cancel seam
    ``run_strategy_comparison_report`` threads down from an operator/CLI trigger). Propagates
    UNCHANGED through ``EdgeReportCache.get_or_compute``/``compute_and_publish`` — both publish
    ONLY after their ``compute_fn`` returns normally (see those methods' own docstrings), so a
    cancelled run publishes NOTHING to the report cache, by construction, with no change needed to
    either method's body. Caught by ``edge_report_compute.EdgeReportComputeManager``'s worker
    thread at its outer boundary to resolve the job's snapshot to ``state: "cancelled"`` rather
    than ``"failed"`` (the NOTES' suggested mechanism)."""


# --- reused computation: ONE backtest per dataset, via the EXISTING runner ----------------------


def _verified_records(dataset_store: DatasetStore) -> list[dict]:
    """Every registered dataset metadata row, checksum-verified (the ONE ``DatasetStore.list``
    read). A file that fails integrity verification anywhere in the store aborts explicitly — a
    partial report is a misleading report. Shared by ``_split_datasets`` (below, filtered to one
    split) and ``peek_strategy_comparison_report`` (era-fast_wall J-01, which needs the FULL,
    unfiltered registry to key the cache and report ``dataset_count``) — ONE list-and-verify call
    site, never a second copy of this error-formatting."""
    records, errors = dataset_store.list()
    if errors:
        raise EdgeReportError(
            f"{len(errors)} dataset file(s) failed integrity verification "
            f"({[e['file'] for e in errors]}) — the report stops with nothing written"
        )
    return records


def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
    """Every registered dataset metadata row for ``split`` — see ``_verified_records`` for the
    integrity discipline."""
    return [r for r in _verified_records(dataset_store) if r["split"] == split]


def _run_backtest(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    dataset_id: str,
    *,
    strategy_id: str,
    profile: str,
    bar_store: BarStore | None = None,
) -> dict:
    """Run ONE backtest synchronously through the EXISTING public job API (the
    ``pnl_scan._run_backtest`` pattern) and return its persisted ``result`` block — refusing
    explicitly unless it completed ``done`` (a failed/cancelled report carries no served
    aggregates, so nothing could be honestly measured from it).

    ``bar_store`` (era-5B J-04, optional, defaults ``None`` — every EXISTING champion-only caller
    below is unaffected byte-for-byte) is threaded through to ``run_sync`` exactly like the
    backtest route's own seam: ``structure_tape``/``structure_tape_map`` read it to arm; v1
    ignores it."""
    payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
    jobs.run_sync(payload["id"], dataset_store=dataset_store, bar_store=bar_store)
    final = store.get_backtest(payload["id"]).payload
    if final.get("status") != STATUS_DONE:
        raise EdgeReportError(
            f"backtest '{payload['id']}' over dataset '{dataset_id}' (strategy={strategy_id}, "
            f"profile={profile}) ended '{final.get('status')}' "
            f"({final.get('error', 'no result block')}) — the report stops with nothing written"
        )
    return final["result"]


def _measurement(aggregates: dict) -> dict:
    """The net_r/net_usd/n triple copied VERBATIM from a persisted aggregates block (never
    recomputed) — the SAME shape ``pnl_scan._measurement`` copies for its own report rows."""
    return {"net_r": aggregates["net_r"], "net_usd": aggregates["net_usd"], "n": aggregates["n"]}


def _dataset_row(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    dataset_meta: dict,
    champion: dict,
) -> dict:
    """One dataset's row: the champion's measurement plus its seeded null baseline, both read
    VERBATIM from the ONE persisted backtest report — no second R/$/edge computation anywhere."""
    result = _run_backtest(
        jobs,
        store,
        dataset_store,
        dataset_meta["id"],
        strategy_id=champion["strategy_id"],
        profile=champion["profile"],
    )
    return {
        "dataset_id": dataset_meta["id"],
        "dataset_checksum": dataset_meta["checksum"],
        "champion": _measurement(result["aggregates"]),
        "null_baseline": _measurement(result["null_baseline"]["aggregates"]),
    }


def _beats_null(row: dict) -> bool:
    """"Beats its own null baseline": BOTH net R AND net $ exceed the seeded random-entry
    baseline on the SAME dataset — the codebase's established "gate on both R and $ jointly"
    convention (see ``pnl_scan._is_positive``), applied here to the champion vs its own null
    rather than a candidate vs the champion. A genuine judgment call — see the dev handoff."""
    return (
        row["champion"]["net_r"] > row["null_baseline"]["net_r"]
        and row["champion"]["net_usd"] > row["null_baseline"]["net_usd"]
    )


def _is_positive_edge(row: dict, config: Config) -> bool:
    """The hold-out-only positive-edge gate: positive net R AND net $, at least the configured
    minimum sample size (``Config.pnl_min_sample_size`` — the existing display/measurement
    floor, reused verbatim, never a new field), AND beating the dataset's own null baseline."""
    champ = row["champion"]
    return (
        champ["net_r"] > 0
        and champ["net_usd"] > 0
        and champ["n"] >= config.pnl_min_sample_size
        and _beats_null(row)
    )


def _rank(rows: list[dict]) -> list[dict]:
    """Order one split's rows by the champion's OWN net R on that dataset (descending), tie-broken
    by ``dataset_id`` ascending — deterministic and reproducible across re-runs."""
    return sorted(rows, key=lambda r: (-r["champion"]["net_r"], r["dataset_id"]))


# --- the ONE computer of Data Contract row 37 ----------------------------------------------------


def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Config) -> dict:
    """Measure the CURRENT champion across every registered dataset ONCE. Returns the complete
    report dict — the SAME shape persisted to ``--out`` (the CLI is a thin wrapper). Raises
    ``EdgeReportError`` for a dishonest state — nothing is written. Strictly read-only: promotes
    nothing, appends no ledger row, moves no champion pointer."""
    champion = store.get_champion_pointer()
    jobs = BacktestJobManager(store, config)

    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)

    train_rows = _rank(
        [_dataset_row(jobs, store, dataset_store, ds, champion) for ds in train_datasets]
    )
    holdout_rows = _rank(
        [_dataset_row(jobs, store, dataset_store, ds, champion) for ds in holdout_datasets]
    )

    # The positive-edge flag is hold-out ONLY (train rows never carry the key — honest omission,
    # not a fabricated False): a dataset that never looked at hold-out data cannot honestly be
    # called an "edge" measurement.
    positive_edge_ids: list[str] = []
    for row in holdout_rows:
        row["positive_edge"] = _is_positive_edge(row, config)
        if row["positive_edge"]:
            positive_edge_ids.append(row["dataset_id"])

    finding = (
        NO_POSITIVE_EDGE_FINDING
        if not positive_edge_ids
        else f"positive-edge dataset(s): {', '.join(positive_edge_ids)}"
    )

    return {
        "register": REGISTER,
        "champion": champion,
        "pnl_min_sample_size": config.pnl_min_sample_size,
        "train": {"datasets": train_rows},
        "holdout": {"datasets": holdout_rows},
        "positive_edge_dataset_ids": positive_edge_ids,
        "finding": finding,
    }


# --- The 3-way strategy-comparison report (era-5B capability 6, J-04; Data Contract row
# "edge-report cells") -- an ADDITIVE extension of THIS module, never a fork: reuses the ONE
# ``BacktestJobManager.create`` + ``run_sync`` path above (``_run_backtest``, now threading
# ``bar_store`` through, see its own docstring), the verbatim ``_aggregate`` trade-population
# arithmetic (imported from ``backtests.py`` — never re-derived), and ``_split_datasets``' ONE
# checksum-verified ``DatasetStore.list()`` read per split (a dataset failing integrity
# verification anywhere aborts the WHOLE report explicitly, same as ``run_edge_report`` above).
# ``run_edge_report``/``main``/``_render_report`` and every helper above this comment stay
# UNTOUCHED — the era-3 champion-only CLI's behaviour is byte-identical to before.
#
# Answers a DIFFERENT question than the champion-only report above: not "does the CURRENT
# champion show a hold-out edge", but "which of the three REGISTERED strategies (v1 /
# structure_tape / structure_tape_map) actually profits, broken down by the tradable-map class,
# side, and touch reaction the recorded window was scanned FROM" — v1/structure_tape/
# structure_tape_map are all measured, never just the champion; the champion pointer itself is
# never read, moved, or promoted by this section (there is nothing here to promote — the identical
# "no train-only promotion, by construction" property ``run_edge_report`` already has).
#
# A "cell" is EXACTLY one (strategy_id, band_class, band_side, reaction, feed) combination —
# strategy x class x side x reaction is the DoD's named shape; ``feed`` is carried as a FIFTH,
# additive dimension so two different feeds' recordings NEVER pool into one measurement (the
# never-pool-across-feeds anti-goal, actively load-bearing here for the first time: unlike every
# EARLIER era-3/4/5 surface, which only ever sees one feed's data per call, this report can
# genuinely receive a mixed-feed dataset registry). Cells are materialized LAZILY -- only for
# (dataset, event) pairs that genuinely attribute -- rather than pre-registering every
# combinatorial slot: unlike the class-only ``_aggregate_by_class`` breakdown (a FIXED, three-value
# enum with no further sub-dimension), a cell's own ``feed`` value is data-driven and unbounded, so
# there is no fixed "every combination" skeleton to pre-populate honestly. An all-empty ``cells``
# list (every registered dataset's window contains no scan event at all, e.g. a symbol outside the
# config-owned panel) is therefore a valid degenerate case of "all cells insufficient_sample" — a
# report with a smaller-than-expected cell count is never an error.


def _dataset_event(dataset_meta: dict, events: list[dict]) -> dict | None:
    """The ``compute_setups`` event this dataset was recorded around, or ``None`` when no scan
    event's own touch falls inside the dataset's registered window — datasets do not carry
    class/side/reaction themselves; only events do (module docstring). The
    ``setups._matching_dataset`` window-containment TEST, mirrored (numeric epoch comparison,
    inclusive both ends — the identical ``parse_utc_epoch`` discipline, never a lexicographic
    string compare) but in the OPPOSITE direction: given ONE already-verified dataset (from THIS
    module's own ``_split_datasets`` read), scan the already-computed ``events`` list for a match,
    rather than re-opening a second ``DatasetStore.list()`` read the way ``_matching_dataset``
    itself does internally (which silently drops a corrupt file's error — inconsistent with this
    module's OWN all-or-nothing integrity discipline, so it is never called from here). Ties (more
    than one event's touch falling inside the SAME window) break on the earliest ``touch_ts``, then
    event ``id`` — deterministic, never insertion-order happenstance."""
    window_start = parse_utc_epoch(dataset_meta["window_start_utc"])
    window_end = parse_utc_epoch(dataset_meta["window_end_utc"])
    candidates = [
        e for e in events
        if e["symbol"] == dataset_meta["symbol"]
        and window_start <= parse_utc_epoch(e["touch_ts"]) <= window_end
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda e: (e["touch_ts"], e["id"]))


def _cell_key(cell: dict) -> tuple:
    """The full identity tuple a cell is pooled/matched by — strategy x class x side x reaction x
    feed, the never-pool-across-feeds dimension included."""
    return (cell["strategy_id"], cell["band_class"], cell["band_side"], cell["reaction"], cell["feed"])


# --- era-fast_wall J-04: the operator-run compute's progress/cancel seam --------------------------
# ``_count_eligible_pairs`` and ``_ProgressReporter`` exist ONLY to report progress; neither
# changes what ``_split_cells`` computes. ``_count_eligible_pairs`` reuses ``_dataset_event`` (the
# SAME join ``_split_cells``'s own loop below re-checks per dataset — a one-line filter repeated,
# never a second join) purely to pre-size the progress snapshot's ``backtests_total`` BEFORE the
# loop starts (both splits' eligible-pair counts are known only once ``compute_setups`` has run).


def _count_eligible_pairs(datasets: list[dict], events: list[dict]) -> int:
    """The number of (dataset, strategy) backtest pairs ``_split_cells`` will actually run for
    ``datasets`` — every dataset resolving an owning, classified event, times the three registered
    strategies (``_ALL_STRATEGY_IDS``)."""
    eligible = 0
    for dataset_meta in datasets:
        event = _dataset_event(dataset_meta, events)
        if event is not None and event["band"]["class"] is not None:
            eligible += len(_ALL_STRATEGY_IDS)
    return eligible


class _ProgressReporter:
    """Wraps a caller-supplied ``progress`` dict-patch sink with running totals SHARED across both
    the train and hold-out ``_split_cells`` calls (one instance is built once per
    ``_compute_strategy_comparison_report`` call and threaded into both), so the whole run's
    ``backtests_done``/``backtests_from_cache`` counts up monotonically across splits rather than
    resetting when the SECOND ``_split_cells`` call starts. Each sink call carries an ``"event"``
    key (``"total"``/``"pair_started"``/``"pair_done"``) so a consumer (the CLI printer, the compute
    manager) can distinguish a start-of-run announcement from a per-pair update; the manager strips
    the key before merging (the served snapshot's ``progress`` sub-dict never carries it — see
    ``edge_report_compute.py``)."""

    def __init__(self, sink, total: int) -> None:
        self._sink = sink
        self._done = 0
        self._from_cache = 0
        self._sink({
            "event": "total", "phase": "backtests", "backtests_total": total,
            "backtests_done": 0, "backtests_from_cache": 0, "current": None,
        })

    def start_pair(self, dataset_id: str, strategy_id: str) -> None:
        self._sink({
            "event": "pair_started",
            "current": {"dataset_id": dataset_id, "strategy_id": strategy_id},
        })

    def note_cache_hit(self) -> None:
        """era-fast_wall J-05: bumps the running from-cache count WITHOUT emitting a sink patch of
        its own. Called by the caching ``run_pair`` closure (``_build_caching_run_pair``, below)
        the INSTANT it serves a sub-cache hit -- strictly BEFORE this pair's own ``pair_done()``
        (UNCHANGED) fires. ``pair_done()``'s EXISTING patch already reads ``self._from_cache``, so
        this single additive method is enough to make ``backtests_from_cache`` genuinely increment
        without widening ``run_pair``'s own 2-arg-in/1-dict-out shape (the NOTES' own
        implementation hint)."""
        self._from_cache += 1

    def pair_done(self) -> None:
        self._done += 1
        self._sink({
            "event": "pair_done", "backtests_done": self._done,
            "backtests_from_cache": self._from_cache, "current": None,
        })


def _split_cells(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    bar_store: BarStore,
    datasets: list[dict],
    events: list[dict],
    config: Config,
    *,
    reporter: "_ProgressReporter | None" = None,
    should_abort=None,
    run_pair=None,
) -> list[dict]:
    """One split's (train or hold-out) cells: for every dataset that resolves an owning event with
    a genuinely inherited class (an unclassified ``class: null`` band is honestly excluded — there
    is no A/B/C to report a cell under), run ALL THREE registered strategies over it and pool their
    trades (and null-baseline trades) into the matching (strategy, class, side, reaction, feed)
    cell. Trades from MULTIPLE datasets sharing a cell are ordered by their reconstructed REAL UTC
    entry instant (``dataset["epoch_anchor"] + trade["entry"]["logical_ts"]`` — the identical
    reconstruction ``setups.py``'s own tape-timeline join and ``serializers.serialize_history``
    already use) before the ONE shared ``_aggregate`` call, so a pooled cell's ``win_rate``/
    ``max_drawdown_r`` reflect a genuine chronological trade sequence — never scan-order/dataset-id
    happenstance (max_drawdown_r is peak-to-trough IN TRADE ORDER; summing already-aggregated
    numbers cannot recover that without the raw, correctly-ordered trade list).

    era-fast_wall J-04: ``reporter``/``should_abort`` (both optional, default ``None`` — the exact
    pre-J-04 loop when omitted) are additions to this loop's body — the pooling/ordering/
    aggregation code below is byte-for-byte untouched. ``should_abort`` (a zero-arg callable) is
    checked ONCE per pair, strictly BEFORE that pair's backtest call — cooperative
    cancellation observed BETWEEN dataset x strategy pairs, never mid-backtest — and raises
    ``EdgeReportComputeCancelled`` the instant it returns ``True``, so an already-completed pair's
    trades are never discarded and a not-yet-started pair never begins.

    era-fast_wall J-05: ``run_pair`` (optional, default ``None`` — the EXACT pre-J-05 inline
    ``_run_backtest`` call when omitted, so this stays BYTE-IDENTICAL to before whenever a caller
    does not supply one) is a ``(dataset_meta, strategy_id) -> dict`` callable (the SAME return
    shape ``_run_backtest`` itself returns) built by ``_build_caching_run_pair`` whenever a
    ``sub_cache`` is threaded in from ``_compute_strategy_comparison_report``. This is the ONLY
    other change to this loop's body — a cache hit notifies ``reporter`` from INSIDE that closure
    (see ``_ProgressReporter.note_cache_hit``), so this call site's own ``reporter.pair_done()``
    below stays textually unchanged."""
    pools: dict[tuple, dict] = {}
    for dataset_meta in datasets:
        event = _dataset_event(dataset_meta, events)
        if event is None or event["band"]["class"] is None:
            continue
        feed = dataset_meta["data_feed"]
        for strategy_id in _ALL_STRATEGY_IDS:
            if should_abort is not None and should_abort():
                raise EdgeReportComputeCancelled()
            if reporter is not None:
                reporter.start_pair(dataset_meta["id"], strategy_id)
            if run_pair is not None:
                result = run_pair(dataset_meta, strategy_id)
            else:
                result = _run_backtest(
                    jobs, store, dataset_store, dataset_meta["id"],
                    strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
                )
            if reporter is not None:
                reporter.pair_done()
            key = (strategy_id, event["band"]["class"], event["band"]["side"], event["reaction"], feed)
            pool = pools.setdefault(key, {"trades": [], "null_trades": [], "dataset_ids": []})
            anchor = dataset_meta.get("epoch_anchor") or 0.0
            pool["trades"].extend(
                (anchor + t["entry"]["logical_ts"], t) for t in result["trades"]
            )
            pool["null_trades"].extend(
                (anchor + t["entry"]["logical_ts"], t) for t in result["null_baseline"]["trades"]
            )
            pool["dataset_ids"].append(dataset_meta["id"])

    cells: list[dict] = []
    for (strategy_id, band_class, band_side, reaction, feed), pool in pools.items():
        ordered_trades = [t for _, t in sorted(pool["trades"], key=lambda pair: pair[0])]
        ordered_null = [t for _, t in sorted(pool["null_trades"], key=lambda pair: pair[0])]
        measurement = _aggregate(ordered_trades)
        cells.append({
            "strategy_id": strategy_id,
            "band_class": band_class,
            "band_side": band_side,
            "reaction": reaction,
            "feed": feed,
            "dataset_ids": sorted(pool["dataset_ids"]),
            "measurement": measurement,
            "null_baseline": _aggregate(ordered_null),
            "insufficient_sample": measurement["n"] < config.pnl_min_sample_size,
        })
    cells.sort(key=_cell_key)
    return cells


# --- era-fast_wall J-05: the resumable sub-cache's run_pair provider + the CLI-only parallel
# pre-warm. See ``EdgeReportBacktestCache``'s own module docstring for the durable cache's
# discipline; the functions below are the ONLY code that ever keys/consults it. -----------------


def _build_caching_run_pair(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    bar_store: BarStore,
    config: Config,
    sub_cache: EdgeReportBacktestCache,
    reporter: "_ProgressReporter | None",
):
    """Builds the caching ``run_pair(dataset_meta, strategy_id)`` closure ``_split_cells`` calls in
    place of its inline ``_run_backtest`` when a ``sub_cache`` is supplied. Every key component
    that is constant across the WHOLE sweep (``bar_store_signature``, ``config_fingerprint``,
    ``config_content_hash``, ``strategy_registry``) is computed EXACTLY ONCE here, outside the pair
    loop, and closed over — never once per pair (the exact wasteful-recomputation pattern this
    whole interlude exists to remove; the NOTES' own implementation hint). A cache hit notifies
    ``reporter`` (if any) via ``note_cache_hit()`` BEFORE returning, so the caller's UNCHANGED
    ``reporter.pair_done()`` call picks up the incremented ``backtests_from_cache`` count — without
    widening ``run_pair``'s own 2-arg-in/1-dict-out return shape. A cache MISS runs the SAME
    ``_run_backtest`` every uncached caller uses (single source of truth) and publishes the result
    — ``EdgeReportBacktestCache.publish`` itself swallows a persistence failure (see its own
    docstring), so a sub-cache write hiccup never blocks this pair's already-computed result from
    being returned and pooled normally."""
    bar_store_signature = _store_signature(bar_store)
    config_fingerprint = config.config_fingerprint()
    config_content_hash = _config_content_hash(config)
    strategy_registry = config.strategy_registry()

    def run_pair(dataset_meta: dict, strategy_id: str) -> dict:
        key = pair_cache_key(
            dataset_id=dataset_meta["id"],
            dataset_checksum=dataset_meta["checksum"],
            strategy_id=strategy_id,
            profile=PROFILE_DEFAULT,
            config_fingerprint=config_fingerprint,
            config_content_hash=config_content_hash,
            strategy_registry=strategy_registry,
            bar_store_signature=bar_store_signature,
        )
        cached = sub_cache.lookup(key)
        if cached is not None:
            if reporter is not None:
                reporter.note_cache_hit()
            return cached
        result = _run_backtest(
            jobs, store, dataset_store, dataset_meta["id"],
            strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
        )
        sub_cache.publish(key, result)
        return result

    return run_pair


def _eligible_datasets(dataset_store: DatasetStore, bar_store: BarStore, config: Config) -> list[dict]:
    """Every registered dataset (both splits, combined) that resolves an owning, classified scan
    event — the IDENTICAL eligibility test ``_split_cells``'s own loop applies per pair, reused
    here to determine the parallel pre-warm's task set BEFORE any worker process starts (never a
    second eligibility rule)."""
    records = _verified_records(dataset_store)
    events = compute_setups(bar_store, config)["events"] if records else []
    return [
        r for r in records
        if (lambda e: e is not None and e["band"]["class"] is not None)(_dataset_event(r, events))
    ]


def _run_dataset_pairs_in_worker(
    *,
    dataset_id: str,
    dataset_dir: str,
    bar_dir: str,
    sub_cache_db_path: str,
    config: Config,
    profile: str,
    bar_store_signature: tuple,
    config_fingerprint: str,
    config_content_hash: str,
    strategy_registry: list[dict],
) -> dict:
    """era-fast_wall J-05 — ONE ``ProcessPoolExecutor`` task: runs ALL THREE registered strategies'
    backtests for ONE dataset in a FRESH worker process. Builds its own ``DatasetStore``/
    ``BarStore`` from the EXPLICIT paths given (never a shared object across the process boundary —
    these cannot be usefully pickled anyway) and its own THROWAWAY temp ``JournalStore`` for job
    bookkeeping ONLY (discarded on return; the report never references backtest ids — goal.md's own
    wording). Publishes each completed pair to the durable ``sub_cache`` (a FRESH connection —
    SQLite/WAL tolerates many concurrent writer processes) the INSTANT it finishes, and SKIPS any
    pair the cache already holds (so a resumed sweep — e.g. re-running the CLI after a prior
    partial parallel run — never redoes already-published work even inside the parallel path
    itself). MUST be a MODULE-LEVEL function (picklable by reference) for the ``spawn`` context.
    Returns ``{"dataset_id", "pid"}`` — bookkeeping/test-observability ONLY; the actual report is
    reassembled by the orchestrator afterward via the untouched sequential ``_split_cells``/
    ``run_pair`` sub-cache-hit path."""
    with tempfile.TemporaryDirectory(prefix="edge-report-sweep-worker-") as tmp_dir:
        store = JournalStore(os.path.join(tmp_dir, "journal.db"), config)
        try:
            dataset_store = DatasetStore(dataset_dir)
            bar_store = BarStore(bar_dir)
            # era-fast_wall follow-up: this worker's task is ONE dataset x all three strategies —
            # the one-slot replay reuse replays it once (see BacktestRunner's contract).
            jobs = BacktestJobManager(store, config, reuse_replay_path=True)
            sub_cache = EdgeReportBacktestCache(sub_cache_db_path)
            dataset_meta = dataset_store.get(dataset_id)
            for strategy_id in _ALL_STRATEGY_IDS:
                key = pair_cache_key(
                    dataset_id=dataset_meta["id"],
                    dataset_checksum=dataset_meta["checksum"],
                    strategy_id=strategy_id,
                    profile=profile,
                    config_fingerprint=config_fingerprint,
                    config_content_hash=config_content_hash,
                    strategy_registry=strategy_registry,
                    bar_store_signature=bar_store_signature,
                )
                if sub_cache.lookup(key) is not None:
                    continue  # already durable -- resumable even inside the parallel path itself
                result = _run_backtest(
                    jobs, store, dataset_store, dataset_meta["id"],
                    strategy_id=strategy_id, profile=profile, bar_store=bar_store,
                )
                sub_cache.publish(key, result)
        finally:
            store.close()
    return {"dataset_id": dataset_id, "pid": os.getpid()}


def _parallel_prewarm_sub_cache(
    dataset_store: DatasetStore,
    bar_store: BarStore,
    config: Config,
    *,
    sub_cache: EdgeReportBacktestCache,
    workers: int,
    should_abort=None,
) -> list[dict]:
    """era-fast_wall J-05 — CLI-ONLY parallel pre-warm (see ``EdgeReportComputeManager.trigger``'s
    own ``workers<=1`` guard/test — this branch is never reachable from a request thread in this
    iteration's shipped callers; ``run_strategy_comparison_report``'s own ``compute()`` dispatch is
    the ONLY call site). Determines the ELIGIBLE (dataset, all 3 strategies) task set with the SAME
    eligibility test ``_split_cells`` itself uses (``_eligible_datasets``, above), schedules
    eligible datasets LARGEST-FIRST (LPT) by their own recorded ``event_counts.total``, and runs
    them across ``workers`` worker PROCESSES (``ProcessPoolExecutor``, ``spawn`` context) — task =
    ONE dataset (its three strategies) each, so peak memory is bounded to ~one parsed dataset per
    worker. Each worker builds its OWN stores from EXPLICIT paths — derived here from
    ``config.dataset_dir_resolved()``/``bar_store.root`` (the CLI's own construction invariant:
    this path is CLI-only, and the CLI's ``dataset_store``/``bar_store`` are ALWAYS built from
    exactly those resolved paths — see ``edge_report_compute.main``) — and a THROWAWAY temp journal
    DB for job bookkeeping, publishing each completed pair to the durable ``sub_cache`` the INSTANT
    it finishes. Returns the raw per-task ``{"dataset_id", "pid"}`` results (bookkeeping/test-
    observability only) — the caller (``run_strategy_comparison_report``) reassembles the ACTUAL
    report afterward through the UNTOUCHED sequential ``_split_cells``/``run_pair`` sub-cache-hit
    path, byte-identical to a fresh sequential run BY CONSTRUCTION (the pooling/aggregation code
    never changed). A registry with ZERO eligible pairs never spins up a process pool at all
    (returns ``[]`` immediately) — no wasted worker-startup cost for nothing to do. Cooperative
    cancellation (``should_abort``) is checked before EACH new task submission — an already-
    in-flight task always finishes and persists its own pairs (goal.md's own wording)."""
    eligible = _eligible_datasets(dataset_store, bar_store, config)
    if not eligible:
        return []
    eligible.sort(key=lambda r: r["event_counts"]["total"], reverse=True)  # LPT: largest first

    bar_store_signature = _store_signature(bar_store)
    config_fingerprint = config.config_fingerprint()
    config_content_hash = _config_content_hash(config)
    strategy_registry = config.strategy_registry()
    dataset_dir = config.dataset_dir_resolved()
    bar_dir = str(bar_store.root)

    results: list[dict] = []
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=max(1, workers), mp_context=ctx) as executor:
        futures: dict = {}
        for dataset_meta in eligible:
            if should_abort is not None and should_abort():
                break  # stop SUBMITTING -- already-submitted futures below still finish/persist
            future = executor.submit(
                _run_dataset_pairs_in_worker,
                dataset_id=dataset_meta["id"], dataset_dir=dataset_dir, bar_dir=bar_dir,
                sub_cache_db_path=sub_cache.db_path, config=config, profile=PROFILE_DEFAULT,
                bar_store_signature=bar_store_signature, config_fingerprint=config_fingerprint,
                config_content_hash=config_content_hash, strategy_registry=strategy_registry,
            )
            futures[future] = dataset_meta["id"]
        for future in as_completed(futures):
            results.append(future.result())
    return results


def _cell_beats_null(cell: dict) -> bool:
    """"Beats its own null baseline" — the ``_beats_null`` gate, applied to a strategy-comparison
    CELL instead of a per-dataset champion row (a genuine twin, not a re-derived formula: BOTH net
    R AND net $ must exceed the cell's own seeded null baseline)."""
    return (
        cell["measurement"]["net_r"] > cell["null_baseline"]["net_r"]
        and cell["measurement"]["net_usd"] > cell["null_baseline"]["net_usd"]
    )


def _cell_clears_gate(cell: dict, config: Config) -> bool:
    """The identical ``_is_positive_edge`` four-part gate (positive net R AND net $, at least
    ``Config.pnl_min_sample_size``, and beating the cell's own null baseline), applied to a
    strategy-comparison cell. Used ONLY to rank/annotate a cell in the informational
    ``surviving_train_cells`` list below — this module promotes nothing (see the module docstring);
    the champion moves ONLY through the existing sweep gate on hold-out data."""
    m = cell["measurement"]
    return (
        m["net_r"] > 0
        and m["net_usd"] > 0
        and m["n"] >= config.pnl_min_sample_size
        and _cell_beats_null(cell)
    )


def _surviving_train_cells(
    train_cells: list[dict], holdout_cells: list[dict], config: Config
) -> list[dict]:
    """A ranked, informational list of TRAIN cells that clear the positivity gate, each carrying
    its OWN matching hold-out cell's status (an honest ``holdout_cell: None`` /
    ``holdout_positive_edge: False`` when no hold-out data exists yet for that exact key — never a
    fabricated verdict). Ranked by the train cell's OWN net R (descending), tie-broken by its full
    identity key — the ``_rank`` pattern, applied to cells."""
    holdout_by_key = {_cell_key(c): c for c in holdout_cells}
    survivors: list[dict] = []
    for cell in train_cells:
        if not _cell_clears_gate(cell, config):
            continue
        holdout_cell = holdout_by_key.get(_cell_key(cell))
        survivors.append({
            "train_cell": cell,
            "holdout_cell": holdout_cell,
            "holdout_positive_edge": holdout_cell is not None and _cell_clears_gate(holdout_cell, config),
        })
    survivors.sort(
        key=lambda s: (-s["train_cell"]["measurement"]["net_r"], _cell_key(s["train_cell"]))
    )
    return survivors


def run_strategy_comparison_report(
    store: JournalStore,
    dataset_store: DatasetStore,
    bar_store: BarStore,
    config: Config,
    *,
    cache: EdgeReportCache | None = None,
    force: bool = False,
    progress=None,
    should_abort=None,
    sub_cache: "EdgeReportBacktestCache | None" = None,
    workers: int | None = None,
) -> dict:
    """The always-recompute-or-serve-through-a-cache entry point for the 3-way strategy-comparison
    report (era-5B J-04). See ``_compute_strategy_comparison_report`` below for the full algorithm
    docstring — this function is a thin dispatcher over that ONE computation, never a second copy
    of it.

    era-fast_wall J-01: ``GET /research/edge-report`` calls ``peek_strategy_comparison_report``
    (below) instead of this function — ``peek_...`` NEVER computes on a cold cache key. This
    function remains the module's ONE optionally-cached compute dispatcher: every direct test in
    ``tests/test_edge_report.py`` still exercises it unmodified, and it is the exact shape
    ``EdgeReportCache.compute_and_publish``'s future operator/CLI "force" callers (J-04) wrap.

    era-5B J-08: ``cache`` is an OPTIONAL rebuildable result cache
    (``edge_report_cache.EdgeReportCache``). ``cache=None`` (the default) is the EXACT pre-J-08
    behaviour — always calls ``_compute_strategy_comparison_report`` directly, byte-for-byte
    identical to before — so every EXISTING call site (every test in ``test_edge_report.py``, and
    any future caller with no cache to offer) is untouched and stays uncached. When a cache IS
    supplied, this function serves ``_compute_strategy_comparison_report``'s output VERBATIM
    through it: the cache never re-derives a cell, a measurement, or a null baseline — a miss
    recomputes byte-identically through the SAME one function below (single source of truth; no
    second computation path, anywhere).

    era-fast_wall J-04: five ADDITIVE keyword-only params for the operator-run compute
    (``edge_report_compute.EdgeReportComputeManager`` and its CLI warmer are the first genuine
    callers) — every default reproduces this function's EXACT pre-J-04 behaviour:

      * ``force`` (default ``False``) — ``False`` keeps dispatching through ``cache.
        get_or_compute`` exactly as today; ``True`` dispatches through the ALREADY-SHIPPED
        ``cache.compute_and_publish`` (J-01) instead, always recomputing and republishing even
        over a warm key. Irrelevant when ``cache is None`` (there is nothing to force through).
      * ``progress``/``should_abort`` thread straight down to ``_split_cells``'s existing
        per-dataset x strategy loop (see that function's own docstring) as an optional
        reporting/cooperative-cancellation seam — the loop's own ordering/pooling/aggregation
        code is untouched. A ``should_abort`` that fires raises ``EdgeReportComputeCancelled``,
        which propagates UNCHANGED through ``cache.get_or_compute``/``compute_and_publish``
        (both publish ONLY after ``compute_fn`` returns normally) — a cancelled run publishes
        NOTHING, by construction, with zero change to either cache method's body.
      * ``sub_cache`` (era-fast_wall J-05, real effect now — see ``_build_caching_run_pair``):
        the durable per-(dataset x strategy)-pair ``EdgeReportBacktestCache``. Threaded straight
        into ``_compute_strategy_comparison_report`` so every backtest pair is served/published
        through it — a killed-and-retriggered sweep with the SAME ``sub_cache`` skips every
        already-published pair (resumable).
      * ``workers`` (era-fast_wall J-05, real effect now): when ``sub_cache`` is ALSO supplied and
        ``workers`` resolves to more than one, this function FIRST pre-warms ``sub_cache`` via
        ``_parallel_prewarm_sub_cache`` (a ``ProcessPoolExecutor``, CLI-only — see that function's
        own docstring for why this is safe to call from ANY caller: the manager's own ``trigger()``
        never supplies ``workers > 1``, a logged, tested assumption) BEFORE calling
        ``_compute_strategy_comparison_report`` — which then finds every eligible pair already
        cached and simply reassembles the report sequentially, byte-identical to a wholly
        sequential run BY CONSTRUCTION (the pooling/aggregation code never changed). ``workers in
        (None, 0, 1)`` (the default, and every caller before this iteration) skips the pre-warm
        entirely — byte-identical to the pre-J-05 body."""

    def compute() -> dict:
        if sub_cache is not None and workers is not None and workers > 1:
            _parallel_prewarm_sub_cache(
                dataset_store, bar_store, config,
                sub_cache=sub_cache, workers=workers, should_abort=should_abort,
            )
        return _compute_strategy_comparison_report(
            store, dataset_store, bar_store, config,
            progress=progress, should_abort=should_abort, sub_cache=sub_cache,
        )

    if cache is None:
        return compute()
    if force:
        return cache.compute_and_publish(dataset_store, config, compute)
    return cache.get_or_compute(dataset_store, config, compute)


def peek_strategy_comparison_report(
    store: JournalStore,
    dataset_store: DatasetStore,
    bar_store: BarStore,
    config: Config,
    *,
    cache: EdgeReportCache,
    compute=None,
) -> dict:
    """The GET-path's EXCLUSIVE entry point (era-fast_wall J-01) — ``routes.get_edge_report`` calls
    ONLY this, never ``run_strategy_comparison_report``, so opening ``/structure`` (or any GET, or
    the MCP ``edge_report`` proxy) can NEVER start the sweep (the interlude's headline CRITICAL
    anti-goal — "no compute on page load, operator-run only"). Three branches:

      * A store-integrity failure raises ``EdgeReportError`` exactly as today (``_verified_
        records``, above) — the route's existing explicit 500; the cache is never even keyed.
      * An EMPTY dataset registry still computes inline — the pre-J-01 O(1), zero-backtest shape
        (``_compute_strategy_comparison_report`` skips the whole scan/backtest path when both
        splits are empty; see that function's own docstring) — the response carries no ``status``
        key, byte-identical to before J-01 shipped.
      * A NON-EMPTY registry consults the cache's READ-ONLY ``lookup`` — NEVER ``get_or_compute``
        or ``compute_and_publish`` (pinned by ``tests/test_edge_report.py``'s ``test_peek_source_
        never_calls_a_compute_triggering_cache_method``): a warm key returns the cached report
        VERBATIM; a cold key returns the honest not-computed payload (``status: "not_computed"``,
        the canonical ``EDGE_REPORT_NOT_COMPUTED_DETAIL``, ``dataset_count``, ``register`` read
        from ``backtests.REGISTER`` — never a restated literal — and ``compute``).

    era-fast_wall J-04: ``compute`` (optional, default ``None`` — the EXACT J-01 placeholder every
    existing caller still gets) is embedded VERBATIM as the payload's own ``compute`` field — this
    function never re-derives or inspects it. The caller (``routes.get_edge_report``) passes
    ``registry.edge_report_compute.snapshot()`` — the SAME snapshot ``GET /research/edge-report/
    compute`` itself serves, so the two are byte-identical in shape by construction (one owner, one
    read, two callers)."""
    records = _verified_records(dataset_store)
    if not records:
        return _compute_strategy_comparison_report(store, dataset_store, bar_store, config)
    cached = cache.lookup(records, config)
    if cached is not None:
        return cached
    return {
        "status": "not_computed",
        "detail": EDGE_REPORT_NOT_COMPUTED_DETAIL,
        "dataset_count": len(records),
        "register": REGISTER,
        "compute": compute,
    }


def _compute_strategy_comparison_report(
    store: JournalStore,
    dataset_store: DatasetStore,
    bar_store: BarStore,
    config: Config,
    *,
    progress=None,
    should_abort=None,
    sub_cache: "EdgeReportBacktestCache | None" = None,
) -> dict:
    """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; renamed from
    ``run_strategy_comparison_report`` at era-5B J-08 — see that function's own docstring for why:
    this is the byte-identical pure-compute body, now wrapped by an optional cache rather than
    called directly). Measures ``v1``, ``structure_tape``, and ``structure_tape_map`` over EVERY
    registered event-window dataset that resolves an owning, classified scan event, aggregated
    into per strategy x class x side x reaction x feed cells. Raises ``EdgeReportError`` for a
    dishonest state (the identical ``_split_datasets`` integrity discipline ``run_edge_report``
    uses) — nothing is written by the CALLER in that case. Strictly read-only: promotes nothing,
    appends no ledger row, moves no champion pointer (see the module docstring).

    era-fast_wall J-04: ``progress``/``should_abort`` (both optional, default ``None`` — the exact
    pre-J-04 body when omitted) thread into BOTH ``_split_cells`` calls below through ONE shared
    ``_ProgressReporter`` (never a separate reporter per split — its running totals must span both
    splits). ``backtests_total`` is sized ONCE, right after ``events`` resolves (the earliest point
    both splits' eligible-pair counts are knowable), via ``_count_eligible_pairs`` — never inside
    ``_split_cells`` itself, so that function's own loop stays untouched.

    era-fast_wall J-05: ``sub_cache`` (optional, default ``None`` — byte-identical to the pre-J-05
    body when omitted) is the durable per-pair ``EdgeReportBacktestCache``. When supplied, ONE
    caching ``run_pair`` provider (``_build_caching_run_pair``) is built HERE — after ``reporter``
    resolves, so a cache hit can notify it — and threaded into BOTH the train and hold-out
    ``_split_cells`` calls below: the SAME provider/cache instance serves both splits (goal.md's
    own wording), never a second cache/provider per split.

    ``reuse_replay_path=True`` (era-fast_wall follow-up): this report's OWN short-lived manager
    replays each dataset ONCE and reuses the deterministic path across its three per-strategy
    backtests (``_split_cells`` iterates dataset-outer/strategy-inner — see
    ``BacktestRunner``'s one-slot contract; byte-identical persisted reports, two of three
    full-engine replays removed)."""
    jobs = BacktestJobManager(store, config, reuse_replay_path=True)
    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)

    # ONE ``compute_setups`` call for the WHOLE report (audit B2 hot-path guard) — never per
    # dataset, never per split; reused for both the train and hold-out join below. Skipped
    # entirely when the registry is empty (nothing to join against), so the empty-registry case
    # never pays for a full panel scan at all.
    events: list[dict] = []
    if train_datasets or holdout_datasets:
        events = compute_setups(bar_store, config)["events"]

    reporter = None
    if progress is not None:
        total = _count_eligible_pairs(train_datasets, events) + _count_eligible_pairs(holdout_datasets, events)
        reporter = _ProgressReporter(progress, total)

    run_pair = None
    if sub_cache is not None:
        run_pair = _build_caching_run_pair(jobs, store, dataset_store, bar_store, config, sub_cache, reporter)

    train_cells = _split_cells(
        jobs, store, dataset_store, bar_store, train_datasets, events, config,
        reporter=reporter, should_abort=should_abort, run_pair=run_pair,
    )
    holdout_cells = _split_cells(
        jobs, store, dataset_store, bar_store, holdout_datasets, events, config,
        reporter=reporter, should_abort=should_abort, run_pair=run_pair,
    )

    return {
        "register": REGISTER,
        "pnl_min_sample_size": config.pnl_min_sample_size,
        "train": {"cells": train_cells},
        "holdout": {"cells": holdout_cells},
        "surviving_train_cells": _surviving_train_cells(train_cells, holdout_cells, config),
    }


def _render_report(report: dict) -> str:
    """Pure, deterministic JSON render (sorted keys — the ``pnl_scan._render_report`` /
    ``datasets.py`` ``_canonical`` precedent): identical ``report`` dicts always render identical
    bytes, and the report itself never carries a wall-clock or per-run-random field (see the
    module docstring), so two independent fresh-state runs of an identical scenario produce
    byte-identical ``--out`` files."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main() -> int:
    """The CLI entry: measure against the operator's journal DB + dataset dir (the SAME
    ``TAPEOLOGY_JOURNAL_DB`` / ``TAPEOLOGY_DATASET_DIR`` resolution seams the backend and every
    other era-3 CLI read), writing the report to ``--out``. An empty registry or zero qualifying
    datasets is an honest, exit-0 outcome; an ``EdgeReportError`` prints an explicit message to
    stderr and exits 1 with NOTHING written."""
    parser = argparse.ArgumentParser(
        description="J-09 baseline-edge report — rank the frozen champion's simulated hold-out "
        "edge per registered dataset, honestly."
    )
    parser.add_argument("--out", required=True, help="path to write the edge report JSON")
    args = parser.parse_args()

    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        dataset_store = DatasetStore(config.dataset_dir_resolved())
        try:
            report = run_edge_report(store, dataset_store, config)
        except EdgeReportError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        store.close()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render_report(report), encoding="utf-8")

    n_train = len(report["train"]["datasets"])
    n_holdout = len(report["holdout"]["datasets"])
    print(
        f"edge report complete: {n_train} train / {n_holdout} hold-out dataset(s) measured "
        f"against champion {report['champion']}; {report['finding']}; report written to {out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
