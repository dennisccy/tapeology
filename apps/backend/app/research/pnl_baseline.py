"""The founding-baseline seeding CLI (era-3 capability 5, J-04) — ``python -m app.research.pnl_baseline``.

Appends the PnL ledger's FOUNDING row: strategy v1 on profile ``default``, measured over the
frozen fixture train AND hold-out datasets (the committed keyless ``PG_SIP_REFERENCE`` windows).
Keyless and deterministic end to end:

  * datasets are obtained ONLY through the real public store path (``record_from_source`` over
    the committed reference window, sliced to the config-owned founding windows — reproducing the
    committed fixture pair content-identically); a window already registered under its expected
    frozen split is REUSED (the 409-style ``DatasetAlreadyRegistered`` refusal carries the
    existing id), never re-recorded and never re-tagged;
  * one backtest per split runs through the EXISTING ``BacktestJobManager`` public API
    (``create`` + ``run_sync`` — the runner's computing logic untouched);
  * the row is composed and appended by the ONE writer (``pnl_ledger.append_validation_row``),
    copying the reports' aggregates VERBATIM, with the explicit ``None`` baseline side (no prior
    incumbent exists — the config-owned founding marker id/title, never fabricated zeros).

IDEMPOTENT: when the founding row already exists the command prints an explicit
"already present" message and exits 0 — no duplicate row, no mutation, no datasets recorded, no
backtests run. Every failure (unavailable reference window, frozen-split conflict, failed
backtest, corrupt report) surfaces an explicit error on stderr and a non-zero exit — a partial
row never exists.
"""

from __future__ import annotations

import sys

from ..config import CONFIG, Config, STRATEGY_V1_ID
from .backtests import BacktestJobManager, PROFILE_DEFAULT, STATUS_DONE
from .datasets import (
    DatasetAlreadyRegistered,
    DatasetIntegrityError,
    DatasetRecordError,
    DatasetStore,
    EmptyWindowError,
    REFERENCE_SOURCE_ID,
    SOURCE_REFERENCE,
    SPLIT_HOLDOUT,
    SPLIT_TRAIN,
    record_from_source,
)
from .pnl_ledger import LedgerCompositionError, append_validation_row
from .store import DuplicateEnhancementError, JournalStore


class FoundingSeedError(Exception):
    """The founding seeding could not proceed (dataset conflict or a non-done backtest) —
    explicit, with NOTHING appended to the ledger."""


def _obtain_dataset(dataset_store: DatasetStore, config: Config, *, split: str, window: tuple) -> str:
    """Record the founding window through the REAL keyless reference path (row 30's one public
    mutation), or REUSE the already-registered dataset carrying this exact content. A frozen-split
    conflict (the content registered under the OTHER split) is an explicit refusal — split tags
    are frozen at registration and never re-tagged."""
    start, end = window
    try:
        meta = record_from_source(
            dataset_store,
            source_kind=SOURCE_REFERENCE,
            source_id=REFERENCE_SOURCE_ID,
            split=split,
            start=start,
            end=end,
            config=config,
        )
        return meta["id"]
    except DatasetAlreadyRegistered as exc:
        if exc.existing_split != split:
            raise FoundingSeedError(
                f"the founding {split} window is already registered as dataset "
                f"'{exc.existing_id}' with the frozen split '{exc.existing_split}' — split tags "
                f"are never re-tagged, so the seeding stops with nothing appended"
            ) from exc
        return exc.existing_id


def _run_backtest(
    jobs: BacktestJobManager, store: JournalStore, dataset_store: DatasetStore, dataset_id: str
) -> str:
    """Run ONE founding backtest synchronously through the EXISTING public job API and return
    its report id — refusing explicitly unless it completed ``done`` (a failed or cancelled
    report carries no served aggregates, so no ledger row could honestly cite it)."""
    payload = jobs.create(
        {"dataset_id": dataset_id, "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    )
    jobs.run_sync(payload["id"], dataset_store=dataset_store)
    final = store.get_backtest(payload["id"]).payload
    if final.get("status") != STATUS_DONE:
        raise FoundingSeedError(
            f"founding backtest '{payload['id']}' over dataset '{dataset_id}' ended "
            f"'{final.get('status')}' ({final.get('error', 'no result block')}) — nothing was "
            f"appended to the ledger"
        )
    return payload["id"]


def seed_founding_row(
    store: JournalStore, dataset_store: DatasetStore, config: Config
) -> tuple[bool, dict]:
    """Seed the founding baseline row ONCE. Returns ``(created, row_payload)``:
    ``created=False`` means the row already existed — the honest no-op (nothing recorded, nothing
    run, nothing appended; the existing payload is returned verbatim)."""
    existing = store.get_pnl_ledger_row(config.pnl_founding_enhancement_id)
    if existing is not None:
        return False, existing.payload
    train_dataset_id = _obtain_dataset(
        dataset_store, config, split=SPLIT_TRAIN, window=config.pnl_founding_train_window
    )
    holdout_dataset_id = _obtain_dataset(
        dataset_store, config, split=SPLIT_HOLDOUT, window=config.pnl_founding_holdout_window
    )
    jobs = BacktestJobManager(store, config)
    train_report_id = _run_backtest(jobs, store, dataset_store, train_dataset_id)
    holdout_report_id = _run_backtest(jobs, store, dataset_store, holdout_dataset_id)
    row = append_validation_row(
        store,
        config,
        enhancement_id=config.pnl_founding_enhancement_id,
        title=config.pnl_founding_enhancement_title,
        candidate_train_report_id=train_report_id,
        candidate_holdout_report_id=holdout_report_id,
        baseline=None,  # no prior incumbent exists — the explicit founding marker, never zeros
    )
    return True, row


def main() -> int:
    """The CLI entry: seed against the operator's journal DB + dataset dir (the same
    ``TAPEOLOGY_JOURNAL_DB`` / ``TAPEOLOGY_DATASET_DIR`` resolution seams the backend reads)."""
    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        dataset_store = DatasetStore(config.dataset_dir_resolved())
        try:
            created, row = seed_founding_row(store, dataset_store, config)
        except (
            FoundingSeedError,
            LedgerCompositionError,
            DuplicateEnhancementError,
            DatasetRecordError,
            DatasetIntegrityError,
            EmptyWindowError,
        ) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        store.close()
    if created:
        print(
            f"founding baseline row appended: '{row['enhancement_id']}' — {row['title']} "
            f"(train n={row['candidate'][SPLIT_TRAIN]['n']}, "
            f"holdout n={row['candidate'][SPLIT_HOLDOUT]['n']}; simulated measurements, "
            f"served at GET /research/pnl/ledger)"
        )
    else:
        print(
            f"already present — the founding baseline row '{row['enhancement_id']}' exists; "
            f"nothing was appended (honest no-op)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
