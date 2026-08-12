"""``scripts/seed_playbook_iter8_replay_rig.py`` -- a smoke check for the goal-playbook-iter-10 fix:
the scoped QA rig's OWN ``bar_index.db`` gains entries for the kept-symbol (AAPL) bar files
``_copy_kept_symbol_series`` copies from the operator's real store, closing the iter-9 blank-
``/structure``-chart evidence gap (a raw ``shutil.copy2`` alone never updated the index, and
``GET /research/bars?symbol=...`` -- what ``/structure``'s chart fetches -- resolves a ``symbol=``
filter through ``BarIndex.list()``, so an unindexed copy stayed invisible to that filtered read).

Not a re-test of ``desk_index_reconcile.py`` itself (already covered end to end by
``test_desk_index_reconcile.py``, its own hermetic ``classify_drift``/``run_reconcile`` suite) --
this file only proves the SCRIPT wires the existing repair path in after its own copy step, using
the ``sys.path`` insertion pattern ``test_record_event_windows.py`` already established for
importing a ``scripts/`` module directly in a test."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import seed_playbook_iter8_replay_rig as driver  # noqa: E402

from app.providers.adapters.base import RawBar  # noqa: E402
from app.research.bar_index import BarIndex  # noqa: E402
from app.research.bars import BarStore  # noqa: E402

E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET


def _aapl_bars() -> list[RawBar]:
    return [
        RawBar("AAPL", "5m", E_OPEN + i * 300.0, 100.0, 101.0, 99.0, 100.5, 1000) for i in range(6)
    ]


def test_copy_kept_symbol_series_alone_leaves_a_fresh_index_blind_to_the_copy(tmp_path):
    """The bug, isolated: copying AAPL's bar file verbatim does NOT, by itself, update a fresh
    ``bar_index.db`` -- confirms the exact gap the fix closes, not just its repair."""
    real_bar_dir = tmp_path / "real_bars"
    scoped_bar_dir = tmp_path / "scoped_bars"
    scoped_bar_dir.mkdir()
    BarStore(real_bar_dir).record(
        symbol="AAPL", timeframe="5m",
        window_start_utc="2026-06-22T00:00:00Z", window_end_utc="2026-06-22T23:59:59Z",
        feed="test", bars=_aapl_bars(),
    )

    copied = driver._copy_kept_symbol_series(scoped_bar_dir, real_bar_dir)
    assert copied == 1
    assert list(scoped_bar_dir.glob("*.json"))  # the file really is physically present

    fresh_index = BarIndex(str(tmp_path / "index_never_reconciled.db"))
    assert fresh_index.list() == []  # ... yet unindexed


def test_reindex_copied_series_leaves_the_scoped_bar_index_with_aapl_entries(tmp_path):
    """goal-playbook-iter-10: ``main()``'s own post-copy step -- ``_reindex_copied_series`` calling
    ``desk_index_reconcile.run_reconcile`` through the resolved ``bar_index.db`` -- repairs exactly
    the gap the test above demonstrates, without mutating any bar file content."""
    real_bar_dir = tmp_path / "real_bars"
    scoped_bar_dir = tmp_path / "scoped_bars"
    scoped_bar_dir.mkdir()
    real_store = BarStore(real_bar_dir)
    real_store.record(
        symbol="AAPL", timeframe="5m",
        window_start_utc="2026-06-22T00:00:00Z", window_end_utc="2026-06-22T23:59:59Z",
        feed="test", bars=_aapl_bars(),
    )
    real_records, _errors = real_store.list(include_bars=False)
    before_checksum = real_records[0]["checksum"]

    driver._copy_kept_symbol_series(scoped_bar_dir, real_bar_dir)
    scoped_store = BarStore(scoped_bar_dir)
    scoped_index = BarIndex(str(tmp_path / "scoped_index.db"))

    result = driver._reindex_copied_series(scoped_store, scoped_index)

    assert result["rows_indexed_before"] == 0
    assert result["rows_indexed_after"] == 1
    assert result["aborted"] is False

    hits = scoped_index.list(symbol="AAPL")
    assert len(hits) == 1
    assert hits[0].series_id == real_records[0]["id"]

    # Read-only on content: the copied file's own checksum, re-verified through the scoped store
    # after reindexing, is byte-unchanged from the real store's original.
    scoped_records, _errors = scoped_store.list(include_bars=False)
    assert scoped_records[0]["checksum"] == before_checksum


def test_reindex_copied_series_is_a_noop_when_nothing_was_copied(tmp_path):
    """``main()`` only calls the repair when ``_copy_kept_symbol_series`` actually copied
    something (the fresh-clone case, where no real store exists, needs nothing to index) -- proven
    directly against an empty scoped store rather than by reading ``main()``'s own branch."""
    scoped_store = BarStore(tmp_path / "scoped_bars")
    scoped_index = BarIndex(str(tmp_path / "scoped_index.db"))

    result = driver._reindex_copied_series(scoped_store, scoped_index)

    assert result["rows_indexed_before"] == 0
    assert result["rows_indexed_after"] == 0
    assert scoped_index.list() == []
