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
from .market_state import MarketState
from .observations import ObservationEmitter
from .snapshot import EngineSnapshot, TradeRow


class TapeEngine:
    def __init__(self, ticker: str, scenario: str, config: Config) -> None:
        self._ticker = ticker
        self._scenario = scenario
        self._config = config

        self._market = MarketState()
        self._features = FeatureEngine(config)
        self._classifier = TapeStateClassifier(config)
        self._emitter = ObservationEmitter()

        self._trade_count = 0
        self._last_ts = 0.0
        self._recent_trades: deque[TradeRow] = deque(maxlen=config.recent_trades_limit)
        self._event_log: deque[str] = deque(maxlen=config.event_log_limit)
        self._stream_status = "connecting"
        self._snapshot = self._build_snapshot()

    @property
    def scenario(self) -> str:
        return self._scenario

    def set_stream_status(self, status: str) -> None:
        self._stream_status = status
        self._snapshot = self._build_snapshot()

    def process_event(self, event: Event) -> EngineSnapshot:
        if isinstance(event, QuoteEvent):
            self._market.update_quote(event)
            self._features.add_quote(event.timestamp, event.ask - event.bid)
        elif isinstance(event, TradeEvent):
            # The quote already in MarketState is the one in effect at this trade's ts,
            # because events arrive in logical-timestamp order (quote before trade).
            side = classify_aggressor(event, self._market.quote)
            self._market.update_trade(event)
            self._features.add_trade(event.timestamp, event.price, event.size, side)
            self._trade_count += 1
            self._recent_trades.appendleft(
                TradeRow(event.timestamp, event.price, event.size, side.value)
            )

        self._last_ts = event.timestamp
        if self._stream_status == "connecting":
            self._stream_status = "live"
        self._snapshot = self._build_snapshot()
        return self._snapshot

    def snapshot(self) -> EngineSnapshot:
        return self._snapshot

    def _build_snapshot(self) -> EngineSnapshot:
        features = self._features.compute(self._last_ts)
        classification = self._classifier.classify(
            features[self._config.primary_window_label], self._trade_count
        )
        for message in self._emitter.on_tick(classification.state):
            self._event_log.append(message)

        return EngineSnapshot(
            ticker=self._ticker,
            scenario=self._scenario,
            timestamp=self._last_ts,
            event_count=self._trade_count,
            warm=self._trade_count >= self._config.warmup_min_events,
            stream_status=self._stream_status,
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
