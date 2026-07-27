#!/usr/bin/env bash
# goal-desk-iter9-scoped-backend.sh — Stand up a FIXTURE-SCOPED backend for goal-desk iter-9 (J-08
# "basis disclosure") golden-script recording/verification and browser-QA evidence. Never touches
# the ambient apps/backend/.data/ store: every directory this backend reads or writes lives under a
# fresh throw-away COPY (the goal-desk-iter8-baseline-diff.py "copy the whole .data/ tree" recipe,
# not the iter-5 narrow-fixture-seed recipe) -- because THIS iteration specifically needs the two
# REAL pre-existing screen snapshots already in history (screen-2026-06-22-3ecd45c062c7,
# screen-2026-07-25-e184a7dc2f86 -- both legacy, basis fields absent by construction) as J-05-style
# drill-through history rows, plus the ~60 real symbols' worth of real bars already recorded, so a
# fresh "Run Screen" click over real data exercises the NEW basis_as_of/basis_age_days fields with
# a real fresh/stale age spread (see docs/goal.md's own iter-9 BACKGROUND: AAPL ~1d, MSFT ~4d,
# META/NFLX/NVDA ~12d, measured live 2026-07-25).
#
# Usage:
#   bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh [root_dir] [port]
#
#   root_dir  Fresh temp root to seed (default: ${TMPDIR:-/tmp}/desk-iter9-scoped-qa). A COPY of
#             the CURRENT apps/backend/.data/ tree + tapeology_journal.db is made here on first use;
#             a root_dir that already holds a `.data/` copy is REUSED as-is (no re-copy) -- pass a
#             fresh/distinct root_dir if you need a byte-for-byte-fresh snapshot of the ambient
#             .data/ as it stands right now (e.g. after a real top-up landed new bars).
#   port      Backend port (default: 8301, the era's browser-QA rig convention -- pair with
#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh` for
#             the frontend so NEXT_PUBLIC_API_URL points at this backend).
#
# Lives under apps/backend/scripts/ (the project's own script tree -- never under scripts/, which
# is a symlink into the vendored incredible_auto_dev/ framework tree that gets content-synced from
# upstream and must not carry project-specific QA tooling).
#
# What this seeds: a full copy of apps/backend/.data/ (bars, bar_index.db, datasets,
# dataset_index.db, universe, screen, tradability_cache.db, setups_scan_cache.db,
# edge_report_*.db) plus tapeology_journal.db -- verbatim, via `cp -a`, never re-derived through any
# store's own `record()` (which would mint new checksums/ids). Every derived-index path
# (bar_index.db, dataset_index.db, ...) resolves as a SIBLING of the directory env vars below
# (routes.py's own `os.path.dirname(...)` convention -- e.g. `get_bar_index`,
# `desk_screen.resolve_desk_screen_dir`), so copying the whole tree is sufficient: no separate
# `*_INDEX_DB`/`*_CACHE_DB` env var is needed (the goal-desk-iter8-baseline-diff.py precedent).
#
# Exec's `scripts/start-backend.sh` at the end (inherits every exported env var below).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/desk-iter9-scoped-qa}"
PORT="${2:-8301}"

mkdir -p "$ROOT"

if [[ ! -d "$ROOT/.data" ]]; then
  cp -a "$BACKEND_DIR/.data" "$ROOT/.data"
  echo "[desk-iter9-scoped-backend] copied $BACKEND_DIR/.data -> $ROOT/.data" >&2
else
  echo "[desk-iter9-scoped-backend] reusing existing $ROOT/.data (already seeded -- pass a fresh root_dir for a byte-for-byte-fresh copy)" >&2
fi
if [[ -f "$BACKEND_DIR/tapeology_journal.db" && ! -f "$ROOT/tapeology_journal.db" ]]; then
  cp -a "$BACKEND_DIR/tapeology_journal.db" "$ROOT/tapeology_journal.db"
fi

export TAPEOLOGY_BAR_DIR="$ROOT/.data/bars"
export TAPEOLOGY_DATASET_DIR="$ROOT/.data/datasets"
export TAPEOLOGY_DESK_UNIVERSE_DIR="$ROOT/.data/universe"
export TAPEOLOGY_DESK_SCREEN_DIR="$ROOT/.data/screen"
export TAPEOLOGY_JOURNAL_DB="$ROOT/tapeology_journal.db"

echo "[desk-iter9-scoped-backend] root=$ROOT port=$PORT" >&2
echo "[desk-iter9-scoped-backend] TAPEOLOGY_BAR_DIR=$TAPEOLOGY_BAR_DIR" >&2
echo "[desk-iter9-scoped-backend] TAPEOLOGY_DATASET_DIR=$TAPEOLOGY_DATASET_DIR" >&2
echo "[desk-iter9-scoped-backend] TAPEOLOGY_DESK_UNIVERSE_DIR=$TAPEOLOGY_DESK_UNIVERSE_DIR" >&2
echo "[desk-iter9-scoped-backend] TAPEOLOGY_DESK_SCREEN_DIR=$TAPEOLOGY_DESK_SCREEN_DIR" >&2
echo "[desk-iter9-scoped-backend] TAPEOLOGY_JOURNAL_DB=$TAPEOLOGY_JOURNAL_DB" >&2

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
