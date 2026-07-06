"""Generate the committed miniature multi-timeframe bar fixture (era-4 J-01) — ONCE.

Two REAL Alpaca bar series (a small daily window + a small hourly window — at least two DISTINCT
timeframes) are fetched through the SAME vendor-neutral ``fetch_bars`` seam the app uses and
recorded through the REAL ``BarStore.record`` path — never hand-crafted JSON — then committed
under ``tests/fixtures/bars/`` (outside the gitignored ``.data/``). CI then proves
fetch->record->read end-to-end, checksum verification included, with NO credentials
(``tests/test_bars.py``'s committed-fixture test loads this directory directly).

NO-FABRICATION BOUNDARY (the ``capture_alpaca_fixture.py`` precedent, critical): this script only
ever writes bars returned by the REAL vendor. If credentials are absent, it refuses and does
nothing — never synthesizes a fixture to force a green journey.

Run from ``apps/backend``:  ``.venv/bin/python scripts/generate_bar_fixtures.py``

The script REFUSES to run if the fixture directory already holds bar series (the committed pair
is frozen at its one generation — the ``generate_dataset_fixtures.py`` precedent). Delete the
directory first if a regeneration is genuinely intended.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402
from app.providers.adapters import get_adapter  # noqa: E402
from app.research.bars import BarStore  # noqa: E402

FIXTURE_BAR_DIR = BACKEND_DIR / "tests" / "fixtures" / "bars"

SYMBOL = "PG"
# Small REAL windows, well before "now" (never the free-plan's embargoed most-recent bars) and
# reusing the same symbol + calendar neighbourhood as the existing committed PG SIP tick fixtures
# (tests/fixtures/datasets, tests/fixtures/alpaca) for consistency.
WINDOWS: tuple[tuple[str, datetime, datetime], ...] = (
    ("1d", datetime(2026, 6, 1, tzinfo=timezone.utc), datetime(2026, 6, 6, tzinfo=timezone.utc)),
    ("1h", datetime(2026, 6, 9, 13, 0, tzinfo=timezone.utc), datetime(2026, 6, 9, 21, 0, tzinfo=timezone.utc)),
)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def main() -> int:
    load_env()
    adapter = get_adapter()
    if not adapter.is_available():
        print(
            "ERROR: no real-data credentials configured — cannot capture. Do NOT fabricate a "
            "fixture; configure ALPACA_API_KEY/ALPACA_API_SECRET and retry.",
            file=sys.stderr,
        )
        return 2

    store = BarStore(FIXTURE_BAR_DIR)
    existing, errors = store.list()
    if existing or errors:
        print(
            f"REFUSED: {FIXTURE_BAR_DIR} already holds {len(existing)} bar series "
            f"(+{len(errors)} unreadable) — the committed fixture is frozen at its one generation."
        )
        return 1

    for timeframe, start, end in WINDOWS:
        bars = adapter.fetch_bars(SYMBOL, start, end, timeframe)
        if not bars:
            print(
                f"ERROR: no real bars returned for {SYMBOL} {timeframe} "
                f"{start.isoformat()}..{end.isoformat()}.",
                file=sys.stderr,
            )
            return 3
        meta = store.record(
            symbol=SYMBOL,
            timeframe=timeframe,
            window_start_utc=_iso(start),
            window_end_utc=_iso(end),
            feed=adapter.historical_feed,
            bars=list(bars),
        )
        print(
            f"{timeframe:4s} id={meta['id']} {meta['symbol']} {meta['window_start_utc']}"
            f" .. {meta['window_end_utc']} feed={meta['feed']} bar_count={meta['bar_count']}"
            f" checksum={meta['checksum']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
