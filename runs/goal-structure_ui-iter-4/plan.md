# goal-structure_ui-iter-4 Execution Plan

Scope check against `docs/goal.md`: **aligned, no drift, no scope creep.** This iteration builds
**nothing new** — J-01–J-04 are all already implemented (iter-1: J-01; iter-2: J-02; iter-3: J-03 +
J-04 sentinel). Per `runs/goal-session-structure_ui/state/journey-history.json` right now: J-01
`passing` (iter-2), J-02 `passing` (iter-3), J-04 `already_passing` (iter-3), and **J-03 `unknown`**
(`last_passing_iter: null`) — not because J-03 is broken, but because iter-3's browser-qa-agent and
demo-narrator ran while both services were down and recorded **SKIPPED 0/26**, so no populated
screenshot of the Comparison section exists anywhere. That SKIP is also why iter-3 closed with a
standing **CLOSURE-FAIL** (phase-closure-auditor), **UX-REGRESSION-WARN** (ux-regression-reviewer),
and **PASS_WITH_GAPS** (auditor finding T1) — all three explicitly contingent on "an independent
browser-qa re-run" before certification. This iteration exists solely to supply that re-run. The
phase spec's own OUT OF SCOPE list is already tight and consistent with `docs/goal.md`'s Anti-goals
(no backend computation, no champion promotion, no new journey); the one explicit deferral —
`PriceChart.tsx`'s carry-forward z-index issue (F2, Cockpit/J-04) — is correctly out of scope here
since this iteration touches neither the Cockpit nor `PriceChart.tsx`.

## What to Build

Nothing new is implemented. The work is an **evidence-capture / hardening pass**:

- **Mandatory precondition, before any QA/browser-qa/demo dispatch:** start both services
  (`bash scripts/dev.sh`) and curl-confirm `http://localhost:3301` (frontend) **and**
  `http://localhost:8301/health` (backend) both return HTTP 200. (Ports independently re-derived
  from `scripts/dev.sh`'s deterministic sha1-of-repo-root offset: offset `301` → backend `8301` /
  frontend `3301` — confirmed both by direct computation and by iter-3's own dev handoff; both ports
  are currently unreachable, confirming services need a fresh start.) This is the exact precondition
  iter-3 skipped — do not dispatch browser-qa-agent or demo-narrator until both checks pass; if
  either is down, start it and re-confirm before proceeding.
- Dispatch **browser-qa-agent** against the live app to independently execute the P1 cases from
  `reports/phase-goal-structure_ui-iter-3-ui-test-plan.md` (or a refreshed equivalent) — at minimum
  the J-03 Comparison happy-path cases plus the J-01/J-02/J-04 regression cases (iter-3's
  UT-18–UT-23 range) — capturing populated-state screenshots into the **new**
  `reports/qa/goal-structure_ui-iter-4-evidence/` directory (iter-3's own evidence directory holds
  only 3 idle-state PNGs and must not be reused/relied on as this iteration's evidence).
- **Conditional, narrowly-scoped fix path (not expected):** only if browser-qa-agent surfaces a
  genuine render defect (e.g., a residual `lightweight-charts` z-index/empty-state occlusion, per
  the iter-1(a) lesson already fixed once on `StructureChart.tsx`) may a **single-file** frontend
  fix be applied — then coherence-auditor and the auditor re-run. Absent such a finding, both the
  frontend and backend diffs stay byte-empty.
- Re-run **phase-closure-auditor**, **ux-regression-reviewer**, and **demo-narrator** against the
  refreshed, populated `ui-test-results.md` to flip iter-3's standing CLOSURE-FAIL →
  **CLOSURE-PASS** and UX-REGRESSION-WARN → **UX-REGRESSION-PASS**.
- Confirm the regression sentinel (J-04) holds: `git diff --stat -- apps/backend` stays empty;
  `config_fingerprint` recomputes live to `4d665603569b9dbf`; backend suite stays at ~1146 passed / 1
  skipped; frontend copy-discipline lint stays green; 5-link nav and `/performance` remain intact.
- Write the dev handoff at `docs/handoffs/goal-structure_ui-iter-4-dev.md` documenting the
  services-up confirmation, the new populated evidence, and (if it fired) the one conditional fix.
- If all four journeys read `passing`/`already_passing` after this iteration, it is a
  **GOAL_ACHIEVED candidate** for the goal-evaluator.

## Agents Required

- backend-data: no -- frozen foundation; zero backend computation, endpoint, or file change is
  permitted this iteration (`docs/goal.md`'s Foundation invariants + the phase spec's explicit "No
  backend code change" scope item). The only backend-adjacent action is *confirming* (never
  changing) that the diff stays empty and `config_fingerprint` recomputes to `4d665603569b9dbf`.
- frontend-ux: no -- J-03 was already fully implemented, reviewed, and self-verified live in iter-3
  (`docs/handoffs/goal-structure_ui-iter-3-dev.md`); no new frontend capability, component, or route
  is in scope this iteration. If (and only if) the independent browser-qa-agent run this iteration
  surfaces a genuine defect, the retry path should dispatch a fix scoped to **exactly one existing
  file**, mirroring iter-1's one-line `StructureChart.tsx` precedent — never a new feature, never a
  second component, never a backend touch. Whatever agent performs the services-up + curl-confirm
  operational step and writes the dev handoff should treat this iteration's "implementation" as that
  operational sequence plus the conditional fix contingency, not new capability work.

Frontend Present: yes

## Files to Create/Modify

- `docs/handoffs/goal-structure_ui-iter-4-dev.md` -- dev handoff (DoD requirement): the services-up
  + curl-200 confirmation, confirmation that `apps/backend`/`apps/frontend` diffs are empty (or, if
  the contingency fired, naming the single fixed file and why), and a pointer to the new evidence
  directory.
- `reports/qa/goal-structure_ui-iter-4-evidence/*.png` -- **new** populated-state screenshots
  (browser-qa-agent output) for J-01, J-02, J-03 (primary target), and J-04.
- `reports/phase-goal-structure_ui-iter-4-ui-test-results.md` -- refreshed results replacing
  iter-3's SKIPPED-0/26 record with real per-case PASS/FAIL and evidence links.
- Expected refreshed showcase artifacts: `reports/phase-goal-structure_ui-iter-4-closure-verdict.md`,
  `-ux-regression.md`, `-demo-results.md`/`-demo-script.md`/`-demo.json`, `-iteration-summary.md`.
- Conditionally, if and only if browser-qa-agent finds a genuine defect: exactly one existing
  frontend file (most likely `apps/frontend/app/structure/page.tsx` or
  `apps/frontend/components/StructureChart.tsx`) -- a minimal, targeted fix. No new file.
- No `apps/backend/` file of any kind.

## UI Evolution

*(Required because Frontend Present: yes — but nothing below is NEW this iteration; it restates the
already-shipped J-03 capability that this iteration exists only to independently, browser-verify.)*

- New user-facing capability: none. The capability being independently re-confirmed: choose a
  registered dataset, run `v1` and `structure_tape` as an offline research job, and see both
  strategies' aggregates plus the per-class A/B/C breakdown side by side.
- New information displayed: none. Every field (aggregates, `aggregates_by_class`,
  `insufficient_sample`, `register`, champion, founding baseline) was already wired to its canonical
  endpoint in iter-3.
- New user actions: none. The dataset selector and "Run comparison" button already exist.
- UI surface changes: none. Same 3-section `/structure` page (Levels & Zones / Registry /
  Comparison). No new route, no nav change.
- Navigation changes: none.

## Visual Requirements

*(Required because Frontend Present: yes — restated for the conditional fix path only; no new
visual work is planned.)*

- Component patterns: if the conditional fix fires, reuse the file's existing `Panel`/
  `LoadingPanel`/`UnavailablePanel`/`EmptyState` locals and `NUMERIC_CELL`/`HEADER_CELL`/
  `LABEL_CELL` constants exactly as iter-1/2/3 did — never redefine or fork them.
- Layout: unchanged — single column, `max-w-7xl` container, three stacked sections (Levels & Zones,
  Registry, Comparison).
- Key visual effects: unchanged — dark instrument-panel style, amber for honest-empty/degraded/
  insufficient states, font-mono numerics. If the conditional fix targets a z-index occlusion
  (iter-1(a) precedent), the overlay's z-index must sit above the `lightweight-charts` canvases,
  mirroring `StructureChart.tsx`'s existing `z-10` fix — do not invent a new stacking approach.
- States to handle: this iteration's job is to *prove* (via browser-qa screenshot) the states
  iter-3 already built render correctly under live, populated conditions — idle, no-datasets,
  queued/running, failed, cancelled, done-with-insufficient-n, backend-unreachable-at-each-step. No
  new state is being added.

## Key Test Scenarios

- **Precondition gate (hard-block — this is exactly why iter-3 burned):** `curl -sf
  http://localhost:3301` and `curl -sf http://localhost:8301/health` both return 200 BEFORE
  browser-qa-agent or demo-narrator is dispatched. If either is down, run `bash scripts/dev.sh` and
  re-confirm. Never accept a developer self-run or an idle-state screenshot as substitute evidence
  (iter-0 / iter-3 lessons) — only an independent browser-qa-agent populated screenshot flips J-03.
- **J-03 populated (primary target):** dataset chosen → both backtests reach `done` → side-by-side
  aggregates (`n`, net R, net $, `win_rate`, `max_drawdown_r`) byte-match a live
  `GET /research/backtests/{id}` call for both `v1` and `structure_tape` → per-class A/B/C table
  shows `insufficient_sample` chips verbatim → `register` string byte-matches the payload → champion
  badge still `v1`/`default` → keyless `structure_tape` shows the honest non-survivor outcome
  (`n=0` → "no trades (n=0)", never a fabricated `0`).
- **J-01 re-verify:** populated chart with S/R level lines + A/B/C confluence zone table render
  correctly; the `StructureChart` empty-hint overlay is NOT occluded (z-index above the
  lightweight-charts canvases — iter-1(a) regression watch).
- **J-02 re-verify:** `v1` + `structure_tape` registry cards with class-scaled stop/reward/size
  maps; champion `v1`/`default` badged; testids distinct from the Comparison section's own champion
  badge (no same-page collision — iter-2 audit finding T2 watch).
- **J-04 regression sentinel:** `git diff --stat -- apps/backend` empty; full backend suite green
  (~1146 passed / 1 skipped); `config_fingerprint` recomputes live to `4d665603569b9dbf`; 5-link nav
  (`Cockpit/Journal/Studies/Performance/Structure`) intact; `/performance` unaffected; sim cockpit
  flows (`SIM-BUYER`/`SIM-SELLER`) still settle correctly.
- **Honesty / anti-goal scan:** no `set_champion_pointer` call anywhere; PnL ledger unwritten; no
  vocabulary drift ("paper trading", "annualized", "expected profit", imperative cues); the
  "simulated — not indicative of live results" register appears verbatim wherever simulated PnL/size
  is shown.
- **Bonus, non-blocking (if practical while services are up):** capture at least one still-unexercised
  honest degraded state named by iter-3's audit finding F1 — `failed`, `cancelled`,
  `comparison-poll-error`, or `comparison-no-datasets`.
- **Closure gate:** phase-closure-auditor returns CLOSURE-PASS (clearing iter-3's CLOSURE-FAIL);
  ux-regression-reviewer returns UX-REGRESSION-PASS (clearing iter-3's WARN); audit returns PASS or
  PASS_WITH_GAPS. If J-01/J-02/J-03/J-04 all read `passing`/`already_passing`, flag this as a
  GOAL_ACHIEVED candidate for the evaluator.

## Out of Scope (confirmed — no drift from `docs/goal.md` or the phase spec)

- Any backend edit of any kind, beyond the already-shipped additive `meta.py` `/structure` entry.
- Any champion promotion, `set_champion_pointer` call, or PnL-ledger write from the UI.
- Building a `/datasets` library-inventory page (Card 5.9 scope).
- Fixing `PriceChart.tsx`'s carry-forward z-index issue (F2, Cockpit/J-04) — pre-existing,
  non-blocking, correctly deferred to a future Cockpit-touching iteration per the phase spec.
- Any new journey or scope beyond re-verifying J-01–J-04.
