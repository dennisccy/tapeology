"""Seed ONE valid snapshot, ONE stale meta, and ONE withheld pool member into a throwaway rig
root, for J-12's browser-QA "fixture-scoped" capture (Era "The Rapid Microscope",
goal-rapid-microscope-iter-33).

**Why this exists.** TC-2 requires all three states on screen at once: a valid snapshot's every
served identity field, a stale meta appearing nowhere as a row (only inside `stale_excluded`), and
a withheld pool member appearing nowhere by id/symbol/session-date/checksum/row-count/bytes (only
inside `withheld_excluded`). The real `.data` corpus cannot reliably discriminate all three at once
on demand, so this script plants them the SAME way every other fixture in this ``scripts/``
directory does: it plants REAL datasets through ``DatasetStore.record``'s own public write path
and builds a REAL snapshot through ``micro_snapshots.run_snapshot_build_and_record`` -- never a
hand-rolled JSON blob standing in for either.

**The one deliberate exception, and why it is the only faithful way to build it.** A "stale" meta
is, by definition, a meta file whose recorded identity no longer matches a FRESH computation
(TR-7) -- normally produced by an algo/format/feature-source/fingerprint code move. A fixture
script cannot change the running code's own bytes out from under itself and remain "the same
production code", so after building the stale-symbol's snapshot for real, this script mutates
ONLY that one persisted meta file's own `dataset_checksum` field directly (the SAME technique
``tests/test_micro_snapshots.py::test_snapshot_meta_report_counts_a_present_but_no_longer_
identity_matching_meta_as_stale`` uses at the unit level) -- never touching the rows file, never
touching any OTHER snapshot's meta, and never inventing a value ``load_snapshot_meta`` would ever
serve (a mismatched identity is a MISS, so nothing about this stale meta's stored fields is ever
read back as current).

**What this plants** (three distinct symbols, none colliding with any other seed script in this
directory -- ``PGVAULT``/``PGQA``/``CALDR``/etc. per those scripts' own registries):

* ``PGSNAPOK`` -- a real tiny tick dataset, snapshot built for real via
  ``run_snapshot_build_and_record``. Stays a genuinely CURRENT, servable snapshot.
* ``PGSNAPST`` -- a real tiny tick dataset, snapshot built for real, THEN its own persisted meta
  file's ``dataset_checksum`` is overwritten with a value that can never match a fresh
  recomputation -- an honest MISS on the very next read (never served as a row; counted only in
  ``stale_excluded``).
* ``PGSNAPWH`` -- a real tiny tick dataset that is NEVER snapshotted. A universe is registered
  whose ``symbol_rule``/``date_rule`` matches its own ``(symbol, session_date)`` (the r5
  rule-membership withholding case, ``vault.unresolved_pool_universe_by_dataset_id``'s own (b)
  test), with a ``registered_at`` well before the dataset's real ``created_utc`` -- so it is
  withheld from BOTH the snapshot listing AND any snapshot build, with no vault shard-ledger row
  needed at all (mirrors ``tests/test_vault.py::test_tc7_micro_snapshots_withheld_excluded_is_
  pool_derived_not_snapshot_file_derived``).

**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
``root`` argument's own env-var scoping, exactly like every other seed script in this directory --
run it against a fresh, never-seeded root via ``TAPEOLOGY_DATASET_DIR=<root>/datasets`` (the
``seed_micro_vault_iter25_sealed_fixture.py`` convention).

Usage:

    TAPEOLOGY_DATASET_DIR=<root>/datasets \\
        .venv/bin/python scripts/seed_micro_snapshots_iter33_disclosure_fixture.py ROOT
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

from app.config import CONFIG  # noqa: E402
from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
from app.research import micro_snapshots as ms  # noqa: E402
from app.research import vault  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402

_SYMBOL_OK = "PGSNAPOK"
_SYMBOL_STALE = "PGSNAPST"
_SYMBOL_WITHHELD = "PGSNAPWH"

_WINDOW_START_UTC = "2026-06-10T13:00:00Z"
_WINDOW_END_UTC = "2026-06-10T13:01:00Z"
# The ET calendar date of `_WINDOW_START_UTC` (EDT, UTC-4 in June) -- the withheld universe's own
# `date_rule` must match this exactly for the rule-membership test to catch the dataset.
_SESSION_DATE = "2026-06-10"

_WITHHELD_UNIVERSE_ID = "iter33-qa-withheld-only-universe"
# Well before ANY real `created_utc` this script's own `DatasetStore.record` call will ever stamp
# (real wall-clock "now") -- the `created_utc >= registered_at` guard that makes rule-membership
# withholding apply.
_WITHHELD_UNIVERSE_REGISTERED_AT = "2020-01-01T00:00:00.000000Z"
_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter33-qa-withheld-only-fixture-vault-secret"

# A stale meta's mutated identity component must never coincidentally match a fresh
# recomputation -- 64 zero hex digits is not a real sha256 digest of anything this script ever
# computes.
_STALE_DATASET_CHECKSUM = "0" * 64


def _events_for_store(symbol: str) -> list:
    """A tiny, REAL trade/quote sequence -- the ``seed_micro_vault_iter25_sealed_fixture.py``/
    ``test_micro_observer.py`` ``_events_for_store`` shape, mirrored verbatim (never re-derived):
    one quote, one aggressor-classified BUY, one SELL."""
    return [
        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(symbol, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
        TradeEvent(symbol, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
    ]


def _plant(dataset_store: DatasetStore, symbol: str, source_id: str) -> dict:
    return dataset_store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id=source_id,
        split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(symbol),
    )


def plant_disclosure_fixture(root: Path) -> dict:
    """Plants all three for real; returns the identifiers a caller (this module's own ``main``,
    or a test) needs to assert against."""
    dataset_dir = root / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_store = DatasetStore(dataset_dir)
    snapshots_dir = ms.resolve_micro_snapshots_dir(str(dataset_dir))
    vault_dir = vault.resolve_vault_dir(str(dataset_dir))

    valid_meta = _plant(dataset_store, _SYMBOL_OK, "goal-rapid-microscope-iter33-qa-valid")
    stale_meta = _plant(dataset_store, _SYMBOL_STALE, "goal-rapid-microscope-iter33-qa-stale")
    withheld_meta = _plant(dataset_store, _SYMBOL_WITHHELD, "goal-rapid-microscope-iter33-qa-withheld")

    # Real builds for the OK and (soon-to-be-mutated) STALE datasets -- never for WITHHELD, which
    # `run_snapshot_build_and_record`'s own filter would refuse to build for anyway.
    ms.run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, [valid_meta["id"], stale_meta["id"]])

    # Mutate ONLY the stale dataset's own persisted meta file's identity -- see module docstring.
    stale_meta_path = Path(snapshots_dir) / f"{stale_meta['id']}.meta.json"
    stored = json.loads(stale_meta_path.read_text())
    stored["dataset_checksum"] = _STALE_DATASET_CHECKSUM
    stale_meta_path.write_text(json.dumps(stored, sort_keys=True))

    universe_ledger = vault.universe_ledger_for_dataset_dir(str(dataset_dir))
    vault.register_universe(
        universe_ledger,
        universe_id=_WITHHELD_UNIVERSE_ID,
        symbol_rule=[_SYMBOL_WITHHELD],
        date_rule=[_SESSION_DATE],
        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_VAULT_SECRET),
        registered_at=_WITHHELD_UNIVERSE_REGISTERED_AT,
    )

    return {
        "dataset_dir": str(dataset_dir),
        "snapshots_dir": snapshots_dir,
        "vault_dir": vault_dir,
        "valid_dataset_id": valid_meta["id"],
        "stale_dataset_id": stale_meta["id"],
        "withheld_dataset_id": withheld_meta["id"],
        "withheld_universe_id": _WITHHELD_UNIVERSE_ID,
    }


def main(root: Path) -> int:
    planted = plant_disclosure_fixture(root)
    print(
        f"[seed-micro-snapshots-iter33] valid dataset_id={planted['valid_dataset_id']} "
        f"({_SYMBOL_OK}), stale dataset_id={planted['stale_dataset_id']} ({_SYMBOL_STALE}, "
        "meta mutated post-build), withheld dataset_id="
        f"{planted['withheld_dataset_id']} ({_SYMBOL_WITHHELD}, universe="
        f"{planted['withheld_universe_id']})",
        file=sys.stderr,
    )

    # Self-check: the served report matches the intended three-way split before handing off to a
    # browser pass.
    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
    report = ms.snapshot_meta_report(planted["snapshots_dir"], dataset_store, CONFIG)
    served_ids = {row["dataset_id"] for row in report["snapshots"]}
    ok = True
    if planted["valid_dataset_id"] not in served_ids:
        print("[seed-micro-snapshots-iter33] ERROR: the valid snapshot is not served", file=sys.stderr)
        ok = False
    if planted["stale_dataset_id"] in served_ids:
        print("[seed-micro-snapshots-iter33] ERROR: the stale meta is served as a row", file=sys.stderr)
        ok = False
    if planted["withheld_dataset_id"] in served_ids:
        print("[seed-micro-snapshots-iter33] ERROR: the withheld member is served as a row", file=sys.stderr)
        ok = False
    if report["stale_excluded"] != 1:
        print(
            f"[seed-micro-snapshots-iter33] ERROR: stale_excluded={report['stale_excluded']!r}, expected 1",
            file=sys.stderr,
        )
        ok = False
    if report["withheld_excluded"] != 1:
        print(
            f"[seed-micro-snapshots-iter33] ERROR: withheld_excluded={report['withheld_excluded']!r}, expected 1",
            file=sys.stderr,
        )
        ok = False
    if not ok:
        return 1
    print("[seed-micro-snapshots-iter33] self-check ok: 1 valid served, 1 stale excluded, 1 withheld excluded", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
