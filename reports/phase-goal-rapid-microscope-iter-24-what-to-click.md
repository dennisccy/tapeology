# Phase goal-rapid-microscope-iter-24 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-24
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Start the scoped QA rig (this seeds the fixture data these steps look for — the ordinary
  backend against an empty store will not show the same content):
  ```
  bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh <root_dir> 8301
  CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh
  ```
- Frontend running at `http://localhost:3301`
- No login required (no auth on this app)

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** Page loads, the text "Playbook Signals" is visible, no error screen

2. Scroll down and click the "Validation Vault" section header (near the bottom of the page)
   - **Expect:** The section expands and shows a table titled with columns including "Sealed at",
     "State", "Assigned at", "Exposed at"

3. Find the row whose "Universe" cell reads `iter18-qa-universe` and read its "Sealed at" column
   value
   - **Expect (what this iteration is supposed to deliver):** a plain date with no time attached,
     e.g. `2026-06-09`
   - **Watch for this instead (a known-risk defect this analysis flagged, not yet confirmed
     live):** a date one day earlier plus a time, e.g. `2026-06-08 20:00 ET`. If you see the
     second form, this is a real display bug — the backend now sends a bare date, but the page's
     date formatter still runs it through a timezone conversion meant for full timestamps, which
     silently shifts it back a day and reattaches a (wrong) time. **Report this exact string if
     you see it.**

4. In the same row, read the "Assigned at" and "Exposed at" columns
   - **Expect:** Both show a normal full date-time with a time and "ET", e.g. `2026-06-09 14:32
     ET` — these two fields were not changed this iteration, so they should look completely normal
     even if "Sealed at" (step 3) looks wrong. This contrast is the fastest way to confirm the bug
     is isolated to one column.

5. Find any row whose "State" column reads `sealed` (not `assigned`/`exposed`)
   - **Expect:** Every cell to the right of "State" for that row (Dataset, Family root, Symbol,
     Session date, Assigned at, Exposed at, Content checksum) reads exactly `sealed — opaque` —
     never a real symbol or date. This must still hold; it is the core privacy guarantee this
     iteration exists to protect.

6. Scroll up and click the "Scout Ledger" section header
   - **Expect:** The section expands and shows the text
     `failed_aggression_score__playbook_signal__trades_20` somewhere in the ledger content — this
     is a newly seeded test row proving the pilot-study screening pipeline ran for real

7. Refresh the page (press F5 or Cmd+R), then re-expand "Validation Vault" and "Scout Ledger"
   - **Expect:** Same data reappears in both sections — confirms nothing was accidentally written
     only to browser memory

---

## What "Working Correctly" Looks Like

- The "Sealed at" column shows a clean date like `2026-06-09` with no time-of-day component, on
  every row (sealed, assigned, and exposed alike).
- Still-sealed rows show `sealed — opaque` in every non-opaque-safe column — no leaked symbol or
  date.
- The Scout Ledger section shows the seeded pilot-study family id, not an empty state.

## If Something Looks Wrong

- **"Sealed at" shows a shifted date plus a time (e.g. `2026-06-08 20:00 ET`)**: this is the
  regression flagged by this analysis (see `reports/phase-goal-rapid-microscope-iter-24-user-
  visible-changes.md`) — the backend's new date-only value is being mis-formatted by the existing
  frontend timezone-conversion code. Report the exact string shown.
- **Blank page / error screen**: confirm both the scoped backend (port 8301) and frontend (port
  3301) are running, and that the rig script finished seeding without error (check its stdout for
  a non-zero exit).
- **Scout Ledger shows "No candidates ledgered." instead of the seeded family id**: confirm you
  started the scoped rig script (which runs the new seeder automatically) rather than pointing the
  frontend at an ordinary/ambient backend.
