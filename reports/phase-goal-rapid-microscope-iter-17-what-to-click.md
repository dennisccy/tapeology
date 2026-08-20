# Phase goal-rapid-microscope-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-17
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
- No login required, no seed data required — this round adds no new feature and changes nothing
  visible; you are confirming the already-shipped product still works after an internal backend
  rewrite (the sealed-verdict computation moved to a new owner module), not trying out something
  new.
- Do not click "Run Screen" (in Scout Ledger) or "Run Walk-Forward" (in Walk-Forward) during this
  guide — both start a real backend computation that can run 25+ minutes with no reliable fast
  cancel, well outside a 5-minute check.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with no error banner. The heading reads "Desk". Every section is
     collapsed with a closed "▸" arrow.

2. Open your browser's DevTools console (press F12, then click the "Console" tab) and leave it
   open for the rest of this guide
   - **Expect:** No red errors so far.

3. Click the "Microscope Readiness" section header, then "Scout Ledger", then "Walk-Forward",
   then "Validation Vault", one at a time
   - **Expect:** Each expands cleanly (arrow becomes "▾") showing either real data or an honest
     "No ... recorded" empty state. **No new red console error appears after any of these
     clicks** — this is the single most important check in this guide, since this round rewrote
     the backend module these sections' data ultimately traces back to.

4. Click "Referee Registry", then "Referee Adjudications", then "Referee Runs"
   - **Expect:** Each of the three expands to show its own content, no error, no new console
     error.

5. Refresh the page (press F5 or Cmd+R)
   - **Expect:** Every section you opened is back to the closed "▸" state — sections always start
     collapsed on reload, on purpose.

6. Navigate to `http://localhost:3301/structure`
   - **Expect:** Page loads with no error banner.

7. Type a symbol (e.g. `AAPL`) into the "Symbol" field, type an as-of date/time into the "As-of
   (ET)" field, then click "Load"
   - **Expect:** No error banner appears; a table of price/structure bands renders (or an honest
     "no bands" result — either is fine, a crash is not).

8. Navigate to `http://localhost:3301/`
   - **Expect:** Page loads with no error banner. The mode selector reads "Simulated".

9. Type `SIM-BUYER` into the ticker field, then click "Watch"
   - **Expect:** The chart renders and the live tape begins updating.

10. Navigate directly to `http://localhost:8301/research/desk/micro/graduation` in the address
    bar
    - **Expect:** The page shows raw JSON starting with `{"families": [...` — not a browser error
      page, not a 500. This is the one piece of code this round actually changed; it has no button
      or page anywhere else that shows it, so this direct URL is the only way to see it working.

---

## What "Working Correctly" Looks Like

- Every `/desk` section (Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, and
  all three Referee sections) expands with zero new red console errors — this round moved an
  internal computation to a new backend module, so a clean console after every click is the pass
  signal, not a new button or new data appearing.
- `/structure` and `/` (Cockpit) look and behave exactly as they did before this round.
- The direct `http://localhost:8301/research/desk/micro/graduation` URL returns valid JSON, never
  an error page.

## If Something Looks Wrong

- **A section shows an amber box reading "Backend unreachable — is the API running?"**: the
  backend isn't running. Check with `curl http://localhost:8301/health` — it should return
  `{"status":"ok"}`.
- **A red console error or hydration warning appears after expanding any section**: note the exact
  section and the exact error text and report it — this round's actual code change lives in the
  backend module these sections' Scout/Walk-Forward/Vault data trace back to, so a new console
  error here is the most likely place a real regression would show up.
- **Walk-Forward looks different from what you expected (empty vs. showing a real fold)**: this is
  a known, already-documented condition — the dev handoff records that this round's replay found
  pre-existing data drift in the real store's Walk-Forward data, unrelated to this round's code.
  Either an empty state or real fold data is fine here; only a crash or blank panel is a problem.
- **The `http://localhost:8301/research/desk/micro/graduation` page shows a 500 error or an
  unparseable page instead of JSON**: this IS a real regression — it is the one endpoint this
  round's code changes actually touch.
- **The Cockpit chart looks frozen/static**: this is a known quirk of some headless/background-tab
  browser setups (`visibilityState: "hidden"`), not necessarily a real bug — confirm the page is
  the active, visible browser tab before reporting it as broken.
- **You accidentally clicked "Run Screen" or "Run Walk-Forward"**: this is safe but leaves a real
  computation running in the backend for a while. You can leave it running (it doesn't corrupt any
  data) or restart the backend process to stop it early.
