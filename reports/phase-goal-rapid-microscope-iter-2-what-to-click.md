# Phase goal-rapid-microscope-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-2
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- The store-scoped QA rig running: backend at `http://localhost:8301`, frontend at
  `http://localhost:3301`, started via
  `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (this iteration's version —
  it now stages 2 real tick-data fixtures before backend start).
- No login is required anywhere in this product.
- A full clean rebuild done first: `rm -rf apps/frontend/.next`, then restart the frontend — a
  stale build can hide this iteration's data change.

This iteration made no code change to any page. It built a backend analysis engine that has no
button or screen yet, and it gave the isolated test rig two small real tick-data files so an
already-shipped panel could finally be screenshotted with real data. Steps 1-4 below confirm that;
steps 5-10 confirm nothing else broke.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" heading loads, no error page

2. Scroll to the very bottom of the page and click the "Microscope Readiness" section header
   - **Expect:** The section expands (arrow changes from ▸ to ▾) and shows a "Corpus Totals" table

3. Look at the "Legacy Tick Shards" table just below the totals
   - **Expect:** Exactly 2 rows appear, both showing Symbol "PG" and Feed "sip" — NOT the message
     "No tick shards recorded."

4. Look at the "Distinct symbol-days" and "Distinct datasets" rows in the Corpus Totals table
   - **Expect:** "Distinct symbol-days" reads `1` and "Distinct datasets" reads `2`

5. Open `http://localhost:3301/` in a new tab
   - **Expect:** The cockpit loads with a "Tapeology" header and a "Ticker" field, no error

6. Type `SIM-BUYER` into the "Ticker" field and click the "Watch" button
   - **Expect:** A live price chart starts rendering within a few seconds — confirms the cockpit
     still works (this iteration never touches it)

7. Open `http://localhost:3301/structure` in a new tab
   - **Expect:** The "Structure" heading, a "Symbol" field, and a "Load" button are all visible

8. Type `PG` into the "Symbol" field, click "Today", then click "Load"
   - **Expect:** The "Tradable Map" panel renders bands for PG with no error message — confirms
     `/structure` still works

9. Back on the `/desk` tab, click the "Referee Registry", "Referee Adjudications", and "Referee
   Runs" section headers, one at a time
   - **Expect:** Each one expands and shows its existing table content — nothing looks different
     from before this iteration

10. Refresh the `/desk` page (F5) and click "Microscope Readiness" again
    - **Expect:** The same 2-row PG shard table reappears immediately — confirms the data is
      actually stored, not a one-time fluke

---

## What "Working Correctly" Looks Like

- The Microscope Readiness panel shows a populated 2-row PG table instead of the old "No tick
  shards recorded." empty message.
- Cockpit (`/`), Structure (`/structure`), and every other `/desk` section still render exactly as
  before — no blank panels, no new error banners, no changed headings or labels.

## Common Issues

- **Blank page / error screen**: confirm both the backend and frontend from the store-scoped rig
  are actually running — `curl http://localhost:8301/health` should respond.
- **Microscope Readiness still shows "No tick shards recorded."**: the rig was likely started
  before this iteration's script change, or from a stale root directory left over from an earlier
  run. Restart it via the current version of
  `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` so the 2 fixture files
  actually get copied in.
- **Data still looks stale/old anywhere**: run `rm -rf apps/frontend/.next` and restart the
  frontend — this project's build can bake in stale data if skipped.
