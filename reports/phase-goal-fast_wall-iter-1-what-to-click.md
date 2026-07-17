# Phase goal-fast_wall-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-fast_wall-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`.
- Backend running at `http://localhost:8301`. No login is required anywhere in this app.
- No seed data needed — the running backend already has 18 datasets registered.

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser.
   - **Expect:** The page loads within a couple of seconds; the heading "Structure" is visible; no
     blank white page or error screen.

2. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge
   Report". Do **not** wait for "Case Studies" to finish loading first — that section is unrelated
   to this update and can take several minutes on its own; just scroll past it.
   - **Expect:** A pulsing gray placeholder box appears under the Edge Report caption within the
     first couple of seconds — this confirms the page started checking for a report automatically.

3. Wait up to about 1 minute, watching only the Edge Report panel (don't touch anything else).
   - **Expect:** The placeholder resolves to ONE of two honest, calm messages — either is correct:
     - An amber box headlined **"Edge report not computed yet."** with one explanation sentence
       beneath it (the expected outcome on this environment as of when this guide was written), or
     - A box headlined **"No edge-report cells yet."** (also correct — it just means someone
       already generated the report and it happened to come back empty).
   - **Broken looks like:** the panel is still showing the pulsing placeholder after a full minute,
     or the browser tab stops responding. Before this update, this exact situation could pin the
     backend at ~98% CPU for hours — that is precisely the bug this update fixes.

4. If you saw "Edge report not computed yet." in step 3, look for any button or input field inside
   that amber box.
   - **Expect:** There is none — just the headline and one sentence of plain-English explanation.
     A "Compute" or "Run report" button does not exist yet anywhere on this page (that's planned
     for a later update, not this one).

5. Reload the page (press F5 or Cmd+R).
   - **Expect:** The Edge Report panel briefly shows its loading placeholder again, then resolves
     to the same message from step 3 within about a minute — it must never take longer the second
     time.

6. Click "Cockpit" in the top navigation bar.
   - **Expect:** The page navigates to `http://localhost:3301/`; the top navigation bar still shows
     5 items — Cockpit, Journal, Studies, Performance, Structure; the page loads with no error.

---

## What "Working Correctly" Looks Like

- The Edge Report panel on `/structure` always finishes loading within about a minute — it never
  spins forever and it never freezes the rest of the page or the browser tab.
- Whichever message it shows ("Edge report not computed yet." or "No edge-report cells yet.") is
  calm, plain-English text in an amber box — never a raw error, a stack trace, or a blank space.
- Everything else on `/structure` (Tradable Map, Case Studies, Fetch from Yahoo Finance) and the
  rest of the navigation bar look exactly as they did before.

## If Something Looks Wrong

- **Edge Report panel still pulsing/loading after 2+ minutes:** this is the exact regression this
  update was built to prevent — note how long you actually waited before giving up.
- **Blank white page anywhere on `/structure`:** check the backend is running —
  `curl http://localhost:8301/health` should return `{"status":"ok"}`.
- **You see a full data table immediately instead of either honest message:** that's also fine —
  it means a report was already computed and it has real rows in it; not a failure.
- **You see the message "Backend unreachable — is the API running?"** instead of either expected
  message: the backend process itself is down or unreachable — this is a different, honest
  degraded state, not the same thing as "not computed yet." Confirm the backend is running and
  reload.
