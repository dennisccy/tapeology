"""The Playbook's shared primitives (Era B2, J-01) -- ``docs/playbook-detector-spec.md`` §2's eight
functions, and NOTHING else in this module. Every detector (``desk_playbook_detect.py``, this
iteration and every later one) is built entirely out of these eight calls; a detector that needs a
ninth building block is a spec gap, not a reason to add one here quietly.

**Constant-free by design.** This module takes every threshold as a PARAMETER (``PLAYBOOK_*``
values live in ``desk_playbook.py``, the constants owner) -- so it never imports from
``desk_playbook.py`` and the dependency graph has no cycle: ``desk_playbook.py`` and
``desk_playbook_detect.py`` both import primitives FROM here, never the reverse.

**RTH is derived properly, not by a fixed UTC offset.** ``09:30``/``16:00`` are ET WALL-CLOCK
times; converting them to a UTC epoch for one session date must account for EST/EDT, so this module
resolves them via ``zoneinfo.ZoneInfo("America/New_York")`` (stdlib, Python 3.12) rather than a
hardcoded offset -- a fixture dated in June (EDT, UTC-4) and one dated in January (EST, UTC-5)
resolve to the correct epoch either way (verified against ``test_desk_forward.py``'s own
``E_OPEN = 1782135000.0`` == "2026-06-22T13:30:00Z" == 09:30 ET that day).

**Session-window extraction is attributed, not re-derived.** ``rth_session_slice`` imports
``desk_forward._session_slice`` for the day-narrowing step (the SAME bisect-based technique the
measurement rail uses to avoid a full-history scan on a ~360k-row 1m series) and applies the RTH
filter on top -- zero diff to ``desk_forward.py``, per T-8 ("the rail is imported, not forked").

**Every bar-index IS the slot.** ``rth_session_slice``'s returned list is ascending and RTH-only,
so a bar's position in that list already IS "index in the RTH 5m sequence" (spec §0's ``slot(bar)``)
-- no separate slot field is attached to the (frozen, immutable) ``RawBar`` records themselves.
"""

from __future__ import annotations

import statistics
from bisect import bisect_left
from datetime import date, datetime, time, timezone
from operator import attrgetter
from zoneinfo import ZoneInfo

from ..providers.adapters.base import RawBar
from .desk_forward import _session_slice

__all__ = [
    "rth_session_slice",
    "opening_range",
    "baselines",
    "swing_pivots",
    "consolidation_range",
    "vertical_move",
    "zone_touches",
    "market_context",
    "side_sign",
]

# Regular trading hours, ET wall-clock -- a market-structure fact, not a tunable (the
# ``desk_sessions.DESK_SESSION_ANCHOR_TIMEFRAME`` precedent: a plain structural constant, never a
# ``Config`` field, never in the playbook's own tunable-constants table).
_ET_ZONE = ZoneInfo("America/New_York")
_RTH_START = time(9, 30)
_RTH_END = time(16, 0)


def _et_epoch(session_date: str, wall_time: time) -> float:
    """The UTC epoch ``wall_time`` (ET) resolves to on ``session_date`` -- DST-correct by
    construction (``zoneinfo`` resolves the UTC offset from the local wall-clock instant given,
    never a fixed offset)."""
    day = date.fromisoformat(session_date)
    return datetime.combine(day, wall_time, tzinfo=_ET_ZONE).timestamp()


def rth_session_slice(bars: list[RawBar], session_date: str) -> list[RawBar]:
    """The session's own regular-trading-hours bars (ET 09:30 <= open < 16:00), ascending by
    epoch -- a bar's INDEX in this list is its slot (0..77 on a full day; fewer on a half-day,
    disclosed by callers as ``session_bar_count``).

    Two steps: ``desk_forward._session_slice`` narrows to the UTC calendar date (imported, not
    forked -- the SAME bisect technique that keeps a full-history read out of every call); the RTH
    hour filter then narrows the (already tiny, ~1 day's worth) result further. Bars outside RTH on
    the same UTC calendar date (pre/post-market, if ever recorded) are excluded -- the detection
    series is RTH-only per spec §0."""
    if not bars:
        return []
    window_date = date.fromisoformat(session_date)
    rth_start = _et_epoch(session_date, _RTH_START)
    rth_end = _et_epoch(session_date, _RTH_END)
    # `_session_slice`'s as_of bound is inclusive; one second past RTH close is comfortably inside
    # the UTC calendar day and still excludes nothing this module wants -- the RTH filter below is
    # the actual right boundary (strict `< rth_end`).
    day_bars = _session_slice(bars, window_date, rth_end + 1.0)
    epoch_of = attrgetter("epoch")
    start_idx = bisect_left(day_bars, rth_start, key=epoch_of)
    return [bar for bar in day_bars[start_idx:] if bar.epoch < rth_end]


def opening_range(
    bars_1m: list[RawBar],
    bars_5m: list[RawBar],
    session_date: str,
    or_minutes: int,
    min_1m_bars: int,
) -> dict | None:
    """``{"high", "low", "width", "basis": "1m"|"5m", "bars_used"}`` over ET
    ``09:30 .. 09:30+or_minutes``. At least ``min_1m_bars`` of the (up to) ``or_minutes`` one-minute
    bars on file -> the 1m basis, built from whichever of those bars actually exist; fewer -> the
    5m basis, the first ``or_minutes // 5`` five-minute bars (spec §2 primitive 2: "fall back to
    the first 3 five-minute bars" -- derived from ``or_minutes``, not a second hardcoded ``3``);
    neither on file -> ``None`` (fail-closed, disclosed by the caller as an absence).

    BOTH bases read the SAME ``09:30 .. 09:30+or_minutes`` epoch window, never "whatever the
    series happens to start with": a session whose early 5m bars are missing has no opening range
    at all, and saying so is the whole point of the null. Taking ``session_5m[:3]`` positionally
    would hand a session starting at 09:40 an "opening range" built from its 09:40/09:45/09:50
    bars, disclosed as ``basis: "5m"`` exactly like a genuine one -- a fabricated value where the
    honest answer is an absence (spec §0's fail-closed discipline; §3.1's "No 1m and no 5m OR =>
    silent symbol-session (disclosed absence)")."""
    window_end = _et_epoch(session_date, _RTH_START) + or_minutes * 60.0

    session_1m = rth_session_slice(bars_1m, session_date)
    one_min_window = [bar for bar in session_1m if bar.epoch < window_end]
    if len(one_min_window) >= min_1m_bars:
        highs = [bar.high for bar in one_min_window]
        lows = [bar.low for bar in one_min_window]
        high, low = max(highs), min(lows)
        return {"high": high, "low": low, "width": high - low, "basis": "1m", "bars_used": len(one_min_window)}

    five_min_bars_needed = or_minutes // 5
    session_5m = rth_session_slice(bars_5m, session_date)
    first_bars = [bar for bar in session_5m if bar.epoch < window_end][:five_min_bars_needed]
    if len(first_bars) >= five_min_bars_needed:
        highs = [bar.high for bar in first_bars]
        lows = [bar.low for bar in first_bars]
        high, low = max(highs), min(lows)
        return {
            "high": high, "low": low, "width": high - low, "basis": "5m",
            "bars_used": len(first_bars),
        }
    return None


def baselines(bar_store, symbol: str, session_date: str, baseline_sessions: int, min_baseline_sessions: int) -> dict:
    """``{"mbr", "sessions", "slot_volume_medians"}`` over the ``baseline_sessions`` RTH 5m
    sessions STRICTLY BEFORE ``session_date`` (entry-time legal by construction -- prior sessions
    only). ``mbr`` = median(high - low) over every RTH 5m bar of those sessions (0.0 if none);
    ``sessions`` = how many prior sessions were actually found (< ``min_baseline_sessions`` is the
    caller's fail-closed signal, per spec §0); ``slot_volume_medians`` = ``{slot: median volume}``,
    a slot present ONLY when at least ``min_baseline_sessions`` prior sessions recorded that slot
    (spec §0's RVOL denominator rule -- fewer observations and RVOL at that slot is null, never a
    thin median). The only baseline builder (spec §2 primitive 3): every RVOL and MBR in the
    playbook reads through this."""
    bars_5m = bar_store.merged_bars(symbol, "5m")
    if not bars_5m:
        return {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}
    all_dates = sorted({datetime.fromtimestamp(bar.epoch, tz=timezone.utc).date().isoformat() for bar in bars_5m})
    prior_dates = [d for d in all_dates if d < session_date][-baseline_sessions:]

    ranges: list[float] = []
    slot_volumes: dict[int, list[int]] = {}
    for prior_date in prior_dates:
        for slot, bar in enumerate(rth_session_slice(bars_5m, prior_date)):
            ranges.append(bar.high - bar.low)
            slot_volumes.setdefault(slot, []).append(bar.volume)

    slot_medians = {
        slot: statistics.median(volumes)
        for slot, volumes in slot_volumes.items()
        if len(volumes) >= min_baseline_sessions
    }
    return {
        "mbr": statistics.median(ranges) if ranges else 0.0,
        "sessions": len(prior_dates),
        "slot_volume_medians": slot_medians,
    }


def swing_pivots(bars: list[RawBar], lookback: int) -> list[dict]:
    """Every STRICT +/-``lookback``-neighbour extreme in ``bars`` -- ``{"index", "kind": "high"|
    "low", "price", "confirmed_at"}``, ``confirmed_at = index + lookback`` (the first index at
    which the pivot is knowable without lookahead: once bars through ``confirmed_at`` are visible).
    Mirrors ``levels._swing_pivots``' rule (``levels.py:325``) -- strictly greater/less than EVERY
    neighbour on BOTH sides, a tie is never a pivot, a centre needs ``lookback`` bars visible on
    each side to be checked at all -- but returns high/low SEPARATELY (``levels._swing_pivots``
    folds both into one ``SWING_PIVOT`` level type, which loses the direction this primitive's
    callers need: cup-and-handle needs swing HIGHS specifically, double-bottom needs swing LOWS).
    A plain O(n * lookback) loop -- one session is at most ~78 bars, so the vectorized apparatus
    ``levels.py`` needs for a multi-year history buys nothing here."""
    pivots: list[dict] = []
    n = len(bars)
    for i in range(lookback, n - lookback):
        left = bars[i - lookback : i]
        right = bars[i + 1 : i + 1 + lookback]
        high = bars[i].high
        low = bars[i].low
        if all(high > b.high for b in left) and all(high > b.high for b in right):
            pivots.append({"index": i, "kind": "high", "price": high, "confirmed_at": i + lookback})
        if all(low < b.low for b in left) and all(low < b.low for b in right):
            pivots.append({"index": i, "kind": "low", "price": low, "confirmed_at": i + lookback})
    return pivots


def consolidation_range(
    bars: list[RawBar], end_idx: int, min_bars: int, max_bars: int, max_range: float
) -> tuple[int, float, float] | None:
    """The MAXIMAL window ending at ``end_idx`` (length in ``[min_bars, max_bars]``) whose
    ``max(high) - min(low) <= max_range`` -- ``(start_idx, U, L)``, or ``None`` if even the
    shortest window fails. A wider window's range can only grow (never shrink), so checking lengths
    from ``max_bars`` down finds the maximal qualifying window in one pass. Shared geometry for
    JBE/DBI's base and cup-and-handle's handle (both J-04)."""
    for length in range(max_bars, min_bars - 1, -1):
        start_idx = end_idx - length + 1
        if start_idx < 0:
            continue
        window = bars[start_idx : end_idx + 1]
        u = max(bar.high for bar in window)
        l = min(bar.low for bar in window)
        if u - l <= max_range:
            return start_idx, u, l
    return None


def vertical_move(
    bars: list[RawBar],
    end_idx: int,
    n: int,
    k: float,
    direction: str,
    *,
    require_volume: bool = False,
    rvol_surge: float | None = None,
    rvols: list[float | None] | None = None,
) -> bool:
    """Did ``bars`` make a vertical move INTO ``end_idx``: net close-to-close move over the last
    ``n`` bars >= ``k`` (an ALREADY MBR-scaled absolute threshold -- this primitive takes no MBR
    itself, keeping it a plain bars-in utility) in ``direction`` ("up"/"down"), with at least
    ``n - 1`` of the ``n`` closes themselves moving that way. ``require_volume`` (only capitulation/
    euphoria, J-05, ever sets it) additionally needs the caller's own precomputed ``rvols`` (a list
    parallel to ``bars``) to show the LAST bar's RVOL >= ``rvol_surge`` and >= the FIRST bar's RVOL
    (rising) -- ``False`` whenever RVOL is unavailable (fail-closed, never a guess). Powers
    capitulation/euphoria's climax leg (J-05) and, with ``n=1`` and no volume clause, the
    spiky-approach flag (this iteration)."""
    start_idx = end_idx - n + 1
    if start_idx < 1 or end_idx >= len(bars) or start_idx > end_idx:
        return False
    sign = 1.0 if direction == "up" else -1.0
    net_move = sign * (bars[end_idx].close - bars[start_idx - 1].close)
    if net_move < k:
        return False
    closes_with = sum(
        1 for i in range(start_idx, end_idx + 1) if sign * (bars[i].close - bars[i - 1].close) > 0
    )
    if closes_with < n - 1:
        return False
    if require_volume:
        if rvols is None or rvol_surge is None:
            return False
        last_rvol, first_rvol = rvols[end_idx], rvols[start_idx]
        if last_rvol is None or first_rvol is None:
            return False
        if last_rvol < rvol_surge or last_rvol < first_rvol:
            return False
    return True


def zone_touches(bars: list[RawBar], lo: float, hi: float) -> list[int]:
    """Indices of ``bars`` touching ``[lo, hi]`` -- overlap (``bar.low <= hi and bar.high >= lo``)
    + full-exit re-arm semantics (attribution: ``desk_forward._touch_scan``, this module's own
    tiny local mirror rather than an import -- ``zone_touches`` has no side/cap/beyond-cap
    disclosure, the touch-scan concept narrowed to what the formation primitives need). Powers
    attempt counts, tested-twice-and-held range arming, and second-top support touches."""
    indices: list[int] = []
    armed = True
    for i, bar in enumerate(bars):
        inside = bar.low <= hi and bar.high >= lo
        if inside and armed:
            indices.append(i)
            armed = False
        elif not inside:
            armed = True
    return indices


def market_context(
    index_bars: list[RawBar], session_date: str, before_epoch: float, lookback_bars: int
) -> dict | None:
    """The index's own mechanical facts as of strictly before ``before_epoch`` (the trigger bar's
    own epoch, so the index's in-progress bar is never read): ``{"move": index close[t-1] - index
    close[t-1-lookback_bars], "close_before": index close[t-1], "bars_available"}``. ``None`` when
    fewer than ``lookback_bars + 1`` of the session's RTH index bars are on file before
    ``before_epoch`` -- covers BOTH "no index bars for the session at all" (an empty ``index_bars``
    list session-slices to ``[]``) and "too early in the session for the lookback window yet"
    uniformly; the caller distinguishes the two for its own disclosure reason. Direction/alignment/
    MBR-normalization are NOT computed here (this primitive has no MBR access by design) -- the
    detector combines this with its own signal's side and the index's own ``baselines()`` MBR."""
    session_bars = rth_session_slice(index_bars, session_date)
    prior = [bar for bar in session_bars if bar.epoch < before_epoch]
    if len(prior) < lookback_bars + 1:
        return None
    return {
        "move": prior[-1].close - prior[-1 - lookback_bars].close,
        "close_before": prior[-1].close,
        "bars_available": len(prior),
    }


def side_sign(side: str) -> float:
    """The playbook's OWN long/short directional multiplier: ``+1.0`` for ``"long"``, ``-1.0`` for
    ``"short"`` -- the single owner of a literal (``1.0 if side == "long" else -1.0``) that used to
    be written three separate times across ``desk_playbook.py`` (``_measure_signal`` and the
    baseline-draw branch of ``compute_playbook``) and ``desk_playbook_detect.py``
    (``_market_block``).

    **Deliberately NOT `desk_forward._side_sign`, and never imported from it.** That helper is
    built exclusively for the rail's OWN support/resistance wall vocabulary
    (``-1.0 if side == "resistance" else 1.0``): `desk_forward._side_sign("short")` returns
    ``+1.0`` (since ``"short" != "resistance"``), which would silently flip every short-side
    playbook signal's forward return and MDD sign positive -- a fabricated-data bug, not a fix.
    `desk_forward._measure_from`'s own docstring confirms ``sign`` is a caller-supplied float: each
    caller computes its OWN sign for its OWN side vocabulary, and this is the playbook's."""
    return 1.0 if side == "long" else -1.0
