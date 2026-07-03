# goal-tape_to_profit-iter-0 Dev Handoff

**Phase:** goal-tape_to_profit-iter-0
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is the era-3 **verify-only baseline** (Mode: baseline, Depth: lean).
Zero code changes were made; the entire scope was executing the spec's verification checklist
against the current codebase and recording the evidence below. `git status --porcelain` shows
**no tracked file modified** — the only untracked entries are pipeline artifacts written by the
goal-mode engine before dev ran (`docs/phases/goal-tape_to_profit-iter-0.md`,
`runs/goal-session-tape_to_profit/`), not product source.

## Baseline test counts (the era-3 anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **Collected: 849 items. Result: 848 passed, 1 skipped, 2 warnings in 346.94s (0:05:46). Exit 0.**
- The single skip is `tests/test_live_integration.py` — the keyless live-vendor skip (no Alpaca
  credentials in this environment), expected and honest.
- This matches goal.md's "848+ tests" clause. **The era-3 baseline is 848 passing / 849 collected.**

Engine equivalence test (byte-identical default outputs, J-68 guard):

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`

- **7 passed in 0.12s.** The serialized-projection byte-identity guard over the observer seam is
  green — the frozen `default` behavior is intact and remains the pinned reference for era 3.

## Journey-by-journey verification evidence

The goal-evaluator assigns statuses; this section records what the codebase actually showed.
Predictions from the spec (J-01–J-07 FAIL, J-08 pass) were **confirmed on every point**.

### J-08 — existing product unchanged (expected PASS) — CONFIRMED WORKING

- Full suite green (848/849 above); equivalence suite green (7/7 above).
- Live backend (uvicorn `main:app`, port 8000): `GET /health` → 200.
- `POST /watch/SIM-BUYER` → 200; `GET /tape/SIM-BUYER/state` settled
  `"tape_state": "buyer_control"` at `"confidence": 0.9326`, `"stream_status": "live"`,
  `"warm": true`; `DELETE /watch/SIM-BUYER` → 200.
- Archived research API intact: `GET /research/taxonomy` → 200, `GET /research/journal` → 200,
  `GET /research/studies` → 200.
- Live frontend (next dev, port 3000, `NEXT_PUBLIC_API_URL=http://localhost:8000`):
  `GET /` → 200, `GET /journal` → 200, `GET /studies` → 200.
- Rendered nav (SSR of `/`) contains exactly three `data-testid="nav-link"` entries:
  Cockpit (`/`), Journal (`/journal`), Studies (`/studies`).
- Full browser-driven J-08 verification (cockpit panels populating over WS, SIM-SELLER settling
  `seller_control`, journal thesis table, studies create form) is the browser-qa step per the
  spec's TESTING REQUIREMENTS; the API/SSR evidence above is the dev-level leg.

### J-01 — read-only MCP server + UI route map (expected FAIL) — CONFIRMED ABSENT

- `cd apps/backend && .venv/bin/python -m app.mcp --help` →
  `No module named app.mcp`, exit 1. No `app/mcp` package or `app/mcp.py` exists.
- `GET /meta/ui-routes` on the running backend → **404** `{"detail":"Not Found"}`; no
  `meta/ui-routes` string anywhere in `apps/backend/app/` or `apps/frontend/components/`.
- `project-extensions/mcp-servers.yaml` is the empty placeholder — effective content
  `servers: {}` (comments only otherwise).
- No `.mcp.json` exists at the repo root.
- The nav list is hardcoded in `apps/frontend/components/NavBar.tsx` (3 enabled entries,
  lines 25–30) — no route-map consumer exists.

### J-02 — dataset store / train-holdout registry (expected FAIL) — CONFIRMED ABSENT

- `GET /research/datasets` → **404**.
- No `TAPEOLOGY_DATASET_DIR` or `DATASET_DIR` reference anywhere in `apps/backend/` or
  `scripts/`.
- No `apps/backend/.data/` directory; no dataset/train/holdout fixture files under
  `apps/backend/tests/fixtures/` (fixtures present: alpaca/, journal_v1–v6 schema SQL only).

### J-03 — strategy grammar + backtest engine (expected FAIL) — CONFIRMED ABSENT

- `GET /research/backtests` → **404**.
- `grep -i "strategy|profile|slippage|dataset|pnl|holdout|backtest" apps/backend/app/config.py`
  → zero matches; no fee/slippage/strategy config sections exist.

### J-04 — PnL ledger (expected FAIL) — CONFIRMED ABSENT

- `GET /research/pnl/ledger` → **404**.
- No `reports/pnl/` directory exists.

### J-05 — /performance page (expected FAIL) — CONFIRMED ABSENT

- Frontend `GET /performance` → **404** with Next.js `<title>404: This page could not be
  found.</title>`.
- No `apps/frontend/app/performance/` directory; rendered nav has no Performance entry
  (see J-08 nav evidence — exactly Cockpit · Journal · Studies).

### J-06 — versioned indicator profiles (expected FAIL) — CONFIRMED ABSENT

- `GET /research/profiles` → **404**.
- No profile registry or profile config sections anywhere (config grep above). The
  byte-equivalence guard that will pin `default` exists and passes (7/7), but no profile
  concept is implemented.

### J-07 — candidate sweep harness (expected FAIL) — CONFIRMED ABSENT

- `cd apps/backend && .venv/bin/python -m app.research.pnl_scan --help` →
  `No module named app.research.pnl_scan`, exit 1. `app/research/` contains only the
  archived-era modules (analytics, excursions, execution_checks, feed_basis, grades, hints,
  journal_rows, marks, monitor, routes, stance, store, studies, taxonomy, verdict).

### Backend route-table cross-check (authoritative absence evidence)

Dumping `app.main:app`'s route table plus the research router shows exactly the archived-era
surface: `/health`, `/watch/{ticker}` (+ pause/resume/speed), `/symbols/search`,
`/market/clock`, `/tape/{ticker}/state|features|events|summary|history`,
`WS /tape/{ticker}/stream`, and `/research/` taxonomy · analytics · thesis* · hints* ·
journal* · studies*. None of the era-3 endpoints are registered.

## Files Changed

- (none — verify-only baseline; zero source modifications)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **848 passed, 1 skipped** (849 collected), 2 warnings, 346.94s, exit 0

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`
Result: **7 passed** in 0.12s

## Service startup verification

- Backend `uvicorn main:app --app-dir apps/backend --port 8000` started clean; `/health` 200.
- Frontend `npx next dev -p 3000` (Next.js 15.5.19) started clean; all three archived pages
  served 200.
- Both processes were killed after verification; ports 8000/3000 confirmed free afterward.

## Known Issues

- **Environment drift note:** the backend venv runs Python **3.14.4** while
  `.claude/project-template.md` states Python 3.12. The full suite is green on 3.14.4, so this
  is a documentation/environment drift observation, not a failure — recorded for honesty, no
  action taken (out of scope for a verify-only iteration).
- pytest emitted dot-format progress despite `-v` (project `pyproject.toml` output config);
  counts were taken from the authoritative summary line.
- `tests/test_live_integration.py` skips keyless (expected — no Alpaca credentials; all era-3
  journeys are keyless by design).
- Browser-level J-08/J-05/J-01 checks (SIM-BUYER/SIM-SELLER cockpit flows, nav rendering,
  /performance 404 in a real browser) remain for the browser-qa step, as the spec assigns.

## Suggested Next Phase

Per the spec's NOTES and goal.md's dependency order: iter-1 should be either **J-01** (the
read-only MCP server + `/meta/ui-routes` — independent, and it unlocks MCP-assisted
verification for every later iteration) or **J-02** (dataset store + train/hold-out registry —
head of the J-02 → J-03 → J-04 → J-05 chain). J-01 first is slightly preferable: it retires
the hardcoded NavBar list behind the canonical route map before any new page ships, and gives
the dev-chain its machine-readable survey surface from the start.
