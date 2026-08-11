# Phase goal-playbook-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-playbook-iter-6
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend at `:8301` (`curl :8301/health` should return `{"status":"ok"}`)
- No login required
- At least one recorded session must exist that fires a `range_trade`, `double_top`, or
  `double_bottom` signal. As of this iteration, no session in the operator's real recorded universe
  is known to fire one yet (the real back-scan is a future iteration's job) — if a QA fixture rig was
  stood up for this iteration (per the accompanying UI test plan: symbol `RTAAA` for range_trade,
  symbol `DTAAA` for double_top, both dated `2026-06-22`), use ITS session date instead of guessing
  one on the real store. If no such session date is available, skip step 3 onward and only verify
  steps 1–2 and 7–8 below.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads with no error screen; scrolling down eventually reaches a panel titled "Playbook Signals"

2. In the "Playbook Signals" panel, find the field labeled "Session date (yyyy-MM-dd) — blank = the most recent recorded session"
   - **Expect:** A text input and a "Run Playbook" button are both visible; the paragraph just above the input mentions "range-trade, double-top, and double-bottom" among the eight families it lists

3. Type the known range-trade/double-top fixture session's date into that field, then click the "Run Playbook" button
   - **Expect:** The button briefly shows "Computing…", then returns to "Run Playbook" with a line reading "Playbook run complete for `<date>`." above it

4. In the signals table that appears, look at the "setup" column for each row
   - **Expect:** At least one row shows one of these three NEW chip labels: "Range Trade", "Double Top", or "Double Bottom" — not the raw text `range_trade`/`double_top`/`double_bottom`

5. Click on that row (anywhere in the row)
   - **Expect:** The row expands into a detail panel showing a trigger/invalidation line, followed by a NEW geometry line specific to that setup type:
     - Range Trade rows show a line starting with "range ... MBR wide · low zone touches ... · high zone touches ..."
     - Double Top / Double Bottom rows show a line starting with "gap ... MBR · separation ... bar(s) · depth ... MBR · nominal risk ... MBR"

6. Scroll to the bottom of the record and read the amber note box
   - **Expect:** The register text lists all eight family names, ending "...capitulation, range-trade, double-top, and double-bottom signals detected..." — a record recomputed under this iteration's code always shows this widened wording (an older, un-recomputed record from before this iteration would still show the old five-family wording — that is expected, not a bug, since records are never rewritten)

7. Refresh the page (F5) with the same session date still entered
   - **Expect:** The same signal row and the same geometry line reappear — the record persisted, it was not a one-time render

8. Scroll up to the top of `/desk` and check one of the ALREADY-SHIPPED sections above Playbook Signals (for example, the screen history calendar or the ranked briefing)
   - **Expect:** That section looks and behaves exactly as before — no layout shift, no missing data, no new errors. This is a quick sanity check that this iteration's Playbook changes did not disturb anything else on the page

---

## What "Working Correctly" Looks Like

- The Playbook Signals table can now show eight possible setup chips instead of five:
  "Open-High Break", "Open-Low Break", "Jump-Base Explosion", "Drop-Base Implosion", "Cup and
  Handle", "Capitulation" (all already shipped) plus "Range Trade", "Double Top", and "Double
  Bottom" (new this iteration).
- Clicking any row shows its own setup-specific geometry line — a Range Trade row never shows
  gap/depth wording, and a Double Top/Bottom row never shows range-width wording.
- The Playbook Signals section's own intro text and the "not computed yet" empty-state message both
  now name all eight families instead of five.
- Every other part of `/desk` (session-date input, Run Playbook/Cancel controls, every section above
  Playbook Signals, and every one of the five previously-shipped setup types) behaves identically to
  before this update.

## Common Issues

- **Blank page / error screen on `/desk`**: check that the backend is running (`curl http://localhost:8301/health`) and that `apps/frontend/.next` was rebuilt after this update (`rm -rf apps/frontend/.next` then rebuild/restart) — a stale build can serve an old page.
- **No Range Trade / Double Top / Double Bottom row ever appears on any date you try**: this is expected on the real recorded universe today — this iteration's own testing was fixture-scoped only, and the real back-scan (a future update) has not run yet. Try the specific fixture-rig session date the QA team used (`2026-06-22` for the `RTAAA`/`DTAAA` fixtures), not an arbitrary real date.
- **Session date rejected with "is not a recorded trading session"**: this is existing, unchanged behavior from before this update — pick a date that is a real recorded trading day, or leave the field blank to use the most recent one.
- **An old record's register note at the bottom still says only five families**: this is expected, not a bug — playbook records are never rewritten. Click "Run Playbook" again for that same date to compute a fresh, newly-versioned record with the updated eight-family wording.
