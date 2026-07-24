# UI Test Results (merged)

**Date:** 2026-07-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | Frontend + WS demolition — the two-page product | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-clean_slate-iter-3-evidence/J-02-verify.png |
| UT-J-05 | The kept product stands — regression sentinel (this iteration's scoped subset: sim cockpit settle + /structure Load wall band; Case Studies / full-suite-under-new-pin / diff-vs-inventory are out of scope until J-04/J-05's own iteration) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-clean_slate-iter-3-evidence/J-05-verify.png |
| UT-J-01 | Backend demolition with byte-identical relocations (Required-still-passing, regression scope: I-9 byte-comparison + full suite) | regression | P1 | Every I-1 route 404s; every OTHER kept route byte-identical to the J-01 baseline; full backend suite green; fingerprint unchanged at `4d665603569b9dbf`; T-12 greps clean | Independently re-verified: `/research/journal`, `/research/analytics`, `/research/studies` all return 404 (curl, live 8301); `runs/goal-session-clean_slate/iter-3/kept-route-after.txt` shows 0 of 28 kept routes differing vs iter-2's capture; full suite re-run fresh = 1164 passed / 7 skipped / 0 failed / 0 errors (1171 collected, exact match to dev handoff); fingerprint re-checked = `4d665603569b9dbf` (unchanged); browser sanity of `/` and `/structure` shows no visible regression | PASS | `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png` |
| UT-J-03 | MCP contract v2 — 15 read-only tools (target journey) | functional | P1 | MCP server advertises exactly the 15 I-6 tools; `journal`/`analytics`/`studies` gone from code and tests; `get_endpoint` on a deleted route surfaces the backend's honest 404; MCP test suite green | Independently re-verified: `grep -n '"journal"\|"analytics"\|"studies"' app/mcp/__init__.py tests/test_mcp_server.py` → zero hits; `grep -c 'types.Tool('  app/mcp/__init__.py` → exactly 15; fresh `pytest tests/test_mcp_server.py -v` → 29 passed, 0 failed (was 28 passed/1 failed pre-iteration per the iter spec's own baseline — the one pre-authorized red test is now green); `curl http://127.0.0.1:8301/research/journal` → 404 (the honest-404 the `get_endpoint` tool proxies verbatim, per the dev handoff's own direct `mcp.client.stdio` check); `curl http://127.0.0.1:8301/research/taxonomy` → 200, slimmed payload with `feed_basis` block intact (the kept MCP `taxonomy` tool's underlying route) | PASS | `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-24

