"""Per-ticker engine: wires provider events -> market state -> features -> classifier
-> single immutable snapshot.

Processing is a pure function of the ordered event stream: each event updates market state,
re-derives features, re-classifies, appends any transition message, and rebuilds the one
snapshot. No wall-clock and no randomness enter here, so the same stream yields the same
snapshots (determinism anti-goal). The engine depends only on the provider interface and
config — never on a concrete provider.
"""

from __future__ import annotations

import logging
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

# Server-side logger for the observer seam. An observer callback that RAISES must be logged here
# (a real, inspectable line) and never swallowed silently — the no-mute / no-silent-failure
# discipline. The engine itself stays research-agnostic: an observer is an opaque object, never a
# research type, so logging a failure leaks no research concept into the engine.
logger = logging.getLogger(__name__)


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
        # record epoch; simulated = config synthetic session-start; live = None at construction,
        # stamped once by the feeder at the first record via ``set_epoch_anchor``). It is additive
        # DISPLAY metadata — it never enters market state / features / classification, so the
        # engine stays deterministic. Defaulted None so every pre-J-31 construction is unchanged.
        self._epoch_anchor = epoch_anchor

        self._market = MarketState()
        self._features = FeatureEngine(config)
        self._classifier = TapeStateClassifier(config)
        self._emitter = ObservationEmitter()
        # Price-history buffer (OHLC candles + tape-state markers). Accrued ONLY from
        # process_event (per real events), never from a status flip or construction — so a
        # set_stream_status call cannot mutate the chart series. Computed once, read-only. The
        # anchor is threaded in so its wall-clock timeframe candles align on the real-epoch grid.
        self._history = HistoryBuffer(config, epoch_anchor=epoch_anchor)

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
        # The reason behind the MOST RECENT terminal status flip (capability 24, J-47). The status
        # string alone cannot tell a user Stop ("watch_stopped") apart from a stream that ran out
        # ("stream_closed") — both flip stream_status to "closed" — so the WatchManager stamps the
        # distinguishing reason here at the flip, and the research monitor reads it (via ``end_reason``)
        # in its on_status hook. Display/lifecycle metadata only — NEVER part of classification, so the
        # same ordered event stream still yields identical features/state/confidence (determinism).
        # ``None`` until a terminal flip carries a reason.
        self._end_reason: str | None = None
        # Honest-pause state (Data Contract row 11), owned ONCE here. `_paused` is the canonical
        # flag; `_pre_pause_status` remembers the stream_status in effect at pause time so resume
        # restores it verbatim (live/connecting/stale) and NEVER fabricates "live".
        self._paused = False
        self._pre_pause_status: str | None = None

        # Canonical feeder-owned DELIVERY LAG (Data Contract row 14, J-63): how far the processed tape
        # trails real time in seconds (LIVE = latest record epoch vs wall clock; PACED replay = the
        # feeder's processing backlog vs its own pacing schedule). The WatchManager (the feeder) STAMPS
        # it via ``set_delivery_lag``; the engine only carries it onto the snapshot as additive
        # display/lifecycle metadata (the iter-9 ``end_reason`` precedent). It is NEVER read by
        # classification — the same ordered event stream yields byte-identical features/state/confidence
        # with or without it (determinism + observer-equivalence anti-goals). ``None`` until the feeder
        # stamps one (an honest "no lag measured", distinct from a measured 0.0).
        self._delivery_lag_seconds: float | None = None

        # --- Research seam (capability 20): the generic snapshot-observer list ----------------
        # The ONLY sanctioned attachment point for the research evolution. Each registered observer
        # is an OPAQUE object exposing optional ``on_event(event, snapshot)`` (invoked at the END of
        # every ``process_event``, after the snapshot is rebuilt) and ``on_status(status)`` (invoked
        # on EVERY stream-status change — status flips do not pass through events, so this hook is
        # what the future research monitor will need for stale/closed/failed). The engine stays
        # research-agnostic: it imports/holds no research type and calls only these two opaque
        # callbacks. Notification is EXCEPTION-ISOLATED — a raising observer is logged and marked
        # failed (a per-observer state a future research monitor reads to surface
        # ``monitor_status: failed``) and event processing/feeding continues UNCHANGED, so engine
        # outputs stay byte-identical with or without an attached (even throwing) observer (J-68).
        # Nothing attaches an observer in production code this iteration — only tests do.
        self._observers: list[object] = []
        self._observer_failed: dict[int, bool] = {}

        self._snapshot = self._build_snapshot()

    @property
    def scenario(self) -> str:
        return self._scenario

    @property
    def epoch_anchor(self) -> float | None:
        """The canonical display/epoch anchor (row 13). Read by the history projection so the
        chart can map a logical bin time to a true clock instant; never recomputed downstream."""
        return self._epoch_anchor

    def add_observer(self, observer: object) -> object:
        """Register a snapshot observer on the research seam (capability 20); returns the handle.

        ``observer`` is an OPAQUE object that may expose ``on_event(event, snapshot)`` and/or
        ``on_status(status)`` — the engine calls only those two callbacks and knows nothing else
        about it (engine stays research-agnostic). The returned handle (the observer itself) is what
        ``observer_failed`` is later queried with. Registration does NOT rebuild the snapshot and
        does NOT fire any callback, so attaching an observer never perturbs engine output.
        """
        self._observers.append(observer)
        self._observer_failed[id(observer)] = False
        return observer

    def observer_failed(self, handle: object) -> bool:
        """Whether the observer behind ``handle`` has raised in any callback (per-observer state).

        Read by the FUTURE research monitor to surface ``monitor_status: failed`` (no research
        projection is built this iteration — only this engine-side flag exists). Defaults ``False``
        for an unknown handle (never raises — a query is side-effect-free)."""
        return self._observer_failed.get(id(handle), False)

    def _notify_event(self, event: Event, snapshot: EngineSnapshot) -> None:
        """Invoke ``on_event`` on every observer, EXCEPTION-ISOLATED (J-68 anti-goal).

        A raising observer is logged and marked failed; the loop continues so one bad observer
        never starves the others, and — crucially — the exception never propagates back into
        ``process_event``, so the engine's outputs are unchanged whether an observer throws or not.
        """
        for observer in self._observers:
            callback = getattr(observer, "on_event", None)
            if callback is None:
                continue
            try:
                callback(event, snapshot)
            except Exception:
                self._observer_failed[id(observer)] = True
                logger.exception("snapshot observer on_event failed for %s", self._ticker)

    def _notify_status(self, status: str) -> None:
        """Invoke ``on_status`` on every observer, EXCEPTION-ISOLATED (mirrors ``_notify_event``).

        Fired from EVERY status writer (``set_stream_status``, ``pause``, ``resume``, and the
        internal connecting/waiting->live promotion) — status flips do not pass through events, so
        this is the only hook the future research monitor has for stale/closed/failed. A raising
        observer is logged + marked failed and the status write itself still succeeds.
        """
        for observer in self._observers:
            callback = getattr(observer, "on_status", None)
            if callback is None:
                continue
            try:
                callback(status)
            except Exception:
                self._observer_failed[id(observer)] = True
                logger.exception("snapshot observer on_status failed for %s", self._ticker)

    @property
    def end_reason(self) -> str | None:
        """The reason behind the most recent terminal status flip (``watch_stopped`` |
        ``stream_closed`` | feeder-failure reason), or ``None``.

        Read by the research monitor's ``on_status`` hook to distinguish a USER stop from a stream
        that ran out (both flip ``stream_status`` to ``closed``). Display/lifecycle metadata only —
        never part of classification."""
        return self._end_reason

    def set_stream_status(self, status: str, end_reason: str | None = None) -> None:
        """Set the canonical row-6 ``stream_status`` (delivery/lifecycle metadata, owned ONCE here).

        Valid values: ``connecting`` | ``waiting`` | ``live`` | ``stale`` | ``paused`` | ``closed``
        | ``failed``. The feeder writes ``waiting`` (stream open, no first event yet), ``stale`` (a
        delivery-gap lull), ``closed`` (clean stop/exhaustion), and ``failed`` (the feeder raised);
        ``connecting``->/``waiting``->``live`` is promoted in ``process_event`` and ``paused`` by
        ``pause()``. This is NOT part of classification — it never enters ``classify(...)`` or any
        feature/score, so the same ordered event stream still yields identical features/state/
        confidence (determinism anti-goal).

        ``end_reason`` (optional) records WHY a terminal flip happened — ``watch_stopped`` (user
        Stop) vs ``stream_closed`` (the stream ran out) vs a feeder-failure reason — so the research
        monitor can tell them apart in ``on_status`` (the status string alone cannot). It is stored
        BEFORE the observer notification so the monitor reads the current reason. Defaulted ``None``
        so every existing caller is unchanged (additive) and a non-terminal flip clears no prior
        reason it does not own — a terminal flip always passes its own reason.
        """
        self._stream_status = status
        if end_reason is not None:
            self._end_reason = end_reason
        self._snapshot = self._build_snapshot()
        # Notify AFTER the write + snapshot rebuild so an observer reading the engine sees the new
        # status (and the just-stamped end_reason). Exception-isolated; the write above has already
        # taken effect regardless.
        self._notify_status(status)

    def set_delivery_lag(self, seconds: float | None) -> None:
        """Stamp the feeder-owned ``delivery_lag_seconds`` (Data Contract row 14, J-63).

        Called ONLY by the WatchManager (the feeder), which owns the per-mode lag semantics (LIVE =
        latest record epoch vs wall clock; PACED replay = processing backlog vs the pacing schedule).
        The engine merely carries the value onto the next-built snapshot as additive display/lifecycle
        metadata — it is NEVER fed into ``classify(...)`` or any feature/score, so the same ordered
        event stream still yields identical features/state/confidence (determinism + observer-
        equivalence anti-goals). Rebuilds the snapshot so the new lag is reflected immediately (the
        feeder may stamp it between events). A non-negative float or ``None`` (no lag measured)."""
        self._delivery_lag_seconds = seconds
        self._snapshot = self._build_snapshot()

    def set_epoch_anchor(self, anchor: float) -> None:
        """Stamp the canonical display/epoch anchor (Data Contract row 13, J-31) ONCE, feeder-owned.

        Called by the WatchManager for a LIVE watch, whose real epoch is only known once the first
        record arrives (sim/historical/progressive learn it at construction). Set-once — a second
        call is a no-op, so the anchor never changes mid-watch. Threads through to the history
        buffer so its wall-clock timeframe candles start binning on the real-epoch grid from the
        first trade onward. Additive DISPLAY metadata only — it never enters ``classify(...)`` or
        any feature/score, so the same ordered event stream still yields identical features/state/
        confidence (determinism + observer-equivalence anti-goals). Rebuilds the snapshot so the
        newly-known anchor is reflected immediately (the feeder stamps it before the first event)."""
        if self._epoch_anchor is not None:
            return
        self._epoch_anchor = anchor
        self._history.set_epoch_anchor(anchor)
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
        self._notify_status("paused")  # status flip => observer hook (exception-isolated)

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
        self._notify_status(self._stream_status)  # restored status => observer hook (isolated)

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
            # `last`; quotes do not create candles). Logical-ts bucketing for the per-bar-size
            # series; the size feeds the additive wall-clock timeframe candles' volume (both
            # display-only — neither enters classification).
            self._history.add_trade(event.timestamp, event.price, event.size)

        self._last_ts = event.timestamp
        # First-event promotion to the post-connect `live` rung. The status climbs
        # connecting (pre-open / cold construction) -> waiting (stream open, no event yet, set by
        # the feeder) -> live (first event arrived). Both pre-live rungs promote here so a stream
        # that signalled open (status `waiting`) also goes `live` on its first event. `stale` ->
        # `live` recovery and `paused`/`closed`/`failed` are owned by the feeder, not flipped here.
        promoted_to_live = False
        if self._stream_status in ("connecting", "waiting"):
            self._stream_status = "live"
            promoted_to_live = True
        self._snapshot = self._build_snapshot()
        # Append a tape-state-transition MARKER if this tick's classified state changed to a
        # meaningful state — reusing the snapshot's OWN tape_state/confidence (single source of
        # truth; no second classification). Done here in process_event (not in _build_snapshot)
        # so a set_stream_status rebuild never appends a spurious marker.
        self._history.note_state(
            self._snapshot.timestamp, self._snapshot.tape_state, self._snapshot.confidence
        )
        # Research-seam notifications (exception-isolated; capability 20). The internal
        # connecting/waiting->live promotion is a status flip that does NOT go through on_event, so
        # it must fire on_status too (the future research monitor needs it). Both notifications run
        # AFTER the snapshot/history are finalised so an observer reads the complete tick, and both
        # are isolated so a throwing observer cannot perturb the value returned here (J-68).
        if promoted_to_live:
            self._notify_status("live")
        self._notify_event(event, self._snapshot)
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
            delivery_lag_seconds=self._delivery_lag_seconds,
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
