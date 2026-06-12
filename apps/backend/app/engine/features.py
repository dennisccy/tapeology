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


class _RefreshSide:
    """Amortised-O(1) weak-record fraction over the COUNTED prints currently in the window — one
    side of the refresh score (capability-34 engine-performance gate).

    This reproduces — BYTE-IDENTICALLY — what the forward-merge oracle (``_Window._refresh_fractions``)
    computes for one side, but maintained incrementally so a dense/long replay is NOT quadratic.

    THE ORACLE QUANTITY (bid side; ask is the mirror with min / ``<=``):
      Over the in-window aggressive-SELL prints that HAVE an in-effect bid, in ARRIVAL order, count
      those whose in-effect bid is at a NEW WEAK HIGH — ``bid >= running_max_of_all_prior`` (ties
      count). ``fraction = refreshed / total`` (``0.0`` when ``total == 0``). This is the count of
      *weak prefix-maxima* (records) over the value sequence — an order-dependent prefix quantity.

    WHY THE INCREMENTAL MAINTENANCE IS CORRECT *and* CHEAP:
      ``append(v)`` — a new tail print: it is a record iff ``v`` is a new weak record vs the running
        watermark (the window-wide best, held in the monotonic ``_best`` deque). O(1).
      ``evict_front()`` — the oldest counted print leaves: removing a LEFT prefix can only LOWER the
        prefix-max seen by later prints, so a print's record status can only flip not→yes, never
        back. When the evicted print WAS a record (records are monotone, so the front record is the
        smallest), we PROMOTE the newly-exposed records in the gap up to the next still-standing
        record, then STOP (that record dominates the exposed prefix). Each print is promoted AT MOST
        ONCE over its lifetime, so the total promotion work across the whole stream is linear →
        amortised O(1) per event.
      The watermark a future ``append`` compares against (the window-wide best) lives in the
      monotonic ``_best`` deque (the classic sliding-window-extremum deque), front-evicted O(1).

    Pinned byte-identical to ``_refresh_fractions`` by ``test_refresh_increment.py`` (a randomised
    differential test of millions of append/evict op sequences) AND over the real SIP dense fixture
    + a seeded sim scenario (``test_dense_replay_gate.py`` / ``test_features.py``).
    """

    __slots__ = ("_high", "_vals", "_rec", "_best", "refreshed", "total")

    def __init__(self, high: bool) -> None:
        self._high = high          # True => bid (weak HIGH record); False => ask (weak LOW record)
        self._vals: deque[float] = deque()   # in-effect quote value per counted print, arrival order
        self._rec: deque[bool] = deque()     # is this print a weak record under the current front?
        self._best: deque[float] = deque()   # monotonic window-wide best (max for high / min for low)
        self.refreshed = 0
        self.total = 0

    def _better_eq(self, a: float, b: float) -> bool:
        return a >= b if self._high else a <= b

    def reset(self) -> None:
        self._vals.clear()
        self._rec.clear()
        self._best.clear()
        self.refreshed = 0
        self.total = 0

    def append(self, value: float) -> None:
        watermark = self._best[0] if self._best else None
        is_rec = watermark is None or self._better_eq(value, watermark)
        self._vals.append(value)
        self._rec.append(is_rec)
        self.total += 1
        if is_rec:
            self.refreshed += 1
        # Maintain the monotonic best deque: drop trailing entries no better than this value so the
        # front always holds the window-wide best (the watermark a future append compares against).
        while self._best and not self._better_eq(self._best[-1], value):
            self._best.pop()
        self._best.append(value)

    def evict_front(self) -> None:
        v0 = self._vals.popleft()
        was_rec = self._rec.popleft()
        self.total -= 1
        if was_rec:
            self.refreshed -= 1
            # Promote newly-exposed records in the gap up to the next still-standing record, then
            # stop (that record dominates the exposed prefix). Each promotion flips a print once.
            mark: float | None = None
            n = len(self._rec)
            i = 0
            while i < n:
                if self._rec[i]:
                    break
                v = self._vals[i]
                if mark is None or self._better_eq(v, mark):
                    self._rec[i] = True
                    self.refreshed += 1
                    mark = v
                i += 1
        # Front-evict the monotonic best deque if its front WAS this evicted value (one per value).
        if self._best and self._best[0] == v0:
            self._best.popleft()

    def fraction(self) -> float:
        return (self.refreshed / self.total) if self.total else 0.0


class _Window:
    """One rolling window of a fixed logical length (seconds).

    PERFORMANCE (J-37 + capability-34 engine-performance gate): a dense Full-RTH window carries tens
    of thousands of prints, and a naive per-tick rescan of the window is O(n²) — which made a real
    GME open-drop window take minutes. Every aggregate is therefore maintained INCREMENTALLY: running
    sums updated on append and on eviction, and — the capability-34 fix — the order-dependent refresh
    scores maintained by per-side ``_RefreshSide`` structures that are NOT rebuilt per event. The
    values produced are BYTE-IDENTICAL to the prior full-rescan implementation (determinism +
    single-source-of-truth preserved — asserted by the existing feature tests, a
    progressive-vs-single-shot determinism test, AND a dedicated oracle-equivalence test that
    compares the incremental refresh scores against ``_refresh_fractions`` at every compute), only
    computed without the quadratic rescan.

    REFRESH-SCORE MAINTENANCE — the capability-34 change in detail:
      BEFORE: the incremental refresh counts were valid only on an APPEND-ONLY window; the FIRST
      trade- or quote-eviction set ``self._refresh_incremental = False`` PERMANENTLY, after which
      EVERY ``compute()`` served the refresh scores from ``_refresh_fractions()`` — a full
      forward-merge over the whole window, i.e. an O(window) rescan PER EVENT (quadratic on any
      stream longer than a feature window — the documented defect this iteration closes).
      NOW: the refresh scores are maintained incrementally ACROSS evictions:
        * a tail append folds the new print onto the ``_RefreshSide`` trackers in amortised O(1);
        * a FRONT trade eviction pops the matching tracker fronts in amortised O(1);
        * the only correctness-critical branch is QUOTE re-mapping — when a quote eviction removes the
          in-effect quote an already-folded FRONT trade depended on, that trade's in-effect quote
          re-maps (to the next surviving quote ≤ its ts, or to NONE — the oracle's "in-window quotes
          only" quirk), so the trackers are rebuilt once from the surviving window. This is the only
          path that re-walks the window, it fires ONLY on such a remap (never per event on dense
          data), and is pinned by the structural no-rescan test (``_refresh_oracle_calls == 0`` on the
          engine path; ``_refresh_rebuilds`` bounded).
      ``_refresh_fractions()`` is RETAINED as (a) the authoritative path for the standalone
      ``FeatureEngine`` API (which threads no in-effect quotes — behaviour unchanged) and (b) the
      test ORACLE the incremental path is pinned byte-identical against.

    The in-effect quote (bid/ask) at each trade's instant is supplied by the engine at ``add_trade``
    time (it already holds it in ``MarketState``); the engine's quote-before-trade ordering means the
    forward two-pointer over the quote deque reproduces it exactly, so the threaded value is used
    only to flag that the engine path is in use.
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

        # --- Incremental refresh-score maintenance (capability-34 engine-performance gate) --------
        # ``_refresh_has_eff`` becomes True once ANY trade carried an in-effect quote (the ENGINE
        # path). The standalone FeatureEngine API never threads one, so it stays False and ``compute``
        # uses the authoritative forward-merge ``_refresh_fractions`` — keeping that API
        # byte-identical while the engine path gets the incremental maintenance.
        self._refresh_has_eff = False
        self._refresh_bid = _RefreshSide(high=True)    # SELL prints vs in-effect bid (weak HIGH)
        self._refresh_ask = _RefreshSide(high=False)   # BUY prints vs in-effect ask (weak LOW)
        # The forward two-pointer cursor over the quote deque (relative index into the CURRENT deque)
        # and the running in-effect bid/ask it produces, with the ABSOLUTE index of that in-effect
        # quote so a quote eviction can be detected. The cursor only ever advances forward.
        self._refresh_qi = 0
        self._refresh_cur_bid: float | None = None
        self._refresh_cur_ask: float | None = None
        self._refresh_cur_qabs = -1
        # Number of in-window trades already folded into the trackers (the fold cursor over trades).
        self._refresh_folded = 0
        # How many quotes have been popped from the FRONT over the window's whole life, so an
        # absolute quote index survives front eviction of the quote deque.
        self._quotes_evicted = 0
        # Per folded trade, in arrival order: ``(which, src_qabs)`` where ``which`` is 0 (contributed
        # to NEITHER tracker — no in-effect quote / non-directional), 1 (bid tracker), or 2 (ask
        # tracker); ``src_qabs`` is the ABSOLUTE index of its in-effect quote (-1 if none). Lets a
        # front trade eviction pop the right tracker, and a quote eviction detect a remap.
        self._refresh_fifo: deque[tuple[int, int]] = deque()

        # --- Instrumentation for the structural no-rescan test ------------------------------------
        # ``_refresh_oracle_calls`` counts ``_refresh_fractions`` invocations (the merge fallback) —
        # the structural test asserts this is ZERO on the engine path after evictions begin.
        # ``_refresh_rebuilds`` counts the bounded quote-remap rebuilds (the only window re-walk on
        # the engine path) — the structural test asserts there is NO per-event full rescan (this is
        # bounded by remap events, not by event count).
        self._refresh_oracle_calls = 0
        self._refresh_rebuilds = 0

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

        if eff_bid is not None or eff_ask is not None:
            self._refresh_has_eff = True  # the engine threaded an in-effect quote: use the cursor

    def add_quote(self, ts: float, bid: float, ask: float, spread: float) -> None:
        self._quotes.append((ts, bid, ask, spread))
        self._spread_sum += spread
        self._mid_sum += (bid + ask) / 2.0
        # A new quote can only become the in-effect quote for FUTURE trades (the engine's
        # quote-before-trade ordering means a quote with ``qts <= a trade ts`` is always appended
        # before that trade). The fold cursor advances onto it lazily when those trades are folded.

    # --- Incremental refresh-score helpers (engine path) ------------------------------------------

    def _refresh_in_effect(self, trade_ts: float) -> None:
        """Advance the fold cursor's two-pointer to the last SURVIVING quote with ``qts <= trade_ts``
        (the oracle's in-effect-quote rule), updating the running in-effect bid/ask. Amortised O(1):
        the cursor only moves forward over the stream."""
        # If the in-effect quote has evicted it is no longer the surviving in-effect quote; reset so
        # a trade with no surviving preceding quote correctly gets None (the oracle's skip quirk).
        if self._refresh_cur_qabs < self._quotes_evicted:
            self._refresh_cur_bid = None
            self._refresh_cur_ask = None
            self._refresh_cur_qabs = -1
        quotes = self._quotes
        n = len(quotes)
        qi = self._refresh_qi
        while qi < n and quotes[qi][0] <= trade_ts:
            self._refresh_cur_bid = quotes[qi][1]
            self._refresh_cur_ask = quotes[qi][2]
            self._refresh_cur_qabs = self._quotes_evicted + qi
            qi += 1
        self._refresh_qi = qi

    def _refresh_fold_one(self, trade_ts: float, side: Side) -> None:
        """Fold one trade into the bid/ask trackers using the cursor's current in-effect quote —
        byte-identical to one iteration of ``_refresh_fractions`` (a SELL with no in-effect bid, or a
        BUY with no in-effect ask, contributes NOTHING — the oracle's skip-when-no-quote quirk)."""
        self._refresh_in_effect(trade_ts)
        if side is Side.SELL and self._refresh_cur_bid is not None:
            self._refresh_bid.append(self._refresh_cur_bid)
            self._refresh_fifo.append((1, self._refresh_cur_qabs))
        elif side is Side.BUY and self._refresh_cur_ask is not None:
            self._refresh_ask.append(self._refresh_cur_ask)
            self._refresh_fifo.append((2, self._refresh_cur_qabs))
        else:
            self._refresh_fifo.append((0, -1))

    def _refresh_rebuild(self) -> None:
        """Full rebuild of the trackers from the current in-window contents — used ONLY when a quote
        eviction re-mapped an already-folded FRONT trade's in-effect quote (the case the cheap
        incremental path cannot reconcile). Identical in result to ``_refresh_fractions`` over the
        surviving window, but folded into the trackers so subsequent appends stay O(1). The
        structural no-rescan test pins that this does NOT run per event on the dense fixture."""
        self._refresh_rebuilds += 1
        self._refresh_bid.reset()
        self._refresh_ask.reset()
        self._refresh_fifo.clear()
        self._refresh_qi = 0
        self._refresh_cur_bid = None
        self._refresh_cur_ask = None
        self._refresh_cur_qabs = -1
        for tts, _price, _size, tside, _delta, _eb, _ea in self._trades:
            self._refresh_fold_one(tts, tside)
        self._refresh_folded = len(self._trades)

    def _evict(self, now_ts: float) -> int:
        """Evict trades/quotes older than the window, updating every running aggregate AND the front
        of the refresh trackers. Returns the count of quotes evicted this call (so ``compute`` can
        decide whether a quote remap may have occurred)."""
        lo = now_ts - self.length
        trades_evicted = 0
        while self._trades and self._trades[0][0] < lo:
            _ts, price, size, side, _delta, _eb, _ea = self._trades.popleft()
            trades_evicted += 1
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
            # Pop the matching refresh-tracker front for this evicted trade (only if it was folded).
            if self._refresh_folded > 0 and self._refresh_fifo:
                which, _src = self._refresh_fifo.popleft()
                if which == 1:
                    self._refresh_bid.evict_front()
                elif which == 2:
                    self._refresh_ask.evict_front()
                self._refresh_folded -= 1
        quotes_evicted = 0
        while self._quotes and self._quotes[0][0] < lo:
            _ts, bid, ask, spread = self._quotes.popleft()
            self._spread_sum -= spread
            self._mid_sum -= (bid + ask) / 2.0
            self._quotes_evicted += 1
            quotes_evicted += 1
        # Keep the relative quote cursor pointing at the same absolute quote after a front pop.
        if quotes_evicted:
            self._refresh_qi = max(0, self._refresh_qi - quotes_evicted)
        return quotes_evicted

    def compute(self, now_ts: float) -> dict[str, float]:
        quotes_evicted = self._evict(now_ts)

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

        # bid_refresh / ask_refresh — see _RefreshSide. On the ENGINE path (in-effect quotes threaded)
        # maintain them incrementally; on the standalone API serve the authoritative forward-merge.
        # Both byte-identical (asserted by the oracle-equivalence tests).
        if self._refresh_has_eff:
            bid_refresh, ask_refresh = self._refresh_engine_path(quotes_evicted)
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

    def _refresh_engine_path(self, quotes_evicted: int) -> tuple[float, float]:
        """Reconcile the incremental trackers for this compute, then return the two fractions.

        ``_evict`` has already popped tracker fronts for the trades that left. Two cases remain:
          * A quote eviction this compute MAY have re-mapped an already-folded FRONT trade's in-effect
            quote (its source quote evicted). Because the source-quote indices are non-decreasing
            along the FIFO, only the FRONT contributor can be affected — if its source quote evicted
            (src < quotes_evicted) we rebuild ONCE (the surviving window re-walk). On dense data the
            front contributor's source quote is almost always still in window, so this rarely fires;
            it NEVER fires per-event-unconditionally (pinned by the structural no-rescan test).
          * Otherwise fold the tail trades appended since the last compute (amortised O(1)).
        """
        if quotes_evicted:
            # Find the FRONT contributing trade's source quote (skip the non-contributing 0-entries).
            # If its source quote has evicted, that trade re-maps → rebuild once.
            for which, src in self._refresh_fifo:
                if which == 0:
                    continue
                if src < self._quotes_evicted:
                    self._refresh_rebuild()
                    return self._refresh_bid.fraction(), self._refresh_ask.fraction()
                break  # the front contributor's source survives ⇒ no contributor re-maps
        # Fold the tail appended since the last compute.
        n = len(self._trades)
        while self._refresh_folded < n:
            tts, _p, _s, tside, _d, _eb, _ea = self._trades[self._refresh_folded]
            self._refresh_fold_one(tts, tside)
            self._refresh_folded += 1
        return self._refresh_bid.fraction(), self._refresh_ask.fraction()

    def _refresh_fractions(self) -> tuple[float, float]:
        """Compute (bid_refresh, ask_refresh) in one forward-merge pass over the window.

        For each trade the in-effect quote is the last quote with ``ts <= trade ts`` (a two-pointer
        forward merge over the ts-ordered series — identical to the prior per-side ``_refresh_fraction``
        merge, just shared across both sides so the window is walked once, not twice). bid_refresh is
        over aggressive-SELL prints with a running-MAX watermark (held = bid did not fall below its
        prior high); ask_refresh is over aggressive-BUY prints with a running-MIN watermark. A side
        with no matching print (or with no in-effect quote yet) scores 0.0 — no fabricated evidence.

        This remains the AUTHORITATIVE path for the standalone ``FeatureEngine`` API (no in-effect
        quotes threaded) and the TEST ORACLE the incremental path is pinned byte-identical against.
        """
        self._refresh_oracle_calls += 1
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
