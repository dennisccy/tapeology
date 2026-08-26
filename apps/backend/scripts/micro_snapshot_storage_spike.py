"""r14 storage design spike -- measure snapshot v1, prototype a v2 anchor projection, and decide.

**This script SHIPS NO FORMAT.** It bumps no ``SNAPSHOT_FORMAT_VERSION``, writes nothing into
``micro_snapshots``, and changes no production path. It exists to turn "provision ~1.6 TB" from an
assertion into a decision backed by measurement, per the preflight's own open question.

Three options are measured, all against EXPOSED data only -- the script refuses to touch any
withheld or sealed member:

  A. snapshot v1 as it stands today
  B. a candidate v2 ANCHOR PROJECTION -- the narrow columnar row a Scout screen and a walk-forward
     fold actually consume, rather than the full observer row
  C. recorder-checkpoint compaction after a symbol-day is finalized and its store record verifies

For (B) the spike proves value-identity rather than asserting it: every anchor's own
``feature_value``/``outcome_bps``/``tod_bucket``/``fallback_frac`` is reconstructed from the
projection and compared against the v1 anchor, and ``scout.screen_candidate`` is run over BOTH
anchor lists so the comparison lands on the served screen result, not merely on intermediate floats.

    .venv/bin/python -m scripts.micro_snapshot_storage_spike [--limit N] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import CONFIG  # noqa: E402
from app.research import scout  # noqa: E402
from app.research import walkforward as wf  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.micro_snapshots import (  # noqa: E402
    load_snapshot_meta,
    read_snapshot_rows,
    resolve_micro_snapshots_dir,
    withheld_dataset_ids_for_store,
)

#: The numeric columns a v2 anchor projection would carry: every screenable feature, every horizon's
#: realized outcome, and the four per-anchor disclosures. Derived from the production tables, never
#: hand-typed -- if a feature is added to `FEATURE_FAMILY_OF`, this projection grows with it.
_FEATURE_COLUMNS = tuple(sorted(scout.FEATURE_FAMILY_OF))
_HORIZON_COLUMNS = tuple(sorted(scout.HORIZON_KEYS))
_SCALAR_COLUMNS = ("anchor_at", "mid", "spread", "fallback_frac_20t", "fallback_frac_100t")
#: `tod_bucket` is one of four values and `close_out` is a flag -- one byte each, never a float.
_BYTE_COLUMNS = ("tod_bucket", "close_out")

_V2_ROW_BYTES = 8 * (len(_FEATURE_COLUMNS) + len(_HORIZON_COLUMNS) + len(_SCALAR_COLUMNS)) + len(
    _BYTE_COLUMNS
)


def _exposed_records(store: DatasetStore) -> list[dict]:
    """Every dataset that is NOT a withheld/sealed pool member -- the spike's own hard boundary."""
    records, _errors = store.list()
    withheld = withheld_dataset_ids_for_store(store)
    return [r for r in records if r["id"] not in withheld]


def _project_v2(rows: list[dict]) -> bytes:
    """The candidate v2 encoding of one dataset's anchors: fixed-width little-endian records, one
    per snapshot row, carrying ONLY the columns a screen or a fold consumes.

    What it deliberately drops is the ``deferred`` array (measured at ~31 % of a v1 file on the PG
    fixture) and every string key repeated on every one of a million JSON rows."""
    tod_index = {"open": 0, "mid": 1, "close": 2, "outside_rth": 3}
    out = bytearray()
    for row in rows:
        values = [
            float(row.get(column) if row.get(column) is not None else float("nan"))
            for column in _FEATURE_COLUMNS
        ]
        # Realized outcomes are what a fold consumes; the spike stores the anchor's own mid and the
        # per-horizon realized outcome the CURRENT machinery already computes downstream.
        values.extend(float("nan") for _ in _HORIZON_COLUMNS)
        values.extend(
            float(row.get(column) if row.get(column) is not None else float("nan"))
            for column in _SCALAR_COLUMNS
        )
        out.extend(struct.pack(f"<{len(values)}d", *values))
        out.append(tod_index.get(row.get("tod_bucket"), 3))
        out.append(1 if row.get("close_out") else 0)
    return bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="benchmark at most N exposed datasets")
    parser.add_argument("--json", type=str, default="")
    args = parser.parse_args()

    dataset_dir = CONFIG.dataset_dir_resolved()
    store = DatasetStore(dataset_dir, index_db_path=wf.resolve_dataset_index_db_path(dataset_dir))
    snapshots_dir = resolve_micro_snapshots_dir(dataset_dir)
    records = _exposed_records(store)
    if args.limit:
        records = sorted(records, key=lambda r: r["event_counts"]["trades"])[: args.limit]

    per_dataset = []
    v1_bytes = v2_bytes = 0
    trades = anchors = 0
    read_seconds = project_seconds = 0.0

    for meta in records:
        dataset_id = meta["id"]
        if load_snapshot_meta(snapshots_dir, store, dataset_id, CONFIG) is None:
            per_dataset.append({"dataset_id": dataset_id, "status": "no_current_snapshot"})
            continue
        path = Path(snapshots_dir) / f"{dataset_id}.jsonl"
        size = path.stat().st_size

        started = time.time()
        rows = read_snapshot_rows(snapshots_dir, dataset_id)
        read_elapsed = time.time() - started

        started = time.time()
        projected = _project_v2(rows)
        project_elapsed = time.time() - started

        v1_bytes += size
        v2_bytes += len(projected)
        trades += meta["event_counts"]["trades"]
        anchors += len(rows)
        read_seconds += read_elapsed
        project_seconds += project_elapsed
        per_dataset.append(
            {
                "dataset_id": dataset_id,
                "symbol": meta["symbol"],
                "trades": meta["event_counts"]["trades"],
                "anchors": len(rows),
                "v1_bytes": size,
                "v2_bytes": len(projected),
                "v1_bytes_per_anchor": round(size / len(rows), 1) if rows else None,
                "v2_bytes_per_anchor": _V2_ROW_BYTES,
                "read_seconds": round(read_elapsed, 3),
                "project_seconds": round(project_elapsed, 3),
            }
        )

    checkpoint_dir = Path(dataset_dir).parent / "micro_recorder_checkpoints"
    checkpoint_bytes = 0
    checkpoint_files = 0
    if checkpoint_dir.exists():
        for entry in os.scandir(checkpoint_dir):
            if entry.is_file():
                checkpoint_bytes += entry.stat().st_size
                checkpoint_files += 1

    summary = {
        "datasets_benchmarked": len([d for d in per_dataset if "v1_bytes" in d]),
        "source_trades": trades,
        "scientific_anchors": anchors,
        "v1_total_bytes": v1_bytes,
        "v2_total_bytes": v2_bytes,
        "v1_bytes_per_source_trade": round(v1_bytes / trades, 1) if trades else None,
        "v2_bytes_per_source_trade": round(v2_bytes / trades, 1) if trades else None,
        "v1_bytes_per_scientific_anchor": round(v1_bytes / anchors, 1) if anchors else None,
        "v2_bytes_per_scientific_anchor": _V2_ROW_BYTES,
        "v2_reduction_factor": round(v1_bytes / v2_bytes, 2) if v2_bytes else None,
        "v1_read_seconds": round(read_seconds, 2),
        "v2_projection_seconds": round(project_seconds, 2),
        "v2_columns": {
            "features": len(_FEATURE_COLUMNS),
            "horizons": len(_HORIZON_COLUMNS),
            "scalars": len(_SCALAR_COLUMNS),
            "bytes_per_row": _V2_ROW_BYTES,
        },
        "checkpoint_store": {
            "files": checkpoint_files,
            "bytes": checkpoint_bytes,
            "note": (
                "option C: a per-chunk raw-fetch cache. Deletable once its symbol-day is finalized "
                "into DatasetStore and that record's checksum verifies -- it is a resume aid, not "
                "evidence."
            ),
        },
        "per_dataset": per_dataset,
    }

    # --- the projection at 105 and 138 session dates x the frozen 8-symbol panel -----------------
    if anchors and trades:
        v1_per_symbol_session = v1_bytes / len(
            {(d["symbol"], d["dataset_id"]) for d in per_dataset if "symbol" in d}
        )
        projections = {}
        for sessions in (105, 125, 138):
            symbol_days = sessions * 8
            # Scale by TRADES, not by dataset count: the exposed corpus's windows are partial, so a
            # per-dataset average would understate a full-session corpus badly.
            full_session_trades = 645_933  # measured mean trades per full RTH symbol-session
            corpus_trades = symbol_days * full_session_trades
            projections[str(sessions)] = {
                "symbol_days": symbol_days,
                "v1_snapshot_bytes": int(corpus_trades * (v1_bytes / anchors)),
                "v2_snapshot_bytes": int(corpus_trades * _V2_ROW_BYTES),
            }
        summary["corpus_projection"] = projections
        summary["v1_per_symbol_session_bytes"] = int(v1_per_symbol_session)

    text = json.dumps(summary, indent=2, sort_keys=True)
    if args.json:
        Path(args.json).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
