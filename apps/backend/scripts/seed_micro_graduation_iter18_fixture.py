"""Seed ONE discriminating graduation family into a throwaway rig root, for J-07's browser-QA pass
(Era "The Rapid Microscope", goal-rapid-microscope-iter-18, TR-30).

Before this iteration, ``GET /research/desk/micro/graduation`` had never been observed non-empty on
the store-scoped browser-QA rig -- every prior browser pass photographed the honest
``{"families": [], "message": "No candidates ledgered."}`` empty state (correct on a fresh install,
but non-discriminating: it would look identical whether the r9/TR-30-rewritten
``micro_sealed_evaluation.evaluate_sealed_verdict`` worked or was broken). This script closes that
gap the SAME way every other playbook/desk fixture in this ``scripts/`` directory does: it plants
REAL records through the REAL production functions -- never a hand-rolled JSON blob standing in for
one -- so a browser screenshot of the seeded endpoint is genuine evidence, not a fabricated fixture
dressed up as a response.

**What this script does, in the exact seven-step ``evaluate_sealed_verdict`` sequence (spec section
8.1) it exercises for real:**

1. Plants ONE real tick dataset (``DatasetStore.record`` -- the ``test_micro_observer.py``
   ``_plant``/``_events_for_store`` precedent, mirrored verbatim) plus its real feature snapshot
   (``build_snapshot_rows``/``write_snapshot`` -- the ``test_micro_accessor.py``
   ``_plant_dataset_and_snapshot`` precedent).
2. Seals -> assigns -> exposes ONE real vault shard bound to that dataset (``vault.seal_shard``/
   ``assign_shard``/``expose_shard`` -- the ``test_micro_sealed_evaluation.py`` ``_exposed_shard_for``
   precedent).
3. Builds ONE real candidate spec (a plain dict -- no persisted "candidate family" ledger exists
   yet in this codebase; a future J-08/J-09 wiring act owns that, per
   ``micro_sealed_evaluation.py``'s own established "not invented here" precedent) whose
   ``registered_at`` is strictly before the shard's ``assigned_at`` and whose
   ``sealed_pass_rule_hash`` is stamped from the CURRENT ``sealed_pass_rule_hash()`` -- exactly
   what a real caller would do.
4. Calls the NOW-FIXED (r9/TR-30) ``micro_sealed_evaluation.evaluate_sealed_verdict`` FOR REAL,
   with 30 real (never fabricated-after-the-fact) observation dicts whose recomputed effect clears
   the family's own registered economic floor in its registered direction -- so the persisted
   verdict is a genuine ``"pass"``, not a hand-set field.
5. The result lands in the ``TAPEOLOGY_MICRO_GRADUATION_DIR``-or-sibling-of-dataset-dir graduation
   ledger, the SAME directory ``GET /research/desk/micro/graduation`` reads from when the scoped
   backend serves the SAME ``TAPEOLOGY_DATASET_DIR`` -- so the seeded row and the served JSON body
   are byte-identical, checkable by a browser-QA agent against the on-disk ledger row (TC-10).

**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
``root`` argument's own env-var scoping (``TAPEOLOGY_DATASET_DIR`` and friends), exactly like every
other seed script in this directory -- this script contains no fallback to an unscoped default path.
**Never a production code path change** -- this script imports and calls the SAME
``evaluate_sealed_verdict``/``DatasetStore.record``/``vault.*`` functions the shipped product uses;
it adds no new module, no new endpoint, no new branch inside any of them.

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports
``TAPEOLOGY_DATASET_DIR`` first, mirroring every other seed script's own convention):

    TAPEOLOGY_DATASET_DIR=... .venv/bin/python scripts/seed_micro_graduation_iter18_fixture.py ROOT
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

from app.config import CONFIG  # noqa: E402
from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
from app.research import micro_sealed_evaluation as sealed_eval  # noqa: E402
from app.research import scout_ledger  # noqa: E402
from app.research import vault  # noqa: E402
from app.research import walkforward as wf  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.micro_accessor import MicroAccessor  # noqa: E402
from app.research.micro_graduation import GraduationLedger, resolve_micro_graduation_dir  # noqa: E402
from app.research.micro_snapshots import (  # noqa: E402
    build_snapshot_rows,
    resolve_micro_snapshots_dir,
    snapshot_identity,
    write_snapshot,
)

_SYMBOL = "PGQA"  # deliberately NOT "PG" -- never collides with the era-2 committed PG tick fixtures
# this same rig also stages (qa_playbook_iter7_fixture_scoped_backend.sh's own DATASET_DIR seed).
_WINDOW_START_UTC = "2026-06-09T13:00:00Z"
_WINDOW_END_UTC = "2026-06-09T13:01:00Z"
_SESSION_DATE = "2026-06-09"

_SPEC_REGISTERED_AT = "2026-06-01T00:00:00.000000Z"  # strictly BEFORE _ASSIGNED_AT below
_ASSIGNED_AT = "2026-06-05T00:00:00.000000Z"
_EXPOSED_AT = "2026-06-06T00:00:00.000000Z"
_EVALUATED_AT = "2026-06-10T00:00:00.000000Z"

# r13: an economic floor must declare its unit (see `micro_features.require_bps_floor`).
_ECON_FLOOR = {"floor_bps": 5.0, "unit": "bps"}
_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter18-qa-only-fixture-vault-secret"


def _events_for_store() -> list:
    """A tiny, REAL trade/quote sequence -- the ``test_micro_observer.py`` ``_events_for_store``
    shape, mirrored verbatim (never re-derived): one quote, one aggressor-classified BUY, one SELL."""
    return [
        QuoteEvent(_SYMBOL, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(_SYMBOL, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
        TradeEvent(_SYMBOL, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
    ]


def _observation(session_date: str, symbol: str, value: float) -> dict:
    # goal-hypothesis-foundry-iter-1 (TC-1/TC-2): every observation must declare the canonical
    # unit its `value` is already expressed in, or `walkforward.require_canonical_observation_units`
    # refuses it before a single value is averaged (r13/r14 unit-discipline guard -- see that
    # function's own docstring). This fixture's values were ALWAYS basis points (`_ECON_FLOOR`
    # above compares them against a `floor_bps` in the SAME `long`/positive direction) -- the bug
    # was a missing declaration, never a wrong unit, so the fix names the SAME canonical constant
    # the guard itself checks against (`walkforward.WF_OBSERVATION_UNIT`, itself
    # `micro_features.OUTCOME_UNIT` -- never a second, independently-spelled unit string).
    return {"session_date": session_date, "symbol": symbol, "value": value, "value_unit": wf.WF_OBSERVATION_UNIT}


def _passing_observations() -> list[dict]:
    """30 real observations from the ONE seeded shard -- session/symbol breadth is
    ``not_applicable_single_shard`` at shard scope (r9), so every observation shares the shard's own
    (symbol, session_date). Deliberately DIFFERENT values (never a repeated constant) symmetric
    around 10.0, so the mean -- the recomputed effect -- is exactly 10.0: clears ``_ECON_FLOOR``'s
    5.0 bps floor in the "long"/positive registered direction, the SAME fixture shape
    ``test_micro_sealed_evaluation.py`` uses (never a second, divergent construction)."""
    values = [10.0 + (i - 14.5) for i in range(30)]
    return [_observation(_SESSION_DATE, _SYMBOL, v) for v in values]


def main(root: Path) -> int:
    dataset_dir = root / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_store = DatasetStore(dataset_dir)
    snapshots_dir = resolve_micro_snapshots_dir(str(dataset_dir))
    graduation_dir = resolve_micro_graduation_dir(str(dataset_dir))
    vault_dir = vault.resolve_vault_dir(str(dataset_dir))

    # --- step 1: a REAL dataset + REAL feature snapshot (never fabricated) ------------------------
    dataset_meta = dataset_store.record(
        symbol=_SYMBOL, source="fixture", source_kind="fixture", source_id="goal-rapid-microscope-iter18-qa",
        split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
    )
    dataset_id = dataset_meta["id"]
    rows = build_snapshot_rows(dataset_store, dataset_id, CONFIG, quote_size_unit="unverified")
    identity = snapshot_identity(dataset_meta, CONFIG)
    write_snapshot(snapshots_dir, dataset_id, rows, {**identity, "quote_size_unit": "unverified"})
    print(f"[seed-micro-graduation-iter18] planted dataset {dataset_id} ({_SYMBOL} / {_SESSION_DATE})", file=sys.stderr)

    # --- step 2: seal -> assign -> expose ONE real vault shard bound to a real family_root_id ------
    family_root_id = scout_ledger.compute_family_root_id(
        "impact_efficiency_trend_iter18_qa", "band_wall_touch", "trades_20",
    )
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    vault.seal_shard(
        shard_ledger, dataset_id=dataset_id, universe_id="iter18-qa-universe",
        content_checksum=dataset_meta["checksum"], event_count=len(_events_for_store()),
        vault_secret=_FIXTURE_VAULT_SECRET, sealed_at="2026-05-01T00:00:00.000000Z",
    )
    vault.assign_shard(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
        symbol=_SYMBOL, session_date=_SESSION_DATE, assigned_at=_ASSIGNED_AT,
    )
    vault.expose_shard(shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, exposed_at=_EXPOSED_AT)
    print(f"[seed-micro-graduation-iter18] sealed -> assigned -> exposed shard for family_root_id={family_root_id}", file=sys.stderr)

    # --- step 3: a real candidate spec, registered strictly before assignment ----------------------
    candidate_spec = {
        "family_root_id": family_root_id,
        "candidate_id": "iter18-qa-candidate-1",
        "family_id": "iter18-qa-family-a",
        "spec_hash": "iter18-qa-spec-hash-1",
        "sidedness": "long",
        "econ_floor": _ECON_FLOOR,
        "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS,
        "process_label": wf.PROCESS_LABEL_RULE,
        "registered_at": _SPEC_REGISTERED_AT,
        "sealed_pass_rule_hash": sealed_eval.sealed_pass_rule_hash(),
        # (r9) deliberately NO "floors" key -- the QA seed exercises the real, evaluator-owned rule,
        # never the retired caller-override shortcut.
    }

    # --- step 4: call the REAL, r9-fixed evaluator -- persists through the real ledger machinery ---
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    graduation_ledger = GraduationLedger(graduation_dir)
    result = sealed_eval.evaluate_sealed_verdict(
        graduation_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_id,
        observations=_passing_observations(), evaluated_at=_EVALUATED_AT,
    )
    row = result["row"]
    print(
        f"[seed-micro-graduation-iter18] evaluate_sealed_verdict -> transition={result['transition']} "
        f"verdict={row['verdict']} n={row['n']} rule_hash={row['rule_hash']}",
        file=sys.stderr,
    )
    if row["verdict"] != sealed_eval.SEALED_VERDICT_PASS:
        print("[seed-micro-graduation-iter18] ERROR: expected a real PASS verdict", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
