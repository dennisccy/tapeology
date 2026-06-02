"""Rolling-window feature computation, keyed on logical event timestamps.

All configured windows are maintained concurrently. Every feature is a pure function of
the events currently inside a window, so feeding the same ordered stream twice yields
identical values (determinism anti-goal) — there is no wall-clock or randomness here.

Price impact is the heart of the product: ``buy_price_impact`` is the cumulative price
change *on aggressive-buy prints* (each buy print's price minus the previous in-window
trade's price), and ``sell_price_impact`` the same on aggressive-sell prints. High buy
aggression with a flat price therefore produces ~0 buy impact — which is exactly what
lets the classifier key on impact, not raw aggression.
"""

from __future__ import annotations

from collections import deque
from statistics import fmean

from ..config import Config
from ..providers.base import Side

# Names of the features this iteration computes. (The remaining blueprint features —
# spread_change, absorption_score, bid/ask_refresh_score, liquidity_imbalance — are added
# additively in their owning iterations.)
FEATURE_NAMES = (
    "trade_speed",
    "volume_speed",
    "aggressive_buy_ratio",
    "aggressive_sell_ratio",
    "net_aggressive_volume",
    "buy_price_impact",
    "sell_price_impact",
    "average_spread",
    "large_print_count",
)


class _Window:
    """One rolling window of a fixed logical length (seconds)."""

    def __init__(self, length: int, large_print_size: int) -> None:
        self.length = length
        self._large_print_size = large_print_size
        # (timestamp, price, size, side)
        self._trades: deque[tuple[float, float, int, Side]] = deque()
        # (timestamp, spread)
        self._quotes: deque[tuple[float, float]] = deque()

    def add_trade(self, ts: float, price: float, size: int, side: Side) -> None:
        self._trades.append((ts, price, size, side))

    def add_quote(self, ts: float, spread: float) -> None:
        self._quotes.append((ts, spread))

    def _evict(self, now_ts: float) -> None:
        lo = now_ts - self.length
        while self._trades and self._trades[0][0] < lo:
            self._trades.popleft()
        while self._quotes and self._quotes[0][0] < lo:
            self._quotes.popleft()

    def compute(self, now_ts: float) -> dict[str, float]:
        self._evict(now_ts)

        trade_count = len(self._trades)
        total_volume = sum(t[2] for t in self._trades)

        buy_volume = sum(t[2] for t in self._trades if t[3] is Side.BUY)
        sell_volume = sum(t[2] for t in self._trades if t[3] is Side.SELL)
        directional = buy_volume + sell_volume

        buy_impact = 0.0
        sell_impact = 0.0
        prev_price: float | None = None
        for _ts, price, _size, side in self._trades:
            if prev_price is not None:
                delta = price - prev_price
                if side is Side.BUY:
                    buy_impact += delta
                elif side is Side.SELL:
                    sell_impact += delta
            prev_price = price

        large_prints = sum(1 for t in self._trades if t[2] >= self._large_print_size)
        average_spread = fmean(q[1] for q in self._quotes) if self._quotes else 0.0

        return {
            "trade_speed": trade_count / self.length,
            "volume_speed": total_volume / self.length,
            "aggressive_buy_ratio": (buy_volume / directional) if directional else 0.0,
            "aggressive_sell_ratio": (sell_volume / directional) if directional else 0.0,
            "net_aggressive_volume": float(buy_volume - sell_volume),
            "buy_price_impact": buy_impact,
            "sell_price_impact": sell_impact,
            "average_spread": average_spread,
            "large_print_count": float(large_prints),
        }


class FeatureEngine:
    """Maintains all configured windows concurrently; the canonical feature producer."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._windows: dict[int, _Window] = {
            w: _Window(w, config.large_print_size) for w in config.windows
        }

    def add_trade(self, ts: float, price: float, size: int, side: Side) -> None:
        for window in self._windows.values():
            window.add_trade(ts, price, size, side)

    def add_quote(self, ts: float, spread: float) -> None:
        for window in self._windows.values():
            window.add_quote(ts, spread)

    def compute(self, now_ts: float) -> dict[str, dict[str, float]]:
        """Feature values for every window, keyed by window label (e.g. ``"30s"``)."""
        return {
            self._config.window_label(length): window.compute(now_ts)
            for length, window in self._windows.items()
        }
