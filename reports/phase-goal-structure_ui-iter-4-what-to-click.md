# Phase goal-structure_ui-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-structure_ui-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Before You Start

This iteration changed **zero lines of application code** — `/structure` looks and behaves
exactly as it did after the last verification pass. What this iteration needs from you is proof:
watch the Comparison section run a real, live comparison end-to-end and confirm none of its
numbers are fabricated. If anything below looks different from how it's described here, that IS a
regression worth reporting, since nothing was supposed to change.

## Prerequisites

- Both services running: frontend at `http://localhost:3301`, backend healthy at
  `http://localhost:8301/health` (ask your developer to run `bash scripts/dev.sh` if either is
  down — do not proceed until both respond, since a down service is exactly what caused the
  previous verification attempt to be skipped)
- No login required anywhere in this app
- At least one dataset already registered (true by default in this environment)

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser
   - **Expect:** The page loads with three stacked sections — "Levels & Zones," "Registry," and
     "Comparison" — and no red error banner.

2. Scroll to the bottom "Comparison" panel, click the dropdown reading "Choose a dataset…" and
   select any dataset, then click the "Run comparison" button
   - **Expect:** The button's label changes to "Running…" and two card slots labeled "v1 (champion
     strategy)" and "structure_tape" appear, each showing "Queued…" or "Running…"

3. Wait for both cards to finish (usually well under 30 seconds — do not refresh or navigate away)
   - **Expect:** Both cards show a list of numbers (n, net R, net $, win_rate, max drawdown (R)), a
     "Per-class (A/B/C)" table with three rows each (Class A/B/C), and an amber line reading
     "simulated — assumed fees/slippage — not indicative of live results"

4. Look at the "Champion (moved never by this view)" box above the dataset dropdown
   - **Expect:** It still reads "v1" and "default" — exactly the same as before you ran the
     comparison in step 2. No button or control sits inside this box.

5. If either card shows `n` = 0 (no trades), check its Per-class table
   - **Expect:** All three class rows show the chip "insufficient sample (n < 5)", and the
     win_rate/max-drawdown fields read the words "no trades (n=0)" — never a bare "0". This is the
     specific honest state this iteration exists to prove works.

6. Refresh the page (press F5)
   - **Expect:** The Comparison section resets to its starting message, "Choose a dataset, then Run
     comparison, to compare structure_tape against v1." This is expected, not a bug — comparisons
     aren't saved between page loads.

7. Scroll to the top "Levels & Zones" section, enter any symbol/as-of time you know has recorded
   data, and click its Load button
   - **Expect:** A price chart renders with candles and dashed level lines, with nothing (no
     loading spinner or empty-state message) covering the chart itself.

8. Scroll to the middle "Registry" section, then look at the top navigation bar and click
   "Performance"
   - **Expect:** Two strategy cards (`v1` and `structure_tape`) and a Champion panel reading
     "v1"/"default" render normally in Registry; the nav bar shows exactly five tabs (Cockpit,
     Journal, Studies, Performance, Structure); clicking "Performance" loads `/performance` with its
     own champion summary reading "v1"/"default".

9. Go to `http://localhost:3301/` (Cockpit) and type "SIM-BUYER" into the symbol field, then press
   Enter
   - **Expect:** The idle placeholder is replaced by a populated thesis strip (entry checklist,
     running R, eventually a realized R once the scenario closes). This flow shares no code with
     `/structure`, so if it's broken, something else in the app broke — not this iteration.

---

## What "Working Correctly" Looks Like

- You picked a dataset, clicked one button, and — without any further clicks — watched two
  strategies' results appear side by side with matching numbers, a per-class breakdown, and an
  honesty disclaimer under each.
- The champion always reads "v1"/"default" in both places it appears on the page (Registry and
  Comparison), and neither offers a way to change it.
- Everything that existed on `/structure` and elsewhere before this iteration still looks and
  works exactly the same — because nothing was supposed to change this time.

## Common Issues

- **Blank page / error screen on `/structure` or Cockpit:** Check that the backend is running
  (`curl http://localhost:8301/health`). If it returns nothing, ask your developer to run
  `bash scripts/dev.sh`.
- **"Run comparison" never leaves "Running…":** Look for the text "Backend unreachable while
  polling — showing the last known status." If present, the backend stopped mid-run — it should
  self-recover once the backend is back up. If absent and it's been several minutes, this is a
  genuine bug worth reporting.
- **`win_rate` or `max drawdown (R)` shows a bare "0" instead of "no trades (n=0)":** Real bug — a
  zero-trade strategy must show the honest "no trades" label, never a numeric zero.
- **The two champion badges (Registry vs. Comparison) show different strategies or profiles:**
  Real bug — both must always read the same value.
- **The chart is covered by a loading/empty overlay that never goes away:** Real bug — this is the
  exact z-index issue this project fixed once before; it must not have come back.
