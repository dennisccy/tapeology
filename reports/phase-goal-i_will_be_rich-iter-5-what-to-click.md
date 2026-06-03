# Phase N — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:3650`
- No login or seed data required — the SIM-* tickers drive everything

---

## Verification Steps

<!-- The app is a single cockpit page. You "watch" a ticker by typing it into the top-bar -->
<!-- Ticker field and clicking the green "Watch" button. Updates arrive live — do NOT reload. -->

1. Open `http://localhost:3650` in your browser
   - **Expect:** "Tapeology" wordmark top-left, a "Ticker e.g. SIM-BUYER" field with a green "Watch" button, and a status dot labeled "idle" top-right. No error banner.

2. Type `SIM-BIDABS` into the Ticker field and click the green "Watch" button
   - **Expect:** Top-right dot goes amber "connecting" then emerald "live"; the six cockpit panels start populating.

3. Wait ~15 seconds (do NOT reload) and read the "Tape State" panel
   - **Expect:** Headline reads **Bid Absorption** in amber (orange-gold), with an amber confidence bar and a Confidence number clearly above 0. It must NOT say "Seller Control" or "Unclear".

4. Read the "Features" panel, below the "Large prints" row
   - **Expect:** Three new rows — **Absorption score**, **Bid refresh score**, **Ask refresh score** — each a 3-decimal slate (grey) number. "Bid refresh score" reads near 1.000.

5. Read the "Event log" panel
   - **Expect:** A line like "Large sell print absorbed" and a line like "Bid refreshing at 100.00" (a real number), alongside "Tape state changed to bid_absorption".

6. Type `SIM-ASKABS` into the Ticker field, click "Watch", wait ~15s
   - **Expect:** Tape State headline reads **Ask Absorption** in amber (NOT "Buyer Control"); "Ask refresh score" reads elevated.

7. Type `SIM-BUYER` into the Ticker field, click "Watch", wait ~15s
   - **Expect:** Tape State headline reads "Buyer Control" in green (NOT amber, NOT "Ask Absorption"); the dot stays emerald "live" — regression check passes.

8. Re-watch `SIM-BIDABS`, then leave the tab open until the bounded stream ends (~30–60s)
   - **Expect:** Once the stream exhausts, the top-right dot turns rose with label "closed" — it does NOT stay a false "live".

---

## What "Working Correctly" Looks Like

- Two amber absorption headlines that you previously could never reach: "Bid Absorption" (SIM-BIDABS) and "Ask Absorption" (SIM-ASKABS).
- Three new slate Features rows justify the call, with the refresh score near 1.000.
- The status dot tells the truth — emerald "live" while streaming, rose "closed" when the stream ends.

## Common Issues

- **Blank page / error screen**: Confirm the backend is up — `curl http://localhost:8000/health` should return OK.
- **Headline stuck on "Warming up — collecting tape data…"**: Wait longer; absorption needs warm-up before it resolves. Do not reload (reloading restarts warm-up).
- **State reads "Seller Control" for SIM-BIDABS**: Keystone failure — the absorption gate is misrouting. Flag immediately.
- **Dot stays "live" after the stream clearly ended**: The stream-status rewire regressed — flag it.
