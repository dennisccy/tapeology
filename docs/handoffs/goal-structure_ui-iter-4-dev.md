# goal-structure_ui-iter-4 Dev Handoff

**Phase:** goal-structure_ui-iter-4
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

**No code was written or changed.** This iteration is an evidence-capture / hardening pass, not a
feature iteration — J-01–J-04 were all already implemented in iter-1/iter-2/iter-3. Per the phase
spec and execution plan, the developer's job this iteration is the operational precondition that
iter-3 skipped: bring both services up, confirm they respond, and confirm the regression baseline —
so the browser-qa-agent step that runs next in the pipeline has a live, verified-working app to
photograph, rather than repeating iter-3's "frontend not running" SKIP 0/26.

Concretely, this session performed and verified:

1. **Zero-diff confirmation (frozen foundation).** `git diff --stat -- apps/backend` and
   `git diff --stat -- apps/frontend` both returned empty before and after this session's work — no
   backend or frontend file was touched. `git status --short` shows only goal-mode bookkeeping files
   (this phase spec, the test-plan, dispatch markers, `runs/goal-structure_ui-iter-4/`) — nothing
   under `apps/`.
2. **`config_fingerprint` recomputed live** via
   `.venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"` →
   `4d665603569b9dbf`, matching the pinned J-04 value exactly.
3. **Fresh service startup, verified twice (cold start + kill-and-restart), per the dev agent's
   standing Pre-handoff verification duty and this phase's explicit precondition:**
   - Ports independently recomputed from the sha1-offset formula in `scripts/dev.sh`
     (`sha1(repo_root) & 0xffff mod 1000` → offset `301`) → backend `:8301`, frontend `:3301`.
     Confirmed nothing was listening on either port before starting (`ss -tln`, `ps aux`).
   - **Cold start:** ran `bash scripts/dev.sh` in the background. Log showed a clean boot with no
     errors: `Uvicorn running on http://0.0.0.0:8301` / `Application startup complete.`, then
     `Next.js 15.5.19 ... ✓ Ready in 1155ms`. Polled both URLs; both returned HTTP 200 within ~1s of
     the poll loop starting (dev.sh itself had already had a couple of seconds' head start by the
     time polling began).
   - **Kill-and-restart:** ran `bash scripts/dev.sh` a **second** time while the first instance was
     still up, to exercise the script's own stale-process cleanup (not just a manual kill). Log
     confirms it correctly found and killed **three** PIDs on port 8301 (the uvicorn parent, its
     `--reload` watcher child, and the actual server process — not just the top-level PID), then
     started fresh backend/frontend processes that became healthy in `Ready in 1293ms`. Post-restart
     `ps aux` showed exactly one uvicorn process and one next-dev process tree — no orphaned
     duplicates, no port conflict.
   - Verified real content, not just bare 200s: `GET /health` → `{"status":"ok"}`;
     `GET /` → `<title>Tapeology</title>`; `GET /structure` → HTTP 200 with the Comparison section's
     testids present in the server-rendered shell (`comparison-champion`,
     `comparison-founding-baseline`, `comparison-datasets-loading`, etc.); `GET /meta/ui-routes` →
     the 5-route array including `{"path":"/structure","label":"Structure","nav":true}`, confirming
     the nav-registry entry J-01 depends on is live and correct.
   - **Cleanup:** killed both processes by port (`lsof -ti :3301`/`:8301` → `kill -9`, matching
     `scripts/dev.sh`'s own kill logic) and confirmed via `ss -tln` and `ps aux` that nothing remains
     listening and no `uvicorn`/`next dev`/`next-server` process survives. Per this iteration's
     architecture, this is safe: `browser-qa-phase.sh` (the next pipeline step) is self-bootstrapping
     — it calls `ensure_services_running` itself with its own 90-second cold-start retry budget and
     stale-server/corrupt-`.next` healing (confirmed by reading `scripts/automation/browser-qa-phase.sh`
     and `scripts/automation/dev-phase.sh`, which each install their own service-lifecycle EXIT trap
     independent of this step) — so there is no "hand off a still-running server" contract between
     the developer step and the browser-qa step; each step starts its own instance fresh, and this
     session confirmed that fresh-start path works cleanly and fast (~1.1–1.3s to ready) against this
     exact code.
4. **Backend regression suite run in full** (see Tests Run below) — green, matching the iter-2/iter-3
   baseline exactly.

## Root-cause read on iter-3's SKIP (for the record, not a fix)

iter-3's own audit/ux-regression/closure reports (`docs/handoffs/goal-structure_ui-iter-3-audit.md`,
`reports/phase-goal-structure_ui-iter-3-ux-regression.md`,
`reports/phase-goal-structure_ui-iter-3-closure-verdict.md`) all independently concluded the SKIP was
"environmental/timing, not a code defect" — the services were reachable through dev+review+QA
(08:33–08:35) and had gone unreachable by the time `browser-qa-agent` (08:48) and `demo-narrator` ran.
This session's own fresh cold-start test (above) found no code-level or environment-level obstruction:
`scripts/dev.sh` brings up a fully healthy app in ~1.1–1.3 seconds, well inside
`browser-qa-phase.sh`'s 90-second retry budget, with clean logs and no port/lock contention. I cannot
identify the exact prior trigger (this session did not have access to iter-3's live process history),
but there is no evidence of a persistent blocker — the documented start path is fast and reliable
against the current code and environment.

## Files Changed

None. `apps/backend/` and `apps/frontend/` diffs are both byte-empty (verified via
`git diff --stat` before and after this session). No `docs/handoffs/goal-structure_ui-iter-4-frontend.md`
is written this iteration — no frontend UI code changed, so a separate frontend handoff would only
restate this same file's operational content under a different name (the execution plan's own "Files
to Create/Modify" list does not call for one either).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<tmp>/junit-iter4.xml`
Result: **1146 passed, 1 skipped, 0 failed, 0 errors** (1147 collected total; junit-xml counts:
`{'errors': '0', 'failures': '0', 'skipped': '1', 'tests': '1147'}`) — identical to the iter-2/iter-3
baseline, as expected since this is a zero-diff iteration for `apps/backend`.

No frontend-specific test command exists in this project's config (matches iter-3's own QA report:
"Not applicable — no frontend-specific test command"). The frontend copy-discipline lint that matters
here (`tests/test_copy_discipline.py::test_lint_frontend_source_literals_are_clean`) is part of the
backend suite above and passed — no vocabulary-drift regression.

## Known Issues

- **The actual DoD-required deliverable of this iteration — independent, populated-state
  browser-qa-agent screenshots of the J-03 Comparison section — is NOT produced by this dev step.**
  Per the plan's own "Agents Required" section and the iter-0/iter-1(b) lessons the phase spec cites
  verbatim, a developer's own self-verification (even a live one, like the curl/log checks above)
  must never be accepted as the populated-state evidence — only an independent `browser-qa-agent` run
  qualifies. This handoff's job was solely to prove the precondition (services start cleanly and
  respond correctly) so that the next pipeline step can succeed; it deliberately does NOT drive
  Chrome MCP against the populated Comparison flow itself, to avoid muddying the evidence trail with
  a second "developer self-run" the way iter-3's audit had to caveat.
- No code change was made or needed — nothing in `apps/backend/` or `apps/frontend/` required a fix.
  If browser-qa-agent's upcoming independent run does surface a genuine render defect, the phase
  spec's own conditional path (a single-file, targeted fix, re-run coherence + audit) applies to a
  *future* developer invocation, not this one.
- Both services were stopped at the end of this session per the standing "kill any server you start
  before finishing" rule; the next pipeline step (`browser-qa-phase.sh`) owns starting its own fresh
  instance via `ensure_services_running`, as detailed above.
