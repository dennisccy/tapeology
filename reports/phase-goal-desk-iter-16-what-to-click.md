# Phase goal-desk-iter-16 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-16
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable, serving the real ambient desk data store (no login required)
- No seed data needed — the real store already contains everything referenced below (as of
  2026-07-29): two recordings sharing the date `2026-07-27` (`screen-2026-07-27-936543601e75`
  recorded `2026-07-27T21:42:14.636275Z`, and `screen-2026-07-27-3ad3c57aa6ba` recorded
  `2026-07-28T21:30:16.111871Z`)

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with a "Desk" heading, no blank screen, no error panel

2. Scroll down to the "Screen History" panel and find the table's header row
   - **Expect:** A "recorded" column appears between "date" and "rows" — this column is new this
     iteration

3. In that table, find the two rows whose "date" column both read `2026-07-27` (they sit next to
   each other, a few rows up from the bottom)
   - **Expect:** Their "recorded" column values are DIFFERENT from each other (one reads
     `2026-07-27T21:42:14.636275Z`, the other `2026-07-28T21:30:16.111871Z`) — this proves two
     separate recordings share the same trading date

4. Click the `2026-07-27` row with the EARLIER "recorded" time (`2026-07-27T21:42:...`)
   - **Expect:** Only that row highlights (darker background); a banner reading "Viewing the
     recorded screen for 2026-07-27 — not the latest." appears with a "Latest" button; scroll up to
     the "Briefing" table and find the "NFLX" row — its "1d" coverage badge is dim/gray

5. Click the OTHER `2026-07-27` row (the LATER one, `2026-07-28T21:30:...`)
   - **Expect:** The highlight moves to this row only; the "NFLX" row's "1d" badge is now lit
     green/emerald — proving you just opened a genuinely different recording for the exact same
     trading date, which was impossible before this iteration

6. Scroll up to the "Provenance" panel
   - **Expect:** A "Snapshot id" row reads `screen-2026-07-27-3ad3c57aa6ba` and a "Recorded at" row
     reads `2026-07-28T21:30:16.111871Z` — both new rows this iteration, matching exactly the row
     you clicked in step 5

7. Click the "Latest" button in the banner above Provenance
   - **Expect:** The banner disappears; Provenance's "Snapshot id"/"Recorded at" revert to the
     store's most-recently-recorded snapshot; a small note reappears below Provenance's rows reading
     "This is the most recently recorded screen (by recorded-at time), not necessarily the latest
     screen date — an earlier same-date recording can still exist and be opened from Screen History
     below."

8. Scroll down to the "Top-up Runs" and "Index Reconciliation" panels
   - **Expect:** Both render their run tables/latest-run details normally, with NO amber
     "failed an integrity check" note anywhere — confirms the new disclosure code doesn't produce
     false alarms against clean data

---

## What "Working Correctly" Looks Like

- Two rows in Screen History can share the exact same "date" value while showing different
  "recorded" values, and clicking each one shows visibly different data (the NFLX `1d` badge flips
  between dim and lit) — previously, clicking either row always showed the same (newer) snapshot.
- The Provenance panel always names the EXACT recording on screen via its "Snapshot id" and
  "Recorded at" rows, which change every time you click a different Screen History row.
- The default-view note is honest about "most recently recorded" vs. "latest date" — it disappears
  the moment you're viewing a non-latest snapshot and reappears exactly when you return to "Latest".

## Common Issues

- **Both `2026-07-27` rows look highlighted together, or clicking either shows the same NFLX badge
  state**: the id-based selection fix did not ship — check that clicking calls
  `GET /research/desk/screen?id=`, not `?date=`.
- **Provenance panel has no "Snapshot id" / "Recorded at" rows**: the frontend build is stale — do
  a clean `.next` rebuild and restart the frontend (a known gotcha on this project, per prior
  iterations' notes).
- **An amber integrity-error note appears in step 8 against the real store**: unexpected — the
  ambient store currently has zero corrupted files; this would mean either a stray corrupt file was
  left behind by a previous test run, or the backend is pointed at a scoped/test data directory
  instead of `apps/backend/.data`. Check the backend's `TAPEOLOGY_DESK_SCREEN_DIR` /
  `TAPEOLOGY_DESK_TOPUP_LOG_DIR` / `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR` env vars.
- **Blank page / error screen**: check that the backend is running and reachable at the port the
  frontend's `NEXT_PUBLIC_API_URL` was built with.
