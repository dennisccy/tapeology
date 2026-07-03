#!/usr/bin/env bash
# Deterministic prep for the goal-proposer: refresh the candidate PnL scan.
# Runs at GOAL_ACHIEVED with env: SESSION_ID, REPO_ROOT, GOAL_FILE, SESSION_DIR, LEDGER_PATH.
# Never fatal — the proposer treats a missing scan as "pipeline not ready yet" (guidance §4).
set -uo pipefail

BACKEND="$REPO_ROOT/apps/backend"
OUT="$SESSION_DIR/state/pnl-scan.json"
PY="$BACKEND/.venv/bin/python"

mkdir -p "$(dirname "$OUT")"

if [ -x "$PY" ] && "$PY" -c "import app.research.pnl_scan" >/dev/null 2>&1; then
  if (cd "$BACKEND" && timeout 600 "$PY" -m app.research.pnl_scan --out "$OUT"); then
    echo "post-goal: PnL scan written to $OUT"
  else
    echo "post-goal: PnL scan failed (non-fatal); removing stale output so the proposer treats it as absent"
    rm -f "$OUT" 2>/dev/null || true
  fi
else
  echo "post-goal: app.research.pnl_scan not built yet — skipping (proposer notes absence)"
fi

exit 0
