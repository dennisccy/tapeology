# Phase goal-rapid-microscope-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-15
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
- No login required
- No seed data required — this guide is written against the app's real, current state: Microscope
  Readiness's new sealed-tranche numbers are genuinely all zero today, the Scout ledger is
  genuinely empty, and the Walk-Forward ledger already has one real recorded sequence. All of that
  is correct and expected — you are not setting anything up.
- **Do not click "Run Screen" (in Scout Ledger) or "Run Walk-Forward" (in Walk-Forward) during this
  guide.** Both start a real computation against the live backend that can run for 25+ minutes and
  isn't reliably cancellable within a few minutes — well outside a 5-minute check.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with no error banner. Section headers "Microscope Readiness",
     "Scout Ledger", "Walk-Forward", "Validation Vault" are all visible, each with a closed "▸"
     arrow.

2. Click the "Microscope Readiness" header
   - **Expect:** It expands (arrow becomes "▾"). Below the existing "Corpus Totals" table, a NEW
     block titled "Sealed Tranche (Aggregate Only)" appears, showing "Sealed shard count: 0",
     "Sealed symbol-days: 0", "Joinable corpus — withheld (excluded): 0", and the text "No sealed
     shards recorded." — these are honest zeroes, not blank or missing values.

3. Click the "Walk-Forward" header
   - **Expect:** It expands, showing a "Fold Specs" block and at least one real sequence card (id
     starting `seq-`) with a "Sequence verdict:" line.

4. Open your browser's DevTools console (press F12, then click the "Console" tab), then click the
   small "detail" text right after "Sequence verdict:" on that sequence card
   - **Expect:** The detail box expands to show verdict JSON. **No new red error appears in the
     console, and no red "Issues" warning badge appears anywhere on screen.** (This exact click
     used to trigger a "5 Issues" warning badge — confirming it's gone is the single most important
     check in this guide.)

5. Click the "Scout Ledger" and "Validation Vault" headers
   - **Expect:** Both expand cleanly with no console errors. Scout Ledger shows "No candidates
     ledgered." (still true — the ledger is empty). Validation Vault shows "No shards recorded."
     and "No universes registered.", with no button anywhere inside it (it's read-only by design).

6. Refresh the page (press F5 or Cmd+R)
   - **Expect:** All four headers ("Microscope Readiness", "Scout Ledger", "Walk-Forward",
     "Validation Vault") are back to the closed "▸" state — they start collapsed on every page
     load, on purpose.

7. Navigate to `http://localhost:3301/structure`, then to `http://localhost:3301/`
   - **Expect:** `/structure` loads with its Tradable Map and comparison dropdown visible; `/`
     (Cockpit) loads with its chart visible. Neither page shows an error — confirms this
     iteration's `/desk`-only change didn't affect the other two pages.

8. Navigate directly to `http://localhost:8301/research/desk/micro/graduation` (note: port 8301,
   the backend — not 3301)
   - **Expect:** A raw JSON page loads (HTTP 200) containing `"families":[]` and `"message":"No
     candidates ledgered."` — confirms the Graduation feature from an earlier round still works.
     There is no button or link anywhere in the app that reaches this page; typing the URL directly
     is the only way to see it, by design.

---

## What "Working Correctly" Looks Like

- A new "Sealed Tranche (Aggregate Only)" block sits inside "Microscope Readiness", showing honest
  zero counts (not blank space) plus "No sealed shards recorded."
- Expanding a Walk-Forward sequence's "detail" toggle no longer produces a red "Issues" warning
  badge.
- Nothing on `/structure` or `/` (Cockpit) looks any different than before.

## Common Issues

- **A section shows an amber box saying the data "could not be loaded"**: the backend isn't running
  or crashed. Check with `curl http://localhost:8301/health` — it should return `{"status":"ok"}`.
- **The "5 Issues" (or similar) red badge still appears after step 4**: this would mean the
  HTML-nesting fix did not take effect — check that the frontend was rebuilt after this iteration's
  change (a stale `.next` build cache is a known cause; try `rm -rf apps/frontend/.next` and restart
  the frontend).
- **The Cockpit chart looks frozen/static**: this is a known quirk of some headless browser setups
  (`visibilityState: "hidden"`), not necessarily a real bug — confirm the page is the active,
  visible browser tab before reporting it as broken.
- **You accidentally clicked "Run Screen" or "Run Walk-Forward"**: this is safe but leaves a real
  computation running in the backend for a while. You can leave it running (it doesn't corrupt any
  data) or restart the backend process to stop it early.
- **Step 8 shows a blank page or a connection error**: double check you navigated to port `8301`,
  not `3301` — this endpoint only exists on the backend, not the frontend.
