# Phase goal-i_will_be_rich-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-7
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000` (verify with `curl http://localhost:8000/health`)
- Optional, to make the live window easier to catch: start the backend with `TAPEOLOGY_FEED_PACE=0.12`
- No login or seed data required — `SIM-BUYER` is a built-in simulator ticker

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The cockpit loads with the "Tapeology" wordmark, a ticker input, and a green "Watch" button. The body reads "No ticker watched" and the top-right status dot reads "idle" (grey). **No "Stop" button is visible.**

2. Type `SIM-BUYER` into the "Ticker e.g. SIM-BUYER" field and click the green "Watch" button
   - **Expect:** The top bar shows "Watching SIM-BUYER" with a rose-outlined "Stop" button right after it. The body switches to the populated cockpit panels.

3. Wait until the top-right status dot reads "live" (green) and panels show numeric values
   - **Expect:** Live values are rendering — the cockpit is active, not empty.

4. Click the "Stop" button (do it promptly, while the dot still reads "live")
   - **Expect:** The body immediately switches back to "No ticker watched". The "Watching SIM-BUYER" label and the "Stop" button disappear, and the status dot returns to "idle" (grey).
   - **Broken looks like:** numbers stay frozen on screen, the Stop button lingers, or the dot stays green/red after the click.

5. Confirm nothing stale remains in the body
   - **Expect:** Only the idle "No ticker watched" prompt is shown — no leftover quote, trades, or feature numbers anywhere.

6. Type `SIM-BUYER` again and click "Watch" a second time
   - **Expect:** The cockpit repopulates from a cold start (dot moves through connecting → live, values fill in fresh). It does NOT come back as a frozen/"closed" leftover frame.

7. (Regression) Click "Stop", then type `SIM-SELLER` and click "Watch"
   - **Expect:** The cockpit populates for `SIM-SELLER` with no page reload — proving Watch still works after the Stop control was added.

---

## What "Working Correctly" Looks Like

- A rose "Stop" button is present ONLY while a ticker is watched, and gone on the idle screen
- Pressing Stop instantly empties the screen to "No ticker watched" with the status dot grey ("idle")
- Re-watching the same ticker gives a fresh, repopulating cockpit — not a frozen last frame

## Common Issues

- **Blank page / error screen:** Confirm the backend is up — `curl http://localhost:8000/health` should return OK.
- **Stop click does nothing / numbers stay frozen:** The client WS may not be closing — check the browser console for errors from `useTapeStream`.
- **Live window too short to catch:** The bounded sim stream may exhaust before you click. Restart the backend with `TAPEOLOGY_FEED_PACE=0.12` to widen it, or note that the idle-return still works even if the dot reached "closed" first.
- **Re-watch shows a red "closed" dot immediately:** the engine was not torn down/removed on Stop — re-watch should always build a fresh engine.
