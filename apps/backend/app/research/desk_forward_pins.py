"""Forward-coverage disclosure (forward-test era) -- answers, for a caller-supplied ``screen_id``,
how much of that snapshot the forward measurement could POSSIBLY reach: how many of its ranked
members hold a recorded 1m/5m series whose window covers the screen date's own session. Served by
``GET /research/desk/forward/pins``.

**The problem this exists for.** ``compute_forward`` reads the touch ladder only
(``DESK_FORWARD_TOUCH_TIMEFRAMES`` -- 1m, then 5m), and the desk top-up fetches those from a vendor
that retains roughly the last 30 days of 1m and 60 of 5m. A screen recorded for a date older than
that is perfectly real -- its wall map is built from 1d/1h/4h/1w bars that reach back years -- while
its forward measurement is structurally empty: every row comes back "no 1m or 5m bars recorded for
the <date> session". Before this disclosure the only way to learn that was to run the measurement,
which on a long as-of range meant hours. Now the panel can say it before anything is clicked.

**An UPPER BOUND, stated as one.** This module reports how many members have a covering SERIES
WINDOW, which is strictly more than the number that have BARS in that session: a holiday, a halt,
or a top-up that ran before the session opened all leave a covering window with nothing in it. On
2026-08-06 three windows covered the date and zero rows were measurable, because the top-up ran at
06:39Z and the US session opens 13:30Z. Every string this feeds must therefore say "at most", and
the exact answer stays where it has always lived -- ``compute_forward``'s own per-row
``merged_bars`` read, during the run.

**Why not just read the bars.** Resolving the exact count means the same ~101 x 2 ``merged_bars``
reads the walk itself makes -- around the whole cost of the measurement. A disclosure that
expensive on a page-load GET is exactly the "GET never computes" rule this codebase already holds
(era-5C J-01), so the fine-coverage count resolves through ``BarIndex.covers_date``: one indexed
aggregate per pair.

**Where the screen date SITS, alongside how far a run could reach.** A count of zero is the same
number for three materially different situations -- the date is a weekend or a market holiday, the
date is a real session whose fine bars fell off the vendor's ~30/60-day retention floor, or the
date has not happened yet. Reading a table of em-dashes, those are indistinguishable, and on
2026-08-08 the ``/desk`` default view was the third one (the newest recorded screen was the coming
Monday). ``session.state`` names which, resolved through ``desk_sessions`` over the SCREEN'S OWN
ranked members -- bounded to a handful of daily-bar anchors (``DESK_SESSION_ANCHOR_LIMIT``), so the
whole addition is a few ``merged_bars("1d")`` reads rather than anything approaching the walk.

**Disclose where it sits; never compose the sentence.** ``session.state`` is a plain statement of
fact about recorded daily bars. It carries no cause, no blame and no advice -- the renderer holds
the record's own row counts and composes the reading from both, so this module stays free of any
judgement about what the emptiness MEANS.

**Disclose, never judge (T-copy discipline).** The response states what is recorded and stops
there -- no threshold, no "enough"/"too little", no advice, no prediction about what a run would
find. A low count proves exactly one thing: at most that many of this snapshot's rows have a fine
series covering the date.

**Persists nothing.** No store, no file, no cache, no index, no new ``Config`` field -- a pure read
over three already-constructed dependencies (``ScreenStore``, ``BarIndex``, ``ForwardStore``)."""

from __future__ import annotations

from .bar_index import BarIndex
from .desk_forward import DESK_FORWARD_TOUCH_TIMEFRAMES, ForwardStore
from .desk_screen import ScreenStore
from .desk_sessions import is_known_non_session, recorded_session_dates, session_evidence

__all__ = ["resolve_desk_forward_pins"]

# The five places a screen date can sit relative to the daily bars actually on file. Deliberately
# descriptive rather than causal: "there is no daily bar for this date, and the anchors' recorded
# span covers it" is a fact, where "this is a holiday" would be an inference this module has no
# basis for.
SESSION_STATE_RECORDED = "recorded_session"
SESSION_STATE_NOT_A_SESSION = "not_a_recorded_session"
SESSION_STATE_AFTER_EVIDENCE = "after_recorded_evidence"
SESSION_STATE_BEFORE_EVIDENCE = "before_recorded_evidence"
SESSION_STATE_UNKNOWN = "unknown"


def _resolve_session_state(screen_date: str, bar_store, members: list[str]) -> dict:
    """Where ``screen_date`` sits relative to the daily bars on file, plus the evidence that
    answer rests on. ``bar_store is None`` (every caller that has not been given one) is the
    honest-unknown state -- never a guess, and never a claim that a date is not a session."""
    if bar_store is None:
        return {"state": SESSION_STATE_UNKNOWN, "evidence": None}

    evidence = session_evidence(bar_store, members)
    sessions = recorded_session_dates(bar_store, members)
    if not evidence["anchor_symbols"]:
        return {"state": SESSION_STATE_UNKNOWN, "evidence": evidence}
    if screen_date in sessions:
        state = SESSION_STATE_RECORDED
    elif is_known_non_session(screen_date, sessions, evidence):
        state = SESSION_STATE_NOT_A_SESSION
    elif screen_date > evidence["through"]:
        state = SESSION_STATE_AFTER_EVIDENCE
    else:
        state = SESSION_STATE_BEFORE_EVIDENCE
    return {"state": state, "evidence": evidence}


def resolve_desk_forward_pins(
    screen_id: str,
    screen_store: ScreenStore,
    bar_index: BarIndex,
    forward_store: ForwardStore,
    bar_store=None,
) -> dict:
    """What a forward measurement of ``screen_id`` could reach right now, plus whether one is
    already recorded. ``screen_id`` is the caller's own value (the panel passes the id of the
    snapshot it currently displays) -- nothing here calls ``now()``: identical inputs (this
    snapshot, the index's rows as they stand) reproduce a byte-identical body.

    Shape::

        {
          "screen_id": str, "screen_date": str | None, "as_of": str | None,
          "touch_timeframes": [str, ...],
          "members_total": int, "members_with_fine_series": int,
          "versions": int,
          "recorded": {"id", "created_utc", "rows_with_touches", "total_touches"} | None,
          "session": {"state": str, "evidence": {...} | None},
        }

    An unknown ``screen_id`` is an honest all-zero/``None`` body at HTTP 200, never a 404 -- the
    ``GET /research/desk/forward``/``desk_screen_pins`` honest-empty convention.

    ``bar_store`` is optional and defaults to ``None``, which resolves ``session.state`` to
    ``"unknown"``. It is a keyword with a default rather than a required argument precisely so that
    "nobody handed me the daily bars" and "the daily bars say nothing" produce the SAME honest
    non-answer -- a caller that cannot supply one still gets every other pin, and never gets a
    fabricated session claim.
    """
    screen = screen_store.get(screen_id)
    if screen is None:
        return {
            "screen_id": screen_id,
            "screen_date": None,
            "as_of": None,
            "touch_timeframes": list(DESK_FORWARD_TOUCH_TIMEFRAMES),
            "members_total": 0,
            "members_with_fine_series": 0,
            "versions": 0,
            "recorded": None,
            "session": {"state": SESSION_STATE_UNKNOWN, "evidence": None},
        }

    screen_date = screen["screen_date"]
    symbols = [row["symbol"] for row in screen["rows"]]
    # A member counts once, whichever ladder rung covers the date -- the walk itself takes the
    # FINEST rung that holds bars, so a 5m-only member is as reachable as a 1m one.
    with_fine_series = sum(
        1
        for symbol in symbols
        if any(
            bar_index.covers_date(symbol, timeframe, screen_date)
            for timeframe in DESK_FORWARD_TOUCH_TIMEFRAMES
        )
    )

    newest, versions = forward_store.newest_for_screen(screen_id)
    recorded = None
    if newest is not None:
        recorded = {
            "id": newest["id"],
            "created_utc": newest["created_utc"],
            "rows_with_touches": newest["rows_with_touches"],
            "total_touches": newest["total_touches"],
        }

    return {
        "screen_id": screen_id,
        "screen_date": screen_date,
        "as_of": screen["as_of"],
        "touch_timeframes": list(DESK_FORWARD_TOUCH_TIMEFRAMES),
        "members_total": len(symbols),
        "members_with_fine_series": with_fine_series,
        "versions": versions,
        "recorded": recorded,
        # The screen's OWN ranked members are the anchors -- the same list the measurement walks,
        # so the session claim rests on exactly the symbols the disclosure is about.
        "session": _resolve_session_state(screen_date, bar_store, symbols),
    }
