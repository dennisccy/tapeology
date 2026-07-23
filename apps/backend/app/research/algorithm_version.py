"""The version of the structural COMPUTATION the derived caches in this package accelerate.

A dependency-free constants module on purpose. Every durable derived cache here
(``setups_scan_cache``, ``edge_report_cache``, ``edge_report_backtest_cache``) keys on its
INPUTS -- the bar/dataset store's own content checksums plus a whole-``Config`` content hash --
because those were the only things that could change a cached value. An ALGORITHM change moves
the answer while leaving every one of those key inputs byte-identical, so without a version in
the key a cache written before the change keeps serving results the current code would never
produce.

It lives HERE rather than in ``levels.py`` so the caches can read it without importing a
computation module: ``edge_report_cache.py`` is structurally forbidden from importing
``levels``/``tradability``/``setups``/``backtests`` (it is a rebuildable accelerator over a
caller-supplied ``compute_fn``, never a second computation path -- pinned by
``test_edge_report_cache.py``'s own coherence guard). A bare integer constant carries no
computation, so this module keeps that guarantee intact while making the caches honest.

Bump ``LEVELS_ALGORITHM_VERSION`` whenever a change to ``levels.py`` -- or to ``tradability.py`` /
``setups.py``, which are lenses over it -- makes it produce a different answer from the SAME
stored bars and the SAME ``Config``. It is folded into ``edge_report_cache._config_content_hash``,
the ONE helper all three caches already share, so a bump invalidates all of them together and
they rebuild on their next read.

  1 -> 2: one MERGED bar series per (symbol, timeframe) instead of one selected recording (the
          most-recently-created one), so every recorded window contributes to the levels, the
          tradable-map basis, and the setups scan. See ``levels.py``'s module docstring.
"""

from __future__ import annotations

LEVELS_ALGORITHM_VERSION = 2
