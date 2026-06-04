# Phase goal-i_will_be_super_rich-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-3
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running and reachable
- For the *real* open/closed readout and the "Market is closed" panel: valid Alpaca vendor
  credentials configured in the backend env. **Without credentials**, the indicator correctly shows
  "market unavailable" — that's the honest path, not a bug (see step 4).
- Best run while the **US market is closed** (evenings / weekends) so the closed branch is visible.
  Today's date is 2026-06-04. If you run during market hours (weekday 09:30–16:00 ET), the indicator
  reads "open" and step 5 returns the honest "streaming not implemented" state instead — note that
  and skip step 5's closed-panel check.

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser
   - **Expect:** The "Tapeology" header loads with a 3-way selector "Live / Historical / Simulated";
     **Simulated** is active. There is **no** "market" pill in the top bar yet.

2. Click the **Live** button in the data-source selector (top bar)
   - **Expect:** A small pill appears in the top bar reading `market` then a status word. It may
     briefly show a grey `…` placeholder first.
   - **Broken looks like:** the pill instantly reads `open`/`closed` with no `…` flash, or no pill
     appears at all.

3. Wait ~3 seconds and read the "market" pill
   - **Expect (creds + market closed):** amber dot, `market closed — next open <time>`, where
     `<time>` is your local time like `Jun 5, 09:30 AM EDT`.
   - **Expect (creds + market open):** green dot, `market open`.
   - **Note which branch you saw.**

4. Hover the pill (only matters if you have no creds)
   - **Expect (no creds):** amber `market unavailable`, tooltip "Live market status needs vendor
     credentials (not configured)". This is the honest no-creds path — never a fabricated open/closed.

5. (Market-closed branch only) Type `AAPL` into the "Symbol search" box, then click the green **Watch** button
   - **Expect:** A centered amber panel titled **"Market is closed"** with the phrase
     "market is closed", the next-open time, and text suggesting "replay a past session with
     Historical instead". **No** cockpit (no quote / trades / state panels) appears.
   - **Broken looks like:** a fabricated cockpit with fake trades, a blank screen, or a raw UTC time
     ending in `Z`.

6. Click the **Simulated** button in the data-source selector
   - **Expect:** The "market" pill **disappears** from the top bar (it lives only in Live mode), and
     any error panel clears.

7. Type `SIM-BUYER` into the "Ticker" box, then click **Watch**
   - **Expect:** The cockpit populates and the classification resolves to **buyer_control**; the top
     bar shows "Watching SIM-BUYER" with a **Stop** button. (Regression check — old flow still works.)

8. Click the **Stop** button next to "Watching SIM-BUYER"
   - **Expect:** The cockpit clears, the page returns to the idle state, and "Watching SIM-BUYER"
     disappears from the top bar.

---

## What "Working Correctly" Looks Like

- The Live "market" pill reflects the **real** US session (open / closed + next-open / unavailable),
  not a frozen "unavailable" stub.
- Next-open times read in local time with a zone label (e.g. `Jun 5, 09:30 AM EDT`), never raw UTC.
- A Live watch while closed shows the honest "Market is closed" panel with no fabricated tape.
- The market pill is present only in Live mode; Simulated and Historical flows are unchanged.

## Common Issues

- **No "market" pill in Live mode:** confirm the backend is up (`curl http://localhost:8000/market/clock`)
  and the frontend is pointed at it.
- **Pill stuck on `unavailable`:** vendor credentials are not configured — this is the correct honest
  state, not a failure. Add Alpaca creds to see open/closed.
- **"Market is closed" panel never appears:** you're likely running during market hours — the live
  branch returns "streaming not implemented" instead; verify the closed branch via backend test TC-06.
- **Time shows as `...Z` / wrong zone:** the local-timezone formatter is not being applied — flag it.
