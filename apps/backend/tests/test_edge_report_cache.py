"""``EdgeReportCache`` (era-5B J-08) — store-level discipline, tested standalone (no FastAPI, no
real backtests): mirrors ``tests/test_bar_index.py``'s directness. Every test here feeds
``get_or_compute`` a CHEAP, counting stub instead of a real ``run_strategy_comparison_report``
sweep — the cache mechanics (keying, durability, concurrency, torn-read safety) are independent of
what ``compute_fn`` actually does, so proving them against a fast stub is both faster and a purer
isolation than routing every case through a real multi-strategy backtest. The wiring into
``edge_report.run_strategy_comparison_report`` (byte-identity against a real, non-degenerate
report; key-busting under real dataset/config changes) is covered separately in
``tests/test_edge_report.py``; the route-level DI wiring is covered in ``tests/test_edge_report_api.py``.
"""

from __future__ import annotations

import dataclasses
import json
import threading
import time

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from app.research.edge_report_cache import EdgeReportCache

WINDOW_START, WINDOW_END = "2026-01-02T14:30:00Z", "2026-01-02T14:30:05Z"


def _record(dstore: DatasetStore, ticker: str, *, split: str, price: float = 100.0) -> dict:
    """The minimal REAL ``DatasetStore.record`` public path (never hand-crafted JSON) needed to
    give a dataset a genuine, content-addressed checksum — no interesting price action is needed
    here, since these tests never run a real backtest over the recorded content."""
    events = [
        QuoteEvent(ticker, 0.0, price, price + 0.02, 800, 800),
        TradeEvent(ticker, 0.0, price + 0.02, 100, Side.UNKNOWN),
    ]
    return dstore.record(
        symbol=ticker, source=f"cache-test {ticker}", source_kind="reference", source_id=ticker,
        split=split, window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
        data_feed="sim", epoch_anchor=CONFIG.sim_session_anchor_epoch, events=events,
    )


class _CountingCompute:
    """A stub ``compute_fn`` that counts its own invocations and returns a fixed, report-shaped
    (but otherwise arbitrary) dict — never a real backtest sweep (see module docstring)."""

    def __init__(self, result: dict | None = None) -> None:
        self.calls = 0
        self._result = result if result is not None else {"train": {"cells": []}, "holdout": {"cells": []}}

    def __call__(self) -> dict:
        self.calls += 1
        return self._result


# --- cold miss -> compute once, persist both layers ------------------------------------------


def test_cold_cache_miss_calls_compute_fn_once_and_returns_its_result(tmp_path):
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    compute = _CountingCompute({"train": {"cells": ["x"]}, "holdout": {"cells": []}})

    result = cache.get_or_compute(dstore, CONFIG, compute)

    assert compute.calls == 1
    assert result == {"train": {"cells": ["x"]}, "holdout": {"cells": []}}


def test_warm_in_process_hit_never_calls_compute_fn_again(tmp_path):
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    compute = _CountingCompute()

    first = cache.get_or_compute(dstore, CONFIG, compute)
    second = cache.get_or_compute(dstore, CONFIG, compute)

    assert compute.calls == 1  # the SECOND call never recomputes
    assert first == second


def test_result_persists_to_the_durable_row_on_a_cold_miss(tmp_path):
    """The durable SQLite row exists after a cold-miss compute — proven directly against the
    table, not merely inferred from a second in-process hit (the in-process and durable layers are
    tested independently; see the durability test below for the layer that matters most)."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    db_path = str(tmp_path / "cache.db")
    cache = EdgeReportCache(db_path)
    compute = _CountingCompute({"train": {"cells": []}, "holdout": {"cells": []}})

    cache.get_or_compute(dstore, CONFIG, compute)

    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT cache_key, result_json FROM edge_report_cache").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert json.loads(rows[0][1]) == {"train": {"cells": []}, "holdout": {"cells": []}}


# --- durability across a simulated backend restart --------------------------------------------


def test_durability_across_simulated_restart_serves_prior_result_without_recompute(tmp_path):
    """The DoD's literal scenario: construct a FRESH ``EdgeReportCache`` at the SAME persisted
    path (no in-process state carried over — a genuinely new instance, the ``BarIndex``
    "delete the DB file and reproduce identical lookups" precedent, applied to "restart the
    process and reproduce the identical warm report")."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    db_path = str(tmp_path / "cache.db")

    warm_result = {"train": {"cells": ["real-shape"]}, "holdout": {"cells": []}}
    original = EdgeReportCache(db_path)
    original_compute = _CountingCompute(warm_result)
    original.get_or_compute(dstore, CONFIG, original_compute)
    assert original_compute.calls == 1

    # Simulate a backend restart: a BRAND NEW instance, no in-process state carried over.
    restarted = EdgeReportCache(db_path)
    restarted_compute = _CountingCompute({"should": "never be returned"})

    served = restarted.get_or_compute(dstore, CONFIG, restarted_compute)

    assert served == warm_result
    assert restarted_compute.calls == 0  # never recomputed — served from the durable row alone


def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
    layer byte-identically (``json.dumps(..., sort_keys=True)`` equality) — the exact equality
    discipline the determinism DoD requires."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    db_path = str(tmp_path / "cache.db")
    original_result = {
        "train": {"cells": [{"n": 3, "net_r": 5.050000000001056, "win_rate": None, "tags": [1, 2, 3]}]},
        "holdout": {"cells": []},
        "surviving_train_cells": [],
    }
    EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute(original_result))

    reloaded = EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute())

    assert json.dumps(reloaded, sort_keys=True) == json.dumps(original_result, sort_keys=True)


def test_result_key_order_is_preserved_through_the_durable_round_trip_not_merely_content_equal(tmp_path):
    """Byte-identity needs MORE than content equality: FastAPI/Starlette serializes a route's
    returned dict in its NATURAL insertion order (never alphabetically), so a durable-cache-hit
    response must reconstruct the SAME key order as the original fresh dict — not merely equal
    content under a sorted comparison. Deliberately picks a top-level key ("register") that would
    sort to a DIFFERENT position than its declared one, so a stray ``sort_keys=True`` anywhere on
    the stored blob would flip this test red (this is the exact regression
    ``tests/test_mcp_server.py``'s raw-bytes REST/MCP-proxy comparison caught for real)."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    db_path = str(tmp_path / "cache.db")
    original_result = {
        "register": "z-would-sort-last-if-broken",
        "pnl_min_sample_size": 5,
        "train": {"cells": []},
        "holdout": {"cells": []},
        "surviving_train_cells": [],
    }
    EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute(original_result))

    reloaded = EdgeReportCache(db_path).get_or_compute(dstore, CONFIG, _CountingCompute())

    assert list(reloaded.keys()) == list(original_result.keys())
    assert json.dumps(reloaded) == json.dumps(original_result)  # NO sort_keys -- true wire-byte identity


# --- key-busting: dataset set, strategy registry, config_fingerprint, and the catch-all -------


def test_adding_a_dataset_busts_the_cache(tmp_path):
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, CONFIG, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_removing_a_dataset_busts_the_cache(tmp_path):
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    meta_b = _record(dstore, "SYN-B", split=SPLIT_HOLDOUT)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    (tmp_path / "datasets" / f"{meta_b['id']}.json").unlink()
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, CONFIG, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_strategy_registry_affecting_field_busts_the_cache(tmp_path):
    """A ``structure_tape_*`` field change (``config_fingerprint``-EXCLUDED, per config.py's own
    documented rationale — arming-only, never fingerprinted) still changes
    ``config.strategy_registry()``'s own output, so the cache must bust on it regardless."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    changed_config = dataclasses.replace(
        CONFIG, structure_tape_proximity_band_bps=CONFIG.structure_tape_proximity_band_bps + 1.0
    )
    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, changed_config, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_config_fingerprint_affecting_field_busts_the_cache(tmp_path):
    """A field that DOES move ``config_fingerprint()`` (and is unrelated to the strategy registry)
    busts the cache too — proof the fingerprint component is genuinely load-bearing, not merely
    subsumed."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    changed_config = dataclasses.replace(
        CONFIG, backtest_null_entry_count=CONFIG.backtest_null_entry_count + 1
    )
    assert changed_config.config_fingerprint() != CONFIG.config_fingerprint()  # sanity: fingerprinted
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, changed_config, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_pnl_min_sample_size_change_busts_the_cache_despite_fingerprint_exclusion(tmp_path):
    """``pnl_min_sample_size`` is EXCLUDED from ``config_fingerprint()`` (config.py's own
    documented "serving/presentation-only... two journals... MUST share a fingerprint"
    rationale) AND is not read by ``strategy_registry()`` — yet it directly gates every cell's own
    ``insufficient_sample`` label inside ``edge_report.py``'s ``_split_cells``. This is exactly the
    gap the module docstring's "why four parts" section documents; the whole-config-content
    catch-all component is what catches it."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    changed_config = dataclasses.replace(CONFIG, pnl_min_sample_size=CONFIG.pnl_min_sample_size + 1)
    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
    assert changed_config.strategy_registry() == CONFIG.strategy_registry()  # sanity: unaffected
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, changed_config, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_tradability_field_change_busts_the_cache_despite_fingerprint_exclusion(tmp_path):
    """``tradability_band_cap_per_side`` is ALSO ``config_fingerprint``-excluded (the "separate
    research computation" rationale) but genuinely changes what ``compute_setups`` (hence this
    report's cells) can resolve — the identical gap ``pnl_min_sample_size`` proves above, for the
    other named family (``sr_*`` / ``tradability_*`` / ``setups_*``)."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    changed_config = dataclasses.replace(
        CONFIG, tradability_band_cap_per_side=CONFIG.tradability_band_cap_per_side + 1
    )
    assert changed_config.config_fingerprint() == CONFIG.config_fingerprint()  # sanity: excluded
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, changed_config, second)

    assert second.calls == 1
    assert result == {"v": 2}


def test_unchanged_inputs_reuse_the_cache_across_a_fresh_config_object_with_equal_values(tmp_path):
    """The counter-proof: a fresh ``dataclasses.replace(CONFIG)`` with NO field actually changed
    (a new Python object, equal content) must still HIT — the key is content-based, never
    ``id(config)``-based (unlike ``setups.py``'s in-process-only ``_SCAN_CACHE``, which this
    module's own docstring explains cannot be reused here because it would not survive a restart)."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    cache.get_or_compute(dstore, CONFIG, _CountingCompute({"v": 1}))

    equal_but_distinct_config = dataclasses.replace(CONFIG)
    assert equal_but_distinct_config is not CONFIG
    second = _CountingCompute({"v": 2})
    result = cache.get_or_compute(dstore, equal_but_distinct_config, second)

    assert second.calls == 0  # never recomputed — content-equal, so still a hit
    assert result == {"v": 1}


# --- store-integrity failures bypass the cache entirely ----------------------------------------


def test_store_integrity_error_bypasses_the_cache_and_persists_nothing(tmp_path):
    dstore = DatasetStore(tmp_path / "datasets")
    meta = _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    path = tmp_path / "datasets" / f"{meta['id']}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))
    db_path = str(tmp_path / "cache.db")
    cache = EdgeReportCache(db_path)

    class _Boom(Exception):
        pass

    def _raising_compute():
        raise _Boom("the real EdgeReportError path, standing in for it here")

    with pytest.raises(_Boom):
        cache.get_or_compute(dstore, CONFIG, _raising_compute)

    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT * FROM edge_report_cache").fetchall()
    finally:
        conn.close()
    assert rows == []  # nothing persisted on the integrity-error bypass path


# --- concurrency / torn-read (mirrors test_setups.py's atomic-publish guard) --------------------


def test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair(tmp_path):
    """Many threads racing a COLD cache (nothing published yet, neither in-process nor durable)
    with a deliberately widened publish window (a sleep injected into ``compute_fn``, forcing
    genuine overlap around the moment the winning thread's result would be published) must ALL
    return a real, non-``None``, byte-identical result — never a crash, never a torn key/result
    pairing. Mirrors ``tests/test_setups.py``'s
    ``test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair`` exactly (same
    barrier-based pattern), applied to ``EdgeReportCache`` instead of the module-level
    ``_SCAN_CACHE``."""
    dstore = DatasetStore(tmp_path / "datasets")
    _record(dstore, "SYN-A", split=SPLIT_TRAIN)
    cache = EdgeReportCache(str(tmp_path / "cache.db"))
    fixed_result = {"train": {"cells": [{"n": 5, "net_r": 1.23456789}]}, "holdout": {"cells": []}}

    def _slow_compute() -> dict:
        time.sleep(0.05)  # widen the window so concurrent callers genuinely overlap the publish
        return fixed_result

    thread_count = 16
    results: list[dict | None] = [None] * thread_count
    errors: list[BaseException] = []
    start_barrier = threading.Barrier(thread_count)

    def _call(index: int) -> None:
        start_barrier.wait()  # every thread reaches get_or_compute at roughly the same instant
        try:
            results[index] = cache.get_or_compute(dstore, CONFIG, _slow_compute)
        except BaseException as exc:  # pragma: no cover -- failure path only
            errors.append(exc)

    threads = [threading.Thread(target=_call, args=(i,)) for i in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert errors == [], f"a concurrent cold-cache read raised (never a torn read, never a crash): {errors}"
    assert all(r is not None for r in results), (
        "every concurrent caller must return a real result -- a None here IS the torn-read bug"
    )
    expected = json.dumps(results[0], sort_keys=True)
    assert all(json.dumps(r, sort_keys=True) == expected for r in results), (
        "every concurrent caller must observe the SAME byte-identical result -- a mismatch would "
        "mean some reader saw a torn/partial key-result pairing"
    )
    assert results[0] == fixed_result


# --- coherence: this module never computes a research value itself -----------------------------


def test_cache_source_never_computes_a_research_value_itself():
    """A coherence guard (the ``test_3way_report_source_reuses_the_shared_aggregate_and_never_a_
    second_edge_formula`` precedent in ``test_edge_report.py``, applied to this module): the cache
    never IMPORTS the backtest runner, the aggregate formula, or the setups/tradability scanners —
    it is a rebuildable accelerator over a caller-supplied ``compute_fn``, never a second
    computation path. Checked as IMPORT statements specifically (never a bare substring scan):
    the module docstring legitimately names these functions in prose to explain what this module
    accelerates, so a substring-anywhere check would false-positive on its own documentation —
    an absent import is the true structural proof this module cannot call them at all (Python
    would raise ``NameError`` otherwise)."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "app" / "research" / "edge_report_cache.py").read_text()
    for forbidden_import in (
        "from .backtests import", "from .setups import", "from .tradability import",
        "from .levels import", "from ..engine.tape_engine import", "from ..engine import",
        "import app.research.backtests", "import app.research.setups",
    ):
        assert forbidden_import not in src, (
            f"a second computation path leaked into edge_report_cache.py: {forbidden_import}"
        )
