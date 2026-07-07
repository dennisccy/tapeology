# Phase goal-structure_ui-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-structure_ui-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301` (this environment's paired ports)
- **Optional, one-time setup to see the fully populated chart + table** (recommended, but not required — if you skip it, step 4 below will show an honest "no data recorded" message instead, which is also a correct result, not a failure): before starting the backend, copy the two files from `apps/backend/tests/fixtures/bars/` into its live bar directory (default `apps/backend/.data/bars/`), or start the backend with the environment variable `TAPEOLOGY_BAR_DIR=apps/backend/tests/fixtures/bars`. Ask a developer if you're unsure how to do this.

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The Cockpit loads. The top nav bar shows exactly 5 links: `Cockpit`, `Journal`, `Studies`, `Performance`, `Structure` — with `Structure` last, right after `Performance`. This is the new part.

2. Click "Structure" in the top nav
   - **Expect:** The browser navigates to `http://localhost:3301/structure`. A heading reading "Structure" appears, and below the controls the message "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones." is visible.

3. Type `PG` into the "Symbol" field, then type `2026-06-09T21:00:00Z` into the "As-of (UTC, ISO-8601)" field
   - **Expect:** The "Load" button changes from greyed-out/dim to fully solid and clickable the moment both fields have text in them.

4. Click "Load" and wait about 2 seconds
   - **Expect (one of two correct outcomes, depending on whether you did the optional setup):**
     - **If you seeded the fixture:** a dark candlestick chart appears with several dashed horizontal reference lines across it, and below the chart a "Confluence zones" section lists 6 cards, each headed "Class C" or "Class B". A small caption directly under the chart starts with "Candles: 1h series (9 of 9 recorded bars...".
     - **If you skipped setup:** the message "No bar series recorded for PG." appears, with a second line explaining that recording historical bars needs provider credentials.
   - Both outcomes are correct — neither is a blank page, a crash, or a fabricated chart.

5. Refresh the page (press F5)
   - **Expect:** The page returns to the same idle message from step 2, and the Symbol/As-of fields are empty again. The page deliberately does not remember your last query — this is correct, not a bug.

6. Click "Journal" in the top nav
   - **Expect:** The Journal page loads exactly as it did before this update — a list/table of journal entries, no trace of anything from the Structure page.

7. Click "Cockpit" (the first nav link), type `SIM-BUYER` into the ticker box, and click the green "Watch" button
   - **Expect:** "Connecting to SIM-BUYER…" appears immediately, then within about 10 seconds a live simulated tape view populates (quote, trades, features, event log) and the tape state reads "buyer control". This confirms the pre-existing simulator still works exactly as before.

---

## What "Working Correctly" Looks Like

- The "Structure" link is the 5th, rightmost item in the top nav on every page — Cockpit, Journal, Studies, and Performance are all unaffected.
- Loading a symbol on `/structure` always ends in one of exactly four outcomes: a real chart + zones table, or one of three distinctly-worded "nothing to show, and here's honestly why" messages — never a blank white screen, never a fake chart.
- The Cockpit's `SIM-BUYER` flow still resolves to a live, populated tape exactly as it did before this update.

## If Something Looks Wrong

- **Blank page or error screen anywhere:** confirm the backend is actually running and reachable at `http://localhost:8301`.
- **No "Structure" link in the nav:** the backend may be running an older build — restart it, then hard-refresh the browser (Ctrl+Shift+R).
- **"Load" button never turns on:** make sure both the Symbol and As-of fields actually contain visible text — an empty-looking field with a stray space still counts as empty.
- **Chart area looks completely blank but no "no data" message is shown either:** wait 2–3 more seconds — the chart draws asynchronously just after the page updates, and an instant look can catch it mid-draw. If it's still blank after that, that IS a problem worth reporting.
- **Typing something nonsensical (e.g. `banana`) into the As-of field and clicking Load:** should show a clearly-marked amber box with a short message (never a raw crash or blank page) — if the whole page goes blank or shows a browser error page instead, that's a real defect.
