# Phase goal-i_will_be_rich-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

> This iteration adds **no new UI** — it browser-proves the existing `SIM-BUYER` cockpit (J-01 / J-02 /
> J-08) that iter-1 left unverified. Your job: confirm the cockpit actually works live and that the two
> backend cleanups changed nothing visible.

---

## Prerequisites

- Backend running on the QA-harness offset port (e.g. `http://localhost:8650`).
- `rm -rf apps/frontend/.next` was done, then the frontend dev server restarted with
  `NEXT_PUBLIC_API_URL` pointed at that backend.
- Frontend running at `http://localhost:3650`.
- No login or seed data required — the `SIM-BUYER` scenario is built in.

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser.
   - **Expect:** Page loads (HTTP 200, **not** the iter-1 error/500). Top bar reads **"Tapeology"**
     with a ticker input and a green **"Watch"** button; center reads **"No ticker watched"** with the
     hint **"Try: SIM-BUYER"**; footer reads **"Descriptive only — not trading advice."**
   - **Broken looks like:** blank page, Next.js error overlay, or HTTP 500 → STOP, the run is invalid.

2. Type `SIM-BUYER` into the ticker input, then click the green **"Watch"** button.
   - **Expect:** Top bar now shows **"Watching SIM-BUYER"**; six panels appear — **Tape State,
     Quote, Features, Recent Trades, Observations, Event Log** — populated with numbers, not "—".

3. Look at the **Quote** panel and do the math: read **Bid**, **Ask**, **Spread**.
   - **Expect:** **Spread ≈ Ask − Bid** (e.g. ≈ `0.02` for Ask `100.26` / Bid `100.24`). In **Features**,
     **Average spread** ≈ `0.020`. (Confirms the spread-cleanup is behavior-preserving.)

4. Wait ~5 seconds **without reloading the page** and watch the **Last** value and the top of
   **Recent Trades**.
   - **Expect:** At least one value changes on its own (Last ticks, or a new trade row appears) over
     the live WebSocket — no reload needed.

5. Let it stabilize, then read the **Tape State** panel.
   - **Expect:** State reads **buyer_control** (label "Buyer Control") with **Confidence ≈ 0.80** and
     the confidence bar filled ~80%.

6. Read the **Features** panel.
   - **Expect:** **Aggressive buy ratio** is high (≈ `0.90`); **Buy price impact** is positive (≈ `+0.41`)
     and shown in green.

7. Read the **Event Log** panel.
   - **Expect:** It contains the line **"Tape state changed to buyer_control"**.

8. Open a second tab to `http://localhost:8650/tape/SIM-BUYER/state` and compare to the UI.
   - **Expect:** JSON `tape_state` = `buyer_control` and `confidence` matches the UI's Confidence
     value (within rounding). The UI is not inventing numbers — it mirrors REST exactly.

9. In a fresh tab, open `http://localhost:3650/` again but **do not** click Watch; then type
   `NOPE_UNKNOWN` and click **"Watch"**.
   - **Expect:** First, the idle **"No ticker watched"** state; then after the bad watch, a red error
     message under the top bar — **no crash, no blank screen**.

10. Glance at the top-right status dot and the footer.
    - **Expect:** The dot is **emerald** with label **"Live"** while watching; footer still reads
      **"Descriptive only — not trading advice."**

---

## What "Working Correctly" Looks Like

- The cockpit fills with live numbers after clicking **Watch**, and **at least one value updates on its
  own** without a reload (the WebSocket is live).
- **Tape State = buyer_control**, confidence ≈ 0.80, buy price impact positive — and the same values
  appear in the REST `/tape/SIM-BUYER/state` and `/features` JSON.
- Nothing new was added: six panels, one watch form, the disclaimer footer — exactly as in iter-1.

## Common Issues

- **Blank page / error overlay / HTTP 500:** the `.next` cache wasn't cleared or the dev server wasn't
  restarted with `NEXT_PUBLIC_API_URL`. The run is **invalid** until `/` returns 200 — don't record a
  SKIP as a pass.
- **Panels show "—" / "No trades yet." forever:** backend not reachable at the configured
  `NEXT_PUBLIC_API_URL`, or the WebSocket didn't connect (status dot stays amber "connecting" or turns
  rose "closed").
- **Spread doesn't equal ask − bid:** flag it — the spread-producer cleanup was supposed to be
  behavior-preserving.
