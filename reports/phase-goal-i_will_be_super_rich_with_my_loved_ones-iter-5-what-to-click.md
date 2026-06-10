# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000` against the persistent `tapeology_journal.db` (schema v2 migration applied)
- Confirm the backend is healthy before starting: open a terminal and run `curl http://localhost:8000/health` — you should receive a 200 response
- No active thesis should exist when you begin (the backend startup sweep resolves any orphans automatically on start)

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The Cockpit page loads fully — price chart visible in the upper area, thesis strip visible between the chart and the lower panels, no error overlay or blank screen

2. Inspect the thesis strip (the horizontal band between the chart and the panel grid)
   - **Expect:** The strip shows a declare affordance — a button or form for entering a new thesis. No verdict chip (no coloured pill), no evidence line, no error message. The strip is in its idle state.
   - **Broken looks like:** The strip shows a "server error" message, a 503/500 notice, or is completely blank/missing from the layout.

3. In the thesis strip declare form, set **Setup type** to `absorption_reversal`, **Direction** to `long`, and type `99.0` in the **Invalidation price** field. Then click the **Declare** button.
   - **Expect:** The strip transitions from the idle declare affordance to an active thesis view within ~2 seconds. A slate-grey chip labelled "pending" appears in the strip. The setup type and direction are visible in the active view. The URL stays at `http://localhost:3650`.
   - **Broken looks like:** The strip stays idle (no transition), shows "503", shows "server error", or the page crashes. This is the core defect this iteration fixed — if this fails, the migration has not applied correctly.

4. Wait up to 10 seconds while remaining on `http://localhost:3650`, watching the verdict chip in the thesis strip
   - **Expect:** The verdict chip label and colour update from "pending" (slate/grey) to "confirming" (emerald/green) as the tape scenario delivers buyer control signals. The transition happens live without any page reload. An evidence line below the chip shows plain-language text.
   - **Broken looks like:** The chip stays "pending" indefinitely with no update, or the strip shows an error after the declaration succeeded.

5. Open browser DevTools (press F12), click the **Elements** tab, and press Ctrl+F to search for the text `thesis-strip`
   - **Expect:** Exactly one element is found — a `<section>` tag with the attribute `data-testid="thesis-strip"`. This is present whether the strip is in idle or active state.
   - **Broken looks like:** No element is found, or the search returns zero results — the `data-testid` attribute is missing.

6. Now test an inline validation error. If no active thesis is currently blocking you, locate the declare form in the thesis strip. Set **Direction** to `long` and set **Invalidation price** to a value ABOVE the current last traded price (an intentionally wrong-side value). Click **Declare**.
   - **Expect:** The declaration fails. An error message appears as visible text INSIDE the thesis strip — not a browser popup, not an auto-dismissing banner, not hidden in the console. The form remains usable so you can correct the value.
   - **Broken looks like:** The page crashes, the error shows only in the browser console, or a browser alert dialog appears instead of an inline message.

7. Refresh the page (press F5 or Cmd+R) while an active thesis is displayed in the strip
   - **Expect:** After reload, the thesis strip shows the same active thesis that was visible before the refresh — the verdict chip and thesis details are restored from the persistent backend. The strip does not revert to the idle declare affordance (unless the thesis has since resolved).
   - **Broken looks like:** After refresh the strip returns to idle (empty) state, indicating the thesis was not persisted.

---

## What "Working Correctly" Looks Like

- The thesis strip transitions from idle declare affordance to active thesis view immediately on a successful declaration — no "503" error, no page crash
- The verdict chip updates its label and colour live (pending → confirming) without a page reload — the verdict engine is running
- The `data-testid="thesis-strip"` attribute is findable in DevTools in both the idle and active states
- Inline validation errors appear as text inside the strip itself — never as browser alerts or hidden in the console

## Common Issues

- **Backend health check fails (`curl http://localhost:8000/health` returns connection refused):** The backend is not running. Start it before proceeding.
- **Declaration returns "503" or "server error":** The persistent `tapeology_journal.db` may not have been migrated to schema v2. Restart the backend — the migration runs automatically on startup.
- **Strip stays idle after a declaration that appeared to submit:** Check the browser console (F12 → Console) for a network error on the POST request to `/research/thesis`. A 409 error means an active thesis is already blocking the ticker (orphan not swept). Restart the backend to trigger the orphan sweep.
- **Verdict chip never updates from "pending":** The tape scenario may need a few more seconds, or the watched ticker may not be producing confirming signals. Try SIM-BUYER with setup type `trend_continuation / long` and wait ~10 seconds after the dwell period.
