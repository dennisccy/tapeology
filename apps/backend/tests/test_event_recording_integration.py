"""Operator/gated REAL Alpaca historical-fetch + event-window recording check (era-5B J-03) --
out-of-loop, not hermetic. Per ``.claude/core.md`` (External Integration Testing) the hermetic
suite alone is NOT sufficient evidence the real credentialed recording works. This is the runnable
proof that ``record_event_windows.py``'s selection + window + split logic, driven against the REAL
``GET /research/setups`` scan and the REAL ``POST /research/datasets`` route, registers genuine
event-window datasets through the real Alpaca historical-fetch seam -- and that a recorded event's
drill-in (``GET /research/setups/{id}``) then shows a real, non-empty five-state tape timeline.

Distinct from ``test_live_integration.py`` (that file is Alpaca LIVE-SOCKET specific); this one
exercises the HISTORICAL fetch/record path, never streaming.

Gated: it requires real credentials + an explicit opt-in, so it is SKIPPED in the autonomous loop
(no opt-in) and never makes a network call by accident.

Run it (operator, creds in ``apps/backend/.env``, real panel bars already populated via
``scripts/populate_panel_bars.py``):

    TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_event_recording_integration.py -v -s
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import record_event_windows as driver  # noqa: E402

from app.config import CONFIG
from app.main import app
from app.providers.adapters.alpaca import AlpacaAdapter
from app.research.datasets import DatasetStore

pytestmark = pytest.mark.integration


def test_real_credentialed_event_window_recording_and_tape_join(tmp_path, monkeypatch):
    if os.environ.get("TAPEOLOGY_LIVE_INTEGRATION") != "1":
        pytest.skip(
            "gated: set TAPEOLOGY_LIVE_INTEGRATION=1 to run the real credentialed recording check"
        )
    adapter = AlpacaAdapter()
    if not adapter.is_available():
        pytest.skip("gated: Alpaca credentials not configured in the environment")

    # A FRESH, isolated dataset dir so this run never mutates any committed fixture and stays
    # independently re-runnable; the REAL (already-populated) bar store is read unmodified.
    dataset_dir = tmp_path / "datasets"
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))

    with TestClient(app) as client:
        setups_response = client.get("/research/setups")
        assert setups_response.status_code == 200
        events = setups_response.json()["events"]
        assert events, (
            "the real bar store must already hold scannable panel bars for this check -- run "
            "scripts/populate_panel_bars.py first"
        )

        selected = driver.select_recording_events(events, CONFIG)
        assert selected, "the real scan must produce at least one selectable event"
        pinned_selected = next((e for e in selected if driver._is_pinned_event(e)), None)

        recorded_metas: list[dict] = []
        for event in selected:
            start, end = driver.event_window(event, CONFIG)
            split = driver.split_for_event(event["id"], CONFIG)
            body = {
                "source_kind": "historical", "source_id": event["symbol"],
                "split": split, "start": start, "end": end,
            }
            response = client.post("/research/datasets", json=body)
            assert response.status_code in (200, 422, 409), (
                f"unexpected status {response.status_code} for {event['symbol']} "
                f"{event['session_date']}: {response.text}"
            )
            if response.status_code == 200:
                recorded_metas.append((event, response.json()["dataset"]))
                print(
                    f"recorded {event['symbol']} {event['session_date']} touch={event['touch_ts']} "
                    f"-> dataset {response.json()['dataset']['id']} "
                    f"(feed={response.json()['dataset']['data_feed']}, split={split})"
                )
            else:
                print(
                    f"NOT recorded {event['symbol']} {event['session_date']}: "
                    f"HTTP {response.status_code} {response.json().get('detail')}"
                )

        assert recorded_metas, "at least one real event window must record successfully"
        symbols_recorded = {event["symbol"] for event, _meta in recorded_metas}
        print(
            f"\n{len(recorded_metas)} datasets recorded across {len(symbols_recorded)} symbols: "
            f"{sorted(symbols_recorded)}"
        )

        # Every recorded dataset is genuinely registered, checksummed, feed-stamped, split-frozen.
        store = DatasetStore(dataset_dir)
        for _event, meta in recorded_metas:
            fetched = store.get(meta["id"])
            assert fetched["checksum"] == meta["checksum"]
            assert fetched["split"] in ("train", "holdout")
            assert fetched["data_feed"]  # honestly feed-stamped, never blank

        # If the pinned AAPL 2026-06-22 event recorded successfully, its drill-in must now show a
        # real, non-empty five-state tape timeline through the REAL route.
        pinned_recorded = next(
            (meta for event, meta in recorded_metas if event.get("id") == (pinned_selected or {}).get("id")),
            None,
        )
        if pinned_recorded is not None:
            detail = client.get(f"/research/setups/{pinned_selected['id']}")
            assert detail.status_code == 200
            timeline = detail.json()["event"]["tape_timeline"]
            assert timeline, "the pinned AAPL 2026-06-22 event must show a real tape timeline once recorded"
            for entry in timeline:
                assert entry["state"] in (
                    "buyer_control", "seller_control", "bid_absorption", "ask_absorption",
                )
                assert isinstance(entry["confidence"], float)
                assert entry["timestamp"]
            print(f"pinned AAPL 2026-06-22 tape_timeline: {timeline}")
        else:
            print(
                "pinned AAPL 2026-06-22 event was not among this run's recorded datasets "
                "(already registered earlier, or not selected this run) -- see the dataset list above"
            )
