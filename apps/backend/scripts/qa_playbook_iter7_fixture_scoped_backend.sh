#!/usr/bin/env bash
# qa_playbook_iter7_fixture_scoped_backend.sh — Stand up a FIXTURE-SCOPED backend carrying the
# iter-6 J-04/J-05/J-06 playbook rig PLUS two additional recorded session dates for the Backscan
# panel (Era B2, J-07), for a browser-QA / golden-replay pass. Never touches the ambient
# apps/backend/.data/ store: every bar/universe/playbook/run-ledger directory this backend reads or
# writes lives under a fresh root, so a "Run Backscan" click in the browser can never land in the
# operator's real store (the iter-3 lesson, restated by this session's own iter-6 audit findings for
# the run-ledger siblings specifically — all FOUR playbook env vars are exported here, including
# TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR).
#
# This is an iter-7 VARIANT of qa_playbook_iter6_fixture_scoped_backend.sh, not an edit of it —
# both scripts stay usable; this one is the ONLY backend entry point for this iteration's test/
# browser work (per the phase spec's own instruction). It reuses
# seed_playbook_iter7_backscan_fixture.py, which itself reuses seed_playbook_fixture_rig.py's own
# main() verbatim (never a second implementation of the DECOR/RTAAA/DTAAA fixtures).
#
# What it seeds, on top of the iter-6 rig's own 2026-06-22 (DECOR/RTAAA/DTAAA, one playbook record
# already computed):
#   - BSCAN — a plain canonical open_high_break firing session, planted on TWO new dates
#     (2026-06-23, 2026-06-24), each with its own 10 prior baseline sessions, LEFT UNRECORDED in
#     the playbook store.
#   - a fourth, NEW universe snapshot naming all four members (universe registration is
#     append-only — this never edits iter-6's own three-member snapshot). Registering BSCAN
#     changes playbook_input_signature (it hashes members ∪ {SPY}), so 2026-06-22's own
#     three-member record no longer matches the CURRENT signature either — a plan preview over
#     [2026-06-22, 2026-06-24] honestly reports all THREE dates missing, and a real "Run Backscan"
#     click has genuine, non-trivial work to do on all three (the old three-member record stays on
#     disk, untouched — append-only, a new version is minted beside it, never over it).
#
# Usage:
#   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
#
#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter7-fixture-qa). Use a
#             FRESH one whenever detector logic OR the back-scan module changed: playbook records
#             are append-only and keyed (session_date, playbook_input_signature), so a root seeded
#             by an older build would keep serving that build's recorded signals at the same
#             signature.
#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter7-fixture-qa}"
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

"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter7_backscan_fixture.py" "$ROOT"

echo "[playbook-iter7-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
           TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
           TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
           TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
  echo "[playbook-iter7-fixture-scoped-backend] $var=${!var}" >&2
done

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
