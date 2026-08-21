# Phase goal-rapid-microscope-iter-22 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-22
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8301` and frontend at `http://localhost:3301`, both
  against a scoped QA fixture backend — never the real `.data/` store.
- No login required.
- Use a **freshly launched** backend for this walk-through — steps 2–5 below permanently populate
  that backend's Scout ledger, which would otherwise break a separate golden-replay run's
  expectation of "No candidates ledgered." on the same backend instance. If you already ran the
  deterministic replay suite against this instance, launch a new one for this guide.
- A terminal with `curl` available — steps 2 and 4 call the backend API directly; there is
  intentionally no on-screen button for this yet.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** Page loads, no blank/error screen; you can see section headers including
     "Scout Ledger" further down the page.

2. In your terminal, run:
   `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"range_wall_failed_aggression_pilot"}'`
   - **Expect:** Response is `{"state":"running","run_id":"<id>"}`

3. Wait about 15–30 seconds, then run:
   `curl -s http://localhost:8301/research/desk/micro/scout/compute`
   - **Expect:** The `"state"` field reads `"done"` (re-run the command if it still says
     `"running"`)

4. Repeat steps 2–3 with `{"grid":"capitulation_exhaustion_pilot"}` instead — POST it, then poll
   until `"state":"done"`.
   - **Expect:** Same `{"state":"running",...}` then `"state":"done"` pattern.

5. Refresh the browser page (press F5 or Cmd+R), then click "Scout Ledger" to expand it
   - **Expect:** The "No candidates ledgered." message is GONE; two new family blocks are
     visible, one headed `failed_aggression_score__band_touch__trades_20` and one headed
     `failed_aggression_score__playbook_signal__trades_20`

6. In the `failed_aggression_score__band_touch__trades_20` block, read the first trial row's
   Feature cell
   - **Expect:** It reads exactly `failed_aggression_score / threshold (band_touch)`

7. In that same family block, read the SECOND row (directly below the first, sharing its
   Candidate ID)
   - **Expect:** Feature and Horizon columns both show `—` (a dash); Decision column reads
     `killed_insufficient_n` — this is the honest "not enough evidence yet" answer, not a blank
     or a fabricated pass

8. Repeat step 7 for the `failed_aggression_score__playbook_signal__trades_20` family block
   - **Expect:** Same pattern — second row shows `—` / `—` / `killed_insufficient_n`

9. Search the whole `/desk` page (Ctrl+F / Cmd+F) for the text
   `range_wall_failed_aggression_pilot`
   - **Expect:** Zero matches — confirms there is still no on-screen button or label for either
     new study; it is reachable only the way you just used it, via the API in steps 2 and 4

10. Click the shipped "Run Screen" button itself (the pre-existing control, not the curl calls)
    - **Expect:** It still runs the ORIGINAL default grid — any new row it produces has NO
      `(band_touch)`/`(playbook_signal)` suffix and no `killed_insufficient_n` floor-check row

---

## What "Working Correctly" Looks Like

- Both new pilot studies produce a real, non-empty family block in the Scout Ledger table after
  being triggered via the CLI or the API — proof the new research path actually ran and rendered,
  not just a backend log line.
- Each new study's walk-forward floor-check appears as its own honest row (dashes +
  `killed_insufficient_n`), never silently dropped and never a fabricated pass.
- Nothing about either new study is clickable anywhere on the page — both are opt-in via the CLI
  or API only, exactly like Study 2 already was since iter-21.
- The shipped "Run Screen" button and the default grid it triggers are completely unaffected.

## Common Issues

- **Curl step returns `{"state":"refused","reason":"already_running"}`**: another Scout compute is
  already in flight on this backend process — wait for it to finish (poll step 3's/step 4's
  command) and retry.
- **Scout Ledger still says "No candidates ledgered." after step 5**: the compute may not have
  reached `"done"` yet — re-poll the relevant curl command; also confirm you refreshed the page
  (Scout Ledger only re-fetches on first section expand per browser session, not automatically).
- **Only one new family block appears instead of two**: confirm step 4's `capitulation_
  exhaustion_pilot` run actually reached `"state":"done"` before refreshing — a run still
  `"running"` will not yet have written its ledger rows.
- **Blank page / error screen**: check that the backend is actually reachable —
  `curl http://localhost:8301/research/desk/micro/readiness` should return JSON, not a connection
  error.
