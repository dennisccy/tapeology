"""Plants a real pilot-study Scout Ledger row for J-09's stored golden replay (era "The Rapid
Microscope", goal-rapid-microscope-iter-24).

**Why this exists.** ``journey-scripts/J-09.json`` is a pure browser-action replay script
(``goto``/``click``/``expect`` only -- ``demo_runner.py`` has no raw-HTTP action type), so it
cannot itself issue the ``POST /research/desk/micro/scout/compute`` call that would trigger a
pilot-study screen, and the ``/desk`` frontend's own Scout compute button sends only the default
reference grid (no UI control selects a pilot grid). This script is the one-time fixture-seeding
act the iteration plan calls for: it plants a genuine, non-vacuous Study-3
(``capitulation_exhaustion_pilot``) Scout Ledger row through the REAL production entry point
(``scout.register_screen_and_walkforward_check`` -- never a hand-rolled JSON blob), so the
resulting row is already on disk when the golden replay's ``goto``/``click``/``expect`` steps run
against the scoped QA rig. Mirrors the ``seed_micro_graduation_iter18_fixture.py`` precedent
(J-07/``micro_graduation.py``), applied here to J-09/``scout.py``.

**What this plants.** ONE real ``setup_id="capitulation"`` playbook signal -- the SAME
``_plant_capitulation_signal(tmp_path, dataset_meta=...)`` shape ``tests/test_scout.py``'s own
``test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`` already proves
produces a genuine, non-vacuous screen -- anchored on the FIRST already-staged real PG SIP tick
dataset this rig's own ``qa_playbook_iter7_fixture_scoped_backend.sh`` copies into
``$ROOT/datasets`` BEFORE any seeder runs (never a second, synthetic dataset: the real committed
historical PG fixture is the exact same, already-proven-workable anchor target
``tests/test_scout.py``'s own ``pg_snapshot_store`` fixture uses). Then calls
``scout.register_screen_and_walkforward_check`` for real (Study 3's own frozen request from
``scout.pilot_study_candidate_grid``), writing through the SAME scout ledger dir
``GET /research/desk/micro/scout`` reads from when the scoped backend serves the same
``TAPEOLOGY_DATASET_DIR``.

**Never touches the real ``.data`` store.** Every directory this script writes to is derived from
the ``root`` argument's own ``TAPEOLOGY_DATASET_DIR``-relative resolvers
(``resolve_scout_ledger_dir``, ``resolve_micro_exposure_registry_dir``,
``resolve_micro_snapshots_dir`` -- the SAME sibling-of-dataset-dir defaults every other era module
uses, and the SAME ones ``GET /research/desk/micro/scout`` resolves when it serves this rig); the
rig's playbook store path (``TAPEOLOGY_DESK_PLAYBOOK_DIR``, already exported by the launcher) is
reused verbatim, not re-derived, so the signal this script plants and the one the served ``/desk``
Playbook section reads are the SAME store.

Uses a distinct ``playbook_input_signature``
(``"goal-rapid-microscope-iter24-j09-capitulation-pilot"``) so this signal can never collide with
anything ``seed_playbook_iter8_replay_rig.py`` or any other seed script in this rig already
planted -- ``PlaybookStore.record``'s own duplicate-key discipline is keyed on
``(session_date, playbook_input_signature)``, never on ``setup_id`` alone: multiple signals
coexist at the same session date routinely (``_plant_capitulation_signal``'s own two-signal test
in ``tests/test_scout.py`` proves exactly this).

**Never a production code path change.** This script imports and calls the SAME
``scout.register_screen_and_walkforward_check``/``PlaybookStore.record``/
``run_snapshot_build_and_record`` functions the shipped product uses; it adds no new module, no
new endpoint, no new branch inside any of them.

Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports
``TAPEOLOGY_DATASET_DIR``/``TAPEOLOGY_DESK_PLAYBOOK_DIR``/``TAPEOLOGY_DESK_UNIVERSE_DIR`` first,
AFTER the PG tick fixtures are copied and after the other seed scripts have run):

    TAPEOLOGY_DATASET_DIR=... TAPEOLOGY_DESK_PLAYBOOK_DIR=... \\
      .venv/bin/python scripts/seed_micro_scout_iter24_j09_fixture.py ROOT
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR.parent))

from app.config import CONFIG  # noqa: E402
from app.research import scout  # noqa: E402
from app.research.datasets import DatasetStore, parse_utc_epoch  # noqa: E402
from app.research.desk_playbook import PlaybookStore, playbook_parameters  # noqa: E402
from app.research.desk_playbook import resolve_desk_playbook_dir  # noqa: E402
from app.research.micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir  # noqa: E402
from app.research.micro_snapshots import resolve_micro_snapshots_dir, run_snapshot_build_and_record  # noqa: E402
from app.research.scout_ledger import ScoutLedger, resolve_scout_ledger_dir  # noqa: E402

_PLAYBOOK_INPUT_SIGNATURE = "goal-rapid-microscope-iter24-j09-capitulation-pilot"
_ET_ZONE = ZoneInfo("America/New_York")


def _session_date_of(dataset_meta: dict) -> str:
    """The dataset's ET session date, derived from its own recorded window -- the
    ``j06_operator._session_date_of`` shape, mirrored (never re-derived from a hardcoded guess)."""
    start = datetime.fromisoformat(dataset_meta["window_start_utc"].replace("Z", "+00:00"))
    return start.astimezone(_ET_ZONE).date().isoformat()


def _first_real_pg_dataset(dataset_store: DatasetStore) -> dict:
    """The FIRST already-staged real PG SIP tick dataset this rig's launcher copies into
    ``$ROOT/datasets`` before any seeder runs -- the SAME real committed fixture
    ``tests/test_scout.py``'s own ``pg_snapshot_store`` fixture reads (never a second, synthetic
    dataset). Sorted by id for a deterministic pick across repeated rig launches."""
    records, _errors = dataset_store.list()
    pg = sorted((r for r in records if r["symbol"] == "PG"), key=lambda r: r["id"])
    if not pg:
        raise SystemExit(
            "[seed-micro-scout-iter24-j09] no PG dataset found in the dataset store -- this "
            "seeder must run AFTER the rig's own PG SIP tick-fixture copy step, never before it"
        )
    return pg[0]


def _plant_capitulation_signal(playbook_dir: str, *, dataset_meta: dict) -> PlaybookStore:
    """ONE real ``setup_id="capitulation"`` playbook signal, ``trigger_ts`` inside
    ``dataset_meta``'s own window -- the ``tests/test_scout.py`` ``_plant_capitulation_signal``
    shape, mirrored, against the RIG's own playbook store dir rather than a throwaway
    ``tmp_path``, with ONE deliberate addition: ``"side": "long"``.

    ``_plant_capitulation_signal`` itself omits ``side`` (harmless for its own callers -- Scout's
    ``join_playbook_signal`` never reads it), but a REAL ``detect_capitulation`` signal always
    carries it (``desk_playbook_detect.py``'s own ``"capitulation entry, long only"`` -- every
    real signal dict is built with ``"side": "long"`` verbatim, never omitted). This rig's own
    ``/research/desk/referee/registry/shortlist`` route reads EVERY playbook signal at the live
    detector basis (``referee_evidence.playbook_occurrence_readiness``, keyed on
    ``(setup_id, side)``) -- discovered live while wiring this seeder in: a signal missing
    ``side`` 500s that route with ``KeyError: 'side'``, breaking J-10's own Referee Registry step.
    Adding the ONE field a genuine signal always carries closes that gap without touching
    ``referee_evidence.py`` (a frozen module this era) at all."""
    playbook_store = PlaybookStore(playbook_dir)
    window_start_epoch = parse_utc_epoch(dataset_meta["window_start_utc"])
    trigger_dt = datetime.fromtimestamp(window_start_epoch + 5.0, tz=timezone.utc)
    trigger_ts = trigger_dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
    playbook_store.record(
        session_date=_session_date_of(dataset_meta),
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=_PLAYBOOK_INPUT_SIGNATURE,
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=[
            {
                "symbol": dataset_meta["symbol"], "setup_id": "capitulation", "side": "long",
                "trigger_ts": trigger_ts,
            },
        ],
        absences=[], diagnostics=[],
    )
    return playbook_store


def main(root: Path) -> int:
    dataset_dir = root / "datasets"
    dataset_store = DatasetStore(dataset_dir)
    dataset_meta = _first_real_pg_dataset(dataset_store)
    print(
        f"[seed-micro-scout-iter24-j09] anchoring on real PG dataset {dataset_meta['id']} "
        f"({dataset_meta['symbol']} / {dataset_meta['window_start_utc']})", file=sys.stderr,
    )

    # --- ensure prerequisite feature snapshots exist (the CLI's own `main()` does this first) ------
    snapshots_dir = resolve_micro_snapshots_dir(str(dataset_dir))
    run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, None)

    # --- plant ONE real capitulation playbook signal, into the RIG's own playbook store -----------
    playbook_dir = os.environ.get("TAPEOLOGY_DESK_PLAYBOOK_DIR") or resolve_desk_playbook_dir(
        str(root / "universe")
    )
    playbook_store = _plant_capitulation_signal(playbook_dir, dataset_meta=dataset_meta)
    print(f"[seed-micro-scout-iter24-j09] planted capitulation signal at {playbook_dir}", file=sys.stderr)

    # --- register+screen Study 3's frozen request, THEN its walk-forward floor check, for real ----
    request = scout.pilot_study_candidate_grid(dataset_store)[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
    ledger = ScoutLedger(resolve_scout_ledger_dir(str(dataset_dir)))
    exposure_registry = ExposureRegistry(resolve_micro_exposure_registry_dir(str(dataset_dir)))
    result = scout.register_screen_and_walkforward_check(
        ledger=ledger, dataset_store=dataset_store, snapshots_dir=snapshots_dir, config=CONFIG,
        exposure_registry=exposure_registry, playbook_store=playbook_store,
        feature_name=request["feature_name"], transform=request["transform"],
        params=request["params"], structure_context_kind=request["structure_context_kind"],
        horizon_key=request["horizon_key"], corpus_manifest=request["corpus_manifest"],
        grid_version=request["grid_version"], sidedness=request["sidedness"],
        fitting_rule=request["fitting_rule"], setup_id=request["setup_id"],
        withheld_excluded=request["withheld_excluded"],
    )
    screen_row = result["screen_row"]
    screen_result = screen_row["screen_result"]
    print(
        f"[seed-micro-scout-iter24-j09] register_screen_and_walkforward_check -> "
        f"candidate_id={screen_row['candidate_id']!r} family_id={screen_row['family_id']!r} "
        f"decision={screen_row['decision']!r} n_candidate={screen_result['n_candidate']} "
        f"n_comparator={screen_result['n_comparator']}", file=sys.stderr,
    )
    if screen_result["n_candidate"] + screen_result["n_comparator"] <= 0:
        print(
            "[seed-micro-scout-iter24-j09] ERROR: vacuous screen -- zero anchors joined "
            "(n_candidate + n_comparator == 0); the planted signal never reached the screen",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
