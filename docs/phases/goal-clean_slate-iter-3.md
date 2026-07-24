# Goal Iteration 3 — MCP contract v2, 15 read-only tools (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** clean_slate
- **Iteration:** 3
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-05 (both scoped to backend/keyless checks this iteration — J-02 is intentionally not re-walked in a browser; see NOTES for the code-isolation proof)
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(This era's one sanctioned exception, operator-approved 2026-07-23: the journal/studies/performance product surfaces are REMOVED outright — never mutated-in-place — and their historical records stay readable; nothing else moves.)* *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **No research-value change beyond the documented epoch bump.** Every number a KEPT surface serves (levels, bands, touch events, edge cells, pnl rows) stays byte-identical on identical inputs; the ONLY sanctioned change is the `config_fingerprint` value itself, moved once via the J-04 Path B journey; cross-epoch pooling is forbidden forever. *(critical)*
  - **Deletion is complete, never cosmetic.** No orphaned imports, dead components, unreachable routes, dangling MCP tools, or skipped tests survive; a deleted surface is gone from code, routes, nav, MCP, types, and tests alike — grep-provably. *(critical)*
  - **No new features.** This era ships zero new product capabilities, pages, endpoints, strategies, or Config fields; anything new belongs to the next eras. *(critical)*
  - **Relocations are moves, not rewrites.** `r_basis` and the dataset-source constants keep byte-identical behaviour at their new homes; every kept caller's output is proven unchanged. *(critical)*
  - **Never modify the charts beyond the one named edit.** No commit in this era may edit `StructureChart.tsx` at all, or edit `PriceChart.tsx` beyond removing its thesis-geometry overlay build (I-7 chart clause); the three chart guard suites must pass byte-unmodified; any other chart diff — visual or behavioral — is a veto-class defect. *(critical)*
  - **Never touch a historical record.** No commit in this era may delete, rewrite, truncate, or re-stamp journal.db's existing rows or tables, any PnL-ledger row, anything under `docs/goal-archive/` or `runs/goal-session-*`, or any `reports/goal-session-*-delivered.md` — a diff touching any of these is a veto-class defect (deleting CODE is the mandate; deleting RECORDS is forbidden). *(critical)*
  - **No guard weakening.** `test_no_execution_path.py`, the source-introspection guards, and every kept test stay as written; the fingerprint pins change ONLY inside J-04 per Path B, never to make a red test green. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth (or PnL-ledger) acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Close the MCP tool catalog to exactly the 15 read-only tools goal.md's I-6 specifies — remove the `journal`/`analytics`/`studies` proxy entries whose backend routes already 404 (deleted in J-01/J-02) — so `tests/test_mcp_server.py`'s one pre-authorized red test goes green and every remaining MCP tool keeps serving byte-identical proxied JSON.

## BACKGROUND

Iteration 2 (full depth) landed J-02, independently re-verified by the evaluator (18/18 browser QA screenshots personally opened, coherence COHERENCE-PASS). Its Next-Step Recommendation explicitly targets **J-03 at lean depth** — the next step in goal.md's own J-01→J-02→J-03→J-04→J-05 dependency order (rubric rule 3: J-03 is the unblocker that finally closes the one pre-authorized red test both J-01 and J-02 deliberately left untouched). **Depth lean is justified** per the Picking-depth rubric's own triggers, none of which fire here: J-03 does not cross the backend/frontend boundary (re-verified this planning pass — `grep -rn "app\.mcp\|from \.mcp" apps/backend/app/main.py apps/backend/app/research/*.py apps/frontend` returns zero hits; the MCP module is a separate stdio process, never imported by the FastAPI app or the frontend), is explicitly marked `(Keyless; automated.)` in goal.md (not browser-verifiable), and is small/mechanical — exactly 6 edit sites across 2 files, independently confirmed via Read/Grep this planning pass (3 rows in `app/mcp/__init__.py`'s `_STATIC_PATHS`, 3 `types.Tool` blocks in its `TOOLS` tuple; the mirrored 3+3 rows in `tests/test_mcp_server.py`'s `EXPECTED_TOOLS`/`LIVE_STATIC`). The prior evaluator returned `CONTINUE` (not `ESCALATE`), and the last coherence verdict was `COHERENCE-PASS` (not `COHERENCE-FAIL`), so this is normal next-scope work, not a consolidation pass.

Two `lessons.md` entries apply directly and were both checked live this planning pass: (1) iter-1's lesson names J-03 by name as the journey allowed to touch `test_mcp_server.py`'s one red case — re-confirmed still red, same cause, via an isolated run (`pytest tests/test_mcp_server.py -q` → 28 passed, 1 failed: `test_static_live_tools_json_byte_identical_to_rest` asserts `rest.status_code == 200` for the `journal` tool's `/research/journal`, which is a 404). (2) iter-2's lesson calls for grepping `apps/backend/tests` for `read_text()`/`open(` references to a deletion target *before* deleting, to catch uncatalogued source-introspection guards; that grep was run this planning pass (`grep -rn "read_text\|open(" tests/*.py | grep -i mcp`) — the only hit is `test_mcp_server.py`'s own `test_server_source_performs_only_gets_and_imports_no_app_modules` (it reads its own file's source; unaffected by which tool names remain in it), so no surprise guard-test trap exists for this journey.

For the first time since iter-1 opened the transient red test, "full backend suite passes (0 failed)" becomes a literal claim again after this iteration, not one read "modulo the pre-authorized MCP test" (per `assumptions.md`'s `iter-1 — goal-evaluator` entry).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/mcp/__init__.py`: remove the 3 `_STATIC_PATHS` rows `"journal": "/research/journal"`, `"analytics": "/research/analytics"`, `"studies": "/research/studies"` (currently lines 86-88), and the 3 corresponding `types.Tool(name="journal", ...)` / `name="analytics"` / `name="studies"` blocks from the `TOOLS` tuple (currently lines ~175-189) — I-6. Keep the remaining 15 tools in their current relative order (a minimal, surgical diff — no reordering; see NOTES for a cosmetic order difference vs. goal.md's I-6 prose enumeration, logged to `assumptions.md`). `get_endpoint`'s `ALLOWED_GET_PREFIXES` and the module's zero-app-import, GET-only discipline are untouched.
- [ ] `apps/backend/tests/test_mcp_server.py`: remove the matching 3 rows from `EXPECTED_TOOLS` (currently lines 53-55) and from `LIVE_STATIC` (currently lines 82-84, leaving `taxonomy` and `ui_route_map` as the two live no-argument static tools) — I-6 step 2.
- [ ] `apps/backend/tests/test_mcp_server.py`: add coverage that `get_endpoint` against a route that WAS real and is now deleted (`/research/journal`) surfaces the backend's actual 404 verbatim (`isError=True`, `content[0].text` byte-identical to the real 404 body, `content[1].text == "HTTP 404 from GET /research/journal"`) — this is goal.md's own named example in J-03's acceptance text, distinct from the pre-existing coverage of a path that was *never* real (`UNKNOWN_RESEARCH_PATH`, a synthetic canary).
- [ ] Re-run the I-9 kept-route byte-comparison capture (`sha256(curl -s <base><route>)` for every kept `/research`+`/tape`+`/meta` GET) against `runs/goal-session-clean_slate/iter-2/kept-route-after.txt`; write the new capture to `runs/goal-session-clean_slate/iter-3/kept-route-after.txt`. Expect zero new diffs beyond the two already-sanctioned ones (`research.taxonomy` from J-01, `meta.ui-routes` from J-02) — J-03 does not touch `routes.py`, so no kept route's served body can change.

### New user-facing capability
None — this iteration only trims a machine (MCP) interface's tool catalog; no page, route, or REST response body changes.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None. J-03 has no page — `blueprint.md`'s Information Architecture already lists its home as "(MCP tool surface; no page)".

### Product surface delta
The MCP tool catalog shrinks from 18 to the 15 tools of I-6; every kept tool keeps proxying byte-identical REST JSON. No REST route, WS frame, or frontend surface changes — nothing a browser user would ever see is different.

### Blueprint conformance
No new surfaces. `blueprint.md`'s Information Architecture already lists J-03's home as `*(MCP tool surface; no page)* | —` — no edit required this iteration.

### Data-contract additions
None. J-03 introduces no new displayed value. Every MCP tool this iteration touches either (a) keeps proxying an already-registered Data Contract row unchanged (`taxonomy`, `ui_route_map`, and every other surviving tool), or (b) removes a proxy of a value already deleted from the Data Contract in J-01/J-02 (`journal`/`analytics`/`studies` had no Data Contract row even before this iteration — their owning modules/routes were already gone).

## OUT OF SCOPE

- J-04 (Config field deletion + the `config_fingerprint` epoch bump, all 13 I-9 pin sites) — strictly deferred to iteration 4 (T-3 pin discipline). `test_mcp_server.py` carries no fingerprint pin site (confirmed: none of the 13 I-9 sites are in this file), so J-03 has nothing to touch there regardless.
- J-05's full sentinel close (Case Studies drill-in, full-suite-green-under-the-new-pin, cumulative diff-vs-inventory cross-check) — depends on J-04; out of scope here. This iteration only advances J-05's step-3 "MCP = 15 tools" surface-inventory sub-clause (TC-9), nothing else of J-05.
- Reordering any of the 15 surviving tools beyond deleting the 3 dead rows in place — unnecessary diff for zero functional benefit (surgical-change principle); see NOTES/assumptions.md.
- Any edit to `app/mcp/__init__.py`'s module docstring or result-contract prose (the "datasets at (era-3) J-02, backtests at J-03, pnl_ledger at J-04..." commentary is pre-existing historical documentation using an EARLIER era's own J-numbering, unrelated to this journey) — not touched.
- `app/research/routes.py`, `app/main.py`, or any REST route body — untouched; J-03 only edits the MCP layer, a separate process that imports nothing from `app`.
- Any research-value computation module (`levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`, `backtests.py`, `datasets.py`, `bars.py`, `strategies.py`, `profiles.py`, `pnl_ledger.py`, `taxonomy.py`) — none are touched; the MCP tools proxying them are unchanged.
- Re-rendering neutral-source framework assets (`project-extensions/mcp-servers.yaml`, `.mcp.json`, `sync-cli-assets`, the MCP self-test) — verified NOT required this iteration: grepped `project-extensions/mcp-servers.yaml`, `.mcp.json`, and `incredible_auto_dev/policy/mcp-servers.yaml` for the tool identifiers `"journal"`/`"analytics"`/`"studies"` and found zero hits; those files only wire the "tapeology" server as a whole, never enumerate its individual tool names. If execution discovers this is wrong, stop and escalate rather than silently re-rendering (see NOTES).
- Restoring `SHOW_CASE_STUDIES` on `/structure` — unrelated pre-existing flag; still pending for whoever plans J-05.
- Schema migrations or any edit to `_migrate`/`_create_schema`/`journal.db` tables — untouched (T-4; not this journey's concern).

## DEFINITION OF DONE

- [ ] J-03 passes: the MCP server advertises exactly the 15 tools of I-6 (`tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`, `levels`, `tradability`, `setups`, `backtests`, `strategies`, `pnl_ledger`, `taxonomy`, `edge_report`, `ui_route_map`, `get_endpoint`); `journal`/`analytics`/`studies` are gone from `_STATIC_PATHS`, `TOOLS`, `EXPECTED_TOOLS`, and `LIVE_STATIC` alike (keyless/automated evidence per goal.md's own J-03 tag — no browser-qa dispatch needed for the target journey itself)
- [ ] Every kept tool's output stays byte-identical to its curl equivalent on the running backend, including the already-slimmed `taxonomy`
- [ ] `get_endpoint` against an ACTUALLY-deleted route (`/research/journal`) surfaces the backend's honest 404 verbatim, `isError=True`, with the explicit `"HTTP 404 from GET /research/journal"` message
- [ ] `get_endpoint`'s allowlist (`/tape/`, `/research/`, `/meta/`) and the module's read-only (GET-only, zero-app-import) discipline are unchanged
- [ ] `tests/test_mcp_server.py` passes in full — 0 failed (closes the one pre-authorized red test carried since iter-1)
- [ ] Required-still-passing: J-01's I-9 kept-route re-capture shows zero new diffs beyond the two already-sanctioned ones; J-05's scoped "MCP = 15 tools" surface-inventory sub-clause now holds
- [ ] No anti-goal violation introduced (rail 8 read-only MCP; rail 6 single source of truth; "deletion is complete, never cosmetic"; "no guard weakening"; "no new features")
- [ ] Zero fingerprint pin sites touched (T-3); `python -c "from app.config import Config; print(Config().config_fingerprint())"` still prints `4d665603569b9dbf`
- [ ] Full backend suite passes: 0 failed, 0 errors (literally, not "modulo" any known residual failure — the first iteration since iter-1 where this is true)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-clean_slate-iter-3-dev.md`

## TESTING REQUIREMENTS

- Browser: none. J-03 is backend-only/keyless per goal.md's own journey marking; no page is touched (`blueprint.md`: "MCP tool surface; no page"). J-01's regression check is the I-9 kept-route re-capture (backend/curl-based, TC-8); J-05's scoped subset re-verified this iteration is also backend/keyless (TC-9). J-02's browser surface is deliberately not re-walked this iteration — TC-12 proves the code-isolation reason why.
- Unit/integration: `tests/test_mcp_server.py` in full (TC-1 through TC-6); the fingerprint-pin zero-touch check (TC-7); the I-9 byte-comparison re-capture (TC-8); the full backend suite (TC-10); the tool-identifier grep (TC-11).
- Error cases: `get_endpoint` against a route that WAS real and is now deleted (`/research/journal`) must surface the backend's actual 404 body + explicit status message, never a synthesized or cached response (TC-4); the pre-existing "backend down → every tool raises `BackendUnreachableError` explicitly" coverage (iterates `EXPECTED_TOOLS` generically) must keep passing unmodified now that the tuple has shrunk.

Test-first contract:

- TC-1: given `_STATIC_PATHS` and `TOOLS` in `app/mcp/__init__.py` drop the `journal`/`analytics`/`studies` entries, when `await list_tools()` runs, then it returns exactly 15 `types.Tool` objects whose names are `tape_state, tape_features, tape_history, datasets, bars, levels, tradability, setups, backtests, strategies, edge_report, pnl_ledger, taxonomy, ui_route_map, get_endpoint` with no `journal`/`analytics`/`studies` present.
- TC-2: given `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` is updated to the same 15-name tuple, when `pytest tests/test_mcp_server.py::test_advertised_tool_set_is_exactly_capability_6 -q` runs, then it reports 1 passed, 0 failed.
- TC-3: given `LIVE_STATIC` drops `journal`/`analytics`/`studies` (leaving `taxonomy` and `ui_route_map`), when `pytest tests/test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest -q` runs, then it reports 1 passed, 0 failed — the one pre-authorized red test carried since iter-1 is now green.
- TC-4: given a test call to `call_tool("get_endpoint", {"path": "/research/journal"})` against the live test backend, when the call executes, then `result.isError is True`, `result.content[0].text` is byte-identical to `httpx.get(f"{backend}/research/journal").content`, and `result.content[1].text == "HTTP 404 from GET /research/journal"` — proving the honest-404 contract holds for an actually-deleted route, not only the pre-existing synthetic canary path.
- TC-5: given every remaining kept tool's existing byte-identity tests (`tape_*`, `datasets`, `bars`, `levels`, `tradability`, `setups`, `backtests`, `strategies`, `edge_report`, `pnl_ledger`, `taxonomy`, `ui_route_map`) are unmodified in substance, when `pytest tests/test_mcp_server.py -q` runs in full, then it reports 0 failed (up from 28 passed / 1 failed pre-iteration).
- TC-6: given `get_endpoint`'s allowlist and the module's read-only discipline are untouched, when `pytest tests/test_mcp_server.py::test_allowlist_prefixes_are_exactly_the_canonical_read_surface tests/test_mcp_server.py::test_server_source_performs_only_gets_and_imports_no_app_modules -q` runs, then both report passed — confirms I-6's "`get_endpoint` allowlist unchanged" clause and the module's zero-app-import invariant both hold after the edit.
- TC-7: given none of the 13 I-9 fingerprint pin sites live inside `app/mcp/__init__.py` or `tests/test_mcp_server.py`, when `python -c "from app.config import Config; print(Config().config_fingerprint())"` runs before and after this iteration's diff, then both print the identical `4d665603569b9dbf` (T-3: zero pins touched).
- TC-8: given the I-9 byte-comparison protocol's per-journey cumulative capture (`runs/goal-session-clean_slate/iter-2/kept-route-after.txt`), when every kept `/research`+`/tape`+`/meta` GET route is re-captured (sha256 of its raw body) at J-03's end and written to `runs/goal-session-clean_slate/iter-3/kept-route-after.txt`, then the diff shows zero new differences beyond the two already-sanctioned ones (`research.taxonomy`, `meta.ui-routes`) — proving `routes.py`, and therefore every kept route's served body, is untouched by this MCP-layer-only journey.
- TC-9: given J-05's step-3 surface-inventory cross-check names "MCP = 15 tools" as one of its clauses, when the MCP tool list is inspected after this iteration (TC-1), then it reads exactly the 15 I-6 names — this specific clause of J-05 (still `partial` pending J-04 for full closure) now holds for the first time.
- TC-10: given the full backend suite collected 1170 tests across 76 files pre-iteration (verified via `pytest tests/ -q --collect-only` at planning time) with exactly 1 failed pre-iteration, when `pytest tests/ -v` runs after this iteration's diff, then it reports 0 failed, and no test FILE is added or removed (the collected-test count changes by at most +1, matching TC-4's new coverage if implemented as a new test function rather than a parametrize extension).
- TC-11: given a grep for the MCP tool identifiers `"journal"`, `"analytics"`, `"studies"` scoped to `apps/backend/app/mcp/__init__.py` and `apps/backend/tests/test_mcp_server.py`, when the grep runs after this iteration's diff, then it returns zero hits in both files (T-1/T-12 — this grep is deliberately scoped to those two files, not the whole repo, since it must not flag the legitimately-kept `JournalStore`/`journal.db`/`journal_db_path` identifiers elsewhere).
- TC-12: given `app/mcp/` is verified to have zero importers outside its own package (`grep -rn "app\.mcp\|from \.mcp" apps/backend/app/main.py apps/backend/app/research/*.py apps/frontend` returns zero hits), when this iteration's diff is inspected, then it touches only `apps/backend/app/mcp/__init__.py` and `apps/backend/tests/test_mcp_server.py` — proving J-02's browser-verified frontend/WS surface is code-isolated from this iteration and does not need re-walking in a browser.

## NOTES

- **Assumption logged** (`runs/goal-session-clean_slate/state/assumptions.md`, entry `iter-3 — goal-decomposer`): goal.md's I-6 prose lists the resulting 15 tools in the order `..., strategies, pnl_ledger, taxonomy, edge_report, ...`, but surgically deleting the 3 dead rows in place (no reordering, per core.md's Surgical Changes principle) leaves the code's natural order `..., strategies, edge_report, pnl_ledger, taxonomy, ...` — the identical 15-item set, sequenced differently among those 3 names only. Read as a membership spec, not an order mandate (no MCP consumer depends on `list_tools()`'s ordinal position). Reversible: yes, a one-line reorder if ever desired.
- **Framework re-render confirmed unnecessary this iteration** (goal.md J-03 step 3's condition): grepped `project-extensions/mcp-servers.yaml`, `.mcp.json`, and `incredible_auto_dev/policy/mcp-servers.yaml` for the 3 tool identifiers — zero hits; these files only wire the "tapeology" server as a whole. If execution discovers a framework asset DOES reference these tool names by name, stop and surface it (T-14) rather than silently re-rendering or improvising a bigger change — that would cross into the render pipeline and likely warrant escalating to full depth, per iter-2's eval Next-Step Recommendation.
- **J-02 deliberately excluded from Required-still-passing** (TC-12 is the proof): `app/mcp/__init__.py` is a separate stdio process that imports nothing from `app` and is imported by nothing in `app.main` or the frontend — this iteration's diff cannot touch J-02's browser surface. Per the goal-decomposer rubric's own allowance ("you need NOT re-list journeys unrelated to this iteration's surface every time"), J-02 is not re-walked in a browser this iteration; it remains covered by iter-2's own evidence and the periodic full-regression pass.
- **`SHOW_CASE_STUDIES = false`** (`apps/frontend/app/structure/page.tsx:335`, carried forward again, unrelated to J-03): still unresolved — restore vs. operator rescopes J-05's "Case Study drill-in" acceptance clause — before J-05 can close. Not touched this iteration.
- **Required-still-passing scoping recap.** J-01 has no browser component (its own acceptance is keyless/automated) — its regression check this iteration is the I-9 byte-comparison re-capture (TC-8) plus the full suite (TC-10). J-05 is included per the session's established precedent (iter-1, iter-2) of tracking goal.md's "guarding continuously" sentinel even while `partial` — its regression check this iteration is scoped to exactly the one clause this iteration's diff can affect (TC-9); J-05's OTHER acceptance clauses (Case Studies, full-suite-under-the-new-pin, cumulative diff-vs-inventory) stay out of scope until J-04/J-05's own iteration.
