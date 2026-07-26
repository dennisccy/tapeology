# Phase goal-desk-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301` (backend at `http://localhost:8301`) — no login required, this product has no auth.
- At least one universe snapshot should already be registered. If none is registered yet, that's fine too — clicking "Run Screen" in step 4 below will correctly show a red error instead of computing (see "If Something Looks Wrong"); this is expected behavior, not a bug.

---

## Verification Steps

1. Open `http://localhost:3301` in your browser
   - **Expect:** The Cockpit page loads with no error screen. The top navigation bar reads **"Cockpit · Structure · Desk"** — three links.

2. Click **"Desk"** in the top navigation bar
   - **Expect:** The page navigates to `http://localhost:3301/desk`; a heading reading **"Desk"** appears near the top; "Desk" is now the highlighted (active) link in the nav.

3. Look at the main panel on the page
   - **Expect:** One of two things, both correct: (a) the text **"Desk screen not computed yet."** with two enabled buttons, "Run Screen" and "Top-up" — meaning no screen has run yet on this backend, or (b) a populated page with four stacked panels titled "Provenance", "Briefing", "Skipped Members", and "Screen History" — meaning a screen already ran previously.

4. Click the **"Run Screen"** button
   - **Expect:** The button becomes disabled and its text changes to **"Computing…"**. Within a few seconds, a line with a small pulsing dot appears reading something like **"3 / 101 members"**, with the first number counting up over time.

5. Click the **"Cancel"** button that appeared next to the progress line
   - **Expect:** The Cancel button's text changes to **"Cancelling — finishing the current member…"**, and shortly after, the text **"Screen compute cancelled — nothing was recorded this run."** appears. The "Run Screen" button returns to its normal, enabled state.

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The page reloads to the same kind of state you left it in (empty-state panel, or a populated briefing) — no crash, no blank white page, no error overlay.

7. Navigate to `http://localhost:3301/structure`, type **"AAPL"** into the "Symbol" field and **"2026-06-22T21:00:00Z"** into the "As-of (UTC, ISO-8601)" field, then click **"Load"**
   - **Expect:** The "Tradable Map" panel renders a resistance band whose range reads **"300.11–302.2"** — this is the project's long-standing pinned regression example; seeing it confirms the existing `/structure` page still works exactly as before this phase.

8. Navigate back to `http://localhost:3301/`
   - **Expect:** The Cockpit page still loads normally — unaffected by the new Desk page.

---

## What "Working Correctly" Looks Like

- The top nav shows exactly three links — "Cockpit", "Structure", "Desk" — on every page, in that order, never more or fewer.
- Clicking "Run Screen" or "Top-up" visibly disables the button, relabels it, and starts a live-updating progress line with a pulsing dot — it never just sits there doing nothing after the click.
- Cancelling a run always ends with an explicit "...cancelled — nothing was recorded..." message, never a silent freeze.

## If Something Looks Wrong

- **Red error appears immediately after clicking "Run Screen"**, mentioning "no universe snapshot is registered": this is CORRECT behavior when no universe has ever been fetched on this backend — not a bug. A universe must be registered first via the CLI/API (outside this guide's scope).
- **Blank page or error overlay at `/desk`**: confirm the backend terminal (`scripts/dev.sh`) shows no errors and is listening on port 8301; also confirm the frontend was rebuilt after this phase's changes (`rm -rf apps/frontend/.next` then restart) — a stale build is a known trap the first time a new page ships.
- **Nav shows fewer than three links, or the text "navigation unavailable — backend unreachable"**: the backend is not reachable from the frontend — restart it.
- **Progress line stuck at "0 / 0" or never changes**: the backend job may have failed silently — check the backend terminal for errors.
