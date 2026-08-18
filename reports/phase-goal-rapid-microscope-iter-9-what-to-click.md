# Phase goal-rapid-microscope-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-9
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

**This is a regression pass plus one absence check, not a new-feature walkthrough.** This iteration
built the Validation Vault backend (`vault.py`: universe registration, the sealed → assigned →
exposed shard lifecycle, a new read-only `GET /research/desk/micro/vault` endpoint) but shipped zero
frontend changes — 5 backend Python source files (1 new) and 4 test files (1 new) only (confirmed
via `git status --porcelain`). `Frontend Present: yes` is declared solely to let the browser-testing
lane run the required-still-passing regression set and the kept-product sentinel. So instead of
clicking through something new, these steps mostly re-confirm the product's existing, already-shipped
surfaces still work — plus one check that a specific thing is still *missing*, on purpose.

**Two things to get right:**
1. Step 2 below expects to find **no** "Validation Vault" section anywhere on `/desk`. That is
   correct, not a bug — the Vault's UI section doesn't ship until a later iteration.
2. Step 3 expects **1 symbol-day / 2 datasets**, not the real store's 12/18 — the test rig only
   ever seeds 2 fixture datasets by design.

---

## Prerequisites

- Backend running at `http://localhost:8301`, pointed at the store-scoped rig (start via
  `apps/backend/scripts/start_scoped_qa_backend.sh` — not the real `.data/datasets` store)
- Frontend running at `http://localhost:3301`, ideally after a clean rebuild
  (`rm -rf apps/frontend/.next` then restart) to rule out a stale build
- No login required

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with the heading "Playbook Signals" visible, no error banner, no
     blank screen.

2. Scroll all the way to the bottom of the page, passing every section header on the way down
   - **Expect:** No section anywhere on the page is titled "Validation Vault" (also none titled
     "Scout Ledger" or "Walk-Forward"). This is expected, not a gap — that UI is not built yet. The
     very last section on the page is "Microscope Readiness".

3. Click the "Microscope Readiness" section header
   - **Expect:** A "Corpus Totals" table appears showing "Distinct symbol-days: 1" and "Distinct
     datasets: 2" (not 12/18 — this test rig only seeds 2 fixture datasets), followed by a "Legacy
     Tick Shards" table listing exactly 2 rows, both symbol `PG`, session date `2026-06-09`. Both
     rows' "Split provenance" column reads `hand_assigned` and "Exposure state" column reads
     `exploratory`. The table's column headers are unchanged from before this iteration — still
     Symbol, Session date, Feed, Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac,
     Checksum, Split provenance, Exposure state, with no new column added.

4. Open `http://localhost:3301/` (the cockpit page)
   - **Expect:** The text "No ticker watched" is visible

5. Type `SIM-BUYER` into the field labeled "Ticker", then click the "Watch" button
   - **Expect:** The text "Buyer Control" appears

6. Open `http://localhost:3301/structure`, type `AAPL` into the "Structure symbol" field, type
   `2026-06-22 17:00:00` into the as-of date field below it, then click the "Load" button
   - **Expect:** The text "300.11–302.2" appears (the pinned real support/resistance band for
     AAPL on that date)

7. Go back to `http://localhost:3301/desk`, click the "Playbook Evidence" section header, then
   type `2026-06-22` into its date field
   - **Expect:** The text "Built from signature:" appears when the section expands, and "recorded
     signals, none hidden" appears after typing the date

8. Click the "Referee Registry" section header
   - **Expect:** The text "config fingerprint 08e471b10130e1e2" appears

9. Click the "Referee Adjudications" section header, then the "Referee Runs" section header
   - **Expect:** "No hypotheses registered" appears for the first, "No evaluation runs recorded
     yet." appears for the second — both honest empty states, not errors

---

## What "Working Correctly" Looks Like

- Step 2's absence of a "Validation Vault" section is itself the correct, verified outcome this
  iteration — not something waiting to be fixed
- Every section that does expand shows real text or real table data within a second or two of
  clicking — never a spinner that never resolves, never a blank panel
- Step 3's Microscope Readiness table shows exactly 2 rows of real data (checksums, coverage gaps,
  fallback fractions all populated) — a small table is correct here, not a bug
- The two "honest empty state" sections in step 9 show their expected "no ... yet" sentences rather
  than an error message — an empty state here is correct, not a bug
- Nothing above should look different from prior iterations — this pass exists to prove the
  product is unchanged (plus the one absence check), not to find something new

## Common Issues

- **Blank page / error screen on `/desk`, `/`, or `/structure`**: check the backend is running and
  healthy — `curl http://localhost:8301/health` should return `{"status":"ok"}`
- **A "Validation Vault" section actually appears on `/desk`**: this would be a real, surprising
  finding this iteration did not intend — flag it rather than treat it as progress; it was not
  supposed to ship this iteration
- **Step 3 shows "Distinct symbol-days: 12" / "Distinct datasets: 18" or 18 shard rows**: the
  frontend is pointed at the real `.data/datasets` store, not the scoped rig — restart the backend
  via `apps/backend/scripts/start_scoped_qa_backend.sh`
- **Step 3 shows 0 rows or an empty table**: the scoped rig failed to seed — check the rig's own
  startup log before assuming a product regression
- **Step 6's band text ("300.11–302.2") doesn't appear**: try a hard refresh after confirming
  `apps/frontend/.next` was rebuilt clean — a stale cached build can mask a working backend
- **Nothing on this list is about a new button or new page** — if you're looking for one, there
  isn't one this iteration; that is expected, not a gap. This iteration's actual new capability
  (the Validation Vault backend and its `GET /research/desk/micro/vault` endpoint) is reachable
  only via a direct API call, not by clicking anything in the app.
