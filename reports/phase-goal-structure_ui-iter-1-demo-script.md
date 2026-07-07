# Demo Script — goal-structure_ui-iter-1

**Mode:** record
**Date:** 2026-07-07
**Frontend URL:** http://localhost:3301
**Iteration:** 1

## Highlights

### Step 01 — Open Tapeology

- **Narration:** Let's start on Tapeology's home page, the Cockpit.
- **Action:** Navigate to /
- **Point out:** The top navigation bar now ends with a new tab called Structure.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-01.png

### Step 02 — Open the new Structure page  [NEW]

- **Narration:** Clicking Structure opens a brand-new page for viewing a symbol's support and resistance levels.
- **Action:** Click the "Structure" link
- **Point out:** A fresh page appears with its own heading and a plain-language explanation of what it shows, plus Symbol, As-of, and Load controls waiting for input.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-02.png

### Step 05 — Refresh the page  [NEW]

- **Narration:** Before loading anything, let's refresh the page.
- **Action:** Navigate to /structure
- **Point out:** The Symbol and As-of fields are empty again, and the same starting message reappears — the page deliberately doesn't remember the last query.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-05.png

### Step 08 — Load PG's levels and zones  [NEW]

- **Narration:** Clicking Load asks the research API for this symbol's real support-and-resistance levels and confluence zones — when history has been recorded for a symbol, this same page draws it on a candlestick chart with a zones table underneath.
- **Action:** Click the "Load" button
- **Point out:** Right now the app is honest that no price history has been recorded yet for PG in this environment — never a blank page or a made-up chart.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-08.png

### Step 10 — See the honest error state  [NEW]

- **Narration:** Loading with a malformed date never crashes the page or leaves it blank.
- **Action:** Click the "Load" button
- **Point out:** An amber-bordered panel shows the exact reason the request failed, plus a note that nothing cached or fabricated is shown in its place.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-10.png

### Step 11 — Confirm Performance still works

- **Narration:** Let's make sure an existing page still works exactly as before.
- **Action:** Click the "Performance" link
- **Point out:** The Performance page loads normally, with its profit-and-loss scorecard and champion strategy intact — and the Structure tab now sits alongside it in the nav.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-11.png

### Step 14 — Watch a simulated tape

- **Narration:** Watching a simulated tape still works exactly as it did before this update.
- **Action:** Click the "Watch" button
- **Point out:** Within moments, the Cockpit populates with a live quote, recent trades, and a tape-state reading of Buyer Control.
- **Screenshot:** reports/demo/goal-structure_ui-iter-1/step-14.png

## Full tour (text only)

### Step 03 — Type a symbol  [NEW]

- **Narration:** Typing a symbol here works just like the search boxes used elsewhere in the app.
- **Action:** Type "PG" into the "Symbol" field
- **Point out:** PG now appears in the Symbol field.

### Step 04 — Set an as-of time  [NEW]

- **Narration:** Adding an as-of date and time completes the query.
- **Action:** Type "2026-06-09T21:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The Load button switches from dim to fully solid the moment both fields are filled.

### Step 06 — Type the symbol again  [NEW]

- **Narration:** Typing the symbol again after the refresh.
- **Action:** Type "PG" into the "Symbol" field
- **Point out:** PG is back in the Symbol field.

### Step 07 — Set the as-of time again  [NEW]

- **Narration:** And the as-of time again.
- **Action:** Type "2026-06-09T21:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** Both fields are filled, so Load is ready.

### Step 09 — Try an invalid date  [NEW]

- **Narration:** Now let's deliberately type something that isn't a valid date.
- **Action:** Type "not-a-date" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field reads not-a-date.

### Step 12 — Go back to the Cockpit

- **Narration:** Back to the Cockpit to check the original live-tape flow.
- **Action:** Click the "Cockpit" link
- **Point out:** The ticker box and green Watch button are right where they were.

### Step 13 — Type a simulated ticker

- **Narration:** Typing in a simulated ticker to watch.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-BUYER appears in the ticker field.
