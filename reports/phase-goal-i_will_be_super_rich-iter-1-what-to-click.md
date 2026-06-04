# Phase goal-i_will_be_super_rich-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650` (substitute `:3000` if running the default port)
- Backend running and reachable
- **No Alpaca credentials configured** — `ALPACA_API_KEY` / `ALPACA_API_SECRET` must be absent from the backend environment. This is the honest no-credentials state you are verifying.

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser
   - **Expect:** The "Tapeology" title loads. Just right of it is a 3-button switch showing `Live` `Historical` `Simulated`, with `Simulated` highlighted. A ticker box (placeholder `Ticker e.g. SIM-BUYER`) and a green `Watch` button are visible. No error screen.

2. With `Simulated` still selected, type `SIM-BUYER` into the ticker box and click the green `Watch` button
   - **Expect:** Within ~10s the cockpit fills with live values, a `Watching SIM-BUYER` label + `Stop` button appear, and the status dot at the far right turns green (`live`). The tape state reads `buyer_control`.
   - **Broken looks like:** an empty cockpit, a stuck grey/amber dot, or no panels populating.

3. Click the `Live` button in the 3-way switch
   - **Expect:** The `Watching SIM-BUYER` label clears and the status dot drops back to `idle`/`connecting` (the old watch is torn down — not left running). The ticker box placeholder changes to `Symbol e.g. AAPL`. A small pill reading `market unavailable` with an amber dot appears.

4. Type `AAPL` into the symbol box and click the green `Watch` button
   - **Expect:** The main area shows an amber-bordered panel titled `Real-data provider unavailable` with a ⚠ icon and the phrase `real-data provider unavailable`. NO cockpit, NO prices, NO fabricated tape.
   - **Broken looks like:** any populated cockpit appearing, or the app silently switching back to Simulated.

5. Click the `Historical` button
   - **Expect:** The market pill disappears and four extra controls appear inline: a date picker, a start-time box, an `–`, an end-time box, and a speed dropdown listing `1× 2× 5× 10×`.

6. Type `MSFT`, pick any date + start/end time, then click `Watch`
   - **Expect:** The same amber `Real-data provider unavailable` panel appears (now referencing `Historical` data). Still no cockpit, no fabricated data.

7. Click `Simulated`, type `SIM-BUYER`, click `Watch`, then click the red `Stop` button
   - **Expect:** The cockpit repopulates and resolves to `buyer_control` again, confirming the real-data work did not break the original flow. After `Stop`, the `Watching` label and cockpit clear and the status dot returns to idle.

---

## What "Working Correctly" Looks Like

- Simulated `SIM-BUYER` always produces a full cockpit resolving to `buyer_control` — unchanged from before.
- Choosing `Live` or `Historical` and clicking `Watch` (with no credentials) **always** yields the amber `real-data provider unavailable` panel — never a cockpit, never fake data, never a silent fall-back to Simulated.
- Switching the data source or symbol cleanly drops the previous watch (the status dot resets; no leftover `Watching SIM-BUYER`).

## Common Issues

- **Blank page / error screen:** Confirm the backend is running (`curl http://localhost:8000/health` — adjust port to your offset, e.g. `:8650`).
- **A cockpit appears for Live/Historical:** This is a failure — it means real data was fabricated or the app fell back to Simulated. The expected result is the unavailable panel.
- **Provider-unavailable panel appears even in Simulated:** This is a failure — Simulated must always run the built-in scenarios.
- **Old `SIM-BUYER` keeps updating after you switch source:** This is the orphaned-watch regression — the prior watch should be torn down on any source/symbol change.
