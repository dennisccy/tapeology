"""Seed FOUR discriminating graduation families -- one per stage token, plus one PERMANENT failed
sealed verdict -- into a throwaway rig root, for J-11's browser-QA "four-stage" capture (Era "The
Rapid Microscope", goal-rapid-microscope-iter-32).

Before this iteration, the ONE non-empty graduation capture on record (``seed_micro_graduation_
iter18_fixture.py``) carried exactly ONE family, stopped at ``sealed_survivor`` via a genuine PASS.
That capture proved the pipe was not broken but could not discriminate a `walkforward_survivor`
render from a `sealed_survivor` one, could not show a permanent FAILED sealed verdict (spec section
7.4's "carried into every later export bundle" claim, TR-12), and could not show the
``referee_handoff_ready`` bundle copy line at all. This script closes that gap the SAME way every
other playbook/desk/graduation fixture in this ``scripts/`` directory does: it plants REAL records
through REAL production functions -- never a hand-rolled JSON blob standing in for one -- so a
browser screenshot of the seeded endpoint is genuine evidence, not a fabricated fixture dressed up
as a response.

**The four families, and how each one's ledger footprint is produced (all via REAL, unmodified
production functions -- ``micro_graduation.py``'s own state-advancing functions and
``micro_sealed_evaluation.evaluate_sealed_verdict``, never a hand-set ``passed``/``state`` field):**

- **Family A -- ``exploratory``.** ``evaluate_walkforward_survivor_transition`` is NEVER called for
  this family (the iteration spec's own words: "no walk-forward survivor transition attempted").
  A disclosed interpretation call (T-1): ``GET /research/desk/micro/graduation``'s
  ``list_graduation_families`` only lists a ``family_root_id`` that owns AT LEAST ONE graduation-
  ledger row of either kind (``state_transition`` OR ``sealed_evaluation`` -- confirmed by direct
  source read of that function's own docstring/loop), and ``"exploratory"`` is never itself a
  ``to_state`` value anywhere in ``micro_graduation.py`` (it is the module's own IMPLICIT default,
  read back by ``current_graduation_state`` only when NO ``state_transition`` row exists at all --
  never a fact this module ever appends). So a family visibly AT ``exploratory`` in the served list
  needs exactly one ``sealed_evaluation`` row and ZERO ``state_transition`` rows -- a sequence the
  code fully permits: ``evaluate_sealed_verdict``/``record_sealed_evaluation`` carry NO
  ``walkforward_survivor`` precondition of their own (only ``evaluate_sealed_survivor_transition``
  enforces state ordering, confirmed by direct source read of all three functions). This script
  therefore calls the REAL ``evaluate_sealed_verdict`` for Family A with 29 real observations --
  ONE short of ``SEALED_MIN_OBSERVATIONS`` = 30, the sealed stage's own r9/TR-30 sufficiency floor
  -- producing a genuine ``verdict == "insufficient"`` row (T-7: "insufficient is an answer";
  never PASS, never FAIL, never advances state) while never once calling
  ``evaluate_walkforward_survivor_transition``, exactly as scoped.
- **Family B -- ``walkforward_survivor``, carrying one PERMANENT FAILED sealed evaluation.** Three
  real, already-``sufficient`` walk-forward fold rows (via ``walkforward_ledger.append_fold_result``
  -- the ``test_micro_graduation.py``/``test_walkforward.py`` "hand-built, ledgered-but-not-
  re-deriving-the-producer's-own-machinery" style for testing a graduation CONSUMER in isolation,
  mirrored here for a fixture script instead of a test) advance it to ``walkforward_survivor`` via
  the REAL ``evaluate_walkforward_survivor_transition``. Then the REAL ``evaluate_sealed_verdict``
  is called with 30 real observations whose recomputed mean effect (1.0) is POSITIVE (the correct
  registered direction) but strictly below the family's own 5.0 bps registered econ floor -- so the
  RECOMPUTED verdict is a genuine ``"fail"`` (``failure_reason == "below_economic_floor"``), never a
  hand-set field (mirrors ``test_micro_graduation.py::test_tc6_a_failed_sealed_evaluation_never_
  advances_and_is_carried_into_the_bundle``'s SHAPE, extended here to call the REAL evaluator that
  test's own hand-built ``_sealed_artifact`` helper stands in for). ``evaluate_sealed_survivor_
  transition`` is deliberately never called for Family B, so its state stays permanently
  ``walkforward_survivor`` -- the failed verdict is carried on record, never advancing anything.
- **Family C -- ``sealed_survivor``.** Same walk-forward-survivor setup as Family B (its own,
  distinct corpus/sequence), then a genuine PASSING sealed evaluation (30 real observations, mean
  effect 10.0, clearing the 5.0 bps floor) against its OWN, DISTINCT vault shard (never Family B's),
  then the REAL ``evaluate_sealed_survivor_transition``.
- **Family D -- ``referee_handoff_ready``.** Identical to Family C's own path, then the REAL
  ``evaluate_referee_handoff_ready_transition`` -- which builds the export bundle and requires it to
  VALIDATE before recording the transition, mirroring ``test_micro_graduation.py::test_tc3_and_
  tc4_the_full_pipeline_produces_a_validating_bundle_and_referee_handoff_ready``. Its bundle's
  ``referee_registration_note`` therefore carries ``micro_graduation.REFEREE_FUTURE_REVISION_
  SENTENCE`` verbatim -- the SAME string the frontend's ``GRADUATION_REFEREE_HANDOFF_NOTE`` constant
  already quotes byte-for-byte (iter-31), rendered whenever a served family's ``state`` reads
  ``"referee_handoff_ready"``.

**Idempotent-replay-safe (TC-6, TR-30's own "replayed, not duplicated" discipline extended to this
script's own upstream store writes).** ``micro_graduation.py``'s own state-advancing functions
already check first and return ``{"transition": "replayed", ...}`` on an identical re-attempt --
that discipline is reused UNCHANGED here. ``DatasetStore.record``/``vault.seal_shard``/
``vault.assign_shard``/``vault.expose_shard`` carry NO such built-in replay branch of their own
(each refuses outright -- ``DatasetAlreadyRegistered``/``ShardLifecycleOrderError`` -- on a second
call against content or a shard already on record); this script supplies that idempotency AT THE
CALL SITE (``_plant_dataset_and_snapshot``'s ``except DatasetAlreadyRegistered`` reuse,
``_idempotent_seal_assign_expose``'s three ``except ShardLifecycleOrderError: pass`` guards) rather
than touching either module (OUT OF SCOPE) -- catching EXACTLY the one exception each step raises
when its own precondition is already satisfied by a prior run, never swallowing any other failure.
A second run against the SAME scoped root therefore appends NO new row anywhere and still exits 0.

**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
``root`` argument's own directory tree (``root/datasets``, sibling ``micro_snapshots``/
``micro_vault``/``micro_graduation`` directories via each module's own ``resolve_*_dir`` -- no env
var is set BY this script, so a caller who ALSO wants ``TAPEOLOGY_MICRO_GRADUATION_DIR`` pointed at
``root/micro_graduation`` for a scoped backend to serve sets it themselves, exactly matching
``resolve_micro_graduation_dir``'s own "SIBLING of the dataset directory, unless overridden" default
-- this script contains no fallback to an unscoped default path). **Never a production code path
change** -- this script imports and calls the SAME ``evaluate_sealed_verdict``/``evaluate_
walkforward_survivor_transition``/``evaluate_sealed_survivor_transition``/``evaluate_referee_
handoff_ready_transition``/``DatasetStore.record``/``vault.*`` functions the shipped product uses;
it adds no new module, no new endpoint, no new branch inside any of them.

Usage::

    .venv/bin/python scripts/seed_micro_graduation_iter32_fourstage_fixture.py ROOT

Exits 0 only if all four families land in their target state (and Family A's/Family B's own sealed
verdicts read ``insufficient``/``fail`` respectively); prints a ``MISMATCH`` line naming exactly
which family/state/verdict diverged otherwise -- a silently-wrong fixture must never be reported as
a passing seed.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

from app.config import CONFIG  # noqa: E402
from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
from app.research import micro_graduation as g  # noqa: E402
from app.research import micro_sealed_evaluation as sealed_eval  # noqa: E402
from app.research import scout_ledger  # noqa: E402
from app.research import vault  # noqa: E402
from app.research import walkforward as wf  # noqa: E402
from app.research import walkforward_ledger as wl  # noqa: E402
from app.research.datasets import DatasetAlreadyRegistered, DatasetStore  # noqa: E402
from app.research.micro_accessor import MicroAccessor  # noqa: E402
from app.research.micro_snapshots import (  # noqa: E402
    build_snapshot_rows,
    resolve_micro_snapshots_dir,
    snapshot_identity,
    write_snapshot,
)
from app.research.scout_ledger import ScoutLedger  # noqa: E402

_ECON_FLOOR = {"floor_bps": 5.0}
_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter32-qa-only-fourstage-fixture-vault-secret"

_SEALED_AT = "2026-05-01T00:00:00.000000Z"
_SPEC_REGISTERED_AT = "2026-06-01T00:00:00.000000Z"  # strictly BEFORE _ASSIGNED_AT below
_ASSIGNED_AT = "2026-06-05T00:00:00.000000Z"
_EXPOSED_AT = "2026-06-06T00:00:00.000000Z"
_SEALED_EVALUATED_AT = "2026-06-10T00:00:00.000000Z"

_WF_REGISTERED_AT = "2026-01-01T00:00:00.000000Z"
_WF_EVALUATED_AT = "2026-01-15T00:00:00.000000Z"

_WINDOW_START_UTC = "2026-06-09T13:00:00Z"
_WINDOW_END_UTC = "2026-06-09T13:01:00Z"
_SESSION_DATE = "2026-06-09"

_UNIVERSE_ID = "goal-rapid-microscope-iter32-qa-universe"
_WF_RULE_ID = "iter32-fourstage-fixture-rule"


# === real trade/quote + observation fixtures (the iter18 script's own shapes, mirrored) =============


def _events_for_store(symbol: str) -> list:
    """A tiny, REAL trade/quote sequence per symbol -- the ``seed_micro_graduation_iter18_
    fixture.py`` ``_events_for_store`` shape, mirrored verbatim (never re-derived)."""
    return [
        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(symbol, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
        TradeEvent(symbol, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
    ]


def _observation(session_date: str, symbol: str, value: float) -> dict:
    return {"session_date": session_date, "symbol": symbol, "value": value}


def _passing_observations(session_date: str, symbol: str) -> list[dict]:
    """30 real observations symmetric around 10.0 -- clears ``_ECON_FLOOR``'s 5.0 bps floor in the
    "long"/positive direction (``test_micro_sealed_evaluation.py``'s own ``_passing_observations``,
    mirrored)."""
    values = [10.0 + (i - 14.5) for i in range(30)]
    return [_observation(session_date, symbol, v) for v in values]


def _below_floor_observations(session_date: str, symbol: str) -> list[dict]:
    """30 real observations, mean effect 1.0 -- POSITIVE (correct direction) but strictly below the
    5.0 bps econ floor, so it FAILS on magnitude alone, never on direction (``test_micro_sealed_
    evaluation.py``'s own ``_below_floor_observations``, mirrored) -- deliberately a DIFFERENT
    numeric value from ``_passing_observations``'s own 10.0, never coincidentally equal."""
    values = [1.0 + (i - 14.5) for i in range(30)]
    return [_observation(session_date, symbol, v) for v in values]


def _insufficient_observations(session_date: str, symbol: str) -> list[dict]:
    """29 real observations -- ONE short of ``SEALED_MIN_OBSERVATIONS`` = 30, the ONLY sufficiency
    floor at shard scope (r9/TR-30). A strict prefix of ``_passing_observations``, never a second,
    differently-shaped fixture."""
    return _passing_observations(session_date, symbol)[:29]


# === idempotent-replay-safe upstream store writes (module docstring) ================================


def _plant_dataset_and_snapshot(
    dataset_store: DatasetStore, snapshots_dir: str, *, symbol: str, source_id: str,
) -> dict:
    """Plants (or, on a second run against the SAME root, reuses) ONE real dataset + REAL feature
    snapshot -- REAL production functions throughout, never a hand-rolled JSON blob."""
    try:
        dataset_meta = dataset_store.record(
            symbol=symbol, source="fixture", source_kind="fixture", source_id=source_id,
            split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
            data_feed="sip", epoch_anchor=0.0, events=_events_for_store(symbol),
        )
    except DatasetAlreadyRegistered as exc:
        dataset_meta = dataset_store.get(exc.existing_id)
    dataset_id = dataset_meta["id"]
    rows = build_snapshot_rows(dataset_store, dataset_id, CONFIG, quote_size_unit="unverified")
    identity = snapshot_identity(dataset_meta, CONFIG)
    write_snapshot(snapshots_dir, dataset_id, rows, {**identity, "quote_size_unit": "unverified"})
    return dataset_meta


def _idempotent_seal_assign_expose(
    shard_ledger: "vault.VaultShardLedger", *, dataset_id: str, family_root_id: str,
    symbol: str, session_date: str, content_checksum: str, event_count: int,
) -> None:
    """seal -> assign -> expose ONE real vault shard, tolerating a repeat run against the SAME
    root. Unlike ``micro_graduation.py``'s own state-advancing functions, ``seal_shard``/
    ``assign_shard``/``expose_shard`` carry NO built-in "already there -> replayed" branch of their
    own (each refuses outright -- ``ShardLifecycleOrderError`` -- when called a second time against
    a shard already past that lifecycle step). This helper supplies that idempotent-replay
    discipline AT THE CALL SITE instead of touching ``vault.py`` (OUT OF SCOPE)."""
    try:
        vault.seal_shard(
            shard_ledger, dataset_id=dataset_id, universe_id=_UNIVERSE_ID,
            content_checksum=content_checksum, event_count=event_count,
            vault_secret=_FIXTURE_VAULT_SECRET, sealed_at=_SEALED_AT,
        )
    except vault.ShardLifecycleOrderError:
        pass  # already sealed (or beyond) on a prior run
    try:
        vault.assign_shard(
            shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
            symbol=symbol, session_date=session_date, assigned_at=_ASSIGNED_AT,
        )
    except vault.ShardLifecycleOrderError:
        pass  # already assigned (or beyond) on a prior run
    try:
        vault.expose_shard(
            shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id, exposed_at=_EXPOSED_AT,
        )
    except vault.ShardLifecycleOrderError:
        pass  # already exposed on a prior run


def _candidate_spec(*, family_root_id: str, spec_hash: str, candidate_id: str, family_id: str) -> dict:
    return {
        "family_root_id": family_root_id,
        "candidate_id": candidate_id,
        "family_id": family_id,
        "spec_hash": spec_hash,
        "sidedness": "long",
        "econ_floor": _ECON_FLOOR,
        "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS,
        "process_label": wf.PROCESS_LABEL_RULE,
        "registered_at": _SPEC_REGISTERED_AT,
        "sealed_pass_rule_hash": sealed_eval.sealed_pass_rule_hash(),
        # (r9) deliberately NO "floors" key -- the QA seed exercises the real, evaluator-owned
        # sufficiency rule, never the retired caller-override shortcut.
    }


def _append_sufficient_fold(
    wf_ledger: "wl.WalkForwardLedger", *, fold_index: int, sequence_id: str, corpus_id: str, spec_hash: str,
) -> dict:
    """A hand-built, already-SUFFICIENT ``fold_result``-shaped row, appended through the REAL
    ``walkforward_ledger.append_fold_result`` -- the ``test_micro_graduation.py``/``test_
    walkforward.py`` "hand-built, ledgered-but-not-re-deriving-the-producer's-own-machinery" style,
    mirrored here for a fixture script rather than a test. ``append_fold_result`` is itself
    idempotent-replay-safe (keyed on ``sequence_id``/``fold_index``/``spec_hash``), so this needs no
    extra guard of its own."""
    fields = {
        "sequence_id": sequence_id, "corpus_id": corpus_id, "mode": "B", "rule_id": _WF_RULE_ID,
        "spec_hash": spec_hash, "fold_index": fold_index, "sidedness": "long", "econ_floor": _ECON_FLOOR,
        "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_OOS, "process_label": wf.PROCESS_LABEL_RULE,
        "registered_at": _WF_REGISTERED_AT, "status": wf.FOLD_STATUS_SUFFICIENT, "n": 40,
        "n_sessions": 10, "n_symbols": 3, "effect": 10.0, "sign": "positive", "missing": {},
    }
    return wl.append_fold_result(wf_ledger, fields)


def _three_survivor_folds(wf_ledger: "wl.WalkForwardLedger", *, sequence_id: str, corpus_id: str, spec_hash: str) -> None:
    for i in range(wf.WF_MIN_SUFFICIENT_FOLDS):
        _append_sufficient_fold(wf_ledger, fold_index=i, sequence_id=sequence_id, corpus_id=corpus_id, spec_hash=spec_hash)


# === the four families ===============================================================================


def _seed_family_a(grad_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor) -> tuple[str, str]:
    """Family A -- stays ``exploratory`` forever (module docstring's own disclosed interpretation
    call): one real, INSUFFICIENT sealed evaluation, zero walk-forward-survivor transitions ever
    attempted."""
    family_root_id = scout_ledger.compute_family_root_id(
        "quote_imbalance_persistence_iter32qa", "band_wall_touch", "trades_20",
    )
    symbol = "MQ32A"
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol=symbol,
        source_id="goal-rapid-microscope-iter32-qa-family-a",
    )
    dataset_id = dataset_meta["id"]
    _idempotent_seal_assign_expose(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
        symbol=symbol, session_date=_SESSION_DATE, content_checksum=dataset_meta["checksum"],
        event_count=len(_events_for_store(symbol)),
    )
    candidate_spec = _candidate_spec(
        family_root_id=family_root_id, spec_hash="iter32-qa-spec-hash-a",
        candidate_id="iter32-qa-candidate-a", family_id="iter32-qa-family-a",
    )
    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_id,
        observations=_insufficient_observations(_SESSION_DATE, symbol), evaluated_at=_SEALED_EVALUATED_AT,
    )
    return family_root_id, result["row"]["verdict"]


def _seed_family_b(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor) -> tuple[str, str, str]:
    """Family B -- ``walkforward_survivor``, carrying one PERMANENT FAILED sealed evaluation."""
    family_root_id = scout_ledger.compute_family_root_id(
        "response_asymmetry_iter32qa", "band_wall_touch", "trades_20",
    )
    corpus_id = "goal-rapid-microscope-iter32-corpus-b"
    sequence_id = wf.sequence_id_for(corpus_id, _WF_RULE_ID)
    spec_hash = "iter32-qa-spec-hash-b"
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id, spec_hash=spec_hash)
    g.evaluate_walkforward_survivor_transition(
        grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
        evaluated_at=_WF_EVALUATED_AT,
    )

    symbol = "MQ32B"
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol=symbol,
        source_id="goal-rapid-microscope-iter32-qa-family-b",
    )
    dataset_id = dataset_meta["id"]
    _idempotent_seal_assign_expose(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
        symbol=symbol, session_date=_SESSION_DATE, content_checksum=dataset_meta["checksum"],
        event_count=len(_events_for_store(symbol)),
    )
    candidate_spec = _candidate_spec(
        family_root_id=family_root_id, spec_hash=spec_hash,
        candidate_id="iter32-qa-candidate-b", family_id="iter32-qa-family-b",
    )
    result = sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_id,
        observations=_below_floor_observations(_SESSION_DATE, symbol), evaluated_at=_SEALED_EVALUATED_AT,
    )
    state = g.current_graduation_state(grad_ledger, family_root_id)
    return family_root_id, state, result["row"]["verdict"]


def _seed_family_c(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor) -> str:
    """Family C -- ``sealed_survivor``, via a genuine PASS on its OWN, DISTINCT shard (never Family
    B's)."""
    family_root_id = scout_ledger.compute_family_root_id(
        "microprice_drift_iter32qa", "band_wall_touch", "trades_20",
    )
    corpus_id = "goal-rapid-microscope-iter32-corpus-c"
    sequence_id = wf.sequence_id_for(corpus_id, _WF_RULE_ID)
    spec_hash = "iter32-qa-spec-hash-c"
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id, spec_hash=spec_hash)
    g.evaluate_walkforward_survivor_transition(
        grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
        evaluated_at=_WF_EVALUATED_AT,
    )

    symbol = "MQ32C"
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol=symbol,
        source_id="goal-rapid-microscope-iter32-qa-family-c",
    )
    dataset_id = dataset_meta["id"]
    _idempotent_seal_assign_expose(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
        symbol=symbol, session_date=_SESSION_DATE, content_checksum=dataset_meta["checksum"],
        event_count=len(_events_for_store(symbol)),
    )
    candidate_spec = _candidate_spec(
        family_root_id=family_root_id, spec_hash=spec_hash,
        candidate_id="iter32-qa-candidate-c", family_id="iter32-qa-family-c",
    )
    sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_id,
        observations=_passing_observations(_SESSION_DATE, symbol), evaluated_at=_SEALED_EVALUATED_AT,
    )
    g.evaluate_sealed_survivor_transition(
        grad_ledger, family_root_id=family_root_id, dataset_id=dataset_id, evaluated_at=_SEALED_EVALUATED_AT,
    )
    return family_root_id


def _seed_family_d(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor, scout) -> str:
    """Family D -- ``referee_handoff_ready``, via a validating export bundle (``test_micro_
    graduation.py::test_tc3_and_tc4_...`` mirrored)."""
    family_root_id = scout_ledger.compute_family_root_id(
        "impact_efficiency_trend_iter32qa", "band_wall_touch", "trades_20",
    )
    corpus_id = "goal-rapid-microscope-iter32-corpus-d"
    sequence_id = wf.sequence_id_for(corpus_id, _WF_RULE_ID)
    spec_hash = "iter32-qa-spec-hash-d"
    _three_survivor_folds(wf_ledger, sequence_id=sequence_id, corpus_id=corpus_id, spec_hash=spec_hash)
    g.evaluate_walkforward_survivor_transition(
        grad_ledger, wf_ledger, family_root_id=family_root_id, sequence_id=sequence_id,
        evaluated_at=_WF_EVALUATED_AT,
    )

    symbol = "MQ32D"
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol=symbol,
        source_id="goal-rapid-microscope-iter32-qa-family-d",
    )
    dataset_id = dataset_meta["id"]
    _idempotent_seal_assign_expose(
        shard_ledger, dataset_id=dataset_id, family_root_id=family_root_id,
        symbol=symbol, session_date=_SESSION_DATE, content_checksum=dataset_meta["checksum"],
        event_count=len(_events_for_store(symbol)),
    )
    candidate_spec = _candidate_spec(
        family_root_id=family_root_id, spec_hash=spec_hash,
        candidate_id="iter32-qa-candidate-d", family_id="iter32-qa-family-d",
    )
    sealed_eval.evaluate_sealed_verdict(
        grad_ledger, shard_ledger, universe_ledger, accessor,
        candidate_spec=candidate_spec, dataset_id=dataset_id,
        observations=_passing_observations(_SESSION_DATE, symbol), evaluated_at=_SEALED_EVALUATED_AT,
    )
    g.evaluate_sealed_survivor_transition(
        grad_ledger, family_root_id=family_root_id, dataset_id=dataset_id, evaluated_at=_SEALED_EVALUATED_AT,
    )
    g.evaluate_referee_handoff_ready_transition(
        grad_ledger, scout, wf_ledger, shard_ledger, universe_ledger,
        family_root_id=family_root_id, sequence_id=sequence_id, evaluated_at=_SEALED_EVALUATED_AT,
    )
    return family_root_id


def _check(label: str, family_root_id: str, actual_state: str, expected_state: str, actual_verdict: str, expected_verdict: str) -> bool:
    ok = actual_state == expected_state and actual_verdict == expected_verdict
    tag = "ok" if ok else "MISMATCH"
    print(
        f"[seed-micro-graduation-iter32] family {label} ({family_root_id}) -> "
        f"state={actual_state!r} verdict={actual_verdict!r} [{tag}]",
        file=sys.stderr,
    )
    if not ok:
        print(
            f"[seed-micro-graduation-iter32] {tag}: family {label} expected "
            f"state={expected_state!r} verdict={expected_verdict!r}",
            file=sys.stderr,
        )
    return ok


def main(root: Path) -> int:
    dataset_dir = root / "datasets"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_store = DatasetStore(dataset_dir)
    snapshots_dir = resolve_micro_snapshots_dir(str(dataset_dir))
    graduation_dir = g.resolve_micro_graduation_dir(str(dataset_dir))
    vault_dir = vault.resolve_vault_dir(str(dataset_dir))

    grad_ledger = g.GraduationLedger(graduation_dir)
    wf_ledger = wl.WalkForwardLedger(str(root / "walkforward"))
    shard_ledger = vault.VaultShardLedger(vault_dir)
    universe_ledger = vault.VaultUniverseLedger(vault_dir)
    accessor = MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    scout = ScoutLedger(str(root / "scout"))

    ok = True

    family_a, verdict_a = _seed_family_a(grad_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor)
    state_a = g.current_graduation_state(grad_ledger, family_a)
    ok &= _check(
        "A", family_a, state_a, g.GRADUATION_STATE_EXPLORATORY,
        verdict_a, sealed_eval.SEALED_VERDICT_INSUFFICIENT,
    )

    family_b, state_b, verdict_b = _seed_family_b(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor)
    ok &= _check(
        "B", family_b, state_b, g.GRADUATION_STATE_WALKFORWARD_SURVIVOR,
        verdict_b, sealed_eval.SEALED_VERDICT_FAIL,
    )

    family_c = _seed_family_c(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor)
    state_c = g.current_graduation_state(grad_ledger, family_c)
    sealed_c = g.sealed_evaluations_for_family(grad_ledger, family_c)
    verdict_c = sealed_c[-1]["verdict"] if sealed_c else None
    ok &= _check(
        "C", family_c, state_c, g.GRADUATION_STATE_SEALED_SURVIVOR,
        verdict_c, sealed_eval.SEALED_VERDICT_PASS,
    )

    family_d = _seed_family_d(grad_ledger, wf_ledger, dataset_store, snapshots_dir, shard_ledger, universe_ledger, accessor, scout)
    state_d = g.current_graduation_state(grad_ledger, family_d)
    sealed_d = g.sealed_evaluations_for_family(grad_ledger, family_d)
    verdict_d = sealed_d[-1]["verdict"] if sealed_d else None
    ok &= _check(
        "D", family_d, state_d, g.GRADUATION_STATE_REFEREE_HANDOFF_READY,
        verdict_d, sealed_eval.SEALED_VERDICT_PASS,
    )

    if not ok:
        print(
            "[seed-micro-graduation-iter32] ERROR: one or more families did not land in their "
            "target state/verdict -- see MISMATCH lines above",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
