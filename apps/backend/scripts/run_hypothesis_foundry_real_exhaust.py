"""Runs the Hypothesis Foundry's real deterministic exhaust pass (goal-hypothesis-foundry-iter-6,
Binding Execution Order step 8, J-07) -- the resumable, single-flight CLI/manager operator act
spec §9 requires, over the ONE real, Git-frozen epoch (§8.1) iter-5/iter-6 already committed.
Following ``generate_hypothesis_foundry_real_epoch.py``'s own convention (argparse, prints a
summary to stderr, no implicit git operations).

**What this script does, in order (§9.1/§8.5):**

1. Verifies freeze integrity: recomputes every pinned freeze-set path's sha256
   (``foundry_freeze.verify_freeze_set_unchanged``) and proves ``freeze_commit`` is an ancestor of
   ``HEAD`` (``foundry_freeze.verify_commit_is_ancestor``). Refuses BEFORE anything else runs.
2. Acquires ``foundry_runner.SingleFlightLock`` -- a concurrent second invocation raises
   ``foundry_runner.ConcurrentRunnerRefused`` and appends no ledger row.
3. Computes the resolved eligible diagnostic-corpus ``(dataset_id, checksum)`` manifest hash
   through the SAME sanctioned data door every other corpus-wide enumerator in this codebase
   shares (``datasets.DatasetStore.list()`` + ``micro_snapshots.exclude_withheld`` --
   ``pnl_scan._verified_corpus``'s own precedent) and ``micro_corpus.corpus_manifest_hash`` (the
   EXISTING scientific-identity hash formula -- never a second one invented here). This reads ONLY
   dataset METADATA (id, checksum, symbol, window) -- no snapshot row, no event, is ever read, so
   this step alone already proves the era's own protected-read-zero property structurally.
4. Appends the ONE epoch-opening / first-read-lock row (``foundry_ledger.FoundryLedger.
   record_epoch_open``) BEFORE any candidate outcome could ever be read -- idempotent on replay
   (a second invocation verifies and no-ops rather than appending a second lock row).
5. Iterates every ``FROZEN_READY`` variant in the frozen manifest's own family/variant order
   through ``foundry_runner.run_family``/``run_one_candidate`` -- the real runner+ledger path, not
   a fixture stand-in. The one real epoch's own committed ``epoch-manifest.json`` carries
   ``families: []`` (§8.1: every one of the 11 required sources disposed non-COMPILED), so this
   step completes honestly with zero terminal evaluations -- see ``_default_frozen_ready_families``
   and ``RealCandidateEvaluationUnsupported`` below for why real per-family CandidateSpec/anchor
   reconstruction from the exposed corpus is a deliberately unbuilt, fail-closed path this era: it
   is never reached against the real committed manifest, so building it now would be new
   candidate-construction machinery for a state this era's one epoch cannot reach.
6. Reports the checkpoint ordinal and a zero protected/withheld/sealed read census.

**Repeat invocation.** Verifies and no-ops (TC-2): the epoch-opening row already exists, every
already-terminal candidate is verified and skipped, no new ledger row is appended for anything
that already reached a terminal state.

**Resume-after-crash / fixture-backed proofs.** ``run_real_exhaust``'s ``frozen_ready_families``
parameter lets a caller inject its own ``(FoundryFamily, [(CandidateSpec, anchors), ...])`` plan
(hermetic fixture data, exactly the discipline ``foundry_hermetic_summary.py`` already uses) to
exercise ``run_family``/``run_one_candidate``'s already-proven crash-resume/canonical-order
machinery (``test_foundry_runner.py``'s ``test_tc15_...``/``test_tc16_...``) THROUGH this exact
same freeze-verify -> single-flight -> corpus-hash -> epoch-open -> exhaust sequence, without
requiring real anchor extraction from real snapshot data (which does not exist and is not needed
this era -- see point 5 above). J-07 step 7 itself permits this: "do not attempt to simulate an
interrupt against the real epoch, which has zero variants to interrupt mid-evaluation anyway."

Run from ``apps/backend`` after the freeze-set/freeze-record regeneration has been committed:

    .venv/bin/python scripts/run_hypothesis_foundry_real_exhaust.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402

load_env()

from app.config import CONFIG  # noqa: E402
from app.research import foundry_family as ffam  # noqa: E402
from app.research import foundry_freeze as fz  # noqa: E402
from app.research import foundry_ledger as fl  # noqa: E402
from app.research import foundry_runner as fr  # noqa: E402
from app.research import micro_corpus  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402
from app.research.foundry_source_registry import resolve_foundry_dir  # noqa: E402
from app.research.micro_snapshots import exclude_withheld  # noqa: E402

FOUNDRY_DOCS_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
EPOCH_MANIFEST_PATH = FOUNDRY_DOCS_DIR / "epoch-manifest.json"
FREEZE_SET_PATH = FOUNDRY_DOCS_DIR / "freeze-set.json"
FREEZE_RECORD_PATH = FOUNDRY_DOCS_DIR / "freeze-record.json"

# The single-flight lock file lives beside the Foundry trial ledger itself (same runtime-scoped
# storage, `get_foundry_dir()`/`TAPEOLOGY_FOUNDRY_DIR`). Defined ONCE, in `foundry_runner.py`
# (`EXHAUST_LOCK_FILENAME`), so `micro_routes.py`'s own live lock probe for
# `exhaust_progress.single_flight_status` targets the IDENTICAL filename this script uses -- never
# a second, independently-typed literal that could silently drift out of sync.
LOCK_FILENAME = fr.EXHAUST_LOCK_FILENAME

# A placeholder econ-floor rule -- ONLY ever passed to `run_family` inside the (this epoch, always
# empty) FROZEN_READY loop below; §6's real numeric-floor derivation is candidate-specific and this
# era's one real epoch has no candidate to derive one for. Present so the call shape matches
# `run_family`'s real signature; never read for a candidate that is never evaluated.
_UNUSED_PLACEHOLDER_ECON_FLOOR = {
    "floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0,
}


class FreezeAncestryUnproven(Exception):
    """§8.4: ``freeze_commit`` failed to verify as an ancestor of ``HEAD`` -- the pre-outcome
    Git-visible commit barrier is not proven. Refused before any epoch-opening row is written
    (never after -- see spec §7.3/§9.3: this is an integrity halt, not something to patch and
    continue past)."""


class DatasetIntegrityFailure(Exception):
    """The sanctioned data door (``datasets.DatasetStore.list()``) reported a dataset file failing
    checksum verification -- the eligible-corpus enumeration refuses rather than silently excluding
    a corrupt/tampered file from the corpus it reports (the ``pnl_scan._verified_corpus`` precedent:
    "a partial report is a misleading report")."""


class RealCandidateEvaluationUnsupported(Exception):
    """goal-hypothesis-foundry-iter-6: real per-family CandidateSpec/anchor reconstruction from the
    exposed diagnostic corpus is deliberately unbuilt. The one real epoch this era will ever
    generate (goal.md §8.1) is frozen with ``families: []`` (every one of the 11 required sources
    disposed non-COMPILED this era -- see ``reports/hypothesis-foundry/source-registry-audit.md``),
    so this exception is never raised against the real committed manifest; it exists purely so a
    hypothetically widened manifest fails CLOSED rather than being silently mis-evaluated by
    unbuilt, unproven logic. A future methodology era that compiles real candidates must implement
    and hermetically prove real anchor extraction before this CLI can run its exhaust pass over
    them -- that is new scientific-construction work this era's own "no candidate rescue" (§9.3)
    and "no new science this epoch" boundaries explicitly place out of scope."""


def _git_rev_parse_head(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), capture_output=True, text=True
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def compute_eligible_corpus(dataset_dir: str) -> dict:
    """§10.1: "use the sanctioned micro accessor/data door; call existing withheld exclusion
    machinery" -- the SAME ``DatasetStore.list()`` + ``micro_snapshots.exclude_withheld`` choke
    point every other corpus-wide enumerator in this codebase already shares
    (``pnl_scan._verified_corpus``, ``desk_screen.py``, ``edge_report_cache.py``). Hashed with the
    EXISTING ``micro_corpus.corpus_manifest_hash`` formula -- never a second one invented here.

    Reads ONLY already-verified dataset METADATA (id, checksum, symbol, window) -- never a snapshot
    row, never an event -- so this function alone already proves the era's own zero-protected-read
    property structurally: nothing here can touch a sealed shard's content, because nothing here
    ever calls ``micro_accessor.MicroAccessor.read_snapshot_rows``."""
    store = DatasetStore(dataset_dir)
    records, errors = store.list()
    if errors:
        raise DatasetIntegrityFailure(
            f"{len(errors)} dataset file(s) failed integrity verification "
            f"({[e['file'] for e in errors]}) -- the exhaust run stops before any epoch-opening row"
        )
    kept, withheld_excluded = exclude_withheld(records, store)
    members = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in kept]
    return {
        "manifest_hash": micro_corpus.corpus_manifest_hash(members),
        "member_count": len(members),
        "withheld_excluded": withheld_excluded,
    }


def _default_frozen_ready_families(
    manifest: dict,
) -> list[tuple[ffam.FoundryFamily, list]]:
    """The default variant-plan resolver ``run_real_exhaust`` uses against the REAL committed
    manifest. For every family entry the manifest carries: a family with zero variants reaches the
    same honest, real ``run_family`` completion (called with an empty variant list) that
    ``foundry_hermetic_summary._all_blocked_epoch_completed`` already proves for this exact shape;
    a family carrying ANY variant raises ``RealCandidateEvaluationUnsupported`` (see that
    exception's own docstring) rather than being silently skipped or mis-evaluated. The real
    committed manifest's own ``families`` list is ``[]`` (§8.1), so this function's own loop body
    never executes against real data -- present so the exhaust sequence's own generic shape is
    real and testable against injected fixture plans (see this module's own docstring)."""
    plan: list[tuple[ffam.FoundryFamily, list]] = []
    for family_manifest in manifest.get("families", []):
        variant_views = family_manifest.get("variants", [])
        family_id = family_manifest["foundry_family_id"]
        if variant_views:
            raise RealCandidateEvaluationUnsupported(
                f"family {family_id!r} carries {len(variant_views)} FROZEN_READY variant(s), but "
                "real per-family CandidateSpec/anchor reconstruction was never built this era -- "
                "refused rather than silently mis-evaluated"
            )
        family = ffam.build_family_registry({family_id: []})[family_id]
        plan.append((family, []))
    return plan


def run_real_exhaust(
    *,
    tracked_dir: Path = FOUNDRY_DOCS_DIR,
    repo_root: Path = REPO_ROOT,
    dataset_dir: str | None = None,
    foundry_dir: str | None = None,
    lock_path: Path | None = None,
    frozen_ready_families: Callable[[dict], list[tuple[ffam.FoundryFamily, Sequence]]] | None = None,
) -> dict:
    """The core, testable exhaust sequence (§9.1-§9.2/§8.5) -- see this module's own docstring for
    the six ordered steps. Every path parameter defaults to the REAL production location; a test
    overrides ``tracked_dir``/``repo_root``/``dataset_dir``/``foundry_dir``/``lock_path`` to point
    at a hermetic fixture tree, and/or ``frozen_ready_families`` to inject a fixture variant plan,
    without touching any real file."""
    dataset_dir = dataset_dir if dataset_dir is not None else CONFIG.dataset_dir_resolved()
    foundry_dir = foundry_dir if foundry_dir is not None else resolve_foundry_dir(dataset_dir)
    lock_path = lock_path if lock_path is not None else Path(foundry_dir) / LOCK_FILENAME
    resolver = frozen_ready_families or _default_frozen_ready_families

    freeze_set = json.loads((tracked_dir / "freeze-set.json").read_text(encoding="utf-8"))
    freeze_record = json.loads((tracked_dir / "freeze-record.json").read_text(encoding="utf-8"))
    manifest = json.loads((tracked_dir / "epoch-manifest.json").read_text(encoding="utf-8"))

    # --- step 1 (§9.1/§8.5): verify freeze integrity BEFORE anything else runs -------------------
    fz.verify_freeze_set_unchanged(freeze_set, repo_root=repo_root)
    head = _git_rev_parse_head(repo_root)
    if not head or not fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=repo_root):
        raise FreezeAncestryUnproven(
            f"freeze_commit {freeze_record.get('freeze_commit')!r} did not verify as an ancestor "
            f"of HEAD ({head!r}) -- refused before any epoch-opening row is written"
        )

    frozen_ready_total = sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))

    # --- step 2 (§9): single-flight -- a concurrent second invocation raises here, no ledger row --
    lock = fr.SingleFlightLock(lock_path)
    with lock.acquire():
        # --- step 3 (§10.1): resolved eligible-corpus manifest hash, sanctioned door only --------
        corpus = compute_eligible_corpus(dataset_dir)

        # --- step 4 (§8.5): the ONE epoch-opening / first-read-lock row, idempotent on replay ----
        ledger = fl.FoundryLedger(foundry_dir)
        epoch_open = ledger.record_epoch_open(
            epoch_id=manifest["epoch_id"],
            freeze_commit=freeze_record["freeze_commit"],
            manifest_hash=freeze_record["manifest_hash"],
            source_registry_hash=freeze_record["source_registry_hash"],
            spec_hash=freeze_record["spec_hash"],
            candidate_spec_schema_hash=freeze_record["candidate_spec_schema_hash"],
            compiler_hash=freeze_record["compiler_hash"],
            interpreter_hash=freeze_record["interpreter_hash"],
            runner_hash=freeze_record["runner_hash"],
            scout_screen_source_hash=freeze_record["scout_screen_source_hash"],
            config_fingerprint=freeze_record["config_fingerprint"],
            freeze_set_hash=freeze_record["freeze_set_hash"],
            era_open_evidence_class_contract=freeze_record["era_open_evidence_class_contract"],
            eligible_corpus_manifest_hash=corpus["manifest_hash"],
        )

        # --- step 5 (§9.1): exhaust every FROZEN_READY variant in canonical family/variant order -
        family_variant_plan = resolver(manifest)
        for family, variants in family_variant_plan:
            fr.run_family(
                family, variants, ledger=ledger, econ_floor=_UNUSED_PLACEHOLDER_ECON_FLOOR,
                manifest_hash=freeze_record["manifest_hash"],
            )

        terminal_count = len([r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL])

    return {
        "epoch_id": manifest["epoch_id"],
        "epoch_open": epoch_open,
        "eligible_corpus_manifest_hash": corpus["manifest_hash"],
        "eligible_corpus_member_count": corpus["member_count"],
        "withheld_excluded": corpus["withheld_excluded"],
        "frozen_ready_total": frozen_ready_total,
        "terminal_count": terminal_count,
        "checkpoint_ordinal": terminal_count,
        # §10.2/§20: nothing above ever calls the snapshot-row accessor -- zero by construction,
        # not by a runtime count that could silently drift from what actually happened.
        "protected_read_count": 0,
        "exhaust_complete": terminal_count >= frozen_ready_total,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    try:
        result = run_real_exhaust()
    except fr.ConcurrentRunnerRefused as exc:
        print(f"[run-hypothesis-foundry-real-exhaust] REFUSED (concurrent runner): {exc}", file=sys.stderr)
        return 1
    except (FreezeAncestryUnproven, fz.FreezeIntegrityHalt, DatasetIntegrityFailure) as exc:
        print(f"[run-hypothesis-foundry-real-exhaust] INTEGRITY HALT: {exc}", file=sys.stderr)
        return 1

    print(
        f"[run-hypothesis-foundry-real-exhaust] epoch_id={result['epoch_id']}\n"
        f"  first_read_lock_recorded_at={result['epoch_open']['recorded_at']}\n"
        f"  eligible_corpus_manifest_hash={result['eligible_corpus_manifest_hash']}\n"
        f"  eligible_corpus_member_count={result['eligible_corpus_member_count']}\n"
        f"  withheld_excluded={result['withheld_excluded']}\n"
        f"  frozen_ready_total={result['frozen_ready_total']}\n"
        f"  terminal_count={result['terminal_count']}\n"
        f"  checkpoint_ordinal={result['checkpoint_ordinal']}\n"
        f"  protected_read_count={result['protected_read_count']}\n"
        f"  exhaust_complete={result['exhaust_complete']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
