# Phase goal-clean_slate-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-clean_slate-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend rebuilt fresh and running at `http://localhost:3301` (this iteration requires
  clearing the Next.js build cache first — `rm -rf apps/frontend/.next` — then restarting,
  so you are not looking at a stale cached build)
- Backend running at `http://localhost:8301`
- No login is required — the app has no auth
- No seed data needs to be created — this guide only reads pre-existing, already-registered
  fixture data (AAPL bars as-of `2026-06-22T21:00:00Z`, existing Case Studies rows)

**Why this check matters:** this iteration deleted 5 dead backend classes and added one
backend test — it shipped **zero** UI changes. Every step below should look and behave
exactly as it did before this iteration. You are not looking for something new; you are
confirming nothing broke.

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** Page loads with the text "No ticker watched" visible. Top navigation shows exactly two items: "Cockpit" and "Structure".

2. Type "SIM-BUYER" into the ticker field (placeholder "Ticker e.g. SIM-BUYER"), then click the "Watch" button
   - **Expect:** The text "Buyer Control" appears on the page.

3. Click the 2nd button inside the "Tape bar size" control (next to the ticker controls)
   - **Expect:** The caption "Logical 30s bars built live from the tape." appears.

4. Click the "Stop watching" button
   - **Expect:** The page returns to showing "No ticker watched".

5. Click "Structure" in the top navigation
   - **Expect:** Page navigates to `http://localhost:3301/structure`.

6. Type "AAPL" into the Symbol field (placeholder "e.g. PG") and "2026-06-22T21:00:00Z" into the As-Of field (placeholder "2026-06-09T21:00:00Z"), then click "Load"
   - **Expect:** The text "300.11" appears on the page.

7. Click any row in the Case Studies table
   - **Expect:** A case-study drill-in panel opens showing that case's detail.

8. Scroll down to the Edge Report section
   - **Expect:** Either populated data cells, or the exact text "Edge report not computed yet." next to a visible "Compute" button. Either is correct — what matters is that it is NOT a blank section or an error/crash.

9. Look at the top navigation bar one final time
   - **Expect:** Still exactly two items — "Cockpit" and "Structure". No "Journal", "Analytics", "Studies", "Monitor", or any other extra link has appeared.

---

## What "Working Correctly" Looks Like

- Steps 1–7 look and behave identically to how this product has always behaved — a
  simulated ticker can be watched and stopped, and Structure levels can be loaded and
  drilled into, with no visual difference from before this iteration.
- The top navigation shows exactly "Cockpit" and "Structure" throughout the whole walk
  (step 1 and step 9) — this is the single most important confirmation for this specific
  iteration, since it is the direct evidence that the dead-code cleanup did not resurrect
  any deleted feature's link.

## If Something Looks Wrong

- **A third nav item appears (e.g., "Journal", "Analytics", "Studies")**: this is a
  regression this iteration was supposed to prevent — report it immediately, do not
  dismiss it as cosmetic.
- **Blank page / error screen on either `/` or `/structure`**: confirm the backend process
  (the terminal running `uvicorn` on port 8301) has not crashed or printed a traceback.
- **`/structure` Load does not show "300.11" for AAPL / 2026-06-22T21:00:00Z**: confirm the
  frontend was actually rebuilt fresh for this test (`rm -rf apps/frontend/.next` then
  restart) — a stale cached build is a known way this check can falsely appear broken.
- **Edge Report section is completely blank (neither cells nor the "not computed yet"
  message, nor a Compute button)**: this is a genuine failure, not an acceptable honest
  state — report it.
