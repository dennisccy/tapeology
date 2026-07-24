# Phase goal-clean_slate-iter-3 — UI Test Results

**Phase:** goal-clean_slate-iter-3
**Date:** 2026-07-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

---

## Methodology note (read before the table)

This run's scope was **J-01, J-03** (J-02 and J-05 are covered separately this iteration by
deterministic golden replay — see `reports/phase-goal-clean_slate-iter-3-regression-replay-results.md`,
already PASS for both). Both J-01 and J-03 are marked **`(Keyless; automated.)`** in `docs/goal.md`'s
own "Must-have user journeys" section, and the iteration spec (`docs/phases/goal-clean_slate-iter-3.md`)
states explicitly under TESTING REQUIREMENTS: **"Browser: none. J-03 is backend-only/keyless... J-01's
regression check is the I-9 kept-route re-capture (backend/curl-based, TC-8)."** Neither journey's Steps
or Acceptance line describes any page, click path, or DOM state — J-01's acceptance is route-404s +
byte-identical-route-comparison + full pytest suite + a `python -c` fingerprint check; J-03's acceptance
is the MCP tool list + a `get_endpoint` proxy call + the MCP pytest suite (MCP is a stdio process, not a
browser surface — `app/mcp/` has zero importers in `app.main`/frontend, confirmed live below).

Given that, this run did two things, both genuinely executed (not merely re-stated from the dev handoff):

1. **Independently re-verified J-01/J-03's actual (keyless) acceptance criteria myself**, from scratch,
   rather than trusting `docs/handoffs/goal-clean_slate-iter-3-dev.md`'s self-report — fresh `pytest`
   invocations, fresh `curl` calls, a fresh `python -c` fingerprint check, and fresh `grep`s. Every number
   matched the dev handoff exactly (see Evidence below), which is itself the independent confirmation.
2. **Used Chrome MCP** (as the dispatch instructed) to browser-sanity-check the two KEPT pages (`/` and
   `/structure`) for visible regression, since J-01/J-03's backend-only diff could in principle have broken
   a kept route a page depends on. Both render cleanly with no visible defect. This is not a test of J-01
   or J-03's own acceptance (which has no browser component) — it is due-diligence evidence toward the
   session's overarching Success Criterion #1 ("nothing kept regresses"), and is reported as a supplement,
   not conflated with the journeys' actual keyless acceptance.

**No golden replay scripts were written for J-01/J-03.** The replay schema's three action types
(`goto`/`click`/`fill`) have no meaningful mapping onto "delete 3 MCP tool rows, run pytest" or "curl 28
routes and hash-compare them" — there is no browser interaction to script. Writing a `goto`-only script
that merely loads `/` would not actually regression-test either journey's real acceptance condition, so
per the agent instructions' "best-effort... skip if you cannot produce one," both are skipped for golden
scripts. (J-02 and J-05 already have golden scripts from a prior run, unaffected.)

**One environment observation, not a product defect:** this session's own `mcp__tapeology__*` tool
connections are bound to the default `http://localhost:8000`, not this goal-session's offset backend
port (`8301`), so my own live MCP calls (`get_endpoint`, `ui_route_map`) errored with a connection
failure rather than exercising the real 8301 server. This is a harness/config binding on my side, not a
regression — the dev handoff's live MCP-over-stdio check (`python -m app.mcp` spoken to directly via
`mcp.client.stdio`, correctly targeting the running 8301 instance) already exercised the real product
contract, and my own curl-based checks against `127.0.0.1:8301` (below) independently corroborate the
same facts through a different path.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backend demolition with byte-identical relocations (Required-still-passing, regression scope: I-9 byte-comparison + full suite) | regression | P1 | Every I-1 route 404s; every OTHER kept route byte-identical to the J-01 baseline; full backend suite green; fingerprint unchanged at `4d665603569b9dbf`; T-12 greps clean | Independently re-verified: `/research/journal`, `/research/analytics`, `/research/studies` all return 404 (curl, live 8301); `runs/goal-session-clean_slate/iter-3/kept-route-after.txt` shows 0 of 28 kept routes differing vs iter-2's capture; full suite re-run fresh = 1164 passed / 7 skipped / 0 failed / 0 errors (1171 collected, exact match to dev handoff); fingerprint re-checked = `4d665603569b9dbf` (unchanged); browser sanity of `/` and `/structure` shows no visible regression | PASS | `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png` |
| UT-J-03 | MCP contract v2 — 15 read-only tools (target journey) | functional | P1 | MCP server advertises exactly the 15 I-6 tools; `journal`/`analytics`/`studies` gone from code and tests; `get_endpoint` on a deleted route surfaces the backend's honest 404; MCP test suite green | Independently re-verified: `grep -n '"journal"\|"analytics"\|"studies"' app/mcp/__init__.py tests/test_mcp_server.py` → zero hits; `grep -c 'types.Tool('  app/mcp/__init__.py` → exactly 15; fresh `pytest tests/test_mcp_server.py -v` → 29 passed, 0 failed (was 28 passed/1 failed pre-iteration per the iter spec's own baseline — the one pre-authorized red test is now green); `curl http://127.0.0.1:8301/research/journal` → 404 (the honest-404 the `get_endpoint` tool proxies verbatim, per the dev handoff's own direct `mcp.client.stdio` check); `curl http://127.0.0.1:8301/research/taxonomy` → 200, slimmed payload with `feed_basis` block intact (the kept MCP `taxonomy` tool's underlying route) | PASS | `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png` |

---

## Passed Tests

### UT-J-01 — Backend demolition with byte-identical relocations (regression scope)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png`

- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8301/research/journal` → `404`
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8301/research/analytics` → `404`
- `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8301/research/studies` → `404`
- `runs/goal-session-clean_slate/iter-3/kept-route-after.txt` header: "Diff vs
  `runs/goal-session-clean_slate/iter-2/kept-route-after.txt`: 0 of 28 lines differ" — read and confirmed
  directly, all 28 rows present including `research.backtests.list`, `research.pnl_ledger`,
  `research.levels.aapl_pinned`, `meta.ui-routes`.
- Fresh, from-scratch `cd apps/backend && .venv/bin/python -m pytest tests/ -q` run by me (not reused from
  the dev handoff): captured raw progress-character tally = **1164 `.` (passed), 7 `s` (skipped), 0 `F`
  (failed), 0 `E` (error)**, 1171 total — exit code 0. Byte-identical to the dev handoff's self-reported
  count, independently reproduced.
- `.venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"` →
  `4d665603569b9dbf` (T-3: zero of the 13 pin sites touched this iteration, as expected — J-01/J-03 don't
  own any of them).
- Browser sanity (Chrome MCP): navigated to `http://localhost:3301/` — nav renders exactly "Cockpit" /
  "Structure", cockpit idle state ("No ticker watched") renders cleanly, no console/DOM error. Navigated
  to `http://localhost:3301/structure` — page renders fully (Tradable Map, Edge Report "not computed yet"
  honest state, Fetch bars, Registry showing `v1`/`structure_tape`/`structure_tape_map`, Comparison
  section) — all of these read from kept routes (`research.tradability`, `research.edge_report`,
  `research.strategies`, `research.backtests`) that this journey's I-9 byte-comparison already proved
  unchanged. No visible regression.

### UT-J-03 — MCP contract v2 — 15 read-only tools
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-cockpit.png`, `reports/qa/goal-clean_slate-iter-3-evidence/J-01-J-03-sanity-structure.png`

- `grep -n '"journal"\|"analytics"\|"studies"' apps/backend/app/mcp/__init__.py apps/backend/tests/test_mcp_server.py`
  → zero hits (exit code 1) — confirmed myself, not just cited from the handoff.
- `grep -n 'types.Tool(' apps/backend/app/mcp/__init__.py` → exactly 15 matches (lines 139, 147, 155, 172,
  181, 190, 210, 230, 243, 252, 261, 275, 284, 289, 297).
- Fresh `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -v` run by me → **29
  passed, 0 failed** in 6.98s — includes the previously-red `test_static_live_tools_json_byte_identical_to_rest`
  (now green, per the iter spec's TC-3) and the new `test_get_endpoint_proxies_a_deleted_route_404_verbatim`
  coverage (TC-4).
- `curl http://127.0.0.1:8301/research/journal` → `404` — the exact honest-404 body `get_endpoint` proxies
  verbatim per the dev handoff's own live `mcp.client.stdio` check (which I did not re-run myself due to a
  local MCP-client port binding to `:8000` instead of this session's `:8301` — see Methodology note above;
  the curl-level check against the real running instance corroborates the same fact through a different
  path).
- `curl http://127.0.0.1:8301/research/taxonomy` → `200`, body begins
  `{"feed_basis":{"feeds":[{"id":"sim","name":"Simulated"},{"id":"iex","name":"IEX (live)"},...` — the
  slimmed payload the kept `taxonomy` MCP tool proxies, `feed_basis` block intact (T-5 respected).
- Browser sanity: same two screenshots as UT-J-01 above — `/structure`'s Registry/Comparison sections
  (which read `research.strategies` and `research.backtests`, both proxied by kept MCP tools of the same
  names) render with no visible defect, corroborating that the MCP-layer-only diff touched nothing a user
  would see.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://127.0.0.1:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-24
- **Evidence directory:** `reports/qa/goal-clean_slate-iter-3-evidence/`
- **Independently re-run commands:** `pytest tests/test_mcp_server.py -v`, `pytest tests/ -q` (full
  suite), `python -c "from app.config import Config; print(Config().config_fingerprint())"`, `grep`
  (tool-identifier absence, `types.Tool(` count), `curl` (deleted routes' 404s, slimmed taxonomy)
