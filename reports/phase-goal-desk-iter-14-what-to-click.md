# Phase goal-desk-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-14 (Era B, Journey J-10 — coverage-index reconciliation)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- This iteration adds one new button, **"Reconcile Index"**, and one new read-only panel, **"Index
  Reconciliation"**, to the existing `/desk` page — no new page, no navigation change.
- Frontend running at `http://localhost:3301`. Backend running at `http://localhost:8301`. This is a
  **dedicated evidence rig for this iteration**, not the app's usual `:3000`/`:8000` — do not
  substitute those ports.
- At the time this guide was written, the frontend was still running but the backend was not — if
  `/desk` shows an amber "Backend unreachable" banner, restart the backend with:
  ```bash
  SCOPED_ROOT="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-14.154299/desk-iter14-scoped-qa"
  nohup bash apps/backend/scripts/goal-desk-iter9-scoped-backend.sh "$SCOPED_ROOT" 8301 > /tmp/backend.log 2>&1 &
  disown
  ```
  This restarts against the same saved data — nothing is lost.
- No login required.
- **This feature has likely already been exercised once** (by an earlier QA pass on this same rig)
  — so the Index Reconciliation panel may already show a recorded run rather than its empty
  placeholder when you first look. That is expected, not a bug; step 2 below covers both cases.
- **Do not click "Top-up" during this walkthrough** — it is a different feature, unrelated to
  reconciliation, and starts a real network fetch.

---

## Steps

1. Open `http://localhost:3301/desk` in your browser.
   - **Expect:** the "Desk" page loads, the top nav shows "Cockpit", "Structure", "Desk", and there
     is no red or amber error banner.

2. In the ranked table (the "Briefing" panel), look down the "coverage" column for any row with a
   mix of colored (lit) and gray (dark) small badges — note which symbol and which badge is dark, if
   any. If every badge is already lit, that's fine too — just skip to step 6.
   - **Expect:** most rows show 4 lit badges (`1h 4h 1d 1w`); at most one row may show one badge
     noticeably duller/grayer than its neighbors.

3. Scroll all the way to the bottom of the page.
   - **Expect:** a section titled "Index Reconciliation" — the very last thing on the page, right
     after "Top-up Runs". It most likely already shows a recorded run (a small table plus a "Latest
     run" summary line), not the empty placeholder — that's expected, since this feature has already
     been exercised once. (If it does read "No reconciliation run recorded yet.", that's the honest
     starting state — also correct, and already separately captured at
     `reports/qa/goal-desk-iter-14-evidence/TC-17-empty-reconciliation.png`.)

4. Scroll back up to the "Run Screen / Top-up / Reconcile Index" panel and click the **"Reconcile
   Index"** button.
   - **Expect:** the button may briefly read "Reconciling…" with a small pulsing dot, then returns to
     reading "Reconcile Index" within a few seconds. (It may complete too fast to see the
     "Reconciling…" moment at all — that's fine, this operation does no network calls.)

5. Scroll back down to "Index Reconciliation".
   - **Expect:** one more row than before appears in the run history table, and the "Latest run"
     line reads "state: done" with a "rows indexed: `X` before, `Y` after" count where `Y` is larger
     than `X`.

6. Click the **"Run Screen"** button.
   - **Expect:** a line appears reading "Recorded a new snapshot — screen-…" (NOT "Reused the
     snapshot already recorded for this key…" — if you see "Reused" here, flag it, since a genuinely
     new snapshot is expected after a reconciliation run).

7. Look at the ranked table's "coverage" column again, at the same row/badge you noted in step 2.
   - **Expect:** that badge is now lit, matching its neighbors — this is the whole point of the
     feature: a badge that was stuck wrong is now correct after Reconcile Index + a fresh Run
     Screen.

8. Scroll to "Screen History".
   - **Expect:** one new dated row was added (from step 6). Click any OTHER, older row — its own
     version of the badge from step 2 should still show its ORIGINAL (pre-repair) state, unchanged —
     proving old records are never rewritten, only new ones added. Click "Latest" to return.

9. Skim the rest of the page (Provenance, Skipped Members) from top to bottom.
   - **Expect:** everything else looks and behaves exactly as it did before this feature existed —
     nothing missing, nothing broken.

10. Confirm you never clicked "Top-up" anywhere during this walkthrough.
    - This is a reminder, not an action — Top-up is a separate feature and clicking it here would
      just add noise, not break anything.

---

## What "Working Correctly" Looks Like

- The Index Reconciliation panel shows either the honest "No reconciliation run recorded yet."
  message (before any run) or a real run record with "state: done" and a rows-indexed count that
  went up (after a run) — never a blank space, a stuck spinner, or raw JSON.
- Clicking "Reconcile Index" always returns to a usable "Reconcile Index" button within a few
  seconds — never stuck, never silently does nothing.
- A coverage badge that was dark for a genuinely-stored stock/timeframe becomes lit after
  Reconcile Index + a fresh Run Screen — and the OLDER screen snapshot's own badge stays exactly as
  it was, never silently rewritten.
- Every other part of `/desk` (Provenance, Briefing, Skipped Members, Screen History, Top-up Runs)
  looks and behaves exactly as it did before this update.

## If Something Looks Wrong

- **Amber "Backend unreachable" banner**: the scoped backend has stopped — restart it with the
  command in Prerequisites above; nothing is lost.
- **"Index Reconciliation" section is missing entirely, or is not the last section on the page**:
  hard refresh (Ctrl+Shift+R / Cmd+Shift+R) — a stale cached frontend build is the most common cause.
- **"Reconcile Index" button stays stuck on "Reconciling…" for well over a minute**: this is a real
  defect — the underlying operation does no network calls and should resolve in well under a minute.
- **Step 6 shows "Reused the snapshot already recorded for this key…" instead of "Recorded a new
  snapshot…"**: flag this — after a reconciliation repairs the index, a fresh Run Screen should
  always produce a genuinely new snapshot, not silently reuse an old one.
- **A previously-dark badge stays dark even after both Reconcile Index and a fresh Run Screen have
  completed**: this is the specific defect this whole feature exists to prevent — flag it.
- **Two evidence screenshots already exist** at
  `reports/qa/goal-desk-iter-14-evidence/TC-17-empty-reconciliation.png` and
  `TC-18-populated-reconciliation.png` from an earlier QA pass on this same rig. As saved, both are
  cropped to the top of the ranked table and do not actually show the Index Reconciliation section —
  if you are asked to confirm "the screenshots prove this works," check what they actually contain
  rather than assuming from the filenames alone.
