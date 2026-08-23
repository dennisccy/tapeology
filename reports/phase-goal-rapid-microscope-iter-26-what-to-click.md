# Phase goal-rapid-microscope-iter-26 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-26
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable (no login required — this app has no auth gate)
- No seed data required — the two sections below read whatever dataset/study state is already
  registered on the running instance

---

## Verification Steps

This iteration is a **backend speed + cleanup change with zero intended UI difference**. You are not
looking for anything new — you are confirming the page still looks and reads exactly as it did before,
just faster on a repeat view of the same data.

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** Page loads, the "Desk" link in the top nav bar is highlighted as active, no error
     screen

2. Scroll down until you see the "Microscope Readiness" section header (a small `▸` marker to its
   left means it's collapsed)
   - **Expect:** Section header is visible and reads exactly "Microscope Readiness"

3. Click the "Microscope Readiness" section header
   - **Expect:** The section expands (marker flips to `▾`) and shows a "Corpus Totals" table
     (Distinct symbol-days, Distinct datasets, RTH minutes covered, Session-equivalents, Referee
     tick-gate) followed by a "Sealed Tranche (Aggregate Only)" table with a row labeled "Joinable
     corpus — band touches" showing either a number or the text "not enumerated"

4. Click the "Microscope Readiness" header again to collapse it, then click it a third time to
   re-expand
   - **Expect:** The "Joinable corpus — band touches" value is exactly the same number as it showed
     in step 3 — this proves the new caching change did not alter what's displayed, only how fast it
     re-appears

5. Scroll down further and click the "Scout Ledger" section header
   - **Expect:** The section expands and shows a line reading "Ledger chain verification: ok"
     followed by one or more pilot-study family blocks, each with a header like
     "`<family-name>` (root `...`) — `N` variants tried"

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** Page reloads cleanly to the same `/desk` URL; both "Microscope Readiness" and "Scout
     Ledger" collapse back to their default closed state (this is normal — sections start closed on
     every fresh load, not just this one)

---

## What "Working Correctly" Looks Like

- The "Joinable corpus — band touches" number in Microscope Readiness never changes between repeated
  expand/collapse clicks on the same page load
- Both "Microscope Readiness" and "Scout Ledger" expand and show data with no error banner, no blank
  panel, and no console errors
- Everything on the page looks exactly like a screenshot taken before this iteration's code was
  deployed — this iteration's entire goal is "no visible difference, just faster"

## Common Issues

- **Blank page / error screen**: Check that the backend is running and reachable (e.g.
  `curl http://localhost:8301/docs` should return HTTP 200)
- **"Microscope Readiness" or "Scout Ledger" shows an "unavailable" panel instead of data**: This
  means the readiness/scout endpoint itself failed to respond — check the backend logs; it is not
  expected behavior from this iteration's change
- **Band-touch number changes between clicks in step 4**: This would be a real regression — the whole
  point of the new cache is that the second read of the same data returns the identical value as the
  first
