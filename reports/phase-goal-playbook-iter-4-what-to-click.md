# Phase goal-playbook-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-playbook-iter-4
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend at `:8301` (`curl :8301/health` should return `{"status":"ok"}`)
- No login required
- At least one recorded session must exist that fires a `jbe`, `dbi`, or `cup_handle` signal. As of
  this iteration, no session in the operator's real recorded universe is known to fire one yet (the
  real back-scan is a future iteration's job) — if a QA fixture rig was stood up for this iteration
  (per the accompanying UI test plan), use ITS session date instead of guessing one on the real
  store. If no such session date is available, skip step 3 onward and only verify steps 1–2 and 6–7
  below.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads with no error screen; scrolling down eventually reaches a panel titled "Playbook Signals"

2. In the "Playbook Signals" panel, find the field labeled "Session date (yyyy-MM-dd) — blank = the most recent recorded session"
   - **Expect:** A text input and a "Run Playbook" button are both visible

3. Type the known JBE/DBI/cup-and-handle fixture session's date into that field, then click the "Run Playbook" button
   - **Expect:** The button briefly shows "Computing…", then returns to "Run Playbook" with a line reading "Playbook run complete for `<date>`." above it

4. In the signals table that appears, look at the "setup" column for each row
   - **Expect:** At least one row shows one of these three NEW chip labels: "Jump-Base Explosion", "Drop-Base Implosion", or "Cup and Handle" — not the raw text `jbe`/`dbi`/`cup_handle`

5. Click on that row (anywhere in the row)
   - **Expect:** The row expands into a detail panel showing a trigger/invalidation line, followed by a NEW geometry line specific to that setup type:
     - Jump-Base Explosion / Drop-Base Implosion rows show a line starting with "base ... MBR wide (... bars) · jump ... MBR"
     - Cup and Handle rows show a line starting with "cup ... bars · depth ... MBR · handle retrace ..."

6. Refresh the page (F5) with the same session date still entered
   - **Expect:** The same signal row and the same geometry line reappear — the record persisted, it was not a one-time render

7. Scroll up to the top of `/desk` and check one of the ALREADY-SHIPPED sections above Playbook Signals (for example, the screen history calendar or the ranked briefing)
   - **Expect:** That section looks and behaves exactly as before — no layout shift, no missing data, no new errors. This is a quick sanity check that this iteration's Playbook changes did not disturb anything else on the page

---

## What "Working Correctly" Looks Like

- The Playbook Signals table can now show five possible setup chips instead of two: "Open-High
  Break" and "Open-Low Break" (both already shipped) plus "Jump-Base Explosion",
  "Drop-Base Implosion", and "Cup and Handle" (new this iteration).
- Clicking any row's own setup-specific geometry line matches that setup's own shape — a JBE/DBI row
  never shows cup/handle wording, and a Cup and Handle row never shows base/jump wording.
- Every other part of `/desk` (session-date input, Run Playbook/Cancel controls, every section above
  Playbook Signals) behaves identically to before this update.

## Common Issues

- **Blank page / error screen on `/desk`**: check that the backend is running (`curl http://localhost:8301/health`) and that `apps/frontend/.next` was rebuilt after this update (`rm -rf apps/frontend/.next` then rebuild/restart) — a stale build can serve an old page.
- **No Jump-Base Explosion / Drop-Base Implosion / Cup and Handle row ever appears on any date you try**: this is expected on the real recorded universe today — this iteration's own testing was fixture-scoped only, and the real back-scan (a future update) has not run yet. Try the specific fixture-rig session date the QA team used, not an arbitrary real date.
- **Session date rejected with "is not a recorded trading session"**: this is existing, unchanged behavior from before this update — pick a date that is a real recorded trading day, or leave the field blank to use the most recent one.
