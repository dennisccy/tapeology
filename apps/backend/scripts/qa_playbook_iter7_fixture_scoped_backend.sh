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
# goal-rapid-microscope-iter-24 extends this file once more, again in place: after the iter-18
# graduation seed step, it also runs seed_micro_scout_iter24_j09_fixture.py (a real
# setup_id="capitulation" playbook signal anchored on the already-staged real PG SIP tick dataset,
# then a real scout.register_screen_and_walkforward_check() call — never a hand-rolled JSON blob)
# so journey-scripts/J-09.json's own golden replay finally has a genuine, non-vacuous pilot-study
# Scout Ledger row to assert against on this rig, instead of the honest-but-non-discriminating
# empty state every prior pass recorded for J-09's own sections. Reuses the ALREADY-STAGED PG
# dataset the iter-2 extension above copies in, so no new dataset (hence no new collision surface)
# is introduced.
#
# goal-rapid-microscope-iter-18 extends this file once more, again in place: after the tick-dataset
# fixtures above stage, it also runs seed_micro_graduation_iter18_fixture.py (a plain dataset +
# vault-shard + real evaluate_sealed_verdict() call, never a hand-rolled JSON blob) so J-07's own
# GET /research/desk/micro/graduation finally photographs a real, non-empty, discriminating
# families entry on this rig instead of the honest-but-non-discriminating empty state every prior
# browser pass recorded. Uses a symbol (PGQA) distinct from the PG tick fixtures above so the two
# seed steps' datasets never collide.
#
# goal-rapid-microscope-iter-25 extends this file once more, again in place: after every seed step
# above, it also runs seed_micro_vault_iter25_sealed_fixture.py (a plain dataset + a REAL
# vault.seal_shard() call that is NEVER assigned/exposed, never a hand-rolled JSON blob), giving
# this rig a SECOND vault shard that stays permanently sealed alongside the iter-18 one's exposed
# shard. Before this, the rig's Validation Vault table only ever showed an exposed row -- the
# sealed-row opaque render branch (page.tsx:6810-6819) and the "Sealed at" bare-date cell
# (page.tsx:6807) had no fixture data to trigger against for three browser-QA rounds. Uses a symbol
# (PGVAULT) distinct from every other symbol this rig's other seed scripts use.
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

# goal-hypothesis-foundry-iter-2 (J-01 step 5 / TC-1/TC-2/TC-3): close the QA-rig visibility gap
# `lessons.md` iter-1 named — `foundry_source_registry.resolve_foundry_dir()` derives the Foundry
# directory as a `foundry` SIBLING of `TAPEOLOGY_DATASET_DIR` when `TAPEOLOGY_FOUNDRY_DIR` is
# unset, which this rig's own `$DATASET_DIR=$ROOT/datasets` resolves to `$ROOT/foundry` — a fresh,
# never-recorded directory, so `GET /research/desk/micro/foundry` served `era_open_baseline: null`
# here even though the real recorded artifact
# (`apps/backend/.data/foundry/era_open_baseline.json`) is genuine. Fix: copy that REAL artifact
# (read-only source, never written to) into this rig's own scoped `$ROOT/foundry/` before backend
# start — the exact same "plain file copy of an already-committed/recorded real artifact into the
# scoped root" pattern the two `cp` lines above already use for the PG tick-dataset fixtures, so
# `GET /research/desk/micro/foundry` on THIS rig now serves the genuine recorded values, never an
# invented one (the anti-goal `lessons.md` explicitly warns against). Honest-absence fallback: if
# the operator has never run the one-time recording script
# (`scripts/record_foundry_era_open_baseline.py`), there is nothing genuine to copy — the rig then
# correctly falls back to the pre-existing honest `era_open_baseline: null` state, exactly like a
# fresh install (never fabricated).
FOUNDRY_DIR="$ROOT/foundry"
REAL_FOUNDRY_BASELINE="$BACKEND_DIR/.data/foundry/era_open_baseline.json"
if [[ -f "$REAL_FOUNDRY_BASELINE" ]]; then
  mkdir -p "$FOUNDRY_DIR"
  cp "$REAL_FOUNDRY_BASELINE" "$FOUNDRY_DIR/"
fi

# goal-hypothesis-foundry-iter-6 (J-07 / TC-9): the SAME visibility gap, one artifact later. The new
# `exhaust_progress` key of `GET /research/desk/micro/foundry` is read per-request by
# `foundry_runner.read_exhaust_progress(foundry_dir, ...)` through the identical
# `get_foundry_dir()`-scoped resolver the era-open baseline above uses — so the real Foundry trial
# ledger the real exhaust CLI wrote (`apps/backend/.data/foundry/foundry_trial_ledger.jsonl` + its
# `.chain_head.json` tail-anchor sidecar) is INVISIBLE to this rig unless it is copied in, and the
# rig would otherwise render the honest-but-wrong pre-first-read-lock EmptyState instead of the real
# completed-exhaust state. Fix: the identical plain-file-copy-of-a-real-recorded-artifact pattern.
# Both files are copied together and only together — the sidecar anchors the hash chain of the exact
# ledger bytes beside it, so copying one without the other would hand this rig a mismatched chain.
# The transient single-flight lock file (`foundry_exhaust_runner.lock`) is deliberately NOT copied:
# it is live OS-advisory-lock state belonging to the machine that ran the CLI, not recorded
# evidence, and this rig's own live probe re-creates it. Honest-absence fallback: if the operator
# has never run `scripts/run_hypothesis_foundry_real_exhaust.py`, there is nothing genuine to copy —
# the rig then correctly falls back to the honest pre-lock `first_read_lock_recorded: false` state,
# exactly like a fresh install (never fabricated).
REAL_FOUNDRY_LEDGER="$BACKEND_DIR/.data/foundry/foundry_trial_ledger.jsonl"
REAL_FOUNDRY_LEDGER_HEAD="$REAL_FOUNDRY_LEDGER.chain_head.json"
if [[ -f "$REAL_FOUNDRY_LEDGER" ]]; then
  mkdir -p "$FOUNDRY_DIR"
  cp "$REAL_FOUNDRY_LEDGER" "$FOUNDRY_DIR/"
  if [[ -f "$REAL_FOUNDRY_LEDGER_HEAD" ]]; then
    cp "$REAL_FOUNDRY_LEDGER_HEAD" "$FOUNDRY_DIR/"
  fi
fi

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

# goal-rapid-microscope-iter-24 (J-09): seed ONE real, non-vacuous pilot-study (Study 3,
# capitulation_exhaustion_pilot) Scout Ledger row through the real
# scout.register_screen_and_walkforward_check() production entry point -- see
# seed_micro_scout_iter24_j09_fixture.py's own docstring for the full sequence this exercises.
"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_scout_iter24_j09_fixture.py" "$ROOT"

# goal-rapid-microscope-iter-25 (J-06): seed ONE new REAL dataset + REAL vault.seal_shard() call
# that is NEVER assigned/exposed -- see seed_micro_vault_iter25_sealed_fixture.py's own docstring
# for the full reasoning. Gives this rig a second, permanently-sealed shard alongside the iter-18
# seeder's exposed one.
"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_vault_iter25_sealed_fixture.py" "$ROOT"

# goal-rapid-microscope-iter-19 (TC-9): the ONE list of store-root vars this launch bound the
# backend to -- shared by the stderr echo below AND the durable manifest file, so the two can never
# silently diverge. Closes iteration 18's evaluator finding ("the quality report states that the
# browser lane used your real data store. It did not.") by giving a QA/reviewer/auditor report a
# FIXED-PATH file to cite, independent of whether this launch's own stdout/stderr was captured.
_TAPEOLOGY_SCOPED_VARS=(
  TAPEOLOGY_BAR_DIR TAPEOLOGY_DESK_UNIVERSE_DIR TAPEOLOGY_DESK_PLAYBOOK_DIR
  TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR
  TAPEOLOGY_PLAYBOOK_EVIDENCE_CACHE_DB
  TAPEOLOGY_DESK_SCREEN_DIR TAPEOLOGY_DATASET_DIR TAPEOLOGY_BAR_INDEX_DB
  TAPEOLOGY_DATASET_INDEX_DB TAPEOLOGY_JOURNAL_DB
)

echo "[playbook-iter8-replay-fixture-scoped-backend] root=$ROOT port=$PORT" >&2
for var in "${_TAPEOLOGY_SCOPED_VARS[@]}"; do
  echo "[playbook-iter8-replay-fixture-scoped-backend] $var=${!var}" >&2
done

MANIFEST_PATH="$REPO_ROOT/reports/qa-scoped-backend-store-manifest.md"
mkdir -p "$(dirname "$MANIFEST_PATH")"
{
  echo "# QA fixture-scoped backend store manifest"
  echo
  echo "Written by \`qa_playbook_iter7_fixture_scoped_backend.sh\` at launch (goal-rapid-microscope-"
  echo "iter-19, TC-9) -- the durable record of which store roots THIS launch's backend process is"
  echo "bound to. A quality/QA report describing what the browser/replay lane exercised MUST cite"
  echo "this file (never assert \"real data store\" for a pass launched through this script)."
  echo
  echo "- launched_at_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- root: $ROOT"
  echo "- port: $PORT"
  for var in "${_TAPEOLOGY_SCOPED_VARS[@]}"; do
    echo "- $var: ${!var}"
  done
} > "$MANIFEST_PATH"
echo "[playbook-iter8-replay-fixture-scoped-backend] manifest written to $MANIFEST_PATH" >&2

exec env CHAIN_BACKEND_PORT="$PORT" bash "$REPO_ROOT/scripts/start-backend.sh"
