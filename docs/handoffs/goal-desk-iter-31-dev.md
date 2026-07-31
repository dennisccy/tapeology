# goal-desk-iter-31 Dev Handoff

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

Two small honesty/correctness fixes that iteration 30's depth-downgrade left unlanded, plus a
repo-hygiene revert. No new capability, no new page, no new `Config` field, no new MCP tool, no
fingerprint move — exactly as scoped.

1. **Backend — `failed_member` honesty fix (`desk_screen_compute.py`).** In
   `run_screen_and_record`'s `except Exception` handler, `failed_member` is no longer fabricated
   as `members[0]` when a screen run crashes BEFORE `_counting_progress` ever fires
   (`attempted == 0`). The single-line condition changed from
   `members[attempted] if attempted < len(members) else None` to
   `members[attempted] if 0 < attempted < len(members) else None`. The `attempted > 0` case
   (a genuine in-progress member) is byte-unchanged — verified by the pre-existing
   `test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member`, which
   still passes unmodified.

2. **Frontend — reused-run suppression fix (`desk/page.tsx`, `LatestScreenRunDetail`).** When the
   latest recorded screen run is `state === "done" && reused === true`, the component no longer
   renders the amber `desk-screen-run-latest-unreached` note ("N members not reached") or the
   `desk-screen-run-latest-counts` line ("0 ranked · 0 skipped..."). Both were misleading for a
   reused run — the run's own `screenRunOutcomeText` already discloses "reused `<id>` — no walk
   was performed" honestly, so a zeroed member/ranked count next to it read as a false failure
   signal. Both elements render byte-unchanged for every other state (fresh walk, cancelled,
   failed) — the added guard is purely `&& !(run.state === "done" && run.reused)` on the unreached
   note and `&& !run.reused` on the counts line.

3. **Repo hygiene — reverted two build files iteration 30's scoped rig polluted.**
   `apps/frontend/next-env.d.ts` and `apps/frontend/tsconfig.json` had a committed absolute
   scratchpad path (`/home/.../scratchpad/iter30-rig/frontend-dist/types/...`) left behind by a
   scoped-rig teardown that never ran `git checkout`. Both files are now byte-identical to their
   pre-iteration-30 content (diffed directly against `git show 48c5fc2^` — zero diff). This closes
   iteration 30's MINOR open anti-goal item.

## Files Changed

- `apps/backend/app/research/desk_screen_compute.py` — one-line fix: `failed_member` is `None`
  (never a fabricated symbol) when a run crashes before any member is attempted.
- `apps/backend/tests/test_desk_screen_compute.py` — added
  `test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null` (TC-1: proves the
  fix — fails without it, `'AAA' is None`) and
  `test_tc3_cli_run_leaves_exactly_one_matching_screen_run_record` (TC-3: a CLI-triggered run
  leaves exactly one `ScreenRunStore` record whose `state`/`screen_id`/`members_attempted` match
  the `ScreenStore` snapshot it produced).
- `apps/frontend/app/desk/page.tsx` — `LatestScreenRunDetail`: suppress the unreached note and the
  counts line for a `done && reused` latest run.
- `apps/frontend/next-env.d.ts` — reverted to pristine content (`./.next/types/routes.d.ts`).
- `apps/frontend/tsconfig.json` — reverted `include` array to pristine order/content (dropped the
  scratchpad glob).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1502 passed, 8 skipped, 0 failed** (exit code 0). Meets/exceeds the required ≥1,500-pass
/ 8-skip baseline.

Note: this run's own terminal reporter did not print its usual final `"N passed, M skipped in
X.XXs"` summary line (also reproduces on a bare `pytest tests/ --collect-only -q` with no code
changes at all — a pre-existing quirk of running the WHOLE `tests/` directory in this suite,
unrelated to this iteration's edits). Verified the count two independent ways instead: (1) `-q`'s
per-test progress characters contain exactly 1502 `.` (pass), 8 `s` (skip), and **zero** `F`
(fail) across all 21 progress lines, ending at `[100%]` with exit code 0; (2)
`pytest --collect-only -q`'s per-file counts sum to exactly 1510 (= 1502 + 8), matching (1)
independently. Not this iteration's concern to chase further (out of the plan's blast radius) but
disclosed here for the reviewer/auditor's own verification.

Targeted file (`tests/test_desk_screen_compute.py`, 37 tests including the two new ones): all
passed, confirmed with a normal (non-truncated) summary line: `37 passed, 2 warnings in 3.75s`.

TDD verification performed: temporarily reverted the backend fix (`git stash` of
`desk_screen_compute.py` only) and re-ran the new TC-1 test in isolation — it genuinely failed
(`assert 'AAA' is None` / `AssertionError: assert 'AAA' is None`), confirming the test exercises
the real bug. Restored the fix (`git stash pop`) and re-ran — passes.

Frontend: `cd apps/frontend && rm -rf .next && npm run build` — compiled successfully (Next.js
15.5.19, type-checking + linting passed, all 4 routes including `/desk` built), confirming the
`tsconfig.json`/`next-env.d.ts` revert and the `page.tsx` edit are type-clean.

Fingerprint / MCP contract verified directly:
`Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).
`len(app.mcp.TOOL_NAMES)` → `17` (unchanged).

`git status --porcelain -- apps/frontend/next-env.d.ts apps/frontend/tsconfig.json` diffed against
`git show 48c5fc2^:...` for both files — zero diff (TC-6/TC-9 satisfied).

## Known Issues

- No browser QA was run by this agent (out of scope for the developer role) — TC-4 (live ambient
  check of the reused-run suppression on `/desk`) and TC-8 (J-18 golden replay) are QA/browser-qa
  responsibilities. Spot-checked statically: `runs/goal-session-desk/journey-scripts/J-18.json`'s
  two `expect` steps target `desk-screen-runs-table`'s own row text (`"101 / 101"`, `"no walk was
  performed"`), not the `LatestScreenRunDetail` testids this iteration touches — so the golden
  replay should be unaffected by the frontend fix, but this has not been executed in a real
  browser by this agent.
- Per the spec, no `[NEW]`-flagged demo-narrator walkthrough was attempted by the developer agent
  — that is a downstream pipeline step, not in scope here.
- No fix to the `demo_runner.py` frame-deduplication bug — explicitly out of scope per the plan.
