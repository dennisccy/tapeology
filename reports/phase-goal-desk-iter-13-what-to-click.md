# Phase goal-desk-iter-13 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-13
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- This iteration shipped **zero product/application code changes** — the `/desk` page looks and behaves exactly as it has since iteration 11. This guide re-verifies that the already-shipped "Top-up Runs" panel genuinely shows accumulated run history, not just its empty placeholder, and that nothing else on the page broke.
- The iteration-13 scoped evidence rig must be running: frontend at `http://localhost:3301`, backend at `http://localhost:8301`. This is a **dedicated evidence rig for this iteration**, not the app's usual `:3000`/`:8000` — do not substitute those ports.
- No login required.
- If the rig is not responding, restart it with the exact recipe in `docs/handoffs/goal-desk-iter-13-dev.md` ("Live scoped processes left running for downstream lanes") — it restarts against the same on-disk data, nothing is lost.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** the "Desk" page loads; the top nav shows both "Cockpit" and "Desk", no error page

2. Scroll all the way to the bottom of the page
   - **Expect:** a section titled "Top-up Runs" — the last section on the page

3. Look at the run history table in that section
   - **Expect:** 3 rows, reading (top to bottom) "done · 404 / 404", "cancelled · 3 / 404", "done · 404 / 404" — NOT the message "No top-up runs recorded yet."

4. Just below the table, read the "Latest run" detail line
   - **Expect:** "state: done", "404 of 404 pairs attempted", and "0 reused · 403 fetched · 1 failed" all visible together

5. Directly below that, read the "Failed pairs (1)" line
   - **Expect:** the text "AAPL 1h — no data for that window" shown in full, not cut off or replaced with a generic error

6. Scroll back to the top and skim down through the rest of the page
   - **Expect:** "Provenance" (with a "Universe snapshot" value), "Briefing" (a ranked table), and "Screen History" (a dated table) all still render normally, exactly as before — nothing missing or broken

7. Click any row in the "Screen History" table
   - **Expect:** a line reading "Viewing the recorded screen for `<that row's date>` — not the latest." appears, with a "Latest" button next to it

8. **Do NOT click the "Top-up" or "Run Screen" buttons anywhere on this page**
   - This is a warning, not an action to perform. Either button starts a real, uncontrolled run against the live keyless Yahoo adapter, which would overwrite the exact evidence (the failed-pair run) this iteration exists to prove. If you clicked one by accident, do not try to undo it — just note it in your report.

---

## What "Working Correctly" Looks Like

- The Top-up Runs table shows real accumulated history (3 rows), not the empty placeholder
- The failed pair's own error text — "AAPL 1h — no data for that window" — is legible and specific, not a generic failure message
- The rest of the `/desk` page (provenance, rankings, screen history, nav) looks exactly as it did before this iteration — nothing regressed

## If Something Looks Wrong

- **Blank page / "connection refused"**: the scoped rig may have stopped. See the restart recipe in `docs/handoffs/goal-desk-iter-13-dev.md` — restarting reuses the same saved data, nothing is lost.
- **Panel still says "No top-up runs recorded yet."**: you are likely pointed at the wrong instance. Double-check the URL is exactly `http://localhost:3301`, not the ambient app on `:3000`.
- **Want to see the "before" (empty) state too**: it cannot be reproduced live on this specific rig anymore (recording a run is a one-way, append-only action, by design). Instead open `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png` directly in an image viewer — it was captured on this same rig moments before the first run was recorded.
