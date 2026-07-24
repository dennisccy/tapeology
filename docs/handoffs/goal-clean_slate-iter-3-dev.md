# goal-clean_slate-iter-3 Dev Handoff

**Phase:** goal-clean_slate-iter-3
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

J-03 (MCP contract v2 — 15 read-only tools), per goal.md's I-6 and the iter spec's IN SCOPE list.
Backend-only; no page, route, or REST response body changed.

- Removed the `journal`, `analytics`, `studies` `_STATIC_PATHS` rows and their matching
  `types.Tool` blocks from `app/mcp/__init__.py`'s `TOOLS` tuple — the MCP server now advertises
  exactly the 15 kept tools (`tape_state`, `tape_features`, `tape_history`, `datasets`, `bars`,
  `levels`, `tradability`, `setups`, `backtests`, `strategies`, `edge_report`, `pnl_ledger`,
  `taxonomy`, `ui_route_map`, `get_endpoint`). No reordering of the remaining 15 — a pure surgical
  deletion in place. `get_endpoint`'s `ALLOWED_GET_PREFIXES` allowlist and the module's
  zero-app-import, GET-only discipline are untouched.
- Updated `tests/test_mcp_server.py`: trimmed `EXPECTED_TOOLS` and `LIVE_STATIC` to match (removes
  the one pre-authorized red test carried since iter-1 — `test_static_live_tools_json_byte_
  identical_to_rest` was failing because the `journal` tool's `/research/journal` 404'd; it is now
  green because the dead row is gone from `LIVE_STATIC`, not because of any code change to the
  route itself).
- Added new test coverage `test_get_endpoint_proxies_a_deleted_route_404_verbatim` (a new
  `DELETED_RESEARCH_ROUTE = "/research/journal"` constant beside the existing
  `UNKNOWN_RESEARCH_PATH` canary): proves `get_endpoint`'s honest-404 contract holds for a path
  that WAS a real, shipped route and is now deleted (J-01), distinct from the pre-existing
  synthetic-canary coverage of a path that was never real. This is goal.md's own named J-03
  acceptance example.
- Re-ran the I-9 kept-route byte-comparison capture and wrote
  `runs/goal-session-clean_slate/iter-3/kept-route-after.txt` — **0 of 28 kept `/research` +
  `/tape` + `/meta` routes differ** from `runs/goal-session-clean_slate/iter-2/kept-route-after.txt`
  (not even the two already-sanctioned J-01/J-02 diffs recur as NEW diffs — every row is
  byte-identical, confirming J-03 touched zero route/store/serialization code).

## Files Changed

- `apps/backend/app/mcp/__init__.py` -- removed 3 `_STATIC_PATHS` rows + 3 `types.Tool` blocks
  (`journal`, `analytics`, `studies`); nothing else in the file touched.
- `apps/backend/tests/test_mcp_server.py` -- trimmed `EXPECTED_TOOLS` (18→15) and `LIVE_STATIC`
  (removed the 3 dead rows); added `DELETED_RESEARCH_ROUTE` constant + one new test function
  (`test_get_endpoint_proxies_a_deleted_route_404_verbatim`).
- `runs/goal-session-clean_slate/iter-3/kept-route-after.txt` -- new I-9 byte-comparison capture
  (28 rows), diffed against iter-2's capture in its header comment.
- `runs/goal-clean_slate-iter-3/status.json` -- `current_step: dev_complete`.

## Tests Run

Command (from `README.md`'s verified "How to run" section — `.claude/project-template.md` is
currently unfilled, a pre-existing framework-sync gap unrelated to this iteration):
`cd apps/backend && .venv/bin/python -m pytest tests/ -v`

Result: **1164 passed, 7 skipped, 0 failed, 0 errors** (1171 collected — exactly +1 vs the
1170-collected/1-failed pre-iteration baseline, matching the iter spec's TC-10 expectation: one
new test function added, zero test files added or removed, the one pre-authorized red test now
green).

Sequence followed (TDD, deletion-shaped):
1. Edited the test file first (`EXPECTED_TOOLS`/`LIVE_STATIC` trim + new test) — confirmed RED:
   `pytest tests/test_mcp_server.py -v` → 2 failed (`test_advertised_tool_set_is_exactly_
   capability_6`, `test_stdio_session_end_to_end` — both assert against `EXPECTED_TOOLS`, which no
   longer matched the still-18-tool code), 27 passed, 29 collected (the new test already passing —
   it exercises pre-existing honest-404 behavior, not this iteration's code diff).
2. Edited `app/mcp/__init__.py` to delete the 3 tool entries — confirmed GREEN:
   `pytest tests/test_mcp_server.py -v` → 29 passed, 0 failed.
3. Ran the full backend suite — 1164 passed, 7 skipped, 0 failed, 0 errors.

Additional keyless checks (all passed):
- `python -c "from app.config import Config; print(Config().config_fingerprint())"` →
  `4d665603569b9dbf` (unchanged; zero of the 13 I-9 pin sites are in either touched file, so this
  iteration cannot and did not move the pin — T-3 respected).
- `grep -n '"journal"\|"analytics"\|"studies"' app/mcp/__init__.py tests/test_mcp_server.py` →
  zero hits (TC-11: deletion is complete in the two files this journey owns).
- `grep -rn "app\.mcp\|from \.mcp" apps/backend/app/main.py apps/backend/app/research/*.py
  apps/frontend` → zero hits (TC-12: `app/mcp/` has zero importers outside its own package,
  confirming this iteration's diff cannot touch J-02's browser/frontend surface — no browser
  re-walk needed for J-03 itself).
- Live spot-check against a real running instance (not just pytest): started the backend via
  `scripts/dev.sh` (port 8301, launched with cwd=`apps/backend` so `journal_db_path_resolved()`
  reads the same dev-mode `apps/backend/tapeology_journal.db` iter-2's capture used), then (a)
  `curl http://127.0.0.1:8301/research/journal` → 404, and (b) spoke real MCP-over-stdio to
  `python -m app.mcp` via `mcp.client.stdio` — `list_tools()` returned exactly the 15 expected
  names, no `journal`/`analytics`/`studies`.

## Pre-handoff verification

- Service startup: `bash scripts/dev.sh` — backend (`/health` → `{"status":"ok"}`) and frontend
  (`GET /` → 200) both came up cleanly on port 8301/3301. Stopped everything (had to kill a
  lingering `next-server` grandchild process directly by PID after `pkill -f "next dev -p 3301"`
  missed it — the wrapper `npm`/`sh -c` layer had already exited, orphaning the actual
  `next-server` process under a different command-line signature), then started again — no port
  conflicts on the restart. All tapeology server processes killed before finishing this handoff
  (confirmed via `ss -tln` and `ps aux` — ports 8301/3301 free, zero tapeology uvicorn/next
  processes remain; the only tapeology processes still running are the outer goal-mode pipeline
  harness itself, not a server I started).
- No native-dependency or external-integration verification needed — this iteration adds no new
  dependency and touches no external adapter.

## Known Issues

- **Tool order vs. goal.md prose (pre-logged, not a new finding).** The iter spec's own NOTES
  section pre-authorized this: goal.md's I-6 prose enumerates the resulting 15 tools as `...,
  strategies, pnl_ledger, taxonomy, edge_report, ...`, but the surgical in-place deletion (no
  reordering, per core.md's Surgical Changes principle) leaves the code's pre-existing natural
  order `..., strategies, edge_report, pnl_ledger, taxonomy, ...` — same 15-item set, membership
  identical, order differs among those 3 names only. `TC-1` in the iter spec itself already lists
  the code-order sequence, and `tests/test_mcp_server.py::test_advertised_tool_set_is_exactly_
  capability_6` explicitly asserts no MCP consumer depends on `list_tools()`'s ordinal position
  (word-scan over write verbs, not position). No action needed; flagging for the reviewer's
  awareness only, per the already-logged `assumptions.md` entry (`iter-3 — goal-decomposer`).
- **Byte-comparison capture reads the real accumulated dev-mode store**, not an isolated fixture —
  same precedent iter-1/iter-2 established (`journal_db_path` is cwd-relative; `dataset_dir`/
  `bar_dir` are package-anchored absolute paths, so only the journal DB choice matters). Launched
  identically to iter-2 (`scripts/dev.sh`, cwd=`apps/backend`) specifically to keep this capture
  comparable; if a future iteration launches the backend from a different cwd, the
  `research.backtests.list`/`research.pnl_ledger` rows will show a launch-cwd artifact again (as
  they did between iter-1 and iter-2) — not a code regression, per the same root-cause already
  documented in iter-2's own capture file.
- No out-of-inventory findings this iteration — the diff is exactly the two files the iter spec
  named, plus the run-dir capture artifact it explicitly asked for. Nothing contradicted the
  Demolition inventory (no T-14 stop-the-line trigger).
