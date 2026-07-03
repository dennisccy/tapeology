# UI Test Results (merged)

**Date:** 2026-07-03
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 route-map leg — nav renders from `GET /meta/ui-routes` | functional/regression | P1 | Rendered top-bar links on `/`, `/journal`, `/studies` match the route map's `nav: true` entries exactly (Cockpit · Journal · Studies, no Performance); `/journal/[id]` keeps Journal active | Nav rendered exactly Cockpit/Journal/Studies (verbatim labels + hrefs from the endpoint) on all three pages, correct `aria-current="page"` per route, no `nav-unavailable` degraded state, no Performance link; `/journal/nonexistent-test-id` kept Journal active | PASS | `reports/qa/goal-tape_to_profit-iter-1-evidence/UT-J-01-*.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-03

