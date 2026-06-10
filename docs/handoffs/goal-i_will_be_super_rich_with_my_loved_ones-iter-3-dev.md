# goal-i_will_be_super_rich_with_my_loved_ones-iter-3 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-3
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

This is a LEAN, verification-first iteration. By design the developer step is near-no-op:
the value of iter-3 is **browser evidence** (produced by browser-qa, not here), and the
committed code diff is intentionally tiny. No backend, engine, classifier, config, or
journal-store change — the iter-2 backend is the verified foundation being surfaced.

- **Gitignore hardening:** extended `.gitignore` with a `.next*` pattern alongside the
  existing `.next` entry so isolated/QA build dirs (`NEXT_DIST_DIR=.next-qa`) can never be
  staged. Verified: `git check-ignore -v apps/frontend/.next-qa` → matches `.gitignore:48 .next*`.
- **Coherence advisory cleanup (iter-2 coherence.md):** removed the unused `fetchActiveThesis`
  export from `apps/frontend/lib/api.ts` and the now-unused `ThesisProjection` type import from
  that file. The strip reads the WS `thesis` key only (one read path per contract value —
  data-contract row 15); QA probes `GET /research/thesis/active` directly for the
  verbatim-equality check (J-38 step 3). A `// NOTE:` comment documents the deliberate single
  read path. `ThesisProjection` is still imported where it is genuinely used (`ThesisStrip.tsx`,
  `lib/types.ts`).
- **Environment repair (not a committed diff):** verified the live Tapeology dev server on the
  QA harness frontend port serves the cockpit at HTTP 200 (the iter-2 corrupt-`.next` failure is
  not present in the current environment); the live `.next` was left untouched.
- **No defect fixes were needed at initial-build time** — the J-38/J-39 UI surface was built and
  type-checks clean. Any defect browser-qa exposes in the strip/declare-form/inline-message legs
  will be fixed in the lean retry loop, scoped to `ThesisStrip.tsx` / `app/page.tsx` / `lib/api.ts`.

## Files Changed (committed app diff — exactly two files)

- `.gitignore` -- added `.next*` pattern so isolated QA build dirs can never be staged.
- `apps/frontend/lib/api.ts` -- removed unused `fetchActiveThesis` export and the now-unused
  `ThesisProjection` import; added a NOTE documenting the single WS read path for the thesis
  projection.

Build-tool side effects were reverted (NOT committed): the isolated `NEXT_DIST_DIR=.next-qa`
build mutated `apps/frontend/tsconfig.json` and `apps/frontend/next-env.d.ts` (Next rewrites the
dist-dir references on every build); both were restored with `git checkout --`, and the ephemeral
`.next-qa` dir was removed. Final committed app diff is the two files above only.

## Environment Repair Performed + Post-Build 200 Re-Probe

- **Pre-build state:** Tapeology frontend dev server already running on the harness port
  (`next-server v15.5.19`, cwd `apps/frontend`); backend running on the harness backend port.
- **Frontend cockpit probe (before build):** HTTP 200.
- **Stale-`.next` check:** the documented iter-2 failure (a `next build` clobbering the dev
  server's shared `.next`, 500-ing the cockpit) is NOT present — the running `.next` is healthy.
  No removal of the live `.next` was required this run.
- **Type-check build (binding harness rule applied):** ran `NEXT_DIST_DIR=.next-qa npm run build`
  in `apps/frontend` — compiled successfully in ~13s, no type errors, routes `/` and `/_not-found`
  generated. The build wrote to the isolated `.next-qa` dir; the live `.next` was never touched.
- **Post-build 200 re-probe (the DoD requirement):** re-probed the cockpit 3× after the isolated
  build + the `api.ts` edit — HTTP 200 on all three attempts. Live `.next` confirmed still present.
- **Live backend smoke (the J-38/J-39 foundation):** `GET /research/taxonomy` → 200;
  `GET /research/thesis/active?ticker=SIM-BIDABS` → `{"thesis":null}` (normal null state);
  `POST /research/thesis` on an unwatched ticker → 404 with explicit detail. The endpoints
  browser-qa will exercise are live and honest.

## Tests Run

Command (backend): `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **332 passed, 1 skipped, 2 warnings** — byte-for-byte the iter-2 green baseline, zero
regressions (the backend was not changed). The 2 warnings are pre-existing deprecation notices
(starlette TestClient / websockets.legacy), not failures.

Command (frontend type-check, isolated): `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build`
Result: compiled successfully, no type errors, 4 static pages generated. Confirms the
`fetchActiveThesis` / import removal compiles clean. (`.next-qa` removed after; ignored by the new
`.gitignore` pattern.)

## Known Issues

- **Browser evidence is the deliverable, produced by the next pipeline step.** J-38 (full declare
  journey on SIM-BIDABS: absorption_reversal/long, ACTIVE strip with frozen expected-behaviour
  statuses, verdict honestly `pending` slate, source + `data_feed: sim` stamp, REST==WS verbatim,
  no page reload) and J-39 (the 422/409/404 rejection matrix with inline messages, nothing
  persisted) must be demonstrated by browser-qa with per-journey screenshots in a non-empty
  evidence dir. The verdict stays honestly `pending` everywhere this iteration — the
  verdict-transition engine (J-40–J-46) is explicitly OUT OF SCOPE and deferred to iter-4.
- **Harness rules are binding for the QA legs:** any `npm run build` during the pipeline MUST use
  `NEXT_DIST_DIR=.next-qa` (or be deferred until after browser tests); kill the dev server by port
  (`fuser -k <port>/tcp`), never `pkill -f "next dev"` (the reloader child survives); re-probe the
  dev server for HTTP 200 after any build. An all-SKIP browser report counts as "frontend
  unverified" and MUST be hard-flagged FAIL (not soft-SKIP) for this iteration — the targets are
  UI journeys.
- **Servers left running on purpose:** the Tapeology harness frontend/backend were already up and
  are healthy (cockpit 200); I started no servers of my own, so none were killed. browser-qa can
  proceed against the live harness ports.
