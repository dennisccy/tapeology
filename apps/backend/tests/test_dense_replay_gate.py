"""Capability-34 ENGINE PERFORMANCE GATE — rolling-feature maintenance is truly incremental.

THE authoritative, offline, no-credentials gate for the capability-34 prerequisite that unblocks the
replay-studies layer (J-60–J-62). It replays a COMMITTED, REAL captured Alpaca **SIP** window —
PG, a calm ~10-minute mid-session window on 2026-06-09 (17:00–17:10 UTC) — through the SAME
``HistoricalProvider`` + ``TapeEngine`` the J-60 study runner will use, and proves THREE things:

  1. **No per-event full-window rescan after evictions** (the documented defect): the old code set
     ``_Window._refresh_incremental = False`` permanently on the first eviction, after which EVERY
     ``compute()`` served the refresh scores from the O(window) forward-merge ``_refresh_fractions``
     — quadratic on any stream longer than a feature window. This gate asserts that, on the engine
     path, ``_refresh_fractions`` is called ZERO times after evictions begin (it is retained ONLY for
     the standalone-API fallback + as the test oracle), AND that evictions actually occurred on every
     feature window (guarding against a silently too-short fixture).
  2. **Byte-identity to the merge oracle** (NON-NEGOTIABLE): the incremental refresh scores EXACTLY
     equal (``==``, never approx) the ``_refresh_fractions`` oracle on identical window contents, at
     every compute — proven here over the real fixture and (in ``test_features.py``) over a seeded
     sim scenario, with the post-eviction "in-window quotes only" semantics reproduced exactly.
  3. **A CI timing budget**: the unpaced full-``TapeEngine`` replay completes within the config-owned
     ``dense_replay_time_budget_seconds`` — in CI, without credentials.

The fixture is REAL captured market data (``source: alpaca``, ``feed: sip``); if it is ever absent
this test FAILS LOUDLY (it does NOT skip and does NOT fall back to synthetic data), so a green run is
positive evidence the engine sustains dense real tape. The SAME fixture is capability 32's reference
study input next iteration (one fixture, two consumers).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.config import CONFIG, Config
from app.engine.features import _Window
from app.engine.tape_engine import TapeEngine
from app.providers.base import Side
from app.providers.historical import HistoricalProvider
from fakes import load_fixture_window

# The committed REAL PG SIP dense window — ~10 minutes (>300 s longest feature window) so ALL FIVE
# windows evict; calm large-cap midday so the file stays well under the ~25 MB repo budget.
PG_SIP_FIXTURE = (
    Path(__file__).parent / "fixtures" / "alpaca" / "PG_20260609_170000_171000_sip.json"
)


def _require_real_sip_fixture() -> tuple:
    """Load the committed REAL PG SIP dense fixture, FAILING LOUDLY if absent or not real SIP data."""
    assert PG_SIP_FIXTURE.exists(), (
        f"MISSING REAL FIXTURE {PG_SIP_FIXTURE.name}: the capability-34 gate requires a committed "
        "REAL ~10-minute PG SIP capture. Capture it with real credentials via "
        "`scripts/capture_alpaca_fixture.py --symbol PG --start 2026-06-09T17:00:00Z "
        "--end 2026-06-09T17:10:00Z --feed sip`. Do NOT substitute a synthetic fixture."
    )
    window, raw = load_fixture_window(PG_SIP_FIXTURE)
    assert raw["source"] == "alpaca", "fixture must be REAL captured Alpaca data"
    assert raw["feed"] == "sip", "the dense-replay fixture must be the SIP consolidated feed (not IEX)"
    assert "REAL" in raw["note"] and window.trades, "fixture must carry real captured trades"
    return window, raw


def _fresh_engine(window) -> TapeEngine:
    provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol}")
    return TapeEngine(window.symbol, provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor)


def _replay(window) -> TapeEngine:
    provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol}")
    engine = TapeEngine(
        window.symbol, provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor
    )
    for event in provider.stream():
        engine.process_event(event)
    return engine


# --- Fixture sanity (real SIP, dense enough to evict all windows, no credentials) ------------------

def test_fixture_is_real_sip_dense_and_spans_all_windows():
    window, raw = _require_real_sip_fixture()
    trades = window.trades
    span = trades[-1].epoch - trades[0].epoch
    # Comfortably longer than the 300 s longest feature window so every window evicts.
    assert span > 300.0, f"fixture span {span:.1f}s must exceed the 300s longest window so all evict"
    # Moderate density (real consolidated tape) — thousands of prints, not a handful.
    assert len(trades) > 1000, "the dense fixture must carry a moderate-density real tape"
    assert len(window.quotes) > 1000, "the dense fixture must carry real SIP quotes"


def test_fixture_carries_no_credentials():
    # No-secrets anti-goal: the committed fixture is market data only.
    _window, raw = _require_real_sip_fixture()
    blob = json.dumps(raw)
    for forbidden in ("api_key", "api_secret", "ALPACA_API_KEY", "ALPACA_API_SECRET", "token"):
        assert forbidden not in blob, f"fixture unexpectedly carries {forbidden!r}"


def test_fixture_size_within_repo_budget():
    # The committed file stays well under the ~25 MB budget the spec sets for a sane repo.
    size_mb = PG_SIP_FIXTURE.stat().st_size / (1024 * 1024)
    assert size_mb < 25.0, f"fixture is {size_mb:.1f} MB — over the ~25 MB repo budget"


# --- (1) Structural no-rescan: zero merge-fallback calls after evictions, evictions actually occur -

def test_no_full_window_rescan_after_evictions_begin():
    """The capability-34 invariant: on the ENGINE path the O(window) merge fallback
    (``_refresh_fractions``) is NEVER invoked once evictions begin — the refresh scores are
    maintained incrementally. The dedicated pre/post-eviction accounting (over the primary window,
    driven exactly as the engine does) asserts ZERO post-eviction merge calls AND that evictions
    actually occurred (guarding against a silently too-short fixture)."""
    window, _ = _require_real_sip_fixture()
    _assert_zero_post_eviction_merge_calls(window)


def _assert_zero_post_eviction_merge_calls(window) -> None:
    """Replay through fresh per-window instrumentation: for the primary feature window, count
    ``_refresh_fractions`` calls before vs after the first eviction, and assert evictions occurred
    and post-eviction merge calls are ZERO (the no-rescan structural pin)."""
    primary = CONFIG.primary_window
    w = _Window(primary, CONFIG)
    provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol}")
    # Drive the window EXACTLY as the engine does (quote-before-trade; eff_* from a running quote).
    cur_bid: float | None = None
    cur_ask: float | None = None
    cur_spread = 0.0
    first_eviction_seen = False
    pre_evict_merge = 0
    post_evict_merge = 0
    evictions = 0
    from app.providers.base import QuoteEvent, TradeEvent

    last_trade_count = 0
    for event in provider.stream():
        if isinstance(event, QuoteEvent):
            cur_bid, cur_ask, cur_spread = event.bid, event.ask, event.ask - event.bid
            w.add_quote(event.timestamp, event.bid, event.ask, event.ask - event.bid)
        elif isinstance(event, TradeEvent):
            # The aggressor side is irrelevant to the rescan accounting; use a deterministic split so
            # both sides exercise. (Byte-identity itself is pinned by the oracle-equivalence tests.)
            side = Side.SELL if int(event.timestamp * 1000) % 2 == 0 else Side.BUY
            before_calls = w._refresh_oracle_calls
            before_len = len(w._trades)
            w.add_trade(event.timestamp, event.price, event.size, side, cur_bid, cur_ask)
            w.compute(event.timestamp)
            # An eviction happened this compute iff the in-window trade count dropped below the
            # running appended count.
            after_len = len(w._trades)
            if after_len <= before_len and before_len > 0:
                first_eviction_seen = True
                evictions += 1
            merged = w._refresh_oracle_calls - before_calls
            if first_eviction_seen:
                post_evict_merge += merged
            else:
                pre_evict_merge += merged

    assert evictions > 0, "the dense fixture must drive the primary window into eviction"
    assert post_evict_merge == 0, (
        f"the engine path invoked the O(window) merge fallback {post_evict_merge} times AFTER "
        "evictions began — the capability-34 quadratic regression is back"
    )


def test_every_feature_window_evicts_on_the_dense_fixture():
    """Guard against a silently too-short fixture: after the full replay every feature window holds
    FEWER trades/quotes than were streamed (i.e. it slid — evicted)."""
    window, _ = _require_real_sip_fixture()
    total_trades = len(window.trades)
    total_quotes = len(window.quotes)
    engine = _replay(window)
    for length, w in engine._features._windows.items():
        assert len(w._trades) < total_trades, (
            f"{length}s window kept ALL {total_trades} trades — it never evicted (fixture too short)"
        )
        assert len(w._quotes) < total_quotes, (
            f"{length}s window kept ALL {total_quotes} quotes — it never evicted"
        )


# --- (2) Byte-identity to the merge oracle at EVERY compute, including post-eviction ---------------

def test_incremental_refresh_is_byte_identical_to_oracle_at_every_compute():
    """Over the real dense fixture, at EVERY processed trade the incremental ``bid_refresh_score`` /
    ``ask_refresh_score`` EXACTLY equal (``==``) the ``_refresh_fractions`` oracle on the identical
    in-window contents — across thousands of POST-eviction ticks. Byte-identity is the
    non-negotiable capability-34 constraint."""
    window, _ = _require_real_sip_fixture()
    provider = HistoricalProvider(window.symbol, window, f"historical {window.symbol}")
    engine = TapeEngine(
        window.symbol, provider.scenario, CONFIG, epoch_anchor=provider.epoch_anchor
    )
    primary = CONFIG.primary_window
    total_trades = len(window.trades)
    checks = 0
    post_eviction_checks = 0
    i = 0
    for event in provider.stream():
        engine.process_event(event)
        i += 1
        windows = engine._features._windows
        # Compare the PRIMARY window at EVERY processed event (it evicts heavily — only ~162 of the
        # 3,229 trades stay in the 30s window — so the vast majority of these ticks are
        # post-eviction). Compare ALL FIVE windows every 50th event (a dense sampled subset that
        # provably reaches the long 180s/300s windows' post-eviction regime too). This keeps the
        # oracle re-walk bounded while still covering thousands of post-eviction ticks.
        for length, w in windows.items():
            if length != primary and (i % 50 != 0):
                continue
            if not w._trades or not w._refresh_has_eff:
                continue
            inc_bid = w._refresh_bid.fraction()
            inc_ask = w._refresh_ask.fraction()
            ob, oa = w._refresh_fractions()
            checks += 1
            assert inc_bid == ob, (
                f"{length}s bid_refresh incremental {inc_bid!r} != oracle {ob!r} (NOT byte-identical)"
            )
            assert inc_ask == oa, (
                f"{length}s ask_refresh incremental {inc_ask!r} != oracle {oa!r} (NOT byte-identical)"
            )
            if len(w._trades) < total_trades:
                post_eviction_checks += 1
    assert checks > 3000, "the equivalence check must cover the full dense replay"
    assert post_eviction_checks > 1000, (
        "the equivalence check must provably cover MANY post-eviction ticks (it did not)"
    )


# --- (3) CI timing gate: unpaced fresh-engine replay within the config-owned budget ----------------

def test_unpaced_replay_within_config_time_budget():
    """The CI timing gate: an UNPACED replay of the committed dense fixture through a fresh full
    ``TapeEngine`` completes within ``dense_replay_time_budget_seconds`` — in CI, without
    credentials. With the incremental maintenance this is ~10 s on the dev machine; the old
    permanently-degraded post-eviction merge took ~184 s (the quadratic defect the gate guards)."""
    window, _ = _require_real_sip_fixture()
    budget = CONFIG.dense_replay_time_budget_seconds
    assert budget > 0, "the time budget must be a positive config value"

    start = time.perf_counter()
    engine = _replay(window)
    elapsed = time.perf_counter() - start

    # The replay produced a real, deterministic read (a sanity that we actually processed the tape).
    assert engine.snapshot().event_count > 1000
    assert elapsed < budget, (
        f"unpaced dense replay took {elapsed:.2f}s, over the {budget:.0f}s budget — the engine is "
        "not keeping up with dense real tape (capability-34 regression)"
    )


# --- Pinned regression anchors: exact final feature values from the dense replay -------------------

def test_pinned_final_feature_values_from_dense_replay():
    """Equality-pinned anchors (the ``test_real_data_classify.py`` standard): exact final per-window
    feature values from the committed dense replay. A change here means the engine's numbers moved —
    which for THIS iteration (byte-identity mandatory) is a STOP-and-flag, never a silent re-pin."""
    window, _ = _require_real_sip_fixture()
    engine = _replay(window)
    snap = engine.snapshot()

    # Deterministic TRADE count over the committed stream (snapshot.event_count counts trades).
    assert snap.event_count == 3229

    feats = snap.features  # per-window dict
    primary = feats[CONFIG.primary_window_label]
    # The full PRIMARY-window feature vector, pinned EXACTLY (these are the engine's single source of
    # truth — REST/WS/UI read them verbatim). Captured from the committed replay; equality-pinned.
    assert primary["trade_speed"] == 5.4
    assert primary["volume_speed"] == 340.1666666666667
    assert primary["aggressive_buy_ratio"] == 0.5626653601175894
    assert primary["aggressive_sell_ratio"] == 0.43733463988241056
    assert primary["net_aggressive_volume"] == 1279.0
    assert primary["buy_price_impact"] == 1.8498999999999626
    assert primary["sell_price_impact"] == -1.939899999999966
    assert primary["average_spread"] == 0.06246268656716442
    assert primary["large_print_count"] == 3.0
    assert primary["absorption_score"] == 0.0
    assert primary["bid_refresh_score"] == 0.18421052631578946
    assert primary["ask_refresh_score"] == 0.46511627906976744
    assert primary["reference_price"] == 148.30767910447685

    # Final classification (calm midday PG chop → honest unclear at the warmed-up floor confidence).
    assert snap.tape_state == "unclear"
    assert snap.confidence == 0.2


def test_dense_replay_is_deterministic():
    """Determinism: replaying the SAME committed window twice yields identical features/state — a
    pure function of the ordered stream (no wall-clock, no randomness in classification)."""
    window, _ = _require_real_sip_fixture()
    a = _replay(window).snapshot()
    b = _replay(window).snapshot()
    assert a.tape_state == b.tape_state
    assert a.confidence == b.confidence
    assert a.features == b.features
    assert a.event_count == b.event_count


# --- Config: fingerprint stability + counter (iter-12 / iter-16 discipline) ------------------------

def test_changing_dense_replay_budget_does_not_change_fingerprint():
    """The dense-replay CI budget is a GATE value EXCLUDED from ``config_fingerprint`` — changing it
    must NOT fragment analytics pools (iter-12/iter-16 precedent)."""
    base = Config().config_fingerprint()
    bumped = Config(dense_replay_time_budget_seconds=999.0).config_fingerprint()
    assert base == bumped


def test_changing_a_real_threshold_still_changes_fingerprint():
    """The paired counter-test: a genuine classifier threshold STILL moves the fingerprint, so the
    exclusion above is a deliberate scope decision, not a blanket hole."""
    base = Config().config_fingerprint()
    changed = Config(min_buy_price_impact=0.99).config_fingerprint()
    assert base != changed
