# Phase goal-rapid-microscope-iter-28 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-28
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable
- No login required
- Before this check, `apps/frontend/.next` should have been rebuilt fresh (`rm -rf
  apps/frontend/.next` then rebuild) so the new caveat markup is actually served

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with the heading "Desk" at the top and the text "Playbook
     Signals" visible; no blank page or error message

2. Scroll down until you see a section header labeled "Referee Registry" and click it
   - **Expect:** The section expands (the arrow next to the label flips from "▸" to "▾") and new
     content appears below it, including a "Registered Hypotheses" heading

3. Keep scrolling within the newly-expanded section until you reach a sub-heading labeled
   "Strategy Family" (it sits below a "Playbook Family" sub-heading, both under an "Evidence
   Readiness" heading)
   - **Expect:** A small table showing "Datasets", "Train / Holdout", and "Trades" rows with
     numbers

4. Read the text directly below that table (below one gray line of text about tick-gate status,
   above a bulleted list of caveats)
   - **Expect:** A new sentence is visible, reading exactly: "Legacy Referee readiness metric —
     seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope
     shards and must not be used as the canonical Rapid-Microscope readiness count."

5. Refresh the page (F5), then repeat steps 2–3
   - **Expect:** The same disclosure sentence from step 4 still appears in the same place — this
     confirms it is static page copy, not something that only appeared once by accident

6. Scroll up to the "Playbook Signals" section near the top of the page and confirm it still
   shows its usual controls (date input, signal table) unchanged
   - **Expect:** No visual difference from before this change — the Playbook Signals section has
     nothing to do with this iteration

7. Navigate to `http://localhost:3301/structure`
   - **Expect:** The page loads normally with "Tradable Map" visible — the Structure page is
     completely unaffected by this iteration

---

## What "Working Correctly" Looks Like

- The new disclosure sentence appears exactly once, in exactly one place: beside the Referee
  Registry's "Strategy Family" Datasets/Trades figures on `/desk`, styled as small gray text
  matching its neighboring caveat lines (not bold, not colored, not in its own box)
- Every other number, table, and section on `/desk`, `/`, and `/structure` looks and behaves
  exactly as before

## If Something Looks Wrong

- **Caveat sentence missing entirely**: make sure you actually clicked "Referee Registry" to
  expand it — the section starts collapsed on every page load by design (not a bug)
- **Caveat sentence present but reworded/truncated**: check that the frontend was rebuilt from a
  clean `.next` cache (`rm -rf apps/frontend/.next`) before this check — a stale build can serve
  old page markup
- **Blank page / error screen anywhere**: check that the backend is running and reachable (e.g.
  `curl http://localhost:8000/health` from a terminal)
