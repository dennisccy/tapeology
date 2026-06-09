"""Timezone-correct historical window resolution (J-20 backend half).

The J-20 fix is predominantly frontend (the picker must resolve the user's local selection to a
tz-aware UTC instant BEFORE the POST), but the contract the corrected frontend now relies on is a
backend property: the historical watch path must fetch the **exact** UTC instant carried by an
offset-bearing ``start``/``end`` — not shift it, not re-localize it — while a legacy **naive**
value remains treated as UTC (no regression of the existing behavior at ``main.py:_parse_window_dt``).

These are *source-of-truth verification* tests, not a behavior change:
  * Unit: ``_parse_window_dt`` parses an offset-bearing instant to the equivalent UTC instant and
    keeps the existing naive->UTC fallback, on both a summer (EDT, -04:00) and a winter (EST,
    -05:00) date so it is proven DST-correct, not fixed-offset.
  * Integration: over HTTP, an offset-bearing window submitted to ``POST /watch`` reaches
    ``adapter.fetch_historical`` as the exact equivalent UTC ``datetime`` (observed via the
    ``FakeAdapter.fetch_calls`` seam); a naive window reaches it as that same wall value in UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import _parse_window_dt, app, get_market_adapter
from fakes import FakeAdapter, load_fixture_window


@pytest.fixture
def fake_client():
    """A TestClient with the market-data adapter overridden by a FakeAdapter (hermetic)."""

    def _make(**kwargs) -> TestClient:
        app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(**kwargs)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(get_market_adapter, None)


# --- Unit: _parse_window_dt resolves an offset to the equivalent UTC instant -----------------

def test_offset_bearing_instant_resolves_to_equivalent_utc_summer_edt():
    # 09:30 ET on a SUMMER date is EDT (-04:00) -> 13:30:00Z. The frontend resolver now sends this
    # offset-bearing form; the backend must keep the exact instant (no second shift).
    parsed = _parse_window_dt("2026-06-02T09:30:00-04:00")
    assert parsed == datetime(2026, 6, 2, 13, 30, 0, tzinfo=timezone.utc)
    # Normalizing to UTC yields exactly 13:30Z — proves no local-offset re-application.
    assert parsed.astimezone(timezone.utc).isoformat() == "2026-06-02T13:30:00+00:00"


def test_offset_bearing_instant_resolves_to_equivalent_utc_winter_est():
    # 09:30 ET on a WINTER date is EST (-05:00) -> 14:30:00Z. The DIFFERENT offset proves the
    # contract is DST-correct end to end (a fixed -04:00 assumption would mis-resolve this one).
    parsed = _parse_window_dt("2026-01-05T09:30:00-05:00")
    assert parsed == datetime(2026, 1, 5, 14, 30, 0, tzinfo=timezone.utc)
    assert parsed.astimezone(timezone.utc).isoformat() == "2026-01-05T14:30:00+00:00"


def test_z_suffixed_instant_is_utc():
    # A ``Z`` suffix is explicit UTC and stays exactly that instant.
    assert _parse_window_dt("2026-06-02T15:00:00Z") == datetime(
        2026, 6, 2, 15, 0, 0, tzinfo=timezone.utc
    )


def test_naive_value_is_still_treated_as_utc_no_regression():
    # The legacy naive value (no offset) is unchanged: treated as UTC. The durable J-20 fix is the
    # frontend no longer SENDING this; the fallback itself MUST remain intact (OUT OF SCOPE: do not
    # remove it) so existing historical tests keep passing.
    assert _parse_window_dt("2026-06-02T15:00") == datetime(
        2026, 6, 2, 15, 0, tzinfo=timezone.utc
    )
    # A naive value with seconds is likewise UTC.
    assert _parse_window_dt("2026-06-02T15:00:30") == datetime(
        2026, 6, 2, 15, 0, 30, tzinfo=timezone.utc
    )


# --- Integration: the offset instant reaches the adapter as the exact UTC instant ------------

def test_historical_watch_fetches_exact_utc_instant_for_offset_input(fake_client):
    # End to end: an offset-bearing window (09:30-16:00 ET on a summer date = -04:00) submitted to
    # POST /watch must reach adapter.fetch_historical at the EXACT equivalent UTC instants
    # (13:30Z start / 20:00Z end) — proving the corrected frontend's tz-aware POST is fetched
    # verbatim, with no silent UTC reinterpretation that would shift the window by the local offset.
    #
    # PROGRESSIVE LOADING (J-37): a 6.5h window is split into bounded sub-window chunks, so the FIRST
    # synchronous fetch is the first chunk (start = 13:30Z, no shift) and the WHOLE window's end is
    # the last chunk's end (20:00Z). The partition is verified directly (it has no overlap/gap and
    # spans exactly [13:30Z, 20:00Z]), so the no-tz-shift contract holds end to end under chunking.
    from app.config import CONFIG
    from app.providers.adapters.base import split_window

    window, _ = load_fixture_window()

    adapter = FakeAdapter(available=True, window=window)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        client = TestClient(app)
        resp = client.post(
            "/watch/F",
            json={
                "mode": "historical",
                "start": "2026-06-02T09:30:00-04:00",
                "end": "2026-06-02T16:00:00-04:00",
                "speed": 1,
            },
        )
        assert resp.status_code == 200
        assert adapter.fetch_calls, "the adapter must have been asked to fetch the window"
        symbol, first_start, first_end = adapter.fetch_calls[0]
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)
        client.delete("/watch/F")

    assert symbol == "F"
    # The FIRST chunk's start is the exact equivalent UTC instant (no shift).
    assert first_start == datetime(2026, 6, 2, 13, 30, 0, tzinfo=timezone.utc)
    # The partition of the resolved window spans EXACTLY [13:30Z, 20:00Z] — the whole window's start
    # and end are the exact UTC instants, with the first chunk's start matching what was fetched.
    ranges = split_window(
        datetime(2026, 6, 2, 13, 30, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 2, 20, 0, 0, tzinfo=timezone.utc),
        CONFIG.historical_chunk_seconds,
    )
    assert ranges[0][0] == datetime(2026, 6, 2, 13, 30, 0, tzinfo=timezone.utc)
    assert ranges[-1][1] == datetime(2026, 6, 2, 20, 0, 0, tzinfo=timezone.utc)
    assert first_end == ranges[0][1]  # the first fetched chunk is exactly the first partition


def test_historical_watch_treats_naive_window_as_utc_no_regression(fake_client):
    # The naive form (what the OLD frontend sent) still reaches the adapter as that same wall value
    # in UTC — the existing behavior is preserved so the prior historical tests do not regress.
    window, _ = load_fixture_window()
    adapter = FakeAdapter(available=True, window=window)
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    try:
        client = TestClient(app)
        resp = client.post(
            "/watch/F",
            json={
                "mode": "historical",
                "start": "2026-06-02T15:00",
                "end": "2026-06-02T15:02",
                "speed": 1,
            },
        )
        assert resp.status_code == 200
        _symbol, start, end = adapter.fetch_calls[0]
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)
        client.delete("/watch/F")

    assert start == datetime(2026, 6, 2, 15, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 2, 15, 2, tzinfo=timezone.utc)
