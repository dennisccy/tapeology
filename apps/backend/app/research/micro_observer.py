"""``micro_observer.py`` -- Era "The Rapid Microscope" J-02: the streaming, prefix-honest observer

(``docs/rapid-validation-spec.md`` section 2.2) that turns ONE ordered replay pass into a
sequence of trade-anchored feature rows. Attached via the additive ``DatasetStore.replay(...,
observer=...)`` kwarg (section 2.1) onto the engine's EXISTING ``add_observer`` seam -- this
module reads the engine's per-tick snapshot, never a second replay, never a recomputed side.

**The prefix law, mechanically.** ``on_event`` is called once per event, in stored order, by the
engine's own ``_notify_event`` (``tape_engine.py``). Row *i* (this module appends one row per
TRADE event -- see "Granularity" below) is built and appended to ``self.rows`` synchronously
inside that call, using only: (a) accumulated state from events ``1..i`` this instance has already
seen, and (b) the engine snapshot handed to THIS call (itself a pure function of events ``1..i``).
Once a row is appended it is **NEVER mutated** -- a later event may only ever APPEND new rows or
attach a deferred completion (see below) to a row not yet appended; it can never reach back and
edit an already-flushed row. This is what makes truncation byte-identical to a prefix of the full
run (TR-1): rows ``1..k`` of a replay stopped after event ``k`` are, by construction, identical to
rows ``1..k`` of the full replay, because no later event can ever have touched them.

**Granularity: one row per TRADE, not one row per raw event.** The section 2.4 benchmark
(``micro_snapshots.py`` / ``scripts/micro_snapshot_granularity_benchmark.py``) measures this
choice against a per-raw-event and a fixed-stride-block alternative and records the comparison;
this module implements the winning representation. Quotes update this observer's OWN internal
state (it tracks its own bid/ask/bid_size/ask_size from the raw ``QuoteEvent`` -- the engine's
``FeatureEngine`` drops quote SIZES at ``add_quote``, so nowhere else carries them) but never
produce a row of their own; every research question this era asks is anchored at a trade or a
future structural touch (spec section 4), never at a bare quote tick.

**Reuse, never recompute (spec section 2.5).** The aggressor SIDE for a trade is read verbatim
from ``snapshot.recent_trades[0].side`` (the engine's own just-computed decision, freshly
``appendleft``-ed by ``process_event`` before ``on_event`` fires) -- this module never calls
``classify_aggressor`` itself. ``side_source`` (which of the classifier's two stages decided) is
NOT part of the engine's public surface at all, so it cannot be "read" from anywhere; this module
derives it by mirroring ``classify_aggressor``'s own DOCUMENTED stage-1 precondition (the identical
technique ``micro_readiness.py``'s ``_quote_rule_decides`` already uses and its own docstring
justifies at length) against quote/prior-trade state this observer tracks itself, in lockstep with
what the engine's ``MarketState``/``_last_tick_dir`` carry internally (mirrored, never read, since
the engine exposes neither) -- it is never a second implementation of the SIDE decision, only of
the (undisclosed) stage that decided it.

**Deferred constructs (spec section 0 / 2.2).** ``response_asymmetry`` (K subsequent trades),
``refill_consistent`` (M subsequent same-side quote updates) and ``quote_depletion`` (a same-price
quote run, up to its own update bound) cannot be known at their own anchor row. Each is tracked in
a small pending queue; the moment it resolves (or is proven ``unavailable`` at session end via
``finalize``) it is attached to the ``deferred`` list of whichever row is CURRENTLY being built
when the resolution happens -- never retroactively edited into the anchor's own already-flushed
row. ``response_asymmetry`` resolves exactly at the K-th subsequent trade's OWN row (a trade-count
horizon over a trade-anchored stream lines up exactly); ``refill_consistent``/``quote_depletion``
are quote-driven and may resolve between two trades, so they queue in ``self._pending_attachments``
until the next row is built (or ``finalize`` sweeps them into an honest closing summary if the
session ends first).

**The section 2.6 cross-basis unit gate, in the STREAMING path (TR-18).** ``quote_depletion``'s
value is a raw SHARE-denominated magnitude, which spec section 3 names CROSS-BASIS alongside the
execution-vs-replenishment ratio: it is refused unless this dataset's ``quote_size_unit`` is
verified. ``_resolve_depletion`` therefore passes ``mf.require_share_denominated_magnitude_allowed``
at the point of emission, and on refusal attaches ``value: None`` plus the closed-vocabulary
``refusal_reason`` (``mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT``) instead of the number -- every one
of the 18 legacy datasets is ``unverified``, so this is the LIVE path, not a corner case. The
refusal is DATA, not an exception, because the alternative -- letting the error escape mid-replay --
would refuse the unit-INVARIANT features (quote imbalance, microprice, everything in F-FLOW and
F-RESPONSE) along with it; the two extra keys ride only on the affected ``quote_depletion``
attachments, so consumers of the OTHER deferred kinds read an unchanged shape. ``refill_consistent``
needs no gate: it compares a displayed size to a displayed size in the SAME dataset, which is
unit-invariant at any ``quote_size_unit`` (spec section 2.6's own carve-out), and it serves a
boolean, never a magnitude. The row-level ``quote_size_unit`` stamp is the label itself, not
arithmetic over it."""

from __future__ import annotations

from collections import deque
from typing import Deque

from ..providers.base import Event, QuoteEvent, Side, TradeEvent
from . import micro_features as mf

__all__ = ["MicroObserver", "MicroObserverFailure"]


class MicroObserverFailure(Exception):
    """``MicroObserver.on_event`` raised while streaming a replay.

    The engine's ``_notify_event`` is exception-ISOLATED by design (``tape_engine.py``: a research
    observer must never perturb engine output, so a raise there is logged, flagged on the ENGINE,
    and swallowed). That is correct for the engine -- but it means a mid-stream observer failure is
    otherwise INVISIBLE to the snapshot builder, which would then persist a silently truncated row
    set and identity-verify it as a complete, valid snapshot. ``MicroObserver`` therefore records
    its own failure (``self.failure``) and stops consuming, and ``micro_snapshots.build_snapshot_
    rows`` raises this typed error rather than writing a partial snapshot -- fail-closed, explicit,
    never a silently short corpus."""

_WINDOW_SIZES: tuple[int, ...] = mf.MICRO_FEATURE_WINDOW_TRADES  # (20, 100)
_SHARE_WINDOW_SIZES: tuple[int, ...] = mf.MICRO_FEATURE_WINDOW_SHARES  # (5_000, 50_000)


class _SlidingPair:
    """O(1)-amortized bookkeeping for ONE trade-count window size ``n``: a "current" trailing
    window of the last ``n`` trades and the "prior" NON-OVERLAPPING window of the ``n`` trades
    immediately before it -- both needed for ``efficiency_trend``/``spread_change`` (current minus
    prior) and ``volume_burst`` (current against a trailing tile history), without ever rescanning
    a deque slice (essential at NVDA's ~929K-trade scale -- see module docstring and the dev
    handoff's timing note).

    On each ``push``: if ``current`` is already full, its OLDEST entry graduates into ``prior``
    (evicting prior's own oldest entry first, if prior is also full) BEFORE the new entry enters
    ``current`` -- so ``current`` always holds the ``n`` most recent trades and ``prior`` the ``n``
    immediately before those, both bounded, both O(1) per push."""

    __slots__ = (
        "n",
        "current",
        "prior",
        "cur_buy",
        "cur_sell",
        "cur_spread_sum",
        "cur_spread_n",
        "cur_fallback",
        "cur_unknown",
        "prior_buy",
        "prior_sell",
        "prior_spread_sum",
        "prior_spread_n",
    )

    def __init__(self, n: int) -> None:
        self.n = n
        self.current: Deque[dict] = deque()
        self.prior: Deque[dict] = deque()
        self.cur_buy = 0.0
        self.cur_sell = 0.0
        self.cur_spread_sum = 0.0
        self.cur_spread_n = 0
        self.cur_fallback = 0
        self.cur_unknown = 0
        self.prior_buy = 0.0
        self.prior_sell = 0.0
        self.prior_spread_sum = 0.0
        self.prior_spread_n = 0

    def _remove_from_prior(self, entry: dict) -> None:
        if entry["side"] == "buy":
            self.prior_buy -= entry["size"]
        elif entry["side"] == "sell":
            self.prior_sell -= entry["size"]
        if entry["spread"] is not None:
            self.prior_spread_sum -= entry["spread"]
            self.prior_spread_n -= 1

    def _add_to_prior(self, entry: dict) -> None:
        if entry["side"] == "buy":
            self.prior_buy += entry["size"]
        elif entry["side"] == "sell":
            self.prior_sell += entry["size"]
        if entry["spread"] is not None:
            self.prior_spread_sum += entry["spread"]
            self.prior_spread_n += 1

    def _remove_from_current(self, entry: dict) -> None:
        if entry["side"] == "buy":
            self.cur_buy -= entry["size"]
        elif entry["side"] == "sell":
            self.cur_sell -= entry["size"]
        if entry["spread"] is not None:
            self.cur_spread_sum -= entry["spread"]
            self.cur_spread_n -= 1
        if entry["side_source"] in (mf.SIDE_SOURCE_TICK_TEST, mf.SIDE_SOURCE_CARRIED):
            self.cur_fallback -= 1
        elif entry["side_source"] == mf.SIDE_SOURCE_UNKNOWN:
            self.cur_unknown -= 1

    def _add_to_current(self, entry: dict) -> None:
        if entry["side"] == "buy":
            self.cur_buy += entry["size"]
        elif entry["side"] == "sell":
            self.cur_sell += entry["size"]
        if entry["spread"] is not None:
            self.cur_spread_sum += entry["spread"]
            self.cur_spread_n += 1
        if entry["side_source"] in (mf.SIDE_SOURCE_TICK_TEST, mf.SIDE_SOURCE_CARRIED):
            self.cur_fallback += 1
        elif entry["side_source"] == mf.SIDE_SOURCE_UNKNOWN:
            self.cur_unknown += 1

    def push(self, entry: dict) -> None:
        if len(self.current) >= self.n:
            graduate = self.current.popleft()
            self._remove_from_current(graduate)
            if len(self.prior) >= self.n:
                evicted = self.prior.popleft()
                self._remove_from_prior(evicted)
            self.prior.append(graduate)
            self._add_to_prior(graduate)
        self.current.append(entry)
        self._add_to_current(entry)

    # --- derived readings -------------------------------------------------------------------

    def window_volume(self) -> float:
        return self.cur_buy + self.cur_sell  # directional only -- unknown-sided prints excluded

    def total_window_volume(self) -> float:
        return sum(e["size"] for e in self.current)  # ALL prints, incl. unknown-sided

    def rolling_imbalance(self) -> float | None:
        return mf.rolling_imbalance(self.cur_buy, self.cur_sell)

    def fallback_frac(self) -> float | None:
        if not self.current:
            return None
        return self.cur_fallback / len(self.current)

    def unknown_frac(self) -> float | None:
        if not self.current:
            return None
        return self.cur_unknown / len(self.current)

    def _window_mid_delta_bps(self, buf: Deque[dict], buy: float, sell: float) -> float | None:
        if not buf:
            return None
        mid_start = buf[0]["mid"]
        mid_end = buf[-1]["mid"]
        raw = mf.bps_move(mid_start, mid_end)
        if raw is None:
            return None
        return raw if buy >= sell else -raw  # aggressor-signed (module docstring's own note)

    def current_delta_bps(self) -> float | None:
        """The aggressor-signed mid move over THIS window -- exposed publicly (not just used
        internally by ``impact_efficiency``) so ``failed_aggression_score`` can share the exact
        same reading rather than recompute it a second way."""
        return self._window_mid_delta_bps(self.current, self.cur_buy, self.cur_sell)

    def impact_efficiency(self) -> float | None:
        return mf.impact_efficiency(self.current_delta_bps(), self.window_volume())

    def prior_impact_efficiency(self) -> float | None:
        if len(self.prior) < self.n:
            return None
        delta_bps = self._window_mid_delta_bps(self.prior, self.prior_buy, self.prior_sell)
        return mf.impact_efficiency(delta_bps, self.prior_buy + self.prior_sell)

    def efficiency_trend(self) -> float | None:
        cur = self.impact_efficiency()
        prior = self.prior_impact_efficiency()
        if cur is None or prior is None:
            return None
        return cur - prior

    def spread_change(self) -> float | None:
        if len(self.prior) < self.n or self.cur_spread_n == 0 or self.prior_spread_n == 0:
            return None
        return (self.cur_spread_sum / self.cur_spread_n) - (self.prior_spread_sum / self.prior_spread_n)


class _ShareWindow:
    """The volume-time counterpart to ``_SlidingPair``: a trailing window bounded by cumulative
    SHARES (``MICRO_FEATURE_WINDOW_SHARES``) rather than trade count. O(1) amortized: a deque of
    (side, size) trimmed from the front while the running total exceeds the threshold."""

    __slots__ = ("threshold", "buf", "buy", "sell")

    def __init__(self, threshold: int) -> None:
        self.threshold = threshold
        self.buf: Deque[tuple[str, float]] = deque()
        self.buy = 0.0
        self.sell = 0.0

    def push(self, side: str, size: float) -> None:
        # Unknown-sided prints carry no direction to contribute to a directional volume-time
        # window -- they are deliberately never buffered here at all (never merely zero-weighted),
        # so ``buf`` only ever holds entries whose size IS reflected in ``buy``/``sell``/``total``;
        # trimming below can then subtract any evicted entry's size from ``total`` unconditionally,
        # with no risk of double-uncounting an entry that was never counted in the first place.
        if side not in ("buy", "sell"):
            return
        self.buf.append((side, size))
        if side == "buy":
            self.buy += size
        else:
            self.sell += size
        total = self.buy + self.sell
        while total > self.threshold and len(self.buf) > 1:
            old_side, old_size = self.buf[0]
            # Only trim while the window's directional total still exceeds the threshold WITHOUT
            # the oldest entry -- never trim the entry that is itself needed to stay >= threshold
            # (a share-bounded window is "at least this many shares", the natural reading of a
            # volume-time window).
            remaining = total - old_size
            if remaining < self.threshold:
                break
            self.buf.popleft()
            if old_side == "buy":
                self.buy -= old_size
            else:
                self.sell -= old_size
            total = self.buy + self.sell

    def rolling_imbalance(self) -> float | None:
        return mf.rolling_imbalance(self.buy, self.sell)


class MicroObserver:
    """One instance per replay (constructed fresh, exactly like the ``TapeEngine`` it attaches
    to). ``on_event`` is the ONLY method the engine's ``_notify_event`` calls; every other method
    is this module's own orchestration, called by the snapshot builder (``micro_snapshots.py``)
    around the replay loop."""

    def __init__(self, *, quote_size_unit: str) -> None:
        self.quote_size_unit = quote_size_unit
        self.rows: list[dict] = []
        # The engine swallows observer exceptions (MicroObserverFailure's docstring), so this is
        # the ONLY place a mid-stream failure survives for the snapshot builder to refuse on.
        self.failure: BaseException | None = None

        # --- side_source mirror state (module docstring) -- lockstep with the engine's own
        # MarketState/_last_tick_dir, which the engine does not expose. ---------------------------
        self._current_quote: QuoteEvent | None = None
        self._current_bid_size: int | None = None
        self._current_ask_size: int | None = None
        self._prior_trade_price: float | None = None
        self._last_tick_dir: Side | None = None

        self._event_index = 0
        self._trade_index = 0

        # --- F-FLOW: cumulative delta ---------------------------------------------------------
        self._cumulative_delta = 0.0
        self._cd_unknown_excluded_count = 0

        # --- F-FLOW / F-RESPONSE / F-LIQUIDITY: trade-count sliding windows ---------------------
        self._pairs: dict[int, _SlidingPair] = {n: _SlidingPair(n) for n in _WINDOW_SIZES}
        self._share_windows: dict[int, _ShareWindow] = {
            s: _ShareWindow(s) for s in _SHARE_WINDOW_SIZES
        }

        # --- F-FLOW: same-side run length --------------------------------------------------------
        self._run_side: str | None = None
        self._run_length = 0

        # --- F-FLOW: volume-burst non-overlapping baseline tiles ---------------------------------
        self._tile_accum: dict[int, float] = {n: 0.0 for n in _WINDOW_SIZES}
        self._tile_count: dict[int, int] = {n: 0 for n in _WINDOW_SIZES}
        self._tile_history: dict[int, Deque[float]] = {
            n: deque(maxlen=mf.BURST_BASELINE_TRAILING_WINDOWS) for n in _WINDOW_SIZES
        }

        # --- F-RESPONSE: deferred response_asymmetry -----------------------------------------------
        self._response_pending: list[dict] = []

        # --- F-LIQUIDITY: deferred refill_consistent (per side) + quote-depletion runs ------------
        self._refill_pending: dict[str, list[dict]] = {"bid": [], "ask": []}
        self._depletion_run: dict[str, dict | None] = {"bid": None, "ask": None}

        # Completions resolved by the quote stream, waiting to attach to the next-built row.
        self._pending_attachments: list[dict] = []

        self._last_event_ts: float | None = None

    # --- the engine-called hook ---------------------------------------------------------------

    def on_event(self, event: Event, snapshot) -> None:
        """The engine's ONE call-in. Records any exception on ``self.failure`` and stops consuming
        (a state machine that already raised cannot honestly keep accumulating rows) so the
        snapshot builder can refuse to persist a truncated stream -- see ``MicroObserverFailure``.
        The engine itself is unaffected either way, exactly as its own isolation guarantees."""
        if self.failure is not None:
            return
        try:
            self._consume(event, snapshot)
        except Exception as exc:  # noqa: BLE001 -- recorded here, surfaced by build_snapshot_rows
            self.failure = exc

    def _consume(self, event: Event, snapshot) -> None:
        self._last_event_ts = event.timestamp
        # The TRUE overall event ordinal ("i" in spec section 2.2's "row i is a pure function of
        # events 1..i") -- counts EVERY event, quotes included, even though only trades ever get
        # their own row; a row's own ``event_index`` is therefore the ordinal of the STREAM
        # position it was built at, distinct from ``trade_index`` (that trade's own ordinal among
        # trades only).
        self._event_index += 1
        if isinstance(event, QuoteEvent):
            self._on_quote(event)
            return
        if isinstance(event, TradeEvent):
            self._on_trade(event, snapshot)

    # --- quote handling: side_source mirror state + the two quote-driven deferred families -------

    def _on_quote(self, event: QuoteEvent) -> None:
        self._advance_depletion_run("bid", event.bid, event.bid_size, event.timestamp)
        self._advance_depletion_run("ask", event.ask, event.ask_size, event.timestamp)
        self._advance_refill_pending("bid", event.bid, event.bid_size, event.timestamp)
        self._advance_refill_pending("ask", event.ask, event.ask_size, event.timestamp)
        self._current_quote = event
        self._current_bid_size = event.bid_size
        self._current_ask_size = event.ask_size

    def _side_source(self, trade_price: float) -> str:
        """Mirrors ``classify_aggressor``'s documented stage-1 precondition (module docstring) --
        never a second implementation of the SIDE it decides, only of which stage decided it."""
        quote = self._current_quote
        if quote is not None and (trade_price >= quote.ask or trade_price <= quote.bid):
            return mf.SIDE_SOURCE_QUOTE_RULE
        if self._prior_trade_price is None:
            return mf.SIDE_SOURCE_UNKNOWN
        if trade_price != self._prior_trade_price:
            return mf.SIDE_SOURCE_TICK_TEST
        return mf.SIDE_SOURCE_CARRIED if self._last_tick_dir is not None else mf.SIDE_SOURCE_UNKNOWN

    # --- trade handling ------------------------------------------------------------------------

    def _on_trade(self, event: TradeEvent, snapshot) -> None:
        self._trade_index += 1

        side_source = self._side_source(event.price)
        # The engine's OWN just-computed decision -- never recomputed (spec section 2.5). The
        # engine appendlefts the just-processed trade, so index 0 is always THIS trade.
        side = snapshot.recent_trades[0].side  # "buy" | "sell" | "unknown"

        bid, ask, spread = snapshot.bid, snapshot.ask, snapshot.spread
        mid = mf.mid_price(bid, ask)

        # --- F-FLOW: cumulative delta (unknowns excluded and counted) ---
        if side == "buy":
            self._cumulative_delta += event.size
        elif side == "sell":
            self._cumulative_delta -= event.size
        else:
            self._cd_unknown_excluded_count += 1

        # --- same-side run length (unknown breaks the run; the anchor print counts) ---
        if side == "unknown":
            self._run_side = None
            self._run_length = 0
            run_length_at_anchor = 0
        elif side == self._run_side:
            self._run_length += 1
            run_length_at_anchor = self._run_length
        else:
            self._run_side = side
            self._run_length = 1
            run_length_at_anchor = 1

        entry = {
            "ts": event.timestamp,
            "side": side,
            "side_source": side_source,
            "size": event.size,
            "mid": mid,
            "spread": spread,
        }
        for pair in self._pairs.values():
            pair.push(entry)
        for share_window in self._share_windows.values():
            share_window.push(side, event.size)

        # --- volume-burst non-overlapping tiles (module docstring) ---
        volume_burst: dict[int, float | None] = {}
        for n in _WINDOW_SIZES:
            self._tile_accum[n] += event.size
            self._tile_count[n] += 1
            if self._tile_count[n] >= n:
                self._tile_history[n].append(self._tile_accum[n])
                self._tile_accum[n] = 0.0
                self._tile_count[n] = 0
            pair = self._pairs[n]
            volume_burst[n] = mf.volume_burst(pair.total_window_volume(), list(self._tile_history[n]))

        # --- F-RESPONSE: resolve any response_asymmetry anchors reaching K trades ---
        resolved_response = self._advance_response_pending(mid, event.timestamp)
        self._pending_attachments.extend(resolved_response)
        self._register_response_pending(side, event.timestamp, mid)

        # --- F-RESPONSE: reused engine absorption_score + the continuous complement ---
        # "Primary" for this NEW continuous feature is this module's own smallest trade-count
        # window (20t) -- a distinct concept from the ENGINE's own primary (a 30s CLOCK window,
        # read verbatim above for the reused absorption_score); an interpretation call, logged in
        # the dev handoff.
        absorption_score = snapshot.primary_features["absorption_score"]
        primary_pair = self._pairs[_WINDOW_SIZES[0]]
        dominant_share = mf.dominant_side_volume_share(primary_pair.cur_buy, primary_pair.cur_sell)
        failed_aggression = mf.failed_aggression_score(dominant_share, primary_pair.current_delta_bps())

        # --- F-LIQUIDITY: quote_imbalance / microprice (instantaneous, at the in-effect NBBO) ---
        q_imbalance = None
        mprice = None
        if self._current_bid_size is not None and self._current_ask_size is not None and bid is not None and ask is not None:
            q_imbalance = mf.quote_imbalance(self._current_bid_size, self._current_ask_size)
            mprice = mf.microprice(bid, ask, self._current_bid_size, self._current_ask_size)

        row = {
            "anchor_at": event.timestamp,
            "observed_through": event.timestamp,
            "available_at": event.timestamp,
            "event_index": self._event_index,
            "trade_index": self._trade_index,
            "side": side,
            "side_source": side_source,
            "price": event.price,
            "size": event.size,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "mid": mid,
            "tape_state": snapshot.tape_state,
            "quote_size_unit": self.quote_size_unit,
            # F-FLOW
            "cumulative_delta": self._cumulative_delta,
            "cumulative_delta_unknown_excluded_count": self._cd_unknown_excluded_count,
            "same_side_run_length": run_length_at_anchor,
            "volume_burst_20t": volume_burst.get(20),
            "volume_burst_100t": volume_burst.get(100),
            # F-RESPONSE
            "absorption_score": absorption_score,
            "failed_aggression_score": failed_aggression,
            # F-LIQUIDITY
            "quote_imbalance": q_imbalance,
            "microprice": mprice,
            # deferred completions resolved AT this row (each carries its own triple)
            "deferred": list(self._pending_attachments),
        }
        self._pending_attachments = []
        for n in _WINDOW_SIZES:
            pair = self._pairs[n]
            row[f"rolling_imbalance_{n}t"] = pair.rolling_imbalance()
            row[f"impact_efficiency_{n}t"] = pair.impact_efficiency()
            row[f"efficiency_trend_{n}t"] = pair.efficiency_trend()
            row[f"spread_change_{n}t"] = pair.spread_change()
            row[f"fallback_frac_{n}t"] = pair.fallback_frac()
            row[f"unknown_frac_{n}t"] = pair.unknown_frac()
        for s in _SHARE_WINDOW_SIZES:
            row[f"rolling_imbalance_{s}sh"] = self._share_windows[s].rolling_imbalance()

        self.rows.append(row)

        # --- update side_source mirror state for the NEXT trade (module docstring: identical to
        # the engine's own unconditional tick-direction update, AFTER this trade is used) ---
        if self._prior_trade_price is not None:
            if event.price > self._prior_trade_price:
                self._last_tick_dir = Side.BUY
            elif event.price < self._prior_trade_price:
                self._last_tick_dir = Side.SELL
        self._prior_trade_price = event.price

        # --- register a refill-pending check IFF this trade genuinely executed against the
        # displayed quote (side_source == quote_rule); see module docstring. ---
        self._maybe_register_refill_pending(side, side_source, event.timestamp)

    # --- deferred: response_asymmetry ------------------------------------------------------------

    def _register_response_pending(self, side: str, ts: float, mid: float | None) -> None:
        if side not in ("buy", "sell"):
            return
        self._response_pending.append(
            {"anchor_at": ts, "side": side, "mid_at_anchor": mid, "trades_since": 0}
        )

    def _advance_response_pending(self, mid_now: float | None, ts: float) -> list[dict]:
        resolved: list[dict] = []
        still: list[dict] = []
        for check in self._response_pending:
            check["trades_since"] += 1
            if check["trades_since"] >= mf.RESPONSE_K_TRADES:
                raw = mf.bps_move(check["mid_at_anchor"], mid_now)
                value = raw if (raw is None or check["side"] != "sell") else -raw
                resolved.append(
                    {
                        "kind": "response_asymmetry",
                        "side": check["side"],
                        "anchor_at": check["anchor_at"],
                        "observed_through": ts,
                        "available_at": ts,
                        "value": value,
                        "unavailable": value is None,
                    }
                )
            else:
                still.append(check)
        self._response_pending = still
        return resolved

    # --- deferred: refill_consistent --------------------------------------------------------------

    def _maybe_register_refill_pending(self, side: str, side_source: str, ts: float) -> None:
        if side_source != mf.SIDE_SOURCE_QUOTE_RULE:
            return  # only a confirmed execution AGAINST the displayed quote is meaningful here
        quote = self._current_quote
        if quote is None:
            return
        if side == "buy" and self._current_ask_size is not None:
            self._refill_pending["ask"].append(
                {"anchor_at": ts, "price": quote.ask, "pre_size": self._current_ask_size, "updates_seen": 0}
            )
        elif side == "sell" and self._current_bid_size is not None:
            self._refill_pending["bid"].append(
                {"anchor_at": ts, "price": quote.bid, "pre_size": self._current_bid_size, "updates_seen": 0}
            )

    def _advance_refill_pending(self, side: str, price: float, size: int, ts: float) -> None:
        pending = self._refill_pending[side]
        if not pending:
            return
        still: list[dict] = []
        for check in pending:
            if price == check["price"] and size >= check["pre_size"]:
                self._pending_attachments.append(
                    {
                        "kind": "refill_consistent",
                        "side": side,
                        "anchor_at": check["anchor_at"],
                        "observed_through": ts,
                        "available_at": ts,
                        "value": True,
                        "unavailable": False,
                    }
                )
                continue
            check["updates_seen"] += 1
            if check["updates_seen"] >= mf.REFILL_M_QUOTES:
                self._pending_attachments.append(
                    {
                        "kind": "refill_consistent",
                        "side": side,
                        "anchor_at": check["anchor_at"],
                        "observed_through": ts,
                        "available_at": ts,
                        "value": False,
                        "unavailable": False,
                    }
                )
                continue
            still.append(check)
        self._refill_pending[side] = still

    # --- deferred: quote_depletion -----------------------------------------------------------------

    def _advance_depletion_run(self, side: str, price: float, size: int, ts: float) -> None:
        run = self._depletion_run[side]
        if run is None or run["price"] != price:
            if run is not None:
                self._resolve_depletion(side, run)
            self._depletion_run[side] = {
                "run_start_ts": ts,
                "price": price,
                "start_size": size,
                "current_size": size,
                "updates_seen": 0,
                "observed_through": ts,
            }
            return
        run["current_size"] = size
        run["updates_seen"] += 1
        run["observed_through"] = ts
        if run["updates_seen"] >= mf.DEPLETION_WINDOW_QUOTES:
            self._resolve_depletion(side, run)
            self._depletion_run[side] = None

    def _resolve_depletion(self, side: str, run: dict, *, unavailable_at: float | None = None) -> None:
        """The depletion MAGNITUDE (``start_size - current_size``) is a raw share-denominated
        CROSS-BASIS quantity (spec section 3's own "as is any share-denominated depletion/
        replenishment magnitude"), so it passes the section 2.6 gate at THIS call site before it is
        ever attached -- under an unverified ``quote_size_unit`` the value is refused (``None`` plus
        the closed-vocabulary ``refusal_reason``), never a silently normalized number. The run's
        unit-INVARIANT facts (the availability triple, the price, how many updates were observed)
        are served either way: the observation completed, only its magnitude is not reportable.
        ``unavailable`` therefore stays ``False`` -- a refusal is a different, honest state from
        "the session ended before this window closed".

        ``unavailable_at`` is passed ONLY by ``finalize()``, for a run the session cut short: the
        window never ended (no price change, no ``DEPLETION_WINDOW_QUOTES`` bound), so spec section
        0's availability law applies verbatim -- the construct is ``unavailable`` (COUNTED, never
        guessed), exactly as ``response_asymmetry``/``refill_consistent`` already are in the same
        sweep. There is no completed magnitude to report, gated or otherwise, so ``refused`` is
        ``False`` too: a refusal states "this window closed and its magnitude is not reportable
        under this unit basis", which would be a false claim about a window that never closed."""
        if unavailable_at is not None:
            depletion = None
            refusal_reason = None
            observed_through = unavailable_at
        else:
            try:
                mf.require_share_denominated_magnitude_allowed(self.quote_size_unit)
            except mf.CrossBasisUnverifiedUnitError:
                depletion = None
                refusal_reason = mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT
            else:
                depletion = run["start_size"] - run["current_size"]
                refusal_reason = None
            observed_through = run["observed_through"]
        self._pending_attachments.append(
            {
                "kind": "quote_depletion",
                "side": side,
                "anchor_at": run["run_start_ts"],
                "observed_through": observed_through,
                "available_at": observed_through,
                "value": depletion,
                "unavailable": unavailable_at is not None,
                "refused": refusal_reason is not None,
                "refusal_reason": refusal_reason,
                "price": run["price"],
                "updates_observed": run["updates_seen"],
            }
        )

    # --- session close-out ---------------------------------------------------------------------

    def finalize(self) -> None:
        """Called ONCE by the snapshot builder after the replay generator is exhausted (the
        engine exposes no "stream ended" observer hook -- module docstring). Sweeps every still-
        pending deferred construct into an honest ``unavailable`` completion (session ended before
        its observation window completed -- COUNTED, never silently dropped) and, if any
        completions -- resolved or newly-unavailable -- are still waiting to attach, appends ONE
        final close-out row carrying them. Idempotent: a second call with nothing pending is a
        no-op. Never touches (mutates) any already-appended row."""
        ts = self._last_event_ts if self._last_event_ts is not None else 0.0
        for check in self._response_pending:
            self._pending_attachments.append(
                {
                    "kind": "response_asymmetry",
                    "side": check["side"],
                    "anchor_at": check["anchor_at"],
                    "observed_through": ts,
                    "available_at": ts,
                    "value": None,
                    "unavailable": True,
                }
            )
        self._response_pending = []
        for side in ("bid", "ask"):
            for check in self._refill_pending[side]:
                self._pending_attachments.append(
                    {
                        "kind": "refill_consistent",
                        "side": side,
                        "anchor_at": check["anchor_at"],
                        "observed_through": ts,
                        "available_at": ts,
                        "value": None,
                        "unavailable": True,
                    }
                )
            self._refill_pending[side] = []
            run = self._depletion_run[side]
            if run is not None:
                # The window never ended (no price change, no update bound) -- spec section 0:
                # unavailable, counted, never guessed. NEVER resolved as if it had completed.
                self._resolve_depletion(side, run, unavailable_at=ts)
                self._depletion_run[side] = None
        if self._pending_attachments:
            self.rows.append(
                {
                    "anchor_at": ts,
                    "observed_through": ts,
                    "available_at": ts,
                    "event_index": self._event_index,
                    "trade_index": None,
                    "close_out": True,
                    "deferred": list(self._pending_attachments),
                }
            )
            self._pending_attachments = []
