# goal-desk-iter-13 Execution Plan

Era B "The Desk", iteration 13 — **zero product/application code change.** This is a pure
evidence/showcase re-attempt closing the ONE clause `docs/goal.md`'s own J-09 acceptance text still
requires: a `[NEW]`-flagged demo-narrator walkthrough that shows, in ONE artifact and in sequence,
the honest "No top-up runs recorded yet." state and a populated Top-up Runs state. J-09's actual
implementation (`desk_topup_log.py`, `GET /research/desk/topup/runs`, the `/desk` panel) shipped in
iteration 11 and is untouched here. Required-still-passing: J-01–J-08 (smoke-replay only, per
`iteration-state.md`'s "Do not redo").

Depth is **full** (already locked in — `runs/goal-session-desk/iter-13/depth-dispatched` = `full`),
mandatory per iteration 12's `ESCALATE` verdict, with no discretion. This is not incidental: at
`full` depth the demo-narrator lane runs BEFORE the goal-evaluator, so the walkthrough this
iteration produces can actually be scored this same iteration — at `lean` depth it cannot (see
"Why two prior attempts failed" below).

## Why two prior attempts failed (context for every downstream lane)

1. **Iteration 11** (full depth) narrated only the honest-empty panel because the store it recorded
   against had zero top-up runs — a feature whose whole point is accumulating state cannot be
   demonstrated on a store deliberately kept empty. Verdict: `CONTINUE`.
2. **Iteration 12** (lean depth) correctly rebuilt a populated rig and captured two genuine
   standalone screenshots, but produced **no** demo-narrator artifact at all — lean depth runs that
   lane AFTER the evaluator, so a lean iteration whose only gap is a showcase artifact can never
   close in the same pass it is produced. It also recorded all three checkpoint runs BEFORE booting
   the frontend, closing the honest "nothing saved yet" window before any browser existed — forcing
   a second, disconnected rig just to photograph the empty half. Verdict: `ESCALATE` (this session's
   first).

This iteration fixes both causes together: full depth (ordering) + a corrected single-rig capture
order (seed → boot BOTH processes → capture empty → record 3 runs → capture populated, all on ONE
still-live rig, never restarted or swapped).

## What to Build

Nothing in source. The work is ops/evidence capture, in this exact order:

1. **Environment hygiene first.** Inventory and stop whatever is currently bound to `:8301`/`:3301`
   (and `:8302`/`:3302` if occupied) — confirmed clear via `ss`/`pgrep` at plan-writing time (nothing
   listening, no uvicorn/next process found), but the developer must verify independently at
   execution time regardless (state may have changed again). For anything found and stopped, confirm
   via `taskset -pc <pid>` that it never ran outside the host-guard CPU mask `4-7,12-15` before
   killing it, and record the finding.
2. Seed **ONE fresh scoped root**, distinctly named from every prior iteration's
   (`desk-iter9-scoped-qa`, `desk-iter10-scoped-qa`, `desk-iter11-scoped-qa`,
   `desk-iter12-scoped-qa` / `desk-iter12-scoped-qa-empty`) — e.g. `desk-iter13-scoped-qa` — via the
   existing `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh <root_dir> 8301` (a `cp -a` of
   the current ambient `apps/backend/.data/` tree). Never target the ambient store.
3. Before recording anything, check the fresh root for a pre-existing top-up-run record under a
   colliding key (a fresh `cp -a` makes this unlikely — iter-12 found none — but disclose the check's
   result either way).
4. `rm -rf apps/frontend/.next` (T-9), then boot **BOTH** the scoped backend (`:8301`) AND the scoped
   frontend (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`)
   against the fresh root — **before recording a single run.** This ordering is the load-bearing fix.
5. **With the rig live and still empty**, capture the honest "No top-up runs recorded yet." state as
   this iteration's FIRST capture — confirm live via `GET /research/desk/topup/runs` returning
   `{"runs": [], "latest": null}` at the same moment.
6. **Only after** that first capture is on disk, record three checkpoint top-up runs into the SAME
   rig via `DeskTopupComputeManager.trigger()` in-process (the recipe iteration 11's browser-QA lane
   and iteration 12's dev lane both already proved): one ordinary run (monkeypatched
   `_run_one_pair` always `"fetched"`, `state: done`, `pairs_attempted == pairs_total`), one run
   cancelled mid-walk (`state: cancelled`, `pairs_attempted < pairs_total`), one run with at least one
   induced `failed` pair via an `_NthCallFailsAdapter`-style double (real `_run_one_pair` restored,
   `get_market_adapter` overridden) whose vendor detail is preserved verbatim. Never a live vendor
   call.
7. **With the rig now populated** (same root, same still-live frontend — never restarted or swapped),
   capture the populated Top-up Runs section as the SECOND capture: attempted-of-total count,
   per-outcome (reused/fetched/failed) counts, and the failed pair's own recorded detail, all legible
   in one image.
8. **Assemble ONE `[NEW]`-flagged demo-narrator walkthrough** for J-09 containing both captures in
   sequence (empty first, populated second). Build-time choice among three equally acceptable paths:
   extend `reports/phase-goal-desk-iter-11-demo.json`'s existing J-09 step (`n:2`, currently narrates
   only the empty state — see its `expect.text: "No top-up runs recorded yet."`) with a paired
   populated-state step immediately after it; add that pair fresh; or author a new
   `reports/phase-goal-desk-iter-13-demo.json` reusing the same highlight steps against this
   iteration's rig. Narration must match what each paired screenshot actually shows — no claim
   unsupported by the image next to it.
9. Name the scoped rig's absolute path explicitly in the demo/showcase dispatch itself (not only
   dev/QA) and in every results report produced this iteration.
10. Replay the regression set (`journey-scripts/J-01.json`–`J-05.json`, `J-07.json`, `J-08.json`)
    against the SAME scoped backend; any step reaching a compute/fetch/Run control stays scoped,
    never ambient. J-06 is re-confirmed via `test_mcp_server.py`'s existing 17-tool contract — no
    browser surface, no golden needed. Record results in a new
    `reports/phase-goal-desk-iter-13-smoke-replay-results.md`.
11. Checksum the ambient `apps/backend/.data/` tree (full file listing + per-file SHA-256) BEFORE any
    of the above begins, and again AFTER everything completes; diff and prove zero write landed
    there.
12. Full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -v` — `-v` required to
    reliably see the summary line in this environment) at/above the 1369-passed/8-skipped/0-failed
    floor; `Config().config_fingerprint()` still `08e471b10130e1e2`.
13. Write the dev handoff at `docs/handoffs/goal-desk-iter-13-dev.md` stating the scoped-root
    absolute path, the port-hygiene finding, the collision-check result, and confirming (via
    `git diff --stat`) zero diff on every named out-of-scope file.

If `journey-scripts/J-09.json` (already edited once, 2026-07-28) or any other golden is touched again
by any lane, that lane's own results report must disclose it explicitly (iter-8 lesson) — not
required by default.

## Agents Required

- developer: yes — ops/evidence-capture dispatch only (steps 1–7, 10–13 above); zero product source
  diff is expected AND required, not merely the default.
- backend-data: yes — scoped backend seed/boot, in-process checkpoint recording via the real
  `DeskTopupComputeManager` code path, ambient-store checksumming, full pytest suite + fingerprint
  check, MCP contract re-confirmation. Ops/verification only — no backend source edits.
- frontend-ux: yes — clean `.next` rebuild + boot the scoped frontend, confirm `/desk` renders both
  the empty and populated Top-up Runs states correctly for capture, regression replay against the
  scoped frontend. Ops/verification only — no frontend source edits.

Downstream pipeline note (not controlled by this plan, full-depth-standard): browser-qa-agent's
standalone J-09 screenshots are **already done and evaluator-opened**
(`reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png`,
`UT-J-09-populated-topup-section.png`) — binding "do not redo"; the demo-narrator lane owns
assembling the `[NEW]`-flagged walkthrough JSON from the developer's two same-rig captures.

## Frontend Present

Frontend Present: yes

(Not because any UI changed — it did not — but because the Definition of Done requires a live
scoped-browser session for the walkthrough captures and the regression replay; QA must run its
Chrome MCP / Playwright browser checks this iteration.)

## Files to Create/Modify

- `docs/handoffs/goal-desk-iter-13-dev.md` — required dev handoff (new).
- `reports/phase-goal-desk-iter-11-demo.json` (edit in place to add the populated-state J-09 step)
  **or** `reports/phase-goal-desk-iter-13-demo.json` (new) — the `[NEW]`-flagged walkthrough
  artifact; build-time choice, disclose which was taken.
- `reports/phase-goal-desk-iter-13-smoke-replay-results.md` — regression replay report (new),
  naming this iteration's scoped-root path.
- `reports/qa/goal-desk-iter-13-evidence/*.png` — capture screenshots for the walkthrough +
  regression replay (new).
- Optionally `runs/goal-session-desk/journey-scripts/J-09.json` — ONLY if an executor chooses to
  refresh it; MUST be disclosed explicitly if touched (iter-8 lesson); not required.

**NO changes to any of** (zero diff is a hard requirement, TC-10 — not merely the default):
`desk_topup_log.py`, `desk_topup_compute.py`, `desk_routes.py`, `desk_screen.py`,
`desk_coverage.py`, `tradability.py`, `levels.py`, `bars.py`,
`apps/frontend/app/desk/page.tsx`, `lib/types.ts`, `lib/api.ts`, `StructureChart.tsx`,
`PriceChart.tsx`, `config.py`, `meta.py`, `app/mcp/__init__.py`.

## Execution-order traps (the whole point of this iteration — read before starting)

1. **Boot BOTH scoped processes before recording any checkpoint run.** Recording first (iteration
   12's mistake) permanently closes the honest-empty window on that rig — the append-only rail
   forbids reopening it by deleting real records, so getting this backwards forces a second,
   disconnected rig and makes a single coherent walkthrough impossible again.
2. **Capture the empty-state screenshot before step 6's recording, on the live rig**, not from a
   separate/second rig and not deferred until after runs exist.
3. **Never restart or swap the rig between the two captures.** Same root, same backend process, same
   frontend process, throughout — TC-2/TC-3 explicitly require "the same rig, not a second one."
4. **Do not click "Top-up" or "Run Screen" on this scoped instance** once checkpoint 3 is recorded —
   the walkthrough depends on checkpoint 3 (the induced-failure run) being the *latest* record; a
   real click would start an uncontrolled 4th run against the real keyless Yahoo adapter and bury the
   evidence. Read-only after step 7.
5. **Depth is full and already locked** (`depth-dispatched` = `full`) — nothing in this plan should
   attempt to downgrade it; the mandatory-full trigger (prior `ESCALATE`) is not discretionary.

## UI Evolution

- New user-facing capability: **None** — the Top-up Runs section, store, and endpoint already
  shipped in iteration 11 and are already visible in production.
- New information displayed: None.
- New user actions: None.
- UI surface changes: None.
- Navigation changes: None.

This iteration only captures the narrated-walkthrough evidence `docs/goal.md`'s acceptance text
still requires; the operator sees nothing new.

## Visual Requirements

Not applicable — no new component, layout, or visual-effect work. The developer/demo-narrator/
browser-qa lanes read the EXISTING `/desk` Top-up Runs section (built iteration 11) exactly as
shipped; only its two already-implemented states (honest-empty, populated) are captured, in the
corrected order, on one live rig. States to handle are the two that already exist — no new state
to design.

## Key Test Scenarios

Full test-first contract is TC-1..TC-11 in `docs/phases/goal-desk-iter-13.md` — condensed:

- TC-1: fresh scoped root, both processes booted, zero runs recorded → `GET
  /research/desk/topup/runs` returns `{"runs": [], "latest": null}` AND a live-browser screenshot
  legibly shows "No top-up runs recorded yet." — captured with the frontend already live, never
  before it existed.
- TC-2: same still-live rig, 3 checkpoint runs recorded in order (ordinary, cancelled, one-failed
  pair) → GET returns 3 runs, `latest.outcomes` includes a `"failed"` entry with non-null verbatim
  `detail`; the same rig — not a second one — still serves the frontend.
- TC-3: same rig reloaded → one screenshot legibly shows attempted-of-total, per-outcome counts, and
  the failed pair's detail together, in the same image.
- TC-4: the `[NEW]`-flagged walkthrough contains both captures in sequence (empty, then populated),
  both from the SAME scoped root, each step legible, narration matching each paired screenshot.
- TC-5: the demo/showcase report AND any browser-QA/evidence report each state the absolute scoped
  data-root path.
- TC-6: ambient `.data/` listing + SHA-256 checksums identical before vs. after (zero new/modified/
  deleted file, including no new `topup_runs`-equivalent directory anywhere in the ambient tree).
- TC-7: J-01–J-05, J-07, J-08 golden replays all PASS, 0 failed steps, against the scoped backend.
- TC-8: `test_mcp_server.py`'s `EXPECTED_TOOLS` still exactly 17 entries.
- TC-9: full suite ≥1369 passed / 8 skipped / 0 failed; a separate fingerprint check prints
  `08e471b10130e1e2`.
- TC-10: cumulative repo diff touches only documentation/evidence/showcase artifacts — zero diff on
  every named product file above.
- TC-11: any prior leftover scoped process bound to a port this iteration reuses is confirmed
  stopped BEFORE this iteration's own rig is seeded/booted, stated in the dev handoff.

## Out of Scope (carried from the phase spec — do not build)

- Any edit to the 16 named product/application files (backend or frontend) — implementation is DONE;
  zero diff is the expectation, not merely the default.
- Any new `Config` field, route, page, MCP tool, or nav-skeleton change.
- Triggering a top-up, screen, or fetch against the ambient `apps/backend/.data/` store.
- A real ~100-symbol operator top-up run (stays a separate, explicit, honestly-reported future act).
- Backfilling, rewriting, or recomputing any already-recorded universe/screen/top-up-run record,
  including on this iteration's own fresh rig (a mistaken loss is fixed by re-seeding a NEW root,
  never by deleting a recorded run).
- Reusing or continuing any prior iteration's scoped root (`desk-iter9/10/11/12(-empty)-scoped-qa`).
- Re-capturing standalone browser-qa-agent J-09 screenshots — already done and evaluator-opened
  (iteration 12); binding "do not redo."
- Re-verifying J-01–J-08's deep acceptance clauses beyond the smoke-set deterministic replay.
- The backlogged `bar-index-store-reconcile` proposal.
- The carried, non-blocking hardening items: run-list `integrity_errors` gap (`desk_routes.py:258`),
  the narrow auto-refresh race (`app/desk/page.tsx:1116-1121`), missing run-table cap, the
  six-stacked-sections page length, same-date-screen ambiguity, keyboard access for history rows —
  all unrelated to this journey.
- Widening, disabling, or bypassing the host-guard CPU caps (`4-7,12-15`) for any process this
  iteration starts, even to make setup/cleanup faster — that anti-goal is `critical`.

## Project alignment check

No drift from `docs/goal.md`. This iteration closes the LAST unmet clause of the goal's own J-09
acceptance text (a `[NEW]`-flagged demo-narrator walkthrough covering the top-up-run disclosure end
to end) with zero new product surface — directly advancing Success Criteria #4 ("the briefing is a
real product surface... all browser-verified with screenshots") without touching frozen foundations,
the fingerprint pin, or any anti-goal rail. It builds on, and does not duplicate, existing
architecture: reuses the existing `goal-desk-iter9-scoped-backend.sh` scoped-rig script, the existing
`DeskTopupComputeManager` production code path (never a synthetic write path), and the existing
demo-narrator/browser-qa-agent pipeline lanes. Two consecutive prior attempts (iteration 11
`CONTINUE`, iteration 12 `ESCALATE`) failed for two now-diagnosed, non-code reasons — lane ordering
(lean depth runs demo-narrator after the evaluator) and capture ordering (recording runs before the
frontend ever booted) — both of which this plan's ordering directly fixes. If every clause above
holds, this returns the era to 9/9 journeys `passing`; per the spec's own NOTES, whether that means
`GOAL_ACHIEVED` is the evaluator's call, not presumed here.
