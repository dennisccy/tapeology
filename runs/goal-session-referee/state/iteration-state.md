# Iteration State — referee

**After iteration:** 13 · **Date:** 2026-08-16 · **Verdict:** CONTINUE

## Journeys

12 passing (J-01..J-12) · 0 failing · 0 unknown — 12 total. J-11 + J-12 carry `evidence_makeup`
(owed captures: J-11's walkthrough recording, J-12's strategy-family tick-gate + caveat).

## Active blockers

- **J-01 + J-02 were DEFERRED-BUDGET** (`phase-goal-referee-iter-13-ui-test-results.md:39-40`) —
  not tested, so the achievement gate blocks GOAL_ACHIEVED. Owner: QA lane. Both are backend-only
  (`J-0{1,2}.json.invalid`): re-verify by running `tests/test_referee_guards.py` +
  `tests/test_referee_evidence.py` and writing real PASS rows into the results table (iter-11).
- **J-12's owed capture.** Both captures truncate at the tool's 4,320px cap; `/desk`'s
  `scrollHeight` is ~8,443px. Capture the `referee-evidence-strategy-block` element itself, or
  collapse the sections above it — a full-page capture cannot reach it. Owner: QA lane.
- Human-owned, non-blocking: uncommitted files; the shared recorder (`.../demo_runner.py`) cannot
  play `scroll`, so the era has no video walkthrough; trendora's port-8255 backend not restarted.

## Last 2 verdicts

- iter 13: CONTINUE — J-12 shipped and verified on two rigs, zero backend diff, rails clean; but
  J-01/J-02 skipped for time and one J-12 capture clause unphotographed.
- iter 12: GOAL_ACHIEVED — J-11's accrual-basis disclosure verified; eleven journeys passing.

## Do not redo

- **J-12 is built + verified** — `lib/api.ts:2122`, `lib/types.ts:2429`,
  `RefereeEvidenceReadinessSection` (`app/desk/page.tsx:5004-5200`), `journey-scripts/J-12.json`.
- **Backend byte-frozen** — `git diff -- apps/backend/app` EMPTY at iter-13; `referee_evidence.py`'s
  served body is pinned by a golden test. Do not touch it. Its `integrity_errors` really is
  `{file, error}[]` (the iter-13 spec's `[string]` paraphrase was wrong) — settled.
- **Guards already widened** — `_PRICE_ARITHMETIC_FIELDS` covers all 7 new referee numerics;
  `_EXPECTED_EFFECT_COUNT` stays 21; `EXPECTED_TOOLS` stays 22. Extend, never edit.
- **Carried clean-ups, non-blocking:** stray assertion `test_desk_ui_guards.py:371-372`; 4 Referee
  store dirs absent from the guard; no-name cert should fail; dash-not-word on a failed 2nd fetch.
- **J-05's replay timeout 8s→12s is by design** (assertion text unchanged) — the iter-13 replay
  FAIL was a latency false negative, verified by screenshot. Not a regression.
