# Phase goal-playbook-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-playbook-iter-8
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Scoped fixture backend running at `http://localhost:8301` — start it with:
  `bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh /tmp/playbook-iter8-fixture-qa 8301`
  (never point this check at the operator's real backend/`.data/` store)
- Frontend running at `http://localhost:3301`, built fresh after `rm -rf apps/frontend/.next`
- No login required

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads, no blank screen or error page.

2. Scroll to the very bottom of the page
   - **Expect:** A new bordered panel titled "Playbook Evidence" is visible directly below the
     "Backscan" panel. It opens with a paragraph of plain-language text describing what was
     measured (starts with "every recorded playbook signal at ONE input signature...").

3. In the "Playbook Evidence" panel's main table, find a row for setup `open_high_break`, side
   `long`, measure `5m`
   - **Expect:** The Signal "n" column shows a number 12 or higher, and the median/p25/p75/mean
     columns to its right show real numbers (not blank).

4. In the same table, find a row for setup `open_high_break`, side `long`, measure `1h`
   - **Expect:** The Flag column on the far right shows an amber badge reading "low n" — but the
     median/p25/p75/mean columns still show numbers, not blanks. Thin data is tagged, not hidden.

5. Scroll down a little further to the "Invalidation breaches" heading
   - **Expect:** A second table appears with columns Setup / Side / Horizon / Breached / Total,
     showing real numbers in the last two columns.

6. Scroll back up to the "Backscan" panel and find the field labeled "Backscan from day"
   - **Expect:** An input box with placeholder `yyyy-MM-dd`.

7. Click into "Backscan from day", clear it, and type `2026-06-2` (one digit short of a full date)
   - **Expect:** No red error text appears below the field. The plan preview shows "0 dates planned
     · 0 missing at the current signature." — never a crash or raw error.

8. Scroll up to the "Playbook Signals" section and find its date field, then type `2026-06-22`
   - **Expect:** A row appears with setup "Capitulation" for symbol "DECOR". Click on that row.

9. After clicking the DECOR row
   - **Expect:** The expanded row shows the text "euphoria recent" — the same detail this row has
     always shown; only the underlying automated test that checks this changed this iteration, not
     the row itself.

10. Refresh the page (F5) and scroll back to the "Playbook Evidence" panel
    - **Expect:** The exact same "low n" cell from step 4 and well-populated cell from step 3 are
      still there with the same numbers — confirms the data is read from storage, not randomly
      regenerated on each load.

---

## What "Working Correctly" Looks Like

- The "Playbook Evidence" panel appears below "Backscan" with a text disclosure paragraph, a wide
  data table (Setup/Side/Measure + Signal columns + Baseline columns + Flag column), and an
  "Invalidation breaches" table beneath it.
- At least one table row shows the amber "low n" badge while still displaying full numeric detail.
- Typing a half-finished date into the Backscan "from day" box never produces a raw error — only a
  clean "0 dates planned" message.

## Common Issues

- **Blank page / error screen on `/desk`**: Check the scoped backend is running
  (`curl http://localhost:8301/research/desk/playbook/evidence` should return JSON, not a
  connection error).
- **"Playbook Evidence" panel shows an amber "could not be loaded" box**: The backend is
  unreachable or was pointed at the wrong port — confirm the frontend was started with
  `CHAIN_BACKEND_PORT=8301` and the scoped backend script is still running.
- **No "low n" badge anywhere in the table**: Confirm the scoped fixture rig was started against a
  fresh root (the seeded evidence corpus lives at `2026-06-25`; an unrelated/older fixture root may
  not have the thin-cell composition this check relies on).
- **Capitulation/Range Trade/Double Top rows missing on 2026-06-22**: Confirm you are pointed at the
  scoped fixture rig, not the operator's real backend — these symbols only exist in the seeded
  fixture data.
