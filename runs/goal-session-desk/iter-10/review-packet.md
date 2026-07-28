# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/docs/goal.md b/docs/goal.md
index e29b188..d914c31 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -639,3 +639,16 @@ audits; only ever grow more specific, never weaker):**
   single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and
   `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value
   journey just to keep the loop alive is a failure. *(critical)*
+
+**Host protection (added 2026-07-28 — a physical constraint of the host, not product scope):**
+
+- **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
+  2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips
+  with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
+  beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
+  (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and memory/task
+  bounds), every heavy path respects them: headless engine runs self-wrap under the mask, and
+  interactive pump sessions are launched via `scripts/automation/host-guard-exec.sh claude`
+  (the engine pauses `AWAITING_HOST_GUARD`, resumable, on an unconfined pump). Never disable,
+  widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows
+  the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*
diff --git a/incredible_auto_dev/.claude/commands/goal.md b/incredible_auto_dev/.claude/commands/goal.md
index c779238..0c6f066 100644
--- a/incredible_auto_dev/.claude/commands/goal.md
+++ b/incredible_auto_dev/.claude/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,10 +12,18 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Launch the engine** in the background (Bash with run_in_background) and
+2. **Host-guard check** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1` and `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`):
+   compare `taskset -cp $$` against `HOST_GUARD_CPU_LIST`. If this session's
+   affinity is wider than the mask, STOP and tell the user to relaunch Claude
+   Code via `scripts/automation/host-guard-exec.sh claude` — subagents and their
+   Bash children inherit THIS session's cpuset, confinement can only be applied
+   at launch, and the engine's iteration gate pauses (AWAITING_HOST_GUARD) on an
+   unconfined pump, so starting now would waste a session.
+3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
-3. **Run the pump loop** from the skill: await requests with
+4. **Run the pump loop** from the skill: await requests with
    `scripts/automation/goal-await-dispatch.sh` (foreground, `--max-wait 500`),
    dispatch each returned request as a subagent (`subagent_type` = the request's
    `agent`, `prompt` passed verbatim; pass the request's `model` as the Agent
@@ -29,7 +37,7 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    pauses, and in the final status block. The full chain narrative is in the
    timestamped `runs/goal-session-<sid>/engine.log` (tell the user to `tail -f`
    it); you do not read it.
-4. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
+5. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
    `status` and the next step.
 
 This runs the work as interactive subagents in THIS session (billed to your
diff --git a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
index 44f43c1..5a38352 100644
--- a/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/.claude/skills/goal-interactive-dispatch.md
@@ -146,6 +146,25 @@ one `goal-await-dispatch.sh` call together (multiple Agent calls in one message)
 then write all of their `.res` files. Request file names are unique, so two
 concurrent requests never collide.
 
+## Host-guard confinement (interactive pump)
+
+The engine's own self-wrap (run-goal.sh) confines only the HEADLESS engine tree.
+Interactive dispatches — every subagent, and every `pytest`/build/browser those
+subagents run through Bash — execute as descendants of THIS foreground CLI
+session, so they inherit whatever CPU/memory confinement this session was
+launched with, and nothing can retrofit it afterwards. When the project declares
+host caps (`project-extensions/host-guard/host-guard.env`), the session must be
+launched through the wrapper:
+
+    scripts/automation/host-guard-exec.sh claude
+
+With `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine verifies the pump's cpuset
+(via the `pid=` line in `.pump-alive`) at each iteration boundary and pauses the
+session (`AWAITING_HOST_GUARD`, resumable) if the pump is wider than
+`HOST_GUARD_CPU_LIST`. If that pause fires, relaunch the CLI via the wrapper and
+`/goal-resume` — do not disable the flag to make the pause go away; the caps
+exist because unconfined goal-mode load has hard-reset the host.
+
 ## Usage sidecar (token telemetry — protocol v2, optional, best-effort)
 
 Headless dispatches record per-invocation token usage (`claude_usage` telemetry
diff --git a/incredible_auto_dev/commands/goal.md b/incredible_auto_dev/commands/goal.md
index c779238..0c6f066 100644
--- a/incredible_auto_dev/commands/goal.md
+++ b/incredible_auto_dev/commands/goal.md
@@ -1,7 +1,7 @@
 ---
 description: Run Goal Mode until the goal is achieved or an existing rule halts/pauses it, inside this Claude Code session (interactive dispatch — bills to your interactive plan allowance).
 argument-hint: "[session-id] [extra run-goal.sh flags]"
-allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Read, Task, Write
+allowed-tools: Bash(./scripts/automation/run-goal.sh:*), Bash(scripts/automation/goal-await-dispatch.sh:*), Bash(jq:*), Bash(cat:*), Bash(ls:*), Bash(taskset:*), Read, Task, Write
 ---
 You are the **pump** for goal mode. Run the EXISTING goal-mode engine until the
 goal is achieved, blocked, halted, or paused by its existing rules. Do NOT add
@@ -12,10 +12,18 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
 1. **Session id:** parse `$ARGUMENTS`. The first token is the session id; if there
    is no first token, generate one like `interactive-<YYYY-MM-DD>-<short>` and
    tell the user what you chose. Any remaining tokens are passthrough flags.
-2. **Launch the engine** in the background (Bash with run_in_background) and
+2. **Host-guard check** (only when `project-extensions/host-guard/host-guard.env`
+   exists with `HOST_GUARD_ENABLED=1` and `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`):
+   compare `taskset -cp $$` against `HOST_GUARD_CPU_LIST`. If this session's
+   affinity is wider than the mask, STOP and tell the user to relaunch Claude
+   Code via `scripts/automation/host-guard-exec.sh claude` — subagents and their
+   Bash children inherit THIS session's cpuset, confinement can only be applied
+   at launch, and the engine's iteration gate pauses (AWAITING_HOST_GUARD) on an
+   unconfined pump, so starting now would waste a session.
+3. **Launch the engine** in the background (Bash with run_in_background) and
    capture its PID:
    `./scripts/automation/run-goal.sh --session-id <sid> --interactive <passthrough flags>`
-3. **Run the pump loop** from the skill: await requests with
+4. **Run the pump loop** from the skill: await requests with
    `scripts/automation/goal-await-dispatch.sh` (foreground, `--max-wait 500`),
    dispatch each returned request as a subagent (`subagent_type` = the request's
    `agent`, `prompt` passed verbatim; pass the request's `model` as the Agent
@@ -29,7 +37,7 @@ First read `.claude/skills/goal-interactive-dispatch.md` and follow it exactly.
    pauses, and in the final status block. The full chain narrative is in the
    timestamped `runs/goal-session-<sid>/engine.log` (tell the user to `tail -f`
    it); you do not read it.
-4. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
+5. **On exit**, read `runs/goal-session-<sid>/session.json` and report the final
    `status` and the next step.
 
 This runs the work as interactive subagents in THIS session (billed to your
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index d4e3029..f95bf60 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -109,6 +109,7 @@ Halt verdicts:
 - `AWAITING_BLUEPRINT_APPROVAL` — only when you ran with `--require-blueprint-approval`: paused after baseline (or after a structural blueprint change) for you to review `state/blueprint.md`; `--resume` to continue (counts as approval)
 - `AWAITING_INTENT_REVIEW` — only when you ran with `--intent-checkpoint` / `--intent-checkpoint-at N`: paused once mid-session for you to read `runs/goal-session-<sid>/intent-review.md` ("is this still the product you wanted?"); `--resume` to continue (counts as acknowledgment; fires once per session)
 - `AWAITING_GITHUB_AUTH` — paused at startup because per-iter push is on but a push to `origin` wouldn't authenticate (expired GitHub session, or no remote); fix auth (the run will offer to launch `gh auth login` for you when interactive) and `--resume`
+- `AWAITING_HOST_GUARD` — only on hosts that declare hardware caps (`project-extensions/host-guard/host-guard.env`): the hwmon forensics sampler could not be started, the engine's CPU-affinity wrap did not take effect, a declared launcher lost its HOST-GUARD cap block, or the interactive pump session is not confined to the declared CPU mask (relaunch the CLI via `scripts/automation/host-guard-exec.sh <cli>`); fix the printed reason and `--resume` — see `docs/host-guard.md`
 
 ## Common workflows
 
diff --git a/incredible_auto_dev/scripts/automation/lib/plain-language.sh b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
index 5a93c4d..bc359fa 100644
--- a/incredible_auto_dev/scripts/automation/lib/plain-language.sh
+++ b/incredible_auto_dev/scripts/automation/lib/plain-language.sh
@@ -29,6 +29,7 @@ AWAITING_INTENT_REVIEW
 AWAITING_PUMP
 AWAITING_GITHUB_AUTH
 AWAITING_DISK
+AWAITING_HOST_GUARD
 KEYS
   return 0
 }
@@ -107,6 +108,10 @@ explain_goal_status() {
       echo "  The chain paused because this computer is low on disk space — it never builds in that state."
       echo "  Free some space (the command above helps), then resume."
       ;;
+    AWAITING_HOST_GUARD)
+      echo "  The chain paused because this computer's hardware protection is not in place — it never builds unprotected."
+      echo "  Follow the reason printed above (project-extensions/host-guard/README.md), then resume."
+      ;;
   esac
   echo "  Read more: ${PLAIN_LANG_GUIDE}  (what each status and verdict means)"
   if [[ -n "$_sid" && -n "$_root" && -f "$_root/reports/goal-session-${_sid}-index.html" ]]; then
diff --git a/incredible_auto_dev/scripts/automation/lib/telemetry.sh b/incredible_auto_dev/scripts/automation/lib/telemetry.sh
index 2f37213..f91f764 100755
--- a/incredible_auto_dev/scripts/automation/lib/telemetry.sh
+++ b/incredible_auto_dev/scripts/automation/lib/telemetry.sh
@@ -79,6 +79,26 @@ record_telemetry_event() {
   fi
 }
 
+# ── engine-step wall-time attribution (RETRO-1, ops-hardening retro) ─────────
+# Wraps big NON-AGENT engine steps (the full/lean sub-pipeline dispatch, the
+# showcase-tail join) so the wall-time report can name what the former
+# "unattributed (glue)" residual — 200-625m per full iteration — actually was.
+# Single-slot by design: wrapped regions must not nest (the run-goal.sh call
+# sites are strictly sequential). A begin without a matching done is dropped.
+_engine_step_begin() {
+  _ENGINE_STEP_NAME="${1:?engine step name}"
+  _ENGINE_STEP_T0="$(date +%s)"
+}
+
+_engine_step_done() {
+  [[ -n "${_ENGINE_STEP_NAME:-}" ]] || return 0
+  local dur=$(( $(date +%s) - ${_ENGINE_STEP_T0:-$(date +%s)} ))
+  record_telemetry_event "engine_step" "$(jq -cn --arg s "$_ENGINE_STEP_NAME" --argjson d "$dur" \
+      '{step:$s, duration_seconds:$d}' 2>/dev/null \
+    || printf '{"step":"%s","duration_seconds":%d}' "$_ENGINE_STEP_NAME" "$dur")"
+  _ENGINE_STEP_NAME=""
+}
+
 # Convenience: record an agent invocation start.
 #
 # Call this as a BARE STATEMENT — never via command substitution $(...).
diff --git a/incredible_auto_dev/scripts/automation/run-goal.sh b/incredible_auto_dev/scripts/automation/run-goal.sh
index d1c1a44..6291321 100755
--- a/incredible_auto_dev/scripts/automation/run-goal.sh
+++ b/incredible_auto_dev/scripts/automation/run-goal.sh
@@ -65,6 +65,10 @@
 #   AWAITING_GITHUB_AUTH - preflight found no GitHub push access; fix auth, then --resume
 #   AWAITING_DISK    - free disk under the hard floor even after automatic aggressive cleanup;
 #                      free space or run scripts/automation/tmp-doctor.sh --aggressive, then --resume
+#   AWAITING_HOST_GUARD - host-guard preflight/gate failed (hwmon sampler dead and unstartable,
+#                      CPU-affinity wrap absent, a launcher lost its HOST-GUARD cap block, or the
+#                      interactive pump session is unconfined); fix per the printed reason
+#                      (project-extensions/host-guard/README.md), then --resume
 #
 # Quota exhaustion is NOT a halt: claude_with_quota_retry transparently sleeps
 # until the quota resets and resumes.
@@ -83,6 +87,49 @@ source "$SCRIPT_DIR/lib/goal-gates.sh"
 source "$SCRIPT_DIR/lib/engine-lock.sh"
 source "$SCRIPT_DIR/lib/plain-language.sh"
 
+# ── Host-guard self-wrap (hardware protection) ─────────────────────────────
+# Origin: a mini-PC host hard-reset instantly (no OOM, no thermal log, no
+# panic) under goal-mode's bursty all-core load — a power/VRM transient trip.
+# When the project declares host caps (project-extensions/host-guard/
+# host-guard.env), re-exec the ENTIRE engine tree under an SMT-aware
+# CPU-affinity mask (taskset — hard, inherited, instantaneous) plus, when a
+# user manager is reachable, a systemd user scope adding AllowedCPUs (cgroup
+# cpuset — inherited by every descendant, cannot be widened from inside) and
+# CPUQuota/MemoryHigh/TasksMax as averaging/aggregate backstops. Sits BEFORE
+# extract_cli_arg so "$@" is still the original argv. HOST_GUARD_WRAPPED
+# guards recursion — deliberately NOT CHAIN_-prefixed so the REL-2 ambient
+# snapshot above stays clean. Absent/disabled env file ⇒ no-op (the framework
+# stays project-neutral). Details: project-extensions/host-guard/README.md.
+_HOST_GUARD_ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+if [[ -z "${HOST_GUARD_WRAPPED:-}" && -f "$_HOST_GUARD_ENV_FILE" ]] \
+   && command -v taskset >/dev/null 2>&1; then
+  # shellcheck disable=SC1090
+  source "$_HOST_GUARD_ENV_FILE"
+  if [[ "${HOST_GUARD_ENABLED:-0}" == "1" && -n "${HOST_GUARD_CPU_LIST:-}" ]]; then
+    export HOST_GUARD_WRAPPED=1
+    _HG_PROPS=( -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}"
+                -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}"
+                -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" )
+    # --expand-environment=no: systemd ExecStart otherwise $-expands argv.
+    if systemd-run --user --scope --quiet --expand-environment=no -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" true 2>/dev/null; then
+      # Full confinement: cpuset + quota backstops (AllowedCPUs probe passed).
+      exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+        --unit "chain-goal-hostguard-$$" \
+        -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" "${_HG_PROPS[@]}" \
+        taskset -c "$HOST_GUARD_CPU_LIST" "$SCRIPT_DIR/run-goal.sh" "$@"
+    elif systemd-run --user --scope --quiet --expand-environment=no -p CPUQuota=10% true 2>/dev/null; then
+      # cpuset controller not delegated: scope backstops + taskset mask only.
+      exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+        --unit "chain-goal-hostguard-$$" \
+        "${_HG_PROPS[@]}" \
+        taskset -c "$HOST_GUARD_CPU_LIST" "$SCRIPT_DIR/run-goal.sh" "$@"
+    else
+      # No user manager at all (headless SSH etc.): affinity mask still applies.
+      exec taskset -c "$HOST_GUARD_CPU_LIST" "$SCRIPT_DIR/run-goal.sh" "$@"
+    fi
+  fi
+fi
+
 # Pull --cli (and --force-cli) out of the args BEFORE the existing parse loop,
 # so the loop below sees only its known flags.
 extract_cli_arg "$@" || exit $?
@@ -792,6 +839,182 @@ PY
   exit 0
 }
 
+# ── Host-guard preflight + iteration gate (hardware protection) ────────────
+# Origin: a mini-PC host hard-reset repeatedly under goal-mode load with
+# NOTHING in the journal — instant power/VRM transient trips, invisible to
+# sysstat's 10-minute cadence. When the project declares host caps
+# (project-extensions/host-guard/host-guard.env), the engine must not run
+# unprotected: verify the affinity wrap (top of this script) took effect and
+# the 1 Hz hwmon forensics sampler is alive — auto-starting the sampler first
+# (self-heal, like the disk guard's sweep), pausing (AWAITING_HOST_GUARD,
+# resumable) only when self-heal fails. Absent or disabled host-guard.env ⇒
+# no-op (framework stays project-neutral).
+_host_guard_mask_width() { # "0-3,8-11" → 8; 0 when unparseable
+  local list="${1:-}" n=0 part a b
+  [[ -n "$list" ]] || { echo 0; return 0; }
+  local -a parts=()
+  IFS=',' read -ra parts <<< "$list"
+  for part in "${parts[@]}"; do
+    if [[ "$part" =~ ^[0-9]+-[0-9]+$ ]]; then
+      a="${part%-*}"; b="${part#*-}"
+      if (( b >= a )); then n=$(( n + b - a + 1 )); fi
+    elif [[ "$part" =~ ^[0-9]+$ ]]; then
+      n=$(( n + 1 ))
+    fi
+  done
+  echo "$n"
+}
+_host_guard_sampler_path() { # project-local copy wins; framework copy is the default
+  local proj="$REPO_ROOT/project-extensions/host-guard/hwmon-log.sh"
+  if [[ -f "$proj" ]]; then printf '%s' "$proj"; else printf '%s' "$SCRIPT_DIR/host-guard/hwmon-log.sh"; fi
+}
+_host_guard_latest_tctl() { # newest Tctl (°C) from the sampler csv; empty if missing/stale
+  local csv="$REPO_ROOT/logs/hwmon/hwmon.csv" mtime line t
+  [[ -f "$csv" ]] || return 0
+  mtime=$(stat -c %Y "$csv" 2>/dev/null || echo 0)
+  (( EPOCHSECONDS - mtime <= 15 )) || return 0
+  line=$(tail -n 1 "$csv" 2>/dev/null || true)
+  t="${line#*,}"; t="${t%%,*}"
+  [[ "$t" =~ ^[0-9]+$ ]] && printf '%s' "$t"
+  return 0
+}
+_host_guard_pause() { # $1 reason, $2 detected_at_step — pause AWAITING_HOST_GUARD (resumable) and exit
+  local reason="$1" step="${2:-preflight}"
+  echo "[run-goal] Host-guard check failed — pausing (AWAITING_HOST_GUARD)."
+  echo "[run-goal]   reason: $reason"
+  python3 - <<PY
+import json, datetime
+d = json.load(open("$SESSION_JSON"))
+d["status"] = "AWAITING_HOST_GUARD"
+d["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
+import os as _os, tempfile as _tf
+_fd, _tmp = _tf.mkstemp(dir=_os.path.dirname("$SESSION_JSON") or ".", suffix=".sjtmp")
+with _os.fdopen(_fd, "w") as _f:
+    json.dump(d, _f, indent=2)
+    _f.write("\n")
+_os.replace(_tmp, "$SESSION_JSON")
+PY
+  record_telemetry_event "halt" "$(printf '{"reason":"AWAITING_HOST_GUARD","detected_at_step":"%s"}' "$step")"
+  echo ""
+  echo "Fix the host-guard issue (project-extensions/host-guard/README.md), then resume:"
+  echo "  ./scripts/automation/run-goal.sh --resume --session-id $SESSION_ID"
+  explain_goal_status "AWAITING_HOST_GUARD" "$SESSION_ID" "$REPO_ROOT"
+  echo "════════════════════════════════════════════════════════════════════"
+  exit 0
+}
+preflight_host_guard() {
+  local hg_env="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+  [[ -f "$hg_env" ]] || return 0
+  # shellcheck disable=SC1090
+  source "$hg_env"
+  [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+  local sampler fail_reason=""
+  sampler="$(_host_guard_sampler_path)"
+
+  # 1. Forensics sampler alive + csv fresh (self-heal: try to start it first).
+  if [[ -f "$sampler" ]]; then
+    if ! HOST_GUARD_ROOT="$REPO_ROOT" bash "$sampler" status >/dev/null 2>&1; then
+      echo "[run-goal] host-guard: hwmon sampler not running — auto-starting."
+      HOST_GUARD_ROOT="$REPO_ROOT" bash "$sampler" start || true
+      sleep 2
+      HOST_GUARD_ROOT="$REPO_ROOT" bash "$sampler" status >/dev/null 2>&1 \
+        || fail_reason="hwmon sampler failed to start (try: bash $sampler start)"
+    fi
+  else
+    fail_reason="sampler script missing: $sampler"
+  fi
+
+  # 2. Affinity wrap took effect: REAL allowed CPUs ≤ declared mask width.
+  # Read Cpus_allowed_list, not `nproc` — nproc honors OMP_NUM_THREADS, so a
+  # BLAS thread-cap env var would fake a confined engine (false PASS).
+  if [[ -z "$fail_reason" ]]; then
+    local width allowed_list allowed_n
+    width=$(_host_guard_mask_width "${HOST_GUARD_CPU_LIST:-}")
+    allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null)
+    allowed_n=$(_host_guard_mask_width "$allowed_list")
+    if (( width > 0 && allowed_n > width )); then
+      fail_reason="engine not confined to HOST_GUARD_CPU_LIST=${HOST_GUARD_CPU_LIST:-} (Cpus_allowed_list=$allowed_list = $allowed_n CPUs > mask width $width — the taskset wrap did not take effect)"
+    fi
+  fi
+
+  # 3. Launcher cap blocks — project-declared list (HOST_GUARD_MARKER_FILES,
+  # space-separated repo-relative paths); enforced only once the project's
+  # launcher caps have landed (HOST_GUARD_REQUIRE_MARKERS=1).
+  if [[ -z "$fail_reason" && "${HOST_GUARD_REQUIRE_MARKERS:-0}" == "1" && -n "${HOST_GUARD_MARKER_FILES:-}" ]]; then
+    local lsc
+    for lsc in ${HOST_GUARD_MARKER_FILES}; do
+      if [[ -f "$REPO_ROOT/$lsc" ]] && ! grep -q "HOST-GUARD" "$REPO_ROOT/$lsc"; then
+        fail_reason="launcher $lsc lost its HOST-GUARD cap block (host-guard regression)"
+        break
+      fi
+    done
+  fi
+
+  [[ -n "$fail_reason" ]] || return 0
+  _host_guard_pause "$fail_reason" "preflight"
+}
+host_guard_iteration_gate() {
+  # Top-of-loop, never mid-iteration. (a) thermal cooldown: when the hwmon csv
+  # is fresh and Tctl ≥ HOST_GUARD_TCTL_PAUSE, wait until ≤ _RESUME (bounded by
+  # _MAX_WAIT — then proceed loudly; the gate is defense-in-depth, not a halt).
+  # (b) interactive pump confinement: the systemd/taskset self-wrap cannot
+  # confine agents dispatched INSIDE the foreground CLI session, so when
+  # HOST_GUARD_REQUIRE_PUMP_CONFINED=1 verify the pump process's own cpuset and
+  # pause (resumable) if it is wider than the declared mask.
+  local hg_env="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+  [[ -f "$hg_env" ]] || return 0
+  # shellcheck disable=SC1090
+  source "$hg_env"
+  [[ "${HOST_GUARD_ENABLED:-0}" == "1" ]] || return 0
+
+  local pause_c="${HOST_GUARD_TCTL_PAUSE:-90}" resume_c="${HOST_GUARD_TCTL_RESUME:-80}"
+  local poll="${HOST_GUARD_TCTL_POLL:-15}" max_wait="${HOST_GUARD_TCTL_MAX_WAIT:-1800}"
+  local waited=0 tctl
+  while :; do
+    tctl="$(_host_guard_latest_tctl)"
+    [[ "$tctl" =~ ^[0-9]+$ ]] || break   # no fresh telemetry → nothing to gate on
+    if (( waited == 0 )); then
+      if (( tctl < pause_c )); then break; fi
+      echo "[run-goal] host-guard: Tctl ${tctl}°C ≥ ${pause_c}°C — cooling down before the next iteration (resumes < ${resume_c}°C)."
+      record_telemetry_event "host_guard_cooldown" "$(printf '{"tctl_c":%s}' "$tctl")"
+    else
+      if (( tctl <= resume_c )); then
+        echo "[run-goal] host-guard: cooled to ${tctl}°C after ${waited}s — continuing."
+        break
+      fi
+      if (( waited >= max_wait )); then
+        echo "[run-goal] host-guard: still ${tctl}°C after ${waited}s (max ${max_wait}s) — continuing anyway; check cooling."
+        break
+      fi
+    fi
+    sleep "$poll"; waited=$(( waited + poll ))
+  done
+
+  if [[ "${HOST_GUARD_REQUIRE_PUMP_CONFINED:-0}" == "1" && "${AGENT_BACKEND:-}" == "interactive" ]]; then
+    local hb="${CHAIN_DISPATCH_DIR:-$GOAL_SESSION_DIR_LOCAL/dispatch}/.pump-alive"
+    local pump_pid="" hb_age width allowed_list allowed_n
+    if [[ -f "$hb" ]]; then
+      hb_age=$(( EPOCHSECONDS - $(stat -c %Y "$hb" 2>/dev/null || echo 0) ))
+      pump_pid=$(sed -n 's/^pid=\([0-9][0-9]*\)$/\1/p' "$hb" 2>/dev/null | head -n 1)
+      # Heartbeat present but no pid line (ident disabled): confinement cannot be
+      # verified — that must be loud, not a silent bypass.
+      if [[ -z "$pump_pid" && "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" ]]; then
+        _host_guard_pause "cannot verify pump confinement: $hb has no pid= line (heartbeat ident disabled?) — re-enable the pump ident or set HOST_GUARD_REQUIRE_PUMP_CONFINED=0" "iteration_gate"
+      fi
+    fi
+    if [[ -n "$pump_pid" && "$hb_age" -le "${HOST_GUARD_PUMP_HB_FRESH:-180}" && -r "/proc/$pump_pid/status" ]]; then
+      width=$(_host_guard_mask_width "${HOST_GUARD_CPU_LIST:-}")
+      allowed_list=$(awk -F'\t' '/^Cpus_allowed_list/{print $2}' "/proc/$pump_pid/status" 2>/dev/null)
+      allowed_n=$(_host_guard_mask_width "$allowed_list")
+      if (( width > 0 && allowed_n > width )); then
+        write_session_summary "AWAITING_HOST_GUARD" "$CURRENT_ITER"
+        _host_guard_pause "interactive pump (pid $pump_pid) is unconfined: Cpus_allowed_list=$allowed_list = $allowed_n CPUs > mask width $width — relaunch the pump CLI under the guard, e.g. scripts/automation/host-guard-exec.sh claude" "iteration_gate"
+      fi
+    fi
+  fi
+  return 0
+}
+
 # ── Preflight doctor (REL-2) ──────────────────────────────────────────────
 # Advisory BY CONSTRUCTION: the doctor observes and reports; it must never be
 # able to stop a session (a broken doctor gating the engine would invert its
@@ -1079,7 +1302,7 @@ if $( [[ "$AUTO_RELEASE" == "true" ]] && echo "True" || echo "False" ):
 d["push_per_iter"] = $( [[ "$PUSH_PER_ITER" == "true" ]] && echo "True" || echo "False" )
 d["push_branch"] = "$PUSH_BRANCH"
 d["agent_backend"] = "$AGENT_BACKEND"
-if "$RUN_MODE" == "resume" and d.get("status") in ("REGRESSION_HALT", "AWAITING_BLUEPRINT_APPROVAL", "AWAITING_PUMP", "AWAITING_INTENT_REVIEW", "AWAITING_GITHUB_AUTH", "AWAITING_DISK"):
+if "$RUN_MODE" == "resume" and d.get("status") in ("REGRESSION_HALT", "AWAITING_BLUEPRINT_APPROVAL", "AWAITING_PUMP", "AWAITING_INTENT_REVIEW", "AWAITING_GITHUB_AUTH", "AWAITING_DISK", "AWAITING_HOST_GUARD"):
   d["status"] = "in_progress"
 import os as _os, tempfile as _tf
 _fd, _tmp = _tf.mkstemp(dir=_os.path.dirname("$SESSION_JSON") or ".", suffix=".sjtmp")
@@ -1451,6 +1674,11 @@ chain_tmp_janitor
 # (AWAITING_DISK) only when the tmp root's filesystem is still critically low.
 preflight_disk_space
 
+# Host-guard preflight: forensics sampler + affinity confinement. Repeated
+# instant hardware resets under goal-mode load make unprotected engine runs
+# unacceptable on hosts that declare caps; no-op everywhere else.
+preflight_host_guard
+
 # Verify we can push to GitHub before the loop starts (once; fresh + resume).
 # Fails fast / pauses here rather than stalling on a credential prompt mid-run.
 preflight_github_access
@@ -1486,6 +1714,12 @@ while true; do
     exit 0
   fi
 
+  # 1d. Host-guard gate — top of the loop, never mid-iteration: thermal
+  # cooldown (wait out heat-soak between iterations) + interactive pump
+  # confinement (the self-wrap cannot cover agents inside the foreground CLI).
+  # No-op unless the project declares host caps.
+  host_guard_iteration_gate
+
   # 1b. Blueprint approval gate (coherence). Pauses at the TOP of the loop —
   # never mid-iteration — so the blueprint is never re-drafted out from under the
   # human. Two triggers: (initial) baseline drafted a blueprint not yet approved;
@@ -1888,6 +2122,12 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
 
   echo "[run-goal] Iter spec depth: $DEPTH"
   echo "[run-goal] Target journeys: ${TARGET_JOURNEYS:-(none parsed)}"
+  # Expose the parsed journey list to run-phase.sh / browser-qa-phase.sh so
+  # detect_frontend_in_plan (lib/common.sh) forces the browser lane whenever this
+  # iteration names journeys — even if the plan mis-states "Frontend Present: no"
+  # (the iter-8 CLOSURE-FAIL root cause). Exported unconditionally (empty = none)
+  # so a prior iteration's value never leaks forward.
+  export CHAIN_GOAL_TARGET_JOURNEYS="$TARGET_JOURNEYS"
   record_telemetry_event "iter_dispatch" "$(jq -cn --arg d "$DEPTH" --arg tj "$TARGET_JOURNEYS" '{depth:$d, target_journeys:$tj}' 2>/dev/null || printf '{"depth":"%s"}' "$DEPTH")"
 
   # 2c. Join the previous iteration's background showcase tail (if any) BEFORE
@@ -1895,7 +2135,9 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
   # reviewer of THIS iteration see exactly the tree the sequential ordering
   # would have produced. Overlapping it with the decomposer above is where the
   # ~6-13 min saving comes from.
+  _engine_step_begin "showcase-join"
   _join_showcase_tail
+  _engine_step_done
 
   # Tmp hygiene boundary — the per-iteration cleanup step. The previous
   # iteration's background showcase tail has just been joined (its demo
@@ -1917,16 +2159,22 @@ Do NOT write code or implement anything. The iteration spec and any blueprint ed
     echo "[run-goal] Dispatching FULL pipeline via run-phase.sh ${_full_extra_args[*]} ..."
     if grep -q '\-\-no-finalize' "$SCRIPT_DIR/run-phase.sh"; then
       printf 'full' > "$ITER_DIR/depth-dispatched"   # SPEED-4: cadence streak input (depth that actually runs)
+      _engine_step_begin "full-pipeline"
       bash "$SCRIPT_DIR/run-phase.sh" "$ITER_NAME" "${_full_extra_args[@]}" || _exec_rc=$?
+      _engine_step_done
     else
       echo "[run-goal] run-phase.sh does not yet support --no-finalize. Falling back to lean for safety." >&2
       printf 'lean' > "$ITER_DIR/depth-dispatched"
+      _engine_step_begin "lean-pipeline"
       bash "$SCRIPT_DIR/goal-iter-lean.sh" "$ITER_NAME" || _exec_rc=$?
+      _engine_step_done
     fi
   else
     echo "[run-goal] Dispatching LEAN pipeline via goal-iter-lean.sh ..."
     printf 'lean' > "$ITER_DIR/depth-dispatched"
+    _engine_step_begin "lean-pipeline"
     bash "$SCRIPT_DIR/goal-iter-lean.sh" "$ITER_NAME" || _exec_rc=$?
+    _engine_step_done
   fi
 
   # Transport/dispatch-unavailable (exit 70) from the interactive backend: the
diff --git a/incredible_auto_dev/skills/goal-interactive-dispatch.md b/incredible_auto_dev/skills/goal-interactive-dispatch.md
index 44f43c1..5a38352 100644
--- a/incredible_auto_dev/skills/goal-interactive-dispatch.md
+++ b/incredible_auto_dev/skills/goal-interactive-dispatch.md
@@ -146,6 +146,25 @@ one `goal-await-dispatch.sh` call together (multiple Agent calls in one message)
 then write all of their `.res` files. Request file names are unique, so two
 concurrent requests never collide.
 
+## Host-guard confinement (interactive pump)
+
+The engine's own self-wrap (run-goal.sh) confines only the HEADLESS engine tree.
+Interactive dispatches — every subagent, and every `pytest`/build/browser those
+subagents run through Bash — execute as descendants of THIS foreground CLI
+session, so they inherit whatever CPU/memory confinement this session was
+launched with, and nothing can retrofit it afterwards. When the project declares
+host caps (`project-extensions/host-guard/host-guard.env`), the session must be
+launched through the wrapper:
+
+    scripts/automation/host-guard-exec.sh claude
+
+With `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`, the engine verifies the pump's cpuset
+(via the `pid=` line in `.pump-alive`) at each iteration boundary and pauses the
+session (`AWAITING_HOST_GUARD`, resumable) if the pump is wider than
+`HOST_GUARD_CPU_LIST`. If that pause fires, relaunch the CLI via the wrapper and
+`/goal-resume` — do not disable the flag to make the pause go away; the caps
+exist because unconfined goal-mode load has hard-reset the host.
+
 ## Usage sidecar (token telemetry — protocol v2, optional, best-effort)
 
 Headless dispatches record per-invocation token usage (`claude_usage` telemetry
```

## Excluded-path stat (dependency/lockfile visibility)

 docs/handoffs/goal-desk-iter-9-dev.md            | 20 +++++++++
 reports/goal-session-desk-index.html             | 11 +++--
 runs/goal-session-desk/.engine.lock/epoch        |  2 +-
 runs/goal-session-desk/.engine.lock/pid          |  2 +-
 runs/goal-session-desk/dispatch/.pump-alive      |  4 +-
 runs/goal-session-desk/engine.pid                |  2 +-
 runs/goal-session-desk/iter-10/goal-slice.md     | 13 ++++++
 runs/goal-session-desk/journey-scripts/J-08.json |  5 +++
 runs/goal-session-desk/session.json              |  6 +--
 runs/goal-session-desk/summary.md                | 57 +++++++++++++++---------
 runs/goal-session-desk/telemetry.jsonl           | 31 +++++++++++++
 runs/goal-session-desk/trace/trace.jsonl         |  2 +
 12 files changed, 123 insertions(+), 32 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
