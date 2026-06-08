"""Canonical display/epoch anchor — Data Contract row 13 (J-31).

The chart's time axis must show TRUE clock time, not elapsed/logical playback seconds. The
engine bins on its deterministic LOGICAL timeline (unchanged), and an ADDITIVE display anchor —
the real UTC epoch that logical-time 0 maps to — is preserved ONCE in the engine/feeder and
exposed read-only through the history projection. The chart maps a logical bin ``start`` to a
true clock instant as ``anchor_epoch + start`` (a pure additive offset — it recomputes no
price/side/state).

These assert:
  * the providers expose the correct ``epoch_anchor`` (historical = the first real record's UTC
    epoch; simulated = a config-owned synthetic session-start; live = None until first event);
  * the engine carries the anchor on its snapshot and surfaces it via the history projection;
  * the anchor is ADDITIVE display metadata only — the SAME ordered event stream still yields
    byte-identical features/state/confidence whether or not an anchor is attached (determinism
    preserved; the anchor never enters classification).
"""

from __future__ import annotations

import itertools

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.historical import HistoricalProvider
from app.providers.simulated import SimulatedProvider
from app.serializers import serialize_history


# --- Providers expose the right anchor ----------------------------------------------------

def test_simulated_provider_anchor_is_config_session_start():
    # The sim anchor is the config-owned synthetic session-start (no inline literal); it is a
    # real UTC epoch (a real clock face), the same for every sim ticker / determinism preserved.
    p = SimulatedProvider("SIM-BUYER", "buyer_control")
    assert p.epoch_anchor == CONFIG.sim_session_anchor_epoch
    p2 = SimulatedProvider("SIM-SELLER", "seller_control")
    assert p2.epoch_anchor == CONFIG.sim_session_anchor_epoch


def test_historical_provider_anchor_is_first_real_record_epoch():
    # The historical anchor is the first real record's UTC epoch — exactly the t0 the provider
    # already subtracts to build its logical timeline (so true_clock = anchor + logical_ts).
    window = HistoricalWindow(
        symbol="F",
        trades=(RawTrade(epoch=1780412400.5, price=12.34, size=100),),
        quotes=(
            RawQuote(epoch=1780412400.0, bid=12.33, ask=12.35, bid_size=10, ask_size=10),
            RawQuote(epoch=1780412405.0, bid=12.34, ask=12.36, bid_size=10, ask_size=10),
        ),
    )
    p = HistoricalProvider("F", window, "historical F window")
    # The earliest of all records (the quote at 1780412400.0) is the window's logical zero.
    assert p.epoch_anchor == 1780412400.0


def test_historical_provider_empty_window_anchor_is_none():
    # An empty window has no first record, so there is no anchor — the chart stays empty and
    # fabricates no timestamps (no-fabricated-data).
    p = HistoricalProvider("F", HistoricalWindow("F", (), ()), "historical F window")
    assert p.epoch_anchor is None


# --- Engine carries the anchor and surfaces it via the history projection -----------------

def _warm_sim_engine(anchor: float | None, n: int = 400) -> TapeEngine:
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG, epoch_anchor=anchor)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


def test_engine_snapshot_carries_epoch_anchor():
    engine = _warm_sim_engine(CONFIG.sim_session_anchor_epoch)
    assert engine.snapshot().epoch_anchor == CONFIG.sim_session_anchor_epoch


def test_engine_defaults_anchor_to_none_for_backward_compatibility():
    # Additive field: an engine built without an anchor (every pre-J-31 construction) reads None.
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    assert engine.snapshot().epoch_anchor is None


def test_history_projection_exposes_anchor():
    anchor = CONFIG.sim_session_anchor_epoch
    engine = _warm_sim_engine(anchor)
    for bar in CONFIG.history_bar_sizes:
        out = serialize_history(engine.history, bar, epoch_anchor=engine.epoch_anchor)
        assert out["epoch_anchor"] == anchor
        # Bars/markers stay LOGICAL (the chart adds the anchor as a pure additive offset) so the
        # single source of truth — the engine's logical buffer — is read verbatim.
        for served, b in zip(out["bars"], engine.history.bars(bar)):
            assert served["time"] == b.start


def test_history_projection_anchor_none_when_unset():
    engine = _warm_sim_engine(None)
    out = serialize_history(engine.history, CONFIG.history_bar_sizes[0], epoch_anchor=None)
    assert out["epoch_anchor"] is None


# --- Determinism: the anchor is additive and does NOT perturb classification --------------

def _run_full_snapshot(anchor: float | None, n: int = 400) -> dict:
    """Run the SAME ordered SIM-BUYER stream and capture every classified value (no anchor field)."""
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG, epoch_anchor=anchor)
    snap = engine.snapshot()
    for event in itertools.islice(provider.stream(), n):
        snap = engine.process_event(event)
    return {
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "features": snap.features,
        "observations": snap.observations,
        "event_log": snap.event_log,
        "timestamp": snap.timestamp,
        "event_count": snap.event_count,
    }


def test_anchor_does_not_change_features_state_or_confidence():
    # The SAME ordered stream classified WITH an anchor and WITHOUT one must be byte-identical in
    # every classified value — the anchor is display metadata, never an input to the engine math.
    with_anchor = _run_full_snapshot(CONFIG.sim_session_anchor_epoch)
    without_anchor = _run_full_snapshot(None)
    assert with_anchor == without_anchor
    # And the directional read still lands (sanity: the stream genuinely classifies, not all-unclear).
    assert with_anchor["tape_state"] == "buyer_control"
    assert with_anchor["confidence"] >= CONFIG.reasonable_confidence
