"""Deterministic, lookahead-free support/resistance level detection AND confluence-zone
classification (era-4 capabilities 2 + 3, J-02 + J-03) -- Data Contract row 39's COMPLETE owner
(levels AND their A/B/C confluence classes).

THIS MODULE is the sole computer of support/resistance levels and their confluence zones. It reads
bars ONLY through the EXISTING ``BarStore`` (era-4 J-01, ``research/bars.py``) -- it owns no
persistence and makes no network/vendor call (vendor-neutral by construction: it touches only
stored ``RawBar`` rows, never a vendor SDK or vendor-specific field). ``GET /research/levels`` and
the read-only MCP ``levels`` tool both serve this module's output VERBATIM (single source of truth
-- no second computation path).

**One merged bar view per timeframe.** A (symbol, timeframe) pair commonly has SEVERAL recorded
series -- a later fetch over a wider window, or the deep-history leg that asks a second vendor for
the part a vendor cap left unfetched; recordings are immutable, so every one of them stays on file.
This module reads them through ``BarStore.merged_bars`` (``research/bars.py``), which folds them all
into one ascending series de-duplicated by timestamp (most recently created recording wins a
contested timestamp). It does NOT select one recording per timeframe: doing so made every level a
function of which window happened to be recorded LAST rather than of the symbol's actual history --
a 1-bar recording created after a 250-bar one froze every level and every as-of basis to that single
bar, while the chart (which has always read the same merged view) drew the full history underneath.
Recordings of one pair can come from different feeds, so a merged series can carry rows whose prices
differ in the last significant digits from a neighbouring recording's -- the same trade-off the
merged chart read has always made, and the one ``merged_bars`` owns and documents.

Two DETERMINISTIC, config-owned detection methods, applied per merged (symbol, timeframe) series:

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

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ..config import Config
from ..providers.adapters.base import RawBar
from .bars import BarStore

# The two level types (Data Contract row 39 / DoD). A level's "kind" (support vs resistance) is
# NOT tracked separately here -- a horizontal price level can act as either depending on the
# direction price approaches from; that classification is a J-03/J-04 tape-reading concern, not a
# structural property computed here.
SWING_PIVOT = "swing-pivot"
PRIOR_PERIOD_EXTREME = "prior-period-extreme"

# NOTE for anyone editing the detection below: the durable derived caches
# (``setups_scan_cache``, ``edge_report_cache``, ``edge_report_backtest_cache``) key on their
# INPUTS -- store checksums + a whole-``Config`` hash -- so a change that moves this module's
# answer without moving those inputs MUST bump ``LEVELS_ALGORITHM_VERSION``
# (``algorithm_version.py``), or those caches keep serving results this code can no longer
# produce.

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
    are unchanged.

    Today this per-query index serves the PRIOR-PERIOD detector (only ever the small 1d/1w/1mo
    series) and the test suite's equivalence chain; the swing-pivot path -- where a dense 1m
    series asks ~118k touch questions per request -- goes through ``_BatchTouchCounter`` below,
    which answers the identical predicate for every query at once."""

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


# Queries per flattened-gather chunk in ``_BatchTouchCounter`` -- a MEMORY bound, not a research
# parameter (the ``_RACY_WRITE_GUARD_SECONDS`` class of constant): each chunk materializes
# ``sum(window sizes)`` candidate rows (~1,500 bars per query on a dense 1m series), so 4,096
# queries tops out around ~30MB of transient arrays. Any value here produces byte-identical
# counts; it only trades peak memory against numpy call overhead.
_BATCH_QUERY_CHUNK = 4096


class _BatchTouchCounter:
    """``_touch_count``'s answer for MANY (price, defining_index) queries at once -- the numpy
    batch twin of ``_TouchIndex``, built for the swing-pivot path where a dense 1m series asks
    ~118k touch questions per request.

    Why: ``_TouchIndex`` made each query logarithmic to FIND its candidates, but still walked and
    set-inserted every candidate in Python -- ~1,500 candidates per query on a dense series at 5
    bps, ~177M interpreter operations per 1m request (measured 13.8s, ~100% of the request).
    This class asks the identical questions in vectorized numpy (~1s for the same request).

    Exactness over cleverness -- the ``_TouchIndex`` discipline, restated for batches:

      * Candidates come from ``searchsorted`` windows widened by the SAME ``_EPSILON_RATIO``
        slack formula ``_TouchIndex.count`` uses, and the ORIGINAL predicate
        ``abs(value - price) <= tol`` then decides every candidate (vectorized, verbatim).
        Slack only ever ADMITS extra candidates for the exact predicate to reject.
      * ``_touch_count`` counts BARS (a bar whose high AND low both lie in the band counts
        once). Instead of a per-query Python set, the union is counted by inclusion-exclusion:
        ``highs passing + lows passing - bars passing on both endpoints``. The overlap term
        re-tests each passing high-candidate's own low against the exact predicate -- complete
        by construction, because a passing endpoint always lies inside its own slack window.
      * ``_touch_count`` counts the DEFINING bar unconditionally (``i == defining_index or …``).
        The union above already contains it whenever its own high or low passes the predicate,
        so the correction is ``+1`` exactly when both fail -- applied per LEVEL, after the
        per-unique-price union (many levels share one price; the union is a pure function of
        price, the correction is not).

    ``tests/test_levels.py`` pins this class ≡ ``_touch_count`` bar-for-bar (the same equivalence
    contract ``_TouchIndex`` carries), including band-edge, duplicate-price and zero-range-bar
    cases, and the committed-fixture end-to-end reference swap."""

    # ``_TouchIndex``'s own slack ratio, bound HERE at class-definition time -- the two counters
    # must widen identically, and a late module-global lookup would break under the test suite's
    # reference-swap monkeypatch of ``_TouchIndex`` itself.
    _EPSILON_RATIO = _TouchIndex._EPSILON_RATIO

    def __init__(self, highs: np.ndarray, lows: np.ndarray) -> None:
        self._highs = highs
        self._lows = lows
        self._high_order = np.argsort(highs, kind="stable")
        self._low_order = np.argsort(lows, kind="stable")
        self._high_sorted = highs[self._high_order]
        self._low_sorted = lows[self._low_order]

    def counts(self, prices: np.ndarray, defining: np.ndarray, tol_bps: float) -> np.ndarray:
        """``_touch_count(bars, prices[k], tol_bps, defining[k])`` for every ``k``, as int64."""
        if len(prices) == 0:
            return np.zeros(0, dtype=np.int64)
        unique_prices, inverse = np.unique(prices, return_inverse=True)
        union = self._union_counts(unique_prices, tol_bps)
        tol = prices * (tol_bps / 10_000.0)
        defining_touches = (np.abs(self._highs[defining] - prices) <= tol) | (
            np.abs(self._lows[defining] - prices) <= tol
        )
        return union[inverse] + (~defining_touches)

    def _union_counts(self, unique_prices: np.ndarray, tol_bps: float) -> np.ndarray:
        """``|{bars whose high OR low passes the predicate}|`` per unique price -- see the class
        docstring for the inclusion-exclusion argument."""
        tol = unique_prices * (tol_bps / 10_000.0)
        # The SAME slack formula `_TouchIndex.count` applies per query, vectorized.
        slack = np.abs(unique_prices) * self._EPSILON_RATIO + np.abs(tol) * self._EPSILON_RATIO
        low_bound = unique_prices - tol - slack
        high_bound = unique_prices + tol + slack
        window_left = {
            "high": np.searchsorted(self._high_sorted, low_bound, "left"),
            "low": np.searchsorted(self._low_sorted, low_bound, "left"),
        }
        window_right = {
            "high": np.searchsorted(self._high_sorted, high_bound, "right"),
            "low": np.searchsorted(self._low_sorted, high_bound, "right"),
        }
        total_queries = len(unique_prices)
        high_hits = np.zeros(total_queries, dtype=np.int64)
        low_hits = np.zeros(total_queries, dtype=np.int64)
        both_hits = np.zeros(total_queries, dtype=np.int64)
        sides = (
            # (window key, sorted values, order map, hit accumulator, overlap accumulator).
            # The overlap term is accumulated on ONE side only: a bar passing on BOTH endpoints
            # is, by definition, among the highs-side passers, so testing each passing high's own
            # low enumerates every double-counted bar exactly once.
            ("high", self._high_sorted, self._high_order, high_hits, both_hits),
            ("low", self._low_sorted, self._low_order, low_hits, None),
        )
        for start in range(0, total_queries, _BATCH_QUERY_CHUNK):
            end = min(start + _BATCH_QUERY_CHUNK, total_queries)
            for key, sorted_values, order, hits, overlap in sides:
                left = window_left[key][start:end]
                sizes = window_right[key][start:end] - left
                total = int(sizes.sum())
                if total == 0:
                    continue
                # Flattened candidate windows: for query q, the run left[q]..right[q] of the
                # sorted array, all concatenated -- the classic repeat/arange construction.
                window_starts = np.cumsum(np.concatenate(([0], sizes[:-1])))
                flat = np.repeat(left, sizes) + (np.arange(total) - np.repeat(window_starts, sizes))
                query = np.repeat(np.arange(end - start), sizes)
                price = unique_prices[start:end][query]
                tolerance = tol[start:end][query]
                passes = np.abs(sorted_values[flat] - price) <= tolerance  # the ORIGINAL predicate
                # np.bincount, not add.reduceat: reduceat mishandles empty windows (it returns the
                # element AT a repeated offset instead of 0). Float weights are exact here -- every
                # per-query sum is far below 2**53.
                hits[start:end] += np.bincount(query, weights=passes, minlength=end - start).astype(
                    np.int64
                )
                if overlap is not None:
                    other = self._lows[order[flat]]
                    both = passes & (np.abs(other - price) <= tolerance)
                    overlap[start:end] += np.bincount(
                        query, weights=both, minlength=end - start
                    ).astype(np.int64)
        return high_hits + low_hits - both_hits


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
) -> list[dict]:
    """Every STRICT +/-``lookback``-neighbour extreme in ``bars`` (already as-of-filtered).

    A bar's high is a swing-high pivot iff it is STRICTLY greater than every one of its
    ``lookback`` neighbours on BOTH sides (a tie is not a pivot -- deterministic; no arbitrary
    tie-break between two equal bars); the mirror rule finds swing-low pivots. A centre index
    needs ``lookback`` visible bars on EACH side to be checked at all, so a pivot near either end
    of the as-of-truncated prefix simply does not register yet -- exactly the lookahead-free
    property: it only confirms once the ``lookback`` bars AFTER it are themselves visible
    (``ts <= as_of``).

    Vectorized (the ``_TouchIndex`` -> ``_BatchTouchCounter`` progression, applied to detection):
    ``centre > max(side window)`` is the SAME truth value as "strictly greater than every
    neighbour on that side", evaluated per side over ``sliding_window_view`` maxima/minima --
    never a changed rule, only a changed iterator (a dense 1m series checks ~277k centres and
    counts ~118k pivots' touches; the Python loop + per-query index was ~14s of a request, this
    is ~1s). Touch counts come from ``_BatchTouchCounter`` (see its exactness contract).

    Emission order is every high pivot (ascending bar index) then every low pivot (ascending),
    where the loop this replaced interleaved high-then-low PER BAR. Unobservable in any served
    output: ``compute_levels`` stable-sorts by ``(timeframe, price, type)``, and two swing-pivot
    levels equal on that key are IDENTICAL dicts -- a pivot's touch count is a pure function of
    its price (the defining bar's own endpoint is the price itself, distance zero, so the
    defining-index correction never fires) -- so any relative order of such ties serializes to
    the same bytes. Pinned by the committed-fixture byte-identity tests."""
    n = len(bars)
    if n < 2 * lookback + 1:
        return []  # no centre has `lookback` bars on both sides -- the loop's own empty range
    highs = np.array([b.high for b in bars], dtype=np.float64)
    lows = np.array([b.low for b in bars], dtype=np.float64)
    centre_highs = highs[lookback : n - lookback]
    centre_lows = lows[lookback : n - lookback]
    # Row j of a width-`lookback` window view is values[j : j+lookback]: a centre at index i has
    # its LEFT window at row i-lookback (values[i-lookback : i]) and its RIGHT window at row i+1
    # (values[i+1 : i+1+lookback]) -- so rows [0, n-2*lookback) and [lookback+1, ...] align the
    # two sides against the centres slice above.
    high_windows = sliding_window_view(highs, lookback)
    low_windows = sliding_window_view(lows, lookback)
    is_high_pivot = (centre_highs > high_windows[: n - 2 * lookback].max(axis=1)) & (
        centre_highs > high_windows[lookback + 1 :].max(axis=1)
    )
    is_low_pivot = (centre_lows < low_windows[: n - 2 * lookback].min(axis=1)) & (
        centre_lows < low_windows[lookback + 1 :].min(axis=1)
    )
    high_pivots = np.flatnonzero(is_high_pivot) + lookback
    low_pivots = np.flatnonzero(is_low_pivot) + lookback
    if len(high_pivots) == 0 and len(low_pivots) == 0:
        return []
    prices = np.concatenate((highs[high_pivots], lows[low_pivots]))
    defining = np.concatenate((high_pivots, low_pivots))
    counts = _BatchTouchCounter(highs, lows).counts(prices, defining, tol_bps)
    # .tolist() materializes native Python floats/ints (bit-exact), never numpy scalars -- a
    # np.float64 leaking into a served dict would break json serialization downstream.
    return [
        _level(price, timeframe, SWING_PIVOT, touches, weight)
        for price, touches in zip(prices.tolist(), counts.tolist())
    ]


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


def _timeframes_for(records: list[dict]) -> list[str]:
    """The distinct timeframes ``records`` (one symbol's HEALTHY series) covers, in a stable
    sorted order. Every recording of a timeframe contributes -- the bars themselves are then read
    as ONE merged series per timeframe (``BarStore.merged_bars``), never one selected recording;
    see the module docstring."""
    return sorted({record["timeframe"] for record in records})


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

    One MERGED series is read per timeframe the symbol has any healthy recording for
    (``BarStore.merged_bars``), so every recorded window contributes and no level depends on
    which recording happened to be written last -- see the module docstring.

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
    for timeframe in _timeframes_for(matching):
        weight = config.sr_timeframe_weights[timeframe]
        bars = _bars_as_of(store.merged_bars(symbol, timeframe), as_of_epoch)
        # The two detectors no longer share a `_TouchIndex`: the swing-pivot path counts touches
        # through its own vectorized `_BatchTouchCounter`, and the prior-period path (only ever
        # the small 1d/1w/1mo series) lazily builds its own per-query index -- so a dense
        # intraday timeframe never pays for an index only the other detector would read.
        levels.extend(
            _swing_pivots(
                bars,
                timeframe,
                config.sr_pivot_lookback,
                config.sr_touch_tolerance_bps,
                weight,
            )
        )
        if timeframe in PRIOR_PERIOD_TIMEFRAMES:
            levels.extend(
                _prior_period_extremes(
                    bars, timeframe, config.sr_touch_tolerance_bps, weight, as_of_epoch
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
    healthy-``records`` half, the SAME ``_timeframes_for`` + ``merged_bars`` read, the SAME
    ``PRIOR_PERIOD_TIMEFRAMES``/``_PERIOD_SECONDS``) so this function can never omit a bar
    ``compute_levels`` itself would read: the union of every MERGED series' own bar epochs (a
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
    for timeframe in _timeframes_for(matching):
        for bar in store.merged_bars(symbol, timeframe):
            points.add(bar.epoch)
            if timeframe in PRIOR_PERIOD_TIMEFRAMES:
                points.add(bar.epoch + _PERIOD_SECONDS[timeframe])
    return tuple(sorted(points))
