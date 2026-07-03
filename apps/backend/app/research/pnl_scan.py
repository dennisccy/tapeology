"""The candidate-sweep harness (era-3 capability 7, J-07) —
``python -m app.research.pnl_scan --out <path>``.

THE single computer of Data Contract row 36 (scan reports): evaluate every registered candidate
profile against the CURRENT persisted champion (strategy held constant at the champion's
``strategy_id``; only ``profile`` varies) over every registered TRAIN dataset, then validate
apparent winners on every registered HOLD-OUT dataset — reusing ``BacktestJobManager`` /
``BacktestRunner`` (``app/research/backtests.py``) as the ONE computation path, EXACTLY as
``app/research/pnl_baseline.py`` already does (``jobs.create(...)`` + ``jobs.run_sync(...)``).
Only for a genuine hold-out survivor does it promote: append exactly ONE PnL-ledger row via the
EXISTING single writer (``pnl_ledger.append_validation_row``) and move the ONE persisted champion
pointer (``JournalStore.set_champion_pointer`` — this module is its ONE caller, source-scan-guard-
enforced). Zero candidates or zero survivors is an honest, exit-0 outcome; a corrupt dataset or an
unavailable store is an explicit, distinct, non-zero-exit failure with NOTHING written or promoted.

Disciplines, clause by clause:

  * **No second computation path.** Every backtest this module runs goes through the SAME
    ``BacktestJobManager.create`` + ``run_sync`` the J-03 route and the J-04 founding-baseline CLI
    use. This module never touches a dataset file, an engine, or a trade/fill/R arithmetic
    directly — it only reads persisted backtest ``aggregates`` (row 31) verbatim and computes
    DELTAS over them (candidate minus champion), never a second PnL computation.

  * **Candidate enumeration reads the ONE registry.** ``Config.profile_registry()`` — the SAME
    registry ``GET /research/profiles`` and the backtest route's validation consult — filtered to
    entries where ``is_default`` is ``False`` (``default`` is never itself a candidate, per the
    goal glossary). Zero registered candidates is an honest empty sweep, never an error.

  * **Champion computed ONCE per dataset, shared across every candidate.** The champion's
    backtest on a given dataset does not depend on which candidate is being evaluated, so it is
    computed exactly once per dataset (not once per candidate x dataset) — efficiency, not a
    second path: it is still the SAME ``BacktestJobManager`` call every candidate's comparison
    reads.

  * **Never pooled across splits; every candidate gets full figures regardless of outcome.**
    Train and hold-out aggregates are two separate value pairs (never summed together); EVERY
    candidate's report entry carries both splits' full breakdown whether it survives or not — the
    hold-out check VALIDATES an apparent train winner, it does not gate whether hold-out is even
    computed and reported.

  * **The promotion gate, precisely.** For a candidate: ``train_positive`` = the SUM of per-
    train-dataset deltas (net R AND net $) is positive; ``robust`` = EVERY individual train
    dataset's delta is positive (both R and $) — else ``speculative``; ``survivor`` = the SUMMED
    hold-out delta is positive (both R and $) AND the summed hold-out candidate ``n`` is at least
    ``Config.promotion_min_sample_size``; ``overfit`` = ``train_positive`` and NOT ``survivor``
    (the phase spec's own definition: "positive train, failing the hold-out gate" — a candidate
    that never looked good on train is honestly just a non-survivor, never mislabeled overfit).
    ``robust``/``overfit`` are independent axes (a candidate can be robust on train yet still
    overfit relative to hold-out).

  * **Promotion is two writes, ordered so a crash never hides itself.** A survivor promotion
    FIRST appends the PnL-ledger row (the existing single writer,
    ``pnl_ledger.append_validation_row`` — durable once committed), THEN moves the champion
    pointer. If the process crashes between the two writes, the ledger row survives but the
    pointer does not move; a RE-RUN evaluates the SAME candidate against the SAME (unmoved)
    champion, finds it a survivor again, and attempts to re-promote — hitting the ledger's
    existing ``DuplicateEnhancementError`` structural refusal, which this module surfaces as an
    explicit ``ScanError`` naming the inconsistency rather than silently retrying or dropping it.
    (The REVERSE order — pointer first — would let a crash leave a PERMANENTLY silent orphan: once
    the pointer has moved, a re-run compares the candidate to ITSELF and never flags the missing
    ledger row again.) Automatic promotion requires EXACTLY one train and one hold-out dataset
    registered (``append_validation_row``'s structural shape — reused verbatim, never modified);
    with more of either registered, the SCAN still fully evaluates and reports every dataset, but
    promotion is explicitly skipped with an honest note rather than an arbitrary guess at which
    pair to cite.

  * **Deterministic; never a second promotion this run.** Every backtest uses the config-owned
    null-baseline seed (never a random one). At most ONE candidate is promoted per invocation —
    the first hold-out survivor encountered in registry order (today's registry has exactly one
    candidate, so this tie-break is currently unreachable; it is documented here for the day a
    second candidate is registered). The written report never contains a wall-clock field or a
    freshly-minted backtest-report id (both are per-run-random / time-varying), so two independent
    fresh-state runs of an IDENTICAL non-promoting scenario produce byte-identical ``--out`` bytes.

  * **Honest failure states.** A dataset file that fails its integrity check anywhere in the
    store aborts the WHOLE sweep with an explicit ``ScanError`` before anything is written — a
    partial report is a misleading report. A backtest that ends anything other than ``done``
    (e.g. a corrupt dataset caught at replay time) is the same explicit refusal. No trade, fill,
    dataset, or PnL figure is ever synthesized to force a result either way.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ..config import CONFIG, Config
from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from .pnl_ledger import LedgerCompositionError, append_validation_row
from .store import DuplicateEnhancementError, JournalStore

__all__ = ["ScanError", "run_sweep", "main"]


class ScanError(Exception):
    """The sweep could not complete honestly — a dataset failed integrity verification, a
    backtest ended non-``done``, or a mid-promotion inconsistency was detected on retry. Explicit;
    nothing is written to ``--out`` and nothing is promoted."""


# --- reused computation: ONE backtest per (dataset, strategy, profile), via the EXISTING runner ----


def _run_backtest(
    jobs: BacktestJobManager,
    store: JournalStore,
    dataset_store: DatasetStore,
    dataset_id: str,
    *,
    strategy_id: str,
    profile: str,
) -> tuple[str, dict]:
    """Run ONE backtest synchronously through the EXISTING public job API (the
    ``pnl_baseline._run_backtest`` pattern) and return ``(report_id, result_block)`` — refusing
    explicitly unless it completed ``done`` (a failed/cancelled report carries no served
    aggregates, so nothing could be honestly compared against it)."""
    payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
    jobs.run_sync(payload["id"], dataset_store=dataset_store)
    final = store.get_backtest(payload["id"]).payload
    if final.get("status") != STATUS_DONE:
        raise ScanError(
            f"backtest '{payload['id']}' over dataset '{dataset_id}' (strategy={strategy_id}, "
            f"profile={profile}) ended '{final.get('status')}' "
            f"({final.get('error', 'no result block')}) — the sweep stops with nothing written"
        )
    return payload["id"], final["result"]


def _split_datasets(dataset_store: DatasetStore, split: str) -> list[dict]:
    """Every registered dataset metadata row for ``split`` (checksum-verified on load, the ONE
    ``DatasetStore.list`` read). A file that fails integrity verification anywhere in the store
    aborts the whole sweep explicitly — a partial report is a misleading report."""
    records, errors = dataset_store.list()
    if errors:
        raise ScanError(
            f"{len(errors)} dataset file(s) failed integrity verification "
            f"({[e['file'] for e in errors]}) — the sweep stops with nothing written"
        )
    return [r for r in records if r["split"] == split]


def _measurement(result: dict) -> dict:
    """The per-report measurement copied VERBATIM from the persisted row-31 aggregates (never
    recomputed) — the SAME shape ``pnl_ledger._split_measurement`` copies for a ledger row."""
    agg = result["aggregates"]
    return {"net_r": agg["net_r"], "net_usd": agg["net_usd"], "n": agg["n"]}


def _dataset_rows(
    datasets: list[dict],
    champion_pairs: list[tuple[str, dict]],
    candidate_pairs: list[tuple[str, dict]],
) -> list[dict]:
    """One row per dataset: the champion's and the candidate's measurements (verbatim) plus the
    candidate-minus-champion deltas. ``candidate_report_id`` is kept ONLY for a possible promotion
    (``append_validation_row`` needs it) — it is per-run-random (a fresh uuid4 every run) and is
    stripped before anything is written to ``--out`` (see ``_split_summary``), so it never breaks
    the byte-identical-re-run guarantee."""
    rows = []
    for dataset, (_champ_report_id, champ_result), (cand_report_id, cand_result) in zip(
        datasets, champion_pairs, candidate_pairs
    ):
        champion = _measurement(champ_result)
        candidate = _measurement(cand_result)
        rows.append(
            {
                "dataset_id": dataset["id"],
                "dataset_checksum": dataset["checksum"],
                "champion": champion,
                "candidate": candidate,
                "delta_net_r": candidate["net_r"] - champion["net_r"],
                "delta_net_usd": candidate["net_usd"] - champion["net_usd"],
                "candidate_report_id": cand_report_id,
            }
        )
    return rows


def _split_summary(rows: list[dict]) -> dict:
    """The per-split report block: the full per-dataset breakdown (report ids stripped — see
    ``_dataset_rows``) plus the SUMMED aggregate delta and n over every dataset in this split
    (never pooled with the OTHER split — train and hold-out are always two separate summaries)."""
    return {
        "datasets": [
            {k: v for k, v in row.items() if k != "candidate_report_id"} for row in rows
        ],
        "aggregate": {
            "delta_net_r": sum(r["delta_net_r"] for r in rows),
            "delta_net_usd": sum(r["delta_net_usd"] for r in rows),
            "candidate_n": sum(r["candidate"]["n"] for r in rows),
            "champion_n": sum(r["champion"]["n"] for r in rows),
        },
    }


def _is_positive(aggregate: dict) -> bool:
    return aggregate["delta_net_r"] > 0 and aggregate["delta_net_usd"] > 0


def _promote(
    store: JournalStore,
    config: Config,
    *,
    champion: dict,
    candidate_id: str,
    train_datasets: list[dict],
    holdout_datasets: list[dict],
    train_rows: list[dict],
    holdout_rows: list[dict],
) -> dict:
    """Promote a genuine hold-out survivor: append ONE PnL-ledger row (the EXISTING single
    writer) THEN move the persisted champion pointer — in that crash-safe order (see the module
    docstring). Requires EXACTLY one train and one hold-out dataset registered
    (``append_validation_row``'s structural shape, reused verbatim, never modified); with more of
    either, promotion is explicitly skipped with an honest note — the SCAN still evaluated and
    reported every dataset."""
    if len(train_datasets) != 1 or len(holdout_datasets) != 1:
        return {
            "candidate_id": candidate_id,
            "promoted": False,
            "note": (
                f"{len(train_datasets)} train / {len(holdout_datasets)} hold-out dataset(s) "
                f"registered — automatic promotion requires exactly one of each (the existing "
                f"ledger writer's shape); nothing was promoted this run"
            ),
        }
    enhancement_id = f"{candidate_id}-over-{champion['strategy_id']}-{champion['profile']}"
    title = (
        f"candidate '{candidate_id}' over champion "
        f"'{champion['strategy_id']}'/'{champion['profile']}'"
    )
    baseline = {SPLIT_TRAIN: train_rows[0]["champion"], SPLIT_HOLDOUT: holdout_rows[0]["champion"]}
    try:
        append_validation_row(
            store,
            config,
            enhancement_id=enhancement_id,
            title=title,
            candidate_train_report_id=train_rows[0]["candidate_report_id"],
            candidate_holdout_report_id=holdout_rows[0]["candidate_report_id"],
            baseline=baseline,
        )
    except (LedgerCompositionError, DuplicateEnhancementError) as exc:
        raise ScanError(
            f"promotion of '{candidate_id}' could not append its PnL-ledger row: {exc} — if a "
            f"row for '{enhancement_id}' already exists but the champion pointer still reads "
            f"{champion}, a PRIOR promotion attempt likely crashed between its two writes; "
            f"resolve manually before re-running (nothing further was written this run)"
        ) from exc
    # The ledger row is now durably committed — safe to move the pointer. A crash AFTER this
    # point leaves a correctly-attributed ledger row and a moved pointer: fully consistent.
    store.set_champion_pointer(
        strategy_id=champion["strategy_id"], profile=candidate_id, wall_ts=time.time()
    )
    return {"candidate_id": candidate_id, "promoted": True, "enhancement_id": enhancement_id}


# --- the ONE computer of Data Contract row 36 --------------------------------------------------


def run_sweep(store: JournalStore, dataset_store: DatasetStore, config: Config) -> dict:
    """Run the full candidate sweep ONCE. Returns the complete report dict — the SAME shape
    persisted to ``--out`` (the CLI is a thin wrapper). A genuine hold-out survivor is promoted
    INLINE (ledger row + champion-pointer move) before this returns, so the returned report
    already reflects the promotion outcome (``champion_after``). Raises ``ScanError`` for a
    dishonest state — nothing is written, nothing promoted."""
    champion = store.get_champion_pointer()
    jobs = BacktestJobManager(store, config)

    # Candidate enumeration reads the ONE registry FIRST: zero registered candidates is an honest
    # empty sweep, and skipping straight to the report avoids running the champion's own backtests
    # for nothing (they exist only to be compared against a candidate).
    candidates = [p for p in config.profile_registry() if not p["is_default"]]

    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)

    champion_train: list[tuple[str, dict]] = []
    champion_holdout: list[tuple[str, dict]] = []
    if candidates:
        # The champion's own backtest is computed ONCE per dataset — shared across every
        # candidate's comparison (efficiency, not a second path: still the same
        # BacktestJobManager call).
        champion_train = [
            _run_backtest(
                jobs, store, dataset_store, ds["id"],
                strategy_id=champion["strategy_id"], profile=champion["profile"],
            )
            for ds in train_datasets
        ]
        champion_holdout = [
            _run_backtest(
                jobs, store, dataset_store, ds["id"],
                strategy_id=champion["strategy_id"], profile=champion["profile"],
            )
            for ds in holdout_datasets
        ]

    candidate_entries: list[dict] = []
    promotion: dict | None = None
    for candidate in candidates:
        candidate_id = candidate["id"]
        candidate_train = [
            _run_backtest(
                jobs, store, dataset_store, ds["id"],
                strategy_id=champion["strategy_id"], profile=candidate_id,
            )
            for ds in train_datasets
        ]
        candidate_holdout = [
            _run_backtest(
                jobs, store, dataset_store, ds["id"],
                strategy_id=champion["strategy_id"], profile=candidate_id,
            )
            for ds in holdout_datasets
        ]
        train_rows = _dataset_rows(train_datasets, champion_train, candidate_train)
        holdout_rows = _dataset_rows(holdout_datasets, champion_holdout, candidate_holdout)
        train_summary = _split_summary(train_rows)
        holdout_summary = _split_summary(holdout_rows)

        train_positive = _is_positive(train_summary["aggregate"])
        holdout_positive = _is_positive(holdout_summary["aggregate"])
        robust = bool(train_rows) and all(
            r["delta_net_r"] > 0 and r["delta_net_usd"] > 0 for r in train_rows
        )
        survivor = (
            holdout_positive
            and holdout_summary["aggregate"]["candidate_n"] >= config.promotion_min_sample_size
        )
        # "Positive train, failing the hold-out gate" (the phase spec's own definition) — a
        # candidate that never looked good on train is honestly just a non-survivor, not overfit.
        overfit = train_positive and not survivor

        candidate_entries.append(
            {
                "candidate_id": candidate_id,
                "train": train_summary,
                "holdout": holdout_summary,
                "survivor": survivor,
                "robustness": "robust" if robust else "speculative",
                "overfit": overfit,
            }
        )

        if survivor and promotion is None:
            promotion = _promote(
                store,
                config,
                champion=champion,
                candidate_id=candidate_id,
                train_datasets=train_datasets,
                holdout_datasets=holdout_datasets,
                train_rows=train_rows,
                holdout_rows=holdout_rows,
            )

    return {
        "register": REGISTER,
        "promotion_min_sample_size": config.promotion_min_sample_size,
        "champion_before": champion,
        "champion_after": store.get_champion_pointer(),
        "candidates": candidate_entries,
        "promotion": promotion,
    }


def _render_report(report: dict) -> str:
    """Pure, deterministic JSON render (sorted keys — the ``datasets.py`` ``_canonical`` /
    ``pnl_ledger`` markdown precedent): identical ``report`` dicts always render identical bytes,
    and the report itself carries no wall-clock or per-run-random field (see the module
    docstring), so two independent fresh-state runs of an identical non-promoting scenario produce
    byte-identical ``--out`` files."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main() -> int:
    """The CLI entry: sweep against the operator's journal DB + dataset dir (the SAME
    ``TAPEOLOGY_JOURNAL_DB`` / ``TAPEOLOGY_DATASET_DIR`` resolution seams the backend and
    ``pnl_baseline`` read), writing the report to ``--out``. Zero candidates or zero survivors is
    an honest, exit-0 outcome; a ``ScanError`` prints an explicit message to stderr and exits 1
    with NOTHING written."""
    parser = argparse.ArgumentParser(
        description="J-07 candidate-sweep harness — evaluate every registered candidate profile "
        "against the current champion, validated on the frozen hold-out set."
    )
    parser.add_argument("--out", required=True, help="path to write the scan report JSON")
    args = parser.parse_args()

    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        dataset_store = DatasetStore(config.dataset_dir_resolved())
        try:
            report = run_sweep(store, dataset_store, config)
        except ScanError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        store.close()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_render_report(report), encoding="utf-8")

    n_candidates = len(report["candidates"])
    n_survivors = sum(1 for c in report["candidates"] if c["survivor"])
    if report["promotion"] is not None and report["promotion"].get("promoted"):
        print(
            f"sweep complete: {n_candidates} candidate(s) evaluated, {n_survivors} hold-out "
            f"survivor(s) — promoted '{report['promotion']['candidate_id']}' "
            f"('{report['promotion']['enhancement_id']}'); report written to {out_path}"
        )
    else:
        print(
            f"sweep complete: {n_candidates} candidate(s) evaluated, {n_survivors} hold-out "
            f"survivor(s); champion unmoved ({report['champion_after']}); report written to "
            f"{out_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
