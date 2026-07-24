"""The committed reference-window fixture load path (capability 34) — still guards the
founding-baseline data path after era-5D J-01.

era-5D J-01 ("The Clean Slate" demolition interlude, I-8 UPDATE row — a real judgment call,
documented in the dev handoff): this file used to be "the J-62 gate" — three tests ran the
committed PG SIP fixture (and a seeded sim) through the (now-demolished) journal-era replay-study
runner (``StudyJobManager``/``StudyRunner``) and asserted EXACT pinned occurrence-arming +
excursion-aggregate numbers. That computation (state-native occurrence arming, per-horizon
excursion measurement, the seeded null-baseline sweep) served NO kept surface — it was
``studies.py``'s own, and ``studies.py`` is deleted whole this iteration (I-2), including its
internal ``StudyRunner``/``_arm_occurrence``/``_measure_excursions``/``_aggregate_horizons``
machinery, none of which was part of the STATUS_*/state-native-arming-vocabulary family relocated
into ``backtests.py``. Reviving any of it just to keep those three tests' pinned numbers passing
would be un-deleting a demolished computation to satisfy a test (T-2's "never stub" spirit) rather
than a genuine kept-surface guard, so those three tests are DROPPED, not reworked.

The fourth test survives and is updated to its new import path: it proves the committed reference
fixture itself still loads correctly (symbol, trade count) via ``_load_reference_window`` — now
``datasets.py``'s own function (relocated byte-identically, era-5D J-01, I-2 RELOCATE table) — the
SAME loader ``record_from_source`` (dataset registration) and, transitively, the PnL-ledger
founding-baseline seeding CLI (``pnl_baseline.py``) still call. THIS is the "founding-baseline
data path" that remains genuinely guarded.
"""

from __future__ import annotations


def test_reference_window_fixture_loads_with_pinned_symbol_and_trade_count():
    """A cheap structural guard that the committed capability-34 fixture still loads correctly
    through its relocated loader — the SAME committed file the dense gate pins."""
    from app.research.datasets import _load_reference_window

    window = _load_reference_window()
    assert window is not None and window.symbol == "PG"
    # The fixture carries thousands of real SIP trades (the same one the dense gate asserts).
    assert len(window.trades) == 3229
