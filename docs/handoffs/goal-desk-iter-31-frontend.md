# goal-desk-iter-31 Frontend Handoff

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

A single honesty fix to `/desk`'s already-shipped "Screen Runs" section, plus a revert of two
tracked TypeScript build-plumbing files. No new page, section, control, or `data-testid`.

- **`LatestScreenRunDetail` (`apps/frontend/app/desk/page.tsx`) — suppress misleading fields on a
  reused run.** When the latest recorded screen run is `state === "done" && reused === true`, the
  component now suppresses:
  - the amber `data-testid="desk-screen-run-latest-unreached"` note ("N members not reached"),
  - the `data-testid="desk-screen-run-latest-counts"` line ("N ranked · N skipped (no bars) · N
    skipped (no basis)").

  Both previously rendered unconditionally, so a reused run (which never walked any member — by
  design, `members_attempted: 0`) showed what read as a failure/incompleteness signal right next
  to its own honest `screenRunOutcomeText` ("reused `<id>` — no walk was performed"). The fix is
  two added boolean guards, nothing else in the component changed: `unreached > 0 &&
  !(run.state === "done" && run.reused) && (...)` and `run.state === "done" && !run.reused &&
  (...)`. Every other state (fresh walk, cancelled, failed) renders byte-unchanged.

- **Build-file revert (`next-env.d.ts`, `tsconfig.json`).** Iteration 30's scoped browser-QA rig
  left both tracked files pointing at an absolute scratchpad path
  (`/home/.../scratchpad/iter30-rig/frontend-dist/types/...`) that its own teardown never
  restored. Both files are now byte-identical (verified by diff) to their pre-iteration-30 content
  at commit `48c5fc2^`. This is pure TypeScript build plumbing — no product behavior change.

## Files Changed

- `apps/frontend/app/desk/page.tsx` — `LatestScreenRunDetail`: two added `&&` guards.
- `apps/frontend/next-env.d.ts` — reverted `<reference path>` to `./.next/types/routes.d.ts`.
- `apps/frontend/tsconfig.json` — reverted `include` array (dropped the scratchpad glob).

## Tests Run

- `cd apps/frontend && rm -rf .next && npm run build` — **compiled successfully** (Next.js
  15.5.19). Type-checking + linting passed with no errors; all 4 routes (`/`, `/_not-found`,
  `/desk`, `/structure`) built and prerendered as static content. This confirms the `tsconfig.json`
  revert (dropped `include` entry) and the `page.tsx` edit are both type-clean.
- No dedicated frontend unit-test runner exists in this project (per `package.json`'s `scripts`
  block — only `dev`/`build`/`start`). Frontend correctness for this fix is proven by (a) the
  clean production build/type-check above and (b) the existing golden replay
  `runs/goal-session-desk/journey-scripts/J-18.json`, whose two `expect` steps target the
  `desk-screen-runs-table` testid's own row text (`"101 / 101"`, `"no walk was performed"`) — NOT
  the `LatestScreenRunDetail` testids this fix touches — so the script's assertions are structurally
  unaffected by this change (spot-checked by reading the script; not executed in a browser by this
  agent — see Known Issues).

## Known Issues

- **No live browser verification performed by this agent.** TC-4 (a live check that the ambient
  store's current latest run — `state: "done"`, `reused: true`, `members_attempted: 0` — renders
  with neither suppressed testid present in the DOM) is a browser-qa responsibility, not the
  developer's. The build/type-check above proves the code compiles and the JSX guard logic is
  syntactically and structurally sound, but does not substitute for a screenshot.
- Per the plan (T-9), no `.next` rebuild + browser pass with a screenshot was attempted here —
  that is the browser-qa-agent's step. Repo hygiene note for that step: this iteration's own build
  above used `rm -rf apps/frontend/.next` immediately before `npm run build`, and left no stray
  files in `next-env.d.ts`/`tsconfig.json` (verified: `git status --porcelain --
  apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` reports only the intentional revert
  diff versus HEAD, and a direct diff against the pristine pre-iteration-30 commit is empty).
