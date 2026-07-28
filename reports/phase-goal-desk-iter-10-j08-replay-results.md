# Regression Replay — goal-desk-iter-10

**Phase:** goal-desk-iter-10
**Date:** 2026-07-28
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | step 04 expected "Viewing the recorded screen for 2026-07-25 — not the latest." did not appear | FAIL | reports/qa/goal-desk-iter-10-evidence/J-08-verify.png |

## Failed Tests

### UT-J-08 — Every ranked briefing row names the bar its distance was measured from

**Verdict:** FAIL
**Failure:** step 04 expected "Viewing the recorded screen for 2026-07-25 — not the latest." did not appear
**Evidence:** `reports/qa/goal-desk-iter-10-evidence/J-08-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-28

## Scoped data root (added by developer, TC-3 / IN SCOPE disclosure requirement)

This replay ran against the SCOPED throwaway copy of `apps/backend/.data/`, never the ambient
store. Absolute path:

```
/home/dennis-chan/.cache/iad/iad.goal-desk-iter-10.53029/desk-iter10-scoped-qa
```

Seeded via `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`; backend served on `:8301`,
frontend on `:3301` pointed at it. The step-04 failure above is the documented, non-blocking,
environmental same-date-screen-ambiguity: this scoped root legitimately holds two
`screen_date=2026-07-25` recordings (the pre-existing legacy `screen-2026-07-25-e184a7dc2f86` plus
this iteration's new `screen-2026-07-25-2ecce66af8d1`); `GET /research/desk/screen?date=` resolves
by date only (newest match wins), so a history-row click for that date is ambiguous. It does not
affect the DoD screenshot, which targets the default/latest view (no history click). See
`docs/handoffs/goal-desk-iter-10-dev.md` and `runs/goal-session-desk/journey-scripts/J-08.json`'s
own `notes` field for the full writeup.
