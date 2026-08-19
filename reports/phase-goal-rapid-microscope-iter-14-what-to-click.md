# Phase goal-rapid-microscope-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-14
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
- No login required
- No seed data required — this guide is written against the app's real, current state: the Scout
  ledger and Validation Vault are genuinely empty today, and the Walk-Forward ledger has one real
  sequence. Both are correct, expected states, not something you need to set up.
- **Do not click "Run Screen" or "Run Walk-Forward" during this guide.** Both start a real
  computation against the live backend that can run for 25+ minutes and is not reliably
  cancellable within a few minutes — outside the scope of a 5-minute check. This guide only
  confirms the buttons are present and correctly labeled.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with no error banner. Four section headers are visible in this
     order: "Microscope Readiness", "Scout Ledger", "Walk-Forward", "Validation Vault", each
     showing a closed "▸" arrow.

2. Click the "Scout Ledger" header
   - **Expect:** It expands (arrow changes to "▾"). A line "Ledger chain verification: ok" is
     visible, followed by either "No candidates ledgered." or a table of real family/trial rows.
     An enabled "Run Screen" button is visible below that (do not click it).

3. Click the "Walk-Forward" header
   - **Expect:** It expands. A line "Ledger chain verification: ok" is visible, followed by a
     "Fold Specs" block and at least one sequence block showing a "Sequence verdict:" line and a
     table of fold rows (Fold / Status / Effect / N / Sessions / Sign / Evidence class / Process
     label) — the real ledger has data today, so you should see actual rows, not an empty state.

4. Click the "Validation Vault" header
   - **Expect:** It expands. Two lines are visible: "Shard ledger chain verification: ok" and
     "Universe ledger chain verification: ok", followed by "No shards recorded." and "No
     universes registered." — and no button of any kind anywhere in this section (it is
     read-only by design).

5. Refresh the page (press F5 or Cmd+R)
   - **Expect:** All three headers ("Scout Ledger", "Walk-Forward", "Validation Vault") are back
     to the closed "▸" state — they start collapsed on every page load, on purpose.

6. Click "Scout Ledger" once more
   - **Expect:** The same content from step 2 reappears — confirms the data loads correctly again
     after a fresh page load, not just on the first visit.

7. Click "Microscope Readiness" (the section directly above the three new ones)
   - **Expect:** Its existing tables (totals, tick shards, floors) render exactly as they did
     before this phase — confirms the new sections did not disturb the section above them.

8. Navigate to `http://localhost:3301/structure`, then to `http://localhost:3301/`
   - **Expect:** `/structure` loads with its Tradable Map and comparison dropdown visible; `/`
     (Cockpit) loads with its chart visible. Neither page shows an error — confirms this phase's
     `/desk`-only change did not affect the other two pages.

---

## What "Working Correctly" Looks Like

- Three new section headers — "Scout Ledger", "Walk-Forward", "Validation Vault" — sit directly
  below "Microscope Readiness" on `/desk`, each expandable with a single click, each showing real
  backend data (or an honest "No … recorded/registered." message) rather than placeholder text.
- The Validation Vault section never shows a button — everything in it is a plain read of data
  already on screen.
- Nothing on `/structure` or `/` (Cockpit) looks any different than before.

## Common Issues

- **A section shows an amber box saying "Backend unreachable — is the API running?"**: the backend
  isn't running or crashed. Check with `curl http://localhost:8301/health` — it should return
  `{"status":"ok"}`.
- **Clicking a section header does nothing**: check the browser console for a JavaScript error;
  also confirm you're clicking directly on the header text/arrow, not elsewhere in the section box.
- **The Cockpit chart looks frozen/static**: this is a known quirk of some headless browser setups
  (`visibilityState: "hidden"`), not necessarily a real bug — check that the page is the active,
  visible browser tab before reporting it as broken.
- **You accidentally clicked "Run Screen" or "Run Walk-Forward"**: this is safe but will leave a
  real computation running in the backend for a while. You can leave it running (it does not
  corrupt any data) or restart the backend process to stop it early.
