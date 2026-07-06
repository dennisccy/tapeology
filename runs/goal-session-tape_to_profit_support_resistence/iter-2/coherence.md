# Iteration 2 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-2
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

Backend-only, machine-surface iteration (Frontend Present: no). Reviewed diff vs snapshot
`37d3ad23077dc27f7e5e2dfbe4533dafbd94081f`: `apps/backend/app/config.py`,
`apps/backend/app/mcp/__init__.py`, `apps/backend/app/research/routes.py`,
`apps/backend/tests/test_mcp_server.py`, `README.md` (tracked, via `git diff`), plus new
untracked files `apps/backend/app/research/levels.py`, `apps/backend/tests/test_levels.py`,
`apps/backend/tests/test_levels_api.py` (read directly — untracked files don't appear in
`git diff`). `apps/frontend/` diff is empty (confirmed via targeted `git diff --stat`), matching
the iteration spec's "no UI change" scope. The ui-surface-map report confirms "No UI surfaces
affected."

## Data Contract check

Blueprint Row 39 ("Support/resistance levels + A/B/C confluence classes") registers the single
owner (a NEW S/R + confluence module) and single endpoint (`GET /research/levels` + MCP
`levels`). This iteration ships the **levels half** of that row (classes/J-03 explicitly out of
scope, per both the iter spec and the blueprint's own "classes field absent, additive-only"
note).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| S/R levels (price, timeframe, type, touch_count, strength) | OK | Computed once in `apps/backend/app/research/levels.py:166` (`compute_levels`) — confirmed the only definition and only call site (`apps/backend/app/research/routes.py:1652`). Served by exactly one route, `GET /research/levels` (`apps/backend/app/research/routes.py:1636-1637`), and proxied byte-identically by the MCP `levels` tool (`apps/backend/app/mcp/__init__.py:190` tool declaration, `:297` dispatch branch), which builds a query string against the same REST path (`_LEVELS_PATH = "/research/levels"`, line 107) rather than recomputing anything client-side. |
| `no_bar_series_for_symbol` honesty flag | OK (not a new contract value) | An additive boolean on the same registered `levels` response (`apps/backend/app/research/levels.py:172-176`), following the existing `insufficient_sample`-style honesty-flag precedent already used elsewhere in the blueprint — not a new business entity, so no separate registration is owed. |
| S/R config parameters (`sr_pivot_lookback`, `sr_touch_tolerance_bps`, `sr_timeframe_weights`) | OK | Config-only inputs (not a displayed value), correctly added to the `config_fingerprint()` `excluded` set (`apps/backend/app/config.py:1305-1319`) per the iter-1 lesson; grep confirms no other module reads or duplicates these fields. |
| Naming collision check (carried iter-1 advisory) | OK — resolved | New fields use a distinct `sr_*` namespace (`apps/backend/app/config.py:1074-1108`), confirmed via grep to be disjoint from the existing unrelated tape-setup fields `level_break`/`failed_move_fade` (`apps/backend/app/config.py:487-488`). No field-name or JSON-key collision between the two "level" concepts. |

No duplicate computation, no non-canonical source, no unregistered new value found.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/levels` + MCP `levels` | OK | Machine surface only — no nav entry needed or added. The blueprint's Information Architecture already lists this exact canonical home at baseline ("J-02 support/resistance levels \| API `GET /research/levels` + MCP `levels` \| machine"), and the nav skeleton (Cockpit · Journal · Studies · Performance) is explicitly unchanged this era. `git diff --stat -- apps/frontend/` against the snapshot is empty — no parallel shell, no new page, nothing to reach from navigation. |

No new page/route requiring a nav path was introduced; nothing to flag.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None.
