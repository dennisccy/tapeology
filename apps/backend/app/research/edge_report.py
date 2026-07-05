"""The baseline-edge report (era-3 capability 9 groundwork, J-09) —
``python -m app.research.edge_report --out <path>``.

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
import sys
from pathlib import Path

from ..config import CONFIG, Config
from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from .store import JournalStore

__all__ = ["EdgeReportError", "run_edge_report", "main"]

# The exact, honest empty finding (DoD-mandated literal string) — emitted whenever zero hold-out
# datasets clear the positive-edge gate, including the true-empty-registry case.
NO_POSITIVE_EDGE_FINDING = "no positive-edge dataset"


class EdgeReportError(Exception):
    """The report could not complete honestly — a dataset failed integrity verification or a
    backtest ended non-``done``. Explicit; nothing is written to ``--out``."""


# --- reused computation: ONE backtest per dataset, via the EXISTING runner ----------------------


def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
    """Every registered dataset metadata row for ``split`` (checksum-verified on load, the ONE
    ``DatasetStore.list`` read). A file that fails integrity verification anywhere in the store
    aborts the whole report explicitly — a partial report is a misleading report."""
    records, errors = dataset_store.list()
    if errors:
        raise EdgeReportError(
            f"{len(errors)} dataset file(s) failed integrity verification "
            f"({[e['file'] for e in errors]}) — the report stops with nothing written"
        )
    return [r for r in records if r["split"] == split]


def _run_backtest(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    dataset_id: str,
    *,
    strategy_id: str,
    profile: str,
) -> dict:
    """Run ONE backtest synchronously through the EXISTING public job API (the
    ``pnl_scan._run_backtest`` pattern) and return its persisted ``result`` block — refusing
    explicitly unless it completed ``done`` (a failed/cancelled report carries no served
    aggregates, so nothing could be honestly measured from it)."""
    payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
    jobs.run_sync(payload["id"], dataset_store=dataset_store)
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
