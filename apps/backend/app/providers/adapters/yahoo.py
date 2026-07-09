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

``fetch_bars`` THIS ITERATION (J-01) maps ONLY the ``"1d"`` neutral timeframe to yfinance's ``"1d"``
interval — the full six-timeframe table (``1w/1d/4h/1h/5m/1m``) and the derived ``4h`` resample are
J-02 (do not build ahead, per the execution plan). A neutral timeframe not yet in ``_INTERVAL_MAP``
is, from THIS iteration's adapter, a genuinely unservable request: it honestly returns an empty
tuple — the SAME "no bars" answer Alpaca's own adapter gives for its embargoed-window case — which
the caller (``BarStore.record``) already turns into the existing, explicit ``EmptyBarWindowError``
(422 — no new exception type, no fabricated bars; mirrors the execution plan's Risk 4).

An unknown/delisted symbol and a genuinely empty window are BOTH answered by yfinance with an empty
DataFrame (verified directly against the live vendor — never a raised exception), so, exactly as
``fetch_bars``'s own protocol docstring already allows ("there is no separate unknown-symbol
distinction here"), a single honest empty tuple covers both cases.

The SDK is imported LAZILY inside ``fetch_bars`` only, so ``is_available`` and the no-op/honest-
raise paths below never pay its import cost (mirrors ``alpaca.py``'s lazy-import discipline) —
though in practice ``yfinance`` reuses this project's already-installed ``pandas``/``numpy``
(pulled in by ``alpaca-py``).
"""

from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator

from .base import HistoricalWindow, LiveRecord, MarketClock, RawBar, SymbolMatch

# Neutral bar-fetch timeframe -> yfinance ``interval`` string. ONLY the daily mapping this
# iteration (era-5 J-01); J-02 adds the remaining five (1w/4h/1h/5m/1m) plus the derived 4h
# resample. The ONE place a neutral timeframe is translated to a vendor string (mirrors Alpaca's
# own ``_TIMEFRAME_PARTS`` seam) — ``config.py`` owns only the neutral vocabulary.
_INTERVAL_MAP: dict[str, str] = {
    "1d": "1d",
}


class YahooAdapter:
    """The concrete Yahoo Finance adapter — keyless, bars-only (era-5, J-01)."""

    name = "yahoo"

    def is_available(self) -> bool:
        """Always ``True`` — Yahoo Finance's public bar data needs no credentials whatsoever."""
        return True

    # --- Bars (the ONE capability this adapter actually serves) --------------------------------

    def fetch_bars(
        self, symbol: str, start: datetime, end: datetime, timeframe: str
    ) -> tuple[RawBar, ...]:
        """Fetch the REAL daily OHLC candle series for ``symbol`` over ``[start, end)`` (J-01;
        only ``timeframe == "1d"`` is mapped this iteration — see the module docstring).

        Honest, never fabricated: a ``timeframe`` outside ``_INTERVAL_MAP`` (not yet built this
        iteration), an unknown/delisted symbol, and a genuinely empty window are ALL answered with
        an empty tuple (the caller's existing ``EmptyBarWindowError`` 422 path already handles
        "no bars" — no new exception type). ``volume`` is coerced to ``int``.
        """
        interval = _INTERVAL_MAP.get(timeframe)
        if interval is None:
            return ()  # not yet mapped this iteration (J-02) — honest empty, never fabricated

        import yfinance as yf  # lazy: the no-op/honest-raise paths below never pay this cost

        sym = symbol.strip().upper()
        history = yf.Ticker(sym).history(start=start, end=end, interval=interval)
        if history.empty:
            # Unknown/delisted symbol OR a genuinely empty window — yfinance answers BOTH with an
            # empty frame (verified against the live vendor), never an exception. No separate
            # unknown-symbol distinction exists here (the base protocol explicitly allows this for
            # fetch_bars); a single honest empty tuple covers both.
            return ()

        bars = [
            RawBar(
                sym,
                timeframe,
                ts.timestamp(),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            )
            for ts, row in history.iterrows()
        ]
        bars.sort(key=lambda b: b.epoch)  # defensive determinism (yfinance already returns ascending)
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
