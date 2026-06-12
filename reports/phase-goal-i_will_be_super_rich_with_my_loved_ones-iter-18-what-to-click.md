# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (canary check: `curl -s http://localhost:8000/research/taxonomy` must return HTTP 200 and include studies copy)
- No login credentials required — the reference-window source uses the committed PG SIP fixture without credentials

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The cockpit page loads. The "Studies" entry in the top navigation bar is a clickable link with a pointer cursor — it is NOT greyed out and has no "Coming with replay studies" tooltip on hover.
   - **Broken looks like:** "Studies" appears as grey, non-interactive text with a `cursor-not-allowed` style.

2. Click the "Studies" link in the top navigation bar
   - **Expect:** Browser navigates to `http://localhost:3650/studies`. The "Studies" nav item gains an emerald (green) active highlight. The page shows a layout with a create-study form on the left and a right-column panel displaying "∅" with the text "Create a study, or select one from the list, to read its results."
   - **Broken looks like:** 404 page, blank white screen, or JavaScript crash banner.

3. In the create form, click the "Reference window" radio card; then select "absorption_reversal" in the Setup dropdown and "long" in the Direction dropdown; then click "Run study"
   - **Expect:** The "Run study" button briefly reads "Running…" while the request is in flight. A new row appears in the job list showing a "Queued" slate badge, the setup name "absorption_reversal", and direction "long". The button returns to "Run study" after the row appears.
   - **Broken looks like:** Button stays stuck on "Running…", no row appears, or a rose error box appears below the form.

4. Watch the job list row (do NOT refresh the page)
   - **Expect:** Within a few seconds the status badge changes from "Queued" (slate) to "Running" (amber) automatically. While Running, a monospace event counter like "3200 events processed" is visible on the row. After the study completes, the badge changes to "Done" (neutral slate) and the Cancel button disappears.
   - **Broken looks like:** Badge stays "Queued" indefinitely without polling; or page requires a manual refresh to show status changes.

5. Click the "Done" row in the job list
   - **Expect:** The right-column results panel renders with: (a) two side-by-side distribution blocks labeled "Your setup" and "Random-time baseline", each showing 10s / 30s / 60s / 120s horizon rows with four distinct chips per row (+1R emerald, −1R rose, neither slate, Truncated amber); (b) an occurrences table with columns "Arm time (logical s)", "Verdict reached", "R basis" in monospace font; (c) three monospace chips in the header — Feed, Config fingerprint (hover to see full hash), and Baseline seed; (d) the text "Descriptive only — not trading advice" visible near the distribution blocks and again at the foot of the panel.
   - **Broken looks like:** Blank or white right panel; only one distribution block; missing monospace header chips; "edge" or "win rate" language present.

6. Select "level_break" in the Setup dropdown (while still on the create form on the left)
   - **Expect:** A "Level price" number input field and an amber hindsight warning box appear below the setup dropdown. The "Run study" button becomes disabled again until the level price is filled.
   - **Broken looks like:** No level input appears; or the Run Study button stays enabled without a level price.

7. Click "Reference window" source, change Setup back to "absorption_reversal", set Direction to "long", click "Run study" — then immediately click "Cancel" on the new row while it shows a "Running" amber badge
   - **Expect:** The status badge changes to "Cancelled" (slate) without a page refresh. The "Cancel" button disappears from the row. Clicking the cancelled row shows a "PARTIAL" warning above any occurrence data in the right panel.
   - **Broken looks like:** Cancel has no effect; badge stays "Running"; or Cancel button remains visible after cancellation.

8. Navigate to `http://localhost:3650` (cockpit page) by clicking "Cockpit" in the nav bar, then navigate to `http://localhost:3650/journal` by clicking "Journal"
   - **Expect:** Cockpit loads cleanly with no new elements, no new buttons, no color changes compared to before this iteration. Journal loads cleanly. The only change visible in the nav on both pages is the enabled "Studies" link.
   - **Broken looks like:** Cockpit shows new panels or controls that were not present in prior iterations; Journal page errors; or other nav links appear broken.

---

## What "Working Correctly" Looks Like

- The Studies nav item is an active green-highlighted link after navigating to `/studies`, not a grey disabled label.
- A reference-window study transitions Queued → Running → Done automatically without a page refresh, and the completed results show two side-by-side distribution blocks with four chips per horizon (not three, and Truncated is never merged).
- The honesty stamps (Feed, Config fingerprint with hover tooltip, Baseline seed) are always present in the results header for every completed study.
- The framing line "Descriptive only — not trading advice" appears both above the distribution blocks and at the foot of the results — nowhere on the page are the words "edge", "win rate", or "predict" present.
- Cancelling a running study flips its badge to "Cancelled" in real time and shows a PARTIAL warning when its row is clicked.
- The cockpit page (home) looks identical to the previous iteration — the only nav difference is the enabled Studies link.

## Common Issues

- **Backend not returning studies copy:** Run `curl -s http://localhost:8000/research/taxonomy` — if it returns 404 or does not include study-related keys, the backend has not started with the iter-18 code. Restart the backend.
- **Studies page shows blank right column with no placeholder text:** The `StudyResultsView` empty state may not be rendering. Check the browser console for JavaScript errors.
- **Status badge not updating automatically:** The `StudyList` polls the backend while any study is active. If polling stops, check the browser console for network errors to `http://localhost:8000/research/studies`.
- **"Run study" button stays disabled after filling all fields for a level setup:** Ensure the "Level price" field has a valid number entered — the button requires a non-empty, numeric level price for `level_break` and `failed_move_fade` setups.
- **Reference-window study fails immediately:** Verify the PG SIP fixture file exists at `apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`. If missing, the backend cannot load the reference data.
