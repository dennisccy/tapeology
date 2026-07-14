"""Generate the ONE committed tape-at-the-wall join-path fixture (era-5B J-03) -- ONCE.

Produced through the REAL record path (``record_from_source`` -> ``DatasetStore``, checksum
computed at registration) from the SAME committed keyless PG SIP reference window
``generate_dataset_fixtures.py`` already uses for the era-3 J-02 train/holdout pair -- never
hand-crafted JSON -- sliced to a NEW, disjoint sub-window and committed under
``tests/fixtures/datasets_j03/`` (a directory of its own, so this fixture is never confused with,
or accidentally pooled with, the era-3 pair). CI then proves the tape-at-the-wall join
end-to-end -- record -> register -> replay through the frozen ``TapeEngine`` -> collapse to a
state-transition timeline -- with no credentials (``tests/test_setups.py``).

The window (2026-06-09T17:02:00Z .. 17:03:00Z) is a ONE-MINUTE slice of the reference capture,
disjoint from BOTH the existing committed train (17:00:00-17:01:00) and holdout (17:05:00-
17:05:45) windows (nothing here is ever pooled with, or judged on, data those already use), dense
enough to carry a real, non-trivial tape-state read (~1,960 real trade+quote events).

Run from ``apps/backend``:  ``.venv/bin/python scripts/generate_setups_join_fixture.py``

The script REFUSES to run if the fixture directory already holds a dataset -- the committed
fixture is frozen at its one generation (regenerating would mint a new id/timestamp and re-pin
the join-path test's exact-value assertions for no reason). Delete the directory first if a
regeneration is genuinely intended.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import CONFIG  # noqa: E402
from app.research.datasets import SPLIT_TRAIN, DatasetStore, record_from_source  # noqa: E402

FIXTURE_DATASET_DIR = BACKEND_DIR / "tests" / "fixtures" / "datasets_j03"

# Disjoint from the era-3 J-02 pair's 17:00:00-17:01:00 (train) / 17:05:00-17:05:45 (holdout).
WINDOW_START, WINDOW_END = "2026-06-09T17:02:00Z", "2026-06-09T17:03:00Z"


def main() -> int:
    store = DatasetStore(FIXTURE_DATASET_DIR)
    existing, errors = store.list()
    if existing or errors:
        print(
            f"REFUSED: {FIXTURE_DATASET_DIR} already holds {len(existing)} dataset(s) "
            f"(+{len(errors)} unreadable) — the committed fixture is frozen at its one generation."
        )
        return 1
    meta = record_from_source(
        store,
        source_kind="reference",
        source_id="PG_SIP_REFERENCE",
        split=SPLIT_TRAIN,
        start=WINDOW_START,
        end=WINDOW_END,
        config=CONFIG,
    )
    counts = meta["event_counts"]
    print(
        f"id={meta['id']} {meta['symbol']} {meta['window_start_utc']} .. {meta['window_end_utc']}"
        f" feed={meta['data_feed']} trades={counts['trades']} quotes={counts['quotes']}"
        f" checksum={meta['checksum']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
