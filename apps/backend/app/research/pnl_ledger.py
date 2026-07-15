"""The PnL-ledger writer + serving projection (era-3 capability 5, J-04) — Data Contract row 32's
ONE owner.

THIS MODULE is the single composer of PnL-ledger rows and the single serving read over them:

  * ``append_validation_row`` composes ONE row at validation time from COMPLETED, PERSISTED
    backtest reports (Data Contract row 31) — copying each split's ``net_r`` / ``net_usd`` / ``n``
    aggregates VERBATIM from the stored payloads (never recomputing trades, never re-deriving R
    or $ — a recomputation here would be a row-31/row-27 violation). It never touches datasets,
    engines, or the runner: provenance (dataset id + checksum, strategy id, profile,
    ``config_fingerprint``) is read from the reports' own stored stamps.
  * ``ledger_projection`` is the ONE read every surface consumes: ``GET /research/pnl/ledger``
    serves it, the markdown render walks it, and the MCP ``pnl_ledger`` tool proxies the route
    byte-identically — so REST, markdown, and MCP can never diverge (single source of truth).
    The projection serves the stored rows verbatim plus the config-owned presentation-only
    ``insufficient_sample`` marker per split (the ``analytics_min_sample_size`` precedent:
    ``n`` stays present; the stored row is never mutated).
  * ``render_history_markdown`` / ``write_history_markdown`` pure-render the SAME projection into
    the committed ``reports/pnl/pnl-history.md``: no wall-clock, no environment-dependent
    formatting — every displayed value derives only from stored row values, so regenerating with
    unchanged rows is a byte-level no-op. Dates render dd-MM-yyyy (foundation invariant 12) from
    each row's stored UTC timestamp; the register string is the ONE existing ``REGISTER``
    constant; every $ figure sits beside its R figure and its n; train and hold-out stay separate
    (never pooled); an empty ledger renders an honest explicit empty state.

Honesty disciplines, clause by clause:
  * **Append-only.** Rows go through ``JournalStore.append_pnl_ledger_row`` — the repository
    exposes NO update and NO delete (the ``verdict_events`` standard); a duplicate enhancement id
    is the store's explicit ``DuplicateEnhancementError`` refusal (one honest row per
    enhancement).
  * **Founding-row honesty.** The founding row has no prior incumbent, so its baseline side is
    explicitly ``None`` with the config-owned founding marker id/title — NEVER fabricated zeros
    implying a measured comparator.
  * **Never pool.** Train and hold-out are four separate value pairs (baseline vs candidate ×
    train vs hold-out) with n per split — no combined figure exists anywhere in the row; the two
    source reports must agree on strategy / profile / ``config_fingerprint`` and each must have
    measured its OWN split (a mismatch is an explicit ``LedgerCompositionError``, never a
    silently mixed row).
  * **Honest failure states.** A missing, non-terminal, or shape-corrupt source report at
    composition time raises ``LedgerCompositionError`` explicitly and appends NOTHING — a partial
    row never exists.
"""

from __future__ import annotations

import copy
import time
from datetime import datetime, timezone
from pathlib import Path

from ..config import Config
from .backtests import REGISTER, STATUS_DONE
from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN
from .store import JournalStore, PnlLedgerRecord

# The NEW row-shape discriminator ``render_history_markdown`` branches on (era-5B J-08) — present
# ONLY on a row appended by ``append_strategy_comparison_row`` below; every EXISTING/OLD row
# (appended by ``append_validation_row`` above) carries no ``kind`` key at all, so
# ``row.get("kind")`` reads ``None`` for them — an explicit tag rather than inferring the shape
# from "has no 'candidate' key" (the codebase's ``_ROW_TRADE``/``_ROW_QUOTE`` tagged-shape
# precedent in ``datasets.py``, applied here).
_KIND_STRATEGY_COMPARISON = "strategy_comparison"


class LedgerCompositionError(Exception):
    """A ledger row could not be composed from its source backtest reports — missing report,
    non-terminal status, corrupt shape, wrong split, or mismatched provenance stamps. Explicit,
    and NOTHING is appended (no partial row exists)."""


def _iso_utc(epoch: float) -> str:
    """The stored UTC timestamp string, computed ONCE at the append moment (the dataset-store
    ``created_utc`` shape). The markdown's dd-MM-yyyy date derives from THIS stored value."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _completed_report(store: JournalStore, report_id: str, expected_split: str) -> dict:
    """Fetch ONE source backtest report and validate it can honestly back a ledger split:
    it must exist, be ``done`` (a cancelled/failed/queued report carries no served result),
    carry the result block's aggregates + dataset stamps, and have measured the EXPECTED frozen
    split (train never stands in for hold-out or vice versa — the never-pool discipline)."""
    record = store.get_backtest(report_id)
    if record is None:
        raise LedgerCompositionError(
            f"no backtest report with id '{report_id}' — the ledger only cites persisted "
            f"reports, so nothing was appended"
        )
    payload = record.payload
    if payload.get("status") != STATUS_DONE:
        raise LedgerCompositionError(
            f"backtest report '{report_id}' is '{payload.get('status')}', not '{STATUS_DONE}' — "
            f"only a completed report carries served aggregates, so nothing was appended"
        )
    result = payload.get("result")
    if (
        not isinstance(result, dict)
        or not isinstance(result.get("aggregates"), dict)
        or not isinstance(result.get("dataset"), dict)
    ):
        raise LedgerCompositionError(
            f"backtest report '{report_id}' does not carry the expected result shape — corrupt "
            f"or incomplete, so nothing was appended"
        )
    split = result["dataset"].get("split")
    if split != expected_split:
        raise LedgerCompositionError(
            f"backtest report '{report_id}' measured the '{split}' split but was passed as the "
            f"'{expected_split}' side — train and hold-out are never pooled or swapped, so "
            f"nothing was appended"
        )
    return payload


def _split_measurement(report_payload: dict) -> dict:
    """The per-split ledger measurement: ``net_r`` / ``net_usd`` / ``n`` copied VERBATIM from the
    persisted row-31 aggregates (never recomputed — equality with the stored report is the
    acceptance test)."""
    aggregates = report_payload["result"]["aggregates"]
    return {
        "net_r": aggregates["net_r"],
        "net_usd": aggregates["net_usd"],
        "n": aggregates["n"],
    }


def _split_provenance(report_payload: dict) -> dict:
    """The per-split provenance: the source report id and its dataset's stored id + checksum
    (read from the report's own stamps — never re-derived)."""
    dataset = report_payload["result"]["dataset"]
    return {
        "backtest_id": report_payload["id"],
        "dataset_id": dataset["id"],
        "dataset_checksum": dataset["checksum"],
    }


def append_validation_row(
    store: JournalStore,
    config: Config,
    *,
    enhancement_id: str,
    title: str,
    candidate_train_report_id: str,
    candidate_holdout_report_id: str,
    baseline: dict | None = None,
) -> dict:
    """Compose and append ONE PnL-ledger row (row 32) at validation time — the single writer.

    Today's only caller is the founding-baseline seeding CLI (``app.research.pnl_baseline``),
    which passes ``baseline=None``: no prior incumbent exists, so the baseline side is stored as
    an explicit ``None`` with ``founding: true`` — never fabricated zeros. (J-07's sweep becomes
    the second caller, passing the incumbent's measured splits as ``baseline``, stored verbatim.)

    The candidate side is copied VERBATIM from the two COMPLETED source reports (one per frozen
    split); the shared provenance stamps (strategy id, profile, ``config_fingerprint``) must
    AGREE across the two reports — composing across mismatched stamps would pool across
    fingerprints, so it is an explicit refusal. Returns the appended payload (which the store now
    serves verbatim). A duplicate enhancement id raises the store's ``DuplicateEnhancementError``."""
    train = _completed_report(store, candidate_train_report_id, SPLIT_TRAIN)
    holdout = _completed_report(store, candidate_holdout_report_id, SPLIT_HOLDOUT)
    for stamp in ("strategy_id", "profile", "config_fingerprint"):
        if train["result"][stamp] != holdout["result"][stamp]:
            raise LedgerCompositionError(
                f"the train and hold-out reports disagree on {stamp} "
                f"('{train['result'][stamp]}' vs '{holdout['result'][stamp]}') — a ledger row "
                f"never pools across strategies, profiles, or config fingerprints, so nothing "
                f"was appended"
            )
    now = time.time()
    row = {
        "enhancement_id": enhancement_id,
        "title": title,
        # No prior incumbent ⇒ a FOUNDING row: the baseline side is explicitly None (honest
        # absence), never zeros implying a measured comparator.
        "founding": baseline is None,
        "baseline": baseline,
        "candidate": {
            SPLIT_TRAIN: _split_measurement(train),
            SPLIT_HOLDOUT: _split_measurement(holdout),
        },
        "provenance": {
            "strategy_id": train["result"]["strategy_id"],
            "profile": train["result"]["profile"],
            "config_fingerprint": train["result"]["config_fingerprint"],
            SPLIT_TRAIN: _split_provenance(train),
            SPLIT_HOLDOUT: _split_provenance(holdout),
        },
        "created_wall_ts": now,
        "created_utc": _iso_utc(now),
    }
    store.append_pnl_ledger_row(
        PnlLedgerRecord(enhancement_id=enhancement_id, payload=row, created_wall_ts=now)
    )
    return row


# --- The 3-way strategy-comparison append (era-5B J-08) — an ADDITIVE second writer beside
# ``append_validation_row`` above (untouched by this section), composing a DIFFERENT row shape
# from a DIFFERENT source. --------------------------------------------------------------------


def _ledger_cell(cell: dict, basis: str) -> dict:
    """One report cell, denormalized for a ledger row: a COPY of the source ``edge_report.py``
    cell (never mutated) with ``basis`` (``"train"`` / ``"holdout"``) added — the split a cell
    floating alone (e.g. copy-pasted out of the row) still honestly names. ``measurement``,
    ``null_baseline``, and ``insufficient_sample`` are copied VERBATIM — ``edge_report.py``'s
    ``_split_cells`` already computed all three against the SAME ``pnl_min_sample_size`` this
    row's own ``pnl_min_sample_size`` field carries, so re-deriving any of them here would risk a
    second, driftable copy of that gate (never recomputed, per this module's own writer
    discipline)."""
    return {**copy.deepcopy(cell), "basis": basis}


def append_strategy_comparison_row(
    store: JournalStore,
    config: Config,
    *,
    enhancement_id: str,
    title: str,
    report: dict,
) -> dict:
    """Compose and append ONE 3-way strategy-comparison PnL-ledger row (era-5B J-08) from an
    ALREADY-COMPLETED ``run_strategy_comparison_report`` output — the identical "verbatim copy,
    never recompute" discipline ``append_validation_row`` uses for its own two source reports,
    applied here to the report's OWN cells (never a dataset/engine/aggregate call of any kind;
    this function takes no dataset store, bar store, or backtest-job manager of any kind — its
    only inputs are the journal store it appends through, the config it reads assumptions from,
    and the already-completed report dict itself).

    Distinct from ``append_validation_row`` above (untouched by this function): that writer
    composes a TWO-SIDED (baseline vs ONE candidate) row from two PERSISTED BACKTEST reports
    fetched by id; THIS writer composes a THREE-STRATEGY (``v1`` / ``structure_tape`` /
    ``structure_tape_map``) row DIRECTLY from an in-memory 3-way comparison report's own cells —
    the report itself already IS the single completed measurement (no per-report id to fetch, no
    provenance to cross-check between two sources). Both writers share the SAME append mechanism
    (``store.append_pnl_ledger_row``) and the SAME structural append-only/no-update-or-delete
    guarantee; ``ledger_projection`` below needs NO change to serve either shape verbatim (a new
    row's absent ``"baseline"``/``"candidate"`` keys make its existing per-row label loop skip it
    silently — see that function's own docstring).

    The appended row NEVER pools: every cell keeps its own (strategy, class, side, reaction, feed)
    identity and its own ``basis`` (train/holdout — kept as two separate top-level lists,
    mirroring the report's own ``train``/``holdout`` shape); this function only re-shapes/labels
    the report's cells (adding ``basis``), it never sums, averages, or merges any two of them, and
    it never touches a cell's ``feed`` (so two feeds recorded into the SAME report stay exactly as
    un-pooled as ``edge_report.py`` already left them). Every cell carries its measurement
    (n/gross/net R/$), its OWN null baseline, and the row-level fee/slippage/dollars-per-R
    assumptions read VERBATIM from ``config`` (never re-derived) — a single shared block rather
    than repeated per cell, since every registered strategy currently shares the identical fee/
    slippage model (``config.strategy_definition``'s own documented "FEES / SLIPPAGE / DOLLAR
    CONVERSION — IDENTICAL to v1" clause). ``insufficient_sample`` is copied VERBATIM from the
    source cell.

    Raises ``LedgerCompositionError`` (never appends a partial row) if ``report`` does not carry
    the expected ``train.cells`` / ``holdout.cells`` shape — the identical honest-failure
    discipline ``_completed_report`` enforces for the two-way writer above. A duplicate
    ``enhancement_id`` raises the store's own ``DuplicateEnhancementError`` (unchanged, structural,
    the SAME one row per enhancement guarantee every ledger row shares)."""
    for split in (SPLIT_TRAIN, SPLIT_HOLDOUT):
        section = report.get(split)
        if not isinstance(section, dict) or "cells" not in section:
            raise LedgerCompositionError(
                f"the report does not carry a '{split}.cells' section — a 3-way comparison row "
                f"is only ever composed from a genuinely completed run_strategy_comparison_report "
                f"output, so nothing was appended"
            )
    now = time.time()
    row = {
        "kind": _KIND_STRATEGY_COMPARISON,
        "enhancement_id": enhancement_id,
        "title": title,
        "register": report.get("register", REGISTER),
        "pnl_min_sample_size": report.get("pnl_min_sample_size", config.pnl_min_sample_size),
        "config_fingerprint": config.config_fingerprint(),
        "assumptions": {
            "fees": {
                "per_share": config.strategy_fee_per_share,
                "min_per_trade": config.strategy_fee_min_per_trade,
            },
            "slippage": {"spread_fraction": config.strategy_slippage_spread_fraction},
            "dollars_per_r": config.strategy_dollars_per_r,
        },
        "cells": {
            SPLIT_TRAIN: [_ledger_cell(cell, SPLIT_TRAIN) for cell in report[SPLIT_TRAIN]["cells"]],
            SPLIT_HOLDOUT: [_ledger_cell(cell, SPLIT_HOLDOUT) for cell in report[SPLIT_HOLDOUT]["cells"]],
        },
        "created_wall_ts": now,
        "created_utc": _iso_utc(now),
    }
    store.append_pnl_ledger_row(
        PnlLedgerRecord(enhancement_id=enhancement_id, payload=row, created_wall_ts=now)
    )
    return row


# --- the ONE serving read (REST, markdown, and — via the route — MCP all consume this) -------------


def ledger_projection(store: JournalStore, config: Config) -> dict:
    """The canonical served ledger: every stored row VERBATIM (insertion order — the append-only
    chronology), wrapped with the visible simulated register (the ONE ``REGISTER`` constant) and
    the config-owned label minimum. Each split measurement additionally carries the
    presentation-only ``insufficient_sample`` marker (``n < pnl_min_sample_size``, with ``n``
    still present — the ``analytics_min_sample_size`` precedent). The marker is applied to a COPY
    at read; the stored row is never mutated. An empty ledger is an honest empty list."""
    min_n = config.pnl_min_sample_size
    rows: list[dict] = []
    for record in store.list_pnl_ledger():
        row = copy.deepcopy(record.payload)
        for side in ("baseline", "candidate"):
            measurements = row.get(side)
            if not isinstance(measurements, dict):
                continue  # the founding row's baseline is explicitly None — nothing to label
            for values in measurements.values():
                values["insufficient_sample"] = values["n"] < min_n
        rows.append(row)
    return {"register": REGISTER, "min_sample_size": min_n, "rows": rows}


# --- the pure markdown render (reports/pnl/pnl-history.md) ------------------------------------------


def _ddmmyyyy(created_utc: str) -> str:
    """dd-MM-yyyy (foundation invariant 12) from the STORED UTC timestamp string — a pure format
    of a stored value (no wall-clock, no local timezone: the committed file must render
    byte-identically in every environment)."""
    return datetime.fromisoformat(created_utc.replace("Z", "+00:00")).strftime("%d-%m-%Y")


def _render_strategy_comparison_row_lines(row: dict, index: int) -> list[str]:
    """The era-5B J-08 rendering branch for a ``_KIND_STRATEGY_COMPARISON`` row — a per-cell
    table (strategy x class x side x reaction x feed) for each split, mirroring the EXISTING
    two-way row's table shape (one line per measurement, net R beside net $ beside n beside its
    sample label) but WITHOUT a ``side`` column (there is no baseline/candidate distinction here —
    ``strategy_id`` already carries that role, comparing all three registered strategies
    side-by-side)."""
    lines = [
        f"## {index}. {row['title']}",
        "",
        f"- Enhancement id: `{row['enhancement_id']}`",
        f"- Appended (UTC): {_ddmmyyyy(row['created_utc'])}",
        f"- Config fingerprint `{row['config_fingerprint']}`",
        f"- Register: {row['register']}",
        f"- Assumptions: fees `{row['assumptions']['fees']['per_share']}`/share (minimum "
        f"`{row['assumptions']['fees']['min_per_trade']}`/trade) · slippage "
        f"`{row['assumptions']['slippage']['spread_fraction']}` of spread · "
        f"`{row['assumptions']['dollars_per_r']}` per R",
        "- Three-way strategy comparison (`v1` / `structure_tape` / `structure_tape_map`) — "
        "train and hold-out separate, feeds never pooled.",
        "",
    ]
    min_n = row["pnl_min_sample_size"]
    for split in (SPLIT_TRAIN, SPLIT_HOLDOUT):
        cells = row["cells"][split]
        lines += [f"### {split}", ""]
        if not cells:
            lines += ["No cells for this split.", ""]
            continue
        lines += [
            "| strategy | class | side | reaction | feed | net R | net $ | n | sample |",
            "|----------|-------|------|----------|------|------:|------:|--:|--------|",
        ]
        for cell in cells:
            measurement = cell["measurement"]
            label = (
                f"insufficient sample (n < {min_n})" if cell["insufficient_sample"] else "ok"
            )
            lines.append(
                f"| {cell['strategy_id']} | {cell['band_class']} | {cell['band_side']} | "
                f"{cell['reaction']} | {cell['feed']} | {measurement['net_r']} | "
                f"{measurement['net_usd']} | {measurement['n']} | {label} |"
            )
        lines.append("")
    return lines


def render_history_markdown(store: JournalStore, config: Config) -> str:
    """Render the ledger to markdown — a PURE function of the stored rows via the SAME
    ``ledger_projection`` read the route serves (never a second query or labeling path).
    Deterministic byte-for-byte: regenerating with unchanged rows is a byte-level no-op."""
    projection = ledger_projection(store, config)
    min_n = projection["min_sample_size"]
    lines = [
        "# PnL History — the append-only enhancement ledger",
        "",
        f"> {projection['register']}",
        "",
        "A pure render of the stored PnL-ledger rows — `GET /research/pnl/ledger` serves the same",
        "rows verbatim (Data Contract row 32). Every figure is a simulated measurement of recorded",
        "historical tape under the disclosed fee/slippage assumptions — never live results, never",
        "a forecast, and not a profitability claim. Train and hold-out figures are separate and",
        f"never pooled. A split whose n is below the configured minimum ({min_n}) carries an",
        "explicit insufficient-sample label, with its n still shown.",
        "",
    ]
    rows = projection["rows"]
    if not rows:
        lines += [
            "No enhancement has been validated yet — the ledger is empty (an honest empty state,",
            "never fabricated rows). The founding baseline row arrives via",
            "`python -m app.research.pnl_baseline`.",
            "",
        ]
        return "\n".join(lines)
    for index, row in enumerate(rows, start=1):
        if row.get("kind") == _KIND_STRATEGY_COMPARISON:
            lines += _render_strategy_comparison_row_lines(row, index)
            continue
        provenance = row["provenance"]
        lines += [
            f"## {index}. {row['title']}",
            "",
            f"- Enhancement id: `{row['enhancement_id']}`",
            f"- Appended (UTC): {_ddmmyyyy(row['created_utc'])}",
            f"- Strategy `{provenance['strategy_id']}` · profile `{provenance['profile']}` · "
            f"config fingerprint `{provenance['config_fingerprint']}`",
        ]
        if row["baseline"] is None:
            lines.append(
                "- Founding row — no prior incumbent: the baseline side is explicitly absent "
                "(`null`), never fabricated zeros."
            )
        lines += [
            "",
            "| side | split | net R | net $ | n | sample |",
            "|------|-------|------:|------:|--:|--------|",
        ]
        for side in ("baseline", "candidate"):
            measurements = row.get(side)
            if not isinstance(measurements, dict):
                continue
            for split in (SPLIT_TRAIN, SPLIT_HOLDOUT):
                values = measurements[split]
                label = (
                    f"insufficient sample (n < {min_n})"
                    if values["insufficient_sample"]
                    else "ok"
                )
                lines.append(
                    f"| {side} | {split} | {values['net_r']} | {values['net_usd']} | "
                    f"{values['n']} | {label} |"
                )
        lines += [
            "",
            f"- Provenance (train): backtest `{provenance['train']['backtest_id']}` · dataset "
            f"`{provenance['train']['dataset_id']}` · checksum "
            f"`{provenance['train']['dataset_checksum']}`",
            f"- Provenance (holdout): backtest `{provenance['holdout']['backtest_id']}` · dataset "
            f"`{provenance['holdout']['dataset_id']}` · checksum "
            f"`{provenance['holdout']['dataset_checksum']}`",
            "",
        ]
    return "\n".join(lines)


def write_history_markdown(store: JournalStore, config: Config, path: Path | None = None) -> Path:
    """Write the rendered markdown to ``path`` (default: the config-owned committed
    ``reports/pnl/pnl-history.md``). Same bytes in ⇒ same bytes out — the byte-level no-op is
    verifiable via ``git diff`` on the committed file as well as by the render-twice test."""
    target = Path(config.pnl_history_md_path) if path is None else Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_history_markdown(store, config), encoding="utf-8")
    return target
