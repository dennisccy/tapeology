# Phase goal-rapid-microscope-iter-16 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-16
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
- No login required, no seed data required — this guide checks the app's real current state.
  Microscope Readiness genuinely has 2 recorded tick shards today; Scout Ledger, Walk-Forward, and
  Validation Vault are all genuinely empty. Both are correct and expected — you are not setting
  anything up.
- **Do not click "Run Screen" (in Scout Ledger) or "Run Walk-Forward" (in Walk-Forward) during this
  guide.** Both start a real backend computation that can run 25+ minutes with no reliable fast
  cancel — well outside a 5-minute check.
- This round adds no new feature or button — you are confirming two small robustness fixes held and
  nothing else broke, not trying out something new.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with no error banner. The heading reads "Desk".

2. Open your browser's DevTools console (press F12, then click the "Console" tab) and leave it open
   for the rest of this guide
   - **Expect:** No red errors so far.

3. Click the "Microscope Readiness" section header
   - **Expect:** It expands (arrow "▸" becomes "▾"), showing "Distinct symbol-days: 1" and
     "Distinct datasets: 2" in the "Corpus Totals" table, plus 2 rows (both symbol `PG`) under
     "Legacy Tick Shards". No new console errors.

4. Right-click anywhere inside that now-open panel → Inspect
   - **Expect:** The nearest ancestor `<div>` carries `data-testid="micro-readiness-section"`. This
     is this round's actual fix — before this round, that attribute was missing whenever the panel
     was loading or unavailable, only present once fully loaded.

5. Click "Scout Ledger", then "Walk-Forward", then "Validation Vault", then each of the three
   Referee section headers, one at a time
   - **Expect:** Every one expands cleanly. Scout Ledger shows "No candidates ledgered."; Walk-Forward
     shows "No fold specs registered." and "No walk-forward sequences run."; Validation Vault shows
     "No shards recorded." and "No universes registered." **No new red console error appears after
     any of these clicks** — this is the single most important check in this guide.

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** Every section header you opened is back to the closed "▸" state — every section
     starts collapsed on reload, on purpose.

7. Navigate to `http://localhost:3301/structure`, then to `http://localhost:3301/`
   - **Expect:** Both pages load with no error banner — confirms this round's `/desk`-only change
     didn't touch either page.

8. On `http://localhost:3301/`, confirm the mode selector reads "Simulated", type `SIM-BUYER` into
   the ticker field, then click "Watch"
   - **Expect:** The chart renders and the live tape begins updating.

---

## What "Working Correctly" Looks Like

- Every `/desk` section expands with zero new red console errors — the entire point of this round
  is robustness, not a new feature, so a clean console after every click is the pass signal.
- The Microscope Readiness panel keeps its `micro-readiness-section` DOM tag whether it's loading,
  unavailable, or fully loaded (step 4).
- Nothing on `/structure` or `/` looks any different than before this round.

## Common Issues

- **A section shows an amber box reading "Backend unreachable — is the API running?"**: the backend
  isn't running. Check with `curl http://localhost:8301/health` — it should return `{"status":"ok"}`.
- **A red console error or hydration warning appears after expanding a section**: note the exact
  section and the exact error text — this is the one regression this guide is specifically watching
  for. A defect exactly like this previously escaped a full iteration because nothing checked the
  console.
- **The Cockpit chart looks frozen/static**: this is a known quirk of some headless/background-tab
  browser setups (`visibilityState: "hidden"`), not necessarily a real bug — confirm the page is
  the active, visible browser tab before reporting it as broken.
- **You accidentally clicked "Run Screen" or "Run Walk-Forward"**: this is safe but leaves a real
  computation running in the backend for a while. You can leave it running (it doesn't corrupt any
  data) or restart the backend process to stop it early.
