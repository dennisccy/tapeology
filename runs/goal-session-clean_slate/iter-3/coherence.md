# Iteration 3 — Coherence Audit

**Iteration:** goal-clean_slate-iter-3
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

J-03 is a lean, backend-only, no-frontend iteration whose entire scope is deleting 3 dead MCP tool
proxies (`journal`, `analytics`, `studies`) whose target REST routes were already 404'd by J-01/J-02,
plus one new regression test that asserts the honest-404 contract for an actually-deleted route. The
diff touches exactly `apps/backend/app/mcp/__init__.py` and `apps/backend/tests/test_mcp_server.py` —
confirmed against `git diff 8d3e74ed513ff10fac235516d1592bea0036e337 --stat` (which also surfaces a
third file, `README.md`; see Note below). This matches the iter spec's own "UI surface changes: None"
/ "New information displayed: None" / "Data-contract additions: None" fields verbatim.

## Data Contract check

Every MCP tool that survives this iteration still points at its already-registered blueprint
endpoint, byte-unchanged. Verified by reading the post-diff `_STATIC_PATHS` dict
(`apps/backend/app/mcp/__init__.py:87-105`): `datasets→/research/datasets`, `bars→/research/bars`,
`backtests→/research/backtests`, `strategies→/research/strategies`, `pnl_ledger→/research/pnl/ledger`,
`taxonomy→/research/taxonomy`, `ui_route_map→/meta/ui-routes`, `setups→/research/setups`,
`edge_report→/research/edge-report` — every one matches the "Served by" column of
`runs/goal-session-clean_slate/state/blueprint.md`'s Data Contract table verbatim. `tape_state` /
`tape_features` / `tape_history` (`_TAPE_PATHS`), `levels`, and `tradability` are untouched by this
diff (only their neighboring dict/tuple entries moved as deletions occurred around them).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| journal (removed proxy) | OK — deletion only, no replacement, no Data Contract row (already gone in J-01/J-02) | `apps/backend/app/mcp/__init__.py` diff hunk @83-88, @172-186 (removed) |
| analytics (removed proxy) | OK — deletion only, same as above | same hunks |
| studies (removed proxy) | OK — deletion only, same as above | same hunks |
| datasets/bars/backtests/strategies/pnl_ledger/taxonomy/ui_route_map/setups/edge_report (surviving proxies) | OK — unchanged canonical source, confirmed against current `_STATIC_PATHS` | `apps/backend/app/mcp/__init__.py:87-105` (post-diff read) |
| honest-404-for-a-deleted-route (new test, not a displayed value) | OK — asserts MCP `get_endpoint` output is byte-identical to the REST 404 it proxies; reinforces the single-source rule rather than violating it | `apps/backend/tests/test_mcp_server.py:174-186` |

No new function, service, endpoint, or client-side computation was added anywhere in the diff — every
hunk in `apps/backend/app/mcp/__init__.py` is a deletion (`-` lines only, confirmed against the
bounded diff and the file's current contents). The one new test function
(`test_get_endpoint_proxies_a_deleted_route_404_verbatim`) calls the pre-existing `get_endpoint` tool
against a path and cross-checks it with a direct `httpx.get` to the same backend — it does not
introduce a second way of computing or serving anything. No new displayed value is introduced (none of
this is user-facing — no page, no page changed).

## Information Architecture check

No new page, route, or feature. The MCP surface's blueprint home was already "(MCP tool surface; no
page)" with nav section "—", and this iteration only shrinks its tool catalog — it does not add a
route or alter `app/meta.py` ROUTES, so there is nothing new to check for a nav path, reachability,
duplicate home, or parallel shell.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| MCP tool catalog (journal/analytics/studies removed) | OK — no page exists or is claimed for this surface; blueprint's IA table already lists it as `*(MCP tool surface; no page)* \| —` | `runs/goal-session-clean_slate/state/blueprint.md` (IA table) — no nav/router file touched by this diff |

Confirmed via `git diff --stat`: no file under `apps/frontend/` appears anywhere in the 3-file diff
(`README.md`, `apps/backend/app/mcp/__init__.py`, `apps/backend/tests/test_mcp_server.py`), so no
nav/sidebar/router component was touched.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s change in this diff range is not iter-3 product work — it is the prior iteration's
  showcase/README-maintainer commit (`21d19d6 chore(goal): iter 2 showcase artifacts`), which landed
  between the captured snapshot SHA and this iteration's working-tree edits, so it appears in the
  `git diff <snapshot-sha>` window even though iter-3 itself never touched it (confirmed:
  `git log 8d3e74ed5..HEAD --oneline` shows exactly that one intervening commit; `git status` shows
  `README.md` clean, only `apps/backend/app/mcp/__init__.py` and `apps/backend/tests/test_mcp_server.py`
  are modified in the working tree). Its content is documentation-only (capability bullets, page count,
  route list) and is consistent with the blueprint's two-page target IA — no action needed.
- Nothing else to note; this is a clean, surgical demolition matching its spec exactly.
