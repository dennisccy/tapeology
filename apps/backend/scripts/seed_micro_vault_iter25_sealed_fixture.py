"""Seed ONE permanently-sealed vault shard into a throwaway rig root, for J-06's browser-QA pass
(Era "The Rapid Microscope", goal-rapid-microscope-iter-25).

**Why this exists.** Every prior browser-QA rig carried exactly one vault shard -- the iter-18
graduation seeder's ``iter18-qa-universe`` shard, which is sealed -> assigned -> exposed in the
same script run. That leaves the rig's Validation Vault table with zero shards ever observed in
the ``sealed`` state by the time a screenshot is taken, so the "a sealed row stays opaque" render
branch (``page.tsx:6810-6819``, shipped since iteration 14) and its browser acceptance check
(TC-2/TC-3) have had no fixture data to trigger against for three rounds. This script closes that
gap the SAME way every other fixture in this ``scripts/`` directory does: it plants a REAL dataset
through ``DatasetStore.record`` and calls the REAL ``vault.seal_shard`` -- never a hand-rolled
JSON blob standing in for either -- and, critically, it NEVER calls ``vault.assign_shard`` or
``vault.expose_shard``, so the shard it plants stays ``sealed`` for the lifetime of the rig.

**What this plants.** ONE real tiny tick dataset (symbol ``PGVAULT`` -- deliberately distinct from
every other symbol this rig's other seed scripts use: ``PG`` (the era-2 committed tick fixtures),
``PGQA`` (the iter-18 graduation seeder's exposed shard), and whatever real PG dataset the iter-24
J-09 seeder reuses -- so this shard can never collide with, or be confused for, any of them), then
``vault.seal_shard(...)`` on it under its own fixture-only universe id
(``iter25-qa-sealed-only-universe``, never registered against a ``VaultUniverseLedger`` row --
``seal_shard`` records ``universe_id`` verbatim without looking one up, so no registration act is
needed for a shard that is never assigned) and its own fixture-only HMAC secret (a literal, never
the operator's real ``TAPEOLOGY_VAULT_SECRET_FILE`` -- no seed script in this repo ever reads that
file). The result: ``GET /research/desk/micro/vault`` on this rig now lists TWO shards -- the
iter-18 one (``exposed``, full provenance) and this one (``sealed``, opaque projection only,
forever) -- exercising both branches of the Vault table's per-row render for the first time.

**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
``root`` argument's own env-var scoping (``TAPEOLOGY_DATASET_DIR`` and the vault dir it resolves
as a sibling of), exactly like every other seed script in this directory. **Never a production
code path change** -- this script imports and calls the SAME ``DatasetStore.record``/
``vault.seal_shard`` functions the shipped product uses; it adds no new module, no new endpoint,
no new branch inside either of them.

``plant_sealed_shard`` is exported (not just callable from ``main``) so
``tests/test_vault.py`` can reuse the identical production seeding logic directly -- proving the
sealed-shard refusal non-vacuously against the literal shard this rig plants, rather than a second,
divergent test-only construction of "a sealed shard."

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports
``TAPEOLOGY_DATASET_DIR`` first, mirroring every other seed script's own convention):

    TAPEOLOGY_DATASET_DIR=... .venv/bin/python scripts/seed_micro_vault_iter25_sealed_fixture.py ROOT
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
from app.research import vault  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402

_SYMBOL = "PGVAULT"  # distinct from PG / PGQA / CALDR -- never collides with any other seed script
_WINDOW_START_UTC = "2026-06-10T13:00:00Z"
_WINDOW_END_UTC = "2026-06-10T13:01:00Z"

_UNIVERSE_ID = "iter25-qa-sealed-only-universe"
_SEALED_AT = "2026-06-07T00:00:00.000000Z"  # a fixed, arbitrary instant -- never wall-clock (T-3/T-7)
_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter25-qa-only-sealed-fixture-vault-secret"


def _events_for_store() -> list:
    """A tiny, REAL trade/quote sequence -- the ``test_micro_observer.py``/
    ``seed_micro_graduation_iter18_fixture.py`` ``_events_for_store`` shape, mirrored verbatim
    (never re-derived): one quote, one aggressor-classified BUY, one SELL."""
    return [
        QuoteEvent(_SYMBOL, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(_SYMBOL, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
        TradeEvent(_SYMBOL, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
    ]


def plant_sealed_shard(root: Path) -> dict:
    """Plants the dataset + seals the shard for real; returns the identifiers a caller (this
    module's own ``main``, or a test) needs to assert against. NEVER calls ``assign_shard``/
    ``expose_shard`` -- the shard this returns stays ``sealed`` for as long as the ledger it was
    written into exists."""
    dataset_dir = root / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_store = DatasetStore(dataset_dir)
    vault_dir = vault.resolve_vault_dir(str(dataset_dir))

    events = _events_for_store()
    dataset_meta = dataset_store.record(
        symbol=_SYMBOL, source="fixture", source_kind="fixture",
        source_id="goal-rapid-microscope-iter25-qa-sealed-only",
        split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
        data_feed="sip", epoch_anchor=0.0, events=events,
    )
    dataset_id = dataset_meta["id"]

    shard_ledger = vault.VaultShardLedger(vault_dir)
    row = vault.seal_shard(
        shard_ledger, dataset_id=dataset_id, universe_id=_UNIVERSE_ID,
        content_checksum=dataset_meta["checksum"], event_count=len(events),
        vault_secret=_FIXTURE_VAULT_SECRET, sealed_at=_SEALED_AT,
    )
    return {
        "dataset_id": dataset_id,
        "symbol": _SYMBOL,
        "universe_id": _UNIVERSE_ID,
        "shard_id": row["shard_id"],
        "content_checksum": dataset_meta["checksum"],
        "vault_dir": vault_dir,
        "dataset_dir": str(dataset_dir),
    }


def main(root: Path) -> int:
    planted = plant_sealed_shard(root)
    print(
        f"[seed-micro-vault-iter25] sealed (never assigned/exposed) shard_id={planted['shard_id']} "
        f"for dataset_id={planted['dataset_id']} ({planted['symbol']}) "
        f"universe_id={planted['universe_id']}",
        file=sys.stderr,
    )
    if planted["symbol"] in planted["shard_id"] or planted["dataset_id"] == planted["shard_id"]:
        print(
            "[seed-micro-vault-iter25] ERROR: the served shard_id is not opaque -- it derives "
            "from or equals the real dataset id/symbol",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
