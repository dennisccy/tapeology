# Phase goal-yahoo_fetch-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-yahoo_fetch-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start: what changed

This iteration added a keyless Yahoo Finance data fetch, but it is **backend/API-only** — there is
no new button, page, or badge to click yet (that arrives in a later iteration). So this guide is
not "try the new feature" — it is a fast check that nothing existing broke while that backend
change was made. Prioritized: (1) the one workflow most at risk of breaking (the live Cockpit
tape), (2) the one other page directly wired to the changed backend endpoint (Structure), (3) a
quick sanity pass over the rest of the app.

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login needed — the app has no authentication
- No seed data needed — step 2 below uses the app's built-in `SIM-BUYER` simulated ticker, which
  requires no historical data, credentials, or network access

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The Cockpit page loads. A "Live / Historical / Simulated" toggle is visible near
     the top-left, with "Simulated" already highlighted. The navigation bar across the very top
     shows exactly 5 links: Cockpit, Journal, Studies, Performance, Structure.

2. Click into the field with placeholder text "Ticker e.g. SIM-BUYER" and type `SIM-BUYER`, then
   click the "Watch" button next to it
   - **Expect:** The screen briefly shows "Connecting to SIM-BUYER…", then within about 10 seconds
     settles into a full grid of panels labeled Tape State, Quote, Recent Trades, Features,
     Observations, and Event Log.

3. Look at the small badge that says "feed" next to the "Watching SIM-BUYER" text near the top of
   the page
   - **Expect:** The badge reads **"Simulated"**. This is the single most important check in this
     guide — this badge must NEVER read "yahoo" or "sip" here. If it does, the backend's new
     Yahoo-vendor default has leaked into the wrong code path and stop here — that is a real
     regression, not a cosmetic issue.

4. Click "Stop" (next to "Watching SIM-BUYER"), then click "Structure" in the top navigation bar
   - **Expect:** You land on `http://localhost:3301/structure`. The heading "Structure" is
     visible, along with a "Symbol" field, an "As-of (UTC, ISO-8601)" field, and a "Load" button.
     Further down, a "Registry" section shows a "Champion" box with a strategy name.

5. Type `AAPL` into the "Symbol" field and `2026-06-05T00:00:00Z` into the "As-of (UTC, ISO-8601)"
   field, then click "Load"
   - **Expect:** Either a candlestick chart with S/R level lines and a "Confluence zones" section
     appears below, or (if `AAPL` has no recorded bars yet in this environment) an honest message
     such as "No bar series recorded for AAPL." appears in its place. Either outcome is fine — what
     matters is there is **no error banner, no blank page, and no crash**.

6. Click "Journal" in the top nav, then "Studies", then "Performance" — one at a time
   - **Expect:** Each page loads its own heading ("Journal", "Replay studies", "Performance") with
     no error banner and no blank white screen.

7. Refresh the page you're currently on (press F5 or Cmd+R)
   - **Expect:** The page reloads cleanly with the same heading and no error — confirms nothing is
     stuck in a broken client-side state.

---

## What "Working Correctly" Looks Like

- After watching SIM-BUYER on the Cockpit, the feed badge reads "Simulated" — never "yahoo"
- All 5 nav links (Cockpit, Journal, Studies, Performance, Structure) load their own page with no
  error banner
- Nothing on screen anywhere says "Yahoo" yet — that label is intentionally not built until a
  later iteration; its absence today is correct, not a bug

## If Something Looks Wrong

- **Blank page / error screen**: confirm both servers are up — frontend
  `http://localhost:3301` and backend `http://localhost:8301/health` (should return
  `{"status":"ok"}`)
- **"Watch" button stays greyed out**: make sure you typed into the field placeholder "Ticker e.g.
  SIM-BUYER" (not a different field) and that "Simulated" mode is selected in the toggle
- **Feed badge shows nothing at all**: expected before you click Watch — the badge is absent
  whenever no ticker is being watched; it should appear right after step 2 above
- **Feed badge reads "yahoo" on the Cockpit**: this is the one true regression this guide is
  designed to catch — report it immediately, it means the new bar-fetch vendor default reached the
  live/simulated tape path instead of staying confined to the bar-fetch endpoint
- **Structure page says "No bar series recorded for AAPL."**: not a bug — it just means nobody has
  fetched data for that symbol yet in this environment; the page is still working correctly
