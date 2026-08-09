"""The tradable level map (era-5B capability 1, J-01) -- Data Contract row "Tradable level map --
bands"'s SOLE owner.

THIS MODULE is a LENS over the frozen ``research/levels.py`` computation, never a second levels
engine: it consumes ``compute_levels``'s output (the ``levels`` list AND ``confluence_zones``)
VERBATIM -- no pivot/extreme re-detection, no second bar-windowing for level discovery, no touch
to ``levels.py``'s 5 bps (``sr_touch_tolerance_bps``) / 20 bps (``sr_confluence_band_bps``)
parameters. It reads stored bars itself for exactly two, narrowly-scoped reasons: (a)
**morning-markup as-of resolution** (finding the prior completed session from the stored DAILY
series) and (b) **price-scale context** (the current reference price for support/resistance side
classification, plus a recency scan over the SAME daily series already read for (a) -- no new bar
read is opened for recency).

``GET /research/tradability`` and the read-only MCP ``tradability`` tool both serve this module's
output VERBATIM (single source of truth -- no second computation path, mirroring ``levels.py``'s
own MCP/REST discipline).

**Morning-markup as-of resolution.** For a requested ``as_of`` inside a session, the basis is the
last COMPLETED daily bar strictly before the requested session's own UTC calendar date (holidays
and weekends are handled for free -- no hardcoded calendar, since a missing daily bar simply is
not a candidate). ``compute_levels`` is handed TWO things: an as-of epoch of that prior bar's own
epoch plus one calendar day (``_ONE_DAY_SECONDS`` -- the SAME structural period-closing convention
``levels.py``'s own ``_prior_period_extremes`` uses for ``"1d"``), so the prior session's own
high/low/close become usable levels (goal.md: "the 2026-06-18 close ... already contained
rejection highs ... 300.57"); and a READ-ONLY view (``_PriorSessionBarView``) over the store that
filters every loaded bar, on every timeframe, to ``epoch <= prior_bar.epoch``.

That second part is NOT redundant with the first. Real daily bars from the SAME vendor are stamped
at a consistent hour-of-day, so for any two CONSECUTIVE trading sessions, "the prior bar's epoch
plus one day" lands EXACTLY on the requested session's own bar epoch, if one is already stored (the
normal state for a fully-fetched historical series). ``levels.py``'s own ``_bars_as_of`` uses a
single inclusive ``<=`` threshold for both "is this bar visible at all" and "has this bar's period
closed" -- so an as-of value chosen to satisfy the second question can, unavoidably given that
frozen, un-modifiable comparison, also satisfy the first for any bar sitting at that exact epoch.
That bar can never itself become a fabricated level (a bar at the very end of the visible window
still needs future confirmation on both sides to register as a swing pivot) -- but it CAN falsely
unlock the bar just before it, letting THAT prior bar be checked as a swing-pivot centre using the
requested session's own bar as its right-hand neighbour, silently changing the prior bar's own
registered levels. ``_PriorSessionBarView`` closes that gap by bounding bar visibility itself, so
the as-of epoch's only remaining job is closing ``prior_bar``'s own period -- this is this module's
own SECOND, deliberate truncation surface, layered in front of ``levels.py``'s frozen one
specifically to cover the case its single inclusive threshold cannot express on its own.

**Band clustering.** The as-of-resolved ``levels`` list is split into two sides by the prior
session's own CLOSE price (levels priced above it are resistance candidates, at-or-below are
support candidates -- a plain comparison, never a re-detection of structure), then each side is
clustered independently by an ANCHOR-FIXED scan over ascending price (the identical TECHNIQUE
``levels.py``'s own ``_cluster_levels`` uses for confluence zones, reused as a technique only --
this module imports no clustering code from ``levels.py``) at a config-owned, wider, price-scale-
aware tolerance (``Config.tradability_band_width_bps``) than the raw confluence band: a tradable
band is deliberately coarser, built to merge nearby REAL rejection highs (the pinned AAPL cluster
spans 300.48 to 302.07, roughly 53 bps apart) into ONE wall a trader would mark, not several
adjacent lines. Every level is assigned to exactly one band (no level is silently dropped before
scoring); at most ``Config.tradability_band_cap_per_side`` bands per side survive, ranked by
quality score -- so the served map is never more than ``2 * tradability_band_cap_per_side`` bands
total (``<= 10`` at the config-owned default cap of 5).

**Quality scoring** (config-owned weights, ``Config.tradability_quality_weights``) sums four
factors: distinct-timeframe breadth among the band's member levels, the **daily** touch count (the
sum of each ``"1d"`` member's own ``touch_count`` -- goal.md's factor is "daily touch count", never
a sum across every timeframe: a band can hold dozens of intraday 5m/1h members whose combined touch
volume near the current price would otherwise drown a genuine multi-day rejection wall; intraday
members still count toward breadth but not toward this daily total -- all ``touch_count`` values are
already computed by ``levels.py``, never re-counted from bars), a recency score (0..1, the position
-- among the as-of-truncated daily bars already read for basis resolution -- of the MOST RECENT bar
whose high/low range intersects the band, or 0.0 if none does), and a round-number flag
(config-owned increment + tolerance, e.g. 300 flagged at the default 50-point increment). No factor
re-derives a level or a zone; every input is either a member level's own field or a plain scan over
bars already read for another named purpose.

**Class inheritance.** A band's A/B/C ``class`` is a PROJECTION of its best overlapping confluence
zone from ``compute_levels``'s ``confluence_zones`` (goal.md: "inherits the band class from its
best member zone ... class stays owned by levels.py -- no re-grading") -- a zone "overlaps" a band
when at least one zone member level's price falls inside the band's own ``[price_low, price_high]``
range; "best" is the highest class (A > B > C), tie-broken by the zone's own score. A band with no
overlapping zone honestly carries ``class: null`` -- never a fabricated/defaulted grade ``levels.py``
itself never assigned.

**Deterministic + honest.** Pure function of the store's stored bars + config: identical inputs
produce byte-identical output (every collection is sorted by an explicit total order; no
wall-clock, no unseeded randomness). Two honest empty states, mirroring ``levels.py``'s own
``no_bar_series_for_symbol`` precedent: a symbol with NO recorded bar series at all (any timeframe)
sets ``no_bar_series_for_symbol: true``; a symbol WITH series but nothing derivable at the resolved
as-of (no daily series to resolve a basis from at all, or a daily series exists but no session
strictly precedes the requested one) reports ``false`` with an empty ``bands`` list and
``basis_as_of: null`` -- never a fabricated band. Once a basis DOES resolve, ``compute_levels``
always contributes at least that prior session's own high/low/close, so a resolved basis with zero
bands is not a state this module can reach -- no branch exists to fabricate one.
"""

from __future__ import annotations

from bisect import bisect_left
from datetime import datetime, timezone
from operator import itemgetter

from ..config import Config
from ..providers.adapters.base import RawBar
from .bars import BarStore
from .levels import compute_levels

SUPPORT = "support"
RESISTANCE = "resistance"

# One calendar day in seconds -- a STRUCTURAL calendar fact (mirrors ``levels.py``'s own
# ``_PERIOD_SECONDS["1d"]``), not a tunable research parameter, so it is deliberately NOT a
# ``Config`` field (the identical ``levels.py`` rationale for its own period-length constant).
_ONE_DAY_SECONDS = 86400.0

# The DAILY timeframe identifier -- a STRUCTURAL identifier (mirrors ``levels.py``'s own literal
# ``"1d"`` in ``PRIOR_PERIOD_TIMEFRAMES`` / ``_PERIOD_SECONDS``), not a tunable research parameter,
# so it is deliberately NOT a ``Config`` field. It names the ONE timeframe whose touches the
# ``touch_count`` quality factor counts -- goal.md's factor is "DAILY touch count", verbatim (see
# ``_quality_score``), never a sum across every timeframe.
_DAILY_TIMEFRAME = "1d"

_CLASS_RANK: dict[str, int] = {"A": 3, "B": 2, "C": 1}


def _iso(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _session_date(epoch: float):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).date()


class _PriorSessionBarView:
    """A read-only, duck-typed view over a real ``BarStore`` (implements the methods
    ``compute_levels`` calls: ``list()``, ``merged_bars()`` -- and ``load_bars()`` for any
    per-series reader) that filters every loaded bar, on EVERY timeframe, to
    ``epoch <= cutoff_epoch`` -- see the module docstring's "morning-markup as-of resolution"
    section for why this second truncation surface is necessary alongside the as-of epoch.
    ``list()`` is delegated unchanged (which TIMEFRAMES a symbol has recordings for must stay
    identical to an unfiltered read; only bar CONTENT is bounded). Never writes anything --
    ``record`` is not implemented, so a coding error that tried to persist through this view
    would fail loudly, never silently.

    ``merged_bars`` MUST be bounded here, not just ``load_bars``: it is the accessor
    ``compute_levels`` actually reads bars through, so leaving it delegated would hand the level
    computation the unbounded history this view exists to withhold."""

    def __init__(self, store: BarStore, cutoff_epoch: float) -> None:
        self._store = store
        self._cutoff_epoch = cutoff_epoch

    def list(self, *, include_bars: bool = True) -> tuple[list[dict], list[dict]]:
        return self._store.list(include_bars=include_bars)

    def load_bars(self, bar_series_id: str) -> list[RawBar]:
        return [b for b in self._store.load_bars(bar_series_id) if b.epoch <= self._cutoff_epoch]

    def merged_bars(self, symbol: str, timeframe: str) -> list[RawBar]:
        return [
            b for b in self._store.merged_bars(symbol, timeframe) if b.epoch <= self._cutoff_epoch
        ]


def _select_daily_series(store: BarStore, symbol: str) -> tuple[list[RawBar] | None, bool]:
    """Returns ``(merged_daily_bars_or_None, has_any_series_for_symbol)``. Reads the ``"1d"``
    bars through the EXACT SAME accessor ``compute_levels`` itself reads them through
    (``BarStore.merged_bars`` -- every recording for the pair folded into one ascending series,
    de-duplicated by timestamp), so this module and ``compute_levels`` always see the identical
    daily history and the ``prior_bar`` this resolves is guaranteed to be a bar ``compute_levels``
    itself reads (never an independently-selected recording).

    ``None`` -- with ``has_any_series_for_symbol`` still ``True`` -- when ``symbol`` has
    recordings but none on the daily timeframe: no basis is derivable, an honest state distinct
    from "no series at all" (see ``compute_tradability``)."""
    # ``include_bars=False``: this enumeration reads only ``symbol``/``timeframe`` — the bars
    # themselves are then read through ``merged_bars`` below, exactly as before.
    records, _integrity_errors = store.list(include_bars=False)
    matching_any = [r for r in records if r["symbol"] == symbol]
    if not matching_any:
        return None, False
    if not any(r["timeframe"] == _DAILY_TIMEFRAME for r in matching_any):
        return None, True
    return store.merged_bars(symbol, _DAILY_TIMEFRAME), True


def _resolve_basis(daily_bars: list[RawBar], as_of_epoch: float) -> tuple[float, RawBar] | None:
    """The morning-markup basis: the last COMPLETED daily bar strictly before the requested
    session's own UTC calendar date, plus the resolved as-of epoch to feed ``compute_levels`` (that
    bar's own epoch + one day -- see module docstring). ``None`` when no prior session exists in
    the store (honest empty state, never a fabricated basis)."""
    requested_date = _session_date(as_of_epoch)
    candidates = [
        b for b in daily_bars if b.epoch <= as_of_epoch and _session_date(b.epoch) < requested_date
    ]
    if not candidates:
        return None
    prior_bar = max(candidates, key=lambda b: b.epoch)
    return prior_bar.epoch + _ONE_DAY_SECONDS, prior_bar


def _cluster_side(levels: list[dict], band_width_bps: float) -> list[list[dict]]:
    """Anchor-fixed scan over ascending price -- the identical TECHNIQUE ``levels.py``'s own
    ``_cluster_levels`` uses for confluence zones (reused as a technique only; no import of, or
    call into, that function), at this module's own wider, config-owned tolerance. Unlike
    ``_cluster_levels`` (which drops singleton levels -- confluence requires >= 2 members), EVERY
    level here joins exactly one band, including size-1 bands: this lens exists to distill via
    scoring + the top-K cap below, never by silently discarding input before scoring."""
    ordered = sorted(levels, key=itemgetter("price", "timeframe", "type"))
    bands: list[list[dict]] = []
    current: list[dict] = []
    anchor = 0.0
    tolerance = 0.0
    for level in ordered:
        if current and abs(level["price"] - anchor) <= tolerance:
            current.append(level)
            continue
        if current:
            bands.append(current)
        anchor = level["price"]
        tolerance = anchor * (band_width_bps / 10_000.0)
        current = [level]
    if current:
        bands.append(current)
    return bands


def _round_number_flag(price_low: float, price_high: float, increment: float, tolerance_bps: float) -> bool:
    """True iff either band edge sits within ``tolerance_bps`` of a multiple of ``increment`` --
    checking BOTH edges (never just the low, never just a computed midpoint that might itself not
    be a real level) keeps this an honest read of the band's own real boundaries."""
    for price in (price_low, price_high):
        nearest_multiple = round(price / increment) * increment
        tolerance = price * (tolerance_bps / 10_000.0)
        if abs(price - nearest_multiple) <= tolerance:
            return True
    return False


def _recency_score(daily_bars: list[RawBar], price_low: float, price_high: float) -> float:
    """0.0..1.0: the position (1-indexed, normalized by total count) of the MOST RECENT bar (among
    the already as-of-truncated ``daily_bars``) whose high/low range intersects
    ``[price_low, price_high]``. 0.0 when no bar touches -- an honest "never recently touched",
    never a fabricated score. A plain range-intersection scan over bars already read for basis
    resolution -- not a re-detection of any level."""
    if not daily_bars:
        return 0.0
    last_touch_index: int | None = None
    for index, bar in enumerate(daily_bars):
        if bar.low <= price_high and bar.high >= price_low:
            last_touch_index = index
    if last_touch_index is None:
        return 0.0
    return (last_touch_index + 1) / len(daily_bars)


def _best_zone_class(zones: list[dict], price_low: float, price_high: float) -> str | None:
    """The band's inherited class: the highest-graded (tie-broken by score) confluence zone with
    at least one member level priced inside ``[price_low, price_high]`` -- ``None`` when no zone
    overlaps (an honest absence; ``levels.py`` itself never graded anything here, so this module
    never invents a grade).

    THE reference definition of class inheritance. ``_ZoneClassIndex`` below answers the identical
    question with a per-zone binary search instead of this full member walk, so the two always
    agree band-for-band (``tests/test_tradability.py`` pins that equivalence)."""
    best_class: str | None = None
    best_key: tuple[int, float] | None = None
    for zone in zones:
        if not any(price_low <= member["price"] <= price_high for member in zone["levels"]):
            continue
        key = (_CLASS_RANK[zone["class"]], zone["score"])
        if best_key is None or key > best_key:
            best_key = key
            best_class = zone["class"]
    return best_class


class _ZoneClassIndex:
    """``_best_zone_class``'s answer via one sorted member-price array per zone, built ONCE per
    ``compute_tradability`` call.

    Why: the reference walks every zone's every member per band (``any(...)``), and a real
    intraday corpus makes that walk enormous -- 313 zones over ~149k member levels asked by ~92
    candidate bands was ~3.9s of a ~19s request (measured), nearly all of it inside that ``any``.
    Sorting each zone's member prices once makes every (band, zone) overlap question one
    ``bisect`` probe: the member with the smallest price at or above the band's low edge exists
    inside the band iff it is also at or below the high edge -- the EXACT same
    ``price_low <= member_price <= price_high`` comparisons, asked of one member instead of all
    of them (plus a min/max prefilter that only ever skips zones the reference would also have
    rejected). Selection is the reference's own loop verbatim (same zone order, same strict
    ``key > best_key`` update), and equal keys imply equal rank and therefore the SAME class, so
    tie behaviour is unobservable either way. Byte-identical served bands -- pinned by the fuzz
    equivalence test and the committed-fixture byte-identity test."""

    def __init__(self, zones: list[dict]) -> None:
        self._zones: list[tuple[float, float, list[float], tuple[int, float], str]] = []
        for zone in zones:
            prices = sorted(member["price"] for member in zone["levels"])
            if not prices:
                continue  # a memberless zone can never overlap -- the reference's `any` says no too
            self._zones.append(
                (prices[0], prices[-1], prices, (_CLASS_RANK[zone["class"]], zone["score"]), zone["class"])
            )

    def best_class(self, price_low: float, price_high: float) -> str | None:
        best_class: str | None = None
        best_key: tuple[int, float] | None = None
        for zone_min, zone_max, prices, key, zone_class in self._zones:
            if zone_max < price_low or zone_min > price_high:
                continue  # every member is outside the band -- the reference would skip it too
            index = bisect_left(prices, price_low)
            if index >= len(prices) or prices[index] > price_high:
                continue  # the nearest member at/above the low edge already overshoots the high edge
            if best_key is None or key > best_key:
                best_key = key
                best_class = zone_class
        return best_class


def _quality_score(
    members: list[dict], daily_bars: list[RawBar], price_low: float, price_high: float,
    round_number: bool, config: Config,
) -> float:
    weights = config.tradability_quality_weights
    breadth = len({member["timeframe"] for member in members})
    # goal.md's factor is the "DAILY touch count", NOT a sum across every timeframe: a real
    # multi-day rejection wall is defined by how many times the DAILY series rejected it, so ONLY
    # ``"1d"`` members contribute here. Summing the touch_count of the dozens of intraday (5m/1h)
    # members a band can hold instead lets sheer intraday level VOLUME near the current price
    # outscore that wall -- the exact miss a daily-only fixture cannot surface (reproduced, and
    # guarded against, by the multi-timeframe regression in tests/test_tradability.py). Intraday
    # members still count toward ``breadth`` above (cross-timeframe agreement is its own signal);
    # they just do not inflate this per-band touch total. Every ``touch_count`` is a member level's
    # own field already computed by ``levels.py`` -- never re-counted from bars here.
    daily_touch_total = sum(
        member["touch_count"] for member in members if member["timeframe"] == _DAILY_TIMEFRAME
    )
    recency = _recency_score(daily_bars, price_low, price_high)
    return (
        weights["timeframe_breadth"] * breadth
        + weights["touch_count"] * daily_touch_total
        + weights["recency"] * recency
        + weights["round_number"] * (1.0 if round_number else 0.0)
    )


def _band(
    members: list[dict], side: str, daily_bars: list[RawBar], zone_index: _ZoneClassIndex, config: Config
) -> dict:
    price_low = min(member["price"] for member in members)
    price_high = max(member["price"] for member in members)
    round_number = _round_number_flag(
        price_low, price_high,
        config.tradability_round_number_increment, config.tradability_round_number_tolerance_bps,
    )
    return {
        "side": side,
        "price_low": price_low,
        "price_high": price_high,
        # `zone_index` is `_best_zone_class` pre-indexed once per compute (see _ZoneClassIndex) --
        # the same inherited class, no per-band full member walk.
        "class": zone_index.best_class(price_low, price_high),
        "quality_score": _quality_score(members, daily_bars, price_low, price_high, round_number, config),
        "round_number": round_number,
        "member_count": len(members),
        # itemgetter builds the identical (price, timeframe, type) sort key as the lambda it
        # replaced, without a Python frame per member -- ~149k members cross this sort per request.
        "members": sorted(members, key=itemgetter("price", "timeframe", "type")),
    }


def _rank_sort_key(band: dict) -> tuple:
    """Descending quality score, tie-broken ascending by price -- the total order used to pick the
    top-K survivors per side (never a fabricated/arbitrary insertion-order tie-break)."""
    return (-band["quality_score"], band["price_low"])


def _served_sort_key(band: dict) -> tuple:
    """A total order over the FINAL served list (side, then descending quality, then price) so the
    served JSON is never perturbed by scan-order happenstance -- the ``levels.py`` byte-identical-
    determinism discipline."""
    return (band["side"], -band["quality_score"], band["price_low"])


def compute_tradability(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict:
    """The canonical ``GET /research/tradability`` + MCP ``tradability`` computation (single
    source of truth) -- see module docstring for the full algorithm. Returns
    ``{"bands": [...], "no_bar_series_for_symbol": bool, "basis_as_of": str | None}``."""
    daily_bars, has_any_series = _select_daily_series(store, symbol)
    if not has_any_series:
        return {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}
    if daily_bars is None:
        # series exist for `symbol` but none is "1d" -- no basis is derivable (honest, not a
        # fabricated flag flip: `levels.py`'s OWN `no_bar_series_for_symbol` stays scoped to "no
        # series at all", so this module's flag mirrors that exact meaning).
        return {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}

    resolved = _resolve_basis(daily_bars, as_of_epoch)
    if resolved is None:
        return {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}
    resolved_as_of_epoch, prior_bar = resolved
    # The SERVED basis marker is the prior session's own bar timestamp (e.g. 2026-06-18T04:00Z for
    # the pinned AAPL case) -- unambiguously dated to that session, never the internal
    # period-closed instant `compute_levels` receives (`prior_bar.epoch + _ONE_DAY_SECONDS`, one
    # calendar day later): the served field answers "which session is this map's basis", the
    # internal epoch only exists to make that session's own high/low/close usable per
    # `levels.py`'s period-closing convention (see module docstring).
    basis_as_of = _iso(prior_bar.epoch)

    # `compute_levels` reads through `_PriorSessionBarView` (bounded to `prior_bar.epoch`, EVERY
    # timeframe -- see module docstring) rather than `store` directly: the as-of epoch alone cannot
    # safely express "close `prior_bar`'s own period but admit nothing dated on/after the requested
    # session" when a same-hour-of-day bar for that later session already exists (the normal state
    # for consecutive trading sessions in a fully-fetched series).
    #
    # `raw_levels` is guaranteed non-empty here: `_resolve_basis` only returns non-None once
    # `prior_bar`'s own daily period is closed as of `resolved_as_of_epoch` (by construction, one
    # calendar day after its own epoch), and `prior_bar` is a bar of the EXACT SAME merged "1d"
    # view `compute_levels` itself reads (`_select_daily_series` calls the identical `merged_bars`
    # accessor, and the view's `list()` is unfiltered) -- so `compute_levels`'s own
    # `_prior_period_extremes` always emits at least that bar's high/low/close. No empty-
    # `raw_levels` branch is reachable,
    # so none is written (an untested dead branch is worse than no branch); the loop below already
    # returns an honest `bands: []` for a side with no levels.
    bounded_store = _PriorSessionBarView(store, prior_bar.epoch)
    levels_result = compute_levels(bounded_store, symbol, resolved_as_of_epoch, config)
    raw_levels = levels_result["levels"]
    zones = levels_result["confluence_zones"]

    current_price = prior_bar.close
    truncated_daily_bars = [b for b in daily_bars if b.epoch <= prior_bar.epoch]
    resistance_levels = [lvl for lvl in raw_levels if lvl["price"] > current_price]
    support_levels = [lvl for lvl in raw_levels if lvl["price"] <= current_price]

    # Class inheritance pre-indexed ONCE for every band of both sides (see _ZoneClassIndex --
    # the same `_best_zone_class` rule, per-zone binary search instead of a per-band member walk).
    zone_index = _ZoneClassIndex(zones)
    bands: list[dict] = []
    for side, side_levels in ((RESISTANCE, resistance_levels), (SUPPORT, support_levels)):
        clusters = _cluster_side(side_levels, config.tradability_band_width_bps)
        side_bands = [_band(members, side, truncated_daily_bars, zone_index, config) for members in clusters]
        side_bands.sort(key=_rank_sort_key)
        bands.extend(side_bands[: config.tradability_band_cap_per_side])

    bands.sort(key=_served_sort_key)
    return {
        "bands": bands,
        "no_bar_series_for_symbol": False,
        "basis_as_of": basis_as_of,
    }


def basis_day_key(as_of_epoch: float) -> str:
    """goal-fast_wall J-03 ("the arm memo"): the UTC session-date key ``_resolve_basis``'s chosen
    prior session is CONSTANT for -- reuses the EXISTING ``_session_date`` date-resolution helper
    verbatim (never a second date derivation). ``_resolve_basis`` filters candidate daily bars by
    ``_session_date(b.epoch) < _session_date(as_of_epoch)`` (the requested session's own UTC
    calendar date) and picks the latest survivor -- a decision that depends on ``as_of_epoch``
    ONLY through its own UTC calendar date, so every ``as_of_epoch`` sharing one UTC date resolves
    the IDENTICAL prior session/basis. ``research/backtests.py``'s ``_StructureArmMemo`` is the
    ONE reader of this contract, using it to collapse per-tick ``compute_tradability`` recomputes
    into one real basis per UTC session date actually visited -- this function computes nothing
    about tradability itself; it only names the key ``_resolve_basis``'s own (frozen, unchanged)
    behaviour is already constant across."""
    return _session_date(as_of_epoch).isoformat()
