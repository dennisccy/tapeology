"""Event-log / transition message emitter.

Emits a discrete ``"Tape state changed to <state>"`` message the moment the tape state
transitions (e.g. from the cold-start ``unclear`` into ``buyer_control``). On a transition
INTO an absorption state it also emits an absorption-specific line built from REAL in-window
evidence — the held bid/ask price and whether a large print was absorbed (no fabrication).
The classifier owns the per-tick *observations* (current evidence); this emitter owns the
*appended* event log so each message is recorded once, on the transition, not every tick.
"""

from __future__ import annotations

from .classifier import STATE_ASK_ABSORPTION, STATE_BID_ABSORPTION


class ObservationEmitter:
    def __init__(self) -> None:
        self._previous_state: str | None = None

    def on_tick(
        self,
        state: str,
        *,
        bid: float | None = None,
        ask: float | None = None,
        large_print_count: float = 0.0,
    ) -> list[str]:
        """Return any new event-log messages for this tick (usually none)."""
        messages: list[str] = []
        if self._previous_state is not None and state != self._previous_state:
            messages.append(f"Tape state changed to {state}")
            messages.extend(self._absorption_messages(state, bid, ask, large_print_count))
        self._previous_state = state
        return messages

    @staticmethod
    def _absorption_messages(
        state: str, bid: float | None, ask: float | None, large_print_count: float
    ) -> list[str]:
        messages: list[str] = []
        if state == STATE_BID_ABSORPTION:
            if large_print_count >= 1:
                messages.append("Large sell print absorbed")
            if bid is not None:
                messages.append(f"Bid refreshing at {bid:.2f}")
        elif state == STATE_ASK_ABSORPTION:
            if large_print_count >= 1:
                messages.append("Large buy print absorbed")
            if ask is not None:
                messages.append(f"Ask refreshing at {ask:.2f}")
        return messages
