"""Era "The Rapid Microscope" J-02, spec section 2.4: the ONE-TIME granularity-decision benchmark.

Before ``SNAPSHOT_FORMAT_VERSION`` is frozen, this script measures THREE candidate snapshot
representations on >=2 real datasets (including the largest on disk, NVDA ``72ca8bc0``) for bytes-
on-disk amplification vs. the raw dataset, one-pass build time, and anchor-query latency:

  A. **per-event rows** -- one row for EVERY raw event (trade AND quote).
  B. **per-event sampled-at-anchors** -- one row per TRADE only (the "anchor" the whole research
     question is built around -- spec section 4's outcomes, the observer's own row model); quotes
     update internal state but never get a row of their own. This is what
     ``micro_observer.MicroObserver``/``micro_snapshots.py`` ALREADY ship as the production
     representation -- this script reuses the REAL built snapshot file directly for B's numbers
     (a second, throwaway implementation of the SAME representation would defeat the point of a
     fair comparison).
  C. **fixed-stride event blocks** -- one SUMMARY row every ``STRIDE`` raw events (first/last
     price, volume, trade count over the block), the coarsest, boundedly-sized candidate.

This is exploratory, throwaway measurement code -- not the shipped observer -- run once via
``python -m scripts.micro_snapshot_granularity_benchmark`` (or directly) against the REAL
``apps/backend/.data/datasets`` store, never through the browser-QA lane and never in the hermetic
pytest suite (module docstring rationale in ``micro_snapshots.py``). The measured table is recorded
verbatim in ``docs/handoffs/goal-rapid-microscope-iter-2-dev.md``.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import CONFIG  # noqa: E402
from app.providers.base import QuoteEvent, TradeEvent  # noqa: E402
from app.research import micro_snapshots as ms  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.micro_observer import MicroObserver  # noqa: E402

STRIDE = 200  # Rep C's fixed stride (events per summary block) -- arbitrary-but-fixed for THIS
# one-time measurement only (never a shipped constant; the winning representation's own constants
# are spec section 1's, in micro_features.py).


def _raw_dataset_bytes(dataset_dir: str, dataset_id: str) -> int:
    return (Path(dataset_dir) / f"{dataset_id}.json").stat().st_size


def _rep_a_per_event_rows(store: DatasetStore, dataset_id: str, config, out_path: Path) -> tuple[float, int]:
    """Every event gets a row: trade rows are the REAL full feature row; quote rows are a smaller
    liquidity-only projection (ts/bid/ask/sizes/quote_imbalance/microprice) -- still genuinely
    computed and written, not fabricated."""
    observer = MicroObserver(quote_size_unit="unverified")
    quote_rows: list[dict] = []

    def _on_event_wrapper(event, snapshot, _orig=observer.on_event):
        _orig(event, snapshot)
        if isinstance(event, QuoteEvent):
            imbalance = None
            microprice = None
            total = event.bid_size + event.ask_size
            if total > 0:
                imbalance = (event.bid_size - event.ask_size) / total
                microprice = (event.ask * event.bid_size + event.bid * event.ask_size) / total
            quote_rows.append(
                {
                    "ts": event.timestamp, "bid": event.bid, "ask": event.ask,
                    "bid_size": event.bid_size, "ask_size": event.ask_size,
                    "quote_imbalance": imbalance, "microprice": microprice,
                }
            )

    observer.on_event = _on_event_wrapper  # type: ignore[method-assign]
    t0 = time.time()
    for _snap in store.replay(dataset_id, config, observer=observer):
        pass
    observer.finalize()
    all_rows = sorted(observer.rows + quote_rows, key=lambda r: r["ts"] if "ts" in r else r["anchor_at"])
    with out_path.open("w") as fh:
        for row in all_rows:
            fh.write(json.dumps(row, sort_keys=True))
            fh.write("\n")
    build_seconds = time.time() - t0
    return build_seconds, len(all_rows)


def _rep_c_fixed_stride_blocks(store: DatasetStore, dataset_id: str, config, out_path: Path) -> tuple[float, int]:
    """One summary row every STRIDE raw events (trade+quote alike): first/last trade price seen in
    the block, block volume, trade count, and the block's end timestamp."""
    t0 = time.time()
    block_rows: list[dict] = []
    block_first_price: float | None = None
    block_last_price: float | None = None
    block_volume = 0
    block_trades = 0
    block_end_ts = 0.0
    n = 0
    for event in store.load_events(dataset_id):
        n += 1
        block_end_ts = event.timestamp
        if isinstance(event, TradeEvent):
            block_trades += 1
            block_volume += event.size
            if block_first_price is None:
                block_first_price = event.price
            block_last_price = event.price
        if n % STRIDE == 0:
            block_rows.append(
                {
                    "block_end_ts": block_end_ts, "first_price": block_first_price,
                    "last_price": block_last_price, "volume": block_volume, "trade_count": block_trades,
                }
            )
            block_first_price = None
            block_last_price = None
            block_volume = 0
            block_trades = 0
    if block_trades or block_volume:
        block_rows.append(
            {
                "block_end_ts": block_end_ts, "first_price": block_first_price,
                "last_price": block_last_price, "volume": block_volume, "trade_count": block_trades,
            }
        )
    with out_path.open("w") as fh:
        for row in block_rows:
            fh.write(json.dumps(row, sort_keys=True))
            fh.write("\n")
    build_seconds = time.time() - t0
    return build_seconds, len(block_rows)


def _query_latency_seconds(jsonl_path: Path, ts_key: str, probe_ts: float, trials: int = 200) -> float:
    """Anchor-query latency: load the (ts-sorted) rows once, then time ``trials`` binary searches
    for the row nearest a probe timestamp -- a fair, representation-agnostic proxy (fewer/lighter
    rows search faster)."""
    rows = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    stamps = [r[ts_key] for r in rows]
    import bisect

    t0 = time.time()
    for i in range(trials):
        probe = probe_ts * (0.2 + 0.6 * (i / max(trials - 1, 1)))
        bisect.bisect_left(stamps, probe)
    return (time.time() - t0) / trials


def benchmark_one(dataset_id: str, label: str, work_dir: Path) -> dict:
    store = DatasetStore(CONFIG.dataset_dir)
    dataset_meta = store.get(dataset_id)
    raw_bytes = _raw_dataset_bytes(CONFIG.dataset_dir, dataset_id)

    # --- Rep B: REUSE the real, already-shipped observer output (see module docstring) ---------
    snapshots_dir = ms.resolve_micro_snapshots_dir(CONFIG.dataset_dir)
    rep_b_meta = ms.load_snapshot_meta(snapshots_dir, store, dataset_id, CONFIG)
    if rep_b_meta is None:
        t0 = time.time()
        rows = ms.build_snapshot_rows(store, dataset_id, CONFIG, quote_size_unit="unverified")
        rep_b_build_seconds = time.time() - t0
        rep_b_meta = ms.write_snapshot(snapshots_dir, dataset_id, rows, {**ms.snapshot_identity(dataset_meta, CONFIG), "quote_size_unit": "unverified"})
    else:
        rep_b_build_seconds = None  # reused -- see the dev handoff for a from-scratch timing note
    rep_b_path = Path(snapshots_dir) / f"{dataset_id}.jsonl"
    rep_b_latency = _query_latency_seconds(rep_b_path, "anchor_at", dataset_meta["event_counts"]["total"])

    # --- Rep A: per-event rows ------------------------------------------------------------------
    # anchor_at exists on trade rows but not quote rows in rep A -- every row carries EITHER key.
    rep_a_path = work_dir / f"{dataset_id}.rep_a.jsonl"
    rep_a_seconds, rep_a_count = _rep_a_per_event_rows(store, dataset_id, CONFIG, rep_a_path)
    rep_a_rows = [json.loads(line) for line in rep_a_path.read_text().splitlines() if line.strip()]
    rep_a_stamps = sorted(r.get("anchor_at", r.get("ts")) for r in rep_a_rows)
    import bisect

    t0 = time.time()
    for i in range(200):
        probe = dataset_meta["event_counts"]["total"] * (0.2 + 0.6 * (i / 199))
        bisect.bisect_left(rep_a_stamps, probe)
    rep_a_latency = (time.time() - t0) / 200

    # --- Rep C: fixed-stride blocks -----------------------------------------------------------
    rep_c_path = work_dir / f"{dataset_id}.rep_c.jsonl"
    rep_c_seconds, rep_c_count = _rep_c_fixed_stride_blocks(store, dataset_id, CONFIG, rep_c_path)
    rep_c_latency = _query_latency_seconds(rep_c_path, "block_end_ts", dataset_meta["event_counts"]["total"])

    return {
        "dataset_id": dataset_id, "label": label,
        "raw_bytes": raw_bytes, "raw_events": dataset_meta["event_counts"]["total"],
        "raw_trades": dataset_meta["event_counts"]["trades"],
        "rep_a": {
            "row_count": rep_a_count, "bytes": rep_a_path.stat().st_size,
            "amplification": rep_a_path.stat().st_size / raw_bytes,
            "build_seconds": rep_a_seconds, "query_latency_seconds": rep_a_latency,
        },
        "rep_b": {
            "row_count": rep_b_meta["row_count"], "bytes": rep_b_meta["bytes_on_disk"],
            "amplification": rep_b_meta["bytes_on_disk"] / raw_bytes,
            "build_seconds": rep_b_build_seconds, "query_latency_seconds": rep_b_latency,
        },
        "rep_c": {
            "row_count": rep_c_count, "bytes": rep_c_path.stat().st_size,
            "amplification": rep_c_path.stat().st_size / raw_bytes,
            "build_seconds": rep_c_seconds, "query_latency_seconds": rep_c_latency,
        },
    }


def main() -> int:
    work_dir = Path(CONFIG.dataset_dir).parent / "micro_snapshot_benchmark_tmp"
    work_dir.mkdir(parents=True, exist_ok=True)
    targets = [
        ("72ca8bc0e5d24e40bef8d2dc6c0fe44b", "NVDA (largest, 1.97M events)"),
        ("dcfcf3cd58184c12bf2db98ed08a2bf7", "PG (14,241 events, the dense_replay_gate twin)"),
    ]
    results = [benchmark_one(dsid, label, work_dir) for dsid, label in targets]
    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
