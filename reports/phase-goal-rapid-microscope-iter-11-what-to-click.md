# goal-rapid-microscope-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-11
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8301` (`bash scripts/start-backend.sh`)
- Frontend running at `http://localhost:3301` (`bash scripts/start-frontend.sh`)
- No login required
- No seed data required — this checks the real `.data` store as-is

**Heads up before you start:** this iteration adds **no new button, page, or field**. It is a
backend correctness fix that closes a data-privacy leak (a recorded batch of tape must stay
unidentifiable until its members are individually released). Because the real store has zero
registered "vault universes" today, the fix has **nothing to act on yet** — every check below
should show the product looking exactly as it did before this iteration. That sameness IS the pass
condition.

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** Cockpit loads, price chart shows candles, live tape panel is updating — no error
     page

2. Click "Desk" in the top navigation bar
   - **Expect:** Navigate to `http://localhost:3301/desk`; the page loads with several sections

3. Scroll to the bottom of the page, to the "Microscope Readiness" panel, and look at the "Legacy
   Tick Shards" table
   - **Expect:** A table of rows, each with a Symbol and Session Date. If you have a prior
     screenshot or memory of this table, the row count and values should be identical — this
     iteration must not add or remove a single row against the real store

4. Scroll up to the "Screen history" and "Screen Runs" sections
   - **Expect:** Both list the same screen runs you'd expect from before this iteration — no new
     blank or error panel

5. Click "Structure" in the top navigation bar
   - **Expect:** Navigate to `http://localhost:3301/structure`; the "Tradable Map" chart loads

6. Scroll down to the "Comparison" panel and click the "Dataset" dropdown
   - **Expect:** A list of dataset options opens, each reading like `AAPL · train · a1b2c3d4`.
     Count them — there should be 18 entries

7. Scroll further to the "Edge Report" and "Case Studies" panels
   - **Expect:** Both show data (or an honest "not computed yet" state) exactly as before — no new
     error

8. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The "Comparison" dataset dropdown and "Edge Report"/"Case Studies" panels reload
     with the same content — confirms nothing broke on a fresh load

9. (Optional, for a technical operator) Open a terminal and run:
   `curl -s http://localhost:8301/research/desk/micro/recorder/compute`
   - **Expect:** The JSON's `progress` object contains only these 10 fields: `chunks_total`,
     `chunks_done`, `chunks_fetched`, `chunks_reused`, `chunks_unchanged`, `chunks_failed`,
     `trades_total`, `quotes_total`, `percent_complete`, `elapsed_seconds` — and nothing named
     `outcomes`, `symbol`, `date`, or `dataset_id` anywhere in the response. This is the direct
     proof of this iteration's actual fix (there's no button for it because no panel renders this
     endpoint yet)

10. Click "Cockpit" in the top navigation bar one more time
    - **Expect:** Returns to `http://localhost:3301/`, active nav link highlights "Cockpit" — the
      3-link nav (Cockpit / Structure / Desk) is unchanged from before this iteration

---

## What "Working Correctly" Looks Like

- Nothing looks different. The Microscope Readiness shard table (step 3) and the Structure
  dataset dropdown (step 6) show exactly the same content as they did before this iteration.
- The optional API check (step 9) never shows a symbol, a date, or a dataset id — only totals.

## Common Issues

- **Blank `/desk` or `/structure` page**: check that the backend is running
  (`curl http://localhost:8301/health`)
- **Fewer rows in the "Legacy Tick Shards" table or fewer options in the "Dataset" dropdown than
  you remember**: this would mean the new withhold rule is over-hiding something in the real store
  — flag immediately. It should not happen (the real store has zero registered vault universes, so
  there is nothing new to hide).
- **The step-9 curl response contains a `symbol`, `date`, or `outcomes` field**: this is a
  regression of the exact leak this iteration fixed — flag as critical, do not dismiss as cosmetic.
- **Nav bar shows "navigation unavailable — backend unreachable"**: the frontend couldn't reach
  `GET /meta/ui-routes` — confirm the backend process is actually up on port 8301.
