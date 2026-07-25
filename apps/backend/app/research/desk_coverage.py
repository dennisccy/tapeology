"""Per-member x per-timeframe bar coverage over the latest universe snapshot (Era B "The Desk",
Key Capability 2, J-02) -- the Product Shape's "Per-member bar coverage/freshness" row's ONE owner,
served by ``GET /research/desk/coverage``.

THIS MODULE computes NOTHING about bars themselves -- it is a pure READ over two already-canonical
owners: the latest registered universe snapshot (``desk_universe.UniverseStore`` -- membership,
J-01) and the durable bar-lookup index (``bar_index.BarIndex`` -- coverage/freshness, era-5 J-03).
T-4 (goal.md's build anchors): coverage is read from ``bar_index`` ONLY, via
``BarIndex.coverage()`` (a single indexed ``COUNT``+``MAX`` query per pair) -- it NEVER walks or
re-hashes the checksummed JSON ``BarStore`` (the era-5C 31.4s mistake this anchor exists to avoid).

**The pinned top-up timeframe set.** ``DESK_TOPUP_TIMEFRAMES`` is a plain structural constant (the
``levels.PRIOR_PERIOD_TIMEFRAMES`` precedent) -- NOT a ``Config`` field, since it is derived
entirely from the existing frozen contract rather than a new tunable knob. Re-verified live against
the tree this iteration (goal-desk-iter-2 spec NOTES): ``Config.bar_timeframes``
(``config.py:770``, the full 9-entry validation allowlist) intersected with what the Yahoo adapter
actually serves (``providers/adapters/yahoo.py``'s ``_INTERVAL_MAP``, 5 direct entries -- ``1d``,
``1w``, ``1h``, ``5m``, ``1m`` -- plus the locally-resampled ``4h``; ``8h``/``15m``/``1mo`` raise
``UnsupportedTimeframe``) and further narrowed to the non-intraday-microscope subset a DAILY-CLOSE
screen needs (excluding ``5m``/``1m`` per the desk-era's own explicit "no 5m/1m in the desk top-up"
acceptance text; ``levels.PRIOR_PERIOD_TIMEFRAMES`` / ``config.py``'s ``sr_timeframe_weights``,
``config.py:821``, confirm ``1d``/``1w`` are the long-term bucket these four timeframes feed) --
leaving exactly ``{"1h", "4h", "1d", "1w"}``.

**Honest empty.** Before any universe snapshot is ever registered, ``get_desk_coverage`` returns
the SAME honest-empty shape ``GET /research/desk/universe`` uses (``universe_snapshot_id: None``,
``members: []``) -- HTTP 200, never 404 or a fabricated row (mirrors J-01's own convention)."""

from __future__ import annotations

from .bar_index import BarIndex
from .desk_universe import UniverseStore

# The desk top-up's pinned timeframe set -- see module docstring for the full citation trail.
# Order is the fixed iteration order both this module and ``desk_topup_compute.py`` use.
DESK_TOPUP_TIMEFRAMES: tuple[str, ...] = ("1h", "4h", "1d", "1w")


def get_desk_coverage(universe_store: UniverseStore, bar_index: BarIndex) -> dict:
    """The latest universe snapshot's per-member x per-``DESK_TOPUP_TIMEFRAMES`` coverage, read
    ENTIRELY from ``bar_index`` (T-4). Shape (Data-contract addition #1, goal-desk-iter-2 spec):
    ``{"universe_snapshot_id": str | None, "timeframes": [...], "members": [{"symbol": str,
    "per_timeframe": {"<tf>": {"has_bars": bool, "latest_window_end_utc": str | None}}}]}``.

    Honest empty (``universe_snapshot_id: None``, ``members: []``) before any universe snapshot
    has ever been registered -- the caller (the route) serves this as an HTTP 200, never a 404
    (mirrors ``get_universe``'s convention, ``desk_routes.py``)."""
    records, _errors = universe_store.list()
    timeframes = list(DESK_TOPUP_TIMEFRAMES)
    if not records:
        return {"universe_snapshot_id": None, "timeframes": timeframes, "members": []}

    latest = records[-1]
    members: list[dict] = []
    for symbol in latest["members"]:
        per_timeframe: dict[str, dict] = {}
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            has_bars, latest_window_end_utc = bar_index.coverage(symbol, timeframe)
            per_timeframe[timeframe] = {
                "has_bars": has_bars,
                "latest_window_end_utc": latest_window_end_utc,
            }
        members.append({"symbol": symbol, "per_timeframe": per_timeframe})

    return {
        "universe_snapshot_id": latest["id"],
        "timeframes": timeframes,
        "members": members,
    }
