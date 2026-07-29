# Demo Script — goal-desk-iter-15

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk briefing

- **Narration:** The Desk page shows the latest recorded screen over the registered universe: a ranked table of tradable walls, read verbatim from the persisted snapshot. Nothing on this page is recomputed in the browser.
- **Action:** Navigate to /desk
- **Point out:** The heading reads 'Desk', and the Provenance panel pins the exact screen this page is showing: universe snapshot, screen date, as-of, config fingerprint, and bar-store signature.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-01.png

### Step 02 — The briefing table gains a history column  [NEW]

- **Narration:** This iteration adds one column to the ranked table: history. It sits immediately right of the existing basis column and says how much completed daily history each row's wall was measured over.
- **Action:** Expect {'testid': 'desk-screen-rows-table'}
- **Point out:** The header row now reads symbol, side, class, distance, score, coverage, tick evidence, basis, and — new — history.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-02.png

### Step 03 — Every ranked row states its own history depth  [NEW]

- **Narration:** Each row now carries its own count of completed daily sessions at or before that row's basis bar, plus the date that history starts from. In the store this walkthrough runs against the counts span 27 to 501 across the same screen, so a recently listed name no longer looks identical to one with two years of sessions.
- **Action:** Expect {'testid': 'desk-row-history'}
- **Point out:** Read the history cell on any row: 'history 500 sessions - from 2024-07-25'. It is a plain count and a date — no score, no threshold, no judgement about whether that is enough.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-03.png

### Step 04 — Full precision lives in the row's existing tooltip  [NEW]

- **Narration:** The cell shows the start date rounded to a day. The untruncated timestamp is not lost: it joins the row drill-in anchor's one composite hover tooltip, beside the distance, score and basis details that were already there. No second tooltip mechanism was added.
- **Action:** Expect {'testid': 'desk-row-drill-in'}
- **Point out:** Hovering a row's symbol shows one tooltip ending with 'history 27 sessions from 2026-06-15T04:00:00.000000Z'. A native title tooltip is not painted into a screenshot — browser-QA read the attribute directly (UT-03).
- **Screenshot:** reports/demo/goal-desk-iter-15/step-04.png

### Step 05 — Open a screen recorded before this feature shipped  [NEW]

- **Narration:** Screen snapshots are append-only: an already-recorded screen is never rewritten or backfilled. Clicking an older row in Screen History swaps that exact persisted snapshot into the page.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-07-29"] td"
- **Point out:** The banner confirms which snapshot is on screen: 'Viewing the recorded screen for 2026-07-29 — not the latest.'
- **Screenshot:** reports/demo/goal-desk-iter-15/step-05.png

### Step 06 — A legacy row says so, instead of inventing a number  [NEW]

- **Narration:** That snapshot was recorded before this iteration's code existed, so its rows carry no history fields at all. The page says exactly that rather than showing a zero, a blank, or the word null.
- **Action:** Click the "history" columnheader
- **Point out:** Every history cell now reads 'history not recorded in this snapshot', while the basis column beside it still shows its own real per-row values.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-06.png

### Step 07 — Return to the latest screen  [NEW]

- **Narration:** The Latest button in Screen History drops the pinned older snapshot and puts the most recently recorded screen back on the page.
- **Action:** Click "desk-history-latest-button"
- **Point out:** The 'not the latest' banner disappears once the latest screen is displayed again.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-07.png

### Step 08 — The append-only screen ledger below the briefing

- **Narration:** Below the ranked table, Screen History lists every screen ever recorded, each with its own row/skip counts and its own provenance pins. Nothing here was rewritten by this iteration — the older snapshots are exactly the bytes they were recorded as.
- **Action:** Click "[data-testid="desk-history-table"] thead th"
- **Point out:** One row per recorded screen: date, rows, skipped, and the universe snapshot, config fingerprint and bar-store signature that screen was pinned to.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-08.png

### Step 09 — A 27-session listing beside a 500-session name  [NEW]

- **Narration:** Back up at the briefing, the whole point of the column is legible in one frame: rows at the top carry 500 completed sessions dating from July 2024, while HONA — ranked eighth on the same scale — carries 27, from June 2026. Before this iteration those two rows were indistinguishable.
- **Action:** Click the "history" columnheader
- **Point out:** Compare BRK-B's 'history 500 sessions - from 2024-07-25' with HONA's 'history 27 sessions - from 2026-06-15', both visible in this single view.
- **Screenshot:** reports/demo/goal-desk-iter-15/step-09.png
