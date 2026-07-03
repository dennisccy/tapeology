# Goal Iteration goal-tape_to_profit-iter-1 — UI Test Results

**Phase:** goal-tape_to_profit-iter-1
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass -->
<!-- FAIL: Any smoke test fails, OR any happy-path test fails, OR any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/1 tests passed (0 skipped)

**Scope note:** Per dispatch instructions, this run tests **exactly J-01** (the browser-testable
"route-map leg" of it, per the iteration spec's Testing Requirements). J-08 is explicitly
excluded this run — it is re-verified by the deterministic replay script
`runs/goal-session-tape_to_profit/journey-scripts/J-08.json`, not by this agent. J-01's
non-browser acceptance items (stdio MCP client session, per-tool byte-identity, read-only/
allowlist guarantees, backend-down tool errors, MCP sync self-test) are automated/unit-test
territory owned by the developer/reviewer steps of this dispatch, not browser QA — they are out
of scope for this report and are not claimed as verified here.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 route-map leg — nav renders from `GET /meta/ui-routes` | functional/regression | P1 | Rendered top-bar links on `/`, `/journal`, `/studies` match the route map's `nav: true` entries exactly (Cockpit · Journal · Studies, no Performance); `/journal/[id]` keeps Journal active | Nav rendered exactly Cockpit/Journal/Studies (verbatim labels + hrefs from the endpoint) on all three pages, correct `aria-current="page"` per route, no `nav-unavailable` degraded state, no Performance link; `/journal/nonexistent-test-id` kept Journal active | PASS | `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-*.png` |

---

## Passed Tests

### UT-J-01 — J-01 route-map leg (canonical nav source)
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-cockpit-nav.png`
- `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-journal-nav.png`
- `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-studies-nav.png`
- `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-journal-detail-nav.png`

Steps executed (goal.md J-01 steps, browser-verifiable slice only):

1. **Fetched `GET http://localhost:8301/meta/ui-routes` directly (curl).** Response:
   `{"routes":[{"path":"/","label":"Cockpit","nav":true},{"path":"/journal","label":"Journal","nav":true},{"path":"/journal/[id]","label":"Journal detail","nav":false},{"path":"/studies","label":"Studies","nav":true}]}`
   — exactly the three live top-bar routes plus the honestly-non-nav journal-detail entry; no
   `/performance` entry (consistent with the anti-goal that the nav must never carry a dead
   link before J-05).
2. **Navigated to `/` (Cockpit).** DOM eval confirmed `[data-testid="app-nav"]` present,
   `[data-testid="nav-unavailable"]` absent, and exactly 3 `[data-testid="nav-link"]` elements
   with `data-label`/`href`/text = `Cockpit → /`, `Journal → /journal`, `Studies → /studies`
   — a verbatim match to the route map's `nav:true` entries. Cockpit carried
   `aria-current="page"`; the other two did not.
3. **Navigated to `/journal`.** Same 3-link set rendered verbatim; Journal carried
   `aria-current="page"`, Cockpit/Studies did not.
4. **Navigated to `/studies`.** Same 3-link set rendered verbatim; Studies carried
   `aria-current="page"`, Cockpit/Journal did not.
5. **Navigated to `/journal/nonexistent-test-id`** (no journal rows exist yet in this fresh
   session — `GET /research/journal` returns `{"rows":[]}` — so a synthetic id was used to
   exercise the pure client-side active-link rule, which matches on path prefix
   (`pathname.startsWith('/journal/')`) independent of whether the record exists). Same 3-link
   set rendered verbatim; Journal carried `aria-current="page"` — confirming the acceptance
   clause "`/journal/[id]` navigation still marks Journal active."

Across all four states: the link set was always exactly Cockpit/Journal/Studies (no more, no
fewer), no hardcoded-fallback artifacts and no degraded state appeared, and the labels/hrefs
were byte-identical to the `nav:true` entries returned by `GET /meta/ui-routes`. This confirms
the nav is now driven by the canonical route map, not the deleted hardcoded `NAV_ITEMS` list.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend (`http://localhost:3301`) and backend (`http://localhost:8301`) were both
confirmed live before testing; Chrome MCP was available throughout.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (offset dev port; frontend's `NEXT_PUBLIC_API_URL`
  confirmed pointed at this same port via the running `next dev` process env)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-1-evidence/`
- **Golden replay script written:** `runs/goal-session-tape_to_profit/journey-scripts/J-01.json`
  (self-contained goto/expect steps reproducing the four states above for future
  no-LLM regression replay)
