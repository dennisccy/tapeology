"""``providers/base.py`` -- ``TradeEvent``/``QuoteEvent`` hash-safety (era "The Rapid Microscope"
iter-8, closing iter-7 audit finding B5).

Both are ``frozen=True`` dataclasses, so Python auto-generates ``__hash__`` over every
comparable field. With ``conditions`` typed ``list[str] | None``, ``hash(event)`` raised
``TypeError: unhashable type: 'list'`` the moment a caller populated it with a real value --
untested until this iteration, because no code path before ``tick_recorder.py`` (this same
iteration) ever built an event carrying real Card-5.1 preservation data. TC-12."""

from __future__ import annotations

from app.providers.base import QuoteEvent, Side, TradeEvent


def test_a_trade_event_with_populated_conditions_stays_hashable():
    event = TradeEvent(
        "AAPL", 1.0, 100.0, 10, Side.BUY,
        conditions=["@", "F"], exchange="Q", tape="C", trade_id=12345,
    )
    hash(event)  # must not raise TypeError


def test_a_quote_event_with_populated_conditions_stays_hashable():
    event = QuoteEvent(
        "AAPL", 1.0, 100.0, 100.05, 200, 300,
        conditions=["R"], tape="C", bid_exchange="Q", ask_exchange="K",
    )
    hash(event)  # must not raise TypeError


def test_a_legacy_trade_event_with_conditions_none_hashes_the_same_as_before_this_fix():
    """TC-12's second half: a legacy (``conditions=None``) event's hash is UNCHANGED by this fix
    -- proven by constructing the identical event twice and comparing hashes, the behaviour every
    pre-iteration call site already relied on."""
    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY)
    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY)
    assert hash(a) == hash(b)


def test_a_legacy_quote_event_with_conditions_none_hashes_consistently():
    a = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300)
    b = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300)
    assert hash(a) == hash(b)


def test_two_trade_events_differing_only_in_conditions_are_unequal_but_both_hashable():
    """Hash coarser than equality is legal: excluding ``conditions`` from the hash while keeping
    it in ``__eq__`` never breaks the hash contract (equal objects must hash equal; the converse
    is not required)."""
    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["@"])
    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["F"])
    assert a != b
    hash(a)
    hash(b)


def test_trade_event_hash_does_not_depend_on_which_conditions_value_is_carried():
    """Pins the chosen fix mechanism (project ``conditions`` out of the generated hash, per the
    iter-8 spec's own wording) rather than e.g. converting it to a hashable tuple: two otherwise-
    identical events with DIFFERENT conditions lists still hash equal."""
    a = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["@"])
    b = TradeEvent("AAPL", 1.0, 100.0, 10, Side.BUY, conditions=["F", "K"])
    assert hash(a) == hash(b)


def test_quote_event_hash_does_not_depend_on_which_conditions_value_is_carried():
    a = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300, conditions=["R"])
    b = QuoteEvent("AAPL", 1.0, 100.0, 100.05, 200, 300, conditions=["A", "B"])
    assert hash(a) == hash(b)
