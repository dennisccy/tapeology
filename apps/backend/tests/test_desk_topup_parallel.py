"""The top-up walk overlaps vendor round-trips without changing what it records.

A pair costs one vendor round-trip; the walk's own bookkeeping is memoized reads. Walking 606 pairs
strictly one at a time therefore spent almost all of its wall-clock waiting on a socket — measured
~640s for a fully-fetching run. ``run_topup`` now keeps up to
``TAPEOLOGY_DESK_TOPUP_FETCH_WORKERS`` pairs in flight.

The contract that must not move: ``outcomes`` is the SAME list, in the SAME pair order, with the
same per-pair provenance, and ``progress`` is called once per pair in that same order. This file
pins that against a deterministic fake vendor — including the two places overlap could go wrong
(a cancelled run, and a vendor that starts rate-limiting)."""

from __future__ import annotations

import threading
import time

import pytest

from app.research import desk_topup_compute
from app.research.desk_topup_compute import TOPUP_WALK_TIMEFRAMES, run_topup

MEMBERS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]


class _FakeStore:
    """A ``BarStore`` stand-in for ``_pair_window``: every pair holds nothing, so the walk takes the
    byte-identical ``full_lookback`` branch for all of them."""

    def merged_bars(self, symbol: str, timeframe: str) -> list:
        return []


def _pairs() -> list[tuple[str, str]]:
    return [(s, tf) for s in MEMBERS for tf in TOPUP_WALK_TIMEFRAMES]


def _walk(monkeypatch, workers: str | None, one_pair, should_abort=None) -> tuple[list[dict], list[dict]]:
    if workers is None:
        monkeypatch.delenv(desk_topup_compute._TOPUP_FETCH_WORKERS_ENV, raising=False)
    else:
        monkeypatch.setenv(desk_topup_compute._TOPUP_FETCH_WORKERS_ENV, workers)
    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", one_pair)
    seen: list[dict] = []
    outcomes = run_topup(
        MEMBERS, _FakeStore(), object(), object(),
        progress=seen.append, should_abort=should_abort,
    )
    return outcomes, seen


def test_the_overlapped_walk_records_exactly_what_the_serial_walk_records(monkeypatch) -> None:
    """The load-bearing equivalence: same entries, same order, whether one pair is in flight or
    four. The fake returns a per-pair distinguishable detail so a reordering cannot hide."""

    def one_pair(symbol, timeframe, *_args):
        return "fetched", f"{symbol}/{timeframe}"

    serial, serial_progress = _walk(monkeypatch, "1", one_pair)
    parallel, parallel_progress = _walk(monkeypatch, "4", one_pair)

    assert parallel == serial
    assert parallel_progress == serial_progress == serial
    assert [(o["symbol"], o["timeframe"]) for o in serial] == _pairs()


def test_order_holds_when_pairs_finish_out_of_order(monkeypatch) -> None:
    """Overlap means a later pair routinely finishes first. The consumer must still emit in pair
    order — so the walk sleeps longest on the FIRST pair, the worst case for an "as it completes"
    implementation."""
    order = {pair: i for i, pair in enumerate(_pairs())}

    def one_pair(symbol, timeframe, *_args):
        # Earlier pairs take strictly longer, so completion order is the reverse of pair order.
        time.sleep(0.02 * max(0, 4 - order[(symbol, timeframe)]))
        return "fetched", f"{symbol}/{timeframe}"

    outcomes, progress = _walk(monkeypatch, "4", one_pair)
    assert [(o["symbol"], o["timeframe"]) for o in outcomes] == _pairs()
    assert progress == outcomes


def test_pairs_really_do_overlap(monkeypatch) -> None:
    """Without this, every other test here would still pass over a silently serial walk."""
    peak = 0
    live = 0
    lock = threading.Lock()

    def one_pair(symbol, timeframe, *_args):
        nonlocal peak, live
        with lock:
            live += 1
            peak = max(peak, live)
        time.sleep(0.02)
        with lock:
            live -= 1
        return "fetched", None

    _walk(monkeypatch, "4", one_pair)
    assert peak > 1, "the walk never had two pairs in flight"
    assert peak <= 4


def test_a_cancelled_run_stops_dispatching_and_keeps_its_prefix(monkeypatch) -> None:
    """A cancelled walk returns a SHORT list whose entries are still the first pairs in order.
    Pairs already dispatched are allowed to finish (they HAVE started), so the cut is bounded by the
    in-flight window rather than exact — what must hold is short, ordered, and prefix-shaped."""
    done = 0
    lock = threading.Lock()

    def one_pair(symbol, timeframe, *_args):
        nonlocal done
        with lock:
            done += 1
        return "fetched", None

    def should_abort() -> bool:
        with lock:
            return done >= 5

    outcomes, progress = _walk(monkeypatch, "4", one_pair, should_abort=should_abort)
    assert 0 < len(outcomes) < len(_pairs())
    assert [(o["symbol"], o["timeframe"]) for o in outcomes] == _pairs()[: len(outcomes)]
    assert progress == outcomes


def test_aborting_before_the_first_pair_walks_nothing(monkeypatch) -> None:
    outcomes, progress = _walk(monkeypatch, "4", lambda *a: ("fetched", None), should_abort=lambda: True)
    assert outcomes == [] and progress == []


def test_a_rate_limited_vendor_narrows_the_walk_to_one_pair_in_flight(monkeypatch) -> None:
    """A vendor answering "too many requests" is telling the walk it is too wide. The remainder is
    walked one at a time — never a raise, and the offending pair keeps its honest failed outcome.

    Concurrency is measured only over pairs dispatched WELL AFTER the limit was reported: pairs
    already in flight when it lands are allowed to finish (narrowing applies to what is dispatched
    next, not to work already sent), so the pairs immediately following it legitimately overlap."""
    order = {pair: i for i, pair in enumerate(_pairs())}
    settled_from = 8  # comfortably past the in-flight window open when the limit was reported
    peak_after = 0
    live = 0
    lock = threading.Lock()

    def one_pair(symbol, timeframe, *_args):
        nonlocal peak_after, live
        index = order[(symbol, timeframe)]
        with lock:
            live += 1
            if index >= settled_from:
                peak_after = max(peak_after, live)
        time.sleep(0.02)
        with lock:
            live -= 1
        if index == 1:
            return "failed", "429 Too Many Requests. Rate limited. Try after a while."
        return "fetched", None

    outcomes, _progress = _walk(monkeypatch, "4", one_pair)
    assert len(outcomes) == len(_pairs())  # the walk still completes every pair
    assert outcomes[1]["outcome"] == "failed"
    assert "Rate limited" in outcomes[1]["detail"]
    assert peak_after == 1, "the walk kept overlapping pairs after the vendor said it was too wide"


def test_an_error_escaping_a_pair_still_fails_the_whole_walk(monkeypatch) -> None:
    """``_run_one_pair`` swallows vendor errors itself; anything that escapes it (a corrupt store
    surfacing through ``_pair_window``) must still abort the run rather than be silently dropped by
    a worker thread."""

    def one_pair(symbol, timeframe, *_args):
        if (symbol, timeframe) == _pairs()[3]:
            raise RuntimeError("store went away")
        return "fetched", None

    with pytest.raises(RuntimeError, match="store went away"):
        _walk(monkeypatch, "4", one_pair)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 4), ("", 4), ("1", 1), ("6", 6), ("0", 1), ("-3", 1), ("99", 8), ("banana", 4), (" 2 ", 2)],
)
def test_the_worker_knob_is_clamped_and_never_fails_a_run(monkeypatch, raw, expected) -> None:
    if raw is None:
        monkeypatch.delenv(desk_topup_compute._TOPUP_FETCH_WORKERS_ENV, raising=False)
    else:
        monkeypatch.setenv(desk_topup_compute._TOPUP_FETCH_WORKERS_ENV, raw)
    assert desk_topup_compute._topup_fetch_workers() == expected


def test_the_manager_still_resolves_cancelled_at_the_default_width(tmp_path, monkeypatch) -> None:
    """The manager's own cancellation contract, exercised at the DEFAULT worker count rather than
    the width-1 walk ``test_desk_topup_compute.py`` pins the exact counts against: state resolves
    ``"cancelled"``, the outcome list is a short ordered prefix, and nothing is fabricated for the
    pairs never walked."""
    from app.research.desk_topup_compute import DeskTopupComputeManager
    from app.research.desk_topup_log import TopupRunStore
    from app.research.desk_universe import UniverseStore

    monkeypatch.delenv(desk_topup_compute._TOPUP_FETCH_WORKERS_ENV, raising=False)
    universe_store = UniverseStore(tmp_path / "universe")
    universe_store.record(
        members=MEMBERS, raw_members={m: m for m in MEMBERS},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )

    seen = threading.Event()
    release = threading.Event()

    def one_pair(symbol, timeframe, *_args):
        seen.set()
        release.wait(timeout=5)
        return "fetched", None

    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", one_pair)
    monkeypatch.setattr(desk_topup_compute, "_pair_window", lambda *a: {
        "requested_window": {"start": "2025-01-01T00:00:00Z", "end": "2025-01-02T00:00:00Z"},
        "store_frozen_from": None, "store_frozen_through": None, "window_basis": "full_lookback",
    })

    mgr = DeskTopupComputeManager()
    mgr.trigger(
        universe_store, _FakeStore(), object(), object(),
        topup_run_store=TopupRunStore(tmp_path / "topup_runs"),
    )
    assert seen.wait(timeout=5)
    mgr.cancel()
    release.set()

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and mgr.snapshot()["state"] == "running":
        time.sleep(0.02)
    snapshot = mgr.snapshot()
    mgr.join_all(timeout=10)

    assert snapshot["state"] == "cancelled"
    assert snapshot["error"] is None
    outcomes = snapshot["progress"]["outcomes"]
    assert 0 < len(outcomes) < len(_pairs())
    assert [(o["symbol"], o["timeframe"]) for o in outcomes] == _pairs()[: len(outcomes)]
