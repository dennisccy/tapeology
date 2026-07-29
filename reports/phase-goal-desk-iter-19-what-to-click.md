# Phase goal-desk-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-19
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable (no login required)
- **Heads up before you start:** this iteration changes no page layout — it only corrects WHICH wall
  the `/desk` table's existing "opposite" column names on any row where two candidate walls exist on
  the far side of price. The corrected value only appears on a screen computed AFTER this fix
  shipped. If the last screen was computed before the fix, you will still see the OLD (best-graded,
  not nearest) selection or the honest "opposite wall not recorded in this snapshot" text on legacy
  rows — that is expected, not a bug. Step 3 below tells you how to check which case you're in and
  what to do about it.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** A "Desk" heading and a short description paragraph load, no blank screen, no amber
     "could not be loaded" panel

2. Scroll down to the ranked table (inside the "Briefing" panel, below "Provenance") and scroll it
   horizontally all the way to the right
   - **Expect:** The last column header still reads **"opposite"** — this iteration adds no new
     column; it only changes what value can appear in cells under this existing header

3. Look at the "Provenance" panel near the top of the page and read its "Recorded at" value
   - **Expect:** A timestamp. If it is from TODAY and you know a screen was computed after this
     fix shipped, the opposite column below already reflects the corrected rule. If it's older, click
     the **"Run Screen"** button near the bottom of the page and wait for its label to change from
     "Computing…" back to "Run Screen" — this computes (or reuses) a fresh screen

4. Find the row whose leftmost cell reads **"HONA"** (scroll down if it isn't near the top) and read
   its rightmost cell (the "opposite" column)
   - **Expect (fix is live on this screen):** The cell reads a pattern like `opposite resistance B
     ...  · 153.6 bps` — a **Class B** wall roughly **153.67 bps** away
   - **Expect (fix not yet reflected on this screen):** The cell instead reads `opposite resistance A
     ... · 336.9 bps` (a farther Class A wall) or the fallback text `opposite wall not recorded in
     this snapshot`. If you see either of these, the currently-displayed screen predates the fix —
     this is a known, disclosed gap (see "Common Issues" below), not something to report as broken

5. Repeat step 4 for the row whose leftmost cell reads **"META"**
   - **Expect (fix is live):** `opposite support C ... · 92.0 bps` (a **Class C** wall roughly
     **92.05 bps** away) — NOT `opposite support A ... · 232.5 bps`

6. Hover your mouse anywhere over either row (the whole row is one clickable link, so any spot works)
   and wait for the tooltip to appear
   - **Expect:** The tooltip ends with a segment reading `bands by class A <n> · B <n> · C <n> ·
     unclassified <n>` — unchanged by this fix, just a re-confirmation it still works

7. Scroll to the "Screen History" panel and click an entry OLDER than today's date
   - **Expect:** The page swaps in that older screen's own recorded values in place (a "Viewing the
     recorded screen for ..." banner appears with a "Latest" button). Its "opposite" column shows
     whatever THAT screen originally recorded, unchanged by today's fix — reloading the page (F5) and
     re-opening the same entry shows the identical values again. Click "Latest" to return to the
     current screen

---

## What "Working Correctly" Looks Like

- On any screen computed after this fix, a row with two candidate walls on the far side of price
  (like `HONA` or `META`) shows the NEARER one in its "opposite" cell, not the higher-graded farther
  one.
- Older, already-recorded screens (opened from "Screen History") keep showing exactly what they
  originally recorded — the fix never rewrites history.
- Every other column (symbol, side, class, distance, score, coverage, tick evidence, basis, history,
  band) and the row's hover tooltip look exactly as they did before this iteration.

## Common Issues

- **`HONA`/`META` rows aren't visible, or their "opposite" cell still shows the OLD Class A value**:
  this means the currently-displayed screen was computed before this fix shipped. Click "Run Screen"
  near the bottom of the page. If the message below the button reads "Reused the snapshot already
  recorded for this key — ...", a screen for today's pins is already recorded and clicking again
  won't produce a new one — this is correct dedup behavior (not a bug); a genuinely fresh, corrected
  example requires either a not-yet-recorded date or a dedicated fixture-scoped verification rig (see
  the dev/QA handoffs for this iteration).
- **An "opposite" cell is blank, or shows "undefined"/"NaN"**: this IS a bug — file it. The only
  correct states are the exact fallback text, the exact `"no band on the other side"` text, or the
  four-value `opposite <side> <class> <low>–<high> · <n> bps` pattern.
- **An older Screen History entry's "opposite" values changed after you reloaded the page**: this
  WOULD be a bug (the append-only guarantee broke) — file it immediately, this is the one regression
  this iteration explicitly guards against.
- **Blank page / error screen**: check that the backend is running and reachable at the port the
  frontend's `NEXT_PUBLIC_API_URL` was built with.
