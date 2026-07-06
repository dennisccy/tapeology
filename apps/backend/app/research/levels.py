"""Deterministic, lookahead-free support/resistance level detection (era-4 capability 2, J-02) --
Data Contract row 39's LEVELS half (confluence classes are J-03; out of scope here).

THIS MODULE is the sole computer of support/resistance levels. It reads bars ONLY through the
EXISTING ``BarStore`` (era-4 J-01, ``research/bars.py``) -- it owns no persistence and makes no
network/vendor call (vendor-neutral by construction: it touches only stored ``RawBar`` rows, never
a vendor SDK or vendor-specific field). ``GET /research/levels`` and the read-only MCP ``levels``
tool both serve this module's output VERBATIM (single source of truth -- no second computation
path).

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
"""

from __future__ import annotations

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
    that falls strictly between that same bar's own high and low)."""
    tol = price * (tol_bps / 10_000.0)
    count = 0
    for i, b in enumerate(bars):
        if i == defining_index or abs(b.high - price) <= tol or abs(b.low - price) <= tol:
            count += 1
    return count


def _level(price: float, timeframe: str, level_type: str, touch_count: int, weight: float) -> dict:
    return {
        "price": price,
        "timeframe": timeframe,
        "type": level_type,
        "touch_count": touch_count,
        "strength": weight * touch_count,
    }


def _swing_pivots(bars: list[RawBar], timeframe: str, lookback: int, tol_bps: float, weight: float) -> list[dict]:
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
    for i in range(lookback, n - lookback):
        centre = bars[i]
        neighbours = bars[i - lookback : i] + bars[i + 1 : i + lookback + 1]
        if all(centre.high > w.high for w in neighbours):
            touches = _touch_count(bars, centre.high, tol_bps, i)
            levels.append(_level(centre.high, timeframe, SWING_PIVOT, touches, weight))
        if all(centre.low < w.low for w in neighbours):
            touches = _touch_count(bars, centre.low, tol_bps, i)
            levels.append(_level(centre.low, timeframe, SWING_PIVOT, touches, weight))
    return levels


def _prior_period_extremes(
    bars: list[RawBar], timeframe: str, tol_bps: float, weight: float, as_of_epoch: float
) -> list[dict]:
    """High/low/close of every COMPLETED period in ``bars`` (already as-of-filtered).

    A period counts as complete only once its end (``bar.epoch + period_seconds``) is at or
    before ``as_of`` (never the still-forming latest period) -- so a day's high/low/close become
    referenceable starting exactly at the FOLLOWING day's as-of, never earlier."""
    period_seconds = _PERIOD_SECONDS[timeframe]
    levels: list[dict] = []
    for i, b in enumerate(bars):
        if b.epoch + period_seconds > as_of_epoch:
            continue  # this period has not closed as of `as_of` -- never a lookahead peek
        for price in (b.high, b.low, b.close):
            touches = _touch_count(bars, price, tol_bps, i)
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


def compute_levels(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict:
    """The canonical ``GET /research/levels`` + MCP ``levels`` computation (single source of
    truth) -- every level for ``symbol`` derived from its stored bar series, as of
    ``as_of_epoch`` (a UTC epoch-seconds instant; the ROUTE parses the ISO string once, never
    here, so this function itself carries no lookahead-leaking default).

    Returns ``{"levels": [...], "no_bar_series_for_symbol": bool}`` -- an explicit, ADDITIVE
    honesty flag (the ``insufficient_sample`` precedent) rather than an ambiguous bare empty
    ``levels`` list: the flag is ``True`` only when NO stored, healthy series exists for
    ``symbol`` at all; a symbol WITH series but nothing derivable at this ``as_of`` reports
    ``False`` with an empty ``levels`` list -- an honest "no levels found", never fabricated.

    A stored series whose timeframe is outside ``config.sr_timeframe_weights`` (impossible today
    -- that set covers every ``bar_timeframes`` entry, pinned by a dedicated config test) would
    raise ``KeyError`` rather than silently skip or fabricate a weight."""
    records, _integrity_errors = store.list()
    matching = [r for r in records if r["symbol"] == symbol]
    if not matching:
        return {"levels": [], "no_bar_series_for_symbol": True}

    levels: list[dict] = []
    for timeframe, record in _select_one_series_per_timeframe(matching).items():
        weight = config.sr_timeframe_weights[timeframe]
        bars = _bars_as_of(store.load_bars(record["id"]), as_of_epoch)
        levels.extend(_swing_pivots(bars, timeframe, config.sr_pivot_lookback, config.sr_touch_tolerance_bps, weight))
        if timeframe in PRIOR_PERIOD_TIMEFRAMES:
            levels.extend(
                _prior_period_extremes(bars, timeframe, config.sr_touch_tolerance_bps, weight, as_of_epoch)
            )
    levels.sort(key=_sort_key)
    return {"levels": levels, "no_bar_series_for_symbol": False}
