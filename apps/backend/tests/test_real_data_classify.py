"""J-36 GATE — a REAL directional move classifies as control, not perpetual ``unclear``.

THE authoritative, offline, no-credentials gate for J-36 (anti-goal #20: real-data journeys are
proven with REAL data, never a synthetic stand-in). It replays a COMMITTED, REAL captured Alpaca
**SIP** window — GME on 14-05-2024, the first seconds of its >5% open-drop cascade into the LULD
halt (13:30:13–13:30:20 UTC) — through the SAME ``HistoricalProvider`` + ``TapeEngine`` the app
uses, and asserts the drop resolves to ``seller_control`` with confidence ≥ the configured
reasonable threshold and seller markers at the transition.

The fixture is REAL captured market data (``source: alpaca``, ``feed: sip``, self-documented
``note: REAL … not synthesized``) — it carries real epochs + prices + SIP quotes, no key. If it is
ever absent the test FAILS LOUDLY (it does NOT skip and does NOT fall back to a synthetic stand-in),
so a green run is positive evidence the real move classifies correctly.

Why this matters (the iter-13 defect this closes): the old classifier applied ``spread <= cap`` as a
HARD veto on every directional gate, so a real fast-mover whose quoted spread is momentarily wide
(or absent/crossed around a halt) was forced to ``unclear`` through an obvious >5% drop. The J-36 fix
is (a) historical fetch uses the SIP consolidated feed (realistic spreads) and (b) the spread is a
GRADED confidence factor for a clearly-directional move, not an absolute veto. This gate proves the
fix on the real data the defect was reported against.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.historical import HistoricalProvider
from app.serializers import serialize_history
from fakes import load_fixture_window

# The committed REAL GME SIP drop window. A dense ~7-second slice of the open cascade — a
# representative slice (a full 10-minute / Full-RTH SIP capture is too large to commit); see the
# dev handoff for the size/coverage decision.
GME_SIP_FIXTURE = (
    Path(__file__).parent / "fixtures" / "alpaca" / "GME_20240514_133013_133020_sip.json"
)


def _require_real_sip_fixture() -> tuple:
    """Load the committed REAL GME SIP fixture, FAILING LOUDLY if it is absent or not real SIP data.

    Anti-goal #20: J-36 is NOT done until a committed real-data test asserts the outcome. A missing
    or non-real fixture is a hard failure (never a skip, never a synthetic stand-in)."""
    assert GME_SIP_FIXTURE.exists(), (
        f"MISSING REAL FIXTURE {GME_SIP_FIXTURE.name}: the J-36 gate requires a committed REAL "
        "GME SIP capture. Capture it with real credentials via "
        "`scripts/capture_alpaca_fixture.py --symbol GME --start 2024-05-14T13:30:13Z "
        "--end 2024-05-14T13:30:20Z --feed sip`. Do NOT substitute a synthetic fixture."
    )
    window, raw = load_fixture_window(GME_SIP_FIXTURE)
    assert raw["source"] == "alpaca", "fixture must be REAL captured Alpaca data"
    assert raw["feed"] == "sip", "the J-36 fixture must be the SIP consolidated feed (not IEX)"
    assert "REAL" in raw["note"] and window.trades, "fixture must carry real captured trades"
    return window, raw


def _replay(window) -> tuple[TapeEngine, set, str | None]:
    """Replay the real window through the engine, capturing the set of states seen and the
    confidence at the first ``seller_control`` tick (single source of truth — read off the snapshot,
    never recomputed)."""
    provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol}")
    engine = TapeEngine(
        window.symbol, provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor
    )
    states_seen: set[str] = set()
    first_seller_conf: float | None = None
    for event in provider.stream():
        snap = engine.process_event(event)
        states_seen.add(snap.tape_state)
        if snap.tape_state == "seller_control" and first_seller_conf is None:
            first_seller_conf = snap.confidence
    return engine, states_seen, first_seller_conf


def test_real_gme_sip_drop_resolves_to_seller_control():
    # THE J-36 GATE: the committed REAL GME SIP drop replayed through the real engine resolves to
    # seller_control (NOT a perpetual `unclear`) with confidence ≥ reasonable_confidence.
    window, _ = _require_real_sip_fixture()
    engine, states_seen, first_seller_conf = _replay(window)
    snap = engine.snapshot()

    assert "seller_control" in states_seen, (
        "the real GME drop MUST resolve to seller_control at some point — it did NOT, which is the "
        "iter-13 J-36 defect (a real >5% move stuck on unclear)"
    )
    assert snap.tape_state == "seller_control", (
        f"the drop should END in seller_control, got {snap.tape_state!r}"
    )
    assert snap.tape_state != "unclear"
    assert first_seller_conf is not None and first_seller_conf >= CONFIG.reasonable_confidence
    assert snap.confidence >= CONFIG.reasonable_confidence


def test_real_gme_sip_drop_is_a_genuine_directional_move_not_a_quoting_artifact_call():
    # The call is grounded in REAL price impact, not aggression alone: the window is a genuine
    # downward move (the last price is materially below the first) with a strong negative sell
    # impact and a high sell ratio — the price-impact-over-aggression discipline holds on real data.
    window, raw = _require_real_sip_fixture()
    prices = [t.price for t in window.trades]
    move_pct = (prices[-1] - prices[0]) / prices[0] * 100.0
    assert move_pct < -1.0, f"the fixture must be a real DOWNWARD move, got {move_pct:.2f}%"

    engine, _states, _c = _replay(window)
    prim = engine.snapshot().primary_features
    assert prim["aggressive_sell_ratio"] >= CONFIG.min_aggressive_sell_ratio  # real sell dominance
    assert prim["sell_price_impact"] < 0  # real downward progress (impact, not aggression)


def test_real_gme_sip_drop_has_seller_markers_at_the_transition():
    # Seller markers appear at the tape-state transition on the chart (single source of truth — the
    # markers carry the engine's own state, never recomputed), so the user sees the call on the chart.
    window, _ = _require_real_sip_fixture()
    engine, _states, _c = _replay(window)
    hist = serialize_history(
        engine.history, CONFIG.history_bar_sizes[0], epoch_anchor=engine.epoch_anchor
    )
    seller_markers = [m for m in hist["markers"] if m["state"] == "seller_control"]
    assert seller_markers, "the real GME drop must place at least one seller_control chart marker"
    # Each marker carries the engine's own confidence (≥ reasonable, by construction of the gate).
    assert all(m["confidence"] >= CONFIG.reasonable_confidence for m in seller_markers)


def test_real_gme_sip_replay_is_deterministic():
    # Determinism / reproducibility: replaying the SAME real window twice yields the identical tape
    # state, confidence, and per-window features (a pure function of the ordered stream — no
    # wall-clock, no randomness), so the J-36 read is reproducible for a fixed symbol + window.
    window, _ = _require_real_sip_fixture()
    a, _sa, _ca = _replay(window)
    b, _sb, _cb = _replay(window)
    sa, sb = a.snapshot(), b.snapshot()
    assert sa.tape_state == sb.tape_state
    assert sa.confidence == sb.confidence
    assert sa.features == sb.features
    assert sa.event_count == sb.event_count


def test_real_gme_sip_fixture_carries_no_credentials():
    # No-secrets anti-goal: the committed fixture is market data only — it must NOT contain any
    # credential-shaped field (the capture script writes only epochs/prices/quotes + provenance).
    _window, raw = _require_real_sip_fixture()
    for forbidden in ("api_key", "api_secret", "ALPACA_API_KEY", "ALPACA_API_SECRET", "token"):
        assert forbidden not in raw, f"fixture unexpectedly carries {forbidden!r}"
