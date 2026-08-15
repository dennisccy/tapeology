# Phase goal-referee-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-referee-iter-4
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Status

This iteration added **no new UI feature** — it fixed a backend statistics bug and added one
currently-invisible field to an already-shipped endpoint (details in
`reports/phase-goal-referee-iter-4-user-visible-changes.md`). There is nothing new to click.

What you ARE confirming below is that the existing app **still works exactly as before** — this
iteration's own completion criteria (TC-15) require proving that the backend-only code change
broke nothing already shipped. If every step below still looks and behaves the same as it always
has, this iteration is verified.

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend reachable — no login (this app has no auth)
- Per this iteration's own test requirement (TC-15), the frontend should have been rebuilt clean
  before this check (`rm -rf apps/frontend/.next`, rebuild, restart) — if you didn't do this
  yourself, confirm with whoever started the servers that it happened
- The backend's bar store must still contain AAPL history through 2026-06-22 (this iteration wrote
  to no data store, so this should already be true if it was true before)

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The text "No ticker watched" is visible; no error page

2. Type "SIM-BUYER" into the "Ticker" field and click the "Watch" button
   - **Expect:** The idle panel is replaced by a live tape-read view; the text "Buyer Control"
     appears

3. Navigate to `http://localhost:3301/structure`
   - **Expect:** The page loads and the text "Structure" is visible

4. Type "AAPL" into the "Structure symbol" field, type "2026-06-22 12:00:00" into the date field
   just below it, then click the "Load" button
   - **Expect:** The text "2026-06-18" appears, and the Tradable map / Levels & zones sections
     below fill in with data (not blank, not an error message)

5. Navigate to `http://localhost:3301/desk`
   - **Expect:** The page loads and the text "Playbook Signals" is visible

6. Click the "Playbook Evidence" section header (it shows a small "▸" arrow before you click it)
   - **Expect:** The arrow flips to "▾" and the section expands, showing the text
     "Built from signature"

7. Click the "Provenance" section header
   - **Expect:** The arrow flips to "▾" and the section expands with content — no red error text

8. Refresh the page (press F5 or Cmd+R)
   - **Expect:** "Playbook Signals" is still visible after reload — confirms the page didn't break

---

## What "Working Correctly" Looks Like

- All three pages (Cockpit, Structure, Desk) load instantly with no error banners or blank screens
- The Cockpit's "Buyer Control" view appears the moment you watch SIM-BUYER, same as always
- The Structure page's AAPL load on 2026-06-22 resolves to the same "2026-06-18" trading-day
  window it always has
- Every Desk section still expands and collapses the same way it did before this iteration

## If Something Looks Wrong

- **Blank page / error screen anywhere**: confirm the backend is running
  (`curl http://localhost:8301/health` — this project's pinned backend port, matching the frontend's
  `3301`) and that the frontend was rebuilt clean per the Prerequisites note above (a stale `.next`
  build cache is a known trap this project has hit before)
- **"2026-06-18" text never appears on `/structure`**: the backend's AAPL bar history may be
  missing that window — this is a data/environment issue, not something this iteration's code
  change could cause (it wrote to no data store)
- **A Desk section won't expand**: note exactly which one and capture a screenshot — this
  iteration touched none of the Desk section rendering code, so any failure here points to an
  unrelated, pre-existing environment problem
