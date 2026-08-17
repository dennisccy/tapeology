# Phase goal-rapid-microscope-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-6
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

**This is a regression pass, not a new-feature walkthrough.** This iteration shipped zero frontend
changes — two backend Python files only. `Frontend Present: yes` is declared solely to force the
browser-testing lane to actually run this time (it silently skipped twice in a row before this).
So instead of clicking through something new, these steps re-confirm the product's existing,
already-shipped surfaces still work — which is exactly what this iteration needs proven, since the
browser lane hasn't had a real run in three tries.

---

## Prerequisites

- Backend running at `http://localhost:8301`, pointed at the store-scoped rig (not the real
  `.data/datasets` store)
- Frontend running at `http://localhost:3301`, ideally after a clean rebuild
  (`rm -rf apps/frontend/.next` then restart) to rule out a stale build
- No login required

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with the heading "Playbook Signals" visible, no error banner, no
     blank screen

2. Scroll to the very bottom of the page and click the "Microscope Readiness" section header
   - **Expect:** A "Corpus Totals" table appears showing "Distinct symbol-days: 12" and "Distinct
     datasets: 18", followed by a "Legacy Tick Shards" table listing 18 rows. Every row's "Split
     provenance" column reads `hand_assigned` and its "Exposure state" column reads `exploratory`
     — real data, not a placeholder or an empty table

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
- The two "honest empty state" sections (Referee Adjudications, Referee Runs) show their expected
  "no ... yet" sentences rather than an error message — an empty state here is correct, not a bug
- Nothing above should look different from prior iterations — this pass exists to prove the
  product is unchanged, not to find something new

## Common Issues

- **Blank page / error screen on `/desk`, `/`, or `/structure`**: check the backend is running and
  healthy — `curl http://localhost:8301/health` should return `{"status":"ok"}`
- **Microscope Readiness table is empty or shows 0 shards**: the frontend is likely pointed at the
  wrong backend — it must be the store-scoped rig, not the real `.data/datasets` store, which this
  seeding fix does not populate with tick datasets
- **Step 6's band text ("300.11–302.2") doesn't appear**: try a hard refresh after confirming
  `apps/frontend/.next` was rebuilt clean — a stale cached build can mask a working backend
- **Nothing on this list is about a new button or new page** — if you're looking for one, there
  isn't one this iteration; that is expected, not a gap
