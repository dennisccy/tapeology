"""The vendor-neutral market-data adapter seam (provider-agnostic anti-goal).

A ``MarketDataAdapter`` is the single seam behind which a concrete vendor (its SDK, its
credential names, its response shapes, its error types) is allowed to live. The engine, API,
providers, and the historical replay layer depend only on the *neutral* contract declared
here — vendor specifics never leak outward, so a second vendor is one new adapter module.

The neutral contract is:
  * ``RawTrade`` / ``RawQuote`` — plain, vendor-free records (a UTC epoch-seconds timestamp
    plus the fields the engine needs). The adapter translates the vendor's response into these.
  * ``RawBar`` (era-4, J-01) — a plain, vendor-free OHLC candle: symbol, timeframe label, a UTC
    bar-open epoch-seconds timestamp, open/high/low/close, volume. ``fetch_bars`` is the
    multi-timeframe historical-BAR counterpart to ``fetch_historical`` (which fetches raw
    trades/quotes); the adapter translates the vendor's bar response into these — never a vendor
    type crosses the seam.
  * ``HistoricalWindow`` — the result of one historical fetch (the symbol + its raw trades and
    quotes). ``HistoricalProvider`` maps these onto the engine's logical timeline.
  * ``SymbolNotTradable`` / ``NoDataForWindow`` — neutral failures the adapter raises so the
    API can map them to explicit, distinct HTTP errors WITHOUT importing any vendor type. They
    are the *honest* real-data failure modes (no fabricated tape ever takes their place).
  * ``SymbolMatch`` — one symbol-search suggestion (symbol + name).
  * ``MarketClock`` — the market session status (open/closed + next open/close as ISO-8601 UTC
    strings). Read by the Live market-status indicator and the live-watch pre-flight gate; the
    adapter only ever builds it from a real vendor reply (a credential/network failure surfaces
    as an explicit unavailable or an exception, never a fabricated session).

This seam carries no network call by itself and never fabricates an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncIterator, Protocol, Union, runtime_checkable


def split_window(start, end, chunk_seconds: float) -> list[tuple]:
    """Split ``[start, end)`` into bounded contiguous sub-windows of at most ``chunk_seconds`` (J-34/J-37).

    Pure and deterministic (no network, no vendor): returns ``(sub_start, sub_end)`` tuples that
    PARTITION ``[start, end)`` with NO overlap and NO gap (each sub-window's end is the next one's
    start; the last ends exactly at ``end``), so stitching the sub-windows' real prints reconstructs
    the full real window with nothing fabricated, dropped, reordered, or de-duplicated. A window
    at/under ``chunk_seconds`` (or non-datetime / non-positive chunk) returns a single
    ``[(start, end)]`` — the single-call fast path. Lives in the NEUTRAL adapter base (not the vendor
    module) so the API can decide single-shot vs. progressive load without importing a vendor."""
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return [(start, end)]
    if chunk_seconds <= 0:
        return [(start, end)]
    span = (end - start).total_seconds()
    if span <= chunk_seconds:
        return [(start, end)]
    step = timedelta(seconds=chunk_seconds)
    ranges: list[tuple] = []
    cursor = start
    while cursor < end:
        nxt = min(cursor + step, end)
        ranges.append((cursor, nxt))
        cursor = nxt
    return ranges


@dataclass(frozen=True)
class RawTrade:
    """A vendor-neutral executed trade: UTC epoch seconds, price, size.

    The four trailing fields are the Card-5.1 data-preservation prerequisite (era "The Rapid
    Microscope" J-06 step 1, ``docs/rapid-validation-spec.md`` section 7.1 r2) — OPTIONAL,
    default-``None`` immutable vendor identifiers populated ONLY when the concrete adapter's SDK
    response actually carries them: ``conditions`` (the trade condition codes), ``exchange`` (the
    venue the trade occurred on), ``tape``, and ``trade_id`` (the vendor's own trade id — named
    ``trade_id`` rather than ``id`` to avoid shadowing the builtin). Absent-key backward
    compatible: every existing construction call site (none of which pass these) is unaffected,
    and the frozen engine never reads them (they exist for research consumers only)."""

    epoch: float
    price: float
    size: int
    conditions: list[str] | None = None
    exchange: str | None = None
    tape: str | None = None
    trade_id: int | None = None


@dataclass(frozen=True)
class RawQuote:
    """A vendor-neutral top-of-book quote: UTC epoch seconds, bid/ask and their sizes.

    The four trailing fields are the SAME Card-5.1 preservation prerequisite ``RawTrade`` carries
    (see its docstring), quote-shaped: ``conditions`` (the quote condition codes), ``tape``, and
    the bid/ask venue equivalents ``bid_exchange``/``ask_exchange`` — optional, default-``None``,
    populated only when the adapter's SDK response provides them."""

    epoch: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    conditions: list[str] | None = None
    tape: str | None = None
    bid_exchange: str | None = None
    ask_exchange: str | None = None


@dataclass(frozen=True)
class HistoricalWindow:
    """One historical fetch: the symbol plus its raw trades and quotes (ascending epoch)."""

    symbol: str
    trades: tuple[RawTrade, ...]
    quotes: tuple[RawQuote, ...]


@dataclass(frozen=True)
class RawBar:
    """A vendor-neutral OHLC candle (era-4, J-01): symbol, timeframe label (e.g. ``"1d"``), the
    UTC bar-OPEN epoch-seconds timestamp, open/high/low/close, volume. Self-describing (unlike
    ``RawTrade``/``RawQuote``, which rely on the enclosing ``HistoricalWindow`` for their symbol)
    because a stored bar series' individual candles are served directly (embedded on the series'
    metadata) rather than through a second wrapper type."""

    symbol: str
    timeframe: str
    epoch: float
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class SymbolMatch:
    """One symbol-search suggestion."""

    symbol: str
    name: str


@dataclass(frozen=True)
class MarketClock:
    """Vendor-neutral market session status: open/closed + next open/close.

    ``is_open`` is the authoritative open/closed flag from the vendor. ``next_open`` and
    ``next_close`` are ISO-8601 **UTC** strings (e.g. ``2026-06-05T13:30:00Z``) or ``None`` when
    the vendor omits them. The adapter constructs this ONLY from a successful vendor reply, so an
    instance always carries a real ``is_open``; a missing credential or an unreachable vendor is
    surfaced as an explicit unavailable (at the API) or an exception — never a fabricated session.
    """

    is_open: bool
    next_open: str | None
    next_close: str | None


# A single live-stream record: a vendor-neutral trade or quote (the live ``stream_live`` yields
# these; ``LiveProvider`` maps each onto the engine's logical timeline).
LiveRecord = Union[RawTrade, RawQuote]


class SymbolNotTradable(Exception):
    """The requested symbol is unknown / not a tradable symbol (neutral; no vendor type)."""


class NoDataForWindow(Exception):
    """The symbol is tradable but the requested window returned no trades/quotes (neutral)."""


class UnsupportedTimeframe(Exception):
    """A ``fetch_bars`` ``timeframe`` this vendor does not serve at all (neutral; no vendor type;
    era-5 J-02). Distinct from ``NoDataForWindow``: this is statically knowable from the
    timeframe value alone, with NO vendor call — e.g. a config-registered ``bar_timeframes``
    entry (``8h`` / ``1mo`` / ``15m``) that Yahoo Finance's adapter does not map this era, as
    opposed to a mapped/servable timeframe whose specific symbol/window legitimately returns
    nothing (that stays ``NoDataForWindow``). Raised by the adapter BEFORE any network call."""


class VendorTimeout(Exception):
    """A vendor call exceeded the real call-level HTTP deadline (J-28 / bounded-honest-vendor).

    Raised by the adapter when the SDK client's underlying HTTP request times out — the TRUE
    call-level bound, distinct from the API's outer ``asyncio.wait_for`` wrapper (which only
    abandons the worker thread). It is a NEUTRAL failure (no vendor exception type leaks out) the
    API maps to the existing row-9 ``provider_timeout`` reason. ``detail`` carries the human
    message: a generic "market data provider timed out" by default, or a more ACTIONABLE variant
    for a deterministically-oversized/high-volume historical window (e.g. "that window is very
    high-volume — try a shorter range") so the user is told the real cause, not a misleading retry.
    """

    def __init__(self, detail: str = "market data provider timed out") -> None:
        super().__init__(detail)
        self.detail = detail


@runtime_checkable
class MarketDataAdapter(Protocol):
    """Vendor-neutral seam the API reads for availability, history, and symbol search.

    ``name`` identifies the vendor for diagnostics. ``is_available()`` is ``True`` only when the
    vendor's credentials are present in the environment (no network, no fabrication).
    ``fetch_historical`` returns a ``HistoricalWindow`` or raises ``SymbolNotTradable`` /
    ``NoDataForWindow``. ``search_symbols`` returns matching tradable ``SymbolMatch`` rows (an
    empty list — never an error — when there is nothing to suggest). ``get_market_clock`` returns
    the real ``MarketClock`` (read-only reference call — it places/echoes no order); a vendor or
    network failure propagates as an exception the API degrades to an explicit unavailable.
    ``stream_live`` opens the vendor's real-time trade+quote socket for ONE symbol and yields
    vendor-neutral ``LiveRecord``s (market data only — no order/account/position call); on
    cancel/close it MUST unsubscribe and close the socket (no leaked connection).
    ``warm_symbol_universe`` pre-loads the tradable-symbol cache so the first ``search_symbols``
    after startup is not a cold stall (J-30); it is a no-op without credentials or when already
    warmed, and it is the neutral entry the API's startup hook calls so ``main.py`` never names a
    vendor SDK or the universe cache. It MUST NOT raise (a warm failure is swallowed — search then
    falls back to its own lazy fetch).
    ``fetch_bars`` (era-4, J-01) returns the REAL OHLC candle series for ``symbol`` over
    ``[start, end)`` at the given neutral ``timeframe`` as an ordered tuple of ``RawBar`` (never a
    vendor type) — a read-only reference call, like ``fetch_historical``. An empty tuple is a
    normal, honest "no bars" answer (never fabricated); the caller (the bar store's ``record``)
    decides how to surface that as an explicit refusal. Unlike ``fetch_historical``, there is no
    separate unknown-symbol distinction here — a bar recording is an explicit, occasional research
    action (not the watch hot-path), so a single round-trip returning empty is honest enough on
    its own.
    """

    name: str

    def is_available(self) -> bool:
        ...

    def fetch_historical(self, symbol: str, start, end) -> HistoricalWindow:
        ...

    def fetch_bars(self, symbol: str, start, end, timeframe: str) -> tuple[RawBar, ...]:
        ...

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        ...

    def get_market_clock(self) -> MarketClock:
        ...

    def stream_live(self, symbol: str) -> AsyncIterator[LiveRecord]:
        ...

    def warm_symbol_universe(self) -> None:
        ...
