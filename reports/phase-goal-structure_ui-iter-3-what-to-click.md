# Phase goal-structure_ui-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-structure_ui-iter-3
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable — no login is required anywhere in this app
- At least one dataset already registered (true by default in this environment — 7 datasets are
  registered today)

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser
   - **Expect:** The page loads with three stacked sections — "Levels & Zones," "Registry," and
     "Comparison" — and no red error banner.

2. Scroll to the bottom "Comparison" panel and read its two side-by-side boxes: "Champion (moved
   never by this view)" and "Founding baseline (PnL ledger)"
   - **Expect:** The Champion box reads "v1" and "default" as plain text with no button next to it.
     The Founding-baseline box shows either a ledger row or the text "No founding row yet — the
     PnL ledger is empty."

3. Click the dropdown that reads "Choose a dataset…" and select any dataset from the list
   - **Expect:** The dropdown now shows your chosen dataset's label; the "Run comparison" button
     (previously greyed out) becomes clickable.

4. Click the "Run comparison" button
   - **Expect:** The button's label changes to "Running…" and two card slots appear side by side,
     labeled "v1 (champion strategy)" and "structure_tape," each showing "Queued…" or "Running…"

5. Wait for both cards to finish (usually well under 30 seconds — do not refresh or navigate away)
   - **Expect:** Both cards now show a list of numbers (`n`, `net R`, `net $`, `win_rate`,
     `max drawdown (R)`), a "Per-class (A/B/C)" table below that, and an amber line reading
     "simulated — assumed fees/slippage — not indicative of live results"

6. Refresh the page (press F5)
   - **Expect:** The Comparison section goes back to its starting message, "Choose a dataset, then
     Run comparison, to compare structure_tape against v1." This is expected — comparisons are not
     saved between page loads — it is not a bug.

7. Scroll to the top "Levels & Zones" section, enter any symbol/as-of time you know has recorded
   data, and click its Load button
   - **Expect:** A price chart renders with candles and dashed level lines, same as before this
     update.

8. Scroll to the middle "Registry" section
   - **Expect:** Two strategy cards (`v1` and `structure_tape`) and a Champion panel reading
     "v1"/"default" still render normally — unaffected by the new Comparison section below.

9. Look at the top navigation bar
   - **Expect:** Exactly five tabs are visible — Cockpit, Journal, Studies, Performance,
     Structure — all clickable.

---

## What "Working Correctly" Looks Like

- You picked a dataset, clicked one button, and — without any further clicks — watched two
  strategies' results appear side by side with matching numbers, a per-class breakdown, and an
  honesty disclaimer under each.
- The champion always reads "v1"/"default" in both places it appears on the page (Registry and
  Comparison), and neither place offers a way to change it.
- Everything that existed on `/structure` before this update (the chart, the zones table, the
  registry cards) still looks and works exactly the same.

## Common Issues

- **Blank page / error screen on `/structure`:** Check that the backend is running
  (`curl http://localhost:8000/health` or your project's health-check equivalent).
- **"Run comparison" never leaves "Running…":** Look for the text "Backend unreachable while
  polling — showing the last known status." If present, the backend stopped mid-run. If absent and
  it's been several minutes, this is a genuine stuck-poll bug worth reporting.
- **Dropdown shows "No datasets registered.":** Expected only in a freshly-initialized environment
  with no data recorded yet — not a bug in a normal dev environment (which has 7 datasets by
  default).
- **`win_rate` or `max drawdown (R)` shows a bare "0" instead of "no trades (n=0)":** This is a real
  bug — a zero-trade strategy must show the honest "no trades" label, never a numeric zero.
- **The two champion badges (Registry vs. Comparison) show different strategies or profiles:**
  This is a real bug — both must always read the same value, since both are read from the same
  underlying source.
