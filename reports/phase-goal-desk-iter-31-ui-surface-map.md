# Phase goal-desk-iter-31 — UI Surface Map

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `LatestScreenRunDetail` — amber "not reached" note (`data-testid="desk-screen-run-latest-unreached"`) and counts line (`data-testid="desk-screen-run-latest-counts"`), inside the "Screen Runs" panel's "Latest run" block | Changed behavior | A reused run's own honest "reused — no walk was performed" outcome text was previously shadowed by an amber "N members not reached" warning and a "0 ranked · 0 skipped..." counts row, reading like a failure when nothing failed | Navigate to `http://localhost:3301/desk`, scroll to the "Screen Runs" panel, and in the "Latest run — 2026-07-31 · screenrun-2026-07-31-fe0829e64a0d" block confirm elements with `data-testid="desk-screen-run-latest-unreached"` and `data-testid="desk-screen-run-latest-counts"` are absent from the DOM (only `desk-screen-run-latest-outcome` reading "reused screen-2026-07-31-c169546856c7 — no walk was performed" is present) |
| `/desk` | `LatestScreenRunDetail` — failed-run block (`data-testid="desk-screen-run-latest-failed"` / `desk-screen-run-latest-failed-detail`), driven by the backend's `failed_member` field from `GET /research/desk/screen/runs` | Changed behavior (backend-driven, indirect) | `desk_screen_compute.py`'s `run_screen_and_record` no longer fabricates `failed_member = members[0]` when a run crashes before `_counting_progress` ever fires (`attempted == 0`); it now records `null`, which the unchanged frontend fallback `run.failed_member ?? "(member not recorded)"` (page.tsx line ~1346) renders honestly | Cannot be exercised on the current ambient `/desk` store — no crash-before-any-attempt run is recorded there today. Verify instead via `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_screen_compute.py -k "test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null or test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member" -q` — both must pass, proving `failed_member` is `null` for an `attempted == 0` crash and unchanged (`members[attempted]`) for `attempted > 0` |
| `/desk` | `LatestScreenRunDetail` — counts line (`data-testid="desk-screen-run-latest-counts"`) for a genuine (non-reused) completed run | Regression / unchanged | This iteration's guard only added `&& !run.reused`; the `done && !reused` branch itself is byte-unchanged and must keep rendering ranked/skipped counts for a real full walk | Not live-verifiable this iteration — the ambient store's current *latest* run is reused, so no live `done && !reused` run is the "latest" one to inspect directly (logged in `runs/goal-session-desk/state/assumptions.md`, iter-31). Verify instead by reading `apps/frontend/app/desk/page.tsx` lines 1337–1342 and confirming the JSX inside the `run.state === "done" && !run.reused` block (`{run.ranked_count} ranked · ...`) is identical to the pre-iteration source, or by finding an earlier non-reused row in the `desk-screen-runs-table` (e.g. `screenrun-2026-07-31-725c4ec2bfcd`, "101 / 101") and confirming it is not currently shown as "latest" |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_screen_compute.py` — adds `test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null` and `test_tc3_cli_run_leaves_exactly_one_matching_screen_run_record` — test-only file, no UI surface affected.
- `apps/backend/app/research/desk_screen_compute.py`'s CLI path (TC-3: a `python -m app.research.desk_screen_compute --date <D>` run leaves exactly one matching `ScreenRunStore` record) — verifies existing recording correctness; the record it checks is the same `GET /research/desk/screen/runs` data already covered by the surface-map rows above, so this specific test adds no NEW UI-visible behavior of its own.
- `apps/frontend/next-env.d.ts` — reverted `<reference path>` from a dangling absolute scratchpad path back to `./.next/types/routes.d.ts` — TypeScript build plumbing only, no runtime/UI effect.
- `apps/frontend/tsconfig.json` — reverted the `include` array to drop a scratchpad glob left by a prior iteration's scoped test rig — TypeScript build plumbing only, no runtime/UI effect.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk`'s `LatestScreenRunDetail` — 2 gated elements)
- **New pages/routes:** 0
- **Modified components:** 1 (`LatestScreenRunDetail`, inside `apps/frontend/app/desk/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (test file + CLI-path test + 2 build-config files)
