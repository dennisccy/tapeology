#!/usr/bin/env bash
# test-store-scope-guard.sh — unit tests for scripts/automation/store-scope/store-scope.sh
# and the lib/replay-lane.sh wrappers that call it.
#
# WHY THIS EXISTS: a goal-mode iteration shipped a *launcher* that stands up a
# fixture-scoped backend, and then the pipeline's own browser/replay lanes ran
# against whatever backend happened to be listening — writing real records and a
# run-ledger row into the operator's append-only store. A launcher nothing is
# obliged to use is not a mechanism. This guard makes it one:
#
#   • require  — refuse to run any browser lane unless the project's own assert
#     command proves the backend under test is the scoped one (one prepare
#     attempt in between, when the project declares a prepare command);
#   • snapshot/verify — bracket the run with a manifest of the project's
#     protected store paths and hard-fail on ANY delta, so "the real store was
#     untouched" stops being prose and becomes an artifact.
#
# Absent project-extensions/store-scope/store-scope.env ⇒ every entry point is a
# no-op exiting 0: the framework stays project-neutral (the host-guard
# precedent), and every other project's stdout is byte-identical.
#
# No API calls, no network, no browser; runs in about a second.
#
# shellcheck disable=SC1090,SC1091,SC2015,SC2034
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PASS=0
FAIL=0
assert() {
  if [[ "$2" == "pass" ]]; then echo "  PASS  $1"; PASS=$((PASS + 1)); else echo "  FAIL  $1"; FAIL=$((FAIL + 1)); fi
}

WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

SBX="$WORK/proj"
mkdir -p "$SBX"
cp -r "$ENGINE_ROOT/scripts" "$SBX/"
GUARD="$SBX/scripts/automation/store-scope/store-scope.sh"
LIB="$SBX/scripts/automation/lib/replay-lane.sh"

STORE="$SBX/apps/backend/.data"
mkdir -p "$STORE/playbook" "$STORE/playbook_runs"
echo '{"id":"pre-existing"}' > "$STORE/playbook/record-1.json"

write_env() {  # $1 = extra lines
  mkdir -p "$SBX/project-extensions/store-scope"
  {
    echo 'STORE_SCOPE_ENABLED=1'
    echo 'STORE_SCOPE_LABEL="test rig"'
    echo 'STORE_SCOPE_PROTECTED_PATHS="apps/backend/.data/playbook apps/backend/.data/playbook_runs"'
    printf '%s\n' "$1"
  } > "$SBX/project-extensions/store-scope/store-scope.env"
}

run_guard() {  # subcommand + args; echoes rc
  local rc=0
  ( cd "$SBX" && STORE_SCOPE_ROOT="$SBX" bash "$GUARD" "$@" ) >"$WORK/guard.out" 2>&1 || rc=$?
  echo "$rc"
}

echo "== 1. No project config: every entry point is a neutral no-op =="
rm -rf "$SBX/project-extensions/store-scope"
rc="$(run_guard require)";                          [[ "$rc" == "0" ]] && assert "require no-ops without config" pass || assert "require no-ops without config (rc=$rc)" fail
rc="$(run_guard snapshot "$WORK/m0.txt")";          [[ "$rc" == "0" ]] && assert "snapshot no-ops without config" pass || assert "snapshot no-ops without config (rc=$rc)" fail
rc="$(run_guard verify "$WORK/m0.txt" "$WORK/r0.md")"; [[ "$rc" == "0" ]] && assert "verify no-ops without config" pass || assert "verify no-ops without config (rc=$rc)" fail
[[ ! -f "$WORK/r0.md" ]] && assert "no disclosure artifact written without config" pass || assert "no disclosure artifact written without config" fail

echo "== 2. require: the project's assert command decides =="
write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"'
cat > "$SBX/scripts-assert.sh" <<'EOF'
#!/usr/bin/env bash
echo "assert ran" >> "$SBX_STAMP"
[[ -f "$SBX_SCOPED_MARKER" ]]
EOF
export SBX_STAMP="$WORK/assert.log" SBX_SCOPED_MARKER="$WORK/scoped.marker"
: > "$SBX_STAMP"; : > "$SBX_SCOPED_MARKER"
rc="$(run_guard require)"
[[ "$rc" == "0" ]] && assert "require passes when the assert command succeeds" pass || assert "require passes when the assert command succeeds (rc=$rc)" fail
[[ "$(wc -l < "$SBX_STAMP")" == "1" ]] && assert "assert command ran exactly once on the happy path" pass || assert "assert command ran exactly once on the happy path" fail

echo "== 3. require: assert fails, prepare rescues it =="
write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"
STORE_SCOPE_PREPARE_CMD="bash scripts-prepare.sh"'
cat > "$SBX/scripts-prepare.sh" <<'EOF'
#!/usr/bin/env bash
echo "prepare ran" >> "$SBX_PREP_STAMP"
touch "$SBX_SCOPED_MARKER"
EOF
export SBX_PREP_STAMP="$WORK/prepare.log"
: > "$SBX_STAMP"; : > "$SBX_PREP_STAMP"; rm -f "$SBX_SCOPED_MARKER"
rc="$(run_guard require)"
[[ "$rc" == "0" ]] && assert "require passes after the prepare command scopes the backend" pass || assert "require passes after prepare (rc=$rc)" fail
[[ "$(wc -l < "$SBX_PREP_STAMP")" == "1" ]] && assert "prepare ran exactly once" pass || assert "prepare ran exactly once" fail
[[ "$(wc -l < "$SBX_STAMP")" == "2" ]] && assert "assert re-ran after prepare (2 invocations)" pass || assert "assert re-ran after prepare" fail

echo "== 4. require: prepare cannot scope it -> refusal (rc 1) =="
cat > "$SBX/scripts-prepare.sh" <<'EOF'
#!/usr/bin/env bash
echo "prepare ran" >> "$SBX_PREP_STAMP"
EOF
: > "$SBX_STAMP"; : > "$SBX_PREP_STAMP"; rm -f "$SBX_SCOPED_MARKER"
rc="$(run_guard require)"
[[ "$rc" == "1" ]] && assert "require REFUSES when the backend cannot be scoped" pass || assert "require REFUSES when the backend cannot be scoped (rc=$rc)" fail
grep -qi "not scoped\|refus" "$WORK/guard.out" && assert "refusal says why, loudly" pass || assert "refusal says why, loudly" fail

echo "== 5. snapshot/verify: an untouched store verifies CLEAN =="
write_env ''
: > "$WORK/m1.txt"
rc="$(run_guard snapshot "$WORK/m1.txt")"
[[ "$rc" == "0" && -s "$WORK/m1.txt" ]] && assert "snapshot writes a manifest" pass || assert "snapshot writes a manifest (rc=$rc)" fail
rc="$(run_guard verify "$WORK/m1.txt" "$WORK/r1.md")"
[[ "$rc" == "0" ]] && assert "verify is CLEAN when nothing changed" pass || assert "verify is CLEAN when nothing changed (rc=$rc)" fail
grep -q "CLEAN" "$WORK/r1.md" && assert "clean run still writes the disclosure artifact" pass || assert "clean run still writes the disclosure artifact" fail

echo "== 6. verify: a NEW record file under a protected path is a BREACH =="
# This is the iteration-8 failure, reproduced: a replay run appended a playbook
# record + a back-scan ledger row into the operator's real store.
echo '{"id":"playbook-2026-06-22"}' > "$STORE/playbook/record-2.json"
echo '{"status":"done"}' > "$STORE/playbook_runs/backscanrun-1.json"
rc="$(run_guard verify "$WORK/m1.txt" "$WORK/r2.md")"
[[ "$rc" == "1" ]] && assert "verify FAILS on a new file under a protected path" pass || assert "verify FAILS on a new file under a protected path (rc=$rc)" fail
grep -q "BREACH" "$WORK/r2.md" && assert "breach report is headlined BREACH" pass || assert "breach report is headlined BREACH" fail
grep -q "record-2.json" "$WORK/r2.md" && assert "breach report names the added record file" pass || assert "breach report names the added record file" fail
grep -q "backscanrun-1.json" "$WORK/r2.md" && assert "breach report names the added ledger file" pass || assert "breach report names the added ledger file" fail

echo "== 7. verify: a MODIFIED protected file is a BREACH too =="
rm -f "$STORE/playbook/record-2.json" "$STORE/playbook_runs/backscanrun-1.json"
: > "$WORK/m2.txt"; run_guard snapshot "$WORK/m2.txt" >/dev/null
sleep 0.01
echo '{"id":"pre-existing","tampered":true}' > "$STORE/playbook/record-1.json"
rc="$(run_guard verify "$WORK/m2.txt" "$WORK/r3.md")"
[[ "$rc" == "1" ]] && assert "verify FAILS on a modified protected file" pass || assert "verify FAILS on a modified protected file (rc=$rc)" fail
grep -q "record-1.json" "$WORK/r3.md" && assert "breach report names the modified file" pass || assert "breach report names the modified file" fail

echo "== 8. lib/replay-lane.sh wrappers =="
run_wrapper() {  # $1 = wrapper call
  (
    set -euo pipefail
    source "$LIB"
    REPO_ROOT="$SBX"
    STORE_SCOPE_ROOT="$SBX"
    eval "$1"
  ) >"$WORK/wrap.out" 2>&1
}
write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"'
: > "$SBX_STAMP"; : > "$SBX_SCOPED_MARKER"
rc=0; run_wrapper 'store_scope_require' || rc=$?
[[ "$rc" == "0" ]] && assert "store_scope_require wrapper passes through success" pass || assert "store_scope_require wrapper passes through success (rc=$rc)" fail
rm -f "$SBX_SCOPED_MARKER"
rc=0; run_wrapper 'store_scope_require' || rc=$?
[[ "$rc" == "1" ]] && assert "store_scope_require wrapper passes through refusal" pass || assert "store_scope_require wrapper passes through refusal (rc=$rc)" fail
rc=0; run_wrapper "store_scope_snapshot '$WORK/m3.txt'" || rc=$?
[[ "$rc" == "0" && -s "$WORK/m3.txt" ]] && assert "store_scope_snapshot wrapper writes the manifest" pass || assert "store_scope_snapshot wrapper writes the manifest (rc=$rc)" fail
echo '{"id":"another"}' > "$STORE/playbook/record-3.json"
rc=0; run_wrapper "store_scope_verify '$WORK/m3.txt' '$WORK/r4.md'" || rc=$?
[[ "$rc" == "1" ]] && assert "store_scope_verify wrapper passes through the breach" pass || assert "store_scope_verify wrapper passes through the breach (rc=$rc)" fail
rm -f "$STORE/playbook/record-3.json"

# The wrappers must survive a stripped engine (no store-scope dir at all) —
# a project that never syncs the feature keeps today's behavior exactly.
mv "$SBX/scripts/automation/store-scope" "$WORK/store-scope-away"
rc=0; run_wrapper 'store_scope_require' || rc=$?
[[ "$rc" == "0" ]] && assert "wrappers no-op when the guard script is absent" pass || assert "wrappers no-op when the guard script is absent (rc=$rc)" fail
mv "$WORK/store-scope-away" "$SBX/scripts/automation/store-scope"

echo ""
echo "test-store-scope-guard: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
