# Phase goal-rapid-microscope-iter-19 — What to Click (Operator Verification Guide)

**Phase:** goal-rapid-microscope-iter-19
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable — for a faithful replay of the fixture-scoped QA rig, launch via `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (it seeds the tick-shard, Scout, and Walk-Forward fixture data these steps check, and writes `reports/qa-scoped-backend-store-manifest.md` recording which store it used)
- No login required

---

## Important context

This iteration shipped **no visible change** — every step below re-verifies existing `/desk`, `/`, and `/structure` behavior. The point of this pass is to confirm the app still looks and behaves exactly as before, after this iteration's test-harness-only changes (a new backend test module, four deepened regression scripts, and a QA launcher script that now also writes a report file).

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** Page loads, heading "Playbook Signals" is visible near the top, no error page

2. Scroll down and click the "Microscope Readiness" section header to expand it
   - **Expect:** Section opens (arrow flips from ▸ to ▾); a table row reads "Joinable corpus — withheld (excluded)" with a number next to it, and further down a table has a column header "Fallback frac"

3. Click the "Scout Ledger" section header to expand it
   - **Expect:** Section opens; the text "Ledger chain verification:" appears, followed by either "ok" or "failed at row N (...)"

4. Click the "Walk-Forward" section header to expand it
   - **Expect:** Section opens; the text "Ledger chain verification:" appears, followed by either "ok" or "failed at row N (...)"

5. Click the "Validation Vault" section header to expand it
   - **Expect:** Section opens; the text "iter18-qa-universe" is visible

6. Navigate to `http://localhost:3301/` (Cockpit home)
   - **Expect:** Page loads; text "No ticker watched" is visible

7. Type "SIM-BUYER" into the "Ticker" field, then click the "Watch" button
   - **Expect:** Text "Buyer Control" appears

8. Navigate to `http://localhost:3301/structure`
   - **Expect:** Page loads; heading "Tradable Map" is visible

9. Type "AAPL" into the "Structure symbol" field, type "2026-06-22 16:00:00" into the as-of field, then click the load button
   - **Expect:** Text "300.11–302.2" appears — this is the real, already-shipped AAPL wall example, unchanged by this iteration

10. Refresh `http://localhost:3301/desk` (press F5) and confirm the "Microscope Readiness", "Scout Ledger", and "Walk-Forward" headings are all visible but collapsed again
    - **Expect:** All three headings show a ▸ (collapsed) marker; no leftover expanded state, no console errors — confirms the page returns to its normal default view

---

## What "Working Correctly" Looks Like

- Every heading and expanded-section text above appears exactly as spelled out — no typos, no missing sections, no "could not be loaded" panels where real data is expected
- Nothing on the page looks or behaves differently from before this iteration — that is the correct outcome for this test-and-harness-only round

## Common Issues

- **A section shows "could not be loaded" / "No tick shards recorded." instead of the expected text**: the backend is not the fixture-seeded one — restart via `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` rather than a bare `start-backend.sh`, and check `reports/qa-scoped-backend-store-manifest.md` for which store roots the running backend is actually bound to
- **Blank page / error screen**: check that the backend is running (`curl http://localhost:8301/health` or the port your launcher printed)
- **`/structure` doesn't show "300.11–302.2"**: confirm you typed the as-of date exactly as `2026-06-22 16:00:00` (ET convention) and the symbol exactly as `AAPL`
