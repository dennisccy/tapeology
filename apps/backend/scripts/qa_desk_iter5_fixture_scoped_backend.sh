#!/usr/bin/env bash
# desk-iter5-fixture-scoped-backend.sh — Stand up a FIXTURE-SCOPED backend for the goal-desk
# iter-5 browser-QA pass (J-04 evidence gap). Never touches the ambient apps/backend/.data/
# store: every desk/bar/dataset directory this backend reads or writes lives under a fresh
# temp root, never under apps/backend/.data/ (see docs/handoffs/goal-desk-iter-5-dev.md for the
# rationale — the iter-4 near-miss that wrote 60 real bar records into the ambient store).
#
# Usage:
#   bash apps/backend/scripts/qa_desk_iter5_fixture_scoped_backend.sh [root_dir] [port]
#
#   root_dir  Fresh temp root to seed (default: ${TMPDIR:-/tmp}/desk-iter5-fixture-qa). MUST be a
#             root nobody else has written screen snapshots into yet if you need TC-1's empty
#             state ("Desk screen not computed yet.") — this dev's own verification run already
#             recorded 2 screen snapshots into ITS root; use a DIFFERENT path for the actual
#             browser-QA pass. Re-using an existing (untouched) root reuses whatever it already
#             contains (the universe/bar stores refuse re-registration of identical content, so a
#             re-run over the SAME still-empty root is a safe no-op reseed).
#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`
#             for the frontend so NEXT_PUBLIC_API_URL points at this backend).
#
# Lives under apps/backend/scripts/ (the project's own script tree — never under scripts/, which
# is a symlink into the vendored incredible_auto_dev/ framework tree that gets content-synced from
# upstream and must not carry project-specific QA tooling).
#
# What this seeds (verbatim copies, never re-derived):
#   - universe dir  <- tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json (103 members)
#   - bar dir       <- tests/fixtures/bars/{009371c9c02f46338bafef47148f92ad,
#                                            b08b1a55ef4a45b2a1adad8fa82ccdf1}.json (PG 1h + 1d)
#   - bar_index.db  <- rebuilt via BarIndex.reindex() over the seeded bar dir (T-4: coverage
#                      reads the index, never the store, so the index must exist before any
#                      GET /research/desk/coverage call)
#   - screen dir, dataset dir, dataset index  <- left empty (honest "not computed yet" /
#     no-tick-evidence states; this iteration adds no screen/dataset fixtures)
#
# Exec's `scripts/start-backend.sh` at the end (inherits every exported env var below).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/desk-iter5-fixture-qa}"
PORT="${2:-8301}"

UNIVERSE_DIR="$ROOT/universe"
BAR_DIR="$ROOT/bars"
SCREEN_DIR="$ROOT/screen"
DATASET_DIR="$ROOT/datasets"
BAR_INDEX_DB="$ROOT/bar_index.db"
DATASET_INDEX_DB="$ROOT/dataset_index.db"
JOURNAL_DB="$ROOT/journal.db"

mkdir -p "$UNIVERSE_DIR" "$BAR_DIR" "$SCREEN_DIR" "$DATASET_DIR"

# Verbatim fixture seeds — never re-derived, never re-registered through record() (that would
# mint a NEW checksum/id; the point is to reproduce the exact committed fixture files).
cp "$BACKEND_DIR/tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json" "$UNIVERSE_DIR/"
cp "$BACKEND_DIR/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json" "$BAR_DIR/"
cp "$BACKEND_DIR/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json" "$BAR_DIR/"

# Rebuild the derived bar_index.db from the seeded bar dir (coverage/screen reads ONLY the
# index per T-4 — dropping raw JSON into the bar dir alone would leave the index empty and
# every member, including PG, would show as "no bars").
"$BACKEND_DIR/.venv/bin/python" -c "
import sys
sys.path.insert(0, '$BACKEND_DIR')
from app.research.bars import BarStore
from app.research.bar_index import BarIndex
store = BarStore('$BAR_DIR')
index = BarIndex('$BAR_INDEX_DB')
index.reindex(store)
records, errors = store.list()
print(f'[desk-iter5-fixture-scoped-backend] bar_index seeded: {len(records)} series, {len(errors)} errors', file=sys.stderr)
"

export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
export TAPEOLOGY_BAR_DIR="$BAR_DIR"
export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
# Not one of the six the spec names, but scoped for the same reason (belt-and-suspenders —
# main.py's lifespan opens this at startup regardless of any desk route being hit): keeps the
# ambient apps/backend/tapeology_journal.db untouched too.
export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"

echo "[desk-iter5-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DESK_UNIVERSE_DIR=$UNIVERSE_DIR" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_BAR_DIR=$BAR_DIR" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DESK_SCREEN_DIR=$SCREEN_DIR" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DATASET_DIR=$DATASET_DIR" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_BAR_INDEX_DB=$BAR_INDEX_DB" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_DATASET_INDEX_DB=$DATASET_INDEX_DB" >&2
echo "[desk-iter5-fixture-scoped-backend] TAPEOLOGY_JOURNAL_DB=$JOURNAL_DB" >&2

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
