# Phase goal-structure_ui-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-structure_ui-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable from the frontend — there is no login in this app, nothing to sign
  in with
- No seed data or setup is required — every step below works against this environment's normal,
  default state

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser
   - **Expect:** The heading "Structure" appears near the top. No error page, no blank white screen.

2. Without clicking anything, wait about 2 seconds, then scroll down past the "Confluence zones" box
   - **Expect:** A "Registry" section appears on its own (no click needed), showing a "Champion" box
     followed by two cards headed "v1" and "structure_tape".

3. In the "Champion" box, read the "strategy" and "profile" values
   - **Expect:** They read "v1" and "default". A small note underneath reads "Confirmed identical to
     the champion served by GET /research/profiles — one store pointer, two read views."

4. Look at the two cards below the Champion box
   - **Expect:** The second card, "structure_tape", shows three small tables titled "stop (bps by
     class)", "reward target (R-multiple by class)", and "size (multiple by class)". The first card,
     "v1", does not have these three tables — that's correct, not a bug.

5. Near the top of the page, type `ZZTEST` into the "Symbol" field, type `2026-06-09T21:00:00Z` into
   the "As-of (UTC, ISO-8601)" field, then click "Load"
   - **Expect:** A message reading "No bar series recorded for ZZTEST." appears above the Registry
     section. This is the correct, honest response for a symbol with no recorded historical data —
     it is not an error and not something to fix; it confirms the page's older feature still tells
     the truth instead of faking a chart.

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The Registry section (Champion box + both cards) reappears with the exact same
     "v1" / "default" / "structure_tape" content as in steps 2–4 — confirms it's read fresh from the
     backend every time, not a one-off fluke.

7. Click "Performance" in the top navigation bar
   - **Expect:** The Performance page loads, and its own "Champion" box (right-hand side of the
     page) still correctly shows "v1" / "default" — confirms the new Structure page section didn't
     break the older Performance page.

---

## What "Working Correctly" Looks Like

- The Registry section (Champion box + "v1"/"structure_tape" cards) appears automatically on
  `/structure` with no click, and every value matches exactly what's described in steps 2–4 above.
- The older Levels & Zones section on the same page still honestly reports "no data" for a symbol
  it has never recorded — it never fakes a chart or a level line.
- `/performance`'s own Champion box, unrelated code from before this phase, still shows correctly.

## Common Issues

- **Blank page or error overlay on `/structure`:** the backend is likely not running or not
  reachable from the frontend — check with whoever started the app.
- **The Registry section stays on a gray pulsing placeholder and never resolves:** the backend is
  probably down. Reload once; if it still doesn't resolve within ~10 seconds, treat it as broken.
- **The Registry section shows an amber box saying "Backend unreachable — is the API running?"
  instead of the cards:** this is the app's intentional honest behavior when it truly cannot reach
  the backend — it is not a client-side bug, but it does mean the backend needs to be started/fixed
  before the rest of this guide can be completed.
- **The Champion box shows anything other than "v1" / "default":** stop and report this — the
  champion should never change without an explicit, separately-audited promotion elsewhere in the
  system.
