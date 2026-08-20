# Phase goal-rapid-microscope-iter-21 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-21
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8301` and frontend at `http://localhost:3301`, both
  against the scoped QA fixture backend (`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh <fresh-root> 8301`,
  paired with `CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh`) —
  never the real `.data/` store.
- No login required.
- Use a **freshly launched** `$ROOT` for this walk-through — steps 6–9 below permanently populate
  that backend's Scout ledger, which would otherwise break the separate J-10 golden-replay
  expectation of "No candidates ledgered." on the same backend instance.
- A terminal with `curl` available (steps 4–5 call the backend API directly — there is
  intentionally no UI button for this yet).

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** Page loads, the text "Playbook Signals" is visible, no blank/error screen

2. Click "Microscope Readiness" to expand it
   - **Expect:** Section expands; a row labeled "Joinable corpus — band touches" is visible,
     showing either a plain number or the text "not enumerated" (never blank)

3. Click "Scout Ledger" to expand it
   - **Expect:** Section expands; the "No candidates ledgered." message is showing (confirms you
     are on a fresh backend before triggering anything)

4. In your terminal, run:
   `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"delta_divergence_pilot"}'`
   - **Expect:** Response is `{"state":"running","run_id":"<id>"}`

5. Wait about 15–30 seconds, then run:
   `curl -s http://localhost:8301/research/desk/micro/scout/compute`
   - **Expect:** The `"state"` field now reads `"completed"` (re-run the command if it still says
     `"running"`)

6. Refresh the browser page (press F5 or Cmd+R), then click "Scout Ledger" again to re-expand it
   - **Expect:** The "No candidates ledgered." message is GONE; at least one family block is
     visible with a "Ledger chain verification: ok" line above it

7. Find the trial row whose Feature cell starts with `divergence_at_level_bearish`
   - **Expect:** That cell reads exactly `divergence_at_level_bearish / threshold (band_touch)` —
     the `(band_touch)` part in parentheses is this iteration's actual visible change

8. Find the row immediately below it, sharing the same candidate ID
   - **Expect:** That row's Feature and Horizon columns both show `—` (a dash), and its Decision
     column reads `insufficient_n` — this is the honest walk-forward eligibility refusal

9. Search the whole `/desk` page (Ctrl+F / Cmd+F) for the text `delta_divergence_pilot`
   - **Expect:** Zero matches — confirms there is still no on-screen button or label for this new
     capability; it is reachable only the way you just used it, via the API in step 4

10. Click the shipped "Run Scout" button itself (the pre-existing control, not the curl call)
    - **Expect:** It still runs the ORIGINAL default grid — any new row it produces has NO
      `(band_touch)`/`(playbook_signal)` suffix in its Feature cell, because that button never
      selects the pilot grid

---

## What "Working Correctly" Looks Like

- Microscope Readiness shows a real number (or the honest "not enumerated" text) instead of a
  placeholder, on every page load, without needing the curl trigger.
- After the curl-triggered compute completes, the Scout Ledger table on `/desk` shows a candidate
  row explicitly labeled `(band_touch)` — proof the new structure-conditioned research path
  actually ran and rendered, not just a backend log line.
- The walk-forward floor-check appears as its own honest row (dashes + `insufficient_n`), never
  silently dropped and never a fabricated pass.
- Nothing about the pilot grid is clickable anywhere on the page — it is opt-in via the API only.

## Common Issues

- **Curl step returns `{"state":"refused","reason":"already_running"}`**: another Scout compute is
  already in flight on this backend process — wait for it to finish (poll step 5's command) and
  retry step 4.
- **Scout Ledger still says "No candidates ledgered." after step 6**: the compute may not have
  reached `"completed"` yet — re-poll step 5's curl command; also confirm you refreshed the page
  (Scout Ledger only re-fetches on first section expand per browser session, not automatically).
- **Band-touch count in step 2 reads `0`**: expected and correct on a fresh fixture backend with
  no pre-computed wall map for its seeded symbol/dates — this is an honest zero, not a bug.
- **Blank page / error screen**: check that the backend is actually reachable —
  `curl http://localhost:8301/research/desk/micro/readiness` should return JSON, not a connection
  error.
