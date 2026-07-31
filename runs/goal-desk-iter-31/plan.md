# goal-desk-iter-31 Execution Plan

## What to Build
- **Backend honesty fix:** in `desk_screen_compute.py`'s `run_screen_and_record` exception
  handler, stop naming `members[0]` as the `failed_member` when a run crashes before
  `_counting_progress` ever fires (`attempted == 0`) — record `null` instead. Keep
  `failed_member = members[attempted]` byte-unchanged for `attempted > 0` (a genuine in-progress
  member).
- **Frontend honesty fix:** in `/desk`'s `LatestScreenRunDetail`, suppress the
  `desk-screen-run-latest-unreached` amber note and the `desk-screen-run-latest-counts` line when
  the latest run is `state === "done" && reused === true` (the run's own `screenRunOutcomeText`
  already discloses the reuse honestly). Both elements stay byte-unchanged for every other state
  (fresh walk, cancelled, failed).
- **Repo hygiene:** revert the two tracked build files iteration 30's scoped rig polluted —
  `apps/frontend/next-env.d.ts` (drop the absolute scratchpad `<reference path>`, restore
  `./.next/types/routes.d.ts`) and `apps/frontend/tsconfig.json` (drop the scratchpad glob from
  `include`, restore the original entry order/count).
- **Tests:** two new backend tests (TC-1 crash-before-any-attempt → `failed_member: null`; TC-3
  CLI run → exactly one matching `ScreenRunStore` record) plus the existing TC-2 regression test
  stays green unmodified. No new frontend test file is required by the spec beyond the existing
  golden replay (`journey-scripts/J-18.json`, unchanged) and TC-4/TC-5's browser/reviewer checks.
- **No new capability, no new page, no new Config field, no new MCP tool, no fingerprint move.**
  This is a two-line-class correctness fix plus a repo-hygiene revert.

## Out of Scope (per spec — do not build)
- No `[NEW]`-flagged demo-narrator walkthrough as a blocking deliverable (non-blocking passenger
  only, last attempt).
- No re-capture of J-18's existing screenshots; no re-pin of `journey-scripts/J-18.json`.
- No touch to the ranked/skipped table, its `<colgroup>`, or any golden replay script J-01..J-16
  depends on.
- No change to `desk_screen.py`'s snapshot/row/skip shapes, rank order, or five-pin key.
- No fix to the `demo_runner.py` frame-deduplication bug.

## Agents Required
- developer: yes -- implement the backend `failed_member` fix, the frontend
  `LatestScreenRunDetail` suppression fix, revert the two polluted build files, and add the two
  new backend tests (TC-1, TC-3) per the exact contract below.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/research/desk_screen_compute.py` (~:277) -- change
  `failed_member = members[attempted] if attempted < len(members) else None` to
  `failed_member = members[attempted] if 0 < attempted < len(members) else None` (or an
  equivalent explicit `if attempted == 0: None else members[attempted] if attempted <
  len(members) else None`) inside the `except Exception` block of `run_screen_and_record`.
  Everything else in this function/module is untouched.
- `apps/backend/tests/test_desk_screen_compute.py` -- add TC-1 (a `fake_compute_screen` that
  raises before ever calling `progress(...)`, i.e. `attempted == 0`; assert the recorded terminal
  `"failed"` run has `failed_member: null` -- follow the pattern of the existing
  `test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member`, which
  must keep passing unmodified as the `attempted > 0` regression guard for TC-2); add TC-3 (drive
  `python -m app.research.desk_screen_compute --date <D>` against a scoped fixture dir --
  reuse the existing CLI test fixtures/pattern near `test_cli_with_date_runs_to_completion_against_a_scoped_fixture_dir`
  -- then assert `ScreenRunStore.list()` returns exactly one record with `state == "done"`,
  `screen_id` equal to the persisted `ScreenStore` snapshot's own `id`, and
  `members_attempted == members_total`).
- `apps/frontend/app/desk/page.tsx` (`LatestScreenRunDetail`, ~:1312-1342) -- guard the
  `unreached > 0 && (...)` block (~:1331) and the `run.state === "done" && (...)` block (~:1337)
  so BOTH also require `!(run.state === "done" && run.reused)` (equivalently, add `&& !run.reused`
  to the second condition and `&& !(run.state === "done" && run.reused)` to the first). Do not
  change any other JSX in this component, its `data-testid` strings, or `screenRunOutcomeText`.
- `apps/frontend/next-env.d.ts` -- restore exactly:
  ```
  /// <reference types="next" />
  /// <reference types="next/image-types/global" />
  /// <reference path="./.next/types/routes.d.ts" />

  // NOTE: This file should not be edited
  // see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
  ```
- `apps/frontend/tsconfig.json` -- restore the `include` array to exactly:
  `["**/*.ts", "**/*.tsx", ".next-eval-iter10/types/**/*.ts", ".next/types/**/*.ts",
  "next-env.d.ts", ".next-qa/types/**/*.ts"]` (this is the pristine pre-iter-30 order/content;
  verify with `git show 48c5fc2^:apps/frontend/tsconfig.json` if in doubt). No other key in this
  file changes.
- `docs/handoffs/goal-desk-iter-31-dev.md` -- dev handoff (required by Definition of Done).

## Operational note for browser-qa / demo-narrator dispatch (not a developer code change)
Per the spec's repo-hygiene item and TC-9: if this iteration's browser-qa or demo-narrator step
provisions a scoped rig (a second `next build`/`next dev` against an alternate `NEXT_DIST_DIR`),
its teardown must either build from a full separate copy of `apps/frontend` (never touching the
tracked working copy) or run `git checkout -- apps/frontend/next-env.d.ts
apps/frontend/tsconfig.json` as its LAST step. Verify with
`git status --porcelain -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` (must be
empty) before reporting done. This is the exact failure mode iteration 30 left open -- do not
repeat it.

## UI Evolution
- New user-facing capability: none -- this is a correctness fix to an existing detail block.
- New information displayed: none -- corrects rendering of already-registered fields (`reused`,
  `members_attempted`, `failed_member`); no new field or endpoint.
- New user actions: none.
- UI surface changes: `/desk`'s existing "Screen Runs" section, "Latest run" detail block only --
  no new page, section, or control.
- Navigation changes: none.

## Visual Requirements
- Component patterns: no new components; reuse the existing `LatestScreenRunDetail` block and its
  existing Tailwind classes/`data-testid`s exactly as shipped, just gated by an added boolean
  condition.
- Layout: unchanged.
- Key visual effects: unchanged (amber note styling stays identical for the cases where it still
  renders -- fresh walk, cancelled, failed).
- States to handle: `done && reused` (suppress both elements, new); `done && !reused` (render
  counts as before, byte-unchanged -- TC-5); `failed` (unaffected, still renders the failed-member
  block, now honestly `null`-safe via the existing `?? "(member not recorded)"` fallback for the
  `attempted == 0` case); `cancelled`/`running` (unaffected).

## Key Test Scenarios
- TC-1: `run_screen_and_record` raises before `_counting_progress` ever fires (`attempted == 0`)
  -> the terminal `"failed"` run record has `failed_member: null`.
- TC-2 (regression): `run_screen_and_record` raises after `attempted > 0` -> `failed_member ==
  members[attempted]`, unchanged (existing test
  `test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member` must
  stay green unmodified).
- TC-3: a CLI run (`python -m app.research.desk_screen_compute --date <D>`) against a scoped
  fixture dir leaves exactly one `ScreenRunStore` record, `state == "done"`, `screen_id` equal to
  the persisted `ScreenStore` snapshot's own id, `members_attempted == members_total`.
- TC-4 (browser, live ambient check): the current ambient store's latest recorded screen run
  (`state: "done"`, `reused: true`, `members_attempted: 0`) renders on `/desk` with NEITHER
  `data-testid="desk-screen-run-latest-unreached"` NOR
  `data-testid="desk-screen-run-latest-counts"` present in the DOM.
- TC-5 (reviewer diff check, not live-verifiable per NOTES): the `done && !reused` branch that
  still renders `desk-screen-run-latest-counts` is byte-unchanged from pre-iteration source.
- TC-6: `next-env.d.ts` / `tsconfig.json` contain no `/scratchpad/` substring and no path outside
  the repository after the revert; `next-env.d.ts`'s reference path reads exactly
  `./.next/types/routes.d.ts`.
- TC-7: full backend suite passes at or above 1,500 pass / 8 skip; `Config().config_fingerprint()`
  still `08e471b10130e1e2`; `len(app.mcp.TOOL_NAMES) == 17`.
- TC-8 (golden replay regression): `journey-scripts/J-18.json` (unchanged) replays all four steps
  green against the ambient store.
- TC-9: after any scoped-rig dispatch this iteration runs, `git status --porcelain --
  apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` reports no diff.
