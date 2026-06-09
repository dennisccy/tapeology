"""Per-ticker engine: wires provider events -> market state -> features -> classifier
-> single immutable snapshot.

Processing is a pure function of the ordered event stream: each event updates market state,
re-derives features, re-classifies, appends any transition message, and rebuilds the one
snapshot. No wall-clock and no randomness enter here, so the same stream yields the same
snapshots (determinism anti-goal). The engine depends only on the provider interface and
config — never on a concrete provider.
"""

from __future__ import annotations

from collections import deque

from ..config import Config
from ..providers.base import Event, QuoteEvent, Side, TradeEvent
from .aggressor import classify_aggressor
from .classifier import TapeStateClassifier
from .features import FeatureEngine
from .history import HistoryBuffer
from .market_state import MarketState
from .observations import ObservationEmitter
from .snapshot import EngineSnapshot, TradeRow


class TapeEngine:
    def __init__(
        self,
        ticker: str,
        scenario: str,
        config: Config,
        epoch_anchor: float | None = None,
    ) -> None:
        self._ticker = ticker
        self._scenario = scenario
        self._config = config
        # Canonical display/epoch anchor (Data Contract row 13, J-31): the real UTC epoch that
        # logical-time 0 maps to, preserved ONCE here from the provider (historical = first real
        # record epoch; simulated = config synthetic session-start; live = None). It is additive
        # DISPLAY metadata — it never enters market state / features / classification, so the
        # engine stays deterministic. Defaulted None so every pre-J-31 construction is unchanged.
        self._epoch_anchor = epoch_anchor

        self._market = MarketState()
        self._features = FeatureEngine(config)
        self._classifier = TapeStateClassifier(config)
        self._emitter = ObservationEmitter()
        # Price-history buffer (OHLC candles + tape-state markers). Accrued ONLY from
        # process_event (per real events), never from a status flip or construction — so a
        # set_stream_status call cannot mutate the chart series. Computed once, read-only.
        self._history = HistoryBuffer(config)

        self._trade_count = 0
        self._last_ts = 0.0
        # Carried state for the aggressor tick-test fallback: the last NON-ZERO tick direction
        # (uptick=BUY / downtick=SELL between consecutive trades). Seeded empty so a fresh watch
        # (or a re-watch after Stop) starts with no direction to carry — the very first zero-tick-
        # before-any-direction print is then honestly UNKNOWN (determinism anti-goal).
        self._last_tick_dir: Side | None = None
        self._recent_trades: deque[TradeRow] = deque(maxlen=config.recent_trades_limit)
        self._event_log: deque[str] = deque(maxlen=config.event_log_limit)
        self._stream_status = "connecting"
        # Honest-pause state (Data Contract row 11), owned ONCE here. `_paused` is the canonical
        # flag; `_pre_pause_status` remembers the stream_status in effect at pause time so resume
        # restores it verbatim (live/connecting/stale) and NEVER fabricates "live".
        self._paused = False
        self._pre_pause_status: str | None = None
        self._snapshot = self._build_snapshot()

    @property
    def scenario(self) -> str:
        return self._scenario

    @property
    def epoch_anchor(self) -> float | None:
        """The canonical display/epoch anchor (row 13). Read by the history projection so the
        chart can map a logical bin time to a true clock instant; never recomputed downstream."""
        return self._epoch_anchor

    def set_stream_status(self, status: str) -> None:
        """Set the canonical row-6 ``stream_status`` (delivery/lifecycle metadata, owned ONCE here).

        Valid values: ``connecting`` | ``waiting`` | ``live`` | ``stale`` | ``paused`` | ``closed``
        | ``failed``. The feeder writes ``waiting`` (stream open, no first event yet), ``stale`` (a
        delivery-gap lull), ``closed`` (clean stop/exhaustion), and ``failed`` (the feeder raised);
        ``connecting``->/``waiting``->``live`` is promoted in ``process_event`` and ``paused`` by
        ``pause()``. This is NOT part of classification — it never enters ``classify(...)`` or any
        feature/score, so the same ordered event stream still yields identical features/state/
        confidence (determinism anti-goal).
        """
        self._stream_status = status
        self._snapshot = self._build_snapshot()

    @property
    def paused(self) -> bool:
        return self._paused

    def pause(self) -> None:
        """Freeze the read: set the canonical paused flag and flip the status to "paused".

        Idempotent — a second pause is a no-op (it does NOT re-capture the already-"paused" status,
        which would make resume restore "paused" instead of the real pre-pause status). The
        pre-pause status is remembered so resume restores it verbatim (honest pause: never a
        fabricated "live"). This only flips the canonical flag/status; the feeder (WatchManager)
        is what stops *applying* events while paused. The engine itself also refuses to advance in
        process_event while paused, so a stray event cannot leak in.
        """
        if self._paused:
            return
        self._pre_pause_status = self._stream_status
        self._paused = True
        self._stream_status = "paused"
        self._snapshot = self._build_snapshot()

    def resume(self) -> None:
        """Continue: clear the paused flag and restore the exact pre-pause status.

        Idempotent — resume-when-not-paused is a quiet no-op. Restores the remembered pre-pause
        status (live / connecting / stale) so a paused-then-resumed live feed rejoins at its prior
        honest status; it NEVER manufactures "live". No catch-up is synthesized — feeding simply
        continues (the feeder resumes applying the next real events).
        """
        if not self._paused:
            return
        self._paused = False
        self._stream_status = self._pre_pause_status or "connecting"
        self._pre_pause_status = None
        self._snapshot = self._build_snapshot()

    def process_event(self, event: Event) -> EngineSnapshot:
        # Honest pause: while paused the engine applies NOTHING (no trades, no quotes, no ts
        # advance) and fabricates no backfill — it returns the frozen snapshot as-is. The feeder
        # already stops calling this while paused; this guard is the engine-level backstop so a
        # stray event from any path cannot advance a paused engine (no fabricated catch-up).
        if self._paused:
            return self._snapshot
        if isinstance(event, QuoteEvent):
            self._market.update_quote(event)
            self._features.add_quote(
                event.timestamp, self._market.bid, self._market.ask, self._market.spread
            )
        elif isinstance(event, TradeEvent):
            # The quote already in MarketState is the one in effect at this trade's ts, and
            # MarketState.last is still the PRIOR trade price — both because events arrive in
            # logical-timestamp order (quote before trade) and we classify BEFORE recording this
            # trade. This ordering is load-bearing for the tick-test fallback; do not reorder.
            prior_trade_price = self._market.last
            side = classify_aggressor(
                event, self._market.quote, prior_trade_price, self._last_tick_dir
            )
            # Update the carried last non-zero tick direction from this trade's price move
            # (a pure function of the consecutive trade prices, independent of how `side` was
            # decided), so a later zero-tick can carry it.
            if prior_trade_price is not None:
                if event.price > prior_trade_price:
                    self._last_tick_dir = Side.BUY
                elif event.price < prior_trade_price:
                    self._last_tick_dir = Side.SELL
            # The in-effect quote at THIS trade's instant is the bid/ask already in MarketState (a
            # quote at the same/earlier logical ts was applied before this trade — the load-bearing
            # ordering preserved above). Capture it BEFORE `update_trade` (which only touches `last`,
            # not the quote) and hand it to the FeatureEngine so the refresh scores can be maintained
            # incrementally (J-37 perf) — it is the SAME in-effect quote the forward-merge would find,
            # so the value is unchanged; only dense-window speed improves.
            eff_bid = self._market.bid
            eff_ask = self._market.ask
            self._market.update_trade(event)
            # Single source of truth: this one `side` value feeds BOTH the displayed recent-trades
            # row and the FeatureEngine (aggressive ratios / net aggressive volume) — never
            # recomputed downstream.
            self._features.add_trade(
                event.timestamp, event.price, event.size, side, eff_bid, eff_ask
            )
            self._trade_count += 1
            self._recent_trades.appendleft(
                TradeRow(event.timestamp, event.price, event.size, side.value)
            )
            # Bin this trade's price into the OHLC candles (same price the snapshot exposes as
            # `last`; quotes do not create candles). Logical-ts bucketing — no wall-clock.
            self._history.add_trade(event.timestamp, event.price)

        self._last_ts = event.timestamp
        # First-event promotion to the post-connect `live` rung. The status climbs
        # connecting (pre-open / cold construction) -> waiting (stream open, no event yet, set by
        # the feeder) -> live (first event arrived). Both pre-live rungs promote here so a stream
        # that signalled open (status `waiting`) also goes `live` on its first event. `stale` ->
        # `live` recovery and `paused`/`closed`/`failed` are owned by the feeder, not flipped here.
        if self._stream_status in ("connecting", "waiting"):
            self._stream_status = "live"
        self._snapshot = self._build_snapshot()
        # Append a tape-state-transition MARKER if this tick's classified state changed to a
        # meaningful state — reusing the snapshot's OWN tape_state/confidence (single source of
        # truth; no second classification). Done here in process_event (not in _build_snapshot)
        # so a set_stream_status rebuild never appends a spurious marker.
        self._history.note_state(
            self._snapshot.timestamp, self._snapshot.tape_state, self._snapshot.confidence
        )
        return self._snapshot

    def snapshot(self) -> EngineSnapshot:
        return self._snapshot

    @property
    def history(self) -> HistoryBuffer:
        """Read-only access to the price-history buffer (OHLC candles + markers).

        The `…/history` serializer reads this; it is computed once here and never recomputed.
        """
        return self._history

    def _build_snapshot(self) -> EngineSnapshot:
        features = self._features.compute(self._last_ts)
        primary = features[self._config.primary_window_label]
        classification = self._classifier.classify(primary, self._trade_count)
        # The emitter owns the appended event log; it needs the held bid/ask and large-print
        # evidence to phrase the absorption message from real values (single source, here).
        for message in self._emitter.on_tick(
            classification.state,
            bid=self._market.bid,
            ask=self._market.ask,
            large_print_count=primary["large_print_count"],
        ):
            self._event_log.append(message)

        return EngineSnapshot(
            ticker=self._ticker,
            scenario=self._scenario,
            timestamp=self._last_ts,
            event_count=self._trade_count,
            warm=self._trade_count >= self._config.warmup_min_events,
            stream_status=self._stream_status,
            paused=self._paused,
            epoch_anchor=self._epoch_anchor,
            bid=self._market.bid,
            ask=self._market.ask,
            spread=self._market.spread,
            last=self._market.last,
            features=features,
            primary_window=self._config.primary_window_label,
            tape_state=classification.state,
            confidence=classification.confidence,
            observations=classification.observations,
            recent_trades=tuple(self._recent_trades),
            event_log=tuple(self._event_log),
        )
