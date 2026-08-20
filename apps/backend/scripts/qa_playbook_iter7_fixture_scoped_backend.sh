#!/usr/bin/env bash
# qa_playbook_iter7_fixture_scoped_backend.sh — Stand up a FIXTURE-SCOPED backend carrying the
# iter-6 J-04/J-05/J-06 playbook rig PLUS the Backscan (J-07) and Evidence (J-08) fixture layers,
# for a browser-QA / golden-replay pass. Never touches the ambient apps/backend/.data/ store: every
# bar/universe/playbook/run-ledger/evidence-cache directory this backend reads or writes lives
# under a fresh root, so a "Run Backscan" click (or ANY playbook-touching golden replay) in the
# browser can never land in the operator's real store (the iter-3 lesson, restated by the iter-6
# audit for the run-ledger siblings, and made MANDATORY for every playbook journey's replay lane by
# the iter-7 evaluator's own carry-item: this script -- extended forward, never rewritten -- is now
# the ONE launcher every playbook golden-replay run (J-01..J-08, and J-10's playbook-touching
# steps) MUST use; a replay script that instead reaches whatever is already listening on :8301 is
# the exact hole that carry item closed).
#
# goal-playbook-iter-8 (J-08) EXTENDS this iter-7 file in place (per this iteration's own
# instruction: extend the launcher forward, never rewrite it) rather than spawning an iter-8
# variant — the launcher stays SINGULAR precisely so "the mandatory launcher" never becomes
# ambiguous between iterations. It adds:
#   - the evidence projection cache's own scoping var (TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB),
#     kept under $ROOT exactly like every other playbook store/log dir;
#   - seed_playbook_iter8_evidence_fixture.py (reusing seed_playbook_iter7_backscan_fixture.py's
#     own main() verbatim, in turn reusing seed_playbook_fixture_rig.py's — never a second
#     implementation of the DECOR/RTAAA/DTAAA/BSCAN fixtures), which on top of everything iter-7
#     already seeded ALSO plants twelve OHB01..OHB12 members firing the SAME canonical
#     open_high_break session as BSCAN, on 2026-06-25 (a FRESH date — deliberately NOT 2026-06-22,
#     which would re-record the date J-07's own golden asserts is still missing) — giving the
#     evidence fold's (open_high_break, long, *) cells n >= PLAYBOOK_MIN_N_DISCLOSURE at the short
#     horizons beside its OWN 1h/4h cells at n = 0, which are below_min_n for free.
#
# goal-playbook-iter-8 FIX PASS (audit finding B2) extends it once more, again in place: the seed
# entry point becomes seed_playbook_iter8_replay_rig.py, which reuses the evidence seeder's main()
# verbatim and then adds what the REMAINING required goldens need, so all EIGHT required-still-
# passing journeys (J-01..J-07, J-10) replay green against THIS one backend instead of five of them
# silently requiring the operator's real store: a weekday-only daily-bar calendar (CALDR) that makes
# J-01's and J-03's non-session refusals reachable, the canonical open_low_break / JBE / DBI
# sessions on 2026-08-07 (J-02, J-04), and every AAPL bar series copied verbatim from the real store
# (read-only) so J-10's /structure step measures the kept product, not a fixture. See that script's
# own docstring for the nineteen-member universe and the two computes it records.
#
# goal-rapid-microscope-iter-2 (J-01's browser gap + J-02 test infra) extends it once more, again
# in place (never rewritten — this file's own long-standing rule): stages the two ALREADY-COMMITTED
# PG SIP tick-dataset fixtures (tests/fixtures/datasets/*.json — the exact on-disk DatasetStore file
# shape, so a plain copy suffices; never a pointer at, or copy of, the real .data/datasets store)
# into this rig's own throwaway $ROOT/datasets before backend start, mirroring how the datasets dir
# was already exported (TAPEOLOGY_DATASET_DIR) but left with zero tick shards. This closes the gap
# iteration 1 left open: the Microscope Readiness panel could only be proven via API/text-extract
# through this mandated rig, never a real non-empty screenshot (T-10). Real, non-fabricated, but
# deliberately small — seeding the full 18-dataset/12-symbol-day corpus is deferred to whichever
# LATER iteration first needs it (J-06/J-08/J-09), per the rubric's "smallest fix that unblocks now."
#
# The default root name changes to playbook-iter8-replay-fixture-qa (a genuinely FRESH root, never
# an earlier one reused) — the universe/signature composition is wider again, and the script's own
# long-standing rule ("use a fresh root whenever the seeded composition changed") applies to this
# extension exactly as it would to detector logic.
#
# goal-rapid-microscope-iter-18 extends this file once more, again in place: after the tick-dataset
# fixtures above stage, it also runs seed_micro_graduation_iter18_fixture.py (a plain dataset +
# vault-shard + real evaluate_sealed_verdict() call, never a hand-rolled JSON blob) so J-07's own
# GET /research/desk/micro/graduation finally photographs a real, non-empty, discriminating
# families entry on this rig instead of the honest-but-non-discriminating empty state every prior
# browser pass recorded. Uses a symbol (PGQA) distinct from the PG tick fixtures above so the two
# seed steps' datasets never collide.
#
# Usage:
#   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
#
#   root_dir  Fresh root to seed (default: ${TMPDIR:-/tmp}/playbook-iter8-replay-fixture-qa). Use a
#             FRESH one whenever detector logic, the back-scan module, OR the seeded fixture
#             composition changed: playbook records are append-only and keyed
#             (session_date, playbook_input_signature), so a root seeded by an older build would
#             keep serving that build's recorded signals at the same signature.
#   port      Backend port (default: 8301, the era's browser-QA rig convention — pair with
#             `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$BACKEND_DIR/../.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/playbook-iter8-replay-fixture-qa}"
PORT="${2:-8301}"

BAR_DIR="$ROOT/bars"
UNIVERSE_DIR="$ROOT/universe"
PLAYBOOK_DIR="$ROOT/playbook"
PLAYBOOK_LOG_DIR="$ROOT/playbook_runs"
PLAYBOOK_BACKSCAN_LOG_DIR="$ROOT/playbook_backscan_runs"
PLAYBOOK_EVIDENCE_CACHE_DB="$ROOT/playbook_evidence_cache.db"
SCREEN_DIR="$ROOT/screen"
DATASET_DIR="$ROOT/datasets"
BAR_INDEX_DB="$ROOT/bar_index.db"
DATASET_INDEX_DB="$ROOT/dataset_index.db"
JOURNAL_DB="$ROOT/journal.db"

mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
         "$PLAYBOOK_BACKSCAN_LOG_DIR" "$SCREEN_DIR" "$DATASET_DIR"

# goal-rapid-microscope-iter-2: seed the two already-committed PG SIP tick-dataset fixtures (a
# plain file copy — the fixture IS the on-disk DatasetStore shape already) so J-01's Microscope
# Readiness panel finally photographs a real, non-empty shard table through this rig instead of an
# empty corpus (see the header comment above).
cp "$BACKEND_DIR/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json" "$DATASET_DIR/"
cp "$BACKEND_DIR/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json" "$DATASET_DIR/"

export TAPEOLOGY_BAR_DIR="$BAR_DIR"
export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR="$PLAYBOOK_LOG_DIR"
export TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR="$PLAYBOOK_BACKSCAN_LOG_DIR"
export TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB="$PLAYBOOK_EVIDENCE_CACHE_DB"
export TAPEOLOGY_DESK_SCREEN_DIR="$SCREEN_DIR"
export TAPEOLOGY_DATASET_DIR="$DATASET_DIR"
export TAPEOLOGY_BAR_INDEX_DB="$BAR_INDEX_DB"
export TAPEOLOGY_DATASET_INDEX_DB="$DATASET_INDEX_DB"
export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"

"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_playbook_iter8_replay_rig.py" "$ROOT"

# goal-rapid-microscope-iter-18 (J-07): seed ONE real, discriminating graduation family through the
# now-fixed (r9/TR-30) evaluate_sealed_verdict() -- see seed_micro_graduation_iter18_fixture.py's
# own docstring for the full seven-step sequence this exercises for real.
"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_graduation_iter18_fixture.py" "$ROOT"

echo "[playbook-iter8-replay-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
for var in TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR \
           TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR \
           TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB \
           TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB \
           TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB; do
  echo "[playbook-iter8-replay-fixture-scoped-backend] $var=${!var}" >&2
done

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
