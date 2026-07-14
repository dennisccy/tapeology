"""Populate the live bar store with the era-5B J-02 12-symbol panel's OHLC bars (operator script).

Runs the config-owned scan panel (``Config.setups_panel_symbols``) through the EXISTING, keyless
``POST /research/bars`` store-first route (era-5 J-01/J-03 -- no new production code; this script
only DRIVES that route, in-process, for THREE timeframes: ``"1d"`` (a long window), ``"1h"``, and
``"5m"`` (bounded by Yahoo's real ~60-day 5-minute retention, ``Config.setups_5m_fetch_retention_days``)
-- so ``research/setups.py``'s touch-event scanner has real, multi-symbol data to walk (the
"≥15 events across ≥8 panel symbols" DoD headline).

Going through the REAL route (an in-process ``TestClient`` against the real app -- the exact code
path a live HTTP POST would take) rather than calling ``BarStore.record`` directly (the
``generate_bar_fixtures.py`` precedent) matters here: the route ALSO updates the derived
``BarIndex`` on a fresh write, and honours the store-first coordinator (an exact-window repeat run
is served from the index with zero new vendor calls -- never a duplicate fetch).

NO-FABRICATION BOUNDARY (the ``capture_alpaca_fixture.py`` precedent, critical): every bar this
script writes is a REAL Yahoo Finance response that reached ``BarStore.record`` through the real
route. Never hand-crafted, never synthesized. A vendor/network failure for one (symbol, timeframe)
pair is reported honestly and does not fabricate data for it.

Live network, keyless (Yahoo Finance needs no credentials). Writes into the REAL project bar store
(``apps/backend/.data/bars``, or the ``TAPEOLOGY_BAR_DIR`` override if set). Run from
``apps/backend``:

    .venv/bin/python scripts/populate_panel_bars.py
    .venv/bin/python scripts/populate_panel_bars.py --symbols AAPL,MSFT --timeframes 1d,5m
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402

load_env()

from fastapi.testclient import TestClient  # noqa: E402

from app.config import CONFIG  # noqa: E402
from app.main import app  # noqa: E402


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _windows(now: datetime) -> dict[str, tuple[datetime, datetime]]:
    """One fetch window per timeframe, each comfortably inside that timeframe's real Yahoo
    retention (the ``test_yahoo_live_integration.py`` precedent) and long enough to cover the
    era-5B J-02 pinned AAPL 2026-06-22 case plus its forward-return horizons."""
    return {
        "1d": (now - timedelta(days=560), now),
        "1h": (now - timedelta(days=45), now),
        "5m": (now - timedelta(days=CONFIG.setups_5m_fetch_retention_days - 3), now),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--symbols", default=",".join(CONFIG.setups_panel_symbols),
        help="comma-separated symbols (default: the config-owned setups_panel_symbols panel)",
    )
    parser.add_argument("--timeframes", default="1d,1h,5m", help="comma-separated timeframes")
    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    windows = _windows(datetime.now(timezone.utc))
    ok = skipped = failed = 0

    with TestClient(app) as client:
        for symbol in symbols:
            for timeframe in timeframes:
                if timeframe not in windows:
                    print(f"SKIP {symbol:6s} {timeframe:3s}: no configured fetch window")
                    skipped += 1
                    continue
                start, end = windows[timeframe]
                body = {"symbol": symbol, "timeframe": timeframe, "start": _iso(start), "end": _iso(end)}
                response = client.post("/research/bars", json=body)
                if response.status_code == 200:
                    meta = response.json()["bar_series"]
                    print(
                        f"OK   {symbol:6s} {timeframe:3s}: {meta['bar_count']:5d} bars "
                        f"({meta['window_start_utc']} .. {meta['window_end_utc']}, feed={meta['feed']})"
                    )
                    ok += 1
                elif response.status_code == 409:
                    print(f"SKIP {symbol:6s} {timeframe:3s}: already registered")
                    skipped += 1
                else:
                    print(f"FAIL {symbol:6s} {timeframe:3s}: HTTP {response.status_code} {response.json()}")
                    failed += 1

    print(f"\n{ok} recorded, {skipped} already-registered/skipped, {failed} failed")
    return 1 if failed and not (ok or skipped) else 0


if __name__ == "__main__":
    raise SystemExit(main())
