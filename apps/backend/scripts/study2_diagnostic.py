"""r14.3 -- the ONE Study 2 exposed-corpus diagnostic run.

**What this does, and the order it does it in.**

    verify preconditions  ->  register + screen (ONE extraction)  ->  continuous report
                          ->  outcome read off the Scout decision

Study 2 asks a cheap question on evidence that is already spent: *does the exposed legacy tick
corpus produce enough paired-touch anchors to estimate anything?* Answering it costs nothing,
because every window it can read was exposed long before any rule could have been frozen against
it -- the result is ``historical_exposed_diagnostic``, permanently, and can never graduate.

**The candidate is the already-frozen pilot spec, not a new one.** This script does not define a
candidate. It takes ``scout.pilot_study_candidate_grid(...)["delta_divergence_level_tests"]``
verbatim -- ``divergence_at_level_bearish`` / ``threshold ge 1.0`` / ``band_touch`` / ``trades_20``
/ ``sidedness=None`` -- exactly as the ``POST /scout/compute {"grid": "delta_divergence_pilot"}``
route and the CLI's own pilot selector do. No threshold sweep, no variant, no second spec.

**Why ``register_and_screen_candidate`` and not ``register_screen_and_walkforward_check``.** The
latter is the pilot path the compute-manager uses, and it RE-EXTRACTS anchors for its walk-forward
floor-check stage -- its own docstring flags that as affordable "on the small, committed fixture
... never the real production corpus". Study 2's continuous report must describe the SAME anchors
the screen judged, so a second extraction is exactly what must not happen here. The floor check
itself is documented to always refuse today (the corpus carries zero ``historical_oos`` sessions),
so skipping it withholds nothing: it would spend a second full pass over the real corpus to
re-derive a known refusal. ``register_screen_and_walkforward_check`` calls
``register_and_screen_candidate`` unmodified anyway, so this is the same screening code either way.

**Dry by default.** The screen is a read; the LEDGER APPEND is the irreversible act. A dry run
verifies every precondition and reports the corpus it would screen, then stops without touching the
ledger. ``--commit`` performs the one real run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps" / "backend"))

from app.config import CONFIG  # noqa: E402
from app.research import micro_study2_diagnostic as s2  # noqa: E402
from app.research import scout, vault, walkforward as wf  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir  # noqa: E402
from app.research.desk_playbook_context import BandMapResolver  # noqa: E402
from app.research.micro_snapshots import (  # noqa: E402
    exclude_withheld,
    feature_source_hash,
    resolve_micro_snapshots_dir,
)
from app.research.scout_ledger import ScoutLedger  # noqa: E402
from app.research.dataset_index import indexed_dataset_store  # noqa: E402

STUDY_ID = "delta_divergence_level_tests"


class PreconditionFailed(SystemExit):
    """A precondition that must hold before any real Study 2 run. Raised as ``SystemExit`` so the
    script stops loudly rather than degrading into a partial run."""


def _bar_store():
    from app.research.bars import BarStore

    return BarStore(CONFIG.bar_dir_resolved())


def verify_preconditions(ledger: ScoutLedger, dataset_store: DatasetStore, snapshots_dir: str) -> dict:
    """Everything that must be true BEFORE the one real run. Each check fails closed.

    1. no Study 2 row already exists (a duplicate real result is never appended silently);
    2. every built snapshot meta is CURRENT under the live ``feature_source_hash``;
    3. the corpus is the permanently-exposed legacy tick corpus;
    4. withheld datasets are excluded, and the count is disclosed;
    5. no sealed dataset id reaches the manifest."""
    report: dict = {}

    # --- 1. no existing Study 2 row -----------------------------------------------------------
    prior = [
        r for r in ledger.all_rows()
        if (r.get("feature") or {}).get("name") == "divergence_at_level_bearish"
        and (r.get("structure_context") or {}).get("kind") == "band_touch"
    ]
    report["existing_study2_rows"] = [
        {"row_index": r["row_index"], "candidate_id": r["candidate_id"], "decision": r["decision"]}
        for r in prior
    ]
    if prior:
        raise PreconditionFailed(
            f"STOP: {len(prior)} Study 2 Scout row(s) already exist in the real ledger "
            f"({report['existing_study2_rows']}). A duplicate real result is never appended."
        )

    # --- 2. snapshot provenance is current ----------------------------------------------------
    live = feature_source_hash()
    metas = sorted(Path(snapshots_dir).glob("*.meta.json"))
    stale = []
    for m in metas:
        j = json.loads(m.read_text())
        if j.get("feature_source_hash") != live:
            stale.append(j.get("dataset_id"))
    report["snapshot_metas"] = len(metas)
    report["snapshot_feature_source_hash"] = live
    report["stale_snapshots"] = stale
    if stale:
        raise PreconditionFailed(
            f"STOP: {len(stale)} snapshot(s) are stale under the live feature_source_hash "
            f"{live[:16]}… -- rebuild before screening, or the screen describes code that no "
            "longer produces those rows."
        )
    if not metas:
        raise PreconditionFailed("STOP: no built snapshots -- nothing to screen.")

    # --- 3/4/5. the corpus: exposed legacy, withheld excluded, no sealed id --------------------
    records, _errors = dataset_store.list()
    kept, withheld_excluded = exclude_withheld(records, dataset_store)
    manifest_ids = {r["id"] for r in kept}

    vault_dir = vault.resolve_vault_dir(CONFIG.dataset_dir_resolved())
    shard_ledger = vault.VaultShardLedger(vault_dir)
    sealed_ids = {
        row["dataset_id"] for row in shard_ledger.all_rows()
        if row.get("exposure_state") == vault.STATE_SEALED
    }
    leaked = sorted(manifest_ids & sealed_ids)
    report["datasets_registered"] = len(records)
    report["datasets_in_manifest"] = len(kept)
    report["withheld_excluded"] = withheld_excluded
    report["sealed_rows_total"] = len(sealed_ids)
    report["sealed_ids_in_manifest"] = leaked
    if leaked:
        raise PreconditionFailed(
            f"STOP: {len(leaked)} SEALED dataset id(s) reached the corpus manifest -- refused."
        )

    session_dates = sorted({vault._et_session_date_of(r["window_start_utc"]) for r in kept})
    symbols = sorted({r["symbol"] for r in kept})
    report["session_dates"] = session_dates
    report["n_session_dates"] = len(session_dates)
    report["symbols"] = symbols

    registry = ExposureRegistry(
        resolve_micro_exposure_registry_dir(CONFIG.dataset_dir_resolved())
    )
    far_future = "2999-01-01T00:00:00.000000Z"
    unexposed = [
        d for d in session_dates
        if not registry.is_exposed_before(
            corpus_id=wf.TICK_LEGACY_CORPUS_ID, window=d, instant=far_future
        )
    ]
    report["legacy_corpus_id"] = wf.TICK_LEGACY_CORPUS_ID
    report["session_dates_not_marked_exposed"] = unexposed
    report["evidence_class"] = wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC
    if unexposed:
        raise PreconditionFailed(
            f"STOP: {len(unexposed)} corpus session date(s) are NOT marked exposed under "
            f"{wf.TICK_LEGACY_CORPUS_ID!r}: {unexposed}. Study 2 discovery runs on the "
            "permanently-exposed legacy corpus only."
        )
    return report


def run(commit: bool) -> dict:
    dataset_store = indexed_dataset_store(CONFIG.dataset_dir_resolved(), DatasetStore)
    snapshots_dir = resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())
    ledger = ScoutLedger(scout.resolve_scout_ledger_dir(CONFIG.dataset_dir_resolved()))

    pre = verify_preconditions(ledger, dataset_store, snapshots_dir)
    out: dict = {"stage": "study2_diagnostic", "preconditions": pre, "committed": commit}
    if not commit:
        out["note"] = "DRY RUN -- preconditions verified; pass --commit to perform the ONE real run"
        return out

    request = dict(scout.pilot_study_candidate_grid(dataset_store, grid_version=1)[STUDY_ID])
    request["resolver"] = BandMapResolver(_bar_store(), CONFIG)
    out["candidate_request"] = {
        k: v for k, v in request.items()
        if k in ("feature_name", "transform", "params", "structure_context_kind", "horizon_key",
                 "sidedness", "fitting_rule", "grid_version", "withheld_excluded")
    }

    # ONE extraction. `anchors_sink` hands back the anchors the production path itself extracted,
    # AFTER the spec was frozen -- so the continuous report and the screened threshold variant
    # describe one identical body of evidence, and no outcome was read before registration.
    anchors: list[dict] = []
    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=CONFIG,
        anchors_sink=anchors, **request,
    )
    out["scout_row"] = {
        "row_index": row["row_index"], "candidate_id": row["candidate_id"],
        "spec_hash": row["spec_hash"], "family_id": row["family_id"],
        "registered_at": row["registered_at"], "decision": row["decision"],
        "reason": row["reason"], "notes": row["notes"],
        "screen_result": row["screen_result"], "withheld_excluded": row["withheld_excluded"],
    }
    out["diagnostic"] = s2.study2_diagnostic(anchors, screen=row)
    return out


def main() -> int:
    commit = "--commit" in sys.argv[1:]
    for arg in sys.argv[1:]:
        if arg != "--commit":
            print(f"unknown argument {arg!r}; usage: python -m scripts.study2_diagnostic [--commit]")
            return 2
    out = run(commit)
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
