"""Seed a scoped walk-forward ledger that carries BOTH unit conventions in one sequence — the
browser fixture for the r13-completion legacy-unit disclosure.

One sequence, two sufficient folds:

  * fold 0 — a **pre-r13** row: a PERCENT magnitude and **no ``unit`` key at all**, exactly as the
    real ledger's own folds 3 and 4 are persisted on disk. It must serve and display as
    ``legacy_percent`` with its magnitude verbatim, never as basis points.
  * fold 1 — an **r13** row: ``return_bps``, declared by the writer.

Rendering them side by side in the same table is the point: a single column header cannot be
truthful for both, which is why each row prints its own served unit.

Writes ONLY into the scoped root it is given. Consumes no vault shard, touches no real store, and
never rewrites an append-only ledger — it seeds a fresh one.

    TAPEOLOGY_DATASET_DIR=<root>/datasets \\
        .venv/bin/python -m scripts.seed_micro_walkforward_unit_disclosure_fixture
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import CONFIG  # noqa: E402
from app.research import walkforward as wf  # noqa: E402
from app.research.walkforward_ledger import (  # noqa: E402
    WalkForwardLedger,
    append_fold_result,
    register_fold_spec,
)

CORPUS_ID = "r13_unit_disclosure_fixture_v1"
SEQUENCE_ID = "seq-r13-unit-disclosure"
SPEC_HASH = "r13unitdisclosurefixturespechash0000000000000000000000000000000000"

_ECON_FLOOR = {
    "multiple": 1.0,
    "family_median_spread_bps": 2.0,
    "floor_bps": 2.0,
    "unit": "bps",
    "proxy_sentence": "quoted spread is a research cost proxy, not a full execution or tradability model",
}


def _base_row(fold_index: int) -> dict:
    return {
        "sequence_id": SEQUENCE_ID,
        "corpus_id": CORPUS_ID,
        "mode": "B",
        "fitting_rule": None,
        "rule_id": "r13_unit_disclosure_fixture:demo",
        "spec_hash": SPEC_HASH,
        "fold_index": fold_index,
        "sidedness": "long",
        "econ_floor": _ECON_FLOOR,
        "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
        "process_label": wf.PROCESS_LABEL_RULE,
        "registered_at": "2026-08-25T00:00:00.000000Z",
        "status": wf.FOLD_STATUS_SUFFICIENT,
        "n": 330,
        "n_sessions": 20,
        "n_symbols": 94,
        "missing": {},
    }


def main() -> int:
    ledger_dir = wf.resolve_walkforward_ledger_dir(CONFIG.dataset_dir_resolved())
    ledger = WalkForwardLedger(ledger_dir)

    register_fold_spec(
        ledger,
        corpus_id=CORPUS_ID,
        corpus_manifest_hash="r13-unit-disclosure-fixture-manifest",
        geometry=dict(wf.DIAGNOSTIC_GEOMETRY),
        clustering_unit="session_date",
        floors={
            "wf_fold_min_observations": wf.WF_FOLD_MIN_OBSERVATIONS,
            "wf_fold_min_signal_sessions": wf.WF_FOLD_MIN_SIGNAL_SESSIONS,
            "wf_fold_min_symbols": wf.WF_FOLD_MIN_SYMBOLS,
        },
        registered_at="2026-08-25T00:00:00.000000Z",
    )

    # fold 0 -- PRE-r13: percent magnitude, NO `unit` key (the real ledger's own shape on disk).
    legacy = _base_row(0)
    legacy["effect"] = 0.019176079727258294
    legacy["sign"] = "positive"
    append_fold_result(ledger, legacy)

    # fold 1 -- r13: the canonical unit, declared by the writer.
    current = _base_row(1)
    current["effect"] = 25.0
    current["unit"] = wf.WF_OBSERVATION_UNIT
    current["sign"] = "positive"
    append_fold_result(ledger, current)

    served = wf.list_walkforward_sequences(ledger)[0]
    units = [row["unit"] for row in served["decay_view"]["fold_rows"]]
    print(f"[seed-r13-unit-disclosure] ledger={ledger_dir}")
    print(f"[seed-r13-unit-disclosure] served fold units: {units}")
    if units != [wf.LEGACY_WF_EFFECT_UNIT, wf.WF_OBSERVATION_UNIT]:
        print("[seed-r13-unit-disclosure] MISMATCH: expected "
              f"[{wf.LEGACY_WF_EFFECT_UNIT!r}, {wf.WF_OBSERVATION_UNIT!r}]")
        return 1
    verdict = served["sequence_verdict"]
    print(f"[seed-r13-unit-disclosure] sequence_verdict.refused={verdict.get('refused')} "
          f"reason={str(verdict.get('reason'))[:80]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
