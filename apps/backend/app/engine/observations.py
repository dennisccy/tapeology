"""Event-log / transition message emitter.

Emits a discrete ``"Tape state changed to <state>"`` message the moment the tape state
transitions (e.g. from the cold-start ``unclear`` into ``buyer_control``). The classifier
owns the per-tick *observations* (current evidence); this emitter owns the *appended* event
log so a message is recorded once, on the transition, not on every tick.
"""

from __future__ import annotations


class ObservationEmitter:
    def __init__(self) -> None:
        self._previous_state: str | None = None

    def on_tick(self, state: str) -> list[str]:
        """Return any new event-log messages for this tick (usually none)."""
        messages: list[str] = []
        if self._previous_state is not None and state != self._previous_state:
            messages.append(f"Tape state changed to {state}")
        self._previous_state = state
        return messages
