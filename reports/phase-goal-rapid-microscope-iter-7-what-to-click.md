# Phase goal-rapid-microscope-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-7
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

**This is a regression pass, not a new-feature walkthrough.** This iteration shipped zero frontend
changes — 6 backend Python source files and 2 test files only (confirmed via `git status`).
`Frontend Present: yes` is declared solely to let the browser-testing lane run the
required-still-passing regression set and the kept-product sentinel. So instead of clicking through
something new, these steps re-confirm the product's existing, already-shipped surfaces still work.

**One number to get right:** step 2 below expects **1 symbol-day / 2 datasets**, not the real
store's 12/18 — the test rig only ever seeds 2 fixture datasets by design. Expecting the bigger
numbers here is what made last iteration's equivalent check fail for no real reason.

---

## Prerequisites

- Backend running at `http://localhost:8301`, pointed at the store-scoped rig (start via
  `apps/backend/scripts/start_scoped_qa_backend.sh` — not the real `.data/datasets` store)
- Frontend running at `http://localhost:3301`, ideally after a clean rebuild
  (`rm -rf apps/frontend/.next` then restart) to rule out a stale build
- No login required

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with the heading "Playbook Signals" visible, no error banner, no
     blank screen. Scroll to the bottom — there is no section called "Scout Ledger",
     "Walk-Forward", or "Validation Vault" anywhere on the page. That is expected, not a gap; those
     sections are not built yet.

2. Scroll to the very bottom of the page and click the "Microscope Readiness" section header
   - **Expect:** A "Corpus Totals" table appears showing "Distinct symbol-days: 1" and "Distinct
     datasets: 2" (not 12/18 — this test rig only seeds 2 fixture datasets), followed by a "Legacy
     Tick Shards" table listing exactly 2 rows, both symbol `PG`, session date `2026-06-09`. Both
     rows' "Split provenance" column reads `hand_assigned` and "Exposure state" column reads
     `exploratory`. The table's column headers are unchanged — still Symbol, Session date, Feed,
     Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum, Split provenance,
     Exposure state, with no new column added.

3. Open `http://localhost:3301/` (the cockpit page)
   - **Expect:** The text "No ticker watched" is visible

4. Type `SIM-BUYER` into the field labeled "Ticker", then click the "Watch" button
   - **Expect:** The text "Buyer Control" appears

5. Open `http://localhost:3301/structure`
   - **Expect:** The text "Tradable Map" is visible

6. Type `AAPL` into the "Structure symbol" field, type `2026-06-22 17:00:00` into the as-of date
   field below it, then click the "Load" button
   - **Expect:** The text "300.11–302.2" appears (the pinned real support/resistance band for
     AAPL on that date)

7. Go back to `http://localhost:3301/desk`, click the "Playbook Evidence" section header, then
   type `2026-06-22` into its date field
   - **Expect:** The text "Built from signature:" appears when the section expands, and "recorded
     signals, none hidden" appears after typing the date

8. Click the "Referee Registry" section header
   - **Expect:** The text "config fingerprint 08e471b10130e1e2" appears

9. Click the "Referee Adjudications" section header
   - **Expect:** The text "No hypotheses registered" appears (an honest empty state, not an error)

10. Click the "Referee Runs" section header
    - **Expect:** The text "No evaluation runs recorded yet." appears (also an honest empty state)

---

## What "Working Correctly" Looks Like

- Every section listed above expands and shows real text or real table data within a second or
  two of clicking — never a spinner that never resolves, never a blank panel
- Step 2's Microscope Readiness table shows exactly 2 rows of real data (checksums, coverage gaps,
  fallback fractions all populated) — a small table is correct here, not a bug
- The two "honest empty state" sections (Referee Adjudications, Referee Runs) show their expected
  "no ... yet" sentences rather than an error message — an empty state here is correct, not a bug
- Nothing above should look different from prior iterations — this pass exists to prove the
  product is unchanged, not to find something new

## Common Issues

- **Blank page / error screen on `/desk`, `/`, or `/structure`**: check the backend is running and
  healthy — `curl http://localhost:8301/health` should return `{"status":"ok"}`
- **Step 2 shows "Distinct symbol-days: 12" / "Distinct datasets: 18" or 18 shard rows**: the
  frontend is pointed at the real `.data/datasets` store, not the scoped rig — restart the backend
  via `apps/backend/scripts/start_scoped_qa_backend.sh`
- **Step 2 shows 0 rows or an empty table**: the scoped rig failed to seed — check the rig's own
  startup log before assuming a product regression
- **Step 6's band text ("300.11–302.2") doesn't appear**: try a hard refresh after confirming
  `apps/frontend/.next` was rebuilt clean — a stale cached build can mask a working backend
- **Nothing on this list is about a new button or new page** — if you're looking for one, there
  isn't one this iteration; that is expected, not a gap. The only new capability this iteration
  added (a `--family tick_legacy` command-line flag) is run from a terminal, not clicked in the app.
