# Phase goal-rapid-microscope-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-13
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Before you start

This iteration is **backend-only** — it fixed a vault recovery routine that has no button, page,
or menu anywhere in the app (zero production call sites; it only runs when an operator calls it
directly from Python during an incident). There is nothing new to click. This guide instead
confirms **nothing broke** in the three existing pages, since the mechanical browser check runs
regardless of whether the UI changed.

---

## Prerequisites

- Backend running at `http://localhost:8301` (check: `curl http://localhost:8301/health` returns
  `{"status":"ok"}`)
- Frontend running at `http://localhost:3301`
- No login required
- Real `.data` store present (18 registered datasets; this is the operator's normal working store —
  no seed step needed)

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The Cockpit top bar loads (a ticker input and a "Watch" button) — no blank page, no
     error banner

2. Type `AAPL` into the ticker input and click "Watch"
   - **Expect:** Within ~10 seconds, a price chart appears below the top bar and live tape data
     starts ticking in. (If the chart looks frozen in a screenshot taken by an automated/headless
     tool, that can be a known capture artifact of a backgrounded browser tab — not a real bug;
     re-check with the tab in focus.)

3. Navigate to `http://localhost:3301/structure`
   - **Expect:** A heading is visible and the "Tradable Map" panel renders band/zone data as the
     default view — no unavailable-panel message

4. Scroll down to the "Comparison" panel and click its dataset dropdown
   - **Expect:** The dropdown lists registered datasets (this store has 18) — it should NOT say "No
     datasets registered."

5. Navigate to `http://localhost:3301/desk`
   - **Expect:** The page loads with the "Playbook Signals" and "Backscan" panels visible
     immediately

6. Scroll to the very bottom of the page and click the "Microscope Readiness" section header to
   expand it
   - **Expect:** It expands (it starts collapsed on every page load) and shows a "Corpus Totals"
     table with five rows — no "could not be loaded" message

7. Just below Corpus Totals, look at the "Legacy Tick Shards" subsection
   - **Expect:** It shows the message "No tick shards recorded." This is correct and unchanged —
     this store has zero recorded tick shards, so an empty state is the right outcome, not a bug

8. Click the "Referee Registry" section header (just above Microscope Readiness) to expand it
   - **Expect:** It expands and shows its existing content (a registered-hypotheses table) exactly
     as before — this section does not touch any code this iteration changed

---

## What "Working Correctly" Looks Like

- All three pages (`/`, `/structure`, `/desk`) load and look exactly as they did before this
  iteration — same panels, same tables, same empty states
- The Cockpit chart lights up with live data once you click "Watch"
- Nothing on `/desk`'s Microscope Readiness section shows a red error message or a raw
  "could not be loaded" panel

## Common Issues

- **Blank page / error screen**: Check that the backend is running
  (`curl http://localhost:8301/health`)
- **"Microscope Readiness" or "Referee Registry" appear to do nothing when clicked**: these sections
  start collapsed on every page load by design — click directly on the section header text, not
  elsewhere in the row
- **Cockpit chart looks static in a screenshot**: if the capture tool ran the browser tab in the
  background, the live chart can visually freeze (`visibilityState: "hidden"`) — this is a known
  capture artifact, not a product defect; re-verify with the tab focused or against the backend data
- This iteration touched only backend Python (`vault.py`, `micro_routes.py`) and two test files — if
  you see ANY visual difference anywhere in the app, it is unexpected and worth flagging, since
  nothing in this iteration's diff should be able to produce one
