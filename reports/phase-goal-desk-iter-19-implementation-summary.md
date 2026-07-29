# goal-desk-iter-19 — Implementation Summary

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Written by:** developer

---

## Features Implemented

- **Corrected "opposite wall" selection**: the `/desk` ranked table's `opposite` column (added last
  iteration) now names the wall genuinely NEAREST to price on the other side of the market, instead
  of the best-graded (highest quality class) wall on that side. On real data this matters: for two
  of the 63 real names checked, the column was previously showing a wall more than twice as far
  away as a closer one that actually existed — for example, a wall shown as "336.96 basis points
  away" when a wall 153.67 basis points away was available and simply lower-graded. This iteration
  makes the column always show the closest one, matching what the feature's own name promises.

---

## Changed Behavior

- **`/desk` opposite-column content, on newly computed screens only**: Previously, when two walls
  existed on the far side of price and one was closer-but-lower-graded while the other was
  farther-but-higher-graded, the column showed the higher-graded (farther) one. Now it shows the
  closer one, with the graded-quality rule only used to break an exact tie in distance. This only
  changes what a NEW screen run (computed after this fix ships) will show — any screen already
  recorded before this fix keeps exactly what it recorded (nothing is silently rewritten).

---

## Backend-Only Items

None. This is a pure selection-rule fix inside an already-shipped, already-wired feature — no new
backend capability without a UI counterpart.

---

## Incomplete Items

None from this iteration's scope. The browser screenshot evidence and the re-recorded product
walkthrough video (both required by this iteration's definition of done) are produced by the
downstream QA and demo-recording steps of the pipeline, not by this implementation step — this step
covers the code fix, its tests, and a real-data verification of the fix.

---

## Config and Environment Changes

None. No new environment variables, no new configuration fields, no database/schema changes.

---

## Known Limitations

- One pre-existing data quality issue was discovered (not caused by, and not fixed by, this
  iteration): one already-recorded price bar for the stock "HONA" in the system's real historical
  data has a missing/invalid price. The system already correctly ignores that one bad data point
  when computing anything — this was confirmed while independently re-verifying the fix — so it has
  no effect on what operators see. It is noted here only for completeness.
