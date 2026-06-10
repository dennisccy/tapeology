# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (verify: `curl http://localhost:8000/health` returns `{"status":"ok"}` or similar)
- No active thesis or watch in progress — if the cockpit shows an active thesis, stop the watch before starting

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The cockpit page loads. The thesis strip area is visible between the chart and the panel grid. The strip shows a "Declare a thesis" button or prompt (idle state). No error banner.
   - **Broken looks like:** Blank page, "Cannot connect" error, or an error banner across the top of the screen.

2. Select "SIM-BUYER" in the ticker selector at the top of the cockpit, then click "Watch" (or "Start watching")
   - **Expect:** The tape begins streaming — you see price prints updating in the tape display. The thesis strip stays in idle state (still shows "Declare a thesis").

3. Click the "Declare a thesis" button in the thesis strip, fill in the form with setup type "trend_continuation", direction "long", and an invalidation price well below the current last price, then click "Declare" (or "Confirm")
   - **Expect:** The form closes and the thesis strip switches to the active-thesis view. A verdict chip labeled "Pending" in a slate (grey) color appears in the top-right of the active-thesis row. An evidence sentence in plain English appears immediately beneath the chip (it is not empty — even "Pending" has a sentence).
   - **Broken looks like:** The form shows a validation error on submission, or the strip stays in idle state after submission, or the chip is missing, or the evidence sentence is empty.

4. Wait approximately 5 seconds without touching anything — keep watching the verdict chip
   - **Expect:** The verdict chip transitions from "Pending" (slate/grey) to "Confirming" (emerald/green) without any page reload. The evidence sentence updates to describe buyer control in plain English (e.g., "buyers keep pressing price up (buy_price_impact +0.xxxx); the tape confirms your thesis"). The chip color is clearly green, not grey, amber, or red.
   - **Broken looks like:** The chip stays "Pending" after 10+ seconds, or the chip text changes but stays slate/grey, or the evidence sentence disappears or reads the raw string `confirming` instead of a human-readable sentence.

5. Stop the current watch by clicking the "Stop watching" (or "Stop") button
   - **Expect:** The thesis strip returns to the idle state — the "Declare a thesis" button or prompt reappears. The "Confirming" chip disappears. This confirms that an *expired* (watch-stopped) thesis correctly clears the strip.

6. Select "SIM-SELLER" in the ticker selector, click "Watch", then declare a new thesis: setup type "trend_continuation", direction "long", invalidation price set just 1–2 points ABOVE the current last price (force immediate invalidation)
   - **Expect:** The thesis is declared and briefly shows "Pending". Within a few seconds, as seller prints come through at or below the invalidation level, the chip transitions to show "✕ Invalidated" with a rose (red/pink) background and a heavier rose-colored ring/border. A second line reading "Thesis invalidated — resolved" appears in rose below the evidence sentence. The evidence sentence mentions the offending print price.

7. With the "Invalidated" treatment visible on the strip, stop the watch by clicking "Stop watching"
   - **Expect:** The terminal invalidated treatment remains on the strip — the "✕ Invalidated" chip, the "Thesis invalidated — resolved" line, and the evidence sentence stay visible. The idle "Declare a thesis" affordance does NOT reappear. This confirms invalidated theses are NOT silently cleared.
   - **Broken looks like:** The strip reverts to idle "Declare a thesis" after stopping the watch when the thesis was invalidated — that is the old (broken) behavior this phase fixes.

---

## What "Working Correctly" Looks Like

- The verdict chip updates live in the strip without a page reload — from slate "Pending" to emerald "Confirming" as the tape evolves on SIM-BUYER
- An evidence sentence in plain English is always present beneath the chip, including while "Pending"
- Invalidated theses show a rose chip with "✕" prefix, a "Thesis invalidated — resolved" notice, and the terminal treatment persists after stopping the watch — the strip never silently reverts to idle for an invalidated thesis

## Common Issues

- **Chip stays "Pending" indefinitely:** The backend verdict engine may not be publishing verdicts. Check that the backend is running and the WebSocket connection is active (open browser DevTools → Network → WS tab and look for a connected `ws://` connection to the thesis stream).
- **Evidence sentence is empty or missing:** The `data-testid="verdict-evidence"` element should always have text. If it is blank, the frontend may not have received the taxonomy data — try refreshing the page.
- **Strip reverts to idle after invalidation:** This is the specific regression this phase fixes. If stopping the watch clears an invalidated thesis back to "Declare a thesis" idle state, the terminal-state fix in `ThesisStrip.tsx` did not take effect — check the frontend build.
- **Blank page / connection error:** Confirm both the frontend (port 3650) and backend (port 8000) are running before starting.
