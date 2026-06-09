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
# spread_change, liquidity_imbalance — are added additively in their owning iterations.)
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
    # Absorption triplet (price impact, not aggression).
    "absorption_score",
    "bid_refresh_score",
    "ask_refresh_score",
    # The price-relative basis (J-33): the instrument's in-window price LEVEL, computed ONCE here so
    # the classifier can judge spread/impact RELATIVE to price (spread in bps, impact as a return)
    # instead of via an absolute dollar constant tuned for the simulator. Single source of truth —
    # the classifier reads this, it never recomputes price.
    "reference_price",
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class _Window:
    """One rolling window of a fixed logical length (seconds)."""

    def __init__(self, length: int, config: Config) -> None:
        self.length = length
        self._config = config
        # (timestamp, price, size, side)
        self._trades: deque[tuple[float, float, int, Side]] = deque()
        # (timestamp, bid, ask, spread) — bid/ask threaded additively for the refresh scores;
        # spread is still stored verbatim so ``average_spread`` is computed unchanged.
        self._quotes: deque[tuple[float, float, float, float]] = deque()

    def add_trade(self, ts: float, price: float, size: int, side: Side) -> None:
        self._trades.append((ts, price, size, side))

    def add_quote(self, ts: float, bid: float, ask: float, spread: float) -> None:
        self._quotes.append((ts, bid, ask, spread))

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

        large_prints = sum(1 for t in self._trades if t[2] >= self._config.large_print_size)
        average_spread = fmean(q[3] for q in self._quotes) if self._quotes else 0.0

        # Price-relative basis (J-33): the in-window price LEVEL the classifier normalises spread
        # and impact against. Prefer the average quote MID-price (the cleanest level indicator);
        # fall back to the average trade price when there are no quotes, and to 0.0 when the window
        # is empty (the classifier then treats it as "no basis" and uses its absolute fallback — a
        # cold/empty window stays honest, never a fabricated relative read). Computed ONCE here.
        if self._quotes:
            reference_price = fmean((q[1] + q[2]) / 2.0 for q in self._quotes)
        elif self._trades:
            reference_price = fmean(t[1] for t in self._trades)
        else:
            reference_price = 0.0

        buy_ratio = (buy_volume / directional) if directional else 0.0
        sell_ratio = (sell_volume / directional) if directional else 0.0

        quotes = list(self._quotes)
        # bid_refresh: among aggressive-SELL prints, fraction at which the bid HELD (did not
        # fall below its in-window high). ask_refresh: among aggressive-BUY prints, fraction
        # at which the ask HELD (did not rise above its in-window low). High when the quote
        # absorbs (SIM-BIDABS / SIM-ASKABS); low when it walks (SIM-SELLER / SIM-BUYER).
        bid_refresh = self._refresh_fraction(quotes, Side.SELL, price_index=1, track_max=True)
        ask_refresh = self._refresh_fraction(quotes, Side.BUY, price_index=2, track_max=False)

        return {
            "trade_speed": trade_count / self.length,
            "volume_speed": total_volume / self.length,
            "aggressive_buy_ratio": buy_ratio,
            "aggressive_sell_ratio": sell_ratio,
            "net_aggressive_volume": float(buy_volume - sell_volume),
            "buy_price_impact": buy_impact,
            "sell_price_impact": sell_impact,
            "average_spread": average_spread,
            "large_print_count": float(large_prints),
            "absorption_score": self._absorption_score(
                buy_ratio, sell_ratio, buy_impact, sell_impact
            ),
            "bid_refresh_score": bid_refresh,
            "ask_refresh_score": ask_refresh,
            "reference_price": reference_price,
        }

    def _refresh_fraction(
        self,
        quotes: list[tuple[float, float, float, float]],
        side: Side,
        price_index: int,
        track_max: bool,
    ) -> float:
        """Fraction of ``side`` prints at which the quote held against its high/low-water mark.

        For each matching print the in-effect quote is the last quote with ``ts <= trade ts``
        (a forward merge over the ts-ordered series). bid uses a running MAX (held = bid did
        not fall below its prior high); ask uses a running MIN (held = ask did not rise above
        its prior low). 0.0 when there is no matching print (no evidence — never fabricated)."""
        qi = 0
        n = len(quotes)
        current: float | None = None
        watermark: float | None = None
        refreshed = 0
        total = 0
        for tts, _price, _size, tside in self._trades:
            while qi < n and quotes[qi][0] <= tts:
                current = quotes[qi][price_index]
                qi += 1
            if tside is not side or current is None:
                continue
            total += 1
            if watermark is None:
                refreshed += 1
                watermark = current
            else:
                held = current >= watermark if track_max else current <= watermark
                if held:
                    refreshed += 1
                watermark = max(watermark, current) if track_max else min(watermark, current)
        return (refreshed / total) if total else 0.0

    def _absorption_score(
        self, buy_ratio: float, sell_ratio: float, buy_impact: float, sell_impact: float
    ) -> float:
        """Summary of "high one-sided aggression with little/no price progress".

        Take the dominant aggressive side; the score is high only when that side's ratio is
        strong AND its price impact is flat (near zero). Real directional progress collapses
        the flatness term to zero, so control scenarios read ~0 here."""
        c = self._config
        if buy_ratio >= sell_ratio:
            dom_ratio, dom_impact, dom_floor = buy_ratio, buy_impact, c.min_aggressive_buy_ratio
        else:
            dom_ratio, dom_impact, dom_floor = sell_ratio, sell_impact, c.min_aggressive_sell_ratio
        ratio_strength = _clamp01((dom_ratio - dom_floor) / c.ratio_scale)
        flatness = _clamp01(1.0 - abs(dom_impact) / c.absorption_flat_band)
        return ratio_strength * flatness


class FeatureEngine:
    """Maintains all configured windows concurrently; the canonical feature producer."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._windows: dict[int, _Window] = {
            w: _Window(w, config) for w in config.windows
        }

    def add_trade(self, ts: float, price: float, size: int, side: Side) -> None:
        for window in self._windows.values():
            window.add_trade(ts, price, size, side)

    def add_quote(self, ts: float, bid: float, ask: float, spread: float) -> None:
        for window in self._windows.values():
            window.add_quote(ts, bid, ask, spread)

    def compute(self, now_ts: float) -> dict[str, dict[str, float]]:
        """Feature values for every window, keyed by window label (e.g. ``"30s"``)."""
        return {
            self._config.window_label(length): window.compute(now_ts)
            for length, window in self._windows.items()
        }
