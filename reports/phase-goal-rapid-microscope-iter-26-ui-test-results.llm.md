# Phase goal-rapid-microscope-iter-26 — UI Test Results

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- SKIPPED: backend unreachable throughout the QA window; frontend was up but every /desk
     surface this test plan targets depends on live backend data and rendered explicit
     "Backend unreachable — is the API running?" banners instead of content. -->

**Overall:** 0/6 tests passed (6 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders without error message; "Playbook Signals" visible; both section headers visible collapsed; no console errors | Page shell rendered but showed "navigation unavailable — backend unreachable" banner near the nav, "Backend unreachable — is the API running?" banners in the Screen Runs, Playbook Signals, and Back-Scan Runs sections | SKIP | `reports/qa/goal-rapid-microscope-iter-26-evidence/UT-01-skip-backend-unreachable.png` |
| UT-02 | Microscope Readiness renders byte-identical figures (J-01) | regression | P1 | Corpus Totals figures match registered J-01 baseline (2 symbol-days, 3 datasets, 1.75 RTH minutes, 0.0045 session-equivalents, 150 referee tick-gate) | Could not be evaluated — section's data comes from `GET /research/desk/micro/readiness`, and the backend serving that route was unreachable for the full QA window | SKIP | none |
| UT-03 | Scout Ledger renders byte-identical family rows (J-08) | regression | P1 | Ledger chain verification reads `ok`; family headers/trial-row columns unchanged | Could not be evaluated — same backend-unreachable condition | SKIP | none |
| UT-04 | Band-touch value stable across repeat expand/refresh | regression | P1 | Identical band-touch value across expand/collapse/re-expand and full-page refresh | Could not be evaluated — same backend-unreachable condition | SKIP | none |
| UT-05 | Corrupted cache degrades to a full miss, never an error | error | P3 | HTTP 200 with freshly-computed value even with a corrupted cache file | Not executed — test plan itself marks this operator/shell-only, not a pure-browser check, and the backend was down for the entire window regardless | SKIP | none |
| UT-06 | Both sections discoverable from a fresh page load | ux | P2 | Clicking "Desk" nav link navigates to `/desk`; both section headers visible as real `<button>` elements | Not executed — same backend-unreachable condition would make any content-based verification (section headers still render as buttons regardless of backend, but the test's purpose — confirming a working page — is moot under a backend outage) unreliable to grade | SKIP | none |

---

## Skipped Tests

### UT-01 — `/desk` loads without errors
**Verdict:** SKIPPED
**Reason:** Backend unreachable. `curl http://localhost:8301/health` returned no response (curl exit code for connection-refused, HTTP code `000`) across 19 polling attempts spanning roughly 3 minutes (attempts at time of first check, then repeated polls at 5s/8s/10s intervals). The backend's own log (`/home/dennis-chan/.cache/iad/iad.goal-rapid-m-dca68098.1873421/fanout-backend-8301.log`) shows a clean shutdown sequence ("Shutting down. Waiting for application shutdown. Application shutdown complete. Finished server process") with no restart recorded afterward, and no `uvicorn` process was found running (`ps aux | grep uvicorn` returned nothing). Live navigation to `http://localhost:3301/desk` confirmed the frontend itself is up (HTTP 200, page shell renders, nav and section headers present) but every data-bearing panel shows "Backend unreachable — is the API running?" or "navigation unavailable — backend unreachable" instead of real content. Per agent instructions, browser-qa-agent must not restart or debug the app — this is recorded as SKIPPED, not FAIL, since it is an infrastructure/environment precondition failure external to this iteration's code, not a defect surfaced by exercising the iteration's changes.

### UT-02 — Microscope Readiness renders byte-identical figures (J-01)
**Verdict:** SKIPPED
**Reason:** Same backend-unreachable condition as UT-01. This section's entire acceptance bar (byte-identical Corpus Totals / Sealed Tranche / Legacy Tick Shards figures) requires live data from `GET /research/desk/micro/readiness`, which the frontend itself reported as unreachable. Fabricating or reusing stale figures to force a PASS would violate the "no invented results" rule.

### UT-03 — Scout Ledger renders byte-identical family rows (J-08)
**Verdict:** SKIPPED
**Reason:** Same backend-unreachable condition as UT-01. Ledger chain verification and pilot-study family rows require live Scout Ledger data from the backend, which was unreachable.

### UT-04 — Band-touch value stable across repeat expand/refresh
**Verdict:** SKIPPED
**Reason:** Same backend-unreachable condition as UT-01. The entire premise of this test (comparing a cached vs. recomputed band-touch value across expand/collapse cycles and a full-page refresh) requires a working backend round-trip; with the backend down, every attempt would show the same "Backend unreachable" banner rather than a real value, giving no meaningful signal either way.

### UT-05 — Corrupted band-touch cache degrades to a full miss, never an error
**Verdict:** SKIPPED
**Reason:** The test plan itself scopes this as P3/informational, requiring backend host filesystem access outside what a browser-only QA pass can exercise, and expects it to be covered by an automated (non-browser) test rather than manual QA. Independently, the backend was also unreachable for the full QA window, so even the browser-observable half of this check (confirming HTTP 200 + a normal-looking panel) could not be exercised.

### UT-06 — Both touched sections are discoverable from a fresh page load
**Verdict:** SKIPPED
**Reason:** Same backend-unreachable condition as UT-01. While the nav-click-to-`/desk` mechanic and the presence of the two section header `<button>` elements are DOM-level and technically independent of backend availability, the test's purpose is to confirm a genuinely working page state, and the page was in a degraded "Backend unreachable" state throughout — verifying only the button/DOM shape without the actual section content would not honestly represent this test's intent, so it is recorded as SKIPPED rather than a partial/manufactured PASS.

---

## Notes for the goal-mode evaluator

- This is an **environment/infrastructure failure**, not a code regression surfaced by this
  iteration's changes: the backend process was not running at all (confirmed via `/health`
  connection-refused and an absent `uvicorn` process), so no test in this plan — happy-path,
  regression, or otherwise — could exercise this iteration's actual `micro_readiness.py` /
  `micro_join.py` / `micro_routes.py` changes through the browser.
- No golden replay scripts were written this run for J-01 or J-08 because no journey passed
  browser verification this iteration — nothing to record as a fresh, verified replay.
- Per the dispatch instructions, the Required-still-passing journeys (J-02, J-03, J-04, J-05,
  J-06, J-09, J-10) were already re-verified via the deterministic replay lane before this
  browser-qa dispatch ran and are not affected by this backend outage (that replay presumably
  ran, or was recorded, while the backend was reachable, or targets a different lane — this
  browser-qa-agent did not re-drive or evaluate those).
- Recommend the goal-mode pipeline confirm/restart the backend service before re-dispatching
  browser-qa for J-01/J-08, since a full QA window (multiple polling attempts across roughly
  3 minutes) elapsed with no self-heal observed.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (unreachable throughout this QA run — `/health` returned no response / connection refused)
- **Browser:** Chrome via MCP (headless, attached to CDP port 9222)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-26-evidence/`
