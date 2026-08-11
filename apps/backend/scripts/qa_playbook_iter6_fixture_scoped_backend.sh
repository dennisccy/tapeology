#!/usr/bin/env bash
# qa_playbook_iter6_fixture_scoped_backend.sh — Stand up a FIXTURE-SCOPED backend carrying the
# J-04/J-05/J-06 playbook rig (DECOR capitulation+euphoria, RTAAA range_trade, DTAAA double_top),
# for a browser-QA / golden-replay pass. Never touches the ambient apps/backend/.data/ store:
# every bar/universe/playbook/run-ledger directory this backend reads or writes lives under a
# fresh root, so a "Run Playbook" click in the browser can never land in the operator's real
# store (the iter-3 lesson; the iter-6 audit's TC-19 orphaned run-ledger rows are what happens
# when the log-dir siblings are left unscoped — all FOUR playbook env vars are exported here).
#
# Why this exists: before iter-6's fix pass the browser rig was hand-built ad hoc by each QA
# agent and reproducible from nothing in the repo, so its evidence could not be re-recorded when
# a detector rule changed. Everything below is planted from the SAME fixture bar values the
# committed goldens hand-compute (tests/test_desk_playbook_detect.py / test_desk_playbook.py) —
# never re-derived here, so the rig and the goldens can never drift.
#
# Usage:
#   bash apps/backend/scripts/qa_playbook_iter6_fixture_scoped_backend.sh [root_dir] [port]
#
#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter6-fixture-qa). Use a
#             FRESH one whenever detector logic changed: playbook records are append-only and
#             keyed (session_date, playbook_input_signature), so a root seeded by an older build
#             would keep serving that build's recorded signals at the same signature.
#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`).
#
# What it seeds, session date 2026-06-22:
#   - DECOR — the euphoria-marker-then-capitulation fixture (J-05: a capitulation signal carrying
#     `euphoria_recent`)
#   - RTAAA — the canonical two-sided armed range (J-06 range_trade long)
#   - DTAAA — the canonical double-top (J-06 double_top short)
#   plus each symbol's 10 prior baseline sessions, a 3-member universe snapshot, and ONE recorded
#   playbook record produced by the real `compute_playbook` walk.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter6-fixture-qa}"
PORT="${2:-8301}"

BAR_DIR="$ROOT/bars"
UNIVERSE_DIR="$ROOT/universe"
PLAYBOOK_DIR="$ROOT/playbook"
PLAYBOOK_LOG_DIR="$ROOT/playbook_runs"
PLAYBOOK_BACKSCAN_LOG_DIR="$ROOT/playbook_backscan_runs"
SCREEN_DIR="$ROOT/screen"
DATASET_DIR="$ROOT/datasets"
BAR_INDEX_DB="$ROOT/bar_index.db"
DATASET_INDEX_DB="$ROOT/dataset_index.db"
JOURNAL_DB="$ROOT/journal.db"

mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
         "$PLAYBOOK_BACKSCAN_LOG_DIR" "$SCREEN_DIR" "$DATASET_DIR"

export TAPEOLOGY_BAR_DIR="$BAR_DIR"
export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR="$PLAYBOOK_LOG_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR="$PLAYBOOK_BACKSCAN_LOG_DIR"
export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"

"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_fixture_rig.py" "$ROOT"

echo "[playbook-iter6-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
           TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
           TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
           TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
  echo "[playbook-iter6-fixture-scoped-backend] $var=${!var}" >&2
done

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
