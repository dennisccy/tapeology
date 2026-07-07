# Demo Script — goal-structure_ui-iter-2

**Mode:** record
**Date:** 2026-07-07
**Frontend URL:** http://localhost:3301
**Iteration:** 2

## Highlights

### Step 01 — Open Tapeology

- **Narration:** Let's start on Tapeology's home page.
- **Action:** Navigate to /
- **Point out:** The navigation bar across the top lists every section of the app, including Structure.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-01.png

### Step 02 — Open the Structure page

- **Narration:** Clicking Structure takes us to the page where a symbol's key price levels live.
- **Action:** Click the "Structure" link
- **Point out:** The Symbol, As-of, and Load controls are waiting for input, with a plain message explaining what to do next.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-02.png

### Step 03 — Meet the new Registry section  [NEW]

- **Narration:** Without clicking anything, a new Registry section has already loaded further down this same page, led by a Champion badge.
- **Action:** Click "champion-summary"
- **Point out:** The badge shows v1 on the default profile, with a note confirming it matches the same champion shown on the Performance page.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-03.png

### Step 04 — See the v1 strategy, honestly  [NEW]

- **Narration:** Right below the badge sits a card for v1, the app's original strategy, listing its entry and exit rules exactly as the system defines them.
- **Action:** Click "state_native_sustained_premise"
- **Point out:** There's no reward-target row on this card — v1 genuinely doesn't use one, so the page leaves it out instead of showing a blank or a fake zero.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-04.png

### Step 05 — See structure_tape's extra detail  [NEW]

- **Narration:** The second card, structure_tape, lists the same kind of rules, plus a reward target this strategy actually uses.
- **Action:** Click "strategy-exit-reward-target"
- **Point out:** Three small tables underneath show how its stop distance, reward target, and position size all scale across zone classes A, B, and C.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-05.png

### Step 08 — Load PG's levels, honestly

- **Narration:** Clicking Load asks the app for this symbol's price history — this iteration specifically re-confirmed this older feature still tells the truth instead of ever faking a chart.
- **Action:** Click the "Load" button
- **Point out:** Since this environment hasn't recorded price history for PG, the page says so plainly, with no blank screen and no invented chart.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-08.png

### Step 09 — Confirm Performance still agrees

- **Narration:** Finally, let's check the Performance page, which has shown its own champion badge since before this iteration.
- **Action:** Click the "Performance" link
- **Point out:** Its Champion box still reads v1 and default, and the Profile registry list underneath is intact — nothing about the new Structure section leaked in or broke anything here.
- **Screenshot:** reports/demo/goal-structure_ui-iter-2/step-09.png

## Full tour (text only)

### Step 06 — Try a symbol

- **Narration:** Now let's revisit the older part of this page and type in a stock symbol.
- **Action:** Type "PG" into the "Symbol" field
- **Point out:** PG appears in the Symbol field.

### Step 07 — Set an as-of time

- **Narration:** Adding a point in time completes the query.
- **Action:** Type "2026-06-09T21:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field now reads 2026-06-09T21:00:00Z.
