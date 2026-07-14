"""Event-window tape recording driver (era-5B capability 3, J-03) -- the operator/integration
script that selects top-ranked band-touch events from ``GET /research/setups`` and records each
event's window (config-owned padding) into a registered ``DatasetStore`` dataset, via the
EXISTING ``POST /research/datasets`` route (``source_kind="historical"``) -- the SAME seam era-3's
studies runner already uses, driven in-process through a real ``TestClient`` against the real app
(the ``scripts/populate_panel_bars.py`` precedent: no new production HTTP path).

Selection (config-owned, deterministic, pre-registered -- no post-hoc tuning to manufacture
survivors): the PINNED AAPL 2026-06-22 ~300 event is ALWAYS included when present in the scan;
remaining events are then picked ONE-BEST-PER-SYMBOL-FIRST (by descending band ``quality_score``,
walked in the config-owned panel order) to maximise SYMBOL SPREAD -- goal.md's ">= 5 symbols"
headline -- before any leftover ``Config.recording_event_selection_cap`` budget fills with the
next-best events overall.

Each selected event's window is ``touch_ts`` +/- the config-owned padding
(``Config.recording_pre_touch_minutes`` / ``recording_post_touch_minutes``), and its split tag is
assigned by a NEW config-owned deterministic rule (``Config.recording_holdout_fraction`` -- see
``config.py``'s own field docstring for the full rationale: a pure sha256 digest of the event's
own stable id, no wall-clock, no unseeded randomness).

CREDENTIALS. When Alpaca credentials are absent, ``POST /research/datasets``'s EXISTING
historical-record validation returns an explicit 422 "unavailable" -- this script counts and
reports that as BLOCKED (never fixture-substituted, never silently retried as something else),
mirroring ``populate_panel_bars.py``'s own OK/SKIP/FAIL counter discipline. Recording is explicit
and logged -- this script is the ONE place that act happens; nothing here is ambient or scheduled.

Live network (when credentialed), keyless to SCAN (``GET /research/setups`` reads only already-
stored bars). Writes into the REAL project dataset store (``apps/backend/.data/datasets``, or the
``TAPEOLOGY_DATASET_DIR`` override if set). Run from ``apps/backend``:

    .venv/bin/python scripts/record_event_windows.py
    .venv/bin/python scripts/record_event_windows.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402

load_env()

from fastapi.testclient import TestClient  # noqa: E402

from app.config import CONFIG, Config  # noqa: E402
from app.main import app  # noqa: E402
from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN  # noqa: E402
from app.research.tradability import RESISTANCE  # noqa: E402

# The pinned AAPL 2026-06-22 ~300 test (goal.md's ground-truth case) -- the SAME band-containment
# check tests/test_setups.py's own pinned-event lookup uses. ALWAYS selected when present.
_PINNED_SYMBOL = "AAPL"
_PINNED_SESSION_DATE = "2026-06-22"
_PINNED_PRICE_LOW_MAX = 300.48
_PINNED_PRICE_HIGH_MIN = 302.07


def _is_pinned_event(event: dict) -> bool:
    return (
        event["symbol"] == _PINNED_SYMBOL
        and event["session_date"] == _PINNED_SESSION_DATE
        and event["band"]["side"] == RESISTANCE
        and event["band"]["price_low"] <= _PINNED_PRICE_LOW_MAX
        and event["band"]["price_high"] >= _PINNED_PRICE_HIGH_MIN
    )


def _rank_key(event: dict) -> tuple:
    """Descending band ``quality_score``, tie-broken by the event's own stable id -- deterministic,
    never insertion-order happenstance (``tradability.py``'s own ``_rank_sort_key`` idiom, reused
    as a technique for a different collection)."""
    return (-event["band"]["quality_score"], event["id"])


def select_recording_events(events: list[dict], config: Config) -> list[dict]:
    """Select at most ``config.recording_event_selection_cap`` events to record: the pinned AAPL
    2026-06-22 event ALWAYS first (when present), then one best-quality event per DISTINCT symbol
    (config-owned panel order) to maximise symbol spread, then the next-best remaining events
    overall fill any leftover cap budget. Pure + deterministic: an identical ``events`` input
    always yields the identical selection."""
    cap = config.recording_event_selection_cap
    selected: list[dict] = [e for e in events if _is_pinned_event(e)]
    selected_ids = {e["id"] for e in selected}

    by_symbol: dict[str, list[dict]] = {}
    for e in events:
        if e["id"] in selected_ids:
            continue
        by_symbol.setdefault(e["symbol"], []).append(e)
    for candidates in by_symbol.values():
        candidates.sort(key=_rank_key)

    # Pass 1: one best event per distinct symbol, in config-owned panel order (symbol spread).
    for symbol in config.setups_panel_symbols:
        if len(selected) >= cap:
            break
        candidates = by_symbol.get(symbol) or []
        if candidates:
            best = candidates[0]
            selected.append(best)
            selected_ids.add(best["id"])

    # Pass 2: fill any remaining cap budget with the next-best events overall.
    remaining = sorted((e for e in events if e["id"] not in selected_ids), key=_rank_key)
    for e in remaining:
        if len(selected) >= cap:
            break
        selected.append(e)
        selected_ids.add(e["id"])

    return selected


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def event_window(event: dict, config: Config) -> tuple[str, str]:
    """The event's recording window (``touch_ts`` -/+ the config-owned padding), as ISO-8601 UTC
    strings the ``/research/datasets`` route accepts verbatim."""
    touch = datetime.fromisoformat(event["touch_ts"].replace("Z", "+00:00"))
    start = touch - timedelta(minutes=config.recording_pre_touch_minutes)
    end = touch + timedelta(minutes=config.recording_post_touch_minutes)
    return _iso(start), _iso(end)


def split_for_event(event_id: str, config: Config) -> str:
    """Deterministic train/holdout split assignment (``config.py``'s own
    ``recording_holdout_fraction`` docstring has the full rationale): a pure sha256 digest of the
    event's OWN stable id, mapped into ``[0, 1)`` and compared against the config-owned holdout
    fraction. No wall-clock, no unseeded randomness -- an identical event id always resolves to the
    identical split, every run."""
    digest = hashlib.sha256(f"recording-split|{event_id}".encode("utf-8")).hexdigest()
    fraction = int(digest[:8], 16) / 0xFFFFFFFF
    return SPLIT_HOLDOUT if fraction < config.recording_holdout_fraction else SPLIT_TRAIN


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the selected events + windows without recording anything",
    )
    args = parser.parse_args()

    with TestClient(app) as client:
        setups_response = client.get("/research/setups")
        if setups_response.status_code != 200:
            print(f"FAIL: GET /research/setups returned HTTP {setups_response.status_code}")
            return 1
        events = setups_response.json()["events"]
        print(f"scanned {len(events)} events across the panel")

        selected = select_recording_events(events, CONFIG)
        pinned_included = any(_is_pinned_event(e) for e in selected)
        print(
            f"selected {len(selected)} events across "
            f"{len({e['symbol'] for e in selected})} symbols "
            f"(pinned AAPL 2026-06-22 included: {pinned_included})"
        )

        recorded = blocked = skipped = failed = 0
        for event in selected:
            start, end = event_window(event, CONFIG)
            split = split_for_event(event["id"], CONFIG)
            if args.dry_run:
                print(
                    f"DRY  {event['symbol']:6s} {event['session_date']} touch={event['touch_ts']} "
                    f"window=[{start} .. {end}) split={split}"
                )
                continue
            body = {
                "source_kind": "historical", "source_id": event["symbol"],
                "split": split, "start": start, "end": end,
            }
            response = client.post("/research/datasets", json=body)
            if response.status_code == 200:
                meta = response.json()["dataset"]
                print(
                    f"OK      {event['symbol']:6s} {event['session_date']} touch={event['touch_ts']}: "
                    f"dataset={meta['id']} feed={meta['data_feed']} split={meta['split']} "
                    f"events={meta['event_counts']['total']}"
                )
                recorded += 1
            elif response.status_code == 422 and "unavailable" in response.json().get("detail", ""):
                print(
                    f"BLOCKED {event['symbol']:6s} {event['session_date']}: real-data provider "
                    f"unavailable -- Alpaca credentials not configured"
                )
                blocked += 1
            elif response.status_code == 409:
                print(f"SKIP    {event['symbol']:6s} {event['session_date']}: already registered")
                skipped += 1
            else:
                print(
                    f"FAIL    {event['symbol']:6s} {event['session_date']}: "
                    f"HTTP {response.status_code} {response.json()}"
                )
                failed += 1

    if args.dry_run:
        return 0

    print(
        f"\n{recorded} recorded, {blocked} blocked (no credentials), "
        f"{skipped} already-registered, {failed} failed"
    )
    if blocked and not recorded:
        print(
            "Alpaca credentials are not configured in this environment -- the credentialed "
            "recording is honestly BLOCKED (never simulated). Set ALPACA_API_KEY / "
            "ALPACA_API_SECRET (and TAPEOLOGY_LIVE_INTEGRATION=1 for the integration test) to "
            "run for real."
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
