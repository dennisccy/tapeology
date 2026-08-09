"""The desk's one owner of "is this date a trading session" — derived entirely from recorded daily
bars, never from a hardcoded calendar.

**The problem this exists for.** The desk chain enumerated raw CALENDAR days: a [From, To] range
screened Saturdays, Sundays, US market holidays and dates that have not happened yet exactly like
real sessions. Each one recorded a perfectly real screen (its wall map comes from the PRIOR
session's 1d/1h/4h/1w bars) whose forward measurement is structurally empty — every row comes back
"no 1m or 5m bars recorded for the <date> session". On 2026-08-08 that was ~268 weekend + ~10
holiday + 2 future snapshots out of 939, and a matching ~272 all-absent forward records: roughly a
third of both stores, and the reason ``/desk`` opened on a table of em-dashes.

**Calendar-free by construction.** There is no holiday table here, no exchange-calendar dependency,
no weekday arithmetic. A session is a date on which a recorded daily bar exists — the SAME premise
``tradability.py`` already states for its morning-markup basis: *"holidays and weekends are handled
for free -- no hardcoded calendar, since a missing daily bar simply is not a candidate."* A future
date is handled by the same rule for free: no bar has been recorded for it yet, so it is not a
recorded session.

**A union over anchor members, not one symbol.** A single symbol can be halted for a day the market
traded, so one symbol's daily series would report a false non-session. The union over the first
``DESK_SESSION_ANCHOR_LIMIT`` members that hold daily bars removes that failure mode at a bounded
cost (a handful of ``merged_bars`` reads, not the ~101 x 2 the forward walk makes).

**Unknown is a first-class answer.** With no daily bars recorded at all, ``recorded_session_dates``
returns an EMPTY set and ``session_evidence`` reports ``anchor_symbols: []`` with null bounds. That
is "no evidence", NOT "no sessions" — every consumer must fail OPEN on it (screen nothing refused,
nothing filtered, nothing classified). ``is_known_non_session`` encodes that rule once so no caller
has to re-derive it.

**Bounded claims only.** Evidence bounds matter as much as the set: a date outside
``[from, through]`` is not a date this module has anything to say about. ``is_known_non_session``
therefore answers ``True`` only for a date the anchors' own recorded span covers and does not
contain — a date after the last recorded daily bar (tomorrow, next Monday) is reported through
``future_of_evidence`` instead, which is a different, equally honest fact.

**Reads through the accessor everything else reads through.** ``BarStore.merged_bars(symbol,
"1d")`` — every recording for the pair folded into one ascending, de-duplicated series, exactly as
``tradability._select_daily_series`` and ``desk_screen`` read it. Never ``BarIndex``: the index
stores window BOUNDS only and documents at ``bar_index.py:195-201`` that a window containing a day
proves nothing about bars on that day, which is precisely the distinction this module exists to
make.

**Persists nothing, computes nothing.** No store, no file, no cache, no index, no new ``Config``
field, no wall-clock read — a pure read over one already-constructed ``BarStore``."""

from __future__ import annotations

from datetime import datetime, timezone

__all__ = [
    "DESK_SESSION_ANCHOR_TIMEFRAME",
    "DESK_SESSION_ANCHOR_LIMIT",
    "recorded_session_dates",
    "session_evidence",
    "is_known_non_session",
    "non_session_refusal",
    "refuse_if_not_a_session",
]

# The timeframe a session is derived from. A daily bar is the market-wide "this date traded" fact:
# it exists for every session and for no non-session, and it reaches back years (unlike the fine
# ladder, which a vendor retains for ~30/60 days). A plain structural constant, NOT a ``Config``
# field — it shapes no persisted tape/backtest/study value, so it carries none of ``config.py``'s
# fingerprint-stability discipline (the ``DESK_TOPUP_TIMEFRAMES``/``DESK_FORWARD_TOUCH_TIMEFRAMES``
# precedent).
DESK_SESSION_ANCHOR_TIMEFRAME = "1d"

# How many daily-bar-holding members the union spans. One symbol can be halted on a day the market
# traded; a handful cannot all be. Bounded deliberately: this resolves on a GET, and each anchor
# costs one ``merged_bars`` read, so the whole universe would make the disclosure as expensive as
# the measurement it describes (the ``desk_forward_pins`` "GET never computes" rule).
DESK_SESSION_ANCHOR_LIMIT = 5


def _session_date(epoch: float) -> str:
    """The UTC calendar date a bar belongs to, as ``yyyy-MM-dd`` — the ``tradability._session_date``
    shape, stringified because every consumer here compares against a ``screen_date`` string."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).date().isoformat()


def _anchor_symbols(bar_store, members: list[str]) -> list[str]:
    """The first ``DESK_SESSION_ANCHOR_LIMIT`` of ``members`` that hold a recorded daily series, in
    the caller's own member order (stable: identical inputs pick identical anchors). Resolved from
    the store's metadata listing alone — ``include_bars=False``, so choosing the anchors reads no
    bars at all."""
    records, _errors = bar_store.list(include_bars=False)
    with_daily = {
        record["symbol"]
        for record in records
        if record["timeframe"] == DESK_SESSION_ANCHOR_TIMEFRAME
    }
    anchors: list[str] = []
    for symbol in members:
        if symbol in with_daily:
            anchors.append(symbol)
            if len(anchors) >= DESK_SESSION_ANCHOR_LIMIT:
                break
    return anchors


def session_evidence(bar_store, members: list[str]) -> dict:
    """What this module can prove about sessions right now, and from what.

    Shape::

        {
          "anchor_timeframe": str,
          "anchor_symbols": [str, ...],       # [] == no evidence at all
          "from": str | None,                 # earliest recorded session date
          "through": str | None,              # latest recorded session date
          "sessions_total": int,
        }

    ``anchor_symbols == []`` (and the null bounds that come with it) is the honest-unknown state:
    no member holds a daily series, so nothing here can classify any date. Callers fail OPEN on it.
    """
    sessions = recorded_session_dates(bar_store, members)
    anchors = _anchor_symbols(bar_store, members)
    ordered = sorted(sessions)
    return {
        "anchor_timeframe": DESK_SESSION_ANCHOR_TIMEFRAME,
        "anchor_symbols": anchors,
        "from": ordered[0] if ordered else None,
        "through": ordered[-1] if ordered else None,
        "sessions_total": len(ordered),
    }


def recorded_session_dates(bar_store, members: list[str]) -> frozenset[str]:
    """Every ``yyyy-MM-dd`` on which a daily bar is recorded for at least one anchor member.

    An EMPTY set means "no daily bars are recorded", never "no sessions exist" — the two are
    indistinguishable from the set alone, which is why ``is_known_non_session`` takes the evidence
    into account and every consumer routes its decision through it."""
    dates: set[str] = set()
    for symbol in _anchor_symbols(bar_store, members):
        for bar in bar_store.merged_bars(symbol, DESK_SESSION_ANCHOR_TIMEFRAME):
            dates.add(_session_date(bar.epoch))
    return frozenset(dates)


def is_known_non_session(day: str, sessions: frozenset[str], evidence: dict) -> bool:
    """``True`` only when ``day`` is PROVABLY not a trading session: the anchors' recorded span
    covers it and does not contain it (a weekend, a US market holiday, an exchange-wide closure).

    Deliberately ``False`` — never "unknown" as a third value the callers would each have to
    handle — in all three unproven cases:

      * no evidence at all (``anchor_symbols == []``): nothing is knowable;
      * ``day`` is AFTER ``through``: the session may simply not have been recorded yet. That a
        future Monday is not a session today is true but not something daily bars can prove, and
        the honest fact about it (``future_of_evidence``) belongs to the caller that renders it;
      * ``day`` is BEFORE ``from``: history the anchors never reached.

    Every consumer therefore fails OPEN by construction — an unproven date is screened, listed and
    kept exactly as it was before this module existed."""
    if not evidence.get("anchor_symbols"):
        return False
    first, last = evidence.get("from"), evidence.get("through")
    if first is None or last is None:
        return False
    if day < first or day > last:
        return False
    return day not in sessions


def non_session_refusal(day: str, evidence: dict) -> str:
    """The one sentence both refusal sites say, so the HTTP route and the CLI can never drift into
    telling an operator two different things about the same date. Names the evidence rather than
    asserting a holiday calendar nobody here holds."""
    anchors = ", ".join(evidence["anchor_symbols"])
    return (
        f"{day} is not a recorded trading session -- the daily bars on file for {anchors} "
        f"({evidence['from']} through {evidence['through']}) record no session on that date. A "
        "screen for it would carry a map built from an earlier session and a forward measurement "
        "that is empty by construction."
    )


def refuse_if_not_a_session(day: str, bar_store, members: list[str]) -> str | None:
    """The refusal both entry points share: the sentence to refuse ``day`` with, or ``None`` to let
    it through. ``None`` on every unproven case (``is_known_non_session``'s fail-open contract), so
    a store with no daily bars refuses nothing at all -- the pre-existing behaviour, unchanged."""
    evidence = session_evidence(bar_store, members)
    sessions = recorded_session_dates(bar_store, members)
    if is_known_non_session(day, sessions, evidence):
        return non_session_refusal(day, evidence)
    return None
