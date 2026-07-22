"""Deterministic, lookahead-free support/resistance level detection AND confluence-zone
classification (era-4 capabilities 2 + 3, J-02 + J-03) -- Data Contract row 39's COMPLETE owner
(levels AND their A/B/C confluence classes).

THIS MODULE is the sole computer of support/resistance levels and their confluence zones. It reads
bars ONLY through the EXISTING ``BarStore`` (era-4 J-01, ``research/bars.py``) -- it owns no
persistence and makes no network/vendor call (vendor-neutral by construction: it touches only
stored ``RawBar`` rows, never a vendor SDK or vendor-specific field). ``GET /research/levels`` and
the read-only MCP ``levels`` tool both serve this module's output VERBATIM (single source of truth
-- no second computation path).

Two DETERMINISTIC, config-owned detection methods, applied per stored bar series:

  * **Swing pivots** -- a bar's high (or low) that is the STRICT extreme over its +/-N neighbours
    (N = ``Config.sr_pivot_lookback``), applied to EVERY stored series regardless of timeframe.
  * **Prior-period extremes** -- a completed period's high/low/close, applied ONLY to series whose
    timeframe is in the "prior period" set (``1d``/``1w``/``1mo`` -- goal.md's long-term bucket; a
    "prior day" is only meaningful read off a 1d series -- this iteration does no cross-timeframe
    aggregation). A period counts as "prior" (closed) only once its END has passed the as-of time
    (never the still-forming latest period) -- see ``_PERIOD_SECONDS``, a structural calendar fact,
    not a tunable parameter.

Every level carries **price, timeframe, type** (``swing-pivot`` | ``prior-period-extreme``),
**touch_count**, and **strength = timeframe_weight * touch_count** -- every number sourced from
``Config`` (``sr_pivot_lookback``, ``sr_touch_tolerance_bps``, ``sr_timeframe_weights``); no magic
numbers, no fitting, no ML (the anti-goal) -- verified by ``tests/test_levels.py``'s introspection
test.

**Lookahead-free by construction**: every bar list is filtered to ``ts <= as_of`` (epoch seconds,
``_bars_as_of``) BEFORE any windowing/period analysis runs -- pivots and prior-period extremes are
computed only over that truncated prefix, so a bar timestamped after ``as_of`` existing in (or
being added to) the store can never change a level computed at ``as_of`` (the headline correctness
property this module exists to prove; asserted by ``tests/test_levels.py``'s lookahead-free test).

**Deterministic**: pure functions over the stored bars + config; two runs on identical inputs
produce byte-identical output (levels are sorted by a total order -- timeframe, then price, then
type -- so no dict/set iteration order can perturb the served JSON).

**Honest failure states** (never a fabricated level, never a silently-empty success masking a
bug): a symbol with NO recorded bar series surfaces ``no_bar_series_for_symbol: true`` (an
additive boolean flag -- the ``insufficient_sample`` / ``integrity_errors`` precedent, not a
fabricated placeholder); a symbol WITH series but no derivable levels at the requested ``as_of``
surfaces an empty ``levels`` list with that flag ``false`` -- an explicit "no levels found",
never a bare, ambiguous empty array.

**Confluence zones + A/B/C conviction classes (J-03).** ``compute_confluence_zones`` is a PURE
function of the ``levels`` list above -- it touches no store/bar of its own, so it inherits the
as-of lookahead-free truncation for free (no second truncation surface to get wrong). Levels
pooled across EVERY timeframe are clustered by price proximity (``Config.sr_confluence_band_bps``,
an anchor-fixed scan -- ``_cluster_levels``); only clusters with >= 2 members are "qualifying" and
become a zone (a lone level has no confluence partner -- never a fabricated one-member "zone").
Each zone carries its member levels (each already stamped with its own ``timeframe``), a
timeframe-weighted ``score`` (the sum of member ``strength`` values -- each already folds in its
OWN timeframe's weight, so the score is never double-weighted), and an honest ``class`` (A/B/C)
graded purely by DISTINCT-TIMEFRAME breadth (``_grade_zone`` -- goal.md's "levels that align
across timeframes matter more"), never by score: class A needs a config-owned minimum of distinct
timeframes AND at least one long-term member (``PRIOR_PERIOD_TIMEFRAMES``, reused verbatim); class
B needs only the (lower) distinct-timeframe floor; a qualifying cluster whose members share ONE
timeframe grades C -- a real, honestly-reported zone of the lowest conviction, never suppressed.
A symbol with levels but no qualifying cluster returns an explicit empty ``confluence_zones`` list
(``no_bar_series_for_symbol`` is unaffected either way -- a SEPARATE, pre-existing honest flag).
Zones are sorted by an explicit total order (``_zone_sort_key``) for byte-identical served JSON.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right

from ..config import Config
from ..providers.adapters.base import RawBar
from .bars import BarStore

# The two level types (Data Contract row 39 / DoD). A level's "kind" (support vs resistance) is
# NOT tracked separately here -- a horizontal price level can act as either depending on the
# direction price approaches from; that classification is a J-03/J-04 tape-reading concern, not a
# structural property computed here.
SWING_PIVOT = "swing-pivot"
PRIOR_PERIOD_EXTREME = "prior-period-extreme"

# The "prior period" timeframe set (goal.md's long-term bucket): ONLY a series at one of these
# granularities yields prior-period-extreme candidates. Swing pivots, by contrast, apply to EVERY
# stored timeframe (the mid-term/shorter buckets too) -- see ``_swing_pivots``.
PRIOR_PERIOD_TIMEFRAMES: tuple[str, ...] = ("1d", "1w", "1mo")

# Calendar period length in seconds for the prior-period timeframes above -- a STRUCTURAL calendar
# fact (a day IS 86400 seconds), not a tunable S/R parameter, so it is deliberately NOT a
# ``Config`` field (the no-magic-numbers test targets the three genuinely tunable parameters:
# ``sr_pivot_lookback``, ``sr_touch_tolerance_bps``, ``sr_timeframe_weights``). ``1mo`` is a
# nominal 30-day calendar approximation (real months vary 28-31 days) used only to decide whether
# a month has closed by ``as_of``; it never enters a level's price, touch_count, or strength.
_PERIOD_SECONDS: dict[str, float] = {"1d": 86400.0, "1w": 604800.0, "1mo": 2_592_000.0}


def _bars_as_of(bars: list[RawBar], as_of_epoch: float) -> list[RawBar]:
    """The lookahead-free prefix: every bar with ``ts <= as_of``, in stored (ascending) order.
    Every detector below runs ONLY over this truncated list -- never the full series -- so a bar
    timestamped after ``as_of`` can never reach a level computed at ``as_of``."""
    return [b for b in bars if b.epoch <= as_of_epoch]


def _touch_count(bars: list[RawBar], price: float, tol_bps: float, defining_index: int) -> int:
    """How many bars' high OR low comes within ``tol_bps`` basis points of ``price``. The level's
    ORIGINATING bar (``defining_index``) always counts, whichever OHLC field it came from -- a
    freshly-derived level is never dishonestly reported as untouched (e.g. a prior-period CLOSE
    that falls strictly between that same bar's own high and low).

    THE reference definition of a touch. ``_TouchIndex`` below answers the identical question in
    log time by pre-filtering candidates and then applying THIS predicate to each one, so the two
    always agree bar-for-bar (``test_levels.py`` pins that equivalence)."""
    tol = price * (tol_bps / 10_000.0)
    count = 0
    for i, b in enumerate(bars):
        if i == defining_index or abs(b.high - price) <= tol or abs(b.low - price) <= tol:
            count += 1
    return count


class _TouchIndex:
    """A sorted view of one bar list's highs and lows, so counting touches costs a binary search
    instead of a full scan.

    Why: ``_touch_count`` is called once per detected level, and each call walked every bar --
    O(levels x bars). That was invisible while a recorded series held ~2,000 bars, and became a
    3.5-minute page load the moment deeper history arrived (AMD 1m: 34k bars, 16.6k levels, ~560M
    comparisons and a BILLION ``abs()`` calls, measured). This makes the same computation
    logarithmic in the bar count.

    Exactness over cleverness: the binary search only NARROWS the candidate set (deliberately
    widened by a relative epsilon so a float rounding of ``price - tol`` can never exclude a true
    match), and the ORIGINAL ``abs(value - price) <= tol`` predicate then decides each candidate.
    So this is not an approximation of the touch rule with new boundary behaviour -- it is the same
    rule, asked of fewer bars. Levels, strengths, zones, bands and every backtest that reads them
    are unchanged."""

    # Relative slack on the candidate window: large enough to absorb the ~1-ulp error of computing
    # ``price - tol`` / ``price + tol`` in floating point, small enough that the candidate set stays
    # tiny. Only ever ADMITS extra candidates for the exact predicate to reject -- it can never
    # exclude a real match, which is the only direction that could change an answer.
    _EPSILON_RATIO = 1e-9

    def __init__(self, bars: list[RawBar]) -> None:
        self._bars = bars
        self._highs = sorted((b.high, i) for i, b in enumerate(bars))
        self._lows = sorted((b.low, i) for i, b in enumerate(bars))
        self._high_values = [value for value, _ in self._highs]
        self._low_values = [value for value, _ in self._lows]

    def count(self, price: float, tol_bps: float, defining_index: int) -> int:
        tol = price * (tol_bps / 10_000.0)
        slack = abs(price) * self._EPSILON_RATIO + abs(tol) * self._EPSILON_RATIO
        low_bound = price - tol - slack
        high_bound = price + tol + slack
        touched = {defining_index}
        for values, pairs in ((self._high_values, self._highs), (self._low_values, self._lows)):
            left = bisect_left(values, low_bound)
            right = bisect_right(values, high_bound)
            for k in range(left, right):
                value, index = pairs[k]
                if abs(value - price) <= tol:  # the ORIGINAL predicate, verbatim
                    touched.add(index)
        return len(touched)


def _level(price: float, timeframe: str, level_type: str, touch_count: int, weight: float) -> dict:
    return {
        "price": price,
        "timeframe": timeframe,
        "type": level_type,
        "touch_count": touch_count,
        "strength": weight * touch_count,
    }


def _swing_pivots(
    bars: list[RawBar],
    timeframe: str,
    lookback: int,
    tol_bps: float,
    weight: float,
    touch_index: "_TouchIndex | None" = None,
) -> list[dict]:
    """Every STRICT +/-``lookback``-neighbour extreme in ``bars`` (already as-of-filtered).

    A bar's high is a swing-high pivot iff it is STRICTLY greater than every one of its
    ``lookback`` neighbours on BOTH sides (a tie is not a pivot -- deterministic; no arbitrary
    tie-break between two equal bars); the mirror rule finds swing-low pivots. A centre index
    needs ``lookback`` visible bars on EACH side to be checked at all, so a pivot near either end
    of the as-of-truncated prefix simply does not register yet -- exactly the lookahead-free
    property: it only confirms once the ``lookback`` bars AFTER it are themselves visible
    (``ts <= as_of``)."""
    levels: list[dict] = []
    n = len(bars)
    touches_in = touch_index or _TouchIndex(bars)
    for i in range(lookback, n - lookback):
        centre = bars[i]
        neighbours = bars[i - lookback : i] + bars[i + 1 : i + lookback + 1]
        if all(centre.high > w.high for w in neighbours):
            touches = touches_in.count(centre.high, tol_bps, i)
            levels.append(_level(centre.high, timeframe, SWING_PIVOT, touches, weight))
        if all(centre.low < w.low for w in neighbours):
            touches = touches_in.count(centre.low, tol_bps, i)
            levels.append(_level(centre.low, timeframe, SWING_PIVOT, touches, weight))
    return levels


def _prior_period_extremes(
    bars: list[RawBar],
    timeframe: str,
    tol_bps: float,
    weight: float,
    as_of_epoch: float,
    touch_index: "_TouchIndex | None" = None,
) -> list[dict]:
    """High/low/close of every COMPLETED period in ``bars`` (already as-of-filtered).

    A period counts as complete only once its end (``bar.epoch + period_seconds``) is at or
    before ``as_of`` (never the still-forming latest period) -- so a day's high/low/close become
    referenceable starting exactly at the FOLLOWING day's as-of, never earlier."""
    period_seconds = _PERIOD_SECONDS[timeframe]
    levels: list[dict] = []
    touches_in = touch_index or _TouchIndex(bars)
    for i, b in enumerate(bars):
        if b.epoch + period_seconds > as_of_epoch:
            continue  # this period has not closed as of `as_of` -- never a lookahead peek
        for price in (b.high, b.low, b.close):
            touches = touches_in.count(price, tol_bps, i)
            levels.append(_level(price, timeframe, PRIOR_PERIOD_EXTREME, touches, weight))
    return levels


def _sort_key(level: dict) -> tuple:
    """A total order over levels (timeframe, then price, then type) so the served list is never
    perturbed by dict/set iteration order -- the byte-identical-determinism discipline."""
    return (level["timeframe"], level["price"], level["type"])


def _select_one_series_per_timeframe(records: list[dict]) -> dict[str, dict]:
    """``BarStore`` has no "get by symbol+timeframe" accessor (only ``list``/``get``/``load_bars``
    by id), so when more than one stored, HEALTHY series shares a (symbol, timeframe) pair, the
    most RECENTLY CREATED one wins -- a documented default judgment call (the committed fixture
    never exercises this; exactly one series per pair)."""
    by_timeframe: dict[str, dict] = {}
    for record in records:
        timeframe = record["timeframe"]
        current = by_timeframe.get(timeframe)
        if current is None or record["created_utc"] > current["created_utc"]:
            by_timeframe[timeframe] = record
    return by_timeframe


# --- Confluence zones + A/B/C conviction classes (era-4 capability 3, J-03) ------------------------
# The three honest grades a qualifying cluster (>= 2 price-clustered levels) can carry -- never a
# fourth/fabricated grade, never assigned to a non-qualifying (< 2 member) cluster (which is simply
# absent from the served list, per the module docstring).
CLASS_A = "A"
CLASS_B = "B"
CLASS_C = "C"


def _cluster_levels(levels: list[dict], band_bps: float) -> list[list[dict]]:
    """Group ``levels`` (POOLED across every timeframe -- confluence is cross-timeframe by
    definition) into confluence clusters.

    An ANCHOR-FIXED scan over levels sorted ascending by price: the FIRST (lowest-priced) member of
    a cluster fixes its tolerance window (``anchor * band_bps / 10_000``); every subsequent level
    within that window of the ANCHOR (never the previous member) joins the SAME cluster -- so a
    cluster's price span is bounded by ONE fixed tolerance rather than an unbounded chain of
    near-neighbours (the classic chaining defect a naive pairwise-consecutive-gap scan would admit).

    Only clusters with >= 2 members are returned -- a lone level has no confluence partner and is
    silently dropped from the result (never a fabricated one-member "zone"; the module docstring's
    "no qualifying cluster" honest-empty state)."""
    ordered = sorted(levels, key=lambda lvl: (lvl["price"], lvl["timeframe"], lvl["type"]))
    clusters: list[list[dict]] = []
    current: list[dict] = []
    anchor = 0.0
    tolerance = 0.0
    for level in ordered:
        if current and abs(level["price"] - anchor) <= tolerance:
            current.append(level)
            continue
        if len(current) >= 2:
            clusters.append(current)
        anchor = level["price"]
        tolerance = anchor * (band_bps / 10_000.0)
        current = [level]
    if len(current) >= 2:
        clusters.append(current)
    return clusters


def _grade_zone(members: list[dict], config: Config) -> str:
    """A/B/C by DISTINCT-TIMEFRAME breadth alone (goal.md: "levels that align across timeframes
    matter more") -- NEVER by score, so the class always answers "how many independent timeframes
    agree here", while the score (``_confluence_zone``) stays a separate, additive number.

    Class A needs BOTH a config-owned minimum distinct-timeframe count AND at least one long-term
    member (the existing ``PRIOR_PERIOD_TIMEFRAMES`` bucket, reused verbatim -- no second "long-term"
    list). Class B needs only the (lower) distinct-timeframe floor. Anything else -- structurally,
    every member sharing exactly ONE timeframe -- grades C: a real, honestly-reported zone of the
    lowest conviction (same-timeframe price proximity, which each level's own ``touch_count``
    already captures), never suppressed and never upgraded."""
    distinct_timeframes = {member["timeframe"] for member in members}
    has_long_term = any(tf in PRIOR_PERIOD_TIMEFRAMES for tf in distinct_timeframes)
    if len(distinct_timeframes) >= config.sr_confluence_class_a_min_timeframes and has_long_term:
        return CLASS_A
    if len(distinct_timeframes) >= config.sr_confluence_class_b_min_timeframes:
        return CLASS_B
    return CLASS_C


def _confluence_zone(members: list[dict], config: Config) -> dict:
    """One served zone: its members (sorted by the SAME total order ``_cluster_levels`` scans in),
    its timeframe-weighted ``score`` (the sum of member ``strength`` values -- each already folds in
    its own timeframe's weight via ``_level``, so this is never double-weighted), and its honest
    ``class``."""
    ordered_members = sorted(members, key=lambda lvl: (lvl["price"], lvl["timeframe"], lvl["type"]))
    return {
        "levels": ordered_members,
        "score": sum(member["strength"] for member in ordered_members),
        "class": _grade_zone(ordered_members, config),
    }


def _zone_sort_key(zone: dict) -> tuple:
    """A total order over zones (lowest member price, then member count) so served JSON is never
    perturbed by scan-order happenstance -- pairs with ``_sort_key``'s total order over levels."""
    return (zone["levels"][0]["price"], len(zone["levels"]))


def compute_confluence_zones(levels: list[dict], config: Config) -> list[dict]:
    """The canonical confluence-zone computation (era-4 capability 3, J-03): a PURE function of the
    ALREADY lookahead-free ``levels`` list ``compute_levels`` produces below -- no bar/store access
    of its own, so it inherits the as-of truncation for free (no second truncation surface to get
    wrong; the identical inputs always yield identical zones). Clusters ``levels`` (pooled across
    every timeframe) within ``config.sr_confluence_band_bps``; each qualifying cluster becomes a
    zone (member levels, timeframe-weighted score, honest A/B/C class). Sorted by an explicit total
    order (``_zone_sort_key``) for byte-identical served JSON."""
    clusters = _cluster_levels(levels, band_bps=config.sr_confluence_band_bps)
    zones = [_confluence_zone(members, config) for members in clusters]
    zones.sort(key=_zone_sort_key)
    return zones


def compute_levels(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict:
    """The canonical ``GET /research/levels`` + MCP ``levels`` computation (single source of
    truth) -- every level for ``symbol`` derived from its stored bar series, as of
    ``as_of_epoch`` (a UTC epoch-seconds instant; the ROUTE parses the ISO string once, never
    here, so this function itself carries no lookahead-leaking default).

    Returns ``{"levels": [...], "no_bar_series_for_symbol": bool, "confluence_zones": [...]}`` --
    ``no_bar_series_for_symbol`` is an explicit, ADDITIVE honesty flag (the ``insufficient_sample``
    precedent) rather than an ambiguous bare empty ``levels`` list: the flag is ``True`` only when
    NO stored, healthy series exists for ``symbol`` at all; a symbol WITH series but nothing
    derivable at this ``as_of`` reports ``False`` with an empty ``levels`` list -- an honest "no
    levels found", never fabricated. ``confluence_zones`` (J-03, additive beside the two J-02 keys)
    is ``compute_confluence_zones``' output over the SAME ``levels`` list -- always ``[]`` when
    ``levels`` is empty (whichever honest reason), never fabricated.

    A stored series whose timeframe is outside ``config.sr_timeframe_weights`` (impossible today
    -- that set covers every ``bar_timeframes`` entry, pinned by a dedicated config test) would
    raise ``KeyError`` rather than silently skip or fabricate a weight.

    Note on the corrupt-sole-series seam (iter-2 finding B1, revisited for J-03): this function
    reads only ``store.list()``'s HEALTHY ``records`` half (the same as J-02) -- a symbol whose
    ONLY bar series is corrupted therefore still aliases to ``no_bar_series_for_symbol: true`` with
    an empty ``confluence_zones`` list, exactly as it aliased before confluence existed. J-03
    introduces no new fabricated or aliased state here: the distinct corrupt-series honest state
    remains owned by ``GET /research/bars`` (a deliberate, unchanged decision -- see the dev
    handoff)."""
    records, _integrity_errors = store.list()
    matching = [r for r in records if r["symbol"] == symbol]
    if not matching:
        return {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}

    levels: list[dict] = []
    for timeframe, record in _select_one_series_per_timeframe(matching).items():
        weight = config.sr_timeframe_weights[timeframe]
        bars = _bars_as_of(store.load_bars(record["id"]), as_of_epoch)
        # ONE sorted view per series, shared by both detectors: they ask the same touch question of
        # the same bars, so building it twice would double the only setup cost this adds.
        touch_index = _TouchIndex(bars)
        levels.extend(
            _swing_pivots(
                bars,
                timeframe,
                config.sr_pivot_lookback,
                config.sr_touch_tolerance_bps,
                weight,
                touch_index,
            )
        )
        if timeframe in PRIOR_PERIOD_TIMEFRAMES:
            levels.extend(
                _prior_period_extremes(
                    bars, timeframe, config.sr_touch_tolerance_bps, weight, as_of_epoch, touch_index
                )
            )
    levels.sort(key=_sort_key)
    return {
        "levels": levels,
        "no_bar_series_for_symbol": False,
        "confluence_zones": compute_confluence_zones(levels, config),
    }


def level_change_points(store: BarStore, symbol: str) -> tuple[float, ...]:
    """goal-fast_wall J-03 ("the arm memo"): a SAFE SUPERSET of every instant at which
    ``compute_levels(store, symbol, as_of, config)`` could possibly change for ``symbol`` --
    between any two CONSECUTIVE entries of the returned tuple, ``compute_levels`` is a constant
    function of ``as_of``. A superset of the true change points is always safe (it costs at most
    one harmless extra memo split); a MISSING true change point is never safe, since it would
    silently serve a stale result across a genuine regime change. ``research/backtests.py``'s
    ``_StructureArmMemo`` is the ONE reader of this contract, using it to collapse thousands of
    per-tick ``compute_levels`` recomputes into the handful of real level states a session
    actually has -- this function itself computes NOTHING about levels; it only enumerates WHEN
    the already-frozen ``compute_levels``/``compute_confluence_zones`` bodies above could move.

    Mirrors ``compute_levels``'s OWN healthy-series enumeration exactly (the SAME ``store.list()``
    healthy-``records`` half, the SAME ``_select_one_series_per_timeframe`` tie-break, the SAME
    ``PRIOR_PERIOD_TIMEFRAMES``/``_PERIOD_SECONDS``) so this function can never omit a series
    ``compute_levels`` itself would read: the union of every SELECTED series' own bar epochs (a
    newly-visible bar can create or newly confirm a swing pivot near either end of the as-of-
    truncated prefix -- see ``_swing_pivots``) plus, for each series whose timeframe is in
    ``PRIOR_PERIOD_TIMEFRAMES``, each of ITS bars' own period-closing instant
    (``epoch + period_seconds`` -- the exact instant ``_prior_period_extremes`` newly treats that
    bar as "completed"). Unlike ``compute_levels``, this reads bars WITHOUT any ``_bars_as_of``
    truncation of its own -- a single per-run tuple must cover every ``as_of`` the run will ever
    ask about, resolved ONCE, so a change point later than any ``as_of`` a particular caller
    happens to query is still a safe, if unused, entry.

    Returns an empty tuple for a symbol with no healthy recorded series at all -- the
    ``no_bar_series_for_symbol`` precedent's honest absence, never a fabricated instant."""
    records, _integrity_errors = store.list()
    matching = [r for r in records if r["symbol"] == symbol]
    if not matching:
        return ()
    points: set[float] = set()
    for timeframe, record in _select_one_series_per_timeframe(matching).items():
        for bar in store.load_bars(record["id"]):
            points.add(bar.epoch)
            if timeframe in PRIOR_PERIOD_TIMEFRAMES:
                points.add(bar.epoch + _PERIOD_SECONDS[timeframe])
    return tuple(sorted(points))
