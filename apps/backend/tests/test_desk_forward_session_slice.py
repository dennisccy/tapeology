"""``desk_forward._session_slice`` is exactly the per-bar filter it replaced.

``compute_forward`` used to select a screen date's own session with
``[b for b in bars if _session_date(b.epoch) == window_date and b.epoch <= as_of_epoch]``, which
re-read a symbol's whole intraday history (a 1m pair on the live store holds ~360k rows) to keep
one session's ~390. ``_session_slice`` binary-searches the run instead. This file pins that the two
forms select the SAME rows, in the SAME order, across the edges where a bisect is easy to get wrong
— empty input, the exact midnight boundaries at both ends, a session absent from the series, and
the ``as_of`` bound biting before the day ends."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.providers.adapters.base import RawBar
from app.research.desk_forward import _session_date, _session_slice


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _bar(epoch: float) -> RawBar:
    return RawBar("AAPL", "1m", epoch, 1.0, 2.0, 0.5, 1.5, 100)


def _linear(bars: list[RawBar], window_date: date, as_of_epoch: float) -> list[RawBar]:
    """The exact expression ``compute_forward`` carried before the bisect."""
    return [b for b in bars if _session_date(b.epoch) == window_date and b.epoch <= as_of_epoch]


# One ascending series spanning three UTC days, deliberately including both midnights and the last
# representable second of each day.
_SERIES = [
    _bar(_epoch(v))
    for v in [
        "2026-07-29T23:58:00Z",
        "2026-07-29T23:59:59Z",
        "2026-07-30T00:00:00Z",  # first row of the target session — the lower edge
        "2026-07-30T00:01:00Z",
        "2026-07-30T13:30:00Z",
        "2026-07-30T19:59:00Z",
        "2026-07-30T23:59:59Z",  # last row of the target session — the upper edge
        "2026-07-31T00:00:00Z",
        "2026-07-31T09:30:00Z",
    ]
]


@pytest.mark.parametrize(
    ("window_date", "as_of"),
    [
        (date(2026, 7, 30), _epoch("2026-07-30T23:59:59Z")),  # the real screen-day contract
        (date(2026, 7, 29), _epoch("2026-07-29T23:59:59Z")),  # first day, run starts mid-series
        (date(2026, 7, 31), _epoch("2026-07-31T23:59:59Z")),  # last day, run reaches the end
        (date(2026, 7, 28), _epoch("2026-07-28T23:59:59Z")),  # a session the series does not hold
        (date(2026, 8, 5), _epoch("2026-08-05T23:59:59Z")),  # entirely after the series
        (date(2026, 7, 30), _epoch("2026-07-30T13:30:00Z")),  # as_of bites before the day ends
        (date(2026, 7, 30), _epoch("2026-07-30T00:00:00Z")),  # as_of admits exactly one row
        (date(2026, 7, 30), _epoch("2026-07-29T12:00:00Z")),  # as_of before the session entirely
    ],
)
def test_the_slice_selects_what_the_filter_selected(window_date: date, as_of: float) -> None:
    assert _session_slice(_SERIES, window_date, as_of) == _linear(_SERIES, window_date, as_of)


def test_an_empty_series_slices_to_nothing() -> None:
    assert _session_slice([], date(2026, 7, 30), _epoch("2026-07-30T23:59:59Z")) == []


def test_a_series_holding_only_the_target_session_is_returned_whole() -> None:
    only = [b for b in _SERIES if _session_date(b.epoch) == date(2026, 7, 30)]
    assert _session_slice(only, date(2026, 7, 30), _epoch("2026-07-30T23:59:59Z")) == only


def test_the_returned_list_is_fresh_so_a_caller_cannot_poison_the_series() -> None:
    """``compute_forward`` hands the slice on to ``_touch_scan``; a slice that aliased the cached
    merged list would let any in-place edit downstream reach every later reader of that pair."""
    sliced = _session_slice(_SERIES, date(2026, 7, 30), _epoch("2026-07-30T23:59:59Z"))
    assert sliced is not _SERIES
    sliced.clear()
    assert len(_SERIES) == 9
