# goal-desk-iter-0 Dev Handoff

**Phase:** goal-desk-iter-0
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is Era B "The Desk"'s verify-only baseline (Mode: baseline, Depth:
lean). Per the spec's BACKGROUND section: "the developer step is a no-op for code; all the value
comes from the browser-QA step exercising every journey and a static probe of the current tree."
My scope was the non-browser half of that probe: live route/config/test-suite verification
against the current codebase plus a scratch backend/frontend, recording evidence for J-01–J-03,
J-06, and J-07's non-browser half, and confirming the decomposer-authored `blueprint.md` already
satisfies its DoD item. Browser-dependent evidence for J-04, J-05, and J-07's kept-behavior
walkthrough is explicitly deferred to the browser-qa-agent step (T-10: no screenshot ⇒ `unknown`,
never `passing`).

**No source file was created, modified, or deleted this iteration.**

```
$ git status --short -- apps/
(empty)
$ git diff --stat -- apps/
(empty)
$ git status --short
?? docs/phases/goal-desk-iter-0.md
?? reports/goal-session-desk-index.html
?? runs/goal-session-desk/
```

All three untracked entries are pipeline/session artifacts written by the goal-decomposer before
this developer step ran (the iter spec itself, the session state directory including the
already-drafted `blueprint.md`, and a rendered session index) — not product source. This confirms
TC-10 and the DoD's "no anti-goal violation introduced" item directly.

## Journey-by-journey verification evidence

Live checks ran against a scratch dev-stack instance (`scripts/start-backend.sh` /
`scripts/start-frontend.sh`, this project's deterministic port-hash offset: backend `:8301`,
frontend `:3301`, frontend rebuilt clean per T-9 — `rm -rf apps/frontend/.next` before starting)
plus direct source-tree grep. Every spec baseline prediction (J-01–J-06 failing/not-started,
J-07's kept-behaviors intact) was **confirmed on every point checked**.

### J-01: Universe ingestion — CONFIRMED FAILING (not started)

- TC-1: `GET /research/desk/universe` (live) → **404**. Supporting:
  `grep -rin desk apps/backend/app apps/frontend/app apps/frontend/components` → zero matches
  anywhere in source; no `desk_universe.py` under `apps/backend/app/research/`; no
  `apps/backend/tests/fixtures/*universe*`; no `.data/universe/` directory (`.data/` contains only
  `bars`, `datasets`, and the existing accelerator DBs).
- TC-2: `grep -n "desk_universe_source_url\|desk_universe_min_members\|desk_universe_max_members"
  apps/backend/app/config.py` → no matches. A broader `grep -n desk apps/backend/app/config.py`
  also returns nothing — none of J-01's Path-A Config fields exist yet.
- Extra: `POST /research/desk/universe/fetch` (live, the J-01 fetch-route name guess) → **404** —
  no desk router is registered at all yet, at any sub-path.

### J-02: Coverage + top-up — CONFIRMED FAILING (not started)

- TC-3: `GET /research/desk/coverage` (live) → **404**; `POST /research/desk/universe/topup`
  (live, top-up route name guess) → **404**. `bar_index.py` confirmed used only as an internal
  FastAPI dependency (`get_bar_index`) inside existing bars routes — no dedicated REST route
  exists yet to reuse or duplicate.

### J-03: The screen — CONFIRMED FAILING (not started)

- TC-4: `GET /research/desk/screen` (live) → **404**. No `desk_screen.py` under
  `apps/backend/app/research/`. Extra: `POST /research/desk/screen` (live) → **404**.

### J-04: The `/desk` briefing page — CONFIRMED FAILING (not started); browser evidence deferred

- TC-5 (non-browser half): `GET /meta/ui-routes` (live) →
  `{"routes":[{"path":"/","label":"Cockpit","nav":true},{"path":"/structure","label":"Structure","nav":true}]}`
  — exactly 2 entries. `GET /desk` against the frontend (live, port 3301, post clean `.next`
  rebuild) → **404** (Next.js's own not-found response; no `apps/frontend/app/desk/` directory
  exists).
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the actual nav-bar
  screenshot proving exactly "Cockpit · Structure" renders, and a screenshot of `/desk`'s honest
  not-found page.

### J-05: Ledger history + `/structure` drill-in — CONFIRMED FAILING (not started); browser evidence deferred

- TC-6 (non-browser half): `grep -n "useSearchParams\|searchParams"
  apps/frontend/app/structure/page.tsx` → no matches — no query-param prefill logic exists.
  `GET /structure?symbol=AAPL&asof=2026-06-22` (live frontend) → **200** (page loads; the URL
  params are inert with no code to read them).
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the screenshot proving
  the Load form actually renders EMPTY (no prefill, no auto-Load) despite the query params being
  present in the URL — that requires visual confirmation of client-side render state, not just an
  HTTP 200.

### J-06: MCP contract v3 — CONFIRMED FAILING (not started, still the 15-tool contract)

- TC-7: `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` tuple (line 49) has exactly 15
  entries ending in `get_endpoint`; neither `desk_universe` nor `desk_screen` appears.
  Cross-checked against `apps/backend/app/mcp/__init__.py`'s `_STATIC_PATHS` dict (9 static-path
  tools: `datasets`, `bars`, `backtests`, `strategies`, `pnl_ledger`, `taxonomy`, `ui_route_map`,
  `setups`, `edge_report`) + the 3 tape-path tools (`tape_state`, `tape_features`, `tape_history`)
  + the 2 parameterized tools (`levels`, `tradability`) + `get_endpoint` = 15, matching
  `EXPECTED_TOOLS` exactly. `test_mcp_server.py`'s full suite (29 tests, all passed per the suite
  run below) includes the write-verb / read-only-argument assertions — still green under the
  current 15-tool contract.

### J-07: Kept-product regression sentinel — KEPT-BEHAVIOR HALF CONFIRMED; desk-completion clauses not yet satisfiable; browser walkthrough deferred

Non-browser evidence (dev-level):

- Full backend suite: **1169 passed, 7 skipped, 0 failed, 0 errors, 2 warnings, 122.00s
  (0:02:02), exit 0** (1176 collected) — green, and matches `docs/goal.md`'s cited era-open
  baseline ("1169 pass / 7 skip") exactly, with zero drift. See Tests Run below for the skip
  breakdown.
- `config_fingerprint` (live-recomputed, not just grepped): `08e471b10130e1e2` — matches the
  pinned value exactly.
- `GET /research/taxonomy` (live) → **200**, kept surface unaffected.
- `GET /` and `GET /structure` (live frontend, post clean `.next` rebuild) → both **200**.
- Every one of the KEEP-surface backend route families (`datasets`, `bars`, `levels`,
  `tradability`, `setups`, `backtests`, `strategies`, `edge-report`, `pnl`, `profiles`, `taxonomy`,
  etc.) has its own passing test file in the suite run above (e.g. `test_strategies_api.py`,
  `test_profiles_api.py`, `test_pnl_ledger_api.py`, `test_tradability_api.py`,
  `test_levels_api.py` all green) — used as supporting evidence that the kept surfaces are intact
  rather than re-probing each with a redundant live GET.
- **Desk-completion clauses NOT YET satisfiable** (by design, per the spec's own BACKGROUND
  framing): `docs/goal.md`'s J-07 acceptance text requires "nav = exactly three routes" and
  "MCP = exactly 17 tools" — today's live state is 2 routes / 15 tools (see J-04/J-06 above),
  which is the honest, expected state before J-04/J-06 ship. This is not a regression of the kept
  product; it is the not-yet-built half of J-07's full-era acceptance text.
- **Not verified by me this iteration** (browser-qa-agent's step, T-10): the `SIM-BUYER` cockpit
  walkthrough (settling `buyer_control`, `PriceChart` candles + timeframe switch + S/R band
  overlay + live tape bar), `/structure` Load for the pinned AAPL `2026-06-22` as-of date (the
  300–302.4 wall band on `StructureChart`), a Case Study drill-in, and the Edge Report section's
  honest state — all require an active WebSocket-driven watch session and visual confirmation, not
  a GET probe.

## `blueprint.md` (DoD item — already drafted, not by me)

`runs/goal-session-desk/state/blueprint.md` already existed when this developer step started
(goal-decomposer-authored, same iteration-0 dispatch). Verified it satisfies TC-11: the
"Information Architecture" section's navigation skeleton lists the 3-route TARGET nav (Cockpit
`/`, Structure `/structure`, Desk `/desk` explicitly marked "[NEW, this era — not yet built]"),
and the "Data Contract" section carries both the unchanged-owner table (14 rows, one per kept
canonical value from `docs/goal.md`'s Product Shape) and a "New rows this era" table with exactly
5 desk-owned rows (universe snapshots/membership, per-member coverage/freshness, screen
snapshots/rank/skip rows, top-up/screen compute progress, the 3-row route list), each with exactly
one named owner module and one serving endpoint. Not edited — already correct on inspection.

## Files Changed

- (none — verify-only baseline; zero source modifications under `apps/`)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1169 passed, 7 skipped, 2 warnings in 122.00s (0:02:02). Exit code 0.** (1176 collected.)

Skip breakdown (all three are the standard two-stage `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in gates,
not credential failures — expected and honest for an autonomous, keyless run):
- `tests/test_event_recording_integration.py` (1)
- `tests/test_live_integration.py` (1)
- `tests/test_yahoo_live_integration.py` (5)

Zero failures, zero errors. The two warnings are pre-existing library deprecation notices
(`starlette.testclient` httpx usage; `websockets.legacy`), unrelated to this iteration (no code
touched).

`config_fingerprint` (direct python, not from the suite):
`cd apps/backend && .venv/bin/python -c "from app.config import Config; print(Config().config_fingerprint())"`
→ `08e471b10130e1e2` — matches the pinned value exactly.

## Service startup verification

- `scripts/start-backend.sh` (port 8301) and `scripts/start-frontend.sh` (port 3301, after
  `rm -rf apps/frontend/.next` per T-9) both started clean: backend `/docs` → 200 within ~6s,
  frontend root → 200 within ~1.2s ("Ready in 1196ms"). No `error`/`EADDRINUSE` in either boot
  log.
- Stopped both via `pkill` + port-based `fuser -k -9 <port>/tcp`; the first pass left a residual
  `next dev` parent + `next-server` child alive despite the port showing free via `lsof` (the
  documented `next dev` child-process gotcha — a parent-PID-only or port-only kill can miss
  grandchild workers); a second explicit `kill -9` on the discovered PIDs cleaned up fully. Final
  state confirmed via `ps aux` — no `uvicorn`/`next dev`/`next-server` process remains, ports
  `8301`/`3301` fully free.

## No side effects (baseline hygiene)

- Every live probe this iteration was a **read-only GET or a 404-only POST against a
  non-existent route** (`/docs`, `/research/desk/universe`, `/research/desk/coverage`,
  `/research/desk/screen`, `/research/desk/universe/fetch`, `/research/desk/universe/topup`,
  `/meta/ui-routes`, `/research/taxonomy`, `/`, `/structure`, `/desk`,
  `/structure?symbol=AAPL&asof=2026-06-22`) — no write ever reached a real handler (every POST
  attempted 404'd before any handler ran), so no journal/dataset/bar-series/universe/screen
  record was created or mutated.
- No Alpaca or Yahoo Finance network call was made or attempted.
- The scratch dev-stack used this project's real local `.data/`/DB files; safe given the
  read-only constraint above.

## Known Issues

- **Environment drift (carried over from every prior era baseline):** the backend venv runs
  Python **3.14.4**; `.claude/project-template.md` is still the generic, unfilled vendored
  template (placeholder text like `<e.g., Python 3.12>`, `<your project name>`) — never
  customized for this project, confirmed again this iteration. Used `docs/goal.md`'s Constraints
  section, the prior `goal-clean_slate-iter-0-dev.md` handoff, and direct codebase inspection
  (`scripts/dev.sh`, `scripts/start-backend.sh`, `scripts/start-frontend.sh`,
  `apps/backend/tests/`) as the real stack-configuration source of truth instead. Not this
  iteration's scope to fix.
- Full click-through browser verification of J-04 (nav + `/desk` not-found screenshots), J-05
  (`/structure?symbol=&asof=` empty-form screenshot), and J-07's kept-behavior walkthrough (sim
  cockpit, both charts, `/structure` Load for the pinned AAPL date, Case Studies, Edge Report) is
  the browser-qa-agent's step per the spec's TESTING REQUIREMENTS; the evidence above is the
  dev-level route/config/suite inspection leg only, per T-10 ("no screenshot ⇒ `unknown`, never
  `passing`").
- No credential blockers this iteration — none of J-01–J-06's baseline checks need Alpaca/Yahoo
  network access; the 7 suite skips are the standard two-stage `TAPEOLOGY_LIVE_INTEGRATION=1`
  opt-in gates, not missing-credential failures.

## Suggested Next Phase

Confirms the spec's own NOTES and `docs/goal.md`'s dependency order (J-01 → J-02 → J-03 → J-04 →
J-05 → J-06, with J-07 guarding continuously): iteration 1 should build **J-01 alone** — the
universe vendor seam + parser (charset check, 90–110 bounds, `BRK.B → BRK-B` normalization,
dedupe, sorted output) + the universe store (`.data/universe/universe-<date>-<checksum12>.json`,
frozen JSON + derived index) + the committed fixture snapshot + `POST /research/desk/universe/fetch`
+ `GET /research/desk/universe`, with the 3 Path-A Config fields named in `docs/goal.md`'s
Constraints section (exclusion set + stability test + counter-test + payload provenance, same
commit). Nothing else (coverage, screen, briefing, MCP tools) can exist until a registered
universe snapshot does.
