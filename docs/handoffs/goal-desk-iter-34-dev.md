# goal-desk-iter-34 Dev Handoff

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

- Fixed `topupLibraryReach` in `apps/frontend/app/desk/page.tsx` so the "newest recorded reach"
  extreme and the "Pairs recorded earlier" partition are both computed by grouping
  `store_frozen_through_after` at CALENDAR-DAY precision (a day-truncated key derived once per
  outcome), never by comparing the raw microsecond-precision timestamp. Before this fix, a pair
  recorded a few hours behind another pair on the IDENTICAL calendar day was miscounted as
  "earlier" purely because of its own sub-day precision — the bug iter-32/33 left unfixed.
- Added a 20-row cap (`EARLIER_PAIRS_DISPLAY_CAP = 20`) on the rendered `earlier` array, with a new
  `earlierTotal` field that preserves the TRUE count separately, so the "Pairs recorded earlier (N)"
  heading always shows the honest true total (never the capped array's own length).
- Added a conditional one-line disclosure ("showing `<shown>` of `<true total>`", new testid
  `desk-topup-run-latest-reach-earlier-cap`) that renders ONLY when the true earlier-pairs total
  exceeds 20. When the true total is ≤ 20, nothing new renders (unchanged behavior).
- Extended `apps/backend/tests/test_desk_topup_library_reach_guard.py` (source-introspection style,
  matching this file's/this codebase's existing pattern — there is no JS test runner in this repo,
  so all frontend logic is guarded by reading `page.tsx` as text) with:
  - a day-truncation structural assertion + its seeded-violation counterpart (proves the check can
    fail against the ACTUAL iter-32/33 buggy body);
  - a cap structural assertion (cap constant + capped slice + a separately-tracked true total) + its
    seeded-violation counterpart;
  - a render-wiring assertion proving the cap-disclosure sits inside the earlier block (between the
    heading and the failed-pairs block), is conditionally gated on `earlierTotal >
    EARLIER_PAIRS_DISPLAY_CAP`, and that the heading itself counts `earlierTotal` (never the capped
    array's length) + its own seeded-violation counterpart.
  - 11 tests total in this file now (was 5), all passing; zero backend production-code diff.
- Repointed `runs/goal-session-desk/journey-scripts/J-19.json` to stable substrings/testid-existence
  checks: no longer asserts any specific date, count, or the bug's own contradictory earlier-row
  text (`"AAPL 4h — 2026-07-30"`). Added a new step proving the cap-disclosure testid renders
  (currently true against the ambient run, documented as an honest environment-dependent assertion
  per the J-09/J-17/J-18 precedent).
- Updated `runs/goal-session-desk/state/blueprint.md`: flipped the iter-34 build-time-scope note
  from "IN BUILD at iter-34" to "RESOLVED at iter-34" (past tense, describing what actually landed
  in this commit, including the concrete post-fix numbers observed against the ambient run), and
  updated the J-19 summary row's pointer text to match.

## Files Changed

- `apps/frontend/app/desk/page.tsx` — day-precision grouping fix in `topupLibraryReach`, 20-row cap
  with a separately-preserved true total, conditional "showing N of M" disclosure sentence. No new
  section/control/column — entirely inside the already-registered library-reach block.
- `apps/backend/tests/test_desk_topup_library_reach_guard.py` — extended with day-truncation + cap
  + render-wiring assertions and their seeded-violation counterparts.
- `runs/goal-session-desk/journey-scripts/J-19.json` — repointed to stable substrings/testid
  existence checks; no longer enshrines the bug.
- `runs/goal-session-desk/state/blueprint.md` — "IN BUILD at iter-34" → "RESOLVED at iter-34",
  landed in the same diff as the code (iter-30 lesson).

No backend production code touched: zero diff to `desk_topup_compute.py`, `desk_topup_log.py`,
`bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, or
`routes.py`'s `record_bar_series`, as required by the spec (`store_frozen_through_after`'s stored
value/precision was already correct — only the frontend's display-time grouping was wrong).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1528 tests, 0 failed, 0 errors, 8 skipped (junit-xml summary; full suite green).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -q`
Result: 39 passed — 17-tool MCP contract intact, zero diff.

Command: `cd apps/backend && .venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"`
Result: `08e471b10130e1e2` — unchanged (zero new `Config` field, as required).

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json`
Result: no type errors.

Deterministic golden-replay (demo_runner.py --mode verify) against the ambient `:3301`/`:8301` pair,
after the mandatory `rm -rf apps/frontend/.next` + clean rebuild + restart (T-9):

```
python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py --mode verify \
  --scripts-dir runs/goal-session-desk/journey-scripts \
  --journeys "J-19,J-04,J-07,J-09,J-16,J-17" \
  --base-url http://127.0.0.1:3301 ...
```
Result: 6/6 journeys PASS (J-19 + the five Required-still-passing journeys J-04, J-07, J-09, J-16,
J-17). Evidence: `reports/qa/goal-desk-iter-34-evidence/regression-replay-dev-check.md` +
`J-19-verify.png` etc.

## TC-1..TC-9 disclosure — live (screenshot) vs unit/fixture level (test output)

Per the spec's own honesty note, disclosing exactly which acceptance criteria I verified live in a
real browser against the ambient run vs. at the unit/structural level:

- **TC-1 (LIVE, screenshot)** — verified in a real browser against the ambient
  `topup-2026-07-31-8fb5c9a1f737` run (404 pairs) post-T9-rebuild: "newest recorded reach
  2026-07-30 · 303 pairs reach it" renders, and every visible "Pairs recorded earlier" row prints
  `2026-07-27` — never `2026-07-30`. Screenshot:
  `reports/qa/goal-desk-iter-34-evidence/UT-J-19-topup-reach-crop.png` (cropped from a full-page
  capture at 1440×900 CSS viewport; DOM-text extraction of the same block is also captured in this
  handoff's supporting session log).
- **TC-2 (unit/structural)** — no JS test runner exists in this repo (frontend logic is guarded via
  Python source-introspection throughout this codebase); proven structurally by
  `test_topup_library_reach_groups_by_day_truncated_key_not_raw_timestamp`. Indirectly corroborated
  live: the ambient run's 303 "newest" pairs span multiple distinct microsecond timestamps all on
  2026-07-30, and none of them appear in "earlier" — the exact TC-2 behavior, occurring naturally in
  real data.
- **TC-3 (LIVE, exceeds the synthetic 25-outcome case)** — the ambient run's TRUE earlier-pairs
  total is 101 (all on 2026-07-27), so the returned `earlier` array is observed capped at exactly 20
  live, with the true total (101) separately visible in the heading. This is a stronger, real-world
  instance of the spec's synthetic 25-outcome example, also covered structurally by
  `test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total`.
- **TC-4 (LIVE, screenshot)** — the ambient run's true earlier-total (101) exceeds 20, so "showing
  20 of 101" is live-observable (same screenshot as TC-1) — the spec's own fallback-to-unit-level
  allowance was not needed this iteration because the current ambient data happens to exceed the
  cap.
- **TC-5 (unit/structural only — NOT live this iteration)** — the ambient run's true total (101)
  is > 20, so the "no disclosure when ≤ 20" branch is not exercised by any run currently on disk.
  Verified only by the conditional's own structure (`{libraryReach.earlierTotal >
  EARLIER_PAIRS_DISPLAY_CAP && (...)}`) and by unmodified render logic — no screenshot of this
  branch exists.
- **TC-6 (unit/structural only — NOT re-verified live)** — the legacy-run fallback path
  (`outcomes.some(... === undefined)`) was not touched by this diff at all, and the existing,
  unmodified test `test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after`
  still passes. No run on the ambient store currently lacks the field, so this was not re-exercised
  in a live browser this iteration.
- **TC-7 (unit/structural)** —
  `test_day_truncation_guard_can_fail_on_a_seeded_violation` passes: feeding the ACTUAL iter-32/33
  buggy function body to the same check makes it fail, proving the day-truncation guard is not
  vacuous.
- **TC-8 (unit/structural)** — `test_cap_guard_can_fail_on_a_seeded_violation` passes: an uncapped
  `earlier` array (the old bug) fails the same cap check.
- **TC-9 (LIVE)** — ran the repointed `journey-scripts/J-19.json` through
  `demo_runner.py --mode verify` against the real ambient `:3301` page: PASS, and by construction
  the script no longer asserts any specific date, count, or the bug's own contradictory row text.
- **TC-10 (LIVE, full suite)** — see Tests Run above: full backend suite green, fingerprint
  unchanged, MCP 17-tool contract intact.

## Pre-handoff verification

- Service startup: `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-backend.sh`
  and `bash scripts/start-frontend.sh`, both after `rm -rf apps/frontend/.next` (T-9). Backend
  responded 200 on `GET /research/desk/topup/runs`; frontend responded 200 on `/` and `/desk` and
  compiled both routes cleanly. Both processes stopped after verification (their PIDs — the ones
  this session started — were terminated; a pre-existing, longer-running ambient uvicorn process on
  the same port, started well before this session began, was left untouched since it does not
  belong to this dispatch).
- No new native dependency or external integration was added this iteration (frontend-only display
  fix + backend test-only change), so the "external integrations" and "native dependency binaries"
  checklist items are not applicable.

## Known Issues

- The `[NEW]`-flagged demo-narrator walkthrough (DoD requirement) was NOT recorded by this
  developer dispatch — that is a separate pipeline step (demo-narrator agent), expected to run
  immediately after this commit lands, narrated from the actually-rendered post-fix page per the
  iter-33 lesson. This handoff's own browser check (TC-1/TC-3/TC-4 screenshot) confirms the page is
  ready for that walkthrough.
- TC-5 and TC-6 are not live-verified this iteration (see disclosure above) because no run currently
  on the ambient store exercises those two branches; both are unchanged/structurally guarded code
  paths, not new risk introduced by this fix.
- `reports/qa/goal-desk-iter-34-evidence/` also contains a full-page screenshot
  (`UT-J-19-dev-sanity-fullpage.png`, 1425×8438) taken to derive the cropped TC-1/TC-3/TC-4 evidence
  — a direct viewport screenshot after `scrollIntoView` came back solid black (a known browser-tool
  rendering quirk on deep-scrolled pages in this environment, previously documented in this
  project's own history); the full-page capture + crop worked around it and is the artifact of
  record.
