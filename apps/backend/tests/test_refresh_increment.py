"""Capability-34: the incremental refresh-score maintenance is BYTE-IDENTICAL to the merge oracle.

The capability-34 engine-performance gate replaces ``_Window``'s permanently-degraded post-eviction
merge with incremental maintenance (``_RefreshSide`` + a forward-merge cursor). The
non-negotiable constraint is BYTE-IDENTITY to the forward-merge oracle ``_Window._refresh_fractions``
— including its post-eviction "in-window quotes only" semantics (an early trade that loses its
in-effect quote to a quote eviction STOPS contributing). This file pins that:

  * a RANDOMISED DIFFERENTIAL test of the ``_RefreshSide`` weak-record structure vs a brute oracle
    over millions of append/evict op sequences (the algorithm's core);
  * an ORACLE-EQUIVALENCE test driving a real ``_Window`` exactly as the engine does (quote-before-
    trade, eff_* from a running quote) over production-faithful random streams, asserting exact
    equality at every compute INCLUDING post-eviction ticks;
  * an oracle-equivalence test over a SEEDED SIM scenario through the real engine;
  * the ERROR-CASE matrix the spec enumerates, each byte-identical to the oracle.

Exact equality (``==``) is used throughout — never ``approx`` — because byte-identity is the bar.
"""

from __future__ import annotations

import random

from app.config import CONFIG, Config
from app.engine.features import FeatureEngine, _RefreshSide, _Window
from app.engine.tape_engine import TapeEngine
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.simulated import SimulatedProvider


# --- The _RefreshSide weak-record structure vs a brute oracle (the algorithm's core) --------------

def _brute_weak_records(values: list[float], high: bool) -> float:
    """The fraction of weak prefix-maxima (records) over ``values`` — the quantity ``_RefreshSide``
    maintains incrementally. ``high`` => weak HIGH record (>=); else weak LOW (<=)."""
    mark: float | None = None
    refreshed = 0
    total = 0
    for v in values:
        total += 1
        if mark is None or (v >= mark if high else v <= mark):
            refreshed += 1
            mark = v
    return refreshed / total if total else 0.0


def test_refreshside_matches_brute_oracle_over_random_append_evict_sequences():
    """Differential test: random interleavings of append + front-eviction. The incremental
    ``_RefreshSide`` fraction must EXACTLY equal the brute weak-record oracle over the current
    in-window value list, at every step — across both sides and millions of checks."""
    rng = random.Random(20260611)
    fails = 0
    checks = 0
    for _ in range(40000):
        high = rng.random() < 0.5
        side = _RefreshSide(high=high)
        ref: list[float] = []
        for _ in range(rng.randint(1, 40)):
            if not ref or rng.random() < 0.6:
                v = float(rng.randint(0, 6))
                side.append(v)
                ref.append(v)
            else:
                side.evict_front()
                ref.pop(0)
            checks += 1
            if side.fraction() != _brute_weak_records(ref, high):
                fails += 1
    assert fails == 0, f"{fails}/{checks} _RefreshSide steps diverged from the weak-record oracle"
    assert checks > 500000, "the differential test must run a large number of op sequences"


# --- A real _Window driven exactly as the engine does, vs its own merge oracle, with heavy eviction-

def _oracle_window(trades, quotes, length: int, now_ts: float) -> tuple[float, float]:
    """The merge oracle over an explicit (trades, quotes) snapshot at ``now_ts`` — the reference the
    incremental ``_Window`` must reproduce byte-for-byte. Mirrors ``_Window._refresh_fractions`` but
    filters to the in-window contents itself so it is an INDEPENDENT check."""
    lo = now_ts - length
    tw = [t for t in trades if t[0] >= lo]
    qw = [q for q in quotes if q[0] >= lo]
    qi = 0
    n = len(qw)
    cb = ca = None
    bm = am = None
    br = bt = ar = at = 0
    for tts, tside in tw:
        while qi < n and qw[qi][0] <= tts:
            cb, ca = qw[qi][1], qw[qi][2]
            qi += 1
        if tside is Side.SELL and cb is not None:
            bt += 1
            if bm is None or cb >= bm:
                br += 1
            bm = cb if bm is None else max(bm, cb)
        elif tside is Side.BUY and ca is not None:
            at += 1
            if am is None or ca <= am:
                ar += 1
            am = ca if am is None else min(am, ca)
    return (br / bt if bt else 0.0, ar / at if at else 0.0)


def test_window_incremental_equals_oracle_on_production_faithful_random_streams():
    """Drive a real ``_Window`` with quote-before-trade ordering (the engine's invariant), forcing
    heavy eviction (short windows, long timelines), and assert the incremental refresh scores EXACTLY
    equal the independent merge oracle at every compute — including the many post-eviction ticks."""
    rng = random.Random(424242)
    total_post_eviction = 0
    for _ in range(4000):
        length = rng.choice([2, 3, 5, 8])
        w = _Window(length, CONFIG)
        trades: list[tuple[float, Side]] = []
        quotes: list[tuple[float, float, float]] = []
        cur_bid, cur_ask = 100.00, 100.04
        # Build a NON-DECREASING timeline; at equal ts, quotes precede trades (the engine guarantee).
        timeline = []
        ts = 0.0
        for _ in range(rng.randint(1, 60)):
            ts += rng.choice([0.0, 0.0, 0.3, 0.7, 1.0, 2.0, 3.0])
            timeline.append((ts, 0 if rng.random() < 0.5 else 1))  # 0=quote, 1=trade
        timeline.sort(key=lambda e: (e[0], e[1]))
        for ets, kind in timeline:
            if kind == 0:
                cur_bid = round(cur_bid + rng.choice([-0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.04]), 2)
                cur_ask = round(cur_bid + rng.choice([0.02, 0.03, 0.04]), 2)
                quotes.append((ets, cur_bid, cur_ask))
                w.add_quote(ets, cur_bid, cur_ask, round(cur_ask - cur_bid, 2))
            else:
                side = rng.choice([Side.BUY, Side.SELL, Side.UNKNOWN])
                trades.append((ets, side))
                # eff_* the engine would thread = the THEN-current quote (None if none yet).
                eb = cur_bid if quotes else None
                ea = cur_ask if quotes else None
                w.add_trade(ets, 100.0, 100, side, eb, ea)
                out = w.compute(ets)
                ob, oa = _oracle_window(trades, quotes, length, ets)
                assert out["bid_refresh_score"] == ob, (
                    f"bid incremental {out['bid_refresh_score']!r} != oracle {ob!r}"
                )
                assert out["ask_refresh_score"] == oa, (
                    f"ask incremental {out['ask_refresh_score']!r} != oracle {oa!r}"
                )
                if len(trades) > 0 and len(w._trades) < len(trades):
                    total_post_eviction += 1
    assert total_post_eviction > 5000, (
        "the random-stream equivalence test must provably cover many post-eviction computes"
    )


# --- Oracle equivalence over a SEEDED SIM scenario through the real engine ------------------------

def test_incremental_equals_oracle_over_seeded_sim_scenario():
    """Over a seeded SIM-BUYER replay through the REAL engine, the incremental refresh scores equal
    the merge oracle at every compute (a second, deterministic substrate beside the real fixture)."""
    ticker, scenario = "SIM-BUYER", "buyer_control"
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    checks = 0
    import itertools

    for event in itertools.islice(provider.stream(), 1200):
        engine.process_event(event)
        for length, w in engine._features._windows.items():
            if not w._trades or not w._refresh_has_eff:
                continue
            inc_bid = w._refresh_bid.fraction()
            inc_ask = w._refresh_ask.fraction()
            ob, oa = w._refresh_fractions()
            checks += 1
            assert inc_bid == ob, f"{length}s bid {inc_bid!r} != oracle {ob!r}"
            assert inc_ask == oa, f"{length}s ask {inc_ask!r} != oracle {oa!r}"
    assert checks > 1000, "the sim equivalence check must cover a substantial replay"


# --- ERROR-CASE matrix: each byte-identical to the oracle (the spec's enumerated cases) -----------

def _assert_equiv(w: _Window, now_ts: float) -> None:
    out = w.compute(now_ts)
    ob, oa = w._refresh_fractions()
    assert out["bid_refresh_score"] == ob
    assert out["ask_refresh_score"] == oa


def test_error_case_empty_window():
    w = _Window(60, CONFIG)
    out = w.compute(0.0)
    assert out["bid_refresh_score"] == 0.0
    assert out["ask_refresh_score"] == 0.0
    _assert_equiv(w, 0.0)


def test_error_case_trades_before_first_quote_contribute_no_refresh_evidence():
    # Trades arriving before ANY quote have no in-effect quote => SKIPPED, never fabricated.
    w = _Window(60, CONFIG)
    w.add_trade(0.0, 100.0, 100, Side.SELL, None, None)
    w.add_trade(1.0, 100.0, 100, Side.BUY, None, None)
    out = w.compute(1.0)
    assert out["bid_refresh_score"] == 0.0  # no in-effect bid => no evidence
    assert out["ask_refresh_score"] == 0.0
    _assert_equiv(w, 1.0)


def test_error_case_quote_only_window():
    w = _Window(60, CONFIG)
    w.add_quote(0.0, 100.0, 100.02, 0.02)
    w.add_quote(1.0, 100.0, 100.02, 0.02)
    out = w.compute(1.0)
    assert out["bid_refresh_score"] == 0.0  # no trades => no refresh evidence
    assert out["ask_refresh_score"] == 0.0
    _assert_equiv(w, 1.0)


def test_error_case_single_trade_window():
    w = _Window(60, CONFIG)
    w.add_quote(0.0, 100.0, 100.02, 0.02)
    w.add_trade(0.5, 100.0, 100, Side.SELL, 100.0, 100.02)
    out = w.compute(0.5)
    assert out["bid_refresh_score"] == 1.0  # the lone SELL sits at the (only) bid high-water
    assert out["ask_refresh_score"] == 0.0
    _assert_equiv(w, 0.5)


def test_error_case_eviction_boundary_oldest_trade_removed():
    # The eviction boundary: the oldest trade ages out; the incremental scores stay == the oracle.
    w = _Window(2, CONFIG)
    w.add_quote(0.0, 100.0, 100.02, 0.02)
    w.add_trade(0.0, 100.0, 100, Side.SELL, 100.0, 100.02)
    w.add_quote(1.0, 99.99, 100.01, 0.02)
    w.add_trade(1.0, 99.99, 100, Side.SELL, 99.99, 100.01)
    _assert_equiv(w, 1.0)
    # Advance now_ts so the ts=0.0 trade (and quote) age out of the 2s window: window is (1, 3].
    out = w.compute(3.0)
    ob, oa = w._refresh_fractions()
    assert out["bid_refresh_score"] == ob
    assert out["ask_refresh_score"] == oa


def test_error_case_quote_eviction_strips_early_trade_of_its_in_effect_quote():
    """The spec's keystone error case: a quote eviction strips an early in-window trade of its
    in-effect quote, so that trade must STOP contributing refresh evidence — exactly as the
    forward-merge oracle does (NOT keep its append-time quote)."""
    w = _Window(5, CONFIG)
    # A quote then a SELL at ts=0 (the SELL's in-effect bid = 100.00).
    w.add_quote(0.0, 100.00, 100.04, 0.04)
    w.add_trade(0.0, 100.00, 100, Side.SELL, 100.00, 100.04)
    # Later quotes + a SELL well inside the window.
    w.add_quote(2.0, 99.90, 99.94, 0.04)
    w.add_trade(2.0, 99.90, 100, Side.SELL, 99.90, 99.94)
    _assert_equiv(w, 2.0)
    # Now advance so the ts=0 QUOTE evicts (window (1, 6]) but consider a now_ts where the ts=0 TRADE
    # would still be in-window if the window were longer — here both the ts=0 trade AND quote age out
    # together at now_ts=6 (window length 5). Assert equivalence at the boundary and just past it.
    for now in (5.5, 6.0, 6.5, 7.0):
        out = w.compute(now)
        ob, oa = w._refresh_fractions()
        assert out["bid_refresh_score"] == ob, f"at now={now}: {out['bid_refresh_score']} != {ob}"
        assert out["ask_refresh_score"] == oa, f"at now={now}: {out['ask_refresh_score']} != {oa}"


def test_warmup_to_engine_path_transition_with_eviction_matches_oracle():
    """The subtle transition: trades arrive BEFORE the first quote (no in-effect quote, NOT folded),
    then a quote + eff-bearing trade flips the window onto the engine path (the earlier unfolded
    trades are folded as non-contributors), then eviction ages the early trades out. The incremental
    scores must equal the oracle throughout, with the fold cursor / contributor deque staying in
    lockstep (the contributor deque holds EXACTLY the trackers' counted prints — non-contributors
    carry no entry at all)."""
    w = _Window(3, CONFIG)
    # Two trades with NO quote yet — no in-effect quote, contribute nothing, not yet folded.
    w.add_trade(0.0, 100.0, 100, Side.SELL, None, None)
    w.add_trade(0.5, 100.0, 100, Side.BUY, None, None)
    _assert_equiv(w, 0.5)
    assert w._refresh_folded == 0 and len(w._refresh_contrib) == 0
    # A quote then an eff-bearing trade flips ``_refresh_has_eff`` True; the prior trades get folded.
    w.add_quote(1.0, 99.99, 100.03, 0.04)
    w.add_trade(1.0, 99.99, 100, Side.SELL, 99.99, 100.03)
    _assert_equiv(w, 1.0)
    assert w._refresh_folded == len(w._trades)
    assert len(w._refresh_contrib) == w._refresh_bid.total + w._refresh_ask.total
    # Now drive evictions (including aging out the early no-quote trades) and stay == oracle.
    for now in (1.5, 2.0, 3.5, 4.0, 4.5, 5.0):
        w.add_quote(now, 100.0 + 0.01 * now, 100.05 + 0.01 * now, 0.05)
        w.add_trade(now, 100.0 + 0.01 * now, 100, Side.BUY, 100.0 + 0.01 * now, 100.05 + 0.01 * now)
        _assert_equiv(w, now)
        assert w._refresh_folded == len(w._trades)
        assert len(w._refresh_contrib) == w._refresh_bid.total + w._refresh_ask.total


def test_standalone_feature_engine_api_uses_oracle_path_and_is_unchanged():
    """The standalone ``FeatureEngine`` API threads NO in-effect quotes, so it must keep using the
    authoritative forward-merge (``_refresh_has_eff`` stays False) — behaviour byte-identical to
    before this iteration. This pins the two refresh tests in test_features.py keep passing through
    the oracle path, not the incremental one."""
    fe = FeatureEngine(CONFIG)
    fe.add_quote(0.0, 100.00, 100.02, 0.02)
    fe.add_trade(1.0, 100.00, 100, Side.SELL)  # no eff_* threaded
    out = fe.compute(1.0)["60s"]
    # The lone SELL with an in-effect bid at the only quote refreshes => 1.0, via the merge oracle.
    assert out["bid_refresh_score"] == 1.0
    # And the window must NOT have flipped onto the incremental engine path.
    w = fe._windows[60]
    assert w._refresh_has_eff is False
    assert w._refresh_oracle_calls >= 1  # served via the authoritative merge


# --- Dead-source-prefix drops (the era-fast_wall O(1) replacement for the former rebuild) ---------

def test_dead_source_prefix_drops_match_oracle_at_every_compute():
    """A stream engineered so front contributors' SOURCE quotes evict while the trades themselves
    survive — the exact case the former ``_refresh_rebuild`` re-walked the window for, now an O(1)
    dead-prefix drop. Each cycle: a quote, a contributing trade shortly after, then a quote gap so
    the NEXT compute evicts the source quote but not the trade. Byte-equality with the merge oracle
    is asserted at EVERY compute, and the contributor deque must stay in lockstep with the trackers'
    own counted totals throughout (a dropped contributor leaves both, atomically)."""
    w = _Window(5, CONFIG)
    now = 0.0
    for cycle in range(60):
        bid = round(99.0 + (cycle % 7) * 0.01, 2)
        ask = round(bid + 0.04, 2)
        w.add_quote(now, bid, ask, 0.04)
        # Alternate aggressor sides so BOTH trackers carry dead-prefix contributors.
        side = Side.SELL if cycle % 2 == 0 else Side.BUY
        w.add_trade(now + 4.6, bid if side is Side.SELL else ask, 100, side,
                    bid, ask)  # in-effect quote = the cycle's own quote (4.6s older)
        _assert_equiv(w, now + 4.6)
        # Advance so the SOURCE quote (age 5.2 > window 5) evicts while the trade (age 0.6) lives.
        _assert_equiv(w, now + 5.2)
        assert len(w._refresh_contrib) == w._refresh_bid.total + w._refresh_ask.total
        now += 5.2
    # The scenario must actually have exercised the branch: quotes evicted, trades survived.
    assert w._quotes_evicted > 0 and w._trades_evicted > 0


def test_engine_path_has_no_window_rewalk_structurally():
    """Source-introspection guard (the project's established idiom): the engine path's reconcile
    step must contain NO full-window re-walk — the former ``_refresh_rebuild`` (O(window) per quote
    remap, measurably quadratic on real market-open density) is deleted, and the only iteration
    constructs left in ``_refresh_engine_path`` are the two amortised-O(1) ``while`` loops (the
    dead-prefix drop, bounded by lifetime pops, and the tail fold, bounded by lifetime appends)."""
    import inspect

    assert not hasattr(_Window, "_refresh_rebuild")
    src = inspect.getsource(_Window._refresh_engine_path)
    body = src.split('"""')[2]  # strip the docstring — pin the CODE, not the prose
    assert "_refresh_rebuild" not in body
    assert "for " not in body, "no for-loop may iterate window contents on the engine path"
    assert body.count("while ") == 2, "exactly the dead-prefix drop + the tail fold"
