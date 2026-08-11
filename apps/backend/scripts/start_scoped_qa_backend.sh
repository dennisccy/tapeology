#!/usr/bin/env bash
# start_scoped_qa_backend.sh — put the FIXTURE-SCOPED backend on the QA port, replacing whatever
# is listening there.
#
# This is tapeology's STORE_SCOPE_PREPARE_CMD: the framework's store-scope guard
# (incredible_auto_dev/scripts/automation/store-scope/store-scope.sh) runs it ONCE when
# assert_scoped_qa_backend.py says the backend a browser lane is about to drive is not the rig,
# then re-runs the assert. Nothing here decides anything — the assert does; this script only tries
# to make the assert true.
#
# WHY IT MAY KILL THE OPERATOR'S OWN BACKEND: on this host the QA port (8301) is also where the
# operator runs a backend bound to the REAL apps/backend/.data/ store. A browser lane driving that
# backend is exactly the goal-playbook-iter-8 defect (three real playbook records + an un-prunable
# back-scan ledger row written by a replayed "Run Backscan" click). Replacing the listener for the
# duration of a QA pass is the lesser cost, and it is disclosed: the replaced process's command line
# is written to <log-dir>/replaced-listener-<port>.txt so the operator (or the next agent) can
# restart it verbatim.
#
# Usage: start_scoped_qa_backend.sh [root_dir] [port]
#   root_dir  fresh scoped root (default: ${TMPDIR:-/tmp}/tapeology-store-scope-qa/rig).
#             RECREATED on every call: the playbook/bar/universe stores are append-only, so a
#             re-seed into a used root would collide instead of producing the rig's own composition.
#             (Which is why the replaced-listener record is written BESIDE the root, not inside it.)
#   port      QA backend port (default: $CHAIN_BACKEND_PORT, else 8301)
# Exit: 0 = a scoped backend answers /health on the port · 1 = it does not
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ROOT="${1:-${TMPDIR:-/tmp}/tapeology-store-scope-qa/rig}"
PORT="${2:-${CHAIN_BACKEND_PORT:-8301}}"
LOG="${STORE_SCOPE_QA_BACKEND_LOG:-${TMPDIR:-/tmp}/tapeology-store-scope-qa/backend-${PORT}.log}"

# Refuse to wipe anything that is not obviously a throwaway QA root — a bug here would delete a
# real store, which is the opposite of this script's whole purpose.
case "$ROOT" in
  *"/.data"*|"$BACKEND_DIR"|"$BACKEND_DIR/"*)
    echo "[scoped-qa-backend] REFUSING: root '$ROOT' is inside the backend tree / a .data store." >&2
    exit 1 ;;
  ""|"/"|"$HOME") echo "[scoped-qa-backend] REFUSING: root '$ROOT' is not a scoped path." >&2; exit 1 ;;
esac

mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# 1. Free the port, disclosing what was there. The record lives BESIDE the root, never inside it:
# step 2 wipes the root (append-only stores cannot be re-seeded in place), which would delete the
# very disclosure that lets the operator restart what this script replaced.
REPLACED_RECORD="$(dirname "$LOG")/replaced-listener-${PORT}.txt"
_pids="$(lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$_pids" ]]; then
  {
    echo "# Replaced by start_scoped_qa_backend.sh at $(date -u +%Y-%m-%dT%H:%M:%SZ) on port $PORT"
    for p in $_pids; do
      echo "pid=$p cmd=$(tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null || echo '?')"
    done
  } > "$REPLACED_RECORD" 2>/dev/null || true
  echo "[scoped-qa-backend] Replacing the listener on :$PORT (pids: $(echo "$_pids" | tr '\n' ' ')) — its command line is recorded in $REPLACED_RECORD so it can be restarted verbatim." >&2
  # shellcheck disable=SC2086
  kill $_pids 2>/dev/null || true
  for _ in $(seq 1 20); do
    sleep 0.5
    lsof -ti "tcp:$PORT" -sTCP:LISTEN >/dev/null 2>&1 || break
  done
  # shellcheck disable=SC2086
  lsof -ti "tcp:$PORT" -sTCP:LISTEN >/dev/null 2>&1 && kill -9 $_pids 2>/dev/null || true
fi

# 2. Fresh root (append-only stores cannot be re-seeded in place), then the ONE mandatory launcher.
rm -rf "$ROOT" 2>/dev/null || true
mkdir -p "$ROOT" 2>/dev/null || true
echo "[scoped-qa-backend] Seeding + starting the fixture rig at root=$ROOT port=$PORT (log: $LOG)" >&2
nohup bash "$SCRIPT_DIR/qa_playbook_iter7_fixture_scoped_backend.sh" "$ROOT" "$PORT" > "$LOG" 2>&1 &

# 3. Wait for health. The seed walks ~16 fixture members plus two playbook computes before uvicorn
# binds, so the budget is generous; a shorter one would report a working rig as a failure.
for _ in $(seq 1 240); do
  sleep 1
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://localhost:$PORT/health" 2>/dev/null || echo 000)"
  [[ "$code" =~ ^[23] ]] && { echo "[scoped-qa-backend] Scoped backend healthy on :$PORT (root=$ROOT)."; exit 0; }
done

echo "[scoped-qa-backend] Scoped backend did NOT become healthy on :$PORT within the budget — see $LOG" >&2
tail -n 25 "$LOG" >&2 2>/dev/null || true
exit 1
