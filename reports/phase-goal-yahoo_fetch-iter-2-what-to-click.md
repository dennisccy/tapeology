# Phase goal-yahoo_fetch-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-yahoo_fetch-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before you start: what changed

This iteration taught the backend to fetch five more Yahoo Finance timeframes (`1w`, `1h`, `5m`,
`1m`) plus a derived `4h`, on top of the `1d` that already worked — and to give a specific, honest
reason when it can't (instead of one generic error for every failure). None of this shipped a new
button or page: the only way to trigger a fetch today is a direct API call; the on-screen "Fetch
from Yahoo Finance" button on the Structure page arrives in a later iteration. Because of that, the
data this guide looks at is fetched once ahead of time (see Prerequisites below) — every numbered
step from there is pure clicking and typing. The guide is half "see the new data reach a real
screen" (steps 1–3) and half "confirm nothing else broke" (steps 4–7).

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login needed — the app has no authentication
- **Two bar series must already be registered before you start.** This iteration's new fetch
  capability has no on-screen button yet, so a developer sets this up once via the API, ahead of the
  click-through below:
  - AAPL `1h` bars for a recent window
  - MSFT `4h` bars for a recent window
  - If you aren't sure these already exist, ask a developer to run:
    ```
    curl -s -X POST http://localhost:8301/research/bars -H "Content-Type: application/json" -d '{"symbol":"AAPL","timeframe":"1h","start":"2026-06-25T00:00:00Z","end":"2026-07-02T00:00:00Z"}'
    curl -s -X POST http://localhost:8301/research/bars -H "Content-Type: application/json" -d '{"symbol":"MSFT","timeframe":"4h","start":"2026-06-25T00:00:00Z","end":"2026-07-02T00:00:00Z"}'
    ```
    Both should return `"feed":"yahoo"` in the response (or a 409 "already registered" message,
    which just means someone already ran this — that's fine too).

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser
   - **Expect:** The page loads with the heading "Structure", a "Symbol" field, an "As-of (UTC,
     ISO-8601)" field, and a greyed-out "Load" button.

2. Type `AAPL` into the "Symbol" field and `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)"
   field, then click "Load"
   - **Expect:** A candlestick chart appears within a few seconds, with a caption underneath reading
     "Candles: **1h** series (...)". This proves this iteration's new hourly data is now real,
     visible chart data — not just something an API returns.

3. Change the "Symbol" field to `MSFT` (leave the As-of field as it is), then click "Load" again
   - **Expect:** A new chart renders with the caption "Candles: **4h** series (...)", with visibly
     wider/fewer candles than the AAPL chart in step 2. This "4h" data isn't a direct Yahoo feed —
     Yahoo has no native 4-hour interval — the backend built it by combining real hourly bars, and
     labels it honestly as its own "4h" series rather than hiding it inside "1h".

4. Click "Cockpit" in the top navigation, type `SIM-BUYER` into the ticker field, and click "Watch"
   - **Expect:** After a few seconds, a full panel grid appears — Tape State, Quote, Recent Trades,
     Features, Observations, Event Log — with "Watching SIM-BUYER" near the top.

5. Look at the small badge that says "feed" next to "Watching SIM-BUYER"
   - **Expect:** The badge reads exactly **"Simulated"**. This is the single most important check in
     this guide — it must never read "yahoo" here. If it does, stop and report it: it would mean
     this iteration's new Yahoo bar-fetch change leaked into the unrelated live/simulated tape path.

6. Click "Journal" in the top navigation, then "Studies", then "Performance" — one at a time
   - **Expect:** Each page loads its own heading ("Journal", "Replay studies", "Performance") with
     no error banner and no blank screen.

7. Refresh the page you're currently on (press F5 or Cmd+R)
   - **Expect:** The page reloads cleanly with the same heading and no error — confirms nothing is
     stuck in a broken client-side state.

---

## What "Working Correctly" Looks Like

- Steps 2 and 3 each show a real, distinctly-labelled candlestick chart ("1h series" / "4h series")
  on the Structure page, built entirely from data fetched in the background — proving the new
  timeframes (including the derived `4h`) are genuinely usable today, even with no on-screen button
  for them yet
- The Cockpit's feed badge reads "Simulated" after watching SIM-BUYER — never "yahoo"
- Journal, Studies, and Performance all load cleanly, with no visible change from before this
  iteration

## If Something Looks Wrong

- **Structure shows "No bar series recorded for AAPL." after step 2, or "...for MSFT." after step
  3**: the Prerequisites setup step wasn't run (or didn't succeed) for that symbol — ask a developer
  to re-run its curl command and confirm the response contains `"feed":"yahoo"` before retrying.
- **Structure shows "No levels found for AAPL/MSFT as of ..." after step 2 or 3**: the fetch itself
  worked, but that specific week produced no qualifying support/resistance levels — ask a developer
  to re-fetch with an earlier `start` date (e.g. three weeks back) and reload.
- **Step 3's chart caption still says "1h" instead of "4h"**: MSFT already has an hourly (or finer)
  series registered from earlier testing, and the page correctly always shows the shortest available
  timeframe — not a bug, just re-run step 3 with a different symbol that has no prior data.
- **Feed badge in step 5 reads "yahoo" instead of "Simulated"**: this is a real regression — the new
  bar-fetch vendor default has leaked into the live/simulated tape path — report it immediately.
- **Blank page / error screen anywhere**: confirm both servers are up — frontend
  `http://localhost:3301` and backend `http://localhost:8301/health` (should return a healthy
  status).
