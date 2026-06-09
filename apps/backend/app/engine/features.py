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
    """One rolling window of a fixed logical length (seconds).

    PERFORMANCE (J-37 — engine handles real consolidated-tape density without stalling): a dense
    Full-RTH window carries tens of thousands of prints, and a naive per-tick rescan of the window
    is O(n²) — which made a real GME open-drop window take minutes. Every aggregate is therefore
    maintained INCREMENTALLY (O(1) amortised per event): running sums updated on append and on
    eviction. The values produced are BYTE-IDENTICAL to the prior full-rescan implementation
    (determinism + single-source-of-truth preserved — asserted by the existing feature tests and a
    progressive-vs-single-shot determinism test), only computed without the quadratic rescan.

    The in-effect quote (bid/ask) at each trade's instant is supplied by the engine at ``add_trade``
    time (it already holds it in ``MarketState``), so the refresh scores need no forward quote-merge.
    """

    def __init__(self, length: int, config: Config) -> None:
        self.length = length
        self._config = config
        # (timestamp, price, size, side, impact_delta, eff_bid, eff_ask) — each trade stores the
        # signed price delta vs the prior trade IN ARRIVAL ORDER (to keep impact incremental on
        # eviction) and the in-effect bid/ask at its instant (supplied by the engine; ``None`` for the
        # standalone FeatureEngine API, which falls back to a forward quote-merge at compute time).
        self._trades: deque[
            tuple[float, float, int, Side, float, float | None, float | None]
        ] = deque()
        # (timestamp, bid, ask, spread)
        self._quotes: deque[tuple[float, float, float, float]] = deque()

        # --- Incrementally-maintained running aggregates (the single source for compute()) -------
        self._total_volume = 0
        self._buy_volume = 0
        self._sell_volume = 0
        self._buy_impact = 0.0
        self._sell_impact = 0.0
        self._large_prints = 0
        self._spread_sum = 0.0
        self._mid_sum = 0.0       # Σ (bid+ask)/2 over in-window quotes (reference_price basis)
        self._price_sum = 0.0     # Σ trade price over in-window trades (reference fallback)
        # The price of the most-recently appended trade, so a new trade's impact_delta is computed
        # in O(1) at append (vs the prior trade in arrival order). ``None`` until the first trade.
        self._last_price: float | None = None

        # --- Incremental refresh-score state (J-37 perf) ----------------------------------------
        # bid_refresh / ask_refresh count the SELL/BUY prints whose in-effect bid/ask was at a new
        # window high/low (the quote "held"). When every trade arrives with its in-effect quote (the
        # engine path) AND nothing has been evicted, these counts update in O(1) on append — so a
        # dense burst that fits inside the window (e.g. the GME drop) never triggers a rescan. They
        # become stale on ANY eviction or when a trade lacked its in-effect quote (the standalone API),
        # in which case ``compute`` falls back to the exact forward-merge rescan. Either way the value
        # is byte-identical; only the cost differs.
        self._refresh_incremental = True   # False once we must fall back to the merge (eviction etc.)
        # True once ANY trade carried an in-effect quote (the engine path). The standalone FeatureEngine
        # API never threads one, so this stays False and ``compute`` uses the authoritative forward-merge
        # — keeping that API byte-identical while the engine path gets the O(1) incremental counts.
        self._refresh_has_eff = False
        self._bid_mark: float | None = None
        self._ask_mark: float | None = None
        self._bid_refreshed = 0
        self._bid_total = 0
        self._ask_refreshed = 0
        self._ask_total = 0

    def add_trade(
        self,
        ts: float,
        price: float,
        size: int,
        side: Side,
        eff_bid: float | None = None,
        eff_ask: float | None = None,
    ) -> None:
        # Impact delta vs the immediately preceding trade in arrival order (0.0 for the very first
        # trade or a non-directional print — it contributes nothing to either impact sum).
        delta = 0.0
        if self._last_price is not None:
            delta = price - self._last_price
            if side is Side.BUY:
                self._buy_impact += delta
            elif side is Side.SELL:
                self._sell_impact += delta
        self._trades.append((ts, price, size, side, delta, eff_bid, eff_ask))
        self._last_price = price
        self._total_volume += size
        self._price_sum += price
        if side is Side.BUY:
            self._buy_volume += size
        elif side is Side.SELL:
            self._sell_volume += size
        if size >= self._config.large_print_size:
            self._large_prints += 1

        # O(1) incremental refresh update (engine path). A SELL/BUY print with NO in-effect quote yet
        # (a trade before the first quote) contributes no refresh evidence — it is SKIPPED, exactly as
        # the forward-merge skips a print whose ``current`` quote is still None (so the two agree). The
        # standalone FeatureEngine API (no eff_* threaded) never reaches the SELL/BUY branches with a
        # value, so it naturally falls through with bid_total/ask_total == 0 here; ``compute`` then
        # serves the merge result whenever the incremental counts have no evidence (see compute()).
        if not self._refresh_incremental:
            return
        if eff_bid is not None or eff_ask is not None:
            self._refresh_has_eff = True  # the engine threaded an in-effect quote: use the O(1) path
        if side is Side.SELL:
            if eff_bid is None:
                return  # no in-effect quote — no refresh evidence (skip, do NOT disable)
            self._bid_total += 1
            if self._bid_mark is None or eff_bid >= self._bid_mark:
                self._bid_refreshed += 1
            self._bid_mark = eff_bid if self._bid_mark is None else max(self._bid_mark, eff_bid)
        elif side is Side.BUY:
            if eff_ask is None:
                return  # no in-effect quote — no refresh evidence (skip, do NOT disable)
            self._ask_total += 1
            if self._ask_mark is None or eff_ask <= self._ask_mark:
                self._ask_refreshed += 1
            self._ask_mark = eff_ask if self._ask_mark is None else min(self._ask_mark, eff_ask)

    def add_quote(self, ts: float, bid: float, ask: float, spread: float) -> None:
        self._quotes.append((ts, bid, ask, spread))
        self._spread_sum += spread
        self._mid_sum += (bid + ask) / 2.0

    def _evict(self, now_ts: float) -> None:
        lo = now_ts - self.length
        while self._trades and self._trades[0][0] < lo:
            _ts, price, size, side, _delta, _eb, _ea = self._trades.popleft()
            # A trade left the window, so the incremental refresh counts (which assume an append-only
            # window) are no longer valid — fall back to the exact forward-merge rescan for refresh.
            # (Sums/impact stay incremental; only the order-dependent refresh needs the rescan.)
            self._refresh_incremental = False
            self._total_volume -= size
            self._price_sum -= price
            if side is Side.BUY:
                self._buy_volume -= size
            elif side is Side.SELL:
                self._sell_volume -= size
            if size >= self._config.large_print_size:
                self._large_prints -= 1
            # The NEW oldest trade no longer has a predecessor inside the window, so its stored
            # impact_delta (computed vs the just-evicted trade) must be removed from the impact sum
            # — keeping buy/sell impact EXACTLY the cumulative in-window consecutive-delta sum the
            # full rescan produced. (Only the boundary trade is affected; everything else is intact.)
            if self._trades:
                new_oldest = self._trades[0]
                d = new_oldest[4]
                if new_oldest[3] is Side.BUY:
                    self._buy_impact -= d
                elif new_oldest[3] is Side.SELL:
                    self._sell_impact -= d
        while self._quotes and self._quotes[0][0] < lo:
            _ts, bid, ask, spread = self._quotes.popleft()
            # A quote leaving the window can change the in-effect quote the merge sees for an early
            # trade, so the incremental refresh (which used the engine's true in-effect quote) must
            # also drop to the merge once any quote is evicted — keeping the two paths in agreement.
            self._refresh_incremental = False
            self._spread_sum -= spread
            self._mid_sum -= (bid + ask) / 2.0

    def compute(self, now_ts: float) -> dict[str, float]:
        self._evict(now_ts)

        trade_count = len(self._trades)
        quote_count = len(self._quotes)
        total_volume = self._total_volume
        buy_volume = self._buy_volume
        sell_volume = self._sell_volume
        directional = buy_volume + sell_volume
        buy_impact = self._buy_impact
        sell_impact = self._sell_impact

        average_spread = (self._spread_sum / quote_count) if quote_count else 0.0

        # Price-relative basis (J-33): prefer the average quote MID-price; fall back to the average
        # trade price when there are no quotes; 0.0 for an empty window (classifier treats as "no
        # basis"). Maintained as running sums so this is O(1) — identical value, no rescan.
        if quote_count:
            reference_price = self._mid_sum / quote_count
        elif trade_count:
            reference_price = self._price_sum / trade_count
        else:
            reference_price = 0.0

        buy_ratio = (buy_volume / directional) if directional else 0.0
        sell_ratio = (sell_volume / directional) if directional else 0.0

        # bid_refresh: among aggressive-SELL prints, fraction at which the bid HELD (did not fall
        # below its in-window high). ask_refresh: among aggressive-BUY prints, fraction at which the
        # ask HELD (did not rise above its in-window low). Served from the O(1) incremental counts
        # when valid (append-only window with in-effect quotes — the dense-burst case J-37 targets),
        # else from the exact forward-merge rescan. Both produce the identical value.
        if self._refresh_incremental and self._refresh_has_eff:
            bid_refresh = (self._bid_refreshed / self._bid_total) if self._bid_total else 0.0
            ask_refresh = (self._ask_refreshed / self._ask_total) if self._ask_total else 0.0
        else:
            bid_refresh, ask_refresh = self._refresh_fractions()

        return {
            "trade_speed": trade_count / self.length,
            "volume_speed": total_volume / self.length,
            "aggressive_buy_ratio": buy_ratio,
            "aggressive_sell_ratio": sell_ratio,
            "net_aggressive_volume": float(buy_volume - sell_volume),
            "buy_price_impact": buy_impact,
            "sell_price_impact": sell_impact,
            "average_spread": average_spread,
            "large_print_count": float(self._large_prints),
            "absorption_score": self._absorption_score(
                buy_ratio, sell_ratio, buy_impact, sell_impact
            ),
            "bid_refresh_score": bid_refresh,
            "ask_refresh_score": ask_refresh,
            "reference_price": reference_price,
        }

    def _refresh_fractions(self) -> tuple[float, float]:
        """Compute (bid_refresh, ask_refresh) in one forward-merge pass over the window.

        For each trade the in-effect quote is the last quote with ``ts <= trade ts`` (a two-pointer
        forward merge over the ts-ordered series — identical to the prior per-side ``_refresh_fraction``
        merge, just shared across both sides so the window is walked once, not twice). bid_refresh is
        over aggressive-SELL prints with a running-MAX watermark (held = bid did not fall below its
        prior high); ask_refresh is over aggressive-BUY prints with a running-MIN watermark. A side
        with no matching print (or with no in-effect quote yet) scores 0.0 — no fabricated evidence."""
        quotes = self._quotes
        qi = 0
        n = len(quotes)
        cur_bid: float | None = None
        cur_ask: float | None = None
        bid_mark: float | None = None
        ask_mark: float | None = None
        bid_refreshed = bid_total = 0
        ask_refreshed = ask_total = 0
        for tts, _price, _size, tside, _delta, _eb, _ea in self._trades:
            while qi < n and quotes[qi][0] <= tts:
                cur_bid = quotes[qi][1]
                cur_ask = quotes[qi][2]
                qi += 1
            if tside is Side.SELL and cur_bid is not None:
                bid_total += 1
                if bid_mark is None or cur_bid >= bid_mark:
                    bid_refreshed += 1
                bid_mark = cur_bid if bid_mark is None else max(bid_mark, cur_bid)
            elif tside is Side.BUY and cur_ask is not None:
                ask_total += 1
                if ask_mark is None or cur_ask <= ask_mark:
                    ask_refreshed += 1
                ask_mark = cur_ask if ask_mark is None else min(ask_mark, cur_ask)
        bid_refresh = (bid_refreshed / bid_total) if bid_total else 0.0
        ask_refresh = (ask_refreshed / ask_total) if ask_total else 0.0
        return bid_refresh, ask_refresh

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

    def add_trade(
        self,
        ts: float,
        price: float,
        size: int,
        side: Side,
        eff_bid: float | None = None,
        eff_ask: float | None = None,
    ) -> None:
        for window in self._windows.values():
            window.add_trade(ts, price, size, side, eff_bid, eff_ask)

    def add_quote(self, ts: float, bid: float, ask: float, spread: float) -> None:
        for window in self._windows.values():
            window.add_quote(ts, bid, ask, spread)

    def compute(self, now_ts: float) -> dict[str, dict[str, float]]:
        """Feature values for every window, keyed by window label (e.g. ``"30s"``)."""
        return {
            self._config.window_label(length): window.compute(now_ts)
            for length, window in self._windows.items()
        }
