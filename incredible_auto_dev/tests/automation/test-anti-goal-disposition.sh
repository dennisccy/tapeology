#!/usr/bin/env bash
# test-anti-goal-disposition.sh — the three-state anti-goal ledger.
#
# `resolved: true` must keep meaning "genuinely discharged". An owner decision that a
# still-unresolved finding belongs to a future named revision or to framework backlog is a
# DIFFERENT state, and must not be expressible by flipping `resolved`. These tests prove the
# general rule; none of them mention a product session id, and the one test that reads a real
# session's ledger discovers it rather than hard-coding it.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LIB="$ROOT/scripts/automation/lib/anti_goal_disposition.py"

pass=0; fail=0
ok()   { echo "  PASS  $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL  $1"; fail=$((fail+1)); }
check(){ if [[ "$2" == "$3" ]]; then ok "$1"; else bad "$1 (expected '$3', got '$2')"; fi; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Classify one violation object (JSON on stdin) -> prints the state token.
classify() {
  python3 - "$LIB" <<PY
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("agd", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.classify(json.loads(r'''$1'''))[0])
PY
}

_DISP='"kind":"framework_backlog","blocks_current_era":false,"ruled_at":"2026-01-01T00:00:00Z","ruling":"owner ruled framework-owned","future_revision_or_backlog":"backlog: scripts/automation/**"'

echo "=== anti-goal disposition: three distinct states ==="

# The module's own self-test carries the fine-grained matrix (A-G plus mutation guards).
if python3 "$LIB" self-test >/dev/null 2>&1; then
  ok "module self-test (A-G matrix + fail-closed guards)"
else
  bad "module self-test"; python3 "$LIB" self-test
fi

# A. unresolved minor, no disposition -> BLOCKS
check "A: unresolved minor + no disposition -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false}')" "blocking"

# B. unresolved CRITICAL + valid non-blocking disposition -> STILL BLOCKS
check "B: unresolved critical + disposition -> still blocking" \
  "$(classify "{\"iter\":\"i\",\"severity\":\"critical\",\"resolved\":false,\"owner_disposition\":{$_DISP}}")" \
  "blocking"

# C. unresolved minor + malformed / unknown disposition -> BLOCKS
check "C1: unknown kind -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":{"kind":"whatever","blocks_current_era":false,"ruled_at":"t","ruling":"r","future_revision_or_backlog":"b"}}')" \
  "blocking"
check "C2: blocks_current_era true -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":{"kind":"framework_backlog","blocks_current_era":true,"ruled_at":"t","ruling":"r","future_revision_or_backlog":"b"}}')" \
  "blocking"
check "C3: disposition not an object -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":"framework_backlog"}')" \
  "blocking"

# D. valid deferred_named_revision -> NON-BLOCKING
check "D: valid deferred_named_revision -> non_blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":{"kind":"deferred_named_revision","blocks_current_era":false,"ruled_at":"t","ruling":"r","future_revision_or_backlog":"rev 2"}}')" \
  "non_blocking"

# E. valid framework_backlog -> NON-BLOCKING
check "E: valid framework_backlog -> non_blocking" \
  "$(classify "{\"iter\":\"i\",\"severity\":\"minor\",\"resolved\":false,\"owner_disposition\":{$_DISP}}")" \
  "non_blocking"

# F. resolved:true -> its own state, never counted as a deferral
check "F: resolved true -> resolved" \
  "$(classify '{"iter":"i","severity":"minor","resolved":true}')" "resolved"

# G. a tripped (or unattested) escalation condition outranks a deferral
check "G1: escalation tripped -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":{"kind":"deferred_named_revision","blocks_current_era":false,"ruled_at":"t","ruling":"r","future_revision_or_backlog":"rev 2","escalation_condition":"re-score CRITICAL if a caller appears","escalation_tripped":true}}')" \
  "blocking"
check "G2: escalation unattested -> blocking" \
  "$(classify '{"iter":"i","severity":"minor","resolved":false,"owner_disposition":{"kind":"deferred_named_revision","blocks_current_era":false,"ruled_at":"t","ruling":"r","future_revision_or_backlog":"rev 2","escalation_condition":"re-score CRITICAL if a caller appears"}}')" \
  "blocking"

# --- summary CLI: counts + exit code -----------------------------------------
cat > "$TMP/hist.json" <<'JSON'
{"journeys":{},"anti_goal_violations":[
 {"iter":"a","severity":"minor","resolved":true},
 {"iter":"b","severity":"minor","resolved":false},
 {"iter":"c","severity":"minor","resolved":false,
  "owner_disposition":{"kind":"framework_backlog","blocks_current_era":false,
   "ruled_at":"t","ruling":"r","future_revision_or_backlog":"b"}}
],"updated_at":"t"}
JSON
out="$(python3 "$LIB" summary "$TMP/hist.json" 2>&1)"; rc=$?
check "summary: exit 1 while a blocking entry remains" "$rc" "1"
if grep -q "resolved=1" <<<"$out" && grep -q "unresolved_blocking=1" <<<"$out" \
   && grep -q "unresolved_non_blocking=1" <<<"$out"; then
  ok "summary: three states counted separately"
else
  bad "summary: three states counted separately -- got: $out"
fi

python3 - "$TMP/hist.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["anti_goal_violations"][1]["owner_disposition"] = {
    "kind": "deferred_named_revision", "blocks_current_era": False,
    "ruled_at": "t", "ruling": "r", "future_revision_or_backlog": "rev 2"}
json.dump(d, open(p, "w"))
PY
python3 "$LIB" summary "$TMP/hist.json" >/dev/null 2>&1
check "summary: exit 0 once every open entry is dispositioned" "$?" "0"

# --- H. a real session ledger, discovered not hard-coded ----------------------
# Generic on purpose: whichever goal sessions exist, each must be internally consistent, and
# any session whose journeys are all passing must reach zero BLOCKING entries or say why.
shopt -s nullglob
histories=("$ROOT"/../runs/goal-session-*/state/journey-history.json)
[[ ${#histories[@]} -eq 0 ]] && histories=("$ROOT"/runs/goal-session-*/state/journey-history.json)
if [[ ${#histories[@]} -eq 0 ]]; then
  echo "  SKIP  H: no goal-session ledger on disk (framework-only checkout)"
else
  for h in "${histories[@]}"; do
    sid="$(basename "$(dirname "$(dirname "$h")")")"
    read -r total blocking nonblocking resolved crit < <(python3 - "$LIB" "$h" <<'PY'
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("agd", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
d = json.load(open(sys.argv[2]))
c = m.summarize(d.get("anti_goal_violations", []))
print(c["total"], c["unresolved_blocking"], c["unresolved_non_blocking"],
      c["resolved"], c["unresolved_critical"])
PY
)
    if [[ "$total" -eq $((blocking + nonblocking + resolved)) ]]; then
      ok "H[$sid]: states partition the ledger ($total = $blocking blocking + $nonblocking non-blocking + $resolved resolved)"
    else
      bad "H[$sid]: states do not partition the ledger"
    fi
    check "H[$sid]: no unresolved critical is ever non-blocking" "$crit" "0"
  done
fi

echo
echo "=== Results: $pass passed, $fail failed ==="
[[ $fail -eq 0 ]]
