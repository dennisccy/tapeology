#!/usr/bin/env python3
"""Capture a REAL Alpaca historical window to a committed fixture (operator script).

Run with real Alpaca credentials configured (in ``apps/backend/.env`` or the environment) to
fetch one fixed symbol + past window through the SAME vendor-neutral adapter the app uses and
write the result to a JSON fixture. The fixture is REAL captured market data (committable — it
is neither a secret nor synthesized), so ``test_historical_provider.py`` can re-verify J-11
deterministically and offline.

    cd apps/backend
    .venv/bin/python scripts/capture_alpaca_fixture.py            # default: F, a fixed window
    .venv/bin/python scripts/capture_alpaca_fixture.py --symbol BAC --start 2026-06-02T15:00:00Z \
        --end 2026-06-02T15:02:00Z

NO-FABRICATION BOUNDARY (critical): this script only ever writes data returned by the real
vendor. Never hand-edit or synthesize a fixture to force a green journey — if a real capture is
impossible (no creds / no network / no entitlement), STOP and escalate rather than inventing data.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.env import load_env  # noqa: E402
from app.providers.adapters import get_adapter  # noqa: E402
from app.providers.adapters.base import NoDataForWindow, SymbolNotTradable  # noqa: E402

DEFAULT_SYMBOL = "F"
DEFAULT_START = "2026-06-02T15:00:00Z"
DEFAULT_END = "2026-06-02T15:02:00Z"
FIXTURE_DIR = BACKEND_ROOT / "tests" / "fixtures" / "alpaca"


def _parse(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _slug(value: str) -> str:
    return value.replace("Z", "").replace(":", "").replace("-", "").replace("T", "_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--out", default=None, help="output path (defaults under tests/fixtures/alpaca)")
    args = parser.parse_args()

    load_env()
    adapter = get_adapter()
    if not adapter.is_available():
        print("ERROR: no real-data credentials configured — cannot capture. Do NOT fabricate a "
              "fixture; configure ALPACA_API_KEY/ALPACA_API_SECRET and retry.", file=sys.stderr)
        return 2

    start, end = _parse(args.start), _parse(args.end)
    try:
        window = adapter.fetch_historical(args.symbol, start, end)
    except SymbolNotTradable:
        print(f"ERROR: {args.symbol} is not a tradable symbol.", file=sys.stderr)
        return 3
    except NoDataForWindow:
        print(f"ERROR: no data for {args.symbol} in {args.start}..{args.end}.", file=sys.stderr)
        return 4

    payload = {
        "symbol": window.symbol,
        "start": args.start,
        "end": args.end,
        "feed": getattr(adapter, "feed", "iex"),
        "source": "alpaca",
        "note": "REAL captured market data — not synthesized. See capture_alpaca_fixture.py.",
        "trades": [{"epoch": t.epoch, "price": t.price, "size": t.size} for t in window.trades],
        "quotes": [
            {"epoch": q.epoch, "bid": q.bid, "ask": q.ask, "bid_size": q.bid_size, "ask_size": q.ask_size}
            for q in window.quotes
        ],
    }

    out = Path(args.out) if args.out else FIXTURE_DIR / f"{window.symbol}_{_slug(args.start)}_{_slug(args.end)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=0))
    print(f"wrote {out} — {len(payload['trades'])} trades, {len(payload['quotes'])} quotes "
          f"({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
