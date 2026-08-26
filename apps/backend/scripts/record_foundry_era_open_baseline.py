"""Records the Hypothesis Foundry era-open baseline snapshot ONCE (goal-hypothesis-foundry-iter-1,
J-01 step 5) -- the full backend suite pass/skip/failed counts and ``tsc --noEmit`` error count are
supplied by the CALLER as CLI flags. This script deliberately never shells out to ``pytest``/
``tsc`` itself: running the full suite and the TypeScript compile is the operator's own
already-necessary verification act (the SAME numbers the dev handoff's "Tests Run" section
reports), and re-running them a second time from inside this script would be slow, redundant, and
would risk a DIFFERENT number than what was actually verified. ``config_fingerprint`` is read live
from ``CONFIG`` (never hand-typed); the six ``referee_*.py`` module SHA-256 hashes are computed
here directly (cheap, deterministic file reads -- see
``foundry_source_registry.record_era_open_baseline``'s own docstring).

Writes into the REAL project dataset-dir sibling (``apps/backend/.data/foundry/``, or the
``TAPEOLOGY_FOUNDRY_DIR``/``TAPEOLOGY_DATASET_DIR`` overrides if set) -- this is era build/test
provenance metadata, never market/tick data, so it belongs beside the other Rapid-Microscope-era
sibling directories (``vault``, ``micro_graduation``, ...) under the SAME real store.

Idempotent-by-explicit-act: re-running this script overwrites the prior snapshot (an intentional
operator re-recording, never something a page load triggers -- ``GET /research/desk/micro/foundry``
only ever READS the persisted file).

Run from ``apps/backend`` after a full green suite + clean ``tsc --noEmit``:

    .venv/bin/python -m pytest tests/ -q --junitxml=/tmp/junit.xml   # note the counts
    (cd ../frontend && ./node_modules/.bin/tsc --noEmit)             # note the error count
    .venv/bin/python scripts/record_foundry_era_open_baseline.py \\
        --passed 3788 --skipped 8 --failed 0 --tsc-errors 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.env import load_env  # noqa: E402

load_env()

from app.config import CONFIG  # noqa: E402
from app.research.foundry_source_registry import (  # noqa: E402
    record_era_open_baseline,
    resolve_foundry_dir,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passed", type=int, required=True, help="pytest pass count")
    parser.add_argument("--skipped", type=int, required=True, help="pytest skip count")
    parser.add_argument("--failed", type=int, required=True, help="pytest failure count")
    parser.add_argument("--tsc-errors", type=int, required=True, help="`tsc --noEmit` error count")
    args = parser.parse_args(argv)

    dataset_dir = CONFIG.dataset_dir_resolved()
    foundry_dir = resolve_foundry_dir(dataset_dir)
    research_dir = BACKEND_DIR / "app" / "research"

    snapshot = record_era_open_baseline(
        foundry_dir,
        suite_passed=args.passed,
        suite_skipped=args.skipped,
        suite_failed=args.failed,
        tsc_error_count=args.tsc_errors,
        config_fingerprint=CONFIG.config_fingerprint(),
        research_dir=research_dir,
    )
    print(
        f"[record-foundry-era-open-baseline] recorded to {foundry_dir}:\n"
        f"  backend_suite={snapshot['backend_suite']}\n"
        f"  tsc_error_count={snapshot['tsc_error_count']}\n"
        f"  config_fingerprint={snapshot['config_fingerprint']}\n"
        f"  referee_module_sha256={snapshot['referee_module_sha256']}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
