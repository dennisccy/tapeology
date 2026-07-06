"""``GET /research/strategies`` (Data Contract row 40, serving side; era-4 capability 4, J-04).

Row 40 declares the strategy registry (config-owned) AND the champion pointer (store-owned) and
assigns BOTH to ONE endpoint, ``GET /research/strategies`` — mirroring ``profiles.py`` (row 33)
exactly: this module computes NOTHING of its own. It projects ``Config.strategy_registry()``
(itself built from ``Config.strategy_definition`` per registered id — the ONE registry
``POST /research/backtests``'s route validation ALSO consults, never a second allowlist) and reads
the champion pointer VERBATIM from the store — the SAME single ``JournalStore.get_champion_pointer``
source ``profiles_projection`` reads (one pointer, two read views — never a second champion source).

Disciplines locked here (identical to ``profiles.py``):
  * The registry values ARE the existing single-copy config-owned projection
    (``Config.strategy_registry()`` in ``app/config.py``) — this module carries NO second copy of
    any id string or grammar value (asserted over its source).
  * GET only — there is no write surface in this module; a strategy is registered exclusively by
    ``Config.strategy_definition`` (code, not data), and the champion moves ONLY via
    ``app/research/pnl_scan.py`` (J-06, out of scope this iteration).
  * ONE registry source: this projection and the backtest route's validation both consult
    ``Config.strategy_definition`` — never a second allowlist.
"""

from __future__ import annotations

from ..config import Config
from .store import JournalStore


def strategies_projection(store: JournalStore, config: Config) -> dict:
    """The canonical row-40 payload, computed nowhere else: the strategy registry (``v1`` plus
    ``structure_tape``, in registration order — ``config.strategy_registry()``) and the current
    champion pointer, read VERBATIM from the ONE persisted source
    (``store.get_champion_pointer()``). This module carries NO copy of any id literal or grammar
    value, and NO copy of the champion pointer's values — everything is a pure read of its two
    owners."""
    return {
        "strategies": config.strategy_registry(),
        "champion": store.get_champion_pointer(),
    }
