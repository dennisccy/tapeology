# Iteration diff (bounded)

Files changed: 14. Shown in full: 14.

```diff
diff --git a/README.md b/README.md
index 925a7a0..482cc59 100644
--- a/README.md
+++ b/README.md
@@ -63,7 +63,7 @@ Current capabilities:
 - **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. The top-up job is also reachable from the Desk page's "Top-up" button (below), in addition to the research API and the command line; the coverage check itself has no dedicated page yet, though each screen's briefing row shows a per-timeframe coverage badge — it otherwise remains reachable through the research API.
 - **A daily screening desk over the fetched universe (research API + command-line tool)** — for the latest registered S&P 100 universe snapshot, run a "screen" as of a chosen date: for every member, read its own already-computed tradable level map and summarize the closest support/resistance band into one ranked list — that band's inherited A/B/C conviction class, how far the screen date's closing price sits from it in basis points, and the band's quality score, ranked strongest and closest first. A member with no recorded price bars for that date is reported as an honest "skipped" entry rather than guessed at. Every run is pinned to its exact inputs — the screen date, which universe snapshot was used, the exact configuration in effect, and the bar data on file at the time — so repeating an identical request returns the same saved result instead of writing a duplicate, and a corrupted or tampered saved run is refused rather than silently overwritten. A run reports live progress as it works through the list and can be cancelled mid-flight; only one run proceeds at a time. Past runs can be browsed as lightweight summaries, or fetched in full by date or as the latest recorded result. Triggered explicitly from the command line, the research API, or the Desk page's "Run Screen" button (below) — never automatically.
-- **Desk page** — the third top-level page, reachable from the top navigation bar alongside Cockpit and Structure. Before any screen has ever been run it shows the plain message "Desk screen not computed yet." with enabled "Run Screen" and "Top-up" buttons. Run Screen starts today's screen over the registered universe and shows live progress — how many members have been checked so far and which symbol is currently being processed — with a Cancel control; clicking it again while a run is already in progress does not start a second one, it just shows the same run already under way. Top-up is the first on-screen control for the bar-fetching job described above, with the same live-progress and cancel behavior. Once a screen has run, the page shows four sections in order: a **Provenance** line naming which universe snapshot and date were used, the as-of timestamp, and the app's own internal settings fingerprint and bar-store signature, so two screens can always be told apart or confirmed identical; the **Briefing** — the ranked table itself, with each symbol's side, A/B/C class (captioned "nearest same-class band"), distance from that level in basis points, band score, a badge per timeframe the symbol has bar coverage for, and a tick-evidence badge where a recorded trade-by-trade dataset exists; **Skipped Members**, split into an honest "no bars" group and a "no basis session" group, each shown only when it has entries; and a **Screen History** list of every past run (date, row/skipped counts, and its own provenance summary). Clicking Run Screen before any universe has ever been registered shows an inline error message instead of silently starting a job, and if the backend becomes unreachable while a run's progress is being checked, the page keeps showing the last progress it knew about rather than going blank. Every row in the Screen History list is now clickable: selecting a past date swaps the whole page's Provenance, Briefing, and Skipped Members display to that exact recorded date's own saved screen — a read-back with nothing recomputed — and a banner ("Viewing the recorded screen for `<date>` — not the latest.") appears above the Provenance panel with a one-click "Latest" button that snaps back to the newest screen instantly; a small inline note appears instead if a history click fails or matches no recorded screen, leaving the rest of the page unchanged. Every symbol row in the Briefing and Skipped Members tables — ranked or skipped — is itself a link into the Structure page for that exact symbol and date, arriving there with the symbol and as-of fields already filled in and the tradable-map chart already drawn, no manual re-typing needed; a skipped symbol still lands on Structure's own honest empty/no-data state, which is expected. Hovering anywhere over a ranked or skipped row (not just a small number or badge inside it) shows a tooltip with that row's exact distance and score figures and each timeframe's data-freshness value; clicking the row still opens the Structure page as before.
+- **Desk page** — the third top-level page, reachable from the top navigation bar alongside Cockpit and Structure. Before any screen has ever been run it shows the plain message "Desk screen not computed yet." with enabled "Run Screen" and "Top-up" buttons. Run Screen starts today's screen over the registered universe and shows live progress — how many members have been checked so far and which symbol is currently being processed — with a Cancel control; clicking it again while a run is already in progress does not start a second one, it just shows the same run already under way. Top-up is the first on-screen control for the bar-fetching job described above, with the same live-progress and cancel behavior. Once a screen has run, the page shows four sections in order: a **Provenance** line naming which universe snapshot and date were used, the as-of timestamp, and the app's own internal settings fingerprint and bar-store signature, so two screens can always be told apart or confirmed identical; the **Briefing** — the ranked table itself, with each symbol's side, A/B/C class (captioned "nearest same-class band"), distance from that level in basis points, band score, a badge per timeframe the symbol has bar coverage for, and a tick-evidence badge where a recorded trade-by-trade dataset exists, and a **basis** column naming the exact date of the price bar that row's distance and class were measured from and how many days before the screen's as-of date that bar is dated (rows from a screen recorded before this detail existed honestly show "basis not recorded in this snapshot" instead of a blank or guessed value); **Skipped Members**, split into an honest "no bars" group and a "no basis session" group, each shown only when it has entries; and a **Screen History** list of every past run (date, row/skipped counts, and its own provenance summary). Clicking Run Screen before any universe has ever been registered shows an inline error message instead of silently starting a job, and if the backend becomes unreachable while a run's progress is being checked, the page keeps showing the last progress it knew about rather than going blank. Every row in the Screen History list is now clickable: selecting a past date swaps the whole page's Provenance, Briefing, and Skipped Members display to that exact recorded date's own saved screen — a read-back with nothing recomputed — and a banner ("Viewing the recorded screen for `<date>` — not the latest.") appears above the Provenance panel with a one-click "Latest" button that snaps back to the newest screen instantly; a small inline note appears instead if a history click fails or matches no recorded screen, leaving the rest of the page unchanged. Every symbol row in the Briefing and Skipped Members tables — ranked or skipped — is itself a link into the Structure page for that exact symbol and date, arriving there with the symbol and as-of fields already filled in and the tradable-map chart already drawn, no manual re-typing needed; a skipped symbol still lands on Structure's own honest empty/no-data state, which is expected. Hovering anywhere over a ranked or skipped row (not just a small number or badge inside it) shows a tooltip with that row's exact distance and score figures, the same basis-date and basis-age detail as the new column, and each timeframe's data-freshness value; clicking the row still opens the Structure page as before.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /research/desk/screen`, `POST /research/desk/screen/compute`, `GET /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, S&P 100 universe snapshots, the Desk screen ledger, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
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
diff --git a/incredible_auto_dev/docs/host-guard.md b/incredible_auto_dev/docs/host-guard.md
new file mode 100644
index 0000000..47736fa
--- /dev/null
+++ b/incredible_auto_dev/docs/host-guard.md
@@ -0,0 +1,73 @@
+# Host-guard — hardware protection for goal-mode load
+
+Some hosts (small-form-factor mini-PCs especially) hard-reset under the bursty
+all-core load an autonomous dev chain generates: an instant power/VRM/thermal
+transient trip, with nothing in the journal. Host-guard is the framework's
+opt-in defense: a project declares resource ceilings, and every heavy execution
+path respects them. **With no declaration, every hook is a byte-for-byte no-op**
+— the framework stays project-neutral.
+
+## Activation contract
+
+Create `project-extensions/host-guard/host-guard.env` in the project repo —
+plain `KEY=VALUE` bash assignments, `HOST_GUARD_*` names only. Machine-specific;
+do not copy between checkouts. `HOST_GUARD_ENABLED=0` (or deleting the file)
+disables everything.
+
+| Knob | Meaning | Typical |
+|---|---|---|
+| `HOST_GUARD_ENABLED` | Master switch | `1` |
+| `HOST_GUARD_CPU_LIST` | SMT-aware affinity mask for all heavy work | `"0-3,8-11"` |
+| `HOST_GUARD_BLAS_THREADS` | OMP/OpenBLAS/MKL/numexpr cap per process | physical cores in mask |
+| `HOST_GUARD_CPUQUOTA` | systemd scope average-CPU backstop | `"800%"` |
+| `HOST_GUARD_MEMORY_HIGH` | scope memory ceiling (reclaim/throttle, no OOM-kill) | `"14G"` |
+| `HOST_GUARD_TASKS_MAX` | fork-storm bound | `2048` |
+| `HOST_GUARD_REQUIRE_PUMP_CONFINED` | enforce cpuset on the interactive pump session | `1` |
+| `HOST_GUARD_REQUIRE_MARKERS` + `HOST_GUARD_MARKER_FILES` | require HOST-GUARD cap blocks in listed launcher scripts | project-specific |
+| `HOST_GUARD_TCTL_PAUSE` / `_RESUME` / `_MAX_WAIT` | thermal gate thresholds (°C, °C, s) | `90` / `80` / `1800` |
+| `HOST_GUARD_SAMPLER_INTERVAL` / `_MAX_BYTES` | forensics sampler cadence / csv ring size | `1` / `10485760` |
+
+Running two projects' goal modes on one host: give them **complementary masks**
+(e.g. `0-3,8-11` and `4-7,12-15` on an 8-core/16-thread part) so a burst can
+never light every core, and size `MEMORY_HIGH` so the sum fits in RAM.
+
+## Enforcement layers (all in `scripts/automation/`)
+
+1. **Engine self-wrap** (`run-goal.sh`, top of script) — re-execs the whole
+   engine under `systemd-run --user --scope` with `AllowedCPUs` (cgroup cpuset,
+   inherited by every descendant, cannot be widened from inside) +
+   CPUQuota/MemoryHigh/TasksMax, plus `taskset -c` (also the no-user-bus
+   fallback). Covers **headless** runs completely.
+2. **Pump wrapper** (`host-guard-exec.sh`) — interactive dispatches run inside
+   the foreground CLI session, which the self-wrap cannot reach. Launch the CLI
+   through the wrapper so its whole subtree inherits the same confinement:
+   `scripts/automation/host-guard-exec.sh claude`
+3. **Preflight** (`preflight_host_guard`) — before the loop: forensics sampler
+   alive (auto-started if not), affinity wrap took effect, launcher marker
+   blocks intact. Failure pauses the session `AWAITING_HOST_GUARD` (resumable).
+4. **Iteration gate** (`host_guard_iteration_gate`, top of loop) — thermal
+   cooldown between iterations (wait out heat-soak, bounded), and pump-cpuset
+   verification via the `pid=` line in `.pump-alive` when
+   `HOST_GUARD_REQUIRE_PUMP_CONFINED=1`.
+5. **Forensics sampler** (`host-guard/hwmon-log.sh`) — 1 Hz temps/power/
+   pressure/memory to `<repo>/logs/hwmon/hwmon.csv`, fsync per line, so the
+   final pre-reset second survives a hard reset. `{run|start|stop|status|watch}`;
+   `status`/`start` recognize an externally-run sampler (e.g. a systemd user
+   unit running `run`) by csv freshness and never double-run.
+
+## When `AWAITING_HOST_GUARD` fires
+
+Read the printed reason, fix it, then
+`./scripts/automation/run-goal.sh --resume --session-id <sid>` (or
+`/goal-resume`). The common one: the pump session is unconfined — relaunch the
+CLI via `host-guard-exec.sh` and resume. Do not disable flags to silence the
+pause; the caps exist because unconfined load has hard-reset a host.
+
+## Origin
+
+Built after a GEEKOM A7 Max (Ryzen 9 7940HS) hard-reset five times in eight
+days (2026-07-20 → 2026-07-28) under goal-mode load, three of the resets
+captured at 1 Hz with benign temperatures and low package power — a
+millisecond-scale power transient. Incident forensics and the cap-widening
+verification ladder live in the originating project:
+`trendora/project-extensions/host-guard/README.md`.
diff --git a/incredible_auto_dev/scripts/automation/host-guard-exec.sh b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
new file mode 100755
index 0000000..bb9ac60
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard-exec.sh
@@ -0,0 +1,69 @@
+#!/usr/bin/env bash
+# host-guard-exec.sh — run ANY command under the project's host-guard caps.
+#
+# WHY: the engine's self-wrap (run-goal.sh) confines headless runs, but
+# interactive-pump dispatches execute INSIDE the foreground CLI session
+# (Claude Code / Codex) — children of a process the engine never wrapped.
+# Launch that CLI through this wrapper and every subagent, pytest, bundler,
+# and browser it spawns inherits the same cgroup/affinity confinement:
+#
+#   scripts/automation/host-guard-exec.sh claude
+#   scripts/automation/host-guard-exec.sh -- codex --some-flag
+#
+# The engine can enforce this: with HOST_GUARD_REQUIRE_PUMP_CONFINED=1 in
+# host-guard.env, run-goal.sh's iteration gate verifies the pump process's
+# cpuset and pauses (AWAITING_HOST_GUARD, resumable) if it is unconfined.
+#
+# Repo root: $HOST_GUARD_ROOT override, else git toplevel of $PWD, else $PWD.
+# Absent or disabled host-guard.env ⇒ exec the command unwrapped (with a
+# warning): the framework stays project-neutral.
+set -euo pipefail
+
+[[ "${1:-}" == "--" ]] && shift
+if [[ $# -eq 0 ]]; then
+  echo "Usage: $0 [--] <command> [args...]" >&2
+  exit 2
+fi
+
+ROOT="${HOST_GUARD_ROOT:-$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd)}"
+ENV_FILE="$ROOT/project-extensions/host-guard/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+
+if [[ "${HOST_GUARD_ENABLED:-0}" != "1" || -z "${HOST_GUARD_CPU_LIST:-}" ]] \
+   || ! command -v taskset >/dev/null 2>&1; then
+  echo "[host-guard-exec] no enabled host-guard.env under $ROOT (or no taskset) — running UNCONFINED." >&2
+  exec "$@"
+fi
+
+# BLAS/OpenMP/numexpr worker caps for every descendant (mirrors the launcher
+# HOST-GUARD blocks): N numpy processes must not oversubscribe the mask with
+# nested thread pools.
+if [[ "${HOST_GUARD_BLAS_THREADS:-}" =~ ^[0-9]+$ ]]; then
+  export OMP_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export OPENBLAS_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export MKL_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+  export NUMEXPR_NUM_THREADS="$HOST_GUARD_BLAS_THREADS"
+fi
+
+_PROPS=( -p "CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}"
+         -p "MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G}"
+         -p "TasksMax=${HOST_GUARD_TASKS_MAX:-2048}" )
+
+# --expand-environment=no: systemd ExecStart otherwise $-expands argv ("$$"→"$").
+if systemd-run --user --scope --quiet --expand-environment=no -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" true 2>/dev/null; then
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (cpuset + CPUQuota=${HOST_GUARD_CPUQUOTA:-800%}, MemoryHigh=${HOST_GUARD_MEMORY_HIGH:-18G})." >&2
+  exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+    --unit "chain-pump-hostguard-$$" \
+    -p "AllowedCPUs=$HOST_GUARD_CPU_LIST" "${_PROPS[@]}" \
+    taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+elif systemd-run --user --scope --quiet --expand-environment=no -p CPUQuota=10% true 2>/dev/null; then
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (taskset + scope backstops; cpuset not delegated)." >&2
+  exec systemd-run --user --scope --quiet --collect --expand-environment=no \
+    --unit "chain-pump-hostguard-$$" \
+    "${_PROPS[@]}" \
+    taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+else
+  echo "[host-guard-exec] confining '$1' to CPUs $HOST_GUARD_CPU_LIST (taskset only; no user manager)." >&2
+  exec taskset -c "$HOST_GUARD_CPU_LIST" "$@"
+fi
diff --git a/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
new file mode 100755
index 0000000..e5632fd
--- /dev/null
+++ b/incredible_auto_dev/scripts/automation/host-guard/hwmon-log.sh
@@ -0,0 +1,233 @@
+#!/usr/bin/env bash
+# hwmon-log.sh — 1 Hz hardware telemetry sampler (host-guard crash forensics).
+#
+# WHY: hosts can hard-reset under bursty all-core load with NOTHING in the
+# journal — an instant power/VRM/thermal trip. sysstat's 10-minute cadence
+# straddles the spike. This sampler records temps/power/pressure every second
+# and fsyncs each line, so the final pre-reset second survives the reboot.
+#
+# Usage: hwmon-log.sh {run|start|stop|status|watch}
+#   run    — sample in the foreground (Ctrl+C stops)
+#   start  — background daemon (nohup); pidfile logs/hwmon/hwmon.pid
+#   stop   — stop the daemon
+#   status — exit 0 iff the daemon is alive AND the csv is fresh; prints one line
+#   watch  — live view: latest sample + session max Tctl/PPT (⚠ at Tctl ≥ 90°C)
+#
+# Output: <repo>/logs/hwmon/hwmon.csv (gitignored), ring-rotated at
+# HOST_GUARD_SAMPLER_MAX_BYTES to hwmon.csv.1. Sensors are resolved BY NAME
+# (k10temp/amdgpu/nvme/spd5118/acpitz) — hwmon indexes shift across boots.
+# A missing sensor yields an empty CSV field, never a crash.
+set -euo pipefail
+
+HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
+# Repo root resolution (which repo's logs/ receives the csv):
+#   1. HOST_GUARD_ROOT env override — the engine preflight passes its $REPO_ROOT;
+#   2. framework placement  <root>/scripts/automation/host-guard/ → 3 dirs up;
+#   3. project placement    <root>/project-extensions/host-guard/ → 2 dirs up.
+if [[ -n "${HOST_GUARD_ROOT:-}" ]]; then
+  REPO_ROOT="$(cd "$HOST_GUARD_ROOT" && pwd)"
+elif [[ "$HERE" == */scripts/automation/host-guard ]]; then
+  REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
+else
+  REPO_ROOT="$(cd "$HERE/../.." && pwd)"
+fi
+# Caps env: the project's declaration wins; a copy next to this script is the
+# fallback (project-extensions placement keeps them side by side).
+ENV_FILE="$REPO_ROOT/project-extensions/host-guard/host-guard.env"
+[[ -f "$ENV_FILE" ]] || ENV_FILE="$HERE/host-guard.env"
+# shellcheck disable=SC1090
+[[ -f "$ENV_FILE" ]] && source "$ENV_FILE" || true
+
+INTERVAL="${HOST_GUARD_SAMPLER_INTERVAL:-1}"
+MAX_BYTES="${HOST_GUARD_SAMPLER_MAX_BYTES:-10485760}"
+LOG_DIR="$REPO_ROOT/logs/hwmon"
+CSV="$LOG_DIR/hwmon.csv"
+PIDFILE="$LOG_DIR/hwmon.pid"
+DAEMON_LOG="$LOG_DIR/hwmon.log"
+HEADER="epoch,tctl_c,gpu_edge_c,ppt_w,ppt_avg_w,nvme_c,dimm0_c,dimm1_c,acpitz_c,load1,mem_avail_mb,swap_free_mb,psi_cpu_avg10,psi_mem_avg10"
+
+# ── Sensor resolution (by hwmon name, once at startup) ─────────────────────
+TCTL="" GPU_TEMP="" PPT_NOW="" PPT_AVG="" NVME_T="" DIMM0="" DIMM1="" ACPITZ=""
+resolve_sensors() {
+  local h name
+  for h in /sys/class/hwmon/hwmon*; do
+    [[ -r "$h/name" ]] || continue
+    IFS= read -r name < "$h/name" 2>/dev/null || continue
+    case "$name" in
+      k10temp)
+        if [[ -r "$h/temp1_input" ]]; then TCTL="$h/temp1_input"; fi ;;
+      amdgpu)
+        if [[ -r "$h/temp1_input" ]]; then GPU_TEMP="$h/temp1_input"; fi
+        if [[ -r "$h/power1_input" ]]; then PPT_NOW="$h/power1_input"; fi
+        if [[ -r "$h/power1_average" ]]; then PPT_AVG="$h/power1_average"; fi ;;
+      nvme)
+        if [[ -z "$NVME_T" && -r "$h/temp1_input" ]]; then NVME_T="$h/temp1_input"; fi ;;
+      spd5118)
+        if [[ -z "$DIMM0" && -r "$h/temp1_input" ]]; then DIMM0="$h/temp1_input"
+        elif [[ -z "$DIMM1" && -r "$h/temp1_input" ]]; then DIMM1="$h/temp1_input"; fi ;;
+      acpitz)
+        if [[ -r "$h/temp1_input" ]]; then ACPITZ="$h/temp1_input"; fi ;;
+    esac
+  done
+  return 0
+}
+
+# ── Field readers (never fail, never fork; empty string on any problem) ────
+_read_scaled() { # $1 sysfs path (may be empty), $2 integer divisor
+  local p="${1:-}" div="${2:-1}" v=""
+  [[ -n "$p" ]] || return 0
+  IFS= read -r v < "$p" 2>/dev/null || v=""
+  [[ "$v" =~ ^[0-9]+$ ]] || return 0
+  printf '%s' $(( v / div ))
+  return 0
+}
+_psi_avg10() { # $1 /proc/pressure/{cpu,memory} → the "some avg10" value
+  local p="$1" line=""
+  IFS= read -r line < "$p" 2>/dev/null || line=""
+  [[ "$line" == *avg10=* ]] || return 0
+  line="${line#*avg10=}"
+  printf '%s' "${line%% *}"
+  return 0
+}
+MEM_AVAIL_MB="" SWAP_FREE_MB=""
+_mem_fields() {
+  MEM_AVAIL_MB="" SWAP_FREE_MB=""
+  local k v u
+  while IFS=' ' read -r k v u; do
+    case "$k" in
+      MemAvailable:) MEM_AVAIL_MB=$(( v / 1024 )) ;;
+      SwapFree:)     SWAP_FREE_MB=$(( v / 1024 )); break ;;
+    esac
+  done < /proc/meminfo
+  return 0
+}
+
+# ── Subcommands ────────────────────────────────────────────────────────────
+cmd_run() {
+  mkdir -p "$LOG_DIR"
+  resolve_sensors
+  [[ -f "$CSV" ]] || printf '%s\n' "$HEADER" > "$CSV"
+  local ts tctl gpu ppt pavg nvt d0 d1 az load1 rest psic psim size
+  while :; do
+    ts=$EPOCHSECONDS
+    tctl=$(_read_scaled "$TCTL" 1000)
+    gpu=$(_read_scaled "$GPU_TEMP" 1000)
+    ppt=$(_read_scaled "$PPT_NOW" 1000000)
+    pavg=$(_read_scaled "$PPT_AVG" 1000000)
+    nvt=$(_read_scaled "$NVME_T" 1000)
+    d0=$(_read_scaled "$DIMM0" 1000)
+    d1=$(_read_scaled "$DIMM1" 1000)
+    az=$(_read_scaled "$ACPITZ" 1000)
+    IFS=' ' read -r load1 rest < /proc/loadavg 2>/dev/null || load1=""
+    _mem_fields
+    psic=$(_psi_avg10 /proc/pressure/cpu)
+    psim=$(_psi_avg10 /proc/pressure/memory)
+    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
+      "$ts" "$tctl" "$gpu" "$ppt" "$pavg" "$nvt" "$d0" "$d1" "$az" \
+      "$load1" "$MEM_AVAIL_MB" "$SWAP_FREE_MB" "$psic" "$psim" >> "$CSV"
+    # fsync the csv so the last pre-crash line survives an instant reset
+    # (uutils-compatible file-arg form; plain `sync` as fallback).
+    sync "$CSV" 2>/dev/null || sync 2>/dev/null || true
+    size=$(stat -c %s "$CSV" 2>/dev/null || echo 0)
+    if [[ "$size" =~ ^[0-9]+$ ]] && (( size > MAX_BYTES )); then
+      mv -f "$CSV" "$CSV.1"
+      printf '%s\n' "$HEADER" > "$CSV"
+    fi
+    sleep "$INTERVAL"
+  done
+}
+
+_csv_fresh() { # true iff the csv was written within the last INTERVAL+5 s
+  local mtime
+  [[ -f "$CSV" ]] || return 1
+  mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+  (( EPOCHSECONDS - mtime <= INTERVAL + 5 ))
+}
+
+cmd_start() {
+  mkdir -p "$LOG_DIR"
+  local pid=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    echo "hwmon-log: already running (pid $pid)"
+    return 0
+  fi
+  # A sampler without our pidfile (e.g. the systemd user unit running `run`)
+  # is still a sampler — never start a second writer on the same csv.
+  if _csv_fresh; then
+    echo "hwmon-log: already running (external sampler, csv fresh)"
+    return 0
+  fi
+  nohup env HOST_GUARD_ROOT="$REPO_ROOT" bash "$HERE/hwmon-log.sh" run >> "$DAEMON_LOG" 2>&1 &
+  pid=$!
+  disown "$pid" 2>/dev/null || true
+  printf '%s\n' "$pid" > "$PIDFILE"
+  echo "hwmon-log: started (pid $pid) → $CSV"
+}
+
+cmd_stop() {
+  local pid=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    kill "$pid" 2>/dev/null || true
+    rm -f "$PIDFILE"
+    echo "hwmon-log: stopped (pid $pid)"
+    return 0
+  fi
+  rm -f "$PIDFILE"
+  echo "hwmon-log: not running"
+}
+
+cmd_status() {
+  local pid="" now mtime age last=""
+  if [[ -f "$PIDFILE" ]] && IFS= read -r pid < "$PIDFILE" 2>/dev/null \
+     && [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
+    if [[ -f "$CSV" ]]; then
+      now=$EPOCHSECONDS
+      mtime=$(stat -c %Y "$CSV" 2>/dev/null || echo 0)
+      age=$(( now - mtime ))
+      if (( age <= INTERVAL + 5 )); then
+        IFS= read -r last < <(tail -n 1 "$CSV" 2>/dev/null) || last=""
+        echo "hwmon-log: running (pid $pid), csv fresh (${age}s old): $last"
+        return 0
+      fi
+      echo "hwmon-log: running (pid $pid) but csv STALE (${age}s old)"
+      return 1
+    fi
+    echo "hwmon-log: running (pid $pid) but no csv yet"
+    return 1
+  fi
+  if _csv_fresh; then
+    IFS= read -r last < <(tail -n 1 "$CSV" 2>/dev/null) || last=""
+    echo "hwmon-log: running (external sampler), csv fresh: $last"
+    return 0
+  fi
+  echo "hwmon-log: not running"
+  return 1
+}
+
+cmd_watch() {
+  [[ -f "$CSV" ]] || { echo "hwmon-log: no csv yet — start the sampler first"; return 1; }
+  local line ts tctl gpu ppt rest maxt=0 maxp=0 mark
+  trap 'echo; exit 0' INT TERM
+  echo "$HEADER"
+  while :; do
+    line=$(tail -n 1 "$CSV" 2>/dev/null || true)
+    IFS=',' read -r ts tctl gpu ppt rest <<< "$line" || true
+    if [[ "$tctl" =~ ^[0-9]+$ ]] && (( tctl > maxt )); then maxt=$tctl; fi
+    if [[ "$ppt" =~ ^[0-9]+$ ]] && (( ppt > maxp )); then maxp=$ppt; fi
+    mark=""
+    if [[ "$tctl" =~ ^[0-9]+$ ]] && (( tctl >= 90 )); then mark=" ⚠ Tctl≥90"; fi
+    printf '\r%s  [max: Tctl %s°C, PPT %sW]%s   ' "$line" "$maxt" "$maxp" "$mark"
+    sleep "$INTERVAL"
+  done
+}
+
+case "${1:-}" in
+  run)    cmd_run ;;
+  start)  cmd_start ;;
+  stop)   cmd_stop ;;
+  status) cmd_status ;;
+  watch)  cmd_watch ;;
+  *) echo "Usage: $0 {run|start|stop|status|watch}" >&2; exit 2 ;;
+esac
diff --git a/project-extensions/host-guard/host-guard.env b/project-extensions/host-guard/host-guard.env
new file mode 100644
index 0000000..35697d5
--- /dev/null
+++ b/project-extensions/host-guard/host-guard.env
@@ -0,0 +1,66 @@
+# host-guard.env — per-host resource ceilings for the AI dev chain (tapeology).
+#
+# WHY THIS EXISTS: this host (GEEKOM A7 Max mini-PC, Ryzen 9 7940HS, 27 GB RAM)
+# hard-reset FIVE times between 2026-07-20 and 2026-07-28 while goal mode ran —
+# no OOM, no thermal log, no kernel panic, machine back up within ~1 minute.
+# The 1 Hz hwmon forensics (trendora/logs/hwmon/) captured the final second of
+# the last three resets at benign temps and low package power: the trigger is a
+# millisecond-scale power/VRM transient from bursty all-core load, invisible to
+# any sampler. These caps bound how many CPUs a burst can light at once.
+# Resets #3-#5 happened while tapeology's goal mode ran UNGUARDED (this file
+# did not exist) alongside trendora's — hence the complementary masks below.
+# Incident details + runbooks: trendora/project-extensions/host-guard/README.md.
+#
+# CONTRACT: plain KEY=VALUE bash assignments only — this file is `source`d by
+# run-goal.sh, hwmon-log.sh, and host-guard-exec.sh. Only HOST_GUARD_* names.
+# Machine-specific — do not copy to other checkouts. Deleting this file (or
+# HOST_GUARD_ENABLED=0) disables every hook: the framework stays project-neutral.
+
+# Master switch for all host-guard behavior (engine wrap, preflight, gates).
+HOST_GUARD_ENABLED=1
+
+# SMT-AWARE CPU affinity mask. 7940HS sibling pairs are (0,8)(1,9)...(7,15).
+# tapeology gets physical cores 4-7 with both SMT threads — the exact
+# complement of trendora's "0-3,8-11" — so the two goal modes can run
+# concurrently and a burst can never span all 16 CPUs.
+HOST_GUARD_CPU_LIST="4-7,12-15"
+
+# BLAS/OpenMP/numexpr worker cap: one per physical core in the mask, so N
+# numpy processes cannot oversubscribe the mask with nested thread pools.
+HOST_GUARD_BLAS_THREADS=4
+
+# systemd user-scope backstops (engine wrap + pump wrapper; skipped when no
+# user bus). CPUQuota averages over ~100 ms so it CANNOT stop the sub-100 ms
+# transient — the cpuset/taskset mask above is the real limiter; this catches
+# sustained overshoot.
+HOST_GUARD_CPUQUOTA="800%"
+# Aggregate memory ceiling (reclaim+throttle, never OOM-kill): 14G each for
+# tapeology + trendora fits inside 27.3G with room for desktop/Chrome.
+HOST_GUARD_MEMORY_HIGH="14G"
+# Fork-storm bound; the whole box normally runs ~1500-1700 tasks in goal mode.
+HOST_GUARD_TASKS_MAX=2048
+
+# hwmon sampler (crash forensics): 1 Hz, fsync per line, 10 MB ring ≈ 1 day per
+# file (hwmon.csv + hwmon.csv.1 ≈ 2 days of history) → tapeology/logs/hwmon/.
+# Implementation: scripts/automation/host-guard/hwmon-log.sh (framework).
+HOST_GUARD_SAMPLER_INTERVAL=1
+HOST_GUARD_SAMPLER_MAX_BYTES=10485760
+
+# Launcher cap-block markers: tapeology's launchers carry no HOST-GUARD blocks
+# yet — confinement comes from the engine self-wrap + the pump wrapper cgroup,
+# which every launcher child inherits. Flip to 1 (and list files in
+# HOST_GUARD_MARKER_FILES) only if tapeology ever grows its own capped launchers.
+HOST_GUARD_REQUIRE_MARKERS=0
+
+# Require the interactive pump (the foreground Claude/Codex session) to be
+# cpuset-confined — the engine self-wrap cannot cover agents dispatched inside
+# the foreground CLI (the gap behind resets #3-#5). The iteration gate verifies
+# the pump's Cpus_allowed_list against the mask and pauses (AWAITING_HOST_GUARD,
+# resumable) when unconfined. Launch the CLI through the wrapper:
+#   scripts/automation/host-guard-exec.sh claude
+HOST_GUARD_REQUIRE_PUMP_CONFINED=1
+
+# Thermal iteration gate (framework defaults shown; uncomment to tune).
+#HOST_GUARD_TCTL_PAUSE=90
+#HOST_GUARD_TCTL_RESUME=80
+#HOST_GUARD_TCTL_MAX_WAIT=1800
```
