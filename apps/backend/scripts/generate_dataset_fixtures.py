"""Generate the committed miniature train + holdout dataset fixture pair (J-02) — ONCE.

The pair is produced through the REAL record path (``record_from_source`` -> ``DatasetStore``,
checksum computed at registration) from the committed keyless PG SIP reference window — never
hand-crafted JSON — and committed under ``tests/fixtures/datasets/`` (outside the gitignored
``.data/``). CI then proves record -> register -> replay end-to-end, checksum verification
included, with no credentials (``tests/test_datasets.py``).

The two slices are DISJOINT sub-windows of the reference capture (nothing is ever judged on the
data it was tuned on) and miniature (about a minute of dense real SIP tape each) so the CI
replays stay fast:

  * train:   2026-06-09T17:00:00Z .. 17:01:00Z
  * holdout: 2026-06-09T17:05:00Z .. 17:05:45Z

Run from ``apps/backend``:  ``.venv/bin/python scripts/generate_dataset_fixtures.py``

The script REFUSES to run if the fixture directory already holds datasets — the committed pair
is frozen at its one generation (regenerating would mint new ids/timestamps and re-pin tests
for no reason). Delete the directory first if a regeneration is genuinely intended.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import CONFIG  # noqa: E402
from app.research.datasets import (  # noqa: E402
    SPLIT_HOLDOUT,
    SPLIT_TRAIN,
    DatasetStore,
    record_from_source,
)

FIXTURE_DATASET_DIR = BACKEND_DIR / "tests" / "fixtures" / "datasets"

SLICES = (
    (SPLIT_TRAIN, "2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z"),
    (SPLIT_HOLDOUT, "2026-06-09T17:05:00Z", "2026-06-09T17:05:45Z"),
)


def main() -> int:
    store = DatasetStore(FIXTURE_DATASET_DIR)
    existing, errors = store.list()
    if existing or errors:
        print(
            f"REFUSED: {FIXTURE_DATASET_DIR} already holds {len(existing)} dataset(s) "
            f"(+{len(errors)} unreadable) — the committed pair is frozen at its one generation."
        )
        return 1
    for split, start, end in SLICES:
        meta = record_from_source(
            store,
            source_kind="reference",
            source_id="PG_SIP_REFERENCE",
            split=split,
            start=start,
            end=end,
            config=CONFIG,
        )
        counts = meta["event_counts"]
        print(
            f"{split:8s} id={meta['id']} {meta['symbol']} {meta['window_start_utc']}"
            f" .. {meta['window_end_utc']} feed={meta['data_feed']}"
            f" trades={counts['trades']} quotes={counts['quotes']} checksum={meta['checksum']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
