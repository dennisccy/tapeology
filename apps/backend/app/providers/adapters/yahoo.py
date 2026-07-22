"""Yahoo Finance market-data adapter (era-5 "The Library", J-01) — the SINGLE module where Yahoo
specifics (the ``yfinance`` SDK, its response shapes) live.

This is the SECOND concrete adapter behind the vendor-neutral ``MarketDataAdapter`` seam (the
provider-agnostic-engine anti-goal in practice — a second vendor is one new adapter module, exactly
as ``providers/adapters/base.py`` promises). Unlike ``AlpacaAdapter``, Yahoo Finance is:

  * **Keyless** — ``is_available()`` is unconditionally ``True``; there are no credentials to
    detect, ever (era-5's headline promise: real bars, fetched for $0 with no signup).
  * **Bars-only** — Yahoo serves OHLC candles and nothing else. ``fetch_historical`` (trades/
    quotes) and ``get_market_clock`` and ``stream_live`` HONESTLY RAISE ``NotImplementedError``
    rather than fabricate a trade tape, a session clock, or a live socket; ``search_symbols``
    honestly returns ``[]`` (no symbol-search reference is offered); ``warm_symbol_universe`` is a
    no-op (MUST NOT raise, per the base seam's own contract — there is nothing here to warm). None
    of these five methods is reachable through this era's bar-fetch-only vendor selector (only
    ``fetch_bars`` and ``is_available`` are called on this adapter in production this iteration —
    see ``research/routes.py::get_bar_fetch_adapter``); they exist so the adapter satisfies the
    ``MarketDataAdapter`` protocol honestly, not because this era's product surface exercises them.

``fetch_bars`` maps the FIVE directly-fetched era-5 neutral timeframes (``1w/1d/1h/5m/1m``) to their
real yfinance interval strings via ``_INTERVAL_MAP`` (each confirmed against the live vendor, era-5
J-02). The SIXTH, ``4h``, is not a vendor interval this adapter ever requests — it is a pure,
deterministic LOCAL resample of real ``1h`` bars (the era's one named new backend computation,
confined entirely to this module; see ``_resample_4h`` below). yfinance 1.5.1 happens to also expose
its OWN native ``"4h"`` interval string (verified live) — this adapter deliberately never uses it:
the goal's anti-goal is explicit that ``4h`` is "honestly derived" and "never presented as a
vendor-native fetch," so the resample stays local and testable regardless of what the vendor itself
offers (empirically cross-checked live: this module's resample of real ``1h`` bars is
bucket-for-bucket identical to yfinance's own native ``4h`` series on the same window).

Three honestly DISTINCT, never-fabricated outcomes exist for a bar-fetch request (era-5 J-02):
  * A timeframe outside ``_INTERVAL_MAP`` and not ``"4h"`` (e.g. ``8h``/``1mo``/``15m`` — all valid
    ``CONFIG.bar_timeframes`` entries this era's Yahoo adapter simply does not map) is STATICALLY
    knowable with no vendor call at all: ``fetch_bars`` raises ``UnsupportedTimeframe`` up front,
    before the lazy ``yfinance`` import even runs.
  * A MAPPED/servable timeframe whose specific symbol/window genuinely returns nothing from the
    vendor (an unknown/delisted symbol OR a real window outside that timeframe's retention —
    yfinance answers BOTH with an empty DataFrame, verified directly against the live vendor, never
    a raised exception, so — exactly as ``fetch_bars``'s own protocol docstring already allows
    ("there is no separate unknown-symbol distinction here") — a single honest signal covers both)
    raises the EXISTING neutral ``NoDataForWindow``.
  * A real vendor call that times out surfaces as the existing ``VendorTimeout`` (unchanged).
None of the three ever writes, pads, forward-fills, or fabricates a bar.

The SDK is imported LAZILY inside ``fetch_bars`` only, so ``is_available`` and the no-op/honest-
raise paths below never pay its import cost (mirrors ``alpaca.py``'s lazy-import discipline) —
though in practice ``yfinance`` reuses this project's already-installed ``pandas``/``numpy``
(pulled in by ``alpaca-py``).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import AsyncIterator

from .base import (
    HistoricalWindow,
    LiveRecord,
    MarketClock,
    NoDataForWindow,
    RawBar,
    SymbolMatch,
    UnsupportedTimeframe,
)

# Neutral bar-fetch timeframe -> yfinance ``interval`` string (era-5 J-01 + J-02 — the FIVE
# directly-fetched timeframes; each confirmed against the live vendor, not assumed from docs
# alone). ``4h`` is deliberately NOT an entry here — it is never requested from the vendor as its
# own interval; ``fetch_bars`` special-cases it into a local resample of ``"1h"`` (see
# ``_resample_4h``). The ONE place a neutral timeframe is translated to a vendor string (mirrors
# Alpaca's own ``_TIMEFRAME_PARTS`` seam) — ``config.py`` owns only the neutral vocabulary.
_INTERVAL_MAP: dict[str, str] = {
    "1d": "1d",
    "1w": "1wk",
    "1h": "1h",
    "5m": "5m",
    "1m": "1m",
}

# Yahoo's per-interval history limits, MEASURED against the live vendor (never assumed from docs) —
# ``interval -> (max lookback days, max days per request)``; an absent entry means "no limit".
# The vendor enforces these by returning an EMPTY frame plus a printed error, never an exception:
#
#   1m  "Only 8 days worth of 1m granularity data are allowed to be fetched per request"
#       (and nothing older than ~30 days: a 7-day window 33 days back is empty, 25 days back is fine)
#   5m  "5m data not available for startTime=... The requested range must be within the last 60 days"
#       (a 58-day window returns 3,042 rows; a 14-day window 75 days back is empty)
#   1h  ~730 days (a 60-day window 700 days back returns 294 rows; 800 days back is empty)
#   1d/1wk  unlimited (a 200-day window 8 years back returns 139 rows)
#
# Before these were honoured, ONE over-long request turned a partially-servable window into nothing at
# all: asking for 1m over 2026-01-01..07-21 recorded no series, rather than the 30 days Yahoo does
# serve. ``1m``'s per-request cap is set to 7 (not the vendor's stated 8) to keep a margin under a
# boundary the vendor evaluates against its own clock.
_INTERVAL_LIMITS: dict[str, tuple[int, int]] = {
    "1m": (30, 7),
    "5m": (60, 60),
    "1h": (730, 730),
}

# The 4h resampler's two tunables (era-5 J-02) — deliberately local constants, not ``config.py``
# fields: they shape ONLY the confined-to-this-module derived-4h computation, never a persisted
# tape/backtest/study value, so they carry none of ``config.py``'s fingerprint-stability
# discipline. ``_FOUR_HOUR_BUCKET_SIZE``: four real ``1h`` bars aggregate into one ``4h`` candle.
# ``_SESSION_GAP_SECONDS``: a gap larger than this between two consecutive ``1h`` bars marks the
# start of a NEW trading session — the overnight/weekend/holiday gap between sessions is always far
# larger than the ~1-hour spacing WITHIN one, whatever the exchange's actual local open time is, so
# this data-driven detector needs no hardcoded exchange hours or timezone conversion.
_FOUR_HOUR_BUCKET_SIZE = 4
_SESSION_GAP_SECONDS = 2 * 3600.0


def _clamp_to_retention(
    start: datetime, end: datetime, interval: str, limits: tuple[int, int] | None
) -> tuple[datetime | None, str | None]:
    """Trim ``start`` forward to the oldest instant this ``interval`` can still serve.

    Returns ``(fetch_start, limit_note)``. ``fetch_start is None`` means the ENTIRE requested window
    predates what the vendor keeps, so there is nothing worth asking for; ``limit_note`` is a plain
    sentence naming the limit (``None`` when no limit applied) that the route stores alongside the
    recording and the UI shows, so a short result is never mistaken for "that is all the data there
    is". Clamping rather than refusing is deliberate: an operator asking for six months of 1m gets
    the 30 days Yahoo actually serves instead of nothing at all."""
    if limits is None:
        return start, None
    retention_days, _ = limits
    horizon = datetime.now(tz=start.tzinfo) - timedelta(days=retention_days)
    if end <= horizon:
        return None, (
            f"Yahoo Finance serves {interval} bars only for the last {retention_days} days, and the "
            f"requested window ends before that"
        )
    if start >= horizon:
        return start, None
    return horizon, (
        f"Yahoo Finance serves {interval} bars only for the last {retention_days} days, so the "
        f"requested start was moved forward to {horizon.date().isoformat()}"
    )


def _chunks(start: datetime, end: datetime, limits: tuple[int, int] | None) -> list[tuple[datetime, datetime]]:
    """Split ``[start, end)`` into consecutive half-open windows no longer than the interval's
    per-request cap (Yahoo refuses an over-long 1m request outright — "Only 8 days worth of 1m
    granularity data are allowed to be fetched per request" — and answers with an empty frame).
    Without a cap this is the single window it always was."""
    if limits is None:
        return [(start, end)]
    span = timedelta(days=limits[1])
    windows: list[tuple[datetime, datetime]] = []
    cursor = start
    while cursor < end:
        stop = min(cursor + span, end)
        windows.append((cursor, stop))
        cursor = stop
    return windows or [(start, end)]


def _resample_4h(hourly: tuple[RawBar, ...]) -> tuple[RawBar, ...]:
    """Deterministically resample REAL ``1h`` bars into aligned 4-hour buckets (era-5 J-02 — the
    era's single named new backend computation, confined entirely to this module; never duplicated
    in ``bars.py``, ``research/levels.py``, or a route).

    Buckets reset at the start of each trading SESSION rather than at a naive wall-clock
    ``epoch % 14400`` boundary: a gap of more than ``_SESSION_GAP_SECONDS`` between two consecutive
    ``1h`` bars marks a new session (see the module-level constant's rationale above). Within a
    session, bars are grouped ``_FOUR_HOUR_BUCKET_SIZE`` at a time in arrival order — open=first,
    high=max, low=min, close=last, volume=sum; a session whose bar count is not an exact multiple
    of four (a 6.5-hour regular session yields 7 real ``1h`` bars) naturally ends in a SHORTER
    trailing bucket built from only the bars that actually exist — never padded, forward-filled, or
    given a future bar (the no-lookahead rail). Empirically cross-checked against yfinance's own
    native ``"4h"`` interval on a live AAPL window: bucket-for-bucket byte-identical OHLCV.

    Pure function of ``hourly`` (already ascending epoch — ``fetch_bars``'s own contract): no
    wall-clock read, no unseeded state, so two identical calls produce byte-identical output. An
    empty input honestly returns an empty output (in practice unreachable via ``fetch_bars`` itself
    — an empty ``1h`` fetch already raises ``NoDataForWindow`` before this is ever called — kept
    here so the function is honest and testable standalone).
    """
    buckets: list[list[RawBar]] = []
    prev_epoch: float | None = None
    for bar in hourly:
        starts_new_bucket = (
            not buckets
            or (bar.epoch - prev_epoch) > _SESSION_GAP_SECONDS
            or len(buckets[-1]) >= _FOUR_HOUR_BUCKET_SIZE
        )
        if starts_new_bucket:
            buckets.append([])
        buckets[-1].append(bar)
        prev_epoch = bar.epoch

    return tuple(
        RawBar(
            bucket[0].symbol,
            "4h",
            bucket[0].epoch,
            bucket[0].open,
            max(b.high for b in bucket),
            min(b.low for b in bucket),
            bucket[-1].close,
            sum(b.volume for b in bucket),
        )
        for bucket in buckets
    )


class YahooAdapter:
    """The concrete Yahoo Finance adapter — keyless, bars-only (era-5, J-01)."""

    name = "yahoo"

    def is_available(self) -> bool:
        """Always ``True`` — Yahoo Finance's public bar data needs no credentials whatsoever."""
        return True

    # --- Bars (the ONE capability this adapter actually serves) --------------------------------

    def bar_fetch_limit(self, timeframe: str, start: datetime, end: datetime) -> str | None:
        """The vendor cap that WILL shorten (or refuse) this exact fetch, as a plain sentence —
        ``None`` when the window is served in full.

        An OPTIONAL adapter capability: the recording route asks for it with ``getattr`` and stores
        whatever it gets, so an adapter without it (Alpaca, the fakes) is simply an adapter with no
        caps to declare. It exists so a shortened recording carries the REASON it is short instead
        of leaving a reader to infer one from a gap — the same clamp logic ``fetch_bars`` itself
        applies, asked ahead of time rather than re-derived."""
        interval = "1h" if timeframe == "4h" else _INTERVAL_MAP.get(timeframe)
        if interval is None:
            return None
        _fetch_start, note = _clamp_to_retention(start, end, interval, _INTERVAL_LIMITS.get(interval))
        return note

    def fetch_bars(
        self, symbol: str, start: datetime, end: datetime, timeframe: str
    ) -> tuple[RawBar, ...]:
        """Fetch the REAL OHLC candle series for ``symbol`` over ``[start, end)`` at ``timeframe``
        (era-5 J-02: the five directly-mapped timeframes, plus the derived ``4h`` resample — see
        the module docstring for the full three-way honest-error taxonomy).

        Honest, never fabricated: a ``timeframe`` this adapter does not serve raises
        ``UnsupportedTimeframe`` (statically knowable — zero vendor calls); a mapped/servable
        timeframe whose specific symbol/window returns nothing from the vendor raises
        ``NoDataForWindow``. ``volume`` is coerced to ``int``.
        """
        if timeframe == "4h":
            # NOT a yfinance interval this adapter ever requests — a pure, deterministic local
            # resample of the real 1h bars (``_resample_4h``). The recursive call may itself raise
            # ``NoDataForWindow``/``UnsupportedTimeframe`` — honestly propagated, never swallowed.
            hourly = self.fetch_bars(symbol, start, end, "1h")
            return _resample_4h(hourly)

        interval = _INTERVAL_MAP.get(timeframe)
        if interval is None:
            raise UnsupportedTimeframe(f"timeframe '{timeframe}' is not served by Yahoo Finance")

        import yfinance as yf  # lazy: the no-op/honest-raise paths below never pay this cost

        sym = symbol.strip().upper()
        limits = _INTERVAL_LIMITS.get(interval)
        fetch_start, limit_note = _clamp_to_retention(start, end, interval, limits)
        if fetch_start is None:
            # The ENTIRE requested window sits outside what this interval can serve — nothing to
            # ask the vendor for. Honest and specific (it names the limit), never a silent empty
            # result and never a guess about the symbol.
            raise NoDataForWindow(
                f"no data for {sym} {timeframe} in the requested window "
                f"{start.isoformat()}..{end.isoformat()} — {limit_note}"
            )

        ticker = yf.Ticker(sym)
        rows_by_epoch: dict[float, RawBar] = {}
        for chunk_start, chunk_end in _chunks(fetch_start, end, limits):
            history = ticker.history(start=chunk_start, end=chunk_end, interval=interval)
            if history.empty:
                # One empty chunk is NOT fatal: a holiday week inside a longer window legitimately
                # has no bars, and failing the whole fetch over it would discard every real bar the
                # other chunks returned. An all-empty result still raises below.
                continue
            for ts, row in history.iterrows():
                bar = RawBar(
                    sym,
                    timeframe,
                    ts.timestamp(),
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                )
                # Chunk bounds are half-open and non-overlapping, so a duplicate epoch means the
                # vendor served the same bar twice; keep ONE (the later read wins, as within a
                # single frame) rather than emitting a duplicated candle.
                rows_by_epoch[bar.epoch] = bar

        if not rows_by_epoch:
            # Unknown/delisted symbol OR a genuinely empty window — yfinance answers BOTH with an
            # empty frame (verified against the live vendor), never an exception. No separate
            # unknown-symbol distinction exists here (the base protocol explicitly allows this for
            # fetch_bars); a single honest NoDataForWindow covers both, now naming the limit that
            # applied when one did.
            detail = limit_note or "Yahoo Finance returned nothing for that window (the symbol may be unknown)"
            raise NoDataForWindow(
                f"no data for {sym} {timeframe} in the requested window "
                f"{start.isoformat()}..{end.isoformat()} — {detail}"
            )

        bars = sorted(rows_by_epoch.values(), key=lambda b: b.epoch)
        return tuple(bars)

    # --- Everything else: honestly bars-only (never fabricated) --------------------------------

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        """Yahoo serves no trade/quote tape. Honestly raises rather than fabricating a window —
        never reached in production this era (arbitrary-window studies and historical-dataset
        recording stay on ``get_study_market_adapter()``'s existing Alpaca-only default,
        untouched this iteration)."""
        raise NotImplementedError(
            "YahooAdapter is bars-only — fetch_historical (trades/quotes) is not supported"
        )

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        """No symbol-search reference is offered by this adapter — an honest empty list (never an
        error), the same "nothing to suggest" contract every adapter uses for zero matches."""
        return []

    def get_market_clock(self) -> MarketClock:
        """Yahoo offers no live session-clock reference. Honestly raises rather than fabricating a
        session."""
        raise NotImplementedError("YahooAdapter is bars-only — get_market_clock is not supported")

    def stream_live(self, symbol: str) -> AsyncIterator[LiveRecord]:
        """Yahoo offers no real-time stream. A plain, immediate, synchronous raise — never a
        lazily-failing async generator — so a caller learns this adapter cannot stream before it
        even attempts to open a socket."""
        raise NotImplementedError("YahooAdapter is bars-only — stream_live is not supported")

    def warm_symbol_universe(self) -> None:
        """No-op — MUST NOT raise (the base seam's own contract). There is no symbol-search
        universe to warm (``search_symbols`` already honestly returns ``[]`` unconditionally)."""
        return None
